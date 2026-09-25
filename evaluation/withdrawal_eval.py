"""Withdrawing an agent *during* a run.

Every scenario measured so far changes the deployment before formation
runs. That is the easy case: formation simply sees a different set of
agents. The harder case, conceded as a limitation, is an agent that
disappears after the team has been formed and while it is being executed.

Two conditions:

  fixed-plan    the plan is computed once and followed. This is the
                behaviour of the system as described in the chapter.
  reforming     when a call to a team member fails, the coordinator
                re-discovers what is still running and re-forms from the
                material already produced, rather than from the beginning.

Two withdrawal cases, chosen because they should behave differently:

  necessary     the withdrawn agent is the only one satisfying a
                requirement the task raised. No recovery is possible and
                the question is only whether that is reported or crashed.
  optional      the withdrawn agent is a refiner that no requirement
                obliges. Recovery is possible, so the conditions separate.

Run:  python -m evaluation.withdrawal_eval
"""

from __future__ import annotations

import contextlib
import csv
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

from phase2_multi_agent.llm import get_backend
from phase4_a2a.client import A2APeers
from phase4_a2a.launch import PORTS
from phase8_discovery.discovery import StaticDiscovery
from phase8_discovery.formation import form_team_targeted, read_capability
from phase8_discovery.requirements import profile

BRIEF = "Question: {q}\n\nMaterial so far:\n{m}\n\nDo your part and return only your contribution."


# --------------------------------------------------------------------------
# a launcher that keeps a handle on each agent, so one can be killed
# --------------------------------------------------------------------------
class Cluster:
    def __init__(self, names: list[str]) -> None:
        self.names = names
        self.procs: dict[str, subprocess.Popen] = {}

    def _up(self, port: int, timeout: float = 45.0) -> bool:
        deadline = time.time() + timeout
        url = f"http://127.0.0.1:{port}/.well-known/agent-card.json"
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=1):
                    return True
            except (urllib.error.URLError, OSError):
                time.sleep(0.2)
        return False

    def __enter__(self) -> "Cluster":
        for n in self.names:
            self.procs[n] = subprocess.Popen(
                [sys.executable, "-m", "phase4_a2a.server", n, str(PORTS[n])],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        for n in self.names:
            if not self._up(PORTS[n]):
                raise RuntimeError(f"{n} did not start")
        return self

    def __exit__(self, *exc: object) -> None:
        for p in self.procs.values():
            p.terminate()
        for p in self.procs.values():
            with contextlib.suppress(Exception):
                p.wait(timeout=10)

    def withdraw(self, name: str) -> None:
        """Remove one agent from the deployment, mid-run."""
        p = self.procs.pop(name, None)
        if p:
            p.kill()
            with contextlib.suppress(Exception):
                p.wait(timeout=5)
        self.names = [n for n in self.names if n != name]

    def urls(self) -> dict[str, str]:
        return {n: f"http://127.0.0.1:{PORTS[n]}" for n in self.names}


# --------------------------------------------------------------------------
def capabilities(peers: A2APeers) -> list:
    return [read_capability(n, c) for n, c in peers.cards.items() if c is not None]


def trial(deployed, question, withdraw, condition, backend_name="stub") -> dict:
    """One run: form a team, start executing, remove an agent, see what happens."""
    required = profile(question)
    row = {
        "condition": condition, "withdraw": withdraw, "required": ",".join(sorted(required)) or "-",
        "planned": "", "executed": 0, "completed": False,
        "detect_s": "", "outcome": "", "reformed": "",
    }

    with Cluster(list(deployed)) as cluster:
        with A2APeers(cluster.urls()) as peers:
            caps = capabilities(peers)
            plan = form_team_targeted(caps, required)
            row["planned"] = " -> ".join(plan.team) or "(none)"
            if not plan.reached_goal:
                row["outcome"] = "no team could be formed"
                return row

            produced = {"query"}
            material = "(nothing yet)"
            queue = list(plan.team)
            done = 0
            killed = False

            while queue:
                agent = queue.pop(0)

                # withdraw just before the target agent is called
                if not killed and agent == withdraw:
                    cluster.withdraw(agent)
                    killed = True

                t0 = time.time()
                result = peers.ask(agent, BRIEF.format(q=question, m=material))
                elapsed = time.time() - t0

                if result.startswith("error:"):
                    row["detect_s"] = f"{elapsed:.2f}"
                    if condition == "fixed-plan":
                        row["outcome"] = f"aborted at {agent}: call failed"
                        row["executed"] = done
                        return row

                    # reforming: ask what is still running, re-plan from here
                    live = StaticDiscovery(cluster.urls()).find_agents()
                    with A2APeers({e.name: e.url for e in live}) as again:
                        caps2 = capabilities(again)
                        plan2 = form_team_targeted(caps2, required, start=produced)
                        row["reformed"] = " -> ".join(plan2.team) or "(none)"
                        if not plan2.reached_goal:
                            row["outcome"] = f"reported: {plan2.describe()}"
                            row["executed"] = done
                            return row
                        queue = list(plan2.team)
                        peers_live = again
                        # continue the remaining chain on the live peers
                        for nxt in queue:
                            out = peers_live.ask(nxt, BRIEF.format(q=question, m=material))
                            if out.startswith("error:"):
                                row["outcome"] = f"re-formed plan also failed at {nxt}"
                                row["executed"] = done
                                return row
                            material += f"\n\n--- {nxt} ---\n{out}"
                            done += 1
                        row["completed"] = True
                        row["executed"] = done
                        row["outcome"] = "recovered and completed"
                        return row

                material = (f"--- {agent} ---\n{result}" if material == "(nothing yet)"
                            else material + f"\n\n--- {agent} ---\n{result}")
                produced |= next(c.produces for c in caps if c.agent == agent)
                done += 1

            row["completed"] = True
            row["executed"] = done
            row["outcome"] = "completed, no withdrawal encountered"
            return row


def main() -> None:
    sole = ["research", "factcheck", "analysis", "writer"]
    redundant = ["research", "factcheck", "analysis", "compute", "writer"]
    q_compute = ("How many multi-agent failure modes are there per category "
                 "on average?")
    cases = [
        # the withdrawn agent is the only satisfier of a raised requirement
        ("sole satisfier", sole, q_compute, "analysis"),
        # a second agent satisfies the same requirement and can be routed to
        ("alternative deployed", redundant, q_compute, "analysis"),
    ]

    rows = []
    for label, deployed, question, victim in cases:
        for condition in ("fixed-plan", "reforming"):
            print(f"\n=== {label}: withdrawing {victim!r} under {condition} ===")
            r = trial(deployed, question, victim, condition)
            r["case"] = label
            rows.append(r)
            print(f"  planned : {r['planned']}")
            if r["reformed"]:
                print(f"  reformed: {r['reformed']}")
            print(f"  detect  : {r['detect_s']}s")
            print(f"  outcome : {r['outcome']}")

    out = pathlib.Path(__file__).parent / "results" / "withdrawal.csv"
    cols = ["case", "condition", "withdraw", "required", "planned", "reformed",
            "executed", "completed", "detect_s", "outcome"]
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in cols} for r in rows])
    print(f"\n{len(rows)} trials -> {out}")


if __name__ == "__main__":
    main()

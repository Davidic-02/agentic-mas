"""An agent that is reachable but not making progress.

`withdrawal_eval.py` removes an agent's process. The connection is then
refused and the failure is obvious within milliseconds. This file tests the
harder case the chapter concedes: the agent is still running, still serving
its capability card, still passing its readiness probe -- and simply never
answers the task.

This is the failure mode that every health signal in the system misses. The
readiness probe fetches the agent's card, which keeps working throughout, so
Kubernetes keeps the pod in service, discovery keeps returning it, and
formation keeps selecting it. Only the task call reveals the problem, and
only after a timeout the caller chose.

Measured:
  detect_s     how long until the caller gives up (a configuration choice,
               not a property of the system)
  card_alive   whether the agent's own health signal still passes while it
               is failing to do any work
  outcome      what the coordinator does about it

Run:  python -m evaluation.unresponsive_eval
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

from phase4_a2a.client import A2APeers
from phase4_a2a.launch import PORTS
from phase8_discovery.discovery import StaticDiscovery
from phase8_discovery.formation import form_team_targeted, read_capability
from phase8_discovery.requirements import profile

BRIEF = "Question: {q}\n\nMaterial so far:\n{m}\n\nDo your part and return only your contribution."

# Short, so the trial finishes quickly. The figure is arbitrary by design:
# the point of the experiment is that detection latency is whatever the
# caller sets it to, not something the system discovers for itself.
TIMEOUT = 8.0
HANG = 600.0


def card_ok(port: int, timeout: float = 2.0) -> bool:
    """Does the agent still pass the health signal Kubernetes would use?"""
    try:
        url = f"http://127.0.0.1:{port}/.well-known/agent-card.json"
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError):
        return False


class Cluster:
    """Agents as processes; one of them may be told to hang."""

    def __init__(self, names: list[str], hanging: str | None = None) -> None:
        self.names = names
        self.hanging = hanging
        self.procs: dict[str, subprocess.Popen] = {}

    def __enter__(self) -> "Cluster":
        import os

        for n in self.names:
            env = dict(os.environ)
            env["AGENT_HANG_SECONDS"] = str(HANG) if n == self.hanging else "0"
            self.procs[n] = subprocess.Popen(
                [sys.executable, "-m", "phase4_a2a.server", n, str(PORTS[n])],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
            )
        deadline = time.time() + 45
        for n in self.names:
            while time.time() < deadline and not card_ok(PORTS[n]):
                time.sleep(0.25)
            if not card_ok(PORTS[n]):
                raise RuntimeError(f"{n} did not start")
        return self

    def __exit__(self, *exc: object) -> None:
        for p in self.procs.values():
            p.kill()
        for p in self.procs.values():
            with contextlib.suppress(Exception):
                p.wait(timeout=10)

    def urls(self) -> dict[str, str]:
        return {n: f"http://127.0.0.1:{PORTS[n]}" for n in self.names}


def trial(deployed, question, hanging, condition) -> dict:
    required = profile(question)
    row = {"condition": condition, "hanging": hanging, "planned": "",
           "detect_s": "", "card_alive": "", "reformed": "", "outcome": "",
           "completed": False}

    with Cluster(list(deployed), hanging=hanging) as cluster:
        with A2APeers(cluster.urls(), timeout=TIMEOUT) as peers:
            caps = [read_capability(n, c) for n, c in peers.cards.items() if c]
            plan = form_team_targeted(caps, required)
            row["planned"] = " -> ".join(plan.team) or "(none)"
            if not plan.reached_goal:
                row["outcome"] = "no team could be formed"
                return row

            produced = {"query"}
            material = "(nothing yet)"
            for agent in plan.team:
                t0 = time.time()
                result = peers.ask(agent, BRIEF.format(q=question, m=material))
                elapsed = time.time() - t0

                if result.startswith("error:"):
                    row["detect_s"] = f"{elapsed:.1f}"
                    # the decisive observation: is the agent still "healthy"?
                    row["card_alive"] = "yes" if card_ok(PORTS[agent]) else "no"

                    if condition == "fixed-plan":
                        row["outcome"] = f"aborted at {agent} after the timeout"
                        return row

                    # re-form, excluding the agent that did not answer
                    live = {e.name: e.url
                            for e in StaticDiscovery(cluster.urls()).find_agents()
                            if e.name != agent}
                    with A2APeers(live, timeout=TIMEOUT) as again:
                        caps2 = [read_capability(n, c)
                                 for n, c in again.cards.items() if c]
                        plan2 = form_team_targeted(caps2, required, start=produced)
                        row["reformed"] = " -> ".join(plan2.team) or "(none)"
                        if not plan2.reached_goal:
                            row["outcome"] = f"declined: {plan2.describe()}"
                            return row
                        for nxt in plan2.team:
                            out = again.ask(nxt, BRIEF.format(q=question, m=material))
                            if out.startswith("error:"):
                                row["outcome"] = f"re-formed plan also failed at {nxt}"
                                return row
                            material += f"\n\n--- {nxt} ---\n{out}"
                        row["completed"] = True
                        row["outcome"] = "recovered and completed"
                        return row

                material = (f"--- {agent} ---\n{result}" if material == "(nothing yet)"
                            else material + f"\n\n--- {agent} ---\n{result}")
                produced |= next(c.produces for c in caps if c.agent == agent)

            row["completed"] = True
            row["outcome"] = "completed (no hang encountered)"
            return row


def main() -> None:
    q = "How many multi-agent failure modes are there per category on average?"
    sole = ["research", "factcheck", "analysis", "writer"]
    redundant = ["research", "factcheck", "analysis", "compute", "writer"]

    cases = [
        ("sole satisfier hangs", sole, "analysis"),
        ("alternative deployed", redundant, "analysis"),
    ]

    print(f"client timeout {TIMEOUT:.0f}s; the hanging agent sleeps {HANG:.0f}s\n")
    rows = []
    for label, deployed, victim in cases:
        for condition in ("fixed-plan", "reforming"):
            print(f"=== {label} — {condition} ===")
            r = trial(deployed, q, victim, condition)
            r["case"] = label
            rows.append(r)
            print(f"  planned    : {r['planned']}")
            print(f"  detected in: {r['detect_s']}s")
            print(f"  card still serving while hung: {r['card_alive']}")
            if r["reformed"]:
                print(f"  re-formed  : {r['reformed']}")
            print(f"  outcome    : {r['outcome']}\n")

    out = pathlib.Path(__file__).parent / "results" / "unresponsive.csv"
    cols = ["case", "condition", "hanging", "planned", "detect_s", "card_alive",
            "reformed", "completed", "outcome"]
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in cols} for r in rows])
    print(f"{len(rows)} trials -> {out}")


if __name__ == "__main__":
    main()

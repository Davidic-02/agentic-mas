"""Tier 1 -- team composition, measured without any model.

Which agents get chosen, and in what order, is decided by `form_team` from
declared capabilities. It does not involve inference at all, so it can be
measured exactly and instantly, with no variance to average away.

Two conditions:

  static    the phase 4 arrangement -- a fixed team written in source
  derived   discovered and chained per run, but blind to the task
  targeted  discovered, and the task's own requirements decide membership

Measures per (condition, scenario, task):

  completes   can this team produce a report at all
  precision   |chosen and needed| / |chosen|   -- penalises agents that
              contribute nothing
  recall      |chosen and needed| / |needed|   -- penalises missing agents
  code_change did accommodating this scenario require editing source
  failure     how it fails when it fails -- "reported" means the system
              says what is missing before acting; "runtime" means it
              discovers the problem by calling something that is not there
"""

from __future__ import annotations

import csv
import pathlib

from phase4_a2a.cards import SPECS, build_card
from phase8_discovery.formation import (
    Capability,
    form_team,
    form_team_targeted,
    read_capability,
)
from phase8_discovery.requirements import profile

from .tasks import SCENARIOS, TASKS

# What phase 4 hardcodes. It cannot change without editing the file.
STATIC_TEAM = ["research", "analysis", "writer"]


def capabilities_for(deployed: list[str], *, tight_writer: bool = False):
    """Capabilities as the agents declare them.

    `tight_writer` restores the original declaration, where the writer
    consumed `conclusions` only. Two things changed between the first
    evaluation and this one -- that declaration, and task-awareness -- so
    both are held as separate conditions rather than confounded.
    """
    caps = [
        read_capability(name, build_card(name, f"http://{name}:8100/"))
        for name in deployed
        if name in SPECS
    ]
    if tight_writer:
        caps = [
            Capability(c.agent, frozenset({"conclusions"}), c.produces, c.satisfies)
            if c.agent == "writer"
            else c
            for c in caps
        ]
    return caps


def score(chosen: list[str], needed: frozenset[str]) -> tuple[float, float]:
    if not chosen:
        return 0.0, 0.0
    hit = len(set(chosen) & needed)
    return hit / len(chosen), hit / len(needed)


def evaluate() -> list[dict]:
    rows = []
    for scenario, deployed in SCENARIOS.items():
        caps = capabilities_for(deployed)
        caps_v1 = capabilities_for(deployed, tight_writer=True)

        for task in TASKS:
            # --- static: the team is whatever the source file says -------
            # It does not consult what is deployed, so it "chooses" agents
            # that may not exist. Those calls fail at runtime.
            missing = [a for a in STATIC_TEAM if a not in deployed]
            static_completes = not missing
            sp, sr = score(STATIC_TEAM, task.needed)
            rows.append(
                {
                    "condition": "static",
                    "scenario": scenario,
                    "task": task.id,
                    "team": " -> ".join(STATIC_TEAM),
                    "team_size": len(STATIC_TEAM),
                    "completes": static_completes,
                    "precision": round(sp, 3),
                    "recall": round(sr, 3),
                    "code_change_required": scenario != "baseline",
                    # A static team cannot know an agent is absent. It finds
                    # out by calling it, mid-task, after partial work.
                    "failure_mode": "runtime" if missing else "none",
                    "failure": f"calls missing agent(s): {missing}" if missing else "",
                }
            )

            # --- derived v1: the mechanism as originally evaluated -------
            p1 = form_team(caps_v1)
            p1p, p1r = score(p1.team, task.needed)
            rows.append(
                {
                    "condition": "derived-v1",
                    "scenario": scenario,
                    "task": task.id,
                    "team": " -> ".join(p1.team) or "(none)",
                    "team_size": len(p1.team),
                    "completes": p1.reached_goal,
                    "precision": round(p1p, 3),
                    "recall": round(p1r, 3),
                    "code_change_required": False,
                    "failure_mode": "none" if p1.reached_goal else "reported",
                    "failure": "" if p1.reached_goal else p1.describe(),
                }
            )

            # --- derived v2: looser declarations, still blind to the task -
            plan = form_team(caps)
            dp, dr = score(plan.team, task.needed)
            rows.append(
                {
                    "condition": "derived-v2",
                    "scenario": scenario,
                    "task": task.id,
                    "team": " -> ".join(plan.team) or "(none)",
                    "team_size": len(plan.team),
                    "completes": plan.reached_goal,
                    "precision": round(dp, 3),
                    "recall": round(dr, 3),
                    "code_change_required": False,
                    # Formation runs before any agent is called, so an
                    # unsatisfiable task is reported rather than attempted.
                    "failure_mode": "none" if plan.reached_goal else "reported",
                    "failure": "" if plan.reached_goal else plan.describe(),
                }
            )

            # --- targeted: the task decides who earns a place ------------
            tplan = form_team_targeted(caps, profile(task.question))
            tp, tr = score(tplan.team, task.needed)
            rows.append(
                {
                    "condition": "targeted",
                    "scenario": scenario,
                    "task": task.id,
                    "team": " -> ".join(tplan.team) or "(none)",
                    "team_size": len(tplan.team),
                    "completes": tplan.reached_goal,
                    "precision": round(tp, 3),
                    "recall": round(tr, 3),
                    "code_change_required": False,
                    "failure_mode": "none" if tplan.reached_goal else "reported",
                    "failure": "" if tplan.reached_goal else tplan.describe(),
                }
            )
    return rows


def main() -> None:
    rows = evaluate()
    out = pathlib.Path(__file__).parent / "results" / "formation.csv"
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()

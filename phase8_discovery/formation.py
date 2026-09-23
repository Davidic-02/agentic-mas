"""Assembling a team from whatever agents happen to exist.

Discovery answers "who is running?". This answers "given these agents and
this task, who should do what, in what order?" -- without the order being
written down anywhere.

The mechanism
-------------
Each agent's card tags declare `consumes:<type>` and `produces:<type>`.
A team is then a chain from what we start with (a `query`) to what we want
(a `report`), where each agent's output feeds the next one's input.

    query --[research]--> findings --[analysis]--> conclusions --[writer]--> report

Nothing in this file knows that research comes before analysis. It knows
that analysis consumes what research produces, which is a property the
agents themselves assert. Deploy an agent that consumes `findings` and
produces `findings` -- a fact-checker, say -- and it becomes eligible for
insertion into the chain without a line of code changing here.

Consequences that matter for the deployment
-------------------------------------------
* An agent that disappears is simply not in the next plan.
* An agent that appears is considered immediately.
* If no chain reaches the goal, that is a *reportable* outcome ("no agent
  produces `report`"), not a crash.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

CONSUMES = "consumes:"
PRODUCES = "produces:"

START = "query"
GOAL = "report"


@dataclass(frozen=True)
class Capability:
    """What one agent needs and what it yields."""

    agent: str
    consumes: frozenset[str]
    produces: frozenset[str]

    def can_run_given(self, available: Iterable[str]) -> bool:
        """An agent can run once everything it consumes is on the table."""
        return self.consumes <= set(available)

    @property
    def is_refiner(self) -> bool:
        """Does this agent hand back a type it was given?

        A refiner improves something in place -- verification, enrichment,
        cleaning -- and leaves the type available for whoever comes next.
        A transformer consumes a type and yields a different one, which
        ends that type's useful life in the chain.

        The distinction decides ordering: a refiner of T must run before a
        transformer of T, or it refines something nobody will read.
        """
        return bool(self.consumes & self.produces)


def read_capability(name: str, card: Any) -> Capability:
    consumes, produces = set(), set()
    for skill in getattr(card, "skills", []):
        for tag in skill.tags:
            if tag.startswith(CONSUMES):
                consumes.add(tag[len(CONSUMES):])
            elif tag.startswith(PRODUCES):
                produces.add(tag[len(PRODUCES):])
    return Capability(name, frozenset(consumes), frozenset(produces))


@dataclass
class Plan:
    """An ordered team, plus why it looks the way it does."""

    team: list[str]
    produced: set[str]
    reached_goal: bool
    unreachable: set[str]

    def describe(self) -> str:
        if self.reached_goal:
            return " -> ".join(self.team) if self.team else "(empty team)"
        have = ", ".join(sorted(self.produced)) or "nothing"
        return (
            f"incomplete: {' -> '.join(self.team) or '(no agents usable)'}; "
            f"produced {have}; cannot produce {GOAL!r}"
        )


def form_team(
    capabilities: list[Capability], *, start: str = START, goal: str = GOAL
) -> Plan:
    """Forward chaining from `start` until `goal` is produced.

    At each step several agents may be runnable. The choice between them is
    where an arbitrary-but-valid order becomes a sensible one:

      1. **Refiners first.** An agent that returns a type it consumed is
         improving material the next agent will read. If a transformer runs
         first, that type is gone and the refinement never happens.
      2. **Then by name**, so a given deployment always produces the same
         plan. A plan that changes between identical runs is not one you
         can reason about.

    Scoping falls out of the chaining: a refiner of `conclusions` cannot
    become runnable until `conclusions` exists, which is already after the
    agents that produce it. So the rule needs no per-type bookkeeping.
    """
    available = {start}
    remaining = list(capabilities)
    team: list[str] = []

    progress = True
    while progress and goal not in available:
        progress = False
        runnable = [c for c in remaining if c.can_run_given(available)]
        if runnable:
            runnable.sort(key=lambda c: (not c.is_refiner, c.agent))
            cap = runnable[0]
            team.append(cap.agent)
            available |= cap.produces
            remaining.remove(cap)
            progress = True

    unreachable = {c.agent for c in remaining}
    return Plan(
        team=team,
        produced=available - {start},
        reached_goal=goal in available,
        unreachable=unreachable,
    )

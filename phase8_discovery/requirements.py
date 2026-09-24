"""What a task actually needs, before deciding who does it.

The measured flaw in the first mechanism was that formation never saw the
task. It chained whatever could be chained, so it built the same team for a
question needing arithmetic and one needing none.

This closes that. A task is profiled into a set of *requirement markers*;
agents declare which markers they satisfy in their A2A card tags
(`satisfies:<marker>`); formation then includes an agent only when it is
necessary to reach a report or satisfies a marker the task raised.

The profiler here is deliberately a keyword heuristic. That keeps formation
deterministic and exactly measurable -- no inference, no variance. Replacing
it with a model-based profiler is the obvious next step, but it would move
team composition from something that can be measured exactly to something
that has to be sampled, so the two should be compared, not conflated.
"""

from __future__ import annotations

import re

SATISFIES = "satisfies:"

# marker -> patterns in the task that raise it
SIGNALS: dict[str, list[str]] = {
    "computation": [
        r"\baverage\b", r"\bmean\b", r"\btotal\b", r"\bsum\b",
        r"\bper\b", r"\bratio\b", r"\bpercent", r"\bhow much\b",
        r"\btimes\b", r"\bmultipl", r"\bdivid", r"\bcalculat",
        r"\bcompare[ds]?\b", r"\bdifference between\b.*\bnumber",
    ],
    "verification": [
        r"\bverify\b", r"\bconfirm\b", r"\bcheck\b", r"\baccurate\b",
        r"\bis it true\b", r"\bfact.?check\b",
    ],
}


def profile(task: str) -> frozenset[str]:
    """Which requirement markers this task raises."""
    text = task.lower()
    return frozenset(
        marker
        for marker, patterns in SIGNALS.items()
        if any(re.search(p, text) for p in patterns)
    )


def read_satisfies(card) -> frozenset[str]:
    """Markers an agent advertises it can satisfy."""
    out = set()
    for skill in getattr(card, "skills", []):
        for tag in skill.tags:
            if tag.startswith(SATISFIES):
                out.add(tag[len(SATISFIES):])
    return frozenset(out)

"""The task set, with ground truth about which agents each task needs.

`needed` is the minimal set of agents required to answer correctly. It is a
judgement, made once, before any results were seen, and it is what the
precision measure is scored against. Recording it here rather than deciding
it per run is the point -- otherwise the metric moves to fit the outcome.

`writer` appears in every set: it is what turns material into the answer.
`factcheck` appears in none: it is a refiner, useful but never required for
correctness.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    id: str
    question: str
    needed: frozenset[str]
    note: str


TASKS = [
    Task(
        "probe-count",
        "How many probe types does Kubernetes have?",
        frozenset({"research", "writer"}),
        "Single retrieved fact. No computation.",
    ),
    Task(
        "protocol-diff",
        "What is the difference between MCP and A2A?",
        frozenset({"research", "writer"}),
        "Synthesis across two documents. No computation.",
    ),
    Task(
        "failure-average",
        "How many multi-agent failure modes are there per category on average?",
        frozenset({"research", "analysis", "writer"}),
        "Retrieval plus arithmetic the corpus does not state.",
    ),
    Task(
        "capability-product",
        "How many capability kinds does MCP expose, and what is that number times four?",
        frozenset({"research", "analysis", "writer"}),
        "Retrieval plus arithmetic.",
    ),
    Task(
        "absent-fact",
        "What is the default Kubernetes pod restart backoff limit?",
        frozenset({"research", "writer"}),
        "Not in the corpus. Correct behaviour is to report its absence.",
    ),
]


# Which agents are deployed. The independent variable on the infrastructure
# side: what the system finds running when it starts.
SCENARIOS = {
    # the team the static version was written for
    "baseline": ["research", "analysis", "writer"],
    # a capability appears after the system was written
    "agent-added": ["research", "analysis", "writer", "factcheck"],
    # a middle link disappears -- the goal is unreachable
    "analysis-removed": ["research", "writer"],
    # the entry point disappears -- nothing consumes a raw query
    "research-removed": ["analysis", "writer", "factcheck"],
}

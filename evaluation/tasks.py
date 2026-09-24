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
    # --- single-fact retrieval -------------------------------------------
    Task("probe-count",
         "How many probe types does Kubernetes have?",
         frozenset({"research", "writer"}),
         "Single retrieved fact."),
    Task("mcp-kinds",
         "How many capability kinds does MCP expose?",
         frozenset({"research", "writer"}),
         "Single retrieved fact."),
    Task("failure-count",
         "How many distinct multi-agent failure modes have been catalogued?",
         frozenset({"research", "writer"}),
         "Single retrieved fact."),

    # --- cross-document synthesis ----------------------------------------
    Task("protocol-diff",
         "What is the difference between MCP and A2A?",
         frozenset({"research", "writer"}),
         "Synthesis across two documents. No computation."),
    Task("protocol-layers",
         "How do MCP and A2A relate to one another as layers of an "
         "interoperability stack?",
         frozenset({"research", "writer"}),
         "Synthesis across two documents."),

    # --- arithmetic the corpus does not state ----------------------------
    Task("failure-average",
         "How many multi-agent failure modes are there per category on average?",
         frozenset({"research", "analysis", "writer"}),
         "Retrieval plus division."),
    Task("capability-product",
         "How many capability kinds does MCP expose, and what is that number "
         "times four?",
         frozenset({"research", "analysis", "writer"}),
         "Retrieval plus multiplication."),
    Task("type-total",
         "What is the total of the number of Kubernetes probe types and the "
         "number of MCP capability kinds?",
         frozenset({"research", "analysis", "writer"}),
         "Retrieval plus addition across two documents."),
    Task("failure-ratio",
         "What is the ratio of multi-agent failure modes to failure categories?",
         frozenset({"research", "analysis", "writer"}),
         "Retrieval plus ratio."),
    Task("count-compare",
         "Compare the number of Kubernetes probe types with the number of "
         "multi-agent failure categories.",
         frozenset({"research", "analysis", "writer"}),
         "Retrieval plus numeric comparison."),

    # --- claims to be checked against the corpus -------------------------
    Task("verify-probes",
         "Verify that Kubernetes supports exactly three probe types.",
         frozenset({"research", "factcheck", "writer"}),
         "Raises verification: a stated claim must be checked, not retrieved."),
    Task("confirm-kinds",
         "Confirm whether MCP exposes four kinds of capability.",
         frozenset({"research", "factcheck", "writer"}),
         "Raises verification; the claim as stated is false."),

    # --- absent from the corpus ------------------------------------------
    Task("absent-backoff",
         "What is the default Kubernetes pod restart backoff limit?",
         frozenset({"research", "writer"}),
         "Not in the corpus. Correct behaviour is to report its absence."),
    Task("absent-replicas",
         "What is the default replica count for a Kubernetes Deployment?",
         frozenset({"research", "writer"}),
         "Not in the corpus."),
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

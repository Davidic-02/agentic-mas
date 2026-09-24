# Project Specification

**An Agentic Application Built Using a Multi-Agent System Based on Open
Standards in a Cloud-Native Environment**

---

## 1. Aim

Design, build and deploy an agentic application in which a team of
specialised AI agents collaborate to complete a complex task, communicating
through open interoperability standards and operating as independently
deployed services in a cloud-native environment.

## 2. Objectives

1. Implement autonomous agents capable of planning and tool use.
2. Decompose a complex task across multiple specialised agents under a
   coordinator.
3. Expose all tool and data access through the **Model Context Protocol
   (MCP)** rather than direct in-process calls.
4. Implement inter-agent communication through the **Agent2Agent (A2A)**
   protocol, so agents interoperate without knowledge of one another's
   internals.
5. Deploy each agent as an independent containerised service orchestrated
   by Kubernetes, with health checking, service discovery and observability.
6. Demonstrate and evaluate the resulting system end to end.

## 3. Scope

**In scope:** the agent layer, the open-standard interfaces between agents
and between agents and tools, and the cloud-native deployment of the whole
system.

**Out of scope:** training or fine-tuning models; building a new agent
framework; contributing new capability to Kubernetes itself.

## 4. Application domain

A **document research assistant**. Given a question, the system searches a
local corpus, extracts and computes over what it finds, and produces a cited
report.

The domain is deliberately modest. It exists to exercise the architecture --
multi-step work, genuine tool dependence, and verifiable answers -- and is
not itself the contribution.

## 5. System architecture

```
                          USER REQUEST
                                |
                                v
                     +----------------------+
                     |   Coordinator Agent  |     plans + delegates
                     +----------+-----------+
                                |
                          A2A protocol
                                |
          +---------------------+---------------------+
          |                     |                     |
          v                     v                     v
   +-------------+       +-------------+       +-------------+
   |  Research   |       |  Analysis   |       |   Writer    |
   |    Agent    |       |    Agent    |       |    Agent    |
   +------+------+       +------+------+       +------+------+
          |                     |                     |
          +---------- MCP protocol ------------------+
                                |
                                v
                     +----------------------+
                     |      MCP Server      |
                     |  search | calculate  |
                     |  fetch  | store      |
                     +----------------------+

   ------------------ CLOUD-NATIVE LAYER -----------------------
   Each agent is an independent containerised service.
   Kubernetes provides deployment, service discovery, health
   probes, scaling and restart. Tracing spans the whole request.
```

### 5.1 Agents

| Agent | Responsibility |
|---|---|
| Coordinator | Interprets the request, plans, delegates, assembles the result |
| Research | Retrieves relevant material from the corpus via MCP |
| Analysis | Compares, computes over and reasons about retrieved material |
| Writer | Synthesises a final cited report |

### 5.2 Open standards

- **MCP** -- the vertical interface. Every tool and data source is reached
  through an MCP server. No agent imports a tool function directly.
- **A2A** -- the horizontal interface. Agents advertise capabilities and
  exchange tasks as standard-conformant peers.

The standards are structural, not decorative: an agent is replaceable by any
other agent exposing the same A2A capability, and a tool is replaceable by
any MCP server exposing the same tool.

### 5.3 Cloud-native design

| Concern | Mechanism |
|---|---|
| Packaging | One container image per agent |
| Orchestration | Kubernetes Deployment + Service per agent |
| Discovery | Kubernetes DNS; A2A capability descriptions |
| Health | HTTP liveness and readiness endpoints |
| Scaling | Independent replica counts per agent |
| Resilience | Restart on failure; coordinator degrades gracefully |
| Observability | Structured logs and request tracing |

## 6. Technology stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| Model | Claude (Anthropic API) |
| Tool interface | MCP (`mcp` Python SDK) |
| Agent interface | A2A |
| Service transport | HTTP / JSON-RPC |
| Containers | Docker |
| Orchestration | Kubernetes (local: kind or Docker Desktop) |

## 7. Build phases

| # | Deliverable | Status |
|---|---|---|
| 1 | Single agent with tool-calling loop | built |
| 2 | Coordinator delegating to specialist agents | **built, runs end to end** |
| 3 | Tools relocated behind an MCP server | **built, runs end to end** |
| 4 | Agents communicating over A2A | **built, runs end to end** |
| 5 | Agents split into independent services | **done** |
| 6 | Containerisation | **built and running** (339 MB image, non-root) |
| 7 | Kubernetes deployment | **deployed and demonstrated** (colima/k3s) |

Phases 1-7 constitute the specified project. Work beyond phase 7 is recorded
separately.

### Model backend

Agents reason through a pluggable backend (`llm.py`). A deterministic stub
backend runs the whole system offline at no cost, which is sufficient to
build and test phases 3-7 -- protocols, services and orchestration do not
require model inference. Real inference runs against a local model through Ollama
(`AGENT_BACKEND=ollama`, `qwen2.5:7b`), requiring no API key, no account and
no network. A hosted frontier model is available as `AGENT_BACKEND=anthropic`
for comparison but is not required at any stage.

That a 7B local model is sufficient to drive this architecture end to end is
itself a result: the architecture does not depend on frontier-model
capability.

## 8. Demonstration

**Status: demonstrated 23 September 2026.** All five points below were
executed against a local k3s cluster.

The completed system is demonstrated by issuing a request that cannot be
answered by any single agent alone, and showing:

1. the coordinator's decomposition of the task,
2. A2A traffic between agents,
3. MCP tool invocations,
4. all agents running as separate Kubernetes workloads,
5. continued operation when an agent replica is deliberately killed.

---

## 9. Beyond the specified project: runtime team formation

Phases 1-7 deliver the specified system. This section records work that goes
past it.

### Problem

Through phase 7 the coordinator's team is a literal in source:

    PORTS = {"research": 8101, "analysis": 8102, "writer": 8103}

This asserts at authoring time three things that are not knowable at
authoring time: which agents exist, how many, and where. In a cloud-native
deployment all three change while the system runs.

### Mechanism

1. **Discovery** (`phase8_discovery/discovery.py`) -- query the Kubernetes
   API for Services labelled `a2a.agent/enabled=true`. Services rather than
   Pods: a Pod address dies with the Pod.
2. **Declared capability** -- each agent's A2A card tags carry
   `consumes:<type>` and `produces:<type>`. These are ordinary A2A tags,
   ignored harmlessly by any other A2A client.
3. **Formation** (`phase8_discovery/formation.py`) -- greedy forward
   chaining from `query` to `report`. The team and its order are derived
   from declared capabilities; no pipeline is written down anywhere.

### Demonstrated

* Team derived correctly from agents discovered in arbitrary order.
* A fourth agent (`factcheck`) deployed and incorporated with **no change to
  any coordinator code**.
* A missing agent yields a reportable incomplete plan, not a failure.
* Coordinator runs in-cluster under a minimal RBAC role (read Services only).

### Ordering: problem found and resolved

The first working version used plain greedy chaining -- take any runnable
agent. With `factcheck` (consumes `findings`, produces `findings`) deployed
alongside `analysis` (consumes `findings`, produces `conclusions`), it
derived

    research -> analysis -> factcheck -> writer

Valid -- every input satisfied -- but wrong: verification ran after the
analysis it should have informed, and refined findings nobody read.

The cause was that greedy chaining cannot distinguish two kinds of agent:

| | consumes | produces | effect on the type |
|---|---|---|---|
| **Refiner** | T | T | improves it, leaves it available |
| **Transformer** | T | U | consumes it; T's useful life ends |

A refiner of T must precede any transformer of T. The selection rule is now:
among runnable agents, prefer refiners; break ties by name.

Scoping needs no per-type bookkeeping: a refiner of `conclusions` cannot
become runnable before `conclusions` exists, which is already after the
agents that produce it. Verified in the cluster:

    research -> factcheck -> analysis -> writer

**Determinism.** Across all 24 orderings of a four-agent input, the rule
yields exactly one plan. The team is a function of the deployed set, not of
the order the API server happened to list Services in.

### Observed: formation is task-independent

Two runs against the same deployed team, 23 September 2026.

**Run A** -- *"How many probe types does Kubernetes have, and how many
multi-agent failure modes are there per category on average?"*

    research -> factcheck -> analysis -> writer

Every agent contributed. `research` retrieved the probe types and the 14
failure modes and correctly declined to compute the average, noting the
corpus does not state it. `factcheck` confirmed both claims and flagged the
gap. `analysis` computed 14/3 = 4.67. `writer` synthesised.

**Run B** -- *"What is the difference between MCP and A2A, how many
capability kinds does MCP expose, and what is the default Kubernetes pod
restart backoff limit?"*

    research -> factcheck -> analysis -> writer

The identical chain. But the task required no computation, and `analysis`
said so explicitly -- *"There are no numerical values to calculate in this
case"* -- then restated its input and returned. It consumed a model call and
contributed nothing.

**The cause.** `form_team()` is a function of the deployed capability set
alone. It never sees the question. It therefore derives the same team for a
task needing arithmetic and a task needing none, because both are answered
by the same reachability argument over `consumes`/`produces`.

This is a deeper limitation than the ordering bug fixed above. Ordering was
wrong and repairable by a sort key. Task-independence is structural: the
mechanism currently answers *"which agents can be chained?"* when the useful
question is *"which agents should be, for this task?"*

A correct treatment would need the task to enter formation -- by inferring
required capability types from the request, by letting agents decline work
they cannot improve, or by treating inclusion as a cost/benefit decision
rather than a reachability one.

### Remaining open questions

1. **Task-independent formation**, as above. The most substantial of these.
2. **No notion of a good plan.** Ties break by name. Where two agents could
   both reach the goal by different routes, nothing prefers the better,
   cheaper or faster one; there is no cost or quality model.
3. **No parallelism.** Agents with no dependency between them are still
   serialised.
4. **Each agent runs at most once**, which prevents cycles bluntly rather
   than reasoning about when re-refinement would help.

(1) and (2) are the same underlying gap: the derived plan is valid,
reproducible and correctly ordered, but nothing makes it *appropriate*.

### Demonstrated with real inference

Both runs above used live model inference, not the stub. Notably, in Run B
every agent correctly reported that the pod restart backoff limit is absent
from the corpus, despite the underlying model almost certainly knowing the
value from pretraining. The corpus-only instruction held across four agents
and two protocol hops.

---

## 10. Task-aware formation, and its evaluation

### The fix

Agents declare `satisfies:<marker>` alongside their consumes/produces tags.
A task is profiled (`phase8_discovery/requirements.py`) into the markers it
raises. `form_team_targeted` searches breadth-first for the smallest agent
set that both reaches `report` and covers those markers, then orders that
set with the refiner-first rule already established. An agent earns a place
by necessity or by satisfying a marker; being runnable is no longer enough.

The writer's declaration was also loosened from `consumes:conclusions` to
`consumes:findings`. The tight version forced `analysis` into every chain,
which is what had masked task-independence.

### Evaluation

`evaluation/` holds the harness. Eighty trials: four conditions x four
deployment scenarios x five tasks. Team formation involves no inference, so
these are exact, not sampled. Ground truth (which agents each task needs)
was fixed before any result was seen.

| Condition | Precision | Recall | Team size | Source edits | Runtime failures |
|---|---|---|---|---|---|
| Static team | 0.800 | 1.000 | 3.00 | 15 | 10 |
| Derived, as first measured | 0.700 | 1.000 | 3.50 | 0 | 0 |
| Derived, looser declarations only | 0.800 | 0.956 | 3.00 | 0 | 0 |
| **Targeted (task-aware)** | **1.000** | **1.000** | **2.31** | **0** | **0** |

The two changes are held apart deliberately. Loosening declarations alone
raises precision to 0.800 but drops recall to 0.956; task-awareness is what
reaches 1.000 on both while cutting the mean team to 2.31 agents.

### The result that matters

Under `analysis-removed`, the looser-declaration condition completes 5 of 5
tasks and the task-aware condition completes 3 of 5.

The lower number is correct. The looser condition answers arithmetic
questions with a team containing no arithmetic agent and reports success;
the task-aware condition reports those two as impossible and names the
missing capability. Completing fewer tasks is better behaviour when the
alternative is failing quietly.

### Limitation

The profiler is a keyword heuristic. It keeps formation deterministic and
exactly measurable, which is why it was chosen, but it will not generalise
to unusually phrased tasks. A model-based profiler is the natural successor
and would require a different evaluation design, since composition would
cease to be exact and would have to be sampled.

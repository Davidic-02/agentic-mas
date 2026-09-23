"""Phase 8 -- a coordinator with no hardcoded team.

    python -m phase8_discovery.run "your question"          (discovers via k8s)
    DISCOVERY=static python -m phase8_discovery.run "..."   (local processes)

What happens on each run:

    1. ask the infrastructure which agents exist
    2. fetch each one's A2A card
    3. read the capabilities they declare
    4. derive a team and an order from those capabilities
    5. execute the chain, feeding each agent the previous one's output

Step 4 is the contribution. Nothing here knows the pipeline; it is
recomputed from scratch every run, against whatever is actually deployed.
"""

import contextlib
import os
import sys

from phase4_a2a.client import A2APeers
from phase4_a2a.launch import agent_services

from .discovery import get_discovery
from .formation import form_team, read_capability

BRIEF = """You have been given the following material to work with.

ORIGINAL QUESTION:
{question}

MATERIAL FROM EARLIER AGENTS:
{material}

Do your part of the work and return only your own contribution."""


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        sys.exit('usage: python -m phase8_discovery.run "your question"')

    kind = os.environ.get("DISCOVERY", "kubernetes")
    backend = os.environ.get("AGENT_BACKEND", "stub")
    static_urls = dict(
        pair.split("=", 1)
        for pair in os.environ.get("AGENT_URLS", "").split(",")
        if "=" in pair
    )

    # "local" means: start the agents here, then discover them. Convenient
    # for a first real run -- no cluster, no secret, one command.
    launcher = contextlib.nullcontext(None)
    if kind == "local":
        print("starting agents locally...")
        launcher = agent_services()

    with launcher as launched:
        if launched:
            static_urls = launched
            kind = "static"
        _run(question, kind, backend, static_urls)


def _run(question: str, kind: str, backend: str, static_urls: dict) -> None:
    # 1. who is running?
    discovery = get_discovery(kind, urls=static_urls)
    endpoints = discovery.find_agents()
    print(f"[discovery: {kind}] found {len(endpoints)} agent(s)")
    for e in endpoints:
        print(f"   {e}")
    if not endpoints:
        sys.exit("\nNo agents are running. Nothing to form a team from.")

    with A2APeers({e.name: e.url for e in endpoints}) as peers:
        # 2 + 3. what can they do? -- straight from their own cards
        capabilities = [
            read_capability(name, card)
            for name, card in peers.cards.items()
            if card is not None
        ]
        print("\n[capabilities, as declared by the agents themselves]")
        for c in capabilities:
            print(
                f"   {c.agent:11s} consumes {sorted(c.consumes) or '-'}"
                f"  produces {sorted(c.produces) or '-'}"
            )

        # 4. derive the team
        plan = form_team(capabilities)
        print(f"\n[team formed] {plan.describe()}")
        if plan.unreachable:
            print(f"[not used]    {sorted(plan.unreachable)}")
        if not plan.reached_goal:
            print("\nThe available agents cannot complete this task.")
            print("This is a result, not an error -- the plan says what is missing.")
            return

        # 5. run the chain
        print(f"\n[backend: {backend}] executing...\n")
        material = "(nothing yet)"
        for agent in plan.team:
            print(f"--> {agent}")
            result = peers.ask(agent, BRIEF.format(question=question, material=material))
            print(f"<-- {result[:100].replace(chr(10), ' ')}...\n")
            material = f"{material}\n\n--- from {agent} ---\n{result}" if material != "(nothing yet)" else f"--- from {agent} ---\n{result}"

    print("=" * 60)
    print(material)


if __name__ == "__main__":
    main()

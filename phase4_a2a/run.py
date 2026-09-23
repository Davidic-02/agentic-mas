"""Phase 4 -- the coordinator delegates over A2A.

Compare the three phases:

    phase 2:  delegate -> specialists[name].run(task)      Python call
    phase 3:  (tools moved to MCP; delegation unchanged)
    phase 4:  delegate -> peers.ask(name, task)            network protocol

The specialists now run in their own OS processes, behind HTTP, and the
coordinator reaches them by URL. It learns what each one does by reading
that agent's published card, not from anything written in this file.

Run:  python -m phase4_a2a.run "how many probe types does kubernetes have?"
"""

import contextlib
import os
import sys

from phase2_multi_agent.base import Agent
from phase2_multi_agent.coordinator import COORDINATOR_PROMPT
from phase2_multi_agent.llm import get_backend

from .client import A2APeers
from .launch import agent_services


def external_urls() -> dict[str, str] | None:
    """Agents already running elsewhere -- a cluster, say.

        AGENT_URLS="research=http://localhost:8301,analysis=http://..."

    When set, we connect to those instead of starting local subprocesses.
    The coordinator cannot tell the difference, which is the whole claim.
    """
    raw = os.environ.get("AGENT_URLS", "").strip()
    if not raw:
        return None
    return dict(pair.split("=", 1) for pair in raw.split(",") if "=" in pair)


def delegate_tool(peers: A2APeers) -> dict:
    """Build the delegate tool from the peers' own agent cards.

    Phase 2 hardcoded this list. Here the enum and the descriptions are
    assembled from what the remote agents say about themselves.
    """
    lines = []
    for name, card in peers.cards.items():
        if card is None:
            lines.append(f"- {name}")
            continue
        skills = ", ".join(s.name for s in card.skills)
        lines.append(f"- {name}: {card.description} Skills: {skills}")

    return {
        "name": "delegate",
        "description": (
            "Assign a subtask to one agent and get its result. Available "
            "agents, as advertised by their A2A agent cards:\n"
            + "\n".join(lines)
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": list(peers.cards.keys()),
                    "description": "Which agent to assign the work to.",
                },
                "task": {
                    "type": "string",
                    "description": (
                        "The full brief for that agent, including any material "
                        "it needs. It has no other context."
                    ),
                },
            },
            "required": ["agent", "task"],
            "additionalProperties": False,
        },
        "strict": True,
    }


def build_coordinator(peers: A2APeers, backend) -> Agent:
    def dispatch(name: str, tool_input: dict) -> str:
        if name != "delegate":
            return f"error: no such tool {name!r}"
        return peers.ask(tool_input["agent"], tool_input["task"])

    return Agent(
        name="coordinator",
        system_prompt=COORDINATOR_PROMPT,
        tool_schemas=[delegate_tool(peers)],
        dispatch=dispatch,
        backend=backend,
    )


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        sys.exit('usage: python -m phase4_a2a.run "your question"')

    choice = os.environ.get("AGENT_BACKEND", "stub")
    print(f"[backend: {choice}]")

    external = external_urls()
    launcher = (
        contextlib.nullcontext(external) if external else agent_services()
    )
    if external:
        print(f"using already-running agents: {list(external)}")
    else:
        print("starting agent services...")

    with launcher as urls:
        with A2APeers(urls) as peers:
            discovered = {n: [s.id for s in c.skills] for n, c in peers.cards.items() if c}
            print(f"[a2a: discovered {discovered}]\n")
            answer = build_coordinator(peers, get_backend(choice)).run(question)

    print("\n" + "=" * 60)
    print(answer)


if __name__ == "__main__":
    main()

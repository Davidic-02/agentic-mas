"""The coordinator -- the agent that decomposes the task and delegates.

Delegation is modelled as a tool call. From the coordinator's point of view
a specialist agent is simply a tool that happens to be expensive and to
think for itself. This is not a shortcut: it is what makes phase 4 cheap,
because the only thing that changes when delegation moves onto A2A is the
body of `_dispatch` below.
"""

import os
import sys

from .base import Agent
from .llm import Backend, get_backend
from .specialists import build_specialists

COORDINATOR_PROMPT = """You coordinate a team of specialist agents to answer \
a user's question. You do not have tools of your own and you do not answer \
from your own knowledge -- you work only through your team.

Your team:
- research: retrieves material from the document corpus. Give it a specific \
search brief.
- analysis: reasons and computes over material. It cannot search, so include \
the material it needs in the task you give it.
- writer: turns findings into the final answer. Give it everything that \
should appear in the answer.

Work in order: research first, then analysis if the question needs reasoning \
or arithmetic, then writer last. Pass each agent what it needs -- they share \
no memory and cannot see each other's work.

When the writer returns, reply with its output as your final answer and \
nothing else."""

# The enum below is the coordinator's view of who exists, fixed at author
# time. Phase 5 replaces this list with agents discovered at runtime.
DELEGATE_TOOL = {
    "name": "delegate",
    "description": (
        "Assign a subtask to one specialist agent and get its result. "
        "The agent sees only the task text you provide here."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "enum": ["research", "analysis", "writer"],
                "description": "Which specialist to assign the work to.",
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


def build_coordinator(backend: Backend) -> Agent:
    specialists = build_specialists(backend)

    def _dispatch(name: str, tool_input: dict) -> str:
        if name != "delegate":
            return f"error: no such tool {name!r}"
        agent = specialists.get(tool_input["agent"])
        if agent is None:
            return f"error: no such agent {tool_input['agent']!r}"
        try:
            # depth=1 just indents the sub-agent's trace in the output
            return agent.run(tool_input["task"], depth=1)
        except Exception as exc:
            # A specialist failing must not take the coordinator down --
            # it gets told, and can route around the failure.
            return f"error: {agent.name} failed: {exc}"

    return Agent(
        name="coordinator",
        system_prompt=COORDINATOR_PROMPT,
        tool_schemas=[DELEGATE_TOOL],
        dispatch=_dispatch,
        backend=backend,
    )


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        sys.exit('usage: python -m phase2_multi_agent.coordinator "your question"')

    # Default to the stub so this runs with no key and no cost.
    # Set AGENT_BACKEND=anthropic for a real model.
    choice = os.environ.get("AGENT_BACKEND", "stub")
    print(f"[backend: {choice}]\n")

    answer = build_coordinator(get_backend(choice)).run(question)
    print("\n" + "=" * 60)
    print(answer)


if __name__ == "__main__":
    main()

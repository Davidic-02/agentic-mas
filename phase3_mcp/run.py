"""Phase 3 -- the same multi-agent system, with tools reached over MCP.

Compare with phase 2. The agents, the prompts, the coordinator and the loop
are unchanged. The only difference is where tools come from:

    phase 2:  tool_schemas = TOOL_SCHEMAS      (hardcoded import)
              dispatch     = run_tool           (direct function call)

    phase 3:  tool_schemas = mcp.schemas        (discovered from the server)
              dispatch     = mcp.dispatch       (a protocol call)

That is the whole change, and it is the point: the agent did not have to
know. Anything that speaks MCP can now serve these agents' tools.

Run:  python -m phase3_mcp.run "how many probe types does kubernetes have?"
"""

import os
import sys

from phase2_multi_agent.base import Agent
from phase2_multi_agent.coordinator import COORDINATOR_PROMPT, DELEGATE_TOOL
from phase2_multi_agent.llm import get_backend
from phase2_multi_agent.specialists import (
    ANALYSIS_PROMPT,
    RESEARCH_PROMPT,
    WRITER_PROMPT,
)
from .provider import McpTools

# Which discovered tool each specialist is allowed to use. Names only --
# the schemas themselves come from the server.
TOOL_GRANTS = {
    "research": ["search_documents"],
    "analysis": ["calculate"],
    "factcheck": ["search_documents"],
    "compute": ["calculate"],
    "writer": [],
}

FACTCHECK_PROMPT = """You are a verification agent. You are given findings \
produced by another agent.

Search the corpus to check each claim. Return the findings annotated: mark \
each claim as confirmed, contradicted, or not found in the corpus. Do not \
add new claims of your own and do not remove anything -- annotate only."""

PROMPTS = {
    "research": RESEARCH_PROMPT,
    "factcheck": FACTCHECK_PROMPT,
    "compute": ANALYSIS_PROMPT,
    "analysis": ANALYSIS_PROMPT,
    "writer": WRITER_PROMPT,
}


def build_team(mcp: McpTools, backend) -> Agent:
    available = {s["name"]: s for s in mcp.schemas}

    missing = {
        name for grants in TOOL_GRANTS.values() for name in grants
    } - available.keys()
    if missing:
        # Fail loudly here rather than letting an agent discover mid-task
        # that the tool it was promised does not exist.
        raise RuntimeError(f"MCP server is missing expected tools: {sorted(missing)}")

    specialists = {
        name: Agent(
            name=name,
            system_prompt=PROMPTS[name],
            tool_schemas=[available[t] for t in grants],
            dispatch=mcp.dispatch,
            backend=backend,
        )
        for name, grants in TOOL_GRANTS.items()
    }

    def delegate(name: str, tool_input: dict) -> str:
        if name != "delegate":
            return f"error: no such tool {name!r}"
        agent = specialists.get(tool_input["agent"])
        if agent is None:
            return f"error: no such agent {tool_input['agent']!r}"
        try:
            return agent.run(tool_input["task"], depth=1)
        except Exception as exc:
            return f"error: {agent.name} failed: {exc}"

    return Agent(
        name="coordinator",
        system_prompt=COORDINATOR_PROMPT,
        tool_schemas=[DELEGATE_TOOL],
        dispatch=delegate,
        backend=backend,
    )


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        sys.exit('usage: python -m phase3_mcp.run "your question"')

    choice = os.environ.get("AGENT_BACKEND", "stub")
    print(f"[backend: {choice}]")

    with McpTools.stdio(sys.executable, "-m", "phase3_mcp.server") as mcp:
        print(f"[mcp: discovered {[s['name'] for s in mcp.schemas]}]\n")
        answer = build_team(mcp, get_backend(choice)).run(question)

    print("\n" + "=" * 60)
    print(answer)


if __name__ == "__main__":
    main()

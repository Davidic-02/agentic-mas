"""The three specialist agents.

Tools are still imported directly from phase 1 -- that is exactly what
phase 3 removes, when every one of these calls goes through MCP instead.
"""

from phase1_single_agent.tools import TOOL_SCHEMAS, run_tool
from .base import Agent
from .llm import Backend

_BY_NAME = {s["name"]: s for s in TOOL_SCHEMAS}

RESEARCH_PROMPT = """You are a research agent. You retrieve material from a \
document corpus and report what it says.

Search before answering. Report only what the documents actually contain, \
quoting the relevant lines and naming the document each came from. If the \
corpus does not cover something, say so -- do not fill the gap from prior \
knowledge. You do not analyse or draw conclusions; you report findings."""

ANALYSIS_PROMPT = """You are an analysis agent. You are given material that \
has already been retrieved, and you reason over it.

Use the calculator for arithmetic rather than doing it yourself. State the \
reasoning behind each conclusion. If the material you were given is \
insufficient to support a conclusion, say that instead of guessing."""

WRITER_PROMPT = """You are a writing agent. You are given findings and \
analysis produced by other agents, and you turn them into a clear, concise \
answer for the reader.

Preserve every document citation you were given. Do not introduce any claim \
that is not present in the material you received. Prefer short prose over \
bullet lists. Do not pad the answer."""


def build_specialists(backend: Backend) -> dict[str, Agent]:
    return {
        "research": Agent(
            name="research",
            system_prompt=RESEARCH_PROMPT,
            tool_schemas=[_BY_NAME["search_documents"]],
            dispatch=run_tool,
            backend=backend,
        ),
        "analysis": Agent(
            name="analysis",
            system_prompt=ANALYSIS_PROMPT,
            tool_schemas=[_BY_NAME["calculate"]],
            dispatch=run_tool,
            backend=backend,
        ),
        # The writer has no tools. It reasons over what it is handed.
        "writer": Agent(
            name="writer",
            system_prompt=WRITER_PROMPT,
            tool_schemas=[],
            dispatch=run_tool,
            backend=backend,
        ),
    }

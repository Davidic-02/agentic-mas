"""Run one specialist agent as an A2A service.

    python -m phase4_a2a.server research 8101

Each agent is now a standalone HTTP service that:
  * publishes its Agent Card at /.well-known/agent-card.json
  * accepts A2A task requests over JSON-RPC
  * owns its own MCP connection for tools

This is the point where "multi-agent system" stops meaning "several objects
in one Python process" and starts meaning what the project spec says.
"""

import os
import sys

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from phase2_multi_agent.base import Agent
from phase2_multi_agent.llm import get_backend
from phase3_mcp.provider import McpTools
from phase3_mcp.run import PROMPTS, TOOL_GRANTS

from .cards import build_card
from .executor import AgentExecutorAdapter


def public_url(name: str, port: int) -> str:
    """The address this agent publishes in its card.

    It must be reachable *by its peers*, which is not always the address it
    binds to. On a laptop those are the same; in a container they are not --
    the agent binds 0.0.0.0 but peers reach it by service name.
    """
    return os.environ.get("AGENT_PUBLIC_URL") or f"http://localhost:{port}/"


def build_app(name: str, port: int, backend_name: str = "stub") -> Starlette:
    mcp = McpTools.stdio(sys.executable, "-m", "phase3_mcp.server").__enter__()
    available = {s["name"]: s for s in mcp.schemas}

    agent = Agent(
        name=name,
        system_prompt=PROMPTS[name],
        tool_schemas=[available[t] for t in TOOL_GRANTS[name]],
        dispatch=mcp.dispatch,
        backend=get_backend(backend_name),
    )

    card = build_card(name, public_url(name, port))
    handler = DefaultRequestHandler(
        agent_executor=AgentExecutorAdapter(agent),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )

    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, "/")
    return Starlette(routes=routes)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: python -m phase4_a2a.server <agent-name> <port>")
    name, port = sys.argv[1], int(sys.argv[2])
    host = os.environ.get("AGENT_HOST", "127.0.0.1")
    backend = os.environ.get("AGENT_BACKEND", "stub")
    if name not in TOOL_GRANTS:
        sys.exit(f"unknown agent {name!r}; expected one of {list(TOOL_GRANTS)}")

    print(f"[{name}] binding {host}:{port}, advertising {public_url(name, port)}")
    uvicorn.run(
        build_app(name, port, backend),
        host=host,
        port=port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()

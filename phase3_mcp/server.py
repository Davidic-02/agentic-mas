"""An MCP server exposing this project's tools.

Nothing about what the tools *do* changes in phase 3 -- `search_documents`
and `calculate` are the same functions from phase 1. What changes is how an
agent reaches them.

Before:  agent  ->  python import  ->  function
After:   agent  ->  MCP client  ->  [protocol]  ->  MCP server  ->  function

The gain is that the right-hand side is now replaceable. Any MCP-speaking
agent can use these tools, and this agent can use any MCP server's tools,
without either side knowing how the other is implemented. That is the
"open standards" requirement in the project spec, made real.

Run standalone (it will wait on stdin, which is correct -- stdio transport):
    python -m phase3_mcp.server
"""

from mcp.server.mcpserver import MCPServer

from phase1_single_agent.tools import calculate as _calculate
from phase1_single_agent.tools import search_documents as _search

server = MCPServer("agentic-mas-tools")


@server.tool()
def search_documents(query: str) -> str:
    """Search the local document corpus for passages relevant to a query.

    Returns the matching documents in full. Use this before answering any
    question that depends on the corpus contents.

    Args:
        query: Keywords to search for, e.g. 'kubernetes scaling'.
    """
    return _search(query)


@server.tool()
def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression (+, -, *, /, **).

    Use this instead of doing arithmetic yourself.

    Args:
        expression: An arithmetic expression, e.g. '(17 * 3) / 4'.
    """
    return _calculate(expression)


if __name__ == "__main__":
    server.run(transport="stdio")

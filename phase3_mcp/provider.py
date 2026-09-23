"""Client side of MCP: discover tools from a server and call them.

Two jobs:

1. **Discovery.** Ask the server what tools it has, at runtime. The agent no
   longer has a hardcoded tool list -- it is told. This is the small version
   of the idea that phase 5 applies to whole agents.

2. **Bridging.** The MCP SDK is async; the agent loop is sync. Rather than
   make every agent async, this owns one event loop in a background thread
   and hands the agent an ordinary blocking `dispatch()`.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from mcp import Client, StdioServerParameters


def to_tool_schema(tool: Any) -> dict:
    """MCP tool description -> the shape our agents' backends expect."""
    schema = dict(tool.input_schema)
    schema.pop("title", None)  # pydantic artefact, not useful to a model
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
    return {
        "name": tool.name,
        "description": (tool.description or "").strip(),
        "input_schema": schema,
    }


class McpTools:
    """A live connection to an MCP server, usable as a context manager.

        with McpTools.stdio("python", "-m", "phase3_mcp.server") as tools:
            tools.schemas        # discovered, not hardcoded
            tools.dispatch("calculate", {"expression": "2+2"})
    """

    def __init__(self, target: Any) -> None:
        self._target = target
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: Client | None = None
        self._ready = threading.Event()
        self._error: BaseException | None = None
        self._shutdown: asyncio.Event | None = None
        self.schemas: list[dict] = []

    @classmethod
    def stdio(cls, command: str, *args: str) -> "McpTools":
        """Launch an MCP server as a subprocess and talk over its stdio."""
        return cls(StdioServerParameters(command=command, args=list(args)))

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> "McpTools":
        threading.Thread(target=self._thread_main, daemon=True).start()
        if not self._ready.wait(timeout=30):
            raise TimeoutError("MCP server did not become ready in 30s")
        if self._error:
            raise self._error
        return self

    def __exit__(self, *exc: object) -> None:
        if self._loop and self._shutdown:
            self._loop.call_soon_threadsafe(self._shutdown.set)

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._serve())

    async def _serve(self) -> None:
        self._shutdown = asyncio.Event()
        try:
            async with Client(self._target) as client:
                self._client = client
                listed = await client.list_tools()
                # SDKs differ on whether this is a result object or a list
                tools = getattr(listed, "tools", listed)
                self.schemas = [to_tool_schema(t) for t in tools]
                self._ready.set()
                await self._shutdown.wait()
        except BaseException as exc:  # noqa: BLE001 - surfaced to __enter__
            self._error = exc
            self._ready.set()

    # -- use ---------------------------------------------------------------

    def dispatch(self, name: str, tool_input: dict) -> str:
        """Blocking tool call. Never raises -- a failed tool is reported to
        the agent as text so it can recover, exactly as in phase 1."""
        if self._loop is None or self._client is None:
            return "error: MCP connection is not open"
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._call(name, tool_input), self._loop
            )
            return future.result(timeout=60)
        except Exception as exc:
            return f"error: MCP call {name!r} failed: {exc}"

    async def _call(self, name: str, tool_input: dict) -> str:
        result = await self._client.call_tool(name, tool_input)
        parts = [
            block.text
            for block in getattr(result, "content", [])
            if getattr(block, "type", None) == "text"
        ]
        text = "\n".join(parts).strip()
        if getattr(result, "is_error", False) or getattr(result, "isError", False):
            return f"error: {text}"
        return text

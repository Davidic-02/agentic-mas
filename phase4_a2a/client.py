"""Client side of A2A -- talk to a remote agent as a standards-conformant peer.

Mirrors `phase3_mcp.provider`: the SDK is async, the agent loop is sync, so
this owns an event loop in a background thread and hands out a blocking
`ask()`.

What matters here is what the caller needs to know about the callee:
its URL. Not its language, its framework, its prompt, or its tools. It
reads the card to learn the rest.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from typing import Any

import httpx
from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client_factory import ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, SendMessageRequest


class A2APeers:
    """Connections to a set of remote A2A agents, keyed by name.

        with A2APeers({"research": "http://localhost:8101"}) as peers:
            peers.cards["research"].skills
            peers.ask("research", "find me the probe types")
    """

    def __init__(self, urls: dict[str, str]) -> None:
        self._urls = urls
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: dict[str, Any] = {}
        self._ready = threading.Event()
        self._error: BaseException | None = None
        self._shutdown: asyncio.Event | None = None
        self.cards: dict[str, Any] = {}

    def __enter__(self) -> "A2APeers":
        threading.Thread(target=self._thread_main, daemon=True).start()
        if not self._ready.wait(timeout=30):
            raise TimeoutError("A2A peers did not connect within 30s")
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
            async with httpx.AsyncClient(timeout=120) as http:
                factory = ClientFactory(ClientConfig(httpx_client=http, streaming=False))
                for name, url in self._urls.items():
                    # Discovery, in two explicit steps: read the agent's
                    # published card, then build a client from it. The card
                    # is the only thing we know about this agent.
                    card = await A2ACardResolver(http, url).get_agent_card()

                    # A card advertises the address the agent's *peers* use.
                    # In a cluster that is a service name ("http://research:8101/"),
                    # which resolves for other pods but not from outside. When
                    # we reached the agent on a different address (a port-forward,
                    # an ingress), keep using the one that actually worked.
                    if card.supported_interfaces:
                        advertised = card.supported_interfaces[0].url
                        if not advertised.startswith(url.rstrip("/")):
                            card.supported_interfaces[0].url = url.rstrip("/") + "/"

                    self.cards[name] = card
                    self._clients[name] = factory.create(card)
                self._ready.set()
                await self._shutdown.wait()
        except BaseException as exc:  # noqa: BLE001
            self._error = exc
            self._ready.set()

    def ask(self, name: str, task: str) -> str:
        """Send a task to a remote agent and block for its answer."""
        if self._loop is None or name not in self._clients:
            return f"error: no A2A connection to {name!r}"
        try:
            future = asyncio.run_coroutine_threadsafe(self._ask(name, task), self._loop)
            return future.result(timeout=180)
        except Exception as exc:
            return f"error: A2A call to {name!r} failed: {exc}"

    async def _ask(self, name: str, task: str) -> str:
        request = SendMessageRequest(
            message=Message(
                message_id=uuid.uuid4().hex,
                role=Role.ROLE_USER,
                parts=[Part(text=task)],
            )
        )
        chunks: list[str] = []
        async for event in self._clients[name].send_message(request):
            chunks.extend(_extract_text(event))
        return "\n".join(c for c in chunks if c).strip() or "[no content returned]"


def _extract_text(event: Any) -> list[str]:
    """Pull text out of whatever the peer sent back.

    A2A responses may carry a bare Message or a Task with a history; we are
    only interested in the text parts either way.
    """
    out: list[str] = []
    msg = getattr(event, "message", None) or getattr(event, "msg", None)
    if msg is not None and getattr(msg, "parts", None):
        out.extend(p.text for p in msg.parts if p.text)
    task = getattr(event, "task", None)
    if task is not None:
        for m in list(getattr(task, "history", [])):
            if getattr(m, "role", None) == Role.ROLE_AGENT:
                out.extend(p.text for p in m.parts if p.text)
        artifacts = getattr(task, "artifacts", [])
        for a in artifacts:
            out.extend(p.text for p in getattr(a, "parts", []) if p.text)
    return out

"""The model backend, behind one small interface.

An agent needs something to think with. That something is the only part of
this system that costs money, so it is the one part we put behind an
interface: the agent loop talks to a `Backend`, and does not know or care
whether a real model or a stub is on the other side.

Two backends:

  StubBackend       -- scripted, free, offline, deterministic. Enough to
                       build and test every protocol, service and container
                       in this project.
  AnthropicBackend  -- a real model. Needed only when the agents must
                       actually reason: demos, and final evaluation runs.

Everything downstream of this file (MCP, A2A, services, Kubernetes) is
identical under either one.
"""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class Reply:
    """One turn from a model, in a shape no provider owns."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    refused: bool = False
    refusal: str = ""
    # Provider-native content, kept so a backend can echo its own history
    # back verbatim. Anthropic needs this (thinking blocks must be replayed
    # unchanged); the stub ignores it.
    raw: Any = None


class Backend(Protocol):
    def complete(
        self, *, agent: str, system: str, history: list, tools: list[dict]
    ) -> Reply: ...


# --------------------------------------------------------------------------
# Stub
# --------------------------------------------------------------------------


class StubBackend:
    """A fake model with a fixed, readable policy.

    It is not trying to be clever. It is trying to be *predictable*, so that
    when something breaks while you are building the MCP server or the
    Kubernetes deployment, you know the model is not the reason.

    Policy, in order:
      1. If the agent has a `delegate` tool, delegate to each teammate in
         turn, then stop. (This drives the whole team from the coordinator.)
      2. Otherwise, if the agent has tools and has not used one yet, call
         the first tool.
      3. Otherwise, answer with a canned summary of what it saw.
    """

    def __init__(self) -> None:
        self._ids = itertools.count(1)

    def _next_id(self) -> str:
        return f"stub_tool_{next(self._ids)}"

    def complete(
        self, *, agent: str, system: str, history: list, tools: list[dict]
    ) -> Reply:
        by_name = {t["name"]: t for t in tools}
        # How many turns this agent has already taken in this run
        taken = sum(1 for role, _ in history if role == "assistant")

        # 1. Coordinator behaviour: work through the team one at a time.
        if "delegate" in by_name:
            team = by_name["delegate"]["input_schema"]["properties"]["agent"]["enum"]
            if taken < len(team):
                target = team[taken]
                return Reply(
                    tool_calls=[
                        ToolCall(
                            id=self._next_id(),
                            name="delegate",
                            input={
                                "agent": target,
                                "task": f"[stub] {target} subtask for: {_first_user(history)}",
                            },
                        )
                    ]
                )
            return Reply(text=_collect_results(history) or "[stub] no results")

        # 2. Specialist with a tool it has not used yet.
        if tools and taken == 0:
            tool = tools[0]
            return Reply(
                tool_calls=[
                    ToolCall(
                        id=self._next_id(),
                        name=tool["name"],
                        input=_plausible_input(tool, _first_user(history)),
                    )
                ]
            )

        # 3. Nothing left to do -- report.
        seen = _collect_results(history)
        return Reply(text=f"[stub:{agent}] {seen}" if seen else f"[stub:{agent}] done")


def _first_user(history: list) -> str:
    for role, payload in history:
        if role == "user":
            return str(payload)[:120]
    return ""


def _collect_results(history: list) -> str:
    out = []
    for role, payload in history:
        if role == "tool_results":
            out.extend(str(r["content"])[:200] for r in payload)
    return " | ".join(out)


def _plausible_input(tool: dict, user_text: str) -> dict:
    """Fill a tool's required fields with something defensible.

    Keyed off the field name rather than the tool name, so a new tool with a
    `query` or `expression` field works without touching this.
    """
    props = tool["input_schema"]["properties"]
    filled = {}
    for field_name in tool["input_schema"].get("required", []):
        if field_name in ("query", "search", "q"):
            filled[field_name] = user_text
        elif field_name in ("expression", "expr"):
            filled[field_name] = "2 + 2"
        elif props.get(field_name, {}).get("enum"):
            filled[field_name] = props[field_name]["enum"][0]
        else:
            filled[field_name] = user_text
    return filled


# --------------------------------------------------------------------------
# Anthropic
# --------------------------------------------------------------------------


class AnthropicBackend:
    """The real thing. Requires ANTHROPIC_API_KEY."""

    MODEL = "claude-opus-5"

    def __init__(self, client=None, model: str | None = None) -> None:
        if client is None:
            import anthropic
            from dotenv import load_dotenv

            load_dotenv()
            client = anthropic.Anthropic()
        self.client = client
        self.model = model or self.MODEL

    def complete(
        self, *, agent: str, system: str, history: list, tools: list[dict]
    ) -> Reply:
        messages = []
        for role, payload in history:
            if role == "user":
                messages.append({"role": "user", "content": payload})
            elif role == "assistant":
                # payload is the Reply; replay its native blocks unchanged
                messages.append({"role": "assistant", "content": payload.raw})
            elif role == "tool_results":
                messages.append({"role": "user", "content": payload})

        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=messages,
            thinking={"type": "adaptive"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if tools:
            kwargs["tools"] = tools

        response = self.client.beta.messages.create(**kwargs)

        if response.stop_reason == "refusal":
            detail = getattr(response, "stop_details", None)
            return Reply(
                refused=True,
                refusal=getattr(detail, "explanation", "") or "declined",
                raw=response.content,
            )

        return Reply(
            text="".join(b.text for b in response.content if b.type == "text").strip(),
            tool_calls=[
                ToolCall(id=b.id, name=b.name, input=b.input)
                for b in response.content
                if b.type == "tool_use"
            ],
            raw=response.content,
        )


# --------------------------------------------------------------------------
# Ollama (local, free, no key)
# --------------------------------------------------------------------------


class OllamaBackend:
    """A model running on this machine, via Ollama.

    No API key, no account, no network. The tradeoff is capability: a 7B
    model is meaningfully worse at multi-step tool use than a frontier
    model, and this system is entirely multi-step tool use. Expect it to
    work, imperfectly -- which is itself worth measuring, since "can a
    small local model drive this architecture?" is a real question.

    Ollama speaks its own chat API with tool support at /api/chat.
    """

    MODEL = "qwen2.5:7b"

    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        import httpx

        self.model = model or os.environ.get("OLLAMA_MODEL") or self.MODEL
        self.host = host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
        # Local inference is slow; a long agent turn should not be cut off.
        self._http = httpx.Client(timeout=600)

    def complete(
        self, *, agent: str, system: str, history: list, tools: list[dict]
    ) -> Reply:
        messages = [{"role": "system", "content": system}]
        for role, payload in history:
            if role == "user":
                messages.append({"role": "user", "content": str(payload)})
            elif role == "assistant":
                entry: dict[str, Any] = {"role": "assistant", "content": payload.text}
                if payload.tool_calls:
                    entry["tool_calls"] = [
                        {"function": {"name": c.name, "arguments": c.input}}
                        for c in payload.tool_calls
                    ]
                messages.append(entry)
            elif role == "tool_results":
                # Ollama takes one message per tool result, and does not
                # correlate them by id -- order is the only linkage.
                for result in payload:
                    messages.append(
                        {"role": "tool", "content": str(result["content"])}
                    )

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ]

        response = self._http.post(f"{self.host}/api/chat", json=body)
        response.raise_for_status()
        message = response.json().get("message", {})

        calls = []
        for i, raw in enumerate(message.get("tool_calls") or []):
            fn = raw.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                # Some builds return the arguments as a JSON string.
                import json

                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            calls.append(
                ToolCall(id=f"ollama_{agent}_{i}", name=fn.get("name", ""), input=args)
            )

        return Reply(text=(message.get("content") or "").strip(), tool_calls=calls)


def get_backend(name: str = "stub"):
    if name == "stub":
        return StubBackend()
    if name == "anthropic":
        return AnthropicBackend()
    if name == "ollama":
        return OllamaBackend()
    raise ValueError(
        f"unknown backend {name!r} (use 'stub', 'ollama' or 'anthropic')"
    )

"""The agent loop, shared by every agent in the system.

Phase 1 had this inline to make it visible. It is the same loop, with one
change: it no longer talks to Anthropic directly. It talks to a `Backend`
(see llm.py), so the same agent runs against a free stub while you build the
protocols and the deployment, and against a real model when it has to think.
"""

from typing import Callable, Sequence

from .llm import Backend, Reply

MAX_TURNS = 12


class Agent:
    """One agent: a name, a brief, a set of tools, and the loop.

    `dispatch` is how this agent reaches the outside world. In phase 2 it
    calls Python functions; in phase 3 it will call an MCP server. The agent
    does not change when that happens -- that is the point of the split.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tool_schemas: Sequence[dict],
        dispatch: Callable[[str, dict], str],
        backend: Backend,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.tool_schemas = list(tool_schemas)
        self.dispatch = dispatch
        self.backend = backend

    def run(self, task: str, *, depth: int = 0) -> str:
        indent = "  " * depth
        print(f"{indent}[{self.name}] task: {task[:70]}")

        history: list = [("user", task)]

        for turn in range(1, MAX_TURNS + 1):
            reply: Reply = self.backend.complete(
                agent=self.name,
                system=self.system_prompt,
                history=history,
                tools=self.tool_schemas,
            )

            if reply.refused:
                return f"[{self.name} refused] {reply.refusal}"

            history.append(("assistant", reply))

            if not reply.tool_calls:
                print(f"{indent}[{self.name}] done ({turn} turn(s))")
                return reply.text

            results = []
            for call in reply.tool_calls:
                print(f"{indent}  -> {call.name}({str(call.input)[:60]})")
                output = self.dispatch(call.name, call.input)
                print(f"{indent}  <- {str(output)[:60]}")
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": output,
                        "is_error": str(output).startswith("error:"),
                    }
                )

            # All results for one turn go back together. Splitting them
            # teaches a real model to stop making parallel calls.
            history.append(("tool_results", results))

        return f"[{self.name}] hit the {MAX_TURNS}-turn limit."

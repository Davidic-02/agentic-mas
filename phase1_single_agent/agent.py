"""Phase 1 -- one agent, one visible loop.

This is written as a MANUAL agentic loop rather than with the SDK's
tool runner. The runner would collapse everything below into three lines,
which is exactly why we are not using it yet: the point of phase 1 is to
see that an "agent" is a while-loop around a chat completion that is
allowed to call functions. There is no other magic.

The loop:

    send messages  ->  Claude replies
                       |
                       +-- stop_reason == "end_turn"  -> done
                       |
                       +-- stop_reason == "tool_use"  -> run the tools,
                           append the results, send again

Run:  python -m phase1_single_agent.agent "how many documents mention MCP?"
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

from .tools import TOOL_SCHEMAS, run_tool

MODEL = "claude-opus-5"
MAX_TURNS = 10  # a runaway agent is a real failure mode -- always bound the loop

SYSTEM_PROMPT = """You are a research assistant with access to a local \
document corpus and a calculator.

Rules:
- Search the corpus before answering questions about its contents. Do not \
answer from prior knowledge and claim it came from the corpus.
- Use the calculator for arithmetic rather than computing it yourself.
- If the corpus does not contain the answer, say so plainly.
- Cite the document name you drew each claim from."""


def build_client() -> anthropic.Anthropic:
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and put your key in it."
        )
    return anthropic.Anthropic()


def run_agent(client: anthropic.Anthropic, question: str, *, verbose: bool = True) -> str:
    messages = [{"role": "user", "content": question}]

    for turn in range(1, MAX_TURNS + 1):
        if verbose:
            print(f"\n[turn {turn}] asking Claude...")

        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
            thinking={"type": "adaptive"},
            # Opus 5's safety classifiers can decline a request outright.
            # Server-side fallback reroutes those instead of returning nothing.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

        # Always check stop_reason BEFORE reading content -- on a refusal
        # there is no answer in there to read.
        if response.stop_reason == "refusal":
            detail = getattr(response, "stop_details", None)
            return f"[refused] {getattr(detail, 'explanation', 'no explanation given')}"

        # Appending the whole content list (not just the text) matters:
        # it carries the thinking blocks and tool_use blocks that the next
        # request needs to stay coherent.
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            text = "".join(b.text for b in response.content if b.type == "text")
            if verbose:
                print(f"[turn {turn}] no tool calls -- Claude is done")
            return text.strip()

        if verbose:
            print(f"[turn {turn}] Claude requested {len(tool_calls)} tool call(s)")

        # All results for one assistant turn go back in ONE user message.
        # Splitting them teaches Claude to stop making parallel calls.
        results = []
        for call in tool_calls:
            if verbose:
                print(f"   -> {call.name}({call.input})")
            output = run_tool(call.name, call.input)
            if verbose:
                preview = output.replace("\n", " ")[:80]
                print(f"   <- {len(output)} chars: {preview}...")
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": output,
                    "is_error": output.startswith("error:"),
                }
            )

        messages.append({"role": "user", "content": results})

    return f"[stopped] hit the {MAX_TURNS}-turn limit without finishing."


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        sys.exit('usage: python -m phase1_single_agent.agent "your question"')

    answer = run_agent(build_client(), question)
    print("\n" + "=" * 60)
    print(answer)


if __name__ == "__main__":
    main()

"""Bridge between A2A and our Agent class.

A2A hands us a request; we run the agent we already have; we put the result
back on the event queue. The Agent itself is untouched -- it does not know
it is being driven over a network protocol.
"""

import asyncio
import os
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part, Role

from phase2_multi_agent.base import Agent


def text_message(text: str, context_id: str = "", task_id: str = "") -> Message:
    return Message(
        message_id=uuid.uuid4().hex,
        role=Role.ROLE_AGENT,
        parts=[Part(text=text)],
        context_id=context_id,
        task_id=task_id,
    )


class AgentExecutorAdapter(AgentExecutor):
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # AGENT_HANG_SECONDS simulates an agent that is up and reachable but
        # not making progress. Its card endpoint keeps serving throughout,
        # which is the whole point: every health signal this system has says
        # the agent is fine.
        hang = float(os.environ.get("AGENT_HANG_SECONDS", "0") or 0)
        if hang:
            await asyncio.sleep(hang)

        task = context.get_user_input()
        try:
            result = self.agent.run(task)
        except Exception as exc:  # a crash here must not kill the service
            result = f"error: {self.agent.name} failed: {exc}"
        await event_queue.enqueue_event(
            text_message(result, context.context_id or "", context.task_id or "")
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            text_message(f"[{self.agent.name}] cancelled")
        )

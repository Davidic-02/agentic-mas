# One image, every agent.
#
# The agents share a codebase and differ only in the argument they are
# started with, so they share an image. This is not a shortcut -- it is why
# `kubectl scale deployment/research` works without a rebuild, and it keeps
# the registry small.

FROM python:3.11-slim

# Non-root: an agent executes model-chosen tool calls, so it should not be
# running as root inside its container.
RUN useradd --create-home --uid 10001 agent

WORKDIR /app

# Dependencies first, so edits to the source don't invalidate this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY phase1_single_agent/ ./phase1_single_agent/
COPY phase2_multi_agent/ ./phase2_multi_agent/
COPY phase3_mcp/        ./phase3_mcp/
COPY phase4_a2a/        ./phase4_a2a/
COPY phase8_discovery/  ./phase8_discovery/
COPY data/              ./data/

USER agent

# Overridden per agent by the deployment; this default makes the image
# runnable on its own for a smoke test.
ENV AGENT_NAME=research AGENT_PORT=8101 AGENT_BACKEND=stub AGENT_HOST=0.0.0.0
EXPOSE 8101

CMD ["sh", "-c", "python -m phase4_a2a.server \"$AGENT_NAME\" \"$AGENT_PORT\""]

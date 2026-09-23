# agentic-mas

Working repository for the Master's project derived from the umbrella topic:

> An Agentic Application Built Using a Multi-Agent System Based on Open
> Standards in a Cloud-Native Environment

## Specification

See [SPEC.md](SPEC.md) for the full project specification.

## Build phases

Phases 1-4 are shared by both candidate projects and are built first.

| Phase | Contents | Status |
|-------|----------|--------|
| 1 | Single agent, manual tool-calling loop | in progress |
| 2 | Coordinator + specialist agents | not started |
| 3 | Tools moved behind an MCP server | not started |
| 4 | Agent-to-agent communication over A2A | not started |

After phase 4 the work forks depending on which research question is taken.

## Setup

    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env    # then add your key to .env

## Run

    python -m phase1_single_agent.agent "your question here"

"""A2A Agent Cards -- how an agent advertises what it can do.

Skill tags carry two structured markers alongside the free-form ones:

    consumes:<type>   what this agent needs as input
    produces:<type>   what it hands back

They are ordinary A2A tags -- any A2A client ignores them harmlessly -- but
a coordinator that understands the convention can chain agents together
without being told the pipeline. See phase8_discovery/formation.py.

This is the centre of A2A. An agent publishes a card at a well-known URL,
and any caller can read it to learn the agent's name, description and
skills, without knowing anything about how it is implemented.

In phase 2 the coordinator knew its team from a hardcoded Python enum. From
here on, it can read cards instead -- which is what makes "which agents
exist" a runtime question rather than an authoring-time one.
"""

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils import TransportProtocol

SPECS = {
    "research": {
        "description": (
            "Retrieves material from a document corpus and reports what it "
            "says, with citations. Does not analyse or draw conclusions."
        ),
        "skills": [
            (
                "search_corpus",
                "Corpus search",
                "Find and return passages from the document corpus relevant "
                "to a query.",
                ["research", "retrieval", "consumes:query", "produces:findings"],
            )
        ],
    },
    "analysis": {
        "description": (
            "Reasons and computes over material it is given. Cannot retrieve "
            "anything itself -- material must be supplied in the request."
        ),
        "skills": [
            (
                "analyse",
                "Analysis and computation",
                "Compare, compute over and draw conclusions from supplied "
                "material.",
                ["analysis", "reasoning", "consumes:findings", "produces:conclusions"],
            )
        ],
    },
    "factcheck": {
        "description": (
            "Checks claims in supplied findings against the corpus and "
            "returns the findings annotated with what could be confirmed."
        ),
        "skills": [
            (
                "verify",
                "Claim verification",
                "Re-check supplied claims against the document corpus and "
                "flag anything unsupported.",
                ["verification", "consumes:findings", "produces:findings"],
            )
        ],
    },
    "writer": {
        "description": (
            "Turns findings and analysis into a clear, cited final answer. "
            "Introduces no new claims."
        ),
        "skills": [
            (
                "compose",
                "Report writing",
                "Synthesise supplied findings into a readable, cited answer.",
                ["writing", "synthesis", "consumes:conclusions", "produces:report"],
            )
        ],
    },
}


def build_card(name: str, url: str) -> AgentCard:
    spec = SPECS[name]
    return AgentCard(
        name=name,
        description=spec["description"],
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(url=url, protocol_binding=TransportProtocol.JSONRPC)
        ],
        skills=[
            AgentSkill(id=sid, name=sname, description=sdesc, tags=list(tags))
            for sid, sname, sdesc, tags in spec["skills"]
        ],
    )

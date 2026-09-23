"""Tools the agent can call.

Phase 1 keeps tools local and dependency-free. In phase 3 these same
functions move behind an MCP server, so the agent reaches them through a
standard protocol instead of a direct Python import. Keeping the logic
here (and the wiring thin) is what makes that swap cheap.
"""

import ast
import operator
import pathlib

CORPUS_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "corpus"

# --- tool implementations -------------------------------------------------

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("unsupported expression")


def calculate(expression: str) -> str:
    """Arithmetic only. Deliberately not eval() -- the agent chooses what
    goes in here, so the tool must not be able to execute arbitrary code."""
    try:
        return str(_eval_node(ast.parse(expression, mode="eval").body))
    except Exception as exc:
        return f"error: {exc}"


def search_documents(query: str) -> str:
    """Naive substring search over the local corpus.

    Naive on purpose: phase 1 is about the agent loop, not retrieval
    quality. Swap in embeddings later if the research question needs it.
    """
    if not CORPUS_DIR.exists():
        return "error: corpus directory not found"

    terms = [t for t in query.lower().split() if len(t) > 2]
    hits = []
    for path in sorted(CORPUS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        score = sum(text.lower().count(t) for t in terms)
        if score:
            hits.append((score, path.name, text.strip()))

    if not hits:
        return f"No documents matched {query!r}."

    hits.sort(reverse=True)
    return "\n\n".join(f"--- {name} (score {s}) ---\n{body}" for s, name, body in hits[:3])


# --- registry -------------------------------------------------------------
# Each entry pairs the schema Claude sees with the function we actually run.
# The schema IS the agent's interface to the world: if the description is
# vague, the agent calls the tool badly. Treat these strings as code.

TOOL_SCHEMAS = [
    {
        "name": "search_documents",
        "description": (
            "Search the local document corpus for passages relevant to a query. "
            "Returns the matching documents in full. Use this before answering "
            "any question that depends on the corpus contents."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for, e.g. 'kubernetes scaling'.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "calculate",
        "description": (
            "Evaluate an arithmetic expression (+, -, *, /, **). "
            "Use this instead of doing arithmetic yourself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "An arithmetic expression, e.g. '(17 * 3) / 4'.",
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

IMPLEMENTATIONS = {
    "search_documents": search_documents,
    "calculate": calculate,
}


def run_tool(name: str, tool_input: dict) -> str:
    """Dispatch one tool call. Never raises -- a crashed tool is reported
    back to the agent as an error string so it can recover, which is the
    whole point of returning is_error results rather than blowing up."""
    fn = IMPLEMENTATIONS.get(name)
    if fn is None:
        return f"error: no such tool {name!r}"
    try:
        return fn(**tool_input)
    except Exception as exc:
        return f"error: {name} failed: {exc}"

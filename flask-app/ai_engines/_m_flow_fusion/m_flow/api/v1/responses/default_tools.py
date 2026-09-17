"""
Default tool definitions for OpenAI-compatible API.

Defines available functions for function-calling endpoints.
"""

from __future__ import annotations

# Tool: search
_SEARCH_TOOL = {
    "type": "function",
    "name": "search",
    "description": "Query the knowledge graph for relevant information.",
    "parameters": {
        "type": "object",
        "properties": {
            "search_query": {
                "type": "string",
                "description": "Natural language query to execute.",
            },
            "recall_mode": {
                "type": "string",
                "description": "Retrieval strategy.",
                "enum": ["TRIPLET_COMPLETION", "EPISODIC", "PROCEDURAL"],
            },
            "top_k": {
                "type": "integer",
                "description": "Max results to return.",
                "default": 10,
            },
            "datasets": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by dataset names (optional).",
            },
        },
        "required": ["search_query"],
    },
}

# Tool: memorize
_MEMORIZE_TOOL = {
    "type": "function",
    "name": "memorize",
    "description": "Process text into the knowledge graph.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Content to ingest and transform.",
            },
        },
        "required": ["text"],
    },
}

# Aggregate list
DEFAULT_TOOLS: list[dict] = [
    _SEARCH_TOOL,
    _MEMORIZE_TOOL,
    # Note: prune tool excluded for safety
]

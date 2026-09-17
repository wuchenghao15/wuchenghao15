"""
Google Gemini Provider Demo

Extract entities and relationships using the Gemini Developer API.
Gemini has no mature embedder path in this repo, so pair it with an
OpenAI-compatible embedder. Requires `pip install 'hyperextract[google]'`.
Set GOOGLE_API_KEY or GEMINI_API_KEY. No real key is required to read
this file.

Usage:
    GOOGLE_API_KEY=xxx OPENAI_API_KEY=sk-xxx python examples/providers/google_demo.py
"""

from hyperextract import create_client, AutoGraph

# Gemini for LLM, OpenAI for embeddings (no Gemini embedder path here)
llm, emb = create_client(
    llm="google",  # default: gemini-3.8-flash
    embedder="openai:text-embedding-3-small",
)

graph = AutoGraph(
    instruction="Extract people and their relationships",
    llm_client=llm,
    embedder=emb,
    node_key_extractor=lambda n: n.name,
    edge_key_extractor=lambda e: (e.source, e.target, e.type),
    nodes_in_edge_extractor=lambda e: (e.source, e.target),
)

text = "Zhang San founded ByteDance. Li Si serves as CEO."
graph.parse(text)

print(f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
for n in graph.nodes:
    print(f"  - {n.name} ({n.type})")

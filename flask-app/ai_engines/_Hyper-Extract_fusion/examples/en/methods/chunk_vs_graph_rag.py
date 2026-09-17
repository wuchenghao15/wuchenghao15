"""Side-by-side chunk_rag vs graph_rag on the Tesla biography.

This is not a benchmark. CI does not run it. It needs a real LLM and
embedder key, same as the other examples/en/methods/*_demo.py scripts.

Usage:
    python examples/en/methods/chunk_vs_graph_rag.py
"""

from __future__ import annotations

import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from hyperextract.methods.rag import Chunk_RAG, Graph_RAG

project_root = Path(__file__).resolve().parent.parent.parent.parent

load_dotenv()

INPUT_FILE = project_root / "examples" / "en" / "tesla.md"
QUESTION_FILE = project_root / "examples" / "en" / "tesla_question.md"

LOOKUP_QUESTIONS = [
    "In what year was Nikola Tesla born?",
    "Where was Nikola Tesla born?",
]


def _load_questions(path: Path) -> list[str]:
    questions: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip().lstrip("-").strip()
            if cleaned:
                questions.append(cleaned)
    if not questions:
        questions = [
            "What are Tesla's major inventions and their significance?",
            "What was the War of Currents and who were the main participants?",
            "How did Tesla's relationship with Edison evolve over time?",
        ]
    # Keep both lookup and multi-hop questions on one corpus.
    merged = list(LOOKUP_QUESTIONS)
    for q in questions:
        if q not in merged:
            merged.append(q)
    return merged[:5]


def _summarize(text: str, limit: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _token_usage(message) -> str:
    usage = getattr(message, "usage_metadata", None)
    if isinstance(usage, dict) and usage:
        total = usage.get("total_tokens")
        inp = usage.get("input_tokens")
        out = usage.get("output_tokens")
        if total is not None or inp is not None or out is not None:
            return (
                f"in={inp if inp is not None else 'n/a'} "
                f"out={out if out is not None else 'n/a'} "
                f"total={total if total is not None else 'n/a'}"
            )
    meta = getattr(message, "response_metadata", None) or {}
    nested = meta.get("token_usage") or meta.get("usage") or {}
    if isinstance(nested, dict) and nested:
        total = nested.get("total_tokens") or nested.get("totalTokenCount")
        inp = (
            nested.get("prompt_tokens")
            or nested.get("input_tokens")
            or nested.get("promptTokenCount")
        )
        out = (
            nested.get("completion_tokens")
            or nested.get("output_tokens")
            or nested.get("candidatesTokenCount")
        )
        if total is not None or inp is not None or out is not None:
            return (
                f"in={inp if inp is not None else 'n/a'} "
                f"out={out if out is not None else 'n/a'} "
                f"total={total if total is not None else 'n/a'}"
            )
    return "n/a"


def _ask(ka, question: str):
    started = time.perf_counter()
    try:
        message = ka.chat(question)
        latency_s = time.perf_counter() - started
        content = getattr(message, "content", None) or str(message)
        return _summarize(str(content)), latency_s, _token_usage(message)
    except Exception as exc:
        latency_s = time.perf_counter() - started
        return f"error: {exc}", latency_s, "n/a"


if __name__ == "__main__":
    print(
        "This is not a benchmark. CI does not run this script. "
        "It needs a real LLM/embedder key."
    )

    text = INPUT_FILE.read_text(encoding="utf-8")
    questions = _load_questions(QUESTION_FILE)

    llm = ChatOpenAI(model="gpt-4o-mini")
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    print("=" * 60)
    print("chunk_rag vs graph_rag — Tesla corpus")
    print(f"source: {INPUT_FILE}")
    print("=" * 60)

    chunk = Chunk_RAG(llm_client=llm, embedder=embedder)
    t0 = time.perf_counter()
    chunk.feed_text(text, source_id="tesla.md")
    chunk.build_index()
    print(f"chunk_rag ingest+index: {time.perf_counter() - t0:.2f}s")

    graph = Graph_RAG(llm_client=llm, embedder=embedder)
    t0 = time.perf_counter()
    graph.feed_text(text, source_id="tesla.md")
    graph.build_index()
    print(
        f"graph_rag ingest+index: {time.perf_counter() - t0:.2f}s "
        f"({len(graph.nodes)} nodes, {len(graph.edges)} edges)"
    )

    for question in questions:
        print("-" * 60)
        print(f"Q: {question}")
        chunk_answer, chunk_s, chunk_tok = _ask(chunk, question)
        graph_answer, graph_s, graph_tok = _ask(graph, question)
        print(f"chunk_rag  {chunk_s:.2f}s  tokens={chunk_tok}")
        print(f"  {chunk_answer}")
        print(f"graph_rag  {graph_s:.2f}s  tokens={graph_tok}")
        print(f"  {graph_answer}")

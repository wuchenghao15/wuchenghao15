"""JSON-backed FAISS index persistence (no pickle deserialization).

Legacy ``FAISS.save_local`` writes ``index.faiss`` + ``index.pkl``; loading
the pickle executes code inside it, so a KA directory is only as safe as
its source. This module stores the raw vectors and documents as plain JSON
and rebuilds the flat index in memory on load — same search behavior, zero
code execution.

Layout (``index.json``)::

    {
      "version": 1,
      "metric": 1,              # faiss metric_type of the saved index
      "dimension": 768,
      "vectors": [[...], ...],  # one vector per item, index order
      "texts": [...],           # page_content per item
      "metadatas": [...],       # metadata per item
      "ids": [...]              # docstore ids per item
    }

Only flat indexes (as built by ``FAISS.from_documents`` with default
settings) are supported — that is what AutoModel/AutoList build.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
from langchain_community.vectorstores import FAISS

from hyperextract.utils.logging import get_logger

logger = get_logger(__name__)

INDEX_JSON_NAME = "index.json"
LEGACY_INDEX_NAME = "index.faiss"
LEGACY_PICKLE_NAME = "index.pkl"


def has_json_index(folder: str | Path) -> bool:
    """True when the folder contains a JSON index."""
    return (Path(folder) / INDEX_JSON_NAME).is_file()


def has_legacy_index(folder: str | Path) -> bool:
    """True when the folder contains a legacy pickle-based FAISS index."""
    folder = Path(folder)
    return (folder / LEGACY_INDEX_NAME).is_file() and (
        folder / LEGACY_PICKLE_NAME
    ).is_file()


def dump_index_json(index: FAISS, folder: str | Path) -> Path:
    """Persist a FAISS vector index as JSON (vectors + documents, no pickle).

    Returns the written ``index.json`` path. Legacy ``index.faiss`` /
    ``index.pkl`` files in the folder are removed after a successful write
    so a stale pickle index can never shadow the JSON one.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    ntotal = int(index.index.ntotal)
    vectors = (
        index.index.reconstruct_n(0, ntotal)
        if ntotal
        else np.zeros((0, int(index.index.d)), dtype="float32")
    )

    items = []
    for i in range(ntotal):
        doc_id = index.index_to_docstore_id[i]
        doc = index.docstore.search(doc_id)
        items.append(
            {
                "id": doc_id,
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
        )

    payload = {
        "version": 1,
        "metric": int(index.index.metric_type),
        "dimension": int(index.index.d),
        "vectors": np.asarray(vectors, dtype="float32").tolist(),
        "texts": [item["text"] for item in items],
        "metadatas": [item["metadata"] for item in items],
        "ids": [item["id"] for item in items],
    }
    path = folder / INDEX_JSON_NAME
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.info("json_index_dumped", path=str(path), items=ntotal)

    for legacy in (LEGACY_INDEX_NAME, LEGACY_PICKLE_NAME):
        stale = folder / legacy
        if stale.exists():
            stale.unlink()
            logger.info("legacy_index_removed", path=str(stale))
    return path


def load_index_json(folder: str | Path, embedder: Any) -> FAISS | None:
    """Load a JSON index and rebuild the FAISS flat index in memory.

    Returns ``None`` when the folder has no ``index.json``. Vectors are
    restored exactly as saved — no re-embedding happens.
    """
    path = Path(folder) / INDEX_JSON_NAME
    if not path.is_file():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    vectors = payload.get("vectors", [])
    texts = payload.get("texts", [])
    metadatas = payload.get("metadatas", [])
    ids = payload.get("ids", [])
    if not (len(vectors) == len(texts) == len(metadatas) == len(ids)):
        raise ValueError(f"Corrupt index.json: field lengths differ in {path}")
    if not vectors:
        raise ValueError(f"Corrupt index.json: no entries in {path}")

    metric = int(payload.get("metric", 0))
    if metric:  # only flat L2 indexes are written today
        saved = metric
        restored = 1  # faiss.METRIC_L2
        if saved != restored:
            logger.warning("json_index_metric_mismatch saved=%s rebuilt=L2", saved)

    index = FAISS.from_embeddings(
        list(zip(texts, vectors)), embedder, metadatas=metadatas, ids=ids
    )
    logger.info("json_index_loaded", path=str(path), items=len(ids))
    return index

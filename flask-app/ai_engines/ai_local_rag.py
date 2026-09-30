#!/usr/bin/env python3
"""
ai_local_rag.py — 本地 RAG 向量检索层 (零 token)
================================================
用 nomic-embed-text (Ollama 11435) 做向量化 + SQLite 存向量
把 .trae/rules/ 12篇规范 + law-codes 25份法典 向量化
推理前先 semantic search 注入相关知识到 prompt

用法:
  python3 ai_local_rag.py build     # 构建/重建知识库
  python3 ai_local_rag.py search "禁止直接云端"   # 测试检索
  python3 ai_local_rag.py status    # 看向量库状态
"""
import json, os, sys, sqlite3, time, argparse, hashlib, re
import urllib.request, urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Tuple

OLLAMA_HOST = "http://localhost:11435"
EMBED_MODEL = "nomic-embed-text"
VEC_DIM = 768

# 向量库存储 (独立 SQLite, 不污染主库)
PROJECT_ROOT = Path(__file__).parent.parent.parent
VEC_DB = PROJECT_ROOT / "flask-app" / "database" / "local_rag_vectors.db"

# 知识源目录
KNOWLEDGE_SOURCES = [
    # (目录, glob, source_type)
    (".trae/rules", "*.md", "rule_doc"),
    (".trae/skills/law-codes/references", "*.md", "law_code"),
]

# ────────────────────────────────────────────────────────────
# 向量存储操作
# ────────────────────────────────────────────────────────────

def _ensure_table(db: sqlite3.Connection):
    db.execute("""
        CREATE TABLE IF NOT EXISTS local_vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,       -- rule_doc / law_code / custom
            source_file TEXT NOT NULL,
            chunk_id TEXT NOT NULL,          -- 文件内块 hash
            chunk_text TEXT NOT NULL,
            vector BLOB NOT NULL,            -- 768 维 float32
            norm REAL DEFAULT 0,             -- 预计算 L2 norm
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_lv_source ON local_vectors(source_type)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_lv_file ON local_vectors(source_file)")

def _embed(text: str) -> Optional[List[float]]:
    """调 nomic-embed-text 本地向量化"""
    try:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/embeddings",
            data=payload, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            r = json.loads(resp.read())
        return r.get("embedding")
    except Exception as e:
        print(f"  ❌ embed fail: {e}")
        return None

def _chunk_text(text: str, max_chars: int = 800) -> List[str]:
    """按段落切块, 不超过 max_chars"""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf = [], ""
    for p in paragraphs:
        if len(buf) + len(p) + 2 <= max_chars:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf: chunks.append(buf)
            buf = p
    if buf: chunks.append(buf)
    return chunks

def _l2_norm(v: List[float]) -> float:
    return sum(x*x for x in v) ** 0.5

def _cosine_sim(a: List[float], b: List[float], norm_a: Optional[float] = None) -> float:
    if norm_a is None: norm_a = _l2_norm(a)
    nb = _l2_norm(b)
    if norm_a == 0 or nb == 0: return 0.0
    return sum(x*y for x,y in zip(a,b)) / (norm_a * nb)

# ────────────────────────────────────────────────────────────
# 构建知识库
# ────────────────────────────────────────────────────────────

def build_knowledge(force: bool = False):
    print(f"\n{'━'*56}\n  🏗️  构建本地 RAG 知识库 (nomic-embed-text 768维)\n{'━'*56}")
    
    # 验证 Ollama
    test = _embed("test")
    if not test:
        print("  ❌ nomic-embed-text 未就绪, 先 ollama pull nomic-embed-text")
        return False
    print(f"  ✅ nomic-embed-text OK ({len(test)} 维)")

    db = sqlite3.connect(str(VEC_DB))
    _ensure_table(db)

    total_before = db.execute("SELECT COUNT(*) FROM local_vectors").fetchone()[0]
    print(f"  当前向量数: {total_before}")

    # 遍历知识源
    files_processed = 0
    chunks_total = 0

    for src_dir, glob, src_type in KNOWLEDGE_SOURCES:
        full_dir = PROJECT_ROOT / src_dir
        if not full_dir.exists():
            print(f"  ⚠️  目录不存在: {src_dir}")
            continue

        for f in sorted(full_dir.glob(glob)):
            content = f.read_text(encoding="utf-8", errors="replace")
            if len(content) < 20: continue

            file_label = f"{src_dir}/{f.name}"
            print(f"  📄 {file_label} ({len(content)} chars)", end=" ")

            # 切块 + 向量化
            chunks = _chunk_text(content)
            new = 0
            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{file_label}:{i}:{chunk[:80]}".encode()).hexdigest()
                # 已存在则跳过 (幂等)
                if not force and db.execute(
                    "SELECT 1 FROM local_vectors WHERE chunk_id=?", (chunk_id,)
                ).fetchone():
                    continue

                emb = _embed(chunk)
                if not emb: continue
                norm = _l2_norm(emb)
                blob = sqlite3.Binary(json.dumps(emb).encode())
                db.execute("""
                    INSERT OR REPLACE INTO local_vectors
                    (source_type, source_file, chunk_id, chunk_text, vector, norm)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (src_type, file_label, chunk_id, chunk[:2000], blob, norm))
                new += 1

            db.commit()
            chunks_total += len(chunks)
            files_processed += 1
            print(f"→ {len(chunks)} 块 ({new} 新增)")

    total_after = db.execute("SELECT COUNT(*) FROM local_vectors").fetchone()[0]
    db.close()

    print(f"\n  📊 构建完成:")
    print(f"     文件: {files_processed} 个")
    print(f"     块数: {chunks_total}")
    print(f"     向量: {total_before} → {total_after} (+{total_after-total_before})")
    print(f"     存储: {VEC_DB} ({VEC_DB.stat().st_size//1024}KB)")
    return True

# ────────────────────────────────────────────────────────────
# 检索
# ────────────────────────────────────────────────────────────

def search(query: str, top_k: int = 5, source_filter: Optional[str] = None) -> List[Dict]:
    """semantic search, 返回 top_k 最相关的知识块"""
    db = sqlite3.connect(str(VEC_DB))
    emb_q = _embed(query)
    if not emb_q:
        db.close(); return []
    norm_q = _l2_norm(emb_q)

    sql = "SELECT id, source_type, source_file, chunk_text, vector, norm FROM local_vectors"
    params = []
    if source_filter:
        sql += " WHERE source_type=?"
        params.append(source_filter)

    rows = db.execute(sql, params).fetchall()
    db.close()

    results = []
    for rid, stype, sfile, chunk, vblob, vnorm in rows:
        try:
            vec = json.loads(bytes(vblob))
            sim = _cosine_sim(emb_q, vec, norm_q)
            results.append({
                "id": rid, "score": round(sim, 4),
                "source_type": stype, "source_file": sfile,
                "text": chunk,
            })
        except: pass

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def build_context(query: str, top_k: int = 3) -> str:
    """把检索结果格式化成 system prompt 可注入的上下文"""
    hits = search(query, top_k=top_k)
    if not hits: return ""
    lines = ["[本地知识检索 (零 token)]"]
    for h in hits:
        if h["score"] < 0.3: break  # 相关性太低就不注入
        lines.append(f"- [{h['source_file']}] (sim={h['score']:.2f}) {h['text'][:300]}")
    return "\n".join(lines)

def status() -> Dict:
    db = sqlite3.connect(str(VEC_DB))
    total = db.execute("SELECT COUNT(*) FROM local_vectors").fetchone()[0]
    by_type = db.execute("SELECT source_type, COUNT(*) FROM local_vectors GROUP BY source_type").fetchall()
    db.close()
    ollama_ok = _embed("ok") is not None
    return {
        "total_vectors": total,
        "by_type": dict(by_type),
        "ollama_embed_ok": ollama_ok,
        "embed_model": EMBED_MODEL,
        "vec_dim": VEC_DIM,
        "db_path": str(VEC_DB),
    }

# ────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="本地 RAG 向量层")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("build")
    sub.add_parser("status")
    sp = sub.add_parser("search"); sp.add_argument("query", nargs="+")
    args = p.parse_args()

    if args.cmd == "build":
        build_knowledge(force=False)
    elif args.cmd == "status":
        s = status()
        print(json.dumps(s, indent=2, ensure_ascii=False))
    elif args.cmd == "search":
        q = " ".join(args.query)
        hits = search(q, top_k=5)
        print(f"\n🔍 Query: '{q}' → {len(hits)} 命中\n")
        for h in hits:
            print(f"  [{h['score']:.2f}] {h['source_file']}")
            print(f"    {h['text'][:150]}...\n")
    else:
        p.print_help()

if __name__ == "__main__": main()

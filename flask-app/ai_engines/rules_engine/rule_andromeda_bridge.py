"""
规则引擎 ↔ 仙女座引擎 桥接模块
================================

MT_RULE_VERSION §3.2 / §3.3 强制要求的双向闭环代码实现:

  规则修改 ──→ ingest_rules_to_knowledge() ──→ mt_andromeda_rule_knowledge
  rule_knowledge 增量 ──→ _auto_bump_from_events() ──→ 自动版本 bump
  版本 bump ──→ trigger_evolution_rule_refresh() ──→ mt_ai_self_evolution_log
  双端同步 ──→ check_version_diff() ──→ 版本差拦截 (≥ major 跳过 rsync)

这个模块**不是可选**的 —— 它是仙女座引擎遵守 §14 IRON_RULE 的唯一代码入口。
autosync_andromeda / andromeda_auto_evolution / rules_engine daemon 都**必须**调用这里的函数。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple


# ── 路径常量 ────────────────────────────────────────────────────────────────

def _project_root() -> str:
    """MTSCOS 项目根 (flask-app/)"""
    return os.path.dirname(os.path.abspath(__file__)) + "/../.."


def _db_path() -> str:
    return os.path.join(_project_root(), "database", "app.db")


def _rules_dir() -> str:
    """规则文件目录 (.trae/rules/)"""
    return os.path.join(_project_root(), "..", ".trae", "rules")


def _ver_path() -> str:
    return os.path.join(_project_root(), "VERSION")


# ── 1. RULES → rule_knowledge 自动 ingest ──────────────────────────────────
# MT_RULE_VERSION §3.2 / AI系统操作规范 (仙女座 AI 员工与脑库联动)

def _parse_rule_meta(md_content: str) -> dict:
    """解析 RULE_META 块, 返回 {rule_id, rule_level, rule_version, status, is_iron_rule}"""
    meta = {
        "rule_id": "UNKNOWN",
        "rule_level": "L2",
        "rule_version": "v1.0.0",
        "status": "ACTIVE",
        "is_iron_rule": 0,
    }
    # 匹配 <!-- RULE_META_START ... RULE_META_END --> 块
    m = re.search(r"<!-- RULE_META_START\s*(.*?)\s*RULE_META_END -->",
                 md_content, re.DOTALL)
    if not m:
        return meta
    block = m.group(1)
    for line in block.split("\n"):
        line = line.strip()
        if line.startswith("RULE_ID:"):
            meta["rule_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("RULE_LEVEL:"):
            meta["rule_level"] = line.split(":", 1)[1].strip()
        elif line.startswith("RULE_VERSION:"):
            meta["rule_version"] = line.split(":", 1)[1].strip()
        elif line.startswith("STATUS:"):
            meta["status"] = line.split(":", 1)[1].strip()
    # IRON_RULE 判定
    meta["is_iron_rule"] = 1 if meta["rule_level"] == "L0 IRON_RULE" else 0
    return meta


def _chunk_content(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    """按段落切分规则内容为分块, 保持语义完整"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    cur = ""
    for p in paragraphs:
        if len(cur) + len(p) + 2 > max_chars and cur:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + "\n\n" + p).strip() if cur else p
    if cur:
        chunks.append(cur)
    return chunks or [text[:max_chars]]


def ingest_rules_to_knowledge(
    rules_dir: Optional[str] = None,
    force: bool = False,
) -> dict:
    """扫描 .trae/rules/*.md → 分块写入 mt_andromeda_rule_knowledge.

    Args:
        rules_dir: 规则目录, 默认自动检测 .trae/rules/
        force: True=重 ingest 所有; False=只处理 7d 内新增或 rule_version 变更的

    Returns:
        {'ingested': int, 'skipped': int, 'errors': int, 'rule_ids': [...]}
    """
    rules_dir = rules_dir or _rules_dir()
    result = {"ingested": 0, "skipped": 0, "errors": 0, "rule_ids": []}

    if not os.path.isdir(rules_dir):
        print(f"[bridge] ingest_rules: 规则目录不存在 {rules_dir}")
        return result

    try:
        c = sqlite3.connect(_db_path(), timeout=15)
    except Exception as exc:
        print(f"[bridge] ingest_rules: DB 连接失败 {exc}")
        result["errors"] = 1
        return result

    # 确保表存在
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS mt_andromeda_rule_knowledge (
                rule_chunk_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id          TEXT NOT NULL,
                rule_name        TEXT NOT NULL,
                rule_level       TEXT,
                rule_version     TEXT,
                status           TEXT,
                depends_on       TEXT,
                effective_date   TEXT,
                section_header   TEXT,
                content_chunk    TEXT NOT NULL,
                chunk_index      INTEGER DEFAULT 0,
                keyword_tags     TEXT,
                is_iron_rule     INTEGER DEFAULT 0,
                last_ingested    TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
    except Exception:
        pass

    # 扫描所有 .md 规则文件
    for fname in sorted(os.listdir(rules_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(rules_dir, fname)
        with open(fpath, encoding="utf-8", errors="replace") as f:
            content = f.read()

        meta = _parse_rule_meta(content)
        rule_id = meta["rule_id"]
        rule_name = fname.replace(".md", "")

        # 没 RULE_META 的跳过
        if rule_id == "UNKNOWN":
            result["skipped"] += 1
            continue

        # 检查是否需要 re-ingest
        if not force:
            row = c.execute(
                "SELECT rule_version FROM mt_andromeda_rule_knowledge "
                "WHERE rule_id=? LIMIT 1",
                (rule_id,),
            ).fetchone()
            if row and row[0] == meta["rule_version"]:
                result["skipped"] += 1
                continue

        # 删掉旧分块 (同一 rule_id)
        c.execute("DELETE FROM mt_andromeda_rule_knowledge WHERE rule_id=?", (rule_id,))

        # 按 ## 标题分段 + chunking
        sections = re.split(r"\n(?=## )", content)
        chunk_index = 0
        for sec in sections:
            # 跳过 RULE_META 块
            if "RULE_META_START" in sec and "RULE_META_END" in sec:
                continue
            sec_header_match = re.search(r"^##+\s+(.+)", sec)
            sec_header = sec_header_match.group(1).strip() if sec_header_match else rule_name

            for chunk in _chunk_content(sec):
                # 关键词提取: 强制约束词 + rule_id
                force_words = re.findall(
                    r"(必须|不得|禁止|强制|铁律|不得绕过|fail-closed|仙女座|evolution|bump|版本)",
                    chunk,
                )
                tags = sorted(set(force_words + [rule_id]))[:12]

                try:
                    c.execute(
                        """
                        INSERT INTO mt_andromeda_rule_knowledge
                        (rule_id, rule_name, rule_level, rule_version, status,
                         section_header, content_chunk, chunk_index,
                         keyword_tags, is_iron_rule, last_ingested)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        """,
                        (
                            rule_id, rule_name, meta["rule_level"], meta["rule_version"],
                            meta["status"], sec_header, chunk, chunk_index,
                            json.dumps(tags, ensure_ascii=False), meta["is_iron_rule"],
                        ),
                    )
                    chunk_index += 1
                except Exception as exc:
                    result["errors"] += 1
                    print(f"[bridge] ingest_rules: {rule_id} chunk {chunk_index} 失败: {exc}")

        if chunk_index > 0:
            result["ingested"] += 1
            result["rule_ids"].append(rule_id)
        c.commit()

    c.close()
    print(
        f"[bridge] ingest_rules_to_knowledge: "
        f"ingested={result['ingested']} skipped={result['skipped']} "
        f"errors={result['errors']} (rule_ids={','.join(result['rule_ids'][:5])}...)"
    )
    return result


# ── 2. 规则修改 → evolution_log 触发仙女座 ──────────────────────────────────
# MT_RULE_VERSION §3.2 / §4 闭环

def trigger_evolution_rule_refresh(
    rule_id: str = "ALL",
    reason: str = "rule_ingest_trigger",
) -> bool:
    """规则 ingest 后 → 写 mt_ai_self_evolution_log → 仙女座感知.

    仙女座 auto_evolution 扫 evolution_log trigger_type='rule_ingest_trigger'
    → 重读 VERSION + rule_knowledge → 调整演化策略.
    """
    try:
        c = sqlite3.connect(_db_path(), timeout=10)
        c.execute(
            """
            INSERT INTO mt_ai_self_evolution_log
            (trigger_type, target_task, rationale, created_at)
            VALUES ('rule_ingest_trigger', ?,
                    ?, datetime('now','localtime'))
            """,
            (
                f"rule_knowledge_refresh:{rule_id}",
                f"规则变更触发仙女座刷新: {reason} ({rule_id})",
            ),
        )
        c.commit()
        c.close()
        print(f"[bridge] trigger_evolution_rule_refresh: rule_id={rule_id} reason={reason}")
        return True
    except Exception as exc:
        print(f"[bridge] trigger_evolution_rule_refresh 失败: {exc}")
        return False


# ── 3. autosync 版本差拦截 ──────────────────────────────────────────────────
# MT_RULE_VERSION §3.3 仙女座版本感知 / 系统操作规范 仙女座守护进程管理

def check_version_diff(
    local_version: Optional[str] = None,
    remote_version: Optional[str] = None,
    db_path: Optional[str] = None,
) -> dict:
    """检查两端版本差, 判断是否允许 rsync.

    Returns:
        {
            'allow_sync': bool,
            'block_reason': str | None,
            'local_version': str,
            'remote_version': str,
            'major_diff': bool,
            'minor_diff': bool,
        }
    """
    result = {
        "allow_sync": True,
        "block_reason": None,
        "local_version": local_version or "unknown",
        "remote_version": remote_version or "unknown",
        "major_diff": False,
        "minor_diff": False,
    }

    # 读本地 VERSION
    if not local_version:
        if os.path.exists(_ver_path()):
            result["local_version"] = open(_ver_path()).read().strip()

    # 读远端 VERSION (如果没传, 去 DB 找 remote 记录)
    if not remote_version:
        try:
            c = sqlite3.connect(db_path or _db_path(), timeout=5)
            row = c.execute(
                "SELECT value FROM mt_system_config WHERE key='remote_version'"
            ).fetchone()
            if row:
                result["remote_version"] = row[0]
            c.close()
        except Exception:
            pass

    # 比较版本
    def _parse_ver(v: str) -> Tuple[int, int, int]:
        v = v.lstrip("v")
        parts = v.split(".")
        return (
            int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0,
            int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
            int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
        )

    try:
        lm, ln, lp = _parse_ver(result["local_version"])
        rm, rn, rp = _parse_ver(result["remote_version"])
    except Exception:
        return result

    if lm != rm:
        result["major_diff"] = True
        result["allow_sync"] = False
        result["block_reason"] = (
            f"Major version difference (local={result['local_version']} "
            f"vs remote={result['remote_version']}) — 禁止跨 major rsync, "
            f"避免 schema 不兼容"
        )
    elif ln != rn:
        result["minor_diff"] = True
        # minor diff 允许同步非核心文件, 但必须 warn
        result["block_reason"] = (
            f"Minor version difference ({result['local_version']} vs {result['remote_version']}) "
            f"— 降级同步 (跳过规则文件)"
        )

    return result


# ── 4. daemon 自动触发的 rule_knowledge 健康检查 ─────────────────────────────
# sys_rule_enforcer 每 300s 调一次

def rule_knowledge_health_check() -> dict:
    """检查 rule_knowledge 是否覆盖所有规则, 缺了就自动补.

    Returns:
        {'covered': int, 'missing': [...], 'auto_ingested': int}
    """
    result = {"covered": 0, "missing": [], "auto_ingested": 0}

    rules_dir = _rules_dir()
    if not os.path.isdir(rules_dir):
        return result

    # DB 中已覆盖的 rule_id
    try:
        c = sqlite3.connect(_db_path(), timeout=5)
        covered_ids = {
            r[0] for r in c.execute(
                "SELECT DISTINCT rule_id FROM mt_andromeda_rule_knowledge"
            ).fetchall()
        }
        c.close()
    except Exception:
        covered_ids = set()

    # 扫描磁盘上所有规则文件
    disk_ids = set()
    for fname in os.listdir(rules_dir):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(rules_dir, fname), encoding="utf-8", errors="replace") as f:
            content = f.read()
        meta = _parse_rule_meta(content)
        if meta["rule_id"] != "UNKNOWN":
            disk_ids.add(meta["rule_id"])

    result["covered"] = len(disk_ids & covered_ids)
    result["missing"] = sorted(disk_ids - covered_ids)

    # 有缺失 → 自动补
    if result["missing"]:
        ing = ingest_rules_to_knowledge(force=False)
        result["auto_ingested"] = ing["ingested"]

    return result


# ── 5. 仙女座版本感知钩子 ──────────────────────────────────────────────────
# 仙女座 auto_evolution 启动时调用

def andromeda_version_check(minimum_version: str = "v22.0.0") -> dict:
    """仙女座 auto_evolution 启动时的版本感知.

    Returns:
        {'ok': bool, 'version': str, 'minimum': str, 'too_old': bool}
    """
    cur = "unknown"
    if os.path.exists(_ver_path()):
        cur = open(_ver_path()).read().strip()

    def _parse(v: str) -> Tuple[int, int, int]:
        v = v.lstrip("v")
        parts = v.split(".")
        return (
            int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0,
            int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
            int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
        )

    try:
        cm, cn, _ = _parse(cur)
        mm, mn, _ = _parse(minimum_version)
        too_old = (cm, cn) < (mm, mn)
    except Exception:
        too_old = False

    if too_old:
        # 写 evolution_log: 版本过旧, 跳过演化
        try:
            c = sqlite3.connect(_db_path(), timeout=5)
            c.execute(
                """INSERT INTO mt_ai_self_evolution_log
                   (trigger_type, target_task, rationale, created_at)
                   VALUES ('version_too_old', 'auto_evolution',
                           ?, datetime('now','localtime'))""",
                (f"系统版本 {cur} < minimum {minimum_version} — 跳过 auto_evolution",),
            )
            c.commit()
            c.close()
        except Exception:
            pass

    return {
        "ok": not too_old,
        "version": cur,
        "minimum": minimum_version,
        "too_old": too_old,
    }


# ── 6. 一键 CLI 入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "ingest":
        force = "--force" in sys.argv
        r = ingest_rules_to_knowledge(force=force)
        print(f"\n✅ ingest_rules_to_knowledge: {r['ingested']} rule_ids, {r['skipped']} skipped")
        for rid in r["rule_ids"]:
            print(f"  + {rid}")

    elif cmd == "health":
        r = rule_knowledge_health_check()
        print(f"\n✅ rule_knowledge_health_check: covered={r['covered']}, missing={r['missing']}")

    elif cmd == "version":
        r = andromeda_version_check()
        print(f"\n✅ andromeda_version_check: version={r['version']}, ok={r['ok']}, too_old={r['too_old']}")

    elif cmd == "diff":
        r = check_version_diff()
        print(f"\n✅ check_version_diff: allow={r['allow_sync']}, reason={r['block_reason']}")

    elif cmd == "trigger":
        rid = sys.argv[2] if len(sys.argv) > 2 else "ALL"
        trigger_evolution_rule_refresh(rule_id=rid)

    elif cmd == "all":
        print("=== Step 1: ingest rules ===")
        ingest_rules_to_knowledge(force=False)
        print("\n=== Step 2: health check ===")
        rule_knowledge_health_check()
        print("\n=== Step 3: trigger evolution refresh ===")
        trigger_evolution_rule_refresh()
        print("\n=== Step 4: version check ===")
        andromeda_version_check()

    else:
        print("Usage:")
        print("  python rule_andromeda_bridge.py ingest [--force]")
        print("  python rule_andromeda_bridge.py health")
        print("  python rule_andromeda_bridge.py version")
        print("  python rule_andromeda_bridge.py diff")
        print("  python rule_andromeda_bridge.py trigger [rule_id]")
        print("  python rule_andromeda_bridge.py all")

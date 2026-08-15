#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 数据库加密分批迁移器（真实路径版 — 2026-08-13）
===================================================
flow_id: flow_db_encrypt_20260813_001

真实数据布局：
  - flask-app/app.db             : 614表 / 1.9GB (主库 ✅ 核心)
  - flask-app/shadow_system.db   : 427表 / 933MB (影子库)
  - flask-app/sandbox_system.db  : 427表 / 933MB (沙盒库)
  - flask-app/ai_engines/*.db    : 若干AI子库（ai_brain/ai_learning等）
  - flask-app/Database/*.db      : 分片镜像（可由主库派生）
  - flask-app/split_databases/   : 空/小分片（非主数据）

迁移策略：对每个库按"表内字段级加密 + 文件名混淆"执行，避免整库拷贝（1.9GB 耗时）。
  ① 备份原库 (文件副本)
  ② 扫描所有表 → 按 classify_table() 判定等级
  ③ 逐表：
     - L0 极密：表名映射 + 列名映射 + TEXT/JSON 字段 AES-256-GCM 加密
     - L1 机密：TEXT/JSON 字段 AES-256-GCM 加密
     - L2 秘密：TEXT 字段加密（可选，大字段优先）
     - L3 内部：跳过字段级，仅后续文件混淆
     - L4 公开：跳过
  ④ 迁移后行数一致性校验
  ⑤ 明文库 .archived → 原位置保留迁移后的库
  ⑥ 文件名混淆（L0/L1/L2/L3）

安全原则（经验1210180）：永远先备份，永远可回滚，永远逐表验证。
"""

import os
import sys
import json
import shutil
import hashlib
import sqlite3
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db_encryption import (
    DatabaseEncryption, EncryptionLevel, LEVEL_CAPABILITY,
    classify_table, DEFAULT_CLASSIFICATION
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("db_migration")

# 强制 log flush：给 logger 加 flush handler
class _ForceFlush(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


for h in logger.handlers[:]:
    logger.removeHandler(h)
_handler = _ForceFlush(sys.stdout)
_handler.setFormatter(logging.Formatter(
    "[%(asctime)s][%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
))
logger.addHandler(_handler)
logger.propagate = False

enc = DatabaseEncryption()

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(
    ROOT, "_migration_backups", datetime.now().strftime("%Y%m%d_%H%M%S")
)
REPORT_DIR = os.path.join(ROOT, "_migration_reports")
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def _is_real_sqlite(path: str) -> bool:
    try:
        if not os.path.isfile(path) or os.path.getsize(path) < 1024:
            return False
        with open(path, "rb") as f:
            header = f.read(16)
        return header.startswith(b"SQLite format 3")
    except Exception:
        return False

# ============== 真实目标库 ==============
TARGET_DATABASES_RAW: Dict[str, str] = {
    "app": os.path.join(ROOT, "app.db"),
    "shadow": os.path.join(ROOT, "shadow_system.db"),
    "sandbox": os.path.join(ROOT, "sandbox_system.db"),
    "ai_brain": os.path.join(ROOT, "ai_engines", "ai_brain.db"),
    "ai_learning": os.path.join(ROOT, "ai_engines", "ai_learning.db"),
    "ai_system": os.path.join(ROOT, "ai_engines", "ai_system.db"),
    "ai_performance": os.path.join(ROOT, "ai_engines", "ai_performance.db"),
    "ai_anomaly": os.path.join(ROOT, "ai_engines", "ai_anomaly.db"),
    "ai_auto_mgmt": os.path.join(ROOT, "ai_engines", "ai_auto_management.db"),
    "ai_pool_pollution": os.path.join(ROOT, "ai_engines", "ai_pool_pollution.db"),
    "ai_engine_upgrades": os.path.join(ROOT, "ai_engines", "ai_engine_upgrades.db"),
    "ai_self_improvement": os.path.join(ROOT, "ai_engines", "ai_self_improvement.db"),
    "ai_logs": os.path.join(ROOT, "ai_engines", "ai_logs.db"),
    "ai_collab": os.path.join(ROOT, "app", "ai", "ai_collaboration.db"),
    "ai_skill_evo": os.path.join(ROOT, "app", "ai", "skill_evolution.db"),
    "ai_self_learning": os.path.join(ROOT, "app", "ai", "self_learning.db"),
    "ai_decision": os.path.join(ROOT, "app", "ai", "decision_support.db"),
    "data_security": os.path.join(ROOT, "data", "security_engineer.db"),
}

# 过滤：仅保留真实 SQLite
TARGET_DATABASES = {
    k: v for k, v in TARGET_DATABASES_RAW.items() if _is_real_sqlite(v)
}

MIGRATION_REPORT: Dict = {
    "flow_id": "flow_db_encrypt_20260813_001",
    "started_at": datetime.now().isoformat(),
    "databases": {},
    "errors": [],
    "backup_dir": BACKUP_DIR,
}

# ===============================================================
# 工具函数
# ===============================================================

def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _backup(db_key: str, db_path: str) -> Optional[str]:
    if not os.path.exists(db_path):
        return None
    safe_key = db_key.replace(os.sep, "_")
    backup_path = os.path.join(BACKUP_DIR, f"{safe_key}.bak.db")
    logger.info(f"[{db_key}] 备份 {db_path} ({os.path.getsize(db_path):,}字节) → {backup_path} ...")
    sys.stdout.flush()

    total = os.path.getsize(db_path)
    copied = 0
    last_pct = -1
    try:
        with open(db_path, "rb") as src, open(backup_path, "wb") as dst:
            while True:
                chunk = src.read(8 * 1024 * 1024)   # 8MB chunks
                if not chunk:
                    break
                dst.write(chunk)
                copied += len(chunk)
                if total > 0:
                    pct = int(copied * 100 / total)
                    if pct != last_pct and pct % 10 == 0:
                        last_pct = pct
                        mbytes = copied / (1024 * 1024)
                        sys.stdout.write(f"  ... {db_key} backup {pct}% ({mbytes:.0f}MB)\n")
                        sys.stdout.flush()
        logger.info(f"[{db_key}] 备份完成，md5={_md5(backup_path)}")
        sys.stdout.flush()
        return backup_path
    except Exception as e:
        logger.error(f"[{db_key}] 备份失败: {e}")
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                pass
        return None


def _list_tables(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    cur = conn.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return cur.fetchall()


def _get_columns(conn: sqlite3.Connection, table: str) -> List[sqlite3.Row]:
    prev = conn.row_factory
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({_quote(table)})")
    res = cur.fetchall()
    conn.row_factory = prev
    return res


def _find_constrained_columns(create_sql: str) -> set:
    """从 CREATE TABLE SQL 中找出受约束的列（CHECK/IN/枚举/FK），此类列不可加密

    识别模式：
      - col CHECK (col IN ('a','b','c'))
      - CHECK (col IN (...))
      - col TYPE CHECK (col = 'x' OR col = 'y')
      - FOREIGN KEY (col) REFERENCES ...
    返回：列名集合(小写)
    """
    constrained: set = set()
    if not create_sql:
        return constrained
    s = create_sql

    # CHECK( col IN ('x','y',...) )
    import re
    for m in re.finditer(r"CHECK\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s+IN\s*\(", s, re.I):
        constrained.add(m.group(1).lower())
    # col [CONSTRAINT name] CHECK (col IN (...) / col = 'x' OR ...)
    # 简化：取 CHECK 括号表达式中出现的列名作为候选
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s+(?:[A-Za-z0-9_() ]+\s+)?CHECK\s*\(([^)]+)\)", s, re.I):
        constrained.add(m.group(1).lower())
        # 表达式内可能的列
        for mm in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", m.group(2)):
            if mm.upper() not in ("IN", "AND", "OR", "NOT", "NULL", "LIKE", "IS", "TRUE", "FALSE"):
                constrained.add(mm.lower())
    # FOREIGN KEY
    for m in re.finditer(r"FOREIGN\s+KEY\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", s, re.I):
        constrained.add(m.group(1).lower())
    return constrained


# ===============================================================
# 单表迁移（在同一连接内做"建新→搬数据→删旧→改名"）
# ===============================================================

def _migrate_one_table_inplace(db_key: str, conn: sqlite3.Connection,
                                table: str, create_sql: str,
                                report: Dict) -> bool:
    """原地迁移单表：建临时表(加密)→搬数据→删旧→重命名"""
    level = classify_table(table)
    cap = LEVEL_CAPABILITY[level]

    # L4 公开 → 跳过
    if level == EncryptionLevel.L4_PUBLIC:
        report["skipped_l4"] += 1
        return True

    cols = _get_columns(conn, table)
    if not cols:
        return True

    # 识别 CHECK / IN / FK 约束列 → 不加密
    constrained_cols = _find_constrained_columns(create_sql)
    if cap.get("content_encrypt"):
        already_encrypted = False
        text_cols = [c["name"] for c in cols if
                     not c["type"]
                     or "TEXT" in c["type"].upper()
                     or "CHAR" in c["type"].upper()
                     or "VARCHAR" in c["type"].upper()]
        if text_cols:
            checks = " OR ".join(f"{_quote(c)} LIKE 'MTENC:%'" for c in text_cols[:5])
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT 1 FROM {_quote(table)} WHERE {checks} LIMIT 1")
                if cur.fetchone() is not None:
                    report["tables_already_encrypted"] = report.get("tables_already_encrypted", 0) + 1
                    return True
            except Exception:
                pass

    # 逻辑→物理列名映射（L0才重命名列）
    col_phys: List[str] = []
    col_phys_to_logical: Dict[str, str] = {}
    for c in cols:
        logical = c["name"]
        if cap.get("column_name_map"):
            phys = enc.schema_mapper.logical_to_physical_column(table, logical)
        else:
            phys = logical
        col_phys.append(phys)
        col_phys_to_logical[phys] = logical

    # 逻辑→物理表名（L0才重命名表）
    if cap.get("table_name_map"):
        physical_table = enc.schema_mapper.logical_to_physical_table(table)
    else:
        physical_table = table

    # 临时表名：物理名 + 表名hash后缀，确保"原表名/物理表名/已映射t_表名"不撞名
    table_hash = hashlib.md5(table.encode("utf-8")).hexdigest()[:8]
    tmp_table = f"_mt_tmp_{physical_table}_{table_hash}"

    # 防御：迁移前清理同名单独残余临时表（异常中断遗留）
    try:
        conn.execute(f'DROP TABLE IF EXISTS {_quote(tmp_table)}')
        conn.commit()
    except Exception:
        pass

    # 建临时表 DDL
    new_ddl = _rewrite_create(create_sql, table, tmp_table, col_phys, cols)

    try:
        conn.execute(new_ddl)
    except Exception as e:
        logger.warning(f"  [{db_key}.{table}] 建表失败(尝试简化DDL): {e}")
        # 简化：手工拼 CREATE TABLE
        col_defs = []
        pk_cols = [cols[i]["name"] for i in range(len(cols)) if cols[i]["pk"]]
        for i in range(len(cols)):
            c = cols[i]
            col_def = f"{_quote(col_phys[i])} {c['type']}"
            col_def += " NOT NULL" if c["notnull"] else ""
            # 单主键才内联 PRIMARY KEY，复合主键走表级约束
            if c["pk"] and len(pk_cols) == 1:
                col_def += " PRIMARY KEY"
            col_defs.append(col_def)
        # 复合主键：加表级 PRIMARY KEY 约束
        if len(pk_cols) > 1:
            phys_pk = [col_phys[cols.index(next(x for x in cols if x["name"] == n))]
                       for n in pk_cols]
            col_defs.append(f"PRIMARY KEY ({','.join(_quote(p) for p in phys_pk)})")
        new_ddl = f"CREATE TABLE {_quote(tmp_table)} ({', '.join(col_defs)})"
        try:
            conn.execute(new_ddl)
        except Exception as e2:
            logger.error(f"  [{db_key}.{table}] 简化DDL也失败: {e2}")
            report["errors"].append(f"{table}: create failed {e2}")
            return False

    # 搬数据：SELECT逻辑列 → 加密后INSERT物理列
    try:
        cur_src = conn.cursor()
        cur_src.execute(f"SELECT * FROM {_quote(table)}")
        rows = cur_src.fetchall()

        if rows:
            # 为防止大内存：分批次，每批 500 行
            BATCH = 500
            col_logical_names = [c["name"] for c in cols]
            placeholders = ",".join(["?"] * len(col_phys))
            insert_sql = (
                f"INSERT INTO {_quote(tmp_table)} "
                f"({','.join(_quote(c) for c in col_phys)}) VALUES ({placeholders})"
            )
            cur_dst = conn.cursor()
            for i in range(0, len(rows), BATCH):
                batch = rows[i:i + BATCH]
                data_batch = []
                for row in batch:
                    new_row = []
                    for j, logical_col in enumerate(col_logical_names):
                        v = row[j]
                        col_type = (cols[j]["type"] or "TEXT").upper()
                        # 不加密：FK/CHECK/IN 约束列 + 已加密 + 非 TEXT类
                        is_constrained = logical_col.lower() in constrained_cols
                        if (cap.get("content_encrypt")
                                and not is_constrained
                                and v is not None
                                and isinstance(v, str)
                                and not v.startswith("MTENC:")
                                and not v.startswith("gAAAAA")
                                and ("TEXT" in col_type or "CHAR" in col_type
                                     or "VARCHAR" in col_type or col_type in ("CLOB", "JSON", ""))):
                            v = enc.encrypt_data(v, level, table, logical_col)
                        new_row.append(v)
                    data_batch.append(new_row)
                cur_dst.executemany(insert_sql, data_batch)
            conn.commit()
        report["rows_migrated"] += len(rows)

        # 行数校验
        cnt1 = conn.execute(f"SELECT COUNT(*) FROM {_quote(table)}").fetchone()[0]
        cnt2 = conn.execute(f"SELECT COUNT(*) FROM {_quote(tmp_table)}").fetchone()[0]
        if cnt1 != cnt2:
            raise RuntimeError(f"行数不一致 src={cnt1} dst={cnt2}")

        # 切换：DROP 旧 → RENAME 新
        conn.execute(f"DROP TABLE {_quote(table)}")
        conn.execute(f"ALTER TABLE {_quote(tmp_table)} RENAME TO {_quote(physical_table)}")
        conn.commit()
        report["tables_encrypted"] += 1
        if report["tables_encrypted"] % 100 == 0 or level == EncryptionLevel.L0_TOP_SECRET:
            logger.info(f"  ✓ {db_key}.{table}({level.name}) → {physical_table} ({cnt1}行)")
        return True
    except Exception as e:
        logger.error(f"  ✗ [{db_key}.{table}] 迁移失败: {e}\n{traceback.format_exc(limit=1)}")
        report["errors"].append(f"{table}: {e}")
        try:
            conn.execute(f"DROP TABLE IF EXISTS {_quote(tmp_table)}")
            conn.commit()
        except Exception:
            pass
        return False


def _rewrite_create(create_sql: str, logical_table: str, new_table: str,
                    col_phys: List[str], cols: List[sqlite3.Row]) -> str:
    """重写 CREATE TABLE：逻辑表→新表名，逻辑列→物理列"""
    if not create_sql:
        col_defs = ", ".join(
            f"{_quote(col_phys[i])} {cols[i]['type']}"
            f"{' NOT NULL' if cols[i]['notnull'] else ''}"
            f"{' PRIMARY KEY' if cols[i]['pk'] else ''}"
            for i in range(len(cols))
        )
        return f"CREATE TABLE {_quote(new_table)} ({col_defs})"
    sql = create_sql
    # 替换表名
    idx = sql.find(logical_table)
    if idx >= 0:
        sql = sql[:idx] + new_table + sql[idx + len(logical_table):]
    # 替换列名（按出现顺序）
    for i, c in enumerate(cols):
        lo = c["name"]
        ph = col_phys[i]
        if lo != ph:
            # 简单替换：只替换独立 token (两侧非字母数字)
            import re
            sql = re.sub(rf"\b{re.escape(lo)}\b", ph, sql, count=1)
    return sql


# ===============================================================
# 单库迁移
# ===============================================================

def migrate_database(db_key: str, db_path: str) -> bool:
    if not os.path.exists(db_path):
        logger.warning(f"[{db_key}] {db_path} 不存在，跳过")
        return True

    size_before = os.path.getsize(db_path)
    report = MIGRATION_REPORT["databases"].setdefault(db_key, {
        "path": db_path, "size_before": size_before,
        "tables_total": 0, "tables_encrypted": 0,
        "rows_migrated": 0, "skipped_l4": 0,
        "tables_already_encrypted": 0,
        "errors": [],
    })

    # 1. 备份
    backup = _backup(db_key, db_path)
    if backup is None:
        return False

    # 2. 连接
    conn = sqlite3.connect(db_path, timeout=60)
    try:
        tables = _list_tables(conn)
        report["tables_total"] = len(tables)
        logger.info(f"[{db_key}] 开始迁移：{len(tables)} 表，{size_before:,} 字节")

        level_counts: Dict[str, int] = {}
        for t, sql in tables:
            lvl = classify_table(t).name
            level_counts[lvl] = level_counts.get(lvl, 0) + 1
        logger.info(f"[{db_key}] 等级分布: {level_counts}")

        # 3. 逐表迁移（L0先迁移，保证极密表优先级）
        ordered = sorted(
            tables, key=lambda ts: classify_table(ts[0]).value  # L0=0先
        )
        for t, sql in ordered:
            ok = _migrate_one_table_inplace(db_key, conn, t, sql, report)
            if not ok:
                MIGRATION_REPORT["errors"].append(f"{db_key}.{t}")
        if report["errors"]:
            conn.rollback()
            raise RuntimeError(f"存在 {len(report['errors'])} 个表错误")
        conn.commit()

        # 4. 文件名混淆（等级>=L3）
        max_level = _max_level_db(tables)
        report["effective_level"] = max_level.name
        cap = LEVEL_CAPABILITY[max_level]
        if cap.get("db_name_obfuscate"):
            archived = db_path + ".cleartext.archived"
            # 此处已完成原地加密，无需再"归档"——备份即可。但为满足"库名混淆"：
            obf_name = enc.db_name_obfuscator.obfuscate_name(os.path.basename(db_path))
            obf_path = os.path.join(os.path.dirname(db_path), obf_name)
            # 软映射：不移动物理文件，只记录映射表（db_manager 后续会接入）
            # 若用户要求强混淆，则取消以下注释：
            # shutil.move(db_path, obf_path)
            report["obfuscated_name"] = obf_name
            report["obfuscated_path"] = obf_path

        report["size_after"] = os.path.getsize(db_path)
        logger.info(
            f"[{db_key}] 完成: {report['tables_encrypted']}/{report['tables_total']} 表 "
            f"({report['rows_migrated']:,} 行) "
            f"跳过: L4={report.get('skipped_l4', 0)} 已加密={report.get('tables_already_encrypted', 0)} "
            f"大小: {report['size_before']:,} → {report['size_after']:,} 字节"
        )
        return True

    except Exception as e:
        logger.error(f"[{db_key}] 迁移失败: {e}")
        MIGRATION_REPORT["errors"].append(f"{db_key}: {e}")
        # 回滚
        try:
            conn.close()
        except Exception:
            pass
        if backup and os.path.exists(backup):
            shutil.copy2(backup, db_path)
            logger.info(f"[{db_key}] 已从备份回滚")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _max_level_db(tables: List[Tuple[str, str]]) -> EncryptionLevel:
    """库内最严等级即为该库等级"""
    return min((classify_table(t) for t, _ in tables), default=EncryptionLevel.L3_INTERNAL)


# ===============================================================
# 主入口
# ===============================================================

def main() -> int:
    # 确保所有 print/logger 立即刷新
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass

    args = sys.argv[1:]
    selected_key = None
    if args and args[0] == "--single":
        if len(args) < 2:
            logger.error("--single 需要指定数据库key")
            return 1
        selected_key = args[1]
        if selected_key not in TARGET_DATABASES:
            logger.error(f"未知key: {selected_key}，可选: {list(TARGET_DATABASES.keys())}")
            return 1
        targets = [(selected_key, TARGET_DATABASES[selected_key])]
    elif args and args[0] == "--rollback":
        # --rollback <db_key>  找到最新备份回滚
        target = args[1]
        backups = sorted([
            os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)
            if f.startswith(target.replace(os.sep, "_") + ".bak")
        ], reverse=True)
        if backups and target in TARGET_DATABASES:
            shutil.copy2(backups[0], TARGET_DATABASES[target])
            logger.info(f"[{target}] 回滚完成 ← {backups[0]}")
            return 0
        logger.error(f"[{target}] 未找到备份")
        return 1
    else:
        targets = list(TARGET_DATABASES.items())

    success = True
    for key, path in targets:
        if not migrate_database(key, path):
            success = False

    # 报告
    report_path = os.path.join(
        REPORT_DIR, f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    MIGRATION_REPORT["finished_at"] = datetime.now().isoformat()
    MIGRATION_REPORT["success"] = success
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(MIGRATION_REPORT, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"迁移报告: {report_path} (success={success})")
    sys.stdout.flush()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

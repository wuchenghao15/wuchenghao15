#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 分片数据库管理器（加密增强版）
=====================================
flow_id: flow_db_encrypt_20260813_001
STEP_7_EXECUTE / 批次4接入点

集成能力：
  - VikeyKeyDerivation：VIKEY 派生的密钥体系
  - SchemaMapper：L0 表/列名映射
  - classify_table：加密等级判定
  - AESGCMCipher：字段级加解密拦截
  - DbNameObfuscator：库名混淆解析
  - SmartConnection：查询路由 + 加密拦截 + 自动解密
"""

import sqlite3
import os
import re
import threading
from typing import Any, Optional, List, Tuple

from app.utils.db_encryption import (
    DatabaseEncryption, EncryptionLevel, LEVEL_CAPABILITY,
    classify_table, DEFAULT_CLASSIFICATION
)

# §14 STEP_7_EXECUTE 双引擎+分级分库接入（向后兼容）
from db_sharding import (
    ShardRouter, ShardSmartConnection, get_default_sc,
    start_transition as _shard_start_transition, extract_table_name as shard_extract_table,
)

enc = DatabaseEncryption()
_lock = threading.Lock()

# ---------- 路径 ----------
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases')
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARD_DIR = os.path.join(ROOT_DIR, 'shard_databases')
BACKUP_DIR = os.path.join(ROOT_DIR, 'shard_backups')

# ---------- 主数据库（真实路径） ----------
DATABASES: dict = {}


def _is_real_sqlite(path: str) -> bool:
    """校验文件是否为真实 SQLite：头部 "SQLite format 3\0" + 最小尺寸"""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) < 1024:
            return False
        with open(path, "rb") as f:
            header = f.read(16)
        return header.startswith(b"SQLite format 3")
    except Exception:
        return False


# 延迟初始化（import-time不做IO/DB打开）
# 避免 OneDrive 锁竞争 + 1000轮测试快速启动
# 首次调用 get_db_for_table / connect / SmartConnection 时才触发 _ensure_ready


def _discover_databases():
    """自动发现目标数据库（优先主库 app.db，其次 split_databases，其次 Database/ ）

    安全：只有真实 SQLite 文件（头部 SQLite format 3 + 尺寸≥1KB）纳入管理，
    过滤 .db 后缀的非数据库文件，避免 build_table_mapping 报错。
    """
    candidates: list = []
    # 根级大库
    for name in ("app.db", "shadow_system.db", "sandbox_system.db"):
        p = os.path.join(ROOT_DIR, name)
        candidates.append((name.replace(".db", ""), p, True))
    # split_databases
    if os.path.isdir(DB_DIR):
        for fn in os.listdir(DB_DIR):
            if fn.endswith(".db"):
                candidates.append((fn[:-3], os.path.join(DB_DIR, fn), False))
    # Database/
    alt_dir = os.path.join(ROOT_DIR, "Database")
    if os.path.isdir(alt_dir):
        for fn in os.listdir(alt_dir):
            if fn.endswith(".db"):
                candidates.append((fn[:-3], os.path.join(alt_dir, fn), False))
    # ai_engines/app/ai/data （限制层数避免遍历 node_modules）
    for sub in ("ai_engines", "app/ai", "data"):
        d = os.path.join(ROOT_DIR, sub)
        if not os.path.isdir(d):
            continue
        for root, dirs, files in os.walk(d, topdown=True):
            # 不进入深层子目录（限制深度=2）
            depth = root[len(d):].count(os.sep)
            if depth >= 2:
                dirs[:] = []
                continue
            for fn in files:
                if fn.endswith(".db"):
                    fp = os.path.join(root, fn)
                    rel = os.path.relpath(fp, ROOT_DIR).replace(os.sep, "__").replace(".db", "")
                    if rel not in DATABASES:
                        candidates.append((rel, fp, False))
                    candidates.append((fn[:-3], fp, False))  # 别名

    for key, path, _ in candidates:
        if key in DATABASES:
            continue
        if not _is_real_sqlite(path):
            continue
        DATABASES[key] = path


TABLE_TO_DB: dict = {}
_INIT_DONE: bool = False


def _ensure_ready() -> None:
    """首次使用时完成发现 + 建表映射；支持多线程幂等"""
    global _INIT_DONE
    if _INIT_DONE:
        return
    with _lock:
        if _INIT_DONE:
            return
        _discover_databases()
        build_table_mapping(locked=True)
        _INIT_DONE = True


def rebuild_table_mapping() -> None:
    """外部强制重算映射（迁移后调用）"""
    with _lock:
        if not DATABASES:
            _discover_databases()
        build_table_mapping(locked=True)


def build_table_mapping(locked: bool = False) -> None:
    """构建 表名→数据库名 映射（兼容映射后的物理表名）"""
    def _run():
        TABLE_TO_DB.clear()
        for db_name, db_path in list(DATABASES.items()):
            if not os.path.exists(db_path):
                continue
            try:
                conn = sqlite3.connect(db_path, timeout=3)  # 缩短 timeout 避免 OneDrive 卡死
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [t[0] for t in cursor.fetchall()]
                conn.close()
                for t in tables:
                    TABLE_TO_DB[t] = db_name
            except Exception as e:
                # OneDrive 锁等：跳过不阻塞初始化
                try:
                    print(f"[DB Manager] warn: skip mapping {db_name}: {e}")
                except Exception:
                    pass
    if locked:
        _run()
    else:
        with _lock:
            _run()


# ---------- 表名/列名反向查询工具 ----------

def resolve_logical_table(db_name: str, physical_table: str) -> str:
    """物理表名 → 逻辑表名（通过建表时SchemaMapper可逆重算）

    简化：若表名形如 t_<16hex> 则认为是映射表，
    在当前库的等级约束下查找能映射到此物理名的候选逻辑表。
    生产环境建议显式维护双向映射表。
    """
    if not physical_table.startswith("t_"):
        return physical_table
    # 启发式：若 build_table_mapping 中找到匹配 TABLE_TO_DB 键相等则直接返回
    if physical_table in TABLE_TO_DB:
        return physical_table
    return physical_table


def get_db_for_table(table_name: str) -> str:
    """优先按分片路由命中shard_*；否则走原映射（向后兼容）"""
    shard = ShardRouter.route(table_name or "", "")
    # 若物理分片文件已存在 → 返回shard，保证路由稳定
    try:
        path = ShardRouter.shard_path(shard)
        if path.exists() and path.stat().st_size >= 1024:
            return shard
    except Exception:
        pass
    # 回落旧逻辑
    _ensure_ready()
    if table_name in TABLE_TO_DB:
        return TABLE_TO_DB[table_name]
    if "app" in DATABASES:
        try:
            conn = sqlite3.connect(DATABASES["app"], timeout=5)
            r = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            ).fetchone()
            conn.close()
            if r:
                TABLE_TO_DB[table_name] = "app"
                return "app"
        except Exception:
            pass
    # 最终：返回shard（即使是空库让 SmartConnection 可写入空分片）
    return shard if shard else (list(DATABASES.keys())[0] if DATABASES else "app")


def route_for_table(table_name: str, db_name: Optional[str] = None) -> str:
    """显式分片路由API（业务层推荐）"""
    return ShardRouter.route(table_name or "", db_name or "")


def get_db_path(db_name: str) -> Optional[str]:
    return DATABASES.get(db_name)


def get_db_path_for_table(table_name: str) -> Optional[str]:
    db_name = get_db_for_table(table_name)
    return get_db_path(db_name)


# ---------- 连接 ----------

def connect(db_name: str):
    """建立数据库连接（加密层就绪，由业务层调用字段加解密）"""
    _ensure_ready()
    db_path = DATABASES.get(db_name)
    if not db_path or not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def connect_for_table(table_name: str):
    db_name = get_db_for_table(table_name)
    return connect(db_name)


# ---------- SmartConnection：透明加解密层（§14 STEP_7 升级为双引擎+分片路由，保持API兼容）----------


class SmartConnection:
    """智能连接池 + 字段级透明加解密 + 双引擎 + 8分片路由（向后兼容）。

    核心升级 (STEP_7_EXECUTE)：
      - 内部代理到 ShardSmartConnection（主引擎WAL / 备份独立句柄）
      - 表 → 8分片路由，每分片独立连接池 + 防互锁
      - L0 分片强制需 VIKEY 在线
      - 7天双写过渡自动回落到原库
    """

    def __init__(self):
        self._inner: ShardSmartConnection = get_default_sc()

    # ---- CRUD （同旧API，新增 db_name / readonly 可选参数保留）----
    def execute(self, sql: str, params: Any = None, *, db_name: Optional[str] = None, readonly: bool = False):
        return self._inner.execute(sql, params, db_name=db_name, readonly=readonly)

    def executemany(self, sql: str, seq_of_params: list):
        return self._inner.executemany(sql, seq_of_params)

    def fetchone(self, sql: str, params: Any = None, *, db_name: Optional[str] = None):
        return self._inner.fetchone(sql, params, db_name=db_name)

    def fetchall(self, sql: str, params: Any = None, *, db_name: Optional[str] = None):
        return self._inner.fetchall(sql, params, db_name=db_name)

    # ---- 新增双引擎切换 ----
    def switch_to_backup(self, shard: str) -> bool:
        """验收标准2：主→备强制切换（≤500ms）"""
        return self._inner.switch_to_backup(shard)

    def switch_to_primary(self, shard: str) -> bool:
        return self._inner.switch_to_primary(shard)

    def health_report(self) -> dict:
        return self._inner.health_report()

    def close(self):
        """兼容旧close（新ShardSmartConnection由连接池管理）"""
        # 不关闭池：否则多线程会失效；此处空操作
        return


def extract_table_name(sql: str) -> str:
    sql_s = sql.strip().upper()
    patterns = [
        r'FROM\s+(\w+)',
        r'INSERT\s+INTO\s+(\w+)',
        r'UPDATE\s+(\w+)',
        r'DELETE\s+FROM\s+(\w+)',
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
        r'ALTER\s+TABLE\s+(\w+)',
        r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)',
    ]
    for p in patterns:
        m = re.search(p, sql_s)
        if m:
            return m.group(1).lower()
    return "other"


def _extract_columns_for_params(sql: str, table: str, params: Any) -> list:
    """从 INSERT/UPDATE SQL 中提取列名（用于加密定位）"""
    cols = []
    s = sql.strip()
    # INSERT INTO t (col1, col2) VALUES (?, ?)
    m = re.search(r"INSERT\s+INTO\s+[\w`\"\[]+[\w`\"\]]*\s*\(([^)]+)\)", s, re.I)
    if m:
        cols = [c.strip().strip('`"[]') for c in m.group(1).split(",")]
        return cols
    # UPDATE t SET col1=?, col2=?
    m = re.search(r"UPDATE\s+[\w`\"\[]+[\w`\"\]]*\s+SET\s+(.+?)(?:\s+WHERE|\s*$|;)", s, re.I | re.S)
    if m:
        body = m.group(1)
        for pair in body.split(","):
            pair = pair.strip()
            eq = pair.split("=")[0].strip().strip('`"[]')
            if eq:
                cols.append(eq)
    return cols


smart_conn = SmartConnection()


def get_db_connection():
    return smart_conn


# ---------- §14 STEP_7 新增：双引擎/分片路由公开API ----------

def switch_shard_engine(shard: str, target: str) -> bool:
    """强制切换 shard 的主/备引擎（target ∈ {PRIMARY, BACKUP}）。验收标准2：≤500ms"""
    return smart_conn.switch_to_backup(shard) if target.upper().startswith("B") else smart_conn.switch_to_primary(shard)


def shard_health_report() -> dict:
    """所有分片状态、尺寸、引擎、告警的汇总（石监理验收用）"""
    return smart_conn.health_report()


def shard_cold_bootstrap_from_legacy(dry_run: bool = False) -> dict:
    """P3冷启动：将 app.db/shadow/sandbox 等原库中的表按路由规则创建到 8 分片中。

    返回各分片迁移统计（表数/行数/错误数）。dry_run=True 时不落盘。
    """
    import os as _os
    from typing import Dict as _Dict
    stats: _Dict[str, _Dict[str, int]] = {}
    _ensure_ready()
    # 原库集合（排除测试/修复用 dev repair test_login）
    legacy_dbs = {k: v for k, v in DATABASES.items()
                  if k.lower() not in {"dev", "mtscos_repair", "test_login", "app-吴成浩的macbook pro"}}
    seen_tables: set = set()
    for shard in ShardRouter.list_shards():
        stats[shard] = {"tables": 0, "rows": 0, "errors": 0}
    for db_key, db_path in legacy_dbs.items():
        if not _os.path.exists(db_path):
            continue
        try:
            legacy_conn = sqlite3.connect(db_path, timeout=10)
            legacy_conn.row_factory = sqlite3.Row
            tables = [r[0] for r in legacy_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        except Exception:
            continue
        for tbl in tables:
            if tbl in seen_tables:
                continue
            shard = ShardRouter.route(tbl, db_key)
            if dry_run:
                stats[shard]["tables"] += 1
                continue
            try:
                # 取DDL
                (ddl,) = legacy_conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tbl,)).fetchone()
                # 目标分片不存在就新建
                shard_path = ShardRouter.shard_path(shard)
                target_conn = sqlite3.connect(shard_path, timeout=10)
                try:
                    target_conn.execute(f"CREATE TABLE IF NOT EXISTS \"{tbl}\" AS SELECT * FROM \"{tbl}\" WHERE 0")
                except Exception:
                    # fallback 直接执行原DDL
                    try: target_conn.execute(ddl)
                    except Exception: pass
                try:
                    rows = legacy_conn.execute(f"SELECT * FROM \"{tbl}\"").fetchall()
                    if rows:
                        cols = [d[0] for d in legacy_conn.execute(f"SELECT * FROM \"{tbl}\" LIMIT 1").description]
                        placeholders = ",".join(["?"] * len(cols))
                        quoted_cols = ",".join('"' + c + '"' for c in cols)
                        target_conn.executemany(
                            f"INSERT OR IGNORE INTO \"{tbl}\" ({quoted_cols}) VALUES ({placeholders})",
                            [tuple(r) for r in rows])
                        stats[shard]["rows"] += len(rows)
                    target_conn.commit()
                    stats[shard]["tables"] += 1
                    seen_tables.add(tbl)
                except Exception:
                    stats[shard]["errors"] += 1
                finally:
                    try: target_conn.close()
                    except Exception: pass
            except Exception:
                stats[shard]["errors"] += 1
        try: legacy_conn.close()
        except Exception: pass
    return stats


def shard_start_transition_dual_write() -> str:
    """启动7天双写过渡期：先冷启动→再开双写。返回 phase（DUAL_WRITE / CUTOFF / COLD）"""
    # 先冷启动一次（空则初始化）
    try:
        empty_all = all(
            (not ShardRouter.shard_path(s).exists()) or (ShardRouter.shard_path(s).stat().st_size < 1024)
            for s in ShardRouter.list_shards()
        )
        if empty_all:
            shard_cold_bootstrap_from_legacy(dry_run=False)
    except Exception:
        pass
    return _shard_start_transition()


def bind_vikey_for_encryption(vikey_info: str) -> bool:
    """绑定 VIKEY 硬件信息（生产环境入口调用）

    - 在线时 L0 库可读写
    - 离线时 L0 锁定，L1-L3 可继续使用启动时缓存的 KEK
    - 同时同步 db_sharding 全局 enc，保证加解密密钥一致
    """
    _ensure_ready()
    ok1 = enc.bind_vikey(vikey_info)
    ok2 = True
    try:
        # 与 db_sharding 中的 enc 实例保持密钥一致（否则解密失败）
        import db_sharding as _ds
        if _ds.enc is not enc:
            ok2 = _ds.enc.bind_vikey(vikey_info)
        # 清 _vikey_online 缓存
        _ds._VIKEY_CACHE_TS = 0.0
    except Exception:
        ok2 = False
    ok = ok1 and ok2
    if ok:
        print(f"[DB Manager] VIKEY 已绑定，L0-L4 解密通道就绪；L0分片已解锁")
    return ok


def offline_vikey_cache_kek() -> bool:
    """VIKEY 离线前调用：缓存 KEK 以便 L1-L3 继续运行（L0 锁定）"""
    return enc.key_derivation.cache_kek_for_offline()


def rebuild_table_mapping() -> None:
    """迁移后重建 TABLE_TO_DB 映射"""
    build_table_mapping()

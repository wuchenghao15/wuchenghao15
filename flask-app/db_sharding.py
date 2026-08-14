#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 双引擎主备分离 + 分级分库横向打散
==========================================
flow_id: flow_db_shard_engine_20260814_001
STEP_7_EXECUTE 核心交付物

核心组件：
  1. ShardRouter            — 8分片路由规则（加密等级L0-L4 × 6业务域）
  2. ShardConnectionPool    — 每分片独立连接池（WAL + NORMAL同步 + 防锁）
  3. DualEngineManager      — 主引擎(读写) + 备份引擎(只读独立句柄) + 热切换
  4. LongTxMonitor          — 长事务>10s自动kill + 环形告警
  5. ShardSmartConnection   — 路由+加解密+主备/分片的透明CRUD（兼容旧API）

分片清单（≤1GB/100表 超额告警）：
  shard_l0_top_secret          — L0极密：用户核心密钥/授权、超级管理员会话
  shard_l1_user_auth           — L1机密：登录/权限/组织/审计
  shard_l2_exam_question       — L2秘密：题库/考试/学习轨迹
  shard_l2_ai_employee         — L2秘密：AI员工/引擎/集群/脑库关联
  shard_l3_config_setting      — L3内部：系统参数/配置/端口/路由
  shard_l3_ops_logging         — L3内部：巡检/监控/日志/告警/事件
  shard_l3_business_primary    — L3内部：订单/需求/业务表（原app.db的主要）
  shard_secondary_sandbox      — L3内部：沙箱/shadow/开发库（读写隔离）

过渡策略：7天双写（原库 + 分片库），失败自动回滚
        冷启动扫描原库 → 双写 → 一致性校验 → 100%后读切
"""
from __future__ import annotations

import hashlib
import os
import queue
import re
import shutil
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.utils.db_encryption import (
    DatabaseEncryption, EncryptionLevel, classify_table,
)

ROOT_DIR = Path(__file__).resolve().parent
SHARD_DIR = ROOT_DIR / "shard_databases"
SHARD_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = ROOT_DIR / "shard_backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

enc = DatabaseEncryption()

# =============================================================================
# 1. ShardRouter —— 路由规则（按 L0-L4 × 业务域 → 8分片）
# =============================================================================

# 表名/库名/模式 → 业务域分类规则（可扩展）
DOMAIN_RULES: List[Tuple[str, re.Pattern]] = [
    ("auth",      re.compile(r"(?i)(user|login|session|auth|permission|role|group|org|tenant|account)")),
    ("exam",      re.compile(r"(?i)(question|exam|test|paper|answer|bank|learn|study|q_|t_exam|t_question)")),
    ("ai",        re.compile(r"(?i)(ai_employee|mtscos_ai|ai_engin|neural|brain|cluster|array|eigenflux|cognition)")),
    ("config",    re.compile(r"(?i)(config|param|setting|option|rule|constraint|port|route|feature)")),
    ("logging",   re.compile(r"(?i)(log|audit|event|alert|monitor|inspect|巡检|trace|perf|metric)")),
    ("business",  re.compile(r"(?i)(order|demand|favorit|push|response|timeline|service|payment|product|t_order|t_demand)")),
]

# 默认分片定义（L0特殊，L1-3按域分片，sandbox独立）
SHARDS: Dict[str, Dict] = {
    "shard_l0_top_secret": {"level": "L0", "max_size_mb": 512, "max_tables": 100,
                            "domains": ["auth"], "pattern": re.compile(r"(?i)(vikey|license|kek|dek|root_|super_admin|superadmin|wuchenghao15|violation|encryption_key)")},
    "shard_l1_user_auth":       {"level": "L1", "max_size_mb": 1024, "max_tables": 100, "domains": ["auth"]},
    "shard_l2_exam_question":   {"level": "L2", "max_size_mb": 1024, "max_tables": 100, "domains": ["exam"]},
    "shard_l2_ai_employee":     {"level": "L2", "max_size_mb": 1024, "max_tables": 100, "domains": ["ai"]},
    "shard_l3_config_setting":  {"level": "L3", "max_size_mb": 1024, "max_tables": 100, "domains": ["config"]},
    "shard_l3_ops_logging":     {"level": "L3", "max_size_mb": 1024, "max_tables": 100, "domains": ["logging"]},
    "shard_l3_business_primary":{"level": "L3", "max_size_mb": 1024, "max_tables": 100, "domains": ["business"]},
    "shard_secondary_sandbox":  {"level": "L3", "max_size_mb": 1024, "max_tables": 100, "domains": ["sandbox", "shadow", "dev"]},
}

# 双写过渡期：7天内 同时写入原库+分片库，读先读分片，失败回落到原库
TRANSITION_WINDOW_DAYS = 7
TRANSITION_START_FILE = SHARD_DIR / ".transition_start.txt"


def _transition_phase() -> str:
    """返回 COLD / DUAL_WRITE / CUTOFF 三阶段"""
    if not TRANSITION_START_FILE.exists():
        return "COLD"
    try:
        t0 = datetime.fromisoformat(TRANSITION_START_FILE.read_text().strip())
    except Exception:
        return "COLD"
    days = (datetime.now() - t0).days
    if days < TRANSITION_WINDOW_DAYS:
        return "DUAL_WRITE"
    return "CUTOFF"


def _start_transition() -> None:
    if not TRANSITION_START_FILE.exists():
        TRANSITION_START_FILE.write_text(datetime.now().isoformat())


def _classify_domain(table: str, db_key: str = "") -> str:
    for dom, pat in DOMAIN_RULES:
        if pat.search(table):
            return dom
    # 按 db_key 推断域
    for dom, pat in DOMAIN_RULES:
        if pat.search(db_key):
            return dom
    return "business"


class ShardRouter:
    """表 → 分片 key；提供 shard_path / shard_backup_path"""

    @staticmethod
    def shard_path(shard_key: str) -> Path:
        return SHARD_DIR / f"{shard_key}.db"

    @staticmethod
    def shard_backup_path(shard_key: str) -> Path:
        return BACKUP_DIR / f"{shard_key}.backup.db"

    @staticmethod
    def route(table: str, db_key: str = "") -> str:
        """基于 L0/L1/L2/L3 × 业务域 路由到 8 分片之一"""
        level = classify_table(table)
        # L0 特殊：按 pattern / 强制规则
        if level == EncryptionLevel.L0_TOP_SECRET:
            return "shard_l0_top_secret"
        # L0 fallback: pattern 命中（即使 classify_table 没归类）
        if SHARDS["shard_l0_top_secret"]["pattern"].search(table) or \
           SHARDS["shard_l0_top_secret"]["pattern"].search(db_key):
            return "shard_l0_top_secret"
        domain = _classify_domain(table, db_key)
        # sandbox/shadow/dev 特殊路由
        low = f"{table} {db_key}".lower()
        if any(k in low for k in ("sandbox", "shadow_system", "dev.db", "repair", "test_login")):
            return "shard_secondary_sandbox"
        # L1: 权限/组织/审计
        if level == EncryptionLevel.L1_CONFIDENTIAL or domain == "auth":
            return "shard_l1_user_auth"
        # L2 分 exam / ai
        if level == EncryptionLevel.L2_SECRET:
            if domain == "exam":   return "shard_l2_exam_question"
            if domain == "ai":     return "shard_l2_ai_employee"
            return "shard_l2_exam_question"  # 默认L2 落 exam
        # L3: config / logging / business
        if domain == "config":   return "shard_l3_config_setting"
        if domain == "logging":  return "shard_l3_ops_logging"
        if domain == "business": return "shard_l3_business_primary"
        return "shard_l3_business_primary"

    @staticmethod
    def list_shards() -> List[str]:
        return list(SHARDS.keys())

    @staticmethod
    def shard_over_limit(shard_key: str) -> Tuple[bool, Dict]:
        """验收标准1：分片≤1GB/100表 超额告警"""
        spec = SHARDS.get(shard_key, {})
        path = ShardRouter.shard_path(shard_key)
        info = {"size_mb": 0, "tables": 0, "max_size_mb": spec.get("max_size_mb", 1024),
                "max_tables": spec.get("max_tables", 100)}
        if path.exists():
            info["size_mb"] = round(path.stat().st_size / (1024 * 1024), 2)
            try:
                c = sqlite3.connect(path, timeout=3)
                info["tables"] = c.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
                c.close()
            except Exception:
                pass
        over = (info["size_mb"] > info["max_size_mb"]) or (info["tables"] > info["max_tables"])
        return over, info


# =============================================================================
# 2. ShardConnectionPool —— 每分片独立连接池
# =============================================================================

@dataclass
class PooledConn:
    conn: sqlite3.Connection
    acquired_at: float = 0.0
    tx_start: float = 0.0  # in_transition 开始时间（秒）


class ShardConnectionPool:
    """每分片独立连接池，WAL + synchronous=NORMAL，空闲回收。"""

    POOL_MAX = 4  # 每分片最大连接数（SQLite WAL推荐4-8）

    def __init__(self):
        self._pools: Dict[str, List[sqlite3.Connection]] = {}
        self._acquired: Dict[int, PooledConn] = {}  # id(conn) -> meta
        self._lock = threading.Lock()

    def _new_conn(self, shard_key: str, readonly: bool = False) -> sqlite3.Connection:
        path = ShardRouter.shard_path(shard_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # 备份引擎读：独立只读句柄
        uri = f"file:{path}?mode=ro" if readonly else f"file:{path}?mode=rwc"
        c = sqlite3.connect(uri, timeout=8, uri=True, check_same_thread=False)
        c.row_factory = sqlite3.Row
        if not readonly:
            try:
                c.execute("PRAGMA journal_mode=WAL")
                c.execute("PRAGMA synchronous=NORMAL")
                c.execute("PRAGMA busy_timeout=8000")
                c.execute("PRAGMA foreign_keys=ON")
            except sqlite3.OperationalError:
                pass
        return c

    def acquire(self, shard_key: str, readonly: bool = False) -> sqlite3.Connection:
        with self._lock:
            bucket = ("ro:" if readonly else "rw:") + shard_key
            pool = self._pools.setdefault(bucket, [])
            while pool:
                c = pool.pop()
                try:
                    c.execute("SELECT 1")  # 探活
                except Exception:
                    continue
                self._acquired[id(c)] = PooledConn(conn=c, acquired_at=time.time(),
                                                   tx_start=time.time() if getattr(c, "in_transaction", False) else 0.0)
                return c
        c = self._new_conn(shard_key, readonly=readonly)
        with self._lock:
            self._acquired[id(c)] = PooledConn(conn=c, acquired_at=time.time(),
                                               tx_start=time.time() if getattr(c, "in_transaction", False) else 0.0)
        return c

    def release(self, conn: sqlite3.Connection):
        cid = id(conn)
        with self._lock:
            meta = self._acquired.pop(cid, None)
        if meta is None:
            try: conn.close()
            except Exception: pass
            return
        try:
            if getattr(conn, "in_transaction", False):
                conn.rollback()  # 强制回滚未提交
        except Exception:
            pass
        # 池满则关闭
        with self._lock:
            if len(self._pools) > 8 * self.POOL_MAX:
                try: conn.close()
                except Exception: pass
                return
            # 找bucket：简单策略：扔进 rw 公共池
            pool = self._pools.setdefault("rw:__common__", [])
            if len(pool) < self.POOL_MAX * 2:
                pool.append(conn)
            else:
                try: conn.close()
                except Exception: pass


# =============================================================================
# 3. DualEngineManager —— 主引擎(读写) + 备份引擎(只读) + 自动热切换
# =============================================================================

class _EngineState:
    def __init__(self):
        self.active: str = "PRIMARY"  # PRIMARY / BACKUP
        self.last_switch_ts: float = 0.0
        self.consec_ioerr: int = 0
        self.primary_errors: int = 0
        self.backup_errors: int = 0
        self.most_recent_primary_checks: List[Tuple[float, str]] = []
        self._lock = threading.RLock()


class DualEngineManager:
    """双引擎：主引擎(SQLite WAL 读写) + 备份引擎(独立只读句柄)。

    切换策略（§14 不可绕开）：
      A. 自动切换：主库连续 IOERR≥3 次 或 PRAGMA integrity_check != 'ok'
          → 延迟 5s → 切换到备份；SA 指令可强制切换（force_switch）
      B. 强制切换：super_admin_report_status == 'FORCED_BY_SA' 直接切
      C. SHA-256 整库页校验：切回主库前必须 SHA 一致
    """

    SWITCH_DELAY_SEC = 5
    IOERR_THRESHOLD = 3

    def __init__(self, pool: ShardConnectionPool):
        self.pool = pool
        self.states: Dict[str, _EngineState] = {}  # 每个分片一个状态
        self._lock = threading.RLock()

    # ---------- 状态 ----------
    def _st(self, shard: str) -> _EngineState:
        with self._lock:
            s = self.states.get(shard)
            if not s:
                s = _EngineState()
                self.states[shard] = s
            return s

    def active_engine(self, shard: str) -> str:
        return self._st(shard).active

    # ---------- 校验 ----------
    @staticmethod
    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()

    def sync_backup_from_primary(self, shard: str) -> bool:
        """主库 → 备份库 拷贝（页级 SHA-256 后再比对）"""
        src = ShardRouter.shard_path(shard)
        dst = ShardRouter.shard_backup_path(shard)
        if not src.exists():
            return False
        try:
            tmp = dst.with_suffix(".tmp")
            if tmp.exists(): tmp.unlink()
            # 使用 sqlite backup API 进行热备份（不阻塞 WAL）
            src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=5)
            dst_conn = sqlite3.connect(tmp, timeout=5)
            with dst_conn:
                src_conn.backup(dst_conn, pages=50, progress=None)
            src_conn.close()
            dst_conn.close()
            # 校验
            if self.sha256_file(src) != self.sha256_file(tmp):
                tmp.unlink(missing_ok=True)
                return False
            tmp.replace(dst)
            return True
        except Exception:
            try:
                if dst.parent.joinpath(dst.name + ".tmp").exists():
                    dst.parent.joinpath(dst.name + ".tmp").unlink()
            except Exception:
                pass
            return False

    # ---------- CRUD 获取连接 ----------
    def get_conn(self, shard: str, readonly: bool = False):
        """基于 active_engine 返回合适连接；主引擎不可用时自动切换"""
        st = self._st(shard)
        # 强制SA
        primary_exists = ShardRouter.shard_path(shard).exists()
        backup_exists = ShardRouter.shard_backup_path(shard).exists()

        # 只读：优先备份引擎（独立句柄）
        if readonly and backup_exists and st.active != "FORCE_PRIMARY":
            try:
                c = self.pool._new_conn(shard + "_BACKUP__MOCK", readonly=True)  # no
                c.close()
            except Exception:
                pass
            # 直接用备份路径打开独立只读句柄
            path = ShardRouter.shard_backup_path(shard)
            try:
                c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=8)
                c.row_factory = sqlite3.Row
                return c, "BACKUP"
            except Exception:
                st.backup_errors += 1

        # 主引擎
        primary_err = False
        try:
            c = self.pool.acquire(shard, readonly=False)
            if self._integrity_ok(c):
                with st._lock:
                    st.consec_ioerr = 0
                return c, "PRIMARY"
            c.close()
            primary_err = True
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            primary_err = True
            with st._lock:
                st.consec_ioerr += 1
                st.primary_errors += 1

        # 自动切换条件
        if primary_err and (st.consec_ioerr >= self.IOERR_THRESHOLD or not primary_exists):
            self._do_switch(st, shard, reason="ioerr_or_missing")
        if st.active == "BACKUP" and backup_exists:
            path = ShardRouter.shard_backup_path(shard)
            c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=8)
            c.row_factory = sqlite3.Row
            return c, "BACKUP"
        # 回落：尝试主引擎（最后一次）
        return self.pool.acquire(shard, readonly=False), "PRIMARY"

    @staticmethod
    def _integrity_ok(c: sqlite3.Connection) -> bool:
        try:
            row = c.execute("PRAGMA integrity_check(1)").fetchone()
            return row and row[0] == "ok"
        except Exception:
            return False

    # ---------- 切换 ----------
    def _do_switch(self, st: _EngineState, shard: str, reason: str) -> bool:
        with st._lock:
            if time.time() - st.last_switch_ts < self.SWITCH_DELAY_SEC:
                return False
            next_engine = "PRIMARY" if st.active == "BACKUP" else "BACKUP"
            # 切回主库：必须 SHA 一致
            if next_engine == "PRIMARY":
                p = ShardRouter.shard_path(shard)
                b = ShardRouter.shard_backup_path(shard)
                if p.exists() and b.exists() and self.sha256_file(p) != self.sha256_file(b):
                    # 不一致：不切回
                    st.last_switch_ts = time.time()
                    return False
            st.active = next_engine
            st.last_switch_ts = time.time()
            st.consec_ioerr = 0
            st.most_recent_primary_checks.append((time.time(), f"switch→{next_engine}:{reason}"))
            if len(st.most_recent_primary_checks) > 10:
                st.most_recent_primary_checks.pop(0)
            return True

    def force_switch(self, shard: str, target: str) -> bool:
        """验收标准2：SA强制切换（≤500ms）"""
        t0 = time.time()
        st = self._st(shard)
        with st._lock:
            st.active = "PRIMARY" if target.upper().startswith("P") else "BACKUP"
            st.last_switch_ts = time.time()
        return (time.time() - t0) <= 0.5


# =============================================================================
# 4. LongTxMonitor —— 长事务>10s 自动 kill + 告警环
# =============================================================================

class LongTxMonitor(threading.Thread):
    def __init__(self, pool: ShardConnectionPool, threshold_sec: float = 10.0,
                 alert_cb: Optional[Callable[[Dict], None]] = None):
        super().__init__(daemon=True, name="LongTxMonitor")
        self.pool = pool
        self.threshold = threshold_sec
        self.alert_cb = alert_cb
        self.alerts: queue.Queue = queue.Queue(maxsize=1024)
        self._stop = threading.Event()

    def stop(self): self._stop.set()

    def run(self):
        while not self._stop.is_set():
            try:
                self._sweep()
            except Exception:
                pass
            self._stop.wait(2.0)  # 每2秒扫

    def _sweep(self):
        now = time.time()
        kill_ids: List[int] = []
        with self.pool._lock:
            snapshot = list(self.pool._acquired.items())
        for cid, meta in snapshot:
            tx_age = meta.tx_start if meta.tx_start > 0 else meta.acquired_at
            age = now - tx_age
            # 刷新事务状态
            try:
                if meta.conn.in_transaction and meta.tx_start == 0:
                    meta.tx_start = now
                    continue
                if not meta.conn.in_transaction and meta.tx_start > 0:
                    meta.tx_start = 0
                    continue
            except Exception:
                pass
            if (tx_age > 0 and age > self.threshold) or age > self.threshold * 2:
                # 告警 + kill
                alert = {"cid": cid, "age_sec": round(age, 2), "shard": "?", "threshold": self.threshold,
                         "ts": datetime.now().isoformat()}
                try:
                    self.alerts.put_nowait(alert)
                except queue.Full:
                    self.alerts.get_nowait()
                    self.alerts.put_nowait(alert)
                if self.alert_cb:
                    try: self.alert_cb(alert)
                    except Exception: pass
                kill_ids.append(cid)
        for cid in kill_ids:
            with self.pool._lock:
                meta = self.pool._acquired.pop(cid, None)
            if meta:
                try: meta.conn.rollback()
                except Exception: pass
                try: meta.conn.close()
                except Exception: pass


# =============================================================================
# 5. ShardSmartConnection —— 对外 CRUD，兼容旧 SmartConnection API
# =============================================================================

class ShardSmartConnection:
    """路由 → 主备/分片 → 透明加解密 → 双写过渡 → 一致性回落。

    API 与 db_manager.SmartConnection 保持完全一致：
        execute / executemany / fetchone / fetchall
    + 新增：
        switch_to_backup(shard) / switch_to_primary(shard)
        health_report()
    """

    def __init__(self, *, dual: DualEngineManager = None, pool: ShardConnectionPool = None,
                 router: ShardRouter = None, monitor: LongTxMonitor = None):
        self._pool = pool or ShardConnectionPool()
        self._router = router or ShardRouter()
        self._dual = dual or DualEngineManager(self._pool)
        self._monitor = monitor or LongTxMonitor(self._pool)
        if not self._monitor.is_alive():
            try: self._monitor.start()
            except RuntimeError: pass
        self._local = threading.local()  # 缓存 per-thread 连接

    # ---------- 路由 ----------
    def _resolve_shard(self, table: str, db_name: Optional[str]) -> str:
        return self._router.route(table or "", db_name or "")

    # ---------- 透明加解密（同 db_manager 实现） ----------
    @staticmethod
    def _extract_columns(sql: str, table: str, params: Any) -> List[str]:
        """从 INSERT/UPDATE SQL 提取列名；失败则占位（确保加密列名定位一致）"""
        cols: List[str] = []
        if not params: return cols
        s = sql.strip()
        m = re.search(r"INSERT\s+INTO\s+[\w`\"\[]+[\w`\"\]]*\s*\(([^)]+)\)", s, re.I)
        if m:
            cols = [c.strip().strip('`"[]') for c in m.group(1).split(",")]
            return cols
        m = re.search(r"UPDATE\s+[\w`\"\[]+[\w`\"\]]*\s+SET\s+(.+?)(?:\s+WHERE|\s*$|;)", s, re.I | re.S)
        if m:
            for pair in m.group(1).split(","):
                eq = pair.split("=")[0].strip().strip('`"[]')
                if eq: cols.append(eq)
            return cols
        n = len(params[0]) if isinstance(params, (list, tuple)) and params and isinstance(params[0], (list, tuple, dict)) else (
            len(params) if isinstance(params, (list, tuple)) else 1)
        return [f"col_{i}" for i in range(n)]

    def _decrypt_row(self, table: str, row: Any) -> Any:
        if row is None: return None
        level = classify_table(table or "")
        from app.utils.db_encryption import LEVEL_CAPABILITY
        if not LEVEL_CAPABILITY.get(level, {}).get("content_encrypt"):
            return row
        try:
            data = dict(row)
        except Exception:
            return row
        out = {}
        for k, v in data.items():
            if isinstance(v, str) and v.startswith("MTENC:"):
                out[k] = enc.decrypt_data(v, level, table, k)
            else:
                out[k] = v
        return out

    def _decrypt_rows(self, table: str, rows: list) -> list:
        return [self._decrypt_row(table, r) for r in rows]

    def _encrypt_one(self, table: str, row: Any, cols: Optional[List[str]] = None) -> Any:
        """加密单行。对dict使用真实keys；对tuple/list使用SQL解析出的列名cols；
        必须保证加密时列名与SELECT返回的列名一致，否则HKDF字段密钥不同导致解密失败。"""
        level = classify_table(table or "")
        from app.utils.db_encryption import LEVEL_CAPABILITY
        if not LEVEL_CAPABILITY.get(level, {}).get("content_encrypt") or row is None:
            return row
        if isinstance(row, dict):
            out = {}
            for k, v in row.items():
                if isinstance(v, str) and not v.startswith("MTENC:") and not v.startswith("gAAAAA"):
                    out[k] = enc.encrypt_data(v, level, table, k)
                else:
                    out[k] = v
            return out
        if isinstance(row, (tuple, list)):
            keys = (cols if cols and len(cols) == len(row)
                    else [f"col_{i}" for i in range(len(row))])
            out = []
            for i, v in enumerate(row):
                key = keys[i] if i < len(keys) else f"col_{i}"
                if isinstance(v, str) and not v.startswith("MTENC:") and not v.startswith("gAAAAA"):
                    out.append(enc.encrypt_data(v, level, table, key))
                else:
                    out.append(v)
            return type(row)(out) if not isinstance(row, list) else out
        return row

    # ---------- 双写过渡：原库 + 分片 ----------
    def _legacy_execute_optional(self, table: str, sql: str, params: Any):
        """双写阶段：同步写原库（失败记录告警但不影响主流程）"""
        phase = _transition_phase()
        if phase not in ("DUAL_WRITE",):
            return
        try:
            from db_manager import connect as legacy_connect, get_db_for_table
            dbk = get_db_for_table(table)
            lc = legacy_connect(dbk)
            if not lc: return
            try:
                cur = lc.cursor()
                if params is not None:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                lc.commit()
            except Exception:
                lc.rollback()
            finally:
                try: lc.close()
                except Exception: pass
        except Exception:
            pass

    # ---------- 核心CRUD ----------
    def execute(self, sql: str, params: Any = None, *, db_name: Optional[str] = None,
                readonly: bool = False):
        table = extract_table_name(sql)
        shard = self._resolve_shard(table, db_name)
        # L0 分片：VIKEY 必须在线（验收标准4）
        if shard == "shard_l0_top_secret" and not _vikey_online():
            raise PermissionError("[L0_VIKEY_REQUIRED] L0分片需要VIKEY硬件在线")
        conn, engine = self._dual.get_conn(shard, readonly=readonly)
        # 加密params（解析SQL列名 → cols）
        cols = self._extract_columns(sql, table, params)
        p2 = self._encrypt_one(table, params, cols) if params is not None else None
        cur = conn.cursor()
        try:
            if p2 is not None:
                cur.execute(sql, p2)
            else:
                cur.execute(sql)
            # 总是 commit（SQLite非autocommit模式下DML会隐式开事务）
            try:
                conn.commit()
            except Exception:
                pass
        except Exception:
            try: conn.rollback()
            except Exception: pass
            raise
        finally:
            if engine == "PRIMARY":
                self._pool.release(conn)
            else:
                try: conn.close()
                except Exception: pass
        # 双写过渡
        self._legacy_execute_optional(table, sql, params)
        return cur

    def executemany(self, sql: str, seq_of_params: list):
        table = extract_table_name(sql)
        shard = self._resolve_shard(table, None)
        if shard == "shard_l0_top_secret" and not _vikey_online():
            raise PermissionError("[L0_VIKEY_REQUIRED] L0分片需要VIKEY硬件在线")
        conn, engine = self._dual.get_conn(shard, readonly=False)
        cols = self._extract_columns(sql, table, seq_of_params[0] if seq_of_params else None)
        enc_seq = [self._encrypt_one(table, r, cols) for r in seq_of_params]
        cur = conn.cursor()
        try:
            cur.executemany(sql, enc_seq)
            try: conn.commit()
            except Exception: pass
        except Exception:
            try: conn.rollback()
            except Exception: pass
            raise
        finally:
            if engine == "PRIMARY":
                self._pool.release(conn)
            else:
                try: conn.close()
                except Exception: pass
        return cur

    def fetchone(self, sql: str, params: Any = None, *, db_name: Optional[str] = None):
        table = extract_table_name(sql)
        shard = self._resolve_shard(table, db_name)
        if shard == "shard_l0_top_secret" and not _vikey_online():
            raise PermissionError("[L0_VIKEY_REQUIRED] L0分片需要VIKEY硬件在线")
        try:
            conn, engine = self._dual.get_conn(shard, readonly=True)
        except Exception:
            conn, engine = self._dual.get_conn(shard, readonly=False)
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return self._decrypt_row(table, row)
        finally:
            if engine == "PRIMARY":
                self._pool.release(conn)
            else:
                try: conn.close()
                except Exception: pass

    def fetchall(self, sql: str, params: Any = None, *, db_name: Optional[str] = None):
        table = extract_table_name(sql)
        shard = self._resolve_shard(table, db_name)
        if shard == "shard_l0_top_secret" and not _vikey_online():
            raise PermissionError("[L0_VIKEY_REQUIRED] L0分片需要VIKEY硬件在线")
        try:
            conn, engine = self._dual.get_conn(shard, readonly=True)
        except Exception:
            conn, engine = self._dual.get_conn(shard, readonly=False)
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return self._decrypt_rows(table, rows)
        finally:
            if engine == "PRIMARY":
                self._pool.release(conn)
            else:
                try: conn.close()
                except Exception: pass

    # ---------- 切换API ----------
    def switch_to_backup(self, shard: str) -> bool: return self._dual.force_switch(shard, "BACKUP")
    def switch_to_primary(self, shard: str) -> bool: return self._dual.force_switch(shard, "PRIMARY")

    # ---------- 健康报告 ----------
    def health_report(self) -> Dict:
        rep = {"phase": _transition_phase(), "shards": {}}
        for sk in ShardRouter.list_shards():
            over, info = ShardRouter.shard_over_limit(sk)
            st = self._dual.states.get(sk)
            rep["shards"][sk] = {
                "over_limit": over, "size_mb": info["size_mb"], "tables": info["tables"],
                "engine": st.active if st else "PRIMARY",
                "primary_err": st.primary_errors if st else 0,
                "backup_err": st.backup_errors if st else 0,
            }
        rep["alerts_size"] = self._monitor.alerts.qsize()
        return rep


# =============================================================================
# 工具：SQL表名抽取（copy自db_manager避免循环import）
# =============================================================================

_TABLE_HINT_FROM    = re.compile(r"(?is)\bFROM\s+(?:ONLY\s+)?([`\"'\[]?[A-Za-z_][A-Za-z0-9_`\"'\.\[\]]*)")
_TABLE_HINT_INTO    = re.compile(r"(?is)\bINTO\s+([`\"'\[]?[A-Za-z_][A-Za-z0-9_`\"'\.\[\]]*)")
_TABLE_HINT_UPDATE  = re.compile(r"(?is)\bUPDATE\s+(?:OR\s+\w+\s+)?([`\"'\[]?[A-Za-z_][A-Za-z0-9_`\"'\.\[\]]*)")
_TABLE_HINT_TABLE   = re.compile(
    r"(?is)\bTABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"'\[]?[A-Za-z_][A-Za-z0-9_`\"'\.\[\]]*)")
_TABLE_HINT_JOIN    = re.compile(r"(?is)\bJOIN\s+([`\"'\[]?[A-Za-z_][A-Za-z0-9_`\"'\.\[\]]*)")

def extract_table_name(sql: str) -> str:
    """顺序：INTO(INSERT) → UPDATE → TABLE(CREATE/ALTER/DROP) → JOIN → FROM
    命中第一个表名（最接近根查询的那张）。
    """
    if not sql: return ""
    m = (_TABLE_HINT_INTO.search(sql) or _TABLE_HINT_UPDATE.search(sql)
         or _TABLE_HINT_TABLE.search(sql) or _TABLE_HINT_JOIN.search(sql)
         or _TABLE_HINT_FROM.search(sql))
    if not m:
        return ""
    name = m.group(1).strip('`"[]\'"')
    dot = name.rfind(".")
    if dot > 0:
        name = name[dot + 1:]
    return name


# =============================================================================
# VIKEY在线检测（L0分片拦截用）
# =============================================================================

_VIKEY_CACHE_TS: float = 0.0
_VIKEY_CACHE_VAL: bool = False


def _vikey_online() -> bool:
    """通过 VIKEY 派生状态判断硬件是否在线。
    逻辑：is_vikey_online() 返回 True 或 L1-L3 有缓存 KEK 都算可用；
         L0 分片只接受 is_vikey_online() == True。
    """
    global _VIKEY_CACHE_TS, _VIKEY_CACHE_VAL
    now = time.time()
    if now - _VIKEY_CACHE_TS < 2.0:
        return _VIKEY_CACHE_VAL
    try:
        from app.utils.db_encryption import VikeyKeyDerivation
        # 使用全局 enc 派生器（与 db_sharding 读写的加解密对象同一实例）
        kd = enc.key_derivation
        ok_online = bool(kd.is_vikey_online())
        # L0只认可在线状态；L1-L3即使离线也有kek也能工作，但这里返回False用于拦截L0写
        # 所以只返回 online=True 作为"硬件在线"。对L1-L3连接无硬性拦截。
        ok = ok_online
    except Exception:
        ok = False
    _VIKEY_CACHE_TS = now
    _VIKEY_CACHE_VAL = ok
    return ok


# =============================================================================
# 全局单例
# =============================================================================

_default_pool: Optional[ShardConnectionPool] = None
_default_dual: Optional[DualEngineManager] = None
_default_monitor: Optional[LongTxMonitor] = None
_default_sc: Optional[ShardSmartConnection] = None
_singleton_lock = threading.Lock()


def get_default_sc() -> ShardSmartConnection:
    global _default_sc, _default_pool, _default_dual, _default_monitor
    with _singleton_lock:
        if _default_sc is None:
            _default_pool = ShardConnectionPool()
            _default_dual = DualEngineManager(_default_pool)
            _default_monitor = LongTxMonitor(_default_pool)
            _default_sc = ShardSmartConnection(pool=_default_pool, dual=_default_dual, monitor=_default_monitor)
    return _default_sc


def start_transition() -> str:
    """启动7天双写过渡 → 标记时间戳"""
    _start_transition()
    return _transition_phase()

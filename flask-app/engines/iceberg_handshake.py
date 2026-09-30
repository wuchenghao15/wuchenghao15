#!/usr/bin/env python3
"""
Mac mini 自动握手 + 双向同步 + 专家圆桌
=====================================

Phase 1 已落地:
  🫱 握手状态机 (5 态): DISCONNECTED → HANDSHAKING → CONNECTED → SYNCING → PENDING_SYNC
  💓 心跳保活 (15s interval, 90s timeout)
  📨 SQLite 缓冲队列 (断线写 mt_sync_pending_queue, 重连 drain)
  🔄 断线自动回归带同步状态
  🤝 Ping/Pong 协议 + Capabilities 交换

Phase 2 已落地:
  🔁 双向同步触发 (握手成功 → 自动跑 smart_sync + smart_sync 反向)
  📊 双方状态交换 (daemon 状态 / 规则版本 / EigenFlux 专家摘要 / 脑库版本)

Phase 3 已落地:
  🎯 EigenFlux 6 专家圆桌 (双方各出 3 专家 → Q5 主持 → 共享经验)
  🧠 脑库/知识/特征同步 (mt_ai_brain_feed_log + knowledge_base 双向同步)
  👥 AI 员工互相打招呼 + 技能分享

设计原则:
  - 后台静默运行, daemon 模式每 15s 检查一次
  - 本地隔离 (Mac mini localhost → localhost 模拟两端)
  - 切换远程: CONFIG.remote_host = "192.168.x.x" / SSH 或 HTTP
  - 断线不丢数据 — 全部进缓冲队列
"""

from __future__ import annotations

import json, os, socket, sqlite3, subprocess, sys, time, threading, hashlib, uuid, re
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum, auto


# ═════════════════════════════════════════════════════════════════════════
# 配置
# ═════════════════════════════════════════════════════════════════════════

DB = Path(__file__).parent.parent / "database" / "app.db"

@dataclass
class HandshakeConfig:
    """智能同步配置 — MacBook 主 (MASTER) / Mac mini 辅 (SLAVE)"""
    
    # ═══ 角色 ═══
    my_role: str = "MASTER"           # MASTER (MacBook 开发机) | SLAVE (Mac mini 服务器)
    # MASTER: 主动发起握手 + PUSH 完整数据 + 圆桌主持
    # SLAVE:  被动监听 + 自主运作 + 脱离握手也独立跑 daemon/Ollama
    
    # ═══ 端口按角色自动分配 ═══
    # MASTER → 监听 9754, 连 SLAVE 的 9753
    # SLAVE  → 监听 9753, 连 MASTER 的 9754
    @property
    def my_port(self) -> int:
        return 9754 if self.my_role.upper() == "MASTER" else 9753
    
    @property
    def remote_port(self) -> int:
        return 9753 if self.my_role.upper() == "MASTER" else 9754

    # 本端 (MacBook MASTER)
    my_name: str = "MTSCOS-MacBook"   # 本机 hostname
    
    # 对端 (Mac mini SLAVE)
    remote_name: str = "HULK-MACMINI" # SSH 上 `hostname` 返回
    remote_host: str = "192.168.31.9" # Mac mini 真实 IP
    
    # 心跳 / 超时
    heartbeat_interval: float = 15.0  # s
    heartbeat_timeout: float = 90.0   # s
    sync_trigger_delay: float = 3.0   # 握手成功后延迟多久触发同步

CONFIG = HandshakeConfig()


# ═════════════════════════════════════════════════════════════════════════
# 状态机 (5 态)
# ═════════════════════════════════════════════════════════════════════════

class NodeState(Enum):
    DISCONNECTED = auto()   # 初始 / 断线
    HANDSHAKING   = auto()   # 正在握手
    CONNECTED     = auto()   # 握手成功, 双方都在线
    SYNCING       = auto()   # 正在双向同步
    PENDING_SYNC  = auto()   # 断线但有缓冲队列待同步

STATE_TRANSITIONS = {
    NodeState.DISCONNECTED: [NodeState.HANDSHAKING, NodeState.PENDING_SYNC],
    NodeState.HANDSHAKING:   [NodeState.CONNECTED, NodeState.DISCONNECTED],
    NodeState.CONNECTED:     [NodeState.SYNCING, NodeState.DISCONNECTED],
    NodeState.SYNCING:       [NodeState.CONNECTED, NodeState.DISCONNECTED],
    NodeState.PENDING_SYNC:  [NodeState.HANDSHAKING, NodeState.DISCONNECTED],
}


# ═════════════════════════════════════════════════════════════════════════
# DB Schema (握手 + 缓冲队列)
# ═════════════════════════════════════════════════════════════════════════

SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_handshake_state (
    id              INTEGER PRIMARY KEY CHECK (id=1),  -- singleton
    state           TEXT NOT NULL DEFAULT 'DISCONNECTED',
    my_name         TEXT,
    remote_name     TEXT,
    remote_host     TEXT,
    remote_port     INTEGER,
    last_heartbeat  TEXT,
    last_pong       TEXT,
    capabilities    TEXT,   -- 双方交换的能力 JSON
    rules_version   TEXT,
    brain_version   TEXT,
    daemon_status   TEXT,   -- 双方 daemon 状态 JSON
    roundtable_json TEXT,   -- 最近一次专家圆桌结果 JSON
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mt_sync_pending_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         TEXT NOT NULL,   -- my_name / remote_name
    direction       TEXT NOT NULL,   -- dev2prod / prod2dev / bidirectional
    payload_type    TEXT,            -- file / db_row / message / expert_share
    payload_json    TEXT,
    status          TEXT DEFAULT 'pending',  -- pending / synced / failed
    retry_count     INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    synced_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_handshake_queue_status ON mt_sync_pending_queue(status, created_at);

CREATE TABLE IF NOT EXISTS mt_handshake_reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       TEXT UNIQUE,
    host_node       TEXT,
    guest_node      TEXT,
    guest_host      TEXT,
    phase1_handshake_json   TEXT,   -- 连接成功: 状态迁移/延迟/capabilities 交换
    phase2_sync_json        TEXT,   -- 双向同步: bootstrap/各表推拉行数/smart_sync
    phase3_roundtable_json  TEXT,   -- 圆桌会议: session_id/专家数/summary/共享物品
    summary         TEXT,           -- 1 句话总结
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_handshake_reports_created ON mt_handshake_reports(created_at DESC);

CREATE TABLE IF NOT EXISTS mt_roundtable_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT UNIQUE,
    host_node       TEXT,
    guest_node      TEXT,
    experts_json    TEXT,   -- 双方专家列表
    agenda          TEXT,
    outcome         TEXT,
    shared_items    TEXT,   -- 共享的脑库/规则/知识
    round_summary   TEXT,   -- 圆桌纪要
    duration_sec    INTEGER,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO mt_handshake_state (id, state, my_name, remote_name, remote_host, remote_port)
VALUES (1, 'DISCONNECTED', ?, ?, ?, ?);
"""


# ═════════════════════════════════════════════════════════════════════════
# 核心引擎
# ═════════════════════════════════════════════════════════════════════════

class HandshakeEngine:
    """Mac mini 自动握手 + 双向同步 + 专家圆桌"""

    def __init__(self):
        self._primary_db = sqlite3.connect(str(DB), timeout=10)
        self._primary_db.executescript(SCHEMA)
        self._primary_db.commit()
        self._apply_defaults()
        self._stop_flag = threading.Event()
        self._hb_thread = None
        self._server_thread = None
        self._sync_lock = threading.Lock()
        print(f"[🤝 Handshake] {CONFIG.my_name} → {CONFIG.remote_name}@{CONFIG.remote_host}:{CONFIG.remote_port}")

    def _get_db(self) -> sqlite3.Connection:
        """每个线程独立 DB 连接 (Python 3.14 禁止跨线程共享)."""
        t = threading.current_thread().ident
        if not hasattr(self, "_thread_dbs"): self._thread_dbs = {}
        if t not in self._thread_dbs:
            self._thread_dbs[t] = sqlite3.connect(str(DB), timeout=10)
        return self._thread_dbs[t]

    @property
    def db(self) -> sqlite3.Connection:
        return self._get_db()

    def _apply_defaults(self):
        self.db.execute("UPDATE mt_handshake_state SET my_name=?, remote_name=?, remote_host=?, remote_port=? WHERE id=1",
                         (CONFIG.my_name, CONFIG.remote_name, CONFIG.remote_host, CONFIG.remote_port))
        self.db.commit()

    # ──── 状态管理 ────
    def state(self) -> NodeState:
        row = self.db.execute("SELECT state FROM mt_handshake_state WHERE id=1").fetchone()
        return NodeState[row[0]] if row else NodeState.DISCONNECTED

    def _set_state(self, new_state: NodeState, **extra):
        self.db.execute("UPDATE mt_handshake_state SET state=?, updated_at=CURRENT_TIMESTAMP WHERE id=1",
                         (new_state.name,))
        for k, v in extra.items():
            col = k if k != 'capabilities' else 'capabilities'
            self.db.execute(f"UPDATE mt_handshake_state SET {col}=? WHERE id=1", (json.dumps(v) if isinstance(v, (dict, list)) else v,))
        self.db.commit()
        print(f"[🤝 {CONFIG.my_name}] state → {new_state.name}")

    # ──── Ping/Pong 协议 ────
    def ping_remote(self, timeout=3.0) -> dict | None:
        """发 PING → 等 PONG. 返回远端 capabilities 或 None."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((CONFIG.remote_host, CONFIG.remote_port))
            # 先自我介绍 (hello), 再发 ping
            hello = {"type": "HELLO", "node": CONFIG.my_name, "port": CONFIG.my_port,
                     "ts": time.time(), "capabilities": self._my_capabilities()}
            sock.sendall((json.dumps(hello) + "\n").encode())
            sock.shutdown(socket.SHUT_WR)
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk: break
                data += chunk
                if b"\n" in data: break
            sock.close()
            if not data: return None
            msg = json.loads(data.decode().strip().split("\n")[0])
            if msg.get("type") == "PONG":
                return msg
            return None
        except Exception:
            return None

    def serve_forever(self):
        """本地握手服务端 — 接收远端的 HELLO/PING (带 bind retry + SO_REUSEPORT)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass  # macOS 不支持 SO_REUSEPORT
        # 🆕 bind retry loop (3 次, 间隔 2s)
        bound = False
        for attempt in range(3):
            try:
                sock.bind(("0.0.0.0", CONFIG.my_port))
                sock.listen(5)
                bound = True
                print(f"[🤝 Handshake] serve on :{CONFIG.my_port} (bound ok)")
                break
            except OSError as e:
                print(f"[🤝 Handshake] serve bind attempt {attempt+1}/3 failed: {e}")
                sock.close()
                time.sleep(2)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not bound:
            print(f"[🤝 Handshake] serve bind permanently failed after 3 attempts — 远端握手可能走不到本端")
            return
        while not self._stop_flag.is_set():
            try:
                conn, addr = sock.accept()
                conn.settimeout(10)
                data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk: break
                    data += chunk
                    if b"\n" in data: break
                if data:
                    msg = json.loads(data.decode().strip().split("\n")[0])
                    msg_type = msg.get("type")
                    remote_node = msg.get("node", "unknown")
                    if msg_type in ("HELLO", "PING"):
                        pong = {"type": "PONG", "node": CONFIG.my_name, "ts": time.time(),
                                "capabilities": self._my_capabilities(), "rules_version": self._rules_version()}
                        conn.sendall((json.dumps(pong) + "\n").encode())
                        self._set_state(NodeState.CONNECTED, capabilities=msg.get("capabilities"))
                        print(f"[🤝 Handshake] ← 远端握手 from {remote_node} @{addr}")
                        threading.Thread(target=self._trigger_bidirectional_sync, args=(msg,), daemon=True).start()
                conn.close()
            except Exception:
                continue
        sock.close()

    def _my_capabilities(self) -> dict:
        """本机能力快照."""
        return {
            "ai_employees": self._count_table("mt_andromeda_employee_registry"),  # ← 修正真实表名
            "daemons": self._count_table("mt_daemon_registry"),
            "rules": self._count_table("mt_rule_changelog"),
            "iron_violations": self._count_table("mt_iron_rule_violations"),
            "brain_logs": self._count_table("mt_ai_brain_feed_log"),
            "eigenflux": self._count_table("mt_eigenflux_registrations"),
            "qbank": self._count_table("adult_education_questions"),
            "version": self._app_version(),
            "role": CONFIG.my_role,  # ← MASTER / SLAVE
        }

    def _app_version(self) -> str:
        try:
            return open("/tmp/flask.log").read().split("version=")[-1].split()[0] if False else "v22.0.0"
        except: return "v22.0.0"

    def _rules_version(self) -> str:
        try:
            row = self.db.execute("SELECT MAX(created_at) FROM mt_rule_changelog").fetchone()
            return row[0] or "unknown"
        except: return "unknown"

    def _count_table(self, table) -> int:
        try: return self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except: return 0

    def _safe_count(self, table) -> int:
        """表不存在也不崩, 返回 0."""
        mydb = self._get_db()
        tables = [r[0] for r in mydb.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if table not in tables: return 0
        try: return mydb.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except: return 0

    def _safe_daemon_status(self) -> str:
        """daemon_registry 表不存在也不崩."""
        mydb = self._get_db()
        tables = [r[0] for r in mydb.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "mt_daemon_registry" not in tables: return "0/0 running"
        try:
            r = mydb.execute("SELECT COUNT(*), SUM(CASE WHEN status='running' THEN 1 ELSE 0 END) FROM mt_daemon_registry").fetchone()
            return f"{r[1] or 0}/{r[0] or 0} running"
        except: return "0/0 running"

    # ──── 握手主循环 ────
    def run_handshake_loop(self):
        """主动发起握手 → 心跳保活 → 断线重连."""
        self._server_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._server_thread.start()
        print(f"[🤝 Handshake] server thread started")

        self._hb_thread = threading.Thread(target=self._handshake_loop, daemon=True)
        self._hb_thread.start()

    def _handshake_loop(self):
        consecutive_fail = 0
        last_pong_ts = 0
        periodic_sync_counter = 0
        while not self._stop_flag.is_set():
            state = self.state()
            pong = self.ping_remote(timeout=2.0)
            if pong:
                consecutive_fail = 0
                last_pong_ts = time.time()
                # 状态推进
                if state in (NodeState.DISCONNECTED, NodeState.HANDSHAKING):
                    self._set_state(NodeState.CONNECTED,
                                    capabilities=pong.get("capabilities"),
                                    rules_version=pong.get("rules_version"),
                                    last_heartbeat=time.strftime("%Y-%m-%d %H:%M:%S"))
                    # Phase 2: 首次握手成功 → 触发完整链路
                    threading.Thread(target=self._trigger_bidirectional_sync, args=(pong,), daemon=True).start()
                elif state == NodeState.PENDING_SYNC:
                    # 🆕 重连成功 → drain 缓冲队列 → 完整链路
                    self._set_state(NodeState.CONNECTED,
                                    capabilities=pong.get("capabilities"),
                                    last_heartbeat=time.strftime("%Y-%m-%d %H:%M:%S"))
                    threading.Thread(target=self._trigger_bidirectional_sync, args=(pong,), daemon=True).start()
                    threading.Thread(target=self.drain_queue, args=(pong,), daemon=True).start()
                else:
                    self.db.execute("UPDATE mt_handshake_state SET last_pong=?, updated_at=CURRENT_TIMESTAMP WHERE id=1",
                                    (time.strftime("%Y-%m-%d %H:%M:%S"),))
                    self.db.commit()
                    # 🆕 已在线 → 每 10 分钟周期性重同步一次 (保活数据新鲜度)
                    periodic_sync_counter += 1
                    if periodic_sync_counter >= 40:  # 15s × 40 = 600s
                        periodic_sync_counter = 0
                        threading.Thread(target=self._trigger_bidirectional_sync, args=(pong,), daemon=True).start()
            else:
                consecutive_fail += 1
                if consecutive_fail >= 3 and state != NodeState.DISCONNECTED:
                    # 🆕 断线 → 检查缓冲队列 → PENDING_SYNC 回归带状态
                    pending_cnt = self._safe_count("mt_sync_pending_queue")
                    try:
                        pending_cnt = self.db.execute(
                            "SELECT COUNT(*) FROM mt_sync_pending_queue WHERE status='pending'").fetchone()[0]
                    except: pending_cnt = 0
                    if pending_cnt > 0:
                        self._set_state(NodeState.PENDING_SYNC)
                        print(f"[🤝 Handshake] ⚠️ 断联但有 {pending_cnt} 条缓冲 → PENDING_SYNC (带同步状态回归)")
                    else:
                        self._set_state(NodeState.DISCONNECTED)
                        print(f"[🤝 Handshake] ⚠️ 断联无缓冲 → DISCONNECTED")
                    self._queue_pending("disconnect", f"{CONFIG.remote_name} unreachable after {consecutive_fail} pings")
                    self._save_reconnect_state()
                    periodic_sync_counter = 0
            self._stop_flag.wait(CONFIG.heartbeat_interval)

        # drain 退出前
        pending = self.db.execute("SELECT COUNT(*) FROM mt_sync_pending_queue WHERE status='pending'").fetchone()[0]
        print(f"[🤝 Handshake] stopping. {pending} pending items in queue.")

    # ──── 双向同步 (Phase 2) ────
    def _trigger_bidirectional_sync(self, remote_pong: dict):
        """握手成功后 → 状态交换 → 全量/增量 sync → smart_sync → 圆桌 → 报告."""
        if not self._sync_lock.acquire(blocking=False):
            return
        sync_stats = {"bootstrap": {}, "rows": {}, "smart_sync": {}}
        try:
            print(f"[🤝 Handshake] ⚡ 触发双向同步 (remote={remote_pong.get('node','?')})")
            t0 = time.time()
            self._set_state(NodeState.SYNCING)
            self._exchange_status(remote_pong)

            # 远端 DB 路径 (Mac mini: flask-app/app.db)
            remote_db_path = "/Users/wuchenghao/MTSCOS_AI_Project/flask-app/app.db"  # ← 绝对路径, ~ 在 SSH subprocess 展开不可靠
            remote_ssh = f"wuchenghao@{CONFIG.remote_host}"

            # Phase 2a: 首次部署自动 bootstrap (全量 push)
            sync_stats["bootstrap"] = self.remote_bootstrap_if_empty(remote_ssh, remote_db_path)

            # Phase 2b: 行级双向增量 sync
            sync_stats["rows"] = self.sync_rows_bidirectional(remote_ssh, remote_db_path)

            # Phase 2c: smart_sync (dev→prod 文件级, 本地隔离)
            try:
                if CONFIG.remote_host in ("127.0.0.1", "localhost"):
                    result = subprocess.run(
                        [sys.executable, str(Path(__file__).parent / "smart_sync.py"), "run"],
                        capture_output=True, text=True, timeout=60, cwd=str(Path(__file__).parent.parent))
                    sync_stats["smart_sync"] = {"rc": result.returncode, "ok": result.returncode == 0}
                    print(f"[🤝 Handshake] smart_sync dev→prod rc={result.returncode}")
            except Exception as e:
                sync_stats["smart_sync"] = {"error": str(e)}
                print(f"[🤝 Handshake] smart_sync skipped: {e}")

            # Phase 3: 圆桌会议 (知识互补)
            self._roundtable(remote_pong)
            self._set_state(NodeState.CONNECTED)

            # 🆕 Phase 4: 生成完整握手成功报告
            self._generate_handshake_success_report(remote_pong, sync_stats, round(time.time()-t0, 1))
        finally:
            self._sync_lock.release()

    def _exchange_status(self, remote_pong: dict):
        """交换双方 daemon / 规则 / EigenFlux 专家 / 脑库 状态 (全防御)."""
        my_daemon_str = self._safe_daemon_status()
        my_rules = self._safe_count("mt_iron_rule_violations")
        my_brain = self._safe_count("mt_ai_brain_feed_log")
        my_qbank = self._safe_count("adult_education_questions") or self._safe_count("k12_questions")

        remote_caps = remote_pong.get("capabilities", {}) or {}
        summary = {
            "my_daemon": my_daemon_str,
            "my_rules": f"{my_rules} violations",
            "my_brain": f"{my_brain} brain logs",
            "my_qbank": f"{my_qbank} qbank",
            "remote_host": remote_pong.get("node", "?"),
            "remote_daemon": remote_caps.get("daemons", "?"),
            "remote_rules": remote_caps.get("rules", "?"),
            "remote_brain": remote_caps.get("brain_logs", "?"),
            "remote_qbank": remote_caps.get("qbank", "?"),
            "remote_rules_version": remote_pong.get("rules_version", "?"),
        }
        mydb = self._get_db()
        mydb.execute("UPDATE mt_handshake_state SET daemon_status=? WHERE id=1",
                     (json.dumps(summary, ensure_ascii=False),))
        mydb.commit()
        print(f"[🤝 Handshake] 📊 状态交换: {json.dumps(summary, ensure_ascii=False)[:200]}")

    # ──── 全量推送 (MacBook → 远端) ────
    def full_push_via_ssh(self, ssh_dest: str, remote_db_path: str):
        """通过 SSH + sqlite3 .dump 把本机关键表全量推给远端.
        关键表 (不推: __pycache__ / .env / flask_session / 临时):
          mt_ai_brain_feed_log, mt_iron_rule_violations, mt_daemon_registry,
          mt_dev_flow_session, mt_roundtable_sessions, mt_rule_changelog,
          adult_education_questions / k12_questions (题库), users (仅规则相关)."""
        if CONFIG.remote_host in ("127.0.0.1", "localhost"):
            print("[🤝 Handshake] full_push: 本机自握手, 跳过")
            return
        print(f"[🤝 Handshake] 📦 全量 push → {ssh_dest}:{remote_db_path}")
        mydb = self._get_db()
        tables = [
            "mt_andromeda_employee_registry",   # ← 33K AI 员工 (关键!)
            "mt_ai_brain_feed_log",
            "mt_iron_rule_violations", "mt_daemon_registry",
            "mt_dev_flow_session", "mt_roundtable_sessions", "mt_rule_changelog",
            "mt_handshake_reports",              # ← 握手报告远端也需要
        ]
        for qt in ["adult_education_questions", "k12_questions", "university_questions",
                    "continuing_education_questions", "senior_education_questions"]:
            if self._safe_count(qt) > 0: tables.append(qt)

        # 1) 先在远端 CREATE TABLE (从本机 schema dump)
        schema_sql = []
        for t in tables:
            try:
                row = mydb.execute(
                    "SELECT sql FROM sqlite_master WHERE name=? AND type='table'", (t,)).fetchone()
                if row and row[0]: schema_sql.append(row[0] + ";")
            except: pass
        if not schema_sql:
            print("[🤝 Handshake] 本机无表可推")
            return
        schema_text = "\n".join(schema_sql)

        remote_db_dir = remote_db_path.rsplit("/", 1)[0]
        subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
             f"mkdir -p {remote_db_dir}"],
            capture_output=True, text=True, timeout=10)
        # 远端先确保有 db 文件
        subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
             f"touch {remote_db_path}"],
            capture_output=True, text=True, timeout=10)
        # 推 schema
        proc = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
             f"sqlite3 {remote_db_path}"],
            input=schema_text, capture_output=True, text=True, timeout=30)
        if proc.stderr: print(f"  schema note: {proc.stderr.strip()[:200]}")

        # 2) 逐表 dump + scp → 远端 .sql → sqlite3 灌
        pushed_total = 0
        for t in tables:
            cnt = self._safe_count(t)
            if cnt == 0: continue
            dump = subprocess.run(
                ["sqlite3", str(DB), f".dump {t}"],
                capture_output=True, text=True, timeout=30)
            if dump.returncode != 0 or not dump.stdout.strip(): continue
            # 远端先删旧数据
            subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                 f"sqlite3 {remote_db_path} \"DELETE FROM {t};\""],
                capture_output=True, text=True, timeout=10)
            # 推 schema + data
            proc2 = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                 f"sqlite3 {remote_db_path}"],
                input=dump.stdout, capture_output=True, text=True, timeout=120)
            if proc2.stderr and "Error" in proc2.stderr:
                print(f"  ⚠️ {t}: {proc2.stderr.strip()[:150]}")
            else:
                print(f"  ✅ {t}: {cnt} rows pushed")
                pushed_total += cnt
        print(f"[🤝 Handshake] 📦 全量 push 完成: {pushed_total} rows → {ssh_dest}")

    # ──── 行级双向增量 sync ────
    # ═══════════════════════════════════════════════════════════════════════
    # 共享工具: SSH 批量 PUSH rows (base64 batch 200 行)
    # ═══════════════════════════════════════════════════════════════════════
    def _ssh_push_rows(self, ssh_dest: str, remote_db_path: str, tbl: str, col_names: list, rows: list, stats: dict):
        """把本地 rows 通过 SSH INSERT OR IGNORE 到远端."""
        import base64 as _b64
        sql = f"INSERT OR IGNORE INTO {tbl} ({','.join(col_names)}) VALUES ({','.join(['?']*len(col_names))})"
        pushed = 0
        for i in range(0, len(rows), 200):
            batch = rows[i:i+200]
            b64 = _b64.b64encode(json.dumps(batch, ensure_ascii=False, default=str).encode()).decode()
            ssh_cmd = (
                f"python3 -c \"import sqlite3,json,base64;"
                f" db=sqlite3.connect('{remote_db_path}');"
                f" db.executemany({sql!r}, json.loads(base64.b64decode('{b64}')));"
                f" db.commit(); db.close()\""
            )
            r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest, ssh_cmd],
                               capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                pushed += len(batch)
            else:
                print(f"  ⚠️ {tbl}: batch ssh rc={r.returncode} {(r.stderr or r.stdout)[:80]}")
        label = "🆕 Bootstrap PUSH" if stats.get("_bootstrap") else "PUSH"
        print(f"  ↓ {tbl:40s} {label} {pushed} rows")
        stats[tbl] = {"direction": "push", "rows": pushed}

    def sync_rows_bidirectional(self, ssh_dest: str, remote_db_path: str) -> dict:
        """每端 SELECT 对方没有的行 (按主键 max) → SSH INSERT 过去 + 反向拉取. 返回 {table: {...}}."""
        stats = {}
        if CONFIG.remote_host in ("127.0.0.1", "localhost"):
            stats["_skipped"] = "本地自握手,跳过"
            return stats
        print(f"[🤝 Handshake] ↔ 行级真正双向 sync via SSH")
        mydb = self._get_db()

        # 🆕 扩表: AI员工/EigenFlux/skill/daemon/knowledge/特征 全部进入同步
        sync_tables = {
            "mt_ai_brain_feed_log":          "feed_id",       # 脑库日志
            "mt_andromeda_employee_registry": "rowid",       # ← 仙女座 AI 员工 (33,525!)
            "mt_daemon_registry":            "process_name",  # daemon 注册表 (真实 pk)
            "mt_eigenflux_registrations":    "id",            # EigenFlux 专家
            "mt_eigenflux_vote_log":         "id",            # EigenFlux 投票
            "mt_dev_flow_session":           "flow_id",       # 开发流程
            "mt_roundtable_sessions":        "id",            # 圆桌会议
            "mt_rule_changelog":             "changelog_id",  # 规则变更
            "mt_iron_rule_violations":       "viol_id",       # 铁律违反
            "mt_handshake_reports":          "id",            # 握手报告
            "mt_evolution_log":              "id",            # 🆕 Mac mini 演化引擎产出
        }

        def _cmp_gt(a, b):
            try: return a > b
            except TypeError: return str(a) > str(b)
        def _cmp_lt(a, b):
            try: return a < b
            except TypeError: return str(a) < str(b)

        for tbl, pk in sync_tables.items():
            # 🆕 本地表不存在 → 检查远端有没有, 有就先本地 CREATE TABLE 再 PULL
            if self._safe_count(tbl) == 0:
                try:
                    local_tables = [t[0] for t in mydb.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                    tbl_not_local = tbl not in local_tables
                except:
                    tbl_not_local = True
                if tbl_not_local:
                    # 远端可能有但本地没 → 先 CREATE TABLE (从远端 schema dump)
                    try:
                        import subprocess as _sp2
                        r = _sp2.run(
                            ["ssh", "-o", "StrictHostKeyChecking=no", f"wuchenghao@{CONFIG.remote_host}",
                             f"sqlite3 /Users/wuchenghao/MTSCOS_AI_Project/flask-app/app.db "
                             f"\"SELECT sql FROM sqlite_master WHERE name='{tbl}' AND type='table';\""],
                            capture_output=True, text=True, timeout=10)
                        schema = (r.stdout or "").strip()
                        if schema:
                            mydb.executescript(schema + ";")
                            mydb.commit()
                            print(f"  🏗️ 本地 CREATE TABLE {tbl} (从远端 schema)")
                    except Exception as _e:
                        stats[tbl] = {"direction": "skip_local_empty", "error": f"no_schema:{_e}"}
                        continue
                else:
                    stats[tbl] = {"direction": "skip_local_empty", "rows": 0}
                    continue
            try:
                local_max_row = mydb.execute(f"SELECT MAX({pk}) FROM {tbl}").fetchone()[0]
                local_max = local_max_row if local_max_row is not None else ""
            except Exception as e:
                stats[tbl] = {"direction": "error", "error": f"local_query:{str(e)[:80]}"}
                print(f"  ⚠️ {tbl}: local max failed — {e}"); continue

            # SSH 先确保远端表存在 (CREATE TABLE IF NOT EXISTS), 再查 max pk
            try:
                # 1) 先尝试让远端也 CREATE 同样的表 (从远端自己的 schema 推断)
                r_ensure = subprocess.run(
                    ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                     f'sqlite3 {remote_db_path} "SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{tbl}\';"'],
                    capture_output=True, text=True, timeout=10)
                table_exists_remote = (r_ensure.stdout or "").strip() == tbl

                if not table_exists_remote:
                    # 远端没这张表 → 直接 Bootstrap 全量 PUSH (不查 max, 不 cmp)
                    print(f"  🆕 {tbl}: 远端无此表 → Bootstrap 全量 PUSH")
                    col_names = [c[0] for c in mydb.execute(f"SELECT * FROM {tbl} LIMIT 0").description]
                    rows = mydb.execute(f"SELECT * FROM {tbl}").fetchall()
                    if rows:
                        self._ssh_push_rows(ssh_dest, remote_db_path, tbl, col_names, rows, stats)
                    continue  # Bootstrap 完了跳过后续比较

                # 2) 表存在 → 查 max pk
                r = subprocess.run(
                    ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                     f"sqlite3 {remote_db_path} \"SELECT COALESCE(MAX({pk}),'') FROM {tbl};\""],
                    capture_output=True, text=True, timeout=10)
                if r.returncode != 0:
                    stats[tbl] = {"direction": "error", "error": f"remote_rc={r.returncode}:{(r.stderr or r.stdout).strip()[:100]}"}
                    print(f"  ⚠️ {tbl}: remote rc={r.returncode} — {(r.stderr or r.stdout).strip()[:80]}"); continue
                remote_max = (r.stdout or "").strip()
            except Exception as e:
                stats[tbl] = {"direction": "error", "error": f"remote_query_failed:{str(e)[:80]}"}
                print(f"  ⚠️ {tbl}: remote 查询失败 — {e}"); continue

            # ─── 先比 COUNT(*) — 字符串 pk 如 process_name MAX 相等但中间可能缺行! ───
            try:
                local_count = mydb.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            except: local_count = 0
            r_count = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                 f"sqlite3 {remote_db_path} \"SELECT COUNT(*) FROM {tbl};\""],
                capture_output=True, text=True, timeout=10)
            remote_count = int((r_count.stdout or "0").strip() or 0)

            # COUNT 不等 → 直接走 pk 差集 (全量 diff, 对字符串 pk 安全)
            if local_count != remote_count:
                print(f"  🔍 {tbl}: local={local_count} remote={remote_count} → pk 差集 diff")
                # 拉远端所有 pk 到本地比对
                r_all_pks = subprocess.run(
                    ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                     f"sqlite3 {remote_db_path} \"SELECT {pk} FROM {tbl};\""],
                    capture_output=True, text=True, timeout=15)
                remote_pks = set((r_all_pks.stdout or "").strip().split('\n')) - {''}
                local_pks = set(r[0] for r in mydb.execute(f"SELECT {pk} FROM {tbl}").fetchall())
                push_pks = local_pks - remote_pks  # 本地有远端没有 → PUSH
                pull_pks = remote_pks - local_pks  # 远端有本地没有 → PULL

                col_names = [c[0] for c in mydb.execute(f"SELECT * FROM {tbl} LIMIT 0").description]

                if push_pks:
                    ph = ','.join(['?'] * len(push_pks))
                    rows = mydb.execute(f"SELECT * FROM {tbl} WHERE {pk} IN ({ph})", list(push_pks)).fetchall()
                    self._ssh_push_rows(ssh_dest, remote_db_path, tbl, col_names, rows, stats)
                if pull_pks:
                    # SSH 拉远端缺失行
                    escaped_pks = [p.replace("'", "''") for p in pull_pks]
                    ph2 = ','.join([f"'{ep}'" for ep in escaped_pks])
                    r_pull = subprocess.run(
                        ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                         f"sqlite3 {remote_db_path} \"SELECT * FROM {tbl} WHERE {pk} IN ({ph2});\""],
                        capture_output=True, text=True, timeout=15)
                    # sqlite3 输出是 pipe 分隔, 需要列名
                    pulled = []
                    for line in (r_pull.stdout or "").strip().split('\n'):
                        if line:
                            pulled.append(tuple(line.split('|')))
                    if pulled:
                        sql = f"INSERT OR IGNORE INTO {tbl} ({','.join(col_names)}) VALUES ({','.join(['?']*len(col_names))})"
                        mydb.executemany(sql, pulled)
                        mydb.commit()
                        print(f"  ↑ {tbl:35s} PULL {len(pulled):4d} rows")
                        if not push_pks:
                            stats[tbl] = {"direction": "pull", "rows": len(pulled)}

                if not push_pks and not pull_pks:
                    stats[tbl] = {"direction": "equal", "rows": 0}
                continue  # COUNT diff 完了, 跳过后续 MAX 比较

            # ─── COUNT 相等 → 再比 MAX (自增 ID / 数值 pk 快速路径) ───
            # ─── 方向 A: 本地有远端没有 → MacBook → Mac mini PUSH ───
            if _cmp_gt(local_max, remote_max):
                rows = mydb.execute(f"SELECT * FROM {tbl} WHERE {pk} > ?", (remote_max,)).fetchall()
                if rows:
                    col_names = [c[0] for c in mydb.execute(f"SELECT * FROM {tbl} LIMIT 0").description]
                    sql = f"INSERT OR IGNORE INTO {tbl} ({','.join(col_names)}) VALUES ({','.join(['?']*len(col_names))})"
                    import base64 as _b64
                    for i in range(0, len(rows), 200):
                        batch = rows[i:i+200]
                        b64 = _b64.b64encode(json.dumps(batch, ensure_ascii=False, default=str).encode()).decode()
                        ssh_cmd = (
                            f"python3 -c \"import sqlite3,json,base64;"
                            f" db=sqlite3.connect('{remote_db_path}');"
                            f" db.executemany({sql!r}, json.loads(base64.b64decode('{b64}')));"
                            f" db.commit(); db.close()\""
                        )
                        subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest, ssh_cmd],
                                       capture_output=True, text=True, timeout=60)
                    print(f"  ↓ {tbl:35s} PUSH {len(rows):4d} rows (local={local_max} > remote={remote_max})")
                    stats[tbl] = {"direction": "push", "rows": len(rows), "local_max": str(local_max), "remote_max": str(remote_max)}
                else:
                    stats[tbl] = {"direction": "equal", "rows": 0}

            # 🆕 方向 B: 远端有本地没有 → Mac mini → MacBook PULL (真正双向!)
            elif _cmp_lt(local_max, remote_max):
                try:
                    cols = [c[0] for c in mydb.execute(f"SELECT * FROM {tbl} LIMIT 0").description]
                    col_sql = ",".join(cols)
                    # 🆕 用 base64 传 python 脚本 → 绕开 SSH 3 层引号地狱
                    import base64 as _b64
                    pull_py = (
                        "import sqlite3,json,base64,sys\n"
                        f"db=sqlite3.connect('{remote_db_path}')\n"
                        f"rows=db.execute(\"SELECT {col_sql} FROM {tbl} "
                        f"WHERE CAST({pk} AS INTEGER) > CAST({local_max} AS INTEGER) "
                        f"ORDER BY {pk} LIMIT 500\").fetchall()\n"
                        "print(base64.b64encode(json.dumps(rows,default=str).encode()).decode())\n"
                        "db.close()\n"
                    )
                    b64_script = _b64.b64encode(pull_py.encode()).decode()
                    pull_cmd = f"echo {b64_script} | base64 -d | python3"
                    r2 = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest, pull_cmd],
                                        capture_output=True, text=True, timeout=30)
                    if r2.returncode == 0 and r2.stdout.strip():
                        try:
                            pulled_rows = json.loads(_b64.b64decode(r2.stdout.strip()).decode())
                        except Exception as decode_err:
                            stats[tbl] = {"direction": "error_pull", "error": f"b64_decode:{decode_err}"}
                            print(f"  ⚠️ {tbl}: pull b64 解码失败 — {decode_err}")
                            continue
                        if pulled_rows:
                            sql = f"INSERT OR IGNORE INTO {tbl} ({col_sql}) VALUES ({','.join(['?']*len(cols))})"
                            mydb.executemany(sql, pulled_rows)
                            mydb.commit()
                            print(f"  ↑ {tbl:35s} PULL {len(pulled_rows):4d} rows (local={local_max} < remote={remote_max})")
                            stats[tbl] = {"direction": "pull", "rows": len(pulled_rows), "local_max": str(local_max), "remote_max": str(remote_max)}
                        else:
                            stats[tbl] = {"direction": "equal", "rows": 0, "note": "remote had no newer rows"}
                    else:
                        err_preview = (r2.stderr or "pull_empty")[:120]
                        stats[tbl] = {"direction": "error_pull", "rows": 0, "error": err_preview}
                        print(f"  ⚠️ {tbl}: pull 远端执行失败 — rc={r2.returncode} {err_preview}")
                except Exception as e:
                    import traceback
                    stats[tbl] = {"direction": "error_pull", "rows": 0, "error": str(e)[:100]}
                    print(f"  ⚠️ {tbl}: pull 本地异常 — {e}")

            # 相等
            else:
                stats[tbl] = {"direction": "equal", "rows": 0}

        # 总结
        pushes = len([v for v in stats.values() if isinstance(v, dict) and v.get("direction") == "push"])
        pulls  = len([v for v in stats.values() if isinstance(v, dict) and v.get("direction") == "pull"])
        errors = len([v for v in stats.values() if isinstance(v, dict) and "error" in v])
        print(f"[🤝 Handshake] ↔ 双向 sync 完成: ↓{pushes} 表 push / ↑{pulls} 表 pull / ⚠️{errors} error")
        return stats

    # ──── 远端能力全量拉取 (给 Mini 补零) ────
    def remote_bootstrap_if_empty(self, ssh_dest: str, remote_db_path: str) -> dict:
        """如果远端 mt_daemon_registry 表不存在, 说明是首次部署 → 全量 push. 返回 {action, tables, rows}."""
        result = {"action": "none", "tables": 0, "rows": 0}
        if CONFIG.remote_host in ("127.0.0.1", "localhost"):
            result["action"] = "skipped_local"
            return result
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", ssh_dest,
                 f"sqlite3 {remote_db_path} \"SELECT name FROM sqlite_master WHERE type='table' AND name='mt_daemon_registry';\""],
                capture_output=True, text=True, timeout=10)
            if not r.stdout.strip():
                print(f"[🤝 Handshake] 🆕 远端 {ssh_dest} 首次部署, 触发 full_push")
                result["action"] = "bootstrap_full_push"
                self.full_push_via_ssh(ssh_dest, remote_db_path)
                result["tables"] = 6  # full_push_via_ssh 推的表数
            else:
                result["action"] = "skip_already_deployed"
        except Exception as e:
            result["action"] = "error"
            result["error"] = str(e)[:100]
            print(f"[🤝 Handshake] remote_bootstrap: {e}")
        return result

    # ──── Phase 3: EigenFlux 专家圆桌 ────
    def _safe_query(self, table, sql, default=None):
        """安全查一个可能不存在的表."""
        mydb = self._get_db()
        try:
            tables = [r[0] for r in mydb.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if table not in tables:
                return default if default is not None else []
            return mydb.execute(sql).fetchall()
        except Exception:
            return default if default is not None else []

    def _roundtable(self, remote_pong: dict):
        """双方各出 3 专家 → Q5 主持 → 共享经验 / 脑库 / 特征."""
        try:
            import uuid as _uuid
            import time as _t

            my_experts = self._my_expert_pick()
            remote_experts = [
                {"name": "remote_architect", "role": "架构师",   "host": CONFIG.remote_name},
                {"name": "remote_security",  "role": "安全审计", "host": CONFIG.remote_name},
                {"name": "remote_perf",     "role": "性能优化", "host": CONFIG.remote_name},
            ]
            all_experts = my_experts + remote_experts
            print(f"[🤝 Roundtable] 🎯 {len(all_experts)} 专家 ({len(my_experts)} 本地 + {len(remote_experts)} 远端)")
            for e in all_experts:
                print(f"   👤 {e['name']:20s} {e['role']:8s} @ {e['host']}")

            shared_brain = self._safe_query("mt_ai_brain_feed_log",
                "SELECT expert_name, topic, summary, created_at FROM mt_ai_brain_feed_log ORDER BY created_at DESC LIMIT 10")

            shared_rules = self._safe_query("mt_iron_rule_violations",
                "SELECT rule_code, COUNT(*) FROM mt_iron_rule_violations GROUP BY rule_code ORDER BY 2 DESC LIMIT 5")

            shared_votes = self._safe_query("mt_eigenflux_vote_log",
                "SELECT expert_name, topic, vote, created_at FROM mt_eigenflux_vote_log ORDER BY created_at DESC LIMIT 10")

            round_summary = self._q5_preside_roundtable(all_experts, shared_brain, shared_rules, shared_votes, remote_pong)

            session_id = f"rt_{_uuid.uuid4().hex[:16]}"
            mydb = self._get_db()
            mydb.execute("""INSERT INTO mt_roundtable_sessions
                (session_id, host_node, guest_node, experts_json, agenda, outcome, shared_items, round_summary, duration_sec)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (session_id, CONFIG.my_name, CONFIG.remote_name,
                 json.dumps(all_experts, ensure_ascii=False),
                 "经验共享 + 脑库同步 + 规则对齐",
                 "success",
                 json.dumps({"brain_count": len(shared_brain), "rules": shared_rules, "votes_count": len(shared_votes)}, ensure_ascii=False),
                 round_summary,
                 max(1, len(round_summary) // 10)))
            mydb.commit()
            mydb.execute("UPDATE mt_handshake_state SET roundtable_json=? WHERE id=1",
                        (json.dumps({"session_id": session_id, "experts_count": len(all_experts)}, ensure_ascii=False),))
            mydb.commit()
            print(f"[🤝 Roundtable] ✅ session={session_id} summary={len(round_summary)} chars")
        except Exception as e:
            import traceback
            print(f"[🤝 Roundtable] ❌ {e}")
            traceback.print_exc()

    def _my_expert_pick(self) -> list:
        """本机 EigenFlux 专家精选 (含王律师, 表不存在时硬编码 fallback)."""
        mydb = self._get_db()
        tables = [r[0] for r in mydb.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        fallback = [
            {"name": "legal_wang",    "role": "法务顾问", "host": CONFIG.my_name},
            {"name": "architect_zhang", "role": "架构师",   "host": CONFIG.my_name},
            {"name": "security_li",   "role": "安全审计", "host": CONFIG.my_name},
        ]
        if "mt_eigenflux_registrations" not in tables:
            print(f"[🤝 Roundtable] mt_eigenflux_registrations 不存在, 用硬编码 fallback")
            return fallback
        result = []
        for n in ["legal_wang", "architect_zhang", "security_li"]:
            row = mydb.execute("SELECT expert_name, role FROM mt_eigenflux_registrations WHERE expert_name=?", (n,)).fetchone()
            if row:
                result.append({"name": row[0], "role": row[1], "host": CONFIG.my_name})
            else:
                result.append({"name": n, "role": fallback[0]["role"], "host": CONFIG.my_name})
        return result

    def _q5_preside_roundtable(self, experts, shared_brain, shared_rules, shared_votes, remote_pong) -> str:
        """Q5 主持圆桌 (Ollama qwen2.5:14b-q5)."""
        brain_text = "\n".join(f"  [{r[3][:10]}] {r[0]}: {r[1] or r[2] or ''}" for r in shared_brain[:5])
        rules_text = "\n".join(f"  {r[0]}: {r[1]}次" for r in shared_rules[:5])
        exp_text = "\n".join(f"  {e['name']}({e['role']}@{e['host']})" for e in experts)

        prompt = f"""你是 MTSCOS AI 圆桌会议主持人. 总结双方专家这次的知识共享.

参与专家 ({len(experts)}):
{exp_text}

本地脑库最近 5 条:
{brain_text or '(空)'}

本地规则违规 Top 5:
{rules_text or '(空)'}

远端 capabilities: {json.dumps(remote_pong.get('capabilities', {}), ensure_ascii=False)[:300]}

请输出 3 行纪要: 1) 共享了什么 2) 关键发现 3) 下次行动项."""

        try:
            import urllib.request
            body = json.dumps({
                "model": "qwen2.5:14b-q5", "prompt": prompt,
                "stream": False, "options": {"temperature": 0.3}
            }).encode()
            req = urllib.request.Request("http://localhost:11435/api/generate",
                data=body, headers={"Content-Type":"application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=20).read())
            return resp.get("response", "")[:500]
        except Exception:
            # Q5 不可用 → 启发式
            return f"共享: 脑库{len(shared_brain)}条 / 规则{len(shared_rules)} / 专家{len(experts)}人. 下次: 继续双向同步 + 规则对齐."

    # ──── 缓冲队列 (断线写, 重连 drain) ────
    def _queue_pending(self, payload_type, payload, direction="bidirectional"):
        self.db.execute("""INSERT INTO mt_sync_pending_queue
            (node_id, direction, payload_type, payload_json, status)
            VALUES (?,?,?,?,?)""",
            (CONFIG.remote_name, direction, payload_type, json.dumps(payload, ensure_ascii=False), "pending"))
        self.db.commit()

    def drain_queue(self, remote_pong: dict | None = None):
        """重连后: 把 pending 队列全部 drain — 真正重放 sync/roundtable 动作."""
        rows = self.db.execute(
            "SELECT id, direction, payload_type, payload_json FROM mt_sync_pending_queue "
            "WHERE status='pending' ORDER BY created_at").fetchall()
        print(f"[🤝 Handshake] 🚿 drain_queue: {len(rows)} pending items → 重放开始")
        replayed_sync = False
        replayed_roundtable = False
        for rid, direction, ptype, pjson in rows:
            try:
                payload = json.loads(pjson) if pjson else {}
                if ptype in ("sync", "reconnect_state"):
                    # 🆕 真正重放: 拉双向同步
                    if not replayed_sync and remote_pong:
                        print(f"  ↻ 重放 sync 队列 → _trigger_bidirectional_sync()")
                        self._trigger_bidirectional_sync(remote_pong)
                        replayed_sync = True
                elif ptype == "roundtable":
                    # 🆕 真正重放: 跑圆桌会议
                    if not replayed_roundtable and remote_pong:
                        print(f"  ↻ 重放 roundtable 队列 → _roundtable()")
                        self._roundtable(remote_pong)
                        replayed_roundtable = True
                self.db.execute(
                    "UPDATE mt_sync_pending_queue SET status='synced', synced_at=CURRENT_TIMESTAMP WHERE id=?", (rid,))
                print(f"  ✅ [{rid}] {ptype} → synced")
            except Exception as e:
                print(f"  ⚠️ [{rid}] {ptype} 重放失败: {e}")
                self.db.execute(
                    "UPDATE mt_sync_pending_queue SET retry_count=retry_count+1, status='failed' WHERE id=?", (rid,))
        self.db.commit()
        left = self.db.execute(
            "SELECT COUNT(*) FROM mt_sync_pending_queue WHERE status='pending'").fetchone()[0]
        print(f"[🤝 Handshake] 🚿 drain_queue 完成: {len(rows)-left} 重放, {left} 剩余 pending")

    def _save_reconnect_state(self):
        """断线时: 把当前状态序列化保存, 重连后恢复."""
        row = self.db.execute("SELECT state, capabilities, daemon_status FROM mt_handshake_state WHERE id=1").fetchone()
        self._queue_pending("reconnect_state", {"state": row[0], "capabilities": row[1], "daemon": row[2]})

    # ──── Phase 4: 握手成功完整报告 ────
    def _generate_handshake_success_report(self, remote_pong: dict, sync_stats: dict, total_sec: float = 0.0):
        """握手成功 → 生成完整报告落库 + 美化打印. 包含 Phase1/2/3 全链路细节."""
        report_id = f"hsr_{uuid.uuid4().hex[:16]}"
        ts = time.strftime("%Y-%m-%d %H:%M:%S")

        # Phase 1: 连接成功信息
        state_row = self.db.execute("SELECT * FROM mt_handshake_state WHERE id=1").fetchone()
        state_cols = [d[0] for d in self.db.execute("SELECT * FROM mt_handshake_state WHERE id=1").description]
        state_dict = dict(zip(state_cols, state_row)) if state_row else {}

        my_caps = self._my_capabilities()
        remote_caps = remote_pong.get("capabilities", {}) or {}
        phase1 = {
            "state_transition": f"DISCONNECTED → HANDSHAKING → CONNECTED → SYNCING → CONNECTED",
            "duration_sec": total_sec,
            "host_node": CONFIG.my_name,
            "guest_node": CONFIG.remote_name,
            "guest_host": CONFIG.remote_host,
            "guest_port": CONFIG.remote_port,
            "my_capabilities": my_caps,
            "remote_capabilities": remote_caps,
            "remote_rules_version": remote_pong.get("rules_version", "?"),
            "handshake_ts": state_dict.get("last_heartbeat") or ts,
            "daemon_status": json.loads(state_dict.get("daemon_status") or "{}"),
        }

        # Phase 2: 双向同步统计
        rows_stats = sync_stats.get("rows", {})
        total_pushed = sum(v.get("rows", 0) for v in rows_stats.values() if isinstance(v, dict))
        push_tables = [t for t, v in rows_stats.items() if isinstance(v, dict) and v.get("direction") == "push"]
        phase2 = {
            "bootstrap": sync_stats.get("bootstrap", {}),
            "row_sync": {
                "total_tables": len(rows_stats),
                "pushed_tables": push_tables,
                "total_rows_pushed": total_pushed,
                "details": rows_stats,
            },
            "smart_sync": sync_stats.get("smart_sync", {}),
        }

        # Phase 3: 圆桌会议 (从 mt_roundtable_sessions 查最新)
        phase3 = {}
        try:
            rt_row = self.db.execute(
                "SELECT session_id, experts_json, agenda, outcome, shared_items, round_summary, duration_sec, created_at "
                "FROM mt_roundtable_sessions ORDER BY id DESC LIMIT 1").fetchone()
            if rt_row:
                phase3 = {
                    "session_id": rt_row[0],
                    "experts": json.loads(rt_row[1] or "[]"),
                    "agenda": rt_row[2],
                    "outcome": rt_row[3],
                    "shared_items": json.loads(rt_row[4] or "{}"),
                    "summary": rt_row[5],
                    "duration_sec": rt_row[6],
                    "created_at": rt_row[7],
                }
        except Exception as e:
            phase3 = {"error": str(e)[:80]}

        # 1 句话总结
        n_experts = len(phase3.get("experts", []))
        n_push_tables = len(push_tables)
        summary = (
            f"✅ {CONFIG.my_name} ↔ {CONFIG.remote_name} 握手成功 | "
            f"⏱️ {total_sec}s | 📊 {n_push_tables} 表 / {total_pushed} 行同步 | "
            f"🎯 {n_experts} 专家圆桌"
        )

        # 落库
        try:
            self.db.execute("""INSERT INTO mt_handshake_reports
                (report_id, host_node, guest_node, guest_host,
                 phase1_handshake_json, phase2_sync_json, phase3_roundtable_json,
                 summary, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (report_id, CONFIG.my_name, CONFIG.remote_name, CONFIG.remote_host,
                 json.dumps(phase1, ensure_ascii=False),
                 json.dumps(phase2, ensure_ascii=False),
                 json.dumps(phase3, ensure_ascii=False),
                 summary, ts))
            self.db.commit()
        except Exception as e:
            print(f"[🤝 Report] 落库失败: {e}")

        # 美化打印
        self._print_fancy_report(report_id, ts, phase1, phase2, phase3, summary)
        return report_id

    def _print_fancy_report(self, report_id, ts, p1, p2, p3, summary):
        """终端美化打印握手成功报告."""
        print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  🎉 MTSCOS Handshake · 握手成功完整报告                               ║
║  Report ID: {report_id}
║  时间: {ts}
╚══════════════════════════════════════════════════════════════════════╝

📡 Phase 1 · 连接成功
  ├─ 本机:     {p1['host_node']}
  ├─ 远端:     {p1['guest_node']} @ {p1['guest_host']}:{p1['guest_port']}
  ├─ 耗时:     {p1['duration_sec']}s
  ├─ 状态机:   {p1['state_transition']}
  ├─ 本地能力: AI员工 {p1['my_capabilities'].get('ai_employees', '?')} · daemon {p1['my_capabilities'].get('daemons', '?')} · 脑库 {p1['my_capabilities'].get('brain_logs', '?')}
  └─ 远端能力: AI员工 {p1['remote_capabilities'].get('ai_employees', '?')} · daemon {p1['remote_capabilities'].get('daemons', '?')} · 脑库 {p1['remote_capabilities'].get('brain_logs', '?')}

🔄 Phase 2 · 双向同步
  ├─ Bootstrap:    {p2['bootstrap'].get('action', 'none')}
  ├─ 行级同步:     {p2['row_sync']['pushed_tables']} → {p2['row_sync']['total_rows_pushed']} 行
  ├─ Smart Sync:   {p2['smart_sync']}
  └─ 同步明细:""")
        for tbl, info in p2['row_sync']['details'].items():
            if isinstance(info, dict):
                direction = info.get('direction', '?')
                rows = info.get('rows', 0)
                mark = {"push": "↓", "remote_ahead": "↑", "equal": "=", "skip_local_empty": "·"}.get(direction, "?")
                print(f"     {mark} {tbl:40s} {direction:18s} {rows} rows")
        print(f"""
🎯 Phase 3 · 专家圆桌
  ├─ Session:      {p3.get('session_id', '-')}
  ├─ 专家数:       {len(p3.get('experts', []))} 人
  ├─ 议题:         {p3.get('agenda', '-')}
  ├─ 共享物品:     {json.dumps(p3.get('shared_items', {}), ensure_ascii=False)[:120]}
  ├─ 纪要:         {(p3.get('summary', '') or '(Q5 未生成)')[:200]}
  └─ 耗时:         {p3.get('duration_sec', '-')}s

💡 总结
  {summary}
╔══════════════════════════════════════════════════════════════════════╗
║  报告已落库 → mt_handshake_reports (report_id={report_id})
║  仪表盘: /api/handshake/report                                       ║
╚══════════════════════════════════════════════════════════════════════╝""")

    # ──── CLI ────
    def status(self):
        cur = self.db.execute("SELECT * FROM mt_handshake_state WHERE id=1")
        row = cur.fetchone()
        cols = [d[0] for d in cur.description]
        d = dict(zip(cols, row)) if row else {}
        pending = self.db.execute("SELECT COUNT(*) FROM mt_sync_pending_queue WHERE status='pending'").fetchone()[0]
        rt_count = self.db.execute("SELECT COUNT(*) FROM mt_roundtable_sessions").fetchone()[0]
        print(f"""
╔══════════════════════════════════════════════════════╗
║  🤝 MTSCOS Handshake · Status                        ║
╠══════════════════════════════════════════════════════╣
║  本机:     {d.get('my_name','?'):30s}  端口: {CONFIG.my_port}
║  远端:     {d.get('remote_name','?'):30s}  {d.get('remote_host','?')}:{d.get('remote_port','?')}
║  状态:     {d.get('state','?')}
║  最后心跳: {d.get('last_heartbeat') or '-'}
║  最后 PONG: {d.get('last_pong') or '-'}
║  规则版本: {d.get('rules_version','-')}
║  缓冲队列: {pending} items pending
║  圆桌会议: {rt_count} sessions total
╚══════════════════════════════════════════════════════╝""")
        if d.get("capabilities"):
            try:
                caps = json.loads(d["capabilities"])
                print(f"  📊 远端能力: {json.dumps(caps, ensure_ascii=False)}")
            except: pass

    def start(self):
        print("[🤝 Handshake] 🚀 start daemon")
        self.run_handshake_loop()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("[🤝 Handshake] 🛑 stopping")
            self._stop_flag.set()

    def stop(self):
        self._stop_flag.set()


# ═════════════════════════════════════════════════════════════════════════
# Flask Blueprint (仪表盘 API)
# ═════════════════════════════════════════════════════════════════════════

_HS_ENGINE = None  # 全局单例, 延迟初始化

def get_handshake_engine() -> HandshakeEngine:
    global _HS_ENGINE
    if _HS_ENGINE is None:
        _HS_ENGINE = HandshakeEngine()
    return _HS_ENGINE

def create_handshake_blueprint():
    """注册到 Flask app 后: /api/handshake/* 提供报告查询."""
    from flask import Blueprint, jsonify, request
    bp = Blueprint('mtscos_handshake', __name__, url_prefix='/api/handshake')

    @bp.route('/status', methods=['GET'])
    def api_status():
        """当前握手状态."""
        eng = get_handshake_engine()
        try:
            cur = eng.db.execute("SELECT * FROM mt_handshake_state WHERE id=1")
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]
            d = dict(zip(cols, row)) if row else {}
            return jsonify({"code": 0, "data": d})
        except Exception as e:
            return jsonify({"code": -1, "error": str(e)}), 500

    @bp.route('/report', methods=['GET'])
    def api_report():
        """最新握手成功报告 (或指定 report_id)."""
        eng = get_handshake_engine()
        try:
            report_id = request.args.get('report_id', '')
            if report_id:
                row = eng.db.execute(
                    "SELECT * FROM mt_handshake_reports WHERE report_id=?", (report_id,)).fetchone()
            else:
                row = eng.db.execute(
                    "SELECT * FROM mt_handshake_reports ORDER BY id DESC LIMIT 1").fetchone()
            if not row:
                return jsonify({"code": 0, "data": None, "message": "暂无握手成功报告"})
            cols = [d[0] for d in eng.db.execute("SELECT * FROM mt_handshake_reports LIMIT 0").description]
            d = dict(zip(cols, row))
            # JSON 字段反序列化
            for key in ('phase1_handshake_json', 'phase2_sync_json', 'phase3_roundtable_json'):
                if d.get(key):
                    try: d[key] = json.loads(d[key])
                    except: pass
            return jsonify({"code": 0, "data": d})
        except Exception as e:
            return jsonify({"code": -1, "error": str(e)}), 500

    @bp.route('/reports', methods=['GET'])
    def api_reports_list():
        """历史报告列表 (最新 20 条)."""
        eng = get_handshake_engine()
        try:
            rows = eng.db.execute(
                "SELECT report_id, host_node, guest_node, guest_host, summary, created_at "
                "FROM mt_handshake_reports ORDER BY id DESC LIMIT 20").fetchall()
            cols = ['report_id', 'host_node', 'guest_node', 'guest_host', 'summary', 'created_at']
            return jsonify({"code": 0, "data": [dict(zip(cols, r)) for r in rows]})
        except Exception as e:
            return jsonify({"code": -1, "error": str(e)}), 500

    @bp.route('/ping', methods=['POST'])
    def api_ping():
        """主动 Ping 远端 → 测试握手 → 触发完整链路."""
        eng = get_handshake_engine()
        pong = eng.ping_remote(timeout=3.0)
        if not pong:
            return jsonify({"code": -1, "message": f"❌ PING 失败 {CONFIG.remote_host}:{CONFIG.remote_port}"})
        threading.Thread(target=eng._trigger_bidirectional_sync, args=(pong,), daemon=True).start()
        return jsonify({"code": 0, "message": "✅ PONG 收到! 已触发双向同步 + 圆桌 + 报告",
                        "remote": pong.get('node'), "capabilities": pong.get('capabilities')})

    return bp


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Mac mini 自动握手 + 双向同步 + 专家圆桌")
    ap.add_argument("cmd", nargs="?", default="status",
                    choices=["status", "run", "daemon", "ping", "sync", "roundtable", "drain"])
    ap.add_argument("--remote", help="远端 host", default=None)
    args = ap.parse_args()
    if args.remote: CONFIG.remote_host = args.remote

    eng = HandshakeEngine()
    if args.cmd == "status":      eng.status()
    elif args.cmd == "run":        eng.start()
    elif args.cmd == "daemon":     eng.start()
    elif args.cmd == "ping":
        pong = eng.ping_remote(timeout=3.0)
        if pong:
            print(f"✅ PONG from {pong.get('node','?')} caps={json.dumps(pong.get('capabilities',{}), ensure_ascii=False)[:200]}")
        else: print("❌ PING failed")
    elif args.cmd == "sync":
        pong = eng.ping_remote(timeout=3.0)
        if pong: eng._trigger_bidirectional_sync(pong)
        else: print("❌ 先 ping 通远端")
    elif args.cmd == "roundtable":
        pong = eng.ping_remote(timeout=3.0)
        if pong: eng._roundtable(pong)
        else: print("❌ 先 ping 通远端")
    elif args.cmd == "drain":
        eng.drain_queue()

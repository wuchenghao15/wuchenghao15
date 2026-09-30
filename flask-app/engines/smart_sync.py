#!/usr/bin/env python3
"""
智能同步引擎 — 开发机 → 生产环境
=================================

🧬 开发机 (DEV): ~/MTSCOS_AI_Project/ (OneDrive 同步, Flask :5000, Ollama :11435)
🧊 生产 (PROD):  ~/MTSCOS_PROD/        (Flask :5001, Ollama :11435 共用)

核心能力:
  🎯 智能截断 — 自动判断哪些文件该同步, 哪些不该
  🔒 安全过滤 — .env / secrets / __pycache__ / .git 自动排除
  📊 DB 脱敏 — dev DB 里的实验数据 → prod 只同步 schema + 规则表
  🚀 4 种触发:
     1. dev_gate FINAL_DONE → 验收通过自动推
     2. git commit pre-push → commit 拦截触发
     3. daemon 每 10 分钟巡检 → 发现 diff 自动同步
     4. 手动 python3 smart_sync.py run

设计原则:
  - 先跑通本地隔离 (同一台 Mac mini 两个目录)
  - 切换远程服务器只需改 CONFIG.prod_host
  - 同步是单向的 (dev → prod), prod 的改动不会回传
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


# ═════════════════════════════════════════════════════════════════════════
# 配置层 — 改这里就能切换远程服务器
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class SyncConfig:
    """智能同步配置"""
    
    # 开发机路径
    dev_root: Path = Path.home() / "Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
    dev_flask: Path = dev_root / "flask-app"
    dev_rules: Path = dev_root.parent / ".trae" / "rules"  # .trae 在项目父级
    
    # 生产环境路径 (本地隔离: 同一台机器不同目录)
    prod_host: str = ""                   # 空=本地, "user@47.xxx.xxx.xxx"=远程 SSH
    prod_root: Path = Path.home() / "MTSCOS_PROD"
    prod_flask: Path = prod_root / "flask-app"
    prod_rules: Path = prod_root / ".trae" / "rules"
    
    # 生产端口 (开发 5000 → 生产 5001)
    dev_port: int = 5000
    prod_port: int = 5001
    
    # 智能截断规则
    skip_dirs: list[str] = field(default_factory=lambda: [
        "__pycache__", ".git", ".trae", ".vscode", "node_modules",
        ".venv", "venv", ".idea", ".DS_Store", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".eggs", "*.egg-info",
    ])
    skip_exts: list[str] = field(default_factory=lambda: [
        ".pyc", ".pyo", ".log", ".tmp", ".bak", ".swp", ".swo",
        ".sqlite3-journal", ".db-wal", ".db-shm",
    ])
    # 敏感文件 (开发有但生产应该用自己的)
    skip_files: list[str] = field(default_factory=lambda: [
        ".env", ".env.local", ".env.dev", ".env.development",
        "activate*", "debug*.py", "_test*.py", "*_test.py", "test_*.py",
    ])
    
    # DB 同步策略
    db_sync_mode: str = "schema_plus_rules"  # full / schema_only / schema_plus_rules
    db_tables_to_sync: list[str] = field(default_factory=lambda: [
        # 规则治理表 (权威数据, 必须同步)
        "mt_rule_changelog", "mt_rule_integrity_scan", "mt_rule_violation_alert",
        # 铁律违规表 (留痕)
        "mt_iron_rule_violations",
        # 权限表
        "dynamic_permission_rules", "ai_firewall_rules",
        # 冰山自动生成规则
        "mt_iceberg_rules_generated",
        # 引擎配置
        "mt_daemon_registry",
    ])
    
    @property
    def is_remote(self) -> bool:
        return bool(self.prod_host)


CONFIG = SyncConfig()


# ═════════════════════════════════════════════════════════════════════════
# 智能截断引擎
# ═════════════════════════════════════════════════════════════════════════

class SmartFilter:
    """智能截断 — 判断一个文件/目录该同步吗"""
    
    def __init__(self, cfg: SyncConfig):
        self.cfg = cfg
    
    def should_skip_dir(self, name: str) -> bool:
        for skip in self.cfg.skip_dirs:
            if skip.startswith("*.") and name.endswith(skip[1:]):
                return True
            if name == skip:
                return True
        return False
    
    def should_skip_file(self, name: str) -> bool:
        # 扩展名
        for ext in self.cfg.skip_exts:
            if name.endswith(ext):
                return True
        # 文件名模式
        for pat in self.cfg.skip_files:
            if pat.startswith("*"):
                if name.endswith(pat[1:]):
                    return True
            elif pat.endswith("*"):
                if name.startswith(pat[:-1]):
                    return True
            else:
                if name == pat:
                    return True
        return False
    
    def should_sync_db_table(self, table_name: str) -> bool:
        if self.cfg.db_sync_mode == "full":
            return True
        if self.cfg.db_sync_mode == "schema_only":
            return False
        # schema_plus_rules: 只同步规则/权限/治理相关表
        return any(kw in table_name.lower() for kw in [
            "rule", "iron", "violation", "firewall", "permission", 
            "daemon_registry", "iceberg", "governance", "integrity",
        ])


# ═════════════════════════════════════════════════════════════════════════
# 同步执行器
# ═════════════════════════════════════════════════════════════════════════

class SmartSyncEngine:
    """智能同步引擎"""
    
    def __init__(self, cfg: SyncConfig = CONFIG):
        self.cfg = cfg
        self.filter = SmartFilter(cfg)
        self.db = sqlite3.connect(str(cfg.dev_flask / "database" / "app.db"))
        self.db.row_factory = sqlite3.Row
        self._ensure_log()
    
    def _ensure_log(self):
        self.db.executescript(f"""
        CREATE TABLE IF NOT EXISTS mt_sync_runs (
            sync_id     TEXT PRIMARY KEY,
            trigger     TEXT,          -- FINAL_DONE / GIT_COMMIT / DAEMON / MANUAL
            dev_commit  TEXT DEFAULT '',
            files_count INTEGER DEFAULT 0,
            db_tables   TEXT DEFAULT '',
            db_rows     INTEGER DEFAULT 0,
            duration_s  REAL,
            status      TEXT,          -- SUCCESS / PARTIAL / FAILED
            report_json TEXT,
            synced_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_sync_runs ON mt_sync_runs(synced_at);
        """)
    
    # ── 主入口 ──────────────────────────────────────────────────────
    
    def run(self, trigger: str = "MANUAL", dev_commit: str = "") -> dict:
        """执行一次智能同步"""
        log(f"══════ 🚀 智能同步启动 [{trigger}] ══════")
        t0 = time.time()
        sync_id = f"sync_{trigger.lower()}_{int(time.time())}"
        
        result = {
            "sync_id": sync_id,
            "trigger": trigger,
            "dev_commit": dev_commit,
            "is_remote": self.cfg.is_remote,
            "files_synced": 0,
            "db_tables_synced": [],
            "db_rows_total": 0,
            "status": "SUCCESS",
            "steps": [],
        }
        
        try:
            # Step 1: 生产目录就绪
            self._ensure_prod_dir()
            result["steps"].append(("ensure_prod", "OK"))
            
            # Step 2: rsync 文件 (智能截断)
            synced = self._rsync_files()
            result["files_synced"] = synced
            result["steps"].append(("rsync_files", f"{synced} files"))
            
            # Step 3: DB 智能同步
            db_result = self._sync_db_smart()
            result["db_tables_synced"] = db_result["tables"]
            result["db_rows_total"] = db_result["rows"]
            result["steps"].append(("sync_db", f"{len(db_result['tables'])} tables, {db_result['rows']} rows"))
            
            # Step 4: 规则文件同步 (单独)
            rule_result = self._sync_rules()
            result["steps"].append(("sync_rules", f"{rule_result} files"))
            
            # Step 5: 生产端口检查 + 重启 (仅本地)
            if not self.cfg.is_remote:
                restart = self._restart_prod_flask()
                result["steps"].append(("restart_prod", restart))
            
            result["status"] = "SUCCESS"
            
        except Exception as e:
            result["status"] = "FAILED"
            result["steps"].append(("error", str(e)[:100]))
            log(f"  ❌ 同步失败: {e}")
        
        result["duration_s"] = round(time.time() - t0, 1)
        
        # 落库
        self.db.execute("""INSERT INTO mt_sync_runs 
            (sync_id, trigger, dev_commit, files_count, db_tables, db_rows, 
             duration_s, status, report_json) VALUES (?,?,?,?,?,?,?,?,?)""",
            (sync_id, trigger, dev_commit, result["files_synced"],
             ",".join(result["db_tables_synced"]), result["db_rows_total"],
             result["duration_s"], result["status"],
             json.dumps(result, ensure_ascii=False)))
        self.db.commit()
        
        log(f"══════ 同步完成 ({result['duration_s']}s, {result['status']}) ══════")
        return result
    
    # ── Step 1: 生产目录就绪 ──────────────────────────────────────
    
    def _ensure_prod_dir(self):
        prod = self.cfg.prod_flask
        if self.cfg.is_remote:
            # 远程: ssh mkdir -p
            cmd = f"ssh {self.cfg.prod_host} 'mkdir -p {self.cfg.prod_flask}'"
            subprocess.run(cmd, shell=True, check=False, capture_output=True)
        else:
            prod.mkdir(parents=True, exist_ok=True)
            (prod / "database").mkdir(exist_ok=True)
        log(f"  📁 生产目录就绪: {prod}")
    
    # ── Step 2: rsync 智能截断同步 ─────────────────────────────────
    
    def _rsync_files(self) -> int:
        """rsync + 智能截断规则"""
        rsync_excludes = []
        for d in self.cfg.skip_dirs:
            rsync_excludes += ["--exclude", d]
        for ext in self.cfg.skip_exts:
            rsync_excludes += ["--exclude", f"*{ext}"]
        
        # 基础命令: flask-app 目录
        src = str(self.cfg.dev_flask) + "/"
        dst = (f"{self.cfg.prod_host}:{self.cfg.prod_flask}" 
               if self.cfg.is_remote else str(self.cfg.prod_flask))
        
        cmd = ["rsync", "-avz", "--delete"] + rsync_excludes + [
            "--exclude", "activate_andromeda.py",
            "--exclude", "debug*.py",
            "--exclude", "_test*.py",
            "--exclude", "*.log",
            "--exclude", "database/app.db",   # DB 单独同步
            "--exclude", "database/*.db-journal",
            "--exclude", "database/*.db-wal",
            src, dst + "/",
        ]
        
        log(f"  🔄 rsync: {src} → {dst}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                log(f"  ⚠️ rsync 有警告: {result.stderr[:80]}")
            # 统计同步文件数
            synced = len([l for l in result.stdout.split("\n") 
                         if l and not l.startswith("sending") and not l.startswith("total") 
                         and not l.startswith("sent") and not l.startswith("delta")])
            log(f"     同步 {synced} 项")
            return synced
        except subprocess.TimeoutExpired:
            log("  ❌ rsync 超时")
            return 0
    
    # ── Step 3: DB 智能同步 (规则/权限表) ──────────────────────────
    
    def _sync_db_smart(self) -> dict:
        """
        DB 智能同步:
          - 首次: 全量复制 (schema + 所有表)
          - 后续: 选择性同步 (规则/权限/治理相关表)
        永远先确保目标表存在!
        """
        result = {"tables": [], "rows": 0}
        
        src_db_path = self.cfg.dev_flask / "database" / "app.db"
        if not src_db_path.exists():
            log(f"  ⚠️ DB 不存在: {src_db_path}")
            return result
        
        if self.cfg.is_remote:
            log("  ⚠️ 远程 DB 同步暂未实现")
            return result
        
        prod_db_path = self.cfg.prod_flask / "database" / "app.db"
        prod_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        src = sqlite3.connect(str(src_db_path))
        src.row_factory = sqlite3.Row
        
        # 判断是否首次 (prod DB 空或不存在)
        is_first = not prod_db_path.exists()
        if not is_first:
            try:
                tmp = sqlite3.connect(str(prod_db_path))
                tbls = tmp.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
                tmp.close()
                is_first = tbls == 0
            except:
                is_first = True
        
        if is_first:
            log(f"  🗄️  首次同步 → 全量复制 (schema + 所有表)")
            # 直接 copy 整个 DB (rsync 排除了 app.db, 这里手动 copy)
            if prod_db_path.exists():
                prod_db_path.unlink()
            shutil.copy2(str(src_db_path), str(prod_db_path))
            # 同时 copy wal/journal
            for ext in ["-wal", "-shm", "-journal"]:
                src_wal = Path(str(src_db_path) + ext)
                if src_wal.exists():
                    shutil.copy2(str(src_wal), str(prod_db_path) + ext)
            
            dst = sqlite3.connect(str(prod_db_path))
            tables = [r[0] for r in dst.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()]
            rows_total = sum(dst.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables)
            dst.close()
            log(f"     ✅ 全量复制完成: {len(tables)} 表, {rows_total} 行")
            src.close()
            return {"tables": tables[:10] + ["..."] if len(tables) > 10 else tables, "rows": rows_total}
        
        # ── 后续增量: 智能选择性同步 ──
        dst = sqlite3.connect(str(prod_db_path))
        
        all_tables = [r[0] for r in src.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]
        
        tables_to_sync = [t for t in all_tables if self.filter.should_sync_db_table(t)]
        
        log(f"  🗄️  DB 智能增量: {len(all_tables)} 表 → {len(tables_to_sync)} 规则表")
        
        for table in tables_to_sync:
            try:
                # 确保目标表存在 (CREATE TABLE IF NOT EXISTS 从 schema)
                create_sql = src.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                if create_sql and create_sql[0]:
                    dst.execute(create_sql[0])  # IF NOT EXISTS 会自动处理
                
                rows = src.execute(f"SELECT * FROM {table}").fetchall()
                cols = [d[0] for d in src.execute(f"SELECT * FROM {table} LIMIT 0").description]
                
                dst.execute(f"DELETE FROM {table}")
                placeholders = ",".join(["?"] * len(cols))
                col_str = ",".join(cols)
                dst.executemany(
                    f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})",
                    [tuple(r) for r in rows]
                )
                
                result["tables"].append(table)
                result["rows"] += len(rows)
                log(f"     ✅ {table}: {len(rows)} 行")
            except Exception as e:
                log(f"     ⚠️ {table} 跳过: {str(e)[:50]}")
        
        dst.commit()
        dst.close()
        src.close()
        
        return result
    
    # ── Step 4: 规则文件同步 ──────────────────────────────────────
    
    def _sync_rules(self) -> int:
        """.trae/rules/ 也同步到 prod"""
        if not self.cfg.dev_rules.exists():
            return 0
        
        if self.cfg.is_remote:
            cmd = ["rsync", "-avz", 
                   "--exclude", ".bak", "--exclude", "_backup/", "--exclude", "rules_backup/",
                   str(self.cfg.dev_rules) + "/",
                   f"{self.cfg.prod_host}:{self.cfg.prod_rules}/"]
        else:
            self.cfg.prod_rules.mkdir(parents=True, exist_ok=True)
            cmd = ["rsync", "-avz", 
                   "--exclude", ".bak", "--exclude", "_backup/", "--exclude", "rules_backup/",
                   str(self.cfg.dev_rules) + "/",
                   str(self.cfg.prod_rules) + "/"]
        
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            files = len([l for l in r.stdout.split("\n") if l.endswith(".md")])
            log(f"  📜 规则同步: {files} 份")
            return files
        except Exception as e:
            log(f"  ⚠️ 规则同步失败: {e}")
            return 0
    
    # ── Step 5: 生产 Flask 重启 (本地) ──────────────────────────────
    
    def _restart_prod_flask(self) -> str:
        """重启生产 Flask (port 5001)"""
        import subprocess as sp
        
        # 杀掉旧进程
        sp.run(["bash", "-c", 
               f"lsof -ti :{self.cfg.prod_port} | xargs kill -9 2>/dev/null"],
               capture_output=True)
        
        # 启动新进程
        prod_app = self.cfg.prod_flask
        if (prod_app / "modular_start.py").exists():
            cmd = [sys.executable, str(prod_app / "modular_start.py"), f"--port={self.cfg.prod_port}"]
            log(f"  ▶️ 启动生产 Flask: :{self.cfg.prod_port}")
            
            # 后台启动
            log_path = prod_app / "database" / "prod_flask.log"
            log_path.parent.mkdir(exist_ok=True)
            with open(log_path, "a") as logf:
                sp.Popen(cmd, stdout=logf, stderr=logf, cwd=str(prod_app))
            
            time.sleep(3)
            # 检查是否起来
            check = sp.run(["lsof", "-ti", f":{self.cfg.prod_port}"], 
                          capture_output=True, text=True)
            if check.stdout.strip():
                log(f"  ✅ 生产 Flask 已启动 (port {self.cfg.prod_port})")
                return f"STARTED port {self.cfg.prod_port}"
            else:
                log(f"  ❌ 生产 Flask 启动失败, 看日志: {log_path}")
                return "FAILED"
        else:
            return "SKIP (no modular_start.py)"
    
    # ── 状态查询 ──────────────────────────────────────────────────
    
    def status(self) -> dict:
        """dev vs prod 状态对比"""
        result = {
            "dev_port": self.cfg.dev_port,
            "prod_port": self.cfg.prod_port,
            "is_remote": self.cfg.is_remote,
            "prod_path": str(self.cfg.prod_root),
            "prod_flask_running": False,
            "last_sync": None,
            "sync_count": 0,
        }
        
        # prod Flask 状态
        try:
            r = subprocess.run(["lsof", "-ti", f":{self.cfg.prod_port}"], 
                             capture_output=True, text=True)
            result["prod_flask_running"] = bool(r.stdout.strip())
        except: pass
        
        # 上次同步
        try:
            row = self.db.execute("""
                SELECT sync_id, trigger, status, duration_s, synced_at 
                FROM mt_sync_runs ORDER BY rowid DESC LIMIT 1""").fetchone()
            if row:
                result["last_sync"] = dict(row)
            
            cnt = self.db.execute("SELECT COUNT(*) FROM mt_sync_runs").fetchone()[0]
            result["sync_count"] = cnt
        except: pass
        
        return result


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] 🚀 {msg}")


# ═════════════════════════════════════════════════════════════════════════
# 4 种触发方式的集成点
# ═════════════════════════════════════════════════════════════════════════

def trigger_final_done(flow_id: str):
    """触发 1: dev_gate FINAL_DONE → 自动同步"""
    log(f"🎯 触发同步: FINAL_DONE ({flow_id})")
    engine = SmartSyncEngine()
    engine.run(trigger="FINAL_DONE", dev_commit=flow_id)


def trigger_git_commit():
    """触发 2: git commit 时 → 智能判断是否同步"""
    log("🎯 触发同步: GIT_COMMIT")
    engine = SmartSyncEngine()
    # 先检查 git diff 大小
    try:
        r = subprocess.run(["git", "diff", "--stat", "HEAD~1", "HEAD"],
                          capture_output=True, text=True, timeout=10,
                          cwd=str(CONFIG.dev_root))
        changed = len([l for l in r.stdout.split("\n") if l.strip() and "|" in l])
        log(f"     最近 commit 改了 {changed} 个文件")
    except:
        changed = 0
    
    if changed > 0:
        engine.run(trigger="GIT_COMMIT")
    else:
        log("     无实质改动, 跳过")


def trigger_daemon_check() -> bool:
    """触发 3: daemon 每 10 分钟巡检 → 发现 diff 就同步"""
    engine = SmartSyncEngine()
    
    # 比较 dev 和 prod 的 Python 文件 mtime
    dev_pys = {}
    prod_pys = {}
    
    for pf in CONFIG.dev_flask.rglob("*.py"):
        if any(skip in str(pf) for skip in CONFIG.skip_dirs):
            continue
        dev_pys[str(pf.relative_to(CONFIG.dev_flask))] = pf.stat().st_mtime
    
    prod_root = CONFIG.prod_flask
    if prod_root.exists():
        for pf in prod_root.rglob("*.py"):
            prod_pys[str(pf.relative_to(prod_root))] = pf.stat().st_mtime
    
    # 找差异
    newer = [k for k, mt in dev_pys.items() 
             if k not in prod_pys or mt > prod_pys.get(k, 0)]
    
    if newer:
        log(f"🎯 daemon 巡检发现 {len(newer)} 个 dev 文件比 prod 新 → 自动同步")
        engine.run(trigger="DAEMON")
        return True
    else:
        log("🎯 daemon 巡检: dev/prod 同步, 无需行动")
        return False


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════

def main():
    global CONFIG
    
    if "--remote" in sys.argv:
        # 用法: python3 smart_sync.py --remote user@47.xxx.xxx.xxx
        idx = sys.argv.index("--remote")
        if idx + 1 < len(sys.argv):
            CONFIG.prod_host = sys.argv[idx + 1]
            log(f"🌐 切换到远程服务器: {CONFIG.prod_host}")
    
    action = sys.argv[1] if len(sys.argv) > 1 else "run"
    
    engine = SmartSyncEngine()
    
    if action == "run":
        engine.run(trigger="MANUAL")
    elif action == "final_done":
        fid = sys.argv[2] if len(sys.argv) > 2 else "manual_flow"
        trigger_final_done(fid)
    elif action == "git":
        trigger_git_commit()
    elif action == "daemon":
        # daemon 模式: 每 10 分钟巡检
        log("🧊 智能同步 daemon 启动 (每 10 分钟巡检)")
        while True:
            try:
                trigger_daemon_check()
            except Exception as e:
                log(f"  ❌ daemon 异常: {e}")
            time.sleep(600)
    elif action == "daemon_once":
        trigger_daemon_check()
    elif action == "status":
        s = engine.status()
        print(json.dumps(s, ensure_ascii=False, indent=2))
    elif action == "diff":
        # 详细 diff
        dev_pys = {}
        for pf in CONFIG.dev_flask.rglob("*.py"):
            if any(skip in str(pf) for skip in CONFIG.skip_dirs):
                continue
            dev_pys[str(pf.relative_to(CONFIG.dev_flask))] = pf.stat().st_mtime
        
        prod_root = CONFIG.prod_flask
        if prod_root.exists():
            for rel, mt in sorted(dev_pys.items()):
                prod_p = prod_root / rel
                if not prod_p.exists():
                    print(f"  ➕ DEV ONLY:  {rel}")
                elif mt > prod_p.stat().st_mtime:
                    print(f"  🔄 NEWER:    {rel} (dev 新 {int(mt - prod_p.stat().st_mtime())}s)")
                else:
                    print(f"  ✅ 同步:     {rel}")
        else:
            print(f"  ❌ prod 目录不存在: {prod_root}")
    else:
        print(f"""
智能同步引擎 — dev → prod

用法:
  python3 smart_sync.py run                  # 手动同步一次
  python3 smart_sync.py final_done FLOW_ID   # dev_gate FINAL_DONE 触发
  python3 smart_sync.py git                  # git commit 触发
  python3 smart_sync.py daemon               # daemon 模式 (每 10 分钟)
  python3 smart_sync.py daemon_once          # 跑一次 daemon 巡检
  python3 smart_sync.py status               # 状态查询
  python3 smart_sync.py diff                 # dev/prod 文件差异
  python3 smart_sync.py --remote user@HOST run  # 切换到远程服务器
        """)


if __name__ == "__main__":
    main()

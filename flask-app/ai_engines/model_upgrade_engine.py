#!/usr/bin/env python3
"""
§四.5 大模型自动升级体系 — engine
====================================
对接 Ollama API 做：版本检测 → 自动评测 → 升级 → 回滚
flow_id: flow_model_upgrade_engine_20260914
"""
from __future__ import annotations
import json, os, sqlite3, time, hashlib, threading, urllib.request, urllib.error, logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("ModelUpgradeEngine")

# ===== 配置 =====
# 🆕 2026-09-17: 统一端口 11435 (launch agent 管理的原生 Ollama)
_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11435")
_DB_PATH = None
for _p in [os.path.expanduser("~/mtscos/_runtime/databases/Database/app.db"),
           os.path.join(os.path.dirname(__file__), "..", "_runtime", "databases", "Database", "app.db")]:
    if os.path.exists(_p) and os.path.getsize(_p) > 1_000_000:
        _DB_PATH = _p; break

# ===== 评测题集（用于自动对比新旧版本）=====
_EVAL_PROMPTS = [
    ("推理-简单", "1+1等于几？只回答数字"),
    ("推理-复杂", "如果x=3，y=x²+2x+1，求y的值"),
    ("写作", "用一句话描述秋天"),
    ("代码", "写一行Python把列表反转"),
    ("翻译", "Translate 'Hello World' to Chinese"),
]

class ModelUpgradeEngine:
    """§四.5 大模型自动升级引擎"""
    
    _instance = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initd', False): return
        self._initd = True
        self._lock = threading.RLock()
        self._db = None
        self._ollama_host = _OLLAMA_HOST
        self._init_db()
    
    def _conn(self) -> sqlite3.Connection:
        if self._db is None or not _DB_PATH:
            self._db = sqlite3.connect(_DB_PATH) if _DB_PATH else None
        c = sqlite3.connect(_DB_PATH)
        c.execute("PRAGMA journal_mode=WAL")
        return c
    
    def _init_db(self):
        c = self._conn()
        c.executescript("""
CREATE TABLE IF NOT EXISTS mt_model_versions (
    version_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name       TEXT NOT NULL,        -- 如 qwen2.5
    ollama_tag       TEXT NOT NULL,        -- 如 qwen2.5:7b
    size_mb          REAL,
    version_hash     TEXT,                  -- 版本唯一标识
    is_current       INTEGER DEFAULT 0,     -- 是否当前在线
    status           TEXT DEFAULT 'available', -- available/testing/active/rollback/deprecated
    eval_score       REAL DEFAULT 0,        -- 自动评测分数 0-100
    eval_rounds      INTEGER DEFAULT 0,
    parent_version   TEXT,                  -- 来源版本
    rollback_to      TEXT,                  -- 可回滚到的版本
    notes            TEXT,
    deployed_at      TEXT,
    created_at       TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS mt_model_upgrade_log (
    log_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    action           TEXT NOT NULL,          -- detect/eval/activate/rollback/pull
    ollama_tag       TEXT NOT NULL,
    prev_tag         TEXT,
    result           TEXT,                   -- success/fail + detail
    eval_scores      TEXT,                   -- JSON
    duration_ms      INTEGER,
    triggered_by     TEXT DEFAULT 'auto',    -- auto/manual
    created_at       TEXT DEFAULT (datetime('now','localtime'))
);
        """)
        c.commit()
        c.close()
    
    # ============ Ollama 接口 ============
    
    def ollama_list(self) -> List[Dict]:
        """拉 Ollama 当前所有模型"""
        try:
            with urllib.request.urlopen(f"{self._ollama_host}/api/tags", timeout=5) as r:
                return json.loads(r.read()).get("models", [])
        except Exception as e:
            logger.error(f"Ollama /api/tags 失败: {e}")
            return []
    
    def ollama_pull(self, tag: str) -> bool:
        """拉取新模型"""
        try:
            req = urllib.request.Request(
                f"{self._ollama_host}/api/pull",
                data=json.dumps({"name": tag, "stream": False}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
                return data.get("status", "").lower() in ("success", "downloading")
        except Exception as e:
            logger.error(f"Ollama pull {tag} 失败: {e}")
            return False
    
    def ollama_generate(self, tag: str, prompt: str, timeout: int = 30) -> str:
        """调用 Ollama 推理"""
        try:
            req = urllib.request.Request(
                f"{self._ollama_host}/api/generate",
                data=json.dumps({"model": tag, "prompt": prompt, "stream": False}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read()).get("response", "")
        except Exception as e:
            logger.error(f"Ollama generate {tag} 失败: {e}")
            return ""
    
    # ============ 自动评测 ============
    
    def eval_model(self, ollama_tag: str, rounds: int = 3) -> Dict[str, Any]:
        """
        对一个模型做多轮基准评测，返回 0-100 分数
        评测维度：响应正确性、稳定性、延迟
        """
        results = {"tag": ollama_tag, "rounds": rounds, "prompts": [], "score": 0}
        total_score = 0
        
        for prompt_name, prompt_text in _EVAL_PROMPTS:
            prompt_scores = []
            for round_n in range(rounds):
                t0 = time.time()
                resp = self.ollama_generate(ollama_tag, prompt_text)
                latency_ms = (time.time() - t0) * 1000
                
                # 简单评分：有内容、延迟合理、非空
                round_score = 0
                if resp and len(resp.strip()) > 2: round_score += 40
                if latency_ms < 5000: round_score += 30
                elif latency_ms < 15000: round_score += 15
                if prompt_text[:10] in resp.lower(): round_score += 15
                round_score = min(round_score, 100)
                prompt_scores.append(round_score)
                
                results["prompts"].append({
                    "name": prompt_name, "round": round_n+1,
                    "latency_ms": round(latency_ms), "response_len": len(resp),
                    "score": round_score
                })
            
            prompt_avg = sum(prompt_scores) / len(prompt_scores)
            total_score += prompt_avg
        
        results["score"] = round(total_score / len(_EVAL_PROMPTS), 1)
        
        # 落库
        c = self._conn()
        c.execute("""INSERT INTO mt_model_upgrade_log
            (action, ollama_tag, result, eval_scores, duration_ms)
            VALUES (?,?,?,?,?)""",
            ("eval", ollama_tag, f"score={results['score']}", json.dumps(results["prompts"]), 0))
        # 更新 mt_model_versions
        ver_id = c.execute("SELECT version_id FROM mt_model_versions WHERE ollama_tag=?", 
                          (ollama_tag,)).fetchone()
        if ver_id:
            c.execute("UPDATE mt_model_versions SET eval_score=?, eval_rounds=eval_rounds+? WHERE version_id=?",
                     (results["score"], rounds, ver_id[0]))
        c.commit()
        c.close()
        
        logger.info(f"[eval] {ollama_tag} → score={results['score']}")
        return results
    
    # ============ 同步 Ollama 状态 ============
    
    def sync_ollama(self) -> Dict[str, Any]:
        """拉 Ollama 当前状态 → 落库 mt_model_versions"""
        models = self.ollama_list()
        c = self._conn()
        updated, new = 0, 0
        
        for m in models:
            tag = m.get("name", "")
            name = tag.split(":")[0]
            size_mb = round(m.get("size", 0) / 1024 / 1024, 1)
            tag_hash = hashlib.md5(tag.encode()).hexdigest()[:12]
            
            existing = c.execute("SELECT version_id FROM mt_model_versions WHERE ollama_tag=?", (tag,)).fetchone()
            if existing:
                c.execute("UPDATE mt_model_versions SET size_mb=?, version_hash=?, status='available', created_at=datetime('now','localtime') WHERE ollama_tag=?",
                         (size_mb, tag_hash, tag))
                updated += 1
            else:
                # 新模型 → 同时是当前版本（先假设，后面手动切换）
                c.execute("""INSERT INTO mt_model_versions
                    (model_name, ollama_tag, size_mb, version_hash, is_current, status)
                    VALUES (?,?,?,?,1,'active')""",
                    (name, tag, size_mb, tag_hash))
                new += 1
        
        # 记录 log
        c.execute("""INSERT INTO mt_model_upgrade_log
            (action, ollama_tag, result)
            VALUES ('sync', 'all', ?)""",
            (f"updated={updated}, new={new}, total={len(models)}",))
        c.commit()
        c.close()
        
        logger.info(f"[sync] updated={updated}, new={new}, ollama_total={len(models)}")
        return {"ollama_total": len(models), "synced_new": new, "synced_updated": updated}
    
    # ============ 切换当前版本 ============
    
    def activate(self, ollama_tag: str) -> Dict[str, Any]:
        """把某个模型设为当前版本"""
        c = self._conn()
        c.execute("UPDATE mt_model_versions SET is_current=0, status='deprecated' WHERE is_current=1")
        c.execute("UPDATE mt_model_versions SET is_current=1, status='active', deployed_at=datetime('now','localtime') WHERE ollama_tag=?",
                 (ollama_tag,))
        c.execute("""INSERT INTO mt_model_upgrade_log
            (action, ollama_tag, result)
            VALUES ('activate', ?, 'success')""", (ollama_tag,))
        c.commit()
        c.close()
        logger.info(f"[activate] → {ollama_tag}")
        return {"success": True, "active_tag": ollama_tag}
    
    def rollback(self, ollama_tag: str) -> Dict[str, Any]:
        """回滚（用 rollback_to 字段指定的版本）"""
        c = self._conn()
        row = c.execute("SELECT rollback_to FROM mt_model_versions WHERE ollama_tag=?", (ollama_tag,)).fetchone()
        target = row[0] if row else None
        if not target:
            c.close()
            return {"success": False, "error": "无回滚目标"}
        c.execute("UPDATE mt_model_versions SET is_current=0, status='rollback' WHERE is_current=1")
        c.execute("UPDATE mt_model_versions SET is_current=1, status='active' WHERE ollama_tag=?", (target,))
        c.execute("""INSERT INTO mt_model_upgrade_log
            (action, ollama_tag, prev_tag, result)
            VALUES ('rollback', ?, ?, 'success')""", (target, ollama_tag))
        c.commit()
        c.close()
        logger.info(f"[rollback] {ollama_tag} → {target}")
        return {"success": True, "rolled_back_to": target}
    
    def get_status(self) -> Dict[str, Any]:
        """全局状态"""
        c = self._conn()
        current = c.execute("SELECT ollama_tag, eval_score, size_mb FROM mt_model_versions WHERE is_current=1").fetchone()
        versions = c.execute("SELECT ollama_tag, is_current, status, eval_score, size_mb FROM mt_model_versions ORDER BY created_at DESC").fetchall()
        logs = c.execute("SELECT action, ollama_tag, result, created_at FROM mt_model_upgrade_log ORDER BY log_id DESC LIMIT 10").fetchall()
        c.close()
        
        ollama_models = self.ollama_list()
        return {
            "current": dict(zip(["ollama_tag","eval_score","size_mb"], current)) if current else None,
            "versions": [dict(zip(["ollama_tag","is_current","status","eval_score","size_mb"], v)) for v in versions],
            "upgrade_log": [dict(zip(["action","ollama_tag","result","created_at"], l)) for l in logs],
            "ollama_available": self._ollama_host,
            "ollama_models_count": len(ollama_models),
        }

# ===== 全局单例 =====
model_upgrade_engine = ModelUpgradeEngine()

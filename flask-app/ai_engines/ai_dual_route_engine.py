# -*- coding: utf-8 -*-
"""
双轨路由AI推理引擎
==================
本地 Ollama 优先（零token）+ 火山引擎云API兜底，按场景智能路由

路由策略：
1. 本地 Ollama 可用 → 本地推理（零token消耗）
2. 本地不可用 + 云API可用 → 火山引擎兜底（消耗token）
3. 两者都不可用 → 返回错误

场景路由：
- 简单任务（分类/审查）→ 本地 3B 模型
- 复杂任务（聊天/Bug分析）→ 本地 7B 模型
- 本地不可用 → 云API兜底

对接：ai_local_inference_engine.py 统一入口
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# 引擎路径
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DB = os.path.join(_AI_ENGINES_DIR, "app.db")

# 确保 ai_engines 目录在 sys.path 中（兼容不同调用方式）
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_APP_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_routing_table() -> None:
    """确保路由决策记录表存在"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_routing_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id TEXT,
            inference_kind TEXT,
            route_chosen TEXT,
            local_available INTEGER,
            cloud_available INTEGER,
            reason TEXT,
            duration_ms INTEGER,
            tokens_saved INTEGER,
            triggered_at TEXT
        )""")
    conn.commit()
    conn.close()


def _log_routing(flow_id: Optional[str], kind: str, route: str,
                local_ok: bool, cloud_ok: bool, reason: str,
                duration_ms: int, tokens_saved: int) -> None:
    """落库路由决策"""
    _ensure_routing_table()
    conn = _get_conn()
    conn.execute("""INSERT INTO mt_ai_routing_decisions
        (flow_id, inference_kind, route_chosen, local_available, cloud_available,
         reason, duration_ms, tokens_saved, triggered_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (flow_id, kind, route, 1 if local_ok else 0, 1 if cloud_ok else 0,
         reason, duration_ms, tokens_saved, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def route_and_chat(prompt: str, system: str = "", kind: str = "chat",
                   flow_id: Optional[str] = None,
                   prefer_local: bool = True) -> Dict[str, Any]:
    """
    双轨路由聊天
    1. prefer_local=True 且本地可用 → Ollama 本地推理（零token）
    2. 本地不可用 → 火山引擎云API兜底
    3. 两者不可用 → 错误

    返回 {success, response, model, route, duration_ms, tokens_saved, error}
    """
    import time
    start = time.time()

    # 检查本地 Ollama
    local_ok = False
    try:
        from ai_ollama_engine import is_available as ollama_available, chat as ollama_chat
        local_ok = ollama_available()
    except Exception:
        local_ok = False

    # 检查云API
    cloud_ok = False
    try:
        from ai_volcengine_engine import is_available as ark_available
        cloud_ok = ark_available()
    except Exception:
        cloud_ok = False

    # 路由决策
    route = "none"
    result: Dict[str, Any] = {
        "success": False, "response": "", "model": "", "route": "none",
        "duration_ms": 0, "tokens_saved": 0, "error": "所有推理引擎不可用"
    }

    if prefer_local and local_ok:
        # 本地优先
        route = "local_ollama"
        result = ollama_chat(prompt, system, flow_id, prefer_7b=(kind in ("chat", "review", "bug_analyze")))
        result["route"] = route
        _log_routing(flow_id, kind, route, True, cloud_ok,
                     "本地Ollama可用，优先本地推理（零token）",
                     int((time.time() - start) * 1000), result.get("tokens_saved", 0))

    elif cloud_ok:
        # 云API兜底
        route = "cloud_volcengine"
        from ai_volcengine_engine import chat as ark_chat
        result = ark_chat(prompt, system, flow_id)
        result["route"] = route
        _log_routing(flow_id, kind, route, local_ok, True,
                     "本地Ollama不可用，云API兜底（消耗token）",
                     int((time.time() - start) * 1000), 0)

    elif local_ok:
        # prefer_local=False 但云API不可用，仍用本地
        route = "local_ollama_fallback"
        result = ollama_chat(prompt, system, flow_id)
        result["route"] = route
        _log_routing(flow_id, kind, route, True, False,
                     "云API不可用，回退本地Ollama",
                     int((time.time() - start) * 1000), result.get("tokens_saved", 0))

    else:
        _log_routing(flow_id, kind, "none", False, False,
                     "本地和云API均不可用", int((time.time() - start) * 1000), 0)

    return result


def chat(prompt: str, system: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """双轨路由聊天（统一入口）"""
    return route_and_chat(prompt, system, "chat", flow_id, prefer_local=True)


def classify(text: str, categories: List[str], flow_id: Optional[str] = None) -> Dict[str, Any]:
    """双轨路由分类"""
    system = "你是分类器，只返回类别名称，不加其他文字。"
    prompt = f"将以下文本分类到 [{', '.join(categories)}] 中的一个：\n{text}\n类别："
    result = route_and_chat(prompt, system, "classify", flow_id, prefer_local=True)
    result["kind"] = "classify"
    return result


def review(code: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """双轨路由代码审查"""
    system = "你是代码审查专家，检查代码质量、安全、性能问题，给出改进建议。"
    prompt = f"审查以下代码：\n```\n{code}\n```\n给出问题和建议："
    result = route_and_chat(prompt, system, "review", flow_id, prefer_local=True)
    result["kind"] = "review"
    return result


def bug_analyze(error_desc: str, code: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """双轨路由Bug分析"""
    system = "你是Bug分析专家，定位根因并给出修复方案。"
    prompt = f"错误描述：{error_desc}\n相关代码：\n```\n{code}\n```\n根因分析和修复方案："
    result = route_and_chat(prompt, system, "bug_analyze", flow_id, prefer_local=True)
    result["kind"] = "bug_analyze"
    return result


def health() -> Dict[str, Any]:
    """双轨路由引擎健康状态"""
    local_ok = False
    cloud_ok = False
    local_models: List[str] = []
    try:
        from ai_ollama_engine import is_available, list_models, health as ollama_health
        local_ok = is_available()
        local_models = list_models()
    except Exception:
        pass
    try:
        from ai_volcengine_engine import is_available as ark_available
        cloud_ok = ark_available()
    except Exception:
        pass
    return {
        "engine": "ai_dual_route_engine",
        "route_strategy": "local_first_zero_token" if local_ok else "cloud_fallback",
        "local_ollama_available": local_ok,
        "cloud_volcengine_available": cloud_ok,
        "local_models": local_models,
        "hw_profile": {
            "chip": "Apple M5",
            "memory_gb": 24,
            "primary_model": "qwen2.5:7b",
            "fallback_model": "qwen2.5:3b",
        },
    }

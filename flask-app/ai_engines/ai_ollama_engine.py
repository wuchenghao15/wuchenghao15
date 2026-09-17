# -*- coding: utf-8 -*-
"""
Ollama 本地推理引擎
====================
适配 MTSCOS AI 项目 ai_local_inference_engine 统一入口
机型适配：Apple M5 / 24GB RAM / 10核 (4P+6E)
主力模型：gpt-oss:20b（Ollama Cloud, 经本地 Cloud Proxy 11434 转发 api.ollama.com）
兜底模型：gpt-oss:20b（同上; Cloud 已下架 qwen2.5:7b 等本地旧模型）
新增特性：多AI引擎聚合调度，支持将系统内其他AI集/AI引擎注册接入Ollama体系
职责：
- 调用 Ollama Cloud Proxy (http://localhost:11434 → api.ollama.com) 云端推理
- 本引擎为「Ollama 云端优先」路径; 本地原生兜底(qwen2.5:7b @ 11435)由网关 _native_ollama_chat 处理
- 落库 mt_local_ai_inference_log + mt_local_ai_token_savings
- 支持 chat / classify / review / bug_analyze 四类推理
- 新增功能：翻译
- 多引擎融合：自动调度已注册的其他外部AI引擎作为Ollama的降级/互补方案

依赖：
- Ollama 服务已安装并运行 (ollama serve)
- 已下载 qwen2.5:7b 或 qwen2.5:3b 模型
- 外部其他AI引擎模块可通过 register_ai_engine 接口注册接入
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Ollama 本地推理引擎 — 自动探测端口
# 优先级: env OLLAMA_HOST (验证后才用) > 自动探测 (11435 原生优先, 11434 proxy 兜底)
def _host_ok(host: str) -> bool:
    """验证 host 是否真的是 Ollama (TCP connect + /api/tags 返回 models)"""
    import socket as _sk, urllib.request as _ur, json as _json
    try:
        _url = host.rstrip("/") + "/api/tags"
        with _ur.urlopen(_url, timeout=2) as _r:
            _data = _json.loads(_r.read())
            return "models" in _data
    except Exception:
        return False

def _detect_ollama_host() -> str:
    # 1) 如果 env 指定了，验证它可用才用，否则 fallback 到自动探测
    explicit = os.environ.get("OLLAMA_HOST", "").strip().rstrip("/")
    if explicit and _host_ok(explicit):
        print(f"[ollama] env OLLAMA_HOST={explicit} verified OK")
        return explicit

    # 2) 自动探测 (优先原生 ollama serve, 再 proxy)
    for _port in (11435, 11434):
        _candidate = f"http://localhost:{_port}"
        if _host_ok(_candidate):
            print(f"[ollama] auto-detected on port {_port}")
            return _candidate

    # 3) fallback — 两个都不通时还是用 11435 (原生 serve 端口)
    print(f"[ollama] WARNING: no Ollama reachable, defaulting to 11435")
    return "http://localhost:11435"

_OLLAMA_HOST = _detect_ollama_host()
_OLLAMA_API = _OLLAMA_HOST + "/api"

# 外部AI引擎注册表：将系统其他AI集/AI引擎注册到Ollama体系下统一调度
_AI_ENGINE_REGISTRY: Dict[str, Dict[str, Any]] = {}

# 机型适配（Apple M5 / 24GB）
_HW_PROFILE = {
    "chip": "Apple M5",
    "cores": 10,
    "memory_gb": 24,
    # 🆕 2026-09-17: 从 gpt-oss:20b (Ollama Cloud Proxy, 本机无) 改为本地真实存在的模型
    "primary_model": "qwen2.5:14b",       # 主力: 14B, 本地 Metal iGPU 推理
    "fallback_model": "qwen2.5:7b",       # 兜底: 7B, 响应更快
    "coding_model": "qwen2.5-coder:14b",   # 代码专用: coder 模型
    "expected_tok_s_7b": 40,   # 7B 预估 30-50 tok/s
    "expected_tok_s_3b": 70,   # 3B 预估 60-80 tok/s
}

# 数据库路径
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DB = os.path.join(_AI_ENGINES_DIR, "app.db")


def register_ai_engine(engine_name: str, call_func: Callable, check_available: Callable, priority: int = 10) -> None:
    """
    注册外部其他AI引擎到Ollama聚合体系，实现多AI集融合
    :param engine_name: 自定义引擎唯一标识
    :param call_func: 引擎推理调用函数，参数格式兼容 (prompt: str, system: str = "")
    :param check_available: 引擎可用性检查函数，返回bool
    :param priority: 调度优先级，数值越小优先级越高，Ollama原生默认优先级为0
    """
    _AI_ENGINE_REGISTRY[engine_name] = {
        "call": call_func,
        "check": check_available,
        "priority": priority,
        "name": engine_name
    }


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_APP_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables() -> None:
    """确保 mt_local_ai_inference_log + mt_local_ai_token_savings 表存在"""
    conn = _get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS mt_local_ai_inference_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id TEXT,
        inference_kind TEXT NOT NULL,
        model_name TEXT NOT NULL,
        prompt_tokens INTEGER DEFAULT 0,
        completion_tokens INTEGER DEFAULT 0,
        duration_ms INTEGER DEFAULT 0,
        tokens_saved INTEGER DEFAULT 0,
        success INTEGER DEFAULT 0,
        error_msg TEXT,
        request_preview TEXT,
        response_preview TEXT,
        triggered_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS mt_local_ai_token_savings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stat_date TEXT NOT NULL,
        total_inferences INTEGER DEFAULT 0,
        total_tokens_saved INTEGER DEFAULT 0,
        total_duration_ms INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()


def is_available() -> bool:
    """检查Ollama服务或任意已注册的融合AI引擎是否可用"""
    # 优先检查原生Ollama
    try:
        req = urllib.request.Request(_OLLAMA_API + "/tags", method="GET", headers={"User-Agent": "curl/8.7.1"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
    # 检查所有注册的外部AI引擎
    for engine in _AI_ENGINE_REGISTRY.values():
        try:
            if engine["check"]():
                return True
        except Exception:
            continue
    return False


def list_models() -> List[str]:
    """列出Ollama本地模型 + 所有注册引擎提供的模型列表"""
    models = []
    # 先拉取Ollama本地模型
    try:
        req = urllib.request.Request(_OLLAMA_API + "/tags", method="GET", headers={"User-Agent": "curl/8.7.1"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models.extend([m["name"] for m in data.get("models", [])])
    except Exception:
        pass
    # 追加外部注册引擎的标识
    models.extend([f"[FUSION_ENGINE]{name}" for name in _AI_ENGINE_REGISTRY.keys()])
    return models


def health() -> Dict[str, Any]:
    """引擎健康状态 (只读, 供统一网关 health()/系统诊断调用)

    注意: 网关 _get_ollama() 通过 `from ai_ollama_engine import health` 依赖本符号;
    若缺失会触发 ImportError 并被静默降级为"整个本地引擎不可用"。
    """
    info: Dict[str, Any] = {"available": False, "host": _OLLAMA_HOST}
    try:
        # 原生 Ollama 探测
        native_ok = False
        try:
            req = urllib.request.Request(_OLLAMA_API + "/tags", method="GET", headers={"User-Agent": "curl/8.7.1"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                native_ok = resp.status == 200
        except Exception:
            native_ok = False
        info["ollama_native"] = native_ok
        info["fusion_engines"] = list(_AI_ENGINE_REGISTRY.keys())
        info["available"] = bool(native_ok or _AI_ENGINE_REGISTRY)
        if native_ok:
            models = [m for m in list_models() if not m.startswith("[FUSION_ENGINE]")]
            info["models"] = models
            info["model_count"] = len(models)
        info["primary_model"] = _HW_PROFILE["primary_model"]
        info["coding_model"] = _HW_PROFILE["coding_model"]
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
    return info


def _select_model(prefer_7b: bool = True, use_coder: bool = False) -> str:
    """根据已下载模型选择主力或兜底模型，无可用Ollama模型时返回融合引擎标识"""
    models = list_models()
    primary = _HW_PROFILE["primary_model"]
    fallback = _HW_PROFILE["fallback_model"]
    coding = _HW_PROFILE["coding_model"]
    # 编码任务优先使用编码专用模型
    if use_coder and coding in models:
        return coding
    if prefer_7b and primary in models:
        return primary
    if fallback in models:
        return fallback
    # 优先返回第一个可用融合引擎
    for engine_name in _AI_ENGINE_REGISTRY.keys():
        if f"[FUSION_ENGINE]{engine_name}" in models:
            return f"[FUSION_ENGINE]{engine_name}"
    # 兜底：返回第一个可用模型
    return models[0] if models else primary


def _dispatch_inference(model: str, prompt: str, system: str = "", stream: bool = False) -> Dict[str, Any]:
    """统一调度入口：优先调用Ollama原生，自动路由到已注册的融合AI引擎"""
    # 判断是否为融合引擎标识
    if model.startswith("[FUSION_ENGINE]"):
        engine_name = model.replace("[FUSION_ENGINE]", "")
        engine = _AI_ENGINE_REGISTRY.get(engine_name)
        if not engine:
            raise RuntimeError(f"融合AI引擎 {engine_name} 未注册")
        return engine["call"](prompt, system)
    # 原生Ollama调用
    return _call_ollama(model, prompt, system, stream)


def _call_ollama(model: str, prompt: str, system: str = "", stream: bool = False) -> Dict[str, Any]:
    """调用 Ollama /api/chat 接口"""
    payload = {
        "model": model,
        "messages": [],
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 2048,
        }
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})

    req = urllib.request.Request(
        _OLLAMA_API + "/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "curl/8.7.1"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _log_inference(flow_id: Optional[str], kind: str, model: str,
                   prompt_tokens: int, completion_tokens: int, duration_ms: int,
                   success: bool, error_msg: str, request_preview: str,
                   response_preview: str) -> None:
    """落库 mt_local_ai_inference_log + mt_local_ai_token_savings (失败不影响推理)"""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        saved = prompt_tokens + completion_tokens if success else 0
        cursor.execute(
            "INSERT INTO mt_local_ai_inference_log (flow_id, inference_kind, model_name, "
            "prompt_tokens, completion_tokens, duration_ms, tokens_saved, success, error_msg, "
            "request_preview, response_preview, triggered_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (flow_id, kind, model, prompt_tokens if success else 0,
             completion_tokens if success else 0, duration_ms, saved, success,
             error_msg, request_preview, response_preview if success else "", datetime.now()))
        conn.commit()
        conn.close()
    except Exception:
        pass  # 日志落库失败永不阻断推理主链路


def chat(prompt: str, system: str = "", flow_id: Optional[str] = None,
         prefer_7b: bool = True, use_coder: bool = False) -> Dict[str, Any]:
    """本地聊天推理 (经 _dispatch_inference 统一调度: 原生Ollama优先, 自动路由融合引擎)"""
    model = _select_model(prefer_7b, use_coder)
    start_time = time.time()
    try:
        result = _dispatch_inference(model, prompt, system)
        duration_ms = int((time.time() - start_time) * 1000)
        # 兼容原生Ollama响应(message.content)与融合引擎返回(response字段)
        response = (result.get("message") or {}).get("content", "") or result.get("response", "")
        prompt_tokens = result.get("prompt_eval_count", len(prompt) // 4)
        completion_tokens = result.get("eval_count", len(response) // 4)
        _log_inference(flow_id, "chat", model, prompt_tokens, completion_tokens,
                       duration_ms, True, "", prompt[:200], response[:200])
        return {
            "success": True,
            "response": response,
            "model": model,
            "duration_ms": duration_ms,
            "tokens_saved": prompt_tokens + completion_tokens,
            "error": "",
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        _log_inference(flow_id, "chat", model, 0, 0, duration_ms, False,
                       str(e), prompt[:200], "")
        return {"success": False, "response": "", "model": model, "error": str(e)}


def classify(text: str, categories: List[str], flow_id: Optional[str] = None) -> Dict[str, Any]:
    """本地分类推理 (轻量模型即可)"""
    system = "你是分类器，只返回类别名称，不加其他文字。"
    prompt = f"将以下文本分类到 [{', '.join(categories)}] 中的一个：\n{text}\n类别："
    result = chat(prompt, system, flow_id, prefer_7b=False)
    result["kind"] = "classify"
    return result


def review(code: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """本地代码审查"""
    system = "你是代码审查专家，检查代码质量、安全、性能问题，给出改进建议。"
    prompt = f"审查以下代码：\n```\n{code}\n```\n给出问题和建议："
    result = chat(prompt, system, flow_id)
    result["kind"] = "review"
    return result


def bug_analyze(error_desc: str, code: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """本地Bug根因分析"""
    system = "你是Bug分析专家，定位根因并给出修复方案。"
    prompt = f"错误描述：{error_desc}\n相关代码：\n```\n{code}\n```\n根因分析和修复方案："
    result = chat(prompt, system, flow_id)
    result["kind"] = "bug_analyze"
    return result


# 模块加载时确保落库表存在 (失败静默, 不影响推理)
try:
    _ensure_tables()
except Exception:
    pass

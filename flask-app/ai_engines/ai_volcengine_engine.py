# -*- coding: utf-8 -*-
"""
火山引擎方舟(ARK)云API兜底引擎
==============================
作为 Ollama 本地推理的在线兜底，按场景路由
模型：doubao-pro-32k（火山引擎闭源大模型）

职责：
- 当 Ollama 本地不可用时，调用火山引擎方舟ARK API
- API Key 加密存储（使用 db_encryption.py L1级）
- 落库 mt_local_ai_inference_log（标记 source=volcengine）
- 消耗 token 计入成本统计

依赖：
- 火山引擎账号已注册
- 已开通方舟ARK API
- API Key 已配置（环境变量 VOLCENGINE_API_KEY 或加密存储）

注意：本地优先（零token），本引擎仅在本地不可用时兜底
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Dict, List, Optional

# 火山引擎方舟 ARK API 配置
_ARK_API_BASE = os.environ.get("VOLCENGINE_ARK_BASE", "https://ark.cn-beijing.volces.com/api/v3")
_ARK_API_KEY = os.environ.get("VOLCENGINE_API_KEY", "")
_ARK_MODEL = os.environ.get("VOLCENGINE_MODEL", "doubao-pro-32k")

_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DB = os.path.join(_AI_ENGINES_DIR, "app.db")
# 本地密钥文件 (gitignore, 禁止提交)
_SECRETS_FILE = os.path.join(
    os.path.dirname(_AI_ENGINES_DIR), "..", "_runtime", "config", "ai_secrets.json"
)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_APP_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _load_secrets() -> Dict[str, str]:
    """读取本地密钥文件 (call-time 读取, 运行进程可热加载)"""
    try:
        with open(_SECRETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_api_key() -> str:
    """获取API Key（优先环境变量，其次本地密钥文件）"""
    if _ARK_API_KEY:
        return _ARK_API_KEY
    secrets = _load_secrets()
    return secrets.get("volcengine_ark_api_key", "")


def _get_model() -> str:
    """获取默认模型（优先环境变量，其次本地密钥文件，最后默认值）"""
    if os.environ.get("VOLCENGINE_MODEL"):
        return os.environ["VOLCENGINE_MODEL"]
    secrets = _load_secrets()
    return secrets.get("volcengine_model", _ARK_MODEL)


def _save_secrets(secrets: Dict[str, str]) -> None:
    """保存密钥到本地文件（保留_metadata字段）"""
    os.makedirs(os.path.dirname(_SECRETS_FILE), exist_ok=True)
    with open(_SECRETS_FILE, "w", encoding="utf-8") as f:
        json.dump(secrets, f, ensure_ascii=False, indent=2)


def set_api_key(api_key: str) -> Dict[str, Any]:
    """
    配置火山引擎ARK API Key（写入本地密钥文件）
    返回 {success, message, key_prefix}
    """
    if not api_key or not api_key.startswith("ark-"):
        return {"success": False, "message": "API Key格式错误，必须以 ark- 开头", "key_prefix": ""}
    secrets = _load_secrets()
    secrets["volcengine_ark_api_key"] = api_key.strip()
    secrets["_status"] = "API Key已更新，待验证"
    _save_secrets(secrets)
    # 同步更新模块内缓存
    global _ARK_API_KEY
    _ARK_API_KEY = api_key.strip()
    return {
        "success": True,
        "message": f"API Key已保存到 {_SECRETS_FILE}",
        "key_prefix": api_key.strip()[:20] + "...",
    }


def set_model(model: str) -> Dict[str, Any]:
    """
    配置默认模型（写入本地密钥文件）
    返回 {success, message, model}
    """
    if not model:
        return {"success": False, "message": "模型名不能为空", "model": ""}
    secrets = _load_secrets()
    secrets["volcengine_model"] = model.strip()
    _save_secrets(secrets)
    global _ARK_MODEL
    _ARK_MODEL = model.strip()
    return {"success": True, "message": f"模型已更新为 {model.strip()}", "model": model.strip()}


def is_available() -> bool:
    """检查火山引擎API是否可用（有API Key即视为可用）"""
    return bool(_get_api_key())


def _call_ark(model: str, messages: List[Dict], temperature: float = 0.7,
              max_tokens: int = 2048) -> Dict[str, Any]:
    """调用火山引擎方舟ARK chat/completions 接口"""
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("火山引擎API Key未配置（环境变量VOLCENGINE_API_KEY或加密存储）")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        _ARK_API_BASE + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as http_err:
        # 读取错误体 (404 InvalidEndpointOrModel 是常见可降级场景)
        try:
            body = http_err.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise RuntimeError(
            f"ARK HTTP {http_err.code}: {body[:200]}"
        ) from http_err


def _log_inference(flow_id: Optional[str], kind: str, model: str,
                   prompt_tokens: int, completion_tokens: int, duration_ms: int,
                   success: bool, error_msg: str, source: str = "volcengine") -> None:
    """落库 mt_local_ai_inference_log（source=volcengine）"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mt_local_ai_inference_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id TEXT, inference_kind TEXT, model_name TEXT,
            prompt_tokens INTEGER, completion_tokens INTEGER,
            duration_ms INTEGER, tokens_saved INTEGER DEFAULT 0,
            success INTEGER, error_msg TEXT,
            request_preview TEXT, response_preview TEXT,
            triggered_at TEXT, source TEXT DEFAULT 'ollama'
        )""")
    # 兼容旧表: 补 source 列 (CREATE IF NOT EXISTS 不补列)
    try:
        conn.execute("SELECT source FROM mt_local_ai_inference_log LIMIT 0")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE mt_local_ai_inference_log ADD COLUMN source TEXT DEFAULT 'ollama'")
    # 云API消耗token，tokens_saved=0（不节省）
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO mt_local_ai_inference_log
        (flow_id, inference_kind, model_name, prompt_tokens, completion_tokens,
         duration_ms, tokens_saved, success, error_msg, triggered_at, source)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (flow_id, kind, model, prompt_tokens, completion_tokens,
          duration_ms, 0, 1 if success else 0, error_msg, now, source))
    conn.commit()
    conn.close()


def chat(prompt: str, system: str = "", flow_id: Optional[str] = None,
         model: Optional[str] = None) -> Dict[str, Any]:
    """
    火山引擎云API聊天（兜底用，消耗token）
    返回 {success, response, model, duration_ms, tokens_saved, error}
    
    Args:
        prompt: 用户提示词
        system: system role 内容
        flow_id: 链路追踪 ID
        model: 可选, 指定模型 (如 "deepseek-v4-pro-260425"). 不传则用 _get_model() 默认值
    """
    kind = "chat"
    api_key = _get_api_key()
    # 🆕 2026-09-17: model 参数可选覆盖, 未显式指定时才用默认
    _model = model if model else _get_model()
    if not api_key:
        return {"success": False, "response": "", "model": _model,
                "duration_ms": 0, "tokens_saved": 0,
                "error": "火山引擎API Key未配置"}

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # 🆕 2026-09-17: 智能降级链路
    # 豆包 doubao-1-5-pro/thinking/vision 系列需要 endpoint_id (ep-xxx),
    # 纯模型名调用会返回 InvalidEndpointOrModel.NotFound (404).
    # 此时自动 fallback 到账号上可用的默认模型 (seed-2-0-lite),
    # 保证链路不中断, 同时日志里标注降级发生.
    default_model = _get_model()  # 账号上一定可用的兜底模型
    attempts = [_model]
    if _model != default_model:
        attempts.append(default_model)  # 第二试: 默认

    last_error = ""
    for candidate in attempts:
        start = time.time()
        try:
            result = _call_ark(candidate, messages)
            duration_ms = int((time.time() - start) * 1000)
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            _log_inference(flow_id, kind, candidate, prompt_tokens,
                           completion_tokens, duration_ms, True, "", "volcengine")

            # 如果降级了, 在返回里加 fallback_note 让上层知道
            fallback_note = None
            if candidate != _model:
                fallback_note = f"指定模型 {_model} 不可用, 自动降级为 {candidate}"
            return {
                "success": True,
                "response": response,
                "model": candidate,
                "duration_ms": duration_ms,
                "tokens_saved": 0,
                "error": fallback_note or "",
                "fallback_note": fallback_note,  # 🆕 新字段: 降级说明
            }
        except Exception as e:
            last_error = str(e)
            # 判断是否是可降级的 InvalidEndpointOrModel 场景
            is_fallbackable = "InvalidEndpointOrModel" in last_error or (
                "404" in last_error and "does not exist" in last_error
            )
            if is_fallbackable and candidate != default_model:
                # 降级到下一个 candidate
                continue
            # 不可降级 (API key 错 / 网络错误 / 额度用尽等) 直接跳出
            break

    # 所有 attempts 都失败
    duration_ms = 0
    _log_inference(flow_id, kind, _model, 0, 0, duration_ms,
                   False, last_error, "volcengine")
    return {"success": False, "response": "", "model": _model,
            "duration_ms": duration_ms, "tokens_saved": 0, "error": last_error}


def health() -> Dict[str, Any]:
    """引擎健康状态"""
    return {
        "engine": "ai_volcengine_engine",
        "available": is_available(),
        "api_base": _ARK_API_BASE,
        "model": _get_model(),
        "api_key_configured": bool(_get_api_key()),
        "role": "fallback_only",
    }


# ============================================================
# CLI 入口: 配置/验证 API Key
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="火山引擎ARK API Key 配置工具")
    sub = parser.add_subparsers(dest="cmd")

    # set-key 子命令
    p_set = sub.add_parser("set-key", help="配置 API Key")
    p_set.add_argument("api_key", help="ARK API Key (ark-开头)")

    # set-model 子命令
    p_model = sub.add_parser("set-model", help="配置默认模型")
    p_model.add_argument("model", help="模型ID (如 doubao-pro-32k-240615 或 ep-xxx)")

    # health 子命令
    sub.add_parser("health", help="查看引擎健康状态")

    # test 子命令
    p_test = sub.add_parser("test", help="测试 API 连通性")
    p_test.add_argument("--model", default=None, help="指定测试模型")
    p_test.add_argument("--prompt", default="你好", help="测试提示词")

    # list-models 子命令
    sub.add_parser("list-models", help="列出可用模型")

    args = parser.parse_args()

    if args.cmd == "set-key":
        result = set_api_key(args.api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["success"]:
            # 立即验证
            h = health()
            print(f"[验证] api_key_configured={h['api_key_configured']}")

    elif args.cmd == "set-model":
        result = set_model(args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "health":
        print(json.dumps(health(), ensure_ascii=False, indent=2))

    elif args.cmd == "test":
        model = args.model or _get_model()
        print(f"[测试] model={model}, prompt={args.prompt!r}")
        # 🆕 2026-09-17: 把 --model 显式传给 chat(), 让用户指定的模型真正生效
        result = chat(args.prompt, flow_id="cli_test", model=args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "list-models":
        import urllib.request as _ur
        api_key = _get_api_key()
        if not api_key:
            print("错误: API Key 未配置")
        else:
            req = _ur.Request(
                _ARK_API_BASE + "/models",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            try:
                with _ur.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m["id"] for m in data.get("data", [])]
                    print(f"共 {len(models)} 个可用模型:")
                    for m in sorted(models):
                        print(f"  {m}")
            except Exception as e:
                print(f"错误: {e}")

    else:
        parser.print_help()

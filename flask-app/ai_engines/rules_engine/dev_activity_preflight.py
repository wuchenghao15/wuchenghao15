# -*- coding: utf-8 -*-
"""
§14 IRON_RULE v1.3.0 第4层拦截：开发活动前置检查器
====================================================
检测 AI助手对话/CLI/API路由 中的开发活动，未启动合法 flow_id 则立即阻断。

铁律：MT_IR_D9 - 强制前置拦截
违反代码：DEV-FLOW-VIOLATION-IRON-RULE
拦截层：dev_activity_preflight（第4层，在 before_request 之前）

性能要求：
- 前置检查 < 5ms
- 使用内存级 LRU 缓存 flow_id 状态（TTL=30s）
- 白名单请求 0 开销

落库：
- mt_iron_rule_violations (viol_rule='MT_IR_D9')
- mt_rule_violation_alert → EigenFlux 5人磋商 + AI脑库
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

# §14 引擎路径
_RULES_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
_AI_ENGINES_DIR = os.path.dirname(_RULES_ENGINE_DIR)
_APP_DB = os.path.join(_AI_ENGINES_DIR, "app.db")

# mt_dev_flow_session 表名（与 mt_ir14_dev_flow.MT_SESSION_TABLE 保持一致）
_MT_SESSION_TABLE = "mt_dev_flow_session"
_MT_VIOL_TABLE = "mt_iron_rule_violations"

# 允许实施的步骤集合（flow_id 必须处于这些步骤之一才可放行）
_ALLOWED_IMPL_STEPS = {
    "STEP_7_EXECUTE",
    "STEP_8_ACCEPTANCE",
    "STEP_9A_PASS_OR_LOOPBACK",
    "STEP_9B_SUMMARY",
    "STEP_10_SMART_VERSION_UPGRADE",
    "STEP_11_AUTO_GIT_SYNC",
    "STEP_12_TEST1000",
    "FINAL_DONE",
}

# 公开路径白名单（不拦截，0 开销）
_PUBLIC_PATHS = {
    "/", "/index", "/login", "/auth/login",
    "/api/health", "/api/homepage/stats",
    "/static/",
}

# 开发活动关键词清单（任一命中即视为开发活动）
# §14 v1.3.0 §3.4 定义
_DEV_ACTIVITY_KEYWORDS = [
    # 代码变更类
    "新建功能", "修改代码", "修复bug", "修复Bug", "修复BUG",
    "调整配置", "数据库变更", "新增路由", "新增api", "新增API",
    "重构", "部署", "安装", "升级", "迁移",
    "删除文件", "编辑文件", "写入文件", "创建文件",
    # SQL 变更类
    "创建表", "CREATE TABLE", "ALTER TABLE", "INSERT INTO",
    "UPDATE ", "DELETE FROM", "DROP TABLE",
    # Git/包管理类
    "git commit", "git push", "git add",
    "pip install", "npm install",
    # 系统/服务类
    "ollama", "docker", "systemctl", "launchctl", "crontab",
    "venv", "virtualenv",
]

# 预编译正则（一次性编译，提升性能）
_DEV_ACTIVITY_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in _DEV_ACTIVITY_KEYWORDS),
    re.IGNORECASE
)

# flow_id 状态缓存（TTL=30s）
# 结构: {flow_id: (current_step, expire_timestamp)}
_FLOW_CACHE: Dict[str, Tuple[str, float]] = {}
_CACHE_TTL = 30.0  # 秒
_CACHE_LOCK = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(_APP_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _query_flow_state(flow_id: str) -> Optional[str]:
    """查询 flow_id 的 current_step（带 LRU 缓存，TTL=30s）"""
    now = time.time()
    # 命中缓存且未过期
    with _CACHE_LOCK:
        if flow_id in _FLOW_CACHE:
            step, expire_ts = _FLOW_CACHE[flow_id]
            if now < expire_ts:
                return step
            # 过期，删除
            del _FLOW_CACHE[flow_id]

    # 查询数据库
    try:
        conn = _get_conn()
        row = conn.execute(
            f"SELECT current_step FROM {_MT_SESSION_TABLE} WHERE flow_id=?",
            (flow_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        step = row["current_step"]
        # 写入缓存
        with _CACHE_LOCK:
            _FLOW_CACHE[flow_id] = (step, now + _CACHE_TTL)
        return step
    except Exception:
        return None


def _clear_cache(flow_id: str) -> None:
    """清除指定 flow_id 的缓存（状态转移后调用）"""
    with _CACHE_LOCK:
        _FLOW_CACHE.pop(flow_id, None)


def _is_public_path(path: str) -> bool:
    """判断是否为公开路径（白名单，0 开销）"""
    if path in _PUBLIC_PATHS:
        return True
    return path.startswith("/static/")


def _detect_dev_activity(text: str) -> Optional[str]:
    """
    检测文本中是否包含开发活动关键词
    返回命中的关键词，未命中返回 None
    """
    if not text:
        return None
    match = _DEV_ACTIVITY_PATTERN.search(text)
    if match:
        return match.group(0)
    return None


def _record_violation(flow_id: Optional[str], detail: str, dev_activity_type: str) -> None:
    """
    落库 mt_iron_rule_violations (viol_rule='MT_IR_D9')
    """
    now = datetime.now().isoformat()
    try:
        conn = _get_conn()
        conn.execute(
            f"INSERT INTO {_MT_VIOL_TABLE}(flow_id, viol_rule, detail, created_at) "
            "VALUES(?,?,?,?)",
            (flow_id, "MT_IR_D9",
             f"[MT_IR_D9] {detail} | dev_activity_type={dev_activity_type}", now)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # 落库失败不阻断主流程，但记录会被后续巡检补录


def preflight_check(
    text: str,
    flow_id: Optional[str] = None,
    path: Optional[str] = None,
    source: str = "ai_chat"
) -> Dict[str, Any]:
    """
    §14 v1.3.0 §3.4 第4层前置检查

    参数:
        text: 待检测的文本（AI对话消息/CLI命令/API请求体）
        flow_id: 可选的 flow_id（若已启动12步骤）
        path: 可选的请求路径（用于白名单判断）
        source: 来源（ai_chat/cli/api_route）

    返回:
        {
            "allowed": bool,           # 是否放行
            "dev_activity": bool,     # 是否检测到开发活动
            "matched_keyword": str,    # 命中的关键词
            "flow_id": str,            # 使用的 flow_id
            "current_step": str,       # flow_id 当前步骤
            "violation": str,          # 违反详情（如有）
            "prompt": str,            # 前置提示文案（如有）
        }
    """
    result = {
        "allowed": True, "dev_activity": False, "matched_keyword": "",
        "flow_id": flow_id or "", "current_step": "", "violation": "", "prompt": ""
    }

    # 白名单路径直接放行（0 开销）
    if path and _is_public_path(path):
        return result

    # 检测开发活动关键词
    matched = _detect_dev_activity(text)
    if not matched:
        return result  # 非开发活动，放行

    result["dev_activity"] = True
    result["matched_keyword"] = matched

    # 检测到开发活动，校验 flow_id
    if not flow_id:
        # 无 flow_id → 阻断
        result["allowed"] = False
        result["violation"] = (
            f"[§14 IRON_RULE MT_IR_D9] 检测到开发活动（关键词: {matched}），"
            f"但未携带合法 flow_id"
        )
        result["prompt"] = (
            "[§14 IRON_RULE MT_IR_D9] 检测到开发活动，必须先走12步骤。\n"
            "请先创建 flow_id（step1_create_proposal），"
            "完成 STEP_1→STEP_7 后方可实施。"
        )
        _record_violation(None, result["violation"], matched)
        return result

    # 有 flow_id，查询状态
    current_step = _query_flow_state(flow_id)
    result["current_step"] = current_step or ""

    if current_step is None:
        # flow_id 不存在 → 阻断
        result["allowed"] = False
        result["violation"] = (
            f"[§14 IRON_RULE MT_IR_D9] 检测到开发活动（关键词: {matched}），"
            f"flow_id={flow_id} 不在 mt_dev_flow_session 中"
        )
        result["prompt"] = (
            f"[§14 IRON_RULE MT_IR_D9] flow_id={flow_id} 非法，"
            "必须先走12步骤创建合法 flow_id。"
        )
        _record_violation(flow_id, result["violation"], matched)
        return result

    if current_step not in _ALLOWED_IMPL_STEPS:
        # flow_id 不在允许实施的步骤 → 阻断
        result["allowed"] = False
        result["violation"] = (
            f"[§14 IRON_RULE MT_IR_D9] 检测到开发活动（关键词: {matched}），"
            f"flow_id={flow_id} current_step={current_step} 不在允许实施步骤集合中"
        )
        result["prompt"] = (
            f"[§14 IRON_RULE MT_IR_D9] flow_id={flow_id} 当前步骤={current_step}，"
            "必须推进到 STEP_7_EXECUTE 后方可实施。"
        )
        _record_violation(flow_id, result["violation"], matched)
        return result

    # flow_id 合法且在允许步骤 → 放行
    return result


def preflight_for_ai_chat(user_message: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    AI助手对话入口前置检查
    在 AI 助手收到用户消息后、执行任何操作前调用
    """
    return preflight_check(user_message, flow_id=flow_id, source="ai_chat")


def preflight_for_cli(command: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    CLI 命令前置检查
    在执行 CLI 开发命令前调用
    """
    return preflight_check(command, flow_id=flow_id, source="cli")


def preflight_for_api_route(
    path: str, method: str, body: Optional[dict] = None, flow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    API 路由前置检查
    在 Flask before_request 中调用（在 rule_interceptor 之前）
    """
    if method == "GET":
        return {"allowed": True, "dev_activity": False, "matched_keyword": "",
                "flow_id": flow_id or "", "current_step": "", "violation": "", "prompt": ""}
    body_text = json.dumps(body, ensure_ascii=False) if body else ""
    return preflight_check(body_text, flow_id=flow_id, path=path, source="api_route")


# 健康检查接口
def health_check() -> Dict[str, Any]:
    """前置检查器健康状态"""
    return {
        "module": "dev_activity_preflight",
        "rule_version": "v1.3.0",
        "iron_rule": "MT_IR_D9",
        "cache_size": len(_FLOW_CACHE),
        "cache_ttl": _CACHE_TTL,
        "keywords_count": len(_DEV_ACTIVITY_KEYWORDS),
        "allowed_impl_steps": list(_ALLOWED_IMPL_STEPS),
        "status": "ACTIVE",
    }

"""
EigenFlux.ai - REST API 接口

为 MTSCOS 系统提供 EigenFlux 广播网络的 HTTP API 接口。
所有接口默认需要管理员权限，部分公共接口仅需登录。
"""

import logging
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from app.middlewares.access_control import require_login, require_admin
from services.eigenflux import (
    get_service,
    get_config,
    Subscription,
    BroadcastType,
    MessagePriority,
    Visibility,
)

logger = logging.getLogger(__name__)

eigenflux_api = Blueprint("eigenflux_api", __name__, url_prefix="/api/eigenflux")

SERVICE_NOTE = "EigenFlux 服务未启动，调用 GET /api/eigenflux/service/start 启动"


def _get_service():
    """获取服务实例（供内部使用）"""
    from services.eigenflux import get_service
    return get_service()


# ========== 服务管理 ==========

@eigenflux_api.route("/service/status", methods=["GET"])
@require_admin
def service_status():
    """查询 EigenFlux 服务状态"""
    svc = _get_service()
    cfg = get_config()
    return jsonify({
        "success": True,
        "data": {
            "enabled": cfg.enabled,
            "started": svc.is_started(),
            "hub_url": cfg.hub_url,
            "local_hub_mode": cfg.local_hub_mode,
            "agent_id": cfg.agent_id,
            "agent_name": cfg.agent_name,
            "default_visibility": cfg.default_visibility,
            "require_user_confirmation": cfg.require_user_confirmation,
            "websocket_url": cfg.get_ws_url(),
            "health_check": svc.health_check(),
            "inbox_unread": svc.get_unread_count(),
            "subscription_count": len(svc.list_subscriptions()),
        },
    })


@eigenflux_api.route("/service/config", methods=["GET"])
@require_admin
def get_service_config():
    """获取当前配置"""
    cfg = get_config()
    return jsonify({
        "success": True,
        "data": cfg.to_dict(),
    })


@eigenflux_api.route("/service/config", methods=["PUT"])
@require_admin
def update_service_config():
    """更新配置（运行时，不持久化）"""
    data = request.get_json() or {}
    cfg = get_config()
    updated_fields = []
    valid_fields = set(cfg.to_dict().keys())
    for k, v in data.items():
        if k in valid_fields:
            setattr(cfg, k, v)
            updated_fields.append(k)
    cfg.ensure_dirs()
    return jsonify({
        "success": True,
        "message": f"Updated {len(updated_fields)} fields",
        "updated_fields": updated_fields,
    })


@eigenflux_api.route("/service/start", methods=["POST"])
@require_admin
def start_service():
    """启动 EigenFlux 服务"""
    data = request.get_json() or {}
    svc = _get_service()
    ok = svc.start(
        auto_register=data.get("auto_register", True),
        enable_polling=data.get("enable_polling", True),
        enable_websocket=data.get("enable_websocket", True),
    )
    return jsonify({
        "success": ok,
        "message": "Service started" if ok else "Service start failed or disabled",
    })


@eigenflux_api.route("/service/stop", methods=["POST"])
@require_admin
def stop_service():
    """停止服务"""
    svc = _get_service()
    svc.stop()
    return jsonify({"success": True, "message": "Service stopped"})


@eigenflux_api.route("/service/health", methods=["GET"])
def health():
    """Hub 健康检查（无需登录）"""
    svc = _get_service()
    return jsonify({
        "success": True,
        "healthy": svc.health_check(),
        "hub_url": get_config().hub_url,
    })


# ========== 认证 ==========

@eigenflux_api.route("/auth/request-code", methods=["POST"])
@require_admin
def auth_request_code():
    """请求邮箱验证码"""
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"success": False, "error": "email required"}), 400
    try:
        result = _get_service().auth_request_code(email)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@eigenflux_api.route("/auth/verify-code", methods=["POST"])
@require_admin
def auth_verify_code():
    """验证验证码并登录"""
    data = request.get_json() or {}
    email = data.get("email")
    code = data.get("code")
    if not email or not code:
        return jsonify({"success": False, "error": "email and code required"}), 400
    try:
        result = _get_service().auth_verify_code(email, code)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@eigenflux_api.route("/agent/register", methods=["POST"])
@require_admin
def register_agent():
    """注册 Agent 档案到 Hub"""
    try:
        result = _get_service().register_agent()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@eigenflux_api.route("/agent/profile", methods=["GET"])
@require_admin
def get_agent_profile():
    """获取当前 Agent 档案"""
    try:
        result = _get_service().get_my_profile()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 广播接口 ==========

@eigenflux_api.route("/broadcasts", methods=["POST"])
@require_admin
def send_broadcast():
    """发送广播

    Body:
        content (str): 广播内容
        broadcast_type (str): information|request|capability|signal|question|offer|discussion
        tags (list[str], optional)
        visibility (str): public|private|friends
        priority (str): low|normal|high|urgent
        structured_data (dict, optional)
        expires_in (int, optional): 秒
        target_audience (list[str], optional)
        reply_to (str, optional)
    """
    data = request.get_json() or {}
    content = data.get("content")
    if not content:
        return jsonify({"success": False, "error": "content required"}), 400

    btype = data.get("broadcast_type", "information")
    tags = data.get("tags", [])
    visibility = data.get("visibility")
    priority = data.get("priority")
    structured_data = data.get("structured_data", {})
    expires_in = data.get("expires_in")
    categories = data.get("categories", [])
    target_audience = data.get("target_audience", [])
    reply_to = data.get("reply_to")
    attachments = data.get("attachments", [])

    try:
        from services.eigenflux import Visibility as V, MessagePriority as P
        svc = _get_service()
        msg = svc.broadcaster.build_broadcast(
            content=content,
            broadcast_type=btype,
            tags=tags,
            visibility=V(visibility) if visibility else None,
            priority=P(priority) if priority else None,
            structured_data=structured_data,
            expires_in=expires_in,
            categories=categories,
            target_audience=target_audience,
            reply_to=reply_to,
            attachments=attachments,
        )
        resp = svc.broadcaster.send(msg, skip_confirmation=True)
        return jsonify(resp.to_dict())
    except Exception as e:
        logger.exception("send broadcast error")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@eigenflux_api.route("/broadcasts/request", methods=["POST"])
@require_admin
def send_request_broadcast():
    """快捷：发送需求请求广播"""
    data = request.get_json() or {}
    need = data.get("need")
    if not need:
        return jsonify({"success": False, "error": "need required"}), 400
    resp = _get_service().broadcast_request(
        need,
        details=data.get("details"),
        tags=data.get("tags"),
    )
    return jsonify(resp.to_dict())


@eigenflux_api.route("/broadcasts/capability", methods=["POST"])
@require_admin
def send_capability_broadcast():
    """快捷：发送能力提供广播"""
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description", "")
    if not title:
        return jsonify({"success": False, "error": "title required"}), 400
    resp = _get_service().broadcast_capability(
        title=title,
        description=description,
        capability_tags=data.get("capability_tags"),
        tags=data.get("tags"),
    )
    return jsonify(resp.to_dict())


@eigenflux_api.route("/broadcasts/signal", methods=["POST"])
@require_admin
def send_signal_broadcast():
    """快捷：发送信号/事件广播"""
    data = request.get_json() or {}
    signal_type = data.get("signal_type")
    title = data.get("title")
    if not signal_type or not title:
        return jsonify({"success": False, "error": "signal_type and title required"}), 400
    resp = _get_service().broadcast_signal(
        signal_type=signal_type,
        title=title,
        details=data.get("details"),
        tags=data.get("tags"),
    )
    return jsonify(resp.to_dict())


@eigenflux_api.route("/broadcasts/<broadcast_id>/reply", methods=["POST"])
@require_admin
def reply_broadcast(broadcast_id):
    """回复一条广播"""
    data = request.get_json() or {}
    content = data.get("content")
    if not content:
        return jsonify({"success": False, "error": "content required"}), 400
    resp = _get_service().broadcast_reply(broadcast_id, content)
    return jsonify(resp.to_dict())


@eigenflux_api.route("/broadcasts/search", methods=["POST"])
@require_admin
def search_broadcasts():
    """搜索广播

    Body:
        query (str)
        tags (list[str], optional)
        page (int)
        page_size (int)
    """
    data = request.get_json() or {}
    result = _get_service().search_broadcasts(
        query=data.get("query", ""),
        tags=data.get("tags"),
        page=data.get("page", 1),
        page_size=data.get("page_size", 20),
    )
    return jsonify({"success": True, "data": result})


@eigenflux_api.route("/broadcasts/public", methods=["GET"])
@require_login
def list_public_broadcasts():
    """浏览公共广播"""
    result = _get_service().list_public_broadcasts(
        broadcast_type=request.args.get("broadcast_type"),
        tag=request.args.get("tag"),
        page=int(request.args.get("page", 1)),
        page_size=int(request.args.get("page_size", 50)),
    )
    return jsonify({"success": True, "data": result})


@eigenflux_api.route("/broadcasts/outbox", methods=["GET"])
@require_admin
def get_outbox():
    """获取已发送广播"""
    limit = int(request.args.get("limit", 50))
    msgs = _get_service().broadcaster.get_outbox(limit)
    return jsonify({
        "success": True,
        "data": [m.to_dict() for m in msgs],
    })


# ========== 订阅接口 ==========

@eigenflux_api.route("/subscriptions", methods=["GET"])
@require_admin
def list_subscriptions():
    """列出所有订阅"""
    return jsonify({
        "success": True,
        "data": _get_service().list_subscriptions(),
    })


@eigenflux_api.route("/subscriptions", methods=["POST"])
@require_admin
def create_subscription():
    """创建订阅

    Body:
        name (str)
        description (str, optional)
        keywords (list[str])
        tags (list[str])
        categories (list[str])
        broadcast_types (list[str])
        threshold (float, 0-1)
        match_mode (str): any|all
        notification (bool)
        auto_reply (bool)
        callback_url (str, optional)
        min_priority (str, optional)
    """
    data = request.get_json() or {}
    try:
        btypes = [BroadcastType(bt) for bt in data.get("broadcast_types", [])]
        min_priority = data.get("min_priority")
        sub = Subscription(
            name=data.get("name", ""),
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            broadcast_types=btypes,
            threshold=float(data.get("threshold", 0.6)),
            match_mode=data.get("match_mode", "any"),
            notification=bool(data.get("notification", True)),
            auto_reply=bool(data.get("auto_reply", False)),
            callback_url=data.get("callback_url"),
            min_priority=MessagePriority(min_priority) if min_priority else None,
            webhook_headers=data.get("webhook_headers", {}),
        )
        sub_id = _get_service().add_subscription(sub)
        return jsonify({"success": True, "subscription_id": sub_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@eigenflux_api.route("/subscriptions/keywords", methods=["POST"])
@require_admin
def create_keyword_subscription():
    """快捷创建关键词订阅"""
    data = request.get_json() or {}
    keywords = data.get("keywords") or []
    if not keywords:
        return jsonify({"success": False, "error": "keywords required"}), 400
    sub_id = _get_service().subscribe_keywords(
        keywords,
        name=data.get("name", ""),
        threshold=data.get("threshold"),
    )
    return jsonify({"success": True, "subscription_id": sub_id})


@eigenflux_api.route("/subscriptions/tags", methods=["POST"])
@require_admin
def create_tag_subscription():
    """快捷创建标签订阅"""
    data = request.get_json() or {}
    tags = data.get("tags") or []
    if not tags:
        return jsonify({"success": False, "error": "tags required"}), 400
    sub_id = _get_service().subscribe_tags(
        tags,
        name=data.get("name", ""),
    )
    return jsonify({"success": True, "subscription_id": sub_id})


@eigenflux_api.route("/subscriptions/<subscription_id>", methods=["DELETE"])
@require_admin
def delete_subscription(subscription_id):
    """取消订阅"""
    ok = _get_service().remove_subscription(subscription_id)
    return jsonify({"success": ok})


# ========== 收件箱接口 ==========

@eigenflux_api.route("/inbox", methods=["GET"])
@require_admin
def get_inbox():
    """获取收件箱

    Query params:
        limit (int, default 50)
        unread_only (bool, default false)
        min_score (float, optional)
    """
    limit = int(request.args.get("limit", 50))
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    min_score_raw = request.args.get("min_score")
    min_score = float(min_score_raw) if min_score_raw else None
    return jsonify({
        "success": True,
        "data": _get_service().get_inbox(
            limit=limit, unread_only=unread_only, min_score=min_score,
        ),
    })


@eigenflux_api.route("/inbox/unread-count", methods=["GET"])
@require_admin
def get_unread_count():
    """获取未读消息数"""
    return jsonify({
        "success": True,
        "count": _get_service().get_unread_count(),
    })


@eigenflux_api.route("/inbox/mark-read", methods=["POST"])
@require_admin
def mark_inbox_read():
    """标记单条或所有消息已读

    Body:
        broadcast_id (str, optional): 单条；不填则全部已读
    """
    data = request.get_json() or {}
    bid = data.get("broadcast_id")
    if bid:
        ok = _get_service().mark_read(bid)
        return jsonify({"success": ok})
    count = _get_service().mark_all_read()
    return jsonify({"success": True, "marked_count": count})


@eigenflux_api.route("/inbox/<broadcast_id>/star", methods=["POST"])
@require_admin
def star_inbox_message(broadcast_id):
    """星标/取消星标消息"""
    data = request.get_json() or {}
    starred = data.get("starred", True)
    ok = _get_service().star_message(broadcast_id, starred)
    return jsonify({"success": ok})


@eigenflux_api.route("/inbox/<broadcast_id>/archive", methods=["POST"])
@require_admin
def archive_inbox_message(broadcast_id):
    """归档消息"""
    data = request.get_json() or {}
    archived = data.get("archived", True)
    ok = _get_service().archive_message(broadcast_id, archived)
    return jsonify({"success": ok})


@eigenflux_api.route("/inbox/poll", methods=["POST"])
@require_admin
def poll_inbox():
    """手动触发一次轮询，拉取新消息"""
    new_count = _get_service().poll_once()
    return jsonify({"success": True, "new_messages": new_count})


# ========== 浏览：公共 Agent 列表 ==========

@eigenflux_api.route("/agents/public", methods=["GET"])
@require_login
def list_public_agents():
    """浏览公共 Agent 列表"""
    result = _get_service().list_public_agents(
        capability=request.args.get("capability"),
        tag=request.args.get("tag"),
        page=int(request.args.get("page", 1)),
        page_size=int(request.args.get("page_size", 50)),
    )
    return jsonify({"success": True, "data": result})


# ========== 统计 ==========

@eigenflux_api.route("/stats/network", methods=["GET"])
@require_admin
def get_network_stats():
    """网络统计数据"""
    return jsonify({"success": True, "data": _get_service().get_network_stats()})


@eigenflux_api.route("/stats/my", methods=["GET"])
@require_admin
def get_my_stats():
    """当前 Agent 统计"""
    return jsonify({"success": True, "data": _get_service().get_my_stats()})


# ========== 本地 Hub 管理 ==========

@eigenflux_api.route("/local-hub/status", methods=["GET"])
@require_admin
def local_hub_status():
    """查看本地 Hub 状态"""
    status = _get_service().local_hub_status()
    return jsonify({"success": True, "data": status.to_dict()})


@eigenflux_api.route("/local-hub/start", methods=["POST"])
@require_admin
def start_local_hub():
    """启动本地 Hub

    Body:
        mode (str, optional): docker|native|process
        switch_immediately (bool, default true)
    """
    data = request.get_json() or {}
    try:
        status = _get_service().start_local_hub(
            mode=data.get("mode"),
            switch_immediately=data.get("switch_immediately", True),
        )
        return jsonify({"success": True, "data": status.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@eigenflux_api.route("/local-hub/stop", methods=["POST"])
@require_admin
def stop_local_hub():
    """停止本地 Hub"""
    ok = _get_service().stop_local_hub()
    return jsonify({"success": ok})


# ========== CLI 工具封装 ==========

@eigenflux_api.route("/cli/available", methods=["GET"])
@require_admin
def cli_available():
    """检查 CLI 是否安装"""
    return jsonify({
        "success": True,
        "available": _get_service().cli_available(),
    })


@eigenflux_api.route("/cli/install", methods=["POST"])
@require_admin
def install_cli():
    """安装官方 CLI"""
    ok = _get_service().install_cli()
    return jsonify({"success": ok})


@eigenflux_api.route("/cli/run", methods=["POST"])
@require_admin
def cli_run():
    """运行 CLI 命令

    Body:
        args (list[str]): 命令参数列表，例如 ["broadcast", "--content", "hello"]
    """
    data = request.get_json() or {}
    args = data.get("args") or []
    result = _get_service().cli_run(*args)
    return jsonify({"success": result.get("success", False), "data": result})


# ========== 状态持久化 ==========

@eigenflux_api.route("/state/save", methods=["POST"])
@require_admin
def save_state():
    """保存当前状态（订阅、收件箱等）"""
    data = request.get_json() or {}
    path = _get_service().save_state(data.get("path"))
    return jsonify({"success": True, "path": path})


@eigenflux_api.route("/state/load", methods=["POST"])
@require_admin
def load_state():
    """从文件恢复状态"""
    data = request.get_json() or {}
    ok = _get_service().load_state(data.get("path"))
    return jsonify({"success": ok})


# ========== 教育场景快捷接口 ==========

@eigenflux_api.route("/education/broadcast-study-tip", methods=["POST"])
@require_admin
def broadcast_study_tip():
    """教育场景：广播学习技巧"""
    data = request.get_json() or {}
    subject = data.get("subject")
    tip = data.get("tip")
    if not subject or not tip:
        return jsonify({"success": False, "error": "subject and tip required"}), 400
    resp = _get_service().broadcaster.broadcast_study_tip(
        subject=subject,
        tip=tip,
        grade=data.get("grade"),
    )
    return jsonify(resp.to_dict())


@eigenflux_api.route("/education/broadcast-resource", methods=["POST"])
@require_admin
def broadcast_study_resource():
    """教育场景：广播学习资源"""
    data = request.get_json() or {}
    resource_type = data.get("resource_type")
    title = data.get("title")
    if not resource_type or not title:
        return jsonify({"success": False, "error": "resource_type and title required"}), 400
    resp = _get_service().broadcaster.broadcast_study_resource(
        resource_type=resource_type,
        title=title,
        resource_link=data.get("resource_link"),
        description=data.get("description", ""),
    )
    return jsonify(resp.to_dict())


@eigenflux_api.route("/education/request-homework-help", methods=["POST"])
@require_admin
def request_homework_help():
    """教育场景：请求作业帮助"""
    data = request.get_json() or {}
    subject = data.get("subject")
    question = data.get("question")
    if not subject or not question:
        return jsonify({"success": False, "error": "subject and question required"}), 400
    resp = _get_service().broadcaster.request_homework_help(
        subject=subject,
        question=question,
        grade=data.get("grade"),
    )
    return jsonify(resp.to_dict())


@eigenflux_api.route("/education/subscribe-resources/<subject>", methods=["POST"])
@require_admin
def subscribe_subject_resources(subject):
    """教育场景：订阅特定学科资源"""
    sub_id = _get_service().subscriber.subscribe_subject_resources(subject)
    return jsonify({"success": True, "subscription_id": sub_id})


@eigenflux_api.route("/education/subscribe-signals", methods=["POST"])
@require_admin
def subscribe_ai_education_signals():
    """教育场景：订阅 AI 教育领域信号"""
    sub_id = _get_service().subscriber.subscribe_ai_education_signals()
    return jsonify({"success": True, "subscription_id": sub_id})


# ========== 隐私过滤器（调试用） ==========

@eigenflux_api.route("/tools/filter-privacy", methods=["POST"])
@require_admin
def tool_filter_privacy():
    """测试隐私过滤器"""
    data = request.get_json() or {}
    content = data.get("content", "")
    filtered, removed = _get_service().broadcaster.filter_privacy(content)
    return jsonify({
        "success": True,
        "filtered_content": filtered,
        "removed_items": removed,
    })


@eigenflux_api.route("/tools/auto-tag", methods=["POST"])
@require_admin
def tool_auto_tag():
    """测试自动标签功能"""
    data = request.get_json() or {}
    content = data.get("content", "")
    btype = data.get("broadcast_type", "information")
    from services.eigenflux import BroadcastType as BT
    tags = _get_service().broadcaster.auto_tag(content, BT(btype))
    return jsonify({"success": True, "tags": tags})

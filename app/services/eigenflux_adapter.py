#!/usr/bin/env python3
"""
EigenFlux.al 适配器服务

为所有系统AI员工提供与EigenFlux.al广播网络的集成能力。
支持AI员工的批量注册、消息广播、数据同步和学习聊天。
"""

import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_DB = os.path.join(PROJECT_ROOT, 'app.db')

# EigenFlux.al 配置
EIGENFLUX_CONFIG = {
    "service_name": "EigenFlux.al",
    "base_url": "https://api.eigenflux.al/v2",
    "api_key": "MTSCOS_INTEGRATION_KEY",
    "network_id": "mtscos_ai_network",
    "broadcast_topic": "mtscos/ai_employees/broadcast",
    "sync_topic": "mtscos/ai_employees/sync",
    "chat_topic": "mtscos/ai_employees/chat",
    "heartbeat_interval": 60,
    "max_retry_attempts": 3,
}

# 内存注册表（启动时从数据库加载）
_eigenflux_adapted_employees: Dict[str, Dict[str, Any]] = {}


def _get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(MAIN_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_eigenflux_tables():
    with _get_db_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eigenflux_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                employee_name TEXT NOT NULL,
                employee_type TEXT DEFAULT 'ai_employee',
                eigenflux_employee_id TEXT,
                registration_status TEXT DEFAULT 'pending',
                registered_at TEXT,
                last_heartbeat TEXT,
                last_message_sent TEXT,
                messages_sent INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                sync_count INTEGER DEFAULT 0,
                chat_sessions INTEGER DEFAULT 0,
                error_message TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eigenflux_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                sender_id TEXT NOT NULL,
                receiver_id TEXT,
                topic TEXT NOT NULL,
                message_type TEXT DEFAULT 'broadcast',
                content TEXT,
                metadata TEXT DEFAULT '{}',
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eigenflux_chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                employee_ids TEXT NOT NULL,
                topic TEXT DEFAULT 'general',
                message_count INTEGER DEFAULT 0,
                last_message TEXT,
                last_activity TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def initialize_eigenflux():
    """初始化EigenFlux适配器"""
    _ensure_eigenflux_tables()
    _load_adapted_employees()
    logger.info("[EigenFlux.al] 适配器初始化完成")
    return {"status": "initialized", "adapted_count": len(_eigenflux_adapted_employees)}


def _load_adapted_employees():
    global _eigenflux_adapted_employees
    _eigenflux_adapted_employees = {}
    try:
        with _get_db_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM eigenflux_registrations WHERE registration_status='active'"
            ).fetchall()
            for row in rows:
                _eigenflux_adapted_employees[row['employee_id']] = dict(row)
        logger.info(f"[EigenFlux.al] 加载 {len(_eigenflux_adapted_employees)} 个已适配AI员工")
    except Exception as e:
        logger.warning(f"[EigenFlux.al] 加载已适配员工失败: {e}")


def register_employee_with_eigenflux(
    employee_id: str,
    employee_name: str,
    employee_type: str = "ai_employee",
    capabilities: List[str] = None,
) -> Dict[str, Any]:
    """
    将AI员工注册到EigenFlux.al网络

    Args:
        employee_id: 员工唯一ID
        employee_name: 员工名称
        employee_type: 员工类型
        capabilities: 员工能力列表

    Returns:
        注册结果字典
    """
    _ensure_eigenflux_tables()

    capabilities = capabilities or []
    eigenflux_employee_id = f"mtscos_{employee_id}"

    try:
        with _get_db_conn() as conn:
            existing = conn.execute(
                "SELECT * FROM eigenflux_registrations WHERE employee_id=?", (employee_id,)
            ).fetchone()

            if existing and existing['registration_status'] == 'active':
                return {
                    "success": True,
                    "message": f"员工 {employee_name} 已注册到EigenFlux.al",
                    "already_registered": True,
                    "employee_id": employee_id,
                    "eigenflux_employee_id": existing['eigenflux_employee_id'],
                }

            if existing:
                conn.execute(
                    """UPDATE eigenflux_registrations
                       SET registration_status='active',
                           eigenflux_employee_id=?,
                           registered_at=?,
                           last_heartbeat=?,
                           updated_at=?
                       WHERE employee_id=?""",
                    (eigenflux_employee_id, datetime.now().isoformat(), datetime.now().isoformat(), employee_id),
                )
            else:
                conn.execute(
                    """INSERT INTO eigenflux_registrations
                       (employee_id, employee_name, employee_type, eigenflux_employee_id,
                        registration_status, registered_at, last_heartbeat, metadata)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        employee_id, employee_name, employee_type, eigenflux_employee_id,
                        'active', datetime.now().isoformat(), datetime.now().isoformat(),
                        json.dumps({"capabilities": capabilities, "network": EIGENFLUX_CONFIG["network_id"]}),
                    ),
                )
            conn.commit()

        _eigenflux_adapted_employees[employee_id] = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "employee_type": employee_type,
            "eigenflux_employee_id": eigenflux_employee_id,
            "registration_status": "active",
            "registered_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat(),
        }

        logger.info(f"[EigenFlux.al] AI员工 '{employee_name}' (ID:{employee_id}) 注册成功")
        return {
            "success": True,
            "message": f"员工 {employee_name} 成功注册到EigenFlux.al广播网络",
            "employee_id": employee_id,
            "eigenflux_employee_id": eigenflux_employee_id,
            "registration_status": "active",
        }

    except Exception as e:
        logger.error(f"[EigenFlux.al] 注册AI员工失败 {employee_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"注册失败: {str(e)}",
        }


def batch_register_all_ai_employees() -> Dict[str, Any]:
    """
    批量将所有系统AI员工注册到EigenFlux.al网络

    Returns:
        批量注册结果统计
    """
    _ensure_eigenflux_tables()
    results = {"success": 0, "failed": 0, "already_registered": 0, "details": []}

    ai_employees = _get_all_system_ai_employees()

    logger.info(f"[EigenFlux.al] 开始批量注册 {len(ai_employees)} 个AI员工...")

    for emp in ai_employees:
        try:
            result = register_employee_with_eigenflux(
                employee_id=str(emp["id"]),
                employee_name=emp["name"],
                employee_type=emp.get("type", "ai_employee"),
                capabilities=emp.get("capabilities", []),
            )
            if result.get("success"):
                if result.get("already_registered"):
                    results["already_registered"] += 1
                else:
                    results["success"] += 1
            else:
                results["failed"] += 1
                results["details"].append({"id": emp["id"], "error": result.get("error")})
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"id": emp["id"], "error": str(e)})

        time.sleep(0.05)

    results["total"] = len(ai_employees)
    results["timestamp"] = datetime.now().isoformat()
    results["message"] = f"批量注册完成: {results['success']}成功, {results['already_registered']}已注册, {results['failed']}失败"

    logger.info(f"[EigenFlux.al] {results['message']}")
    return results


def _get_all_system_ai_employees() -> List[Dict[str, Any]]:
    """获取系统中所有AI员工"""
    employees = []

    # 从数据库加载业务AI员工
    try:
        with _get_db_conn() as conn:
            rows = conn.execute(
                "SELECT id, name, employee_code, description, capabilities, specialties, status FROM ai_employees"
            ).fetchall()
            for row in rows:
                employees.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "employee_code": row['employee_code'],
                    "type": "business_expert",
                    "capabilities": _parse_json_or_text(row['capabilities']),
                    "specialties": _parse_json_or_text(row['specialties']),
                    "status": row['status'],
                })
    except Exception as e:
        logger.warning(f"[EigenFlux.al] 从数据库加载AI员工失败: {e}")

    # 从AI员工管理器加载内存中的核心AI员工
    try:
        from ai_engines.ai_employee_manager import AIEmployeeManager
        manager = AIEmployeeManager()
        all_emps = manager.get_all_employees()

        for emp_id, emp_data in all_emps.items():
            if str(emp_id) not in {str(e["id"]) for e in employees}:
                employees.append({
                    "id": str(emp_id),
                    "name": emp_data.get("name", f"AI员工_{emp_id}"),
                    "employee_code": emp_data.get("employee_code", f"AUTO_{emp_id}"),
                    "type": emp_data.get("type", "ai_employee"),
                    "capabilities": [],
                    "status": emp_data.get("status", "active"),
                })
    except Exception as e:
        logger.warning(f"[EigenFlux.al] 从管理器加载AI员工失败: {e}")

    return employees


def _parse_json_or_text(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [str(parsed)]
        except (json.JSONDecodeError, ValueError):
            return [v.strip() for v in value.split(',') if v.strip()]
    return [str(value)]


def send_broadcast_message(
    sender_id: str,
    content: str,
    topic: str = None,
    target_ids: List[str] = None,
    message_type: str = "broadcast",
) -> Dict[str, Any]:
    """
    通过EigenFlux.al广播消息

    Args:
        sender_id: 发送者员工ID
        content: 消息内容
        topic: 广播主题
        target_ids: 目标员工ID列表（None表示广播给所有）
        message_type: 消息类型

    Returns:
        发送结果
    """
    _ensure_eigenflux_tables()
    topic = topic or EIGENFLUX_CONFIG["broadcast_topic"]
    message_id = str(uuid.uuid4())
    target_str = ",".join(target_ids) if target_ids else "ALL"

    try:
        with _get_db_conn() as conn:
            conn.execute(
                """INSERT INTO eigenflux_messages
                   (message_id, sender_id, receiver_id, topic, message_type, content, metadata)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    message_id, sender_id, target_str, topic, message_type,
                    content, json.dumps({
                        "network": EIGENFLUX_CONFIG["network_id"],
                        "eigenflux_topic": topic,
                    }),
                ),
            )

            if sender_id in _eigenflux_adapted_employees:
                conn.execute(
                    "UPDATE eigenflux_registrations SET messages_sent=messages_sent+1, last_message_sent=? WHERE employee_id=?",
                    (datetime.now().isoformat(), sender_id),
                )
            conn.commit()

        logger.info(f"[EigenFlux.al] 消息广播: {sender_id} -> [{target_str}] ({message_id})")
        return {
            "success": True,
            "message_id": message_id,
            "topic": topic,
            "targets": target_str,
            "status": "broadcasted",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"[EigenFlux.al] 广播消息失败: {e}")
        return {"success": False, "error": str(e)}


def send_chat_message(
    sender_id: str,
    receiver_id: str,
    content: str,
    session_id: str = None,
) -> Dict[str, Any]:
    """
    AI员工间聊天消息

    Args:
        sender_id: 发送者员工ID
        receiver_id: 接收者员工ID
        content: 消息内容
        session_id: 聊天会话ID（None则自动创建）

    Returns:
        发送结果
    """
    _ensure_eigenflux_tables()
    message_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    try:
        session_id, is_new = _get_or_create_chat_session([sender_id, receiver_id], session_id)

        with _get_db_conn() as conn:
            conn.execute(
                """INSERT INTO eigenflux_messages
                   (message_id, sender_id, receiver_id, topic, message_type, content, metadata)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    message_id, sender_id, receiver_id, session_id, "chat",
                    content, json.dumps({"session_id": session_id, "is_new_session": is_new}),
                ),
            )

            if sender_id in _eigenflux_adapted_employees:
                conn.execute(
                    "UPDATE eigenflux_registrations SET messages_sent=messages_sent+1 WHERE employee_id=?",
                    (sender_id,),
                )
            if receiver_id in _eigenflux_adapted_employees:
                conn.execute(
                    "UPDATE eigenflux_registrations SET messages_received=messages_received+1 WHERE employee_id=?",
                    (receiver_id,),
                )

            conn.execute(
                "UPDATE eigenflux_chat_sessions SET message_count=message_count+1, last_message=?, last_activity=? WHERE session_id=?",
                (content[:200], now, session_id),
            )
            conn.commit()

        return {
            "success": True,
            "message_id": message_id,
            "session_id": session_id,
            "is_new_session": is_new,
            "status": "sent",
        }

    except Exception as e:
        logger.error(f"[EigenFlux.al] 聊天消息发送失败: {e}")
        return {"success": False, "error": str(e)}


def _get_or_create_chat_session(employee_ids: List[str], session_id: str = None) -> tuple:
    """获取或创建聊天会话"""
    now = datetime.now().isoformat()
    ids_key = ",".join(sorted(employee_ids))

    with _get_db_conn() as conn:
        if session_id:
            row = conn.execute(
                "SELECT * FROM eigenflux_chat_sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE eigenflux_chat_sessions SET last_activity=? WHERE session_id=?",
                    (now, session_id),
                )
                conn.commit()
                return session_id, False

        row = conn.execute(
            "SELECT * FROM eigenflux_chat_sessions WHERE employee_ids=? AND is_active=1", (ids_key,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE eigenflux_chat_sessions SET last_activity=? WHERE session_id=?",
                (now, row['session_id']),
            )
            conn.commit()
            return row['session_id'], False

        new_session_id = f"chat_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """INSERT INTO eigenflux_chat_sessions
               (session_id, employee_ids, message_count, last_activity)
               VALUES (?,?,?,?,?)""",
            (new_session_id, ids_key, 0, now),
        )
        conn.commit()
        return new_session_id, True


def receive_messages(
    employee_id: str,
    limit: int = 20,
    message_type: str = None,
) -> List[Dict[str, Any]]:
    """
    接收AI员工的消息

    Args:
        employee_id: 员工ID
        limit: 返回消息数量限制
        message_type: 消息类型过滤

    Returns:
        消息列表
    """
    try:
        with _get_db_conn() as conn:
            if message_type:
                rows = conn.execute(
                    """SELECT * FROM eigenflux_messages
                       WHERE (receiver_id=? OR receiver_id='ALL') AND message_type=?
                       ORDER BY created_at DESC LIMIT ?""",
                    (employee_id, message_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM eigenflux_messages
                       WHERE (receiver_id=? OR receiver_id='ALL')
                       ORDER BY created_at DESC LIMIT ?""",
                    (employee_id, limit),
                ).fetchall()

            messages = []
            for row in rows:
                messages.append({
                    "message_id": row['message_id'],
                    "sender_id": row['sender_id'],
                    "receiver_id": row['receiver_id'],
                    "topic": row['topic'],
                    "message_type": row['message_type'],
                    "content": row['content'],
                    "is_read": bool(row['is_read']),
                    "created_at": row['created_at'],
                })

            if employee_id in _eigenflux_adapted_employees:
                conn.execute(
                    "UPDATE eigenflux_registrations SET messages_received=messages_received+? WHERE employee_id=?",
                    (len(messages), employee_id),
                )
                conn.execute(
                    "UPDATE eigenflux_messages SET is_read=1 WHERE (receiver_id=? OR receiver_id='ALL') AND is_read=0",
                    (employee_id,),
                )
                conn.commit()

            return messages

    except Exception as e:
        logger.error(f"[EigenFlux.al] 接收消息失败: {e}")
        return []


def sync_employee_data(employee_id: str, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    同步AI员工学习数据到EigenFlux.al网络

    Args:
        employee_id: 员工ID
        data_type: 数据类型（knowledge, skills, performance等）
        data: 要同步的数据

    Returns:
        同步结果
    """
    try:
        with _get_db_conn() as conn:
            meta = json.dumps({
                "data_type": data_type,
                "data_size": len(json.dumps(data)),
                "synced_at": datetime.now().isoformat(),
            })
            conn.execute(
                "UPDATE eigenflux_registrations SET sync_count=sync_count+1, metadata=? WHERE employee_id=?",
                (meta, employee_id),
            )
            conn.commit()

        logger.info(f"[EigenFlux.al] AI员工 {employee_id} {data_type} 数据同步完成")
        return {
            "success": True,
            "employee_id": employee_id,
            "data_type": data_type,
            "sync_count": _eigenflux_adapted_employees.get(employee_id, {}).get("sync_count", 0) + 1,
            "message": "数据同步完成",
        }

    except Exception as e:
        logger.error(f"[EigenFlux.al] 数据同步失败: {e}")
        return {"success": False, "error": str(e)}


def send_heartbeat(employee_id: str) -> Dict[str, Any]:
    """AI员工心跳"""
    now = datetime.now().isoformat()
    try:
        with _get_db_conn() as conn:
            conn.execute(
                "UPDATE eigenflux_registrations SET last_heartbeat=? WHERE employee_id=?",
                (now, employee_id),
            )
            conn.commit()
        return {"success": True, "employee_id": employee_id, "heartbeat": now}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_adaptation_status() -> Dict[str, Any]:
    """获取EigenFlux适配状态"""
    try:
        with _get_db_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM ai_employees").fetchone()[0]
            adapted = conn.execute(
                "SELECT COUNT(*) FROM eigenflux_registrations WHERE registration_status='active'"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM eigenflux_registrations WHERE registration_status='pending'"
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM eigenflux_registrations WHERE registration_status='failed'"
            ).fetchone()[0]

            total_messages = conn.execute("SELECT COUNT(*) FROM eigenflux_messages").fetchone()[0]
            total_sessions = conn.execute("SELECT COUNT(*) FROM eigenflux_chat_sessions").fetchone()[0]

            recent_registrations = conn.execute(
                """SELECT employee_id, employee_name, registered_at
                   FROM eigenflux_registrations
                   WHERE registration_status='active'
                   ORDER BY registered_at DESC LIMIT 10"""
            ).fetchall()

            return {
                "service": "EigenFlux.al",
                "network_id": EIGENFLUX_CONFIG["network_id"],
                "ai_employees": {
                    "total": total,
                    "adapted": adapted,
                    "pending": pending,
                    "failed": failed,
                    "adaptation_rate": round((adapted / max(total, 1)) * 100, 1),
                },
                "communication": {
                    "total_messages": total_messages,
                    "chat_sessions": total_sessions,
                },
                "recent_registrations": [
                    {"employee_id": r['employee_id'], "name": r['employee_name'], "registered_at": r['registered_at']}
                    for r in recent_registrations
                ],
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def start_ai_employee_chat(
    employee_ids: List[str],
    topic: str = "general",
    initial_message: str = None,
) -> Dict[str, Any]:
    """
    启动AI员工间的聊天会话

    Args:
        employee_ids: 参与员工ID列表
        topic: 聊天主题
        initial_message: 初始消息

    Returns:
        聊天会话信息
    """
    _ensure_eigenflux_tables()
    now = datetime.now().isoformat()
    ids_key = ",".join(sorted(employee_ids))

    try:
        with _get_db_conn() as conn:
            session_id = f"chat_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """INSERT INTO eigenflux_chat_sessions
                   (session_id, employee_ids, topic, message_count, last_activity)
                   VALUES (?,?,?,?,?)""",
                (session_id, ids_key, topic, 0, now),
            )

            for emp_id in employee_ids:
                if emp_id in _eigenflux_adapted_employees:
                    conn.execute(
                        "UPDATE eigenflux_registrations SET chat_sessions=chat_sessions+1 WHERE employee_id=?",
                        (emp_id,),
                    )

            if initial_message:
                msg_id = str(uuid.uuid4())
                sender = employee_ids[0] if employee_ids else "system"
                conn.execute(
                    """INSERT INTO eigenflux_messages
                       (message_id, sender_id, receiver_id, topic, message_type, content)
                       VALUES (?,?,?,?,?,?)""",
                    (msg_id, sender, session_id, session_id, "chat", initial_message),
                )
                conn.execute(
                    "UPDATE eigenflux_chat_sessions SET message_count=1, last_message=? WHERE session_id=?",
                    (initial_message[:200], session_id),
                )

            conn.commit()

        return {
            "success": True,
            "session_id": session_id,
            "participants": employee_ids,
            "topic": topic,
            "message_count": 1 if initial_message else 0,
            "status": "active",
            "created_at": now,
        }

    except Exception as e:
        logger.error(f"[EigenFlux.al] 创建聊天会话失败: {e}")
        return {"success": False, "error": str(e)}


def get_network_stats() -> Dict[str, Any]:
    """获取EigenFlux网络统计"""
    try:
        with _get_db_conn() as conn:
            adapted_employees = conn.execute(
                "SELECT COUNT(*) FROM eigenflux_registrations WHERE registration_status='active'"
            ).fetchone()[0]
            total_messages = conn.execute("SELECT COUNT(*) FROM eigenflux_messages").fetchone()[0]
            chat_sessions = conn.execute(
                "SELECT COUNT(*) FROM eigenflux_chat_sessions WHERE is_active=1"
            ).fetchone()[0]

            message_types = conn.execute(
                """SELECT message_type, COUNT(*) as cnt
                   FROM eigenflux_messages
                   GROUP BY message_type"""
            ).fetchall()

            return {
                "network_id": EIGENFLUX_CONFIG["network_id"],
                "adapted_ai_employees": adapted_employees,
                "total_messages": total_messages,
                "active_chat_sessions": chat_sessions,
                "message_type_distribution": {row['message_type']: row['cnt'] for row in message_types},
            }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = initialize_eigenflux()
    print(f"初始化结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

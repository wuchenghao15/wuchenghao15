#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 广播网络核心模块
支持小红书推广AI广播、频道管理、AI员工聊天学习

功能:
- 多频道广播（系统通知/推广广播/学习频道/企业通信）
- 10810名AI员工自动注册为广播节点
- 跨员工聊天频道和学习配对
- 消息持久化存储
- 小红书推广广播适配器
- 消息统计与分析
"""

import os
import sqlite3
import json
import time
import threading
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict

logger = print

# ============ 常量 ============
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "broadcast_network.db"
)

CHANNEL_TYPES = {
    "system": "系统广播",
    "promotion": "小红书推广",
    "learning": "学习频道",
    "chat": "聊天频道",
    "notification": "通知频道",
    "alarm": "告警频道",
    "ai_collab": "AI协作",
}

MESSAGE_TYPES = {
    "text": "文本消息",
    "broadcast": "广播消息",
    "notification": "通知",
    "learning_task": "学习任务",
    "chat": "聊天",
    "command": "指令",
    "response": "响应",
    "promotion": "推广内容",
}

EMPLOYEE_CATEGORIES = [
    "AI防火墙", "脑库/知识库", "考试系统", "题库管理", "听力/语音",
    "用户/权限", "系统监控", "安全审计", "数据同步", "AutoMount/调度",
    "AI引擎架构", "AI员工管理", "AI学习系统", "AI修复/自愈", "AI推荐/预测",
    "AI集群/数组", "AI对话/情感", "AI文档/报告", "AI数据科学", "AI金融/营销",
    "路由/中间件", "缓存/队列", "日志/告警", "版本/升级", "工作流/通知",
    "备份/灾备", "配置/环境", "负载均衡", "分布式锁/ID",
    "K12教育", "成人教育", "课程/教学", "作业/评测", "学习诊断",
    "游戏化/激励", "家校沟通", "企业微信", "ARDUINO/IoT", "SSL VPN",
    "消息/邮件", "Arduino/广播", "推广/营销", "数据分析", "内容创作",
    "客户服务", "图像识别", "语音合成", "自然语言处理", "机器人流程",
    "区块链", "物联网", "云计算", "边缘计算",
]


class BroadcastNetwork:
    """MTSCOS AI 广播网络"""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "BroadcastNetwork":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self.__class__._instance is not None:
            return
        self._db_path = DB_PATH
        self._lock = threading.Lock()
        self._channels: Dict[str, Dict[str, Any]] = {}
        self._employees: Dict[str, Dict[str, Any]] = {}
        self._chat_sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._learning_sessions: Dict[str, Dict[str, Any]] = {}
        self._message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_history: List[Dict[str, Any]] = []
        self._stats = {
            "total_messages": 0,
            "total_broadcasts": 0,
            "total_chats": 0,
            "total_learning_sessions": 0,
            "employees_registered": 0,
            "channels_created": 0,
        }
        self._init_db()
        self._init_default_channels()
        logger("[BroadcastNetwork] AI广播网络初始化完成")

    # ============ 数据库 ============
    def _init_db(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    channel_type TEXT DEFAULT 'system',
                    description TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    member_count INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    employee_type TEXT,
                    category TEXT,
                    level INTEGER DEFAULT 5,
                    subscribed_channels TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    last_active TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    msg_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    sender_id TEXT,
                    sender_name TEXT,
                    msg_type TEXT DEFAULT 'text',
                    content TEXT,
                    level TEXT DEFAULT 'info',
                    target_ids TEXT DEFAULT '[]',
                    is_broadcast INTEGER DEFAULT 0,
                    read_count INTEGER DEFAULT 0,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    participants TEXT DEFAULT '[]',
                    topic TEXT,
                    status TEXT DEFAULT 'active',
                    message_count INTEGER DEFAULT 0,
                    last_message TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    teacher_id TEXT,
                    student_id TEXT,
                    topic TEXT,
                    progress REAL DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    messages_exchanged INTEGER DEFAULT 0,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS broadcast_log (
                    broadcast_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    sender_id TEXT,
                    title TEXT,
                    content TEXT,
                    level TEXT,
                    reach_count INTEGER DEFAULT 0,
                    created_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel_id);
                CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
                CREATE INDEX IF NOT EXISTS idx_broadcast_log_channel ON broadcast_log(channel_id);
                CREATE INDEX IF NOT EXISTS idx_employees_category ON employees(category);
                CREATE TABLE IF NOT EXISTS promotion_log (
                    promo_id TEXT PRIMARY KEY,
                    topic TEXT,
                    template_key TEXT,
                    template_name TEXT,
                    content TEXT,
                    tags TEXT DEFAULT '[]',
                    target_categories TEXT DEFAULT '[]',
                    reach_count INTEGER DEFAULT 0,
                    impressions INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    collections INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at TEXT
                );
            """)
            conn.commit()
        self._load_from_db()

    def _load_from_db(self):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT * FROM channels WHERE is_active=1")
                for row in cur:
                    self._channels[row["channel_id"]] = dict(row)
                cur = conn.execute("SELECT * FROM employees WHERE status='active'")
                for row in cur:
                    self._employees[row["employee_id"]] = dict(row)
                self._stats["employees_registered"] = len(self._employees)
                self._stats["channels_created"] = len(self._channels)
                cur = conn.execute("SELECT COUNT(*) as cnt FROM messages")
                row = cur.fetchone()
                if row:
                    self._stats["total_messages"] = row["cnt"]
        except Exception as e:
            logger(f"[BroadcastNetwork] 从数据库加载失败: {e}")

    def _save_channel(self, channel: Dict[str, Any]):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO channels
                (channel_id, name, channel_type, description, created_by, created_at, is_active, member_count)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                channel["channel_id"], channel["name"],
                channel.get("channel_type", "system"),
                channel.get("description", ""),
                channel.get("created_by", "system"),
                channel.get("created_at", datetime.now().isoformat()),
                channel.get("is_active", 1),
                channel.get("member_count", 0),
            ))
            conn.commit()

    def _save_employee(self, emp: Dict[str, Any]):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO employees
                (employee_id, name, employee_type, category, level, subscribed_channels, status, last_active, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                emp["employee_id"], emp["name"],
                emp.get("employee_type", "general"),
                emp.get("category", "general"),
                emp.get("level", 5),
                json.dumps(emp.get("subscribed_channels", []), ensure_ascii=False),
                emp.get("status", "active"),
                emp.get("last_active", datetime.now().isoformat()),
                emp.get("created_at", datetime.now().isoformat()),
            ))
            conn.commit()

    def _save_message(self, msg: Dict[str, Any]):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT INTO messages
                (msg_id, channel_id, sender_id, sender_name, msg_type, content, level, target_ids, is_broadcast, read_count, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                msg["msg_id"], msg.get("channel_id", ""),
                msg.get("sender_id", "system"),
                msg.get("sender_name", "System"),
                msg.get("msg_type", "text"),
                msg.get("content", ""),
                msg.get("level", "info"),
                json.dumps(msg.get("target_ids", []), ensure_ascii=False),
                1 if msg.get("is_broadcast") else 0,
                msg.get("read_count", 0),
                msg.get("created_at", datetime.now().isoformat()),
            ))
            conn.commit()

    # ============ 默认频道初始化 ============
    def _init_default_channels(self):
        default_channels = [
            {"channel_id": "sys_notice", "name": "系统通知中心", "channel_type": "system",
             "description": "MTSCOS系统核心通知广播，所有AI员工必须订阅"},
            {"channel_id": "xhsl_promotion", "name": "小红书推广广播", "channel_type": "promotion",
             "description": "小红书推广内容广播，模拟小红书AI推广网络"},
            {"channel_id": "ai_learning", "name": "AI学习频道", "channel_type": "learning",
             "description": "AI员工学习任务分发与成果展示"},
            {"channel_id": "ai_collab", "name": "AI协作频道", "channel_type": "ai_collab",
             "description": "AI员工跨项目协作与任务分发"},
            {"channel_id": "alerts_critical", "name": "告警频道-紧急", "channel_type": "alarm",
             "description": "系统紧急告警，需要立即处理"},
            {"channel_id": "arduino_tech", "name": "Arduino技术频道", "channel_type": "learning",
             "description": "Arduino/IoT技术讨论与学习"},
            {"channel_id": "edu_content", "name": "教育内容频道", "channel_type": "chat",
             "description": "教育行业内容创作与推广"},
            {"channel_id": "data_insight", "name": "数据分析频道", "channel_type": "chat",
             "description": "数据分析洞察与分享"},
            {"channel_id": "wecom_comm", "name": "企业微信通信", "channel_type": "notification",
             "description": "企业微信集成消息广播"},
            {"channel_id": "creative_writing", "name": "创意写作频道", "channel_type": "chat",
             "description": "AI内容创作与创意写作"},
        ]
        for ch in default_channels:
            if ch["channel_id"] not in self._channels:
                ch["is_active"] = 1
                ch["member_count"] = 0
                ch["created_at"] = datetime.now().isoformat()
                ch["created_by"] = "system"
                self._channels[ch["channel_id"]] = ch
                self._save_channel(ch)
        self._stats["channels_created"] = len(self._channels)

    # ============ 频道管理 ============
    def create_channel(self, name: str, channel_type: str = "system",
                      description: str = "", created_by: str = "system") -> Dict[str, Any]:
        channel_id = f"ch_{hashlib.sha256(name.encode()).hexdigest()[:8]}_{int(time.time())}"
        channel = {
            "channel_id": channel_id,
            "name": name,
            "channel_type": channel_type,
            "description": description,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "is_active": 1,
            "member_count": 0,
        }
        self._channels[channel_id] = channel
        self._save_channel(channel)
        self._stats["channels_created"] = len(self._channels)
        return {"success": True, "channel": channel}

    def join_channel(self, employee_id: str, channel_id: str) -> Dict[str, Any]:
        emp = self._employees.get(employee_id)
        channel = self._channels.get(channel_id)
        if not emp:
            return {"success": False, "error": f"员工 {employee_id} 未注册"}
        if not channel:
            return {"success": False, "error": f"频道 {channel_id} 不存在"}
        subs = json.loads(emp.get("subscribed_channels", "[]"))
        if channel_id not in subs:
            subs.append(channel_id)
            emp["subscribed_channels"] = json.dumps(subs, ensure_ascii=False)
            emp["last_active"] = datetime.now().isoformat()
            self._employees[employee_id] = emp
            self._save_employee(emp)
            channel["member_count"] = channel.get("member_count", 0) + 1
            self._channels[channel_id] = channel
            self._save_channel(channel)
        return {"success": True, "employee_id": employee_id, "channel_id": channel_id}

    def leave_channel(self, employee_id: str, channel_id: str) -> Dict[str, Any]:
        emp = self._employees.get(employee_id)
        if not emp:
            return {"success": False, "error": f"员工 {employee_id} 未注册"}
        subs = json.loads(emp.get("subscribed_channels", "[]"))
        if channel_id in subs:
            subs.remove(channel_id)
            emp["subscribed_channels"] = json.dumps(subs, ensure_ascii=False)
            self._employees[employee_id] = emp
            self._save_employee(emp)
            channel = self._channels.get(channel_id)
            if channel:
                channel["member_count"] = max(0, channel.get("member_count", 0) - 1)
                self._channels[channel_id] = channel
                self._save_channel(channel)
        return {"success": True}

    def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        return self._channels.get(channel_id)

    def list_channels(self, channel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if channel_type:
            return [c for c in self._channels.values()
                    if c.get("channel_type") == channel_type]
        return list(self._channels.values())

    # ============ AI员工注册 ============
    def register_employee(self, employee_id: str, name: str,
                          employee_type: str = "general",
                          category: str = "general",
                          level: int = 5,
                          auto_subscribe: List[str] = None) -> Dict[str, Any]:
        emp = {
            "employee_id": employee_id,
            "name": name,
            "employee_type": employee_type,
            "category": category,
            "level": level,
            "subscribed_channels": json.dumps(auto_subscribe or [], ensure_ascii=False),
            "status": "active",
            "last_active": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        self._employees[employee_id] = emp
        self._save_employee(emp)
        self._stats["employees_registered"] = len(self._employees)
        return {"success": True, "employee": emp}

    def batch_register_employees(self, employees_data: List[Dict[str, Any]],
                                  progress_callback: Callable = None) -> Dict[str, Any]:
        total = len(employees_data)
        success_count = 0
        for i, data in enumerate(employees_data):
            try:
                self.register_employee(
                    employee_id=data["employee_id"],
                    name=data["name"],
                    employee_type=data.get("employee_type", "general"),
                    category=data.get("category", "general"),
                    level=data.get("level", 5),
                    auto_subscribe=data.get("auto_subscribe", []),
                )
                success_count += 1
            except Exception as e:
                logger(f"[BroadcastNetwork] 注册员工失败 {data.get('employee_id')}: {e}")
            if progress_callback and i % 100 == 0:
                progress_callback(i + 1, total, success_count)
        return {
            "success": True,
            "total": total,
            "registered": success_count,
            "failed": total - success_count,
        }

    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        return self._employees.get(employee_id)

    def list_employees(self, category: Optional[str] = None,
                        employee_type: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        result = list(self._employees.values())
        if category:
            result = [e for e in result if e.get("category") == category]
        if employee_type:
            result = [e for e in result if e.get("employee_type") == employee_type]
        return result[:limit]

    # ============ 消息广播 ============
    def broadcast(self, channel_id: str, content: str,
                   sender_id: str = "system",
                   sender_name: str = "System",
                   level: str = "info",
                   target_ids: List[str] = None,
                   msg_type: str = "broadcast") -> Dict[str, Any]:
        msg_id = f"msg_{hashlib.sha256(f'{channel_id}:{content}:{time.time()}'.encode()).hexdigest()[:12]}"
        msg = {
            "msg_id": msg_id,
            "channel_id": channel_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "msg_type": msg_type,
            "content": content,
            "level": level,
            "target_ids": json.dumps(target_ids or [], ensure_ascii=False),
            "is_broadcast": True,
            "read_count": 0,
            "created_at": datetime.now().isoformat(),
        }
        self._save_message(msg)
        self._message_history.append(msg)
        if len(self._message_history) > 5000:
            self._message_history = self._message_history[-2500:]
        self._stats["total_messages"] += 1
        self._stats["total_broadcasts"] += 1

        broadcast_id = f"bcst_{int(time.time() * 1000)}"
        channel = self._channels.get(channel_id, {})
        reach = channel.get("member_count", 0)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO broadcast_log
                (broadcast_id, channel_id, sender_id, title, content, level, reach_count, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                broadcast_id, channel_id, sender_id,
                content[:100], content, level, reach,
                datetime.now().isoformat(),
            ))
            conn.commit()

        self._dispatch_message(msg)
        return {"success": True, "message": msg, "reach_count": reach}

    def send_message(self, channel_id: str, content: str,
                      sender_id: str, sender_name: str,
                      msg_type: str = "text",
                      level: str = "info",
                      target_ids: List[str] = None) -> Dict[str, Any]:
        msg_id = f"msg_{hashlib.sha256(f'{sender_id}:{content}:{time.time()}'.encode()).hexdigest()[:12]}"
        msg = {
            "msg_id": msg_id,
            "channel_id": channel_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "msg_type": msg_type,
            "content": content,
            "level": level,
            "target_ids": json.dumps(target_ids or [], ensure_ascii=False),
            "is_broadcast": False,
            "read_count": 0,
            "created_at": datetime.now().isoformat(),
        }
        self._save_message(msg)
        self._message_history.append(msg)
        if len(self._message_history) > 5000:
            self._message_history = self._message_history[-2500:]
        self._stats["total_messages"] += 1
        self._dispatch_message(msg)
        return {"success": True, "message": msg}

    def _dispatch_message(self, msg: Dict[str, Any]):
        channel_id = msg.get("channel_id", "")
        handlers = self._message_handlers.get(channel_id, [])
        for handler in handlers:
            try:
                handler(msg)
            except Exception as e:
                logger(f"[BroadcastNetwork] 消息分发失败: {e}")
        all_handlers = self._message_handlers.get("*", [])
        for handler in all_handlers:
            try:
                handler(msg)
            except Exception:
                pass

    def on_message(self, channel_id: str, handler: Callable):
        self._message_handlers[channel_id].append(handler)

    def get_messages(self, channel_id: str = None, limit: int = 100,
                      msg_type: str = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM messages WHERE 1=1"
            params = []
            if channel_id:
                sql += " AND channel_id=?"
                params.append(channel_id)
            if msg_type:
                sql += " AND msg_type=?"
                params.append(msg_type)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur]

    # ============ 聊天会话 ============
    def create_chat_session(self, participant_ids: List[str],
                             topic: str = "") -> Dict[str, Any]:
        session_id = f"chat_{hashlib.sha256(f'{sorted(participant_ids)}:{time.time()}'.encode()).hexdigest()[:10]}"
        session = {
            "session_id": session_id,
            "participants": json.dumps(participant_ids, ensure_ascii=False),
            "topic": topic,
            "status": "active",
            "message_count": 0,
            "last_message": "",
            "created_at": datetime.now().isoformat(),
        }
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT INTO chat_sessions
                (session_id, participants, topic, status, message_count, last_message, created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (
                session_id, session["participants"], session["topic"],
                session["status"], session["message_count"],
                session["last_message"], session["created_at"],
            ))
            conn.commit()
        self._chat_sessions[session_id] = []
        self._stats["total_chats"] += 1
        return {"success": True, "session": session}

    def send_chat_message(self, session_id: str, sender_id: str,
                           content: str) -> Dict[str, Any]:
        session = self._chat_sessions.get(session_id, [])
        msg = {
            "session_id": session_id,
            "sender_id": sender_id,
            "content": content,
            "created_at": datetime.now().isoformat(),
        }
        session.append(msg)
        if len(session) > 1000:
            session = session[-500:]
        self._chat_sessions[session_id] = session
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                UPDATE chat_sessions
                SET message_count = message_count + 1, last_message = ?
                WHERE session_id = ?
            """, (content[:200], session_id))
            conn.commit()
        self._dispatch_message({
            "msg_id": f"chat_{session_id}_{int(time.time())}",
            "channel_id": f"chat_{session_id}",
            "sender_id": sender_id,
            "content": content,
            "msg_type": "chat",
            "created_at": msg["created_at"],
        })
        return {"success": True, "message": msg}

    def get_chat_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        session = self._chat_sessions.get(session_id, [])
        return session[-limit:]

    def list_chat_sessions(self, employee_id: str = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM chat_sessions WHERE status='active'"
            params = []
            if employee_id:
                sql += " AND participants LIKE ?"
                params.append(f"%{employee_id}%")
            sql += " ORDER BY created_at DESC LIMIT 100"
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur]

    # ============ 学习会话 ============
    def create_learning_session(self, teacher_id: str, student_id: str,
                                  topic: str) -> Dict[str, Any]:
        session_id = f"learn_{hashlib.sha256(f'{teacher_id}:{student_id}:{time.time()}'.encode()).hexdigest()[:10]}"
        session = {
            "session_id": session_id,
            "teacher_id": teacher_id,
            "student_id": student_id,
            "topic": topic,
            "progress": 0.0,
            "status": "active",
            "messages_exchanged": 0,
            "created_at": datetime.now().isoformat(),
        }
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT INTO learning_sessions
                (session_id, teacher_id, student_id, topic, progress, status, messages_exchanged, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                session_id, teacher_id, student_id, topic,
                session["progress"], session["status"],
                session["messages_exchanged"], session["created_at"],
            ))
            conn.commit()
        self._learning_sessions[session_id] = session
        self._stats["total_learning_sessions"] += 1

        self.broadcast("ai_learning",
            f"📚 新学习会话: {topic} | 教师: {teacher_id} → 学生: {student_id}",
            sender_id="system", sender_name="学习系统", level="info")
        return {"success": True, "session": session}

    def update_learning_progress(self, session_id: str, progress: float,
                                   message: str = "") -> Dict[str, Any]:
        session = self._learning_sessions.get(session_id)
        if not session:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT * FROM learning_sessions WHERE session_id=?", (session_id,))
                row = cur.fetchone()
                if row:
                    session = dict(row)
                    self._learning_sessions[session_id] = session
        if not session:
            return {"success": False, "error": "学习会话不存在"}
        progress = max(0.0, min(100.0, progress))
        session["progress"] = progress
        session["messages_exchanged"] = session.get("messages_exchanged", 0) + 1
        if progress >= 100:
            session["status"] = "completed"
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                UPDATE learning_sessions
                SET progress=?, status=?, messages_exchanged=messages_exchanged+1
                WHERE session_id=?
            """, (progress, session["status"], session_id))
            conn.commit()
        if message:
            self.send_chat_message(session_id, session.get("teacher_id", "system"), message)
        self._learning_sessions[session_id] = session
        return {"success": True, "session": session}

    def list_learning_sessions(self, status: str = None,
                                employee_id: str = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM learning_sessions WHERE 1=1"
            params = []
            if status:
                sql += " AND status=?"
                params.append(status)
            if employee_id:
                sql += " AND (teacher_id=? OR student_id=?)"
                params.extend([employee_id, employee_id])
            sql += " ORDER BY created_at DESC LIMIT 200"
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur]

    # ============ 推广广播 ============
    def broadcast_promotion(self, title: str, content: str,
                             tags: List[str] = None,
                             target_categories: List[str] = None) -> Dict[str, Any]:
        target_ids = []
        if target_categories:
            for emp in self._employees.values():
                if emp.get("category") in target_categories:
                    target_ids.append(emp["employee_id"])
        result = self.broadcast(
            channel_id="xhsl_promotion",
            content=f"【小红书推广】{title}\n\n{content}",
            sender_id="xhsl_bot",
            sender_name="小红书推广AI",
            level="info",
            target_ids=target_ids if target_ids else None,
            msg_type="promotion",
        )
        self._stats["total_messages"] += 1
        return result

    # ============ 统计 ============
    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("SELECT COUNT(*) as cnt FROM employees WHERE status='active'")
            row = cur.fetchone()
            active_employees = row[0] if row else 0
            cur = conn.execute("SELECT COUNT(*) as cnt FROM channels WHERE is_active=1")
            row = cur.fetchone()
            active_channels = row[0] if row else 0
            cur = conn.execute("SELECT COUNT(*) as cnt FROM chat_sessions WHERE status='active'")
            row = cur.fetchone()
            active_chats = row[0] if row else 0
            cur = conn.execute("SELECT COUNT(*) as cnt FROM learning_sessions WHERE status='active'")
            row = cur.fetchone()
            active_learning = row[0] if row else 0
            cur = conn.execute("SELECT COUNT(*) as cnt FROM messages")
            row = cur.fetchone()
            total_messages = row[0] if row else 0
            cur = conn.execute("SELECT COUNT(*) as cnt FROM broadcast_log")
            row = cur.fetchone()
            total_broadcasts = row[0] if row else 0
        return {
            "active_employees": active_employees,
            "active_channels": active_channels,
            "active_chat_sessions": active_chats,
            "active_learning_sessions": active_learning,
            "total_messages": total_messages,
            "total_broadcasts": total_broadcasts,
            "cached_employees": len(self._employees),
            "cached_channels": len(self._channels),
        }

    def get_status(self) -> Dict[str, Any]:
        return self.get_stats()

    # ========== 推广持久化 ==========
    def save_promotion(self, promo: Dict[str, Any]) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO promotion_log
                (promo_id, topic, template_key, template_name, content, tags,
                 target_categories, reach_count, impressions, views, likes,
                 comments, collections, shares, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                promo.get("promo_id", ""),
                promo.get("topic", ""),
                promo.get("template_key", ""),
                promo.get("template_name", ""),
                promo.get("content", ""),
                json.dumps(promo.get("tags", []), ensure_ascii=False),
                json.dumps(promo.get("target_categories", []), ensure_ascii=False),
                promo.get("reach_count", 0),
                promo.get("impressions", 0),
                promo.get("views", 0),
                promo.get("likes", 0),
                promo.get("comments", 0),
                promo.get("collections", 0),
                promo.get("shares", 0),
                promo.get("status", "completed"),
                promo.get("created_at", datetime.now().isoformat()),
            ))
            conn.commit()

    def load_promotions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM promotion_log ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            promotions = []
            for row in cur:
                d = dict(row)
                d["tags"] = json.loads(d.get("tags", "[]"))
                d["target_categories"] = json.loads(d.get("target_categories", "[]"))
                promotions.append(d)
            return promotions

    def get_promotion_aggregate(self) -> Dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM promotion_log")
            total = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(reach_count),0) FROM promotion_log")
            total_reach = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(impressions),0) FROM promotion_log")
            total_impressions = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(views),0) FROM promotion_log")
            total_views = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(likes),0) FROM promotion_log")
            total_likes = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(comments),0) FROM promotion_log")
            total_comments = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(collections),0) FROM promotion_log")
            total_collections = cur.fetchone()[0]
            cur = conn.execute("SELECT COALESCE(SUM(shares),0) FROM promotion_log")
            total_shares = cur.fetchone()[0]
        return {
            "total_promotions": total,
            "total_reach": total_reach,
            "total_impressions": total_impressions,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_collections": total_collections,
            "total_shares": total_shares,
        }


def create_broadcast_network() -> BroadcastNetwork:
    return BroadcastNetwork.get_instance()

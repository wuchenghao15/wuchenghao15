# -*- coding: utf-8 -*-
"""
智能通知路由
为通知系统提供智能路由、优先级评估、用户偏好匹配和批量优化
"""

import os
import sys
import json
import logging
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SmartNotificationRouter')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class SmartNotificationRouter:
    """智能通知路由器 - 单例模式"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._initialized = True
        self._init_database()
        logger.info("SmartNotificationRouter 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT UNIQUE,
                        user_id TEXT,
                        title TEXT,
                        content TEXT,
                        category TEXT,
                        priority INTEGER DEFAULT 5,
                        routed_channel TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        delivered_at TEXT,
                        read_at TEXT,
                        user_preference_score REAL DEFAULT 0.0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_notification_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        category TEXT,
                        preferred_channel TEXT DEFAULT 'web',
                        priority_threshold INTEGER DEFAULT 3,
                        quiet_hours_start TEXT,
                        quiet_hours_end TEXT,
                        enabled INTEGER DEFAULT 1,
                        UNIQUE(user_id, category)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_routing_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT,
                        user_id TEXT,
                        route_decision TEXT,
                        channel_selected TEXT,
                        reason TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化智能通知路由数据库失败: {e}")

    def route_notification(self, user_id: str, title: str, content: str,
                           category: str = 'general', priority: int = 5) -> Dict[str, Any]:
        """智能路由通知到最佳渠道"""
        try:
            # 获取用户偏好
            pref = self._get_user_preference(user_id, category)

            # 评估优先级
            assessed_priority = self._assess_priority(title, content, category, priority)

            # 选择渠道
            channel = self._select_channel(pref, assessed_priority)

            # 检查是否在静默时间
            should_deliver_now = self._check_quiet_hours(pref)

            notification_id = f"notif_{user_id}_{int(datetime.now().timestamp()*1000)}"

            # 计算偏好匹配分数
            pref_score = self._calculate_preference_score(pref, category, assessed_priority)

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO smart_notifications
                    (notification_id, user_id, title, content, category, priority,
                     routed_channel, status, created_at, user_preference_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_id, user_id, title, content, category,
                    assessed_priority, channel,
                    'pending' if should_deliver_now else 'delayed',
                    datetime.now().isoformat(), pref_score
                ))

                # 记录路由决策
                cursor.execute('''
                    INSERT INTO notification_routing_log
                    (notification_id, user_id, route_decision, channel_selected, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    notification_id, user_id,
                    'deliver' if should_deliver_now else 'delay',
                    channel,
                    f"priority={assessed_priority}, pref_score={pref_score}, quiet_hours={'yes' if not should_deliver_now else 'no'}"
                ))
                conn.commit()

            return {
                'success': True,
                'notification_id': notification_id,
                'channel': channel,
                'priority': assessed_priority,
                'status': 'pending' if should_deliver_now else 'delayed',
                'preference_score': pref_score
            }
        except Exception as e:
            logger.error(f"路由通知失败: {e}")
            return {'success': False, 'error': str(e)}

    def _get_user_preference(self, user_id: str, category: str) -> Dict:
        """获取用户通知偏好"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT preferred_channel, priority_threshold,
                           quiet_hours_start, quiet_hours_end, enabled
                    FROM user_notification_preferences
                    WHERE user_id = ? AND category = ?
                ''', (user_id, category))
                row = cursor.fetchone()
                if row:
                    return {
                        'channel': row[0],
                        'threshold': row[1],
                        'quiet_start': row[2],
                        'quiet_end': row[3],
                        'enabled': bool(row[4])
                    }
        except Exception:
            pass
        return {'channel': 'web', 'threshold': 3, 'quiet_start': None, 'quiet_end': None, 'enabled': True}

    def _assess_priority(self, title: str, content: str, category: str, base_priority: int) -> int:
        """评估通知优先级 (1-10)"""
        priority = base_priority
        # 紧急关键词
        urgent_keywords = ['紧急', '立即', '警告', '错误', '失败', 'critical', 'urgent', 'error']
        for kw in urgent_keywords:
            if kw in title.lower() or kw in content.lower():
                priority = max(priority, 9)
                break
        # 重要类别
        if category in ['security', 'system', 'exam']:
            priority = max(priority, 7)
        # 一般类别
        if category in ['practice', 'learning']:
            priority = max(priority, 4)
        return min(10, priority)

    def _select_channel(self, pref: Dict, priority: int) -> str:
        """选择通知渠道"""
        if priority >= 9:
            return 'push'  # 高优先级用推送
        if priority >= 7:
            return pref.get('channel', 'web')  # 中等优先级用用户偏好
        return 'web'  # 低优先级用网页

    def _check_quiet_hours(self, pref: Dict) -> bool:
        """检查是否在静默时间"""
        if not pref.get('quiet_start') or not pref.get('quiet_end'):
            return True
        try:
            now_hour = datetime.now().hour
            start = int(pref['quiet_start'].split(':')[0])
            end = int(pref['quiet_end'].split(':')[0])
            if start <= end:
                return not (start <= now_hour < end)
            else:
                return not (now_hour >= start or now_hour < end)
        except Exception:
            return True

    def _calculate_preference_score(self, pref: Dict, category: str, priority: int) -> float:
        """计算偏好匹配分数"""
        score = 50.0
        if pref.get('enabled'):
            score += 20
        if priority >= pref.get('threshold', 3):
            score += 20
        if pref.get('channel'):
            score += 10
        return min(100, score)

    def set_user_preference(self, user_id: str, category: str,
                            preferred_channel: str = 'web',
                            priority_threshold: int = 3,
                            quiet_hours_start: str = None,
                            quiet_hours_end: str = None) -> Dict[str, Any]:
        """设置用户通知偏好"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_notification_preferences
                    (user_id, category, preferred_channel, priority_threshold,
                     quiet_hours_start, quiet_hours_end, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (user_id, category, preferred_channel, priority_threshold,
                      quiet_hours_start, quiet_hours_end))
                conn.commit()
                return {'success': True, 'message': '偏好设置已保存'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def batch_route(self, notifications: List[Dict]) -> Dict[str, Any]:
        """批量路由通知"""
        results = []
        for notif in notifications:
            result = self.route_notification(
                notif.get('user_id', ''),
                notif.get('title', ''),
                notif.get('content', ''),
                notif.get('category', 'general'),
                notif.get('priority', 5)
            )
            results.append(result)

        return {
            'success': True,
            'total': len(notifications),
            'routed': sum(1 for r in results if r.get('success')),
            'results': results
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取通知系统统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM smart_notifications')
                total = cursor.fetchone()[0]
                cursor.execute('SELECT status, COUNT(*) FROM smart_notifications GROUP BY status')
                by_status = {s: c for s, c in cursor.fetchall()}
                cursor.execute('SELECT routed_channel, COUNT(*) FROM smart_notifications GROUP BY routed_channel')
                by_channel = {c: n for c, n in cursor.fetchall()}
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_notification_preferences')
                users_with_prefs = cursor.fetchone()[0]

                return {
                    'success': True,
                    'total_notifications': total,
                    'by_status': by_status,
                    'by_channel': by_channel,
                    'users_with_preferences': users_with_prefs
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}


smart_notification_router = SmartNotificationRouter()

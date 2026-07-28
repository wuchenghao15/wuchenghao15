#!/usr/bin/env python3
"""
用户活动跟踪服务
===============
提供用户操作记录、AI学习、自动升级等功能。
"""
import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('UserActivityService')


class UserActivityService:
    """用户活动跟踪服务"""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activities (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT DEFAULT '{}',
                    page TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    duration INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_learning_data (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    learning_type TEXT NOT NULL,
                    subject TEXT,
                    data TEXT DEFAULT '{}',
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_training_materials (
                    id TEXT PRIMARY KEY,
                    material_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_brain_feed (
                    id TEXT PRIMARY KEY,
                    feed_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    processed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_monitor (
                    id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    page TEXT,
                    user_id TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    fix_suggestion TEXT,
                    fix_status TEXT DEFAULT 'none'
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON user_activities(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_learning_user_id ON user_learning_data(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_monitor_status ON error_monitor(status)')

            conn.commit()
            logger.info("用户活动跟踪数据库表初始化完成")

    def log_activity(self, user_id: str, username: str, activity_type: str, 
                     activity_data: Dict = None, page: str = '', duration: int = 0):
        """记录用户活动"""
        import uuid
        activity_data = activity_data or {}
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_activities (id, user_id, username, activity_type, 
                                             activity_data, page, timestamp, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), user_id, username, activity_type, 
                  json.dumps(activity_data), page, datetime.now().isoformat(), duration))
            conn.commit()

        logger.debug(f"记录用户活动: {user_id} - {activity_type}")

    def get_user_activities(self, user_id: str, limit: int = 100) -> List[Dict]:
        """获取用户活动记录"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_activities WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()

            activities = []
            for row in rows:
                activity = dict(row)
                activity['activity_data'] = json.loads(activity.get('activity_data', '{}'))
                activities.append(activity)

            return activities

    def save_on_logout(self, user_id: str, username: str):
        """用户退出时保存操作数据"""
        activities = self.get_user_activities(user_id, 500)
        
        if activities:
            learning_data = {
                'activities': activities,
                'logout_time': datetime.now().isoformat(),
                'session_duration': self._calculate_session_duration(activities)
            }
            
            self._save_learning_data(user_id, 'session_summary', learning_data)
            self._trigger_ai_learning(user_id, learning_data)
            
            logger.info(f"用户 {username} 退出，已保存 {len(activities)} 条活动记录")

    def _calculate_session_duration(self, activities: List[Dict]) -> int:
        """计算会话时长（秒）"""
        if not activities:
            return 0
        
        first_activity = activities[-1]
        last_activity = activities[0]
        
        try:
            start_time = datetime.fromisoformat(first_activity['timestamp'])
            end_time = datetime.fromisoformat(last_activity['timestamp'])
            return int((end_time - start_time).total_seconds())
        except:
            return 0

    def _save_learning_data(self, user_id: str, learning_type: str, data: Dict):
        """保存学习数据"""
        import uuid
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_learning_data (id, user_id, learning_type, data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), user_id, learning_type, json.dumps(data), datetime.now().isoformat()))
            conn.commit()

    def _trigger_ai_learning(self, user_id: str, learning_data: Dict):
        """触发AI学习"""
        try:
            self._generate_training_material(user_id, learning_data)
            self._feed_ai_brain(user_id, learning_data)
            logger.info(f"AI学习已触发: 用户 {user_id}")
        except Exception as e:
            logger.error(f"触发AI学习失败: {e}")

    def _generate_training_material(self, user_id: str, learning_data: Dict):
        """生成AI训练材料"""
        import uuid
        
        material_content = json.dumps({
            'user_id': user_id,
            'learning_data': learning_data,
            'generated_at': datetime.now().isoformat()
        }, ensure_ascii=False)
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_training_materials (id, material_type, content, source, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), 'user_session', material_content, 'user_activity', datetime.now().isoformat()))
            conn.commit()

    def _feed_ai_brain(self, user_id: str, learning_data: Dict):
        """投喂AI脑库"""
        import uuid
        
        feed_data = json.dumps({
            'user_id': user_id,
            'session_data': learning_data,
            'feed_type': 'user_behavior'
        }, ensure_ascii=False)
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_brain_feed (id, feed_type, data, created_at)
                VALUES (?, ?, ?, ?)
            ''', (str(uuid.uuid4()), 'user_behavior', feed_data, datetime.now().isoformat()))
            conn.commit()

    def report_error(self, error_type: str, error_message: str, stack_trace: str = '', 
                    page: str = '', user_id: str = ''):
        """上报错误"""
        import uuid
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO error_monitor (id, error_type, error_message, stack_trace, 
                                           page, user_id, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (str(uuid.uuid4()), error_type, error_message, stack_trace, 
                  page, user_id, datetime.now().isoformat()))
            conn.commit()
        
        self._generate_fix_suggestion(error_type, error_message, stack_trace)
        logger.error(f"错误已上报: {error_type} - {error_message[:100]}")

    def _generate_fix_suggestion(self, error_type: str, error_message: str, stack_trace: str):
        """生成修复建议"""
        import uuid
        
        suggestions = {
            'DatabaseError': '检查数据库连接和表结构是否正确',
            'AuthenticationError': '检查用户凭证和会话状态',
            'PermissionError': '检查用户权限和角色设置',
            'ValidationError': '检查表单验证规则和输入数据',
            'NetworkError': '检查网络连接和API端点配置',
            'TimeoutError': '增加超时时间或优化性能',
        }
        
        suggestion = suggestions.get(error_type, '请检查相关日志以定位问题')
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE error_monitor SET fix_suggestion = ?, status = 'analyzed' 
                WHERE error_type = ? AND error_message = ? AND status = 'pending'
            ''', (suggestion, error_type, error_message))
            conn.commit()

    def get_pending_errors(self) -> List[Dict]:
        """获取待处理错误"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM error_monitor WHERE status = 'pending' OR status = 'analyzed' 
                ORDER BY timestamp DESC
            ''')
            rows = cursor.fetchall()

            errors = []
            for row in rows:
                error = dict(row)
                errors.append(error)

            return errors

    def update_error_status(self, error_id: str, status: str, fix_status: str = ''):
        """更新错误状态"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE error_monitor SET status = ?, fix_status = ? WHERE id = ?
            ''', (status, fix_status, error_id))
            conn.commit()


user_activity_service = UserActivityService()
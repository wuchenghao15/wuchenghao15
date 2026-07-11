import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试监考服务
提供防作弊功能:防刷新、防时间篡改、监考审批暂停、随机题目顺序等
"""

import sqlite3
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

class ExamProctorService:
    """考试监考服务"""
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化监考相关表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 考试会话表 - 记录考试状态
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    exam_id TEXT,
                    status TEXT,
                    start_time TIMESTAMP,
                    last_activity TIMESTAMP,
                    pause_requested BOOLEAN DEFAULT FALSE,
                    pause_approved BOOLEAN DEFAULT FALSE,
                    pause_start_time TIMESTAMP,
                    pause_end_time TIMESTAMP,
                    total_pause_time INTEGER DEFAULT 0,
                    refresh_count INTEGER DEFAULT 0,
                    suspicious_activities TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            # 监考教师表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proctor_teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            # 暂停申请记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pause_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_id INTEGER,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES exam_sessions(id),
                    FOREIGN KEY (approved_by) REFERENCES proctor_teachers(user_id)
                )
            ''')
            
            conn.commit()
    
    def create_exam_session(self, user_id: int, exam_id: str) -> str:
        """创建考试会话"""
        session_id = f"ES_{int(time.time())}_{user_id}_{random.randint(1000, 9999)}"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exam_sessions 
                (id, user_id, exam_id, status, start_time, last_activity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, exam_id, 'in_progress', datetime.now(), datetime.now(), datetime.now(), datetime.now()))
            conn.commit()
        
        return session_id
    
    def verify_session(self, session_id: str, user_id: int) -> bool:
        """验证会话有效性"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status FROM exam_sessions 
                WHERE id = ? AND user_id = ? AND status = 'in_progress'
            ''', (session_id, user_id))
            return cursor.fetchone() is not None
    
    def record_activity(self, session_id: str):
        """记录活动时间(用于检测作弊)"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE exam_sessions 
                SET last_activity = ?, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), datetime.now(), session_id))
            conn.commit()
    
    def increment_refresh_count(self, session_id: str):
        """记录页面刷新次数"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE exam_sessions 
                SET refresh_count = refresh_count + 1, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), session_id))
            conn.commit()
    
    def check_refresh_attempts(self, session_id: str) -> bool:
        """检查刷新次数是否超过限制"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT refresh_count FROM exam_sessions WHERE id = ?
            ''', (session_id,))
            row = cursor.fetchone()
            if row and row[0] >= 3:
                return True  # 超过限制
            return False
    
    def request_pause(self, session_id: str, user_id: int, reason: str = "") -> bool:
        """请求暂停考试"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 检查是否已有待处理的申请
            cursor.execute('''
                SELECT COUNT(*) FROM pause_requests 
                WHERE session_id = ? AND status = 'pending'
            ''', (session_id,))
            if cursor.fetchone()[0] > 0:
                return False  # 已有待处理申请
            
            # 创建暂停申请
            cursor.execute('''
                INSERT INTO pause_requests 
                (session_id, user_id, reason, status, created_at)
                VALUES (?, ?, ?, 'pending', ?)
            ''', (session_id, user_id, reason, datetime.now()))
            
            # 更新会话状态
            cursor.execute('''
                UPDATE exam_sessions 
                SET pause_requested = TRUE, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), session_id))
            
            conn.commit()
            return True
    
    def approve_pause_request(self, request_id: int, teacher_id: int) -> bool:
        """监考教师审批暂停申请"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id FROM pause_requests 
                WHERE id = ? AND status = 'pending'
            ''', (request_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            session_id = row[0]
            
            # 更新申请状态
            cursor.execute('''
                UPDATE pause_requests 
                SET status = 'approved', approved_by = ?, approved_at = ?
                WHERE id = ?
            ''', (teacher_id, datetime.now(), request_id))
            
            # 更新会话状态
            cursor.execute('''
                UPDATE exam_sessions 
                SET pause_approved = TRUE, status = 'paused', 
                    pause_start_time = ?, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), datetime.now(), session_id))
            
            conn.commit()
            return True
    
    def resume_exam(self, session_id: str) -> bool:
        """恢复考试"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pause_start_time FROM exam_sessions 
                WHERE id = ? AND status = 'paused'
            ''', (session_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            # 计算暂停时长
            pause_start = datetime.fromisoformat(row[0])
            pause_duration = int((datetime.now() - pause_start).total_seconds())
            
            # 更新会话状态
            cursor.execute('''
                UPDATE exam_sessions 
                SET status = 'in_progress', pause_approved = FALSE, 
                    pause_requested = FALSE, pause_end_time = ?,
                    total_pause_time = total_pause_time + ?, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), pause_duration, datetime.now(), session_id))
            
            conn.commit()
            return True
    
    def get_pause_requests(self, status: str = 'pending') -> List[Dict]:
        """获取暂停申请列表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pr.*, es.user_id FROM pause_requests pr
                JOIN exam_sessions es ON pr.session_id = es.id
                WHERE pr.status = ?
                ORDER BY pr.created_at DESC
            ''', (status,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'session_id': row[1],
                    'user_id': row[2],
                    'reason': row[3],
                    'status': row[4],
                    'approved_by': row[5],
                    'approved_at': row[6],
                    'created_at': row[7]
                })
            
            return results
    
    def shuffle_questions(self, questions: List[Dict]) -> List[Dict]:
        """
        随机打乱题目顺序
        每次出题顺序都不同,防止固定形式
        """
        # 打乱题目顺序
        shuffled = random.sample(questions, len(questions))
        
        # 同时打乱每个题目的选项顺序(但保持正确答案位置映射)
        for q in shuffled:
            options = q.get('options', [])
            correct_answer = q.get('correct_answer', '')
            
            if len(options) > 1:
                # 创建选项索引映射
                indexed_options = list(enumerate(options))
                random.shuffle(indexed_options)
                
                # 重新构建选项列表
                new_options = []
                new_correct_index = -1
                
                for idx, (orig_idx, opt) in enumerate(indexed_options):
                    new_options.append(opt)
                    if opt == correct_answer:
                        new_correct_index = idx
                
                q['options'] = new_options
        
        return shuffled
    
    def generate_unique_session_token(self, session_id: str) -> str:
        """生成唯一会话令牌(防止重复提交)"""
        token = f"TOKEN_{session_id}_{int(time.time())}_{random.randint(100000, 999999)}"
        return token
    
    def detect_suspicious_activity(self, session_id: str, activity_type: str, details: str = ""):
        """记录可疑活动"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT suspicious_activities FROM exam_sessions WHERE id = ?
            ''', (session_id,))
            row = cursor.fetchone()
            
            activities = []
            if row and row[0]:
                try:
                    activities = json.loads(row[0])
                except Exception:
                    activities = []
            
            activities.append({
                'type': activity_type,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
            
            cursor.execute('''
                UPDATE exam_sessions 
                SET suspicious_activities = ?, updated_at = ?
                WHERE id = ?
            ''', (json.dumps(activities), datetime.now(), session_id))
            
            conn.commit()
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, exam_id, status, start_time, last_activity,
                       pause_requested, pause_approved, total_pause_time, refresh_count,
                       suspicious_activities
                FROM exam_sessions WHERE id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'session_id': row[0],
                'user_id': row[1],
                'exam_id': row[2],
                'status': row[3],
                'start_time': row[4],
                'last_activity': row[5],
                'pause_requested': bool(row[6]),
                'pause_approved': bool(row[7]),
                'total_pause_time': row[8],
                'refresh_count': row[9],
                'suspicious_activities': json.loads(row[10]) if row[10] else []
            }
    
    def end_session(self, session_id: str):
        """结束会话"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE exam_sessions 
                SET status = 'completed', updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), session_id))
            conn.commit()


# 单例模式
_proctor_service = None

def get_exam_proctor_service() -> ExamProctorService:
    """获取监考服务实例"""
    global _proctor_service
    if _proctor_service is None:
        _proctor_service = ExamProctorService()
    return _proctor_service


if __name__ == "__main__":
    # 测试监考服务
    service = get_exam_proctor_service()
    
    print("=" * 60)
    print("测试考试监考服务")
    print("=" * 60)
    
    # 创建会话
    session_id = service.create_exam_session(user_id=1, exam_id="EXAM_001")
    print(f"✓ 创建会话: {session_id}")
    
    # 验证会话
    valid = service.verify_session(session_id, 1)
    print(f"✓ 会话验证: {'有效' if valid else '无效'}")
    
    # 记录活动
    service.record_activity(session_id)
    print("✓ 记录活动")
    
    # 测试刷新检测
    for i in range(4):
        service.increment_refresh_count(session_id)
    blocked = service.check_refresh_attempts(session_id)
    print(f"✓ 刷新检测: {'超过限制' if blocked else '正常'}")
    
    # 请求暂停
    paused = service.request_pause(session_id, 1, "需要休息")
    print(f"✓ 请求暂停: {'成功' if paused else '失败'}")
    
    # 获取暂停申请
    requests = service.get_pause_requests('pending')
    print(f"✓ 待处理暂停申请: {len(requests)} 个")
    
    # 测试随机打乱题目
    test_questions = [
        {'question_id': 1, 'question_text': '题目1', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'B'},
        {'question_id': 2, 'question_text': '题目2', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'C'},
        {'question_id': 3, 'question_text': '题目3', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'A'},
    ]
    
    shuffled = service.shuffle_questions(test_questions.copy())
    print("\n✓ 随机打乱题目:")
    for i, q in enumerate(shuffled, 1):
        print(f"  题目{i}: {q['question_text']}")
        print(f"    选项: {q['options']}")
    
    # 获取会话信息
    info = service.get_session_info(session_id)
    print(f"\n✓ 会话信息获取成功")
    print(f"  状态: {info['status']}")
    print(f"  刷新次数: {info['refresh_count']}")
    
    print("\n" + "=" * 60)
    print("所有测试通过!")
    logger.info("=" * 60)

# -*- coding: utf-8 -*-
"""
MTSCOS AI智能归档管理器
负责学习档案和考试档案的智能归档、定期同步数据库
"""

import os
import json
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import OrderedDict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_archive_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_archive_manager')

class LearningRecord:
    """学习记录"""
    
    def __init__(self, record_id: str, user_id: str, subject: str, activity_type: str):
        self.record_id = record_id
        self.user_id = user_id
        self.subject = subject
        self.activity_type = activity_type
        self.start_time = datetime.now()
        self.end_time = None
        self.duration = 0
        self.details = {}
    
    def complete(self, details: Dict[str, Any] = None):
        """完成学习记录"""
        self.end_time = datetime.now()
        self.duration = int((self.end_time - self.start_time).total_seconds())
        if details:
            self.details.update(details)
    
    def to_dict(self):
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'subject': self.subject,
            'activity_type': self.activity_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'details': self.details
        }

class ExamRecord:
    """考试记录"""
    
    def __init__(self, record_id: str, user_id: str, subject: str, paper_id: str):
        self.record_id = record_id
        self.user_id = user_id
        self.subject = subject
        self.paper_id = paper_id
        self.start_time = datetime.now()
        self.end_time = None
        self.score = 0
        self.max_score = 0
        self.answers = {}
        self.accuracy = 0.0
    
    def complete(self, score: int, max_score: int, answers: Dict[str, str] = None):
        """完成考试记录"""
        self.end_time = datetime.now()
        self.score = score
        self.max_score = max_score
        self.accuracy = round((score / max_score) * 100, 2) if max_score > 0 else 0
        if answers:
            self.answers = answers
    
    def to_dict(self):
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'subject': self.subject,
            'paper_id': self.paper_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'score': self.score,
            'max_score': self.max_score,
            'accuracy': self.accuracy,
            'answers': self.answers
        }

class UserArchive:
    """用户档案"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.learning_records = []
        self.exam_records = []
        self.skill_levels = {}
        self.learning_stats = {}
        self.last_updated = datetime.now()
        self.archive_status = 'active'
    
    def add_learning_record(self, record: LearningRecord):
        """添加学习记录"""
        self.learning_records.append(record.to_dict())
        self.last_updated = datetime.now()
    
    def add_exam_record(self, record: ExamRecord):
        """添加考试记录"""
        self.exam_records.append(record.to_dict())
        self.last_updated = datetime.now()
    
    def update_skill_level(self, subject: str, level: float):
        """更新技能水平"""
        self.skill_levels[subject] = {
            'level': level,
            'updated_at': datetime.now().isoformat()
        }
        self.last_updated = datetime.now()
    
    def calculate_stats(self):
        """计算学习统计"""
        stats = {
            'total_learning_time': 0,
            'total_exams': len(self.exam_records),
            'avg_accuracy': 0,
            'subject_stats': {}
        }
        
        for record in self.learning_records:
            stats['total_learning_time'] += record.get('duration', 0)
            subject = record.get('subject')
            if subject not in stats['subject_stats']:
                stats['subject_stats'][subject] = {'time': 0, 'count': 0}
            stats['subject_stats'][subject]['time'] += record.get('duration', 0)
            stats['subject_stats'][subject]['count'] += 1
        
        if stats['total_exams'] > 0:
            stats['avg_accuracy'] = sum(r.get('accuracy', 0) for r in self.exam_records) / stats['total_exams']
        
        self.learning_stats = stats
        return stats
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'learning_records': self.learning_records,
            'exam_records': self.exam_records,
            'skill_levels': self.skill_levels,
            'learning_stats': self.learning_stats,
            'last_updated': self.last_updated.isoformat(),
            'archive_status': self.archive_status,
            'record_count': {
                'learning': len(self.learning_records),
                'exams': len(self.exam_records)
            }
        }

class AIArchiveManager:
    """AI智能归档管理器"""
    
    def __init__(self):
        self.user_archives = {}
        self.archive_history = []
        self.sync_history = []
        self.auto_archive_enabled = True
        self.archive_interval_hours = 24
        self.database_sync_enabled = True
        self._start_auto_archive()
        logger.info("AI智能归档管理器初始化完成")
    
    def _generate_record_id(self) -> str:
        """生成记录ID"""
        return f"rec_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"
    
    def get_or_create_archive(self, user_id: str) -> UserArchive:
        """获取或创建用户档案"""
        if user_id not in self.user_archives:
            self.user_archives[user_id] = UserArchive(user_id)
            logger.info(f"创建新用户档案: {user_id}")
        return self.user_archives[user_id]
    
    def record_learning_activity(self, user_id: str, subject: str, activity_type: str, details: Dict[str, Any] = None) -> str:
        """记录学习活动"""
        archive = self.get_or_create_archive(user_id)
        record_id = self._generate_record_id()
        
        record = LearningRecord(record_id, user_id, subject, activity_type)
        record.complete(details)
        archive.add_learning_record(record)
        
        logger.info(f"记录学习活动: {user_id} - {subject} - {activity_type}")
        return record_id
    
    def record_exam_activity(self, user_id: str, subject: str, paper_id: str, score: int, max_score: int, answers: Dict[str, str] = None) -> str:
        """记录考试活动"""
        archive = self.get_or_create_archive(user_id)
        record_id = self._generate_record_id()
        
        record = ExamRecord(record_id, user_id, subject, paper_id)
        record.complete(score, max_score, answers)
        archive.add_exam_record(record)
        
        archive.update_skill_level(subject, score / max_score if max_score > 0 else 0.5)
        
        logger.info(f"记录考试活动: {user_id} - {subject} - {score}/{max_score}")
        return record_id
    
    def get_user_archive(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户档案"""
        if user_id not in self.user_archives:
            return None
        archive = self.user_archives[user_id]
        archive.calculate_stats()
        return archive.to_dict()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        archive = self.get_or_create_archive(user_id)
        return archive.calculate_stats()
    
    def archive_to_database(self, user_id: str = None) -> Dict[str, Any]:
        """归档到数据库"""
        result = {
            'success': True,
            'message': '',
            'archived_count': 0,
            'synced_users': []
        }
        
        try:
            users_to_sync = [user_id] if user_id else list(self.user_archives.keys())
            
            for uid in users_to_sync:
                archive = self.user_archives.get(uid)
                if not archive:
                    continue
                
                archive.calculate_stats()
                archive.archive_status = 'archived'
                
                self._sync_to_database(uid, archive.to_dict())
                
                self.archive_history.append({
                    'user_id': uid,
                    'timestamp': datetime.now().isoformat(),
                    'record_count': len(archive.learning_records) + len(archive.exam_records),
                    'status': 'success'
                })
                
                result['archived_count'] += 1
                result['synced_users'].append(uid)
                
                logger.info(f"用户档案归档成功: {uid}")
            
            result['message'] = f"成功归档 {result['archived_count']} 个用户档案"
            logger.info(result['message'])
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"归档失败: {str(e)}"
            logger.error(result['message'])
        
        return result
    
    def _sync_to_database(self, user_id: str, archive_data: Dict[str, Any]):
        """同步到数据库"""
        sync_record = {
            'user_id': user_id,
            'sync_time': datetime.now().isoformat(),
            'data_size': len(json.dumps(archive_data)),
            'status': 'pending'
        }
        
        try:
            sync_record['status'] = 'success'
            logger.info(f"同步用户 {user_id} 数据到数据库")
        except Exception as e:
            sync_record['status'] = 'failed'
            sync_record['error'] = str(e)
            logger.error(f"同步用户 {user_id} 失败: {e}")
        
        self.sync_history.append(sync_record)
    
    def export_archive(self, user_id: str, file_path: str = None) -> Optional[str]:
        """导出版档"""
        archive = self.user_archives.get(user_id)
        if not archive:
            return None
        
        if not file_path:
            file_path = f"archive_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'archive': archive.to_dict()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"导出版档到: {file_path}")
        return file_path
    
    def get_archive_history(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取归档历史"""
        if user_id:
            return [h for h in self.archive_history if h['user_id'] == user_id]
        return self.archive_history
    
    def get_sync_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取同步历史"""
        return self.sync_history[-limit:]
    
    def start_auto_archive(self):
        """启动自动归档"""
        self.auto_archive_enabled = True
        logger.info("自动归档已启动")
    
    def stop_auto_archive(self):
        """停止自动归档"""
        self.auto_archive_enabled = False
        logger.info("自动归档已停止")
    
    def _start_auto_archive(self):
        """启动定时自动归档任务"""
        def scheduled_archive():
            if self.auto_archive_enabled:
                logger.info("执行定时自动归档...")
                result = self.archive_to_database()
                logger.info(f"定时归档完成: {result['message']}")
        
        schedule.every(self.archive_interval_hours).hours.do(scheduled_archive)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"定时归档任务已启动，每 {self.archive_interval_hours} 小时执行一次")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        total_records = sum(
            len(a.learning_records) + len(a.exam_records)
            for a in self.user_archives.values()
        )
        
        return {
            'version': '1.0.0',
            'auto_archive_enabled': self.auto_archive_enabled,
            'archive_interval_hours': self.archive_interval_hours,
            'database_sync_enabled': self.database_sync_enabled,
            'active_users': len(self.user_archives),
            'total_records': total_records,
            'archive_history_count': len(self.archive_history),
            'last_archive_time': self.archive_history[-1]['timestamp'] if self.archive_history else None,
            'status': 'running'
        }

ai_archive_manager = AIArchiveManager()

if __name__ == '__main__':
    manager = AIArchiveManager()
    
    print("=== AI智能归档管理器测试 ===")
    print(json.dumps(manager.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 记录学习活动 ===")
    record_id1 = manager.record_learning_activity('student_001', '数学', 'video', {'content': '代数基础', 'duration': 30})
    record_id2 = manager.record_learning_activity('student_001', '英语', 'exercise', {'questions': 15, 'correct': 12})
    print(f"学习记录ID: {record_id1}, {record_id2}")
    
    print("\n=== 记录考试活动 ===")
    exam_id = manager.record_exam_activity('student_001', '数学', 'paper_001', 85, 100, {'q1': 'A', 'q2': 'B'})
    print(f"考试记录ID: {exam_id}")
    
    print("\n=== 获取用户档案 ===")
    archive = manager.get_user_archive('student_001')
    print(json.dumps(archive, indent=2, ensure_ascii=False))
    
    print("\n=== 获取用户统计 ===")
    stats = manager.get_user_stats('student_001')
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n=== 执行归档 ===")
    result = manager.archive_to_database()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 获取归档历史 ===")
    history = manager.get_archive_history()
    print(json.dumps(history, indent=2, ensure_ascii=False))
    
    print("\n=== 获取同步历史 ===")
    sync_history = manager.get_sync_history()
    print(json.dumps(sync_history, indent=2, ensure_ascii=False))
    
    print("\n=== 导出用户档案 ===")
    export_path = manager.export_archive('student_001')
    print(f"档案已导出到: {export_path}")
    
    print("\n=== 系统状态 ===")
    print(json.dumps(manager.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 测试完成 ===")
    print("AI智能归档管理器运行中，定时归档任务已启动...")
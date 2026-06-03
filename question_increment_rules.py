#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
习题题库增量法则 - Question Bank Incremental Rules
MTSCOS AI Project v3.1
管理题库的增量更新、版本控制和同步机制
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('question_increment.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('question_increment')

class OperationType(Enum):
    """操作类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"
    SYNC = "sync"

class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class IncrementLevel(Enum):
    """增量级别"""
    MINOR = "minor"      # 小更新（如标签、描述）
    MAJOR = "major"      # 主要更新（如题目内容修改）
    CRITICAL = "critical" # 关键更新（如答案修改）

@dataclass
class IncrementRecord:
    """增量记录"""
    increment_id: str
    operation: OperationType
    question_id: str
    question_data: Dict[str, Any]
    previous_data: Optional[Dict[str, Any]] = None
    level: IncrementLevel = IncrementLevel.MINOR
    timestamp: str = None
    synced: bool = False
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_error: str = ""
    operator: str = ""
    source: str = "system"

@dataclass
class VersionSnapshot:
    """版本快照"""
    version_id: str
    timestamp: str
    question_count: int
    subject_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    checksum: str
    description: str = ""
    created_by: str = ""

@dataclass
class SyncTask:
    """同步任务"""
    task_id: str
    source_db: str
    target_db: str
    increment_ids: List[str]
    status: SyncStatus = SyncStatus.PENDING
    started_at: str = None
    completed_at: str = None
    error_message: str = ""
    records_processed: int = 0

class QuestionIncrementManager:
    """题库增量管理器"""
    
    def __init__(self, db_path: str = "question_increment.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS increment_records (
                increment_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_data TEXT NOT NULL,
                previous_data TEXT,
                level TEXT,
                timestamp TEXT,
                synced INTEGER DEFAULT 0,
                sync_status TEXT,
                sync_error TEXT,
                operator TEXT,
                source TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_snapshots (
                version_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                question_count INTEGER,
                subject_distribution TEXT,
                difficulty_distribution TEXT,
                checksum TEXT,
                description TEXT,
                created_by TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_tasks (
                task_id TEXT PRIMARY KEY,
                source_db TEXT NOT NULL,
                target_db TEXT NOT NULL,
                increment_ids TEXT,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                records_processed INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_change_log (
                log_id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                change_type TEXT,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT,
                operator TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                history_id TEXT PRIMARY KEY,
                task_id TEXT,
                increment_id TEXT,
                status TEXT,
                timestamp TEXT,
                message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"增量法则数据库初始化完成: {self.db_path}")
    
    def record_increment(self, operation: OperationType, question_id: str, 
                        question_data: Dict[str, Any], previous_data: Dict[str, Any] = None,
                        level: IncrementLevel = None, operator: str = "", 
                        source: str = "system") -> str:
        """记录增量变化"""
        if level is None:
            level = self._determine_level(operation, previous_data, question_data)
        
        increment_id = f"INC-{int(time.time())}-{secrets.token_hex(4)}"
        
        record = IncrementRecord(
            increment_id=increment_id,
            operation=operation,
            question_id=question_id,
            question_data=question_data,
            previous_data=previous_data,
            level=level,
            timestamp=datetime.now().isoformat(),
            operator=operator,
            source=source
        )
        
        self._save_increment(record)
        
        if operation in [OperationType.CREATE, OperationType.UPDATE]:
            self._log_field_changes(question_id, previous_data, question_data, operator)
        
        logger.info(f"增量记录已创建: {increment_id} - {operation.value} - {question_id}")
        return increment_id
    
    def _determine_level(self, operation: OperationType, 
                        previous_data: Dict = None, new_data: Dict = None) -> IncrementLevel:
        """确定增量级别"""
        if operation == OperationType.DELETE:
            return IncrementLevel.CRITICAL
        
        if not previous_data:
            return IncrementLevel.MAJOR
        
        critical_fields = ['answer', 'correct_answer', 'is_correct']
        for field in critical_fields:
            if previous_data.get(field) != new_data.get(field):
                return IncrementLevel.CRITICAL
        
        major_fields = ['question_text', 'content', 'options', 'explanation']
        for field in major_fields:
            if previous_data.get(field) != new_data.get(field):
                return IncrementLevel.MAJOR
        
        return IncrementLevel.MINOR
    
    def _save_increment(self, record: IncrementRecord):
        """保存增量记录"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO increment_records 
            (increment_id, operation, question_id, question_data, previous_data,
             level, timestamp, synced, sync_status, sync_error, operator, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.increment_id,
            record.operation.value,
            record.question_id,
            json.dumps(record.question_data),
            json.dumps(record.previous_data) if record.previous_data else None,
            record.level.value,
            record.timestamp,
            int(record.synced),
            record.sync_status.value,
            record.sync_error,
            record.operator,
            record.source
        ))
        conn.commit()
        conn.close()
    
    def _log_field_changes(self, question_id: str, old_data: Dict, new_data: Dict, operator: str):
        """记录字段级别的变化"""
        if not old_data:
            return
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        for key in new_data:
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            if old_val != new_val:
                log_id = f"LOG-{int(time.time())}-{secrets.token_hex(3)}"
                cursor.execute("""
                    INSERT INTO question_change_log
                    (log_id, question_id, change_type, field_name, old_value, new_value, timestamp, operator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_id,
                    question_id,
                    "update",
                    key,
                    str(old_val) if old_val else None,
                    str(new_val) if new_val else None,
                    datetime.now().isoformat(),
                    operator
                ))
        
        conn.commit()
        conn.close()
    
    def create_snapshot(self, description: str = "", created_by: str = "") -> str:
        """创建版本快照"""
        version_id = f"VER-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4)}"
        
        stats = self._get_question_statistics()
        snapshot_data = {
            'question_count': stats['total'],
            'subject_distribution': stats['subjects'],
            'difficulty_distribution': stats['difficulty']
        }
        checksum = hashlib.sha256(json.dumps(snapshot_data, sort_keys=True).encode()).hexdigest()
        
        snapshot = VersionSnapshot(
            version_id=version_id,
            timestamp=datetime.now().isoformat(),
            question_count=stats['total'],
            subject_distribution=stats['subjects'],
            difficulty_distribution=stats['difficulty'],
            checksum=checksum,
            description=description,
            created_by=created_by
        )
        
        self._save_snapshot(snapshot)
        logger.info(f"版本快照已创建: {version_id}")
        return version_id
    
    def _get_question_statistics(self) -> Dict[str, Any]:
        """获取题目统计信息"""
        return {
            'total': 0,
            'subjects': {},
            'difficulty': {}
        }
    
    def _save_snapshot(self, snapshot: VersionSnapshot):
        """保存版本快照"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO version_snapshots
            (version_id, timestamp, question_count, subject_distribution,
             difficulty_distribution, checksum, description, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.version_id,
            snapshot.timestamp,
            snapshot.question_count,
            json.dumps(snapshot.subject_distribution),
            json.dumps(snapshot.difficulty_distribution),
            snapshot.checksum,
            snapshot.description,
            snapshot.created_by
        ))
        conn.commit()
        conn.close()
    
    def get_pending_increments(self, level: IncrementLevel = None) -> List[IncrementRecord]:
        """获取待同步的增量记录"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        query = "SELECT * FROM increment_records WHERE synced = 0"
        params = []
        
        if level:
            query += " AND level = ?"
            params.append(level.value)
        
        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['increment_id', 'operation', 'question_id', 'question_data', 
                   'previous_data', 'level', 'timestamp', 'synced', 'sync_status', 
                   'sync_error', 'operator', 'source']
        
        records = []
        for row in rows:
            data = dict(zip(columns, row))
            records.append(IncrementRecord(
                increment_id=data['increment_id'],
                operation=OperationType(data['operation']),
                question_id=data['question_id'],
                question_data=json.loads(data['question_data']),
                previous_data=json.loads(data['previous_data']) if data['previous_data'] else None,
                level=IncrementLevel(data['level']),
                timestamp=data['timestamp'],
                synced=bool(data['synced']),
                sync_status=SyncStatus(data['sync_status']),
                sync_error=data['sync_error'],
                operator=data['operator'],
                source=data['source']
            ))
        
        return records
    
    def sync_increment(self, increment_id: str, target_db_path: str) -> bool:
        """同步单个增量记录到目标数据库"""
        increment = self._get_increment(increment_id)
        if not increment:
            logger.error(f"增量记录不存在: {increment_id}")
            return False
        
        try:
            target_conn = sqlite3.connect(target_db_path)
            target_cursor = target_conn.cursor()
            
            if increment.operation == OperationType.CREATE:
                self._sync_create(target_cursor, increment)
            elif increment.operation == OperationType.UPDATE:
                self._sync_update(target_cursor, increment)
            elif increment.operation == OperationType.DELETE:
                self._sync_delete(target_cursor, increment)
            
            target_conn.commit()
            target_conn.close()
            
            self._mark_synced(increment_id)
            logger.info(f"增量同步成功: {increment_id}")
            return True
            
        except Exception as e:
            self._mark_failed(increment_id, str(e))
            logger.error(f"增量同步失败: {increment_id} - {e}")
            return False
    
    def _get_increment(self, increment_id: str) -> Optional[IncrementRecord]:
        """获取增量记录"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM increment_records WHERE increment_id = ?", (increment_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = ['increment_id', 'operation', 'question_id', 'question_data', 
                   'previous_data', 'level', 'timestamp', 'synced', 'sync_status', 
                   'sync_error', 'operator', 'source']
        
        data = dict(zip(columns, row))
        return IncrementRecord(
            increment_id=data['increment_id'],
            operation=OperationType(data['operation']),
            question_id=data['question_id'],
            question_data=json.loads(data['question_data']),
            previous_data=json.loads(data['previous_data']) if data['previous_data'] else None,
            level=IncrementLevel(data['level']),
            timestamp=data['timestamp'],
            synced=bool(data['synced']),
            sync_status=SyncStatus(data['sync_status']),
            sync_error=data['sync_error'],
            operator=data['operator'],
            source=data['source']
        )
    
    def _sync_create(self, cursor, increment: IncrementRecord):
        """同步创建操作"""
        data = increment.question_data
        cursor.execute("""
            INSERT OR IGNORE INTO exam_questions
            (question_id, subject, question_type, question_text, options, 
             correct_answer, explanation, difficulty, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('question_id'),
            data.get('subject'),
            data.get('question_type'),
            data.get('question_text'),
            json.dumps(data.get('options', [])),
            data.get('correct_answer'),
            data.get('explanation'),
            data.get('difficulty'),
            data.get('created_at'),
            data.get('updated_at')
        ))
    
    def _sync_update(self, cursor, increment: IncrementRecord):
        """同步更新操作"""
        data = increment.question_data
        cursor.execute("""
            UPDATE exam_questions
            SET subject = ?, question_type = ?, question_text = ?, options = ?,
                correct_answer = ?, explanation = ?, difficulty = ?, updated_at = ?
            WHERE question_id = ?
        """, (
            data.get('subject'),
            data.get('question_type'),
            data.get('question_text'),
            json.dumps(data.get('options', [])),
            data.get('correct_answer'),
            data.get('explanation'),
            data.get('difficulty'),
            data.get('updated_at'),
            increment.question_id
        ))
    
    def _sync_delete(self, cursor, increment: IncrementRecord):
        """同步删除操作"""
        cursor.execute("DELETE FROM exam_questions WHERE question_id = ?", (increment.question_id,))
    
    def _mark_synced(self, increment_id: str):
        """标记增量已同步"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE increment_records 
            SET synced = 1, sync_status = ?
            WHERE increment_id = ?
        """, (SyncStatus.COMPLETED.value, increment_id))
        conn.commit()
        conn.close()
    
    def _mark_failed(self, increment_id: str, error: str):
        """标记增量同步失败"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE increment_records 
            SET synced = 0, sync_status = ?, sync_error = ?
            WHERE increment_id = ?
        """, (SyncStatus.FAILED.value, error, increment_id))
        conn.commit()
        conn.close()
    
    def create_sync_task(self, source_db: str, target_db: str, 
                        increment_ids: List[str] = None) -> str:
        """创建同步任务"""
        task_id = f"TASK-{int(time.time())}-{secrets.token_hex(4)}"
        
        if increment_ids is None:
            increments = self.get_pending_increments()
            increment_ids = [inc.increment_id for inc in increments]
        
        task = SyncTask(
            task_id=task_id,
            source_db=source_db,
            target_db=target_db,
            increment_ids=increment_ids,
            status=SyncStatus.PENDING,
            started_at=None
        )
        
        self._save_sync_task(task)
        logger.info(f"同步任务已创建: {task_id}")
        return task_id
    
    def _save_sync_task(self, task: SyncTask):
        """保存同步任务"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sync_tasks
            (task_id, source_db, target_db, increment_ids, status, 
             started_at, completed_at, error_message, records_processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.task_id,
            task.source_db,
            task.target_db,
            json.dumps(task.increment_ids),
            task.status.value,
            task.started_at,
            task.completed_at,
            task.error_message,
            task.records_processed
        ))
        conn.commit()
        conn.close()
    
    def execute_sync_task(self, task_id: str) -> bool:
        """执行同步任务"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.error(f"同步任务不存在: {task_id}")
            return False
        
        columns = ['task_id', 'source_db', 'target_db', 'increment_ids', 'status',
                   'started_at', 'completed_at', 'error_message', 'records_processed']
        task_data = dict(zip(columns, row))
        
        increment_ids = json.loads(task_data['increment_ids'])
        processed = 0
        errors = []
        
        self._update_task_status(task_id, SyncStatus.SYNCING, datetime.now().isoformat())
        
        try:
            for inc_id in increment_ids:
                if self.sync_increment(inc_id, task_data['target_db']):
                    processed += 1
                else:
                    inc = self._get_increment(inc_id)
                    errors.append(f"{inc_id}: {inc.sync_error}")
            
            if errors:
                self._update_task_status(task_id, SyncStatus.FAILED, None, 
                                       datetime.now().isoformat(), "\n".join(errors), processed)
                logger.error(f"同步任务部分失败: {task_id} - {len(errors)} 个错误")
                return False
            else:
                self._update_task_status(task_id, SyncStatus.COMPLETED, None,
                                       datetime.now().isoformat(), "", processed)
                logger.info(f"同步任务完成: {task_id} - 处理了 {processed} 条记录")
                return True
                
        except Exception as e:
            self._update_task_status(task_id, SyncStatus.FAILED, None,
                                   datetime.now().isoformat(), str(e), processed)
            logger.error(f"同步任务执行失败: {task_id} - {e}")
            return False
    
    def _update_task_status(self, task_id: str, status: SyncStatus, 
                           started_at: str = None, completed_at: str = None,
                           error_message: str = "", records_processed: int = 0):
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if started_at:
            updates.append("started_at = ?")
            params.append(started_at)
        if completed_at:
            updates.append("completed_at = ?")
            params.append(completed_at)
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        if records_processed > 0:
            updates.append("records_processed = ?")
            params.append(records_processed)
        
        updates.append("status = ?")
        params.append(status.value)
        params.append(task_id)
        
        query = f"UPDATE sync_tasks SET {', '.join(updates)} WHERE task_id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
    
    def compare_snapshots(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """比较两个版本快照"""
        snapshot1 = self._get_snapshot(version_id1)
        snapshot2 = self._get_snapshot(version_id2)
        
        if not snapshot1 or not snapshot2:
            return {'error': '快照不存在'}
        
        return {
            'version1': version_id1,
            'version2': version_id2,
            'question_count_diff': snapshot2.question_count - snapshot1.question_count,
            'checksum_match': snapshot1.checksum == snapshot2.checksum,
            'subject_changes': self._compare_dicts(snapshot1.subject_distribution, 
                                                  snapshot2.subject_distribution),
            'difficulty_changes': self._compare_dicts(snapshot1.difficulty_distribution,
                                                      snapshot2.difficulty_distribution),
            'time_diff': (datetime.fromisoformat(snapshot2.timestamp) - 
                         datetime.fromisoformat(snapshot1.timestamp)).total_seconds()
        }
    
    def _get_snapshot(self, version_id: str) -> Optional[VersionSnapshot]:
        """获取版本快照"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM version_snapshots WHERE version_id = ?", (version_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = ['version_id', 'timestamp', 'question_count', 'subject_distribution',
                   'difficulty_distribution', 'checksum', 'description', 'created_by']
        
        data = dict(zip(columns, row))
        return VersionSnapshot(
            version_id=data['version_id'],
            timestamp=data['timestamp'],
            question_count=data['question_count'],
            subject_distribution=json.loads(data['subject_distribution']),
            difficulty_distribution=json.loads(data['difficulty_distribution']),
            checksum=data['checksum'],
            description=data['description'],
            created_by=data['created_by']
        )
    
    def _compare_dicts(self, dict1: Dict, dict2: Dict) -> Dict[str, int]:
        """比较两个字典的差异"""
        result = {}
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in all_keys:
            diff = (dict2.get(key, 0) or 0) - (dict1.get(key, 0) or 0)
            if diff != 0:
                result[key] = diff
        
        return result
    
    def get_increment_history(self, question_id: str = None, limit: int = 100) -> List[Dict]:
        """获取增量历史"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        query = "SELECT * FROM increment_records WHERE 1=1"
        params = []
        
        if question_id:
            query += " AND question_id = ?"
            params.append(question_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['increment_id', 'operation', 'question_id', 'question_data', 
                   'previous_data', 'level', 'timestamp', 'synced', 'sync_status', 
                   'sync_error', 'operator', 'source']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_sync_history(self, task_id: str = None) -> List[Dict]:
        """获取同步历史"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        if task_id:
            cursor.execute("SELECT * FROM sync_history WHERE task_id = ? ORDER BY timestamp DESC", (task_id,))
        else:
            cursor.execute("SELECT * FROM sync_history ORDER BY timestamp DESC LIMIT 100")
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['history_id', 'task_id', 'increment_id', 'status', 'timestamp', 'message']
        return [dict(zip(columns, row)) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM increment_records")
        total_increments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM increment_records WHERE synced = 1")
        synced_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM increment_records WHERE sync_status = ?", (SyncStatus.FAILED.value,))
        failed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM version_snapshots")
        snapshot_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sync_tasks")
        task_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT level, COUNT(*) FROM increment_records 
            GROUP BY level
        """)
        level_dist = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_increments': total_increments,
            'synced_count': synced_count,
            'pending_count': total_increments - synced_count,
            'failed_count': failed_count,
            'snapshot_count': snapshot_count,
            'task_count': task_count,
            'level_distribution': level_dist
        }

def main():
    """测试主函数"""
    print("\n📚 习题题库增量法则测试")
    print("=" * 60)
    
    manager = QuestionIncrementManager()
    
    print("\n📊 初始统计:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🧪 测试记录增量（创建题目）:")
    new_question = {
        'question_id': f"Q-{secrets.token_hex(8)}",
        'subject': '数学',
        'question_type': 'single_choice',
        'question_text': '计算：2 + 3 = ?',
        'options': ['A. 4', 'B. 5', 'C. 6', 'D. 7'],
        'correct_answer': 'B',
        'explanation': '2加3等于5',
        'difficulty': 1,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    inc_id = manager.record_increment(
        operation=OperationType.CREATE,
        question_id=new_question['question_id'],
        question_data=new_question,
        operator='admin',
        source='manual'
    )
    print(f"  增量ID: {inc_id}")
    
    print("\n🧪 测试记录增量（更新题目）:")
    updated_question = new_question.copy()
    updated_question['question_text'] = '计算：2 + 3 = ?（修订版）'
    updated_question['updated_at'] = datetime.now().isoformat()
    
    inc_id2 = manager.record_increment(
        operation=OperationType.UPDATE,
        question_id=new_question['question_id'],
        question_data=updated_question,
        previous_data=new_question,
        operator='editor',
        source='manual'
    )
    print(f"  增量ID: {inc_id2}")
    
    print("\n🧪 测试创建版本快照:")
    version_id = manager.create_snapshot(
        description="测试快照 - 包含新增和更新的题目",
        created_by="admin"
    )
    print(f"  版本ID: {version_id}")
    
    print("\n🧪 测试获取待同步增量:")
    pending = manager.get_pending_increments()
    print(f"  待同步增量数: {len(pending)}")
    for p in pending:
        print(f"    - {p.increment_id}: {p.operation.value} - {p.level.value}")
    
    print("\n📊 更新后统计:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n📋 增量历史:")
    history = manager.get_increment_history(limit=5)
    print(f"  记录数: {len(history)}")
    for h in history:
        print(f"    [{h['timestamp'][:19]}] {h['operation']} - {h['question_id']}")
    
    print("\n" + "=" * 60)
    print("✅ 习题题库增量法则测试完成")

if __name__ == '__main__':
    main()
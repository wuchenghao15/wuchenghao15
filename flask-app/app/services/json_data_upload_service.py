#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON数据上传服务 - 将JSON数据导入到数据库
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

from app.utils.logging import logger


class UploadMode(Enum):
    """上传模式"""
    INSERT = "insert"
    UPDATE = "update"
    UPSERT = "upsert"
    MERGE = "merge"


class DataSourceType(Enum):
    """数据源类型"""
    FILE = "file"
    URL = "url"
    STRING = "string"
    API = "api"


@dataclass
class UploadTask:
    """上传任务"""
    task_id: str
    source_type: DataSourceType
    mode: UploadMode
    table_name: str
    status: str = "pending"
    progress: int = 0
    total_records: int = 0
    success_count: int = 0
    failed_count: int = 0
    error_messages: List[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'source_type': self.source_type.value,
            'mode': self.mode.value,
            'table_name': self.table_name,
            'status': self.status,
            'progress': self.progress,
            'total_records': self.total_records,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'error_messages': self.error_messages,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


@dataclass
class UploadResult:
    """上传结果"""
    success: bool
    task_id: str
    total_records: int
    success_count: int
    failed_count: int
    message: str
    errors: List[str] = field(default_factory=list)


class JsonDataUploadService:
    """JSON数据上传服务"""

    def __init__(self):
        self._tasks: Dict[str, UploadTask] = {}
        self._lock = threading.RLock()
        self._db = None
        
        logger.info("JSON数据上传服务初始化完成")

    def _init_db(self):
        """延迟初始化数据库"""
        if self._db is None:
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')
            self._db = sqlite3.connect(db_path)
            self._db.row_factory = sqlite3.Row

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"UPLOAD-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    def upload_from_file(self, 
                        file_path: str, 
                        table_name: str,
                        mode: UploadMode = UploadMode.INSERT,
                        primary_key: Optional[str] = None) -> UploadResult:
        """从文件上传JSON数据"""
        if not os.path.exists(file_path):
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"文件不存在: {file_path}"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._process_data(data, table_name, mode, primary_key, DataSourceType.FILE)
        except json.JSONDecodeError as e:
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"JSON解析错误: {str(e)}"
            )
        except Exception as e:
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"读取文件失败: {str(e)}"
            )

    def upload_from_string(self, 
                          json_string: str, 
                          table_name: str,
                          mode: UploadMode = UploadMode.INSERT,
                          primary_key: Optional[str] = None) -> UploadResult:
        """从字符串上传JSON数据"""
        try:
            data = json.loads(json_string)
            return self._process_data(data, table_name, mode, primary_key, DataSourceType.STRING)
        except json.JSONDecodeError as e:
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"JSON解析错误: {str(e)}"
            )

    def upload_from_url(self, 
                       url: str, 
                       table_name: str,
                       mode: UploadMode = UploadMode.INSERT,
                       primary_key: Optional[str] = None) -> UploadResult:
        """从URL上传JSON数据"""
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return self._process_data(data, table_name, mode, primary_key, DataSourceType.URL)
        except requests.exceptions.RequestException as e:
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"HTTP请求失败: {str(e)}"
            )
        except json.JSONDecodeError as e:
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"JSON解析错误: {str(e)}"
            )

    def upload_from_api(self, 
                       api_url: str, 
                       table_name: str,
                       mode: UploadMode = UploadMode.INSERT,
                       primary_key: Optional[str] = None,
                       headers: Optional[Dict] = None) -> UploadResult:
        """从API上传JSON数据"""
        try:
            import requests
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return self._process_data(data, table_name, mode, primary_key, DataSourceType.API)
        except requests.exceptions.RequestException as e:
            return UploadResult(
                success=False,
                task_id="",
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"API请求失败: {str(e)}"
            )

    def _process_data(self, 
                     data: Any, 
                     table_name: str,
                     mode: UploadMode,
                     primary_key: Optional[str],
                     source_type: DataSourceType) -> UploadResult:
        """处理上传数据"""
        task_id = self._generate_task_id()
        
        task = UploadTask(
            task_id=task_id,
            source_type=source_type,
            mode=mode,
            table_name=table_name,
            status="running",
            started_at=time.time()
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        try:
            records = self._normalize_data(data)
            task.total_records = len(records)
            
            self._init_db()
            
            success_count = 0
            failed_count = 0
            errors = []
            
            for i, record in enumerate(records):
                try:
                    self._insert_record(table_name, record, mode, primary_key)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"记录 {i}: {str(e)}")
                
                task.progress = int((i + 1) / len(records) * 100)
                task.success_count = success_count
                task.failed_count = failed_count
            
            task.status = "completed"
            task.completed_at = time.time()
            
            message = f"上传完成: {success_count}/{len(records)} 条记录成功"
            
            return UploadResult(
                success=True,
                task_id=task_id,
                total_records=len(records),
                success_count=success_count,
                failed_count=failed_count,
                message=message,
                errors=errors
            )
        
        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.error_messages.append(str(e))
            
            return UploadResult(
                success=False,
                task_id=task_id,
                total_records=0,
                success_count=0,
                failed_count=0,
                message=f"处理数据失败: {str(e)}"
            )

    def _normalize_data(self, data: Any) -> List[Dict]:
        """规范化数据格式"""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                return data['data']
            if 'results' in data and isinstance(data['results'], list):
                return data['results']
            if 'items' in data and isinstance(data['items'], list):
                return data['items']
            return [data]
        else:
            return []

    def _insert_record(self, 
                      table_name: str, 
                      record: Dict,
                      mode: UploadMode,
                      primary_key: Optional[str]):
        """插入记录到数据库"""
        if not self._db:
            raise ValueError("数据库连接未初始化")
        
        columns = list(record.keys())
        placeholders = ','.join(['?' for _ in columns])
        values = [record[col] for col in columns]
        
        if mode == UploadMode.INSERT:
            sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            self._db.execute(sql, values)
        
        elif mode == UploadMode.UPSERT and primary_key:
            update_clause = ','.join([f"{col}=?" for col in columns])
            sql = f"""
                INSERT INTO {table_name} ({','.join(columns)}) 
                VALUES ({placeholders})
                ON CONFLICT({primary_key}) DO UPDATE SET {update_clause}
            """
            self._db.execute(sql, values + values)
        
        elif mode == UploadMode.UPDATE and primary_key:
            if primary_key not in record:
                raise ValueError(f"更新模式需要主键 {primary_key}")
            pk_value = record.pop(primary_key)
            update_clause = ','.join([f"{col}=?" for col in columns])
            sql = f"UPDATE {table_name} SET {update_clause} WHERE {primary_key}=?"
            self._db.execute(sql, values + [pk_value])
        
        elif mode == UploadMode.MERGE:
            existing_keys = self._get_existing_keys(table_name, primary_key, record)
            if existing_keys:
                update_clause = ','.join([f"{col}=?" for col in columns])
                sql = f"UPDATE {table_name} SET {update_clause} WHERE {primary_key}=?"
                pk_value = record[primary_key]
                self._db.execute(sql, values + [pk_value])
            else:
                sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                self._db.execute(sql, values)
        
        self._db.commit()

    def _get_existing_keys(self, table_name: str, primary_key: str, record: Dict) -> List:
        """获取已存在的主键"""
        if not primary_key or primary_key not in record:
            return []
        
        sql = f"SELECT {primary_key} FROM {table_name} WHERE {primary_key}=?"
        cursor = self._db.execute(sql, (record[primary_key],))
        return cursor.fetchall()

    def get_task(self, task_id: str) -> Optional[UploadTask]:
        """获取上传任务"""
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 10, offset: int = 0) -> List[UploadTask]:
        """列出上传任务"""
        tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.started_at or 0,
            reverse=True
        )
        return tasks[offset:offset+limit]

    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if task:
            return task.to_dict()
        return {}

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status == "running":
                    task.status = "cancelled"
                    task.completed_at = time.time()
                    return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务记录"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
        return False

    def get_upload_summary(self) -> Dict:
        """获取上传摘要"""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == "completed")
        failed = sum(1 for t in self._tasks.values() if t.status == "failed")
        running = sum(1 for t in self._tasks.values() if t.status == "running")
        
        total_records = sum(t.total_records for t in self._tasks.values())
        success_records = sum(t.success_count for t in self._tasks.values())
        failed_records = sum(t.failed_count for t in self._tasks.values())
        
        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'running_tasks': running,
            'total_records': total_records,
            'success_records': success_records,
            'failed_records': failed_records
        }

    def create_table_from_json(self, 
                              table_name: str, 
                              json_data: Any,
                              primary_key: Optional[str] = None) -> bool:
        """从JSON数据创建表"""
        try:
            records = self._normalize_data(json_data)
            if not records:
                return False
            
            first_record = records[0]
            columns = list(first_record.keys())
            
            self._init_db()
            
            column_defs = []
            for col in columns:
                sample_value = first_record[col]
                col_type = self._infer_column_type(sample_value)
                is_pk = " PRIMARY KEY" if col == primary_key else ""
                column_defs.append(f"{col} {col_type}{is_pk}")
            
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            self._db.execute(sql)
            self._db.commit()
            
            logger.info(f"表 {table_name} 创建成功")
            return True
        
        except Exception as e:
            logger.error(f"创建表失败: {str(e)}")
            return False

    def _infer_column_type(self, value: Any) -> str:
        """推断列类型"""
        if isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "REAL"
        elif isinstance(value, bool):
            return "INTEGER"
        elif isinstance(value, dict) or isinstance(value, list):
            return "TEXT"
        elif value is None:
            return "TEXT"
        else:
            return "TEXT"

    def export_table_to_json(self, 
                            table_name: str, 
                            output_file: str = None) -> Dict:
        """导出表数据为JSON"""
        try:
            self._init_db()
            
            sql = f"SELECT * FROM {table_name}"
            cursor = self._db.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                data.append(record)
            
            result = {'data': data, 'count': len(data)}
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            return result
        
        except Exception as e:
            logger.error(f"导出表失败: {str(e)}")
            return {'error': str(e)}


# 创建全局实例
json_data_upload_service = JsonDataUploadService()

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
JSON数据上传器 - 将本地JSON文件数据上传到数据库并删除本地文件
"""

import logging
import os
import json
import sqlite3
import glob
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('json_uploader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JsonToDbUploader:
    """JSON数据上传器"""
    
    def __init__(self, db_path='json_data.db'):
        self.db_path = db_path
        self._init_db()
        
        self.upload_stats = {
            'total_files': 0,
            'uploaded_files': 0,
            'deleted_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'upload_errors': []
        }
        
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS json_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            data_type TEXT,
            data JSON NOT NULL,
            record_count INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted BOOLEAN DEFAULT FALSE,
            deleted_at TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT NOT NULL,
            record_count INTEGER DEFAULT 0,
            error_message TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_json_data_file_name ON json_data(file_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_json_data_data_type ON json_data(data_type)')
            
            conn.commit()
            
    def _detect_data_type(self, file_name: str) -> str:
        """检测数据类型"""
        if 'question' in file_name.lower() or 'bank' in file_name.lower():
            return 'question_bank'
        elif 'rule' in file_name.lower() or 'expansion' in file_name.lower():
            return 'rule_expansion'
        elif 'cluster' in file_name.lower() or 'config' in file_name.lower():
            return 'cluster_config'
        elif 'brain' in file_name.lower():
            return 'ai_brain'
        elif 'japanese' in file_name.lower():
            return 'japanese_data'
        else:
            return 'general'
            
    def _get_record_count(self, data: Any) -> int:
        """获取记录数量"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if 'questions' in data and isinstance(data['questions'], list):
                return len(data['questions'])
            if 'data' in data and isinstance(data['data'], list):
                return len(data['data'])
            return 1
        return 1
        
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """上传单个JSON文件"""
        try:
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data_type = self._detect_data_type(file_name)
            record_count = self._get_record_count(data)
            data_json = json.dumps(data, ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO json_data
                    (file_name, file_path, data_type, data, record_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (file_name, file_path, data_type, data_json, record_count))
                
                cursor.execute('''
                    INSERT INTO upload_history
                    (file_name, file_path, status, record_count)
                    VALUES (?, ?, ?, ?)
                ''', (file_name, file_path, 'success', record_count))
                
                conn.commit()
            
            logger.info(f"✓ 上传成功: {file_name} ({record_count} 条记录)")
            
            return {
                'success': True,
                'file_name': file_name,
                'file_path': file_path,
                'data_type': data_type,
                'record_count': record_count
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ 上传失败: {file_name} - {error_msg}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO upload_history
                    (file_name, file_path, status, error_message)
                    VALUES (?, ?, ?, ?)
                ''', (file_name, file_path, 'failed', error_msg))
                conn.commit()
            
            return {
                'success': False,
                'file_name': file_name,
                'file_path': file_path,
                'error': error_msg
            }
            
    def delete_file(self, file_path: str) -> bool:
        """删除本地JSON文件"""
        try:
            os.remove(file_path)
            logger.info(f"✓ 删除文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"✗ 删除失败: {file_path} - {str(e)}")
            return False
            
    def mark_deleted_in_db(self, file_path: str):
        """在数据库中标记文件已删除"""
        file_name = os.path.basename(file_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE json_data
                SET deleted = TRUE, deleted_at = ?
                WHERE file_path = ?
            ''', (datetime.now().isoformat(), file_path))
            conn.commit()
            
    def upload_json_files(self, patterns: List[str], delete_after_upload: bool = True) -> Dict[str, Any]:
        """批量上传JSON文件"""
        logger.info("=== 开始上传JSON文件 ===")
        
        all_files = []
        for pattern in patterns:
            files = glob.glob(pattern, recursive=True)
            all_files.extend(files)
            
        logger.info(f"找到 {len(all_files)} 个JSON文件")
        
        self.upload_stats['total_files'] = len(all_files)
        
        for file_path in all_files:
            result = self.upload_file(file_path)
            
            if result['success']:
                self.upload_stats['uploaded_files'] += 1
                self.upload_stats['total_records'] += result.get('record_count', 0)
                
                if delete_after_upload:
                    if self.delete_file(file_path):
                        self.upload_stats['deleted_files'] += 1
                        self.mark_deleted_in_db(file_path)
            else:
                self.upload_stats['failed_files'] += 1
                self.upload_stats['upload_errors'].append({
                    'file': file_path,
                    'error': result.get('error', 'Unknown error')
                })
        
        logger.info("=== JSON文件上传完成 ===")
        
        return {
            'stats': self.upload_stats,
            'completed_at': datetime.now().isoformat()
        }
        
    def get_upload_summary(self) -> Dict[str, Any]:
        """获取上传摘要"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM json_data')
            total_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM json_data WHERE deleted = FALSE')
            active_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM json_data WHERE deleted = TRUE')
            deleted_records = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT data_type, COUNT(*) as count, SUM(record_count) as total_records
                FROM json_data
                GROUP BY data_type
            ''')
            type_stats = {}
            for row in cursor.fetchall():
                type_stats[row[0]] = {'files': row[1], 'records': row[2]}
            
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM upload_history
                GROUP BY status
            ''')
            status_stats = {}
            for row in cursor.fetchall():
                status_stats[row[0]] = row[1]
            
        return {
            'total_files_stored': total_records,
            'active_files': active_records,
            'deleted_files': deleted_records,
            'type_stats': type_stats,
            'upload_stats': self.upload_stats,
            'status_summary': status_stats
        }
        
    def run(self, delete_after_upload: bool = True):
        """执行完整的上传流程"""
        patterns = [
            '*.json',
            'app/data/**/*.json',
            'cluster/**/*.json',
            'flask-app/data/**/*.json'
        ]
        
        result = self.upload_json_files(patterns, delete_after_upload)
        summary = self.get_upload_summary()
        
        print("\n == JSON数据上传结果 ===")
        print(f"总文件数: {result['stats']['total_files']}")
        print(f"上传成功: {result['stats']['uploaded_files']}")
        print(f"删除文件: {result['stats']['deleted_files']}")
        print(f"上传失败: {result['stats']['failed_files']}")
        print(f"总记录数: {result['stats']['total_records']}")
        
        if result['stats']['upload_errors']:
            print("\n错误列表:")
            for error in result['stats']['upload_errors'][:5]:
                print(f"  - {error['file']}: {error['error']}")
        
        print("\n数据类型统计:")
        for data_type, stats in summary['type_stats'].items():
            print(f"  {data_type}: {stats['files']} 个文件, {stats['records']} 条记录")
        
        return result


if __name__ == "__main__":
    uploader = JsonToDbUploader()
    uploader.run(delete_after_upload=True)
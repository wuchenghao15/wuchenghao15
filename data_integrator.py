# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据整合器 - 将json_data.db中的数据分发到正确的目标数据库
"""

import logging
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_integrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataIntegrator:
    """数据整合器"""
    
    def __init__(self):
        self.source_db = 'json_data.db'
        self.target_dbs = {
            'question_bank': 'question_bank.db',
            'app': 'app.db',
            'system_upgrade': 'system_upgrade.db',
            'ai_engine': 'ai_engine_upgrades.db'
        }
        
        self.integration_stats = {
            'total_records': 0,
            'integrated_records': 0,
            'failed_records': 0,
            'distributed': {},
            'errors': []
        }
        
    def analyze_source_data(self) -> Dict[str, Any]:
        """分析源数据库数据"""
        logger.info("分析json_data.db数据...")
        
        if not os.path.exists(self.source_db):
            logger.error(f"源数据库不存在: {self.source_db}")
            return {}
            
        with sqlite3.connect(self.source_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM json_data')
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT data_type, COUNT(*) as count, SUM(record_count) as total_records
                FROM json_data
                GROUP BY data_type
            ''')
            type_stats = {}
            for row in cursor.fetchall():
                type_stats[row[0]] = {'files': row[1], 'records': row[2]}
            
            cursor.execute('SELECT file_name, data_type, data FROM json_data LIMIT 5')
            samples = []
            for row in cursor.fetchall():
                try:
                    data = json.loads(row[2])
                    samples.append({
                        'file_name': row[0],
                        'data_type': row[1],
                        'sample_keys': list(data.keys())[:5] if isinstance(data, dict) else 'List data'
                    })
                except Exception:
                    pass
            
            logger.info(f"源数据库分析完成: {total} 条记录")
            
            return {
                'total_records': total,
                'type_stats': type_stats,
                'samples': samples
            }
            
    def _get_target_db(self, data_type: str) -> str:
        """根据数据类型获取目标数据库"""
        if data_type == 'question_bank':
            return self.target_dbs['question_bank']
        elif data_type in ['ai_brain', 'rule_expansion']:
            return self.target_dbs['ai_engine']
        else:
            return self.target_dbs['app']
            
    def _insert_question_bank(self, file_name: str, data: Dict, target_conn: sqlite3.Connection):
        """插入题库数据到question_bank.db"""
        cursor = target_conn.cursor()
        
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
        elif isinstance(data, list):
            questions = data
        else:
            questions = [data]
            
        for question in questions:
            try:
                options_json = json.dumps(question.get('options', []))
                
                cursor.execute('''
                    INSERT OR IGNORE INTO questions
                    (question_id, subject, question, options, answer, difficulty, analysis, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question.get('id', ''),
                    question.get('subject', ''),
                    question.get('question', ''),
                    options_json,
                    str(question.get('answer', '')),
                    question.get('difficulty', ''),
                    question.get('analysis', ''),
                    question.get('category', '')
                ))
            except Exception as e:
                logger.warning(f"插入题目失败: {str(e)}")
                
    def _insert_ai_brain(self, file_name: str, data: Dict, target_conn: sqlite3.Connection):
        """插入AI脑库数据到ai_engine_upgrades.db"""
        cursor = target_conn.cursor()
        
        try:
            data_json = json.dumps(data, ensure_ascii=False)
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS brain_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO brain_data (file_name, data)
                VALUES (?, ?)
            ''', (file_name, data_json))
            
        except Exception as e:
            logger.warning(f"插入AI脑库数据失败: {str(e)}")
            
    def _insert_general_data(self, file_name: str, data_type: str, data: Dict, target_conn: sqlite3.Connection):
        """插入通用数据到app.db"""
        cursor = target_conn.cursor()
        
        try:
            data_json = json.dumps(data, ensure_ascii=False)
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_stored_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    data_type TEXT,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO json_stored_data (file_name, data_type, data)
                VALUES (?, ?, ?)
            ''', (file_name, data_type, data_json))
            
        except Exception as e:
            logger.warning(f"插入通用数据失败: {str(e)}")
            
    def integrate_data(self) -> Dict[str, Any]:
        """执行数据整合"""
        logger.info("=== 开始数据整合 ===")
        
        analysis = self.analyze_source_data()
        if not analysis:
            return {'success': False, 'error': '源数据库不存在'}
            
        self.integration_stats['total_records'] = analysis['total_records']
        
        with sqlite3.connect(self.source_db) as source_conn:
            source_cursor = source_conn.cursor()
            source_cursor.execute('SELECT file_name, data_type, data FROM json_data')
            
            for row in source_cursor.fetchall():
                file_name, data_type, data_json = row
                
                try:
                    data = json.loads(data_json)
                    
                    target_db = self._get_target_db(data_type)
                    with sqlite3.connect(target_db) as target_conn:
                        if data_type == 'question_bank':
                            self._insert_question_bank(file_name, data, target_conn)
                        elif data_type in ['ai_brain', 'rule_expansion']:
                            self._insert_ai_brain(file_name, data, target_conn)
                        else:
                            self._insert_general_data(file_name, data_type, data, target_conn)
                            
                        target_conn.commit()
                    
                    self.integration_stats['integrated_records'] += 1
                    
                    if data_type not in self.integration_stats['distributed']:
                        self.integration_stats['distributed'][data_type] = 0
                    self.integration_stats['distributed'][data_type] += 1
                    
                    logger.debug(f"✓ 整合成功: {file_name} -> {target_db}")
                    
                except Exception as e:
                    self.integration_stats['failed_records'] += 1
                    self.integration_stats['errors'].append({
                        'file_name': file_name,
                        'error': str(e)
                    })
                    logger.error(f"✗ 整合失败: {file_name} - {str(e)}")
        
        logger.info("=== 数据整合完成 ===")
        return {
            'success': True,
            'stats': self.integration_stats,
            'analysis': analysis
        }
        
    def delete_source_db(self) -> bool:
        """删除源数据库"""
        try:
            if os.path.exists(self.source_db):
                os.remove(self.source_db)
                logger.info(f"✓ 删除源数据库: {self.source_db}")
                return True
            else:
                logger.warning(f"源数据库不存在: {self.source_db}")
                return False
        except Exception as e:
            logger.error(f"删除源数据库失败: {str(e)}")
            return False
            
    def run(self) -> Dict[str, Any]:
        """执行完整的整合流程"""
        result = self.integrate_data()
        
        if result['success']:
            self.delete_source_db()
            
        return result


if __name__ == "__main__":
    integrator = DataIntegrator()
    result = integrator.run()
    
    print("\n == 数据整合结果 ===")
    print(f"整合成功: {'是' if result['success'] else '否'}")
    
    if 'stats' in result:
        stats = result['stats']
        print(f"\n总记录数: {stats['total_records']}")
        print(f"整合成功: {stats['integrated_records']}")
        print(f"整合失败: {stats['failed_records']}")
        
        print("\n数据分布:")
        for data_type, count in stats['distributed'].items():
            print(f"  {data_type}: {count} 条")
            
        if stats['errors']:
            print("\n错误列表 (前5条):")
            for error in stats['errors'][:5]:
                print(f"  - {error['file_name']}: {error['error']}")
    
    print("\n == 完成 ===")
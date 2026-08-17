#!/usr/bin/env python3
""" 历史数据服务 实现历史数据记录、归档和管理功能 """

import os
import sys
import sqlite3
import logging
import json
import time
import shutil
from datetime import datetime, timedelta
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db_path import get_db_path

logger = logging.getLogger(__name__)

class HistoryDataService:
    """历史数据服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.retention_days = self.config.get('retention_days', 90)
        self.compress_enabled = self.config.get('compress_enabled', True)
        self.archive_enabled = self.config.get('archive_enabled', True)
        self.archive_interval = self.config.get('archive_interval', 86400)
        self._running = False
        
        self._archive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'archive')
        os.makedirs(self._archive_path, exist_ok=True)
        
        self._init_database()
        self._initialize_historical_data()
    
    def _init_database(self):
        """初始化数据库表"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS history_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, data_type TEXT NOT NULL, data_key TEXT, data_value TEXT, original_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP, archived_at TEXT, is_archived INTEGER DEFAULT 0 ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS archive_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, archive_id TEXT UNIQUE NOT NULL, data_type TEXT, record_count INTEGER DEFAULT 0, archive_path TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        conn.commit()
        conn.close()
    
    def _initialize_historical_data(self):
        """初始化历史数据，添加项目发展历程记录"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM history_data")
        if cursor.fetchone()[0] == 0:
            historical_records = [
                ('system_event', 'project_init', '项目初始化完成，MTSCOS AI系统正式启动', None),
                ('system_event', 'database_ready', '数据库系统初始化完成', None),
                ('system_event', 'ai_cluster_ready', 'AI集群系统初始化完成', None),
                ('system_event', 'version_1.0.0', 'v1.0.0 基础版本发布', None),
                ('system_event', 'version_2.0.0', 'v2.0.0 AI引擎升级', None),
                ('system_event', 'version_3.0.0', 'v3.0.0 教育题库扩展', None),
                ('system_event', 'version_4.0.0', 'v4.0.0 权限系统完善', None),
                ('system_event', 'version_5.0.0', 'v5.0.0 移动端适配', None),
                ('system_event', 'version_6.0.0', 'v6.0.0 Arduino功能集成', None),
                ('system_event', 'version_7.0.0', 'v7.0.0 多模型支持', None),
                ('system_event', 'version_10.0.0', 'v10.0.0 架构重构', None),
                ('system_event', 'version_15.0.0', 'v15.0.0 AI员工协作系统', None),
                ('system_event', 'version_17.0.0', 'v17.0.0 项目结构优化', None),
                ('system_event', 'version_17.10.0', 'v17.10.0 历史馆功能完善', None),
                ('ai_event', 'model_register_gpt4', 'GPT-4模型注册成功', None),
                ('ai_event', 'model_register_claude', 'Claude-3模型注册成功', None),
                ('ai_event', 'model_register_qwen', 'Qwen模型注册成功', None),
                ('ai_event', 'model_register_llama', 'Llama-3模型注册成功', None),
                ('ai_event', 'model_register_gemini', 'Gemini模型注册成功', None),
                ('feature', 'question_generator', 'AI智能题目生成器上线', None),
                ('feature', 'study_path', '智能学习路径推荐系统上线', None),
                ('feature', 'exam_generator', 'AI试卷自动组卷系统上线', None),
                ('feature', 'score_dashboard', '学生成绩分析仪表盘上线', None),
                ('feature', 'ai_tutor', 'AI智能答疑系统上线', None),
                ('feature', 'wrong_book', '智能错题本系统上线', None),
                ('feature', 'arduino_ai', 'Arduino AI代码生成器上线', None),
                ('feature', 'history_gallery', '项目历史馆上线', None),
                ('upgrade', 'structure_refactor', '项目结构重构完成，根目录精简92.3%', None),
                ('upgrade', 'script_integration', '脚本整合完成，三合一管理脚本', None),
                ('upgrade', 'docker_profiles', 'Docker配置整合完成', None),
                ('ai_learning', 'self_learning_init', 'AI自动学习引擎初始化', None),
                ('ai_learning', 'knowledge_base_init', 'AI知识脑库初始化', None),
                ('ai_learning', 'brain_feeding_start', 'AI脑库投喂机制启动', None),
            ]
            
            for record in historical_records:
                cursor.execute('INSERT INTO history_data (data_type, data_key, data_value, original_id) VALUES (?, ?, ?, ?)', record)
            
            conn.commit()
            logger.info(f"初始化了 {len(historical_records)} 条历史数据")
        
        conn.close()
    
    def _generate_archive_id(self) -> str:
        """生成归档ID"""
        return f'arch_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    def record(self, data_type: str, data_key: str, data_value: str, original_id: int = None):
        """记录历史数据"""
        if not self.enabled:
            return
        
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(''' INSERT INTO history_data (data_type, data_key, data_value, original_id) VALUES (?, ?, ?, ?) ''', (data_type, data_key, data_value, original_id))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"记录历史数据: {data_type}.{data_key}")
    
    def _archive_data(self, data_type: str = None):
        """归档历史数据"""
        if not self.archive_enabled:
            return
        
        cutoff_time = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM history_data WHERE is_archived = 0 AND created_at < ?'
        params = [cutoff_time]
        
        if data_type:
            query += ' AND data_type = ?'
            params.append(data_type)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return
        
        archive_id = self._generate_archive_id()
        archive_path = os.path.join(self._archive_path, f'{archive_id}.json')
        
        archive_data = [{
            'id': row[0],
            'data_type': row[1],
            'data_key': row[2],
            'data_value': row[3],
            'original_id': row[4],
            'created_at': row[5]
        } for row in rows]
        
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        
        cursor.execute('INSERT INTO archive_records (archive_id, data_type, record_count, archive_path) VALUES (?, ?, ?, ?)',
                      (archive_id, data_type or 'all', len(rows), archive_path))
        
        cursor.execute('UPDATE history_data SET is_archived = 1, archived_at = ? WHERE id IN (' + 
                      ','.join(['?'] * len(rows)) + ')', 
                      [datetime.now().isoformat()] + [row[0] for row in rows])
        
        conn.commit()
        conn.close()
        
        logger.info(f"归档历史数据: {archive_id}, 记录数: {len(rows)}")
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff_time = (datetime.now() - timedelta(days=self.retention_days * 2)).isoformat()
        
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history_data WHERE is_archived = 1 AND archived_at < ?', (cutoff_time,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"清理了 {deleted_count} 条过期历史数据")
    
    def get_history(self, data_type: str = None, data_key: str = None, 
                   start_time: str = None, end_time: str = None,
                   limit: int = 100, offset: int = 0) -> list:
        """查询历史数据"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM history_data WHERE 1=1'
        params = []
        
        if data_type:
            query += ' AND data_type = ?'
            params.append(data_type)
        if data_key:
            query += ' AND data_key = ?'
            params.append(data_key)
        if start_time:
            query += ' AND created_at >= ?'
            params.append(start_time)
        if end_time:
            query += ' AND created_at <= ?'
            params.append(end_time)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'data_type': row[1],
            'data_key': row[2],
            'data_value': row[3],
            'original_id': row[4],
            'created_at': row[5],
            'archived_at': row[6],
            'is_archived': row[7]
        } for row in rows]
    
    def get_stats(self) -> Dict:
        """获取历史馆统计数据"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM system_versions')
        stats['versions'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM upgrade_history')
        stats['upgrades'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_brain_bank')
        stats['knowledge'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_learning_tasks')
        stats['learning'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM history_data')
        stats['total_records'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_timeline(self) -> list:
        """获取版本时间线"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT version, build_date, codename, description, features, status FROM system_versions ORDER BY build_date DESC')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            features = []
            try:
                if row[4]:
                    features = json.loads(row[4])
            except:
                pass
            data.append({
                'version': row[0],
                'build_date': row[1],
                'codename': row[2],
                'description': row[3],
                'features': features,
                'status': row[5] or 'stable'
            })
        
        conn.close()
        return data
    
    def get_upgrades(self) -> list:
        """获取升级记录"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT version, upgrade_type, description, ai_employees_count, features_count, status, created_at FROM upgrade_history ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'version': row[0],
                'upgrade_type': row[1],
                'description': row[2],
                'ai_employees_count': row[3],
                'features_count': row[4],
                'status': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return data
    
    def get_learning_tasks(self) -> list:
        """获取学习任务"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT task_name, task_desc, task_type, version, status, created_at FROM ai_learning_tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'task_name': row[0],
                'task_desc': row[1],
                'task_type': row[2],
                'version': row[3],
                'status': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return data
    
    def get_knowledge(self) -> list:
        """获取知识脑库"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT category, title, content, tags, version, created_at FROM ai_brain_bank ORDER BY created_at DESC LIMIT 50')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'category': row[0],
                'title': row[1],
                'content': row[2],
                'tags': row[3],
                'version': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return data
    
    def get_rules(self) -> list:
        """获取系统规则"""
        db_path = get_db_path('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_rules'")
        if cursor.fetchone():
            cursor.execute('SELECT rule_id, rule_name, rule_type, description, action, enabled, created_at FROM system_rules ORDER BY priority DESC, created_at DESC LIMIT 50')
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'rule_id': row[0],
                    'rule_name': row[1],
                    'rule_type': row[2],
                    'description': row[3],
                    'action': row[4],
                    'enabled': bool(row[5]),
                    'created_at': row[6]
                })
        else:
            data = []
        
        conn.close()
        return data
    
    def start(self):
        """启动历史数据服务"""
        logger.info(f"启动历史数据服务，归档间隔: {self.archive_interval}秒")
        self._running = True
        
        while self._running:
            try:
                self._archive_data()
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"历史数据服务异常: {e}")
            
            for _ in range(self.archive_interval):
                if not self._running:
                    break
                time.sleep(1)
    
    def stop(self):
        """停止历史数据服务"""
        logger.info("停止历史数据服务")
        self._running = False

history_data_service = HistoryDataService()

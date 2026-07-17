# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库自动投喂系统
功能: 自动将知识写入AI脑库,实现脑库壮大功能
支持知识验证、去重、分类、存储
"""

import os
import sys
import json
import logging
import threading
import time
import sqlite3
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_brain_auto_feeding.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KnowledgeValidator:
    """知识验证器"""
    
    def __init__(self, rules: Dict):
        self.rules = rules
        self.min_confidence = rules.get('knowledge_quality_standards', {}).get('minimum_confidence', 0.7)
        self.required_fields = rules.get('brain_feeding_rules', {}).get('knowledge_structure', {}).get('required_fields', [])
    
    def validate(self, knowledge: Dict) -> Dict:
        """验证知识条目"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'knowledge': knowledge
        }
        
        if not self._check_required_fields(knowledge, result):
            result['valid'] = False
        
        if not self._check_confidence(knowledge, result):
            result['valid'] = False
        
        self._check_content_quality(knowledge, result)
        self._check_format(knowledge, result)
        
        return result
    
    def _check_required_fields(self, knowledge: Dict, result: Dict) -> bool:
        """检查必填字段"""
        missing_fields = []
        for field in self.required_fields:
            if field not in knowledge or not knowledge[field]:
                missing_fields.append(field)
        
        if missing_fields:
            result['errors'].append(f"缺少必填字段: {', '.join(missing_fields)}")
            return False
        
        return True
    
    def _check_confidence(self, knowledge: Dict, result: Dict) -> bool:
        """检查置信度"""
        confidence = knowledge.get('confidence', 0)
        if confidence < self.min_confidence:
            result['errors'].append(f"置信度 {confidence} 低于阈值 {self.min_confidence}")
            return False
        return True
    
    def _check_content_quality(self, knowledge: Dict, result: Dict):
        """检查内容质量"""
        content = knowledge.get('content', '')
        if len(content) < 10:
            result['warnings'].append("知识内容过短")
        
        if len(content) > 10000:
            result['warnings'].append("知识内容过长,建议拆分")
    
    def _check_format(self, knowledge: Dict, result: Dict):
        """检查格式"""
        if 'tags' in knowledge and not isinstance(knowledge['tags'], list):
            result['errors'].append("tags必须是列表格式")
        
        if 'timestamp' in knowledge:
            try:
                datetime.fromisoformat(knowledge['timestamp'])
            except ValueError:
                result['warnings'].append("timestamp格式不正确")


class KnowledgeDeduplicator:
    """知识去重器"""
    
    def __init__(self, db_path: str = 'ai_brain.db'):
        self.db_path = db_path
        self.duplicate_threshold = 0.9
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL UNIQUE,
                knowledge_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_fingerprint(self, knowledge: Dict) -> str:
        """生成知识指纹"""
        content = knowledge.get('content', '')
        title = knowledge.get('title', '')
        combined = f"{title}\n{content}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, knowledge: Dict) -> bool:
        """检查是否重复"""
        fingerprint = self.generate_fingerprint(knowledge)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM knowledge_fingerprints WHERE fingerprint = ?
        ''', (fingerprint,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def record_fingerprint(self, knowledge: Dict, knowledge_id: str):
        """记录知识指纹"""
        fingerprint = self.generate_fingerprint(knowledge)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO knowledge_fingerprints (fingerprint, knowledge_id, created_at)
                VALUES (?, ?, ?)
            ''', (fingerprint, knowledge_id, datetime.now().isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"记录指纹失败: {str(e)}")
        finally:
            conn.close()


class KnowledgeClassifier:
    """知识分类器"""
    
    def __init__(self):
        self.categories = {
            'tech_update': {
                'keywords': ['update', 'version', 'feature', 'framework', 'library', 'release', 'upgrade'],
                'description': '技术更新'
            },
            'performance': {
                'keywords': ['performance', 'optimization', 'speed', 'latency', 'throughput', 'bottleneck'],
                'description': '性能优化'
            },
            'security': {
                'keywords': ['security', 'vulnerability', 'patch', 'secure', 'authentication', 'encryption'],
                'description': '安全防护'
            },
            'bug_fix': {
                'keywords': ['bug', 'fix', 'repair', 'error', 'issue', 'problem', 'resolved'],
                'description': '问题修复'
            },
            'best_practice': {
                'keywords': ['best practice', 'guide', 'tutorial', 'how to', 'recommendation'],
                'description': '最佳实践'
            },
            'architecture': {
                'keywords': ['architecture', 'design', 'pattern', 'microservice', 'system', 'infrastructure'],
                'description': '架构设计'
            },
            'industry_report': {
                'keywords': ['report', 'trend', 'analysis', 'market', 'industry', 'survey'],
                'description': '行业报告'
            },
            'general': {
                'keywords': [],
                'description': '通用知识'
            }
        }
    
    def classify(self, knowledge: Dict) -> str:
        """分类知识"""
        if 'type' in knowledge and knowledge['type']:
            if knowledge['type'] in self.categories:
                return knowledge['type']
        
        content = knowledge.get('content', '').lower()
        title = knowledge.get('title', '').lower()
        
        text = f"{title} {content}"
        
        for category, config in self.categories.items():
            for keyword in config['keywords']:
                if keyword.lower() in text:
                    return category
        
        return 'general'
    
    def enrich_tags(self, knowledge: Dict) -> List[str]:
        """丰富标签"""
        tags = knowledge.get('tags', [])
        category = self.classify(knowledge)
        
        if category not in tags:
            tags.append(category)
        
        content = knowledge.get('content', '').lower()
        title = knowledge.get('title', '').lower()
        text = f"{title} {content}"
        
        category_keywords = self.categories.get(category, {}).get('keywords', [])
        for keyword in category_keywords:
            if keyword.lower() in text:
                if keyword.lower() not in tags:
                    tags.append(keyword.lower())
        
        return tags


class BrainStorageManager:
    """脑库存储管理器"""
    
    def __init__(self, db_path: str = 'ai_brain.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                tags TEXT,
                metadata TEXT,
                timestamp TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                version INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_knowledge_id TEXT NOT NULL,
                target_knowledge_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brain_growth_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_count INTEGER NOT NULL,
                total_size_bytes INTEGER NOT NULL,
                avg_confidence REAL NOT NULL,
                category_distribution TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_knowledge(self, knowledge: Dict) -> str:
        """存储知识"""
        knowledge_id = hashlib.md5(f"{knowledge['title']}{knowledge['content']}".encode('utf-8')).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO ai_brain_knowledge (
                    knowledge_id, title, content, type, source, confidence, 
                    tags, metadata, timestamp, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT version FROM ai_brain_knowledge WHERE knowledge_id = ?), 0) + 1
                )
            ''', (
                knowledge_id,
                knowledge['title'],
                knowledge['content'],
                knowledge['type'],
                knowledge['source'],
                knowledge['confidence'],
                json.dumps(knowledge.get('tags', []), ensure_ascii=False),
                json.dumps(knowledge.get('metadata', {}), ensure_ascii=False),
                knowledge.get('timestamp', datetime.now().isoformat()),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                knowledge_id
            ))
            
            conn.commit()
            logger.info(f"知识已存储: {knowledge['title']}")
            
            self._update_growth_stats()
            
            return knowledge_id
        except Exception as e:
            logger.error(f"存储知识失败: {str(e)}")
            return None
        finally:
            conn.close()
    
    def batch_store_knowledge(self, knowledge_list: List[Dict]) -> Dict:
        """批量存储知识"""
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'knowledge_ids': []
        }
        
        for knowledge in knowledge_list:
            try:
                knowledge_id = self.store_knowledge(knowledge)
                if knowledge_id:
                    results['success'] += 1
                    results['knowledge_ids'].append(knowledge_id)
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"存储知识失败: {str(e)}")
                results['failed'] += 1
        
        logger.info(f"批量存储完成: 成功 {results['success']} 条,失败 {results['failed']} 条")
        return results
    
    def _update_growth_stats(self):
        """更新脑库增长统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge WHERE is_active = 1')
        knowledge_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(LENGTH(content)) FROM ai_brain_knowledge WHERE is_active = 1')
        total_size_bytes = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(confidence) FROM ai_brain_knowledge WHERE is_active = 1')
        avg_confidence = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT type, COUNT(*) FROM ai_brain_knowledge WHERE is_active = 1 GROUP BY type
        ''')
        category_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('''
            INSERT INTO brain_growth_stats (knowledge_count, total_size_bytes, avg_confidence, 
                                           category_distribution, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            knowledge_count,
            total_size_bytes,
            avg_confidence,
            json.dumps(category_dist, ensure_ascii=False),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_brain_stats(self) -> Dict:
        """获取脑库统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge WHERE is_active = 1')
        knowledge_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(LENGTH(content)) FROM ai_brain_knowledge WHERE is_active = 1')
        total_size_bytes = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(confidence) FROM ai_brain_knowledge WHERE is_active = 1')
        avg_confidence = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT type, COUNT(*) FROM ai_brain_knowledge WHERE is_active = 1 GROUP BY type
        ''')
        category_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('SELECT MAX(created_at) FROM ai_brain_knowledge')
        last_added = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'knowledge_count': knowledge_count,
            'total_size_bytes': total_size_bytes,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'avg_confidence': round(avg_confidence, 2),
            'category_distribution': category_dist,
            'last_added': last_added,
            'growth_rate': self._calculate_growth_rate()
        }
    
    def _calculate_growth_rate(self) -> float:
        """计算增长速率"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT knowledge_count, created_at 
            FROM brain_growth_stats 
            ORDER BY created_at DESC 
            LIMIT 2
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < 2:
            return 0.0
        
        recent_count, recent_time = rows[0]
        previous_count, previous_time = rows[1]
        
        try:
            recent_dt = datetime.fromisoformat(recent_time)
            previous_dt = datetime.fromisoformat(previous_time)
            hours_diff = (recent_dt - previous_dt).total_seconds() / 3600
            
            if hours_diff > 0:
                return round((recent_count - previous_count) / hours_diff, 2)
        except Exception as e:
            logger.error(f"计算增长速率失败: {str(e)}")
        
        return 0.0


class AIBrainAutoFeedingSystem:
    """AI脑库自动投喂系统"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = self._load_rules()
        
        self.validator = KnowledgeValidator(self.rules)
        self.deduplicator = KnowledgeDeduplicator()
        self.classifier = KnowledgeClassifier()
        self.storage = BrainStorageManager()
        
        self.is_running = False
        self.feeding_thread = None
        self.feeding_interval = 3600
        self.feeding_buffer = []
        
        self.batch_size = self.rules.get('brain_feeding_rules', {}).get('feeding_strategy', {}).get('batch_size', 100)
    
    def _load_rules(self) -> Dict:
        """加载规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}")
            return {}
    
    def start(self):
        """启动自动投喂系统"""
        if not self.is_running:
            self.is_running = True
            self.feeding_thread = threading.Thread(target=self._feeding_loop, daemon=True)
            self.feeding_thread.start()
            logger.info("AI脑库自动投喂系统已启动")
    
    def stop(self):
        """停止自动投喂系统"""
        self.is_running = False
        if self.feeding_thread and self.feeding_thread.is_alive():
            self.feeding_thread.join(timeout=5)
        self.flush_buffer()
        logger.info("AI脑库自动投喂系统已停止")
    
    def _feeding_loop(self):
        """投喂循环"""
        while self.is_running:
            try:
                if self.feeding_buffer:
                    self._feed_brain()
                time.sleep(self.feeding_interval)
            except Exception as e:
                logger.error(f"投喂循环出错: {str(e)}")
                time.sleep(600)
    
    def add_knowledge(self, knowledge: Dict) -> Dict:
        """添加知识到缓冲区"""
        validation = self.validator.validate(knowledge)
        
        if not validation['valid']:
            logger.warning(f"知识验证失败: {validation['errors']}")
            return {'status': 'rejected', 'errors': validation['errors']}
        
        if self.deduplicator.is_duplicate(knowledge):
            logger.info(f"知识重复,已跳过: {knowledge.get('title', '')}")
            return {'status': 'duplicate'}
        
        knowledge['type'] = self.classifier.classify(knowledge)
        knowledge['tags'] = self.classifier.enrich_tags(knowledge)
        
        self.feeding_buffer.append(knowledge)
        
        if len(self.feeding_buffer) >= self.batch_size:
            self._feed_brain()
        
        return {'status': 'accepted', 'type': knowledge['type']}
    
    def batch_add_knowledge(self, knowledge_list: List[Dict]) -> Dict:
        """批量添加知识"""
        results = {
            'accepted': 0,
            'rejected': 0,
            'duplicate': 0
        }
        
        for knowledge in knowledge_list:
            result = self.add_knowledge(knowledge)
            results[result['status']] += 1
        
        logger.info(f"批量添加完成: 接受 {results['accepted']} 条,拒绝 {results['rejected']} 条,重复 {results['duplicate']} 条")
        return results
    
    def _feed_brain(self):
        """投喂脑库"""
        logger.info(f"开始投喂脑库,待投喂知识数量: {len(self.feeding_buffer)}")
        
        knowledge_to_feed = list(self.feeding_buffer)
        self.feeding_buffer = []
        
        results = self.storage.batch_store_knowledge(knowledge_to_feed)
        
        for knowledge in knowledge_to_feed:
            if 'knowledge_id' in results.get('knowledge_ids', []):
                self.deduplicator.record_fingerprint(knowledge, knowledge['knowledge_id'])
        
        stats = self.storage.get_brain_stats()
        logger.info(f"脑库投喂完成,当前知识总量: {stats['knowledge_count']} 条")
    
    def flush_buffer(self):
        """清空缓冲区并投喂"""
        if self.feeding_buffer:
            self._feed_brain()
    
    def get_brain_stats(self) -> Dict:
        """获取脑库统计"""
        return self.storage.get_brain_stats()
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索知识"""
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ai_brain_knowledge 
            WHERE is_active = 1 AND (title LIKE ? OR content LIKE ?)
            ORDER BY confidence DESC, created_at DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'knowledge_id': row[1],
                'title': row[2],
                'content': row[3],
                'type': row[4],
                'source': row[5],
                'confidence': row[6],
                'tags': json.loads(row[7]) if row[7] else [],
                'metadata': json.loads(row[8]) if row[8] else {},
                'created_at': row[11]
            })
        
        conn.close()
        return results


if __name__ == "__main__":
    feeding_system = AIBrainAutoFeedingSystem()
    feeding_system.start()
    
    try:
        logger.info("测试添加知识...")
        
        test_knowledge = [
            {
                'title': 'Python性能优化技巧',
                'content': '使用生成器代替列表推导可以显著减少内存使用,特别是在处理大数据集时。',
                'type': 'performance',
                'source': 'test_source',
                'confidence': 0.9,
                'tags': ['python', 'performance', 'optimization']
            },
            {
                'title': 'API安全最佳实践',
                'content': '使用JWT令牌进行身份认证,并设置合理的过期时间。',
                'type': 'security',
                'source': 'test_source',
                'confidence': 0.85,
                'tags': ['api', 'security', 'authentication']
            }
        ]
        
        results = feeding_system.batch_add_knowledge(test_knowledge)
        logger.info(f"添加结果: {results}")
        
        logger.info("获取脑库统计...")
        stats = feeding_system.get_brain_stats()
        logger.info(f"脑库统计: {stats}")
        
        logger.info("搜索知识...")
        search_results = feeding_system.search_knowledge('性能')
        for result in search_results:
            logger.info(f"搜索结果: {result['title']}")
        
        time.sleep(30)
    except KeyboardInterrupt:
        feeding_system.stop()
        logger.info("AI脑库自动投喂系统已停止")
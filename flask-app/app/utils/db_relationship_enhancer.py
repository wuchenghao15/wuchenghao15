# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库表间关系强化系统
管理表间关系、添加外键约束、建立数据链路
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption
from app.utils.db_structure_analyzer import db_structure_analyzer
from app.utils.logging import logger


class DBRelationshipEnhancer:
    """数据库关系强化器"""
    
    RELATIONSHIP_CONFIG_FILE = 'app/config/relationships.json'
    
    def __init__(self):
        self.db = db_manager
        self.analyzer = db_structure_analyzer
        self._relationship_config = self._load_relationship_config()
    
    def _ensure_tokens(self, required: int):
        """确保有足够的令牌"""
        try:
            token_bucket = getattr(self.db, '_token_bucket', None)
            token_lock = getattr(self.db, '_token_bucket_lock', None)
            if token_bucket and token_lock:
                with token_lock:
                    deficit = max(0, required - token_bucket['tokens'])
                    if deficit > 0:
                        token_bucket['tokens'] = min(
                            token_bucket['capacity'],
                            token_bucket['tokens'] + deficit
                        )
        except Exception:
            pass
    
    def _load_relationship_config(self) -> Dict:
        """加载关系配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'relationships.json'
        )
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'relationships': [], 'enhanced_at': None}
    
    def _save_relationship_config(self):
        """保存关系配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'relationships.json'
        )
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._relationship_config, f, indent=2, ensure_ascii=False)
    
    def add_foreign_key_constraint(self, table_name: str, column_name: str, 
                                  referenced_table: str, referenced_column: str = 'id',
                                  on_delete: str = 'SET NULL', on_update: str = 'CASCADE') -> bool:
        """添加外键约束
        
        Args:
            table_name: 表名
            column_name: 外键字段名
            referenced_table: 引用表名
            referenced_column: 引用字段名
            on_delete: 删除行为
            on_update: 更新行为
            
        Returns:
            是否成功
        """
        if self._has_foreign_key_constraint(table_name, column_name):
            logger.info(f"外键约束已存在: {table_name}.{column_name} -> {referenced_table}.{referenced_column}")
            return True
        
        encrypted_table = table_encryption.encrypt_table_name(table_name)
        encrypted_ref_table = table_encryption.encrypt_table_name(referenced_table)
        
        try:
            query = f"""
                ALTER TABLE {encrypted_table} 
                ADD CONSTRAINT fk_{table_name}_{column_name}
                FOREIGN KEY ({column_name}) 
                REFERENCES {encrypted_ref_table}({referenced_column})
                ON DELETE {on_delete}
                ON UPDATE {on_update}
            """
            
            cursor, success = self.db.execute(query)
            if success:
                logger.info(f"外键约束添加成功: {table_name}.{column_name} -> {referenced_table}.{referenced_column}")
                self._record_enhanced_relationship(table_name, column_name, referenced_table, referenced_column)
                return True
            else:
                logger.warning(f"外键约束添加失败: {table_name}.{column_name}")
                return False
        except Exception as e:
            logger.error(f"添加外键约束失败: {str(e)}")
            return False
    
    def _has_foreign_key_constraint(self, table_name: str, column_name: str) -> bool:
        """检查外键约束是否存在"""
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        query = f"PRAGMA foreign_key_list({encrypted_name})"
        results = self.db.fetch_all(query)
        
        for fk in results:
            if isinstance(fk, dict):
                if fk.get('from') == column_name:
                    return True
            elif fk[3] == column_name:
                return True
        
        return False
    
    def _record_enhanced_relationship(self, table_name: str, column_name: str, 
                                      referenced_table: str, referenced_column: str):
        """记录强化的关系"""
        relationship = {
            'table_name': table_name,
            'column_name': column_name,
            'referenced_table': referenced_table,
            'referenced_column': referenced_column,
            'enhanced_at': datetime.now().isoformat(),
            'type': 'foreign_key'
        }
        
        existing = [r for r in self._relationship_config['relationships'] 
                   if r['table_name'] == table_name and r['column_name'] == column_name]
        
        if not existing:
            self._relationship_config['relationships'].append(relationship)
            self._relationship_config['enhanced_at'] = datetime.now().isoformat()
            self._save_relationship_config()
    
    def add_index(self, table_name: str, columns: List[str], unique: bool = False) -> bool:
        """添加索引
        
        Args:
            table_name: 表名
            columns: 字段列表
            unique: 是否唯一索引
            
        Returns:
            是否成功
        """
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        index_suffix = '_'.join(columns)
        index_name = f"idx_{table_name}_{index_suffix}"
        
        try:
            unique_clause = 'UNIQUE' if unique else ''
            columns_str = ', '.join(columns)
            query = f"CREATE {unique_clause} INDEX IF NOT EXISTS {index_name} ON {encrypted_name} ({columns_str})"
            
            cursor, success = self.db.execute(query)
            if success:
                logger.info(f"索引添加成功: {table_name}.{index_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"添加索引失败: {str(e)}")
            return False
    
    def enhance_all_relationships(self) -> Dict[str, Any]:
        """强化所有识别到的关系"""
        missing_relationships = self.analyzer.find_missing_relationships()
        result = {
            'total_candidates': len(missing_relationships),
            'success_count': 0,
            'failed_count': 0,
            'enhanced': [],
            'failed': []
        }
        
        for rel in missing_relationships:
            success = self.add_foreign_key_constraint(
                rel['table'],
                rel['column'],
                rel['referenced_table'],
                rel['referenced_column']
            )
            
            if success:
                result['success_count'] += 1
                result['enhanced'].append(rel)
            else:
                result['failed_count'] += 1
                result['failed'].append(rel)
        
        logger.info(f"关系强化完成: 成功={result['success_count']}, 失败={result['failed_count']}")
        return result
    
    def add_missing_timestamps(self) -> Dict[str, Any]:
        """为缺少时间戳字段的表添加created_at和updated_at"""
        self._ensure_tokens(100)
        integrity = self.analyzer.analyze_data_integrity()
        tables_without_updated_at = integrity['tables_without_updated_at']
        
        result = {
            'total_tables': len(tables_without_updated_at),
            'success_count': 0,
            'failed_count': 0,
            'enhanced': [],
            'failed': []
        }
        
        for table_name in tables_without_updated_at:
            encrypted_name = table_encryption.encrypt_table_name(table_name)
            
            try:
                cursor, success1 = self.db.execute(f"ALTER TABLE {encrypted_name} ADD COLUMN IF NOT EXISTS created_at TEXT DEFAULT CURRENT_TIMESTAMP")
                cursor, success2 = self.db.execute(f"ALTER TABLE {encrypted_name} ADD COLUMN IF NOT EXISTS updated_at TEXT DEFAULT CURRENT_TIMESTAMP")
                
                if success1 and success2:
                    result['success_count'] += 1
                    result['enhanced'].append(table_name)
                    logger.info(f"时间戳字段添加成功: {table_name}")
                else:
                    result['failed_count'] += 1
                    result['failed'].append(table_name)
            except Exception as e:
                logger.error(f"添加时间戳字段失败: {table_name}, 错误: {str(e)}")
                result['failed_count'] += 1
                result['failed'].append(table_name)
        
        return result
    
    def add_primary_key(self, table_name: str, column_name: str = 'id') -> bool:
        """为缺少主键的表添加主键
        
        Args:
            table_name: 表名
            column_name: 主键字段名
            
        Returns:
            是否成功
        """
        structure = self.analyzer.get_table_structure(table_name)
        if not structure:
            return False
        
        if any(col_info['primary_key'] for col_info in structure.values()):
            logger.info(f"表已存在主键: {table_name}")
            return True
        
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        
        try:
            if column_name not in structure:
                cursor, success = self.db.execute(f"ALTER TABLE {encrypted_name} ADD COLUMN {column_name} TEXT")
                if not success:
                    return False
            
            query = f"ALTER TABLE {encrypted_name} ADD PRIMARY KEY ({column_name})"
            cursor, success = self.db.execute(query)
            
            if success:
                logger.info(f"主键添加成功: {table_name}.{column_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"添加主键失败: {table_name}, 错误: {str(e)}")
            return False
    
    def add_default_indexes(self) -> Dict[str, Any]:
        """为关键表添加默认索引"""
        self._ensure_tokens(50)
        index_config = {
            'users': [
                {'columns': ['username'], 'unique': True},
                {'columns': ['email'], 'unique': True},
                {'columns': ['role']},
                {'columns': ['created_at']}
            ],
            'exams': [
                {'columns': ['title']},
                {'columns': ['status']},
                {'columns': ['created_at']},
                {'columns': ['exam_type']}
            ],
            'questions': [
                {'columns': ['exam_id']},
                {'columns': ['type']},
                {'columns': ['difficulty']},
                {'columns': ['created_at']}
            ],
            'ai_employees': [
                {'columns': ['agent_code'], 'unique': True},
                {'columns': ['status']},
                {'columns': ['agent_type']}
            ],
            'sessions': [
                {'columns': ['user_id']},
                {'columns': ['expires_at']}
            ],
            'exam_papers': [
                {'columns': ['exam_id']},
                {'columns': ['user_id']},
                {'columns': ['created_at']}
            ],
            'exam_results': [
                {'columns': ['exam_id']},
                {'columns': ['user_id']},
                {'columns': ['score']},
                {'columns': ['created_at']}
            ]
        }
        
        result = {
            'total_indexes': 0,
            'success_count': 0,
            'failed_count': 0,
            'indexes': []
        }
        
        for table_name, indexes in index_config.items():
            structure = self.analyzer.get_table_structure(table_name)
            if not structure:
                continue
            
            for idx_config in indexes:
                if all(col in structure for col in idx_config['columns']):
                    result['total_indexes'] += 1
                    success = self.add_index(
                        table_name,
                        idx_config['columns'],
                        idx_config['unique']
                    )
                    if success:
                        result['success_count'] += 1
                        result['indexes'].append({
                            'table': table_name,
                            'columns': idx_config['columns'],
                            'unique': idx_config['unique']
                        })
                    else:
                        result['failed_count'] += 1
        
        logger.info(f"索引添加完成: 总数={result['total_indexes']}, 成功={result['success_count']}, 失败={result['failed_count']}")
        return result
    
    def run_full_enhancement(self) -> Dict[str, Any]:
        """运行完整的数据库关系强化"""
        logger.info("开始数据库关系强化...")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }
        
        step1 = self.add_missing_timestamps()
        result['steps'].append({'name': 'add_missing_timestamps', 'result': step1})
        
        step2 = self.add_default_indexes()
        result['steps'].append({'name': 'add_default_indexes', 'result': step2})
        
        step3 = self.enhance_all_relationships()
        result['steps'].append({'name': 'enhance_relationships', 'result': step3})
        
        result['summary'] = {
            'total_success': sum(step['result']['success_count'] for step in result['steps']),
            'total_failed': sum(step['result']['failed_count'] for step in result['steps']),
            'total_tables_enhanced': len(set([item for step in result['steps'] 
                                              for item in step['result'].get('enhanced', [])]))
        }
        
        logger.info(f"数据库关系强化完成: 成功={result['summary']['total_success']}, 失败={result['summary']['total_failed']}")
        return result
    
    def get_enhanced_relationships(self) -> List[Dict]:
        """获取已强化的关系列表"""
        return self._relationship_config.get('relationships', [])


db_relationship_enhancer = DBRelationshipEnhancer()
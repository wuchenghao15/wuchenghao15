# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库结构分析工具
分析数据库表结构、字段关系、数据完整性等
"""

import sqlite3
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption
from app.utils.logging import logger


class DBStructureAnalyzer:
    """数据库结构分析器"""
    
    def __init__(self):
        self.db = db_manager
        self._table_info_cache = {}
        self._relationships_cache = {}
    
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
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        self._ensure_tokens(10)
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = self.db.fetch_all(query)
        tables = []
        for row in results:
            name = row['name'] if isinstance(row, dict) else row[0]
            if not name.startswith('sqlite_'):
                decrypted_name = table_encryption.decrypt_table_name(name)
                tables.append(decrypted_name)
        return tables
    
    def get_table_structure(self, table_name: str) -> Optional[Dict[str, Dict]]:
        """获取表结构详情"""
        if table_name in self._table_info_cache:
            return self._table_info_cache[table_name]
        
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        query = f"PRAGMA table_info({encrypted_name})"
        results = self.db.fetch_all(query)
        
        if not results:
            return None
        
        structure = {}
        for col in results:
            if isinstance(col, dict):
                name = col['name']
                col_type = col['type']
                not_null = bool(col['notnull'])
                pk = bool(col['pk'])
                default = col.get('dflt_value')
            else:
                name = col[1]
                col_type = col[2]
                not_null = bool(col[3])
                pk = bool(col[5])
                default = col[4]
            
            structure[name] = {
                'type': col_type,
                'not_null': not_null,
                'primary_key': pk,
                'default': default,
                'is_foreign_key': name.endswith('_id') or '_id_' in name
            }
        
        self._table_info_cache[table_name] = structure
        return structure
    
    def get_table_indexes(self, table_name: str) -> List[Dict]:
        """获取表索引信息"""
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        query = f"PRAGMA index_list({encrypted_name})"
        results = self.db.fetch_all(query)
        
        indexes = []
        for idx in results:
            if isinstance(idx, dict):
                index_name = idx['name']
                unique = bool(idx['unique'])
            else:
                index_name = idx[1]
                unique = bool(idx[2])
            
            query_cols = f"PRAGMA index_info({index_name})"
            col_results = self.db.fetch_all(query_cols)
            columns = []
            for col in col_results:
                if isinstance(col, dict):
                    columns.append(col['name'])
                else:
                    columns.append(col[2])
            
            indexes.append({
                'name': index_name,
                'unique': unique,
                'columns': columns
            })
        
        return indexes
    
    def get_table_row_count(self, table_name: str) -> int:
        """获取表行数"""
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        query = f"SELECT COUNT(*) FROM {encrypted_name}"
        result = self.db.fetch_one(query)
        return result[0] if result else 0
    
    def get_table_size(self, table_name: str) -> Dict:
        """获取表大小信息"""
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        
        query = f"SELECT COUNT(*) FROM {encrypted_name}"
        row_count = self.db.fetch_one(query)
        row_count = row_count[0] if row_count else 0
        
        query = f"PRAGMA table_info({encrypted_name})"
        cols = self.db.fetch_all(query)
        col_count = len(cols)
        
        return {
            'row_count': row_count,
            'column_count': col_count,
            'estimated_size_mb': (row_count * col_count * 100) / (1024 * 1024)
        }
    
    def analyze_relationships(self) -> Dict[str, List[Dict]]:
        """分析表间关系（基于字段命名约定）"""
        if self._relationships_cache:
            return self._relationships_cache
        
        all_tables = self.get_all_tables()
        relationships = {}
        
        for table_name in all_tables:
            structure = self.get_table_structure(table_name)
            if not structure:
                continue
            
            table_relationships = []
            
            for col_name, col_info in structure.items():
                if col_info['is_foreign_key']:
                    referenced_table = self._guess_referenced_table(col_name)
                    if referenced_table and referenced_table != table_name:
                        table_relationships.append({
                            'column': col_name,
                            'referenced_table': referenced_table,
                            'referenced_column': 'id',
                            'relationship_type': self._determine_relationship_type(table_name, col_name),
                            'is_candidate': True
                        })
            
            if table_relationships:
                relationships[table_name] = table_relationships
        
        self._relationships_cache = relationships
        return relationships
    
    def _guess_referenced_table(self, column_name: str) -> Optional[str]:
        """根据字段名猜测引用的表"""
        patterns = [
            r'^(\w+)_id$',
            r'^(\w+)id$',
            r'^(\w+)_uuid$',
            r'^(\w+)_uid$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, column_name.lower())
            if match:
                table_prefix = match.group(1)
                possible_tables = [table_prefix, f"{table_prefix}s"]
                for pt in possible_tables:
                    encrypted = table_encryption.encrypt_table_name(pt)
                    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{encrypted}'"
                    result = self.db.fetch_one(query)
                    if result:
                        return pt
        
        return None
    
    def _determine_relationship_type(self, from_table: str, column_name: str) -> str:
        """确定关系类型"""
        if 'user_id' in column_name.lower():
            return 'many_to_one'
        if 'parent_id' in column_name.lower():
            return 'self_referential'
        if 'group_id' in column_name.lower():
            return 'many_to_one'
        if 'exam_id' in column_name.lower():
            return 'many_to_one'
        if 'question_id' in column_name.lower():
            return 'many_to_one'
        return 'many_to_one'
    
    def find_missing_relationships(self) -> List[Dict]:
        """查找缺失的外键关系"""
        relationships = self.analyze_relationships()
        missing = []
        
        for table_name, rels in relationships.items():
            for rel in rels:
                if not self._has_foreign_key_constraint(table_name, rel['column']):
                    missing.append({
                        'table': table_name,
                        'column': rel['column'],
                        'referenced_table': rel['referenced_table'],
                        'referenced_column': rel['referenced_column']
                    })
        
        return missing
    
    def _has_foreign_key_constraint(self, table_name: str, column_name: str) -> bool:
        """检查是否存在外键约束"""
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
    
    def analyze_data_integrity(self) -> Dict[str, Any]:
        """分析数据完整性"""
        all_tables = self.get_all_tables()
        integrity_report = {
            'total_tables': len(all_tables),
            'tables_without_pk': [],
            'tables_without_indexes': [],
            'missing_relationships': [],
            'orphaned_records': [],
            'duplicate_records': [],
            'tables_without_updated_at': []
        }
        
        for table_name in all_tables:
            structure = self.get_table_structure(table_name)
            if not structure:
                continue
            
            has_pk = any(col_info['primary_key'] for col_info in structure.values())
            if not has_pk:
                integrity_report['tables_without_pk'].append(table_name)
            
            indexes = self.get_table_indexes(table_name)
            if not indexes:
                integrity_report['tables_without_indexes'].append(table_name)
            
            if 'updated_at' not in structure:
                integrity_report['tables_without_updated_at'].append(table_name)
        
        integrity_report['missing_relationships'] = self.find_missing_relationships()
        integrity_report['orphaned_records'] = self._find_orphaned_records()
        integrity_report['duplicate_records'] = self._find_duplicate_records()
        
        return integrity_report
    
    def _find_orphaned_records(self) -> List[Dict]:
        """查找孤立记录"""
        relationships = self.analyze_relationships()
        orphaned = []
        
        for table_name, rels in relationships.items():
            for rel in rels:
                count = self._count_orphaned_records(table_name, rel['column'], rel['referenced_table'])
                if count > 0:
                    orphaned.append({
                        'table': table_name,
                        'column': rel['column'],
                        'referenced_table': rel['referenced_table'],
                        'orphaned_count': count
                    })
        
        return orphaned
    
    def _count_orphaned_records(self, table_name: str, column_name: str, referenced_table: str) -> int:
        """统计孤立记录数量"""
        encrypted_table = table_encryption.encrypt_table_name(table_name)
        encrypted_ref = table_encryption.encrypt_table_name(referenced_table)
        
        query = f"""
            SELECT COUNT(*) FROM {encrypted_table} t
            LEFT JOIN {encrypted_ref} r ON t.{column_name} = r.id
            WHERE t.{column_name} IS NOT NULL AND r.id IS NULL
        """
        
        result = self.db.fetch_one(query)
        return result[0] if result else 0
    
    def _find_duplicate_records(self) -> List[Dict]:
        """查找重复记录"""
        duplicates = []
        
        check_tables = ['users', 'questions', 'exams', 'ai_employees']
        for table_name in check_tables:
            structure = self.get_table_structure(table_name)
            if not structure:
                continue
            
            for col_name in structure:
                if col_name in ['id', 'created_at', 'updated_at']:
                    continue
                
                encrypted_name = table_encryption.encrypt_table_name(table_name)
                query = f"""
                    SELECT {col_name}, COUNT(*) as cnt 
                    FROM {encrypted_name} 
                    GROUP BY {col_name} 
                    HAVING COUNT(*) > 1
                    LIMIT 5
                """
                
                results = self.db.fetch_all(query)
                if results:
                    duplicates.append({
                        'table': table_name,
                        'column': col_name,
                        'duplicate_count': sum(r[1] if not isinstance(r, dict) else r['cnt'] for r in results)
                    })
        
        return duplicates
    
    def generate_structure_report(self) -> Dict[str, Any]:
        """生成完整的数据库结构报告"""
        self._ensure_tokens(200)
        start_time = datetime.now()
        
        all_tables = self.get_all_tables()
        report = {
            'generated_at': datetime.now().isoformat(),
            'database_path': self.db.db_path,
            'total_tables': len(all_tables),
            'tables': {},
            'relationships': self.analyze_relationships(),
            'integrity': self.analyze_data_integrity(),
            'stats': {}
        }
        
        total_rows = 0
        for table_name in all_tables[:50]:
            structure = self.get_table_structure(table_name)
            size = self.get_table_size(table_name)
            indexes = self.get_table_indexes(table_name)
            
            report['tables'][table_name] = {
                'structure': structure,
                'size': size,
                'indexes': indexes
            }
            total_rows += size['row_count']
        
        report['stats'] = {
            'total_rows': total_rows,
            'tables_analyzed': min(len(all_tables), 50),
            'elapsed_time': (datetime.now() - start_time).total_seconds()
        }
        
        return report


db_structure_analyzer = DBStructureAnalyzer()
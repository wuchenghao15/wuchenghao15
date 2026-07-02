# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI智能JSON数据导入系统
自动扫描JSON数据结构，自动匹配数据库表，实现增量保存
"""

import json
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption
from app.utils.logging import logger


class AIJSONImporter:
    """AI智能JSON数据导入器"""
    
    def __init__(self):
        self.db = db_manager
        self.import_history = []
        self._table_structures = {}
    
    def _scan_json_structure(self, json_data: List[Dict]) -> Dict[str, Dict]:
        """扫描JSON数据结构，分析字段类型和出现频率
        
        Args:
            json_data: JSON数据列表
            
        Returns:
            字段结构分析结果
        """
        if not json_data:
            return {}
        
        field_info = {}
        
        for item in json_data:
            for key, value in item.items():
                if key not in field_info:
                    field_info[key] = {
                        'types': set(),
                        'count': 0,
                        'null_count': 0,
                        'sample_values': [],
                        'max_length': 0,
                        'is_unique': True,
                        'values': set()
                    }
                
                field_info[key]['count'] += 1
                field_info[key]['values'].add(str(value))
                
                if value is None:
                    field_info[key]['null_count'] += 1
                else:
                    field_type = type(value).__name__
                    field_info[key]['types'].add(field_type)
                    
                    if field_type in ['str', 'string']:
                        field_info[key]['max_length'] = max(
                            field_info[key]['max_length'], len(str(value))
                        )
                        if len(field_info[key]['sample_values']) < 3:
                            field_info[key]['sample_values'].append(str(value)[:50])
                    elif field_type in ['int', 'float', 'bool']:
                        if len(field_info[key]['sample_values']) < 3:
                            field_info[key]['sample_values'].append(value)
        
        for key in field_info:
            field_info[key]['is_unique'] = len(field_info[key]['values']) == field_info[key]['count']
            field_info[key]['unique_ratio'] = len(field_info[key]['values']) / max(field_info[key]['count'], 1)
        
        return field_info
    
    def _get_table_structure(self, table_name: str) -> Optional[Dict[str, str]]:
        """获取数据库表结构
        
        Args:
            table_name: 表名
            
        Returns:
            表结构字典 {字段名: 字段类型}
        """
        if table_name in self._table_structures:
            return self._table_structures[table_name]
        
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        cursor, success = self.db.execute(f"PRAGMA table_info({encrypted_name})")
        
        if not success or not cursor:
            return None
        
        columns = cursor.fetchall()
        if not columns:
            return None
        
        structure = {}
        for col in columns:
            if isinstance(col, dict):
                structure[col['name']] = col['type']
            else:
                structure[col[1]] = col[2]
        
        self._table_structures[table_name] = structure
        return structure
    
    def _get_all_table_names(self) -> List[str]:
        """获取所有数据库表名（解密后的）
        
        Returns:
            表名列表
        """
        cursor, success = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not success or not cursor:
            return []
        
        tables = cursor.fetchall()
        table_names = []
        
        for table in tables:
            if isinstance(table, dict):
                name = table['name']
            else:
                name = table[0]
            
            if name.startswith('t_'):
                decrypted = table_encryption.decrypt_table_name(name)
                if decrypted != name:
                    table_names.append(decrypted)
            elif not name.startswith('sqlite_'):
                table_names.append(name)
        
        return table_names
    
    def _calculate_match_score(self, json_fields: List[str], table_structure: Dict[str, str]) -> float:
        """计算JSON字段与表结构的匹配度
        
        Args:
            json_fields: JSON字段列表
            table_structure: 表结构
            
        Returns:
            匹配度分数 (0-1)
        """
        table_fields = set(table_structure.keys())
        json_field_set = set(json_fields)
        
        intersection = json_field_set & table_fields
        union = json_field_set | table_fields
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _auto_match_table(self, json_fields: List[str], json_structure: Dict[str, Dict]) -> Optional[str]:
        """自动匹配最适合的数据库表
        
        Args:
            json_fields: JSON字段列表
            json_structure: JSON结构分析结果
            
        Returns:
            匹配的表名，如果没有匹配返回None
        """
        all_tables = self._get_all_table_names()
        best_match = None
        best_score = 0.0
        
        for table_name in all_tables:
            table_structure = self._get_table_structure(table_name)
            if not table_structure:
                continue
            
            score = self._calculate_match_score(json_fields, table_structure)
            
            if score > best_score:
                best_score = score
                best_match = table_name
        
        if best_score >= 0.6:
            logger.info(f"自动匹配表: {best_match} (匹配度: {best_score:.2f})")
            return best_match
        
        logger.info(f"未找到匹配的表，匹配度最高: {best_match} ({best_score:.2f})")
        return None
    
    def _generate_table_name(self, json_structure: Dict[str, Dict]) -> str:
        """根据JSON结构生成表名
        
        Args:
            json_structure: JSON结构分析结果
            
        Returns:
            生成的表名
        """
        field_names = list(json_structure.keys())
        
        keywords = {
            'user': ['user', 'username', 'email', 'password', 'role'],
            'question': ['question', 'content', 'options', 'answer', 'exam'],
            'exam': ['exam', 'title', 'duration', 'questions', 'score'],
            'record': ['record', 'history', 'log', 'activity'],
            'config': ['config', 'setting', 'option', 'parameter'],
            'data': ['data', 'info', 'detail', 'item']
        }
        
        matched_keyword = 'data'
        max_matches = 0
        
        for keyword, patterns in keywords.items():
            matches = sum(1 for field in field_names if any(p in field.lower() for p in patterns))
            if matches > max_matches:
                max_matches = matches
                matched_keyword = keyword
        
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"{matched_keyword}_{timestamp}"
    
    def _convert_to_sqlite_type(self, python_type: str, max_length: int = 0) -> str:
        """将Python类型转换为SQLite类型
        
        Args:
            python_type: Python类型名称
            max_length: 字符串最大长度
            
        Returns:
            SQLite类型
        """
        type_map = {
            'str': 'TEXT',
            'string': 'TEXT',
            'int': 'INTEGER',
            'float': 'REAL',
            'bool': 'INTEGER',
            'dict': 'TEXT',
            'list': 'TEXT',
            'NoneType': 'TEXT'
        }
        
        base_type = type_map.get(python_type, 'TEXT')
        
        if base_type == 'TEXT' and max_length > 0:
            if max_length <= 255:
                return 'VARCHAR(255)'
            elif max_length <= 1024:
                return 'VARCHAR(1024)'
            elif max_length <= 4096:
                return 'VARCHAR(4096)'
        
        return base_type
    
    def _create_table(self, table_name: str, json_structure: Dict[str, Dict]) -> bool:
        """根据JSON结构自动创建新表
        
        Args:
            table_name: 表名
            json_structure: JSON结构分析结果
            
        Returns:
            创建是否成功
        """
        columns = []
        
        has_id = False
        for field, info in json_structure.items():
            if field.lower() == 'id':
                has_id = True
                columns.append(f"{field} TEXT PRIMARY KEY")
            elif info['is_unique'] and info['null_count'] == 0:
                columns.append(f"{field} TEXT PRIMARY KEY")
            else:
                main_type = next(iter(info['types']), 'str')
                sqlite_type = self._convert_to_sqlite_type(main_type, info['max_length'])
                columns.append(f"{field} {sqlite_type}")
        
        if not has_id:
            columns.insert(0, "id TEXT PRIMARY KEY")
        
        columns.append("created_at TEXT DEFAULT CURRENT_TIMESTAMP")
        columns.append("updated_at TEXT DEFAULT CURRENT_TIMESTAMP")
        
        columns_sql = ', '.join(columns)
        success = self.db.create_table(table_name, {col.split()[0]: col.split()[1] for col in columns})
        
        if success:
            logger.info(f"自动创建表: {table_name}")
            self._table_structures.pop(table_name, None)
        
        return success
    
    def _generate_record_id(self, record: Dict[str, Any]) -> str:
        """生成记录唯一ID
        
        Args:
            record: 记录数据
            
        Returns:
            唯一ID
        """
        if 'id' in record and record['id']:
            return str(record['id'])
        
        content = json.dumps(record, sort_keys=True, ensure_ascii=False)
        return f"REC_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _check_existing_record(self, table_name: str, record: Dict[str, Any]) -> Optional[Dict]:
        """检查记录是否已存在（增量检查）
        
        Args:
            table_name: 表名
            record: 记录数据
            
        Returns:
            已存在的记录，如果不存在返回None
        """
        record_id = self._generate_record_id(record)
        
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        query = f"SELECT * FROM {encrypted_name} WHERE id = ?"
        result = self.db.fetch_one(query, (record_id,))
        
        return result
    
    def _insert_record(self, table_name: str, record: Dict[str, Any]) -> bool:
        """插入新记录
        
        Args:
            table_name: 表名
            record: 记录数据
            
        Returns:
            插入是否成功
        """
        record_id = self._generate_record_id(record)
        record['id'] = record_id
        
        if 'created_at' not in record:
            record['created_at'] = datetime.now().isoformat()
        if 'updated_at' not in record:
            record['updated_at'] = datetime.now().isoformat()
        
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                record[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                record[key] = 1 if value else 0
        
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        columns = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))
        values = tuple(record.values())
        query = f"INSERT INTO {encrypted_name} ({columns}) VALUES ({placeholders})"
        
        cursor, success = self.db.execute(query, values)
        return success
    
    def _update_record(self, table_name: str, record: Dict[str, Any]) -> bool:
        """更新已存在的记录
        
        Args:
            table_name: 表名
            record: 记录数据
            
        Returns:
            更新是否成功
        """
        record_id = self._generate_record_id(record)
        record['id'] = record_id
        record['updated_at'] = datetime.now().isoformat()
        
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                record[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                record[key] = 1 if value else 0
        
        encrypted_name = table_encryption.encrypt_table_name(table_name)
        
        set_clause = ', '.join([f"{key} = ?" for key in record.keys()])
        values = tuple(record.values()) + (record_id,)
        query = f"UPDATE {encrypted_name} SET {set_clause} WHERE id = ?"
        
        _, success = self.db.execute(query, values)
        return success
    
    def _convert_record_to_table_format(self, record: Dict[str, Any], table_structure: Dict[str, str]) -> Dict[str, Any]:
        """将记录转换为适合表结构的格式
        
        Args:
            record: 原始记录
            table_structure: 表结构
            
        Returns:
            转换后的记录
        """
        converted = {}
        
        for key, value in record.items():
            if key not in table_structure:
                continue
            
            col_type = table_structure[key].upper()
            
            if isinstance(value, (dict, list)):
                converted[key] = json.dumps(value, ensure_ascii=False)
            elif col_type in ['INTEGER', 'INT']:
                try:
                    converted[key] = int(value) if value is not None else None
                except (ValueError, TypeError):
                    converted[key] = None
            elif col_type in ['REAL', 'FLOAT', 'DOUBLE']:
                try:
                    converted[key] = float(value) if value is not None else None
                except (ValueError, TypeError):
                    converted[key] = None
            else:
                converted[key] = str(value) if value is not None else None
        
        return converted
    
    def _ensure_tokens(self, required: int):
        """确保有足够的令牌用于批量操作"""
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
    
    def import_json_data(self, json_data: List[Dict], table_name: str = None, auto_create: bool = True) -> Dict[str, Any]:
        """导入JSON数据到数据库（核心方法）
        
        Args:
            json_data: JSON数据列表
            table_name: 指定表名（可选，不指定则自动匹配）
            auto_create: 是否自动创建新表
            
        Returns:
            导入结果统计
        """
        if not json_data:
            return {
                'success': False,
                'message': 'JSON数据为空',
                'stats': {'total': 0, 'inserted': 0, 'updated': 0, 'failed': 0}
            }
        
        self._ensure_tokens(len(json_data) * 3)
        
        start_time = datetime.now()
        stats = {
            'total': len(json_data),
            'inserted': 0,
            'updated': 0,
            'failed': 0
        }
        
        json_structure = self._scan_json_structure(json_data)
        json_fields = list(json_structure.keys())
        
        if not table_name:
            table_name = self._auto_match_table(json_fields, json_structure)
        
        if not table_name:
            if auto_create:
                table_name = self._generate_table_name(json_structure)
                self._create_table(table_name, json_structure)
            else:
                return {
                    'success': False,
                    'message': '未找到匹配的表，请指定表名或开启自动创建',
                    'stats': stats
                }
        
        table_structure = self._get_table_structure(table_name)
        if not table_structure:
            return {
                'success': False,
                'message': f'表 {table_name} 不存在且无法创建',
                'stats': stats
            }
        
        conn = self.db.begin_transaction()
        if not conn:
            return {
                'success': False,
                'message': '无法开始事务',
                'stats': stats
            }
        
        try:
            cursor = conn.cursor()
            encrypted_name = table_encryption.encrypt_table_name(table_name)
            
            for record in json_data:
                try:
                    converted = self._convert_record_to_table_format(record, table_structure)
                    if not converted:
                        stats['failed'] += 1
                        continue
                    
                    record_id = self._generate_record_id(record)
                    converted['id'] = record_id
                    
                    cursor.execute(f"SELECT id FROM {encrypted_name} WHERE id = ?", (record_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        set_clause = ', '.join([f"{key} = ?" for key in converted.keys()])
                        values = tuple(converted.values()) + (record_id,)
                        cursor.execute(f"UPDATE {encrypted_name} SET {set_clause} WHERE id = ?", values)
                        stats['updated'] += 1
                    else:
                        columns = ', '.join(converted.keys())
                        placeholders = ', '.join(['?'] * len(converted))
                        values = tuple(converted.values())
                        cursor.execute(f"INSERT INTO {encrypted_name} ({columns}) VALUES ({placeholders})", values)
                        stats['inserted'] += 1
                except Exception as e:
                    logger.error(f"处理记录失败: {str(e)}")
                    stats['failed'] += 1
            
            self.db.commit_transaction(conn)
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'message': f'导入完成，表: {table_name}',
                'table_name': table_name,
                'stats': stats,
                'elapsed_time': elapsed_time,
                'json_structure': json_structure
            }
            
            self.import_history.append({
                'timestamp': datetime.now().isoformat(),
                'table_name': table_name,
                'stats': stats,
                'elapsed_time': elapsed_time
            })
            
            logger.info(f"JSON数据导入成功: 表={table_name}, 总数={stats['total']}, 新增={stats['inserted']}, 更新={stats['updated']}, 失败={stats['failed']}, 耗时={elapsed_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"导入JSON数据失败: {str(e)}")
            self.db.rollback_transaction(conn)
            return {
                'success': False,
                'message': f'导入失败: {str(e)}',
                'table_name': table_name,
                'stats': stats
            }
    
    def import_json_file(self, file_path: str, table_name: str = None, auto_create: bool = True) -> Dict[str, Any]:
        """从JSON文件导入数据
        
        Args:
            file_path: JSON文件路径
            table_name: 指定表名（可选）
            auto_create: 是否自动创建新表
            
        Returns:
            导入结果统计
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f'文件不存在: {file_path}',
                'stats': {'total': 0, 'inserted': 0, 'updated': 0, 'failed': 0}
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if isinstance(json_data, dict):
                json_data = [json_data]
            
            return self.import_json_data(json_data, table_name, auto_create)
        
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'message': f'JSON解析错误: {str(e)}',
                'stats': {'total': 0, 'inserted': 0, 'updated': 0, 'failed': 0}
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'读取文件失败: {str(e)}',
                'stats': {'total': 0, 'inserted': 0, 'updated': 0, 'failed': 0}
            }
    
    def analyze_json_for_import(self, json_data: List[Dict]) -> Dict[str, Any]:
        """分析JSON数据，提供导入建议
        
        Args:
            json_data: JSON数据列表
            
        Returns:
            分析结果和建议
        """
        if not json_data:
            return {'success': False, 'message': 'JSON数据为空'}
        
        json_structure = self._scan_json_structure(json_data)
        json_fields = list(json_structure.keys())
        
        best_table = self._auto_match_table(json_fields, json_structure)
        
        suggestions = []
        
        if best_table:
            table_structure = self._get_table_structure(best_table)
            if table_structure:
                table_fields = set(table_structure.keys())
                json_field_set = set(json_fields)
                
                missing_in_table = json_field_set - table_fields
                missing_in_json = table_fields - json_field_set
                
                if missing_in_table:
                    suggestions.append(f"以下JSON字段在表中不存在，导入时将被忽略: {', '.join(missing_in_table)}")
                
                if missing_in_json:
                    suggestions.append(f"以下表字段在JSON中不存在，将使用默认值: {', '.join(missing_in_json)}")
                
                suggestions.append(f"建议导入到表: {best_table}")
        else:
            suggestions.append("未找到匹配的表，建议创建新表")
            suggestions.append(f"建议表名: {self._generate_table_name(json_structure)}")
        
        return {
            'success': True,
            'json_structure': json_structure,
            'suggested_table': best_table,
            'suggestions': suggestions,
            'record_count': len(json_data)
        }


ai_json_importer = AIJSONImporter()
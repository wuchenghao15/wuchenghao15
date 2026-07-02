# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据链路闭环系统
建立数据流转链路，确保数据完整性和可追溯性
"""

import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption
from app.utils.db_structure_analyzer import db_structure_analyzer
from app.utils.logging import logger


class DataLinkClosure:
    """数据链路闭环系统"""
    
    LINK_CONFIG_FILE = 'app/config/data_links.json'
    
    def __init__(self):
        self.db = db_manager
        self.analyzer = db_structure_analyzer
        self._link_config = self._load_link_config()
        self._ensure_link_tables()
    
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
    
    def _load_link_config(self) -> Dict:
        """加载链路配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'data_links.json'
        )
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'links': [], 'closures': [], 'version': '1.0'}
    
    def _save_link_config(self):
        """保存链路配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'data_links.json'
        )
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._link_config, f, indent=2, ensure_ascii=False)
    
    def _ensure_link_tables(self):
        """确保链路追踪表存在"""
        tables = {
            'data_links': {
                'id': 'TEXT PRIMARY KEY',
                'source_table': 'TEXT NOT NULL',
                'source_id': 'TEXT',
                'target_table': 'TEXT NOT NULL',
                'target_id': 'TEXT',
                'link_type': 'TEXT',
                'link_data': 'TEXT',
                'created_at': 'TEXT DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TEXT DEFAULT CURRENT_TIMESTAMP'
            },
            'data_closure': {
                'id': 'TEXT PRIMARY KEY',
                'link_id': 'TEXT NOT NULL',
                'closure_type': 'TEXT',
                'status': 'TEXT DEFAULT "open"',
                'checksum': 'TEXT',
                'data_snapshot': 'TEXT',
                'verified_at': 'TEXT',
                'verified_by': 'TEXT',
                'created_at': 'TEXT DEFAULT CURRENT_TIMESTAMP'
            },
            'data_flow': {
                'id': 'TEXT PRIMARY KEY',
                'flow_id': 'TEXT NOT NULL',
                'step': 'INTEGER',
                'table_name': 'TEXT NOT NULL',
                'record_id': 'TEXT',
                'operation': 'TEXT',
                'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP',
                'user_id': 'TEXT',
                'session_id': 'TEXT'
            }
        }
        
        for table_name, columns in tables.items():
            self.db.create_table(table_name, columns)
    
    def create_link(self, source_table: str, source_id: str, 
                   target_table: str, target_id: str, 
                   link_type: str = 'reference', link_data: Dict = None) -> str:
        """创建数据链路
        
        Args:
            source_table: 源表名
            source_id: 源记录ID
            target_table: 目标表名
            target_id: 目标记录ID
            link_type: 链路类型
            link_data: 链路附加数据
            
        Returns:
            链路ID
        """
        self._ensure_tokens(10)
        link_id = f"LNK_{uuid.uuid4().hex[:12].upper()}"
        
        link_data_json = json.dumps(link_data, ensure_ascii=False) if link_data else '{}'
        
        query = f"""
            INSERT INTO data_links 
            (id, source_table, source_id, target_table, target_id, link_type, link_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor, success = self.db.execute(query, (
            link_id, source_table, source_id, target_table, target_id, link_type, link_data_json
        ))
        
        if success:
            logger.info(f"数据链路创建成功: {source_table}.{source_id} -> {target_table}.{target_id}")
            self._record_link_config(source_table, target_table, link_type)
            return link_id
        
        return None
    
    def _record_link_config(self, source_table: str, target_table: str, link_type: str):
        """记录链路配置"""
        link = {
            'source_table': source_table,
            'target_table': target_table,
            'link_type': link_type,
            'created_at': datetime.now().isoformat()
        }
        
        existing = [l for l in self._link_config['links'] 
                   if l['source_table'] == source_table 
                   and l['target_table'] == target_table
                   and l['link_type'] == link_type]
        
        if not existing:
            self._link_config['links'].append(link)
            self._save_link_config()
    
    def close_closure(self, link_id: str, closure_type: str = 'integrity') -> bool:
        """关闭链路闭环（验证完整性）
        
        Args:
            link_id: 链路ID
            closure_type: 闭环类型
            
        Returns:
            是否成功
        """
        query = "SELECT * FROM data_links WHERE id = ?"
        result = self.db.fetch_one(query, (link_id,))
        
        if not result:
            logger.warning(f"链路不存在: {link_id}")
            return False
        
        source_table = result['source_table'] if isinstance(result, dict) else result[1]
        source_id = result['source_id'] if isinstance(result, dict) else result[2]
        target_table = result['target_table'] if isinstance(result, dict) else result[3]
        target_id = result['target_id'] if isinstance(result, dict) else result[4]
        
        source_exists = self._record_exists(source_table, source_id)
        target_exists = self._record_exists(target_table, target_id)
        
        checksum = self._calculate_closure_checksum(source_table, source_id, target_table, target_id)
        data_snapshot = self._create_data_snapshot(source_table, source_id, target_table, target_id)
        
        closure_id = f"CLS_{uuid.uuid4().hex[:8].upper()}"
        
        query = f"""
            INSERT INTO data_closure 
            (id, link_id, closure_type, status, checksum, data_snapshot, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        status = 'closed' if source_exists and target_exists else 'broken'
        
        cursor, success = self.db.execute(query, (
            closure_id, link_id, closure_type, status, checksum, data_snapshot, datetime.now().isoformat()
        ))
        
        if success:
            logger.info(f"链路闭环创建: {link_id}, 状态: {status}")
            self._record_closure_config(link_id, closure_type, status)
        
        return success
    
    def _record_exists(self, table_name: str, record_id: str) -> bool:
        """检查记录是否存在"""
        query = f"SELECT COUNT(*) FROM {table_name} WHERE id = ?"
        result = self.db.fetch_one(query, (record_id,))
        return result[0] > 0 if result else False
    
    def _calculate_closure_checksum(self, source_table: str, source_id: str,
                                   target_table: str, target_id: str) -> str:
        """计算闭环校验和"""
        content = f"{source_table}:{source_id}:{target_table}:{target_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _create_data_snapshot(self, source_table: str, source_id: str,
                             target_table: str, target_id: str) -> str:
        """创建数据快照"""
        snapshot = {
            'source_table': source_table,
            'source_id': source_id,
            'target_table': target_table,
            'target_id': target_id,
            'timestamp': datetime.now().isoformat(),
            'source_exists': self._record_exists(source_table, source_id),
            'target_exists': self._record_exists(target_table, target_id)
        }
        return json.dumps(snapshot, ensure_ascii=False)
    
    def _record_closure_config(self, link_id: str, closure_type: str, status: str):
        """记录闭环配置"""
        closure = {
            'link_id': link_id,
            'closure_type': closure_type,
            'status': status,
            'created_at': datetime.now().isoformat()
        }
        self._link_config['closures'].append(closure)
        self._save_link_config()
    
    def record_data_flow(self, flow_id: str, step: int, table_name: str, 
                        record_id: str, operation: str, 
                        user_id: str = None, session_id: str = None):
        """记录数据流
        
        Args:
            flow_id: 数据流ID
            step: 步骤编号
            table_name: 表名
            record_id: 记录ID
            operation: 操作类型
            user_id: 用户ID
            session_id: 会话ID
        """
        flow_record_id = f"FLW_{uuid.uuid4().hex[:8].upper()}"
        
        query = f"""
            INSERT INTO data_flow 
            (id, flow_id, step, table_name, record_id, operation, user_id, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            flow_record_id, flow_id, step, table_name, record_id, operation, user_id, session_id
        ))
    
    def start_data_flow(self) -> str:
        """开始新的数据流追踪"""
        return f"FLOW_{uuid.uuid4().hex[:12].upper()}"
    
    def trace_data_flow(self, record_id: str, table_name: str) -> List[Dict]:
        """追踪记录的数据流转历史
        
        Args:
            record_id: 记录ID
            table_name: 表名
            
        Returns:
            数据流历史列表
        """
        query = f"""
            SELECT * FROM data_flow 
            WHERE table_name = ? AND record_id = ? 
            ORDER BY step ASC
        """
        
        results = self.db.fetch_all(query, (table_name, record_id))
        flows = []
        
        for row in results:
            if isinstance(row, dict):
                flows.append({
                    'flow_id': row['flow_id'],
                    'step': row['step'],
                    'operation': row['operation'],
                    'timestamp': row['timestamp'],
                    'user_id': row['user_id'],
                    'session_id': row['session_id']
                })
            else:
                flows.append({
                    'flow_id': row[1],
                    'step': row[2],
                    'operation': row[4],
                    'timestamp': row[5],
                    'user_id': row[6],
                    'session_id': row[7]
                })
        
        return flows
    
    def verify_closure(self, link_id: str) -> Dict[str, Any]:
        """验证链路闭环
        
        Args:
            link_id: 链路ID
            
        Returns:
            验证结果
        """
        query = "SELECT * FROM data_links WHERE id = ?"
        result = self.db.fetch_one(query, (link_id,))
        
        if not result:
            return {'success': False, 'message': '链路不存在'}
        
        source_table = result['source_table'] if isinstance(result, dict) else result[1]
        source_id = result['source_id'] if isinstance(result, dict) else result[2]
        target_table = result['target_table'] if isinstance(result, dict) else result[3]
        target_id = result['target_id'] if isinstance(result, dict) else result[4]
        
        source_exists = self._record_exists(source_table, source_id)
        target_exists = self._record_exists(target_table, target_id)
        
        return {
            'success': True,
            'link_id': link_id,
            'source_table': source_table,
            'source_id': source_id,
            'source_exists': source_exists,
            'target_table': target_table,
            'target_id': target_id,
            'target_exists': target_exists,
            'is_closed': source_exists and target_exists,
            'verified_at': datetime.now().isoformat()
        }
    
    def get_all_links(self) -> List[Dict]:
        """获取所有链路"""
        results = self.db.fetch_all("SELECT * FROM data_links")
        
        links = []
        for row in results:
            if isinstance(row, dict):
                links.append({
                    'id': row['id'],
                    'source_table': row['source_table'],
                    'source_id': row['source_id'],
                    'target_table': row['target_table'],
                    'target_id': row['target_id'],
                    'link_type': row['link_type'],
                    'created_at': row['created_at']
                })
            else:
                links.append({
                    'id': row[0],
                    'source_table': row[1],
                    'source_id': row[2],
                    'target_table': row[3],
                    'target_id': row[4],
                    'link_type': row[5],
                    'created_at': row[6]
                })
        
        return links
    
    def get_broken_closures(self) -> List[Dict]:
        """获取所有断开的闭环"""
        results = self.db.fetch_all("SELECT * FROM data_closure WHERE status = 'broken'")
        
        broken = []
        for row in results:
            if isinstance(row, dict):
                broken.append({
                    'id': row['id'],
                    'link_id': row['link_id'],
                    'closure_type': row['closure_type'],
                    'status': row['status'],
                    'created_at': row['created_at']
                })
            else:
                broken.append({
                    'id': row[0],
                    'link_id': row[1],
                    'closure_type': row[2],
                    'status': row[3],
                    'created_at': row[7]
                })
        
        return broken
    
    def run_closure_verification(self) -> Dict[str, Any]:
        """运行全链路闭环验证"""
        links = self.get_all_links()
        result = {
            'total_links': len(links),
            'verified_count': 0,
            'closed_count': 0,
            'broken_count': 0,
            'details': []
        }
        
        for link in links:
            verification = self.verify_closure(link['id'])
            result['verified_count'] += 1
            
            if verification['is_closed']:
                result['closed_count'] += 1
            else:
                result['broken_count'] += 1
            
            result['details'].append(verification)
        
        logger.info(f"闭环验证完成: 总数={len(links)}, 正常={result['closed_count']}, 断开={result['broken_count']}")
        return result


data_link_closure = DataLinkClosure()
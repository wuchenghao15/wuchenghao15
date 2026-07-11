# -*- coding: utf-8 -*-
"""
系统综合增强管理器
整合数据库拓展、端口管理、集群管理、多维度监控、权限规则升级、题库升级、
AI集群升级、AI模型库升级、前端布局优化、Git自动同步十大功能模块
提供统一的系统增强与监控接口
"""

import os
import sys
import json
import socket
import logging
import sqlite3
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SystemEnhancementManager')

SPLIT_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'split_databases'
)

# 各功能模块对应的分片库映射
SHARD_DB_MAP = {
    'database': 'system.db',
    'port': 'system.db',
    'cluster': 'system.db',
    'permission': 'auth.db',
    'question': 'question.db',
    'ai_cluster': 'ai.db',
    'ai_model': 'ai.db',
    'ai_model_lib': 'ai.db',
    'frontend': 'system.db',
    'git': 'log.db',
}


class SystemEnhancementManager:
    """系统综合增强管理器 - 统一管理十大功能模块"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self.app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.split_db_dir = SPLIT_DB_DIR
        os.makedirs(self.split_db_dir, exist_ok=True)
        # 初始化所有子模块状态
        self.module_status = {
            'database': {'name': '数据库功能拓展', 'enabled': True, 'last_run': None},
            'port': {'name': '端口管理', 'enabled': True, 'last_run': None},
            'cluster': {'name': '集群管理', 'enabled': True, 'last_run': None},
            'multi_dimension': {'name': '多维度管理', 'enabled': True, 'last_run': None},
            'permission': {'name': '权限规则升级', 'enabled': True, 'last_run': None},
            'question_bank': {'name': '题库升级', 'enabled': True, 'last_run': None},
            'ai_cluster': {'name': 'AI集群升级', 'enabled': True, 'last_run': None},
            'ai_model_lib': {'name': 'AI模型库升级', 'enabled': True, 'last_run': None},
            'frontend_layout': {'name': '前端布局优化', 'enabled': True, 'last_run': None},
            'git_sync': {'name': 'Git自动同步', 'enabled': True, 'last_run': None},
        }
        self._init_database()
        self._initialized = True
        logger.info("SystemEnhancementManager 初始化完成")

    # ============================================================
    # 基础工具方法
    # ============================================================
    def _get_db_path(self, module: str) -> str:
        """获取指定模块对应的分片库路径"""
        db_file = SHARD_DB_MAP.get(module, 'system.db')
        return os.path.join(self.split_db_dir, db_file)

    def _connect(self, module: str) -> Optional[sqlite3.Connection]:
        """连接指定模块的分片库"""
        try:
            db_path = self._get_db_path(module)
            conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"连接分片库失败[{module}]: {e}")
            return None

    def _init_database(self):
        """初始化各模块所需表结构"""
        try:
            # 系统库：端口/集群/前端/数据库拓展
            conn = self._connect('database')
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS enh_port_registry (
                        port INTEGER PRIMARY KEY,
                        service TEXT,
                        status TEXT DEFAULT 'allocated',
                        owner TEXT,
                        allocated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS enh_cluster_nodes (
                        node_id TEXT PRIMARY KEY,
                        node_type TEXT,
                        address TEXT,
                        status TEXT DEFAULT 'offline',
                        load REAL DEFAULT 0.0,
                        last_heartbeat TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS enh_frontend_layout (
                        layout_id TEXT PRIMARY KEY,
                        layout_name TEXT,
                        config TEXT DEFAULT '{}',
                        theme TEXT DEFAULT 'default',
                        is_active INTEGER DEFAULT 0,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                conn.close()
            # 权限库
            conn = self._connect('permission')
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS enh_permission_rules (
                        rule_id TEXT PRIMARY KEY,
                        role TEXT NOT NULL,
                        resource TEXT NOT NULL,
                        action_name TEXT NOT NULL,
                        allowed INTEGER DEFAULT 0,
                        priority INTEGER DEFAULT 0,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                conn.close()
            # AI 库
            conn = self._connect('ai_cluster')
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS enh_ai_nodes (
                        node_id TEXT PRIMARY KEY,
                        node_name TEXT,
                        model TEXT,
                        status TEXT DEFAULT 'idle',
                        load REAL DEFAULT 0.0,
                        capacity INTEGER DEFAULT 10,
                        last_heartbeat TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS enh_ai_models (
                        model_id TEXT PRIMARY KEY,
                        model_name TEXT,
                        version TEXT,
                        status TEXT DEFAULT 'registered',
                        performance_score REAL DEFAULT 0.0,
                        config TEXT DEFAULT '{}',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                conn.close()
            logger.info("系统增强管理表结构初始化完成")
        except Exception as e:
            logger.error(f"初始化系统增强表结构失败: {e}")

    def _touch(self, module: str):
        """更新模块运行时间"""
        self.module_status[module]['last_run'] = datetime.now().isoformat()

    # ==================== 1. 数据库功能拓展 ====================
    def db_health_check(self) -> Dict[str, Any]:
        """数据库健康检查"""
        self._touch('database')
        try:
            results = []
            if not os.path.isdir(self.split_db_dir):
                return {'success': False, 'databases': [], 'error': '分片库目录不存在'}
            for db_file in os.listdir(self.split_db_dir):
                if not db_file.endswith('.db'):
                    continue
                db_path = os.path.join(self.split_db_dir, db_file)
                info = {'name': db_file, 'healthy': True, 'size_bytes': 0}
                try:
                    info['size_bytes'] = os.path.getsize(db_path)
                    conn = sqlite3.connect(db_path, timeout=5.0)
                    cur = conn.cursor()
                    cur.execute('PRAGMA integrity_check')
                    integrity = cur.fetchone()
                    info['integrity'] = integrity[0] if integrity else 'unknown'
                    info['healthy'] = (info['integrity'] == 'ok')
                    cur.execute('SELECT count(*) FROM sqlite_master WHERE type="table"')
                    info['table_count'] = cur.fetchone()[0]
                    conn.close()
                except Exception as e:
                    info['healthy'] = False
                    info['error'] = str(e)
                results.append(info)
            healthy_count = sum(1 for r in results if r['healthy'])
            return {
                'success': True, 'timestamp': datetime.now().isoformat(),
                'total': len(results), 'healthy': healthy_count,
                'unhealthy': len(results) - healthy_count, 'databases': results,
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {'success': False, 'databases': [], 'error': str(e)}

    def analyze_table_structure(self, db_name: str) -> Dict[str, Any]:
        """分析指定分片库的表结构"""
        self._touch('database')
        try:
            db_path = os.path.join(self.split_db_dir, db_name)
            if not os.path.exists(db_path):
                return {'success': False, 'error': f'数据库 {db_name} 不存在'}
            conn = sqlite3.connect(db_path, timeout=5.0)
            cur = conn.cursor()
            cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = [row[0] for row in cur.fetchall()]
            analysis = []
            for table in tables:
                cur.execute(f'PRAGMA table_info("{table}")')
                columns = [{'name': col[1], 'type': col[2], 'pk': bool(col[5])} for col in cur.fetchall()]
                cur.execute(f'PRAGMA index_list("{table}")')
                indexes = [{'name': idx[1], 'unique': bool(idx[2])} for idx in cur.fetchall()]
                try:
                    cur.execute(f'SELECT count(*) FROM "{table}"')
                    row_count = cur.fetchone()[0]
                except Exception:
                    row_count = -1
                analysis.append({'table': table, 'columns': columns, 'indexes': indexes, 'row_count': row_count})
            conn.close()
            return {'success': True, 'database': db_name, 'table_count': len(analysis), 'tables': analysis}
        except Exception as e:
            logger.error(f"表结构分析失败[{db_name}]: {e}")
            return {'success': False, 'error': str(e)}

    def suggest_index_optimization(self, db_name: str) -> Dict[str, Any]:
        """索引优化建议"""
        self._touch('database')
        try:
            structure = self.analyze_table_structure(db_name)
            if not structure.get('success'):
                return structure
            suggestions = []
            for table in structure['tables']:
                if table['row_count'] > 1000 and not table['indexes']:
                    suggestions.append({
                        'table': table['table'], 'row_count': table['row_count'],
                        'issue': '大表无索引', 'action': '建议为主键或高频查询字段添加索引',
                    })
                idx_count = len(table['indexes'])
                if table['row_count'] > 10000 and idx_count < 2:
                    suggestions.append({
                        'table': table['table'], 'row_count': table['row_count'],
                        'index_count': idx_count, 'issue': '大表索引不足',
                        'action': '建议根据查询模式增加复合索引',
                    })
            return {
                'success': True, 'database': db_name,
                'total_suggestions': len(suggestions), 'suggestions': suggestions,
            }
        except Exception as e:
            logger.error(f"索引优化建议失败[{db_name}]: {e}")
            return {'success': False, 'error': str(e)}

    def manage_db_cluster(self, action: str = 'status', node_info: Optional[Dict] = None) -> Dict[str, Any]:
        """数据库集群管理"""
        self._touch('database')
        try:
            conn = self._connect('database')
            if not conn:
                return {'success': False, 'error': '无法连接系统库'}
            cur = conn.cursor()
            result = {}
            if action == 'status':
                cur.execute('SELECT * FROM enh_cluster_nodes')
                result = {'success': True, 'nodes': [dict(r) for r in cur.fetchall()]}
            elif action == 'add' and node_info:
                cur.execute(
                    'INSERT OR REPLACE INTO enh_cluster_nodes(node_id,node_type,address,status,load) VALUES(?,?,?,?,?)',
                    (node_info.get('node_id'), node_info.get('node_type', 'worker'),
                     node_info.get('address', ''), node_info.get('status', 'online'),
                     node_info.get('load', 0.0))
                )
                result = {'success': True, 'message': '节点已添加', 'node_id': node_info.get('node_id')}
            elif action == 'remove' and node_info:
                cur.execute('DELETE FROM enh_cluster_nodes WHERE node_id=?', (node_info.get('node_id'),))
                result = {'success': True, 'message': '节点已移除', 'node_id': node_info.get('node_id')}
            else:
                result = {'success': False, 'error': f'不支持的操作: {action}'}
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"数据库集群管理失败[{action}]: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 2. 端口管理 ====================
    def scan_ports(self, host: str = '127.0.0.1', port_range: str = '8000-9000') -> Dict[str, Any]:
        """扫描指定范围的端口"""
        self._touch('port')
        try:
            start, end = (int(x) for x in port_range.split('-'))
            open_ports = []
            for port in range(start, end + 1):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.2)
                        if s.connect_ex((host, port)) == 0:
                            open_ports.append(port)
                except Exception:
                    continue
            return {
                'success': True, 'host': host, 'range': port_range,
                'open_count': len(open_ports), 'open_ports': open_ports,
            }
        except Exception as e:
            logger.error(f"端口扫描失败: {e}")
            return {'success': False, 'open_ports': [], 'error': str(e)}

    def get_port_usage_stats(self) -> Dict[str, Any]:
        """端口使用统计"""
        self._touch('port')
        try:
            conn = self._connect('port')
            if not conn:
                return {'success': False, 'error': '无法连接系统库'}
            cur = conn.cursor()
            cur.execute('SELECT status, count(*) as cnt FROM enh_port_registry GROUP BY status')
            stats = {row['status']: row['cnt'] for row in cur.fetchall()}
            cur.execute('SELECT * FROM enh_port_registry ORDER BY port')
            ports = [dict(r) for r in cur.fetchall()]
            conn.close()
            return {'success': True, 'stats': stats, 'total': len(ports), 'ports': ports}
        except Exception as e:
            logger.error(f"端口使用统计失败: {e}")
            return {'success': False, 'stats': {}, 'error': str(e)}

    def allocate_port(self, service: str, preferred: Optional[int] = None, port_range=(8000, 9000)) -> Dict[str, Any]:
        """分配端口"""
        self._touch('port')
        try:
            conn = self._connect('port')
            if not conn:
                return {'success': False, 'error': '无法连接系统库'}
            cur = conn.cursor()
            cur.execute('SELECT port FROM enh_port_registry')
            used = {row['port'] for row in cur.fetchall()}
            chosen = None
            if preferred and preferred not in used:
                chosen = preferred
            else:
                for p in range(port_range[0], port_range[1] + 1):
                    if p not in used:
                        chosen = p
                        break
            if chosen is None:
                conn.close()
                return {'success': False, 'error': '无可用端口'}
            cur.execute(
                'INSERT OR REPLACE INTO enh_port_registry(port, service, status, owner) VALUES(?,?,?,?)',
                (chosen, service, 'allocated', service)
            )
            conn.commit()
            conn.close()
            return {'success': True, 'port': chosen, 'service': service, 'message': '端口已分配'}
        except Exception as e:
            logger.error(f"端口分配失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 3. 集群管理 ====================
    def manage_cluster_nodes(self, action: str = 'list', node: Optional[Dict] = None) -> Dict[str, Any]:
        """集群节点管理"""
        return self.manage_db_cluster(action, node)

    def monitor_cluster_status(self) -> Dict[str, Any]:
        """集群状态监控"""
        self._touch('cluster')
        try:
            conn = self._connect('cluster')
            if not conn:
                return {'success': False, 'error': '无法连接系统库'}
            cur = conn.cursor()
            cur.execute('SELECT status, count(*) as cnt FROM enh_cluster_nodes GROUP BY status')
            status_count = {row['status']: row['cnt'] for row in cur.fetchall()}
            cur.execute('SELECT avg(load) as avg_load FROM enh_cluster_nodes')
            row = cur.fetchone()
            avg_load = row['avg_load'] if row and row['avg_load'] is not None else 0.0
            cur.execute('SELECT * FROM enh_cluster_nodes')
            nodes = [dict(r) for r in cur.fetchall()]
            conn.close()
            return {
                'success': True, 'timestamp': datetime.now().isoformat(),
                'node_count': len(nodes), 'status_summary': status_count,
                'avg_load': round(avg_load, 2), 'nodes': nodes,
            }
        except Exception as e:
            logger.error(f"集群状态监控失败: {e}")
            return {'success': False, 'error': str(e)}

    def load_balance(self, strategy: str = 'round_robin') -> Dict[str, Any]:
        """负载均衡"""
        self._touch('cluster')
        try:
            status = self.monitor_cluster_status()
            if not status.get('success'):
                return status
            nodes = [n for n in status['nodes'] if n['status'] == 'online']
            if not nodes:
                return {'success': False, 'error': '无在线节点'}
            if strategy == 'least_load':
                target = min(nodes, key=lambda n: n['load'])
            else:  # round_robin
                target = nodes[0]
            return {
                'success': True, 'strategy': strategy,
                'target_node': target['node_id'], 'target_load': target['load'],
                'online_nodes': len(nodes),
            }
        except Exception as e:
            logger.error(f"负载均衡失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 4. 多维度管理 ====================
    def monitor_system_resources(self) -> Dict[str, Any]:
        """系统资源多维度监控"""
        self._touch('multi_dimension')
        try:
            import shutil
            cpu_count = os.cpu_count() or 1
            disk = shutil.disk_usage(self.app_root)
            # 进程数 (Unix)
            process_count = 0
            try:
                process_count = len(os.listdir('/proc')) - 1 if os.path.isdir('/proc') else 0
            except Exception:
                process_count = 0
            mem_info = {}
            try:
                import resource
                rusage = resource.getrusage(resource.RUSAGE_SELF)
                mem_info['max_rss_kb'] = rusage.ru_maxrss
            except Exception:
                pass
            return {
                'success': True, 'timestamp': datetime.now().isoformat(),
                'cpu': {'count': cpu_count},
                'disk': {'total': disk.total, 'used': disk.used, 'free': disk.free,
                         'usage_percent': round(disk.used / disk.total * 100, 2)},
                'memory': mem_info,
                'processes': process_count,
                'split_db_dir': self.split_db_dir,
            }
        except Exception as e:
            logger.error(f"系统资源监控失败: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_performance(self) -> Dict[str, Any]:
        """性能分析"""
        self._touch('multi_dimension')
        try:
            res = self.monitor_system_resources()
            if not res.get('success'):
                return res
            disk_pct = res['disk']['usage_percent']
            score = 100
            if disk_pct > 90:
                score -= 40
            elif disk_pct > 75:
                score -= 20
            grade = 'A' if score >= 90 else ('B' if score >= 75 else ('C' if score >= 60 else 'D'))
            return {
                'success': True, 'performance_score': score, 'grade': grade,
                'disk_usage_percent': disk_pct, 'cpu_count': res['cpu']['count'],
                'recommendations': self._build_recommendations(score, disk_pct),
            }
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            return {'success': False, 'error': str(e)}

    def _build_recommendations(self, score: int, disk_pct: float) -> List[str]:
        recs = []
        if disk_pct > 90:
            recs.append('磁盘使用率过高，建议立即清理日志和临时文件')
        elif disk_pct > 75:
            recs.append('磁盘使用率偏高，建议规划清理策略')
        if score < 75:
            recs.append('整体性能评分偏低，建议优化数据库查询和索引')
        if not recs:
            recs.append('系统运行状态良好')
        return recs

    # ==================== 5. 权限规则升级 ====================
    def manage_permission_rules(self, action: str = 'list', rule: Optional[Dict] = None) -> Dict[str, Any]:
        """权限规则数据库管理"""
        self._touch('permission')
        try:
            conn = self._connect('permission')
            if not conn:
                return {'success': False, 'error': '无法连接权限库'}
            cur = conn.cursor()
            result = {}
            if action == 'list':
                cur.execute('SELECT * FROM enh_permission_rules ORDER BY priority DESC')
                result = {'success': True, 'rules': [dict(r) for r in cur.fetchall()]}
            elif action == 'upsert' and rule:
                cur.execute('''
                    INSERT OR REPLACE INTO enh_permission_rules
                    (rule_id, role, resource, action_name, allowed, priority)
                    VALUES (?,?,?,?,?,?)
                ''', (rule.get('rule_id'), rule.get('role'), rule.get('resource'),
                      rule.get('action_name', rule.get('action')), rule.get('allowed', 0), rule.get('priority', 0)))
                result = {'success': True, 'message': '权限规则已保存', 'rule_id': rule.get('rule_id')}
            elif action == 'delete' and rule:
                cur.execute('DELETE FROM enh_permission_rules WHERE rule_id=?', (rule.get('rule_id'),))
                result = {'success': True, 'message': '权限规则已删除', 'rule_id': rule.get('rule_id')}
            else:
                result = {'success': False, 'error': f'不支持的操作: {action}'}
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"权限规则管理失败[{action}]: {e}")
            return {'success': False, 'error': str(e)}

    def get_role_permission_matrix(self) -> Dict[str, Any]:
        """角色权限矩阵"""
        self._touch('permission')
        try:
            conn = self._connect('permission')
            if not conn:
                return {'success': False, 'error': '无法连接权限库'}
            cur = conn.cursor()
            cur.execute('SELECT role, resource, action_name, allowed FROM enh_permission_rules')
            matrix = {}
            for row in cur.fetchall():
                role = row['role']
                if role not in matrix:
                    matrix[role] = []
                matrix[role].append({
                    'resource': row['resource'], 'action': row['action_name'],
                    'allowed': bool(row['allowed']),
                })
            conn.close()
            return {
                'success': True, 'roles': list(matrix.keys()),
                'matrix': matrix,
            }
        except Exception as e:
            logger.error(f"角色权限矩阵获取失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 6. 题库升级 ====================
    def get_question_bank_stats(self) -> Dict[str, Any]:
        """题库统计"""
        self._touch('question_bank')
        try:
            db_path = self._get_db_path('question')
            if not os.path.exists(db_path):
                return {'success': False, 'error': '题库不存在'}
            conn = sqlite3.connect(db_path, timeout=10.0)
            cur = conn.cursor()
            cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = [r[0] for r in cur.fetchall()]
            stats = {'tables': {}, 'total_questions': 0}
            for table in tables:
                if 'question' in table.lower() or 'exam' in table.lower():
                    try:
                        cur.execute(f'SELECT count(*) FROM "{table}"')
                        cnt = cur.fetchone()[0]
                        stats['tables'][table] = cnt
                        stats['total_questions'] += cnt
                    except Exception:
                        stats['tables'][table] = -1
            conn.close()
            return {'success': True, 'total_tables': len(tables), 'stats': stats}
        except Exception as e:
            logger.error(f"题库统计失败: {e}")
            return {'success': False, 'error': str(e)}

    def manage_question_categories(self, action: str = 'list', category: Optional[Dict] = None) -> Dict[str, Any]:
        """题目分类管理"""
        self._touch('question_bank')
        try:
            db_path = self._get_db_path('question')
            conn = sqlite3.connect(db_path, timeout=10.0)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS enh_question_categories (
                    category_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id TEXT,
                    description TEXT,
                    question_count INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            result = {}
            if action == 'list':
                cur.execute('SELECT * FROM enh_question_categories ORDER BY name')
                result = {'success': True, 'categories': [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]}
            elif action == 'upsert' and category:
                cur.execute('''
                    INSERT OR REPLACE INTO enh_question_categories(category_id, name, parent_id, description, question_count)
                    VALUES(?,?,?,?,?)
                ''', (category.get('category_id'), category.get('name'), category.get('parent_id'),
                      category.get('description', ''), category.get('question_count', 0)))
                result = {'success': True, 'message': '分类已保存', 'category_id': category.get('category_id')}
            elif action == 'delete' and category:
                cur.execute('DELETE FROM enh_question_categories WHERE category_id=?', (category.get('category_id'),))
                result = {'success': True, 'message': '分类已删除'}
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"题目分类管理失败[{action}]: {e}")
            return {'success': False, 'error': str(e)}

    def evaluate_question_quality(self, limit: int = 100) -> Dict[str, Any]:
        """题目质量评估"""
        self._touch('question_bank')
        try:
            db_path = self._get_db_path('question')
            conn = sqlite3.connect(db_path, timeout=10.0)
            cur = conn.cursor()
            cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%question%"')
            tables = [r[0] for r in cur.fetchall()]
            evaluations = []
            for table in tables[:5]:
                try:
                    cur.execute(f'SELECT * FROM "{table}" LIMIT ?', (limit,))
                    rows = cur.fetchall()
                    cols = [c[0] for c in cur.description]
                    for row in rows:
                        rec = dict(zip(cols, row))
                        text = str(rec.get('content') or rec.get('question') or rec.get('title') or '')
                        length = len(text)
                        if length < 10:
                            grade, score = 'D', 30
                        elif length < 50:
                            grade, score = 'C', 60
                        elif length < 200:
                            grade, score = 'B', 80
                        else:
                            grade, score = 'A', 95
                        evaluations.append({
                            'table': table, 'id': rec.get('id'), 'length': length,
                            'quality_score': score, 'quality_grade': grade,
                        })
                except Exception:
                    continue
            conn.close()
            avg = round(sum(e['quality_score'] for e in evaluations) / len(evaluations), 2) if evaluations else 0
            return {
                'success': True, 'evaluated': len(evaluations),
                'average_score': avg, 'evaluations': evaluations[:limit],
            }
        except Exception as e:
            logger.error(f"题目质量评估失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 7. AI集群升级 ====================
    def manage_ai_nodes(self, action: str = 'list', node: Optional[Dict] = None) -> Dict[str, Any]:
        """AI节点管理"""
        self._touch('ai_cluster')
        try:
            conn = self._connect('ai_cluster')
            if not conn:
                return {'success': False, 'error': '无法连接AI库'}
            cur = conn.cursor()
            result = {}
            if action == 'list':
                cur.execute('SELECT * FROM enh_ai_nodes ORDER BY status')
                result = {'success': True, 'nodes': [dict(r) for r in cur.fetchall()]}
            elif action == 'upsert' and node:
                cur.execute('''
                    INSERT OR REPLACE INTO enh_ai_nodes(node_id, node_name, model, status, load, capacity)
                    VALUES(?,?,?,?,?,?)
                ''', (node.get('node_id'), node.get('node_name'), node.get('model'),
                      node.get('status', 'idle'), node.get('load', 0.0), node.get('capacity', 10)))
                result = {'success': True, 'message': 'AI节点已保存', 'node_id': node.get('node_id')}
            elif action == 'delete' and node:
                cur.execute('DELETE FROM enh_ai_nodes WHERE node_id=?', (node.get('node_id'),))
                result = {'success': True, 'message': 'AI节点已删除'}
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"AI节点管理失败[{action}]: {e}")
            return {'success': False, 'error': str(e)}

    def schedule_ai_models(self, model_id: str) -> Dict[str, Any]:
        """AI模型调度"""
        self._touch('ai_cluster')
        try:
            conn = self._connect('ai_cluster')
            if not conn:
                return {'success': False, 'error': '无法连接AI库'}
            cur = conn.cursor()
            cur.execute('SELECT * FROM enh_ai_nodes WHERE status="idle" ORDER BY load ASC LIMIT 1')
            row = cur.fetchone()
            if not row:
                conn.close()
                return {'success': False, 'error': '无可用AI节点'}
            target = dict(row)
            cur.execute('UPDATE enh_ai_nodes SET status="busy", load=load+1 WHERE node_id=?', (target['node_id'],))
            conn.commit()
            conn.close()
            return {
                'success': True, 'model_id': model_id,
                'assigned_node': target['node_id'], 'message': '模型已调度到节点',
            }
        except Exception as e:
            logger.error(f"AI模型调度失败: {e}")
            return {'success': False, 'error': str(e)}

    def ai_load_balance(self) -> Dict[str, Any]:
        """AI负载均衡"""
        self._touch('ai_cluster')
        try:
            conn = self._connect('ai_cluster')
            if not conn:
                return {'success': False, 'error': '无法连接AI库'}
            cur = conn.cursor()
            cur.execute('SELECT status, count(*) as cnt FROM enh_ai_nodes GROUP BY status')
            status_count = {row['status']: row['cnt'] for row in cur.fetchall()}
            cur.execute('SELECT * FROM enh_ai_nodes WHERE status="idle" ORDER BY load ASC LIMIT 1')
            row = cur.fetchone()
            conn.close()
            target = dict(row) if row else None
            return {
                'success': True, 'status_summary': status_count,
                'recommended_node': target['node_id'] if target else None,
                'message': '负载均衡分析完成',
            }
        except Exception as e:
            logger.error(f"AI负载均衡失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 8. AI模型库升级 ====================
    def register_model(self, model: Dict) -> Dict[str, Any]:
        """模型注册"""
        self._touch('ai_model_lib')
        try:
            conn = self._connect('ai_model_lib')
            if not conn:
                return {'success': False, 'error': '无法连接AI库'}
            cur = conn.cursor()
            model_id = model.get('model_id') or f"model_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cur.execute('''
                INSERT OR REPLACE INTO enh_ai_models(model_id, model_name, version, status, performance_score, config)
                VALUES(?,?,?,?,?,?)
            ''', (model_id, model.get('model_name'), model.get('version', '1.0.0'),
                  model.get('status', 'registered'), model.get('performance_score', 0.0),
                  json.dumps(model.get('config', {}), ensure_ascii=False)))
            conn.commit()
            conn.close()
            return {'success': True, 'model_id': model_id, 'message': '模型注册成功'}
        except Exception as e:
            logger.error(f"模型注册失败: {e}")
            return {'success': False, 'error': str(e)}

    def manage_model_versions(self, model_name: str) -> Dict[str, Any]:
        """模型版本管理"""
        self._touch('ai_model_lib')
        try:
            conn = self._connect('ai_model_lib')
            if not conn:
                return {'success': False, 'error': '无法连接AI库'}
            cur = conn.cursor()
            cur.execute('SELECT * FROM enh_ai_models WHERE model_name=? ORDER BY version DESC', (model_name,))
            versions = [dict(r) for r in cur.fetchall()]
            conn.close()
            return {
                'success': True, 'model_name': model_name,
                'version_count': len(versions), 'versions': versions,
            }
        except Exception as e:
            logger.error(f"模型版本管理失败: {e}")
            return {'success': False, 'error': str(e)}

    def evaluate_model_performance(self, model_id: str, score: float = 0.0) -> Dict[str, Any]:
        """模型性能评估"""
        self._touch('ai_model_lib')
        try:
            conn = self._connect('ai_model_lib')
            if not conn:
                return {'success': False, 'error': '无法连接AI库'}
            cur = conn.cursor()
            cur.execute('SELECT * FROM enh_ai_models WHERE model_id=?', (model_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return {'success': False, 'error': '模型不存在'}
            model = dict(row)
            grade = 'A' if score >= 90 else ('B' if score >= 75 else ('C' if score >= 60 else 'D'))
            cur.execute('UPDATE enh_ai_models SET performance_score=?, updated_at=? WHERE model_id=?',
                        (score, datetime.now().isoformat(), model_id))
            conn.commit()
            conn.close()
            return {
                'success': True, 'model_id': model_id, 'model_name': model['model_name'],
                'version': model['version'], 'performance_score': score, 'grade': grade,
            }
        except Exception as e:
            logger.error(f"模型性能评估失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 9. 前端布局优化 ====================
    def manage_layout_config(self, action: str = 'list', layout: Optional[Dict] = None) -> Dict[str, Any]:
        """布局配置管理"""
        self._touch('frontend_layout')
        try:
            conn = self._connect('frontend')
            if not conn:
                return {'success': False, 'error': '无法连接系统库'}
            cur = conn.cursor()
            result = {}
            if action == 'list':
                cur.execute('SELECT * FROM enh_frontend_layout ORDER BY is_active DESC')
                result = {'success': True, 'layouts': [dict(r) for r in cur.fetchall()]}
            elif action == 'upsert' and layout:
                cur.execute('''
                    INSERT OR REPLACE INTO enh_frontend_layout(layout_id, layout_name, config, theme, is_active)
                    VALUES(?,?,?,?,?)
                ''', (layout.get('layout_id'), layout.get('layout_name'),
                      json.dumps(layout.get('config', {}), ensure_ascii=False),
                      layout.get('theme', 'default'), layout.get('is_active', 0)))
                result = {'success': True, 'message': '布局已保存', 'layout_id': layout.get('layout_id')}
            elif action == 'activate' and layout:
                cur.execute('UPDATE enh_frontend_layout SET is_active=0')
                cur.execute('UPDATE enh_frontend_layout SET is_active=1 WHERE layout_id=?', (layout.get('layout_id'),))
                result = {'success': True, 'message': '布局已激活', 'layout_id': layout.get('layout_id')}
            elif action == 'delete' and layout:
                cur.execute('DELETE FROM enh_frontend_layout WHERE layout_id=?', (layout.get('layout_id'),))
                result = {'success': True, 'message': '布局已删除'}
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"布局配置管理失败[{action}]: {e}")
            return {'success': False, 'error': str(e)}

    def manage_themes(self, action: str = 'list', theme: Optional[Dict] = None) -> Dict[str, Any]:
        """主题管理"""
        self._touch('frontend_layout')
        try:
            conn = self._connect('frontend')
            if not conn:
                return {'success': False, 'error': '无法连接系统库'}
            cur = conn.cursor()
            result = {}
            if action == 'list':
                cur.execute('SELECT layout_id, layout_name, theme, is_active FROM enh_frontend_layout')
                result = {'success': True, 'themes': [dict(r) for r in cur.fetchall()]}
            elif action == 'apply' and theme:
                cur.execute('UPDATE enh_frontend_layout SET theme=? WHERE layout_id=?',
                            (theme.get('theme', 'default'), theme.get('layout_id')))
                result = {'success': True, 'message': '主题已应用', 'layout_id': theme.get('layout_id')}
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"主题管理失败[{action}]: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 10. Git自动同步 ====================
    def detect_changes(self, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """变更检测"""
        self._touch('git_sync')
        try:
            repo = repo_path or self.app_root
            if not os.path.isdir(os.path.join(repo, '.git')):
                return {'success': False, 'error': '不是Git仓库', 'repo_path': repo}
            result = subprocess.run(
                ['git', 'status', '--porcelain'], cwd=repo,
                capture_output=True, text=True, timeout=30,
            )
            changes = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            branch = subprocess.run(
                ['git', 'branch', '--show-current'], cwd=repo,
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            return {
                'success': True, 'repo_path': repo, 'branch': branch,
                'change_count': len(changes), 'changes': changes,
            }
        except Exception as e:
            logger.error(f"变更检测失败: {e}")
            return {'success': False, 'error': str(e)}

    def auto_commit(self, message: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """自动提交"""
        self._touch('git_sync')
        try:
            repo = repo_path or self.app_root
            detection = self.detect_changes(repo)
            if not detection.get('success') or detection['change_count'] == 0:
                return {'success': False, 'error': '无变更或仓库不可用'}
            subprocess.run(['git', 'add', '-A'], cwd=repo, capture_output=True, timeout=60)
            commit_msg = message or f"自动提交 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg], cwd=repo,
                capture_output=True, text=True, timeout=60,
            )
            committed = result.returncode == 0
            return {
                'success': committed, 'message': commit_msg,
                'output': result.stdout.strip(), 'error': result.stderr.strip() if not committed else '',
            }
        except Exception as e:
            logger.error(f"自动提交失败: {e}")
            return {'success': False, 'error': str(e)}

    def auto_push(self, remote: str = 'origin', branch: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """自动推送"""
        self._touch('git_sync')
        try:
            repo = repo_path or self.app_root
            if not branch:
                branch = subprocess.run(
                    ['git', 'branch', '--show-current'], cwd=repo,
                    capture_output=True, text=True, timeout=10,
                ).stdout.strip()
            result = subprocess.run(
                ['git', 'push', remote, branch], cwd=repo,
                capture_output=True, text=True, timeout=120,
            )
            pushed = result.returncode == 0
            return {
                'success': pushed, 'remote': remote, 'branch': branch,
                'output': result.stdout.strip(), 'error': result.stderr.strip() if not pushed else '',
            }
        except Exception as e:
            logger.error(f"自动推送失败: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # 统一状态接口
    # ============================================================
    def get_enhancement_status(self) -> Dict[str, Any]:
        """返回所有模块状态"""
        try:
            with self._lock:
                return {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'manager': 'SystemEnhancementManager',
                    'version': '1.0.0',
                    'split_db_dir': self.split_db_dir,
                    'module_count': len(self.module_status),
                    'modules': self.module_status,
                }
        except Exception as e:
            logger.error(f"获取增强状态失败: {e}")
            return {'success': False, 'error': str(e), 'modules': {}}


# 全局实例
system_enhancement_manager = SystemEnhancementManager()

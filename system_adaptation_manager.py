#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI系统适配与重启管理器 - System Adaptation and Restart Manager
MTSCOS AI Project v3.1
负责系统重启、加载新法则、初始化各模块适配
"""

import os
import sys
import json
import logging
import sqlite3
import hashlib
import time
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_adaptation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('system_adaptation')

class SystemStatus(Enum):
    """系统状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class RuleType(Enum):
    """法则类型"""
    SECURITY = "security"
    USER_BEHAVIOR = "user_behavior"
    DATA_SECURITY = "data_security"
    QUESTION_INCREMENT = "question_increment"
    AI_ADAPTIVE = "ai_adaptive"
    AI_HIGHDIM = "ai_highdim"
    PERMISSION_PRIORITY = "permission_priority"
    RULE_OPTIMIZER = "rule_optimizer"

@dataclass
class RuleInfo:
    """法则信息"""
    rule_id: str
    rule_type: RuleType
    name: str
    file_path: str
    version: str
    status: str
    last_loaded: str
    dependencies: List[str]

from dataclasses import dataclass, field

class SystemAdaptationManager:
    """系统适配管理器"""
    
    def __init__(self, db_path: str = "system_adaptation.db"):
        self.db_path = db_path
        self.system_status = SystemStatus.STOPPED
        self.loaded_rules = {}
        self.adapters = {}
        self._init_database()
        self._init_rule_registry()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_status (
                status_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_registry (
                rule_id TEXT PRIMARY KEY,
                rule_type TEXT NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                version TEXT DEFAULT '1.0.0',
                status TEXT DEFAULT 'unloaded',
                last_loaded TEXT,
                dependencies TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptation_logs (
                log_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                target TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_components (
                component_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                status TEXT,
                health_score REAL DEFAULT 0.0,
                last_check TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"系统适配数据库初始化完成: {self.db_path}")
    
    def _init_rule_registry(self):
        """初始化法则注册表"""
        rule_files = [
            {
                'rule_id': 'RULE-SEC-001',
                'rule_type': RuleType.SECURITY.value,
                'name': '系统安全法则',
                'file_path': 'security_rules.py',
                'version': '1.0.0',
                'dependencies': []
            },
            {
                'rule_id': 'RULE-UBH-001',
                'rule_type': RuleType.USER_BEHAVIOR.value,
                'name': '用户行为法则',
                'file_path': 'user_behavior.py',
                'version': '1.0.0',
                'dependencies': []
            },
            {
                'rule_id': 'RULE-DAT-001',
                'rule_type': RuleType.DATA_SECURITY.value,
                'name': '数据安全法则',
                'file_path': 'data_security.py',
                'version': '1.0.0',
                'dependencies': []
            },
            {
                'rule_id': 'RULE-QIN-001',
                'rule_type': RuleType.QUESTION_INCREMENT.value,
                'name': '习题题库增量法则',
                'file_path': 'question_increment_rules.py',
                'version': '1.0.0',
                'dependencies': []
            },
            {
                'rule_id': 'RULE-AAD-001',
                'rule_type': RuleType.AI_ADAPTIVE.value,
                'name': 'AI自适应学习升级法则',
                'file_path': 'ai_adaptive_learning_rules.py',
                'version': '1.0.0',
                'dependencies': []
            },
            {
                'rule_id': 'RULE-AHD-001',
                'rule_type': RuleType.AI_HIGHDIM.value,
                'name': 'AI高维适配法则',
                'file_path': 'ai_highdim_adaptation_rules.py',
                'version': '1.0.0',
                'dependencies': ['RULE-AAD-001']
            },
            {
                'rule_id': 'RULE-PRP-001',
                'rule_type': RuleType.PERMISSION_PRIORITY.value,
                'name': '系统权限优先判定法则',
                'file_path': 'permission_priority_rules.py',
                'version': '1.0.0',
                'dependencies': ['RULE-SEC-001']
            },
            {
                'rule_id': 'RULE-OPT-001',
                'rule_type': RuleType.RULE_OPTIMIZER.value,
                'name': 'AI法则自动优化强化系统',
                'file_path': 'ai_rule_optimizer.py',
                'version': '1.0.0',
                'dependencies': []
            }
        ]
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        for rule in rule_files:
            cursor.execute("SELECT rule_id FROM rule_registry WHERE rule_id = ?", (rule['rule_id'],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO rule_registry
                    (rule_id, rule_type, name, file_path, version, status, dependencies)
                    VALUES (?, ?, ?, ?, ?, 'unloaded', ?)
                """, (
                    rule['rule_id'],
                    rule['rule_type'],
                    rule['name'],
                    rule['file_path'],
                    rule['version'],
                    json.dumps(rule['dependencies'])
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"法则注册表初始化完成: {len(rule_files)} 个法则")
    
    def update_system_status(self, status: SystemStatus, details: str = None):
        """更新系统状态"""
        self.system_status = status
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        status_id = f"STS-{int(time.time())}-{secrets.token_hex(3)}"
        cursor.execute("""
            INSERT INTO system_status (status_id, status, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (status_id, status.value, datetime.now().isoformat(), details))
        
        conn.commit()
        conn.close()
        
        logger.info(f"系统状态已更新: {status.value}")
    
    def load_rule(self, rule_id: str) -> bool:
        """加载单个法则"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM rule_registry WHERE rule_id = ?", (rule_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            logger.error(f"法则不存在: {rule_id}")
            return False
        
        columns = ['rule_id', 'rule_type', 'name', 'file_path', 'version', 'status', 'last_loaded', 'dependencies', 'metadata']
        rule_info = dict(zip(columns, row))
        
        file_path = rule_info['file_path']
        if not os.path.exists(file_path):
            conn.close()
            logger.error(f"法则文件不存在: {file_path}")
            return False
        
        try:
            spec = __import__(file_path.replace('.py', ''))
            
            if hasattr(spec, 'AIAdaptiveLearningSystem'):
                self.adapters[rule_id] = spec.AIAdaptiveLearningSystem()
            elif hasattr(spec, 'HighDimensionalAdapter'):
                self.adapters[rule_id] = spec.HighDimensionalAdapter()
            elif hasattr(spec, 'PermissionPriorityEngine'):
                self.adapters[rule_id] = spec.PermissionPriorityEngine()
            elif hasattr(spec, 'AIRuleOptimizer'):
                self.adapters[rule_id] = spec.AIRuleOptimizer()
            elif hasattr(spec, 'DataSecuritySystem'):
                self.adapters[rule_id] = spec.DataSecuritySystem()
            elif hasattr(spec, 'QuestionIncrementSystem'):
                self.adapters[rule_id] = spec.QuestionIncrementSystem()
            elif hasattr(spec, 'SecurityRuleEngine'):
                self.adapters[rule_id] = spec.SecurityRuleEngine()
            elif hasattr(spec, 'UserBehaviorSystem'):
                self.adapters[rule_id] = spec.UserBehaviorSystem()
            else:
                logger.warning(f"法则无可识别的适配器类: {rule_id}")
            
            cursor.execute("""
                UPDATE rule_registry 
                SET status = 'loaded', last_loaded = ?
                WHERE rule_id = ?
            """, (datetime.now().isoformat(), rule_id))
            
            self.loaded_rules[rule_id] = rule_info
            self._log_adaptation(f"LOAD_RULE", rule_id, "success", f"已加载法则: {rule_info['name']}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"法则加载成功: {rule_id} - {rule_info['name']}")
            return True
            
        except Exception as e:
            cursor.execute("""
                UPDATE rule_registry SET status = 'error' WHERE rule_id = ?
            """, (rule_id,))
            conn.commit()
            conn.close()
            
            self._log_adaptation(f"LOAD_RULE", rule_id, "failed", str(e))
            logger.error(f"法则加载失败: {rule_id} - {e}")
            return False
    
    def unload_rule(self, rule_id: str) -> bool:
        """卸载单个法则"""
        if rule_id in self.loaded_rules:
            del self.loaded_rules[rule_id]
        
        if rule_id in self.adapters:
            del self.adapters[rule_id]
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE rule_registry SET status = 'unloaded' WHERE rule_id = ?
        """, (rule_id,))
        
        conn.commit()
        conn.close()
        
        self._log_adaptation(f"UNLOAD_RULE", rule_id, "success", f"已卸载法则: {rule_id}")
        logger.info(f"法则已卸载: {rule_id}")
        return True
    
    def _log_adaptation(self, action: str, target: str, status: str, details: str = None):
        """记录适配日志"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        log_id = f"LOG-{int(time.time())}-{secrets.token_hex(4)}"
        cursor.execute("""
            INSERT INTO adaptation_logs (log_id, action, target, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, action, target, status, details, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_rule_status(self, rule_id: str = None) -> Dict[str, Any]:
        """获取法则状态"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        if rule_id:
            cursor.execute("SELECT * FROM rule_registry WHERE rule_id = ?", (rule_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            columns = ['rule_id', 'rule_type', 'name', 'file_path', 'version', 'status', 'last_loaded', 'dependencies', 'metadata']
            return dict(zip(columns, row))
        else:
            cursor.execute("SELECT * FROM rule_registry")
            rows = cursor.fetchall()
            conn.close()
            
            columns = ['rule_id', 'rule_type', 'name', 'file_path', 'version', 'status', 'last_loaded', 'dependencies', 'metadata']
            return [dict(zip(columns, row)) for row in rows]
    
    def check_dependencies(self, rule_id: str) -> Dict[str, Any]:
        """检查法则依赖"""
        rule = self.get_rule_status(rule_id)
        if not rule:
            return {'valid': False, 'error': '法则不存在'}
        
        dependencies = json.loads(rule['dependencies']) if rule['dependencies'] else []
        missing_deps = []
        unloaded_deps = []
        
        for dep_id in dependencies:
            dep = self.get_rule_status(dep_id)
            if not dep:
                missing_deps.append(dep_id)
            elif dep['status'] != 'loaded':
                unloaded_deps.append(dep_id)
        
        return {
            'valid': len(missing_deps) == 0 and len(unloaded_deps) == 0,
            'missing_dependencies': missing_deps,
            'unloaded_dependencies': unloaded_deps
        }
    
    def start_system(self) -> Dict[str, Any]:
        """启动系统"""
        logger.info("=" * 70)
        logger.info("🚀 正在启动MTSCOS AI系统...")
        self.update_system_status(SystemStatus.STARTING, "系统启动中")
        
        start_time = time.time()
        
        rules = self.get_rule_status()
        load_order = []
        failed_loads = []
        
        for rule in rules:
            deps = self.check_dependencies(rule['rule_id'])
            if deps['valid']:
                load_order.append(rule)
        
        load_order.sort(key=lambda r: len(json.loads(r['dependencies']) if r['dependencies'] else []))
        
        for rule in load_order:
            rule_id = rule['rule_id']
            logger.info(f"正在加载: {rule['name']} ({rule_id})...")
            
            if self.load_rule(rule_id):
                logger.info(f"✅ {rule['name']} 加载成功")
            else:
                logger.error(f"❌ {rule['name']} 加载失败")
                failed_loads.append(rule_id)
        
        self._register_components()
        
        elapsed = time.time() - start_time
        
        if len(failed_loads) == 0:
            self.update_system_status(SystemStatus.RUNNING, f"系统启动完成，耗时{elapsed:.2f}秒")
            status = "success"
            message = f"系统启动成功！已加载 {len(self.loaded_rules)} 个法则，耗时 {elapsed:.2f} 秒"
        else:
            self.update_system_status(SystemStatus.ERROR, f"系统启动完成但有{len(failed_loads)}个法则加载失败")
            status = "partial"
            message = f"系统启动完成，但 {len(failed_loads)} 个法则加载失败"
        
        self._log_adaptation("SYSTEM_START", "all", status, message)
        
        logger.info("=" * 70)
        logger.info(f"✅ {message}")
        logger.info("=" * 70)
        
        return {
            'status': status,
            'loaded_count': len(self.loaded_rules),
            'failed_count': len(failed_loads),
            'failed_rules': failed_loads,
            'elapsed_time': elapsed,
            'loaded_rules': list(self.loaded_rules.keys())
        }
    
    def stop_system(self) -> Dict[str, Any]:
        """停止系统"""
        logger.info("正在停止系统...")
        self.update_system_status(SystemStatus.STOPPING, "系统停止中")
        
        for rule_id in list(self.loaded_rules.keys()):
            self.unload_rule(rule_id)
        
        self._log_adaptation("SYSTEM_STOP", "all", "success", "系统已停止")
        
        self.update_system_status(SystemStatus.STOPPED, "系统已停止")
        logger.info("✅ 系统已停止")
        
        return {
            'status': 'success',
            'unloaded_count': len(self.loaded_rules)
        }
    
    def restart_system(self) -> Dict[str, Any]:
        """重启系统"""
        logger.info("=" * 70)
        logger.info("🔄 正在重启MTSCOS AI系统...")
        
        stop_result = self.stop_system()
        
        time.sleep(1)
        
        start_result = self.start_system()
        
        logger.info("=" * 70)
        logger.info("✅ 系统重启完成")
        logger.info("=" * 70)
        
        return {
            'stop_result': stop_result,
            'start_result': start_result
        }
    
    def reload_rule(self, rule_id: str) -> bool:
        """重新加载法则"""
        logger.info(f"正在重新加载法则: {rule_id}")
        
        self.unload_rule(rule_id)
        
        return self.load_rule(rule_id)
    
    def adapt_to_new_rules(self) -> Dict[str, Any]:
        """适配新法则"""
        logger.info("正在分析并适配新法则...")
        
        current_rules = self.get_rule_status()
        new_rules = [r for r in current_rules if r['status'] != 'loaded']
        
        adapted = []
        failed = []
        
        for rule in new_rules:
            deps = self.check_dependencies(rule['rule_id'])
            
            if not deps['valid']:
                for dep_id in deps['missing_dependencies']:
                    if not self.load_rule(dep_id):
                        failed.append({'rule': rule['rule_id'], 'error': f'依赖缺失: {dep_id}'})
                        continue
            
            for dep_id in deps['unloaded_dependencies']:
                self.load_rule(dep_id)
            
            if self.load_rule(rule['rule_id']):
                adapted.append(rule['rule_id'])
            else:
                failed.append({'rule': rule['rule_id'], 'error': '加载失败'})
        
        self._log_adaptation("ADAPT_NEW_RULES", "all", "completed", 
                            f"已适配 {len(adapted)} 个新法则")
        
        return {
            'adapted_count': len(adapted),
            'failed_count': len(failed),
            'adapted_rules': adapted,
            'failed_rules': failed
        }
    
    def _register_components(self):
        """注册系统组件"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        components = [
            {'component_id': 'COMP-CORE', 'name': '核心系统', 'type': 'core', 'status': 'running'},
            {'component_id': 'COMP-DB', 'name': '数据库', 'type': 'infrastructure', 'status': 'running'},
            {'component_id': 'COMP-API', 'name': 'API网关', 'type': 'service', 'status': 'running'},
            {'component_id': 'COMP-SEC', 'name': '安全模块', 'type': 'security', 'status': 'running'},
            {'component_id': 'COMP-AI', 'name': 'AI引擎', 'type': 'ai', 'status': 'running'}
        ]
        
        for comp in components:
            cursor.execute("""
                INSERT OR REPLACE INTO system_components
                (component_id, name, type, status, health_score, last_check)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                comp['component_id'],
                comp['name'],
                comp['type'],
                comp['status'],
                1.0,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM system_components")
        components = cursor.fetchall()
        
        cursor.execute("SELECT status, COUNT(*) FROM rule_registry GROUP BY status")
        rule_stats = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM adaptation_logs WHERE timestamp > datetime('now', '-1 hour')")
        recent_logs = cursor.fetchone()[0]
        
        conn.close()
        
        total_rules = sum(rule_stats.values())
        loaded_rules = rule_stats.get('loaded', 0)
        
        health_score = (loaded_rules / total_rules * 0.6 + 
                       recent_logs / 100 * 0.4) if total_rules > 0 else 0.0
        
        return {
            'system_status': self.system_status.value,
            'health_score': round(health_score, 2),
            'total_rules': total_rules,
            'loaded_rules': loaded_rules,
            'unloaded_rules': rule_stats.get('unloaded', 0),
            'error_rules': rule_stats.get('error', 0),
            'recent_activity': recent_logs,
            'components': [
                {
                    'component_id': c[0],
                    'name': c[1],
                    'type': c[2],
                    'status': c[3],
                    'health_score': c[4]
                } for c in components
            ]
        }
    
    def get_adaptation_history(self, limit: int = 50) -> List[Dict]:
        """获取适配历史"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM adaptation_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['log_id', 'action', 'target', 'status', 'details', 'timestamp']
        return [dict(zip(columns, row)) for row in rows]

def main():
    """测试主函数"""
    print("\n" + "=" * 70)
    print("🤖 MTSCOS AI系统适配与重启管理器")
    print("=" * 70)
    
    manager = SystemAdaptationManager()
    
    print("\n📊 系统当前状态:")
    health = manager.get_system_health()
    print(f"  系统状态: {health['system_status']}")
    print(f"  健康评分: {health['health_score']:.2%}")
    print(f"  法则总数: {health['total_rules']}")
    print(f"  已加载: {health['loaded_rules']}")
    print(f"  未加载: {health['unloaded_rules']}")
    print(f"  错误: {health['error_rules']}")
    
    print("\n📋 法则列表:")
    rules = manager.get_rule_status()
    for rule in rules:
        status_icon = "✅" if rule['status'] == 'loaded' else "❌" if rule['status'] == 'error' else "⏸️"
        print(f"  {status_icon} [{rule['rule_id']}] {rule['name']} ({rule['version']})")
    
    print("\n🚀 执行系统启动...")
    start_result = manager.start_system()
    
    print(f"\n📊 启动结果:")
    print(f"  状态: {start_result['status']}")
    print(f"  已加载: {start_result['loaded_count']} 个法则")
    print(f"  失败: {start_result['failed_count']} 个法则")
    print(f"  耗时: {start_result['elapsed_time']:.2f} 秒")
    
    if start_result['failed_rules']:
        print(f"  失败的法则: {', '.join(start_result['failed_rules'])}")
    
    print("\n🏥 系统健康检查:")
    final_health = manager.get_system_health()
    print(f"  健康评分: {final_health['health_score']:.2%}")
    print(f"  活跃组件: {len([c for c in final_health['components'] if c['status'] == 'running'])}")
    
    print("\n📝 最近适配历史:")
    history = manager.get_adaptation_history(limit=10)
    for log in history[:5]:
        print(f"  [{log['timestamp'][:19]}] {log['action']} - {log['status']}")
    
    print("\n" + "=" * 70)
    print("✅ 系统适配与启动测试完成")
    print("=" * 70)

if __name__ == '__main__':
    main()
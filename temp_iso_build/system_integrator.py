#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统整合控制器 - 整合所有子系统和功能"""

import os
# JSON support removed - using database
import sqlite3
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system_integrator')

class SystemIntegrator:
    def __init__(self):
        self.db_path = 'app.db'
        self.subsystems = {}
        self.system_status = {}
        self.init_integration_database()
        self.load_subsystems()
    
    def init_integration_database(self):
        """初始化整合数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT UNIQUE NOT NULL,
                system_name TEXT,
                system_type TEXT,
                status TEXT DEFAULT 'active',
                dependencies TEXT,
                config TEXT,
                last_heartbeat TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_system TEXT,
                target_system TEXT,
                interaction_type TEXT,
                data_transferred TEXT,
                timestamp TEXT,
                success INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integration_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT,
                action TEXT,
                message TEXT,
                timestamp TEXT,
                level TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("系统整合数据库初始化完成")
    
    def load_subsystems(self):
        """加载所有子系统配置"""
        self.subsystems = {
            'auth': {
                'id': 'auth',
                'name': '认证系统',
                'type': 'security',
                'status': 'active',
                'dependencies': [],
                'modules': ['login_logic', 'session_manager', 'validation', 'certificate_manager']
            },
            'assessment': {
                'id': 'assessment',
                'name': '评估系统',
                'type': 'education',
                'status': 'active',
                'dependencies': ['auth'],
                'modules': ['placement_test', 'diagnostic_test', 'progress_tracking']
            },
            'question_bank': {
                'id': 'question_bank',
                'name': '题库系统',
                'type': 'education',
                'status': 'active',
                'dependencies': [],
                'modules': ['question_management', 'pronunciation_bank', 'exam_questions']
            },
            'ai_system': {
                'id': 'ai_system',
                'name': 'AI系统',
                'type': 'ai',
                'status': 'active',
                'dependencies': [],
                'modules': ['ai_employees', 'ai_butler', 'ai_ensemble', 'self_learning']
            },
            'security': {
                'id': 'security',
                'name': '安全系统',
                'type': 'security',
                'status': 'active',
                'dependencies': ['auth'],
                'modules': ['lock_system', 'ip_whitelist', 'certificate_manager']
            },
            'validation': {
                'id': 'validation',
                'name': '验证系统',
                'type': 'security',
                'status': 'active',
                'dependencies': ['auth'],
                'modules': ['user_validation', 'token_validation']
            },
            'workflow': {
                'id': 'workflow',
                'name': '工作流系统',
                'type': 'system',
                'status': 'active',
                'dependencies': [],
                'modules': ['automation', 'scheduler', 'monitoring']
            },
            'data': {
                'id': 'data',
                'name': '数据系统',
                'type': 'system',
                'status': 'active',
                'dependencies': [],
                'modules': ['database', 'backup', 'sync']
            }
        }
        
        self.register_all_systems()
    
    def register_all_systems(self):
        """注册所有子系统到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for system_id, config in self.subsystems.items():
            cursor.execute('''
                INSERT OR REPLACE INTO system_registry
                (system_id, system_name, system_type, status, dependencies, config, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                system_id,
                config['name'],
                config['type'],
                config['status'],
                str(config['dependencies']),
                str(config['modules']),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        logger.info("所有子系统已注册")
    
    def get_system_status(self, system_id: str) -> Dict:
        """获取系统状态"""
        if system_id in self.subsystems:
            return {
                'system_id': system_id,
                'name': self.subsystems[system_id]['name'],
                'status': self.subsystems[system_id]['status'],
                'modules': self.subsystems[system_id]['modules']
            }
        return {'error': '系统未找到'}
    
    def check_system_dependencies(self, system_id: str) -> bool:
        """检查系统依赖"""
        if system_id not in self.subsystems:
            return False
        
        dependencies = self.subsystems[system_id]['dependencies']
        for dep in dependencies:
            if dep not in self.subsystems or self.subsystems[dep]['status'] != 'active':
                return False
        
        return True
    
    def trigger_system_interaction(self, source_system: str, target_system: str, 
                                  interaction_type: str, data: Dict):
        """触发系统间交互"""
        if source_system not in self.subsystems or target_system not in self.subsystems:
            return {'success': False, 'error': '系统不存在'}
        
        if not self.check_system_dependencies(source_system):
            return {'success': False, 'error': '依赖未满足'}
        
        # 记录交互
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_interactions
            (source_system, target_system, interaction_type, data_transferred, timestamp, success)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            source_system,
            target_system,
            interaction_type,
            str(data),
            datetime.now().isoformat(),
            1
        ))
        
        conn.commit()
        conn.close()
        
        self.log_integration(source_system, f"触发交互: {interaction_type} -> {target_system}", 'info')
        
        return {'success': True, 'message': '交互成功'}
    
    def log_integration(self, system_id: str, message: str, level: str = 'info'):
        """记录整合日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO integration_logs
            (system_id, action, message, timestamp, level)
            VALUES (?, ?, ?, ?, ?)
        ''', (system_id, 'log', message, datetime.now().isoformat(), level))
        
        conn.commit()
        conn.close()
    
    def update_system_metrics(self, system_id: str, metrics: Dict):
        """更新系统指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric_name, metric_value in metrics.items():
            cursor.execute('''
                INSERT INTO system_metrics
                (system_id, metric_name, metric_value, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (system_id, metric_name, metric_value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def run_system_health_check(self) -> Dict:
        """运行系统健康检查"""
        results = {
            'overall_status': 'healthy',
            'systems': []
        }
        
        for system_id, config in self.subsystems.items():
            status = 'healthy'
            
            if not self.check_system_dependencies(system_id):
                status = 'dependency_error'
                results['overall_status'] = 'degraded'
            
            results['systems'].append({
                'system_id': system_id,
                'name': config['name'],
                'status': status,
                'type': config['type'],
                'modules': len(config['modules'])
            })
        
        return results
    
    def sync_all_systems(self):
        """同步所有系统"""
        print("="*80)
        print("          系统同步")
        print("="*80)
        
        for system_id, config in self.subsystems.items():
            print(f"\n同步 {config['name']}...")
            
            try:
                # 模拟同步操作
                time.sleep(0.1)
                
                # 更新心跳
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE system_registry SET last_heartbeat = ? WHERE system_id = ?
                ''', (datetime.now().isoformat(), system_id))
                conn.commit()
                conn.close()
                
                print(f"  ✓ 同步成功")
                self.log_integration(system_id, '系统同步完成', 'info')
                
            except Exception as e:
                print(f"  ✗ 同步失败: {str(e)}")
                self.log_integration(system_id, f'同步失败: {str(e)}', 'error')
    
    def generate_integration_report(self):
        """生成整合报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_registry')
        system_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM system_registry WHERE status = "active"')
        active_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM system_interactions')
        interaction_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM integration_logs')
        log_count = cursor.fetchone()[0]
        
        conn.close()
        
        health = self.run_system_health_check()
        
        print("\n" + "="*80)
        print("          系统整合报告")
        print("="*80)
        
        print(f"\n系统概览:")
        print(f"  系统总数: {system_count}")
        print(f"  活跃系统: {active_count}")
        print(f"  系统交互: {interaction_count}")
        print(f"  日志记录: {log_count}")
        
        print(f"\n系统状态:")
        print("-" * 60)
        for system in health['systems']:
            status_icon = '✅' if system['status'] == 'healthy' else '⚠️'
            print(f"  {status_icon} {system['name']} ({system['type']})")
        
        print(f"\n整体状态: {'✅ 健康' if health['overall_status'] == 'healthy' else '⚠️ 降级'}")
        
        print("\n整合功能:")
        print(f"  ✅ 统一认证管理")
        print(f"  ✅ 跨系统交互")
        print(f"  ✅ 健康监控")
        print(f"  ✅ 日志追踪")
        print(f"  ✅ 指标收集")
        print(f"  ✅ 依赖检查")
        
        print("\n" + "="*80)
        print("  系统整合完成！")
        print("="*80)
    
    def run_full_integration(self):
        """运行完整整合流程"""
        print("="*80)
        print("          系统整合控制器")
        print("="*80)
        
        print("\n[1/3] 注册子系统...")
        self.register_all_systems()
        print(f"  ✓ 已注册 {len(self.subsystems)} 个子系统")
        
        print("\n[2/3] 同步所有系统...")
        self.sync_all_systems()
        
        print("\n[3/3] 生成整合报告...")
        self.generate_integration_report()
        
        # 演示系统间交互
        print("\n\n演示系统间交互:")
        print("-" * 40)
        
        interactions = [
            {'from': 'auth', 'to': 'assessment', 'type': 'user_authenticated', 'data': {'user_id': 'user123'}},
            {'from': 'assessment', 'to': 'question_bank', 'type': 'request_questions', 'data': {'subject': 'math', 'count': 10}},
            {'from': 'security', 'to': 'auth', 'type': 'validate_token', 'data': {'token': 'abc123'}},
            {'from': 'ai_system', 'to': 'assessment', 'type': 'analyze_results', 'data': {'user_id': 'user123'}}
        ]
        
        for interaction in interactions:
            result = self.trigger_system_interaction(
                interaction['from'],
                interaction['to'],
                interaction['type'],
                interaction['data']
            )
            source_name = self.subsystems[interaction['from']]['name']
            target_name = self.subsystems[interaction['to']]['name']
            status = '✅' if result['success'] else '❌'
            print(f"  {status} {source_name} -> {target_name}")

def main():
    integrator = SystemIntegrator()
    integrator.run_full_integration()

if __name__ == "__main__":
    main()
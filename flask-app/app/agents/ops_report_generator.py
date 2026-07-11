# -*- coding: utf-8 -*-
"""
运维报告生成器 - 每日报告、审批日志、操作日志
自动生成运维报告并上传数据库
"""
import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class OpsReportGenerator:
    """运维报告生成器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        
        self._init_database()
        self._start_report_thread()
        
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ops_reports (
                    report_id TEXT PRIMARY KEY,
                    report_date TEXT NOT NULL,
                    report_type TEXT NOT NULL DEFAULT 'daily',
                    status TEXT NOT NULL DEFAULT 'generated',
                    content TEXT DEFAULT '{}',
                    created_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[运维报告] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[运维报告] 初始化数据库失败: {e}")
    
    def _start_report_thread(self):
        """启动定时报告线程"""
        def report_loop():
            while True:
                try:
                    now = datetime.now()
                    if now.hour == 2 and now.minute == 0:
                        self.generate_daily_report()
                except Exception as e:
                    logger.error(f"[运维报告] 生成报告失败: {e}")
                time.sleep(60)
        
        thread = threading.Thread(target=report_loop, daemon=True)
        thread.start()
        logger.info("[运维报告] 定时报告线程已启动")
    
    def generate_daily_report(self) -> Dict:
        """生成每日运维报告"""
        report_date = datetime.now().strftime('%Y-%m-%d')
        report_id = f"report_{report_date}"
        
        report = {
            'report_id': report_id,
            'report_date': report_date,
            'report_type': 'daily',
            'status': 'generating',
            'content': {},
            'created_at': datetime.now().isoformat()
        }
        
        try:
            report['content'] = self._collect_report_data()
            report['status'] = 'generated'
            
            self._save_report(report)
            logger.info(f"[运维报告] 每日报告生成完成: {report_date}")
            
        except Exception as e:
            report['status'] = 'failed'
            report['content'] = {'error': str(e)}
            self._save_report(report)
            logger.error(f"[运维报告] 生成每日报告失败: {e}")
        
        return report
    
    def _collect_report_data(self) -> Dict:
        """收集报告数据"""
        data = {}
        
        data['overview'] = self._collect_overview()
        data['system_metrics'] = self._collect_system_metrics()
        data['agent_status'] = self._collect_agent_status()
        data['approval_activity'] = self._collect_approval_activity()
        data['git_operations'] = self._collect_git_operations()
        data['test_results'] = self._collect_test_results()
        data['vulnerability_scans'] = self._collect_vulnerability_scans()
        data['iteration_plans'] = self._collect_iteration_plans()
        data['recommendations'] = self._generate_recommendations(data)
        
        return data
    
    def _collect_overview(self) -> Dict:
        """收集概览信息"""
        return {
            'report_time': datetime.now().isoformat(),
            'environment': 'production',
            'system_status': 'healthy'
        }
    
    def _collect_system_metrics(self) -> Dict:
        """收集系统指标"""
        metrics = {}
        
        try:
            import requests
            
            response = requests.get('http://localhost:8888/api/monitoring/system', timeout=5)
            if response.status_code == 200:
                data = response.json()['metrics']
                metrics = {
                    'cpu_usage': data['cpu']['usage_percent'],
                    'memory_usage': data['memory']['used_percent'],
                    'disk_usage': data['disk']['used_percent'],
                    'uptime_days': data['uptime']['days']
                }
        except Exception as e:
            logger.debug(f"[运维报告] 收集系统指标失败: {e}")
        
        return metrics
    
    def _collect_agent_status(self) -> Dict:
        """收集Agent状态"""
        agents = {}
        
        try:
            import requests
            
            response = requests.get('http://localhost:8888/api/core-agents/agents', timeout=5)
            if response.status_code == 200:
                agents = response.json()['agents']
        except Exception as e:
            logger.debug(f"[运维报告] 收集Agent状态失败: {e}")
        
        return agents
    
    def _collect_approval_activity(self) -> List[Dict]:
        """收集审批活动"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM approvals WHERE created_at LIKE ? ORDER BY created_at DESC
            ''', (f'{yesterday}%',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._format_approval(row) for row in rows]
        
        except Exception as e:
            logger.error(f"[运维报告] 收集审批活动失败: {e}")
            return []
    
    def _collect_git_operations(self) -> List[Dict]:
        """收集Git操作"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM git_operations WHERE created_at LIKE ? ORDER BY created_at DESC
            ''', (f'{yesterday}%',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._format_git_operation(row) for row in rows]
        
        except Exception as e:
            logger.error(f"[运维报告] 收集Git操作失败: {e}")
            return []
    
    def _collect_test_results(self) -> List[Dict]:
        """收集测试结果"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM test_results WHERE created_at LIKE ? ORDER BY created_at DESC
            ''', (f'{yesterday}%',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._format_test_result(row) for row in rows]
        
        except Exception as e:
            logger.error(f"[运维报告] 收集测试结果失败: {e}")
            return []
    
    def _collect_vulnerability_scans(self) -> List[Dict]:
        """收集漏洞扫描结果"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM vulnerability_scans WHERE scan_time LIKE ? ORDER BY scan_time DESC
            ''', (f'{yesterday}%',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._format_scan_result(row) for row in rows]
        
        except Exception as e:
            logger.error(f"[运维报告] 收集漏洞扫描失败: {e}")
            return []
    
    def _collect_iteration_plans(self) -> List[Dict]:
        """收集迭代计划"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT * FROM iteration_plans WHERE created_at LIKE ? ORDER BY created_at DESC
            ''', (f'{yesterday}%',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._format_iteration_plan(row) for row in rows]
        
        except Exception as e:
            logger.error(f"[运维报告] 收集迭代计划失败: {e}")
            return []
    
    def _generate_recommendations(self, data: Dict) -> List[str]:
        """生成建议"""
        recommendations = []
        
        metrics = data.get('system_metrics', {})
        if metrics.get('cpu_usage', 0) > 80:
            recommendations.append("CPU使用率过高，建议优化性能或增加资源")
        if metrics.get('memory_usage', 0) > 85:
            recommendations.append("内存使用率过高，建议清理缓存或增加内存")
        
        agent_status = data.get('agent_status', {})
        for agent_id, agent in agent_status.items():
            if agent.get('status') != 'idle':
                recommendations.append(f"Agent {agent.get('agent_name')} 状态异常，建议检查")
        
        scans = data.get('vulnerability_scans', [])
        for scan in scans:
            if scan.get('critical_count', 0) > 0:
                recommendations.append(f"检测到 {scan['critical_count']} 个高危漏洞，建议立即处理")
        
        return recommendations
    
    def _format_approval(self, row) -> Dict:
        return {
            'approval_id': row[0],
            'operation_type': row[1],
            'operation_level': row[2],
            'status': row[3],
            'description': row[6],
            'created_at': row[8]
        }
    
    def _format_git_operation(self, row) -> Dict:
        return {
            'op_id': row[0],
            'operation_type': row[1],
            'branch': row[2],
            'commit_hash': row[3],
            'status': row[5],
            'created_at': row[8]
        }
    
    def _format_test_result(self, row) -> Dict:
        return {
            'test_id': row[0],
            'test_type': row[1],
            'status': row[2],
            'passed': row[4],
            'failed': row[5],
            'duration': row[7],
            'created_at': row[13]
        }
    
    def _format_scan_result(self, row) -> Dict:
        return {
            'scan_id': row[0],
            'scan_time': row[1],
            'total_packages': row[3],
            'vulnerable_packages': row[4],
            'critical_count': row[5],
            'high_count': row[6]
        }
    
    def _format_iteration_plan(self, row) -> Dict:
        return {
            'plan_id': row[0],
            'status': row[1],
            'iteration_type': row[2],
            'priority': row[3],
            'created_at': row[8]
        }
    
    def _save_report(self, report: Dict):
        """保存报告"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ops_reports VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report['report_id'],
                report['report_date'],
                report['report_type'],
                report['status'],
                json.dumps(report['content'], ensure_ascii=False),
                report['created_at']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[运维报告] 保存报告失败: {e}")
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """获取报告"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM ops_reports WHERE report_id = ?', (report_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'report_id': row[0],
                    'report_date': row[1],
                    'report_type': row[2],
                    'status': row[3],
                    'content': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                }
            
            return None
        except Exception as e:
            logger.error(f"[运维报告] 获取报告失败: {e}")
            return None
    
    def get_all_reports(self) -> List[Dict]:
        """获取所有报告"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM ops_reports ORDER BY report_date DESC LIMIT 30')
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'report_id': row[0],
                    'report_date': row[1],
                    'report_type': row[2],
                    'status': row[3],
                    'content': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                })
            
            conn.close()
            return results
        
        except Exception as e:
            logger.error(f"[运维报告] 获取报告列表失败: {e}")
            return []


def get_report_generator() -> OpsReportGenerator:
    """获取运维报告生成器单例"""
    return OpsReportGenerator()


def init_report_generator():
    """初始化运维报告生成器"""
    generator = get_report_generator()
    logger.info("[运维报告] 运维报告生成器初始化完成")
    return generator
# -*- coding: utf-8 -*-
"""
OpsInspectionAgent - 运维巡检Agent
定期检查系统运行状态，生成运维报告
"""
import json
import logging
import os
import psutil
import sqlite3
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base_core_agent import BaseCoreAgent

logger = logging.getLogger(__name__)


class OpsInspectionAgent(BaseCoreAgent):
    """运维巡检Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id='core_ops_inspection',
            agent_name='运维巡检Agent',
            agent_type='ops_inspection'
        )
        self.inspection_count = 0
        self.last_report_time = None
    
    def inspect_system(self) -> Dict:
        """执行系统巡检"""
        results = {}
        
        results['system_info'] = self._get_system_info()
        results['resource_usage'] = self._get_resource_usage()
        results['database_status'] = self._check_database()
        results['service_status'] = self._check_services()
        results['network_status'] = self._check_network()
        results['disk_status'] = self._check_disk()
        results['security_check'] = self._security_check()
        
        return results
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            'hostname': socket.gethostname(),
            'platform': os.name,
            'cpu_count': psutil.cpu_count(),
            'memory_total': f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    def _get_resource_usage(self) -> Dict:
        """获取资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': f"{memory.available / (1024**3):.2f} GB",
            'disk_used_percent': disk.percent,
            'disk_available': f"{disk.free / (1024**3):.2f} GB",
            'load_avg': os.getloadavg()
        }
    
    def _check_database(self) -> Dict:
        """检查数据库状态"""
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            db_size = os.path.getsize(db_path) / (1024 ** 2)
            
            conn.close()
            
            return {
                'status': 'healthy',
                'path': db_path,
                'size_mb': round(db_size, 2),
                'table_count': table_count,
                'tables': tables[:10]
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _check_services(self) -> Dict:
        """检查服务状态"""
        services = {}
        
        services['flask_app'] = self._check_port(8888)
        services['agent_manager'] = self._check_agent_manager()
        services['rule_engine'] = self._check_rule_engine()
        
        return services
    
    def _check_port(self, port: int) -> Dict:
        """检查端口是否在监听"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', port))
                return {
                    'port': port,
                    'status': 'running' if result == 0 else 'stopped'
                }
        except Exception as e:
            return {'port': port, 'status': 'error', 'message': str(e)}
    
    def _check_agent_manager(self) -> Dict:
        """检查Agent管理器状态"""
        try:
            from app.agents.agent_manager import get_agent_manager
            
            manager = get_agent_manager()
            if manager:
                return {'status': 'running', 'agent_count': manager.get_agent_count()}
            return {'status': 'not_initialized'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_rule_engine(self) -> Dict:
        """检查规则引擎状态"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if engine:
                status = engine.get_status()
                return {
                    'status': 'running' if status.get('monitor_running') else 'stopped',
                    'rule_count': status.get('total_rules', 0)
                }
            return {'status': 'not_initialized'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_network(self) -> Dict:
        """检查网络状态"""
        try:
            public_ip = self._get_public_ip()
            interfaces = []
            
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces.append({
                            'interface': iface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
            
            return {
                'public_ip': public_ip,
                'interfaces': interfaces,
                'status': 'healthy'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_public_ip(self) -> str:
        """获取公网IP"""
        try:
            import urllib.request
            with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                return response.read().decode('utf-8')
        except Exception:
            return 'unknown'
    
    def _check_disk(self) -> Dict:
        """检查磁盘状态"""
        partitions = []
        
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': usage.percent
                })
            except Exception:
                pass
        
        return {'partitions': partitions}
    
    def _security_check(self) -> Dict:
        """安全检查"""
        issues = []
        
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        if os.path.exists(db_path):
            perms = oct(os.stat(db_path).st_mode)[-3:]
            if perms != '600':
                issues.append(f"数据库文件权限不安全: {perms} (建议600)")
        
        return {
            'issues': issues,
            'status': 'warning' if issues else 'healthy'
        }
    
    def generate_report(self, inspection_results: Dict) -> Dict:
        """生成巡检报告"""
        risk_level = 'low'
        warnings = []
        
        resource = inspection_results.get('resource_usage', {})
        if resource.get('cpu_percent', 0) > 80:
            warnings.append('CPU使用率过高')
            risk_level = 'high'
        if resource.get('memory_percent', 0) > 85:
            warnings.append('内存使用率过高')
            risk_level = 'high'
        if resource.get('disk_used_percent', 0) > 90:
            warnings.append('磁盘空间不足')
            risk_level = 'high'
        
        db_status = inspection_results.get('database_status', {})
        if db_status.get('status') != 'healthy':
            warnings.append('数据库状态异常')
            risk_level = 'high'
        
        service_status = inspection_results.get('service_status', {})
        for service, status in service_status.items():
            if status.get('status') == 'stopped':
                warnings.append(f"{service}服务未运行")
                risk_level = 'medium'
        
        return {
            'report_id': self.generate_task_id(),
            'generated_at': datetime.now().isoformat(),
            'risk_level': risk_level,
            'warnings': warnings,
            'summary': inspection_results,
            'recommendations': self._generate_recommendations(warnings)
        }
    
    def _generate_recommendations(self, warnings: List[str]) -> List[str]:
        """生成运维建议"""
        recommendations = []
        
        for warning in warnings:
            if 'CPU' in warning:
                recommendations.append('考虑优化代码或增加CPU资源')
            if '内存' in warning:
                recommendations.append('考虑释放内存或增加内存资源')
            if '磁盘' in warning:
                recommendations.append('清理磁盘空间或扩大磁盘容量')
            if '数据库' in warning:
                recommendations.append('检查数据库连接和运行状态')
            if '服务' in warning:
                recommendations.append('启动相关服务')
        
        return recommendations
    
    def execute(self, context: Dict = None) -> Dict:
        """执行运维巡检"""
        task_id = self.generate_task_id()
        self.status = 'running'
        self.heartbeat()
        
        try:
            inspection_results = self.inspect_system()
            report = self.generate_report(inspection_results)
            
            self.inspection_count += 1
            self.last_report_time = datetime.now()
            
            self.report_to_db(task_id, 'completed', {
                'inspection_results': inspection_results,
                'report': report
            })
            
            self.record_task(task_id, 'completed', {'risk_level': report.get('risk_level')})
            
            self.status = 'idle'
            
            return {
                'success': True,
                'task_id': task_id,
                'agent': self.agent_name,
                'inspection_results': inspection_results,
                'report': report
            }
        
        except Exception as e:
            return self.handle_error(e, task_id)

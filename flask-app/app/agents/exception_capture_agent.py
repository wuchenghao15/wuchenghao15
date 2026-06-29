# -*- coding: utf-8 -*-
"""
ExceptionCaptureAgent - 异常捕捉Agent
实时监控系统运行状态，捕捉各类异常并记录
"""
import json
import logging
import traceback
import sys
from datetime import datetime
from typing import Dict, Any

from .base_core_agent import BaseCoreAgent

logger = logging.getLogger(__name__)


class ExceptionCaptureAgent(BaseCoreAgent):
    """异常捕捉Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id='core_exception_capture',
            agent_name='异常捕捉Agent',
            agent_type='exception_capture'
        )
        self.error_count = 0
        self.warning_count = 0
        self.last_error_time = None
        self.register_exception_hook()
    
    def register_exception_hook(self):
        """注册全局异常钩子"""
        original_excepthook = sys.excepthook
        
        def custom_excepthook(exc_type, exc_value, exc_tb):
            error_info = {
                'type': exc_type.__name__,
                'message': str(exc_value),
                'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                'timestamp': datetime.now().isoformat()
            }
            self.capture_exception(error_info)
            original_excepthook(exc_type, exc_value, exc_tb)
        
        sys.excepthook = custom_excepthook
    
    def capture_exception(self, error_info: Dict):
        """捕捉异常并记录"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        task_id = self.generate_task_id()
        
        self.report_to_db(task_id, 'completed', {
            'error_info': error_info,
            'severity': self._determine_severity(error_info),
            'recommendation': self._generate_recommendation(error_info)
        })
        
        self.record_task(task_id, 'completed', {'error_type': error_info.get('type')})
        
        logger.warning(f"[{self.agent_name}] 捕捉到异常: {error_info['type']} - {error_info['message']}")
        
        self.trigger_rule('exception_detected', {
            'error_type': error_info['type'],
            'severity': self._determine_severity(error_info),
            'error_info': error_info
        })
    
    def _determine_severity(self, error_info: Dict) -> str:
        """确定异常严重级别"""
        error_type = error_info.get('type', '')
        
        critical_errors = ['OSError', 'MemoryError', 'ConnectionError', 'TimeoutError', 'SQLiteError']
        warning_errors = ['ValueError', 'TypeError', 'KeyError', 'IndexError']
        
        if any(err in error_type for err in critical_errors):
            return 'critical'
        elif any(err in error_type for err in warning_errors):
            return 'warning'
        return 'info'
    
    def _generate_recommendation(self, error_info: Dict) -> str:
        """生成修复建议"""
        error_type = error_info.get('type', '')
        
        recommendations = {
            'OSError': '检查文件权限和路径是否正确',
            'MemoryError': '系统内存不足，考虑优化内存使用或增加资源',
            'ConnectionError': '检查网络连接和服务可用性',
            'TimeoutError': '增加超时时间或优化网络请求',
            'SQLiteError': '检查数据库连接和SQL语句',
            'ValueError': '验证输入参数格式是否正确',
            'TypeError': '检查数据类型转换是否正确',
            'KeyError': '确保字典键存在',
            'IndexError': '检查列表索引范围'
        }
        
        return recommendations.get(error_type, '请检查相关代码逻辑')
    
    def execute(self, context: Dict = None) -> Dict:
        """执行异常扫描"""
        task_id = self.generate_task_id()
        self.status = 'running'
        self.heartbeat()
        
        try:
            scan_results = self._scan_recent_errors()
            
            self.report_to_db(task_id, 'completed', {
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'scan_results': scan_results,
                'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None
            })
            
            self.record_task(task_id, 'completed', {'scan_count': len(scan_results)})
            
            self.status = 'idle'
            
            return {
                'success': True,
                'task_id': task_id,
                'agent': self.agent_name,
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'scan_results': scan_results
            }
        
        except Exception as e:
            return self.handle_error(e, task_id)
    
    def _scan_recent_errors(self) -> list:
        """扫描最近的错误日志"""
        errors = []
        
        try:
            import sqlite3
            db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM error_logs ORDER BY created_at DESC LIMIT 20')
            rows = cursor.fetchall()
            
            for row in rows:
                errors.append({
                    'error_id': row[0],
                    'error_type': row[1],
                    'error_message': row[2],
                    'stack_trace': row[3],
                    'created_at': row[4]
                })
            
            conn.close()
        except Exception:
            pass
        
        return errors

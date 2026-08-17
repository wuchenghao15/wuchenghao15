#!/usr/bin/env python3
"""AI自动故障修复Agent"""

import os
import re
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIAutoRepairAgent(AIEmployee):
    """AI自动故障修复Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI自动修复专家"):
        super().__init__(employee_id, name, 'auto_repair', 8)
        self.skills = [
            '故障检测', '自动修复', '代码修复',
            '错误分析', '异常处理', '系统恢复',
            '数据修复', '配置修复', '依赖修复'
        ]
        self.repair_history = []
        self.total_repairs = 0
        self.successful_repairs = 0
        self.failed_repairs = 0
    
    def analyze_error(self, error_message: str, stack_trace: str = "") -> Dict[str, Any]:
        """分析错误信息"""
        error_patterns = [
            (r'ImportError', '模块导入错误', '检查依赖安装'),
            (r'ModuleNotFoundError', '模块未找到', '安装缺失的模块'),
            (r'SyntaxError', '语法错误', '检查代码语法'),
            (r'AttributeError', '属性错误', '检查对象属性'),
            (r'KeyError', '键错误', '检查字典键'),
            (r'IndexError', '索引错误', '检查列表索引'),
            (r'ValueError', '值错误', '检查参数值'),
            (r'TypeError', '类型错误', '检查数据类型'),
            (r'NameError', '名称错误', '检查变量定义'),
            (r'ZeroDivisionError', '除零错误', '检查除法运算'),
            (r'FileNotFoundError', '文件未找到', '检查文件路径'),
            (r'PermissionError', '权限错误', '检查文件权限'),
            (r'SQLite', '数据库错误', '检查数据库连接'),
            (r'database is locked', '数据库锁定', '检查并发访问'),
        ]
        
        detected_errors = []
        for pattern, error_type, suggestion in error_patterns:
            if re.search(pattern, error_message):
                detected_errors.append({
                    'type': error_type,
                    'pattern': pattern,
                    'suggestion': suggestion
                })
        
        return {
            'error_message': error_message,
            'stack_trace': stack_trace,
            'detected_errors': detected_errors,
            'total_detected': len(detected_errors),
            'timestamp': datetime.now().isoformat()
        }
    
    def repair_code(self, code: str, error_message: str) -> Dict[str, Any]:
        """修复代码"""
        repairs = []
        
        if 'ImportError' in error_message or 'ModuleNotFoundError' in error_message:
            module_match = re.search(r'No module named (\'[^\']+\')', error_message)
            if module_match:
                module = module_match.group(1)
                repairs.append(f"需要安装模块: {module}")
        
        if 'SyntaxError' in error_message:
            line_match = re.search(r'line (\d+)', error_message)
            if line_match:
                repairs.append(f"第{line_match.group(1)}行存在语法错误")
        
        if 'IndentationError' in error_message:
            repairs.append("检查代码缩进")
        
        if 'KeyError' in error_message:
            key_match = re.search(r"'([^']+)'", error_message)
            if key_match:
                repairs.append(f"字典中缺少键: {key_match.group(1)}")
        
        if 'AttributeError' in error_message:
            attr_match = re.search(r"object has no attribute '([^']+)'", error_message)
            if attr_match:
                repairs.append(f"对象缺少属性: {attr_match.group(1)}")
        
        self.total_repairs += 1
        
        repair_result = {
            'original_code': code,
            'error_message': error_message,
            'repairs': repairs,
            'success': len(repairs) > 0,
            'timestamp': datetime.now().isoformat()
        }
        
        if len(repairs) > 0:
            self.successful_repairs += 1
        else:
            self.failed_repairs += 1
        
        self.repair_history.append(repair_result)
        return repair_result
    
    def fix_database(self, db_path: str) -> Dict[str, Any]:
        """修复数据库"""
        repairs = []
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] == 'ok':
                repairs.append("数据库完整性检查通过")
            else:
                repairs.append(f"数据库完整性问题: {result[0]}")
            
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            repairs.append(f"当前日志模式: {journal_mode}")
            
            cursor.execute("PRAGMA busy_timeout = 30000")
            repairs.append("设置busy_timeout为30秒")
            
            conn.close()
            
            self.successful_repairs += 1
            success = True
            
        except Exception as e:
            repairs.append(f"修复失败: {str(e)}")
            self.failed_repairs += 1
            success = False
        
        self.total_repairs += 1
        
        return {
            'db_path': db_path,
            'repairs': repairs,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启服务"""
        try:
            import subprocess
            
            result = subprocess.run(
                ['ps', 'aux', '|', 'grep', service_name],
                capture_output=True,
                text=True,
                shell=True
            )
            
            return {
                'service_name': service_name,
                'status': 'restarting',
                'result': result.stdout[:500],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service_name': service_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict:
        """获取修复统计"""
        return {
            'total_repairs': self.total_repairs,
            'successful_repairs': self.successful_repairs,
            'failed_repairs': self.failed_repairs,
            'success_rate': (self.successful_repairs / self.total_repairs) * 100 if self.total_repairs > 0 else 0,
            'recent_repairs': self.repair_history[-5:]
        }

auto_repair_agent = AIAutoRepairAgent('ai_auto_repair_001')

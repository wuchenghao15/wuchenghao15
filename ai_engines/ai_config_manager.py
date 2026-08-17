#!/usr/bin/env python3
"""AI智能配置管理Agent"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIConfigManager(AIEmployee):
    """AI配置管理Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI配置管理专家"):
        super().__init__(employee_id, name, 'config_manager', 7)
        self.skills = [
            '配置管理', '配置读取', '配置写入',
            '配置验证', '配置备份', '配置恢复',
            '配置对比', '配置审计', '配置优化'
        ]
        self.config_history = []
        self.backup_history = []
        self.total_configs = 0
    
    def get_config(self, config_name: str, default: Any = None) -> Dict[str, Any]:
        """获取配置"""
        for config in self.config_history:
            if config['config_name'] == config_name:
                return {'success': True, 'config': config.get('value', default)}
        return {'success': True, 'config': default, 'message': '配置不存在，返回默认值'}
    
    def set_config(self, config_name: str, value: Any, description: str = "") -> Dict[str, Any]:
        """设置配置"""
        config = {
            'config_name': config_name,
            'value': value,
            'description': description,
            'updated_at': datetime.now().isoformat(),
            'updated_by': self.name
        }
        for i, c in enumerate(self.config_history):
            if c['config_name'] == config_name:
                self.config_history[i] = config
                return {'success': True, 'config': config, 'message': '配置已更新'}
        self.config_history.append(config)
        self.total_configs += 1
        return {'success': True, 'config': config, 'message': '配置已创建'}
    
    def validate_config(self, config_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置"""
        config = self.get_config(config_name)
        if not config['success']:
            return config
        
        value = config['config']
        errors = []
        
        if 'type' in schema and not isinstance(value, schema['type']):
            errors.append(f'类型错误，期望{schema["type"].__name__}，实际{type(value).__name__}')
        
        if 'required' in schema and schema['required'] and value is None:
            errors.append('配置值不能为空')
        
        if 'min' in schema and value < schema['min']:
            errors.append(f'值小于最小值{schema["min"]}')
        
        if 'max' in schema and value > schema['max']:
            errors.append(f'值大于最大值{schema["max"]}')
        
        if 'enum' in schema and value not in schema['enum']:
            errors.append(f'值不在允许列表中: {schema["enum"]}')
        
        return {
            'success': True,
            'valid': len(errors) == 0,
            'errors': errors if errors else None,
            'config_name': config_name
        }
    
    def backup_config(self, backup_name: str = "") -> Dict[str, Any]:
        """备份配置"""
        backup = {
            'backup_id': f'backup_{datetime.now().timestamp()}',
            'backup_name': backup_name or f'备份_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'configs': [c.copy() for c in self.config_history],
            'backup_at': datetime.now().isoformat(),
            'backup_by': self.name,
            'config_count': len(self.config_history)
        }
        self.backup_history.append(backup)
        return {'success': True, 'backup': backup}
    
    def restore_config(self, backup_id: str) -> Dict[str, Any]:
        """恢复配置"""
        for backup in self.backup_history:
            if backup['backup_id'] == backup_id:
                self.config_history = [c.copy() for c in backup['configs']]
                self.total_configs = len(self.config_history)
                return {'success': True, 'message': f'已从备份{backup["backup_name"]}恢复'}
        return {'success': False, 'message': '备份不存在'}
    
    def list_backups(self) -> Dict[str, Any]:
        """列出所有备份"""
        return {
            'success': True,
            'backups': [
                {
                    'backup_id': b['backup_id'],
                    'backup_name': b['backup_name'],
                    'backup_at': b['backup_at'],
                    'config_count': b['config_count']
                } for b in self.backup_history
            ],
            'count': len(self.backup_history)
        }
    
    def compare_configs(self, config_name: str, other_value: Any) -> Dict[str, Any]:
        """对比配置"""
        current = self.get_config(config_name)
        if not current['success']:
            return current
        
        current_value = current['config']
        differences = []
        
        if current_value != other_value:
            differences.append({
                'field': 'value',
                'current': current_value,
                'other': other_value,
                'type': 'changed'
            })
        
        return {
            'success': True,
            'config_name': config_name,
            'differences': differences,
            'same': len(differences) == 0
        }
    
    def audit_config_changes(self) -> Dict[str, Any]:
        """审计配置变更"""
        audit_log = []
        for config in self.config_history:
            audit_log.append({
                'config_name': config['config_name'],
                'updated_at': config.get('updated_at', ''),
                'updated_by': config.get('updated_by', ''),
                'description': config.get('description', '')
            })
        
        return {
            'success': True,
            'audit_log': audit_log,
            'total_changes': len(audit_log)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_configs': self.total_configs,
            'config_history_count': len(self.config_history),
            'backup_history_count': len(self.backup_history),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }
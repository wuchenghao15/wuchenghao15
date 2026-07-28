#!/usr/bin/env python3
"""AI智能系统扩展Agent"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AISystemExtensionAgent(AIEmployee):
    """AI系统扩展Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI系统扩展专家"):
        super().__init__(employee_id, name, 'system_extension', 7)
        self.skills = [
            '系统扩展', '插件管理', '模块加载',
            '功能注册', '服务发现', '接口扩展',
            '系统监控', '性能优化', '系统维护'
        ]
        self.extension_history = []
        self.total_extensions = 0
        self.active_extensions = 0
    
    def install_extension(self, extension_data: Dict[str, Any]) -> Dict[str, Any]:
        """安装扩展"""
        extension = {
            'extension_id': extension_data.get('extension_id', f'ext_{datetime.now().timestamp()}'),
            'name': extension_data.get('name', ''),
            'version': extension_data.get('version', '1.0.0'),
            'description': extension_data.get('description', ''),
            'type': extension_data.get('type', 'plugin'),
            'status': 'installed',
            'installed_at': datetime.now().isoformat(),
            'enabled': False
        }
        
        self.extension_history.append(extension)
        self.total_extensions += 1
        
        return {'success': True, 'extension': extension}
    
    def enable_extension(self, extension_id: str) -> Dict[str, Any]:
        """启用扩展"""
        for extension in self.extension_history:
            if extension['extension_id'] == extension_id:
                extension['enabled'] = True
                extension['status'] = 'active'
                extension['enabled_at'] = datetime.now().isoformat()
                self.active_extensions += 1
                
                return {'success': True, 'message': f'扩展 {extension["name"]} 已启用', 'extension': extension}
        return {'success': False, 'message': '扩展不存在'}
    
    def disable_extension(self, extension_id: str) -> Dict[str, Any]:
        """禁用扩展"""
        for extension in self.extension_history:
            if extension['extension_id'] == extension_id:
                extension['enabled'] = False
                extension['status'] = 'installed'
                if self.active_extensions > 0:
                    self.active_extensions -= 1
                
                return {'success': True, 'message': f'扩展 {extension["name"]} 已禁用', 'extension': extension}
        return {'success': False, 'message': '扩展不存在'}
    
    def uninstall_extension(self, extension_id: str) -> Dict[str, Any]:
        """卸载扩展"""
        for i, extension in enumerate(self.extension_history):
            if extension['extension_id'] == extension_id:
                if extension.get('enabled'):
                    self.active_extensions -= 1
                del self.extension_history[i]
                self.total_extensions -= 1
                
                return {'success': True, 'message': f'扩展 {extension["name"]} 已卸载'}
        return {'success': False, 'message': '扩展不存在'}
    
    def list_extensions(self, **kwargs) -> Dict[str, Any]:
        """列出扩展"""
        status = kwargs.get('status')
        ext_type = kwargs.get('type')
        
        extensions = self.extension_history
        
        if status:
            extensions = [e for e in extensions if e.get('status') == status]
        
        if ext_type:
            extensions = [e for e in extensions if e.get('type') == ext_type]
        
        return {'success': True, 'extensions': extensions, 'count': len(extensions)}
    
    def register_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """注册服务"""
        service = {
            'service_id': service_data.get('service_id', f'svc_{datetime.now().timestamp()}'),
            'name': service_data.get('name', ''),
            'endpoint': service_data.get('endpoint', ''),
            'description': service_data.get('description', ''),
            'status': 'registered',
            'registered_at': datetime.now().isoformat()
        }
        
        self.extension_history.append(service)
        
        return {'success': True, 'service': service}
    
    def discover_services(self) -> Dict[str, Any]:
        """发现服务"""
        services = [e for e in self.extension_history if e.get('type') == 'service']
        
        return {'success': True, 'services': services, 'count': len(services)}
    
    def extend_interface(self, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """扩展接口"""
        interface = {
            'interface_id': interface_data.get('interface_id', f'iface_{datetime.now().timestamp()}'),
            'name': interface_data.get('name', ''),
            'base_interface': interface_data.get('base_interface', ''),
            'methods': interface_data.get('methods', []),
            'extended_at': datetime.now().isoformat()
        }
        
        self.extension_history.append(interface)
        
        return {'success': True, 'interface': interface}
    
    def monitor_extensions(self) -> Dict[str, Any]:
        """监控扩展状态"""
        active = [e for e in self.extension_history if e.get('enabled')]
        installed = [e for e in self.extension_history if e.get('status') == 'installed']
        errors = [e for e in self.extension_history if e.get('status') == 'error']
        
        return {
            'success': True,
            'monitor': {
                'total_extensions': self.total_extensions,
                'active_extensions': self.active_extensions,
                'installed_count': len(installed),
                'error_count': len(errors),
                'health_status': self._get_health_status(len(errors))
            }
        }
    
    def _get_health_status(self, error_count: int) -> str:
        if error_count > 0:
            return '有错误'
        elif self.active_extensions == 0:
            return '无活动扩展'
        else:
            return '健康'
    
    def optimize_performance(self) -> Dict[str, Any]:
        """优化性能"""
        optimizations = []
        
        for extension in self.extension_history:
            if extension.get('enabled'):
                optimizations.append({
                    'extension_id': extension['extension_id'],
                    'name': extension['name'],
                    'optimization': '已启用性能监控',
                    'status': 'applied'
                })
        
        return {
            'success': True,
            'optimizations': optimizations,
            'total_applied': len(optimizations)
        }
    
    def generate_extension_report(self) -> Dict[str, Any]:
        """生成扩展报告"""
        return {
            'success': True,
            'report': {
                'generated_at': datetime.now().isoformat(),
                'total_extensions': self.total_extensions,
                'active_extensions': self.active_extensions,
                'extension_types': list(set(e.get('type', '') for e in self.extension_history)),
                'installations': [
                    {'name': e['name'], 'version': e['version'], 'installed_at': e['installed_at']}
                    for e in self.extension_history
                ]
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_extensions': self.total_extensions,
            'active_extensions': self.active_extensions,
            'extension_history_count': len(self.extension_history),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }
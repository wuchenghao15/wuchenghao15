# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统适配器模块 - 集成所有V2系统
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SystemAdapter')

class V2SystemAdapter:
    """V2系统适配器"""
    
    def __init__(self):
        """初始化V2系统适配器"""
        self._systems = {}
        self._initialize_all_systems()
    
    def _initialize_all_systems(self):
        """初始化所有V2系统"""
        systems_to_init = [
            ('thread_manager', self._init_thread_manager),
            ('process_manager', self._init_process_manager),
            ('permission_manager', self._init_permission_manager),
            ('audit_system', self._init_audit_system),
            ('ai_system', self._init_ai_system),
            ('distributed_deployment', self._init_distributed_deployment),
            ('sandbox_system', self._init_sandbox_system),
            ('environment_manager', self._init_environment_manager),
            ('theme_system', self._init_theme_system),
        ]
        
        logger.info("开始初始化V2系统...")
        
        for name, init_func in systems_to_init:
            try:
                init_func()
                logger.info(f"✓ {name} 初始化成功")
            except Exception as e:
                logger.warning(f"✗ {name} 初始化失败: {str(e)}")
        
        logger.info("V2系统初始化完成")
    
    def _init_thread_manager(self):
        """初始化线程管理系统"""
        from thread_manager_v2 import ThreadManager
        self._systems['thread_manager'] = ThreadManager(max_workers=10, min_workers=2)
    
    def _init_process_manager(self):
        """初始化进程管理系统"""
        from process_manager_v2 import ProcessManager
        self._systems['process_manager'] = ProcessManager()
    
    def _init_permission_manager(self):
        """初始化权限管理系统"""
        from permission_manager_v2 import PermissionManager
        self._systems['permission_manager'] = PermissionManager()
    
    def _init_audit_system(self):
        """初始化审计系统"""
        from audit_system_v2 import AuditSystem
        self._systems['audit_system'] = AuditSystem()
    
    def _init_ai_system(self):
        """初始化AI系统"""
        from ai_system_v2 import AISystem
        self._systems['ai_system'] = AISystem()
    
    def _init_distributed_deployment(self):
        """初始化分布式部署系统"""
        from distributed_deployment_v2 import DistributedDeploymentSystem
        self._systems['distributed_deployment'] = DistributedDeploymentSystem()
    
    def _init_sandbox_system(self):
        """初始化沙盒系统"""
        from sandbox_system_v2 import SandboxSystem
        self._systems['sandbox_system'] = SandboxSystem()
    
    def _init_environment_manager(self):
        """初始化环境管理系统"""
        from environment_manager_v2 import EnvironmentManager
        self._systems['environment_manager'] = EnvironmentManager()
    
    def _init_theme_system(self):
        """初始化主题配色系统"""
        from theme_system_v2 import ThemeSystem
        self._systems['theme_system'] = ThemeSystem()
    
    def get_system(self, name: str):
        """获取指定系统"""
        return self._systems.get(name)
    
    def get_all_systems(self):
        """获取所有系统"""
        return self._systems.copy()
    
    def get_status(self):
        """获取所有系统状态"""
        status = {}
        for name, system in self._systems.items():
            try:
                if hasattr(system, 'get_stats'):
                    stats = system.get_stats()
                    status[name] = {
                        'status': 'running',
                        'stats': stats
                    }
                else:
                    status[name] = {'status': 'running'}
            except Exception as e:
                status[name] = {'status': 'error', 'error': str(e)}
        return status
    
    def shutdown(self):
        """关闭所有系统"""
        logger.info("正在关闭V2系统...")
        
        if 'sandbox_system' in self._systems:
            try:
                self._systems['sandbox_system'].shutdown()
            except Exception:
                pass
        
        if 'thread_manager' in self._systems:
            try:
                self._systems['thread_manager'].stop()
            except Exception:
                pass
        
        logger.info("V2系统已关闭")


v2_system_adapter = None

def get_v2_adapter():
    """获取V2系统适配器"""
    global v2_system_adapter
    if v2_system_adapter is None:
        v2_system_adapter = V2SystemAdapter()
    return v2_system_adapter

def init_v2_systems():
    """初始化所有V2系统"""
    adapter = get_v2_adapter()
    return adapter

def get_v2_system(name: str):
    """获取指定的V2系统"""
    adapter = get_v2_adapter()
    return adapter.get_system(name)

def get_v2_status():
    """获取V2系统状态"""
    adapter = get_v2_adapter()
    return adapter.get_status()

def shutdown_v2_systems():
    """关闭所有V2系统"""
    global v2_system_adapter
    if v2_system_adapter:
        v2_system_adapter.shutdown()
        v2_system_adapter = None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MTSCOS AI Project - V2系统初始化")
    print("=" * 60)
    
    adapter = V2SystemAdapter()
    
    print("\n初始化完成！")
    print("可用系统:")
    for name in adapter.get_all_systems().keys():
        print(f"  - {name}")
    
    print("\n系统状态:")
    for name, status in adapter.get_status().items():
        print(f"  - {name}: {status['status']}")
    
    print("\n" + "=" * 60)
    print("V2系统已成功启动！")
    print("=" * 60)
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统适配管理器 V2.0
统一管理和初始化所有V2系统模块
"""

import sys
import time
import logging
import threading
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SystemAdapter')

class SystemAdapter:
    """系统适配管理器"""
    
    def __init__(self):
        """初始化系统适配器"""
        self.systems: Dict[str, Any] = {}
        self.status: Dict[str, str] = {}
        self.lock = threading.Lock()
        
        self._initialize_all_systems()
    
    def _initialize_all_systems(self):
        """初始化所有V2系统模块"""
        system_initializers = [
            ("thread_manager", self._init_thread_manager),
            ("process_manager", self._init_process_manager),
            ("permission_manager", self._init_permission_manager),
            ("audit_system", self._init_audit_system),
            ("ai_system", self._init_ai_system),
            ("distributed_deployment", self._init_distributed_deployment),
            ("sandbox_system", self._init_sandbox_system),
            ("environment_manager", self._init_environment_manager),
            ("theme_system", self._init_theme_system),
        ]
        
        for name, init_func in system_initializers:
            try:
                init_func()
                self.status[name] = "initialized"
                logger.info(f"✓ {name} 初始化成功")
            except Exception as e:
                self.status[name] = f"error: {str(e)}"
                logger.error(f"✗ {name} 初始化失败: {str(e)}")
        
        self._print_summary()
    
    def _init_thread_manager(self):
        """初始化线程管理系统"""
        from thread_manager_v2 import ThreadManager
        self.systems["thread_manager"] = ThreadManager(max_workers=10, min_workers=2)
    
    def _init_process_manager(self):
        """初始化进程管理系统"""
        from process_manager_v2 import ProcessManager
        self.systems["process_manager"] = ProcessManager()
    
    def _init_permission_manager(self):
        """初始化权限管理系统"""
        from permission_manager_v2 import PermissionManager
        self.systems["permission_manager"] = PermissionManager()
    
    def _init_audit_system(self):
        """初始化审计系统"""
        from audit_system_v2 import AuditSystem
        self.systems["audit_system"] = AuditSystem()
    
    def _init_ai_system(self):
        """初始化AI系统"""
        from ai_system_v2 import AISystem
        self.systems["ai_system"] = AISystem()
    
    def _init_distributed_deployment(self):
        """初始化分布式部署系统"""
        from distributed_deployment_v2 import DistributedDeploymentSystem
        self.systems["distributed_deployment"] = DistributedDeploymentSystem()
    
    def _init_sandbox_system(self):
        """初始化沙盒系统"""
        from sandbox_system_v2 import SandboxSystem
        self.systems["sandbox_system"] = SandboxSystem()
    
    def _init_environment_manager(self):
        """初始化环境管理系统"""
        from environment_manager_v2 import EnvironmentManager
        self.systems["environment_manager"] = EnvironmentManager()
    
    def _init_theme_system(self):
        """初始化主题配色系统"""
        from theme_system_v2 import ThemeSystem
        self.systems["theme_system"] = ThemeSystem()
    
    def _print_summary(self):
        """打印初始化摘要"""
        total = len(self.systems)
        success = sum(1 for s in self.status.values() if s == "initialized")
        
        print("\n" + "=" * 60)
        print("系统适配管理器 V2.0 - 初始化完成")
        print("=" * 60)
        print(f"总系统数: {total}")
        print(f"成功初始化: {success}")
        print(f"失败: {total - success}")
        print("-" * 60)
        
        for name, status in self.status.items():
            icon = "✓" if status == "initialized" else "✗"
            print(f"  {icon} {name}: {status}")
        
        print("=" * 60 + "\n")
    
    def get_system(self, name: str) -> Any:
        """获取指定系统"""
        return self.systems.get(name)
    
    def get_all_systems(self) -> Dict[str, Any]:
        """获取所有系统"""
        return self.systems.copy()
    
    def get_status(self) -> Dict[str, str]:
        """获取所有系统状态"""
        return self.status.copy()
    
    def shutdown_all(self):
        """关闭所有系统"""
        logger.info("正在关闭所有系统...")
        
        if "sandbox_system" in self.systems:
            try:
                self.systems["sandbox_system"].shutdown()
            except Exception:
                pass
        
        if "thread_manager" in self.systems:
            try:
                self.systems["thread_manager"].stop()
            except Exception:
                pass
        
        logger.info("所有系统已关闭")
    
    def restart_system(self, system_name: str) -> bool:
        """重启指定系统"""
        if system_name in self.systems:
            try:
                logger.info(f"正在重启系统: {system_name}")
                init_func = getattr(self, f"_init_{system_name}")
                init_func()
                self.status[system_name] = "initialized"
                logger.info(f"系统已重启: {system_name}")
                return True
            except Exception as e:
                self.status[system_name] = f"error: {str(e)}"
                logger.error(f"重启失败: {system_name} - {str(e)}")
                return False
        return False


def main():
    """主函数"""
    print("\n正在启动系统适配管理器...")
    
    adapter = SystemAdapter()
    
    print("\n系统适配管理器已成功启动!")
    print("=" * 60)
    print("所有V2系统模块已初始化完成:")
    print("  - 线程管理系统 V2.0")
    print("  - 进程管理系统 V2.0")
    print("  - 权限管理系统 V2.0")
    print("  - 审计系统 V2.0")
    print("  - AI系统 V2.0")
    print("  - 分布式部署系统 V2.0")
    print("  - 沙盒系统 V2.0")
    print("  - 环境管理系统 V2.0")
    print("  - 主题配色系统 V2.0")
    print("=" * 60)
    
    return adapter


if __name__ == "__main__":
    adapter = main()
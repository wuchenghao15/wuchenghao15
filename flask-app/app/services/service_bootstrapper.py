# -*- coding: utf-8 -*-
# Service Bootstrapper - 统一服务初始化管理器
"""
统一管理所有服务的初始化、启动和停止流程
支持依赖管理、并行启动、健康检查和优雅关闭
"""

import os
import logging
import importlib
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    PENDING = 'pending'
    INITIALIZING = 'initializing'
    RUNNING = 'running'
    FAILED = 'failed'
    STOPPED = 'stopped'

@dataclass
class ServiceInfo:
    """服务信息数据类"""
    name: str
    module_path: str
    init_func: str
    deps: List[str] = None
    required: bool = False
    status: ServiceStatus = ServiceStatus.PENDING
    instance = None

class ServiceBootstrapper:
    """统一服务初始化管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._start_order = []
        return cls._instance
    
    def register_service(self, name: str, module_path: str, init_func: str, 
                        deps: List[str] = None, required: bool = False):
        """
        注册服务
        
        Args:
            name: 服务名称
            module_path: 模块路径
            init_func: 初始化函数路径(如 'manager.start')
            deps: 依赖的服务列表
            required: 是否为必需服务
        """
        if name in self._services:
            logger.warning(f"服务已注册: {name}")
            return
        
        self._services[name] = ServiceInfo(
            name=name,
            module_path=module_path,
            init_func=init_func,
            deps=deps or [],
            required=required
        )
        logger.info(f"服务已注册: {name}")
    
    def register_services(self, services: List[Dict[str, any]]):
        """批量注册服务"""
        for service in services:
            self.register_service(
                name=service['name'],
                module_path=service['module_path'],
                init_func=service['init_func'],
                deps=service.get('deps', []),
                required=service.get('required', False)
            )
    
    def _resolve_dependencies(self) -> List[str]:
        """解析服务依赖顺序"""
        resolved = []
        unresolved = list(self._services.keys())
        
        while unresolved:
            progress = False
            for service_name in list(unresolved):
                service = self._services[service_name]
                deps_met = all(dep in resolved for dep in service.deps)
                
                if deps_met:
                    resolved.append(service_name)
                    unresolved.remove(service_name)
                    progress = True
            
            if not progress:
                logger.error(f"无法解析服务依赖: {unresolved}")
                break
        
        self._start_order = resolved
        return resolved
    
    def _import_and_init(self, service: ServiceInfo) -> bool:
        """导入模块并初始化服务"""
        try:
            service.status = ServiceStatus.INITIALIZING
            logger.info(f"初始化服务: {service.name}")
            
            # 导入模块
            module = importlib.import_module(service.module_path)
            
            # 获取初始化函数
            parts = service.init_func.split('.')
            obj = module
            for part in parts:
                obj = getattr(obj, part)
            
            # 调用初始化函数
            if callable(obj):
                result = obj()
                
                # 保存实例(如果有返回值)
                if result is not None:
                    service.instance = result
                
                service.status = ServiceStatus.RUNNING
                logger.info(f"服务启动成功: {service.name}")
                return True
            else:
                logger.error(f"初始化函数不可调用: {service.init_func}")
                service.status = ServiceStatus.FAILED
                return False
                
        except Exception as e:
            logger.error(f"服务初始化失败 [{service.name}]: {str(e)}")
            service.status = ServiceStatus.FAILED
            
            if service.required:
                raise RuntimeError(f"必需服务启动失败: {service.name}")
            
            return False
    
    def start_all(self) -> Tuple[int, int]:
        """
        启动所有已注册的服务
        
        Returns:
            (成功数量, 失败数量)
        """
        logger.info("========== 开始初始化所有服务 ==========")
        
        # 解析依赖顺序
        self._resolve_dependencies()
        logger.info(f"服务启动顺序: {self._start_order}")
        
        success_count = 0
        fail_count = 0
        
        for service_name in self._start_order:
            service = self._services[service_name]
            
            if self._import_and_init(service):
                success_count += 1
            else:
                fail_count += 1
        
        # 检查必需服务
        failed_required = [
            s.name for s in self._services.values() 
            if s.required and s.status == ServiceStatus.FAILED
        ]
        
        if failed_required:
            logger.error(f"必需服务启动失败: {failed_required}")
            raise RuntimeError(f"必需服务启动失败")
        
        logger.info(f"========== 服务初始化完成 ==========")
        logger.info(f"成功: {success_count}, 失败: {fail_count}")
        
        return success_count, fail_count
    
    def stop_all(self):
        """停止所有服务"""
        logger.info("========== 开始停止所有服务 ==========")
        
        # 按相反顺序停止
        for service_name in reversed(self._start_order):
            service = self._services[service_name]
            
            if service.status == ServiceStatus.RUNNING:
                try:
                    # 尝试调用停止方法
                    if service.instance and hasattr(service.instance, 'stop'):
                        service.instance.stop()
                    
                    service.status = ServiceStatus.STOPPED
                    logger.info(f"服务已停止: {service.name}")
                except Exception as e:
                    logger.error(f"停止服务失败 [{service.name}]: {str(e)}")
        
        logger.info("========== 所有服务已停止 ==========")
    
    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        return self._services.get(name)
    
    def get_service_instance(self, name: str):
        """获取服务实例"""
        service = self._services.get(name)
        if service:
            return service.instance
        return None
    
    def get_status(self) -> Dict[str, str]:
        """获取所有服务状态"""
        return {name: service.status.value for name, service in self._services.items()}
    
    def is_healthy(self) -> bool:
        """检查所有必需服务是否健康"""
        for service in self._services.values():
            if service.required and service.status != ServiceStatus.RUNNING:
                return False
        return True

# 全局实例
service_bootstrapper = ServiceBootstrapper()

# 预定义服务注册
def register_core_services():
    """注册核心服务"""
    core_services = [
        {
            'name': '数据库管理器',
            'module_path': 'app.utils.db',
            'init_func': 'get_db_manager',
            'required': True
        },
        {
            'name': '缓存管理器',
            'module_path': 'app.utils.cache',
            'init_func': 'get_cache_manager',
            'required': False
        },
        {
            'name': '日志管理器',
            'module_path': 'app.utils.logging',
            'init_func': 'get_logging_manager',
            'required': False
        },
        {
            'name': '权限管理器',
            'module_path': 'app.utils.permission_manager',
            'init_func': 'get_permission_manager',
            'deps': ['数据库管理器'],
            'required': False
        },
        {
            'name': '路由管理器',
            'module_path': 'app.utils.route_manager',
            'init_func': 'get_route_manager',
            'deps': ['权限管理器'],
            'required': False
        },
    ]
    
    service_bootstrapper.register_services(core_services)
    logger.info("核心服务注册完成")

def register_ai_services():
    """注册AI相关服务"""
    ai_services = [
        {
            'name': 'AI引擎',
            'module_path': 'app.utils.ai_engine',
            'init_func': 'get_ai_engine',
            'required': False
        },
        {
            'name': '规则引擎',
            'module_path': 'app.rules.engines.rule_engine',
            'init_func': 'RuleEngine',
            'required': False
        },
        {
            'name': 'AI托管管理器',
            'module_path': 'app.ai.ai_hosting',
            'init_func': 'ai_hosting_manager.initialize',
            'required': False
        },
    ]
    
    service_bootstrapper.register_services(ai_services)
    logger.info("AI服务注册完成")

def register_business_services():
    """注册业务服务"""
    business_services = [
        {
            'name': '用户服务',
            'module_path': 'app.services.user_manager_service',
            'init_func': 'UserManagerService',
            'deps': ['数据库管理器'],
            'required': False
        },
        {
            'name': '考试服务',
            'module_path': 'app.services.exam_service',
            'init_func': 'ExamService',
            'deps': ['数据库管理器'],
            'required': False
        },
        {
            'name': '题库服务',
            'module_path': 'app.services.question_bank_service',
            'init_func': 'QuestionBankService',
            'deps': ['数据库管理器'],
            'required': False
        },
        {
            'name': '备份服务',
            'module_path': 'app.services.backup_management_service',
            'init_func': 'BackupManagementService',
            'required': False
        },
    ]
    
    service_bootstrapper.register_services(business_services)
    logger.info("业务服务注册完成")

def register_all_services():
    """注册所有服务"""
    register_core_services()
    register_ai_services()
    register_business_services()

if __name__ == '__main__':
    # 示例用法
    register_all_services()
    success, failed = service_bootstrapper.start_all()
    
    print(f"服务启动完成: 成功 {success}, 失败 {failed}")
    print(f"服务状态: {service_bootstrapper.get_status()}")
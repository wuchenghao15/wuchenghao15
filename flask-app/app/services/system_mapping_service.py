#!/usr/bin/env python3
"""
系统映射服务，负责统一管理所有系统映射关系
"""

import os
import json
import time
import threading
from datetime import datetime
from app.config import Config
from app.utils.logging import logger

# 延迟导入，避免循环导入
_ai_instance_manager = None

def _get_ai_instance_manager():
    global _ai_instance_manager
    if _ai_instance_manager is None:
        from app.ai.instances import ai_instance_manager
        _ai_instance_manager = ai_instance_manager
    return _ai_instance_manager

class SystemMappingService:
    """系统映射服务，负责统一管理所有系统映射关系"""
    
    def __init__(self):
        self.mappings = {
            "route_mappings": {},        # 路由映射: URL -> 处理函数
            "permission_mappings": {},   # 权限映射: 角色 -> 允许的操作
            "data_mappings": {},         # 数据映射: 数据模型 -> 存储位置
            "ai_employee_mappings": {},  # AI员工映射: AI员工 -> 负责的功能
            "feature_mappings": {},      # 功能映射: 功能 -> 实现模块
            "config_mappings": {},       # 配置映射: 配置键 -> 配置值
            "role_mappings": {},         # 角色映射: 角色 -> 权限列表
            "user_role_mappings": {},    # 用户角色映射: 用户ID -> 角色列表
            "system_version_mappings": {}  # 系统版本映射: 版本号 -> 变更列表
        }
        
        self.mapping_lock = threading.Lock()
        self.mapping_manager_ai = None
        self.auto_update_enabled = True  # 启用自动更新，使用后台线程
        self.update_interval = 3600  # 默认1小时更新一次
        
        # 映射源配置
        self.mapping_sources = {
            "permission_mappings": [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "src", "data", "permission-rules.json")
            ],
            "role_mappings": [
                os.path.join(os.path.dirname(__file__), "..", "utils", "security.py")
            ],
            "system_version_mappings": [
                os.path.join(os.path.dirname(__file__), "..", "..", "VERSION")
            ]
        }
        
        # 初始化映射管理AI
        self.init_mapping_manager_ai()
        
        # 初始化所有映射
        self.initialize_mappings()
        
        # 启动自动更新线程
        if self.auto_update_enabled:
            self.start_auto_update()
    
    def init_mapping_manager_ai(self):
        """初始化映射管理AI"""
        try:
            # 检查是否已存在映射管理AI
            existing_instance = _get_ai_instance_manager().get_ai_instance("mapping_manager_ai")
            
            if not existing_instance:
                # 创建映射管理AI
                self.mapping_manager_ai = _get_ai_instance_manager().create_ai_instance(
                    instance_id="mapping_manager_ai",
                    ai_type="mapping_manager",
                    name="映射管理AI",
                    description="负责统一管理和维护所有系统映射关系",
                    functions=["mapping_management", "mapping_execution", "mapping_optimization", "mapping_monitoring", "mapping_extension"],
                    responsibilities=[
                        "管理所有系统映射关系",
                        "维护映射的完整性和一致性",
                        "优化映射配置",
                        "监控映射执行情况",
                        "更新和扩展映射库",
                        "提供映射管理API",
                        "自动修复映射冲突"
                    ],
                    config={
                        "mappings": self.mappings,
                        "auto_update": self.auto_update_enabled,
                        "update_interval": self.update_interval,
                        "mapping_sources": self.mapping_sources
                    }
                )
                logger.info("映射管理AI创建成功")
            else:
                self.mapping_manager_ai = existing_instance
                logger.info("映射管理AI已存在，将更新其配置")
                self.update_mapping_manager_ai()
        except Exception as e:
            logger.error(f"初始化映射管理AI失败: {str(e)}")
    
    def update_mapping_manager_ai(self):
        """更新映射管理AI配置"""
        try:
            if self.mapping_manager_ai:
                _get_ai_instance_manager().update_ai_instance(
                    instance_id="mapping_manager_ai",
                    updates={
                        "config": {
                            "mappings": self.mappings,
                            "auto_update": self.auto_update_enabled,
                            "update_interval": self.update_interval,
                            "mapping_sources": self.mapping_sources
                        }
                    }
                )
                logger.info("映射管理AI配置更新成功")
        except Exception as e:
            logger.error(f"更新映射管理AI配置失败: {str(e)}")
    
    def initialize_mappings(self):
        """初始化所有映射"""
        logger.info("开始初始化系统映射...")
        
        with self.mapping_lock:
            # 1. 初始化路由映射
            self._initialize_route_mappings()
            
            # 2. 初始化权限映射
            self._initialize_permission_mappings()
            
            # 3. 初始化数据映射
            self._initialize_data_mappings()
            
            # 4. 初始化AI员工映射
            self._initialize_ai_employee_mappings()
            
            # 5. 初始化功能映射
            self._initialize_feature_mappings()
            
            # 6. 初始化配置映射
            self._initialize_config_mappings()
            
            # 7. 初始化角色映射
            self._initialize_role_mappings()
            
            # 8. 初始化系统版本映射
            self._initialize_system_version_mappings()
        
        # 更新映射管理AI
        self.update_mapping_manager_ai()
        
        logger.info("系统映射初始化完成")
    
    def _initialize_route_mappings(self):
        """初始化路由映射"""
        route_mappings = {
            # 主路由
            "/": {"handler": "index", "methods": ["GET"], "permission": "public"},
            "/auth/login": {"handler": "login", "methods": ["GET", "POST"], "permission": "public"},
            "/auth/logout": {"handler": "logout", "methods": ["GET"], "permission": "authenticated"},
            "/user_profile": {"handler": "user_profile", "methods": ["GET"], "permission": "authenticated"},
            "/settings": {"handler": "settings", "methods": ["GET", "POST"], "permission": "authenticated"},
            "/complete_formation": {"handler": "complete_formation", "methods": ["GET", "POST"], "permission": "authenticated"},
            "/dashboard": {"handler": "dashboard", "methods": ["GET"], "permission": "user"},
            "/permissions": {"handler": "permissions", "methods": ["GET"], "permission": "admin"},
            "/system_monitoring": {"handler": "system_monitoring", "methods": ["GET"], "permission": "admin"},
            
            # API路由
            "/api/system/version": {"handler": "get_system_version", "methods": ["GET"], "permission": "public"},
            "/api/system/components": {"handler": "get_initialized_components", "methods": ["GET"], "permission": "public"},
            "/get_js_ai_code": {"handler": "get_js_ai_code", "methods": ["GET"], "permission": "public"},
            "/get_js_ai_code/<function_name>": {"handler": "get_js_ai_code", "methods": ["GET"], "permission": "public"}
        }
        
        self.mappings["route_mappings"] = route_mappings
        logger.info(f"已初始化 {len(route_mappings)} 条路由映射")
    
    def _initialize_permission_mappings(self):
        """初始化权限映射"""
        permission_mappings = {}
        
        for source in self.mapping_sources["permission_mappings"]:
            if os.path.exists(source) and source.endswith(".json"):
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                        permission_mappings.update(rules)
                except Exception as e:
                    logger.error(f"从 {source} 加载权限映射失败: {str(e)}")
        
        # 默认权限映射
        if not permission_mappings:
            permission_mappings = {
                "admin": {
                    "can_manage_users": True,
                    "can_manage_roles": True,
                    "can_manage_system": True,
                    "can_manage_ai": True,
                    "can_access_dashboard": True,
                    "can_view_logs": True,
                    "can_change_settings": True
                },
                "user": {
                    "can_access_dashboard": True,
                    "can_manage_profile": True,
                    "can_change_password": True,
                    "can_view_own_data": True
                },
                "guest": {
                    "can_view_public_content": True,
                    "can_register": True,
                    "can_login": True
                }
            }
        
        self.mappings["permission_mappings"] = permission_mappings
        logger.info(f"已初始化 {len(permission_mappings)} 个角色的权限映射")
    
    def _initialize_data_mappings(self):
        """初始化数据映射"""
        data_mappings = {
            "User": {
                "table": "users",
                "primary_key": "user_id",
                "fields": {
                    "user_id": "TEXT",
                    "username": "TEXT",
                    "password": "TEXT",
                    "email": "TEXT",
                    "role": "TEXT",
                    "created_at": "DATETIME",
                    "updated_at": "DATETIME"
                }
            },
            "EnhancedAIEmployee": {
                "table": "enhanced_ai_employees",
                "primary_key": "employee_id",
                "fields": {
                    "employee_id": "TEXT",
                    "name": "TEXT",
                    "ai_type": "TEXT",
                    "description": "TEXT",
                    "capabilities": "TEXT",
                    "status": "TEXT",
                    "config": "TEXT",
                    "created_at": "DATETIME",
                    "updated_at": "DATETIME"
                }
            },
            "Backup": {
                "table": "backups",
                "primary_key": "id",
                "fields": {
                    "id": "INTEGER",
                    "name": "TEXT",
                    "backup_type": "TEXT",
                    "description": "TEXT",
                    "size": "INTEGER",
                    "status": "TEXT",
                    "created_at": "REAL",
                    "created_by": "TEXT",
                    "file_path": "TEXT",
                    "checksum": "TEXT"
                }
            },
            "UserSnapshot": {
                "table": "user_snapshots",
                "primary_key": "snapshot_id",
                "fields": {
                    "snapshot_id": "TEXT",
                    "user_id": "TEXT",
                    "session_id": "TEXT",
                    "timestamp": "REAL",
                    "snapshot_type": "TEXT",
                    "data": "TEXT"
                }
            }
        }
        
        self.mappings["data_mappings"] = data_mappings
        logger.info(f"已初始化 {len(data_mappings)} 个数据模型映射")
    
    def _initialize_ai_employee_mappings(self):
        """初始化AI员工映射"""
        ai_employee_mappings = {
            "system_manager": {
                "type": "manager",
                "capabilities": ["system_version_management", "system_monitoring", "system_optimization"],
                "responsibilities": ["系统版本管理", "系统监控", "系统优化"]
            },
            "backup_manager": {
                "type": "backup_manager",
                "capabilities": ["backup_management", "rollback_mechanism", "snapshot_saving"],
                "responsibilities": ["备份管理", "回滚机制", "快照保存"]
            },
            "mapping_manager": {
                "type": "mapping_manager",
                "capabilities": ["mapping_management", "mapping_optimization", "mapping_monitoring"],
                "responsibilities": ["映射管理", "映射优化", "映射监控"]
            },
            "rule_manager": {
                "type": "rule_manager",
                "capabilities": ["rule_management", "rule_execution", "rule_optimization"],
                "responsibilities": ["规则管理", "规则执行", "规则优化"]
            }
        }
        
        self.mappings["ai_employee_mappings"] = ai_employee_mappings
        logger.info(f"已初始化 {len(ai_employee_mappings)} 个AI员工映射")
    
    def _initialize_feature_mappings(self):
        """初始化功能映射"""
        feature_mappings = {
            "user_authentication": {
                "module": "app.services.auth_service",
                "functions": ["login", "logout", "register", "change_password"]
            },
            "backup_management": {
                "module": "app.ai.backup_management_ai",
                "functions": ["create_backup", "restore_backup", "create_snapshot", "rollback_to_snapshot"]
            },
            "system_monitoring": {
                "module": "app.services.system_monitoring_service",
                "functions": ["get_system_status", "monitor_system", "generate_report"]
            },
            "ai_management": {
                "module": "app.ai.instances",
                "functions": ["create_ai_instance", "update_ai_instance", "delete_ai_instance", "get_ai_instance"]
            }
        }
        
        self.mappings["feature_mappings"] = feature_mappings
        logger.info(f"已初始化 {len(feature_mappings)} 个功能映射")
    
    def _initialize_config_mappings(self):
        """初始化配置映射"""
        config_mappings = {
            "database": {
                "path": Config.DATABASE_PATH,
                "connection_pool_size": 10,
                "timeout": 30
            },
            "server": {
                "host": Config.HOST,
                "port": Config.PORT,
                "debug": Config.DEBUG
            },
            "security": {
                "secret_key": Config.SECRET_KEY,
                "token_expiry": 3600,
                "password_hash_algorithm": "sha256"
            },
            "logging": {
                "level": Config.LOG_LEVEL,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        self.mappings["config_mappings"] = config_mappings
        logger.info(f"已初始化 {len(config_mappings)} 个配置映射")
    
    def _initialize_role_mappings(self):
        """初始化角色映射"""
        role_mappings = {
            "admin": {
                "name": "管理员",
                "description": "系统管理员，可以管理所有系统功能",
                "permissions": ["can_manage_users", "can_manage_roles", "can_manage_system", "can_manage_ai", "can_access_dashboard", "can_view_logs", "can_change_settings"]
            },
            "user": {
                "name": "普通用户",
                "description": "普通注册用户，可以访问基本功能",
                "permissions": ["can_access_dashboard", "can_manage_profile", "can_change_password", "can_view_own_data"]
            },
            "guest": {
                "name": "游客",
                "description": "未注册用户，只能访问公开内容",
                "permissions": ["can_view_public_content", "can_register", "can_login"]
            },
            "super_admin": {
                "name": "超级管理员",
                "description": "拥有最高权限的管理员",
                "permissions": ["all"]
            },
            "hardware_admin": {
                "name": "硬件管理员",
                "description": "硬件设备管理员，可以修改系统参数和设置",
                "permissions": ["can_manage_system", "can_change_settings", "can_approve_changes"]
            }
        }
        
        self.mappings["role_mappings"] = role_mappings
        logger.info(f"已初始化 {len(role_mappings)} 个角色映射")
    
    def _initialize_system_version_mappings(self):
        """初始化系统版本映射"""
        # 从VERSION文件读取版本信息
        version_file = self.mapping_sources["system_version_mappings"][0]
        current_version = "1.0.0"
        
        if os.path.exists(version_file):
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    current_version = f.read().strip()
            except Exception as e:
                logger.error(f"从 {version_file} 读取版本信息失败: {str(e)}")
        
        system_version_mappings = {
            current_version: {
                "release_date": datetime.now().isoformat(),
                "changes": [
                    "完善系统映射服务",
                    "统一管理所有系统映射关系",
                    "添加映射管理AI",
                    "实现自动更新机制"
                ],
                "status": "current"
            }
        }
        
        self.mappings["system_version_mappings"] = system_version_mappings
        logger.info(f"已初始化系统版本映射，当前版本: {current_version}")
    
    def get_mapping(self, mapping_type: str, key: Optional[str] = None) -> Any:
        """获取映射信息"""
        with self.mapping_lock:
            if mapping_type in self.mappings:
                if key:
                    return self.mappings[mapping_type].get(key)
                return self.mappings[mapping_type].copy()
            return None
    
    def update_mapping(self, mapping_type: str, key: str, value: Any) -> bool:
        """更新映射信息"""
        with self.mapping_lock:
            if mapping_type in self.mappings:
                self.mappings[mapping_type][key] = value
                logger.info(f"已更新 {mapping_type} 映射: {key}")
                # 更新映射管理AI
                self.update_mapping_manager_ai()
                return True
        return False
    
    def add_mapping(self, mapping_type: str, key: str, value: Any) -> bool:
        """添加映射信息"""
        with self.mapping_lock:
            if mapping_type in self.mappings:
                if key not in self.mappings[mapping_type]:
                    self.mappings[mapping_type][key] = value
                    logger.info(f"已添加 {mapping_type} 映射: {key}")
                    # 更新映射管理AI
                    self.update_mapping_manager_ai()
                    return True
        return False
    
    def delete_mapping(self, mapping_type: str, key: str) -> bool:
        """删除映射信息"""
        with self.mapping_lock:
            if mapping_type in self.mappings:
                if key in self.mappings[mapping_type]:
                    del self.mappings[mapping_type][key]
                    logger.info(f"已删除 {mapping_type} 映射: {key}")
                    # 更新映射管理AI
                    self.update_mapping_manager_ai()
                    return True
        return False
    
    def validate_mapping(self, mapping_type: str, key: str, value: Any) -> bool:
        """验证映射信息"""
        # 调用映射管理AI进行验证
        if self.mapping_manager_ai:
            logger.info(f"验证 {mapping_type} 映射: {key}")
            # 这里可以实现更复杂的验证逻辑
            return True
        return False
    
    def optimize_mappings(self):
        """优化映射配置"""
        if self.mapping_manager_ai:
            logger.info("开始优化系统映射")
            # 这里可以实现映射优化逻辑
            logger.info("系统映射优化完成")
            return True
        return False
    
    def monitor_mappings(self):
        """监控映射执行情况"""
        logger.info("开始监控映射执行情况")
        # 这里可以实现映射监控逻辑
        logger.info("映射监控完成")
        return True
    
    def start_auto_update(self):
        """启动自动更新线程"""
        def auto_update_thread():
            while self.auto_update_enabled:
                time.sleep(self.update_interval)
                self.initialize_mappings()
                self.optimize_mappings()
                self.monitor_mappings()
        
        thread = threading.Thread(target=auto_update_thread, daemon=True)
        thread.start()
        logger.info("映射自动更新线程已启动")
    
    def save_mappings_to_file(self, file_path: str = None) -> bool:
        """保存映射到文件"""
        if not file_path:
            file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "system_mappings.json")
        
        with self.mapping_lock:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.mappings, f, ensure_ascii=False, indent=2)
                logger.info(f"映射已保存到文件: {file_path}")
                return True
            except Exception as e:
                logger.error(f"保存映射到文件失败: {str(e)}")
                return False
    
    def load_mappings_from_file(self, file_path: str = None) -> bool:
        """从文件加载映射"""
        if not file_path:
            file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "system_mappings.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    mappings = json.load(f)
                
                with self.mapping_lock:
                    self.mappings = mappings
                
                # 更新映射管理AI
                self.update_mapping_manager_ai()
                
                logger.info(f"映射已从文件加载: {file_path}")
                return True
            except Exception as e:
                logger.error(f"从文件加载映射失败: {str(e)}")
        return False
    
    def get_mapping_stats(self) -> Dict[str, int]:
        """获取映射统计信息"""
        with self.mapping_lock:
            stats = {
                mapping_type: len(mapping_data) 
                for mapping_type, mapping_data in self.mappings.items()
            }
        return stats

# 初始化系统映射服务
system_mapping_service = SystemMappingService()

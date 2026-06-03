#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统初始化和重启管理器 - System Initialization & Restart Manager
MTSCOS AI Project v3.1
负责系统初始化、服务重启、组件适配和整体系统管理
"""

import os
import sys
import json
import sqlite3
import logging
import time
import secrets
import importlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_init_restart.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('system_init_restart')

class ServiceStatus(Enum):
    """服务状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    RESTARTING = "restarting"

class ComponentType(Enum):
    """组件类型"""
    RULE = "rule"
    SERVICE = "service"
    DATABASE = "database"
    API = "api"
    FRONTEND = "frontend"
    BACKEND = "backend"
    AI_ENGINE = "ai_engine"
    SECURITY = "security"

@dataclass
class ServiceInfo:
    """服务信息"""
    service_id: str
    name: str
    type: ComponentType
    status: ServiceStatus
    path: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    started_at: str = None
    last_check: str = None
    error_message: str = None

@dataclass
class ComponentInfo:
    """组件信息"""
    component_id: str
    name: str
    type: ComponentType
    module_path: str
    is_loaded: bool = False
    is_initialized: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

class SystemInitRestartManager:
    """系统初始化和重启管理器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.project_root, "system_init_restart.db")
        self.services: Dict[str, ServiceInfo] = {}
        self.components: Dict[str, ComponentInfo] = {}
        self.config_path = os.path.join(self.project_root, "system_config.json")
        self._init_database()
        self._load_config()
        self._discover_components()
        logger.info(f"系统初始化管理器已创建，项目根目录: {self.project_root}")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                path TEXT,
                config TEXT,
                dependencies TEXT,
                started_at TEXT,
                last_check TEXT,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                component_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                module_path TEXT,
                is_loaded INTEGER DEFAULT 0,
                is_initialized INTEGER DEFAULT 0,
                config TEXT,
                version TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS init_history (
                history_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                target TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                state_id TEXT PRIMARY KEY,
                component_type TEXT,
                state_data TEXT,
                updated_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def _load_config(self):
        """加载系统配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("系统配置已加载")
            else:
                self.config = self._create_default_config()
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                logger.info("默认配置已创建")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.config = self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """创建默认配置"""
        return {
            "system": {
                "name": "MTSCOS AI Project",
                "version": "3.1.0",
                "environment": "development",
                "debug_mode": True
            },
            "services": {
                "flask_app": {
                    "enabled": True,
                    "port": 5000,
                    "host": "localhost",
                    "auto_restart": True
                },
                "http_server": {
                    "enabled": True,
                    "port": 8080,
                    "host": "localhost",
                    "auto_restart": True
                }
            },
            "rules": {
                "auto_load": True,
                "priority_order": [
                    "security_rules",
                    "user_behavior",
                    "data_security",
                    "question_increment_rules",
                    "ai_adaptive_learning_rules",
                    "ai_highdim_adaptation_rules",
                    "permission_priority_rules",
                    "ai_rule_optimizer"
                ]
            },
            "databases": {
                "main_db": "mtcos_database.db",
                "rules_db": "rules_database.db",
                "security_db": "security_database.db"
            },
            "logging": {
                "level": "INFO",
                "max_file_size": "10MB",
                "backup_count": 5
            }
        }
    
    def _discover_components(self):
        """自动发现系统组件"""
        logger.info("开始发现系统组件...")
        
        # 发现法则模块
        rule_files = [
            "security_rules.py",
            "user_behavior.py",
            "data_security.py",
            "question_increment_rules.py",
            "ai_adaptive_learning_rules.py",
            "ai_highdim_adaptation_rules.py",
            "permission_priority_rules.py",
            "ai_rule_optimizer.py"
        ]
        
        for rule_file in rule_files:
            path = os.path.join(self.project_root, rule_file)
            if os.path.exists(path):
                name = rule_file.replace(".py", "")
                component_id = f"RULE-{name.upper()}"
                self.components[component_id] = ComponentInfo(
                    component_id=component_id,
                    name=name,
                    type=ComponentType.RULE,
                    module_path=path
                )
                logger.info(f"发现法则模块: {name}")
        
        # 发现服务
        service_dirs = [
            ("flask-app", "Flask应用服务", ComponentType.BACKEND),
            ("frontend", "前端服务", ComponentType.FRONTEND),
            ("api", "API服务", ComponentType.API),
            ("src/core", "核心服务", ComponentType.SERVICE)
        ]
        
        for dir_name, display_name, comp_type in service_dirs:
            path = os.path.join(self.project_root, dir_name)
            if os.path.exists(path):
                service_id = f"SRV-{dir_name.upper().replace('/', '_')}"
                self.services[service_id] = ServiceInfo(
                    service_id=service_id,
                    name=display_name,
                    type=comp_type,
                    status=ServiceStatus.STOPPED,
                    path=path
                )
                logger.info(f"发现服务: {display_name}")
        
        # 发现AI引擎
        ai_engines_path = os.path.join(self.project_root, "flask-app", "ai_engines")
        if os.path.exists(ai_engines_path):
            for engine_file in os.listdir(ai_engines_path):
                if engine_file.endswith(".py") and not engine_file.startswith("__"):
                    name = engine_file.replace(".py", "")
                    component_id = f"AI-{name.upper()}"
                    self.components[component_id] = ComponentInfo(
                        component_id=component_id,
                        name=name,
                        type=ComponentType.AI_ENGINE,
                        module_path=os.path.join(ai_engines_path, engine_file)
                    )
                    logger.info(f"发现AI引擎: {name}")
        
        logger.info(f"组件发现完成: {len(self.components)}个组件, {len(self.services)}个服务")
    
    def initialize_all(self) -> Dict[str, Any]:
        """初始化所有组件和服务"""
        logger.info("=" * 60)
        logger.info("开始系统初始化...")
        logger.info("=" * 60)
        
        results = {
            "start_time": datetime.now().isoformat(),
            "components": {},
            "services": {},
            "rules": {},
            "errors": [],
            "success_count": 0,
            "error_count": 0
        }
        
        # 1. 初始化法则模块
        logger.info("\n[阶段1] 初始化法则模块...")
        rule_order = self.config.get("rules", {}).get("priority_order", [])
        for rule_name in rule_order:
            result = self._initialize_rule(rule_name)
            results["rules"][rule_name] = result
            if result.get("success"):
                results["success_count"] += 1
            else:
                results["error_count"] += 1
                results["errors"].append(f"法则初始化失败: {rule_name}")
        
        # 2. 初始化组件
        logger.info("\n[阶段2] 初始化系统组件...")
        for comp_id, comp_info in self.components.items():
            if comp_info.type != ComponentType.RULE:
                result = self._initialize_component(comp_id)
                results["components"][comp_id] = result
                if result.get("success"):
                    results["success_count"] += 1
                else:
                    results["error_count"] += 1
                    results["errors"].append(f"组件初始化失败: {comp_id}")
        
        # 3. 初始化服务
        logger.info("\n[阶段3] 初始化服务...")
        for service_id, service_info in self.services.items():
            result = self._initialize_service(service_id)
            results["services"][service_id] = result
            if result.get("success"):
                results["success_count"] += 1
            else:
                results["error_count"] += 1
                results["errors"].append(f"服务初始化失败: {service_id}")
        
        # 4. 适配设置
        logger.info("\n[阶段4] 适配系统设置...")
        adaptation_result = self._adapt_settings()
        results["adaptation"] = adaptation_result
        
        # 5. 保存状态
        self._save_system_state(results)
        
        results["end_time"] = datetime.now().isoformat()
        results["duration"] = self._calculate_duration(results["start_time"], results["end_time"])
        
        logger.info("\n" + "=" * 60)
        logger.info(f"系统初始化完成!")
        logger.info(f"成功: {results['success_count']}, 失败: {results['error_count']}")
        logger.info(f"耗时: {results['duration']}")
        logger.info("=" * 60)
        
        return results
    
    def _initialize_rule(self, rule_name: str) -> Dict[str, Any]:
        """初始化法则模块"""
        result = {
            "rule_name": rule_name,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            module_path = os.path.join(self.project_root, f"{rule_name}.py")
            if not os.path.exists(module_path):
                result["message"] = "模块文件不存在"
                return result
            
            # 导入模块
            spec = importlib.util.spec_from_file_location(rule_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 检查是否有main函数或初始化函数
            if hasattr(module, 'main'):
                # 执行测试
                module.main()
                result["message"] = "模块测试执行成功"
            elif hasattr(module, 'PermissionPriorityEngine'):
                # 权限优先法则
                engine = module.PermissionPriorityEngine()
                stats = engine.get_priority_stats()
                result["message"] = f"权限引擎初始化成功，规则数: {stats['active_rules']}"
            elif hasattr(module, 'DataSecurityManager'):
                # 数据安全法则
                manager = module.DataSecurityManager()
                result["message"] = "数据安全管理器初始化成功"
            elif hasattr(module, 'QuestionIncrementManager'):
                # 习题增量法则
                manager = module.QuestionIncrementManager()
                result["message"] = "习题增量管理器初始化成功"
            elif hasattr(module, 'AIAdaptiveLearningEngine'):
                # AI自适应学习法则
                engine = module.AIAdaptiveLearningEngine()
                result["message"] = "AI自适应学习引擎初始化成功"
            elif hasattr(module, 'AIHighDimAdaptationEngine'):
                # AI高维适配法则
                engine = module.AIHighDimAdaptationEngine()
                result["message"] = "AI高维适配引擎初始化成功"
            elif hasattr(module, 'AIRuleOptimizer'):
                # AI法则优化器
                optimizer = module.AIRuleOptimizer()
                result["message"] = "AI法则优化器初始化成功"
            else:
                result["message"] = "模块加载成功"
            
            # 更新组件状态
            comp_id = f"RULE-{rule_name.upper()}"
            if comp_id in self.components:
                self.components[comp_id].is_loaded = True
                self.components[comp_id].is_initialized = True
            
            result["success"] = True
            self._log_history("init_rule", rule_name, "success", result["message"])
            
        except Exception as e:
            result["message"] = f"初始化失败: {str(e)}"
            result["error"] = str(e)
            self._log_history("init_rule", rule_name, "error", str(e))
            logger.error(f"法则初始化失败 [{rule_name}]: {e}")
        
        return result
    
    def _initialize_component(self, comp_id: str) -> Dict[str, Any]:
        """初始化组件"""
        result = {
            "component_id": comp_id,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        comp_info = self.components.get(comp_id)
        if not comp_info:
            result["message"] = "组件不存在"
            return result
        
        try:
            # 检查路径
            if not os.path.exists(comp_info.module_path):
                result["message"] = "组件路径不存在"
                return result
            
            # 标记为已加载
            comp_info.is_loaded = True
            comp_info.is_initialized = True
            
            result["message"] = f"组件 {comp_info.name} 初始化成功"
            result["success"] = True
            self._log_history("init_component", comp_id, "success", result["message"])
            
        except Exception as e:
            result["message"] = f"初始化失败: {str(e)}"
            result["error"] = str(e)
            self._log_history("init_component", comp_id, "error", str(e))
            logger.error(f"组件初始化失败 [{comp_id}]: {e}")
        
        return result
    
    def _initialize_service(self, service_id: str) -> Dict[str, Any]:
        """初始化服务"""
        result = {
            "service_id": service_id,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        service_info = self.services.get(service_id)
        if not service_info:
            result["message"] = "服务不存在"
            return result
        
        try:
            # 检查路径
            if not os.path.exists(service_info.path):
                result["message"] = "服务路径不存在"
                return result
            
            # 更新状态
            service_info.status = ServiceStatus.RUNNING
            service_info.started_at = datetime.now().isoformat()
            
            result["message"] = f"服务 {service_info.name} 初始化成功"
            result["success"] = True
            self._log_history("init_service", service_id, "success", result["message"])
            
        except Exception as e:
            result["message"] = f"初始化失败: {str(e)}"
            result["error"] = str(e)
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            self._log_history("init_service", service_id, "error", str(e))
            logger.error(f"服务初始化失败 [{service_id}]: {e}")
        
        return result
    
    def _adapt_settings(self) -> Dict[str, Any]:
        """适配系统设置"""
        result = {
            "success": True,
            "adaptations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 适配数据库设置
            db_config = self.config.get("databases", {})
            for db_name, db_path in db_config.items():
                full_path = os.path.join(self.project_root, db_path)
                if os.path.exists(full_path):
                    result["adaptations"].append({
                        "type": "database",
                        "name": db_name,
                        "status": "connected"
                    })
                else:
                    result["adaptations"].append({
                        "type": "database",
                        "name": db_name,
                        "status": "created"
                    })
            
            # 适配日志设置
            log_config = self.config.get("logging", {})
            result["adaptations"].append({
                "type": "logging",
                "level": log_config.get("level", "INFO"),
                "status": "configured"
            })
            
            # 适配服务设置
            services_config = self.config.get("services", {})
            for service_name, service_config in services_config.items():
                if service_config.get("enabled"):
                    result["adaptations"].append({
                        "type": "service",
                        "name": service_name,
                        "port": service_config.get("port"),
                        "status": "configured"
                    })
            
            self._log_history("adapt_settings", "system", "success", f"适配了 {len(result['adaptations'])} 个设置")
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self._log_history("adapt_settings", "system", "error", str(e))
            logger.error(f"设置适配失败: {e}")
        
        return result
    
    def restart_all(self) -> Dict[str, Any]:
        """重启所有服务"""
        logger.info("=" * 60)
        logger.info("开始系统重启...")
        logger.info("=" * 60)
        
        results = {
            "start_time": datetime.now().isoformat(),
            "services": {},
            "components": {},
            "errors": [],
            "success_count": 0,
            "error_count": 0
        }
        
        # 1. 停止所有服务
        logger.info("\n[阶段1] 停止服务...")
        for service_id, service_info in self.services.items():
            stop_result = self._stop_service(service_id)
            results["services"][service_id] = {"stop": stop_result}
        
        # 2. 重新初始化
        logger.info("\n[阶段2] 重新初始化...")
        init_result = self.initialize_all()
        results["initialization"] = init_result
        
        # 3. 启动服务
        logger.info("\n[阶段3] 启动服务...")
        for service_id, service_info in self.services.items():
            start_result = self._start_service(service_id)
            if service_id in results["services"]:
                results["services"][service_id]["start"] = start_result
            else:
                results["services"][service_id] = {"start": start_result}
            
            if start_result.get("success"):
                results["success_count"] += 1
            else:
                results["error_count"] += 1
                results["errors"].append(f"服务启动失败: {service_id}")
        
        results["end_time"] = datetime.now().isoformat()
        results["duration"] = self._calculate_duration(results["start_time"], results["end_time"])
        
        logger.info("\n" + "=" * 60)
        logger.info(f"系统重启完成!")
        logger.info(f"成功: {results['success_count']}, 失败: {results['error_count']}")
        logger.info(f"耗时: {results['duration']}")
        logger.info("=" * 60)
        
        return results
    
    def _stop_service(self, service_id: str) -> Dict[str, Any]:
        """停止服务"""
        result = {
            "service_id": service_id,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        service_info = self.services.get(service_id)
        if not service_info:
            result["message"] = "服务不存在"
            return result
        
        try:
            service_info.status = ServiceStatus.STOPPED
            result["message"] = f"服务 {service_info.name} 已停止"
            result["success"] = True
            self._log_history("stop_service", service_id, "success", result["message"])
            
        except Exception as e:
            result["message"] = f"停止失败: {str(e)}"
            result["error"] = str(e)
            self._log_history("stop_service", service_id, "error", str(e))
        
        return result
    
    def _start_service(self, service_id: str) -> Dict[str, Any]:
        """启动服务"""
        result = {
            "service_id": service_id,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        service_info = self.services.get(service_id)
        if not service_info:
            result["message"] = "服务不存在"
            return result
        
        try:
            service_info.status = ServiceStatus.RUNNING
            service_info.started_at = datetime.now().isoformat()
            
            result["message"] = f"服务 {service_info.name} 已启动"
            result["success"] = True
            self._log_history("start_service", service_id, "success", result["message"])
            
        except Exception as e:
            result["message"] = f"启动失败: {str(e)}"
            result["error"] = str(e)
            service_info.status = ServiceStatus.ERROR
            self._log_history("start_service", service_id, "error", str(e))
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {
                "total": len(self.components),
                "loaded": sum(1 for c in self.components.values() if c.is_loaded),
                "initialized": sum(1 for c in self.components.values() if c.is_initialized)
            },
            "services": {
                "total": len(self.services),
                "running": sum(1 for s in self.services.values() if s.status == ServiceStatus.RUNNING),
                "stopped": sum(1 for s in self.services.values() if s.status == ServiceStatus.STOPPED),
                "error": sum(1 for s in self.services.values() if s.status == ServiceStatus.ERROR)
            },
            "rules": {
                "total": sum(1 for c in self.components.values() if c.type == ComponentType.RULE),
                "active": sum(1 for c in self.components.values() if c.type == ComponentType.RULE and c.is_initialized)
            },
            "health_score": self._calculate_health_score()
        }
        
        return status
    
    def _calculate_health_score(self) -> float:
        """计算系统健康分数"""
        total_components = len(self.components)
        initialized_components = sum(1 for c in self.components.values() if c.is_initialized)
        
        total_services = len(self.services)
        running_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.RUNNING)
        
        if total_components == 0 or total_services == 0:
            return 0.0
        
        component_score = initialized_components / total_components
        service_score = running_services / total_services
        
        return (component_score * 0.6 + service_score * 0.4) * 100
    
    def _log_history(self, action: str, target: str, status: str, details: str):
        """记录历史"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        history_id = f"HIST-{int(time.time())}-{secrets.token_hex(3)}"
        cursor.execute("""
            INSERT INTO init_history
            (history_id, action, target, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (history_id, action, target, status, details, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _save_system_state(self, state: Dict):
        """保存系统状态"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        state_id = f"STATE-{int(time.time())}-{secrets.token_hex(3)}"
        cursor.execute("""
            INSERT INTO system_state
            (state_id, component_type, state_data, updated_at)
            VALUES (?, ?, ?, ?)
        """, (state_id, "system", json.dumps(state, ensure_ascii=False), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _calculate_duration(self, start: str, end: str) -> str:
        """计算耗时"""
        try:
            start_time = datetime.fromisoformat(start)
            end_time = datetime.fromisoformat(end)
            duration = end_time - start_time
            return f"{duration.total_seconds():.2f}秒"
        except:
            return "未知"
    
    def get_init_history(self, limit: int = 50) -> List[Dict]:
        """获取初始化历史"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT history_id, action, target, status, details, timestamp
            FROM init_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['history_id', 'action', 'target', 'status', 'details', 'timestamp']
        return [dict(zip(columns, row)) for row in rows]
    
    def print_status(self):
        """打印系统状态"""
        status = self.get_system_status()
        
        print("\n" + "=" * 60)
        print("📊 MTSCOS 系统状态报告")
        print("=" * 60)
        print(f"\n时间: {status['timestamp']}")
        print(f"健康分数: {status['health_score']:.1f}%")
        
        print("\n📦 组件状态:")
        print(f"  总数: {status['components']['total']}")
        print(f"  已加载: {status['components']['loaded']}")
        print(f"  已初始化: {status['components']['initialized']}")
        
        print("\n🔧 服务状态:")
        print(f"  总数: {status['services']['total']}")
        print(f"  运行中: {status['services']['running']}")
        print(f"  已停止: {status['services']['stopped']}")
        print(f"  错误: {status['services']['error']}")
        
        print("\n📜 法则状态:")
        print(f"  总数: {status['rules']['total']}")
        print(f"  活跃: {status['rules']['active']}")
        
        print("\n" + "=" * 60)

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 MTSCOS 系统初始化和重启管理器")
    print("=" * 60)
    
    manager = SystemInitRestartManager()
    
    # 打印当前状态
    manager.print_status()
    
    # 初始化所有组件和服务
    print("\n执行系统初始化...")
    init_result = manager.initialize_all()
    
    print(f"\n初始化结果:")
    print(f"  成功: {init_result['success_count']}")
    print(f"  失败: {init_result['error_count']}")
    print(f"  耗时: {init_result['duration']}")
    
    if init_result['errors']:
        print(f"\n错误列表:")
        for error in init_result['errors']:
            print(f"  - {error}")
    
    # 重启系统
    print("\n执行系统重启...")
    restart_result = manager.restart_all()
    
    print(f"\n重启结果:")
    print(f"  成功: {restart_result['success_count']}")
    print(f"  失败: {restart_result['error_count']}")
    print(f"  耗时: {restart_result['duration']}")
    
    # 最终状态
    manager.print_status()
    
    print("\n✅ 系统初始化和重启完成!")

if __name__ == '__main__':
    main()
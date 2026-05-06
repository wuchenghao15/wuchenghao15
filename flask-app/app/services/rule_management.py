#!/usr/bin/env python3
"""
系统规则管理服务，负责收集、整合、管理和执行所有系统规则

import os
# JSON import removed - using database
import time
import threading
from app.utils.logging import logger
# 延迟导入，避免循环导入
_ai_instance_manager = None

def _get_ai_instance_manager():
    global _ai_instance_manager
    if _ai_instance_manager is None:
        from app.ai.instances import ai_instance_manager
        _ai_instance_manager = ai_instance_manager
    return _ai_instance_manager

class RuleManagementService:
    """规则管理服务，负责收集、整合、管理和执行所有系统规则"""

    def __init__(self):
        self.rules = {
            "permission_rules": {},
            "security_rules": {},
            "business_rules": {},
            "test_rules": {},
            "ai_management_rules": {}
        }
        self.rule_lock = threading.Lock()
        self.rule_manager_ai = None
        self.auto_update_enabled = True  # 启用自动更新，使用后台线程
        self.monitoring_enabled = True
        self.update_interval = 3600  # 默认1小时更新一次
        self.rule_sources = {
            "permission_rules": [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "src", "data", "permission-rules.json")
            ],
            "security_rules": [
                os.path.join(os.path.dirname(__file__), "..", "utils", "security.py")
            ],
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "system-rules.json")
            ],
                os.path.join(os.path.dirname(__file__), "..", "ai", "test_generator.py")
            ]
        }
        # 初始化规则管理AI
        self.init_rule_manager_ai()

        # 启动自动更新线程
        if self.auto_update_enabled:
            self.start_auto_update()

    def init_rule_manager_ai(self):
        """初始化规则管理AI员工"""
        try:
            # 跳过AI实例创建，避免循环依赖
            # 注意：这里移除了对AI实例管理器的依赖，解决循环依赖问题
            logger.info("跳过规则管理AI初始化，避免循环依赖")
            self.rule_manager_ai = None
        except Exception as e:
            self.rule_manager_ai = None

        """更新规则管理AI配置"""
        try:
            # 跳过AI实例更新，避免循环依赖
            logger.info("跳过规则管理AI配置更新，避免循环依赖")
        except Exception as e:
            logger.error(f"更新规则管理AI配置失败: {str(e)}")

        """收集所有系统规则"""
        logger.info("开始收集系统规则...")

            # 收集权限规则
            self._collect_permission_rules()

            # 收集安全规则
            self._collect_security_rules()

            # 收集业务规则
            self._collect_business_rules()

            # 收集测试规则
            self._collect_test_rules()

            # 收集AI管理规则
            self._collect_ai_management_rules()

        # 更新规则管理AI
        self.update_rule_manager_ai()

        logger.info("系统规则收集完成")
        return self.rules

    def _collect_permission_rules(self):
        """收集权限规则"""
        permission_rules = {}

        for source in self.rule_sources["permission_rules"]:
            if os.path.exists(source) and source.endswith(".json"):
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                        permission_rules.update(rules)
                except Exception as e:
                    logger.error(f"从 {source} 收集权限规则失败: {str(e)}")
        self.rules["permission_rules"] = permission_rules

    def _collect_security_rules(self):
        """收集安全规则"""
        security_rules = {
        }
        for source in self.rule_sources["security_rules"]:
            if os.path.exists(source) and source.endswith(".py"):
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 提取role_permissions字典
                    import re
                    role_permissions_match = re.search(r'role_permissions = (\{.*?\})', content, re.DOTALL)
                        role_permissions_str = role_permissions_match.group(1)
                        # 修复字符串格式以便安全评估
                        role_permissions_str = role_permissions_str.replace('"', '\\"')
                        role_permissions_str = role_permissions_str.replace("'", '\\"')
                        # 移除注释

                        try:
                            role_permissions = eval(role_permissions_str)
                            security_rules["role_permissions"] = role_permissions
                        except Exception as e:
                            logger.error(f"解析细粒度权限规则失败: {str(e)}")
                except Exception as e:
                    logger.error(f"从 {source} 收集安全规则失败: {str(e)}")
        self.rules["security_rules"] = security_rules

    def _collect_business_rules(self):
        """收集业务规则"""
        business_rules = {}

            if os.path.exists(source) and source.endswith(".json"):
                    with open(source, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                        business_rules.update(rules)
                except Exception as e:
                    logger.error(f"从 {source} 收集业务规则失败: {str(e)}")


    def _collect_test_rules(self):
        """收集测试规则"""
        test_rules = {
            "test_generator": {
                "admin_cannot_test": True,
                "guest_default_levels": {
                },
                "user_level_assessment": True,
            }
        for source in self.rule_sources["test_rules"]:
                # 可以从test_generator.py中提取更多规则
                pass

        self.rules["test_rules"] = test_rules

    def _collect_ai_management_rules(self):
        """收集AI管理规则"""
        ai_management_rules = {
            "ai_instance_management": {
                "max_instances_per_user": 5,
                "instance_id_format": "^[a-z0-9_-]{3,32}$",
                "instance_name_required": True,
                "instance_description_min_length": 10
            },
            "ai_security": {
                "sandbox_required": True,
                "function_whitelist": ["rule_management", "rule_execution", "rule_optimization", "rule_monitoring", "rule_extension"],
                "config_validation_required": True
            },
            "ai_performance": {
                "max_response_time": 5,
                "auto_cleanup_inactive_instances": True,
            },
            "ai_decision_rules": {
                "decision_required": True,
                "rule_based_decision": True,
                "permission_check_required": True,
                "audit_log_required": True,
                "decision_timeout": 30
            },
            "ai_permission_rules": {
                "super_admin_permissions": ["create_instance", "delete_instance", "update_instance", "view_all_instances", "manage_rules"],
                "admin_permissions": ["create_instance", "update_instance", "view_own_instances"],
                "user_permissions": ["view_own_instances", "use_instances"],
                "guest_permissions": ["use_public_instances"],
                "role_based_access_control": True,
            },
            "ai_constraint_rules": {
                "instance_type_constraints": {
                    "technical": {"max_instances": 10, "allowed_functions": ["hardware_management", "system_monitoring", "technical_support"]},
                    "general": {"max_instances": 20, "allowed_functions": ["general_assistant", "content_generation", "data_analysis"]}
                },
                "function_constraints": {
                    "rule_management": {"requires_role": "super_admin"},
                    "hardware_management": {"requires_role": "hardware_admin"}
                }
            "config_constraints": {
                "max_config_size": 1024 * 1024,
                "allowed_config_keys": ["version", "vikey_support", "usb_detection", "driver_management", "auto_healing"]
            },
                "admin_redirect": "main.index",
                "manager_redirect": "main.index",
                "user_redirect": "main.index",
                "guest_redirect": "language_tests.test_system",
                "default_redirect": "main.index",
                "always_redirect_after_login": True,
                "preserve_original_url": False
        self.rules["ai_management_rules"] = ai_management_rules

    def add_rule_source(self, rule_type, source_path):
        """添加规则源"""
        if rule_type in self.rule_sources:
                self.rule_sources[rule_type].append(source_path)
                logger.info(f"已添加规则源: {source_path} 到 {rule_type}")
                # 收集新规则
                self.collect_rules()
                return True

    def remove_rule_source(self, rule_type, source_path):
        """移除规则源"""
            if source_path in self.rule_sources[rule_type]:
                self.rule_sources[rule_type].remove(source_path)
                logger.info(f"已移除规则源: {source_path} 从 {rule_type}")
                # 重新收集规则
                self.collect_rules()
                return True
        return False

    def get_rules(self, rule_type=None):
        """获取规则"""
        with self.rule_lock:
            if rule_type:
                return self.rules.get(rule_type, {})
            return self.rules.copy()

    def add_rule(self, rule_type, rule_name, rule_content):
        """添加规则"""
        with self.rule_lock:
            if rule_type in self.rules:
                self.rules[rule_type][rule_name] = rule_content
                logger.info(f"已添加规则: {rule_name} 到 {rule_type}")
                # 更新规则管理AI
                self.update_rule_manager_ai()
                return True
        return False

    def update_rule(self, rule_type, rule_name, rule_content):
        """更新规则"""
        with self.rule_lock:
            if rule_type in self.rules and rule_name in self.rules[rule_type]:
                self.rules[rule_type][rule_name] = rule_content
                logger.info(f"已更新规则: {rule_name} 到 {rule_type}")
                self.update_rule_manager_ai()
                return True

    def delete_rule(self, rule_type, rule_name):
        """删除规则"""
            if rule_type in self.rules and rule_name in self.rules[rule_type]:
                del self.rules[rule_type][rule_name]
                # 更新规则管理AI
                self.update_rule_manager_ai()
        return False

    def validate_rule(self, rule_type, rule_name, rule_content):
        """验证规则"""
        if self.rule_manager_ai:
            # 这里可以实现更复杂的规则验证逻辑
            logger.info(f"验证规则: {rule_name} 类型: {rule_type}")
            return True
        return False

        """优化规则"""
        # 调用规则管理AI进行规则优化
        if self.rule_manager_ai:
            # 这里可以实现规则优化逻辑
            logger.info("规则优化完成")
            return True
        return False

    def monitor_rules(self):
        """监控规则执行情况"""
            logger.info("开始监控规则执行情况")
            # 这里可以实现规则监控逻辑
            logger.info("规则监控完成")
            return True

    def start_auto_update(self):
        """启动自动更新线程"""
        def auto_update_thread():
            while self.auto_update_enabled:
                time.sleep(self.update_interval)
                self.collect_rules()
                self.optimize_rules()
                if self.monitoring_enabled:
                    self.monitor_rules()
        thread = threading.Thread(target=auto_update_thread, daemon=True)
        thread.start()
        logger.info("规则自动更新线程已启动")

    def save_rules_to_file(self, file_path=None):
        """保存规则到文件"""
        if not file_path:
            file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "integrated_ruleset.json")

        with self.rule_lock:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.rules, f, ensure_ascii=False, indent=2)
                logger.info(f"规则已保存到文件: {file_path}")
                return True
            except Exception as e:
                logger.error(f"保存规则到文件失败: {str(e)}")
                return False

    def load_rules_from_file(self, file_path=None):
        """从文件加载规则"""
        if not file_path:

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)

                with self.rule_lock:
                    self.rules = rules


                logger.info(f"规则已从文件加载: {file_path}")
                return True
                logger.error(f"从文件加载规则失败: {str(e)}")
        return False

    def get_rule_manager_ai(self):
        return self.rule_manager_ai

    def set_auto_update(self, enabled):
        """设置自动更新"""
        self.auto_update_enabled = enabled
            self.update_rule_manager_ai()
        logger.info(f"规则自动更新已{'启用' if enabled else '禁用'}")

    def set_monitoring(self, enabled):
        """设置监控"""
        if self.rule_manager_ai:
        logger.info(f"规则监控已{'启用' if enabled else '禁用'}")

    def set_update_interval(self, interval):
        """设置更新间隔"""
        self.update_interval = interval
        if self.rule_manager_ai:
            self.update_rule_manager_ai()

rule_management_service = RuleManagementService()

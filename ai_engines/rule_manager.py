#!/usr/bin/env python3
"""
AI规则管理器: 负责管理和执行系统规则
"""
import time
import threading
from app.utils.logging import logger
from app.services.rule_management import rule_management_service
from app.models.rule import Rule

class AIRuleManager:
    """AI规则管理器: 负责管理和执行系统规则"""

    def __init__(self):
        self.ai_id = "rule_manager_ai"
        self.name = "规则管理AI"
        self.description = "负责管理和执行系统所有规则的AI模块"
        self.status = "active"
        self.created_at = time.time()
        self.updated_at = time.time()
        self.rules = {}
        self.rule_execution_history = []
        self.monitoring_enabled = True
        self.auto_optimize_enabled = True
        self.lock = threading.Lock()

        self._init_rules()

        if self.monitoring_enabled:
            self._start_monitoring_thread()

        logger.info("AI规则管理器初始化完成")

    def _init_rules(self):
        """初始化规则"""
        self.rules = rule_management_service.get_rules()
        logger.info(f"初始化规则完成, 共加载 {sum(len(rules) for rules in self.rules.values())} 个规则")

    def _start_monitoring_thread(self):
        """启动规则监控线程"""
        def monitoring_thread():
            while self.monitoring_enabled:
                self.monitor_rules()
                time.sleep(300)

        thread = threading.Thread(target=monitoring_thread, daemon=True)
        thread.start()
        logger.info("规则监控线程已启动")

    def load_rules(self):
        """加载规则"""
        self.rules = rule_management_service.get_rules()
        return self.rules

    def execute_rule(self, rule_type, rule_name, **kwargs):
        """执行指定规则"""
        with self.lock:
            user_role = kwargs.get('user_role', 'guest')
            from app.services.rule_management import rule_management_service
            permission_rules = rule_management_service.get_rules().get("ai_permission_rules", {})
            user_permissions = permission_rules.get(f"{user_role}_permissions", [])

            if "rule_execution" not in user_permissions:
                logger.error(f"权限不足: 用户角色 {user_role} 没有执行规则的权限")
                return False

            if rule_type not in self.rules or rule_name not in self.rules[rule_type]:
                logger.error(f"规则不存在: {rule_type}.{rule_name}")
                return False

            rule_content = self.rules[rule_type][rule_name]
            result = self._execute_rule_logic(rule_content, **kwargs)

            self.rule_execution_history.append({
                "rule_type": rule_type,
                "rule_name": rule_name,
                "timestamp": time.time(),
                "status": "success" if result else "error",
                "kwargs": kwargs
            })

            return result

    def _execute_rule_logic(self, rule_content, **kwargs):
        if isinstance(rule_content, dict):
            rule_action = rule_content.get("action")
            rule_conditions = rule_content.get("conditions", [])
            rule_parameters = rule_content.get("parameters", {})

            all_conditions_met = True
            for condition in rule_conditions:
                condition_met = self._check_condition(condition, **kwargs)
                if not condition_met:
                    all_conditions_met = False
                    break

            if all_conditions_met:
                return self._execute_action(rule_action, rule_parameters, **kwargs)

        return False

    def _check_condition(self, condition, **kwargs):
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if field in kwargs:
            actual_value = kwargs[field]

            if operator == "equals":
                return actual_value == value
            elif operator == "not_equals":
                return actual_value != value
            elif operator == "contains":
                return value in actual_value
            elif operator == "greater_than":
                return actual_value > value
            elif operator == "less_than":
                return actual_value < value

        return False

    def _execute_action(self, action, parameters, **kwargs):
        logger.info(f"执行动作: {action}, 参数: {parameters}")

        if action == "send_notification":
            message = parameters.get("message", "")
            recipient = parameters.get("recipient", "")
            logger.info(f"发送通知给 {recipient}: {message}")
            return True

        return False

    def execute_rules_by_type(self, rule_type, **kwargs):
        results = {}
        if rule_type in self.rules:
            for rule_name in self.rules[rule_type]:
                result = self.execute_rule(rule_type, rule_name, **kwargs)
                results[rule_name] = result
        return results

    def monitor_rules(self):
        """监控规则执行情况"""
        logger.info("开始监控规则执行情况")

        recent_executions = [exec for exec in self.rule_execution_history if time.time() - exec["timestamp"] < 3600]
        error_executions = [exec for exec in recent_executions if exec["status"] == "error"]

        if error_executions:
            logger.warning(f"最近1小时内有 {len(error_executions)} 个规则执行失败")

        self.load_rules()
        logger.info("规则监控完成")

    def optimize_rules(self):
        """优化规则"""
        if self.auto_optimize_enabled:
            logger.info("开始优化规则...")

            error_counts = {}
            for exec_record in self.rule_execution_history:
                rule_key = f"{exec_record['rule_type']}.{exec_record['rule_name']}"
                if exec_record['status'] == "error":
                    error_counts[rule_key] = error_counts.get(rule_key, 0) + 1

            for rule_key, error_count in error_counts.items():
                if error_count > 3:
                    rule_type, rule_name = rule_key.split(".")
                    logger.info(f"优化规则: {rule_key}")

            logger.info("规则优化完成")
            return True
        return False

    def add_rule(self, rule_type, rule_name, rule_content):
        result = rule_management_service.add_rule(rule_type, rule_name, rule_content)
        if result:
            self.load_rules()
        return result

    def update_rule(self, rule_type, rule_name, rule_content):
        """更新规则"""
        result = rule_management_service.update_rule(rule_type, rule_name, rule_content)
        if result:
            self.load_rules()
        return result

    def delete_rule(self, rule_type, rule_name):
        result = rule_management_service.delete_rule(rule_type, rule_name)
        if result:
            self.load_rules()
        return result

    def get_rule_execution_history(self, limit=100):
        return self.rule_execution_history[-limit:]

    def get_rule_stats(self):
        """获取规则统计信息"""
        total_executions = len(self.rule_execution_history)
        error_executions = len([exec for exec in self.rule_execution_history if exec["status"] == "error"])

        rule_type_counts = {}
        for rule_type in self.rules:
            rule_type_counts[rule_type] = len(self.rules[rule_type])

        return {
            "total_executions": total_executions,
            "error_executions": error_executions,
            "error_rate": error_executions / total_executions if total_executions > 0 else 0,
            "rule_type_counts": rule_type_counts
        }

    def enable_auto_optimize(self):
        """启用自动优化"""
        self.auto_optimize_enabled = True
        logger.info("规则自动优化已启用")

    def disable_auto_optimize(self):
        """禁用自动优化"""
        self.auto_optimize_enabled = False
        logger.info("规则自动优化已禁用")


rule_manager_ai = AIRuleManager()

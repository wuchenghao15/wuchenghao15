# -*- coding: utf-8 -*-
# MTSCOS AI Project 规则引擎 - 升级版本
"""
规则引擎负责规则的执行,包括条件评估和动作执行.
支持复杂条件表达式、规则优先级、规则冲突解决.
"""

from typing import Dict, Any, List, Optional
import time
import json
import re
from threading import Lock
from datetime import datetime

try:
    from app.utils.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    from app.rules import RULE_STATUS
except ImportError:
    RULE_STATUS = {"ACTIVE": "active", "INACTIVE": "inactive", "DISABLED": "disabled"}

class RuleEngine:
    """规则引擎 - 升级版本"""

    def __init__(self, rule_manager):
        self._rule_manager = rule_manager
        self._action_executors = {
            "send_notification": self._execute_send_notification,
            "update_system_config": self._execute_update_system_config,
            "execute_script": self._execute_execute_script,
            "send_alert": self._execute_send_alert,
            "grant_permission": self._execute_grant_permission,
            "revoke_permission": self._execute_revoke_permission,
            "log_event": self._execute_log_event,
            "send_email": self._execute_send_email,
            "call_api": self._execute_call_api,
            "transform_data": self._execute_transform_data,
            "redirect": self._execute_redirect,
            "set_variable": self._execute_set_variable
        }
        self._execution_history = []
        self._max_history = 1000
        self._lock = Lock()

    def execute_rule(self, rule_id: str, **context) -> Any:
        """执行指定规则"""
        rule = self._rule_manager.get_rule(rule_id)
        if not rule:
            logger.error(f"规则不存在: {rule_id}")
            return False

        if rule.get("status") != RULE_STATUS["ACTIVE"]:
            logger.info(f"规则 {rule_id} 未激活,跳过执行")
            return False

        logger.info(f"执行规则: {rule_id} (名称: {rule.get('name', '未命名')})")

        start_time = time.time()
        try:
            if not self._evaluate_conditions(rule.get("conditions", []), context):
                logger.info(f"规则 {rule_id} 条件不满足,跳过执行")
                self._record_execution(rule_id, False, "条件不满足", start_time)
                return False

            results = self._execute_actions(rule.get("actions", []), context)

            execution_time = time.time() - start_time
            self._record_execution(rule_id, True, None, start_time, execution_time)

            logger.info(f"规则 {rule_id} 执行完成,耗时 {execution_time:.3f} 秒")

            return results
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_execution(rule_id, False, str(e), start_time, execution_time)
            logger.error(f"执行规则 {rule_id} 失败: {str(e)}")
            return False

    def execute_rules_by_type(self, rule_type: str, **context) -> Dict[str, Any]:
        """执行指定类型的所有规则(按优先级排序)"""
        results = {}

        rules = self._rule_manager.get_rules(rule_type)
        rules.sort(key=lambda r: r.get("priority", 1), reverse=True)

        for rule in rules:
            if rule.get("status") == RULE_STATUS["ACTIVE"]:
                result = self.execute_rule(rule["id"], **context)
                results[rule["id"]] = result

        return results

    def execute_all_rules(self, **context) -> Dict[str, Any]:
        """执行所有激活的规则(按优先级排序)"""
        results = {}
        rules = self._rule_manager.get_rules()
        rules.sort(key=lambda r: r.get("priority", 1), reverse=True)

        for rule in rules:
            if rule.get("status") == RULE_STATUS["ACTIVE"]:
                result = self.execute_rule(rule["id"], **context)
                results[rule["id"]] = result

        return results

    def execute_rules_with_resolution(self, **context) -> Dict[str, Any]:
        """执行规则并处理规则冲突"""
        rules = self._rule_manager.get_rules()
        rules.sort(key=lambda r: r.get("priority", 1), reverse=True)

        results = {}
        executed_rules = []
        conflicts = []

        for rule in rules:
            if rule.get("status") != RULE_STATUS["ACTIVE"]:
                continue

            result = self.execute_rule(rule["id"], **context)
            
            if result:
                executed_rules.append(rule["id"])
                results[rule["id"]] = result

                conflicts = self._detect_conflicts(rule, executed_rules, results)
                if conflicts:
                    resolved = self._resolve_conflicts(conflicts, results)
                    results.update(resolved)

        return {
            "results": results,
            "executed_rules": executed_rules,
            "conflicts": conflicts
        }

    def _detect_conflicts(self, current_rule, executed_rules, results) -> List[Dict]:
        """检测规则冲突"""
        conflicts = []
        current_actions = current_rule.get("actions", [])

        for rule_id in executed_rules[:-1]:
            prev_result = results.get(rule_id)
            if not prev_result:
                continue

            for action in current_actions:
                action_type = action.get("type")
                params = action.get("parameters", {})

                if action_type == "update_system_config":
                    config_key = params.get("config_key")
                    if config_key in prev_result:
                        conflicts.append({
                            "rule1": rule_id,
                            "rule2": current_rule["id"],
                            "type": "config_conflict",
                            "key": config_key
                        })

                elif action_type == "grant_permission" or action_type == "revoke_permission":
                    user_id = params.get("user_id")
                    permission = params.get("permission")
                    if f"{user_id}:{permission}" in str(prev_result):
                        conflicts.append({
                            "rule1": rule_id,
                            "rule2": current_rule["id"],
                            "type": "permission_conflict",
                            "user_id": user_id,
                            "permission": permission
                        })

        return conflicts

    def _resolve_conflicts(self, conflicts, results) -> Dict[str, Any]:
        """解决规则冲突(高优先级规则优先)"""
        resolved = {}

        for conflict in conflicts:
            rule1 = self._rule_manager.get_rule(conflict["rule1"])
            rule2 = self._rule_manager.get_rule(conflict["rule2"])

            priority1 = rule1.get("priority", 1)
            priority2 = rule2.get("priority", 1)

            if priority2 > priority1:
                resolved[conflict["rule2"]] = {"conflict_resolved": True, "winner": conflict["rule2"]}
                logger.info(f"规则冲突已解决: {conflict['rule2']} 优先于 {conflict['rule1']}")
            else:
                resolved[conflict["rule1"]] = {"conflict_resolved": True, "winner": conflict["rule1"]}
                logger.info(f"规则冲突已解决: {conflict['rule1']} 优先于 {conflict['rule2']}")

        return resolved

    def _evaluate_conditions(self, conditions: List[Dict], context: Dict[str, Any]) -> bool:
        """评估规则条件(支持复杂表达式)"""
        if not conditions:
            return True

        results = []
        for condition in conditions:
            result = self._evaluate_condition(condition, context)
            results.append(result)

        combination = conditions[0].get("combination", "and").lower()

        if combination == "and":
            return all(results)
        elif combination == "or":
            return any(results)
        elif combination == "not":
            return not all(results)
        else:
            logger.error(f"不支持的条件组合方式: {combination}")
            return False

    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估单个条件"""
        condition_type = condition.get("type", "simple")

        if condition_type == "simple":
            return self._evaluate_simple_condition(condition, context)
        elif condition_type == "compound":
            return self._evaluate_compound_condition(condition, context)
        elif condition_type == "expression":
            return self._evaluate_expression_condition(condition, context)
        elif condition_type == "function":
            return self._evaluate_function_condition(condition, context)
        else:
            logger.error(f"不支持的条件类型: {condition_type}")
            return False

    def _evaluate_simple_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估简单条件"""
        field = condition.get("field")
        operator = condition.get("operator", "equals")
        value = condition.get("value")
        case_sensitive = condition.get("case_sensitive", True)

        actual_value = context.get(field)

        try:
            if not case_sensitive and isinstance(actual_value, str):
                actual_value = str(actual_value).lower()
                value = str(value).lower()

            if operator == "equals":
                return actual_value == value
            elif operator == "not_equals":
                return actual_value != value
            elif operator == "contains":
                return value in str(actual_value) if actual_value else False
            elif operator == "not_contains":
                return value not in str(actual_value) if actual_value else True
            elif operator == "greater_than":
                return float(actual_value) > float(value) if actual_value else False
            elif operator == "less_than":
                return float(actual_value) < float(value) if actual_value else False
            elif operator == "greater_or_equal":
                return float(actual_value) >= float(value) if actual_value else False
            elif operator == "less_or_equal":
                return float(actual_value) <= float(value) if actual_value else False
            elif operator == "in":
                return actual_value in value if isinstance(value, list) else False
            elif operator == "not_in":
                return actual_value not in value if isinstance(value, list) else True
            elif operator == "exists":
                return field in context
            elif operator == "not_exists":
                return field not in context
            elif operator == "startswith":
                return str(actual_value).startswith(str(value)) if actual_value else False
            elif operator == "endswith":
                return str(actual_value).endswith(str(value)) if actual_value else False
            elif operator == "regex":
                return bool(re.match(value, str(actual_value))) if actual_value else False
            elif operator == "not_regex":
                return not bool(re.match(value, str(actual_value))) if actual_value else True
            elif operator == "between":
                if isinstance(value, list) and len(value) == 2:
                    min_val, max_val = value
                    return min_val <= float(actual_value) <= max_val if actual_value else False
                return False
            elif operator == "not_between":
                if isinstance(value, list) and len(value) == 2:
                    min_val, max_val = value
                    return not (min_val <= float(actual_value) <= max_val) if actual_value else True
                return False
            else:
                logger.error(f"不支持的操作符: {operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"条件评估失败: {str(e)}")
            return False

    def _evaluate_compound_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估复合条件"""
        operator = condition.get("operator", "AND").upper()
        sub_conditions = condition.get("conditions", [])

        results = [self._evaluate_condition(c, context) for c in sub_conditions]

        if operator == "AND":
            return all(results)
        elif operator == "OR":
            return any(results)
        elif operator == "NOT":
            return not all(results)
        else:
            logger.error(f"不支持的复合操作符: {operator}")
            return False

    def _evaluate_expression_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估表达式条件"""
        expression = condition.get("expression")
        if not expression:
            return False

        try:
            local_vars = {k: v for k, v in context.items() if isinstance(v, (int, float, str, bool, list, dict))}
            return eval(expression, {}, local_vars)
        except Exception as e:
            logger.error(f"表达式评估失败: {str(e)}")
            return False

    def _evaluate_function_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估函数条件"""
        function_name = condition.get("function")
        params = condition.get("params", {})

        function_map = {
            "current_date": self._evaluate_current_date,
            "current_time": self._evaluate_current_time,
            "is_weekend": self._evaluate_is_weekend,
            "contains_all": self._evaluate_contains_all,
            "contains_any": self._evaluate_contains_any,
            "has_role": self._evaluate_has_role,
            "is_time_range": self._evaluate_is_time_range
        }

        if function_name in function_map:
            return function_map[function_name](params, context)
        else:
            logger.error(f"不支持的函数: {function_name}")
            return False

    def _evaluate_current_date(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估当前日期条件"""
        from datetime import date
        current_date = date.today()

        operator = params.get("operator", "equals")
        target_date_str = params.get("date", "2023-01-01")
        
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            logger.error(f"无效的日期格式: {target_date_str}")
            return False

        if operator == "equals":
            return current_date == target_date
        elif operator == "greater_than":
            return current_date > target_date
        elif operator == "less_than":
            return current_date < target_date
        elif operator == "greater_or_equal":
            return current_date >= target_date
        elif operator == "less_or_equal":
            return current_date <= target_date
        else:
            return False

    def _evaluate_current_time(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估当前时间条件"""
        from datetime import datetime
        current_time = datetime.now().time()

        operator = params.get("operator", "equals")
        target_time_str = params.get("time", "00:00")
        
        try:
            target_time = datetime.strptime(target_time_str, "%H:%M").time()
        except ValueError:
            logger.error(f"无效的时间格式: {target_time_str}")
            return False

        if operator == "equals":
            return current_time == target_time
        elif operator == "greater_than":
            return current_time > target_time
        elif operator == "less_than":
            return current_time < target_time
        elif operator == "greater_or_equal":
            return current_time >= target_time
        elif operator == "less_or_equal":
            return current_time <= target_time
        else:
            return False

    def _evaluate_is_weekend(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估是否为周末"""
        from datetime import datetime
        return datetime.now().weekday() >= 5

    def _evaluate_contains_all(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估是否包含所有指定值"""
        field = params.get("field")
        values = params.get("values", [])

        actual_value = context.get(field)
        if not actual_value:
            return False

        actual_str = str(actual_value)
        return all(val in actual_str for val in values)

    def _evaluate_contains_any(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估是否包含任何指定值"""
        field = params.get("field")
        values = params.get("values", [])

        actual_value = context.get(field)
        if not actual_value:
            return False

        actual_str = str(actual_value)
        return any(val in actual_str for val in values)

    def _evaluate_has_role(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估用户是否具有指定角色"""
        user_roles = context.get("user_roles", [])
        required_role = params.get("role")

        return required_role in user_roles

    def _evaluate_is_time_range(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估当前时间是否在指定范围内"""
        from datetime import datetime
        current_time = datetime.now().time()

        start_time_str = params.get("start", "09:00")
        end_time_str = params.get("end", "18:00")

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            logger.error(f"无效的时间格式")
            return False

        return start_time <= current_time <= end_time

    def _execute_actions(self, actions: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Any]:
        """执行规则动作"""
        results = []
        for action in actions:
            result = self._execute_action(action, context)
            results.append(result)
        return results

    def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """执行单个动作"""
        action_type = action.get("type")
        parameters = action.get("parameters", {})

        executor = self._action_executors.get(action_type)
        if not executor:
            logger.error(f"不支持的动作类型: {action_type}")
            return False

        try:
            result = executor(parameters, context)
            logger.info(f"执行动作 {action_type} 成功")
            return result
        except Exception as e:
            logger.error(f"执行动作 {action_type} 失败: {str(e)}")
            return False

    def _execute_send_notification(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """发送通知"""
        message = parameters.get("message", "")
        recipient = parameters.get("recipient", "")
        notification_type = parameters.get("type", "info")
        
        logger.info(f"发送通知 [{notification_type}] 给 {recipient}: {message}")
        return True

    def _execute_update_system_config(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """更新系统配置"""
        config_key = parameters.get("config_key")
        config_value = parameters.get("config_value")
        
        logger.info(f"更新系统配置: {config_key} = {config_value}")
        return {config_key: config_value}

    def _execute_execute_script(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行脚本"""
        script_path = parameters.get("script_path")
        script_args = parameters.get("args", [])
        
        logger.info(f"执行脚本: {script_path} {json.dumps(script_args)}")
        return True

    def _execute_send_alert(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """发送警报"""
        alert_type = parameters.get("alert_type", "info")
        message = parameters.get("message", "")
        severity = parameters.get("severity", "medium")
        
        logger.info(f"发送警报 [{alert_type}][{severity}]: {message}")
        return True

    def _execute_grant_permission(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """授予权限"""
        user_id = parameters.get("user_id")
        permission = parameters.get("permission")
        
        logger.info(f"授予用户 {user_id} 权限: {permission}")
        return {"user_id": user_id, "permission": permission, "action": "granted"}

    def _execute_revoke_permission(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """撤销权限"""
        user_id = parameters.get("user_id")
        permission = parameters.get("permission")
        
        logger.info(f"撤销用户 {user_id} 权限: {permission}")
        return {"user_id": user_id, "permission": permission, "action": "revoked"}

    def _execute_log_event(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """记录事件"""
        event_type = parameters.get("event_type", "info")
        event_data = parameters.get("event_data", {})
        
        logger.info(f"记录事件 [{event_type}]: {json.dumps(event_data)}")
        return True

    def _execute_send_email(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """发送邮件"""
        to = parameters.get("to")
        subject = parameters.get("subject")
        body = parameters.get("body")
        cc = parameters.get("cc", [])
        
        logger.info(f"发送邮件给 {to} (抄送: {cc}): {subject}")
        return True

    def _execute_call_api(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """调用API"""
        url = parameters.get("url")
        method = parameters.get("method", "GET")
        headers = parameters.get("headers", {})
        body = parameters.get("body", {})
        
        logger.info(f"调用API {method} {url}")
        return {"url": url, "method": method, "status": "success"}

    def _execute_transform_data(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """转换数据"""
        source_field = parameters.get("source_field")
        target_field = parameters.get("target_field")
        transform_type = parameters.get("transform_type", "copy")
        
        value = context.get(source_field)
        
        if transform_type == "uppercase":
            result = str(value).upper() if value else value
        elif transform_type == "lowercase":
            result = str(value).lower() if value else value
        elif transform_type == "trim":
            result = str(value).strip() if value else value
        elif transform_type == "json":
            result = json.dumps(value) if value else None
        else:
            result = value
        
        logger.info(f"数据转换: {source_field} -> {target_field} ({transform_type})")
        return {target_field: result}

    def _execute_redirect(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """重定向"""
        target_url = parameters.get("target_url")
        status_code = parameters.get("status_code", 302)
        
        logger.info(f"重定向到: {target_url} (状态码: {status_code})")
        return {"redirect_to": target_url, "status_code": status_code}

    def _execute_set_variable(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """设置变量"""
        variable_name = parameters.get("variable_name")
        variable_value = parameters.get("variable_value")
        
        logger.info(f"设置变量: {variable_name} = {variable_value}")
        return {variable_name: variable_value}

    def _record_execution(self, rule_id: str, success: bool, error: str = None, 
                          start_time: float = None, execution_time: float = None):
        """记录规则执行历史"""
        record = {
            "rule_id": rule_id,
            "success": success,
            "error": error,
            "start_time": start_time,
            "execution_time": execution_time,
            "timestamp": time.time()
        }

        with self._lock:
            self._execution_history.append(record)
            while len(self._execution_history) > self._max_history:
                self._execution_history.pop(0)

    def register_action_executor(self, action_type: str, executor):
        """注册自定义动作执行器"""
        self._action_executors[action_type] = executor
        logger.info(f"注册动作执行器: {action_type}")

    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """获取规则执行历史"""
        with self._lock:
            return self._execution_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取规则引擎统计"""
        with self._lock:
            total_executions = len(self._execution_history)
            successful = sum(1 for r in self._execution_history if r["success"])
            failed = total_executions - successful
            
            return {
                "total_executions": total_executions,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": successful / total_executions if total_executions > 0 else 0
            }
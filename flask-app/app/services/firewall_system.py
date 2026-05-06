#!/usr/bin/env python3
"""
防火墙系统，用于保护系统安全
提供IP过滤、速率限制、URL过滤等功能

import time
import threading
# JSON import removed - using database
import re
import random
from typing import Dict, Any, List, Optional, Set
from app.utils.logging import logger

class FirewallSystem:
    防火墙系统主类，负责管理和执行防火墙规则

    def __init__(self):
        初始化防火墙系统
        self._rules = []  # 防火墙规则列表
        self._ip_whitelist = set()  # IP白名单
        self._ip_blacklist = set()  # IP黑名单
        self._rate_limits = {}  # 速率限制配置
        self._request_count = {}  # 请求计数，用于速率限制
        self._config = {
            "firewall_id": f"firewall_{int(time.time())}_{random.randint(1000, 9999)}",
            "firewall_name": "MTSCOS Firewall System",
            "enabled": True,
            "default_action": "allow",  # 默认动作：allow或block
            "log_enabled": True,  # 是否启用日志
            "rate_limit_enabled": True,  # 是否启用速率限制
            "ip_filter_enabled": True,  # 是否启用IP过滤
            "url_filter_enabled": True,  # 是否启用URL过滤
            "method_filter_enabled": True,  # 是否启用方法过滤
            "port_filter_enabled": True,  # 是否启用端口过滤
        }
        self._status = {
            "running": False,
            "initialized": False,
            "rule_count": 0,
            "whitelist_count": 0,
            "blacklist_count": 0,
            "blocked_requests": 0,
            "allowed_requests": 0
        }
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._event_handlers = {}

        logger.info("防火墙系统初始化完成")

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        初始化防火墙系统

        Args:
            config: 配置参数

        Returns:
        with self._lock:
            if self._status["initialized"]:
                logger.warning("防火墙系统已经初始化")
                return True

            try:
                logger.info("开始初始化防火墙系统...")

                # 更新配置
                if config:
                    self._config.update(config)

                # 加载默认规则
                self._load_default_rules()

                # 启动清理线程
                self._start_cleanup_thread()

                self._status["initialized"] = True
                self._status["running"] = True

                logger.info(f"防火墙系统初始化成功，防火墙ID: {self._config['firewall_id']}")
                return True
            except Exception as e:
                logger.error(f"防火墙系统初始化失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

    def _load_default_rules(self):
        加载默认规则
        # 默认允许所有请求
        default_rule = {
            "rule_id": "rule_default",
            "name": "默认规则",
            "description": "默认允许所有请求",
            "action": "allow",
            "priority": 100,
            "enabled": True,
            "conditions": [],
            "created_at": time.time(),
            "updated_at": time.time()
        }
        self._rules.append(default_rule)
        self._status["rule_count"] = len(self._rules)

        logger.info("默认防火墙规则加载完成")

        启动清理线程，定期清理过期的请求计数
        def cleanup_loop():
            while self._status["running"]:
                time.sleep(60)  # 每分钟清理一次
                self._cleanup_request_count()

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("防火墙清理线程启动成功")

    def _cleanup_request_count(self):
        清理过期的请求计数
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, counts in self._request_count.items():
                # 清理超过60秒的请求计数
                expired_entries = [t for t in counts if current_time - t > 60]
                for t in expired_entries:
                    counts.remove(t)

                # 如果该key下没有计数了，移除该key
                if not counts:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._request_count[key]

            logger.debug(f"清理了 {len(expired_keys)} 个过期的请求计数")

    def add_rule(self, rule: Dict[str, Any]) -> str:
        添加防火墙规则

        Args:
            rule: 规则信息

        Returns:
            str: 规则ID
        with self._lock:
            # 生成规则ID
            rule_id = rule.get("rule_id", f"rule_{int(time.time())}_{random.randint(1000, 9999)}")

            # 补充默认信息
            default_rule = {
                "rule_id": rule_id,
                "name": rule.get("name", f"Rule_{rule_id}"),
                "description": rule.get("description", ""),
                "action": rule.get("action", "allow"),
                "priority": rule.get("priority", 50),
                "enabled": rule.get("enabled", True),
                "conditions": rule.get("conditions", []),
                "created_at": time.time(),
                "updated_at": time.time()
            }

            # 添加规则
            self._rules.append(default_rule)
            # 按优先级排序
            self._rules.sort(key=lambda x: x["priority"])
            self._status["rule_count"] = len(self._rules)
            logger.info(f"防火墙规则添加成功: {rule_id} - {default_rule['name']}")
            self._notify_event("rule_added", {"rule_id": rule_id, "rule": default_rule})

            return rule_id

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        更新防火墙规则

            rule_id: 规则ID

        Returns:
            bool: 是否更新成功
        with self._lock:
                if rule["rule_id"] == rule_id:
                    # 更新规则
                    self._rules[i].update(updates)
                    # 重新排序
                    self._rules.sort(key=lambda x: x["priority"])

                    logger.info(f"防火墙规则更新成功: {rule_id}")
                    self._notify_event("rule_updated", {"rule_id": rule_id, "updates": updates})
                    return True

            logger.warning(f"防火墙规则不存在: {rule_id}")
            return False

    def delete_rule(self, rule_id: str) -> bool:
        删除防火墙规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        with self._lock:
            for i, rule in enumerate(self._rules):
                if rule["rule_id"] == rule_id:
                    # 删除规则
                    del self._rules[i]
                    self._status["rule_count"] = len(self._rules)

                    self._notify_event("rule_deleted", {"rule_id": rule_id})
                    return True

            logger.warning(f"防火墙规则不存在: {rule_id}")
            return False

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        获取防火墙规则

        Args:
            rule_id: 规则ID

        Returns:
            Optional[Dict[str, Any]]: 规则信息
            for rule in self._rules:
                if rule["rule_id"] == rule_id:
                    return rule.copy()
            return None

    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        Args:

        Returns:
            List[Dict[str, Any]]: 规则列表
        with self._lock:
            rules = self._rules.copy()

            # 应用过滤条件
            if filters:
                if "enabled" in filters:
                    rules = [r for r in rules if r["enabled"] == enabled]
                if "action" in filters:
                    action = filters["action"]
                    rules = [r for r in rules if r["action"] == action]
            return rules

    def add_to_whitelist(self, ip: str) -> bool:
        添加IP到白名单

        Args:
            ip: IP地址

        Returns:
        with self._lock:
            if ip not in self._ip_whitelist:
                self._ip_whitelist.add(ip)
                self._status["whitelist_count"] = len(self._ip_whitelist)

                logger.info(f"IP添加到白名单成功: {ip}")
                self._notify_event("ip_whitelisted", {"ip": ip})
                return True
            return False

    def remove_from_whitelist(self, ip: str) -> bool:
        从白名单移除IP

        Args:
            ip: IP地址

        Returns:
            bool: 是否移除成功
        with self._lock:
            if ip in self._ip_whitelist:
                self._ip_whitelist.remove(ip)
                self._status["whitelist_count"] = len(self._ip_whitelist)

                logger.info(f"IP从白名单移除成功: {ip}")
                self._notify_event("ip_removed_from_whitelist", {"ip": ip})
                return True
            return False

    def add_to_blacklist(self, ip: str) -> bool:
        添加IP到黑名单

        Args:
            ip: IP地址

        Returns:
            bool: 是否添加成功
        with self._lock:
            if ip not in self._ip_blacklist:
                self._ip_blacklist.add(ip)
                self._status["blacklist_count"] = len(self._ip_blacklist)

                logger.info(f"IP添加到黑名单成功: {ip}")
                self._notify_event("ip_blacklisted", {"ip": ip})
                return True
            return False

    def remove_from_blacklist(self, ip: str) -> bool:
        从黑名单移除IP

        Args:
            ip: IP地址

        Returns:
            bool: 是否移除成功
        with self._lock:
                self._ip_blacklist.remove(ip)
                self._status["blacklist_count"] = len(self._ip_blacklist)

                logger.info(f"IP从黑名单移除成功: {ip}")
                self._notify_event("ip_removed_from_blacklist", {"ip": ip})
                return True
            return False

        设置速率限制

        Args:
            key: 限制键（如IP地址、URL路径等）
            limit: 限制数量
            window: 时间窗口（秒）

        Returns:
            bool: 是否设置成功
        with self._lock:
                "limit": limit,
                "window": window
            }

            self._notify_event("rate_limit_set", {"key": key, "limit": limit, "window": window})
            return True

    def check_request(self, request_data: Dict[str, Any]) -> bool:
        检查请求是否允许通过

        Args:
            request_data: 请求数据，包含ip、port、method、url、headers等

        Returns:
            bool: 是否允许通过
        if not self._config["enabled"]:
            self._status["allowed_requests"] += 1
            return True
        ip = request_data.get("ip", "")
        port = request_data.get("port", 0)
        method = request_data.get("method", "GET")
        url = request_data.get("url", "")
        headers = request_data.get("headers", {})

        # 检查白名单
            self._status["allowed_requests"] += 1
            return True

        # 检查黑名单
        if ip in self._ip_blacklist:
            self._log_blocked_request(request_data, "IP在黑名单中")
            self._notify_event("request_blocked", {"request_data": request_data, "reason": "IP在黑名单中"})
            return False

        # 检查速率限制
        if self._config["rate_limit_enabled"]:
            if not self._check_rate_limit(ip):
                self._status["blocked_requests"] += 1
                self._log_blocked_request(request_data, "超出速率限制")
                self._notify_event("request_blocked", {"request_data": request_data, "reason": "超出速率限制"})
                return False

        # 检查防火墙规则
        for rule in self._rules:
            if rule["enabled"] and self._match_rule(rule, request_data):
                if rule["action"] == "allow":
                    self._status["allowed_requests"] += 1
                    return True
                else:
                    self._status["blocked_requests"] += 1
                    self._log_blocked_request(request_data, f"匹配规则: {rule['name']}")
                    self._notify_event("request_blocked", {"request_data": request_data, "reason": f"匹配规则: {rule['name']}"})
                    return False

        # 默认动作
        if self._config["default_action"] == "allow":
            self._status["allowed_requests"] += 1
            return True
        else:
            self._status["blocked_requests"] += 1
            self._log_blocked_request(request_data, "默认动作阻止")
            self._notify_event("request_blocked", {"request_data": request_data, "reason": "默认动作阻止"})
            return False

    def _check_rate_limit(self, key: str) -> bool:
        检查速率限制

        Args:
            key: 限制键

        Returns:
            bool: 是否允许通过
        if key not in self._rate_limits:
            return True

        limit_info = self._rate_limits[key]
        limit = limit_info["limit"]
        window = limit_info["window"]


        # 初始化请求计数
            self._request_count[key] = []

        # 添加当前请求时间

        # 清理过期的请求计数
        self._request_count[key] = [t for t in self._request_count[key] if current_time - t <= window]

        # 检查是否超出限制
        return len(self._request_count[key]) <= limit
    def _match_rule(self, rule: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        检查请求是否匹配规则

        Args:
            request_data: 请求数据

        Returns:
            bool: 是否匹配
        conditions = rule.get("conditions", [])
        if not conditions:
            return True
        for condition in conditions:
            field = condition.get("field", "")
            operator = condition.get("operator", "")
            value = condition.get("value", "")
            if field == "ip":
                if not self._match_ip(request_data.get("ip", ""), operator, value):
                    return False
            elif field == "port":
                    return False
            elif field == "method":
                if not self._match_method(request_data.get("method", "GET"), operator, value):
                    return False
            elif field == "url":
                    return False
                if not self._match_header(request_data.get("headers", {}), header_name, operator, value):
                    return False

        return True

    def _match_ip(self, ip: str, operator: str, value: str) -> bool:
        匹配IP条件
        Args:
            ip: IP地址
            operator: 操作符，如eq、ne、contains、regex等
            value: 比较值

        Returns:
            bool: 是否匹配
        if operator == "eq":
            return ip == value
        elif operator == "ne":
            return ip != value
        elif operator == "contains":
            return value in ip
        elif operator == "regex":
            return bool(re.match(value, ip))
        elif operator == "cidr":
            return self._is_ip_in_cidr(ip, value)
        return False

    def _is_ip_in_cidr(self, ip: str, cidr: str) -> bool:
        检查IP是否在CIDR范围内

        Args:
            ip: IP地址
            cidr: CIDR格式的IP范围

        Returns:
            bool: 是否在范围内
        try:
            from ipaddress import ip_address, ip_network
            return ip_address(ip) in ip_network(cidr)
        except Exception as e:
            logger.error(f"CIDR检查失败: {str(e)}")
            return False

    def _match_port(self, port: int, operator: str, value: str) -> bool:
        匹配端口条件

        Args:
            port: 端口
            operator: 操作符，如eq、ne、gt、lt、in等
            value: 比较值

        Returns:
            bool: 是否匹配
        try:
            if operator == "eq":
                return port == int(value)
            elif operator == "ne":
                return port != int(value)
            elif operator == "gt":
                return port > int(value)
            elif operator == "lt":
                return port < int(value)
            elif operator == "in":
                ports = [int(p) for p in value.split(",")]
                return port in ports
        except Exception as e:
        return False

    def _match_method(self, method: str, operator: str, value: str) -> bool:
        匹配方法条件

        Args:
            method: 请求方法
            operator: 操作符，如eq、ne、in等
            value: 比较值

        Returns:
            bool: 是否匹配
        if operator == "eq":
            return method.upper() == value.upper()
        elif operator == "ne":
            return method.upper() != value.upper()
        elif operator == "in":
            methods = [m.upper() for m in value.split(",")]
            return method.upper() in methods
        return False

    def _match_url(self, url: str, operator: str, value: str) -> bool:
        Args:
            url: URL路径
            operator: 操作符，如eq、ne、contains、regex等
            value: 比较值

        Returns:
            bool: 是否匹配
        if operator == "eq":
            return url == value
        elif operator == "ne":
            return url != value
        elif operator == "contains":
            return value in url
        elif operator == "regex":
            return bool(re.match(value, url))
        elif operator == "startswith":
            return url.startswith(value)
        elif operator == "endswith":
            return url.endswith(value)
        return False

    def _match_header(self, headers: Dict[str, str], header_name: str, operator: str, value: str) -> bool:
        匹配头信息条件

        Args:
            headers: 请求头
            header_name: 头名称
            operator: 操作符，如eq、ne、contains等
            value: 比较值

        Returns:
            bool: 是否匹配
        header_value = headers.get(header_name, "")
        if operator == "eq":
            return header_value == value
        elif operator == "ne":
            return header_value != value
        elif operator == "contains":
            return value in header_value

        记录被阻止的请求

        Args:
            request_data: 请求数据
            reason: 阻止原因
            logger.warning(f"请求被阻止: IP={request_data.get('ip', '')}, Method={request_data.get('method', '')}, URL={request_data.get('url', '')}, 原因: {reason}")

    def get_status(self) -> Dict[str, Any]:
        获取防火墙系统状态

        Returns:
            Dict[str, Any]: 系统状态信息
        with self._lock:
            return {
                "config": self._config.copy(),
                "status": self._status.copy(),
                "rule_count": len(self._rules),
                "whitelist_count": len(self._ip_whitelist),
                "blacklist_count": len(self._ip_blacklist),
                "rules": [rule["rule_id"] for rule in self._rules],
                "ip_whitelist": list(self._ip_whitelist),
                "ip_blacklist": list(self._ip_blacklist),
                "rate_limits": self._rate_limits.copy()
            }


        Args:
            event_type: 事件类型
            handler: 事件处理函数
        with self._lock:
            if event_type not in self._event_handlers:
            self._event_handlers[event_type].append(handler)

    def _notify_event(self, event_type: str, event_data: Dict[str, Any]):
        通知事件

            event_type: 事件类型
            event_data: 事件数据
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": time.time(),

            handlers = self._event_handlers.get(event_type, [])

        # 调用事件处理器
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:

    def shutdown(self) -> bool:
        关闭防火墙系统

        Returns:
            bool: 是否关闭成功
        with self._lock:
            if not self._status["running"]:
                return True

            try:
                logger.info("开始关闭防火墙系统...")

                # 停止清理线程
                self._status["running"] = False
                # 清理资源
                self._rules.clear()
                self._ip_blacklist.clear()
                self._rate_limits.clear()
                self._request_count.clear()
                self._status["rule_count"] = 0
                self._status["whitelist_count"] = 0
                self._status["blacklist_count"] = 0

                logger.info("防火墙系统关闭成功")
                return True
                logger.error(f"防火墙系统关闭失败: {str(e)}")
                return False
# 初始化防火墙系统实例
firewall_system = FirewallSystem()

"""
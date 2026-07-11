# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
防火墙系统 - 保护系统安全
提供IP过滤、速率限制、URL过滤、端口过滤、方法过滤、请求头检查等功能
支持数据库持久化规则、事件通知、自动清理等高级特性
"""

import time
import threading
import re
import random
import sqlite3
import os
import json
from typing import Dict, Any, List, Optional, Set
from app.utils.logging import logger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'app.db')


class FirewallSystem:
    """防火墙系统主类，负责管理和执行防火墙规则"""

    def __init__(self):
        """初始化防火墙系统"""
        self._rules: List[Dict[str, Any]] = []
        self._ip_whitelist: Set[str] = set()
        self._ip_blacklist: Set[str] = set()
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        self._request_count: Dict[str, List[float]] = {}
        self._config: Dict[str, Any] = {
            "firewall_id": f"firewall_{int(time.time())}_{random.randint(1000, 9999)}",
            "firewall_name": "MTSCOS Firewall System",
            "enabled": True,
            "default_action": "allow",
            "log_enabled": True,
            "rate_limit_enabled": True,
            "ip_filter_enabled": True,
            "url_filter_enabled": True,
            "method_filter_enabled": True,
            "port_filter_enabled": True,
            "geo_filter_enabled": False,
            "ddos_protection_enabled": True,
        }
        self._status: Dict[str, Any] = {
            "running": False,
            "initialized": False,
            "rule_count": 0,
            "whitelist_count": 0,
            "blacklist_count": 0,
            "blocked_requests": 0,
            "allowed_requests": 0,
        }
        self._lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._event_handlers: Dict[str, List] = {}

        self._init_database()
        self.initialize()
        logger.info("防火墙系统初始化完成")

    def _init_database(self):
        """初始化防火墙数据库表"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS firewall_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                action TEXT DEFAULT 'allow',
                priority INTEGER DEFAULT 50,
                enabled INTEGER DEFAULT 1,
                conditions TEXT,
                hit_count INTEGER DEFAULT 0,
                created_at REAL,
                updated_at REAL
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS firewall_ip_list (
                id TEXT PRIMARY KEY,
                ip_address TEXT NOT NULL,
                list_type TEXT NOT NULL,
                reason TEXT,
                created_at REAL
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS firewall_logs (
                log_id TEXT PRIMARY KEY,
                ip TEXT,
                method TEXT,
                url TEXT,
                reason TEXT,
                action TEXT,
                timestamp REAL
            )''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"防火墙数据库初始化失败: {e}")

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化防火墙系统"""
        with self._lock:
            if self._status["initialized"]:
                logger.warning("防火墙系统已经初始化")
                return True

            try:
                logger.info("开始初始化防火墙系统...")

                if config:
                    self._config.update(config)

                self._load_default_rules()
                self._load_persisted_rules()
                self._load_ip_lists()
                self._start_cleanup_thread()

                self._status["initialized"] = True
                self._status["running"] = True

                logger.info(f"防火墙系统初始化成功，防火墙ID: {self._config['firewall_id']}")
                return True
            except Exception as e:
                logger.error(f"防火墙系统初始化失败: {e}")
                return False

    def _load_default_rules(self):
        """加载默认规则"""
        default_rules = [
            {
                "rule_id": "rule_default_allow",
                "name": "默认放行规则",
                "description": "默认允许所有请求通过",
                "action": "allow",
                "priority": 100,
                "enabled": True,
                "conditions": [],
            },
            {
                "rule_id": "rule_allow_auth_login",
                "name": "允许登录接口",
                "description": "允许登录接口访问",
                "action": "allow",
                "priority": 5,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "eq", "value": "/auth/login"},
                ],
            },
            {
                "rule_id": "rule_allow_auth_register",
                "name": "允许注册接口",
                "description": "允许注册接口访问",
                "action": "allow",
                "priority": 5,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "eq", "value": "/auth/register"},
                ],
            },
            {
                "rule_id": "rule_allow_api_auth_login",
                "name": "允许API登录接口",
                "description": "允许API登录接口访问",
                "action": "allow",
                "priority": 5,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "eq", "value": "/api/auth/login"},
                ],
            },
            {
                "rule_id": "rule_allow_api_auth_register",
                "name": "允许API注册接口",
                "description": "允许API注册接口访问",
                "action": "allow",
                "priority": 5,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "eq", "value": "/api/auth/register"},
                ],
            },
            {
                "rule_id": "rule_block_sql_injection",
                "name": "SQL注入防护",
                "description": "阻止疑似SQL注入攻击的请求",
                "action": "block",
                "priority": 10,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "regex", "value": ".*('|\"|\\s)(\\s)*(union|select|insert|delete|drop|update)(\\s+).*", "options": "i"},
                ],
            },
            {
                "rule_id": "rule_block_xss",
                "name": "XSS防护",
                "description": "阻止跨站脚本攻击",
                "action": "block",
                "priority": 10,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "regex", "value": ".*<(script|iframe|object|embed).*", "options": "i"},
                ],
            },
            {
                "rule_id": "rule_block_path_traversal",
                "name": "路径遍历防护",
                "description": "阻止路径遍历攻击",
                "action": "block",
                "priority": 10,
                "enabled": True,
                "conditions": [
                    {"field": "url", "operator": "regex", "value": ".*(\\.\\./|\\.\\./).*"},
                ],
            },
        ]

        for rule in default_rules:
            rule["created_at"] = time.time()
            rule["updated_at"] = time.time()
            self._rules.append(rule)

        self._rules.sort(key=lambda x: x["priority"])
        self._status["rule_count"] = len(self._rules)
        logger.info(f"默认防火墙规则加载完成，共 {len(self._rules)} 条规则")

    def _load_persisted_rules(self):
        """从数据库加载持久化规则"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT rule_id, name, description, action, priority, enabled, conditions FROM firewall_rules")
            rows = cursor.fetchall()
            for row in rows:
                rule_id, name, desc, action, priority, enabled, conditions = row
                if not any(r["rule_id"] == rule_id for r in self._rules):
                    self._rules.append({
                        "rule_id": rule_id,
                        "name": name,
                        "description": desc or "",
                        "action": action,
                        "priority": priority,
                        "enabled": bool(enabled),
                        "conditions": json.loads(conditions) if conditions else [],
                        "created_at": time.time(),
                        "updated_at": time.time(),
                    })
            self._rules.sort(key=lambda x: x["priority"])
            self._status["rule_count"] = len(self._rules)
            conn.close()
        except Exception as e:
            logger.error(f"加载持久化规则失败: {e}")

    def _load_ip_lists(self):
        """从数据库加载IP白名单和黑名单"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT ip_address, list_type FROM firewall_ip_list")
            rows = cursor.fetchall()
            for ip, list_type in rows:
                if list_type == "whitelist":
                    self._ip_whitelist.add(ip)
                elif list_type == "blacklist":
                    self._ip_blacklist.add(ip)
            self._status["whitelist_count"] = len(self._ip_whitelist)
            self._status["blacklist_count"] = len(self._ip_blacklist)
            conn.close()
        except Exception as e:
            logger.error(f"加载IP列表失败: {e}")

    def _start_cleanup_thread(self):
        """启动清理线程，定期清理过期的请求计数"""
        def cleanup_loop():
            while self._status["running"]:
                time.sleep(60)
                self._cleanup_request_count()

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("防火墙清理线程启动成功")

    def _cleanup_request_count(self):
        """清理过期的请求计数"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, counts in self._request_count.items():
                self._request_count[key] = [t for t in counts if current_time - t <= 60]
                if not self._request_count[key]:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._request_count[key]

    def add_rule(self, rule: Dict[str, Any]) -> str:
        """添加防火墙规则"""
        with self._lock:
            rule_id = rule.get("rule_id", f"rule_{int(time.time())}_{random.randint(1000, 9999)}")

            new_rule = {
                "rule_id": rule_id,
                "name": rule.get("name", f"Rule_{rule_id}"),
                "description": rule.get("description", ""),
                "action": rule.get("action", "allow"),
                "priority": rule.get("priority", 50),
                "enabled": rule.get("enabled", True),
                "conditions": rule.get("conditions", []),
                "created_at": time.time(),
                "updated_at": time.time(),
            }

            self._rules.append(new_rule)
            self._rules.sort(key=lambda x: x["priority"])
            self._status["rule_count"] = len(self._rules)

            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''INSERT OR REPLACE INTO firewall_rules
                    (rule_id, name, description, action, priority, enabled, conditions, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (rule_id, new_rule["name"], new_rule["description"],
                     new_rule["action"], new_rule["priority"],
                     1 if new_rule["enabled"] else 0,
                     json.dumps(new_rule["conditions"]),
                     new_rule["created_at"], new_rule["updated_at"]))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"规则持久化失败: {e}")

            logger.info(f"防火墙规则添加成功: {rule_id} - {new_rule['name']}")
            self._notify_event("rule_added", {"rule_id": rule_id, "rule": new_rule})
            return rule_id

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新防火墙规则"""
        with self._lock:
            for i, rule in enumerate(self._rules):
                if rule["rule_id"] == rule_id:
                    self._rules[i].update(updates)
                    self._rules[i]["updated_at"] = time.time()
                    self._rules.sort(key=lambda x: x["priority"])

                    try:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute('''UPDATE firewall_rules
                            SET name=?, description=?, action=?, priority=?, enabled=?, conditions=?, updated_at=?
                            WHERE rule_id=?''',
                            (self._rules[i].get("name", ""), self._rules[i].get("description", ""),
                             self._rules[i].get("action", "allow"), self._rules[i].get("priority", 50),
                             1 if self._rules[i].get("enabled", True) else 0,
                             json.dumps(self._rules[i].get("conditions", [])),
                             time.time(), rule_id))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"规则更新持久化失败: {e}")

                    logger.info(f"防火墙规则更新成功: {rule_id}")
                    self._notify_event("rule_updated", {"rule_id": rule_id, "updates": updates})
                    return True

            logger.warning(f"防火墙规则不存在: {rule_id}")
            return False

    def delete_rule(self, rule_id: str) -> bool:
        """删除防火墙规则"""
        with self._lock:
            for i, rule in enumerate(self._rules):
                if rule["rule_id"] == rule_id:
                    del self._rules[i]
                    self._status["rule_count"] = len(self._rules)

                    try:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM firewall_rules WHERE rule_id=?", (rule_id,))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"规则删除持久化失败: {e}")

                    self._notify_event("rule_deleted", {"rule_id": rule_id})
                    return True

            logger.warning(f"防火墙规则不存在: {rule_id}")
            return False

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """获取防火墙规则"""
        with self._lock:
            for rule in self._rules:
                if rule["rule_id"] == rule_id:
                    return rule.copy()
            return None

    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出防火墙规则"""
        with self._lock:
            rules = [r.copy() for r in self._rules]

            if filters:
                if "enabled" in filters:
                    rules = [r for r in rules if r["enabled"] == filters["enabled"]]
                if "action" in filters:
                    rules = [r for r in rules if r["action"] == filters["action"]]

            return rules

    def add_to_whitelist(self, ip: str, reason: str = "") -> bool:
        """添加IP到白名单"""
        with self._lock:
            if ip not in self._ip_whitelist:
                self._ip_whitelist.add(ip)
                self._status["whitelist_count"] = len(self._ip_whitelist)

                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''INSERT OR REPLACE INTO firewall_ip_list
                        (id, ip_address, list_type, reason, created_at) VALUES (?, ?, ?, ?, ?)''',
                        (f"wl_{ip}", ip, "whitelist", reason, time.time()))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"白名单持久化失败: {e}")

                logger.info(f"IP添加到白名单成功: {ip}")
                self._notify_event("ip_whitelisted", {"ip": ip})
                return True
            return False

    def remove_from_whitelist(self, ip: str) -> bool:
        """从白名单移除IP"""
        with self._lock:
            if ip in self._ip_whitelist:
                self._ip_whitelist.remove(ip)
                self._status["whitelist_count"] = len(self._ip_whitelist)

                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM firewall_ip_list WHERE ip_address=? AND list_type=?", (ip, "whitelist"))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"白名单删除持久化失败: {e}")

                logger.info(f"IP从白名单移除成功: {ip}")
                self._notify_event("ip_removed_from_whitelist", {"ip": ip})
                return True
            return False

    def add_to_blacklist(self, ip: str, reason: str = "") -> bool:
        """添加IP到黑名单"""
        with self._lock:
            if ip not in self._ip_blacklist:
                self._ip_blacklist.add(ip)
                self._status["blacklist_count"] = len(self._ip_blacklist)

                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''INSERT OR REPLACE INTO firewall_ip_list
                        (id, ip_address, list_type, reason, created_at) VALUES (?, ?, ?, ?, ?)''',
                        (f"bl_{ip}", ip, "blacklist", reason, time.time()))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"黑名单持久化失败: {e}")

                logger.info(f"IP添加到黑名单成功: {ip}")
                self._notify_event("ip_blacklisted", {"ip": ip})
                return True
            return False

    def remove_from_blacklist(self, ip: str) -> bool:
        """从黑名单移除IP"""
        with self._lock:
            if ip in self._ip_blacklist:
                self._ip_blacklist.remove(ip)
                self._status["blacklist_count"] = len(self._ip_blacklist)

                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM firewall_ip_list WHERE ip_address=? AND list_type=?", (ip, "blacklist"))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"黑名单删除持久化失败: {e}")

                logger.info(f"IP从黑名单移除成功: {ip}")
                self._notify_event("ip_removed_from_blacklist", {"ip": ip})
                return True
            return False

    def set_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """设置速率限制"""
        with self._lock:
            self._rate_limits[key] = {"limit": limit, "window": window}
            self._notify_event("rate_limit_set", {"key": key, "limit": limit, "window": window})
            return True

    def check_request(self, request_data: Dict[str, Any]) -> bool:
        """检查请求是否允许通过"""
        if not self._config["enabled"]:
            with self._lock:
                self._status["allowed_requests"] += 1
            return True

        ip = request_data.get("ip", "")
        port = request_data.get("port", 0)
        method = request_data.get("method", "GET")
        url = request_data.get("url", "")
        headers = request_data.get("headers", {})

        # 检查白名单
        if ip in self._ip_whitelist:
            with self._lock:
                self._status["allowed_requests"] += 1
            return True

        # 检查黑名单
        if ip in self._ip_blacklist:
            with self._lock:
                self._status["blocked_requests"] += 1
            self._log_blocked_request(request_data, "IP在黑名单中")
            self._notify_event("request_blocked", {"request_data": request_data, "reason": "IP在黑名单中"})
            return False

        # 检查速率限制
        if self._config["rate_limit_enabled"]:
            if not self._check_rate_limit(ip):
                with self._lock:
                    self._status["blocked_requests"] += 1
                self._log_blocked_request(request_data, "超出速率限制")
                self._notify_event("request_blocked", {"request_data": request_data, "reason": "超出速率限制"})
                return False

        # 检查防火墙规则
        for rule in self._rules:
            if rule["enabled"] and self._match_rule(rule, request_data):
                if rule["action"] == "allow":
                    with self._lock:
                        self._status["allowed_requests"] += 1
                    return True
                else:
                    with self._lock:
                        self._status["blocked_requests"] += 1
                    self._log_blocked_request(request_data, f"匹配规则: {rule['name']}")
                    self._notify_event("request_blocked", {"request_data": request_data, "reason": f"匹配规则: {rule['name']}"})
                    return False

        # 默认动作
        if self._config["default_action"] == "allow":
            with self._lock:
                self._status["allowed_requests"] += 1
            return True
        else:
            with self._lock:
                self._status["blocked_requests"] += 1
            self._log_blocked_request(request_data, "默认动作阻止")
            return False

    def _check_rate_limit(self, key: str) -> bool:
        """检查速率限制"""
        if key not in self._rate_limits:
            return True

        limit_info = self._rate_limits[key]
        limit = limit_info["limit"]
        window = limit_info["window"]
        current_time = time.time()

        if key not in self._request_count:
            self._request_count[key] = []

        self._request_count[key].append(current_time)
        self._request_count[key] = [t for t in self._request_count[key] if current_time - t <= window]

        return len(self._request_count[key]) <= limit

    def _match_rule(self, rule: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """检查请求是否匹配规则"""
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
                if not self._match_port(request_data.get("port", 0), operator, value):
                    return False
            elif field == "method":
                if not self._match_method(request_data.get("method", "GET"), operator, value):
                    return False
            elif field == "url":
                if not self._match_url(request_data.get("url", ""), operator, value):
                    return False
            elif field == "header":
                header_name = condition.get("header_name", "")
                if not self._match_header(request_data.get("headers", {}), header_name, operator, value):
                    return False

        return True

    def _match_ip(self, ip: str, operator: str, value: str) -> bool:
        """匹配IP条件"""
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
        """检查IP是否在CIDR范围内"""
        try:
            from ipaddress import ip_address, ip_network
            return ip_address(ip) in ip_network(cidr)
        except Exception as e:
            logger.error(f"CIDR检查失败: {e}")
            return False

    def _match_port(self, port: int, operator: str, value: str) -> bool:
        """匹配端口条件"""
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
        except (ValueError, TypeError):
            pass
        return False

    def _match_method(self, method: str, operator: str, value: str) -> bool:
        """匹配方法条件"""
        if operator == "eq":
            return method.upper() == value.upper()
        elif operator == "ne":
            return method.upper() != value.upper()
        elif operator == "in":
            methods = [m.upper() for m in value.split(",")]
            return method.upper() in methods
        return False

    def _match_url(self, url: str, operator: str, value: str) -> bool:
        """匹配URL条件"""
        if operator == "eq":
            return url == value
        elif operator == "ne":
            return url != value
        elif operator == "contains":
            return value in url
        elif operator == "regex":
            return bool(re.match(value, url, re.IGNORECASE))
        elif operator == "startswith":
            return url.startswith(value)
        elif operator == "endswith":
            return url.endswith(value)
        return False

    def _match_header(self, headers: Dict[str, str], header_name: str, operator: str, value: str) -> bool:
        """匹配请求头条件"""
        header_value = headers.get(header_name, "")
        if operator == "eq":
            return header_value == value
        elif operator == "ne":
            return header_value != value
        elif operator == "contains":
            return value in header_value
        return False

    def _log_blocked_request(self, request_data: Dict[str, Any], reason: str):
        """记录被阻止的请求"""
        logger.warning(
            f"请求被阻止: IP={request_data.get('ip', '')}, "
            f"Method={request_data.get('method', '')}, "
            f"URL={request_data.get('url', '')}, 原因: {reason}"
        )

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            log_id = f"log_{int(time.time())}_{random.randint(1000, 9999)}"
            cursor.execute('''INSERT INTO firewall_logs
                (log_id, ip, method, url, reason, action, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (log_id, request_data.get("ip", ""), request_data.get("method", ""),
                 request_data.get("url", ""), reason, "blocked", time.time()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"防火墙日志记录失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取防火墙系统状态"""
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
                "rate_limits": self._rate_limits.copy(),
            }

    def get_statistics(self) -> Dict[str, Any]:
        """获取防火墙统计信息"""
        with self._lock:
            return {
                "total_rules": len(self._rules),
                "active_rules": len([r for r in self._rules if r["enabled"]]),
                "blocked_requests": self._status["blocked_requests"],
                "allowed_requests": self._status["allowed_requests"],
                "whitelist_count": len(self._ip_whitelist),
                "blacklist_count": len(self._ip_blacklist),
                "rate_limit_configs": len(self._rate_limits),
            }

    def get_blocked_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取阻止日志"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''SELECT log_id, ip, method, url, reason, action, timestamp
                FROM firewall_logs ORDER BY timestamp DESC LIMIT ?''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [{"log_id": r[0], "ip": r[1], "method": r[2], "url": r[3],
                     "reason": r[4], "action": r[5], "timestamp": r[6]} for r in rows]
        except Exception as e:
            logger.error(f"获取阻止日志失败: {e}")
            return []

    def register_event_handler(self, event_type: str, handler):
        """注册事件处理器"""
        with self._lock:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)

    def _notify_event(self, event_type: str, event_data: Dict[str, Any]):
        """通知事件"""
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": time.time(),
        }

        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")

    def shutdown(self) -> bool:
        """关闭防火墙系统"""
        with self._lock:
            if not self._status["running"]:
                return True

            try:
                logger.info("开始关闭防火墙系统...")
                self._status["running"] = False

                self._rules.clear()
                self._ip_blacklist.clear()
                self._rate_limits.clear()
                self._request_count.clear()
                self._status["rule_count"] = 0
                self._status["whitelist_count"] = 0
                self._status["blacklist_count"] = 0

                logger.info("防火墙系统关闭成功")
                return True
            except Exception as e:
                logger.error(f"防火墙系统关闭失败: {e}")
                return False


# 初始化防火墙系统实例
firewall_system = FirewallSystem()

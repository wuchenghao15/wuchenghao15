# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""服务器规则管理器模块"""

import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class ServerRuleManager:
    """服务器规则管理器类"""

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载规则配置"""
        return {
            "server_registration": {
                "allowed_ips": [],
                "denied_ips": [],
                "required_metadata": ["server_name", "host", "port"]
            },
            "server_health": {
                "health_check_interval": 30,
                "max_failed_checks": 3,
                "timeout": 5,
                "min_response_time": 0,
                "max_response_time": 5000,
                "min_uptime": 60
            },
            "resource_usage": {
                "max_cpu_usage": 90,
                "max_memory_usage": 90,
                "max_disk_usage": 95,
                "max_network_traffic": 90,
                "min_free_memory": 512,
                "min_free_disk": 5120
            },
            "load_balancing": {
                "strategy": "round_robin"
            }
        }

    def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """获取规则"""
        return self.rules.get(rule_name)

    def update_rule(self, rule_name: str, rule_data: Dict[str, Any]):
        """更新规则"""
        if rule_name in self.rules:
            self.rules[rule_name].update(rule_data)
            logger.info(f"规则 {rule_name} 已更新")

    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有规则"""
        return self.rules

    def initialize(self):
        """初始化规则管理器"""
        logger.info("规则管理器初始化完成")

server_rule_manager = ServerRuleManager()
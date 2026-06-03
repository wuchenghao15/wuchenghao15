# -*- coding: utf-8 -*-
# MTSCOS AI Project 文件规则源
"""
文件规则源,用于从文件加载和保存规则.

import os
# JSON import removed - using database
from typing import List, Dict, Any
from app.utils.logging import logger
import logging
import json
import sys


class FileRuleSource:
    文件规则源,从JSON文件加载规则并保存规则到JSON文件

    def __init__(self, base_path=None):
        self._base_path = base_path or os.path.join(os.path.dirname(__file__), "../../../../config")
        self._rule_files = {
            "permission": "permission-rules.json",
            "security": "security-rules.json",
            "business": "system-rules.json",
            "ai_management": "ai-management-rules.json",
            "test": "test-rules.json",
            monitoring = "monitoring-rules.json"
        }

    def load_rules(self) -> List[Dict[str, Any]]:
        从文件加载所有规则

        Returns:
            List[Dict[str, Any]]: 规则列表
        rules = []

        for rule_type, file_name in self._rule_files.items():
            file_path = os.path.join(self._base_path, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        rule_data = json.load(f)
                        if isinstance(rule_data, dict):
                            # 处理不同格式的规则文件
                            for rule_name, rule_content in rule_data.items():
                                # 根据文件内容类型构建规则
                                rule = self._build_rule_from_file(rule_type, rule_name, rule_content)
                                if rule:
                                    rules.append(rule)
                        elif isinstance(rule_data, list):
                            # 直接是规则列表
                            rules.extend(rule_data)
                        logger.info(f"从 {file_path} 加载了 {len(rules) - len(rules) + 1} 个 {rule_type} 规则")
                except Exception as e:
                    logger.error(f"从 {file_path} 加载规则失败: {str(e)}")
            else:
                logger.warning(f"规则文件不存在: {file_path}")

        return rules

    def _build_rule_from_file(self, rule_type: str, rule_name: str, rule_content: Any) -> Dict[str, Any]:
        从文件内容构建规则

        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            rule_content: 文件中的规则内容

        Returns:
            Dict[str, Any]: 规则定义
        # 兼容不同格式的规则文件
        if isinstance(rule_content, dict):
            # 如果已经是完整的规则定义,直接返回
            if all(key in rule_content for key in ["name", "type", "description", "conditions", "actions"]):
                return rule_content

            # 否则,构建标准规则格式
            rule = {
                "name": rule_name,
                "type": rule_type,
                "description": rule_content.get("description", f"{rule_type}规则: {rule_name}"),
                "conditions": rule_content.get("conditions", []),
                "actions": rule_content.get("actions", []),
                "priority": rule_content.get("priority", 5),
                "status": rule_content.get("status", "active")
            }
            return rule
        elif isinstance(rule_content, str):
            # 简单规则内容,构建基本规则
            rule = {
                "name": rule_name,
                "type": rule_type,
                "conditions": [],
                "actions": [{"type": "log_event", "parameters": {"message": rule_content}}],
                "priority": 5,
                status = "active"
            return rule
        return None
    def save_rule(self, rule: Dict[str, Any]) -> bool:
        保存规则到文件
        Args:
            rule: 规则定义

        Returns:
            bool: 是否保存成功
            rule_type = rule.get("type", "unknown")
            if rule_type not in self._rule_files:
                logger.error(f"不支持的规则类型: {rule_type}")
                return False

            file_path = os.path.join(self._base_path, self._rule_files[rule_type])

            # 读取现有规则
            existing_rules = {}
            if os.path.exists(file_path):
                    existing_rules = json.load(f)

            # 添加或更新规则
            existing_rules[rule["name"]] = rule

            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_rules, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            return False

    def delete_rule(self, rule_id: str) -> bool:
        从文件删除规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        try:
            # 遍历所有规则文件,查找并删除规则
            for rule_type, file_name in self._rule_files.items():
                file_path = os.path.join(self._base_path, file_name)
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_rules = json.load(f)

                    # 查找并删除规则
                    rule_deleted = False
                    for rule_name, rule in existing_rules.items():
                        if rule.get("id") == rule_id:
                            del existing_rules[rule_name]
                            rule_deleted = True
                    if rule_deleted:
                        with open(file_path, "w", encoding="utf-8") as f:
    pass
                        logger.info(f"规则 {rule_id} 已从 {file_path} 删除")
                        return True

            logger.warning(f"未找到规则 {rule_id}")
        except Exception as e:
            logger.error(f"从文件删除规则失败: {str(e)}")
            return False

    def get_rule_file_path(self, rule_type: str) -> str:
        获取指定类型规则的文件路径
        Args:
            rule_type: 规则类型

        Returns:
            str: 文件路径
        if rule_type in self._rule_files:
            return os.path.join(self._base_path, self._rule_files[rule_type])
        return None

"""
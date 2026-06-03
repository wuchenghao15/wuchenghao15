# -*- coding: utf-8 -*-
# MTSCOS AI Project 数据库规则源
"""
数据库规则源,用于从数据库加载和保存规则.

from typing import List, Dict, Any
from app.utils.logging import logger


class DatabaseRuleSource:
    数据库规则源,从数据库加载规则并保存规则到数据库

    def __init__(self):
        self._table_name = "rules"

    def load_rules(self) -> List[Dict[str, Any]]:
        从数据库加载所有规则

        Returns:
            List[Dict[str, Any]]: 规则列表
        rules = []

        try:
            # 延迟导入,避免循环依赖
            from app.utils.db import db_manager

            # 查询所有规则
            query = f"SELECT * FROM {self._table_name}"
            rows = db_manager.fetch_all(query)

            for row in rows:
                # 转换为规则定义格式
                rule = self._row_to_rule(row)
                rules.append(rule)

            logger.info(f"从数据库加载了 {len(rules)} 个规则")
        except Exception as e:
            logger.error(f"从数据库加载规则失败: {str(e)}")

        return rules

    def save_rule(self, rule: Dict[str, Any]) -> bool:
        保存规则到数据库

        Args:
            rule: 规则定义

        Returns:
            bool: 是否保存成功
        try:
            # 延迟导入,避免循环依赖
            from app.utils.db import db_manager

            existing_rule = self._get_rule_by_id(rule.get("id"))

            if existing_rule:
                # 更新现有规则
                update_data = {
                    "rule_name": rule.get("name"),
                    "rule_type": rule.get("type"),
                    "description": rule.get("description"),
                    "rule_content": self._rule_to_content(rule),
                    "priority": rule.get("priority", 5),
                    "enabled": 1 if rule.get("status") == "active" else 0,
                    "version": existing_rule.get("version", 1) + 1
                }

                success = db_manager.update(
                    table=self._table_name,
                    data=update_data,
                    where_clause="id = ?",
                    where_params=(rule.get("id"),)
                )
            else:
                # 插入新规则
                insert_data = {
                    "id": rule.get("id"),
                    "rule_type": rule.get("type"),
                    "rule_name": rule.get("name"),
                    "rule_content": self._rule_to_content(rule),
                    "description": rule.get("description"),
                    "priority": rule.get("priority", 5),
                    "enabled": 1 if rule.get("status") == "active" else 0,
                    version = 1
                }
                    table=self._table_name,
                    data=insert_data
            if success:
                logger.info(f"规则 {rule.get('name')} 已保存到数据库")
                logger.error(f"保存规则 {rule.get('name')} 到数据库失败")
            return success
        except Exception as e:
            logger.error(f"保存规则到数据库失败: {str(e)}")
            return False

        从数据库删除规则

        Args:
            rule_id: 规则ID

        Returns:
    pass
        try:
            # 延迟导入,避免循环依赖
            from app.utils.db import db_manager

            success = db_manager.delete(
                table=self._table_name,
                where_params=(rule_id,)
            )

            if success:
                logger.info(f"规则 {rule_id} 已从数据库删除")
            else:
                logger.error(f"从数据库删除规则 {rule_id} 失败")

            return success
        except Exception as e:
            logger.error(f"从数据库删除规则失败: {str(e)}")
            return False

    def _row_to_rule(self, row) -> Dict[str, Any]:
        将数据库行转换为规则定义
        Args:
            row: 数据库行
        Returns:
            Dict[str, Any]: 规则定义
rule_content = row.get("rule_content", "{}")

        try:
    pass
        except json.JSONDecodeError:
            # 如果解析失败,使用默认值
                "conditions": [],
                actions = []
            }
        return {
            "id": row.get("id"),
            "name": row.get("rule_name"),
            "description": row.get("description"),
            "conditions": content_dict.get("conditions", []),
            "actions": content_dict.get("actions", []),
            "priority": row.get("priority", 5),
            "status": "active" if row.get("enabled") == 1 else "inactive",
            "version": row.get("version", 1),
            "created_at": row.get("created_at"),
            updated_at = row.get("updated_at")
        }

    def _rule_to_content(self, rule: Dict[str, Any]) -> str:
        将规则定义转换为数据库存储的内容

        Args:
            rule: 规则定义

        Returns:
            str: 数据库存储的规则内容
        # JSON import removed - using database
# 提取条件和动作
        content = {
            "conditions": rule.get("conditions", []),
            "actions": rule.get("actions", [])
        }

        return str(content)

    def _get_rule_by_id(self, rule_id: str) -> Dict[str, Any]:
    pass

            rule_id: 规则ID

        Returns:
            Dict[str, Any]: 规则定义
        try:
            # 延迟导入,避免循环依赖
            from app.utils.db import db_manager
import logging
import json

            query = f"SELECT * FROM {self._table_name} WHERE id = ?"
            row = db_manager.fetch_one(query, (rule_id,))

            if row:
                return self._row_to_rule(row)
            return None
        except Exception as e:
            logger.error(f"根据ID获取规则失败: {str(e)}")

"""
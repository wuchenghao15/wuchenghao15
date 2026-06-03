# -*- coding: utf-8 -*-
# MTSCOS AI Project 规则系统
"""
规则系统是一个模块化,可扩展的规则管理框架,用于定义,存储,执行和管理系统中的各种规则.

from typing import Dict, Any, List, Optional
from app.utils.logging import logger


class RuleSystem:
    规则系统主类,负责管理规则系统的各个组件

    def __init__(self):
        self._rule_manager = None
        self._rule_engine = None
        self._rule_sources = []
        self._initialized = False

    def initialize(self):
        初始化规则系统
        if self._initialized:
            return

        logger.info("初始化规则系统...")

        # 延迟导入,避免循环依赖
        from app.rules.managers.rule_manager import RuleManager
        from app.rules.engines.rule_engine import RuleEngine

        # 初始化规则管理器
        self._rule_manager = RuleManager()

        # 初始化规则引擎
        self._rule_engine = RuleEngine(self._rule_manager)

        # 初始化规则源
        self._init_rule_sources()

        # 加载所有规则
        self._rule_manager.load_all_rules()

        self._initialized = True
        logger.info("规则系统初始化完成")

    def _init_rule_sources(self):
        初始化规则源
        from app.rules.sources.file_source import FileRuleSource
        from app.rules.sources.database_source import DatabaseRuleSource
import logging
import sys

        # 添加文件规则源
        file_source = FileRuleSource()
        self.add_rule_source(file_source)

        # 添加数据库规则源
        db_source = DatabaseRuleSource()
        self.add_rule_source(db_source)

    def add_rule_source(self, source):
        添加规则源

        Args:
            source: 规则源对象,必须实现IRuleSource接口
        self._rule_sources.append(source)
        logger.info(f"添加规则源: {source.__class__.__name__}")

        # 如果规则系统已经初始化,立即从新源加载规则
        if self._initialized and self._rule_manager:
            self._rule_manager.load_rules_from_source(source)

    def get_rule_manager(self):
        获取规则管理器

        Returns:
            RuleManager: 规则管理器实例
        if not self._initialized:
            self.initialize()
        return self._rule_manager

    def get_rule_engine(self):
        获取规则引擎

        Returns:
            RuleEngine: 规则引擎实例
        if not self._initialized:
            self.initialize()
        return self._rule_engine

    def execute_rule(self, rule_id: str, **context) -> Any:
        执行指定规则

        Args:
            rule_id: 规则ID
            **context: 规则执行上下文
        Returns:
            Any: 规则执行结果
        if not self._initialized:
            self.initialize()
        return self._rule_engine.execute_rule(rule_id, **context)

    def execute_rules_by_type(self, rule_type: str, **context) -> Dict[str, Any]:
        执行指定类型的所有规则

        Args:
            **context: 规则执行上下文

        Returns:
            Dict[str, Any]: 规则执行结果,键为规则ID,值为执行结果
            self.initialize()
        return self._rule_engine.execute_rules_by_type(rule_type, **context)

    def add_rule(self, rule: Dict[str, Any]) -> str:
        添加新规则

        Args:
            rule: 规则定义

            str: 规则ID
        if not self._initialized:
            self.initialize()
        return self._rule_manager.add_rule(rule)


        Args:
            rule_id: 规则ID
            rule: 规则定义

        Returns:
            bool: 是否更新成功
            self.initialize()
        return self._rule_manager.update_rule(rule_id, rule)

    def delete_rule(self, rule_id: str) -> bool:
        删除规则
        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        if not self._initialized:
            self.initialize()

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        获取规则

        Args:
            rule_id: 规则ID

            Optional[Dict[str, Any]]: 规则定义
            self.initialize()
        return self._rule_manager.get_rule(rule_id)
    def get_rules(self, rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
    pass

        Args:
            rule_type: 规则类型,可选

        Returns:
            List[Dict[str, Any]]: 规则列表
        if not self._initialized:
    pass
        return self._rule_manager.get_rules(rule_type)


rule_system = RuleSystem()

# 规则系统常量
RULE_TYPES = {
    "PERMISSION": "permission",
    "SECURITY": "security",
    "BUSINESS": "business",
    "AI_MANAGEMENT": "ai_management",
    "TEST": "test",
}

RULE_STATUS = {
    "ACTIVE": "active",
    ARCHIVED = "archived"
}

RULE_PRIORITIES = {
    "LOW": 1,
    "MEDIUM": 5,
    "HIGH": 10,
    URGENT = 15

"""
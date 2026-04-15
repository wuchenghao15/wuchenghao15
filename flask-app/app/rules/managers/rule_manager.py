# MTSCOS AI Project 规则管理器
"""
规则管理器负责规则的存储、检索、添加、更新和删除。
"""

from typing import Dict, Any, List, Optional
import uuid
from app.utils.logging import logger
from app.rules import RULE_STATUS


class RuleManager:
    """
    规则管理器，负责规则的存储和管理
    """
    
    def __init__(self):
        self._rules: Dict[str, Dict[str, Any]] = {}  # 规则存储，键为规则ID
        self._rules_by_type: Dict[str, Dict[str, str]] = {}  # 按类型索引，键为规则类型，值为规则ID字典
        self._sources = []  # 规则源列表
    
    def load_all_rules(self):
        """
        从所有规则源加载规则
        """
        logger.info("从所有规则源加载规则...")
        
        # 延迟导入，避免循环依赖
        from app.rules.sources.file_source import FileRuleSource
        from app.rules.sources.database_source import DatabaseRuleSource
        
        # 从文件源加载规则
        file_source = FileRuleSource()
        self.load_rules_from_source(file_source)
        
        # 从数据库源加载规则
        db_source = DatabaseRuleSource()
        self.load_rules_from_source(db_source)
        
        logger.info(f"共加载 {len(self._rules)} 个规则")
    
    def load_rules_from_source(self, source):
        """
        从指定规则源加载规则
        
        Args:
            source: 规则源对象，必须实现load_rules方法
        """
        try:
            rules = source.load_rules()
            for rule in rules:
                self.add_rule(rule)
            logger.info(f"从 {source.__class__.__name__} 加载了 {len(rules)} 个规则")
        except Exception as e:
            logger.error(f"从 {source.__class__.__name__} 加载规则失败: {str(e)}")
    
    def add_rule(self, rule: Dict[str, Any]) -> str:
        """
        添加新规则
        
        Args:
            rule: 规则定义
        
        Returns:
            str: 规则ID
        """
        # 验证规则定义
        if not self._validate_rule(rule):
            logger.error("规则验证失败")
            return None
        
        # 生成规则ID
        rule_id = rule.get("id", str(uuid.uuid4()))
        rule["id"] = rule_id
        
        # 设置默认状态
        if "status" not in rule:
            rule["status"] = RULE_STATUS["ACTIVE"]
        
        # 添加规则到存储
        self._rules[rule_id] = rule
        
        # 更新按类型索引
        rule_type = rule.get("type", "unknown")
        if rule_type not in self._rules_by_type:
            self._rules_by_type[rule_type] = {}
        self._rules_by_type[rule_type][rule_id] = rule_id
        
        logger.info(f"添加规则: {rule_id} (类型: {rule_type}, 名称: {rule.get('name', '未命名')})")
        
        # 保存到持久化存储
        self._persist_rule(rule)
        
        return rule_id
    
    def update_rule(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """
        更新规则
        
        Args:
            rule_id: 规则ID
            rule: 规则定义
        
        Returns:
            bool: 是否更新成功
        """
        if rule_id not in self._rules:
            logger.error(f"规则不存在: {rule_id}")
            return False
        
        # 验证规则定义
        if not self._validate_rule(rule):
            logger.error("规则验证失败")
            return False
        
        # 获取旧规则，保留ID
        old_rule = self._rules[rule_id]
        rule["id"] = rule_id
        
        # 更新规则
        self._rules[rule_id] = rule
        
        # 更新按类型索引
        old_type = old_rule.get("type", "unknown")
        new_type = rule.get("type", "unknown")
        
        if old_type != new_type:
            # 从旧类型索引中移除
            if old_type in self._rules_by_type and rule_id in self._rules_by_type[old_type]:
                del self._rules_by_type[old_type][rule_id]
            
            # 添加到新类型索引
            if new_type not in self._rules_by_type:
                self._rules_by_type[new_type] = {}
            self._rules_by_type[new_type][rule_id] = rule_id
        
        logger.info(f"更新规则: {rule_id} (类型: {new_type}, 名称: {rule.get('name', '未命名')})")
        
        # 保存到持久化存储
        self._persist_rule(rule)
        
        return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        删除规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            bool: 是否删除成功
        """
        if rule_id not in self._rules:
            logger.error(f"规则不存在: {rule_id}")
            return False
        
        # 获取规则信息
        rule = self._rules[rule_id]
        rule_type = rule.get("type", "unknown")
        
        # 从存储中删除
        del self._rules[rule_id]
        
        # 从类型索引中删除
        if rule_type in self._rules_by_type and rule_id in self._rules_by_type[rule_type]:
            del self._rules_by_type[rule_type][rule_id]
        
        logger.info(f"删除规则: {rule_id} (类型: {rule_type}, 名称: {rule.get('name', '未命名')})")
        
        # 从持久化存储中删除
        self._delete_persisted_rule(rule_id)
        
        return True
    
    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        获取规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            Optional[Dict[str, Any]]: 规则定义
        """
        return self._rules.get(rule_id)
    
    def get_rules(self, rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取规则列表
        
        Args:
            rule_type: 规则类型，可选
        
        Returns:
            List[Dict[str, Any]]: 规则列表
        """
        if rule_type:
            # 按类型获取规则
            rule_ids = self._rules_by_type.get(rule_type, {})
            return [self._rules[rule_id] for rule_id in rule_ids if rule_id in self._rules]
        else:
            # 获取所有规则
            return list(self._rules.values())
    
    def get_rules_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        按状态获取规则
        
        Args:
            status: 规则状态
        
        Returns:
            List[Dict[str, Any]]: 规则列表
        """
        return [rule for rule in self._rules.values() if rule.get("status") == status]
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """
        验证规则定义
        
        Args:
            rule: 规则定义
        
        Returns:
            bool: 是否有效
        """
        # 检查必要字段
        required_fields = ["name", "type", "description", "conditions", "actions"]
        for field in required_fields:
            if field not in rule:
                logger.error(f"规则缺少必要字段: {field}")
                return False
        
        # 验证条件格式
        if not isinstance(rule["conditions"], list):
            logger.error("规则条件必须是列表")
            return False
        
        # 验证条件结构
        for i, condition in enumerate(rule["conditions"]):
            if not isinstance(condition, dict):
                logger.error(f"规则条件 {i} 必须是字典")
                return False
            # 检查条件必要字段
            if "type" not in condition or "params" not in condition:
                logger.error(f"规则条件 {i} 缺少必要字段 type 或 params")
                return False
        
        # 验证动作格式
        if not isinstance(rule["actions"], list):
            logger.error("规则动作必须是列表")
            return False
        
        # 验证动作结构
        for i, action in enumerate(rule["actions"]):
            if not isinstance(action, dict):
                logger.error(f"规则动作 {i} 必须是字典")
                return False
            # 检查动作必要字段
            if "type" not in action or "params" not in action:
                logger.error(f"规则动作 {i} 缺少必要字段 type 或 params")
                return False
        
        # 验证规则类型
        from app.rules import RULE_TYPES
        if rule["type"] not in RULE_TYPES.values() and rule["type"] != "unknown":
            logger.error(f"无效的规则类型: {rule['type']}")
            return False
        
        # 验证规则状态
        from app.rules import RULE_STATUS
        if "status" in rule and rule["status"] not in RULE_STATUS.values():
            logger.error(f"无效的规则状态: {rule['status']}")
            return False
        
        # 验证优先级
        if "priority" in rule:
            if not isinstance(rule["priority"], int) or rule["priority"] < 1 or rule["priority"] > 15:
                logger.error(f"规则优先级必须是1-15之间的整数: {rule['priority']}")
                return False
        
        return True
    
    def _persist_rule(self, rule: Dict[str, Any]):
        """
        持久化规则到存储
        
        Args:
            rule: 规则定义
        """
        try:
            # 延迟导入，避免循环依赖
            from app.rules.sources.database_source import DatabaseRuleSource
            from app.rules.sources.file_source import FileRuleSource
            
            # 保存到数据库
            db_source = DatabaseRuleSource()
            db_source.save_rule(rule)
            
            # 保存到文件
            file_source = FileRuleSource()
            file_source.save_rule(rule)
        except Exception as e:
            logger.error(f"持久化规则失败: {str(e)}")
    
    def _delete_persisted_rule(self, rule_id: str):
        """
        从持久化存储中删除规则
        
        Args:
            rule_id: 规则ID
        """
        try:
            # 延迟导入，避免循环依赖
            from app.rules.sources.database_source import DatabaseRuleSource
            from app.rules.sources.file_source import FileRuleSource
            
            # 从数据库删除
            db_source = DatabaseRuleSource()
            db_source.delete_rule(rule_id)
            
            # 从文件删除
            file_source = FileRuleSource()
            file_source.delete_rule(rule_id)
        except Exception as e:
            logger.error(f"从持久化存储删除规则失败: {str(e)}")
    
    def clear_all_rules(self):
        """
        清除所有规则
        """
        self._rules.clear()
        self._rules_by_type.clear()
        logger.info("已清除所有规则")
    
    def get_rule_count(self) -> int:
        """
        获取规则数量
        
        Returns:
            int: 规则数量
        """
        return len(self._rules)
    
    def get_rule_types(self) -> List[str]:
        """
        获取所有规则类型
        
        Returns:
            List[str]: 规则类型列表
        """
        return list(self._rules_by_type.keys())

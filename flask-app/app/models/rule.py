#!/usr/bin/env python3
"""
系统规则模型 - 用于存储和管理系统规则
"""

from app.models.base_model import BaseModel

class Rule(BaseModel):
    """系统规则模型"""

    table_name = 'rules'
    primary_key = 'id'

    columns = {
        'rule_type': 'TEXT NOT NULL',
        'rule_name': 'TEXT NOT NULL',
        'rule_content': 'TEXT NOT NULL',
        'description': 'TEXT',
        'priority': 'INTEGER DEFAULT 1',
        'enabled': 'INTEGER DEFAULT 1',
        'created_at': 'TEXT DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TEXT DEFAULT CURRENT_TIMESTAMP',
        'version': 'INTEGER DEFAULT 1',
        'status': 'TEXT DEFAULT "active"',
        'author': 'TEXT DEFAULT "system"',
        'conditions': 'TEXT DEFAULT "[]"',
        'actions': 'TEXT DEFAULT "[]"',
        'tags': 'TEXT DEFAULT "[]"',
        'effective_from': 'TEXT',
        'effective_to': 'TEXT',
        'last_executed_at': 'TEXT',
        'execution_count': 'INTEGER DEFAULT 0',
        'last_verified_at': 'TEXT',
        'verified_by': 'TEXT'
    }

    @classmethod
    def get_rules_by_type(cls, rule_type):
        """根据类型获取规则"""
        return cls.filter(rule_type=rule_type)

    @classmethod
    def get_enabled_rules(cls):
        """获取所有启用的规则"""
        return cls.filter(enabled=1)

    @classmethod
    def update_rule_content(cls, rule_id, new_content):
        """更新规则内容"""
        return cls.update(rule_id, rule_content=new_content)

    @classmethod
    def add_new_rule(cls, rule_type, rule_name, rule_content, description="", priority=1):
        """添加新规则"""
        return cls.create(
            rule_type=rule_type,
            rule_name=rule_name,
            rule_content=rule_content,
            description=description,
            priority=priority
        )

    def enable(self):
        """启用规则"""
        self.enabled = 1
        self.status = "active"
        return self.save()

    def disable(self):
        """禁用规则"""
        self.enabled = 0
        self.status = "inactive"
        return self.save()

    def archive(self):
        """归档规则"""
        self.enabled = 0
        return self.save()

    def get_conditions(self):
        """获取规则条件列表"""
        return eval(self.conditions or "[]")

    def set_conditions(self, conditions):
        """设置规则条件列表"""
        self.conditions = str(conditions or [])

    def get_actions(self):
        """获取规则动作列表"""
        return eval(self.actions or "[]")

    def set_actions(self, actions):
        """设置规则动作列表"""
        self.actions = str(actions or [])

    def get_tags(self):
        """获取规则标签列表"""
        return eval(self.tags or "[]")

    def set_tags(self, tags):
        """设置规则标签列表"""
        self.tags = str(tags or [])

    def verify(self, verified_by):
        """验证规则"""
        from datetime import datetime
        self.last_verified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.verified_by = verified_by
        return self.save()

    def increment_execution_count(self):
        """增加执行次数"""
        from datetime import datetime
        self.last_executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execution_count = (self.execution_count or 0) + 1
        return self.save()

    def to_dict(self):
        """转换为字典: 包含解析后的条件和动作"""
        result = super().to_dict()
        result['conditions'] = self.get_conditions()
        result['actions'] = self.get_actions()
        result['tags'] = self.get_tags()
        return result

#!/usr/bin/env python3
"""
系统规则模型，用于存储和管理系统规则
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
        'conditions': 'TEXT DEFAULT "[]"',  # 存储为JSON字符串
        'actions': 'TEXT DEFAULT "[]"',      # 存储为JSON字符串
        'tags': 'TEXT DEFAULT "[]"',        # 存储为JSON字符串
        'effective_from': 'TEXT',            # 生效时间
        'effective_to': 'TEXT',              # 失效时间
        'last_executed_at': 'TEXT',         # 最后执行时间
        'execution_count': 'INTEGER DEFAULT 0',  # 执行次数
        'last_verified_at': 'TEXT',         # 最后验证时间
        'verified_by': 'TEXT'               # 验证人
    }
    
    @classmethod
    def get_rules_by_type(cls, rule_type):
        """根据类型获取规则"""
        return cls.filter(
            where_clause="rule_type = ? AND enabled = 1",
            where_params=(rule_type,),
            order_by="priority DESC"
        )
    
    @classmethod
    def get_enabled_rules(cls):
        """获取所有启用的规则"""
        return cls.filter(
            where_clause="enabled = 1",
            order_by="rule_type, priority DESC"
        )
    
    @classmethod
    def update_rule_content(cls, rule_id, new_content):
        """更新规则内容"""
        rule = cls.get_by_id(rule_id)
        if rule:
            rule.rule_content = new_content
            rule.version += 1
            return rule.save()
        return False
    
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
        self.status = "archived"
        return self.save()
    
    def get_conditions(self):
        """获取规则条件列表"""
        import json
        return json.loads(self.conditions or "[]")
    
    def set_conditions(self, conditions):
        """设置规则条件列表"""
        import json
        self.conditions = json.dumps(conditions or [])
    
    def get_actions(self):
        """获取规则动作列表"""
        import json
        return json.loads(self.actions or "[]")
    
    def set_actions(self, actions):
        """设置规则动作列表"""
        import json
        self.actions = json.dumps(actions or [])
    
    def get_tags(self):
        """获取规则标签列表"""
        import json
        return json.loads(self.tags or "[]")
    
    def set_tags(self, tags):
        """设置规则标签列表"""
        import json
        self.tags = json.dumps(tags or [])
    
    def verify(self, verified_by):
        """验证规则"""
        from datetime import datetime
        self.last_verified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.verified_by = verified_by
        return self.save()
    
    def increment_execution_count(self):
        """增加执行次数"""
        from datetime import datetime
        self.execution_count = (self.execution_count or 0) + 1
        self.last_executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.save()
    
    @classmethod
    def get_rules_by_status(cls, status):
        """根据状态获取规则"""
        return cls.filter(
            where_clause="status = ?",
            where_params=(status,),
            order_by="priority DESC"
        )
    
    @classmethod
    def get_rules_by_tag(cls, tag):
        """根据标签获取规则"""
        import json
        rules = cls.filter(order_by="priority DESC")
        return [rule for rule in rules if tag in rule.get_tags()]
    
    def to_dict(self):
        """转换为字典，包含解析后的条件和动作"""
        result = super().to_dict()
        result['conditions'] = self.get_conditions()
        result['actions'] = self.get_actions()
        result['tags'] = self.get_tags()
        return result

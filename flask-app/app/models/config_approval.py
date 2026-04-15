#!/usr/bin/env python3
"""
系统参数配置审批模型
"""

from app.models.base_model import BaseModel

class ConfigApproval(BaseModel):
    """系统参数配置审批模型"""
    
    # 表名
    table_name = "config_approval"
    
    # 字段定义
    fields = {
        "id": {"type": "INTEGER", "primary_key": True, "auto_increment": True},
        "config_key": {"type": "VARCHAR(100)", "not_null": True},  # 关联的配置键
        "old_value": {"type": "TEXT"},  # 旧值
        "new_value": {"type": "TEXT", "not_null": True},  # 新值
        "description": {"type": "VARCHAR(255)"},  # 变更描述
        "category": {"type": "VARCHAR(50)"},  # 参数类别
        "data_type": {"type": "VARCHAR(20)"},  # 参数数据类型
        "requested_by": {"type": "VARCHAR(50)", "not_null": True},  # 请求人
        "requested_role": {"type": "VARCHAR(50)", "not_null": True},  # 请求人角色
        "requested_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},  # 请求时间
        "status": {"type": "VARCHAR(20)", "default": "pending"},  # 状态：pending, approved, rejected
        "approved_by": {"type": "VARCHAR(50)"},  # 审批人
        "approved_at": {"type": "TIMESTAMP"},  # 审批时间
        "approval_comments": {"type": "TEXT"}  # 审批意见
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @classmethod
    def get_pending_approvals(cls):
        """获取所有待审批的请求"""
        return cls.filter(status="pending").all()
    
    @classmethod
    def get_by_config_key(cls, config_key):
        """根据配置键获取审批请求"""
        return cls.filter(config_key=config_key).all()
    
    @classmethod
    def get_by_requestor(cls, requested_by):
        """根据请求人获取审批请求"""
        return cls.filter(requested_by=requested_by).all()
    
    def approve(self, approved_by):
        """批准变更"""
        from app.models.system_config import SystemConfig
        import datetime
        
        self.status = "approved"
        self.approved_by = approved_by
        self.approved_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save()
        
        # 更新实际配置
        config = SystemConfig.get_by_key(self.config_key)
        if config:
            config.value = self.new_value
            config.description = self.description
            config.category = self.category
            config.data_type = self.data_type
            config.save()
        else:
            # 如果配置不存在，创建新配置
            SystemConfig(
                key=self.config_key,
                value=self.new_value,
                description=self.description,
                category=self.category,
                data_type=self.data_type
            ).save()
    
    def reject(self, rejected_by, comments=""):
        """拒绝变更"""
        import datetime
        
        self.status = "rejected"
        self.approved_by = rejected_by
        self.approved_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.approval_comments = comments
        self.save()

# 初始化数据表
if __name__ == "__main__":
    ConfigApproval.create_table()
    print("系统参数配置审批表创建成功")

#!/usr/bin/env python3
"""
系统参数配置审批模型
"""

from app.models.base_model import BaseModel

class ConfigApproval(BaseModel):
    """系统参数配置审批模型"""

    table_name = "config_approval"

    fields = {
        "id": {"type": "INTEGER", "primary_key": True, "auto_increment": True},
        "config_key": {"type": "VARCHAR(100)", "not_null": True},
        "old_value": {"type": "TEXT"},
        "new_value": {"type": "TEXT", "not_null": True},
        "description": {"type": "VARCHAR(255)"},
        "category": {"type": "VARCHAR(50)"},
        "data_type": {"type": "VARCHAR(20)"},
        "requested_by": {"type": "VARCHAR(50)", "not_null": True},
        "requested_role": {"type": "VARCHAR(50)", "not_null": True},
        "requested_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
        "status": {"type": "VARCHAR(20)", "default": "pending"},
        "approved_by": {"type": "VARCHAR(50)"},
        "approved_at": {"type": "TIMESTAMP"},
        "approval_comments": {"type": "TEXT"}
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_pending_approvals(cls):
        """获取所有待审批的请求"""
        return cls.filter(status="pending").all()

    def approve(self, approved_by):
        """批准变更"""
        from app.models.system_config import SystemConfig
        import datetime

        self.status = "approved"
        self.approved_by = approved_by
        self.approved_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save()

        config = SystemConfig.get_by_key(self.config_key)
        if config:
            config.value = self.new_value
            config.description = self.description
            config.category = self.category
            config.data_type = self.data_type
            config.save()
        else:
            SystemConfig.create(
                key=self.config_key,
                value=self.new_value,
                description=self.description,
                category=self.category,
                data_type=self.data_type
            )

    def reject(self, rejected_by, comments=""):
        """拒绝变更"""
        import datetime

        self.status = "rejected"
        self.approved_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.approval_comments = comments
        self.save()

if __name__ == "__main__":
    ConfigApproval.create_table()

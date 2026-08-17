# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI基类模块
为所有AI实例提供基础功能
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger('base_ai')

class BaseAI:
    """AI基类"""

    def __init__(self, instance_id: str, ai_type: str = 'base'):
        """初始化AI基类"""
        self.instance_id = instance_id
        self.ai_type = ai_type
        self.name = 'Base AI'
        self.description = 'AI基类'
        self.responsibilities = []
        self.status = 'initialized'
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.config = {}
        self.bound_user = None
        logger.info(f"AI实例初始化: {self.instance_id} (类型: {self.ai_type})")

    def initialize(self) -> bool:
        """初始化AI实例"""
        try:
            self.status = 'running'
            self.updated_at = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"AI实例初始化失败: {str(e)}")
            self.status = 'error'
            return False

    def shutdown(self):
        """关闭AI实例"""
        try:
            self.status = 'stopped'
        except Exception as e:
            logger.error(f"关闭AI实例时出错: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        return {
            'instance_id': self.instance_id,
            'ai_type': self.ai_type,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'responsibilities': self.responsibilities
        }

    def update_config(self, config: Dict[str, Any]) -> bool:
        """更新AI实例配置"""
        try:
            self.config.update(config)
            self.updated_at = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"更新AI实例配置失败: {str(e)}")
            return False

    def bind_user(self, user_id: str) -> bool:
        """绑定用户"""
        try:
            self.bound_user = user_id
            self.updated_at = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"绑定用户失败: {str(e)}")
            return False

    def unbind_user(self) -> bool:
        """解绑用户"""
        try:
            self.bound_user = None
            self.updated_at = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"解绑用户失败: {str(e)}")
            return False

    def get_responsibilities(self) -> List[str]:
        """获取职责列表"""
        return self.responsibilities

    def add_responsibility(self, responsibility: str) -> bool:
        """添加职责"""
        try:
            if responsibility not in self.responsibilities:
                self.responsibilities.append(responsibility)
                self.updated_at = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"添加职责失败: {str(e)}")
            return False

    def remove_responsibility(self, responsibility: str) -> bool:
        """移除职责"""
        try:
            if responsibility in self.responsibilities:
                self.responsibilities.remove(responsibility)
                self.updated_at = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"移除职责失败: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'ai_type': self.ai_type,
            'name': self.name,
            'description': self.description,
            'responsibilities': self.responsibilities,
            'status': self.status,
            'config': self.config,
            'updated_at': self.updated_at
        }

if __name__ == '__main__':
    base_ai = BaseAI('test-base-ai', 'test')
    print("初始化BaseAI:")
    print(f"实例ID: {base_ai.instance_id}")
    print(f"类型: {base_ai.ai_type}")
    print(f"状态: {base_ai.status}")

    # 测试初始化
    success = base_ai.initialize()
    print(f"初始化成功: {success}")
    print(f"状态: {base_ai.status}")

    # 测试添加职责
    print("\n测试添加职责:")
    base_ai.add_responsibility('测试职责1')
    base_ai.add_responsibility('测试职责2')
    print(f"职责列表: {base_ai.responsibilities}")

    print("\n测试更新配置:")
    base_ai.update_config({'test_key': 'test_value'})
    print(f"配置: {base_ai.config}")

    # 测试绑定用户
    base_ai.bind_user('test-user-1')
    print(f"绑定用户: {base_ai.bound_user}")

    # 测试获取状态
    print("\n测试获取状态:")
    status = base_ai.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")

    print("\n测试关闭:")
    base_ai.shutdown()
    print(f"状态: {base_ai.status}")

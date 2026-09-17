"""system_upgrade_manager 模块 stub.

提供 check_upgrade() 与 get_upgrade_history() 空数据占位, 避免依赖此模块的 API 路由
因 ImportError / AttributeError 而返回 500. 后续可替换为真实升级逻辑。
"""
from __future__ import annotations


def check_upgrade(*args, **kwargs):
    """检查系统升级状态 (stub). 返回空结果。"""
    return {
        "upgrade_available": False,
        "current_version": "",
        "latest_version": "",
        "detail": "system_upgrade_manager stub: no upgrade data available",
    }


def get_upgrade_history(*args, **kwargs):
    """返回升级历史 (stub). 返回空列表。"""
    return []

class SystemUpgradeManager:
    """system_upgrade_manager 对象占位, 提供 API 路由所需的方法接口。"""

    def check_for_updates(self, *args, **kwargs):
        return check_upgrade(*args, **kwargs)

    def get_upgrade_history(self, *args, **kwargs):
        return get_upgrade_history(*args, **kwargs)

    def execute_upgrade(self, upgrade_type='full', *args, **kwargs):
        return {
            "success": False,
            "upgrade_type": upgrade_type,
            "message": "system_upgrade_manager stub: 升级执行未实现",
        }


system_upgrade_manager = SystemUpgradeManager()

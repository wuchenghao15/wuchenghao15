#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记录硬件管理系统UI增强版更新到数据库版本管理系统
"""

import sys
import os

# 确保我们在正确的目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
os.chdir(project_dir)

# 添加项目路径
sys.path.insert(0, project_dir)

from app.models.database_version_manager import db_version_manager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_hardware_ui_update():
    """记录硬件管理系统UI增强版更新"""
    
    version = "1.6.0"
    description = "硬件管理系统UI增强版 - 完善侧边栏和主内容区功能"
    
    changes = [
        "完善侧边栏功能 - 添加系统状态指示器、导航折叠、多级菜单、快捷操作面板",
        "拓展主内容区顶部栏 - 添加全局搜索增强、通知下拉面板、用户菜单、快捷操作按钮",
        "优化仪表盘主内容 - 添加实时数据图表、设备状态热力图、AI分析面板增强",
        "添加响应式设计和移动端适配",
        "修复模板路径配置问题 - 确保硬件管理系统模板正确加载",
        "完善所有硬件管理页面 - 仪表盘、设备管理、系统设置、性能监控、系统日志、API密钥管理",
        "增强用户体验 - 添加实时性能监控和智能分析功能"
    ]
    
    # 记录到数据库版本管理系统
    success = db_version_manager.create_version(
        version=version,
        description=description,
        changes=changes,
        created_by="System AI"
    )
    
    if success:
        logger.info(f"✅ 成功记录版本 {version} 到数据库版本管理系统")
        
        # 记录相关变更
        db_version_manager.record_change(
            version=version,
            change_type="ui_enhancement",
            table_name="templates",
            field_name="hardware_ui",
            old_value="1.5.0",
            new_value="1.6.0",
            sql_statement="Update hardware management templates",
            affected_rows=6,
            created_by="System AI"
        )
        
        logger.info(f"✅ 成功记录版本 {version} 的变更详情")
        return True
    else:
        logger.error(f"❌ 记录版本 {version} 失败")
        return False


if __name__ == "__main__":
    print("正在记录硬件管理系统UI增强版更新...")
    result = record_hardware_ui_update()
    
    if result:
        print("✅ 更新记录成功！")
        
        # 显示数据库版本信息
        print("\n当前数据库版本信息:")
        versions = db_version_manager.get_all_versions()
        for v in versions:
            print(f"  - v{v['version']}: {v['description']}")
    else:
        print("❌ 更新记录失败！")
        sys.exit(1)

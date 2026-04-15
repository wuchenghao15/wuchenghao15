#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI表创建和实例保存
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.ai import AIInstance


def test_ai_table_creation():
    """测试AI表创建"""
    print("测试AI表创建...")
    
    # 创建表
    success = AIInstance.create_table()
    print(f"创建表结果: {'成功' if success else '失败'}")
    
    # 创建测试AI实例
    print("\n测试创建AI实例...")
    ai_instance = AIInstance(
        instance_id='test-ai-1',
        ai_type='general',
        name='测试AI',
        description='测试AI实例',
        functions=['test_function'],
        responsibilities=['test_responsibility'],
        status='active',
        config={'test_key': 'test_value'}
    )
    
    # 保存AI实例
    saved_instance = ai_instance.save()
    print(f"保存AI实例结果: {'成功' if saved_instance else '失败'}")
    
    # 获取AI实例
    print("\n测试获取AI实例...")
    retrieved_instance = AIInstance.get_by_id('test-ai-1')
    print(f"获取AI实例结果: {'成功' if retrieved_instance else '失败'}")
    
    if retrieved_instance:
        print(f"实例ID: {retrieved_instance.instance_id}")
        print(f"实例类型: {retrieved_instance.ai_type}")
        print(f"实例名称: {retrieved_instance.name}")
        print(f"实例状态: {retrieved_instance.status}")
    
    # 获取所有AI实例
    print("\n测试获取所有AI实例...")
    all_instances = AIInstance.get_all_instances()
    print(f"获取所有AI实例结果: {len(all_instances)} 个实例")
    
    for instance in all_instances:
        print(f"- {instance.instance_id}: {instance.name}")
    
    print("\n测试完成!")


if __name__ == '__main__':
    test_ai_table_creation()

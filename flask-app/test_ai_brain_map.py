#!/usr/bin/env python3
"""
AI脑图分布式管理系统测试脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from app.ai.ai_brain_map import ai_brain_map

def test_ai_brain_map():
    """测试AI脑图分布式管理系统"""
    print("=" * 60)
    print("AI脑图分布式管理系统测试")
    print("=" * 60)
    
    # 1. 初始化AI脑图
    print("\n1. 初始化AI脑图...")
    success = ai_brain_map.initialize()
    if success:
        print("✅ AI脑图初始化成功")
    else:
        print("❌ AI脑图初始化失败")
        return False
    
    # 2. 创建分布式AI功能集
    print("\n2. 创建分布式AI功能集...")
    collection = ai_brain_map.create_distributed_ai_collection(
        name="测试AI功能集",
        description="用于测试的分布式AI功能集",
        knowledge_tags=["AI", "管理", "优化"]
    )
    
    if collection:
        print(f"✅ 成功创建分布式AI功能集: {collection['name']} (ID: {collection['collection_id']})")
    else:
        print("❌ 创建分布式AI功能集失败")
        return False
    
    # 3. 基于AI脑图创建AI员工
    print("\n3. 基于AI脑图创建AI员工...")
    ai_employee = ai_brain_map.create_ai_employee_from_brain(
        name="测试AI员工",
        ai_type="general",
        capabilities=["对话交互", "信息查询", "任务执行"],
        knowledge_tags=["AI", "对话"]
    )
    
    if ai_employee:
        print(f"✅ 成功创建AI员工: {ai_employee['name']} (ID: {ai_employee['employee_id']})")
    else:
        print("❌ 创建AI员工失败")
        return False
    
    # 4. 将AI员工分配到AI功能集
    print("\n4. 将AI员工分配到AI功能集...")
    success = ai_brain_map.assign_ai_employee_to_collection(
        employee_id=ai_employee["employee_id"],
        collection_id=collection["collection_id"]
    )
    
    if success:
        print(f"✅ 成功将AI员工 {ai_employee['employee_id']} 分配到AI功能集 {collection['collection_id']}")
    else:
        print("❌ 将AI员工分配到AI功能集失败")
        return False
    
    # 5. 基于知识域分布式部署AI员工
    print("\n5. 基于知识域分布式部署AI员工...")
    deployed_employees = ai_brain_map.distribute_ai_employees(
        knowledge_domain="系统优化",
        ai_count=2
    )
    
    if deployed_employees:
        print(f"✅ 成功基于知识域分布式部署 {len(deployed_employees)} 个AI员工")
        for i, employee in enumerate(deployed_employees, 1):
            print(f"   {i}. {employee['name']} (ID: {employee['employee_id']})")
    else:
        print("❌ 基于知识域分布式部署AI员工失败")
    
    # 6. 获取AI功能集中的AI员工
    print(f"\n6. 获取AI功能集 {collection['name']} 中的AI员工...")
    employees = ai_brain_map.get_ai_collection_employees(collection["collection_id"])
    if employees:
        print(f"✅ 成功获取 {len(employees)} 个AI员工:")
        for employee in employees:
            print(f"   - {employee['name']} (ID: {employee['employee_id']})")
    else:
        print(f"❌ 未找到AI功能集 {collection['name']} 中的AI员工")
    
    # 7. 生成AI脑图报告
    print("\n7. 生成AI脑图报告...")
    report = ai_brain_map.generate_brain_map_report()
    if report:
        print("✅ 成功生成AI脑图报告:")
        print(f"   - 时间戳: {report['timestamp']}")
        print(f"   - 总节点数: {report['total_nodes']}")
        print(f"   - 总边数: {report['total_edges']}")
        print(f"   - AI集数量: {report['ai_collections']}")
        print(f"   - AI员工数量: {report['ai_employees']}")
        print(f"   - 节点类型: {report['node_types']}")
        print(f"   - 边类型: {report['edge_types']}")
    else:
        print("❌ 生成AI脑图报告失败")
    
    # 8. 优化AI脑图
    print("\n8. 优化AI脑图...")
    success = ai_brain_map.optimize_brain_map()
    if success:
        print("✅ AI脑图优化完成")
    else:
        print("❌ AI脑图优化失败")
    
    print("\n" + "=" * 60)
    print("AI脑图分布式管理系统测试完成")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_ai_brain_map()
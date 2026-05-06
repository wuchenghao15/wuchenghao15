#!/usr/bin/env python3
"""
初始化AI脑库

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

print("初始化AI脑库...")

# 导入AI脑库服务
try:
    from app.services.ai_brain_service import ai_brain_service
    print("✓ 成功导入AI脑库服务")

    # 导入AI实例管理器
    from app.ai.instances import ai_instance_manager
    print("✓ 成功导入AI实例管理器")

    # 添加初始知识
    print("\n添加初始知识到AI脑库...")

    # 添加服务器启动问题知识
    problem = ai_brain_service.add_problem(
        title="服务器启动失败问题",
        content="服务器无法在指定端口上启动，curl请求返回连接失败",
        source="system",
        tags=["服务器", "启动失败", "端口", "curl", "连接失败"]
    )

    if problem:
        # 添加解决方案
        ai_brain_service.add_solution(
            title="服务器启动失败解决方案",
            content="1. 检查端口是否被占用\n2. 检查防火墙设置\n3. 检查服务器绑定的IP地址\n4. 检查服务器启动脚本\n5. 检查应用配置\n6. 尝试使用不同的端口\n7. 检查Werkzeug版本兼容性",
            source="system",
            tags=["服务器", "启动失败", "解决方案", "端口", "防火墙", "IP地址", "Werkzeug"]
        )

    ai_brain_service.add_experience(
        title="AI集管理最佳实践",
        content="1. 定期同步AI实例知识到AI脑库\n2. 为AI集添加清晰的描述和标签\n3. 定期检查AI集状态\n4. 优化AI集配置\n5. 监控AI集性能\n6. 定期升级AI集",
        source="system",
    )

    # 添加AI实例管理规则
        title="AI实例管理规则",
        content="1. 每个AI实例必须有唯一的ID\n2. AI实例必须分配到合适的AI集\n3. 定期检查AI实例状态\n4. 定期同步AI实例知识到AI脑库\n5. 定期清理长时间未使用的AI实例\n6. 定期升级AI实例配置",
        source="system",
    )

    print("✓ 成功添加初始知识到AI脑库")

    print("\n同步AI实例知识到AI脑库...")
    synced_count = ai_instance_manager.sync_all_instances_to_brain()
    print(f"✓ 成功同步 {synced_count} 个AI实例知识到AI脑库")

    # 获取AI脑库统计信息
    print("\n获取AI脑库统计信息...")
    stats = ai_brain_service.get_knowledge_stats()
    if stats:
        print(f"✓ AI脑库统计信息:")
        print(f"  总知识数: {stats['total_knowledge']}")
        print(f"  知识类型: {stats['knowledge_types']}")
        print(f"  知识来源: {stats['sources']}")
        print(f"  活跃知识数: {stats['active_knowledge']}")
        print(f"  热门标签: {stats['top_tags']}")

    print("\n✓ AI脑库初始化完成")

except Exception as e:
    print(f"✗ AI脑库初始化失败: {str(e)}")
    import traceback
    traceback.print_exc()

"""
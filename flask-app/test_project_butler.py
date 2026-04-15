#!/usr/bin/env python3
"""
项目管家测试脚本
"""

import sys
from app.services.project_butler import project_butler

# 初始化项目管家
try:
    print("初始化项目管家...")
    success = project_butler.initialize()
    if success:
        print("✓ 项目管家初始化成功")
    else:
        print("✗ 项目管家初始化失败")
        sys.exit(1)
except Exception as e:
    print(f"✗ 项目管家初始化异常: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试系统状态获取
try:
    print("\n测试系统状态获取...")
    status = project_butler.get_system_status()
    print(f"✓ 系统状态获取成功")
    print(f"  - 初始化状态: {status['initialized']}")
    print(f"  - 运行状态: {status['running']}")
    print(f"  - 项目数量: {status['projects_count']}")
    print(f"  - 任务数量: {status['tasks_count']}")
except Exception as e:
    print(f"✗ 系统状态获取失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试项目创建
try:
    print("\n测试项目创建...")
    
    # 测试数据
    project_info = {
        "name": "测试项目",
        "description": "这是一个测试项目",
        "goals": ["完成项目管家开发", "测试所有功能", "生成报告"],
        "priority": "high",
        "team": "default",
        "owner": "system"
    }
    
    project_id = project_butler.create_project(project_info)
    if project_id:
        print(f"✓ 项目创建成功，项目ID: {project_id}")
    else:
        print("✗ 项目创建失败")
        sys.exit(1)
except Exception as e:
    print(f"✗ 项目创建失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试获取项目信息
try:
    print("\n测试获取项目信息...")
    project = project_butler.get_project(project_id)
    if project:
        print(f"✓ 项目信息获取成功")
        print(f"  - 项目名称: {project['name']}")
        print(f"  - 项目状态: {project['status']}")
        print(f"  - 项目优先级: {project['priority']}")
        print(f"  - 项目目标: {', '.join(project['goals'])}")
    else:
        print("✗ 项目信息获取失败")
except Exception as e:
    print(f"✗ 项目信息获取失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试项目列表获取
try:
    print("\n测试项目列表获取...")
    projects = project_butler.list_projects()
    print(f"✓ 项目列表获取成功，共 {len(projects)} 个项目")
    for proj in projects:
        print(f"  - {proj['name']} ({proj['status']})")
except Exception as e:
    print(f"✗ 项目列表获取失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试任务创建
try:
    print("\n测试任务创建...")
    
    # 创建第一个任务
    task1_info = {
        "name": "任务1: 实现项目管家核心功能",
        "description": "实现项目创建、任务分配、进度跟踪等核心功能",
        "priority": "high",
        "assignee": "developer1",
        "duration": 8
    }
    
    task1_id = project_butler.create_task(project_id, task1_info)
    if task1_id:
        print(f"✓ 任务1创建成功，任务ID: {task1_id}")
    else:
        print("✗ 任务1创建失败")
    
    # 创建第二个任务
    task2_info = {
        "name": "任务2: 编写测试脚本",
        "description": "编写项目管家的测试脚本",
        "priority": "medium",
        "assignee": "tester1",
        "duration": 4,
        "dependencies": [task1_id]
    }
    
    task2_id = project_butler.create_task(project_id, task2_info)
    if task2_id:
        print(f"✓ 任务2创建成功，任务ID: {task2_id}")
    else:
        print("✗ 任务2创建失败")
except Exception as e:
    print(f"✗ 任务创建失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试任务分配
try:
    print("\n测试任务分配...")
    success = project_butler.assign_task(task1_id, "developer2")
    if success:
        print(f"✓ 任务分配成功，任务 {task1_id} 分配给 developer2")
    else:
        print(f"✗ 任务分配失败")
except Exception as e:
    print(f"✗ 任务分配失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试任务进度更新
try:
    print("\n测试任务进度更新...")
    success = project_butler.update_task_progress(task1_id, 50)
    if success:
        print(f"✓ 任务进度更新成功，任务 {task1_id} 进度: 50%")
    else:
        print(f"✗ 任务进度更新失败")
    
    # 获取任务信息验证进度
    task = project_butler.get_task(task1_id)
    if task and task["progress"] == 50:
        print(f"✓ 任务进度验证成功")
except Exception as e:
    print(f"✗ 任务进度更新失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试任务状态更新
try:
    print("\n测试任务状态更新...")
    # 更新任务1为已完成
    success = project_butler.update_task(task1_id, {"status": "completed", "progress": 100})
    if success:
        print(f"✓ 任务1状态更新成功，状态: completed")
    else:
        print(f"✗ 任务1状态更新失败")
    
    # 更新任务2为进行中
    success = project_butler.update_task(task2_id, {"status": "in_progress", "progress": 30})
    if success:
        print(f"✓ 任务2状态更新成功，状态: in_progress，进度: 30%")
    else:
        print(f"✗ 任务2状态更新失败")
except Exception as e:
    print(f"✗ 任务状态更新失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试任务列表获取
try:
    print("\n测试任务列表获取...")
    tasks = project_butler.list_tasks({"project_id": project_id})
    print(f"✓ 任务列表获取成功，共 {len(tasks)} 个任务")
    for task in tasks:
        print(f"  - {task['name']}: {task['status']} ({task['progress']}%)")
except Exception as e:
    print(f"✗ 任务列表获取失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试项目仪表板
try:
    print("\n测试项目仪表板获取...")
    dashboard = project_butler.get_project_dashboard(project_id)
    if "error" not in dashboard:
        print(f"✓ 项目仪表板获取成功")
        print(f"  - 项目名称: {dashboard['project']['name']}")
        print(f"  - 项目状态: {dashboard['project']['status']}")
        print(f"  - 总任务数: {dashboard['statistics']['total_tasks']}")
        print(f"  - 完成任务数: {dashboard['statistics']['completed_tasks']}")
        print(f"  - 进行中任务数: {dashboard['statistics']['in_progress_tasks']}")
        print(f"  - 项目进度: {dashboard['statistics']['progress']}%")
        print(f"  - 时间线事件数: {len(dashboard['timeline'])}")
    else:
        print(f"✗ 项目仪表板获取失败: {dashboard['error']}")
except Exception as e:
    print(f"✗ 项目仪表板获取失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试项目删除
try:
    print("\n测试项目删除...")
    success = project_butler.delete_project(project_id)
    if success:
        print(f"✓ 项目删除成功")
    else:
        print(f"✗ 项目删除失败")
except Exception as e:
    print(f"✗ 项目删除失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 关闭项目管家
try:
    print("\n关闭项目管家...")
    success = project_butler.shutdown()
    if success:
        print("✓ 项目管家关闭成功")
    else:
        print("✗ 项目管家关闭失败")
except Exception as e:
    print(f"✗ 项目管家关闭异常: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")

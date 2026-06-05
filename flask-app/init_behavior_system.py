#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化学生行为管理系统
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.models.student_behavior import init_behavior_system

if __name__ == '__main__':
    print("开始初始化学生行为管理系统...")
    try:
        success = init_behavior_system()
        if success:
            print("✓ 学生行为管理系统初始化成功！")
            print("创建的表包括：")
            print("  - behavior_categories (行为分类表)")
            print("  - behavior_records (行为记录表)")
            print("  - behavior_goals (行为目标表)")
            print("默认分类包括：")
            print("  1. 课堂表现")
            print("  2. 作业完成")
            print("  3. 考试成绩")
            print("  4. 纪律表现")
            print("  5. 团队合作")
            print("  6. 创新实践")
            print("  7. 助人为乐")
            print("  8. 出勤情况")
            print("  9. 学习态度")
            print("  10. 其他")
        else:
            print("✗ 初始化失败！")
    except Exception as e:
        print(f"✗ 初始化出错：{e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化锦标赛系统数据库
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.exam_tournament import init_tournament_system

if __name__ == '__main__':
    print("正在初始化锦标赛系统...")
    try:
        result = init_tournament_system()
        if result:
            print("✅ 锦标赛系统初始化成功!")
            print("已创建以下默认锦标赛:")
            print("  1. 🥇 金牌杯数学挑战赛")
            print("  2. 🏆 大师杯英语能力赛")
            print("  3. ⚡ 编程大奖赛")
            print("  4. 🎯 综合知识挑战赛")
            print("  5. 🥇 日语能力挑战赛")
            print("  6. 🏆 AI技能大师杯")
        else:
            print("❌ 锦标赛系统初始化失败")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化学习系统脚本
用于创建学习系统的表结构，并添加初始数据

import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('initialize_learning_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('InitializeLearningSystem')

def initialize_learning_system():
    """初始化学习系统"""
    logger.info("开始初始化学习系统...")

    try:
        # 添加项目根目录到Python路径
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # 导入学习系统模型
        from app.models.learning_system import LearningSystem

        # 初始化学习系统表
        logger.info("初始化学习系统表结构...")
        LearningSystem.initialize_tables()

        # 导入课程和章节模型
        from app.models.learning_system import Course, Lesson

        # 添加初始课程
        logger.info("添加初始课程...")

        # 创建日语基础课程
        basic_japanese_course = Course(
            title="日语基础入门",
            description="适合零基础学习者的日语入门课程，涵盖基本词汇、语法和日常对话。",
            language="japanese",
            level="beginner",
            category="日常对话",
            created_by=1  # 假设用户ID为1的是管理员
        )
        logger.info(f"创建课程: {basic_japanese_course.title}")

        # 创建日语基础课程的章节
        lesson1 = Lesson(
            course_id=basic_japanese_course.course_id,
            title="日语字母 - 平假名",
            description="学习日语平假名的发音和书写",
            order_index=1,
            content={
                "sections": [
                    {
                        "title": "平假名简介",
                        "content": "平假名是日语的基础字母之一，用于表示日语的固有词汇和语法结构。",
                        "type": "text"
                    },
                    {
                        "title": "あ行",
                        "type": "hiragana"
                    },
                    {
                        "title": "か行",
                    }
                ],
                "exercises": [
                    {
                        "options": [
                            {"hiragana": "あ", "pronunciation": "a"},
                            {"hiragana": "い", "pronunciation": "i"},
                            {"hiragana": "う", "pronunciation": "u"}
                        ]
                ]
        )
        lesson1.save()
        logger.info(f"创建章节: {lesson1.title}")
        lesson2 = Lesson(
            course_id=basic_japanese_course.course_id,
            title="日语字母 - 片假名",
            order_index=2,
                    {
                        "title": "片假名简介",
                        "content": "片假名主要用于表示外来语、拟声词和强调。",
                        "type": "text"
                    {
                        "content": "アイウエオ",
                    }
                ]
        )
        lesson2.save()

        basic_english_course = Course(
            description="适合零基础学习者的英语入门课程，涵盖基本词汇、语法和日常对话。",
            level="beginner",
            category="日常对话",
            created_by=1
        )
        basic_english_course.save()
        logger.info(f"创建课程: {basic_english_course.title}")

            description="学习英语26个字母的发音和书写",
            content={
                "sections": [
                    {
                        "title": "字母表简介",
                        "content": "英语使用拉丁字母表，共有26个字母。",
                        "type": "text"
                    },
                    {
                        "title": "元音字母",
                        "content": "a, e, i, o, u",
                    },
                        "title": "辅音字母",
                        "content": "b, c, d, f, g, h, j, k, l, m, n, p, q, r, s, t, v, w, x, y, z",
                    }
                ]
        lesson3.save()
        logger.info(f"创建章节: {lesson3.title}")

        logger.info("初始课程和章节创建完成")
        logger.info("\n学习系统初始化结果:")
        logger.info("- 表结构已创建")
        logger.info("- 2门课程已创建")
        logger.info("- 3个章节已创建")

    except Exception as e:
        import traceback
        return False

def test_learning_system_api():

    try:
        import requests

        # 测试API基础URL
        base_url = "http://localhost:5000/api/learning"

        # 测试获取课程列表
        logger.info("测试获取课程列表...")
        if response.status_code == 200:
        else:
            logger.error(f"获取课程列表失败: {response.status_code}")

        # 测试获取用户学习摘要
        logger.info("测试获取用户学习摘要...")
        response = requests.get(f"{base_url}/user/1/summary")
        if response.status_code == 200:
            summary = response.json().get("data", {})
            logger.info(f"用户学习摘要: {summary}")
        else:
            logger.error(f"获取用户学习摘要失败: {response.status_code}")

        logger.info("学习系统API测试完成")

    except Exception as e:
        logger.error(f"学习系统API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    success = initialize_learning_system()
    if success:
        print("\n学习系统初始化成功！")
        print("您可以通过以下API访问学习系统:")
        print("- 获取课程列表: GET /api/learning/courses")
        print("- 获取课程详情: GET /api/learning/courses/<course_id>")
        print("- 获取课程章节: GET /api/learning/courses/<course_id>/lessons")
        print("- 获取用户进度: GET /api/learning/user/<user_id>/progress")
        print("- 更新用户进度: POST /api/learning/user/progress")
        print("- 获取用户学习摘要: GET /api/learning/user/<user_id>/summary")
        print("- 获取课程推荐: GET /api/learning/user/<user_id>/recommendations")

        # 询问是否测试API
        test_api = input("\n是否测试学习系统API？(y/n): ")
        if test_api.lower() == 'y':
            test_learning_system_api()
    else:
        print("\n学习系统初始化失败！")
        sys.exit(1)

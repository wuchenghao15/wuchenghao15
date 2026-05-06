#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI知识库测试脚本
测试知识管理、搜索和自动更新等功能

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ai_knowledge_base')

def test_initialization():
    """测试初始化"""
    try:
        logger.info("=" * 60)
        logger.info("测试1: 初始化AI知识库")
        logger.info("=" * 60)
        from app.ai.ai_knowledge_base import ai_knowledge_base

        stats = ai_knowledge_base.get_statistics()
        logger.info(f"知识库初始化成功")
        logger.info(f"知识类别数量: {len(stats['categories'])}")
        logger.info(f"总知识条目: {stats['total_entries']}")
        logger.info(f"知识来源数量: {len(stats['sources_count'])}")

        # 验证类别
        assert 'python' in stats['categories'], "缺少Python类别"
        assert 'flask' in stats['categories'], "缺少Flask类别"
        assert 'git' in stats['categories'], "缺少Git类别"
        assert 'sqlite' in stats['categories'], "缺少SQLite类别"
        assert 'ai' in stats['categories'], "缺少AI类别"

        logger.info("✅ 初始化测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 初始化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_add_knowledge():
    """测试添加知识"""
    try:
        logger.info("测试2: 添加知识")
        logger.info("=" * 60)


        # 测试添加Python知识
        logger.info("\n2.1 添加Python知识")
            'python',
            'Python基础语法',
            'Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。\n\n基本语法包括：\n- 变量定义\n- 数据类型\n- 控制结构\n- 函数定义',
            'https://docs.python.org/3/tutorial/',
            ['python', 'basic', 'syntax']
        )

        # 测试添加Flask知识
        logger.info("\n2.2 添加Flask知识")
        success = ai_knowledge_base.add_knowledge(
            'flask',
            'Flask路由',
            'Flask使用@app.route()装饰器来定义路由。\n\n示例：\n@app.route(\'/\')\ndef index():\n    return \'Hello, World!\'',
            'https://flask.palletsprojects.com/en/2.0.x/quickstart/',
            ['flask', 'routing', 'web']

        # 测试添加Git知识
        logger.info("\n2.3 添加Git知识")
        success = ai_knowledge_base.add_knowledge(
            'git',
            'Git基本命令',
            'Git的基本命令包括：\n- git init\n- git add\n- git commit\n- git push\n- git pull',
            'https://git-scm.com/docs',
            ['git', 'basic', 'commands']
        )
        # 验证添加结果
        stats = ai_knowledge_base.get_statistics()
        logger.info(f"\n添加后总知识条目: {stats['total_entries']}")
        assert stats['total_entries'] >= 3, "知识添加失败"

        logger.info("✅ 添加知识测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 添加知识测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_search_knowledge():
    """测试搜索知识"""
        logger.info("\n" + "=" * 60)
        logger.info("=" * 60)
        from app.ai.ai_knowledge_base import ai_knowledge_base

        # 测试按关键词搜索
        logger.info("\n3.1 按关键词搜索 'Python'")
        logger.info(f"找到 {len(results)} 条结果")
        for result in results:
            logger.info(f"  - {result['title']} (类别: {result['category']})")

        logger.info("\n3.2 按类别搜索 'flask'")
        flask_results = ai_knowledge_base.search_knowledge('路由', category='flask')
        logger.info(f"找到 {len(flask_results)} 条Flask路由相关结果")

        # 测试按标签搜索
        logger.info("\n3.3 按标签搜索 'basic'")
        basic_results = ai_knowledge_base.search_knowledge('基本', tags=['basic'])
        logger.info(f"找到 {len(basic_results)} 条基础相关结果")

        # 验证搜索结果
        assert len(results) > 0, "搜索失败"
        assert len(flask_results) > 0, "按类别搜索失败"

        logger.info("✅ 搜索知识测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 搜索知识测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_get_by_category():
    """测试按类别获取知识"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试4: 按类别获取知识")
        from app.ai.ai_knowledge_base import ai_knowledge_base

        logger.info("\n4.1 获取Python类别知识")
        python_knowledge = ai_knowledge_base.get_knowledge_by_category('python')

        # 测试获取Flask类别知识
        logger.info("\n4.2 获取Flask类别知识")
        flask_knowledge = ai_knowledge_base.get_knowledge_by_category('flask')
        logger.info(f"Flask类别知识数量: {len(flask_knowledge)}")
        # 测试获取Git类别知识
        logger.info("\n4.3 获取Git类别知识")
        git_knowledge = ai_knowledge_base.get_knowledge_by_category('git')
        logger.info(f"Git类别知识数量: {len(git_knowledge)}")

        # 验证结果
        assert len(python_knowledge) > 0, "获取Python知识失败"
        assert len(flask_knowledge) > 0, "获取Flask知识失败"
        assert len(git_knowledge) > 0, "获取Git知识失败"

        logger.info("✅ 按类别获取知识测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 按类别获取知识测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_statistics():
    """测试统计信息"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试5: 统计信息")
        logger.info("=" * 60)
        from app.ai.ai_knowledge_base import ai_knowledge_base


        logger.info(f"总知识条目: {stats['total_entries']}")
        logger.info(f"最后更新时间: {stats['last_updated']}")
        logger.info("\n各类别知识数量:")
        for category, info in stats['categories'].items():
            logger.info(f"  {info['name']}: {info['entry_count']} 条")

        logger.info("\n各类别知识来源数量:")
            logger.info(f"  {category}: {count} 个来源")

        # 验证统计信息
        assert 'total_entries' in stats, "统计信息不完整"
        assert 'categories' in stats, "缺少类别统计"

        logger.info("✅ 统计信息测试通过")
        return True
        logger.error(f"❌ 统计信息测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_learning_history():
    """测试学习历史"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 学习历史")
        logger.info("=" * 60)
        from app.ai.ai_knowledge_base import ai_knowledge_base

        history = ai_knowledge_base.get_learning_history(10)
        logger.info(f"学习历史记录数: {len(history)}")

        for i, entry in enumerate(history[:5]):  # 只显示前5条
            logger.info(f"\n6.{i+1} 历史记录:")
            logger.info(f"  详情: {entry['details']}")

        # 验证学习历史
        assert len(history) > 0, "学习历史为空"
        logger.info("✅ 学习历史测试通过")
    except Exception as e:
        logger.error(f"❌ 学习历史测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_auto_update():
    """测试自动更新知识库"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试7: 自动更新知识库")
        logger.info("=" * 60)
        from app.ai.ai_knowledge_base import ai_knowledge_base

        logger.info("7.1 开始自动更新知识库")
        update_result = ai_knowledge_base.auto_update_knowledge()

        if update_result['success']:
            logger.info(f"  更新成功")
            logger.info(f"  更新类别: {update_result['updated_categories']}")

            if update_result['errors']:
        else:
            logger.error(f"  更新失败: {update_result['errors']}")
            return False

        # 验证更新结果

        logger.info("✅ 自动更新测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 自动更新测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("AI知识库测试套件")
    logger.info("=" * 60)

    results = []

    # 运行所有测试
    results.append(("初始化", test_initialization()))
    results.append(("添加知识", test_add_knowledge()))
    results.append(("搜索知识", test_search_knowledge()))
    results.append(("自动更新", test_auto_update()))

    # 显示测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)

        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")

    # 计算总体通过率
    passed = sum(1 for _, result in results if result)
    total = len(results)
    return all(result for _, result in results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

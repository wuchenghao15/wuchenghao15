#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统AI分配器测试脚本
测试重新给系统指配专业AI，到系统各个层级和功能并完成适配和托管

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ai_system_assigner')

def create_test_ai_profiles():
    """创建测试用的AI档案"""
    return [
        {
            'ai_instance_id': 'ai_web_001',
            'ai_name': 'Web开发专家',
            'ai_type': 'web_specialist',
            'current_skills': ['python_basic', 'python_oop', 'python_web', 'git_basic']
        },
        {
            'ai_name': '老师AI',
            'ai_type': 'teacher_ai',
            'current_skills': ['teaching_basic', 'error_analysis', 'personalized_feedback']
        },
        {
            'ai_type': 'engineer_ai',
            'current_skills': ['code_analysis', 'bug_fixing', 'performance_optimization', 'git_basic']
        },
        {
            'ai_name': 'Git专家',
            'current_skills': ['git_basic', 'git_branching', 'git_workflow', 'git_conflict']
        },
        {
            'ai_name': '通用AI',
            'ai_type': 'general',
        }
    ]

def test_system_structure():
    """测试系统结构"""
    try:
        logger.info("=" * 60)
        logger.info("测试1: 系统结构")
        logger.info("=" * 60)

        from app.ai.ai_system_assigner import ai_system_assigner

        structure = ai_system_assigner.get_system_structure()
        logger.info(f"系统层级数量: {len(structure)}")

        for level_id, level_info in structure.items():
            logger.info(f"  描述: {level_info['description']}")
            logger.info(f"  功能数量: {len(level_info['functions'])}")
            for func in level_info['functions']:
                logger.info(f"    - {func['name']}: {func['description']}")
                logger.info(f"      必需技能: {func['required_skills']}")
                logger.info(f"      首选AI类型: {func['preferred_ai_types']}")

        assert len(structure) >= 6, "系统层级数量不足"

        logger.info("✅ 系统结构测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 系统结构测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_assign_ai_to_system():
    """测试分配AI到系统"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 分配AI到系统")
        logger.info("=" * 60)

        from app.ai.ai_system_assigner import ai_system_assigner
        ai_profiles = create_test_ai_profiles()

            logger.info(f"\n2.1 分配 {ai_profile['ai_name']} 到系统")
            result = ai_system_assigner.assign_ai_to_system(ai_profile)

                logger.info(f"  分配成功")
                logger.info(f"  托管状态: {result['hosting_status']}")

                assignments = result['assignments']
                logger.info(f"  分配到的层级数量: {len(assignments)}")
                for level_id, level_assignments in assignments.items():
                    logger.info(f"    - {level_id}: {len(level_assignments)} 个功能")
                    for assignment in level_assignments[:2]:  # 只显示前2个
                        logger.info(f"      * {assignment['function_name']} (匹配度: {assignment['overall_score']:.2f})")
            else:
                logger.error(f"  分配失败: {result['error']}")

        # 验证分配结果
        assignments = ai_system_assigner.get_ai_assignments()
        assert len(assignments) == len(ai_profiles), "分配数量不匹配"

        logger.info("✅ 分配AI到系统测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 分配AI到系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_hosting_status():
    """测试AI托管状态"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试3: AI托管状态")


        hosting_status = ai_system_assigner.get_ai_hosting_status()
        for ai_id, status in hosting_status.items():
            logger.info(f"\n3.1 AI {ai_id} 托管状态")
            logger.info(f"  状态: {status['status']}")
            logger.info(f"  分配的功能数量: {sum(len(funcs) for funcs in status['assigned_functions'].values())}")

        assert len(hosting_status) > 0, "没有托管的AI"

        return True
    except Exception as e:
        logger.error(f"❌ AI托管状态测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_adapt_ai_to_function():
    """测试适配AI到特定功能"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试4: 适配AI到特定功能")
        logger.info("=" * 60)

        from app.ai.ai_system_assigner import ai_system_assigner
        # 获取已分配的AI
        if not assignments:
            return False

        # 选择一个AI进行测试
        logger.info(f"选择AI: {ai_info['ai_name']} (ID: {ai_id})")

        # 选择一个分配的功能进行适配
        if ai_info['assignments']:
            function_name = ai_info['assignments'][level_id][0]['function_name']

            logger.info(f"\n4.1 适配到 {level_id} 层级的 {function_name} 功能")
            result = ai_system_assigner.adapt_ai_to_function(ai_id, level_id, function_name)

            if result['success']:
                logger.info(f"  适配成功")
                logger.info(f"  适配ID: {result['adaptation_id']}")
                logger.info(f"  状态: {result['status']}")
            else:
                logger.error(f"  适配失败: {result['error']}")

        # 验证适配记录
        adaptation_records = ai_system_assigner.get_adaptation_records()
        assert len(adaptation_records) > 0, "没有适配记录"

        logger.info("✅ 适配AI到特定功能测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 适配AI到特定功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_optimize_assignments():
    """测试优化AI分配"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("=" * 60)

        from app.ai.ai_system_assigner import ai_system_assigner


            logger.error(f"  优化失败: {result['error']}")
            return False

        logger.info(f"  总分配数: {result['total_assignments']}")
        logger.info(f"  状态: {result['status']}")

        logger.info("✅ 优化AI分配测试通过")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def test_ai_distribution():
    """测试AI在系统中的分布情况"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试6: AI系统分布")
        logger.info("=" * 60)

        from app.ai.ai_system_assigner import ai_system_assigner

        assignments = ai_system_assigner.get_ai_assignments()
        # 统计每个层级的AI数量
        level_distribution = {}
        for ai_id, ai_info in assignments.items():
            for level_id in ai_info['assignments']:
                    level_distribution[level_id] = 0
                level_distribution[level_id] += 1
        logger.info("\n6.1 AI在各层级的分布:")
        for level_id, count in level_distribution.items():

        # 统计每个AI分配的功能数量
        logger.info("\n6.2 每个AI分配的功能数量:")
        for ai_id, ai_info in assignments.items():
            logger.info(f"  {ai_info['ai_name']}: {total_functions} 个功能")
        return True
    except Exception as e:
        logger.error(f"❌ AI系统分布测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("系统AI分配器测试套件")
    logger.info("=" * 60)

    results = []

    # 运行所有测试
    results.append(("系统结构", test_system_structure()))
    results.append(("AI托管状态", test_hosting_status()))
    results.append(("适配AI到特定功能", test_adapt_ai_to_function()))
    results.append(("优化AI分配", test_optimize_assignments()))
    results.append(("AI系统分布", test_ai_distribution()))
    # 显示测试结果汇总
    logger.info("测试结果汇总")

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    logger.info(f"\n总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    return all(result for _, result in results)

    sys.exit(0 if success else 1)

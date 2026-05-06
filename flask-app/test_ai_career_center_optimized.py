#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版AI职业介绍所测试脚本
测试数据库持久化、技能学习路径、性能评估等功能

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ai_career_center_optimized')

def test_initialization():
    """测试初始化"""
    try:
        logger.info("=" * 60)
        logger.info("测试1: 初始化AI职业介绍所")
        logger.info("=" * 60)
        from app.ai.ai_career_center_optimized import ai_career_center_optimized

        logger.info(f"技能数量: {len(ai_career_center_optimized.skills_database)}")
        logger.info(f"职业路径数量: {len(ai_career_center_optimized.career_paths)}")
        logger.info(f"学习路径数量: {len(ai_career_center_optimized.learning_paths)}")

        # 验证默认数据
        assert len(ai_career_center_optimized.skills_database) >= 15, "技能数量不足"
        assert len(ai_career_center_optimized.career_paths) >= 10, "职业路径数量不足"
        assert len(ai_career_center_optimized.learning_paths) >= 4, "学习路径数量不足"

        logger.info("✅ 初始化测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 初始化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_search():
    """测试技能搜索"""
    try:
        logger.info("测试2: 技能搜索功能")
        logger.info("=" * 60)


        # 按关键词搜索
        logger.info("\n2.1 按关键词搜索 'Git'")
        logger.info(f"找到 {len(git_skills)} 个Git相关技能")
        for skill in git_skills:
            logger.info(f"  - {skill['skill_name']} ({skill['level']})")

        # 按类别搜索
        logger.info("\n2.2 按类别搜索 '教学'")
        teaching_skills = ai_career_center_optimized.search_skills(category='教学')
        logger.info(f"找到 {len(teaching_skills)} 个教学技能")

        # 按级别搜索
        logger.info("\n2.3 按级别搜索 '高级'")
        advanced_skills = ai_career_center_optimized.search_skills(level='高级')
        logger.info(f"找到 {len(advanced_skills)} 个高级技能")

        # 组合搜索
        logger.info("\n2.4 组合搜索 (关键词='Python', 级别='高级')")
        python_advanced = ai_career_center_optimized.search_skills(keyword='Python', level='高级')
        logger.info(f"找到 {len(python_advanced)} 个Python高级技能")

        assert len(git_skills) >= 6, "Git技能数量不足"
        assert len(teaching_skills) >= 3, "教学技能数量不足"

        logger.info("✅ 技能搜索测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 技能搜索测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    """测试职业路径搜索"""
    try:
        logger.info("=" * 60)

        from app.ai.ai_career_center_optimized import ai_career_center_optimized
        # 按关键词搜索
        logger.info("\n3.1 按关键词搜索 '专家'")
        expert_careers = ai_career_center_optimized.search_career_paths(keyword='专家')
        logger.info(f"找到 {len(expert_careers)} 个专家职业")
            logger.info(f"  - {career['path_name']}")

        # 按技能搜索
        logger.info("\n3.2 按技能搜索 (需要 'git_basic')")
        git_careers = ai_career_center_optimized.search_career_paths(has_skill='git_basic')
        logger.info(f"找到 {len(git_careers)} 个需要git_basic的职业")
        assert len(expert_careers) >= 2, "专家职业数量不足"

        logger.info("✅ 职业路径搜索测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 职业路径搜索测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_registration_and_empowerment():
    try:
        logger.info("测试4: AI注册和赋能")

        from app.ai.ai_career_center_optimized import ai_career_center_optimized

        success = ai_career_center_optimized.register_ai(
            'test_ai_001',
            'general',
            '测试AI一号',
        )
        logger.info("✅ AI注册成功")

        # 赋能AI（测试前置技能检查）
        logger.info("\n4.2 尝试赋能高级技能（应该失败，缺少前置技能）")
        result = ai_career_center_optimized.empower_ai('test_ai_001', ['python_web'])
        logger.info(f"赋能结果: {result}")
        assert len(result['prerequisite_issues']) > 0, "应该检测到前置技能问题"
        logger.info("✅ 前置技能检查正常")

        # 逐步赋能
        logger.info("\n4.3 逐步赋能")
        result1 = ai_career_center_optimized.empower_ai('test_ai_001', ['python_oop'])
        logger.info(f"第一步赋能: {result1}")

        result2 = ai_career_center_optimized.empower_ai('test_ai_001', ['python_web'])
        logger.info(f"第二步赋能: {result2}")

        assert len(result1['added_skills']) > 0, "第一步赋能应该成功"
        assert len(result2['added_skills']) > 0, "第二步赋能应该成功"

        logger.info("✅ AI赋能测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ AI注册和赋能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_learning_path_tracking():
    """测试学习路径跟踪"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("=" * 60)
        from app.ai.ai_career_center_optimized import ai_career_center_optimized

        # 先注册一个AI
            'git_specialist',
            'Git学习AI',
            ['git_basic']
        )
        logger.info("\n5.1 初始学习进度")
        logger.info(f"进度: {progress1['progress_percentage']:.1f}%")
        logger.info(f"已完成: {progress1['completed_skills']}/{progress1['total_skills']}")
        logger.info(f"待完成: {progress1['pending_skills']}")

        # 继续学习
        logger.info("\n5.2 继续学习，添加更多技能")
        ai_career_center_optimized.empower_ai('test_ai_002', ['git_branching', 'git_workflow'])

        # 再次跟踪进度
        progress2 = ai_career_center_optimized.track_learning_progress('test_ai_002', 'learn_git_expert')
        logger.info(f"新进度: {progress2['progress_percentage']:.1f}%")
        logger.info(f"已完成: {progress2['completed_skills']}/{progress2['total_skills']}")

        assert progress2['progress_percentage'] > progress1['progress_percentage'], "进度应该增加"

        logger.info("✅ 学习路径跟踪测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 学习路径跟踪测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_recording():
    """测试性能记录和评估"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 性能记录和评估")

        from app.ai.ai_career_center_optimized import ai_career_center_optimized

        # 先注册一个AI并添加技能
            'test_ai_003',
            'engineer',
            ['code_analysis']
        )
        logger.info("\n6.1 记录性能表现")
        performances = [
            ('code_analysis', 0.75, 'code_review'),
            ('code_analysis', 0.85, 'code_review'),
        ]
        for skill_id, score, task_type in performances:
            success = ai_career_center_optimized.record_performance(
                'test_ai_003',
                skill_id,
                score,
                task_type
            )

        # 获取性能总结
        logger.info("\n6.2 获取性能总结")
        summary = ai_career_center_optimized.get_ai_performance_summary('test_ai_003')
        logger.info(f"总记录数: {summary['total_records']}")
        logger.info(f"整体平均分: {summary['overall_average']:.2f}")

        for skill_id, stats in summary['skill_summary'].items():
            logger.info(f"  {skill_id}: 平均分={stats['average_score']:.2f}, 练习次数={stats['practice_count']}")

        assert summary['total_records'] == 3, "性能记录数量不对"

        logger.info("✅ 性能记录和评估测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 性能记录和评估测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_statistics():
    """测试统计功能"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试7: 统计功能")
        logger.info("=" * 60)



        logger.info(f"总技能数: {stats['total_skills']}")
        logger.info(f"总职业路径: {stats['total_career_paths']}")
        logger.info(f"总AI档案: {stats['total_ai_profiles']}")
        logger.info(f"总学习路径: {stats['total_learning_paths']}")
        logger.info("\n技能按类别分布:")
        for category, count in stats['skills_by_category'].items():
            logger.info(f"  {category}: {count}")

        logger.info("\nAI按类型分布:")
            logger.info(f"  {ai_type}: {count}")

        assert 'skills_by_category' in stats, "缺少技能分类统计"

        logger.info("✅ 统计功能测试通过")
        return True
        logger.error(f"❌ 统计功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("优化版AI职业介绍所测试套件")
    logger.info("=" * 60)

    results = []

    # 运行所有测试
    results.append(("初始化", test_initialization()))
    results.append(("技能搜索", test_skill_search()))
    results.append(("职业路径搜索", test_career_path_search()))
    results.append(("AI注册和赋能", test_ai_registration_and_empowerment()))
    results.append(("性能记录和评估", test_performance_recording()))

    # 显示测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    logger.info(f"\n总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")


if __name__ == '__main__':
    success = main()

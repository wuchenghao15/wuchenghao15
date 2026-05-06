#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI员工审评系统测试脚本
测试绩效评估、改进计划和职业发展计划等功能

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ai_performance_review')

def test_review_criteria():
    """测试审评标准"""
    try:
        logger.info("=" * 60)
        logger.info("测试1: 审评标准")
        logger.info("=" * 60)
        from app.ai.ai_performance_review import ai_performance_review_system

        criteria = ai_performance_review_system.get_review_criteria()
        logger.info(f"审评标准数量: {len(criteria)}")

        for category, category_data in criteria.items():
            logger.info(f"\n分类: {category_data['name']} (权重: {category_data['weight']})")
            for sub_criterion, sub_data in category_data['sub_criteria'].items():
                logger.info(f"  - {sub_data['name']} (权重: {sub_data['weight']})")

        assert len(criteria) == 4, "审评标准数量不对"

        logger.info("✅ 审评标准测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 审评标准测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_create_performance_review():
    """测试创建绩效审评"""
    try:
        logger.info("测试2: 创建绩效审评")
        logger.info("=" * 60)


        # 测试数据
        ai_instance_id = 'ai_web_001'
        review_period = '2026-Q2'

        # 评分数据
        ratings = {
            'performance': {
                'task_completion': 4.5,
                'quality': 4.0,
                'efficiency': 3.5
            },
            'skills': {
                'technical_skills': 4.2,
                'soft_skills': 3.8,
                'learning_ability': 4.0
            },
            'teamwork': {
                'collaboration': 3.5,
                'communication': 3.8
            },
                'problem_solving': 4.0,
                'creativity': 3.5
            }

        # 目标
        goals = [
            {
                'description': '提高代码质量',
                'actions': ['学习代码审查技巧', '使用静态代码分析工具'],
            },
            {
                'description': '提升团队协作能力',
                'actions': ['参加团队建设活动', '改进沟通方式'],
                'deadline': '2026-07-31'
        ]

        # 创建审评
        result = ai_performance_review_system.create_performance_review(
            reviewer_id,
            review_period,
            comments='表现良好，继续努力',
            goals=goals
        )
        if result['success']:
            logger.info(f"  审评创建成功")
            logger.info(f"  审评ID: {result['review_id']}")
            logger.info(f"  总评分: {result['total_score']}")
            logger.info(f"  绩效等级: {result['performance_level']}")
        else:
            logger.error(f"  审评创建失败: {result['error']}")
            return False

        # 验证审评记录
        reviews = ai_performance_review_system.get_all_reviews()
        assert len(reviews) > 0, "没有创建审评记录"

        logger.info("✅ 创建绩效审评测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 创建绩效审评测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
def test_review_history():
    try:
        logger.info("\n" + "=" * 60)

        from app.ai.ai_performance_review import ai_performance_review_system

        history = ai_performance_review_system.get_review_history(ai_instance_id)

        logger.info(f"  审评历史记录数: {len(history)}")

            logger.info(f"  - 审评ID: {review['review_id']}")
            logger.info(f"    期间: {review['review_period']}")
            logger.info(f"    评分: {review['total_score']}")
            logger.info(f"    等级: {review['performance_level']}")

        assert len(history) > 0, "没有审评历史"
        logger.info("✅ 审评历史测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 审评历史测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_trend():
    """测试绩效趋势"""
        logger.info("\n" + "=" * 60)
        logger.info("=" * 60)
        from app.ai.ai_performance_review import ai_performance_review_system

        # 先创建第二个审评记录
        review_period = '2026-Q1'

        # 稍微低一点的评分
        ratings = {
                'task_completion': 4.0,
                'quality': 3.5,
                'efficiency': 3.0
            },
            'skills': {
                'technical_skills': 3.8,
                'soft_skills': 3.5,
                'learning_ability': 3.6
            },
            'teamwork': {
                'collaboration': 3.0,
            },
            'innovation': {
                'creativity': 3.0
            }
        }

        ai_performance_review_system.create_performance_review(
            reviewer_id,
            review_period,
            ratings,
            comments='表现一般，需要改进'
        # 获取绩效趋势
        trend = ai_performance_review_system.get_performance_trend(ai_instance_id)

        if trend['success']:
            logger.info(f"  最高评分: {trend['highest_score']}")
            logger.info(f"  最低评分: {trend['lowest_score']}")
        else:
            logger.error(f"  获取绩效趋势失败: {trend['error']}")
            return False
        assert trend['trend'] == 'improving', "绩效应该有提升趋势"

        logger.info("✅ 绩效趋势测试通过")
        return True
        logger.error(f"❌ 绩效趋势测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
def test_performance_report():
    """测试绩效报告"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试5: 绩效报告")


        ai_instance_id = 'ai_web_001'
        report = ai_performance_review_system.generate_performance_report(ai_instance_id)
            logger.info(f"  报告日期: {report['report_date']}")
            logger.info(f"  最新审评评分: {report['latest_review']['total_score']}")
            for recommendation in report['recommendations']:
                logger.info(f"    - {recommendation}")
        else:
            logger.error(f"  报告生成失败: {report['error']}")
            return False

        logger.info("✅ 绩效报告测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 绩效报告测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    """测试改进计划"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 改进计划")

        from app.ai.ai_performance_review import ai_performance_review_system

        # 获取改进计划
        logger.info(f"  改进计划数量: {len(improvement_plans)}")

            review_id = list(improvement_plans.keys())[0]
            plan = improvement_plans[review_id]
            logger.info(f"  改进计划ID: {review_id}")
            logger.info(f"  目标数量: {len(plan['goals'])}")
            logger.info("  行动项:")
            for item in plan['action_items']:
                for action in item['actions']:

            # 更新改进计划
            progress = {
                'overall_progress': 0.3,
                'action_item_progress': [
                    {'goal': plan['action_items'][0]['goal'], 'progress': 0.5},
                    {'goal': plan['action_items'][1]['goal'], 'progress': 0.1}
                ]
            }

            update_result = ai_performance_review_system.update_improvement_plan(review_id, progress)
            if update_result['success']:
                logger.info("  改进计划更新成功")
            else:
                logger.error(f"  改进计划更新失败: {update_result['error']}")
                return False

        logger.info("✅ 改进计划测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 改进计划测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_career_development_plan():
    """测试职业发展计划"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试7: 职业发展计划")

        from app.ai.ai_performance_review import ai_performance_review_system

        ai_instance_id = 'ai_web_001'

        # 职业目标
        career_goals = [
                'target_date': '2027-04-01'
            },
            {
                'description': '领导一个开发团队',
                'target_date': '2028-04-01'
        ]

        skills_to_develop = ['python_web', 'git_workflow', 'leadership', 'project_management']

        # 创建职业发展计划
        result = ai_performance_review_system.create_career_development_plan(
            career_goals,
            skills_to_develop
        )
        if result['success']:
            logger.info(f"  职业发展计划创建成功")
            logger.info(f"  计划ID: {result['plan_id']}")
            logger.error(f"  职业发展计划创建失败: {result['error']}")
            return False

        # 验证计划
        career_plans = ai_performance_review_system.get_all_career_plans()
        assert len(career_plans) > 0, "没有创建职业发展计划"

        logger.info("✅ 职业发展计划测试通过")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("AI员工审评系统测试套件")
    logger.info("=" * 60)

    results = []

    # 运行所有测试
    results.append(("创建绩效审评", test_create_performance_review()))
    results.append(("审评历史", test_review_history()))
    results.append(("绩效报告", test_performance_report()))
    results.append(("职业发展计划", test_career_development_plan()))

    # 显示测试结果汇总
    logger.info("测试结果汇总")
    logger.info("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
    # 计算总体通过率
    total = len(results)
    logger.info(f"\n总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")

if __name__ == '__main__':
    sys.exit(0 if success else 1)

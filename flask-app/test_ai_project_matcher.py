#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI项目匹配器测试脚本
测试动态匹配专业AI到项目各个领域和功能
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ai_project_matcher')

def create_test_ai_profiles():
    """创建测试用的AI档案"""
    return [
        {
            'ai_instance_id': 'test_ai_001',
            'ai_name': 'Web开发AI',
            'ai_type': 'general',
            'current_skills': ['python_basic', 'python_oop', 'python_web', 'git_basic']
        },
        {
            'ai_instance_id': 'test_ai_002',
            'ai_name': '老师AI',
            'ai_type': 'teacher_ai',
            'current_skills': ['teaching_basic', 'error_analysis', 'personalized_feedback']
        },
        {
            'ai_instance_id': 'test_ai_003',
            'ai_name': '工程师AI',
            'ai_type': 'engineer_ai',
            'current_skills': ['code_analysis', 'bug_fixing', 'performance_optimization']
        },
        {
            'ai_instance_id': 'test_ai_004',
            'ai_name': 'Git AI',
            'ai_type': 'git_ai',
            'current_skills': ['git_basic', 'git_branching', 'git_workflow', 'git_conflict']
        },
        {
            'ai_instance_id': 'test_ai_005',
            'ai_name': '新手AI',
            'ai_type': 'general',
            'current_skills': ['python_basic']
        }
    ]

def test_get_project_domains():
    """测试获取项目领域"""
    try:
        logger.info("=" * 60)
        logger.info("测试1: 获取项目领域")
        logger.info("=" * 60)
        
        from app.ai.ai_project_matcher import ai_project_matcher
        
        domains = ai_project_matcher.get_project_domains()
        logger.info(f"找到 {len(domains)} 个项目领域")
        
        for domain in domains:
            logger.info(f"\n领域: {domain['name']} (ID: {domain['domain_id']})")
            logger.info(f"  必需技能: {domain['required_skills']}")
            logger.info(f"  推荐技能: {domain['recommended_skills']}")
            logger.info(f"  功能: {[func['name'] for func in domain['functions']]}")
        
        assert len(domains) >= 4, "项目领域数量不足"
        
        logger.info("✅ 获取项目领域测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 获取项目领域测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_match_ai_to_project():
    """测试匹配AI到项目"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 匹配AI到项目")
        logger.info("=" * 60)
        
        from app.ai.ai_project_matcher import ai_project_matcher
        ai_profiles = create_test_ai_profiles()
        
        # 测试Web开发领域
        logger.info("\n2.1 测试Web开发领域匹配")
        web_ai = ai_profiles[0]
        web_match = ai_project_matcher.match_ai_to_project(web_ai, 'web_development')
        logger.info(f"AI: {web_ai['ai_name']}")
        logger.info(f"匹配度: {web_match['overall_match_score']:.2f}")
        logger.info(f"技能匹配: {web_match['skill_match']}")
        
        # 测试教育领域
        logger.info("\n2.2 测试教育领域匹配")
        teacher_ai = ai_profiles[1]
        education_match = ai_project_matcher.match_ai_to_project(teacher_ai, 'education')
        logger.info(f"AI: {teacher_ai['ai_name']}")
        logger.info(f"匹配度: {education_match['overall_match_score']:.2f}")
        
        # 测试软件工程领域
        logger.info("\n2.3 测试软件工程领域匹配")
        engineer_ai = ai_profiles[2]
        engineering_match = ai_project_matcher.match_ai_to_project(engineer_ai, 'software_engineering')
        logger.info(f"AI: {engineer_ai['ai_name']}")
        logger.info(f"匹配度: {engineering_match['overall_match_score']:.2f}")
        
        # 测试版本控制领域
        logger.info("\n2.4 测试版本控制领域匹配")
        git_ai = ai_profiles[3]
        git_match = ai_project_matcher.match_ai_to_project(git_ai, 'version_control')
        logger.info(f"AI: {git_ai['ai_name']}")
        logger.info(f"匹配度: {git_match['overall_match_score']:.2f}")
        
        # 测试新手AI（应该匹配度较低）
        logger.info("\n2.5 测试新手AI匹配")
        new_ai = ai_profiles[4]
        new_match = ai_project_matcher.match_ai_to_project(new_ai, 'web_development')
        logger.info(f"AI: {new_ai['ai_name']}")
        logger.info(f"匹配度: {new_match['overall_match_score']:.2f}")
        
        # 验证匹配度
        assert web_match['overall_match_score'] >= 0.8, "Web开发AI匹配度应该很高"
        assert education_match['overall_match_score'] >= 0.8, "老师AI匹配度应该很高"
        assert engineering_match['overall_match_score'] >= 0.8, "工程师AI匹配度应该很高"
        assert git_match['overall_match_score'] >= 0.8, "Git AI匹配度应该很高"
        assert new_match['overall_match_score'] < 0.5, "新手AI匹配度应该较低"
        
        logger.info("✅ 匹配AI到项目测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 匹配AI到项目测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_find_best_ai():
    """测试寻找最佳AI"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试3: 寻找最佳AI")
        logger.info("=" * 60)
        
        from app.ai.ai_project_matcher import ai_project_matcher
        ai_profiles = create_test_ai_profiles()
        
        # 为Web开发领域寻找最佳AI
        logger.info("\n3.1 为Web开发领域寻找最佳AI")
        web_result = ai_project_matcher.find_best_ai_for_project('web_development', ai_profiles=ai_profiles)
        logger.info(f"最佳匹配: {web_result['best_match']['ai_name']} (匹配度: {web_result['best_match']['overall_match_score']:.2f})")
        
        # 为教育领域寻找最佳AI
        logger.info("\n3.2 为教育领域寻找最佳AI")
        education_result = ai_project_matcher.find_best_ai_for_project('education', ai_profiles=ai_profiles)
        logger.info(f"最佳匹配: {education_result['best_match']['ai_name']} (匹配度: {education_result['best_match']['overall_match_score']:.2f})")
        
        # 为软件工程领域寻找最佳AI
        logger.info("\n3.3 为软件工程领域寻找最佳AI")
        engineering_result = ai_project_matcher.find_best_ai_for_project('software_engineering', ai_profiles=ai_profiles)
        logger.info(f"最佳匹配: {engineering_result['best_match']['ai_name']} (匹配度: {engineering_result['best_match']['overall_match_score']:.2f})")
        
        # 为版本控制领域寻找最佳AI
        logger.info("\n3.4 为版本控制领域寻找最佳AI")
        git_result = ai_project_matcher.find_best_ai_for_project('version_control', ai_profiles=ai_profiles)
        logger.info(f"最佳匹配: {git_result['best_match']['ai_name']} (匹配度: {git_result['best_match']['overall_match_score']:.2f})")
        
        # 验证最佳匹配
        assert web_result['best_match']['ai_name'] == 'Web开发AI', "Web开发领域应该匹配Web开发AI"
        assert education_result['best_match']['ai_name'] == '老师AI', "教育领域应该匹配老师AI"
        assert engineering_result['best_match']['ai_name'] == '工程师AI', "软件工程领域应该匹配工程师AI"
        assert git_result['best_match']['ai_name'] == 'Git AI', "版本控制领域应该匹配Git AI"
        
        logger.info("✅ 寻找最佳AI测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 寻找最佳AI测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_gaps():
    """测试技能差距分析"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试4: 技能差距分析")
        logger.info("=" * 60)
        
        from app.ai.ai_project_matcher import ai_project_matcher
        ai_profiles = create_test_ai_profiles()
        
        # 分析新手AI的技能差距
        logger.info("\n4.1 分析新手AI在Web开发领域的技能差距")
        new_ai = ai_profiles[4]
        skill_gaps = ai_project_matcher.get_skill_gaps(new_ai, 'web_development')
        logger.info(f"AI: {new_ai['ai_name']}")
        logger.info(f"缺失的必需技能: {skill_gaps['skill_gaps']['required']['missing']}")
        logger.info(f"缺失的推荐技能: {skill_gaps['skill_gaps']['recommended']['missing']}")
        
        # 分析Web开发AI的技能差距（应该很小）
        logger.info("\n4.2 分析Web开发AI在Web开发领域的技能差距")
        web_ai = ai_profiles[0]
        web_gaps = ai_project_matcher.get_skill_gaps(web_ai, 'web_development')
        logger.info(f"AI: {web_ai['ai_name']}")
        logger.info(f"缺失的必需技能: {web_gaps['skill_gaps']['required']['missing']}")
        logger.info(f"缺失的推荐技能: {web_gaps['skill_gaps']['recommended']['missing']}")
        
        # 验证技能差距
        assert len(skill_gaps['skill_gaps']['required']['missing']) > 0, "新手AI应该有技能差距"
        assert len(web_gaps['skill_gaps']['required']['missing']) == 0, "Web开发AI不应该缺少必需技能"
        
        logger.info("✅ 技能差距分析测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 技能差距分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_development_plan():
    """测试技能发展计划"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试5: 技能发展计划")
        logger.info("=" * 60)
        
        from app.ai.ai_project_matcher import ai_project_matcher
        ai_profiles = create_test_ai_profiles()
        
        # 为新手AI生成技能发展计划
        logger.info("\n5.1 为新手AI生成Web开发技能发展计划")
        new_ai = ai_profiles[4]
        plan = ai_project_matcher.generate_skill_development_plan(new_ai, 'web_development')
        logger.info(f"AI: {new_ai['ai_name']}")
        logger.info(f"总技能数: {plan['total_skills_to_learn']}")
        logger.info("发展计划:")
        for item in plan['development_plan']:
            logger.info(f"  - {item['skill_id']} (优先级: {item['priority']}, 类型: {item['type']})")
        
        # 验证计划
        assert plan['total_skills_to_learn'] > 0, "应该生成发展计划"
        assert len([item for item in plan['development_plan'] if item['priority'] == 'high']) > 0, "应该有高优先级技能"
        
        logger.info("✅ 技能发展计划测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 技能发展计划测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_function_specific_matching():
    """测试特定功能的匹配"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 特定功能匹配")
        logger.info("=" * 60)
        
        from app.ai.ai_project_matcher import ai_project_matcher
        ai_profiles = create_test_ai_profiles()
        
        # 测试Web开发中的后端开发功能
        logger.info("\n6.1 测试Web开发中的后端开发功能匹配")
        web_ai = ai_profiles[0]
        backend_match = ai_project_matcher.match_ai_to_project(
            web_ai, 'web_development', '后端开发'
        )
        logger.info(f"AI: {web_ai['ai_name']}")
        logger.info(f"功能匹配度: {backend_match['function_matches'][0]['match_score']:.2f}")
        
        # 测试教育领域中的个性化教学功能
        logger.info("\n6.2 测试教育领域中的个性化教学功能匹配")
        teacher_ai = ai_profiles[1]
        teaching_match = ai_project_matcher.match_ai_to_project(
            teacher_ai, 'education', '个性化教学'
        )
        logger.info(f"AI: {teacher_ai['ai_name']}")
        logger.info(f"功能匹配度: {teaching_match['function_matches'][0]['match_score']:.2f}")
        
        # 验证功能匹配
        assert backend_match['function_matches'][0]['match_score'] >= 0.8, "后端开发匹配度应该很高"
        assert teaching_match['function_matches'][0]['match_score'] >= 0.8, "个性化教学匹配度应该很高"
        
        logger.info("✅ 特定功能匹配测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 特定功能匹配测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("AI项目匹配器测试套件")
    logger.info("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("获取项目领域", test_get_project_domains()))
    results.append(("匹配AI到项目", test_match_ai_to_project()))
    results.append(("寻找最佳AI", test_find_best_ai()))
    results.append(("技能差距分析", test_skill_gaps()))
    results.append(("技能发展计划", test_skill_development_plan()))
    results.append(("特定功能匹配", test_function_specific_matching()))
    
    # 显示测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    # 计算总体通过率
    passed = sum(1 for _, result in results if result)
    total = len(results)
    logger.info(f"\n总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return all(result for _, result in results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

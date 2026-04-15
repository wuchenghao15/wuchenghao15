#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git AI功能测试脚本
测试Git AI模块、Git管理器和AI职业介绍所的集成
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_git_ai')

def test_git_manager():
    """测试Git管理器"""
    try:
        logger.info("=" * 60)
        logger.info("测试Git管理器")
        logger.info("=" * 60)
        
        from app.services.git_manager import git_manager
        
        # 测试仓库状态
        logger.info("\n1. 测试仓库状态检查...")
        is_repo = git_manager._is_git_repo()
        logger.info(f"当前目录是否为Git仓库: {is_repo}")
        
        # 测试获取系统版本
        logger.info("\n2. 测试获取系统版本...")
        version_info = git_manager.get_system_version()
        logger.info(f"系统版本信息: {version_info}")
        
        # 测试查看仓库状态
        logger.info("\n3. 测试查看仓库状态...")
        status = git_manager.status()
        logger.info(f"仓库状态: {status.get('stdout', '').strip()[:200]}...")
        
        logger.info("\n✅ Git管理器测试完成")
        return True
    except Exception as e:
        logger.error(f"❌ Git管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_git_ai():
    """测试Git AI"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试Git AI")
        logger.info("=" * 60)
        
        from app.ai.git_ai import git_ai
        
        logger.info(f"\nGit AI实例ID: {git_ai.instance_id}")
        logger.info(f"Git AI名称: {git_ai.name}")
        logger.info(f"Git AI职责: {git_ai.responsibilities}")
        
        # 测试分析Git状态
        logger.info("\n1. 测试分析Git状态...")
        status_analysis = git_ai.analyze_git_status()
        logger.info(f"Git状态分析: {status_analysis}")
        
        # 测试分析分支策略
        logger.info("\n2. 测试分析分支策略...")
        branch_analysis = git_ai.analyze_branch_strategy()
        logger.info(f"分支策略分析: {branch_analysis}")
        
        # 测试冲突检测
        logger.info("\n3. 测试冲突检测...")
        conflict_analysis = git_ai.detect_and_suggest_conflicts()
        logger.info(f"冲突分析: {conflict_analysis}")
        
        # 测试代码变更分析
        logger.info("\n4. 测试代码变更分析...")
        code_analysis = git_ai.analyze_code_changes()
        logger.info(f"代码变更分析: {code_analysis}")
        
        logger.info("\n✅ Git AI测试完成")
        return True
    except Exception as e:
        logger.error(f"❌ Git AI测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_career_center_git_integration():
    """测试AI职业介绍所的Git集成"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试AI职业介绍所Git集成")
        logger.info("=" * 60)
        
        from app.ai.ai_career_center import ai_career_center
        
        # 测试Git技能
        logger.info("\n1. 检查Git技能...")
        git_skills = [
            skill for skill_id, skill in ai_career_center.skills_database.items()
            if skill.get('category') == 'Git'
        ]
        logger.info(f"Git技能数量: {len(git_skills)}")
        for skill in git_skills:
            logger.info(f"  - {skill['skill_name']} ({skill['level']})")
        
        # 测试Git职业路径
        logger.info("\n2. 检查Git职业路径...")
        git_careers = [
            path for path_id, path in ai_career_center.career_paths.items()
            if 'git' in path_id.lower() or 'Git' in path['path_name']
        ]
        logger.info(f"Git职业路径数量: {len(git_careers)}")
        for career in git_careers:
            logger.info(f"  - {career['path_name']}: {career['description']}")
        
        # 测试注册Git AI
        logger.info("\n3. 注册Git AI到职业介绍所...")
        ai_career_center.register_ai(
            'git_ai_test',
            'git',
            ['git_basic', 'git_branching', 'git_workflow'],
            'git_expert'
        )
        logger.info("Git AI注册成功")
        
        # 测试获取职业建议
        logger.info("\n4. 获取Git AI职业建议...")
        recommendations = ai_career_center.get_ai_career_recommendations('git_ai_test')
        logger.info(f"职业建议数量: {len(recommendations)}")
        for rec in recommendations:
            logger.info(f"  - {rec['path_name']} (匹配度: {rec['match_score']:.2f})")
        
        # 测试提取AI知识
        logger.info("\n5. 提取Git AI知识...")
        knowledge = ai_career_center.extract_ai_knowledge('git_ai_test')
        logger.info(f"提取的知识: {knowledge}")
        
        logger.info("\n✅ AI职业介绍所Git集成测试完成")
        return True
    except Exception as e:
        logger.error(f"❌ AI职业介绍所Git集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("Git AI系统测试")
    logger.info("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("Git管理器", test_git_manager()))
    results.append(("Git AI", test_git_ai()))
    results.append(("AI职业介绍所Git集成", test_ai_career_center_git_integration()))
    
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

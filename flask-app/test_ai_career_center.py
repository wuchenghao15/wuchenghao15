#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI职业介绍所功能
"""

import logging
from app.ai.ai_career_center import ai_career_center

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_ai_career_center')

def test_ai_career_center():
    """测试AI职业介绍所功能"""
    try:
        logger.info("开始测试AI职业介绍所...")
        
        # 添加技能
        logger.info("\n1. 添加技能...")
        ai_career_center.add_skill('skill_1', 'Python编程', 'Python语言编程技能', '编程', '高级')
        ai_career_center.add_skill('skill_2', 'Flask框架', 'Flask Web框架开发', '编程', '中级')
        ai_career_center.add_skill('skill_3', '数据库设计', '数据库设计与优化', '数据库', '中级')
        ai_career_center.add_skill('skill_4', '网络安全', '网络安全防护', '安全', '高级')
        ai_career_center.add_skill('skill_5', 'AI算法', '人工智能算法设计', 'AI', '高级')
        
        # 添加职业路径
        logger.info("\n2. 添加职业路径...")
        ai_career_center.add_career_path('path_1', 'Web开发者', ['skill_1', 'skill_2', 'skill_3'], 'Web应用开发')
        ai_career_center.add_career_path('path_2', 'AI工程师', ['skill_1', 'skill_5', 'skill_3'], '人工智能开发')
        ai_career_center.add_career_path('path_3', '安全专家', ['skill_1', 'skill_4'], '网络安全防护')
        
        # 注册AI
        logger.info("\n3. 注册AI...")
        ai_career_center.register_ai('ai_1', 'general', ['skill_1', 'skill_2'])
        ai_career_center.register_ai('ai_2', 'ai_specialist', ['skill_1', 'skill_5'])
        
        # 赋能AI
        logger.info("\n4. 赋能AI...")
        success = ai_career_center.empower_ai('ai_1', ['skill_3'])
        logger.info(f"赋能AI结果: {success}")
        
        # 转岗AI
        logger.info("\n5. 转岗AI...")
        success = ai_career_center.transfer_ai_career('ai_1', 'path_1')
        logger.info(f"转岗AI结果: {success}")
        
        # 提取AI知识
        logger.info("\n6. 提取AI知识...")
        knowledge = ai_career_center.extract_ai_knowledge('ai_1')
        logger.info(f"提取的知识: {knowledge}")
        
        # 学习知识库
        logger.info("\n7. 学习知识库...")
        success = ai_career_center.learn_knowledge_base('ai_2', 'kb_1', ['resource_1', 'resource_2'])
        logger.info(f"学习知识库结果: {success}")
        
        # 维护AI
        logger.info("\n8. 维护AI...")
        success = ai_career_center.maintain_ai('ai_1', 'performance_optimization', {'cpu': '优化', 'memory': '清理'})
        logger.info(f"维护AI结果: {success}")
        
        # 获取职业建议
        logger.info("\n9. 获取职业建议...")
        recommendations = ai_career_center.get_ai_career_recommendations('ai_2')
        for rec in recommendations:
            logger.info(f"推荐职业: {rec['path_name']} (匹配度: {rec['match_score']})")
        
        # 获取技能差距
        logger.info("\n10. 获取技能差距...")
        skill_gap = ai_career_center.get_ai_skill_gap('ai_2', 'path_2')
        logger.info(f"技能差距: {skill_gap}")
        
        logger.info("\nAI职业介绍所测试完成！")
        return True
    except Exception as e:
        logger.error(f"测试AI职业介绍所时出错: {str(e)}")
        return False

if __name__ == '__main__':
    test_ai_career_center()
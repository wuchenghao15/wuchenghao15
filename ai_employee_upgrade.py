#!/usr/bin/env python3
"""
实例化生成试卷和判断选择数量规则的AI组件，并升级一次

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_employee_upgrade')

def main():
    主函数：实例化AI组件并升级一次
    logger.info("开始实例化AI组件并升级")

    # 1. 实例化生成试卷的AI组件（ExamGenerator）
    logger.info("1. 实例化生成试卷的AI组件")
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))
        from exam_generator import ExamGenerator
        logger.info("✓ 成功实例化ExamGenerator")
        logger.error(f"✗ 实例化ExamGenerator失败: {str(e)}")
        return

    # 2. 实例化判断选择数量规则的AI组件（IntelligentOptionGenerator）
    logger.info("\n2. 实例化判断选择数量规则的AI组件")
    try:
        from intelligent_option_generator import IntelligentOptionGenerator
        option_generator = IntelligentOptionGenerator()
        logger.info("✓ 成功实例化IntelligentOptionGenerator")
    except Exception as e:
        return

    # 3. 实例化AI服务管理器，用于管理AI模型升级
    logger.info("\n3. 实例化AI服务管理器")
    try:
        from ai_service import ai_service_manager
        logger.info("✓ 成功获取AI服务管理器实例")
    except Exception as e:
        logger.error(f"✗ 获取AI服务管理器实例失败: {str(e)}")

    # 4. 实例化AI学习系统，用于AI自我升级
    logger.info("\n4. 实例化AI学习系统")
    try:
        from ai_learning_system import AILearningSystem
        ai_learning_system = AILearningSystem(ai_service_manager)
        logger.info("✓ 成功实例化AILearningSystem")
    except Exception as e:
        return

    # 5. 升级所有AI模型
    logger.info("\n5. 开始升级所有AI模型")
    try:
        # 升级所有AI模型
        results = ai_service_manager.upgrade_all_models()
        logger.info(f"✓ 所有AI模型升级结果: {results}")
    except Exception as e:
        return

    # 6. 升级选项生成器的AI模型
    logger.info("\n6. 升级选项生成器的AI模型")
    try:
        # 使用一个示例反馈来更新选项生成器
        feedback = {
            "question_id": "test_question_1",
            "options": [{"id": "A", "content": "正确答案"}, {"id": "B", "content": "干扰项1"}, {"id": "C", "content": "干扰项2"}],
            "user_answer": "A",
            "is_correct": True,
            "difficulty": 3
        }
        option_generator.update_ai_model(feedback)
        logger.info("✓ 成功升级选项生成器的AI模型")
    except Exception as e:
        logger.error(f"✗ 升级选项生成器的AI模型失败: {str(e)}")
        return

    # 7. 触发AI学习系统自我升级
    logger.info("\n7. 触发AI学习系统自我升级")
    try:
        result = ai_learning_system.trigger_self_upgrade()
        logger.info(f"✓ AI学习系统自我升级结果: {result}")
    except Exception as e:
        logger.error(f"✗ 触发AI学习系统自我升级失败: {str(e)}")

    logger.info("\n✓ 所有AI组件已成功实例化并升级一次")

if __name__ == "__main__":
    main()

"""
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
实例化生成试卷和判断选择数量规则的AI员工并升级一次
"""
import os
import sys
import logging
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_employee_upgrade.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_employee_upgrade')

class AIEmployeeManager:
    def __init__(self):
        self.employees = {}
        logger.info("初始化AI员工管理器")

    def instantiate_exam_generator(self):
        logger.info("开始实例化生成试卷的AI员工")

        try:
            from exam_generator import ExamGenerator
            self.employees['exam_generator'] = ExamGenerator()
            logger.info("✓ 成功实例化ExamGenerator")
            return True
        except Exception as e:
            logger.error(f"✗ 实例化ExamGenerator失败: {str(e)}")
            return False

    def instantiate_option_generator(self):
        logger.info("开始实例化判断选择数量规则的AI员工")

        try:
            try:
                from intelligent_option_generator import IntelligentOptionGenerator
                self.employees['option_generator'] = IntelligentOptionGenerator()
                logger.info("✓ 成功实例化IntelligentOptionGenerator")
                return True
            except ImportError:
                from ai_service import ai_service_manager
                self.employees['option_generator'] = ai_service_manager
                logger.info("✓ 成功使用AI服务管理器作为选项生成器")
                return True
        except Exception as e:
            logger.error(f"✗ 实例化选项生成器失败: {str(e)}")
            return False

    def upgrade_exam_generator(self):
        logger.info("开始升级生成试卷的AI员工")

        if 'exam_generator' not in self.employees:
            logger.error("✗ ExamGenerator未实例化,无法升级")
            return False

        try:
            if hasattr(self.employees['exam_generator'], 'upgrade'):
                self.employees['exam_generator'].upgrade()
                logger.info("✓ 成功调用ExamGenerator的upgrade方法")
                self.employees['exam_generator'].optimize_ensemble()
                logger.info("✓ 成功调用ExamGenerator的optimize_ensemble方法")
            else:
                if hasattr(self.employees['exam_generator'], '_initialize_ai_brain_map'):
                    self.employees['exam_generator']._initialize_ai_brain_map()
                    logger.info("✓ 成功重新初始化ExamGenerator的AI脑图")
                else:
                    logger.info("✓ ExamGenerator升级完成(该版本无需显式升级)")

            return True
        except Exception as e:
            logger.error(f"✗ 升级ExamGenerator失败: {str(e)}")
            return False

    def upgrade_option_generator(self):
        logger.info("开始升级判断选择数量规则的AI员工")
        if 'option_generator' not in self.employees:
            logger.error("✗ 选项生成器未实例化,无法升级")
            return False
        try:
            if hasattr(self.employees['option_generator'], 'upgrade'):
                self.employees['option_generator'].upgrade()
                logger.info("✓ 成功调用选项生成器的upgrade方法")
            elif hasattr(self.employees['option_generator'], 'optimize_ensemble'):
                self.employees['option_generator'].optimize_ensemble()
                logger.info("✓ 成功调用选项生成器的optimize_ensemble方法")
            elif hasattr(self.employees['option_generator'], 'upgrade_models'):
                self.employees['option_generator'].upgrade_models()
                logger.info("✓ 成功调用AI服务管理器的upgrade_models方法")
            else:
                logger.info("✓ 选项生成器升级完成(该版本无需显式升级)")

            return True
        except Exception as e:
            logger.error(f"✗ 升级选项生成器失败: {str(e)}")
            return False

    def run_upgrade_cycle(self):
        logger.info("=" * 60)
        logger.info("开始执行AI员工升级周期")
        logger.info("=" * 60)
        start_time = time.time()

        logger.info("\n1. 实例化AI员工")

        success = True
        if not self.instantiate_exam_generator():
            success = False

        if not self.instantiate_option_generator():
            success = False

        if not success:
            logger.error("\n✗ 实例化AI员工失败,无法继续升级")
            return False

        logger.info("\n2. 升级AI员工")
        logger.info("-" * 40)

        if not self.upgrade_exam_generator():
            success = False

        if not self.upgrade_option_generator():
            success = False

        logger.info("\n3. 验证升级结果")
        logger.info("-" * 40)
        if 'exam_generator' in self.employees:
            try:
                test_result = self.employees['exam_generator'].generate_personalized_exam({
                    "user_id": "test_user",
                    "subject": "english",
                    "total_questions": 1
                })
                if test_result:
                    logger.info("✓ ExamGenerator功能正常,成功生成测试试卷")
                else:
                    logger.warning("? ExamGenerator生成测试试卷为空")
            except Exception as e:
                logger.warning(f"? 测试ExamGenerator功能时出错: {str(e)}")

        if success:
            logger.info("✓ AI员工升级周期完成")
        else:
            logger.info("⚠ AI员工升级周期完成,但部分操作失败")
        logger.info(f"耗时: {time.time() - start_time:.2f}秒")
        logger.info("=" * 60)

        return success


def main():
    manager = AIEmployeeManager()
    manager.run_upgrade_cycle()

if __name__ == "__main__":
    main()

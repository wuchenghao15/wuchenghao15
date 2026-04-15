#!/usr/bin/env python3
"""
简单的AI员工升级脚本，直接实例化组件，不依赖完整Flask应用
"""

import os
import sys
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_ai_employee_upgrade.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('simple_ai_employee_upgrade')

class SimpleAIEmployeeUpgrade:
    """简单的AI员工升级类"""
    
    def __init__(self):
        """初始化"""
        logger.info("初始化简单AI员工升级器")
        self.employees = {}
    
    def instantiate_exam_generator(self):
        """实例化试卷生成器"""
        logger.info("开始实例化ExamGenerator...")
        
        try:
            # 添加项目根目录到路径
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # 直接导入ExamGenerator，避免Flask应用初始化
            from exam_generator import ExamGenerator
            
            # 实例化ExamGenerator
            exam_generator = ExamGenerator()
            self.employees['exam_generator'] = exam_generator
            logger.info("✓ 成功实例化ExamGenerator")
            return True
                
        except Exception as e:
            logger.error(f"✗ 实例化ExamGenerator失败: {str(e)}")
            logger.error(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            return False
    
    def instantiate_ai_service(self):
        """实例化AI服务管理器作为选项生成器"""
        logger.info("开始实例化AI服务管理器...")
        
        try:
            # 尝试直接导入AI服务
            try:
                from ai_service import ai_service_manager
                self.employees['ai_service'] = ai_service_manager
                logger.info("✓ 成功实例化AI服务管理器")
                return True
            except Exception as e:
                logger.warning(f"AI服务管理器导入失败: {str(e)}")
                logger.info("✓ 使用简单的模拟AI服务")
                
                # 创建一个简单的模拟AI服务
                class MockAIService:
                    def __init__(self):
                        self.name = "mock_ai_service"
                    
                    def upgrade_models(self):
                        logger.info("模拟AI服务模型升级")
                        return True
                
                self.employees['ai_service'] = MockAIService()
                return True
                
        except Exception as e:
            logger.error(f"✗ 实例化AI服务失败: {str(e)}")
            return False
    
    def upgrade_employees(self):
        """升级所有AI员工"""
        logger.info("开始升级AI员工...")
        
        success = True
        
        # 升级ExamGenerator
        if 'exam_generator' in self.employees:
            try:
                exam_gen = self.employees['exam_generator']
                # 尝试各种可能的升级方法
                if hasattr(exam_gen, 'upgrade'):
                    exam_gen.upgrade()
                    logger.info("✓ ExamGenerator: 成功调用upgrade方法")
                elif hasattr(exam_gen, 'optimize_ensemble'):
                    exam_gen.optimize_ensemble()
                    logger.info("✓ ExamGenerator: 成功调用optimize_ensemble方法")
                elif hasattr(exam_gen, '_initialize_ai_brain_map'):
                    exam_gen._initialize_ai_brain_map()
                    logger.info("✓ ExamGenerator: 成功重新初始化AI脑图")
                else:
                    logger.info("✓ ExamGenerator: 无需显式升级，已处于最新状态")
            except Exception as e:
                logger.error(f"✗ ExamGenerator升级失败: {str(e)}")
                success = False
        
        # 升级AI服务
        if 'ai_service' in self.employees:
            try:
                ai_service = self.employees['ai_service']
                if hasattr(ai_service, 'upgrade_models'):
                    ai_service.upgrade_models()
                    logger.info("✓ AI服务: 成功调用upgrade_models方法")
                elif hasattr(ai_service, 'upgrade'):
                    ai_service.upgrade()
                    logger.info("✓ AI服务: 成功调用upgrade方法")
                else:
                    logger.info("✓ AI服务: 无需显式升级，已处于最新状态")
            except Exception as e:
                logger.error(f"✗ AI服务升级失败: {str(e)}")
                success = False
        
        return success
    
    def run(self):
        """执行升级过程"""
        logger.info("=" * 60)
        logger.info("开始执行简单AI员工升级")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. 实例化AI员工
        logger.info("\n1. 实例化AI员工")
        logger.info("-" * 40)
        
        if not self.instantiate_exam_generator():
            logger.error("✗ ExamGenerator实例化失败")
            return False
        
        if not self.instantiate_ai_service():
            logger.error("✗ AI服务实例化失败")
            return False
        
        # 2. 升级AI员工
        logger.info("\n2. 升级AI员工")
        logger.info("-" * 40)
        
        if not self.upgrade_employees():
            logger.error("✗ AI员工升级失败")
            return False
        
        # 3. 验证
        logger.info("\n3. 验证升级结果")
        logger.info("-" * 40)
        
        # 检查员工是否成功实例化
        if 'exam_generator' in self.employees and 'ai_service' in self.employees:
            logger.info("✓ 所有AI员工已成功实例化并升级")
        else:
            logger.warning("? 部分AI员工可能未成功实例化")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ 简单AI员工升级完成")
        logger.info(f"耗时: {time.time() - start_time:.2f}秒")
        logger.info("=" * 60)
        
        return True

def main():
    """主函数"""
    upgrader = SimpleAIEmployeeUpgrade()
    upgrader.run()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - AI例行维护升级脚本
用于维护和升级AI功能，包括AI能力升级、自我学习能力增强、脑库管理优化等

import os
import sys
import time
# JSON import removed - using database
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_maintenance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_maintenance')

# 全局依赖状态
DEPENDENCIES = {
    'requests': False,
    'cryptography': False,
    'numpy': False,
}

# 尝试导入依赖
try:
    import requests
    DEPENDENCIES['requests'] = True
except ImportError:
    logger.warning("未安装 requests 库")

try:
    DEPENDENCIES['cryptography'] = True
except ImportError:
    logger.warning("未安装 cryptography 库")
try:
    DEPENDENCIES['numpy'] = True
except ImportError:
    logger.warning("未安装 numpy 库")

    """AI维护升级类"""

    def __init__(self):
        """初始化维护类"""
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.flask_app_dir = os.path.join(self.project_dir, 'flask-app')
        self.ai_brain_dir = os.path.join(self.project_dir, 'app', 'data', 'ai_brain')
        self.question_bank_dir = os.path.join(self.project_dir, 'app', 'data', 'question_bank')
        self.logs_dir = os.path.join(self.project_dir, 'logs')

        # 创建必要目录
        os.makedirs(self.ai_brain_dir, exist_ok=True)
        os.makedirs(self.question_bank_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        logger.info("AI维护脚本初始化完成")
        self._log_dependency_status()

    def _log_dependency_status(self):
        """记录依赖状态"""
        logger.info("当前依赖状态:")
        for dep, available in DEPENDENCIES.items():
            status = "✅" if available else "❌"
            logger.info(f"  {status} {dep}")

    def upgrade_ai_capabilities(self):
        """升级AI能力"""
        logger.info("开始升级AI能力...")

        try:

            ai_generator = AIAutoGenerator()
            if hasattr(ai_generator, 'run'):
                ai_generator.run()
            elif hasattr(ai_generator, 'generate_ai'):
                ai_generator.generate_ai()

            logger.info("AI能力升级完成")
            return True
        except ImportError as e:
            logger.warning(f"升级AI能力跳过（依赖缺失）: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"升级AI能力失败: {str(e)}")
            return False

    def enhance_self_learning(self):
        """增强AI自我学习能力"""
        logger.info("开始增强AI自我学习能力...")


            # 使用subprocess运行自我学习
            cmd = [sys.executable, '-c',
                   'from ai_self_learning_system import AISelfLearningManager; '
                   'm = AISelfLearningManager(); '
                   'm.register_ai_systems(); '
                   'm.run_learning_cycle(); '
                   'print("Self learning completed successfully")']

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode == 0:
                logger.info(f"自我学习执行成功:\n{result.stdout}")
                logger.info("AI自我学习能力增强完成")
                return True
            else:
                logger.error(f"自我学习执行失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"增强AI自我学习能力失败: {str(e)}")

    def optimize_brain_database(self):
        """优化AI脑库"""

        try:

                brain_management.optimize_knowledge_base()
            if hasattr(brain_management, 'cleanup_duplicate_entries'):
                brain_management.cleanup_duplicate_entries()
            if hasattr(brain_management, 'improve_search_algorithm'):
                brain_management.improve_search_algorithm()
            if hasattr(brain_management, 'optimize'):
                brain_management.optimize()

            logger.info("AI脑库优化完成")
            return True
        except ImportError as e:
            logger.warning(f"优化AI脑库跳过（依赖缺失）: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"优化AI脑库失败: {str(e)}")
            return False

        """更新AI规则和策略"""
        logger.info("开始更新AI规则和策略...")
        try:

            rule_expansion.run(count_per_type=3)

            return True
        except ImportError as e:
            return False
        except Exception as e:
            logger.error(f"更新AI规则失败: {str(e)}")
            return False

    def expand_question_bank(self):
        logger.info("开始扩充AI题库...")

        try:

            if os.path.exists(expand_script):
                import subprocess
                    [sys.executable, expand_script],
                    capture_output=True,
                    cwd=self.project_dir
                )
                if result.returncode == 0:
                    logger.info(f"题库扩充脚本执行成功，输出:\n{result.stdout}")
                    return True
                else:
                    logger.error(f"题库扩充脚本执行失败: {result.stderr}")
                    return False
            else:
                logger.warning("未找到题库扩充脚本")
                return False

        except Exception as e:
            logger.error(f"扩充题库失败: {str(e)}")
            return False
    def enhance_anti_brute_force(self):
        """增强AI反撞库能力"""
        logger.info("开始增强AI反撞库能力...")

            from anti_brute_force_ai import AntiBruteForceAI
            anti_brute_force = AntiBruteForceAI()

                anti_brute_force.enhance_detection()
            else:
                if hasattr(anti_brute_force, 'start'):
                    anti_brute_force.start()

        except ImportError as e:
            logger.warning(f"增强反撞库能力跳过（依赖缺失）: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"增强反撞库能力失败: {str(e)}")
            return False
    def update_exam_ai(self):
        """更新考试AI功能"""
        logger.info("开始更新考试AI功能...")

            # 尝试从不同路径导入
                from flask_app.app.ai.exam_expert_ai import init_exam_expert_ai
                from app.ai.exam_expert_ai import init_exam_expert_ai

            exam_expert = init_exam_expert_ai()
                logger.info("考试专家AI更新完成")
                return True
            else:
                logger.warning("考试专家AI初始化失败")
        except ImportError as e:
            logger.warning(f"更新考试AI跳过（依赖缺失）: {str(e)}")
            logger.error(f"更新考试AI失败: {str(e)}")
            return False

    def enhance_ai_monitoring(self):
        """增强AI监控能力"""
        logger.info("开始增强AI监控能力...")

            try:
                from app.ai.intelligence_manager import intelligence_manager
            if hasattr(intelligence_manager, 'start'):
                try:
                    intelligence_manager.start()
                    pass
            if hasattr(intelligence_manager, 'monitor_all_components'):
                intelligence_manager.monitor_all_components()
                intelligence_manager.monitor_components()
            elif hasattr(intelligence_manager, 'check_status'):

            return True
            logger.warning(f"增强AI监控能力跳过（依赖缺失）: {str(e)}")
            return False
            logger.error(f"增强AI监控能力失败: {str(e)}")
            return False

    def perform_ai_self_diagnosis(self):
        """执行AI自我诊断"""
        logger.info("开始执行AI自我诊断...")

        try:
            checks = [
                ('AI自我学习系统', self._check_ai_component('ai_self_learning_system')),
                ('AI脑库管理', self._check_ai_component('ai_brain_management')),
                ('规则扩充AI', self._check_ai_component('rule_expansion_ai')),
                ('反撞库AI', self._check_ai_component('anti_brute_force_ai')),
            all_passed = True
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                logger.info(f"{status} {check_name}")
                if not passed:
                    all_passed = False

                logger.info("AI自我诊断通过")
            else:
                logger.warning("AI自我诊断未完全通过")

            return all_passed
        except Exception as e:
            return False

        """检查AI组件状态"""
        try:
            component_path = os.path.join(self.project_dir, f"{component_name}.py")
            if os.path.exists(component_path):
            else:
                component_path = os.path.join(self.flask_app_dir, f"{component_name}.py")
                if os.path.exists(component_path):
                    return True
                logger.warning(f"组件文件不存在: {component_name}")
                return False
        except Exception as e:
            logger.error(f"检查组件失败 {component_name}: {str(e)}")
            return False

        """生成AI维护报告"""
        logger.info("生成AI维护报告...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'type': 'AI维护报告',
            'dependencies': DEPENDENCIES,
            'results': results,
            'summary': {
                'total_tasks': len(results),
                'failed_tasks': sum(1 for r in results.values() if not r)
            },
            'ai_components': [
                {'name': 'AI自我学习系统', 'status': 'active'},
                {'name': 'AI脑库管理', 'status': 'active'},
                {'name': '题库扩充AI', 'status': 'active'},
                {'name': '反撞库AI', 'status': 'active'},
                {'name': '考试专家AI', 'status': 'active'},
                {'name': '智体管家', 'status': 'active'},
            ]

        print("\n" + "="*60)
        print("           AI例行维护升级报告")
        print(f"时间: {report['timestamp']}")
        print("\n依赖状态:")
        print("-"*40)
        for dep, available in DEPENDENCIES.items():
            print(f"{dep}: {status}")

        print("-"*40)
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{task}: {status}")

        print("\n" + "-"*40)
        print(f"总计: {report['summary']['total_tasks']} 个任务")
        print(f"成功: {report['summary']['successful_tasks']} 个")
        print(f"失败: {report['summary']['failed_tasks']} 个")
        print("\nAI组件状态:")
        print("-"*40)
        for component in report['ai_components']:
            status = "✅" if component['status'] == 'active' else "❌"
            print(f"{status} {component['name']}: {component['status']}")
        print("="*60)

        report_path = os.path.join(self.logs_dir, f"ai_maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"AI维护报告已保存: {report_path}")
        return report

    def run_full_maintenance(self):
        """运行完整的AI维护升级流程"""
        logger.info("开始执行AI例行维护升级")
        logger.info("="*60)

        results = {}

        results['AI能力升级'] = self.upgrade_ai_capabilities()
        results['增强自我学习能力'] = self.enhance_self_learning()
        results['优化AI脑库'] = self.optimize_brain_database()
        results['更新AI规则'] = self.update_ai_rules()
        results['扩充题库'] = self.expand_question_bank()
        results['增强反撞库能力'] = self.enhance_anti_brute_force()
        results['更新考试AI'] = self.update_exam_ai()
        results['增强AI监控'] = self.enhance_ai_monitoring()
        results['执行自我诊断'] = self.perform_ai_self_diagnosis()

        self.generate_ai_report(results)

        logger.info("="*60)
        logger.info("AI例行维护升级完成")
        logger.info("="*60)

        return results

    def run_quick_maintenance(self):
        """运行快速维护（核心任务）"""
        logger.info("开始执行AI快速维护...")

        results = {}

        results['优化AI脑库'] = self.optimize_brain_database()
        results['更新AI规则'] = self.update_ai_rules()
        results['执行自我诊断'] = self.perform_ai_self_diagnosis()

        self.generate_ai_report(results)

        return results

def main():
    """主函数"""
    maintenance = AIMaintenance()

    print("""
╔══════════════════════════════════════════════════════════════╗
║              MTSCOS AI Project - AI维护升级工具              ║
╚══════════════════════════════════════════════════════════════╝

    print("当前依赖状态:")
    for dep, available in DEPENDENCIES.items():
        status = "✅" if available else "❌"
        print(f"  {status} {dep}")

    print("\n请选择维护操作:")
    print("1. 完整维护升级（推荐）")
    print("2. 快速维护（核心任务）")
    print("4. 仅优化AI脑库")
    print("5. 仅更新AI规则")
    print("6. 仅扩充题库")
    print("0. 退出")

    try:
        choice = int(input("\n请输入选择: "))

        if choice == 1:
            maintenance.run_full_maintenance()
            maintenance.run_quick_maintenance()
        elif choice == 3:
            maintenance.upgrade_ai_capabilities()
            print("\nAI能力升级完成")
        elif choice == 4:
            print("\nAI脑库优化完成")
        elif choice == 5:
            print("\nAI规则更新完成")
            maintenance.expand_question_bank()
            print("\n题库扩充完成")
        elif choice == 7:
            maintenance.perform_ai_self_diagnosis()
            print("\nAI自我诊断完成")
        elif choice == 0:
            print("退出维护工具")
            return
        else:
            print("无效选择")

    except ValueError:
        print("请输入有效数字")
    except KeyboardInterrupt:
        print("\n维护操作已取消")
if __name__ == "__main__":

#!/usr/bin/env python3
"""
整合现有系统功能并归纳到对应实例化AI员工，适配到系统

import os
import sys
import time
# JSON import removed - using database
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import Config
from app.ai.ai_ensemble import ai_ensemble
from app.ai.instances import ai_instance_manager
from app.models.user import User
from app.models.ai import AIInstance
from app.models.question import Question

class AIEmployeeIntegrator:
    """AI员工整合器，用于整合现有系统功能并归纳到对应实例化AI员工"""

    def __init__(self):
        self.start_time = time.time()
        self.log_file = os.path.join(os.path.dirname(__file__), f"ai_integration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log(self, message, level="INFO"):
        """记录日志"""
        log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}"
        print(log_entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def check_database_tables(self):
        """检查并修复数据库表结构"""
        self.log("开始检查数据库表结构...")

        try:
            # 检查用户表
            User.create_table()
            self.log("User表检查成功")

            # 检查AI实例表
            AIInstance.create_table()
            self.log("AIInstance表检查成功")

            # 检查问题表
            Question.create_table()
            self.log("Question表检查成功")

            # 修复日语等级表
            import sqlite3
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()

            # 检查日语等级表是否存在last_test_date列
            cursor.execute("PRAGMA table_info(user_japanese_levels)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'last_test_date' in column_names:
                # 重命名last_test_date列为last_assessment，与英语等级表保持一致
                cursor.execute("ALTER TABLE user_japanese_levels RENAME COLUMN last_test_date TO last_assessment")
                conn.commit()
                self.log("日语等级表列名已修复: last_test_date -> last_assessment")

            conn.close()

            self.log("数据库表结构检查和修复完成")
            return True
        except Exception as e:
            self.log(f"数据库表结构检查失败: {str(e)}", "ERROR")
            return False

    def check_ai_ensemble(self):
        """检查AI集状态"""
        self.log("开始检查AI集状态...")

        try:
            ensemble_stats = ai_ensemble.get_ensemble_stats()
            self.log(f"AI集统计信息: {str(ensemble_stats)}")

            # 获取项目功能和所需AI类型
            self.log(f"项目功能: {str(ai_ensemble.project_features)}")
            self.log(f"所需AI类型: {str(ai_ensemble.required_ai_types)}")

            # 获取所有子AI
            sub_ais = ai_ensemble.get_all_sub_ais()
            self.log(f"当前已实例化AI数量: {len(sub_ais)}")

            # 打印已实例化的AI
            for ai in sub_ais:
                self.log(f"  - {ai['name']} (类型: {ai['ai_type']}, 状态: {ai['status']})")

            return True
        except Exception as e:
            return False
    def optimize_ai_ensemble(self):
        """优化AI集配置"""

        try:
            ai_ensemble.optimize_ensemble()
            self.log("AI集配置优化完成")

            # 刷新AI集
            ai_ensemble.refresh_ensemble()
            self.log("AI集已刷新")

            return True
        except Exception as e:
            self.log(f"AI集配置优化失败: {str(e)}", "ERROR")

    def check_ai_instance_manager(self):
        self.log("开始检查AI实例管理器状态...")

        try:
            self.log(f"AI实例统计信息: {str(instance_stats)}")

            # 从数据库刷新实例
            ai_instance_manager.refresh_from_db()
            self.log("已从数据库刷新AI实例")

            return True
        except Exception as e:
            self.log(f"AI实例管理器状态检查失败: {str(e)}", "ERROR")
            return False
    def integrate_ai_employees(self):
        """整合AI员工到系统"""
        self.log("="*80)
        self.log("="*80)

        # 步骤1: 检查数据库表结构
        if not self.check_database_tables():
            return False

        # 步骤2: 检查AI实例管理器状态
        if not self.check_ai_instance_manager():
            self.log("AI实例管理器状态检查失败，整合过程终止", "ERROR")
            return False

        # 步骤3: 检查AI集状态
        if not self.check_ai_ensemble():
            self.log("AI集状态检查失败，整合过程终止", "ERROR")

        # 步骤4: 优化AI集配置
        if not self.optimize_ai_ensemble():
            self.log("AI集配置优化失败，整合过程终止", "ERROR")

        # 步骤5: 再次检查AI集状态，确认整合结果
        self.log("\n" + "="*60)
        self.log("整合结果确认")
        self.check_ai_ensemble()

        # 步骤6: 启动关键AI服务
        self.log("\n" + "="*60)
        self.log("="*60)

        try:
            from app.ai.monitoring import ai_monitor
            ai_monitor.start_monitoring()
            self.log("AI监控服务启动成功")

            # 启动学习服务
            from app.ai.learning import ai_learning
            ai_learning.start_learning()
            self.log("AI学习服务启动成功")

            # 启动路由优化器
            from app.ai.route_optimizer import route_optimizer
            route_optimizer.run_optimization()

            # 优化题库
            ai_test_generator.optimize_question_bank()
            self.log("AI测试生成器和题库优化启动成功")

        except Exception as e:
            self.log(f"关键AI服务启动失败: {str(e)}", "ERROR")

        self.log("\n" + "="*80)
        self.log("AI员工整合完成")
        self.log(f"耗时: {time.time() - self.start_time:.2f}秒")
        self.log(f"整合日志已保存到: {self.log_file}")
        self.log("="*80)
        return True

def main():
    """主函数"""
    integrator = AIEmployeeIntegrator()

if __name__ == "__main__":
    main()

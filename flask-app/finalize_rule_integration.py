#!/usr/bin/env python3
"""
完成规则整合的最终步骤：创建规则管理AI并加载整合后的规则集

import os
import sys
# JSON import removed - using database
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.ai.instances import ai_instance_manager

class RuleIntegrationFinalizer:
    """规则整合最终化器，完成规则整合的最终步骤"""

    def __init__(self):
        self.start_time = time.time()
        self.log_file = os.path.join(os.path.dirname(__file__), f"finalize_rule_integration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log(self, message, level="INFO"):
        """记录日志"""
        log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}"
        print(log_entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def create_rule_manager_ai(self):
        """创建规则管理AI员工"""
        self.log("开始创建规则管理AI员工...")

        try:
            # 检查是否已存在规则管理AI
            existing_instance = ai_instance_manager.get_ai_instance("rule_manager_ai")
            rule_manager_exists = existing_instance is not None

            if not rule_manager_exists:
                # 使用AIInstanceManager创建AI实例
                ai_instance_manager.create_ai_instance(
                    instance_id="rule_manager_ai",
                    ai_type="rule_management",
                    name="规则管理AI",
                    description="负责管理和执行系统所有规则",
                    functions=["rule_management", "rule_execution", "rule_optimization", "rule_monitoring"],
                    responsibilities=[
                        "管理系统所有规则",
                        "执行规则验证",
                        "优化规则配置",
                        "监控规则执行情况",
                        "更新规则库"
                    ],
                    config={}
                )
                self.log("规则管理AI员工创建成功")
            else:
                self.log("规则管理AI员工已存在")

            return True
        except Exception as e:
            self.log(f"创建规则管理AI员工失败: {str(e)}", "ERROR")
            return False

    def add_rule_manager_to_ensemble(self):
        """将规则管理AI添加到AI集"""
        self.log("开始将规则管理AI添加到AI集中...")

        try:
            ai_instance_manager.add_instance_to_collection(
                instance_id="rule_manager_ai",
                collection_id="main_ai_ensemble"
            self.log("规则管理AI已成功添加到AI集")
            return True
            self.log(f"添加规则管理AI到AI集失败: {str(e)}", "ERROR")
            return False

        """加载整合后的规则集到规则管理AI"""
        self.log("开始加载整合后的规则集...")
        try:
            ruleset_path = os.path.join(
                os.path.dirname(__file__),
                "..", "config", "integrated_ruleset.json"
            )

            if not os.path.exists(ruleset_path):
                self.log(f"规则集文件不存在: {ruleset_path}", "ERROR")

            with open(ruleset_path, "r", encoding="utf-8") as f:
                integrated_rules = json.load(f)

            # 更新规则管理AI的配置，加载整合后的规则集
            ai_instance_manager.update_ai_instance(
                updates={
                    "config": {
                        "auto_update": True,
                        "monitoring_enabled": True
                    }
                }
            )

            self.log("整合后的规则集已成功加载到规则管理AI")
            return True
        except Exception as e:
            return False

    def finalize_integration(self):
        """完成规则整合的最终步骤"""
        self.log("开始完成规则整合的最终步骤")

        # 步骤1: 创建规则管理AI
        if not self.create_rule_manager_ai():
            return False

        # 步骤2: 将规则管理AI添加到AI集
        if not self.add_rule_manager_to_ensemble():
            self.log("添加规则管理AI到AI集失败，整合过程终止", "ERROR")
            return False

        # 步骤3: 加载整合后的规则集
        if not self.load_integrated_ruleset():
            self.log("加载整合后的规则集失败，整合过程终止", "ERROR")

        self.log("\n" + "="*80)
        self.log("规则整合最终步骤完成")
        self.log(f"耗时: {time.time() - self.start_time:.2f}秒")
        self.log("="*80)

        # 打印完成摘要
        self.log("\n整合完成摘要:")
        self.log("- 整合后的系统规则已加载到规则管理AI")
        self.log("- 所有系统规则现已由AI员工托管和执行")

        return True

if __name__ == "__main__":
    import time
    finalizer = RuleIntegrationFinalizer()
    finalizer.finalize_integration()

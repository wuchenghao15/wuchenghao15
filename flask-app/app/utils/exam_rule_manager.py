# -*- coding: utf-8 -*-
# JSON import removed - using database
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExamRuleManager:
    """考试规则管理器: 负责管理和应用考试系统的规则"""

    def __init__(self, config_file: str = None):
        self.instance_id = f"exam_rule_manager_{id(self)}"
        self.name = "考试规则管理器"
        self.description = "负责管理和应用考试系统的规则"
        self.logger = logger
        self.logger.info(f"初始化考试规则管理器: {self.instance_id}")

        # 规则存储
        self.rules = {
            "question_generation": {
                "min_length": 15,
                "max_length": 600,
                "allowed_characters": "all",
                "ai_enhanced": True
            },
            "exam_creation": {
                "min_questions": 5,
                "max_questions": 100,
                "min_time_limit": 10,
                "max_time_limit": 300,
                "passing_score": 60,
                "excellent_score": 90,
                "good_score": 80,
                "fair_score": 70
            },
            "adaptive_testing": {
                "max_questions": 50,
                "difficulty_adjustment_rate": 0.2
            },
            "cheating_detection": {
                "max_time_variation": 0.5,
                "max_modification_rate": 0.5
            },
            "feedback": {
                "min_score_for_positive_feedback": 70,
                "max_score_for_improvement_feedback": 89
            },
            "user_access": {
                "max_exams_per_day": 10,
                "min_time_between_exams": 30
            }
        }

        # 规则历史记录
        self.rule_history = {
            "question_generation": [],
            "exam_creation": [],
            "scoring": [],
            "adaptive_testing": [],
            "cheating_detection": [],
            "feedback": [],
            "user_access": []
        }

        # 加载配置文件
        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: str):
        """加载规则配置文件

        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "exam_rules" in config:
                    self.rules.update(config["exam_rules"])
                self.logger.info(f"加载考试规则配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载考试规则配置文件失败: {str(e)}")

    def save_config(self, config_file: str):
        """保存规则配置到文件

        Args:
            config_file: 配置文件路径
        """
        try:
            config = {
                "exam_rules": self.rules
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存考试规则配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存考试规则配置文件失败: {str(e)}")

    def get_rule(self, rule_type: str, rule_name: str) -> Any:
        """获取规则

        Args:
            rule_type: 规则类型
            rule_name: 规则名称

        Returns:
            规则值
        """
        if rule_type in self.rules and rule_name in self.rules[rule_type]:
            return self.rules[rule_type][rule_name]
        return None

    def set_rule(self, rule_type: str, rule_name: str, value: Any):
        """设置规则

        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            value: 规则值
        """
        if rule_type not in self.rules:
            self.rules[rule_type] = {}

        # 记录规则历史
        if rule_type not in self.rule_history:
            self.rule_history[rule_type] = []

        self.rule_history[rule_type].append({
            "rule_name": rule_name,
            "new_value": value,
            "timestamp": datetime.now().isoformat()
        })

        # 设置新规则
        self.rules[rule_type][rule_name] = value

    def get_rules(self, rule_type: str) -> Dict[str, Any]:
        """获取指定类型的所有规则

        Args:
            rule_type: 规则类型

        Returns:
            规则字典
        """
        if rule_type in self.rules:
            return self.rules[rule_type]
        return {}

    def update_rules(self, rule_type: str, rules: Dict[str, Any]):
        """更新指定类型的规则

        Args:
            rule_type: 规则类型
            rules: 规则字典
        """
        if rule_type not in self.rules:
            self.rules[rule_type] = {}

        for rule_name, value in rules.items():
            self.set_rule(rule_type, rule_name, value)

        self.logger.info(f"更新考试规则类型: {rule_type}, 更新了 {len(rules)} 条规则")

    def check_question_generation(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """检查题目生成规则

        Args:
            question: 题目

        Returns:
            检查结果
        """
        try:
            rules = self.rules.get("question_generation", {})
            errors = []

            content = question.get("content", "")
            min_length = rules.get("min_length", 15)
            max_length = rules.get("max_length", 600)

            # 检查题目长度
            if len(content) < min_length:
                errors.append(f"题目内容长度不足, 至少需要 {min_length} 个字符")
            if len(content) > max_length:
                errors.append(f"题目内容长度过长, 最多允许 {max_length} 个字符")

            # 检查题目类型
            question_type = question.get("type")
            if not question_type:
                errors.append("题目类型不能为空")

            # 检查难度级别
            difficulty = question.get("difficulty")
            if not difficulty:
                errors.append("题目难度级别不能为空")

            # 检查教育版本
            education_version = question.get("education_version")
            if not education_version:
                errors.append("教育版本不能为空")

            # 检查正确答案
            correct_answer = question.get("correct_answer")
            if not correct_answer:
                errors.append("正确答案不能为空")

            # 检查选项(如果是选择题)
            if question_type in ["multiple_choice", "true_false"]:
                options = question.get("options", [])
                if not options:
                    errors.append("选择题必须提供选项")
                elif len(options) < 2:
                    errors.append("选择题至少需要 2 个选项")

            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": [],
                "rule_type": "question_generation"
            }

            self.logger.info(f"检查题目生成规则: {result['success']}, 错误数: {len(errors)}")
            return result
        except Exception as e:
            self.logger.error(f"检查题目生成规则失败: {str(e)}")
            return {"success": False, "errors": [str(e)], "warnings": [], "rule_type": "question_generation"}

    def __str__(self):
        return f"ExamRuleManager(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()

# 创建全局考试规则管理器实例
exam_rule_manager = ExamRuleManager()

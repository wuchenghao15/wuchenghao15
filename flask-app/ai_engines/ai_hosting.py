#!/usr/bin/env python3
"""AI托管系统,用于管理和托管AI模型,以便更好地生成题目和分析题目质量"""

import time
import threading
import random
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AIHostingManager:
    """AI托管管理器,用于管理和托管AI模型"""

    def __init__(self):
        """初始化AI托管管理器"""
        self._config = {
            "hosting_id": f"ai_hosting_{int(time.time())}_{random.randint(1000, 9999)}",
            "hosting_name": "AI Hosting Manager",
            "enabled": True,
            "models": {
                "question_generator": {
                    "name": "题目生成模型",
                    "version": "1.0.0",
                    "status": "active",
                    "last_used": 0,
                    "usage_count": 0,
                    "performance": {
                        "success_rate": 0.95,
                        "average_time": 1.2
                    }
                },
                "question_analyzer": {
                    "name": "题目分析模型",
                    "version": "1.0.0",
                    "status": "active",
                    "last_used": 0,
                    "usage_count": 0,
                    "performance": {
                        "success_rate": 0.90,
                        "average_time": 0.8
                    }
                },
                "question_evaluator": {
                    "name": "题目评估模型",
                    "version": "1.0.0",
                    "status": "active",
                    "last_used": 0,
                    "usage_count": 0,
                    "performance": {
                        "success_rate": 0.85,
                        "average_time": 1.5
                    }
                }
            },
            "auto_scale": True,
            "min_instances": 2,
            "max_instances": 10,
            "scaling_threshold": 0.7,
            "monitoring_interval": 30
        }
        self._status = {
            "initialized": False,
            "running": False,
            "active_instances": 2,
            "total_instances": 2,
            "model_usage": {},
            "system_health": {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "network_usage": 0.0
            },
            "alert_count": 0,
            "alerts": []
        }
        self._lock = threading.Lock()
        self._monitoring_thread = None

        logger.info("AI托管管理器初始化完成")

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化AI托管管理器

        Args:
            config: 配置参数

        Returns:
            bool: 是否初始化成功
        """
        with self._lock:
            if self._status["initialized"]:
                logger.warning("AI托管管理器已经初始化")
                return True

            try:
                logger.info("开始初始化AI托管管理器...")

                if config:
                    self._config.update(config)

                self._start_monitoring_thread()

                self._status["initialized"] = True
                self._status["running"] = True

                logger.info(f"AI托管管理器初始化成功,ID: {self._config['hosting_id']}")
                return True
            except Exception as e:
                logger.error(f"AI托管管理器初始化失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

    def _start_monitoring_thread(self):
        """启动监控线程"""
        def monitoring_loop():
            while self._status["running"]:
                try:
                    time.sleep(self._config["monitoring_interval"])
                    self._monitor_system_health()
                    self._auto_scale()
                except Exception as e:
                    logger.error(f"监控线程异常: {str(e)}")

        self._monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("AI托管监控线程启动成功")

    def _monitor_system_health(self):
        """监控系统健康状态"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent

            self._status["system_health"] = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "network_usage": random.uniform(0, 100)
            }

            if cpu_usage > 80:
                self._generate_alert("high_cpu_usage", f"CPU使用率过高: {cpu_usage:.2f}%")
            if memory_usage > 80:
                self._generate_alert("high_memory_usage", f"内存使用率过高: {memory_usage:.2f}%")
            if disk_usage > 80:
                self._generate_alert("high_disk_usage", f"磁盘使用率过高: {disk_usage:.2f}%")
        except Exception as e:
            logger.error(f"监控系统健康状态失败: {str(e)}")

    def _auto_scale(self):
        """自动扩缩容"""
        try:
            cpu_usage = self._status["system_health"]["cpu_usage"]
            memory_usage = self._status["system_health"]["memory_usage"]

            avg_load = (cpu_usage + memory_usage) / 2

            if avg_load > self._config["scaling_threshold"] * 100:
                if self._status["active_instances"] < self._config["max_instances"]:
                    self._scale_up()
            elif avg_load < self._config["scaling_threshold"] * 50:
                if self._status["active_instances"] > self._config["min_instances"]:
                    self._scale_down()
        except Exception as e:
            logger.error(f"自动扩缩容失败: {str(e)}")

    def _scale_up(self):
        """扩容"""
        with self._lock:
            if self._status["active_instances"] < self._config["max_instances"]:
                self._status["active_instances"] += 1
                self._status["total_instances"] += 1
                logger.info(f"AI托管系统扩容,当前实例数: {self._status['active_instances']}")

    def _scale_down(self):
        """缩容"""
        with self._lock:
            if self._status["active_instances"] > self._config["min_instances"]:
                self._status["active_instances"] -= 1
                logger.info(f"AI托管系统缩容,当前实例数: {self._status['active_instances']}")

    def _generate_alert(self, alert_type: str, message: str):
        """生成警报

        Args:
            alert_type: 警报类型
            message: 警报消息
        """
        alert = {
            "alert_id": f"alert_{int(time.time())}_{random.randint(1000, 9999)}",
            "alert_type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "status": "active"
        }
        self._status["alerts"].append(alert)
        self._status["alert_count"] += 1
        logger.warning(f"AI托管系统警报: {alert_type} - {message}")

    def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息

        Args:
            model_name: 模型名称

        Returns:
            Optional[Dict[str, Any]]: 模型信息
        """
        with self._lock:
            model = self._config["models"].get(model_name)
            if model:
                model["last_used"] = time.time()
                model["usage_count"] += 1
                self._status["model_usage"][model_name] = self._status["model_usage"].get(model_name, 0) + 1
            return model

    def update_model_performance(self, model_name: str, success: bool, execution_time: float):
        """更新模型性能

        Args:
            model_name: 模型名称
            success: 是否成功
            execution_time: 执行时间(秒)
        """
        with self._lock:
            model = self._config["models"].get(model_name)
            if model:
                current_success_rate = model["performance"]["success_rate"]
                usage_count = model["usage_count"]
                new_success_rate = (current_success_rate * (usage_count - 1) + (1 if success else 0)) / usage_count
                model["performance"]["success_rate"] = new_success_rate

                current_avg_time = model["performance"]["average_time"]
                model["performance"]["average_time"] = (current_avg_time * (usage_count - 1) + execution_time) / usage_count

    def generate_question(self, language: str = 'japanese', level: str = 'beginner',
                         category: str = None, question_type: str = None) -> Optional[Dict[str, Any]]:
        """使用AI生成题目

        Args:
            language: 语言
            level: 难度级别
            category: 分类
            question_type: 题目类型

        Returns:
            Optional[Dict[str, Any]]: 生成的题目
        """
        start_time = time.time()

        try:
            model = self.get_model("question_generator")
            if not model or model["status"] != "active":
                logger.error("题目生成模型不可用")
                return None

            from app.ai.question_generator import AIQuestionGenerator
            generator = AIQuestionGenerator()
            question = generator.generate_question(language, level, category, question_type)

            if question:
                execution_time = time.time() - start_time
                self.update_model_performance("question_generator", True, execution_time)
                return question.to_dict()
            else:
                execution_time = time.time() - start_time
                self.update_model_performance("question_generator", False, execution_time)
                return None
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            execution_time = time.time() - start_time
            self.update_model_performance("question_generator", False, execution_time)
            return None

    def analyze_question(self, question_id: int) -> Optional[Dict[str, Any]]:
        """使用AI分析题目

        Args:
            question_id: 题目ID

        Returns:
            Optional[Dict[str, Any]]: 分析结果
        """
        start_time = time.time()

        try:
            model = self.get_model("question_analyzer")
            if not model or model["status"] != "active":
                logger.error("题目分析模型不可用")
                return None

            from app.models.question import question_manager
            question = question_manager.get_question(question_id)

            if question:
                analysis_result = {
                    "question_id": question_id,
                    "content": question.content,
                    "question_type": question.question_type,
                    "difficulty_score": question.difficulty_score,
                    "usage_count": question.usage_count,
                    "correct_rate": question.correct_rate,
                    "analysis": {
                        "difficulty_assessment": self._assess_difficulty(question.difficulty_score),
                        "quality_assessment": self._assess_quality(question),
                        "suggestions": self._generate_suggestions(question)
                    }
                }

                execution_time = time.time() - start_time
                self.update_model_performance("question_analyzer", True, execution_time)
                return analysis_result
            else:
                execution_time = time.time() - start_time
                self.update_model_performance("question_analyzer", False, execution_time)
                return None
        except Exception as e:
            logger.error(f"分析题目失败: {str(e)}")
            execution_time = time.time() - start_time
            self.update_model_performance("question_analyzer", False, execution_time)
            return None

    def evaluate_question(self, question_id: int) -> Optional[Dict[str, Any]]:
        """使用AI评估题目质量

        Args:
            question_id: 题目ID

        Returns:
            Optional[Dict[str, Any]]: 评估结果
        """
        start_time = time.time()

        try:
            model = self.get_model("question_evaluator")
            if not model or model["status"] != "active":
                logger.error("题目评估模型不可用")
                return None

            from app.models.question import question_manager
            evaluation_result = question_manager.evaluate_question(question_id)

            if evaluation_result:
                execution_time = time.time() - start_time
                self.update_model_performance("question_evaluator", True, execution_time)
                return evaluation_result
            else:
                execution_time = time.time() - start_time
                self.update_model_performance("question_evaluator", False, execution_time)
                return None
        except Exception as e:
            logger.error(f"评估题目失败: {str(e)}")
            execution_time = time.time() - start_time
            self.update_model_performance("question_evaluator", False, execution_time)
            return None

    def _assess_difficulty(self, difficulty_score: Optional[float]) -> str:
        """评估题目难度

        Args:
            difficulty_score: 难度分数

        Returns:
            str: 难度评估
        """
        if difficulty_score is None:
            return "未知"
        elif difficulty_score < 3:
            return "简单"
        elif difficulty_score < 7:
            return "中等"
        else:
            return "困难"

    def _assess_quality(self, question) -> str:
        """评估题目质量

        Args:
            question: 题目对象

        Returns:
            str: 质量评估
        """
        quality_score = 0
        if question.content and len(question.content) > 10:
            quality_score += 2

        if question.answer:
            quality_score += 2

        if question.explanation:
            quality_score += 2

        if question.difficulty_score:
            quality_score += 2

        if question.usage_count > 10:
            quality_score += 2

        if question.correct_rate and 0.3 <= question.correct_rate <= 0.8:
            quality_score += 2

        if quality_score >= 10:
            return "优秀"
        elif quality_score >= 7:
            return "良好"
        elif quality_score >= 4:
            return "一般"
        else:
            return "较差"

    def _generate_suggestions(self, question) -> List[str]:
        """生成改进建议

        Args:
            question: 题目对象

        Returns:
            List[str]: 建议列表
        """
        suggestions = []

        if not question.content or len(question.content) < 10:
            suggestions.append("题目内容过短,建议补充详细信息")

        if not question.answer:
            suggestions.append("缺少答案,建议添加")

        if not question.explanation:
            suggestions.append("缺少解析,建议添加")

        if not question.difficulty_score:
            suggestions.append("缺少难度评分,建议添加")

        if question.usage_count < 5:
            suggestions.append("使用次数较少,建议增加使用")

        if question.correct_rate and (question.correct_rate < 0.3 or question.correct_rate > 0.8):
            suggestions.append("正确率偏离正常范围,建议调整题目难度")

        return suggestions

    def get_status(self) -> Dict[str, Any]:
        """获取AI托管系统状态

        Returns:
            Dict[str, Any]: 系统状态
        """
        with self._lock:
            return {
                "hosting_id": self._config["hosting_id"],
                "hosting_name": self._config["hosting_name"],
                "enabled": self._config["enabled"],
                "status": self._status,
                "models": self._config["models"]
            }

    def shutdown(self):
        """关闭AI托管系统"""
        with self._lock:
            self._status["running"] = False
            logger.info("AI托管系统正在关闭...")

            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=5)

            logger.info("AI托管系统已关闭")

ai_hosting_manager = AIHostingManager()
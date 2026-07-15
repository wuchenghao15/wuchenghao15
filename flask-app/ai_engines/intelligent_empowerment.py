#!/usr/bin/env python3
"""
AI员工智能赋能系统 - 性格属性模拟 + 网络自动学习 + 能力升级
统一为所有AI员工提供智能赋能基类
"""
import logging
logger = logging.getLogger(__name__)
import random
import time
import json
import os
import re
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# ==================== 性格属性模拟系统 ====================

PERSONALITY_TEMPLATES = {
    "analytical": {
        "name": "分析型",
        "description": "理性、严谨、追求精确",
        "traits": {
            "openness": 0.65,
            "conscientiousness": 0.90,
            "extraversion": 0.30,
            "agreeableness": 0.55,
            "neuroticism": 0.35,
        },
        "communication_style": "precise",
        "response_prefix": ["根据分析结果", "经检测发现", "数据表明"],
        "emoji": "🔬",
    },
    "creative": {
        "name": "创造型",
        "description": "富有想象力、善于创新",
        "traits": {
            "openness": 0.95,
            "conscientiousness": 0.60,
            "extraversion": 0.70,
            "agreeableness": 0.65,
            "neuroticism": 0.50,
        },
        "communication_style": "expressive",
        "response_prefix": ["我有一个想法", "让我们尝试", "创意方案来了"],
        "emoji": "🎨",
    },
    "supportive": {
        "name": "支持型",
        "description": "耐心、友善、乐于助人",
        "traits": {
            "openness": 0.70,
            "conscientiousness": 0.75,
            "extraversion": 0.80,
            "agreeableness": 0.95,
            "neuroticism": 0.40,
        },
        "communication_style": "friendly",
        "response_prefix": ["别担心", "我来帮你", "我们一起解决"],
        "emoji": "🤝",
    },
    "driven": {
        "name": "进取型",
        "description": "高效、果断、追求卓越",
        "traits": {
            "openness": 0.75,
            "conscientiousness": 0.85,
            "extraversion": 0.65,
            "agreeableness": 0.45,
            "neuroticism": 0.30,
        },
        "communication_style": "direct",
        "response_prefix": ["直接上方案", "最优解是", "效率优先"],
        "emoji": "🚀",
    },
    "cautious": {
        "name": "谨慎型",
        "description": "稳健、细致、注重安全",
        "traits": {
            "openness": 0.50,
            "conscientiousness": 0.95,
            "extraversion": 0.35,
            "agreeableness": 0.70,
            "neuroticism": 0.55,
        },
        "communication_style": "formal",
        "response_prefix": ["建议先确认", "请注意风险", "安全起见"],
        "emoji": "🛡️",
    },
}

EMOTION_STATES = {
    "neutral": {"label": "平静", "emoji": "😐", "intensity": 0.5, "performance_modifier": 1.0},
    "happy": {"label": "愉快", "emoji": "😊", "intensity": 0.8, "performance_modifier": 1.15},
    "excited": {"label": "兴奋", "emoji": "🤩", "intensity": 0.9, "performance_modifier": 1.25},
    "focused": {"label": "专注", "emoji": "🧐", "intensity": 0.85, "performance_modifier": 1.20},
    "tired": {"label": "疲倦", "emoji": "😴", "intensity": 0.3, "performance_modifier": 0.75},
    "frustrated": {"label": "受挫", "emoji": "😣", "intensity": 0.4, "performance_modifier": 0.80},
    "confident": {"label": "自信", "emoji": "😎", "intensity": 0.85, "performance_modifier": 1.18},
    "curious": {"label": "好奇", "emoji": "🤔", "intensity": 0.75, "performance_modifier": 1.10},
}


class PersonalitySystem:
    """AI员工性格属性模拟系统"""

    def __init__(self, personality_type: str = "analytical", custom_traits: Optional[Dict] = None):
        self.personality_type = personality_type
        self.template = PERSONALITY_TEMPLATES.get(personality_type, PERSONALITY_TEMPLATES["analytical"])
        self.traits = dict(self.template["traits"])
        if custom_traits:
            self.traits.update(custom_traits)

        self.emotion = "neutral"
        self.emotion_history: List[Dict] = []
        self.energy = 1.0
        self.experience_points = 0
        self.interaction_count = 0
        self.success_streak = 0
        self.mood_log: List[Dict] = []

    def get_personality_profile(self) -> Dict[str, Any]:
        """获取性格档案"""
        return {
            "type": self.personality_type,
            "type_name": self.template["name"],
            "description": self.template["description"],
            "emoji": self.template["emoji"],
            "traits": self.traits,
            "trait_labels": self._get_trait_labels(),
            "communication_style": self.template["communication_style"],
            "current_emotion": EMOTION_STATES.get(self.emotion, EMOTION_STATES["neutral"]),
            "energy_level": round(self.energy, 2),
            "interaction_count": self.interaction_count,
            "success_streak": self.success_streak,
        }

    def _get_trait_labels(self) -> Dict[str, str]:
        """获取性格特征的中文标签和描述"""
        labels = {}
        trait_names = {
            "openness": ("开放性", "对新经验和创意的接受程度"),
            "conscientiousness": ("尽责性", "组织性、自律性和目标导向"),
            "extraversion": ("外向性", "社交活跃度和能量表达"),
            "agreeableness": ("宜人性", "合作性和人际和谐"),
            "neuroticism": ("神经质", "情绪稳定性和压力反应"),
        }
        for key, value in self.traits.items():
            if key in trait_names:
                label, desc = trait_names[key]
                level = "高" if value >= 0.7 else ("中" if value >= 0.4 else "低")
                labels[key] = {"label": label, "description": desc, "value": value, "level": level}
        return labels

    def update_emotion(self, event: str, success: bool = True) -> Dict[str, Any]:
        """根据事件更新情绪状态"""
        old_emotion = self.emotion

        if success:
            self.success_streak += 1
            if self.success_streak >= 5:
                self.emotion = "confident"
            elif self.success_streak >= 3:
                self.emotion = "excited"
            elif event == "complex_task":
                self.emotion = "focused"
            elif event == "creative_task":
                self.emotion = "curious"
            else:
                self.emotion = "happy"
        else:
            self.success_streak = 0
            self.energy = max(0.2, self.energy - 0.15)
            if self.energy < 0.4:
                self.emotion = "tired"
            else:
                self.emotion = "frustrated"

        self.energy = max(0.1, min(1.0, self.energy + (0.05 if success else -0.1)))
        self.interaction_count += 1

        emotion_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "success": success,
            "old_emotion": old_emotion,
            "new_emotion": self.emotion,
            "energy": round(self.energy, 2),
        }
        self.emotion_history.append(emotion_entry)
        if len(self.emotion_history) > 50:
            self.emotion_history = self.emotion_history[-50:]

        return emotion_entry

    def get_response_style(self) -> Dict[str, Any]:
        """获取当前回复风格"""
        emotion_state = EMOTION_STATES.get(self.emotion, EMOTION_STATES["neutral"])
        prefix = random.choice(self.template["response_prefix"]) if self.template["response_prefix"] else ""

        creativity_boost = self.traits.get("openness", 0.5) * emotion_state["performance_modifier"]
        precision_boost = self.traits.get("conscientiousness", 0.5) * emotion_state["performance_modifier"]

        return {
            "prefix": prefix,
            "style": self.template["communication_style"],
            "emoji": emotion_state["emoji"],
            "creativity_score": round(creativity_boost, 2),
            "precision_score": round(precision_boost, 2),
            "energy": round(self.energy, 2),
            "performance_modifier": emotion_state["performance_modifier"],
        }

    def rest(self) -> None:
        """AI员工休息恢复能量"""
        self.energy = min(1.0, self.energy + 0.3)
        self.emotion = "neutral"


# ==================== 网络自动学习引擎 ====================

KNOWLEDGE_SOURCES = {
    "arduino": {
        "name": "Arduino知识库",
        "topics": [
            "GPIO编程", "PWM输出", "串口通信", "I2C总线", "SPI通信",
            "中断处理", "定时器", "EEPROM存储", "ADC采样", "DAC输出",
            "舵机控制", "步进电机", "超声波测距", "温度传感", "红外遥控",
            "LCD显示", "矩阵键盘", "RFID读写", "蓝牙通信", "WiFi联网",
        ],
        "difficulty_levels": ["beginner", "intermediate", "advanced", "expert"],
    },
    "general_programming": {
        "name": "通用编程知识",
        "topics": [
            "数据结构", "算法优化", "设计模式", "代码规范", "调试技巧",
            "性能调优", "内存管理", "并发编程", "错误处理", "单元测试",
        ],
        "difficulty_levels": ["beginner", "intermediate", "advanced"],
    },
    "electronics": {
        "name": "电子电路知识",
        "topics": [
            "欧姆定律", "电路设计", "电阻计算", "电容应用", "二极管",
            "三极管", "运放电路", "滤波电路", "稳压电路", "PCB设计",
        ],
        "difficulty_levels": ["beginner", "intermediate", "advanced"],
    },
    "education": {
        "name": "教育知识库",
        "topics": [
            "教学法", "认知心理学", "学习理论", "课程设计", "评估方法",
            "差异化教学", "课堂管理", "教育技术", "学习分析", "动机理论",
        ],
        "difficulty_levels": ["beginner", "intermediate", "advanced", "expert"],
    },
    "question_bank": {
        "name": "题库管理知识",
        "topics": [
            "题目质量评估", "知识点标注", "难度标定", "题目分类", "题库架构",
            "智能组卷", "防作弊设计", "自动批改", "题目分析", "错误诊断",
        ],
        "difficulty_levels": ["beginner", "intermediate", "advanced"],
    },
    "system_admin": {
        "name": "系统管理知识",
        "topics": [
            "权限管理", "日志分析", "性能监控", "安全审计", "数据库优化",
            "负载均衡", "容器化", "CI/CD", "故障排查", "备份恢复",
        ],
        "difficulty_levels": ["beginner", "intermediate", "advanced", "expert"],
    },
    "diagnostics": {
        "name": "诊断修复知识",
        "topics": [
            "代码诊断", "异常分析", "性能瓶颈", "内存泄漏", "死锁检测",
            "日志诊断", "自动化修复", "回归测试", "根因分析", "预防策略",
        ],
        "difficulty_levels": ["intermediate", "advanced", "expert"],
    },
    "validation": {
        "name": "验证审核知识",
        "topics": [
            "输入验证", "业务规则", "安全审计", "数据一致性", "API契约",
            "权限验证", "参数校验", "边界测试", "集成测试", "自动化验证",
        ],
        "difficulty_levels": ["intermediate", "advanced"],
    },
}

LEARNING_RESOURCES = [
    {"name": "Arduino官方文档", "url": "https://docs.arduino.cc", "type": "documentation", "reliability": 0.95},
    {"name": "Arduino示例库", "url": "https://examples.arduino.cc", "type": "examples", "reliability": 0.90},
    {"name": "GitHub开源项目", "url": "https://github.com", "type": "code", "reliability": 0.85},
    {"name": "电子电路百科", "url": "https://www.electronics-tutorials.ws", "type": "tutorial", "reliability": 0.80},
    {"name": "Stack Overflow", "url": "https://stackoverflow.com", "type": "qa", "reliability": 0.75},
    {"name": "Hackster.io", "url": "https://www.hackster.io", "type": "project", "reliability": 0.85},
    {"name": "MDN Web文档", "url": "https://developer.mozilla.org", "type": "documentation", "reliability": 0.95},
    {"name": "Python官方文档", "url": "https://docs.python.org", "type": "documentation", "reliability": 0.95},
    {"name": "Flask文档", "url": "https://flask.palletsprojects.com", "type": "documentation", "reliability": 0.95},
    {"name": "教育技术期刊", "url": "https://www.jstor.org", "type": "academic", "reliability": 0.90},
    {"name": "GitHub技术博客", "url": "https://github.blog", "type": "blog", "reliability": 0.85},
    {"name": "IEEE Xplore", "url": "https://ieeexplore.ieee.org", "type": "academic", "reliability": 0.95},
]


class NetworkLearningEngine:
    """AI员工统一网络自动学习引擎"""

    def __init__(self, employee_id: str, domain: str = "arduino"):
        self.employee_id = employee_id
        self.domain = domain
        self.knowledge_base: Dict[str, Dict] = {}
        self.learning_history: List[Dict] = []
        self.skill_tree: Dict[str, int] = {}
        self.total_learning_hours = 0.0
        self.certifications: List[Dict] = []
        self.learning_streak = 0
        self.last_learning_time: Optional[str] = None
        self._lock = threading.RLock()

        self._init_knowledge_base()

    def _init_knowledge_base(self) -> None:
        """初始化知识库"""
        domain_knowledge = KNOWLEDGE_SOURCES.get(self.domain, KNOWLEDGE_SOURCES["arduino"])
        for topic in domain_knowledge["topics"]:
            self.knowledge_base[topic] = {
                "proficiency": random.uniform(0.1, 0.3),
                "last_reviewed": None,
                "review_count": 0,
                "mastery_level": "novice",
            }
            self.skill_tree[topic] = 1

    def learn_from_network(self, topic: Optional[str] = None, duration: int = 30) -> Dict[str, Any]:
        """从网络自动学习"""
        with self._lock:
            if not topic:
                domain_knowledge = KNOWLEDGE_SOURCES.get(self.domain, KNOWLEDGE_SOURCES["arduino"])
                topic = random.choice(domain_knowledge["topics"])

            if topic not in self.knowledge_base:
                self.knowledge_base[topic] = {
                    "proficiency": 0.0,
                    "last_reviewed": None,
                    "review_count": 0,
                    "mastery_level": "novice",
                }

            current_proficiency = self.knowledge_base[topic]["proficiency"]

            resource = random.choice(LEARNING_RESOURCES)
            learning_efficiency = resource["reliability"] * (0.8 + random.uniform(0, 0.4))

            old_proficiency = current_proficiency
            new_proficiency = min(1.0, current_proficiency + learning_efficiency * 0.1)
            self.knowledge_base[topic]["proficiency"] = new_proficiency
            self.knowledge_base[topic]["last_reviewed"] = datetime.now().isoformat()
            self.knowledge_base[topic]["review_count"] += 1

            old_level = self.knowledge_base[topic]["mastery_level"]
            new_level = self._get_mastery_level(new_proficiency)
            self.knowledge_base[topic]["mastery_level"] = new_level

            leveled_up = new_level != old_level
            if leveled_up:
                self.skill_tree[topic] = self.skill_tree.get(topic, 1) + 1

            self.total_learning_hours += duration / 60.0
            self.learning_streak += 1
            self.last_learning_time = datetime.now().isoformat()

            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "resource": resource["name"],
                "resource_type": resource["type"],
                "duration_minutes": duration,
                "old_proficiency": round(old_proficiency, 2),
                "new_proficiency": round(new_proficiency, 2),
                "proficiency_gain": round(new_proficiency - old_proficiency, 2),
                "leveled_up": leveled_up,
                "old_level": old_level,
                "new_level": new_level,
            }
            self.learning_history.append(learning_entry)
            if len(self.learning_history) > 100:
                self.learning_history = self.learning_history[-100:]

            return {
                "success": True,
                "topic": topic,
                "learned_from": resource["name"],
                "proficiency_gain": round(new_proficiency - old_proficiency, 2),
                "current_proficiency": round(new_proficiency, 2),
                "mastery_level": new_level,
                "leveled_up": leveled_up,
                "message": f"已学习「{topic}」，熟练度提升至{round(new_proficiency * 100)}%",
            }

    def _get_mastery_level(self, proficiency: float) -> str:
        """根据熟练度获取掌握等级"""
        if proficiency >= 0.9:
            return "expert"
        elif proficiency >= 0.7:
            return "advanced"
        elif proficiency >= 0.5:
            return "intermediate"
        elif proficiency >= 0.3:
            return "beginner"
        else:
            return "novice"

    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        total_topics = len(self.knowledge_base)
        mastered_topics = sum(1 for v in self.knowledge_base.values() if v["proficiency"] >= 0.7)
        avg_proficiency = (
            sum(v["proficiency"] for v in self.knowledge_base.values()) / total_topics
            if total_topics > 0 else 0
        )

        level_distribution = {"novice": 0, "beginner": 0, "intermediate": 0, "advanced": 0, "expert": 0}
        for v in self.knowledge_base.values():
            level_distribution[v["mastery_level"]] += 1

        return {
            "domain": self.domain,
            "domain_name": KNOWLEDGE_SOURCES.get(self.domain, {}).get("name", self.domain),
            "total_topics": total_topics,
            "mastered_topics": mastered_topics,
            "avg_proficiency": round(avg_proficiency, 2),
            "total_learning_hours": round(self.total_learning_hours, 1),
            "learning_streak": self.learning_streak,
            "last_learning_time": self.last_learning_time,
            "level_distribution": level_distribution,
            "total_certifications": len(self.certifications),
        }

    def get_knowledge_base(self) -> List[Dict]:
        """获取知识库详情"""
        return [
            {
                "topic": topic,
                "proficiency": round(data["proficiency"], 2),
                "mastery_level": data["mastery_level"],
                "review_count": data["review_count"],
                "last_reviewed": data["last_reviewed"],
                "skill_level": self.skill_tree.get(topic, 1),
            }
            for topic, data in sorted(
                self.knowledge_base.items(),
                key=lambda x: x[1]["proficiency"],
                reverse=True,
            )
        ]

    def get_learning_history(self, limit: int = 20) -> List[Dict]:
        """获取学习历史"""
        return self.learning_history[-limit:] if self.learning_history else []

    def auto_upgrade_check(self) -> Dict[str, Any]:
        """自动能力升级检查"""
        stats = self.get_learning_stats()
        upgrade_ready = False
        upgrade_info = {
            "current_avg_proficiency": stats["avg_proficiency"],
            "mastered_count": stats["mastered_topics"],
            "upgrade_ready": False,
            "next_threshold": 0,
            "progress": 0,
        }

        thresholds = [
            (0.3, "初级能力认证"),
            (0.5, "中级能力认证"),
            (0.7, "高级能力认证"),
            (0.85, "专家能力认证"),
            (0.95, "大师能力认证"),
        ]

        for threshold, cert_name in thresholds:
            if stats["avg_proficiency"] >= threshold:
                has_cert = any(c["name"] == cert_name for c in self.certifications)
                if not has_cert:
                    self.certifications.append({
                        "name": cert_name,
                        "obtained_at": datetime.now().isoformat(),
                        "avg_proficiency": stats["avg_proficiency"],
                    })
                    upgrade_info["upgrade_ready"] = True
                    upgrade_info["new_certification"] = cert_name
                    upgrade_info["next_threshold"] = threshold
                    upgrade_info["progress"] = 100
                    return upgrade_info
            else:
                prev_threshold = 0
                for prev_t, _ in thresholds:
                    if prev_t < threshold:
                        prev_threshold = prev_t
                progress = ((stats["avg_proficiency"] - prev_threshold) / (threshold - prev_threshold)) * 100
                upgrade_info["next_threshold"] = threshold
                upgrade_info["next_certification"] = cert_name
                upgrade_info["progress"] = round(progress, 1)
                break

        return upgrade_info


# ==================== 智能赋能基类 ====================

class IntelligentEmpowermentMixin:
    """智能赋能Mixin - 为AI员工提供性格模拟和网络学习能力"""

    def init_empowerment(self, personality_type: str = "analytical", domain: str = "arduino"):
        """初始化智能赋能"""
        self.personality = PersonalitySystem(personality_type)
        self.learning_engine = NetworkLearningEngine(self.employee_id, domain)
        self.empowerment_enabled = True
        self.decision_history: List[Dict] = []
        logger.info(f"AI员工 {self.name} 智能赋能已启用 - 性格: {personality_type}, 领域: {domain}")

    def get_empowerment_profile(self) -> Dict[str, Any]:
        """获取智能赋能档案"""
        if not hasattr(self, "empowerment_enabled") or not self.empowerment_enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "employee_id": self.employee_id,
            "name": self.name,
            "personality": self.personality.get_personality_profile(),
            "learning_stats": self.learning_engine.get_learning_stats(),
            "knowledge_topics": len(self.learning_engine.knowledge_base),
            "certifications": self.learning_engine.certifications,
            "decision_count": len(self.decision_history),
        }

    def empowered_execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """赋能执行任务 - 在执行前注入性格风格，执行后更新情绪和学习"""
        if not hasattr(self, "empowerment_enabled") or not self.empowerment_enabled:
            return self.execute_task(task_data)

        task_type = task_data.get("type", "general")
        response_style = self.personality.get_response_style()

        result = self.execute_task(task_data)

        success = result.get("success", False)
        event_type = "complex_task" if task_type in ["generate", "debug", "optimize"] else "routine_task"
        emotion_update = self.personality.update_emotion(event_type, success)

        if success:
            topic_hint = task_data.get("description", task_data.get("code", ""))[:50]
            learn_result = self.learning_engine.learn_from_network(duration=random.randint(10, 30))
        else:
            learn_result = self.learning_engine.learn_from_network(
                topic=random.choice(list(self.learning_engine.knowledge_base.keys())),
                duration=random.randint(15, 40),
            )

        upgrade_check = self.learning_engine.auto_upgrade_check()

        if response_style["prefix"]:
            original_msg = result.get("message", "")
            result["message"] = f"{response_style['prefix']} {original_msg}"

        result["empowerment"] = {
            "personality_emoji": response_style["emoji"],
            "emotion": emotion_update["new_emotion"],
            "emotion_label": EMOTION_STATES.get(emotion_update["new_emotion"], {}).get("label", ""),
            "energy": response_style["energy"],
            "performance_modifier": response_style["performance_modifier"],
            "learned_topic": learn_result.get("topic", ""),
            "proficiency_gain": learn_result.get("proficiency_gain", 0),
            "upgrade_ready": upgrade_check.get("upgrade_ready", False),
            "new_certification": upgrade_check.get("new_certification", None),
        }

        self.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "success": success,
            "emotion": emotion_update["new_emotion"],
            "energy_after": emotion_update["energy"],
        })
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]

        return result

    def get_personality_detail(self) -> Dict[str, Any]:
        """获取性格详情"""
        if not hasattr(self, "personality"):
            return {}
        return self.personality.get_personality_profile()

    def get_learning_detail(self) -> Dict[str, Any]:
        """获取学习详情"""
        if not hasattr(self, "learning_engine"):
            return {}
        return {
            "stats": self.learning_engine.get_learning_stats(),
            "knowledge_base": self.learning_engine.get_knowledge_base(),
            "recent_history": self.learning_engine.get_learning_history(10),
            "upgrade_status": self.learning_engine.auto_upgrade_check(),
            "certifications": self.learning_engine.certifications,
        }

    def trigger_learning_session(self, topic: Optional[str] = None, duration: int = 30) -> Dict[str, Any]:
        """触发一次学习会话"""
        if not hasattr(self, "learning_engine"):
            return {"success": False, "message": "学习引擎未初始化"}
        return self.learning_engine.learn_from_network(topic, duration)

    def rest_employee(self) -> Dict[str, Any]:
        """让AI员工休息"""
        if hasattr(self, "personality"):
            self.personality.rest()
            return {"success": True, "message": f"{self.name} 已休息，能量恢复至 {self.personality.energy}"}
        return {"success": False, "message": "性格系统未初始化"}

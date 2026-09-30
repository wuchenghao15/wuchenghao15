# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Education AI System - 教育AI系统
包含教研员AI、专家AI、教师AI、学生AI
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re
import os

class EducationalAI:
    """教育AI基类"""
    
    def __init__(self, role: str, name: str):
        self.role = role
        self.name = name
        self.knowledge_base = {}
        self.experience = 0
        self.specializations = []
    
    def get_role(self) -> str:
        return self.role
    
    def get_name(self) -> str:
        return self.name
    
    def add_knowledge(self, topic: str, content: Any):
        self.knowledge_base[topic] = content
    
    def get_knowledge(self, topic: str) -> Optional[Any]:
        return self.knowledge_base.get(topic)
    
    def add_specialization(self, spec: str):
        if spec not in self.specializations:
            self.specializations.append(spec)


class ResearcherAI(EducationalAI):
    """教研员AI - 教学研究和课程设计专家"""
    
    def __init__(self, name: str = "教研员AI"):
        super().__init__("researcher", name)
        self.curriculum_expertise = []
        self.education_policies = {}
        self.research_projects = []
    
    def analyze_curriculum(self, curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析教学大纲"""
        analysis = {
            "curriculum_name": curriculum_data.get("name", "Unknown"),
            "subject": curriculum_data.get("subject", "Unknown"),
            "grade_level": curriculum_data.get("grade_level", "Unknown"),
            "analysis": {},
            "suggestions": []
        }
        
        objectives = curriculum_data.get("objectives", [])
        if objectives:
            analysis["analysis"]["total_objectives"] = len(objectives)
            analysis["analysis"]["cognitive_levels"] = self._analyze_cognitive_levels(objectives)
        
        topics = curriculum_data.get("topics", [])
        if topics:
            analysis["analysis"]["total_topics"] = len(topics)
            analysis["analysis"]["topic_distribution"] = self._analyze_topic_distribution(topics)
            analysis["suggestions"].extend(self._generate_curriculum_suggestions(topics))
        
        return analysis
    
    def _analyze_cognitive_levels(self, objectives: List[str]) -> Dict[str, int]:
        """分析认知层次"""
        levels = {
            "记忆": 0,
            "理解": 0,
            "应用": 0,
            "分析": 0,
            "评价": 0,
            "创造": 0
        }
        
        level_keywords = {
            "记忆": ["记住", "回忆", "识别", "列举", "复述"],
            "理解": ["解释", "说明", "描述", "比较", "归纳"],
            "应用": ["应用", "运用", "解决", "实践", "操作"],
            "分析": ["分析", "分解", "比较", "对比", "推断"],
            "评价": ["评价", "评估", "判断", "论证", "批判"],
            "创造": ["创造", "设计", "构建", "创新", "综合"]
        }
        
        for objective in objectives:
            for level, keywords in level_keywords.items():
                if any(kw in objective for kw in keywords):
                    levels[level] += 1
        
        return levels
    
    def _analyze_topic_distribution(self, topics: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析主题分布"""
        distribution = {}
        for topic in topics:
            category = topic.get("category", "其他")
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def _generate_curriculum_suggestions(self, topics: List[Dict[str, Any]]) -> List[str]:
        """生成课程改进建议"""
        suggestions = []
        
        if len(topics) < 5:
            suggestions.append("建议增加更多主题以丰富课程内容")
        
        topic_names = [t.get("name", "") for t in topics]
        if "实践" not in "".join(topic_names):
            suggestions.append("建议增加实践环节，提升学生动手能力")
        
        return suggestions
    
    def design_course(self, subject: str, grade_level: str, duration: int) -> Dict[str, Any]:
        """设计课程方案"""
        return {
            "course_name": f"{subject}课程方案",
            "grade_level": grade_level,
            "duration_hours": duration,
            "modules": self._generate_modules(subject, duration),
            "assessment_methods": ["课堂测验", "作业", "项目报告", "期末考试"],
            "resources_needed": ["教材", "实验设备", "在线平台", "参考资料"]
        }
    
    def _generate_modules(self, subject: str, duration: int) -> List[Dict[str, Any]]:
        """生成课程模块"""
        modules = []
        num_modules = max(3, duration // 4)
        
        for i in range(num_modules):
            modules.append({
                "module_number": i + 1,
                "title": f"{subject}模块{i + 1}",
                "hours": duration // num_modules,
                "topics": ["主题A", "主题B", "主题C"],
                "learning_objectives": ["掌握基本概念", "理解核心原理", "能够应用解决问题"]
            })
        
        return modules


class ExpertAI(EducationalAI):
    """专家AI - 学科专业知识专家"""
    
    def __init__(self, name: str = "专家AI"):
        super().__init__("expert", name)
        self.subjects = []
        self.publications = []
        self.expertise_level = "高级"
    
    def set_subjects(self, subjects: List[str]):
        self.subjects = subjects
    
    def generate_knowledge_points(self, topic: str, depth: int = 3) -> Dict[str, Any]:
        """生成知识点体系"""
        knowledge = {
            "topic": topic,
            "depth": depth,
            "knowledge_tree": self._build_knowledge_tree(topic, depth)
        }
        return knowledge
    
    def _build_knowledge_tree(self, topic: str, depth: int) -> Dict[str, Any]:
        """构建知识树"""
        if depth <= 0:
            return {}
        
        base_points = {
            "数学": ["代数", "几何", "概率统计", "微积分"],
            "物理": ["力学", "电磁学", "光学", "热学"],
            "化学": ["无机化学", "有机化学", "分析化学", "物理化学"],
            "语文": ["阅读", "写作", "文言文", "诗词鉴赏"],
            "英语": ["词汇", "语法", "阅读", "写作"]
        }
        
        second_level = {
            "代数": ["方程", "函数", "不等式", "数列"],
            "几何": ["平面几何", "立体几何", "解析几何"],
            "力学": ["运动学", "动力学", "能量守恒"],
            "电磁学": ["静电场", "恒定电流", "磁场"]
        }
        
        result = {"name": topic, "children": []}
        
        if topic in base_points:
            for subtopic in base_points[topic][:3]:
                child = {"name": subtopic, "children": []}
                if subtopic in second_level and depth > 1:
                    for detail in second_level[subtopic][:2]:
                        child["children"].append({"name": detail})
                result["children"].append(child)
        
        return result
    
    def answer_question(self, question: str, subject: str = "") -> Dict[str, Any]:
        """回答学科问题"""
        analysis = self._analyze_question(question, subject)
        
        return {
            "question": question,
            "subject": subject,
            "analysis": analysis,
            "answer": self._generate_answer(question, analysis),
            "related_knowledge": self._find_related_knowledge(question, subject),
            "difficulty_level": self._estimate_difficulty(question)
        }
    
    def _analyze_question(self, question: str, subject: str) -> Dict[str, Any]:
        """分析问题"""
        analysis = {
            "question_type": self._detect_question_type(question),
            "keywords": self._extract_keywords(question),
            "complexity": "中等"
        }
        return analysis
    
    def _detect_question_type(self, question: str) -> str:
        """检测问题类型"""
        if "为什么" in question or "原因" in question:
            return "原因分析"
        elif "如何" in question or "方法" in question:
            return "方法步骤"
        elif "证明" in question or "推导" in question:
            return "证明推导"
        elif "比较" in question or "区别" in question:
            return "比较对比"
        return "综合分析"
    
    def _extract_keywords(self, question: str) -> List[str]:
        """提取关键词"""
        keywords = []
        subject_keywords = {
            "数学": ["方程", "函数", "几何", "概率", "导数"],
            "物理": ["力", "速度", "能量", "电场", "磁场"],
            "化学": ["反应", "元素", "化合物", "溶液", "平衡"]
        }
        
        for subject, terms in subject_keywords.items():
            for term in terms:
                if term in question:
                    keywords.append(term)
        
        return keywords
    
    def _generate_answer(self, question: str, analysis: Dict[str, Any]) -> str:
        """生成答案"""
        return f"针对问题 '{question}' 的详细解答：\n\n1. 核心概念解析\n2. 相关原理说明\n3. 具体应用示例\n4. 拓展思考"
    
    def _find_related_knowledge(self, question: str, subject: str) -> List[str]:
        """查找相关知识"""
        return ["知识点A", "知识点B", "知识点C"]
    
    def _estimate_difficulty(self, question: str) -> str:
        """估算难度"""
        if len(question) > 50:
            return "较难"
        elif len(question) > 30:
            return "中等"
        return "较易"


class TeacherAI(EducationalAI):
    """教师AI - 辅助教学工作"""
    
    def __init__(self, name: str = "教师AI"):
        super().__init__("teacher", name)
        self.teaching_strategies = []
        self.student_profiles = {}
        self.classes = []
    
    def generate_lesson_plan(self, topic: str, duration: int, grade_level: str) -> Dict[str, Any]:
        """生成教案"""
        return {
            "topic": topic,
            "duration_minutes": duration,
            "grade_level": grade_level,
            "teaching_objectives": self._define_objectives(topic),
            "teaching_procedures": self._design_procedures(duration),
            "teaching_methods": ["讲授法", "讨论法", "案例教学", "小组活动"],
            "assessment": self._design_assessment(),
            "homework": self._assign_homework(topic)
        }
    
    def _define_objectives(self, topic: str) -> List[str]:
        """定义教学目标"""
        return [
            f"理解{topic}的基本概念",
            f"掌握{topic}的核心原理",
            f"能够运用{topic}知识解决实际问题"
        ]
    
    def _design_procedures(self, duration: int) -> List[Dict[str, Any]]:
        """设计教学流程"""
        procedures = []
        
        if duration >= 45:
            procedures.extend([
                {"环节": "导入", "时间": 5, "内容": "复习旧知识，引入新课"},
                {"环节": "讲解", "时间": 20, "内容": "核心知识点讲解"},
                {"环节": "练习", "时间": 15, "内容": "课堂练习巩固"},
                {"环节": "总结", "时间": 5, "内容": "总结归纳，布置作业"}
            ])
        
        return procedures
    
    def _design_assessment(self) -> Dict[str, Any]:
        """设计评估方式"""
        return {
            "formative": ["课堂提问", "小组讨论", "随堂测验"],
            "summative": ["单元测试", "作业评价", "项目报告"]
        }
    
    def _assign_homework(self, topic: str) -> Dict[str, Any]:
        """布置作业"""
        return {
            "练习": f"完成{topic}相关练习题3-5道",
            "拓展": f"查阅{topic}相关资料，写一篇小短文",
            "预习": "预习下一章节内容"
        }
    
    def analyze_student_progress(self, student_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析学生学习进度"""
        return {
            "student_id": student_id,
            "overall_progress": self._calculate_progress(data),
            "strengths": self._identify_strengths(data),
            "weaknesses": self._identify_weaknesses(data),
            "suggestions": self._generate_improvement_suggestions(data)
        }
    
    def _calculate_progress(self, data: Dict[str, Any]) -> float:
        """计算总体进度"""
        completed = data.get("completed_tasks", 0)
        total = data.get("total_tasks", 1)
        return min(100, (completed / total) * 100)
    
    def _identify_strengths(self, data: Dict[str, Any]) -> List[str]:
        """识别优势"""
        strengths = []
        if data.get("quiz_scores", {}).get("average", 0) > 80:
            strengths.append("基础知识扎实")
        if data.get("participation", 0) > 8:
            strengths.append("课堂参与积极")
        return strengths
    
    def _identify_weaknesses(self, data: Dict[str, Any]) -> List[str]:
        """识别薄弱环节"""
        weaknesses = []
        if data.get("quiz_scores", {}).get("average", 0) < 60:
            weaknesses.append("需要加强基础知识")
        if data.get("homework_completion", 0) < 80:
            weaknesses.append("作业完成率有待提高")
        return weaknesses
    
    def _generate_improvement_suggestions(self, data: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        if "需要加强基础知识" in self._identify_weaknesses(data):
            suggestions.append("建议每天花30分钟复习基础概念")
        if "作业完成率有待提高" in self._identify_weaknesses(data):
            suggestions.append("制定学习计划，按时完成作业")
        return suggestions
    
    def create_quiz(self, topic: str, num_questions: int = 5) -> Dict[str, Any]:
        """创建测验题"""
        questions = []
        for i in range(num_questions):
            questions.append({
                "question_id": f"q{i+1}",
                "question_type": self._random_question_type(),
                "content": self._generate_question_content(topic, i),
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                "correct_answer": "A",
                "difficulty": self._random_difficulty()
            })
        
        return {
            "topic": topic,
            "total_questions": num_questions,
            "questions": questions,
            "time_limit_minutes": num_questions * 5
        }
    
    def _random_question_type(self) -> str:
        """随机选择题型"""
        types = ["单选题", "多选题", "填空题", "判断题"]
        return types[hash(self.name) % len(types)]
    
    def _generate_question_content(self, topic: str, index: int) -> str:
        """生成题目内容"""
        return f"{topic}相关问题{index + 1}：关于{topic}的核心概念是什么？"
    
    def _random_difficulty(self) -> str:
        """随机难度"""
        levels = ["简单", "中等", "较难"]
        return levels[hash(datetime.now()) % len(levels)]


class StudentAI(EducationalAI):
    """学生AI - 辅助学生学习"""
    
    def __init__(self, name: str = "学生AI"):
        super().__init__("student", name)
        self.learning_goals = []
        self.progress = {}
        self.learning_style = "visual"
    
    def set_learning_goals(self, goals: List[str]):
        """设置学习目标"""
        self.learning_goals = goals
    
    def get_learning_path(self, subject: str, current_level: str = "入门") -> List[Dict[str, Any]]:
        """获取学习路径"""
        paths = {
            "入门": [
                {"阶段": "基础概念", "时长": "1-2周", "重点": "理解基本定义"},
                {"阶段": "简单应用", "时长": "2-3周", "重点": "掌握基础题型"}
            ],
            "进阶": [
                {"阶段": "深入理解", "时长": "3-4周", "重点": "掌握核心原理"},
                {"阶段": "综合应用", "时长": "4-6周", "重点": "解决复杂问题"}
            ],
            "高级": [
                {"阶段": "拓展深化", "时长": "4-6周", "重点": "研究性学习"},
                {"阶段": "创新应用", "时长": "6-8周", "重点": "知识创新"}
            ]
        }
        
        return paths.get(current_level, paths["入门"])
    
    def study_recommendation(self, subject: str, time_available: int) -> Dict[str, Any]:
        """学习推荐"""
        recommendations = {
            "subject": subject,
            "time_available_minutes": time_available,
            "plan": self._create_study_plan(subject, time_available),
            "resources": self._suggest_resources(subject),
            "tips": self._learning_tips(subject)
        }
        return recommendations
    
    def _create_study_plan(self, subject: str, time: int) -> List[Dict[str, Any]]:
        """创建学习计划"""
        plan = []
        
        if time >= 60:
            plan.extend([
                {"活动": "复习旧知识", "时间": 15, "内容": "回顾上次学习内容"},
                {"活动": "学习新知识", "时间": 30, "内容": f"{subject}新知识点学习"},
                {"活动": "练习巩固", "时间": 15, "内容": "完成相关练习题"}
            ])
        elif time >= 30:
            plan.append({"活动": "重点突破", "时间": 30, "内容": f"{subject}薄弱环节专项练习"})
        
        return plan
    
    def _suggest_resources(self, subject: str) -> List[str]:
        """推荐学习资源"""
        resources = {
            "数学": ["教材章节", "在线课程视频", "练习题集", "数学学习APP"],
            "物理": ["实验视频", "模拟仿真软件", "物理公式手册", "科普文章"],
            "化学": ["实验演示", "分子模型软件", "元素周期表", "化学反应库"],
            "语文": ["经典名著", "阅读材料", "写作范文", "诗词赏析"],
            "英语": ["单词APP", "听力材料", "阅读文章", "口语练习"]
        }
        
        return resources.get(subject, ["教材", "参考书籍", "在线资源"])
    
    def _learning_tips(self, subject: str) -> List[str]:
        """学习技巧"""
        tips = {
            "数学": ["多做练习，总结规律", "理解公式推导过程", "错题整理复习"],
            "物理": ["理解物理模型", "多做实验观察", "画图辅助分析"],
            "化学": ["记忆化学反应规律", "理解原子结构", "多做实验练习"],
            "语文": ["多读多写", "积累词汇", "分析文章结构"],
            "英语": ["多听多说", "背诵范文", "积累句型"]
        }
        
        return tips.get(subject, ["保持专注", "定期复习", "做好笔记"])
    
    def ask_question(self, question: str, context: str = "") -> Dict[str, Any]:
        """提问"""
        return {
            "question": question,
            "context": context,
            "analysis": self._analyze_question(question),
            "possible_answers": self._generate_possible_answers(question),
            "next_steps": self._suggest_next_steps(question)
        }
    
    def _analyze_question(self, question: str) -> str:
        """分析问题"""
        if "是什么" in question:
            return "定义类问题"
        elif "为什么" in question:
            return "原因类问题"
        elif "怎么做" in question:
            return "方法类问题"
        return "综合类问题"
    
    def _generate_possible_answers(self, question: str) -> List[str]:
        """生成可能的答案方向"""
        return [
            "答案方向A：从基本概念入手",
            "答案方向B：参考相关例题",
            "答案方向C：查阅教材相关章节"
        ]
    
    def _suggest_next_steps(self, question: str) -> List[str]:
        """建议下一步"""
        return [
            "1. 回顾相关知识点",
            "2. 尝试独立思考解答",
            "3. 查阅参考资料",
            "4. 向老师或同学请教"
        ]


class QuestionBankOptimizer:
    """题库优化器"""
    
    def __init__(self):
        self.question_types = ["单选题", "多选题", "填空题", "判断题", "问答题", "计算题"]
        self.difficulty_levels = ["简单", "较易", "中等", "较难", "困难"]
        self.cognitive_levels = ["记忆", "理解", "应用", "分析", "评价", "创造"]
    
    def optimize_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """优化单道题目"""
        optimized = question.copy()
        
        if "difficulty" not in optimized:
            optimized["difficulty"] = self._calculate_difficulty(question)
        
        if "cognitive_level" not in optimized:
            optimized["cognitive_level"] = self._determine_cognitive_level(question)
        
        if "tags" not in optimized:
            optimized["tags"] = self._generate_tags(question)
        
        if "usage_count" not in optimized:
            optimized["usage_count"] = 0
        
        if "last_used_at" not in optimized:
            optimized["last_used_at"] = datetime.now().isoformat()
        
        return optimized
    
    def _calculate_difficulty(self, question: Dict[str, Any]) -> str:
        """计算难度"""
        content = question.get("content", "")
        options = question.get("options", [])
        
        if len(content) < 30:
            return "简单"
        elif len(content) < 60:
            return "较易"
        elif len(content) < 100:
            return "中等"
        elif len(options) > 4:
            return "较难"
        return "困难"
    
    def _determine_cognitive_level(self, question: Dict[str, Any]) -> str:
        """确定认知层次"""
        content = question.get("content", "")
        
        level_keywords = {
            "记忆": ["定义", "名称", "属于", "包括", "列举"],
            "理解": ["解释", "说明", "描述", "含义", "区别"],
            "应用": ["应用", "计算", "求解", "设计", "解决"],
            "分析": ["分析", "比较", "对比", "原因", "推理"],
            "评价": ["评价", "判断", "论证", "优缺点", "建议"],
            "创造": ["创造", "设计", "构建", "开发", "创新"]
        }
        
        for level, keywords in level_keywords.items():
            if any(kw in content for kw in keywords):
                return level
        
        return "理解"
    
    def _generate_tags(self, question: Dict[str, Any]) -> List[str]:
        """生成标签"""
        tags = []
        subject = question.get("subject", "")
        topic = question.get("topic", "")
        
        if subject:
            tags.append(subject)
        if topic:
            tags.append(topic)
        
        tags.append(question.get("difficulty", "中等"))
        tags.append(question.get("question_type", "单选题"))
        
        return tags
    
    def analyze_bank_quality(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析题库质量"""
        if not questions:
            return {"error": "没有题目数据"}
        
        stats = {
            "total_questions": len(questions),
            "question_type_distribution": {},
            "difficulty_distribution": {},
            "cognitive_level_distribution": {},
            "subject_distribution": {},
            "quality_score": 0,
            "suggestions": []
        }
        
        for q in questions:
            q_type = q.get("question_type", "未知")
            stats["question_type_distribution"][q_type] = stats["question_type_distribution"].get(q_type, 0) + 1
            
            difficulty = q.get("difficulty", "中等")
            stats["difficulty_distribution"][difficulty] = stats["difficulty_distribution"].get(difficulty, 0) + 1
            
            cognitive = q.get("cognitive_level", "理解")
            stats["cognitive_level_distribution"][cognitive] = stats["cognitive_level_distribution"].get(cognitive, 0) + 1
            
            subject = q.get("subject", "未知")
            stats["subject_distribution"][subject] = stats["subject_distribution"].get(subject, 0) + 1
        
        stats["quality_score"] = self._calculate_quality_score(stats)
        stats["suggestions"] = self._generate_quality_suggestions(stats)
        
        return stats
    
    def _calculate_quality_score(self, stats: Dict[str, Any]) -> float:
        """计算质量分数"""
        score = 50
        
        if len(stats["question_type_distribution"]) >= 3:
            score += 10
        if len(stats["subject_distribution"]) >= 2:
            score += 10
        
        difficulty_dist = stats["difficulty_distribution"]
        if difficulty_dist.get("中等", 0) > 0:
            score += 10
        if difficulty_dist.get("简单", 0) > 0 and difficulty_dist.get("困难", 0) > 0:
            score += 10
        
        cognitive_dist = stats["cognitive_level_distribution"]
        if len(cognitive_dist) >= 3:
            score += 10
        
        return min(100, score)
    
    def _generate_quality_suggestions(self, stats: Dict[str, Any]) -> List[str]:
        """生成质量改进建议"""
        suggestions = []
        
        if stats["total_questions"] < 50:
            suggestions.append("建议增加题目数量，丰富题库内容")
        
        if len(stats["question_type_distribution"]) < 3:
            suggestions.append("建议增加题型多样性")
        
        difficulty_dist = stats["difficulty_distribution"]
        if "困难" not in difficulty_dist:
            suggestions.append("建议增加高难度题目")
        if "简单" not in difficulty_dist:
            suggestions.append("建议增加基础题")
        
        return suggestions


class CurriculumMatcher:
    """教学大纲匹配引擎"""
    
    def __init__(self):
        self.subjects = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
        self.grade_levels = ["小学", "初中", "高中"]
    
    def match_questions_to_curriculum(self, questions: List[Dict[str, Any]], 
                                      curriculum: Dict[str, Any]) -> List[Dict[str, Any]]:
        """匹配题目到教学大纲"""
        matched = []
        
        for question in questions:
            match_score = self._calculate_match_score(question, curriculum)
            if match_score > 0:
                question["curriculum_match_score"] = match_score
                question["matched_objectives"] = self._find_matched_objectives(question, curriculum)
                matched.append(question)
        
        matched.sort(key=lambda x: x["curriculum_match_score"], reverse=True)
        return matched
    
    def _calculate_match_score(self, question: Dict[str, Any], curriculum: Dict[str, Any]) -> float:
        """计算匹配分数"""
        score = 0
        
        subject = question.get("subject", "")
        curriculum_subject = curriculum.get("subject", "")
        if subject == curriculum_subject:
            score += 30
        
        topic = question.get("topic", "")
        topics = curriculum.get("topics", [])
        topic_names = [t.get("name", "") for t in topics]
        if topic in topic_names:
            score += 40
        elif any(topic in tn for tn in topic_names):
            score += 20
        
        cognitive_level = question.get("cognitive_level", "")
        objectives = curriculum.get("objectives", [])
        if any(cognitive_level in obj for obj in objectives):
            score += 30
        
        return score
    
    def _find_matched_objectives(self, question: Dict[str, Any], curriculum: Dict[str, Any]) -> List[str]:
        """查找匹配的教学目标"""
        matched = []
        objectives = curriculum.get("objectives", [])
        question_text = question.get("content", "")
        
        for obj in objectives:
            if any(keyword in question_text for keyword in ["理解", "掌握", "应用", "分析"]):
                matched.append(obj)
        
        return matched[:3]
    
    def generate_curriculum_aligned_questions(self, curriculum: Dict[str, Any], 
                                              count: int = 10) -> List[Dict[str, Any]]:
        """生成符合教学大纲的题目"""
        questions = []
        
        topics = curriculum.get("topics", [])
        objectives = curriculum.get("objectives", [])
        
        for i in range(count):
            topic = topics[i % len(topics)] if topics else {"name": "未知主题", "category": "其他"}
            objective = objectives[i % len(objectives)] if objectives else "掌握基本概念"
            
            question = {
                "question_id": f"curriculum_{i+1}",
                "subject": curriculum.get("subject", "未知"),
                "topic": topic.get("name", "未知"),
                "content": self._generate_question_content(topic, objective),
                "question_type": self._select_question_type(i),
                "difficulty": self._select_difficulty(i),
                "cognitive_level": self._extract_cognitive_level(objective),
                "curriculum_alignment": "high"
            }
            questions.append(question)
        
        return questions
    
    def _generate_question_content(self, topic: Dict[str, Any], objective: str) -> str:
        """生成题目内容"""
        topic_name = topic.get("name", "知识点")
        return f"关于{topic_name}的问题：{objective}相关内容是什么？"
    
    def _select_question_type(self, index: int) -> str:
        """选择题型"""
        types = ["单选题", "多选题", "填空题", "判断题"]
        return types[index % len(types)]
    
    def _select_difficulty(self, index: int) -> str:
        """选择难度"""
        levels = ["简单", "较易", "中等", "较难"]
        return levels[index % len(levels)]
    
    def _extract_cognitive_level(self, objective: str) -> str:
        """从目标中提取认知层次"""
        levels = ["记忆", "理解", "应用", "分析", "评价", "创造"]
        for level in levels:
            if level in objective:
                return level
        return "理解"


# 全局实例
researcher_ai = ResearcherAI()
expert_ai = ExpertAI()
teacher_ai = TeacherAI()
student_ai = StudentAI()
question_bank_optimizer = QuestionBankOptimizer()
curriculum_matcher = CurriculumMatcher()

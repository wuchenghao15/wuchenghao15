#!/usr/bin/env python3
"""
老师AI模块，负责处理错题交接和分析，提供智能教学支持
"""

import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.models.error_question import error_question_manager
from app.utils.logging import logger

class TeacherAI:
    """老师AI类"""
    
    def __init__(self, teacher_ai_id: str, name: str, subject: str):
        """初始化老师AI
        
        Args:
            teacher_ai_id: 老师AI ID
            name: 老师AI名称
            subject: 学科领域
        """
        self.teacher_ai_id = teacher_ai_id
        self.name = name
        self.subject = subject
        self.description = f"{subject}学科的智能老师AI"
        self.logger = logger
        self.logger.info(f"初始化老师AI: {self.name} ({self.teacher_ai_id})")
        
        # 配置参数
        self.config = {
            "analysis_enabled": True,
            "feedback_enabled": True,
            "learning_suggestions": True,
            "question_generation": True,
            "student_progress_tracking": True,
            "personalization": True,
            "adaptive_learning": True
        }
        
        # 知识图谱 - 增强版，包含知识点之间的关联
        self.knowledge_graph = {
            "math": {
                "代数": {"subtopics": ["方程", "函数", "不等式", "数列"], "difficulty": 3},
                "几何": {"subtopics": ["平面几何", "立体几何", "解析几何"], "difficulty": 4},
                "三角函数": {"subtopics": ["三角恒等式", "三角函数图像", "解三角形"], "difficulty": 3},
                "微积分": {"subtopics": ["导数", "积分", "微分方程"], "difficulty": 5},
                "概率统计": {"subtopics": ["概率", "统计", "数据分析"], "difficulty": 3}
            },
            "english": {
                "语法": {"subtopics": ["时态", "语态", "从句", "虚拟语气"], "difficulty": 3},
                "词汇": {"subtopics": ["单词记忆", "短语搭配", "同义词辨析"], "difficulty": 2},
                "听力": {"subtopics": ["对话理解", "短文听力", "讲座听力"], "difficulty": 3},
                "阅读": {"subtopics": ["阅读理解", "快速阅读", "批判性阅读"], "difficulty": 4},
                "写作": {"subtopics": ["议论文", "记叙文", "说明文"], "difficulty": 4}
            },
            "physics": {
                "力学": {"subtopics": ["牛顿运动定律", "动量守恒", "能量守恒"], "difficulty": 4},
                "热学": {"subtopics": ["热力学定律", "热传递", "理想气体"], "difficulty": 3},
                "电学": {"subtopics": ["电路", "电磁场", "电磁感应"], "difficulty": 4},
                "光学": {"subtopics": ["光的传播", "光的干涉", "光的衍射"], "difficulty": 3},
                "近代物理": {"subtopics": ["相对论", "量子力学", "原子核物理"], "difficulty": 5}
            },
            "chemistry": {
                "无机化学": {"subtopics": ["元素周期律", "化学键", "化学反应"], "difficulty": 3},
                "有机化学": {"subtopics": ["烃", "官能团", "有机反应"], "difficulty": 4},
                "物理化学": {"subtopics": ["化学热力学", "化学动力学", "电化学"], "difficulty": 5},
                "分析化学": {"subtopics": ["定量分析", "定性分析", "仪器分析"], "difficulty": 3}
            },
            "biology": {
                "细胞生物学": {"subtopics": ["细胞结构", "细胞代谢", "细胞分裂"], "difficulty": 3},
                "遗传学": {"subtopics": ["孟德尔遗传", "分子遗传", "基因工程"], "difficulty": 4},
                "生态学": {"subtopics": ["生态系统", "种群生态学", "环境保护"], "difficulty": 2},
                "进化论": {"subtopics": ["自然选择", "物种形成", "进化证据"], "difficulty": 3}
            }
        }
        
        # 错误模式库
        self.error_patterns = {
            "conceptual": {
                "description": "概念理解错误",
                "suggestions": ["重新学习相关概念", "做概念辨析练习", "绘制概念图谱"],
                "severity": "high"
            },
            "calculation": {
                "description": "计算错误",
                "suggestions": ["加强计算练习", "养成检查习惯", "学习计算技巧"],
                "severity": "medium"
            },
            "misunderstanding": {
                "description": "题意理解错误",
                "suggestions": ["提高阅读能力", "练习审题技巧", "分析题目结构"],
                "severity": "medium"
            },
            "careless": {
                "description": "粗心大意",
                "suggestions": ["加强专注力训练", "养成检查习惯", "规范答题步骤"],
                "severity": "low"
            }
        }
        
        # 学习资源库
        self.learning_resources = {
            "math": {
                "websites": ["https://www.khanacademy.org/math", "https://www.mathway.com/"],
                "books": ["《高中数学必修》", "《数学思维训练》"],
                "videos": ["数学思维讲座", "解题技巧视频"]
            },
            "english": {
                "websites": ["https://www.englishclub.com/", "https://www.grammarly.com/"],
                "books": ["《英语语法大全》", "《词汇突破》"],
                "videos": ["英语听力训练", "口语表达技巧"]
            },
            "physics": {
                "websites": ["https://phet.colorado.edu/", "https://www.physicsclassroom.com/"],
                "books": ["《高中物理必修》", "《物理竞赛教程》"],
                "videos": ["物理实验演示", "解题思路分析"]
            },
            "chemistry": {
                "websites": ["https://www.chemguide.co.uk/", "https://chemistry.stackexchange.com/"],
                "books": ["《高中化学必修》", "《化学实验指南》"],
                "videos": ["化学实验视频", "化学反应原理"]
            },
            "biology": {
                "websites": ["https://www.biologyonline.com/", "https://www.nature.com/scitable/"],
                "books": ["《高中生物必修》", "《生物学导论》"],
                "videos": ["生物实验演示", "生态系统讲解"]
            }
        }
    
    def analyze_error_question(self, error_question_id: int, user_id: int = None) -> Dict[str, Any]:
        """
        分析错题
        
        Args:
            error_question_id: 错题ID
            user_id: 用户ID（用于个性化分析）
        
        Returns:
            分析结果
        """
        if not self.config.get("analysis_enabled", False):
            return None
        
        try:
            # 获取错题信息
            # 先尝试通过用户ID获取，如果没有提供用户ID则获取所有错题
            if user_id:
                error_questions = error_question_manager.get_user_error_questions(user_id)
            else:
                # 这里应该实现一个获取所有错题的方法，暂时使用较大的limit
                error_questions = error_question_manager.get_user_error_questions(0, limit=1000)
            
            error_question = None
            for eq in error_questions:
                if eq['id'] == error_question_id:
                    error_question = eq
                    break
            
            if not error_question:
                raise Exception("错题不存在")
            
            # 分析错误原因
            error_reason = self._analyze_error_reason(error_question)
            
            # 分析知识点关联
            knowledge_points = self._identify_knowledge_points(error_question)
            
            # 分析错误模式
            error_pattern = self._identify_error_pattern(error_question)
            
            # 分析错误严重程度
            severity = self._assess_error_severity(error_question, error_pattern)
            
            # 生成改进建议
            suggestions = self._generate_suggestions(error_question, knowledge_points, error_pattern)
            
            # 推荐学习资源
            resources = self._recommend_resources(error_question, knowledge_points)
            
            # 个性化分析（如果提供了用户ID）
            personalization = {}
            if user_id and self.config.get("personalization", False):
                personalization = self._personalize_analysis(user_id, error_question, knowledge_points)
            
            analysis_result = {
                "error_question_id": error_question_id,
                "question_content": error_question['content'],
                "user_answer": error_question['user_answer'],
                "correct_answer": error_question['correct_answer'],
                "error_reason": error_reason,
                "knowledge_points": knowledge_points,
                "error_pattern": error_pattern,
                "severity": severity,
                "suggestions": suggestions,
                "learning_resources": resources,
                "personalization": personalization,
                "analysis_time": datetime.now().isoformat(),
                "teacher_ai_id": self.teacher_ai_id
            }
            
            self.logger.info(f"分析错题成功: {error_question_id}")
            return analysis_result
        except Exception as e:
            self.logger.error(f"分析错题失败: {str(e)}")
            return None
    
    def provide_feedback(self, user_id: int, error_question_id: int, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        提供反馈
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            analysis_result: 分析结果
        
        Returns:
            反馈结果
        """
        if not self.config.get("feedback_enabled", False):
            return None
        
        try:
            # 生成个性化反馈
            feedback = {
                "user_id": user_id,
                "error_question_id": error_question_id,
                "teacher_ai_id": self.teacher_ai_id,
                "feedback_type": "personalized",
                "content": self._generate_personalized_feedback(analysis_result),
                "suggested_actions": self._generate_suggested_actions(analysis_result),
                "learning_resources": self._recommend_resources_from_analysis(analysis_result),
                "feedback_time": datetime.now().isoformat()
            }
            
            self.logger.info(f"提供反馈成功: {user_id}, 错题: {error_question_id}")
            return feedback
        except Exception as e:
            self.logger.error(f"提供反馈失败: {str(e)}")
            return None
    
    def generate_practice_questions(self, user_id: int, knowledge_points: List[str], 
                                  difficulty: str = "medium", count: int = 5, 
                                  question_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        生成练习题目
        
        Args:
            user_id: 用户ID
            knowledge_points: 知识点列表
            difficulty: 难度
            count: 题目数量
            question_types: 题目类型列表
        
        Returns:
            题目列表
        """
        if not self.config.get("question_generation", False):
            return []
        
        try:
            questions = []
            
            # 确定题目类型
            if not question_types:
                question_types = ["multiple_choice", "fill_blank", "short_answer"]
            
            # 基于用户历史错题分析，调整题目难度和类型
            user_difficulty = self._assess_user_difficulty(user_id, knowledge_points)
            if user_difficulty:
                difficulty = user_difficulty
            
            for i in range(count):
                # 随机选择知识点
                knowledge_point = random.choice(knowledge_points) if knowledge_points else "基础知识点"
                
                # 随机选择题目类型
                question_type = random.choice(question_types)
                
                # 生成题目
                question = self._generate_question(knowledge_point, question_type, difficulty)
                question["id"] = f"practice_{int(datetime.now().timestamp() * 1000)}_{i}"
                question["created_by"] = self.teacher_ai_id
                question["created_at"] = datetime.now().isoformat()
                question["target_user"] = user_id
                
                questions.append(question)
            
            self.logger.info(f"生成练习题目成功: {user_id}, 数量: {count}")
            return questions
        except Exception as e:
            self.logger.error(f"生成练习题目失败: {str(e)}")
            return []
    
    def track_student_progress(self, user_id: int) -> Dict[str, Any]:
        """
        跟踪学生进度
        
        Args:
            user_id: 用户ID
        
        Returns:
            进度报告
        """
        if not self.config.get("student_progress_tracking", False):
            return None
        
        try:
            # 获取用户错题统计
            statistics = error_question_manager.get_error_question_statistics(user_id)
            
            # 分析学习趋势
            learning_trend = self._analyze_learning_trend(user_id)
            
            # 评估掌握程度
            mastery_levels = self._evaluate_mastery_levels(statistics)
            
            # 生成学习计划
            learning_plan = self._generate_learning_plan(mastery_levels, learning_trend)
            
            progress_report = {
                "user_id": user_id,
                "teacher_ai_id": self.teacher_ai_id,
                "statistics": statistics,
                "learning_trend": learning_trend,
                "mastery_levels": mastery_levels,
                "learning_plan": learning_plan,
                "report_time": datetime.now().isoformat()
            }
            
            self.logger.info(f"跟踪学生进度成功: {user_id}")
            return progress_report
        except Exception as e:
            self.logger.error(f"跟踪学生进度失败: {str(e)}")
            return None
    
    def process_transfer(self, transfer_id: int) -> bool:
        """
        处理交接任务
        
        Args:
            transfer_id: 交接记录ID
        
        Returns:
            是否成功
        """
        try:
            # 这里应该实现具体的交接处理逻辑
            # 例如：分析错题、生成反馈、更新状态等
            self.logger.info(f"处理交接任务成功: {transfer_id}")
            return True
        except Exception as e:
            self.logger.error(f"处理交接任务失败: {str(e)}")
            return False
    
    def _analyze_error_reason(self, error_question: Dict[str, Any]) -> str:
        """
        分析错误原因
        
        Args:
            error_question: 错题信息
        
        Returns:
            错误原因
        """
        # 根据题目类型和答案分析错误原因
        question_type = error_question.get('question_type', '')
        user_answer = error_question.get('user_answer', '')
        correct_answer = error_question.get('correct_answer', '')
        
        if question_type == 'multiple_choice':
            return "对知识点理解不透彻，选择了错误的选项"
        elif question_type == 'true_false':
            return "对概念的判断有误"
        elif question_type == 'fill_blank':
            return "对知识点的记忆不牢固"
        elif question_type == 'short_answer':
            return "对问题的理解不够深入，回答不完整"
        else:
            return "需要进一步分析错误原因"
    
    def _identify_knowledge_points(self, error_question: Dict[str, Any]) -> List[str]:
        """
        识别知识点
        
        Args:
            error_question: 错题信息
        
        Returns:
            知识点列表
        """
        # 根据题目内容和标签识别知识点
        content = error_question.get('content', '')
        tags = error_question.get('tags', [])
        
        # 简单的知识点识别逻辑
        knowledge_points = []
        
        # 从标签中提取知识点
        for tag in tags:
            if tag in self._get_all_knowledge_points():
                knowledge_points.append(tag)
        
        # 如果没有从标签中找到知识点，根据学科默认添加
        if not knowledge_points and self.subject in self.knowledge_graph:
            knowledge_points = self.knowledge_graph[self.subject][:2]  # 默认取前两个知识点
        
        return knowledge_points
    
    def _identify_error_pattern(self, error_question: Dict[str, Any]) -> str:
        """
        识别错误模式
        
        Args:
            error_question: 错题信息
        
        Returns:
            错误模式
        """
        # 简单的错误模式识别
        error_type = error_question.get('error_type', '')
        
        if error_type == 'conceptual':
            return "概念理解错误"
        elif error_type == 'calculation':
            return "计算错误"
        elif error_type == 'misunderstanding':
            return "题意理解错误"
        elif error_type == 'careless':
            return "粗心大意"
        else:
            return "其他错误模式"
    
    def _generate_suggestions(self, error_question: Dict[str, Any], knowledge_points: List[str], error_pattern: str = None) -> List[str]:
        """
        生成改进建议
        
        Args:
            error_question: 错题信息
            knowledge_points: 知识点列表
            error_pattern: 错误模式（可选）
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 根据知识点生成建议
        for point in knowledge_points:
            suggestions.append(f"加强对{point}知识点的学习和理解")
        
        # 根据题目类型生成建议
        question_type = error_question.get('question_type', '')
        if question_type == 'multiple_choice':
            suggestions.append("多做选择题练习，提高解题技巧")
        elif question_type == 'short_answer':
            suggestions.append("加强对问题的分析能力，提高回答的完整性")
        
        # 根据错误模式生成建议
        if error_pattern and error_pattern in self.error_patterns:
            suggestions.extend(self.error_patterns[error_pattern]['suggestions'])
        
        # 通用建议
        suggestions.append("定期复习错题，巩固知识点")
        suggestions.append("多做相关练习题，加深理解")
        
        return suggestions
    
    def _generate_personalized_feedback(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成个性化反馈
        
        Args:
            analysis_result: 分析结果
        
        Returns:
            反馈内容
        """
        error_reason = analysis_result.get('error_reason', '')
        knowledge_points = analysis_result.get('knowledge_points', [])
        
        feedback = f"同学，你好！我是{self.name}。\n"
        feedback += f"关于这道题，你的错误原因是：{error_reason}。\n"
        feedback += "涉及的知识点包括：" + ", ".join(knowledge_points) + "。\n"
        feedback += "希望你能针对这些知识点加强学习，相信你会有很大的进步！"
        
        return feedback
    
    def _generate_suggested_actions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        生成建议行动
        
        Args:
            analysis_result: 分析结果
        
        Returns:
            建议行动列表
        """
        suggestions = analysis_result.get('suggestions', [])
        return suggestions
    
    def _recommend_resources_from_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从分析结果中推荐学习资源
        
        Args:
            analysis_result: 分析结果
        
        Returns:
            资源列表
        """
        knowledge_points = analysis_result.get('knowledge_points', [])
        resources = []
        
        for point in knowledge_points:
            resource = {
                "title": f"{point}知识点详解",
                "type": "article",
                "url": f"https://example.com/resources/{point}",
                "description": f"详细讲解{point}知识点的相关内容"
            }
            resources.append(resource)
        
        return resources
    
    def _analyze_learning_trend(self, user_id: int) -> Dict[str, Any]:
        """
        分析学习趋势
        
        Args:
            user_id: 用户ID
        
        Returns:
            学习趋势
        """
        # 简单的学习趋势分析
        return {
            "improvement_rate": 0.15,  # 假设提高了15%
            "weak_areas": ["代数", "几何"],
            "strong_areas": ["三角函数"],
            "learning_speed": "medium"
        }
    
    def _evaluate_mastery_levels(self, statistics: Dict[str, Any]) -> Dict[str, int]:
        """
        评估掌握程度
        
        Args:
            statistics: 统计信息
        
        Returns:
            掌握程度
        """
        # 简单的掌握程度评估
        return {
            "代数": 3,
            "几何": 2,
            "三角函数": 4,
            "微积分": 1
        }
    
    def _generate_learning_plan(self, mastery_levels: Dict[str, int], learning_trend: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成学习计划
        
        Args:
            mastery_levels: 掌握程度
            learning_trend: 学习趋势
        
        Returns:
            学习计划
        """
        # 生成学习计划
        plan = {
            "daily_tasks": [
                "复习10道错题",
                "完成5道新练习题",
                "阅读相关知识点讲解"
            ],
            "weekly_goals": [
                "掌握代数基础知识",
                "提高几何解题能力",
                "巩固三角函数知识点"
            ],
            "monthly_objectives": [
                "完成所有错题的复习",
                "提高考试成绩10%",
                "建立完整的知识体系"
            ]
        }
        
        return plan
    
    def _get_all_knowledge_points(self) -> List[str]:
        """
        获取所有知识点
        
        Returns:
            知识点列表
        """
        all_points = []
        for subject in self.knowledge_graph.values():
            all_points.extend(subject.keys())
        return all_points
    
    def _assess_error_severity(self, error_question: Dict[str, Any], error_pattern: str) -> str:
        """
        评估错误严重程度
        
        Args:
            error_question: 错题信息
            error_pattern: 错误模式
        
        Returns:
            严重程度
        """
        # 根据错误模式确定严重程度
        if error_pattern in self.error_patterns:
            return self.error_patterns[error_pattern]['severity']
        
        # 根据题目难度确定严重程度
        difficulty_level = error_question.get('difficulty_level', 1)
        if difficulty_level >= 4:
            return "high"
        elif difficulty_level >= 3:
            return "medium"
        else:
            return "low"
    
    def _personalize_analysis(self, user_id: int, error_question: Dict[str, Any], knowledge_points: List[str]) -> Dict[str, Any]:
        """
        个性化分析
        
        Args:
            user_id: 用户ID
            error_question: 错题信息
            knowledge_points: 知识点列表
        
        Returns:
            个性化分析结果
        """
        try:
            # 获取用户错题统计
            stats = error_question_manager.get_error_question_statistics(user_id)
            
            # 分析用户在相关知识点上的表现
            knowledge_performance = {}
            for point in knowledge_points:
                point_errors = stats.get('knowledge_points', {}).get(point, 0)
                mastery_level = error_question.get('mastery_level', 0)
                knowledge_performance[point] = {
                    "error_count": point_errors,
                    "mastery_level": mastery_level,
                    "suggested_approach": self._get_suggested_approach(point, mastery_level)
                }
            
            # 分析用户的学习模式
            learning_pattern = self._analyze_learning_pattern(user_id)
            
            return {
                "knowledge_performance": knowledge_performance,
                "learning_pattern": learning_pattern,
                "personalized_tips": self._generate_personalized_tips(learning_pattern, knowledge_performance)
            }
        except Exception as e:
            self.logger.error(f"个性化分析失败: {str(e)}")
            return {}
    
    def _analyze_learning_pattern(self, user_id: int) -> Dict[str, Any]:
        """
        分析用户学习模式
        
        Args:
            user_id: 用户ID
        
        Returns:
            学习模式分析
        """
        # 简化实现，实际应基于用户历史数据
        return {
            "preferred_learning_style": "visual",  # 视觉学习者
            "study_time_preference": "evening",  # 晚上学习
            "difficulty_preference": "challenging",  # 喜欢挑战
            "progress_rate": "steady"  # 稳步进步
        }
    
    def _generate_personalized_tips(self, learning_pattern: Dict[str, Any], knowledge_performance: Dict[str, Any]) -> List[str]:
        """
        生成个性化学习建议
        
        Args:
            learning_pattern: 学习模式
            knowledge_performance: 知识点表现
        
        Returns:
            个性化建议列表
        """
        tips = []
        
        # 基于学习风格的建议
        if learning_pattern.get("preferred_learning_style") == "visual":
            tips.append("建议使用图表、思维导图等视觉工具来学习")
        
        # 基于学习时间的建议
        if learning_pattern.get("study_time_preference") == "evening":
            tips.append("建议在晚上集中精力学习难点知识")
        
        # 基于知识点表现的建议
        for point, performance in knowledge_performance.items():
            if performance["mastery_level"] < 3:
                tips.append(f"加强{point}知识点的学习，建议多做基础练习题")
            elif performance["error_count"] > 3:
                tips.append(f"{point}知识点错误较多，建议分析错误原因并针对性练习")
        
        return tips
    
    def _get_suggested_approach(self, knowledge_point: str, mastery_level: int) -> str:
        """
        获取建议的学习方法
        
        Args:
            knowledge_point: 知识点
            mastery_level: 掌握程度
        
        Returns:
            建议的学习方法
        """
        if mastery_level < 2:
            return "从基础概念开始，多做基础练习"
        elif mastery_level < 4:
            return "加强中等难度题目练习，巩固知识点"
        else:
            return "挑战高难度题目，拓展知识应用"
    
    def _assess_user_difficulty(self, user_id: int, knowledge_points: List[str]) -> str:
        """
        评估用户难度水平
        
        Args:
            user_id: 用户ID
            knowledge_points: 知识点列表
        
        Returns:
            难度等级
        """
        try:
            # 获取用户错题统计
            stats = error_question_manager.get_error_question_statistics(user_id)
            
            # 分析用户在相关知识点上的表现
            total_errors = 0
            total_questions = 0
            
            for point in knowledge_points:
                total_errors += stats.get('knowledge_points', {}).get(point, 0)
                total_questions += 1
            
            if total_questions == 0:
                return "medium"
            
            error_rate = total_errors / total_questions
            if error_rate > 0.6:
                return "easy"
            elif error_rate > 0.3:
                return "medium"
            else:
                return "hard"
        except Exception as e:
            self.logger.error(f"评估用户难度失败: {str(e)}")
            return "medium"
    
    def _generate_question(self, knowledge_point: str, question_type: str, difficulty: str) -> Dict[str, Any]:
        """
        生成具体题目
        
        Args:
            knowledge_point: 知识点
            question_type: 题目类型
            difficulty: 难度
        
        Returns:
            题目信息
        """
        # 基于知识点、类型和难度生成题目
        question = {
            "content": f"关于{knowledge_point}的{difficulty}难度{question_type}题",
            "type": question_type,
            "difficulty": difficulty,
            "knowledge_points": [knowledge_point]
        }
        
        # 根据题目类型生成选项或答案
        if question_type == "multiple_choice":
            question["options"] = ["选项A", "选项B", "选项C", "选项D"]
            question["correct_answer"] = "选项A"
        elif question_type == "fill_blank":
            question["correct_answer"] = "正确答案"
        elif question_type == "short_answer":
            question["correct_answer"] = "详细的正确答案"
        
        return question
    
    def _recommend_resources(self, error_question: Dict[str, Any], knowledge_points: List[str]) -> List[Dict[str, Any]]:
        """
        推荐学习资源
        
        Args:
            error_question: 错题信息
            knowledge_points: 知识点列表
        
        Returns:
            资源列表
        """
        resources = []
        
        # 基于知识点推荐资源
        for point in knowledge_points:
            if self.subject in self.learning_resources:
                subject_resources = self.learning_resources[self.subject]
                
                # 推荐网站
                for website in subject_resources.get("websites", []):
                    resources.append({
                        "title": f"{point}学习网站",
                        "type": "website",
                        "url": website,
                        "description": f"关于{point}的详细学习资源"
                    })
                
                # 推荐书籍
                for book in subject_resources.get("books", []):
                    resources.append({
                        "title": book,
                        "type": "book",
                        "description": f"关于{point}的参考书籍"
                    })
                
                # 推荐视频
                for video in subject_resources.get("videos", []):
                    resources.append({
                        "title": video,
                        "type": "video",
                        "description": f"关于{point}的视频讲解"
                    })
        
        return resources
    
    def __str__(self):
        return f"TeacherAI(id={self.teacher_ai_id}, name={self.name}, subject={self.subject})"
    
    def __repr__(self):
        return self.__str__()

# 创建老师AI实例
math_teacher_ai = TeacherAI("teacher_ai_math", "数学智能老师", "math")
english_teacher_ai = TeacherAI("teacher_ai_english", "英语智能老师", "english")
physics_teacher_ai = TeacherAI("teacher_ai_physics", "物理智能老师", "physics")
chemistry_teacher_ai = TeacherAI("teacher_ai_chemistry", "化学智能老师", "chemistry")
biology_teacher_ai = TeacherAI("teacher_ai_biology", "生物智能老师", "biology")

# 老师AI映射
teacher_ai_map = {
    "math": math_teacher_ai,
    "english": english_teacher_ai,
    "physics": physics_teacher_ai,
    "chemistry": chemistry_teacher_ai,
    "biology": biology_teacher_ai
}

def init_teacher_ai():
    """
    初始化教师AI
    
    Returns:
        bool: 是否初始化成功
    """
    try:
        # 验证所有教师AI实例是否成功创建
        for subject, ai_instance in teacher_ai_map.items():
            if not ai_instance:
                logger.error(f"教师AI {subject} 初始化失败")
                return False
        
        logger.info("教师AI初始化成功")
        return True
    except Exception as e:
        logger.error(f"初始化教师AI失败: {str(e)}")
        return False

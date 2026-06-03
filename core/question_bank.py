# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Question Bank Expander - 题库扩充系统
支持从网络获取题库数据，扩充历年真题和练习
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import random
import re

class QuestionBankExpander:
    """题库扩充器"""
    
    def __init__(self):
        self.online_sources = [
            {"name": "学科网", "url": "mock://xueke.com"},
            {"name": "菁优网", "url": "mock://jyeoo.com"},
            {"name": "中学学科网", "url": "mock://zxxk.com"},
            {"name": "组卷网", "url": "mock://zujuan.com"}
        ]
        self.subjects = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
        self.question_types = ["单选题", "多选题", "填空题", "判断题", "问答题", "计算题", "应用题"]
        self.difficulty_levels = ["简单", "较易", "中等", "较难", "困难"]
    
    def expand_from_online(self, subject: str, grade_level: str, 
                          count: int = 20, question_type: str = "all") -> List[Dict[str, Any]]:
        """从网络扩充题库"""
        questions = []
        
        for i in range(count):
            source = random.choice(self.online_sources)
            question = self._generate_mock_question(subject, grade_level, i)
            question["source"] = source["name"]
            question["source_url"] = source["url"]
            questions.append(question)
        
        return questions
    
    def _generate_mock_question(self, subject: str, grade_level: str, index: int) -> Dict[str, Any]:
        """生成模拟题目"""
        templates = {
            "语文": {
                "单选题": [
                    "下列词语中，加点字注音完全正确的一项是（ ）",
                    "下列句子中，没有语病的一项是（ ）",
                    "下列词语书写完全正确的一项是（ ）",
                    "下列句子中，标点符号使用正确的一项是（ ）"
                ],
                "填空题": [
                    "根据课文内容填空：______，一览众山小。",
                    "默写古诗《静夜思》：床前明月光，______。",
                    "解释下列词语的意思：______"
                ],
                "问答题": [
                    "分析文章中划线句子的表达效果。",
                    "谈谈你对文章主题的理解。",
                    "赏析文中运用的修辞手法。"
                ]
            },
            "数学": {
                "单选题": [
                    "已知集合A={1,2,3}，则A的子集个数为（ ）",
                    "函数f(x)=x²-2x+1的最小值为（ ）",
                    "若a+b=5，ab=6，则a²+b²的值为（ ）"
                ],
                "填空题": [
                    "计算：2³ + 3² = ______",
                    "方程x²-5x+6=0的解为______",
                    "已知sin30°=______"
                ],
                "计算题": [
                    "解方程：2x + 5 = 13",
                    "计算：(x+2)² - (x-2)²",
                    "求函数y=x³-3x的极值"
                ]
            },
            "英语": {
                "单选题": [
                    "The book ______ on the desk belongs to my sister.",
                    "He suggested that we ______ early the next morning.",
                    "By the time he arrived, we ______ already left."
                ],
                "填空题": [
                    "She ______ (study) English for five years.",
                    "The weather is getting ______ (cold) day by day.",
                    "I look forward to ______ (hear) from you."
                ],
                "问答题": [
                    "Translate the following sentence into English：我爱学习。",
                    "Write a short paragraph about your favorite hobby.",
                    "Explain the difference between 'affect' and 'effect'."
                ]
            },
            "物理": {
                "单选题": [
                    "一个物体从高处自由落下，下落2秒后的速度为（g=10m/s²）",
                    "下列关于牛顿第一定律的说法正确的是（ ）",
                    "电阻R₁和R₂串联，总电阻为（ ）"
                ],
                "计算题": [
                    "一辆汽车以20m/s的速度行驶，刹车后做匀减速运动，加速度为-5m/s²，求刹车距离。",
                    "质量为2kg的物体受到10N的力作用，求加速度。",
                    "计算电功率：P=UI，已知U=220V，I=5A。"
                ],
                "问答题": [
                    "解释什么是惯性，并举例说明。",
                    "简述欧姆定律的内容及其适用条件。",
                    "说明动能定理的物理意义。"
                ]
            },
            "化学": {
                "单选题": [
                    "下列物质中，属于纯净物的是（ ）",
                    "下列反应中，属于置换反应的是（ ）",
                    "原子的核电荷数等于（ ）"
                ],
                "填空题": [
                    "水的化学式是______，相对分子质量为______。",
                    "写出电解水的化学方程式：______",
                    "元素周期表中，第一周期有______种元素。"
                ],
                "问答题": [
                    "说明质量守恒定律的内容。",
                    "解释为什么化学反应前后质量守恒。",
                    "简述化学平衡的特征。"
                ]
            }
        }
        
        if question_type == "all":
            q_type = random.choice(self.question_types)
        else:
            q_type = question_type
        
        subject_templates = templates.get(subject, templates["数学"])
        type_templates = subject_templates.get(q_type, subject_templates["单选题"])
        
        content = random.choice(type_templates)
        
        options = self._generate_options(subject, q_type)
        correct_answer = random.choice(["A", "B", "C", "D"])
        
        return {
            "question_id": f"{subject}_{grade_level}_{index+1}",
            "subject": subject,
            "grade_level": grade_level,
            "question_type": q_type,
            "content": content,
            "options": options,
            "correct_answer": correct_answer,
            "difficulty": random.choice(self.difficulty_levels),
            "cognitive_level": self._determine_cognitive_level(content),
            "created_at": datetime.now().isoformat(),
            "tags": self._generate_tags(subject, grade_level, q_type)
        }
    
    def _generate_options(self, subject: str, q_type: str) -> List[str]:
        """生成选项"""
        if q_type in ["填空题", "问答题", "计算题"]:
            return []
        
        option_templates = {
            "语文": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
            "数学": ["A. 2", "B. 4", "C. 6", "D. 8"],
            "英语": ["A. is", "B. are", "C. was", "D. were"],
            "物理": ["A. 10m/s", "B. 20m/s", "C. 30m/s", "D. 40m/s"],
            "化学": ["A. H₂O", "B. CO₂", "C. O₂", "D. N₂"]
        }
        
        return option_templates.get(subject, ["A. 答案A", "B. 答案B", "C. 答案C", "D. 答案D"])
    
    def _determine_cognitive_level(self, content: str) -> str:
        """确定认知层次"""
        if "计算" in content or "求解" in content:
            return "应用"
        elif "解释" in content or "说明" in content:
            return "理解"
        elif "分析" in content or "赏析" in content:
            return "分析"
        elif "设计" in content or "创造" in content:
            return "创造"
        return "记忆"
    
    def _generate_tags(self, subject: str, grade_level: str, q_type: str) -> List[str]:
        """生成标签"""
        return [subject, grade_level, q_type, "自动生成"]
    
    def import_from_file(self, file_path: str, format_type: str = "json") -> List[Dict[str, Any]]:
        """从文件导入题目"""
        questions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if format_type == "json":
                    data = json.load(f)
                    if isinstance(data, list):
                        questions = data
                    elif isinstance(data, dict) and "questions" in data:
                        questions = data["questions"]
                elif format_type == "txt":
                    questions = self._parse_txt_file(f.read())
        except Exception as e:
            print(f"导入文件失败: {e}")
        
        return questions
    
    def _parse_txt_file(self, content: str) -> List[Dict[str, Any]]:
        """解析TXT文件"""
        questions = []
        lines = content.strip().split('\n')
        
        current_question = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("题目"):
                if current_question:
                    questions.append(current_question)
                current_question = {"content": line[2:].strip()}
            elif line.startswith("选项"):
                current_question["options"] = []
            elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                if "options" not in current_question:
                    current_question["options"] = []
                current_question["options"].append(line)
            elif line.startswith("答案"):
                current_question["correct_answer"] = line[2:].strip()
            elif line.startswith("难度"):
                current_question["difficulty"] = line[2:].strip()
        
        if current_question:
            questions.append(current_question)
        
        return questions
    
    def export_to_file(self, questions: List[Dict[str, Any]], file_path: str, format_type: str = "json") -> bool:
        """导出题目到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format_type == "json":
                    json.dump({"questions": questions, "exported_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
                elif format_type == "txt":
                    f.write(self._format_as_txt(questions))
            return True
        except Exception as e:
            print(f"导出文件失败: {e}")
            return False
    
    def _format_as_txt(self, questions: List[Dict[str, Any]]) -> str:
        """格式化为TXT"""
        lines = []
        for i, q in enumerate(questions, 1):
            lines.append(f"题目{i}：{q.get('content', '')}")
            if "options" in q and q["options"]:
                lines.append("选项：")
                lines.extend(q["options"])
            if "correct_answer" in q:
                lines.append(f"答案：{q['correct_answer']}")
            if "difficulty" in q:
                lines.append(f"难度：{q['difficulty']}")
            lines.append("")
        
        return '\n'.join(lines)


class ExamPaperCollector:
    """历年真题收集器"""
    
    def __init__(self):
        self.exam_types = ["高考", "中考", "期中", "期末", "模拟"]
        self.years = list(range(2015, datetime.now().year + 1))
        self.regions = ["全国卷", "北京", "上海", "广东", "江苏", "浙江", "山东", "四川"]
    
    def collect_exam_papers(self, subject: str, exam_type: str = "高考", 
                           years: List[int] = None) -> List[Dict[str, Any]]:
        """收集历年真题"""
        papers = []
        
        if years is None:
            years = self.years[-3:]
        
        for year in years:
            region = random.choice(self.regions)
            paper = self._generate_exam_paper(subject, exam_type, year, region)
            papers.append(paper)
        
        return papers
    
    def _generate_exam_paper(self, subject: str, exam_type: str, year: int, region: str) -> Dict[str, Any]:
        """生成模拟试卷"""
        paper = {
            "paper_id": f"{exam_type}_{subject}_{year}_{region}",
            "exam_type": exam_type,
            "subject": subject,
            "year": year,
            "region": region,
            "total_score": 150 if subject in ["语文", "数学", "英语"] else 100,
            "duration_minutes": 120,
            "sections": self._generate_sections(subject),
            "created_at": datetime.now().isoformat()
        }
        
        return paper
    
    def _generate_sections(self, subject: str) -> List[Dict[str, Any]]:
        """生成试卷结构"""
        sections = []
        
        if subject in ["语文", "英语"]:
            sections.extend([
                {"name": "选择题", "questions": 10, "score": 30},
                {"name": "填空题", "questions": 5, "score": 20},
                {"name": "阅读理解", "questions": 3, "score": 40},
                {"name": "作文/写作", "questions": 1, "score": 60}
            ])
        elif subject == "数学":
            sections.extend([
                {"name": "选择题", "questions": 12, "score": 60},
                {"name": "填空题", "questions": 4, "score": 20},
                {"name": "解答题", "questions": 6, "score": 70}
            ])
        else:
            sections.extend([
                {"name": "选择题", "questions": 20, "score": 40},
                {"name": "填空题", "questions": 10, "score": 20},
                {"name": "问答题", "questions": 5, "score": 40}
            ])
        
        return sections
    
    def get_exam_statistics(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取试卷统计信息"""
        stats = {
            "total_papers": len(papers),
            "subject_distribution": {},
            "year_distribution": {},
            "region_distribution": {},
            "average_score": 0,
            "total_questions": 0
        }
        
        total_score = 0
        total_questions = 0
        
        for paper in papers:
            subject = paper.get("subject", "未知")
            stats["subject_distribution"][subject] = stats["subject_distribution"].get(subject, 0) + 1
            
            year = paper.get("year", 0)
            stats["year_distribution"][year] = stats["year_distribution"].get(year, 0) + 1
            
            region = paper.get("region", "未知")
            stats["region_distribution"][region] = stats["region_distribution"].get(region, 0) + 1
            
            total_score += paper.get("total_score", 0)
            
            for section in paper.get("sections", []):
                total_questions += section.get("questions", 0)
        
        if len(papers) > 0:
            stats["average_score"] = total_score / len(papers)
        stats["total_questions"] = total_questions
        
        return stats


class PracticeGenerator:
    """练习题生成器"""
    
    def __init__(self):
        self.difficulty_profiles = {
            "基础巩固": {"简单": 0.6, "较易": 0.3, "中等": 0.1},
            "能力提升": {"较易": 0.2, "中等": 0.5, "较难": 0.3},
            "冲刺拔高": {"中等": 0.2, "较难": 0.5, "困难": 0.3}
        }
    
    def generate_practice_set(self, subject: str, topic: str, 
                              difficulty_profile: str = "能力提升",
                              question_count: int = 10) -> Dict[str, Any]:
        """生成练习册"""
        profile = self.difficulty_profiles.get(difficulty_profile, self.difficulty_profiles["能力提升"])
        
        practice = {
            "practice_id": f"{subject}_{topic}_{difficulty_profile}",
            "subject": subject,
            "topic": topic,
            "difficulty_profile": difficulty_profile,
            "total_questions": question_count,
            "questions": [],
            "created_at": datetime.now().isoformat()
        }
        
        for _ in range(question_count):
            difficulty = self._select_difficulty(profile)
            question = self._generate_practice_question(subject, topic, difficulty)
            practice["questions"].append(question)
        
        return practice
    
    def _select_difficulty(self, profile: Dict[str, float]) -> str:
        """根据概率选择难度"""
        rand = random.random()
        cumulative = 0
        
        for difficulty, probability in profile.items():
            cumulative += probability
            if rand < cumulative:
                return difficulty
        
        return "中等"
    
    def _generate_practice_question(self, subject: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """生成练习题"""
        templates = {
            "数学": {
                "函数": f"已知函数f(x)={topic}，求f(x)的定义域/值域/单调性。",
                "方程": f"解方程：{topic}相关方程",
                "几何": f"已知{topic}图形，求相关长度/面积/体积。"
            },
            "物理": {
                "力学": f"一个物体在{topic}作用下运动，求相关物理量。",
                "电学": f"电路中{topic}相关问题，计算电流/电压/功率。",
                "光学": f"{topic}相关光学现象，解释原理或计算。"
            },
            "化学": {
                "化学反应": f"{topic}相关化学反应方程式配平。",
                "元素": f"{topic}元素的性质和用途。",
                "溶液": f"计算{topic}溶液的浓度/溶解度。"
            }
        }
        
        subject_templates = templates.get(subject, templates["数学"])
        content = subject_templates.get(topic, f"{topic}相关练习题")
        
        return {
            "question_id": f"practice_{hash(content) % 10000}",
            "content": content,
            "question_type": random.choice(["单选题", "填空题", "计算题"]),
            "difficulty": difficulty,
            "topic": topic,
            "subject": subject
        }
    
    def generate_daily_practice(self, subject: str, student_level: str = "中等") -> Dict[str, Any]:
        """生成每日练习"""
        topics = self._select_topics(subject, student_level)
        
        practice = {
            "practice_id": f"daily_{subject}_{datetime.now().strftime('%Y%m%d')}",
            "type": "daily",
            "subject": subject,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "questions": []
        }
        
        for topic in topics:
            question = self._generate_practice_question(subject, topic, self._adjust_difficulty(student_level))
            practice["questions"].append(question)
        
        return practice
    
    def _select_topics(self, subject: str, level: str) -> List[str]:
        """选择今日练习主题"""
        topic_banks = {
            "数学": ["函数", "方程", "几何", "概率", "数列"],
            "物理": ["力学", "电学", "光学", "热学", "波动"],
            "化学": ["化学反应", "元素周期", "溶液", "有机化学"]
        }
        
        topics = topic_banks.get(subject, ["综合"])
        return random.sample(topics, min(3, len(topics)))
    
    def _adjust_difficulty(self, level: str) -> str:
        """根据学生水平调整难度"""
        level_map = {
            "基础": "简单",
            "中等": "中等",
            "优秀": "较难"
        }
        return level_map.get(level, "中等")


# 全局实例
question_bank_expander = QuestionBankExpander()
exam_paper_collector = ExamPaperCollector()
practice_generator = PracticeGenerator()

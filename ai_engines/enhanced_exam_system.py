# -*- coding: utf-8 -*-
"""
MTSCOS 增强考试系统 v3.0
智能出题、自适应评分、错题分析、成绩预测
"""

import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('exam_system')

class ExamQuestion:
    """考试题目"""
    
    def __init__(self, question_id: str, subject: str, topic: str, difficulty: float, content: str, 
                 options: List[str] = None, answer: str = None, analysis: str = ""):
        self.question_id = question_id
        self.subject = subject
        self.topic = topic
        self.difficulty = difficulty
        self.content = content
        self.options = options or []
        self.answer = answer
        self.analysis = analysis
    
    def to_dict(self):
        return {
            'question_id': self.question_id,
            'subject': self.subject,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'content': self.content,
            'options': self.options,
            'answer': self.answer,
            'analysis': self.analysis
        }

class ExamPaper:
    """试卷"""
    
    def __init__(self, paper_id: str, subject: str, grade: int, duration: int):
        self.paper_id = paper_id
        self.subject = subject
        self.grade = grade
        self.duration = duration
        self.questions = []
        self.total_score = 0
        self.created_at = datetime.now()
    
    def add_question(self, question: ExamQuestion, score: int):
        """添加题目"""
        self.questions.append({
            'question': question.to_dict(),
            'score': score
        })
        self.total_score += score
    
    def to_dict(self):
        return {
            'paper_id': self.paper_id,
            'subject': self.subject,
            'grade': self.grade,
            'duration': self.duration,
            'questions': self.questions,
            'total_score': self.total_score,
            'question_count': len(self.questions),
            'created_at': self.created_at.isoformat()
        }

class ExamResult:
    """考试结果"""
    
    def __init__(self, exam_id: str, user_id: str, paper_id: str):
        self.exam_id = exam_id
        self.user_id = user_id
        self.paper_id = paper_id
        self.answers = {}
        self.scores = {}
        self.total_score = 0
        self.max_score = 0
        self.completed_at = None
        self.duration = 0
    
    def add_answer(self, question_id: str, user_answer: str, correct_answer: str, score: int):
        """添加答题记录"""
        is_correct = user_answer == correct_answer
        earned_score = score if is_correct else 0
        
        self.answers[question_id] = {
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'score': earned_score,
            'max_score': score
        }
        self.scores[question_id] = earned_score
        self.total_score += earned_score
        self.max_score += score
    
    def to_dict(self):
        correct_count = sum(1 for a in self.answers.values() if a['is_correct'])
        return {
            'exam_id': self.exam_id,
            'user_id': self.user_id,
            'paper_id': self.paper_id,
            'answers': self.answers,
            'total_score': self.total_score,
            'max_score': self.max_score,
            'correct_count': correct_count,
            'question_count': len(self.answers),
            'accuracy': round((correct_count / len(self.answers)) * 100, 2) if self.answers else 0,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration
        }

class EnhancedExamSystem:
    """增强考试系统"""
    
    def __init__(self):
        self.question_bank = {}
        self.exam_history = {}
        self.user_profiles = {}
        self._load_question_bank()
        logger.info("增强考试系统 v3.0 初始化完成")
    
    def _load_question_bank(self):
        """加载题库"""
        self.question_bank = {
            '数学': {
                '代数': [
                    {'id': 'm_algebra_1', 'content': '解方程: 2x + 5 = 15', 'options': ['x=5', 'x=10', 'x=7', 'x=3'], 'answer': 'x=5', 'difficulty': 0.3, 'analysis': '移项得 2x = 10，所以 x = 5'},
                    {'id': 'm_algebra_2', 'content': '计算: (3x^2 + 2x - 1) + (2x^2 - 3x + 4)', 'options': ['5x^2 - x + 3', '5x^2 + 5x + 3', '5x^2 - x - 3', '5x^2 + x + 3'], 'answer': '5x^2 - x + 3', 'difficulty': 0.4, 'analysis': '合并同类项: 3x^2+2x^2=5x^2, 2x-3x=-x, -1+4=3'},
                    {'id': 'm_algebra_3', 'content': '因式分解: x^2 - 9', 'options': ['(x+3)(x-3)', '(x+9)(x-1)', '(x-3)^2', '(x+3)^2'], 'answer': '(x+3)(x-3)', 'difficulty': 0.35, 'analysis': '平方差公式: a^2 - b^2 = (a+b)(a-b)'},
                    {'id': 'm_algebra_4', 'content': '解方程: x^2 - 5x + 6 = 0', 'options': ['x=2或x=3', 'x=-2或x=-3', 'x=1或x=6', 'x=-1或x=-6'], 'answer': 'x=2或x=3', 'difficulty': 0.5, 'analysis': '因式分解为(x-2)(x-3)=0，所以x=2或x=3'},
                    {'id': 'm_algebra_5', 'content': '化简: (a+b)^2 - (a-b)^2', 'options': ['4ab', '2a^2+2b^2', '2a^2-2b^2', '4a^2'], 'answer': '4ab', 'difficulty': 0.45, 'analysis': '展开后相减得4ab'}
                ],
                '几何': [
                    {'id': 'm_geo_1', 'content': '三角形面积公式是', 'options': ['S=1/2*底*高', 'S=底*高', 'S=1/3*底*高', 'S=2*底*高'], 'answer': 'S=1/2*底*高', 'difficulty': 0.2, 'analysis': '三角形面积等于底乘高的一半'},
                    {'id': 'm_geo_2', 'content': '圆的面积公式是', 'options': ['S=πr²', 'S=2πr', 'S=πd', 'S=4πr²'], 'answer': 'S=πr²', 'difficulty': 0.25, 'analysis': '圆的面积等于π乘以半径的平方'},
                    {'id': 'm_geo_3', 'content': '正方形对角线长为10cm，求面积', 'options': ['50cm²', '100cm²', '25cm²', '75cm²'], 'answer': '50cm²', 'difficulty': 0.45, 'analysis': '对角线平方除以2等于面积: 10²/2=50'},
                    {'id': 'm_geo_4', 'content': '直角三角形两直角边分别为3cm和4cm，斜边长为', 'options': ['5cm', '7cm', '12cm', '25cm'], 'answer': '5cm', 'difficulty': 0.35, 'analysis': '勾股定理: √(3²+4²)=5'}
                ],
                '函数': [
                    {'id': 'm_func_1', 'content': '函数y=2x+1的斜率是', 'options': ['2', '1', '-2', '-1'], 'answer': '2', 'difficulty': 0.25, 'analysis': '一次函数y=kx+b中，k是斜率'},
                    {'id': 'm_func_2', 'content': '函数y=x²的顶点坐标是', 'options': ['(0,0)', '(1,1)', '(0,1)', '(1,0)'], 'answer': '(0,0)', 'difficulty': 0.3, 'analysis': '抛物线y=x²开口向上，顶点在原点'},
                    {'id': 'm_func_3', 'content': '函数y=sin(x)的最大值是', 'options': ['1', '-1', '0', 'π'], 'answer': '1', 'difficulty': 0.35, 'analysis': '正弦函数的值域是[-1,1]'}
                ],
                '概率统计': [
                    {'id': 'm_prob_1', 'content': '掷一枚骰子，出现偶数的概率是', 'options': ['1/2', '1/3', '1/6', '2/3'], 'answer': '1/2', 'difficulty': 0.3, 'analysis': '偶数有2,4,6三个，概率=3/6=1/2'},
                    {'id': 'm_prob_2', 'content': '数据2,4,6,8,10的平均数是', 'options': ['6', '5', '7', '8'], 'answer': '6', 'difficulty': 0.25, 'analysis': '平均数=(2+4+6+8+10)/5=6'}
                ]
            },
            '语文': {
                '语法': [
                    {'id': 'c_grammar_1', 'content': '下列词语中，书写正确的是', 'options': ['再接再厉', '再接再励', '再接再砺', '再接在厉'], 'answer': '再接再厉', 'difficulty': 0.3, 'analysis': '厉表示磨砺，不是鼓励的励'},
                    {'id': 'c_grammar_2', 'content': '选出正确的词语填空：他____地完成了任务', 'options': ['出色', '杰出', '卓越', '优秀'], 'answer': '出色', 'difficulty': 0.35, 'analysis': '出色更适合形容完成任务的表现'}
                ],
                '古诗词': [
                    {'id': 'c_poetry_1', 'content': '"床前明月光"的作者是', 'options': ['李白', '杜甫', '白居易', '王维'], 'answer': '李白', 'difficulty': 0.15, 'analysis': '这是李白的《静夜思》'},
                    {'id': 'c_poetry_2', 'content': '"春眠不觉晓"的下一句是', 'options': ['处处闻啼鸟', '夜来风雨声', '花落知多少', '床前明月光'], 'answer': '处处闻啼鸟', 'difficulty': 0.2, 'analysis': '出自孟浩然的《春晓》'}
                ],
                '阅读理解': [
                    {'id': 'c_reading_1', 'content': '文章中"他"指代的是', 'options': ['作者', '主人公', '读者', '老师'], 'answer': '主人公', 'difficulty': 0.4, 'analysis': '需要根据上下文判断代词指代'},
                    {'id': 'c_reading_2', 'content': '文章的主要观点是', 'options': ['保护环境', '热爱学习', '珍惜时间', '团结友爱'], 'answer': '保护环境', 'difficulty': 0.5, 'analysis': '需要通读全文理解主旨'}
                ]
            },
            '英语': {
                '词汇': [
                    {'id': 'e_vocab_1', 'content': 'The opposite of "happy" is', 'options': ['sad', 'angry', 'tired', 'hungry'], 'answer': 'sad', 'difficulty': 0.2, 'analysis': 'happy的反义词是sad'},
                    {'id': 'e_vocab_2', 'content': 'Choose the correct word: He ___ to school every day', 'options': ['goes', 'go', 'going', 'went'], 'answer': 'goes', 'difficulty': 0.3, 'analysis': '第三人称单数动词要加s'}
                ],
                '语法': [
                    {'id': 'e_grammar_1', 'content': 'She ___ (study) English for 5 years', 'options': ['has studied', 'studied', 'studies', 'study'], 'answer': 'has studied', 'difficulty': 0.45, 'analysis': 'for+时间段用现在完成时'},
                    {'id': 'e_grammar_2', 'content': 'If I ___ you, I would study harder', 'options': ['were', 'was', 'am', 'be'], 'answer': 'were', 'difficulty': 0.5, 'analysis': '虚拟语气中be动词用were'}
                ],
                '阅读理解': [
                    {'id': 'e_reading_1', 'content': 'What is the main idea of the passage?', 'options': ['Importance of reading', 'History of books', 'How to read fast', 'Famous authors'], 'answer': 'Importance of reading', 'difficulty': 0.5, 'analysis': '需要理解文章主旨'}
                ]
            },
            '物理': {
                '力学': [
                    {'id': 'p_mechanics_1', 'content': '物体做匀速直线运动时，合力为', 'options': ['0', '正', '负', '无法确定'], 'answer': '0', 'difficulty': 0.35, 'analysis': '根据牛顿第一定律，匀速直线运动合力为零'},
                    {'id': 'p_mechanics_2', 'content': '重力加速度约为', 'options': ['9.8m/s²', '10m/s', '9.8m/s', '10m/s²'], 'answer': '9.8m/s²', 'difficulty': 0.25, 'analysis': '地球表面重力加速度约为9.8m/s²'}
                ],
                '电学': [
                    {'id': 'p_electric_1', 'content': '欧姆定律的公式是', 'options': ['U=IR', 'P=UI', 'W=Pt', 'Q=It'], 'answer': 'U=IR', 'difficulty': 0.3, 'analysis': '欧姆定律：电压=电流×电阻'}
                ]
            },
            '化学': {
                '元素': [
                    {'id': 'ch_element_1', 'content': '水的化学式是', 'options': ['H₂O', 'CO₂', 'NaCl', 'H₂SO₄'], 'answer': 'H₂O', 'difficulty': 0.15, 'analysis': '水由两个氢原子和一个氧原子组成'},
                    {'id': 'ch_element_2', 'content': '氧气的化学式是', 'options': ['O₂', 'O', 'O₃', 'H₂O'], 'answer': 'O₂', 'difficulty': 0.2, 'analysis': '氧气是双原子分子'}
                ],
                '反应': [
                    {'id': 'ch_reaction_1', 'content': '铁在空气中生锈是一种什么变化', 'options': ['化学变化', '物理变化', '核变化', '相变'], 'answer': '化学变化', 'difficulty': 0.3, 'analysis': '生锈生成了新物质氧化铁'}
                ]
            }
        }
    
    def create_user_profile(self, user_id: str, grade: int = 1, education_type: str = 'k12'):
        """创建用户档案"""
        self.user_profiles[user_id] = {
            'user_id': user_id,
            'grade': grade,
            'education_type': education_type,
            'skill_levels': {},
            'exam_history': [],
            'error_questions': []
        }
    
    def generate_exam_paper(self, subject: str, grade: int, question_count: int = 10, 
                            difficulty_range: Tuple[float, float] = (0.3, 0.7)) -> Dict[str, Any]:
        """智能生成试卷"""
        subject_questions = self.question_bank.get(subject, {})
        
        all_questions = []
        for topic, questions in subject_questions.items():
            filtered = [q for q in questions if difficulty_range[0] <= q['difficulty'] <= difficulty_range[1]]
            all_questions.extend([{'topic': topic, **q} for q in filtered])
        
        if not all_questions:
            return {'error': '暂无匹配的题目'}
        
        selected = random.sample(all_questions, min(question_count, len(all_questions)))
        
        paper = ExamPaper(
            paper_id=f"paper_{int(datetime.now().timestamp())}",
            subject=subject,
            grade=grade,
            duration=question_count * 5
        )
        
        for q in selected:
            question = ExamQuestion(
                question_id=q['id'],
                subject=subject,
                topic=q['topic'],
                difficulty=q['difficulty'],
                content=q['content'],
                options=q['options'],
                answer=q['answer'],
                analysis=q.get('analysis', '')
            )
            score = max(1, int((1 - q['difficulty']) * 20))
            paper.add_question(question, score)
        
        return paper.to_dict()
    
    def grade_exam(self, exam_id: str, user_id: str, paper_id: str, answers: Dict[str, str], 
                   paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """评分考试"""
        result = ExamResult(exam_id, user_id, paper_id)
        
        for q in paper_data.get('questions', []):
            question_id = q['question']['question_id']
            correct_answer = q['question']['answer']
            user_answer = answers.get(question_id, '')
            score = q['score']
            
            result.add_answer(question_id, user_answer, correct_answer, score)
        
        result.completed_at = datetime.now()
        
        if user_id in self.user_profiles:
            self.user_profiles[user_id]['exam_history'].append({
                'exam_id': exam_id,
                'paper_id': paper_id,
                'subject': paper_data['subject'],
                'score': result.total_score,
                'max_score': result.max_score,
                'completed_at': result.completed_at.isoformat()
            })
            
            for q in paper_data.get('questions', []):
                question_id = q['question']['question_id']
                user_answer = answers.get(question_id, '')
                if user_answer != q['question']['answer']:
                    if question_id not in self.user_profiles[user_id]['error_questions']:
                        self.user_profiles[user_id]['error_questions'].append({
                            'question_id': question_id,
                            'subject': paper_data['subject'],
                            'topic': q['question']['topic'],
                            'content': q['question']['content'],
                            'user_answer': user_answer,
                            'correct_answer': q['question']['answer'],
                            'analysis': q['question'].get('analysis', ''),
                            'timestamp': datetime.now().isoformat()
                        })
        
        self.exam_history[exam_id] = result.to_dict()
        return result.to_dict()
    
    def get_user_error_notebook(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户错题本"""
        if user_id not in self.user_profiles:
            return []
        return self.user_profiles[user_id].get('error_questions', [])
    
    def clear_error_notebook(self, user_id: str):
        """清空错题本"""
        if user_id in self.user_profiles:
            self.user_profiles[user_id]['error_questions'] = []
            return True
        return False
    
    def predict_score(self, user_id: str, subject: str) -> float:
        """预测用户成绩"""
        if user_id not in self.user_profiles:
            return 60.0
        
        history = self.user_profiles[user_id].get('exam_history', [])
        subject_history = [h for h in history if h['subject'] == subject]
        
        if not subject_history:
            return 60.0
        
        avg_score = sum(h['score'] / h['max_score'] for h in subject_history) / len(subject_history)
        return round(avg_score * 100, 2)
    
    def generate_personalized_practice(self, user_id: str, subject: str, count: int = 10) -> Dict[str, Any]:
        """生成个性化练习题"""
        if user_id not in self.user_profiles:
            return self.generate_exam_paper(subject, 1, count)
        
        error_questions = self.user_profiles[user_id].get('error_questions', [])
        subject_errors = [e for e in error_questions if e['subject'] == subject]
        
        if subject_errors:
            questions = []
            for error in subject_errors[:count]:
                questions.append({
                    'question': {
                        'question_id': error['question_id'],
                        'subject': error['subject'],
                        'topic': error['topic'],
                        'difficulty': 0.5,
                        'content': error['content'],
                        'options': [],
                        'answer': error['correct_answer'],
                        'analysis': error.get('analysis', '')
                    },
                    'score': 10
                })
            
            return {
                'paper_id': f"practice_{int(datetime.now().timestamp())}",
                'subject': subject,
                'grade': self.user_profiles[user_id]['grade'],
                'duration': count * 5,
                'questions': questions,
                'total_score': len(questions) * 10,
                'question_count': len(questions),
                'type': 'practice',
                'generated_at': datetime.now().isoformat()
            }
        
        return self.generate_exam_paper(subject, self.user_profiles[user_id]['grade'], count)

enhanced_exam_system = EnhancedExamSystem()

if __name__ == '__main__':
    exam_system = EnhancedExamSystem()
    
    print("=== 生成试卷 ===")
    paper = exam_system.generate_exam_paper('数学', 7, 5)
    print(json.dumps(paper, indent=2, ensure_ascii=False))
    
    print("\n=== 创建用户档案 ===")
    exam_system.create_user_profile('student_001', grade=7)
    
    print("\n=== 模拟答题 ===")
    answers = {}
    for q in paper['questions']:
        answers[q['question']['question_id']] = q['question']['options'][0]
    
    print("\n=== 评分 ===")
    result = exam_system.grade_exam('exam_001', 'student_001', paper['paper_id'], answers, paper)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 获取错题本 ===")
    errors = exam_system.get_user_error_notebook('student_001')
    print(f"错题数量: {len(errors)}")
    
    print("\n=== 预测成绩 ===")
    prediction = exam_system.predict_score('student_001', '数学')
    print(f"预测成绩: {prediction}分")
    
    print("\n=== 生成个性化练习 ===")
    practice = exam_system.generate_personalized_practice('student_001', '数学', 3)
    print(json.dumps(practice, indent=2, ensure_ascii=False))
# -*- coding: utf-8 -*-
"""
AI智能学习路径推荐服务
分析学生学习数据，推荐个性化学习路径
"""

import json
import logging
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class AIStudyPathService:
    """AI智能学习路径推荐服务"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   'split_databases/learning.db')
        self.question_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                            'split_databases/question.db')
        
        self.subject_knowledge_map = {
            '语文': [
                {'topic': '阅读理解', 'sub_topics': ['主旨概括', '细节理解', '推断判断', '词义猜测']},
                {'topic': '写作', 'sub_topics': ['记叙文', '议论文', '说明文', '应用文']},
                {'topic': '文言文', 'sub_topics': ['实词虚词', '句式句式', '翻译', '理解']},
                {'topic': '诗词鉴赏', 'sub_topics': ['意象分析', '意境理解', '情感把握', '手法赏析']},
                {'topic': '基础知识', 'sub_topics': ['字音字形', '词语运用', '病句辨析', '标点符号']}
            ],
            '数学': [
                {'topic': '函数', 'sub_topics': ['一次函数', '二次函数', '反比例函数', '指数对数']},
                {'topic': '几何', 'sub_topics': ['三角形', '四边形', '圆', '立体几何']},
                {'topic': '代数', 'sub_topics': ['方程', '不等式', '数列', '概率统计']},
                {'topic': '三角函数', 'sub_topics': ['三角恒等变换', '三角函数图像', '解三角形']},
                {'topic': '解析几何', 'sub_topics': ['直线与圆', '椭圆', '双曲线', '抛物线']}
            ],
            '英语': [
                {'topic': '阅读理解', 'sub_topics': ['主旨大意', '细节理解', '推理判断', '词义猜测']},
                {'topic': '语法', 'sub_topics': ['时态语态', '从句', '非谓语', '主谓一致']},
                {'topic': '词汇', 'sub_topics': ['核心词汇', '短语搭配', '词根词缀']},
                {'topic': '完形填空', 'sub_topics': ['逻辑关系', '词汇辨析', '语法填空']},
                {'topic': '写作', 'sub_topics': ['应用文', '读后续写', '概要写作']}
            ],
            '物理': [
                {'topic': '力学', 'sub_topics': ['牛顿运动定律', '动量守恒', '能量守恒', '圆周运动']},
                {'topic': '电学', 'sub_topics': ['电路分析', '电磁感应', '电场磁场', '交流电']},
                {'topic': '光学', 'sub_topics': ['几何光学', '物理光学', '光电效应']},
                {'topic': '热学', 'sub_topics': ['分子动理论', '热力学定律', '理想气体']},
                {'topic': '近代物理', 'sub_topics': ['原子结构', '原子核', '相对论']}
            ],
            '化学': [
                {'topic': '化学反应', 'sub_topics': ['反应速率', '化学平衡', '电化学', '氧化还原']},
                {'topic': '物质结构', 'sub_topics': ['原子结构', '化学键', '晶体结构', '元素周期律']},
                {'topic': '有机化学', 'sub_topics': ['烃类', '烃的衍生物', '有机合成', '高分子']},
                {'topic': '无机化学', 'sub_topics': ['金属元素', '非金属元素', '化合物性质']},
                {'topic': '化学实验', 'sub_topics': ['实验设计', '实验操作', '数据分析']}
            ],
            '生物': [
                {'topic': '细胞', 'sub_topics': ['细胞结构', '细胞代谢', '细胞分裂', '细胞分化']},
                {'topic': '遗传', 'sub_topics': ['遗传规律', 'DNA复制', '基因表达', '生物进化']},
                {'topic': '生态', 'sub_topics': ['生态系统', '种群群落', '生态平衡', '环境保护']},
                {'topic': '代谢', 'sub_topics': ['光合作用', '呼吸作用', '酶', 'ATP']},
                {'topic': '生命调节', 'sub_topics': ['神经调节', '体液调节', '免疫调节']}
            ],
            '历史': [
                {'topic': '中国古代史', 'sub_topics': ['先秦', '秦汉', '唐宋', '明清']},
                {'topic': '中国近现代史', 'sub_topics': ['鸦片战争', '太平天国', '辛亥革命', '新中国']},
                {'topic': '世界史', 'sub_topics': ['古希腊罗马', '中世纪', '文艺复兴', '工业革命']},
                {'topic': '历史事件', 'sub_topics': ['改革变法', '战争冲突', '文化交流']},
                {'topic': '历史人物', 'sub_topics': ['政治家', '思想家', '科学家', '文学家']}
            ],
            '地理': [
                {'topic': '自然地理', 'sub_topics': ['地球运动', '大气环流', '水循环', '地质作用']},
                {'topic': '人文地理', 'sub_topics': ['人口', '城市', '农业', '工业']},
                {'topic': '区域地理', 'sub_topics': ['中国区域', '世界区域', '区域发展']},
                {'topic': '地图', 'sub_topics': ['等高线', '经纬网', '比例尺', '地图投影']},
                {'topic': '环境保护', 'sub_topics': ['环境问题', '可持续发展', '资源利用']}
            ],
            '政治': [
                {'topic': '哲学', 'sub_topics': ['唯物论', '辩证法', '认识论', '历史唯物主义']},
                {'topic': '经济', 'sub_topics': ['市场经济', '宏观调控', '国际贸易', '经济全球化']},
                {'topic': '政治', 'sub_topics': ['国家制度', '政党制度', '民主政治', '国际关系']},
                {'topic': '文化', 'sub_topics': ['文化传承', '文化创新', '中华文化', '民族精神']},
                {'topic': '法律', 'sub_topics': ['宪法', '民法', '刑法', '行政法']}
            ]
        }
        
        logger.info("[AI学习路径服务] 初始化完成")
    
    def analyze_weak_points(self, user_id: int, subject: str = None) -> Dict:
        """分析学生薄弱环节"""
        weak_points = []
        
        try:
            conn = sqlite3.connect(self.question_db_path)
            cursor = conn.cursor()
            
            where_clause = ""
            params = []
            
            if subject:
                where_clause = "WHERE subject = ?"
                params.append(subject)
            
            cursor.execute(f'''
                SELECT topic, COUNT(*) as total, SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong_count
                FROM wrong_questions 
                WHERE user_id = ? {where_clause}
                GROUP BY topic
                HAVING wrong_count > 0
                ORDER BY wrong_count DESC
            ''', (user_id, *params))
            
            results = cursor.fetchall()
            
            for row in results:
                topic, total, wrong_count = row
                error_rate = wrong_count / total
                
                if error_rate > 0.6:
                    level = 'critical'
                    suggestion = '紧急加强'
                elif error_rate > 0.4:
                    level = 'high'
                    suggestion = '重点复习'
                elif error_rate > 0.2:
                    level = 'medium'
                    suggestion = '巩固练习'
                else:
                    level = 'low'
                    suggestion = '日常练习'
                
                weak_points.append({
                    'topic': topic,
                    'total_questions': total,
                    'wrong_count': wrong_count,
                    'error_rate': round(error_rate, 2),
                    'level': level,
                    'suggestion': suggestion
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[分析薄弱环节失败] {e}")
        
        return {
            'success': True,
            'data': {
                'weak_points': weak_points,
                'total_weak_topics': len(weak_points)
            }
        }
    
    def generate_study_path(self, user_id: int, subject: str = None, days: int = 7) -> Dict:
        """生成学习路径"""
        analysis = self.analyze_weak_points(user_id, subject)
        weak_points = analysis['data']['weak_points']
        
        study_path = []
        
        if not weak_points:
            for day in range(1, days + 1):
                study_path.append({
                    'day': day,
                    'subject': subject or '综合',
                    'focus_area': '基础巩固',
                    'tasks': [
                        {
                            'type': 'review',
                            'description': '复习已掌握的知识点',
                            'duration': 30,
                            'difficulty': 'easy'
                        },
                        {
                            'type': 'practice',
                            'description': '做10道随机练习题',
                            'duration': 20,
                            'difficulty': 'medium'
                        }
                    ]
                })
        else:
            critical_topics = [p for p in weak_points if p['level'] == 'critical']
            high_topics = [p for p in weak_points if p['level'] == 'high']
            medium_topics = [p for p in weak_points if p['level'] == 'medium']
            
            all_topics = critical_topics + high_topics + medium_topics
            
            topic_index = 0
            for day in range(1, days + 1):
                if topic_index < len(all_topics):
                    topic = all_topics[topic_index]
                    topic_index += 1
                    
                    tasks = []
                    if topic['level'] == 'critical':
                        tasks = [
                            {
                                'type': 'video',
                                'description': f'观看「{topic["topic"]}」知识点讲解视频',
                                'duration': 20,
                                'difficulty': 'medium'
                            },
                            {
                                'type': 'practice',
                                'description': f'完成「{topic["topic"]}」专项练习 15题',
                                'duration': 40,
                                'difficulty': 'hard'
                            },
                            {
                                'type': 'review',
                                'description': f'复习「{topic["topic"]}」相关错题',
                                'duration': 20,
                                'difficulty': 'medium'
                            }
                        ]
                    elif topic['level'] == 'high':
                        tasks = [
                            {
                                'type': 'practice',
                                'description': f'完成「{topic["topic"]}」专项练习 10题',
                                'duration': 30,
                                'difficulty': 'medium'
                            },
                            {
                                'type': 'review',
                                'description': f'复习「{topic["topic"]}」相关错题',
                                'duration': 15,
                                'difficulty': 'easy'
                            }
                        ]
                    else:
                        tasks = [
                            {
                                'type': 'practice',
                                'description': f'完成「{topic["topic"]}」练习 8题',
                                'duration': 25,
                                'difficulty': 'easy'
                            }
                        ]
                    
                    study_path.append({
                        'day': day,
                        'subject': topic.get('subject', subject or '综合'),
                        'focus_area': topic['topic'],
                        'tasks': tasks,
                        'error_rate': topic['error_rate'],
                        'suggestion': topic['suggestion']
                    })
                else:
                    study_path.append({
                        'day': day,
                        'subject': subject or '综合',
                        'focus_area': '综合复习',
                        'tasks': [
                            {
                                'type': 'mixed',
                                'description': '综合练习题 20题',
                                'duration': 40,
                                'difficulty': 'medium'
                            },
                            {
                                'type': 'review',
                                'description': '本周错题回顾',
                                'duration': 20,
                                'difficulty': 'easy'
                            }
                        ]
                    })
        
        return {
            'success': True,
            'data': {
                'study_path': study_path,
                'total_days': days,
                'weak_points_count': len(weak_points),
                'estimated_total_hours': round(sum(sum(t['duration'] for t in day['tasks']) for day in study_path) / 60, 1)
            }
        }
    
    def get_subject_knowledge_graph(self, subject: str) -> Dict:
        """获取科目知识图谱"""
        if subject not in self.subject_knowledge_map:
            return {
                'success': False,
                'message': '未知科目'
            }
        
        return {
            'success': True,
            'data': {
                'subject': subject,
                'topics': self.subject_knowledge_map[subject]
            }
        }
    
    def get_all_subjects(self) -> Dict:
        """获取所有科目列表"""
        subjects = list(self.subject_knowledge_map.keys())
        return {
            'success': True,
            'data': subjects
        }
    
    def get_learning_progress(self, user_id: int) -> Dict:
        """获取学习进度"""
        progress = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT subject, 
                       SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_count,
                       COUNT(*) as total_count
                FROM learning_tasks
                WHERE user_id = ?
                GROUP BY subject
            ''', (user_id,))
            
            results = cursor.fetchall()
            
            for row in results:
                subject, completed_count, total_count = row
                progress[subject] = {
                    'completed': completed_count,
                    'total': total_count,
                    'percentage': round(completed_count / total_count * 100, 1) if total_count > 0 else 0
                }
            
            cursor.execute('''
                SELECT COUNT(*) FROM learning_tasks WHERE user_id = ? AND is_completed = 1
            ''', (user_id,))
            total_completed = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM learning_tasks WHERE user_id = ?
            ''', (user_id,))
            total_tasks = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[获取学习进度失败] {e}")
        
        return {
            'success': True,
            'data': {
                'progress_by_subject': progress,
                'total_completed': total_completed,
                'total_tasks': total_tasks,
                'overall_percentage': round(total_completed / total_tasks * 100, 1) if total_tasks > 0 else 0
            }
        }


ai_study_path_service = AIStudyPathService()

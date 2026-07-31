#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
import re
from datetime import datetime
from collections import defaultdict

class AILearningDiagnosis:
    DIAGNOSIS_LEVELS = ['critical', 'warning', 'normal', 'excellent']
    KNOWLEDGE_DOMAINS = {
        '语文': ['阅读理解', '写作表达', '语言知识', '古诗词鉴赏'],
        '数学': ['代数运算', '几何图形', '函数分析', '概率统计'],
        '英语': ['词汇语法', '阅读理解', '写作表达', '听力理解'],
        '物理': ['力学', '电磁学', '热学', '光学'],
        '化学': ['无机化学', '有机化学', '化学反应', '化学实验'],
        '生物': ['细胞生物学', '遗传学', '生态学', '生理学'],
        '历史': ['中国古代史', '中国近现代史', '世界史'],
        '地理': ['自然地理', '人文地理', '区域地理'],
        '政治': ['经济生活', '政治生活', '文化生活', '哲学']
    }
    
    SKILL_LEVELS = ['基础薄弱', '需要巩固', '掌握良好', '精通']
    
    def __init__(self):
        self.diagnosis_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
        self._init_knowledge_points()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_diagnosis.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS diagnosis_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    diagnosis_level TEXT DEFAULT 'normal',
                    overall_score REAL DEFAULT 0.0,
                    knowledge_gaps TEXT,
                    weak_areas TEXT,
                    strong_areas TEXT,
                    recommendations TEXT,
                    improvement_plan TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    point_id TEXT NOT NULL UNIQUE,
                    subject TEXT NOT NULL,
                    domain TEXT,
                    point_name TEXT NOT NULL,
                    difficulty_level TEXT DEFAULT 'medium',
                    related_points TEXT,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analytics_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    domain TEXT,
                    knowledge_point TEXT,
                    correct_rate REAL DEFAULT 0.0,
                    practice_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_practice_time TEXT,
                    trend TEXT,
                    skill_level TEXT DEFAULT '基础薄弱',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS improvement_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    record_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    knowledge_point TEXT,
                    task_type TEXT,
                    task_content TEXT,
                    target_score REAL DEFAULT 0.0,
                    current_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    deadline TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS diagnosis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    diagnosis_level TEXT,
                    overall_score REAL DEFAULT 0.0,
                    knowledge_gaps TEXT,
                    recommendations TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"创建表失败: {e}")

    def _init_knowledge_points(self):
        try:
            conn = sqlite3.connect('ai_diagnosis.db')
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM knowledge_points')
            if cursor.fetchone()[0] == 0:
                all_points = []
                
                for subject, domains in self.KNOWLEDGE_DOMAINS.items():
                    for domain in domains:
                        if subject == '语文':
                            points = ['文言文阅读', '现代文阅读', '诗歌鉴赏', '作文写作', 
                                      '病句辨析', '成语运用', '修辞手法', '文学常识']
                        elif subject == '数学':
                            points = ['一元二次方程', '三角函数', '立体几何', '导数应用',
                                      '概率计算', '数列求和', '向量运算', '不等式']
                        elif subject == '英语':
                            points = ['时态语态', '从句结构', '词汇辨析', '阅读理解',
                                      '完形填空', '书面表达', '听力理解', '语法填空']
                        elif subject == '物理':
                            points = ['牛顿运动定律', '能量守恒', '电场磁场', '电路分析',
                                      '光学现象', '热力学定律', '机械波', '原子物理']
                        elif subject == '化学':
                            points = ['化学反应速率', '化学平衡', '电化学', '有机合成',
                                      '元素周期律', '化学实验', '溶液配制', '氧化还原']
                        elif subject == '生物':
                            points = ['细胞呼吸', '光合作用', '遗传定律', 'DNA复制',
                                      '生态系统', '神经调节', '免疫调节', '细胞分裂']
                        elif subject == '历史':
                            points = ['古代政治制度', '近代化探索', '世界史纲要', '经济政策',
                                      '文化发展', '国际关系', '重大改革', '思想演变']
                        elif subject == '地理':
                            points = ['地球运动', '气候分析', '水文地理', '地貌形成',
                                      '城市规划', '农业区位', '工业区位', '区域发展']
                        elif subject == '政治':
                            points = ['市场经济', '宏观调控', '公民权利', '政府职能',
                                      '文化创新', '传统文化', '唯物论', '辩证法']
                        else:
                            points = ['基础概念', '核心原理', '应用分析', '综合运用']
                        
                        for idx, point in enumerate(points):
                            point_id = hashlib.md5(f"{subject}{domain}{point}".encode()).hexdigest()[:16]
                            difficulty = ['easy', 'easy', 'medium', 'medium', 'medium', 'hard', 'hard', 'hard'][idx]
                            all_points.append({
                                'point_id': point_id,
                                'subject': subject,
                                'domain': domain,
                                'point_name': point,
                                'difficulty_level': difficulty,
                                'weight': 1.0
                            })

                for point in all_points:
                    cursor.execute('''
                        INSERT INTO knowledge_points 
                        (point_id, subject, domain, point_name, difficulty_level, weight)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (point['point_id'], point['subject'], point['domain'], 
                          point['point_name'], point['difficulty_level'], point['weight']))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"初始化知识点失败: {e}")

    def diagnose_learning(self, user_id, subject, exam_data=None, homework_data=None, practice_data=None):
        """诊断学习情况"""
        record_id = hashlib.md5(f"{user_id}{subject}{datetime.now()}".encode()).hexdigest()[:16]
        
        analytics = self._analyze_learning_data(user_id, subject, exam_data, homework_data, practice_data)
        
        knowledge_gaps = []
        weak_areas = []
        strong_areas = []
        
        for domain, points in analytics.items():
            for point, data in points.items():
                correct_rate = data['correct_rate']
                if correct_rate < 0.5:
                    knowledge_gaps.append(point)
                    weak_areas.append(f"{domain} - {point}")
                elif correct_rate < 0.65:
                    weak_areas.append(f"{domain} - {point}")
                elif correct_rate >= 0.75:
                    strong_areas.append(f"{domain} - {point}")
        
        overall_score = self._calculate_overall_score(analytics)
        diagnosis_level = self._determine_diagnosis_level(overall_score, len(knowledge_gaps))
        
        recommendations = self._generate_recommendations(subject, knowledge_gaps, weak_areas, strong_areas,
        overall_score)
        improvement_plan = self._generate_improvement_plan(record_id, user_id, subject, knowledge_gaps, weak_areas)
        
        self._save_diagnosis_record(record_id, user_id, subject, diagnosis_level, overall_score, 
                                   knowledge_gaps, weak_areas, strong_areas, recommendations, improvement_plan)
        
        return {
            'success': True,
            'record_id': record_id,
            'user_id': user_id,
            'subject': subject,
            'diagnosis_level': diagnosis_level,
            'overall_score': round(overall_score, 2),
            'knowledge_gaps': knowledge_gaps,
            'weak_areas': weak_areas,
            'strong_areas': strong_areas,
            'recommendations': recommendations,
            'improvement_plan': improvement_plan,
            'analytics': analytics,
            'created_at': datetime.now().isoformat()
        }

    def _analyze_learning_data(self, user_id, subject, exam_data, homework_data, practice_data):
        """分析学习数据"""
        analytics = defaultdict(dict)
        
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT domain, point_name FROM knowledge_points WHERE subject = ?', (subject,))
        knowledge_points = cursor.fetchall()
        conn.close()
        
        domain_points = defaultdict(list)
        for domain, point in knowledge_points:
            domain_points[domain].append(point)
        
        for domain, points in domain_points.items():
            for point in points:
                correct_rate = self._calculate_point_correct_rate(user_id, subject, domain, point, 
                                                                   exam_data, homework_data, practice_data)
                practice_count = random.randint(5, 50)
                error_count = int(practice_count * (1 - correct_rate))
                
                trend = self._calculate_trend(correct_rate)
                skill_level = self._determine_skill_level(correct_rate)
                
                analytics[domain][point] = {
                    'correct_rate': round(correct_rate, 2),
                    'practice_count': practice_count,
                    'error_count': error_count,
                    'trend': trend,
                    'skill_level': skill_level
                }
                
                self._update_learning_analytics(user_id, subject, domain, point, correct_rate, 
                                               practice_count, error_count, trend, skill_level)
        
        return analytics

    def _calculate_point_correct_rate(self, user_id, subject, domain, point, exam_data, homework_data, practice_data):
        """计算知识点正确率"""
        weights = {'exam': 0.4, 'homework': 0.3, 'practice': 0.3}
        total_weight = 0
        total_score = 0
        
        if exam_data:
            point_score = exam_data.get(point, random.uniform(0.3, 0.95))
            total_score += point_score * weights['exam']
            total_weight += weights['exam']
        
        if homework_data:
            point_score = homework_data.get(point, random.uniform(0.4, 0.9))
            total_score += point_score * weights['homework']
            total_weight += weights['homework']
        
        if practice_data:
            point_score = practice_data.get(point, random.uniform(0.5, 0.95))
            total_score += point_score * weights['practice']
            total_weight += weights['practice']
        
        if total_weight == 0:
            return random.uniform(0.4, 0.8)
        
        return total_score / total_weight

    def _calculate_trend(self, correct_rate):
        """计算趋势"""
        recent_changes = random.uniform(-0.15, 0.15)
        if recent_changes > 0.05:
            return 'improving'
        elif recent_changes < -0.05:
            return 'declining'
        else:
            return 'stable'

    def _determine_skill_level(self, correct_rate):
        """确定技能等级"""
        if correct_rate >= 0.9:
            return '精通'
        elif correct_rate >= 0.7:
            return '掌握良好'
        elif correct_rate >= 0.5:
            return '需要巩固'
        else:
            return '基础薄弱'

    def _calculate_overall_score(self, analytics):
        """计算综合得分"""
        total_score = 0
        total_count = 0
        
        for domain, points in analytics.items():
            for point, data in points.items():
                total_score += data['correct_rate'] * 100
                total_count += 1
        
        if total_count == 0:
            return 0
        
        return total_score / total_count

    def _determine_diagnosis_level(self, overall_score, gap_count):
        """确定诊断等级"""
        if overall_score >= 90:
            return 'excellent'
        elif overall_score >= 70:
            return 'normal'
        elif overall_score >= 50:
            return 'warning'
        else:
            return 'critical'

    def _generate_recommendations(self, subject, knowledge_gaps, weak_areas, strong_areas, overall_score):
        """生成改进建议"""
        recommendations = []
        
        if knowledge_gaps:
            recommendations.append({
                'priority': 'high',
                'title': '重点补漏',
                'content': f'发现{len(knowledge_gaps)}个知识薄弱点，建议优先复习：{", ".join(knowledge_gaps[:3])}'
            })
        
        if weak_areas:
            recommendations.append({
                'priority': 'medium',
                'title': '强化练习',
                'content': f'在以下领域需要加强练习：{", ".join(weak_areas[:3])}'
            })
        
        if strong_areas:
            recommendations.append({
                'priority': 'low',
                'title': '保持优势',
                'content': f'以下领域掌握良好，建议保持并拓展：{", ".join(strong_areas[:3])}'
            })
        
        if overall_score < 60:
            recommendations.append({
                'priority': 'high',
                'title': '学习计划调整',
                'content': '当前成绩偏低，建议重新制定学习计划，增加练习时间'
            })
        
        if overall_score >= 80:
            recommendations.append({
                'priority': 'medium',
                'title': '挑战提升',
                'content': '成绩优秀，建议尝试更高难度的题目，挑战自我'
            })
        
        recommendations.append({
            'priority': 'medium',
            'title': '定期复习',
            'content': '建议每周进行一次知识回顾，巩固所学内容'
        })
        
        return recommendations

    def _generate_improvement_plan(self, record_id, user_id, subject, knowledge_gaps, weak_areas):
        """生成改进计划"""
        tasks = []
        
        for idx, gap in enumerate(knowledge_gaps[:5]):
            task_id = hashlib.md5(f"{user_id}{subject}{gap}{idx}".encode()).hexdigest()[:16]
            deadline = (datetime.now() + timedelta(days=(idx + 1) * 3)).isoformat()
            
            tasks.append({
                'task_id': task_id,
                'knowledge_point': gap,
                'task_type': 'practice',
                'task_content': f'针对"{gap}"进行专项练习，建议完成至少20道相关题目',
                'target_score': 0.85,
                'current_score': 0.3,
                'status': 'pending',
                'deadline': deadline
            })
        
        for idx, area in enumerate(weak_areas[:3]):
            task_id = hashlib.md5(f"{user_id}{subject}{area}review".encode()).hexdigest()[:16]
            
            tasks.append({
                'task_id': task_id,
                'knowledge_point': area,
                'task_type': 'review',
                'task_content': f'复习"{area}"相关知识点，整理错题并分析原因',
                'target_score': 0.8,
                'current_score': 0.5,
                'status': 'pending',
                'deadline': (datetime.now() + timedelta(days=(idx + 1) * 5)).isoformat()
            })
        
        self._save_improvement_tasks(record_id, user_id, subject, tasks)
        
        return tasks

    def _save_diagnosis_record(self, record_id, user_id, subject, diagnosis_level, overall_score, 
                              knowledge_gaps, weak_areas, strong_areas, recommendations, improvement_plan):
        """保存诊断记录"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO diagnosis_records 
            (record_id, user_id, subject, diagnosis_level, overall_score, 
             knowledge_gaps, weak_areas, strong_areas, recommendations, improvement_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record_id, user_id, subject, diagnosis_level, overall_score,
              json.dumps(knowledge_gaps), json.dumps(weak_areas), json.dumps(strong_areas),
              json.dumps(recommendations), json.dumps(improvement_plan)))
        
        cursor.execute('''
            INSERT INTO diagnosis_history 
            (record_id, user_id, subject, diagnosis_level, overall_score, knowledge_gaps, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (record_id, user_id, subject, diagnosis_level, overall_score, 
              json.dumps(knowledge_gaps), json.dumps(recommendations)))
        
        conn.commit()
        conn.close()

    def _update_learning_analytics(self, user_id, subject, domain, knowledge_point, 
                                   correct_rate, practice_count, error_count, trend, skill_level):
        """更新学习分析数据"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_analytics WHERE user_id = ? AND subject = ? AND knowledge_point = ?',
                      (user_id, subject, knowledge_point))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE learning_analytics 
                SET correct_rate = ?, practice_count = ?, error_count = ?, trend = ?, skill_level = ?, updated_at = ?
                WHERE user_id = ? AND subject = ? AND knowledge_point = ?
            ''', (correct_rate, practice_count, error_count, trend, skill_level, datetime.now().isoformat(),
                  user_id, subject, knowledge_point))
        else:
            analytics_id = hashlib.md5(f"{user_id}{subject}{knowledge_point}".encode()).hexdigest()[:16]
            cursor.execute('''
                INSERT INTO learning_analytics 
                (analytics_id, user_id, subject, domain, knowledge_point, 
                 correct_rate, practice_count, error_count, trend, skill_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (analytics_id, user_id, subject, domain, knowledge_point,
                  correct_rate, practice_count, error_count, trend, skill_level))
        
        conn.commit()
        conn.close()

    def _save_improvement_tasks(self, record_id, user_id, subject, tasks):
        """保存改进任务"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        for task in tasks:
            cursor.execute('SELECT * FROM improvement_tasks WHERE task_id = ?', (task['task_id'],))
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute('''
                    INSERT INTO improvement_tasks 
                    (task_id, record_id, user_id, subject, knowledge_point, task_type, 
                     task_content, target_score, current_score, status, deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (task['task_id'], record_id, user_id, subject, task['knowledge_point'], task['task_type'],
                      task['task_content'], task['target_score'], task['current_score'], 
                      task['status'], task['deadline']))
        
        conn.commit()
        conn.close()

    def get_diagnosis(self, record_id):
        """获取诊断记录"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM diagnosis_records WHERE record_id = ?', (record_id,))
        record = cursor.fetchone()
        
        if record:
            conn.close()
            return {
                'success': True,
                'diagnosis': {
                    'record_id': record[1],
                    'user_id': record[2],
                    'subject': record[3],
                    'diagnosis_level': record[4],
                    'overall_score': record[5],
                    'knowledge_gaps': json.loads(record[6]) if record[6] else [],
                    'weak_areas': json.loads(record[7]) if record[7] else [],
                    'strong_areas': json.loads(record[8]) if record[8] else [],
                    'recommendations': json.loads(record[9]) if record[9] else [],
                    'improvement_plan': json.loads(record[10]) if record[10] else [],
                    'created_at': record[11],
                    'updated_at': record[12]
                }
            }
        
        conn.close()
        return {'success': False, 'error': '诊断记录不存在'}

    def list_diagnoses(self, user_id=None, subject=None, limit=20):
        """列出诊断记录"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM diagnosis_records WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        result = []
        for r in records:
            result.append({
                'record_id': r[1],
                'user_id': r[2],
                'subject': r[3],
                'diagnosis_level': r[4],
                'overall_score': r[5],
                'created_at': r[11]
            })
        
        return {'success': True, 'diagnoses': result}

    def get_learning_analytics(self, user_id, subject):
        """获取学习分析数据"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_analytics WHERE user_id = ? AND subject = ?', (user_id, subject))
        records = cursor.fetchall()
        conn.close()
        
        analytics = defaultdict(list)
        for r in records:
            analytics[r[4]].append({
                'knowledge_point': r[5],
                'correct_rate': r[6],
                'practice_count': r[7],
                'error_count': r[8],
                'trend': r[9],
                'skill_level': r[10]
            })
        
        return {'success': True, 'analytics': analytics}

    def get_improvement_tasks(self, user_id, subject=None):
        """获取改进任务"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM improvement_tasks WHERE user_id = ?'
        params = [user_id]
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        query += ' ORDER BY deadline ASC'
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        conn.close()
        
        result = []
        for t in tasks:
            result.append({
                'task_id': t[1],
                'record_id': t[2],
                'user_id': t[3],
                'subject': t[4],
                'knowledge_point': t[5],
                'task_type': t[6],
                'task_content': t[7],
                'target_score': t[8],
                'current_score': t[9],
                'status': t[10],
                'deadline': t[11],
                'created_at': t[12],
                'completed_at': t[13]
            })
        
        return {'success': True, 'tasks': result}

    def update_task_status(self, task_id, status, current_score=None):
        """更新任务状态"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        if current_score is not None:
            cursor.execute('''
                UPDATE improvement_tasks 
                SET status = ?, current_score = ?, completed_at = ?
                WHERE task_id = ?
            ''', (status, current_score, datetime.now().isoformat() if status == 'completed' else None, task_id))
        else:
            cursor.execute('''
                UPDATE improvement_tasks 
                SET status = ?, completed_at = ?
                WHERE task_id = ?
            ''', (status, datetime.now().isoformat() if status == 'completed' else None, task_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'task_id': task_id, 'status': status}

    def get_knowledge_points(self, subject):
        """获取知识点列表"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM knowledge_points WHERE subject = ?', (subject,))
        points = cursor.fetchall()
        conn.close()
        
        result = []
        for p in points:
            result.append({
                'point_id': p[1],
                'subject': p[2],
                'domain': p[3],
                'point_name': p[4],
                'difficulty_level': p[5],
                'weight': p[7]
            })
        
        return {'success': True, 'knowledge_points': result}

    def get_diagnosis_history(self, user_id, subject=None):
        """获取诊断历史"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM diagnosis_history WHERE user_id = ?'
        params = [user_id]
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        query += ' ORDER BY created_at DESC LIMIT 10'
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        result = []
        for r in records:
            result.append({
                'record_id': r[1],
                'user_id': r[2],
                'subject': r[3],
                'diagnosis_level': r[4],
                'overall_score': r[5],
                'knowledge_gaps': json.loads(r[6]) if r[6] else [],
                'created_at': r[8]
            })
        
        return {'success': True, 'history': result}

    def generate_report(self, user_id, subject):
        """生成诊断报告"""
        diagnosis = self.diagnose_learning(user_id, subject)
        
        if not diagnosis['success']:
            return diagnosis
        
        report = {
            'report_id': hashlib.md5(f"{user_id}{subject}{datetime.now()}".encode()).hexdigest()[:16],
            'user_id': user_id,
            'subject': subject,
            'report_date': datetime.now().isoformat(),
            'overall_summary': self._generate_overall_summary(diagnosis),
            'detailed_analysis': self._generate_detailed_analysis(diagnosis),
            'improvement_recommendations': diagnosis['recommendations'],
            'action_plan': diagnosis['improvement_plan'],
            'score_history': self.get_diagnosis_history(user_id, subject)['history']
        }
        
        return {'success': True, 'report': report}

    def _generate_overall_summary(self, diagnosis):
        """生成综合摘要"""
        level_labels = {'critical': '严重', 'warning': '警告', 'normal': '正常', 'excellent': '优秀'}
        
        summary = {
            'diagnosis_level': level_labels[diagnosis['diagnosis_level']],
            'overall_score': diagnosis['overall_score'],
            'knowledge_gap_count': len(diagnosis['knowledge_gaps']),
            'weak_area_count': len(diagnosis['weak_areas']),
            'strong_area_count': len(diagnosis['strong_areas']),
            'recommendation_count': len(diagnosis['recommendations'])
        }
        
        return summary

    def _generate_detailed_analysis(self, diagnosis):
        """生成详细分析"""
        analysis = []
        
        for domain, points in diagnosis['analytics'].items():
            domain_avg = sum(p['correct_rate'] for p in points.values()) / len(points)
            domain_items = []
            
            for point, data in points.items():
                domain_items.append({
                    'point_name': point,
                    'correct_rate': data['correct_rate'],
                    'skill_level': data['skill_level'],
                    'trend': data['trend'],
                    'practice_count': data['practice_count'],
                    'error_count': data['error_count']
                })
            
            analysis.append({
                'domain': domain,
                'domain_average': round(domain_avg, 2),
                'items': domain_items
            })
        
        return analysis

    def list_diagnoses(self, user_id=None, subject=None, limit=20):
        """列出诊断记录"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM diagnosis_records WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        result = []
        for r in records:
            result.append({
                'record_id': r[1],
                'user_id': r[2],
                'subject': r[3],
                'diagnosis_level': r[4],
                'overall_score': r[5],
                'created_at': r[11]
            })
        
        return {'success': True, 'diagnoses': result}

    def update_task_status(self, task_id, status, current_score=None):
        """更新任务状态"""
        conn = sqlite3.connect('ai_diagnosis.db')
        cursor = conn.cursor()
        
        if current_score is not None:
            cursor.execute('''
                UPDATE improvement_tasks 
                SET status = ?, current_score = ?, updated_at = ?
                WHERE task_id = ?
            ''', (status, current_score, datetime.now().isoformat(), task_id))
        else:
            cursor.execute('''
                UPDATE improvement_tasks 
                SET status = ?, updated_at = ?
                WHERE task_id = ?
            ''', (status, datetime.now().isoformat(), task_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'task_id': task_id, 'status': status}

from datetime import timedelta
ai_learning_diagnosis = AILearningDiagnosis()
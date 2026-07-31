#!/usr/bin/env python3
"""
AI学习路径推荐系统
根据学生学习情况、考试成绩、错题记录等数据，推荐个性化学习路径
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta

class AILearningPathRecommender:
    LEARNING_PHASES = ['基础巩固', '进阶提升', '专项突破', '综合强化', '冲刺阶段']
    
    LEARNING_RESOURCES = {
        '数学': {
            '函数基础': ['教材第一章', '课后习题', '在线课程A', '练习册P1-P20'],
            '导数': ['教材第三章', '导数专题', '真题训练', '模拟试卷'],
            '概率统计': ['教材第五章', '统计案例', '数据分析', '综合练习'],
            '三角函数': ['教材第二章', '三角恒等式', '图像变换', '应用实例'],
            '立体几何': ['教材第四章', '空间向量', '几何证明', '综合题']
        },
        '英语': {
            '词汇': ['单词书', '背词APP', '阅读积累', '词汇测试'],
            '语法': ['语法书', '语法精讲', '语法练习', '错题整理'],
            '阅读': ['阅读真题', '外刊阅读', '阅读技巧', '限时训练'],
            '写作': ['范文阅读', '写作模板', '仿写练习', '批改反馈']
        },
        '物理': {
            '力学': ['力学基础', '牛顿定律', '功和能', '动量守恒'],
            '电磁学': ['静电场', '恒定电流', '磁场', '电磁感应']
        },
        '化学': {
            '无机化学': ['元素周期', '化学键', '化学反应', '化学计算'],
            '有机化学': ['烃类', '烃的衍生物', '有机合成', '有机推断']
        },
        '语文': {
            '文言文': ['文言实词', '文言虚词', '文言句式', '古文阅读'],
            '现代文': ['现代文阅读', '文学鉴赏', '写作技巧', '作文训练']
        }
    }
    
    def __init__(self):
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect('ai_learning_path.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                current_phase TEXT,
                target_score INTEGER,
                estimated_time TEXT,
                path_content TEXT,
                progress TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_plan_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                resource TEXT,
                duration INTEGER,
                order_num INTEGER,
                status TEXT DEFAULT 'pending',
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_user_exam_scores(self, user_id):
        """获取用户考试成绩"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT score FROM exam_results WHERE user_id = ?', (user_id,))
        scores = cursor.fetchall()
        
        conn.close()
        
        if not scores:
            return {'avg_score': 60, 'scores': []}
        
        score_list = [s[0] for s in scores]
        return {
            'avg_score': sum(score_list) / len(score_list),
            'scores': score_list,
            'max_score': max(score_list),
            'min_score': min(score_list)
        }
    
    def _get_user_wrong_topics(self, user_id, subject):
        """获取用户错题知识点"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question_content, wrong_count FROM wrong_questions 
            WHERE user_id = ? AND subject = ? ORDER BY wrong_count DESC
        ''', (str(user_id), subject))
        records = cursor.fetchall()
        
        conn.close()
        
        topics = {}
        for content, count in records:
            if content not in topics:
                topics[content] = 0
            topics[content] += count
        
        return topics
    
    def _get_user_learning_progress(self, user_id, subject):
        """获取用户学习进度"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT topic, progress, duration FROM learning_records 
            WHERE user_id = ?
        ''', (user_id,))
        records = cursor.fetchall()
        
        conn.close()
        
        progress = {}
        total_duration = 0
        for topic, prog, dur in records:
            if subject in topic or topic in subject:
                progress[topic] = prog
                total_duration += dur
        
        return {'topics': progress, 'total_duration': total_duration}
    
    def _determine_learning_phase(self, avg_score):
        """确定学习阶段"""
        if avg_score >= 90:
            return '冲刺阶段'
        elif avg_score >= 80:
            return '综合强化'
        elif avg_score >= 70:
            return '专项突破'
        elif avg_score >= 60:
            return '进阶提升'
        else:
            return '基础巩固'
    
    def _generate_learning_plan(self, user_id, subject, exam_scores, wrong_topics, learning_progress):
        """生成学习计划"""
        avg_score = exam_scores['avg_score']
        phase = self._determine_learning_phase(avg_score)
        
        topics = list(self.LEARNING_RESOURCES.get(subject, {}).keys())
        
        weak_topics = []
        if wrong_topics:
            weak_topics = [t for t, c in sorted(wrong_topics.items(), key=lambda x: -x[1])[:3]]
        
        plan_items = []
        order_num = 1
        
        if weak_topics:
            for topic in weak_topics:
                resources = self.LEARNING_RESOURCES.get(subject, {}).get(topic, ['相关资料'])
                for resource in resources[:2]:
                    plan_items.append({
                        'topic': topic,
                        'resource': resource,
                        'duration': 60,
                        'order_num': order_num,
                        'status': 'pending'
                    })
                    order_num += 1
        
        for topic in topics:
            if topic not in weak_topics:
                progress = learning_progress.get('topics', {}).get(topic, 0)
                if progress < 0.8:
                    resources = self.LEARNING_RESOURCES.get(subject, {}).get(topic, ['相关资料'])
                    for resource in resources[:1]:
                        plan_items.append({
                            'topic': topic,
                            'resource': resource,
                            'duration': 45,
                            'order_num': order_num,
                            'status': 'pending'
                        })
                        order_num += 1
        
        estimated_days = max(1, len(plan_items) // 3)
        
        return {
            'phase': phase,
            'plan_items': plan_items,
            'estimated_days': estimated_days,
            'target_score': min(100, avg_score + 10)
        }
    
    def generate_learning_path(self, user_id, subject, target_score=None):
        """生成学习路径"""
        exam_scores = self._get_user_exam_scores(user_id)
        wrong_topics = self._get_user_wrong_topics(user_id, subject)
        learning_progress = self._get_user_learning_progress(user_id, subject)
        
        plan = self._generate_learning_plan(user_id, subject, exam_scores, wrong_topics, learning_progress)
        
        path_id = hashlib.md5(f"{user_id}{subject}{datetime.now()}".encode()).hexdigest()[:16]
        
        path_content = {
            'subject': subject,
            'current_phase': plan['phase'],
            'target_score': target_score or plan['target_score'],
            'estimated_days': plan['estimated_days'],
            'exam_scores': exam_scores,
            'weak_topics': list(wrong_topics.keys()),
            'learning_progress': learning_progress,
            'plan_items': plan['plan_items']
        }
        
        conn = sqlite3.connect('ai_learning_path.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO learning_paths 
            (path_id, user_id, subject, current_phase, target_score, estimated_time, path_content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (path_id, str(user_id), subject, plan['phase'], 
              target_score or plan['target_score'], 
              f'{plan["estimated_days"]}天', json.dumps(path_content)))
        
        for item in plan['plan_items']:
            cursor.execute('''
                INSERT INTO learning_plan_items 
                (plan_id, user_id, subject, topic, resource, duration, order_num, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (path_id, str(user_id), subject, item['topic'], item['resource'],
                  item['duration'], item['order_num'], item['status']))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'path_id': path_id,
            'user_id': user_id,
            'subject': subject,
            'current_phase': plan['phase'],
            'target_score': target_score or plan['target_score'],
            'estimated_time': f'{plan["estimated_days"]}天',
            'path_content': path_content,
            'created_at': datetime.now().isoformat()
        }
    
    def get_learning_path(self, path_id):
        """获取学习路径"""
        conn = sqlite3.connect('ai_learning_path.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_paths WHERE path_id = ?', (path_id,))
        record = cursor.fetchone()
        
        if record:
            conn.close()
            return {
                'success': True,
                'path_id': record[1],
                'user_id': record[2],
                'subject': record[3],
                'current_phase': record[4],
                'target_score': record[5],
                'estimated_time': record[6],
                'path_content': json.loads(record[7]) if record[7] else {},
                'created_at': record[9]
            }
        
        conn.close()
        return {'success': False, 'error': '学习路径不存在'}
    
    def get_user_paths(self, user_id):
        """获取用户学习路径列表"""
        conn = sqlite3.connect('ai_learning_path.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_paths WHERE user_id = ? ORDER BY created_at DESC', (str(user_id),))
        records = cursor.fetchall()
        
        paths = []
        for r in records:
            paths.append({
                'path_id': r[1],
                'subject': r[3],
                'current_phase': r[4],
                'target_score': r[5],
                'estimated_time': r[6],
                'created_at': r[9]
            })
        
        conn.close()
        return {'success': True, 'paths': paths}
    
    def update_plan_item_status(self, plan_id, order_num, status):
        """更新计划项状态"""
        conn = sqlite3.connect('ai_learning_path.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE learning_plan_items 
            SET status = ?, completed_at = ?
            WHERE plan_id = ? AND order_num = ?
        ''', (status, datetime.now().isoformat() if status == 'completed' else None, plan_id, order_num))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def get_plan_items(self, plan_id):
        """获取计划项列表"""
        conn = sqlite3.connect('ai_learning_path.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_plan_items WHERE plan_id = ? ORDER BY order_num', (plan_id,))
        records = cursor.fetchall()
        
        items = []
        for r in records:
            items.append({
                'topic': r[4],
                'resource': r[5],
                'duration': r[6],
                'order_num': r[7],
                'status': r[8],
                'completed_at': r[9]
            })
        
        conn.close()
        return {'success': True, 'items': items}

ai_learning_path_recommender = AILearningPathRecommender()
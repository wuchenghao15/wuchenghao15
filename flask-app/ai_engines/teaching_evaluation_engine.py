# -*- coding: utf-8 -*-
"""
智能教学评估引擎
评估教师教学质量、课程效果、学生学习成果，提供教学改进建议
评估维度：教学设计、教学实施、教学效果、学生满意度、专业发展
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('teaching_evaluation_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TeachingEvaluationEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class TeachingEvaluationEngine:
    """智能教学评估引擎 - 多维度教学评估与改进建议"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        # 评估指标体系：5个一级维度 × 20个二级指标
        self.indicator_system = {
            'teaching_design': {
                'name': '教学设计',
                'weight': 0.20,
                'indicators': {
                    'objective_clarity': '教学目标清晰度',
                    'content_structure': '内容结构合理性',
                    'difficulty_progression': '难度梯度设计',
                    'resource_richness': '教学资源丰富度'
                }
            },
            'teaching_implementation': {
                'name': '教学实施',
                'weight': 0.25,
                'indicators': {
                    'classroom_interaction': '课堂互动性',
                    'knowledge_delivery': '知识传授效果',
                    'student_engagement': '学生参与度',
                    'time_management': '时间管理',
                    'method_diversity': '教学方法多样性'
                }
            },
            'teaching_effect': {
                'name': '教学效果',
                'weight': 0.30,
                'indicators': {
                    'exam_pass_rate': '考试通过率',
                    'score_improvement': '成绩提升幅度',
                    'knowledge_retention': '知识保持率',
                    'skill_application': '技能应用能力',
                    'learning_efficiency': '学习效率'
                }
            },
            'student_satisfaction': {
                'name': '学生满意度',
                'weight': 0.15,
                'indicators': {
                    'teaching_attitude': '教学态度',
                    'patience': '耐心程度',
                    'accessibility': '答疑可及性',
                    'fairness': '公平性'
                }
            },
            'professional_development': {
                'name': '专业发展',
                'weight': 0.10,
                'indicators': {
                    'research_output': '教研成果',
                    'innovation': '教学创新',
                    'peer_collaboration': '同行协作'
                }
            }
        }
        self._init_database()
        self._initialized = True
        logger.info("TeachingEvaluationEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 教学评估主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teaching_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        teacher_id TEXT NOT NULL,
                        evaluator_id TEXT,
                        evaluator_role TEXT,
                        course_id TEXT,
                        course_name TEXT,
                        subject TEXT,
                        grade TEXT,
                        term TEXT,
                        eval_type TEXT DEFAULT 'comprehensive',
                        eval_period_start TEXT,
                        eval_period_end TEXT,
                        total_score REAL DEFAULT 0,
                        level TEXT DEFAULT 'pending',
                        dimensions TEXT DEFAULT '{}',
                        summary TEXT,
                        recommendations TEXT DEFAULT '[]',
                        status TEXT DEFAULT 'completed',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 学生反馈表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        evaluation_id TEXT,
                        student_id TEXT NOT NULL,
                        teacher_id TEXT NOT NULL,
                        course_id TEXT,
                        ratings TEXT DEFAULT '{}',
                        comments TEXT,
                        anonymous BOOLEAN DEFAULT 1,
                        sentiment_score REAL DEFAULT 0,
                        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (evaluation_id) REFERENCES teaching_evaluations(evaluation_id)
                    )
                ''')

                # 3. 同行评价表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS peer_reviews (
                        review_id TEXT PRIMARY KEY,
                        evaluation_id TEXT,
                        reviewer_id TEXT NOT NULL,
                        reviewee_id TEXT NOT NULL,
                        course_id TEXT,
                        ratings TEXT DEFAULT '{}',
                        strengths TEXT,
                        improvements TEXT,
                        overall_comment TEXT,
                        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (evaluation_id) REFERENCES teaching_evaluations(evaluation_id)
                    )
                ''')

                # 4. 教学改进计划表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teaching_improvement_plans (
                        plan_id TEXT PRIMARY KEY,
                        teacher_id TEXT NOT NULL,
                        evaluation_id TEXT,
                        target_dimension TEXT,
                        current_score REAL,
                        target_score REAL,
                        actions TEXT DEFAULT '[]',
                        timeline TEXT,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (evaluation_id) REFERENCES teaching_evaluations(evaluation_id)
                    )
                ''')

                # 5. 评估历史快照表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        teacher_id TEXT NOT NULL,
                        snapshot_date TEXT,
                        total_score REAL,
                        level TEXT,
                        dimension_scores TEXT DEFAULT '{}',
                        student_count INTEGER,
                        feedback_count INTEGER,
                        rank_in_subject INTEGER,
                        trend TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_te_teacher ON teaching_evaluations(teacher_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sf_teacher ON student_feedback(teacher_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pr_reviewee ON peer_reviews(reviewee_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tip_teacher ON teaching_improvement_plans(teacher_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_es_teacher ON evaluation_snapshots(teacher_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化教学评估数据库失败: {e}")

    # ==================== 评估核心方法 ====================

    def create_evaluation(self, teacher_id: str, course_id: str = None,
                          course_name: str = None, subject: str = None,
                          grade: str = None, term: str = None,
                          evaluator_id: str = None, evaluator_role: str = 'auto',
                          eval_type: str = 'comprehensive',
                          eval_period_start: str = None,
                          eval_period_end: str = None) -> Dict[str, Any]:
        """创建教学评估任务"""
        with self._lock:
            try:
                evaluation_id = f"eval_{int(time.time())}_{teacher_id}"
                period_end = eval_period_end or datetime.now().isoformat()
                period_start = eval_period_start or (datetime.now() - timedelta(days=30)).isoformat()

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teaching_evaluations
                        (evaluation_id, teacher_id, evaluator_id, evaluator_role,
                         course_id, course_name, subject, grade, term, eval_type,
                         eval_period_start, eval_period_end, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    ''', (evaluation_id, teacher_id, evaluator_id, evaluator_role,
                          course_id, course_name, subject, grade, term, eval_type,
                          period_start, period_end))
                    conn.commit()

                return {
                    'success': True,
                    'evaluation_id': evaluation_id,
                    'message': '教学评估任务已创建'
                }
            except Exception as e:
                logger.error(f"创建教学评估任务失败: {e}")
                return {'success': False, 'error': str(e)}

    def submit_student_feedback(self, teacher_id: str, student_id: str,
                                ratings: Dict[str, float], comments: str = None,
                                course_id: str = None, anonymous: bool = True,
                                evaluation_id: str = None) -> Dict[str, Any]:
        """提交学生反馈"""
        with self._lock:
            try:
                feedback_id = f"fb_{int(time.time() * 1000)}_{student_id}"
                sentiment = self._analyze_sentiment(comments) if comments else 0.0

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO student_feedback
                        (feedback_id, evaluation_id, student_id, teacher_id,
                         course_id, ratings, comments, anonymous, sentiment_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (feedback_id, evaluation_id, student_id, teacher_id,
                          course_id, json.dumps(ratings, ensure_ascii=False),
                          comments, 1 if anonymous else 0, sentiment))
                    conn.commit()

                return {
                    'success': True,
                    'feedback_id': feedback_id,
                    'sentiment_score': round(sentiment, 2),
                    'message': '学生反馈已提交'
                }
            except Exception as e:
                logger.error(f"提交学生反馈失败: {e}")
                return {'success': False, 'error': str(e)}

    def submit_peer_review(self, reviewer_id: str, reviewee_id: str,
                           ratings: Dict[str, float], strengths: str = None,
                           improvements: str = None, overall_comment: str = None,
                           course_id: str = None,
                           evaluation_id: str = None) -> Dict[str, Any]:
        """提交同行评价"""
        with self._lock:
            try:
                review_id = f"pr_{int(time.time() * 1000)}_{reviewer_id}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO peer_reviews
                        (review_id, evaluation_id, reviewer_id, reviewee_id,
                         course_id, ratings, strengths, improvements, overall_comment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (review_id, evaluation_id, reviewer_id, reviewee_id,
                          course_id, json.dumps(ratings, ensure_ascii=False),
                          strengths, improvements, overall_comment))
                    conn.commit()

                return {
                    'success': True,
                    'review_id': review_id,
                    'message': '同行评价已提交'
                }
            except Exception as e:
                logger.error(f"提交同行评价失败: {e}")
                return {'success': False, 'error': str(e)}

    def compute_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """计算教学评估结果（聚合学生反馈、同行评价、客观数据）"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 1. 获取评估基本信息
                    cursor.execute('SELECT * FROM teaching_evaluations WHERE evaluation_id = ?',
                                   (evaluation_id,))
                    eval_row = cursor.fetchone()
                    if not eval_row:
                        return {'success': False, 'message': '评估任务不存在'}

                    teacher_id = eval_row[1]

                    # 2. 聚合学生反馈
                    cursor.execute('''
                        SELECT ratings, sentiment_score FROM student_feedback
                        WHERE evaluation_id = ? OR teacher_id = ?
                    ''', (evaluation_id, teacher_id))
                    feedback_rows = cursor.fetchall()

                    student_scores = {}
                    if feedback_rows:
                        for row in feedback_rows:
                            try:
                                ratings = json.loads(row[0]) if row[0] else {}
                                for k, v in ratings.items():
                                    if isinstance(v, (int, float)):
                                        student_scores.setdefault(k, []).append(v)
                            except Exception:
                                pass

                    # 3. 聚合同行评价
                    cursor.execute('''
                        SELECT ratings FROM peer_reviews
                        WHERE evaluation_id = ? OR reviewee_id = ?
                    ''', (evaluation_id, teacher_id))
                    peer_rows = cursor.fetchall()

                    peer_scores = {}
                    for row in peer_rows:
                        try:
                            ratings = json.loads(row[0]) if row[0] else {}
                            for k, v in ratings.items():
                                if isinstance(v, (int, float)):
                                    peer_scores.setdefault(k, []).append(v)
                        except Exception:
                            pass

                    # 4. 计算各维度得分
                    dimension_scores = {}
                    for dim_key, dim_info in self.indicator_system.items():
                        dim_score = 0.0
                        indicator_count = 0
                        for ind_key in dim_info['indicators']:
                            # 优先学生反馈，其次同行评价
                            student_vals = student_scores.get(ind_key, [])
                            peer_vals = peer_scores.get(ind_key, [])
                            all_vals = student_vals + peer_vals
                            if all_vals:
                                avg = sum(all_vals) / len(all_vals)
                                dim_score += avg
                                indicator_count += 1
                        if indicator_count > 0:
                            dim_score = dim_score / indicator_count
                        else:
                            dim_score = 70.0  # 默认基线
                        dimension_scores[dim_key] = round(dim_score, 1)

                    # 5. 计算总分（加权）
                    total_score = 0.0
                    for dim_key, dim_info in self.indicator_system.items():
                        total_score += dimension_scores[dim_key] * dim_info['weight']
                    total_score = round(total_score, 1)

                    # 6. 评级
                    level = self._score_to_level(total_score)

                    # 7. 生成建议
                    recommendations = self._generate_recommendations(dimension_scores)

                    # 8. 汇总
                    summary = self._generate_summary(teacher_id, dimension_scores,
                                                     total_score, level,
                                                     len(feedback_rows), len(peer_rows))

                    # 9. 保存结果
                    cursor.execute('''
                        UPDATE teaching_evaluations
                        SET total_score = ?, level = ?, dimensions = ?,
                            summary = ?, recommendations = ?, status = 'completed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE evaluation_id = ?
                    ''', (total_score, level,
                          json.dumps(dimension_scores, ensure_ascii=False),
                          summary, json.dumps(recommendations, ensure_ascii=False),
                          evaluation_id))
                    conn.commit()

                return {
                    'success': True,
                    'evaluation_id': evaluation_id,
                    'teacher_id': teacher_id,
                    'total_score': total_score,
                    'level': level,
                    'dimensions': dimension_scores,
                    'recommendations': recommendations,
                    'summary': summary,
                    'feedback_count': len(feedback_rows),
                    'peer_review_count': len(peer_rows)
                }
            except Exception as e:
                logger.error(f"计算教学评估结果失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """获取评估详情"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM teaching_evaluations WHERE evaluation_id = ?',
                               (evaluation_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '评估不存在'}

                cols = ['evaluation_id', 'teacher_id', 'evaluator_id', 'evaluator_role',
                        'course_id', 'course_name', 'subject', 'grade', 'term',
                        'eval_type', 'eval_period_start', 'eval_period_end',
                        'total_score', 'level', 'dimensions', 'summary',
                        'recommendations', 'status', 'created_at', 'updated_at']
                result = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}

                # 解析 JSON
                for k in ['dimensions', 'recommendations']:
                    if result.get(k):
                        try:
                            result[k] = json.loads(result[k])
                        except Exception:
                            pass

                return {'success': True, 'evaluation': result}
        except Exception as e:
            logger.error(f"获取评估详情失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_teacher_evaluations(self, teacher_id: str, limit: int = 20) -> Dict[str, Any]:
        """获取教师历史评估"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT evaluation_id, course_name, subject, term,
                           total_score, level, status, created_at
                    FROM teaching_evaluations
                    WHERE teacher_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (teacher_id, limit))
                rows = cursor.fetchall()

                evaluations = [{
                    'evaluation_id': r[0], 'course_name': r[1], 'subject': r[2],
                    'term': r[3], 'total_score': r[4], 'level': r[5],
                    'status': r[6], 'created_at': r[7]
                } for r in rows]

                return {
                    'success': True,
                    'teacher_id': teacher_id,
                    'evaluations': evaluations,
                    'count': len(evaluations)
                }
        except Exception as e:
            logger.error(f"获取教师历史评估失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 改进计划 ====================

    def create_improvement_plan(self, teacher_id: str, target_dimension: str,
                                 current_score: float, target_score: float,
                                 actions: List[str], timeline: str,
                                 evaluation_id: str = None) -> Dict[str, Any]:
        """创建教学改进计划"""
        with self._lock:
            try:
                plan_id = f"plan_{int(time.time())}_{teacher_id}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teaching_improvement_plans
                        (plan_id, teacher_id, evaluation_id, target_dimension,
                         current_score, target_score, actions, timeline)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (plan_id, teacher_id, evaluation_id, target_dimension,
                          current_score, target_score,
                          json.dumps(actions, ensure_ascii=False), timeline))
                    conn.commit()

                return {
                    'success': True,
                    'plan_id': plan_id,
                    'message': '改进计划已创建'
                }
            except Exception as e:
                logger.error(f"创建改进计划失败: {e}")
                return {'success': False, 'error': str(e)}

    def update_plan_progress(self, plan_id: str, progress: float,
                             status: str = None) -> Dict[str, Any]:
        """更新改进计划进度"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    if status:
                        cursor.execute('''
                            UPDATE teaching_improvement_plans
                            SET progress = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE plan_id = ?
                        ''', (progress, status, plan_id))
                    else:
                        cursor.execute('''
                            UPDATE teaching_improvement_plans
                            SET progress = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE plan_id = ?
                        ''', (progress, plan_id))
                    conn.commit()

                return {'success': True, 'plan_id': plan_id, 'progress': progress}
            except Exception as e:
                logger.error(f"更新改进计划进度失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_improvement_plans(self, teacher_id: str, status: str = None) -> Dict[str, Any]:
        """获取教师改进计划"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT plan_id, target_dimension, current_score, target_score,
                                actions, timeline, progress, status, created_at, updated_at
                         FROM teaching_improvement_plans WHERE teacher_id = ?'''
                params = [teacher_id]
                if status:
                    sql += ' AND status = ?'
                    params.append(status)
                sql += ' ORDER BY created_at DESC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                plans = []
                for r in rows:
                    actions = r[5]
                    try:
                        actions = json.loads(actions) if actions else []
                    except Exception:
                        actions = []
                    plans.append({
                        'plan_id': r[0], 'target_dimension': r[1],
                        'current_score': r[2], 'target_score': r[3],
                        'actions': actions, 'timeline': r[5],
                        'progress': r[6], 'status': r[7],
                        'created_at': r[8], 'updated_at': r[9]
                    })

                return {
                    'success': True,
                    'teacher_id': teacher_id,
                    'plans': plans,
                    'count': len(plans)
                }
        except Exception as e:
            logger.error(f"获取改进计划失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 排名与统计 ====================

    def get_teacher_ranking(self, subject: str = None, grade: str = None,
                            limit: int = 20) -> Dict[str, Any]:
        """获取教师排名"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''
                    SELECT teacher_id, MAX(total_score) as best_score, MAX(created_at) as latest
                    FROM teaching_evaluations
                    WHERE status = 'completed'
                '''
                params = []
                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)
                if grade:
                    sql += ' AND grade = ?'
                    params.append(grade)
                sql += ' GROUP BY teacher_id ORDER BY best_score DESC LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                rankings = [{
                    'rank': idx + 1,
                    'teacher_id': r[0],
                    'best_score': r[1],
                    'latest_eval': r[2]
                } for idx, r in enumerate(rows)]

                return {
                    'success': True,
                    'rankings': rankings,
                    'subject': subject,
                    'grade': grade
                }
        except Exception as e:
            logger.error(f"获取教师排名失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM teaching_evaluations')
                eval_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM student_feedback')
                feedback_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM peer_reviews')
                review_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM teaching_improvement_plans')
                plan_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM evaluation_snapshots')
                snapshot_count = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(total_score) FROM teaching_evaluations WHERE status = "completed"')
                avg_score_row = cursor.fetchone()
                avg_score = avg_score_row[0] if avg_score_row and avg_score_row[0] else 0

                return {
                    'success': True,
                    'evaluations': eval_count,
                    'student_feedback': feedback_count,
                    'peer_reviews': review_count,
                    'improvement_plans': plan_count,
                    'snapshots': snapshot_count,
                    'avg_score': round(avg_score, 1)
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 内部辅助方法 ====================

    def _analyze_sentiment(self, text: str) -> float:
        """简易情感分析（基于关键词）"""
        if not text:
            return 0.0
        positive_keywords = ['好', '优秀', '棒', '耐心', '清晰', '有趣', '负责', '认真', '喜欢', '感谢', '推荐']
        negative_keywords = ['差', '糟糕', '无聊', '敷衍', '不清晰', '不喜欢', '失望', '建议改进', '不耐心']

        pos = sum(1 for k in positive_keywords if k in text)
        neg = sum(1 for k in negative_keywords if k in text)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def _score_to_level(self, score: float) -> str:
        """分数转评级"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'qualified'
        elif score >= 60:
            return 'basic'
        else:
            return 'needs_improvement'

    def _generate_recommendations(self, dimension_scores: Dict[str, float]) -> List[str]:
        """生成教学改进建议"""
        recs = []
        sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1])

        # 最低维度优先
        for dim_key, score in sorted_dims[:3]:
            if score < 70:
                dim_name = self.indicator_system[dim_key]['name']
                if dim_key == 'teaching_design':
                    recs.append(f"加强教学设计：明确教学目标，优化内容结构，提供多样化教学资源")
                elif dim_key == 'teaching_implementation':
                    recs.append(f"改进教学实施：增加课堂互动，丰富教学方法，提高学生参与度")
                elif dim_key == 'teaching_effect':
                    recs.append(f"提升教学效果：关注学习困难学生，加强课后辅导，优化复习策略")
                elif dim_key == 'student_satisfaction':
                    recs.append(f"提高学生满意度：增加答疑时间，关注学生反馈，改善教学态度")
                elif dim_key == 'professional_development':
                    recs.append(f"加强专业发展：参与教研活动，更新教学理念，开展教学创新")

        if not recs:
            recs.append("整体教学评估良好，建议保持现有教学水平并持续优化")

        return recs[:5]

    def _generate_summary(self, teacher_id: str, dimensions: Dict[str, float],
                          total_score: float, level: str,
                          feedback_count: int, peer_count: int) -> str:
        """生成评估摘要"""
        level_map = {
            'excellent': '优秀',
            'good': '良好',
            'qualified': '合格',
            'basic': '基本合格',
            'needs_improvement': '需改进'
        }
        level_cn = level_map.get(level, level)

        # 找最强和最弱维度
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_dims[0] if sorted_dims else None
        weakest = sorted_dims[-1] if sorted_dims else None

        strongest_name = self.indicator_system[strongest[0]]['name'] if strongest else ''
        weakest_name = self.indicator_system[weakest[0]]['name'] if weakest else ''

        summary = (f"教师 {teacher_id} 综合评估得分 {total_score} 分，评级：{level_cn}。"
                   f"共收到 {feedback_count} 条学生反馈和 {peer_count} 条同行评价。")
        if strongest:
            summary += f"优势维度：{strongest_name}（{strongest[1]}分）。"
        if weakest:
            summary += f"待改进维度：{weakest_name}（{weakest[1]}分）。"

        return summary


# 单例实例
teaching_evaluation_engine = TeachingEvaluationEngine()

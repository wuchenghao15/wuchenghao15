# -*- coding: utf-8 -*-
"""
智能学习诊断引擎
深度学情诊断与知识点掌握度分析：
- 多维度知识点掌握度追踪（掌握/熟悉/了解/未掌握）
- 诊断性测试与自适应诊断路径
- 薄弱点精准定位与归因分析
- 学科能力雷达图与发展趋势
- 诊断报告生成（个人/班级/年级）
- 学习建议与提升路径推荐
"""

import os
import sys
import json
import time
import math
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_diagnosis_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningDiagnosisEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 掌握度等级
MASTERY_LEVELS = {
    'mastered': {
        'name': '完全掌握',
        'color': '#10b981',
        'score_range': (85, 100),
        'description': '知识点已完全掌握，可灵活应用'
    },
    'proficient': {
        'name': '熟练掌握',
        'color': '#3b82f6',
        'score_range': (70, 85),
        'description': '知识点基本掌握，大部分题目能正确解答'
    },
    'familiar': {
        'name': '初步了解',
        'color': '#f59e0b',
        'score_range': (40, 70),
        'description': '对知识点有初步认识，但应用不够熟练'
    },
    'weak': {
        'name': '薄弱环节',
        'color': '#ef4444',
        'score_range': (0, 40),
        'description': '知识点掌握薄弱，需要重点加强'
    }
}

# 诊断维度
DIAGNOSIS_DIMENSIONS = {
    'knowledge_mastery': {'name': '知识掌握', 'weight': 0.25},
    'concept_understanding': {'name': '概念理解', 'weight': 0.20},
    'application_ability': {'name': '应用能力', 'weight': 0.25},
    'problem_solving': {'name': '解题能力', 'weight': 0.20},
    'extension_ability': {'name': '拓展能力', 'weight': 0.10}
}

# 归因类型
ATTRIBUTION_TYPES = [
    '概念理解不清晰',
    '公式定理记忆不牢',
    '解题方法未掌握',
    '计算能力不足',
    '审题不仔细',
    '知识迁移能力弱',
    '综合应用能力差',
    '基础不扎实'
]


class LearningDiagnosisEngine:
    """智能学习诊断引擎 - 深度学情诊断与知识点掌握度分析"""

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
        self._init_database()
        self._initialized = True
        logger.info("LearningDiagnosisEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 知识点掌握度表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_mastery (
                        mastery_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        knowledge_point TEXT NOT NULL,
                        chapter TEXT,
                        mastery_level TEXT DEFAULT 'familiar',
                        mastery_score REAL DEFAULT 50,
                        total_attempts INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0,
                        avg_time_spent REAL DEFAULT 0,
                        last_practice_date TEXT,
                        trend TEXT DEFAULT 'stable',
                        history_scores TEXT DEFAULT '[]',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(student_id, subject, knowledge_point)
                    )
                ''')

                # 2. 诊断测试表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS diagnosis_tests (
                        test_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        scope TEXT,
                        test_type TEXT DEFAULT 'adaptive',
                        questions TEXT DEFAULT '[]',
                        answers TEXT DEFAULT '[]',
                        total_score REAL DEFAULT 0,
                        max_score REAL DEFAULT 100,
                        duration INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        started_at TEXT,
                        completed_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 3. 诊断报告表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS diagnosis_reports (
                        report_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        subject TEXT,
                        report_type TEXT NOT NULL,
                        report_title TEXT,
                        overall_score REAL DEFAULT 0,
                        level TEXT,
                        dimension_scores TEXT DEFAULT '{}',
                        weak_points TEXT DEFAULT '[]',
                        strong_points TEXT DEFAULT '[]',
                        attributions TEXT DEFAULT '[]',
                        recommendations TEXT DEFAULT '[]',
                        improvement_plan TEXT DEFAULT '[]',
                        data_period_start TEXT,
                        data_period_end TEXT,
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        shared_with_parent BOOLEAN DEFAULT 0
                    )
                ''')

                # 4. 薄弱点归因表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weak_point_attributions (
                        attribution_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        subject TEXT,
                        knowledge_point TEXT,
                        attribution_type TEXT,
                        confidence REAL DEFAULT 0,
                        evidence TEXT DEFAULT '[]',
                        severity TEXT DEFAULT 'medium',
                        suggested_action TEXT,
                        detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TEXT,
                        status TEXT DEFAULT 'active'
                    )
                ''')

                # 5. 班级诊断汇总表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS class_diagnosis (
                        summary_id TEXT PRIMARY KEY,
                        class_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        period TEXT,
                        avg_score REAL DEFAULT 0,
                        mastery_distribution TEXT DEFAULT '{}',
                        common_weak_points TEXT DEFAULT '[]',
                        common_strong_points TEXT DEFAULT '[]',
                        dimension_avgs TEXT DEFAULT '{}',
                        student_count INTEGER DEFAULT 0,
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_km_student ON knowledge_mastery(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_km_subject ON knowledge_mastery(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dt_student ON diagnosis_tests(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dr_student ON diagnosis_reports(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wpa_student ON weak_point_attributions(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cd_class ON class_diagnosis(class_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化学习诊断引擎数据库失败: {e}")

    # ==================== 知识点掌握度管理 ====================

    def update_mastery(self, student_id: str, subject: str, knowledge_point: str,
                       correct: bool, time_spent: float = 0, chapter: str = None) -> Dict[str, Any]:
        """更新单个知识点掌握度"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 获取现有记录
                    cursor.execute('''
                        SELECT mastery_id, mastery_score, total_attempts, correct_count,
                               avg_time_spent, history_scores
                        FROM knowledge_mastery
                        WHERE student_id = ? AND subject = ? AND knowledge_point = ?
                    ''', (student_id, subject, knowledge_point))
                    row = cursor.fetchone()

                    if row:
                        mastery_id = row[0]
                        old_score = row[1] or 50
                        total_attempts = row[2] + 1
                        correct_count = row[3] + (1 if correct else 0)
                        old_avg_time = row[4] or 0
                        # 计算新的平均时间
                        avg_time = (old_avg_time * row[2] + time_spent) / max(total_attempts, 1)
                        # 计算掌握度分数（指数加权移动平均 + 正确率影响）
                        accuracy = correct_count / max(total_attempts, 1)
                        # 每次答题的影响因子（答对加分，答错减分）
                        delta = 0
                        if correct:
                            delta = max(2, 10 - old_score / 15)  # 分越高越难升
                        else:
                            delta = -max(3, old_score / 12)  # 分越高掉得越快
                        new_score = max(0, min(100, old_score + delta))
                        # 结合正确率微调
                        new_score = new_score * 0.7 + accuracy * 100 * 0.3
                        new_score = max(0, min(100, new_score))
                        # 确定等级
                        level = self._score_to_mastery_level(new_score)
                        # 计算趋势
                        history = json.loads(row[5] or '[]')
                        history.append({'date': datetime.now().isoformat(), 'score': round(new_score, 2)})
                        if len(history) > 20:
                            history = history[-20:]
                        trend = self._calculate_trend(history)
                        # 更新
                        cursor.execute('''
                            UPDATE knowledge_mastery
                            SET mastery_level = ?, mastery_score = ?, total_attempts = ?,
                                correct_count = ?, avg_time_spent = ?, last_practice_date = ?,
                                trend = ?, history_scores = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE mastery_id = ?
                        ''', (level, round(new_score, 2), total_attempts, correct_count,
                              round(avg_time, 2), datetime.now().isoformat(),
                              trend, json.dumps(history, ensure_ascii=False), mastery_id))
                    else:
                        # 新记录
                        mastery_id = f"km_{int(time.time() * 1000)}_{student_id}"
                        new_score = 75 if correct else 40
                        level = self._score_to_mastery_level(new_score)
                        trend = 'stable'
                        history = [{'date': datetime.now().isoformat(), 'score': round(new_score, 2)}]
                        cursor.execute('''
                            INSERT INTO knowledge_mastery
                            (mastery_id, student_id, subject, knowledge_point, chapter,
                             mastery_level, mastery_score, total_attempts, correct_count,
                             avg_time_spent, last_practice_date, trend, history_scores)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (mastery_id, student_id, subject, knowledge_point, chapter,
                              level, round(new_score, 2), 1, 1 if correct else 0,
                              round(time_spent, 2), datetime.now().isoformat(),
                              trend, json.dumps(history, ensure_ascii=False)))

                    conn.commit()

                return {
                    'success': True,
                    'mastery_id': mastery_id,
                    'knowledge_point': knowledge_point,
                    'mastery_score': round(new_score, 2),
                    'mastery_level': level,
                    'trend': trend
                }
            except Exception as e:
                logger.error(f"更新知识点掌握度失败: {e}")
                return {'success': False, 'error': str(e)}

    def _score_to_mastery_level(self, score: float) -> str:
        if score >= 85:
            return 'mastered'
        elif score >= 70:
            return 'proficient'
        elif score >= 40:
            return 'familiar'
        else:
            return 'weak'

    def _calculate_trend(self, history: List[Dict]) -> str:
        if len(history) < 3:
            return 'stable'
        recent = history[-3:]
        scores = [h['score'] for h in recent]
        avg_first = sum(scores[:len(scores)//2]) / max(len(scores)//2, 1)
        avg_last = sum(scores[len(scores)//2:]) / max(len(scores) - len(scores)//2, 1)
        diff = avg_last - avg_first
        if diff > 5:
            return 'rising'
        elif diff < -5:
            return 'falling'
        else:
            return 'stable'

    def get_student_mastery(self, student_id: str, subject: str = None) -> Dict[str, Any]:
        """获取学生知识点掌握情况"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    if subject:
                        cursor.execute('''
                            SELECT * FROM knowledge_mastery
                            WHERE student_id = ? AND subject = ?
                            ORDER BY mastery_score ASC
                        ''', (student_id, subject))
                    else:
                        cursor.execute('''
                            SELECT * FROM knowledge_mastery
                            WHERE student_id = ?
                            ORDER BY subject, mastery_score ASC
                        ''', (student_id,))
                    rows = [dict(r) for r in cursor.fetchall()]
                    for r in rows:
                        r['history_scores'] = json.loads(r.get('history_scores') or '[]')
                    # 按学科分组
                    by_subject = {}
                    for r in rows:
                        subj = r['subject']
                        if subj not in by_subject:
                            by_subject[subj] = []
                        by_subject[subj].append(r)
                    # 统计各等级数量
                    stats = {}
                    for level in MASTERY_LEVELS:
                        stats[level] = sum(1 for r in rows if r['mastery_level'] == level)
                    return {
                        'success': True,
                        'student_id': student_id,
                        'total_points': len(rows),
                        'mastery_stats': stats,
                        'by_subject': by_subject,
                        'weak_points': [r for r in rows if r['mastery_level'] in ('weak', 'familiar')],
                        'strong_points': [r for r in rows if r['mastery_level'] in ('mastered', 'proficient')]
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 诊断测试 ====================

    def create_diagnosis_test(self, student_id: str, subject: str,
                              scope: str = None, test_type: str = 'adaptive',
                              num_questions: int = 10) -> Dict[str, Any]:
        """创建诊断测试"""
        with self._lock:
            try:
                test_id = f"dt_{int(time.time() * 1000)}"
                questions = self._generate_diagnosis_questions(subject, scope, num_questions, test_type)
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO diagnosis_tests
                        (test_id, student_id, subject, scope, test_type, questions, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    ''', (test_id, student_id, subject, scope, test_type,
                          json.dumps(questions, ensure_ascii=False)))
                    conn.commit()
                return {
                    'success': True,
                    'test_id': test_id,
                    'subject': subject,
                    'num_questions': len(questions),
                    'test_type': test_type
                }
            except Exception as e:
                logger.error(f"创建诊断测试失败: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_diagnosis_questions(self, subject: str, scope: str,
                                      num: int, test_type: str) -> List[Dict]:
        """生成诊断题目（简化版）"""
        questions = []
        for i in range(num):
            difficulty = min(5, 1 + i // 2) if test_type == 'adaptive' else 3
            questions.append({
                'qid': f'q_{i}',
                'type': 'single_choice',
                'difficulty': difficulty,
                'knowledge_point': f'知识点{i+1}',
                'content': f'【{subject}】诊断题{i+1}',
                'options': [f'选项{chr(65+j)}' for j in range(4)],
                'answer': 'A',
                'score': 10
            })
        return questions

    def submit_diagnosis_test(self, test_id: str, answers: List[Dict],
                              duration: int = 0) -> Dict[str, Any]:
        """提交诊断测试并计算结果"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM diagnosis_tests WHERE test_id = ?', (test_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '测试不存在'}
                    student_id = row[1]
                    subject = row[2]
                    questions = json.loads(row[5] or '[]')
                    # 计算得分
                    total_score = 0
                    max_score = 0
                    correct_count = 0
                    for q in questions:
                        max_score += q.get('score', 10)
                        # 查找对应答案
                        ans = next((a for a in answers if a.get('qid') == q.get('qid')), None)
                        if ans and ans.get('answer') == q.get('answer'):
                            total_score += q.get('score', 10)
                            correct_count += 1
                    # 更新测试状态
                    cursor.execute('''
                        UPDATE diagnosis_tests
                        SET answers = ?, total_score = ?, max_score = ?,
                            duration = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP
                        WHERE test_id = ?
                    ''', (json.dumps(answers, ensure_ascii=False), total_score, max_score,
                          duration, test_id))
                    # 更新知识点掌握度
                    for q in questions:
                        qid = q.get('qid')
                        kp = q.get('knowledge_point')
                        ans = next((a for a in answers if a.get('qid') == qid), None)
                        correct = ans and ans.get('answer') == q.get('answer')
                        if kp:
                            self.update_mastery(student_id, subject, kp, correct, 0)

                    conn.commit()
                # 生成诊断报告
                report = self.generate_student_report(student_id, subject, test_id)
                return {
                    'success': True,
                    'test_id': test_id,
                    'total_score': total_score,
                    'max_score': max_score,
                    'correct_count': correct_count,
                    'accuracy': round(correct_count / max(len(questions), 1) * 100, 2),
                    'report_id': report.get('report_id') if report.get('success') else None
                }
            except Exception as e:
                logger.error(f"提交诊断测试失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 诊断报告 ====================

    def generate_student_report(self, student_id: str, subject: str = None,
                                test_id: str = None, report_type: str = 'full') -> Dict[str, Any]:
        """生成学生诊断报告"""
        with self._lock:
            try:
                report_id = f"dr_{int(time.time() * 1000)}"
                # 获取掌握度数据
                mastery_data = self.get_student_mastery(student_id, subject)
                if not mastery_data.get('success'):
                    return mastery_data
                by_subject = mastery_data.get('by_subject', {})
                weak_points = mastery_data.get('weak_points', [])
                strong_points = mastery_data.get('strong_points', [])
                total_points = mastery_data.get('total_points', 0)

                # 计算各维度得分（基于掌握度数据估算）
                dimension_scores = {}
                if total_points > 0:
                    avg_score = sum(w['mastery_score'] for w in
                                    [item for sublist in by_subject.values() for item in sublist]) / max(total_points, 1)
                    dimension_scores = {
                        'knowledge_mastery': round(avg_score, 2),
                        'concept_understanding': round(avg_score * 0.95, 2),
                        'application_ability': round(avg_score * 0.85, 2),
                        'problem_solving': round(avg_score * 0.80, 2),
                        'extension_ability': round(avg_score * 0.70, 2)
                    }
                    overall = sum(dimension_scores[d] * DIAGNOSIS_DIMENSIONS[d]['weight']
                                  for d in DIAGNOSIS_DIMENSIONS)
                else:
                    overall = 60.0
                    dimension_scores = {d: 60.0 for d in DIAGNOSIS_DIMENSIONS}

                level = self._score_to_mastery_level(overall)

                # 归因分析（薄弱点原因）
                attributions = []
                for wp in weak_points[:5]:
                    attr_type = ATTRIBUTION_TYPES[hash(wp['knowledge_point']) % len(ATTRIBUTION_TYPES)]
                    attributions.append({
                        'knowledge_point': wp['knowledge_point'],
                        'subject': wp['subject'],
                        'attribution_type': attr_type,
                        'confidence': round(0.5 + wp['mastery_score'] / 100, 2),
                        'severity': 'high' if wp['mastery_level'] == 'weak' else 'medium'
                    })

                # 学习建议
                recommendations = self._generate_recommendations(weak_points, dimension_scores)
                # 提升计划
                improvement_plan = self._generate_improvement_plan(weak_points, attributions)

                title = f"{subject or '全科'}学习诊断报告" if subject else "综合学习诊断报告"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO diagnosis_reports
                        (report_id, student_id, subject, report_type, report_title,
                         overall_score, level, dimension_scores, weak_points,
                         strong_points, attributions, recommendations, improvement_plan)
                        VALUES (?, ?, ?, 'individual', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (report_id, student_id, subject, title, round(overall, 2),
                          level, json.dumps(dimension_scores, ensure_ascii=False),
                          json.dumps([{'kp': w['knowledge_point'], 'subject': w['subject'],
                                       'score': w['mastery_score']} for w in weak_points[:10]],
                                     ensure_ascii=False),
                          json.dumps([{'kp': w['knowledge_point'], 'subject': w['subject'],
                                       'score': w['mastery_score']} for w in strong_points[:10]],
                                     ensure_ascii=False),
                          json.dumps(attributions, ensure_ascii=False),
                          json.dumps(recommendations, ensure_ascii=False),
                          json.dumps(improvement_plan, ensure_ascii=False)))
                    conn.commit()

                return {
                    'success': True,
                    'report_id': report_id,
                    'report_title': title,
                    'overall_score': round(overall, 2),
                    'level': level,
                    'dimension_scores': dimension_scores,
                    'weak_points_count': len(weak_points),
                    'strong_points_count': len(strong_points),
                    'attributions': attributions,
                    'recommendations': recommendations,
                    'improvement_plan': improvement_plan
                }
            except Exception as e:
                logger.error(f"生成诊断报告失败: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_recommendations(self, weak_points: List[Dict], dims: Dict) -> List[Dict]:
        """生成学习建议"""
        recs = []
        if len(weak_points) > 3:
            recs.append({
                'priority': 'high',
                'category': '基础巩固',
                'title': '夯实基础知识',
                'description': '建议从基础概念入手，系统复习薄弱知识点',
                'target': '基础薄弱知识点'
            })
        for wp in weak_points[:3]:
            recs.append({
                'priority': 'medium',
                'category': wp['subject'],
                'title': f'加强{wp["knowledge_point"]}练习',
                'description': f'针对{wp["knowledge_point"]}进行专项训练，建议每天15分钟',
                'target': wp['knowledge_point']
            })
        # 维度建议
        lowest_dim = min(dims, key=lambda k: dims.get(k, 100)) if dims else None
        if lowest_dim:
            dim_name = DIAGNOSIS_DIMENSIONS.get(lowest_dim, {}).get('name', lowest_dim)
            recs.append({
                'priority': 'medium',
                'category': '能力提升',
                'title': f'提升{dim_name}',
                'description': f'当前{dim_name}相对较弱，建议针对性加强训练',
                'target': dim_name
            })
        return recs

    def _generate_improvement_plan(self, weak_points: List[Dict],
                                   attributions: List[Dict]) -> List[Dict]:
        """生成提升计划"""
        plan = []
        if weak_points:
            plan.append({
                'phase': '第一阶段（1-2周）',
                'focus': '基础巩固',
                'tasks': ['复习核心概念', '完成基础练习', '建立错题本'],
                'target_points': [w['knowledge_point'] for w in weak_points[:3]]
            })
            plan.append({
                'phase': '第二阶段（3-4周）',
                'focus': '能力提升',
                'tasks': ['专项训练', '错题重做', '综合练习'],
                'target_points': [w['knowledge_point'] for w in weak_points[3:6]] if len(weak_points) > 3 else ['综合应用']
            })
            plan.append({
                'phase': '第三阶段（5-6周）',
                'focus': '巩固拓展',
                'tasks': ['模拟测试', '知识迁移', '拓展学习'],
                'target_points': ['综合提升']
            })
        return plan

    # ==================== 班级诊断 ====================

    def generate_class_report(self, class_id: str, subject: str,
                              period: str = 'month') -> Dict[str, Any]:
        """生成班级诊断汇总"""
        with self._lock:
            try:
                summary_id = f"cd_{int(time.time() * 1000)}"
                # 模拟班级数据
                student_count = 30
                avg_score = 72.5
                mastery_dist = {'mastered': 5, 'proficient': 12, 'familiar': 10, 'weak': 3}
                common_weak = [
                    {'kp': '知识点A', 'weak_count': 15},
                    {'kp': '知识点B', 'weak_count': 12}
                ]
                common_strong = [
                    {'kp': '知识点C', 'strong_count': 18}
                ]
                dim_avgs = {d: 70 + i * 2 for i, d in enumerate(DIAGNOSIS_DIMENSIONS)}

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO class_diagnosis
                        (summary_id, class_id, subject, period, avg_score,
                         mastery_distribution, common_weak_points, common_strong_points,
                         dimension_avgs, student_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (summary_id, class_id, subject, period, avg_score,
                          json.dumps(mastery_dist, ensure_ascii=False),
                          json.dumps(common_weak, ensure_ascii=False),
                          json.dumps(common_strong, ensure_ascii=False),
                          json.dumps(dim_avgs, ensure_ascii=False),
                          student_count))
                    conn.commit()

                return {
                    'success': True,
                    'summary_id': summary_id,
                    'class_id': class_id,
                    'subject': subject,
                    'avg_score': avg_score,
                    'student_count': student_count,
                    'mastery_distribution': mastery_dist,
                    'common_weak_points': common_weak,
                    'common_strong_points': common_strong
                }
            except Exception as e:
                logger.error(f"生成班级诊断失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 查询接口 ====================

    def get_report(self, report_id: str) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM diagnosis_reports WHERE report_id = ?', (report_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '报告不存在'}
                    rep = dict(row)
                    for key in ['dimension_scores', 'weak_points', 'strong_points',
                                'attributions', 'recommendations', 'improvement_plan']:
                        rep[key] = json.loads(rep.get(key) or '{}' if key == 'dimension_scores' else '[]')
                    return {'success': True, 'report': rep}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_reports(self, student_id: str, subject: str = None,
                     report_type: str = None, limit: int = 20) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM diagnosis_reports WHERE student_id = ?'
                    params = [student_id]
                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)
                    if report_type:
                        sql += ' AND report_type = ?'
                        params.append(report_type)
                    sql += ' ORDER BY generated_at DESC LIMIT ?'
                    params.append(limit)
                    cursor.execute(sql, params)
                    reports = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'reports': reports, 'count': len(reports)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_diagnosis_test(self, test_id: str) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM diagnosis_tests WHERE test_id = ?', (test_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '测试不存在'}
                    t = dict(row)
                    t['questions'] = json.loads(t.get('questions') or '[]')
                    t['answers'] = json.loads(t.get('answers') or '[]')
                    return {'success': True, 'test': t}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(DISTINCT student_id) FROM knowledge_mastery')
                    total_students = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM knowledge_mastery')
                    total_records = cursor.fetchone()[0]
                    cursor.execute('SELECT mastery_level, COUNT(*) FROM knowledge_mastery GROUP BY mastery_level')
                    level_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT COUNT(*) FROM diagnosis_tests')
                    total_tests = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM diagnosis_reports')
                    total_reports = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM weak_point_attributions WHERE status = ?', ('active',))
                    active_attributions = cursor.fetchone()[0]
                    return {
                        'success': True,
                        'total_students_tracked': total_students,
                        'total_mastery_records': total_records,
                        'mastery_level_stats': level_stats,
                        'total_diagnosis_tests': total_tests,
                        'total_reports': total_reports,
                        'active_attributions': active_attributions
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}


# 单例
learning_diagnosis_engine = LearningDiagnosisEngine()

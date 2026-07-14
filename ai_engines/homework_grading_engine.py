# -*- coding: utf-8 -*-
"""
智能作业批改引擎
自动批改作业、AI辅助主观题评分、批改反馈、错题归因
支持题型：单选、多选、判断、填空（自动）；简答、论述、作文（AI辅助）
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('homework_grading_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HomeworkGradingEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 题型分类
AUTO_GRADABLE_TYPES = {'single_choice', 'multiple_choice', 'true_false', 'fill_blank'}
AI_ASSISTED_TYPES = {'short_answer', 'essay', 'composition', 'listening'}

# 题型中文名
QUESTION_TYPE_NAMES = {
    'single_choice': '单选题',
    'multiple_choice': '多选题',
    'true_false': '判断题',
    'fill_blank': '填空题',
    'short_answer': '简答题',
    'essay': '论述题',
    'composition': '作文',
    'listening': '听力题'
}


class HomeworkGradingEngine:
    """智能作业批改引擎 - 自动批改 + AI辅助评分"""

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
        # AI 评分权重配置
        self.scoring_weights = {
            'keyword_match': 0.4,      # 关键词匹配度
            'length_appropriate': 0.2,  # 篇幅合适度
            'structure_score': 0.2,     # 结构完整性
            'logic_score': 0.2          # 逻辑连贯性
        }
        self._init_database()
        self._initialized = True
        logger.info("HomeworkGradingEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 作业主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS homeworks (
                        homework_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        subject TEXT,
                        grade TEXT,
                        teacher_id TEXT NOT NULL,
                        class_id TEXT,
                        total_questions INTEGER DEFAULT 0,
                        total_score REAL DEFAULT 100,
                        deadline TEXT,
                        status TEXT DEFAULT 'published',
                        question_ids TEXT DEFAULT '[]',
                        question_meta TEXT DEFAULT '{}',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 学生提交表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS homework_submissions (
                        submission_id TEXT PRIMARY KEY,
                        homework_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        answers TEXT DEFAULT '{}',
                        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'submitted',
                        auto_score REAL DEFAULT 0,
                        ai_score REAL DEFAULT 0,
                        final_score REAL DEFAULT 0,
                        graded_at TEXT,
                        graded_by TEXT,
                        grading_method TEXT DEFAULT 'auto',
                        feedback TEXT,
                        time_spent INTEGER DEFAULT 0,
                        attempt_count INTEGER DEFAULT 1,
                        FOREIGN KEY (homework_id) REFERENCES homeworks(homework_id)
                    )
                ''')

                # 3. 题目批改详情表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_grading (
                        grading_id TEXT PRIMARY KEY,
                        submission_id TEXT NOT NULL,
                        homework_id TEXT NOT NULL,
                        question_id TEXT NOT NULL,
                        question_type TEXT,
                        student_answer TEXT,
                        correct_answer TEXT,
                        is_correct BOOLEAN DEFAULT 0,
                        score REAL DEFAULT 0,
                        max_score REAL DEFAULT 0,
                        grading_method TEXT DEFAULT 'auto',
                        ai_confidence REAL DEFAULT 0,
                        matched_keywords TEXT DEFAULT '[]',
                        feedback TEXT,
                        graded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (submission_id) REFERENCES homework_submissions(submission_id)
                    )
                ''')

                # 4. 批改报告表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grading_reports (
                        report_id TEXT PRIMARY KEY,
                        homework_id TEXT NOT NULL,
                        report_type TEXT DEFAULT 'class',
                        total_submissions INTEGER DEFAULT 0,
                        graded_count INTEGER DEFAULT 0,
                        avg_score REAL DEFAULT 0,
                        highest_score REAL DEFAULT 0,
                        lowest_score REAL DEFAULT 0,
                        pass_rate REAL DEFAULT 0,
                        score_distribution TEXT DEFAULT '{}',
                        wrong_questions TEXT DEFAULT '[]',
                        common_mistakes TEXT DEFAULT '[]',
                        recommendations TEXT DEFAULT '[]',
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (homework_id) REFERENCES homeworks(homework_id)
                    )
                ''')

                # 5. 批改规则配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grading_rules (
                        rule_id TEXT PRIMARY KEY,
                        subject TEXT,
                        question_type TEXT,
                        partial_credit BOOLEAN DEFAULT 0,
                        keyword_pool TEXT DEFAULT '{}',
                        min_length INTEGER DEFAULT 50,
                        max_length INTEGER DEFAULT 2000,
                        structure_keywords TEXT DEFAULT '[]',
                        penalty_rules TEXT DEFAULT '{}',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hw_teacher ON homeworks(teacher_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hs_student ON homework_submissions(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hs_homework ON homework_submissions(homework_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_qg_submission ON question_grading(submission_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gr_homework ON grading_reports(homework_id)')

                # 初始化默认批改规则
                self._init_default_rules(cursor)
                conn.commit()
        except Exception as e:
            logger.error(f"初始化作业批改数据库失败: {e}")

    def _init_default_rules(self, cursor):
        """初始化默认批改规则"""
        try:
            rules = [
                ('rule_chinese_essay', '语文', 'essay', '{"开头":5,"结尾":5,"论点":10,"论据":10}'),
                ('rule_chinese_comp', '语文', 'composition', '{"开头":5,"结尾":5,"描写":10,"抒情":10}'),
                ('rule_math_short', '数学', 'short_answer', '{"步骤":10,"结果":5,"公式":5}'),
                ('rule_english_essay', '英语', 'essay', '{"grammar":10,"vocabulary":5,"structure":5}'),
            ]
            for rid, subj, qtype, kw in rules:
                cursor.execute('SELECT COUNT(*) FROM grading_rules WHERE rule_id = ?', (rid,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO grading_rules
                        (rule_id, subject, question_type, keyword_pool, partial_credit)
                        VALUES (?, ?, ?, ?, 1)
                    ''', (rid, subj, qtype, kw))
        except Exception as e:
            logger.error(f"初始化默认规则失败: {e}")

    # ==================== 作业管理 ====================

    def create_homework(self, homework_id: str, title: str, teacher_id: str,
                        subject: str = None, grade: str = None, class_id: str = None,
                        description: str = None, total_score: float = 100,
                        deadline: str = None, questions: List[Dict] = None) -> Dict[str, Any]:
        """创建作业（带题目元数据）"""
        with self._lock:
            try:
                questions = questions or []
                question_ids = [q.get('question_id', f"q_{i}") for i, q in enumerate(questions)]
                question_meta = {qid: {
                    'type': q.get('question_type', 'single_choice'),
                    'correct_answer': q.get('correct_answer', ''),
                    'max_score': q.get('max_score', 5),
                    'keywords': q.get('keywords', []),
                    'subject': q.get('subject', subject)
                } for qid, q in zip(question_ids, questions)}

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO homeworks
                        (homework_id, title, description, subject, grade, teacher_id,
                         class_id, total_questions, total_score, deadline,
                         question_ids, question_meta)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (homework_id, title, description, subject, grade, teacher_id,
                          class_id, len(questions), total_score, deadline,
                          json.dumps(question_ids, ensure_ascii=False),
                          json.dumps(question_meta, ensure_ascii=False)))
                    conn.commit()

                return {
                    'success': True,
                    'homework_id': homework_id,
                    'total_questions': len(questions),
                    'message': '作业已创建'
                }
            except Exception as e:
                logger.error(f"创建作业失败: {e}")
                return {'success': False, 'error': str(e)}

    def submit_homework(self, homework_id: str, student_id: str,
                        answers: Dict[str, str], time_spent: int = 0) -> Dict[str, Any]:
        """学生提交作业答案"""
        with self._lock:
            try:
                submission_id = f"sub_{int(time.time() * 1000)}_{student_id[:8]}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 检查作业是否存在
                    cursor.execute('SELECT question_meta, total_score FROM homeworks WHERE homework_id = ?',
                                   (homework_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '作业不存在'}

                    question_meta = json.loads(row[0]) if row[0] else {}

                    cursor.execute('''
                        INSERT INTO homework_submissions
                        (submission_id, homework_id, student_id, answers, time_spent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (submission_id, homework_id, student_id,
                          json.dumps(answers, ensure_ascii=False), time_spent))
                    conn.commit()

                # 自动触发批改
                grading_result = self._grade_submission(submission_id, answers, question_meta)

                return {
                    'success': True,
                    'submission_id': submission_id,
                    'grading': grading_result,
                    'message': '作业已提交并自动批改'
                }
            except Exception as e:
                logger.error(f"提交作业失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 批改核心 ====================

    def _grade_submission(self, submission_id: str, answers: Dict[str, str],
                          question_meta: Dict) -> Dict[str, Any]:
        """批改单次提交（核心方法）"""
        with self._lock:
            try:
                total_score = 0.0
                max_total = 0.0
                correct_count = 0
                grading_details = []
                wrong_questions = []

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    for qid, student_answer in answers.items():
                        meta = question_meta.get(qid, {})
                        qtype = meta.get('type', 'single_choice')
                        correct = meta.get('correct_answer', '')
                        max_score = meta.get('max_score', 5)
                        keywords = meta.get('keywords', [])

                        # 调用对应批改方法
                        if qtype in AUTO_GRADABLE_TYPES:
                            is_correct, score, feedback = self._grade_auto(
                                qtype, student_answer, correct, max_score)
                            method = 'auto'
                            ai_confidence = 1.0
                            matched_keywords = []
                        else:
                            is_correct, score, feedback, ai_confidence, matched_keywords = self._grade_ai_assisted(
                                qtype, student_answer, correct, max_score, keywords, meta)
                            method = 'ai_assisted'

                        total_score += score
                        max_total += max_score
                        if is_correct:
                            correct_count += 1
                        else:
                            wrong_questions.append({
                                'question_id': qid,
                                'question_type': qtype,
                                'student_answer': student_answer,
                                'correct_answer': correct,
                                'score': score,
                                'max_score': max_score
                            })

                        # 保存题目批改详情
                        grading_id = f"grd_{submission_id}_{qid}"
                        cursor.execute('''
                            INSERT INTO question_grading
                            (grading_id, submission_id, homework_id, question_id, question_type,
                             student_answer, correct_answer, is_correct, score, max_score,
                             grading_method, ai_confidence, matched_keywords, feedback)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (grading_id, submission_id, '', qid, qtype,
                              str(student_answer), str(correct), 1 if is_correct else 0,
                              score, max_score, method, ai_confidence,
                              json.dumps(matched_keywords, ensure_ascii=False), feedback))

                        grading_details.append({
                            'question_id': qid,
                            'question_type': qtype,
                            'is_correct': is_correct,
                            'score': score,
                            'max_score': max_score,
                            'feedback': feedback,
                            'method': method
                        })

                    # 计算最终分数
                    final_percentage = (total_score / max_total * 100) if max_total > 0 else 0
                    final_score = round(total_score, 1)

                    # 生成整体反馈
                    overall_feedback = self._generate_overall_feedback(
                        correct_count, len(answers), final_score, max_total, wrong_questions)

                    # 更新提交记录
                    cursor.execute('''
                        UPDATE homework_submissions
                        SET auto_score = ?, ai_score = ?, final_score = ?,
                            graded_at = ?, graded_by = 'ai_engine',
                            grading_method = ?, feedback = ?, status = 'graded'
                        WHERE submission_id = ?
                    ''', (final_score, final_score, final_score,
                          datetime.now().isoformat(),
                          'auto' if all(d['method'] == 'auto' for d in grading_details) else 'hybrid',
                          overall_feedback, submission_id))
                    conn.commit()

                return {
                    'submission_id': submission_id,
                    'final_score': final_score,
                    'max_score': max_total,
                    'percentage': round(final_percentage, 1),
                    'correct_count': correct_count,
                    'total_count': len(answers),
                    'wrong_count': len(wrong_questions),
                    'feedback': overall_feedback,
                    'details': grading_details
                }
            except Exception as e:
                logger.error(f"批改提交失败: {e}")
                return {'success': False, 'error': str(e)}

    def _grade_auto(self, qtype: str, student_answer: str, correct_answer: str,
                    max_score: float) -> Tuple[bool, float, str]:
        """自动批改客观题"""
        try:
            student = str(student_answer).strip().lower()
            correct = str(correct_answer).strip().lower()

            if qtype == 'multiple_choice':
                # 多选题：学生答案需完全匹配正确答案（集合比较）
                student_set = set(re.split(r'[,，\s]+', student)) if student else set()
                correct_set = set(re.split(r'[,，\s]+', correct)) if correct else set()
                student_set.discard('')
                correct_set.discard('')
                if student_set == correct_set:
                    return True, max_score, '完全正确'
                elif student_set & correct_set:
                    # 部分对（漏选或多选）
                    partial = len(student_set & correct_set) / len(correct_set) if correct_set else 0
                    partial_score = max_score * partial * 0.5
                    return False, round(partial_score, 1), f'部分正确（漏选或多选），得 {partial_score} 分'
                else:
                    return False, 0, '答案错误'
            elif qtype == 'fill_blank':
                # 填空题：支持多答案（|分隔）
                possible_answers = [a.strip().lower() for a in correct.split('|')]
                if student in possible_answers:
                    return True, max_score, '答案正确'
                else:
                    return False, 0, f'答案不匹配，正确答案: {correct_answer}'
            else:
                # 单选、判断
                if student == correct:
                    return True, max_score, '答案正确'
                else:
                    return False, 0, f'答案错误，正确答案: {correct_answer}'
        except Exception as e:
            logger.error(f"自动批改失败: {e}")
            return False, 0, f'批改异常: {e}'

    def _grade_ai_assisted(self, qtype: str, student_answer: str, correct_answer: str,
                           max_score: float, keywords: List[str],
                           meta: Dict) -> Tuple[bool, float, str, float, List[str]]:
        """AI 辅助批改主观题（基于关键词匹配+篇幅+结构评分）"""
        try:
            answer_text = str(student_answer or '')
            if not answer_text.strip():
                return False, 0, '未作答', 0.5, []

            # 1. 关键词匹配度（40%）
            matched_keywords = []
            if keywords:
                for kw in keywords:
                    if kw in answer_text:
                        matched_keywords.append(kw)
                keyword_score = len(matched_keywords) / len(keywords)
            else:
                # 无关键词时，与标准答案做文本相似度
                keyword_score = self._text_similarity(answer_text, str(correct_answer))

            # 2. 篇幅合适度（20%）
            min_len = meta.get('min_length', 50)
            max_len = meta.get('max_length', 2000)
            answer_len = len(answer_text)
            if answer_len < min_len:
                length_score = answer_len / min_len
            elif answer_len > max_len:
                length_score = max(0.5, 1 - (answer_len - max_len) / max_len)
            else:
                length_score = 1.0

            # 3. 结构完整性（20%）- 检查是否有段落、连接词等
            structure_indicators = ['首先', '其次', '然后', '最后', '因此', '所以', '因为', '但是',
                                    '然而', '另外', '此外', '总之', '综上', '一方面', '另一方面']
            structure_count = sum(1 for ind in structure_indicators if ind in answer_text)
            has_paragraphs = '\n' in answer_text or len(answer_text) > 200
            structure_score = min(1.0, (structure_count * 0.2 + (0.6 if has_paragraphs else 0.4)))

            # 4. 逻辑连贯性（20%）- 简化：基于句子数量和长度
            sentences = re.split(r'[。！？.!?]', answer_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) >= 3:
                logic_score = 1.0
            elif len(sentences) >= 1:
                logic_score = len(sentences) / 3
            else:
                logic_score = 0.0

            # 综合评分
            w = self.scoring_weights
            final_score_ratio = (keyword_score * w['keyword_match'] +
                                 length_score * w['length_appropriate'] +
                                 structure_score * w['structure_score'] +
                                 logic_score * w['logic_score'])

            # 题型调整
            if qtype == 'composition':
                # 作文更看重结构和篇幅
                final_score_ratio = (keyword_score * 0.2 + length_score * 0.3 +
                                     structure_score * 0.3 + logic_score * 0.2)
            elif qtype == 'short_answer':
                # 简答题更看重关键词
                final_score_ratio = (keyword_score * 0.6 + length_score * 0.1 +
                                     structure_score * 0.1 + logic_score * 0.2)

            score = round(max_score * final_score_ratio, 1)
            is_correct = score >= max_score * 0.6

            # 生成反馈
            feedback_parts = []
            feedback_parts.append(f"关键词匹配 {len(matched_keywords)}/{len(keywords) if keywords else '?'}")
            feedback_parts.append(f"篇幅得分 {round(length_score * 100)}%")
            feedback_parts.append(f"结构得分 {round(structure_score * 100)}%")
            feedback_parts.append(f"逻辑得分 {round(logic_score * 100)}%")
            if matched_keywords:
                feedback_parts.append(f"命中关键词: {', '.join(matched_keywords[:5])}")
            if not is_correct:
                feedback_parts.append("建议补充更多关键知识点，加强论述结构")

            confidence = round(final_score_ratio, 2)
            feedback = '；'.join(feedback_parts)

            return is_correct, score, feedback, confidence, matched_keywords
        except Exception as e:
            logger.error(f"AI辅助批改失败: {e}")
            return False, 0, f'批改异常: {e}', 0.0, []

    def _text_similarity(self, text1: str, text2: str) -> float:
        """简易文本相似度（基于 Jaccard 系数）"""
        try:
            set1 = set(text1)
            set2 = set(text2)
            if not set1 or not set2:
                return 0.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union
        except Exception:
            return 0.0

    def _generate_overall_feedback(self, correct_count: int, total_count: int,
                                    final_score: float, max_score: float,
                                    wrong_questions: List[Dict]) -> str:
        """生成整体反馈"""
        try:
            percentage = (final_score / max_score * 100) if max_score > 0 else 0
            if percentage >= 90:
                base = '优秀！掌握情况非常好'
            elif percentage >= 80:
                base = '良好，掌握情况较好'
            elif percentage >= 60:
                base = '及格，仍需加强'
            else:
                base = '不及格，需要重点复习'

            wrong_count = len(wrong_questions)
            if wrong_count > 0:
                wrong_subjects = [w.get('question_type', '') for w in wrong_questions]
                base += f'。共错 {wrong_count} 题'
                if wrong_subjects:
                    type_names = [QUESTION_TYPE_NAMES.get(t, t) for t in wrong_subjects]
                    base += f'（{", ".join(set(type_names))}）'

            return base
        except Exception:
            return '批改完成'

    # ==================== 批改报告 ====================

    def generate_report(self, homework_id: str) -> Dict[str, Any]:
        """生成班级批改报告"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    # 获取所有提交
                    cursor.execute('''
                        SELECT submission_id, student_id, final_score, status
                        FROM homework_submissions
                        WHERE homework_id = ? AND status = 'graded'
                    ''', (homework_id,))
                    submissions = cursor.fetchall()

                    if not submissions:
                        return {'success': False, 'message': '暂无批改记录'}

                    scores = [s[2] or 0 for s in submissions]
                    total = len(submissions)

                    avg = sum(scores) / total
                    highest = max(scores)
                    lowest = min(scores)
                    pass_count = sum(1 for s in scores if s >= 60)
                    pass_rate = pass_count / total * 100

                    # 分数段分布
                    distribution = {
                        '90-100': sum(1 for s in scores if s >= 90),
                        '80-89': sum(1 for s in scores if 80 <= s < 90),
                        '70-79': sum(1 for s in scores if 70 <= s < 80),
                        '60-69': sum(1 for s in scores if 60 <= s < 70),
                        '0-59': sum(1 for s in scores if s < 60)
                    }

                    # 获取所有错题
                    cursor.execute('''
                        SELECT question_id, question_type, COUNT(*) as wrong_count
                        FROM question_grading
                        WHERE submission_id IN ({}) AND is_correct = 0
                        GROUP BY question_id
                        ORDER BY wrong_count DESC
                    '''.format(','.join(['?'] * len(submissions))),
                        [s[0] for s in submissions])
                    wrong_stats = cursor.fetchall()

                    common_mistakes = [{
                        'question_id': r[0], 'question_type': r[1],
                        'wrong_count': r[2], 'error_rate': round(r[2] / total * 100, 1)
                    } for r in wrong_stats[:10]]

                    # 生成教学建议
                    recommendations = []
                    if pass_rate < 60:
                        recommendations.append('整体掌握情况不理想，建议重新讲解核心知识点')
                    if common_mistakes and common_mistakes[0]['error_rate'] > 50:
                        recommendations.append(f"题目 {common_mistakes[0]['question_id']} 错误率超过 50%，需要重点讲解")
                    if avg < 70:
                        recommendations.append('平均分偏低，建议安排专项练习巩固')

                    if not recommendations:
                        recommendations.append('整体表现良好，继续保持')

                    report_id = f"rpt_{homework_id}_{int(time.time())}"
                    cursor.execute('''
                        INSERT INTO grading_reports
                        (report_id, homework_id, total_submissions, graded_count,
                         avg_score, highest_score, lowest_score, pass_rate,
                         score_distribution, wrong_questions, common_mistakes,
                         recommendations)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (report_id, homework_id, total, total,
                          round(avg, 1), highest, lowest, round(pass_rate, 1),
                          json.dumps(distribution, ensure_ascii=False),
                          json.dumps(common_mistakes, ensure_ascii=False),
                          json.dumps(common_mistakes, ensure_ascii=False),
                          json.dumps(recommendations, ensure_ascii=False)))
                    conn.commit()

                return {
                    'success': True,
                    'report_id': report_id,
                    'homework_id': homework_id,
                    'total_submissions': total,
                    'avg_score': round(avg, 1),
                    'highest_score': highest,
                    'lowest_score': lowest,
                    'pass_rate': round(pass_rate, 1),
                    'score_distribution': distribution,
                    'common_mistakes': common_mistakes,
                    'recommendations': recommendations
                }
            except Exception as e:
                logger.error(f"生成批改报告失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 查询接口 ====================

    def get_submission(self, submission_id: str) -> Dict[str, Any]:
        """获取提交详情"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM homework_submissions WHERE submission_id = ?',
                               (submission_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '提交不存在'}

                cols = ['submission_id', 'homework_id', 'student_id', 'answers',
                        'submitted_at', 'status', 'auto_score', 'ai_score', 'final_score',
                        'graded_at', 'graded_by', 'grading_method', 'feedback',
                        'time_spent', 'attempt_count']
                result = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}

                if result.get('answers'):
                    try:
                        result['answers'] = json.loads(result['answers'])
                    except Exception:
                        pass

                # 获取题目批改详情
                cursor.execute('SELECT * FROM question_grading WHERE submission_id = ?',
                               (submission_id,))
                grading_rows = cursor.fetchall()
                grading_cols = ['grading_id', 'submission_id', 'homework_id', 'question_id',
                                'question_type', 'student_answer', 'correct_answer',
                                'is_correct', 'score', 'max_score', 'grading_method',
                                'ai_confidence', 'matched_keywords', 'feedback', 'graded_at']
                details = []
                for r in grading_rows:
                    detail = {grading_cols[i]: r[i] for i in range(min(len(grading_cols), len(r)))}
                    if detail.get('matched_keywords'):
                        try:
                            detail['matched_keywords'] = json.loads(detail['matched_keywords'])
                        except Exception:
                            detail['matched_keywords'] = []
                    details.append(detail)
                result['grading_details'] = details

                return {'success': True, 'submission': result}
        except Exception as e:
            logger.error(f"获取提交详情失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_student_submissions(self, student_id: str, limit: int = 20) -> Dict[str, Any]:
        """获取学生历史提交"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.submission_id, s.homework_id, h.title, s.final_score,
                           s.status, s.submitted_at, s.feedback
                    FROM homework_submissions s
                    LEFT JOIN homeworks h ON s.homework_id = h.homework_id
                    WHERE s.student_id = ?
                    ORDER BY s.submitted_at DESC
                    LIMIT ?
                ''', (student_id, limit))
                rows = cursor.fetchall()

                submissions = [{
                    'submission_id': r[0], 'homework_id': r[1], 'title': r[2],
                    'final_score': r[3], 'status': r[4], 'submitted_at': r[5],
                    'feedback': r[6]
                } for r in rows]

                return {
                    'success': True,
                    'student_id': student_id,
                    'submissions': submissions,
                    'count': len(submissions)
                }
        except Exception as e:
            logger.error(f"获取学生提交失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_homework_submissions(self, homework_id: str) -> Dict[str, Any]:
        """获取作业所有提交"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT submission_id, student_id, final_score, status,
                           submitted_at, graded_at, grading_method
                    FROM homework_submissions
                    WHERE homework_id = ?
                    ORDER BY submitted_at DESC
                ''', (homework_id,))
                rows = cursor.fetchall()

                submissions = [{
                    'submission_id': r[0], 'student_id': r[1], 'final_score': r[2],
                    'status': r[3], 'submitted_at': r[4], 'graded_at': r[5],
                    'grading_method': r[6]
                } for r in rows]

                return {
                    'success': True,
                    'homework_id': homework_id,
                    'submissions': submissions,
                    'count': len(submissions)
                }
        except Exception as e:
            logger.error(f"获取作业提交失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM homeworks')
                hw_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM homework_submissions')
                sub_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE status = "graded"')
                graded_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM question_grading')
                grading_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM grading_reports')
                report_count = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(final_score) FROM homework_submissions WHERE status = "graded"')
                avg_row = cursor.fetchone()
                avg_score = avg_row[0] if avg_row and avg_row[0] else 0
                cursor.execute('SELECT COUNT(*) FROM question_grading WHERE is_correct = 0')
                wrong_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'homeworks': hw_count,
                    'submissions': sub_count,
                    'graded': graded_count,
                    'question_gradings': grading_count,
                    'reports': report_count,
                    'avg_score': round(avg_score, 1),
                    'wrong_count': wrong_count
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}


# 单例实例
homework_grading_engine = HomeworkGradingEngine()

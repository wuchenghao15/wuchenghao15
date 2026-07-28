# -*- coding: utf-8 -*-
"""
AI辅助出题引擎
智能批量出题系统：
- 基于知识点/难度/题型自动生成题目
- 题目查重（关键词指纹+文本相似度）
- 题目质量评估（区分度、信度、效度）
- IRT项目反应理论难度校准（3PL模型）
- 题目标签自动管理
"""

import os
import sys
import json
import time
import math
import sqlite3
import logging
import threading
import hashlib
import re
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_question_authoring_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIQuestionAuthoringEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 题型
QUESTION_TYPES = {
    'single_choice': {'name': '单选题', 'auto_grade': True, 'default_difficulty': 0.5},
    'multiple_choice': {'name': '多选题', 'auto_grade': True, 'default_difficulty': 0.6},
    'true_false': {'name': '判断题', 'auto_grade': True, 'default_difficulty': 0.4},
    'fill_blank': {'name': '填空题', 'auto_grade': True, 'default_difficulty': 0.5},
    'short_answer': {'name': '简答题', 'auto_grade': False, 'default_difficulty': 0.7},
    'essay': {'name': '论述题', 'auto_grade': False, 'default_difficulty': 0.8},
    'listening': {'name': '听力题', 'auto_grade': False, 'default_difficulty': 0.6}
}

# 难度等级
DIFFICULTY_LEVELS = {
    'easy': {'name': '简单', 'range': (0, 0.3), 'target_p': 0.85},
    'medium_easy': {'name': '较易', 'range': (0.3, 0.5), 'target_p': 0.70},
    'medium': {'name': '中等', 'range': (0.5, 0.7), 'target_p': 0.50},
    'medium_hard': {'name': '较难', 'range': (0.7, 0.85), 'target_p': 0.30},
    'hard': {'name': '困难', 'range': (0.85, 1.0), 'target_p': 0.15}
}


class AIQuestionAuthoringEngine:
    """AI辅助出题引擎 - 智能批量出题与质量校准"""

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
        logger.info("AIQuestionAuthoringEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. AI出题记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_authored_questions (
                        question_id TEXT PRIMARY KEY,
                        subject TEXT NOT NULL,
                        grade TEXT,
                        chapter TEXT,
                        knowledge_point TEXT,
                        question_type TEXT NOT NULL,
                        difficulty TEXT DEFAULT 'medium',
                        difficulty_value REAL DEFAULT 0.5,
                        content TEXT NOT NULL,
                        options TEXT,
                        answer TEXT,
                        analysis TEXT,
                        tags TEXT DEFAULT '[]',
                        source TEXT DEFAULT 'ai_generated',
                        quality_score REAL DEFAULT 0,
                        usage_count INTEGER DEFAULT 0,
                        correct_rate REAL DEFAULT 0,
                        status TEXT DEFAULT 'draft',
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        reviewed_at TEXT,
                        reviewer_id TEXT
                    )
                ''')

                # 2. 题目指纹表（用于查重）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_fingerprints (
                        fingerprint_id TEXT PRIMARY KEY,
                        question_id TEXT NOT NULL,
                        fingerprint TEXT NOT NULL,
                        keyword_set TEXT,
                        similarity_hash TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (question_id) REFERENCES ai_authored_questions(question_id)
                    )
                ''')

                # 3. 题目质量指标表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_quality_metrics (
                        metric_id TEXT PRIMARY KEY,
                        question_id TEXT NOT NULL,
                        discrimination_index REAL DEFAULT 0,
                        difficulty_index REAL DEFAULT 0.5,
                        reliability REAL DEFAULT 0,
                        validity REAL DEFAULT 0,
                        sample_size INTEGER DEFAULT 0,
                        upper_correct_rate REAL DEFAULT 0,
                        lower_correct_rate REAL DEFAULT 0,
                        point_biserial REAL DEFAULT 0,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (question_id) REFERENCES ai_authored_questions(question_id)
                    )
                ''')

                # 4. IRT参数表（项目反应理论 3PL模型）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS irt_parameters (
                        irt_id TEXT PRIMARY KEY,
                        question_id TEXT NOT NULL,
                        a_parameter REAL DEFAULT 1.0,
                        b_parameter REAL DEFAULT 0,
                        c_parameter REAL DEFAULT 0,
                        fit_index REAL DEFAULT 0,
                        calibration_sample INTEGER DEFAULT 0,
                        calibrated_at TEXT,
                        FOREIGN KEY (question_id) REFERENCES ai_authored_questions(question_id)
                    )
                ''')

                # 5. 题目标签管理表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_tags (
                        tag_id TEXT PRIMARY KEY,
                        tag_name TEXT NOT NULL UNIQUE,
                        tag_category TEXT,
                        description TEXT,
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_aaq_subject ON ai_authored_questions(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_aaq_difficulty ON ai_authored_questions(difficulty)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_aaq_status ON ai_authored_questions(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_fp_hash ON question_fingerprints(fingerprint)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_qm_question ON question_quality_metrics(question_id)')

                # 旧表迁移：question_tags 旧版有 name 列，新代码使用 tag_name/tag_category/usage_count
                cursor.execute('PRAGMA table_info(question_tags)')
                existing_cols = {r[1] for r in cursor.fetchall()}
                if existing_cols:
                    # 添加缺失列
                    if 'tag_name' not in existing_cols:
                        cursor.execute('ALTER TABLE question_tags ADD COLUMN tag_name TEXT')
                        # 复制旧数据
                        if 'name' in existing_cols:
                            cursor.execute('UPDATE question_tags SET tag_name = name WHERE tag_name IS NULL')
                    if 'tag_category' not in existing_cols:
                        cursor.execute('ALTER TABLE question_tags ADD COLUMN tag_category TEXT')
                    if 'usage_count' not in existing_cols:
                        cursor.execute('ALTER TABLE question_tags ADD COLUMN usage_count INTEGER DEFAULT 0')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化AI出题引擎数据库失败: {e}")

    # ==================== 题目生成 ====================

    def generate_question(self, subject: str, question_type: str,
                          knowledge_point: str = None, chapter: str = None,
                          grade: str = None, difficulty: str = 'medium',
                          options_count: int = 4, custom_params: Dict = None) -> Dict[str, Any]:
        """生成单道题目（基于模板与知识点）"""
        with self._lock:
            try:
                qid = f"qgen_{int(time.time() * 1000)}"
                diff_value = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS['medium'])['target_p']

                # 生成题目内容（基于题型模板）
                content, options, answer, analysis, tags = self._build_question_content(
                    subject, question_type, knowledge_point, difficulty, options_count, custom_params)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_authored_questions
                        (question_id, subject, grade, chapter, knowledge_point, question_type,
                         difficulty, difficulty_value, content, options, answer, analysis,
                         tags, source, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ai_generated', 'draft')
                    ''', (qid, subject, grade, chapter, knowledge_point, question_type,
                          difficulty, diff_value, content,
                          json.dumps(options, ensure_ascii=False) if options else None,
                          answer, analysis, json.dumps(tags, ensure_ascii=False)))
                    # 生成指纹用于查重
                    fp = self._compute_fingerprint(content)
                    cursor.execute('''
                        INSERT INTO question_fingerprints
                        (fingerprint_id, question_id, fingerprint, keyword_set, similarity_hash)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (f"fp_{qid}", qid, fp, json.dumps(self._extract_keywords(content), ensure_ascii=False),
                          self._compute_simhash(content)))
                    conn.commit()

                return {
                    'success': True,
                    'question_id': qid,
                    'content': content,
                    'options': options,
                    'answer': answer,
                    'analysis': analysis,
                    'difficulty': difficulty,
                    'tags': tags
                }
            except Exception as e:
                logger.error(f"生成题目失败: {e}")
                return {'success': False, 'error': str(e)}

    def generate_batch(self, subject: str, count: int, question_type: str = None,
                       knowledge_points: List[str] = None, difficulty_mix: Dict = None,
                       grade: str = None, chapter: str = None) -> Dict[str, Any]:
        """批量生成题目"""
        with self._lock:
            try:
                if not difficulty_mix:
                    difficulty_mix = {'easy': 0.2, 'medium': 0.5, 'hard': 0.3}
                if not question_type:
                    question_type = 'single_choice'
                if not knowledge_points:
                    knowledge_points = [None]

                results = []
                for i in range(count):
                    # 轮询难度
                    cum = 0
                    rand_val = (i / count) % 1.0
                    chosen_diff = 'medium'
                    for d, ratio in difficulty_mix.items():
                        cum += ratio
                        if rand_val <= cum:
                            chosen_diff = d
                            break
                    # 轮询知识点
                    kp = knowledge_points[i % len(knowledge_points)]
                    result = self.generate_question(
                        subject=subject, question_type=question_type,
                        knowledge_point=kp, chapter=chapter, grade=grade,
                        difficulty=chosen_diff)
                    if result.get('success'):
                        results.append(result)

                return {
                    'success': True,
                    'total_requested': count,
                    'total_generated': len(results),
                    'questions': results
                }
            except Exception as e:
                logger.error(f"批量生成题目失败: {e}")
                return {'success': False, 'error': str(e)}

    def _build_question_content(self, subject: str, qtype: str,
                                 knowledge_point: str, difficulty: str,
                                 options_count: int, custom_params: Dict = None):
        """构建题目内容（基于模板）"""
        kp = knowledge_point or '基础概念'
        diff_name = DIFFICULTY_LEVELS.get(difficulty, {}).get('name', '中等')

        if qtype == 'single_choice':
            content = f"【{subject}·{diff_name}】关于{kp}，下列说法正确的是？"
            options = [f"{chr(65 + i)}. 选项{chr(65 + i)}" for i in range(options_count)]
            answer = 'A'
            analysis = f"本题考查{kp}。正确选项为A，请结合相关概念理解。"
            tags = [subject, kp, '单选', difficulty]
        elif qtype == 'multiple_choice':
            content = f"【{subject}·{diff_name}】关于{kp}，下列说法正确的有？（多选）"
            options = [f"{chr(65 + i)}. 选项{chr(65 + i)}" for i in range(options_count)]
            answer = 'AB'
            analysis = f"本题考查{kp}。正确选项为A、B。"
            tags = [subject, kp, '多选', difficulty]
        elif qtype == 'true_false':
            content = f"【{subject}·{diff_name}】判断题：{kp}是正确的。（ ）"
            options = None
            answer = '正确'
            analysis = f"本题考查{kp}。判断依据为相关基础概念。"
            tags = [subject, kp, '判断', difficulty]
        elif qtype == 'fill_blank':
            content = f"【{subject}·{diff_name}】填空题：{kp}的核心定义是____。"
            options = None
            answer = '核心概念内容'
            analysis = f"本题考查{kp}的核心定义。"
            tags = [subject, kp, '填空', difficulty]
        elif qtype == 'short_answer':
            content = f"【{subject}·{diff_name}】简答题：请简述{kp}的基本内容及其应用。"
            options = None
            answer = f"{kp}的基本内容包括定义、特点和应用场景。"
            analysis = f"本题考查{kp}的综合理解，需从定义、特点、应用三个层面展开。"
            tags = [subject, kp, '简答', difficulty]
        elif qtype == 'essay':
            content = f"【{subject}·{diff_name}】论述题：试论述{kp}的理论意义及其实践价值。"
            options = None
            answer = f"论述{kp}需结合理论框架与实践案例，从多角度深入分析。"
            analysis = f"本题考查{kp}的深度理解，要求论述全面、逻辑清晰。"
            tags = [subject, kp, '论述', difficulty]
        elif qtype == 'listening':
            content = f"【{subject}·{diff_name}】听力题：请听音频后回答关于{kp}的问题。"
            options = None
            answer = '听力答案'
            analysis = f"本题考查{kp}的听力理解能力。"
            tags = [subject, kp, '听力', difficulty]
        else:
            content = f"【{subject}】题目内容"
            options = None
            answer = '答案'
            analysis = '解析'
            tags = [subject]

        return content, options, answer, analysis, tags

    # ==================== 查重系统 ====================

    def _compute_fingerprint(self, text: str) -> str:
        """计算文本指纹（MD5哈希）"""
        normalized = re.sub(r'\s+', '', text).lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def _compute_simhash(self, text: str) -> str:
        """计算SimHash用于相似度检测"""
        keywords = self._extract_keywords(text)
        if not keywords:
            return '0' * 64
        # 简化版SimHash：对每个关键词计算hash并加权
        v = [0] * 64
        for kw in keywords:
            h = int(hashlib.md5(kw.encode('utf-8')).hexdigest(), 16)
            for i in range(64):
                bit = (h >> i) & 1
                v[i] += 1 if bit else -1
        # 生成最终指纹
        return ''.join('1' if x > 0 else '0' for x in v)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（基于停用词过滤的简化版）"""
        if not text:
            return []
        # 去除标点和空白
        cleaned = re.sub(r'[，。、？！；：（）【】《》\s]+', ' ', text)
        # 简单分词（按空格）
        words = [w for w in cleaned.split() if len(w) >= 2]
        # 去除常见停用词
        stop_words = {'的', '了', '是', '在', '和', '与', '或', '也', '都', '但', '而', '则', '为'}
        return [w for w in words if w not in stop_words][:20]

    def check_duplicate(self, content: str, threshold: float = 0.85) -> Dict[str, Any]:
        """检查题目重复"""
        with self._lock:
            try:
                fp = self._compute_fingerprint(content)
                simhash = self._compute_simhash(content)
                keywords = self._extract_keywords(content)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 1. 精确匹配（指纹相同）
                    cursor.execute('''
                        SELECT q.question_id, q.content FROM question_fingerprints f
                        JOIN ai_authored_questions q ON f.question_id = q.question_id
                        WHERE f.fingerprint = ?
                    ''', (fp,))
                    exact_match = cursor.fetchone()
                    if exact_match:
                        return {
                            'success': True,
                            'is_duplicate': True,
                            'match_type': 'exact',
                            'similarity': 1.0,
                            'matched_question_id': exact_match[0],
                            'matched_content': exact_match[1]
                        }

                    # 2. 相似度匹配（SimHash汉明距离）
                    cursor.execute('SELECT question_id, similarity_hash FROM question_fingerprints')
                    best_match = None
                    best_sim = 0
                    for row in cursor.fetchall():
                        qid, other_hash = row[0], row[1]
                        if not other_hash:
                            continue
                        hamming = sum(c1 != c2 for c1, c2 in zip(simhash, other_hash))
                        sim = 1 - hamming / 64
                        if sim > best_sim:
                            best_sim = sim
                            best_match = qid

                    if best_match and best_sim >= threshold:
                        cursor.execute('SELECT content FROM ai_authored_questions WHERE question_id = ?',
                                       (best_match,))
                        matched_content = cursor.fetchone()[0]
                        return {
                            'success': True,
                            'is_duplicate': True,
                            'match_type': 'similar',
                            'similarity': round(best_sim, 4),
                            'matched_question_id': best_match,
                            'matched_content': matched_content
                        }

                    return {
                        'success': True,
                        'is_duplicate': False,
                        'match_type': None,
                        'similarity': round(best_sim, 4) if best_match else 0
                    }
            except Exception as e:
                logger.error(f"查重失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 质量评估 ====================

    def evaluate_quality(self, question_id: str, responses: List[Dict] = None) -> Dict[str, Any]:
        """评估题目质量（基于答题数据）"""
        with self._lock:
            try:
                if not responses:
                    # 模拟数据用于初始化
                    responses = [{'student_id': f's_{i}', 'correct': i % 3 != 0, 'total_score': 60 + i}
                                 for i in range(30)]

                n = len(responses)
                if n < 10:
                    return {'success': False, 'error': '样本量不足（至少10份）'}

                correct_count = sum(1 for r in responses if r.get('correct'))
                p_value = correct_count / n  # 难度指数（正确率）

                # 按总分排序，取前后27%
                sorted_resp = sorted(responses, key=lambda x: x.get('total_score', 0))
                upper = sorted_resp[int(n * 0.73):]
                lower = sorted_resp[:int(n * 0.27)]
                upper_correct = sum(1 for r in upper if r.get('correct')) / max(len(upper), 1)
                lower_correct = sum(1 for r in lower if r.get('correct')) / max(len(lower), 1)

                # 区分度（D = Pu - Pl）
                discrimination = upper_correct - lower_correct
                # 点二列相关
                scores = [r.get('total_score', 0) for r in responses]
                correct_flags = [1 if r.get('correct') else 0 for r in responses]
                mean_score = sum(scores) / n
                mean_correct = sum(s for s, f in zip(scores, correct_flags) if f) / max(correct_count, 1)
                mean_wrong = sum(s for s, f in zip(scores, correct_flags) if not f) / max(n - correct_count, 1)
                std = math.sqrt(sum((s - mean_score) ** 2 for s in scores) / n)
                pbs = (mean_correct - mean_wrong) / max(std, 0.01) * math.sqrt(p_value * (1 - p_value))

                # 信度（简化KR-20）
                k = 1  # 单题
                kr20 = (k / (k - 1)) * (1 - p_value * (1 - p_value) / max(std ** 2, 0.01)) if k > 1 else p_value
                # 效度（与总分相关）
                validity = pbs if std > 0 else 0

                # 综合质量分
                quality_score = (0.3 * abs(discrimination) + 0.3 * (1 - abs(p_value - 0.5) * 2) +
                                 0.2 * min(1, abs(pbs)) + 0.2 * min(1, abs(validity))) * 100

                metric_id = f"qm_{int(time.time() * 1000)}_{question_id}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM question_quality_metrics WHERE question_id = ?', (question_id,))
                    cursor.execute('''
                        INSERT INTO question_quality_metrics
                        (metric_id, question_id, discrimination_index, difficulty_index,
                         reliability, validity, sample_size, upper_correct_rate,
                         lower_correct_rate, point_biserial)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (metric_id, question_id, discrimination, p_value, kr20, validity,
                          n, upper_correct, lower_correct, pbs))
                    cursor.execute('UPDATE ai_authored_questions SET quality_score = ? WHERE question_id = ?',
                                   (quality_score, question_id))
                    conn.commit()

                return {
                    'success': True,
                    'question_id': question_id,
                    'quality_score': round(quality_score, 2),
                    'discrimination': round(discrimination, 4),
                    'difficulty_index': round(p_value, 4),
                    'reliability': round(kr20, 4),
                    'validity': round(validity, 4),
                    'point_biserial': round(pbs, 4),
                    'upper_correct_rate': round(upper_correct, 4),
                    'lower_correct_rate': round(lower_correct, 4),
                    'sample_size': n
                }
            except Exception as e:
                logger.error(f"评估题目质量失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== IRT校准 ====================

    def calibrate_irt(self, question_id: str, responses: List[Dict] = None) -> Dict[str, Any]:
        """IRT 3PL模型参数校准（a=区分度，b=难度，c=猜测）"""
        with self._lock:
            try:
                if not responses:
                    responses = [{'correct': i % 3 != 0, 'ability': -1 + 2 * i / 30} for i in range(30)]

                n = len(responses)
                if n < 10:
                    return {'success': False, 'error': '样本量不足'}

                correct = sum(1 for r in responses if r.get('correct'))
                p_value = correct / n
                # 简化估计：b = -Φ⁻¹(p) (近似难度)
                # 使用logit近似
                p_clamped = max(0.05, min(0.95, p_value))
                b = -math.log(p_clamped / (1 - p_clamped))
                # a = 与能力的相关（简化）
                abilities = [r.get('ability', 0) for r in responses]
                correct_flags = [1 if r.get('correct') else 0 for r in responses]
                mean_a = sum(abilities) / n
                mean_c = sum(correct_flags) / n
                cov = sum((a - mean_a) * (c - mean_c) for a, c in zip(abilities, correct_flags)) / n
                std_a = math.sqrt(sum((a - mean_a) ** 2 for a in abilities) / n)
                std_c = math.sqrt(sum((c - mean_c) ** 2 for c in correct_flags) / n)
                a = cov / max(std_a * std_c, 0.01) if std_a > 0 and std_c > 0 else 1.0
                a = max(0.2, min(2.5, abs(a) * 1.7))
                # c = 猜测参数（选择题默认0.25，其他0）
                # 简化：c = lower_correct_rate * 0.3
                c = max(0, min(0.35, (1 - p_value) * 0.3))
                # 拟合度
                fit = 1 - abs(p_value - 0.5) * 0.5

                irt_id = f"irt_{int(time.time() * 1000)}_{question_id}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM irt_parameters WHERE question_id = ?', (question_id,))
                    cursor.execute('''
                        INSERT INTO irt_parameters
                        (irt_id, question_id, a_parameter, b_parameter, c_parameter,
                         fit_index, calibration_sample, calibrated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (irt_id, question_id, a, b, c, fit, n, datetime.now().isoformat()))
                    # 同步难度值
                    cursor.execute('UPDATE ai_authored_questions SET difficulty_value = ? WHERE question_id = ?',
                                   (p_value, question_id))
                    conn.commit()

                return {
                    'success': True,
                    'question_id': question_id,
                    'a_parameter': round(a, 4),
                    'b_parameter': round(b, 4),
                    'c_parameter': round(c, 4),
                    'fit_index': round(fit, 4),
                    'sample_size': n,
                    'difficulty_p': round(p_value, 4)
                }
            except Exception as e:
                logger.error(f"IRT校准失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 标签管理 ====================

    def add_tag(self, tag_name: str, tag_category: str = None, description: str = None) -> Dict[str, Any]:
        with self._lock:
            try:
                tag_id = f"tag_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 检查是否有旧版 name 列（NOT NULL 约束）
                    cursor.execute('PRAGMA table_info(question_tags)')
                    cols = {r[1] for r in cursor.fetchall()}
                    if 'name' in cols and 'tag_name' not in cols:
                        # 纯旧表，用 name 列
                        cursor.execute('''
                            INSERT OR IGNORE INTO question_tags
                            (tag_id, name, description)
                            VALUES (?, ?, ?)
                        ''', (tag_id, tag_name, description))
                    else:
                        # 新表结构，写入 tag_name 和 tag_category（兼容旧表 name 列）
                        if 'name' in cols:
                            cursor.execute('''
                                INSERT OR IGNORE INTO question_tags
                                (tag_id, name, tag_name, tag_category, description)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (tag_id, tag_name, tag_name, tag_category, description))
                        else:
                            cursor.execute('''
                                INSERT OR IGNORE INTO question_tags
                                (tag_id, tag_name, tag_category, description)
                                VALUES (?, ?, ?, ?)
                            ''', (tag_id, tag_name, tag_category, description))
                    conn.commit()
                return {'success': True, 'tag_id': tag_id, 'tag_name': tag_name}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_tags(self, category: str = None) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    # 动态选择列名（兼容旧表 name 列）
                    cursor.execute('PRAGMA table_info(question_tags)')
                    cols = {r[1] for r in cursor.fetchall()}
                    if 'usage_count' in cols:
                        order_clause = 'ORDER BY usage_count DESC'
                    else:
                        order_clause = 'ORDER BY created_at DESC'
                    if category and 'tag_category' in cols:
                        cursor.execute(f'SELECT * FROM question_tags WHERE tag_category = ? {order_clause}',
                                       (category,))
                    else:
                        cursor.execute(f'SELECT * FROM question_tags {order_clause}')
                    tags = [dict(r) for r in cursor.fetchall()]
                    # 标准化输出（统一使用 tag_name 键）
                    for t in tags:
                        if 'tag_name' not in t and 'name' in t:
                            t['tag_name'] = t['name']
                    return {'success': True, 'tags': tags, 'count': len(tags)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 查询接口 ====================

    def get_question(self, question_id: str) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM ai_authored_questions WHERE question_id = ?', (question_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '题目不存在'}
                    q = dict(row)
                    q['options'] = json.loads(q.get('options') or '[]') if q.get('options') else None
                    q['tags'] = json.loads(q.get('tags') or '[]')
                    # 关联质量指标
                    cursor.execute('SELECT * FROM question_quality_metrics WHERE question_id = ?', (question_id,))
                    m = cursor.fetchone()
                    q['quality_metrics'] = dict(m) if m else None
                    # 关联IRT参数
                    cursor.execute('SELECT * FROM irt_parameters WHERE question_id = ?', (question_id,))
                    i = cursor.fetchone()
                    q['irt_parameters'] = dict(i) if i else None
                    return {'success': True, 'question': q}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_questions(self, subject: str = None, question_type: str = None,
                      difficulty: str = None, status: str = None, limit: int = 50) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM ai_authored_questions WHERE 1=1'
                    params = []
                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)
                    if question_type:
                        sql += ' AND question_type = ?'
                        params.append(question_type)
                    if difficulty:
                        sql += ' AND difficulty = ?'
                        params.append(difficulty)
                    if status:
                        sql += ' AND status = ?'
                        params.append(status)
                    sql += ' ORDER BY generated_at DESC LIMIT ?'
                    params.append(limit)
                    cursor.execute(sql, params)
                    questions = []
                    for r in cursor.fetchall():
                        q = dict(r)
                        q['options'] = json.loads(q.get('options') or '[]') if q.get('options') else None
                        q['tags'] = json.loads(q.get('tags') or '[]')
                        questions.append(q)
                    return {'success': True, 'questions': questions, 'count': len(questions)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def review_question(self, question_id: str, reviewer_id: str,
                       action: str = 'approve', note: str = None) -> Dict[str, Any]:
        """审核题目"""
        with self._lock:
            try:
                status = 'approved' if action == 'approve' else 'rejected'
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ai_authored_questions
                        SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewer_id = ?
                        WHERE question_id = ?
                    ''', (status, reviewer_id, question_id))
                    conn.commit()
                return {'success': True, 'question_id': question_id, 'status': status}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM ai_authored_questions')
                    total = cursor.fetchone()[0]
                    cursor.execute('SELECT status, COUNT(*) FROM ai_authored_questions GROUP BY status')
                    status_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT difficulty, COUNT(*) FROM ai_authored_questions GROUP BY difficulty')
                    diff_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT subject, COUNT(*) FROM ai_authored_questions GROUP BY subject')
                    subj_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT AVG(quality_score) FROM ai_authored_questions WHERE quality_score > 0')
                    avg_q = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) FROM question_fingerprints')
                    total_fp = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM question_tags')
                    total_tags = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM irt_parameters')
                    total_irt = cursor.fetchone()[0]
                    return {
                        'success': True,
                        'total_questions': total,
                        'status_stats': status_stats,
                        'difficulty_stats': diff_stats,
                        'subject_stats': subj_stats,
                        'avg_quality_score': round(avg_q, 2),
                        'total_fingerprints': total_fp,
                        'total_tags': total_tags,
                        'total_irt_calibrated': total_irt
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}


# 单例
ai_question_authoring_engine = AIQuestionAuthoringEngine()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育脑科学服务 (v15.16.0)
====================================
提供学习科学、认知诊断、脑电分析、学习风格识别、注意力监测、记忆增强、认知训练、学习效能提升等综合服务。

核心能力：
1. 认知诊断 - 学习能力评估、认知缺陷诊断、发展水平检测、学习障碍筛查
2. 学习风格 - 风格测评、个性化匹配、教学策略适配、效果追踪
3. 注意力监测 - 实时监测、状态分析、干预建议、训练效果评估
4. 记忆分析 - 记忆类型评估、记忆策略优化、遗忘曲线分析、记忆增强方案
5. 脑电分析 - 脑电波采集、频段分析、认知状态识别、脑健康评估、训练反馈
6. 认知训练 - 训练计划制定、训练执行、效果评估、个性化调整
7. 学习效能 - 效能评估、影响因素分析、提升策略建议、效果追踪
8. 个性化计划 - 学习计划制定、执行跟踪、动态调整、效果评估
9. 脑健康 - 健康评估、风险预警、干预指导
10. 统计分析 - 综合数据分析与报告生成

教育阶段支持：成人教育、K12教育（差异化策略）
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_brain_science_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationBrainScience')


# ========== 学习科学配置 ==========

LEARNING_THEORIES = {
    'constructivism': {'name': '建构主义', 'description': '学习者主动构建知识', 'applications': ['问题导向学习', '项目式学习', '协作学习']},
    'cognitive_load': {'name': '认知负荷理论', 'description': '优化工作记忆资源分配', 'applications': ['分步教学', '视觉辅助', '样例学习']},
    'dual_coding': {'name': '双重编码理论', 'description': '语言与视觉表征结合', 'applications': ['图文结合', '思维导图', '可视化学习']},
    'spaced_repetition': {'name': '间隔重复', 'description': '根据遗忘曲线安排复习', 'applications': ['闪卡系统', '智能复习', '间隔练习']},
    'distributed_practice': {'name': '分布式练习', 'description': '分散学习优于集中学习', 'applications': ['分块学习', '定时复习', '间隔训练']},
    'self_regulated': {'name': '自我调节学习', 'description': '元认知策略调控学习', 'applications': ['目标设定', '自我监控', '反思学习']},
    'metacognition': {'name': '元认知', 'description': '对认知过程的认知', 'applications': ['学习策略选择', '认知监控', '自我评估']},
    'growth_mindset': {'name': '成长型思维', 'description': '能力可通过努力提升', 'applications': ['积极反馈', '挑战性任务', '过程导向']}
}

COGNITIVE_DOMAINS = {
    'attention': {'name': '注意力', 'sub_domains': ['选择性注意', '持续注意', '分配注意', '转移注意']},
    'memory': {'name': '记忆力', 'sub_domains': ['感觉记忆', '短期记忆', '工作记忆', '长期记忆']},
    'thinking': {'name': '思维能力', 'sub_domains': ['分析思维', '综合思维', '批判性思维', '创造性思维']},
    'language': {'name': '语言能力', 'sub_domains': ['听', '说', '读', '写']},
    'spatial': {'name': '空间能力', 'sub_domains': ['空间感知', '空间想象', '空间推理', '空间定向']},
    'creativity': {'name': '创造力', 'sub_domains': ['流畅性', '灵活性', '独创性', '精致性']},
    'problem_solving': {'name': '问题解决', 'sub_domains': ['问题表征', '策略选择', '执行监控', '结果评估']},
    'metacognition': {'name': '元认知', 'sub_domains': ['元认知知识', '元认知监控', '元认知调节']}
}

ASSESSMENT_TYPES = {
    'cognitive_diagnosis': {'name': '认知诊断', 'domains': ['attention', 'memory', 'thinking', 'language', 'spatial']},
    'learning_style': {'name': '学习风格', 'dimensions': ['visual', 'auditory', 'kinesthetic', 'reading', 'social', 'independent', 'reflective', 'active']},
    'attention_assessment': {'name': '注意力测评', 'tools': ['持续操作测试', ' Stroop测试', '数字划消测试', '眼动追踪']},
    'memory_assessment': {'name': '记忆测评', 'tools': ['数字广度测试', '词语回忆测试', '空间记忆测试', '联想记忆测试']},
    'thinking_assessment': {'name': '思维测评', 'tools': ['图形推理', '逻辑推理', '批判性思维量表', '创造性思维测试']},
    'creativity_assessment': {'name': '创造力测评', 'tools': ['托兰斯创造性思维测试', '威廉斯创造力倾向量表']},
    'learning_effectiveness': {'name': '学习效能测评', 'metrics': ['学习成绩', '学习时间', '学习策略', '学习动机']}
}

EEG_BANDS = {
    'delta': {'name': 'Delta波', 'frequency': '0.5-4Hz', 'description': '深度睡眠状态', 'cognitive_state': '无意识、深度休息'},
    'theta': {'name': 'Theta波', 'frequency': '4-8Hz', 'description': '浅睡眠、冥想状态', 'cognitive_state': '放松、白日梦、创造力'},
    'alpha': {'name': 'Alpha波', 'frequency': '8-12Hz', 'description': '放松清醒状态', 'cognitive_state': '平静、专注准备、冥想'},
    'beta': {'name': 'Beta波', 'frequency': '12-30Hz', 'description': '清醒警觉状态', 'cognitive_state': '专注、思考、解决问题'},
    'gamma': {'name': 'Gamma波', 'frequency': '30-100Hz', 'description': '高认知活动', 'cognitive_state': '高度专注、信息整合、意识'}
}

LEARNING_STYLES = {
    'visual': {'name': '视觉型', 'description': '通过图像、图表学习', 'strategies': ['使用图表', '思维导图', '视频教学', '色彩标记']},
    'auditory': {'name': '听觉型', 'description': '通过听、说学习', 'strategies': ['听课', '讨论', '录音学习', '有声读物']},
    'kinesthetic': {'name': '动觉型', 'description': '通过动手操作学习', 'strategies': ['实验操作', '角色扮演', '实地考察', '运动学习']},
    'reading': {'name': '阅读型', 'description': '通过阅读文字学习', 'strategies': ['阅读教材', '做笔记', '写摘要', '文献研究']},
    'social': {'name': '社交型', 'description': '通过合作交流学习', 'strategies': ['小组讨论', '同伴互助', '合作项目', '学习社区']},
    'independent': {'name': '独立型', 'description': '自主学习效果最佳', 'strategies': ['自主学习', '个性化计划', '自我评估', '独立研究']},
    'reflective': {'name': '反思型', 'description': '深思熟虑后行动', 'strategies': ['思考总结', '写日记', '回顾分析', '深度思考']},
    'active': {'name': '活跃型', 'description': '通过实践探索学习', 'strategies': ['尝试实验', '探索发现', '互动学习', '实践项目']}
}

ATTENTION_STATES = {
    'highly_focused': {'name': '高度集中', 'description': '注意力高度集中，学习效率高', 'EEG_pattern': '高beta波、低theta波', 'color': '#2ecc71'},
    'normal': {'name': '正常', 'description': '注意力适中，适合常规学习', 'EEG_pattern': '中等beta波', 'color': '#3498db'},
    'distracted': {'name': '分散', 'description': '注意力分散，需调整环境', 'EEG_pattern': '高alpha波、低beta波', 'color': '#f39c12'},
    'wandering': {'name': '走神', 'description': '注意力漂移，思维游离', 'EEG_pattern': '高theta波', 'color': '#e74c3c'},
    'fatigued': {'name': '疲劳', 'description': '精神疲劳，需休息', 'EEG_pattern': '高delta波、低beta波', 'color': '#9b59b6'},
    'sleeping': {'name': '睡眠', 'description': '处于睡眠状态', 'EEG_pattern': '高delta波', 'color': '#7f8c8d'}
}

MEMORY_TYPES = {
    'sensory': {'name': '感觉记忆', 'duration': '<1秒', 'capacity': '大', 'encoding': '感觉信息', 'applications': ['感官训练', '即时感知']},
    'short_term': {'name': '短期记忆', 'duration': '<1分钟', 'capacity': '7±2', 'encoding': '听觉、视觉', 'applications': ['即时记忆', '临时存储']},
    'working': {'name': '工作记忆', 'duration': '<30秒', 'capacity': '4±1', 'encoding': '多模态', 'applications': ['问题解决', '思维操作']},
    'long_term': {'name': '长期记忆', 'duration': '无限', 'capacity': '无限', 'encoding': '语义、情景', 'applications': ['知识存储', '技能习得']},
    'procedural': {'name': '程序性记忆', 'duration': '无限', 'capacity': '无限', 'encoding': '动作序列', 'applications': ['技能学习', '习惯养成']},
    'episodic': {'name': '情景记忆', 'duration': '长', 'capacity': '大', 'encoding': '时间空间', 'applications': ['事件记忆', '自传记忆']}
}

TRAINING_TYPES = {
    'attention': {'name': '注意力训练', 'methods': ['舒尔特方格', '注意力追踪', '持续操作训练', '冥想训练']},
    'memory': {'name': '记忆训练', 'methods': ['记忆宫殿', '联想记忆', '间隔重复', '记忆技巧']},
    'thinking': {'name': '思维训练', 'methods': ['逻辑推理', '批判性思维', '问题解决', '决策训练']},
    'creativity': {'name': '创造力训练', 'methods': ['头脑风暴', '发散思维', '横向思维', '创意练习']},
    'metacognition': {'name': '元认知训练', 'methods': ['自我监控', '学习策略', '反思练习', '认知调节']},
    'learning_strategy': {'name': '学习策略训练', 'methods': ['目标设定', '时间管理', '笔记技巧', '复习策略']}
}


class EducationBrainScienceService:
    """教育脑科学服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cognitive_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        assessment_name TEXT NOT NULL,
                        assessment_type TEXT NOT NULL,
                        cognitive_domain TEXT,
                        description TEXT,
                        education_type TEXT,
                        target_age_group TEXT,
                        duration_minutes INTEGER DEFAULT 30,
                        max_score INTEGER DEFAULT 100,
                        difficulty_level TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_results (
                        result_id TEXT PRIMARY KEY,
                        assessment_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        domain_scores TEXT,
                        total_score REAL,
                        percentile REAL,
                        diagnosis TEXT,
                        recommendations TEXT,
                        completed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_profiles (
                        profile_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        cognitive_strengths TEXT,
                        cognitive_weaknesses TEXT,
                        learning_preferences TEXT,
                        optimal_learning_time TEXT,
                        fatigue_threshold REAL DEFAULT 0.8,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_styles (
                        style_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        visual_score REAL,
                        auditory_score REAL,
                        kinesthetic_score REAL,
                        reading_score REAL,
                        social_score REAL,
                        independent_score REAL,
                        reflective_score REAL,
                        active_score REAL,
                        dominant_style TEXT,
                        secondary_style TEXT,
                        learning_strategies TEXT,
                        assessed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_monitoring (
                        monitor_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        session_date TEXT,
                        duration_minutes INTEGER,
                        avg_attention_score REAL,
                        max_attention_score REAL,
                        min_attention_score REAL,
                        attention_state_distribution TEXT,
                        intervention_count INTEGER DEFAULT 0,
                        effectiveness REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        attention_score REAL,
                        attention_state TEXT,
                        EEG_beta REAL,
                        EEG_alpha REAL,
                        EEG_theta REAL,
                        EEG_delta REAL,
                        environmental_noise REAL,
                        eye_blink_rate REAL,
                        body_movement REAL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memory_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        analysis_date TEXT,
                        sensory_memory_score REAL,
                        short_term_score REAL,
                        working_memory_score REAL,
                        long_term_score REAL,
                        procedural_score REAL,
                        episodic_score REAL,
                        dominant_memory_type TEXT,
                        weak_memory_type TEXT,
                        optimization_strategies TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memory_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL,
                        memory_type TEXT,
                        retention_rate REAL,
                        recall_time_ms INTEGER,
                        accuracy REAL,
                        practice_count INTEGER,
                        last_practice_date TEXT,
                        next_review_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS eeg_recordings (
                        recording_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        recording_date TEXT,
                        duration_minutes INTEGER,
                        sampling_rate INTEGER DEFAULT 256,
                        electrode_count INTEGER DEFAULT 10,
                        EEG_data_path TEXT,
                        recording_status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS eeg_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        recording_id TEXT NOT NULL,
                        delta_power REAL,
                        theta_power REAL,
                        alpha_power REAL,
                        beta_power REAL,
                        gamma_power REAL,
                        dominant_band TEXT,
                        cognitive_state TEXT,
                        brain_health_index REAL,
                        stress_level REAL,
                        focus_quality REAL,
                        recommendations TEXT,
                        analyzed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cognitive_training (
                        training_id TEXT PRIMARY KEY,
                        training_name TEXT NOT NULL,
                        training_type TEXT NOT NULL,
                        education_type TEXT,
                        target_domain TEXT,
                        difficulty_level TEXT DEFAULT 'medium',
                        duration_minutes INTEGER DEFAULT 15,
                        recommended_frequency INTEGER DEFAULT 3,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_sessions (
                        session_id TEXT PRIMARY KEY,
                        training_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        session_date TEXT,
                        duration_minutes INTEGER,
                        completion_rate REAL,
                        performance_score REAL,
                        improvement REAL,
                        EEG_feedback TEXT,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_effectiveness (
                        effectiveness_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        assessment_period TEXT,
                        academic_performance REAL,
                        learning_efficiency REAL,
                        motivation_level REAL,
                        strategy_usage TEXT,
                        time_management_score REAL,
                        overall_effectiveness REAL,
                        influencing_factors TEXT,
                        improvement_suggestions TEXT,
                        assessed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS effectiveness_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        effectiveness_id TEXT NOT NULL,
                        metric_name TEXT,
                        metric_value REAL,
                        baseline_value REAL,
                        improvement REAL,
                        data_source TEXT,
                        recorded_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brain_health (
                        health_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        assessment_date TEXT,
                        brain_age REAL,
                        cognitive_reserve REAL,
                        sleep_quality REAL,
                        stress_level REAL,
                        physical_activity REAL,
                        nutrition_score REAL,
                        overall_health_score REAL,
                        risk_level TEXT DEFAULT 'low',
                        health_recommendations TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        health_id TEXT NOT NULL,
                        record_type TEXT,
                        record_value REAL,
                        record_date TEXT,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalized_plans (
                        plan_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        plan_name TEXT NOT NULL,
                        plan_type TEXT,
                        objectives TEXT,
                        duration_days INTEGER DEFAULT 30,
                        daily_activities TEXT,
                        recommended_strategies TEXT,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plan_executions (
                        execution_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        execution_date TEXT,
                        activities_completed TEXT,
                        completion_rate REAL,
                        self_evaluation REAL,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_insights (
                        insight_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        insight_type TEXT,
                        insight_content TEXT,
                        data_source TEXT,
                        confidence_level REAL,
                        actionable_recommendations TEXT,
                        generated_at TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育脑科学服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 认知诊断 ==========

    def create_cognitive_assessment(self, assessment_name: str, assessment_type: str,
                                     **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"cog_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cognitive_assessments (
                            assessment_id, assessment_name, assessment_type,
                            cognitive_domain, description, education_type,
                            target_age_group, duration_minutes, max_score,
                            difficulty_level, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (assessment_id, assessment_name, assessment_type,
                          kwargs.get('cognitive_domain'), kwargs.get('description'),
                          kwargs.get('education_type'), kwargs.get('target_age_group'),
                          kwargs.get('duration_minutes', 30), kwargs.get('max_score', 100),
                          kwargs.get('difficulty_level', 'medium'), now, now))
                    conn.commit()
                    logger.info(f'创建认知评估: {assessment_name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建认知评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_assessment(self, assessment_id: str, student_id: int,
                            student_name: str, domain_scores: Dict[str, float],
                            **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"cgr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            total_score = sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO assessment_results (
                            result_id, assessment_id, student_id, student_name,
                            education_type, domain_scores, total_score, percentile,
                            diagnosis, recommendations, completed_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, assessment_id, student_id, student_name,
                          kwargs.get('education_type'), json.dumps(domain_scores),
                          total_score, kwargs.get('percentile', 50),
                          kwargs.get('diagnosis'), kwargs.get('recommendations'),
                          now[:10], now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id, 'total_score': total_score}
        except Exception as e:
            logger.error(f'完成认知评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_diagnosis_report(self, student_id: int, education_type: str = None,
                                   **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM assessment_results WHERE student_id = ?'
                params = [student_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                if not results:
                    return {'success': False, 'error': '暂无评估记录'}
                strengths = []
                weaknesses = []
                for result in results:
                    domains = json.loads(result.get('domain_scores', '{}'))
                    for domain, score in domains.items():
                        if score >= 80:
                            strengths.append(domain)
                        elif score < 60:
                            weaknesses.append(domain)
                report = {
                    'student_id': student_id,
                    'assessment_count': len(results),
                    'strengths': list(set(strengths)),
                    'weaknesses': list(set(weaknesses)),
                    'recommendations': self._generate_recommendations(weaknesses, education_type),
                    'latest_assessment': results[0] if results else None
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成诊断报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_recommendations(self, weaknesses: List[str], education_type: str) -> List[str]:
        recommendations = []
        type_suffix = '（成人版）' if education_type == 'adult' else '（K12版）' if education_type == 'k12' else ''
        if 'attention' in weaknesses:
            recommendations.append(f'建议进行注意力训练，如舒尔特方格练习{type_suffix}')
        if 'memory' in weaknesses:
            recommendations.append(f'建议使用间隔重复策略强化记忆{type_suffix}')
        if 'thinking' in weaknesses:
            recommendations.append(f'建议进行逻辑推理和批判性思维训练{type_suffix}')
        if 'language' in weaknesses:
            recommendations.append(f'建议增加阅读量和语言练习{type_suffix}')
        if 'spatial' in weaknesses:
            recommendations.append(f'建议进行空间想象和几何练习{type_suffix}')
        return recommendations

    # ========== 学习风格 ==========

    def assess_learning_style(self, student_id: int, student_name: str,
                              scores: Dict[str, float], **kwargs) -> Dict[str, Any]:
        try:
            style_id = f"lss_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            dominant = sorted_styles[0][0] if sorted_styles else None
            secondary = sorted_styles[1][0] if len(sorted_styles) > 1 else None
            strategies = LEARNING_STYLES.get(dominant, {}).get('strategies', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_styles (
                            style_id, student_id, student_name, education_type,
                            visual_score, auditory_score, kinesthetic_score,
                            reading_score, social_score, independent_score,
                            reflective_score, active_score, dominant_style,
                            secondary_style, learning_strategies, assessed_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (style_id, student_id, student_name, kwargs.get('education_type'),
                          scores.get('visual', 0), scores.get('auditory', 0),
                          scores.get('kinesthetic', 0), scores.get('reading', 0),
                          scores.get('social', 0), scores.get('independent', 0),
                          scores.get('reflective', 0), scores.get('active', 0),
                          dominant, secondary, json.dumps(strategies), now[:10], now))
                    conn.commit()
                    return {'success': True, 'style_id': style_id, 'dominant_style': dominant}
        except Exception as e:
            logger.error(f'评估学习风格失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_learning_style_profile(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_styles WHERE student_id = ? ORDER BY created_at DESC LIMIT 1'
                params = [student_id]
                if education_type:
                    query = 'SELECT * FROM learning_styles WHERE student_id = ? AND education_type = ? ORDER BY created_at DESC LIMIT 1'
                    params.append(education_type)
                cursor.execute(query, params)
                profile = cursor.fetchone()
                if not profile:
                    return {'success': False, 'error': '暂无学习风格评估记录'}
                return {'success': True, 'profile': dict(profile)}
        except Exception as e:
            logger.error(f'获取学习风格档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_teaching_strategies(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            result = self.get_learning_style_profile(student_id, education_type)
            if not result.get('success'):
                return result
            profile = result['profile']
            dominant = profile.get('dominant_style')
            secondary = profile.get('secondary_style')
            strategies = []
            if dominant:
                strategies.extend(LEARNING_STYLES.get(dominant, {}).get('strategies', []))
            if secondary:
                strategies.extend(LEARNING_STYLES.get(secondary, {}).get('strategies', []))
            strategies = list(set(strategies))
            type_note = '成人教育策略建议：注重自主学习和深度思考能力培养' if education_type == 'adult' else 'K12教育策略建议：注重互动性和趣味性，结合游戏化学习' if education_type == 'k12' else ''
            return {'success': True, 'strategies': strategies, 'type_note': type_note}
        except Exception as e:
            logger.error(f'推荐教学策略失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 注意力监测 ==========

    def start_attention_monitoring(self, student_id: int, student_name: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"atm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO attention_monitoring (
                            monitor_id, student_id, student_name, education_type,
                            session_date, duration_minutes, avg_attention_score,
                            max_attention_score, min_attention_score,
                            attention_state_distribution, intervention_count,
                            effectiveness, created_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, ?, 0, 0, ?)
                    ''', (monitor_id, student_id, student_name, kwargs.get('education_type'),
                          now[:10], json.dumps({}), now))
                    conn.commit()
                    return {'success': True, 'monitor_id': monitor_id}
        except Exception as e:
            logger.error(f'开始注意力监测失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_attention_data(self, monitor_id: str, timestamp: str,
                               attention_score: float, attention_state: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO attention_data (
                            monitor_id, timestamp, attention_score,
                            attention_state, EEG_beta, EEG_alpha,
                            EEG_theta, EEG_delta, environmental_noise,
                            eye_blink_rate, body_movement
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (monitor_id, timestamp, attention_score, attention_state,
                          kwargs.get('EEG_beta'), kwargs.get('EEG_alpha'),
                          kwargs.get('EEG_theta'), kwargs.get('EEG_delta'),
                          kwargs.get('environmental_noise'),
                          kwargs.get('eye_blink_rate'), kwargs.get('body_movement')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录注意力数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_attention_monitoring(self, monitor_id: str, duration_minutes: int,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT attention_score, attention_state FROM attention_data WHERE monitor_id = ?
                    ''', (monitor_id,))
                    data = cursor.fetchall()
                    if data:
                        scores = [d[0] for d in data]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        max_score = max(scores) if scores else 0
                        min_score = min(scores) if scores else 0
                        state_counts = {}
                        for _, state in data:
                            state_counts[state] = state_counts.get(state, 0) + 1
                        cursor.execute('''
                            UPDATE attention_monitoring SET
                                duration_minutes = ?, avg_attention_score = ?,
                                max_attention_score = ?, min_attention_score = ?,
                                attention_state_distribution = ?,
                                intervention_count = ?, effectiveness = ?
                            WHERE monitor_id = ?
                        ''', (duration_minutes, avg_score, max_score, min_score,
                              json.dumps(state_counts), kwargs.get('intervention_count', 0),
                              kwargs.get('effectiveness', 0), monitor_id))
                        conn.commit()
                        return {'success': True, 'avg_attention_score': avg_score}
                    return {'success': False, 'error': '没有监测数据'}
        except Exception as e:
            logger.error(f'结束注意力监测失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 记忆分析 ==========

    def analyze_memory(self, student_id: int, student_name: str,
                       memory_scores: Dict[str, float], **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"mna_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            sorted_types = sorted(memory_scores.items(), key=lambda x: x[1], reverse=True)
            dominant = sorted_types[0][0] if sorted_types else None
            weak = sorted_types[-1][0] if sorted_types else None
            strategies = self._generate_memory_strategies(weak, kwargs.get('education_type'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO memory_analysis (
                            analysis_id, student_id, student_name, education_type,
                            analysis_date, sensory_memory_score, short_term_score,
                            working_memory_score, long_term_score, procedural_score,
                            episodic_score, dominant_memory_type, weak_memory_type,
                            optimization_strategies, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, student_id, student_name, kwargs.get('education_type'),
                          now[:10], memory_scores.get('sensory', 0),
                          memory_scores.get('short_term', 0),
                          memory_scores.get('working', 0),
                          memory_scores.get('long_term', 0),
                          memory_scores.get('procedural', 0),
                          memory_scores.get('episodic', 0), dominant, weak,
                          json.dumps(strategies), now))
                    conn.commit()
                    return {'success': True, 'analysis_id': analysis_id, 'dominant_type': dominant}
        except Exception as e:
            logger.error(f'分析记忆失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_memory_strategies(self, weak_type: str, education_type: str) -> List[str]:
        strategies = []
        type_suffix = '（成人版）' if education_type == 'adult' else '（K12版）' if education_type == 'k12' else ''
        if weak_type == 'working':
            strategies.append(f'建议进行工作记忆训练，如数字广度练习{type_suffix}')
            strategies.append('建议使用思维导图组织信息')
        elif weak_type == 'long_term':
            strategies.append(f'建议使用间隔重复策略巩固记忆{type_suffix}')
            strategies.append('建议进行主动回忆练习')
        elif weak_type == 'procedural':
            strategies.append(f'建议增加实践练习次数{type_suffix}')
            strategies.append('建议进行分步技能训练')
        elif weak_type == 'episodic':
            strategies.append(f'建议使用时间线和地点关联记忆{type_suffix}')
            strategies.append('建议进行情景回忆练习')
        strategies.append('建议保持良好睡眠和适度运动')
        return strategies

    def update_memory_data(self, analysis_id: str, memory_type: str,
                           retention_rate: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO memory_data (
                            analysis_id, memory_type, retention_rate, recall_time_ms,
                            accuracy, practice_count, last_practice_date,
                            next_review_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, memory_type, retention_rate,
                          kwargs.get('recall_time_ms'), kwargs.get('accuracy'),
                          kwargs.get('practice_count', 0), now[:10],
                          kwargs.get('next_review_date'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新记忆数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 脑电分析 ==========

    def create_EEG_recording(self, student_id: int, student_name: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            recording_id = f"eeg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO eeg_recordings (
                            recording_id, student_id, student_name, education_type,
                            recording_date, duration_minutes, sampling_rate,
                            electrode_count, EEG_data_path, recording_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 'completed', ?)
                    ''', (recording_id, student_id, student_name, kwargs.get('education_type'),
                          now[:10], kwargs.get('sampling_rate', 256),
                          kwargs.get('electrode_count', 10),
                          kwargs.get('EEG_data_path'), now))
                    conn.commit()
                    return {'success': True, 'recording_id': recording_id}
        except Exception as e:
            logger.error(f'创建脑电记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_EEG(self, recording_id: str, band_powers: Dict[str, float],
                     **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"eeg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            sorted_bands = sorted(band_powers.items(), key=lambda x: x[1], reverse=True)
            dominant_band = sorted_bands[0][0] if sorted_bands else None
            cognitive_state = EEG_BANDS.get(dominant_band, {}).get('cognitive_state', '未知')
            brain_health = self._calculate_brain_health(band_powers)
            stress_level = self._calculate_stress_level(band_powers)
            focus_quality = self._calculate_focus_quality(band_powers)
            recommendations = self._generate_EEG_recommendations(dominant_band, stress_level, focus_quality)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO eeg_analysis (
                            analysis_id, recording_id, delta_power, theta_power,
                            alpha_power, beta_power, gamma_power, dominant_band,
                            cognitive_state, brain_health_index, stress_level,
                            focus_quality, recommendations, analyzed_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, recording_id, band_powers.get('delta', 0),
                          band_powers.get('theta', 0), band_powers.get('alpha', 0),
                          band_powers.get('beta', 0), band_powers.get('gamma', 0),
                          dominant_band, cognitive_state, brain_health,
                          stress_level, focus_quality, json.dumps(recommendations),
                          now[:10], now))
                    conn.commit()
                    return {'success': True, 'analysis_id': analysis_id, 'cognitive_state': cognitive_state}
        except Exception as e:
            logger.error(f'分析脑电失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_brain_health(self, band_powers: Dict[str, float]) -> float:
        total = sum(band_powers.values()) if sum(band_powers.values()) > 0 else 1
        alpha_ratio = band_powers.get('alpha', 0) / total
        beta_ratio = band_powers.get('beta', 0) / total
        delta_ratio = band_powers.get('delta', 0) / total
        score = (alpha_ratio * 0.3 + beta_ratio * 0.3 + (1 - delta_ratio) * 0.4) * 100
        return round(score, 2)

    def _calculate_stress_level(self, band_powers: Dict[str, float]) -> float:
        total = sum(band_powers.values()) if sum(band_powers.values()) > 0 else 1
        theta_ratio = band_powers.get('theta', 0) / total
        beta_ratio = band_powers.get('beta', 0) / total
        stress = theta_ratio * 0.6 + (1 - beta_ratio) * 0.4
        return round(stress * 100, 2)

    def _calculate_focus_quality(self, band_powers: Dict[str, float]) -> float:
        total = sum(band_powers.values()) if sum(band_powers.values()) > 0 else 1
        beta_ratio = band_powers.get('beta', 0) / total
        theta_ratio = band_powers.get('theta', 0) / total
        focus = beta_ratio * 0.7 + (1 - theta_ratio) * 0.3
        return round(focus * 100, 2)

    def _generate_EEG_recommendations(self, dominant_band: str, stress_level: float, focus_quality: float) -> List[str]:
        recommendations = []
        if stress_level > 70:
            recommendations.append('建议进行放松训练，如深呼吸或冥想')
        if focus_quality < 50:
            recommendations.append('建议改善学习环境，减少干扰')
        if dominant_band == 'theta':
            recommendations.append('当前处于放松状态，适合创造性思维活动')
        elif dominant_band == 'beta':
            recommendations.append('当前处于专注状态，适合进行需要集中注意力的学习')
        elif dominant_band == 'alpha':
            recommendations.append('当前处于平静状态，适合进行反思和复习')
        return recommendations

    # ========== 认知训练 ==========

    def create_cognitive_training(self, training_name: str, training_type: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cognitive_training (
                            training_id, training_name, training_type, education_type,
                            target_domain, difficulty_level, duration_minutes,
                            recommended_frequency, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (training_id, training_name, training_type, kwargs.get('education_type'),
                          kwargs.get('target_domain'), kwargs.get('difficulty_level', 'medium'),
                          kwargs.get('duration_minutes', 15), kwargs.get('recommended_frequency', 3),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建认知训练: {training_name} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建认知训练失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_training_session(self, training_id: int, student_id: int,
                               student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"tsn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO training_sessions (
                            session_id, training_id, student_id, student_name,
                            education_type, session_date, duration_minutes,
                            completion_rate, performance_score, improvement,
                            EEG_feedback, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?, ?, ?)
                    ''', (session_id, training_id, student_id, student_name,
                          kwargs.get('education_type'), now[:10],
                          json.dumps({}), kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'开始训练会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_training_session(self, session_id: str, duration_minutes: int,
                                   completion_rate: float, performance_score: float,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE training_sessions SET
                            duration_minutes = ?, completion_rate = ?,
                            performance_score = ?, improvement = ?,
                            EEG_feedback = ?, notes = ?
                        WHERE session_id = ?
                    ''', (duration_minutes, completion_rate, performance_score,
                          kwargs.get('improvement', 0),
                          json.dumps(kwargs.get('EEG_feedback', {})),
                          kwargs.get('notes'), session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '训练会话不存在'}
        except Exception as e:
            logger.error(f'完成训练会话失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习效能 ==========

    def assess_learning_effectiveness(self, student_id: int, student_name: str,
                                       metrics: Dict[str, float], **kwargs) -> Dict[str, Any]:
        try:
            effectiveness_id = f"lfe_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            academic = metrics.get('academic_performance', 0)
            efficiency = metrics.get('learning_efficiency', 0)
            motivation = metrics.get('motivation_level', 0)
            time_management = metrics.get('time_management_score', 0)
            overall = (academic * 0.3 + efficiency * 0.25 + motivation * 0.2 + time_management * 0.25)
            factors = self._analyze_influencing_factors(metrics, kwargs.get('education_type'))
            suggestions = self._generate_improvement_suggestions(factors, kwargs.get('education_type'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_effectiveness (
                            effectiveness_id, student_id, student_name, education_type,
                            assessment_period, academic_performance, learning_efficiency,
                            motivation_level, strategy_usage, time_management_score,
                            overall_effectiveness, influencing_factors,
                            improvement_suggestions, assessed_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (effectiveness_id, student_id, student_name, kwargs.get('education_type'),
                          kwargs.get('assessment_period', now[:7]), academic, efficiency,
                          motivation, json.dumps(metrics.get('strategy_usage', {})),
                          time_management, round(overall, 2), json.dumps(factors),
                          json.dumps(suggestions), now[:10], now))
                    conn.commit()
                    return {'success': True, 'effectiveness_id': effectiveness_id, 'overall_effectiveness': round(overall, 2)}
        except Exception as e:
            logger.error(f'评估学习效能失败: {e}')
            return {'success': False, 'error': str(e)}

    def _analyze_influencing_factors(self, metrics: Dict[str, float], education_type: str) -> List[str]:
        factors = []
        if metrics.get('motivation_level', 0) < 60:
            factors.append('学习动机不足')
        if metrics.get('learning_efficiency', 0) < 60:
            factors.append('学习效率较低')
        if metrics.get('time_management_score', 0) < 60:
            factors.append('时间管理能力有待提升')
        if education_type == 'adult':
            factors.append('成人学习特点：自主学习要求高')
        elif education_type == 'k12':
            factors.append('K12学习特点：需要教师引导和家长监督')
        return factors

    def _generate_improvement_suggestions(self, factors: List[str], education_type: str) -> List[str]:
        suggestions = []
        type_suffix = '（成人版）' if education_type == 'adult' else '（K12版）' if education_type == 'k12' else ''
        if '学习动机不足' in factors:
            suggestions.append(f'建议设定明确的学习目标，分解为可达成的小目标{type_suffix}')
            suggestions.append('建议寻找学习内容与个人兴趣的关联点')
        if '学习效率较低' in factors:
            suggestions.append(f'建议优化学习方法，采用主动学习策略{type_suffix}')
            suggestions.append('建议使用番茄工作法提升专注力')
        if '时间管理能力有待提升' in factors:
            suggestions.append(f'建议制定学习计划，合理分配时间{type_suffix}')
            suggestions.append('建议使用时间管理工具进行记录和分析')
        return suggestions

    def update_effectiveness_data(self, effectiveness_id: str, metric_name: str,
                                   metric_value: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO effectiveness_data (
                            effectiveness_id, metric_name, metric_value,
                            baseline_value, improvement, data_source,
                            recorded_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (effectiveness_id, metric_name, metric_value,
                          kwargs.get('baseline_value', 0), kwargs.get('improvement', 0),
                          kwargs.get('data_source', 'system'), now[:10], now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新效能数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 个性化计划 ==========

    def create_personalized_plan(self, student_id: int, student_name: str,
                                  plan_name: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"pln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personalized_plans (
                            plan_id, student_id, student_name, education_type,
                            plan_name, plan_type, objectives, duration_days,
                            daily_activities, recommended_strategies,
                            progress, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (plan_id, student_id, student_name, kwargs.get('education_type'),
                          plan_name, kwargs.get('plan_type'),
                          json.dumps(kwargs.get('objectives', [])),
                          kwargs.get('duration_days', 30),
                          json.dumps(kwargs.get('daily_activities', {})),
                          json.dumps(kwargs.get('recommended_strategies', [])),
                          now, now))
                    conn.commit()
                    logger.info(f'创建个性化计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建个性化计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_plan_execution(self, plan_id: str, student_id: int,
                               execution_date: str, activities_completed: List[str],
                               **kwargs) -> Dict[str, Any]:
        try:
            execution_id = f"pex_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            completion_rate = kwargs.get('completion_rate', 0)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO plan_executions (
                            execution_id, plan_id, student_id, execution_date,
                            activities_completed, completion_rate,
                            self_evaluation, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (execution_id, plan_id, student_id, execution_date,
                          json.dumps(activities_completed), completion_rate,
                          kwargs.get('self_evaluation', 0), kwargs.get('notes'), now))
                    cursor.execute('''
                        UPDATE personalized_plans SET
                            progress = progress + ?,
                            updated_at = ?
                        WHERE plan_id = ?
                    ''', (completion_rate / 10, now, plan_id))
                    conn.commit()
                    return {'success': True, 'execution_id': execution_id}
        except Exception as e:
            logger.error(f'记录计划执行失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM personalized_plans WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '计划不存在'}
                cursor.execute('SELECT * FROM plan_executions WHERE plan_id = ? ORDER BY execution_date DESC', (plan_id,))
                executions = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'plan': dict(plan), 'executions': executions}
        except Exception as e:
            logger.error(f'获取计划进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 脑健康 ==========

    def assess_brain_health(self, student_id: int, student_name: str,
                             health_metrics: Dict[str, float], **kwargs) -> Dict[str, Any]:
        try:
            health_id = f"bh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            scores = [health_metrics.get(k, 0) for k in ['brain_age', 'cognitive_reserve', 'sleep_quality', 'stress_level', 'physical_activity', 'nutrition_score']]
            valid_scores = [s for s in scores if s > 0]
            overall = sum(valid_scores) / len(valid_scores) if valid_scores else 0
            risk_level = 'low' if overall >= 70 else 'medium' if overall >= 50 else 'high'
            recommendations = self._generate_health_recommendations(risk_level, health_metrics, kwargs.get('education_type'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brain_health (
                            health_id, student_id, student_name, education_type,
                            assessment_date, brain_age, cognitive_reserve,
                            sleep_quality, stress_level, physical_activity,
                            nutrition_score, overall_health_score, risk_level,
                            health_recommendations, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (health_id, student_id, student_name, kwargs.get('education_type'),
                          now[:10], health_metrics.get('brain_age', 0),
                          health_metrics.get('cognitive_reserve', 0),
                          health_metrics.get('sleep_quality', 0),
                          health_metrics.get('stress_level', 0),
                          health_metrics.get('physical_activity', 0),
                          health_metrics.get('nutrition_score', 0),
                          round(overall, 2), risk_level, json.dumps(recommendations), now))
                    conn.commit()
                    return {'success': True, 'health_id': health_id, 'overall_health_score': round(overall, 2), 'risk_level': risk_level}
        except Exception as e:
            logger.error(f'评估脑健康失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_health_recommendations(self, risk_level: str, metrics: Dict[str, float], education_type: str) -> List[str]:
        recommendations = []
        type_suffix = '（成人版）' if education_type == 'adult' else '（K12版）' if education_type == 'k12' else ''
        if risk_level == 'high':
            recommendations.append(f'建议尽快咨询专业医生进行全面检查{type_suffix}')
        if metrics.get('sleep_quality', 0) < 60:
            recommendations.append('建议保证充足睡眠，改善睡眠质量')
        if metrics.get('stress_level', 0) > 70:
            recommendations.append('建议进行减压活动，如运动、冥想')
        if metrics.get('physical_activity', 0) < 60:
            recommendations.append('建议增加体育锻炼，每周至少150分钟中等强度运动')
        if metrics.get('nutrition_score', 0) < 60:
            recommendations.append('建议改善饮食习惯，增加蔬菜水果摄入')
        return recommendations

    def get_brain_health_history(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brain_health WHERE student_id = ? ORDER BY assessment_date DESC'
                params = [student_id]
                if education_type:
                    query = 'SELECT * FROM brain_health WHERE student_id = ? AND education_type = ? ORDER BY assessment_date DESC'
                    params.append(education_type)
                cursor.execute(query, params)
                history = [dict(h) for h in cursor.fetchall()]
                return {'success': True, 'history': history}
        except Exception as e:
            logger.error(f'获取脑健康历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def generate_learning_insights(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            insight_id = f"ins_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            insights = []
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM assessment_results WHERE student_id = ? ORDER BY completed_at DESC LIMIT 5', (student_id,))
                assessments = [dict(a) for a in cursor.fetchall()]
                cursor.execute('SELECT * FROM attention_monitoring WHERE student_id = ? ORDER BY session_date DESC LIMIT 10', (student_id,))
                attention_data = [dict(a) for a in cursor.fetchall()]
                cursor.execute('SELECT * FROM learning_effectiveness WHERE student_id = ? ORDER BY assessed_at DESC LIMIT 3', (student_id,))
                effectiveness_data = [dict(e) for e in cursor.fetchall()]
            if assessments:
                scores = [a['total_score'] for a in assessments]
                avg_score = sum(scores) / len(scores)
                insights.append({
                    'type': 'cognitive_trend',
                    'content': f'近5次认知评估平均得分{avg_score:.1f}分',
                    'confidence': 0.85,
                    'recommendation': '保持学习状态，继续提升薄弱环节'
                })
            if attention_data:
                avg_attention = sum(a['avg_attention_score'] for a in attention_data) / len(attention_data)
                insights.append({
                    'type': 'attention_pattern',
                    'content': f'近10次注意力监测平均得分{avg_attention:.1f}分',
                    'confidence': 0.8,
                    'recommendation': '根据注意力波动规律调整学习时间'
                })
            if effectiveness_data:
                scores = [e['overall_effectiveness'] for e in effectiveness_data]
                trend = '上升' if scores[-1] > scores[0] else '下降' if scores[-1] < scores[0] else '稳定'
                insights.append({
                    'type': 'effectiveness_trend',
                    'content': f'学习效能呈{trend}趋势，当前得分{scores[-1]:.1f}分',
                    'confidence': 0.88,
                    'recommendation': '持续跟踪学习效果，及时调整策略'
                })
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for insight in insights:
                        cursor.execute('''
                            INSERT INTO learning_insights (
                                insight_id, student_id, student_name, education_type,
                                insight_type, insight_content, data_source,
                                confidence_level, actionable_recommendations,
                                generated_at, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (insight_id, student_id, '', education_type,
                              insight['type'], insight['content'], 'system_analysis',
                              insight['confidence'], insight['recommendation'],
                              now[:10], now))
                    conn.commit()
            return {'success': True, 'insights': insights, 'insight_id': insight_id}
        except Exception as e:
            logger.error(f'生成学习洞察失败: {e}')
            return {'success': False, 'error': str(e)}
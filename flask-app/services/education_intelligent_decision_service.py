#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育智能决策服务 (v15.28.0)
====================================
提供决策分析、预测分析、风险评估、优化建议、决策支持、智能推荐、数据分析和可视化展示等综合服务。

核心能力：
1. 决策分析 - 战略/战术/运营/财务/人事/教学/科研/管理决策
2. 预测分析 - 趋势预测、结果预测、需求预测、资源预测
3. 风险评估 - 战略/财务/运营/合规/市场/技术/人才/声誉风险
4. 优化建议 - 资源优化、流程优化、成本优化、绩效优化、策略优化
5. 决策支持 - 数据支撑、方案对比、模拟推演、决策跟踪
6. 智能推荐 - 个性化/热门/协同/内容推荐
7. 数据分析 - 数据采集、清洗、处理、分析
8. 可视化展示 - 图表、仪表盘、报告生成
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_decision_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationDecision')


# ========== 决策配置 ==========

DECISION_TYPES = {
    'strategic': {'name': '战略决策', 'description': '长期发展规划与战略方向', 'scope': '宏观'},
    'tactical': {'name': '战术决策', 'description': '中期行动计划与资源配置', 'scope': '中观'},
    'operational': {'name': '运营决策', 'description': '日常运营管理与流程优化', 'scope': '微观'},
    'financial': {'name': '财务决策', 'description': '预算分配与成本控制', 'scope': '专项'},
    'human_resource': {'name': '人事决策', 'description': '人员配置与绩效评估', 'scope': '专项'},
    'teaching': {'name': '教学决策', 'description': '课程设计与教学方法', 'scope': '专项'},
    'research': {'name': '科研决策', 'description': '科研项目与学术发展', 'scope': '专项'},
    'management': {'name': '管理决策', 'description': '组织架构与管理制度', 'scope': '综合'}
}

ANALYSIS_METHODS = {
    'trend': {'name': '趋势分析', 'description': '数据变化趋势识别', 'suitable_for': ['时间序列数据', '发展预测']},
    'comparative': {'name': '对比分析', 'description': '多维度数据对比', 'suitable_for': ['绩效评估', '差异分析']},
    'correlation': {'name': '关联分析', 'description': '变量间关联关系', 'suitable_for': ['因素分析', '因果推断']},
    'regression': {'name': '回归分析', 'description': '变量间定量关系', 'suitable_for': ['预测建模', '影响评估']},
    'clustering': {'name': '聚类分析', 'description': '数据分组与分类', 'suitable_for': ['用户画像', '群体分析']},
    'factor': {'name': '因子分析', 'description': '多维数据降维', 'suitable_for': ['指标体系', '综合评价']},
    'time_series': {'name': '时间序列', 'description': '时序数据建模', 'suitable_for': ['趋势预测', '周期性分析']},
    'prediction': {'name': '预测分析', 'description': '未来趋势预测', 'suitable_for': ['需求预测', '结果预估']}
}

PREDICTION_MODELS = {
    'linear_regression': {'name': '线性回归', 'accuracy': '中', 'complexity': '低', 'training_data_required': '中等'},
    'nonlinear_regression': {'name': '非线性回归', 'accuracy': '中高', 'complexity': '中', 'training_data_required': '中等'},
    'time_series': {'name': '时间序列', 'accuracy': '高', 'complexity': '中', 'training_data_required': '大量'},
    'machine_learning': {'name': '机器学习', 'accuracy': '高', 'complexity': '高', 'training_data_required': '大量'},
    'deep_learning': {'name': '深度学习', 'accuracy': '很高', 'complexity': '很高', 'training_data_required': '海量'},
    'neural_network': {'name': '神经网络', 'accuracy': '高', 'complexity': '很高', 'training_data_required': '大量'},
    'expert_system': {'name': '专家系统', 'accuracy': '中高', 'complexity': '中', 'training_data_required': '知识规则'},
    'hybrid': {'name': '混合模型', 'accuracy': '很高', 'complexity': '很高', 'training_data_required': '综合'}
}

RISK_TYPES = {
    'strategic': {'name': '战略风险', 'level': '高', 'impact': '重大', 'frequency': '低'},
    'financial': {'name': '财务风险', 'level': '高', 'impact': '重大', 'frequency': '中'},
    'operational': {'name': '运营风险', 'level': '中', 'impact': '中等', 'frequency': '高'},
    'compliance': {'name': '合规风险', 'level': '高', 'impact': '重大', 'frequency': '中'},
    'market': {'name': '市场风险', 'level': '中', 'impact': '中等', 'frequency': '中'},
    'technology': {'name': '技术风险', 'level': '中', 'impact': '中等', 'frequency': '中'},
    'talent': {'name': '人才风险', 'level': '中高', 'impact': '较大', 'frequency': '低'},
    'reputation': {'name': '声誉风险', 'level': '中高', 'impact': '较大', 'frequency': '低'}
}

OPTIMIZATION_METHODS = {
    'linear_programming': {'name': '线性规划', 'applicability': '资源分配', 'complexity': '低'},
    'nonlinear_programming': {'name': '非线性规划', 'applicability': '复杂优化', 'complexity': '高'},
    'integer_programming': {'name': '整数规划', 'applicability': '离散决策', 'complexity': '中高'},
    'dynamic_programming': {'name': '动态规划', 'applicability': '序列决策', 'complexity': '高'},
    'heuristic': {'name': '启发式算法', 'applicability': '全局优化', 'complexity': '中'},
    'genetic': {'name': '遗传算法', 'applicability': '组合优化', 'complexity': '很高'},
    'simulated_annealing': {'name': '模拟退火', 'applicability': '局部最优', 'complexity': '中高'},
    'ant_colony': {'name': '蚁群算法', 'applicability': '路径优化', 'complexity': '很高'}
}

RECOMMENDATION_TYPES = {
    'personalized': {'name': '个性化推荐', 'algorithm': '基于用户', 'real_time': False},
    'popular': {'name': '热门推荐', 'algorithm': '基于热度', 'real_time': True},
    'intelligent': {'name': '智能推荐', 'algorithm': '混合算法', 'real_time': True},
    'collaborative': {'name': '协同推荐', 'algorithm': '协同过滤', 'real_time': False},
    'rule_based': {'name': '基于规则', 'algorithm': '规则引擎', 'real_time': True},
    'content_based': {'name': '基于内容', 'algorithm': '内容分析', 'real_time': False},
    'hybrid': {'name': '混合推荐', 'algorithm': '多算法融合', 'real_time': True},
    'real_time': {'name': '实时推荐', 'algorithm': '流式计算', 'real_time': True}
}

DATA_SOURCE_TYPES = {
    'structured': {'name': '结构化数据', 'format': ['CSV', 'Excel', '数据库'], 'quality': '高'},
    'unstructured': {'name': '非结构化数据', 'format': ['文本', '图片', '视频'], 'quality': '中'},
    'real_time': {'name': '实时数据', 'format': ['API', '消息队列', '传感器'], 'quality': '高'},
    'historical': {'name': '历史数据', 'format': ['归档文件', '数据仓库'], 'quality': '高'},
    'external': {'name': '外部数据', 'format': ['公开API', '第三方数据源'], 'quality': '中'},
    'internal': {'name': '内部数据', 'format': ['业务系统', '日志文件'], 'quality': '高'},
    'sensor': {'name': '传感器数据', 'format': ['IoT设备', '监控系统'], 'quality': '高'},
    'social_media': {'name': '社交媒体数据', 'format': ['微博', '微信', '论坛'], 'quality': '中'}
}

VISUALIZATION_TYPES = {
    'line': {'name': '折线图', 'use_case': '趋势展示', 'data_type': '时序数据'},
    'bar': {'name': '柱状图', 'use_case': '对比分析', 'data_type': '分类数据'},
    'pie': {'name': '饼图', 'use_case': '占比展示', 'data_type': '比例数据'},
    'scatter': {'name': '散点图', 'use_case': '相关性分析', 'data_type': '双变量数据'},
    'heatmap': {'name': '热力图', 'use_case': '密度分布', 'data_type': '矩阵数据'},
    'map': {'name': '地图', 'use_case': '地理分布', 'data_type': '空间数据'},
    'dashboard': {'name': '仪表盘', 'use_case': '综合展示', 'data_type': '多维度数据'},
    'wordcloud': {'name': '词云', 'use_case': '文本分析', 'data_type': '文本数据'}
}


class EducationIntelligentDecisionService:
    """教育智能决策服务"""

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
                    CREATE TABLE IF NOT EXISTS decision_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        decision_type TEXT NOT NULL,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL,
                        data_source TEXT,
                        analysis_method TEXT,
                        result_data TEXT,
                        conclusion TEXT,
                        confidence REAL,
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prediction_models (
                        model_id TEXT PRIMARY KEY,
                        model_name TEXT NOT NULL,
                        model_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        accuracy REAL,
                        trained_at TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prediction_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT NOT NULL,
                        prediction_type TEXT,
                        input_data TEXT,
                        prediction_result TEXT,
                        confidence REAL,
                        actual_result TEXT,
                        prediction_date TEXT,
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        risk_type TEXT NOT NULL,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        risk_level TEXT,
                        impact_score REAL,
                        probability REAL,
                        status TEXT DEFAULT 'assessing',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT NOT NULL,
                        factor_name TEXT,
                        factor_score REAL,
                        mitigation_strategy TEXT,
                        responsible_party TEXT,
                        deadline TEXT,
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS optimization_suggestions (
                        suggestion_id TEXT PRIMARY KEY,
                        optimization_type TEXT NOT NULL,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        optimization_method TEXT,
                        expected_improvement REAL,
                        status TEXT DEFAULT 'proposed',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS suggestion_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suggestion_id TEXT NOT NULL,
                        implementation_step TEXT,
                        resource_requirement TEXT,
                        estimated_cost REAL,
                        timeline TEXT,
                        responsible_party TEXT,
                        status TEXT DEFAULT 'pending',
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decision_support (
                        support_id TEXT PRIMARY KEY,
                        decision_id TEXT,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        data_summary TEXT,
                        options_analysis TEXT,
                        recommendation TEXT,
                        confidence_level REAL,
                        status TEXT DEFAULT 'supporting',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS support_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        support_id TEXT NOT NULL,
                        support_type TEXT,
                        data_source TEXT,
                        analysis_result TEXT,
                        supporting_evidence TEXT,
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intelligent_recommendation (
                        recommendation_id TEXT PRIMARY KEY,
                        recommendation_type TEXT NOT NULL,
                        education_type TEXT,
                        target_user_id INTEGER,
                        target_user_name TEXT,
                        recommended_items TEXT,
                        algorithm_used TEXT,
                        confidence REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recommendation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recommendation_id TEXT NOT NULL,
                        item_id TEXT,
                        item_name TEXT,
                        relevance_score REAL,
                        user_feedback TEXT,
                        feedback_score INTEGER,
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        data_source TEXT,
                        analysis_method TEXT,
                        status TEXT DEFAULT 'analyzing',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL,
                        raw_data TEXT,
                        processed_data TEXT,
                        key_insights TEXT,
                        metrics TEXT,
                        recorded_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS visualization_display (
                        display_id TEXT PRIMARY KEY,
                        visualization_type TEXT NOT NULL,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        data_source TEXT,
                        chart_config TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS display_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        display_id TEXT NOT NULL,
                        view_count INTEGER DEFAULT 0,
                        export_count INTEGER DEFAULT 0,
                        last_viewed_at TEXT,
                        recorded_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育智能决策服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 决策分析 ==========

    def create_decision_analysis(self, decision_type: str, title: str,
                                  education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"dca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_analysis (
                            analysis_id, decision_type, education_type,
                            title, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (analysis_id, decision_type, education_type,
                          title, kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建决策分析: {title} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建决策分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_analysis(self, analysis_id: str, data_source: str,
                          analysis_method: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT decision_type, education_type FROM decision_analysis WHERE analysis_id = ?', (analysis_id,))
                    analysis = cursor.fetchone()
                    if not analysis:
                        return {'success': False, 'error': '决策分析不存在'}
                    result_data = json.dumps(kwargs.get('result_data', {}), ensure_ascii=False)
                    cursor.execute('''
                        INSERT INTO analysis_records (
                            analysis_id, data_source, analysis_method,
                            result_data, conclusion, confidence, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, data_source, analysis_method,
                          result_data, kwargs.get('conclusion'),
                          kwargs.get('confidence', 0.85), now))
                    cursor.execute('UPDATE decision_analysis SET status = ?, updated_at = ? WHERE analysis_id = ?', ('completed', now, analysis_id))
                    conn.commit()
                    logger.info(f'执行决策分析: {analysis_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'执行决策分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM decision_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '决策分析不存在'}
                cursor.execute('SELECT * FROM analysis_records WHERE analysis_id = ? ORDER BY recorded_at DESC', (analysis_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'analysis': dict(analysis), 'records': records}
        except Exception as e:
            logger.error(f'获取分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_decision_analysis(self, decision_type: str = None,
                               education_type: str = None,
                               status: str = None, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM decision_analysis WHERE 1=1'
                params = []
                if decision_type:
                    query += ' AND decision_type = ?'
                    params.append(decision_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                analyses = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'analyses': analyses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取决策分析列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预测分析 ==========

    def create_prediction_model(self, model_name: str, model_type: str,
                                 education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            model_id = f"prm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PREDICTION_MODELS.get(model_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO prediction_models (
                            model_id, model_name, model_type, education_type,
                            description, accuracy, trained_at, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (model_id, model_name, model_type, education_type,
                          kwargs.get('description'),
                          kwargs.get('accuracy', float(config.get('accuracy', '中').replace('高', '0.8').replace('中', '0.6').replace('很', ''))),
                          kwargs.get('trained_at', now[:10]), now))
                    conn.commit()
                    logger.info(f'创建预测模型: {model_name} ({model_id})')
                    return {'success': True, 'model_id': model_id}
        except Exception as e:
            logger.error(f'创建预测模型失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_prediction(self, model_id: str, prediction_type: str,
                            input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT model_type, education_type FROM prediction_models WHERE model_id = ? AND status = ?', (model_id, 'active'))
                    model = cursor.fetchone()
                    if not model:
                        return {'success': False, 'error': '预测模型不存在或未激活'}
                    cursor.execute('''
                        INSERT INTO prediction_records (
                            model_id, prediction_type, input_data,
                            prediction_result, confidence, prediction_date, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (model_id, prediction_type,
                          json.dumps(input_data, ensure_ascii=False),
                          json.dumps(kwargs.get('prediction_result', {}), ensure_ascii=False),
                          kwargs.get('confidence', 0.8),
                          kwargs.get('prediction_date', now[:10]), now))
                    conn.commit()
                    logger.info(f'执行预测分析: {model_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'执行预测分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_prediction_actual(self, record_id: int, actual_result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE prediction_records SET actual_result = ? WHERE id = ?',
                                 (json.dumps(actual_result, ensure_ascii=False), record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预测记录不存在'}
        except Exception as e:
            logger.error(f'记录预测实际结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_prediction_history(self, model_id: str = None,
                                prediction_type: str = None,
                                education_type: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT pr.*, pm.model_name, pm.model_type, pm.education_type
                    FROM prediction_records pr
                    JOIN prediction_models pm ON pr.model_id = pm.model_id
                    WHERE 1=1
                '''
                params = []
                if model_id:
                    query += ' AND pr.model_id = ?'
                    params.append(model_id)
                if prediction_type:
                    query += ' AND pr.prediction_type = ?'
                    params.append(prediction_type)
                if education_type:
                    query += ' AND pm.education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY pr.recorded_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预测历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 风险评估 ==========

    def create_risk_assessment(self, risk_type: str, title: str,
                                education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"rsa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = RISK_TYPES.get(risk_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO risk_assessment (
                            assessment_id, risk_type, education_type,
                            title, description, risk_level,
                            impact_score, probability, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'assessing', ?, ?)
                    ''', (assessment_id, risk_type, education_type,
                          title, kwargs.get('description'),
                          kwargs.get('risk_level', config.get('level', '中')),
                          kwargs.get('impact_score', 0.5),
                          kwargs.get('probability', 0.5), now, now))
                    conn.commit()
                    logger.info(f'创建风险评估: {title} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建风险评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_risk_factor(self, assessment_id: str, factor_name: str,
                         factor_score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM risk_assessment WHERE assessment_id = ?', (assessment_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '风险评估不存在'}
                    cursor.execute('''
                        INSERT INTO assessment_records (
                            assessment_id, factor_name, factor_score,
                            mitigation_strategy, responsible_party, deadline, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (assessment_id, factor_name, factor_score,
                          kwargs.get('mitigation_strategy'),
                          kwargs.get('responsible_party'),
                          kwargs.get('deadline'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加风险因素失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_assessment(self, assessment_id: str, risk_level: str,
                             impact_score: float, probability: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE risk_assessment SET risk_level = ?, impact_score = ?, probability = ?, status = ?, updated_at = ? WHERE assessment_id = ?',
                                 (risk_level, impact_score, probability, 'completed', now, assessment_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'risk_level': risk_level}
                    return {'success': False, 'error': '风险评估不存在'}
        except Exception as e:
            logger.error(f'完成风险评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_risk_assessments(self, risk_type: str = None,
                              education_type: str = None,
                              risk_level: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM risk_assessment WHERE 1=1'
                params = []
                if risk_type:
                    query += ' AND risk_type = ?'
                    params.append(risk_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if risk_level:
                    query += ' AND risk_level = ?'
                    params.append(risk_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assessments = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assessments': assessments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取风险评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 优化建议 ==========

    def create_optimization_suggestion(self, optimization_type: str, title: str,
                                        education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            suggestion_id = f"opt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO optimization_suggestions (
                            suggestion_id, optimization_type, education_type,
                            title, description, optimization_method,
                            expected_improvement, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?)
                    ''', (suggestion_id, optimization_type, education_type,
                          title, kwargs.get('description'),
                          kwargs.get('optimization_method'),
                          kwargs.get('expected_improvement', 0), now, now))
                    conn.commit()
                    logger.info(f'创建优化建议: {title} ({suggestion_id})')
                    return {'success': True, 'suggestion_id': suggestion_id}
        except Exception as e:
            logger.error(f'创建优化建议失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_implementation_step(self, suggestion_id: str, implementation_step: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM optimization_suggestions WHERE suggestion_id = ?', (suggestion_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '优化建议不存在'}
                    cursor.execute('''
                        INSERT INTO suggestion_records (
                            suggestion_id, implementation_step, resource_requirement,
                            estimated_cost, timeline, responsible_party, status, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (suggestion_id, implementation_step,
                          kwargs.get('resource_requirement'),
                          kwargs.get('estimated_cost', 0),
                          kwargs.get('timeline'),
                          kwargs.get('responsible_party'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加实施步骤失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE optimization_suggestions SET status = ?, updated_at = ? WHERE suggestion_id = ? AND status = ?',
                                 ('approved', now, suggestion_id, 'proposed'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '优化建议状态不允许审批'}
        except Exception as e:
            logger.error(f'审批优化建议失败: {e}')
            return {'success': False, 'error': str(e)}

    def implement_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE optimization_suggestions SET status = ?, updated_at = ? WHERE suggestion_id = ? AND status = ?',
                                 ('implemented', now, suggestion_id, 'approved'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE suggestion_records SET status = ? WHERE suggestion_id = ? AND status = ?', ('completed', suggestion_id, 'pending'))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '优化建议状态不允许实施'}
        except Exception as e:
            logger.error(f'实施优化建议失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_suggestion_details(self, suggestion_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM optimization_suggestions WHERE suggestion_id = ?', (suggestion_id,))
                suggestion = cursor.fetchone()
                if not suggestion:
                    return {'success': False, 'error': '优化建议不存在'}
                cursor.execute('SELECT * FROM suggestion_records WHERE suggestion_id = ? ORDER BY recorded_at', (suggestion_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'suggestion': dict(suggestion), 'records': records}
        except Exception as e:
            logger.error(f'获取优化建议详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 决策支持 ==========

    def create_decision_support(self, decision_id: str, title: str,
                                 education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            support_id = f"dcs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_support (
                            support_id, decision_id, education_type,
                            title, data_summary, options_analysis,
                            recommendation, confidence_level, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'supporting', ?, ?)
                    ''', (support_id, decision_id, education_type,
                          title, kwargs.get('data_summary'),
                          kwargs.get('options_analysis'),
                          kwargs.get('recommendation'),
                          kwargs.get('confidence_level', 0.8), now, now))
                    conn.commit()
                    logger.info(f'创建决策支持: {title} ({support_id})')
                    return {'success': True, 'support_id': support_id}
        except Exception as e:
            logger.error(f'创建决策支持失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_supporting_evidence(self, support_id: str, support_type: str,
                                 data_source: str, analysis_result: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM decision_support WHERE support_id = ?', (support_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '决策支持不存在'}
                    cursor.execute('''
                        INSERT INTO support_records (
                            support_id, support_type, data_source,
                            analysis_result, supporting_evidence, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (support_id, support_type, data_source,
                          analysis_result, kwargs.get('supporting_evidence'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加支持证据失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_decision_support(self, support_id: str, final_recommendation: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE decision_support SET recommendation = ?, status = ?, updated_at = ? WHERE support_id = ?',
                                 (final_recommendation, 'completed', now, support_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '决策支持不存在'}
        except Exception as e:
            logger.error(f'完成决策支持失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_decision_support_history(self, decision_id: str = None,
                                      education_type: str = None,
                                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM decision_support WHERE 1=1'
                params = []
                if decision_id:
                    query += ' AND decision_id = ?'
                    params.append(decision_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                supports = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'supports': supports, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取决策支持历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能推荐 ==========

    def generate_recommendation(self, recommendation_type: str,
                                 target_user_id: int, target_user_name: str,
                                 education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            recommendation_id = f"rcm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO intelligent_recommendation (
                            recommendation_id, recommendation_type, education_type,
                            target_user_id, target_user_name, recommended_items,
                            algorithm_used, confidence, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (recommendation_id, recommendation_type, education_type,
                          target_user_id, target_user_name,
                          json.dumps(kwargs.get('recommended_items', []), ensure_ascii=False),
                          kwargs.get('algorithm_used', recommendation_type),
                          kwargs.get('confidence', 0.75), now))
                    conn.commit()
                    logger.info(f'生成智能推荐: {recommendation_id}')
                    return {'success': True, 'recommendation_id': recommendation_id}
        except Exception as e:
            logger.error(f'生成智能推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_recommendation_item(self, recommendation_id: str, item_id: str,
                                 item_name: str, relevance_score: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM intelligent_recommendation WHERE recommendation_id = ?', (recommendation_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '推荐不存在'}
                    cursor.execute('''
                        INSERT INTO recommendation_records (
                            recommendation_id, item_id, item_name,
                            relevance_score, user_feedback, feedback_score, recorded_at
                        ) VALUES (?, ?, ?, ?, NULL, NULL, ?)
                    ''', (recommendation_id, item_id, item_name, relevance_score, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加推荐项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_user_feedback(self, record_id: int, user_feedback: str,
                              feedback_score: int) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE recommendation_records SET user_feedback = ?, feedback_score = ? WHERE id = ?',
                                 (user_feedback, feedback_score, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推荐记录不存在'}
        except Exception as e:
            logger.error(f'记录用户反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_recommendations(self, target_user_id: int,
                                  education_type: str = None,
                                  page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM intelligent_recommendation WHERE target_user_id = ?'
                params = [target_user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                recommendations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'recommendations': recommendations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取用户推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据分析 ==========

    def create_data_analysis(self, data_type: str, title: str,
                              education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"dta_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_analysis (
                            analysis_id, data_type, education_type,
                            title, description, data_source,
                            analysis_method, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'analyzing', ?, ?)
                    ''', (analysis_id, data_type, education_type,
                          title, kwargs.get('description'),
                          kwargs.get('data_source'),
                          kwargs.get('analysis_method'), now, now))
                    conn.commit()
                    logger.info(f'创建数据分析: {title} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建数据分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_analysis_data(self, analysis_id: str, raw_data: Dict[str, Any],
                           processed_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM data_analysis WHERE analysis_id = ?', (analysis_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '数据分析不存在'}
                    cursor.execute('''
                        INSERT INTO analysis_data (
                            analysis_id, raw_data, processed_data,
                            key_insights, metrics, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, json.dumps(raw_data, ensure_ascii=False),
                          json.dumps(processed_data, ensure_ascii=False),
                          kwargs.get('key_insights'),
                          json.dumps(kwargs.get('metrics', {}), ensure_ascii=False), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加分析数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_data_analysis(self, analysis_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE data_analysis SET status = ?, updated_at = ? WHERE analysis_id = ?',
                                 ('completed', now, analysis_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '数据分析不存在'}
        except Exception as e:
            logger.error(f'完成数据分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_data_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM data_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '数据分析不存在'}
                cursor.execute('SELECT * FROM analysis_data WHERE analysis_id = ? ORDER BY recorded_at DESC', (analysis_id,))
                data_records = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'analysis': dict(analysis), 'data_records': data_records}
        except Exception as e:
            logger.error(f'获取数据分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 可视化展示 ==========

    def create_visualization(self, visualization_type: str, title: str,
                              education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            display_id = f"viz_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO visualization_display (
                            display_id, visualization_type, education_type,
                            title, data_source, chart_config, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (display_id, visualization_type, education_type,
                          title, kwargs.get('data_source'),
                          json.dumps(kwargs.get('chart_config', {}), ensure_ascii=False), now, now))
                    conn.commit()
                    logger.info(f'创建可视化展示: {title} ({display_id})')
                    return {'success': True, 'display_id': display_id}
        except Exception as e:
            logger.error(f'创建可视化展示失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_view(self, display_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM visualization_display WHERE display_id = ?', (display_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '可视化展示不存在'}
                    cursor.execute('INSERT INTO display_records (display_id, view_count, export_count, last_viewed_at, recorded_at) VALUES (?, 1, 0, ?, ?)',
                                 (display_id, now, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录视图失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_export(self, display_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM visualization_display WHERE display_id = ?', (display_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '可视化展示不存在'}
                    cursor.execute('INSERT INTO display_records (display_id, view_count, export_count, last_viewed_at, recorded_at) VALUES (?, 0, 1, ?, ?)',
                                 (display_id, now, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录导出失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_visualization_stats(self, display_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM visualization_display WHERE display_id = ?', (display_id,))
                display = cursor.fetchone()
                if not display:
                    return {'success': False, 'error': '可视化展示不存在'}
                cursor.execute('SELECT SUM(view_count) as total_views, SUM(export_count) as total_exports FROM display_records WHERE display_id = ?', (display_id,))
                stats = cursor.fetchone()
                return {
                    'success': True,
                    'display': dict(display),
                    'total_views': stats['total_views'] or 0,
                    'total_exports': stats['total_exports'] or 0
                }
        except Exception as e:
            logger.error(f'获取可视化统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_service_statistics(self, education_type: str = None,
                                date_range: Tuple[str, str] = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                query_base = 'WHERE 1=1'
                params = []
                if education_type:
                    query_base += ' AND education_type = ?'
                    params.append(education_type)
                if date_range:
                    query_base += ' AND created_at >= ? AND created_at <= ?'
                    params.extend(date_range)

                cursor.execute(f'SELECT COUNT(*) FROM decision_analysis {query_base}', params)
                stats['decision_analysis_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM prediction_models {query_base}', params)
                stats['prediction_model_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM prediction_records')
                stats['prediction_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM risk_assessment {query_base}', params)
                stats['risk_assessment_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM optimization_suggestions {query_base}', params)
                stats['optimization_suggestion_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM decision_support {query_base}', params)
                stats['decision_support_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM intelligent_recommendation {query_base}', params)
                stats['recommendation_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_analysis {query_base}', params)
                stats['data_analysis_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM visualization_display {query_base}', params)
                stats['visualization_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT SUM(view_count) FROM display_records')
                stats['total_views'] = cursor.fetchone()[0] or 0

                cursor.execute('SELECT SUM(export_count) FROM display_records')
                stats['total_exports'] = cursor.fetchone()[0] or 0

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}
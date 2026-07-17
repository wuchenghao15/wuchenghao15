#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育智慧决策服务 (v15.15.0)
====================================
提供教育大数据决策、智能分析、预测预警、决策支持、知识图谱、可视化仪表盘、智能推荐、绩效评估等综合服务。

核心能力：
1. 决策模型 - 模型管理、规则配置、策略优化、方案生成
2. 数据分析 - 数据查询、统计分析、趋势分析、对比分析
3. 知识图谱 - 图谱构建、实体管理、关系挖掘、路径分析
4. 可视化 - 仪表盘、报表、图表、数据大屏
5. 智能推荐 - 课程推荐、学习路径、教师推荐、资源推荐
6. 预测预警 - 成绩预警、辍学预警、资源预警、财务预警、安全预警
7. 绩效评估 - 指标管理、数据采集、评估计算、报告生成
8. 决策日志 - 日志记录、查询分析、审计追踪
9. 反馈管理 - 反馈收集、分析处理、改进建议
10. 统计分析 - 综合统计、趋势预测
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_smart_decision_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSmartDecision')


# ========== 决策配置 ==========

DECISION_TYPES = {
    'strategic': {'name': '战略决策', 'description': '学校发展规划、办学方向、重大投资'},
    'operational': {'name': '运营决策', 'description': '日常运营管理、流程优化、资源调度'},
    'teaching': {'name': '教学决策', 'description': '课程设置、教学方法、教学质量提升'},
    'management': {'name': '管理决策', 'description': '人事管理、制度建设、组织架构'},
    'financial': {'name': '财务决策', 'description': '预算分配、成本控制、资金管理'},
    'enrollment': {'name': '招生决策', 'description': '招生计划、生源分析、录取策略'},
    'employment': {'name': '就业决策', 'description': '就业指导、校企合作、职业规划'},
    'resource': {'name': '资源配置决策', 'description': '教室分配、设备采购、师资调配'}
}

ANALYSIS_MODELS = {
    'regression': {'name': '回归分析', 'description': '建立变量间的函数关系，预测数值型结果'},
    'clustering': {'name': '聚类分析', 'description': '将数据分组，发现数据内在结构'},
    'association': {'name': '关联分析', 'description': '发现数据间的关联规则和模式'},
    'prediction': {'name': '预测模型', 'description': '基于历史数据预测未来趋势'},
    'optimization': {'name': '优化模型', 'description': '寻找最优解或最优策略'},
    'evaluation': {'name': '评估模型', 'description': '综合评估多维度指标'},
    'recommendation': {'name': '推荐模型', 'description': '基于用户画像生成个性化推荐'},
    'knowledge_graph': {'name': '知识图谱', 'description': '构建知识网络，挖掘语义关系'}
}

DATA_DOMAINS = {
    'teaching': {'name': '教学数据', 'description': '课程、教学、学习、考试数据'},
    'student': {'name': '学生数据', 'description': '学生基本信息、成绩、行为数据'},
    'teacher': {'name': '教师数据', 'description': '教师信息、教学、科研、绩效数据'},
    'financial': {'name': '财务数据', 'description': '预算、收支、成本、资产数据'},
    'resource': {'name': '资源数据', 'description': '教室、设备、图书、场地数据'},
    'management': {'name': '管理数据', 'description': '行政、人事、制度、流程数据'},
    'enrollment': {'name': '招生数据', 'description': '报名、录取、生源、报到数据'},
    'employment': {'name': '就业数据', 'description': '就业、实习、职业发展数据'}
}

METRIC_TYPES = {
    'efficiency': {'name': '效率指标', 'description': '投入产出比、资源利用率'},
    'effectiveness': {'name': '效果指标', 'description': '目标达成度、成果产出'},
    'benefit': {'name': '效益指标', 'description': '经济效益、社会效益'},
    'quality': {'name': '质量指标', 'description': '教学质量、服务质量'},
    'satisfaction': {'name': '满意度指标', 'description': '师生满意度、家长满意度'},
    'competitiveness': {'name': '竞争力指标', 'description': '排名、影响力、竞争力'}
}

DECISION_LEVELS = {
    'school': {'name': '校级决策', 'description': '学校层面的重大决策'},
    'department': {'name': '部门决策', 'description': '职能部门层面的决策'},
    'faculty': {'name': '院系决策', 'description': '院系层面的决策'},
    'class': {'name': '班级决策', 'description': '班级层面的决策'},
    'individual': {'name': '个人决策', 'description': '个人学习、发展决策'}
}

VISUALIZATION_TYPES = {
    'dashboard': {'name': '仪表盘', 'description': '综合数据展示面板'},
    'report': {'name': '报表', 'description': '结构化数据报表'},
    'chart': {'name': '图表', 'description': '折线图、柱状图、饼图等'},
    'map': {'name': '地图', 'description': '地理空间数据展示'},
    'heatmap': {'name': '热力图', 'description': '密度分布可视化'},
    'trend': {'name': '趋势图', 'description': '时间序列趋势展示'},
    'comparison': {'name': '对比图', 'description': '多维度对比分析'},
    'funnel': {'name': '漏斗图', 'description': '转化漏斗分析'}
}

RECOMMENDATION_TYPES = {
    'course': {'name': '课程推荐', 'description': '基于学习历史推荐课程'},
    'learning_path': {'name': '学习路径', 'description': '个性化学习路径规划'},
    'teacher': {'name': '教师推荐', 'description': '基于学生需求推荐教师'},
    'resource': {'name': '资源推荐', 'description': '教学资源、学习资料推荐'},
    'activity': {'name': '活动推荐', 'description': '校园活动、社团活动推荐'},
    'employment': {'name': '就业推荐', 'description': '实习、就业岗位推荐'}
}

ALERT_TYPES = {
    'academic': {'name': '成绩预警', 'description': '学生成绩下滑预警'},
    'dropout': {'name': '辍学预警', 'description': '学生辍学风险预警'},
    'resource': {'name': '资源预警', 'description': '资源短缺、设备故障预警'},
    'financial': {'name': '财务预警', 'description': '财务风险、资金异常预警'},
    'safety': {'name': '安全预警', 'description': '校园安全、突发事件预警'},
    'public_opinion': {'name': '舆情预警', 'description': '负面舆情、网络热点预警'}
}


class EducationSmartDecisionService:
    """教育智慧决策服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS decision_models (
                            model_id TEXT PRIMARY KEY,
                            model_name TEXT NOT NULL,
                            model_type TEXT,
                            decision_type TEXT,
                            analysis_model TEXT,
                            education_type TEXT,
                            description TEXT,
                            config_json TEXT,
                            accuracy REAL DEFAULT 0,
                            status TEXT DEFAULT 'active',
                            version TEXT DEFAULT '1.0',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS decision_rules (
                            rule_id TEXT PRIMARY KEY,
                            model_id TEXT NOT NULL,
                            rule_name TEXT NOT NULL,
                            rule_expression TEXT,
                            priority INTEGER DEFAULT 1,
                            education_type TEXT,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT,
                            FOREIGN KEY (model_id) REFERENCES decision_models(model_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS analysis_tasks (
                            task_id TEXT PRIMARY KEY,
                            task_name TEXT NOT NULL,
                            data_domain TEXT,
                            analysis_model TEXT,
                            education_type TEXT,
                            parameters_json TEXT,
                            status TEXT DEFAULT 'pending',
                            progress INTEGER DEFAULT 0,
                            created_at TEXT,
                            started_at TEXT,
                            completed_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS analysis_results (
                            result_id TEXT PRIMARY KEY,
                            task_id TEXT NOT NULL,
                            data_domain TEXT,
                            education_type TEXT,
                            result_json TEXT,
                            summary TEXT,
                            recommendations TEXT,
                            confidence REAL DEFAULT 0,
                            created_at TEXT,
                            FOREIGN KEY (task_id) REFERENCES analysis_tasks(task_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS data_sources (
                            source_id TEXT PRIMARY KEY,
                            source_name TEXT NOT NULL,
                            data_domain TEXT,
                            source_type TEXT,
                            connection_string TEXT,
                            education_type TEXT,
                            is_active INTEGER DEFAULT 1,
                            last_sync_at TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS data_pipelines (
                            pipeline_id TEXT PRIMARY KEY,
                            pipeline_name TEXT NOT NULL,
                            source_id TEXT,
                            data_domain TEXT,
                            education_type TEXT,
                            transform_rules TEXT,
                            schedule_type TEXT DEFAULT 'daily',
                            status TEXT DEFAULT 'active',
                            last_run_at TEXT,
                            created_at TEXT,
                            updated_at TEXT,
                            FOREIGN KEY (source_id) REFERENCES data_sources(source_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS knowledge_graph (
                            graph_id TEXT PRIMARY KEY,
                            graph_name TEXT NOT NULL,
                            description TEXT,
                            education_type TEXT,
                            node_count INTEGER DEFAULT 0,
                            edge_count INTEGER DEFAULT 0,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS graph_nodes (
                            node_id TEXT PRIMARY KEY,
                            graph_id TEXT NOT NULL,
                            node_name TEXT NOT NULL,
                            node_type TEXT,
                            properties_json TEXT,
                            education_type TEXT,
                            created_at TEXT,
                            FOREIGN KEY (graph_id) REFERENCES knowledge_graph(graph_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS graph_edges (
                            edge_id TEXT PRIMARY KEY,
                            graph_id TEXT NOT NULL,
                            source_node_id TEXT NOT NULL,
                            target_node_id TEXT NOT NULL,
                            edge_type TEXT,
                            properties_json TEXT,
                            education_type TEXT,
                            created_at TEXT,
                            FOREIGN KEY (graph_id) REFERENCES knowledge_graph(graph_id),
                            FOREIGN KEY (source_node_id) REFERENCES graph_nodes(node_id),
                            FOREIGN KEY (target_node_id) REFERENCES graph_nodes(node_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS dashboards (
                            dashboard_id TEXT PRIMARY KEY,
                            dashboard_name TEXT NOT NULL,
                            decision_level TEXT,
                            education_type TEXT,
                            layout_json TEXT,
                            refresh_interval INTEGER DEFAULT 300,
                            is_public INTEGER DEFAULT 0,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS dashboard_widgets (
                            widget_id TEXT PRIMARY KEY,
                            dashboard_id TEXT NOT NULL,
                            widget_name TEXT NOT NULL,
                            visualization_type TEXT,
                            data_domain TEXT,
                            config_json TEXT,
                            position_json TEXT,
                            education_type TEXT,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT,
                            FOREIGN KEY (dashboard_id) REFERENCES dashboards(dashboard_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS recommendations (
                            rec_id TEXT PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            user_type TEXT,
                            rec_type TEXT,
                            education_type TEXT,
                            items_json TEXT,
                            reason TEXT,
                            confidence REAL DEFAULT 0,
                            is_viewed INTEGER DEFAULT 0,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS recommendation_rules (
                            rule_id TEXT PRIMARY KEY,
                            rec_type TEXT NOT NULL,
                            education_type TEXT,
                            rule_name TEXT NOT NULL,
                            rule_logic TEXT,
                            weight REAL DEFAULT 1.0,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS performance_metrics (
                            metric_id TEXT PRIMARY KEY,
                            metric_name TEXT NOT NULL,
                            metric_type TEXT,
                            data_domain TEXT,
                            education_type TEXT,
                            calculation_formula TEXT,
                            target_value REAL,
                            unit TEXT,
                            description TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS metric_data (
                            data_id TEXT PRIMARY KEY,
                            metric_id TEXT NOT NULL,
                            education_type TEXT,
                            period TEXT,
                            actual_value REAL,
                            target_value REAL,
                            trend TEXT,
                            score REAL DEFAULT 0,
                            created_at TEXT,
                            FOREIGN KEY (metric_id) REFERENCES performance_metrics(metric_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS prediction_results (
                            pred_id TEXT PRIMARY KEY,
                            model_id TEXT NOT NULL,
                            data_domain TEXT,
                            education_type TEXT,
                            prediction_json TEXT,
                            confidence REAL DEFAULT 0,
                            forecast_period TEXT,
                            created_at TEXT,
                            FOREIGN KEY (model_id) REFERENCES decision_models(model_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS alert_records (
                            alert_id TEXT PRIMARY KEY,
                            alert_type TEXT NOT NULL,
                            education_type TEXT,
                            severity TEXT DEFAULT 'medium',
                            title TEXT NOT NULL,
                            description TEXT,
                            affected_objects TEXT,
                            status TEXT DEFAULT 'pending',
                            trigger_time TEXT,
                            acknowledged_at TEXT,
                            resolved_at TEXT,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS decision_logs (
                            log_id TEXT PRIMARY KEY,
                            decision_type TEXT,
                            education_type TEXT,
                            decision_level TEXT,
                            user_id INTEGER,
                            user_name TEXT,
                            action TEXT,
                            details_json TEXT,
                            result TEXT,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS decision_feedback (
                            feedback_id TEXT PRIMARY KEY,
                            decision_id TEXT,
                            education_type TEXT,
                            user_id INTEGER,
                            user_name TEXT,
                            rating INTEGER,
                            comment TEXT,
                            improvement_suggestions TEXT,
                            created_at TEXT
                        )
                    ''')
                    conn.commit()
                    logger.info('教育智慧决策服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 决策模型 ==========

    def create_decision_model(self, model_name: str, model_type: str,
                              decision_type: str, analysis_model: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            model_id = f"dm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_models (
                            model_id, model_name, model_type, decision_type,
                            analysis_model, education_type, description,
                            config_json, accuracy, status, version,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', '1.0', ?, ?)
                    ''', (model_id, model_name, model_type, decision_type,
                          analysis_model, kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('config_json', '{}'),
                          kwargs.get('accuracy', 0), now, now))
                    conn.commit()
                    logger.info(f'创建决策模型: {model_name} ({model_id})')
                    return {'success': True, 'model_id': model_id}
        except Exception as e:
            logger.error(f'创建决策模型失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_decision_rule(self, model_id: str, rule_name: str,
                          rule_expression: str, **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"dr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT model_id FROM decision_models WHERE model_id = ?', (model_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '决策模型不存在'}
                    cursor.execute('''
                        INSERT INTO decision_rules (
                            rule_id, model_id, rule_name, rule_expression,
                            priority, education_type, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (rule_id, model_id, rule_name, rule_expression,
                          kwargs.get('priority', 1), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'添加决策规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def optimize_decision_strategy(self, model_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT model_id FROM decision_models WHERE model_id = ?', (model_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '决策模型不存在'}
                    accuracy = kwargs.get('accuracy', 0)
                    config_json = kwargs.get('config_json')
                    updates = []
                    params = []
                    if accuracy:
                        updates.append('accuracy = ?')
                        params.append(accuracy)
                    if config_json:
                        updates.append('config_json = ?')
                        params.append(config_json)
                    updates.append('updated_at = ?')
                    params.append(now)
                    params.append(model_id)
                    cursor.execute(f'UPDATE decision_models SET {", ".join(updates)} WHERE model_id = ?', params)
                    conn.commit()
                    return {'success': True, 'message': '策略优化完成'}
        except Exception as e:
            logger.error(f'优化决策策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_decision_scheme(self, model_id: str, input_data: Dict[str, Any],
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT model_name, decision_type, analysis_model, education_type FROM decision_models WHERE model_id = ?', (model_id,))
                model = cursor.fetchone()
                if not model:
                    return {'success': False, 'error': '决策模型不存在'}
                decision_type_info = DECISION_TYPES.get(model[1], {})
                analysis_model_info = ANALYSIS_MODELS.get(model[2], {})
                scheme = {
                    'scheme_id': f"ds_{uuid.uuid4().hex[:12]}",
                    'model_id': model_id,
                    'model_name': model[0],
                    'decision_type': model[1],
                    'decision_type_name': decision_type_info.get('name', ''),
                    'analysis_model': model[2],
                    'analysis_model_name': analysis_model_info.get('name', ''),
                    'education_type': model[3],
                    'input_data': input_data,
                    'generated_at': now,
                    'recommendations': [],
                    'confidence': 0.85
                }
                cursor.execute('SELECT rule_name, rule_expression, priority FROM decision_rules WHERE model_id = ? AND is_active = 1 ORDER BY priority', (model_id,))
                rules = cursor.fetchall()
                for rule in rules:
                    scheme['recommendations'].append({
                        'rule_name': rule[0],
                        'rule_expression': rule[1],
                        'priority': rule[2]
                    })
                return {'success': True, 'scheme': scheme}
        except Exception as e:
            logger.error(f'生成决策方案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据分析 ==========

    def create_analysis_task(self, task_name: str, data_domain: str,
                             analysis_model: str, **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"at_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO analysis_tasks (
                            task_id, task_name, data_domain, analysis_model,
                            education_type, parameters_json, status, progress,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, ?)
                    ''', (task_id, task_name, data_domain, analysis_model,
                          kwargs.get('education_type'),
                          kwargs.get('parameters_json', '{}'), now))
                    conn.commit()
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_analysis(self, task_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM analysis_tasks WHERE task_id = ?', (task_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '分析任务不存在'}
                    if task[0] == 'running':
                        return {'success': False, 'error': '任务正在执行中'}
                    cursor.execute('UPDATE analysis_tasks SET status = ?, started_at = ?, progress = ? WHERE task_id = ?', ('running', now, 50, task_id))
                    conn.commit()
            cursor.execute('SELECT data_domain, analysis_model, education_type, parameters_json FROM analysis_tasks WHERE task_id = ?', (task_id,))
            task_info = cursor.fetchone()
            result_id = f"ar_{uuid.uuid4().hex[:12]}"
            domain_info = DATA_DOMAINS.get(task_info[0], {})
            model_info = ANALYSIS_MODELS.get(task_info[1], {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO analysis_results (
                            result_id, task_id, data_domain, education_type,
                            result_json, summary, recommendations, confidence,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, task_id, task_info[0], task_info[2],
                          json.dumps({'analysis_type': task_info[1], 'domain': task_info[0]}),
                          f'{domain_info.get("name", "")} {model_info.get("name", "")}分析完成',
                          json.dumps([]), 0.88, now))
                    cursor.execute('UPDATE analysis_tasks SET status = ?, completed_at = ?, progress = ? WHERE task_id = ?', ('completed', now, 100, task_id))
                    conn.commit()
            return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'执行分析任务失败: {e}')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE analysis_tasks SET status = ?, completed_at = ?, progress = ? WHERE task_id = ?', ('failed', datetime.now().isoformat(), 0, task_id))
                    conn.commit()
            return {'success': False, 'error': str(e)}

    def query_analysis_results(self, task_id: str = None, data_domain: str = None,
                               education_type: str = None, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM analysis_results WHERE 1=1'
                params = []
                if task_id:
                    query += ' AND task_id = ?'
                    params.append(task_id)
                if data_domain:
                    query += ' AND data_domain = ?'
                    params.append(data_domain)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def compare_analysis_results(self, result_ids: List[str]) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                placeholders = ','.join(['?'] * len(result_ids))
                query = f'SELECT * FROM analysis_results WHERE result_id IN ({placeholders})'
                cursor.execute(query, result_ids)
                results = [dict(r) for r in cursor.fetchall()]
                if len(results) < 2:
                    return {'success': False, 'error': '至少需要两个结果进行对比'}
                comparison = {
                    'comparison_id': f"cmp_{uuid.uuid4().hex[:12]}",
                    'result_ids': result_ids,
                    'results_count': len(results),
                    'comparison_data': [],
                    'summary': ''
                }
                for r in results:
                    comparison['comparison_data'].append({
                        'result_id': r['result_id'],
                        'data_domain': r['data_domain'],
                        'education_type': r['education_type'],
                        'confidence': r['confidence'],
                        'created_at': r['created_at']
                    })
                comparison['summary'] = f'完成{len(results)}个分析结果对比'
                return {'success': True, 'comparison': comparison}
        except Exception as e:
            logger.error(f'对比分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识图谱 ==========

    def create_knowledge_graph(self, graph_name: str, **kwargs) -> Dict[str, Any]:
        try:
            graph_id = f"kg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_graph (
                            graph_id, graph_name, description, education_type,
                            node_count, edge_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 0, 0, 'active', ?, ?)
                    ''', (graph_id, graph_name, kwargs.get('description'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建知识图谱: {graph_name} ({graph_id})')
                    return {'success': True, 'graph_id': graph_id}
        except Exception as e:
            logger.error(f'创建知识图谱失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_graph_node(self, graph_id: str, node_name: str, node_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            node_id = f"gn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT graph_id FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '知识图谱不存在'}
                    cursor.execute('''
                        INSERT INTO graph_nodes (
                            node_id, graph_id, node_name, node_type,
                            properties_json, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (node_id, graph_id, node_name, node_type,
                          kwargs.get('properties_json', '{}'),
                          kwargs.get('education_type'), now))
                    cursor.execute('UPDATE knowledge_graph SET node_count = node_count + 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    conn.commit()
                    return {'success': True, 'node_id': node_id}
        except Exception as e:
            logger.error(f'添加图谱节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_graph_edge(self, graph_id: str, source_node_id: str,
                       target_node_id: str, edge_type: str, **kwargs) -> Dict[str, Any]:
        try:
            edge_id = f"ge_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT graph_id FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '知识图谱不存在'}
                    cursor.execute('SELECT node_id FROM graph_nodes WHERE node_id = ? AND graph_id = ?', (source_node_id, graph_id))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '源节点不存在'}
                    cursor.execute('SELECT node_id FROM graph_nodes WHERE node_id = ? AND graph_id = ?', (target_node_id, graph_id))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '目标节点不存在'}
                    cursor.execute('''
                        INSERT INTO graph_edges (
                            edge_id, graph_id, source_node_id, target_node_id,
                            edge_type, properties_json, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (edge_id, graph_id, source_node_id, target_node_id,
                          edge_type, kwargs.get('properties_json', '{}'),
                          kwargs.get('education_type'), now))
                    cursor.execute('UPDATE knowledge_graph SET edge_count = edge_count + 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    conn.commit()
                    return {'success': True, 'edge_id': edge_id}
        except Exception as e:
            logger.error(f'添加图谱边失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_graph_path(self, graph_id: str, start_node_id: str,
                           end_node_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT graph_id FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                if not cursor.fetchone():
                    return {'success': False, 'error': '知识图谱不存在'}
                cursor.execute('SELECT node_name FROM graph_nodes WHERE node_id = ?', (start_node_id,))
                start_node = cursor.fetchone()
                cursor.execute('SELECT node_name FROM graph_nodes WHERE node_id = ?', (end_node_id,))
                end_node = cursor.fetchone()
                if not start_node or not end_node:
                    return {'success': False, 'error': '节点不存在'}
                cursor.execute('''
                    SELECT e.edge_id, e.edge_type, e.source_node_id, e.target_node_id,
                           sn.node_name as source_name, tn.node_name as target_name
                    FROM graph_edges e
                    JOIN graph_nodes sn ON e.source_node_id = sn.node_id
                    JOIN graph_nodes tn ON e.target_node_id = tn.node_id
                    WHERE e.graph_id = ? AND (e.source_node_id = ? OR e.target_node_id = ?)
                ''', (graph_id, start_node_id, start_node_id))
                edges = [dict(e) for e in cursor.fetchall()]
                path_analysis = {
                    'analysis_id': f"pa_{uuid.uuid4().hex[:12]}",
                    'graph_id': graph_id,
                    'start_node_id': start_node_id,
                    'start_node_name': start_node['node_name'],
                    'end_node_id': end_node_id,
                    'end_node_name': end_node['node_name'],
                    'path_found': len(edges) > 0,
                    'related_edges': edges,
                    'path_count': len(edges)
                }
                return {'success': True, 'path_analysis': path_analysis}
        except Exception as e:
            logger.error(f'图谱路径分析失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 可视化 ==========

    def create_dashboard(self, dashboard_name: str, decision_level: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            dashboard_id = f"db_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO dashboards (
                            dashboard_id, dashboard_name, decision_level,
                            education_type, layout_json, refresh_interval,
                            is_public, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (dashboard_id, dashboard_name, decision_level,
                          kwargs.get('education_type'),
                          kwargs.get('layout_json', '{}'),
                          kwargs.get('refresh_interval', 300),
                          kwargs.get('is_public', 0), now, now))
                    conn.commit()
                    logger.info(f'创建仪表盘: {dashboard_name} ({dashboard_id})')
                    return {'success': True, 'dashboard_id': dashboard_id}
        except Exception as e:
            logger.error(f'创建仪表盘失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_dashboard_widget(self, dashboard_id: str, widget_name: str,
                             visualization_type: str, data_domain: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            widget_id = f"dw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT dashboard_id FROM dashboards WHERE dashboard_id = ?', (dashboard_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '仪表盘不存在'}
                    cursor.execute('''
                        INSERT INTO dashboard_widgets (
                            widget_id, dashboard_id, widget_name,
                            visualization_type, data_domain, config_json,
                            position_json, education_type, is_active, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ''', (widget_id, dashboard_id, widget_name, visualization_type,
                          data_domain, kwargs.get('config_json', '{}'),
                          kwargs.get('position_json', '{}'),
                          kwargs.get('education_type'), now))
                    conn.commit()
                    return {'success': True, 'widget_id': widget_id}
        except Exception as e:
            logger.error(f'添加仪表盘组件失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_report(self, dashboard_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM dashboards WHERE dashboard_id = ?', (dashboard_id,))
                dashboard = cursor.fetchone()
                if not dashboard:
                    return {'success': False, 'error': '仪表盘不存在'}
                cursor.execute('SELECT * FROM dashboard_widgets WHERE dashboard_id = ? AND is_active = 1', (dashboard_id,))
                widgets = [dict(w) for w in cursor.fetchall()]
                report = {
                    'report_id': f"rp_{uuid.uuid4().hex[:12]}",
                    'dashboard_id': dashboard_id,
                    'dashboard_name': dashboard['dashboard_name'],
                    'decision_level': dashboard['decision_level'],
                    'education_type': dashboard['education_type'],
                    'generated_at': now,
                    'widget_count': len(widgets),
                    'widgets': widgets,
                    'period': kwargs.get('period', 'monthly')
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成报表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM dashboards WHERE dashboard_id = ?', (dashboard_id,))
                dashboard = cursor.fetchone()
                if not dashboard:
                    return {'success': False, 'error': '仪表盘不存在'}
                cursor.execute('SELECT * FROM dashboard_widgets WHERE dashboard_id = ? AND is_active = 1', (dashboard_id,))
                widgets = [dict(w) for w in cursor.fetchall()]
                widget_data = []
                for widget in widgets:
                    domain_info = DATA_DOMAINS.get(widget['data_domain'], {})
                    vis_info = VISUALIZATION_TYPES.get(widget['visualization_type'], {})
                    widget_data.append({
                        'widget_id': widget['widget_id'],
                        'widget_name': widget['widget_name'],
                        'visualization_type': widget['visualization_type'],
                        'visualization_name': vis_info.get('name', ''),
                        'data_domain': widget['data_domain'],
                        'domain_name': domain_info.get('name', ''),
                        'config': json.loads(widget['config_json']),
                        'position': json.loads(widget['position_json']),
                        'mock_data': {
                            'labels': ['一月', '二月', '三月', '四月', '五月', '六月'],
                            'values': [120, 150, 180, 160, 200, 220],
                            'trend': 'up'
                        }
                    })
                return {'success': True, 'dashboard': dict(dashboard), 'widget_data': widget_data}
        except Exception as e:
            logger.error(f'获取仪表盘数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能推荐 ==========

    def generate_recommendation(self, user_id: int, user_type: str,
                                rec_type: str, **kwargs) -> Dict[str, Any]:
        try:
            rec_id = f"rc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT rule_name, rule_logic, weight FROM recommendation_rules WHERE rec_type = ? AND education_type = ? AND is_active = 1', (rec_type, education_type))
                    rules = cursor.fetchall()
                    rec_info = RECOMMENDATION_TYPES.get(rec_type, {})
                    items = []
                    if rec_type == 'course':
                        items = [{'id': 1, 'name': '高等数学', 'score': 0.92},
                                 {'id': 2, 'name': '英语四级', 'score': 0.88},
                                 {'id': 3, 'name': '计算机基础', 'score': 0.85}]
                    elif rec_type == 'learning_path':
                        items = [{'id': 1, 'name': '基础阶段', 'duration': '2个月'},
                                 {'id': 2, 'name': '进阶阶段', 'duration': '3个月'},
                                 {'id': 3, 'name': '提升阶段', 'duration': '2个月'}]
                    elif rec_type == 'teacher':
                        items = [{'id': 1, 'name': '张老师', 'subject': '数学', 'rating': 4.9},
                                 {'id': 2, 'name': '李老师', 'subject': '英语', 'rating': 4.8}]
                    elif rec_type == 'resource':
                        items = [{'id': 1, 'name': '教材', 'type': 'book'},
                                 {'id': 2, 'name': '在线课程', 'type': 'video'}]
                    reason = f'基于{rec_info.get("name", "")}规则生成'
                    cursor.execute('''
                        INSERT INTO recommendations (
                            rec_id, user_id, user_type, rec_type, education_type,
                            items_json, reason, confidence, is_viewed, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ''', (rec_id, user_id, user_type, rec_type, education_type,
                          json.dumps(items), reason, kwargs.get('confidence', 0.85), now))
                    conn.commit()
                    return {'success': True, 'rec_id': rec_id, 'items': items}
        except Exception as e:
            logger.error(f'生成推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_recommendation_rule(self, rec_type: str, rule_name: str,
                                rule_logic: str, **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"rr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO recommendation_rules (
                            rule_id, rec_type, education_type, rule_name,
                            rule_logic, weight, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (rule_id, rec_type, kwargs.get('education_type'),
                          rule_name, rule_logic, kwargs.get('weight', 1.0),
                          now, now))
                    conn.commit()
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'添加推荐规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_recommendations(self, user_id: int, rec_type: str = None,
                                 education_type: str = None, page: int = 1,
                                 page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM recommendations WHERE user_id = ?'
                params = [user_id]
                if rec_type:
                    query += ' AND rec_type = ?'
                    params.append(rec_type)
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

    def update_recommendation_viewed(self, rec_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE recommendations SET is_viewed = 1 WHERE rec_id = ?', (rec_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推荐记录不存在'}
        except Exception as e:
            logger.error(f'更新推荐状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预测预警 ==========

    def create_prediction(self, model_id: str, data_domain: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            pred_id = f"pr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT model_id FROM decision_models WHERE model_id = ?', (model_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '决策模型不存在'}
                    domain_info = DATA_DOMAINS.get(data_domain, {})
                    prediction_data = {
                        'data_domain': data_domain,
                        'domain_name': domain_info.get('name', ''),
                        'forecast_period': kwargs.get('forecast_period', 'next_month'),
                        'predictions': [],
                        'trend': 'stable'
                    }
                    cursor.execute('''
                        INSERT INTO prediction_results (
                            pred_id, model_id, data_domain, education_type,
                            prediction_json, confidence, forecast_period, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (pred_id, model_id, data_domain, kwargs.get('education_type'),
                          json.dumps(prediction_data), kwargs.get('confidence', 0.82),
                          kwargs.get('forecast_period', 'next_month'), now))
                    conn.commit()
                    return {'success': True, 'pred_id': pred_id}
        except Exception as e:
            logger.error(f'创建预测失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, alert_type: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"al_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            alert_info = ALERT_TYPES.get(alert_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO alert_records (
                            alert_id, alert_type, education_type, severity,
                            title, description, affected_objects, status,
                            trigger_time, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (alert_id, alert_type, kwargs.get('education_type'),
                          kwargs.get('severity', 'medium'), title,
                          kwargs.get('description'), kwargs.get('affected_objects', '[]'),
                          now, now))
                    conn.commit()
                    logger.warning(f'触发预警: {alert_info.get("name", "")} - {title} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id, 'alert_name': alert_info.get('name', '')}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE alert_records SET status = ?, acknowledged_at = ? WHERE alert_id = ? AND status = ?', ('acknowledged', now, alert_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警记录不存在或状态不允许确认'}
        except Exception as e:
            logger.error(f'确认预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE alert_records SET status = ?, resolved_at = ? WHERE alert_id = ?', ('resolved', now, alert_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警记录不存在'}
        except Exception as e:
            logger.error(f'解决预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_alerts(self, alert_type: str = None, severity: str = None,
                     status: str = None, education_type: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM alert_records WHERE 1=1'
                params = []
                if alert_type:
                    query += ' AND alert_type = ?'
                    params.append(alert_type)
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY trigger_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alert_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT alert_type, status, COUNT(*) as count FROM alert_records WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY alert_type, status'
                cursor.execute(query, params)
                rows = cursor.fetchall()
                summary = {'total_alerts': 0, 'pending': 0, 'acknowledged': 0, 'resolved': 0, 'by_type': {}}
                for row in rows:
                    alert_type = row['alert_type']
                    status = row['status']
                    count = row['count']
                    summary['total_alerts'] += count
                    summary[status] = summary.get(status, 0) + count
                    if alert_type not in summary['by_type']:
                        summary['by_type'][alert_type] = {'name': ALERT_TYPES.get(alert_type, {}).get('name', ''), 'count': 0, 'status': {}}
                    summary['by_type'][alert_type]['count'] += count
                    summary['by_type'][alert_type]['status'][status] = count
                return {'success': True, 'summary': summary}
        except Exception as e:
            logger.error(f'获取预警汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 绩效评估 ==========

    def create_performance_metric(self, metric_name: str, metric_type: str,
                                  data_domain: str, **kwargs) -> Dict[str, Any]:
        try:
            metric_id = f"pm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO performance_metrics (
                            metric_id, metric_name, metric_type, data_domain,
                            education_type, calculation_formula, target_value,
                            unit, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (metric_id, metric_name, metric_type, data_domain,
                          kwargs.get('education_type'), kwargs.get('calculation_formula'),
                          kwargs.get('target_value'), kwargs.get('unit'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建绩效指标: {metric_name} ({metric_id})')
                    return {'success': True, 'metric_id': metric_id}
        except Exception as e:
            logger.error(f'创建绩效指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_metric_data(self, metric_id: str, period: str,
                           actual_value: float, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"md_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT target_value FROM performance_metrics WHERE metric_id = ?', (metric_id,))
                    metric = cursor.fetchone()
                    if not metric:
                        return {'success': False, 'error': '绩效指标不存在'}
                    target_value = metric[0] or 0
                    score = min(actual_value / target_value * 100, 100) if target_value > 0 else 0
                    trend = 'up' if actual_value > target_value * 0.9 else ('down' if actual_value < target_value * 0.7 else 'stable')
                    cursor.execute('''
                        INSERT INTO metric_data (
                            data_id, metric_id, education_type, period,
                            actual_value, target_value, trend, score, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, metric_id, kwargs.get('education_type'), period,
                          actual_value, target_value, trend, round(score, 1), now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id, 'score': round(score, 1), 'trend': trend}
        except Exception as e:
            logger.error(f'记录指标数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_performance(self, metric_ids: List[str], period: str,
                              education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                placeholders = ','.join(['?'] * len(metric_ids))
                query = f'''
                    SELECT m.metric_id, m.metric_name, m.metric_type, m.data_domain,
                           md.actual_value, md.target_value, md.score, md.trend
                    FROM performance_metrics m
                    LEFT JOIN metric_data md ON m.metric_id = md.metric_id AND md.period = ?
                    WHERE m.metric_id IN ({placeholders})
                '''
                params = [period] + metric_ids
                if education_type:
                    query += ' AND m.education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                rows = [dict(r) for r in cursor.fetchall()]
                total_score = 0
                valid_count = 0
                for row in rows:
                    if row['score']:
                        total_score += row['score']
                        valid_count += 1
                avg_score = round(total_score / valid_count, 1) if valid_count > 0 else 0
                result = {
                    'calculation_id': f"pc_{uuid.uuid4().hex[:12]}",
                    'period': period,
                    'education_type': education_type,
                    'metrics_count': len(rows),
                    'valid_metrics': valid_count,
                    'average_score': avg_score,
                    'overall_level': 'excellent' if avg_score >= 90 else ('good' if avg_score >= 75 else ('medium' if avg_score >= 60 else 'poor')),
                    'details': rows
                }
                return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f'计算绩效失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_performance_report(self, education_type: str = None,
                                    period: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM performance_metrics WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                metrics = [dict(m) for m in cursor.fetchall()]
                metric_ids = [m['metric_id'] for m in metrics]
                metric_data = []
                if metric_ids:
                    placeholders = ','.join(['?'] * len(metric_ids))
                    data_query = f'SELECT * FROM metric_data WHERE metric_id IN ({placeholders})'
                    if period:
                        data_query += ' AND period = ?'
                        params_data = metric_ids + [period]
                    else:
                        data_query += ' ORDER BY period DESC LIMIT 1'
                        params_data = metric_ids
                    cursor.execute(data_query, params_data)
                    metric_data = [dict(d) for d in cursor.fetchall()]
                report = {
                    'report_id': f"prf_{uuid.uuid4().hex[:12]}",
                    'generated_at': now,
                    'education_type': education_type,
                    'period': period,
                    'metrics_count': len(metrics),
                    'data_count': len(metric_data),
                    'metrics': metrics,
                    'metric_data': metric_data,
                    'summary': f'绩效评估报告，共{len(metrics)}个指标，{len(metric_data)}条数据'
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成绩效报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 决策日志 ==========

    def record_decision_log(self, decision_type: str, action: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"dl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_logs (
                            log_id, decision_type, education_type, decision_level,
                            user_id, user_name, action, details_json, result, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, decision_type, kwargs.get('education_type'),
                          kwargs.get('decision_level'), kwargs.get('user_id'),
                          kwargs.get('user_name'), action, kwargs.get('details_json', '{}'),
                          kwargs.get('result', 'success'), now))
                    conn.commit()
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'记录决策日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_decision_logs(self, decision_type: str = None, user_id: int = None,
                            education_type: str = None, decision_level: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM decision_logs WHERE 1=1'
                params = []
                if decision_type:
                    query += ' AND decision_type = ?'
                    params.append(decision_type)
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if decision_level:
                    query += ' AND decision_level = ?'
                    params.append(decision_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询决策日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_decision_audit(self, decision_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM decision_logs WHERE details_json LIKE ?'
                params = [f'%{decision_id}%']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at'
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                audit = {
                    'decision_id': decision_id,
                    'audit_count': len(logs),
                    'timeline': []
                }
                for log in logs:
                    audit['timeline'].append({
                        'time': log['created_at'],
                        'action': log['action'],
                        'user': log['user_name'],
                        'result': log['result']
                    })
                return {'success': True, 'audit': audit}
        except Exception as e:
            logger.error(f'获取决策审计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 反馈管理 ==========

    def submit_decision_feedback(self, decision_id: str, user_id: int,
                                  rating: int, **kwargs) -> Dict[str, Any]:
        try:
            feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_feedback (
                            feedback_id, decision_id, education_type, user_id,
                            user_name, rating, comment, improvement_suggestions, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (feedback_id, decision_id, kwargs.get('education_type'),
                          user_id, kwargs.get('user_name'), rating,
                          kwargs.get('comment'), kwargs.get('improvement_suggestions'), now))
                    conn.commit()
                    return {'success': True, 'feedback_id': feedback_id}
        except Exception as e:
            logger.error(f'提交决策反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_decision_feedback(self, decision_id: str = None, user_id: int = None,
                                education_type: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM decision_feedback WHERE 1=1'
                params = []
                if decision_id:
                    query += ' AND decision_id = ?'
                    params.append(decision_id)
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                feedbacks = [dict(f) for f in cursor.fetchall()]
                return {'success': True, 'feedbacks': feedbacks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询决策反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_feedback(self, decision_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT rating, COUNT(*) as count FROM decision_feedback WHERE 1=1'
                params = []
                if decision_id:
                    query += ' AND decision_id = ?'
                    params.append(decision_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY rating'
                cursor.execute(query, params)
                rows = cursor.fetchall()
                total_count = sum(r['count'] for r in rows)
                avg_rating = sum(r['rating'] * r['count'] for r in rows) / total_count if total_count > 0 else 0
                rating_dist = {}
                for row in rows:
                    rating_dist[row['rating']] = row['count']
                query_comments = 'SELECT comment FROM decision_feedback WHERE 1=1 AND comment IS NOT NULL AND comment != ""'
                params_comments = []
                if decision_id:
                    query_comments += ' AND decision_id = ?'
                    params_comments.append(decision_id)
                if education_type:
                    query_comments += ' AND education_type = ?'
                    params_comments.append(education_type)
                cursor.execute(query_comments, params_comments)
                comments = [c['comment'] for c in cursor.fetchall()]
                analysis = {
                    'analysis_id': f"fa_{uuid.uuid4().hex[:12]}",
                    'total_feedback': total_count,
                    'average_rating': round(avg_rating, 1),
                    'rating_distribution': rating_dist,
                    'positive_count': rating_dist.get(5, 0) + rating_dist.get(4, 0),
                    'negative_count': rating_dist.get(1, 0) + rating_dist.get(2, 0),
                    'comment_count': len(comments),
                    'summary': f'共收到{total_count}条反馈，平均评分{round(avg_rating, 1)}分'
                }
                return {'success': True, 'analysis': analysis}
        except Exception as e:
            logger.error(f'分析反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_comprehensive_statistics(self, education_type: str = None, period: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            statistics = {
                'statistics_id': f"stat_{uuid.uuid4().hex[:12]}",
                'generated_at': now,
                'education_type': education_type,
                'period': period,
                'decision_models': 0,
                'analysis_tasks': 0,
                'completed_analyses': 0,
                'active_alerts': 0,
                'performance_metrics': 0,
                'recommendations': 0,
                'knowledge_graphs': 0,
                'dashboards': 0,
                'decision_logs': 0,
                'feedback_count': 0
            }
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM decision_models WHERE status = ?', ('active',))
                statistics['decision_models'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM analysis_tasks')
                statistics['analysis_tasks'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM analysis_results')
                statistics['completed_analyses'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM alert_records WHERE status != ?', ('resolved',))
                statistics['active_alerts'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM performance_metrics WHERE status = ?', ('active',))
                statistics['performance_metrics'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM recommendations')
                statistics['recommendations'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM knowledge_graph WHERE status = ?', ('active',))
                statistics['knowledge_graphs'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM dashboards WHERE status = ?', ('active',))
                statistics['dashboards'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM decision_logs')
                statistics['decision_logs'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM decision_feedback')
                statistics['feedback_count'] = cursor.fetchone()[0]
            return {'success': True, 'statistics': statistics}
        except Exception as e:
            logger.error(f'获取综合统计失败: {e}')
            return {'success': False, 'error': str(e)}
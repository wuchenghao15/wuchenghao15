#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育数字孪生服务 (v15.21.0)
====================================
提供教育领域数字孪生建模、虚拟仿真、实时同步、预测分析、优化决策、可视化展示、交互操作、智能控制等综合服务。

核心能力：
1. 数字孪生建模 - 校园/教室/实验室/学生/教师/教学/管理/设施孪生
2. 虚拟仿真 - 实时/离线/混合/事件/过程/系统/优化/决策仿真
3. 实时同步 - 实时/定时/事件触发/增量/全量/双向/异步/延迟同步
4. 预测分析 - 趋势/预测/优化/风险/决策/效能/对比/综合分析
5. 可视化展示 - 3D/2D/仪表盘/热力图/流程图/时序图/对比图/全息投影
6. 交互操作 - 漫游/操作/查询/编辑/协作/控制/反馈/沉浸式交互
7. 智能控制 - 智能/自动/手动/远程/协同/优化/应急/自适应控制
8. 预警管理 - 实时监测、预警触发、处置跟踪

支持教育类型：成人教育、K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_digital_twin_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationDigitalTwin')


# ========== 数字孪生配置 ==========

TWIN_TYPES = {
    'campus': {'name': '校园孪生', 'description': '校园整体环境与设施的数字映射', 'education_type': ['adult', 'k12']},
    'classroom': {'name': '教室孪生', 'description': '教室空间与教学设备的数字映射', 'education_type': ['adult', 'k12']},
    'laboratory': {'name': '实验室孪生', 'description': '实验室设备与实验环境的数字映射', 'education_type': ['adult', 'k12']},
    'student': {'name': '学生孪生', 'description': '学生学习状态与行为的数字映射', 'education_type': ['adult', 'k12']},
    'teacher': {'name': '教师孪生', 'description': '教师教学行为与能力的数字映射', 'education_type': ['adult', 'k12']},
    'teaching': {'name': '教学孪生', 'description': '教学过程与资源的数字映射', 'education_type': ['adult', 'k12']},
    'management': {'name': '管理孪生', 'description': '教育管理流程与数据的数字映射', 'education_type': ['adult', 'k12']},
    'facility': {'name': '设施孪生', 'description': '教育设施运行状态的数字映射', 'education_type': ['adult', 'k12']}
}

MODEL_TYPES = {
    'physical': {'name': '物理模型', 'description': '实体对象的几何与物理属性模型'},
    'digital': {'name': '数字模型', 'description': '实体对象的数字化表达模型'},
    'behavior': {'name': '行为模型', 'description': '实体对象行为规律的建模'},
    'process': {'name': '过程模型', 'description': '业务流程的建模与仿真'},
    'system': {'name': '系统模型', 'description': '复杂系统的整体建模'},
    'decision': {'name': '决策模型', 'description': '决策支持的模型化表达'},
    'prediction': {'name': '预测模型', 'description': '基于历史数据的预测模型'},
    'optimization': {'name': '优化模型', 'description': '资源优化与配置模型'}
}

SIMULATION_TYPES = {
    'realtime': {'name': '实时仿真', 'description': '与现实世界同步的仿真'},
    'offline': {'name': '离线仿真', 'description': '脱离实时数据的仿真分析'},
    'hybrid': {'name': '混合仿真', 'description': '实时与离线结合的仿真'},
    'event': {'name': '事件仿真', 'description': '基于事件驱动的仿真'},
    'process': {'name': '过程仿真', 'description': '业务流程的仿真'},
    'system': {'name': '系统仿真', 'description': '复杂系统的整体仿真'},
    'optimization': {'name': '优化仿真', 'description': '优化目标导向的仿真'},
    'decision': {'name': '决策仿真', 'description': '决策方案的仿真验证'}
}

SYNC_METHODS = {
    'realtime': {'name': '实时同步', 'description': '数据实时更新同步'},
    'periodic': {'name': '定时同步', 'description': '按固定周期同步'},
    'event_triggered': {'name': '事件触发', 'description': '基于事件触发同步'},
    'incremental': {'name': '增量同步', 'description': '仅同步变化数据'},
    'full': {'name': '全量同步', 'description': '全部数据同步'},
    'bidirectional': {'name': '双向同步', 'description': '双向数据同步'},
    'asynchronous': {'name': '异步同步', 'description': '异步方式同步'},
    'delayed': {'name': '延迟同步', 'description': '延迟一定时间后同步'}
}

ANALYSIS_METHODS = {
    'trend': {'name': '趋势分析', 'description': '数据趋势的分析预测'},
    'prediction': {'name': '预测分析', 'description': '基于模型的预测'},
    'optimization': {'name': '优化分析', 'description': '最优解的分析'},
    'risk': {'name': '风险分析', 'description': '风险识别与评估'},
    'decision': {'name': '决策分析', 'description': '决策方案的分析'},
    'efficiency': {'name': '效能分析', 'description': '效率与效益分析'},
    'comparative': {'name': '对比分析', 'description': '多维度对比分析'},
    'comprehensive': {'name': '综合分析', 'description': '多方法综合分析'}
}

VISUALIZATION_TYPES = {
    '3d': {'name': '3D可视化', 'description': '三维场景可视化展示'},
    '2d': {'name': '2D可视化', 'description': '二维图表可视化展示'},
    'dashboard': {'name': '仪表盘', 'description': '数据指标仪表盘'},
    'heatmap': {'name': '热力图', 'description': '数据分布热力图'},
    'flowchart': {'name': '流程图', 'description': '业务流程可视化'},
    'timeline': {'name': '时序图', 'description': '时间序列可视化'},
    'comparison': {'name': '对比图', 'description': '数据对比可视化'},
    'holographic': {'name': '全息投影', 'description': '全息投影展示'}
}

INTERACTION_TYPES = {
    'navigation': {'name': '漫游交互', 'description': '场景漫游与浏览'},
    'operation': {'name': '操作交互', 'description': '对象操作与控制'},
    'query': {'name': '查询交互', 'description': '信息查询与检索'},
    'edit': {'name': '编辑交互', 'description': '对象编辑与修改'},
    'collaboration': {'name': '协作交互', 'description': '多人协作交互'},
    'control': {'name': '控制交互', 'description': '系统控制交互'},
    'feedback': {'name': '反馈交互', 'description': '用户反馈交互'},
    'immersive': {'name': '沉浸式交互', 'description': '沉浸式体验交互'}
}

CONTROL_FUNCTIONS = {
    'smart': {'name': '智能控制', 'description': '基于AI的智能控制'},
    'automatic': {'name': '自动控制', 'description': '自动化控制'},
    'manual': {'name': '手动控制', 'description': '人工手动控制'},
    'remote': {'name': '远程控制', 'description': '远程操作控制'},
    'collaborative': {'name': '协同控制', 'description': '多系统协同控制'},
    'optimization': {'name': '优化控制', 'description': '优化目标控制'},
    'emergency': {'name': '应急控制', 'description': '应急场景控制'},
    'adaptive': {'name': '自适应控制', 'description': '自适应调节控制'}
}


class EducationDigitalTwinService:
    """教育数字孪生服务"""

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
                    CREATE TABLE IF NOT EXISTS digital_twins (
                        twin_id TEXT PRIMARY KEY,
                        twin_name TEXT NOT NULL,
                        twin_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS twin_models (
                        model_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        model_name TEXT NOT NULL,
                        model_data TEXT,
                        version TEXT DEFAULT '1.0',
                        status TEXT DEFAULT 'ready',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS twin_instances (
                        instance_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        instance_name TEXT NOT NULL,
                        instance_data TEXT,
                        status TEXT DEFAULT 'running',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id),
                        FOREIGN KEY(model_id) REFERENCES twin_models(model_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS instance_data (
                        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        instance_id TEXT NOT NULL,
                        data_key TEXT NOT NULL,
                        data_value TEXT,
                        data_type TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(instance_id) REFERENCES twin_instances(instance_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS simulation_runs (
                        run_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        simulation_type TEXT NOT NULL,
                        run_name TEXT NOT NULL,
                        parameters TEXT,
                        status TEXT DEFAULT 'pending',
                        start_time TEXT,
                        end_time TEXT,
                        created_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS simulation_results (
                        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT NOT NULL,
                        result_data TEXT,
                        metrics TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(run_id) REFERENCES simulation_runs(run_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS realtime_sync (
                        sync_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        sync_method TEXT NOT NULL,
                        source TEXT,
                        target TEXT,
                        sync_interval INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'running',
                        created_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sync_id TEXT NOT NULL,
                        sync_type TEXT,
                        sync_status TEXT,
                        records_count INTEGER DEFAULT 0,
                        duration_ms INTEGER DEFAULT 0,
                        error_message TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(sync_id) REFERENCES realtime_sync(sync_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_tasks (
                        task_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        analysis_method TEXT NOT NULL,
                        task_name TEXT NOT NULL,
                        parameters TEXT,
                        status TEXT DEFAULT 'pending',
                        priority INTEGER DEFAULT 1,
                        created_at TEXT,
                        completed_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        result_data TEXT,
                        summary TEXT,
                        confidence REAL DEFAULT 0,
                        timestamp TEXT,
                        FOREIGN KEY(task_id) REFERENCES analysis_tasks(task_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS visualization_config (
                        config_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        visualization_type TEXT NOT NULL,
                        config_name TEXT NOT NULL,
                        config_data TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS visual_data (
                        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_id TEXT NOT NULL,
                        data_content TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(config_id) REFERENCES visualization_config(config_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interaction_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        twin_id TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        action_data TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interaction_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        record_id INTEGER NOT NULL,
                        log_type TEXT,
                        log_content TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(record_id) REFERENCES interaction_records(record_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_control (
                        control_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        control_function TEXT NOT NULL,
                        control_name TEXT NOT NULL,
                        parameters TEXT,
                        status TEXT DEFAULT 'enabled',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS control_actions (
                        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        control_id TEXT NOT NULL,
                        action_type TEXT,
                        action_data TEXT,
                        result TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(control_id) REFERENCES smart_control(control_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS twin_metrics (
                        metric_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_type TEXT,
                        unit TEXT,
                        threshold_min REAL,
                        threshold_max REAL,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metric_data (
                        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_id TEXT NOT NULL,
                        value REAL,
                        timestamp TEXT,
                        FOREIGN KEY(metric_id) REFERENCES twin_metrics(metric_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS twin_alerts (
                        alert_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        metric_id TEXT,
                        alert_level TEXT DEFAULT 'warning',
                        alert_message TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY(twin_id) REFERENCES digital_twins(twin_id),
                        FOREIGN KEY(metric_id) REFERENCES twin_metrics(metric_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        action TEXT,
                        action_by TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(alert_id) REFERENCES twin_alerts(alert_id)
                    )
                ''')
                conn.commit()
                logger.info('教育数字孪生服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 数字孪生 ==========

    def create_twin(self, twin_name: str, twin_type: str,
                    education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            if twin_type not in TWIN_TYPES:
                return {'success': False, 'error': '无效的孪生类型'}
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '无效的教育类型'}
            twin_id = f"twn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO digital_twins (
                            twin_id, twin_name, twin_type, education_type,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (twin_id, twin_name, twin_type, education_type,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建数字孪生: {twin_name} ({twin_id})')
                    return {'success': True, 'twin_id': twin_id}
        except Exception as e:
            logger.error(f'创建数字孪生失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_twin(self, twin_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM digital_twins WHERE twin_id = ?', (twin_id,))
                twin = cursor.fetchone()
                if not twin:
                    return {'success': False, 'error': '孪生不存在'}
                return {'success': True, 'twin': dict(twin)}
        except Exception as e:
            logger.error(f'获取孪生失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_twin(self, twin_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            update_fields = []
            params = []
            for key, value in kwargs.items():
                if key in ['twin_name', 'description', 'status']:
                    update_fields.append(f'{key} = ?')
                    params.append(value)
            if not update_fields:
                return {'success': False, 'error': '没有可更新的字段'}
            params.extend([now, twin_id])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE digital_twins SET {", ".join(update_fields)}, updated_at = ? WHERE twin_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '孪生不存在'}
        except Exception as e:
            logger.error(f'更新孪生失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_twin(self, twin_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '孪生不存在'}
        except Exception as e:
            logger.error(f'删除孪生失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 虚拟仿真 ==========

    def create_simulation(self, twin_id: str, simulation_type: str,
                          run_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if simulation_type not in SIMULATION_TYPES:
                return {'success': False, 'error': '无效的仿真类型'}
            run_id = f"sim_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO simulation_runs (
                            run_id, twin_id, simulation_type, run_name,
                            parameters, status, start_time, end_time, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', NULL, NULL, ?)
                    ''', (run_id, twin_id, simulation_type, run_name,
                          json.dumps(kwargs.get('parameters', {})), now))
                    conn.commit()
                    logger.info(f'创建仿真运行: {run_name} ({run_id})')
                    return {'success': True, 'run_id': run_id}
        except Exception as e:
            logger.error(f'创建仿真失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_simulation(self, run_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE simulation_runs SET status = ?, start_time = ? WHERE run_id = ? AND status = ?',
                                 ('running', now, run_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '仿真状态不允许启动'}
        except Exception as e:
            logger.error(f'启动仿真失败: {e}')
            return {'success': False, 'error': str(e)}

    def stop_simulation(self, run_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE simulation_runs SET status = ?, end_time = ? WHERE run_id = ? AND status = ?',
                                 ('completed', now, run_id, 'running'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '仿真状态不允许停止'}
        except Exception as e:
            logger.error(f'停止仿真失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_simulation_results(self, run_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM simulation_results WHERE run_id = ? ORDER BY timestamp DESC', (run_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'获取仿真结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实时同步 ==========

    def create_sync(self, twin_id: str, sync_method: str,
                    source: str, target: str, **kwargs) -> Dict[str, Any]:
        try:
            if sync_method not in SYNC_METHODS:
                return {'success': False, 'error': '无效的同步方法'}
            sync_id = f"sync_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO realtime_sync (
                            sync_id, twin_id, sync_method, source,
                            target, sync_interval, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'running', ?)
                    ''', (sync_id, twin_id, sync_method, source, target,
                          kwargs.get('sync_interval', 0), now))
                    conn.commit()
                    logger.info(f'创建同步任务: {sync_id}')
                    return {'success': True, 'sync_id': sync_id}
        except Exception as e:
            logger.error(f'创建同步任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_sync(self, sync_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT sync_method FROM realtime_sync WHERE sync_id = ? AND status = ?',
                                 (sync_id, 'running'))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '同步任务不存在或已停止'}
                    cursor.execute('''
                        INSERT INTO sync_logs (sync_id, sync_type, sync_status, records_count, duration_ms, timestamp)
                        VALUES (?, ?, 'success', ?, ?, ?)
                    ''', (sync_id, 'manual', 0, 0, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'触发同步失败: {e}')
            return {'success': False, 'error': str(e)}

    def pause_sync(self, sync_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE realtime_sync SET status = ? WHERE sync_id = ? AND status = ?',
                                 ('paused', sync_id, 'running'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '同步任务状态不允许暂停'}
        except Exception as e:
            logger.error(f'暂停同步失败: {e}')
            return {'success': False, 'error': str(e)}

    def resume_sync(self, sync_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE realtime_sync SET status = ? WHERE sync_id = ? AND status = ?',
                                 ('running', sync_id, 'paused'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '同步任务状态不允许恢复'}
        except Exception as e:
            logger.error(f'恢复同步失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预测分析 ==========

    def create_analysis_task(self, twin_id: str, analysis_method: str,
                             task_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if analysis_method not in ANALYSIS_METHODS:
                return {'success': False, 'error': '无效的分析方法'}
            task_id = f"ans_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO analysis_tasks (
                            task_id, twin_id, analysis_method, task_name,
                            parameters, status, priority, created_at, completed_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL)
                    ''', (task_id, twin_id, analysis_method, task_name,
                          json.dumps(kwargs.get('parameters', {})),
                          kwargs.get('priority', 1), now))
                    conn.commit()
                    logger.info(f'创建分析任务: {task_name} ({task_id})')
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
                    cursor.execute('UPDATE analysis_tasks SET status = ? WHERE task_id = ? AND status = ?',
                                 ('running', task_id, 'pending'))
                    if cursor.rowcount == 0:
                        return {'success': False, 'error': '任务状态不允许执行'}
                    cursor.execute('''
                        INSERT INTO analysis_results (task_id, result_data, summary, confidence, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (task_id, json.dumps({}), '分析完成', 0.85, now))
                    cursor.execute('UPDATE analysis_tasks SET status = ?, completed_at = ? WHERE task_id = ?',
                                 ('completed', now, task_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'执行分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_result(self, task_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM analysis_results WHERE task_id = ? ORDER BY timestamp DESC LIMIT 1', (task_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '分析结果不存在'}
                return {'success': True, 'result': dict(result)}
        except Exception as e:
            logger.error(f'获取分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_analysis_task(self, task_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE analysis_tasks SET status = ? WHERE task_id = ? AND status = ?',
                                 ('cancelled', task_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '任务状态不允许取消'}
        except Exception as e:
            logger.error(f'取消分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_analysis_tasks(self, twin_id: str = None, status: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM analysis_tasks WHERE 1=1'
                params = []
                if twin_id:
                    query += ' AND twin_id = ?'
                    params.append(twin_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取分析任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 可视化 ==========

    def create_visualization(self, twin_id: str, visualization_type: str,
                             config_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if visualization_type not in VISUALIZATION_TYPES:
                return {'success': False, 'error': '无效的可视化类型'}
            config_id = f"vis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO visualization_config (
                            config_id, twin_id, visualization_type, config_name,
                            config_data, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (config_id, twin_id, visualization_type, config_name,
                          json.dumps(kwargs.get('config_data', {})), now, now))
                    conn.commit()
                    logger.info(f'创建可视化配置: {config_name} ({config_id})')
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'创建可视化配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_visualization(self, config_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            update_fields = []
            params = []
            for key, value in kwargs.items():
                if key in ['config_name', 'config_data', 'status']:
                    update_fields.append(f'{key} = ?')
                    params.append(json.dumps(value) if key == 'config_data' else value)
            if not update_fields:
                return {'success': False, 'error': '没有可更新的字段'}
            params.extend([now, config_id])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE visualization_config SET {", ".join(update_fields)}, updated_at = ? WHERE config_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '可视化配置不存在'}
        except Exception as e:
            logger.error(f'更新可视化配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_visual_data(self, config_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM visual_data WHERE config_id = ? ORDER BY timestamp DESC LIMIT 1', (config_id,))
                data = cursor.fetchone()
                if not data:
                    return {'success': False, 'error': '可视化数据不存在'}
                return {'success': True, 'data': dict(data)}
        except Exception as e:
            logger.error(f'获取可视化数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def push_visual_data(self, config_id: str, data_content: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT config_id FROM visualization_config WHERE config_id = ? AND status = ?',
                                 (config_id, 'active'))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '可视化配置不存在或未激活'}
                    cursor.execute('''
                        INSERT INTO visual_data (config_id, data_content, timestamp)
                        VALUES (?, ?, ?)
                    ''', (config_id, json.dumps(data_content), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'推送可视化数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 交互操作 ==========

    def record_interaction(self, twin_id: str, interaction_type: str,
                           user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            if interaction_type not in INTERACTION_TYPES:
                return {'success': False, 'error': '无效的交互类型'}
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO interaction_records (
                            twin_id, interaction_type, user_id, user_name,
                            action_data, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (twin_id, interaction_type, user_id,
                          kwargs.get('user_name'),
                          json.dumps(kwargs.get('action_data', {})), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录交互失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_interaction_history(self, twin_id: str, interaction_type: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM interaction_records WHERE twin_id = ?'
                params = [twin_id]
                if interaction_type:
                    query += ' AND interaction_type = ?'
                    params.append(interaction_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取交互历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_collaborative_session(self, twin_id: str, session_name: str,
                                     **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"cls_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO interaction_records (
                            twin_id, interaction_type, user_id, user_name,
                            action_data, timestamp
                        ) VALUES (?, 'collaboration', ?, ?, ?, ?)
                    ''', (twin_id, kwargs.get('user_id', 0), kwargs.get('user_name'),
                          json.dumps({'session_id': session_id, 'session_name': session_name, 'participants': []}), now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'创建协作会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_interaction(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO interaction_logs (record_id, log_type, log_content, timestamp)
                        VALUES (?, 'end', '交互结束', ?)
                    ''', (record_id, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'结束交互失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能控制 ==========

    def create_control(self, twin_id: str, control_function: str,
                       control_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if control_function not in CONTROL_FUNCTIONS:
                return {'success': False, 'error': '无效的控制功能'}
            control_id = f"ctl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO smart_control (
                            control_id, twin_id, control_function, control_name,
                            parameters, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'enabled', ?, ?)
                    ''', (control_id, twin_id, control_function, control_name,
                          json.dumps(kwargs.get('parameters', {})), now, now))
                    conn.commit()
                    logger.info(f'创建智能控制: {control_name} ({control_id})')
                    return {'success': True, 'control_id': control_id}
        except Exception as e:
            logger.error(f'创建智能控制失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_control_action(self, control_id: str, action_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT control_id FROM smart_control WHERE control_id = ? AND status = ?',
                                 (control_id, 'enabled'))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '控制不存在或已禁用'}
                    cursor.execute('''
                        INSERT INTO control_actions (control_id, action_type, action_data, result, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (control_id, action_type, json.dumps(kwargs.get('action_data', {})),
                          'success', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'执行控制动作失败: {e}')
            return {'success': False, 'error': str(e)}

    def enable_control(self, control_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE smart_control SET status = ? WHERE control_id = ?',
                                 ('enabled', control_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '控制不存在'}
        except Exception as e:
            logger.error(f'启用控制失败: {e}')
            return {'success': False, 'error': str(e)}

    def disable_control(self, control_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE smart_control SET status = ? WHERE control_id = ?',
                                 ('disabled', control_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '控制不存在'}
        except Exception as e:
            logger.error(f'禁用控制失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 孪生指标 ==========

    def create_metric(self, twin_id: str, metric_name: str,
                      metric_type: str = 'numeric', **kwargs) -> Dict[str, Any]:
        try:
            metric_id = f"met_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO twin_metrics (
                            metric_id, twin_id, metric_name, metric_type,
                            unit, threshold_min, threshold_max, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (metric_id, twin_id, metric_name, metric_type,
                          kwargs.get('unit'), kwargs.get('threshold_min'),
                          kwargs.get('threshold_max'), now))
                    conn.commit()
                    logger.info(f'创建孪生指标: {metric_name} ({metric_id})')
                    return {'success': True, 'metric_id': metric_id}
        except Exception as e:
            logger.error(f'创建孪生指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_metric_data(self, metric_id: str, value: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT metric_id FROM twin_metrics WHERE metric_id = ? AND status = ?',
                                 (metric_id, 'active'))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '指标不存在或未激活'}
                    cursor.execute('''
                        INSERT INTO metric_data (metric_id, value, timestamp)
                        VALUES (?, ?, ?)
                    ''', (metric_id, value, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录指标数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_metric_history(self, metric_id: str, start_time: str = None,
                           end_time: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM metric_data WHERE metric_id = ?'
                params = [metric_id]
                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time)
                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time)
                query += ' ORDER BY timestamp DESC'
                cursor.execute(query, params)
                data = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'data': data}
        except Exception as e:
            logger.error(f'获取指标历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_metric_stats(self, metric_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT AVG(value), MIN(value), MAX(value), COUNT(*) FROM metric_data WHERE metric_id = ?', (metric_id,))
                stats = cursor.fetchone()
                return {
                    'success': True,
                    'avg': stats[0] or 0,
                    'min': stats[1] or 0,
                    'max': stats[2] or 0,
                    'count': stats[3] or 0
                }
        except Exception as e:
            logger.error(f'获取指标统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert(self, twin_id: str, alert_level: str = 'warning',
                     **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT twin_id FROM digital_twins WHERE twin_id = ?', (twin_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '孪生不存在'}
                    cursor.execute('''
                        INSERT INTO twin_alerts (
                            alert_id, twin_id, metric_id, alert_level,
                            alert_message, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?)
                    ''', (alert_id, twin_id, kwargs.get('metric_id'), alert_level,
                          kwargs.get('alert_message', '预警触发'), now))
                    conn.commit()
                    logger.info(f'创建预警: {alert_id}')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: str, action_by: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE twin_alerts SET status = ? WHERE alert_id = ? AND status = ?',
                                 ('acknowledged', alert_id, 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO alert_history (alert_id, action, action_by, timestamp)
                            VALUES (?, 'acknowledge', ?, ?)
                        ''', (alert_id, action_by, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在或已处理'}
        except Exception as e:
            logger.error(f'确认预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, action_by: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE twin_alerts SET status = ? WHERE alert_id = ? AND status != ?',
                                 ('resolved', alert_id, 'resolved'))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO alert_history (alert_id, action, action_by, timestamp)
                            VALUES (?, 'resolve', ?, ?)
                        ''', (alert_id, action_by, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在或已解决'}
        except Exception as e:
            logger.error(f'解决预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_active_alerts(self, twin_id: str = None, alert_level: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM twin_alerts WHERE status = ?'
                params = ['active']
                if twin_id:
                    query += ' AND twin_id = ?'
                    params.append(twin_id)
                if alert_level:
                    query += ' AND alert_level = ?'
                    params.append(alert_level)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts}
        except Exception as e:
            logger.error(f'获取活跃预警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_twin_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM digital_twins WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                total_twins = cursor.fetchone()[0]

                query = 'SELECT twin_type, COUNT(*) as cnt FROM digital_twins WHERE 1=1'
                if education_type:
                    query += ' AND education_type = ?'
                    params = [education_type]
                else:
                    params = []
                query += ' GROUP BY twin_type'
                cursor.execute(query, params)
                type_stats = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute('SELECT COUNT(*) FROM simulation_runs WHERE status = ?', ('completed',))
                completed_simulations = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM analysis_tasks WHERE status = ?', ('completed',))
                completed_analyses = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM twin_alerts WHERE status = ?', ('active',))
                active_alerts = cursor.fetchone()[0]

                return {
                    'success': True,
                    'statistics': {
                        'total_twins': total_twins,
                        'type_distribution': type_stats,
                        'completed_simulations': completed_simulations,
                        'completed_analyses': completed_analyses,
                        'active_alerts': active_alerts
                    }
                }
        except Exception as e:
            logger.error(f'获取孪生统计失败: {e}')
            return {'success': False, 'error': str(e)}
#!/usr/bin/env python3
"""
MTSCOS AI 实验追踪服务 (v14.9.0)
===================================
AI 实验管理和超参数追踪服务。

核心能力：
1. 实验管理 - 创建/运行/对比实验
2. 超参数追踪 - 参数记录和版本管理
3. 指标记录 - 训练指标实时记录和可视化
4. 超参搜索 - 网格搜索/随机搜索/贝叶斯优化
5. 实验对比 - 多实验指标对比和统计
6. 模型注册 - 模型版本和工件管理
7. 实验报告 - 综合实验报告生成
8. 协作管理 - 实验标签和备注
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict, deque

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_experiment.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIExperimentTracker')


# ========== 超参数搜索 ==========

def grid_search(param_grid: Dict[str, List]) -> List[Dict]:
    """网格搜索生成所有参数组合"""
    if not param_grid:
        return [{}]

    keys = list(param_grid.keys())
    values = list(param_grid.values())

    combinations = []
    def _generate(idx: int, current: Dict):
        if idx == len(keys):
            combinations.append(dict(current))
            return
        for val in values[idx]:
            current[keys[idx]] = val
            _generate(idx + 1, current)

    _generate(0, {})
    return combinations


def random_search(param_space: Dict[str, Tuple], n_trials: int = 20) -> List[Dict]:
    """随机搜索"""
    results = []
    for _ in range(n_trials):
        params = {}
        for key, (low, high) in param_space.items():
            if isinstance(low, int) and isinstance(high, int):
                params[key] = random.randint(low, high)
            else:
                params[key] = round(random.uniform(low, high), 6)
        results.append(params)
    return results


def bayesian_optimization_suggest(param_space: Dict[str, Tuple],
                                  history: List[Dict],
                                  n_suggestions: int = 1) -> List[Dict]:
    """贝叶斯优化简化版（基于EI近似）"""
    if not history:
        # 无历史时随机采样
        return random_search(param_space, n_suggestions)

    # 找到最佳历史参数
    best_score = max(h.get('score', 0) for h in history)
    best_params = max(history, key=lambda h: h.get('score', 0)).get('params', {})

    suggestions = []
    for _ in range(n_suggestions):
        # 在最佳参数附近扰动
        params = {}
        for key, (low, high) in param_space.items():
            if key in best_params:
                center = best_params[key]
                # 在最佳值附近高斯采样
                scale = (high - low) * 0.2
                val = center + random.gauss(0, scale)
                val = max(low, min(high, val))
                if isinstance(low, int):
                    val = int(val)
                params[key] = val
            else:
                if isinstance(low, int):
                    params[key] = random.randint(low, high)
                else:
                    params[key] = round(random.uniform(low, high), 6)
        suggestions.append(params)

    return suggestions


# ========== 实验追踪服务 ==========

class AIExperimentTracker:
    """AI 实验追踪服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiments (
                        experiment_id TEXT PRIMARY KEY,
                        experiment_name TEXT NOT NULL,
                        project_name TEXT DEFAULT 'default',
                        status TEXT DEFAULT 'created',
                        hyperparameters TEXT,
                        metrics TEXT,
                        tags TEXT,
                        notes TEXT,
                        parent_id TEXT,
                        model_artifact TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration_sec REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiment_metrics_log (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        experiment_id TEXT NOT NULL,
                        step INTEGER,
                        metric_name TEXT,
                        metric_value REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS model_registry (
                        model_id TEXT PRIMARY KEY,
                        model_name TEXT NOT NULL,
                        version TEXT,
                        experiment_id TEXT,
                        metrics TEXT,
                        artifact_path TEXT,
                        status TEXT DEFAULT 'registered',
                        tags TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS hyperparameter_searches (
                        search_id TEXT PRIMARY KEY,
                        search_name TEXT,
                        method TEXT,
                        param_space TEXT,
                        n_trials INTEGER,
                        best_score REAL,
                        best_params TEXT,
                        status TEXT DEFAULT 'running',
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_exp_project ON experiments(project_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric_exp ON experiment_metrics_log(experiment_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化实验追踪数据库失败: {e}")

    # ========== 实验管理 ==========

    def create_experiment(self, experiment_name: str,
                         project_name: str = 'default',
                         hyperparameters: Dict = None,
                         tags: List[str] = None,
                         parent_id: str = None,
                         notes: str = '') -> Dict:
        """创建实验"""
        exp_id = f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO experiments
                    (experiment_id, experiment_name, project_name, status,
                     hyperparameters, metrics, tags, notes, parent_id,
                     start_time, created_at)
                    VALUES (?, ?, ?, 'running', ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    exp_id, experiment_name, project_name,
                    json.dumps(hyperparameters or {}, ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False),
                    json.dumps(tags or [], ensure_ascii=False),
                    notes, parent_id,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        logger.info(f"创建实验: {exp_id} ({experiment_name})")
        return {'success': True, 'experiment_id': exp_id}

    def log_metric(self, experiment_id: str, metric_name: str,
                  metric_value: float, step: int = None) -> Dict:
        """记录指标"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO experiment_metrics_log
                    (experiment_id, step, metric_name, metric_value, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    experiment_id, step, metric_name, metric_value,
                    datetime.now().isoformat()
                ))

                # 更新实验的最终指标
                cursor.execute('SELECT metrics FROM experiments WHERE experiment_id = ?', (experiment_id,))
                row = cursor.fetchone()
                if row:
                    metrics = json.loads(row[0]) if row[0] else {}
                    if metric_name not in metrics:
                        metrics[metric_name] = {}
                    metrics[metric_name]['value'] = metric_value
                    metrics[metric_name]['step'] = step
                    cursor.execute('''
                        UPDATE experiments SET metrics = ? WHERE experiment_id = ?
                    ''', (json.dumps(metrics, ensure_ascii=False), experiment_id))

                conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def log_metrics_batch(self, experiment_id: str, metrics: Dict[str, float],
                         step: int = None) -> Dict:
        """批量记录指标"""
        for name, value in metrics.items():
            self.log_metric(experiment_id, name, value, step)
        return {'success': True, 'metrics_logged': len(metrics)}

    def complete_experiment(self, experiment_id: str,
                           final_metrics: Dict = None,
                           model_artifact: str = None) -> Dict:
        """完成实验"""
        end_time = datetime.now()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 获取开始时间计算持续时间
                cursor.execute('SELECT start_time FROM experiments WHERE experiment_id = ?', (experiment_id,))
                row = cursor.fetchone()
                duration = 0
                if row and row[0]:
                    start = datetime.fromisoformat(row[0])
                    duration = (end_time - start).total_seconds()

                # 更新最终指标
                if final_metrics:
                    cursor.execute('SELECT metrics FROM experiments WHERE experiment_id = ?', (experiment_id,))
                    row = cursor.fetchone()
                    metrics = json.loads(row[0]) if row and row[0] else {}
                    for k, v in final_metrics.items():
                        if k not in metrics:
                            metrics[k] = {}
                        metrics[k]['value'] = v
                        metrics[k]['final'] = True

                    cursor.execute('''
                        UPDATE experiments
                        SET status = 'completed', end_time = ?, duration_sec = ?,
                            metrics = ?, model_artifact = ?
                        WHERE experiment_id = ?
                    ''', (
                        end_time.isoformat(), duration,
                        json.dumps(metrics, ensure_ascii=False),
                        model_artifact, experiment_id
                    ))
                else:
                    cursor.execute('''
                        UPDATE experiments
                        SET status = 'completed', end_time = ?, duration_sec = ?
                        WHERE experiment_id = ?
                    ''', (end_time.isoformat(), duration, experiment_id))

                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True, 'experiment_id': experiment_id, 'duration_sec': round(duration, 2)}

    def fail_experiment(self, experiment_id: str, error: str = '') -> Dict:
        """标记实验失败"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE experiments
                    SET status = 'failed', end_time = ?,
                        notes = COALESCE(notes, '') || ?
                    WHERE experiment_id = ?
                ''', (datetime.now().isoformat(), f'\n错误: {error}', experiment_id))
                conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 实验查询 ==========

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM experiments WHERE experiment_id = ?', (experiment_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'experiment_id': row[0], 'experiment_name': row[1],
                    'project_name': row[2], 'status': row[3],
                    'hyperparameters': json.loads(row[4]) if row[4] else {},
                    'metrics': json.loads(row[5]) if row[5] else {},
                    'tags': json.loads(row[6]) if row[6] else [],
                    'notes': row[7], 'parent_id': row[8],
                    'model_artifact': row[9],
                    'start_time': row[10], 'end_time': row[11],
                    'duration_sec': row[12], 'created_at': row[13]
                }
        except Exception:
            return None

    def list_experiments(self, project_name: str = None, status: str = None,
                        tags: List[str] = None, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT experiment_id, experiment_name, project_name, status, metrics, tags, created_at FROM experiments'
                conditions = []
                params = []
                if project_name:
                    conditions.append('project_name = ?')
                    params.append(project_name)
                if status:
                    conditions.append('status = ?')
                    params.append(status)
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                return [
                    {
                        'experiment_id': r[0], 'experiment_name': r[1],
                        'project_name': r[2], 'status': r[3],
                        'metrics': json.loads(r[4]) if r[4] else {},
                        'tags': json.loads(r[5]) if r[5] else [],
                        'created_at': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_metric_history(self, experiment_id: str, metric_name: str = None,
                          limit: int = 1000) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if metric_name:
                    cursor.execute('''
                        SELECT step, metric_name, metric_value, created_at
                        FROM experiment_metrics_log
                        WHERE experiment_id = ? AND metric_name = ?
                        ORDER BY step LIMIT ?
                    ''', (experiment_id, metric_name, limit))
                else:
                    cursor.execute('''
                        SELECT step, metric_name, metric_value, created_at
                        FROM experiment_metrics_log
                        WHERE experiment_id = ?
                        ORDER BY step LIMIT ?
                    ''', (experiment_id, limit))
                return [
                    {
                        'step': r[0], 'metric_name': r[1],
                        'value': r[2], 'created_at': r[3]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 实验对比 ==========

    def compare_experiments(self, experiment_ids: List[str]) -> Dict:
        """对比多个实验"""
        experiments = []
        for eid in experiment_ids:
            exp = self.get_experiment(eid)
            if exp:
                experiments.append(exp)

        if not experiments:
            return {'success': False, 'error': '无有效实验'}

        # 收集所有指标名
        all_metrics = set()
        for exp in experiments:
            all_metrics.update(exp.get('metrics', {}).keys())

        # 构建对比表
        comparison = {}
        for metric in all_metrics:
            comparison[metric] = {}
            values = []
            for exp in experiments:
                val = exp.get('metrics', {}).get(metric, {}).get('value')
                comparison[metric][exp['experiment_id']] = val
                if val is not None:
                    values.append(val)

            # 统计
            if values:
                comparison[metric]['_best'] = max(values)
                comparison[metric]['_worst'] = min(values)
                comparison[metric]['_mean'] = round(sum(values) / len(values), 6)

        # 超参数差异
        all_params = set()
        for exp in experiments:
            all_params.update(exp.get('hyperparameters', {}).keys())

        param_diff = {}
        for param in all_params:
            param_diff[param] = {
                exp['experiment_id']: exp.get('hyperparameters', {}).get(param)
                for exp in experiments
            }

        return {
            'success': True,
            'experiments': [
                {
                    'experiment_id': e['experiment_id'],
                    'experiment_name': e['experiment_name'],
                    'status': e['status'],
                    'duration_sec': e.get('duration_sec')
                }
                for e in experiments
            ],
            'metric_comparison': comparison,
            'hyperparameter_diff': param_diff,
            'total_metrics': len(all_metrics)
        }

    # ========== 超参搜索 ==========

    def run_hyperparameter_search(self, search_name: str, method: str,
                                 param_space: Dict, objective_fn: Callable,
                                 n_trials: int = 20) -> Dict:
        """运行超参搜索"""
        search_id = f"SRCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        # 生成参数组合
        if method == 'grid':
            # 网格搜索需要 List 值
            trials = grid_search(param_space)
        elif method == 'random':
            trials = random_search(param_space, n_trials)
        elif method == 'bayesian':
            trials = random_search(param_space, min(5, n_trials))
        else:
            return {'success': False, 'error': f'不支持的搜索方法: {method}'}

        # 保存搜索
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO hyperparameter_searches
                    (search_id, search_name, method, param_space, n_trials,
                     status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'running', ?)
                ''', (
                    search_id, search_name, method,
                    json.dumps(param_space, ensure_ascii=False, default=str),
                    len(trials), datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

        # 执行搜索
        results = []
        history = []
        best_score = float('-inf')
        best_params = None

        for i, params in enumerate(trials):
            # 创建实验
            exp_result = self.create_experiment(
                f"{search_name}-trial-{i+1}",
                project_name=f"search-{search_id}",
                hyperparameters=params
            )

            if not exp_result.get('success'):
                continue

            exp_id = exp_result['experiment_id']

            # 运行目标函数
            try:
                score = objective_fn(params)
                self.log_metric(exp_id, 'objective_score', score)
                self.complete_experiment(exp_id, final_metrics={'objective_score': score})

                results.append({
                    'trial': i + 1,
                    'experiment_id': exp_id,
                    'params': params,
                    'score': score
                })
                history.append({'params': params, 'score': score})

                if score > best_score:
                    best_score = score
                    best_params = params

                # 贝叶斯优化：追加建议
                if method == 'bayesian' and i < n_trials - 1:
                    suggestions = bayesian_optimization_suggest(param_space, history, 1)
                    trials.extend(suggestions)

            except Exception as e:
                self.fail_experiment(exp_id, str(e))

        # 更新搜索结果
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE hyperparameter_searches
                    SET status = 'completed', best_score = ?, best_params = ?,
                        completed_at = ?
                    WHERE search_id = ?
                ''', (
                    best_score,
                    json.dumps(best_params or {}, ensure_ascii=False, default=str),
                    datetime.now().isoformat(), search_id
                ))
                conn.commit()
        except Exception:
            pass

        return {
            'success': True,
            'search_id': search_id,
            'method': method,
            'total_trials': len(results),
            'best_score': round(best_score, 6),
            'best_params': best_params,
            'all_results': sorted(results, key=lambda x: x['score'], reverse=True)[:10]
        }

    # ========== 模型注册 ==========

    def register_model(self, model_name: str, version: str,
                      experiment_id: str = None, metrics: Dict = None,
                      artifact_path: str = None, tags: List[str] = None) -> Dict:
        """注册模型"""
        model_id = f"MODEL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO model_registry
                    (model_id, model_name, version, experiment_id, metrics,
                     artifact_path, tags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    model_id, model_name, version, experiment_id,
                    json.dumps(metrics or {}, ensure_ascii=False),
                    artifact_path,
                    json.dumps(tags or [], ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True, 'model_id': model_id}

    def list_models(self, model_name: str = None, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if model_name:
                    cursor.execute('''
                        SELECT model_id, model_name, version, metrics, status, tags, created_at
                        FROM model_registry WHERE model_name = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (model_name, limit))
                else:
                    cursor.execute('''
                        SELECT model_id, model_name, version, metrics, status, tags, created_at
                        FROM model_registry
                        ORDER BY created_at DESC LIMIT ?
                    ''', (limit,))
                return [
                    {
                        'model_id': r[0], 'model_name': r[1], 'version': r[2],
                        'metrics': json.loads(r[3]) if r[3] else {},
                        'status': r[4], 'tags': json.loads(r[5]) if r[5] else [],
                        'created_at': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 统计 ==========

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM experiments')
                total_experiments = cursor.fetchone()[0]
                cursor.execute("SELECT status, COUNT(*) FROM experiments GROUP BY status")
                status_dist = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM model_registry')
                total_models = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM experiment_metrics_log')
                total_metrics = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM hyperparameter_searches')
                total_searches = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(DISTINCT project_name) FROM experiments')
                total_projects = cursor.fetchone()[0]
                return {
                    'total_experiments': total_experiments,
                    'status_distribution': status_dist,
                    'total_models': total_models,
                    'total_metrics_logged': total_metrics,
                    'total_searches': total_searches,
                    'total_projects': total_projects
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    tracker = AIExperimentTracker()

    print("=== 创建实验 ===")
    exp1 = tracker.create_experiment(
        'ResNet分类实验',
        project_name='图像分类',
        hyperparameters={'lr': 0.001, 'batch_size': 32, 'epochs': 50, 'model': 'resnet50'},
        tags=['cnn', 'classification']
    )
    exp2 = tracker.create_experiment(
        'ViT分类实验',
        project_name='图像分类',
        hyperparameters={'lr': 0.0001, 'batch_size': 16, 'epochs': 100, 'model': 'vit-base'},
        tags=['transformer', 'classification']
    )
    print(f"  实验1: {exp1['experiment_id']}")
    print(f"  实验2: {exp2['experiment_id']}")

    print("\n=== 记录指标 ===")
    for step in range(10):
        acc1 = 0.5 + step * 0.04 + random.gauss(0, 0.02)
        loss1 = 1.0 - step * 0.08 + random.gauss(0, 0.05)
        tracker.log_metric(exp1['experiment_id'], 'accuracy', acc1, step)
        tracker.log_metric(exp1['experiment_id'], 'loss', loss1, step)

        acc2 = 0.4 + step * 0.05 + random.gauss(0, 0.02)
        loss2 = 1.2 - step * 0.09 + random.gauss(0, 0.05)
        tracker.log_metric(exp2['experiment_id'], 'accuracy', acc2, step)
        tracker.log_metric(exp2['experiment_id'], 'loss', loss2, step)

    print("  指标记录完成")

    print("\n=== 完成实验 ===")
    tracker.complete_experiment(exp1['experiment_id'],
                               final_metrics={'accuracy': 0.92, 'loss': 0.15})
    tracker.complete_experiment(exp2['experiment_id'],
                               final_metrics={'accuracy': 0.95, 'loss': 0.10})
    print("  实验已完成")

    print("\n=== 实验对比 ===")
    comparison = tracker.compare_experiments([exp1['experiment_id'], exp2['experiment_id']])
    print(f"  对比指标数: {comparison['total_metrics']}")
    for metric, values in comparison['metric_comparison'].items():
        if not metric.startswith('_'):
            print(f"  {metric}: 最佳={values.get('_best')}, 平均={values.get('_mean')}")

    print("\n=== 超参搜索 ===")
    def objective(params):
        # 模拟目标函数
        return params.get('lr', 0.001) * 100 - abs(params.get('batch_size', 32) - 16) * 0.1

    search_result = tracker.run_hyperparameter_search(
        '学习率搜索', 'random',
        {'lr': (0.0001, 0.01), 'batch_size': (8, 64)},
        objective, n_trials=10
    )
    print(f"  搜索方法: {search_result['method']}")
    print(f"  总试验: {search_result['total_trials']}")
    print(f"  最佳分数: {search_result['best_score']}")
    print(f"  最佳参数: {search_result['best_params']}")

    print("\n=== 模型注册 ===")
    model_result = tracker.register_model(
        'image-classifier', 'v1.0',
        experiment_id=exp2['experiment_id'],
        metrics={'accuracy': 0.95, 'loss': 0.10},
        tags=['production', 'best']
    )
    print(f"  模型ID: {model_result.get('model_id')}")

    print("\n=== 指标历史 ===")
    history = tracker.get_metric_history(exp1['experiment_id'], 'accuracy')
    print(f"  记录数: {len(history)}")
    for h in history[:5]:
        print(f"    step={h['step']}: {h['value']}")

    print(f"\n统计: {tracker.get_statistics()}")

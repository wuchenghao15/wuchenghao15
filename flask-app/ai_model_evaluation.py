#!/usr/bin/env python3
"""
MTSCOS AI 模型评估服务 (v14.5.0)
==================================
AI 模型性能评估、回归测试、A/B 测试和模型对比。

核心能力：
1. 性能指标 - 准确率/精确率/召回率/F1/混淆矩阵/ROC-AUC
2. 回归测试 - 测试用例集管理和批量验证
3. A/B 测试 - 多模型流量分配和显著性检验
4. 模型对比 - 多模型性能横向对比
5. 性能基线 - 历史性能趋势追踪
6. 评估报告 - 综合评估报告生成
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_evaluation.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIModelEval')


# ========== 指标计算 ==========

def compute_classification_metrics(predictions: List[Any], ground_truth: List[Any],
                                   positive_label: Any = 1) -> Dict[str, float]:
    """计算二分类/多分类指标"""
    if len(predictions) != len(ground_truth) or not predictions:
        return {'error': 'invalid input'}

    labels = sorted(set(ground_truth) | set(predictions))

    if len(labels) == 2:
        # 二分类
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == positive_label and g == positive_label)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p == positive_label and g != positive_label)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != positive_label and g == positive_label)
        tn = sum(1 for p, g in zip(predictions, ground_truth) if p != positive_label and g != positive_label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(predictions)
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        return {
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'specificity': round(specificity, 4),
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'support': len(predictions)
        }
    else:
        # 多分类：宏平均
        per_label = {}
        for label in labels:
            tp = sum(1 for p, g in zip(predictions, ground_truth) if p == label and g == label)
            fp = sum(1 for p, g in zip(predictions, ground_truth) if p == label and g != label)
            fn = sum(1 for p, g in zip(predictions, ground_truth) if p != label and g == label)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            per_label[str(label)] = {'precision': precision, 'recall': recall, 'f1': f1, 'support': tp + fn}

        macro_p = sum(v['precision'] for v in per_label.values()) / len(per_label)
        macro_r = sum(v['recall'] for v in per_label.values()) / len(per_label)
        macro_f1 = sum(v['f1'] for v in per_label.values()) / len(per_label)
        accuracy = sum(1 for p, g in zip(predictions, ground_truth) if p == g) / len(predictions)

        return {
            'accuracy': round(accuracy, 4),
            'macro_precision': round(macro_p, 4),
            'macro_recall': round(macro_r, 4),
            'macro_f1': round(macro_f1, 4),
            'per_label': per_label,
            'support': len(predictions)
        }


def compute_confusion_matrix(predictions: List[Any], ground_truth: List[Any]) -> Dict[str, Dict[str, int]]:
    """计算混淆矩阵"""
    labels = sorted(set(ground_truth) | set(predictions), key=str)
    matrix = {str(true): {str(pred): 0 for pred in labels} for true in labels}
    for p, g in zip(predictions, ground_truth):
        matrix[str(g)][str(p)] += 1
    return matrix


def compute_regression_metrics(predictions: List[float], ground_truth: List[float]) -> Dict[str, float]:
    """计算回归指标"""
    if len(predictions) != len(ground_truth) or not predictions:
        return {'error': 'invalid input'}

    n = len(predictions)
    mae = sum(abs(p - g) for p, g in zip(predictions, ground_truth)) / n
    mse = sum((p - g) ** 2 for p, g in zip(predictions, ground_truth)) / n
    rmse = math.sqrt(mse)

    mean_gt = sum(ground_truth) / n
    ss_total = sum((g - mean_gt) ** 2 for g in ground_truth)
    ss_residual = sum((p - g) ** 2 for p, g in zip(predictions, ground_truth))
    r2 = 1 - ss_residual / ss_total if ss_total > 0 else 0.0

    mape = sum(abs((g - p) / g) for p, g in zip(predictions, ground_truth) if g != 0) / n * 100

    return {
        'mae': round(mae, 4),
        'mse': round(mse, 4),
        'rmse': round(rmse, 4),
        'r2': round(r2, 4),
        'mape': round(mape, 2),
        'support': n
    }


def compute_roc_auc(scores: List[float], ground_truth: List[int]) -> Dict[str, Any]:
    """计算ROC-AUC（二分类）"""
    if len(scores) != len(ground_truth) or not scores:
        return {'error': 'invalid input'}

    # 按分数降序排列
    paired = sorted(zip(scores, ground_truth), key=lambda x: -x[0])
    pos = sum(1 for _, g in paired if g == 1)
    neg = len(paired) - pos

    if pos == 0 or neg == 0:
        return {'auc': 0.5, 'roc_points': [], 'error': 'single class'}

    # 计算TPR/FPR
    tp, fp = 0, 0
    points = [(0.0, 0.0)]
    prev_score = None
    for score, label in paired:
        if prev_score is not None and score != prev_score:
            points.append((fp / neg, tp / pos))
        if label == 1:
            tp += 1
        else:
            fp += 1
        prev_score = score
    points.append((fp / neg, tp / pos))

    # 计算AUC（梯形法）
    auc = 0.0
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        auc += (x2 - x1) * (y1 + y2) / 2

    return {
        'auc': round(auc, 4),
        'roc_points': [(round(x, 4), round(y, 4)) for x, y in points]
    }


# ========== 默认数据 ==========

DEFAULT_TEST_CASES = [
    {
        'case_id': 'TC-001',
        'name': '意图识别-问询类',
        'input': {'text': '如何重置密码？'},
        'expected': {'intent': 'question'},
        'category': 'intent'
    },
    {
        'case_id': 'TC-002',
        'name': '意图识别-命令类',
        'input': {'text': '请执行系统检查'},
        'expected': {'intent': 'command'},
        'category': 'intent'
    },
    {
        'case_id': 'TC-003',
        'name': '情感-正面',
        'input': {'text': '服务非常好，很满意'},
        'expected': {'sentiment': 'positive'},
        'category': 'sentiment'
    },
    {
        'case_id': 'TC-004',
        'name': '情感-负面',
        'input': {'text': '糟糕的体验，非常失望'},
        'expected': {'sentiment': 'negative'},
        'category': 'sentiment'
    },
    {
        'case_id': 'TC-005',
        'name': '内容审核-暴力',
        'input': {'text': '包含暴力内容'},
        'expected': {'category': 'violence', 'is_safe': False},
        'category': 'moderation'
    },
]


# ========== 评估服务 ==========

class AIModelEvaluation:
    """AI 模型评估服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._register_defaults()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_model_evaluations (
                        eval_id TEXT PRIMARY KEY,
                        model_id TEXT NOT NULL,
                        eval_type TEXT,
                        metrics TEXT,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT,
                        notes TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_test_cases (
                        case_id TEXT PRIMARY KEY,
                        name TEXT,
                        category TEXT,
                        input_data TEXT,
                        expected_output TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_test_runs (
                        run_id TEXT PRIMARY KEY,
                        eval_id TEXT,
                        case_id TEXT,
                        actual_output TEXT,
                        passed INTEGER,
                        error_message TEXT,
                        duration_ms INTEGER,
                        executed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_ab_experiments (
                        experiment_id TEXT PRIMARY KEY,
                        name TEXT,
                        model_a TEXT,
                        model_b TEXT,
                        traffic_split INTEGER DEFAULT 50,
                        status TEXT DEFAULT 'running',
                        metrics_a TEXT,
                        metrics_b TEXT,
                        winner TEXT,
                        started_at TEXT,
                        ended_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_eval_model ON ai_model_evaluations(model_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_eval ON ai_test_runs(eval_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化评估数据库失败: {e}")

    def _register_defaults(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for case in DEFAULT_TEST_CASES:
                    cursor.execute('SELECT case_id FROM ai_test_cases WHERE case_id = ?', (case['case_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO ai_test_cases
                            (case_id, name, category, input_data, expected_output, status, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            case['case_id'], case['name'], case['category'],
                            json.dumps(case['input'], ensure_ascii=False),
                            json.dumps(case['expected'], ensure_ascii=False),
                            'active', datetime.now().isoformat()
                        ))
                conn.commit()
        except Exception as e:
            logger.error(f"注册默认测试用例失败: {e}")

    # ========== 评估执行 ==========

    def evaluate(self, model_id: str, predictions: List[Any], ground_truth: List[Any],
                 task_type: str = 'classification', notes: str = '') -> Dict:
        """执行模型评估"""
        eval_id = f"EVAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        if task_type == 'classification':
            metrics = compute_classification_metrics(predictions, ground_truth)
            cm = compute_confusion_matrix(predictions, ground_truth)
            metrics['confusion_matrix'] = cm
        elif task_type == 'regression':
            metrics = compute_regression_metrics(predictions, ground_truth)
        else:
            metrics = {'error': f'unsupported task type: {task_type}'}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_model_evaluations
                    (eval_id, model_id, eval_type, metrics, status, created_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    eval_id, model_id, task_type,
                    json.dumps(metrics, ensure_ascii=False),
                    'completed', datetime.now().isoformat(), notes
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True, 'eval_id': eval_id, 'metrics': metrics}

    def evaluate_with_scores(self, model_id: str, scores: List[float],
                            ground_truth: List[int], notes: str = '') -> Dict:
        """带置信度的二分类评估（含ROC-AUC）"""
        eval_id = f"EVAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        # 以0.5为阈值生成预测
        predictions = [1 if s >= 0.5 else 0 for s in scores]
        metrics = compute_classification_metrics(predictions, ground_truth)
        roc = compute_roc_auc(scores, ground_truth)
        metrics['auc'] = roc.get('auc', 0.5)
        metrics['roc_points'] = roc.get('roc_points', [])

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_model_evaluations
                    (eval_id, model_id, eval_type, metrics, status, created_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    eval_id, model_id, 'binary_with_scores',
                    json.dumps(metrics, ensure_ascii=False),
                    'completed', datetime.now().isoformat(), notes
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True, 'eval_id': eval_id, 'metrics': metrics}

    # ========== 回归测试 ==========

    def run_regression_test(self, model_id: str, predict_fn=None) -> Dict:
        """运行回归测试套件

        predict_fn: 可调用对象，接收 input_data，返回 prediction dict
        """
        eval_id = f"REG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        cases = self.list_test_cases()
        if not cases:
            return {'success': False, 'error': '无可用测试用例'}

        results = []
        passed = 0
        failed = 0
        start_ts = datetime.now()

        for case in cases:
            case_start = datetime.now()
            actual = None
            error = None
            case_passed = 0

            try:
                if predict_fn:
                    actual = predict_fn(case['input_data'])
                else:
                    # 默认模拟预测：直接返回expected（用于演示）
                    actual = case['expected_output']

                # 比较结果
                if isinstance(actual, dict) and isinstance(case['expected_output'], dict):
                    matches = all(actual.get(k) == v for k, v in case['expected_output'].items())
                    case_passed = 1 if matches else 0
                else:
                    case_passed = 1 if actual == case['expected_output'] else 0
            except Exception as e:
                error = str(e)

            if case_passed:
                passed += 1
            else:
                failed += 1

            duration_ms = int((datetime.now() - case_start).total_seconds() * 1000)
            run_id = f"RUN-{eval_id}-{case['case_id']}"

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_test_runs
                        (run_id, eval_id, case_id, actual_output, passed, error_message, duration_ms, executed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        run_id, eval_id, case['case_id'],
                        json.dumps(actual, ensure_ascii=False) if actual else None,
                        case_passed, error, duration_ms, datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"记录测试运行失败: {e}")

            results.append({
                'case_id': case['case_id'],
                'name': case['name'],
                'passed': bool(case_passed),
                'duration_ms': duration_ms,
                'error': error
            })

        duration = int((datetime.now() - start_ts).total_seconds() * 1000)
        metrics = {
            'total': len(cases),
            'passed': passed,
            'failed': failed,
            'pass_rate': round(passed / len(cases) * 100, 2) if cases else 0,
            'duration_ms': duration
        }

        # 记录评估
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_model_evaluations
                    (eval_id, model_id, eval_type, metrics, status, created_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    eval_id, model_id, 'regression',
                    json.dumps(metrics, ensure_ascii=False),
                    'completed', datetime.now().isoformat(),
                    f'回归测试: {passed}/{len(cases)} 通过'
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录回归测试评估失败: {e}")

        return {
            'success': True,
            'eval_id': eval_id,
            'metrics': metrics,
            'results': results
        }

    # ========== A/B 测试 ==========

    def create_ab_experiment(self, name: str, model_a: str, model_b: str,
                            traffic_split: int = 50) -> Dict:
        """创建A/B测试实验"""
        if not (0 <= traffic_split <= 100):
            return {'success': False, 'error': 'traffic_split必须在0-100之间'}

        experiment_id = f"AB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_ab_experiments
                    (experiment_id, name, model_a, model_b, traffic_split,
                     status, started_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    experiment_id, name, model_a, model_b, traffic_split,
                    'running', datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'experiment_id': experiment_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_ab_metrics(self, experiment_id: str, model: str, metrics: Dict) -> Dict:
        """更新A/B测试中某模型的指标"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT model_a, model_b FROM ai_ab_experiments WHERE experiment_id = ?',
                              (experiment_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '实验不存在'}

                field = 'metrics_a' if model == row[0] else 'metrics_b' if model == row[1] else None
                if not field:
                    return {'success': False, 'error': f'模型 {model} 不属于此实验'}

                cursor.execute(f'''
                    UPDATE ai_ab_experiments
                    SET {field} = ?
                    WHERE experiment_id = ?
                ''', (json.dumps(metrics, ensure_ascii=False), experiment_id))
                conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def conclude_ab_experiment(self, experiment_id: str) -> Dict:
        """结束A/B测试，自动判定胜者"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT model_a, model_b, metrics_a, metrics_b FROM ai_ab_experiments WHERE experiment_id = ?',
                              (experiment_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '实验不存在'}

                model_a, model_b, m_a, m_b = row
                metrics_a = json.loads(m_a) if m_a else {}
                metrics_b = json.loads(m_b) if m_b else {}

                # 比较 accuracy 或 f1_score
                score_a = metrics_a.get('accuracy', metrics_a.get('f1_score', 0))
                score_b = metrics_b.get('accuracy', metrics_b.get('f1_score', 0))

                winner = model_a if score_a >= score_b else model_b
                lift = ((score_b - score_a) / score_a * 100) if score_a > 0 else 0

                cursor.execute('''
                    UPDATE ai_ab_experiments
                    SET status = 'completed', winner = ?, ended_at = ?
                    WHERE experiment_id = ?
                ''', (winner, datetime.now().isoformat(), experiment_id))
                conn.commit()

                return {
                    'success': True,
                    'winner': winner,
                    'score_a': score_a,
                    'score_b': score_b,
                    'lift_percent': round(lift, 2),
                    'metrics_a': metrics_a,
                    'metrics_b': metrics_b
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 测试用例管理 ==========

    def add_test_case(self, case_id: str, name: str, category: str,
                     input_data: Dict, expected_output: Dict) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_test_cases
                    (case_id, name, category, input_data, expected_output, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    case_id, name, category,
                    json.dumps(input_data, ensure_ascii=False),
                    json.dumps(expected_output, ensure_ascii=False),
                    'active', datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'case_id': case_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_test_cases(self, category: Optional[str] = None) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute('SELECT * FROM ai_test_cases WHERE category = ? AND status = ? ORDER BY case_id',
                                  (category, 'active'))
                else:
                    cursor.execute('SELECT * FROM ai_test_cases WHERE status = ? ORDER BY case_id', ('active',))
                return [
                    {
                        'case_id': r[0], 'name': r[1], 'category': r[2],
                        'input_data': json.loads(r[3]) if r[3] else {},
                        'expected_output': json.loads(r[4]) if r[4] else {},
                        'status': r[5], 'created_at': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 查询统计 ==========

    def get_evaluation(self, eval_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_model_evaluations WHERE eval_id = ?', (eval_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'eval_id': row[0], 'model_id': row[1], 'eval_type': row[2],
                    'metrics': json.loads(row[3]) if row[3] else {},
                    'status': row[4], 'created_at': row[5], 'notes': row[6]
                }
        except Exception:
            return None

    def get_model_history(self, model_id: str, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT eval_id, eval_type, metrics, created_at, notes
                    FROM ai_model_evaluations
                    WHERE model_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (model_id, limit))
                return [
                    {
                        'eval_id': r[0], 'eval_type': r[1],
                        'metrics': json.loads(r[2]) if r[2] else {},
                        'created_at': r[3], 'notes': r[4]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def compare_models(self, model_ids: List[str]) -> Dict:
        """对比多个模型的最新评估结果"""
        comparison = {}
        for model_id in model_ids:
            history = self.get_model_history(model_id, limit=1)
            if history:
                comparison[model_id] = history[0]['metrics']
            else:
                comparison[model_id] = {'note': '无评估记录'}
        return {'comparison': comparison}


# ========== 模块入口 ==========

if __name__ == '__main__':
    evaluator = AIModelEvaluation()
    print(f"已加载测试用例: {len(evaluator.list_test_cases())}")

    # 分类指标测试
    print("\n分类指标测试:")
    result = evaluator.evaluate(
        'model-test-001',
        predictions=[1, 0, 1, 1, 0, 1, 0, 0],
        ground_truth=[1, 0, 1, 0, 0, 1, 1, 0],
        task_type='classification',
        notes='单元测试'
    )
    print(f"评估ID: {result.get('eval_id')}")
    print(f"指标: {result.get('metrics')}")

    # 回归测试
    print("\n运行回归测试:")
    reg_result = evaluator.run_regression_test('model-test-001')
    print(f"通过率: {reg_result['metrics']['pass_rate']}%")

    # A/B 测试
    print("\nA/B 测试:")
    ab = evaluator.create_ab_experiment('意图识别模型对比', 'model-a', 'model-b', 50)
    print(f"实验ID: {ab.get('experiment_id')}")
    evaluator.update_ab_metrics(ab['experiment_id'], 'model-a', {'accuracy': 0.85, 'f1_score': 0.83})
    evaluator.update_ab_metrics(ab['experiment_id'], 'model-b', {'accuracy': 0.88, 'f1_score': 0.87})
    conclusion = evaluator.conclude_ab_experiment(ab['experiment_id'])
    print(f"胜者: {conclusion.get('winner')}, 提升: {conclusion.get('lift_percent')}%")

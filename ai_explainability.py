#!/usr/bin/env python3
"""
MTSCOS AI 可解释性服务 (v14.7.0)
===================================
AI 模型可解释性和模型透明度服务。

核心能力：
1. 特征重要性 - Permutation Importance
2. 局部解释 - LIME 风格局部可解释
3. 反事实解释 - 最小特征改变预测结果
4. SHAP 简化版 - Shapley 值近似计算
5. 决策路径 - 决策路径可视化
6. 置信度分解 - 各特征贡献度分解
7. 模型对比 - 多模型解释对比
8. 解释报告 - 生成可解释性报告
"""
import os
import json
import math
import sqlite3
import random
import logging
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_explainability.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIExplainability')


# ========== 特征重要性 ==========

def permutation_importance(predict_fn, X: List[List[float]], y: List[Any],
                     feature_names: List[str], n_repeats: int = 10) -> Dict:
    """排列重要性：打乱每个特征，观察性能下降"""
    baseline_pred = [predict_fn(x) for x in X]
    baseline_score = _accuracy(baseline_pred, y)

    importances = []

    for feat_idx, feat_name in enumerate(feature_names):
        scores = []
        for _ in range(n_repeats):
            X_permuted = [list(row) for row in X]
            permuted_col = [row[feat_idx] for row in X_permuted]
            random.shuffle(permuted_col)
            for i in range(len(X_permuted)):
                X_permuted[i][feat_idx] = permuted_col[i]
            perm_pred = [predict_fn(x) for x in X_permuted]
            perm_score = _accuracy(perm_pred, y)
            scores.append(baseline_score - perm_score)

        avg_importance = sum(scores) / len(scores)
        std_importance = _std(scores)
        importances.append({
            'feature': feat_name,
            'importance': round(avg_importance, 6),
            'std': round(std_importance, 6),
            'rank': 0
        })

    # 排序并排名
    importances.sort(key=lambda x: x['importance'], reverse=True)
    for i, imp in enumerate(importances):
        imp['rank'] = i + 1

    return {
        'method': 'permutation_importance',
        'baseline_score': round(baseline_score, 6),
        'importances': importances,
        'n_repeats': n_repeats
    }


def _accuracy(pred: List, actual: List) -> float:
    if len(pred) != len(actual) or not pred:
        return 0.0
    correct = sum(1 for p, a in zip(pred, actual) if p == a)
    return correct / len(pred)


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


# ========== 局部解释 (LIME 简化版) ==========

def lime_explain(predict_fn, instance: List[float], feature_names: List[str],
                 num_samples: int = 100, num_features: int = 5) -> Dict:
    """LIME 风格局部解释：在实例附近扰动，拟合线性模型"""
    # 1. 在实例附近生成扰动样本
    samples = []
    for _ in range(num_samples):
        perturbed = list(instance)
        for j in range(len(perturbed)):
            if random.random() < 0.3:  # 30%概率扰动
                scale = max(abs(perturbed[j]) * 0.1, 0.01) if perturbed[j] else 0.1
                perturbed[j] += random.gauss(0, scale)
        samples.append(perturbed)

    # 2. 预测所有样本
    predictions = [predict_fn(s) for s in samples]

    # 3. 计算每个样本与原实例的距离权重
    weights = []
    for s in samples:
        dist = math.sqrt(sum((s[i] - instance[i]) ** 2 for i in range(len(instance))))
        weights.append(math.exp(-dist ** 2 / (2 * (len(instance) * 0.1) ** 2)))  # 核函数
    # 归一化权重
    w_sum = sum(weights) if sum(weights) > 0 else 1
    weights = [w / w_sum for w in weights]

    # 4. 加权线性回归（简化版：直接计算特征相关性作为重要性）
    # 把预测转为数值
    pred_numeric = []
    for p in predictions:
        if isinstance(p, (int, float)):
            pred_numeric.append(float(p))
        else:
            pred_numeric.append(1.0 if p else 0.0)

    # 计算加权特征重要性
    feature_importance = []
    for feat_idx, feat_name in enumerate(feature_names):
        feat_vals = [s[feat_idx] for s in samples]
        # 加权相关性
        weighted_corr = _weighted_correlation(feat_vals, pred_numeric, weights)
        feature_importance.append({
            'feature': feat_name,
            'value': round(instance[feat_idx], 6),
            'contribution': round(weighted_corr, 6),
            'importance': round(abs(weighted_corr), 6)
        })

    feature_importance.sort(key=lambda x: x['importance'], reverse=True)

    return {
        'method': 'lime',
        'instance': instance,
        'prediction': predict_fn(instance),
        'top_features': feature_importance[:num_features],
        'num_samples': num_samples
    }


def _weighted_correlation(x: List[float], y: List[float], w: List[float]) -> float:
    """加权皮尔逊相关系数"""
    n = len(x)
    if n == 0:
        return 0.0
    mean_x = sum(w[i] * x[i] for i in range(n))
    mean_y = sum(w[i] * y[i] for i in range(n))
    cov = sum(w[i] * (x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    var_x = sum(w[i] * (x[i] - mean_x) ** 2 for i in range(n))
    var_y = sum(w[i] * (y[i] - mean_y) ** 2 for i in range(n))
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)


# ========== 反事实解释 ==========

def counterfactual_explain(predict_fn, instance: List[float], target_class: Any,
                        feature_names: List[str],
                        max_iter: int = 100, step_size: float = 0.01) -> Dict:
    """反事实解释：找到最小特征变化使预测变为目标类别"""
    current = list(instance)
    original_pred = predict_fn(current)

    if original_pred == target_class:
        return {
            'method': 'counterfactual',
            'instance': instance,
            'target_class': target_class,
            'found': True,
            'message': '实例已经是目标类别',
            'changes': []
        }

    best_counterfactual = None
    min_distance = float('inf')

    for iteration in range(max_iter):
        # 在每个特征上尝试微调
        for feat_idx in range(len(instance)):
            for direction in [-1, 1]:
                candidate = list(current)
                # 计算调整步长与原始值成比例
                step = max(abs(instance[feat_idx]) * step_size, 0.001) if instance[feat_idx] else step_size
                candidate[feat_idx] += direction * step
                pred = predict_fn(candidate)
                if pred == target_class:
                    dist = math.sqrt(sum((candidate[i] - instance[i]) ** 2 for i in range(len(instance))))
                    if dist < min_distance:
                        min_distance = dist
                        best_counterfactual = list(candidate)

        if best_counterfactual:
            break

    if best_counterfactual:
        changes = []
        for i, name in enumerate(feature_names):
            if abs(best_counterfactual[i] - instance[i]) > 1e-6:
                changes.append({
                    'feature': name,
                    'original': round(instance[i], 6),
                    'counterfactual': round(best_counterfactual[i], 6),
                    'change': round(best_counterfactual[i] - instance[i], 6),
                    'change_percent': round((best_counterfactual[i] - instance[i]) / max(abs(instance[i]), 1e-10) * 100, 2)
                })
        changes.sort(key=lambda x: abs(x['change_percent']), reverse=True)
        return {
            'method': 'counterfactual',
            'instance': instance,
            'counterfactual': best_counterfactual,
            'original_prediction': original_pred,
            'target_class': target_class,
            'found': True,
            'distance': round(min_distance, 6),
            'changes': changes,
            'num_changes': len(changes)
        }
    else:
        return {
            'method': 'counterfactual',
            'instance': instance,
            'original_prediction': original_pred,
            'target_class': target_class,
            'found': False,
            'message': '未找到反事实样本'
        }


# ========== SHAP 简化版 ==========

def shap_approximate(predict_fn, instance: List[float], feature_names: List[str],
                     background_dataset: List[List[float]] = None,
                     n_samples: int = 50) -> Dict:
    """SHAP 值近似（基于特征排列的简化版）"""
    n_features = len(instance)
    shap_values = [0.0] * n_features

    # 如果没有背景数据集，用实例自身的扰动作为背景
    if background_dataset is None:
        background_dataset = []
        for _ in range(20):
            background = []
            for j in range(n_features):
                scale = max(abs(instance[j]) * 0.3, 0.1) if instance[j] else 0.1
                background.append(instance[j] + random.gauss(0, scale))
            background_dataset.append(background)

    # 对每个特征计算近似shap值
    baseline_pred = [predict_fn(bg) for bg in background_dataset]
    baseline = sum(1 if p == 1 else 0 for p in baseline_pred) / len(baseline_pred) if baseline_pred else 0

    for feat_idx in range(n_features):
        marginal_contributions = []
        for _ in range(n_samples):
            # 随机选一个背景样本
            bg = random.choice(background_dataset)
            # 含该特征的预测
            with_feat = list(instance)
            # 不含该特征（用背景值替代）
            without_feat = list(instance)
            without_feat[feat_idx] = bg[feat_idx]

            pred_with = predict_fn(with_feat)
            pred_without = predict_fn(without_feat)

            # 转为数值
            val_with = float(pred_with) if isinstance(pred_with, (int, float)) else (1.0 if pred_with else 0.0)
            val_without = float(pred_without) if isinstance(pred_without, (int, float)) else (1.0 if pred_without else 0.0)
            marginal_contributions.append(val_with - val_without)

        shap_values[feat_idx] = sum(marginal_contributions) / len(marginal_contributions)

    # 整理结果
    results = []
    for i, name in enumerate(feature_names):
        results.append({
            'feature': name,
            'value': round(instance[i], 6),
            'shap_value': round(shap_values[i], 6),
            'impact': 'positive' if shap_values[i] > 0 else 'negative',
            'abs_value': round(abs(shap_values[i]), 6)
        })

    results.sort(key=lambda x: x['abs_value'], reverse=True)

    return {
        'method': 'shap_approximate',
        'instance': instance,
        'baseline_value': round(baseline, 6),
        'prediction': predict_fn(instance),
        'shap_values': results,
        'n_samples': n_samples
    }


# ========== 置信度分解 ==========

def confidence_decomposition(predict_proba_fn, instance: List[float],
                            feature_names: List[str]) -> Dict:
    """置信度分解：展示各特征对预测置信度的贡献"""
    base_prob = predict_proba_fn(instance)
    if isinstance(base_prob, (list, tuple)):
        base_prob = base_prob[1]  # 取正类概率

    contributions = []
    for i, name in enumerate(feature_names):
        # 扰动该特征
        perturbed = list(instance)
        scale = max(abs(instance[i]) * 0.1, 0.01) if instance[i] else 0.01
        perturbed[i] += scale
        prob_up = predict_proba_fn(perturbed)
        if isinstance(prob_up, (list, tuple)):
            prob_up = prob_up[1]

        perturbed[i] = instance[i] - scale
        prob_down = predict_proba_fn(perturbed)
        if isinstance(prob_down, (list, tuple)):
            prob_down = prob_down[1]

        sensitivity = (prob_up - prob_down) / (2 * scale) if scale > 0 else 0
        contribution = sensitivity * instance[i]

        contributions.append({
            'feature': name,
            'value': round(instance[i], 6),
            'contribution': round(contribution, 6),
            'sensitivity': round(sensitivity, 6),
            'abs_contribution': round(abs(contribution), 6)
        })

    contributions.sort(key=lambda x: x['abs_contribution'], reverse=True)

    return {
        'method': 'confidence_decomposition',
        'instance': instance,
        'confidence': round(base_prob, 6),
        'contributions': contributions
    }


# ========== 可解释性服务 ==========

class AIExplainability:
    """AI 可解释性服务"""

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
                    CREATE TABLE IF NOT EXISTS ai_explain_reports (
                        report_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        method TEXT,
                        target TEXT,
                        results TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_feature_importances (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT,
                        method TEXT,
                        feature_name TEXT,
                        importance REAL,
                        rank INTEGER,
                        created_at TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化可解释性数据库失败: {e}")

    # ========== 全局解释 ==========

    def explain_global(self, predict_fn, X: List[List[float]], y: List[Any],
                      feature_names: List[str], model_id: str = 'default',
                      methods: List[str] = None) -> Dict:
        """全局模型解释"""
        methods = methods or ['permutation']
        results = {}

        if 'permutation' in methods:
            result = permutation_importance(predict_fn, X, y, feature_names)
            results['permutation_importance'] = result
            # 保存重要性
            self._save_feature_importance(model_id, 'permutation', result['importances'])

        report_id = f"EXP-G-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        self._save_report(report_id, model_id, 'global', json.dumps(results, ensure_ascii=False))

        return {
            'success': True,
            'report_id': report_id,
            'model_id': model_id,
            'methods': methods,
            'results': results
        }

    # ========== 局部解释 ==========

    def explain_local(self, predict_fn, instance: List[float], feature_names: List[str],
                     model_id: str = 'default', methods: List[str] = None,
                     predict_proba_fn=None, target_class=None) -> Dict:
        """局部实例解释"""
        methods = methods or ['lime', 'shap']
        results = {}

        if 'lime' in methods:
            results['lime'] = lime_explain(predict_fn, instance, feature_names)

        if 'shap' in methods:
            results['shap'] = shap_approximate(predict_fn, instance, feature_names)

        if 'counterfactual' in methods and target_class is not None:
            results['counterfactual'] = counterfactual_explain(
                predict_fn, instance, target_class, feature_names
            )

        if 'confidence' in methods and predict_proba_fn:
            results['confidence_decomposition'] = confidence_decomposition(
                predict_proba_fn, instance, feature_names
            )

        report_id = f"EXP-L-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        self._save_report(report_id, model_id, 'local', json.dumps(results, ensure_ascii=False))

        return {
            'success': True,
            'report_id': report_id,
            'model_id': model_id,
            'instance': instance,
            'prediction': predict_fn(instance),
            'methods': methods,
            'results': results
        }

    # ========== 模型对比解释 ==========

    def compare_models(self, model_predictors: Dict[str, Callable],
                       X: List[List[float]], y: List[Any],
                       feature_names: List[str]) -> Dict:
        """多模型解释对比"""
        comparisons = {}

        for model_name, predict_fn in model_predictors.items():
            imp = permutation_importance(predict_fn, X, y, feature_names, n_repeats=5)
            comparisons[model_name] = {
                'accuracy': imp['baseline_score'],
                'top_features': imp['importances'][:5]
            }

        # 计算特征重要性一致性
        if len(comparisons) >= 2:
            model_names = list(comparisons.keys())
            top_features_a = {f['feature'] for f in comparisons[model_names[0]]['top_features']}
            top_features_b = {f['feature'] for f in comparisons[model_names[1]]['top_features']}
            overlap = top_features_a & top_features_b
            consistency = len(overlap) / len(top_features_a) if top_features_a else 0
            comparisons['_consistency'] = {
                'overlapping_features': list(overlap),
                'consistency_score': round(consistency, 4)
            }

        return {
            'method': 'model_comparison',
            'models': list(model_predictors.keys()),
            'comparisons': comparisons
        }

    # ========== 生成报告 ==========

    def generate_report(self, predict_fn, X: List[List[float]], y: List[Any],
                       feature_names: List[str], instance: List[float] = None,
                       model_id: str = 'default') -> Dict:
        """生成综合可解释性报告"""
        report = {}

        # 全局特征重要性
        global_imp = permutation_importance(predict_fn, X, y, feature_names, n_repeats=5)
        report['global_importance'] = global_imp

        # 局部解释（用第一个样本）
        if instance is None and X:
            instance = X[0]
        if instance:
            local_exp = lime_explain(predict_fn, instance, feature_names)
            report['local_explanation'] = local_exp

        # 特征统计
        report['feature_stats'] = self._compute_feature_stats(X, feature_names)

        # 模型性能
        predictions = [predict_fn(x) for x in X]
        report['model_performance'] = {
            'accuracy': round(_accuracy(predictions, y), 4),
            'total_samples': len(X),
            'feature_count': len(feature_names)
        }

        report_id = f"EXP-R-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        self._save_report(report_id, model_id, 'full_report', json.dumps(report, ensure_ascii=False))

        return {
            'success': True,
            'report_id': report_id,
            'model_id': model_id,
            'report': report
        }

    def _compute_feature_stats(self, X: List[List[float]], feature_names: List[str]) -> List[Dict]:
        """计算特征统计"""
        stats = []
        if not X:
            return stats
        for i, name in enumerate(feature_names):
            vals = [row[i] for row in X if i < len(row)]
            if not vals:
                continue
            stats.append({
                'feature': name,
                'min': round(min(vals), 6),
                'max': round(max(vals), 6),
                'mean': round(sum(vals) / len(vals), 6),
                'std': round(_std(vals), 6),
                'count': len(vals)
            })
        return stats

    def _save_feature_importance(self, model_id: str, method: str, importances: List[Dict]):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for imp in importances:
                    cursor.execute('''
                        INSERT INTO ai_feature_importances
                        (model_id, method, feature_name, importance, rank, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        model_id, method, imp['feature'],
                        imp['importance'], imp['rank'],
                        datetime.now().isoformat()
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存特征重要性失败: {e}")

    def _save_report(self, report_id: str, model_id: str, method: str, results: str):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_explain_reports
                    (report_id, model_id, method, results, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (report_id, model_id, method, results, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"保存解释报告失败: {e}")

    # ========== 查询 ==========

    def get_report(self, report_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_explain_reports WHERE report_id = ?', (report_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'report_id': row[0], 'model_id': row[1], 'method': row[2],
                    'results': json.loads(row[3]) if row[3] else {},
                    'created_at': row[4]
                }
        except Exception:
            return None

    def list_reports(self, model_id: str = None, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if model_id:
                    cursor.execute('''
                        SELECT report_id, model_id, method, created_at
                        FROM ai_explain_reports WHERE model_id = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (model_id, limit))
                else:
                    cursor.execute('''
                        SELECT report_id, model_id, method, created_at
                        FROM ai_explain_reports
                        ORDER BY created_at DESC LIMIT ?
                    ''', (limit,))
                return [
                    {'report_id': r[0], 'model_id': r[1], 'method': r[2], 'created_at': r[3]}
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_explain_reports')
                total_reports = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_feature_importances')
                total_importances = cursor.fetchone()[0]
                cursor.execute('SELECT DISTINCT model_id FROM ai_explain_reports')
                models = [r[0] for r in cursor.fetchall()]
                return {
                    'total_reports': total_reports,
                    'total_importance_records': total_importances,
                    'model_count': len(models)
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 示例预测函数 ==========

def _simple_classifier(x: List[float]) -> int:
    """示例分类器：简单加权和决策"""
    if len(x) < 4:
        return 0
    score = x[0] * 0.5 + x[1] * 0.3 + x[2] * 0.15 + x[3] * 0.05
    return 1 if score > 0.5 else 0


def _simple_proba(x: List[float]) -> float:
    """示例概率预测器"""
    if len(x) < 4:
        return 0.5
    score = x[0] * 0.5 + x[1] * 0.3 + x[2] * 0.15 + x[3] * 0.05
    # sigmoid
    return 1 / (1 + math.exp(-10 * (score - 0.5)))


# ========== 模块入口 ==========

if __name__ == '__main__':
    explainer = AIExplainability()

    feature_names = ['feature_1', 'feature_2', 'feature_3', 'feature_4']

    # 生成测试数据
    random.seed(42)
    X = [[random.random() for _ in range(4)] for _ in range(100)]
    y = [_simple_classifier(x) for x in X]

    print("全局特征重要性:")
    result = explainer.explain_global(_simple_classifier, X, y, feature_names)
    print(f"  基线准确率: {result['results']['permutation_importance']['baseline_score']}")
    for imp in result['results']['permutation_importance']['importances'][:5]:
        print(f"    #{imp['rank']} {imp['feature']}: {imp['importance']} (±{imp['std']})")

    print("\n局部解释 (LIME):")
    instance = [0.8, 0.2, 0.6, 0.4]
    local_result = explainer.explain_local(
        _simple_classifier, instance, feature_names,
        methods=['lime', 'shap', 'confidence'],
        predict_proba_fn=_simple_proba
    )
    print(f"  预测: {local_result['prediction']}")
    lime = local_result['results']['lime']
    print(f"  LIME Top特征:")
    for f in lime['top_features'][:3]:
        print(f"    {f['feature']}: 贡献={f['contribution']}, 值={f['value']}")

    print("\n反事实解释:")
    cf = counterfactual_explain(_simple_classifier, instance, target_class=0, feature_names=feature_names)
    print(f"  找到: {cf['found']}")
    if cf['found']:
        for c in cf['changes'][:3]:
            print(f"    {c['feature']}: {c['original']} → {c['counterfactual']} ({c['change_percent']}%)")

    print(f"\n统计: {explainer.get_statistics()}")

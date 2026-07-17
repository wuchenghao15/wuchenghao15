#!/usr/bin/env python3
"""
MTSCOS AI 特征工程服务 (v15.0.0)
===================================
AI 自动特征工程和特征选择服务。

核心能力：
1. 特征生成 - 数值变换/组合/多项式特征
2. 特征选择 - 方差/相关性/互信息选择
3. 特征变换 - 归一化/标准化/分箱
4. 特征编码 - 标签/频率/目标编码
5. 特征评估 - 特征重要性和冗余检测
6. 自动特征工程 - 自动特征生成管道
7. 特征降维 - PCA/LDA 简化版
8. 特征报告 - 特征分析报告
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, Counter

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_feature_engineering.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIFeatureEngineering')


# ========== 特征生成 ==========

def generate_numeric_features(values: List[float], name: str) -> Dict[str, List[float]]:
    """从数值特征生成衍生特征"""
    features = {}
    n = len(values)
    if n == 0:
        return features

    mean = sum(values) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0

    # 基本统计衍生
    features[f'{name}_mean_centered'] = [v - mean for v in values]
    features[f'{name}_standardized'] = [(v - mean) / std if std > 0 else 0.0 for v in values]
    features[f'{name}_squared'] = [v ** 2 for v in values]
    features[f'{name}_cubed'] = [v ** 3 for v in values]
    features[f'{name}_log'] = [math.log(abs(v) + 1) * (1 if v >= 0 else -1) for v in values]
    features[f'{name}_sqrt'] = [math.sqrt(abs(v)) * (1 if v >= 0 else -1) for v in values]
    features[f'{name}_reciprocal'] = [1 / v if v != 0 else 0.0 for v in values]
    features[f'{name}_abs'] = [abs(v) for v in values]

    # 分位数特征
    sorted_vals = sorted(values)
    q25 = sorted_vals[n // 4]
    q75 = sorted_vals[3 * n // 4]
    features[f'{name}_above_q75'] = [1.0 if v > q75 else 0.0 for v in values]
    features[f'{name}_below_q25'] = [1.0 if v < q25 else 0.0 for v in values]
    features[f'{name}_in_iqr'] = [1.0 if q25 <= v <= q75 else 0.0 for v in values]

    return features


def generate_interaction_features(feature_dict: Dict[str, List[float]],
                                  max_pairs: int = 10) -> Dict[str, List[float]]:
    """生成特征交互项"""
    features = {}
    names = list(feature_dict.keys())
    pairs = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairs.append((names[i], names[j]))

    # 限制数量
    if len(pairs) > max_pairs:
        pairs = random.sample(pairs, max_pairs)

    for name_a, name_b in pairs:
        a_vals = feature_dict[name_a]
        b_vals = feature_dict[name_b]
        n = min(len(a_vals), len(b_vals))

        # 乘法交互
        features[f'{name_a}_x_{name_b}'] = [a_vals[i] * b_vals[i] for i in range(n)]
        # 加法交互
        features[f'{name_a}_plus_{name_b}'] = [a_vals[i] + b_vals[i] for i in range(n)]
        # 减法交互
        features[f'{name_a}_minus_{name_b}'] = [a_vals[i] - b_vals[i] for i in range(n)]
        # 比率交互
        features[f'{name_a}_div_{name_b}'] = [a_vals[i] / b_vals[i] if b_vals[i] != 0 else 0.0 for i in range(n)]

    return features


def generate_polynomial_features(feature_dict: Dict[str, List[float]],
                                degree: int = 2) -> Dict[str, List[float]]:
    """生成多项式特征"""
    features = {}
    for name, values in feature_dict.items():
        for d in range(2, degree + 1):
            features[f'{name}_pow{d}'] = [v ** d for v in values]
    return features


# ========== 特征选择 ==========

def variance_threshold_select(feature_dict: Dict[str, List[float]],
                              threshold: float = 0.01) -> Dict:
    """方差阈值选择"""
    results = {}
    selected = []
    dropped = []

    for name, values in feature_dict.items():
        n = len(values)
        if n == 0:
            dropped.append(name)
            continue
        mean = sum(values) / n
        var = sum((v - mean) ** 2 for v in values) / n
        if var >= threshold:
            selected.append(name)
            results[name] = {'variance': round(var, 6), 'selected': True}
        else:
            dropped.append(name)
            results[name] = {'variance': round(var, 6), 'selected': False}

    return {
        'method': 'variance_threshold',
        'threshold': threshold,
        'selected': selected,
        'dropped': dropped,
        'details': results
    }


def correlation_select(feature_dict: Dict[str, List[float]], target: List[float],
                      threshold: float = 0.1) -> Dict:
    """基于与目标相关性的特征选择"""
    results = {}
    correlations = {}

    for name, values in feature_dict.items():
        corr = _pearson_correlation(values, target)
        correlations[name] = corr
        results[name] = {
            'correlation': round(corr, 6),
            'abs_correlation': round(abs(corr), 6),
            'selected': abs(corr) >= threshold
        }

    selected = [name for name, r in results.items() if r['selected']]
    selected.sort(key=lambda n: abs(correlations[n]), reverse=True)

    return {
        'method': 'correlation',
        'threshold': threshold,
        'selected': selected,
        'details': results
    }


def mutual_information_select(feature_dict: Dict[str, List[float]],
                             target: List[float], n_bins: int = 10,
                             top_k: int = 10) -> Dict:
    """基于互信息的特征选择"""
    results = {}

    for name, values in feature_dict.items():
        mi = _mutual_information(values, target, n_bins)
        results[name] = {'mutual_information': round(mi, 6)}

    # 按互信息排序选top_k
    sorted_features = sorted(results.items(), key=lambda x: x[1]['mutual_information'], reverse=True)
    selected = [name for name, _ in sorted_features[:top_k]]

    return {
        'method': 'mutual_information',
        'top_k': top_k,
        'selected': selected,
        'details': results
    }


def _pearson_correlation(x: List[float], y: List[float]) -> float:
    n = min(len(x), len(y))
    if n == 0:
        return 0
    mean_x = sum(x[:n]) / n
    mean_y = sum(y[:n]) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    var_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    var_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    if var_x == 0 or var_y == 0:
        return 0
    return cov / math.sqrt(var_x * var_y)


def _mutual_information(x: List[float], y: List[float], n_bins: int = 10) -> float:
    """简化版互信息计算"""
    n = min(len(x), len(y))
    if n == 0:
        return 0

    # 分箱
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    x_range = x_max - x_min if x_max > x_min else 1
    y_range = y_max - y_min if y_max > y_min else 1

    # 计算联合分布
    joint = Counter()
    x_marginal = Counter()
    y_marginal = Counter()

    for i in range(n):
        xi = min(int((x[i] - x_min) / x_range * n_bins), n_bins - 1)
        yi = min(int((y[i] - y_min) / y_range * n_bins), n_bins - 1)
        joint[(xi, yi)] += 1
        x_marginal[xi] += 1
        y_marginal[yi] += 1

    # 计算互信息
    mi = 0
    for (xi, yi), count in joint.items():
        p_xy = count / n
        p_x = x_marginal[xi] / n
        p_y = y_marginal[yi] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log(p_xy / (p_x * p_y))

    return max(0, mi)


# ========== 特征变换 ==========

def minmax_scale(values: List[float]) -> Tuple[List[float], Dict]:
    """Min-Max 归一化"""
    if not values:
        return [], {}
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val > min_val else 1
    scaled = [(v - min_val) / range_val for v in values]
    return scaled, {'min': min_val, 'max': max_val, 'range': range_val}


def standard_scale(values: List[float]) -> Tuple[List[float], Dict]:
    """标准化"""
    n = len(values)
    if n == 0:
        return [], {}
    mean = sum(values) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 1
    if std == 0:
        std = 1
    scaled = [(v - mean) / std for v in values]
    return scaled, {'mean': mean, 'std': std}


def robust_scale(values: List[float]) -> Tuple[List[float], Dict]:
    """鲁棒缩放（基于分位数）"""
    n = len(values)
    if n == 0:
        return [], {}
    sorted_vals = sorted(values)
    q25 = sorted_vals[n // 4]
    q50 = sorted_vals[n // 2]
    q75 = sorted_vals[3 * n // 4]
    iqr = q75 - q25 if q75 > q25 else 1
    scaled = [(v - q50) / iqr for v in values]
    return scaled, {'q25': q25, 'q50': q50, 'q75': q75, 'iqr': iqr}


def bin_features(values: List[float], n_bins: int = 5,
                strategy: str = 'uniform') -> Tuple[List[int], Dict]:
    """分箱"""
    n = len(values)
    if n == 0:
        return [], {}

    if strategy == 'uniform':
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val > min_val else 1
        bins = [min(int((v - min_val) / range_val * n_bins), n_bins - 1) for v in values]
        edges = [min_val + i * range_val / n_bins for i in range(n_bins + 1)]
    elif strategy == 'quantile':
        sorted_vals = sorted(values)
        bins = [0] * n
        edges = [sorted_vals[int(i * n / n_bins)] for i in range(n_bins + 1)]
        edges[-1] = max(values) + 1
        for i, v in enumerate(values):
            for b in range(n_bins):
                if edges[b] <= v < edges[b + 1]:
                    bins[i] = b
                    break
    else:
        bins = [0] * n
        edges = []

    return bins, {'n_bins': n_bins, 'strategy': strategy, 'edges': edges}


# ========== 特征编码 ==========

def label_encode(values: List[Any]) -> Tuple[List[int], Dict]:
    """标签编码"""
    unique_vals = sorted(set(values))
    mapping = {v: i for i, v in enumerate(unique_vals)}
    encoded = [mapping[v] for v in values]
    return encoded, {'mapping': mapping, 'n_classes': len(unique_vals)}


def frequency_encode(values: List[Any]) -> Tuple[List[float], Dict]:
    """频率编码"""
    counter = Counter(values)
    n = len(values)
    mapping = {v: count / n for v, count in counter.items()}
    encoded = [mapping[v] for v in values]
    return encoded, {'mapping': mapping}


def target_encode(values: List[Any], target: List[float],
                 smoothing: float = 1.0) -> Tuple[List[float], Dict]:
    """目标编码"""
    n = len(values)
    global_mean = sum(target) / n if n > 0 else 0

    # 计算每类目标均值
    class_stats = defaultdict(lambda: {'sum': 0, 'count': 0})
    for v, t in zip(values, target):
        class_stats[v]['sum'] += t
        class_stats[v]['count'] += 1

    # 平滑编码
    mapping = {}
    for v, stats in class_stats.items():
        smooth_mean = (stats['sum'] + smoothing * global_mean) / (stats['count'] + smoothing)
        mapping[v] = smooth_mean

    encoded = [mapping.get(v, global_mean) for v in values]
    return encoded, {'mapping': mapping, 'global_mean': global_mean, 'smoothing': smoothing}


# ========== 特征降维 ==========

def pca_reduce(feature_dict: Dict[str, List[float]], n_components: int = 2) -> Dict:
    """简化版 PCA 降维"""
    names = list(feature_dict.keys())
    n_features = len(names)
    n_samples = len(feature_dict[names[0]]) if names else 0

    if n_features == 0 or n_samples == 0:
        return {'error': '无数据'}

    # 构建数据矩阵
    matrix = [feature_dict[name] for name in names]

    # 中心化
    centered = []
    for row in matrix:
        mean = sum(row) / n_samples
        centered.append([v - mean for v in row])

    # 计算协方差矩阵
    cov = [[0.0] * n_features for _ in range(n_features)]
    for i in range(n_features):
        for j in range(n_features):
            cov[i][j] = sum(centered[i][k] * centered[j][k] for k in range(n_samples)) / max(n_samples - 1, 1)

    # 简化：使用对角线作为主成分（近似）
    explained_variance = [cov[i][i] for i in range(n_features)]
    total_var = sum(explained_variance)

    # 按方差排序
    sorted_idx = sorted(range(n_features), key=lambda i: explained_variance[i], reverse=True)
    selected = sorted_idx[:n_components]

    # 投影到选定成分
    reduced = [[centered[idx][k] for idx in selected] for k in range(n_samples)]

    return {
        'method': 'pca',
        'n_components': n_components,
        'selected_features': [names[i] for i in selected],
        'explained_variance': [round(explained_variance[i] / total_var, 6) for i in selected],
        'total_explained': round(sum(explained_variance[i] for i in selected) / total_var, 6),
        'reduced_dim': n_components
    }


# ========== 特征工程服务 ==========

class AIFeatureEngineering:
    """AI 特征工程服务"""

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
                    CREATE TABLE IF NOT EXISTS feature_engineering_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_name TEXT,
                        operation TEXT,
                        config TEXT,
                        input_features TEXT,
                        output_features TEXT,
                        statistics TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化特征工程数据库失败: {e}")

    def auto_engineer(self, feature_dict: Dict[str, List[float]],
                     target: List[float] = None,
                     max_features: int = 50) -> Dict:
        """自动特征工程管道"""
        original_count = len(feature_dict)
        all_features = dict(feature_dict)

        # 1. 生成数值衍生特征
        for name, values in list(feature_dict.items()):
            if all(isinstance(v, (int, float)) for v in values):
                derived = generate_numeric_features(values, name)
                all_features.update(derived)

        # 2. 生成交互特征
        numeric_features = {k: v for k, v in feature_dict.items()
                           if all(isinstance(x, (int, float)) for x in v)}
        if len(numeric_features) >= 2:
            interactions = generate_interaction_features(numeric_features, max_pairs=5)
            all_features.update(interactions)

        # 3. 生成多项式特征
        poly = generate_polynomial_features(numeric_features, degree=2)
        all_features.update(poly)

        generated_count = len(all_features) - original_count

        # 4. 特征选择
        selection_result = None
        if target and len(all_features) > max_features:
            selection_result = correlation_select(all_features, target, threshold=0.05)
            selected_features = {k: all_features[k] for k in selection_result['selected'][:max_features]}
        else:
            # 方差选择
            selection_result = variance_threshold_select(all_features, threshold=0.001)
            selected_features = {k: all_features[k] for k in selection_result['selected']}

        # 5. 统计
        task_id = f"FE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        stats = {
            'original_features': original_count,
            'generated_features': generated_count,
            'total_before_selection': len(all_features),
            'selected_features': len(selected_features),
            'feature_names': list(selected_features.keys())
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO feature_engineering_tasks
                    (task_id, task_name, operation, config, input_features,
                     output_features, statistics, created_at)
                    VALUES (?, ?, 'auto_engineer', ?, ?, ?, ?, ?)
                ''', (
                    task_id, f'自动特征工程-{task_id[-6:]}',
                    json.dumps({'max_features': max_features}, ensure_ascii=False),
                    json.dumps(list(feature_dict.keys())),
                    json.dumps(list(selected_features.keys())),
                    json.dumps(stats, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

        return {
            'success': True,
            'task_id': task_id,
            'statistics': stats,
            'selected_features': selected_features,
            'selection_method': selection_result.get('method')
        }

    def analyze_features(self, feature_dict: Dict[str, List[float]],
                        target: List[float] = None) -> Dict:
        """特征分析报告"""
        analysis = {}

        for name, values in feature_dict.items():
            n = len(values)
            if n == 0:
                continue

            # 基本统计
            mean = sum(values) / n
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0
            sorted_vals = sorted(values)
            q25 = sorted_vals[n // 4]
            q50 = sorted_vals[n // 2]
            q75 = sorted_vals[3 * n // 4]

            feature_stats = {
                'count': n,
                'mean': round(mean, 6),
                'std': round(std, 6),
                'min': round(min(values), 6),
                'max': round(max(values), 6),
                'q25': round(q25, 6),
                'q50': round(q50, 6),
                'q75': round(q75, 6),
                'missing_count': sum(1 for v in values if v is None),
                'unique_count': len(set(values))
            }

            # 与目标的相关性
            if target:
                feature_stats['correlation_with_target'] = round(_pearson_correlation(values, target), 6)
                feature_stats['mutual_info_with_target'] = round(_mutual_information(values, target), 6)

            analysis[name] = feature_stats

        # 冗余检测
        redundancy = {}
        names = list(feature_dict.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                corr = _pearson_correlation(feature_dict[names[i]], feature_dict[names[j]])
                if abs(corr) > 0.8:
                    redundancy[f'{names[i]}_vs_{names[j]}'] = round(corr, 6)

        return {
            'total_features': len(analysis),
            'feature_analysis': analysis,
            'redundant_pairs': redundancy,
            'high_correlation_count': len(redundancy)
        }

    def transform_features(self, feature_dict: Dict[str, List[float]],
                          method: str = 'standard') -> Dict:
        """批量特征变换"""
        transformers = {
            'minmax': minmax_scale,
            'standard': standard_scale,
            'robust': robust_scale
        }

        if method not in transformers:
            return {'success': False, 'error': f'不支持的变换: {method}'}

        transformed = {}
        params = {}
        for name, values in feature_dict.items():
            result, p = transformers[method](values)
            transformed[name] = result
            params[name] = p

        return {
            'success': True,
            'method': method,
            'transformed_features': transformed,
            'parameters': params
        }

    def encode_categorical(self, values: List[Any], target: List[float] = None,
                          method: str = 'label') -> Dict:
        """分类特征编码"""
        if method == 'label':
            encoded, info = label_encode(values)
        elif method == 'frequency':
            encoded, info = frequency_encode(values)
        elif method == 'target':
            if target is None:
                return {'success': False, 'error': '目标编码需要target参数'}
            encoded, info = target_encode(values, target)
        else:
            return {'success': False, 'error': f'不支持的编码: {method}'}

        return {
            'success': True,
            'method': method,
            'encoded_values': encoded,
            'info': info
        }

    def select_features(self, feature_dict: Dict[str, List[float]],
                       target: List[float] = None, method: str = 'variance',
                       **kwargs) -> Dict:
        """特征选择"""
        if method == 'variance':
            return variance_threshold_select(feature_dict, kwargs.get('threshold', 0.01))
        elif method == 'correlation':
            if target is None:
                return {'error': '相关性选择需要target'}
            return correlation_select(feature_dict, target, kwargs.get('threshold', 0.1))
        elif method == 'mutual_info':
            if target is None:
                return {'error': '互信息选择需要target'}
            return mutual_information_select(feature_dict, target,
                                           kwargs.get('n_bins', 10),
                                           kwargs.get('top_k', 10))
        else:
            return {'error': f'不支持的选择方法: {method}'}

    def reduce_dimensions(self, feature_dict: Dict[str, List[float]],
                         method: str = 'pca', n_components: int = 2) -> Dict:
        """特征降维"""
        if method == 'pca':
            return pca_reduce(feature_dict, n_components)
        else:
            return {'error': f'不支持的降维方法: {method}'}

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM feature_engineering_tasks')
                total_tasks = cursor.fetchone()[0]
                cursor.execute("SELECT operation, COUNT(*) FROM feature_engineering_tasks GROUP BY operation")
                op_dist = {r[0]: r[1] for r in cursor.fetchall()}
            return {
                'total_tasks': total_tasks,
                'operation_distribution': op_dist
            }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    fe = AIFeatureEngineering()

    # 生成测试数据
    random.seed(42)
    feature_dict = {
        'age': [random.randint(18, 70) for _ in range(100)],
        'income': [random.gauss(50000, 15000) for _ in range(100)],
        'score': [random.uniform(0, 100) for _ in range(100)]
    }
    target = [1 if f['income'][i] > 50000 and f['age'][i] > 30 else 0 for i in range(100)]

    print("=== 特征分析 ===")
    analysis = fe.analyze_features(feature_dict, target)
    for name, stats in analysis['feature_analysis'].items():
        print(f"  {name}: mean={stats['mean']}, std={stats['std']}, corr={stats.get('correlation_with_target')}")
    print(f"  冗余对: {analysis['high_correlation_count']}")

    print("\n=== 特征变换 ===")
    transformed = fe.transform_features(feature_dict, method='standard')
    print(f"  方法: {transformed['method']}")
    print(f"  参数: {transformed['parameters']['age']}")

    print("\n=== 特征选择（方差）===")
    sel = fe.select_features(feature_dict, method='variance', threshold=0.1)
    print(f"  选择: {sel['selected']}")
    print(f"  丢弃: {sel['dropped']}")

    print("\n=== 特征选择（相关性）===")
    sel = fe.select_features(feature_dict, target=target, method='correlation', threshold=0.05)
    print(f"  选择: {sel['selected']}")

    print("\n=== 特征选择（互信息）===")
    sel = fe.select_features(feature_dict, target=target, method='mutual_info', top_k=2)
    print(f"  Top 2: {sel['selected']}")

    print("\n=== 自动特征工程 ===")
    auto_result = fe.auto_engineer(feature_dict, target, max_features=20)
    print(f"  原始特征: {auto_result['statistics']['original_features']}")
    print(f"  生成特征: {auto_result['statistics']['generated_features']}")
    print(f"  选择特征: {auto_result['statistics']['selected_features']}")
    print(f"  选择方法: {auto_result['selection_method']}")

    print("\n=== 分类编码 ===")
    categories = ['cat', 'dog', 'cat', 'bird', 'dog', 'cat', 'bird'] * 15
    encoded = fe.encode_categorical(categories, method='frequency')
    print(f"  方法: {encoded['method']}")
    print(f"  映射: {encoded['info']['mapping']}")

    # 目标编码
    cat_target = [1.0, 0.5, 1.2, 0.3, 0.4, 0.9, 0.2] * 15
    encoded = fe.encode_categorical(categories, target=cat_target, method='target')
    print(f"  目标编码映射: {encoded['info']['mapping']}")

    print("\n=== 特征降维 ===")
    pca = fe.reduce_dimensions(feature_dict, method='pca', n_components=2)
    print(f"  方法: {pca['method']}")
    print(f"  选择的特征: {pca['selected_features']}")
    print(f"  解释方差: {pca['explained_variance']}")
    print(f"  总解释: {pca['total_explained']}")

    print(f"\n统计: {fe.get_statistics()}")

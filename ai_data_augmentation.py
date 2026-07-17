#!/usr/bin/env python3
"""
MTSCOS AI 数据增强服务 (v15.0.0)
===================================
AI 数据增强和样本扩充服务。

核心能力：
1. 文本增强 - 同义词替换/回译/随机删除/插入
2. 数值增强 - 噪声注入/SMOTE/插值
3. 图像增强 - 翻转/旋转/裁剪/颜色抖动（模拟）
4. 时序增强 - 时间偏移/缩放/抖动
5. Mixup - 混合样本增强
6. CutMix - 区域混合增强
7. 增强策略 - 自动增强策略搜索
8. 增强报告 - 增强效果评估
"""
import os
import json
import math
import random
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_data_augmentation.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIDataAugmentation')


# ========== 文本增强 ==========

# 简单同义词词典
SYNONYMS = {
    '好': ['优秀', '棒', '佳', '出色'],
    '坏': ['差', '糟', '劣', '不好'],
    '大': ['巨大', '庞大', '大型', '硕大'],
    '小': ['微小', '小巧', '小型', '迷你'],
    '快': ['迅速', '敏捷', '快速', '迅捷'],
    '慢': ['缓慢', '迟缓', '慢悠悠'],
    '美丽': ['漂亮', '好看', '优美', '绚丽'],
    '聪明': ['智慧', '机智', '聪慧', '灵巧'],
    '开心': ['快乐', '高兴', '愉悦', '欢喜'],
    '悲伤': ['难过', '伤心', '哀伤', '忧愁'],
    'good': ['great', 'excellent', 'fine', 'nice'],
    'bad': ['poor', 'terrible', 'awful', 'worse'],
    'happy': ['joyful', 'glad', 'pleased', 'delighted'],
    'sad': ['unhappy', 'sorrowful', 'depressed', 'gloomy'],
    'fast': ['quick', 'rapid', 'swift', 'speedy'],
    'slow': ['sluggish', 'gradual', 'leisurely'],
}

STOPWORDS = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', 'the', 'a', 'an', 'is', 'are', 'was', 'were'}


def synonym_replacement(text: str, n: int = 3) -> str:
    """同义词替换"""
    words = text.split()
    replaced = 0
    for i, word in enumerate(words):
        clean = word.lower().strip('.,!?;:')
        if clean in SYNONYMS and random.random() < 0.3:
            synonym = random.choice(SYNONYMS[clean])
            words[i] = word.replace(clean, synonym)
            replaced += 1
            if replaced >= n:
                break
    return ' '.join(words)


def random_deletion(text: str, p: float = 0.1) -> str:
    """随机删除词语"""
    words = text.split()
    if len(words) <= 1:
        return text
    result = [w for w in words if random.random() > p]
    if not result:
        result = [random.choice(words)]
    return ' '.join(result)


def random_insertion(text: str, n: int = 2) -> str:
    """随机插入词语"""
    words = text.split()
    if not words:
        return text
    for _ in range(n):
        idx = random.randint(0, len(words))
        # 随机选一个已有词插入
        insert_word = random.choice(words)
        words.insert(idx, insert_word)
    return ' '.join(words)


def random_swap(text: str, n: int = 2) -> str:
    """随机交换词语位置"""
    words = text.split()
    if len(words) < 2:
        return text
    for _ in range(n):
        idx1, idx2 = random.sample(range(len(words)), 2)
        words[idx1], words[idx2] = words[idx2], words[idx1]
    return ' '.join(words)


def back_translation_simulate(text: str) -> str:
    """模拟回译增强（简化版）"""
    # 模拟翻译过程中的词序变化
    words = text.split()
    if len(words) <= 2:
        return text
    # 随机调整一些词序
    for _ in range(random.randint(1, 2)):
        idx = random.randint(0, len(words) - 2)
        words[idx], words[idx + 1] = words[idx + 1], words[idx]
    return ' '.join(words)


TEXT_AUGMENTORS = {
    'synonym': synonym_replacement,
    'deletion': random_deletion,
    'insertion': random_insertion,
    'swap': random_swap,
    'back_translation': back_translation_simulate,
}


# ========== 数值增强 ==========

def noise_injection(values: List[float], noise_factor: float = 0.05,
                   noise_type: str = 'gaussian') -> List[float]:
    """噪声注入"""
    if not values:
        return []
    n = len(values)
    if noise_type == 'gaussian':
        mean = sum(values) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 1
        noise = [random.gauss(0, std * noise_factor) for _ in range(n)]
    elif noise_type == 'uniform':
        mean = sum(values) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 1
        noise = [random.uniform(-std * noise_factor, std * noise_factor) for _ in range(n)]
    else:
        noise = [0] * n

    return [v + noise[i] for i, v in enumerate(values)]


def smote_sample(features: List[List[float]], labels: List[int],
                minority_class: int, n_synthetic: int = 50,
                k: int = 5) -> Tuple[List[List[float]], List[int]]:
    """SMOTE 过采样"""
    # 找出少数类样本
    minority_indices = [i for i, l in enumerate(labels) if l == minority_class]
    if not minority_indices:
        return [], []

    minority_features = [features[i] for i in minority_indices]
    n_minority = len(minority_features)
    if n_minority < 2:
        return [], []

    synthetic = []
    synthetic_labels = []

    for _ in range(n_synthetic):
        # 随机选一个少数类样本
        idx = random.randint(0, n_minority - 1)
        sample = minority_features[idx]

        # 找k近邻（简化：欧氏距离）
        distances = []
        for j in range(n_minority):
            if j != idx:
                dist = math.sqrt(sum((sample[d] - minority_features[j][d]) ** 2
                                    for d in range(len(sample))))
                distances.append((dist, j))

        distances.sort()
        knn_indices = [d[1] for d in distances[:k]] if distances else []

        if knn_indices:
            # 选一个邻居
            neighbor_idx = random.choice(knn_indices)
            neighbor = minority_features[neighbor_idx]

            # 插值生成新样本
            gap = random.random()
            new_sample = [sample[d] + gap * (neighbor[d] - sample[d])
                         for d in range(len(sample))]
            synthetic.append(new_sample)
            synthetic_labels.append(minority_class)

    return synthetic, synthetic_labels


def interpolate_samples(sample_a: List[float], sample_b: List[float],
                       alpha: float = None) -> List[float]:
    """线性插值两个样本"""
    if alpha is None:
        alpha = random.random()
    return [a + alpha * (b - a) for a, b in zip(sample_a, sample_b)]


# ========== Mixup / CutMix ==========

def mixup(features_a: List[float], features_b: List[float],
         label_a: Any, label_b: Any,
         alpha: float = 0.2) -> Dict:
    """Mixup 增强"""
    lam = random.betavariate(alpha, alpha) if alpha > 0 else 0.5
    mixed_features = [a * lam + b * (1 - lam) for a, b in zip(features_a, features_b)]
    return {
        'features': mixed_features,
        'label_a': label_a,
        'label_b': label_b,
        'lambda': round(lam, 6)
    }


def cutmix_numeric(features_a: List[float], features_b: List[float],
                  label_a: Any, label_b: Any,
                  alpha: float = 0.2) -> Dict:
    """CutMix 数值版（交换一段特征）"""
    lam = random.betavariate(alpha, alpha) if alpha > 0 else 0.5
    n = len(features_a)
    cut_point = int(n * lam)

    mixed = list(features_a[:cut_point]) + list(features_b[cut_point:])
    actual_lam = cut_point / n

    return {
        'features': mixed,
        'label_a': label_a,
        'label_b': label_b,
        'lambda': round(actual_lam, 6),
        'cut_point': cut_point
    }


# ========== 时序增强 ==========

def time_shift(values: List[float], shift: int = None,
               mode: str = 'wrap') -> List[float]:
    """时间偏移"""
    n = len(values)
    if n == 0:
        return []
    if shift is None:
        shift = random.randint(-n // 4, n // 4)

    if mode == 'wrap':
        shift = shift % n
        return values[shift:] + values[:shift]
    elif mode == 'reflect':
        result = list(values)
        for i in range(n):
            src = i + shift
            if 0 <= src < n:
                result[i] = values[src]
        return result
    else:
        result = [0.0] * n
        for i in range(n):
            src = i + shift
            if 0 <= src < n:
                result[i] = values[src]
        return result


def time_scale(values: List[float], scale_factor: float = None) -> List[float]:
    """时间缩放"""
    if scale_factor is None:
        scale_factor = random.uniform(0.8, 1.2)
    n = len(values)
    new_n = max(1, int(n * scale_factor))
    result = []
    for i in range(new_n):
        src_idx = i / scale_factor
        src_low = int(src_idx)
        src_high = min(src_low + 1, n - 1)
        frac = src_idx - src_low
        result.append(values[src_low] * (1 - frac) + values[src_high] * frac)
    return result


def time_jitter(values: List[float], sigma: float = 0.01) -> List[float]:
    """时间抖动"""
    return [v + random.gauss(0, sigma) for v in values]


def time_warp(values: List[float], n_knots: int = 4,
              sigma: float = 0.2) -> List[float]:
    """时间扭曲"""
    n = len(values)
    if n < 4:
        return list(values)

    # 生成扭曲点
    knot_positions = [0] + sorted(random.sample(range(1, n - 1), n_knots - 2)) + [n - 1]
    knot_warps = [0] + [random.gauss(0, sigma) for _ in range(n_knots - 2)] + [0]

    # 插值
    result = []
    for i in range(n):
        # 找到当前所在的段
        for j in range(len(knot_positions) - 1):
            if knot_positions[j] <= i <= knot_positions[j + 1]:
                frac = (i - knot_positions[j]) / max(knot_positions[j + 1] - knot_positions[j], 1)
                warp = knot_warps[j] * (1 - frac) + knot_warps[j + 1] * frac
                src_idx = int(i + warp * n * 0.1)
                src_idx = max(0, min(n - 1, src_idx))
                result.append(values[src_idx])
                break
    return result


# ========== 数据增强服务 ==========

class AIDataAugmentation:
    """AI 数据增强服务"""

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
                    CREATE TABLE IF NOT EXISTS augmentation_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_name TEXT,
                        data_type TEXT,
                        method TEXT,
                        config TEXT,
                        original_count INTEGER,
                        augmented_count INTEGER,
                        created_at TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化数据增强数据库失败: {e}")

    def augment_text(self, texts: List[str], methods: List[str] = None,
                    n_aug_per_sample: int = 2) -> Dict:
        """文本数据增强"""
        methods = methods or ['synonym', 'deletion', 'swap']
        augmented = []
        original_count = len(texts)

        for text in texts:
            for _ in range(n_aug_per_sample):
                method = random.choice(methods)
                aug_fn = TEXT_AUGMENTORS.get(method)
                if aug_fn:
                    aug_text = aug_fn(text)
                    augmented.append({
                        'original': text,
                        'augmented': aug_text,
                        'method': method
                    })

        task_id = self._save_task('text', methods, original_count, len(augmented))
        return {
            'success': True,
            'task_id': task_id,
            'original_count': original_count,
            'augmented_count': len(augmented),
            'methods': methods,
            'augmented_samples': augmented[:10]  # 预览
        }

    def augment_numeric(self, features: List[List[float]], labels: List[int] = None,
                       methods: List[str] = None,
                       target_count: int = None) -> Dict:
        """数值数据增强"""
        methods = methods or ['noise', 'mixup']
        augmented_features = list(features)
        augmented_labels = list(labels) if labels else []
        original_count = len(features)

        # 噪声注入
        if 'noise' in methods and features:
            n_noise = min(target_count or original_count, original_count)
            for _ in range(n_noise):
                idx = random.randint(0, len(features) - 1)
                noisy = noise_injection(features[idx], noise_factor=0.05)
                augmented_features.append(noisy)
                if labels:
                    augmented_labels.append(labels[idx])

        # SMOTE
        if 'smote' in methods and labels:
            class_counts = defaultdict(int)
            for l in labels:
                class_counts[l] += 1
            minority_class = min(class_counts, key=class_counts.get)
            synth_features, synth_labels = smote_sample(
                features, labels, minority_class,
                n_synthetic=min(50, target_count or 50)
            )
            augmented_features.extend(synth_features)
            augmented_labels.extend(synth_labels)

        # Mixup
        if 'mixup' in methods and len(features) >= 2:
            n_mixup = min(target_count or original_count, original_count)
            for _ in range(n_mixup):
                idx_a, idx_b = random.sample(range(len(features)), 2)
                result = mixup(features[idx_a], features[idx_b],
                              labels[idx_a] if labels else None,
                              labels[idx_b] if labels else None)
                augmented_features.append(result['features'])
                if labels:
                    augmented_labels.append(result['label_a'])

        # CutMix
        if 'cutmix' in methods and len(features) >= 2:
            n_cutmix = min(target_count or original_count, original_count)
            for _ in range(n_cutmix):
                idx_a, idx_b = random.sample(range(len(features)), 2)
                result = cutmix_numeric(features[idx_a], features[idx_b],
                                       labels[idx_a] if labels else None,
                                       labels[idx_b] if labels else None)
                augmented_features.append(result['features'])
                if labels:
                    augmented_labels.append(result['label_a'])

        task_id = self._save_task('numeric', methods, original_count,
                                  len(augmented_features) - original_count)

        return {
            'success': True,
            'task_id': task_id,
            'original_count': original_count,
            'augmented_count': len(augmented_features) - original_count,
            'total_count': len(augmented_features),
            'methods': methods,
            'augmented_features': augmented_features[original_count:original_count + 5],  # 预览
            'augmented_labels': augmented_labels[original_count:original_count + 5] if labels else None
        }

    def augment_timeseries(self, series: List[float], methods: List[str] = None,
                          n_augmentations: int = 5) -> Dict:
        """时序数据增强"""
        methods = methods or ['shift', 'scale', 'jitter', 'warp']
        augmented = []

        for _ in range(n_augmentations):
            method = random.choice(methods)
            if method == 'shift':
                aug = time_shift(series)
            elif method == 'scale':
                aug = time_scale(series)
            elif method == 'jitter':
                aug = time_jitter(series)
            elif method == 'warp':
                aug = time_warp(series)
            else:
                aug = list(series)
            augmented.append({
                'method': method,
                'values': aug
            })

        task_id = self._save_task('timeseries', methods, 1, len(augmented))

        return {
            'success': True,
            'task_id': task_id,
            'original_length': len(series),
            'augmented_count': len(augmented),
            'methods': methods,
            'augmented_samples': augmented[:5]
        }

    def auto_augment(self, data_type: str, data: Any,
                    labels: Any = None,
                    target_ratio: float = 2.0) -> Dict:
        """自动增强（根据数据类型自动选择策略）"""
        original_count = len(data) if isinstance(data, list) else 1
        target_count = int(original_count * target_ratio)

        if data_type == 'text':
            return self.augment_text(data, n_aug_per_sample=int(target_ratio))
        elif data_type == 'numeric':
            return self.augment_numeric(data, labels, target_count=target_count)
        elif data_type == 'timeseries':
            return self.augment_timeseries(data, n_augmentations=int(target_ratio))
        else:
            return {'success': False, 'error': f'不支持的数据类型: {data_type}'}

    def evaluate_augmentation(self, original: List, augmented: List,
                             eval_fn: Callable = None) -> Dict:
        """评估增强效果"""
        if not augmented:
            return {'error': '无增强数据'}

        # 基本统计
        orig_size = len(original)
        aug_size = len(augmented)
        expansion_ratio = aug_size / max(orig_size, 1)

        # 多样性评估（简化：唯一样本比例）
        if isinstance(augmented[0], str):
            unique_aug = len(set(augmented))
            diversity = unique_aug / max(aug_size, 1)
        elif isinstance(augmented[0], list):
            unique_set = set()
            for sample in augmented:
                unique_set.add(tuple(round(x, 4) for x in sample))
            diversity = len(unique_set) / max(aug_size, 1)
        else:
            diversity = 0

        # 如果提供了评估函数
        quality_score = None
        if eval_fn:
            try:
                quality_score = eval_fn(augmented)
            except Exception:
                quality_score = None

        return {
            'original_size': orig_size,
            'augmented_size': aug_size,
            'expansion_ratio': round(expansion_ratio, 2),
            'diversity_score': round(diversity, 4),
            'quality_score': round(quality_score, 4) if quality_score else None,
            'novelty_rate': round(1 - diversity, 4)  # 重复率
        }

    def _save_task(self, data_type: str, methods: List[str],
                  original_count: int, augmented_count: int) -> str:
        task_id = f"AUG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO augmentation_tasks
                    (task_id, task_name, data_type, method, config,
                     original_count, augmented_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id, f'增强任务-{task_id[-6:]}', data_type,
                    ','.join(methods), json.dumps({'methods': methods}),
                    original_count, augmented_count, datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass
        return task_id

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM augmentation_tasks')
                total_tasks = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(original_count), SUM(augmented_count) FROM augmentation_tasks')
                row = cursor.fetchone()
                total_original = row[0] or 0
                total_augmented = row[1] or 0
                cursor.execute("SELECT data_type, COUNT(*) FROM augmentation_tasks GROUP BY data_type")
                type_dist = {r[0]: r[1] for r in cursor.fetchall()}
            return {
                'total_tasks': total_tasks,
                'total_original_samples': total_original,
                'total_augmented_samples': total_augmented,
                'data_type_distribution': type_dist
            }
        except Exception as e:
            return {'error': str(e)}


# 导入缺失的类型
from typing import Callable

# ========== 模块入口 ==========

if __name__ == '__main__':
    aug = AIDataAugmentation()

    print("=== 文本增强 ===")
    texts = ['今天天气很好 很开心', '这个产品非常好 值得购买', '速度很快 质量不错']
    result = aug.augment_text(texts, methods=['synonym', 'swap', 'deletion'], n_aug_per_sample=3)
    print(f"  原始: {result['original_count']}, 增强: {result['augmented_count']}")
    for s in result['augmented_samples'][:3]:
        print(f"    [{s['method']}] {s['original']} → {s['augmented']}")

    print("\n=== 数值增强 ===")
    features = [[random.gauss(0, 1) for _ in range(5)] for _ in range(20)]
    labels = [random.choice([0, 1]) for _ in range(20)]
    result = aug.augment_numeric(features, labels, methods=['noise', 'mixup'], target_count=40)
    print(f"  原始: {result['original_count']}, 增强: {result['augmented_count']}, 总计: {result['total_count']}")

    print("\n=== SMOTE 增强 ===")
    # 制造不平衡数据
    imbalanced_features = [[random.gauss(0, 1) for _ in range(3)] for _ in range(50)]
    imbalanced_labels = [0] * 45 + [1] * 5  # 严重不平衡
    result = aug.augment_numeric(imbalanced_features, imbalanced_labels,
                                methods=['smote'], target_count=50)
    print(f"  原始: {result['original_count']}, 增强: {result['augmented_count']}")

    print("\n=== Mixup ===")
    sample_a = [1.0, 2.0, 3.0, 4.0]
    sample_b = [5.0, 6.0, 7.0, 8.0]
    mixed = mixup(sample_a, sample_b, 0, 1, alpha=0.2)
    print(f"  A: {sample_a}")
    print(f"  B: {sample_b}")
    print(f"  混合: {[round(x, 4) for x in mixed['features']]} (lambda={mixed['lambda']})")

    print("\n=== CutMix ===")
    cut = cutmix_numeric(sample_a, sample_b, 0, 1, alpha=0.2)
    print(f"  混合: {[round(x, 4) for x in cut['features']]} (cut={cut['cut_point']})")

    print("\n=== 时序增强 ===")
    series = [math.sin(i * 0.1) for i in range(50)]
    result = aug.augment_timeseries(series, methods=['shift', 'scale', 'jitter', 'warp'],
                                   n_augmentations=5)
    print(f"  原始长度: {result['original_length']}, 增强数: {result['augmented_count']}")
    for s in result['augmented_samples'][:3]:
        print(f"    [{s['method']}] 前5值: {[round(v, 4) for v in s['values'][:5]]}")

    print("\n=== 自动增强 ===")
    auto_result = aug.auto_augment('text', texts, target_ratio=3.0)
    print(f"  类型: text, 原始: {auto_result['original_count']}, 增强: {auto_result['augmented_count']}")

    print("\n=== 增强评估 ===")
    aug_texts = [s['augmented'] for s in result.get('augmented_samples', [])] if 'augmented_samples' in result else []
    if not aug_texts:
        aug_texts = ['增强文本1', '增强文本2', '增强文本3']
    eval_result = aug.evaluate_augmentation(texts, aug_texts + ['额外文本1', '额外文本2'])
    print(f"  扩展比: {eval_result['expansion_ratio']}")
    print(f"  多样性: {eval_result['diversity_score']}")
    print(f"  重复率: {eval_result['novelty_rate']}")

    print(f"\n统计: {aug.get_statistics()}")

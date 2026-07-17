#!/usr/bin/env python3
"""
MTSCOS AI 元学习服务 (v14.9.0)
===================================
AI 元学习和 Few-shot 学习管理服务。

核心能力：
1. Few-shot 学习 - 原型网络、匹配网络
2. 元学习率 - 学习率自适应元学习
3. 任务分布学习 - 跨任务知识迁移
4. 原型计算 - 类原型向量和距离分类
5. MAML 简化版 - 模型不可知元学习
6. 经验回放 - 任务经验存储和复用
7. 快速适应 - 少样本快速微调
8. 元学习报告 - 跨任务性能分析
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_meta_learning.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIMetaLearning')


# ========== 距离函数 ==========

def euclidean_distance(a: List[float], b: List[float]) -> float:
    """欧氏距离"""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def cosine_distance(a: List[float], b: List[float]) -> float:
    """余弦距离"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(y ** 2 for y in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1 - dot / (norm_a * norm_b)


DISTANCE_FUNCTIONS = {
    'euclidean': euclidean_distance,
    'cosine': cosine_distance,
}


# ========== 原型网络 ==========

class PrototypicalNetwork:
    """原型网络：Few-shot 分类"""

    def __init__(self, distance_metric: str = 'euclidean'):
        self.distance_fn = DISTANCE_FUNCTIONS.get(distance_metric, euclidean_distance)
        self.prototypes: Dict[str, List[float]] = {}
        self.support_counts: Dict[str, int] = {}

    def compute_prototype(self, support_set: List[Tuple[List[float], str]]) -> Dict:
        """从支持集计算类原型"""
        class_features = defaultdict(list)
        for features, label in support_set:
            class_features[label].append(features)

        for label, features_list in class_features.items():
            # 原型 = 类内特征均值
            n = len(features_list)
            dim = len(features_list[0]) if features_list else 0
            prototype = [0.0] * dim
            for features in features_list:
                for i in range(dim):
                    prototype[i] += features[i]
            prototype = [p / n for p in prototype]
            self.prototypes[label] = prototype
            self.support_counts[label] = n

        return {
            'num_classes': len(self.prototypes),
            'classes': list(self.prototypes.keys()),
            'support_counts': dict(self.support_counts)
        }

    def predict(self, query_features: List[float], return_distances: bool = False) -> Dict:
        """预测查询样本类别"""
        if not self.prototypes:
            return {'prediction': None, 'error': '无原型可用'}

        distances = {}
        for label, prototype in self.prototypes.items():
            distances[label] = self.distance_fn(query_features, prototype)

        # softmax 转换为概率
        min_dist = min(distances.values())
        exp_dists = {l: math.exp(-(d - min_dist)) for l, d in distances.items()}
        total = sum(exp_dists.values())
        probabilities = {l: e / total for l, e in exp_dists.items()}

        prediction = min(distances, key=distances.get)
        confidence = probabilities[prediction]

        result = {
            'prediction': prediction,
            'confidence': round(confidence, 6),
            'probabilities': {l: round(p, 6) for l, p in probabilities.items()}
        }
        if return_distances:
            result['distances'] = {l: round(d, 6) for l, d in distances.items()}
        return result

    def update_prototype(self, label: str, features: List[float], lr: float = 0.1):
        """增量更新原型"""
        if label in self.prototypes:
            old_proto = self.prototypes[label]
            new_proto = [old + lr * (new - old) for old, new in zip(old_proto, features)]
            self.prototypes[label] = new_proto
            self.support_counts[label] += 1
        else:
            self.prototypes[label] = list(features)
            self.support_counts[label] = 1

    def stats(self) -> Dict:
        return {
            'num_classes': len(self.prototypes),
            'classes': list(self.prototypes.keys()),
            'support_counts': dict(self.support_counts),
            'distance_metric': self.distance_fn.__name__
        }


# ========== 匹配网络 ==========

class MatchingNetwork:
    """匹配网络：基于注意力机制的 Few-shot 分类"""

    def __init__(self, distance_metric: str = 'cosine'):
        self.distance_fn = DISTANCE_FUNCTIONS.get(distance_metric, cosine_distance)
        self.support_set: List[Tuple[List[float], str]] = []

    def set_support(self, support_set: List[Tuple[List[float], str]]):
        """设置支持集"""
        self.support_set = list(support_set)

    def predict(self, query_features: List[float]) -> Dict:
        """预测查询样本"""
        if not self.support_set:
            return {'prediction': None, 'error': '支持集为空'}

        # 计算与支持集每个样本的距离
        distances = []
        for features, label in self.support_set:
            d = self.distance_fn(query_features, features)
            distances.append((d, label))

        # softmax 注意力权重
        min_d = min(d for d, _ in distances)
        weights = [math.exp(-(d - min_d)) for d, _ in distances]
        total = sum(weights)
        weights = [w / total for w in weights]

        # 加权投票
        label_scores = defaultdict(float)
        for w, (_, label) in zip(weights, distances):
            label_scores[label] += w

        prediction = max(label_scores, key=label_scores.get)
        confidence = label_scores[prediction]

        return {
            'prediction': prediction,
            'confidence': round(confidence, 6),
            'label_scores': {l: round(s, 6) for l, s in label_scores.items()}
        }


# ========== MAML 简化版 ==========

class SimplifiedMAML:
    """MAML (Model-Agnostic Meta-Learning) 简化实现"""

    def __init__(self, n_features: int, inner_lr: float = 0.01,
                 outer_lr: float = 0.001, n_inner_steps: int = 5):
        self.n_features = n_features
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.n_inner_steps = n_inner_steps
        # 元参数（全局初始权重）
        self.meta_weights = [random.gauss(0, 0.1) for _ in range(n_features)]
        self.meta_bias = 0.0
        self._task_history = []

    def _predict(self, weights: List[float], bias: float, x: List[float]) -> float:
        return sum(w * xi for w, xi in zip(weights, x)) + bias

    def _inner_loop(self, support_x: List[List[float]], support_y: List[int],
                   query_x: List[List[float]], query_y: List[int]) -> Dict:
        """内循环：在任务上快速适应"""
        # 复制元参数
        weights = list(self.meta_weights)
        bias = self.meta_bias

        # 在支持集上梯度下降
        for step in range(self.n_inner_steps):
            for x, y in zip(support_x, support_y):
                pred = self._predict(weights, bias, x)
                error = y - (1 / (1 + math.exp(-pred)))  # sigmoid
                for i in range(self.n_features):
                    weights[i] += self.inner_lr * error * x[i]
                bias += self.inner_lr * error

        # 在查询集上计算损失
        query_loss = 0
        correct = 0
        for x, y in zip(query_x, query_y):
            pred = self._predict(weights, bias, x)
            proba = 1 / (1 + math.exp(-pred))
            query_loss += -(y * math.log(proba + 1e-10) + (1 - y) * math.log(1 - proba + 1e-10))
            if (proba > 0.5) == (y == 1):
                correct += 1

        return {
            'adapted_weights': weights,
            'adapted_bias': bias,
            'query_loss': query_loss / max(len(query_y), 1),
            'query_accuracy': correct / max(len(query_y), 1)
        }

    def train_step(self, tasks: List[Dict]) -> Dict:
        """元训练一步"""
        total_loss = 0
        total_accuracy = 0
        n_tasks = len(tasks)

        meta_grad_w = [0.0] * self.n_features
        meta_grad_b = 0.0

        for task in tasks:
            result = self._inner_loop(
                task['support_x'], task['support_y'],
                task['query_x'], task['query_y']
            )
            total_loss += result['query_loss']
            total_accuracy += result['query_accuracy']

            # 简化元梯度：使用查询损失对初始参数的近似梯度
            adapted_w = result['adapted_weights']
            for i in range(self.n_features):
                meta_grad_w[i] += (self.meta_weights[i] - adapted_w[i]) / self.inner_lr

        # 更新元参数
        for i in range(self.n_features):
            self.meta_weights[i] -= self.outer_lr * meta_grad_w[i] / n_tasks
        self.meta_bias -= self.outer_lr * meta_grad_b / n_tasks

        avg_loss = total_loss / n_tasks
        avg_acc = total_accuracy / n_tasks

        self._task_history.append({
            'loss': round(avg_loss, 6),
            'accuracy': round(avg_acc, 6)
        })

        return {
            'meta_loss': round(avg_loss, 6),
            'meta_accuracy': round(avg_acc, 6),
            'tasks_trained': n_tasks
        }

    def adapt_to_task(self, support_x: List[List[float]],
                     support_y: List[int], n_steps: int = None) -> Dict:
        """适应新任务"""
        n_steps = n_steps or self.n_inner_steps
        weights = list(self.meta_weights)
        bias = self.meta_bias

        for step in range(n_steps):
            for x, y in zip(support_x, support_y):
                pred = self._predict(weights, bias, x)
                proba = 1 / (1 + math.exp(-pred))
                error = y - proba
                for i in range(self.n_features):
                    weights[i] += self.inner_lr * error * x[i]
                bias += self.inner_lr * error

        return {
            'adapted_weights': [round(w, 6) for w in weights],
            'adapted_bias': round(bias, 6),
            'adaptation_steps': n_steps
        }

    def stats(self) -> Dict:
        return {
            'n_features': self.n_features,
            'inner_lr': self.inner_lr,
            'outer_lr': self.outer_lr,
            'n_inner_steps': self.n_inner_steps,
            'tasks_seen': len(self._task_history),
            'recent_accuracy': self._task_history[-1]['accuracy'] if self._task_history else None,
            'recent_loss': self._task_history[-1]['loss'] if self._task_history else None
        }


# ========== 经验回放 ==========

class ExperienceReplay:
    """任务经验存储和回放"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._experiences: deque = deque(maxlen=max_size)

    def add(self, task_id: str, support_set: List, query_results: Dict,
            task_metadata: Dict = None):
        self._experiences.append({
            'task_id': task_id,
            'support_set': support_set,
            'query_results': query_results,
            'metadata': task_metadata or {},
            'timestamp': datetime.now().isoformat()
        })

    def sample(self, n: int = 5) -> List[Dict]:
        if len(self._experiences) <= n:
            return list(self._experiences)
        return random.sample(list(self._experiences), n)

    def get_by_task(self, task_id: str) -> Optional[Dict]:
        for exp in self._experiences:
            if exp['task_id'] == task_id:
                return exp
        return None

    def stats(self) -> Dict:
        return {
            'total_experiences': len(self._experiences),
            'max_size': self.max_size,
            'task_ids': list(set(e['task_id'] for e in self._experiences))
        }


# ========== 元学习服务 ==========

class AIMetaLearning:
    """AI 元学习服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._proto_networks: Dict[str, PrototypicalNetwork] = {}
        self._matching_nets: Dict[str, MatchingNetwork] = {}
        self._maml_models: Dict[str, SimplifiedMAML] = {}
        self._experience_replay = ExperienceReplay()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meta_learning_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_name TEXT,
                        method TEXT,
                        n_way INTEGER,
                        k_shot INTEGER,
                        config TEXT,
                        status TEXT DEFAULT 'created',
                        accuracy REAL,
                        loss REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meta_learning_episodes (
                        episode_id TEXT PRIMARY KEY,
                        task_id TEXT,
                        method TEXT,
                        support_size INTEGER,
                        query_size INTEGER,
                        accuracy REAL,
                        loss REAL,
                        adaptation_steps INTEGER,
                        created_at TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化元学习数据库失败: {e}")

    # ========== Few-shot 学习 ==========

    def create_fewshot_task(self, task_id: str, task_name: str,
                           method: str = 'prototypical', n_way: int = 5,
                           k_shot: int = 5, config: Dict = None) -> Dict:
        """创建 Few-shot 学习任务"""
        config = config or {}
        distance_metric = config.get('distance_metric', 'euclidean')

        if method == 'prototypical':
            self._proto_networks[task_id] = PrototypicalNetwork(distance_metric)
        elif method == 'matching':
            self._matching_nets[task_id] = MatchingNetwork(distance_metric)
        elif method == 'maml':
            n_features = config.get('n_features', 10)
            self._maml_models[task_id] = SimplifiedMAML(
                n_features=n_features,
                inner_lr=config.get('inner_lr', 0.01),
                outer_lr=config.get('outer_lr', 0.001)
            )
        else:
            return {'success': False, 'error': f'不支持的元学习方法: {method}'}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO meta_learning_tasks
                    (task_id, task_name, method, n_way, k_shot, config, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'created', ?)
                ''', (
                    task_id, task_name, method, n_way, k_shot,
                    json.dumps(config, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True, 'task_id': task_id, 'method': method}

    def fewshot_train(self, task_id: str,
                     support_set: List[Tuple[List[float], str]]) -> Dict:
        """Few-shot 训练（设置支持集）"""
        method = self._get_method(task_id)
        if not method:
            return {'success': False, 'error': '任务不存在'}

        if task_id in self._proto_networks:
            result = self._proto_networks[task_id].compute_prototype(support_set)
        elif task_id in self._matching_nets:
            self._matching_nets[task_id].set_support(support_set)
            result = {'support_size': len(support_set)}
        else:
            return {'success': False, 'error': '不支持的方法'}

        # 更新任务状态
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE meta_learning_tasks SET status = 'trained' WHERE task_id = ?
                ''', (task_id,))
                conn.commit()
        except Exception:
            pass

        return {'success': True, 'task_id': task_id, **result}

    def fewshot_predict(self, task_id: str,
                       query_features: List[float]) -> Dict:
        """Few-shot 预测"""
        if task_id in self._proto_networks:
            result = self._proto_networks[task_id].predict(query_features, return_distances=True)
        elif task_id in self._matching_nets:
            result = self._matching_nets[task_id].predict(query_features)
        else:
            return {'success': False, 'error': '任务不存在或未训练'}

        return {'success': True, 'task_id': task_id, **result}

    # ========== MAML 训练 ==========

    def maml_train(self, task_id: str, tasks: List[Dict]) -> Dict:
        """MAML 元训练"""
        model = self._maml_models.get(task_id)
        if not model:
            return {'success': False, 'error': 'MAML模型不存在'}

        result = model.train_step(tasks)
        return {'success': True, 'task_id': task_id, **result}

    def maml_adapt(self, task_id: str, support_x: List[List[float]],
                  support_y: List[int]) -> Dict:
        """MAML 快速适应新任务"""
        model = self._maml_models.get(task_id)
        if not model:
            return {'success': False, 'error': 'MAML模型不存在'}

        result = model.adapt_to_task(support_x, support_y)
        return {'success': True, 'task_id': task_id, **result}

    # ========== 经验管理 ==========

    def store_experience(self, task_id: str, support_set: List,
                        query_results: Dict, metadata: Dict = None) -> Dict:
        """存储任务经验"""
        self._experience_replay.add(task_id, support_set, query_results, metadata)
        return {'success': True, 'total_experiences': self._experience_replay.stats()['total_experiences']}

    def replay_experiences(self, n: int = 5) -> Dict:
        """回放历史经验"""
        experiences = self._experience_replay.sample(n)
        return {
            'success': True,
            'replayed': len(experiences),
            'experiences': [
                {
                    'task_id': e['task_id'],
                    'timestamp': e['timestamp'],
                    'metadata': e['metadata']
                }
                for e in experiences
            ]
        }

    # ========== 评估 ==========

    def evaluate_episode(self, task_id: str, support_set: List,
                        query_set: List[Tuple[List[float], str]]) -> Dict:
        """评估一个 Few-shot 学习 episode"""
        # 训练
        train_result = self.fewshot_train(task_id, support_set)

        # 预测
        correct = 0
        total = len(query_set)
        predictions = []

        for features, true_label in query_set:
            pred_result = self.fewshot_predict(task_id, features)
            if pred_result.get('success'):
                pred = pred_result.get('prediction')
                predictions.append({
                    'true': true_label,
                    'pred': pred,
                    'correct': pred == true_label,
                    'confidence': pred_result.get('confidence')
                })
                if pred == true_label:
                    correct += 1

        accuracy = correct / max(total, 1)
        episode_id = f"EP-{random.randint(100000, 999999)}"

        # 保存 episode
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO meta_learning_episodes
                    (episode_id, task_id, method, support_size, query_size,
                     accuracy, adaptation_steps, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    episode_id, task_id, self._get_method(task_id),
                    len(support_set), total, accuracy, 0,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

        # 存储经验
        self.store_experience(task_id, support_set, {'accuracy': accuracy})

        return {
            'success': True,
            'episode_id': episode_id,
            'task_id': task_id,
            'support_size': len(support_set),
            'query_size': total,
            'accuracy': round(accuracy, 6),
            'correct': correct,
            'total': total,
            'predictions': predictions[:10]  # 限制前10个
        }

    def _get_method(self, task_id: str) -> Optional[str]:
        if task_id in self._proto_networks:
            return 'prototypical'
        elif task_id in self._matching_nets:
            return 'matching'
        elif task_id in self._maml_models:
            return 'maml'
        return None

    # ========== 查询 ==========

    def list_tasks(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT task_id, task_name, method, n_way, k_shot, status, created_at
                    FROM meta_learning_tasks ORDER BY created_at DESC
                ''')
                return [
                    {
                        'task_id': r[0], 'task_name': r[1], 'method': r[2],
                        'n_way': r[3], 'k_shot': r[4], 'status': r[5], 'created_at': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM meta_learning_tasks')
                total_tasks = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM meta_learning_episodes')
                total_episodes = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(accuracy) FROM meta_learning_episodes')
                avg_accuracy = cursor.fetchone()[0] or 0
                cursor.execute("SELECT method, COUNT(*) FROM meta_learning_tasks GROUP BY method")
                method_dist = {r[0]: r[1] for r in cursor.fetchall()}
            return {
                'total_tasks': total_tasks,
                'total_episodes': total_episodes,
                'avg_accuracy': round(avg_accuracy, 6),
                'method_distribution': method_dist,
                'experience_stats': self._experience_replay.stats()
            }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    ml = AIMetaLearning()

    print("=== 原型网络 Few-shot 学习 ===")
    ml.create_fewshot_task('proto-task', '原型网络任务', 'prototypical', n_way=3, k_shot=5)

    # 生成支持集
    support_set = []
    for class_id in range(3):
        for _ in range(5):
            features = [random.gauss(class_id * 2, 0.5) for _ in range(10)]
            support_set.append((features, f'class_{class_id}'))

    result = ml.fewshot_train('proto-task', support_set)
    print(f"  训练: {result}")

    # 预测
    query = [random.gauss(2, 0.5) for _ in range(10)]  # class_1
    pred = ml.fewshot_predict('proto-task', query)
    print(f"  预测: {pred['prediction']}, 置信度: {pred['confidence']}")

    # 评估 episode
    query_set = []
    for class_id in range(3):
        for _ in range(5):
            features = [random.gauss(class_id * 2, 0.5) for _ in range(10)]
            query_set.append((features, f'class_{class_id}'))

    print("\n评估 episode:")
    eval_result = ml.evaluate_episode('proto-task', support_set, query_set)
    print(f"  准确率: {eval_result['accuracy']} ({eval_result['correct']}/{eval_result['total']})")

    print("\n=== 匹配网络 ===")
    ml.create_fewshot_task('match-task', '匹配网络任务', 'matching', n_way=3, k_shot=5,
                          config={'distance_metric': 'cosine'})
    ml.fewshot_train('match-task', support_set)
    pred = ml.fewshot_predict('match-task', query)
    print(f"  预测: {pred['prediction']}, 置信度: {pred['confidence']}")

    print("\n=== MAML 元学习 ===")
    ml.create_fewshot_task('maml-task', 'MAML任务', 'maml', config={'n_features': 5})

    # 生成元训练任务
    meta_tasks = []
    for _ in range(10):
        support_x = [[random.gauss(0, 1) for _ in range(5)] for _ in range(10)]
        support_y = [random.randint(0, 1) for _ in range(10)]
        query_x = [[random.gauss(0, 1) for _ in range(5)] for _ in range(10)]
        query_y = [random.randint(0, 1) for _ in range(10)]
        meta_tasks.append({
            'support_x': support_x, 'support_y': support_y,
            'query_x': query_x, 'query_y': query_y
        })

    print("元训练:")
    for epoch in range(5):
        result = ml.maml_train('maml-task', meta_tasks)
        print(f"  Epoch {epoch+1}: loss={result['meta_loss']}, acc={result['meta_accuracy']}")

    print("\n适应新任务:")
    new_support_x = [[random.gauss(0, 1) for _ in range(5)] for _ in range(5)]
    new_support_y = [1, 0, 1, 0, 1]
    adapt_result = ml.maml_adapt('maml-task', new_support_x, new_support_y)
    print(f"  适应步数: {adapt_result['adaptation_steps']}")

    print("\n经验回放:")
    replay = ml.replay_experiences(3)
    print(f"  回放 {replay['replayed']} 条经验")

    print(f"\n统计: {ml.get_statistics()}")

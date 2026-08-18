from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
"""
MTSCOS AI 在线学习服务 (v14.9.0)
===================================
AI 在线学习和增量更新管理服务。

核心能力：
1. 增量学习 - 在线梯度下降、SGD更新
2. 概念漂移检测 - ADWIN/DDM/页面块检测
3. 在线分类器 - 感知器、PA、在线逻辑回归
4. 数据流管理 - 滑动窗口、采样缓冲
5. 模型版本管理 - 在线模型快照和回滚
6. 性能监控 - 持续准确率追踪和预警
7. 自适应学习率 - 学习率衰减和调整
8. 学习报告 - 在线学习过程报告
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque, defaultdict

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_online_learning.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIOnlineLearning')


# ========== 概念漂移检测 ==========

class DriftDetector:
    """概念漂移检测器"""

    def __init__(self, method: str = 'ddm', warning_threshold: float = 2.0,
                 drift_threshold: float = 3.0, window_size: int = 100):
        self.method = method
        self.warning_threshold = warning_threshold
        self.drift_threshold = drift_threshold
        self.window_size = window_size
        self._window = deque(maxlen=window_size)
        self._total = 0
        self._errors = 0
        self._p_min = float('inf')
        self._s_min = float('inf')
        self.drift_detected = False
        self.warning_detected = False

    def update(self, prediction_correct: bool) -> Dict:
        """更新检测结果"""
        error = 0 if prediction_correct else 1
        self._total += 1
        self._errors += error
        self._window.append(error)

        if self.method == 'ddm':
            return self._ddm_update(error)
        elif self.method == 'adwin':
            return self._adwin_update(error)
        else:
            return self._window_update(error)

    def _ddm_update(self, error: int) -> Dict:
        """DDM (Drift Detection Method)"""
        n = self._total
        if n < 30:
            return {'status': 'warming', 'n': n}

        p = self._errors / n
        s = math.sqrt(p * (1 - p) / n)

        self.warning_detected = False
        self.drift_detected = False

        if p + s < self._p_min + self._s_min:
            self._p_min = p
            self._s_min = s

        if p + s > self._p_min + self.warning_threshold * self._s_min:
            self.warning_detected = True

        if p + s > self._p_min + self.drift_threshold * self._s_min:
            self.drift_detected = True
            self._reset()

        return {
            'status': 'drift' if self.drift_detected else ('warning' if self.warning_detected else 'stable'),
            'error_rate': round(p, 6),
            'std': round(s, 6),
            'p_min': round(self._p_min, 6),
            'n': n
        }

    def _adwin_update(self, error: int) -> Dict:
        """ADWIN 简化版（基于滑动窗口变体）"""
        self._window.append(error)
        if len(self._window) < self.window_size:
            return {'status': 'warming', 'n': len(self._window)}

        # 分割窗口检测变化
        half = len(self._window) // 2
        first_half = list(self._window)[:half]
        second_half = list(self._window)[half:]

        mean1 = sum(first_half) / len(first_half)
        mean2 = sum(second_half) / len(second_half)

        diff = abs(mean2 - mean1)
        threshold = math.sqrt(2 * math.log(1 / 0.01) / self.window_size)

        self.drift_detected = diff > threshold
        self.warning_detected = diff > threshold * 0.5

        if self.drift_detected:
            # 保留后半部分
            self._window = deque(second_half, maxlen=self.window_size)

        return {
            'status': 'drift' if self.drift_detected else ('warning' if self.warning_detected else 'stable'),
            'mean_before': round(mean1, 6),
            'mean_after': round(mean2, 6),
            'difference': round(diff, 6),
            'threshold': round(threshold, 6)
        }

    def _window_update(self, error: int) -> Dict:
        """简单窗口检测"""
        if len(self._window) < self.window_size:
            return {'status': 'warming', 'n': len(self._window)}

        error_rate = sum(self._window) / len(self._window)
        self.drift_detected = error_rate > 0.3
        self.warning_detected = error_rate > 0.2

        return {
            'status': 'drift' if self.drift_detected else ('warning' if self.warning_detected else 'stable'),
            'window_error_rate': round(error_rate, 6),
            'window_size': len(self._window)
        }

    def _reset(self):
        self._total = 0
        self._errors = 0
        self._p_min = float('inf')
        self._s_min = float('inf')

    def stats(self) -> Dict:
        return {
            'method': self.method,
            'total_samples': self._total,
            'total_errors': self._errors,
            'error_rate': round(self._errors / max(self._total, 1), 6),
            'drift_detected': self.drift_detected,
            'warning_detected': self.warning_detected
        }


# ========== 在线分类器 ==========

class OnlinePerceptron:
    """在线感知器分类器"""

    def __init__(self, n_features: int, learning_rate: float = 0.01):
        self.n_features = n_features
        self.learning_rate = learning_rate
        self.weights = [0.0] * n_features
        self.bias = 0.0
        self._updates = 0

    def predict(self, x: List[float]) -> int:
        score = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        return 1 if score > 0 else 0

    def partial_fit(self, x: List[float], y: int) -> Dict:
        """单样本在线更新"""
        pred = self.predict(x)
        error = y - pred
        if error != 0:
            for i in range(self.n_features):
                self.weights[i] += self.learning_rate * error * x[i]
            self.bias += self.learning_rate * error
            self._updates += 1
        return {'prediction': pred, 'actual': y, 'correct': pred == y, 'updates': self._updates}


class OnlineLogisticRegression:
    """在线逻辑回归"""

    def __init__(self, n_features: int, learning_rate: float = 0.01,
                 l2_reg: float = 0.01):
        self.n_features = n_features
        self.learning_rate = learning_rate
        self.l2_reg = l2_reg
        self.weights = [0.0] * n_features
        self.bias = 0.0
        self._samples_seen = 0

    def _sigmoid(self, z: float) -> float:
        if z >= 0:
            return 1 / (1 + math.exp(-z))
        else:
            ez = math.exp(z)
            return ez / (1 + ez)

    def predict_proba(self, x: List[float]) -> float:
        z = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        return self._sigmoid(z)

    def predict(self, x: List[float]) -> int:
        return 1 if self.predict_proba(x) > 0.5 else 0

    def partial_fit(self, x: List[float], y: int) -> Dict:
        """单样本在线更新"""
        proba = self.predict_proba(x)
        error = y - proba
        # L2 正则化梯度
        for i in range(self.n_features):
            grad = error * x[i] - self.l2_reg * self.weights[i]
            self.weights[i] += self.learning_rate * grad
        self.bias += self.learning_rate * error
        self._samples_seen += 1

        pred = 1 if proba > 0.5 else 0
        return {
            'prediction': pred,
            'probability': round(proba, 6),
            'actual': y,
            'correct': pred == y,
            'samples_seen': self._samples_seen
        }


class PassiveAggressiveClassifier:
    """被动攻击分类器"""

    def __init__(self, n_features: int, C: float = 1.0):
        self.n_features = n_features
        self.C = C
        self.weights = [0.0] * n_features
        self.bias = 0.0
        self._updates = 0

    def predict(self, x: List[float]) -> int:
        score = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        return 1 if score > 0 else 0

    def partial_fit(self, x: List[float], y: int) -> Dict:
        """PA-I 更新"""
        y_signed = 1 if y == 1 else -1
        score = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        loss = max(0, 1 - y_signed * score)

        if loss > 0:
            norm_sq = sum(xi ** 2 for xi in x)
            if norm_sq > 0:
                # PA-I: tau = min(C, loss / norm_sq)
                tau = min(self.C, loss / norm_sq)
                for i in range(self.n_features):
                    self.weights[i] += tau * y_signed * x[i]
                self.bias += tau * y_signed
                self._updates += 1

        pred = self.predict(x)
        return {
            'prediction': pred,
            'actual': y,
            'correct': pred == y,
            'loss': round(loss, 6),
            'updates': self._updates
        }


ONLINE_CLASSIFIERS = {
    'perceptron': OnlinePerceptron,
    'logistic': OnlineLogisticRegression,
    'pa': PassiveAggressiveClassifier,
}


# ========== 自适应学习率 ==========

class AdaptiveLearningRate:
    """自适应学习率管理"""

    def __init__(self, initial_lr: float = 0.01, method: str = 'exponential',
                 decay_rate: float = 0.95, warmup_steps: int = 100):
        self.initial_lr = initial_lr
        self.current_lr = initial_lr
        self.method = method
        self.decay_rate = decay_rate
        self.warmup_steps = warmup_steps
        self._step = 0
        self._loss_history = deque(maxlen=100)
        self._best_loss = float('inf')
        self._patience = 5
        self._wait = 0

    def step(self, loss: float = None) -> float:
        """更新学习率"""
        self._step += 1

        if self.method == 'exponential':
            self.current_lr = self.initial_lr * (self.decay_rate ** (self._step / 100))
        elif self.method == 'linear':
            self.current_lr = self.initial_lr / (1 + self._step * 0.001)
        elif self.method == 'cosine':
            self.current_lr = self.initial_lr * 0.5 * (1 + math.cos(math.pi * self._step / 1000))
        elif self.method == 'warmup':
            if self._step < self.warmup_steps:
                self.current_lr = self.initial_lr * (self._step / self.warmup_steps)
            else:
                self.current_lr = self.initial_lr * (self.decay_rate ** ((self._step - self.warmup_steps) / 100))
        elif self.method == 'reduce_on_plateau':
            if loss is not None:
                self._loss_history.append(loss)
                if loss < self._best_loss:
                    self._best_loss = loss
                    self._wait = 0
                else:
                    self._wait += 1
                    if self._wait >= self._patience:
                        self.current_lr *= self.decay_rate
                        self._wait = 0

        self.current_lr = max(1e-10, self.current_lr)
        return self.current_lr

    def stats(self) -> Dict:
        return {
            'method': self.method,
            'initial_lr': self.initial_lr,
            'current_lr': round(self.current_lr, 8),
            'step': self._step,
            'best_loss': round(self._best_loss, 6) if self._best_loss != float('inf') else None
        }


# ========== 在线学习服务 ==========

class AIOnlineLearning:
    """AI 在线学习服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._models: Dict[str, Dict] = {}  # model_id -> {classifier, drift_detector, lr_scheduler, stats}

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS online_models (
                        model_id TEXT PRIMARY KEY,
                        model_name TEXT,
                        model_type TEXT,
                        n_features INTEGER,
                        config TEXT,
                        status TEXT DEFAULT 'created',
                        samples_seen INTEGER DEFAULT 0,
                        correct_predictions INTEGER DEFAULT 0,
                        accuracy REAL DEFAULT 0,
                        drift_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        last_update TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS online_learning_events (
                        event_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        event_type TEXT,
                        sample_count INTEGER,
                        accuracy REAL,
                        drift_detected INTEGER,
                        learning_rate REAL,
                        details TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS online_model_snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        version INTEGER,
                        weights TEXT,
                        accuracy REAL,
                        samples_seen INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ol_model ON online_learning_events(model_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化在线学习数据库失败: {e}")

    # ========== 模型管理 ==========

    def create_model(self, model_id: str, model_name: str = '',
                    model_type: str = 'logistic', n_features: int = 10,
                    config: Dict = None) -> Dict:
        """创建在线学习模型"""
        config = config or {}
        if model_type not in ONLINE_CLASSIFIERS:
            return {'success': False, 'error': f'不支持的模型类型: {model_type}'}

        classifier_cls = ONLINE_CLASSIFIERS[model_type]
        lr = config.get('learning_rate', 0.01)
        classifier = classifier_cls(n_features, learning_rate=lr) if model_type != 'pa' \
            else classifier_cls(n_features, C=config.get('C', 1.0))

        drift_method = config.get('drift_method', 'ddm')
        drift_detector = DriftDetector(method=drift_method,
                                       window_size=config.get('window_size', 100))

        lr_method = config.get('lr_method', 'exponential')
        lr_scheduler = AdaptiveLearningRate(
            initial_lr=lr, method=lr_method,
            decay_rate=config.get('decay_rate', 0.95)
        )

        self._models[model_id] = {
            'classifier': classifier,
            'drift_detector': drift_detector,
            'lr_scheduler': lr_scheduler,
            'samples_seen': 0,
            'correct': 0,
            'recent_accuracy': deque(maxlen=1000),
            'accuracy_history': [],
            'drift_count': 0
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO online_models
                    (model_id, model_name, model_type, n_features, config, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'active', ?)
                ''', (
                    model_id, model_name or model_id, model_type, n_features,
                    json.dumps(config, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        logger.info(f"创建在线学习模型: {model_id} ({model_type})")
        return {'success': True, 'model_id': model_id}

    def partial_fit(self, model_id: str, x: List[float], y: int) -> Dict:
        """单样本在线学习"""
        model = self._models.get(model_id)
        if not model:
            return {'success': False, 'error': '模型不存在'}

        classifier = model['classifier']
        lr_scheduler = model['lr_scheduler']
        drift_detector = model['drift_detector']

        # 预测并更新
        result = classifier.partial_fit(x, y)
        correct = result['correct']

        # 漂移检测
        drift_result = drift_detector.update(correct)

        # 学习率更新
        loss = 0 if correct else 1
        current_lr = lr_scheduler.step(loss)

        # 更新统计
        model['samples_seen'] += 1
        if correct:
            model['correct'] += 1
        model['recent_accuracy'].append(1 if correct else 0)
        current_acc = sum(model['recent_accuracy']) / len(model['recent_accuracy'])
        model['accuracy_history'].append({
            'sample': model['samples_seen'],
            'accuracy': round(current_acc, 6)
        })

        # 漂移处理
        if drift_result.get('status') == 'drift':
            model['drift_count'] += 1
            self._save_snapshot(model_id, model)
            self._record_event(model_id, 'drift', model, drift_result, current_lr)
            logger.warning(f"模型 {model_id} 检测到概念漂移 (第{model['samples_seen']}个样本)")

        # 定期记录
        if model['samples_seen'] % 100 == 0:
            self._record_event(model_id, 'checkpoint', model, drift_result, current_lr)
            self._update_model_db(model_id, model, current_acc)

        return {
            'success': True,
            'model_id': model_id,
            'prediction': result['prediction'],
            'actual': y,
            'correct': correct,
            'current_accuracy': round(current_acc, 6),
            'samples_seen': model['samples_seen'],
            'drift_status': drift_result.get('status'),
            'learning_rate': round(current_lr, 8)
        }

    def partial_fit_batch(self, model_id: str, X: List[List[float]],
                         y: List[int]) -> Dict:
        """批量在线学习"""
        if len(X) != len(y):
            return {'success': False, 'error': 'X和y长度不匹配'}

        results = []
        correct_count = 0
        drift_detected = False

        for xi, yi in zip(X, y):
            result = self.partial_fit(model_id, xi, yi)
            if result.get('success'):
                results.append(result)
                if result['correct']:
                    correct_count += 1
                if result['drift_status'] == 'drift':
                    drift_detected = True

        return {
            'success': True,
            'model_id': model_id,
            'total_samples': len(X),
            'correct': correct_count,
            'accuracy': round(correct_count / max(len(X), 1), 6),
            'drift_detected': drift_detected,
            'samples_seen': self._models.get(model_id, {}).get('samples_seen', 0)
        }

    def predict(self, model_id: str, x: List[float]) -> Dict:
        """在线预测（不更新模型）"""
        model = self._models.get(model_id)
        if not model:
            return {'success': False, 'error': '模型不存在'}

        pred = model['classifier'].predict(x)
        proba = None
        if hasattr(model['classifier'], 'predict_proba'):
            proba = model['classifier'].predict_proba(x)

        return {
            'success': True,
            'model_id': model_id,
            'prediction': pred,
            'probability': round(proba, 6) if proba is not None else None
        }

    # ========== 快照和回滚 ==========

    def _save_snapshot(self, model_id: str, model: Dict):
        """保存模型快照"""
        snapshot_id = f"SNAP-{model_id}-{model['samples_seen']}"
        classifier = model['classifier']
        weights = {
            'weights': getattr(classifier, 'weights', []),
            'bias': getattr(classifier, 'bias', 0)
        }
        accuracy = sum(model['recent_accuracy']) / len(model['recent_accuracy']) if model['recent_accuracy'] else 0
        version = model['drift_count']

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO online_model_snapshots
                    (snapshot_id, model_id, version, weights, accuracy,
                     samples_seen, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot_id, model_id, version,
                    json.dumps(weights, ensure_ascii=False),
                    accuracy, model['samples_seen'],
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存快照失败: {e}")

    def rollback(self, model_id: str, version: int = None) -> Dict:
        """回滚到指定版本"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if version:
                    cursor.execute('''
                        SELECT weights, samples_seen FROM online_model_snapshots
                        WHERE model_id = ? AND version = ?
                        ORDER BY created_at DESC LIMIT 1
                    ''', (model_id, version))
                else:
                    cursor.execute('''
                        SELECT weights, samples_seen FROM online_model_snapshots
                        WHERE model_id = ?
                        ORDER BY created_at DESC LIMIT 1
                    ''', (model_id,))

                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '无可用快照'}

                weights = json.loads(row[0])
                model = self._models.get(model_id)
                if model:
                    classifier = model['classifier']
                    if hasattr(classifier, 'weights'):
                        classifier.weights = weights['weights']
                    if hasattr(classifier, 'bias'):
                        classifier.bias = weights['bias']

                return {'success': True, 'model_id': model_id, 'restored_version': version}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 内部方法 ==========

    def _record_event(self, model_id: str, event_type: str, model: Dict,
                     drift_result: Dict, lr: float):
        event_id = f"EVT-{random.randint(100000, 999999)}"
        accuracy = sum(model['recent_accuracy']) / len(model['recent_accuracy']) if model['recent_accuracy'] else 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO online_learning_events
                    (event_id, model_id, event_type, sample_count, accuracy,
                     drift_detected, learning_rate, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id, model_id, event_type, model['samples_seen'],
                    accuracy, 1 if drift_result.get('status') == 'drift' else 0,
                    lr, json.dumps(drift_result, ensure_ascii=False, default=str),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

    def _update_model_db(self, model_id: str, model: Dict, accuracy: float):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE online_models
                    SET samples_seen = ?, correct_predictions = ?,
                        accuracy = ?, drift_count = ?, last_update = ?
                    WHERE model_id = ?
                ''', (
                    model['samples_seen'], model['correct'],
                    accuracy, model['drift_count'],
                    datetime.now().isoformat(), model_id
                ))
                conn.commit()
        except Exception:
            pass

    # ========== 查询和统计 ==========

    def get_model_info(self, model_id: str) -> Optional[Dict]:
        model = self._models.get(model_id)
        if not model:
            return None
        accuracy = sum(model['recent_accuracy']) / len(model['recent_accuracy']) if model['recent_accuracy'] else 0
        return {
            'model_id': model_id,
            'samples_seen': model['samples_seen'],
            'correct_predictions': model['correct'],
            'current_accuracy': round(accuracy, 6),
            'drift_count': model['drift_count'],
            'lr_stats': model['lr_scheduler'].stats(),
            'drift_stats': model['drift_detector'].stats()
        }

    def get_accuracy_history(self, model_id: str, limit: int = 100) -> List[Dict]:
        model = self._models.get(model_id)
        if not model:
            return []
        return model['accuracy_history'][-limit:]

    def list_models(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT model_id, model_name, model_type, status, samples_seen,
                           accuracy, drift_count, created_at
                    FROM online_models ORDER BY created_at DESC
                ''')
                return [
                    {
                        'model_id': r[0], 'model_name': r[1], 'model_type': r[2],
                        'status': r[3], 'samples_seen': r[4], 'accuracy': r[5],
                        'drift_count': r[6], 'created_at': r[7]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM online_models')
                total_models = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(samples_seen) FROM online_models')
                total_samples = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM online_learning_events WHERE drift_detected = 1')
                total_drifts = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM online_model_snapshots')
                total_snapshots = cursor.fetchone()[0]
            return {
                'total_models': total_models,
                'total_samples': total_samples,
                'total_drifts': total_drifts,
                'total_snapshots': total_snapshots,
                'active_models': len(self._models)
            }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    ol = AIOnlineLearning()

    print("创建在线学习模型:")
    result = ol.create_model('test-model', '测试模型', 'logistic', n_features=5,
                            config={'learning_rate': 0.05, 'drift_method': 'ddm',
                                   'lr_method': 'exponential'})
    print(f"  结果: {result}")

    # 生成测试数据
    print("\n在线学习（正常数据）:")
    random.seed(42)
    for i in range(200):
        x = [random.gauss(0, 1) for _ in range(5)]
        y = 1 if sum(x) > 0 else 0
        result = ol.partial_fit('test-model', x, y)

    info = ol.get_model_info('test-model')
    print(f"  样本数: {info['samples_seen']}")
    print(f"  准确率: {info['current_accuracy']}")
    print(f"  漂移数: {info['drift_count']}")
    print(f"  学习率: {info['lr_stats']['current_lr']}")

    # 引入概念漂移
    print("\n引入概念漂移（反转标签）:")
    for i in range(200):
        x = [random.gauss(0, 1) for _ in range(5)]
        y = 0 if sum(x) > 0 else 1  # 反转
        result = ol.partial_fit('test-model', x, y)
        if result['drift_status'] == 'drift':
            print(f"  第{result['samples_seen']}个样本检测到漂移!")
            break

    info = ol.get_model_info('test-model')
    print(f"  最终准确率: {info['current_accuracy']}")
    print(f"  总漂移数: {info['drift_count']}")

    print("\n准确率历史（最后10个点）:")
    for h in ol.get_accuracy_history('test-model', limit=10):
        print(f"  样本{h['sample']}: {h['accuracy']}")

    print(f"\n统计: {ol.get_statistics()}")

#!/usr/bin/env python3
"""
MTSCOS AI 联邦学习服务 (v14.7.0)
===================================
联邦学习框架和模型聚合管理服务。

核心能力：
1. 联邦任务管理 - 创建/监控/结束联邦训练任务
2. 客户端管理 - 客户端注册、认证、状态管理
3. 模型聚合 - FedAvg/FedProx/FedMedian 等聚合算法
4. 轮次管理 - 训练轮次追踪和参数更新
5. 数据统计 - 各客户端数据分布统计
6. 性能监控 - 各轮次准确率和损失变化
7. 异常客户端检测 - 低质量/恶意客户端检测
8. 差分隐私 - 高斯噪声、Laplace机制
"""
import os
import json
import math
import sqlite3
import random
import logging
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_federated.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIFederatedLearning')


# ========== 聚合算法 ==========

def fedavg(weights_list: List[Dict], sample_counts: List[int] = None) -> Dict:
    """FedAvg：按样本数加权平均

    weights_list: 每个客户端的模型权重字典 {layer_name: [values]}
    sample_counts: 每个客户端的训练样本数
    """
    if not weights_list:
        return {}

    if sample_counts is None:
        sample_counts = [1] * len(weights_list)

    total_samples = sum(sample_counts)
    if total_samples == 0:
        total_samples = len(weights_list)
        sample_counts = [1] * len(weights_list)

    # 找出所有层级
    all_layers = set()
    for w in weights_list:
        all_layers.update(w.keys())

    aggregated = {}
    for layer in all_layers:
        layer_weights = []
        layer_counts = []
        for i, w in enumerate(weights_list):
            if layer in w:
                layer_weights.append(w[layer])
                layer_counts.append(sample_counts[i])

        if not layer_weights:
            continue

        # 加权平均
        total_count = sum(layer_counts)
        if isinstance(layer_weights[0], (list, tuple)):
            # 列表型权重
            aggregated[layer] = []
            for j in range(len(layer_weights[0])):
                weighted_sum = sum(
                    layer_weights[i][j] * layer_counts[i]
                    for i in range(len(layer_weights))
                )
                aggregated[layer].append(round(weighted_sum / total_count, 8))
        else:
            # 标量型权重
            weighted_sum = sum(
                layer_weights[i] * layer_counts[i]
                for i in range(len(layer_weights))
            )
            aggregated[layer] = round(weighted_sum / total_count, 8)

    return aggregated


def fedmedian(weights_list: List[Dict]) -> Dict:
    """FedMedian：中位数聚合（更鲁棒）"""
    if not weights_list:
        return {}

    all_layers = set()
    for w in weights_list:
        all_layers.update(w.keys())

    aggregated = {}
    for layer in all_layers:
        layer_vals = [w[layer] for w in weights_list if layer in w]
        if not layer_vals:
            continue

        if isinstance(layer_vals[0], (list, tuple)):
            n = len(layer_vals[0])
            aggregated[layer] = []
            for j in range(n):
                vals = [w[j] for w in layer_vals if j < len(w)]
                vals.sort()
                mid = len(vals) // 2
                aggregated[layer].append(round(vals[mid], 8))
        else:
            layer_vals.sort()
            mid = len(layer_vals) // 2
            aggregated[layer] = round(layer_vals[mid], 8)

    return aggregated


def fedprox(weights_list: List[Dict], global_weights: Dict,
            mu: float = 0.1, sample_counts: List[int] = None) -> Dict:
    """FedProx：带近端项的聚合（简化版）"""
    if not weights_list or not global_weights:
        return fedavg(weights_list, sample_counts)

    # 先做FedAvg
    avg = fedavg(weights_list, sample_counts)
    # 添加近端正则（向全局模型靠近）
    aggregated = {}
    for layer in avg:
        if layer in global_weights:
            if isinstance(avg[layer], list):
                aggregated[layer] = [
                    round(avg[layer][j] + mu * global_weights[layer][j], 8)
                    for j in range(len(avg[layer]))
                ]
            else:
                aggregated[layer] = round(avg[layer] + mu * global_weights[layer], 8)
        else:
            aggregated[layer] = avg[layer]
    return aggregated


AGGREGATION_METHODS = {
    'fedavg': fedavg,
    'fedmedian': fedmedian,
    'fedprox': fedprox,
}


# ========== 差分隐私 ==========

def add_gaussian_noise(weights: Dict, sigma: float = 0.1,
                       clip_norm: float = 1.0) -> Dict:
    """添加高斯噪声"""
    noised = {}
    for layer, val in weights.items():
        if isinstance(val, list):
            noised[layer] = [
                round(v + random.gauss(0, sigma * clip_norm), 8)
                for v in val
            ]
        else:
            noised[layer] = round(val + random.gauss(0, sigma * clip_norm), 8)
    return noised


def add_laplace_noise(weights: Dict, epsilon: float = 1.0,
                      sensitivity: float = 1.0) -> Dict:
    """添加Laplace噪声"""
    scale = sensitivity / epsilon
    noised = {}
    for layer, val in weights.items():
        if isinstance(val, list):
            noised[layer] = [
                round(v + random.expovariate(1/scale) - random.expovariate(1/scale), 8)
                for v in val
            ]
        else:
            noised[layer] = round(val + random.expovariate(1/scale) - random.expovariate(1/scale), 8)
    return noised


# ========== 联邦学习服务 ==========

class AIFederatedLearning:
    """AI 联邦学习服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._active_tasks: Dict[str, Dict] = {}

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fl_clients (
                        client_id TEXT PRIMARY KEY,
                        client_name TEXT,
                        client_type TEXT DEFAULT 'standard',
                        status TEXT DEFAULT 'inactive',
                        data_size INTEGER DEFAULT 0,
                        data_distribution TEXT,
                        compute_capacity REAL DEFAULT 1.0,
                        trust_score REAL DEFAULT 0.5,
                        total_rounds INTEGER DEFAULT 0,
                        success_rounds INTEGER DEFAULT 0,
                        last_seen TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fl_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_name TEXT NOT NULL,
                        model_name TEXT,
                        aggregation_method TEXT DEFAULT 'fedavg',
                        target_rounds INTEGER DEFAULT 10,
                        current_round INTEGER DEFAULT 0,
                        min_clients INTEGER DEFAULT 2,
                        max_clients INTEGER DEFAULT 100,
                        status TEXT DEFAULT 'created',
                        global_model TEXT,
                        dp_enabled INTEGER DEFAULT 0,
                        dp_method TEXT,
                        dp_epsilon REAL,
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fl_rounds (
                        round_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        round_number INTEGER NOT NULL,
                        status TEXT DEFAULT 'in_progress',
                        participating_clients INTEGER DEFAULT 0,
                        aggregated_model TEXT,
                        accuracy REAL,
                        loss REAL,
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fl_client_updates (
                        update_id TEXT PRIMARY KEY,
                        task_id TEXT,
                        round_id TEXT,
                        client_id TEXT,
                        round_number INTEGER,
                        model_weights TEXT,
                        sample_count INTEGER,
                        accuracy REAL,
                        loss REAL,
                        training_time_sec INTEGER,
                        status TEXT DEFAULT 'submitted',
                        submitted_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_fl_task ON fl_rounds(task_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_fl_client ON fl_client_updates(client_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化联邦学习数据库失败: {e}")

    # ========== 客户端管理 ==========

    def register_client(self, client_id: str, client_name: str = '',
                       client_type: str = 'standard',
                       data_size: int = 0,
                       compute_capacity: float = 1.0) -> Dict:
        """注册客户端"""
        client_id = client_id or f"FL-C-{random.randint(100000, 999999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT client_id FROM fl_clients WHERE client_id = ?', (client_id,))
                if cursor.fetchone():
                    return {'success': False, 'error': '客户端已存在'}

                cursor.execute('''
                    INSERT INTO fl_clients
                    (client_id, client_name, client_type, status, data_size,
                     compute_capacity, trust_score, created_at)
                    VALUES (?, ?, ?, 'inactive', ?, ?, 0.5, ?)
                ''', (
                    client_id, client_name or client_id, client_type,
                    data_size, compute_capacity, datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'client_id': client_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_client_status(self, client_id: str, status: str,
                            data_size: int = None,
                            data_distribution: Dict = None) -> Dict:
        """更新客户端状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                updates = ['status = ?', 'last_seen = ?']
                values = [status, datetime.now().isoformat()]
                if data_size is not None:
                    updates.append('data_size = ?')
                    values.append(data_size)
                if data_distribution is not None:
                    updates.append('data_distribution = ?')
                    values.append(json.dumps(data_distribution, ensure_ascii=False))
                values.append(client_id)

                cursor.execute(f'''
                    UPDATE fl_clients
                    SET {', '.join(updates)}
                    WHERE client_id = ?
                ''', values)
                conn.commit()
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_client(self, client_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM fl_clients WHERE client_id = ?', (client_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'client_id': row[0], 'client_name': row[1], 'client_type': row[2],
                    'status': row[3], 'data_size': row[4],
                    'data_distribution': json.loads(row[5]) if row[5] else {},
                    'compute_capacity': row[6], 'trust_score': row[7],
                    'total_rounds': row[8], 'success_rounds': row[9],
                    'last_seen': row[10], 'created_at': row[11]
                }
        except Exception:
            return None

    def list_clients(self, status: str = None) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('SELECT client_id, client_name, status, data_size, trust_score FROM fl_clients WHERE status = ?',
                                  (status,))
                else:
                    cursor.execute('SELECT client_id, client_name, status, data_size, trust_score FROM fl_clients')
                return [
                    {
                        'client_id': r[0], 'client_name': r[1], 'status': r[2],
                        'data_size': r[3], 'trust_score': r[4]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def update_trust_score(self, client_id: str, delta: float) -> Dict:
        """更新客户端信任分"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE fl_clients
                    SET trust_score = MAX(0.0, MIN(1.0, trust_score + ?))
                    WHERE client_id = ?
                ''', (delta, client_id))
                conn.commit()
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 任务管理 ==========

    def create_task(self, task_name: str, model_name: str = 'default_model',
                   aggregation_method: str = 'fedavg',
                   target_rounds: int = 10,
                   min_clients: int = 2,
                   initial_weights: Dict = None,
                   dp_enabled: bool = False,
                   dp_method: str = 'gaussian',
                   dp_epsilon: float = 1.0) -> Dict:
        """创建联邦学习任务"""
        if aggregation_method not in AGGREGATION_METHODS:
            return {'success': False, 'error': f'不支持的聚合方法: {aggregation_method}'}

        task_id = f"FL-T-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO fl_tasks
                    (task_id, task_name, model_name, aggregation_method, target_rounds,
                     min_clients, status, global_model, dp_enabled, dp_method, dp_epsilon, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'created', ?, ?, ?, ?, ?)
                ''', (
                    task_id, task_name, model_name, aggregation_method,
                    target_rounds, min_clients,
                    json.dumps(initial_weights or {}, ensure_ascii=False),
                    1 if dp_enabled else 0, dp_method, dp_epsilon,
                    datetime.now().isoformat()
                ))
                conn.commit()
            self._active_tasks[task_id] = {
                'task_id': task_id,
                'status': 'created',
                'current_round': 0,
                'rounds': {}
            }
            logger.info(f"创建联邦学习任务: {task_id} ({task_name})")
            return {'success': True, 'task_id': task_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def start_task(self, task_id: str) -> Dict:
        """开始联邦学习任务"""
        task = self.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}
        if task['status'] not in ('created', 'paused'):
            return {'success': False, 'error': f'任务状态不支持启动: {task["status"]}'}

        # 开始第一轮
        round_result = self._start_round(task_id, 1)
        if not round_result.get('success'):
            return round_result

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE fl_tasks
                    SET status = 'running', current_round = 1
                    WHERE task_id = ?
                ''', (task_id,))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        if task_id in self._active_tasks:
            self._active_tasks[task_id]['status'] = 'running'

        logger.info(f"启动联邦学习任务: {task_id}")
        return {'success': True, 'task_id': task_id, 'first_round': round_result.get('round_id')}

    def get_task(self, task_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM fl_tasks WHERE task_id = ?', (task_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'task_id': row[0], 'task_name': row[1], 'model_name': row[2],
                    'aggregation_method': row[3], 'target_rounds': row[4],
                    'current_round': row[5], 'min_clients': row[6],
                    'max_clients': row[7], 'status': row[8],
                    'global_model': json.loads(row[9]) if row[9] else {},
                    'dp_enabled': bool(row[10]), 'dp_method': row[11],
                    'dp_epsilon': row[12], 'created_at': row[13],
                    'completed_at': row[14]
                }
        except Exception:
            return None

    def list_tasks(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT task_id, task_name, status, current_round, target_rounds, created_at
                    FROM fl_tasks ORDER BY created_at DESC
                ''')
                return [
                    {
                        'task_id': r[0], 'task_name': r[1], 'status': r[2],
                        'current_round': r[3], 'target_rounds': r[4], 'created_at': r[5]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 轮次管理 ==========

    def _start_round(self, task_id: str, round_number: int) -> Dict:
        """启动新的训练轮次"""
        round_id = f"FL-R-{task_id[-8:]}-{round_number:04d}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO fl_rounds
                    (round_id, task_id, round_number, status, created_at)
                    VALUES (?, ?, ?, 'in_progress', ?)
                ''', (round_id, task_id, round_number, datetime.now().isoformat()))
                conn.commit()
            return {'success': True, 'round_id': round_id, 'round_number': round_number}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def submit_update(self, task_id: str, client_id: str, model_weights: Dict,
                     sample_count: int, accuracy: float = None,
                     loss: float = None, training_time_sec: int = None) -> Dict:
        """客户端提交模型更新"""
        task = self.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}
        if task['status'] != 'running':
            return {'success': False, 'error': f'任务未运行: {task["status"]}'}

        client = self.get_client(client_id)
        if not client:
            return {'success': False, 'error': '客户端不存在'}

        round_num = task['current_round']
        update_id = f"FL-U-{random.randint(100000, 999999)}"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO fl_client_updates
                    (update_id, task_id, client_id, round_number, model_weights,
                     sample_count, accuracy, loss, training_time_sec, status, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted', ?)
                ''', (
                    update_id, task_id, client_id, round_num,
                    json.dumps(model_weights, ensure_ascii=False),
                    sample_count, accuracy, loss, training_time_sec,
                    datetime.now().isoformat()
                ))

                # 更新客户端统计
                cursor.execute('''
                    UPDATE fl_clients
                    SET total_rounds = total_rounds + 1,
                        success_rounds = success_rounds + 1,
                        last_seen = ?
                    WHERE client_id = ?
                ''', (datetime.now().isoformat(), client_id))

                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        logger.info(f"客户端 {client_id} 提交更新: 任务 {task_id}, 轮次 {round_num}")
        return {'success': True, 'update_id': update_id, 'round_number': round_num}

    def aggregate_and_next_round(self, task_id: str) -> Dict:
        """聚合当前轮次并开始下一轮"""
        task = self.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}

        current_round = task['current_round']

        # 收集当前轮次的更新
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT client_id, model_weights, sample_count, accuracy, loss
                    FROM fl_client_updates
                    WHERE task_id = ? AND round_number = ? AND status = 'submitted'
                ''', (task_id, current_round))
                updates = cursor.fetchall()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        if len(updates) < task['min_clients']:
            return {
                'success': False,
                'error': f'参与客户端不足: {len(updates)}/{task["min_clients"]}'
            }

        # 提取权重和样本数
        weights_list = [json.loads(u[1]) for u in updates]
        sample_counts = [u[2] for u in updates]

        # 执行聚合
        agg_fn = AGGREGATION_METHODS.get(task['aggregation_method'])
        if not agg_fn:
            return {'success': False, 'error': f'未知聚合方法: {task["aggregation_method"]}'}

        if task['aggregation_method'] == 'fedprox':
            aggregated = agg_fn(weights_list, task['global_model'],
                                mu=0.1, sample_counts=sample_counts)
        else:
            aggregated = agg_fn(weights_list, sample_counts)

        # 差分隐私
        if task['dp_enabled']:
            if task['dp_method'] == 'gaussian':
                aggregated = add_gaussian_noise(aggregated, sigma=0.1)
            elif task['dp_method'] == 'laplace':
                aggregated = add_laplace_noise(aggregated, epsilon=task['dp_epsilon'] or 1.0)

        # 计算轮次统计
        accuracies = [u[3] for u in updates if u[3] is not None]
        losses = [u[4] for u in updates if u[4] is not None]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
        avg_loss = sum(losses) / len(losses) if losses else None

        # 更新轮次记录
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE fl_rounds
                    SET status = 'completed', participating_clients = ?,
                        aggregated_model = ?, accuracy = ?, loss = ?, completed_at = ?
                    WHERE task_id = ? AND round_number = ?
                ''', (
                    len(updates),
                    json.dumps(aggregated, ensure_ascii=False),
                    avg_accuracy, avg_loss, datetime.now().isoformat(),
                    task_id, current_round
                ))

                # 更新全局模型
                next_round = current_round + 1
                if next_round <= task['target_rounds']:
                    cursor.execute('''
                        UPDATE fl_tasks
                        SET global_model = ?, current_round = ?
                        WHERE task_id = ?
                    ''', (json.dumps(aggregated, ensure_ascii=False), next_round, task_id))
                    # 启动下一轮
                    self._start_round(task_id, next_round)
                else:
                    # 任务完成
                    cursor.execute('''
                        UPDATE fl_tasks
                        SET global_model = ?, status = 'completed', completed_at = ?
                        WHERE task_id = ?
                    ''', (json.dumps(aggregated, ensure_ascii=False),
                          datetime.now().isoformat(), task_id))
                    if task_id in self._active_tasks:
                        self._active_tasks[task_id]['status'] = 'completed'

                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        logger.info(f"任务 {task_id} 第 {current_round} 轮聚合完成: {len(updates)} 个客户端")

        return {
            'success': True,
            'task_id': task_id,
            'round_number': current_round,
            'participating_clients': len(updates),
            'avg_accuracy': avg_accuracy,
            'avg_loss': avg_loss,
            'next_round': next_round if next_round <= task['target_rounds'] else None,
            'task_completed': next_round > task['target_rounds']
        }

    # ========== 异常客户端检测 ==========

    def detect_anomalous_clients(self, task_id: str, round_number: int = None) -> Dict:
        """检测异常/恶意客户端"""
        task = self.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}

        if round_number is None:
            round_number = task['current_round']

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT client_id, accuracy, loss, model_weights, sample_count
                    FROM fl_client_updates
                    WHERE task_id = ? AND round_number = ? AND status = 'submitted'
                ''', (task_id, round_number))
                updates = cursor.fetchall()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        if len(updates) < 3:
            return {'success': True, 'anomalous': [], 'note': '客户端不足无法检测'}

        # 基于准确率离群检测
        accuracies = [u[1] for u in updates if u[1] is not None]
        if len(accuracies) >= 3:
            mean_acc = sum(accuracies) / len(accuracies)
            std_acc = math.sqrt(sum((a - mean_acc)**2 for a in accuracies) / len(accuracies))
            anomalous = []
            for u in updates:
                if u[1] is not None and std_acc > 0:
                    z_score = abs(u[1] - mean_acc) / std_acc
                    if z_score > 2.0:
                        anomalous.append({
                            'client_id': u[0],
                            'accuracy': u[1],
                            'z_score': round(z_score, 4),
                            'reason': '准确率显著偏离均值'
                        })
        else:
            anomalous = []

        return {
            'success': True,
            'task_id': task_id,
            'round_number': round_number,
            'total_clients': len(updates),
            'anomalous': anomalous,
            'mean_accuracy': round(mean_acc, 4) if accuracies else None,
            'std_accuracy': round(std_acc, 4) if accuracies else None
        }

    # ========== 统计 ==========

    def get_task_stats(self, task_id: str) -> Dict:
        """获取任务统计"""
        task = self.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT round_number, participating_clients, accuracy, loss, status
                    FROM fl_rounds
                    WHERE task_id = ?
                    ORDER BY round_number
                ''', (task_id,))
                rounds = [
                    {
                        'round': r[0],
                        'clients': r[1],
                        'accuracy': r[2],
                        'loss': r[3],
                        'status': r[4]
                    }
                    for r in cursor.fetchall()
                ]

                cursor.execute('''
                    SELECT COUNT(DISTINCT client_id)
                    FROM fl_client_updates
                    WHERE task_id = ?
                ''', (task_id,))
                total_clients = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COUNT(*)
                    FROM fl_client_updates
                    WHERE task_id = ?
                ''', (task_id,))
                total_updates = cursor.fetchone()[0]

                return {
                    'task': task,
                    'rounds': rounds,
                    'total_clients': total_clients,
                    'total_updates': total_updates,
                    'round_count': len(rounds)
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM fl_clients')
                total_clients = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM fl_tasks')
                total_tasks = cursor.fetchone()[0]
                cursor.execute("SELECT status, COUNT(*) FROM fl_tasks GROUP BY status")
                task_status = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM fl_client_updates')
                total_updates = cursor.fetchone()[0]
                return {
                    'total_clients': total_clients,
                    'total_tasks': total_tasks,
                    'task_status_distribution': task_status,
                    'total_client_updates': total_updates
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    fl = AIFederatedLearning()
    print(f"统计: {fl.get_statistics()}")

    # 注册测试客户端
    print("\n注册客户端:")
    for i in range(3):
        cid = f"test-client-{i+1}"
        result = fl.register_client(cid, f"测试客户端{i+1}", data_size=1000 + i * 500)
        print(f"  {cid}: {result.get('success')}")

    # 创建任务
    print("\n创建联邦学习任务:")
    initial_weights = {'layer1': [0.1, 0.2, 0.3], 'layer2': [0.4, 0.5], 'bias': 0.01}
    result = fl.create_task('测试任务', model_name='simple_model',
                           aggregation_method='fedavg',
                           target_rounds=5, min_clients=2,
                           initial_weights=initial_weights)
    print(f"  任务ID: {result.get('task_id')}")
    task_id = result['task_id']

    # 启动任务
    print("\n启动任务:")
    start_result = fl.start_task(task_id)
    print(f"  结果: {start_result.get('success')}, 第一轮: {start_result.get('first_round')}")

    # 模拟客户端提交
    print("\n模拟客户端提交:")
    for round_num in range(1, 6):
        for i in range(3):
            cid = f"test-client-{i+1}"
            weights = {
                'layer1': [0.1 + i * 0.01 + round_num * 0.001,
                          0.2 + i * 0.02 + round_num * 0.002,
                          0.3 + i * 0.03 + round_num * 0.003],
                'layer2': [0.4 + i * 0.01, 0.5 + i * 0.02],
                'bias': 0.01 + i * 0.001
            }
            acc = 0.7 + i * 0.05 + round_num * 0.02
            fl.submit_update(task_id, cid, weights, sample_count=1000,
                            accuracy=round(acc, 4), loss=round(0.5 - i*0.1, 4))

        # 聚合
        agg_result = fl.aggregate_and_next_round(task_id)
        if agg_result.get('success'):
            print(f"  第{round_num}轮: {agg_result['participating_clients']}个客户端, "
                  f"准确率={agg_result.get('avg_accuracy')}, "
                  f"下一轮={agg_result.get('next_round')}")

    # 任务统计
    print("\n任务统计:")
    stats = fl.get_task_stats(task_id)
    print(f"  总客户端: {stats['total_clients']}")
    print(f"  总更新: {stats['total_updates']}")
    print(f"  轮次数: {stats['round_count']}")
    for r in stats['rounds']:
        print(f"    轮{r['round']}: acc={r['accuracy']}, clients={r['clients']}")

    # 异常检测
    print("\n异常客户端检测:")
    anomaly = fl.detect_anomalous_clients(task_id, round_number=3)
    print(f"  异常数: {len(anomaly.get('anomalous', []))}")

    print(f"\n最终统计: {fl.get_statistics()}")

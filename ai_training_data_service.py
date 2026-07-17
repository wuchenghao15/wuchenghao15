#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI训练数据管理服务
提供数据集管理、数据标注和数据增强功能
"""

import os
import sys
import json
import time
import random
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print


class Dataset:
    """数据集"""

    def __init__(self, dataset_id: str, name: str, description: str = '',
                 data_type: str = 'text', format: str = 'jsonl',
                 tags: List[str] = None):
        self.dataset_id = dataset_id
        self.name = name
        self.description = description
        self.data_type = data_type  # text, image, audio, multimodal
        self.format = format  # jsonl, csv, parquet
        self.tags = tags or []
        self.samples: List[Dict[str, Any]] = []
        self.labeled_count = 0
        self.unlabeled_count = 0
        self.validation_count = 0
        self.is_active = True
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def add_sample(self, content: str, label: str = '',
                   metadata: Dict[str, Any] = None) -> str:
        """添加样本"""
        sample_id = f"smp_{int(time.time()*1000)}_{random.randint(1000,9999)}"

        sample = {
            'sample_id': sample_id,
            'content': content,
            'label': label,
            'metadata': metadata or {},
            'is_labeled': bool(label),
            'is_validated': False,
            'created_at': datetime.now().isoformat()
        }

        self.samples.append(sample)

        if label:
            self.labeled_count += 1
        else:
            self.unlabeled_count += 1

        self.updated_at = datetime.now().isoformat()
        return sample_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            'dataset_id': self.dataset_id,
            'name': self.name,
            'description': self.description,
            'data_type': self.data_type,
            'format': self.format,
            'tags': self.tags,
            'total_samples': len(self.samples),
            'labeled_count': self.labeled_count,
            'unlabeled_count': self.unlabeled_count,
            'validation_count': self.validation_count,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class AITrainingDataService:
    """AI训练数据管理服务"""

    def __init__(self):
        self.datasets: Dict[str, Dataset] = {}
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_datasets()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    data_type TEXT DEFAULT 'text',
                    format TEXT DEFAULT 'jsonl',
                    tags TEXT,
                    total_samples INTEGER DEFAULT 0,
                    labeled_count INTEGER DEFAULT 0,
                    unlabeled_count INTEGER DEFAULT 0,
                    validation_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id TEXT NOT NULL UNIQUE,
                    dataset_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    label TEXT,
                    metadata TEXT,
                    is_labeled INTEGER DEFAULT 0,
                    is_validated INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'manual',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_data_augmentation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    original_count INTEGER DEFAULT 0,
                    generated_count INTEGER DEFAULT 0,
                    params TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_training_samples_dataset ON ai_training_samples(dataset_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[训练数据] 初始化数据库失败: {e}")

    def _register_default_datasets(self):
        """注册默认数据集"""
        defaults = [
            Dataset('ds_qa', '问答数据集', '系统问答训练数据', 'text', 'jsonl', ['qa', 'training']),
            Dataset('ds_intent', '意图分类数据集', '用户意图分类训练数据', 'text', 'jsonl', ['intent', 'classification']),
            Dataset('ds_summary', '摘要数据集', '文本摘要训练数据', 'text', 'jsonl', ['summary']),
            Dataset('ds_feedback', '反馈数据集', '用户反馈训练数据', 'text', 'jsonl', ['feedback', 'rlhf']),
        ]

        # 为问答数据集添加示例
        qa_samples = [
            ('如何重置密码？', 'password_reset'),
            ('系统支持哪些浏览器？', 'compatibility'),
            ('如何导出数据？', 'data_export'),
            ('怎样创建新用户？', 'user_management'),
            ('如何查看系统日志？', 'system_logs'),
        ]

        for content, label in qa_samples:
            defaults[0].add_sample(content, label)

        # 为意图分类数据集添加示例
        intent_samples = [
            ('帮我搜索文件', 'search'),
            ('执行系统命令', 'command'),
            ('你好，谢谢', 'chat'),
            ('分析这组数据', 'analysis'),
            ('生成报表', 'command'),
        ]

        for content, label in intent_samples:
            defaults[1].add_sample(content, label)

        for dataset in defaults:
            self.datasets[dataset.dataset_id] = dataset
            self._save_dataset_to_db(dataset)

    def _save_dataset_to_db(self, dataset: Dataset):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_datasets
                (dataset_id, name, description, data_type, format, tags,
                 total_samples, labeled_count, unlabeled_count, validation_count,
                 is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset.dataset_id, dataset.name, dataset.description,
                dataset.data_type, dataset.format, json.dumps(dataset.tags),
                len(dataset.samples), dataset.labeled_count,
                dataset.unlabeled_count, dataset.validation_count,
                1 if dataset.is_active else 0, dataset.updated_at
            ))

            for sample in dataset.samples:
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_training_samples
                    (sample_id, dataset_id, content, label, metadata,
                     is_labeled, is_validated, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sample['sample_id'], dataset.dataset_id,
                    sample['content'], sample['label'],
                    json.dumps(sample['metadata']),
                    1 if sample['is_labeled'] else 0,
                    1 if sample['is_validated'] else 0,
                    sample.get('source', 'manual')
                ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[训练数据] 保存数据集失败: {e}")

    def create_dataset(self, name: str, description: str = '',
                       data_type: str = 'text', format: str = 'jsonl',
                       tags: List[str] = None) -> str:
        """创建数据集"""
        import uuid
        dataset_id = f"ds_{uuid.uuid4().hex[:8]}"

        dataset = Dataset(dataset_id, name, description, data_type, format, tags)

        with self.lock:
            self.datasets[dataset_id] = dataset

        self._save_dataset_to_db(dataset)
        logger(f"[训练数据] 创建数据集: {name}")

        return dataset_id

    def add_samples(self, dataset_id: str, samples: List[Dict[str, Any]]) -> int:
        """批量添加样本"""
        with self.lock:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return 0

            count = 0
            for s in samples:
                content = s.get('content', '')
                label = s.get('label', '')
                metadata = s.get('metadata', {})

                dataset.add_sample(content, label, metadata)
                count += 1

        self._save_dataset_to_db(dataset)
        return count

    def label_sample(self, dataset_id: str, sample_id: str,
                     label: str) -> bool:
        """标注样本"""
        with self.lock:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return False

            for sample in dataset.samples:
                if sample['sample_id'] == sample_id:
                    if not sample['is_labeled']:
                        dataset.labeled_count += 1
                        dataset.unlabeled_count = max(0, dataset.unlabeled_count - 1)

                    sample['label'] = label
                    sample['is_labeled'] = True
                    dataset.updated_at = datetime.now().isoformat()

                    self._save_dataset_to_db(dataset)
                    return True

        return False

    def validate_sample(self, dataset_id: str, sample_id: str) -> bool:
        """验证样本"""
        with self.lock:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return False

            for sample in dataset.samples:
                if sample['sample_id'] == sample_id:
                    if not sample['is_validated']:
                        sample['is_validated'] = True
                        dataset.validation_count += 1
                        dataset.updated_at = datetime.now().isoformat()

                    self._save_dataset_to_db(dataset)
                    return True

        return False

    def augment_data(self, dataset_id: str, operation: str = 'synonym',
                     count: int = 10, params: Dict[str, Any] = None) -> int:
        """数据增强"""
        with self.lock:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return 0

            original_count = len(dataset.samples)
            generated = 0

            if operation == 'synonym':
                # 同义词替换增强
                for sample in list(dataset.samples):
                    if generated >= count:
                        break

                    content = sample['content']
                    # 简单的伪同义词替换
                    augmented = content.replace('系统', '平台').replace('如何', '怎么')
                    if augmented != content:
                        dataset.add_sample(augmented, sample['label'],
                                         {'source': 'augmentation', 'operation': 'synonym'})
                        generated += 1

            elif operation == 'paraphrase':
                # 改写增强
                for sample in list(dataset.samples):
                    if generated >= count:
                        break

                    content = sample['content']
                    augmented = f"请问{content}"
                    dataset.add_sample(augmented, sample['label'],
                                     {'source': 'augmentation', 'operation': 'paraphrase'})
                    generated += 1

            elif operation == 'noise':
                # 噪声增强
                for sample in list(dataset.samples):
                    if generated >= count:
                        break

                    content = sample['content']
                    # 添加轻微噪声
                    chars = list(content)
                    if len(chars) > 3:
                        pos = random.randint(0, len(chars) - 1)
                        chars[pos] = random.choice('abcdefghijklmnopqrstuvwxyz')
                        augmented = ''.join(chars)
                        dataset.add_sample(augmented, sample['label'],
                                         {'source': 'augmentation', 'operation': 'noise'})
                        generated += 1

            elif operation == 'back_translation':
                # 回译增强（模拟）
                for sample in list(dataset.samples):
                    if generated >= count:
                        break

                    content = sample['content']
                    augmented = f"（翻译版）{content}"
                    dataset.add_sample(augmented, sample['label'],
                                     {'source': 'augmentation', 'operation': 'back_translation'})
                    generated += 1

        self._save_dataset_to_db(dataset)
        self._log_augmentation(dataset_id, operation, original_count, generated, params)

        logger(f"[训练数据] 数据增强: {operation}, 生成 {generated} 条")
        return generated

    def _log_augmentation(self, dataset_id: str, operation: str,
                          original_count: int, generated_count: int,
                          params: Dict[str, Any]):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO ai_data_augmentation_logs
                (dataset_id, operation, original_count, generated_count, params)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                dataset_id, operation, original_count,
                generated_count, json.dumps(params or {})
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = self.datasets.get(dataset_id)
        return dataset.to_dict() if dataset else None

    def get_samples(self, dataset_id: str, labeled: bool = None,
                    validated: bool = None, limit: int = 100) -> List[Dict[str, Any]]:
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return []

        samples = dataset.samples

        if labeled is not None:
            samples = [s for s in samples if s['is_labeled'] == labeled]
        if validated is not None:
            samples = [s for s in samples if s['is_validated'] == validated]

        return samples[:limit]

    def get_datasets(self, active_only: bool = False) -> List[Dict[str, Any]]:
        with self.lock:
            datasets = list(self.datasets.values())
            if active_only:
                datasets = [d for d in datasets if d.is_active]
            return [d.to_dict() for d in datasets]

    def split_dataset(self, dataset_id: str, train_ratio: float = 0.8,
                      val_ratio: float = 0.1) -> Dict[str, Any]:
        """分割数据集（训练/验证/测试）"""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {}

        samples = list(dataset.samples)
        random.shuffle(samples)

        total = len(samples)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        return {
            'dataset_id': dataset_id,
            'total': total,
            'train': len(samples[:train_end]),
            'validation': len(samples[train_end:val_end]),
            'test': len(samples[val_end:]),
            'ratios': {'train': train_ratio, 'val': val_ratio, 'test': 1 - train_ratio - val_ratio}
        }

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_samples = sum(len(d.samples) for d in self.datasets.values())
            total_labeled = sum(d.labeled_count for d in self.datasets.values())
            total_validated = sum(d.validation_count for d in self.datasets.values())

            return {
                'total_datasets': len(self.datasets),
                'total_samples': total_samples,
                'labeled_samples': total_labeled,
                'unlabeled_samples': total_samples - total_labeled,
                'validated_samples': total_validated,
                'label_rate': round(total_labeled / max(1, total_samples) * 100, 2)
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_datasets': len(self.datasets)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[训练数据] 训练数据服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[训练数据] 训练数据服务已停止")


ai_training_data_service = AITrainingDataService()

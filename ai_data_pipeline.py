#!/usr/bin/env python3
"""
MTSCOS AI 数据预处理管道 (v14.6.0)
====================================
AI 数据预处理和特征工程管道服务。

核心能力：
1. 数据清洗 - 缺失值/异常值/重复值处理
2. 数据转换 - 编码/归一化/标准化
3. 特征工程 - 特征提取/选择/构造
4. 文本预处理 - 分词/去停用词/词干化
5. 数据分割 - 训练/验证/测试集划分
6. 数据增强 - 噪声/采样/平衡
7. 管道编排 - 步骤链式执行
8. 持久化 - 处理结果入库
"""
import os
import re
import json
import math
import random
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_data_pipeline.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIDataPipeline')


# ========== 停用词表 ==========

DEFAULT_STOPWORDS = {
    # 中文停用词
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '这', '那', '它', '他', '她', '我们', '你们', '他们', '什么', '怎么', '为什么',
    # 英文停用词
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'
}


# ========== 处理器函数 ==========

def clean_missing(values: List[Any], strategy: str = 'mean',
                 fill_value: Any = None) -> Tuple[List[Any], Dict]:
    """缺失值处理"""
    stats = {'strategy': strategy, 'original_count': len(values), 'missing_count': 0}
    cleaned = list(values)

    # 统计缺失
    for v in cleaned:
        if v is None or (isinstance(v, str) and v.strip() == '') or (isinstance(v, float) and math.isnan(v)):
            stats['missing_count'] += 1

    if stats['missing_count'] == 0:
        return cleaned, stats

    # 填充
    if strategy == 'drop':
        cleaned = [v for v in cleaned if v is not None and not (isinstance(v, str) and v.strip() == '')]
    elif strategy == 'fill':
        fill = fill_value if fill_value is not None else 0
        cleaned = [fill if v is None or (isinstance(v, str) and v.strip() == '') else v for v in cleaned]
    elif strategy == 'mean':
        nums = [float(v) for v in cleaned if v is not None and _is_number(v)]
        mean = sum(nums) / len(nums) if nums else 0
        cleaned = [mean if v is None or (isinstance(v, str) and v.strip() == '') else v for v in cleaned]
    elif strategy == 'median':
        nums = sorted([float(v) for v in cleaned if v is not None and _is_number(v)])
        median = nums[len(nums) // 2] if nums else 0
        cleaned = [median if v is None or (isinstance(v, str) and v.strip() == '') else v for v in cleaned]
    elif strategy == 'mode':
        # 众数
        counter = {}
        for v in cleaned:
            if v is not None and not (isinstance(v, str) and v.strip() == ''):
                key = str(v)
                counter[key] = counter.get(key, 0) + 1
        mode = max(counter, key=counter.get) if counter else 0
        try:
            mode = float(mode)
        except (ValueError, TypeError):
            pass
        cleaned = [mode if v is None or (isinstance(v, str) and v.strip() == '') else v for v in cleaned]
    elif strategy == 'forward':
        # 前向填充
        last_valid = None
        for i, v in enumerate(cleaned):
            if v is None or (isinstance(v, str) and v.strip() == ''):
                cleaned[i] = last_valid
            else:
                last_valid = v

    stats['cleaned_count'] = len(cleaned)
    return cleaned, stats


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def clean_outliers(values: List[float], method: str = 'iqr',
                  threshold: float = 1.5) -> Tuple[List[float], Dict]:
    """异常值处理"""
    stats = {'method': method, 'original_count': len(values), 'outlier_count': 0}
    if not values:
        return values, stats

    nums = [float(v) for v in values if _is_number(v)]
    if len(nums) < 4:
        return values, stats

    if method == 'iqr':
        sorted_nums = sorted(nums)
        q1 = sorted_nums[len(sorted_nums) // 4]
        q3 = sorted_nums[3 * len(sorted_nums) // 4]
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
    elif method == 'zscore':
        mean = sum(nums) / len(nums)
        std = math.sqrt(sum((x - mean) ** 2 for x in nums) / len(nums))
        if std == 0:
            return values, stats
        lower = mean - threshold * std
        upper = mean + threshold * std
    else:
        return values, stats

    cleaned = []
    outliers = []
    for v in values:
        if _is_number(v):
            num = float(v)
            if num < lower or num > upper:
                stats['outlier_count'] += 1
                outliers.append(num)
                # 用边界值替代
                cleaned.append(lower if num < lower else upper)
            else:
                cleaned.append(num)
        else:
            cleaned.append(v)

    stats['lower_bound'] = round(lower, 4)
    stats['upper_bound'] = round(upper, 4)
    return cleaned, stats


def clean_duplicates(records: List[Dict], key_fields: List[str] = None) -> Tuple[List[Dict], Dict]:
    """重复记录处理"""
    stats = {'original_count': len(records), 'duplicate_count': 0}
    if not records:
        return records, stats

    key_fields = key_fields or list(records[0].keys()) if records else []
    seen = set()
    cleaned = []

    for record in records:
        # 生成唯一键
        key_parts = []
        for field in key_fields:
            key_parts.append(str(record.get(field, '')))
        key = '|'.join(key_parts)

        if key in seen:
            stats['duplicate_count'] += 1
        else:
            seen.add(key)
            cleaned.append(record)

    stats['cleaned_count'] = len(cleaned)
    return cleaned, stats


def normalize_minmax(values: List[float]) -> Tuple[List[float], Dict]:
    """Min-Max 归一化"""
    stats = {'method': 'minmax'}
    if not values:
        return values, stats

    nums = [float(v) for v in values if _is_number(v)]
    if not nums:
        return values, stats

    min_v = min(nums)
    max_v = max(nums)
    range_v = max_v - min_v

    if range_v == 0:
        return [0.5] * len(values), {**stats, 'min': min_v, 'max': max_v}

    normalized = []
    for v in values:
        if _is_number(v):
            normalized.append(round((float(v) - min_v) / range_v, 6))
        else:
            normalized.append(v)

    stats['min'] = min_v
    stats['max'] = max_v
    return normalized, stats


def normalize_zscore(values: List[float]) -> Tuple[List[float], Dict]:
    """Z-Score 标准化"""
    stats = {'method': 'zscore'}
    if not values:
        return values, stats

    nums = [float(v) for v in values if _is_number(v)]
    if not nums:
        return values, stats

    mean = sum(nums) / len(nums)
    std = math.sqrt(sum((x - mean) ** 2 for x in nums) / len(nums))

    if std == 0:
        return [0.0] * len(values), {**stats, 'mean': mean, 'std': std}

    normalized = []
    for v in values:
        if _is_number(v):
            normalized.append(round((float(v) - mean) / std, 6))
        else:
            normalized.append(v)

    stats['mean'] = mean
    stats['std'] = std
    return normalized, stats


def encode_label(values: List[Any]) -> Tuple[List[int], Dict]:
    """标签编码"""
    stats = {'method': 'label'}
    label_map = {}
    next_id = 0
    encoded = []

    for v in values:
        if v not in label_map:
            label_map[v] = next_id
            next_id += 1
        encoded.append(label_map[v])

    stats['mapping'] = {str(k): v for k, v in label_map.items()}
    return encoded, stats


def encode_onehot(values: List[Any]) -> Tuple[List[List[int]], Dict]:
    """独热编码"""
    stats = {'method': 'onehot'}
    categories = sorted(set(values), key=str)
    cat_index = {c: i for i, c in enumerate(categories)}

    encoded = []
    for v in values:
        vec = [0] * len(categories)
        if v in cat_index:
            vec[cat_index[v]] = 1
        encoded.append(vec)

    stats['categories'] = [str(c) for c in categories]
    return encoded, stats


def tokenize_text(text: str, language: str = 'auto') -> List[str]:
    """文本分词"""
    if not text:
        return []

    tokens = []
    # 英文单词
    en_words = re.findall(r'[a-zA-Z]+', text.lower())
    tokens.extend(en_words)

    # 中文按字
    cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
    tokens.extend(cn_chars)

    # 数字
    numbers = re.findall(r'\d+', text)
    tokens.extend(numbers)

    return tokens


def remove_stopwords(tokens: List[str], stopwords: set = None) -> List[str]:
    """去停用词"""
    stopwords = stopwords or DEFAULT_STOPWORDS
    return [t for t in tokens if t.lower() not in stopwords and t not in stopwords]


def split_dataset(records: List[Any], train_ratio: float = 0.7,
                 val_ratio: float = 0.15, seed: int = 42) -> Dict:
    """数据集分割"""
    n = len(records)
    if n == 0:
        return {'train': [], 'val': [], 'test': []}

    random.seed(seed)
    shuffled = list(records)
    random.shuffle(shuffled)

    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    return {
        'train': shuffled[:train_end],
        'val': shuffled[train_end:val_end],
        'test': shuffled[val_end:],
        'stats': {
            'total': n,
            'train': train_end,
            'val': val_end - train_end,
            'test': n - val_end
        }
    }


def augment_noise(values: List[float], noise_level: float = 0.05,
                 seed: int = 42) -> List[float]:
    """数据增强：添加噪声"""
    random.seed(seed)
    if not values:
        return values

    nums = [float(v) for v in values if _is_number(v)]
    if not nums:
        return values

    mean = sum(nums) / len(nums)
    std = math.sqrt(sum((x - mean) ** 2 for x in nums) / len(nums)) if len(nums) > 1 else 1

    augmented = []
    for v in values:
        if _is_number(v):
            noise = random.gauss(0, std * noise_level)
            augmented.append(round(float(v) + noise, 6))
        else:
            augmented.append(v)
    return augmented


def augment_oversample(records: List[Dict], label_field: str,
                      target_count: int = None) -> List[Dict]:
    """过采样（针对不平衡数据）"""
    if not records:
        return records

    # 按标签分组
    groups = {}
    for r in records:
        label = r.get(label_field)
        if label not in groups:
            groups[label] = []
        groups[label].append(r)

    # 找最大数量
    max_count = target_count or max(len(g) for g in groups.values())

    # 过采样
    result = []
    for label, group in groups.items():
        result.extend(group)
        if len(group) < max_count:
            needed = max_count - len(group)
            for _ in range(needed):
                result.append(random.choice(group))

    return result


# ========== 预处理管道 ==========

class AIDataPipeline:
    """AI 数据预处理管道"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        # 注册处理器
        self.processors: Dict[str, Callable] = {
            'clean_missing': clean_missing,
            'clean_outliers': clean_outliers,
            'clean_duplicates': clean_duplicates,
            'normalize_minmax': normalize_minmax,
            'normalize_zscore': normalize_zscore,
            'encode_label': encode_label,
            'encode_onehot': encode_onehot,
            'tokenize_text': tokenize_text,
            'remove_stopwords': remove_stopwords,
            'split_dataset': split_dataset,
            'augment_noise': augment_noise,
            'augment_oversample': augment_oversample,
        }

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_data_pipelines (
                        pipeline_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        steps TEXT NOT NULL,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_data_pipeline_runs (
                        run_id TEXT PRIMARY KEY,
                        pipeline_id TEXT,
                        input_data TEXT,
                        output_data TEXT,
                        step_results TEXT,
                        status TEXT,
                        duration_ms INTEGER,
                        created_at TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化数据管道数据库失败: {e}")

    # ========== 管道管理 ==========

    def create_pipeline(self, name: str, steps: List[Dict],
                       description: str = '') -> Dict:
        """创建预处理管道

        steps 格式: [
            {'processor': 'clean_missing', 'params': {'strategy': 'mean'}},
            {'processor': 'normalize_minmax', 'params': {}}
        ]
        """
        # 校验步骤
        for step in steps:
            proc_name = step.get('processor')
            if proc_name not in self.processors:
                return {'success': False, 'error': f'未知处理器: {proc_name}'}

        pipeline_id = f"DP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_data_pipelines
                    (pipeline_id, name, description, steps, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pipeline_id, name, description,
                    json.dumps(steps, ensure_ascii=False),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'pipeline_id': pipeline_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_pipeline(self, pipeline_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_data_pipelines WHERE pipeline_id = ?', (pipeline_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'pipeline_id': row[0], 'name': row[1], 'description': row[2],
                    'steps': json.loads(row[3]) if row[3] else [],
                    'created_at': row[4], 'updated_at': row[5]
                }
        except Exception:
            return None

    def list_pipelines(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT pipeline_id, name, description, created_at FROM ai_data_pipelines ORDER BY created_at DESC')
                return [
                    {'pipeline_id': r[0], 'name': r[1], 'description': r[2], 'created_at': r[3]}
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 管道执行 ==========

    def execute(self, pipeline_id: str, input_data: Any) -> Dict:
        """执行管道"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return {'success': False, 'error': '管道不存在'}

        return self._execute_steps(pipeline['steps'], input_data, pipeline_id)

    def execute_steps(self, steps: List[Dict], input_data: Any,
                     name: str = 'adhoc') -> Dict:
        """直接执行步骤（无需持久化管道）"""
        return self._execute_steps(steps, input_data, None, name)

    def _execute_steps(self, steps: List[Dict], input_data: Any,
                      pipeline_id: Optional[str], name: str = '') -> Dict:
        run_id = f"DPR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        start_time = datetime.now()
        current_data = input_data
        step_results = []

        try:
            for i, step in enumerate(steps):
                proc_name = step.get('processor')
                params = step.get('params', {})

                processor = self.processors.get(proc_name)
                if not processor:
                    return {'success': False, 'error': f'未知处理器: {proc_name}', 'step': i}

                step_start = datetime.now()
                try:
                    # 处理器有两种返回格式：(result, stats) 或 result
                    result = processor(current_data, **params)
                    if isinstance(result, tuple) and len(result) == 2:
                        current_data, stats = result
                    else:
                        current_data = result
                        stats = {}

                    step_duration = int((datetime.now() - step_start).total_seconds() * 1000)
                    step_results.append({
                        'step': i,
                        'processor': proc_name,
                        'params': params,
                        'success': True,
                        'duration_ms': step_duration,
                        'stats': stats
                    })
                except Exception as e:
                    step_results.append({
                        'step': i,
                        'processor': proc_name,
                        'success': False,
                        'error': str(e)
                    })
                    raise

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # 保存运行记录
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 输入输出过大时只存摘要
                    input_str = json.dumps(input_data, ensure_ascii=False, default=str)
                    output_str = json.dumps(current_data, ensure_ascii=False, default=str)
                    if len(input_str) > 10000:
                        input_str = input_str[:10000] + '...[truncated]'
                    if len(output_str) > 10000:
                        output_str = output_str[:10000] + '...[truncated]'

                    cursor.execute('''
                        INSERT INTO ai_data_pipeline_runs
                        (run_id, pipeline_id, input_data, output_data, step_results,
                         status, duration_ms, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        run_id, pipeline_id, input_str, output_str,
                        json.dumps(step_results, ensure_ascii=False, default=str),
                        'success', duration_ms, datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"保存管道运行记录失败: {e}")

            return {
                'success': True,
                'run_id': run_id,
                'output': current_data,
                'step_results': step_results,
                'duration_ms': duration_ms
            }
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_data_pipeline_runs
                        (run_id, pipeline_id, input_data, output_data, step_results,
                         status, duration_ms, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        run_id, pipeline_id, json.dumps(input_data, default=str), None,
                        json.dumps(step_results, ensure_ascii=False, default=str),
                        'failed', duration_ms, datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception:
                pass

            return {
                'success': False,
                'run_id': run_id,
                'error': str(e),
                'step_results': step_results,
                'duration_ms': duration_ms
            }

    # ========== 单处理器调用 ==========

    def process(self, processor_name: str, data: Any, **params) -> Dict:
        """直接调用单个处理器"""
        processor = self.processors.get(processor_name)
        if not processor:
            return {'success': False, 'error': f'未知处理器: {processor_name}'}

        try:
            start_time = datetime.now()
            result = processor(data, **params)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if isinstance(result, tuple) and len(result) == 2:
                output, stats = result
            else:
                output = result
                stats = {}

            return {
                'success': True,
                'processor': processor_name,
                'params': params,
                'output': output,
                'stats': stats,
                'duration_ms': duration_ms
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 查询 ==========

    def list_processors(self) -> List[Dict]:
        """列出所有可用处理器"""
        return [
            {'name': name, 'doc': fn.__doc__ or ''}
            for name, fn in self.processors.items()
        ]

    def get_run(self, run_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_data_pipeline_runs WHERE run_id = ?', (run_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'run_id': row[0], 'pipeline_id': row[1],
                    'input_data': row[2], 'output_data': row[3],
                    'step_results': json.loads(row[4]) if row[4] else [],
                    'status': row[5], 'duration_ms': row[6], 'created_at': row[7]
                }
        except Exception:
            return None

    def list_runs(self, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT run_id, pipeline_id, status, duration_ms, created_at
                    FROM ai_data_pipeline_runs
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                return [
                    {
                        'run_id': r[0], 'pipeline_id': r[1], 'status': r[2],
                        'duration_ms': r[3], 'created_at': r[4]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []


# ========== 模块入口 ==========

if __name__ == '__main__':
    pipeline = AIDataPipeline()

    print("可用处理器:")
    for p in pipeline.list_processors():
        print(f"  - {p['name']}: {p['doc'][:50] if p['doc'] else ''}")

    # 测试1：缺失值处理
    print("\n测试1: 缺失值处理")
    data = [1.0, 2.0, None, 4.0, None, 6.0, 7.0]
    result = pipeline.process('clean_missing', data, strategy='mean')
    print(f"  输入: {data}")
    print(f"  输出: {result['output']}")
    print(f"  统计: {result['stats']}")

    # 测试2：归一化
    print("\n测试2: Min-Max 归一化")
    data = [10, 20, 30, 40, 50]
    result = pipeline.process('normalize_minmax', data)
    print(f"  输入: {data}")
    print(f"  输出: {result['output']}")

    # 测试3：异常值处理
    print("\n测试3: 异常值检测")
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
    result = pipeline.process('clean_outliers', data, method='iqr', threshold=1.5)
    print(f"  输入: {data}")
    print(f"  输出: {result['output']}")
    print(f"  统计: {result['stats']}")

    # 测试4：管道执行
    print("\n测试4: 创建并执行管道")
    steps = [
        {'processor': 'clean_missing', 'params': {'strategy': 'median'}},
        {'processor': 'normalize_minmax', 'params': {}}
    ]
    create_result = pipeline.create_pipeline('数值预处理管道', steps, '缺失值填充+归一化')
    print(f"  创建: {create_result}")

    if create_result.get('success'):
        exec_result = pipeline.execute(create_result['pipeline_id'], [1, 2, None, 4, 5])
        print(f"  执行成功: {exec_result['success']}")
        print(f"  输出: {exec_result['output']}")
        for sr in exec_result['step_results']:
            print(f"  步骤 {sr['step']}: {sr['processor']} ({sr['duration_ms']}ms)")

    # 测试5：文本预处理
    print("\n测试5: 文本分词和去停用词")
    text = "the quick brown fox jumps over the lazy dog 真的是一只快速的狐狸"
    tokens = tokenize_text(text)
    print(f"  分词结果: {tokens}")
    filtered = remove_stopwords(tokens)
    print(f"  去停用词: {filtered}")

    # 测试6：数据集分割
    print("\n测试6: 数据集分割")
    records = [{'id': i, 'value': random.random()} for i in range(100)]
    splits = split_dataset(records, train_ratio=0.7, val_ratio=0.15)
    print(f"  分割: {splits['stats']}")

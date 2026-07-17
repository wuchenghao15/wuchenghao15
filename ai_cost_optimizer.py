#!/usr/bin/env python3
"""
MTSCOS AI 成本优化服务 (v14.7.0)
===================================
AI 服务成本优化和资源效率管理服务。

核心能力：
1. 成本追踪 - 模型调用费用、训练成本、推理成本
2. 资源优化 - 计算资源分配和利用率优化
3. 缓存策略 - 预测结果缓存和命中率管理
4. 模型压缩 - 量化、剪枝、蒸馏建议
5. 自动缩放 - 根据负载自动调整资源
6. 预算管理 - 成本预算设置和告警
7. 成本预测 - 基于历史数据的成本预测
8. ROI 分析 - 投资回报率分析
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_cost_optimizer.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AICostOptimizer')


# ========== 成本计算 ==========

# 默认成本模型
DEFAULT_COST_MODEL = {
    'gpt35': {
        'input_per_1k_tokens': 0.0015,
        'output_per_1k_tokens': 0.002,
        'name': 'GPT-3.5-Turbo'
    },
    'gpt4': {
        'input_per_1k_tokens': 0.03,
        'output_per_1k_tokens': 0.06,
        'name': 'GPT-4'
    },
    'embedding': {
        'per_1k_tokens': 0.0001,
        'name': 'Embedding模型'
    },
    'gpu_training_hour': {
        'v100': 3.0,
        'a100': 8.0,
        't4': 0.75,
        'name': 'GPU训练小时'
    },
    'storage_gb_month': 0.15,
    'compute_cpu_hour': 0.05,
}


def calculate_inference_cost(model_id: str, input_tokens: int, output_tokens: int,
                           cost_model: Dict = None) -> Dict:
    """计算推理成本"""
    cost_model = cost_model or DEFAULT_COST_MODEL
    model_info = cost_model.get(model_id, {})

    if model_id in ('gpt35', 'gpt4'):
        input_cost = (input_tokens / 1000) * model_info.get('input_per_1k_tokens', 0)
        output_cost = (output_tokens / 1000) * model_info.get('output_per_1k_tokens', 0)
        total = input_cost + output_cost
    elif model_id == 'embedding':
        total = (input_tokens / 1000) * model_info.get('per_1k_tokens', 0)
        input_cost = total
        output_cost = 0
    else:
        total = 0
        input_cost = 0
        output_cost = 0

    return {
        'model_id': model_id,
        'model_name': model_info.get('name', model_id),
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'input_cost': round(input_cost, 6),
        'output_cost': round(output_cost, 6),
        'total_cost': round(total, 6)
    }


def calculate_training_cost(gpu_type: str, hours: float,
                           storage_gb: float = 0,
                           cost_model: Dict = None) -> Dict:
    """计算训练成本"""
    cost_model = cost_model or DEFAULT_COST_MODEL
    gpu_costs = cost_model.get('gpu_training_hour', {})
    gpu_rate = gpu_costs.get(gpu_type, 0)
    storage_cost = storage_gb * cost_model.get('storage_gb_month', 0) / 30 / 24 * hours

    compute_cost = gpu_rate * hours
    total = compute_cost + storage_cost

    return {
        'gpu_type': gpu_type,
        'hours': hours,
        'gpu_cost_rate': gpu_rate,
        'gpu_cost': round(compute_cost, 6),
        'storage_gb': storage_gb,
        'storage_cost': round(storage_cost, 6),
        'total_cost': round(total, 6)
    }


# ========== 缓存策略 ==========

class CacheOptimizer:
    """缓存优化器"""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._access_count = defaultdict(int)
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            item = self._cache[key]
            if (datetime.now() - datetime.fromisoformat(item['created_at'])).total_seconds() > self.ttl:
                del self._cache[key]
                self._miss_count += 1
                return None
            self._access_count[key] += 1
            self._hit_count += 1
            return item['value']
        self._miss_count += 1
        return None

    def set(self, key: str, value: Any, cost_saved: float = 0):
        if len(self._cache) >= self.max_size:
            self._evict()
        self._cache[key] = {
            'value': value,
            'cost_saved': cost_saved,
            'created_at': datetime.now().isoformat()
        }

    def _evict(self):
        """LRU+成本混合淘汰策略"""
        if not self._cache:
            return
        # 淘汰访问次数最少且节省成本最低的
        min_score = float('inf')
        evict_key = None
        for key in list(self._cache.keys()):
            accesses = self._access_count.get(key, 0)
            cost_saved = self._cache[key].get('cost_saved', 0)
            score = accesses * cost_saved  # 综合得分
            if score < min_score:
                min_score = score
                evict_key = key
        if evict_key:
            del self._cache[evict_key]
            if evict_key in self._access_count:
                del self._access_count[evict_key]

    def stats(self) -> Dict:
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0
        total_saved = sum(item.get('cost_saved', 0) for item in self._cache.values())
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': round(hit_rate, 4),
            'estimated_savings': round(total_saved, 6),
            'ttl_seconds': self.ttl
        }


# ========== 成本优化服务 ==========

class AICostOptimizer:
    """AI 成本优化服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._cache = CacheOptimizer()
        self._budget_alert_callbacks = []

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cost_records (
                        record_id TEXT PRIMARY KEY,
                        cost_type TEXT NOT NULL,
                        model_id TEXT,
                        category TEXT,
                        amount REAL NOT NULL,
                        tokens INTEGER,
                        duration_sec INTEGER,
                        metadata TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cost_budgets (
                        budget_id TEXT PRIMARY KEY,
                        budget_name TEXT,
                        category TEXT,
                        amount REAL NOT NULL,
                        period TEXT DEFAULT 'monthly',
                        used_amount REAL DEFAULT 0,
                        alert_threshold REAL DEFAULT 0.8,
                        alert_triggered INTEGER DEFAULT 0,
                        created_at TEXT,
                        period_start TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS optimization_suggestions (
                        suggestion_id TEXT PRIMARY KEY,
                        category TEXT,
                        priority TEXT,
                        title TEXT,
                        description TEXT,
                        estimated_savings REAL,
                        estimated_effort TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_date ON cost_records(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_type ON cost_records(cost_type)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化成本优化数据库失败: {e}")

    # ========== 成本记录 ==========

    def record_cost(self, cost_type: str, amount: float, model_id: str = None,
                   category: str = None, tokens: int = None,
                   duration_sec: int = None, metadata: Dict = None) -> Dict:
        """记录成本"""
        record_id = f"COST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cost_records
                    (record_id, cost_type, model_id, category, amount, tokens,
                     duration_sec, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record_id, cost_type, model_id, category or cost_type,
                    amount, tokens, duration_sec,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
            # 更新预算
            self._update_budget_usage(category or cost_type, amount)
            return {'success': True, 'record_id': record_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def record_inference(self, model_id: str, input_tokens: int,
                        output_tokens: int, metadata: Dict = None) -> Dict:
        """记录推理成本"""
        cost = calculate_inference_cost(model_id, input_tokens, output_tokens)
        return self.record_cost(
            cost_type='inference',
            amount=cost['total_cost'],
            model_id=model_id,
            category='inference',
            tokens=input_tokens + output_tokens,
            metadata=metadata
        )

    def record_training(self, gpu_type: str, hours: float,
                       storage_gb: float = 0, metadata: Dict = None) -> Dict:
        """记录训练成本"""
        cost = calculate_training_cost(gpu_type, hours, storage_gb)
        return self.record_cost(
            cost_type='training',
            amount=cost['total_cost'],
            model_id=gpu_type,
            category='training',
            duration_sec=int(hours * 3600),
            metadata=metadata
        )

    # ========== 成本查询 ==========

    def get_cost_summary(self, days: int = 30, category: str = None) -> Dict:
        """获取成本汇总"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute('''
                        SELECT SUM(amount), COUNT(*), cost_type, model_id
                        FROM cost_records
                        WHERE created_at >= ? AND category = ?
                        GROUP BY cost_type, model_id
                    ''', (start_date, category))
                else:
                    cursor.execute('''
                        SELECT SUM(amount), COUNT(*), cost_type, model_id
                        FROM cost_records
                        WHERE created_at >= ?
                        GROUP BY cost_type, model_id
                    ''', (start_date,))

                breakdown = [
                    {
                        'cost_type': r[2],
                        'model_id': r[3],
                        'total_amount': round(r[0], 6),
                        'count': r[1]
                    }
                    for r in cursor.fetchall()
                ]

                total_amount = sum(b['total_amount'] for b in breakdown)
                total_count = sum(b['count'] for b in breakdown)

                # 按天统计
                cursor.execute('''
                    SELECT DATE(created_at) as day, SUM(amount)
                    FROM cost_records
                    WHERE created_at >= ?
                    GROUP BY day
                    ORDER BY day
                ''', (start_date,))
                daily = [{'date': r[0], 'amount': round(r[1], 6)} for r in cursor.fetchall()]

                return {
                    'period_days': days,
                    'total_amount': round(total_amount, 6),
                    'total_records': total_count,
                    'breakdown': breakdown,
                    'daily_trend': daily
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_model_costs(self, model_id: str = None, days: int = 30) -> Dict:
        """获取模型成本排行"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if model_id:
                    cursor.execute('''
                        SELECT model_id, SUM(amount), COUNT(*), SUM(tokens)
                        FROM cost_records
                        WHERE created_at >= ? AND model_id = ?
                        GROUP BY model_id
                    ''', (start_date, model_id))
                else:
                    cursor.execute('''
                        SELECT model_id, SUM(amount), COUNT(*), SUM(tokens)
                        FROM cost_records
                        WHERE created_at >= ? AND cost_type = 'inference'
                        GROUP BY model_id
                        ORDER BY SUM(amount) DESC
                        LIMIT 20
                    ''', (start_date,))

                models = [
                    {
                        'model_id': r[0],
                        'total_cost': round(r[1], 6),
                        'call_count': r[2],
                        'total_tokens': r[3] or 0,
                        'avg_cost_per_call': round(r[1] / r[2], 8) if r[2] > 0 else 0
                    }
                    for r in cursor.fetchall()
                ]

                return {
                    'period_days': days,
                    'models': models,
                    'total_model_cost': round(sum(m['total_cost'] for m in models), 6)
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 预算管理 ==========

    def set_budget(self, budget_name: str, amount: float,
                  category: str = 'total', period: str = 'monthly',
                  alert_threshold: float = 0.8) -> Dict:
        """设置预算"""
        budget_id = f"BUDGET-{random.randint(100000, 999999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cost_budgets
                    (budget_id, budget_name, category, amount, period,
                     alert_threshold, created_at, period_start)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    budget_id, budget_name, category, amount, period,
                    alert_threshold, datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'budget_id': budget_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _update_budget_usage(self, category: str, amount: float):
        """更新预算使用量"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 更新对应类别预算
                cursor.execute('''
                    UPDATE cost_budgets
                    SET used_amount = used_amount + ?,
                        alert_triggered = CASE
                            WHEN (used_amount + ?) / amount >= alert_threshold THEN 1
                            ELSE alert_triggered
                        END
                    WHERE category = ? OR category = 'total'
                ''', (amount, amount, category))
                conn.commit()
        except Exception as e:
            logger.error(f"更新预算失败: {e}")

    def get_budgets(self) -> List[Dict]:
        """获取所有预算"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT budget_id, budget_name, category, amount, used_amount,
                           period, alert_threshold, alert_triggered, period_start
                    FROM cost_budgets
                    ORDER BY created_at DESC
                ''')
                budgets = []
                for r in cursor.fetchall():
                    used = r[4]
                    total = r[3]
                    budgets.append({
                        'budget_id': r[0],
                        'budget_name': r[1],
                        'category': r[2],
                        'amount': total,
                        'used_amount': round(used, 6),
                        'usage_percent': round(used / total * 100, 2) if total > 0 else 0,
                        'period': r[5],
                        'alert_threshold': r[6],
                        'alert_triggered': bool(r[7]),
                        'remaining': round(max(0, total - used), 6)
                    })
                return budgets
        except Exception:
            return []

    def check_budget_alerts(self) -> List[Dict]:
        """检查预算告警"""
        budgets = self.get_budgets()
        alerts = [
            b for b in budgets
            if b['usage_percent'] >= b['alert_threshold'] * 100
        ]
        return alerts

    # ========== 缓存优化 ==========

    def cache_get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def cache_set(self, key: str, value: Any, cost_saved: float = 0):
        self._cache.set(key, value, cost_saved)

    def cache_stats(self) -> Dict:
        return self._cache.stats()

    # ========== 优化建议 ==========

    def generate_suggestions(self) -> Dict:
        """生成成本优化建议"""
        suggestions = []
        stats = self.get_cost_summary(days=30)
        model_costs = self.get_model_costs(days=30)
        cache_stats = self.cache_stats()

        # 建议1: 缓存优化
        if cache_stats.get('hit_rate', 0) < 0.5:
            suggestions.append({
                'category': 'cache',
                'priority': 'high',
                'title': '提升缓存命中率',
                'description': f'当前缓存命中率为 {cache_stats.get("hit_rate", 0):.1%}，建议增加缓存容量或优化缓存策略',
                'estimated_savings': round(stats.get('total_amount', 0) * 0.1, 4),
                'estimated_effort': 'low'
            })

        # 建议2: 模型降级
        models = model_costs.get('models', [])
        if models:
            expensive = [m for m in models if m['avg_cost_per_call'] > 0.01]
            if expensive:
                suggestions.append({
                    'category': 'model',
                    'priority': 'medium',
                    'title': '考虑使用更经济的模型',
                    'description': f'有 {len(expensive)} 个高成本模型调用，评估是否可用低成本模型替代',
                    'estimated_savings': round(sum(m['total_cost'] for m in expensive) * 0.3, 4),
                    'estimated_effort': 'medium'
                })

        # 建议3: 请求批处理
        suggestions.append({
            'category': 'batch',
            'priority': 'medium',
            'title': '启用批处理优化',
            description: '对非实时请求使用批处理模式，可降低约 20-30% 计算成本',
            'estimated_savings': round(stats.get('total_amount', 0) * 0.15, 4),
            'estimated_effort': 'medium'
        })

        # 建议4: 模型量化
        suggestions.append({
            'category': 'quantization',
            'priority': 'low',
            'title': '模型量化压缩',
            'description': '对部署的模型进行 INT8/FP16 量化，可减少显存占用和推理成本',
            'estimated_savings': round(stats.get('total_amount', 0) * 0.2, 4),
            'estimated_effort': 'high'
        })

        # 保存建议
        saved_ids = []
        for s in suggestions:
            sid = f"SUG-{random.randint(100000, 999999)}"
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO optimization_suggestions
                        (suggestion_id, category, priority, title, description,
                         estimated_savings, estimated_effort, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sid, s['category'], s['priority'], s['title'],
                        s['description'], s['estimated_savings'],
                        s['estimated_effort'], datetime.now().isoformat()
                    ))
                    conn.commit()
                saved_ids.append(sid)
            except Exception:
                pass

        return {
            'suggestions': suggestions,
            'total_suggestions': len(suggestions),
            'total_estimated_savings': round(sum(s['estimated_savings'] for s in suggestions), 6),
            'saved_ids': saved_ids
        }

    # ========== 成本预测 ==========

    def forecast_cost(self, days: int = 30, forecast_days: int = 30) -> Dict:
        """预测未来成本（基于历史数据的简单线性趋势）"""
        historical = self.get_cost_summary(days=days)
        daily = historical.get('daily_trend', [])

        if len(daily) < 2:
            return {'forecast': [], 'note': '历史数据不足'}

        # 简单线性回归
        n = len(daily)
        x = list(range(n))
        y = [d['amount'] for d in daily]
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0

        # 预测未来
        forecast = []
        last_date = datetime.now()
        for i in range(forecast_days):
            pred_y = mean_y + slope * (n + i)
            forecast.append({
                'date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                'predicted_amount': round(max(0, pred_y), 6)
            })

        total_forecast = round(sum(f['predicted_amount'] for f in forecast), 6)

        return {
            'historical_days': days,
            'forecast_days': forecast_days,
            'daily_forecast': forecast,
            'total_forecast': total_forecast,
            'daily_average': round(mean_y, 6),
            'growth_trend': 'increasing' if slope > 0 else 'decreasing',
            'daily_growth': round(slope, 6)
        }

    # ========== ROI 分析 ==========

    def calculate_roi(self, investment_cost: float,
                     saved_cost: float, improved_efficiency: float = 0,
                     timeframe_days: int = 30) -> Dict:
        """计算投资回报率"""
        total_benefit = saved_cost + improved_efficiency
        net_profit = total_benefit - investment_cost
        roi = (net_profit / investment_cost * 100) if investment_cost > 0 else 0
        payback_days = (investment_cost / (total_benefit / timeframe_days)
                        if total_benefit > 0 else float('inf'))

        return {
            'investment_cost': investment_cost,
            'total_benefit': round(total_benefit, 6),
            'net_profit': round(net_profit, 6),
            'roi_percent': round(roi, 2),
            'payback_days': round(payback_days, 1),
            'timeframe_days': timeframe_days
        }

    # ========== 自动缩放建议 ==========

    def autoscale_suggestion(self, avg_requests_per_sec: float,
                            avg_latency_ms: float,
                            target_latency_ms: float = 500) -> Dict:
        """自动缩放建议"""
        if avg_latency_ms > target_latency_ms * 1.5:
            action = 'scale_out'
            reason = '平均延迟超过目标值1.5倍，需要增加实例'
            recommended_instances = max(1, int(avg_latency_ms / target_latency_ms))
        elif avg_latency_ms < target_latency_ms * 0.3 and avg_requests_per_sec < 1:
            action = 'scale_in'
            reason = '延迟低且流量小，可以减少实例'
            recommended_instances = 1
        else:
            action = 'maintain'
            reason = '负载正常，保持当前配置'
            recommended_instances = None

        return {
            'action': action,
            'reason': reason,
            'avg_requests_per_sec': avg_requests_per_sec,
            'avg_latency_ms': avg_latency_ms,
            'target_latency_ms': target_latency_ms,
            'recommended_instances': recommended_instances
        }

    # ========== 综合统计 ==========

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM cost_records')
                total_records = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(amount) FROM cost_records')
                total_cost = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM cost_budgets')
                budget_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM optimization_suggestions WHERE status = 'pending'")
                pending_suggestions = cursor.fetchone()[0]

            cache = self.cache_stats()
            summary_30d = self.get_cost_summary(days=30)
            forecast = self.forecast_cost()

            return {
                'total_records': total_records,
                'total_cost': round(total_cost, 6),
                'budget_count': budget_count,
                'pending_suggestions': pending_suggestions,
                'cache_stats': cache,
                'cost_30d': summary_30d.get('total_amount', 0),
                'forecast_30d': forecast.get('total_forecast', 0)
            }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    co = AICostOptimizer()

    print("生成测试成本数据...")
    models = ['gpt35', 'gpt4', 'embedding']
    for i in range(50):
        model = random.choice(models)
        in_tokens = random.randint(100, 2000)
        out_tokens = random.randint(50, 1000)
        co.record_inference(model, in_tokens, out_tokens)

    print(f"30天成本汇总: {co.get_cost_summary(30)['total_amount']}")

    print("\n模型成本排行:")
    model_costs = co.get_model_costs(days=30)
    for m in model_costs['models'][:5]:
        print(f"  {m['model_id']}: ¥{m['total_cost']} ({m['call_count']}次调用)")

    print("\n设置预算:")
    result = co.set_budget('月度AI预算', 1000, category='total', alert_threshold=0.8)
    print(f"  预算ID: {result.get('budget_id')}")

    print(f"\n预算列表: {len(co.get_budgets())}")

    print("\n优化建议:")
    suggestions = co.generate_suggestions()
    print(f"  共 {suggestions['total_suggestions']} 条建议")
    print(f"  预计节省: ¥{suggestions['total_estimated_savings']}")
    for s in suggestions['suggestions']:
        print(f"    [{s['priority']}] {s['title']}: 预计节省 ¥{s['estimated_savings']}")

    print("\n成本预测:")
    forecast = co.forecast_cost(days=30, forecast_days=7)
    print(f"  趋势: {forecast['growth_trend']}")
    print(f"  未来7天预测总费用: ¥{forecast['total_forecast']}")

    print("\n缓存统计:")
    print(f"  {co.cache_stats()}")

    print(f"\n综合统计: {co.get_statistics()}")

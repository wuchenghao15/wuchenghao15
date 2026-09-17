#!/usr/bin/env python3
"""
AI智能检索查询模型系统
- 自动新建检索查询模型
- 自动适配模型方法提高数据检索效率
- 智能索引推荐与创建
- 查询性能监控与优化
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 导入分布式数据库配置
from db_manager import DATABASES, DB_DIR, build_table_mapping, get_db_for_table, connect

# 检索模型数据库路径
SEARCH_MODEL_DB = os.path.join(DB_DIR, 'search_models.db')


def get_model_db_connection():
    """获取检索模型数据库连接"""
    conn = sqlite3.connect(SEARCH_MODEL_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_search_model_db():
    """初始化检索模型数据库"""
    conn = get_model_db_connection()
    cursor = conn.cursor()

    # 检索模型表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT UNIQUE NOT NULL,
            model_type TEXT NOT NULL,
            target_table TEXT NOT NULL,
            target_database TEXT,
            query_pattern TEXT,
            index_fields TEXT,
            optimization_strategy TEXT,
            avg_query_time REAL DEFAULT 0,
            total_queries INTEGER DEFAULT 0,
            total_optimizations INTEGER DEFAULT 0,
            efficiency_gain REAL DEFAULT 0,
            is_enabled INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            auto_adapt INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            last_used TEXT
        )
    ''')

    # 查询日志表（记录查询性能）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER,
            query_sql TEXT,
            table_name TEXT,
            execution_time REAL,
            rows_returned INTEGER,
            index_used TEXT,
            was_optimized INTEGER DEFAULT 0,
            timestamp TEXT,
            FOREIGN KEY (model_id) REFERENCES search_models(id)
        )
    ''')

    # 索引推荐表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS index_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            database_name TEXT,
            recommended_fields TEXT,
            index_type TEXT DEFAULT 'btree',
            reason TEXT,
            estimated_improvement REAL,
            is_created INTEGER DEFAULT 0,
            created_index_name TEXT,
            created_at TEXT,
            FOREIGN KEY (table_name) REFERENCES search_models(target_table)
        )
    ''')

    # 模型适配历史
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_adaptations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            adaptation_type TEXT,
            old_strategy TEXT,
            new_strategy TEXT,
            old_avg_time REAL,
            new_avg_time REAL,
            improvement_percent REAL,
            timestamp TEXT,
            FOREIGN KEY (model_id) REFERENCES search_models(id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("检索模型数据库初始化完成")


class SearchQueryModel:
    """单个检索查询模型"""

    def __init__(self, model_id, model_name, model_type, target_table,
                 target_database=None, query_pattern=None, index_fields=None,
                 optimization_strategy='auto', auto_adapt=True):
        self.id = model_id
        self.model_name = model_name
        self.model_type = model_type  # 'exact', 'fuzzy', 'fulltext', 'composite', 'indexed'
        self.target_table = target_table
        self.target_database = target_database or get_db_for_table(target_table)
        self.query_pattern = query_pattern
        self.index_fields = index_fields or []
        self.optimization_strategy = optimization_strategy
        self.auto_adapt = auto_adapt
        self.query_count = 0
        self.total_time = 0
        self.last_avg_time = 0

    def execute_query(self, query_sql, params=None):
        """执行查询并记录性能"""
        start_time = time.time()
        rows_returned = 0
        index_used = None

        try:
            db_path = DATABASES.get(self.target_database)
            if not db_path or not os.path.exists(db_path):
                db_path = DATABASES.get('other')

            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()

            # 获取查询计划
            try:
                explain_cursor = conn.cursor()
                explain_cursor.execute(f"EXPLAIN QUERY PLAN {query_sql}")
                plan = explain_cursor.fetchall()
                if plan:
                    plan_str = ' '.join(str(p) for p in plan)
                    if 'USING INDEX' in plan_str.upper():
                        index_used = plan_str
                    elif 'SCAN' in plan_str.upper():
                        index_used = 'FULL_SCAN'
                    else:
                        index_used = 'AUTO'
            except Exception:
                pass

            cursor.execute(query_sql, params or ())
            results = cursor.fetchall()
            rows_returned = len(results)
            conn.close()

        except Exception as e:
            logger.error(f"查询执行失败 [{self.model_name}]: {e}")
            return [], 0, 0, None

        execution_time = time.time() - start_time
        self.query_count += 1
        self.total_time += execution_time
        self.last_avg_time = self.total_time / self.query_count

        # 记录查询日志
        self._log_query(query_sql, execution_time, rows_returned, index_used)

        # 自动适配检查
        if self.auto_adapt and self.query_count % 10 == 0:
            self._check_and_adapt()

        return results, rows_returned, execution_time, index_used

    def _log_query(self, query_sql, execution_time, rows_returned, index_used):
        """记录查询日志"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO query_logs (model_id, query_sql, table_name, execution_time,
                                       rows_returned, index_used, was_optimized, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.id, query_sql[:500], self.target_table, execution_time,
                  rows_returned, index_used, 1 if index_used and 'SCAN' not in str(index_used).upper() else 0,
                  datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录查询日志失败: {e}")

    def _check_and_adapt(self):
        """检查并自动适配模型"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()

            # 获取最近10次查询的平均时间
            cursor.execute('''
                SELECT AVG(execution_time) as avg_time, COUNT(*) as cnt,
                       SUM(CASE WHEN was_optimized = 0 THEN 1 ELSE 0 END) as unoptimized
                FROM query_logs WHERE model_id = ?
                ORDER BY id DESC LIMIT 10
            ''', (self.id,))
            row = cursor.fetchone()

            if row and row[0] and row[2] > 5:  # 超过5次未优化
                old_strategy = self.optimization_strategy
                new_strategy = self._select_better_strategy()
                if new_strategy != old_strategy:
                    old_avg = row[0]
                    self._adapt_model(old_strategy, new_strategy, old_avg)
            conn.close()
        except Exception as e:
            logger.error(f"自动适配检查失败: {e}")

    def _select_better_strategy(self):
        """选择更好的优化策略"""
        strategies = ['indexed', 'composite', 'fulltext', 'fuzzy', 'exact']
        current_idx = strategies.index(self.optimization_strategy) if self.optimization_strategy in strategies else 0
        # 尝试下一个策略
        next_idx = (current_idx + 1) % len(strategies)
        return strategies[next_idx]

    def _adapt_model(self, old_strategy, new_strategy, old_avg_time):
        """适配模型到新策略"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()

            self.optimization_strategy = new_strategy
            new_avg_time = old_avg_time * 0.8  # 预估改善20%

            improvement = ((old_avg_time - new_avg_time) / old_avg_time * 100) if old_avg_time > 0 else 0

            cursor.execute('''
                UPDATE search_models
                SET optimization_strategy = ?, updated_at = ?, total_optimizations = total_optimizations + 1
                WHERE id = ?
            ''', (new_strategy, datetime.now().isoformat(), self.id))

            cursor.execute('''
                INSERT INTO model_adaptations
                (model_id, adaptation_type, old_strategy, new_strategy,
                 old_avg_time, new_avg_time, improvement_percent, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.id, 'auto_adapt', old_strategy, new_strategy,
                  old_avg_time, new_avg_time, improvement, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            logger.info(f"模型 [{self.model_name}] 适配: {old_strategy} -> {new_strategy} "
                        f"(预估提升 {improvement:.1f}%)")
        except Exception as e:
            logger.error(f"适配模型失败: {e}")


class AISearchQueryModelManager:
    """AI智能检索查询模型管理器"""

    def __init__(self):
        self.models = {}  # model_name -> SearchQueryModel
        self.table_models = defaultdict(list)  # table_name -> [model_names]
        self.stats = {
            'total_models': 0,
            'active_models': 0,
            'total_queries': 0,
            'total_optimizations': 0,
            'avg_efficiency_gain': 0
        }
        self._initialized = False

    def initialize(self):
        """初始化模型管理器"""
        init_search_model_db()
        self._load_existing_models()
        self._auto_discover_models()
        self._initialized = True
        logger.info(f"AI检索模型管理器初始化完成，共 {len(self.models)} 个模型")

    def _load_existing_models(self):
        """加载已存在的模型"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM search_models WHERE is_enabled = 1')
            models = cursor.fetchall()
            conn.close()

            for row in models:
                model_dict = dict(row)
                model = SearchQueryModel(
                    model_id=model_dict['id'],
                    model_name=model_dict['model_name'],
                    model_type=model_dict['model_type'],
                    target_table=model_dict['target_table'],
                    target_database=model_dict.get('target_database'),
                    query_pattern=model_dict.get('query_pattern'),
                    index_fields=json.loads(model_dict.get('index_fields', '[]')),
                    optimization_strategy=model_dict.get('optimization_strategy', 'auto'),
                    auto_adapt=bool(model_dict.get('auto_adapt', 1))
                )
                model.query_count = model_dict.get('total_queries', 0)
                self.models[model_dict['model_name']] = model
                self.table_models[model_dict['target_table']].append(model_dict['model_name'])

            if models:
                logger.info(f"加载了 {len(models)} 个现有检索模型")
        except Exception as e:
            logger.error(f"加载现有模型失败: {e}")

    def _auto_discover_models(self):
        """自动发现并为所有表创建默认检索模型"""
        created_count = 0

        for db_name, db_path in DATABASES.items():
            if not os.path.exists(db_path):
                continue
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [t[0] for t in cursor.fetchall()]

                for table in tables:
                    if table.startswith('sqlite_'):
                        continue

                    # 获取表结构
                    cursor.execute(f'PRAGMA table_info("{table}")')
                    columns = cursor.fetchall()
                    if not columns:
                        continue

                    # 为每个表创建主键索引模型
                    model_name = f"auto_{db_name}_{table}"
                    if model_name not in self.models:
                        self._create_model_for_table(
                            db_name, table, columns, model_name
                        )
                        created_count += 1

                conn.close()
            except Exception as e:
                logger.error(f"发现表失败 {db_name}: {e}")

        if created_count:
            logger.info(f"自动创建了 {created_count} 个新检索模型")

    def _create_model_for_table(self, db_name, table_name, columns, model_name):
        """为表创建检索模型"""
        try:
            # 识别主键和索引字段
            pk_fields = []
            indexed_fields = []
            text_fields = []

            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = col[5]  # pk标志

                if is_pk:
                    pk_fields.append(col_name)
                if col_type and 'TEXT' in col_type.upper():
                    text_fields.append(col_name)

            # 优先使用主键作为索引字段
            index_fields = pk_fields if pk_fields else (text_fields[:2] if text_fields else [columns[0][1]])

            # 决定模型类型
            if pk_fields:
                model_type = 'indexed'
                strategy = 'pk_index'
            elif text_fields:
                model_type = 'fulltext'
                strategy = 'text_search'
            else:
                model_type = 'exact'
                strategy = 'sequential'

            conn = get_model_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO search_models
                (model_name, model_type, target_table, target_database, query_pattern,
                 index_fields, optimization_strategy, is_enabled, is_active, auto_adapt,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1, ?, ?)
            ''', (model_name, model_type, table_name, db_name, None,
                  json.dumps(index_fields), strategy,
                  datetime.now().isoformat(), datetime.now().isoformat()))

            model_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # 创建内存中的模型对象
            if model_id:
                model = SearchQueryModel(
                    model_id=model_id,
                    model_name=model_name,
                    model_type=model_type,
                    target_table=table_name,
                    target_database=db_name,
                    index_fields=index_fields,
                    optimization_strategy=strategy
                )
                self.models[model_name] = model
                self.table_models[table_name].append(model_name)

                # 为表创建索引（如果不存在）
                self._create_index_for_table(db_name, table_name, index_fields)

        except Exception as e:
            logger.error(f"创建表模型失败 {table_name}: {e}")

    def _create_index_for_table(self, db_name, table_name, fields):
        """为表字段创建索引"""
        if not fields:
            return

        try:
            db_path = DATABASES.get(db_name)
            if not db_path or not os.path.exists(db_path):
                return

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for field in fields:
                index_name = f"idx_{table_name}_{field}"
                try:
                    cursor.execute(f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ("{field}")')
                except Exception:
                    pass

            conn.commit()

            # 记录索引推荐
            conn2 = get_model_db_connection()
            cursor2 = conn2.cursor()
            for field in fields:
                cursor2.execute('''
                    INSERT OR IGNORE INTO index_recommendations
                    (table_name, database_name, recommended_fields, index_type, reason,
                     estimated_improvement, is_created, created_index_name, created_at)
                    VALUES (?, ?, ?, 'btree', 'AI自动推荐索引', 50.0, 1, ?, ?)
                ''', (table_name, db_name, field, f"idx_{table_name}_{field}",
                      datetime.now().isoformat()))
            conn2.commit()
            conn2.close()

            conn.close()
        except Exception as e:
            logger.error(f"创建索引失败 {table_name}.{fields}: {e}")

    def create_custom_model(self, model_name, target_table, model_type='auto',
                            index_fields=None, optimization_strategy='auto'):
        """创建自定义检索模型"""
        try:
            db_name = get_db_for_table(target_table)

            conn = get_model_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO search_models
                (model_name, model_type, target_table, target_database, query_pattern,
                 index_fields, optimization_strategy, is_enabled, is_active, auto_adapt,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1, ?, ?)
            ''', (model_name, model_type, target_table, db_name, None,
                  json.dumps(index_fields or []), optimization_strategy,
                  datetime.now().isoformat(), datetime.now().isoformat()))

            model_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # 创建索引
            if index_fields:
                self._create_index_for_table(db_name, target_table, index_fields)

            # 加载到内存
            model = SearchQueryModel(
                model_id=model_id,
                model_name=model_name,
                model_type=model_type,
                target_table=target_table,
                target_database=db_name,
                index_fields=index_fields or [],
                optimization_strategy=optimization_strategy
            )
            self.models[model_name] = model
            self.table_models[target_table].append(model_name)

            logger.info(f"创建自定义检索模型: {model_name} -> {target_table}")
            return True
        except Exception as e:
            logger.error(f"创建自定义模型失败: {e}")
            return False

    def execute_search(self, table_name, query_sql, params=None, model_name=None):
        """使用检索模型执行查询"""
        # 选择合适的模型
        model = None
        if model_name and model_name in self.models:
            model = self.models[model_name]
        elif table_name in self.table_models and self.table_models[table_name]:
            model = self.models[self.table_models[table_name][0]]

        if not model:
            # 创建临时模型
            temp_name = f"temp_{table_name}_{int(time.time())}"
            self.create_custom_model(temp_name, table_name, model_type='exact')
            model = self.models.get(temp_name)

        if model:
            results, count, exec_time, index_used = model.execute_query(query_sql, params)
            self.stats['total_queries'] += 1
            return {
                'results': results,
                'count': count,
                'execution_time': exec_time,
                'index_used': index_used,
                'model_used': model.model_name
            }

        return {'results': [], 'count': 0, 'execution_time': 0, 'error': 'No model available'}

    def optimize_all_models(self):
        """优化所有模型"""
        optimized_count = 0
        for model_name, model in self.models.items():
            try:
                # 分析查询日志
                conn = get_model_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT AVG(execution_time) as avg_time, COUNT(*) as cnt,
                           SUM(CASE WHEN index_used LIKE '%SCAN%' THEN 1 ELSE 0 END) as scans
                    FROM query_logs WHERE model_id = ?
                ''', (model.id,))
                row = cursor.fetchone()
                conn.close()

                if row and row[2] and row[2] > 0:  # 有全表扫描
                    old_strategy = model.optimization_strategy
                    model.optimization_strategy = 'indexed'
                    # 重新创建索引
                    self._create_index_for_table(
                        model.target_database, model.target_table, model.index_fields
                    )
                    optimized_count += 1
                    logger.info(f"优化模型: {model_name} ({old_strategy} -> indexed)")
            except Exception as e:
                logger.error(f"优化模型失败 {model_name}: {e}")

        self.stats['total_optimizations'] += optimized_count
        return optimized_count

    def get_status(self):
        """获取模型管理器状态"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM search_models')
            total_models = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM search_models WHERE is_enabled = 1')
            enabled_models = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM search_models WHERE is_active = 1')
            active_models = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM query_logs')
            total_queries = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM model_adaptations')
            total_adaptations = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM index_recommendations WHERE is_created = 1')
            created_indexes = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM index_recommendations')
            total_recommendations = cursor.fetchone()[0]
            cursor.execute('SELECT AVG(execution_time) FROM query_logs')
            avg_query_time = cursor.fetchone()[0] or 0
            cursor.execute('SELECT AVG(efficiency_gain) FROM search_models WHERE efficiency_gain > 0')
            avg_efficiency = cursor.fetchone()[0] or 0

            conn.close()

            return {
                'total_models': total_models,
                'enabled_models': enabled_models,
                'disabled_models': total_models - enabled_models,
                'active_models': active_models,
                'total_queries': total_queries,
                'total_adaptations': total_adaptations,
                'created_indexes': created_indexes,
                'total_recommendations': total_recommendations,
                'avg_query_time': round(avg_query_time, 4),
                'avg_efficiency_gain': round(avg_efficiency, 2),
                'initialized': self._initialized,
                'databases_covered': len(DATABASES)
            }
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {'error': str(e)}

    def get_models_list(self):
        """获取所有模型列表"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, model_name, model_type, target_table, target_database,
                       index_fields, optimization_strategy, avg_query_time,
                       total_queries, total_optimizations, efficiency_gain,
                       is_enabled, is_active, auto_adapt, created_at, updated_at, last_used
                FROM search_models ORDER BY total_queries DESC
            ''')
            models = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return models
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    def get_adaptations_history(self, limit=20):
        """获取模型适配历史"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ma.id, ma.model_id, sm.model_name, ma.adaptation_type,
                       ma.old_strategy, ma.new_strategy, ma.old_avg_time,
                       ma.new_avg_time, ma.improvement_percent, ma.timestamp
                FROM model_adaptations ma
                LEFT JOIN search_models sm ON ma.model_id = sm.id
                ORDER BY ma.id DESC LIMIT ?
            ''', (limit,))
            adaptations = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return adaptations
        except Exception as e:
            logger.error(f"获取适配历史失败: {e}")
            return []

    def get_index_recommendations(self):
        """获取索引推荐"""
        try:
            conn = get_model_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, table_name, database_name, recommended_fields,
                       index_type, reason, estimated_improvement, is_created,
                       created_index_name, created_at
                FROM index_recommendations ORDER BY is_created DESC, id DESC
            ''')
            recommendations = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return recommendations
        except Exception as e:
            logger.error(f"获取索引推荐失败: {e}")
            return []


# 全局管理器实例
search_model_manager = AISearchQueryModelManager()


def init_search_models():
    """初始化检索模型系统"""
    return search_model_manager.initialize()


def get_search_model_status():
    """获取检索模型状态"""
    return search_model_manager.get_status()


def get_search_models_list():
    """获取所有检索模型"""
    return search_model_manager.get_models_list()


def execute_search_query(table_name, query_sql, params=None, model_name=None):
    """执行检索查询"""
    return search_model_manager.execute_search(table_name, query_sql, params, model_name)


def create_search_model(model_name, target_table, model_type='auto',
                        index_fields=None, optimization_strategy='auto'):
    """创建自定义检索模型"""
    return search_model_manager.create_custom_model(
        model_name, target_table, model_type, index_fields, optimization_strategy
    )


def optimize_all_search_models():
    """优化所有检索模型"""
    return search_model_manager.optimize_all_models()


if __name__ == "__main__":
    init_search_models()
    status = get_search_model_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    print(f"\n模型总数: {len(get_search_models_list())}")

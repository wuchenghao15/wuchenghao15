#!/usr/bin/env python3
"""
数据库配置加载器 - 分段从数据库调取系统配置参数
支持多阶段加载：基础配置 -> 安全配置 -> 功能配置 -> 高级配置
"""

import os
import sys
import json
import sqlite3
import logging
from typing import Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# 分布式数据库目录
SPLIT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')
SYSTEM_DB = os.path.join(SPLIT_DB_DIR, 'system.db')
AUTH_DB = os.path.join(SPLIT_DB_DIR, 'auth.db')
ADMIN_DB = os.path.join(SPLIT_DB_DIR, 'admin.db')


class DatabaseConfigLoader:
    """数据库配置加载器 - 分段加载配置"""

    def __init__(self):
        self.configs = {
            'base': {},        # 阶段1: 基础配置
            'security': {},    # 阶段2: 安全配置
            'feature': {},     # 阶段3: 功能配置
            'advanced': {},    # 阶段4: 高级配置
            'ai': {},          # 阶段5: AI引擎配置
            'database': {},    # 阶段6: 数据库配置
            'cache': {},       # 阶段7: 缓存配置
            'api': {},         # 阶段8: API配置
        }
        self.loaded_stages = []
        self._initialized = False

    def _get_db_connection(self, db_path: str) -> Optional[sqlite3.Connection]:
        """获取数据库连接"""
        if not os.path.exists(db_path):
            logger.warning(f"数据库不存在: {db_path}")
            return None
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败 {db_path}: {e}")
            return None

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """检查表是否存在"""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def _load_from_config_table(self, db_path: str, table_name: str,
                                stage: str, filters: dict = None) -> dict:
        """从配置表加载配置"""
        result = {}
        conn = self._get_db_connection(db_path)
        if not conn:
            return result

        try:
            if not self._table_exists(conn, table_name):
                logger.debug(f"表不存在: {table_name}")
                return result

            cursor = conn.cursor()
            query = f"SELECT * FROM {table_name}"
            params = []
            conditions = []

            if filters:
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                row_dict = dict(row)
                if 'config_key' in row_dict and 'config_value' in row_dict:
                    key = row_dict['config_key']
                    value = row_dict['config_value']
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
                elif 'key' in row_dict and 'value' in row_dict:
                    key = row_dict['key']
                    value = row_dict['value']
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value

            if result:
                self.configs[stage].update(result)
                logger.info(f"从 {db_path}/{table_name} 加载了 {len(result)} 项配置到 [{stage}] 阶段")

        except Exception as e:
            logger.error(f"从 {table_name} 加载配置失败: {e}")
        finally:
            conn.close()

        return result

    # ==================== 阶段1: 基础配置 ====================
    def load_base_config(self) -> Dict[str, Any]:
        """阶段1: 加载基础配置"""
        logger.info("=" * 60)
        logger.info("[阶段 1/8] 加载基础配置...")
        logger.info("=" * 60)

        base_defaults = {
           'app_name': 'MTSCOS AI 智能考试系统',
           'app_version': '7.1.0',
           'app_code_name': 'Intelligent Modular Enhanced Edition',
            'debug': False,
            'timezone': 'Asia/Shanghai',
            'language': 'zh-CN',
            'max_content_length': 100 * 1024 * 1024,
        }

        self.configs['base'].update(base_defaults)

        # 尝试从system数据库加载
        self._load_from_config_table(SYSTEM_DB, 'system_config', 'base')
        self._load_from_config_table(SYSTEM_DB, 'configs', 'base')
        self._load_from_config_table(SYSTEM_DB, 'settings', 'base')
        self._load_from_config_table(ADMIN_DB, 'system_config', 'base')
        self._load_from_config_table(ADMIN_DB, 'settings', 'base')

        self.loaded_stages.append('base')
        logger.info(f"基础配置加载完成: {len(self.configs['base'])} 项")
        return self.configs['base']

    # ==================== 阶段2: 安全配置 ====================
    def load_security_config(self) -> Dict[str, Any]:
        """阶段2: 加载安全配置"""
        logger.info("=" * 60)
        logger.info("[阶段 2/8] 加载安全配置...")
        logger.info("=" * 60)

        security_defaults = {
            'secret_key': os.environ.get('SECRET_KEY', 'mtscos_ai_secret_key_2026'),
            'password_hash_rounds': 12,
            'session_lifetime': 86400,
            'max_login_attempts': 5,
            'lockout_duration': 300,
            'enable_captcha': True,
            'enable_2fa': False,
            'csrf_protection': True,
            'rate_limit_per_minute': 60,
            'ip_whitelist_enabled': False,
            'ip_whitelist': [],
        }

        self.configs['security'].update(security_defaults)

        # 从auth数据库加载
        self._load_from_config_table(AUTH_DB, 'security_config', 'security')
        self._load_from_config_table(AUTH_DB, 'settings', 'security')
        self._load_from_config_table(SYSTEM_DB, 'security_config', 'security')

        self.loaded_stages.append('security')
        logger.info(f"安全配置加载完成: {len(self.configs['security'])} 项")
        return self.configs['security']

    # ==================== 阶段3: 功能配置 ====================
    def load_feature_config(self) -> Dict[str, Any]:
        """阶段3: 加载功能配置"""
        logger.info("=" * 60)
        logger.info("[阶段 3/8] 加载功能配置...")
        logger.info("=" * 60)

        feature_defaults = {
            'enable_user_registration': True,
            'enable_exam_system': True,
            'enable_question_bank': True,
            'enable_ai_engine': True,
            'enable_learning_system': True,
            'enable_proctor_system': True,
            'enable_parent_monitor': True,
            'enable_hardware_admin': True,
            'enable_file_upload': True,
            'max_upload_size': 50 * 1024 * 1024,
        }

        self.configs['feature'].update(feature_defaults)

        # 从各功能数据库加载
        for db_name in ['exam', 'question', 'learning', 'proctor', 'user']:
            db_path = os.path.join(SPLIT_DB_DIR, f'{db_name}.db')
            if os.path.exists(db_path):
                self._load_from_config_table(db_path, 'feature_config', 'feature')
                self._load_from_config_table(db_path, 'settings', 'feature')

        self._load_from_config_table(SYSTEM_DB, 'feature_config', 'feature')
        self._load_from_config_table(ADMIN_DB, 'feature_config', 'feature')

        self.loaded_stages.append('feature')
        logger.info(f"功能配置加载完成: {len(self.configs['feature'])} 项")
        return self.configs['feature']

    # ==================== 阶段4: 高级配置 ====================
    def load_advanced_config(self) -> Dict[str, Any]:
        """阶段4: 加载高级配置"""
        logger.info("=" * 60)
        logger.info("[阶段 4/8] 加载高级配置...")
        logger.info("=" * 60)

        advanced_defaults = {
            'worker_processes': 1,
            'thread_pool_size': 20,
            'request_timeout': 30,
            'keepalive_timeout': 65,
            'gzip_enabled': True,
            'gzip_level': 6,
            'log_level': 'INFO',
            'log_file_enabled': True,
            'log_max_size': '50MB',
            'log_backup_count': 10,
            'performance_monitoring': True,
            'slow_query_threshold': 2.0,
        }

        self.configs['advanced'].update(advanced_defaults)

        self._load_from_config_table(SYSTEM_DB, 'advanced_config', 'advanced')
        self._load_from_config_table(ADMIN_DB, 'advanced_config', 'advanced')
        self._load_from_config_table(ADMIN_DB, 'system_settings', 'advanced')

        self.loaded_stages.append('advanced')
        logger.info(f"高级配置加载完成: {len(self.configs['advanced'])} 项")
        return self.configs['advanced']

    # ==================== 阶段5: AI引擎配置 ====================
    def load_ai_config(self) -> Dict[str, Any]:
        """阶段5: 加载AI引擎配置"""
        logger.info("=" * 60)
        logger.info("[阶段 5/8] 加载AI引擎配置...")
        logger.info("=" * 60)

        ai_db = os.path.join(SPLIT_DB_DIR, 'ai.db')

        ai_defaults = {
            'ai_enabled': True,
            'ai_engine_type': 'hybrid',
            'max_ai_workers': 5,
            'ai_auto_start': True,
            'ai_employees_enabled': True,
            'ai_agents_enabled': True,
            'ai_search_models_enabled': True,
            'ai_auto_adapt': True,
            'ai_auto_optimize': True,
            'ai_model_path': './models',
            'ai_temperature': 0.7,
            'ai_max_tokens': 2048,
        }

        self.configs['ai'].update(ai_defaults)

        self._load_from_config_table(ai_db, 'ai_config', 'ai')
        self._load_from_config_table(ai_db, 'ai_settings', 'ai')
        self._load_from_config_table(ai_db, 'engine_config', 'ai')
        self._load_from_config_table(SYSTEM_DB, 'ai_config', 'ai')

        self.loaded_stages.append('ai')
        logger.info(f"AI引擎配置加载完成: {len(self.configs['ai'])} 项")
        return self.configs['ai']

    # ==================== 阶段6: 数据库配置 ====================
    def load_database_config(self) -> Dict[str, Any]:
        """阶段6: 加载数据库配置"""
        logger.info("=" * 60)
        logger.info("[阶段 6/8] 加载数据库配置...")
        logger.info("=" * 60)

        database_defaults = {
            'db_type': 'sqlite',
            'db_pool_size': 10,
            'db_max_overflow': 20,
            'db_pool_timeout': 30,
            'db_pool_recycle': 3600,
            'db_echo': False,
            'enable_connection_pool': True,
            'enable_read_write_split': False,
            'enable_db_cache': True,
            'db_cache_ttl': 300,
            'distributed_mode': True,
            'db_count': 14,
        }

        self.configs['database'].update(database_defaults)

        self._load_from_config_table(SYSTEM_DB, 'database_config', 'database')
        self._load_from_config_table(ADMIN_DB, 'database_config', 'database')

        self.loaded_stages.append('database')
        logger.info(f"数据库配置加载完成: {len(self.configs['database'])} 项")
        return self.configs['database']

    # ==================== 阶段7: 缓存配置 ====================
    def load_cache_config(self) -> Dict[str, Any]:
        """阶段7: 加载缓存配置"""
        logger.info("=" * 60)
        logger.info("[阶段 7/8] 加载缓存配置...")
        logger.info("=" * 60)

        cache_defaults = {
            'cache_enabled': True,
            'cache_type': 'memory',
            'cache_default_ttl': 300,
            'cache_max_size': 1000,
            'redis_enabled': False,
            'redis_host': '127.0.0.1',
            'redis_port': 6379,
            'redis_db': 0,
            'redis_password': None,
            'local_cache_enabled': True,
            'session_cache_enabled': True,
        }

        self.configs['cache'].update(cache_defaults)

        self._load_from_config_table(SYSTEM_DB, 'cache_config', 'cache')
        self._load_from_config_table(ADMIN_DB, 'cache_config', 'cache')

        self.loaded_stages.append('cache')
        logger.info(f"缓存配置加载完成: {len(self.configs['cache'])} 项")
        return self.configs['cache']

    # ==================== 阶段8: API配置 ====================
    def load_api_config(self) -> Dict[str, Any]:
        """阶段8: 加载API配置"""
        logger.info("=" * 60)
        logger.info("[阶段 8/8] 加载API配置...")
        logger.info("=" * 60)

        api_defaults = {
            'api_enabled': True,
            'api_version': 'v1',
            'api_prefix': '/api',
            'api_rate_limit': 100,
            'api_rate_limit_window': 60,
            'api_enable_cors': True,
            'api_cors_origins': ['*'],
            'api_default_format': 'json',
            'api_pagination_default': 20,
            'api_pagination_max': 100,
            'api_doc_enabled': True,
        }

        self.configs['api'].update(api_defaults)

        api_management_db = os.path.join(SPLIT_DB_DIR, 'api_management.db')
        routes_db = os.path.join(SPLIT_DB_DIR, 'routes_management.db')

        self._load_from_config_table(api_management_db, 'api_config', 'api')
        self._load_from_config_table(routes_db, 'route_config', 'api')
        self._load_from_config_table(SYSTEM_DB, 'api_config', 'api')

        self.loaded_stages.append('api')
        logger.info(f"API配置加载完成: {len(self.configs['api'])} 项")
        return self.configs['api']

    # ==================== 完整加载流程 ====================
    def load_all_configs(self) -> Dict[str, Any]:
        """加载所有配置（8个阶段）"""
        logger.info("开始分段加载数据库配置...")
        logger.info(f"配置数据库: {SYSTEM_DB}")
        start_time = datetime.now()

        self.load_base_config()
        self.load_security_config()
        self.load_feature_config()
        self.load_advanced_config()
        self.load_ai_config()
        self.load_database_config()
        self.load_cache_config()
        self.load_api_config()

        elapsed = (datetime.now() - start_time).total_seconds()
        total_items = sum(len(cfg) for cfg in self.configs.values())

        logger.info("=" * 60)
        logger.info(f"所有配置加载完成！共 {len(self.loaded_stages)} 个阶段, {total_items} 项配置")
        logger.info(f"加载耗时: {elapsed:.2f}秒")
        logger.info("=" * 60)

        self._initialized = True
        return self.get_all_configs()

    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置（合并后）"""
        all_configs = {}
        for stage_configs in self.configs.values():
            all_configs.update(stage_configs)
        return all_configs

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取单个配置项"""
        all_configs = self.get_all_configs()
        return all_configs.get(key, default)

    def get_stage_config(self, stage: str) -> Dict[str, Any]:
        """获取指定阶段的配置"""
        return self.configs.get(stage, {})

    def reload_stage(self, stage: str) -> Dict[str, Any]:
        """重新加载指定阶段的配置"""
        load_method = getattr(self, f'load_{stage}_config', None)
        if load_method and stage in self.loaded_stages:
            self.loaded_stages.remove(stage)
            return load_method()
        return {}


# 全局配置加载器实例
config_loader = DatabaseConfigLoader()


def load_db_configs(stages=None):
    """加载数据库配置（分段）"""
    if stages is None:
        return config_loader.load_all_configs()

    for stage in stages:
        load_method = getattr(config_loader, f'load_{stage}_config', None)
        if load_method:
            load_method()

    return config_loader.get_all_configs()


def get_db_config(key, default=None):
    """从数据库配置中获取值"""
    return config_loader.get_config(key, default)


def get_all_db_configs():
    """获取所有数据库配置"""
    return config_loader.get_all_configs()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    configs = load_db_configs()
    print(f"\n总配置项数: {len(configs)}")
    print(f"加载阶段: {config_loader.loaded_stages}")

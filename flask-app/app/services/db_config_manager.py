# -*- coding: utf-8 -*-
"""
数据库配置管理器
实现系统参数统一从数据库读取和写入
"""

import os
import json
import sqlite3
import logging
import threading
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


class DatabaseConfigManager:
    """数据库配置管理器"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        
        self.db_path = db_path or DATABASE_PATH
        self._cache = {}
        self._cache_updated = datetime.now()
        self._cache_ttl = 300
        self._lock = threading.RLock()
        self._initialized = True
        
        self._init_table()
        self._load_cache()
    
    def _init_table(self):
        """初始化配置表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    value TEXT,
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_settings_key ON system_settings(setting_key)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_settings_category ON system_settings(category)
            ''')
            
            cursor.execute("PRAGMA table_info(system_settings)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'category' not in columns:
                cursor.execute('ALTER TABLE system_settings ADD COLUMN category TEXT DEFAULT "general"')
                logger.info("[数据库配置] 添加缺失列: category")
            
            if 'description' not in columns:
                cursor.execute('ALTER TABLE system_settings ADD COLUMN description TEXT')
                logger.info("[数据库配置] 添加缺失列: description")
            
            if 'updated_at' not in columns:
                cursor.execute('ALTER TABLE system_settings ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                logger.info("[数据库配置] 添加缺失列: updated_at")
            
            conn.commit()
            conn.close()
            logger.info("[数据库配置] 配置表初始化完成")
        except Exception as e:
            logger.error(f"[数据库配置] 初始化配置表失败: {str(e)}")
    
    def _load_cache(self):
        """加载配置到缓存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, value, category FROM system_settings')
            rows = cursor.fetchall()
            conn.close()
            
            with self._lock:
                for key, value, category in rows:
                    try:
                        self._cache[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        self._cache[key] = value
            
            self._cache_updated = datetime.now()
            logger.info(f"[数据库配置] 缓存加载完成，共 {len(self._cache)} 个配置项")
        except Exception as e:
            logger.error(f"[数据库配置] 加载缓存失败: {str(e)}")
    
    def _is_cache_expired(self) -> bool:
        """检查缓存是否过期"""
        return (datetime.now() - self._cache_updated).seconds > self._cache_ttl
    
    def _get_value(self, key: str) -> Any:
        """从数据库获取配置值"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM system_settings WHERE setting_key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return row[0]
            return None
        except Exception as e:
            logger.error(f"[数据库配置] 获取配置 {key} 失败: {str(e)}")
            return None
    
    def _set_value(self, key: str, value: Any, category: str = 'general', description: str = '') -> bool:
        """设置配置值到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            serialized_value = json.dumps(value, ensure_ascii=False)
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_settings 
                (setting_key, value, category, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, serialized_value, category, description, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            with self._lock:
                self._cache[key] = value
            
            logger.info(f"[数据库配置] 配置 {key} 更新成功")
            return True
        except Exception as e:
            logger.error(f"[数据库配置] 设置配置 {key} 失败: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        with self._lock:
            if key in self._cache and not self._is_cache_expired():
                return self._cache.get(key, default)
        
        value = self._get_value(key)
        if value is not None:
            with self._lock:
                self._cache[key] = value
            return value
        
        return default
    
    def set(self, key: str, value: Any, category: str = 'general', description: str = '') -> bool:
        """设置配置值"""
        return self._set_value(key, value, category, description)
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """获取指定分类的所有配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, value FROM system_settings WHERE category = ?', (category,))
            rows = cursor.fetchall()
            conn.close()
            
            result = {}
            for key, value in rows:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            
            return result
        except Exception as e:
            logger.error(f"[数据库配置] 获取分类 {category} 配置失败: {str(e)}")
            return {}
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        self._load_cache()
        return self._cache.copy()
    
    def get_all_with_category(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置，按分类分组"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, value, category FROM system_settings')
            rows = cursor.fetchall()
            conn.close()
            
            result = {}
            for key, value, category in rows:
                if category not in result:
                    result[category] = {}
                try:
                    result[category][key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[category][key] = value
            
            return result
        except Exception as e:
            logger.error(f"[数据库配置] 获取所有配置失败: {str(e)}")
            return {}
    
    def delete(self, key: str) -> bool:
        """删除配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM system_settings WHERE setting_key = ?', (key,))
            conn.commit()
            conn.close()
            
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
            
            logger.info(f"[数据库配置] 配置 {key} 删除成功")
            return True
        except Exception as e:
            logger.error(f"[数据库配置] 删除配置 {key} 失败: {str(e)}")
            return False
    
    def batch_set(self, settings: Dict[str, Any], category: str = 'general') -> bool:
        """批量设置配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for key, value in settings.items():
                serialized_value = json.dumps(value, ensure_ascii=False)
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings 
                    (setting_key, value, category, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (key, serialized_value, category, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            with self._lock:
                self._cache.update(settings)
            
            logger.info(f"[数据库配置] 批量更新 {len(settings)} 个配置项")
            return True
        except Exception as e:
            logger.error(f"[数据库配置] 批量设置配置失败: {str(e)}")
            return False
    
    def init_defaults(self, defaults: Dict[str, Any], category: str = 'general') -> None:
        """初始化默认配置（仅在配置项不存在时设置）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for key, value in defaults.items():
                cursor.execute('SELECT COUNT(*) FROM system_settings WHERE setting_key = ?', (key,))
                if cursor.fetchone()[0] == 0:
                    serialized_value = json.dumps(value, ensure_ascii=False)
                    cursor.execute('''
                        INSERT INTO system_settings 
                        (setting_key, value, category, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (key, serialized_value, category, datetime.now().isoformat(), datetime.now().isoformat()))
                    logger.debug(f"[数据库配置] 初始化默认配置: {key}")
            
            conn.commit()
            conn.close()
            self._load_cache()
            logger.info(f"[数据库配置] 默认配置初始化完成")
        except Exception as e:
            logger.error(f"[数据库配置] 初始化默认配置失败: {str(e)}")
    
    def clear_cache(self):
        """清除缓存"""
        with self._lock:
            self._cache.clear()
            self._cache_updated = datetime.now()
        logger.info("[数据库配置] 缓存已清除")
    
    def refresh_cache(self):
        """刷新缓存"""
        self._load_cache()
    
    def get_keys_by_category(self, category: str) -> List[str]:
        """获取指定分类的所有配置键"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key FROM system_settings WHERE category = ?', (category,))
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"[数据库配置] 获取分类 {category} 的键失败: {str(e)}")
            return []
    
    def get_categories(self) -> List[str]:
        """获取所有配置分类"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM system_settings')
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"[数据库配置] 获取分类列表失败: {str(e)}")
            return []


db_config_manager = DatabaseConfigManager()

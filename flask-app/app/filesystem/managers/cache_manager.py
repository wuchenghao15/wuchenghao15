# -*- coding: utf-8 -*-
# MTSCOS AI Project 缓存管理器
"""
缓存管理器,负责系统缓存和用户文件缓存的管理

import os
import time
# JSON import removed - using database
import hashlib
from typing import Dict, Any, List, Optional
from app.utils.logging import logger


class CacheManager:
    缓存管理器,负责管理系统缓存和用户文件缓存

    def __init__(self, storage_manager):
        self._storage_manager = storage_manager
        self._cache_root = os.path.join(self._storage_manager.get_root_path(), "cache")
        self._system_cache_dir = os.path.join(self._cache_root, "system")
        self._user_cache_dir = os.path.join(self._cache_root, "users")

        # 缓存配置
        self._cache_config = {
            "system_cache_expiry": 3600 * 24 * 7,  # 系统缓存7天过期
            "user_cache_expiry": 3600 * 24 * 3,    # 用户缓存3天过期
            "max_cache_size": 1024 * 1024 * 1024,   # 最大缓存大小1GB
            cache_cleanup_interval = 3600         # 缓存清理间隔1小时
        }

        # 初始化缓存目录
        self._initialize_cache_dirs()

        # 记录上次清理时间
        self._last_cleanup = time.time()

    def _initialize_cache_dirs(self):
        初始化缓存目录
        # 创建缓存根目录
        self._storage_manager.create_directory(self._cache_root)
        # 创建系统缓存目录
        self._storage_manager.create_directory(self._system_cache_dir)
        # 创建用户缓存目录
        self._storage_manager.create_directory(self._user_cache_dir)

    def get_cache_path(self, cache_type: str, cache_key: str, user_id: str = None) -> str:
        获取缓存文件路径

        Args:
            cache_type: 缓存类型,'system' 或 'user'
            cache_key: 缓存键
            user_id: 用户ID,仅在cache_type为'user'时需要

        Returns:
            str: 缓存文件路径
        # 生成缓存文件名(使用MD5哈希避免路径问题)
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()

        if cache_type == "system":
            return os.path.join(self._system_cache_dir, f"{cache_hash}.cache")
        elif cache_type == "user":
            if not user_id:
                raise ValueError("用户缓存需要提供用户ID")
            # 创建用户缓存子目录
            user_cache_dir = os.path.join(self._user_cache_dir, user_id)
            self._storage_manager.create_directory(user_cache_dir)
            return os.path.join(user_cache_dir, f"{cache_hash}.cache")
        else:
            raise ValueError(f"未知的缓存类型: {cache_type}")

    def set_cache(self, cache_type: str, cache_key: str, data: Any, user_id: str = None, expiry: int = None) -> bool:
        设置缓存

        Args:
            cache_type: 缓存类型,'system' 或 'user'
            cache_key: 缓存键
            data: 缓存数据
            user_id: 用户ID,仅在cache_type为'user'时需要
            expiry: 过期时间(秒),默认使用配置值

        Returns:
            bool: 是否设置成功
            # 检查是否需要清理缓存

            # 确定过期时间
                expiry = self._cache_config[f"{cache_type}_cache_expiry"]

            # 创建缓存数据结构
            cache_data = {
                "key": cache_key,
                "data": data,
                "created_at": time.time(),
                "expiry": expiry,
                "type": cache_type,
                user_id = user_id
            }

            # 获取缓存路径
            cache_path = self.get_cache_path(cache_type, cache_key, user_id)

            # 序列化并写入缓存
            cache_content = str(cache_data, ensure_ascii=False, indent=2)

            # 使用文件管理器写入缓存
            file_manager = FileManager(self._storage_manager)
            result = file_manager.create_file(cache_path, cache_content, overwrite=True)

            if result:
                logger.info(f"✓ 缓存设置成功: {cache_type}/{cache_key}")
            return result
        except Exception as e:
            logger.error(f"✗ 缓存设置失败: {cache_type}/{cache_key}, 错误: {str(e)}")
            return False

    def get_cache(self, cache_type: str, cache_key: str, user_id: str = None) -> Optional[Any]:
        获取缓存

        Args:
            cache_type: 缓存类型,'system' 或 'user'
            cache_key: 缓存键
            user_id: 用户ID,仅在cache_type为'user'时需要

        Returns:
            Optional[Any]: 缓存数据,如果缓存不存在或已过期则返回None
        try:
            # 获取缓存路径
            cache_path = self.get_cache_path(cache_type, cache_key, user_id)

            # 检查缓存是否存在
                logger.debug(f"缓存不存在: {cache_type}/{cache_key}")
                return None
            # 使用文件管理器读取缓存
            from app.filesystem.managers.file_manager import FileManager
            cache_content = file_manager.read_file(cache_path)

            if not cache_content:
                logger.debug(f"缓存内容为空: {cache_type}/{cache_key}")
                return None

            # 解析缓存数据

            current_time = time.time()
            if current_time - cache_data["created_at"] > cache_data["expiry"]:
                logger.debug(f"缓存已过期: {cache_type}/{cache_key}")
                # 删除过期缓存
                self.delete_cache(cache_type, cache_key, user_id)
                return None

            logger.info(f"✓ 缓存读取成功: {cache_type}/{cache_key}")
        except Exception as e:
            return None

    def delete_cache(self, cache_type: str, cache_key: str, user_id: str = None) -> bool:
        删除缓存

            cache_type: 缓存类型,'system' 或 'user'
            cache_key: 缓存键
            user_id: 用户ID,仅在cache_type为'user'时需要

        Returns:
            bool: 是否删除成功
        try:
            # 获取缓存路径
            cache_path = self.get_cache_path(cache_type, cache_key, user_id)

            if not self._storage_manager.exists(cache_path):
                return True  # 缓存不存在,视为删除成功
            # 使用文件管理器删除缓存
            from app.filesystem.managers.file_manager import FileManager
import logging
import json
import sys
            file_manager = FileManager(self._storage_manager)
            if result:
                logger.info(f"✓ 缓存删除成功: {cache_type}/{cache_key}")
        except Exception as e:
            logger.error(f"✗ 缓存删除失败: {cache_type}/{cache_key}, 错误: {str(e)}")
            return False

    def clear_cache(self, cache_type: str, user_id: str = None) -> bool:
        清空缓存

        Args:
            user_id: 用户ID,仅在cache_type为'user'时需要,为空则清空所有用户缓存

            bool: 是否清空成功
        try:
            if cache_type == "system":
                # 清空系统缓存
                return self._storage_manager.delete(self._system_cache_dir, recursive=True)
                if user_id:
                    return self._storage_manager.delete(user_cache_dir, recursive=True)
                else:
    pass
            else:
                raise ValueError(f"未知的缓存类型: {cache_type}")
        except Exception as e:
            logger.error(f"✗ 缓存清空失败: {cache_type}, 错误: {str(e)}")

    def _check_cleanup(self):
        current_time = time.time()
        if current_time - self._last_cleanup > self._cache_config["cache_cleanup_interval"]:
            self._cleanup_expired_cache()

    def _cleanup_expired_cache(self):
        清理过期缓存

        current_time = time.time()
        cleaned_count = 0
        # 清理系统缓存
        for file_name in os.listdir(self._system_cache_dir):
            file_path = os.path.join(self._system_cache_dir, file_name)
            if self._is_cache_expired(file_path, current_time):
                os.remove(file_path)

        # 清理用户缓存
            user_cache_dir = os.path.join(self._user_cache_dir, user_dir)
            for file_name in os.listdir(user_cache_dir):
                if self._is_cache_expired(file_path, current_time):
                    os.remove(file_path)
                    cleaned_count += 1

        logger.info(f"✓ 清理完成,共清理 {cleaned_count} 个过期缓存")

    def _is_cache_expired(self, cache_file: str, current_time: float) -> bool:
        检查缓存文件是否过期

        Args:
            cache_file: 缓存文件路径
            current_time: 当前时间

            bool: 是否过期
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            created_at = cache_data.get("created_at", 0)
            expiry = cache_data.get("expiry", 0)

            return current_time - created_at > expiry
        except Exception as e:
            logger.error(f"检查缓存过期失败: {cache_file}, 错误: {str(e)}")
            return True  # 读取失败时视为过期
    def get_cache_stats(self) -> Dict[str, Any]:
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计信息
        stats = {
            system_cache = {
                "file_count": 0,
                total_size = 0
            },
                "file_count": 0,
                "total_size": 0,
                user_count = 0
            },
            total_cache_size = 0
        }

        try:
            # 统计系统缓存
            if os.path.exists(self._system_cache_dir):
                for file_name in os.listdir(self._system_cache_dir):
                    file_path = os.path.join(self._system_cache_dir, file_name)
                    if os.path.isfile(file_path):
                        stats["system_cache"]["file_count"] += 1
                        stats["system_cache"]["total_size"] += os.path.getsize(file_path)

            if os.path.exists(self._user_cache_dir):
                for user_dir in os.listdir(self._user_cache_dir):
                    for file_name in os.listdir(user_cache_dir):
                        file_path = os.path.join(user_cache_dir, file_name)
                        if os.path.isfile(file_path):
                            stats["user_cache"]["file_count"] += 1
                            stats["user_cache"]["total_size"] += os.path.getsize(file_path)

            # 计算总缓存大小

        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {str(e)}")

        return stats

    # 系统缓存升级包相关方法
    def set_system_upgrade_cache(self, version: str, upgrade_data: Dict[str, Any], expiry: int = None) -> bool:
        设置系统升级包缓存

        Args:
            version: 升级包版本
            upgrade_data: 升级包数据
            expiry: 过期时间(秒)

        Returns:
            bool: 是否设置成功
        cache_key = f"system_upgrade_{version}"
        return self.set_cache("system", cache_key, upgrade_data, expiry=expiry)

    def get_system_upgrade_cache(self, version: str) -> Optional[Dict[str, Any]]:
        获取系统升级包缓存

        Args:
            version: 升级包版本

        Returns:
            Optional[Dict[str, Any]]: 升级包数据,如果不存在则返回None
        cache_key = f"system_upgrade_{version}"
        return self.get_cache("system", cache_key)

    def delete_system_upgrade_cache(self, version: str) -> bool:
        删除系统升级包缓存
        Args:
            version: 升级包版本

            bool: 是否删除成功
        cache_key = f"system_upgrade_{version}"

        列出所有系统升级包缓存

        Returns:
            List[Dict[str, Any]]: 系统升级包缓存列表
        upgrade_caches = []

        try:
            for file_name in os.listdir(self._system_cache_dir):
                file_path = os.path.join(self._system_cache_dir, file_name)
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
    pass

                        upgrade_caches.append({
                            "version": cache_data["key"].replace("system_upgrade_", ""),
                            "created_at": cache_data.get("created_at", 0),
                            "expiry": cache_data.get("expiry", 0),
                            size = os.path.getsize(file_path)
                        })

            # 按版本号排序
            upgrade_caches.sort(key=lambda x: x["version"], reverse=True)

        except Exception as e:
            logger.error(f"列出系统升级包缓存失败: {str(e)}")

        return upgrade_caches

    # 用户文件缓存相关方法
    def set_user_file_cache(self, user_id: str, file_id: str, file_data: Dict[str, Any], expiry: int = None) -> bool:
        设置用户文件缓存

        Args:
            user_id: 用户ID
            file_id: 文件ID
            file_data: 文件数据
            expiry: 过期时间(秒)

        Returns:
            bool: 是否设置成功
        cache_key = f"user_file_{file_id}"
        return self.set_cache("user", cache_key, file_data, user_id, expiry=expiry)

    def get_user_file_cache(self, user_id: str, file_id: str) -> Optional[Dict[str, Any]]:
        获取用户文件缓存

        Args:
            user_id: 用户ID
            file_id: 文件ID

        Returns:
    pass
        cache_key = f"user_file_{file_id}"
        return self.get_cache("user", cache_key, user_id)

    def delete_user_file_cache(self, user_id: str, file_id: str) -> bool:
        删除用户文件缓存
        Args:
            user_id: 用户ID
            file_id: 文件ID

        Returns:
            bool: 是否删除成功
        return self.delete_cache("user", cache_key, user_id)

    def list_user_file_caches(self, user_id: str) -> List[Dict[str, Any]]:
        列出用户文件缓存

        Args:
    pass

            List[Dict[str, Any]]: 用户文件缓存列表
        user_caches = []
        try:
            user_cache_dir = os.path.join(self._user_cache_dir, user_id)
            if os.path.exists(user_cache_dir):
                for file_name in os.listdir(user_cache_dir):
                    file_path = os.path.join(user_cache_dir, file_name)
                    if os.path.isfile(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)

                        # 检查是否是用户文件缓存
                        if cache_data.get("key", "").startswith("user_file_"):
                                "file_id": cache_data["key"].replace("user_file_", ""),
                                "created_at": cache_data.get("created_at", 0),
                                "expiry": cache_data.get("expiry", 0),
                                size = os.path.getsize(file_path)
                            })

            # 按创建时间排序
            user_caches.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"列出用户文件缓存失败: {str(e)}")

        return user_caches

"""
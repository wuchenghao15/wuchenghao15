# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统版本管理服务,用于管理系统版本、升级和兼容性检查
"""

import os
import json
import time
import re
import threading
from datetime import datetime
from app.utils.logging import logger
import logging
import sys


class SystemVersionService:
    """系统版本管理服务"""

    _instance = None
    _lock = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._lock = cls._lock or threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SystemVersionService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化系统版本管理服务"""
        if not self._initialized:
            self._initialized = True
            self._version_file = os.path.join(os.path.dirname(__file__), '..', '..', 'VERSION')
            self._config_file = os.path.join(os.path.dirname(__file__), '..', 'config.py')
            self._current_versions = {
                'system_version': '1.0.0',
                'internal_version': '1.0.0.0',
                'test_version': '1.0.0-beta',
                'api_version': '1.0'
            }
            self._version_history = []
            self._load_current_versions()
            logger.info("✅ 系统版本管理服务初始化完成")

    def _load_current_versions(self):
        """从版本文件或配置中加载当前版本信息"""
        if os.path.exists(self._version_file):
            try:
                with open(self._version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    self._current_versions.update(version_data)
                    logger.info(f"从VERSION文件加载版本信息: {self._current_versions}")
                    return
            except Exception as e:
                logger.error(f"从VERSION文件加载版本信息失败: {str(e)}")

        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    system_version_match = re.search(r'SYSTEM_VERSION\s*=\s*["\'](.*?)["\']', content)
                    if system_version_match:
                        self._current_versions['system_version'] = system_version_match.group(1)

                    internal_version_match = re.search(r'INTERNAL_VERSION\s*=\s*["\'](.*?)["\']', content)
                    if internal_version_match:
                        self._current_versions['internal_version'] = internal_version_match.group(1)

                    test_version_match = re.search(r'TEST_VERSION\s*=\s*["\'](.*?)["\']', content)
                    if test_version_match:
                        self._current_versions['test_version'] = test_version_match.group(1)

                    logger.info(f"从配置文件提取版本信息: {self._current_versions}")
                    return
            except Exception as e:
                logger.error(f"从配置文件提取版本信息失败: {str(e)}")

        logger.info(f"使用默认版本信息: {self._current_versions}")

    def _save_versions_to_file(self):
        """将版本信息保存到VERSION文件"""
        try:
            with open(self._version_file, 'w', encoding='utf-8') as f:
                json.dump(self._current_versions, f, indent=2, ensure_ascii=False)
            logger.info(f"版本信息已保存到文件: {self._version_file}")
        except Exception as e:
            logger.error(f"保存版本信息到文件失败: {str(e)}")

    def get_current_versions(self):
        """获取当前版本信息"""
        return self._current_versions.copy()

    def get_version_history(self, limit=20):
        """获取版本历史记录"""
        return self._version_history[-limit:]

    def update_version(self, version_type: str, new_version: str) -> dict:
        """更新指定类型的版本"""
        if version_type not in self._current_versions:
            return {'success': False, 'error': f'未知的版本类型: {version_type}'}

        old_version = self._current_versions[version_type]
        self._current_versions[version_type] = new_version

        self._version_history.append({
            'type': version_type,
            'old_version': old_version,
            'new_version': new_version,
            'timestamp': datetime.now().isoformat()
        })

        self._save_versions_to_file()

        return {
            'success': True,
            'type': version_type,
            'old_version': old_version,
            'new_version': new_version
        }

    def upgrade_system_version(self):
        """升级系统版本"""
        system_version = self._current_versions['system_version']
        parts = system_version.split('.')
        parts = list(map(int, parts))

        parts[-1] += 1
        new_system_version = '.'.join(map(str, parts))

        internal_version = self._current_versions['internal_version']
        internal_parts = internal_version.split('.')
        internal_parts = list(map(int, internal_parts))
        internal_parts[-1] += 1
        new_internal_version = '.'.join(map(str, internal_parts))

        results = []
        results.append(self.update_version('system_version', new_system_version))
        results.append(self.update_version('internal_version', new_internal_version))

        new_test_version = f"{new_system_version}-beta"
        results.append(self.update_version('test_version', new_test_version))

        all_success = all(result['success'] for result in results)

        if all_success:
            logger.info(f"🎉 系统版本升级成功! 新系统版本: {new_system_version}")
        else:
            logger.error("❌ 系统版本升级部分步骤失败")

        return {
            'success': all_success,
            'results': results,
            'new_system_version': new_system_version
        }

    def get_version_info(self):
        """获取完整的版本信息"""
        return {
            'versions': self.get_current_versions(),
            'history_count': len(self._version_history),
            'last_updated': self._version_history[-1] if self._version_history else None
        }

    def check_compatibility(self, required_version: str) -> dict:
        """检查版本兼容性"""
        current = self._current_versions['system_version']

        def parse_version(v):
            return list(map(int, v.split('.')))

        current_parts = parse_version(current)
        required_parts = parse_version(required_version)

        is_compatible = current_parts >= required_parts

        return {
            'is_compatible': is_compatible,
            'current_version': current,
            'required_version': required_version,
            'message': '版本兼容' if is_compatible else '版本不兼容,请升级系统'
        }


system_version_service = SystemVersionService()

#!/usr/bin/env python3
"""
系统版本管理服务，用于管理系统版本、升级和兼容性检查

import os
# JSON import removed - using database
import time
import re
import threading
from datetime import datetime
from app.utils.logging import logger

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
        return cls._instance

    def __init__(self):
        """初始化系统版本管理服务"""
        if not hasattr(self, '_initialized'):
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
        # 1. 尝试从VERSION文件读取
        if os.path.exists(self._version_file):
            try:
                with open(self._version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    self._current_versions.update(version_data)
                    logger.info(f"从VERSION文件加载版本信息: {self._current_versions}")
                    return
            except Exception as e:
                logger.error(f"从VERSION文件加载版本信息失败: {str(e)}")

        # 2. 尝试从配置文件中提取版本信息
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:

                    # 尝试匹配版本号模式
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
        # 3. 如果都失败，使用默认版本并创建VERSION文件
        logger.info(f"使用默认版本信息: {self._current_versions}")

    def _save_versions_to_file(self):
        """将版本信息保存到VERSION文件"""
        try:
            with open(self._version_file, 'w', encoding='utf-8') as f:
            logger.info(f"版本信息已保存到文件: {self._version_file}")
        except Exception as e:
            logger.error(f"保存版本信息到文件失败: {str(e)}")

    def get_current_versions(self):
        """获取当前版本信息"""

    def get_version_history(self, limit=20):
        """获取版本历史记录"""
        return {
            'history': self._version_history[-limit:],
            'total': len(self._version_history),
            'limit': limit
        }

        """更新指定类型的版本号"""
        if version_type not in self._current_versions:
            logger.error(f"无效的版本类型: {version_type}")
            return {
                'success': False,
                'message': f"无效的版本类型: {version_type}",
                'valid_types': list(self._current_versions.keys())
            }


        # 验证版本号格式
            return {
                'success': False,
                'message': f"无效的版本号格式: {new_version}"
            }

        self._current_versions[version_type] = new_version

        # 保存版本历史
        version_record = {
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'versions': self._current_versions.copy(),
                version_type: {
                    'old': old_version,
                    'new': new_version
                }
            },
        }
        self._version_history.append(version_record)
        # 限制历史记录长度
        if len(self._version_history) > 100:
            self._version_history = self._version_history[-100:]

        # 保存到文件
        self._save_versions_to_file()

        logger.info(f"版本更新成功: {version_type} 从 {old_version} 变为 {new_version}")
        return {
            'success': True,
            'message': f"版本更新成功: {version_type} 从 {old_version} 变为 {new_version}",
            'current_versions': self._current_versions,
            'version_record': version_record
        }

        """验证版本号格式"""
        version_pattern = r'^\d+(\.\d+)*(?:-(alpha|beta|rc)\d*)?$'

    def upgrade_system_version(self):
        """升级系统版本"""

        # 1. 升级系统版本号
        system_version = self._current_versions['system_version']
        parts = system_version.split('.')
        parts = list(map(int, parts))

        # 简单的版本升级逻辑：递增小版本号
        parts[-1] += 1
        new_system_version = '.'.join(map(str, parts))

        # 2. 升级内部版本号
        internal_version = self._current_versions['internal_version']
        internal_parts = internal_version.split('.')
        internal_parts = list(map(int, internal_parts))
        internal_parts[-1] += 1
        new_internal_version = '.'.join(map(str, internal_parts))

        # 3. 更新所有版本
        results = []
        results.append(self.update_version('system_version', new_system_version))
        results.append(self.update_version('internal_version', new_internal_version))

        # 4. 更新测试版本
        new_test_version = f"{new_system_version}-beta"
        results.append(self.update_version('test_version', new_test_version))

        # 5. 检查是否所有升级都成功
        all_success = all(result['success'] for result in results)

        if all_success:
            logger.info(f"🎉 系统版本升级成功！新系统版本: {new_system_version}")
        else:
            logger.error("❌ 系统版本升级部分步骤失败")

        return {
            'success': all_success,
            'results': results,
            'new_versions': self._current_versions
        }

        """检查当前版本与所需版本的兼容性"""
        current = self._current_versions['system_version']

        # 简单的兼容性检查：当前版本 >= 所需版本
        current_parts = list(map(int, re.sub(r'[^\d.]', '', current).split('.')))
        required_parts = list(map(int, re.sub(r'[^\d.]', '', required_version).split('.')))

        # 确保两个版本号的部分数量一致
        current_parts += [0] * (max_length - len(current_parts))
        required_parts += [0] * (max_length - len(required_parts))

        # 比较版本号
        for current_part, required_part in zip(current_parts, required_parts):
            if current_part > required_part:
                return True
            elif current_part < required_part:
                return False

        return True

    def get_version_info(self):
        """获取完整的版本信息"""
        return {
            'current_versions': self._current_versions,
            'last_checked': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version_file': self._version_file,
            'version_history_count': len(self._version_history)
        }

        """保存当前版本快照"""
        snapshot = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'versions': self._current_versions.copy(),
            'reason': reason
        }


        if len(self._version_history) > 100:
            self._version_history = self._version_history[-100:]

        logger.info(f"版本快照已保存: {reason}")


# 初始化系统版本管理服务
system_version_service = SystemVersionService()

# -*- coding: utf-8 -*-
import os
import time
# JSON import removed - using database
import re
from datetime import datetime
from app.utils.logging import logger

class VersionManagerAI:
    """版本管理AI，用于自动监控系统版本号、内部版本号和测试版本号"""

    def __init__(self):
        self.name = "版本管理AI"
        self.description = "负责自动监控系统版本号、内部版本号和测试版本号"
        self.version_history = []
        self.current_versions = {
            'system_version': '1.0.0',
            'internal_version': '1.0.0.0',
            'test_version': '1.0.0-beta'
        }
        self.version_file = os.path.join(os.path.dirname(__file__), '..', '..', 'VERSION')
        self.config_file = os.path.join(os.path.dirname(__file__), '..', 'config.py')

        # 初始化时读取当前版本信息
        self._load_current_versions()
        logger.info(f"版本管理AI初始化完成，当前版本: {self.current_versions}")

    def _load_current_versions(self):
        """从版本文件或配置中加载当前版本信息"""
        # 1. 尝试从VERSION文件读取
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    self.current_versions.update(version_data)
                    logger.info(f"从VERSION文件加载版本信息: {self.current_versions}")
                    return
            except Exception as e:
                logger.error(f"从VERSION文件加载版本信息失败: {str(e)}")

        # 2. 尝试从配置文件中提取版本信息
        if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # 尝试匹配版本号模式
                    system_version_match = re.search(r'SYSTEM_VERSION\s*=\s*["\'](.*?)["\']', content)
                    if system_version_match:
                        self.current_versions['system_version'] = system_version_match.group(1)

                    internal_version_match = re.search(r'INTERNAL_VERSION\s*=\s*["\'](.*?)["\']', content)
                    if internal_version_match:
                        self.current_versions['internal_version'] = internal_version_match.group(1)

                    test_version_match = re.search(r'TEST_VERSION\s*=\s*["\'](.*?)["\']', content)
                    if test_version_match:
                        self.current_versions['test_version'] = test_version_match.group(1)

                    logger.info(f"从配置文件提取版本信息: {self.current_versions}")
                    return
                logger.error(f"从配置文件提取版本信息失败: {str(e)}")
        # 3. 如果都失败，使用默认版本并创建VERSION文件
        self._save_versions_to_file()
        logger.info(f"使用默认版本信息: {self.current_versions}")

    def _save_versions_to_file(self):
        """将版本信息保存到VERSION文件"""
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_versions, f, ensure_ascii=False, indent=2)
            logger.info(f"版本信息已保存到文件: {self.version_file}")
        except Exception as e:
            logger.error(f"保存版本信息到文件失败: {str(e)}")

        """监控版本号变化"""
        logger.info("开始监控版本号")

        # 1. 检查当前版本是否有变化
        old_versions = self.current_versions.copy()

        # 2. 记录版本历史
        version_record = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'versions': self.current_versions.copy(),
            'changes': {}

        # 3. 检测版本变化
        for version_type, current_version in self.current_versions.items():
            old_version = old_versions.get(version_type)
            if current_version != old_version:
                version_record['changes'][version_type] = {
                    'old': old_version,
                    'new': current_version
                logger.info(f"版本变化: {version_type} 从 {old_version} 变为 {current_version}")

        # 4. 保存版本历史
        self.version_history.append(version_record)

        # 限制历史记录长度
        if len(self.version_history) > 100:
            self.version_history = self.version_history[-100:]

        # 5. 如果有变化，更新VERSION文件
        if version_record['changes']:
            self._save_versions_to_file()

        return version_record

    def get_version_info(self):
        """获取当前版本信息"""
        return {
            'current_versions': self.current_versions,

    def get_version_history(self, limit=20):
        """获取版本历史记录"""
        return {
            'history': self.version_history[-limit:],
            'total': len(self.version_history),
            'limit': limit

    def update_version(self, version_type, new_version):
        """更新指定类型的版本号"""
        if version_type in self.current_versions:
            old_version = self.current_versions[version_type]
            self.current_versions[version_type] = new_version
            self._save_versions_to_file()

            # 记录版本变化
            version_record = {
                'timestamp': time.time(),
                'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'versions': self.current_versions.copy(),
                'changes': {
                    version_type: {
                        'old': old_version,
            self.version_history.append(version_record)

            logger.info(f"手动更新版本: {version_type} 从 {old_version} 变为 {new_version}")
            return {
                'message': f"版本更新成功: {version_type} 从 {old_version} 变为 {new_version}",
        else:
            return {
                'message': f"无效的版本类型: {version_type}",
                'valid_types': list(self.current_versions.keys())

        """自动更新版本号（用于开发环境）"""
        # 仅在开发环境启用自动更新
        if os.environ.get('APP_ENV') == 'development':
            # 示例：内部版本号自动递增
            internal_version = self.current_versions['internal_version']
            parts[-1] += 1  # 递增最后一位
            new_internal_version = '.'.join(map(str, parts))

            return self.update_version('internal_version', new_internal_version)
        else:
            return {
                'success': False,
                'message': "自动版本更新仅在开发环境启用"

    def check_version_consistency(self):
        """检查版本号一致性"""
        logger.info("检查版本号一致性")

        # 验证版本号格式
        version_pattern = r'^\d+(\.\d+)*(-[a-zA-Z0-9]+)?$'
        issues = []

        for version_type, version in self.current_versions.items():
            if not re.match(version_pattern, version):
                issues.append({
                    'type': 'format_error',
                    'version_type': version_type,
                    'version': version,
                    'message': f"版本号格式无效: {version}"
                })

        # 检查版本号逻辑一致性（示例：系统版本号应为内部版本号的前缀）
        internal_parts = self.current_versions['internal_version'].split('.')

            for i, part in enumerate(system_parts):
                if part != internal_parts[i]:
                    issues.append({
                        'type': 'consistency_error',
                        'message': f"系统版本号 {self.current_versions['system_version']} 与内部版本号 {self.current_versions['internal_version']} 不一致"
                    })
                    break

        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'checked_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 初始化版本管理AI实例
version_manager_ai = VersionManagerAI()

#!/usr/bin/env python3
"""
版本管理服务
"""

import time
import json
import logging
import os
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger

class VersionManager:
    """版本管理器"""
    
    def __init__(self):
        """初始化版本管理器"""
        self.current_version = "1.0.0"
        self.version_history = []
        self.version_file = "version.json"
        self._create_version_table()
        self._load_version()
        logger.info(f"版本管理器初始化完成，当前版本: {self.current_version}")
    
    def _create_version_table(self):
        """创建版本历史表"""
        try:
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    description TEXT,
                    upgrade_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed'  -- pending, in_progress, completed, failed
                )
            ''')
            logger.info("版本历史表创建完成")
        except Exception as e:
            logger.error(f"创建版本历史表失败: {str(e)}")
    
    def _load_version(self):
        """加载当前版本"""
        # 从版本文件加载
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    self.current_version = version_data.get('version', '1.0.0')
                    self.version_history = version_data.get('history', [])
            except Exception as e:
                logger.error(f"加载版本文件失败: {str(e)}")
        
        # 从数据库加载
        try:
            history = db_manager.fetch_all(
                'SELECT version, description, upgrade_time, status FROM version_history ORDER BY upgrade_time DESC'
            )
            for record in history:
                version_info = {
                    'version': record['version'] if isinstance(record, dict) else record[0],
                    'description': record['description'] if isinstance(record, dict) else record[1],
                    'upgrade_time': record['upgrade_time'] if isinstance(record, dict) else record[2],
                    'status': record['status'] if isinstance(record, dict) else record[3]
                }
                if version_info not in self.version_history:
                    self.version_history.append(version_info)
        except Exception as e:
            logger.error(f"从数据库加载版本历史失败: {str(e)}")
    
    def _save_version(self):
        """保存版本信息"""
        try:
            version_data = {
                'version': self.current_version,
                'history': self.version_history,
                'last_updated': time.time()
            }
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, ensure_ascii=False, indent=2)
            logger.info(f"版本信息保存成功: {self.current_version}")
        except Exception as e:
            logger.error(f"保存版本信息失败: {str(e)}")
    
    def get_current_version(self) -> str:
        """
        获取当前版本
        
        Returns:
            当前版本号
        """
        return self.current_version
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """
        获取版本历史
        
        Returns:
            版本历史列表
        """
        return self.version_history
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较版本号
        
        Args:
            version1: 版本号1
            version2: 版本号2
        
        Returns:
            1: version1 > version2
            0: version1 == version2
            -1: version1 < version2
        """
        v1_parts = [int(part) for part in version1.split('.')]
        v2_parts = [int(part) for part in version2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        
        return 0
    
    def upgrade_version(self, new_version: str, description: str) -> Dict[str, Any]:
        """
        升级版本
        
        Args:
            new_version: 新版本号
            description: 版本描述
        
        Returns:
            升级结果
        """
        # 验证版本号格式
        if not self._validate_version(new_version):
            return {
                'status': 'error',
                'message': '无效的版本号格式'
            }
        
        # 检查版本号是否高于当前版本
        if self.compare_versions(new_version, self.current_version) <= 0:
            return {
                'status': 'error',
                'message': '新版本号必须高于当前版本号'
            }
        
        try:
            # 开始升级
            logger.info(f"开始升级版本: {self.current_version} -> {new_version}")
            
            # 记录升级开始
            db_manager.execute(
                '''
                INSERT INTO version_history (version, description, status)
                VALUES (?, ?, ?)
                ''',
                (new_version, description, 'in_progress')
            )
            
            # 执行升级操作
            upgrade_result = self._perform_upgrade(new_version)
            
            if upgrade_result['status'] == 'success':
                # 更新版本信息
                self.current_version = new_version
                
                # 记录版本历史
                version_info = {
                    'version': new_version,
                    'description': description,
                    'upgrade_time': time.time(),
                    'status': 'completed'
                }
                self.version_history.insert(0, version_info)
                
                # 更新数据库记录
                db_manager.execute(
                    'UPDATE version_history SET status = ? WHERE version = ? AND status = ?',
                    ('completed', new_version, 'in_progress')
                )
                
                # 保存版本信息
                self._save_version()
                
                logger.info(f"版本升级成功: {new_version}")
                return {
                    'status': 'success',
                    'message': f'版本升级成功: {new_version}',
                    'version': new_version,
                    'description': description
                }
            else:
                # 更新数据库记录为失败
                db_manager.execute(
                    'UPDATE version_history SET status = ? WHERE version = ? AND status = ?',
                    ('failed', new_version, 'in_progress')
                )
                
                logger.error(f"版本升级失败: {upgrade_result['message']}")
                return {
                    'status': 'error',
                    'message': f'版本升级失败: {upgrade_result['message']}'
                }
                
        except Exception as e:
            # 更新数据库记录为失败
            try:
                db_manager.execute(
                    'UPDATE version_history SET status = ? WHERE version = ? AND status = ?',
                    ('failed', new_version, 'in_progress')
                )
            except:
                pass
            
            logger.error(f"版本升级异常: {str(e)}")
            return {
                'status': 'error',
                'message': f'版本升级异常: {str(e)}'
            }
    
    def _validate_version(self, version: str) -> bool:
        """
        验证版本号格式
        
        Args:
            version: 版本号
        
        Returns:
            是否有效
        """
        parts = version.split('.')
        if len(parts) != 3:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
        
        return True
    
    def _perform_upgrade(self, new_version: str) -> Dict[str, Any]:
        """
        执行升级操作
        
        Args:
            new_version: 新版本号
        
        Returns:
            升级结果
        """
        try:
            # 执行数据库迁移
            self._migrate_database(new_version)
            
            # 执行配置更新
            self._update_config(new_version)
            
            # 执行其他升级操作
            self._perform_other_upgrades(new_version)
            
            return {
                'status': 'success',
                'message': '升级操作执行成功'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _migrate_database(self, new_version: str) -> None:
        """
        执行数据库迁移
        
        Args:
            new_version: 新版本号
        """
        logger.info("执行数据库迁移")
        
        # 这里可以添加数据库迁移代码
        # 例如：创建新表、修改表结构、添加索引等
        
        # 示例：添加新字段或表
        try:
            # 检查是否需要添加新表或字段
            # 这里可以根据版本号执行不同的迁移操作
            
            logger.info("数据库迁移完成")
        except Exception as e:
            logger.error(f"数据库迁移失败: {str(e)}")
            raise
    
    def _update_config(self, new_version: str) -> None:
        """
        更新配置
        
        Args:
            new_version: 新版本号
        """
        logger.info("更新配置")
        
        # 这里可以添加配置更新代码
        # 例如：更新配置文件、环境变量等
        
        logger.info("配置更新完成")
    
    def _perform_other_upgrades(self, new_version: str) -> None:
        """
        执行其他升级操作
        
        Args:
            new_version: 新版本号
        """
        logger.info("执行其他升级操作")
        
        # 这里可以添加其他升级操作
        # 例如：更新依赖、清理缓存、重建索引等
        
        logger.info("其他升级操作完成")
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        检查更新
        
        Returns:
            更新检查结果
        """
        # 这里可以添加检查更新的逻辑
        # 例如：从服务器获取最新版本信息
        
        # 模拟检查更新
        latest_version = "1.1.0"
        update_available = self.compare_versions(latest_version, self.current_version) > 0
        
        return {
            'status': 'success',
            'current_version': self.current_version,
            'latest_version': latest_version,
            'update_available': update_available,
            'message': f'当前版本: {self.current_version}, 最新版本: {latest_version}'
        }
    
    def rollback_version(self, target_version: str) -> Dict[str, Any]:
        """
        回滚版本
        
        Args:
            target_version: 目标版本号
        
        Returns:
            回滚结果
        """
        # 检查目标版本是否存在
        target_version_info = None
        for info in self.version_history:
            if info['version'] == target_version:
                target_version_info = info
                break
        
        if not target_version_info:
            return {
                'status': 'error',
                'message': '目标版本不存在'
            }
        
        # 检查目标版本是否低于当前版本
        if self.compare_versions(target_version, self.current_version) >= 0:
            return {
                'status': 'error',
                'message': '目标版本必须低于当前版本'
            }
        
        try:
            logger.info(f"开始回滚版本: {self.current_version} -> {target_version}")
            
            # 执行回滚操作
            # 这里可以添加回滚逻辑
            
            # 更新版本信息
            self.current_version = target_version
            
            # 记录回滚历史
            rollback_info = {
                'version': target_version,
                'description': f'回滚到版本 {target_version}',
                'upgrade_time': time.time(),
                'status': 'completed'
            }
            self.version_history.insert(0, rollback_info)
            
            # 保存版本信息
            self._save_version()
            
            logger.info(f"版本回滚成功: {target_version}")
            return {
                'status': 'success',
                'message': f'版本回滚成功: {target_version}',
                'version': target_version
            }
            
        except Exception as e:
            logger.error(f"版本回滚失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'版本回滚失败: {str(e)}'
            }
    
    def get_version_info(self) -> Dict[str, Any]:
        """
        获取版本信息
        
        Returns:
            版本信息
        """
        return {
            'current_version': self.current_version,
            'version_history': self.version_history,
            'last_updated': time.time(),
            'system_info': {
                'python_version': '3.8+',
                'flask_version': '2.0+',
                'database': 'SQLite/MySQL'
            }
        }

# 创建全局版本管理器实例
version_manager = VersionManager()

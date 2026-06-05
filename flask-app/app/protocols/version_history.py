#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本历史记录模块
记录协议版本变更历史
"""

import json
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.utils.logging import logger


class VersionHistory:
    """版本历史记录类"""
    
    def __init__(self, history_file: Optional[str] = None):
        self.history: List[Dict[str, Any]] = []
        self.history_file = history_file or 'protocol_version_history.json'
        
        # 加载历史记录
        if os.path.exists(self.history_file):
            self.load_history()
        
        # 预定义版本历史
        self._initialize_default_history()
    
    def _initialize_default_history(self):
        """初始化默认版本历史记录"""
        if not self.history:
            default_history = [
                {
                    'version': '1.0.0',
                    'release_date': '2024-01-15',
                    'description': '初始版本发布',
                    'changes': [
                        'HTTP协议实现，支持GET/POST/PUT/DELETE/PATCH',
                        'WebSocket协议实现，支持双向通信',
                        'MQTT协议实现，支持发布订阅模式',
                        'gRPC协议实现，支持远程过程调用',
                        '协议管理器统一管理所有协议',
                        '基础消息路由系统'
                    ],
                    'author': 'MTSCOS Development Team',
                    'status': 'stable'
                },
                {
                    'version': '1.1.0',
                    'release_date': '2024-02-20',
                    'description': '性能优化版本',
                    'changes': [
                        'HTTP协议添加重试机制和退避策略',
                        'WebSocket添加连接池管理',
                        'MQTT添加主题通配符匹配',
                        '协议统计信息全面升级',
                        '错误处理机制增强'
                    ],
                    'author': 'MTSCOS Development Team',
                    'status': 'stable'
                },
                {
                    'version': '1.2.0',
                    'release_date': '2024-03-25',
                    'description': '安全增强版本',
                    'changes': [
                        '新增私有数据交互协议',
                        '端到端加密支持',
                        'RSA签名验证',
                        '数据压缩传输',
                        '安全通道封装'
                    ],
                    'author': 'MTSCOS Security Team',
                    'status': 'stable'
                },
                {
                    'version': '1.3.0',
                    'release_date': '2024-04-30',
                    'description': '版本历史记录功能',
                    'changes': [
                        '版本历史记录系统',
                        '自动版本追踪',
                        '变更日志管理',
                        '版本兼容性检查',
                        '升级路径建议'
                    ],
                    'author': 'MTSCOS Development Team',
                    'status': 'stable'
                }
            ]
            self.history = default_history
            self.save_history()
    
    def add_version(self, version: str, description: str, changes: List[str], 
                    author: str = 'Unknown', status: str = 'beta'):
        """添加新版本记录"""
        version_record = {
            'version': version,
            'release_date': datetime.now().strftime('%Y-%m-%d'),
            'description': description,
            'changes': changes,
            'author': author,
            'status': status,
            'timestamp': int(time.time())
        }
        
        self.history.append(version_record)
        self._sort_history()
        self.save_history()
        
        logger.info(f"新版本记录已添加: {version}")
        return version_record
    
    def get_version(self, version: str) -> Optional[Dict[str, Any]]:
        """获取指定版本信息"""
        for record in self.history:
            if record['version'] == version:
                return record
        return None
    
    def get_latest_version(self) -> Dict[str, Any]:
        """获取最新版本"""
        if not self.history:
            return None
        return self.history[0]
    
    def get_all_versions(self) -> List[Dict[str, Any]]:
        """获取所有版本记录"""
        return self.history.copy()
    
    def get_version_history(self, start_version: str = None, end_version: str = None) -> List[Dict[str, Any]]:
        """获取版本历史范围"""
        result = self.history.copy()
        
        if start_version:
            start_idx = None
            for i, record in enumerate(result):
                if record['version'] == start_version:
                    start_idx = i
                    break
            if start_idx is not None:
                result = result[:start_idx + 1]
        
        if end_version:
            end_idx = None
            for i, record in enumerate(result):
                if record['version'] == end_version:
                    end_idx = i
                    break
            if end_idx is not None:
                result = result[end_idx:]
        
        return result
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """比较两个版本的差异"""
        v1 = self.get_version(version1)
        v2 = self.get_version(version2)
        
        if not v1 or not v2:
            return None
        
        v1_changes = set(v1.get('changes', []))
        v2_changes = set(v2.get('changes', []))
        
        return {
            'version1': version1,
            'version2': version2,
            'added': list(v2_changes - v1_changes),
            'removed': list(v1_changes - v2_changes),
            'common': list(v1_changes & v2_changes)
        }
    
    def get_upgrade_path(self, from_version: str) -> List[Dict[str, Any]]:
        """获取升级路径"""
        versions = []
        found = False
        
        for record in self.history:
            if found:
                versions.append(record)
            if record['version'] == from_version:
                found = True
        
        return versions
    
    def validate_version_compatibility(self, version: str) -> Dict[str, Any]:
        """验证版本兼容性"""
        latest = self.get_latest_version()
        if not latest:
            return {'compatible': False, 'message': '无版本记录'}
        
        latest_version = latest['version']
        
        if version == latest_version:
            return {
                'compatible': True,
                'message': '已是最新版本',
                'current_version': version,
                'latest_version': latest_version,
                'upgrade_available': False
            }
        
        # 检查主版本号
        current_parts = version.split('.')
        latest_parts = latest_version.split('.')
        
        if current_parts[0] != latest_parts[0]:
            return {
                'compatible': False,
                'message': '主版本不兼容，需要升级',
                'current_version': version,
                'latest_version': latest_version,
                'upgrade_available': True,
                'upgrade_path': self.get_upgrade_path(version)
            }
        
        return {
            'compatible': True,
            'message': '版本兼容',
            'current_version': version,
            'latest_version': latest_version,
            'upgrade_available': True,
            'upgrade_path': self.get_upgrade_path(version)
        }
    
    def _sort_history(self):
        """按版本号降序排序"""
        self.history.sort(key=lambda x: self._version_to_tuple(x['version']), reverse=True)
    
    def _version_to_tuple(self, version: str) -> tuple:
        """将版本号转换为元组用于比较"""
        parts = version.split('.')
        return tuple(int(p) if p.isdigit() else p for p in parts)
    
    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.info(f"版本历史已保存: {self.history_file}")
        except Exception as e:
            logger.error(f"保存版本历史失败: {str(e)}")
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
            self._sort_history()
            logger.info(f"版本历史已加载: {self.history_file}")
        except Exception as e:
            logger.error(f"加载版本历史失败: {str(e)}")
            self.history = []
    
    def export_history(self, filepath: str, format: str = 'json') -> bool:
        """导出历史记录"""
        try:
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, ensure_ascii=False, indent=2)
            elif format == 'markdown':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self._generate_markdown())
            
            logger.info(f"版本历史已导出: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出版本历史失败: {str(e)}")
            return False
    
    def _generate_markdown(self) -> str:
        """生成Markdown格式的版本历史"""
        md = "# 协议版本历史\n\n"
        
        for record in self.history:
            md += f"## v{record['version']}\n\n"
            md += f"**发布日期**: {record['release_date']}\n\n"
            md += f"**状态**: {record['status']}\n\n"
            md += f"**作者**: {record['author']}\n\n"
            md += f"**描述**: {record['description']}\n\n"
            
            if record.get('changes'):
                md += "**变更内容**:\n\n"
                for change in record['changes']:
                    md += f"- {change}\n"
            
            md += "\n---\n\n"
        
        return md


class VersionTracker:
    """版本追踪器"""
    
    def __init__(self):
        self.history = VersionHistory()
        self.current_version = self.history.get_latest_version()['version']
        self.upgrade_log = []
    
    def track_version(self, version: str, source: str = 'unknown'):
        """记录版本使用情况"""
        log_entry = {
            'version': version,
            'source': source,
            'timestamp': int(time.time()),
            'datetime': datetime.now().isoformat()
        }
        self.upgrade_log.append(log_entry)
        
        logger.info(f"版本使用记录: {version} from {source}")
    
    def get_version_stats(self) -> Dict[str, Any]:
        """获取版本使用统计"""
        version_counts = {}
        for entry in self.upgrade_log:
            version = entry['version']
            version_counts[version] = version_counts.get(version, 0) + 1
        
        return {
            'total_records': len(self.upgrade_log),
            'version_distribution': version_counts,
            'current_version': self.current_version,
            'latest_version': self.history.get_latest_version()['version']
        }
    
    def suggest_upgrade(self, current_version: str) -> Dict[str, Any]:
        """提供升级建议"""
        compatibility = self.history.validate_version_compatibility(current_version)
        
        if not compatibility['upgrade_available']:
            return {
                'suggestion': '当前已是最新版本，无需升级',
                'action': 'none'
            }
        
        upgrade_path = compatibility.get('upgrade_path', [])
        
        if not upgrade_path:
            return {
                'suggestion': '建议升级到最新版本',
                'action': 'upgrade',
                'target_version': compatibility['latest_version']
            }
        
        return {
            'suggestion': f'检测到可用升级，建议升级到 v{compatibility["latest_version"]}',
            'action': 'upgrade',
            'target_version': compatibility['latest_version'],
            'upgrade_steps': len(upgrade_path),
            'path': upgrade_path
        }


# 创建全局版本历史记录实例
version_history = VersionHistory()
version_tracker = VersionTracker()
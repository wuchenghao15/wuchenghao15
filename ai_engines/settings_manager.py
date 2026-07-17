# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理系统
Settings Management System

特性:
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict
import threading
import logging

logger = logging.getLogger('settings_manager')


class SettingScope(Enum):
    """设置作用域"""
    GLOBAL = "global"           # 全局设置
    USER = "user"               # 用户设置
    SESSION = "session"         # 会话设置
    SYSTEM = "system"           # 系统设置


class SettingType(Enum):
    """设置类型"""
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    LIST = "list"
    DICT = "dict"
    JSON = "json"


class SettingSyncStatus(Enum):
    """同步状态"""
    SYNCED = "synced"           # 已同步
    PENDING = "pending"         # 待同步
    CONFLICT = "conflict"       # 冲突
    SYNCING = "syncing"         # 同步中


class Setting:
    """设置项定义"""
    
    def __init__(self, key: str, name: str, setting_type: SettingType):
        self.key = key
        self.name = name
        self.type = setting_type
        self.scope = SettingScope.GLOBAL
        
        self.value = None
        self.default_value = None
        self.description = ""
        
        self.options = []
        self.validators = []
        
        self.ai_recommended = False
        self.ai_score = 0.0
        self.ai_reason = ""
        
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.last_synced_at = None
        self.sync_status = SettingSyncStatus.SYNCED
        
        self.metadata = {}
    
    def set_value(self, value, validate=True):
        """设置值"""
        if validate:
            self._validate(value)
        
        old_value = self.value
        self.value = value
        self.updated_at = datetime.now().isoformat()
        self.sync_status = SettingSyncStatus.PENDING
        
        return old_value
    
    def _validate(self, value):
        """验证值"""
        if self.type == SettingType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError(f"Expected boolean, got {type(value).__name__}")
        
        elif self.type == SettingType.INTEGER:
            if not isinstance(value, int):
                raise ValueError(f"Expected integer, got {type(value).__name__}")
        
        elif self.type == SettingType.FLOAT:
            if not isinstance(value, (int, float)):
                raise ValueError(f"Expected float, got {type(value).__name__}")
        
        elif self.type == SettingType.STRING:
            if not isinstance(value, str):
                raise ValueError(f"Expected string, got {type(value).__name__}")
        
        elif self.type == SettingType.LIST:
            if not isinstance(value, list):
                raise ValueError(f"Expected list, got {type(value).__name__}")
        
        elif self.type == SettingType.DICT:
            if not isinstance(value, dict):
                raise ValueError(f"Expected dict, got {type(value).__name__}")
        
        # 自定义验证器
        for validator in self.validators:
            validator(value)
    
    def apply_ai_recommendation(self, recommended_value, score, reason):
        """应用AI推荐"""
        self.value = recommended_value
        self.ai_recommended = True
        self.ai_score = score
        self.ai_reason = reason
        self.updated_at = datetime.now().isoformat()
        self.sync_status = SettingSyncStatus.PENDING
    
    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'name': self.name,
            'type': self.type.value,
            'scope': self.scope.value,
            'value': self.value,
            'default_value': self.default_value,
            'description': self.description,
            'options': self.options,
            'ai_recommended': self.ai_recommended,
            'ai_score': self.ai_score,
            'ai_reason': self.ai_reason,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_synced_at': self.last_synced_at,
            'sync_status': self.sync_status.value,
            'metadata': self.metadata
        }


class SettingsManager:
    """设置管理器"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'settings'
        )
        
        self.settings_dir = os.path.join(self.storage_dir, 'settings')
        self.snapshots_dir = os.path.join(self.storage_dir, 'snapshots')
        self.metadata_dir = os.path.join(self.storage_dir, '.metadata')
        
        self.settings_file = os.path.join(self.metadata_dir, 'settings.json')
        self.sync_log_file = os.path.join(self.metadata_dir, 'sync_log.json')
        
        self.settings = {}
        self.sync_log = []
        
        self.lock = threading.Lock()
        
        self._ensure_directories()
        self._load_data()
        self._register_default_settings()
        
        # AI优化器
        self.ai_optimizer = AISettingsOptimizer(self)
        
        # 同步管理器
        self.sync_manager = SyncManager(self)
        
        # 启动同步线程
        self._start_sync_thread()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        directories = [
            self.storage_dir,
            self.settings_dir,
            self.snapshots_dir,
            self.metadata_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def _load_data(self):
        """加载数据"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, setting_data in data.items():
                        setting = Setting(key, setting_data['name'], SettingType(setting_data['type']))
                        setting.__dict__.update(setting_data)
                        setting.type = SettingType(setting.type)
                        setting.scope = SettingScope(setting.scope)
                        setting.sync_status = SettingSyncStatus(setting.sync_status)
                        self.settings[key] = setting
            except Exception as e:
                logger.error(f"加载设置失败: {str(e)}")
        
        if os.path.exists(self.sync_log_file):
            try:
                with open(self.sync_log_file, 'r', encoding='utf-8') as f:
                    self.sync_log = json.load(f)
            except Exception as e:
                logger.error(f"加载同步日志失败: {str(e)}")
    
    def _save_data(self):
        """保存数据"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                data = {key: setting.to_dict() for key, setting in self.settings.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存设置失败: {str(e)}")
        
        try:
            with open(self.sync_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.sync_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存同步日志失败: {str(e)}")
    
    def _register_default_settings(self):
        """注册默认设置"""
        default_settings = [
            {
                'key': 'system.auto_upgrade_enabled',
                'name': '自动升级',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.SYSTEM,
                'default_value': True,
                'description': '是否启用自动升级'
            },
            {
                'key': 'system.maintenance_enabled',
                'name': '例行维护',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.SYSTEM,
                'default_value': True,
                'description': '是否启用力行维护'
            },
            {
                'key': 'ai.auto_analytics_enabled',
                'name': 'AI自动分析',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.GLOBAL,
                'default_value': True,
                'description': '是否启用AI自动分析'
            },
            {
                'key': 'ai.skill_recommendation_enabled',
                'name': '技能推荐',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.GLOBAL,
                'default_value': True,
                'description': '是否启用AI技能推荐'
            },
            {
                'key': 'backup.dual_backup_enabled',
                'name': '双备份机制',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.GLOBAL,
                'default_value': True,
                'description': '是否启用双备份机制'
            },
            {
                'key': 'backup.backup_interval',
                'name': '备份间隔',
                'type': SettingType.INTEGER,
                'scope': SettingScope.GLOBAL,
                'default_value': 24,
                'description': '备份间隔(小时)',
                'options': [6, 12, 24, 48]
            },
            {
                'key': 'certificate.auto_renew_enabled',
                'name': '证书自动续期',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.GLOBAL,
                'default_value': True,
                'description': '是否启用证书自动续期'
            },
            {
                'key': 'recovery.incremental_backup_enabled',
                'name': '增量备份',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.GLOBAL,
                'default_value': True,
                'description': '是否启用增量备份'
            },
            {
                'key': 'task.auto_assignment_enabled',
                'name': '任务自动分配',
                'type': SettingType.BOOLEAN,
                'scope': SettingScope.GLOBAL,
                'default_value': True,
                'description': '是否启用任务自动分配'
            },
            {
                'key': 'task.priority_threshold',
                'name': '优先级阈值',
                'type': SettingType.INTEGER,
                'scope': SettingScope.GLOBAL,
                'default_value': 3,
                'description': '任务优先级阈值',
                'options': [1, 2, 3, 4, 5]
            },
        ]
        
        for setting_data in default_settings:
            key = setting_data['key']
            if key not in self.settings:
                setting = Setting(key, setting_data['name'], setting_data['type'])
                setting.scope = setting_data['scope']
                setting.default_value = setting_data['default_value']
                setting.description = setting_data.get('description', '')
                setting.value = setting_data['default_value']
                
                if 'options' in setting_data:
                    setting.options = setting_data['options']
                
                self.settings[key] = setting
        
        self._save_data()
    
    def _start_sync_thread(self):
        """启动同步线程"""
        def sync_loop():
            while True:
                self.sync_manager.run_sync()
                time.sleep(30)
        
        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()
        logger.info("设置同步线程已启动")
    
    def get_setting(self, key: str) -> Optional[Setting]:
        """获取设置"""
        return self.settings.get(key)
    
    def set_setting(self, key: str, value, user_id: str = None) -> bool:
        """设置值"""
        setting = self.get_setting(key)
        if not setting:
            return False
        
        try:
            setting.set_value(value)
            
            # 记录变更
            self._log_change(key, 'update', value, user_id)
            
            # 触发AI优化
            self.ai_optimizer.on_setting_change(key, value)
            
            self._save_data()
            return True
        except ValueError as e:
            logger.error(f"设置值失败: {str(e)}")
            return False
    
    def create_setting(self, key: str, name: str, setting_type: SettingType, **kwargs) -> bool:
        """创建设置"""
        if key in self.settings:
            return False
        
        setting = Setting(key, name, setting_type)
        
        if 'scope' in kwargs:
            setting.scope = kwargs['scope']
        if 'default_value' in kwargs:
            setting.default_value = kwargs['default_value']
            setting.value = kwargs['default_value']
        if 'description' in kwargs:
            setting.description = kwargs['description']
        if 'options' in kwargs:
            setting.options = kwargs['options']
        if 'validators' in kwargs:
            setting.validators = kwargs['validators']
        if 'metadata' in kwargs:
            setting.metadata = kwargs['metadata']
        
        self.settings[key] = setting
        self._save_data()
        
        self._log_change(key, 'create', setting.value, None)
        
        logger.info(f"创建设置: {key}")
        return True
    
    def delete_setting(self, key: str) -> bool:
        """删除设置"""
        if key not in self.settings:
            return False
        
        del self.settings[key]
        self._save_data()
        
        self._log_change(key, 'delete', None, None)
        
        logger.info(f"删除设置: {key}")
        return True
    
    def list_settings(self, scope: SettingScope = None,
                     setting_type: SettingType = None) -> List[Dict]:
        """列出设置"""
        results = []
        
        for setting in self.settings.values():
            if scope and setting.scope != scope:
                continue
            if setting_type and setting.type != setting_type:
                continue
            
            results.append(setting.to_dict())
        
        return sorted(results, key=lambda x: x['key'])
    
    def apply_ai_recommendations(self):
        """应用AI推荐"""
        recommendations = self.ai_optimizer.generate_recommendations()
        
        for key, rec in recommendations.items():
            setting = self.get_setting(key)
            if setting:
                setting.apply_ai_recommendation(rec['value'], rec['score'], rec['reason'])
                logger.info(f"应用AI推荐: {key} -> {rec['value']}")
        
        self._save_data()
        return recommendations
    
    def get_ai_recommendations(self) -> Dict:
        """获取AI推荐"""
        return self.ai_optimizer.generate_recommendations()
    
    def _log_change(self, key: str, action: str, value, user_id: str):
        """记录变更日志"""
        log_entry = {
            'id': f"log_{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now().isoformat(),
            'key': key,
            'action': action,
            'value': value,
            'user_id': user_id
        }
        
        self.sync_log.append(log_entry)
        if len(self.sync_log) > 1000:
            self.sync_log = self.sync_log[-1000:]
    
    def get_change_log(self, limit: int = 50) -> List[Dict]:
        """获取变更日志"""
        return sorted(self.sync_log, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        total_settings = len(self.settings)
        pending_sync = sum(1 for s in self.settings.values() if s.sync_status == SettingSyncStatus.PENDING)
        synced = sum(1 for s in self.settings.values() if s.sync_status == SettingSyncStatus.SYNCED)
        conflict = sum(1 for s in self.settings.values() if s.sync_status == SettingSyncStatus.CONFLICT)
        
        return {
            'total_settings': total_settings,
            'pending_sync': pending_sync,
            'synced': synced,
            'conflict': conflict,
            'last_sync': self.sync_manager.last_sync_time,
            'ai_optimization_enabled': self.ai_optimizer.enabled
        }


class AISettingsOptimizer:
    """AI设置优化器"""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.enabled = True
        
        # 匹配规则
        self.matching_rules = {
            'system.auto_upgrade_enabled': {
                'dependencies': ['ai.auto_analytics_enabled'],
                'condition': lambda s: s.get('ai.auto_analytics_enabled') == True,
                'recommendation': True,
                'score': 0.85,
                'reason': 'AI分析已启用,建议启用自动升级以保持系统最新'
            },
            'system.maintenance_enabled': {
                'dependencies': ['backup.dual_backup_enabled'],
                'condition': lambda s: s.get('backup.dual_backup_enabled') == True,
                'recommendation': True,
                'score': 0.9,
                'reason': '双备份已启用,建议启用力行维护确保数据安全'
            },
            'backup.backup_interval': {
                'dependencies': ['task.auto_assignment_enabled'],
                'condition': lambda s: s.get('task.auto_assignment_enabled') == True,
                'recommendation': 12,
                'score': 0.75,
                'reason': '任务自动分配已启用,建议缩短备份间隔至12小时'
            },
            'ai.skill_recommendation_enabled': {
                'dependencies': ['ai.auto_analytics_enabled'],
                'condition': lambda s: s.get('ai.auto_analytics_enabled') == True,
                'recommendation': True,
                'score': 0.95,
                'reason': 'AI分析已启用,建议启用技能推荐以提升AI能力'
            },
            'recovery.incremental_backup_enabled': {
                'dependencies': ['backup.dual_backup_enabled'],
                'condition': lambda s: s.get('backup.dual_backup_enabled') == True,
                'recommendation': True,
                'score': 0.88,
                'reason': '双备份已启用,建议启用增量备份节省存储空间'
            },
        }
    
    def on_setting_change(self, key: str, value):
        """设置变更时触发优化"""
        if not self.enabled:
            return
        
        # 检查是否有相关推荐需要更新
        recommendations = self.generate_recommendations()
        
        for rec_key, rec in recommendations.items():
            if rec['score'] > 0.8:
                setting = self.settings_manager.get_setting(rec_key)
                if setting and setting.value != rec['value']:
                    logger.info(f"AI推荐: {rec_key} -> {rec['value']}")
    
    def generate_recommendations(self) -> Dict:
        """生成推荐"""
        recommendations = {}
        current_settings = self._get_current_settings_dict()
        
        for key, rule in self.matching_rules.items():
            # 检查依赖条件
            if 'condition' in rule and not rule['condition'](current_settings):
                continue
            
            # 获取当前值
            current_value = current_settings.get(key)
            
            # 如果当前值已经是推荐值,跳过
            if current_value == rule['recommendation']:
                continue
            
            recommendations[key] = {
                'value': rule['recommendation'],
                'score': rule['score'],
                'reason': rule['reason'],
                'current_value': current_value
            }
        
        return recommendations
    
    def _get_current_settings_dict(self) -> Dict:
        """获取当前设置字典"""
        return {
            key: setting.value
            for key, setting in self.settings_manager.settings.items()
        }
    
    def analyze_settings(self) -> Dict:
        """分析设置状态"""
        current_settings = self._get_current_settings_dict()
        recommendations = self.generate_recommendations()
        
        # 计算匹配度
        total_rules = len(self.matching_rules)
        matched_rules = sum(
            1 for rule in self.matching_rules.values()
            if rule['condition'](current_settings)
        )
        
        return {
            'total_rules': total_rules,
            'matched_rules': matched_rules,
            'match_rate': matched_rules / total_rules * 100,
            'recommendations_count': len(recommendations),
            'recommendations': recommendations
        }


class SyncManager:
    """同步管理器"""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.last_sync_time = None
        self.sync_interval = 30
        self.enabled = True
    
    def run_sync(self):
        """执行同步"""
        if not self.enabled:
            return
        
        try:
            self.last_sync_time = datetime.now().isoformat()
            
            # 检查待同步项
            pending_settings = [
                s for s in self.settings_manager.settings.values()
                if s.sync_status == SettingSyncStatus.PENDING
            ]
            
            if not pending_settings:
                return
            
            logger.info(f"同步 {len(pending_settings)} 个设置项")
            
            # 模拟同步到数据库
            for setting in pending_settings:
                self._sync_setting(setting)
            
            logger.info("设置同步完成")
            
        except Exception as e:
            logger.error(f"同步失败: {str(e)}")
    
    def _sync_setting(self, setting: Setting):
        """同步单个设置"""
        setting.sync_status = SettingSyncStatus.SYNCING
        
        try:
            # 模拟数据库同步
            time.sleep(0.1)
            
            setting.last_synced_at = datetime.now().isoformat()
            setting.sync_status = SettingSyncStatus.SYNCED
            
            logger.debug(f"同步成功: {setting.key}")
            
        except Exception as e:
            setting.sync_status = SettingSyncStatus.CONFLICT
            logger.error(f"同步失败: {setting.key} - {str(e)}")
    
    def force_sync(self, key: str = None) -> bool:
        """强制同步"""
        if key:
            setting = self.settings_manager.get_setting(key)
            if setting:
                self._sync_setting(setting)
                return setting.sync_status == SettingSyncStatus.SYNCED
            return False
        else:
            self.run_sync()
            return True
    
    def check_consistency(self) -> Dict:
        """检查数据一致性"""
        results = {
            'conflicts': [],
            'pending_count': 0,
            'synced_count': 0,
            'consistent': True
        }
        
        for setting in self.settings_manager.settings.values():
            if setting.sync_status == SettingSyncStatus.CONFLICT:
                results['conflicts'].append({
                    'key': setting.key,
                    'value': setting.value,
                    'last_synced_at': setting.last_synced_at
                })
                results['consistent'] = False
            elif setting.sync_status == SettingSyncStatus.PENDING:
                results['pending_count'] += 1
            else:
                results['synced_count'] += 1
        
        return results
    
    def resolve_conflicts(self) -> Dict:
        """解决冲突"""
        conflicts = self.check_consistency()['conflicts']
        resolved = []
        
        for conflict in conflicts:
            setting = self.settings_manager.get_setting(conflict['key'])
            if setting:
                setting.sync_status = SettingSyncStatus.PENDING
                self._sync_setting(setting)
                resolved.append(conflict['key'])
        
        return {
            'resolved': resolved,
            'count': len(resolved)
        }


# 全局实例
settings_manager = SettingsManager()

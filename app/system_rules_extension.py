#!/usr/bin/env python3
"""
系统规则扩展服务
管理Git同步、自动备份、影子节点、副本、记录点、日志记录、历史数据、灰度发布等规则
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

class SystemRulesExtension:
    """系统规则扩展服务"""
    
    NEW_SYSTEM_RULES = [
        # ==================== Git自动同步规则 ====================
        ('GIT_AUTO_SYNC_ENABLED', 'Git自动同步启用', '1', 'git', '是否启用Git自动同步功能', 1),
        ('GIT_AUTO_SYNC_INTERVAL', 'Git同步间隔', '300', 'git', '自动同步时间间隔(秒)', 1),
        ('GIT_SYNC_BRANCH', '同步分支', 'main', 'git', '默认同步分支', 1),
        ('GIT_SYNC_REMOTE', '远程仓库', 'origin', 'git', '远程仓库名称', 1),
        ('GIT_AUTO_COMMIT_ENABLED', '自动提交启用', '1', 'git', '是否启用自动提交', 1),
        ('GIT_COMMIT_MESSAGE', '提交消息模板', 'Auto sync: {timestamp}', 'git', '自动提交消息模板', 1),
        ('GIT_AUTO_PUSH_ENABLED', '自动推送启用', '1', 'git', '是否启用自动推送到远程', 1),
        ('GIT_SYNC_ON_STARTUP', '启动时同步', '1', 'git', '系统启动时是否执行同步', 1),
        ('GIT_SYNC_ON_SHUTDOWN', '关闭时同步', '1', 'git', '系统关闭时是否执行同步', 1),
        ('GIT_SYNC_RETRY_COUNT', '同步重试次数', '3', 'git', '同步失败时重试次数', 1),
        ('GIT_SYNC_RETRY_DELAY', '同步重试延迟', '30', 'git', '同步重试间隔(秒)', 1),
        ('GIT_SYNC_MODE', '同步模式', 'file_change', 'git', '同步触发模式: file_change(文件变更触发) / timer(定时触发)', 1),

        # ==================== AI安全防御规则 ====================
        ('AI_SECURITY_DEFEND_ENABLED', 'AI安全防御启用', '1', 'security', '是否启用AI自动安全防御', 1),
        ('AI_SECURITY_DEFEND_INTERVAL', 'AI防御检测间隔', '300', 'security', 'AI安全防御检测间隔(秒)', 1),
        ('SECURITY_LOCK_LEVEL_SOFT', '软锁定时长', '900', 'security', '软锁定持续时间(秒)', 1),
        ('SECURITY_LOCK_LEVEL_HARD', '硬锁定时长', '3600', 'security', '硬锁定持续时间(秒)', 1),
        ('SECURITY_LOCK_LEVEL_PERMANENT', '永久锁定时长', '86400', 'security', '永久锁定持续时间(秒)', 1),
        ('SECURITY_MAX_FAILED_LOGINS', '最大登录失败次数', '5', 'security', '触发锁定的登录失败次数阈值', 1),
        ('SECURITY_MAX_UNLOCK_ATTEMPTS', '最大解锁尝试次数', '3', 'security', '触发暴力解锁保护的尝试次数', 1),
        ('SECURITY_IP_RATE_LIMIT', 'IP限流阈值', '60', 'security', '单IP每分钟最大请求数', 1),
        ('SECURITY_IP_BLACKLIST_DURATION', 'IP黑名单时长', '3600', 'security', 'IP黑名单持续时长(秒)', 1),
        ('SECURITY_SESSION_ABSOLUTE_TIMEOUT', '会话绝对超时', '28800', 'security', '会话最大持续时间(秒)', 1),
        ('SECURITY_AUTO_BLACKLIST_THRESHOLD', '自动黑名单阈值', '10', 'security', 'AI自动拉黑IP的安全事件次数阈值', 1),
        
        # ==================== VIKEY加密狗强制规则 ====================
        ('VIKEY_FORCE_CHECK_ENABLED', 'VIKEY强制检查启用', '1', 'security', '是否启用VIKEY强制检查（无论调试/普通模式）', 1),
        ('VIKEY_SUPER_ADMIN_REQUIRED', '超级管理员强制VIKEY', '1', 'security', '超级管理员界面和操作是否必须插入VIKEY', 1),
        ('VIKEY_CHECK_INTERVAL', 'VIKEY检测间隔', '2000', 'security', 'VIKEY状态轮询检测间隔(毫秒)', 1),
        ('VIKEY_LOCK_TIMEOUT', 'VIKEY锁定超时', '300', 'security', 'VIKEY拔出后锁定超时时间(秒)，超时后自动退出系统', 1),
        ('VIKEY_LOCK_SNAPSHOT_ENABLED', '锁定时快照启用', '1', 'security', 'VIKEY拔出时是否保存操作状态快照', 1),
        ('VIKEY_ALLOW_DEBUG_BYPASS', '允许调试模式绕过', '0', 'security', '是否允许在调试模式下绕过VIKEY检测（0=不允许，1=允许）', 1),
        ('VIKEY_REQUIRED_SERIAL', '要求的VIKEY序列号', '', 'security', '指定必须插入的VIKEY序列号（为空则接受任何已绑定VIKEY）', 1),
        
        # ==================== GitHub自动同步规则 ====================
        ('GITHUB_AUTO_SYNC_ENABLED', 'GitHub自动同步启用', '1', 'github', '是否启用GitHub自动同步', 1),
        ('GITHUB_SYNC_TOKEN', 'GitHub访问令牌', '', 'github', 'GitHub Personal Access Token', 1),
        ('GITHUB_REPO_OWNER', '仓库所有者', 'MTSCOS', 'github', 'GitHub仓库所有者', 1),
        ('GITHUB_REPO_NAME', '仓库名称', 'MTSCOS_AI_Project', 'github', 'GitHub仓库名称', 1),
        ('GITHUB_SYNC_DIRECTION', '同步方向', 'bidirectional', 'github', '同步方向: push/pull/bidirectional', 1),
        ('GITHUB_SYNC_ON_COMMIT', '提交时同步', '1', 'github', '本地提交后是否同步到GitHub', 1),
        
        # ==================== 自动备份规则 ====================
        ('AUTO_BACKUP_ENABLED', '自动备份启用', '1', 'backup', '是否启用自动备份功能', 1),
        ('BACKUP_INTERVAL', '备份间隔', '3600', 'backup', '自动备份时间间隔(秒)', 1),
        ('BACKUP_RETENTION_DAYS', '备份保留天数', '7', 'backup', '备份文件保留天数', 1),
        ('BACKUP_MAX_COUNT', '最大备份数', '30', 'backup', '保留的最大备份数量', 1),
        ('BACKUP_ON_SHUTDOWN', '关闭时备份', '1', 'backup', '系统关闭时是否执行备份', 1),
        ('BACKUP_ON_STARTUP', '启动时备份', '0', 'backup', '系统启动时是否执行备份', 1),
        ('BACKUP_COMPRESS_ENABLED', '压缩备份', '1', 'backup', '是否压缩备份文件', 1),
        ('BACKUP_ENCRYPT_ENABLED', '加密备份', '0', 'backup', '是否加密备份文件', 1),
        ('BACKUP_PATH', '备份路径', './backups', 'backup', '备份文件存储路径', 1),
        ('BACKUP_INCLUDE_LOGS', '包含日志', '1', 'backup', '备份是否包含日志文件', 1),
        
        # ==================== 增量备份规则 ====================
        ('INCREMENTAL_BACKUP_ENABLED', '增量备份启用', '1', 'backup', '是否启用增量备份', 1),
        ('INCREMENTAL_BACKUP_INTERVAL', '增量备份间隔', '600', 'backup', '增量备份时间间隔(秒)', 1),
        ('INCREMENTAL_BACKUP_FULL_INTERVAL', '全量备份间隔', '86400', 'backup', '全量备份时间间隔(秒)', 1),
        
        # ==================== 影子节点规则 ====================
        ('SHADOW_NODE_ENABLED', '影子节点启用', '1', 'high_availability', '是否启用影子节点', 1),
        ('SHADOW_NODE_COUNT', '影子节点数量', '2', 'high_availability', '影子节点数量', 1),
        ('SHADOW_NODE_SYNC_INTERVAL', '节点同步间隔', '60', 'high_availability', '影子节点同步时间间隔(秒)', 1),
        ('SHADOW_NODE_FAILOVER_ENABLED', '自动故障转移', '1', 'high_availability', '是否启用自动故障转移', 1),
        ('SHADOW_NODE_HEALTH_CHECK_INTERVAL', '健康检查间隔', '10', 'high_availability', '健康检查时间间隔(秒)', 1),
        
        # ==================== 副本规则 ====================
        ('DATA_REPLICATION_ENABLED', '数据副本启用', '1', 'high_availability', '是否启用数据副本', 1),
        ('REPLICATION_FACTOR', '副本因子', '3', 'high_availability', '数据副本数量', 1),
        ('REPLICATION_SYNC_MODE', '同步模式', 'synchronous', 'high_availability', '副本同步模式: synchronous/asynchronous', 1),
        ('REPLICATION_CONSISTENCY', '一致性级别', 'strong', 'high_availability', '数据一致性级别', 1),
        
        # ==================== 记录点规则 ====================
        ('CHECKPOINT_ENABLED', '记录点启用', '1', 'recovery', '是否启用记录点功能', 1),
        ('CHECKPOINT_INTERVAL', '记录点间隔', '300', 'recovery', '记录点时间间隔(秒)', 1),
        ('CHECKPOINT_ON_OPERATION', '操作记录点', '1', 'recovery', '关键操作后是否创建记录点', 1),
        ('CHECKPOINT_RETENTION', '记录点保留数', '50', 'recovery', '保留的记录点数量', 1),
        ('CHECKPOINT_COMPRESS_ENABLED', '压缩记录点', '1', 'recovery', '是否压缩记录点数据', 1),
        
        # ==================== 操作记录规则 ====================
        ('OPERATION_LOG_ENABLED', '操作日志启用', '1', 'audit', '是否启用操作日志', 1),
        ('OPERATION_LOG_TO_DATABASE', '记录到数据库', '1', 'audit', '是否将操作记录到数据库', 1),
        ('OPERATION_LOG_TO_FILE', '记录到文件', '1', 'audit', '是否将操作记录到日志文件', 1),
        ('OPERATION_LOG_LEVEL', '日志级别', 'INFO', 'audit', '操作日志级别', 1),
        ('OPERATION_LOG_RETENTION_DAYS', '日志保留天数', '30', 'audit', '操作日志保留天数', 1),
        ('OPERATION_LOG_MAX_SIZE', '日志最大大小', '104857600', 'audit', '单个日志文件最大大小(字节)', 1),
        
        # ==================== 历史数据规则 ====================
        ('HISTORY_DATA_ENABLED', '历史数据启用', '1', 'data', '是否启用历史数据记录', 1),
        ('HISTORY_DATA_RETENTION_DAYS', '历史数据保留天数', '90', 'data', '历史数据保留天数', 1),
        ('HISTORY_DATA_COMPRESS_ENABLED', '压缩历史数据', '1', 'data', '是否压缩历史数据', 1),
        ('HISTORY_DATA_ARCHIVE_ENABLED', '归档历史数据', '1', 'data', '是否自动归档历史数据', 1),
        ('HISTORY_DATA_ARCHIVE_INTERVAL', '归档间隔', '86400', 'data', '自动归档时间间隔(秒)', 1),
        
        # ==================== 灰度发布规则 ====================
        ('GRAY_RELEASE_ENABLED', '灰度发布启用', '1', 'release', '是否启用灰度发布', 1),
        ('GRAY_RELEASE_PERCENTAGE', '灰度比例', '10', 'release', '灰度发布用户比例(%)', 1),
        ('GRAY_RELEASE_USER_LIST', '灰度用户列表', '', 'release', '指定的灰度用户ID列表(逗号分隔)', 1),
        ('GRAY_RELEASE_ROLLBACK_ON_ERROR', '错误回滚', '1', 'release', '检测到错误时是否自动回滚', 1),
        ('GRAY_RELEASE_ERROR_THRESHOLD', '错误阈值', '5', 'release', '触发回滚的错误率阈值(%)', 1),
        ('GRAY_RELEASE_GRADUAL_ENABLED', '渐进式发布', '1', 'release', '是否启用渐进式灰度发布', 1),
        ('GRAY_RELEASE_GRADUAL_STEPS', '渐进步骤', '5', 'release', '渐进式发布步骤数', 1),
        ('GRAY_RELEASE_GRADUAL_INTERVAL', '渐进间隔', '3600', 'release', '渐进式发布步骤间隔(秒)', 1),
        ('GRAY_RELEASE_MONITOR_ENABLED', '发布监控', '1', 'release', '是否启用灰度发布监控', 1),
        
        # ==================== 自动增量规则 ====================
        ('AUTO_INCREMENTAL_ENABLED', '自动增量启用', '1', 'update', '是否启用自动增量更新', 1),
        ('AUTO_INCREMENTAL_CHECK_INTERVAL', '增量检查间隔', '300', 'update', '增量更新检查间隔(秒)', 1),
        ('AUTO_INCREMENTAL_APPLY_ON_DETECT', '检测后自动应用', '1', 'update', '检测到增量更新后是否自动应用', 1),
        ('AUTO_INCREMENTAL_BACKUP_BEFORE', '应用前备份', '1', 'update', '应用增量更新前是否备份', 1),
    ]
    
    def __init__(self):
        self._init_rules()
    
    def _init_rules(self):
        """初始化系统规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                rule_value TEXT,
                rule_type TEXT DEFAULT 'system',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        added_count = 0
        skipped_count = 0
        
        for rule in self.NEW_SYSTEM_RULES:
            rule_code = rule[0]
            cursor.execute('SELECT COUNT(*) FROM system_rules WHERE rule_code = ?', (rule_code,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO system_rules (rule_code, rule_name, rule_value, rule_type, description, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', rule)
                added_count += 1
                logger.info(f"✓ 添加系统规则: {rule_code}")
            else:
                skipped_count += 1
        
        conn.commit()
        conn.close()
        
        if added_count > 0:
            logger.info(f"✓ 已添加 {added_count} 条新系统规则")
        if skipped_count > 0:
            logger.info(f"✓ 跳过 {skipped_count} 条已存在规则")
    
    def get_rule(self, rule_code: str) -> Optional[str]:
        """获取规则值"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (rule_code,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_rule(self, rule_code: str, value: str) -> bool:
        """设置规则值"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE system_rules SET rule_value = ?, updated_at = ? WHERE rule_code = ?
        ''', (value, datetime.now().isoformat(), rule_code))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_rules_by_type(self, rule_type: str) -> List[Dict]:
        """按类型获取规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_rules WHERE rule_type = ? AND is_active = 1', (rule_type,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'rule_code': row[1],
            'rule_name': row[2],
            'rule_value': row[3],
            'rule_type': row[4],
            'description': row[5],
            'is_active': row[6],
            'created_at': row[7],
            'updated_at': row[8]
        } for row in rows]
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_rules WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'rule_code': row[1],
            'rule_name': row[2],
            'rule_value': row[3],
            'rule_type': row[4],
            'description': row[5],
            'is_active': row[6],
            'created_at': row[7],
            'updated_at': row[8]
        } for row in rows]
    
    def is_rule_enabled(self, rule_code: str) -> bool:
        """检查规则是否启用"""
        value = self.get_rule(rule_code)
        return value is not None and value == '1'
    
    def get_git_sync_config(self) -> Dict:
        """获取Git同步配置"""
        return {
            'auto_sync_enabled': self.is_rule_enabled('GIT_AUTO_SYNC_ENABLED'),
            'sync_mode': self.get_rule('GIT_SYNC_MODE') or 'file_change',
            'sync_interval': int(self.get_rule('GIT_AUTO_SYNC_INTERVAL') or 300),
            'sync_branch': self.get_rule('GIT_SYNC_BRANCH') or 'main',
            'sync_remote': self.get_rule('GIT_SYNC_REMOTE') or 'mtscos_origin',
            'auto_commit_enabled': self.is_rule_enabled('GIT_AUTO_COMMIT_ENABLED'),
            'commit_message': self.get_rule('GIT_COMMIT_MESSAGE') or 'Auto sync: {timestamp}',
            'auto_push_enabled': self.is_rule_enabled('GIT_AUTO_PUSH_ENABLED'),
            'sync_on_startup': self.is_rule_enabled('GIT_SYNC_ON_STARTUP'),
            'sync_on_shutdown': self.is_rule_enabled('GIT_SYNC_ON_SHUTDOWN'),
            'retry_count': int(self.get_rule('GIT_SYNC_RETRY_COUNT') or 3),
            'retry_delay': int(self.get_rule('GIT_SYNC_RETRY_DELAY') or 30)
        }
    
    def get_github_sync_config(self) -> Dict:
        """获取GitHub同步配置"""
        return {
            'auto_sync_enabled': self.is_rule_enabled('GITHUB_AUTO_SYNC_ENABLED'),
            'access_token': self.get_rule('GITHUB_SYNC_TOKEN') or '',
            'repo_owner': self.get_rule('GITHUB_REPO_OWNER') or 'MTSCOS',
            'repo_name': self.get_rule('GITHUB_REPO_NAME') or 'MTSCOS_AI_Project',
            'sync_direction': self.get_rule('GITHUB_SYNC_DIRECTION') or 'bidirectional',
            'sync_on_commit': self.is_rule_enabled('GITHUB_SYNC_ON_COMMIT')
        }
    
    def get_backup_config(self) -> Dict:
        """获取备份配置"""
        return {
            'auto_backup_enabled': self.is_rule_enabled('AUTO_BACKUP_ENABLED'),
            'backup_interval': int(self.get_rule('BACKUP_INTERVAL') or 3600),
            'retention_days': int(self.get_rule('BACKUP_RETENTION_DAYS') or 7),
            'max_count': int(self.get_rule('BACKUP_MAX_COUNT') or 30),
            'backup_on_shutdown': self.is_rule_enabled('BACKUP_ON_SHUTDOWN'),
            'backup_on_startup': self.is_rule_enabled('BACKUP_ON_STARTUP'),
            'compress_enabled': self.is_rule_enabled('BACKUP_COMPRESS_ENABLED'),
            'encrypt_enabled': self.is_rule_enabled('BACKUP_ENCRYPT_ENABLED'),
            'backup_path': self.get_rule('BACKUP_PATH') or './backups',
            'include_logs': self.is_rule_enabled('BACKUP_INCLUDE_LOGS'),
            'incremental_enabled': self.is_rule_enabled('INCREMENTAL_BACKUP_ENABLED'),
            'incremental_interval': int(self.get_rule('INCREMENTAL_BACKUP_INTERVAL') or 600),
            'full_backup_interval': int(self.get_rule('INCREMENTAL_BACKUP_FULL_INTERVAL') or 86400)
        }
    
    def get_shadow_node_config(self) -> Dict:
        """获取影子节点配置"""
        return {
            'enabled': self.is_rule_enabled('SHADOW_NODE_ENABLED'),
            'node_count': int(self.get_rule('SHADOW_NODE_COUNT') or 2),
            'sync_interval': int(self.get_rule('SHADOW_NODE_SYNC_INTERVAL') or 60),
            'failover_enabled': self.is_rule_enabled('SHADOW_NODE_FAILOVER_ENABLED'),
            'health_check_interval': int(self.get_rule('SHADOW_NODE_HEALTH_CHECK_INTERVAL') or 10)
        }
    
    def get_replication_config(self) -> Dict:
        """获取副本配置"""
        return {
            'enabled': self.is_rule_enabled('DATA_REPLICATION_ENABLED'),
            'replication_factor': int(self.get_rule('REPLICATION_FACTOR') or 3),
            'sync_mode': self.get_rule('REPLICATION_SYNC_MODE') or 'synchronous',
            'consistency': self.get_rule('REPLICATION_CONSISTENCY') or 'strong'
        }
    
    def get_checkpoint_config(self) -> Dict:
        """获取记录点配置"""
        return {
            'enabled': self.is_rule_enabled('CHECKPOINT_ENABLED'),
            'interval': int(self.get_rule('CHECKPOINT_INTERVAL') or 300),
            'on_operation': self.is_rule_enabled('CHECKPOINT_ON_OPERATION'),
            'retention': int(self.get_rule('CHECKPOINT_RETENTION') or 50),
            'compress_enabled': self.is_rule_enabled('CHECKPOINT_COMPRESS_ENABLED')
        }
    
    def get_operation_log_config(self) -> Dict:
        """获取操作日志配置"""
        return {
            'enabled': self.is_rule_enabled('OPERATION_LOG_ENABLED'),
            'to_database': self.is_rule_enabled('OPERATION_LOG_TO_DATABASE'),
            'to_file': self.is_rule_enabled('OPERATION_LOG_TO_FILE'),
            'log_level': self.get_rule('OPERATION_LOG_LEVEL') or 'INFO',
            'retention_days': int(self.get_rule('OPERATION_LOG_RETENTION_DAYS') or 30),
            'max_size': int(self.get_rule('OPERATION_LOG_MAX_SIZE') or 104857600)
        }
    
    def get_history_data_config(self) -> Dict:
        """获取历史数据配置"""
        return {
            'enabled': self.is_rule_enabled('HISTORY_DATA_ENABLED'),
            'retention_days': int(self.get_rule('HISTORY_DATA_RETENTION_DAYS') or 90),
            'compress_enabled': self.is_rule_enabled('HISTORY_DATA_COMPRESS_ENABLED'),
            'archive_enabled': self.is_rule_enabled('HISTORY_DATA_ARCHIVE_ENABLED'),
            'archive_interval': int(self.get_rule('HISTORY_DATA_ARCHIVE_INTERVAL') or 86400)
        }
    
    def get_gray_release_config(self) -> Dict:
        """获取灰度发布配置"""
        return {
            'enabled': self.is_rule_enabled('GRAY_RELEASE_ENABLED'),
            'percentage': int(self.get_rule('GRAY_RELEASE_PERCENTAGE') or 10),
            'user_list': self.get_rule('GRAY_RELEASE_USER_LIST') or '',
            'rollback_on_error': self.is_rule_enabled('GRAY_RELEASE_ROLLBACK_ON_ERROR'),
            'error_threshold': int(self.get_rule('GRAY_RELEASE_ERROR_THRESHOLD') or 5),
            'gradual_enabled': self.is_rule_enabled('GRAY_RELEASE_GRADUAL_ENABLED'),
            'gradual_steps': int(self.get_rule('GRAY_RELEASE_GRADUAL_STEPS') or 5),
            'gradual_interval': int(self.get_rule('GRAY_RELEASE_GRADUAL_INTERVAL') or 3600),
            'monitor_enabled': self.is_rule_enabled('GRAY_RELEASE_MONITOR_ENABLED')
        }
    
    def get_auto_incremental_config(self) -> Dict:
        """获取自动增量配置"""
        return {
            'enabled': self.is_rule_enabled('AUTO_INCREMENTAL_ENABLED'),
            'check_interval': int(self.get_rule('AUTO_INCREMENTAL_CHECK_INTERVAL') or 300),
            'apply_on_detect': self.is_rule_enabled('AUTO_INCREMENTAL_APPLY_ON_DETECT'),
            'backup_before': self.is_rule_enabled('AUTO_INCREMENTAL_BACKUP_BEFORE')
        }

system_rules_extension = SystemRulesExtension()
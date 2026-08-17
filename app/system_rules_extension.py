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

        # ==================== 升级：API访问控制规则 ====================
        ('API_RATE_LIMIT_ENABLED', 'API限流启用', '1', 'api_security', '是否启用API级别限流', 1),
        ('API_GLOBAL_RATE_LIMIT', 'API全局速率', '300', 'api_security', '单IP对/api/路径每分钟最大请求数', 1),
        ('API_AUTH_RATE_LIMIT', '认证API速率', '10', 'api_security', '认证相关API每分钟最大请求数', 1),
        ('API_WRITE_RATE_LIMIT', '写操作API速率', '60', 'api_security', 'POST/PUT/DELETE每分钟最大请求数', 1),
        ('API_READ_RATE_LIMIT', '读操作API速率', '600', 'api_security', 'GET每分钟最大请求数', 1),
        ('API_ADMIN_RATE_LIMIT', '管理API速率', '120', 'api_security', '管理接口每分钟最大请求数', 1),
        ('API_SENSITIVE_RATE_LIMIT', '敏感API速率', '30', 'api_security', '用户管理/权限管理/系统配置每分钟最大请求数', 1),
        ('API_BURST_LIMIT', 'API突发限制', '50', 'api_security', '1秒内最大请求数（防突发）', 1),
        ('API_CONCURRENT_LIMIT', 'API并发限制', '10', 'api_security', '单用户最大并发请求数', 1),
        ('API_TIMEOUT', 'API超时(秒)', '30', 'api_security', 'API请求超时时间(秒)', 1),
        ('API_UPLOAD_MAX_SIZE', '上传最大大小(MB)', '10', 'api_security', 'API上传文件最大大小(MB)', 1),
        ('API_ALLOWED_ORIGINS', '允许的CORS来源', '*', 'api_security', '逗号分隔的允许来源(*=全部)', 1),
        ('API_LOG_SENSITIVE_PARAMS', '记录敏感参数', '0', 'api_security', '是否在日志中记录敏感参数(0=脱敏,1=记录)', 1),

        # ==================== 升级：数据脱敏规则 ====================
        ('DATA_MASKING_ENABLED', '数据脱敏启用', '1', 'data_masking', '是否启用响应数据脱敏', 1),
        ('DATA_MASK_PHONE', '手机号脱敏', '1', 'data_masking', '手机号中间4位脱敏 (138****1234)', 1),
        ('DATA_MASK_EMAIL', '邮箱脱敏', '1', 'data_masking', '邮箱用户名部分脱敏 (z***@example.com)', 1),
        ('DATA_MASK_ID_CARD', '身份证脱敏', '1', 'data_masking', '身份证中间8位脱敏', 1),
        ('DATA_MASK_BANK_CARD', '银行卡脱敏', '1', 'data_masking', '银行卡号仅显示后4位', 1),
        ('DATA_MASK_IP_ADDRESS', 'IP地址脱敏', '0', 'data_masking', 'IP地址最后一段脱敏 (192.168.1.***)', 1),
        ('DATA_MASK_USERNAME_IN_LOG', '日志用户名脱敏', '1', 'data_masking', '日志中用户名部分脱敏', 1),
        ('DATA_MASK_PASSWORD_IN_RESPONSE', '响应密码脱敏', '1', 'data_masking', 'API响应中绝不含密码字段(强制)', 1),
        ('DATA_MASK_TOKEN_IN_LOG', '日志Token脱敏', '1', 'data_masking', '日志中Token/密钥仅显示前4后4位', 1),

        # ==================== 升级：审计增强规则 ====================
        ('AUDIT_ENABLE_DETAILED', '详细审计启用', '1', 'audit', '是否记录详细操作审计日志(含请求参数)', 1),
        ('AUDIT_LOG_SENSITIVE_OPS', '敏感操作审计', '1', 'audit', '记录删除/修改权限/导出等敏感操作', 1),
        ('AUDIT_LOG_FAILED_ACCESS', '失败访问审计', '1', 'audit', '记录所有失败的权限检查和登录尝试', 1),
        ('AUDIT_LOG_DATA_EXPORT', '数据导出审计', '1', 'audit', '记录所有数据导出/批量查询操作', 1),
        ('AUDIT_LOG_CONFIG_CHANGE', '配置变更审计', '1', 'audit', '记录所有系统配置变更', 1),
        ('AUDIT_LOG_USER_MGMT', '用户管理审计', '1', 'audit', '记录用户创建/删除/角色变更', 1),
        ('AUDIT_LOG_API_KEY_USE', 'API Key使用审计', '1', 'audit', '记录API Key的使用记录', 1),
        ('AUDIT_REALTIME_ALERT', '实时告警启用', '1', 'audit', '高危操作实时推送给超级管理员', 1),
        ('AUDIT_ALERT_SEVERITY_THRESHOLD', '告警级别阈值', 'high', 'audit', '触发实时告警的最低严重级别', 1),
        ('AUDIT_RETENTION_DAYS_DETAILED', '详细审计保留天数', '180', 'audit', '详细审计日志保留天数', 1),
        ('AUDIT_LOG_INTEGRITY_CHECK', '审计完整性校验', '1', 'audit', '定期校验审计日志是否被篡改', 1),
        ('AUDIT_LOG_HASH_CHAIN', '审计哈希链', '1', 'audit', '使用哈希链保证审计日志不可篡改', 1),

        # ==================== 升级：权限矩阵规则 ====================
        ('PERMISSION_MATRIX_ENABLED', '权限矩阵启用', '1', 'permission', '是否启用路径-角色权限矩阵', 1),
        ('PERMISSION_STRICT_MODE', '权限严格模式', '0', 'permission', '严格模式下未匹配路径默认拒绝(0=允许,1=拒绝)', 1),
        ('PERMISSION_CACHE_TTL', '权限缓存TTL', '300', 'permission', '权限检查结果缓存时间(秒)', 1),
        ('PERMISSION_INHERIT_PARENT', '权限继承父级', '1', 'permission', '子路径继承父路径的权限约束', 1),
        ('PERMISSION_SUPER_ADMIN_BYPASS', 'SA权限绕过', '1', 'permission', '超级管理员是否绕过所有权限检查', 1),
        ('PERMISSION_GUEST_ALLOWED_PATHS', '游客允许路径', '/,/,/auth/login,/auth/register,/auth/forgot_password,/api/health,/api/time,/api/status', 'permission', '游客可访问的路径(逗号分隔)', 1),
        ('PERMISSION_API_TOKEN_AUTH', 'API Token认证启用', '1', 'permission', '是否支持API Token认证(替代session)', 1),
        ('PERMISSION_TOKEN_EXPIRE', 'Token过期时间', '3600', 'permission', 'API Token过期时间(秒)', 1),
        ('PERMISSION_TOKEN_REFRESH_WINDOW', 'Token刷新窗口', '300', 'permission', 'Token可自动刷新的时间窗口(秒)', 1),
        ('PERMISSION_MAX_TOKENS_PER_USER', '每用户最大Token数', '5', 'permission', '每用户最多可创建的API Token数量', 1),

        # ==================== 升级：安全增强规则 ====================
        ('SECURITY_CSRF_ENABLED', 'CSRF防护启用', '1', 'security', '是否启用CSRF Token验证', 1),
        ('SECURITY_CSRF_TOKEN_ROTATE', 'CSRF Token轮换', '0', 'security', '是否每次请求后轮换CSRF Token', 1),
        ('SECURITY_CSRF_COOKIE_HTTPONLY', 'CSRF Cookie HttpOnly', '1', 'security', 'CSRF Cookie 是否设置 HttpOnly', 1),
        ('SECURITY_CSRF_COOKIE_SAMESITE', 'CSRF Cookie SameSite', 'Lax', 'security', 'CSRF Cookie SameSite 策略(Lax/Strict/None)', 1),
        ('SECURITY_REQUEST_BODY_MAX', '请求体最大大小(MB)', '10', 'security', '请求体最大允许大小(MB)', 1),
        ('SECURITY_QUERY_STRING_MAX', '查询字符串最大长度', '2048', 'security', 'URL查询字符串最大长度', 1),
        ('SECURITY_CONCURRENT_LOGIN_IPS', '并发登录IP数', '2', 'security', '同用户最多同时在线的不同IP数', 1),
        ('SECURITY_PASSWORD_MIN_LENGTH', '密码最小长度', '6', 'security', '密码最小长度要求', 1),
        ('SECURITY_PASSWORD_REQUIRE_UPPER', '密码需大写字母', '0', 'security', '密码是否必须包含大写字母', 1),
        ('SECURITY_PASSWORD_REQUIRE_LOWER', '密码需小写字母', '0', 'security', '密码是否必须包含小写字母', 1),
        ('SECURITY_PASSWORD_REQUIRE_DIGIT', '密码需数字', '0', 'security', '密码是否必须包含数字', 1),
        ('SECURITY_PASSWORD_REQUIRE_SPECIAL', '密码需特殊字符', '0', 'security', '密码是否必须包含特殊字符', 1),
        ('SECURITY_PASSWORD_HISTORY_CHECK', '密码历史检查', '0', 'security', '修改密码时是否检查历史密码', 1),
        ('SECURITY_PASSWORD_HISTORY_COUNT', '密码历史数量', '5', 'security', '保留的密码历史数量(防止重复使用)', 1),
        ('SECURITY_2FA_ENABLED', '双因素认证启用', '0', 'security', '是否启用双因素认证(0=可选,1=强制)', 1),
        ('SECURITY_2FA_REQUIRED_ROLES', '2FA强制角色', 'super_admin', 'security', '必须启用2FA的角色(逗号分隔)', 1),
        ('SECURITY_SESSION_FINGERPRINT', '会话指纹绑定', '1', 'security', '会话绑定IP+UA指纹(防会话劫持)', 1),
        ('SECURITY_SESSION_REGENERATE_ON_LOGIN', '登录时重生成SessionID', '1', 'security', '登录成功后是否重新生成SessionID(防固定会话)', 1),
        ('SECURITY_SECURITY_HEADERS', '安全响应头启用', '1', 'security', '是否添加安全响应头(X-Frame-Options等)', 1),
        ('SECURITY_HSTS_MAX_AGE', 'HSTS最大时长', '31536000', 'security', 'HSTS Strict-Transport-Security 最大时长(秒)', 1),
        ('SECURITY_HSTS_INCLUDE_SUBDOMAINS', 'HSTS含子域名', '1', 'security', 'HSTS 是否包含子域名', 1),
        ('SECURITY_CSP_POLICY', 'CSP策略', "default-src 'self'", 'security', 'Content-Security-Policy 响应头值', 1),
        ('SECURITY_X_FRAME_OPTIONS', 'X-Frame-Options', 'DENY', 'security', 'X-Frame-Options 响应头值(DENY/SAMEORIGIN)', 1),
        ('SECURITY_X_CONTENT_TYPE_OPTIONS', 'X-Content-Type-Options', 'nosniff', 'security', 'X-Content-Type-Options 响应头值', 1),
        ('SECURITY_X_XSS_PROTECTION', 'X-XSS-Protection', '1; mode=block', 'security', 'X-XSS-Protection 响应头值', 1),
        ('SECURITY_REFERRER_POLICY', 'Referrer-Policy', 'strict-origin-when-cross-origin', 'security', 'Referrer-Policy 响应头值', 1),
        ('SECURITY_PERMISSIONS_POLICY', 'Permissions-Policy', 'geolocation=(),camera=(),microphone=()', 'security', 'Permissions-Policy 响应头值', 1),

        # ==================== 升级：内容安全规则 ====================
        ('CONTENT_SECURITY_SCAN_ENABLED', '内容安全扫描启用', '1', 'content_security', '是否对用户输入内容进行安全扫描', 1),
        ('CONTENT_MAX_LENGTH', '内容最大长度', '10000', 'content_security', '单次提交内容最大字符数', 1),
        ('CONTENT_FILTER_PROFANITY', '脏话过滤', '1', 'content_security', '是否过滤脏话和不当内容', 1),
        ('CONTENT_FILTER_PERSONAL_INFO', '个人信息过滤', '1', 'content_security', '是否过滤手机号/身份证等个人信息', 1),
        ('CONTENT_FILTER_HTML', 'HTML过滤', '1', 'content_security', '是否过滤HTML标签(防XSS)', 1),
        ('CONTENT_FILTER_SQL', 'SQL关键字过滤', '1', 'content_security', '是否过滤SQL注入关键字', 1),
        ('CONTENT_QUARANTINE_ENABLED', '内容隔离启用', '1', 'content_security', '可疑内容是否隔离待审而非直接拒绝', 1),
        ('CONTENT_QUARANTINE_RETENTION', '隔离内容保留天数', '30', 'content_security', '隔离内容保留天数', 1),

        # ==================== 升级：系统监控规则 ====================
        ('MONITOR_ENABLED', '系统监控启用', '1', 'monitor', '是否启用系统监控', 1),
        ('MONITOR_CPU_THRESHOLD', 'CPU告警阈值', '80', 'monitor', 'CPU使用率告警阈值(%)', 1),
        ('MONITOR_MEMORY_THRESHOLD', '内存告警阈值', '85', 'monitor', '内存使用率告警阈值(%)', 1),
        ('MONITOR_DISK_THRESHOLD', '磁盘告警阈值', '90', 'monitor', '磁盘使用率告警阈值(%)', 1),
        ('MONITOR_RESPONSE_TIME_THRESHOLD', '响应时间告警阈值', '5000', 'monitor', 'API响应时间告警阈值(毫秒)', 1),
        ('MONITOR_ERROR_RATE_THRESHOLD', '错误率告警阈值', '5', 'monitor', '错误率告警阈值(%)', 1),
        ('MONITOR_INTERVAL', '监控采集间隔', '60', 'monitor', '监控数据采集间隔(秒)', 1),
        ('MONITOR_ALERT_ENABLED', '告警启用', '1', 'monitor', '是否启用告警通知', 1),
        ('MONITOR_ALERT_METHOD', '告警方式', 'log', 'monitor', '告警通知方式(log/email/webhook)', 1),
        ('MONITOR_AUTO_RESTART', '自动重启', '0', 'monitor', '服务异常时是否自动重启', 1),
        ('MONITOR_HEALTH_CHECK_PATHS', '健康检查路径', '/api/health,/api/monitoring/health', 'monitor', '健康检查路径(逗号分隔)', 1),

        # ==================== 数据真实性规则 ====================
        ('NO_FAKE_DATA_ENABLED', '禁止假数据启用', '1', 'data_integrity', '所有页面禁止使用假数据/模拟数据，必须使用数据库真实查询', 1),
        ('NO_MOCK_DATA_ALLOWED', '禁止Mock数据', '1', 'data_integrity', 'API接口禁止返回mock/fake/simulated数据，数据不可用时返回错误', 1),
        ('NO_HARDCODED_STATS', '禁止硬编码统计', '1', 'data_integrity', '统计数据必须从数据库查询，禁止使用硬编码数字作为初始值或fallback', 1),
        ('DB_QUERY_FAILURE_POLICY', '数据库查询失败策略', 'return_zero', 'data_integrity', '数据库查询失败时返回0/空值，不允许返回假数据', 1),
        ('FAKE_DATA_AUDIT_ENABLED', '假数据审计启用', '1', 'data_integrity', '自动审计代码中是否存在假数据模式', 1),
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

    # ===== 升级：新增规则配置获取方法 =====

    def get_api_security_config(self) -> Dict:
        """获取API安全配置"""
        return {
            'rate_limit_enabled': self.is_rule_enabled('API_RATE_LIMIT_ENABLED'),
            'global_rate_limit': int(self.get_rule('API_GLOBAL_RATE_LIMIT') or 300),
            'auth_rate_limit': int(self.get_rule('API_AUTH_RATE_LIMIT') or 10),
            'write_rate_limit': int(self.get_rule('API_WRITE_RATE_LIMIT') or 60),
            'read_rate_limit': int(self.get_rule('API_READ_RATE_LIMIT') or 600),
            'admin_rate_limit': int(self.get_rule('API_ADMIN_RATE_LIMIT') or 120),
            'sensitive_rate_limit': int(self.get_rule('API_SENSITIVE_RATE_LIMIT') or 30),
            'burst_limit': int(self.get_rule('API_BURST_LIMIT') or 50),
            'concurrent_limit': int(self.get_rule('API_CONCURRENT_LIMIT') or 10),
            'timeout': int(self.get_rule('API_TIMEOUT') or 30),
            'upload_max_size_mb': int(self.get_rule('API_UPLOAD_MAX_SIZE') or 10),
            'allowed_origins': self.get_rule('API_ALLOWED_ORIGINS') or '*',
            'log_sensitive_params': self.is_rule_enabled('API_LOG_SENSITIVE_PARAMS'),
        }

    def get_data_masking_config(self) -> Dict:
        """获取数据脱敏配置"""
        return {
            'enabled': self.is_rule_enabled('DATA_MASKING_ENABLED'),
            'mask_phone': self.is_rule_enabled('DATA_MASK_PHONE'),
            'mask_email': self.is_rule_enabled('DATA_MASK_EMAIL'),
            'mask_id_card': self.is_rule_enabled('DATA_MASK_ID_CARD'),
            'mask_bank_card': self.is_rule_enabled('DATA_MASK_BANK_CARD'),
            'mask_ip': self.is_rule_enabled('DATA_MASK_IP_ADDRESS'),
            'mask_username_in_log': self.is_rule_enabled('DATA_MASK_USERNAME_IN_LOG'),
            'mask_password_in_response': self.is_rule_enabled('DATA_MASK_PASSWORD_IN_RESPONSE'),
            'mask_token_in_log': self.is_rule_enabled('DATA_MASK_TOKEN_IN_LOG'),
        }

    def get_audit_config(self) -> Dict:
        """获取审计配置"""
        return {
            'detailed_enabled': self.is_rule_enabled('AUDIT_ENABLE_DETAILED'),
            'log_sensitive_ops': self.is_rule_enabled('AUDIT_LOG_SENSITIVE_OPS'),
            'log_failed_access': self.is_rule_enabled('AUDIT_LOG_FAILED_ACCESS'),
            'log_data_export': self.is_rule_enabled('AUDIT_LOG_DATA_EXPORT'),
            'log_config_change': self.is_rule_enabled('AUDIT_LOG_CONFIG_CHANGE'),
            'log_user_mgmt': self.is_rule_enabled('AUDIT_LOG_USER_MGMT'),
            'log_api_key_use': self.is_rule_enabled('AUDIT_LOG_API_KEY_USE'),
            'realtime_alert': self.is_rule_enabled('AUDIT_REALTIME_ALERT'),
            'alert_severity_threshold': self.get_rule('AUDIT_ALERT_SEVERITY_THRESHOLD') or 'high',
            'retention_days_detailed': int(self.get_rule('AUDIT_RETENTION_DAYS_DETAILED') or 180),
            'integrity_check': self.is_rule_enabled('AUDIT_LOG_INTEGRITY_CHECK'),
            'hash_chain': self.is_rule_enabled('AUDIT_LOG_HASH_CHAIN'),
        }

    def get_permission_config(self) -> Dict:
        """获取权限矩阵配置"""
        return {
            'matrix_enabled': self.is_rule_enabled('PERMISSION_MATRIX_ENABLED'),
            'strict_mode': self.is_rule_enabled('PERMISSION_STRICT_MODE'),
            'cache_ttl': int(self.get_rule('PERMISSION_CACHE_TTL') or 300),
            'inherit_parent': self.is_rule_enabled('PERMISSION_INHERIT_PARENT'),
            'sa_bypass': self.is_rule_enabled('PERMISSION_SUPER_ADMIN_BYPASS'),
            'guest_allowed_paths': self.get_rule('PERMISSION_GUEST_ALLOWED_PATHS') or '',
            'api_token_auth': self.is_rule_enabled('PERMISSION_API_TOKEN_AUTH'),
            'token_expire': int(self.get_rule('PERMISSION_TOKEN_EXPIRE') or 3600),
            'token_refresh_window': int(self.get_rule('PERMISSION_TOKEN_REFRESH_WINDOW') or 300),
            'max_tokens_per_user': int(self.get_rule('PERMISSION_MAX_TOKENS_PER_USER') or 5),
        }

    def get_security_headers_config(self) -> Dict:
        """获取安全响应头配置"""
        return {
            'enabled': self.is_rule_enabled('SECURITY_SECURITY_HEADERS'),
            'hsts_max_age': int(self.get_rule('SECURITY_HSTS_MAX_AGE') or 31536000),
            'hsts_include_subdomains': self.is_rule_enabled('SECURITY_HSTS_INCLUDE_SUBDOMAINS'),
            'csp_policy': self.get_rule('SECURITY_CSP_POLICY') or "default-src 'self'",
            'x_frame_options': self.get_rule('SECURITY_X_FRAME_OPTIONS') or 'DENY',
            'x_content_type_options': self.get_rule('SECURITY_X_CONTENT_TYPE_OPTIONS') or 'nosniff',
            'x_xss_protection': self.get_rule('SECURITY_X_XSS_PROTECTION') or '1; mode=block',
            'referrer_policy': self.get_rule('SECURITY_REFERRER_POLICY') or 'strict-origin-when-cross-origin',
            'permissions_policy': self.get_rule('SECURITY_PERMISSIONS_POLICY') or 'geolocation=(),camera=(),microphone=()',
        }

    def get_content_security_config(self) -> Dict:
        """获取内容安全配置"""
        return {
            'scan_enabled': self.is_rule_enabled('CONTENT_SECURITY_SCAN_ENABLED'),
            'max_length': int(self.get_rule('CONTENT_MAX_LENGTH') or 10000),
            'filter_profanity': self.is_rule_enabled('CONTENT_FILTER_PROFANITY'),
            'filter_personal_info': self.is_rule_enabled('CONTENT_FILTER_PERSONAL_INFO'),
            'filter_html': self.is_rule_enabled('CONTENT_FILTER_HTML'),
            'filter_sql': self.is_rule_enabled('CONTENT_FILTER_SQL'),
            'quarantine_enabled': self.is_rule_enabled('CONTENT_QUARANTINE_ENABLED'),
            'quarantine_retention': int(self.get_rule('CONTENT_QUARANTINE_RETENTION') or 30),
        }

    def get_monitor_config(self) -> Dict:
        """获取系统监控配置"""
        return {
            'enabled': self.is_rule_enabled('MONITOR_ENABLED'),
            'cpu_threshold': int(self.get_rule('MONITOR_CPU_THRESHOLD') or 80),
            'memory_threshold': int(self.get_rule('MONITOR_MEMORY_THRESHOLD') or 85),
            'disk_threshold': int(self.get_rule('MONITOR_DISK_THRESHOLD') or 90),
            'response_time_threshold': int(self.get_rule('MONITOR_RESPONSE_TIME_THRESHOLD') or 5000),
            'error_rate_threshold': int(self.get_rule('MONITOR_ERROR_RATE_THRESHOLD') or 5),
            'interval': int(self.get_rule('MONITOR_INTERVAL') or 60),
            'alert_enabled': self.is_rule_enabled('MONITOR_ALERT_ENABLED'),
            'alert_method': self.get_rule('MONITOR_ALERT_METHOD') or 'log',
            'auto_restart': self.is_rule_enabled('MONITOR_AUTO_RESTART'),
            'health_check_paths': self.get_rule('MONITOR_HEALTH_CHECK_PATHS') or '/api/health,/api/monitoring/health',
        }

system_rules_extension = SystemRulesExtension()
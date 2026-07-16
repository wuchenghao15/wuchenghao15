#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def create_system_rules_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT NOT NULL UNIQUE,
                rule_name TEXT NOT NULL,
                rule_value TEXT,
                rule_type TEXT DEFAULT 'system',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_maintenance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                target TEXT NOT NULL,
                result TEXT NOT NULL,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permission_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                target TEXT NOT NULL,
                operator TEXT NOT NULL,
                role TEXT,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_fix_code_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fix_id TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                original_code TEXT NOT NULL,
                fixed_code TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT,
                fix_strategy TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                executed_by TEXT NOT NULL,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pending',
                rollback_available INTEGER DEFAULT 1,
                rollback_code TEXT,
                validation_result TEXT,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resident_service_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT UNIQUE NOT NULL,
                service_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                status TEXT DEFAULT 'stopped',
                is_running INTEGER DEFAULT 0,
                pid INTEGER,
                start_time TEXT,
                last_heartbeat TEXT,
                last_status_change TEXT,
                restart_count INTEGER DEFAULT 0,
                max_restart_count INTEGER DEFAULT 5,
                health_score REAL DEFAULT 100.0,
                error_message TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sandbox_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sandbox_id TEXT UNIQUE NOT NULL,
                instance_id TEXT NOT NULL,
                status TEXT DEFAULT 'created',
                isolation_level TEXT DEFAULT 'medium',
                resource_limits TEXT,
                file_system_access INTEGER DEFAULT 1,
                network_isolation INTEGER DEFAULT 1,
                clipboard_access INTEGER DEFAULT 0,
                gpu_access INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                stopped_at TEXT,
                last_health_check TEXT,
                health_score REAL DEFAULT 100.0,
                error_message TEXT,
                prewarmed INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                metadata TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_port_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                protocol TEXT DEFAULT 'tcp',
                external_port INTEGER NOT NULL,
                internal_port INTEGER NOT NULL,
                internal_ip TEXT DEFAULT '127.0.0.1',
                rule_type TEXT DEFAULT 'dnat',
                comment TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_firewall_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                chain TEXT DEFAULT 'INPUT',
                protocol TEXT DEFAULT 'tcp',
                src_ip TEXT,
                dst_ip TEXT,
                src_port INTEGER,
                dst_port INTEGER,
                action TEXT DEFAULT 'ACCEPT',
                comment TEXT,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 100,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protocol_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol_id TEXT UNIQUE NOT NULL,
                protocol_name TEXT NOT NULL,
                protocol_type TEXT NOT NULL,
                protocol_version TEXT DEFAULT '1.0',
                connection_type TEXT DEFAULT 'tcp',
                default_port INTEGER,
                encoding TEXT DEFAULT 'utf-8',
                timeout INTEGER DEFAULT 300,
                max_connections INTEGER DEFAULT 1000,
                retry_count INTEGER DEFAULT 3,
                keep_alive_enabled INTEGER DEFAULT 1,
                compression_enabled INTEGER DEFAULT 0,
                encryption_enabled INTEGER DEFAULT 1,
                certificate_path TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protocol_endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id TEXT UNIQUE NOT NULL,
                protocol_id TEXT NOT NULL,
                endpoint_name TEXT NOT NULL,
                endpoint_type TEXT DEFAULT 'rest',
                url TEXT NOT NULL,
                method TEXT DEFAULT 'GET',
                auth_required INTEGER DEFAULT 1,
                rate_limit INTEGER DEFAULT 100,
                rate_limit_window TEXT DEFAULT '1minute',
                timeout INTEGER DEFAULT 30,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS port_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                port_id TEXT UNIQUE NOT NULL,
                port_name TEXT NOT NULL,
                port_number INTEGER NOT NULL,
                protocol TEXT DEFAULT 'tcp',
                service_name TEXT,
                binding_ip TEXT DEFAULT '0.0.0.0',
                allowed_ips TEXT,
                blocked_ips TEXT,
                rate_limit INTEGER DEFAULT 0,
                rate_limit_window TEXT DEFAULT '1minute',
                connection_limit INTEGER DEFAULT 0,
                timeout INTEGER DEFAULT 0,
                tls_enabled INTEGER DEFAULT 0,
                tls_certificate_path TEXT,
                enabled INTEGER DEFAULT 1,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS port_mapping_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mapping_id TEXT UNIQUE NOT NULL,
                mapping_name TEXT NOT NULL,
                external_port INTEGER NOT NULL,
                internal_port INTEGER NOT NULL,
                internal_ip TEXT DEFAULT '127.0.0.1',
                protocol TEXT DEFAULT 'tcp',
                enabled INTEGER DEFAULT 1,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                document_name TEXT NOT NULL,
                document_type TEXT DEFAULT 'markdown',
                document_category TEXT DEFAULT 'system',
                document_path TEXT,
                document_content TEXT,
                version TEXT DEFAULT '1.0',
                author TEXT,
                status TEXT DEFAULT 'draft',
                publish_date TEXT,
                expiry_date TEXT,
                access_level TEXT DEFAULT 'public',
                tags TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                version TEXT NOT NULL,
                version_number INTEGER DEFAULT 1,
                change_log TEXT,
                content_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frontend_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                rule_category TEXT DEFAULT 'spacing',
                rule_property TEXT NOT NULL,
                rule_value TEXT NOT NULL,
                rule_unit TEXT DEFAULT 'px',
                description TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frontend_component_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id TEXT UNIQUE NOT NULL,
                component_name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                border_radius TEXT DEFAULT '8px',
                padding TEXT DEFAULT '12px 16px',
                margin TEXT DEFAULT '0',
                opacity TEXT DEFAULT '1',
                font_size TEXT DEFAULT '14px',
                text_align TEXT DEFAULT 'left',
                line_height TEXT DEFAULT '1.5',
                background_color TEXT DEFAULT '#ffffff',
                text_color TEXT DEFAULT '#333333',
                border_color TEXT DEFAULT '#e0e0e0',
                shadow TEXT DEFAULT 'none',
                enabled INTEGER DEFAULT 1,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialog_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dialog_id TEXT UNIQUE NOT NULL,
                dialog_name TEXT NOT NULL,
                dialog_type TEXT DEFAULT 'modal',
                dialog_title TEXT,
                dialog_content TEXT,
                dialog_size TEXT DEFAULT 'medium',
                show_header INTEGER DEFAULT 1,
                show_footer INTEGER DEFAULT 1,
                show_close_button INTEGER DEFAULT 1,
                show_confirm_button INTEGER DEFAULT 1,
                confirm_button_text TEXT DEFAULT '确定',
                cancel_button_text TEXT DEFAULT '取消',
                auto_close INTEGER DEFAULT 0,
                auto_close_delay INTEGER DEFAULT 3000,
                backdrop INTEGER DEFAULT 1,
                keyboard INTEGER DEFAULT 1,
                draggable INTEGER DEFAULT 0,
                resizable INTEGER DEFAULT 0,
                position TEXT DEFAULT 'center',
                animation_enabled INTEGER DEFAULT 1,
                animation_type TEXT DEFAULT 'fade',
                enabled INTEGER DEFAULT 1,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialog_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                document_name TEXT NOT NULL,
                document_type TEXT DEFAULT 'welcome',
                dialog_id TEXT,
                content TEXT,
                version TEXT DEFAULT '1.0',
                language TEXT DEFAULT 'zh-CN',
                target_users TEXT DEFAULT 'all',
                display_condition TEXT,
                display_order INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM system_rules')
        total_count = cursor.fetchone()[0]
        
        default_rules = [
            ('SYS_VERSION', '系统版本', '10.0.0', 'system', '当前系统版本号', 1),
            ('SYS_NAME', '系统名称', 'MTSCOS AI', 'system', '系统显示名称', 1),
            ('MAX_UPLOAD_SIZE', '最大上传大小', '52428800', 'system', '文件上传最大限制(字节)', 1),
            ('SESSION_TIMEOUT', '会话超时时间', '3600', 'system', '用户会话超时时间(秒)', 1),
            ('AI_ENABLED', 'AI功能启用', '1', 'system', '是否启用AI功能', 1),
            ('LOG_LEVEL', '日志级别', 'INFO', 'system', '系统日志级别', 1),
            ('DEBUG_MODE', '调试模式', '0', 'system', '是否启用调试模式', 0),
            ('MAINTENANCE_MODE', '维护模式', '0', 'system', '系统维护模式', 0),
            ('ALLOW_REGISTRATION', '允许注册', '1', 'system', '是否允许用户注册', 1),
            ('EMAIL_NOTIFICATION', '邮件通知', '1', 'system', '是否启用邮件通知', 1),
            ('MAX_LOGIN_ATTEMPTS', '最大登录尝试次数', '5', 'security', '允许的最大登录尝试次数', 1),
            ('LOCKOUT_DURATION', '账户锁定时长', '900', 'security', '账户锁定时长(秒)', 1),
            ('PASSWORD_MIN_LENGTH', '密码最小长度', '8', 'security', '密码最小长度', 1),
            ('PASSWORD_COMPLEXITY', '密码复杂度', '1', 'security', '是否启用密码复杂度要求', 1),
            ('EXAM_MAX_DURATION', '考试最大时长', '7200', 'exam', '考试最大时长(秒)', 1),
            ('EXAM_AUTO_SUBMIT', '考试自动提交', '1', 'exam', '超时是否自动提交', 1),
            ('GRADING_AUTO', '自动批改', '1', 'exam', '是否启用自动批改', 1),
            ('LEARNING_PATH_ENABLED', '学习路径启用', '1', 'learning', '是否启用智能学习路径', 1),
            ('RECOMMENDATION_ENABLED', '推荐功能启用', '1', 'learning', '是否启用智能推荐', 1),
            ('WARNING_SYSTEM_ENABLED', '预警系统启用', '1', 'learning', '是否启用学习预警系统', 1),
            
            ('MAINT_EMPLOYEE_STATUS_CHECK', 'AI员工状态检查频率', '1800', 'maintenance', 'AI员工状态检查间隔(秒)', 1),
            ('MAINT_EMPLOYEE_LEARNING_TRIGGER', 'AI员工学习触发频率', '7200', 'maintenance', 'AI员工学习触发间隔(秒)', 1),
            ('MAINT_EMPLOYEE_PERFORMANCE_EVAL', 'AI员工性能评估频率', '86400', 'maintenance', 'AI员工性能评估间隔(秒)', 1),
            ('MAINT_EMPLOYEE_LOG_CLEANUP', 'AI员工日志清理频率', '604800', 'maintenance', 'AI员工日志清理间隔(秒)', 1),
            ('MAINT_ENGINE_HEALTH_CHECK', 'AI引擎健康检查频率', '60', 'maintenance', 'AI引擎健康检查间隔(秒)', 1),
            ('MAINT_ENGINE_RESPONSE_TIME', 'AI引擎响应时间监控频率', '300', 'maintenance', 'AI引擎响应时间监控间隔(秒)', 1),
            ('MAINT_ENGINE_ERROR_RATE', 'AI引擎错误率监控频率', '600', 'maintenance', 'AI引擎错误率监控间隔(秒)', 1),
            ('MAINT_ENGINE_RESOURCE_USAGE', 'AI引擎资源使用监控频率', '1800', 'maintenance', 'AI引擎资源使用监控间隔(秒)', 1),
            ('MAINT_CLUSTER_ONLINE_RATE', 'AI集群员工在线率监控频率', '300', 'maintenance', 'AI集群员工在线率监控间隔(秒)', 1),
            ('MAINT_CLUSTER_TASK_SUCCESS_RATE', 'AI集群任务成功率监控频率', '600', 'maintenance', 'AI集群任务成功率监控间隔(秒)', 1),
            ('MAINT_CLUSTER_RESPONSE_TIME', 'AI集群响应时间监控频率', '900', 'maintenance', 'AI集群响应时间监控间隔(秒)', 1),
            ('MAINT_CLUSTER_RESOURCE_USAGE', 'AI集群资源使用率监控频率', '1800', 'maintenance', 'AI集群资源使用率监控间隔(秒)', 1),
            ('MAINT_ARRAY_NODE_ALIVE', 'AI阵列节点存活检测频率', '30', 'maintenance', 'AI阵列节点存活检测间隔(秒)', 1),
            ('MAINT_ARRAY_COMMUNICATION_DELAY', 'AI阵列通信延迟检测频率', '60', 'maintenance', 'AI阵列通信延迟检测间隔(秒)', 1),
            ('MAINT_ARRAY_LOAD_STATUS', 'AI阵列负载状态检测频率', '300', 'maintenance', 'AI阵列负载状态检测间隔(秒)', 1),
            ('MAINT_ARRAY_SYNC_STATUS', 'AI阵列同步状态检测频率', '600', 'maintenance', 'AI阵列同步状态检测间隔(秒)', 1),
            ('MAINT_GIT_SYNC_INTERVAL', 'Git自动同步频率', '1800', 'maintenance', 'Git自动同步间隔(秒)', 1),
            ('MAINT_DATABASE_BACKUP', '数据库备份频率', '86400', 'maintenance', '数据库备份间隔(秒)', 1),
            ('MAINT_LOG_CLEANUP', '系统日志清理频率', '604800', 'maintenance', '系统日志清理间隔(秒)', 1),
            ('MAINT_PERFORMANCE_REPORT', '性能报告生成频率', '2592000', 'maintenance', '性能报告生成间隔(秒)', 1),
            ('MAINT_AUTO_RECOVER_ENABLED', '自动恢复启用', '1', 'maintenance', '是否启用自动恢复功能', 1),
            ('MAINT_AUTO_REPAIR_ENABLED', '自动修复启用', '1', 'maintenance', '是否启用自动修复功能', 1),
            ('MAINT_PERFORMANCE_TUNING_ENABLED', '性能调优启用', '1', 'maintenance', '是否启用性能调优功能', 1),
            ('MAINT_AUDIT_LOG_ENABLED', '审计日志启用', '1', 'maintenance', '是否启用审计日志', 1),
            
            ('MAINT_VERSION_CHECK_INTERVAL', '版本号检查频率', '3600', 'maintenance', '版本号检查间隔(秒)', 1),
            ('MAINT_VERSION_AUTO_INCREMENT_ENABLED', '版本号自动递增启用', '1', 'maintenance', '是否启用版本号自动递增', 1),
            ('MAINT_VERSION_FORMAT', '版本号格式', 'major.minor.patch', 'maintenance', '版本号格式规范', 1),
            ('MAINT_VERSION_INCREMENT_ON_UPGRADE', '升级时版本递增', '1', 'maintenance', '升级成功后是否自动递增版本号', 1),
            ('MAINT_VERSION_INCREMENT_TYPE', '版本递增类型', 'patch', 'maintenance', '默认版本递增类型(major/minor/patch)', 1),
            ('MAINT_VERSION_HISTORY_ENABLED', '版本历史记录启用', '1', 'maintenance', '是否启用版本历史记录', 1),
            
            ('GRAY_RELEASE_ENABLED', '灰度发布启用', '1', 'maintenance', '是否启用灰度发布功能', 1),
            ('GRAY_RELEASE_PERCENTAGE', '灰度发布比例', '10', 'maintenance', '初始灰度发布用户比例(%)', 1),
            ('GRAY_HEALTH_CHECK_INTERVAL', '灰度健康检查间隔', '60', 'maintenance', '灰度环境健康检查间隔(秒)', 1),
            ('GRAY_HEALTH_CHECK_DURATION', '灰度健康检查持续时间', '300', 'maintenance', '灰度健康检查持续时间(秒)', 1),
            ('GRAY_AUTO_ROLLBACK_THRESHOLD', '灰度自动回滚阈值', '5', 'maintenance', '错误率超过此阈值自动回滚(%)', 1),
            ('GRAY_AUTO_ROLLBACK_LATENCY', '灰度自动回滚延迟阈值', '5000', 'maintenance', '响应时间超过此阈值自动回滚(毫秒)', 1),
            ('GRAY_DURATION', '灰度发布持续时间', '3600', 'maintenance', '单次灰度发布持续时间(秒)', 1),
            ('GRAY_PROMOTE_INTERVAL', '灰度放量间隔', '1800', 'maintenance', '灰度放量检查间隔(秒)', 1),
            ('GRAY_PROMOTE_STEPS', '灰度放量步骤', '10,30,50,70,100', 'maintenance', '灰度放量步骤百分比列表', 1),
            ('GRAY_ENVIRONMENT_URL', '灰度环境URL', '', 'maintenance', '灰度测试环境访问地址', 1),
            ('GRAY_NOTIFY_ADMIN_ENABLED', '灰度通知管理员', '1', 'maintenance', '灰度发布时是否通知管理员', 1),
            ('GRAY_ROLLBACK_ON_FAILURE', '失败时自动回滚', '1', 'maintenance', '灰度发布失败时是否自动回滚', 1),
            
            ('PERM_CHECK_INTERVAL', '权限检查间隔', '3600', 'maintenance', '权限缓存检查间隔(秒)', 1),
            ('PERM_CACHE_REFRESH_ENABLED', '权限缓存刷新启用', '1', 'maintenance', '是否启用权限缓存自动刷新', 1),
            ('PERM_ROLE_HIERARCHY_ENABLED', '角色层级启用', '1', 'maintenance', '是否启用角色层级继承', 1),
            ('PERM_AUDIT_ENABLED', '权限审计启用', '1', 'maintenance', '是否启用权限操作审计', 1),
            ('PERM_AUTO_SYNC_ENABLED', '权限自动同步启用', '1', 'maintenance', '是否启用权限规则自动同步', 1),
            ('PERM_EDUCATION_TYPE_FILTER_ENABLED', '教育类型权限过滤启用', '1', 'maintenance', '是否启用按教育类型过滤考试权限', 1),
            ('PERM_K12_RESTRICTION_ENABLED', 'K12权限限制启用', '1', 'maintenance', '是否启用K12学生考试权限限制', 1),
            ('PERM_HARDWARE_ADMIN_DEBUG_ENABLED', '硬件管理员调试权限启用', '1', 'maintenance', '是否启用硬件管理员调试环境权限', 1),
            ('PERM_MAX_LOGIN_ATTEMPTS', '最大登录尝试次数', '5', 'maintenance', '允许的最大登录尝试次数', 1),
            ('PERM_LOCKOUT_DURATION', '账户锁定时长', '900', 'maintenance', '账户锁定时长(秒)', 1),
            ('PERM_PASSWORD_MIN_LENGTH', '密码最小长度', '8', 'maintenance', '密码最小长度', 1),
            ('PERM_PASSWORD_COMPLEXITY_ENABLED', '密码复杂度启用', '1', 'maintenance', '是否启用密码复杂度要求', 1),
            ('PERM_SUPER_ADMIN_UNIQUE_USER', '超级管理员唯一用户', 'wuchenghao15', 'maintenance', '系统超级管理员唯一用户，有且仅有此用户拥有super_admin角色', 1),
            
            ('AUTOFIX_ENABLED', '自动修复启用', '1', 'maintenance', '是否启用自动修复功能', 1),
            ('AUTOFIX_CODE_BACKUP_ENABLED', '修复代码备份启用', '1', 'maintenance', '是否启用修复前代码备份', 1),
            ('AUTOFIX_DB_RECORD_ENABLED', '修复数据库留底启用', '1', 'maintenance', '是否启用修复记录数据库留底', 1),
            ('AUTOFIX_DB_RECORD_RETENTION_DAYS', '修复记录保留天数', '90', 'maintenance', '修复记录在数据库中的保留天数', 1),
            ('AUTOFIX_VALIDATION_ENABLED', '修复验证启用', '1', 'maintenance', '是否启用修复后验证', 1),
            ('AUTOFIX_ROLLBACK_ON_FAILURE_ENABLED', '修复失败回滚启用', '1', 'maintenance', '修复失败时是否自动回滚', 1),
            ('AUTOFIX_MAX_CONCURRENT_OPERATIONS', '最大并发修复数', '5', 'maintenance', '同时进行的最大修复操作数', 1),
            ('AUTOFIX_CONFIDENCE_THRESHOLD', '修复置信度阈值', '0.8', 'maintenance', '自动修复的最低置信度阈值', 1),
            ('AUTOFIX_RETRY_COUNT', '修复重试次数', '3', 'maintenance', '修复失败后的重试次数', 1),
            ('AUTOFIX_TIMEOUT', '修复超时时间', '300', 'maintenance', '单次修复操作的超时时间(秒)', 1),
            ('AUTOFIX_SELF_LEARNING_ENABLED', '修复自学习启用', '1', 'maintenance', '是否启用修复系统自学习能力', 1),
            ('AUTOFIX_MONITORING_INTERVAL', '修复监控间隔', '60', 'maintenance', '自动修复监控检查间隔(秒)', 1),
            ('AUTOFIX_NOTIFICATION_ENABLED', '修复通知启用', '1', 'maintenance', '是否启用修复通知功能', 1),
            ('AUTOFIX_ADMIN_EMAIL', '修复通知邮箱', '', 'maintenance', '接收修复通知的管理员邮箱', 1),
            ('AUTOFIX_LOG_LEVEL', '修复日志级别', 'INFO', 'maintenance', '自动修复系统的日志级别', 1),
            
            ('RESIDENT_ENABLED', '常驻服务启用', '1', 'maintenance', '是否启用系统常驻服务', 1),
            ('RESIDENT_HEARTBEAT_INTERVAL', '常驻服务心跳间隔', '30', 'maintenance', '常驻服务心跳发送间隔(秒)', 1),
            ('RESIDENT_HEALTH_CHECK_INTERVAL', '常驻服务健康检查间隔', '60', 'maintenance', '常驻服务健康检查间隔(秒)', 1),
            ('RESIDENT_AUTO_RESTART_ENABLED', '常驻服务自动重启启用', '1', 'maintenance', '是否启用常驻服务自动重启', 1),
            ('RESIDENT_MAX_RESTART_COUNT', '常驻服务最大重启次数', '5', 'maintenance', '单个常驻服务最大自动重启次数', 1),
            ('RESIDENT_RESTART_DELAY', '常驻服务重启延迟', '60', 'maintenance', '常驻服务重启间隔(秒)', 1),
            ('RESIDENT_SERVICE_TIMEOUT', '常驻服务超时时间', '300', 'maintenance', '常驻服务启动/执行超时时间(秒)', 1),
            ('RESIDENT_LOG_RETENTION_DAYS', '常驻服务日志保留天数', '30', 'maintenance', '常驻服务日志保留天数', 1),
            ('RESIDENT_CONCURRENT_LIMIT', '常驻服务并发数限制', '10', 'maintenance', '同时运行的常驻服务最大数量', 1),
            ('RESIDENT_SHUTDOWN_GRACE_PERIOD', '常驻服务优雅关闭等待时间', '10', 'maintenance', '常驻服务关闭时等待任务完成的时间(秒)', 1),
            ('RESIDENT_STARTUP_TIMEOUT', '常驻服务启动超时时间', '120', 'maintenance', '常驻服务启动超时时间(秒)', 1),
            ('RESIDENT_WATCHDOG_ENABLED', '常驻服务看门狗启用', '1', 'maintenance', '是否启用常驻服务看门狗监控', 1),
            ('RESIDENT_NOTIFICATION_ENABLED', '常驻服务通知启用', '1', 'maintenance', '是否启用常驻服务异常通知', 1),
            ('RESIDENT_PRIORITY_ORDER', '常驻服务启动优先级', 'core,scheduler,ai,task,maintenance', 'maintenance', '常驻服务启动顺序', 1),
            ('RESIDENT_AUTO_START_ENABLED', '常驻服务自动启动启用', '1', 'maintenance', '系统启动时是否自动启动所有常驻服务', 1),
            
            ('SANDBOX_ENABLED', '沙盒启用', '1', 'maintenance', '是否启用沙盒隔离环境', 1),
            ('SANDBOX_ISOLATION_LEVEL', '沙盒隔离级别', 'medium', 'maintenance', '沙盒隔离级别(low/medium/high)', 1),
            ('SANDBOX_MAX_INSTANCES', '沙盒最大实例数', '50', 'maintenance', '同时运行的最大沙盒实例数', 1),
            ('SANDBOX_MIN_INSTANCES', '沙盒最小实例数', '5', 'maintenance', '保持运行的最小沙盒实例数', 1),
            ('SANDBOX_RESOURCE_LIMIT_CPU', '沙盒CPU资源限制', '50', 'maintenance', '单个沙盒CPU使用率上限(%)', 1),
            ('SANDBOX_RESOURCE_LIMIT_MEMORY', '沙盒内存资源限制', '1024', 'maintenance', '单个沙盒内存上限(MB)', 1),
            ('SANDBOX_RESOURCE_LIMIT_DISK', '沙盒磁盘资源限制', '10240', 'maintenance', '单个沙盒磁盘使用上限(MB)', 1),
            ('SANDBOX_RESOURCE_LIMIT_PROCESSES', '沙盒进程数限制', '10', 'maintenance', '单个沙盒最大进程数', 1),
            ('SANDBOX_DYNAMIC_SCALING_ENABLED', '沙盒动态扩缩容启用', '1', 'maintenance', '是否启用沙盒动态扩缩容', 1),
            ('SANDBOX_PREWARM_ENABLED', '沙盒预温启用', '1', 'maintenance', '是否启用沙盒预温机制', 1),
            ('SANDBOX_HEALTH_CHECK_INTERVAL', '沙盒健康检查间隔', '60', 'maintenance', '沙盒健康检查间隔(秒)', 1),
            ('SANDBOX_AUTO_CLEANUP_ENABLED', '沙盒自动清理启用', '1', 'maintenance', '是否启用沙盒自动清理', 1),
            ('SANDBOX_CLEANUP_INTERVAL', '沙盒清理间隔', '3600', 'maintenance', '沙盒自动清理间隔(秒)', 1),
            ('SANDBOX_TIMEOUT', '沙盒超时时间', '3600', 'maintenance', '沙盒最长运行时间(秒)', 1),
            ('SANDBOX_NETWORK_ISOLATION_ENABLED', '沙盒网络隔离启用', '1', 'maintenance', '是否启用沙盒网络隔离', 1),
            ('SANDBOX_FILE_SYSTEM_ACCESS', '沙盒文件系统访问', '1', 'maintenance', '是否允许沙盒访问文件系统', 1),
            ('SANDBOX_CLIPBOARD_ACCESS', '沙盒剪贴板访问', '0', 'maintenance', '是否允许沙盒访问剪贴板', 1),
            ('SANDBOX_GPU_ACCESS', '沙盒GPU访问', '0', 'maintenance', '是否允许沙盒访问GPU', 1),
            
            ('NETWORK_ENABLED', '网络规则启用', '1', 'maintenance', '是否启用网络规则管理', 1),
            ('NETWORK_PORT_MAPPING_ENABLED', '端口映射启用', '1', 'maintenance', '是否启用端口映射功能', 1),
            ('NETWORK_FIREWALL_ENABLED', '防火墙规则启用', '1', 'maintenance', '是否启用防火墙规则管理', 1),
            ('NETWORK_IDEMPOTENT_SYNC_ENABLED', '幂等同步启用', '1', 'maintenance', '是否启用网络规则幂等同步，避免重复添加规则', 1),
            ('NETWORK_SYNC_INTERVAL', '网络规则同步间隔', '60', 'maintenance', '网络规则同步检查间隔(秒)', 1),
            ('NETWORK_MAX_PORT_RULES', '最大端口规则数', '100', 'maintenance', '允许的最大端口映射规则数', 1),
            ('NETWORK_MAX_FIREWALL_RULES', '最大防火墙规则数', '500', 'maintenance', '允许的最大防火墙规则数', 1),
            ('NETWORK_ALLOWED_PROTOCOLS', '允许的协议', 'tcp,udp', 'maintenance', '允许使用的网络协议列表', 1),
            ('NETWORK_ALLOWED_CHAINS', '允许的链', 'INPUT,OUTPUT,FORWARD,PREROUTING,POSTROUTING', 'maintenance', '允许配置的iptables链', 1),
            ('NETWORK_EXTERNAL_INTERFACE', '外部网络接口', 'eth0', 'maintenance', '对外服务的网络接口名称', 1),
            ('NETWORK_INTERNAL_INTERFACE', '内部网络接口', 'lo', 'maintenance', '内部服务的网络接口名称', 1),
            ('NETWORK_DEFAULT_INTERNAL_IP', '默认内部IP', '127.0.0.1', 'maintenance', '端口映射的默认内部IP地址', 1),
            ('NETWORK_DNAT_ENABLED', 'DNAT规则启用', '1', 'maintenance', '是否启用DNAT端口转发规则', 1),
            ('NETWORK_SNAT_ENABLED', 'SNAT规则启用', '1', 'maintenance', '是否启用SNAT源地址转换规则', 1),
            ('NETWORK_MASQUERADE_ENABLED', 'MASQUERADE启用', '1', 'maintenance', '是否启用MASQUERADE地址伪装', 1),
            ('NETWORK_PERSISTENT_ENABLED', '网络规则持久化启用', '1', 'maintenance', '是否启用网络规则持久化，重启后自动恢复', 1),
            ('NETWORK_AUTO_CLEANUP_ENABLED', '网络规则自动清理启用', '1', 'maintenance', '是否启用无效网络规则自动清理', 1),
            ('NETWORK_CLEANUP_INTERVAL', '网络规则清理间隔', '3600', 'maintenance', '网络规则自动清理间隔(秒)', 1),
            ('NETWORK_HEALTH_CHECK_INTERVAL', '网络健康检查间隔', '60', 'maintenance', '网络连通性检查间隔(秒)', 1),
            ('NETWORK_ALERT_ON_FAILURE', '网络故障告警', '1', 'maintenance', '网络规则应用失败时是否发送告警', 1),
            
            ('PROTOCOL_ENABLED', '协议管理启用', '1', 'maintenance', '是否启用协议管理功能', 1),
            ('PROTOCOL_DEFAULT_ENCODING', '默认编码', 'utf-8', 'maintenance', '协议通信默认编码格式', 1),
            ('PROTOCOL_DEFAULT_TIMEOUT', '默认超时时间', '300', 'maintenance', '协议连接默认超时时间(秒)', 1),
            ('PROTOCOL_DEFAULT_RETRY_COUNT', '默认重试次数', '3', 'maintenance', '协议操作默认重试次数', 1),
            ('PROTOCOL_MAX_CONNECTIONS', '最大连接数', '1000', 'maintenance', '协议服务最大并发连接数', 1),
            ('PROTOCOL_KEEP_ALIVE_ENABLED', '长连接启用', '1', 'maintenance', '是否启用协议长连接', 1),
            ('PROTOCOL_COMPRESSION_ENABLED', '压缩启用', '0', 'maintenance', '是否启用协议数据压缩', 1),
            ('PROTOCOL_ENCRYPTION_ENABLED', '加密启用', '1', 'maintenance', '是否启用协议加密传输', 1),
            ('PROTOCOL_SSL_CERTIFICATE_PATH', 'SSL证书路径', '', 'maintenance', 'SSL证书文件路径', 1),
            ('PROTOCOL_SSL_KEY_PATH', 'SSL密钥路径', '', 'maintenance', 'SSL密钥文件路径', 1),
            ('PROTOCOL_SUPPORTED_TYPES', '支持的协议类型', 'http,https,grpc,websocket,mqtt,amqp', 'maintenance', '系统支持的协议类型列表', 1),
            ('PROTOCOL_API_RATE_LIMIT', 'API限流', '100', 'maintenance', '协议API默认限流阈值(次/分钟)', 1),
            ('PROTOCOL_API_RATE_LIMIT_WINDOW', 'API限流窗口', '1minute', 'maintenance', '协议API限流时间窗口', 1),
            ('PROTOCOL_AUTH_REQUIRED', '认证要求', '1', 'maintenance', '协议接口是否默认需要认证', 1),
            ('PROTOCOL_AUTH_TOKEN_EXPIRY', '认证令牌过期时间', '3600', 'maintenance', '协议认证令牌过期时间(秒)', 1),
            ('PROTOCOL_WEBSOCKET_ENABLED', 'WebSocket启用', '1', 'maintenance', '是否启用WebSocket协议支持', 1),
            ('PROTOCOL_WEBSOCKET_PING_INTERVAL', 'WebSocket心跳间隔', '30', 'maintenance', 'WebSocket连接心跳检测间隔(秒)', 1),
            ('PROTOCOL_GRPC_ENABLED', 'gRPC启用', '1', 'maintenance', '是否启用gRPC协议支持', 1),
            ('PROTOCOL_MQTT_ENABLED', 'MQTT启用', '1', 'maintenance', '是否启用MQTT协议支持', 1),
            ('PROTOCOL_MQTT_BROKER_URL', 'MQTT Broker地址', '', 'maintenance', 'MQTT Broker连接地址', 1),
            ('PROTOCOL_MQTT_KEEP_ALIVE', 'MQTT心跳间隔', '60', 'maintenance', 'MQTT连接心跳间隔(秒)', 1),
            ('PROTOCOL_EVENT_STREAMING_ENABLED', '事件流启用', '1', 'maintenance', '是否启用事件流协议支持', 1),
            ('PROTOCOL_EVENT_BATCH_SIZE', '事件批处理大小', '100', 'maintenance', '事件流批处理最大条数', 1),
            ('PROTOCOL_EVENT_FLUSH_INTERVAL', '事件刷新间隔', '1', 'maintenance', '事件流缓冲区刷新间隔(秒)', 1),
            
            ('PORT_ENABLED', '端口管理启用', '1', 'maintenance', '是否启用端口管理功能', 1),
            ('PORT_DEFAULT_PROTOCOL', '默认协议', 'tcp', 'maintenance', '端口默认使用的协议', 1),
            ('PORT_DEFAULT_BINDING_IP', '默认绑定IP', '0.0.0.0', 'maintenance', '端口默认绑定的IP地址', 1),
            ('PORT_MIN_NUMBER', '最小端口号', '1024', 'maintenance', '允许使用的最小端口号', 1),
            ('PORT_MAX_NUMBER', '最大端口号', '65535', 'maintenance', '允许使用的最大端口号', 1),
            ('PORT_DEFAULT_RATE_LIMIT', '默认限流', '0', 'maintenance', '端口默认限流阈值(0=不限)', 1),
            ('PORT_DEFAULT_RATE_LIMIT_WINDOW', '默认限流窗口', '1minute', 'maintenance', '端口默认限流时间窗口', 1),
            ('PORT_DEFAULT_CONNECTION_LIMIT', '默认连接数限制', '0', 'maintenance', '端口默认最大连接数(0=不限)', 1),
            ('PORT_DEFAULT_TIMEOUT', '默认超时时间', '0', 'maintenance', '端口默认连接超时时间(秒)(0=不限)', 1),
            ('PORT_TLS_ENABLED', 'TLS启用', '0', 'maintenance', '是否默认启用TLS加密', 1),
            ('PORT_TLS_CERTIFICATE_PATH', 'TLS证书路径', '', 'maintenance', 'TLS证书文件路径', 1),
            ('PORT_TLS_KEY_PATH', 'TLS密钥路径', '', 'maintenance', 'TLS密钥文件路径', 1),
            ('PORT_IDEMPOTENT_SYNC_ENABLED', '幂等同步启用', '1', 'maintenance', '是否启用端口规则幂等同步，避免重复添加', 1),
            ('PORT_SYNC_INTERVAL', '端口规则同步间隔', '60', 'maintenance', '端口规则同步检查间隔(秒)', 1),
            ('PORT_MAX_RULES', '最大端口规则数', '200', 'maintenance', '允许的最大端口规则数', 1),
            ('PORT_MAX_MAPPING_RULES', '最大映射规则数', '100', 'maintenance', '允许的最大端口映射规则数', 1),
            ('PORT_AUTO_CLEANUP_ENABLED', '自动清理启用', '1', 'maintenance', '是否启用无效端口规则自动清理', 1),
            ('PORT_CLEANUP_INTERVAL', '清理间隔', '3600', 'maintenance', '端口规则自动清理间隔(秒)', 1),
            ('PORT_HEALTH_CHECK_INTERVAL', '健康检查间隔', '60', 'maintenance', '端口健康检查间隔(秒)', 1),
            ('PORT_ALERT_ON_FAILURE', '故障告警', '1', 'maintenance', '端口规则应用失败时是否发送告警', 1),
            ('PORT_RESERVED_START', '保留端口起始', '1', 'maintenance', '系统保留端口起始号', 1),
            ('PORT_RESERVED_END', '保留端口结束', '1023', 'maintenance', '系统保留端口结束号', 1),
            ('PORT_SYSTEM_START', '系统端口起始', '8000', 'maintenance', '系统服务端口起始号', 1),
            ('PORT_SYSTEM_END', '系统端口结束', '9000', 'maintenance', '系统服务端口结束号', 1),
            ('PORT_USER_START', '用户端口起始', '9000', 'maintenance', '用户自定义端口起始号', 1),
            ('PORT_USER_END', '用户端口结束', '65535', 'maintenance', '用户自定义端口结束号', 1),
            
            ('DOCUMENT_ENABLED', '文档管理启用', '1', 'maintenance', '是否启用文档管理功能', 1),
            ('DOCUMENT_DEFAULT_TYPE', '默认文档类型', 'markdown', 'maintenance', '文档默认类型', 1),
            ('DOCUMENT_DEFAULT_CATEGORY', '默认文档分类', 'system', 'maintenance', '文档默认分类', 1),
            ('DOCUMENT_DEFAULT_ACCESS_LEVEL', '默认访问级别', 'public', 'maintenance', '文档默认访问级别(public/internal/private)', 1),
            ('DOCUMENT_MAX_SIZE', '最大文档大小', '10485760', 'maintenance', '单个文档最大大小(字节)', 1),
            ('DOCUMENT_MAX_COUNT', '最大文档数量', '1000', 'maintenance', '系统允许的最大文档数量', 1),
            ('DOCUMENT_VERSION_HISTORY_ENABLED', '版本历史启用', '1', 'maintenance', '是否启用文档版本历史', 1),
            ('DOCUMENT_VERSION_MAX_COUNT', '最大版本数量', '10', 'maintenance', '单个文档保留的最大版本数', 1),
            ('DOCUMENT_AUTO_SAVE_ENABLED', '自动保存启用', '1', 'maintenance', '是否启用文档自动保存', 1),
            ('DOCUMENT_AUTO_SAVE_INTERVAL', '自动保存间隔', '300', 'maintenance', '文档自动保存间隔(秒)', 1),
            ('DOCUMENT_SEARCH_ENABLED', '文档搜索启用', '1', 'maintenance', '是否启用文档全文搜索', 1),
            ('DOCUMENT_SEARCH_INDEX_INTERVAL', '搜索索引间隔', '3600', 'maintenance', '文档搜索索引更新间隔(秒)', 1),
            ('DOCUMENT_EXPORT_ENABLED', '文档导出启用', '1', 'maintenance', '是否启用文档导出功能', 1),
            ('DOCUMENT_EXPORT_FORMATS', '支持的导出格式', 'markdown,pdf,html', 'maintenance', '文档支持的导出格式列表', 1),
            ('DOCUMENT_IMPORT_ENABLED', '文档导入启用', '1', 'maintenance', '是否启用文档导入功能', 1),
            ('DOCUMENT_IMPORT_FORMATS', '支持的导入格式', 'markdown,html,txt', 'maintenance', '文档支持的导入格式列表', 1),
            ('DOCUMENT_AUTO_CLEANUP_ENABLED', '自动清理启用', '1', 'maintenance', '是否启用过期文档自动清理', 1),
            ('DOCUMENT_CLEANUP_INTERVAL', '清理间隔', '86400', 'maintenance', '文档自动清理间隔(秒)', 1),
            ('DOCUMENT_RETENTION_DAYS', '文档保留天数', '90', 'maintenance', '过期文档保留天数(天)', 1),
            ('DOCUMENT_ALERT_ON_FAILURE', '故障告警', '1', 'maintenance', '文档操作失败时是否发送告警', 1),
            ('DOCUMENT_ENCRYPTION_ENABLED', '文档加密启用', '1', 'maintenance', '是否启用文档内容加密存储', 1),
            ('DOCUMENT_COMPRESSION_ENABLED', '文档压缩启用', '1', 'maintenance', '是否启用文档压缩存储', 1),
            ('DOCUMENT_CACHE_ENABLED', '文档缓存启用', '1', 'maintenance', '是否启用文档缓存', 1),
            ('DOCUMENT_CACHE_TTL', '文档缓存TTL', '3600', 'maintenance', '文档缓存有效期(秒)', 1),
            
            ('FRONTEND_ENABLED', '前端样式规范启用', '1', 'maintenance', '是否启用前端样式规范', 1),
            ('FRONTEND_BORDER_RADIUS_SMALL', '小倒角', '4px', 'maintenance', '小尺寸元素圆角(px)', 1),
            ('FRONTEND_BORDER_RADIUS_MEDIUM', '中等倒角', '8px', 'maintenance', '中等尺寸元素圆角(px)', 1),
            ('FRONTEND_BORDER_RADIUS_LARGE', '大倒角', '12px', 'maintenance', '大尺寸元素圆角(px)', 1),
            ('FRONTEND_BORDER_RADIUS_EXTRA_LARGE', '超大倒角', '16px', 'maintenance', '超大尺寸元素圆角(px)', 1),
            ('FRONTEND_BORDER_RADIUS_FULL', '完全圆角', '9999px', 'maintenance', '圆形元素圆角(px)', 1),
            ('FRONTEND_PADDING_SMALL', '小内边距', '8px', 'maintenance', '小尺寸元素内边距(px)', 1),
            ('FRONTEND_PADDING_MEDIUM', '中等内边距', '12px', 'maintenance', '中等尺寸元素内边距(px)', 1),
            ('FRONTEND_PADDING_LARGE', '大内边距', '16px', 'maintenance', '大尺寸元素内边距(px)', 1),
            ('FRONTEND_MARGIN_SMALL', '小外边距', '8px', 'maintenance', '小尺寸元素外边距(px)', 1),
            ('FRONTEND_MARGIN_MEDIUM', '中等外边距', '12px', 'maintenance', '中等尺寸元素外边距(px)', 1),
            ('FRONTEND_MARGIN_LARGE', '大外边距', '16px', 'maintenance', '大尺寸元素外边距(px)', 1),
            ('FRONTEND_MARGIN_EXTRA_LARGE', '超大外边距', '24px', 'maintenance', '超大尺寸元素外边距(px)', 1),
            ('FRONTEND_OPACITY_DISABLED', '禁用透明度', '0.5', 'maintenance', '禁用状态元素透明度', 1),
            ('FRONTEND_OPACITY_HOVER', '悬停透明度', '0.85', 'maintenance', '悬停状态元素透明度', 1),
            ('FRONTEND_OPACITY_FOCUS', '聚焦透明度', '0.9', 'maintenance', '聚焦状态元素透明度', 1),
            ('FRONTEND_OPACITY_ACTIVE', '激活透明度', '0.95', 'maintenance', '激活状态元素透明度', 1),
            ('FRONTEND_FONT_SIZE_XS', '特小号字体', '12px', 'maintenance', '特小号字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_SMALL', '小号字体', '13px', 'maintenance', '小号字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_NORMAL', '正常字体', '14px', 'maintenance', '正常字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_LARGE', '大号字体', '16px', 'maintenance', '大号字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_XL', '特大号字体', '18px', 'maintenance', '特大号字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_XXL', '超大号字体', '24px', 'maintenance', '超大号字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_HEADING_1', '一级标题字体', '32px', 'maintenance', '一级标题字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_HEADING_2', '二级标题字体', '24px', 'maintenance', '二级标题字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_HEADING_3', '三级标题字体', '20px', 'maintenance', '三级标题字体大小(px)', 1),
            ('FRONTEND_FONT_SIZE_HEADING_4', '四级标题字体', '18px', 'maintenance', '四级标题字体大小(px)', 1),
            ('FRONTEND_TEXT_ALIGN_DEFAULT', '默认对齐', 'left', 'maintenance', '文本默认对齐方式', 1),
            ('FRONTEND_TEXT_ALIGN_CENTER', '居中对齐', 'center', 'maintenance', '文本居中对齐方式', 1),
            ('FRONTEND_TEXT_ALIGN_RIGHT', '右对齐', 'right', 'maintenance', '文本右对齐方式', 1),
            ('FRONTEND_TEXT_ALIGN_JUSTIFY', '两端对齐', 'justify', 'maintenance', '文本两端对齐方式', 1),
            ('FRONTEND_LINE_HEIGHT_DEFAULT', '默认行高', '1.5', 'maintenance', '默认行高倍数', 1),
            ('FRONTEND_LINE_HEIGHT_TIGHT', '紧凑行高', '1.25', 'maintenance', '紧凑行高倍数', 1),
            ('FRONTEND_LINE_HEIGHT_LOOSE', '宽松行高', '1.75', 'maintenance', '宽松行高倍数', 1),
            ('FRONTEND_SPACING_ICON_TEXT', '图标文字间距', '8px', 'maintenance', '图标与文字之间的间距(px)', 1),
            ('FRONTEND_SPACING_ELEMENTS', '元素间距', '16px', 'maintenance', '同级元素之间的间距(px)', 1),
            ('FRONTEND_SPACING_SECTIONS', '区块间距', '24px', 'maintenance', '区块之间的间距(px)', 1),
            ('FRONTEND_SHADOW_SMALL', '小阴影', '0 2px 4px rgba(0,0,0,0.1)', 'maintenance', '小尺寸元素阴影', 1),
            ('FRONTEND_SHADOW_MEDIUM', '中等阴影', '0 4px 12px rgba(0,0,0,0.12)', 'maintenance', '中等尺寸元素阴影', 1),
            ('FRONTEND_SHADOW_LARGE', '大阴影', '0 8px 24px rgba(0,0,0,0.15)', 'maintenance', '大尺寸元素阴影', 1),
            ('FRONTEND_BORDER_WIDTH_DEFAULT', '默认边框宽度', '1px', 'maintenance', '默认边框宽度(px)', 1),
            ('FRONTEND_BORDER_STYLE_DEFAULT', '默认边框样式', 'solid', 'maintenance', '默认边框样式', 1),
            ('FRONTEND_TRANSITION_DURATION', '过渡动画时长', '0.2s', 'maintenance', '元素过渡动画时长(秒)', 1),
            ('FRONTEND_ANIMATION_DURATION', '动画时长', '0.3s', 'maintenance', '元素动画时长(秒)', 1),
            
            ('DIALOG_ENABLED', '弹窗功能启用', '1', 'maintenance', '是否启用弹窗功能', 1),
            ('DIALOG_DEFAULT_TYPE', '默认弹窗类型', 'modal', 'maintenance', '弹窗默认类型(modal/toast/notification/confirm)', 1),
            ('DIALOG_DEFAULT_SIZE', '默认弹窗大小', 'medium', 'maintenance', '弹窗默认大小(small/medium/large/full)', 1),
            ('DIALOG_DEFAULT_POSITION', '默认弹窗位置', 'center', 'maintenance', '弹窗默认位置(center/top/top-right/bottom/bottom-right)', 1),
            ('DIALOG_SHOW_HEADER', '显示头部', '1', 'maintenance', '弹窗默认是否显示头部', 1),
            ('DIALOG_SHOW_FOOTER', '显示底部', '1', 'maintenance', '弹窗默认是否显示底部', 1),
            ('DIALOG_SHOW_CLOSE_BUTTON', '显示关闭按钮', '1', 'maintenance', '弹窗默认是否显示关闭按钮', 1),
            ('DIALOG_SHOW_CONFIRM_BUTTON', '显示确认按钮', '1', 'maintenance', '弹窗默认是否显示确认按钮', 1),
            ('DIALOG_CONFIRM_BUTTON_TEXT', '确认按钮文字', '确定', 'maintenance', '弹窗确认按钮默认文字', 1),
            ('DIALOG_CANCEL_BUTTON_TEXT', '取消按钮文字', '取消', 'maintenance', '弹窗取消按钮默认文字', 1),
            ('DIALOG_AUTO_CLOSE', '自动关闭', '0', 'maintenance', '弹窗默认是否自动关闭', 1),
            ('DIALOG_AUTO_CLOSE_DELAY', '自动关闭延迟', '3000', 'maintenance', '弹窗自动关闭延迟时间(毫秒)', 1),
            ('DIALOG_BACKDROP', '遮罩层', '1', 'maintenance', '弹窗默认是否显示遮罩层', 1),
            ('DIALOG_KEYBOARD', '键盘关闭', '1', 'maintenance', '弹窗默认是否支持键盘ESC关闭', 1),
            ('DIALOG_DRAGGABLE', '可拖拽', '0', 'maintenance', '弹窗默认是否可拖拽', 1),
            ('DIALOG_RESIZABLE', '可调整大小', '0', 'maintenance', '弹窗默认是否可调整大小', 1),
            ('DIALOG_ANIMATION_ENABLED', '动画启用', '1', 'maintenance', '弹窗默认是否启用动画', 1),
            ('DIALOG_ANIMATION_TYPE', '动画类型', 'fade', 'maintenance', '弹窗动画类型(fade/zoom/slide-up/slide-down/slide-left/slide-right)', 1),
            ('DIALOG_MAX_WIDTH', '最大宽度', '600px', 'maintenance', '弹窗最大宽度', 1),
            ('DIALOG_MIN_WIDTH', '最小宽度', '300px', 'maintenance', '弹窗最小宽度', 1),
            ('DIALOG_MAX_HEIGHT', '最大高度', '80vh', 'maintenance', '弹窗最大高度', 1),
            ('DIALOG_MIN_HEIGHT', '最小高度', '200px', 'maintenance', '弹窗最小高度', 1),
            ('DIALOG_WELCOME_ENABLED', '欢迎文档启用', '1', 'maintenance', '是否启用欢迎弹窗文档', 1),
            ('DIALOG_WELCOME_DISPLAY_ONCE', '欢迎文档只显示一次', '1', 'maintenance', '欢迎文档是否只在首次登录显示', 1),
            ('DIALOG_WELCOME_DISPLAY_INTERVAL', '欢迎文档显示间隔', '0', 'maintenance', '欢迎文档重复显示间隔(天)(0=只显示一次)', 1),
            ('DIALOG_INSTRUCTION_ENABLED', '说明文档启用', '1', 'maintenance', '是否启用说明弹窗文档', 1),
            ('DIALOG_INSTRUCTION_DISPLAY_ONCE', '说明文档只显示一次', '1', 'maintenance', '说明文档是否只显示一次', 1),
            ('DIALOG_INSTRUCTION_DISPLAY_INTERVAL', '说明文档显示间隔', '0', 'maintenance', '说明文档重复显示间隔(天)(0=只显示一次)', 1),
            ('DIALOG_NOTIFICATION_ENABLED', '通知文档启用', '1', 'maintenance', '是否启用通知弹窗文档', 1),
            ('DIALOG_NOTIFICATION_AUTO_CLOSE', '通知自动关闭', '1', 'maintenance', '通知弹窗是否自动关闭', 1),
            ('DIALOG_NOTIFICATION_AUTO_CLOSE_DELAY', '通知自动关闭延迟', '5000', 'maintenance', '通知弹窗自动关闭延迟时间(毫秒)', 1),
            ('DIALOG_MAX_DOCUMENTS', '最大文档数量', '50', 'maintenance', '弹窗文档最大数量', 1),
            ('DIALOG_DEFAULT_LANGUAGE', '默认语言', 'zh-CN', 'maintenance', '弹窗文档默认语言', 1),
        ]
        
        added_count = 0
        skipped_count = 0
        
        for rule in default_rules:
            rule_code = rule[0]
            cursor.execute('SELECT COUNT(*) FROM system_rules WHERE rule_code = ?', (rule_code,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO system_rules (rule_code, rule_name, rule_value, rule_type, description, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', rule)
                added_count += 1
            else:
                skipped_count += 1
        
        if added_count > 0:
            print(f"✓ 已添加 {added_count} 条新规则")
        if skipped_count > 0:
            print(f"✓ 跳过 {skipped_count} 条已存在规则")
        
        if total_count == 0:
            print("✓ 已初始化默认系统规则")
        
        conn.commit()
        conn.close()
        print("✓ system_rules 表创建成功")
        return True
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        return False

def check_system_rules_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_rules'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print("✓ system_rules 表已存在")
            return True
        else:
            print("✗ system_rules 表不存在")
            return False
    except Exception as e:
        print(f"✗ 检查表失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("修复 system_rules 表")
    print("=" * 50)
    
    create_system_rules_table()
    
    print("=" * 50)
    print("修复完成")
    print("=" * 50)

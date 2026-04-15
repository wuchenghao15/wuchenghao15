#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加缺失的必要系统配置项
"""

import sqlite3
import os
import time

# 数据库文件路径
DB_FILES = ['primary.db', 'backup.db']

# 新增系统配置项
new_configs = [
	# 数据库相关配置
	('db_max_connections', '100', 'integer', '数据库最大连接数'),
	('db_connection_timeout', '30', 'integer', '数据库连接超时时间(秒)'),
	
	# AI相关配置
	('ai_response_timeout', '30', 'integer', 'AI响应超时时间(秒)'),
	('ai_max_concurrent_requests', '50', 'integer', 'AI最大并发请求数'),
	('ai_auto_scale', 'true', 'boolean', 'AI实例自动缩放'),
	
	# 用户认证相关配置
	('password_min_length', '8', 'integer', '密码最小长度'),
	('password_require_uppercase', 'true', 'boolean', '密码必须包含大写字母'),
	('password_require_lowercase', 'true', 'boolean', '密码必须包含小写字母'),
	('password_require_digit', 'true', 'boolean', '密码必须包含数字'),
	('password_require_special', 'true', 'boolean', '密码必须包含特殊字符'),
	('login_attempts_limit', '5', 'integer', '登录尝试次数限制'),
	('login_lockout_duration', '300', 'integer', '登录锁定持续时间(秒)'),
	
	# 安全相关配置
	('csrf_protection', 'true', 'boolean', '启用CSRF保护'),
	('cors_enabled', 'false', 'boolean', '启用CORS'),
	('cors_allow_origins', '*', 'string', '允许的CORS来源'),
	
	# 系统行为配置
	('auto_cleanup_enabled', 'true', 'boolean', '启用自动清理'),
	('auto_cleanup_interval', '86400', 'integer', '自动清理间隔(秒)'),
	('log_retention_days', '30', 'integer', '日志保留天数'),
	
	# 用户界面配置
	('default_language', 'zh-CN', 'string', '默认语言'),
	('theme', 'light', 'string', '系统主题'),
	('sidebar_collapsed', 'false', 'boolean', '侧边栏默认折叠状态'),
	
	# 邮件配置
	('smtp_enabled', 'false', 'boolean', '启用SMTP服务'),
	('smtp_host', '', 'string', 'SMTP服务器地址'),
	('smtp_port', '587', 'integer', 'SMTP服务器端口'),
	('smtp_username', '', 'string', 'SMTP用户名'),
	('smtp_password', '', 'string', 'SMTP密码'),
	('smtp_from_email', '', 'string', '发件人邮箱'),
	('smtp_tls', 'true', 'boolean', '启用SMTP TLS'),
	
	# 监控配置
	('monitoring_enabled', 'true', 'boolean', '启用系统监控'),
	('alert_threshold_cpu', '80', 'integer', 'CPU告警阈值(%)'),
	('alert_threshold_memory', '85', 'integer', '内存告警阈值(%)'),
	('alert_threshold_disk', '90', 'integer', '磁盘告警阈值(%)'),
	
	# 数据备份配置
	('backup_enabled', 'true', 'boolean', '启用自动备份'),
	('backup_retention_count', '7', 'integer', '备份保留数量'),
	('backup_time', '02:00', 'string', '自动备份时间'),
	
	# 新添加的用户数据管理配置
	('user_data_management_enabled', 'true', 'boolean', '启用用户数据AI管理'),
	('user_data_auto_complete', 'true', 'boolean', '启用用户数据自动补全'),
	('user_data_update_interval', '3600', 'integer', '用户数据更新间隔(秒)')
]

def add_configs(db_file):
	"""向指定数据库添加配置项"""
	try:
		conn = sqlite3.connect(db_file)
		cursor = conn.cursor()
		
		# 创建表（如果不存在）
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS system_config (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				config_key TEXT UNIQUE NOT NULL,
				config_value TEXT NOT NULL,
				config_type TEXT NOT NULL DEFAULT 'string',
				description TEXT DEFAULT '',
				is_active INTEGER DEFAULT 1,
				created_at TEXT DEFAULT CURRENT_TIMESTAMP,
				updated_at TEXT DEFAULT CURRENT_TIMESTAMP
			)
		''')
		
		# 插入或忽略配置项
		for config_key, config_value, config_type, description in new_configs:
			cursor.execute('''
				INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description, is_active)
				VALUES (?, ?, ?, ?, 1)
			''', (config_key, config_value, config_type, description))
		
		conn.commit()
		conn.close()
		
		print(f"[{time.strftime('%H:%M:%S')}] 成功添加配置到 {db_file}")
		return True
		
	except Exception as e:
		print(f"[{time.strftime('%H:%M:%S')}] 添加配置到 {db_file} 失败: {str(e)}")
		return False

# 主函数
def main():
	print("开始添加系统配置项...")
	
	for db_file in DB_FILES:
		if os.path.exists(db_file):
			add_configs(db_file)
		else:
			print(f"[{time.strftime('%H:%M:%S')}] 数据库文件 {db_file} 不存在，跳过")
	
	print("\n所有配置项添加操作完成！")

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(f"执行脚本时发生错误: {str(e)}")
		import traceback
		traceback.print_exc()
		exit(1)

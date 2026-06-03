# -*- coding: utf-8 -*-
import os
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
双数据库配置文件

# 双数据库配置
DB_SYNC_INTERVAL = 3600  # 同步间隔(秒)

# 主数据库配置
PRIMARY_DB_TYPE = 'sqlite'  # 主数据库类型:sqlite, mysql, postgresql
PRIMARY_DB_PATH = 'instance/mtscos.db'  # SQLite数据库路径
PRIMARY_DB_HOST = 'localhost'  # MySQL/PostgreSQL主机
PRIMARY_DB_PORT = 3306  # MySQL/PostgreSQL端口
PRIMARY_DB_USER = 'root'  # MySQL/PostgreSQL用户名
PRIMARY_DB_PASSWORD = 'password'  # MySQL/PostgreSQL密码
PRIMARY_DB_NAME = 'mtscos'  # MySQL/PostgreSQL数据库名

# 备份数据库配置
BACKUP_DB_TYPE = 'sqlite'  # 备份数据库类型:sqlite, mysql, postgresql
BACKUP_DB_PATH = 'instance/mtscos_backup.db'  # SQLite备份数据库路径
BACKUP_DB_HOST = 'localhost'  # MySQL/PostgreSQL备份主机
BACKUP_DB_PORT = 3306  # MySQL/PostgreSQL备份端口
BACKUP_DB_USER = 'root'  # MySQL/PostgreSQL备份用户名
BACKUP_DB_PASSWORD = 'password'  # MySQL/PostgreSQL备份密码
BACKUP_DB_NAME = 'mtscos_backup'  # MySQL/PostgreSQL备份数据库名

"""
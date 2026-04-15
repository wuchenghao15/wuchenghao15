#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库自动升级系统
自动升级数据库结构和数据
"""

import os
import sys
import logging
import subprocess
import json
import time
from datetime import datetime
import sqlite3
import shutil
import signal
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_db_upgrade.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoDBUpgrader:
    """数据库自动升级器"""
    
    def __init__(self):
        self.running = True
        self.db_config_file = 'db_config.json'
        self.migrations_dir = 'migrations'
        self.backups_dir = 'db_backups'
        self.default_db_path = 'color_schemes.db'  # 默认使用配色方案数据库
        
        # 初始化配置
        self.init_config()
    
    def init_config(self):
        """初始化数据库配置"""
        if not os.path.exists(self.db_config_file):
            default_config = {
                'current_version': '1.0.0',
                'last_upgraded': datetime.now().isoformat(),
                'upgrade_check_interval': 86400,  # 24小时
                'database_path': self.default_db_path,
                'auto_upgrade_enabled': True,
                'migration_history': []
            }
            with open(self.db_config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"已创建默认数据库配置文件: {self.db_config_file}")
        
        # 创建迁移目录
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            logger.info(f"已创建迁移目录: {self.migrations_dir}")
        
        # 创建备份目录
        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)
            logger.info(f"已创建备份目录: {self.backups_dir}")
        
        # 创建初始迁移脚本
        self.create_initial_migration()
    
    def create_initial_migration(self):
        """创建初始迁移脚本"""
        initial_migration = os.path.join(self.migrations_dir, '001_initial.sql')
        if not os.path.exists(initial_migration):
            with open(initial_migration, 'w') as f:
                f.write("""-- 初始数据库结构
-- 配色方案表
CREATE TABLE IF NOT EXISTS color_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    colors TEXT,
    source TEXT,
    scraped_at TEXT,
    popularity INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 0
);

-- 布局方案表
CREATE TABLE IF NOT EXISTS layout_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    layout_json TEXT,
    source TEXT,
    scraped_at TEXT,
    popularity INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 0
);

-- 系统版本表
CREATE TABLE IF NOT EXISTS system_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT,
    created_at TEXT,
    updated_at TEXT,
    description TEXT
);

-- 插入初始版本记录
INSERT OR IGNORE INTO system_version (version, created_at, updated_at, description)
VALUES ('1.0.0', datetime('now'), datetime('now'), '初始版本');
""")
            logger.info(f"已创建初始迁移脚本: {initial_migration}")
    
    def load_config(self):
        """加载数据库配置"""
        try:
            with open(self.db_config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据库配置失败: {str(e)}")
            return {
                'current_version': '1.0.0',
                'last_upgraded': datetime.now().isoformat(),
                'upgrade_check_interval': 86400,
                'database_path': self.default_db_path,
                'auto_upgrade_enabled': True,
                'migration_history': []
            }
    
    def save_config(self, config):
        """保存数据库配置"""
        try:
            with open(self.db_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"已保存数据库配置到 {self.db_config_file}")
        except Exception as e:
            logger.error(f"保存数据库配置失败: {str(e)}")
    
    def start_upgrade_monitor(self, interval=86400):
        """开始升级监控"""
        logger.info("启动数据库自动升级监控...")
        
        while self.running:
            try:
                # 检查是否需要升级
                if self.should_upgrade():
                    logger.info("开始数据库自动升级...")
                    self.run_upgrade()
                else:
                    logger.info("数据库版本已是最新，无需升级")
                
                # 等待指定时间
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"升级监控发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
        
        logger.info("数据库自动升级监控已停止")
    
    def stop(self, signum=None, frame=None):
        """停止监控系统"""
        logger.info("正在停止数据库自动升级监控...")
        self.running = False
    
    def should_upgrade(self):
        """检查是否需要升级"""
        config = self.load_config()
        
        if not config.get('auto_upgrade_enabled', True):
            logger.info("数据库自动升级已禁用")
            return False
        
        # 检查距离上次升级的时间
        last_upgraded = datetime.fromisoformat(config.get('last_upgraded', datetime.now().isoformat()))
        interval = config.get('upgrade_check_interval', 86400)
        
        if (datetime.now() - last_upgraded).total_seconds() < interval:
            logger.debug(f"距离上次升级时间不足 {interval} 秒，跳过升级检查")
            return False
        
        # 检查数据库当前版本
        current_db_version = self.get_current_db_version()
        config_version = config.get('current_version', '1.0.0')
        
        # 检查是否有新的迁移脚本
        latest_migration_version = self.get_latest_migration_version()
        
        if latest_migration_version and self.is_newer_version(latest_migration_version, current_db_version):
            logger.info(f"发现新的迁移脚本: {latest_migration_version} (当前数据库版本: {current_db_version})")
            return True
        
        return False
    
    def get_current_db_version(self):
        """获取当前数据库版本"""
        logger.info("获取当前数据库版本...")
        
        config = self.load_config()
        db_path = config.get('database_path', self.default_db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查system_version表是否存在
            cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='system_version';""")
            if cursor.fetchone():
                cursor.execute("""SELECT version FROM system_version ORDER BY id DESC LIMIT 1;""")
                result = cursor.fetchone()
                if result:
                    conn.close()
                    return result[0]
            
            conn.close()
            return '1.0.0'  # 默认版本
            
        except Exception as e:
            logger.error(f"获取当前数据库版本失败: {str(e)}")
            return '1.0.0'
    
    def get_latest_migration_version(self):
        """获取最新的迁移脚本版本"""
        logger.info("检查最新迁移脚本版本...")
        
        migration_files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        if not migration_files:
            return '1.0.0'
        
        # 按文件名排序，获取最新版本
        migration_files.sort()
        latest_file = migration_files[-1]
        
        # 从文件名中提取版本号 (格式: 001_initial.sql -> 1.0.0)
        try:
            version_num = int(latest_file.split('_')[0])
            return f"{version_num}.0.0"
        except Exception as e:
            logger.error(f"提取迁移脚本版本失败: {str(e)}")
            return '1.0.0'
    
    def is_newer_version(self, latest, current):
        """检查是否是更新的版本"""
        try:
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False
            
            # 如果前面的版本号相同，检查长度
            return len(latest_parts) > len(current_parts)
        except Exception as e:
            logger.error(f"版本比较失败: {str(e)}")
            return False
    
    def run_upgrade(self):
        """执行升级"""
        logger.info("开始执行数据库升级...")
        
        config = self.load_config()
        current_version = config.get('current_version', '1.0.0')
        current_db_version = self.get_current_db_version()
        latest_migration_version = self.get_latest_migration_version()
        
        if not latest_migration_version:
            logger.error("无法获取最新迁移脚本版本，升级失败")
            return False
        
        try:
            # 1. 备份当前数据库
            backup_path = self.backup_database()
            
            # 2. 执行迁移脚本
            self.execute_migrations(current_db_version, latest_migration_version)
            
            # 3. 更新数据库版本记录
            self.update_db_version(latest_migration_version)
            
            # 4. 更新配置
            config['current_version'] = latest_migration_version
            config['last_upgraded'] = datetime.now().isoformat()
            
            # 记录迁移历史
            migration_record = {
                'from_version': current_db_version,
                'to_version': latest_migration_version,
                'migrated_at': datetime.now().isoformat(),
                'backup_path': backup_path,
                'status': 'success'
            }
            
            if 'migration_history' not in config:
                config['migration_history'] = []
            config['migration_history'].append(migration_record)
            
            self.save_config(config)
            
            # 5. 验证升级结果
            self.verify_upgrade(latest_migration_version)
            
            logger.info(f"数据库升级成功，已从版本 {current_db_version} 升级到 {latest_migration_version}")
            return True
            
        except Exception as e:
            logger.error(f"数据库升级失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 尝试恢复备份
            self.restore_from_backup()
            return False
    
    def backup_database(self):
        """备份当前数据库"""
        logger.info("备份当前数据库...")
        
        config = self.load_config()
        db_path = config.get('database_path', self.default_db_path)
        
        if not os.path.exists(db_path):
            logger.warning(f"数据库文件不存在: {db_path}")
            return None
        
        backup_file = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(self.backups_dir, backup_file)
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"数据库已备份到: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"备份数据库失败: {str(e)}")
            return None
    
    def restore_from_backup(self):
        """从备份恢复数据库"""
        logger.info("尝试从备份恢复数据库...")
        
        config = self.load_config()
        db_path = config.get('database_path', self.default_db_path)
        
        # 查找最新的备份文件
        backup_files = [f for f in os.listdir(self.backups_dir) if f.endswith('.db')]
        if not backup_files:
            logger.error("没有找到可用的数据库备份")
            return False
        
        # 按修改时间排序，获取最新备份
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.backups_dir, x)), reverse=True)
        latest_backup = backup_files[0]
        backup_path = os.path.join(self.backups_dir, latest_backup)
        
        try:
            # 关闭可能的数据库连接
            time.sleep(1)
            
            # 恢复备份
            shutil.copy2(backup_path, db_path)
            logger.info(f"已从备份 {latest_backup} 恢复数据库")
            return True
        except Exception as e:
            logger.error(f"从备份恢复数据库失败: {str(e)}")
            return False
    
    def execute_migrations(self, from_version, to_version):
        """执行迁移脚本"""
        logger.info(f"执行数据库迁移，从版本 {from_version} 到 {to_version}...")
        
        config = self.load_config()
        db_path = config.get('database_path', self.default_db_path)
        
        # 获取所有迁移脚本并排序
        migration_files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        migration_files.sort()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            for migration_file in migration_files:
                # 从文件名中提取版本号
                migration_version = self.get_migration_file_version(migration_file)
                
                # 只执行版本号大于当前数据库版本的迁移脚本
                if self.is_newer_version(migration_version, from_version):
                    migration_path = os.path.join(self.migrations_dir, migration_file)
                    logger.info(f"执行迁移脚本: {migration_file}")
                    
                    # 读取并执行迁移脚本
                    with open(migration_path, 'r') as f:
                        sql_commands = f.read()
                    
                    # 执行所有SQL命令
                    cursor.executescript(sql_commands)
                    conn.commit()
                    
                    logger.info(f"迁移脚本 {migration_file} 执行成功")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"执行迁移脚本失败: {str(e)}")
            conn.rollback()
            conn.close()
            raise
    
    def get_migration_file_version(self, migration_file):
        """从迁移文件名中提取版本号"""
        try:
            version_num = int(migration_file.split('_')[0])
            return f"{version_num}.0.0"
        except Exception as e:
            logger.error(f"提取迁移文件版本失败: {str(e)}")
            return '1.0.0'
    
    def update_db_version(self, version):
        """更新数据库版本记录"""
        logger.info(f"更新数据库版本记录为: {version}")
        
        config = self.load_config()
        db_path = config.get('database_path', self.default_db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 插入新版本记录
            cursor.execute("""
            INSERT INTO system_version (version, created_at, updated_at, description)
            VALUES (?, ?, ?, ?)
            """, (version, datetime.now().isoformat(), datetime.now().isoformat(), f"自动升级到版本 {version}"))
            
            conn.commit()
            conn.close()
            
            logger.info(f"数据库版本记录已更新为: {version}")
            
        except Exception as e:
            logger.error(f"更新数据库版本记录失败: {str(e)}")
            raise
    
    def verify_upgrade(self, version):
        """验证升级结果"""
        logger.info(f"验证数据库升级结果，版本: {version}")
        
        config = self.load_config()
        db_path = config.get('database_path', self.default_db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 验证关键表是否存在
            key_tables = ['color_schemes', 'layout_schemes', 'system_version']
            for table in key_tables:
                cursor.execute(f"""SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';""")
                if not cursor.fetchone():
                    conn.close()
                    raise Exception(f"关键表 {table} 不存在，升级失败")
                logger.info(f"表 {table} 验证通过")
            
            # 验证版本记录是否正确
            cursor.execute("""SELECT version FROM system_version ORDER BY id DESC LIMIT 1;""")
            result = cursor.fetchone()
            if not result or result[0] != version:
                conn.close()
                raise Exception(f"版本记录不正确，预期: {version}, 实际: {result[0] if result else 'None'}")
            
            conn.close()
            logger.info("数据库升级验证全部通过")
            
        except Exception as e:
            logger.error(f"验证数据库升级失败: {str(e)}")
            raise
    
    def create_new_migration(self, description):
        """创建新的迁移脚本"""
        logger.info(f"创建新的迁移脚本: {description}")
        
        # 获取当前最大迁移脚本编号
        migration_files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        max_num = 0
        
        for f in migration_files:
            try:
                num = int(f.split('_')[0])
                if num > max_num:
                    max_num = num
            except Exception as e:
                logger.error(f"解析迁移文件名失败: {f}, 错误: {str(e)}")
        
        # 创建新的迁移脚本
        new_num = max_num + 1
        new_filename = f"{new_num:03d}_{description.replace(' ', '_')}.sql"
        new_path = os.path.join(self.migrations_dir, new_filename)
        
        with open(new_path, 'w') as f:
            f.write(f"-- 迁移脚本 {new_num}.0.0\n-- 描述: {description}\n-- 创建时间: {datetime.now().isoformat()}\n\n")
        
        logger.info(f"已创建新的迁移脚本: {new_path}")
        return new_path
    
    def manual_upgrade(self):
        """手动触发升级"""
        logger.info("手动触发数据库升级...")
        return self.run_upgrade()


def main():
    """主函数"""
    upgrader = AutoDBUpgrader()
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=upgrader.start_upgrade_monitor, args=(86400,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    logger.info("数据库自动升级系统已启动，按Ctrl+C停止")
    
    try:
        # 主线程保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        upgrader.stop()
        monitor_thread.join(timeout=5)


if __name__ == "__main__":
    main()

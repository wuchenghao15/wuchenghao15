# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则决策自动升级系统
自动管理和升级系统中的规则和决策逻辑
"""
import os
import logging
import json
import time
from datetime import datetime
import shutil
import threading
import sqlite3
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_rule_upgrade.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoRuleUpgrader:
    def __init__(self):
        self.running = True
        self.rule_config_file = 'rule_config.json'
        self.rules_dir = 'rules'
        self.backups_dir = 'rule_backups'
        self.db_path = 'rule_database.db'

        self.init_config()

    def init_config(self):
        if not os.path.exists(self.rule_config_file):
            default_config = {
                'current_version': '1.0.0',
                'last_upgraded': datetime.now().isoformat(),
                'upgrade_check_interval': 86400,
                'rule_types': [
                    'color_selection_rules',
                    'layout_generation_rules',
                    'security_rules',
                    'upgrade_rules',
                    'decision_rules'
                ],
                'auto_upgrade_enabled': True,
                'upgrade_history': []
            }
            with open(self.rule_config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"已创建默认规则配置文件: {self.rule_config_file}")

        if not os.path.exists(self.rules_dir):
            os.makedirs(self.rules_dir)
            logger.info(f"已创建规则目录: {self.rules_dir}")

        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)
            logger.info(f"已创建备份目录: {self.backups_dir}")

        self.init_rule_database()

        self.create_initial_rules()

    def init_rule_database(self):
        logger.info("初始化规则数据库...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT UNIQUE,
            rule_type TEXT,
            rule_content TEXT,
            version TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_active INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 0
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rule_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER,
            version TEXT,
            rule_content TEXT,
            created_at TEXT,
            FOREIGN KEY (rule_id) REFERENCES rules (id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rule_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER,
            execution_time TEXT,
            result TEXT,
            status TEXT,
            FOREIGN KEY (rule_id) REFERENCES rules (id)
        )
        ''')

        conn.commit()
        conn.close()

        logger.info(f"规则数据库已初始化: {self.db_path}")

    def create_initial_rules(self):
        color_rules = {
            "name": "color_selection_rules",
            "type": "color_selection",
            "version": "1.0.0",
            "rules": [
                {
                    "name": "complementary_colors",
                    "description": "选择互补色配色方案",
                    "priority": 1,
                    "condition": "if color_count >= 4",
                    "action": "select complementary color scheme"
                },
                {
                    "name": "monochromatic_colors",
                    "description": "选择单色配色方案",
                    "priority": 2,
                    "condition": "if color_count < 4",
                    "action": "select monochromatic color scheme"
                }
            ]
        }

        layout_rules = {
            "name": "layout_generation_rules",
            "type": "layout_generation",
            "version": "1.0.0",
            "rules": [
                {
                    "name": "responsive_layout",
                    "description": "生成响应式布局",
                    "priority": 1,
                    "condition": "always",
                    "action": "generate responsive layout with Tailwind CSS"
                },
                {
                    "name": "mobile_first",
                    "description": "采用移动优先设计",
                    "priority": 2,
                    "condition": "always",
                    "action": "use mobile-first design approach"
                }
            ]
        }

        security_rules = {
            "name": "security_rules",
            "type": "security",
            "version": "1.0.0",
            "rules": [
                {
                    "name": "input_validation",
                    "description": "验证所有用户输入",
                    "priority": 1,
                    "condition": "on user input",
                    "action": "validate input against security rules"
                },
                {
                    "name": "rate_limiting",
                    "description": "限制请求速率",
                    "priority": 2,
                    "condition": "on request",
                    "action": "apply rate limiting"
                }
            ]
        }

        self.save_rule_to_file(color_rules)
        self.save_rule_to_file(layout_rules)
        self.save_rule_to_file(security_rules)

        self.save_rule_to_database(color_rules)
        self.save_rule_to_database(layout_rules)
        self.save_rule_to_database(security_rules)
        logger.info("初始规则已创建")

    def save_rule_to_file(self, rule_data):
        rule_file = os.path.join(self.rules_dir, f"{rule_data['name']}.json")
        with open(rule_file, 'w') as f:
            json.dump(rule_data, f, indent=2)

    def save_rule_to_database(self, rule_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM rules WHERE rule_name = ?", (rule_data['name'],))
        existing_rule = cursor.fetchone()

        if existing_rule:
            cursor.execute('''
            UPDATE rules SET rule_type = ?, rule_content = ?, version = ?, updated_at = ?, is_active = 1
            WHERE id = ?
            ''', (rule_data['type'], str(rule_data), rule_data['version'], datetime.now().isoformat(), existing_rule[0]))

            cursor.execute('''
            INSERT INTO rule_versions (rule_id, version, rule_content, created_at)
            VALUES (?, ?, ?, ?)
            ''', (existing_rule[0], rule_data['version'], str(rule_data), datetime.now().isoformat()))

            logger.info(f"已更新规则: {rule_data['name']} 到版本 {rule_data['version']}")
        else:
            cursor.execute('''
            INSERT INTO rules (rule_name, rule_type, rule_content, version, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (rule_data['name'], rule_data['type'], str(rule_data), rule_data['version'], datetime.now().isoformat(), datetime.now().isoformat()))

            rule_id = cursor.lastrowid

            cursor.execute('''
            INSERT INTO rule_versions (rule_id, version, rule_content, created_at)
            VALUES (?, ?, ?, ?)
            ''', (rule_id, rule_data['version'], str(rule_data), datetime.now().isoformat()))

            logger.info(f"已创建新规则: {rule_data['name']} 版本 {rule_data['version']}")

        conn.commit()
        conn.close()

    def load_config(self):
        try:
            with open(self.rule_config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则配置失败: {str(e)}")
            return {
                'current_version': '1.0.0',
                'last_upgraded': datetime.now().isoformat(),
                'upgrade_check_interval': 86400,
                'rule_types': [
                    'color_selection_rules',
                    'layout_generation_rules',
                    'security_rules',
                    'decision_rules'
                ],
                'auto_upgrade_enabled': True,
                'upgrade_history': []
            }

    def save_config(self, config):
        try:
            with open(self.rule_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"已保存规则配置到 {self.rule_config_file}")
        except Exception as e:
            logger.error(f"保存规则配置失败: {str(e)}")

    def start_upgrade_monitor(self, interval=86400):
        logger.info("启动规则决策自动升级监控...")
        while self.running:
            try:
                if self.should_upgrade():
                    logger.info("开始规则决策自动升级...")
                    self.run_upgrade()
                else:
                    logger.info("规则决策版本已是最新,无需升级")

                time.sleep(interval)
            except Exception as e:
                logger.error(f"升级监控发生错误: {str(e)}")
                import traceback
                traceback.print_exc()

        logger.info("规则决策自动升级监控已停止")

    def stop(self, signum=None, frame=None):
        logger.info("正在停止规则决策自动升级监控...")
        self.running = False

    def should_upgrade(self):
        config = self.load_config()

        if not config.get('auto_upgrade_enabled', True):
            logger.info("规则决策自动升级已禁用")
            return False

        last_upgraded = datetime.fromisoformat(config.get('last_upgraded', datetime.now().isoformat()))
        interval = config.get('upgrade_check_interval', 86400)

        if (datetime.now() - last_upgraded).total_seconds() < interval:
            logger.debug(f"距离上次升级时间不足 {interval} 秒,跳过升级检查")
            return False

        current_version = config.get('current_version', '1.0.0')
        latest_version = self.get_latest_version()

        if latest_version and self.is_newer_version(latest_version, current_version):
            logger.info(f"发现新版本: {latest_version} (当前版本: {current_version})")
            return True

        return False

    def get_latest_version(self):
        logger.info("检查最新规则决策版本...")

        try:
            return '2.0.0'
        except Exception as e:
            logger.error(f"获取最新版本失败: {str(e)}")
            return None

    def is_newer_version(self, latest, current):
        try:
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))

            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False

            return len(latest_parts) > len(current_parts)
        except Exception as e:
            logger.error(f"版本比较失败: {str(e)}")
            return False

    def run_upgrade(self):
        logger.info("开始执行规则决策升级...")

        config = self.load_config()
        current_version = config.get('current_version', '1.0.0')
        latest_version = self.get_latest_version()

        if not latest_version:
            logger.error("无法获取最新版本,升级失败")
            return False

        try:
            backup_path = self.backup_rules()

            self.download_and_install_rules(latest_version)

            config['current_version'] = latest_version
            config['last_upgraded'] = datetime.now().isoformat()

            upgrade_record = {
                'from_version': current_version,
                'to_version': latest_version,
                'upgraded_at': datetime.now().isoformat(),
                'backup_path': backup_path,
                'status': 'success'
            }

            if 'upgrade_history' not in config:
                config['upgrade_history'] = []
            config['upgrade_history'].append(upgrade_record)

            self.save_config(config)

            self.verify_upgrade(latest_version)

            logger.info(f"规则决策升级成功,已从版本 {current_version} 升级到 {latest_version}")
            return True

        except Exception as e:
            logger.error(f"规则决策升级失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def backup_rules(self):
        backup_file = f"rule_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backups_dir, backup_file)

        if os.path.exists(self.rules_dir):
            rule_files_backup = os.path.join(backup_path, 'rule_files')
            shutil.copytree(self.rules_dir, rule_files_backup)

        db_backup = os.path.join(self.backups_dir, f"rule_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, db_backup)
        return self.backups_dir

    def restore_from_backup(self, backup_path):
        logger.info("尝试从备份恢复规则...")

        if not backup_path or not os.path.exists(backup_path):
            logger.error(f"备份目录不存在: {backup_path}")
            return False

        rule_backups = sorted([d for d in os.listdir(backup_path) if d.startswith('rule_files_')], reverse=True)
        if rule_backups:
            latest_rule_backup = os.path.join(backup_path, rule_backups[0])
            try:
                if os.path.exists(self.rules_dir):
                    shutil.rmtree(self.rules_dir)
                os.makedirs(self.rules_dir)
                for file in os.listdir(latest_rule_backup):
                    shutil.copy2(os.path.join(latest_rule_backup, file), os.path.join(self.rules_dir, file))
                logger.info("已从备份恢复规则文件")
            except Exception as e:
                logger.error(f"恢复规则文件失败: {str(e)}")

        db_backups = sorted([f for f in os.listdir(backup_path) if f.startswith('rule_db_') and f.endswith('.db')], reverse=True)
        if db_backups:
            latest_db_backup = os.path.join(backup_path, db_backups[0])
            try:
                shutil.copy2(latest_db_backup, self.db_path)
                logger.info("已从备份恢复规则数据库")
            except Exception as e:
                logger.error(f"恢复规则数据库失败: {str(e)}")
        logger.info("规则恢复完成")

    def download_and_install_rules(self, version):
        logger.info(f"下载并安装规则版本 {version}...")

        updated_rules = [
            {
                "name": "color_selection_rules",
                "type": "color_selection",
                "version": version,
                "rules": [
                    {
                        "name": "complementary_colors",
                        "description": "选择互补色配色方案",
                        "priority": 1,
                        "condition": "if color_count >= 4",
                        "action": "select complementary color scheme"
                    },
                    {
                        "name": "monochromatic_colors",
                        "description": "选择单色配色方案",
                        "priority": 2,
                        "condition": "if color_count < 4",
                        "action": "select monochromatic color scheme"
                    },
                    {
                        "name": "triadic_colors",
                        "description": "选择三色配色方案",
                        "priority": 3,
                        "condition": "if color_count >= 3",
                        "action": "select triadic color scheme"
                    }
                ]
            },
            {
                "name": "layout_generation_rules",
                "type": "layout_generation",
                "version": version,
                "rules": [
                    {
                        "name": "responsive_layout",
                        "description": "生成响应式布局",
                        "priority": 1,
                        "condition": "always",
                        "action": "generate responsive layout with Tailwind CSS"
                    },
                    {
                        "name": "mobile_first",
                        "description": "采用移动优先设计",
                        "priority": 2,
                        "condition": "always",
                        "action": "use mobile-first design approach"
                    },
                    {
                        "name": "minimalist_design",
                        "description": "采用简约设计",
                        "priority": 3,
                        "condition": "always",
                        "action": "use minimalist design principles"
                    }
                ]
            },
            {
                "name": "security_rules",
                "type": "security",
                "version": version,
                "rules": [
                    {
                        "name": "input_validation",
                        "description": "验证所有用户输入",
                        "priority": 1,
                        "condition": "on user input",
                        "action": "validate input against security rules"
                    },
                    {
                        "name": "rate_limiting",
                        "description": "限制请求速率",
                        "priority": 2,
                        "condition": "on request",
                        "action": "apply rate limiting"
                    },
                    {
                        "name": "csrf_protection",
                        "description": "CSRF保护",
                        "priority": 3,
                        "condition": "on form submission",
                        "action": "add CSRF token to form"
                    }
                ]
            }
        ]

        for rule in updated_rules:
            self.save_rule_to_file(rule)
            self.save_rule_to_database(rule)
        logger.info(f"规则版本 {version} 安装完成")

    def verify_upgrade(self, version):
        logger.info(f"验证规则决策升级结果,版本: {version}")
        rule_files = os.listdir(self.rules_dir)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rules WHERE version = ?", (version,))
        rule_count = cursor.fetchone()[0]
        conn.close()

        if rule_count > 0:
            logger.info(f"验证成功,数据库中有 {rule_count} 条版本为 {version} 的规则")
        else:
            logger.error(f"数据库中没有版本为 {version} 的规则,验证失败")
            raise Exception(f"数据库中没有版本为 {version} 的规则")


    def get_active_rules(self, rule_type=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if rule_type:
            cursor.execute("SELECT * FROM rules WHERE rule_type = ? AND is_active = 1 ORDER BY priority DESC", (rule_type,))
        else:
            cursor.execute("SELECT * FROM rules WHERE is_active = 1 ORDER BY priority DESC")
        rules = cursor.fetchall()
        conn.close()
        return rules


    def execute_rule(self, rule_name, data):
        logger.info(f"执行规则: {rule_name},数据: {data}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules WHERE rule_name = ? AND is_active = 1", (rule_name,))
        rule = cursor.fetchone()

        if not rule:
            logger.error(f"规则 {rule_name} 不存在或未激活")
            conn.close()
            return None


        try:
            result = {
                "rule_id": rule[0],
                "rule_name": rule[1],
                "rule_type": rule[2],
                "version": rule[4],
                "output": f"规则 {rule_name} 执行成功,处理数据: {data}",
                "timestamp": datetime.now().isoformat()
            }
            cursor.execute('''
            INSERT INTO rule_execution_logs (rule_id, execution_time, result, status)
            VALUES (?, ?, ?, ?)
            ''', (rule[0], datetime.now().isoformat(), str(result), "success"))

            conn.commit()
        except Exception as e:
            logger.error(f"执行规则 {rule_name} 失败: {str(e)}")
            cursor.execute('''
            INSERT INTO rule_execution_logs (rule_id, execution_time, result, status)
            VALUES (?, ?, ?, ?)
            ''', (rule[0], datetime.now().isoformat(), str(e), "error"))
            conn.commit()
            result = None

        conn.close()
        return result

    def manual_upgrade(self):
        logger.info("手动触发规则决策升级...")
        return self.run_upgrade()

def main():
    upgrader = AutoRuleUpgrader()

    monitor_thread = threading.Thread(target=upgrader.start_upgrade_monitor, args=(86400,))
    monitor_thread.start()

    logger.info("规则决策自动升级系统已启动,按Ctrl+C停止")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        upgrader.stop()
        monitor_thread.join(timeout=5)


if __name__ == "__main__":
    main()

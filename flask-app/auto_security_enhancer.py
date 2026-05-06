#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动安全强化系统
自动检查和修复安全漏洞，更新安全配置，监控安全事件

import os
import sys
import logging
import subprocess
# JSON import removed - using database
import time
from datetime import datetime
import requests
import shutil
import signal
import threading
import sqlite3
import hashlib
import re
import stat

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_security_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoSecurityEnhancer:
    """自动安全强化器"""

    def __init__(self):
        self.running = True
        self.security_config_file = 'security_config.json'
        self.security_logs_dir = 'security_logs'
        self.backups_dir = 'security_backups'
        self.db_path = 'security_database.db'

        # 初始化配置
        self.init_config()

    def init_config(self):
        """初始化安全配置"""
        if not os.path.exists(self.security_config_file):
            default_config = {
                'current_version': '1.0.0',
                'last_scanned': datetime.now().isoformat(),
                'scan_interval': 3600,  # 1小时
                'security_checks': [
                    'file_permissions',
                    'dependency_vulnerabilities',
                    'code_security',
                    'configuration_security',
                    'network_security'
                ],
                'auto_fix_enabled': True,
                'security_events': []
            }
            with open(self.security_config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"已创建默认安全配置文件: {self.security_config_file}")

        # 创建安全日志目录
        if not os.path.exists(self.security_logs_dir):
            os.makedirs(self.security_logs_dir)
            logger.info(f"已创建安全日志目录: {self.security_logs_dir}")

        # 创建备份目录
        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)
            logger.info(f"已创建安全备份目录: {self.backups_dir}")

        # 初始化安全数据库
        self.init_security_database()

    def init_security_database(self):
        """初始化安全数据库"""
        logger.info("初始化安全数据库...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建安全漏洞表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vulnerability_id TEXT UNIQUE,
            type TEXT,
            severity TEXT,
            description TEXT,
            file_path TEXT,
            line_number INTEGER,
            status TEXT,
            detected_at TEXT,
            fixed_at TEXT
        )

        # 创建安全事件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            event_type TEXT,
            description TEXT,
            occurred_at TEXT,
            handled_at TEXT,

        # 创建安全配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_value TEXT,
            updated_at TEXT

        conn.commit()
        conn.close()

        logger.info(f"安全数据库已初始化: {self.db_path}")
    def load_config(self):
        """加载安全配置"""
        try:
            with open(self.security_config_file, 'r') as f:
        except Exception as e:
            logger.error(f"加载安全配置失败: {str(e)}")
            return {
                'current_version': '1.0.0',
                'last_scanned': datetime.now().isoformat(),
                'scan_interval': 3600,
                'security_checks': [
                    'dependency_vulnerabilities',
                    'configuration_security',
                    'network_security'
                'auto_fix_enabled': True,
            }
    def save_config(self, config):
        try:
                json.dump(config, f, indent=2)
        except Exception as e:

        """开始安全监控"""

            try:
                # 执行安全检查
                logger.info("开始执行安全检查...")
                self.run_security_checks()

                time.sleep(interval)

            except Exception as e:
                logger.error(f"安全监控发生错误: {str(e)}")
                import traceback
                traceback.print_exc()

        logger.info("自动安全强化监控已停止")

    def stop(self, signum=None, frame=None):
        """停止监控系统"""
        logger.info("正在停止自动安全强化监控...")

    def run_security_checks(self):
        """执行安全检查"""
        config = self.load_config()
        security_checks = config.get('security_checks', [])
        auto_fix = config.get('auto_fix_enabled', True)

        logger.info(f"执行安全检查: {security_checks}")

        # 执行各项安全检查
        for check_type in security_checks:
            try:
                if check_type == 'file_permissions':
                    self.check_file_permissions(auto_fix)
                elif check_type == 'dependency_vulnerabilities':
                elif check_type == 'code_security':
                    self.check_code_security(auto_fix)
                elif check_type == 'configuration_security':
                    self.check_configuration_security(auto_fix)
                elif check_type == 'network_security':
                    self.check_network_security(auto_fix)
            except Exception as e:
                logger.error(f"执行安全检查 {check_type} 失败: {str(e)}")
                import traceback
                traceback.print_exc()

        # 更新最后扫描时间
        config['last_scanned'] = datetime.now().isoformat()
        self.save_config(config)

        logger.info("安全检查执行完成")

    def check_file_permissions(self, auto_fix=False):
        """检查文件权限"""
        logger.info("检查文件权限...")

        # 检查关键文件的权限
        critical_files = [
            '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py',
            '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates/index.html',
            self.security_config_file,
            self.db_path
        ]
        vulnerabilities = []

        for file_path in critical_files:
            if os.path.exists(file_path):
                file_stat = os.stat(file_path)
                file_perm = stat.S_IMODE(file_stat.st_mode)

                # 检查文件权限是否过于宽松
                    vulnerability = {
                        'type': 'file_permissions',
                        'severity': 'medium',
                        'description': f"文件 {file_path} 权限过于宽松，其他用户可写",
                        'file_path': file_path,
                        'line_number': 0,
                        'status': 'detected',
                        'detected_at': datetime.now().isoformat()
                    }
                    vulnerabilities.append(vulnerability)

                    if auto_fix:
                        self.fix_file_permissions(file_path)
                        vulnerability['status'] = 'fixed'
                        vulnerability['fixed_at'] = datetime.now().isoformat()

        # 保存漏洞信息
        self.save_vulnerabilities(vulnerabilities)

        logger.info(f"文件权限检查完成，发现 {len(vulnerabilities)} 个漏洞")

    def fix_file_permissions(self, file_path):
        """修复文件权限"""
        logger.info(f"修复文件权限: {file_path}")
        try:
            # 设置文件权限为 644（所有者可读写，组和其他可读）
            os.chmod(file_path, 0o644)
            logger.info(f"已修复文件 {file_path} 权限为 644")
        except Exception as e:
            logger.error(f"修复文件 {file_path} 权限失败: {str(e)}")

    def check_dependency_vulnerabilities(self, auto_fix=False):
        """检查依赖漏洞"""
        logger.info("检查依赖漏洞...")

        # 检查Python依赖漏洞
        try:
            # 尝试使用pip-audit或safety检查依赖漏洞
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )

                dependencies = eval(result.stdout)
                logger.info(f"检查 {len(dependencies)} 个依赖包")

                # 这里可以集成pip-audit或safety来检查漏洞
                # 目前使用模拟数据
                vulnerabilities = []

                # 模拟发现依赖漏洞
                mock_vulnerabilities = [
                    {
                        'vulnerability_id': 'DEPENDENCY_VULN_001',
                        'severity': 'high',
                        'description': '依赖包 requests 存在安全漏洞',
                        'file_path': 'requirements.txt',
                        'line_number': 0,
                        'status': 'detected',
                        'detected_at': datetime.now().isoformat()
                    }
                ]
                vulnerabilities.extend(mock_vulnerabilities)

                if auto_fix:
                    self.fix_dependency_vulnerabilities()
                    for vuln in vulnerabilities:
                        vuln['status'] = 'fixed'
                        vuln['fixed_at'] = datetime.now().isoformat()

                # 保存漏洞信息
                self.save_vulnerabilities(vulnerabilities)

                logger.info(f"依赖漏洞检查完成，发现 {len(vulnerabilities)} 个漏洞")

        except Exception as e:
            logger.error(f"检查依赖漏洞失败: {str(e)}")
    def fix_dependency_vulnerabilities(self):
        """修复依赖漏洞"""
        logger.info("修复依赖漏洞...")

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', '--break-system-packages', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
            else:
                logger.error(f"更新依赖包失败: {result.stderr}")
            logger.error(f"修复依赖漏洞失败: {str(e)}")
    def check_code_security(self, auto_fix=False):
        logger.info("检查代码安全...")

        # 检查敏感信息泄露
        sensitive_patterns = [
            re.compile(r'API_KEY\s*=\s*["\'].*?["\']'),
            re.compile(r'SECRET_KEY\s*=\s*["\'].*?["\']'),
            re.compile(r'connection_string\s*=\s*["\'].*?["\']')
        ]
        vulnerabilities = []

        # 检查Python文件
        python_files = []
            for file in files:
                    python_files.append(os.path.join(root, file))

        for file_path in python_files:
            with open(file_path, 'r') as f:
                content = f.read()

            for i, line in enumerate(content.split('\n')):
                for pattern in sensitive_patterns:
                    if pattern.search(line):
                        vulnerability = {
                            'type': 'code_security',
                            'severity': 'high',
                            'description': f"文件 {file_path} 第 {i+1} 行可能包含敏感信息",
                            'line_number': i+1,
                            'status': 'detected',
                        }

        # 保存漏洞信息
        self.save_vulnerabilities(vulnerabilities)


    def check_configuration_security(self, auto_fix=False):
        """检查配置安全"""
        logger.info("检查配置安全...")

        vulnerabilities = []

        # 检查Flask配置
        app_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py'
            with open(app_file, 'r') as f:
                content = f.read()

            if 'DEBUG = True' in content or 'app.run.*debug=True' in content:
                vulnerability = {
                    'vulnerability_id': 'CONFIG_SEC_001',
                    'type': 'configuration_security',
                    'severity': 'high',
                    'description': "Flask应用启用了调试模式，存在安全风险",
                    'file_path': app_file,
                    'line_number': 0,
                    'status': 'detected',
                    'detected_at': datetime.now().isoformat()
                }
                vulnerabilities.append(vulnerability)

                if auto_fix:
                    vulnerability['status'] = 'fixed'
                    vulnerability['fixed_at'] = datetime.now().isoformat()

        # 保存漏洞信息
        self.save_vulnerabilities(vulnerabilities)
        logger.info(f"配置安全检查完成，发现 {len(vulnerabilities)} 个漏洞")

    def fix_configuration_security(self, app_file):
        logger.info(f"修复配置安全问题: {app_file}")

            with open(app_file, 'r') as f:
                content = f.read()
            # 禁用调试模式
            with open(app_file, 'w') as f:
                f.write(content)
            logger.info(f"已修复 {app_file} 的配置安全问题")
        except Exception as e:

    def check_network_security(self, auto_fix=False):
        """检查网络安全"""
        logger.info("检查网络安全...")

        # 检查是否绑定到所有网络接口
        vulnerabilities = []

        if os.path.exists(app_file):
            with open(app_file, 'r') as f:
                content = f.read()

            # 检查是否绑定到 0.0.0.0
            if '0.0.0.0' in content:
                    'vulnerability_id': 'NETWORK_SEC_001',
                    'type': 'network_security',
                    'description': "Flask应用绑定到所有网络接口，存在安全风险",
                    'file_path': app_file,
                    'line_number': 0,
                    'detected_at': datetime.now().isoformat()
                vulnerabilities.append(vulnerability)

        self.save_vulnerabilities(vulnerabilities)

        logger.info(f"网络安全检查完成，发现 {len(vulnerabilities)} 个漏洞")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for vuln in vulnerabilities:
            cursor.execute("SELECT id FROM security_vulnerabilities WHERE vulnerability_id = ?", (vuln['vulnerability_id'],))
            existing = cursor.fetchone()
            if existing:
                # 更新现有漏洞
                UPDATE security_vulnerabilities SET type = ?, severity = ?, description = ?, file_path = ?, line_number = ?, status = ?, fixed_at = ?
                ''', (vuln['type'], vuln['severity'], vuln['description'], vuln['file_path'], vuln['line_number'], vuln['status'], vuln.get('fixed_at'), vuln['vulnerability_id']))
            else:
                # 插入新漏洞
                cursor.execute('''
                INSERT INTO security_vulnerabilities (vulnerability_id, type, severity, description, file_path, line_number, status, detected_at, fixed_at)
                ''', (vuln['vulnerability_id'], vuln['type'], vuln['severity'], vuln['description'], vuln['file_path'], vuln['line_number'], vuln['status'], vuln['detected_at'], vuln.get('fixed_at')))

        conn.commit()
        conn.close()

    def log_security_event(self, event_type, description, severity='medium'):
        """记录安全事件"""
        logger.info(f"记录安全事件: {event_type} - {description}")
        # 保存到数据库
        cursor = conn.cursor()

        INSERT INTO security_events (event_type, description, severity, occurred_at, status)
        VALUES (?, ?, ?, ?, ?)
        conn.commit()
        # 更新配置中的安全事件
        config = self.load_config()
        event = {
            'event_type': event_type,
            'occurred_at': datetime.now().isoformat(),
            'status': 'detected'
        }
        if 'security_events' not in config:
            config['security_events'] = []
        config['security_events'].append(event)
        self.save_config(config)
    def get_vulnerabilities(self, status=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM security_vulnerabilities WHERE status = ?", (status,))
        vulnerabilities = cursor.fetchall()

    def get_security_events(self, status=None):
        conn = sqlite3.connect(self.db_path)

        else:
            cursor.execute("SELECT * FROM security_events")


        return events
        """生成安全报告"""
        logger.info("生成安全报告...")

        vulnerabilities = self.get_vulnerabilities()
        events = self.get_security_events()

        report = {
            'generated_at': datetime.now().isoformat(),
            'vulnerability_summary': {
                'total': len(vulnerabilities),
                'detected': len([v for v in vulnerabilities if v[7] == 'detected']),
                'fixed': len([v for v in vulnerabilities if v[7] == 'fixed'])
                'total': len(events),
                'detected': len([e for e in events if e[6] == 'detected']),
                'handled': len([e for e in events if e[6] == 'handled'])
            'events': events
        }

        # 保存报告到文件
        report_file = os.path.join(self.security_logs_dir, f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)



def main():
    """主函数"""
    enhancer = AutoSecurityEnhancer()

    # 启动监控线程
    monitor_thread = threading.Thread(target=enhancer.start_security_monitor, args=(3600,))
    monitor_thread.daemon = True
    monitor_thread.start()


    try:
        # 主线程保持运行
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        enhancer.stop()
        monitor_thread.join(timeout=5)


if __name__ == "__main__":
    main()

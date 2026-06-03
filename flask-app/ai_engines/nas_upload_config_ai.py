# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NAS上传配置AI - 负责上传项目并完成配置到飞牛NAS服务器,最后共享错误修复案例到脑库使AI共享学习
"""

import os
import sqlite3
from contextlib import contextmanager
import json
import time
import logging
import ftplib
import shutil
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nas_upload_config_ai')

class NASUploadConfigAI:
    """NAS上传配置AI"""

    def __init__(self):
        self.ai_id = f"nas-upload-config-ai-{int(time.time())}"
        self.name = "NAS上传配置AI"
        self.description = "负责上传项目并完成配置到飞牛NAS服务器,最后共享错误修复案例到脑库使AI共享学习"
        self.created_at = datetime.now().isoformat()
        self.nas_config = {
            'server': 'wuchenghao15.fnos.net',
            'username': 'wuchenghao15',
            'password': '!+.557KKZBchno',
            'remote_path': '/MTSCOS_AI_Project'
        }
        logger.info(f"新建NAS上传配置AI: {self.ai_id}")

    def prepare_project(self):
        """准备项目文件"""
        logger.info("=== 开始准备项目文件 ===")

        try:
            project_files = []
            project_root = '.'

            for root, dirs, files in os.walk(project_root):
                excluded_dirs = ['__pycache__', '.git', 'venv', 'env', 'node_modules']
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                for file in files:
                    if not (file.endswith('.pyc') or file.endswith('.log') or file.startswith('.')):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_root)
                        project_files.append({
                            'local_path': file_path,
                            'relative_path': relative_path,
                            'size': os.path.getsize(file_path)
                        })

            logger.info(f"项目文件准备完成,共 {len(project_files)} 个文件")
            return project_files

        except Exception as e:
            logger.error(f"项目文件准备失败: {str(e)}")
            return []

    def upload_to_nas(self, project_files):
        """上传项目到NAS服务器"""
        logger.info("=== 开始上传项目到NAS服务器 ===")

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                logger.info(f"尝试连接到NAS服务器: {self.nas_config['server']}")
                ftp = ftplib.FTP(self.nas_config['server'])
                logger.info("成功连接到服务器,正在登录...")
                ftp.login(self.nas_config['username'], self.nas_config['password'])
                logger.info("成功登录到NAS服务器")

                try:
                    ftp.mkd(self.nas_config['remote_path'])
                    logger.info(f"创建远程目录: {self.nas_config['remote_path']}")
                except ftplib.error_perm as e:
                    if '550' in str(e):
                        logger.info(f"远程目录已存在: {self.nas_config['remote_path']}")
                    else:
                        logger.error(f"创建远程目录失败: {str(e)}")
                        ftp.quit()
                        retry_count += 1
                        continue

                uploaded_files = []
                for file_info in project_files:
                    remote_file_path = f"{self.nas_config['remote_path']}/{file_info['relative_path']}"

                    remote_dir = os.path.dirname(remote_file_path)
                    dirs = remote_dir.split('/')
                    current_path = ''

                    for dir_name in dirs:
                        if dir_name:
                            current_path += f"/{dir_name}"
                            try:
                                ftp.mkd(current_path)
                            except ftplib.error_perm:
                                pass

                    try:
                        with open(file_info['local_path'], 'rb') as f:
                            ftp.storbinary(f'STOR {remote_file_path}', f)
                        uploaded_files.append(file_info)
                    except Exception as e:
                        logger.error(f"上传文件失败 {file_info['relative_path']}: {str(e)}")

                ftp.quit()

                logger.info(f"项目上传完成,成功上传 {len(uploaded_files)} 个文件")
                return {'status': 'ok', 'uploaded_files': uploaded_files, 'total_files': len(project_files)}

            except Exception as e:
                retry_count += 1
                logger.error(f"上传到NAS服务器失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    logger.info(f"等待3秒后重试...")
                    time.sleep(3)
                else:
                    logger.error("达到最大重试次数,上传失败")
                    return {'status': 'error', 'message': str(e), 'retry_count': retry_count}

    def configure_nas_project(self):
        """配置NAS上的项目"""
        logger.info("=== 开始配置NAS上的项目 ===")
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                logger.info(f"尝试连接到NAS服务器: {self.nas_config['server']}")
                ftp = ftplib.FTP(self.nas_config['server'])
                ftp.login(self.nas_config['username'], self.nas_config['password'])

                config_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# NAS服务器配置
NAS_SERVER = "wuchenghao15.fnos.net"
NAS_USERNAME = "wuchenghao15"
NAS_PASSWORD = "!+.557KKZBchno"

PROJECT_NAME = "MTSCOS AI Project"
DEBUG_MODE = False
"""

                config_file_path = f"{self.nas_config['remote_path']}/app/config/nas_config.py"

                remote_dir = os.path.dirname(config_file_path)
                dirs = remote_dir.split('/')
                current_path = ''

                for dir_name in dirs:
                    if dir_name:
                        current_path += f"/{dir_name}"
                        try:
                            ftp.mkd(current_path)
                        except ftplib.error_perm:
                            pass

                ftp.storbinary(f'STOR {config_file_path}', config_content.encode('utf-8'))
                logger.info(f"上传配置文件: {config_file_path}")

                ftp.quit()
                logger.info("已断开NAS服务器连接")

                logger.info("NAS项目配置完成")
                return {'status': 'ok', 'message': 'NAS项目配置成功'}

            except Exception as e:
                retry_count += 1
                logger.error(f"配置NAS项目失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    logger.info(f"等待3秒后重试...")
                    time.sleep(3)
                else:
                    logger.error("达到最大重试次数,配置失败")
                    return {'status': 'error', 'message': str(e)}

    def report_to_database(self, upload_result, config_result):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'mtscos_ai_project.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS nas_uploads (id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id TEXT UNIQUE, nas_server TEXT, nas_path TEXT, total_files INTEGER, uploaded_files INTEGER, config_status TEXT, created_at TEXT, updated_at TEXT)")

            upload_id = f"nas-upload-{int(time.time())}"
            total_files = upload_result.get('total_files', 0)
            uploaded_files = len(upload_result.get('uploaded_files', []))
            config_status = config_result.get('status', 'unknown')

            cursor.execute("INSERT INTO nas_uploads (upload_id, nas_server, nas_path, total_files, uploaded_files, config_status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                upload_id,
                self.nas_config['server'],
                self.nas_config['remote_path'],
                total_files,
                uploaded_files,
                config_status,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            report_file = f'reports/nas_upload_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            if not os.path.exists('reports'):
                os.makedirs('reports')

            report_data = {
                'ai_id': self.ai_id,
                'nas_server': self.nas_config['server'],
                'nas_path': self.nas_config['remote_path'],
                'total_files': total_files,
                'uploaded_files': uploaded_files,
                'config_status': config_status,
                'created_at': self.created_at
            }
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            logger.info(f"上报到数据库完成,保存至: {report_file}")
            return {'status': 'ok', 'report': report_data, 'file': report_file}

        except Exception as e:
            logger.error(f"上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")

        try:
            error_cases = [
                {
                    "id": f"nas-upload-case-001",
                    "title": "NAS服务器连接失败",
                    "description": "无法连接到NAS服务器,可能是网络问题或服务器地址错误",
                    "solution": "检查网络连接,确认服务器地址、用户名和密码是否正确",
                    "affected_files": ["app/config/nas_config.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": f"nas-upload-case-002",
                    "title": "文件上传失败",
                    "description": "文件上传到NAS服务器失败,可能是权限问题或磁盘空间不足",
                    "solution": "检查NAS服务器权限设置,确保有足够的磁盘空间",
                    "affected_files": ["app/config/nas_config.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": f"nas-upload-case-003",
                    "title": "目录创建失败",
                    "description": "无法在NAS服务器上创建目录,可能是权限问题",
                    "solution": "确保NAS服务器用户有创建目录的权限",
                    "affected_files": ["app/config/nas_config.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                }
            ]

            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')

            existing_cases = []
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except Exception:
                        existing_cases = []

            all_cases = existing_cases + error_cases

            seen_ids = set()
            unique_cases = []
            for case in all_cases:
                if case['id'] not in seen_ids:
                    seen_ids.add(case['id'])
                    unique_cases.append(case)

            with open(brain_file, 'w', encoding='utf-8') as f:
                json.dump(unique_cases, f, ensure_ascii=False, indent=2)

            logger.info(f"错误修复案例共享完成,保存至: {brain_file}")
            logger.info(f"共共享 {len(error_cases)} 个新案例")

            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}
        except Exception as e:
            logger.error(f"共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def run_workflow(self):
        """执行完整的工作流程"""
        logger.info("=== 开始NAS上传配置AI工作流程 ===")

        project_files = self.prepare_project()
        if not project_files:
            logger.error("项目文件准备失败,工作流程终止")
            return {'status': 'error', 'message': '项目文件准备失败'}

        upload_result = self.upload_to_nas(project_files)

        config_result = self.configure_nas_project()

        database_report = self.report_to_database(upload_result, config_result)

        error_cases = self.share_error_cases()

        results = {
            'project_files': project_files,
            'upload_result': upload_result,
            'config_result': config_result,
            'database_report': database_report,
            'error_cases': error_cases
        }

        report_file = f'reports/nas_upload_config_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        if not os.path.exists('reports'):
            os.makedirs('reports')

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"工作流报告保存至: {report_file}")
        logger.info("=== NAS上传配置AI工作流程完成 ===")

        return results

def main():
    """主函数"""
    logger.info("=== 启动NAS上传配置AI ===")

    nas_ai = NASUploadConfigAI()

    results = nas_ai.run_workflow()

    logger.info("\n == 工作结果摘要 ===")
    logger.info(f"项目文件数量: {len(results['project_files'])} 个")
    logger.info(f"上传结果: {results['upload_result']}")
    logger.info(f"配置结果: {results['config_result']}")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")

    logger.info("\n == NAS上传配置AI工作完成 ===")

if __name__ == '__main__':
    main()

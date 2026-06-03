# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置到数据库AI - 负责将所有配置参数上传到数据库保存,上报数据库并共享错误修复案例到脑库
"""

import os
import sqlite3
from contextlib import contextmanager
import time
import logging
import re
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_to_db_ai')

db_path = 'mtscos.db'

class ConfigToDbAI:
    """配置到数据库AI"""

    def __init__(self):
        self.ai_id = f"config-to-db-ai-{int(time.time())}"
        self.name = "配置到数据库AI"
        self.description = "负责将所有配置参数上传到数据库保存,上报数据库并共享错误修复案例到脑库"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建配置到数据库AI: {self.ai_id}")

    def scan_configs(self):
        """扫描配置文件"""
        logger.info("=== 开始扫描配置文件 ===")

        configs = {
            'python_files': self.scan_python_configs(),
            'env_files': self.scan_env_configs(),
            'other_files': self.scan_other_configs(),
            'scan_time': self.created_at
        }

        logger.info(f"✅ 配置文件扫描完成,发现 {len(configs['python_files'])} 个Python配置文件,{len(configs['env_files'])} 个环境配置文件")
        return configs

    def scan_python_configs(self):
        """扫描Python配置文件"""
        try:
            python_configs = []
            for root, dirs, files in os.walk('.'):
                excluded_dirs = ['__pycache__', '.git', 'venv', 'env', 'node_modules']
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                for file in files:
                    if file.endswith('.py') and ('config' in file.lower() or 'setting' in file.lower()):
                        file_path = os.path.join(root, file)
                        python_configs.append({
                            'path': file_path,
                            'type': 'python',
                            'parameters': self.extract_python_configs(file_path)
                        })

            return python_configs

        except Exception as e:
            logger.error(f"❌ 扫描Python配置文件失败: {str(e)}")
            return []

    def extract_python_configs(self, file_path):
        """提取Python配置文件中的参数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r'\b([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)(?=\n\s*[A-Z_]|$)'
            matches = re.findall(pattern, content, re.DOTALL)

            parameters = []
            for match in matches:
                key, value = match
                value = value.strip()
                if value:
                    parameters.append({
                        'key': key,
                        'value': value,
                        'type': self.infer_type(value)
                    })

            return parameters

        except Exception as e:
            logger.warning(f"❌ 提取Python配置参数失败 {file_path}: {str(e)}")
            return []

    def infer_type(self, value):
        """推断值的类型"""
        if value.startswith('"') and value.endswith('"'):
            return 'string'
        elif value.startswith("'") and value.endswith("'"):
            return 'string'
        elif value.lower() in ['true', 'false']:
            return 'boolean'
        elif value.isdigit():
            return 'integer'
        elif '.' in value and value.replace('.', '').isdigit():
            return 'float'
        elif value.startswith('[') and value.endswith(']'):
            return 'list'
        elif value.startswith('{') and value.endswith('}'):
            return 'dict'
        else:
            return 'unknown'

    def scan_env_configs(self):
        """扫描环境配置文件"""
        try:
            env_configs = []
            for root, dirs, files in os.walk('.'):
                excluded_dirs = ['__pycache__', '.git', 'venv', 'env', 'node_modules']
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                for file in files:
                    if file == '.env' or file.endswith('.env'):
                        file_path = os.path.join(root, file)
                        env_configs.append({
                            'path': file_path,
                            'type': 'env',
                            'parameters': self.extract_env_configs(file_path)
                        })

            return env_configs
        except Exception as e:
            logger.error(f"❌ 扫描环境配置文件失败: {str(e)}")
            return []

    def extract_env_configs(self, file_path):
        """提取环境配置文件中的参数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            parameters = []
            for line in lines:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    if key:
                        parameters.append({
                            'key': key,
                            'value': value,
                            'type': self.infer_type(value)
                        })
            return parameters

        except Exception as e:
            return []

    def scan_other_configs(self):
        """扫描其他配置文件"""
        try:
            other_configs = []
            config_extensions = ['.yaml', '.yml', '.ini', '.cfg', '.conf']

            for root, dirs, files in os.walk('.'):
                excluded_dirs = ['__pycache__', '.git', 'venv', 'env', 'node_modules']
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                for file in files:
                    if any(file.endswith(ext) for ext in config_extensions):
                        file_path = os.path.join(root, file)
                        other_configs.append({
                            'path': file_path,
                            'type': 'other'
                        })

            return other_configs

        except Exception as e:
            logger.error(f"❌ 扫描其他配置文件失败: {str(e)}")
            return []

    def upload_to_database(self, configs):
        """上传配置到数据库"""

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("CREATE TABLE IF NOT EXISTS config_parameters (id INTEGER PRIMARY KEY AUTOINCREMENT, config_id TEXT, file_path TEXT, parameter_key TEXT, parameter_value TEXT, parameter_type TEXT, file_type TEXT, uploaded_at TEXT, updated_at TEXT)")
            
            config_id = f"config-upload-{int(time.time())}"
            uploaded_count = 0
            
            for python_config in configs['python_files']:
                for param in python_config['parameters']:
                    cursor.execute("INSERT OR REPLACE INTO config_parameters (config_id, file_path, parameter_key, parameter_value, parameter_type, file_type, uploaded_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                        config_id,
                        python_config['path'],
                        param['key'],
                        param['value'],
                        param['type'],
                        python_config['type'],
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    uploaded_count += 1
            
            for env_config in configs['env_files']:
                for param in env_config['parameters']:
                    cursor.execute("INSERT OR REPLACE INTO config_parameters (config_id, file_path, parameter_key, parameter_value, parameter_type, file_type, uploaded_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                        config_id,
                        env_config['path'],
                        param['key'],
                        param['value'],
                        param['type'],
                        env_config['type'],
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    uploaded_count += 1
            
            conn.commit()
            conn.close()

            logger.info(f"✅ 配置上传完成,共上传 {uploaded_count} 个配置参数")
            return {'status': 'ok', 'config_id': config_id, 'uploaded_count': uploaded_count}

        except Exception as e:
            logger.error(f"❌ 上传配置到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def report_to_database(self, configs, upload_result):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS config_uploads (id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id TEXT UNIQUE, total_files INTEGER, python_files INTEGER, env_files INTEGER, other_files INTEGER, uploaded_parameters INTEGER, status TEXT, created_at TEXT, updated_at TEXT)")

            total_files = len(configs['python_files']) + len(configs['env_files']) + len(configs['other_files'])
            python_files = len(configs['python_files'])
            env_files = len(configs['env_files'])
            other_files = len(configs['other_files'])
            uploaded_parameters = upload_result.get('uploaded_count', 0)
            status = upload_result.get('status', 'error')
            upload_id = upload_result.get('config_id', f"upload-{int(time.time())}")

            cursor.execute("INSERT OR REPLACE INTO config_uploads (upload_id, total_files, python_files, env_files, other_files, uploaded_parameters, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                upload_id,
                total_files,
                python_files,
                env_files,
                other_files,
                uploaded_parameters,
                status,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()

            if not os.path.exists('reports'):
                os.makedirs('reports')

            report_file = f'reports/config_upload_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

            report_data = {
                'upload_id': upload_id,
                'ai_id': self.ai_id,
                'config_id': upload_result.get('config_id'),
                'scanned_at': self.created_at,
                'total_files': total_files,
                'python_files': python_files,
                'env_files': env_files,
                'other_files': other_files,
                'uploaded_parameters': uploaded_parameters,
                'configs': configs
            }
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            conn.close()

            logger.info(f"✅ 上报到数据库完成,保存至: {report_file}")
            return {'status': 'ok', 'report': report_data, 'file': report_file}

        except Exception as e:
            logger.error(f"❌ 上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")

        try:
            error_cases = [
                {
                    "id": "config-db-case-001",
                    "title": "配置文件读取失败",
                    "description": "配置文件读取失败,可能是文件不存在或权限问题",
                    "solution": "检查配置文件是否存在且有读取权限",
                    "affected_files": ["app/drivers/config_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "config-db-case-002",
                    "title": "数据库连接失败",
                    "description": "数据库连接失败,可能是数据库文件不存在或权限问题",
                    "solution": "检查数据库文件是否存在且有读写权限",
                    "affected_files": ["app/drivers/config_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "config-db-case-003",
                    "title": "配置参数提取失败",
                    "description": "配置参数提取失败,可能是文件格式错误",
                    "solution": "检查文件格式是否正确",
                    "affected_files": ["app/drivers/config_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "config-db-case-004",
                    "title": "表创建失败",
                    "description": "数据库表创建失败,可能是SQL语法错误或权限问题",
                    "solution": "检查SQL语句语法,确保数据库有创建表的权限",
                    "affected_files": ["app/drivers/config_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "config-db-case-005",
                    "title": "配置上传失败",
                    "description": "配置参数上传到数据库失败,可能是数据格式错误",
                    "solution": "检查配置参数格式,确保数据符合数据库表结构要求",
                    "affected_files": ["app/drivers/config_to_db_manager.py"],
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

            logger.info(f"✅ 错误修复案例共享完成,保存至: {brain_file}")
            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")

            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}
        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def run_workflow(self):
        """执行完整的工作流程"""

        configs = self.scan_configs()
        upload_result = self.upload_to_database(configs)
        database_report = self.report_to_database(configs, upload_result)
        error_cases = self.share_error_cases()

        results = {
            'configs': configs,
            'upload_result': upload_result,
            'database_report': database_report,
            'error_cases': error_cases
        }

        if not os.path.exists('reports'):
            os.makedirs('reports')

        report_file = f'reports/config_to_db_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 工作流程完成,报告保存至: {report_file}")

        return results

def main():
    logger.info("=== 启动配置到数据库AI ===")

    config_ai = ConfigToDbAI()

    results = config_ai.run_workflow()

    logger.info("\n == 工作结果摘要 ===")
    logger.info(f"扫描的配置文件: {len(results['configs']['python_files'])} 个Python文件, {len(results['configs']['env_files'])} 个环境文件")
    logger.info(f"上传结果: {results['upload_result']}")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")

    logger.info("\n == 配置到数据库AI工作完成 ===")

if __name__ == '__main__':
    main()

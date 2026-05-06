#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统增强AI - 负责完善并加强系统所有功能，并上报数据库，最后共享错误修复案例到脑库使AI共享学习

import os
import sqlite3
# JSON import removed - using database
import time
import logging
import subprocess
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system_enhancement_ai')

class SystemEnhancementAI:
    """系统增强AI"""

    def __init__(self):
        self.ai_id = f"system-enhancement-ai-{int(time.time())}"
        self.name = "系统增强AI"
        self.description = "负责完善并加强系统所有功能，并上报数据库，最后共享错误修复案例到脑库使AI共享学习"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建系统增强AI: {self.ai_id}")

    def analyze_system(self):
        """分析系统"""
        logger.info("=== 开始分析系统 ===")

        system_analysis = {
            'modules': {
                'ai_engine': self.analyze_ai_engine(),
                'database': self.analyze_database(),
                'web_server': self.analyze_web_server(),
                'file_system': self.analyze_file_system(),
                'security': self.analyze_security()
            },
            'issues': []
        }

        # 收集问题
        for module_name, module_info in system_analysis['modules'].items():
            if 'issues' in module_info:
                for issue in module_info['issues']:
                    system_analysis['issues'].append({
                        'module': module_name,
                        'type': issue['type'],
                        'severity': issue['severity'],
                        'description': issue['description'],
                        'location': issue['location']
                    })

        logger.info(f"✅ 系统分析完成，发现 {len(system_analysis['issues'])} 个问题")
        return system_analysis

    def analyze_ai_engine(self):
        """分析AI引擎"""
        try:
            # 检查AI引擎配置
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查AI引擎配置表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_engine_config';")
            table_exists = cursor.fetchone() is not None

            engines = []
            if table_exists:
                cursor.execute("SELECT * FROM ai_engine_config;")
                engines = cursor.fetchall()

            conn.close()

            issues = []
            if not table_exists:
                issues.append({
                    'type': 'configuration',
                    'severity': 'high',
                    'description': 'AI引擎配置表不存在',
                    'location': 'ai_engine_config'
                })
                issues.append({
                    'type': 'configuration',
                    'description': 'AI引擎配置为空',
                })
            return {
                'table_exists': table_exists,
                'issues': issues
            }
        except Exception as e:
            logger.error(f"❌ AI引擎分析失败: {str(e)}")
            return {'issues': [{'type': 'error', 'severity': 'high', 'description': f'AI引擎分析失败: {str(e)}', 'location': 'ai_engine'}]}

    def analyze_database(self):
        """分析数据库"""
        try:
            # 检查数据库文件
            db_path = 'data/mtscos_ai_project.db'
            exists = os.path.exists(db_path)
            tables = []
            if exists:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0] for table in cursor.fetchall()]
                conn.close()

            if not exists:
                    'type': 'database',
                    'severity': 'high',
                    'description': '数据库文件不存在',
                })
            elif len(tables) < 5:
                    'severity': 'medium',
                    'description': '数据库表数量不足',
                })

                'exists': exists,
                'table_count': len(tables),
                'issues': issues
        except Exception as e:
            logger.error(f"❌ 数据库分析失败: {str(e)}")
            return {'issues': [{'type': 'error', 'severity': 'high', 'description': f'数据库分析失败: {str(e)}', 'location': 'database'}]}

    def analyze_web_server(self):
        """分析Web服务器"""
            try:
                import requests
                response = requests.get('http://localhost:5001', timeout=2)
                status = response.status_code
            except:
            if status is None:
                issues.append({
                    'type': 'service',
                    'severity': 'high',
                    'location': 'web_server'
                })
            elif status != 200:
                issues.append({
                    'severity': 'medium',
                    'description': f'Web服务器响应异常，状态码: {status}',
                    'location': 'web_server'
                })
            return {
                'issues': issues
            }
            logger.error(f"❌ Web服务器分析失败: {str(e)}")
            return {'issues': [{'type': 'error', 'severity': 'high', 'description': f'Web服务器分析失败: {str(e)}', 'location': 'web_server'}]}

    def analyze_file_system(self):
        """分析文件系统"""
        try:
            dir_status = []
            issues = []

            for directory in critical_dirs:
                exists = os.path.exists(directory)
                writable = os.access(directory, os.W_OK) if exists else False
                dir_status.append({
                    'exists': exists,
                    'writable': writable

                if not exists:
                    issues.append({
                        'description': f'目录 {directory} 不存在',
                        'location': directory
                elif not writable:
                        'description': f'目录 {directory} 不可写',
                    })

            return {
                'directories': dir_status,
            }
        except Exception as e:
            logger.error(f"❌ 文件系统分析失败: {str(e)}")
            return {'issues': [{'type': 'error', 'severity': 'high', 'description': f'文件系统分析失败: {str(e)}', 'location': 'filesystem'}]}

    def analyze_security(self):
        """分析安全性"""
            # 检查配置文件权限
            config_files = ['app/config/config.py', 'app/config/settings.py']
            security_issues = []

            for config_file in config_files:
                if os.path.exists(config_file):
                    if permissions != '644':
                        security_issues.append({
                            'severity': 'medium',
                            'description': f'配置文件 {config_file} 权限不安全',
                            'location': config_file
            return {
                'issues': security_issues
            logger.error(f"❌ 安全性分析失败: {str(e)}")
            return {'issues': [{'type': 'error', 'severity': 'high', 'description': f'安全性分析失败: {str(e)}', 'location': 'security'}]}

        """增强系统"""
        logger.info("=== 开始增强系统 ===")

        enhancements = {
            'ai_engine': self.enhance_ai_engine(),
            'database': self.enhance_database(),
            'web_server': self.enhance_web_server(),
            'security': self.enhance_security()
        }
        logger.info("=== 系统增强完成 ===")
    def enhance_ai_engine(self):
        """增强AI引擎"""
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 创建AI引擎配置表
            cursor.execute("CREATE TABLE IF NOT EXISTS ai_engine_config (id INTEGER PRIMARY KEY AUTOINCREMENT, engine_name TEXT UNIQUE, api_key TEXT, endpoint TEXT, model TEXT, is_enabled INTEGER, created_at TEXT, updated_at TEXT)")

            # 插入默认配置
            default_configs = [
                ('local', '', 'http://localhost:8000', 'gpt-3.5-turbo', 0),
                ('doubao', 'your-api-key-here', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'ep-20240413171442-72s62', 0),
                ('zhipu', 'your-api-key-here', 'https://open.bigmodel.cn/api/mt/text2image', 'cogview-3', 0),
                ('wenxin', 'your-api-key-here', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'ernie-3.5', 0)
            ]
            for config in default_configs:
                cursor.execute("INSERT OR REPLACE INTO ai_engine_config (engine_name, api_key, endpoint, model, is_enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (config[0], config[1], config[2], config[3], config[4], datetime.now().isoformat(), datetime.now().isoformat()))

            conn.close()

            logger.info("✅ AI引擎增强完成")

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

        """增强数据库"""
        try:
            # 确保数据库文件和表存在
            db_path = 'data/mtscos_ai_project.db'
            os.makedirs('data', exist_ok=True)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 创建必要的表
            tables = [
                "CREATE TABLE IF NOT EXISTS ai_engine_config (id INTEGER PRIMARY KEY AUTOINCREMENT, engine_name TEXT UNIQUE, api_key TEXT, endpoint TEXT, model TEXT, is_enabled INTEGER, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY AUTOINCREMENT, config_key TEXT UNIQUE, config_value TEXT, description TEXT, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS services_config (id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT UNIQUE, config TEXT, status TEXT, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS error_cases (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT UNIQUE, title TEXT, description TEXT, solution TEXT, affected_files TEXT, fix_date TEXT, fixer TEXT, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS system_exceptions (id INTEGER PRIMARY KEY AUTOINCREMENT, exception_id TEXT UNIQUE, type TEXT, severity TEXT, description TEXT, location TEXT, detected_at TEXT, fixed INTEGER, solution TEXT, fixer TEXT, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS nas_uploads (id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id TEXT UNIQUE, nas_server TEXT, nas_path TEXT, total_files INTEGER, uploaded_files INTEGER, config_status TEXT, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS system_boot_checks (id INTEGER PRIMARY KEY AUTOINCREMENT, check_id TEXT UNIQUE, system_status TEXT, services_status TEXT, database_status TEXT, filesystem_status TEXT, network_status TEXT, errors_count INTEGER, fixed_count INTEGER, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS log_optimizations (id INTEGER PRIMARY KEY AUTOINCREMENT, optimization_id TEXT UNIQUE, issues_count INTEGER, optimizations_count INTEGER, log_files_count INTEGER, log_size INTEGER, created_at TEXT, updated_at TEXT)",
                "CREATE TABLE IF NOT EXISTS system_enhancements (id INTEGER PRIMARY KEY AUTOINCREMENT, enhancement_id TEXT UNIQUE, modules TEXT, issues_count INTEGER, enhancements_count INTEGER, created_at TEXT, updated_at TEXT)"

            for table_sql in tables:
                cursor.execute(table_sql)

            conn.commit()
            conn.close()
            logger.info("✅ 数据库增强完成")
            return {'status': 'ok', 'message': '数据库增强成功'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def enhance_web_server(self):
        try:
            # 检查Flask服务配置
            config_file = 'app/config/settings.py'
            if not os.path.exists(config_file):
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write('''
# 应用设置
APP_HOST = "0.0.0.0"
APP_PORT = 5000
DATABASE_PATH = "data/mtscos_ai_project.db"
''')

            logger.info("✅ Web服务器增强完成")
            return {'status': 'ok', 'message': 'Web服务器增强成功'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def enhance_file_system(self):
        """增强文件系统"""
        try:
            critical_dirs = ['app', 'data', 'reports', 'logs']
            for directory in critical_dirs:
                os.makedirs(directory, exist_ok=True)
                if not os.access(directory, os.W_OK):
                    os.chmod(directory, 0o755)

            logger.info("✅ 文件系统增强完成")
            return {'status': 'ok', 'message': '文件系统增强成功'}

        except Exception as e:
            logger.error(f"❌ 文件系统增强失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def enhance_security(self):
        """增强安全性"""
            # 修复配置文件权限
            config_files = ['app/config/config.py', 'app/config/settings.py']
            for config_file in config_files:
                if os.path.exists(config_file):
                    os.chmod(config_file, 0o644)

            logger.info("✅ 安全性增强完成")
            return {'status': 'ok', 'message': '安全性增强成功'}

        except Exception as e:
            logger.error(f"❌ 安全性增强失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def report_to_database(self, system_analysis, enhancements):
        logger.info("=== 开始上报到数据库 ===")
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 创建系统增强报告表
            cursor.execute("CREATE TABLE IF NOT EXISTS system_enhancements (id INTEGER PRIMARY KEY AUTOINCREMENT, enhancement_id TEXT UNIQUE, modules TEXT, issues_count INTEGER, enhancements_count INTEGER, created_at TEXT, updated_at TEXT)")

            # 计算问题和增强数量
            issues_count = len(system_analysis['issues'])
            enhancements_count = sum(1 for enh in enhancements.values() if enh.get('status') == 'ok')
            modules = list(enhancements.keys())

            # 插入增强信息
            enhancement_id = f"system-enhancement-{int(time.time())}"
            cursor.execute("INSERT OR REPLACE INTO system_enhancements (enhancement_id, modules, issues_count, enhancements_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (
                enhancement_id,
                issues_count,
                enhancements_count,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            # 保存上报结果
            report_file = f'reports/system_enhancement_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                os.makedirs('reports')

            report_data = {
                'enhancement_id': enhancement_id,
                'analyzed_at': self.created_at,
                'issues_count': issues_count,
                'enhancements_count': enhancements_count,
                'modules': modules,
                'enhancements': enhancements
            with open(report_file, 'w', encoding='utf-8') as f:

            logger.info(f"✅ 上报到数据库完成，保存至: {report_file}")
            return {'status': 'ok', 'report': report_data, 'file': report_file}

        except Exception as e:
            logger.error(f"❌ 上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self, system_analysis, enhancements):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")

        try:
            # 收集错误修复案例
            error_cases = []
            case_id_counter = 1

            # 从增强结果中提取修复案例
                if enhancement.get('status') == 'ok':

                        "id": case_id,
                        "title": f"{module}模块增强",
                        "description": f"增强{module}模块的功能",
                        "solution": enhancement.get('message', '模块增强成功'),
                        "affected_files": [f"app/{module}"],
                        "fix_date": self.created_at,
                    })

            # 从分析结果中提取问题修复案例
            for issue in system_analysis['issues']:
                case_id = f"system-enhancement-case-{str(case_id_counter).zfill(3)}"
                case_id_counter += 1

                error_cases.append({
                    "title": f"{issue['module']}模块问题",
                    "description": issue['description'],
                    "solution": f"已增强{issue['module']}模块，修复了{issue['type']}问题",
                    "affected_files": [issue['location']],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                })

            # 保存到脑库
            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')

            # 如果文件存在，读取现有数据
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except:
                        existing_cases = []

            # 合并案例
            all_cases = existing_cases + error_cases

            # 去重
            unique_cases = []
            for case in all_cases:
                if case['id'] not in seen_ids:
                    seen_ids.add(case['id'])
                    unique_cases.append(case)

            # 保存
            with open(brain_file, 'w', encoding='utf-8') as f:
                json.dump(unique_cases, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")

            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}

        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def run_workflow(self):
        """执行完整的工作流程"""
        logger.info("=== 开始系统增强AI工作流程 ===")

        # 1. 分析系统
        system_analysis = self.analyze_system()

        # 2. 增强系统
        enhancements = self.enhance_system(system_analysis)

        # 3. 上报到数据库
        database_report = self.report_to_database(system_analysis, enhancements)

        # 4. 共享错误修复案例到脑库
        error_cases = self.share_error_cases(system_analysis, enhancements)

        results = {
            'system_analysis': system_analysis,
            'enhancements': enhancements,
            'database_report': database_report,
            'error_cases': error_cases
        }
        # 保存工作流报告
        report_file = f'reports/system_enhancement_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        if not os.path.exists('reports'):
            os.makedirs('reports')

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 工作流报告保存至: {report_file}")
        logger.info("=== 系统增强AI工作流程完成 ===")

        return results

def main():
    """主函数"""
    logger.info("=== 启动系统增强AI ===")

    enhancement_ai = SystemEnhancementAI()
    # 执行工作流程
    results = enhancement_ai.run_workflow()
    # 输出结果
    logger.info(f"检测到的问题: {len(results['system_analysis']['issues'])} 个")
    logger.info(f"增强项数量: {sum(1 for enh in results['enhancements'].values() if enh.get('status') == 'ok')} 个")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")
    logger.info("\n=== 系统增强AI工作完成 ===")
if __name__ == '__main__':

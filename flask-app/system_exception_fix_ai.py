#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统异常修复AI - 负责检测系统异常，尝试修复，并上报数据库，最后共享错误修复案例到脑库使AI共享学习

import os
import sqlite3
# JSON import removed - using database
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system_exception_fix_ai')

class SystemExceptionFixAI:
    """系统异常修复AI"""

    def __init__(self):
        self.ai_id = f"system-exception-fix-ai-{int(time.time())}"
        self.name = "系统异常修复AI"
        self.description = "负责检测系统异常，尝试修复，并上报数据库，最后共享错误修复案例到脑库使AI共享学习"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建系统异常修复AI: {self.ai_id}")

    def detect_system_exceptions(self):
        """检测系统异常"""
        logger.info("=== 开始检测系统异常 ===")

        exceptions = {
            'file_system': self.detect_file_system_exceptions(),
            'database': self.detect_database_exceptions(),
            'services': self.detect_service_exceptions(),
            'configuration': self.detect_configuration_exceptions()
        }

        logger.info("=== 系统异常检测完成 ===")
        return exceptions

    def detect_file_system_exceptions(self):
        """检测文件系统异常"""
        try:
            exceptions = []

            # 检查关键目录是否存在
            critical_dirs = ['app', 'data', 'reports']
            for directory in critical_dirs:
                if not os.path.exists(directory):
                    exceptions.append({
                        'type': 'file_system',
                        'severity': 'high',
                        'description': f'关键目录 {directory} 不存在',
                        'location': directory
                    })

            # 检查数据库文件是否存在
            db_path = 'data/mtscos_ai_project.db'
            if not os.path.exists(db_path):
                exceptions.append({
                    'severity': 'high',
                    'location': db_path

            # 检查日志目录是否可写
            if not os.access('reports', os.W_OK):
                    'severity': 'medium',
                    'description': 'reports目录不可写',
                })

            logger.info(f"✅ 文件系统异常检测完成，发现 {len(exceptions)} 个异常")
            return exceptions
        except Exception as e:
            logger.error(f"❌ 文件系统异常检测失败: {str(e)}")

    def detect_database_exceptions(self):
        """检测数据库异常"""
        try:
            exceptions = []
            # 尝试连接数据库
            try:
                conn = sqlite3.connect(db_path)

                # 检查关键表是否存在
                critical_tables = ['ai_engine_config', 'system_config', 'services_config', 'error_cases']
                for table in critical_tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
                    if not cursor.fetchone():
                        exceptions.append({
                            'type': 'database',
                            'description': f'数据库表 {table} 不存在',
                            'location': table

                conn.close()
            except Exception as db_error:
                exceptions.append({
                    'type': 'database',
                    'severity': 'high',
                    'location': db_path

            logger.info(f"✅ 数据库异常检测完成，发现 {len(exceptions)} 个异常")
            return exceptions
            logger.error(f"❌ 数据库异常检测失败: {str(e)}")
            return []

        """检测服务异常"""
        try:
            exceptions = []

            try:
                        'type': 'services',
                        'severity': 'medium',
                        'location': 'http://localhost:5000'
                    })
            except:
                exceptions.append({
                    'type': 'services',
                    'description': 'Flask服务未运行',
                })

            return exceptions
            logger.error(f"❌ 服务异常检测失败: {str(e)}")
            return []

    def detect_configuration_exceptions(self):
        """检测配置异常"""
        try:
            exceptions = []

                if not os.path.exists(config_file):
                    exceptions.append({
                        'type': 'configuration',
                        'location': config_file
                    })
            logger.info(f"✅ 配置异常检测完成，发现 {len(exceptions)} 个异常")
            return exceptions
        except Exception as e:
            logger.error(f"❌ 配置异常检测失败: {str(e)}")
            return []
    def fix_exceptions(self, exceptions):
        """尝试修复系统异常"""

        fixes = {
            'file_system': self.fix_file_system_exceptions(exceptions.get('file_system', [])),
            'services': self.fix_service_exceptions(exceptions.get('services', [])),
        }
        logger.info("=== 系统异常修复完成 ===")
        return fixes
    def fix_file_system_exceptions(self, exceptions):
        """修复文件系统异常"""
        try:
            fixed = []
            for exception in exceptions:
                if exception['description'].startswith('关键目录'):
                    directory = exception['location']
                    fixed.append({
                        'exception': exception,
                        'solution': f'创建了目录 {directory}'
                    })
                elif exception['description'] == 'reports目录不可写':
                    os.chmod('reports', 0o755)
                    fixed.append({
                        'exception': exception,
                        'fixed': True,
                        'solution': '修改了reports目录权限为755'
                    })
            logger.info(f"✅ 文件系统异常修复完成，修复了 {len(fixed)} 个异常")
            return fixed

        except Exception as e:
            return []

    def fix_database_exceptions(self, exceptions):
        """修复数据库异常"""
        try:
            fixed = []

            for exception in exceptions:
                if exception['description'] == '数据库文件不存在':
                    # 创建数据库文件和必要的表
                    os.makedirs('data', exist_ok=True)
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute("CREATE TABLE IF NOT EXISTS ai_engine_config (id INTEGER PRIMARY KEY AUTOINCREMENT, engine_name TEXT UNIQUE, api_key TEXT, endpoint TEXT, model TEXT, is_enabled INTEGER, created_at TEXT, updated_at TEXT)")
                    cursor.execute("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY AUTOINCREMENT, config_key TEXT UNIQUE, config_value TEXT, description TEXT, created_at TEXT, updated_at TEXT)")
                    cursor.execute("CREATE TABLE IF NOT EXISTS services_config (id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT UNIQUE, config TEXT, status TEXT, created_at TEXT, updated_at TEXT)")
                    cursor.execute("CREATE TABLE IF NOT EXISTS error_cases (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT UNIQUE, title TEXT, description TEXT, solution TEXT, affected_files TEXT, fix_date TEXT, fixer TEXT, created_at TEXT, updated_at TEXT)")

                    conn.commit()

                    fixed.append({
                        'exception': exception,
                        'fixed': True,
                        'solution': '创建了数据库文件和必要的表'
                    })
                elif exception['description'].startswith('数据库表'):
                    # 创建缺失的表
                    table_name = exception['location']
                    db_path = 'data/mtscos_ai_project.db'
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    if table_name == 'ai_engine_config':
                        cursor.execute("CREATE TABLE IF NOT EXISTS ai_engine_config (id INTEGER PRIMARY KEY AUTOINCREMENT, engine_name TEXT UNIQUE, api_key TEXT, endpoint TEXT, model TEXT, is_enabled INTEGER, created_at TEXT, updated_at TEXT)")
                    elif table_name == 'system_config':
                        cursor.execute("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY AUTOINCREMENT, config_key TEXT UNIQUE, config_value TEXT, description TEXT, created_at TEXT, updated_at TEXT)")
                    elif table_name == 'error_cases':


                        'exception': exception,
                        'fixed': True,
                        'solution': f'创建了缺失的表 {table_name}'
                    })

            logger.info(f"✅ 数据库异常修复完成，修复了 {len(fixed)} 个异常")
            return fixed

            logger.error(f"❌ 数据库异常修复失败: {str(e)}")
            return []
    def fix_service_exceptions(self, exceptions):
        """修复服务异常"""

                if exception['description'] == 'Flask服务未运行':
                    # 这里可以尝试启动Flask服务
                    fixed.append({
                        'exception': exception,
                        'solution': '建议手动启动Flask服务: python3 -m flask run'
                    })

            logger.info(f"✅ 服务异常修复完成，处理了 {len(fixed)} 个异常")
            return fixed

            logger.error(f"❌ 服务异常修复失败: {str(e)}")
            return []
    def fix_configuration_exceptions(self, exceptions):
        """修复配置异常"""
        try:
            fixed = []
                if exception['description'].startswith('配置文件'):
                    config_file = exception['location']
                    if config_file.endswith('config.py'):
                        with open(config_file, 'w', encoding='utf-8') as f:
# 系统配置
SYSTEM_NAME = "MTSCOS AI Project"
SYSTEM_VERSION = "2.0.0"
DEBUG_MODE = False
LOG_LEVEL = "INFO"
''')
                    elif config_file.endswith('settings.py'):
                        with open(config_file, 'w', encoding='utf-8') as f:
    pass
APP_HOST = "0.0.0.0"
APP_PORT = 5000
''')

                        'fixed': True,
                        'solution': f'创建了默认配置文件 {config_file}'

            return fixed
        except Exception as e:
            return []
    def report_to_database(self, exceptions, fixes):
        logger.info("=== 开始上报到数据库 ===")
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 创建异常报告表

                for exception in exception_list:
                    exception_id = f"exception-{int(time.time())}-{len(reported_exceptions)}"

                    # 查找对应的修复信息
                    solution = ""
                    for fix_type, fix_list in fixes.items():
                        for fix in fix_list:
                                solution = fix['solution']
                                fixed = 1 if fix['fixed'] else 0
                        if solution:
                            break

                    cursor.execute("INSERT OR REPLACE INTO system_exceptions (exception_id, type, severity, description, location, detected_at, fixed, solution, fixer, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                        exception_id,
                        exception['type'],
                        exception['description'],
                        exception['location'],
                        self.created_at,
                        fixed,
                        self.ai_id,
                        datetime.now().isoformat(),
                    ))

                    reported_exceptions.append({
                        'exception_id': exception_id,
                        'type': exception['type'],
                        'description': exception['description'],
                        'fixed': fixed,
                    })

            conn.commit()
            conn.close()

            # 保存上报结果
            if not os.path.exists('reports'):
                os.makedirs('reports')

            report_data = {
                'report_id': f"report-{int(time.time())}",
                'ai_id': self.ai_id,
                'detected_at': self.created_at,
                'total_exceptions': sum(len(exc_list) for exc_list in exceptions.values()),
                'fixed_exceptions': sum(len(fix_list) for fix_list in fixes.values()),
                'exceptions': reported_exceptions
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            return {'status': 'ok', 'report': report_data, 'file': report_file}

            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self, exceptions, fixes):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===" )
            error_cases = []

            for exception_type, fix_list in fixes.items():
                for fix in fix_list:
                        case_id = f"system-exception-case-{str(case_id_counter).zfill(3)}"
                        case_id_counter += 1
                            "id": case_id,
                            "title": f"{exception_type}异常: {fix['exception']['description']}",
                            "description": fix['exception']['description'],
                            "solution": fix['solution'],
                            "affected_files": [fix['exception']['location']],
                            "fix_date": self.created_at,
                            "fixer": self.ai_id
                        })

            # 保存到脑库
            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')

            # 如果文件存在，读取现有数据
            existing_cases = []
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except:
                        existing_cases = []

            # 合并案例
            all_cases = existing_cases + error_cases
            # 去重
            seen_ids = set()
            unique_cases = []
            for case in all_cases:
                if case['id'] not in seen_ids:
                    seen_ids.add(case['id'])
                    unique_cases.append(case)

            # 保存

            logger.info(f"✅ 错误修复案例共享完成，保存至: {brain_file}")
            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")

            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}
        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

        """执行完整的工作流程"""
        logger.info("=== 开始系统异常修复AI工作流程 ===")

        # 1. 检测系统异常
        exceptions = self.detect_system_exceptions()

        # 2. 尝试修复异常
        fixes = self.fix_exceptions(exceptions)

        # 3. 上报到数据库
        database_report = self.report_to_database(exceptions, fixes)

        # 4. 共享错误修复案例到脑库
        error_cases = self.share_error_cases(exceptions, fixes)

        results = {
            'exceptions': exceptions,
            'fixes': fixes,
            'database_report': database_report,
            'error_cases': error_cases
        # 保存工作流报告
        report_file = f'reports/system_exception_fix_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        if not os.path.exists('reports'):
            os.makedirs('reports')

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 工作流报告保存至: {report_file}")
        logger.info("=== 系统异常修复AI工作流程完成 ===")

        return results

def main():
    """主函数"""
    logger.info("=== 启动系统异常修复AI ===")

    # 创建系统异常修复AI
    exception_fix_ai = SystemExceptionFixAI()

    # 执行工作流程
    results = exception_fix_ai.run_workflow()

    # 输出结果
    logger.info("\n=== 工作结果摘要 ===")
    logger.info(f"检测到的异常: {sum(len(exc_list) for exc_list in results['exceptions'].values())} 个")
    logger.info(f"修复的异常: {sum(len(fix_list) for fix_list in results['fixes'].values())} 个")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")

    logger.info("\n=== 系统异常修复AI工作完成 ===")
if __name__ == '__main__':
    main()

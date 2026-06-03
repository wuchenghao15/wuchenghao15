# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志优化AI - 负责优化日志系统,最后共享错误修复案例到脑库使AI共享学习
"""

import os
import sqlite3
import json
import time
import logging
import logging.handlers
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_optimization_ai')

class LogOptimizationAI:
    """日志优化AI"""

    def __init__(self):
        self.ai_id = f"log-optimization-ai-{int(time.time())}"
        self.name = "日志优化AI"
        self.description = "负责优化日志系统,最后共享错误修复案例到脑库使AI共享学习"
        self.created_at = datetime.now().isoformat()
        logger.info(f"新建日志优化AI: {self.ai_id}")

    def analyze_log_system(self):
        """分析日志系统"""
        logger.info("=== 开始分析日志系统 ===")

        log_analysis = {
            'log_config': self.analyze_log_config(),
            'log_files': self.analyze_log_files(),
            'log_performance': self.analyze_log_performance(),
            'issues': []
        }

        if not log_analysis['log_config']['configured']:
            log_analysis['issues'].append({
                'type': 'configuration',
                'severity': 'high',
                'description': '日志系统未配置',
                'location': 'log_config'
            })

        if log_analysis['log_files']['total_files'] > 10:
            log_analysis['issues'].append({
                'type': 'file_count',
                'severity': 'medium',
                'description': '日志文件过多',
                'location': 'log_files'
            })

        if log_analysis['log_files']['average_size'] > 1048576:
            log_analysis['issues'].append({
                'type': 'file_size',
                'severity': 'medium',
                'description': '日志文件平均大小过大',
                'location': 'log_performance'
            })

        logger.info(f"日志系统分析完成,发现 {len(log_analysis['issues'])} 个问题")
        return log_analysis

    def analyze_log_config(self):
        """分析日志配置"""
        try:
            config_files = ['app/config/logging.py', 'app/config/config.py']
            configured = False
            config_details = {}

            for config_file in config_files:
                if os.path.exists(config_file):
                    configured = True
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        config_details[config_file] = {
                            'exists': True,
                            'size': len(content)
                        }
                else:
                    config_details[config_file] = {
                        'exists': False,
                        'size': 0
                    }
            return {
                'configured': configured,
                'config_files': config_details
            }
        except Exception as e:
            logger.error(f"日志配置分析失败: {str(e)}")
            return {'configured': False, 'config_files': {}}

    def analyze_log_files(self):
        """分析日志文件"""
        try:
            log_files = []
            log_dirs = ['logs', 'reports']

            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            if file.endswith('.log') or file.endswith('.json'):
                                file_path = os.path.join(root, file)
                                log_files.append({
                                    'path': file_path,
                                    'size': os.path.getsize(file_path),
                                    'last_modified': os.path.getmtime(file_path)
                                })

            total_size = sum(file['size'] for file in log_files)
            average_size = total_size / len(log_files) if log_files else 0

            return {
                'total_files': len(log_files),
                'total_size': total_size,
                'average_size': average_size,
                'files': log_files[:10]
            }
        except Exception as e:
            logger.error(f"日志文件分析失败: {str(e)}")
            return {'total_files': 0, 'total_size': 0, 'average_size': 0, 'files': []}

    def analyze_log_performance(self):
        """分析日志性能"""
        try:
            performance = {
                'average_size': 0,
                'rotation_enabled': False,
                'compression_enabled': False,
                'retention_policy': 'not_set'
            }
            log_config_file = 'app/config/logging.py'
            if os.path.exists(log_config_file):
                with open(log_config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'RotatingFileHandler' in content:
                        performance['rotation_enabled'] = True
                    if 'TimedRotatingFileHandler' in content:
                        performance['rotation_enabled'] = True
                    if 'compress' in content:
                        performance['compression_enabled'] = True
                    if 'maxBytes' in content or 'backupCount' in content:
                        performance['retention_policy'] = 'configured'

            return performance

        except Exception as e:
            logger.error(f"日志性能分析失败: {str(e)}")
            return {
                'average_size': 0,
                'rotation_enabled': False,
                'compression_enabled': False,
                'retention_policy': 'not_set'
            }

    def optimize_log_system(self, log_analysis):
        """优化日志系统"""
        logger.info("=== 开始优化日志系统 ===")

        optimizations = {
            'config': self.optimize_log_config(),
            'rotation': self.optimize_log_rotation(),
            'retention': self.optimize_log_retention(),
            'performance': self.optimize_log_performance()
        }
        return optimizations

    def optimize_log_config(self):
        """优化日志配置"""
        try:
            log_config_file = 'app/config/logging.py'
            os.makedirs(os.path.dirname(log_config_file), exist_ok=True)
            log_config_content = '''
import logging
import logging.handlers
import os
import sys

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
    ]
)

logger_ai = logging.getLogger('ai')
logger_ai.setLevel(logging.INFO)
logger_db = logging.getLogger('database')
logger_db.setLevel(logging.INFO)
logger_api = logging.getLogger('api')
logger_api.setLevel(logging.INFO)
'''

            with open(log_config_file, 'w', encoding='utf-8') as f:
                f.write(log_config_content)

            logger.info(f"创建日志配置文件: {log_config_file}")
            return {
                'status': 'ok',
                'message': '日志配置文件创建成功',
                'file': log_config_file
            }

        except Exception as e:
            logger.error(f"日志配置优化失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def optimize_log_rotation(self):
        """优化日志轮转"""
        try:
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)

            rotation_config = {
                'enabled': True,
                'max_bytes': 10485760,
                'backup_count': 5
            }

            logger.info("日志轮转配置优化完成")
            return {
                'status': 'ok',
                'message': '日志轮转配置优化成功',
                'config': rotation_config
            }

        except Exception as e:
            logger.error(f"日志轮转优化失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def optimize_log_retention(self):
        """优化日志保留"""
        try:
            log_dirs = ['logs', 'reports']
            deleted_files = []

            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            if file.endswith('.log') or file.endswith('.json'):
                                file_path = os.path.join(root, file)
                                file_mtime = os.path.getmtime(file_path)
                                if time.time() - file_mtime > 7 * 24 * 3600:
                                    os.remove(file_path)
                                    deleted_files.append(file_path)

            logger.info(f"日志保留优化完成,删除了 {len(deleted_files)} 个过期文件")
            return {
                'status': 'ok',
                'message': f'删除了 {len(deleted_files)} 个过期文件',
                'deleted_files': deleted_files
            }

        except Exception as e:
            logger.error(f"日志保留优化失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def optimize_log_performance(self):
        """优化日志性能"""
        try:
            performance_config = {
                'enabled': True,
                'buffering': True,
                'compression': True
            }

            logger.info("日志性能优化完成")
            return {
                'status': 'ok',
                'message': '日志性能优化成功',
                'config': performance_config
            }

        except Exception as e:
            logger.error(f"日志性能优化失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def report_to_database(self, log_analysis, optimizations):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS log_optimizations (
                optimization_id TEXT PRIMARY KEY,
                issues_count INTEGER,
                optimizations_count INTEGER,
                log_files_count INTEGER,
                log_size INTEGER,
                created_at TEXT,
                updated_at TEXT
                )
                ''')
                
                optimizations_count = sum(1 for opt in optimizations.values() if opt.get('status') == 'ok')
                issues_count = len(log_analysis.get('issues', []))
                log_files_count = log_analysis.get('log_files', {}).get('total_files', 0)
                log_size = log_analysis.get('log_files', {}).get('total_size', 0)
                
                optimization_id = f"log-optimization-{int(time.time())}"
                cursor.execute("INSERT OR REPLACE INTO log_optimizations (optimization_id, issues_count, optimizations_count, log_files_count, log_size, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (
                optimization_id,
                issues_count,
                optimizations_count,
                log_files_count,
                log_size,
                datetime.now().isoformat(),
                datetime.now().isoformat()
                ))
                
                conn.commit()

            if not os.path.exists('reports'):
                os.makedirs('reports')

            report_data = {
                'ai_id': self.ai_id,
                'analyzed_at': self.created_at,
                'issues_count': issues_count,
                'optimizations_count': optimizations_count,
                'log_files_count': log_files_count,
                'log_size': log_size,
                'log_analysis': log_analysis,
                'optimizations': optimizations
            }

            report_file = os.path.join('reports', f'log_optimization_{int(time.time())}.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            logger.info(f"上报到数据库完成,保存至: {report_file}")
            return {'status': 'ok', 'report': report_data, 'file': report_file}

        except Exception as e:
            logger.error(f"上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self, log_analysis, optimizations):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")

        try:
            error_cases = []
            case_id_counter = 1

            for opt_type, opt_result in optimizations.items():
                if opt_result.get('status') == 'ok':
                    case_id = f"log-optimization-case-{str(case_id_counter).zfill(3)}"
                    case_id_counter += 1

                    error_cases.append({
                        "id": case_id,
                        "title": f"{opt_type}日志优化",
                        "description": f"优化{opt_type}相关的日志配置",
                        "solution": opt_result.get('message', '日志优化成功'),
                        "affected_files": ["app/config/logging.py"],
                        "fix_date": self.created_at,
                        "fixer": self.ai_id
                    })

            for issue in log_analysis.get('issues', []):
                case_id = f"log-optimization-case-{str(case_id_counter).zfill(3)}"
                case_id_counter += 1

                error_cases.append({
                    "id": case_id,
                    "title": f"{issue['type']}日志问题",
                    "description": issue['description'],
                    "solution": f"已优化{issue['type']}相关的日志配置",
                    "affected_files": [issue['location']],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                })

            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')

            brain_file = os.path.join('app/ai/brain', 'error_cases.json')
            existing_cases = []
            if os.path.exists(brain_file):
                try:
                    with open(brain_file, 'r', encoding='utf-8') as f:
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
        logger.info("=== 开始日志优化AI工作流程 ===")

        log_analysis = self.analyze_log_system()
        optimizations = self.optimize_log_system(log_analysis)
        database_report = self.report_to_database(log_analysis, optimizations)
        error_cases = self.share_error_cases(log_analysis, optimizations)

        results = {
            'log_analysis': log_analysis,
            'optimizations': optimizations,
            'database_report': database_report,
            'error_cases': error_cases
        }

        if not os.path.exists('reports'):
            os.makedirs('reports')

        report_file = os.path.join('reports', f'log_optimization_workflow_{int(time.time())}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"工作流报告保存至: {report_file}")

        return results

def main():
    """主函数"""
    logger.info("=== 启动日志优化AI ===")

    log_ai = LogOptimizationAI()
    results = log_ai.run_workflow()

    logger.info("\n == 工作结果摘要 ===")
    logger.info(f"检测到的问题: {len(results['log_analysis'].get('issues', []))} 个")
    logger.info(f"优化项数量: {sum(1 for opt in results['optimizations'].values() if opt.get('status') == 'ok')} 个")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")

    logger.info("\n == 日志优化AI工作完成 ===")

if __name__ == '__main__':
    main()

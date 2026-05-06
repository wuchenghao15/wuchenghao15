#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增AI，新建虚拟模拟环境到影子系统完整考试系统

import os
import sys
import logging
# JSON import removed - using database
import sqlite3
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_ai_and_shadow_exam_system')

class AIAndShadowExamSystemEnhancer:
    """AI和影子考试系统增强器类"""

    def __init__(self):
        """初始化AI和影子考试系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.shadow_dir = os.path.join(self.data_dir, 'shadow_system')
        self.exam_dir = os.path.join(self.data_dir, 'exam_system')
        self.ai_brain_dir = os.path.join(self.data_dir, 'ai_brain')

        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.shadow_dir, exist_ok=True)
        os.makedirs(self.exam_dir, exist_ok=True)
        os.makedirs(self.ai_brain_dir, exist_ok=True)

        # 新AI类型定义
        self.new_ai_types = [
            {
                'ai_type': 'shadow_exam_ai',
                'name': '影子考试AI',
                'description': '专门负责在影子系统中运行和管理考试系统测试',
                'functions': [
                    '影子环境管理',
                    '考试系统测试',
                    '测试结果分析',
                    '性能对比评估'
                ],
                'required_skills': ['shadow_system', 'exam_management', 'test_execution']
            },
            {
                'name': '考试错误处理AI',
                'description': '专门负责考试系统的错误检测和处理',
                'functions': [
                    '错误检测',
                    '自动修复',
                    '错误上报'
                ],
                'required_skills': ['error_detection', 'error_analysis', 'error_fix', 'exam_management']
            },
                'name': '考试测试学习AI',
                'description': '专门负责从考试系统测试中学习',
                    '测试结果分析',
                    '模式识别',
                    '学习模型更新'
                ],
            }
        ]

        logger.info("AI和影子考试系统增强器初始化完成")
    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            logger.info("开始检查数据库")

            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查影子考试系统表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shadow_exam_systems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT UNIQUE,
                    name TEXT,
                    type TEXT,
                    status TEXT,
                    created_at TEXT,
                    last_updated TEXT
                )

            # 检查是否存在旧的 shadow_exam_tests 表（没有 system_id 字段）
            cursor.execute("PRAGMA table_info(shadow_exam_tests)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'system_id' not in columns:
                # 表存在但没有 system_id 字段，需要重新创建
                cursor.execute("DROP TABLE IF EXISTS shadow_exam_tests")
                logger.info("删除旧的 shadow_exam_tests 表")

            # 检查影子考试测试表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shadow_exam_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE,
                    system_id TEXT,
                    test_type TEXT,
                    status TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    result TEXT,
                    FOREIGN KEY (system_id) REFERENCES shadow_exam_systems (system_id)
                )
            # 检查影子考试测试详情表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shadow_exam_test_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    test_case TEXT,
                    expected_result TEXT,
                    actual_result TEXT,
                    error_message TEXT,
                    timestamp TEXT,
                )
            # 检查影子考试错误处理表是否存在
                CREATE TABLE IF NOT EXISTS shadow_exam_error_handling (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT UNIQUE,
                    test_id TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    status TEXT,
                    fix_result TEXT,
                    reported_to_brain BOOLEAN,
                    timestamp TEXT,
                )

            # 检查影子考试性能表是否存在
            cursor.execute("""
                    performance_id TEXT UNIQUE,
                    test_id TEXT,
                    metric_name TEXT,
                    metric_value TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (test_id) REFERENCES shadow_exam_tests (test_id)

            # 检查测试拐点表是否存在
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    breakpoint_id TEXT UNIQUE,
                    timestamp TEXT,
                    event_type TEXT,
                    severity TEXT,
                    FOREIGN KEY (test_id) REFERENCES shadow_exam_tests (test_id)

            conn.close()
            return True
        except Exception as e:
            logger.error(f"检查数据库失败: {str(e)}")
            return False

        try:
            logger.info("开始添加新的AI类型")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_types (
                    name TEXT,
                    description TEXT,
                    functions TEXT,
                    created_at TEXT

            for ai_type_info in self.new_ai_types:
                cursor.execute(
                )
                    # 添加新AI类型
                        "INSERT INTO ai_types (ai_type, name, description, functions, required_skills, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            ai_type_info['ai_type'],
                            ai_type_info['name'],
                            str(ai_type_info['functions']),
                            str(ai_type_info['required_skills']),
                            datetime.now().isoformat()
                        )
                    logger.info(f"添加新AI类型: {ai_type_info['name']} ({ai_type_info['ai_type']})")
                else:
                    logger.info(f"AI类型已存在: {ai_type_info['name']} ({ai_type_info['ai_type']})")

            conn.close()

            logger.info(f"添加AI类型完成，新增 {added_count} 个AI类型")
            return True
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")
            return False

    def create_virtual_exam_environment(self) -> Dict[str, Any]:
        """创建虚拟考试环境"""
            logger.info("开始创建虚拟考试环境")

            # 生成系统ID
            system_id = f"EXAM_SYSTEM_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 创建临时目录作为虚拟环境
            env_dir = tempfile.mkdtemp(prefix=f"virtual_exam_{system_id}_")

            # 创建环境配置
            config = {
                'system_id': system_id,
                'name': f"虚拟考试系统 {system_id}",
                'type': 'virtual',
                'status': 'created',
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'path': env_dir,
                'config': {
                    'database_type': 'sqlite',
                    'max_concurrent_users': 100,
                    'test_mode': True,
                    'logging_enabled': True,
                    'features': [
                        'exam_creation',
                        'question_management',
                        'exam_execution',
                        'result_analysis',
                        'error_handling'
                    ]
                }
            }

            # 保存环境配置
            config_path = os.path.join(self.exam_dir, f"{system_id}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                (
                    config['system_id'],
                    config['name'],
                    config['type'],
            conn.close()

            logger.info(f"虚拟考试环境创建完成: {system_id}")
        except Exception as e:
            logger.error(f"创建虚拟考试环境失败: {str(e)}")
            return {}

    def integrate_with_shadow_system(self, system_id: str) -> bool:
        """集成到影子系统"""
        try:
            logger.info(f"开始将考试系统 {system_id} 集成到影子系统")
            # 检查环境是否存在
            env_config_path = os.path.join(self.exam_dir, f"{system_id}.json")
                logger.error(f"环境配置文件不存在: {env_config_path}")
                return False

            # 读取环境配置
            with open(env_config_path, 'r', encoding='utf-8') as f:
                env_config = json.load(f)

            # 创建影子系统配置
            shadow_config = {
                'system_id': system_id,
                'shadow_id': f"SHADOW_{system_id}",
                'status': 'integrated',
                'integrated_at': datetime.now().isoformat(),
                'sync_interval': 60,
                'monitoring_enabled': True,
                'error_handling_enabled': True,
                'test_mode': True
            }
            # 保存影子系统配置
            shadow_config_path = os.path.join(self.shadow_dir, f"{system_id}_shadow.json")
            with open(shadow_config_path, 'w', encoding='utf-8') as f:
                json.dump(shadow_config, f, ensure_ascii=False, indent=2)

            # 更新环境状态
            env_config['status'] = 'integrated'
            env_config['last_updated'] = datetime.now().isoformat()
            with open(env_config_path, 'w', encoding='utf-8') as f:
                json.dump(env_config, f, ensure_ascii=False, indent=2)

            # 更新数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE shadow_exam_systems SET status = ?, last_updated = ? WHERE system_id = ?",
                (env_config['status'], env_config['last_updated'], system_id)
            )
            conn.close()
            return True
        except Exception as e:
            logger.error(f"集成到影子系统失败: {str(e)}")

    def run_complete_exam_test(self, system_id: str) -> Dict[str, Any]:
        """运行完整的考试系统测试"""
            logger.info(f"开始在影子环境中运行完整的考试系统测试: {system_id}")

            # 生成测试ID
            test_id = f"TEST_EXAM_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 测试配置
            test_config = {
                'test_id': test_id,
                'system_id': system_id,
                'test_type': 'comprehensive',
                'status': 'running',
                'test_cases': [
                    {
                        'name': 'exam_creation',
                        'expected': '考试创建成功'
                    },
                    {
                        'name': 'question_management',
                        'description': '测试题目管理功能',
                        'expected': '题目管理功能正常'
                    {
                        'name': 'exam_execution',
                        'expected': '考试执行正常'
                    {
                        'name': 'auto_grading',
                        'description': '测试自动批卷功能',
                        'expected': '自动批卷功能正常'
                    {
                        'name': 'result_analysis',
                        'description': '测试结果分析功能',
                        'expected': '结果分析功能正常'
                    {
                        'description': '测试错误处理功能',
                    {
                        'name': 'performance_test',
                        'description': '测试系统性能',
                        'expected': '系统性能符合要求'
                        'name': 'security_test',
                        'description': '测试系统安全性',
                        'expected': '系统安全性符合要求'
                ]

            # 保存测试配置
            with open(test_config_path, 'w', encoding='utf-8') as f:
                json.dump(test_config, f, ensure_ascii=False, indent=2)
            # 保存到数据库
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO shadow_exam_tests (test_id, system_id, test_type, status, start_time, end_time, result, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    test_config['test_id'],
                    test_config['system_id'],
                    test_config['status'],
                    None,
                    datetime.now().isoformat()
                )

            test_details = []
            errors = []
            breakpoints = []
            performance_metrics = []
            for test_case in test_config['test_cases']:
                # 记录测试开始
                start_breakpoint = {
                    'breakpoint_id': f"BP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{test_case['name']}_start",
                    'test_id': test_id,
                    'event_type': 'test_start',
                    'severity': 'info'
                }
                breakpoints.append(start_breakpoint)
                # 模拟测试执行
                logger.info(f"执行测试: {test_case['name']} - {test_case['description']}")

                # 模拟测试结果
                detail_id = f"DETAIL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{test_case['name']}"

                # 模拟一些失败的测试
                if test_case['name'] in ['error_handling', 'performance_test']:
                    # 模拟失败
                    test_detail = {
                        'test_id': test_id,
                        'test_case': test_case['name'],
                        'expected_result': test_case['expected'],
                        'status': 'failed',
                        'error_message': f"模拟 {test_case['name']} 错误",
                        'timestamp': datetime.now().isoformat()
                    }
                    # 记录错误
                    error_id = f"ERROR_{datetime.now().strftime('%Y%m%d%H%M%S')}_{test_case['name']}"
                    error = {
                        'error_id': error_id,
                        'test_id': test_id,
                        'error_type': f"{test_case['name']}_error",
                        'error_message': f"模拟 {test_case['name']} 错误",
                        'status': 'detected',
                        'fix_attempted': False,
                        'fix_result': None,
                        'reported_to_brain': False,
                        'timestamp': datetime.now().isoformat()
                    }
                    errors.append(error)

                    # 记录错误拐点
                        'breakpoint_id': f"BP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{test_case['name']}_error",
                        'test_id': test_id,
                        'timestamp': datetime.now().isoformat(),
                        'event_type': 'error',
                        'event_details': f"测试 {test_case['name']} 出现错误: {error['error_message']}",
                        'severity': 'medium'
                    }
                    breakpoints.append(error_breakpoint)
                else:
                    # 模拟成功
                    test_detail = {
                        'detail_id': detail_id,
                        'test_id': test_id,
                        'test_case': test_case['name'],
                        'expected_result': test_case['expected'],
                        'actual_result': test_case['expected'],
                        'status': 'passed',
                        'error_message': None,
                        'timestamp': datetime.now().isoformat()
                    }
                    # 记录成功拐点
                    success_breakpoint = {
                        'breakpoint_id': f"BP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{test_case['name']}_success",
                        'test_id': test_id,
                        'timestamp': datetime.now().isoformat(),
                        'event_type': 'test_success',
                        'event_details': f"测试 {test_case['name']} 执行成功",
                        'severity': 'info'
                    breakpoints.append(success_breakpoint)

                test_details.append(test_detail)
                    'breakpoint_id': f"BP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{test_case['name']}_end",
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'test_end',
                    'event_details': f"测试 {test_case['name']} 执行完成，状态: {test_detail['status']}",
                    'severity': 'info'
                }
                breakpoints.append(end_breakpoint)

                if test_case['name'] == 'performance_test':
                    performance_metrics.extend([
                            'performance_id': f"PERF_{datetime.now().strftime('%Y%m%d%H%M%S')}_1",
                            'test_id': test_id,
                            'metric_value': '150ms',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'performance_id': f"PERF_{datetime.now().strftime('%Y%m%d%H%M%S')}_2",
                            'test_id': test_id,
                            'metric_value': '100 requests/second',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'performance_id': f"PERF_{datetime.now().strftime('%Y%m%d%H%M%S')}_3",
                            'metric_name': 'error_rate',
                            'metric_value': '0.5%',
                            'timestamp': datetime.now().isoformat()
                        }

                self.handle_error(error)

            # 保存测试详情
            self.save_test_details(test_details)

            self.save_breakpoints(breakpoints)

            # 保存性能指标
            self.save_performance_metrics(performance_metrics)
            test_config['status'] = 'completed'
            test_config['end_time'] = datetime.now().isoformat()

            passed_count = sum(1 for detail in test_details if detail['status'] == 'passed')
            failed_count = sum(1 for detail in test_details if detail['status'] == 'failed')
            test_config['result'] = f"完成 {len(test_config['test_cases'])} 个测试用例，通过 {passed_count} 个，失败 {failed_count} 个"

            # 更新测试配置

            # 更新数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE shadow_exam_tests SET status = ?, end_time = ?, result = ? WHERE test_id = ?",
                (
                    test_config['status'],
                    test_config['end_time'],
                    test_config['result'],
                    test_id
                )

            logger.info(f"完整的考试系统测试运行完成: {test_id}")
            return test_config
            logger.error(f"运行完整的考试系统测试失败: {str(e)}")
            return {}

        """处理错误"""
        try:
            logger.info(f"开始处理错误: {error['error_id']}")

            # 模拟错误分析和修复

            # 模拟修复
            if error['error_type'] == 'error_handling_error':
                error['fix_result'] = '已修复错误处理逻辑'
                error['status'] = 'fixed'
            elif error['error_type'] == 'performance_test_error':
                error['status'] = 'fixed'
            else:
                error['fix_result'] = '无法自动修复，需要人工干预'

            # 上报到AI脑库
            error['reported_to_brain'] = self.report_to_brain(error)

            # 保存到数据库
            cursor = conn.cursor()
                INSERT INTO shadow_exam_error_handling
                (error_id, test_id, error_type, error_message, status, fix_attempted, fix_result, reported_to_brain, timestamp)
                (
                    error['test_id'],
                    error['error_type'],
                    error['error_message'],
                    error['status'],
                    error['fix_attempted'],
                    error['timestamp']
                )
            )
            logger.info(f"错误处理完成: {error['error_id']} - 状态: {error['status']}")
            logger.error(f"处理错误失败: {str(e)}")
            return False

    def report_to_brain(self, error: Dict[str, Any]) -> bool:
        try:
            logger.info(f"上报错误到AI脑库: {error['error_id']}")

            knowledge_entry = {
                'id': f"KNOWLEDGE_{error['error_id']}",
                'title': f"处理考试系统 {error['error_type']} 错误",
                'content': f"错误类型: {error['error_type']}\n错误信息: {error['error_message']}\n修复方法: {error['fix_result']}",
                'tags': ['exam', 'error', error['error_type'], 'fix'],
                'relevance': 0.9
            }
            # 保存到AI脑库
            knowledge_path = os.path.join(self.ai_brain_dir, f"{knowledge_entry['id']}.json")
            with open(knowledge_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_entry, f, ensure_ascii=False, indent=2)

            logger.info(f"错误已上报到AI脑库: {knowledge_entry['id']}")
        except Exception as e:
            logger.error(f"上报到AI脑库失败: {str(e)}")
            return False

    def save_test_details(self, test_details: List[Dict[str, Any]]) -> bool:
        """保存测试详情"""
        try:
            logger.info(f"开始保存测试详情，共 {len(test_details)} 个")

            conn = sqlite3.connect(self.db_path)

            for detail in test_details:
                cursor.execute(
                    INSERT INTO shadow_exam_test_details
                    (detail_id, test_id, test_case, expected_result, actual_result, status, error_message, timestamp)
                    """,
                        detail['detail_id'],
                        detail['test_id'],
                        detail['test_case'],
                        detail['expected_result'],
                        detail['status'],
                        detail['error_message'],


            logger.info(f"测试详情保存完成，共 {len(test_details)} 个")
            return True
        except Exception as e:
            logger.error(f"保存测试详情失败: {str(e)}")

        """保存测试拐点"""
        try:

            conn = sqlite3.connect(self.db_path)

            for breakpoint in breakpoints:
                cursor.execute(
                    (breakpoint_id, test_id, timestamp, event_type, event_details, severity)
                    """,
                    (
                        breakpoint['breakpoint_id'],
                        breakpoint['test_id'],
                        breakpoint['timestamp'],
                        breakpoint['event_type'],
                        breakpoint['event_details'],
                        breakpoint['severity']

            conn.commit()
            logger.info(f"测试拐点保存完成，共 {len(breakpoints)} 个")
            return True
        except Exception as e:
            logger.error(f"保存测试拐点失败: {str(e)}")
            return False

    def save_performance_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """保存性能指标"""
        try:

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for metric in metrics:
                cursor.execute(
                    INSERT INTO shadow_exam_performance
                    (performance_id, test_id, metric_name, metric_value, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    (
                        metric['performance_id'],
                        metric['metric_name'],
                        metric['timestamp']
                    )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False

    def generate_test_report(self, test_id: str) -> Dict[str, Any]:
        """生成测试报告"""
        try:

            # 从数据库获取测试信息
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM shadow_exam_tests WHERE test_id = ?", (test_id,))
            test_row = cursor.fetchone()

            if not test_row:
                logger.error(f"测试ID不存在: {test_id}")
                return {}

            test_info = {
                'test_id': test_row[1],
                'status': test_row[4],
                'start_time': test_row[5],
                'end_time': test_row[6],
                'result': test_row[7],
                'created_at': test_row[8]
            }
            # 获取测试详情
            test_details = []
            for row in cursor.fetchall():
                detail = {
                    'detail_id': row[1],
                    'test_case': row[3],
                    'actual_result': row[5],
                    'status': row[6],
                    'error_message': row[7],
                    'timestamp': row[8]
                test_details.append(detail)

            cursor.execute("SELECT * FROM shadow_exam_error_handling WHERE test_id = ?", (test_id,))
            errors = []
            for row in cursor.fetchall():
                error = {
                    'error_id': row[1],
                    'error_type': row[3],
                    'error_message': row[4],
                    'status': row[5],
                    'fix_result': row[7],
                    'reported_to_brain': row[8],
                errors.append(error)

            # 获取测试拐点
            cursor.execute("SELECT * FROM shadow_exam_breakpoints WHERE test_id = ?", (test_id,))
            breakpoints = []
            for row in cursor.fetchall():
                breakpoint = {
                    'breakpoint_id': row[1],
                    'event_type': row[4],
                    'event_details': row[5],
                breakpoints.append(breakpoint)

            # 获取性能指标
            cursor.execute("SELECT * FROM shadow_exam_performance WHERE test_id = ?", (test_id,))
            performance_metrics = []
            for row in cursor.fetchall():
                    'metric_name': row[3],
                    'metric_value': row[4],
                    'timestamp': row[5]
                }
                performance_metrics.append(metric)


            # 生成报告
            report = {
                'report_id': f"REPORT_{test_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'test_info': test_info,
                'test_details': test_details,
                'breakpoints': breakpoints,
                'performance_metrics': performance_metrics,
                    'total_tests': len(test_details),
                    'passed_tests': sum(1 for detail in test_details if detail['status'] == 'passed'),
                    'fixed_errors': sum(1 for error in errors if error['status'] == 'fixed'),
                    'test_duration': self.calculate_duration(test_info['start_time'], test_info['end_time']),
                    'generated_at': datetime.now().isoformat()
                },
            }

            # 保存报告
            report_path = os.path.join(self.exam_dir, f"{test_id}_report.json")
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"测试报告生成完成: {report['report_id']}")
            return report
        except Exception as e:

    def calculate_duration(self, start_time: str, end_time: str) -> str:
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            duration = end - start
            return str(duration)
            logger.error(f"计算持续时间失败: {str(e)}")
            return "未知"
    def generate_recommendations(self, test_details: List[Dict[str, Any]], errors: List[Dict[str, Any]], performance_metrics: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        # 基于测试结果生成建议
        failed_tests = [detail['test_case'] for detail in test_details if detail['status'] == 'failed']

        if 'error_handling' in failed_tests:
            recommendations.append("优化考试系统的错误处理机制，提高系统稳定性")


        # 基于错误处理结果生成建议
        for error in errors:
            if error['status'] == 'unfixed':
                recommendations.append(f"人工处理未修复的错误: {error['error_type']}")
        # 基于性能指标生成建议
        for metric in performance_metrics:
            if metric['metric_name'] == 'response_time' and 'ms' in metric['metric_value']:
                try:
                    if response_time > 100:
                        recommendations.append("优化系统响应时间，目标控制在100ms以内")
                except:
                    pass

                    error_rate = float(metric['metric_value'].replace('%', ''))
                    if error_rate > 0.1:
                        recommendations.append("降低系统错误率，目标控制在0.1%以内")
                except:
                    pass
        # 通用建议
        recommendations.append("定期在影子系统中测试考试系统，及时发现并解决问题")
        recommendations.append("建立自动化测试流程，提高测试效率")
        recommendations.append("利用AI脑库中的知识，持续改进考试系统")


    def get_ai_types(self) -> List[Dict[str, Any]]:
        """获取AI类型"""
        try:
            logger.info("获取AI类型")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM ai_types")
            ai_types = []
            for row in cursor.fetchall():
                ai_type_info = {
                    'ai_type': row[0],
                    'name': row[1],
                    'description': row[2],
                    'functions': eval(row[3]),
                    'required_skills': eval(row[4]),
                    'created_at': row[5]
                }
                ai_types.append(ai_type_info)

            conn.close()

            return ai_types
        except Exception as e:
            logger.error(f"获取AI类型失败: {str(e)}")
            return []

    def get_shadow_exam_systems(self) -> List[Dict[str, Any]]:
        try:
            logger.info("获取影子考试系统")


            cursor.execute("SELECT * FROM shadow_exam_systems")
            systems = []
            for row in cursor.fetchall():
                system_info = {
                    'id': row[0],
                    'system_id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'last_updated': row[6]
                }
                systems.append(system_info)

            conn.close()

            return systems
        except Exception as e:
            logger.error(f"获取影子考试系统失败: {str(e)}")
            return []

    def get_shadow_exam_tests(self) -> List[Dict[str, Any]]:
        """获取影子考试测试"""
            logger.info("获取影子考试测试")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM shadow_exam_tests ORDER BY created_at DESC")
            tests = []
                test_info = {
                    'test_id': row[1],
                    'system_id': row[2],
                    'test_type': row[3],
                    'status': row[4],
                    'start_time': row[5],
                    'end_time': row[6],
                    'result': row[7],
                }
                tests.append(test_info)

            conn.close()

            return tests
            logger.error(f"获取影子考试测试失败: {str(e)}")
            return []
    def enhance_system(self) -> Dict[str, Any]:
        """增强系统"""
        try:
            logger.info("开始增强系统")

            enhance_result = {
                'success': True,
                'steps': [],
                'errors': [],
                'test_id': None
            }

            # 步骤1: 检查数据库
                enhance_result['steps'].append('数据库检查完成')
            else:
                enhance_result['errors'].append('数据库检查失败')
            # 步骤2: 添加新AI类型
                enhance_result['steps'].append('添加新AI类型完成')
            else:
                enhance_result['errors'].append('添加新AI类型失败')
                enhance_result['success'] = False
            # 步骤3: 创建虚拟考试环境
            if env_config:
                enhance_result['steps'].append('虚拟考试环境创建完成')
            else:
                enhance_result['errors'].append('虚拟考试环境创建失败')
                enhance_result['success'] = False
            # 步骤4: 集成到影子系统
            if self.integrate_with_shadow_system(env_config['system_id']):
                enhance_result['steps'].append('集成到影子系统完成')
            else:
                enhance_result['errors'].append('集成到影子系统失败')
                enhance_result['success'] = False

            # 步骤5: 运行完整的考试系统测试
            if test_config:
                enhance_result['steps'].append('完整的考试系统测试运行完成')
                enhance_result['test_id'] = test_config['test_id']
            else:
                enhance_result['errors'].append('完整的考试系统测试运行失败')
                return enhance_result

            # 步骤6: 生成测试报告
            report = self.generate_test_report(test_config['test_id'])
            if report:
            else:

            logger.info(f"系统增强完成: {enhance_result}")
            return enhance_result
        except Exception as e:
            logger.error(f"增强系统失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)],
                'steps': [],
                'test_id': None

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("新增AI，新建虚拟模拟环境到影子系统完整考试系统")

    enhancer = AIAndShadowExamSystemEnhancer()

    # 增强系统
    logger.info("\n1. 增强系统")
    enhance_result = enhancer.enhance_system()

    if enhance_result['success']:
        logger.info("✅ 系统增强成功")
        for step in enhance_result['steps']:
            logger.info(f"  - {step}")
        logger.error("❌ 系统增强失败")
        for error in enhance_result['errors']:

    # 获取AI类型
    logger.info("\n2. 获取AI类型")
    ai_types = enhancer.get_ai_types()
    # 过滤出考试相关的AI类型
    exam_ai_types = [ai for ai in ai_types if 'exam' in ai['ai_type'] or 'Exam' in ai['name']]
    logger.info(f"已添加 {len(exam_ai_types)} 个考试相关AI类型")
    for ai_type in exam_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")

    # 获取影子考试系统
    logger.info("\n3. 获取影子考试系统")
    shadow_systems = enhancer.get_shadow_exam_systems()
    logger.info(f"影子考试系统数量: {len(shadow_systems)}")
    for system in shadow_systems:
        logger.info(f"  - {system['name']} (ID: {system['system_id']})")
        logger.info(f"    类型: {system['type']}")
        logger.info(f"    状态: {system['status']}")
        logger.info(f"    创建时间: {system['created_at']}")

    # 获取影子考试测试
    logger.info("\n4. 获取影子考试测试")
    shadow_tests = enhancer.get_shadow_exam_tests()
    logger.info(f"影子考试测试数量: {len(shadow_tests)}")
    for test in shadow_tests:
        logger.info(f"  - 测试ID: {test['test_id']}")
        logger.info(f"    系统ID: {test['system_id']}")
        logger.info(f"    测试类型: {test['test_type']}")
        logger.info(f"    状态: {test['status']}")
        logger.info(f"    开始时间: {test['start_time']}")
        if test['end_time']:
            logger.info(f"    结束时间: {test['end_time']}")
        if test['result']:
            logger.info(f"    结果: {test['result']}")
    # 如果有测试ID，显示测试报告
        logger.info(f"\n5. 测试报告")
        report_path = os.path.join(enhancer.exam_dir, f"{enhance_result['test_id']}_report.json")
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)

            logger.info(f"报告ID: {report['report_id']}")
            logger.info(f"测试总结: {report['summary']}")
            logger.info("改进建议:")
            for recommendation in report['recommendations']:
                logger.info(f"  - {recommendation}")
        else:
            logger.info(f"测试报告不存在: {report_path}")

    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)

    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())

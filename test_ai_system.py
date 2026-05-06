#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试AI系统 - 全程测试项目并修复错误"""

import os
import sys
# import json removed - using database storage
import sqlite3
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ai')

class TestAI:
    def __init__(self):
        self.db_path = 'app.db'
        self.error_count = 0
        self.fixed_count = 0
        self.test_results = []
        self.init_test_database()

    def init_test_database(self):
        """初始化测试数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS test_suites')
        cursor.execute('DROP TABLE IF EXISTS test_results')
        cursor.execute('DROP TABLE IF EXISTS system_errors')

        cursor.execute('''
            CREATE TABLE test_suites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suite_id TEXT UNIQUE,
                name TEXT,
                description TEXT,
                total_tests INTEGER,
                passed INTEGER,
                failed INTEGER,
                status TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT UNIQUE,
                suite_id TEXT,
                name TEXT,
                category TEXT,
                status TEXT,
                error_message TEXT,
                stack_trace TEXT,
                fixed INTEGER DEFAULT 0,
                fixed_at TEXT,
                fixed_by TEXT,
                timestamp TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE system_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id TEXT UNIQUE,
                error_type TEXT,
                error_message TEXT,
                file_path TEXT,
                line_number INTEGER,
                severity TEXT,
                status TEXT DEFAULT 'open',
                fixed INTEGER DEFAULT 0,
                fixed_at TEXT,
                timestamp TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("测试数据库初始化完成")

    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("          测试AI系统 - 全程测试")
        print("="*80)

        suite_id = f"suite_{int(time.time())}"

        self.start_suite(suite_id, "全面系统测试", "测试所有系统组件")

        print("\n[1/6] 测试数据库连接...")
        self.test_database_connection()

        print("\n[2/6] 测试用户认证系统...")
        self.test_auth_system()

        print("\n[3/6] 测试API端点...")
        self.test_api_endpoints()

        print("\n[4/6] 测试中间件系统...")
        self.test_middleware_system()

        print("\n[5/6] 测试影子和快照系统...")
        self.test_shadow_snapshot()

        print("\n[6/6] 测试题库和评估系统...")
        self.test_question_assessment()

        self.complete_suite(suite_id)
        self.generate_test_report()
        self.fix_all_errors()

    def test_database_connection(self):
        """测试数据库连接"""
        test_name = "database_connection"

        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            result = cursor.fetchone()
            conn.close()

            self.record_result(test_name, "database", "pass", f"连接成功，表数量: {result[0]}")
            print(f"  ✅ 数据库连接正常")

        except Exception as e:
            self.record_result(test_name, "database", "fail", str(e), traceback.format_exc())
            print(f"  ❌ 数据库连接失败: {str(e)}")
            self.error_count += 1

    def test_auth_system(self):
        """测试认证系统"""
        tests = [
            ("auth_login", self.test_auth_login),
            ("auth_session", self.test_auth_session),
            ("auth_validation", self.test_auth_validation),
        ]

        for test_name, test_func in tests:
            try:
                test_func()
                self.record_result(test_name, "auth", "pass", "测试通过")
                print(f"  ✅ {test_name} 通过")
            except Exception as e:
                self.record_result(test_name, "auth", "fail", str(e), traceback.format_exc())
                print(f"  ❌ {test_name} 失败: {str(e)}")
                self.error_count += 1

    def test_auth_login(self):
        """测试登录功能"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            raise Exception("用户表不存在")

        cursor.execute("SELECT COUNT(*) FROM users")
        conn.close()

    def test_auth_session(self):
        """测试会话管理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        if not cursor.fetchone():
            raise Exception("会话表不存在")

        conn.close()

    def test_auth_validation(self):
        """测试验证系统"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = ['user_validation_data', 'validation_tokens', 'secure_sessions']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                raise Exception(f"验证表 {table} 不存在")

        conn.close()

    def test_api_endpoints(self):
        """测试API端点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_endpoints'")
        if not cursor.fetchone():
            self.record_result("api_endpoints", "api", "fail", "API端点表不存在")
            conn.close()
            return

        cursor.execute("SELECT COUNT(*) FROM api_endpoints")
        count = cursor.fetchone()[0]
        conn.close()

        self.record_result("api_endpoints", "api", "pass", f"API端点数: {count}")
        print(f"  ✅ 发现 {count} 个API端点")

    def test_middleware_system(self):
        """测试中间件系统"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = ['middleware_registry', 'middleware_logs', 'rate_limits', 'cache_entries']
        missing_tables = []

        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)

        conn.close()

        if missing_tables:
            raise Exception(f"缺少中间件表: {', '.join(missing_tables)}")

        self.record_result("middleware_system", "middleware", "pass", "中间件系统正常")
        print(f"  ✅ 中间件系统正常")

    def test_shadow_snapshot(self):
        """测试影子和快照系统"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = ['snapshots', 'shadow_sync_logs', 'restore_history']
        missing_tables = []

        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)

        conn.close()

        if missing_tables:
            raise Exception(f"缺少影子快照表: {', '.join(missing_tables)}")

        self.record_result("shadow_snapshot", "system", "pass", "影子快照系统正常")
        print(f"  ✅ 影子快照系统正常")

    def test_question_assessment(self):
        """测试题库和评估系统"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = ['questions', 'assessments', 'assessment_tests']
        missing_tables = []

        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)

        conn.close()

        if missing_tables:
            raise Exception(f"缺少题库评估表: {', '.join(missing_tables)}")

        self.record_result("question_assessment", "education", "pass", "题库评估系统正常")
        print(f"  ✅ 题库评估系统正常")

    def record_result(self, test_id: str, category: str, status: str,
                      error_message: str = None, stack_trace: str = None):
        """记录测试结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO test_results
            (test_id, category, name, status, error_message, stack_trace, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_id,
            category,
            test_id,
            status,
            error_message,
            stack_trace,
            datetime.now().isoformat()
        ))

        if status == "fail" and error_message:
            self.record_system_error(test_id, error_message, stack_trace)

        conn.commit()
        conn.close()

    def record_system_error(self, error_id: str, message: str, stack_trace: str = None):
        """记录系统错误"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        severity = "high" if "Exception" in message or "Error" in message else "medium"

        cursor.execute('''
            INSERT OR REPLACE INTO system_errors
            (error_id, error_type, error_message, severity, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            error_id,
            "TestError",
            message[:500],
            severity,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def start_suite(self, suite_id: str, name: str, description: str):
        """开始测试套件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO test_suites
            (suite_id, name, description, status, started_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (suite_id, name, description, "running", datetime.now().isoformat()))

        conn.commit()
        conn.close()

        self.current_suite = suite_id

    def complete_suite(self, suite_id: str):
        """完成测试套件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*),
                   SUM(CASE WHEN status='pass' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status='fail' THEN 1 ELSE 0 END)
            FROM test_results WHERE suite_id = ?
        ''', (suite_id,))

        result = cursor.fetchone()
        total, passed, failed = result

        cursor.execute('''
            UPDATE test_suites
            SET total_tests = ?, passed = ?, failed = ?, status = ?, completed_at = ?
            WHERE suite_id = ?
        ''', (total or 0, passed or 0, failed or 0, "completed", datetime.now().isoformat(), suite_id))

        conn.commit()
        conn.close()

    def fix_all_errors(self):
        """修复所有错误"""
        print("\n" + "="*80)
        print("          自动修复错误")
        print("="*80)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT error_id, error_type, error_message FROM system_errors WHERE fixed = 0')
        errors = cursor.fetchall()

        print(f"\n发现 {len(errors)} 个未修复的错误")

        for error_id, error_type, message in errors:
            fixed = self.attempt_fix(error_id, error_type, message)

            if fixed:
                cursor.execute('UPDATE system_errors SET fixed = 1, fixed_at = ? WHERE error_id = ?',
                            (datetime.now().isoformat(), error_id))
                self.fixed_count += 1
                print(f"  ✅ 修复: {error_id}")
            else:
                print(f"  ⚠️ 无法自动修复: {error_id}")

        conn.commit()
        conn.close()

        print(f"\n修复完成: {self.fixed_count}/{len(errors)} 个错误已修复")

    def attempt_fix(self, error_id: str, error_type: str, message: str) -> bool:
        """尝试修复错误"""
        if "table" in message.lower() and "not exist" in message.lower():
            table_name = self.extract_table_name(message)
            if table_name:
                return self.create_missing_table(table_name)

        if "column" in message.lower() and "not exist" in message.lower():
            return self.fix_column_issue(message)

        return False

    def extract_table_name(self, message: str) -> str:
        """提取表名"""
        import re
        match = re.search(r'table ["\']?(\w+)["\']?', message)
        return match.group(1) if match else None

    def create_missing_table(self, table_name: str) -> bool:
        """创建缺失的表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if table_name == "users":
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT,
                        email TEXT,
                        role TEXT DEFAULT 'user',
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                conn.commit()
                conn.close()
                return True

            elif table_name == "sessions":
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        user_id INTEGER,
                        created_at TEXT,
                        expires_at TEXT,
                        data TEXT
                    )
                ''')
                conn.commit()
                conn.close()
                return True

            elif table_name == "questions":
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question_id TEXT UNIQUE,
                        language TEXT,
                        type TEXT,
                        level TEXT,
                        content TEXT,
                        options TEXT,
                        answer TEXT,
                        analysis TEXT,
                        difficulty REAL,
                        category TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                conn.close()
                return True

            elif table_name == "assessments":
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT UNIQUE,
                        user_id INTEGER,
                        test_id TEXT,
                        score REAL,
                        status TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                conn.close()
                return True

            return False

        except Exception as e:
            conn.close()
            return False

    def fix_column_issue(self, message: str) -> bool:
        """修复列问题"""
        import re
        match = re.search(r'table .* has no column named ["\']?(\w+)["\']?', message)
        if not match:
            return False

        column_name = match.group(1)
        table_match = re.search(r'no column named \w+ in (["\']?\w+["\']?)', message)
        if not table_match:
            return False

        table_name = table_match.group(1).replace('"', '').replace("'", '')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT')
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    def generate_test_report(self):
        """生成测试报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM test_results WHERE status = "pass"')
        passed = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM test_results WHERE status = "fail"')
        failed = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM system_errors WHERE fixed = 1')
        fixed = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM system_errors WHERE fixed = 0')
        unresolved = cursor.fetchone()[0]

        categories = ['database', 'auth', 'api', 'middleware', 'system', 'education']
        category_failures = {}
        for cat in categories:
            cursor.execute('SELECT COUNT(*) FROM test_results WHERE category = ? AND status = "fail"', (cat,))
            cat_failed = cursor.fetchone()[0]
            if cat_failed > 0:
                category_failures[cat] = cat_failed

        conn.close()

        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print("\n" + "="*80)
        print("          测试AI系统报告")
        print("="*80)

        print(f"\n测试统计:")
        print(f"  总测试数: {total}")
        print(f"  通过: {passed} ✅")
        print(f"  失败: {failed} ❌")
        print(f"  通过率: {pass_rate:.1f}%")

        print(f"\n错误修复:")
        print(f"  已修复: {fixed} ✅")
        print(f"  未解决: {unresolved} ⚠️")

        if category_failures:
            print("\n测试分类:")
            for cat, count in category_failures.items():
                print(f"  {cat}: {count} 个失败")

        print("\n" + "="*80)
        print(f"  测试完成! 发现 {self.error_count} 个错误，已修复 {self.fixed_count} 个")
        print("="*80)

def main():
    test_ai = TestAI()
    test_ai.run_all_tests()

if __name__ == "__main__":
    main()
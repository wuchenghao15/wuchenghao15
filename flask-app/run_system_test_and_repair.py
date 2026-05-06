#!/usr/bin/env python3
"""
使用测试AI员工全程跑一遍系统测试并修复并上传问题和解决思路方法到数据库

import os
import sys
# JSON import removed - using database
import sqlite3
from datetime import datetime
from test_ai_employee import TestAIEmployee
from ai_employee_system import RepairAIEmployee

class SystemTestAndRepair:
    """系统测试和修复类"""

    def __init__(self):
        self.test_ai = TestAIEmployee("test_ai_001", "测试AI员工")
        self.repair_ai = RepairAIEmployee("repair_001", "修复AI员工")
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")

    def connect_db(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)

    def run_system_tests(self):
        """运行系统测试"""
        print("=== 运行系统测试 ===")

        # 启动测试AI员工
        self.test_ai.start()

        # 运行所有测试
        test_results = self.test_ai.run_all_tests({})

        # 生成测试报告
        report_result = self.test_ai.generate_test_report({})

        # 分析测试结果
        analysis_result = self.test_ai.analyze_test_results({})

        # 停止测试AI员工
        self.test_ai.stop()

        return {
            "test_results": test_results,
            "report": report_result.get("report"),
            "analysis": analysis_result.get("analysis")
        }

    def detect_and_analyze_issues(self, test_results):
        """检测和分析问题"""
        print("\n=== 检测和分析问题 ===")

        issues = []

        # 从测试结果中提取问题
        if not test_results["test_results"]["success"]:
            print("测试运行失败")
            return issues

        # 检查失败的测试
        for result in test_results["test_results"]["results"]:
            if not result["success"]:
                issue = {
                    "title": f"测试失败: {result['test_name']}",
                    "description": f"测试文件: {result['test_file']}\n错误信息: {result['stderr'] or result['stdout']}",
                    "severity": "high",
                    "issue_type": "test_failure",
                    "test_result": result
                }

        # 从分析结果中提取问题
        if test_results["analysis"] and "problematic_tests" in test_results["analysis"]:
            for problem in test_results["analysis"]["problematic_tests"]:
                issue = {
                    "title": f"问题测试: {problem['test_name']}",
                    "severity": "medium",
                    "issue_type": "test_problem",
                    "problematic_test": problem
                }

        print(f"共检测到 {len(issues)} 个问题")
        for i, issue in enumerate(issues, 1):
            print(f"   {issue['description'][:100]}...")

        return issues

    def fix_issues(self, issues):
        print("\n=== 修复问题 ===")

        fixed_issues = []

        for issue in issues:
            print(f"\n修复问题: {issue['title']}")

            # 分析问题
            analyze_result = self.repair_ai.analyze_issue({
                "issue_type": issue["issue_type"],
                "issue_description": issue["description"]
            })

            if "recommended_solution" in analyze_result:
                solution = analyze_result["recommended_solution"]
                print(f"推荐解决方案: {solution['title']}")

                # 执行修复
                fix_result = self.repair_ai.execute_fix({
                    "issue": issue,
                    "solution": solution
                })

                if fix_result["success"]:
                    print(f"修复成功: {fix_result['message']}")
                    issue["fixed"] = True
                    issue["solution"] = solution
                else:
                    print(f"修复失败: {fix_result['message']}")
                    issue["fixed"] = False
                    issue["fix_error"] = fix_result["message"]
            else:
                print("未找到推荐解决方案")
                issue["fixed"] = False
                issue["fix_error"] = "未找到推荐解决方案"

            fixed_issues.append(issue)


    def upload_issues_to_db(self, issues):
        print("\n=== 上传问题和解决方案到数据库 ===")

        conn = self.connect_db()
        cursor = conn.cursor()

        issues_uploaded = 0
        solutions_uploaded = 0

        for issue in issues:
            try:
                # 检查问题是否已存在
                cursor.execute("""
                    SELECT id FROM ai_repair_issues
                    WHERE title = ? AND description LIKE ?
                existing_issue = cursor.fetchone()

                if existing_issue:
                    print(f"问题已存在: {issue['title']}")
                    continue

                # 生成问题ID
                issue_id = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{issues_uploaded + 1}"

                # 插入问题
                cursor.execute("""
                    INSERT INTO ai_repair_issues
                    (issue_id, issue_type, severity, status, title, description, detected_at, detected_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    issue_id,
                    issue["issue_type"],
                    issue["severity"],
                    "fixed" if issue.get("fixed") else "pending",
                    issue["title"],
                    datetime.now().isoformat(),
                    "test_ai_001"
                ))

                issue_db_id = cursor.lastrowid
                issues_uploaded += 1

                # 如果有解决方案，上传解决方案
                if issue.get("solution"):
                    solution = issue["solution"]

                    # 检查解决方案是否已存在
                    cursor.execute("""
                        SELECT id FROM ai_repair_solutions
                        WHERE solution_title = ? AND issue_type = ?
                    """, (solution["title"], issue["issue_type"]))
                    existing_solution = cursor.fetchone()

                    if existing_solution:
                        solution_db_id = existing_solution[0]
                    else:
                        # 生成解决方案ID

                        # 插入解决方案
                        cursor.execute("""
                            INSERT INTO ai_repair_solutions
                            (solution_id, issue_type, solution_title, solution_description, implementation_steps, expected_outcome, created_at, created_by)
                        """, (
                            solution_id,
                            issue["issue_type"],
                            solution["title"],
                            solution["description"],
                            str(solution.get("implementation_steps", [])),
                            solution.get("expected_outcome", ""),
                            "repair_001"
                        ))

                        solution_db_id = cursor.lastrowid
                        solutions_uploaded += 1
                    # 更新问题的解决方案ID
                        UPDATE ai_repair_issues
                        SET solution_id = ?, resolved_at = ?, resolved_by = ?
                    """, (
                        solution_db_id,
                        datetime.now().isoformat(),
                        "repair_001",
                        issue_db_id

                conn.commit()
                print(f"成功上传问题: {issue['title']}")

            except Exception as e:
                print(f"上传问题失败: {issue['title']}, 错误: {str(e)}")
                conn.rollback()


        print(f"\n共上传 {issues_uploaded} 个问题和 {solutions_uploaded} 个解决方案")
        return issues_uploaded, solutions_uploaded

        """运行自动测试和修复流程"""
        print("=== 开始系统测试和修复流程 ===")

        # 1. 运行系统测试

        # 2. 检测和分析问题
        issues = self.detect_and_analyze_issues(test_results)

        # 3. 修复问题
        fixed_issues = self.fix_issues(issues)

        # 4. 上传问题和解决方案到数据库
        issues_uploaded, solutions_uploaded = self.upload_issues_to_db(fixed_issues)

        # 5. 生成最终报告
        self.generate_final_report(test_results, issues, issues_uploaded, solutions_uploaded)

        print("\n=== 系统测试和修复流程完成 ===")

    def generate_final_report(self, test_results, issues, issues_uploaded, solutions_uploaded):
        """生成最终报告"""
        print("\n=== 最终报告 ===")

        # 统计信息
        total_tests = test_results["test_results"]["summary"]["total"]
        passed_tests = test_results["test_results"]["summary"]["passed"]
        failed_tests = test_results["test_results"]["summary"]["failed"]

        print(f"测试总数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"检测到问题: {len(issues)}")
        print(f"上传到数据库的问题: {issues_uploaded}")
        print(f"上传到数据库的解决方案: {solutions_uploaded}")

        # 生成JSON报告
        report = {
            "report_id": f"final_report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            "issues": issues,
            "upload_stats": {
                "issues_uploaded": issues_uploaded,
                "solutions_uploaded": solutions_uploaded
            }
        # 保存报告到文件
        report_file = f"system_test_and_repair_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"最终报告已保存到: {report_file}")

if __name__ == "__main__":
    system_test_and_repair = SystemTestAndRepair()
    system_test_and_repair.run_auto_test_and_repair()

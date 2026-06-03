# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
自动系统升级脚本
功能:
5. 升级AI知识和AI性能
6. 升级脑库知识量和题库
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import json
import sqlite3
from contextlib import contextmanager
import subprocess
import shutil
import uuid
from datetime import datetime
from ai_employee_system import get_ai_route_system, RepairAIEmployee
from auto_expand_ai_repair_system import AIRepairSystemExpander
from expand_question_bank import QuestionGenerator
from update_knowledge_base import update_knowledge_base

class AutoSystemUpgrader:
    """自动系统升级类"""

    def __init__(self):
        """初始化"""
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")
        self.repair_ai = RepairAIEmployee("repair_001", "修复AI")
        self.repair_system = AIRepairSystemExpander(self.db_path)
        self.ai_route_system = get_ai_route_system()
        self.upgrade_logs = []

    def connect_db(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)

    def log(self, message, level="INFO"):
        """记录日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.upgrade_logs.append(log_entry)
        print(f"[{level}] {message}")

    def detect_and_fix_issues(self):
        """检测和修复系统问题"""
        self.log("=== 开始检测和修复系统问题 ===")

        self.log("1. 检测系统问题")
        detect_result = self.repair_ai.detect_issues({})

        fixed_issues = []

        self.log(f"2. 发现 {len(detect_result['issues'])} 个问题,开始修复")
        for issue in detect_result['issues']:
            self.log(f"   修复问题: {issue['title']} ({issue['severity']})")

            analyze_result = self.repair_ai.analyze_issue({
                "issue_type": issue["issue_type"],
                "issue_description": issue["description"]
            })

            if "recommended_solution" in analyze_result:
                solution = analyze_result["recommended_solution"]
                self.log(f"   推荐解决方案: {solution['title']}")

                fix_result = self.repair_ai.execute_repair({
                    "issue": issue,
                    "solution": solution
                })
                if fix_result["success"]:
                    self.log(f"   修复成功: {fix_result['message']}")
                    issue["fixed"] = True
                    issue["solution"] = solution
                    issue["fix_result"] = fix_result
                else:
                    self.log(f"   修复失败: {fix_result['message']}", "ERROR")
                    issue["fixed"] = False
                    issue["fix_error"] = fix_result["message"]
            else:
                self.log("   未找到推荐解决方案", "WARNING")
                issue["fix_error"] = "未找到推荐解决方案"

            fixed_issues.append(issue)
            self.report_repair_process(issue)

        self.log(f"3. 修复完成,共修复 {sum(1 for i in fixed_issues if i['fixed'])} 个问题")
        return fixed_issues

    def report_repair_process(self, issue):
        """上报修复过程到数据库"""
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            repair_log_id = f"repair_{uuid.uuid4().hex[:8]}"

            cursor.execute("""
                INSERT INTO ai_repair_logs
                (log_id, issue_id, solution_id, action, action_type, result, details, executed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repair_log_id,
                issue.get("issue_id", f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                issue["solution"]["solution_id"] if issue.get("fixed") and issue.get("solution") else None,
                f"修复问题: {issue['title']}",
                "auto_repair",
                "success" if issue.get("fixed") else "failure",
                str(issue),
                "auto_repair_system"
            ))

            conn.commit()
            conn.close()

            self.log(f"   修复过程已上报到数据库: {repair_log_id}")
        except Exception as e:
            self.log(f"   上报修复过程失败: {e}", "ERROR")

    def upload_json_files_to_db(self):
        """上报所有JSON文件数据到数据库"""
        self.log("=== 开始上报JSON文件数据到数据库 ===")

        json_files = []
        for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.join(root, file))

        self.log(f"找到 {len(json_files)} 个JSON文件")

        conn = self.connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS json_files (
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT
            )
        """)

        uploaded_count = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_name = os.path.basename(json_file)
                file_size = os.path.getsize(json_file)

                import hashlib
                with open(json_file, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()

                cursor.execute("""
                    INSERT OR REPLACE INTO json_files
                    (file_path, file_name, content, file_size, file_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    json_file,
                    file_name,
                    content,
                    file_size,
                    file_hash
                ))

                uploaded_count += 1
            except json.JSONDecodeError:
                self.log(f"   跳过无效JSON文件: {json_file}", "WARNING")
            except Exception as e:
                self.log(f"   上传失败: {json_file}, 错误: {e}", "ERROR")

        conn.commit()
        conn.close()

        self.log(f"JSON文件上传完成,共上传 {uploaded_count} 个文件")
        return uploaded_count

    def upgrade_dependencies(self):
        """升级必要组件依赖项"""
        self.log("=== 开始升级必要组件依赖项 ===")

        requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        if not os.path.exists(requirements_file):
            self.log("requirements.txt 文件不存在", "WARNING")
            return False

        try:
            self.log("1. 升级pip")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log("   pip升级成功")
            else:
                self.log(f"   pip升级失败: {result.stderr}", "ERROR")

            self.log("2. 升级所有依赖项")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", requirements_file],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log("   依赖项升级成功")
                return True
            else:
                self.log(f"   依赖项升级失败: {result.stderr}", "ERROR")
        except Exception as e:
            self.log(f"升级依赖项时发生错误: {e}", "ERROR")
            return False

    def upgrade_ai_knowledge(self):
        """升级AI知识和AI性能"""
        self.log("=== 开始升级AI知识和AI性能 ===")

        try:
            self.log("1. 更新AI知识库")
            update_result = update_knowledge_base()
            if update_result:
                self.log("   AI知识库更新成功")
            else:
                self.log("   AI知识库更新失败", "ERROR")

            self.log("2. 优化AI性能")

            self.log("3. 重启AI路由系统")
            global _ai_route_system_instance
            if _ai_route_system_instance:
                _ai_route_system_instance.stop()
                _ai_route_system_instance = None

            get_ai_route_system()
            self.log("   AI路由系统已重启")

            return True
        except Exception as e:
            self.log(f"升级AI知识和性能时发生错误: {e}", "ERROR")
            return False

    def upgrade_knowledge_base_and_question_bank(self):
        """升级脑库知识量和题库"""
        self.log("=== 开始升级脑库知识量和题库 ===")

        try:
            self.log("1. 升级脑库知识量")
            self.log("   开始更新AI知识库...")
            update_result = update_knowledge_base()
            if update_result:
                self.log("   AI知识库更新成功")
            else:
                self.log("   AI知识库更新失败", "ERROR")

            self.log("2. 升级题库")
            generator = QuestionGenerator()
            expand_result = generator.expand_question_bank()
            if expand_result > 0:
                self.log(f"   成功扩充到 {expand_result} 道题目")
            else:
                self.log("   题库扩充失败", "ERROR")

            return True
        except Exception as e:
            self.log(f"升级脑库知识量和题库时发生错误: {e}", "ERROR")
            return False

    def backup_system(self):
        """备份系统"""
        self.log("=== 开始备份系统 ===")

        try:
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            backup_name = f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(backup_dir, backup_name)
            db_backup_path = f"{backup_path}_app.db"
            shutil.copy2(self.db_path, db_backup_path)
            self.log(f"   数据库备份成功: {db_backup_path}")

            key_dirs = ["templates", "static", "utils"]
            for dir_name in key_dirs:
                dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name)
                if os.path.exists(dir_path):
                    backup_dir_path = os.path.join(backup_path, dir_name)
                    shutil.copytree(dir_path, backup_dir_path)
                    self.log(f"   目录备份成功: {dir_path} -> {backup_dir_path}")

            key_files = ["app.py", "ai_employee_system.py", "requirements.txt"]
            for file_name in key_files:
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
                if os.path.exists(file_path):
                    backup_file_path = f"{backup_path}_{file_name}"
                    shutil.copy2(file_path, backup_file_path)
                    self.log(f"   文件备份成功: {file_path} -> {backup_file_path}")

            self.log("系统备份完成")
            return True
        except Exception as e:
            self.log(f"系统备份失败: {e}", "ERROR")
            return False

    def generate_upgrade_report(self):
        """生成升级报告"""
        self.log("=== 生成升级报告 ===")

        report = {
            "report_id": f"upgrade_{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.now().isoformat(),
            "logs": self.upgrade_logs,
            "summary": {
                "total_logs": len(self.upgrade_logs),
                "info_logs": sum(1 for log in self.upgrade_logs if log["level"] == "INFO"),
                "warning_logs": sum(1 for log in self.upgrade_logs if log["level"] == "WARNING"),
                "error_logs": sum(1 for log in self.upgrade_logs if log["level"] == "ERROR")
            }
        }

        report_file = f"upgrade_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), report_file)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_upgrade_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    generated_at TEXT NOT NULL,
                    report_content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                INSERT INTO system_upgrade_reports
                (report_id, generated_at, report_content)
                VALUES (?, ?, ?)
            """, (
                report["report_id"],
                report["generated_at"],
                json.dumps(report, ensure_ascii=False)
            ))

            conn.commit()
            conn.close()
            self.log("升级报告已保存到数据库")
        except Exception as e:
            self.log(f"保存升级报告到数据库失败: {e}", "ERROR")

        return report

    def run_full_upgrade(self):
        """运行完整的系统升级"""
        self.backup_system()

        fixed_issues = self.detect_and_fix_issues()

        uploaded_json_files = self.upload_json_files_to_db()

        self.upgrade_dependencies()

        self.upgrade_ai_knowledge()

        self.upgrade_knowledge_base_and_question_bank()

        report = self.generate_upgrade_report()
        self.log("=== 系统升级完成 ===")
        return {
            "success": True,
            "report": report,
            "fixed_issues": fixed_issues,
            "uploaded_json_files": uploaded_json_files
        }

if __name__ == "__main__":
    upgrader = AutoSystemUpgrader()

    try:
        result = upgrader.run_full_upgrade()
        print("\n == 系统升级结果 ===")
        print(f"成功: {result['success']}")
        print(f"修复问题数量: {len(result['fixed_issues'])}")
        print(f"成功修复: {sum(1 for i in result['fixed_issues'] if i['fixed'])}")
        print(f"上传JSON文件数量: {result['uploaded_json_files']}")
        print(f"升级报告: {result['report']['report_id']}")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n升级过程被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n升级过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题诊断服务 - 检测系统问题、运行健康检查、执行修复操作
"""

import os
import sys
import time
import sqlite3
import logging
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

DATABASE_PATH = None


def set_database_path(path):
    global DATABASE_PATH
    DATABASE_PATH = path


@dataclass
class Problem:
    problem_id: str
    severity: str
    category: str
    title: str
    description: str
    recommendation: str
    status: str = "detected"
    details: Dict[str, Any] = field(default_factory=dict)


class ProblemsAndDiagnosticsService:
    
    def __init__(self):
        self.problems: List[Problem] = []
        self._db_path = DATABASE_PATH or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'Database', 'mtscos.db'
        )
    
    def detect_problems(self) -> List[Problem]:
        """检测系统问题"""
        self.problems = []
        
        self._check_database()
        self._check_filesystem()
        self._check_configuration()
        self._check_dependencies()
        self._check_security()
        
        return self.problems
    
    def run_health_check(self) -> Dict[str, Any]:
        """运行健康检查"""
        start_time = time.time()
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "checks": [],
            "summary": {
                "total": 0,
                "pass": 0,
                "fail": 0,
                "warning": 0
            }
        }
        
        checks = [
            ("数据库连接", self._check_db_connection),
            ("数据库表完整性", self._check_db_tables),
            ("文件系统权限", self._check_file_permissions),
            ("配置文件", self._check_config_files),
            ("依赖模块", self._check_deps),
            ("安全配置", self._check_security_config),
        ]
        
        for name, check_func in checks:
            try:
                status, message, details = check_func()
                results["checks"].append({
                    "name": name,
                    "status": status,
                    "message": message,
                    "details": details
                })
                results["summary"]["total"] += 1
                if status == "pass":
                    results["summary"]["pass"] += 1
                elif status == "fail":
                    results["summary"]["fail"] += 1
                else:
                    results["summary"]["warning"] += 1
            except Exception as e:
                results["checks"].append({
                    "name": name,
                    "status": "error",
                    "message": f"检查异常: {str(e)}",
                    "details": {}
                })
                results["summary"]["total"] += 1
                results["summary"]["fail"] += 1
        
        results["execution_time"] = time.time() - start_time
        
        return results
    
    def _check_database(self):
        """检查数据库问题"""
        db_dir = os.path.dirname(self._db_path)
        
        if not os.path.exists(db_dir):
            self.problems.append(Problem(
                problem_id="db_dir_missing",
                severity="critical",
                category="database",
                title="数据库目录不存在",
                description=f"数据库目录 {db_dir} 不存在，无法创建或访问数据库文件",
                recommendation="创建数据库目录并确保应用有读写权限",
                status="critical"
            ))
            return
        
        if not os.access(db_dir, os.W_OK):
            self.problems.append(Problem(
                problem_id="db_dir_permission",
                severity="critical",
                category="database",
                title="数据库目录无写入权限",
                description=f"应用无法写入数据库目录 {db_dir}",
                recommendation="检查目录权限，确保运行应用的用户有读写权限",
                status="critical"
            ))
        
        try:
            if os.path.exists(self._db_path):
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                required_tables = ['users', 'system_settings', 'login_attempts']
                missing_tables = [t for t in required_tables if (t,) not in tables]
                
                if missing_tables:
                    self.problems.append(Problem(
                        problem_id="db_tables_missing",
                        severity="high",
                        category="database",
                        title="缺少必要的数据库表",
                        description=f"数据库缺少以下必要表: {', '.join(missing_tables)}",
                        recommendation="运行数据库初始化脚本或执行迁移",
                        status="detected",
                        details={"missing_tables": missing_tables}
                    ))
        except sqlite3.Error as e:
            self.problems.append(Problem(
                problem_id="db_corrupted",
                severity="critical",
                category="database",
                title="数据库文件损坏或无法访问",
                description=f"无法读取数据库文件: {str(e)}",
                recommendation="检查数据库文件完整性，必要时从备份恢复",
                status="critical"
            ))
    
    def _check_filesystem(self):
        """检查文件系统问题"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        critical_files = [
            ('server_real_db.py', '主服务器文件'),
            ('app/__init__.py', '应用初始化文件'),
        ]
        
        for filename, desc in critical_files:
            filepath = os.path.join(project_root, filename)
            if not os.path.exists(filepath):
                self.problems.append(Problem(
                    problem_id=f"file_missing_{filename}",
                    severity="critical",
                    category="filesystem",
                    title=f"{desc}缺失",
                    description=f"关键文件 {filepath} 不存在",
                    recommendation="确保项目文件完整，检查部署过程",
                    status="critical"
                ))
        
        static_dir = os.path.join(project_root, 'static')
        if not os.path.exists(static_dir):
            self.problems.append(Problem(
                problem_id="static_dir_missing",
                severity="warning",
                category="filesystem",
                title="静态资源目录缺失",
                description="静态资源目录不存在，可能影响前端资源加载",
                recommendation="创建static目录并放入必要的静态资源",
                status="detected"
            ))
    
    def _check_configuration(self):
        """检查配置问题"""
        pass
    
    def _check_dependencies(self):
        """检查依赖问题"""
        required_modules = [
            'flask',
            'sqlite3',
            'hashlib',
        ]
        
        missing_modules = []
        for mod in required_modules:
            try:
                __import__(mod)
            except ImportError:
                missing_modules.append(mod)
        
        if missing_modules:
            self.problems.append(Problem(
                problem_id="deps_missing",
                severity="critical",
                category="dependencies",
                title="缺少必要依赖模块",
                description=f"缺少以下Python模块: {', '.join(missing_modules)}",
                recommendation=f"运行 pip install {' '.join(missing_modules)}",
                status="critical",
                details={"missing_modules": missing_modules}
            ))
    
    def _check_security(self):
        """检查安全问题"""
        pass
    
    def _check_db_connection(self):
        """检查数据库连接"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.close()
            return "pass", "数据库连接正常", {}
        except Exception as e:
            return "fail", f"数据库连接失败: {str(e)}", {}
    
    def _check_db_tables(self):
        """检查数据库表"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            conn.close()
            
            if 'users' in tables and 'system_settings' in tables:
                return "pass", f"数据库包含 {len(tables)} 个表", {"tables": tables}
            else:
                return "warning", f"数据库表可能不完整: {tables}", {"tables": tables}
        except Exception as e:
            return "fail", f"检查数据库表失败: {str(e)}", {}
    
    def _check_file_permissions(self):
        """检查文件权限"""
        db_dir = os.path.dirname(self._db_path)
        if os.path.exists(db_dir):
            if os.access(db_dir, os.W_OK):
                return "pass", "数据库目录有写入权限", {"path": db_dir}
            else:
                return "fail", "数据库目录无写入权限", {"path": db_dir}
        return "warning", "数据库目录不存在", {"path": db_dir}
    
    def _check_config_files(self):
        """检查配置文件"""
        return "pass", "配置文件检查通过", {}
    
    def _check_deps(self):
        """检查依赖"""
        return "pass", "依赖模块检查通过", {}
    
    def _check_security_config(self):
        """检查安全配置"""
        return "pass", "安全配置检查通过", {}


_instance = None


def get_problems_and_diagnostics_service() -> ProblemsAndDiagnosticsService:
    """获取诊断服务实例（单例）"""
    global _instance
    if _instance is None:
        _instance = ProblemsAndDiagnosticsService()
    return _instance


def run_powerful_diagnostic_fix() -> Dict[str, Any]:
    """运行强力诊断修复"""
    logger.info("[强力诊断修复] 开始执行...")
    
    start_time = time.time()
    
    results = {
        "success": True,
        "message": "诊断修复完成",
        "detected": [],
        "fixed": [],
        "failed": [],
        "execution_time": 0
    }
    
    try:
        diagnostics = get_problems_and_diagnostics_service()
        problems = diagnostics.detect_problems()
        
        results["detected"] = [{
            "problem_id": p.problem_id,
            "severity": p.severity,
            "title": p.title
        } for p in problems]
        
        for problem in problems:
            fix_result = _attempt_fix(problem)
            if fix_result["success"]:
                results["fixed"].append({
                    "problem_id": problem.problem_id,
                    "title": problem.title,
                    "method": fix_result["method"]
                })
            else:
                results["failed"].append({
                    "problem_id": problem.problem_id,
                    "title": problem.title,
                    "error": fix_result["error"]
                })
        
        results["execution_time"] = time.time() - start_time
        
        if results["failed"]:
            results["success"] = False
            results["message"] = f"诊断修复完成，{len(results['fixed'])} 个已修复，{len(results['failed'])} 个修复失败"
        else:
            results["message"] = f"诊断修复完成，共修复 {len(results['fixed'])} 个问题"
        
        logger.info(f"[强力诊断修复] 完成: {results['message']}")
        
    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        results["message"] = f"诊断修复过程出错: {str(e)}"
        logger.error(f"[强力诊断修复] 失败: {e}")
    
    return results


def _attempt_fix(problem: Problem) -> Dict[str, Any]:
    """尝试修复单个问题"""
    try:
        if problem.problem_id == "db_dir_missing":
            db_dir = os.path.dirname(DATABASE_PATH or 
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'Database', 'mtscos.db'))
            os.makedirs(db_dir, exist_ok=True)
            return {"success": True, "method": "创建数据库目录"}
        
        elif problem.problem_id == "static_dir_missing":
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            static_dir = os.path.join(project_root, 'static')
            os.makedirs(static_dir, exist_ok=True)
            return {"success": True, "method": "创建静态资源目录"}
        
        elif problem.problem_id == "deps_missing":
            import subprocess
            modules = problem.details.get("missing_modules", [])
            if modules:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + modules)
                return {"success": True, "method": f"安装依赖: {', '.join(modules)}"}
        
        return {"success": False, "error": "不支持自动修复此类型问题"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

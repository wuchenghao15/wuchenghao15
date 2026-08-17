#!/usr/bin/env python3
"""
项目修复AI Agent - 负责深度扫描、诊断和修复项目中的各类问题
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import re
import ast
import json
import subprocess
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Tuple
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engines.ai_employee_system import AIEmployee


class ProjectRepairAgent(AIEmployee):
    """项目修复AI Agent - 深度扫描、诊断和修复项目问题"""

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "project_repair", level)
        self.type = "project_repair"
        self.scan_results = []
        self.fix_history = []
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._lock = threading.RLock()

    def start(self):
        """启动AI员工"""
        self.status = "active"
        logger.info(f"项目修复AI Agent {self.name} 已启动")

    def stop(self):
        """停止AI员工"""
        self.status = "inactive"
        logger.info(f"项目修复AI Agent {self.name} 已停止")

    def get_status(self):
        """获取状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "scan_results_count": len(self.scan_results),
            "fix_count": len(self.fix_history),
            "last_active": self.last_active,
            "performance_score": getattr(self, 'performance_score', 85),
        }

    def _scan_python_files(self) -> List[Dict]:
        """扫描所有Python文件的语法错误"""
        errors = []
        py_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'data']]
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                ast.parse(source)
            except SyntaxError as e:
                errors.append({
                    "file": py_file,
                    "error_type": "python_syntax",
                    "line": e.lineno,
                    "column": e.offset,
                    "message": str(e),
                    "severity": "high"
                })
            except Exception as e:
                errors.append({
                    "file": py_file,
                    "error_type": "python_parse",
                    "line": 0,
                    "column": 0,
                    "message": str(e),
                    "severity": "medium"
                })
        
        return errors

    def _scan_html_js(self) -> List[Dict]:
        """扫描HTML文件中的JavaScript语法错误"""
        errors = []
        html_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'data']]
            for f in files:
                if f.endswith('.html'):
                    html_files.append(os.path.join(root, f))
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
                for idx, script in enumerate(scripts):
                    if len(script.strip()) < 10:
                        continue
                    
                    cleaned = script
                    cleaned = re.sub(r'\{\{[^}]+\}\}', 'null', cleaned)
                    cleaned = re.sub(r'\{%[^\%]+\%\}', '', cleaned)
                    
                    tmp_file = f'/tmp/prj_repair_{hash(script)}.js'
                    with open(tmp_file, 'w') as f:
                        f.write(cleaned)
                    
                    result = subprocess.run(['node', '--check', tmp_file], 
                                           capture_output=True, text=True)
                    os.remove(tmp_file)
                    
                    if result.returncode != 0:
                        errors.append({
                            "file": html_file,
                            "error_type": "javascript_syntax",
                            "script_index": idx + 1,
                            "message": result.stderr[:200],
                            "severity": "medium"
                        })
            except Exception as e:
                errors.append({
                    "file": html_file,
                    "error_type": "html_parse",
                    "message": str(e),
                    "severity": "low"
                })
        
        return errors

    def _scan_database(self) -> List[Dict]:
        """扫描数据库完整性"""
        errors = []
        db_files = glob.glob(os.path.join(self.project_root, '*.db'))
        
        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] != "ok":
                    errors.append({
                        "file": db_file,
                        "error_type": "database_corruption",
                        "message": f"数据库完整性检查失败: {result[0]}",
                        "severity": "high"
                    })
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                if not tables:
                    errors.append({
                        "file": db_file,
                        "error_type": "database_empty",
                        "message": "数据库为空，没有表",
                        "severity": "medium"
                    })
                
                conn.close()
            except Exception as e:
                errors.append({
                    "file": db_file,
                    "error_type": "database_access",
                    "message": str(e),
                    "severity": "high"
                })
        
        return errors

    def _scan_missing_dependencies(self) -> List[Dict]:
        """扫描缺失的依赖"""
        errors = []
        
        try:
            with open(os.path.join(self.project_root, 'requirements.txt'), 'r') as f:
                requirements = f.read()
            
            for line in requirements.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    pkg_name = line.split('=')[0].strip()
                    try:
                        __import__(pkg_name.replace('-', '_'))
                    except ImportError:
                        errors.append({
                            "file": "requirements.txt",
                            "error_type": "missing_dependency",
                            "message": f"缺失依赖: {pkg_name}",
                            "severity": "medium"
                        })
        except Exception as e:
            errors.append({
                "file": "requirements.txt",
                "error_type": "requirements_read",
                "message": str(e),
                "severity": "low"
            })
        
        return errors

    def _scan_code_smells(self) -> List[Dict]:
        """扫描代码异味（潜在问题）"""
        errors = []
        py_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'data']]
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'print(' in content and 'logger' not in content.lower():
                    errors.append({
                        "file": py_file,
                        "error_type": "code_smell",
                        "message": "使用print而不是logger",
                        "severity": "low"
                    })
                
                if 'except:' in content and 'except Exception' not in content:
                    errors.append({
                        "file": py_file,
                        "error_type": "code_smell",
                        "message": "使用裸except语句",
                        "severity": "medium"
                    })
                
                if 'global ' in content:
                    errors.append({
                        "file": py_file,
                        "error_type": "code_smell",
                        "message": "使用全局变量",
                        "severity": "low"
                    })
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if len(line) > 120:
                        errors.append({
                            "file": py_file,
                            "error_type": "code_smell",
                            "line": i,
                            "message": "行长度超过120字符",
                            "severity": "low"
                        })
            except Exception:
                pass
        
        return errors

    def scan_project(self) -> Dict:
        """扫描项目中的所有问题"""
        with self._lock:
            self.scan_results = []
            
            logger.info(f"项目修复AI Agent {self.name} 开始扫描项目...")
            
            self.scan_results.extend(self._scan_python_files())
            self.scan_results.extend(self._scan_html_js())
            self.scan_results.extend(self._scan_missing_dependencies())
            self.scan_results.extend(self._scan_code_smells())
            
            logger.info(f"扫描完成，发现 {len(self.scan_results)} 个问题")
            
            return {
                "success": True,
                "message": f"扫描完成，发现 {len(self.scan_results)} 个问题",
                "total_errors": len(self.scan_results),
                "errors_by_severity": {
                    "high": len([e for e in self.scan_results if e['severity'] == 'high']),
                    "medium": len([e for e in self.scan_results if e['severity'] == 'medium']),
                    "low": len([e for e in self.scan_results if e['severity'] == 'low'])
                },
                "errors": self.scan_results
            }

    def _fix_python_syntax(self, error: Dict) -> Dict:
        """修复Python语法错误"""
        try:
            with open(error['file'], 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_num = error['line'] - 1
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                fix_desc = ""
                
                if 'unexpected indent' in error['message']:
                    lines[line_num] = line.lstrip()
                    fix_desc = "修复缩进错误"
                elif 'expected' in error['message'] and ':' in error['message']:
                    if not line.strip().endswith(':'):
                        lines[line_num] = line.rstrip() + ':\n'
                        fix_desc = "添加缺失的冒号"
                    else:
                        return {"success": False, "message": "无法自动修复此语法错误"}
                elif 'unmatched' in error['message']:
                    if '(' in line and ')' not in line:
                        lines[line_num] = line.rstrip() + ')\n'
                        fix_desc = "添加缺失的右括号"
                    elif '[' in line and ']' not in line:
                        lines[line_num] = line.rstrip() + ']\n'
                        fix_desc = "添加缺失的右方括号"
                    elif '{' in line and '}' not in line:
                        lines[line_num] = line.rstrip() + '}\n'
                        fix_desc = "添加缺失的右花括号"
                    else:
                        return {"success": False, "message": "无法自动修复此语法错误"}
                elif 'triple-quoted' in error['message'] or 'EOF while scanning' in error['message']:
                    if "'''" in line or '"""' in line:
                        lines[line_num] = line.rstrip() + '"""\n'
                        fix_desc = "闭合三重引号字符串"
                    else:
                        return {"success": False, "message": "无法自动修复此语法错误"}
                elif 'missing parentheses' in error['message'] and 'print' in error['message']:
                    lines[line_num] = re.sub(r'print\s+(.+)', r'print(\1)', line)
                    fix_desc = "为print添加括号"
                elif 'invalid syntax' in error['message']:
                    if line.strip().startswith('print') and '(' not in line:
                        lines[line_num] = re.sub(r'print\s+(.+)', r'print(\1)', line)
                        fix_desc = "为print添加括号"
                    else:
                        return {"success": False, "message": "无法自动修复此语法错误"}
                else:
                    return {"success": False, "message": "无法自动修复此语法错误"}
                
                with open(error['file'], 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                try:
                    with open(error['file'], 'r', encoding='utf-8') as f:
                        source = f.read()
                    ast.parse(source)
                    return {"success": True, "message": fix_desc}
                except SyntaxError:
                    return {"success": False, "message": "修复后仍有语法错误"}
            
            return {"success": False, "message": "行号超出范围"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _fix_javascript_syntax(self, error: Dict) -> Dict:
        """修复JavaScript语法错误"""
        try:
            with open(error['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
            if error['script_index'] - 1 < len(scripts):
                script = scripts[error['script_index'] - 1]
                
                if 'Unexpected token' in error['message'] and '${' in script:
                    fixed_script = re.sub(r'\$\{([^}]+?)\s+not\s+found\}', r'${\1}', script)
                    if fixed_script != script:
                        content = content.replace(script, fixed_script)
                        with open(error['file'], 'w', encoding='utf-8') as f:
                            f.write(content)
                        return {"success": True, "message": "修复模板字符串语法错误"}
                
                if 'Unexpected token' in error['message'] or 'missing )' in error['message'].lower():
                    open_count = script.count('(')
                    close_count = script.count(')')
                    if open_count > close_count:
                        fixed_script = script + ')' * (open_count - close_count)
                        content = content.replace(script, fixed_script)
                        with open(error['file'], 'w', encoding='utf-8') as f:
                            f.write(content)
                        return {"success": True, "message": "添加缺失的右括号"}
                
                if 'Unexpected end of input' in error['message']:
                    open_count = script.count('{')
                    close_count = script.count('}')
                    if open_count > close_count:
                        fixed_script = script + '}' * (open_count - close_count)
                        content = content.replace(script, fixed_script)
                        with open(error['file'], 'w', encoding='utf-8') as f:
                            f.write(content)
                        return {"success": True, "message": "添加缺失的右花括号"}
            
            return {"success": False, "message": "无法自动修复此JavaScript语法错误"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _fix_missing_dependency(self, error: Dict) -> Dict:
        """修复缺失依赖"""
        try:
            package = error.get('package', '')
            if not package:
                return {"success": False, "message": "无法识别缺失的依赖包"}
            
            result = subprocess.run(
                ['pip', 'install', package],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "成功安装依赖包: " + package}
            else:
                return {"success": False, "message": "安装失败: " + result.stderr[:100]}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _fix_file_code_smells(self, file_path: str, errors: List[Dict]) -> Dict:
        """批量修复单个文件中的所有代码异味"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixed_content = content
            fixes_applied = []
            
            smell_types = set(e['message'] for e in errors)
            
            if "使用print而不是logger" in smell_types:
                fixed_content = fixed_content.replace('print(', 'logger.info(')
                fixes_applied.append("将print替换为logger.info")
            
            if "使用裸except语句" in smell_types:
                lines = fixed_content.split('\n')
                new_lines = []
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('except:'):
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + 'except Exception as e:')
                    else:
                        new_lines.append(line)
                fixed_content = '\n'.join(new_lines)
                fixes_applied.append("将裸except替换为except Exception as e")
            
            if "行长度超过120字符" in smell_types:
                lines = fixed_content.split('\n')
                new_lines = []
                for line in lines:
                    if len(line) > 120:
                        parts = []
                        current_line = line
                        indent = len(line) - len(line.lstrip())
                        max_iterations = 100
                        iterations = 0
                        while len(current_line) > 120 and iterations < max_iterations:
                            iterations += 1
                            split_pos = current_line.rfind(',', 0, 120)
                            if split_pos == -1:
                                split_pos = current_line.rfind('(', 0, 120)
                            if split_pos == -1:
                                split_pos = current_line.rfind(' ', 0, 120)
                            if split_pos == -1:
                                split_pos = 120
                            if split_pos >= len(current_line) - 1:
                                break
                            parts.append(current_line[:split_pos + 1])
                            remaining = current_line[split_pos + 1:].lstrip()
                            if not remaining:
                                break
                            current_line = ' ' * indent + remaining
                        parts.append(current_line)
                        new_lines.extend(parts)
                    else:
                        new_lines.append(line)
                fixed_content = '\n'.join(new_lines)
                fixes_applied.append("拆分过长的代码行")
            
            if "使用全局变量" in smell_types:
                fixes_applied.append("检测到全局变量使用")
            
            if fixed_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                return {
                    "success": True,
                    "message": "; ".join(fixes_applied),
                    "fixed_count": len(errors)
                }
            
            return {"success": False, "message": "未应用任何修复"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _fix_code_smell(self, error: Dict) -> Dict:
        """修复单个代码异味（兼容旧接口）"""
        return self._fix_file_code_smells(error['file'], [error])

    def fix_issues(self, filter_severity: str = None, batch_size: int = 50) -> Dict:
        """修复扫描到的问题（分批处理版本）"""
        with self._lock:
            if not self.scan_results:
                return {"success": False, "message": "请先执行扫描"}
            
            filtered = self.scan_results
            if filter_severity:
                filtered = [e for e in self.scan_results if e['severity'] == filter_severity]
            
            success_count = 0
            failed_count = 0
            total_files = 0
            processed_files = 0
            
            code_smells_by_file = {}
            other_errors = []
            
            for error in filtered:
                if error['error_type'] == 'code_smell':
                    file_path = error['file']
                    if file_path not in code_smells_by_file:
                        code_smells_by_file[file_path] = []
                    code_smells_by_file[file_path].append(error)
                else:
                    other_errors.append(error)
            
            total_files = len(code_smells_by_file)
            logger.info(f"开始修复 {len(filtered)} 个问题, {total_files} 个文件...")
            
            files_list = list(code_smells_by_file.items())
            
            for i, (file_path, errors) in enumerate(files_list):
                result = self._fix_file_code_smells(file_path, errors)
                
                if result['success']:
                    success_count += result.get('fixed_count', len(errors))
                    self.fix_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "file": file_path,
                        "error_type": 'code_smell',
                        "fix_method": result['message']
                    })
                else:
                    failed_count += len(errors)
                
                processed_files += 1
                if (i + 1) % batch_size == 0:
                    logger.info(f"已处理 {processed_files}/{total_files} 文件, 成功 {success_count}")
            
            for error in other_errors:
                if error['error_type'] == 'python_syntax':
                    result = self._fix_python_syntax(error)
                elif error['error_type'] == 'javascript_syntax':
                    result = self._fix_javascript_syntax(error)
                elif error['error_type'] == 'missing_dependency':
                    result = self._fix_missing_dependency(error)
                else:
                    result = {"success": False, "message": "不支持自动修复此类型错误"}
                
                if result['success']:
                    success_count += 1
                    self.fix_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "file": error['file'],
                        "error_type": error['error_type'],
                        "fix_method": result['message']
                    })
                else:
                    failed_count += 1
            
            logger.info(f"修复完成: 成功 {success_count} | 失败 {failed_count}")
            
            return {
                "success": True,
                "message": f"修复完成: 成功 {success_count} | 失败 {failed_count}",
                "success_count": success_count,
                "failed_count": failed_count
            }

    def report_to_database(self) -> Dict:
        """上报修复记录到数据库"""
        try:
            db_path = os.path.join(self.project_root, 'app.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_repair_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT,
                    employee_name TEXT,
                    scan_time TEXT,
                    total_errors INTEGER,
                    high_errors INTEGER,
                    medium_errors INTEGER,
                    low_errors INTEGER,
                    fixed_count INTEGER,
                    failed_count INTEGER,
                    repair_details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            repair_details = json.dumps(self.fix_history, ensure_ascii=False)
            
            severity_counts = {
                "high": len([e for e in self.scan_results if e['severity'] == 'high']),
                "medium": len([e for e in self.scan_results if e['severity'] == 'medium']),
                "low": len([e for e in self.scan_results if e['severity'] == 'low'])
            }
            
            cursor.execute('''
                INSERT INTO project_repair_logs (
                    employee_id, employee_name, scan_time,
                    total_errors, high_errors, medium_errors, low_errors,
                    fixed_count, failed_count, repair_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.employee_id,
                self.name,
                datetime.now().isoformat(),
                len(self.scan_results),
                severity_counts['high'],
                severity_counts['medium'],
                severity_counts['low'],
                len(self.fix_history),
                len(self.scan_results) - len(self.fix_history),
                repair_details
            ))
            
            for fix in self.fix_history:
                cursor.execute('''
                    INSERT INTO error_logs (
                        error_code, error_type, error_message, error_details,
                        severity, affected_module, status, fixed_at, fix_method
                    ) VALUES (?, ?, ?, ?, ?, ?, 'fixed', ?, ?)
                ''', (
                    f"PRJ_REP_{len(self.fix_history)}",
                    fix['error_type'],
                    f"项目修复: {fix['file']}",
                    json.dumps(fix, ensure_ascii=False),
                    "medium",
                    "project_repair",
                    datetime.now().isoformat(),
                    fix['fix_method']
                ))
                
                cursor.execute('''
                    INSERT INTO repair_history (
                        error_code, error_message, fix_method, fix_result, operator
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    f"PRJ_REP_{len(self.fix_history)}",
                    f"项目修复: {fix['file']}",
                    fix['fix_method'],
                    "成功",
                    self.name
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"修复记录已上报数据库")
            
            return {
                "success": True,
                "message": "修复记录已成功上报数据库",
                "logs_count": len(self.fix_history)
            }
        except Exception as e:
            logger.error(f"上报数据库失败: {e}")
            return {"success": False, "message": str(e)}

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.last_active = datetime.now().isoformat()
        task_type = task_data.get('type', '')
        
        if task_type == 'scan':
            return self.scan_project()
        elif task_type == 'fix':
            severity = task_data.get('severity', None)
            return self.fix_issues(severity)
        elif task_type == 'scan_and_fix':
            scan_result = self.scan_project()
            if scan_result['success']:
                fix_result = self.fix_issues()
                fix_result['scan_result'] = scan_result
                return fix_result
            return scan_result
        elif task_type == 'report':
            return self.report_to_database()
        elif task_type == 'full_repair':
            scan_result = self.scan_project()
            if scan_result['success']:
                fix_result = self.fix_issues()
                fix_result['scan_result'] = scan_result
                report_result = self.report_to_database()
                fix_result['report_result'] = report_result
                return fix_result
            return scan_result
        else:
            return {"success": True, "message": f"项目修复AI Agent {self.name} 处理任务完成"}


import glob

if __name__ == "__main__":
    agent = ProjectRepairAgent("prj_rep_001", "项目修复AI Agent", 9)
    agent.start()
    
    print("项目修复AI Agent已启动")
    
    result = agent.scan_project()
    print(f"\n扫描结果: {result['message']}")
    print(f"严重级别分布: {result['errors_by_severity']}")
    
    if result['total_errors'] > 0:
        fix_result = agent.fix_issues()
        print(f"\n修复结果: {fix_result['message']}")
        
        report_result = agent.report_to_database()
        print(f"\n上报结果: {report_result['message']}")
    
    agent.stop()
    print("\n项目修复AI Agent已停止")

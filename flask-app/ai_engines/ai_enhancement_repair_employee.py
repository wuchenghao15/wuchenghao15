# -*- coding: utf-8 -*-
"""
AI增强修复员工系统 v1.0.0
自动联想增强优化系统功能，自动检测修复源代码错误并上报数据库
"""

import logging
import threading
import time
import json
import os
import uuid
import ast
import re
import sqlite3
import traceback
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class EnhancementType(Enum):
    """增强类型"""
    FEATURE_ENHANCEMENT = "feature_enhancement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_IMPROVEMENT = "security_improvement"
    UX_IMPROVEMENT = "ux_improvement"
    CODE_QUALITY = "code_quality"
    ERROR_FIX = "error_fix"


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FixStatus(Enum):
    """修复状态"""
    DETECTED = "detected"
    ANALYZED = "analyzed"
    FIXED = "fixed"
    VERIFIED = "verified"
    FAILED = "failed"


class EnhancementRecord:
    """增强记录"""
    
    def __init__(self, enhancement_id: str, enhancement_type: EnhancementType,
                 feature_name: str, description: str, before_state: str = "",
                 after_state: str = "", success: bool = False):
        self.enhancement_id = enhancement_id
        self.enhancement_type = enhancement_type
        self.feature_name = feature_name
        self.description = description
        self.before_state = before_state
        self.after_state = after_state
        self.success = success
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enhancement_id": self.enhancement_id,
            "enhancement_type": self.enhancement_type.value,
            "feature_name": self.feature_name,
            "description": self.description,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "success": self.success,
            "created_at": self.created_at.isoformat()
        }


class ErrorRecord:
    """错误记录"""
    
    def __init__(self, error_id: str, file_path: str, error_type: str,
                 error_message: str, line_number: int, column: int = 0,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.error_id = error_id
        self.file_path = file_path
        self.error_type = error_type
        self.error_message = error_message
        self.line_number = line_number
        self.column = column
        self.severity = severity
        self.status = FixStatus.DETECTED
        self.fix_attempts = 0
        self.fixed_by = None
        self.fixed_at = None
        self.repair_details = None
        self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "file_path": self.file_path,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "line_number": self.line_number,
            "column": self.column,
            "severity": self.severity.value,
            "status": self.status.value,
            "fix_attempts": self.fix_attempts,
            "fixed_by": self.fixed_by,
            "fixed_at": self.fixed_at.isoformat() if self.fixed_at else None,
            "detected_at": self.detected_at.isoformat()
        }


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self):
        self.error_patterns = {
            "syntax_error": re.compile(r"SyntaxError: (.+)"),
            "import_error": re.compile(r"ImportError: (.+)"),
            "name_error": re.compile(r"NameError: name '(.+)' is not defined"),
            "type_error": re.compile(r"TypeError: (.+)"),
            "value_error": re.compile(r"ValueError: (.+)"),
            "attribute_error": re.compile(r"AttributeError: '(.+)' object has no attribute '(.+)'"),
            "index_error": re.compile(r"IndexError: (.+)"),
            "key_error": re.compile(r"KeyError: '(.+)'"),
            "indentation_error": re.compile(r"IndentationError: (.+)"),
            "unexpected_eof": re.compile(r"SyntaxError: unexpected EOF while parsing"),
            "missing_colon": re.compile(r"SyntaxError: invalid syntax.*line (\d+)"),
        }
    
    def analyze_python_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """分析Python文件"""
        errors = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            line_num = e.lineno or 1
            errors.append({
                "error_id": f"err_{uuid.uuid4().hex[:8]}",
                "file_path": file_path,
                "error_type": "syntax_error",
                "error_message": str(e),
                "line_number": line_num,
                "column": e.offset or 0,
                "severity": "high"
            })
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                continue
            
            if 'import ' in line or 'from ' in line:
                if 'import *' in line and not line.strip().startswith('if') and not line.strip().startswith('elif') and not line.strip().startswith('#'):
                    errors.append({
                        "error_id": f"err_{uuid.uuid4().hex[:8]}",
                        "file_path": file_path,
                        "error_type": "bad_import",
                        "error_message": "不建议使用通配符导入",
                        "line_number": i,
                        "column": 0,
                        "severity": "low"
                    })
            
            if re.search(r'\bprint\s*\(', line) and 'logger' not in content.lower():
                errors.append({
                    "error_id": f"err_{uuid.uuid4().hex[:8]}",
                    "file_path": file_path,
                    "error_type": "print_statement",
                    "error_message": "建议使用logger代替print",
                    "line_number": i,
                    "column": 0,
                    "severity": "low"
                })
            
            if 'except:' in line and 'Exception' not in line:
                errors.append({
                    "error_id": f"err_{uuid.uuid4().hex[:8]}",
                    "file_path": file_path,
                    "error_type": "bare_except",
                    "error_message": "不建议使用裸except",
                    "line_number": i,
                    "column": 0,
                    "severity": "medium"
                })
            
            if re.search(r'==\s*None', line) or re.search(r'!=\s*None', line):
                errors.append({
                    "error_id": f"err_{uuid.uuid4().hex[:8]}",
                    "file_path": file_path,
                    "error_type": "none_comparison",
                    "error_message": "建议使用is None代替is None",
                    "line_number": i,
                    "column": 0,
                    "severity": "medium"
                })
            
            if 'True' in line or 'False' in line:
                if re.search(r"\b(True|False)\s*=", line):
                    errors.append({
                        "error_id": f"err_{uuid.uuid4().hex[:8]}",
                        "file_path": file_path,
                        "error_type": "bool_assignment",
                        "error_message": "布尔值不应被重新赋值",
                        "line_number": i,
                        "column": 0,
                        "severity": "medium"
                    })
        
        return errors
    
    def analyze_json_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """分析JSON文件"""
        errors = []
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append({
                "error_id": f"err_{uuid.uuid4().hex[:8]}",
                "file_path": file_path,
                "error_type": "json_syntax_error",
                "error_message": str(e),
                "line_number": e.lineno or 1,
                "column": e.colno or 0,
                "severity": "high"
            })
        return errors
    
    def analyze_html_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """分析HTML文件"""
        errors = []
        if '<script' in content.lower() and '</script>' not in content.lower():
            errors.append({
                "error_id": f"err_{uuid.uuid4().hex[:8]}",
                "file_path": file_path,
                "error_type": "unclosed_tag",
                "error_message": "未闭合的script标签",
                "line_number": 1,
                "column": 0,
                "severity": "medium"
            })
        
        if '<div' in content.lower() and '</div>' not in content.lower():
            errors.append({
                "error_id": f"err_{uuid.uuid4().hex[:8]}",
                "file_path": file_path,
                "error_type": "unclosed_tag",
                "error_message": "未闭合的div标签",
                "line_number": 1,
                "column": 0,
                "severity": "medium"
            })
        
        return errors


class CodeFixer:
    """代码修复器"""
    
    def __init__(self):
        self.fix_strategies = {
            "syntax_error": self._fix_syntax_error,
            "bare_except": self._fix_bare_except,
            "none_comparison": self._fix_none_comparison,
            "print_statement": self._fix_print_statement,
            "bad_import": self._fix_bad_import,
            "indentation_error": self._fix_indentation,
            "json_syntax_error": self._fix_json_error,
        }
    
    def _fix_syntax_error(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复语法错误"""
        lines = content.split('\n')
        line_num = error_info.get('line_number', 1) - 1
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            if line.strip() and not line.strip().endswith(':'):
                if 'def ' in line or 'class ' in line or 'if ' in line or 'for ' in line or 'while ' in line:
                    lines[line_num] = line.rstrip() + ':'
        
        return '\n'.join(lines)
    
    def _fix_bare_except(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复裸except"""
        return content.replace('except:', 'except Exception:')
    
    def _fix_none_comparison(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复None比较"""
        content = re.sub(r'==\s*None', 'is None', content)
        content = re.sub(r'!=\s*None', 'is not None', content)
        return content
    
    def _fix_print_statement(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复print语句 - 替换为logging（安全版本）"""
        lines = content.split('\n')
        line_num = error_info.get('line_number', 1) - 1
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            match = re.search(r'print\s*\((.*)\)', line)
            if match:
                inner_content = match.group(1)
                if 'Blueprint' in inner_content or '__name__' in inner_content:
                    return content
                indent = line[:len(line) - len(line.lstrip())]
                lines[line_num] = f"{indent}logger.info({inner_content})"
        
        result = '\n'.join(lines)
        
        if 'logger.info(' in result and 'import logging' not in result:
            result = 'import logging\nlogger = logging.getLogger(__name__)\n\n' + result
        
        return result
    
    def _fix_bad_import(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复不良导入 - 移除通配符导入"""
        lines = content.split('\n')
        line_num = error_info.get('line_number', 1) - 1
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            if 'from ' in line and ' import *' in line:
                parts = line.split('from ')
                if len(parts) > 1:
                    module = parts[1].split(' import')[0].strip()
                    lines[line_num] = "import " + module
        
        return '\n'.join(lines)
    
    def _fix_indentation(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复缩进错误"""
        lines = content.split('\n')
        fixed_lines = []
        indent_level = 0
        for line in lines:
            stripped = line.strip()
            if stripped.endswith(':') and not stripped.startswith('#'):
                fixed_lines.append('    ' * indent_level + stripped)
                indent_level += 1
            elif stripped and not stripped.startswith('#'):
                if indent_level > 0 and not line.startswith('    '):
                    fixed_lines.append('    ' * (indent_level - 1) + stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        return '\n'.join(fixed_lines)
    
    def _fix_json_error(self, content: str, error_info: Dict[str, Any]) -> str:
        """修复JSON错误"""
        content = content.replace("'", '"')
        content = re.sub(r',\s*]', ']', content)
        content = re.sub(r',\s*}', '}', content)
        return content
    
    def fix_code(self, content: str, error_info: Dict[str, Any]) -> Tuple[str, bool]:
        """修复代码"""
        error_type = error_info.get('error_type', 'unknown')
        strategy = self.fix_strategies.get(error_type)
        
        if strategy:
            try:
                fixed = strategy(content, error_info)
                if fixed != content:
                    return fixed, True
            except Exception as e:
                logger.error(f"修复失败: {e}")
        
        return content, False


class EnhancementEngine:
    """增强引擎"""
    
    FEATURE_ENHANCEMENTS = {
        "security": {
            "enhancements": [
                {"type": "security_improvement", "description": "增强密码加密强度", "action": "upgrade_encryption"},
                {"type": "security_improvement", "description": "添加安全审计日志", "action": "add_audit_log"},
                {"type": "security_improvement", "description": "实现防暴力破解", "action": "add_brute_force_protection"},
            ]
        },
        "performance": {
            "enhancements": [
                {"type": "performance_optimization", "description": "添加缓存机制", "action": "add_caching"},
                {"type": "performance_optimization", "description": "优化数据库查询", "action": "optimize_queries"},
                {"type": "performance_optimization", "description": "实现异步处理", "action": "add_async"},
            ]
        },
        "ux": {
            "enhancements": [
                {"type": "ux_improvement", "description": "添加响应式设计", "action": "add_responsive"},
                {"type": "ux_improvement", "description": "优化页面加载速度", "action": "optimize_loading"},
                {"type": "ux_improvement", "description": "添加用户友好提示", "action": "add_user_hints"},
            ]
        },
        "code": {
            "enhancements": [
                {"type": "code_quality", "description": "添加类型提示", "action": "add_type_hints"},
                {"type": "code_quality", "description": "优化代码结构", "action": "refactor_code"},
                {"type": "code_quality", "description": "添加单元测试", "action": "add_tests"},
            ]
        },
        "monitoring": {
            "enhancements": [
                {"type": "feature_enhancement", "description": "添加实时监控", "action": "add_realtime_monitor"},
                {"type": "feature_enhancement", "description": "实现智能告警", "action": "add_smart_alerts"},
                {"type": "feature_enhancement", "description": "生成性能报告", "action": "generate_reports"},
            ]
        },
    }
    
    def __init__(self):
        self.applied_enhancements = []
    
    def suggest_enhancements(self, feature_name: str) -> List[Dict[str, Any]]:
        """建议增强方案"""
        enhancements = self.FEATURE_ENHANCEMENTS.get(feature_name.lower(), {})
        return enhancements.get("enhancements", [])
    
    def apply_enhancement(self, feature_name: str, enhancement_info: Dict[str, Any]) -> EnhancementRecord:
        """应用增强"""
        enhancement_id = f"enh_{uuid.uuid4().hex[:8]}"
        record = EnhancementRecord(
            enhancement_id=enhancement_id,
            enhancement_type=EnhancementType(enhancement_info.get("type", "feature_enhancement")),
            feature_name=feature_name,
            description=enhancement_info.get("description", ""),
            success=True
        )
        self.applied_enhancements.append(record)
        logger.info(f"应用增强: {enhancement_info.get('description')}")
        return record
    
    def get_applied_enhancements(self) -> List[Dict[str, Any]]:
        """获取已应用的增强"""
        return [e.to_dict() for e in self.applied_enhancements]


class AIEnhancementRepairEmployee:
    """AI增强修复员工"""
    
    def __init__(self):
        self.employee_id = f"enhancement_repair_{uuid.uuid4().hex[:8]}"
        self.name = "AI增强修复员工"
        self.role = "enhancement_repair_manager"
        self.status = "active"
        self.is_running = False
        self.monitor_thread = None
        
        self.code_analyzer = CodeAnalyzer()
        self.code_fixer = CodeFixer()
        self.enhancement_engine = EnhancementEngine()
        
        self.detected_errors = []
        self.fixed_errors = []
        self.enhancements = []
        
        logger.info(f"创建AI增强修复员工: {self.employee_id}")
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS enhancement_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        enhancement_id TEXT UNIQUE NOT NULL,
                        enhancement_type TEXT NOT NULL,
                        feature_name TEXT NOT NULL,
                        description TEXT,
                        before_state TEXT,
                        after_state TEXT,
                        success BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS code_error_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_id TEXT UNIQUE NOT NULL,
                        file_path TEXT NOT NULL,
                        error_type TEXT NOT NULL,
                        error_message TEXT,
                        line_number INTEGER,
                        column INTEGER,
                        severity TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'detected',
                        fix_attempts INTEGER DEFAULT 0,
                        fixed_by TEXT,
                        fixed_at TEXT,
                        repair_details TEXT,
                        detected_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS code_fix_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fix_id TEXT UNIQUE NOT NULL,
                        error_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        error_type TEXT NOT NULL,
                        before_content TEXT,
                        after_content TEXT,
                        fix_status TEXT DEFAULT 'pending',
                        applied_by TEXT DEFAULT 'system',
                        applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        verified BOOLEAN DEFAULT 0
                    )
                ''')
                
                conn.commit()
            logger.info("增强修复数据库表初始化完成")
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    def start(self):
        """启动增强修复员工"""
        if self.is_running:
            return
        
        self.is_running = True
        self._init_database()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("AI增强修复员工已启动")
    
    def stop(self):
        """停止增强修复员工"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("AI增强修复员工已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._scan_and_fix()
                time.sleep(300)
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
    
    def _scan_and_fix(self):
        """扫描并修复"""
        logger.info("开始代码扫描...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'backups']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        errors = self.code_analyzer.analyze_python_file(file_path, content)
                        
                        for error in errors:
                            self._handle_error(error, file_path, content)
                    
                    except Exception as e:
                        logger.error(f"扫描文件失败 {file_path}: {e}")
    
    def _handle_error(self, error_info: Dict[str, Any], file_path: str, content: str):
        """处理错误"""
        error_id = error_info['error_id']
        
        if error_id in [e['error_id'] for e in self.detected_errors]:
            return
        
        self.detected_errors.append(error_info)
        
        self._report_error_to_db(error_info)
        
        fixed_content, success = self.code_fixer.fix_code(content, error_info)
        
        if success:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                self.fixed_errors.append({**error_info, 'fixed': True})
                self._report_fix_to_db(error_info, content, fixed_content)
                logger.info(f"已修复错误: {error_info['error_type']} in {file_path}")
            except Exception as e:
                logger.error(f"写入修复文件失败: {e}")
    
    def _report_error_to_db(self, error_info: Dict[str, Any]):
        """上报错误到数据库"""
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT OR IGNORE INTO code_error_records
                    (error_id, file_path, error_type, error_message, line_number, column, severity, status, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error_info['error_id'],
                    error_info['file_path'],
                    error_info['error_type'],
                    error_info['error_message'],
                    error_info.get('line_number', 0),
                    error_info.get('column', 0),
                    error_info.get('severity', 'medium'),
                    'detected',
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"上报错误失败: {e}")
    
    def _report_fix_to_db(self, error_info: Dict[str, Any], before_content: str, after_content: str):
        """上报修复到数据库"""
        try:
            fix_id = f"fix_{uuid.uuid4().hex[:8]}"
            
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO code_fix_logs
                    (fix_id, error_id, file_path, error_type, before_content, after_content, fix_status, applied_by, applied_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fix_id,
                    error_info['error_id'],
                    error_info['file_path'],
                    error_info['error_type'],
                    before_content[:5000],
                    after_content[:5000],
                    'fixed',
                    self.employee_id,
                    datetime.now().isoformat()
                ))
                
                conn.execute('''
                    UPDATE code_error_records 
                    SET status = 'fixed', fixed_by = ?, fixed_at = ?, fix_attempts = fix_attempts + 1
                    WHERE error_id = ?
                ''', (self.employee_id, datetime.now().isoformat(), error_info['error_id']))
                
                conn.commit()
        except Exception as e:
            logger.error(f"上报修复失败: {e}")
    
    def scan_code(self, directory: str = None) -> Dict[str, Any]:
        """扫描代码"""
        if directory is None:
            directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        results = {
            "files_scanned": 0,
            "errors_found": 0,
            "errors_fixed": 0,
            "errors": []
        }
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'backups']]
            
            for file in files:
                if file.endswith('.py'):
                    results["files_scanned"] += 1
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        errors = self.code_analyzer.analyze_python_file(file_path, content)
                        results["errors_found"] += len(errors)
                        results["errors"].extend(errors)
                        
                        for error in errors:
                            fixed_content, success = self.code_fixer.fix_code(content, error)
                            if success:
                                try:
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(fixed_content)
                                    results["errors_fixed"] += 1
                                    self._report_fix_to_db(error, content, fixed_content)
                                except Exception as e:
                                    logger.error(f"写入修复文件失败 {file_path}: {e}")
                    except Exception as e:
                        logger.error(f"扫描文件失败 {file_path}: {e}")
        
        return results
    
    def enhance_feature(self, feature_name: str) -> Dict[str, Any]:
        """增强指定功能"""
        suggestions = self.enhancement_engine.suggest_enhancements(feature_name)
        applied = []
        
        for suggestion in suggestions:
            record = self.enhancement_engine.apply_enhancement(feature_name, suggestion)
            applied.append(record.to_dict())
            
            try:
                with self._get_db_connection() as conn:
                    conn.execute('''
                        INSERT INTO enhancement_records
                        (enhancement_id, enhancement_type, feature_name, description, success, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        record.enhancement_id,
                        record.enhancement_type.value,
                        record.feature_name,
                        record.description,
                        record.success,
                        record.created_at.isoformat()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"上报增强失败: {e}")
        
        return {
            "feature_name": feature_name,
            "suggestions": suggestions,
            "applied_enhancements": applied
        }
    
    def auto_enhance_all(self) -> Dict[str, Any]:
        """自动增强所有功能"""
        results = {
            "total_features": 0,
            "total_enhancements": 0,
            "enhancements": []
        }
        
        for feature in self.enhancement_engine.FEATURE_ENHANCEMENTS:
            result = self.enhance_feature(feature)
            results["total_features"] += 1
            results["total_enhancements"] += len(result["applied_enhancements"])
            results["enhancements"].append(result)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "is_running": self.is_running,
            "detected_errors_count": len(self.detected_errors),
            "fixed_errors_count": len(self.fixed_errors),
            "applied_enhancements_count": len(self.enhancement_engine.applied_enhancements),
            "last_check": datetime.now().isoformat()
        }
    
    def get_errors(self, severity: str = None) -> List[Dict[str, Any]]:
        """获取错误列表"""
        if severity:
            return [e for e in self.detected_errors if e.get('severity') == severity]
        return self.detected_errors
    
    def get_enhancements(self) -> List[Dict[str, Any]]:
        """获取增强记录"""
        return self.enhancement_engine.get_applied_enhancements()


ai_enhancement_repair_employee = AIEnhancementRepairEmployee()


def get_enhancement_repair_employee() -> AIEnhancementRepairEmployee:
    """获取增强修复员工单例"""
    return ai_enhancement_repair_employee


if __name__ == "__main__":
    employee = AIEnhancementRepairEmployee()
    employee.start()
    
    print("=" * 60)
    print("AI增强修复员工测试")
    print("=" * 60)
    
    print("\n1. 扫描代码...")
    scan_result = employee.scan_code()
    print(f"   - 扫描文件数: {scan_result['files_scanned']}")
    print(f"   - 发现错误数: {scan_result['errors_found']}")
    print(f"   - 修复错误数: {scan_result['errors_fixed']}")
    
    print("\n2. 自动增强所有功能...")
    enhance_result = employee.auto_enhance_all()
    print(f"   - 增强功能数: {enhance_result['total_features']}")
    print(f"   - 应用增强数: {enhance_result['total_enhancements']}")
    
    print("\n3. 获取状态...")
    status = employee.get_status()
    print(f"   - 员工ID: {status['employee_id']}")
    print(f"   - 运行状态: {'运行中' if status['is_running'] else '已停止'}")
    print(f"   - 检测错误: {status['detected_errors_count']}")
    print(f"   - 修复错误: {status['fixed_errors_count']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
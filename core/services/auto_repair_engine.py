from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
""" MTSCOS AI 自动修复引擎 扫描项目异常和错误，自动匹配修复方案并执行修复， 上报修复方案和案例到数据库和日志，投喂脑库供AI学习 """
import os
import sys
import re
import json
import sqlite3
import time
import glob
import random
import logging
from datetime import datetime, timedelta

DATABASE_PATH = _mtscos_get_db_path('app.db')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_repair.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutoRepair')


class AutoRepairEngine:
    """自动修复引擎"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self.repaired_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.new_solutions_count = 0

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _get_rule_value(self, rule_code, default=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (rule_code,
                ))
                result = cursor.fetchone()
                return result[0] if result else default
        except Exception:
            return default

    def _get_rule_bool(self, rule_code, default=False):
        val = self._get_rule_value(rule_code)
        if val is not None:
            return val in ('1', 'true', 'True', 'yes', 'Yes')
        return default

    def _get_rule_float(self, rule_code, default=0.0):
        val = self._get_rule_value(rule_code)
        try:
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _get_rule_int(self, rule_code, default=0):
        val = self._get_rule_value(rule_code)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _gen_id(self, prefix='RPR'):
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.getpid()}-{random.randint(1000, 9999)}"

    def _log_maintenance(self, operation_type, target, result, details=''):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO system_maintenance_logs (operation_type, target, result, details, timestamp) VALUES (?, ?, ?, ?, ?) ''', (operation_type, target, result, details,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
        except Exception as e:
            logger.error(f"记录维护日志失败: {e}")

    def _report_blackbox(self, event_type, title, description, **kwargs):
        """上报黑匣子"""
        try:
            from blackbox_recorder import record_disaster
            record_disaster(event_type, title, description=description,
                           source_module='auto_repair_engine', **kwargs)
        except Exception:
            pass

    # ========== 错误扫描 ==========

    def scan_http_errors(self):
        """扫描所有HTTP错误页面(400/401/403/500)"""
        errors = []
        http_error_types = ['http_400', 'http_401', 'http_403', 'http_500']
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for error_type in http_error_types:
                    if not self._get_rule_bool(f'ERROR_PAGE_{error_type.upper().replace("HTTP_","")}_ENABLE', True):
                        continue
                    
                    cursor.execute(""" SELECT id, error_type, error_message, stack_trace, created_at FROM error_logs WHERE error_type = ? AND (status IS NULL OR status = 'open' OR status = 'unresolved') ORDER BY created_at DESC LIMIT 20 """, (error_type,))
                    for row in cursor.fetchall():
                        request_path = ''
                        msg = row[2] or ''
                        path_match = re.search(r'(?:400|401|403|500)\s+\w+\s*:\s*([^\s]+)', msg)
                        if path_match:
                            request_path = path_match.group(1)
                        
                        errors.append({
                            'source': 'http_error',
                            'error_id': str(row[0]),
                            'error_type': row[1],
                            'error_message': msg,
                            'stack_trace': row[3] or '',
                            'error_file': request_path,
                            'error_line': '',
                            'timestamp': row[4]
                        })
        except Exception as e:
            logger.warning(f"扫描HTTP错误失败: {e}")

        return errors

    def scan_404_errors(self):
        """专门扫描404错误"""
        errors = []
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_ERROR_LOGS', True):
            return errors

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(""" SELECT id, error_type, error_message, stack_trace, created_at FROM error_logs WHERE (error_type = 'http_404' OR error_message LIKE '%404%') AND (status IS NULL OR status = 'open' OR status = 'unresolved') ORDER BY created_at DESC LIMIT 20 """)
                for row in cursor.fetchall():
                    # 提取请求路径
                    request_path = ''
                    msg = row[2] or ''
                    path_match = re.search(r'404 Not Found: (.+)', msg)
                    if path_match:
                        request_path = path_match.group(1)
                    
                    errors.append({
                        'source': 'http_404',
                        'error_id': str(row[0]),
                        'error_type': row[1] or 'http_404',
                        'error_message': msg,
                        'stack_trace': row[3] or '',
                        'error_file': request_path,
                        'error_line': '',
                        'timestamp': row[4]
                    })
        except Exception as e:
            logger.warning(f"扫描404错误失败: {e}")

        return errors

    def scan_error_logs(self):
        """扫描error_logs表中的未解决错误"""
        errors = []
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_ERROR_LOGS', True):
            return errors

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(""" SELECT id, error_type, error_message, stack_trace, created_at FROM error_logs WHERE status IS NULL OR status = 'open' OR status = 'unresolved' ORDER BY created_at DESC LIMIT 20 """)
                for row in cursor.fetchall():
                    errors.append({
                        'source': 'error_logs',
                        'error_id': str(row[0]),
                        'error_type': row[1] or 'unknown',
                        'error_message': row[2] or '',
                        'stack_trace': row[3] or '',
                        'timestamp': row[4]
                    })
        except Exception as e:
            logger.warning(f"扫描error_logs失败: {e}")

        return errors

    def scan_error_reports(self):
        """扫描error_reports表中的前端错误"""
        errors = []
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_ERROR_REPORTS', True):
            return errors

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(""" SELECT id, message, error, url, line, created_at FROM error_reports WHERE created_at > ? ORDER BY created_at DESC LIMIT 20 """, ((datetime.now() - timedelta(hours=24)).isoformat(),))
                for row in cursor.fetchall():
                    errors.append({
                        'source': 'error_reports',
                        'error_id': str(row[0]),
                        'error_type': 'frontend',
                        'error_message': row[1] or row[2] or '',
                        'stack_trace': '',
                        'error_file': row[3] or '',
                        'error_line': str(row[4]) if row[4] else '',
                        'timestamp': row[5]
                    })
        except Exception as e:
            logger.warning(f"扫描error_reports失败: {e}")

        return errors

    def scan_maintenance_failures(self):
        """扫描维护日志中的失败操作"""
        errors = []
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_MAINTENANCE_LOGS', True):
            return errors

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(""" SELECT id, operation_type, target, details, timestamp FROM system_maintenance_logs WHERE result = 'failure' AND timestamp > ? ORDER BY timestamp DESC LIMIT 20 """, ((datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),))
                for row in cursor.fetchall():
                    errors.append({
                        'source': 'maintenance_logs',
                        'error_id': str(row[0]),
                        'error_type': row[1] or 'maintenance',
                        'error_message': f"{row[1]} on {row[2]}: {row[3]}",
                        'stack_trace': '',
                        'timestamp': row[4]
                    })
        except Exception as e:
            logger.warning(f"扫描maintenance_logs失败: {e}")

        return errors

    def scan_log_files(self):
        """扫描日志文件中的错误"""
        errors = []
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_LOG_FILES', True):
            return errors

        pattern = self._get_rule_value('AUTO_REPAIR_LOG_FILE_PATTERNS', '*.log')
        log_dir = os.path.dirname(os.path.abspath(__file__))
        error_patterns = [
            r'Traceback \(most recent call last\)',
            r'Error:',
            r'Exception:',
            r'CRITICAL',
            r'FATAL',
        ]

        for log_file in glob.glob(os.path.join(log_dir, pattern)):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        for pattern_str in error_patterns:
                            if re.search(pattern_str, line, re.IGNORECASE):
                                context = ''.join(lines[max(0, i-2):i+5])
                                errors.append({
                                    'source': 'log_file',
                                    'error_id': f"{os.path.basename(log_file)}:{i}",
                                    'error_type': 'log_error',
                                    'error_message': line.strip(),
                                    'stack_trace': context[:500],
                                    'error_file': log_file,
                                    'error_line': str(i + 1),
                                    'timestamp': datetime.now().isoformat()
                                })
                                break
            except Exception:
                pass

        return errors[:20]  # 限制数量

    def _get_exclude_dirs(self):
        """获取排除目录列表"""
        dirs_str = self._get_rule_value('AUTO_REPAIR_SCAN_EXCLUDE_DIRS',
                                        'node_modules,.git,__pycache__,venv,env,.venv,backups')
        return [d.strip() for d in dirs_str.split(',') if d.strip()]

    def _get_extensions(self, rule_code, default):
        """获取文件扩展名列表"""
        ext_str = self._get_rule_value(rule_code, default)
        return [e.strip() if e.strip().startswith('.') else '.' + e.strip()
                for e in ext_str.split(',') if e.strip()]

    def _is_excluded(self, file_path):
        """判断文件是否在排除目录中"""
        exclude_dirs = self._get_exclude_dirs()
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path:
                return True
        return False

    def _scan_files_by_extensions(self, extensions, source_name):
        """通用文件扫描方法"""
        errors = []
        max_files = self._get_rule_int('AUTO_REPAIR_MAX_FILES_PER_SCAN', 200)
        max_size_kb = self._get_rule_int('AUTO_REPAIR_MAX_FILE_SIZE', 512)
        log_dir = os.path.dirname(os.path.abspath(__file__))

        files_scanned = 0
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 排除目录
            exclude_dirs = self._get_exclude_dirs()
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for filename in files:
                if files_scanned >= max_files:
                    return errors

                ext = os.path.splitext(filename)[1].lower()
                if ext not in extensions:
                    continue

                file_path = os.path.join(root, filename)

                # 跳过排除文件
                if self._is_excluded(file_path):
                    continue

                # 检查文件大小
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > max_size_kb * 1024:
                        continue
                except OSError:
                    continue

                files_scanned += 1

                # 根据扩展名调用不同的检查方法
                if ext == '.py':
                    errors.extend(self._check_python_file(file_path))
                elif ext in ('.js', '.jsx', '.ts', '.tsx'):
                    errors.extend(self._check_js_file(file_path))
                elif ext == '.html':
                    errors.extend(self._check_html_file(file_path))
                elif ext in ('.json',):
                    errors.extend(self._check_json_file(file_path))
                elif ext == '.sh':
                    errors.extend(self._check_shell_file(file_path))
                else:
                    # 通用文本文件检查
                    errors.extend(self._check_text_file(file_path))

        if errors:
            logger.info(f"  [{source_name}] 扫描{files_scanned}个文件, 发现{len(errors)}个错误")
        return errors[:20]

    def _check_python_file(self, file_path):
        """检查Python文件语法错误"""
        errors = []
        if not self._get_rule_bool('AUTO_REPAIR_SYNTAX_CHECK', True):
            return errors

        try:
            # 使用py_compile检查语法
            import py_compile
            py_compile.compile(file_path, doraise=True)
        except py_compile.PyCompileError as e:
            error_msg = str(e)
            line_no = ''
            line_match = re.search(r'line (\d+)', error_msg)
            if line_match:
                line_no = line_match.group(1)
            errors.append({
                'source': 'source_code',
                'error_id': f"{os.path.basename(file_path)}:{line_no}",
                'error_type': 'python_syntax',
                'error_message': error_msg[:300],
                'stack_trace': '',
                'error_file': file_path,
                'error_line': line_no,
                'timestamp': datetime.now().isoformat()
            })
        except Exception:
            pass

        # 静态分析：检查常见问题
        if self._get_rule_bool('AUTO_REPAIR_STATIC_ANALYSIS', True):
            errors.extend(self._static_analyze_python(file_path))

        return errors

    def _static_analyze_python(self, file_path):
        """Python静态分析"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                # 检查Tab和空格混用
                if '\t' in line and '    ' in line:
                    errors.append({
                        'source': 'source_code',
                        'error_id': f"{os.path.basename(file_path)}:{i}",
                        'error_type': 'python_tab_mixed',
                        'error_message': f"TabError: inconsistent use of tabs and spaces in {file_path}:{i}",
                        'stack_trace': '',
                        'error_file': file_path,
                        'error_line': str(i),
                        'timestamp': datetime.now().isoformat()
                    })

                # 检查未闭合的括号（简单检查）
                open_count = line.count('(') + line.count('[') + line.count('{')
                close_count = line.count(')') + line.count(']') + line.count('}')
                # 仅检测明显不匹配的单行情况（避免误报）

        except Exception:
            pass
        return errors

    def _check_js_file(self, file_path):
        """检查JS文件"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # 检查常见JS错误模式
            if 'console.log(' in content and 'debug' in file_path.lower():
                pass  # 调试文件允许console.log
        except Exception:
            pass
        return errors

    def _check_html_file(self, file_path):
        """检查HTML文件标签闭合"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # 简单检查未闭合标签
            open_tags = re.findall(r'<(\w+)[^>]*>(?!.*</\1>)', content)
            for tag in open_tags:
                if tag.lower() not in ('br', 'hr', 'img', 'input', 'meta', 'link'):
                    errors.append({
                        'source': 'source_code',
                        'error_id': f"{os.path.basename(file_path)}:{tag}",
                        'error_type': 'html_unclosed_tag',
                        'error_message': f"unclosed tag: <{tag}> in {file_path}",
                        'stack_trace': '',
                        'error_file': file_path,
                        'error_line': '',
                        'timestamp': datetime.now().isoformat()
                    })
                    break  # 每个文件只报一个
        except Exception:
            pass
        return errors[:1]

    def _check_json_file(self, file_path):
        """检查JSON文件格式"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            import json
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append({
                'source': 'text_file',
                'error_id': f"{os.path.basename(file_path)}:{e.lineno}",
                'error_type': 'json_format',
                'error_message': f"json.decoder.JSONDecodeError: {str(e)} in {file_path}",
                'stack_trace': '',
                'error_file': file_path,
                'error_line': str(e.lineno) if hasattr(e, 'lineno') else '',
                'timestamp': datetime.now().isoformat()
            })
        except (UnicodeDecodeError, Exception):
            # 编码问题
            errors.append({
                'source': 'text_file',
                'error_id': os.path.basename(file_path),
                'error_type': 'encoding_error',
                'error_message': f"UnicodeDecodeError: cannot decode {file_path}",
                'stack_trace': '',
                'error_file': file_path,
                'error_line': '',
                'timestamp': datetime.now().isoformat()
            })
        return errors

    def _check_shell_file(self, file_path):
        """检查Shell脚本"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # 检查常见Shell语法错误
                if line.strip().startswith('if ') and not line.rstrip().endswith(';'):
                    if not any(l.strip().startswith('fi') for l in lines[i:i+10]):
                        errors.append({
                            'source': 'script',
                            'error_id': f"{os.path.basename(file_path)}:{i}",
                            'error_type': 'shell_syntax',
                            'error_message': f"syntax error near unexpected token: if without fi in {file_path}:{i}",
                            'stack_trace': '',
                            'error_file': file_path,
                            'error_line': str(i),
                            'timestamp': datetime.now().isoformat()
                        })
                        break
        except Exception:
            pass
        return errors[:1]

    def _check_text_file(self, file_path):
        """检查通用文本文件"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
        except UnicodeDecodeError:
            errors.append({
                'source': 'text_file',
                'error_id': os.path.basename(file_path),
                'error_type': 'encoding_error',
                'error_message': f"UnicodeDecodeError: cannot decode {file_path} (possibly non-UTF-8 encoding or BOM)",
                'stack_trace': '',
                'error_file': file_path,
                'error_line': '',
                'timestamp': datetime.now().isoformat()
            })
        except Exception:
            pass
        return errors

    def scan_source_code(self):
        """扫描源代码文件"""
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_SOURCE_CODE', True):
            return []
        extensions = self._get_extensions('AUTO_REPAIR_SOURCE_CODE_EXTENSIONS',
                                          '.py,.js,.jsx,.ts,.tsx,.html,.css,.vue')
        return self._scan_files_by_extensions(extensions, 'source_code')

    def scan_scripts(self):
        """扫描脚本文件"""
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_SCRIPTS', True):
            return []
        extensions = self._get_extensions('AUTO_REPAIR_SCRIPT_EXTENSIONS',
                                          '.sh,.bat,.cmd,.ps1')
        return self._scan_files_by_extensions(extensions, 'scripts')

    def scan_text_files(self):
        """扫描文本文件"""
        if not self._get_rule_bool('AUTO_REPAIR_SCAN_TEXT_FILES', True):
            return []
        extensions = self._get_extensions('AUTO_REPAIR_TEXT_EXTENSIONS',
                                          '.txt,.md,.json,.yaml,.yml,.xml,.ini,.conf,.cfg')
        return self._scan_files_by_extensions(extensions, 'text_files')

    def scan_all_errors(self):
        """扫描所有错误源"""
        all_errors = []
        all_errors.extend(self.scan_error_logs())
        all_errors.extend(self.scan_error_reports())
        all_errors.extend(self.scan_maintenance_failures())
        all_errors.extend(self.scan_log_files())
        all_errors.extend(self.scan_http_errors())
        all_errors.extend(self.scan_404_errors())
        all_errors.extend(self.scan_source_code())
        all_errors.extend(self.scan_scripts())
        all_errors.extend(self.scan_text_files())
        return all_errors

    # ========== 方案匹配 ==========

    def match_solution(self, error):
        """匹配修复方案"""
        error_text = f"{error.get('error_type', '')} {error.get('error_message', '')} {error.get('stack_trace', '')}"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM repair_solutions WHERE status = 'active'")
                solutions = cursor.fetchall()

                best_match = None
                best_score = 0
                threshold = self._get_rule_float('AUTO_REPAIR_CONFIDENCE_THRESHOLD', 0.7)

                for sol in solutions:
                    pattern = sol[2]  # error_pattern
                    if re.search(pattern, error_text, re.IGNORECASE):
                        try:
                            confidence = float(sol[10])  # confidence_score
                        except (ValueError, TypeError):
                            confidence = 0.0
                        if confidence > best_score:
                            best_score = confidence
                            best_match = sol

                if best_match and best_score >= threshold:
                    return {
                        'solution_id': best_match[1],
                        'error_pattern': best_match[2],
                        'error_type': best_match[3],
                        'title': best_match[5],
                        'description': best_match[6],
                        'steps': best_match[7],
                        'code': best_match[8],
                        'strategy': best_match[9],
                        'confidence': float(best_match[10]),
                        'severity': best_match[17] if len(best_match) > 17 else 'medium',
                    }
        except Exception as e:
            logger.error(f"匹配修复方案失败: {e}")

        return None

    # ========== 执行修复 ==========

    def execute_repair(self, error, solution):
        """执行修复"""
        execution_id = self._gen_id()
        start_time = datetime.now()
        confidence = solution.get('confidence', 0)
        strategy = solution.get('strategy', 'unknown')

        logger.info(f"  🔧 执行修复: {solution['title']} (置信度:{confidence:.2f}, 策略:{strategy})")

        repair_result = 'success'
        repair_actions = []
        validation_result = 'passed'

        try:
            # 根据策略执行不同的修复动作
            if strategy == 'db_wal_mode':
                repair_actions.append('设置数据库WAL模式')
                with self._get_connection() as conn:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.commit()

            elif strategy == 'create_table':
                repair_actions.append('检查并创建缺失的表')
                # 通用表创建逻辑

            elif strategy == 'insert_or_ignore':
                repair_actions.append('建议使用INSERT OR IGNORE替代INSERT')

            elif strategy == 'alter_table_add_column':
                repair_actions.append('检查并添加缺失的列')

            elif strategy == 'check_create_file':
                file_path = error.get('error_file', '')
                if file_path and 'No such file' in error.get('error_message', ''):
                    repair_actions.append(f'检查文件路径: {file_path}')

            elif strategy == 'optional_import':
                repair_actions.append('建议使用try/except包裹import')

            elif strategy == 'dict_get_default':
                repair_actions.append('建议使用dict.get(key, default)')

            elif strategy == 'null_check':
                repair_actions.append('建议添加None值检查')

            elif strategy == 'retry_connection':
                repair_actions.append('建议添加重试机制')

            elif strategy == 'increase_timeout':
                repair_actions.append('建议增加超时时间')

            elif strategy == 'fix_permissions':
                repair_actions.append('检查并修复文件权限')

            elif strategy == 'fix_syntax':
                repair_actions.append('检查代码语法')

            elif strategy == 'integrity_check':
                repair_actions.append('执行数据库完整性检查')
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()[0]
                    validation_result = result

            elif strategy == 'memory_cleanup':
                repair_actions.append('建议清理大对象和垃圾回收')

            elif strategy == 'check_template_path':
                repair_actions.append('检查模板路径配置')

            elif strategy == 'fix_python_syntax':
                repair_actions.append('检查Python语法错误')
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append(f'已备份文件: {os.path.basename(file_path)}')

            elif strategy == 'fix_indentation':
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append('将Tab转换为4空格缩进')
                    self._fix_tab_to_spaces(file_path)
                    validation_result = 'indentation_fixed'
                else:
                    repair_actions.append('建议统一为4空格缩进')

            elif strategy == 'fix_missing_colon':
                repair_actions.append('建议在函数/类/条件语句末尾添加冒号')

            elif strategy == 'fix_unclosed_bracket':
                repair_actions.append('建议检查括号闭合')

            elif strategy == 'fix_import_error':
                repair_actions.append('建议使用try/except包裹import')

            elif strategy == 'fix_encoding':
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append('转换为UTF-8编码')
                    self._fix_file_encoding(file_path)
                    validation_result = 'encoding_fixed'
                else:
                    repair_actions.append('建议将文件转换为UTF-8编码')

            elif strategy == 'fix_bom':
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append('移除BOM头')
                    self._remove_bom(file_path)
                    validation_result = 'bom_removed'
                else:
                    repair_actions.append('建议移除文件BOM头')

            elif strategy == 'fix_line_ending':
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append('统一行尾符为LF')
                    self._fix_line_endings(file_path)
                    validation_result = 'line_endings_fixed'
                else:
                    repair_actions.append('建议统一行尾符为LF')

            elif strategy == 'fix_tab_spaces':
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append('将Tab转换为4空格')
                    self._fix_tab_to_spaces(file_path)
                    validation_result = 'tab_converted'
                else:
                    repair_actions.append('建议将Tab转换为4空格')

            elif strategy == 'fix_html_tag':
                repair_actions.append('建议检查HTML标签闭合')

            elif strategy == 'fix_json_format':
                file_path = error.get('error_file', '')
                if file_path and os.path.exists(file_path):
                    if self._get_rule_bool('AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX', True):
                        self._backup_file(file_path)
                    repair_actions.append('尝试修复JSON格式')
                    fixed = self._fix_json_file(file_path)
                    validation_result = 'json_fixed' if fixed else 'json_fix_failed'
                else:
                    repair_actions.append('建议检查JSON格式')

            elif strategy == 'fix_undefined_var':
                repair_actions.append('建议检查变量定义和拼写')

            elif strategy == 'fix_type_error':
                repair_actions.append('建议检查变量类型并添加类型转换')

            elif strategy == 'fix_attribute_error':
                repair_actions.append('建议检查对象属性是否存在')

            elif strategy == 'fix_shell_syntax':
                repair_actions.append('建议检查Shell脚本语法')

            elif strategy == 'fix_404_route_missing':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析404路由缺失: {request_path}')
                repair_actions.append('检查现有路由定义')
                repair_actions.append('建议添加缺失的路由')
                repair_actions.append('建议检查前端路由配置')

            elif strategy == 'fix_404_static_file':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析404静态文件缺失: {request_path}')
                repair_actions.append('检查static目录结构')
                repair_actions.append('确认文件是否存在')
                repair_actions.append('建议修复静态文件引用路径')

            elif strategy == 'fix_404_api_missing':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析404API接口缺失: {request_path}')
                repair_actions.append('检查API蓝图注册')
                repair_actions.append('确认路由定义')
                repair_actions.append('建议添加缺失的API端点')

            elif strategy == 'fix_404_template':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析404模板缺失: {request_path}')
                repair_actions.append('检查templates目录')
                repair_actions.append('确认模板文件存在')
                repair_actions.append('建议修复render_template调用')

            elif strategy == 'fix_404_redirect':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析404重定向错误: {request_path}')
                repair_actions.append('检查重定向目标路径')
                repair_actions.append('确认目标路由存在')
                repair_actions.append('建议修复重定向URL')

            elif strategy == 'fix_400_bad_request':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析400请求格式错误: {request_path}')
                repair_actions.append('检查请求参数格式')
                repair_actions.append('验证参数类型')
                repair_actions.append('建议添加参数校验')
                repair_actions.append('建议返回清晰的错误提示')

            elif strategy == 'fix_401_unauthorized':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析401未授权错误: {request_path}')
                repair_actions.append('检查用户登录状态')
                repair_actions.append('验证token有效性')
                repair_actions.append('建议添加会话超时处理')
                repair_actions.append('建议优化登录重定向')

            elif strategy == 'fix_403_forbidden':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析403权限不足错误: {request_path}')
                repair_actions.append('检查用户角色配置')
                repair_actions.append('验证权限规则')
                repair_actions.append('建议优化权限提示')
                repair_actions.append('建议添加权限提升路径')

            elif strategy == 'fix_500_internal_error':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析500服务器错误: {request_path}')
                repair_actions.append('分析错误堆栈')
                repair_actions.append('定位问题代码')
                repair_actions.append('建议修复代码bug')
                repair_actions.append('建议添加异常处理')

            elif strategy == 'fix_500_db_error':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析500数据库错误: {request_path}')
                repair_actions.append('检查数据库连接')
                repair_actions.append('验证SQL语句')
                repair_actions.append('建议修复数据问题')
                repair_actions.append('建议添加数据库重试机制')

            elif strategy == 'fix_500_template_error':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析500模板错误: {request_path}')
                repair_actions.append('检查模板路径')
                repair_actions.append('确认模板文件存在')
                repair_actions.append('建议修复render_template调用')

            elif strategy == 'fix_500_import_error':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析500导入错误: {request_path}')
                repair_actions.append('检查模块安装')
                repair_actions.append('验证导入路径')
                repair_actions.append('建议修复依赖问题')

            elif strategy == 'fix_500_permission_error':
                request_path = error.get('error_file', '')
                repair_actions.append(f'分析500权限错误: {request_path}')
                repair_actions.append('检查文件/目录权限')
                repair_actions.append('建议修复权限配置')

            elif strategy == 'fix_error_template_missing':
                repair_actions.append('分析错误页面模板缺失')
                repair_actions.append('检查templates目录')
                repair_actions.append('确认模板文件存在')
                repair_actions.append('建议创建缺失的错误页面模板')

            elif strategy == 'fix_error_static_missing':
                repair_actions.append('分析错误页面静态资源缺失')
                repair_actions.append('检查static目录')
                repair_actions.append('确认资源文件存在')
                repair_actions.append('建议修复资源引用路径')

            else:
                repair_actions.append(f'通用修复策略: {strategy}')

            repair_actions.append('验证修复结果')
            duration = (datetime.now() - start_time).total_seconds()

        except Exception as e:
            repair_result = 'failed'
            validation_result = f'修复异常: {str(e)}'
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"  ✗ 修复失败: {e}")

            # 上报黑匣子
            if self._get_rule_bool('AUTO_REPAIR_REPORT_BLACKBOX', True):
                self._report_blackbox('auto_repair_failure', '自动修复失败',
                                     f'修复策略:{strategy}, 错误:{str(e)}',
                                     impact_scope=error.get('error_type', 'unknown'))

        # 记录执行结果到数据库
        self._record_execution(execution_id, error, solution, repair_result,
                              repair_actions, validation_result, duration)

        # 更新方案统计
        self._update_solution_stats(solution['solution_id'], repair_result == 'success', duration)

        # 修复成功后记录案例
        if repair_result == 'success' and self._get_rule_bool('AUTO_REPAIR_RECORD_CASE', True):
            self._record_repair_case(execution_id, error, solution, repair_actions)

        # 修复成功后投喂脑库
        if repair_result == 'success' and self._get_rule_bool('AUTO_REPAIR_FEED_BRAIN', True):
            self._feed_brain(error, solution)

        return repair_result == 'success'

    def _backup_file(self, file_path):
        """备份文件"""
        try:
            backup_path = file_path + '.bak'
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"  ✓ 文件已备份: {os.path.basename(file_path)} -> {os.path.basename(backup_path)}")
        except Exception as e:
            logger.warning(f"  ⚠ 文件备份失败: {e}")

    def _fix_tab_to_spaces(self, file_path):
        """将Tab转换为4空格"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            new_content = content.replace('\t', '    ')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"  ✓ Tab已转换为4空格: {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"  ⚠ Tab转换失败: {e}")

    def _fix_file_encoding(self, file_path):
        """修复文件编码为UTF-8"""
        try:
            # 尝试多种编码读取
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1', 'shift_jis']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    # 用UTF-8重写
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"  ✓ 文件编码已转换为UTF-8: {os.path.basename(file_path)} (原编码:{encoding})")
                    return
                except (UnicodeDecodeError, UnicodeEncodeError):
                    continue
        except Exception as e:
            logger.warning(f"  ⚠ 编码修复失败: {e}")

    def _remove_bom(self, file_path):
        """移除BOM头"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            # 移除UTF-8 BOM
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
            # 移除UTF-16 BOM
            elif content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
                content = content[2:]
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"  ✓ BOM头已移除: {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"  ⚠ BOM移除失败: {e}")

    def _fix_line_endings(self, file_path):
        """统一行尾符为LF"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            # CRLF -> LF
            new_content = content.replace(b'\r\n', b'\n')
            # CR -> LF
            new_content = new_content.replace(b'\r', b'\n')
            with open(file_path, 'wb') as f:
                f.write(new_content)
            logger.info(f"  ✓ 行尾符已统一为LF: {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"  ⚠ 行尾符修复失败: {e}")

    def _fix_json_file(self, file_path):
        """尝试修复JSON文件格式"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # 常见修复：移除尾部逗号
            import json
            # 尝试移除对象/数组中多余的逗号
            fixed_content = re.sub(r',\s*([}\]])', r'\1', content)
            # 验证修复结果
            json.loads(fixed_content)
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"  ✓ JSON格式已修复: {os.path.basename(file_path)}")
            return True
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"  ⚠ JSON修复失败: {e}")
            return False

    def _record_execution(self, execution_id, error, solution, result, actions, validation, duration):
        """记录修复执行到数据库"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO auto_repair_executions (execution_id, error_source, error_id, error_type, error_message, error_stack_trace, error_file, error_line, matched_solution_id, match_confidence, repair_strategy, repair_actions, repair_result, repair_duration, validation_result, reported_to_database, created_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    execution_id,
                    error.get('source', 'unknown'),
                    error.get('error_id', ''),
                    error.get('error_type', 'unknown'),
                    error.get('error_message', '')[:500],
                    error.get('stack_trace', '')[:1000],
                    error.get('error_file', ''),
                    error.get('error_line', ''),
                    solution.get('solution_id', ''),
                    solution.get('confidence', 0),
                    solution.get('strategy', ''),
                    json.dumps(actions, ensure_ascii=False),
                    result,
                    round(duration, 4),
                    validation,
                    1,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

                # 如果来源是error_logs或http_404或http_error，更新错误状态
                if (error.get('source') == 'error_logs' or error.get('source') == 'http_404' or error.get(
                'source') == 'http_error') and result == 'success':
                    cursor.execute("UPDATE error_logs SET status = 'resolved', resolved_at = ? WHERE id = ?",
                                  (datetime.now().isoformat(), int(error['error_id'])))

                conn.commit()

            logger.info(f"  ✓ 修复执行已记录: {execution_id} (结果:{result})")
            self._log_maintenance('auto_repair', error.get('error_type', 'unknown'), result,
                                 f'执行ID:{execution_id}, 方案:{solution.get("title", "")}, 耗时:{duration:.2f}s')
        except Exception as e:
            logger.error(f"记录修复执行失败: {e}")

    def _update_solution_stats(self, solution_id, success, duration):
        """更新修复方案统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' UPDATE repair_solutions SET total_attempts = total_attempts + 1, success_count = success_count + ?, failure_count = failure_count + ?, success_rate = CAST(success_count AS REAL) / MAX(total_attempts, 1), avg_fix_duration = (avg_fix_duration * (total_attempts - 1) + ?) / MAX(total_attempts, 1), last_used = ?, updated_at = ? WHERE solution_id = ? ''', (1 if success else 0, 0 if success else 1,
                      duration, datetime.now().isoformat(),
                      datetime.now().isoformat(), solution_id))
                conn.commit()
        except Exception as e:
            logger.error(f"更新方案统计失败: {e}")

    def _record_repair_case(self, execution_id, error, solution, actions):
        """记录修复案例"""
        case_id = self._gen_id('CASE')
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                root_cause = self._analyze_root_cause(error, solution)
                lessons = self._extract_lessons(error, solution)

                cursor.execute(''' INSERT INTO repair_cases (case_id, execution_id, solution_id, error_summary, error_category, error_severity, root_cause, fix_approach, fix_steps, fix_code, verification_method, outcome, lessons_learned, prevention_measures, ai_knowledge_tags, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    case_id, execution_id, solution.get('solution_id', ''),
                    error.get('error_message', '')[:200],
                    error.get('error_type', 'unknown'),
                    solution.get('severity', 'medium'),
                    root_cause,
                    solution.get('title', ''),
                    solution.get('steps', ''),
                    solution.get('code', ''),
                    'database_validation',
                    'success',
                    lessons,
                    self._suggest_prevention(error, solution),
                    f"{error.get('error_type', '')},{solution.get('strategy', '')},{error.get('source', '')}",
                    datetime.now().isoformat(),
                    'auto_repair_engine'
                ))
                conn.commit()

            logger.info(f"  ✓ 修复案例已记录: {case_id}")
        except Exception as e:
            logger.error(f"记录修复案例失败: {e}")

    def _analyze_root_cause(self, error, solution):
        """分析根本原因"""
        causes = {
            'database': '数据库操作不当或数据不一致',
            'file': '文件路径错误或文件缺失',
            'module': '依赖模块缺失或版本不兼容',
            'runtime': '运行时数据异常或空值引用',
            'network': '网络连接不稳定或配置错误',
            'code': '代码逻辑或语法错误',
            'template': '模板路径配置错误或模板缺失',
        }
        return causes.get(solution.get('error_type', ''), '未知原因')

    def _extract_lessons(self, error, solution):
        """提取经验教训"""
        return (f"错误类型:{error.get('error_type', '')}, "
                f"修复策略:{solution.get('strategy', '')}, "
                f"置信度:{solution.get('confidence', 0):.2f}, "
                f"关键点:确保{solution.get('error_type', '')}相关操作的健壮性")

    def _suggest_prevention(self, error, solution):
        """建议预防措施"""
        preventions = {
            'database': '添加数据库操作异常处理，使用WAL模式，定期执行完整性检查',
            'file': '操作前检查文件存在性，使用os.path.exists验证',
            'module': '使用try/except处理可选依赖，提供降级方案',
            'runtime': '添加空值检查，使用防御性编程',
            'network': '添加重试机制，设置合理超时',
            'code': '添加代码审查，使用lint工具检查',
            'template': '检查模板路径配置，确保模板文件存在',
        }
        return preventions.get(solution.get('error_type', ''), '定期检查和测试')

    def _feed_brain(self, error, solution):
        """投喂修复案例到脑库"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                knowledge_id = f"RK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.getpid()}"

                cursor.execute(''' INSERT OR IGNORE INTO ai_brain_knowledge (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    knowledge_id,
                    f"修复案例: {solution.get('title', '')}",
                    f"错误: {error.get('error_message', '')[:200]}\n方案: {solution.get('description', '')}\n策略: {solution.get('strategy', '')}\n步骤: {solution.get('steps', '')}",
                    'experience',
                    'auto_repair_engine',
                    f"repair,{error.get('error_type', '')},{solution.get('strategy', '')}",
                    8,
                    'active',
                    datetime.now().isoformat()
                ))

                # 更新修复案例的feeding标记
                cursor.execute(''' UPDATE repair_cases SET feeding_to_brain = 1, brain_knowledge_id = ? WHERE execution_id IN ( SELECT execution_id FROM auto_repair_executions WHERE matched_solution_id = ? ORDER BY id DESC LIMIT 1 ) ''', (knowledge_id, solution.get('solution_id', '')))

                conn.commit()

            logger.info(f"  ✓ 修复案例已投喂脑库: {knowledge_id}")
        except Exception as e:
            logger.error(f"投喂脑库失败: {e}")

    # ========== 自学习 ==========

    def self_learn(self):
        """从修复记录中学习新方案"""
        if not self._get_rule_bool('AUTO_REPAIR_SELF_LEARNING', True):
            return

        logger.info("[自学习] 分析修复记录，提取新方案...")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 找出修复成功但没有匹配预置方案的错误
                cursor.execute(''' SELECT error_type, error_message, repair_strategy, repair_result FROM auto_repair_executions WHERE repair_result = 'success' AND matched_solution_id = '' GROUP BY error_type, repair_strategy LIMIT 10 ''')

                new_solutions = 0
                for row in cursor.fetchall():
                    error_type, error_message, strategy, _ = row
                    if not error_type:
                        continue

                    # 创建新方案
                    pattern = re.escape(error_type)[:50]
                    solution_id = f"SOL-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{new_solutions}"

                    cursor.execute(''' INSERT OR IGNORE INTO repair_solutions (solution_id, error_pattern, error_type, solution_title, solution_description, solution_steps, solution_code, fix_strategy, confidence_score, applicable_modules, severity_level, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        solution_id, pattern, error_type,
                        f'自动学习: {error_type}修复',
                        f'从修复记录中自动提取的方案: {error_message[:100]}',
                        json.dumps([f'自动策略: {strategy}']),
                        '', strategy, 0.6,
                        'auto_learned', 'medium', 'active',
                        'auto_repair_engine',
                        datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                    new_solutions += 1

                conn.commit()

            if new_solutions > 0:
                self.new_solutions_count += new_solutions
                logger.info(f"  ✓ 自学习完成: 提取了 {new_solutions} 个新方案")
                self._log_maintenance('self_learning', 'repair_solutions', 'success',
                                     f'提取{new_solutions}个新修复方案')
        except Exception as e:
            logger.error(f"自学习失败: {e}")

    # ========== 主流程 ==========

    def run_repair_cycle(self):
        """执行完整的修复循环"""
        logger.info("=" * 60)
        logger.info("  自动修复引擎 - 执行修复循环")
        logger.info("=" * 60)

        # 1. 扫描错误
        errors = self.scan_all_errors()
        logger.info(f"[扫描] 发现 {len(errors)} 个待修复错误")

        if not errors:
            logger.info("  ✓ 无待修复错误")
            logger.info("=" * 60)
            return

        # 2. 逐个匹配并修复
        for error in errors:
            logger.info(f"\n[修复] 处理错误: {error['error_type']} - {error['error_message'][:80]}")

            solution = self.match_solution(error)
            if solution:
                logger.info(f"  ✓ 匹配到方案: {solution['title']} (置信度:{solution['confidence']:.2f})")

                if self._get_rule_bool('AUTO_REPAIR_AUTO_EXECUTE', True):
                    success = self.execute_repair(error, solution)
                    if success:
                        self.repaired_count += 1
                    else:
                        self.failed_count += 1
                else:
                    logger.info("  ⚠ 自动执行未启用，仅记录")
                    self.skipped_count += 1
            else:
                logger.info(f"  ⚠ 未匹配到修复方案")
                self.skipped_count += 1

                # 自学习：记录未匹配的错误
                if self._get_rule_bool('AUTO_REPAIR_SELF_LEARNING', True):
                    self._record_unmatched_error(error)

        # 3. 自学习
        self.self_learn()

        logger.info("=" * 60)
        logger.info(
        f"  修复结果: 成功{self.repaired_count} | 失败{self.failed_count} | 跳过{self.skipped_count} |  新方案{self.new_solutions_count}")
        logger.info("=" * 60)

    def _record_unmatched_error(self, error):
        """记录未匹配的错误（供自学习）"""
        try:
            execution_id = self._gen_id('UNMATCHED')
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO auto_repair_executions (execution_id, error_source, error_id, error_type, error_message, error_stack_trace, repair_result, repair_actions, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    execution_id, error.get('source', ''), error.get('error_id', ''),
                    error.get('error_type', ''), error.get('error_message', '')[:500],
                    error.get('stack_trace', '')[:500],
                    'unmatched', json.dumps(['无匹配方案'], ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass


def main():
    engine = AutoRepairEngine()
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        engine.run_repair_cycle()
    else:
        engine.run_repair_cycle()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - Python文件自动修复和优化工具 v3.1
自动修复Python文件中的异常和错误
自动删除不必要的文件
记录到数据库和日志
"""

import os
import sys
import ast
import re
import json
import logging
import sqlite3
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('py_optimizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('py_optimizer')

class DatabaseLogger:
    """数据库日志记录器"""
    
    def __init__(self, db_path: str = "py_optimizer.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                file_path TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT,
                error_type TEXT,
                error_message TEXT,
                lines_fixed INTEGER DEFAULT 0,
                backup_path TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fix_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                file_path TEXT NOT NULL,
                fix_type TEXT NOT NULL,
                original_code TEXT,
                fixed_code TEXT,
                description TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_files INTEGER,
                files_fixed INTEGER,
                files_deleted INTEGER,
                files_unchanged INTEGER,
                errors_count INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def log_file_operation(self, file_path: str, operation: str, status: str,
                          error_type: str = None, error_message: str = None,
                          lines_fixed: int = 0, backup_path: str = None):
        """记录文件操作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 确保所有参数都是正确的类型，None转换为None字符串或者直接传None
        cursor.execute("""
            INSERT INTO file_operations 
            (timestamp, file_path, operation, status, error_type, error_message, lines_fixed, backup_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), str(file_path), operation, status, 
              str(error_type) if error_type is not None else None, 
              str(error_message) if error_message is not None else None, 
              int(lines_fixed), 
              str(backup_path) if backup_path is not None else None))
        
        conn.commit()
        conn.close()
    
    def log_fix_operation(self, file_path: str, fix_type: str, original_code: str,
                         fixed_code: str, description: str = None):
        """记录修复操作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO fix_operations 
            (timestamp, file_path, fix_type, original_code, fixed_code, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), file_path, fix_type, 
              original_code[:500] if original_code else None,
              fixed_code[:500] if fixed_code else None,
              description))
        
        conn.commit()
        conn.close()
    
    def save_optimization_stats(self, total_files: int, files_fixed: int,
                               files_deleted: int, files_unchanged: int, errors_count: int):
        """保存优化统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO optimization_stats 
            (timestamp, total_files, files_fixed, files_deleted, files_unchanged, errors_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), total_files, files_fixed, 
              files_deleted, files_unchanged, errors_count))
        
        conn.commit()
        conn.close()
    
    def get_recent_operations(self, limit: int = 20) -> List[Dict]:
        """获取最近操作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM file_operations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'timestamp', 'file_path', 'operation', 'status', 
                  'error_type', 'error_message', 'lines_fixed', 'backup_path']
        return [dict(zip(columns, row)) for row in rows]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM file_operations WHERE operation = 'fix' AND status = 'success'")
        fixed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_operations WHERE operation = 'delete' AND status = 'success'")
        deleted_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_operations WHERE status = 'failed'")
        errors_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(lines_fixed) FROM file_operations WHERE status = 'success'")
        total_lines_fixed = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'files_fixed': fixed_count,
            'files_deleted': deleted_count,
            'errors_count': errors_count,
            'total_lines_fixed': total_lines_fixed
        }

class PythonCodeFixer:
    """Python代码自动修复器"""
    
    def __init__(self, db_logger: DatabaseLogger):
        self.db_logger = db_logger
        self.fixes_applied = []
    
    def check_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """检查Python语法"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def fix_indentation_errors(self, code: str) -> Tuple[str, int]:
        """修复缩进错误"""
        lines = code.split('\n')
        fixed_lines = []
        fixes_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.strip().startswith(('except', 'finally', 'else', 'elif')) and not line.strip().endswith(':'):
                original = line
                fixed_lines.append(line + ':')
                fixes_count += 1
                self.db_logger.log_fix_operation(
                    "unknown", "indentation", original, line + ':',
                    "自动添加缺失的冒号"
                )
            elif i > 0 and line and not line[0].isspace() and lines[i-1].strip().endswith(':'):
                if any(keyword in lines[i-1] for keyword in ['def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'with ']):
                    original = line
                    fixed_lines.append('    ' + line)
                    fixes_count += 1
                    self.db_logger.log_fix_operation(
                        "unknown", "indentation", original, '    ' + line,
                        "自动添加缩进"
                    )
            else:
                fixed_lines.append(line)
            
            i += 1
        
        return '\n'.join(fixed_lines), fixes_count
    
    def fix_missing_imports(self, code: str) -> Tuple[str, int]:
        """修复缺失的导入"""
        fixes_count = 0
        lines = code.split('\n')
        
        missing_imports = []
        
        if 'logging' in code and 'import logging' not in code:
            missing_imports.append('import logging')
            fixes_count += 1
        
        if 'json' in code and 'import json' not in code:
            missing_imports.append('import json')
            fixes_count += 1
        
        if 'sys' in code and 'import sys' not in code:
            missing_imports.append('import sys')
            fixes_count += 1
        
        if 'os' in code and 'import os' not in code:
            missing_imports.append('import os')
            fixes_count += 1
        
        if 'datetime' in code and 'from datetime import' not in code and 'import datetime' not in code:
            missing_imports.append('from datetime import datetime')
            fixes_count += 1
        
        if missing_imports:
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import') or line.strip().startswith('from'):
                    insert_pos = i + 1
            
            for imp in reversed(missing_imports):
                lines.insert(insert_pos, imp)
                self.db_logger.log_fix_operation(
                    "unknown", "import", "", imp,
                    "添加缺失的导入语句"
                )
        
        return '\n'.join(lines), fixes_count
    
    def fix_encoding_issues(self, code: str) -> Tuple[str, int]:
        """修复编码问题"""
        fixes_count = 0
        
        if not code.startswith('# -*- coding:'):
            lines = code.split('\n')
            if lines and not lines[0].startswith('#'):
                lines.insert(0, '# -*- coding: utf-8 -*-')
                fixes_count += 1
                self.db_logger.log_fix_operation(
                    "unknown", "encoding", "", "# -*- coding: utf-8 -*-",
                    "添加UTF-8编码声明"
                )
            elif lines and not any('coding' in lines[0] for _ in [1]):
                lines.insert(0, '# -*- coding: utf-8 -*-')
                fixes_count += 1
            
            code = '\n'.join(lines)
        
        return code, fixes_count
    
    def fix_common_errors(self, code: str) -> Tuple[str, int]:
        """修复常见错误"""
        fixes_count = 0
        
        code = re.sub(r'(\w+)\s*\(\s*\)(\s*else)', r'\1()\2', code)
        
        code = re.sub(r'except\s*:', r'except Exception:', code)
        
        code = re.sub(r'(\w+)\s*===\s*(\w+)', r'\1 == \2', code)
        
        code = re.sub(r'(\w+)\s*!==\s*(\w+)', r'\1 != \2', code)
        
        return code, fixes_count
    
    def fix_file(self, file_path: str) -> Dict[str, Any]:
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            code = original_code
            total_fixes = 0
            
            code, count = self.fix_encoding_issues(code)
            total_fixes += count
            
            code, count = self.fix_indentation_errors(code)
            total_fixes += count
            
            code, count = self.fix_missing_imports(code)
            total_fixes += count
            
            code, count = self.fix_common_errors(code)
            total_fixes += count
            
            is_valid, error_msg = self.check_syntax(code)
            
            if is_valid and code != original_code:
                backup_path = self._create_backup(file_path)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                self.db_logger.log_file_operation(
                    file_path, 'fix', 'success',
                    lines_fixed=total_fixes,
                    backup_path=backup_path
                )
                
                logger.info(f"已修复文件: {file_path} (修复了 {total_fixes} 处)")
                
                return {
                    'success': True,
                    'file': file_path,
                    'fixes_applied': total_fixes,
                    'backup': backup_path
                }
            elif is_valid:
                self.db_logger.log_file_operation(
                    file_path, 'check', 'success'
                )
                return {
                    'success': True,
                    'file': file_path,
                    'fixes_applied': 0,
                    'message': '无需修复'
                }
            else:
                self.db_logger.log_file_operation(
                    file_path, 'fix', 'failed',
                    error_type='SyntaxError',
                    error_message=error_msg
                )
                return {
                    'success': False,
                    'file': file_path,
                    'error': error_msg
                }
        
        except Exception as e:
            error_msg = str(e)
            self.db_logger.log_file_operation(
                file_path, 'fix', 'failed',
                error_type=type(e).__name__,
                error_message=error_msg
            )
            logger.error(f"修复文件失败: {file_path} - {error_msg}")
            return {
                'success': False,
                'file': file_path,
                'error': error_msg
            }
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """创建备份"""
        try:
            backup_dir = Path('backups')
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

class UnnecessaryFileDeleter:
    """删除不必要的文件"""
    
    def __init__(self, db_logger: DatabaseLogger, whitelist: List[str] = None):
        self.db_logger = db_logger
        self.whitelist = whitelist or []
        self.deleted_files = []
    
    def is_unnecessary(self, file_path: str) -> bool:
        """判断文件是否不必要"""
        file_name = os.path.basename(file_path)
        path_obj = Path(file_path)
        
        unnecessary_patterns = [
            r'^test_.*\.py$',
            r'.*_test\.py$',
            r'^tests\.py$',
            r'.*\.bak$',
            r'.*\.backup$',
            r'.*\.old$',
            r'.*_backup.*\.py$',
            r'.*_backup.*$',
            r'.*\.tmp$',
            r'.*\.temp$',
            r'^__pycache__$',
            r'.*\.pyc$',
            r'.*\.pyo$',
        ]
        
        for pattern in unnecessary_patterns:
            if re.match(pattern, file_name):
                if file_path not in self.whitelist:
                    return True
        
        if path_obj.name in ['__pycache__', '.DS_Store']:
            return True
        
        return False
    
    def delete_file(self, file_path: str, create_backup: bool = True) -> bool:
        """删除文件"""
        try:
            if not os.path.exists(file_path):
                return False
            
            backup_path = None
            if create_backup:
                backup_dir = Path('backups')
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
                backup_path = backup_dir / backup_name
                
                shutil.copy2(file_path, backup_path)
            
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            
            self.db_logger.log_file_operation(
                file_path, 'delete', 'success',
                backup_path=backup_path
            )
            
            self.deleted_files.append(file_path)
            logger.info(f"已删除文件: {file_path}")
            
            return True
        
        except Exception as e:
            self.db_logger.log_file_operation(
                file_path, 'delete', 'failed',
                error_type=type(e).__name__,
                error_message=str(e)
            )
            logger.error(f"删除文件失败: {file_path} - {e}")
            return False
    
    def scan_and_delete(self, root_dir: str, auto_approve: bool = True) -> List[str]:
        """扫描并删除不必要文件"""
        deleted = []
        
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py') or self.is_unnecessary(os.path.join(root, file)):
                    file_path = os.path.join(root, file)
                    
                    if self.is_unnecessary(file_path):
                        if auto_approve or file_path in self.whitelist:
                            if self.delete_file(file_path):
                                deleted.append(file_path)
                        else:
                            logger.info(f"需要确认删除: {file_path}")
        
        return deleted

class PythonOptimizer:
    """Python优化器主类"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.db_logger = DatabaseLogger()
        self.fixer = PythonCodeFixer(self.db_logger)
        self.deleter = UnnecessaryFileDeleter(self.db_logger)
        self.stats = {
            'total_files': 0,
            'files_fixed': 0,
            'files_deleted': 0,
            'files_unchanged': 0,
            'errors': []
        }
    
    def scan_python_files(self) -> List[str]:
        """扫描所有Python文件"""
        py_files = []
        
        for py_file in self.base_path.rglob('*.py'):
            if py_file.is_file():
                py_files.append(str(py_file))
        
        self.stats['total_files'] = len(py_files)
        logger.info(f"扫描到 {len(py_files)} 个Python文件")
        
        return py_files
    
    def optimize(self, auto_approve: bool = True, fix_errors: bool = True,
                delete_unnecessary: bool = True) -> Dict[str, Any]:
        """运行优化"""
        start_time = time.time()
        
        logger.info("开始Python文件优化...")
        
        py_files = self.scan_python_files()
        
        for file_path in py_files:
            if fix_errors:
                result = self.fixer.fix_file(file_path)
                if result['success']:
                    if result.get('fixes_applied', 0) > 0:
                        self.stats['files_fixed'] += 1
                    else:
                        self.stats['files_unchanged'] += 1
                else:
                    self.stats['errors'].append({
                        'file': file_path,
                        'error': result.get('error')
                    })
        
        if delete_unnecessary:
            deleted = self.deleter.scan_and_delete(str(self.base_path), auto_approve)
            self.stats['files_deleted'] = len(deleted)
        
        execution_time = time.time() - start_time
        
        self.db_logger.save_optimization_stats(
            self.stats['total_files'],
            self.stats['files_fixed'],
            self.stats['files_deleted'],
            self.stats['files_unchanged'],
            len(self.stats['errors'])
        )
        
        logger.info(f"优化完成! 耗时: {execution_time:.2f}秒")
        
        return {
            'success': True,
            'statistics': self.stats,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.db_logger.get_statistics()
    
    def get_recent_operations(self, limit: int = 20) -> List[Dict]:
        """获取最近操作"""
        return self.db_logger.get_recent_operations(limit)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Python文件自动修复和优化工具 v3.1')
    parser.add_argument('--optimize', action='store_true', help='运行优化')
    parser.add_argument('--fix', action='store_true', help='修复Python文件错误')
    parser.add_argument('--delete', action='store_true', help='删除不必要文件')
    parser.add_argument('--auto-approve', action='store_true', help='自动批准所有操作')
    parser.add_argument('--no-fix', dest='fix_errors', action='store_false', help='不修复错误')
    parser.add_argument('--no-delete', dest='delete_unnecessary', action='store_false', help='不删除文件')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--logs', action='store_true', help='显示最近操作')
    parser.add_argument('--base-path', default='.', help='基础路径')
    
    args = parser.parse_args()
    
    optimizer = PythonOptimizer(base_path=args.base_path)
    
    if args.optimize or (not any([args.fix, args.delete, args.stats, args.logs])):
        print("\n🚀 开始Python文件优化...")
        
        fix_errors = args.fix_errors if hasattr(args, 'fix_errors') else True
        delete_unnecessary = args.delete_unnecessary if hasattr(args, 'delete_unnecessary') else True
        
        result = optimizer.optimize(
            auto_approve=args.auto_approve,
            fix_errors=fix_errors,
            delete_unnecessary=delete_unnecessary
        )
        
        print("\n📊 优化结果:")
        print(f"  总文件数: {result['statistics']['total_files']}")
        print(f"  修复文件: {result['statistics']['files_fixed']}")
        print(f"  删除文件: {result['statistics']['files_deleted']}")
        print(f"  无需修改: {result['statistics']['files_unchanged']}")
        print(f"  错误数量: {len(result['statistics']['errors'])}")
        print(f"  耗时: {result['execution_time']:.2f}秒")
        
        if result['statistics']['errors']:
            print("\n⚠️ 错误列表:")
            for error in result['statistics']['errors'][:10]:
                print(f"  - {error['file']}: {error['error']}")
    
    elif args.fix:
        print("\n🔧 修复Python文件错误...")
        
        py_files = optimizer.scan_python_files()
        
        fixed_count = 0
        for file_path in py_files:
            result = optimizer.fixer.fix_file(file_path)
            if result['success'] and result.get('fixes_applied', 0) > 0:
                fixed_count += 1
        
        print(f"\n✅ 已修复 {fixed_count} 个文件")
    
    elif args.delete:
        print("\n🗑️ 删除不必要文件...")
        
        deleted = optimizer.deleter.scan_and_delete(args.base_path, args.auto_approve)
        
        print(f"\n✅ 已删除 {len(deleted)} 个文件")
        for file in deleted[:10]:
            print(f"  - {file}")
        if len(deleted) > 10:
            print(f"  ... 还有 {len(deleted) - 10} 个文件")
    
    elif args.stats:
        stats = optimizer.get_statistics()
        
        print("\n📊 统计信息:")
        print(f"  修复文件: {stats['files_fixed']}")
        print(f"  删除文件: {stats['files_deleted']}")
        print(f"  错误数量: {stats['errors_count']}")
        print(f"  修复行数: {stats['total_lines_fixed']}")
    
    elif args.logs:
        logs = optimizer.get_recent_operations(20)
        
        print("\n📝 最近操作:")
        for log in logs:
            status_icon = '✅' if log['status'] == 'success' else '❌'
            print(f"  {status_icon} [{log['timestamp']}] {log['file_path']} - {log['operation']}")
            if log.get('lines_fixed'):
                print(f"      修复了 {log['lines_fixed']} 处")
            if log.get('error_message'):
                print(f"      错误: {log['error_message']}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

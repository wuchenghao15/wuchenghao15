# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - Enhanced System Manager v3.1
系统管理增强模块 - 包含数据库记录、白名单、自动操作确认
"""

import os
import sys
import json
import logging
import sqlite3
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('system_manager')

class DatabaseLogger:
    """数据库日志记录器"""
    
    def __init__(self, db_path: str = "system_manager.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                operation TEXT NOT NULL,
                user_id TEXT,
                details TEXT,
                status TEXT,
                error_message TEXT,
                execution_time REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_value TEXT NOT NULL UNIQUE,
                added_by TEXT,
                added_at TEXT,
                description TEXT,
                enabled INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                file_path TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT,
                backup_path TEXT,
                error_message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def log_operation(self, operation: str, user_id: str = None, details: str = None,
                     status: str = "success", error_message: str = None, execution_time: float = 0.0):
        """记录操作日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO operation_logs (timestamp, operation, user_id, details, status, error_message, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), operation, user_id, details, status, error_message, execution_time))
        
        conn.commit()
        conn.close()
        
        logger.info(f"操作日志已记录: {operation} - {status}")
    
    def add_to_whitelist(self, item_type: str, item_value: str, added_by: str = "system",
                        description: str = None) -> bool:
        """添加白名单项"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO whitelist (item_type, item_value, added_by, added_at, description, enabled)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (item_type, item_value, added_by, datetime.now().isoformat(), description))
            
            conn.commit()
            conn.close()
            
            logger.info(f"白名单已添加: {item_type} - {item_value}")
            return True
        except Exception as e:
            logger.error(f"添加白名单失败: {e}")
            return False
    
    def is_in_whitelist(self, item_type: str, item_value: str) -> bool:
        """检查是否在白名单中"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM whitelist
            WHERE item_type = ? AND item_value = ? AND enabled = 1
        """, (item_type, item_value))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_whitelist(self, item_type: str = None) -> List[Dict]:
        """获取白名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if item_type:
            cursor.execute("""
                SELECT * FROM whitelist WHERE item_type = ? AND enabled = 1
            """, (item_type,))
        else:
            cursor.execute("SELECT * FROM whitelist WHERE enabled = 1")
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'item_type', 'item_value', 'added_by', 'added_at', 'description', 'enabled']
        return [dict(zip(columns, row)) for row in rows]
    
    def remove_from_whitelist(self, item_type: str, item_value: str) -> bool:
        """从白名单移除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE whitelist SET enabled = 0
                WHERE item_type = ? AND item_value = ?
            """, (item_type, item_value))
            
            conn.commit()
            conn.close()
            
            logger.info(f"白名单项已禁用: {item_type} - {item_value}")
            return True
        except Exception as e:
            logger.error(f"移除白名单失败: {e}")
            return False
    
    def log_file_operation(self, file_path: str, operation: str, status: str,
                          backup_path: str = None, error_message: str = None):
        """记录文件操作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO file_operations (timestamp, file_path, operation, status, backup_path, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), file_path, operation, status, backup_path, error_message))
        
        conn.commit()
        conn.close()
    
    def get_operation_logs(self, limit: int = 100) -> List[Dict]:
        """获取操作日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM operation_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'timestamp', 'operation', 'user_id', 'details', 'status', 'error_message', 'execution_time']
        return [dict(zip(columns, row)) for row in rows]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM operation_logs WHERE status = 'success'")
        success_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM operation_logs WHERE status = 'failed'")
        failed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM whitelist WHERE enabled = 1")
        whitelist_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_operations")
        file_ops_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_operations': success_count + failed_count,
            'successful_operations': success_count,
            'failed_operations': failed_count,
            'whitelist_items': whitelist_count,
            'file_operations': file_ops_count
        }

class AutoApprovalManager:
    """自动批准管理器"""
    
    def __init__(self, whitelist_file: str = "whitelist.json"):
        self.whitelist_file = whitelist_file
        self.whitelist = self._load_whitelist()
        self.auto_approve_patterns = self._get_default_patterns()
    
    def _load_whitelist(self) -> Dict[str, List[str]]:
        """加载白名单"""
        if os.path.exists(self.whitelist_file):
            try:
                with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载白名单失败: {e}")
        
        return {
            'file_patterns': [],
            'operations': [],
            'users': []
        }
    
    def _save_whitelist(self):
        """保存白名单"""
        try:
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(self.whitelist, f, ensure_ascii=False, indent=2)
            logger.info("白名单已保存")
        except Exception as e:
            logger.error(f"保存白名单失败: {e}")
    
    def _get_default_patterns(self) -> List[str]:
        """获取默认自动批准模式"""
        return [
            '*.py',
            '*.json',
            '*.txt',
            '*.md',
            '*.yml',
            '*.yaml',
            '*.html',
            '*.css',
            '*.js'
        ]
    
    def add_auto_approve_pattern(self, pattern: str):
        """添加自动批准模式"""
        if pattern not in self.whitelist['file_patterns']:
            self.whitelist['file_patterns'].append(pattern)
            self._save_whitelist()
            logger.info(f"自动批准模式已添加: {pattern}")
    
    def remove_auto_approve_pattern(self, pattern: str):
        """移除自动批准模式"""
        if pattern in self.whitelist['file_patterns']:
            self.whitelist['file_patterns'].remove(pattern)
            self._save_whitelist()
            logger.info(f"自动批准模式已移除: {pattern}")
    
    def should_auto_approve(self, item_type: str, item_value: str) -> bool:
        """检查是否应该自动批准"""
        if item_type == 'file_pattern':
            for pattern in self.whitelist['file_patterns']:
                if self._match_pattern(item_value, pattern):
                    return True
        
        elif item_type == 'operation':
            return item_value in self.whitelist['operations']
        
        elif item_type == 'user':
            return item_value in self.whitelist['users']
        
        return False
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """匹配文件名模式"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def approve_operation(self, operation: str) -> bool:
        """批准操作"""
        if operation not in self.whitelist['operations']:
            self.whitelist['operations'].append(operation)
            self._save_whitelist()
            logger.info(f"操作已批准: {operation}")
            return True
        return False
    
    def add_trusted_user(self, user_id: str):
        """添加信任用户"""
        if user_id not in self.whitelist['users']:
            self.whitelist['users'].append(user_id)
            self._save_whitelist()
            logger.info(f"信任用户已添加: {user_id}")

class SystemOptimizer:
    """系统优化器"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.db_logger = DatabaseLogger()
        self.approval_manager = AutoApprovalManager()
    
    def scan_redundant_files(self) -> Dict[str, List[str]]:
        """扫描冗余文件"""
        redundant = {
            'test_files': [],
            'backup_files': [],
            'temp_files': [],
            'duplicate_files': [],
            'obsolete_files': []
        }
        
        test_patterns = ['test_*.py', '*_test.py', 'tests.py']
        backup_patterns = ['*.bak', '*.backup', '*.old', '*_backup*']
        temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store']
        obsolete_patterns = ['__pycache__', '*.pyc', '*.pyo', 'node_modules']
        
        import fnmatch
        
        for py_file in self.base_path.rglob('*.py'):
            if py_file.is_file():
                relative_path = str(py_file.relative_to(self.base_path))
                
                for pattern in test_patterns:
                    if fnmatch.fnmatch(py_file.name, pattern):
                        redundant['test_files'].append(relative_path)
                        break
                
                for pattern in backup_patterns:
                    if fnmatch.fnmatch(py_file.name, pattern):
                        redundant['backup_files'].append(relative_path)
                        break
                
                for pattern in temp_patterns:
                    if fnmatch.fnmatch(py_file.name, pattern):
                        redundant['temp_files'].append(relative_path)
                        break
                
                if '__pycache__' in str(py_file) or py_file.suffix == '.pyc':
                    redundant['obsolete_files'].append(relative_path)
        
        logger.info(f"扫描完成: 发现 {len(redundant['test_files'])} 个测试文件, "
                   f"{len(redundant['backup_files'])} 个备份文件, "
                   f"{len(redundant['temp_files'])} 个临时文件, "
                   f"{len(redundant['obsolete_files'])} 个过时文件")
        
        return redundant
    
    def delete_file(self, file_path: str, create_backup: bool = True) -> bool:
        """删除文件（带备份）"""
        try:
            full_path = self.base_path / file_path if not os.path.isabs(file_path) else Path(file_path)
            
            if not full_path.exists():
                logger.warning(f"文件不存在: {full_path}")
                return False
            
            backup_path = None
            if create_backup:
                backup_dir = self.base_path / 'backups'
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = backup_dir / f"{full_path.stem}_{timestamp}{full_path.suffix}"
                import shutil
                shutil.copy2(full_path, backup_path)
            
            full_path.unlink()
            
            self.db_logger.log_file_operation(str(full_path), 'delete', 'success', str(backup_path))
            logger.info(f"文件已删除: {full_path}")
            
            return True
        
        except Exception as e:
            error_msg = str(e)
            self.db_logger.log_file_operation(str(file_path), 'delete', 'failed', error_message=error_msg)
            logger.error(f"删除文件失败: {file_path} - {error_msg}")
            return False
    
    def optimize_py_files(self, auto_approve: bool = False) -> Dict[str, Any]:
        """优化Python文件"""
        start_time = time.time()
        results = {
            'scanned': 0,
            'optimized': 0,
            'deleted': 0,
            'errors': []
        }
        
        redundant = self.scan_redundant_files()
        
        all_files = (
            redundant['test_files'] +
            redundant['backup_files'] +
            redundant['temp_files'] +
            redundant['obsolete_files']
        )
        
        for file_path in all_files:
            results['scanned'] += 1
            
            if auto_approve or self.approval_manager.should_auto_approve('file_pattern', file_path):
                if self.delete_file(file_path, create_backup=True):
                    results['deleted'] += 1
            else:
                logger.info(f"需要确认删除: {file_path}")
        
        execution_time = time.time() - start_time
        self.db_logger.log_operation(
            operation='optimize_py_files',
            details=f"扫描: {results['scanned']}, 删除: {results['deleted']}, 错误: {len(results['errors'])}",
            status='success' if not results['errors'] else 'partial',
            execution_time=execution_time
        )
        
        return results
    
    def analyze_code_quality(self, file_path: str) -> Dict[str, Any]:
        """分析代码质量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            blank_lines = total_lines - code_lines - comment_lines
            
            issues = []
            
            if total_lines > 1000:
                issues.append('文件过大，建议拆分成多个模块')
            
            if 'import *' in content:
                issues.append('避免使用 import *')
            
            if len([l for l in lines if len(l) > 120]) > total_lines * 0.1:
                issues.append('存在过多长行，建议控制在120字符以内')
            
            return {
                'file': file_path,
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'issues': issues,
                'quality_score': max(0, 100 - len(issues) * 10)
            }
        
        except Exception as e:
            return {
                'file': file_path,
                'error': str(e)
            }

class EnhancedSystemManager:
    """增强的系统管理器"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.db_logger = DatabaseLogger()
        self.approval_manager = AutoApprovalManager()
        self.optimizer = SystemOptimizer(base_path)
        self._init_default_whitelist()
    
    def _init_default_whitelist(self):
        """初始化默认白名单"""
        self.db_logger.add_to_whitelist(
            'file_pattern', '*.py',
            added_by='system',
            description='Python源代码文件'
        )
        
        self.db_logger.add_to_whitelist(
            'file_pattern', '*.json',
            added_by='system',
            description='JSON配置文件'
        )
        
        self.db_logger.add_to_whitelist(
            'file_pattern', '*.md',
            added_by='system',
            description='Markdown文档'
        )
        
        logger.info("默认白名单初始化完成")
    
    def setup_trusted_environment(self):
        """设置信任环境"""
        self.approval_manager.add_trusted_user('system')
        self.approval_manager.add_trusted_user('admin')
        self.approval_manager.add_trusted_user('root')
        
        for pattern in ['*.py', '*.json', '*.txt', '*.md', '*.yml', '*.yaml']:
            self.approval_manager.add_auto_approve_pattern(pattern)
        
        logger.info("信任环境设置完成")
    
    def run_optimization(self, auto_approve: bool = True) -> Dict[str, Any]:
        """运行优化"""
        logger.info("开始系统优化...")
        
        if auto_approve:
            self.setup_trusted_environment()
        
        results = self.optimizer.optimize_py_files(auto_approve=auto_approve)
        
        stats = self.db_logger.get_statistics()
        
        return {
            'optimization_results': results,
            'system_statistics': stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'version': '3.1.0',
            'status': 'running',
            'statistics': self.db_logger.get_statistics(),
            'whitelist_count': len(self.db_logger.get_whitelist()),
            'recent_operations': len(self.db_logger.get_operation_logs(10))
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MTSCOS AI System Manager v3.1')
    parser.add_argument('--scan', action='store_true', help='扫描冗余文件')
    parser.add_argument('--optimize', action='store_true', help='优化系统')
    parser.add_argument('--auto-approve', action='store_true', help='自动批准所有操作')
    parser.add_argument('--add-whitelist', nargs=2, metavar=('TYPE', 'VALUE'), help='添加白名单')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--logs', action='store_true', help='显示操作日志')
    parser.add_argument('--base-path', default='.', help='基础路径')
    
    args = parser.parse_args()
    
    manager = EnhancedSystemManager(base_path=args.base_path)
    
    if args.scan:
        redundant = manager.optimizer.scan_redundant_files()
        print("\n扫描结果:")
        print(f"  测试文件: {len(redundant['test_files'])}")
        print(f"  备份文件: {len(redundant['backup_files'])}")
        print(f"  临时文件: {len(redundant['temp_files'])}")
        print(f"  过时文件: {len(redundant['obsolete_files'])}")
    
    elif args.optimize:
        results = manager.run_optimization(auto_approve=args.auto_approve)
        print("\n优化结果:")
        print(f"  扫描文件: {results['optimization_results']['scanned']}")
        print(f"  删除文件: {results['optimization_results']['deleted']}")
        print(f"  错误数量: {len(results['optimization_results']['errors'])}")
        print(f"  总操作数: {results['system_statistics']['total_operations']}")
    
    elif args.add_whitelist:
        item_type, item_value = args.add_whitelist
        success = manager.db_logger.add_to_whitelist(item_type, item_value, added_by='cli')
        print(f"\n添加白名单: {'成功' if success else '失败'}")
    
    elif args.status:
        status = manager.get_system_status()
        print("\n系统状态:")
        print(f"  版本: {status['version']}")
        print(f"  状态: {status['status']}")
        print(f"  白名单项: {status['whitelist_count']}")
        print(f"  最近操作: {status['recent_operations']}")
    
    elif args.logs:
        logs = manager.db_logger.get_operation_logs(20)
        print("\n最近操作:")
        for log in logs:
            print(f"  [{log['timestamp']}] {log['operation']} - {log['status']}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

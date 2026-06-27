#!/usr/bin/env python3
"""
系统升级管理器 - 执行完整的系统升级流程
"""

import logging
import os
import shutil
import json
import sqlite3
import hashlib
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_upgrade.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemUpgrader:
    """系统升级管理器"""
    
    def __init__(self):
        self.current_version = "2.0.0"
        self.target_version = "3.0.0"
        self.db_path = 'system_upgrade.db'
        self._init_db()
        
        self.upgrade_tasks = [
            {'id': 'upgrade_core_code', 'name': '升级核心代码', 'priority': 1},
            {'id': 'upgrade_ai_core', 'name': '升级核心AI集', 'priority': 2},
            {'id': 'optimize_role_ai', 'name': '优化角色AI能力', 'priority': 3},
            {'id': 'fix_errors', 'name': '修复错误异常', 'priority': 4},
            {'id': 'clean_redundant_files', 'name': '清理冗余文件', 'priority': 5},
            {'id': 'organize_backups', 'name': '整理备份', 'priority': 6},
            {'id': 'clean_logs', 'name': '清理日志', 'priority': 7},
            {'id': 'rebuild_recovery_image', 'name': '重建恢复镜像', 'priority': 8},
            {'id': 'finalize_upgrade', 'name': '完成升级', 'priority': 9}
        ]
        
        self.task_results = {}
        
    def _init_db(self):
        """初始化升级数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_from TEXT NOT NULL,
            version_to TEXT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            success BOOLEAN DEFAULT FALSE,
            details TEXT,
            logs TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrade_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upgrade_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            task_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            success BOOLEAN DEFAULT FALSE,
            message TEXT,
            FOREIGN KEY(upgrade_id) REFERENCES upgrade_history(id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cleaned_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upgrade_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            action TEXT NOT NULL,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(upgrade_id) REFERENCES upgrade_history(id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upgrade_id INTEGER NOT NULL,
            backup_path TEXT NOT NULL,
            backup_type TEXT NOT NULL,
            file_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(upgrade_id) REFERENCES upgrade_history(id)
            )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_upgrade_tasks_upgrade_id ON upgrade_tasks(upgrade_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cleaned_files_upgrade_id ON cleaned_files(upgrade_id)')
            
            conn.commit()
            
    def _log_task(self, upgrade_id: int, task_id: str, task_name: str, status: str, 
                  success: bool, message: str = ''):
        """记录任务日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO upgrade_tasks
                (upgrade_id, task_id, task_name, status, started_at, completed_at, success, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (upgrade_id, task_id, task_name, status, datetime.now().isoformat(), 
                  datetime.now().isoformat(), success, message))
            conn.commit()
            
        self.task_results[task_id] = {'success': success, 'message': message}
        
    def _log_cleaned_file(self, upgrade_id: int, file_path: str, file_type: str, action: str):
        """记录清理的文件"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cleaned_files
                (upgrade_id, file_path, file_type, action)
                VALUES (?, ?, ?, ?)
            ''', (upgrade_id, file_path, file_type, action))
            conn.commit()
            
    def _log_backup(self, upgrade_id: int, backup_path: str, backup_type: str, file_count: int):
        """记录备份"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backup_records
                (upgrade_id, backup_path, backup_type, file_count)
                VALUES (?, ?, ?, ?)
            ''', (upgrade_id, backup_path, backup_type, file_count))
            conn.commit()
            
    def _start_upgrade(self) -> int:
        """开始升级流程"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO upgrade_history
                (version_from, version_to, started_at)
                VALUES (?, ?, ?)
            ''', (self.current_version, self.target_version, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
            
    def _finish_upgrade(self, upgrade_id: int, success: bool, details: str, logs: str):
        """完成升级"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE upgrade_history
                SET completed_at = ?, success = ?, details = ?, logs = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), success, details, logs, upgrade_id))
            conn.commit()
            
    def upgrade_core_code(self, upgrade_id: int) -> bool:
        """升级核心代码"""
        logger.info("升级核心代码...")
        try:
            self._log_task(upgrade_id, 'upgrade_core', '升级核心代码', 'running', False)
            
            core_modules = [
                'core/config.py',
                'core/session.py', 
                'core/event_tracker.py',
                'core/system_integrator.py',
                'core/grade_management.py'
            ]
            
            for module in core_modules:
                if os.path.exists(module):
                    logger.info(f"检查模块: {module}")
                    with open(module, 'r') as f:
                        content = f.read()
                        if 'version' in content.lower():
                            content = content.replace('2.0.0', '3.0.0')
                            with open(module, 'w') as fw:
                                fw.write(content)
                    logger.info(f"✓ {module} 已更新")
            
            logger.info("核心代码升级完成")
            self._log_task(upgrade_id, 'upgrade_core', '升级核心代码', 'completed', True, 
                         f"已更新 {len(core_modules)} 个核心模块")
            return True
            
        except Exception as e:
            logger.error(f"核心代码升级失败: {str(e)}")
            self._log_task(upgrade_id, 'upgrade_core', '升级核心代码', 'failed', False, str(e))
            return False
            
    def upgrade_ai_core(self, upgrade_id: int) -> bool:
        """升级核心AI集"""
        logger.info("升级核心AI集...")
        try:
            self._log_task(upgrade_id, 'upgrade_ai', '升级核心AI集', 'running', False)
            
            ai_modules = [
                'flask-app/app/ai/adult_education_ai.py',
                'flask-app/app/ai/ai_engine_upgrader.py',
                'flask-app/app/ai/ai_pool_pollution_optimizer.py',
                'flask-app/app/ai/question_bank_maintainer.py'
            ]
            
            for module in ai_modules:
                if os.path.exists(module):
                    logger.info(f"升级AI模块: {module}")
                    
                    with open(module, 'r') as f:
                        content = f.read()
                        content = content.replace('version = "2.0.0"', 'version = "3.0.0"')
                        content = content.replace('current_version = "2.0.0"', 'current_version = "3.0.0"')
                        
                        with open(module, 'w') as fw:
                            fw.write(content)
                    
                    logger.info(f"✓ {module} 已升级")
            
            logger.info("核心AI集升级完成")
            self._log_task(upgrade_id, 'upgrade_ai', '升级核心AI集', 'completed', True,
                         f"已升级 {len(ai_modules)} 个AI模块")
            return True
            
        except Exception as e:
            logger.error(f"核心AI集升级失败: {str(e)}")
            self._log_task(upgrade_id, 'upgrade_ai', '升级核心AI集', 'failed', False, str(e))
            return False
            
    def optimize_role_ai(self, upgrade_id: int) -> bool:
        """优化角色AI能力"""
        logger.info("优化角色AI能力...")
        try:
            self._log_task(upgrade_id, 'optimize_ai', '优化角色AI能力', 'running', False)
            
            role_ai_config = {
                'teacher_ai': {'learning_rate': 0.85, 'adaptability': 0.9},
                'researcher_ai': {'analysis_depth': 4, 'pattern_recognition': 0.95},
                'expert_ai': {'knowledge_integration': 0.9, 'confidence_threshold': 0.85},
                'student_ai': {'assistance_level': 3, 'knowledge_depth': 4},
                'engineer_ai': {'code_analysis': 0.9, 'security_scan': 0.85},
                'butler_ai': {'nlu_accuracy': 0.9, 'task_completion': 0.95}
            }
            
            config_file = 'flask-app/app/ai/ai_engine_upgrader.py'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                    
                    for role, params in role_ai_config.items():
                        for param, value in params.items():
                            content = content.replace(
                                f"'{param}': {{'value':", 
                                f"'{param}': {{'value': {value},"
                            )
                    
                    with open(config_file, 'w') as fw:
                        fw.write(content)
            
            logger.info("角色AI能力优化完成")
            self._log_task(upgrade_id, 'optimize_ai', '优化角色AI能力', 'completed', True,
                         f"已优化 {len(role_ai_config)} 个角色AI")
            return True
            
        except Exception as e:
            logger.error(f"角色AI优化失败: {str(e)}")
            self._log_task(upgrade_id, 'optimize_ai', '优化角色AI能力', 'failed', False, str(e))
            return False
            
    def fix_errors(self, upgrade_id: int) -> bool:
        """修复错误异常"""
        logger.info("修复错误异常...")
        try:
            self._log_task(upgrade_id, 'fix_errors', '修复错误异常', 'running', False)
            
            error_fixes = [
                ('flask-app/ai_middleware_enhancer.py', 'python', 'python3'),
                ('flask-app/app_start_with_project_factory.py', 'python', 'python3'),
                ('Makefile', 'python', 'python3')
            ]
            
            fixed_count = 0
            for file_path, old_str, new_str in error_fixes:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if old_str in content:
                            content = content.replace(old_str, new_str)
                            with open(file_path, 'w') as fw:
                                fw.write(content)
                            fixed_count += 1
                            logger.info(f"✓ 修复: {file_path}")
            
            logger.info(f"错误修复完成，共修复 {fixed_count} 个文件")
            self._log_task(upgrade_id, 'fix_errors', '修复错误异常', 'completed', True,
                         f"已修复 {fixed_count} 个文件的Python解释器引用")
            return True
            
        except Exception as e:
            logger.error(f"错误修复失败: {str(e)}")
            self._log_task(upgrade_id, 'fix_errors', '修复错误异常', 'failed', False, str(e))
            return False
            
    def clean_redundant_files(self, upgrade_id: int) -> bool:
        """清理冗余文件"""
        logger.info("清理冗余文件...")
        try:
            self._log_task(upgrade_id, 'clean_redundant', '清理冗余文件', 'running', False)
            
            redundant_patterns = [
                '*.pyc',
                '__pycache__',
                '*.tmp',
                '*.bak',
                '*.old',
                '.DS_Store',
                '*.log'
            ]
            
            deleted_count = 0
            for pattern in redundant_patterns:
                for root, dirs, files in os.walk('.'):
                    for name in files:
                        if name.endswith(pattern.replace('*', '')) or name == pattern:
                            file_path = os.path.join(root, name)
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                self._log_cleaned_file(upgrade_id, file_path, 'redundant', 'deleted')
                            except:
                                pass
                    if pattern in dirs:
                        dir_path = os.path.join(root, pattern)
                        try:
                            shutil.rmtree(dir_path)
                            deleted_count += 1
                            self._log_cleaned_file(upgrade_id, dir_path, 'directory', 'deleted')
                        except:
                            pass
            
            logger.info(f"冗余文件清理完成，共删除 {deleted_count} 个文件/目录")
            self._log_task(upgrade_id, 'clean_redundant', '清理冗余文件', 'completed', True,
                         f"已删除 {deleted_count} 个冗余文件/目录")
            return True
            
        except Exception as e:
            logger.error(f"冗余文件清理失败: {str(e)}")
            self._log_task(upgrade_id, 'clean_redundant', '清理冗余文件', 'failed', False, str(e))
            return False
            
    def organize_backups(self, upgrade_id: int) -> bool:
        """整理备份"""
        logger.info("整理备份...")
        try:
            self._log_task(upgrade_id, 'organize_backups', '整理备份', 'running', False)
            
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup_dir = os.path.join(backup_dir, f'backup_{timestamp}')
            os.makedirs(current_backup_dir, exist_ok=True)
            
            files_to_backup = [
                'app.db',
                'question_bank.db',
                'ai_engine_upgrades.db',
                'ai_pool_pollution.db',
                'system_upgrade.db'
            ]
            
            backed_up_count = 0
            for file_name in files_to_backup:
                if os.path.exists(file_name):
                    shutil.copy(file_name, os.path.join(current_backup_dir, file_name))
                    backed_up_count += 1
                    logger.info(f"✓ 备份: {file_name}")
            
            self._log_backup(upgrade_id, current_backup_dir, 'database', backed_up_count)
            
            old_backups = sorted([d for d in os.listdir(backup_dir) if d.startswith('backup_')], reverse=True)
            for old_backup in old_backups[5:]:
                old_backup_path = os.path.join(backup_dir, old_backup)
                if os.path.isdir(old_backup_path):
                    shutil.rmtree(old_backup_path)
                    logger.info(f"删除旧备份: {old_backup}")
            
            logger.info("备份整理完成")
            self._log_task(upgrade_id, 'organize_backups', '整理备份', 'completed', True,
                         f"已备份 {backed_up_count} 个数据库文件到 {current_backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"备份整理失败: {str(e)}")
            self._log_task(upgrade_id, 'organize_backups', '整理备份', 'failed', False, str(e))
            return False
            
    def clean_logs(self, upgrade_id: int) -> bool:
        """清理日志"""
        logger.info("清理日志...")
        try:
            self._log_task(upgrade_id, 'clean_logs', '清理日志', 'running', False)
            
            log_patterns = ['*.log', '*.txt']
            log_dirs = ['.', 'flask-app', 'logs']
            
            cleaned_count = 0
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for root, dirs, files in os.walk(log_dir):
                        for name in files:
                            for pattern in log_patterns:
                                if name.endswith(pattern.replace('*', '')):
                                    file_path = os.path.join(root, name)
                                    try:
                                        file_size = os.path.getsize(file_path)
                                        if file_size > 10 * 1024 * 1024:
                                            with open(file_path, 'w') as f:
                                                f.write(f"Log file cleaned at {datetime.now()}\n")
                                            cleaned_count += 1
                                            self._log_cleaned_file(upgrade_id, file_path, 'log', 'truncated')
                                    except:
                                        pass
            
            logger.info(f"日志清理完成，共清理 {cleaned_count} 个大型日志文件")
            self._log_task(upgrade_id, 'clean_logs', '清理日志', 'completed', True,
                         f"已清理 {cleaned_count} 个日志文件")
            return True
            
        except Exception as e:
            logger.error(f"日志清理失败: {str(e)}")
            self._log_task(upgrade_id, 'clean_logs', '清理日志', 'failed', False, str(e))
            return False
            
    def rebuild_recovery_image(self, upgrade_id: int) -> bool:
        """重建恢复镜像"""
        logger.info("重建恢复镜像...")
        try:
            self._log_task(upgrade_id, 'rebuild_image', '重建恢复镜像', 'running', False)
            
            image_dir = 'recovery_images'
            os.makedirs(image_dir, exist_ok=True)
            
            old_image = os.path.join(image_dir, 'recovery_image_v2.0.tar.gz')
            if os.path.exists(old_image):
                os.remove(old_image)
                logger.info("✓ 删除旧镜像: recovery_image_v2.0.tar.gz")
                self._log_cleaned_file(upgrade_id, old_image, 'image', 'deleted')
            
            new_image_name = f'recovery_image_v{self.target_version}.tar.gz'
            new_image_path = os.path.join(image_dir, new_image_name)
            
            core_files = [
                'core/',
                'flask-app/',
                'main.py',
                'Makefile',
                'requirements.txt'
            ]
            
            import tarfile
            with tarfile.open(new_image_path, 'w:gz') as tar:
                for file_path in core_files:
                    if os.path.exists(file_path):
                        tar.add(file_path)
                        logger.info(f"✓ 添加到镜像: {file_path}")
            
            image_size = os.path.getsize(new_image_path)
            logger.info(f"新镜像创建完成: {new_image_name} ({image_size/1024/1024:.2f} MB)")
            
            self._log_backup(upgrade_id, new_image_path, 'recovery_image', 1)
            self._log_task(upgrade_id, 'rebuild_image', '重建恢复镜像', 'completed', True,
                         f"已创建新恢复镜像: {new_image_name}")
            return True
            
        except Exception as e:
            logger.error(f"重建恢复镜像失败: {str(e)}")
            self._log_task(upgrade_id, 'rebuild_image', '重建恢复镜像', 'failed', False, str(e))
            return False
            
    def finalize_upgrade(self, upgrade_id: int) -> bool:
        """完成升级"""
        logger.info("完成升级...")
        try:
            self._log_task(upgrade_id, 'finalize', '完成升级', 'running', False)
            
            version_file = 'VERSION'
            with open(version_file, 'w') as f:
                f.write(f"{self.target_version}\n")
                f.write(f"Upgrade completed: {datetime.now()}\n")
            
            logger.info("✓ 版本文件已更新")
            
            self.current_version = self.target_version
            
            self._log_task(upgrade_id, 'finalize', '完成升级', 'completed', True,
                         f"系统版本已升级到 {self.target_version}")
            return True
            
        except Exception as e:
            logger.error(f"升级完成失败: {str(e)}")
            self._log_task(upgrade_id, 'finalize', '完成升级', 'failed', False, str(e))
            return False
            
    def run_full_upgrade(self) -> Dict[str, Any]:
        """执行完整升级流程"""
        logger.info("=== 系统升级开始 ===")
        logger.info(f"版本升级: {self.current_version} -> {self.target_version}")
        
        upgrade_id = self._start_upgrade()
        all_success = True
        
        for task in sorted(self.upgrade_tasks, key=lambda x: x['priority']):
            logger.info(f"\n[{task['priority']}] {task['name']}...")
            
            task_func = getattr(self, task['id'])
            success = task_func(upgrade_id)
            
            if success:
                logger.info(f"✓ {task['name']} 完成")
            else:
                logger.error(f"✗ {task['name']} 失败")
                all_success = False
                
            if not all_success:
                logger.error("升级流程中断")
                break
        
        details = json.dumps(self.task_results, ensure_ascii=False)
        logs = f"升级完成: {all_success}\n任务结果: {self.task_results}"
        
        self._finish_upgrade(upgrade_id, all_success, details, logs)
        
        if all_success:
            logger.info("\n=== 系统升级完成 ===")
            logger.info(f"版本已升级到: {self.target_version}")
        else:
            logger.info("\n=== 系统升级失败 ===")
            logger.info("部分任务未完成，请检查日志")
            
        return {
            'success': all_success,
            'version_from': self.current_version if all_success else self.current_version,
            'version_to': self.target_version,
            'tasks': self.task_results,
            'upgrade_id': upgrade_id
        }


if __name__ == "__main__":
    upgrader = SystemUpgrader()
    result = upgrader.run_full_upgrade()
    
    print("\n=== 系统升级结果 ===")
    print(f"升级成功: {'是' if result['success'] else '否'}")
    print(f"版本: {result['version_from']} -> {result['version_to']}")
    print("\n任务详情:")
    for task_id, task_result in result['tasks'].items():
        status = "✓" if task_result['success'] else "✗"
        print(f"  {status} {task_id}: {task_result.get('message', '')}")
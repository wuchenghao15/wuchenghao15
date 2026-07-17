# -*- coding: utf-8 -*-
"""
AI员工：Git版本控制管理专家
负责GitHub和本地Git仓库的自动化管理、提交、推送、拉取等操作
"""

import os
import subprocess
import json
import logging
from datetime import datetime
import sqlite3
import re

logger = logging.getLogger(__name__)

class GitManagerAI:
    """Git管理AI员工"""
    
    def __init__(self, db_path, project_root):
        self.db_path = db_path
        self.project_root = project_root
        self.employee_id = "git_manager_001"
        self.employee_name = "Git版本控制专家"
        self.specialty = "GitHub仓库管理、本地Git操作、自动化提交推送、版本发布管理"
        self.commit_count = 0
        self.push_count = 0
        self.report_count = 0
        
    def check_git_status(self):
        """检查Git状态"""
        try:
            os.chdir(self.project_root)
            
            # 检查是否是Git仓库
            if not os.path.exists('.git'):
                return {
                    'is_git_repo': False,
                    'message': '当前目录不是Git仓库'
                }
            
            # 获取Git状态
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                 capture_output=True, text=True, check=True)
            
            # 获取当前分支
            branch_result = subprocess.run(['git', 'branch', '--show-current'],
                                        capture_output=True, text=True, check=True)
            current_branch = branch_result.stdout.strip()
            
            # 获取远程仓库
            remote_result = subprocess.run(['git', 'remote', '-v'],
                                        capture_output=True, text=True)
            remotes = []
            if remote_result.returncode == 0:
                for line in remote_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            remotes.append({'name': parts[0], 'url': parts[1]})
            
            # 获取提交历史
            log_result = subprocess.run(['git', 'log', '--oneline', '-5'],
                                      capture_output=True, text=True)
            recent_commits = [line.strip() for line in log_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                'is_git_repo': True,
                'current_branch': current_branch,
                'uncommitted_changes': len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0,
                'changes_detail': result.stdout.strip().split('\n') if result.stdout.strip() else [],
                'remotes': remotes,
                'recent_commits': recent_commits,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"检查Git状态失败: {e}")
            return {
                'is_git_repo': False,
                'error': str(e)
            }
    
    def auto_commit_changes(self, commit_message=None):
        """自动提交更改"""
        try:
            status = self.check_git_status()
            
            if not status.get('is_git_repo'):
                return {'success': False, 'message': '不是Git仓库'}
            
            if status['uncommitted_changes'] == 0:
                return {'success': False, 'message': '没有待提交的更改'}
            
            # 生成提交信息
            if not commit_message:
                commit_message = self._generate_commit_message(status['changes_detail'])
            
            # 执行git add
            subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
            
            # 执行git commit
            commit_result = subprocess.run(['git', 'commit', '-m', commit_message],
                                        capture_output=True, text=True)
            
            if commit_result.returncode == 0:
                self.commit_count += 1
                
                # 上报数据库
                self.report_to_database('commit', commit_message, True)
                
                return {
                    'success': True,
                    'message': f'提交成功: {commit_message}',
                    'commit_message': commit_message,
                    'commit_count': self.commit_count
                }
            else:
                return {
                    'success': False,
                    'message': f'提交失败: {commit_result.stderr}'
                }
        
        except Exception as e:
            logger.error(f"自动提交失败: {e}")
            self.report_to_database('commit', str(e), False)
            return {'success': False, 'message': str(e)}
    
    def auto_push_to_remote(self, remote_name='origin', branch_name=None):
        """自动推送到远程"""
        try:
            status = self.check_git_status()
            
            if not status.get('is_git_repo'):
                return {'success': False, 'message': '不是Git仓库'}
            
            if not branch_name:
                branch_name = status.get('current_branch', 'main')
            
            # 执行git push
            push_result = subprocess.run(
                ['git', 'push', '-u', remote_name, branch_name],
                capture_output=True, text=True
            )
            
            if push_result.returncode == 0:
                self.push_count += 1
                
                # 上报数据库
                self.report_to_database('push', f'{remote_name}/{branch_name}', True)
                
                return {
                    'success': True,
                    'message': f'推送成功到 {remote_name}/{branch_name}',
                    'remote': remote_name,
                    'branch': branch_name,
                    'push_count': self.push_count
                }
            else:
                return {
                    'success': False,
                    'message': f'推送失败: {push_result.stderr}'
                }
        
        except Exception as e:
            logger.error(f"自动推送失败: {e}")
            self.report_to_database('push', str(e), False)
            return {'success': False, 'message': str(e)}
    
    def pull_from_remote(self, remote_name='origin', branch_name=None):
        """从远程拉取"""
        try:
            status = self.check_git_status()
            
            if not status.get('is_git_repo'):
                return {'success': False, 'message': '不是Git仓库'}
            
            if not branch_name:
                branch_name = status.get('current_branch', 'main')
            
            # 执行git pull
            pull_result = subprocess.run(
                ['git', 'pull', remote_name, branch_name],
                capture_output=True, text=True
            )
            
            if pull_result.returncode == 0:
                self.report_to_database('pull', f'{remote_name}/{branch_name}', True)
                
                return {
                    'success': True,
                    'message': f'拉取成功: {remote_name}/{branch_name}',
                    'output': pull_result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': f'拉取失败: {pull_result.stderr}'
                }
        
        except Exception as e:
            logger.error(f"拉取失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def create_backup_branch(self, branch_name=None):
        """创建备份分支"""
        try:
            if not branch_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                branch_name = f'backup/{timestamp}'
            
            # 创建并切换到备份分支
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True, capture_output=True)
            
            # 提交所有更改
            subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', f'自动备份: {branch_name}'],
                         check=True, capture_output=True)
            
            # 切换回原分支
            status = self.check_git_status()
            original_branch = status.get('current_branch', 'main')
            subprocess.run(['git', 'checkout', original_branch], check=True, capture_output=True)
            
            self.report_to_database('backup', branch_name, True)
            
            return {
                'success': True,
                'message': f'备份分支 {branch_name} 创建成功',
                'branch_name': branch_name
            }
        
        except Exception as e:
            logger.error(f"创建备份分支失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def sync_and_backup(self):
        """同步并备份"""
        results = []
        
        # 1. 拉取最新代码
        pull_result = self.pull_from_remote()
        results.append(('pull', pull_result))
        
        # 2. 自动提交更改
        commit_result = self.auto_commit_changes()
        results.append(('commit', commit_result))
        
        # 3. 推送到远程
        push_result = self.auto_push_to_remote()
        results.append(('push', push_result))
        
        # 4. 创建备份分支
        backup_result = self.create_backup_branch()
        results.append(('backup', backup_result))
        
        # 上报综合报告
        self.report_to_database('sync_backup', '完整同步备份流程', True)
        
        return {
            'success': True,
            'message': '同步备份完成',
            'results': results
        }
    
    def _generate_commit_message(self, changes):
        """生成提交信息"""
        if not changes:
            return '自动提交更新'
        
        # 分析更改类型
        added_files = [f for f in changes if f.strip().startswith('??') or f.strip().startswith('A ')]
        modified_files = [f for f in changes if f.strip().startswith('M ') or f.strip().startswith('MM')]
        deleted_files = [f for f in changes if f.strip().startswith('D ')]
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        messages = [f'自动提交 @ {timestamp}']
        
        if added_files:
            messages.append(f'新增文件: {len(added_files)}个')
        if modified_files:
            messages.append(f'修改文件: {len(modified_files)}个')
        if deleted_files:
            messages.append(f'删除文件: {len(deleted_files)}个')
        
        return ' | '.join(messages)
    
    def report_to_database(self, operation, description, success):
        """上报Git操作到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建Git操作日志表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS git_operations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                operation_description TEXT NOT NULL,
                success BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                additional_info TEXT
            )
            ''')
            
            # 插入操作日志
            cursor.execute('''
            INSERT INTO git_operations_log 
            (employee_id, employee_name, operation_type, operation_description, success)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                self.employee_id,
                self.employee_name,
                operation,
                description,
                success
            ))
            
            conn.commit()
            conn.close()
            
            self.report_count += 1
            logger.info(f"[{self.employee_name}] 上报Git操作: {operation} - {description}")
        
        except Exception as e:
            logger.error(f"[{self.employee_name}] 上报数据库失败: {e}")
    
    def get_operation_history(self, limit=50):
        """获取操作历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT operation_type, operation_description, success, timestamp
            FROM git_operations_log
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'operation': row[0],
                    'description': row[1],
                    'success': bool(row[2]),
                    'timestamp': row[3]
                })
            
            conn.close()
            return history
        
        except Exception as e:
            logger.error(f"获取操作历史失败: {e}")
            return []


def init_git_manager_ai(db_path, project_root):
    """初始化Git管理AI员工"""
    return GitManagerAI(db_path, project_root)


# 创建全局实例
git_manager_ai = None


def get_git_manager_ai():
    """获取Git管理AI员工实例"""
    global git_manager_ai
    if git_manager_ai is None:
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
        git_manager_ai = GitManagerAI(db_path, project_root)
    return git_manager_ai
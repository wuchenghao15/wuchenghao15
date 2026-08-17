# -*- coding: utf-8 -*-
"""
AI Agent: GitHub自动上传专家
负责自动化检测代码变更、生成提交信息、执行提交和推送到GitHub仓库
支持定时自动同步、手动触发上传、上传状态查询等功能
"""

import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
import sqlite3
import threading
import time
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

class GitHubAutoUploadAgent:
    """GitHub自动上传AI Agent"""
    
    def __init__(self, db_path, project_root):
        self.db_path = db_path
        self.project_root = project_root
        self.agent_id = "github_upload_001"
        self.agent_name = "GitHub自动上传专家"
        self.specialty = "GitHub自动化上传、代码变更检测、智能提交信息生成、定时同步"
        
        self.upload_count = 0
        self.last_upload_time = None
        self.is_uploading = False
        self.upload_history = []
        
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_upload_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                status TEXT NOT NULL,
                commit_message TEXT,
                file_count INTEGER DEFAULT 0,
                added_files INTEGER DEFAULT 0,
                modified_files INTEGER DEFAULT 0,
                deleted_files INTEGER DEFAULT 0,
                remote_name TEXT,
                branch_name TEXT,
                error_message TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL DEFAULT 0
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_upload_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    def check_git_status(self):
        """检查Git仓库状态"""
        try:
            os.chdir(self.project_root)
            
            if not os.path.exists('.git'):
                return {
                    'is_git_repo': False,
                    'message': '当前目录不是Git仓库'
                }
            
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, check=True
            )
            
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, check=True
            )
            
            remote_result = subprocess.run(
                ['git', 'remote', '-v'],
                capture_output=True, text=True
            )
            
            remotes = []
            if remote_result.returncode == 0:
                for line in remote_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            remotes.append({'name': parts[0], 'url': parts[1]})
            
            changes = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
            
            added_files = [f for f in changes if f.strip().startswith('??') or f.strip().startswith('A ')]
            modified_files = [f for f in changes if f.strip().startswith('M ') or f.strip().startswith('MM')]
            deleted_files = [f for f in changes if f.strip().startswith('D ')]
            
            return {
                'is_git_repo': True,
                'current_branch': branch_result.stdout.strip(),
                'has_changes': len(changes) > 0,
                'total_files': len(changes),
                'added_files': len(added_files),
                'modified_files': len(modified_files),
                'deleted_files': len(deleted_files),
                'changes_detail': changes,
                'remotes': remotes,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"检查Git状态失败: {e}")
            return {'is_git_repo': False, 'error': str(e)}
    
    def generate_commit_message(self, changes):
        """智能生成提交信息"""
        if not changes:
            return '自动同步: 无变更'
        
        added_files = [f for f in changes if f.strip().startswith('??') or f.strip().startswith('A ')]
        modified_files = [f for f in changes if f.strip().startswith('M ') or f.strip().startswith('MM')]
        deleted_files = [f for f in changes if f.strip().startswith('D ')]
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message_parts = [f'🤖 自动同步 @ {timestamp}']
        
        if modified_files:
            module_names = set()
            for f in modified_files:
                file_path = f[3:].strip() if f.startswith('M ') else f[4:].strip()
                if file_path:
                    parts = file_path.split('/')
                    if len(parts) >= 2:
                        module_names.add(parts[0])
            if module_names:
                message_parts.append(f'模块: {", ".join(list(module_names)[:5])}')
        
        if added_files:
            message_parts.append(f'新增 {len(added_files)} 个文件')
        if modified_files:
            message_parts.append(f'修改 {len(modified_files)} 个文件')
        if deleted_files:
            message_parts.append(f'删除 {len(deleted_files)} 个文件')
        
        return ' | '.join(message_parts)
    
    def execute_upload(self, commit_message=None, remote_name='origin', branch_name=None):
        """执行完整上传流程"""
        if self.is_uploading:
            return {
                'success': False,
                'message': '正在上传中，请稍后再试'
            }
        
        self.is_uploading = True
        start_time = datetime.now()
        
        log_entry = {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'operation_type': 'upload',
            'status': 'running',
            'start_time': start_time.isoformat(),
            'remote_name': remote_name,
            'branch_name': branch_name
        }
        
        try:
            status = self.check_git_status()
            
            if not status.get('is_git_repo'):
                log_entry['status'] = 'failed'
                log_entry['error_message'] = '不是Git仓库'
                self._save_log_entry(log_entry)
                self.is_uploading = False
                return {'success': False, 'message': '不是Git仓库'}
            
            if not status['has_changes']:
                log_entry['status'] = 'completed'
                log_entry['commit_message'] = '无变更'
                self._save_log_entry(log_entry)
                self.is_uploading = False
                return {'success': True, 'message': '没有待上传的更改'}
            
            if not branch_name:
                branch_name = status['current_branch']
            
            if not commit_message:
                commit_message = self.generate_commit_message(status['changes_detail'])
            
            log_entry['commit_message'] = commit_message
            log_entry['file_count'] = status['total_files']
            log_entry['added_files'] = status['added_files']
            log_entry['modified_files'] = status['modified_files']
            log_entry['deleted_files'] = status['deleted_files']
            log_entry['branch_name'] = branch_name
            
            os.chdir(self.project_root)
            
            subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
            
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True, text=True
            )
            
            if commit_result.returncode != 0:
                error_msg = commit_result.stderr.strip()
                log_entry['status'] = 'failed'
                log_entry['error_message'] = error_msg
                self._save_log_entry(log_entry)
                self.is_uploading = False
                return {'success': False, 'message': f'提交失败: {error_msg}'}
            
            push_result = subprocess.run(
                ['git', 'push', '-u', remote_name, branch_name],
                capture_output=True, text=True
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if push_result.returncode == 0:
                self.upload_count += 1
                self.last_upload_time = end_time
                
                log_entry['status'] = 'completed'
                log_entry['end_time'] = end_time.isoformat()
                log_entry['duration_seconds'] = duration
                self._save_log_entry(log_entry)
                
                self.is_uploading = False
                
                return {
                    'success': True,
                    'message': f'上传成功！推送到 {remote_name}/{branch_name}',
                    'commit_message': commit_message,
                    'files': {
                        'total': status['total_files'],
                        'added': status['added_files'],
                        'modified': status['modified_files'],
                        'deleted': status['deleted_files']
                    },
                    'remote': remote_name,
                    'branch': branch_name,
                    'upload_count': self.upload_count,
                    'duration_seconds': round(duration, 2),
                    'timestamp': end_time.isoformat()
                }
            else:
                error_msg = push_result.stderr.strip()
                log_entry['status'] = 'failed'
                log_entry['error_message'] = error_msg
                log_entry['end_time'] = end_time.isoformat()
                log_entry['duration_seconds'] = duration
                self._save_log_entry(log_entry)
                
                self.is_uploading = False
                return {'success': False, 'message': f'推送失败: {error_msg}'}
        
        except Exception as e:
            end_time = datetime.now()
            log_entry['status'] = 'failed'
            log_entry['error_message'] = str(e)
            log_entry['end_time'] = end_time.isoformat()
            self._save_log_entry(log_entry)
            
            self.is_uploading = False
            logger.error(f"上传失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _save_log_entry(self, entry):
        """保存上传日志到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO github_upload_log 
            (agent_id, agent_name, operation_type, status, commit_message, 
             file_count, added_files, modified_files, deleted_files,
             remote_name, branch_name, error_message, start_time, end_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.get('agent_id'),
                entry.get('agent_name'),
                entry.get('operation_type'),
                entry.get('status'),
                entry.get('commit_message'),
                entry.get('file_count'),
                entry.get('added_files'),
                entry.get('modified_files'),
                entry.get('deleted_files'),
                entry.get('remote_name'),
                entry.get('branch_name'),
                entry.get('error_message'),
                entry.get('start_time'),
                entry.get('end_time'),
                entry.get('duration_seconds')
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存日志失败: {e}")
    
    def get_upload_history(self, limit=20):
        """获取上传历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, commit_message, status, file_count, added_files, 
                   modified_files, deleted_files, remote_name, branch_name,
                   error_message, start_time, end_time, duration_seconds
            FROM github_upload_log
            ORDER BY id DESC
            LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'commit_message': row[1],
                    'status': row[2],
                    'files': {
                        'total': row[3],
                        'added': row[4],
                        'modified': row[5],
                        'deleted': row[6]
                    },
                    'remote': row[7],
                    'branch': row[8],
                    'error_message': row[9],
                    'start_time': row[10],
                    'end_time': row[11],
                    'duration_seconds': row[12]
                })
            
            conn.close()
            return history
        
        except Exception as e:
            logger.error(f"获取上传历史失败: {e}")
            return []
    
    def get_status(self):
        """获取当前状态"""
        status = self.check_git_status()
        
        return {
            'agent_name': self.agent_name,
            'agent_id': self.agent_id,
            'is_uploading': self.is_uploading,
            'upload_count': self.upload_count,
            'last_upload_time': self.last_upload_time.isoformat() if self.last_upload_time else None,
            'git_status': status,
            'timestamp': datetime.now().isoformat()
        }
    
    def scheduled_upload(self, interval_minutes=60):
        """定时自动上传"""
        def scheduler():
            while True:
                try:
                    logger.info(f"[{self.agent_name}] 定时检查...")
                    status = self.check_git_status()
                    
                    if status.get('is_git_repo') and status.get('has_changes'):
                        logger.info(f"[{self.agent_name}] 检测到变更，开始自动上传...")
                        result = self.execute_upload()
                        if result['success']:
                            logger.info(f"[{self.agent_name}] 定时上传成功")
                        else:
                            logger.error(f"[{self.agent_name}] 定时上传失败: {result['message']}")
                    else:
                        logger.info(f"[{self.agent_name}] 无变更，跳过上传")
                except Exception as e:
                    logger.error(f"[{self.agent_name}] 定时任务异常: {e}")
                
                time.sleep(interval_minutes * 60)
        
        thread = threading.Thread(target=scheduler, daemon=True)
        thread.start()
        logger.info(f"[{self.agent_name}] 定时上传任务已启动，间隔 {interval_minutes} 分钟")


github_upload_agent = None

def get_github_upload_agent():
    """获取GitHub自动上传Agent实例"""
    global github_upload_agent
    if github_upload_agent is None:
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
        github_upload_agent = GitHubAutoUploadAgent(db_path, project_root)
    return github_upload_agent


github_upload_bp = Blueprint('github_upload', __name__)

@github_upload_bp.route('/api/github/upload/status', methods=['GET'])
def api_get_status():
    """获取上传Agent状态"""
    agent = get_github_upload_agent()
    return jsonify(agent.get_status())

@github_upload_bp.route('/api/github/upload/history', methods=['GET'])
def api_get_history():
    """获取上传历史"""
    agent = get_github_upload_agent()
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'success': True,
        'history': agent.get_upload_history(limit)
    })

@github_upload_bp.route('/api/github/upload/execute', methods=['POST'])
def api_execute_upload():
    """手动触发上传"""
    agent = get_github_upload_agent()
    
    data = request.get_json() or {}
    commit_message = data.get('commit_message')
    remote_name = data.get('remote_name', 'origin')
    branch_name = data.get('branch_name')
    
    result = agent.execute_upload(commit_message, remote_name, branch_name)
    return jsonify(result)

@github_upload_bp.route('/api/github/upload/git-status', methods=['GET'])
def api_check_git_status():
    """检查Git状态"""
    agent = get_github_upload_agent()
    return jsonify(agent.check_git_status())

@github_upload_bp.route('/api/github/upload/count', methods=['GET'])
def api_get_upload_count():
    """获取上传次数"""
    agent = get_github_upload_agent()
    return jsonify({
        'success': True,
        'upload_count': agent.upload_count,
        'last_upload_time': agent.last_upload_time.isoformat() if agent.last_upload_time else None
    })

@github_upload_bp.route('/api/github/upload/start-scheduler', methods=['POST'])
def api_start_scheduler():
    """启动定时上传任务"""
    agent = get_github_upload_agent()
    
    data = request.get_json() or {}
    interval = data.get('interval_minutes', 60)
    
    try:
        agent.scheduled_upload(interval)
        return jsonify({
            'success': True,
            'message': f'定时上传任务已启动，间隔 {interval} 分钟'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def init_github_upload_agent(app):
    """初始化GitHub上传Agent并注册蓝图"""
    global github_upload_agent
    
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
    
    github_upload_agent = GitHubAutoUploadAgent(db_path, project_root)
    
    app.register_blueprint(github_upload_bp, url_prefix='')
    
    logger.info(f"[{github_upload_agent.agent_name}] 已初始化并注册到Flask应用")
    
    return github_upload_agent
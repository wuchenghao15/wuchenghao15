# -*- coding: utf-8 -*-
"""
Git源码自动操作模块 - 安全护栏、分支操作、代码修改
支持：自动拉取、精准修改、配置调整、安全推送
"""
import os
import json
import logging
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GitAutoOps:
    """Git自动操作模块"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self._repo_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._default_branch = 'main'
        self._protected_branches = ['main', 'master', 'develop']
        self._max_file_changes = 100
        self._max_line_changes = 1000
        self._approval_required_changes = 50
        
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        
        self._init_database()
        
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS git_operations (
                    op_id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    commit_hash TEXT DEFAULT '',
                    commit_message TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending',
                    changes TEXT DEFAULT '{}',
                    approval_id TEXT DEFAULT '',
                    created_at TEXT,
                    executed_at TEXT,
                    error_message TEXT DEFAULT ''
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS git_diff_history (
                    diff_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    op_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    old_content TEXT DEFAULT '',
                    new_content TEXT DEFAULT '',
                    diff TEXT DEFAULT '',
                    FOREIGN KEY (op_id) REFERENCES git_operations (op_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[Git操作] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[Git操作] 初始化数据库失败: {e}")
    
    def _run_git_cmd(self, cmd: List[str], cwd: str = None) -> str:
        """运行Git命令"""
        try:
            result = subprocess.run(
                ['git'] + cmd,
                cwd=cwd or self._repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0 and result.stderr:
                logger.warning(f"[Git操作] 命令失败: {' '.join(cmd)} - {result.stderr.strip()}")
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"[Git操作] 运行命令失败: {' '.join(cmd)} - {e}")
            return ''
    
    def _get_current_branch(self) -> str:
        """获取当前分支"""
        return self._run_git_cmd(['branch', '--show-current'])
    
    def _stash_changes(self) -> str:
        """暂存当前更改"""
        return self._run_git_cmd(['stash'])
    
    def _restore_stash(self):
        """恢复暂存的更改"""
        self._run_git_cmd(['stash', 'pop'])
    
    def pull_branch(self, branch: str = None) -> Dict:
        """拉取指定分支"""
        branch = branch or self._default_branch
        
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_pull"
        
        result = {
            'op_id': op_id,
            'operation_type': 'pull',
            'branch': branch,
            'status': 'running',
            'changes': {}
        }
        
        self._save_operation(result)
        
        try:
            current_branch = self._get_current_branch()
            if current_branch != branch:
                self._run_git_cmd(['checkout', branch])
            
            output = self._run_git_cmd(['pull', 'origin', branch])
            
            result['status'] = 'completed'
            result['changes'] = {'output': output}
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            logger.info(f"[Git操作] 拉取分支成功: {branch}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 拉取分支失败: {branch} - {e}")
        
        return result
    
    def create_branch(self, branch_name: str, base_branch: str = None) -> Dict:
        """创建新分支"""
        base_branch = base_branch or self._default_branch
        
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_create"
        
        result = {
            'op_id': op_id,
            'operation_type': 'create_branch',
            'branch': branch_name,
            'status': 'running',
            'changes': {'base_branch': base_branch}
        }
        
        self._save_operation(result)
        
        try:
            self._run_git_cmd(['checkout', base_branch])
            self._run_git_cmd(['pull', 'origin', base_branch])
            self._run_git_cmd(['checkout', '-b', branch_name])
            
            result['status'] = 'completed'
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            logger.info(f"[Git操作] 创建分支成功: {branch_name}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 创建分支失败: {branch_name} - {e}")
        
        return result
    
    def modify_file(self, file_path: str, changes: Dict) -> Dict:
        """精准修改文件"""
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_modify"
        
        result = {
            'op_id': op_id,
            'operation_type': 'modify_file',
            'branch': self._get_current_branch(),
            'status': 'running',
            'changes': {'file_path': file_path, 'changes': changes}
        }
        
        self._save_operation(result)
        
        try:
            full_path = os.path.join(self._repo_path, file_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            with open(full_path, 'r') as f:
                old_content = f.read()
            
            new_content = old_content
            
            for change in changes.get('replace', []):
                old_str = change.get('old', '')
                new_str = change.get('new', '')
                if old_str in new_content:
                    new_content = new_content.replace(old_str, new_str)
            
            for change in changes.get('append', []):
                position = change.get('position', 'end')
                content = change.get('content', '')
                if position == 'end':
                    new_content += content
                elif position == 'beginning':
                    new_content = content + new_content
            
            for change in changes.get('insert', []):
                line_number = change.get('line', 0)
                content = change.get('content', '')
                lines = new_content.split('\n')
                if 0 < line_number <= len(lines):
                    lines.insert(line_number - 1, content)
                    new_content = '\n'.join(lines)
            
            diff = self._generate_diff(old_content, new_content)
            
            self._save_diff(op_id, file_path, old_content, new_content, diff)
            
            with open(full_path, 'w') as f:
                f.write(new_content)
            
            result['status'] = 'completed'
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            logger.info(f"[Git操作] 修改文件成功: {file_path}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 修改文件失败: {file_path} - {e}")
        
        return result
    
    def _generate_diff(self, old_content: str, new_content: str) -> str:
        """生成差异对比"""
        import difflib
        
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
        return '\n'.join(diff)
    
    def modify_config(self, config_path: str, updates: Dict) -> Dict:
        """修改配置文件"""
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_config"
        
        result = {
            'op_id': op_id,
            'operation_type': 'modify_config',
            'branch': self._get_current_branch(),
            'status': 'running',
            'changes': {'config_path': config_path, 'updates': updates}
        }
        
        self._save_operation(result)
        
        try:
            full_path = os.path.join(self._repo_path, config_path)
            
            if config_path.endswith('.json'):
                with open(full_path, 'r') as f:
                    config = json.load(f)
                
                self._deep_update(config, updates)
                
                with open(full_path, 'w') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            elif config_path.endswith('.py'):
                with open(full_path, 'r') as f:
                    content = f.read()
                
                for key, value in updates.items():
                    old_pattern = rf"{key}\s*=\s*[^\n]*"
                    if isinstance(value, str):
                        new_pattern = f"{key} = '{value}'"
                    else:
                        new_pattern = f"{key} = {value}"
                    
                    import re
                    content = re.sub(old_pattern, new_pattern, content)
                
                with open(full_path, 'w') as f:
                    f.write(content)
            
            else:
                with open(full_path, 'r') as f:
                    content = f.read()
                
                for key, value in updates.items():
                    content = content.replace(f"${{{key}}}", str(value))
                
                with open(full_path, 'w') as f:
                    f.write(content)
            
            result['status'] = 'completed'
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            logger.info(f"[Git操作] 修改配置成功: {config_path}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 修改配置失败: {config_path} - {e}")
        
        return result
    
    def _deep_update(self, config: Dict, updates: Dict):
        """深度更新配置"""
        for key, value in updates.items():
            if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                self._deep_update(config[key], value)
            else:
                config[key] = value
    
    def commit_changes(self, message: str) -> Dict:
        """提交更改"""
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_commit"
        
        result = {
            'op_id': op_id,
            'operation_type': 'commit',
            'branch': self._get_current_branch(),
            'commit_message': message,
            'status': 'running',
            'changes': {}
        }
        
        self._save_operation(result)
        
        try:
            self._run_git_cmd(['add', '.'])
            
            diff_output = self._run_git_cmd(['diff', '--cached', '--stat'])
            result['changes'] = {'diff': diff_output}
            
            file_count = len([line for line in diff_output.split('\n') if line.strip()])
            if file_count == 0:
                result['status'] = 'skipped'
                result['executed_at'] = datetime.now().isoformat()
                self._save_operation(result)
                logger.info("[Git操作] 没有更改需要提交")
                return result
            
            if file_count >= self._approval_required_changes:
                from app.agents.approval_manager import get_approval_manager, OperationLevel
                
                approval_manager = get_approval_manager()
                approval_id = approval_manager.create_approval(
                    'git_commit',
                    OperationLevel.CRITICAL.value,
                    f"大规模提交: {file_count}个文件",
                    {'file_count': file_count, 'diff': diff_output}
                )
                
                result['approval_id'] = approval_id
                result['status'] = 'pending_approval'
                self._save_operation(result)
                logger.warning(f"[Git操作] 需要审批: {file_count}个文件变更")
                return result
            
            commit_output = self._run_git_cmd(['commit', '-m', message])
            
            commit_hash = ''
            for line in commit_output.split('\n'):
                if 'commit' in line.lower():
                    parts = line.split()
                    for part in parts:
                        if len(part) == 40:
                            commit_hash = part
                            break
            
            result['commit_hash'] = commit_hash
            result['status'] = 'completed'
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            logger.info(f"[Git操作] 提交成功: {commit_hash}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 提交失败: {e}")
        
        return result
    
    def push_branch(self, branch: str = None, force: bool = False) -> Dict:
        """推送分支"""
        branch = branch or self._get_current_branch()
        
        if force and branch in self._protected_branches:
            return {
                'status': 'rejected',
                'error_message': f"禁止强制推送到保护分支: {branch}"
            }
        
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_push"
        
        result = {
            'op_id': op_id,
            'operation_type': 'push',
            'branch': branch,
            'status': 'running',
            'changes': {'force': force}
        }
        
        self._save_operation(result)
        
        try:
            if force:
                output = self._run_git_cmd(['push', '--force', 'origin', branch])
            else:
                output = self._run_git_cmd(['push', '-u', 'origin', branch])
            
            result['changes']['output'] = output
            result['status'] = 'completed'
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            logger.info(f"[Git操作] 推送分支成功: {branch}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 推送分支失败: {branch} - {e}")
        
        return result
    
    def create_pull_request(self, head_branch: str, base_branch: str = None, 
                           title: str = '', body: str = '') -> Dict:
        """创建Pull Request"""
        base_branch = base_branch or self._default_branch
        
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_pr"
        
        result = {
            'op_id': op_id,
            'operation_type': 'create_pr',
            'branch': head_branch,
            'status': 'running',
            'changes': {'base_branch': base_branch, 'title': title}
        }
        
        self._save_operation(result)
        
        try:
            try:
                from app.agents.github_integration import get_github_integration
                
                github = get_github_integration()
                if github:
                    pr = github.create_pull_request(base_branch, head_branch, title, body)
                    result['changes']['pr_url'] = pr.get('html_url', '')
                    logger.info(f"[Git操作] 创建PR成功: {pr.get('html_url', '')}")
                else:
                    logger.info("[Git操作] GitHub集成未配置，仅创建分支")
            except ImportError:
                logger.info("[Git操作] GitHub集成模块未找到，仅创建分支")
            
            result['status'] = 'completed'
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 创建PR失败: {e}")
        
        return result
    
    def merge_branch(self, source_branch: str, target_branch: str = None) -> Dict:
        """合并分支"""
        target_branch = target_branch or self._default_branch
        
        if target_branch in self._protected_branches:
            from app.agents.approval_manager import get_approval_manager, OperationLevel
            
            approval_manager = get_approval_manager()
            approval_id = approval_manager.create_approval(
                'git_merge',
                OperationLevel.CRITICAL.value,
                f"合并到保护分支: {source_branch} -> {target_branch}"
            )
            
            return {
                'status': 'pending_approval',
                'approval_id': approval_id,
                'message': f"需要审批才能合并到保护分支: {target_branch}"
            }
        
        op_id = f"git_{datetime.now().strftime('%Y%m%d_%H%M%S')}_merge"
        
        result = {
            'op_id': op_id,
            'operation_type': 'merge',
            'branch': target_branch,
            'status': 'running',
            'changes': {'source_branch': source_branch}
        }
        
        self._save_operation(result)
        
        try:
            self._run_git_cmd(['checkout', target_branch])
            self._run_git_cmd(['pull', 'origin', target_branch])
            
            merge_output = self._run_git_cmd(['merge', source_branch, '--no-ff', '-m', f"Merge {source_branch} into {target_branch}"])
            
            if 'CONFLICT' in merge_output:
                result['status'] = 'conflict'
                result['error_message'] = '合并冲突，需要手动解决'
            else:
                self._run_git_cmd(['push', 'origin', target_branch])
                result['status'] = 'completed'
            
            result['changes']['output'] = merge_output
            result['executed_at'] = datetime.now().isoformat()
            
            self._save_operation(result)
            
        except Exception as e:
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['executed_at'] = datetime.now().isoformat()
            self._save_operation(result)
            logger.error(f"[Git操作] 合并分支失败: {e}")
        
        return result
    
    def _save_operation(self, operation: Dict):
        """保存操作记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO git_operations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                operation['op_id'],
                operation['operation_type'],
                operation['branch'],
                operation.get('commit_hash', ''),
                operation.get('commit_message', ''),
                operation.get('status', 'pending'),
                json.dumps(operation.get('changes', {})),
                operation.get('approval_id', ''),
                operation.get('created_at', datetime.now().isoformat()),
                operation.get('executed_at'),
                operation.get('error_message', '')
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[Git操作] 保存操作记录失败: {e}")
    
    def _save_diff(self, op_id: str, file_path: str, old_content: str, new_content: str, diff: str):
        """保存差异记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO git_diff_history (op_id, file_path, old_content, new_content, diff)
                VALUES (?, ?, ?, ?, ?)
            ''', (op_id, file_path, old_content, new_content, diff))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[Git操作] 保存差异记录失败: {e}")
    
    def get_operation(self, op_id: str) -> Optional[Dict]:
        """获取操作记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM git_operations WHERE op_id = ?', (op_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'op_id': row[0],
                    'operation_type': row[1],
                    'branch': row[2],
                    'commit_hash': row[3],
                    'commit_message': row[4],
                    'status': row[5],
                    'changes': json.loads(row[6]) if row[6] else {},
                    'approval_id': row[7],
                    'created_at': row[8],
                    'executed_at': row[9],
                    'error_message': row[10]
                }
            
            return None
        except Exception as e:
            logger.error(f"[Git操作] 获取操作记录失败: {e}")
            return None
    
    def get_all_operations(self) -> List[Dict]:
        """获取所有操作记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM git_operations ORDER BY created_at DESC LIMIT 20')
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'op_id': row[0],
                    'operation_type': row[1],
                    'branch': row[2],
                    'commit_hash': row[3],
                    'commit_message': row[4],
                    'status': row[5],
                    'changes': json.loads(row[6]) if row[6] else {},
                    'approval_id': row[7],
                    'created_at': row[8],
                    'executed_at': row[9],
                    'error_message': row[10]
                })
            
            conn.close()
            return results
        
        except Exception as e:
            logger.error(f"[Git操作] 获取操作记录失败: {e}")
            return []


def get_git_auto_ops() -> GitAutoOps:
    """获取Git自动操作模块单例"""
    return GitAutoOps()


def init_git_ops():
    """初始化Git操作模块"""
    ops = get_git_auto_ops()
    logger.info("[Git操作] Git源码自动操作模块初始化完成")
    return ops


def init_git_auto_ops():
    """初始化Git自动操作模块"""
    ops = get_git_auto_ops()
    logger.info("[Git操作] Git源码自动操作模块初始化完成")
    return ops
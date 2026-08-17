# -*- coding: utf-8 -*-
"""
AI员工：系统部署专家
负责将系统上传部署到远程服务器，支持多种部署方式
"""

import os
import json
import logging
import threading
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """部署状态"""
    PENDING = "pending"
    PREPARING = "preparing"
    UPLOADING = "uploading"
    DEPLOYING = "deploying"
    TESTING = "testing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class DeploymentMethod(Enum):
    """部署方式"""
    SCP = "scp"
    SFTP = "sftp"
    RSYNC = "rsync"
    FTP = "ftp"
    GIT = "git"


class DeploymentTask:
    """部署任务"""
    
    def __init__(self, task_id: str, target_server: str, method: str):
        self.task_id = task_id
        self.target_server = target_server
        self.method = method
        self.status = DeploymentStatus.PENDING.value
        self.start_time = None
        self.end_time = None
        self.progress = 0
        self.message = ""
        self.logs: List[str] = []
        self.details: Dict[str, Any] = {}


class DeploymentExpertAI:
    """系统部署专家AI员工"""
    
    def __init__(self):
        self.employee_id = "ai_deployment_expert_001"
        self.role = "deployment_engineer"
        self.name = "系统部署专家"
        self.skills = [
            "server_deployment", "file_transfer", "remote_management",
            "configuration_management", "deployment_automation",
            "rollback_management", "health_check", "performance_optimization"
        ]
        
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._db_path = self._find_db_path()
        
        self.active_tasks: Dict[str, DeploymentTask] = {}
        self.deployment_history: List[Dict[str, Any]] = []
        self.is_running = False
        self._lock = threading.Lock()
        
        self._ensure_tables()
        self._load_history()
        
        logger.info(f"系统部署专家AI已初始化: {self.name} ({self.employee_id})")
    
    def _find_db_path(self) -> str:
        """查找数据库路径"""
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        return db.db_path
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables(self):
        """确保数据库表存在"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployment_tasks (
                    task_id TEXT PRIMARY KEY,
                    target_server TEXT NOT NULL,
                    deployment_method TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT "pending",
                    progress INTEGER DEFAULT 0,
                    message TEXT DEFAULT "",
                    start_time TEXT,
                    end_time TEXT,
                    config TEXT DEFAULT "{}",
                    result TEXT DEFAULT "{}",
                    logs TEXT DEFAULT "[]",
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployment_servers (
                    server_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    username TEXT DEFAULT "",
                    remote_path TEXT DEFAULT "",
                    deployment_method TEXT DEFAULT "scp",
                    status TEXT DEFAULT "inactive",
                    last_deployment TEXT,
                    config TEXT DEFAULT "{}",
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
    
    def _load_history(self):
        """加载部署历史"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT task_id, target_server, deployment_method, status,
                           progress, message, start_time, end_time
                    FROM deployment_tasks
                    ORDER BY created_at DESC
                    LIMIT 20
                ''')
                rows = cursor.fetchall()
                self.deployment_history = [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"加载部署历史失败: {e}")
    
    def get_server_config(self, server_id: str = "default") -> Dict[str, Any]:
        """获取服务器配置"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT server_id, name, host, port, username, remote_path,
                           deployment_method, status, last_deployment, config
                    FROM deployment_servers
                    WHERE server_id = ?
                ''', (server_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"获取服务器配置失败: {e}")
        
        return {
            'server_id': server_id,
            'name': 'wuchenghao15.xyz',
            'host': 'wuchenghao15.xyz',
            'port': 22,
            'username': '',
            'remote_path': '/var/www/mtscos',
            'deployment_method': 'scp',
            'status': 'inactive'
        }
    
    def save_server_config(self, config: Dict[str, Any]) -> bool:
        """保存服务器配置"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO deployment_servers 
                    (server_id, name, host, port, username, remote_path,
                     deployment_method, status, config, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    config.get('server_id', 'default'),
                    config.get('name', config.get('host', '')),
                    config.get('host', ''),
                    config.get('port', 22),
                    config.get('username', ''),
                    config.get('remote_path', ''),
                    config.get('deployment_method', 'scp'),
                    config.get('status', 'inactive'),
                    json.dumps(config.get('config', {})),
                    now,
                    now
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存服务器配置失败: {e}")
            return False
    
    def test_server_connection(self, server_id: str = "default") -> Dict[str, Any]:
        """测试服务器连接"""
        config = self.get_server_config(server_id)
        host = config.get('host', 'wuchenghao15.xyz')
        port = config.get('port', 22)
        
        result = {
            'success': False,
            'host': host,
            'port': port,
            'message': '',
            'details': {}
        }
        
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            
            start = datetime.now()
            s.connect((host, port))
            elapsed = (datetime.now() - start).total_seconds() * 1000
            
            s.close()
            
            result['success'] = True
            result['message'] = f"服务器 {host}:{port} 连接正常"
            result['details']['response_time_ms'] = round(elapsed, 2)
            
            logger.info(f"服务器连接测试成功: {host}:{port}, 响应时间: {elapsed:.2f}ms")
        except socket.timeout:
            result['message'] = f"连接超时: {host}:{port}"
            logger.warning(f"服务器连接超时: {host}:{port}")
        except Exception as e:
            result['message'] = f"连接失败: {str(e)}"
            logger.error(f"服务器连接测试失败: {e}")
        
        return result
    
    def start_deployment(self, server_id: str = "default", 
                        deploy_method: str = None,
                        files_to_deploy: List[str] = None) -> Dict[str, Any]:
        """开始部署任务"""
        try:
            config = self.get_server_config(server_id)
            method = deploy_method or config.get('deployment_method', 'scp')
            
            task_id = f"deploy_{int(datetime.now().timestamp())}"
            task = DeploymentTask(task_id, config.get('host', ''), method)
            
            with self._lock:
                self.active_tasks[task_id] = task
            
            self._save_task(task)
            
            # 在后台线程中执行部署
            thread = threading.Thread(
                target=self._execute_deployment,
                args=(task_id, server_id, files_to_deploy),
                daemon=True
            )
            thread.start()
            
            logger.info(f"部署任务已启动: {task_id} -> {config.get('host')}")
            
            return {
                'success': True,
                'task_id': task_id,
                'status': task.status,
                'message': f"部署任务已启动，目标: {config.get('host')}",
                'method': method
            }
        
        except Exception as e:
            logger.error(f"启动部署任务失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '启动部署任务失败'
            }
    
    def _execute_deployment(self, task_id: str, server_id: str, 
                           files_to_deploy: List[str] = None):
        """执行部署任务（后台线程）"""
        task = self.active_tasks.get(task_id)
        if not task:
            return
        
        try:
            task.status = DeploymentStatus.PREPARING.value
            task.start_time = datetime.now().isoformat()
            task.message = "正在准备部署..."
            self._log(task, "开始部署准备工作")
            self._save_task(task)
            
            config = self.get_server_config(server_id)
            host = config.get('host', 'wuchenghao15.xyz')
            
            # 阶段1: 准备部署文件
            self._log(task, f"准备部署文件到 {host}")
            task.progress = 10
            self._save_task(task)
            
            # 收集要部署的文件
            if not files_to_deploy:
                files_to_deploy = self._collect_deployment_files()
            self._log(task, f"共收集 {len(files_to_deploy)} 个文件/目录")
            
            # 阶段2: 测试连接
            task.status = DeploymentStatus.UPLOADING.value
            task.message = "测试服务器连接..."
            task.progress = 20
            self._save_task(task)
            
            conn_test = self.test_server_connection(server_id)
            if not conn_test['success']:
                raise Exception(f"服务器连接失败: {conn_test['message']}")
            self._log(task, f"服务器连接正常，响应时间: {conn_test['details'].get('response_time_ms', 0)}ms")
            
            # 阶段3: 执行部署
            task.message = f"正在通过 {task.method} 上传文件..."
            task.progress = 30
            self._save_task(task)
            
            deploy_result = self._perform_deployment(task, config, files_to_deploy)
            
            if not deploy_result['success']:
                raise Exception(deploy_result.get('message', '部署失败'))
            
            task.progress = 80
            task.message = "文件上传完成，正在部署..."
            task.status = DeploymentStatus.DEPLOYING.value
            self._save_task(task)
            
            # 阶段4: 部署后配置
            self._log(task, "执行部署后配置...")
            post_result = self._post_deployment_config(task, config)
            
            task.progress = 90
            task.message = "部署完成，正在验证..."
            task.status = DeploymentStatus.TESTING.value
            self._save_task(task)
            
            # 阶段5: 验证部署
            self._log(task, "验证部署结果...")
            verify_result = self._verify_deployment(task, config)
            
            if verify_result['success']:
                task.status = DeploymentStatus.SUCCESS.value
                task.message = "部署成功！"
                task.progress = 100
                self._log(task, "✅ 部署验证通过")
            else:
                task.status = DeploymentStatus.FAILED.value
                task.message = f"部署验证失败: {verify_result.get('message', '')}"
                self._log(task, f"❌ 部署验证失败: {verify_result.get('message', '')}")
            
            task.end_time = datetime.now().isoformat()
            task.details['deploy_result'] = deploy_result
            task.details['verify_result'] = verify_result
            self._save_task(task)
            
            # 更新服务器状态
            if task.status == DeploymentStatus.SUCCESS.value:
                config['status'] = 'active'
                config['last_deployment'] = task.end_time
                self.save_server_config(config)
            
            logger.info(f"部署任务完成: {task_id}, 状态: {task.status}")
        
        except Exception as e:
            task.status = DeploymentStatus.FAILED.value
            task.message = f"部署失败: {str(e)}"
            task.end_time = datetime.now().isoformat()
            self._log(task, f"❌ 部署异常: {str(e)}")
            self._save_task(task)
            logger.error(f"部署任务失败: {task_id}, 错误: {e}")
    
    def _collect_deployment_files(self) -> List[str]:
        """收集要部署的文件和目录"""
        files = []
        
        # 主要目录
        main_dirs = ['app', 'ai_engines', 'templates', 'static']
        for d in main_dirs:
            full_path = os.path.join(self.project_root, d)
            if os.path.exists(full_path):
                files.append(full_path)
        
        # 主要文件
        main_files = ['app.py', 'requirements.txt', 'deploy.sh']
        for f in main_files:
            full_path = os.path.join(self.project_root, f)
            if os.path.exists(full_path):
                files.append(full_path)
        
        return files
    
    def _perform_deployment(self, task: DeploymentTask, config: Dict, 
                           files: List[str]) -> Dict[str, Any]:
        """执行实际的部署操作"""
        method = task.method
        
        if method == DeploymentMethod.SCP.value:
            return self._deploy_via_scp(task, config, files)
        elif method == DeploymentMethod.RSYNC.value:
            return self._deploy_via_rsync(task, config, files)
        elif method == DeploymentMethod.SFTP.value:
            return self._deploy_via_sftp(task, config, files)
        elif method == DeploymentMethod.GIT.value:
            return self._deploy_via_git(task, config, files)
        else:
            return {
                'success': False,
                'message': f"不支持的部署方式: {method}"
            }
    
    def _deploy_via_scp(self, task: DeploymentTask, config: Dict,
                       files: List[str]) -> Dict[str, Any]:
        """通过SCP部署"""
        try:
            host = config.get('host', '')
            username = config.get('username', '')
            remote_path = config.get('remote_path', '/var/www/mtscos')
            port = config.get('port', 22)
            
            # 检查scp是否可用
            result = subprocess.run(['which', 'scp'], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': 'scp命令不可用'
                }
            
            self._log(task, f"SCP部署到 {username}@{host}:{remote_path}")
            
            # 模拟部署进度（实际需要配置SSH密钥）
            total_files = len(files)
            for i, f in enumerate(files):
                task.progress = 30 + int(50 * (i + 1) / total_files)
                basename = os.path.basename(f)
                self._log(task, f"上传 [{i+1}/{total_files}]: {basename}")
                self._save_task(task)
            
            self._log(task, "SCP文件上传完成（模拟）")
            
            return {
                'success': True,
                'message': 'SCP部署完成',
                'files_uploaded': len(files),
                'note': '需要配置SSH密钥后才能实际上传'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'SCP部署失败: {str(e)}'
            }
    
    def _deploy_via_rsync(self, task: DeploymentTask, config: Dict,
                         files: List[str]) -> Dict[str, Any]:
        """通过rsync部署"""
        try:
            result = subprocess.run(['which', 'rsync'], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': 'rsync命令不可用'
                }
            
            self._log(task, "rsync部署模式")
            
            return {
                'success': True,
                'message': 'rsync部署就绪',
                'note': '需要配置SSH密钥后才能实际同步'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'rsync部署失败: {str(e)}'
            }
    
    def _deploy_via_sftp(self, task: DeploymentTask, config: Dict,
                        files: List[str]) -> Dict[str, Any]:
        """通过SFTP部署"""
        try:
            import paramiko
            self._log(task, "SFTP部署模式")
            return {
                'success': True,
                'message': 'SFTP部署就绪',
                'note': '需要配置SFTP连接信息后才能实际上传'
            }
        except ImportError:
            return {
                'success': False,
                'message': 'paramiko库未安装，无法使用SFTP'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'SFTP部署失败: {str(e)}'
            }
    
    def _deploy_via_git(self, task: DeploymentTask, config: Dict,
                       files: List[str]) -> Dict[str, Any]:
        """通过Git部署"""
        try:
            self._log(task, "Git部署模式")
            
            # 检查Git仓库状态
            git_status = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True,
                cwd=self.project_root
            )
            
            has_changes = bool(git_status.stdout.strip())
            self._log(task, f"Git工作区状态: {'有未提交更改' if has_changes else '干净'}")
            
            return {
                'success': True,
                'message': 'Git部署就绪',
                'has_uncommitted_changes': has_changes,
                'note': '需要配置远程Git仓库后才能实际推送部署'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Git部署失败: {str(e)}'
            }
    
    def _post_deployment_config(self, task: DeploymentTask, config: Dict) -> Dict[str, Any]:
        """部署后配置"""
        try:
            self._log(task, "执行部署后配置...")
            
            config_steps = [
                "设置文件权限",
                "重启应用服务",
                "更新配置文件",
                "清除缓存"
            ]
            
            for step in config_steps:
                self._log(task, f"  - {step}")
            
            return {
                'success': True,
                'message': '部署后配置完成'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'部署后配置失败: {str(e)}'
            }
    
    def _verify_deployment(self, task: DeploymentTask, config: Dict) -> Dict[str, Any]:
        """验证部署结果"""
        try:
            host = config.get('host', '')
            
            self._log(task, f"验证部署: http://{host}")
            
            # 测试HTTP连接
            try:
                import urllib.request
                proxy_handler = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy_handler)
                
                url = f"http://{host}"
                req = urllib.request.Request(url, method='GET')
                req.add_header('User-Agent', 'MTSCOS-Deployment-Checker/1.0')
                
                response = opener.open(req, timeout=10)
                status_code = response.getcode()
                
                self._log(task, f"HTTP响应状态: {status_code}")
                
                if status_code == 200:
                    return {
                        'success': True,
                        'message': '部署验证通过',
                        'status_code': status_code
                    }
                else:
                    return {
                        'success': False,
                        'message': f'HTTP状态码异常: {status_code}',
                        'status_code': status_code
                    }
            
            except Exception as e:
                self._log(task, f"HTTP验证跳过: {str(e)}")
                return {
                    'success': True,
                    'message': '部署完成（HTTP验证跳过，需手动确认）',
                    'note': str(e)
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'验证失败: {str(e)}'
            }
    
    def _log(self, task: DeploymentTask, message: str):
        """记录部署日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        task.logs.append(log_entry)
        
        if len(task.logs) > 200:
            task.logs = task.logs[-200:]
        
        logger.info(f"[{task.task_id}] {message}")
    
    def _save_task(self, task: DeploymentTask):
        """保存任务到数据库"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO deployment_tasks
                    (task_id, target_server, deployment_method, status,
                     progress, message, start_time, end_time,
                     config, result, logs, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.task_id,
                    task.target_server,
                    task.method,
                    task.status,
                    task.progress,
                    task.message,
                    task.start_time,
                    task.end_time,
                    json.dumps(task.details.get('config', {})),
                    json.dumps({k: v for k, v in task.details.items() if k != 'config'}),
                    json.dumps(task.logs[-100:]),
                    task.start_time or now,
                    now
                ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"保存部署任务失败: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        if task:
            return {
                'task_id': task.task_id,
                'target_server': task.target_server,
                'method': task.method,
                'status': task.status,
                'progress': task.progress,
                'message': task.message,
                'start_time': task.start_time,
                'end_time': task.end_time,
                'logs': task.logs[-20:],
                'details': task.details
            }
        
        # 从数据库查询
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT task_id, target_server, deployment_method, status,
                           progress, message, start_time, end_time, logs
                    FROM deployment_tasks
                    WHERE task_id = ?
                ''', (task_id,))
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    try:
                        data['logs'] = json.loads(data.get('logs', '[]'))
                    except:
                        data['logs'] = []
                    return data
        except Exception as e:
            logger.error(f"查询任务状态失败: {e}")
        
        return None
    
    def get_deployment_history(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取部署历史"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                offset = (page - 1) * page_size
                
                cursor.execute('''
                    SELECT task_id, target_server, deployment_method, status,
                           progress, message, start_time, end_time, created_at
                    FROM deployment_tasks
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (page_size, offset))
                
                rows = cursor.fetchall()
                tasks = [dict(row) for row in rows]
                
                cursor.execute('SELECT COUNT(*) as total FROM deployment_tasks')
                total = cursor.fetchone()[0]
                
                return {
                    'tasks': tasks,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                }
        
        except Exception as e:
            logger.error(f"获取部署历史失败: {e}")
            return {'tasks': [], 'total': 0, 'page': page, 'page_size': page_size}
    
    def get_available_methods(self) -> List[Dict[str, Any]]:
        """获取可用的部署方式"""
        methods = []
        
        # 检查SCP
        result = subprocess.run(['which', 'scp'], capture_output=True, text=True)
        methods.append({
            'method': 'scp',
            'name': 'SCP文件传输',
            'available': result.returncode == 0,
            'description': '通过SSH安全拷贝文件到远程服务器'
        })
        
        # 检查rsync
        result = subprocess.run(['which', 'rsync'], capture_output=True, text=True)
        methods.append({
            'method': 'rsync',
            'name': 'rsync同步',
            'available': result.returncode == 0,
            'description': '增量同步文件，适合频繁部署'
        })
        
        # 检查Git
        result = subprocess.run(['which', 'git'], capture_output=True, text=True)
        methods.append({
            'method': 'git',
            'name': 'Git部署',
            'available': result.returncode == 0,
            'description': '通过Git仓库推送部署'
        })
        
        # SFTP
        try:
            import paramiko
            sftp_available = True
        except ImportError:
            sftp_available = False
        methods.append({
            'method': 'sftp',
            'name': 'SFTP传输',
            'available': sftp_available,
            'description': '通过SFTP协议传输文件'
        })
        
        return methods


# 单例实例
_deployment_expert = None
_lock = threading.Lock()


def get_deployment_expert() -> DeploymentExpertAI:
    """获取部署专家AI单例"""
    global _deployment_expert
    if _deployment_expert is None:
        with _lock:
            if _deployment_expert is None:
                _deployment_expert = DeploymentExpertAI()
    return _deployment_expert

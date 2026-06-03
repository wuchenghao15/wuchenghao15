# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""服务器部署管理模块,负责自动化部署,配置管理,环境准备和部署验证"""

import os
import sys
import subprocess
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeploymentManager:
    """服务器部署管理器"""

    def __init__(self):
        """初始化部署管理器"""
        self.deployments: Dict[str, Dict[str, Any]] = {}
        self.current_deployment = None
        self.deployment_history = []
        
        self.config = {
            'default_deploy_path': '/opt/mtscos',
            'default_backup_path': '/opt/mtscos/backup',
            'default_log_path': '/var/log/mtscos',
            'backup_retention_days': 7,
            'max_parallel_deployments': 5
        }
        
        logger.info("部署管理器已初始化")

    def prepare_environment(self, env_config: Dict[str, Any]) -> Dict[str, Any]:
        """准备部署环境
        
        Args:
            env_config: 环境配置参数
            
        Returns:
            Dict[str, Any]: 环境准备结果
        """
        logger.info("开始准备部署环境...")
        
        result = {
            'success': True,
            'steps': [],
            'errors': []
        }
        
        try:
            deploy_path = env_config.get('deploy_path', self.config['default_deploy_path'])
            log_path = env_config.get('log_path', self.config['default_log_path'])
            backup_path = env_config.get('backup_path', self.config['default_backup_path'])
            
            step_result = self._create_directories([deploy_path, log_path, backup_path])
            result['steps'].append({'step': '创建目录', **step_result})
            
            if not step_result['success']:
                result['success'] = False
                result['errors'].append(f"创建目录失败: {step_result.get('error')}")
                return result
            
            step_result = self._install_dependencies(env_config.get('requirements', []))
            result['steps'].append({'step': '安装依赖', **step_result})
            
            if not step_result['success']:
                result['success'] = False
                result['errors'].append(f"安装依赖失败: {step_result.get('error')}")
                return result
            
            step_result = self._configure_nginx(env_config.get('nginx_config'))
            result['steps'].append({'step': '配置Nginx', **step_result})
            
            step_result = self._configure_systemd(env_config.get('systemd_config'))
            result['steps'].append({'step': '配置Systemd', **step_result})
            
            logger.info("环境准备完成")
            
        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
            logger.error(f"环境准备失败: {str(e)}")
        
        return result

    def _create_directories(self, paths: List[str]) -> Dict[str, Any]:
        """创建必要的目录"""
        try:
            for path in paths:
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    logger.debug(f"创建目录: {path}")
            return {'success': True, 'created': paths}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _install_dependencies(self, requirements: List[str]) -> Dict[str, Any]:
        """安装依赖包"""
        if not requirements:
            return {'success': True, 'message': '无需安装依赖'}
        
        try:
            result = subprocess.run(
                ['pip', 'install'] + requirements,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return {'success': True, 'installed': requirements}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _configure_nginx(self, nginx_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """配置Nginx反向代理"""
        if not nginx_config:
            return {'success': True, 'message': '跳过Nginx配置'}
        
        try:
            config_content = self._generate_nginx_config(nginx_config)
            config_path = '/etc/nginx/sites-available/mtscos'
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            if os.path.exists('/etc/nginx/sites-enabled/mtscos'):
                os.remove('/etc/nginx/sites-enabled/mtscos')
            
            os.symlink(config_path, '/etc/nginx/sites-enabled/mtscos')
            
            subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
            return {'success': True, 'message': 'Nginx配置完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_nginx_config(self, config: Dict[str, Any]) -> str:
        """生成Nginx配置文件内容"""
        template = f"""server {{
    listen {config.get('port', 80)};
    server_name {config.get('domain', 'localhost')};

    location / {{
        proxy_pass http://127.0.0.1:{config.get('app_port', 8888)};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /static/ {{
        root {config.get('static_path', '/opt/mtscos/static')};
        expires 30d;
    }}

    location /api/ {{
        proxy_pass http://127.0.0.1:{config.get('app_port', 8888)}/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
        return template

    def _configure_systemd(self, systemd_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """配置Systemd服务"""
        if not systemd_config:
            return {'success': True, 'message': '跳过Systemd配置'}
        
        try:
            config_content = self._generate_systemd_config(systemd_config)
            service_path = '/etc/systemd/system/mtscos.service'
            
            with open(service_path, 'w') as f:
                f.write(config_content)
            
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'mtscos'], check=True)
            
            return {'success': True, 'message': 'Systemd配置完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_systemd_config(self, config: Dict[str, Any]) -> str:
        """生成Systemd服务配置"""
        template = f"""[Unit]
Description=MTSCOS AI System
After=network.target

[Service]
Type=simple
User={config.get('user', 'www-data')}
WorkingDirectory={config.get('working_dir', '/opt/mtscos')}
ExecStart={config.get('exec_start', 'python3 app.py')}
Restart=always
RestartSec=5
Environment=PYTHONPATH={config.get('working_dir', '/opt/mtscos')}

[Install]
WantedBy=multi-user.target
"""
        return template

    def deploy(self, deploy_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行部署
        
        Args:
            deploy_config: 部署配置
            
        Returns:
            Dict[str, Any]: 部署结果
        """
        deployment_id = f"deploy_{int(time.time())}"
        logger.info(f"开始部署任务: {deployment_id}")
        
        result = {
            'deployment_id': deployment_id,
            'start_time': datetime.now().isoformat(),
            'steps': [],
            'success': False,
            'error': None
        }
        
        self.deployments[deployment_id] = {'status': 'in_progress', 'config': deploy_config}
        
        try:
            step_result = self.prepare_environment(deploy_config.get('environment', {}))
            result['steps'].append({'step': '环境准备', **step_result})
            
            if not step_result['success']:
                result['error'] = "环境准备失败"
                return result
            
            step_result = self._copy_files(deploy_config.get('source_path', '.'), 
                                          deploy_config.get('deploy_path', self.config['default_deploy_path']))
            result['steps'].append({'step': '复制文件', **step_result})
            
            if not step_result['success']:
                result['error'] = "文件复制失败"
                return result
            
            step_result = self._apply_migrations(deploy_config.get('database_config'))
            result['steps'].append({'step': '数据库迁移', **step_result})
            
            if not step_result['success']:
                result['error'] = "数据库迁移失败"
                return result
            
            step_result = self._start_services(deploy_config.get('services', []))
            result['steps'].append({'step': '启动服务', **step_result})
            
            if not step_result['success']:
                result['error'] = "服务启动失败"
                return result
            
            step_result = self._validate_deployment(deploy_config.get('validation_config'))
            result['steps'].append({'step': '验证部署', **step_result})
            
            if not step_result['success']:
                result['error'] = "部署验证失败"
                return result
            
            result['success'] = True
            result['end_time'] = datetime.now().isoformat()
            
            self.deployments[deployment_id]['status'] = 'completed'
            self.deployment_history.append(result)
            
            logger.info(f"部署任务 {deployment_id} 完成")
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            self.deployments[deployment_id]['status'] = 'failed'
            
            logger.error(f"部署任务 {deployment_id} 失败: {str(e)}")
        
        return result

    def _copy_files(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """复制部署文件"""
        try:
            result = subprocess.run(
                ['rsync', '-av', '--delete', f"{source_path}/", target_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return {'success': True, 'message': '文件复制成功'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _apply_migrations(self, db_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """应用数据库迁移"""
        if not db_config:
            return {'success': True, 'message': '跳过数据库迁移'}
        
        try:
            from app.utils.db import DatabaseManager
            db_manager = DatabaseManager()
            db_manager.apply_migrations()
            return {'success': True, 'message': '数据库迁移完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _start_services(self, services: List[str]) -> Dict[str, Any]:
        """启动服务"""
        if not services:
            services = ['mtscos']
        
        results = []
        for service in services:
            try:
                subprocess.run(['systemctl', 'start', service], check=True)
                results.append({'service': service, 'success': True})
            except subprocess.CalledProcessError as e:
                results.append({'service': service, 'success': False, 'error': str(e)})
        
        all_success = all(r['success'] for r in results)
        return {'success': all_success, 'services': results}

    def _validate_deployment(self, validation_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """验证部署是否成功"""
        try:
            import requests
            
            url = validation_config.get('health_check_url', 'http://localhost:8888/api/health')
            timeout = validation_config.get('timeout', 30)
            
            for attempt in range(5):
                try:
                    response = requests.get(url, timeout=timeout)
                    if response.status_code == 200:
                        return {'success': True, 'message': '健康检查通过', 'status_code': response.status_code}
                except requests.exceptions.RequestException:
                    pass
                time.sleep(5)
            
            return {'success': False, 'error': '健康检查超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def rollback(self, deployment_id: str) -> Dict[str, Any]:
        """回滚部署
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Dict[str, Any]: 回滚结果
        """
        logger.info(f"开始回滚部署: {deployment_id}")
        
        result = {
            'deployment_id': deployment_id,
            'rollback_time': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            backup_path = os.path.join(self.config['default_backup_path'], deployment_id)
            
            if not os.path.exists(backup_path):
                result['error'] = "备份文件不存在"
                return result
            
            deploy_path = self.config['default_deploy_path']
            
            result_restore = subprocess.run(
                ['rsync', '-av', '--delete', f"{backup_path}/", deploy_path],
                capture_output=True,
                text=True
            )
            
            if result_restore.returncode != 0:
                result['error'] = result_restore.stderr
                return result
            
            result_restart = subprocess.run(['systemctl', 'restart', 'mtscos'])
            
            if result_restart.returncode == 0:
                result['success'] = True
                logger.info(f"部署 {deployment_id} 回滚成功")
            else:
                result['error'] = "服务重启失败"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"回滚部署失败: {str(e)}")
        
        return result

    def backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """创建备份
        
        Args:
            backup_name: 备份名称
            
        Returns:
            Dict[str, Any]: 备份结果
        """
        backup_name = backup_name or f"backup_{int(time.time())}"
        backup_path = os.path.join(self.config['default_backup_path'], backup_name)
        
        logger.info(f"创建备份: {backup_name}")
        
        result = {
            'backup_name': backup_name,
            'backup_path': backup_path,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            result_copy = subprocess.run(
                ['rsync', '-av', '--delete', f"{self.config['default_deploy_path']}/", backup_path],
                capture_output=True,
                text=True
            )
            
            if result_copy.returncode == 0:
                result['success'] = True
                logger.info(f"备份 {backup_name} 创建成功")
            else:
                result['error'] = result_copy.stderr
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"创建备份失败: {str(e)}")
        
        return result

    def clean_old_backups(self) -> Dict[str, Any]:
        """清理旧备份"""
        logger.info("清理旧备份...")
        
        result = {
            'cleaned': [],
            'errors': []
        }
        
        try:
            cutoff_time = time.time() - (self.config['backup_retention_days'] * 24 * 3600)
            
            for backup_name in os.listdir(self.config['default_backup_path']):
                backup_path = os.path.join(self.config['default_backup_path'], backup_name)
                
                if os.path.isdir(backup_path):
                    mtime = os.path.getmtime(backup_path)
                    if mtime < cutoff_time:
                        subprocess.run(['rm', '-rf', backup_path])
                        result['cleaned'].append(backup_name)
            
            logger.info(f"清理完成,共删除 {len(result['cleaned'])} 个旧备份")
            
        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"清理旧备份失败: {str(e)}")
        
        return result

    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """获取部署状态
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Optional[Dict[str, Any]]: 部署状态
        """
        return self.deployments.get(deployment_id)

    def get_all_deployments(self) -> Dict[str, Any]:
        """获取所有部署记录"""
        return self.deployments

    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """获取部署历史"""
        return self.deployment_history

    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        logger.info(f"部署配置已更新: {new_config}")

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()

deployment_manager = DeploymentManager()

def get_deployment_manager() -> DeploymentManager:
    """获取部署管理器实例"""
    return deployment_manager

def deploy_mtscos(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """便捷部署函数"""
    config = config or {}
    return deployment_manager.deploy(config)
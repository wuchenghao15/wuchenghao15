#!/usr/bin/env python3
"""
Git/GitHub 自动同步模块
处理 Git 仓库的自动同步、提交、推送等操作
"""

import os
import sys
import json
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GitSyncManager:
    """Git同步管理器"""

    def __init__(self, config_path='sync_config.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self.project_dir = os.path.dirname(os.path.abspath(config_path))
        self.git_dir = os.path.join(self.project_dir, '.git')
        self._setup_logging()

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()

    def _get_default_config(self):
        """获取默认配置"""
        return {
            'sync': {
                'enabled': True,
                'interval_minutes': 60,
                'auto_commit': True,
                'commit_message': "Auto sync: {timestamp}",
                'push_on_sync': True,
                'pull_on_start': True,
                'remote_name': 'origin',
                'main_branch': 'main'
            },
            'github': {
                'remote_url': 'git@github.com:zhudoiwen/wenhaixingchen2.git',
                'https_url': 'https://github.com/zhudoiwen/wenhaixingchen2.git',
                'use_ssh': True
            }
        }

    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.expanduser(self.config.get('logging', {}).get('log_dir', '~/MTSCOS_Sync_Logs'))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"git_sync_{datetime.now().strftime('%Y%m%d')}.log")

        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _run_command(self, cmd, cwd=None, check=True):
        """运行命令并返回结果"""
        if cwd is None:
            cwd = self.project_dir

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if check and result.returncode != 0:
                logger.error(f"命令执行失败: {' '.join(cmd)}")
                logger.error(f"stderr: {result.stderr}")
                raise RuntimeError(f"Command failed with code {result.returncode}")
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"命令超时: {' '.join(cmd)}")
            return "", "Command timed out"
        except Exception as e:
            logger.error(f"命令执行异常: {' '.join(cmd)} - {e}")
            return "", str(e)

    def is_git_repo(self):
        """检查是否是Git仓库"""
        return os.path.exists(self.git_dir)

    def init_git_repo(self):
        """初始化Git仓库"""
        if self.is_git_repo():
            logger.info("Git仓库已存在")
            return True

        logger.info("初始化Git仓库...")
        try:
            self._run_command(['git', 'init'], check=True)
            self._run_command(['git', 'config', 'user.email', 'auto-sync@mtscos.com'], check=True)
            self._run_command(['git', 'config', 'user.name', 'MTSCOS Auto Sync'], check=True)
            logger.info("Git仓库初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化Git仓库失败: {e}")
            return False

    def get_remote_url(self, remote_name='origin'):
        """获取远程仓库URL"""
        try:
            stdout, _ = self._run_command(['git', 'remote', 'get-url', remote_name], check=False)
            return stdout if stdout else None
        except Exception as e:
            logger.error(f"获取远程URL失败: {e}")
            return None

    def set_remote_url(self, url, remote_name='origin'):
        """设置远程仓库URL"""
        try:
            current_url = self.get_remote_url(remote_name)
            if current_url == url:
                logger.info(f"远程URL已正确配置: {url}")
                return True

            if current_url:
                logger.info(f"更新远程URL: {current_url} -> {url}")
                self._run_command(['git', 'remote', 'set-url', remote_name, url], check=True)
            else:
                logger.info(f"添加远程仓库: {url}")
                self._run_command(['git', 'remote', 'add', remote_name, url], check=True)

            return True
        except Exception as e:
            logger.error(f"设置远程URL失败: {e}")
            return False

    def check_ssh_key(self):
        """检查SSH密钥是否存在"""
        ssh_dir = os.path.expanduser('~/.ssh')
        key_files = ['id_ed25519', 'id_rsa']

        for key_file in key_files:
            if os.path.exists(os.path.join(ssh_dir, key_file)):
                logger.info(f"找到SSH密钥: {key_file}")
                return True

        logger.warning("未找到SSH密钥，将使用HTTPS方式")
        return False

    def get_working_remote_url(self):
        """获取可用的远程URL（优先SSH）"""
        github_config = self.config.get('github', {})

        if github_config.get('use_ssh', True) and self.check_ssh_key():
            return github_config.get('remote_url', '')

        return github_config.get('https_url', '')

    def check_github_connectivity(self):
        """检查GitHub连接性"""
        try:
            url = self.get_working_remote_url()
            if url.startswith('git@'):
                host = url.split('@')[1].split(':')[0]
                result = subprocess.run(
                    ['ssh', '-T', '-o', 'ConnectTimeout=5', url.split(':')[0]],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode in [0, 1]:
                    logger.info("SSH连接GitHub成功")
                    return True
                else:
                    logger.warning(f"SSH连接失败: {result.stderr}")
            else:
                result = subprocess.run(
                    ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://github.com'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout == '200':
                    logger.info("HTTPS连接GitHub成功")
                    return True
                else:
                    logger.warning(f"HTTPS连接失败: {result.stdout}")

            return False
        except Exception as e:
            logger.error(f"检查GitHub连接性失败: {e}")
            return False

    def add_all_files(self):
        """添加所有文件到暂存区"""
        try:
            self._run_command(['git', 'add', '.'], check=True)
            logger.info("文件已添加到暂存区")
            return True
        except Exception as e:
            logger.error(f"添加文件失败: {e}")
            return False

    def get_status(self):
        """获取Git状态"""
        try:
            stdout, _ = self._run_command(['git', 'status', '--porcelain'], check=True)
            return stdout
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return ""

    def has_changes(self):
        """检查是否有未提交的更改"""
        status = self.get_status()
        return len(status) > 0

    def commit(self, message=None):
        """提交更改"""
        if not self.has_changes():
            logger.info("没有需要提交的更改")
            return True

        if message is None:
            message = self.config['sync']['commit_message'].format(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        try:
            self._run_command(['git', 'commit', '-m', message], check=True)
            logger.info(f"提交成功: {message}")
            return True
        except Exception as e:
            logger.error(f"提交失败: {e}")
            return False

    def pull(self, branch=None):
        """拉取远程分支"""
        if branch is None:
            branch = self.config['sync']['main_branch']

        try:
            stdout, stderr = self._run_command(
                ['git', 'pull', 'origin', branch],
                check=False
            )
            if "Already up to date" in stdout:
                logger.info("本地已是最新")
                return True
            elif "merge conflict" in stdout.lower() or "merge conflict" in stderr.lower():
                logger.error("拉取时发生合并冲突")
                return False
            elif "error" in stderr.lower():
                logger.error(f"拉取失败: {stderr}")
                return False
            else:
                logger.info(f"拉取成功: {stdout}")
                return True
        except Exception as e:
            logger.error(f"拉取失败: {e}")
            return False

    def push(self, branch=None):
        """推送远程分支"""
        if branch is None:
            branch = self.config['sync']['main_branch']

        try:
            stdout, stderr = self._run_command(
                ['git', 'push', '-u', 'origin', branch],
                check=False,
                timeout=120
            )
            if "rejected" in stderr.lower():
                logger.error(f"推送被拒绝: {stderr}")
                return False
            elif "error" in stderr.lower() and "fatal" in stderr.lower():
                logger.error(f"推送失败: {stderr}")
                return False
            else:
                logger.info(f"推送成功: {stdout}")
                return True
        except subprocess.TimeoutExpired:
            logger.error("推送超时，可能需要认证")
            return False
        except Exception as e:
            logger.error(f"推送失败: {e}")
            return False

    def get_current_branch(self):
        """获取当前分支"""
        try:
            stdout, _ = self._run_command(['git', 'branch', '--show-current'], check=True)
            return stdout
        except Exception as e:
            logger.error(f"获取当前分支失败: {e}")
            return None

    def switch_branch(self, branch):
        """切换分支"""
        try:
            self._run_command(['git', 'checkout', branch], check=True)
            logger.info(f"切换到分支: {branch}")
            return True
        except Exception as e:
            logger.error(f"切换分支失败: {e}")
            return False

    def sync(self):
        """执行完整同步流程"""
        logger.info("========== 开始Git同步 ==========")

        if not self.config['sync']['enabled']:
            logger.info("同步已禁用")
            return {'success': False, 'message': '同步已禁用'}

        try:
            # 1. 初始化仓库
            if not self.init_git_repo():
                return {'success': False, 'message': '初始化仓库失败'}

            # 2. 检查GitHub连接性
            if not self.check_github_connectivity():
                logger.warning("GitHub连接性检查失败，将尝试直接同步")

            # 3. 配置远程仓库
            remote_url = self.get_working_remote_url()
            if not self.set_remote_url(remote_url):
                return {'success': False, 'message': '配置远程仓库失败'}

            # 4. 拉取最新代码
            if self.config['sync']['pull_on_start']:
                current_branch = self.get_current_branch()
                if not current_branch:
                    current_branch = self.config['sync']['main_branch']
                    self.switch_branch(current_branch)

                if not self.pull(current_branch):
                    logger.warning("拉取失败，继续执行本地提交")

            # 5. 添加并提交更改
            if self.config['sync']['auto_commit']:
                self.add_all_files()
                if not self.commit():
                    logger.warning("提交失败")

            # 6. 推送
            if self.config['sync']['push_on_sync'] and self.has_changes():
                current_branch = self.get_current_branch() or self.config['sync']['main_branch']
                if not self.push(current_branch):
                    return {'success': False, 'message': '推送失败'}

            logger.info("========== Git同步完成 ==========")
            return {'success': True, 'message': '同步成功'}

        except Exception as e:
            logger.error(f"同步失败: {e}")
            return {'success': False, 'message': str(e)}

    def run_periodic_sync(self, interval_minutes=None):
        """运行周期性同步"""
        if interval_minutes is None:
            interval_minutes = self.config['sync']['interval_minutes']

        logger.info(f"启动周期性同步，间隔: {interval_minutes}分钟")

        while True:
            try:
                result = self.sync()
                if result['success']:
                    logger.info(f"同步成功，下次同步在 {interval_minutes} 分钟后")
                else:
                    logger.error(f"同步失败: {result['message']}")
            except Exception as e:
                logger.error(f"同步循环异常: {e}")

            time.sleep(interval_minutes * 60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Git/GitHub自动同步')
    parser.add_argument('--config', default='sync_config.json', help='配置文件路径')
    parser.add_argument('--sync', action='store_true', help='执行单次同步')
    parser.add_argument('--periodic', action='store_true', help='启动周期性同步')
    parser.add_argument('--check', action='store_true', help='检查仓库状态')

    args = parser.parse_args()

    git_sync = GitSyncManager(args.config)

    if args.check:
        print(f"Git仓库: {'是' if git_sync.is_git_repo() else '否'}")
        print(f"远程URL: {git_sync.get_remote_url() or '未配置'}")
        print(f"当前分支: {git_sync.get_current_branch() or '未知'}")
        print(f"有更改: {'是' if git_sync.has_changes() else '否'}")
        print(f"SSH密钥: {'有' if git_sync.check_ssh_key() else '无'}")
        print(f"GitHub连接: {'可达' if git_sync.check_github_connectivity() else '不可达'}")

    elif args.sync:
        result = git_sync.sync()
        print(f"同步结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.periodic:
        git_sync.run_periodic_sync()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
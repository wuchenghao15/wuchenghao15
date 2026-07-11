#!/usr/bin/env python3
"""
沙盒环境管理模块
处理自动创建和管理沙盒环境
"""

import os
import sys
import json
import logging
import shutil
import time
import glob
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SandboxManager:
    """沙盒管理器"""

    def __init__(self, config_path='sync_config.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self.project_dir = os.path.dirname(os.path.abspath(config_path))
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
            'sandbox': {
                'enabled': False,
                'sandbox_dir': '${HOME}/MTSCOS_Sandbox',
                'auto_create_on_change': False,
                'cleanup_interval_hours': 24
            }
        }

    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.expanduser(self.config.get('logging', {}).get('log_dir', '~/MTSCOS_Sync_Logs'))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"sandbox_{datetime.now().strftime('%Y%m%d')}.log")

        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _expand_path(self, path):
        """扩展路径中的环境变量"""
        return os.path.expandvars(os.path.expanduser(path))

    def _get_sandbox_dir(self):
        """获取沙盒目录"""
        return self._expand_path(self.config['sandbox']['sandbox_dir'])

    def create_sandbox(self, name=None, description=""):
        """创建沙盒环境"""
        if not self.config['sandbox']['enabled']:
            logger.info("沙盒功能已禁用")
            return {'success': False, 'message': '沙盒功能已禁用'}

        sandbox_dir = self._get_sandbox_dir()
        os.makedirs(sandbox_dir, exist_ok=True)

        if name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"sandbox_{timestamp}"

        sandbox_path = os.path.join(sandbox_dir, name)

        if os.path.exists(sandbox_path):
            logger.warning(f"沙盒已存在: {name}")
            return {'success': False, 'message': f"沙盒已存在: {name}"}

        logger.info(f"创建沙盒环境: {name}")

        try:
            os.makedirs(sandbox_path, exist_ok=True)

            # 创建沙盒目录结构
            os.makedirs(os.path.join(sandbox_path, 'app'), exist_ok=True)
            os.makedirs(os.path.join(sandbox_path, 'data'), exist_ok=True)
            os.makedirs(os.path.join(sandbox_path, 'logs'), exist_ok=True)
            os.makedirs(os.path.join(sandbox_path, 'config'), exist_ok=True)
            os.makedirs(os.path.join(sandbox_path, 'tmp'), exist_ok=True)

            # 复制项目文件到沙盒
            self._copy_project_to_sandbox(sandbox_path)

            # 创建沙盒配置
            sandbox_config = {
                'name': name,
                'path': sandbox_path,
                'created_at': datetime.now().isoformat(),
                'description': description,
                'source': self.project_dir,
                'status': 'running',
                'pid': None,
                'port': None
            }

            config_path = os.path.join(sandbox_path, 'sandbox_config.json')
            with open(config_path, 'w') as f:
                json.dump(sandbox_config, f, indent=2)

            logger.info(f"沙盒环境创建成功: {name}")

            return {
                'success': True,
                'message': '沙盒环境创建成功',
                'name': name,
                'path': sandbox_path,
                'description': description
            }

        except Exception as e:
            logger.error(f"创建沙盒环境失败: {e}")
            # 清理已创建的目录
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)
            return {'success': False, 'message': str(e)}

    def _copy_project_to_sandbox(self, sandbox_path):
        """复制项目文件到沙盒"""
        app_dir = os.path.join(sandbox_path, 'app')

        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'backup', 'backups']]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.project_dir)
                target_path = os.path.join(app_dir, rel_path)

                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(full_path, target_path)
                logger.debug(f"复制文件到沙盒: {rel_path}")

    def list_sandboxes(self):
        """列出所有沙盒环境"""
        sandbox_dir = self._get_sandbox_dir()
        sandbox_pattern = os.path.join(sandbox_dir, 'sandbox_*')
        sandboxes = sorted(glob.glob(sandbox_pattern), reverse=True)

        result = []
        for sandbox in sandboxes:
            if os.path.isdir(sandbox):
                config_path = os.path.join(sandbox, 'sandbox_config.json')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            result.append({
                                'name': config.get('name', os.path.basename(sandbox)),
                                'path': sandbox,
                                'created_at': config.get('created_at', ''),
                                'description': config.get('description', ''),
                                'status': config.get('status', 'unknown')
                            })
                    except:
                        result.append({
                            'name': os.path.basename(sandbox),
                            'path': sandbox,
                            'status': 'unknown'
                        })
                else:
                    result.append({
                        'name': os.path.basename(sandbox),
                        'path': sandbox,
                        'status': 'unknown'
                    })

        return result

    def get_sandbox(self, name):
        """获取沙盒信息"""
        sandbox_dir = self._get_sandbox_dir()
        sandbox_path = os.path.join(sandbox_dir, name)

        if not os.path.exists(sandbox_path):
            return None

        config_path = os.path.join(sandbox_path, 'sandbox_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)

        return None

    def start_sandbox(self, name):
        """启动沙盒环境"""
        sandbox = self.get_sandbox(name)
        if not sandbox:
            return {'success': False, 'message': f"沙盒不存在: {name}"}

        logger.info(f"启动沙盒环境: {name}")

        try:
            # 更新状态
            sandbox['status'] = 'running'
            config_path = os.path.join(sandbox['path'], 'sandbox_config.json')
            with open(config_path, 'w') as f:
                json.dump(sandbox, f, indent=2)

            logger.info(f"沙盒启动成功: {name}")

            return {
                'success': True,
                'message': '沙盒启动成功',
                'name': name,
                'path': sandbox['path']
            }

        except Exception as e:
            logger.error(f"启动沙盒失败: {e}")
            return {'success': False, 'message': str(e)}

    def stop_sandbox(self, name):
        """停止沙盒环境"""
        sandbox = self.get_sandbox(name)
        if not sandbox:
            return {'success': False, 'message': f"沙盒不存在: {name}"}

        logger.info(f"停止沙盒环境: {name}")

        try:
            sandbox['status'] = 'stopped'
            config_path = os.path.join(sandbox['path'], 'sandbox_config.json')
            with open(config_path, 'w') as f:
                json.dump(sandbox, f, indent=2)

            logger.info(f"沙盒停止成功: {name}")

            return {
                'success': True,
                'message': '沙盒停止成功',
                'name': name
            }

        except Exception as e:
            logger.error(f"停止沙盒失败: {e}")
            return {'success': False, 'message': str(e)}

    def delete_sandbox(self, name):
        """删除沙盒环境"""
        sandbox_dir = self._get_sandbox_dir()
        sandbox_path = os.path.join(sandbox_dir, name)

        if not os.path.exists(sandbox_path):
            return {'success': False, 'message': f"沙盒不存在: {name}"}

        logger.info(f"删除沙盒环境: {name}")

        try:
            shutil.rmtree(sandbox_path)
            logger.info(f"沙盒删除成功: {name}")

            return {
                'success': True,
                'message': '沙盒删除成功',
                'name': name
            }

        except Exception as e:
            logger.error(f"删除沙盒失败: {e}")
            return {'success': False, 'message': str(e)}

    def cleanup_old_sandboxes(self):
        """清理旧沙盒环境"""
        sandbox_dir = self._get_sandbox_dir()
        cleanup_interval = self.config['sandbox']['cleanup_interval_hours']

        sandbox_pattern = os.path.join(sandbox_dir, 'sandbox_*')
        sandboxes = sorted(glob.glob(sandbox_pattern), reverse=True)

        now = datetime.now()
        deleted_count = 0

        for sandbox in sandboxes:
            if os.path.isdir(sandbox):
                config_path = os.path.join(sandbox, 'sandbox_config.json')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                        created_at = datetime.fromisoformat(config.get('created_at', ''))
                        age_hours = (now - created_at).total_seconds() / 3600

                        if age_hours > cleanup_interval:
                            shutil.rmtree(sandbox)
                            deleted_count += 1
                            logger.info(f"清理旧沙盒: {os.path.basename(sandbox)}")
                    except:
                        pass

        return {
            'success': True,
            'message': f"清理完成，共删除 {deleted_count} 个沙盒",
            'deleted_count': deleted_count
        }

    def run_auto_cleanup(self):
        """运行自动清理"""
        logger.info("启动沙盒自动清理")

        while True:
            try:
                result = self.cleanup_old_sandboxes()
                logger.info(result['message'])
            except Exception as e:
                logger.error(f"沙盒清理异常: {e}")

            interval_hours = self.config['sandbox']['cleanup_interval_hours']
            time.sleep(interval_hours * 3600)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='沙盒环境管理')
    parser.add_argument('--config', default='sync_config.json', help='配置文件路径')
    parser.add_argument('--create', action='store_true', help='创建沙盒环境')
    parser.add_argument('--list', action='store_true', help='列出所有沙盒')
    parser.add_argument('--start', help='启动指定沙盒')
    parser.add_argument('--stop', help='停止指定沙盒')
    parser.add_argument('--delete', help='删除指定沙盒')
    parser.add_argument('--cleanup', action='store_true', help='清理旧沙盒')

    args = parser.parse_args()

    sandbox_manager = SandboxManager(args.config)

    if args.list:
        sandboxes = sandbox_manager.list_sandboxes()
        for s in sandboxes:
            print(f"{s['name']} - {s['status']} - {s.get('created_at', '')}")

    elif args.create:
        result = sandbox_manager.create_sandbox()
        print(f"创建结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.start:
        result = sandbox_manager.start_sandbox(args.start)
        print(f"启动结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.stop:
        result = sandbox_manager.stop_sandbox(args.stop)
        print(f"停止结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.delete:
        result = sandbox_manager.delete_sandbox(args.delete)
        print(f"删除结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.cleanup:
        result = sandbox_manager.cleanup_old_sandboxes()
        print(f"清理结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
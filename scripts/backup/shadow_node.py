#!/usr/bin/env python3
"""
影子系统节点管理模块
处理自动创建和管理影子系统节点
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


class ShadowNodeManager:
    """影子节点管理器"""

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
            'shadow': {
                'enabled': False,
                'shadow_dir': '${HOME}/MTSCOS_Shadow',
                'sync_interval_minutes': 30,
                'keep_versions': 5
            }
        }

    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.expanduser(self.config.get('logging', {}).get('log_dir', '~/MTSCOS_Sync_Logs'))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"shadow_{datetime.now().strftime('%Y%m%d')}.log")

        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _expand_path(self, path):
        """扩展路径中的环境变量"""
        return os.path.expandvars(os.path.expanduser(path))

    def _get_shadow_dir(self):
        """获取影子节点目录"""
        return self._expand_path(self.config['shadow']['shadow_dir'])

    def create_shadow_node(self, name=None, description=""):
        """创建影子系统节点"""
        if not self.config['shadow']['enabled']:
            logger.info("影子节点功能已禁用")
            return {'success': False, 'message': '影子节点功能已禁用'}

        shadow_dir = self._get_shadow_dir()
        os.makedirs(shadow_dir, exist_ok=True)

        if name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"shadow_{timestamp}"

        shadow_path = os.path.join(shadow_dir, name)

        if os.path.exists(shadow_path):
            logger.warning(f"影子节点已存在: {name}")
            return {'success': False, 'message': f"影子节点已存在: {name}"}

        logger.info(f"创建影子系统节点: {name}")

        try:
            os.makedirs(shadow_path, exist_ok=True)

            # 创建目录结构
            os.makedirs(os.path.join(shadow_path, 'app'), exist_ok=True)
            os.makedirs(os.path.join(shadow_path, 'data'), exist_ok=True)
            os.makedirs(os.path.join(shadow_path, 'logs'), exist_ok=True)
            os.makedirs(os.path.join(shadow_path, 'config'), exist_ok=True)

            # 同步项目文件到影子节点
            self._sync_to_shadow(shadow_path)

            # 创建节点配置
            node_config = {
                'name': name,
                'path': shadow_path,
                'created_at': datetime.now().isoformat(),
                'last_sync': datetime.now().isoformat(),
                'description': description,
                'source': self.project_dir,
                'status': 'active',
                'version': 1
            }

            config_path = os.path.join(shadow_path, 'shadow_config.json')
            with open(config_path, 'w') as f:
                json.dump(node_config, f, indent=2)

            # 清理旧版本
            self._cleanup_old_versions()

            logger.info(f"影子系统节点创建成功: {name}")

            return {
                'success': True,
                'message': '影子系统节点创建成功',
                'name': name,
                'path': shadow_path,
                'description': description
            }

        except Exception as e:
            logger.error(f"创建影子系统节点失败: {e}")
            if os.path.exists(shadow_path):
                shutil.rmtree(shadow_path)
            return {'success': False, 'message': str(e)}

    def _sync_to_shadow(self, shadow_path):
        """同步项目文件到影子节点"""
        app_dir = os.path.join(shadow_path, 'app')

        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'backup', 'backups']]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.project_dir)
                target_path = os.path.join(app_dir, rel_path)

                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # 仅复制更新的文件
                if not os.path.exists(target_path) or \
                        os.path.getmtime(full_path) > os.path.getmtime(target_path):
                    shutil.copy2(full_path, target_path)
                    logger.debug(f"同步文件: {rel_path}")

    def list_shadow_nodes(self):
        """列出所有影子节点"""
        shadow_dir = self._get_shadow_dir()
        shadow_pattern = os.path.join(shadow_dir, 'shadow_*')
        shadows = sorted(glob.glob(shadow_pattern), reverse=True)

        result = []
        for shadow in shadows:
            if os.path.isdir(shadow):
                config_path = os.path.join(shadow, 'shadow_config.json')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            result.append({
                                'name': config.get('name', os.path.basename(shadow)),
                                'path': shadow,
                                'created_at': config.get('created_at', ''),
                                'last_sync': config.get('last_sync', ''),
                                'description': config.get('description', ''),
                                'status': config.get('status', 'unknown'),
                                'version': config.get('version', 1)
                            })
                    except:
                        result.append({
                            'name': os.path.basename(shadow),
                            'path': shadow,
                            'status': 'unknown'
                        })
                else:
                    result.append({
                        'name': os.path.basename(shadow),
                        'path': shadow,
                        'status': 'unknown'
                    })

        return result

    def sync_shadow_nodes(self):
        """同步所有影子节点"""
        if not self.config['shadow']['enabled']:
            return {'success': False, 'message': '影子节点功能已禁用'}

        shadow_dir = self._get_shadow_dir()
        shadow_pattern = os.path.join(shadow_dir, 'shadow_*')
        shadows = sorted(glob.glob(shadow_pattern))

        sync_count = 0
        for shadow in shadows:
            if os.path.isdir(shadow):
                config_path = os.path.join(shadow, 'shadow_config.json')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)

                        if config.get('status') == 'active':
                            self._sync_to_shadow(shadow)
                            config['last_sync'] = datetime.now().isoformat()
                            config['version'] = config.get('version', 1) + 1

                            with open(config_path, 'w') as f:
                                json.dump(config, f, indent=2)

                            sync_count += 1
                            logger.info(f"同步影子节点: {config['name']}")
                    except Exception as e:
                        logger.error(f"同步影子节点失败: {shadow} - {e}")

        return {
            'success': True,
            'message': f"同步完成，共同步 {sync_count} 个影子节点",
            'synced_count': sync_count
        }

    def _cleanup_old_versions(self):
        """清理旧版本影子节点"""
        shadow_dir = self._get_shadow_dir()
        keep_versions = self.config['shadow']['keep_versions']

        shadow_pattern = os.path.join(shadow_dir, 'shadow_*')
        shadows = sorted(glob.glob(shadow_pattern), reverse=True)

        if len(shadows) <= keep_versions:
            return

        old_shadows = shadows[keep_versions:]
        for shadow in old_shadows:
            if os.path.isdir(shadow):
                shutil.rmtree(shadow)
                logger.info(f"删除旧影子节点: {shadow}")

    def run_periodic_sync(self):
        """运行周期性同步"""
        if not self.config['shadow']['enabled']:
            logger.info("影子节点功能已禁用")
            return

        interval_minutes = self.config['shadow']['sync_interval_minutes']
        logger.info(f"启动影子节点周期性同步，间隔: {interval_minutes}分钟")

        while True:
            try:
                result = self.sync_shadow_nodes()
                logger.info(result['message'])
            except Exception as e:
                logger.error(f"影子节点同步异常: {e}")

            time.sleep(interval_minutes * 60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='影子系统节点管理')
    parser.add_argument('--config', default='sync_config.json', help='配置文件路径')
    parser.add_argument('--create', action='store_true', help='创建影子节点')
    parser.add_argument('--list', action='store_true', help='列出所有影子节点')
    parser.add_argument('--sync', action='store_true', help='同步所有影子节点')
    parser.add_argument('--periodic', action='store_true', help='启动周期性同步')

    args = parser.parse_args()

    shadow_manager = ShadowNodeManager(args.config)

    if args.list:
        nodes = shadow_manager.list_shadow_nodes()
        for n in nodes:
            print(f"{n['name']} - {n['status']} - 版本: {n.get('version', 1)}")

    elif args.create:
        result = shadow_manager.create_shadow_node()
        print(f"创建结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.sync:
        result = shadow_manager.sync_shadow_nodes()
        print(f"同步结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.periodic:
        shadow_manager.run_periodic_sync()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
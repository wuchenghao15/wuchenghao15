#!/usr/bin/env python3
"""
自动备份和恢复点管理模块
处理系统备份、恢复镜像创建和管理
"""

import os
import sys
import json
import logging
import tarfile
import shutil
import time
import glob
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupManager:
    """备份管理器"""

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
            'backup': {
                'enabled': True,
                'interval_minutes': 120,
                'max_backups': 30,
                'backup_dir': '${HOME}/MTSCOS_Backup',
                'include_patterns': ['**/*.py', '**/*.html', '**/*.css', '**/*.js'],
                'exclude_patterns': ['node_modules/**', '__pycache__/**', '.git/**']
            },
            'recovery': {
                'enabled': True,
                'create_image_on_sync': True,
                'image_format': 'tar.gz',
                'image_dir': '${HOME}/MTSCOS_Recovery',
                'max_images': 10
            }
        }

    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.expanduser(self.config.get('logging', {}).get('log_dir', '~/MTSCOS_Sync_Logs'))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"backup_{datetime.now().strftime('%Y%m%d')}.log")

        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _expand_path(self, path):
        """扩展路径中的环境变量"""
        return os.path.expandvars(os.path.expanduser(path))

    def _get_backup_dir(self):
        """获取备份目录"""
        return self._expand_path(self.config['backup']['backup_dir'])

    def _get_recovery_dir(self):
        """获取恢复镜像目录"""
        return self._expand_path(self.config['recovery']['image_dir'])

    def _should_include(self, rel_path):
        """判断文件是否应该包含在备份中"""
        include_patterns = self.config['backup'].get('include_patterns', [])
        exclude_patterns = self.config['backup'].get('exclude_patterns', [])

        for pattern in exclude_patterns:
            if self._match_pattern(rel_path, pattern):
                return False

        if not include_patterns:
            return True

        for pattern in include_patterns:
            if self._match_pattern(rel_path, pattern):
                return True

        return False

    def _match_pattern(self, path, pattern):
        """简单的模式匹配"""
        if '**' in pattern:
            parts = pattern.split('**')
            if parts[0] and not path.startswith(parts[0]):
                return False
            if parts[-1] and not path.endswith(parts[-1].replace('/', '')):
                return False
            return True
        elif '*' in pattern:
            import fnmatch
            return fnmatch.fnmatch(path, pattern)
        else:
            return path == pattern

    def create_backup(self, description="自动备份"):
        """创建备份"""
        if not self.config['backup']['enabled']:
            logger.info("备份已禁用")
            return {'success': False, 'message': '备份已禁用'}

        backup_dir = self._get_backup_dir()
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"mtscos_backup_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)

        logger.info(f"创建备份: {backup_path}")

        try:
            os.makedirs(backup_path, exist_ok=True)

            # 遍历项目目录
            for root, dirs, files in os.walk(self.project_dir):
                # 过滤目录
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'backup', 'backups']]

                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.project_dir)

                    if not self._should_include(rel_path):
                        continue

                    # 创建目标目录
                    target_dir = os.path.join(backup_path, os.path.dirname(rel_path))
                    os.makedirs(target_dir, exist_ok=True)

                    # 复制文件
                    shutil.copy2(full_path, target_dir)
                    logger.debug(f"备份文件: {rel_path}")

            # 创建备份摘要
            self._create_backup_summary(backup_path, description)

            # 创建恢复镜像
            if self.config['recovery']['create_image_on_sync']:
                self.create_recovery_image(backup_path, description)

            # 清理旧备份
            self._cleanup_old_backups()

            backup_size = self._get_directory_size(backup_path)
            logger.info(f"备份成功，大小: {backup_size}")

            return {
                'success': True,
                'message': '备份成功',
                'backup_path': backup_path,
                'backup_name': backup_name,
                'size': backup_size,
                'timestamp': timestamp,
                'description': description
            }

        except Exception as e:
            logger.error(f"备份失败: {e}")
            return {'success': False, 'message': str(e)}

    def _create_backup_summary(self, backup_path, description):
        """创建备份摘要"""
        summary_path = os.path.join(backup_path, 'backup_summary.txt')
        with open(summary_path, 'w') as f:
            f.write(f"MTSCOS 系统备份摘要\n")
            f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"备份路径: {backup_path}\n")
            f.write(f"描述: {description}\n")
            f.write(f"\n备份内容:\n")
            f.write(f"- 项目源代码\n")
            f.write(f"- 配置文件\n")
            f.write(f"- 脚本文件\n")
            f.write(f"- 文档文件\n")

    def _get_directory_size(self, directory):
        """获取目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)

        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.2f} KB"
        else:
            return f"{total_size / (1024 * 1024):.2f} MB"

    def _cleanup_old_backups(self):
        """清理旧备份"""
        backup_dir = self._get_backup_dir()
        max_backups = self.config['backup']['max_backups']

        backup_pattern = os.path.join(backup_dir, 'mtscos_backup_*')
        backups = sorted(glob.glob(backup_pattern), reverse=True)

        if len(backups) <= max_backups:
            return

        old_backups = backups[max_backups:]
        for backup in old_backups:
            if os.path.isdir(backup):
                shutil.rmtree(backup)
                logger.info(f"删除旧备份: {backup}")

    def create_recovery_image(self, source_path=None, description="恢复镜像"):
        """创建恢复镜像"""
        if not self.config['recovery']['enabled']:
            logger.info("恢复镜像已禁用")
            return {'success': False, 'message': '恢复镜像已禁用'}

        recovery_dir = self._get_recovery_dir()
        os.makedirs(recovery_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_name = f"mtscos_recovery_{timestamp}.tar.gz"
        image_path = os.path.join(recovery_dir, image_name)

        # 如果没有指定源路径，使用项目目录
        if source_path is None:
            source_path = self.project_dir

        logger.info(f"创建恢复镜像: {image_path}")

        try:
            with tarfile.open(image_path, 'w:gz') as tar:
                for root, dirs, files in os.walk(source_path):
                    dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]

                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, source_path)

                        if not self._should_include(rel_path):
                            continue

                        tar.add(full_path, arcname=rel_path)

            # 创建镜像元数据
            self._create_image_metadata(image_path, description)

            # 清理旧镜像
            self._cleanup_old_images()

            image_size = self._get_file_size(image_path)
            logger.info(f"恢复镜像创建成功，大小: {image_size}")

            return {
                'success': True,
                'message': '恢复镜像创建成功',
                'image_path': image_path,
                'image_name': image_name,
                'size': image_size,
                'timestamp': timestamp,
                'description': description
            }

        except Exception as e:
            logger.error(f"创建恢复镜像失败: {e}")
            return {'success': False, 'message': str(e)}

    def _create_image_metadata(self, image_path, description):
        """创建镜像元数据"""
        metadata_path = image_path + '.metadata.json'
        metadata = {
            'image_path': image_path,
            'created_at': datetime.now().isoformat(),
            'description': description,
            'source': self.project_dir,
            'version': '1.0'
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _get_file_size(self, filepath):
        """获取文件大小"""
        size = os.path.getsize(filepath)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    def _cleanup_old_images(self):
        """清理旧恢复镜像"""
        recovery_dir = self._get_recovery_dir()
        max_images = self.config['recovery']['max_images']

        image_pattern = os.path.join(recovery_dir, 'mtscos_recovery_*.tar.gz')
        images = sorted(glob.glob(image_pattern), reverse=True)

        if len(images) <= max_images:
            return

        old_images = images[max_images:]
        for image in old_images:
            os.remove(image)
            metadata = image + '.metadata.json'
            if os.path.exists(metadata):
                os.remove(metadata)
            logger.info(f"删除旧镜像: {image}")

    def list_backups(self):
        """列出所有备份"""
        backup_dir = self._get_backup_dir()
        backup_pattern = os.path.join(backup_dir, 'mtscos_backup_*')
        backups = sorted(glob.glob(backup_pattern), reverse=True)

        result = []
        for backup in backups:
            if os.path.isdir(backup):
                summary_path = os.path.join(backup, 'backup_summary.txt')
                description = "自动备份"

                if os.path.exists(summary_path):
                    with open(summary_path, 'r') as f:
                        for line in f:
                            if line.startswith('描述:'):
                                description = line.split(':', 1)[1].strip()
                                break

                result.append({
                    'name': os.path.basename(backup),
                    'path': backup,
                    'size': self._get_directory_size(backup),
                    'description': description,
                    'timestamp': os.path.basename(backup).replace('mtscos_backup_', '')
                })

        return result

    def list_recovery_images(self):
        """列出所有恢复镜像"""
        recovery_dir = self._get_recovery_dir()
        image_pattern = os.path.join(recovery_dir, 'mtscos_recovery_*.tar.gz')
        images = sorted(glob.glob(image_pattern), reverse=True)

        result = []
        for image in images:
            metadata_path = image + '.metadata.json'
            description = "恢复镜像"

            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        description = metadata.get('description', description)
                except:
                    pass

            result.append({
                'name': os.path.basename(image),
                'path': image,
                'size': self._get_file_size(image),
                'description': description,
                'timestamp': os.path.basename(image).replace('mtscos_recovery_', '').replace('.tar.gz', '')
            })

        return result

    def restore_backup(self, backup_name, target_dir=None):
        """恢复备份"""
        backup_dir = self._get_backup_dir()
        backup_path = os.path.join(backup_dir, backup_name)

        if not os.path.exists(backup_path):
            return {'success': False, 'message': f"备份不存在: {backup_name}"}

        if target_dir is None:
            target_dir = self.project_dir

        logger.info(f"恢复备份: {backup_name} -> {target_dir}")

        try:
            for root, dirs, files in os.walk(backup_path):
                rel_path = os.path.relpath(root, backup_path)
                target_path = os.path.join(target_dir, rel_path)
                os.makedirs(target_path, exist_ok=True)

                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(target_path, file)
                    shutil.copy2(source_file, target_file)
                    logger.debug(f"恢复文件: {rel_path}/{file}")

            logger.info("备份恢复成功")
            return {'success': True, 'message': '备份恢复成功', 'backup_name': backup_name, 'target_dir': target_dir}

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return {'success': False, 'message': str(e)}

    def restore_image(self, image_name, target_dir=None):
        """从恢复镜像恢复"""
        recovery_dir = self._get_recovery_dir()
        image_path = os.path.join(recovery_dir, image_name)

        if not os.path.exists(image_path):
            return {'success': False, 'message': f"镜像不存在: {image_name}"}

        if target_dir is None:
            target_dir = self.project_dir

        logger.info(f"从镜像恢复: {image_name} -> {target_dir}")

        try:
            with tarfile.open(image_path, 'r:gz') as tar:
                tar.extractall(target_dir)

            logger.info("镜像恢复成功")
            return {'success': True, 'message': '镜像恢复成功', 'image_name': image_name, 'target_dir': target_dir}

        except Exception as e:
            logger.error(f"恢复镜像失败: {e}")
            return {'success': False, 'message': str(e)}

    def run_periodic_backup(self, interval_minutes=None):
        """运行周期性备份"""
        if interval_minutes is None:
            interval_minutes = self.config['backup']['interval_minutes']

        logger.info(f"启动周期性备份，间隔: {interval_minutes}分钟")

        while True:
            try:
                result = self.create_backup()
                if result['success']:
                    logger.info(f"备份成功，下次备份在 {interval_minutes} 分钟后")
                else:
                    logger.error(f"备份失败: {result['message']}")
            except Exception as e:
                logger.error(f"备份循环异常: {e}")

            time.sleep(interval_minutes * 60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='自动备份和恢复管理')
    parser.add_argument('--config', default='sync_config.json', help='配置文件路径')
    parser.add_argument('--backup', action='store_true', help='创建备份')
    parser.add_argument('--image', action='store_true', help='创建恢复镜像')
    parser.add_argument('--list-backups', action='store_true', help='列出所有备份')
    parser.add_argument('--list-images', action='store_true', help='列出所有恢复镜像')
    parser.add_argument('--restore-backup', help='恢复指定备份')
    parser.add_argument('--restore-image', help='从指定镜像恢复')
    parser.add_argument('--periodic', action='store_true', help='启动周期性备份')

    args = parser.parse_args()

    backup_manager = BackupManager(args.config)

    if args.list_backups:
        backups = backup_manager.list_backups()
        for b in backups:
            print(f"{b['name']} - {b['size']} - {b['description']}")

    elif args.list_images:
        images = backup_manager.list_recovery_images()
        for i in images:
            print(f"{i['name']} - {i['size']} - {i['description']}")

    elif args.backup:
        result = backup_manager.create_backup()
        print(f"备份结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.image:
        result = backup_manager.create_recovery_image()
        print(f"镜像创建结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.restore_backup:
        result = backup_manager.restore_backup(args.restore_backup)
        print(f"恢复结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.restore_image:
        result = backup_manager.restore_image(args.restore_image)
        print(f"恢复结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.periodic:
        backup_manager.run_periodic_backup()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
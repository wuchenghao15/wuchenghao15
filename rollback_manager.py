#!/usr/bin/env python3
"""
Rollback记录点管理模块
处理系统回滚记录点的创建、管理和回滚操作
"""

import os
import sys
import json
import logging
import subprocess
import time
import glob
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class RollbackManager:
    """回滚管理器"""

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
            'rollback': {
                'enabled': True,
                'create_on_backup': True,
                'create_on_sync': True,
                'max_rollback_points': 50,
                'rollback_dir': '${HOME}/MTSCOS_Rollback'
            }
        }

    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.expanduser(self.config.get('logging', {}).get('log_dir', '~/MTSCOS_Sync_Logs'))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"rollback_{datetime.now().strftime('%Y%m%d')}.log")

        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _expand_path(self, path):
        """扩展路径中的环境变量"""
        return os.path.expandvars(os.path.expanduser(path))

    def _get_rollback_dir(self):
        """获取回滚目录"""
        return self._expand_path(self.config['rollback']['rollback_dir'])

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
                raise RuntimeError(f"Command failed with code {result.returncode}")
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"命令超时: {' '.join(cmd)}")
            return "", "Command timed out"
        except Exception as e:
            logger.error(f"命令执行异常: {' '.join(cmd)} - {e}")
            return "", str(e)

    def create_rollback_point(self, reason="自动创建", description=""):
        """创建回滚记录点"""
        if not self.config['rollback']['enabled']:
            logger.info("回滚功能已禁用")
            return {'success': False, 'message': '回滚功能已禁用'}

        rollback_dir = self._get_rollback_dir()
        os.makedirs(rollback_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        point_name = f"rollback_{timestamp}"
        point_path = os.path.join(rollback_dir, point_name)

        logger.info(f"创建回滚记录点: {point_name}")

        try:
            os.makedirs(point_path, exist_ok=True)

            # 获取Git提交信息
            git_commit = ""
            git_branch = ""
            try:
                git_commit, _ = self._run_command(['git', 'rev-parse', 'HEAD'], check=False)
                git_branch, _ = self._run_command(['git', 'branch', '--show-current'], check=False)
            except:
                pass

            # 获取文件清单
            file_list = []
            for root, dirs, files in os.walk(self.project_dir):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.project_dir)
                    file_list.append({
                        'path': rel_path,
                        'size': os.path.getsize(full_path),
                        'mtime': os.path.getmtime(full_path)
                    })

            # 创建回滚点元数据
            rollback_data = {
                'name': point_name,
                'path': point_path,
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'reason': reason,
                'description': description,
                'git_commit': git_commit,
                'git_branch': git_branch,
                'file_count': len(file_list),
                'files': file_list[:1000]
            }

            # 保存元数据
            metadata_path = os.path.join(point_path, 'rollback_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(rollback_data, f, indent=2)

            # 创建文件快照（关键配置文件）
            self._create_file_snapshot(point_path)

            # 清理旧回滚点
            self._cleanup_old_points()

            logger.info(f"回滚记录点创建成功: {point_name}")

            return {
                'success': True,
                'message': '回滚记录点创建成功',
                'point_name': point_name,
                'point_path': point_path,
                'timestamp': timestamp,
                'reason': reason,
                'git_commit': git_commit,
                'file_count': len(file_list)
            }

        except Exception as e:
            logger.error(f"创建回滚记录点失败: {e}")
            return {'success': False, 'message': str(e)}

    def _create_file_snapshot(self, point_path):
        """创建关键文件快照"""
        snapshot_dir = os.path.join(point_path, 'snapshot')
        os.makedirs(snapshot_dir, exist_ok=True)

        key_files = [
            '.env',
            '.env.example',
            'docker-compose.yml',
            'VERSION',
            'sync_config.json'
        ]

        for file in key_files:
            source_path = os.path.join(self.project_dir, file)
            if os.path.exists(source_path):
                import shutil
                shutil.copy2(source_path, snapshot_dir)
                logger.debug(f"快照文件: {file}")

    def _cleanup_old_points(self):
        """清理旧回滚点"""
        rollback_dir = self._get_rollback_dir()
        max_points = self.config['rollback']['max_rollback_points']

        point_pattern = os.path.join(rollback_dir, 'rollback_*')
        points = sorted(glob.glob(point_pattern), reverse=True)

        if len(points) <= max_points:
            return

        old_points = points[max_points:]
        for point in old_points:
            if os.path.isdir(point):
                import shutil
                shutil.rmtree(point)
                logger.info(f"删除旧回滚点: {point}")

    def list_rollback_points(self):
        """列出所有回滚点"""
        rollback_dir = self._get_rollback_dir()
        point_pattern = os.path.join(rollback_dir, 'rollback_*')
        points = sorted(glob.glob(point_pattern), reverse=True)

        result = []
        for point in points:
            if os.path.isdir(point):
                metadata_path = os.path.join(point, 'rollback_metadata.json')
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            result.append({
                                'name': metadata.get('name', os.path.basename(point)),
                                'timestamp': metadata.get('timestamp', ''),
                                'datetime': metadata.get('datetime', ''),
                                'reason': metadata.get('reason', ''),
                                'description': metadata.get('description', ''),
                                'git_commit': metadata.get('git_commit', '')[:7] if metadata.get('git_commit') else '',
                                'git_branch': metadata.get('git_branch', ''),
                                'file_count': metadata.get('file_count', 0),
                                'path': point
                            })
                    except:
                        result.append({
                            'name': os.path.basename(point),
                            'timestamp': os.path.basename(point).replace('rollback_', ''),
                            'reason': '未知',
                            'path': point
                        })
                else:
                    result.append({
                        'name': os.path.basename(point),
                        'timestamp': os.path.basename(point).replace('rollback_', ''),
                        'reason': '未知',
                        'path': point
                    })

        return result

    def get_rollback_point(self, point_name):
        """获取回滚点详细信息"""
        rollback_dir = self._get_rollback_dir()
        point_path = os.path.join(rollback_dir, point_name)

        if not os.path.exists(point_path):
            return None

        metadata_path = os.path.join(point_path, 'rollback_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)

        return None

    def rollback_to_point(self, point_name, dry_run=False):
        """回滚到指定记录点"""
        rollback_dir = self._get_rollback_dir()
        point_path = os.path.join(rollback_dir, point_name)

        if not os.path.exists(point_path):
            return {'success': False, 'message': f"回滚点不存在: {point_name}"}

        metadata_path = os.path.join(point_path, 'rollback_metadata.json')
        if not os.path.exists(metadata_path):
            return {'success': False, 'message': f"回滚点元数据不存在"}

        logger.info(f"回滚到记录点: {point_name}")

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            if dry_run:
                logger.info(f"模拟回滚到 {point_name}")
                return {
                    'success': True,
                    'message': '模拟回滚完成',
                    'dry_run': True,
                    'point_name': point_name,
                    'file_count': metadata.get('file_count', 0),
                    'git_commit': metadata.get('git_commit', '')
                }

            # 如果有Git提交，尝试通过Git回滚
            if metadata.get('git_commit'):
                try:
                    logger.info(f"通过Git回滚到提交: {metadata['git_commit']}")
                    self._run_command(['git', 'checkout', metadata['git_commit']], check=True)
                    logger.info("Git回滚成功")
                except Exception as e:
                    logger.warning(f"Git回滚失败，将尝试文件级回滚: {e}")

            # 恢复关键配置文件
            snapshot_dir = os.path.join(point_path, 'snapshot')
            if os.path.exists(snapshot_dir):
                import shutil
                for file in os.listdir(snapshot_dir):
                    source_path = os.path.join(snapshot_dir, file)
                    target_path = os.path.join(self.project_dir, file)
                    shutil.copy2(source_path, target_path)
                    logger.info(f"恢复配置文件: {file}")

            logger.info(f"回滚成功: {point_name}")

            return {
                'success': True,
                'message': '回滚成功',
                'point_name': point_name,
                'git_commit': metadata.get('git_commit', ''),
                'file_count': metadata.get('file_count', 0)
            }

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {'success': False, 'message': str(e)}

    def create_pre_sync_rollback(self):
        """同步前创建回滚点"""
        if self.config['rollback']['create_on_sync']:
            return self.create_rollback_point(
                reason="sync_before",
                description="同步前自动创建的回滚点"
            )
        return {'success': False, 'message': '同步回滚点创建已禁用'}

    def create_post_backup_rollback(self):
        """备份后创建回滚点"""
        if self.config['rollback']['create_on_backup']:
            return self.create_rollback_point(
                reason="backup_after",
                description="备份后自动创建的回滚点"
            )
        return {'success': False, 'message': '备份回滚点创建已禁用'}


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Rollback记录点管理')
    parser.add_argument('--config', default='sync_config.json', help='配置文件路径')
    parser.add_argument('--create', action='store_true', help='创建回滚点')
    parser.add_argument('--list', action='store_true', help='列出所有回滚点')
    parser.add_argument('--rollback', help='回滚到指定回滚点')
    parser.add_argument('--dry-run', action='store_true', help='模拟回滚')

    args = parser.parse_args()

    rollback_manager = RollbackManager(args.config)

    if args.list:
        points = rollback_manager.list_rollback_points()
        for p in points:
            print(f"{p['name']} - {p['reason']} - Git: {p.get('git_commit', '')}")

    elif args.create:
        result = rollback_manager.create_rollback_point()
        print(f"创建结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    elif args.rollback:
        result = rollback_manager.rollback_to_point(args.rollback, args.dry_run)
        print(f"回滚结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
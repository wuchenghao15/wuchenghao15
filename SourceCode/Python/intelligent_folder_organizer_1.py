#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件夹归类与文档结构监控脚本

功能：
1. 自动归类项目中的文件到合适的文件夹
2. 监控文档文件夹的逻辑树合理性
3. 提供报告生成功能
4. 支持定时自动执行

import os
import re
# JSON import removed - using database
import shutil
import datetime
import logging
import argparse
import time
import hashlib
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / f'Logs/文件夹整理/folder_organizer_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('folder_organizer')

class FolderOrganizer:
    """智能文件夹管理器"""

    def __init__(self, root_dir, dry_run=False):
        """初始化文件夹管理器

        Args:
            root_dir: 项目根目录
            dry_run: 是否为模拟运行（不实际移动文件）
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run

        # 文件类型映射表
        self.file_type_map = {
            # 源代码文件
            'SourceCode/JavaScript': ['.js', '.jsx', '.ts', '.tsx'],
            'SourceCode/Python': ['.py'],
            'SourceCode/HTML': ['.html'],
            'SourceCode/CSS': ['.css', '.scss', '.sass', '.less'],
            'SourceCode/CSharp': ['.cs'],
            'SourceCode/Java': ['.java'],
            'SourceCode/CPP': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hh', '.hxx', '.h++'],

            # 文档文件
            'Documentation/Markdown': ['.md', '.markdown'],
            'Documentation/PDF': ['.pdf'],
            'Documentation/Word': ['.docx', '.doc'],
            'Documentation/Excel': ['.xlsx', '.xls', '.csv'],
            'Documentation/Text': ['.txt', '.text', '.log'],

            # 配置文件
            'Configuration': ['.json', '.yaml', '.yml', '.xml', '.conf', '.config', '.ini'],

            # 脚本文件
            'Scripts': ['.sh', '.bat', '.ps1', '.bash'],

            # 数据文件
            'Data': ['.db', '.sqlite', '.sql', '.mdb', '.accdb'],

            # 图像文件
            'Media/Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],

            # 备份文件
            'Backups': ['.bak', '.backup', '.zip', '.rar', '.7z', '.tar', '.gz'],
        }

        # 文档文件夹逻辑树结构规范
        self.documentation_structure = {
            'Documentation': {
                'Markdown': {},
                'PDF': {},
                'Word': {},
                'Excel': {},
                'Text': {},
                'Images': {}
            }
        }
        self.stats = {
            'total_files': 0,
            'organized_files': 0,
            'moved_files': 0,
            'errors': 0,
            'unknown_files': 0,
            'structure_issues': []
        }

        """计算文件哈希值，用于检测重复文件"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # 分块读取文件
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {str(e)}")
            return None

    def get_target_folder(self, file_path):
        """根据文件扩展名确定目标文件夹"""
        extension = file_path.suffix.lower()
        for folder, extensions in self.file_type_map.items():
            if extension in extensions:
                return self.root_dir / folder
        return None

    def organize_file(self, file_path):
        """组织单个文件到合适的文件夹"""
        self.stats['total_files'] += 1
        # 跳过已经在正确位置的文件
        if self._is_in_proper_location(file_path):
            logger.debug(f"文件已在正确位置: {file_path}")
            return

        target_folder = self.get_target_folder(file_path)

        if target_folder:
            # 确保目标文件夹存在
            if not self.dry_run:
                target_folder.mkdir(parents=True, exist_ok=True)

            target_path = target_folder / file_path.name

            # 处理文件名冲突
            counter = 1
            base_name = target_path.stem
            extension = target_path.suffix
            while target_path.exists():
                # 检查是否为重复文件
                if target_path.exists() and self.calculate_file_hash(file_path) == self.calculate_file_hash(target_path):
                    logger.info(f"发现重复文件，跳过: {file_path} -> {target_path}")
                    return
                # 重命名文件
                new_name = f"{base_name}_{counter}{extension}"
                target_path = target_folder / new_name
                counter += 1

            if not self.dry_run:
                try:
                    shutil.move(str(file_path), str(target_path))
                    self.stats['moved_files'] += 1
                    logger.info(f"移动文件: {file_path} -> {target_path}")
                except Exception as e:
                    logger.error(f"移动文件失败 {file_path}: {str(e)}")
                logger.info(f"[模拟] 将移动文件: {file_path} -> {target_path}")
        else:
            logger.warning(f"未知文件类型: {file_path}")

    def _is_in_proper_location(self, file_path):
        """检查文件是否已经在正确的位置"""
        for folder, extensions in self.file_type_map.items():
            if file_path.suffix.lower() in extensions:
                expected_folder = self.root_dir / folder
                # 检查文件是否在预期文件夹或其子文件夹中
                try:
                    return expected_folder in file_path.parents
                except Exception:
                    return False
    def organize_folder(self, folder_path):
        """递归组织文件夹中的所有文件"""
        folder_path = Path(folder_path)

        # 排除不需要处理的文件夹
        exclude_folders = {'Backups', 'Logs', 'Build', '.git'}
        if folder_path.name in exclude_folders:
            logger.debug(f"跳过排除的文件夹: {folder_path}")
            return

            for item in folder_path.iterdir():
                if item.is_file() and not self._should_skip_file(item):
                    self.organize_file(item)
                elif item.is_dir():
        except PermissionError as e:
            logger.error(f"权限错误，无法访问文件夹: {folder_path}: {str(e)}")
        except Exception as e:

    def _should_skip_file(self, file_path):
        """检查是否应该跳过某些特殊文件"""
        # 跳过隐藏文件
        if file_path.name.startswith('.'):
            return True
        if file_path.name.endswith('~') or file_path.name.endswith('.tmp'):
            return True
        # 跳过IDE生成的文件
        if file_path.name in ('Thumbs.db', '.DS_Store'):
            return True
        return False

    def check_documentation_structure(self):
        """检查文档文件夹结构的合理性"""
        doc_folder = self.root_dir / 'Documentation'
        if not doc_folder.exists():
            self.stats['structure_issues'].append(f"文档文件夹不存在: {doc_folder}")
            logger.warning(f"文档文件夹不存在: {doc_folder}")
            return

        # 递归检查结构
        self._check_structure_recursive(doc_folder, self.documentation_structure['Documentation'], [])
        # 检查是否有未分类的文档
        for item in doc_folder.iterdir():
                logger.warning(f"未分类的文档文件: {item}")

    def _check_structure_recursive(self, current_path, expected_structure, path_parts):
        # 检查期望的子文件夹是否存在
        for folder_name in expected_structure.keys():
            subfolder_path = current_path / folder_name
            full_path_parts = path_parts + [folder_name]

            if not subfolder_path.exists():
                issue = f"缺失的文档子文件夹: {'/'.join(full_path_parts)} 在 {current_path}"
                self.stats['structure_issues'].append(issue)
                logger.warning(issue)
            elif subfolder_path.exists() and not subfolder_path.is_dir():
                issue = f"路径存在但不是文件夹: {subfolder_path}"
                self.stats['structure_issues'].append(issue)
                logger.warning(issue)
            elif subfolder_path.is_dir():
                # 递归检查子结构
                if expected_structure[folder_name]:
                    self._check_structure_recursive(subfolder_path, expected_structure[folder_name], full_path_parts)

    def generate_report(self):
        """生成整理报告"""
        report_time = datetime.datetime.now()
        report = {
            'timestamp': report_time.isoformat(),
            'dry_run': self.dry_run,
            'root_directory': str(self.root_dir),
            'statistics': self.stats,
            'structure_issues': self.stats['structure_issues']
        }

        report_dir = self.root_dir / 'Documentation/Reports/FolderOrganizer'
        if not self.dry_run:
            report_file = report_dir / f"folder_organizer_report_{report_time.strftime('%Y%m%d_%H%M%S')}.json"
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"报告已保存到: {report_file}")

        # 打印报告到控制台
        logger.info("\n===== 文件夹整理报告 =====")
        logger.info(f"执行时间: {report_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"根目录: {self.root_dir}")
        logger.info(f"模式: {'模拟' if self.dry_run else '实际'}")
        logger.info(f"\n统计信息:")
        logger.info(f"- 总文件数: {self.stats['total_files']}")
        logger.info(f"- 已组织文件数: {self.stats['organized_files']}")
        logger.info(f"- 已移动文件数: {self.stats['moved_files']}")
        logger.info(f"- 错误数: {self.stats['errors']}")

        if self.stats['structure_issues']:
            logger.info(f"\n结构问题 ({len(self.stats['structure_issues'])}):")
            for issue in self.stats['structure_issues']:
                logger.info(f"- {issue}")
        else:
            logger.info("\n结构检查: 通过")

        return report

    def run(self):
        """运行文件夹组织和结构检查"""
        logger.info("开始智能文件夹整理...")
        start_time = time.time()

        # 首先检查文档结构
        logger.info("检查文档文件夹结构...")
        self.check_documentation_structure()

        # 然后整理根目录下的文件
        logger.info(f"开始整理文件，根目录: {self.root_dir}")
        self.organize_folder(self.root_dir)

        # 生成报告
        self.generate_report()

        end_time = time.time()
        logger.info(f"整理完成，耗时: {end_time - start_time:.2f} 秒")

def schedule_organizer(root_dir, interval_hours=24, dry_run=False):
    """定时执行文件夹整理任务

    Args:
        root_dir: 项目根目录
        dry_run: 是否为模拟运行

    try:
        while True:
            organizer = FolderOrganizer(root_dir, dry_run)
            organizer.run()

            sleep_time = interval_hours * 3600
            logger.info(f"等待下次执行，睡眠 {sleep_time} 秒...")
            time.sleep(sleep_time)
    except KeyboardInterrupt:
    except Exception as e:
        logger.error(f"定时任务发生错误: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能文件夹归类与文档结构监控工具')
    parser.add_argument('--root', type=str, default=os.getcwd(),
                        help='项目根目录路径')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟运行，不实际移动文件')
    parser.add_argument('--schedule', type=int, default=0,
                        help='定时执行间隔（小时），0表示仅执行一次')
    parser.add_argument('--verbose', action='store_true',

    args = parser.parse_args()

    # 如果启用详细日志
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    root_dir = Path(args.root).resolve()
    logger.info(f"根目录: {root_dir}")

    if args.schedule > 0:
        # 定时执行模式
        schedule_organizer(root_dir, args.schedule, args.dry_run)
    else:
        # 单次执行模式
        organizer = FolderOrganizer(root_dir, args.dry_run)
        organizer.run()

if __name__ == "__main__":
    main()

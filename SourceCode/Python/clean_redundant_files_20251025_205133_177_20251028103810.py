# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:24
#!/usr/bin/env python3
"""
项目冗余文件检测和清理工具
用于识别并安全删除项目中的冗余文件
"""
import os
import shutil
import logging
import hashlib
# JSON import removed - using database
from datetime import datetime
import re

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f"clean_redundant_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('clean_redundant')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 冗余文件类型定义
REDUNDANT_PATTERNS = {
    'backup': {
        'description': '备份文件',
        'patterns': ['*.bak', '*.backup', '*~'],
        'delete': True
    },
    'temp': {
        'description': '临时文件',
        'patterns': ['*.tmp', '*.temp', 'temp/', '.temp/', '*.swp', '*.swo'],
        'delete': True
    },
        'description': '旧日志文件（保留最近7天）',
        'delete': False,  # 特殊处理，只删除旧日志
        'days_to_keep': 7
    },
    'dist_build': {
        'description': '构建输出目录',
        'delete': False  # 默认不删除，需要确认
    },
    'system': {
        'description': '系统文件',
        'delete': True
    },
        'description': '包缓存目录',
        'patterns': ['__pycache__/', '.pytest_cache/', '.alpackages/'],
    },
        'description': 'IDE配置文件',
        'patterns': ['.idea/', '.vscode/', '*.suo', '*.ntvs*', '*.njsproj', '*.sln'],
        'delete': False  # 默认不删除，需要确认
    'git': {
        'description': 'Git相关文件（不包括.git目录本身）',
        'patterns': ['.gitattributes', '.gitignore', '.gitmodules', '.gitkeep'],
        'delete': False  # 默认不删除，需要确认
    'temp_dir': {
        'description': '临时目录',
        'patterns': ['temp/', 'tmp/', 'TEMP/', 'TMP/'],
        'delete': True
# 需要保留的目录（相对于项目根目录）
KEEP_DIRECTORIES = [
    '.git/',  # 版本控制目录
    'Logs/',  # 日志目录
    'MyData/',  # 数据目录
    'MyPages/',  # 页面目录
    'MyScript/',  # 脚本目录
    'MyStyle/',  # 样式目录
    'MyTools/',  # 工具目录
    'deploy_site/',  # 部署目录
    'init-mssql/',  # 数据库初始化目录
    'users_data/',  # 用户数据目录

KEEP_FILES = [
    'README.md',
    'VERSION',
    'DEPLOYMENT_GUIDE.md',
    'docker-compose.yml',
    'package.json',
    'build.py',
    'deploy.sh',
    'clean_redundant_files.py',  # 保留自身
]

def should_keep(path):
    """
    """
    for keep_dir in KEEP_DIRECTORIES:
        if path.startswith(os.path.join(PROJECT_ROOT, keep_dir)):
            return True

    # 检查是否是保留文件
    for keep_file in KEEP_FILES:
        if path == os.path.join(PROJECT_ROOT, keep_file):
            return True

    return False


def match_pattern(path, pattern):
    """
    """
    if pattern.endswith('/'):
        pattern_dir = pattern[:-1]
        # 检查是否是该目录或其子目录
        parts = path.split(os.sep)
        return pattern_dir in parts

    # 文件通配符模式
    if '*' in pattern:
        # 简单的通配符匹配（仅支持*在开头或结尾）
        if pattern.startswith('*'):
            return path.endswith(pattern[1:])
        elif pattern.endswith('*'):

    # 精确文件名匹配
    return os.path.basename(path) == pattern


def get_file_age_days(file_path):
    """
    """
        return 0

    mtime = os.path.getmtime(file_path)
    now = datetime.now().timestamp()
    days = (now - mtime) / (24 * 3600)
    return days


def is_redundant(path, dry_run=True):
    """
    返回 (是否冗余, 冗余类型描述, 建议操作)
    """
    if should_keep(path):
        return False, None, None

    # 检查各种冗余模式
    for category, config in REDUNDANT_PATTERNS.items():
        for pattern in config['patterns']:
            if match_pattern(path, pattern):
                # 特殊处理旧日志文件
                if category == 'log_old' and path.endswith('.log'):
                    age_days = get_file_age_days(path)
                    if age_days > config.get('days_to_keep', 7):
                        return True, f"{config['description']} (创建于{age_days:.1f}天前)", 'delete'
                    else:
                        return False, None, None

                suggested_action = 'delete' if config['delete'] else 'review'
                return True, config['description'], suggested_action

    # 检查是否是空目录
    if os.path.isdir(path) and not os.listdir(path):
        return True, "空目录", 'delete'

    # 检查是否是临时组织目录
    if os.path.basename(path) == 'ORGANIZED_TEMP':
        return True, "临时组织目录", 'delete'

    return False, None, None


def find_redundant_files(root_dir, max_depth=3):
    """
    """

    # 计算根目录深度
    root_depth = len(root_dir.split(os.sep))

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # 计算当前深度
        current_depth = len(dirpath.split(os.sep)) - root_depth

        if current_depth > max_depth:
            del dirnames[:]  # 清空目录列表，停止递归
            continue

        # 检查目录本身
        is_redun, desc, action = is_redundant(dirpath)
        if is_redun:
            redundant_items.append({
                'path': dirpath,
                'type': 'directory',
                'size': get_dir_size(dirpath) if os.path.isdir(dirpath) else os.path.getsize(dirpath),
                'redundant_type': desc,
            })
            # 如果是冗余目录，不再检查其子内容
            del dirnames[:]
            continue

        # 检查文件
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            is_redun, desc, action = is_redundant(filepath)
            if is_redun:
                redundant_items.append({
                    'path': filepath,
                    'type': 'file',
                    'size': os.path.getsize(filepath),
                    'redundant_type': desc,
                    'suggested_action': action
                })

    return redundant_items


def get_dir_size(path):
    """
    """
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.warning(f"无法计算目录大小 {path}: {str(e)}")
    return total_size

def format_size(size_bytes):
    """
    """
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
        return f"{size_bytes / (1024 * 1024):.2f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def delete_redundant_items(redundant_items, force=False):
    """
        'failed': 0,
        'freed_space': 0,
        'failed_items': []
    }

    for item in redundant_items:
        # 只删除建议删除的项目
        if item['suggested_action'] != 'delete' and not force:
            logger.info(f"跳过 {item['path']} (建议: {item['suggested_action']})")
            stats['skipped'] += 1
            continue

        try:

                shutil.rmtree(item['path'])
            else:
                os.remove(item['path'])

            stats['deleted'] += 1
            stats['freed_space'] += item['size']

        except Exception as e:
            logger.error(f"删除失败 {item['path']}: {str(e)}")
            stats['failed'] += 1
            stats['failed_items'].append({
                'path': item['path'],
                'error': str(e)
            })

    return stats


def generate_report(redundant_items, deletion_stats=None):
    """
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'project_root': PROJECT_ROOT,
        'redundant_summary': {
            'total_items': len(redundant_items),
            'total_size': sum(item['size'] for item in redundant_items),
            'files': len([item for item in redundant_items if item['type'] == 'file']),
            'directories': len([item for item in redundant_items if item['type'] == 'directory'])
        },
        'by_type': {},
        'redundant_items': redundant_items
    }
    # 按冗余类型统计
    for item in redundant_items:
        if item['redundant_type'] not in report['by_type']:
            report['by_type'][item['redundant_type']] = {
                'count': 0,
                'size': 0,
                'files': 0,
                'directories': 0
            }

        report['by_type'][item['redundant_type']]['size'] += item['size']
        if item['type'] == 'file':
            report['by_type'][item['redundant_type']]['files'] += 1
        else:
            report['by_type'][item['redundant_type']]['directories'] += 1

    # 添加删除统计（如果有）
    if deletion_stats:
        report['deletion_stats'] = deletion_stats

    json_report_path = os.path.join(PROJECT_ROOT, f"redundant_files_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
        with open(json_report_path, 'w', encoding='utf-8') as f:
        logger.info(f"JSON报告已生成: {json_report_path}")
    except Exception as e:
        logger.error(f"生成JSON报告失败: {str(e)}")

    # 生成可读文本报告
    txt_report_path = os.path.join(PROJECT_ROOT, f"redundant_files_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
    try:
        with open(txt_report_path, 'w', encoding='utf-8') as f:
            f.write(f"生成时间: {report['timestamp']}\n")
            f.write(f"项目根目录: {report['project_root']}\n")
            f.write("=" * 60 + "\n\n")

            f.write("冗余文件统计:\n")
            f.write(f"  总计项目: {report['redundant_summary']['total_items']}\n")
            f.write(f"  总计大小: {format_size(report['redundant_summary']['total_size'])}\n")
            f.write(f"  文件数: {report['redundant_summary']['files']}\n")
            f.write(f"  目录数: {report['redundant_summary']['directories']}\n\n")
            f.write("按类型统计:\n")
            for rtype, stats in sorted(report['by_type'].items()):
                f.write(f"  {rtype}:\n")
                f.write(f"    数量: {stats['count']} ({stats['files']} 文件, {stats['directories']} 目录)\n")
                f.write(f"    大小: {format_size(stats['size'])}\n")
            f.write("\n")

            if deletion_stats:
                f.write("删除结果:\n")
                f.write(f"  成功删除: {deletion_stats['deleted']}\n")
                f.write(f"  失败: {deletion_stats['failed']}\n")
                f.write(f"  释放空间: {format_size(deletion_stats['freed_space'])}\n\n")

                if deletion_stats['failed_items']:
                    f.write("删除失败的项目:\n")
                    for item in deletion_stats['failed_items']:
                        f.write(f"  {item['path']}: {item['error']}\n")
                    f.write("\n")

            f.write("冗余项目列表:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'路径':<60} {'类型':<10} {'大小':<12}\n")
            f.write("-" * 80 + "\n")
            for item in sorted(redundant_items, key=lambda x: x['size'], reverse=True):
                f.write(f"{os.path.relpath(item['path'], PROJECT_ROOT)[:57]:<60} {item['type'][:9]:<10} {format_size(item['size']):<12}\n")
            f.write("-" * 80 + "\n\n")

            f.write("说明:\n")
            f.write("1. 本报告列出了项目中可能的冗余文件和目录\n")
            f.write("2. 建议在删除前仔细检查每个项目\n")
            f.write("4. 重要文件已被排除在清理范围之外\n")

        logger.info(f"文本报告已生成: {txt_report_path}")
    except Exception as e:
        logger.error(f"生成文本报告失败: {str(e)}")
    return report

def main():
    """
    """
    logger.info(f"项目根目录: {PROJECT_ROOT}")

    # 显示操作提示
    print("=" * 80)
    print("          项目冗余文件清理工具          ")
    print("=" * 80)
    print("注意事项:")
    print("1. 本工具首先进行扫描并生成报告，不会直接删除文件")
    print("2. 扫描完成后，请查看报告确认需要删除的项目")
    print("3. 重要文件和目录已被排除在清理范围之外")
    print("=" * 80)

    # 扫描冗余文件
    print("正在扫描冗余文件...")
    redundant_items = find_redundant_files(PROJECT_ROOT)

    # 生成报告
    report = generate_report(redundant_items)

    # 显示摘要
    print("\n扫描完成！")
    print(f"发现 {report['redundant_summary']['total_items']} 个冗余项目，共 {format_size(report['redundant_summary']['total_size'])}")
    print(f"  - 目录: {report['redundant_summary']['directories']}")
    print("\n请查看生成的报告文件以获取详细信息")

    # 询问是否删除
    delete_prompt = "\n是否要删除这些冗余文件？(y/N): "
    if input(delete_prompt).lower() == 'y':
        print("\n开始删除冗余文件...")
        deletion_stats = delete_redundant_items(redundant_items)

        # 生成更新后的报告
        generate_report(redundant_items, deletion_stats)
        print("\n删除完成！")
        print(f"成功删除: {deletion_stats['deleted']}")
        print(f"删除失败: {deletion_stats['failed']}")
        print(f"跳过项目: {deletion_stats['skipped']}")
        print(f"释放空间: {format_size(deletion_stats['freed_space'])}")
        print("已取消删除操作")

    logger.info("冗余文件扫描完成！")
    return report


    main()

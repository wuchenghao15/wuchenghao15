# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:29
#!/usr/bin/env python3
"""
按照创造者（功能模块）对日志文件进行分类
"""
import os
import shutil
import re
import logging
from datetime import datetime

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"Logs/logs_sorter_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定义日志文件与创造者/模块的映射关系
LOG_CREATOR_MAPPING = {
    'anti_hotlink_update': '防盗链脚本',
    'arduino': 'Arduino模块',
    'auto_backup_js_files': '自动备份',
    'auto_sync': '自动同步',
    'build': '构建系统',
    'clean_redundant': '冗余清理',
    'folder_organizer': '文件夹整理',
    'js_encrypt': 'JavaScript加密',
    'js_monitor': 'JavaScript监控',
    'login': '登录系统',
    'logs_sorter': '日志分类器',  # 用于本脚本自身的日志
    'move_bak_files': '备份工具',
    'mssql_setup': '数据库配置',
    'performance_optimization': '性能优化',
    'register': '注册系统',
    'root_organizer': '根目录整理',
    'verifycode': '验证码系统',
    'version_update': '版本更新'
}

# 日志文件命名模式正则表达式 - 改进版本
LOG_FILE_PATTERN = re.compile(r'^([a-z_]+)')

# 反向映射：从目录名映射到关键词列表
DIR_TO_KEYWORDS = {
    'Arduino模块': ['arduino'],
    'JavaScript加密': ['js_encrypt'],
    'JavaScript监控': ['js_monitor'],
    '登录系统': ['login'],
    '备份工具': ['move_bak_files'],
    '数据库配置': ['mssql_setup'],
    '注册系统': ['register'],
    '验证码系统': ['verifycode'],
    '版本更新': ['version_update'],
    '构建系统': ['build'],
    '防盗链脚本': ['anti_hotlink_update'],
    '日志分类器': ['logs_sorter']
}

    """
    使用关键词匹配而不仅仅是前缀
    """
    if filename == 'README.md' or filename == 'ERROR_LOGGING_GUIDE.md':
        return '文档文件'

    # 检查是否是Python脚本
    if filename.endswith('.py'):
        if filename == 'flatten_logs.py':
            return '日志工具'
        return '未分类'

    # 检查是否是报告文件
    if filename.endswith('.txt') and filename.startswith('logs_sorting_report'):
        return '报告文件'

    # 首先尝试原始的前缀匹配
    match = LOG_FILE_PATTERN.match(filename)
    if match:
        prefix = match.group(1)
        if prefix in LOG_CREATOR_MAPPING:
            return LOG_CREATOR_MAPPING[prefix]

    # 然后尝试关键词匹配
    for dir_name, keywords in DIR_TO_KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename:
                return dir_name

    # 更全面地检查文件名中的关键词
    for keyword, creator in LOG_CREATOR_MAPPING.items():
        if keyword in filename:
            return creator

    return '未分类'

    """
    """
    # 确保所有可能的分类目录都被创建
    all_categories = set(LOG_CREATOR_MAPPING.values())
    # 添加特殊分类目录
    special_categories = ['未分类', '报告文件', '文档文件', '日志工具']
    all_categories.update(special_categories)

    for category in all_categories:
        dir_path = os.path.join(logs_dir, category)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            created_dirs.add(category)
            logger.info(f'创建目录: {dir_path}')
    return created_dirs

def sort_logs_by_creator(logs_dir):
    """
    """
    uncategorized_dir = os.path.join(logs_dir, '未分类')
    if not os.path.exists(uncategorized_dir):
        os.makedirs(uncategorized_dir)
        logger.info(f'创建目录: {uncategorized_dir}')

    # 创建分类目录
    create_creator_directories(logs_dir)

    # 统计信息
    moved_count = 0
    skipped_count = 0
    error_count = 0

    # 首先将未分类目录中的文件移回Logs根目录
    if os.path.exists(uncategorized_dir):
        for filename in os.listdir(uncategorized_dir):
            source_path = os.path.join(uncategorized_dir, filename)
            if os.path.isfile(source_path):
                target_path = os.path.join(logs_dir, filename)
                # 避免覆盖
                if os.path.exists(target_path):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name, ext = os.path.splitext(filename)
                    new_filename = f"{name}_{timestamp}{ext}"
                    target_path = os.path.join(logs_dir, new_filename)
                shutil.move(source_path, target_path)
                logger.info(f'将文件从未分类移回: {filename} -> {os.path.basename(target_path)}')

    # 获取所有日志文件（排除目录和本脚本日志）
    log_files = []
    for filename in os.listdir(logs_dir):
        file_path = os.path.join(logs_dir, filename)
        if os.path.isfile(file_path) and not filename.startswith('logs_sorter_'):
            log_files.append(filename)

    logger.info(f'找到 {len(log_files)} 个日志文件待分类')

    # 遍历日志文件
    for filename in log_files:
        try:
            # 获取创造者信息
            creator = get_creator_from_filename(filename)

            # 目标路径
            if creator == '未分类':
                target_dir = uncategorized_dir
            else:
                target_dir = os.path.join(logs_dir, creator)

            target_path = os.path.join(target_dir, filename)

            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                # 为避免覆盖，添加时间戳
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}_{timestamp}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                logger.warning(f'文件已存在，重命名为: {new_filename}')

            # 移动文件
            source_path = os.path.join(logs_dir, filename)
            shutil.move(source_path, target_path)
            moved_count += 1

            logger.error(f'移动文件 {filename} 时出错: {str(e)}')


def generate_report(moved_count, skipped_count, error_count, logs_dir):
    """
    """
    report_path = os.path.join(logs_dir, report_filename)

        f.write(f"日志分类报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"分类统计:\n")
        f.write(f"  成功移动: {moved_count}\n")
        f.write(f"  跳过文件: {skipped_count}\n")
        f.write(f"  错误文件: {error_count}\n\n")

        f.write("分类详情:\n")
        for creator in LOG_CREATOR_MAPPING.values():
            creator_dir = os.path.join(logs_dir, creator)
            if os.path.exists(creator_dir):
                files = os.listdir(creator_dir)
                if files:
                    f.write(f"  {creator}: {len(files)} 个文件\n")
                    for file in sorted(files):
                        f.write(f"    - {file}\n")
                    f.write("\n")

    logger.info(f'生成分类报告: {report_path}')
    return report_path

def main():
    """
    """
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Logs')

    if not os.path.exists(logs_dir):
        logger.error(f'Logs目录不存在: {logs_dir}')
        return

    logger.info('开始按创造者分类日志文件...')

    # 执行分类
    moved_count, skipped_count, error_count = sort_logs_by_creator(logs_dir)

    # 生成报告
    report_path = generate_report(moved_count, skipped_count, error_count, logs_dir)

    logger.info(f'日志分类完成!')
    logger.info(f'  成功移动: {moved_count}')
    logger.info(f'  跳过文件: {skipped_count}')
    logger.info(f'  错误文件: {error_count}')
    logger.info(f'  报告路径: {report_path}')

if __name__ == '__main__':
    main()

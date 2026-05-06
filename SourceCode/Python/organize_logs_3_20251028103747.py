# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:19
#!/usr/bin/env python3

"""
日志文件自动分类工具
功能：将Logs目录根目录下的日志文件根据文件名关键词分类到相应的子目录中
无法分类的文件将被移动到"其他"目录
"""
import os
import shutil
import re
import logging
from datetime import datetime

# 设置日志配置
LOG_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Logs"
LOG_FILE = os.path.join(LOG_DIR, "日志分类器", "logs_organizer.log")

# 创建日志目录
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("LogsOrganizer")

# 定义分类规则：关键词 -> 目标目录
CATEGORIES = {
    'auto_sync': '自动同步',
    'logs_sorter': '日志分类器',
    'logs_sorting_report': '报告文件',
    'test': '其他',
    'backup': '备份工具',
    'performance': '性能优化',
    'clean': '冗余清理',
    'organizer': '文件夹整理',
    'root_organizer': '根目录整理',
    'error_log': '错误日志',
    'build': '构建系统',
    'encrypt': 'JavaScript加密',
    'monitor': 'JavaScript监控',
    'anti_hotlink': '防盗链脚本',
    'version': '版本更新',
    'login': '登录系统',
    'register': '注册系统',
    'verifycode': '验证码系统',
    'arduino': 'Arduino模块',
    'mssql': '数据库配置',
    'database': '数据库配置'
}

def get_category(filename):
    """
    """
    for keyword, category in CATEGORIES.items():
        if keyword in filename_lower:
            return category
    # 无法分类的文件归为其他
    return "其他"

def ensure_directory_exists(directory):
    """
    """
    logger.debug(f"确保目录存在: {directory}")

def move_file(source, destination):
    """
    """
        # 文件已存在，添加时间戳避免覆盖
        base_name, ext = os.path.splitext(destination)
        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
        destination = f"{base_name}{timestamp}{ext}"
        logger.info(f"文件已存在，使用新名称: {os.path.basename(destination)}")

    try:
        shutil.move(source, destination)
        logger.info(f"移动成功: {os.path.basename(source)} -> {os.path.basename(destination)}")
        return True
    except Exception as e:
        logger.error(f"移动失败: {os.path.basename(source)} -> {e}")
        return False

def organize_logs():
    """
    """

    # 确保"其他"目录存在
    other_dir = os.path.join(LOG_DIR, "其他")
    ensure_directory_exists(other_dir)

    # 统计信息
    total_files = 0
    moved_files = 0
    failed_files = 0
    category_stats = {}

    # 获取LOG_DIR目录下的所有文件（不包括子目录）
    for item in os.listdir(LOG_DIR):
        item_path = os.path.join(LOG_DIR, item)

        # 跳过目录
        if os.path.isdir(item_path):
            continue

        # 跳过隐藏文件
        if item.startswith('.'):
            continue

        # 跳过日志分类器自身的日志文件
        if item_path == LOG_FILE:
            continue

        total_files += 1
        logger.info(f"处理文件: {item}")

        # 确定分类
        category_dir = os.path.join(LOG_DIR, category)
        ensure_directory_exists(category_dir)

        destination_path = os.path.join(category_dir, item)
        if move_file(item_path, destination_path):
            moved_files += 1
            # 更新统计信息
            category_stats[category] = category_stats.get(category, 0) + 1
        else:
            failed_files += 1

    # 生成报告
    logger.info(f"\n===== 整理报告 =====")
    logger.info(f"总文件数: {total_files}")
    logger.info(f"成功移动: {moved_files}")
    logger.info(f"移动失败: {failed_files}")
    logger.info("\n分类统计:")
    for category, count in sorted(category_stats.items()):
        logger.info(f"  {category}: {count} 个文件")
    logger.info("====================\n")

    return {
        "total": total_files,
        "moved": moved_files,
        "failed": failed_files,
        "categories": category_stats
    }

def main():
    """
    """
        start_time = datetime.now()
        logger.info(f"日志分类器启动 - 时间: {start_time}")

        # 执行分类
        result = organize_logs()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"日志分类完成 - 耗时: {duration:.2f} 秒")
        logger.info(f"处理结果: {result['moved']}/{result['total']} 个文件成功移动")

        logger.error(f"分类过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()

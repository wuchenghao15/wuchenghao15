# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:07
#!/usr/bin/env python3

"""
增强版日志文件自动分类工具
功能：
1. 根据文件名关键词和模式分类日志文件
2. 支持处理子目录中的日志文件
3. 按错误类型、日期等多维度分类
4. 提供详细的统计报告
5. 智能处理文件冲突
"""
import os
import shutil
import re
import logging
from datetime import datetime
# JSON import removed - using database
# 设置日志配置
LOG_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Logs"
LOG_FILE = os.path.join(LOG_DIR, "日志管理", "enhanced_log_organizer.log")
REPORT_FILE = os.path.join(LOG_DIR, "日志管理", "organize_report.json")

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

logger = logging.getLogger("EnhancedLogsOrganizer")

# 定义分类规则：
# 1. 精确关键词匹配
EXACT_KEYWORDS = {
    '403_error': 'errors_403',
    '404_error': 'errors_404',
    'css_error': 'errors_css',
    'network_error': 'errors_network',
    'script_error': 'errors_script',
    'other_error': 'errors_other',
    'login_2025': '登录系统',
    'register_': '注册系统',
    'auto_sync': '自动同步',
    'backup_service': '备份工具',
    'monitor_': '系统监控',
    'log_manager': '日志管理',
    'quick_fix': '冗余清理',
    'build_': '构建系统',
    'encrypt_js': 'JavaScript加密',
    'js_monitor': 'JavaScript监控',
    'version_update': '版本更新',
    'update_version': '版本更新',
    'mssql_setup': '数据库配置',
    'error_log_processor': '错误日志',
    'fix_remaining_tasks': '冗余清理',
    'organize_and_update': '文件夹整理',
    'rename_and_optimize': '文件夹整理',
    'unify_logs': '日志管理',
    'log_organizer': '日志管理',
    'performance_': '性能优化',
    'test_2025': '其他测试'
}

# 2. 正则表达式模式匹配
REGEX_PATTERNS = [
    (r'^login_\d{4}-\d{2}-\d{2}', '登录系统'),
    (r'^register_\d{4}-\d{2}-\d{2}', '注册系统'),
    (r'^auto_sync_\d{4}-\d{2}-\d{2}', '自动同步'),
    (r'^test_\d{4}-\d{2}-\d{2}', '其他测试'),
]

GENERAL_KEYWORDS = {
    'backup': '备份工具',
    'performance': '性能优化',
    'clean': '冗余清理',
    'organizer': '文件夹整理',
    'organize': '文件夹整理',
    'error': '错误日志',
    'build': '构建系统',
    'encrypt': 'JavaScript加密',
    'monitor': 'JavaScript监控',
    'version': '版本更新',
    'login': '登录系统',
    'register': '注册系统',
    'verify': '验证码系统',
    'arduino': 'Arduino模块',
    'mssql': '数据库配置',
    'database': '数据库配置',
    'sync': '自动同步',
    'test': '其他测试',
    '优化': '性能优化',
    '备份': '备份工具',
    '清理': '冗余清理',
    '整理': '文件夹整理',
    '错误': '错误日志',
    '构建': '构建系统',
    '监控': '系统监控',
    '版本': '版本更新',
    '登录': '登录系统',
    '注册': '注册系统',
    '数据库': '数据库配置',
    '同步': '自动同步',
    '测试': '其他测试'
}

# 4. 按文件扩展名分类
    '.log': '日志文件',
    '.py': 'Python脚本',
    '.js': 'JavaScript监控',
    '.json': '配置文件',
    '.md': '文档文件',
    '.txt': '文本文件',
    '.html': 'HTML文件',
    '.css': 'CSS文件',
    '.sh': 'Shell脚本'
}

def get_category(filename):
    优先级：精确关键词 > 正则表达式 > 通用关键词 > 文件扩展名 > 其他
    """

    # 1. 检查精确关键词
    for keyword, category in EXACT_KEYWORDS.items():
        if keyword in filename_lower:
            return category

    # 2. 检查正则表达式模式
    for pattern, category in REGEX_PATTERNS:
        if re.match(pattern, filename):
            return category

    # 3. 检查通用关键词
    for keyword, category in GENERAL_KEYWORDS.items():
        if keyword in filename_lower:
            return category

    _, ext = os.path.splitext(filename_lower)
    if ext in EXTENSION_CATEGORIES:
        return EXTENSION_CATEGORIES[ext]
    # 无法分类的文件归为其他

def get_date_from_filename(filename):
    """
    """
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if date_match:
        return date_match.group(1)

    # 匹配 YYYYMMDD 格式
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        date_str = date_match.group(1)
        # 转换为 YYYY-MM-DD 格式
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    return None

def ensure_directory_exists(directory):
    """
    """
    logger.debug(f"确保目录存在: {directory}")

    """
    """
        # 文件已存在，添加时间戳避免覆盖
        base_name, ext = os.path.splitext(destination)
        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S_%f")[:-3]  # 添加毫秒以确保唯一性
        destination = f"{base_name}{timestamp}{ext}"
        logger.info(f"文件已存在，使用新名称: {os.path.basename(destination)}")

    try:
        # 确保目标目录存在
        ensure_directory_exists(os.path.dirname(destination))

        # 移动文件
        shutil.move(source, destination)
        logger.info(f"移动成功: {os.path.basename(source)} -> {os.path.basename(destination)}")
        return True
    except Exception as e:
        logger.error(f"移动失败: {os.path.basename(source)} -> {str(e)}")
        return False

def should_process_file(file_path, processed_files):
    """
    """
    if os.path.basename(file_path).startswith('.'):
        return False

    # 跳过脚本自身的日志文件
    if file_path == LOG_FILE or file_path == REPORT_FILE:
        return False

    # 跳过已经处理过的文件
    if file_path in processed_files:
        return False

    return True

def organize_logs(include_subdirs=True, process_all_extensions=False):
    """

    参数:
    include_subdirs: 是否处理子目录中的文件
    process_all_extensions: 是否处理所有文件类型（默认只处理.log文件和脚本文件）
    """

    # 确保必要的目录存在
    base_dirs = ["其他", "日志管理"]
        ensure_directory_exists(os.path.join(LOG_DIR, dir_name))

    # 统计信息
        "total_files": 0,
        "failed_files": 0,
        "skipped_files": 0,
        "categories": {},
        "date_distribution": {},
        "extension_distribution": {},
        "errors": []
    }

    # 已处理文件集合，避免重复处理
    processed_files = set()

    # 遍历目录
    walk_args = [LOG_DIR]
    if not include_subdirs:
        walk_args.append(False)  # topdown=False 不是我们想要的，这里需要单独处理

    for root, dirs, files in os.walk(*walk_args):
        # 如果不处理子目录，只处理根目录
        if not include_subdirs and root != LOG_DIR:
            continue

        if any(excluded in root for excluded in ["Backups", "Logs_Archive", "Old_Logs"]):
            continue

        for filename in files:
            file_path = os.path.join(root, filename)

            # 检查是否应该处理该文件
            if not should_process_file(file_path, processed_files):
                stats["skipped_files"] += 1
                continue

            # 检查文件扩展名
            _, ext = os.path.splitext(filename)
            if not process_all_extensions and ext not in [".log", ".py", ".js", ".sh"]:
                stats["skipped_files"] += 1
                continue

            stats["total_files"] += 1
            processed_files.add(file_path)
            logger.info(f"处理文件: {os.path.relpath(file_path, LOG_DIR)}")

            try:
                # 确定分类
                category = get_category(filename)
                category_dir = os.path.join(LOG_DIR, category)

                # 尝试从文件名提取日期
                if date_str:
                    # 如果有日期信息，创建日期子目录
                    destination_dir = os.path.join(category_dir, date_str)
                    # 更新日期分布统计
                    stats["date_distribution"][date_str] = stats["date_distribution"].get(date_str, 0) + 1
                else:
                    destination_dir = category_dir
                # 移动文件
                destination_path = os.path.join(destination_dir, filename)
                if move_file(file_path, destination_path):
                    stats["moved_files"] += 1
                    # 更新分类统计
                    # 更新扩展名统计
                else:
                    stats["failed_files"] += 1
                    stats["errors"].append(f"移动失败: {os.path.basename(file_path)}")

            except Exception as e:
                logger.error(f"处理文件时出错: {filename} -> {str(e)}")
                stats["failed_files"] += 1
                stats["errors"].append(f"处理错误: {filename} - {str(e)}")

    # 生成并保存报告
    generate_report(stats)

    return stats

    """
    """
    report_content = {
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

    # 保存到文件
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report_content, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存到: {REPORT_FILE}")
    except Exception as e:
        logger.error(f"保存报告失败: {str(e)}")

    # 输出到日志
    logger.info(f"总文件数: {stats['total_files']}")
    logger.info(f"成功移动: {stats['moved_files']}")
    logger.info(f"移动失败: {stats['failed_files']}")
    logger.info(f"跳过文件: {stats['skipped_files']}")

    for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):

    if stats['date_distribution']:
        logger.info("\n日期分布:")
        for date, count in sorted(stats['date_distribution'].items(), reverse=True):
            logger.info(f"  {date}: {count} 个文件")

    if stats['extension_distribution']:
        logger.info("\n扩展名分布:")
        for ext, count in sorted(stats['extension_distribution'].items()):
            logger.info(f"  {ext}: {count} 个文件")

    if stats['errors']:
        logger.info("\n错误列表:")
        for error in stats['errors'][:10]:  # 只显示前10个错误
            logger.info(f"  - {error}")
        if len(stats['errors']) > 10:
            logger.info(f"  ... 还有 {len(stats['errors']) - 10} 个错误")

    logger.info("====================\n")

def clean_empty_directories():
    """
    """
    empty_dirs = []

    # 遍历所有目录，从最深层开始
    for root, dirs, files in os.walk(LOG_DIR, topdown=False):
        # 跳过根目录和特定保护目录
        if root == LOG_DIR or any(protected in root for protected in ["Backups", "Logs_Archive", "Old_Logs"]):
            continue

        # 检查是否为空目录
        if not dirs and not files:
            empty_dirs.append(root)
            try:
                os.rmdir(root)
                logger.info(f"已删除空目录: {os.path.relpath(root, LOG_DIR)}")
            except Exception as e:
                logger.error(f"删除空目录失败: {os.path.relpath(root, LOG_DIR)} -> {str(e)}")

    logger.info(f"清理完成，共删除 {len(empty_dirs)} 个空目录")
    return empty_dirs

def main():
    """
    """
        start_time = datetime.now()
        logger.info(f"增强版日志分类器启动 - 时间: {start_time}")

        # 执行分类
        stats = organize_logs(include_subdirs=True, process_all_extensions=True)

        # 清理空目录
        clean_empty_directories()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"日志分类完成 - 耗时: {duration:.2f} 秒")
        logger.info(f"处理结果: {stats['moved_files']}/{stats['total_files']} 个文件成功移动")

    except KeyboardInterrupt:
        logger.info("用户中断了操作")
        return 1
    except Exception as e:
        logger.error(f"分类过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main())

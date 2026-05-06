# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:15
#!/usr/bin/env python3
"""
自动整理归类bak文件脚本（修复版）
功能：
- 扫描指定目录中的.bak文件
- 根据原始文件类型和修改日期进行分类
- 显示实时进度条
- 增强错误处理和重试机制
- 只处理未整理的文件
- 生成整理统计报告
"""
import os
import re
import shutil
import time
from datetime import datetime
# JSON import removed - using database
import sys
import traceback

# 配置参数
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 默认为脚本所在目录
SCAN_DIRS = [BASE_DIR, os.path.join(BASE_DIR, 'Logs'), os.path.join(BASE_DIR, 'Backups')]  # 扫描目录
REPORT_FILE = os.path.join(BASE_DIR, 'bak_organize_report_fixed.json')  # 报告文件路径
BACKUP_ROOT_DIR = os.path.join(BASE_DIR, '整理后的备份文件')  # 整理后的备份文件根目录
MAX_RETRY = 3  # 最大重试次数

# 文件类型分类规则
FILE_TYPE_CATEGORIES = {
    # 文档类
    '文档文件': ['.docx', '.doc', '.pdf', '.txt', '.md', '.rtf', '.pptx', '.ppt', '.xlsx', '.xls'],
    # 代码类
    '代码文件': ['.py', '.java', '.js', '.html', '.css', '.cpp', '.c', '.h', '.php', '.go', '.rb', '.swift', '.kt'],
    # 配置类
    '配置文件': ['.ini', '.config', '.json', '.yaml', '.yml', '.xml', '.properties', '.conf', '.cfg'],
    # 图像类
    '图像文件': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
    # 压缩类
    '压缩文件': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
    # 系统类
    '系统文件': ['.dll', '.exe', '.sys', '.ini', '.dat', '.db'],
    # 其他类
    '其他文件': []
}

# 统计数据
stats = {
    'total_files': 0,
    'organized_files': 0,
    'already_organized': 0,
    'errors': 0,
    'retries': 0,
    'by_type': {},
    'by_date': {},
    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'end_time': '',
    'duration': 0
}

def init_stats():
    for category in FILE_TYPE_CATEGORIES.keys():
        stats['by_type'][category] = 0

def get_timestamp():
    """获取当前时间戳，用于文件重命名"""
    return datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]

def get_original_extension(bak_filename):
    """从bak文件名中提取原始文件扩展名"""
    # 增强的命名格式识别
    patterns = [
        r'(.+?)\.bak$',          # file.ext.bak
        r'(.+?)_backup\.bak$',   # file.ext_backup.bak
        r'(.+?)_backup$',         # file.ext_backup
        r'(.+)\~$',              # file.ext~
        r'(.+)\.old$',           # file.ext.old
        r'(.+)\.orig$',          # file.ext.orig
        r'(\w+)_\d{8}\.bak$',  # file_YYYYMMDD.bak
        r'(\w+)_\d{14}\.bak$', # file_YYYYMMDDHHMMSS.bak
        r'(\w+)_\d{8}$',        # file_YYYYMMDD
        r'(\w+)_\d{14}$',       # file_YYYYMMDDHHMMSS
    ]

    for pattern in patterns:
        match = re.match(pattern, bak_filename, re.IGNORECASE)
        if match:
            original_name = match.group(1)
            _, ext = os.path.splitext(original_name)
            return ext.lower() if ext else '.unknown'

    # 直接根据文件名中包含的扩展名提示判断
    common_exts = ['.py', '.js', '.html', '.css', '.txt', '.json', '.xml']
    for ext in common_exts:
        if ext in bak_filename.lower():
            return ext

    return '.unknown'

def categorize_by_extension(extension):
    """根据扩展名对文件进行分类"""
    for category, extensions in FILE_TYPE_CATEGORIES.items():
        if extension in extensions:
            return category
    return '其他文件'

def get_file_modify_date(file_path):
    """获取文件修改日期，格式为YYYY-MM-DD"""
    try:
        modify_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(modify_time).strftime('%Y-%m-%d')
    except Exception:
        return '未知日期'

def ensure_directory(dir_path):
    """确保目录存在，增强错误处理"""
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)  # 使用exist_ok参数避免竞争条件
        print(f"\n创建目录失败 {dir_path}: {e}")

def is_file_already_organized(file_path):
    """检查文件是否已经被整理过"""
    return BACKUP_ROOT_DIR in file_path

def handle_file_conflict(dest_path):
    """处理文件冲突，添加时间戳"""
    if os.path.exists(dest_path):
        file_dir = os.path.dirname(dest_path)
        file_name = os.path.basename(dest_path)
        name, ext = os.path.splitext(file_name)
        new_name = f"{name}_{get_timestamp()}{ext}"
        new_dest_path = os.path.join(file_dir, new_name)
        return new_dest_path
    return dest_path

def move_file_with_retry(file_path, dest_path, retry_count=0):
    """带重试机制的文件移动函数"""
    try:
        # 检查源文件是否存在
        if not os.path.exists(file_path):

        # 确保目标目录存在
        dest_dir = os.path.dirname(dest_path)
        ensure_directory(dest_dir)

        # 处理文件冲突
        final_dest = handle_file_conflict(dest_path)

        # 使用复制后删除的方式替代直接移动，避免某些权限问题
        shutil.copy2(file_path, final_dest)  # copy2保留文件元数据
        os.remove(file_path)  # 复制成功后删除源文件

        return True
    except Exception as e:
        if retry_count < MAX_RETRY:
            stats['retries'] += 1
            retry_delay = (retry_count + 1) * 0.5  # 指数退避
            print(f"\n移动文件失败，{retry_delay:.1f}秒后重试 ({retry_count+1}/{MAX_RETRY}): {e}")
            return move_file_with_retry(file_path, dest_path, retry_count + 1)
        else:
            print(f"\n文件移动失败（已重试{MAX_RETRY}次）: {file_path}")
            print(f"错误详情: {str(e)}")
            return False

def move_file_to_category(file_path, category, date_str):
    """移动文件到对应的分类和日期目录"""
    try:
        # 创建分类和日期目录
        category_dir = os.path.join(BACKUP_ROOT_DIR, category, date_str)

        # 目标路径
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(category_dir, file_name)

        # 使用带重试的移动函数
        if move_file_with_retry(file_path, dest_path):
            # 更新统计
            stats['organized_files'] += 1
            stats['by_type'][category] += 1

            # 更新日期统计
            if date_str not in stats['by_date']:
                stats['by_date'][date_str] = 0
            stats['by_date'][date_str] += 1

            return True
        else:
            stats['errors'] += 1
            return False
    except Exception as e:
        print(f"\n处理文件时出错 {file_path}: {e}")
        print(traceback.format_exc())
        return False
    """显示进度条"""
    if total == 0:

    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    percentage = round(100 * current / total, 1)
    sys.stdout.write(f'\r进度: [{bar}] {percentage}% ({current}/{total} 文件)')
    sys.stdout.flush()

def find_all_bak_files():
    """查找所有的bak文件"""
    bak_files = []

    # 定义更多的备份文件扩展名和模式
    backup_patterns = [
        '.bak', '.old', '.orig', '~',
        '.bak1', '.bak2', '.bak3', '.bak4', '.bak5',
        '_backup', '_BAK', '.BAK', '.OLD', '.ORIG'
    ]

    for scan_dir in SCAN_DIRS:
            print(f"扫描目录不存在: {scan_dir}")
            continue

        print(f"正在扫描目录: {scan_dir}")

        try:
            # 遍历目录
            for root, dirs, files in os.walk(scan_dir):
                # 跳过已经整理过的目录
                    continue

                # 跳过可能包含敏感或系统文件的目录
                if any(skip_dir in root.lower() for skip_dir in ['system', 'tmp', 'temp', '.git', '.svn']):
                    continue

                for file in files:
                    # 查找各种备份文件格式
                    if any(file.lower().endswith(pattern) or pattern in file.lower() for pattern in backup_patterns):
                        file_path = os.path.join(root, file)
                        # 检查文件是否为普通文件且大小合理
                        try:
                            if os.path.isfile(file_path) and os.path.getsize(file_path) < 100 * 1024 * 1024:  # 小于100MB
                                bak_files.append(file_path)
                        except Exception:
            print(f"扫描目录时出错 {scan_dir}: {e}")
            continue


def organize_bak_files():
    start_time = time.time()
    print("开始整理备份文件...")
    print(f"目标目录: {BACKUP_ROOT_DIR}")
    print(f"最大重试次数: {MAX_RETRY}")

    # 初始化统计
    init_stats()

    bak_files = find_all_bak_files()
    stats['total_files'] = len(bak_files)
    print(f"\n找到 {len(bak_files)} 个备份文件")

    if not bak_files:
        print("没有找到备份文件，退出程序")
        return

    # 开始整理
    print("\n开始整理文件:")
    for i, file_path in enumerate(bak_files, 1):
        try:
            # 更新进度条
            progress_bar(i, len(bak_files))

            # 检查是否已经整理过
                stats['already_organized'] += 1
                continue

            # 获取文件名和扩展名
            file_name = os.path.basename(file_path)
            original_ext = get_original_extension(file_name)

            # 分类
            category = categorize_by_extension(original_ext)
            # 获取文件修改日期
            date_str = get_file_modify_date(file_path)

            # 移动文件
            move_file_to_category(file_path, category, date_str)

        except Exception as e:
            print(f"\n处理文件时出错 {file_path}: {e}")
            stats['errors'] += 1
            continue

    # 更新结束时间和持续时间
    stats['duration'] = round(end_time - start_time, 2)

    # 打印完成信息
    print("\n\n整理完成！")
    # 生成报告
    generate_report()

def generate_report():
    """生成整理报告"""
    print("\n===== 整理报告 =====")
    print(f"开始时间: {stats['start_time']}")
    print(f"结束时间: {stats['end_time']}")
    print(f"总耗时: {stats['duration']} 秒")
    print(f"扫描文件总数: {stats['total_files']}")
    print(f"重试次数: {stats['retries']}")
    print(f"错误数量: {stats['errors']}")

    for category, count in stats['by_type'].items():
        if count > 0:
            percentage = round(100 * count / stats['total_files'], 1) if stats['total_files'] > 0 else 0
            print(f"  - {category}: {count} 个文件 ({percentage}%)")

    print("\n按日期统计:")
    sorted_dates = sorted(stats['by_date'].items(), key=lambda x: x[0], reverse=True)[:10]  # 只显示最近10天
    for date, count in sorted_dates:
        print(f"  - {date}: {count} 个文件")
    if len(stats['by_date']) > 10:
        print(f"  ... 等 {len(stats['by_date']) - 10} 个日期")

    print("\n==================\n")

    # 保存报告到文件
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"修复版报告已保存到: {REPORT_FILE}")
    except Exception as e:

def main():
    """主函数"""
    print("备份文件自动整理工具 v2.0（修复版）")
    print(f"整理目录: {BASE_DIR}")

    # 开始整理
    organize_bak_files()

    print("程序执行完毕！")

    main()

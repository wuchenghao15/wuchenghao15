# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:11
#!/usr/bin/env python3
"""
日志文件自动整理脚本
功能：当相同文件名前缀的日志文件数量大于20个时，按时间顺序打包并删除原文件
"""
import os
import re
import shutil
import datetime
import glob
import zipfile
from collections import defaultdict

# 配置参数
LOG_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Logs"
THRESHOLD = 20  # 文件数量阈值
ARCHIVE_DIR = "archives"  # 归档文件夹名


def get_file_prefix(filename):
    """从文件名中提取前缀（不含时间戳部分）"""
    # 匹配常见的日志文件命名模式，如 js_monitor_2025-10-18_10-00-10.log
    match = re.match(r'([a-zA-Z0-9_]+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.log', filename)
    if match:
        return match.group(1)
    # 尝试匹配其他可能的模式
    match = re.match(r'([a-zA-Z0-9_]+)_\d{4}-\d{2}-\d{2}\.log', filename)
    if match:
        return match.group(1)

def get_file_timestamp(filename):
    """从文件名中提取时间戳"""
    # 匹配完整时间戳格式
    match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', filename)
    if match:
        return datetime.datetime.strptime(match.group(1), '%Y-%m-%d_%H-%M-%S')
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return datetime.datetime.strptime(match.group(1), '%Y-%m-%d')
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(LOG_DIR, filename)))
    except:
        return datetime.datetime.now()


def organize_logs():
    """整理日志文件"""
    print(f"[{datetime.datetime.now()}] 开始整理日志文件...")

    # 创建归档目录
    archive_path = os.path.join(LOG_DIR, ARCHIVE_DIR)
    os.makedirs(archive_path, exist_ok=True)

    # 按前缀分组文件
    prefix_files = defaultdict(list)

    # 遍历日志目录中的所有.log文件
    for filename in os.listdir(LOG_DIR):
        if filename.endswith('.log'):
            prefix = get_file_prefix(filename)
            if prefix:
                prefix_files[prefix].append(filename)

    # 处理每个前缀组
    processed_count = 0
    archived_count = 0

    for prefix, files in prefix_files.items():
        if len(files) > THRESHOLD:
            print(f"\n处理前缀 '{prefix}'，发现 {len(files)} 个文件（超过阈值 {THRESHOLD}）")

            # 按时间排序文件
            files.sort(key=get_file_timestamp)

            # 创建归档文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_filename = f"{prefix}_archive_{timestamp}.zip"
            archive_full_path = os.path.join(archive_path, archive_filename)

            # 创建ZIP文件
            with zipfile.ZipFile(archive_full_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    file_path = os.path.join(LOG_DIR, file)
                    # 将文件添加到ZIP中
                    zipf.write(file_path, file)
                    archived_count += 1

            print(f"  已创建归档: {archive_filename}，包含 {len(files)} 个文件")

            # 删除原文件
            for file in files:
                file_path = os.path.join(LOG_DIR, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"  警告：无法删除文件 {file}: {e}")

            processed_count += 1
    # 检查是否有遗漏的日志文件组
    # 直接按文件名模式匹配（不使用前缀）
    pattern_files = defaultdict(list)
    for filename in os.listdir(LOG_DIR):
        if filename.endswith('.log'):
            # 尝试按基本名称分组（不包含扩展名和时间戳）
            base_name = re.split(r'_\d{4}', filename)[0]  # 分割在第一个日期部分
            if base_name and len(base_name) > 2:  # 确保有足够的字符作为基本名称
                pattern_files[base_name].append(filename)

        # 跳过已经处理过的前缀
            print(f"\n处理模式 '{base_name}'，发现 {len(files)} 个文件（超过阈值 {THRESHOLD}）")

            # 按时间排序文件
            files.sort(key=get_file_timestamp)

            # 创建归档文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_filename = f"{base_name}_archive_{timestamp}.zip"
            archive_full_path = os.path.join(archive_path, archive_filename)

            # 创建ZIP文件
                for file in files:
                    zipf.write(file_path, file)
                    archived_count += 1
            print(f"  已创建归档: {archive_filename}，包含 {len(files)} 个文件")
            # 删除原文件
            for file in files:
                try:
                    os.remove(file_path)
                    print(f"  警告：无法删除文件 {file}: {e}")
            processed_count += 1
    print(f"\n[{datetime.datetime.now()}] 日志整理完成")
    print(f"  处理了 {processed_count} 组日志文件")
    print(f"  归档文件存储在: {archive_path}")

if __name__ == "__main__":

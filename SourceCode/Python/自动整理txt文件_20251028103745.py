# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:16
#!/usr/bin/env python3
"""
自动整理归类txt文件脚本
功能：
- 扫描指定目录中的.txt文件
- 根据文件名和内容关键词进行分类
- 创建对应的分类目录并移动文件
- 处理文件冲突（添加时间戳）
- 生成整理统计报告
"""
import os
import re
import shutil
import time
from datetime import datetime
# JSON import removed - using database
# 配置参数
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 默认为脚本所在目录
SCAN_DIRS = [BASE_DIR, os.path.join(BASE_DIR, 'Logs'), os.path.join(BASE_DIR, 'Text')]  # 扫描目录
REPORT_FILE = os.path.join(BASE_DIR, 'txt_organize_report.json')  # 报告文件路径

# 分类规则定义
CATEGORIES = {
    # 技术相关
    '编程开发': {
        'keywords': ['python', 'java', 'javascript', 'html', 'css', '代码', '编程', '算法', '开发', 'debug', 'bug', '修复', '测试'],
        'file_patterns': [r'\.py', r'\.java', r'\.js', r'\.html', r'\.css', r'\.c$', r'\.cpp', r'\.php']
    },
    '配置文件': {
        'keywords': ['config', '配置', 'setting', 'settings', '环境变量', '参数', '配置项'],
        'file_patterns': [r'config', r'setting', r'env']
    },

    '技术文档': {
        'keywords': ['文档', '说明', '教程', '指南', '手册', '帮助', 'document', 'manual', 'guide', 'tutorial'],
        'file_patterns': [r'doc', r'说明', r'教程', r'guide']
    },
    '笔记': {
        'file_patterns': [r'笔记', r'note', r'memo']
    },

    '数据记录': {
        'keywords': ['数据', '记录', '日志', 'log', 'data', '统计', 'analysis', '分析'],
        'file_patterns': [r'data', r'log', r'统计', r'记录']
    },
    '表格数据': {
        'file_patterns': [r'table', r'sheet']
    },

    '系统日志': {
        'keywords': ['系统', 'system', 'error', '错误', 'warning', '警告', 'crash', '崩溃', 'exception'],
        'file_patterns': [r'error', r'log', r'系统', r'warning']
    },
    '备份文件': {
        'file_patterns': [r'backup', r'备份', r'archive']
    },

    '工作计划': {
        'keywords': ['计划', '任务', 'todo', '计划任务', 'schedule', 'planning', 'task'],
        'file_patterns': [r'todo', r'计划', r'task']
    },
    '会议记录': {
        'file_patterns': [r'会议', r'meeting', r'minutes']
    },
    '其他文档': {
        'file_patterns': []
    }
}

# 统计数据
stats = {
    'total_files': 0,
    'organized_files': 0,
    'skipped_files': 0,
    'errors': 0,
    'by_category': {},
    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'end_time': '',
}

# 初始化分类统计
def init_stats():
    for category in CATEGORIES.keys():
        stats['by_category'][category] = 0

def get_timestamp():
    """获取当前时间戳，用于文件重命名"""
    return datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]

    """读取文件内容，用于分类分析"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = ''.join(f.readlines(max_lines))
            return content.lower()
    except Exception as e:
        print(f"读取文件内容失败 {file_path}: {e}")
        stats['errors'] += 1
        return ''

def match_category(file_name, file_content):
    """根据文件名和内容匹配最适合的分类"""
    file_name_lower = file_name.lower()
    file_content_lower = file_content.lower()

    # 首先尝试精确匹配
    for category, rules in CATEGORIES.items():
        if category == '其他文档':
            continue

        # 检查文件名模式
        for pattern in rules['file_patterns']:
            if re.search(pattern, file_name_lower):
                return category

        # 检查关键词
        for keyword in rules['keywords']:
            if keyword.lower() in file_name_lower or keyword.lower() in file_content_lower:
                return category

    # 默认返回'其他文档'
    return '其他文档'

def ensure_directory(dir_path):
    """确保目录存在"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"创建目录: {dir_path}")

def handle_file_conflict(dest_path):
    """处理文件冲突，添加时间戳"""
        file_dir = os.path.dirname(dest_path)
        file_name = os.path.basename(dest_path)
        name, ext = os.path.splitext(file_name)
        new_name = f"{name}_{get_timestamp()}{ext}"
        new_dest_path = os.path.join(file_dir, new_name)
        print(f"文件冲突，重命名为: {new_name}")
        return new_dest_path
    return dest_path

def move_file_to_category(file_path, category):
    """移动文件到对应的分类目录"""
    try:
        # 创建分类目录
        category_dir = os.path.join(BASE_DIR, '整理后的文本文件', category)
        ensure_directory(category_dir)

        # 目标路径
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(category_dir, file_name)

        # 处理文件冲突
        dest_path = handle_file_conflict(dest_path)

        # 移动文件
        print(f"移动文件: {file_name} -> {category}")
        stats['organized_files'] += 1
        stats['by_category'][category] += 1

        return True
    except Exception as e:
        print(f"移动文件失败 {file_path}: {e}")
        stats['errors'] += 1
        return False

def scan_and_organize():
    """扫描目录并整理txt文件"""
    start_time = time.time()
    print("开始扫描和整理txt文件...")

    for scan_dir in SCAN_DIRS:
        if not os.path.exists(scan_dir):
            print(f"扫描目录不存在: {scan_dir}")
            continue
        print(f"扫描目录: {scan_dir}")

        for root, dirs, files in os.walk(scan_dir):
            # 跳过已经整理过的目录
            if '整理后的文本文件' in root:
                continue

            for file in files:
                # 只处理txt文件
                if not file.lower().endswith('.txt'):
                    continue

                file_path = os.path.join(root, file)

                # 读取文件内容
                file_content = read_file_content(file_path)

                # 匹配分类
                category = match_category(file, file_content)

                move_file_to_category(file_path, category)

    # 更新结束时间和持续时间
    end_time = time.time()
    stats['duration'] = round(end_time - start_time, 2)

    # 生成报告
    generate_report()

def generate_report():
    """生成整理报告"""
    print("\n===== 整理报告 =====")
    print(f"开始时间: {stats['start_time']}")
    print(f"结束时间: {stats['end_time']}")
    print(f"总耗时: {stats['duration']} 秒")
    print(f"扫描文件总数: {stats['total_files']}")
    print(f"成功整理: {stats['organized_files']}")
    print(f"跳过文件: {stats['skipped_files']}")
    print("\n按分类统计:")
    for category, count in stats['by_category'].items():
        if count > 0:
            print(f"  - {category}: {count} 个文件")
    print("==================\n")

    # 保存报告到文件
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"报告已保存到: {REPORT_FILE}")
    except Exception as e:
        print(f"保存报告失败: {e}")

def main():
    """主函数"""
    print("文本文件自动整理工具 v1.0")
    print(f"整理目录: {BASE_DIR}")
    print("按回车键开始整理...")

    init_stats()

    # 开始扫描和整理
    scan_and_organize()


if __name__ == "__main__":
    main()

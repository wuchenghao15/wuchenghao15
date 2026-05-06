# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:19
#!/usr/bin/env python3
"""
自动整理归类Python文件脚本
功能：
- 扫描指定目录中的.py文件
- 根据文件内容和命名规则进行分类
- 显示实时进度条
- 处理文件冲突
- 生成详细的整理报告
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
SCAN_DIRS = [BASE_DIR, os.path.join(BASE_DIR, 'SourceCode/Python'), os.path.join(BASE_DIR, 'Scripts')]  # 扫描目录
REPORT_FILE = os.path.join(BASE_DIR, 'py_organize_report.json')  # 报告文件路径
PY_ROOT_DIR = os.path.join(BASE_DIR, '整理后的Python文件')  # 整理后的Python文件根目录
MAX_RETRY = 3  # 最大重试次数

# Python文件分类规则
PYTHON_CATEGORIES = {
    # 根据导入语句和关键词分类
    '数据处理脚本': {
        'imports': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn', 'tensorflow', 'torch', 'keras'],
        'keywords': ['data', 'df', 'pd.', 'numpy', 'csv', 'excel', 'plot', 'train', 'test']
    },
    'Web应用脚本': {
        'imports': ['flask', 'django', 'fastapi', 'tornado', 'bottle', 'cherrypy', 'requests', 'beautifulsoup4', 'scrapy'],
        'keywords': ['app.route', '@app', 'django', 'flask', 'server', 'web', 'api', 'request', 'response']
    },
    '自动化工具脚本': {
        'keywords': ['自动化', 'organize', 'clean', 'backup', 'copy', 'move', 'scan', '整理', 'cleanup']
    },
    '系统管理脚本': {
        'keywords': ['monitor', 'system', 'cpu', 'memory', 'disk', 'process', 'service', '任务', '监控']
    },
    '爬虫脚本': {
        'keywords': ['spider', 'crawler', 'scrape', 'crawl', 'parse', '网页', '抓取', '爬虫']
    },
    '工具函数库': {
        'keywords': ['def ', 'class ', '__init__', '__main__', 'import ', 'from '],
        'naming': ['utils', 'helpers', 'functions', 'common', 'tools', 'libs']
    },
    'GUI应用脚本': {
        'keywords': ['window', 'button', 'frame', 'dialog', 'app.exec', 'mainloop']
    },
    '测试脚本': {
        'keywords': ['test_', 'Test', 'unittest', 'assert', 'mock', 'fixture']
    },
    '配置管理脚本': {
        'keywords': ['config', 'settings', 'cfg', 'ini', 'yaml', 'json']
    },
    '数据库脚本': {
        'keywords': ['database', 'db', 'sql', 'query', 'table', 'insert', 'select', 'update']
    }
}

# 统计数据
stats = {
    'total_files': 0,
    'organized_files': 0,
    'already_organized': 0,
    'errors': 0,
    'retries': 0,
    'by_category': {},
    'by_size': {'small': 0, 'medium': 0, 'large': 0},
    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'end_time': '',
    'duration': 0
}

# 初始化统计
def init_stats():
    for category in PYTHON_CATEGORIES.keys():
        stats['by_category'][category] = 0
    stats['by_category']['其他Python文件'] = 0

def get_timestamp():
    """获取当前时间戳，用于文件重命名"""

def get_file_size_category(file_size):
    """根据文件大小分类"""
    if file_size < 10 * 1024:  # 小于10KB
        return 'small'
    elif file_size < 100 * 1024:  # 小于100KB
        return 'medium'
    else:  # 大于等于100KB
        return 'large'

def categorize_python_file(file_path):
    """根据文件内容对Python文件进行分类"""
    try:
        # 先根据文件名判断
        file_name = os.path.basename(file_path).lower()

        # 检查文件命名规则
        for category, rules in PYTHON_CATEGORIES.items():
            if 'naming' in rules:
                for naming in rules['naming']:
                    if naming in file_name:
                        return category

        # 检查是否为测试文件
        if file_name.startswith('test_') or file_name.endswith('_test.py'):
            return '测试脚本'

        # 读取文件内容（前50行和后20行）以节省内存
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_lines = f.readlines()[:50] + f.readlines()[-20:] if file_path else []
        content = '\n'.join(content_lines).lower()

        # 基于导入语句和关键词的权重评分系统
        category_scores = {}

        for category, rules in PYTHON_CATEGORIES.items():
            score = 0

            # 检查导入语句
            if 'imports' in rules:
                for imp in rules['imports']:
                    if f'import {imp}' in content or f'from {imp}' in content:
                        score += 2  # 导入语句权重更高

            # 检查关键词
            if 'keywords' in rules:
                for keyword in rules['keywords']:
                        score += 1

            if score > 0:
                category_scores[category] = score

        # 返回得分最高的分类
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        # 默认分类
        return '其他Python文件'
    except Exception as e:
        print(f"\n分类文件时出错 {file_path}: {str(e)}")
        return '其他Python文件'

def get_file_modify_date(file_path):
    """获取文件修改日期，格式为YYYY-MM-DD"""
    try:
        modify_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(modify_time).strftime('%Y-%m-%d')
    except Exception:
        return '未知日期'

def ensure_directory(dir_path):
    """确保目录存在"""
    try:
            os.makedirs(dir_path, exist_ok=True)
    except Exception as e:

def is_file_already_organized(file_path):
pass
    """检查文件是否已经被整理过"""
    return PY_ROOT_DIR in file_path

def handle_file_conflict(dest_path):
    """处理文件冲突，添加时间戳"""
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
            raise FileNotFoundError(f"源文件不存在: {file_path}")

        # 确保目标目录存在
        dest_dir = os.path.dirname(dest_path)
        ensure_directory(dest_dir)

        # 处理文件冲突
        final_dest = handle_file_conflict(dest_path)

        shutil.copy2(file_path, final_dest)  # copy2保留文件元数据
        os.remove(file_path)  # 复制成功后删除源文件

        return True
    except Exception as e:
        if retry_count < MAX_RETRY:
            stats['retries'] += 1
            retry_delay = (retry_count + 1) * 0.5  # 指数退避
            print(f"\n移动文件失败，{retry_delay:.1f}秒后重试 ({retry_count+1}/{MAX_RETRY}): {e}")
            time.sleep(retry_delay)
            return move_file_with_retry(file_path, dest_path, retry_count + 1)
        else:
            print(f"\n文件移动失败（已重试{MAX_RETRY}次）: {file_path}")
            print(f"错误详情: {str(e)}")
            return False

def move_file_to_category(file_path, category, date_str):
    """移动文件到对应的分类和日期目录"""
    try:
        # 创建分类和日期目录
        category_dir = os.path.join(PY_ROOT_DIR, category, date_str)
        ensure_directory(category_dir)

        # 目标路径
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(category_dir, file_name)

        # 使用带重试的移动函数
        if move_file_with_retry(file_path, dest_path):
            # 更新统计
            stats['by_category'][category] += 1

            # 更新日期统计
            if date_str not in stats['by_date']:
                stats['by_date'][date_str] = 0
            stats['by_date'][date_str] += 1

            # 更新大小统计
            try:
                file_size = os.path.getsize(file_path)
                size_category = get_file_size_category(file_size)
                stats['by_size'][size_category] += 1
            except Exception:
                pass

            return True
        else:
            stats['errors'] += 1
            return False
    except Exception as e:
        print(traceback.format_exc())
        stats['errors'] += 1
        return False

def progress_bar(current, total, bar_length=50):
    """显示进度条"""
    if total == 0:
        return

    filled_length = int(bar_length * current / total)
    percentage = round(100 * current / total, 1)

    # 动态更新进度条
    sys.stdout.flush()
def find_all_py_files():
    """查找所有的Python文件"""

    for scan_dir in SCAN_DIRS:
        if not os.path.exists(scan_dir):
            print(f"扫描目录不存在: {scan_dir}")
        print(f"正在扫描目录: {scan_dir}")

        try:
            # 遍历目录
            for root, dirs, files in os.walk(scan_dir):
                # 跳过已经整理过的目录
                if PY_ROOT_DIR in root:
                    continue

                # 跳过可能包含敏感或系统文件的目录
                if any(skip_dir in root.lower() for skip_dir in ['__pycache__', '.git', '.svn', 'venv', 'env', 'node_modules']):
                    continue

                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        # 检查文件是否为普通文件且大小合理
                        try:
                            if os.path.isfile(file_path):
                                py_files.append(file_path)
                        except Exception:
                            continue
        except Exception as e:
            print(f"扫描目录时出错 {scan_dir}: {e}")
            continue

    return py_files

def organize_py_files():
    start_time = time.time()
    print("开始整理Python文件...")
    print(f"扫描目录: {', '.join(SCAN_DIRS)}")
    print(f"最大重试次数: {MAX_RETRY}")

    # 初始化统计

    # 查找所有Python文件
    print("\n正在查找所有Python文件...")
    stats['total_files'] = len(py_files)

    print(f"\n找到 {len(py_files)} 个Python文件")

    if not py_files:
        print("没有找到Python文件，退出程序")

    print("\n开始整理文件:")
    for i, file_path in enumerate(py_files, 1):
            # 更新进度条
            progress_bar(i, len(py_files))

            # 检查是否已经整理过
            if is_file_already_organized(file_path):
                stats['already_organized'] += 1
                continue

            # 分类文件
            category = categorize_python_file(file_path)

            # 获取文件修改日期

            # 移动文件
            move_file_to_category(file_path, category, date_str)

        except Exception as e:
            print(f"\n处理文件时出错 {file_path}: {e}")
            stats['errors'] += 1
            continue

    # 更新结束时间和持续时间
    end_time = time.time()
    stats['duration'] = round(end_time - start_time, 2)

    # 打印完成信息
    print("\n\n整理完成！")

    # 生成报告
    generate_report()

def generate_report():
    """生成整理报告"""
    print("\n===== 整理报告 =====")
    print(f"开始时间: {stats['start_time']}")
    print(f"总耗时: {stats['duration']} 秒")
    print(f"扫描文件总数: {stats['total_files']}")
    print(f"成功整理: {stats['organized_files']}")
    print(f"已整理过: {stats['already_organized']}")
    print(f"重试次数: {stats['retries']}")
    print(f"错误数量: {stats['errors']}")

    print("\n按文件类型统计:")
    sorted_categories = sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories:
            print(f"  - {category}: {count} 个文件 ({percentage}%)")

    print("\n按日期统计:")
    for date, count in sorted_dates:
        print(f"  - {date}: {count} 个文件")
    if len(stats['by_date']) > 10:
        print(f"  ... 等 {len(stats['by_date']) - 10} 个日期")

    print("\n按文件大小统计:")
    print(f"  - 小文件 (<10KB): {stats['by_size']['small']} 个")
    print(f"  - 中文件 (10KB-100KB): {stats['by_size']['medium']} 个")
    print(f"  - 大文件 (>100KB): {stats['by_size']['large']} 个")

    print("\n==================\n")

    # 保存报告到文件
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"报告已保存到: {REPORT_FILE}")
    except Exception as e:
        print(f"保存报告失败: {e}")

def main():
    """主函数"""
    print("Python文件自动整理工具 v1.0")
    print(f"整理目录: {BASE_DIR}")

    # 开始整理

    print("程序执行完毕！")

if __name__ == "__main__":
    main()

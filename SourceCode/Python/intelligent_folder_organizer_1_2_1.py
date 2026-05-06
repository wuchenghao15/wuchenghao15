# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:22
#!/usr/bin/env python3
"""
智能归类项目文件夹脚本
根据文件类型、功能和用途对项目文件进行系统性组织
"""
import os
import shutil
import logging
import re
from datetime import datetime
# JSON import removed - using database
# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f"folder_organizer_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('folder_organizer')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 定义文件类型与目标目录的映射
FILE_TYPE_MAPPING = {
    # 文档类
    '.md': 'Documentation/',
    '.txt': 'Documentation/',
    '.pdf': 'Documentation/',
    '.doc': 'Documentation/',
    '.docx': 'Documentation/',
    '.ppt': 'Documentation/',
    '.pptx': 'Documentation/',

    # 代码类
    '.py': 'SourceCode/Python/',
    '.js': 'SourceCode/JavaScript/',
    '.html': 'SourceCode/HTML/',
    '.css': 'SourceCode/CSS/',
    '.sql': 'SourceCode/SQL/',
    '.sh': 'SourceCode/Scripts/',

    # 配置类
    '.json': 'Configuration/',
    '.yaml': 'Configuration/',
    '.yml': 'Configuration/',
    '.ini': 'Configuration/',
    '.conf': 'Configuration/',
    '.env': 'Configuration/',

    # 数据类
    '.db': 'Data/',
    '.sqlite': 'Data/',
    '.csv': 'Data/',
    '.xls': 'Data/',
    '.xlsx': 'Data/',

    # 媒体类
    '.png': 'Media/Images/',
    '.jpg': 'Media/Images/',
    '.jpeg': 'Media/Images/',
    '.gif': 'Media/Images/',
    '.svg': 'Media/Images/',
    '.ico': 'Media/Images/',
    '.mp4': 'Media/Videos/',
    '.avi': 'Media/Videos/',
    '.mp3': 'Media/Audio/',

    # 备份类
    '.bak': 'Backups/',
    '.zip': 'Backups/Archives/',
    '.tar': 'Backups/Archives/',
    '.gz': 'Backups/Archives/',

    # 可执行类
    '.exe': 'Executables/',
    '.bin': 'Executables/',

    # 系统文件（保留但移至系统文件夹）
    '.DS_Store': 'System/',
    '.pid': 'System/',
}

# 特殊文件映射（基于文件名或内容特征）
SPECIAL_FILE_MAPPING = {
    'VERSION': 'Documentation/ProjectInfo/',
    'README.md': 'Documentation/ProjectInfo/',
    'DEPLOYMENT_GUIDE.md': 'Documentation/Deployment/',
    'docker-compose.yml': 'Configuration/Deployment/',
    'package.json': 'Configuration/Project/',
}

DIRECTORY_MAPPING = {
    'MyPages': 'Web/Frontend/Pages/',
    'MyScript': 'Web/Frontend/Scripts/',
    'MyStyle': 'Web/Frontend/Styles/',
    'MyData': 'Web/Data/',
    'MyTools': 'Web/Tools/',
    'MyBackup': 'Backups/Web/',
    'Logs': 'Logs/',
    'deploy_site': 'Deployment/Site/',
    'dist': 'Deployment/Build/',
    'init-mssql': 'Database/MSSQL/',
    'temp': 'System/Temp/',
    'users_data': 'Web/Users/',
    '.alpackages': 'System/Packages/',
    '.snapshots': 'Backups/Snapshots/',
}

CONTENT_PATTERN_MAPPING = {
    r'#!/usr/bin/env python': 'SourceCode/Python/Scripts/',  # Python可执行脚本
    r'<\?php': 'SourceCode/PHP/',  # PHP文件
    r'function\s+\w+\s*\(': 'SourceCode/JavaScript/Functions/',  # JavaScript函数文件
    r'class\s+\w+': 'SourceCode/JavaScript/Classes/',  # JavaScript类文件
    r'<html': 'SourceCode/HTML/',  # HTML文件
    r'\{[^\}]*\}': 'SourceCode/CSS/',  # CSS规则文件
}

IGNORE_PATTERNS = [
    '.git/',
    '.svn/',
    '__pycache__/',
    '.pytest_cache/',
    '.vscode/',
    '.idea/',
    'node_modules/',
    '__MACOSX/',
    '.DS_Store',
    '*.swp',
    '*.swo',
    '*~',
    '.gitignore',
    '.gitattributes',
    'intelligent_folder_organizer.py',  # 排除自身
    'Logs/',  # 排除日志目录
    'Backups/',  # 避免重复备份
]

def should_ignore(path):
    """
    """
        if pattern.endswith('/'):
            # 目录模式
            if path.endswith(pattern):
                return True
            if pattern[:-1] in path.split(os.sep):
                return True
        else:
            # 文件模式
            if pattern.startswith('*'):
                # 通配符模式
                if path.endswith(pattern[1:]):
                    return True
            elif os.path.basename(path) == pattern:
    return False


def get_file_content_signature(file_path, max_lines=5):
    """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return content.lower()
    except Exception as e:
        logger.warning(f"无法读取文件内容 {file_path}: {str(e)}")
        return ''


def get_target_directory(file_path, filename):
    """
    """
    if filename in SPECIAL_FILE_MAPPING:
        return SPECIAL_FILE_MAPPING[filename]

    # 获取文件扩展名
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    # 检查文件类型映射
    if ext in FILE_TYPE_MAPPING:
        return FILE_TYPE_MAPPING[ext]

    # 检查文件内容特征
    content_sig = get_file_content_signature(file_path)
    for pattern, directory in CONTENT_PATTERN_MAPPING.items():
        if re.search(pattern, content_sig):
            return directory

    # 默认目录
    return 'Others/'


def organize_files():
    """
    """
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'project_root': PROJECT_ROOT,
        'organize_summary': {
            'processed': 0,
            'moved': 0,
            'failed': 0,
            'ignored': 0,
            'unclassified': 0
        },
        'category_stats': {},
        'directory_stats': {},
        'failed_files': []
    }

    # 创建组织临时目录
    organize_dir = os.path.join(PROJECT_ROOT, 'ORGANIZED_TEMP')
    if os.path.exists(organize_dir):
        shutil.rmtree(organize_dir)
    os.makedirs(organize_dir)

    # 首先处理现有目录
    for src_dir_name, target_dir_name in DIRECTORY_MAPPING.items():
        src_dir_path = os.path.join(PROJECT_ROOT, src_dir_name)
            target_dir_path = os.path.join(organize_dir, target_dir_name)
            os.makedirs(target_dir_path, exist_ok=True)

            try:
                shutil.copytree(src_dir_path, os.path.join(target_dir_path, src_dir_name))
                logger.info(f"复制目录: {src_dir_name} -> {target_dir_name}/{src_dir_name}")
                report['directory_stats'][src_dir_name] = target_dir_name
                report['organize_summary']['moved'] += 1
            except Exception as e:
                logger.error(f"复制目录失败 {src_dir_name}: {str(e)}")
                report['failed_files'].append({
                    'path': src_dir_name,
                    'error': str(e)
                })
                report['organize_summary']['failed'] += 1

    # 处理根目录下的文件
    for filename in os.listdir(PROJECT_ROOT):
        file_path = os.path.join(PROJECT_ROOT, filename)

        # 跳过目录
            continue

        # 跳过已在目录映射中处理的文件
        if filename in SPECIAL_FILE_MAPPING:
            continue
        # 检查是否应该忽略
        if should_ignore(file_path):
            logger.info(f"忽略文件: {filename}")
            report['organize_summary']['ignored'] += 1
            continue

        report['organize_summary']['processed'] += 1

        # 获取目标目录
        target_dir = get_target_directory(file_path, filename)
        if target_dir == 'Others/':
            report['organize_summary']['unclassified'] += 1

        # 更新分类统计
        if target_dir not in report['category_stats']:
            report['category_stats'][target_dir] = 0
        report['category_stats'][target_dir] += 1
        # 创建目标目录
        os.makedirs(target_path, exist_ok=True)

        # 复制文件
        try:
            dest_file = os.path.join(target_path, filename)
            logger.info(f"复制文件: {filename} -> {target_dir}{filename}")
            report['organize_summary']['moved'] += 1
        except Exception as e:
            logger.error(f"复制文件失败 {filename}: {str(e)}")
            report['failed_files'].append({
                'path': filename,
                'error': str(e)
            })
            report['organize_summary']['failed'] += 1

    # 生成组织报告
    report_file = os.path.join(PROJECT_ROOT, f"organization_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"生成组织报告失败: {str(e)}")

    # 生成可读报告
    readable_report = os.path.join(PROJECT_ROOT, f"organization_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
    try:
            f.write(f"项目文件组织报告\n")
            f.write(f"项目根目录: {report['project_root']}\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"  处理文件数: {report['organize_summary']['processed']}\n")
            f.write(f"  失败: {report['organize_summary']['failed']}\n")
            f.write(f"  未分类: {report['organize_summary']['unclassified']}\n\n")
            f.write("分类统计:\n")
            f.write("\n")
            f.write("目录映射:\n")
            for src, target in sorted(report['directory_stats'].items()):
                f.write(f"  {src} -> {target}\n")
            f.write("\n")

            if report['failed_files']:
                f.write("失败文件列表:\n")
                for item in report['failed_files']:
                    f.write(f"  {item['path']}: {item['error']}\n")
                f.write("\n")

            f.write("组织说明:\n")
            f.write("1. 所有文件已复制到 ORGANIZED_TEMP 目录中，保持原有结构\n")
            f.write("2. 请检查临时目录中的组织结果是否符合预期\n")
            f.write("3. 如果满意，可以手动将 ORGANIZED_TEMP 中的内容移动回项目根目录\n")
            f.write("4. 请确保备份重要数据后再进行实际移动\n")

        logger.info(f"可读组织报告已生成: {readable_report}")
    except Exception as e:
        logger.error(f"生成可读组织报告失败: {str(e)}")

    logger.info("文件组织预览完成！请查看 ORGANIZED_TEMP 目录和组织报告")
    logger.info(f"组织统计: 处理 {report['organize_summary']['processed']} 个文件, "
                f"成功 {report['organize_summary']['moved']}, "
                f"失败 {report['organize_summary']['failed']}, "
                f"忽略 {report['organize_summary']['ignored']}")

    return report


def main():
    """
    """
    logger.info(f"项目根目录: {PROJECT_ROOT}")

    # 显示操作提示
    print("          项目文件智能归类工具          ")
    print("=" * 80)
    print("注意事项:")
    print("2. 所有操作都将在 ORGANIZED_TEMP 目录中进行")
    print("3. 请在执行前确保已备份重要数据")
    print("=" * 80)

    # 执行文件组织
    report = organize_files()

    logger.info("文件智能归类完成！")

    return report


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
MTSCOS AI Project - Markdown文件精简脚本
清理重复、过时、冗余的markdown文档
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 统计信息
stats = {
    'total_before': 0,
    'total_after': 0,
    'deleted': 0,
    'kept': 0,
    'archived': 0,
    'space_saved': 0
}

def count_markdown_files(directory):
    """统计markdown文件数量"""
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                count += 1
    return count

def get_file_size(filepath):
    """获取文件大小"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def delete_markdown_files(directory, patterns, description=""):
    """删除指定模式的markdown文件"""
    deleted = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                # 检查是否匹配模式
                for pattern in patterns:
                    if pattern in file:
                        size = get_file_size(filepath)
                        try:
                            os.remove(filepath)
                            deleted.append(str(filepath))
                            stats['deleted'] += 1
                            stats['space_saved'] += size
                            print(f"  ✓ 删除: {filepath.relative_to(PROJECT_ROOT)}")
                        except Exception as e:
                            print(f"  ✗ 删除失败: {filepath.relative_to(PROJECT_ROOT)} - {e}")
                        break
    return deleted

def delete_directory_markdown(directory, description=""):
    """删除整个目录下的所有markdown文件"""
    deleted = []
    dir_path = PROJECT_ROOT / directory
    if dir_path.exists():
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.md'):
                    filepath = Path(root) / file
                    size = get_file_size(filepath)
                    try:
                        os.remove(filepath)
                        deleted.append(str(filepath))
                        stats['deleted'] += 1
                        stats['space_saved'] += size
                        print(f"  ✓ 删除: {filepath.relative_to(PROJECT_ROOT)}")
                    except Exception as e:
                        print(f"  ✗ 删除失败: {filepath.relative_to(PROJECT_ROOT)} - {e}")
    return deleted

def clean_logs_markdown():
    """清理Logs目录下的重复markdown文件"""
    print("\n" + "="*60)
    print("清理 Logs/ 目录下的重复markdown文件")
    print("="*60)
    
    logs_dir = PROJECT_ROOT / "Logs"
    if not logs_dir.exists():
        print("  Logs目录不存在")
        return
    
    # 删除所有带数字后缀的README文件 (如 README_1.md, README_1_1.md)
    patterns = ['README_', '其他_README', '文档文件_README', 'page_categorization']
    
    for root, dirs, files in os.walk(logs_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                # 检查是否是重复文件（带数字后缀）
                if any(pattern in file for pattern in patterns):
                    # 保留不带数字后缀的原始文件
                    if file != 'README.md' and file != '其他_README.md' and file != '文档文件_README.md':
                        size = get_file_size(filepath)
                        try:
                            os.remove(filepath)
                            stats['deleted'] += 1
                            stats['space_saved'] += size
                            print(f"  ✓ 删除: {filepath.relative_to(PROJECT_ROOT)}")
                        except Exception as e:
                            print(f"  ✗ 删除失败: {filepath} - {e}")

def clean_docs_markdown():
    """清理docs目录下的重复markdown文件"""
    print("\n" + "="*60)
    print("清理 docs/ 目录下的重复markdown文件")
    print("="*60)
    
    # 删除版本更新日志文件
    update_logs_dir = PROJECT_ROOT / "docs" / "Markdown"
    if update_logs_dir.exists():
        for file in os.listdir(update_logs_dir):
            if file.startswith('update_[') and file.endswith('.md'):
                filepath = update_logs_dir / file
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    stats['deleted'] += 1
                    stats['space_saved'] += size
                    print(f"  ✓ 删除版本日志: {file}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {file} - {e}")

def clean_deploy_package_markdown():
    """清理deploy-package目录下的重复markdown文件"""
    print("\n" + "="*60)
    print("清理 deploy-package/docs/ 目录下的重复markdown文件")
    print("="*60)
    
    deploy_docs = PROJECT_ROOT / "deploy-package" / "docs"
    if deploy_docs.exists():
        # 删除整个deploy-package/docs目录下的所有markdown
        for root, dirs, files in os.walk(deploy_docs):
            for file in files:
                if file.endswith('.md'):
                    filepath = Path(root) / file
                    size = get_file_size(filepath)
                    try:
                        os.remove(filepath)
                        stats['deleted'] += 1
                        stats['space_saved'] += size
                        print(f"  ✓ 删除: {filepath.relative_to(PROJECT_ROOT)}")
                    except Exception as e:
                        print(f"  ✗ 删除失败: {filepath} - {e}")

def clean_documentation_markdown():
    """清理Documentation目录下的重复markdown文件"""
    print("\n" + "="*60)
    print("清理 Documentation/Markdown/ 目录下的重复markdown文件")
    print("="*60)
    
    doc_markdown = PROJECT_ROOT / "Documentation" / "Markdown"
    if doc_markdown.exists():
        for file in os.listdir(doc_markdown):
            if file.endswith('.md'):
                filepath = doc_markdown / file
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    stats['deleted'] += 1
                    stats['space_saved'] += size
                    print(f"  ✓ 删除: {file}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {file} - {e}")

def clean_root_temp_markdown():
    """清理根目录下的临时markdown文件"""
    print("\n" + "="*60)
    print("清理根目录下的临时markdown文件")
    print("="*60)
    
    # 临时报告文件
    temp_files = [
        'AI引擎升级报告.md',
        'UPGRADE_GUIDE_v3.4.0.md',
        'UPGRADE_SUMMARY_v3.3.0.md',
        'PERMISSION_CONTROL_UPDATE.md',
        'NINE_YEAR_UPGRADE_SYSTEM_DESIGN.md',
        'NINE_YEAR_USER_GUIDE.md',
        'LEARNING_SYSTEM_SUMMARY.md',
        'FONT_AWESOME_FIX.md',
        'FIX_EXECUTIVE_SUMMARY.md',
        'DEBUG_LOG_API_FIX.md',
        'GRADE_SELECTOR_UPDATE.md',
        'GRADE_UPGRADE_SYSTEM.md',
        'README_JSON_SYNC.md',
        'PROJECT_SPEC.md',
        'GIT_FEATURES.md',
        'port-configuration-guide.md',
        'project_structure.md',
        'SYSTEM_DOCUMENTATION.md',
    ]
    
    for file in temp_files:
        filepath = PROJECT_ROOT / file
        if filepath.exists():
            size = get_file_size(filepath)
            try:
                os.remove(filepath)
                stats['deleted'] += 1
                stats['space_saved'] += size
                print(f"  ✓ 删除临时文档: {file}")
            except Exception as e:
                print(f"  ✗ 删除失败: {file} - {e}")

def clean_docs_temp_markdown():
    """清理docs目录下的临时markdown文件"""
    print("\n" + "="*60)
    print("清理 docs/ 目录下的临时markdown文件")
    print("="*60)
    
    docs_dir = PROJECT_ROOT / "docs"
    if not docs_dir.exists():
        return
    
    temp_files = [
        'UI-优化报告.md',
        'UI-优化报告-修复版.md',
        'automaintain-report.md',
        'self_adaptive_system_doc.md',
    ]
    
    for file in temp_files:
        filepath = docs_dir / file
        if filepath.exists():
            size = get_file_size(filepath)
            try:
                os.remove(filepath)
                stats['deleted'] += 1
                stats['space_saved'] += size
                print(f"  ✓ 删除临时文档: {file}")
            except Exception as e:
                print(f"  ✗ 删除失败: {file} - {e}")

def clean_archives_markdown():
    """清理archives目录下的markdown文件"""
    print("\n" + "="*60)
    print("清理 archives/ 目录下的markdown文件")
    print("="*60)
    
    archives_dir = PROJECT_ROOT / "archives"
    if archives_dir.exists():
        for root, dirs, files in os.walk(archives_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = Path(root) / file
                    size = get_file_size(filepath)
                    try:
                        os.remove(filepath)
                        stats['deleted'] += 1
                        stats['space_saved'] += size
                        print(f"  ✓ 删除: {filepath.relative_to(PROJECT_ROOT)}")
                    except Exception as e:
                        print(f"  ✗ 删除失败: {filepath} - {e}")

def clean_temp_markdown():
    """清理Temp目录下的markdown文件"""
    print("\n" + "="*60)
    print("清理 Temp/ 目录下的markdown文件")
    print("="*60)
    
    temp_dir = PROJECT_ROOT / "Temp"
    if temp_dir.exists():
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = Path(root) / file
                    size = get_file_size(filepath)
                    try:
                        os.remove(filepath)
                        stats['deleted'] += 1
                        stats['space_saved'] += size
                        print(f"  ✓ 删除: {filepath.relative_to(PROJECT_ROOT)}")
                    except Exception as e:
                        print(f"  ✗ 删除失败: {filepath} - {e}")

def clean_trae_markdown():
    """清理.trae/documents目录下的markdown文件"""
    print("\n" + "="*60)
    print("清理 .trae/documents/ 目录下的markdown文件")
    print("="*60)
    
    trae_docs = PROJECT_ROOT / ".trae" / "documents"
    if trae_docs.exists():
        for file in os.listdir(trae_docs):
            if file.endswith('.md'):
                filepath = trae_docs / file
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    stats['deleted'] += 1
                    stats['space_saved'] += size
                    print(f"  ✓ 删除: {file}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {file} - {e}")

def main():
    print("="*60)
    print("MTSCOS AI Project - Markdown文件精简脚本")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 统计清理前的markdown文件数量
    stats['total_before'] = count_markdown_files(PROJECT_ROOT)
    print(f"\n清理前markdown文件总数: {stats['total_before']}")
    
    # 执行清理
    clean_logs_markdown()
    clean_docs_markdown()
    clean_deploy_package_markdown()
    clean_documentation_markdown()
    clean_root_temp_markdown()
    clean_docs_temp_markdown()
    clean_archives_markdown()
    clean_temp_markdown()
    clean_trae_markdown()
    
    # 统计清理后的markdown文件数量
    stats['total_after'] = count_markdown_files(PROJECT_ROOT)
    
    # 输出统计信息
    print("\n" + "="*60)
    print("清理完成统计")
    print("="*60)
    print(f"清理前markdown文件数: {stats['total_before']}")
    print(f"清理后markdown文件数: {stats['total_after']}")
    print(f"删除文件数: {stats['deleted']}")
    print(f"释放空间: {stats['space_saved'] / 1024:.2f} KB")
    print(f"精简率: {(stats['total_before'] - stats['total_after']) / stats['total_before'] * 100:.1f}%")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 列出保留的核心文档
    print("\n" + "="*60)
    print("保留的核心文档")
    print("="*60)
    core_docs = [
        'README.md',
        'CHANGELOG.md',
        'CODE_WIKI.md',
        'AI_CAPABILITIES.md',
        'docs/PROJECT_STARTUP.md',
        'docs/api.md',
        'docs/CHANGELOG.md',
        'docs/guides/',
        'docs/config/',
        'docs/Project/',
        'docs/Architecture/',
        'docs/documents/',
        'flask-app/README.md',
        'flask-app/docs/',
        'exam_app/README.md',
        'frontend/docs/',
        'src/html/docs/',
        'SourceCode/JavaScript/README.md',
    ]
    
    for doc in core_docs:
        doc_path = PROJECT_ROOT / doc
        if doc_path.exists():
            print(f"  ✓ {doc}")

if __name__ == '__main__':
    main()
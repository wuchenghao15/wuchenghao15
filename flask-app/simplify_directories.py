#!/usr/bin/env python3
"""
MTSCOS AI Project - 目录精简脚本
清理各目录下的重复、冗余文件
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 统计信息
stats = {
    'total_files_before': 0,
    'total_files_after': 0,
    'deleted_files': 0,
    'deleted_dirs': 0,
    'space_saved': 0
}

def count_files(directory):
    """统计文件数量"""
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def get_file_size(filepath):
    """获取文件大小"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def is_duplicate_file(filename):
    """判断是否是重复文件（带数字后缀）"""
    # 匹配模式：filename_1.ext, filename_1_1.ext, filename_2_1.ext等
    patterns = [
        r'_\d+$',  # _1, _2, _3
        r'_\d+_\d+$',  # _1_1, _2_1
        r'_\d+_\d+_\d+$',  # _1_1_1
    ]
    
    # 提取文件名（不含扩展名）
    name = Path(filename).stem
    ext = Path(filename).suffix
    
    for pattern in patterns:
        if re.search(pattern + ext, filename) or re.search(pattern, name):
            return True
    
    return False

def clean_logs_directory():
    """清理Logs目录下的重复文件"""
    print("\n" + "="*60)
    print("清理 Logs/ 目录")
    print("="*60)
    
    logs_dir = PROJECT_ROOT / "Logs"
    if not logs_dir.exists():
        print("  Logs目录不存在")
        return
    
    deleted_count = 0
    
    # 需要清理的子目录
    subdirs_to_clean = [
        'Arduino模块',
        'CSS文件',
        'HTML文件',
        'Shell脚本',
        '其他日志',
        '备份工具',
        '文档文件',
        '日志管理',
        '注册系统',
        '版本更新',
        '登录系统',
        '系统监控',
        '自动同步',
        '错误日志',
        '文件夹整理'
    ]
    
    for subdir in subdirs_to_clean:
        subdir_path = logs_dir / subdir
        if not subdir_path.exists():
            continue
        
        print(f"\n  清理 {subdir}/")
        
        for file in os.listdir(subdir_path):
            filepath = subdir_path / file
            
            # 跳过目录
            if filepath.is_dir():
                continue
            
            # 判断是否是重复文件
            if is_duplicate_file(file):
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    stats['deleted_files'] += 1
                    stats['space_saved'] += size
                    print(f"    ✓ 删除重复文件: {file}")
                except Exception as e:
                    print(f"    ✗ 删除失败: {file} - {e}")
    
    print(f"\n  Logs目录删除文件数: {deleted_count}")

def clean_deploy_package():
    """清理deploy-package目录"""
    print("\n" + "="*60)
    print("清理 deploy-package/ 目录")
    print("="*60)
    
    deploy_dir = PROJECT_ROOT / "deploy-package"
    if not deploy_dir.exists():
        print("  deploy-package目录不存在")
        return
    
    # 删除整个deploy-package目录（它是部署包副本）
    try:
        total_size = 0
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                total_size += get_file_size(Path(root) / file)
        
        shutil.rmtree(deploy_dir)
        stats['deleted_dirs'] += 1
        stats['space_saved'] += total_size
        print(f"  ✓ 删除整个deploy-package目录（部署包副本）")
        print(f"  释放空间: {total_size / 1024:.2f} KB")
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")

def clean_documentation():
    """清理Documentation目录"""
    print("\n" + "="*60)
    print("清理 Documentation/ 目录")
    print("="*60)
    
    doc_dir = PROJECT_ROOT / "Documentation"
    if not doc_dir.exists():
        print("  Documentation目录不存在")
        return
    
    # Documentation/Markdown与docs/Markdown重复，删除整个Documentation目录
    try:
        total_size = 0
        for root, dirs, files in os.walk(doc_dir):
            for file in files:
                total_size += get_file_size(Path(root) / file)
        
        shutil.rmtree(doc_dir)
        stats['deleted_dirs'] += 1
        stats['space_saved'] += total_size
        print(f"  ✓ 删除Documentation目录（与docs重复）")
        print(f"  释放空间: {total_size / 1024:.2f} KB")
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")

def clean_archives():
    """清理archives目录"""
    print("\n" + "="*60)
    print("清理 archives/ 目录")
    print("="*60)
    
    archives_dir = PROJECT_ROOT / "archives"
    if not archives_dir.exists():
        print("  archives目录不存在")
        return
    
    # 删除整个archives目录（旧版本归档）
    try:
        total_size = 0
        for root, dirs, files in os.walk(archives_dir):
            for file in files:
                total_size += get_file_size(Path(root) / file)
        
        shutil.rmtree(archives_dir)
        stats['deleted_dirs'] += 1
        stats['space_saved'] += total_size
        print(f"  ✓ 删除archives目录（旧版本归档）")
        print(f"  释放空间: {total_size / 1024:.2f} KB")
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")

def clean_temp():
    """清理Temp目录"""
    print("\n" + "="*60)
    print("清理 Temp/ 目录")
    print("="*60)
    
    temp_dir = PROJECT_ROOT / "Temp"
    if not temp_dir.exists():
        print("  Temp目录不存在")
        return
    
    # 删除整个Temp目录
    try:
        total_size = 0
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                total_size += get_file_size(Path(root) / file)
        
        shutil.rmtree(temp_dir)
        stats['deleted_dirs'] += 1
        stats['space_saved'] += total_size
        print(f"  ✓ 删除Temp目录")
        print(f"  释放空间: {total_size / 1024:.2f} KB")
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")

def clean_backup_files():
    """清理整理后的备份文件目录"""
    print("\n" + "="*60)
    print("清理 整理后的备份文件/ 目录")
    print("="*60)
    
    backup_dir = PROJECT_ROOT / "整理后的备份文件"
    if not backup_dir.exists():
        print("  目录不存在")
        return
    
    # 删除整个备份目录
    try:
        total_size = 0
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                total_size += get_file_size(Path(root) / file)
        
        shutil.rmtree(backup_dir)
        stats['deleted_dirs'] += 1
        stats['space_saved'] += total_size
        print(f"  ✓ 删除整理后的备份文件目录")
        print(f"  释放空间: {total_size / 1024:.2f} KB")
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")

def clean_css_duplicates():
    """清理CSS目录下的重复文件"""
    print("\n" + "="*60)
    print("清理 CSS/ 目录下的重复文件")
    print("="*60)
    
    css_dir = PROJECT_ROOT / "CSS"
    if not css_dir.exists():
        print("  CSS目录不存在")
        return
    
    deleted_count = 0
    
    for root, dirs, files in os.walk(css_dir):
        for file in files:
            filepath = Path(root) / file
            
            if is_duplicate_file(file):
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    stats['deleted_files'] += 1
                    stats['space_saved'] += size
                    print(f"  ✓ 删除: {Path(root).relative_to(PROJECT_ROOT)}/{file}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {file} - {e}")
    
    print(f"\n  CSS目录删除文件数: {deleted_count}")

def clean_javascript_duplicates():
    """清理JavaScript目录下的重复文件"""
    print("\n" + "="*60)
    print("清理 JavaScript/ 目录下的重复文件")
    print("="*60)
    
    js_dir = PROJECT_ROOT / "JavaScript"
    if not js_dir.exists():
        print("  JavaScript目录不存在")
        return
    
    deleted_count = 0
    
    for file in os.listdir(js_dir):
        filepath = js_dir / file
        
        if filepath.is_dir():
            continue
        
        if is_duplicate_file(file):
            size = get_file_size(filepath)
            try:
                os.remove(filepath)
                deleted_count += 1
                stats['deleted_files'] += 1
                stats['space_saved'] += size
                print(f"  ✓ 删除: {file}")
            except Exception as e:
                print(f"  ✗ 删除失败: {file} - {e}")
    
    print(f"\n  JavaScript目录删除文件数: {deleted_count}")

def clean_encrypted_js_duplicates():
    """清理Encrypted_JS目录下的重复文件"""
    print("\n" + "="*60)
    print("清理 Encrypted_JS/ 目录下的重复文件")
    print("="*60)
    
    enc_js_dir = PROJECT_ROOT / "Encrypted_JS"
    if not enc_js_dir.exists():
        print("  Encrypted_JS目录不存在")
        return
    
    deleted_count = 0
    
    for file in os.listdir(enc_js_dir):
        filepath = enc_js_dir / file
        
        if filepath.is_dir():
            continue
        
        if is_duplicate_file(file):
            size = get_file_size(filepath)
            try:
                os.remove(filepath)
                deleted_count += 1
                stats['deleted_files'] += 1
                stats['space_saved'] += size
                print(f"  ✓ 删除: {file}")
            except Exception as e:
                print(f"  ✗ 删除失败: {file} - {e}")
    
    print(f"\n  Encrypted_JS目录删除文件数: {deleted_count}")

def clean_sourcecode_duplicates():
    """清理SourceCode目录下的重复文件"""
    print("\n" + "="*60)
    print("清理 SourceCode/ 目录下的重复文件")
    print("="*60)
    
    src_dir = PROJECT_ROOT / "SourceCode"
    if not src_dir.exists():
        print("  SourceCode目录不存在")
        return
    
    deleted_count = 0
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            filepath = Path(root) / file
            
            if is_duplicate_file(file):
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    stats['deleted_files'] += 1
                    stats['space_saved'] += size
                    print(f"  ✓ 删除: {Path(root).relative_to(PROJECT_ROOT)}/{file}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {file} - {e}")
    
    print(f"\n  SourceCode目录删除文件数: {deleted_count}")

def clean_flask_app_duplicates():
    """清理flask-app目录下的重复文件"""
    print("\n" + "="*60)
    print("清理 flask-app/ 目录下的重复文件")
    print("="*60)
    
    flask_dir = PROJECT_ROOT / "flask-app"
    if not flask_dir.exists():
        print("  flask-app目录不存在")
        return
    
    deleted_count = 0
    
    for root, dirs, files in os.walk(flask_dir):
        # 跳过特定目录
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
        
        for file in files:
            filepath = Path(root) / file
            
            if is_duplicate_file(file):
                size = get_file_size(filepath)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    stats['deleted_files'] += 1
                    stats['space_saved'] += size
                    print(f"  ✓ 删除: {Path(root).relative_to(PROJECT_ROOT)}/{file}")
                except Exception as e:
                    print(f"  ✗ 删除失败: {file} - {e}")
    
    print(f"\n  flask-app目录删除文件数: {deleted_count}")

def main():
    print("="*60)
    print("MTSCOS AI Project - 目录精简脚本")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 统计清理前的文件数量
    stats['total_files_before'] = count_files(PROJECT_ROOT)
    print(f"\n清理前文件总数: {stats['total_files_before']}")
    
    # 执行清理
    clean_logs_directory()
    clean_deploy_package()
    clean_documentation()
    clean_archives()
    clean_temp()
    clean_backup_files()
    clean_css_duplicates()
    clean_javascript_duplicates()
    clean_encrypted_js_duplicates()
    clean_sourcecode_duplicates()
    clean_flask_app_duplicates()
    
    # 统计清理后的文件数量
    stats['total_files_after'] = count_files(PROJECT_ROOT)
    
    # 输出统计信息
    print("\n" + "="*60)
    print("清理完成统计")
    print("="*60)
    print(f"清理前文件数: {stats['total_files_before']}")
    print(f"清理后文件数: {stats['total_files_after']}")
    print(f"删除文件数: {stats['deleted_files']}")
    print(f"删除目录数: {stats['deleted_dirs']}")
    print(f"释放空间: {stats['space_saved'] / 1024 / 1024:.2f} MB")
    print(f"精简率: {(stats['total_files_before'] - stats['total_files_after']) / stats['total_files_before'] * 100:.1f}%")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 列出保留的核心目录
    print("\n" + "="*60)
    print("保留的核心目录")
    print("="*60)
    core_dirs = [
        'flask-app/',
        'app/',
        'frontend/',
        'docs/',
        'CSS/',
        'JavaScript/',
        'HTML/',
        'Database/',
        'Configuration/',
        'config/',
        'ViKey/',
        'user_management_server/',
        'cluster/',
        'tools/',
        'iso_images/',
        'core/',
        'cache/',
        'databases/',
        'snapshots/',
    ]
    
    for dir_name in core_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            file_count = count_files(dir_path)
            print(f"  ✓ {dir_name} ({file_count} 文件)")

if __name__ == '__main__':
    main()
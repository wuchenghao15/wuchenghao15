# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:09
#!/usr/bin/env python3
"""
README文件重命名工具
按照文件夹名称规范化README文件命名
"""
import os
import shutil
from datetime import datetime

# 配置
MARKDOWN_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Documentation/Markdown"
BAK_DIR = os.path.join(MARKDOWN_DIR, "rename_bak")

# 创建备份目录
def create_backup_directory():
    """创建备份目录"""
    if not os.path.exists(BAK_DIR):
        os.makedirs(BAK_DIR)
        print(f"创建备份目录: {BAK_DIR}")

# 备份文件
def backup_file(file_path, new_name=None):
    """备份文件到备份目录"""
    if os.path.exists(file_path):
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filename}.{timestamp}.bak"
        if new_name:
            backup_name = f"{filename}_to_{new_name}.{timestamp}.bak"
        backup_path = os.path.join(BAK_DIR, backup_name)
        shutil.copy2(file_path, backup_path)
        print(f"备份文件: {filename} -> {backup_path}")
        return backup_path
    return None

# 获取所有README文件
def get_readme_files():
    """获取所有README文件"""
    readme_files = []
    for file in os.listdir(MARKDOWN_DIR):
        if file.startswith("README") and file.endswith(".md"):
            readme_files.append(os.path.join(MARKDOWN_DIR, file))
    return sorted(readme_files)

# 读取文件内容
def read_file(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return ""

# 提取文件标题
def extract_title(content):
    """从文件内容中提取标题"""
    import re
    title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    return ""

def extract_folder_name(title):
    """从标题中提取文件夹名称"""
    # 提取第一个单词作为文件夹名称
    parts = title.split(' - ')
    if parts:
        return parts[0].strip()
    return ""

def rename_readme_files():
    """重命名README文件，使其与文件夹名称匹配"""
    print("开始重命名README文件...")

    # 预定义的重命名映射
    rename_mapping = {
        "README.md": "README_Database.md",           # Database - 数据库文件夹
        "README_1.md": "README_Configuration.md",     # Configuration - 配置文件夹
        "README_2.md": "README_Documentation.md",      # Documentation - 文档文件夹
        "README_3.md": "README_Media.md",             # Media - 媒体资源文件夹
        "README_4.md": "README_Web.md",               # Web - Web资源文件夹
        "README_5.md": "README_Others.md",            # Others - 其他文件夹
        "README_6.md": "README_Project_Overview.md",  # MTSCOS - 智能管理系统
        "README_7.md": "README_Scripts.md",           # Scripts - 脚本文件夹
        "README_8.md": "README_Data.md",              # Data - 数据文件夹
        "README_9.md": "README_SourceCode.md"         # SourceCode - 源代码文件夹
    }

    # 处理特殊文件
    special_files = ["README_INDEX.md", "README_ORGANIZE_LOGS.md"]

    renamed_files = []
    skipped_files = []

    # 获取所有README文件
    all_readme_files = get_readme_files()
    for file_path in all_readme_files:
        filename = os.path.basename(file_path)

        if filename in special_files:
            skipped_files.append((filename, "特殊文件，无需重命名"))
            continue

        # 检查是否在映射中
        if filename in rename_mapping:
            new_filename = rename_mapping[filename]
            new_file_path = os.path.join(MARKDOWN_DIR, new_filename)

            # 备份原文件
            backup_file(file_path, new_filename)

            # 重命名文件
            try:
                # 如果新文件已存在，先备份
                if os.path.exists(new_file_path):
                    backup_file(new_file_path, "existing")

                os.rename(file_path, new_file_path)
                renamed_files.append((filename, new_filename))
                print(f"重命名成功: {filename} -> {new_filename}")
            except Exception as e:
                print(f"重命名失败 {filename}: {e}")
                skipped_files.append((filename, str(e)))
        else:
            # 对于不在映射中的文件，尝试智能重命名
            title = extract_title(content)
            folder_name = extract_folder_name(title)

            if folder_name:
                new_filename = f"README_{folder_name.replace(' ', '_')}.md"
                new_file_path = os.path.join(MARKDOWN_DIR, new_filename)

                # 备份原文件
                backup_file(file_path, new_filename)

                # 重命名文件
                try:
                    if os.path.exists(new_file_path):
                        os.remove(new_file_path)
                    os.rename(file_path, new_file_path)
                    print(f"智能重命名成功: {filename} -> {new_filename}")
                    print(f"智能重命名失败 {filename}: {e}")
                    skipped_files.append((filename, str(e)))
            else:
                skipped_files.append((filename, "无法提取文件夹名称"))
    update_index_file(rename_mapping)
    # 输出统计信息
    print(f"成功重命名: {len(renamed_files)}")
    for old_name, new_name in renamed_files:

    for filename, reason in skipped_files:
        print(f"  - {filename}: {reason}")

    print(f"\n备份文件保存在: {BAK_DIR}")
# 更新README_INDEX.md中的链接
    """更新README_INDEX.md文件中的链接"""
    index_path = os.path.join(MARKDOWN_DIR, "README_INDEX.md")

    if os.path.exists(index_path):
        # 备份索引文件
        backup_file(index_path, "updated")

        # 读取内容
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换文件名链接
        for old_name, new_name in rename_mapping.items():
            # 替换链接
            content = content.replace(f"[{old_name}]({old_name})", f"[{new_name}]({new_name})")

        # 写入更新后的内容
        with open(index_path, 'w', encoding='utf-8') as f:

        print(f"已更新README_INDEX.md中的链接")

# 主函数
def main():
    """主函数"""
    print("README文件重命名工具")
    print("====================\n")

    # 创建备份目录
    create_backup_directory()
    # 显示当前的README文件
    print("当前README文件列表:")
    for file_path in get_readme_files():
        filename = os.path.basename(file_path)
        content = read_file(file_path)
        title = extract_title(content)

    print("\n开始重命名...")

    # 重命名文件
    rename_readme_files()

    print("\nREADME文件重命名完成!")
    print("注意：请检查更新后的文件内容和链接是否正常工作")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:12
#!/usr/bin/env python3
"""
README文件整理工具
用于分析、合并和更新项目中的README文件，解决重复内容和过时信息的问题
"""
import os
import re
import shutil
from datetime import datetime

# 配置
MARKDOWN_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Documentation/Markdown"
BAK_DIR = os.path.join(MARKDOWN_DIR, "bak")
PROJECT_ROOT = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"

# 创建备份目录
def create_backup_directory():
    """创建备份目录"""
    if not os.path.exists(BAK_DIR):
        os.makedirs(BAK_DIR)
        print(f"创建备份目录: {BAK_DIR}")

# 备份文件
def backup_file(file_path):
    """备份文件到备份目录"""
    if os.path.exists(file_path):
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BAK_DIR, f"{filename}.{timestamp}.bak")
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

# 写入文件内容
def write_file(file_path, content):
    """写入文件内容"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
        print(f"写入文件成功: {file_path}")
        pass
        return True
    except Exception as e:
        print(f"写入文件失败 {file_path}: {e}")
        return False
# 检查文件夹是否存在
def check_folder_exists(folder_name):
    """检查项目根目录下文件夹是否存在"""
    folder_path = os.path.join(PROJECT_ROOT, folder_name)
    return os.path.isdir(folder_path)

# 更新README_3.md（删除Tools文件夹的描述）
def update_readme_3():
    """更新README_3.md，移除对已删除Tools文件夹的描述"""
    readme_3_path = os.path.join(MARKDOWN_DIR, "README_3.md")

    if os.path.exists(readme_3_path):
        # 备份文件
        backup_file(readme_3_path)
        # 读取内容
        content = read_file(readme_3_path)

        # 如果Tools文件夹不存在，更新内容
        if not check_folder_exists("Tools"):
            # 将内容更新为Media文件夹的描述
            new_content = """
# Media - 媒体资源文件夹

## 文件夹说明

Media文件夹用于存储项目的媒体资源文件，包括图片等视觉元素。这些资源用于丰富用户界面和提升用户体验。

## 目录结构

```
Media/
└── Images/              # 图片资源目录
```

## 内容说明

### Images/
包含项目中使用的各种图片资源：
- 界面图标
- 背景图片
- 按钮图标
- 其他装饰性图片

## 使用建议

- 图片文件应适当压缩，以提高加载速度
- 关键图标建议使用SVG格式，以保证在不同分辨率下的清晰度
- 媒体文件应按照功能或用途进行分类组织

## 注意事项

- 确保所有媒体资源有适当的使用权限
- 大型媒体文件应考虑延迟加载策略
- 更新媒体资源后，确保更新相关的引用路径
"""
            # 写入新内容
            write_file(readme_3_path, new_content.strip())
            print("已更新README_3.md，将Tools文件夹描述替换为Media文件夹描述")

# 更新README_6.md（修复过时的项目结构信息）
def update_readme_6():
    """更新README_6.md，修复过时的项目结构信息"""
    readme_6_path = os.path.join(MARKDOWN_DIR, "README_6.md")

    if os.path.exists(readme_6_path):
        # 备份文件
        backup_file(readme_6_path)

        content = read_file(readme_6_path)

        # 更新项目结构部分，移除Tools文件夹，添加Media文件夹
        # 查找项目结构部分
        structure_pattern = r'## 项目结构\s*```[\s\S]*?```'

        updated_structure = """
## 项目结构

```
├── Backups/                # 备份文件夹
│   └── MyBackup/
│       └── Javascript/
├── Build/                  # 构建文件夹
│   └── Output/
│       └── dist/
├── Configuration/          # 配置文件夹
│   ├── package.json
│   └── 各类报告文件
├── Data/                   # 数据文件夹
│   ├── MyData/
│   │   └── db_connection_string.txt
│   └── Users/
│       └── users_data/
├── Database/               # 数据库文件夹
│   └── Init/
│       └── init-mssql/
├── Deployment/             # 部署文件夹
│   └── deploy_site/
│       ├── MyPages/
│       ├── MyScript/
│       ├── MyStyle/
│       ├── MyTools/
│       └── 其他部署文件
├── Documentation/          # 文档文件夹
│   ├── DEPLOYMENT_GUIDE.md
│   ├── Markdown/
│   ├── Text/
│   └── performance_optimization_report.txt
├── Logs/                   # 日志文件夹
│   ├── archives/
│   ├── auto_sync.log
│   ├── build_*.log
│   ├── login_*.log
│   └── 其他日志文件
├── Media/                  # 媒体资源文件夹
│   └── Images/
├── Others/                 # 其他文件夹
│   └── VERSION
├── Scripts/                # 脚本文件夹
│   ├── auto_backup_js_files.py
│   ├── deploy.sh
│   ├── organize_log_files.py
│   ├── run_log_organizer.sh
│   └── 其他自动化脚本
├── SourceCode/             # 源代码文件夹
│   ├── JavaScript/
│   │   └── MyScript/
│   └── Python/
│       ├── build.py
│       └── 其他Python脚本

├── Web/                    # Web资源文件夹（已弃用，内容已迁移）
│   ├── Pages/
│   │   ├── MyPages/
```"""

        # 替换项目结构部分
        updated_content = re.sub(structure_pattern, updated_structure.strip(), content)

        # 写入更新后的内容
        write_file(readme_6_path, updated_content)
        print("已更新README_6.md，修复了过时的项目结构信息")

# 创建综合索引文件
def create_index_file():
    """创建README文件的综合索引"""
    index_path = os.path.join(MARKDOWN_DIR, "README_INDEX.md")

    # 备份现有索引（如果存在）
    if os.path.exists(index_path):
        backup_file(index_path)

    # 收集所有README文件信息
    readme_info = []
    for file_path in get_readme_files():
        filename = os.path.basename(file_path)
        content = read_file(file_path)

        # 提取标题
        title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)

        # 提取简要描述
        desc_match = re.search(r'^##\s+文件夹说明\s*$(.*?)(?=^##|$)', content, re.DOTALL | re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else "无描述"

        readme_info.append((filename, title, description))

    # 创建索引内容
    index_content = """
# README文件索引

本文档提供了项目中所有README文件的索引，方便快速查找和了解各部分文档内容。

## 索引列表

| 文件名 | 标题 | 描述 |
|--------|------|------|
"""
    # 添加表格行
    for filename, title, description in sorted(readme_info, key=lambda x: x[0]):
        # 限制描述长度
        short_desc = (description[:100] + '...') if len(description) > 100 else description
        index_content += f"| [{filename}]({filename}) | {title} | {short_desc} |\n"

    # 添加说明
    index_content += """

## 使用说明

- 点击文件名可以跳转到相应的详细文档
- 主要功能说明请参考 [README_6.md](README_6.md) 项目概述
- 各模块详细说明请参考对应文件夹的README文件

## 注意事项

- 文档内容应与实际代码和配置保持一致
- 重要的项目变更应及时更新相关文档
- 如有发现文档与实际不符的情况，请及时更新
"""
    # 写入索引文件
    write_file(index_path, index_content.strip())
    print(f"已创建README索引文件: {index_path}")

# 检查README文件的完整性
def check_readme_integrity():
    print("\n=== README文件完整性检查 ===")
    issues_found = False

    for file_path in get_readme_files():
        filename = os.path.basename(file_path)
        content = read_file(file_path)

        # 检查是否包含必要的章节
        required_sections = ["# ", "## 文件夹说明"]

        for section in required_sections:
                print(f"[{filename}] 缺少必要章节: {section}")
                issues_found = True

    # 检查是否有过时的文件夹描述
    if os.path.exists(os.path.join(MARKDOWN_DIR, "README_3.md")):
        content = read_file(os.path.join(MARKDOWN_DIR, "README_3.md"))
            print("[README_3.md] 包含已删除的Tools文件夹描述")
            issues_found = True
    if not issues_found:
        print("未发现明显问题")

# 主函数
def main():
    """主函数"""
    print("开始整理README文件...")

    # 创建备份目录
    create_backup_directory()

    # 检查完整性
    check_readme_integrity()
    # 更新过时的README文件
    update_readme_3()  # 更新Tools文件夹为Media文件夹

    # 创建索引文件
    create_index_file()

    print("\nREADME文件整理完成!")
    print(f"备份文件保存在: {BAK_DIR}")
    print("请查看更新后的文件内容是否符合预期")

if __name__ == "__main__":
    main()

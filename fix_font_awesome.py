#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Font Awesome CDN引用
将外部CDN链接替换为本地资源或可靠的CDN
"""

import os
import re
from pathlib import Path

def fix_font_awesome_references():
    """修复所有Font Awesome CDN引用"""
    project_root = Path(__file__).parent
    fixed_files = []

    # 新的CDN链接（使用jsDelivr，比cloudflare更可靠）
    new_cdn = "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css"

    # 需要修复的文件模式
    file_patterns = ['*.html', '*.js']

    for pattern in file_patterns:
        for file_path in project_root.rglob(pattern):
            # 跳过node_modules和其他不需要的目录
            skip_dirs = {'node_modules', '.git', 'venv', '__pycache__', '.venv'}
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找Font Awesome CDN引用
                if 'cdnjs.cloudflare.com' in content and 'font-awesome' in content:
                    # 替换CDN链接
                    old_patterns = [
                        r'https?://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"\']+',
                        r'https?://maxcdn\.bootstrapcdn\.com/font-awesome/[^"\']+',
                    ]

                    new_content = content
                    for pattern in old_patterns:
                        new_content = re.sub(pattern, new_cdn, new_content)

                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        fixed_files.append(str(file_path))
                        print(f"✅ 修复: {file_path}")

            except Exception as e:
                print(f"⚠️  错误: {file_path} - {e}")

    return fixed_files

def create_local_font_awesome():
    """创建本地Font Awesome资源（可选）"""
    print("\n📝 提示: 如需使用本地Font Awesome资源，请:")
    print("   1. 下载Font Awesome: https://fontawesome.com/download")
    print("   2. 解压到 frontend/assets/libs/font-awesome/")
    print("   3. 在HTML中引用本地CSS文件")

def main():
    print("=" * 70)
    print("🔧 Font Awesome CDN引用修复工具")
    print("=" * 70)

    print("\n🔍 正在扫描文件...")
    fixed = fix_font_awesome_references()

    print("\n" + "=" * 70)
    print(f"✅ 修复完成! 共修复 {len(fixed)} 个文件")
    print("=" * 70)

    if fixed:
        print("\n已修复的文件:")
        for f in fixed[:10]:  # 只显示前10个
            print(f"  - {f}")
        if len(fixed) > 10:
            print(f"  ... 还有 {len(fixed) - 10} 个文件")

    create_local_font_awesome()

    print("\n💡 建议:")
    print("   1. 清除浏览器缓存")
    print("   2. 重新加载页面")
    print("   3. 如果问题仍然存在，考虑使用本地资源")

if __name__ == '__main__':
    main()

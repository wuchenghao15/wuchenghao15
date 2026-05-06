#!/usr/bin/env python3
"""
HTML模板自动更新脚本
用于更新所有HTML模板的前端设计，确保它们使用新的CSS变量和样式系统

import os
import re
from typing import List

def get_template_files(directory: str) -> List[str]:
    获取目录中所有HTML模板文件

    Args:
        directory: 要搜索的目录路径

    Returns:
        HTML文件路径列表
    template_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                template_files.append(os.path.join(root, file))
    return template_files

def update_template(file_path: str) -> None:
    更新单个HTML模板文件

    Args:
        file_path: HTML模板文件路径
    try:
        with open(file_path, 'r', encoding='utf-8') as f:

        # 更新CSS引用（确保使用新的样式文件）
        content = re.sub(r'<link rel="stylesheet" href="(.*?)style\.css">(?!.*style\.css)',
                        '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">',
                        content)

        # 添加必要的meta标签（如果缺失）
        if '<meta name="viewport"' not in content:
            meta_viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            content = re.sub(r'(<head[^>]*?>)', f'\\1\n    {meta_viewport}', content)

        # 添加主题颜色meta标签
        if '<meta name="theme-color"' not in content:
            meta_theme = '<meta name="theme-color" content="#3b82f6">'
            content = re.sub(r'(<head[^>]*?>)', f'\\1\n    {meta_theme}', content)

        # 更新旧的CSS类名到新的类名
        # 例如：将旧的主题颜色类更新为新的CSS变量系统
        content = re.sub(r'bg-gradient', 'bg-gradient-primary', content)
        content = re.sub(r'btn-primary', 'btn-primary', content)  # 保持一致
        content = re.sub(r'card', 'ai-card', content)

        # 添加现代化的HTML结构
        if '{% block content %}' in content and '<!-- 主内容区 -->' not in content:
            content = re.sub(r'{% block content %}(?!<!-- 主内容区 -->)',
                            '{% block content %}\n    <!-- 主内容区 -->\n', content)

        # 添加页脚（如果缺失）
        if '{% block footer %}' not in content and '</body>' in content:
            footer_block = '\n    {% block footer %}{% endblock %}\n'
            content = re.sub(r'(</body>)', f'{footer_block}\1', content)

        # 更新JavaScript引用
        if '<script src="{{ url_for(\'get_js_ai_code\') }}"></script>' not in content:
            js_code = '<script src="{{ url_for(\'get_js_ai_code\') }}"></script>'
            content = re.sub(r'(</body>)', f'    {js_code}\n\1', content)

        # 保存更新后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ 更新成功: {file_path}")

    except Exception as e:
        print(f"✗ 更新失败: {file_path} - {str(e)}")

def update_all_templates(directory: str) -> None:
    更新目录中所有HTML模板文件

    Args:
        directory: 包含HTML模板的目录路径
    print(f"开始更新HTML模板文件...")
    print(f"搜索目录: {directory}")

    template_files = get_template_files(directory)

    for file_path in template_files:
        update_template(file_path)

    print(f"\n更新完成！")

def main() -> None:
    主函数
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 定义模板目录
    template_dirs = [
        os.path.join(script_dir, 'templates'),
        # 如果有其他模板目录，可以在这里添加
    ]

    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            update_all_templates(template_dir)
        else:
            print(f"模板目录不存在: {template_dir}")

if __name__ == "__main__":
    main()

"""
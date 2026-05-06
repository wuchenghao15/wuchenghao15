#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 threading 导入问题

import os
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fix_threading')

def fix_threading_in_file(file_path):
    """修复单个文件中的 threading 导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 检查是否使用了 threading 但没有导入
        if 'threading.' in content and 'import threading' not in content:
            # 在第一个 import 行添加 threading
            lines = content.split('\n')
            new_lines = []
            threading_added = False

            for line in lines:
                if not threading_added and line.startswith('import '):
                    if 'threading' not in line:
                        line = line.rstrip() + ', threading'
                        threading_added = True
                new_lines.append(line)

            content = '\n'.join(new_lines)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"✅ 修复 threading 导入: {file_path}")
            return True
        else:
            logger.info(f"无需修复 threading: {file_path}")
            return False

    except Exception as e:
        logger.error(f"❌ 修复失败: {file_path} - {str(e)}")
        return False
def main():
    """主函数"""
    logger.info("=== 开始修复 threading 导入 ===")

    # 需要检查的文件
    files_to_check = [
        'app/api/cluster_api.py',
        'app/api/ai_cluster_api.py'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            logger.info(f"检查文件: {file_path}")
            fix_threading_in_file(file_path)
        else:

    logger.info("=== threading 导入修复完成 ===")

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:18
#!/usr/bin/env python3
"""
日志文件整理脚本
将所有二级文件夹中的日志文件移动到一级Logs文件夹，并删除空的二级文件夹
"""
import os
import shutil
from pathlib import Path

def flatten_logs(logs_dir):
    """将二级文件夹中的日志文件移动到一级目录"""
    logs_path = Path(logs_dir)
    moved_files = []
    deleted_dirs = []

    # 遍历Logs目录下的所有子目录
    for item in logs_path.iterdir():
        if item.is_dir():
            # 获取子目录中的所有文件
            for subitem in item.iterdir():
                if subitem.is_file():
                    # 构建目标文件路径
                    target_path = logs_path / subitem.name

                    # 如果文件名已存在，添加前缀避免覆盖
                    counter = 1
                    original_name = subitem.name
                    while target_path.exists():
                        name_parts = original_name.split('.')
                        if len(name_parts) > 1:
                            name_parts[0] = f"{name_parts[0]}_{counter}"
                            new_name = '.'.join(name_parts)
                        else:
                            new_name = f"{original_name}_{counter}"
                        target_path = logs_path / new_name
                        counter += 1

                    # 移动文件
                    print(f"移动文件: {subitem} -> {target_path}")
                    shutil.move(str(subitem), str(target_path))
                    moved_files.append(str(subitem))

            # 删除空目录
            if not any(item.iterdir()):
                print(f"删除空目录: {item}")
                item.rmdir()
                deleted_dirs.append(str(item))

    return moved_files, deleted_dirs

if __name__ == "__main__":
    # 获取当前脚本所在目录（Logs目录）
    logs_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"开始整理日志目录: {logs_dir}")
    moved_files, deleted_dirs = flatten_logs(logs_dir)

    print(f"\n整理完成!")
    print(f"共移动 {len(moved_files)} 个文件")
    print(f"共删除 {len(deleted_dirs)} 个空目录")

    # 显示剩余的子目录（如果有）
    remaining_dirs = [d for d in os.listdir(logs_dir) if os.path.isdir(os.path.join(logs_dir, d))]
    if remaining_dirs:
        print(f"\n剩余子目录 ({len(remaining_dirs)} 个):")
        for d in remaining_dirs:
            print(f"- {d}")
    else:
        print("\n没有剩余的子目录")

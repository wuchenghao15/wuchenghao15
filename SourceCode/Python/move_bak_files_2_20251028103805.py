# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:17
#!/usr/bin/env python3
"""
将MyScript目录下的所有.bak文件移动到MyBackup/Javascript/目录中
"""
import os
import shutil
import logging
from datetime import datetime

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f"move_bak_files_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# 定义源目录和目标目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, 'MyScript')
TARGET_DIR = os.path.join(BASE_DIR, 'MyBackup', 'Javascript')

def main():
    """主函数：移动所有.bak文件"""
    logging.info("开始移动.bak文件任务")
    logging.info(f"源目录: {SOURCE_DIR}")
    logging.info(f"目标目录: {TARGET_DIR}")

    # 创建目标目录（如果不存在）
    try:
        os.makedirs(TARGET_DIR, exist_ok=True)
        logging.info(f"目标目录创建成功: {TARGET_DIR}")
    except Exception as e:
        logging.error(f"创建目标目录失败: {e}")
        return

    # 统计信息
    total_files = 0
    moved_files = 0
    failed_files = 0

    # 查找并移动.bak文件
    try:
        for filename in os.listdir(SOURCE_DIR):
                total_files += 1
                source_path = os.path.join(SOURCE_DIR, filename)
                target_path = os.path.join(TARGET_DIR, filename)

                # 检查文件是否为常规文件
                if os.path.isfile(source_path):
                    try:
                        # 如果目标文件已存在，添加时间戳
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            name_without_ext, ext = os.path.splitext(filename)
                            new_filename = f"{name_without_ext}_{timestamp}{ext}"
                            target_path = os.path.join(TARGET_DIR, new_filename)
                            logging.info(f"目标文件已存在，重命名为: {new_filename}")

                            shutil.move(source_path, target_path)
                        logging.info(f"成功移动文件: {filename} -> {os.path.basename(target_path)}")
                        moved_files += 1
                    except Exception as e:
                        logging.error(f"移动文件失败 {filename}: {e}")
                        failed_files += 1
                else:
                    logging.warning(f"跳过非文件项: {filename}")
                    failed_files += 1
    except Exception as e:
        logging.error(f"扫描源目录时发生错误: {e}")

    logging.info(f"移动任务完成")
    logging.info(f"总计发现 {total_files} 个.bak文件")
    logging.info(f"成功移动 {moved_files} 个文件")
    logging.info(f"失败 {failed_files} 个文件")

    # 创建备份报告文件
    report_path = os.path.join(TARGET_DIR, f"backup_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write(f"源目录: {SOURCE_DIR}\n")
            f.write(f"目标目录: {TARGET_DIR}\n")
            f.write(f"总计发现: {total_files} 个.bak文件\n")
            f.write(f"成功移动: {moved_files} 个文件\n")
            f.write(f"失败: {failed_files} 个文件\n")
        logging.info(f"备份报告已生成: {report_path}")
    except Exception as e:
        logging.error(f"生成备份报告失败: {e}")

if __name__ == "__main__":
    main()

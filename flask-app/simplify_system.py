#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简system相关文件
- 清理根目录的过时日志文件
- 归档不再使用的system文件
"""
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('system_simplifier')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def remove_root_log_files():
    """清理根目录的system日志文件"""
    removed_files = []
    log_patterns = [
        'system_size.log',
        'system_time.log',
    ]

    for item in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, item)
        if not os.path.isfile(full_path):
            continue

        is_old_log = False
        for pattern in log_patterns:
            if item.startswith(pattern + '.') or item == pattern:
                is_old_log = True
                break

        if is_old_log:
            try:
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                os.remove(full_path)
                removed_files.append((item, f"{size_mb:.2f}MB"))
                logger.info(f"✓ 删除日志: {item} ({size_mb:.2f}MB)")
            except OSError as e:
                logger.warning(f"无法删除 {item}: {e}")

    return removed_files


def check_root_db_files():
    """检查根目录的数据库文件"""
    db_files = []
    for item in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, item)
        if not os.path.isfile(full_path):
            continue

        if item.endswith('.db') and not os.access(full_path, os.W_OK):
            continue

        if item.endswith('.db-journal'):
            try:
                os.remove(full_path)
                db_files.append(item)
                logger.info(f"✓ 删除journal: {item}")
            except OSError as e:
                logger.warning(f"无法删除 {item}: {e}")

    return db_files


def check_obsolete_system_files():
    """检查过时的system根目录文件"""
    removed = []
    candidates = [
        'monitoring_system.py',
        'exam_judge_system.py',
    ]

    for filename in candidates:
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            continue

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'app.' not in content and 'ai_engines.' not in content:
                    archive_dir = os.path.join(BASE_DIR, 'archive', 'old_system_files')
                    os.makedirs(archive_dir, exist_ok=True)
                    shutil.move(filepath, os.path.join(archive_dir, filename))
                    removed.append(filename)
                    logger.info(f"✓ 归档: {filename}")
                else:
                    logger.info(f"⊘ 保留: {filename} (仍被引用)")
        except Exception as e:
            logger.warning(f"检查 {filename} 失败: {e}")

    return removed


def main():
    logger.info("=" * 70)
    logger.info("精简system相关文件")
    logger.info("=" * 70)

    before_size = sum(
        os.path.getsize(os.path.join(BASE_DIR, f))
        for f in os.listdir(BASE_DIR)
        if os.path.isfile(os.path.join(BASE_DIR, f))
    )

    logger.info("\n1. 清理根目录的过时日志文件...")
    log_removed = remove_root_log_files()
    total_log_size = sum(float(s.split('MB')[0]) for _, s in log_removed)
    logger.info(f"  共删除 {len(log_removed)} 个日志文件，释放 {total_log_size:.2f}MB")

    logger.info("\n2. 清理journal文件...")
    journals = check_root_db_files()

    logger.info("\n3. 归档过时的system文件...")
    obsolete = check_obsolete_system_files()

    after_size = sum(
        os.path.getsize(os.path.join(BASE_DIR, f))
        for f in os.listdir(BASE_DIR)
        if os.path.isfile(os.path.join(BASE_DIR, f))
    )

    saved_mb = (before_size - after_size) / (1024 * 1024)

    logger.info("\n" + "=" * 70)
    logger.info(f"精简完成!")
    logger.info(f"  删除日志: {len(log_removed)}个 ({total_log_size:.2f}MB)")
    logger.info(f"  删除journal: {len(journals)}个")
    logger.info(f"  归档文件: {len(obsolete)}个")
    logger.info(f"  释放空间: {saved_mb:.2f}MB")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()

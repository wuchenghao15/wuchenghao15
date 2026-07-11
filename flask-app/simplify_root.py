#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简MTSCOS系统根目录
- 删除空目录
- 整合重复目录
- 清理缓存目录
"""
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('root_simplifier')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def remove_empty_dirs():
    """删除空目录"""
    removed = []
    skip_dirs = {'.git', '.github'}

    for item in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, item)
        if not os.path.isdir(full_path):
            continue
        if item in skip_dirs:
            continue

        try:
            if not os.listdir(full_path):
                os.rmdir(full_path)
                removed.append(item)
                logger.info(f"✓ 删除空目录: {item}/")
        except OSError as e:
            logger.warning(f"无法删除 {item}: {e}")

    return removed


def remove_cache_dirs():
    """删除Python缓存目录"""
    removed = []
    cache_patterns = ['__pycache__', '.pytest_cache', '.cache']

    for root, dirs, _files in os.walk(BASE_DIR):
        for d in dirs:
            if d in cache_patterns:
                full_path = os.path.join(root, d)
                try:
                    shutil.rmtree(full_path)
                    removed.append(full_path)
                except OSError:
                    pass
        dirs[:] = [d for d in dirs if d not in cache_patterns]

    if removed:
        logger.info(f"✓ 清理 {len(removed)} 个缓存目录")
    return removed


def merge_data_into_database():
    """将data/目录下的数据库文件整合到database/"""
    data_dir = os.path.join(BASE_DIR, 'data')
    database_dir = os.path.join(BASE_DIR, 'database')
    db_subdir = os.path.join(database_dir, 'sqlite')
    os.makedirs(db_subdir, exist_ok=True)

    if not os.path.exists(data_dir):
        return []

    moved = []
    for item in os.listdir(data_dir):
        src = os.path.join(data_dir, item)
        if os.path.isfile(src) and item.endswith('.db'):
            dst = os.path.join(db_subdir, item)
            if not os.path.exists(dst):
                try:
                    shutil.move(src, dst)
                    moved.append(item)
                except OSError as e:
                    logger.warning(f"移动 {item} 失败: {e}")

    if moved:
        logger.info(f"✓ 移动 {len(moved)} 个数据库文件到 database/sqlite/")
    return moved


def merge_backups_into_archive():
    """将backups/目录整合到archive/"""
    backups_dir = os.path.join(BASE_DIR, 'backups')
    archive_dir = os.path.join(BASE_DIR, 'archive')
    archive_backups = os.path.join(archive_dir, 'backups')
    os.makedirs(archive_backups, exist_ok=True)

    if not os.path.exists(backups_dir):
        return []

    moved_items = []
    for item in os.listdir(backups_dir):
        src = os.path.join(backups_dir, item)
        dst = os.path.join(archive_backups, item)
        if not os.path.exists(dst):
            try:
                shutil.move(src, dst)
                moved_items.append(item)
            except OSError as e:
                logger.warning(f"移动 {item} 失败: {e}")

    if moved_items:
        logger.info(f"✓ 移动 {len(moved_items)} 个备份目录到 archive/backups/")

    try:
        if not os.listdir(backups_dir):
            os.rmdir(backups_dir)
            logger.info("✓ 删除空的 backups/ 目录")
    except OSError:
        pass

    return moved_items


def move_shadow_to_archive():
    """将shadow_export/整合到archive/"""
    shadow_dir = os.path.join(BASE_DIR, 'shadow_export')
    archive_dir = os.path.join(BASE_DIR, 'archive')
    archive_shadow = os.path.join(archive_dir, 'shadow_export')

    if not os.path.exists(shadow_dir):
        return False

    if os.path.exists(archive_shadow):
        return False

    try:
        shutil.move(shadow_dir, archive_shadow)
        logger.info("✓ 移动 shadow_export/ 到 archive/shadow_export/")
        return True
    except OSError as e:
        logger.warning(f"移动 shadow_export 失败: {e}")
        return False


def move_skills_to_app():
    """将skills/移动到app/"""
    skills_dir = os.path.join(BASE_DIR, 'skills')
    app_skills = os.path.join(BASE_DIR, 'app', 'skills')

    if not os.path.exists(skills_dir):
        return False

    if os.path.exists(app_skills):
        return False

    try:
        shutil.move(skills_dir, app_skills)
        logger.info("✓ 移动 skills/ 到 app/skills/")
        return True
    except OSError as e:
        logger.warning(f"移动 skills 失败: {e}")
        return False


def main():
    logger.info("=" * 70)
    logger.info("精简MTSCOS系统根目录")
    logger.info("=" * 70)

    before_dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d)) and not d.startswith('.')]
    before_count = len(before_dirs)
    logger.info(f"精简前根目录数: {before_count}")

    logger.info("\n1. 清理缓存目录...")
    cache_removed = remove_cache_dirs()

    logger.info("\n2. 删除空目录...")
    empty_removed = remove_empty_dirs()

    logger.info("\n3. 整合 data/ 数据库文件...")
    db_moved = merge_data_into_database()

    logger.info("\n4. 整合 backups/ 到 archive/backups/...")
    backups_moved = merge_backups_into_archive()

    logger.info("\n5. 移动 shadow_export/ 到 archive/...")
    move_shadow_to_archive()

    logger.info("\n6. 移动 skills/ 到 app/skills/...")
    move_skills_to_app()

    after_dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d)) and not d.startswith('.')]
    after_count = len(after_dirs)
    logger.info(f"\n精简后根目录数: {after_count}")
    logger.info(f"减少目录数: {before_count - after_count}")

    logger.info("\n" + "=" * 70)
    logger.info("精简完成!")
    logger.info("=" * 70)
    logger.info("\n最终根目录:")
    for d in sorted(after_dirs):
        logger.info(f"  - {d}/")


if __name__ == '__main__':
    main()

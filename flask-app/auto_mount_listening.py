#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动挂载匹配 listening 音频文件
- 扫描所有 listening 题目的 audio_url
- 在 static/audio 目录中查找匹配的音频文件
- 更新数据库的 audio_url 指向实际存在的文件
"""
import os
import re
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('listening_auto_mounter')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
AUDIO_BASE_DIR = os.path.join(BASE_DIR, 'static', 'audio')


def build_audio_index():
    """构建音频文件索引 {normalized_name: actual_path}"""
    audio_index = {}
    audio_exts = {'.wav', '.mp3', '.ogg', '.m4a', '.flac', '.aac'}

    for root, _dirs, files in os.walk(AUDIO_BASE_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in audio_exts:
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, BASE_DIR)
            name = os.path.splitext(f)[0]
            base_name = re.sub(r'_[a-z]+_[a-z]+_[a-z]+$', '', name)
            audio_index.setdefault(base_name, []).append('/' + rel_path.replace(os.sep, '/'))
            audio_index.setdefault(name, []).append('/' + rel_path.replace(os.sep, '/'))
    return audio_index


def extract_listening_number(audio_url):
    """从audio_url中提取listening编号"""
    match = re.search(r'listening[_-]?(\d+)', audio_url, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def find_matching_audio(audio_url, audio_index):
    """为指定的audio_url找到匹配的音频文件"""
    if not audio_url:
        return None

    number = extract_listening_number(audio_url)
    if number is None:
        return None

    candidates = []

    for fmt in [f'listening_{number}', f'listening{number}', f'listening-{number}']:
        if fmt in audio_index:
            candidates = audio_index[fmt]
            break

    if not candidates:
        target = f'listening_{number}'
        for key, paths in audio_index.items():
            key_base = re.sub(r'_[a-z]+_[a-z]+_[a-z]+$', '', key)
            if key_base == target:
                candidates = paths
                break

    if not candidates:
        return None

    candidates.sort(key=lambda p: (
        0 if 'standard' in p else 1,
        0 if 'female' in p else 1 if 'male' in p else 2,
        len(p)
    ))
    return candidates[0]


def main():
    logger.info("=" * 60)
    logger.info("自动挂载匹配 listening 文件")
    logger.info("=" * 60)

    if not os.path.exists(DB_PATH):
        logger.error(f"数据库不存在: {DB_PATH}")
        return
    if not os.path.exists(AUDIO_BASE_DIR):
        logger.error(f"音频目录不存在: {AUDIO_BASE_DIR}")
        return

    logger.info("构建音频文件索引...")
    audio_index = build_audio_index()
    logger.info(f"索引了 {len(audio_index)} 个唯一音频文件")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, audio_url FROM questions
        WHERE type = 'listening' OR tags LIKE '%listening%'
    """)
    listening_questions = cursor.fetchall()
    logger.info(f"找到 {len(listening_questions)} 道 listening 题目")

    matched = 0
    not_matched = 0
    updates = []

    for qid, current_url in listening_questions:
        new_url = find_matching_audio(current_url, audio_index)
        if new_url and new_url != current_url:
            updates.append((new_url, qid))
            matched += 1
        else:
            not_matched += 1

    if updates:
        cursor.executemany("UPDATE questions SET audio_url = ? WHERE id = ?", updates)
        conn.commit()
        logger.info(f"已更新 {len(updates)} 个 audio_url")
    else:
        logger.info("没有需要更新的 audio_url")

    conn.close()

    logger.info("=" * 60)
    logger.info(f"匹配结果: 成功 {matched}, 失败 {not_matched}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

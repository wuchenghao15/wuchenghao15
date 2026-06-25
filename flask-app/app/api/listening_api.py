# -*- coding: utf-8 -*-
"""
Listening 自动挂载 API
"""
import os
import sys
import sqlite3
import logging
from flask import Blueprint, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('listening_api')

listening_api = Blueprint('listening_api', __name__, url_prefix='/api/listening')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, 'app.db')


@listening_api.route('/mount', methods=['POST'])
def mount_listening():
    """执行自动挂载匹配"""
    try:
        from auto_mount_listening import build_audio_index, find_matching_audio
    except ImportError as e:
        return jsonify({"success": False, "error": f"无法导入脚本: {e}"}), 500

    audio_index = build_audio_index()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, audio_url FROM questions WHERE type='listening' OR tags LIKE '%listening%'")
    questions = cursor.fetchall()

    matched = 0
    not_matched = 0
    updates = []

    for qid, current_url in questions:
        new_url = find_matching_audio(current_url, audio_index)
        if new_url and new_url != current_url:
            updates.append((new_url, qid))
            matched += 1
        else:
            not_matched += 1

    if updates:
        cursor.executemany("UPDATE questions SET audio_url = ? WHERE id = ?", updates)
        conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "data": {
            "total": len(questions),
            "matched": matched,
            "not_matched": not_matched,
            "updated": len(updates),
            "audio_index_size": len(audio_index)
        }
    })


@listening_api.route('/status', methods=['GET'])
def get_status():
    """获取listening挂载状态"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN audio_url LIKE '%.wav' OR audio_url LIKE '%.mp3' OR audio_url LIKE '%.ogg' THEN 1 ELSE 0 END) as with_audio,
                SUM(CASE WHEN audio_url LIKE '%listening_0%' AND audio_url LIKE '%.mp3' THEN 1 ELSE 0 END) as unmatched
            FROM questions
            WHERE type = 'listening' OR tags LIKE '%listening%'
        """)
        row = cursor.fetchone()
        conn.close()

        total, with_audio, unmatched = row

        return jsonify({
            "success": True,
            "data": {
                "total_listening": total or 0,
                "with_audio": with_audio or 0,
                "unmatched": unmatched or 0,
                "matched_rate": f"{(with_audio or 0) / (total or 1) * 100:.2f}%"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

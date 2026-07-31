#!/usr/bin/env python3
"""
Listening API - 听力题全功能 API
提供：考试组卷 / 自适应难度 / 错题重听 / 多音轨 / 口语评测 / 诊断报告 / 自动强化 / 题库适配
"""
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin, allow_guest_access

listening_api = Blueprint('listening_api', __name__)


def _get_svc():
    from app.services.listening_service import listening_service
    return listening_service


@listening_api.route('/api/listening/health', methods=['GET'])
@allow_guest_access
def health():
    svc = _get_svc()
    stats = svc._get_snapshot_stats()
    return jsonify({"status": "ok", "stats": stats})


@listening_api.route('/api/listening/exam_pack', methods=['POST'])
@require_login
def exam_pack():
    data = request.get_json() or {}
    subject = data.get('subject', 'english')
    level = data.get('level', '')
    count = min(int(data.get('count', 10)), 50)
    include_audio = data.get('include_audio', True)
    svc = _get_svc()
    questions = svc.build_listening_exam_questions(
        subject=subject, level=level, count=count, include_audio=include_audio
    )
    return jsonify({"success": True, "count": len(questions), "questions": questions})


@listening_api.route('/api/listening/adaptive', methods=['POST'])
@require_login
def adaptive():
    data = request.get_json() or {}
    user_id = data.get('user_id', 'anonymous')
    subject = data.get('subject', '')
    target_diff = float(data.get('target_difficulty', 2.0))
    count = min(int(data.get('count', 10)), 30)
    svc = _get_svc()
    questions = svc.get_adaptive_questions(user_id, subject, target_diff, count)
    return jsonify({"success": True, "count": len(questions), "questions": questions})


@listening_api.route('/api/listening/wrong_set', methods=['GET'])
@require_login
def wrong_set():
    user_id = request.args.get('user_id', 'anonymous')
    subject = request.args.get('subject', '')
    include_relisten = request.args.get('include_relisten', 'true') == 'true'
    svc = _get_svc()
    result = svc.get_wrong_listening_set(user_id, subject, include_relisten)
    return jsonify({"success": True, "data": result})


@listening_api.route('/api/listening/multi_track', methods=['POST'])
@require_login
def multi_track():
    data = request.get_json() or {}
    subject = data.get('subject', '')
    count = min(int(data.get('count', 5)), 20)
    tracks = data.get('tracks', ['slow', 'normal', 'fast'])
    svc = _get_svc()
    questions = svc.get_multi_track_questions(subject, count, tracks)
    return jsonify({"success": True, "count": len(questions), "questions": questions})


@listening_api.route('/api/listening/speaking_eval', methods=['POST'])
@require_login
def speaking_eval():
    data = request.get_json() or {}
    user_id = data.get('user_id', 'anonymous')
    question_id = data.get('question_id', '')
    user_audio_url = data.get('user_audio_url')
    recognized_text = data.get('recognized_text', '')
    if not question_id:
        return jsonify({"success": False, "error": "question_id 不能为空"}), 400
    svc = _get_svc()
    result = svc.evaluate_speaking_attempt(user_id, question_id, user_audio_url, recognized_text)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@listening_api.route('/api/listening/diagnostic', methods=['GET'])
@require_login
def diagnostic():
    user_id = request.args.get('user_id', 'anonymous')
    subject = request.args.get('subject', '')
    svc = _get_svc()
    report = svc.get_diagnostic_report(user_id, subject)
    return jsonify({"success": True, "report": report})


@listening_api.route('/api/listening/boost', methods=['POST'])
@require_admin
def auto_boost():
    data = request.get_json() or {}
    rounds = min(int(data.get('rounds', 100)), 500)
    svc = _get_svc()
    result = svc.run_auto_boost(rounds=rounds)
    return jsonify({"success": True, "rounds": rounds, "total_new": result.get("total_new_questions"), "final_stats": result.get("final_stats")})


@listening_api.route('/api/listening/adapt/subject', methods=['POST'])
@require_admin
def adapt_subject():
    data = request.get_json() or {}
    subject = data.get('subject', '')
    limit = int(data.get('limit', 20))
    if not subject:
        return jsonify({"success": False, "error": "subject 不能为空"}), 400
    svc = _get_svc()
    result = svc.auto_adapt_to_subject(subject, limit)
    return jsonify({"success": True, "result": result})


@listening_api.route('/api/listening/adapt/bank', methods=['POST'])
@require_admin
def adapt_bank():
    data = request.get_json() or {}
    bank_id = data.get('bank_id')
    svc = _get_svc()
    result = svc.auto_adapt_to_bank(bank_id)
    return jsonify({"success": True, "result": result})


@listening_api.route('/api/listening/adapt/practice', methods=['POST'])
@require_admin
def adapt_practice():
    data = request.get_json() or {}
    subject = data.get('subject', '')
    min_questions = int(data.get('min_questions', 50))
    svc = _get_svc()
    result = svc.auto_adapt_to_practice(subject, min_questions)
    return jsonify({"success": True, "result": result})


@listening_api.route('/api/listening/bank/list', methods=['GET'])
@allow_guest_access
def list_banks():
    svc = _get_svc()
    try:
        import sqlite3
        from app.services.listening_service import DATABASE_PATH
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT bank_id, bank_name, subject, language, level, description, question_count FROM listening_banks ORDER BY subject, level")
            rows = [dict(r) for r in cur.fetchall()]
            return jsonify({"success": True, "banks": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@listening_api.route('/api/listening/stats', methods=['GET'])
@allow_guest_access
def stats():
    svc = _get_svc()
    data = svc._get_snapshot_stats()
    return jsonify({"success": True, "stats": data})


@listening_api.route('/api/listening/questions', methods=['GET'])
@allow_guest_access
def list_questions():
    svc = _get_svc()
    subject = request.args.get('subject', '')
    level = request.args.get('level', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    randomize = request.args.get('randomize', 'true') == 'true'
    questions = svc.get_listening_questions(subject=subject, level=level, limit=limit, randomize=randomize)
    return jsonify({"success": True, "count": len(questions), "questions": questions})

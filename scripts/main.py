#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - Main Application v2.4.0
教育AI系统 - 教研员AI、专家AI、教师AI、学生AI
题库优化与扩充系统
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from core import init as core_init, get_version
from core.config import config
from core.logging import logger
from core.system import system
from core.ai import ai_service
from core.cache import cache
from core.queue import queue_manager
from core.scheduler import scheduler
from core.intelligence import intelligence
from core.knowledge_graph import knowledge_graph
from core.recommendation import recommendation_engine
from core.education import (
    researcher_ai, expert_ai, teacher_ai, student_ai,
    curriculum_matcher, question_bank_optimizer
)
from core.question_bank import (
    question_bank_expander, exam_paper_collector, practice_generator
)
from core.settings import settings_manager
from core.session import session_manager, SessionStatus
from core.encryption import encryption_manager
from core.grade_management import exam_manager, GradeLevel, Subject, ExamType
from core.teacher_management import teacher_manager, TeacherSpecialty
from core.application_management import application_manager, ApplicationType

from api.routes import api_bp

__version__ = "3.1.0"

def create_app():
    """Create Flask application"""
    app = Flask(__name__)

    CORS(app)

    app.config['SECRET_KEY'] = config.get("security.secret_key", "mtscos-secret-key")
    app.config['DEBUG'] = config.get("api.debug", False)

    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return jsonify({
            "name": "MTSCOS AI Project API Server",
            "version": __version__,
            "features": {
                "intelligence_engine": True,
                "knowledge_graph": True,
                "recommendation_system": True,
                "education_ai": {
                    "researcher_ai": True,
                    "expert_ai": True,
                    "teacher_ai": True,
                    "student_ai": True
                },
                "question_bank": {
                    "optimizer": True,
                    "expander": True,
                    "exam_collector": True,
                    "practice_generator": True
                }
            },
            "docs": "Access /api for API endpoints",
            "status": "online"
        })

    @app.route('/settings')
    def settings_page():
        from flask import send_file
        return send_file('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/frontend/pages/settings-v3.html')

    @app.route('/status')
    def status():
        health = system.get_health_report()
        ai_status = ai_service.get_status()

        return jsonify({
            "status": "running",
            "version": __version__,
            "core_version": get_version(),
            "health": health,
            "ai": ai_status
        })

    @app.route('/health')
    def health():
        return jsonify(system.get_health_report())

    @app.route('/system')
    def system_info():
        return jsonify(system.get_system_info())

    @app.route('/performance')
    def performance():
        return jsonify(system.get_performance_report())

    # Intelligence API
    @app.route('/api/intelligence/analyze', methods=['POST'])
    def api_intelligence_analyze():
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "Missing data field"}), 400
        result = intelligence.analyze_data(data['data'], data.get('type', 'auto'))
        return jsonify(result)

    @app.route('/api/intelligence/process_text', methods=['POST'])
    def api_intelligence_text():
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing text field"}), 400
        result = intelligence.process_text(data['text'])
        return jsonify(result)

    @app.route('/api/intelligence/predict', methods=['POST'])
    def api_intelligence_predict():
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "Missing data field"}), 400
        predictions = intelligence.predict_next_value(data['data'], data.get('steps', 1))
        return jsonify({"predictions": predictions})

    # Knowledge Graph API
    @app.route('/api/knowledge/stats', methods=['GET'])
    def api_knowledge_stats():
        stats = knowledge_graph.get_statistics()
        return jsonify(stats)

    @app.route('/api/knowledge/search', methods=['GET'])
    def api_knowledge_search():
        query = request.args.get('q', '')
        search_type = request.args.get('type', None)
        if not query:
            return jsonify({"error": "Missing query parameter"}), 400
        results = knowledge_graph.search(query, search_type)
        return jsonify({"results": [r.to_dict() for r in results]})

    @app.route('/api/knowledge/entity', methods=['POST'])
    def api_knowledge_add_entity():
        data = request.get_json()
        if not data or 'type' not in data or 'name' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        entity_id = knowledge_graph.add_entity(data['type'], data['name'], data.get('properties', {}))
        return jsonify({"entity_id": entity_id})

    @app.route('/api/knowledge/relation', methods=['POST'])
    def api_knowledge_add_relation():
        data = request.get_json()
        if not data or 'source' not in data or 'target' not in data or 'type' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        relation_id = knowledge_graph.add_relation(data['source'], data['target'], data['type'], data.get('properties', {}), data.get('weight', 1.0))
        return jsonify({"relation_id": relation_id})

    # Recommendation API
    @app.route('/api/recommend', methods=['POST'])
    def api_recommend():
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"error": "Missing user_id"}), 400
        method = data.get('method', 'hybrid')
        top_n = data.get('top_n', 10)
        if method == 'collaborative':
            recs = recommendation_engine.collaborative_filtering(data['user_id'], top_n)
        elif method == 'content':
            recs = recommendation_engine.content_based_filtering(data['user_id'], top_n)
        elif method == 'item_based':
            recs = recommendation_engine.item_based_filtering(data['user_id'], top_n)
        else:
            recs = recommendation_engine.hybrid_recommendation(data['user_id'], top_n)
        results = []
        for item_id, score in recs:
            if item_id in recommendation_engine.items:
                item = recommendation_engine.items[item_id]
                results.append({"item_id": item_id, "item_name": item.name, "score": score, "category": item.category})
        return jsonify({"recommendations": results})

    @app.route('/api/recommend/popular', methods=['GET'])
    def api_recommend_popular():
        top_n = request.args.get('top_n', 10, type=int)
        popular = recommendation_engine.get_popular_items(top_n)
        results = []
        for item_id, count in popular:
            if item_id in recommendation_engine.items:
                item = recommendation_engine.items[item_id]
                results.append({"item_id": item_id, "item_name": item.name, "rating_count": count, "category": item.category})
        return jsonify({"popular_items": results})

    @app.route('/api/recommend/rate', methods=['POST'])
    def api_recommend_rate():
        data = request.get_json()
        if not data or 'user_id' not in data or 'item_id' not in data or 'rating' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        recommendation_engine.rate_item(data['user_id'], data['item_id'], data['rating'])
        return jsonify({"success": True})

    # Researcher AI API
    @app.route('/api/education/researcher/analyze_curriculum', methods=['POST'])
    def api_researcher_analyze_curriculum():
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing curriculum data"}), 400
        analysis = researcher_ai.analyze_curriculum(data)
        return jsonify(analysis)

    @app.route('/api/education/researcher/design_course', methods=['POST'])
    def api_researcher_design_course():
        data = request.get_json()
        subject = data.get('subject', '数学')
        grade_level = data.get('grade_level', '高中')
        duration = data.get('duration', 36)
        course = researcher_ai.design_course(subject, grade_level, duration)
        return jsonify(course)

    # Expert AI API
    @app.route('/api/education/expert/knowledge_points', methods=['GET'])
    def api_expert_knowledge_points():
        topic = request.args.get('topic', '')
        depth = request.args.get('depth', 3, type=int)
        if not topic:
            return jsonify({"error": "Missing topic parameter"}), 400
        knowledge = expert_ai.generate_knowledge_points(topic, depth)
        return jsonify(knowledge)

    @app.route('/api/education/expert/answer', methods=['POST'])
    def api_expert_answer():
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Missing question field"}), 400
        answer = expert_ai.answer_question(data['question'], data.get('subject', ''))
        return jsonify(answer)

    # Teacher AI API
    @app.route('/api/education/teacher/lesson_plan', methods=['POST'])
    def api_teacher_lesson_plan():
        data = request.get_json()
        topic = data.get('topic', '数学')
        duration = data.get('duration', 45)
        grade_level = data.get('grade_level', '高中')
        plan = teacher_ai.generate_lesson_plan(topic, duration, grade_level)
        return jsonify(plan)

    @app.route('/api/education/teacher/analyze_progress', methods=['POST'])
    def api_teacher_analyze_progress():
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({"error": "Missing student_id"}), 400
        progress = teacher_ai.analyze_student_progress(data['student_id'], data.get('data', {}))
        return jsonify(progress)

    @app.route('/api/education/teacher/create_quiz', methods=['POST'])
    def api_teacher_create_quiz():
        data = request.get_json()
        topic = data.get('topic', '数学')
        num_questions = data.get('num_questions', 5)
        quiz = teacher_ai.create_quiz(topic, num_questions)
        return jsonify(quiz)

    # Student AI API
    @app.route('/api/education/student/learning_path', methods=['GET'])
    def api_student_learning_path():
        subject = request.args.get('subject', '数学')
        current_level = request.args.get('level', '入门')
        path = student_ai.get_learning_path(subject, current_level)
        return jsonify({"learning_path": path})

    @app.route('/api/education/student/recommendation', methods=['POST'])
    def api_student_recommendation():
        data = request.get_json()
        subject = data.get('subject', '数学')
        time_available = data.get('time_available', 60)
        recommendation = student_ai.study_recommendation(subject, time_available)
        return jsonify(recommendation)

    @app.route('/api/education/student/ask', methods=['POST'])
    def api_student_ask():
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Missing question field"}), 400
        response = student_ai.ask_question(data['question'], data.get('context', ''))
        return jsonify(response)

    # Question Bank API
    @app.route('/api/question_bank/optimize', methods=['POST'])
    def api_question_bank_optimize():
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Missing question field"}), 400
        optimized = question_bank_optimizer.optimize_question(data['question'])
        return jsonify(optimized)

    @app.route('/api/question_bank/analyze_quality', methods=['POST'])
    def api_question_bank_analyze_quality():
        data = request.get_json()
        if not data or 'questions' not in data:
            return jsonify({"error": "Missing questions field"}), 400
        analysis = question_bank_optimizer.analyze_bank_quality(data['questions'])
        return jsonify(analysis)

    @app.route('/api/question_bank/expand', methods=['POST'])
    def api_question_bank_expand():
        data = request.get_json()
        subject = data.get('subject', '数学')
        grade_level = data.get('grade_level', '高中')
        count = data.get('count', 10)
        question_type = data.get('question_type', 'all')
        questions = question_bank_expander.expand_from_online(subject, grade_level, count, question_type)
        return jsonify({"questions": questions})

    @app.route('/api/question_bank/match_curriculum', methods=['POST'])
    def api_question_bank_match_curriculum():
        data = request.get_json()
        if not data or 'questions' not in data or 'curriculum' not in data:
            return jsonify({"error": "Missing questions or curriculum field"}), 400
        matched = curriculum_matcher.match_questions_to_curriculum(data['questions'], data['curriculum'])
        return jsonify({"matched_questions": matched})

    @app.route('/api/question_bank/generate_curriculum_questions', methods=['POST'])
    def api_question_bank_generate_curriculum_questions():
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing curriculum data"}), 400
        count = data.get('count', 10)
        questions = curriculum_matcher.generate_curriculum_aligned_questions(data, count)
        return jsonify({"questions": questions})

    # Exam Paper API
    @app.route('/api/exam_paper/collect', methods=['POST'])
    def api_exam_paper_collect():
        data = request.get_json()
        subject = data.get('subject', '数学')
        exam_type = data.get('exam_type', '高考')
        years = data.get('years', [2024, 2023, 2022])
        papers = exam_paper_collector.collect_exam_papers(subject, exam_type, years)
        return jsonify({"papers": papers})

    @app.route('/api/exam_paper/statistics', methods=['POST'])
    def api_exam_paper_statistics():
        data = request.get_json()
        if not data or 'papers' not in data:
            return jsonify({"error": "Missing papers field"}), 400
        stats = exam_paper_collector.get_exam_statistics(data['papers'])
        return jsonify(stats)

    # Practice API
    @app.route('/api/practice/generate', methods=['POST'])
    def api_practice_generate():
        data = request.get_json()
        subject = data.get('subject', '数学')
        topic = data.get('topic', '函数')
        difficulty_profile = data.get('difficulty_profile', '能力提升')
        question_count = data.get('question_count', 10)
        practice = practice_generator.generate_practice_set(subject, topic, difficulty_profile, question_count)
        return jsonify(practice)

    @app.route('/api/practice/daily', methods=['POST'])
    def api_practice_daily():
        data = request.get_json()
        subject = data.get('subject', '数学')
        student_level = data.get('student_level', '中等')
        practice = practice_generator.generate_daily_practice(subject, student_level)
        return jsonify(practice)

    # Settings API
    @app.route('/api/settings/roles', methods=['GET'])
    def api_settings_roles():
        roles = {role_id: role.to_dict() for role_id, role in settings_manager.roles.items()}
        return jsonify({"roles": roles})

    @app.route('/api/settings/user/create', methods=['POST'])
    def api_settings_create_user():
        data = request.get_json()
        user_id = data.get('user_id')
        username = data.get('username')
        email = data.get('email', '')
        
        if not user_id or not username:
            return jsonify({"error": "Missing user_id or username"}), 400
        
        user = settings_manager.create_user(user_id, username, email)
        return jsonify({"success": True, "user": user.to_dict()})

    @app.route('/api/settings/user/assign_role', methods=['POST'])
    def api_settings_assign_role():
        data = request.get_json()
        user_id = data.get('user_id')
        role_id = data.get('role_id')
        
        success = settings_manager.assign_role(user_id, role_id)
        return jsonify({"success": success})

    @app.route('/api/settings/user/visible_features', methods=['POST'])
    def api_settings_visible_features():
        data = request.get_json()
        user_id = data.get('user_id')
        
        user = settings_manager.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        features = settings_manager.get_visible_features(user)
        return jsonify({"features": features})

    @app.route('/api/settings/user/visible_settings', methods=['POST'])
    def api_settings_visible_settings():
        data = request.get_json()
        user_id = data.get('user_id')
        
        user = settings_manager.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        settings_groups = settings_manager.get_visible_settings(user)
        return jsonify({"settings": settings_groups})

    @app.route('/api/settings/user/update', methods=['POST'])
    def api_settings_update_user_settings():
        data = request.get_json()
        user_id = data.get('user_id')
        settings = data.get('settings', {})
        
        success = settings_manager.update_user_settings(user_id, settings)
        return jsonify({"success": success})

    @app.route('/api/settings/user/get', methods=['POST'])
    def api_settings_get_user_settings():
        data = request.get_json()
        user_id = data.get('user_id')
        
        settings = settings_manager.get_user_settings(user_id)
        return jsonify({"settings": settings})

    @app.route('/api/settings/user/permissions', methods=['POST'])
    def api_settings_user_permissions():
        data = request.get_json()
        user_id = data.get('user_id')
        
        user = settings_manager.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user_id,
            "permissions": list(user.get_effective_permissions()),
            "features": list(user.get_effective_features()),
            "roles": [role.id for role in user.roles]
        })

    # Session API
    @app.route('/api/session/login', methods=['POST'])
    def api_session_login():
        data = request.get_json()
        user_id = data.get('user_id')
        username = data.get('username', '')
        remember_me = data.get('remember_me', False)
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        session = session_manager.create_session(user_id, username, remember_me)
        result = {
            "success": True,
            "session": session.to_dict()
        }
        
        if remember_me and session.remember_me_token:
            result["remember_me_token"] = session.remember_me_token.token_id
        
        return jsonify(result)

    @app.route('/api/session/validate', methods=['POST'])
    def api_session_validate():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        valid, message = session_manager.validate_session(session_id)
        return jsonify({"valid": valid, "message": message})

    @app.route('/api/session/logout', methods=['POST'])
    def api_session_logout():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        session_manager.logout(session_id)
        return jsonify({"success": True, "message": "已成功退出"})

    @app.route('/api/session/lock', methods=['POST'])
    def api_session_lock():
        data = request.get_json()
        session_id = data.get('session_id')
        reason = data.get('reason', '暂时锁定')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        session_manager.lock_session(session_id, reason)
        return jsonify({"success": True, "message": "会话已锁定"})

    @app.route('/api/session/unlock', methods=['POST'])
    def api_session_unlock():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        session_manager.unlock_session(session_id)
        return jsonify({"success": True, "message": "会话已解锁"})

    @app.route('/api/session/force_logout', methods=['POST'])
    def api_session_force_logout():
        data = request.get_json()
        session_id = data.get('session_id')
        reason = data.get('reason', '非法操作')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        session_manager.force_logout(session_id, reason)
        return jsonify({"success": True, "message": "已强行退出"})

    @app.route('/api/session/logout_all', methods=['POST'])
    def api_session_logout_all():
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        session_manager.logout_all(user_id)
        return jsonify({"success": True, "message": "已退出所有会话"})

    @app.route('/api/session/force_logout_all', methods=['POST'])
    def api_session_force_logout_all():
        data = request.get_json()
        user_id = data.get('user_id')
        reason = data.get('reason', '强制退出')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        session_manager.force_logout_all(user_id, reason)
        return jsonify({"success": True, "message": "已强制退出所有会话"})

    @app.route('/api/session/statistics', methods=['GET'])
    def api_session_statistics():
        stats = session_manager.get_statistics()
        return jsonify(stats)

    @app.route('/api/session/user_sessions', methods=['POST'])
    def api_session_user_sessions():
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        sessions = session_manager.get_user_sessions(user_id)
        return jsonify({
            "user_id": user_id,
            "sessions": [s.to_dict() for s in sessions if s]
        })

    @app.route('/api/session/logs', methods=['POST'])
    def api_session_logs():
        data = request.get_json()
        user_id = data.get('user_id')
        limit = data.get('limit', 100)
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        logs = session_manager.log.get_logs_by_user(user_id, limit)
        return jsonify({"logs": logs})

    @app.route('/api/session/extend', methods=['POST'])
    def api_session_extend():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        session_manager.update_session_activity(session_id)
        return jsonify({"success": True, "message": "会话已延长"})

    @app.route('/api/session/auto_login', methods=['POST'])
    def api_session_auto_login():
        data = request.get_json()
        token_id = data.get('token_id')
        
        if not token_id:
            return jsonify({"error": "Missing token_id"}), 400
        
        session = session_manager.auto_login(token_id)
        if session:
            result = {
                "success": True,
                "session": session.to_dict(),
                "remember_me_token": session.remember_me_token.token_id if session.remember_me_token else None
            }
            return jsonify(result)
        return jsonify({"error": "无效的记住我令牌"}), 401

    @app.route('/api/session/refresh_token', methods=['POST'])
    def api_session_refresh_token():
        data = request.get_json()
        token_id = data.get('token_id')
        
        if not token_id:
            return jsonify({"error": "Missing token_id"}), 400
        
        new_token_id = session_manager.refresh_remember_me_token(token_id)
        if new_token_id:
            return jsonify({"success": True, "new_token_id": new_token_id})
        return jsonify({"error": "刷新令牌失败"}), 401

    @app.route('/api/session/revoke_remember_me', methods=['POST'])
    def api_session_revoke_remember_me():
        data = request.get_json()
        token_id = data.get('token_id')
        
        if not token_id:
            return jsonify({"error": "Missing token_id"}), 400
        
        session_manager.revoke_remember_me_token(token_id)
        return jsonify({"success": True, "message": "记住我令牌已撤销"})

    @app.route('/api/session/revoke_all_remember_me', methods=['POST'])
    def api_session_revoke_all_remember_me():
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        session_manager.revoke_all_remember_me_tokens(user_id)
        return jsonify({"success": True, "message": "用户所有记住我令牌已撤销"})

    @app.route('/api/session/logout_with_revoke', methods=['POST'])
    def api_session_logout_with_revoke():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        session_manager.logout(session_id, revoke_remember_me=True)
        return jsonify({"success": True, "message": "已退出并撤销记住我令牌"})

    # Encryption API
    @app.route('/api/encryption/enable', methods=['POST'])
    def api_encryption_enable():
        data = request.get_json()
        key_id = data.get('key_id')
        
        encryption_manager.enable_encryption(key_id)
        return jsonify({"success": True, "message": "数据库加密已启用"})

    @app.route('/api/encryption/disable', methods=['POST'])
    def api_encryption_disable():
        encryption_manager.disable_encryption()
        return jsonify({"success": True, "message": "数据库加密已禁用"})

    @app.route('/api/encryption/status', methods=['GET'])
    def api_encryption_status():
        status = {
            "enabled": encryption_manager.encrypted,
            "active_key_id": encryption_manager.encryption_key_id,
            "tables": encryption_manager.get_all_tables_config()
        }
        return jsonify(status)

    @app.route('/api/encryption/generate_key', methods=['POST'])
    def api_encryption_generate_key():
        data = request.get_json()
        key_type = data.get('key_type', 'aes')
        
        key_id = encryption_manager.generate_encryption_key(key_type)
        return jsonify({"success": True, "key_id": key_id})

    @app.route('/api/encryption/rotate_keys', methods=['POST'])
    def api_encryption_rotate_keys():
        new_key_id = encryption_manager.rotate_keys()
        return jsonify({"success": True, "new_key_id": new_key_id})

    @app.route('/api/encryption/configure_column', methods=['POST'])
    def api_encryption_configure_column():
        data = request.get_json()
        table_name = data.get('table_name')
        column_name = data.get('column_name')
        encrypted = data.get('encrypted', False)
        hash_column = data.get('hash_column', False)
        
        if not table_name or not column_name:
            return jsonify({"error": "Missing table_name or column_name"}), 400
        
        encryption_manager.configure_column(table_name, column_name, encrypted, hash_column=hash_column)
        return jsonify({"success": True, "message": "列加密配置已更新"})

    @app.route('/api/encryption/encrypt_data', methods=['POST'])
    def api_encryption_encrypt_data():
        data = request.get_json()
        table_name = data.get('table_name')
        column_name = data.get('column_name')
        plain_data = data.get('data')
        
        if not table_name or not column_name or plain_data is None:
            return jsonify({"error": "Missing table_name, column_name, or data"}), 400
        
        encrypted = encryption_manager.encrypt_column_data(table_name, column_name, str(plain_data))
        return jsonify({"success": True, "encrypted_data": encrypted.decode('utf-8', errors='ignore')})

    @app.route('/api/encryption/decrypt_data', methods=['POST'])
    def api_encryption_decrypt_data():
        data = request.get_json()
        table_name = data.get('table_name')
        column_name = data.get('column_name')
        encrypted_data = data.get('data')
        
        if not table_name or not column_name or encrypted_data is None:
            return jsonify({"error": "Missing table_name, column_name, or data"}), 400
        
        decrypted = encryption_manager.decrypt_column_data(table_name, column_name, encrypted_data.encode('utf-8'))
        return jsonify({"success": True, "decrypted_data": decrypted})

    @app.route('/api/encryption/hash_data', methods=['POST'])
    def api_encryption_hash_data():
        data = request.get_json()
        plain_data = data.get('data')
        salt = data.get('salt')
        
        if plain_data is None:
            return jsonify({"error": "Missing data"}), 400
        
        hashed = encryption_manager.key_manager.hash_data(str(plain_data), salt)
        return jsonify({"success": True, "hash": hashed})

    @app.route('/api/encryption/verify_hash', methods=['POST'])
    def api_encryption_verify_hash():
        data = request.get_json()
        plain_data = data.get('data')
        hash_value = data.get('hash')
        salt = data.get('salt')
        
        if plain_data is None or hash_value is None:
            return jsonify({"error": "Missing data or hash"}), 400
        
        verified = encryption_manager.key_manager.verify_hash(str(plain_data), hash_value, salt)
        return jsonify({"success": verified, "message": "验证成功" if verified else "验证失败"})

    @app.route('/api/encryption/export_keys', methods=['POST'])
    def api_encryption_export_keys():
        data = request.get_json()
        file_path = data.get('file_path', 'encryption_keys.json')
        password = data.get('password')
        
        encryption_manager.export_keys(file_path, password)
        return jsonify({"success": True, "message": f"密钥已导出到 {file_path}"})

    @app.route('/api/encryption/table_config', methods=['POST'])
    def api_encryption_table_config():
        data = request.get_json()
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({"error": "Missing table_name"}), 400
        
        config = encryption_manager.get_table_config(table_name)
        if config:
            return jsonify({"success": True, "config": config})
        return jsonify({"error": "Table not found"}), 404


    # ==================== 年级管理API ====================
    @app.route('/api/grade/select', methods=['POST'])
    def api_grade_select():
        data = request.get_json()
        user_id = data.get('user_id')
        grade = data.get('grade')
        
        if not user_id or not grade:
            return jsonify({"error": "Missing user_id or grade"}), 400
        
        student_grade = exam_manager.create_student_grade(user_id)
        try:
            grade_level = GradeLevel(grade)
        except ValueError:
            return jsonify({"error": "Invalid grade"}), 400
        
        success = student_grade.select_grade(grade_level)
        return jsonify({"success": success, "message": "年级选择成功" if success else "无法选择年级"})

    @app.route('/api/grade/confirm', methods=['POST'])
    def api_grade_confirm():
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        student_grade = exam_manager.get_student_grade(user_id)
        if not student_grade:
            return jsonify({"error": "User not found"}), 404
        
        success = student_grade.confirm_grade()
        return jsonify({"success": success, "message": "年级确认成功" if success else "无法确认年级"})

    @app.route('/api/grade/info', methods=['POST'])
    def api_grade_info():
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        student_grade = exam_manager.get_student_grade(user_id)
        if not student_grade:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user_id,
            "current_grade": student_grade.current_grade.value if student_grade.current_grade else None,
            "is_confirmed": student_grade.is_grade_confirmed,
            "can_change": student_grade.can_change_grade
        })


    # ==================== 考试管理API ====================
    @app.route('/api/exam/create', methods=['POST'])
    def api_exam_create():
        data = request.get_json()
        user_id = data.get('user_id')
        subject = data.get('subject')
        exam_type = data.get('exam_type')
        grade = data.get('grade')
        
        if not user_id or not subject or not exam_type or not grade:
            return jsonify({"error": "Missing required fields"}), 400
        
        try:
            subject_enum = Subject(subject)
            exam_type_enum = ExamType(exam_type)
            grade_enum = GradeLevel(grade)
        except ValueError:
            return jsonify({"error": "Invalid parameter"}), 400
        
        exam = exam_manager.create_exam(user_id, subject_enum, exam_type_enum, grade_enum)
        return jsonify({"success": True, "exam_id": exam.exam_id, "max_score": exam.max_score})

    @app.route('/api/exam/start', methods=['POST'])
    def api_exam_start():
        data = request.get_json()
        exam_id = data.get('exam_id')
        
        # 这里需要实现从存储中找到考试对象
        return jsonify({"success": True, "message": "考试已开始"})

    @app.route('/api/exam/complete', methods=['POST'])
    def api_exam_complete():
        data = request.get_json()
        exam_id = data.get('exam_id')
        score = data.get('score')
        
        # 这里需要实现从存储中找到考试对象
        return jsonify({"success": True, "message": "考试已完成"})


    # ==================== 教师管理API ====================
    @app.route('/api/teacher/delegate', methods=['POST'])
    def api_teacher_delegate():
        data = request.get_json()
        user_id = data.get('user_id')
        username = data.get('username')
        name = data.get('name')
        created_by = data.get('created_by')
        specialties = data.get('specialties', [])
        grades = data.get('grades', [])
        
        if not user_id or not username or not name or not created_by:
            return jsonify({"error": "Missing required fields"}), 400
        
        specialty_list = []
        for s in specialties:
            try:
                specialty_list.append(TeacherSpecialty(s))
            except ValueError:
                continue
        
        teacher = teacher_manager.delegate_teacher(user_id, username, name, created_by, specialty_list, grades)
        return jsonify({"success": True, "teacher": teacher.to_dict()})

    @app.route('/api/teacher/list', methods=['GET'])
    def api_teacher_list():
        teachers = teacher_manager.get_all_teachers()
        return jsonify({"teachers": [t.to_dict() for t in teachers]})

    @app.route('/api/teacher/info', methods=['POST'])
    def api_teacher_info():
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        
        if not teacher_id:
            return jsonify({"error": "Missing teacher_id"}), 400
        
        teacher = teacher_manager.get_teacher(teacher_id)
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404
        
        return jsonify({"teacher": teacher.to_dict()})


    # ==================== 申请审批API ====================
    @app.route('/api/application/grade_change/create', methods=['POST'])
    def api_application_grade_change_create():
        data = request.get_json()
        user_id = data.get('user_id')
        current_grade = data.get('current_grade')
        new_grade = data.get('new_grade')
        reason = data.get('reason', '')
        
        if not user_id or not current_grade or not new_grade:
            return jsonify({"error": "Missing required fields"}), 400
        
        application = application_manager.create_grade_change_application(user_id, current_grade, new_grade, reason)
        return jsonify({"success": True, "application": application.to_dict()})

    @app.route('/api/application/exam_pause/create', methods=['POST'])
    def api_application_exam_pause_create():
        data = request.get_json()
        user_id = data.get('user_id')
        exam_id = data.get('exam_id')
        subject = data.get('subject')
        reason = data.get('reason', '')
        
        if not user_id or not exam_id or not subject:
            return jsonify({"error": "Missing required fields"}), 400
        
        application = application_manager.create_exam_pause_application(user_id, exam_id, subject, reason)
        return jsonify({"success": True, "application": application.to_dict()})

    @app.route('/api/application/list/pending', methods=['GET'])
    def api_application_list_pending():
        applications = application_manager.get_pending_applications()
        return jsonify({"applications": [app.to_dict() for app in applications]})

    @app.route('/api/application/user/list', methods=['POST'])
    def api_application_user_list():
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        applications = application_manager.get_user_applications(user_id)
        return jsonify({"applications": [app.to_dict() for app in applications]})

    @app.route('/api/application/approve', methods=['POST'])
    def api_application_approve():
        data = request.get_json()
        application_id = data.get('application_id')
        reviewed_by = data.get('reviewed_by')
        comment = data.get('comment', '')
        
        if not application_id or not reviewed_by:
            return jsonify({"error": "Missing required fields"}), 400
        
        application = application_manager.approve_application(application_id, reviewed_by, comment)
        if application:
            return jsonify({"success": True, "application": application.to_dict()})
        return jsonify({"error": "Application not found or already reviewed"}), 400

    @app.route('/api/application/reject', methods=['POST'])
    def api_application_reject():
        data = request.get_json()
        application_id = data.get('application_id')
        reviewed_by = data.get('reviewed_by')
        comment = data.get('comment', '')
        
        if not application_id or not reviewed_by:
            return jsonify({"error": "Missing required fields"}), 400
        
        application = application_manager.reject_application(application_id, reviewed_by, comment)
        if application:
            return jsonify({"success": True, "application": application.to_dict()})
        return jsonify({"error": "Application not found or already reviewed"}), 400

    return app

def setup_scheduled_tasks():
    """Setup scheduled tasks"""
    def daily_backup():
        logger.info("Running daily backup task")
        try:
            from core.database import db
            db.backup()
            logger.info("Daily backup completed")
        except Exception as e:
            logger.error(f"Daily backup failed: {e}")

    def hourly_health_check():
        logger.debug("Running hourly health check")
        try:
            health = system.get_health_report()
            if health['status'] != 'healthy':
                logger.warning(f"Health check warning: {health}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def cache_cleanup():
        logger.debug("Running cache cleanup")
        try:
            cache.clear()
            logger.info("Cache cleanup completed")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    scheduler.add_task("daily_backup", daily_backup, "daily", at="02:00")
    scheduler.add_task("hourly_health", hourly_health_check, "hourly")
    scheduler.add_task("weekly_cache_cleanup", cache_cleanup, "weekly", day="sunday", at="03:00")
    scheduler.add_task("performance_monitor", system.log_system_status, "interval", minutes=30)
    logger.info("Scheduled tasks registered")

def register_queue_handlers():
    """Register queue task handlers"""
    def process_ai_request(payload):
        logger.debug(f"Processing AI request: {payload}")
        try:
            prompt = payload.get("prompt", "")
            result = ai_service.generate(prompt)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return {"success": False, "error": str(e)}

    def process_data_export(payload):
        logger.debug(f"Processing data export: {payload}")
        return {"success": True}

    def process_intelligence_analysis(payload):
        logger.debug(f"Processing intelligence analysis: {payload}")
        try:
            data = payload.get("data", [])
            analysis_type = payload.get("type", "auto")
            result = intelligence.analyze_data(data, analysis_type)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Intelligence analysis failed: {e}")
            return {"success": False, "error": str(e)}

    queue_manager.register_handler("ai_request", process_ai_request)
    queue_manager.register_handler("data_export", process_data_export)
    queue_manager.register_handler("intelligence_analysis", process_intelligence_analysis)
    logger.info("Queue handlers registered")

def main():
    """Main entry point"""
    logger.info(f"Starting MTSCOS AI Project v{__version__}...")
    logger.info("Intelligence features: Pattern Analysis, Text Analysis, Data Classification")
    logger.info("Knowledge features: Entity Management, Relation Mapping, Graph Query")
    logger.info("Recommendation features: Collaborative Filtering, Content-Based, Hybrid")
    logger.info("Education AI: Researcher, Expert, Teacher, Student AI")
    logger.info("Question Bank: Optimization, Expansion, Exam Papers, Practice Generator")

    core_init()
    setup_scheduled_tasks()
    register_queue_handlers()

    scheduler.start()
    queue_manager.start()
    logger.info("Scheduler and Queue Manager started")

    app = create_app()
    host = config.get("api.host", "0.0.0.0")
    port = config.get("api.port", 5001)
    logger.info(f"Starting API server on {host}:{port}")

    try:
        app.run(host=host, port=port, debug=config.get("api.debug", False))
    finally:
        scheduler.stop()
        queue_manager.stop()
        logger.info("Scheduler and Queue Manager stopped")

if __name__ == "__main__":
    main()

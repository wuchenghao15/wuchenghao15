# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from app.models.question import Question
from app.models.system_config import SystemConfig
from app.ai.brain_updater import AIBrainUpdater
from app.ai.exam_generator import ExamGenerator
from app.services.ai_brain_service import ai_brain_service
import json
import sys

# 创建AI脑库API蓝图
ai_brain_api = Blueprint(r'ai_brain_api', __name__)

@ai_brain_api.route(r'/')
def ai_brain_root():
    r"""AI脑库API根路径r"""
    return jsonify({r'status': r'ok', r'message': r'AI Brain API is running'})

@ai_brain_api.route(r'/questions')
def get_questions():
    r"""获取AI脑库题库r"""
    subject = request.args.get(r'subject', r'japanese')
    difficulty = request.args.get(r'difficulty', r'all')
    question_type = request.args.get(r'type', r'all')
    limit = request.args.get(r'limit', 10, type=int)

    questions = Question.get_questions(subject, difficulty, question_type, limit)

    return jsonify({
        r'count': len(questions),
        r'subject': subject,
        r'difficulty': difficulty,
        r'type': question_type,
        r'questions': questions
    })

@ai_brain_api.route(r'/generate-questions', methods=[r'POST'])
def generate_questions():
    r"""AI生成新问题r"""
    data = request.get_json() or {}
    subject = data.get(r'subject', r'japanese')
    difficulty = data.get(r'difficulty', r'medium')
    question_type = data.get(r'type', r'multiple_choice')
    count = data.get(r'count', 5)

    updater = AIBrainUpdater()
    new_questions = updater.generate_questions(subject, difficulty, question_type, count)

    return jsonify({
        r'message': r'Questions generated successfully',
        r'count': len(new_questions),
        r'questions': new_questions
    })

@ai_brain_api.route(r'/exam', methods=[r'POST'])
def generate_exam():
    r"""生成个性化考试r"""
    user_preferences = request.get_json() or {}
    generator = ExamGenerator()
    exam = generator.generate_personalized_exam(user_preferences)
    return jsonify(exam)

@ai_brain_api.route(r'/status')
def get_ai_brain_status():
    r"""获取AI脑库状态r"""
    config = SystemConfig.get_all_configs()
    total_questions = Question.get_question_count()
    japanese_questions = Question.get_question_count(r'japanese')
    english_questions = Question.get_question_count(r'english')

    return jsonify({
        r'status': r'active',
        r'total_questions': total_questions,
        r'japanese_questions': japanese_questions,
        r'english_questions': english_questions,
        r'config': {c.config_key: c.config_value for c in config}
    })

@ai_brain_api.route(r'/validate-knowledge/<knowledge_id>')
def validate_knowledge(knowledge_id):
    r"""验证单个知识条目r"""
    result = ai_brain_service.validate_knowledge(knowledge_id)

    if result:
        return jsonify({
            r'success': True,
            r'data': result
        })
    else:
        return jsonify({
            r'success': False,
            r'message': r'知识验证失败'
        }), 404

@ai_brain_api.route(r'/validate-knowledge/batch', methods=[r'POST'])
def batch_validate_knowledge():
    r"""批量验证知识r"""
    data = request.get_json() or {}
    limit = data.get(r'limit')
    results = ai_brain_service.batch_validate_knowledge(limit=limit)

    return jsonify({
        r'data': {
            r'total_validated': len(results),
            r'results': results
        }
    })

@ai_brain_api.route(r'/validation-report')
def get_validation_report():
    r"""获取知识验证报告r"""
    report = ai_brain_service.get_validation_report()

    if report:
        return jsonify({
            r'success': True,
            r'data': report
        })
    else:
        return jsonify({
            r'success': False,
            r'message': r'获取验证报告失败'
        }), 500

@ai_brain_api.route(r'/knowledge-by-status/<status>')
def get_knowledge_by_status(status):
    r"""根据验证状态获取知识r"""
    knowledge_list = ai_brain_service.get_knowledge_by_status(status)
    knowledge_dict = []

    for knowledge in knowledge_list:
        knowledge_dict.append({
            r'knowledge_id': knowledge.knowledge_id,
            r'title': knowledge.title,
            r'content': knowledge.content,
            r'knowledge_type': knowledge.knowledge_type,
            r'source': knowledge.source,
            r'tags': knowledge.tags,
            r'priority': knowledge.priority,
            r'is_active': knowledge.is_active,
            r'review_status': knowledge.review_status,
            r'confidence_score': knowledge.confidence_score,
            r'created_at': knowledge.created_at,
            r'updated_at': knowledge.updated_at,
            r'reviewed_at': knowledge.reviewed_at,
            r'reviewed_by': knowledge.reviewed_by
        })

    return jsonify({
        r'success': True,
        r'data': {
            r'status': status,
            r'count': len(knowledge_dict),
            r'knowledge': knowledge_dict
        }
    })

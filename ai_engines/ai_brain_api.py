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
ai_brain_api = Blueprint('ai_brain_api', __name__)

@ai_brain_api.route('/')
def ai_brain_root():
    """AI脑库API根路径"""
    return jsonify({'status': 'ok', 'message': 'AI Brain API is running'})

@ai_brain_api.route('/questions')
def get_questions():
    """获取AI脑库题库"""
    subject = request.args.get('subject', 'japanese')
    difficulty = request.args.get('difficulty', 'all')
    question_type = request.args.get('type', 'all')
    limit = request.args.get('limit', 10, type=int)

    questions = Question.get_questions(subject, difficulty, question_type, limit)

    return jsonify({
        'count': len(questions),
        'subject': subject,
        'difficulty': difficulty,
        'type': question_type,
        'questions': questions
    })

@ai_brain_api.route('/generate-questions', methods=['POST'])
def generate_questions():
    """AI生成新问题"""
    data = request.get_json() or {}
    subject = data.get('subject', 'japanese')
    difficulty = data.get('difficulty', 'medium')
    question_type = data.get('type', 'multiple_choice')
    count = data.get('count', 5)

    updater = AIBrainUpdater()
    new_questions = updater.generate_questions(subject, difficulty, question_type, count)

    return jsonify({
        'message': 'Questions generated successfully',
        'count': len(new_questions),
        'questions': new_questions
    })

@ai_brain_api.route('/exam', methods=['POST'])
def generate_exam():
    """生成个性化考试"""
    user_preferences = request.get_json() or {}
    generator = ExamGenerator()
    exam = generator.generate_personalized_exam(user_preferences)
    return jsonify(exam)

@ai_brain_api.route('/status')
def get_ai_brain_status():
    """获取AI脑库状态"""
    config = SystemConfig.get_all_configs()
    total_questions = Question.get_question_count()
    japanese_questions = Question.get_question_count('japanese')
    english_questions = Question.get_question_count('english')

    return jsonify({
        'status': 'active',
        'total_questions': total_questions,
        'japanese_questions': japanese_questions,
        'english_questions': english_questions,
        'config': {c.config_key: c.config_value for c in config}
    })

@ai_brain_api.route('/validate-knowledge/<knowledge_id>')
def validate_knowledge(knowledge_id):
    """验证单个知识条目"""
    result = ai_brain_service.validate_knowledge(knowledge_id)

    if result:
        return jsonify({
            'success': True,
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'message': '知识验证失败'
        }), 404

@ai_brain_api.route('/validate-knowledge/batch', methods=['POST'])
def batch_validate_knowledge():
    """批量验证知识"""
    data = request.get_json() or {}
    limit = data.get('limit')
    results = ai_brain_service.batch_validate_knowledge(limit=limit)

    return jsonify({
        'data': {
            'total_validated': len(results),
            'results': results
        }
    })

@ai_brain_api.route('/validation-report')
def get_validation_report():
    """获取知识验证报告"""
    report = ai_brain_service.get_validation_report()

    if report:
        return jsonify({
            'success': True,
            'data': report
        })
    else:
        return jsonify({
            'success': False,
            'message': '获取验证报告失败'
        }), 500

@ai_brain_api.route('/knowledge-by-status/<status>')
def get_knowledge_by_status(status):
    """根据验证状态获取知识"""
    knowledge_list = ai_brain_service.get_knowledge_by_status(status)
    knowledge_dict = []
    
    for knowledge in knowledge_list:
        knowledge_dict.append({
            'knowledge_id': knowledge.knowledge_id,
            'title': knowledge.title,
            'content': knowledge.content,
            'knowledge_type': knowledge.knowledge_type,
            'source': knowledge.source,
            'tags': knowledge.tags,
            'priority': knowledge.priority,
            'is_active': knowledge.is_active,
            'review_status': knowledge.review_status,
            'confidence_score': knowledge.confidence_score,
            'created_at': knowledge.created_at,
            'updated_at': knowledge.updated_at,
            'reviewed_at': knowledge.reviewed_at,
            'reviewed_by': knowledge.reviewed_by
        })

    return jsonify({
        'success': True,
        'data': {
            'status': status,
            'count': len(knowledge_dict),
            'knowledge': knowledge_dict
        }
    })

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成人教育与K12题库API
支持全学段题库查询、管理和统计
"""

from flask import Blueprint, request, jsonify
from app.services.adult_k12_question_bank_service import adult_k12_question_bank

adult_k12_api = Blueprint('adult_k12_api', __name__)


@adult_k12_api.route('/api/adult_k12/questions', methods=['GET'])
def get_questions():
    filters = {}
    
    if 'stage' in request.args:
        filters['stage'] = request.args['stage']
    if 'subject' in request.args:
        filters['subject'] = request.args['subject']
    if 'type' in request.args:
        filters['type'] = request.args['type']
    if 'difficulty' in request.args:
        filters['difficulty'] = request.args['difficulty']
    
    questions = adult_k12_question_bank.get_questions(filters)
    
    return jsonify({
        'status': 'success',
        'data': questions,
        'total': len(questions)
    })


@adult_k12_api.route('/api/adult_k12/questions', methods=['POST'])
def add_question():
    try:
        data = request.get_json()
        
        required_fields = ['stage', 'subject', 'type', 'difficulty', 'content', 'correct_answer']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        question_id = adult_k12_question_bank.add_question(data)
        
        return jsonify({
            'status': 'success',
            'message': '题目添加成功',
            'question_id': question_id
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@adult_k12_api.route('/api/adult_k12/questions/batch', methods=['POST'])
def add_questions_batch():
    try:
        data = request.get_json()
        
        if 'questions' not in data or not isinstance(data['questions'], list):
            return jsonify({
                'status': 'error',
                'message': '缺少questions列表'
            }), 400
        
        success, failed = adult_k12_question_bank.add_questions_batch(data['questions'])
        
        return jsonify({
            'status': 'success',
            'message': f'批量添加完成',
            'success': success,
            'failed': failed
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@adult_k12_api.route('/api/adult_k12/questions/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    try:
        success = adult_k12_question_bank.delete_question(question_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '题目删除成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '题目不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@adult_k12_api.route('/api/adult_k12/stats', methods=['GET'])
def get_stats():
    stats = adult_k12_question_bank.get_stats()
    
    return jsonify({
        'status': 'success',
        'data': stats
    })


@adult_k12_api.route('/api/adult_k12/stages', methods=['GET'])
def get_stages():
    stages = {
        'primary': '小学',
        'junior_high': '初中',
        'senior_high': '高中',
        'vocational': '职业教育',
        'college': '专科',
        'undergraduate': '本科',
        'adult_exam': '成人高考',
        'self_exam': '自学考试',
        'professional_cert': '职业资格'
    }
    
    return jsonify({
        'status': 'success',
        'data': stages
    })


@adult_k12_api.route('/api/adult_k12/subjects', methods=['GET'])
def get_subjects():
    subjects = {
        'chinese': '语文',
        'math': '数学',
        'english': '英语',
        'physics': '物理',
        'chemistry': '化学',
        'biology': '生物',
        'history': '历史',
        'geography': '地理',
        'politics': '政治',
        'computer': '计算机',
        'economics': '经济学',
        'law': '法律',
        'management': '管理学',
        'accounting': '会计学'
    }
    
    return jsonify({
        'status': 'success',
        'data': subjects
    })
#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_intelligent_evaluation import intelligent_evaluation_system

ai_evaluation_api = Bluelogger.info('ai_evaluation_api', __name__)

@ai_evaluation_api.route('/api/ai/evaluation/evaluate', methods=['POST'])
@require_login
def evaluate():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    evaluation_type = data.get('evaluation_type')
    eval_data = data.get('data', {})
    
    if not user_id or not evaluation_type:
        return jsonify({'success': False, 'error': '用户ID和评估类型不能为空'}), 400
    
    result = intelligent_evaluation_system.evaluate(user_id, evaluation_type, eval_data)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_evaluation_api.route('/api/ai/evaluation/<evaluation_id>', methods=['GET'])
@require_login
def get_evaluation(evaluation_id):
    result = intelligent_evaluation_system.get_evaluation(evaluation_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '评估记录不存在'}), 404

@ai_evaluation_api.route('/api/ai/evaluation/user', methods=['GET'])
@require_login
def get_user_evaluations():
    user_id = request.args.get('user_id')
    evaluation_type = request.args.get('type')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = intelligent_evaluation_system.get_user_evaluations(user_id, evaluation_type)
    return jsonify({'success': True, 'data': result, 'count': len(result)})

@ai_evaluation_api.route('/api/ai/evaluation/trend', methods=['GET'])
@require_login
def get_user_evaluation_trend():
    user_id = request.args.get('user_id')
    evaluation_type = request.args.get('type')
    
    if not user_id or not evaluation_type:
        return jsonify({'success': False, 'error': '用户ID和评估类型不能为空'}), 400
    
    result = intelligent_evaluation_system.get_user_evaluation_trend(user_id, evaluation_type)
    return jsonify({'success': True, 'data': result})

@ai_evaluation_api.route('/api/ai/evaluation/summary', methods=['GET'])
@require_login
def get_evaluation_summary():
    result = intelligent_evaluation_system.get_evaluation_summary()
    return jsonify({'success': True, 'data': result})

@ai_evaluation_api.route('/api/ai/evaluation/types', methods=['GET'])
@require_login
def get_evaluation_types():
    return jsonify({
        'success': True,
        'data': {
            'evaluation_types': intelligent_evaluation_system.EVALUATION_TYPES,
            'evaluation_methods': intelligent_evaluation_system.EVALUATION_METHODS,
            'rating_scale': intelligent_evaluation_system.RATING_SCALE
        }
    })

@ai_evaluation_api.route('/api/ai/evaluation/criteria', methods=['GET'])
@require_login
def get_evaluation_criteria():
    evaluation_type = request.args.get('type')
    
    try:
        import sqlite3
        conn = sqlite3.connect('intelligent_evaluation.db')
        cursor = conn.cursor()
        
        if evaluation_type:
            cursor.execute('SELECT * FROM evaluation_criteria WHERE evaluation_type = ? AND is_active = 1',
            (evaluation_type,))
        else:
            cursor.execute('SELECT * FROM evaluation_criteria WHERE is_active = 1')
        
        rows = cursor.fetchall()
        conn.close()
        
        criteria = []
        for row in rows:
            criteria.append({
                'criteria_id': row[1],
                'criteria_name': row[2],
                'evaluation_type': row[3],
                'weight': row[4],
                'description': row[5],
                'min_score': row[6],
                'max_score': row[7]
            })
        
        return jsonify({'success': True, 'data': criteria})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
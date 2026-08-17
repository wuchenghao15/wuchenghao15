#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_professional_role import ai_professional_role_system

ai_professional_api = Bluelogger.info('ai_professional_api', __name__)

@ai_professional_api.route('/api/ai/professional/roles', methods=['GET'])
@require_login
def list_roles():
    roles = ai_professional_role_system.list_all_roles()
    return jsonify({'success': True, 'data': roles})

@ai_professional_api.route('/api/ai/professional/assign', methods=['POST'])
@require_admin
def assign_role():
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    employee_name = data.get('employee_name')
    role_type = data.get('role_type')
    
    if not employee_id or not employee_name or not role_type:
        return jsonify({'success': False, 'error': '员工ID、员工名称和职业角色类型不能为空'}), 400
    
    result = ai_professional_role_system.assign_role(employee_id, employee_name, role_type)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('message'),
    'available_roles': result.get('available_roles')}), 400

@ai_professional_api.route('/api/ai/professional/role/<employee_id>', methods=['GET'])
@require_login
def get_role(employee_id):
    result = ai_professional_role_system.get_role(employee_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('message')}), 404

@ai_professional_api.route('/api/ai/professional/thinking', methods=['POST'])
@require_admin
def trigger_thinking():
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    employee_name = data.get('employee_name')
    current_skills = data.get('current_skills', {})
    
    if not employee_id or not employee_name:
        return jsonify({'success': False, 'error': '员工ID和员工名称不能为空'}), 400
    
    result = ai_professional_role_system.trigger_independent_thinking(employee_id, employee_name, current_skills)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('message')}), 400

@ai_professional_api.route('/api/ai/professional/thinking/history/<employee_id>', methods=['GET'])
@require_login
def get_thinking_history(employee_id):
    history = ai_professional_role_system.thinking_engine.get_thinking_history(employee_id)
    return jsonify({'success': True, 'data': history})

@ai_professional_api.route('/api/ai/professional/learning/plan/<employee_id>', methods=['GET'])
@require_login
def get_learning_plan(employee_id):
    result = ai_professional_role_system.get_learning_plan(employee_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('message')}), 404

@ai_professional_api.route('/api/ai/professional/learning/plan/<employee_id>', methods=['PUT'])
@require_admin
def update_learning_plan(employee_id):
    data = request.get_json() or {}
    progress = data.get('progress')
    skill_name = data.get('skill_name')
    
    if progress is None:
        return jsonify({'success': False, 'error': '进度不能为空'}), 400
    
    result = ai_professional_role_system.thinking_engine.update_plan_progress(employee_id, progress, skill_name)
    if result:
        return jsonify({'success': True, 'message': '学习计划进度更新成功'})
    return jsonify({'success': False, 'error': '更新失败'}), 400

@ai_professional_api.route('/api/ai/professional/web_learning', methods=['POST'])
@require_admin
def trigger_web_learning():
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    employee_name = data.get('employee_name')
    topic = data.get('topic')
    
    if not employee_id or not employee_name or not topic:
        return jsonify({'success': False, 'error': '员工ID、员工名称和学习主题不能为空'}), 400
    
    result = ai_professional_role_system.trigger_web_learning(employee_id, employee_name, topic)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('message')}), 400

@ai_professional_api.route('/api/ai/professional/knowledge/<employee_id>', methods=['GET'])
@require_login
def get_knowledge_base(employee_id):
    domain = request.args.get('domain')
    result = ai_professional_role_system.get_knowledge_base(employee_id)
    if domain:
        knowledge = [k for k in result.get('knowledge_base', []) if k.get('domain') == domain]
        return jsonify({'success': True, 'data': {'knowledge_base': knowledge, 'count': len(knowledge)}})
    return jsonify({'success': True, 'data': result})

@ai_professional_api.route('/api/ai/professional/learning/history/<employee_id>', methods=['GET'])
@require_login
def get_learning_history(employee_id):
    history = ai_professional_role_system.internet_learning.get_learning_history(employee_id)
    return jsonify({'success': True, 'data': history})

@ai_professional_api.route('/api/ai/professional/summary', methods=['GET'])
@require_login
def get_summary():
    summaries = ai_professional_role_system.get_professional_summary()
    return jsonify({'success': True, 'data': summaries})

@ai_professional_api.route('/api/ai/professional/overview', methods=['GET'])
@require_admin
def get_overview():
    overview = ai_professional_role_system.get_all_employees_overview()
    return jsonify({'success': True, 'data': overview})

@ai_professional_api.route('/api/ai/professional/search', methods=['POST'])
@require_login
def search_knowledge():
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    topic = data.get('topic')
    
    if not employee_id or not topic:
        return jsonify({'success': False, 'error': '员工ID和搜索主题不能为空'}), 400
    
    results = ai_professional_role_system.internet_learning.search_knowledge(topic, employee_id)
    return jsonify({'success': True, 'data': results})

@ai_professional_api.route('/api/ai/professional/skill_gaps/<employee_id>', methods=['GET'])
@require_login
def get_skill_gaps(employee_id):
    try:
        import sqlite3
        conn = sqlite3.connect('professional_role.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM skill_gaps WHERE employee_id = ? AND resolved = 0', (employee_id,))
        rows = cursor.fetchall()
        conn.close()
        
        gaps = []
        for row in rows:
            gaps.append({
                'id': row[0],
                'skill_name': row[2],
                'current_level': row[3],
                'target_level': row[4],
                'gap_score': row[5],
                'priority': row[6],
                'action_plan': row[7]
            })
        return jsonify({'success': True, 'data': gaps})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@ai_professional_api.route('/api/ai/professional/skill_gaps/<gap_id>', methods=['PUT'])
@require_admin
def resolve_skill_gap(gap_id):
    try:
        import sqlite3
        conn = sqlite3.connect('professional_role.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE skill_gaps SET resolved = 1 WHERE id = ?', (gap_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '技能缺口已标记为已解决'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
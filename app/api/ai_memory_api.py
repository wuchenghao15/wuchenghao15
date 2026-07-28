#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_memory_system import ai_memory_system

ai_memory_api = Bluelogger.info('ai_memory_api', __name__)

@ai_memory_api.route('/api/ai/memory/add', methods=['POST'])
@require_login
def add_memory():
    data = request.get_json() or {}
    memory_type = data.get('memory_type')
    content = data.get('content')
    summary = data.get('summary', '')
    tags = data.get('tags', [])
    source = data.get('source', '')
    author = data.get('author', 'system')
    metadata = data.get('metadata', {})
    
    if not memory_type or not content:
        return jsonify({'success': False, 'error': '记忆类型和内容不能为空'}), 400
    
    result = ai_memory_system.add_memory(memory_type, content, summary, tags, source, author, metadata)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/search', methods=['GET'])
@require_login
def search_memories():
    query = request.args.get('query', '')
    memory_type = request.args.get('type')
    tags = request.args.getlist('tags')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
    
    result = ai_memory_system.search_memories(query, memory_type, tags, limit)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/<memory_id>', methods=['GET'])
@require_login
def get_memory(memory_id):
    result = ai_memory_system.get_memory(memory_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '记忆不存在'}), 404

@ai_memory_api.route('/api/ai/memory/<memory_id>', methods=['PUT'])
@require_login
def update_memory(memory_id):
    data = request.get_json() or {}
    content = data.get('content')
    summary = data.get('summary')
    tags = data.get('tags')
    priority = data.get('priority')
    status = data.get('status')
    
    result = ai_memory_system.update_memory(memory_id, content, summary, tags, priority, status)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/<memory_id>', methods=['DELETE'])
@require_admin
def delete_memory(memory_id):
    result = ai_memory_system.delete_memory(memory_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/relation', methods=['POST'])
@require_login
def add_relation():
    data = request.get_json() or {}
    source_memory_id = data.get('source_memory_id')
    target_memory_id = data.get('target_memory_id')
    relation_type = data.get('relation_type')
    confidence = data.get('confidence', 0.8)
    
    if not source_memory_id or not target_memory_id or not relation_type:
        return jsonify({'success': False, 'error': '源记忆ID、目标记忆ID和关系类型不能为空'}), 400
    
    result = ai_memory_system.add_memory_relation(source_memory_id, target_memory_id, relation_type, confidence)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/<memory_id>/relations', methods=['GET'])
@require_login
def get_relations(memory_id):
    result = ai_memory_system.get_memory_relations(memory_id)
    return jsonify({'success': True, 'data': result})

@ai_memory_api.route('/api/ai/memory/types', methods=['GET'])
@require_login
def get_memories_by_type():
    memory_type = request.args.get('type')
    if not memory_type:
        return jsonify({'success': False, 'error': '记忆类型不能为空'}), 400
    
    result = ai_memory_system.get_memories_by_type(memory_type)
    return jsonify({'success': True, 'data': result, 'count': len(result)})

@ai_memory_api.route('/api/ai/memory/summary', methods=['GET'])
@require_login
def get_memory_summary():
    result = ai_memory_system.get_memory_summary()
    return jsonify({'success': True, 'data': result})

@ai_memory_api.route('/api/ai/memory/cleanup', methods=['POST'])
@require_admin
def auto_cleanup():
    result = ai_memory_system.auto_cleanup()
    if result.get('success'):
        return jsonify({'success': True, 'message': '自动清理完成'})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/insight', methods=['POST'])
@require_login
def generate_insight():
    data = request.get_json() or {}
    memory_ids = data.get('memory_ids', [])
    
    if not memory_ids:
        return jsonify({'success': False, 'error': '记忆ID列表不能为空'}), 400
    
    result = ai_memory_system.generate_insight(memory_ids)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_memory_api.route('/api/ai/memory/types/list', methods=['GET'])
@require_login
def get_memory_types():
    return jsonify({
        'success': True,
        'data': {
            'memory_types': ai_memory_system.MEMORY_TYPES,
            'priorities': ai_memory_system.MEMORY_PRIORITIES,
            'status_values': ai_memory_system.MEMORY_STATUS
        }
    })
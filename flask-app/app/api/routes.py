#!/usr/bin/env python3
"""API路由管理模块,实现统一的API路由管理系统"""

from flask import jsonify, request
from app.api import api_bp
from app.services.rule_management import rule_management_service
from app.services.ai_brain_service import ai_brain_service
from app.services.exam_service import exam_service
from app.utils.logging import logger

API_VERSION = "v1"

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API健康检查"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'api_version': API_VERSION,
            'service': 'MTSCOS API'
        }
    })

@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        rule_status = rule_management_service.get_rules()
        brain_status = ai_brain_service.get_status()
        exam_status = exam_service.get_status()

        return jsonify({
            'success': True,
            'data': {
                'api_version': API_VERSION,
                'rule_management': {
                    'rules_count': sum(len(rules) for rules in rule_status.values())
                },
                'ai_brain': {
                    'status': brain_status.get('status', 'unknown'),
                    'knowledge_count': brain_status.get('knowledge_count', 0)
                },
                'exam_service': {
                    'status': exam_status.get('status', 'unknown'),
                    'questions_count': exam_status.get('questions_count', 0)
                }
            }
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取系统状态失败: {str(e)}'
        }), 500

@api_bp.route('/handshake', methods=['POST'])
def handshake():
    """API握手端点"""
    try:
        import uuid
        import time

        session_id = str(uuid.uuid4())
        api_key = str(uuid.uuid4())

        return jsonify({
            'success': True,
            'data': {
                'sessionId': session_id,
                'apiKey': api_key,
                'apiVersion': API_VERSION,
                'timestamp': int(time.time())
            }
        })
    except Exception as e:
        logger.error(f"握手失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'握手失败: {str(e)}'
        }), 500

@api_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """API心跳端点"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'ok',
                'timestamp': int(time.time())
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'心跳失败: {str(e)}'
        }), 500

@api_bp.route('/docs', methods=['GET'])
def get_api_docs():
    """获取API文档"""
    docs = {
        'api_version': API_VERSION,
        'endpoints': [
            {
                'path': '/api/health',
                'method': 'GET',
                'description': 'API健康检查'
            },
            {
                'path': '/api/status',
                'method': 'GET',
                'description': '获取系统状态'
            },
            {
                'path': '/api/handshake',
                'method': 'POST',
                'description': 'API握手'
            },
            {
                'path': '/api/heartbeat',
                'method': 'POST',
                'description': 'API心跳'
            },
            {
                'path': '/api/exam/list',
                'method': 'GET',
                'description': '获取考试列表'
            },
            {
                'path': '/api/exam/questions',
                'method': 'GET',
                'description': '获取考试题目'
            },
            {
                'path': '/api/exam/generate',
                'method': 'POST',
                'description': '生成试卷'
            },
            {
                'path': '/api/exam/<exam_id>',
                'method': 'GET',
                'description': '获取考试详情'
            }
        ],
        'rate_limit': {
            'enabled': True,
            'limit': '100 requests per minute'
        }
    }

    return jsonify({
        'success': True,
        'data': docs
    })

@api_bp.route('/rules', methods=['GET'])
def get_rules():
    """获取所有规则"""
    try:
        rules = rule_management_service.get_rules()
        return jsonify({
            'success': True,
            'data': rules
        })
    except Exception as e:
        logger.error(f"获取规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取规则失败: {str(e)}'
        }), 500

@api_bp.route('/rules/<rule_type>', methods=['GET'])
def get_rules_by_type(rule_type):
    """根据类型获取规则"""
    try:
        rules = rule_management_service.get_rules(rule_type)
        return jsonify({
            'success': True,
            'data': rules
        })
    except Exception as e:
        logger.error(f"获取规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取规则失败: {str(e)}'
        }), 500

@api_bp.route('/ai-brain/status', methods=['GET'])
def get_ai_brain_status():
    """获取AI脑库状态"""
    try:
        status = ai_brain_service.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取AI脑库状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取AI脑库状态失败: {str(e)}'
        }), 500

@api_bp.route('/exam/list', methods=['GET'])
def get_exam_list():
    """获取考试列表"""
    try:
        exams = exam_service.get_exam_list()
        return jsonify({
            'success': True,
            'data': exams
        })
    except Exception as e:
        logger.error(f"获取考试列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取考试列表失败: {str(e)}'
        }), 500

@api_bp.route('/exam/questions', methods=['GET'])
def get_exam_questions():
    """获取考试题目"""
    try:
        questions = exam_service.get_questions()
        return jsonify({
            'success': True,
            'data': questions
        })
    except Exception as e:
        logger.error(f"获取考试题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取考试题目失败: {str(e)}'
        }), 500

@api_bp.route('/exam/generate', methods=['POST'])
def generate_exam():
    """生成试卷"""
    try:
        data = request.json or {}
        exam = exam_service.generate_exam(data)
        return jsonify({
            'success': True,
            'data': exam
        })
    except Exception as e:
        logger.error(f"生成试卷失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'生成试卷失败: {str(e)}'
        }), 500

@api_bp.route('/exam/<exam_id>', methods=['GET'])
def get_exam_detail(exam_id):
    """获取考试详情"""
    try:
        exam = exam_service.get_exam(exam_id)
        return jsonify({
            'success': True,
            'data': exam
        })
    except Exception as e:
        logger.error(f"获取考试详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取考试详情失败: {str(e)}'
        }), 500
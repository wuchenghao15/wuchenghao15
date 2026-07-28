# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

import json
from flask import Blueprint, jsonify, request

matrix_bp = Blueprint('matrix', __name__, url_prefix='/api/matrix')

@matrix_bp.route('/types', methods=['GET'])
def get_matrix_types():
    try:
        types = matrix_manager.get_matrix_types()
        return jsonify({
            'success': True,
            'data': types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/types', methods=['POST'])
def create_matrix_type():
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        dimensions = data.get('dimensions', [])

        if not name:
            return jsonify({
                'success': False,
                'error': '名称不能为空'
            }), 400

        matrix_type_id = matrix_manager.create_matrix_type(name, description, dimensions)

        return jsonify({
            'success': True,
            'data': {'id': matrix_type_id}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/data', methods=['GET'])
def get_matrix_data():
    try:
        matrix_type_id = request.args.get('matrix_type_id')
        data = matrix_manager.get_matrix_data(matrix_type_id)

        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/data', methods=['POST'])
def create_matrix_data():
    try:
        data = request.json
        matrix_type_id = data.get('matrix_type_id')
        name = data.get('name')
        description = data.get('description', '')
        matrix_data = data.get('data', {})
        metadata = data.get('metadata', {})

        if not matrix_type_id or not name:
            return jsonify({
                'success': False,
                'error': '矩阵类型ID和名称不能为空'
            }), 400

        matrix_id = matrix_manager.create_matrix_data(matrix_type_id, name,
                                                        description, matrix_data,
                                                        metadata)

        return jsonify({
            'success': True,
            'data': {'id': matrix_id}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/knowledge-points', methods=['GET'])
def get_knowledge_points():
    try:
        subject = request.args.get('subject')
        grade = request.args.get('grade')

        points = matrix_manager.get_knowledge_points(subject, grade)

        return jsonify({
            'success': True,
            'data': points
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/knowledge-points', methods=['POST'])
def create_knowledge_point():
    try:
        data = request.json
        subject = data.get('subject')
        grade = data.get('grade')
        chapter = data.get('chapter')
        name = data.get('name')
        description = data.get('description', '')
        difficulty = data.get('difficulty', 1)
        importance = data.get('importance', 3)
        tags = data.get('tags', [])

        if not subject or not grade or not name:
            return jsonify({
                'success': False,
                'error': '学科、年级和名称不能为空'
            }), 400

        kp_id = matrix_manager.create_knowledge_point(subject, grade, chapter,
                                                       name, description, difficulty,
                                                       importance, tags)

        return jsonify({
            'success': True,
            'data': {'id': kp_id}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/abilities', methods=['GET'])
def get_abilities():
    try:
        abilities = matrix_manager.get_ability_dimensions()

        return jsonify({
            'success': True,
            'data': abilities
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/question-mapping', methods=['POST'])
def map_question():
    try:
        data = request.json
        question_id = data.get('question_id')
        matrix_data_id = data.get('matrix_data_id')
        dimension_values = data.get('dimension_values', {})

        if not question_id or not matrix_data_id:
            return jsonify({
                'success': False,
                'error': '题目ID和矩阵数据ID不能为空'
            }), 400

        mapping_id = matrix_manager.map_question_to_matrix(question_id, matrix_data_id,
                                                            dimension_values)

        return jsonify({
            'success': True,
            'data': {'id': mapping_id}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/question-mapping/<question_id>', methods=['GET'])
def get_question_mapping(question_id):
    try:
        mappings = matrix_manager.get_question_matrix_mapping(question_id)

        return jsonify({
            'success': True,
            'data': mappings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/analyze/coverage', methods=['GET'])
def analyze_coverage():
    try:
        subject = request.args.get('subject')
        grade = request.args.get('grade')

        if not subject or not grade:
            return jsonify({
                'success': False,
                'error': '请提供学科和年级'
            }), 400

        analysis = matrix_manager.analyze_coverage(subject, grade)

        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/analyze/difficulty', methods=['GET'])
def analyze_difficulty():
    try:
        subject = request.args.get('subject')
        grade = request.args.get('grade')

        if not subject or not grade:
            return jsonify({
                'success': False,
                'error': '请提供学科和年级'
            }), 400

        analysis = matrix_manager.get_difficulty_distribution(subject, grade)

        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/generate/knowledge-ability', methods=['POST'])
def generate_knowledge_ability_matrix():
    try:
        data = request.json
        subject = data.get('subject')
        grade = data.get('grade')

        if not subject or not grade:
            return jsonify({
                'success': False,
                'error': '请提供学科和年级'
            }), 400

        matrix = matrix_manager.generate_knowledge_ability_matrix(subject, grade)

        return jsonify({
            'success': True,
            'data': matrix
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@matrix_bp.route('/generate/coverage', methods=['POST'])
def generate_coverage_matrix():
    try:
        data = request.json
        subject = data.get('subject')
        grade = data.get('grade')

        if not subject or not grade:
            return jsonify({
                'success': False,
                'error': '请提供学科和年级'
            }), 400

        matrix = matrix_manager.generate_coverage_matrix(subject, grade)

        return jsonify({
            'success': True,
            'data': matrix
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# -*- coding: utf-8 -*-
"""
AI题库优化API
提供智能题库分析和优化接口
"""

from flask import Blueprint, jsonify, request
from app.ai.question_bank_ai import question_bank_ai
from app.utils.logging import logger

question_bank_ai_api = Blueprint('question_bank_ai_api', __name__)


@question_bank_ai_api.route('/ai/analyze', methods=['POST'])
def analyze_question():
    """分析单个题目"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少题目内容'
            }), 400
        
        # 分析题目
        analysis = question_bank_ai.analyze_question(data)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        logger.error(f"题目分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@question_bank_ai_api.route('/ai/optimize', methods=['POST'])
def optimize_question():
    """优化单个题目"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少题目内容'
            }), 400
        
        # 优化题目
        optimized = question_bank_ai.optimize_question(data)
        
        return jsonify({
            'success': True,
            'optimized_question': optimized
        })
    
    except Exception as e:
        logger.error(f"题目优化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@question_bank_ai_api.route('/ai/batch-optimize', methods=['POST'])
def batch_optimize():
    """批量优化题目"""
    try:
        data = request.get_json()
        
        if not data or 'questions' not in data:
            return jsonify({
                'success': False,
                'error': '缺少题目列表'
            }), 400
        
        questions = data['questions']
        
        # 批量处理
        results = question_bank_ai.process_question_batch(questions, optimize=True)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"批量优化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@question_bank_ai_api.route('/ai/suggestions', methods=['POST'])
def get_suggestions():
    """获取优化建议"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少题目内容'
            }), 400
        
        # 生成建议
        suggestions = question_bank_ai.generate_suggestions(data)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    
    except Exception as e:
        logger.error(f"生成建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@question_bank_ai_api.route('/ai/statistics')
def get_statistics():
    """获取统计报告"""
    try:
        report = question_bank_ai.get_statistics_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@question_bank_ai_api.route('/ai/summary')
def get_summary():
    """获取优化摘要"""
    try:
        summary = question_bank_ai.get_optimization_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"获取摘要失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@question_bank_ai_api.route('/ai/capabilities')
def get_capabilities():
    """获取AI员工能力"""
    capabilities = {
        'name': 'AI题库优化员工',
        'version': '1.0.0',
        'capabilities': [
            {
                'name': '题目分析',
                'description': '智能分析题目内容、难度、类型',
                'methods': ['analyze_difficulty', 'analyze_type', 'extract_keywords']
            },
            {
                'name': '质量评估',
                'description': '评估题目质量并提供改进建议',
                'methods': ['assess_quality', 'generate_suggestions']
            },
            {
                'name': '题目优化',
                'description': '自动优化题目格式和内容',
                'methods': ['optimize_question', 'batch_optimize']
            },
            {
                'name': '统计分析',
                'description': '题库统计分析和报告生成',
                'methods': ['get_statistics', 'get_summary']
            }
        ],
        'features': [
            '自动难度分析',
            '智能类型识别',
            '关键词提取',
            '质量评分',
            '批量处理',
            '优化建议生成'
        ]
    }
    
    return jsonify({
        'success': True,
        'capabilities': capabilities
    })

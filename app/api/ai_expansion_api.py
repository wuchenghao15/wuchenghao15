#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.intelligent_assessment import AIIntelligentAssessment
from app.ai.intelligent_search import AIIntelligentSearch

ai_expansion_api = Bluelogger.info('ai_expansion_api', __name__)

@ai_expansion_api.route('/api/ai/assessment/user/<user_id>', methods=['GET'])
def assess_user_knowledge(user_id):
    """评估用户知识掌握程度"""
    try:
        assessor = AIIntelligentAssessment()
        assessment = assessor.assess_user_knowledge(user_id)
        assessor.close()
        
        return jsonify({
            'success': True,
            'data': assessment
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expansion_api.route('/api/ai/assessment/report/<user_id>', methods=['GET'])
def generate_assessment_report(user_id):
    """生成评估报告"""
    try:
        assessor = AIIntelligentAssessment()
        report = assessor.generate_assessment_report(user_id)
        assessor.save_assessment(report)
        assessor.close()
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expansion_api.route('/api/ai/assessment/history/<user_id>', methods=['GET'])
def get_assessment_history(user_id):
    """获取评估历史"""
    limit = int(request.args.get('limit', 10))
    
    try:
        assessor = AIIntelligentAssessment()
        history = assessor.get_user_assessment_history(user_id, limit)
        assessor.close()
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expansion_api.route('/api/ai/search', methods=['GET'])
def search():
    """综合搜索"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    
    if not query:
        return jsonify({
            'success': False,
            'error': '查询参数q不能为空'
        }), 400
    
    try:
        searcher = AIIntelligentSearch()
        results = searcher.search(query, limit=limit)
        searcher.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expansion_api.route('/api/ai/search/advanced', methods=['POST'])
def advanced_search():
    """高级搜索"""
    data = request.get_json() or {}
    query = data.get('query', '')
    filters = data.get('filters')
    sort_by = data.get('sort_by', 'score')
    limit = int(data.get('limit', 20))
    
    if not query:
        return jsonify({
            'success': False,
            'error': '查询参数不能为空'
        }), 400
    
    try:
        searcher = AIIntelligentSearch()
        results = searcher.advanced_search(query, filters, sort_by, limit)
        searcher.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expansion_api.route('/api/ai/search/suggestions', methods=['GET'])
def search_suggestions():
    """搜索建议"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 5))
    
    if not query:
        return jsonify({
            'success': False,
            'error': '查询参数q不能为空'
        }), 400
    
    try:
        searcher = AIIntelligentSearch()
        suggestions = searcher.search_suggestions(query, limit)
        searcher.close()
        
        return jsonify({
            'success': True,
            'data': suggestions,
            'count': len(suggestions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expansion_api.route('/api/ai/search/stats', methods=['GET'])
def search_stats():
    """搜索统计"""
    try:
        searcher = AIIntelligentSearch()
        stats = searcher.get_search_stats()
        searcher.close()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
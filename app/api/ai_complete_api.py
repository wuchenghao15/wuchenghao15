#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.learning_tracker import AILearningTracker
from app.ai.intelligent_qna import AIIntelligentQNA

ai_complete_api = Bluelogger.info('ai_complete_api', __name__)

@ai_complete_api.route('/api/ai/tracker/daily', methods=['GET'])
def get_daily_stats():
    """获取每日学习统计"""
    user_id = request.args.get('user_id', '1')
    
    try:
        tracker = AILearningTracker()
        stats = tracker.get_daily_stats(user_id)
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/tracker/weekly', methods=['GET'])
def get_weekly_stats():
    """获取本周学习统计"""
    user_id = request.args.get('user_id', '1')
    
    try:
        tracker = AILearningTracker()
        stats = tracker.get_weekly_stats(user_id)
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': stats,
            'count': len(stats)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/tracker/monthly', methods=['GET'])
def get_monthly_progress():
    """获取月度学习进度"""
    user_id = request.args.get('user_id', '1')
    
    try:
        tracker = AILearningTracker()
        progress = tracker.get_monthly_progress(user_id)
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': progress,
            'count': len(progress)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/tracker/trend', methods=['GET'])
def get_learning_trend():
    """获取学习趋势"""
    user_id = request.args.get('user_id', '1')
    days = int(request.args.get('days', 30))
    
    try:
        tracker = AILearningTracker()
        trend = tracker.get_learning_trend(user_id, days)
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': trend,
            'count': len(trend)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/tracker/summary', methods=['GET'])
def get_learning_summary():
    """获取学习综合摘要"""
    user_id = request.args.get('user_id', '1')
    
    try:
        tracker = AILearningTracker()
        summary = tracker.get_learning_summary(user_id)
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/tracker/ranking', methods=['GET'])
def get_user_ranking():
    """获取用户学习排行榜"""
    try:
        tracker = AILearningTracker()
        ranking = tracker.get_user_ranking()
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': ranking,
            'count': len(ranking)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/tracker/report', methods=['GET'])
def generate_progress_report():
    """生成学习进度报告"""
    user_id = request.args.get('user_id', '1')
    
    try:
        tracker = AILearningTracker()
        report = tracker.generate_progress_report(user_id)
        tracker.close()
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/qna/answer', methods=['POST'])
def answer_question():
    """回答问题"""
    data = request.get_json() or {}
    question = data.get('question', '')
    
    if not question:
        return jsonify({
            'success': False,
            'error': '问题不能为空'
        }), 400
    
    try:
        qna = AIIntelligentQNA()
        answer = qna.answer_question(question)
        qna.save_question_answer(question, answer)
        qna.close()
        
        return jsonify({
            'success': True,
            'data': answer
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/qna/frequent', methods=['GET'])
def get_frequent_questions():
    """获取常见问题"""
    limit = int(request.args.get('limit', 10))
    
    try:
        qna = AIIntelligentQNA()
        questions = qna.get_frequent_questions(limit)
        qna.close()
        
        return jsonify({
            'success': True,
            'data': questions,
            'count': len(questions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_complete_api.route('/api/ai/qna/knowledge', methods=['GET'])
def query_knowledge():
    """查询知识库"""
    question = request.args.get('q', '')
    
    if not question:
        return jsonify({
            'success': False,
            'error': '查询参数q不能为空'
        }), 400
    
    try:
        qna = AIIntelligentQNA()
        results = qna.query_knowledge(question, 5)
        qna.close()
        
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
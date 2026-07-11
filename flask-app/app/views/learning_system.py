# -*- coding: utf-8 -*-
"""
学习系统视图模块
负责学习记录、错题本、学习分析等功能
使用统一权限装饰器进行权限控制
包含学习路径规划、错题智能推荐、知识图谱可视化等增强功能
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from app.middlewares.permission_decorators import require_student_or_vip, get_permission_info, require_login
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

learning_system_bp = Blueprint('learning_system', __name__)

# 数据库路径配置
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


def get_user_info():
    """获取当前用户信息"""
    return get_permission_info()


@learning_system_bp.route('/learning_system')
@require_student_or_vip
def learning_system_index():
    """学习系统首页"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问学习系统")
    
    return render_template('learning_system.html', user=user_info)


@learning_system_bp.route('/learning/history')
@require_student_or_vip
def learning_history():
    """学习历史记录页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问学习历史")
    
    return render_template('learning_history.html', user=user_info)


@learning_system_bp.route('/learning/wrong_questions')
@require_student_or_vip
def wrong_questions():
    """错题本页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问错题本")
    
    return render_template('wrong_questions.html', user=user_info)


@learning_system_bp.route('/learning/analysis')
@require_student_or_vip
def learning_analysis():
    """学习分析页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问学习分析")
    
    return render_template('learning_analysis.html', user=user_info)


# ==================== 学习增强功能页面 ====================

@learning_system_bp.route('/learning/path')
@require_student_or_vip
def learning_path_page():
    """学习路径规划页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问学习路径规划")
    
    return render_template('learning_path.html', user=user_info)


@learning_system_bp.route('/learning/wrong_recommend')
@require_student_or_vip
def wrong_question_recommend_page():
    """错题智能推荐页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问错题智能推荐")
    
    return render_template('wrong_question_recommend.html', user=user_info)


@learning_system_bp.route('/learning/knowledge_graph')
@require_student_or_vip
def knowledge_graph_page():
    """知识图谱可视化页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问知识图谱")
    
    return render_template('knowledge_graph.html', user=user_info)


@learning_system_bp.route('/learning/comprehensive')
@require_student_or_vip
def comprehensive_analysis_page():
    """综合学习分析页面"""
    user_info = get_user_info()
    logger.info(f"[学习系统] 用户 {user_info['username']} ({user_info['role']}) 访问综合分析")
    
    return render_template('learning_comprehensive.html', user=user_info)


@learning_system_bp.route('/api/learning/user_info')
@require_login
def api_get_user_info():
    """获取当前用户信息"""
    user_info = get_permission_info()
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'role': user_info['role'],
            'email': session.get('email', '')
        }
    })


@learning_system_bp.route('/api/learning/history', methods=['GET'])
@require_student_or_vip
def get_learning_history():
    """获取学习历史记录"""
    user_id = session.get('user_id')
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM learning_records 
                WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 20
            ''', (user_id,))
            records = cursor.fetchall()
            
            history = []
            for record in records:
                history.append({
                    'id': record['id'],
                    'subject': record.get('subject', ''),
                    'content': record.get('content', ''),
                    'duration': record.get('duration', 0),
                    'created_at': record.get('created_at', '')
                })
        
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        logger.error(f"获取学习历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_system_bp.route('/api/learning/wrong_questions', methods=['GET'])
@require_student_or_vip
def get_wrong_questions():
    """获取错题列表"""
    user_id = session.get('user_id')
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM wrong_questions 
                WHERE user_id = ? 
                ORDER BY wrong_count DESC LIMIT 30
            ''', (user_id,))
            questions = cursor.fetchall()
            
            wrong_list = []
            for q in questions:
                wrong_list.append({
                    'id': q['id'],
                    'question_id': q.get('question_id', ''),
                    'content': q.get('content', ''),
                    'wrong_count': q.get('wrong_count', 0),
                    'last_wrong_at': q.get('last_wrong_at', '')
                })
        
        return jsonify({'success': True, 'data': wrong_list})
    except Exception as e:
        logger.error(f"获取错题列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
# -*- coding: utf-8 -*-
"""
错误反馈API
处理用户在错误页面提交的问题反馈
"""

from flask import Blueprint, request, jsonify, session
import sqlite3
import os
from datetime import datetime
from app.utils.logging import logger

error_feedback_bp = Blueprint('error_feedback', __name__, url_prefix='/api')

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')


@error_feedback_bp.route('/error-feedback', methods=['POST'])
def submit_error_feedback():
    """
    提交错误反馈
    
    接收用户在错误页面提交的问题反馈，保存到数据库
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        # 提取反馈信息
        error_id = data.get('error_id', '')
        error_code = data.get('error_code', 0)
        contact = data.get('contact', '')
        description = data.get('description', '')
        timestamp = data.get('timestamp', '')
        
        # 验证必填字段
        if not description or not description.strip():
            return jsonify({
                'success': False,
                'message': '请填写问题描述'
            }), 400
        
        # 获取用户信息
        user_id = session.get('user_id')
        username = session.get('username')
        role = session.get('role', 'guest')
        
        # 保存到数据库
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 创建反馈表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT,
                    error_code INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    role TEXT,
                    contact TEXT,
                    description TEXT,
                    timestamp TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    processed_by TEXT,
                    response TEXT
                )
            ''')
            
            # 插入反馈记录
            cursor.execute('''
                INSERT INTO error_feedbacks 
                (error_id, error_code, user_id, username, role, contact, description, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (error_id, error_code, user_id, username, role, contact, description, timestamp))
            
            conn.commit()
            
            logger.info(f"错误反馈已保存: error_id={error_id}, user={username}")
        
        # 触发AI自动处理
        try:
            from app.services.error_report_service import error_report_service, ErrorLevel, ErrorCategory
            
            # 创建错误报告
            report = error_report_service.report_error(
                message=f"用户反馈: {description}",
                error_type="UserFeedback",
                level=ErrorLevel.WARNING,
                category=ErrorCategory.SYSTEM,
                context={
                    'error_id': error_id,
                    'error_code': error_code,
                    'user_contact': contact,
                    'feedback_source': 'error_page'
                },
                user_id=str(user_id) if user_id else None
            )
            
            logger.info(f"AI错误处理已触发: {report.error_id}")
            
        except ImportError:
            logger.warning("错误上报服务未找到，跳过AI处理")
        except Exception as e:
            logger.error(f"AI错误处理触发失败: {e}")
        
        return jsonify({
            'success': True,
            'message': '反馈已提交，我们会尽快处理',
            'feedback_id': cursor.lastrowid if 'cursor' in locals() else None
        }), 200
        
    except Exception as e:
        logger.error(f"提交错误反馈失败: {e}")
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


@error_feedback_bp.route('/error-feedbacks', methods=['GET'])
def get_error_feedbacks():
    """
    获取错误反馈列表（管理员接口）
    
    需要管理员权限
    """
    try:
        # 检查权限
        role = session.get('role')
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
        
        # 获取参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'all')
        
        # 查询数据库
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            where_clause = ''
            params = []
            
            if status != 'all':
                where_clause = 'WHERE status = ?'
                params.append(status)
            
            # 获取总数
            cursor.execute(f'''
                SELECT COUNT(*) FROM error_feedbacks {where_clause}
            ''', params)
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            offset = (page - 1) * per_page
            cursor.execute(f'''
                SELECT id, error_id, error_code, username, role, contact, 
                       description, timestamp, status, created_at, processed_at
                FROM error_feedbacks {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', params + [per_page, offset])
            
            feedbacks = []
            for row in cursor.fetchall():
                feedbacks.append({
                    'id': row[0],
                    'error_id': row[1],
                    'error_code': row[2],
                    'username': row[3],
                    'role': row[4],
                    'contact': row[5],
                    'description': row[6],
                    'timestamp': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'processed_at': row[10]
                })
        
        return jsonify({
            'success': True,
            'data': {
                'feedbacks': feedbacks,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取错误反馈列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@error_feedback_bp.route('/error-feedbacks/<int:feedback_id>', methods=['GET'])
def get_error_feedback(feedback_id):
    """
    获取单个错误反馈详情（管理员接口）
    """
    try:
        # 检查权限
        role = session.get('role')
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
        
        # 查询数据库
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, error_id, error_code, user_id, username, role, 
                       contact, description, timestamp, status, created_at, 
                       processed_at, processed_by, response
                FROM error_feedbacks
                WHERE id = ?
            ''', (feedback_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'message': '反馈不存在'
                }), 404
            
            feedback = {
                'id': row[0],
                'error_id': row[1],
                'error_code': row[2],
                'user_id': row[3],
                'username': row[4],
                'role': row[5],
                'contact': row[6],
                'description': row[7],
                'timestamp': row[8],
                'status': row[9],
                'created_at': row[10],
                'processed_at': row[11],
                'processed_by': row[12],
                'response': row[13]
            }
        
        return jsonify({
            'success': True,
            'data': feedback
        }), 200
        
    except Exception as e:
        logger.error(f"获取错误反馈详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@error_feedback_bp.route('/error-feedbacks/<int:feedback_id>/process', methods=['POST'])
def process_error_feedback(feedback_id):
    """
    处理错误反馈（管理员接口）
    
    标记反馈为已处理，并添加处理回复
    """
    try:
        # 检查权限
        role = session.get('role')
        username = session.get('username')
        
        if role not in ['admin', 'super_admin', 'hardware_admin']:
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
        
        data = request.get_json()
        response = data.get('response', '')
        status = data.get('status', 'processed')
        
        if not response:
            return jsonify({
                'success': False,
                'message': '请填写处理回复'
            }), 400
        
        # 更新数据库
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE error_feedbacks
                SET status = ?, response = ?, processed_at = ?, processed_by = ?
                WHERE id = ?
            ''', (status, response, datetime.now(), username, feedback_id))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '反馈不存在'
                }), 404
        
        logger.info(f"错误反馈已处理: feedback_id={feedback_id}, by={username}")
        
        return jsonify({
            'success': True,
            'message': '反馈已处理'
        }), 200
        
    except Exception as e:
        logger.error(f"处理错误反馈失败: {e}")
        return jsonify({
            'success': False,
            'message': f'处理失败: {str(e)}'
        }), 500


@error_feedback_bp.route('/error-feedbacks/statistics', methods=['GET'])
def get_feedback_statistics():
    """
    获取错误反馈统计（管理员接口）
    """
    try:
        # 检查权限
        role = session.get('role')
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
        
        # 查询统计
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 确保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT,
                    error_code INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    role TEXT,
                    contact TEXT,
                    description TEXT,
                    timestamp TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    processed_by TEXT,
                    response TEXT
                )
            ''')
            
            # 总数
            cursor.execute('SELECT COUNT(*) FROM error_feedbacks')
            total = cursor.fetchone()[0]
            
            # 按状态统计
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM error_feedbacks 
                GROUP BY status
            ''')
            by_status = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按错误代码统计
            cursor.execute('''
                SELECT error_code, COUNT(*) 
                FROM error_feedbacks 
                GROUP BY error_code
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            by_error_code = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 今日新增
            cursor.execute('''
                SELECT COUNT(*) 
                FROM error_feedbacks 
                WHERE DATE(created_at) = DATE('now')
            ''')
            today_count = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'by_status': by_status,
                'by_error_code': by_error_code,
                'today_count': today_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取反馈统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500

#!/usr/bin/env python3
"""项目历史馆API路由"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, render_template

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.db_path import get_db_path

history_api = Blueprint('history', __name__)

def get_db_connection():
    db_path = get_db_path('app.db')
    return sqlite3.connect(db_path)

@history_api.route('/api/history/stats')
def api_history_stats():
    """获取历史馆统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_versions')
        versions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM upgrade_history')
        upgrades = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_brain_bank')
        knowledge = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_learning_tasks')
        learning = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'versions': versions,
                'upgrades': upgrades,
                'knowledge': knowledge,
                'learning': learning
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@history_api.route('/api/history/timeline')
def api_history_timeline():
    """获取版本时间线"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT version, build_date, codename, description, features, status 
                         FROM system_versions ORDER BY build_date DESC''')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            features = []
            try:
                if row[4]:
                    features = json.loads(row[4])
            except:
                pass
            data.append({
                'version': row[0],
                'build_date': row[1],
                'codename': row[2],
                'description': row[3],
                'features': features,
                'status': row[5] or 'stable'
            })
        
        conn.close()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@history_api.route('/api/history/upgrades')
def api_history_upgrades():
    """获取升级记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT version, upgrade_type, description, ai_employees_count, 
                         features_count, status, created_at FROM upgrade_history ORDER BY created_at DESC''')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'version': row[0],
                'upgrade_type': row[1],
                'description': row[2],
                'ai_employees_count': row[3],
                'features_count': row[4],
                'status': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@history_api.route('/api/history/learning')
def api_history_learning():
    """获取学习任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT task_name, task_desc, task_type, version, status, created_at 
                         FROM ai_learning_tasks ORDER BY created_at DESC''')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'task_name': row[0],
                'task_desc': row[1],
                'task_type': row[2],
                'version': row[3],
                'status': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@history_api.route('/api/history/knowledge')
def api_history_knowledge():
    """获取知识脑库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT category, title, content, tags, version, created_at 
                         FROM ai_brain_bank ORDER BY created_at DESC LIMIT 50''')
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'category': row[0],
                'title': row[1],
                'content': row[2],
                'tags': row[3],
                'version': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@history_api.route('/api/history/rules')
def api_history_rules():
    """获取系统规则"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_rules'")
        if cursor.fetchone():
            cursor.execute('''SELECT rule_id, rule_name, rule_type, description, action, enabled, created_at 
                             FROM system_rules ORDER BY priority DESC, created_at DESC LIMIT 50''')
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'rule_id': row[0],
                    'rule_name': row[1],
                    'rule_type': row[2],
                    'description': row[3],
                    'action': row[4],
                    'enabled': bool(row[5]),
                    'created_at': row[6]
                })
        else:
            data = []
        
        conn.close()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@history_api.route('/history')
def history_page():
    """历史馆页面"""
    return render_template('history_gallery.html')

#!/usr/bin/env python3
""" AI自我学习引擎API 提供自我学习引擎的Web接口，支持触发学习、查看状态、获取学习规则等功能 """

import os
import sys
import json
import functools
from flask import Blueprint, jsonify, request, session

try:
    from flask_wtf.csrf import csrf_exempt
except ImportError:
    csrf_exempt = lambda x: x

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

engine_imported = False
try:
    from ai_self_learning_engine import AISelfLearningEngine
    engine_imported = True
except Exception as e:
    logger.info("[ERROR] 导入AI自我学习引擎失败:", e)

self_learning_api = Bluelogger.info('self_learning_api', __name__)

engine = None

def get_engine():
    global engine
    if engine is None and engine_imported:
        engine = AISelfLearningEngine()
    return engine

def require_admin(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录，请先登录'}), 401
        if session.get('role') not in ['admin', 'super_admin']:
            return jsonify({'success': False, 'error': '权限不足，需要管理员权限'}), 403
        return func(*args, **kwargs)
    return wrapper

@self_learning_api.route('/api/ai/self_learning/status', methods=['GET'])
def get_learning_status():
    try:
        engine = get_engine()
        if engine:
            status = engine.get_learning_status()
            return jsonify({'success': True, 'data': status})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化', 'engine_imported': engine_imported}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/run_once', methods=['POST'])
@csrf_exempt
@require_admin
def run_self_learning_once():
    try:
        engine = get_engine()
        if engine:
            stats = engine.run_self_learning_cycle()
            return jsonify({'success': True, 'data': stats})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/start', methods=['POST'])
@require_admin
def start_auto_learning():
    try:
        engine = get_engine()
        if engine:
            interval = request.json.get('interval', 3600)
            result = engine.start_auto_learning(interval)
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/stop', methods=['POST'])
@require_admin
def stop_auto_learning():
    try:
        engine = get_engine()
        if engine:
            result = engine.stop_auto_learning()
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/network_learning', methods=['POST'])
@require_admin
def run_network_learning():
    try:
        engine = get_engine()
        if engine:
            count = engine._execute_network_learning()
            return jsonify({'success': True, 'network_knowledge': count, 'message': '成功采集 ' + str(count) + ' 个知识点'})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/self_awareness', methods=['POST'])
@require_admin
def run_self_awareness():
    try:
        engine = get_engine()
        if engine:
            count = engine._execute_self_awareness()
            return jsonify({'success': True, 'discovered_insights': count, 'message': '发现 ' + str(count) + ' 条学习洞察'})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/generate_rules', methods=['POST'])
@require_admin
def generate_learning_rules():
    try:
        engine = get_engine()
        if engine:
            count = engine._execute_rule_generation()
            return jsonify({'success': True, 'generated_rules': count, 'message': '成功生成 ' + str(count) + ' 条学习规则'})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/execute_policy', methods=['POST'])
@require_admin
def execute_learning_policy():
    try:
        engine = get_engine()
        if engine:
            count = engine._execute_learning_policy()
            return jsonify({'success': True, 'executed_rules': count, 'message': '成功执行 ' + str(count) + ' 条学习政策'})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/brain_feeding', methods=['POST'])
@require_admin
def run_brain_feeding():
    try:
        engine = get_engine()
        if engine:
            count = engine._execute_brain_feeding()
            return jsonify({'success': True, 'fed_to_brain': count, 'message': '成功投喂 ' + str(count) + ' 条知识到脑库'})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/rules', methods=['GET'])
def get_learning_rules():
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT rule_code, rule_name, rule_value, learning_domain, learning_priority, confidence, execution_count, last_executed, description, created_at FROM learning_rules ORDER BY learning_priority DESC, confidence DESC')

        rules = []
        for row in cursor.fetchall():
            rules.append({
                'rule_code': row[0],
                'rule_name': row[1],
                'rule_value': row[2],
                'learning_domain': row[3],
                'learning_priority': row[4],
                'confidence': row[5],
                'execution_count': row[6],
                'last_executed': row[7],
                'description': row[8],
                'created_at': row[9]
            })

        conn.close()
        return jsonify({'success': True, 'data': rules, 'count': len(rules)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/knowledge_stats', methods=['GET'])
def get_knowledge_stats():
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge')
        total_knowledge = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge WHERE source = "self_learning_engine"')
        self_learning_knowledge = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge WHERE source = "network_learner"')
        network_knowledge = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge WHERE source = "brain_feeding_engine"')
        engine_knowledge = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM brain_feeding_queue')
        feeding_records = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM ai_brain_activity')
        activity_records = cursor.fetchone()[0]

        conn.close()

        stats = {
            'total_knowledge': total_knowledge,
            'self_learning_knowledge': self_learning_knowledge,
            'network_knowledge': network_knowledge,
            'engine_knowledge': engine_knowledge,
            'feeding_records': feeding_records,
            'activity_records': activity_records
        }

        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@self_learning_api.route('/api/ai/self_learning/insights', methods=['GET'])
def get_discovered_insights():
    try:
        engine = get_engine()
        if engine:
            insights = engine.self_awareness_analyzer.get_saved_insights()

            result = []
            for insight in insights[:20]:
                result.append({
                    'type': insight.get('insight_type', ''),
                    'domain': insight.get('domain', ''),
                    'topic': insight.get('topic', ''),
                    'insight': insight.get('insight', ''),
                    'priority': insight.get('priority', 'low'),
                    'confidence': insight.get('confidence', 0),
                    'score': insight.get('score', 0),
                    'source': insight.get('source', ''),
                    'created_at': insight.get('created_at', '')
                })

            return jsonify({'success': True, 'data': result, 'count': len(result)})
        else:
            return jsonify({'success': False, 'error': '引擎未初始化'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

#!/usr/bin/env python3
"""
自动升级维护API
提供AI系统自动升级、脑库投喂、学习训练、神经网络训练、集群统筹等功能
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_auto_upgrade_api = Bluelogger.info('ai_auto_upgrade_api', __name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def _get_brain_feeding_engine():
    try:
        from brain_feeding_engine import BrainFeedingEngine
        return BrainFeedingEngine()
    except Exception as e:
        return None


@ai_auto_upgrade_api.route('/api/ai/upgrade/feed', methods=['POST'])
@require_admin
def trigger_feeding():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.feed_knowledge()
        return jsonify({'success': True, 'message': '脑库投喂完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/feed/network', methods=['POST'])
@require_admin
def trigger_network_feeding():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.feed_from_network()
        return jsonify({'success': True, 'message': '网络知识采集完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/discover', methods=['POST'])
@require_admin
def trigger_discovery():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.discover_learning_directions()
        return jsonify({'success': True, 'message': '学习方向发现完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/learn', methods=['POST'])
@require_admin
def trigger_learning():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.trigger_learning()
        return jsonify({'success': True, 'message': 'AI员工学习完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/upgrade', methods=['POST'])
@require_admin
def trigger_upgrade():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.trigger_upgrade()
        return jsonify({'success': True, 'message': 'AI员工升级完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/train', methods=['POST'])
@require_admin
def trigger_training():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.train_neural_network()
        return jsonify({'success': True, 'message': '神经网络训练完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/coordinate', methods=['POST'])
@require_admin
def trigger_coordination():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.coordinate_clusters()
        return jsonify({'success': True, 'message': '集群统筹完成', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/full', methods=['POST'])
@require_admin
def trigger_full_upgrade():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.run_all()
        return jsonify({
            'success': True,
            'message': '完整升级流程完成',
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'feeding_count': engine.feeding_count,
                'network_learning_count': engine.network_learning_count,
                'learning_count': engine.learning_count,
                'upgrade_count': engine.upgrade_count,
                'coordination_count': engine.coordination_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/network-only', methods=['POST'])
@require_admin
def trigger_network_only():
    engine = _get_brain_feeding_engine()
    if not engine:
        return jsonify({'success': False, 'error': '脑库投喂引擎不可用'}), 503
    
    try:
        engine.run_network_learning()
        return jsonify({
            'success': True,
            'message': '网络学习完成',
            'timestamp': datetime.now().isoformat(),
            'network_learning_count': engine.network_learning_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/stats', methods=['GET'])
@require_admin
def get_upgrade_stats():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM brain_feeding_stats ORDER BY stat_date DESC LIMIT 1")
            latest_stats = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) FROM ai_brain_knowledge")
            knowledge_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
            active_employees = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status = 'active'")
            active_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_connections WHERE status = 'active'")
            active_connections = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
            active_rules = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_upgrade_records WHERE status = 'completed'")
            completed_upgrades = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM brain_learning_records")
            learning_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cluster_coordination_records WHERE status = 'completed'")
            completed_coordinations = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_cluster_config WHERE status = 'active'")
            active_clusters = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(accuracy) FROM ai_employees")
            avg_accuracy = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(proficiency_after) FROM brain_learning_records")
            avg_proficiency = cursor.fetchone()[0] or 0
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'brain_knowledge': {
                'total': knowledge_count
            },
            'ai_employees': {
                'active': active_employees,
                'avg_accuracy': round(avg_accuracy, 4)
            },
            'neural_network': {
                'active_nodes': active_nodes,
                'active_connections': active_connections,
                'density': round(active_connections / max(active_nodes, 1), 2)
            },
            'system_rules': {
                'active': active_rules
            },
            'clusters': {
                'active': active_clusters,
                'completed_coordinations': completed_coordinations
            },
            'learning': {
                'total_records': learning_records,
                'avg_proficiency': round(avg_proficiency, 4)
            },
            'upgrades': {
                'completed': completed_upgrades
            },
            'latest_feeding_stats': {
                'stat_date': latest_stats[1] if latest_stats else None,
                'total_feeds': latest_stats[2] if latest_stats else 0,
                'total_learnings': latest_stats[3] if latest_stats else 0,
                'total_upgrades': latest_stats[4] if latest_stats else 0,
                'total_coordinations': latest_stats[5] if latest_stats else 0
            } if latest_stats else None
        }
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/history', methods=['GET'])
@require_admin
def get_upgrade_history():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            limit = int(request.args.get('limit', 50))
            
            cursor.execute('''
                SELECT * FROM ai_upgrade_records 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                'upgrade_id': row[0],
                'employee_id': row[1],
                'employee_name': row[2],
                'upgrade_type': row[3],
                'upgrade_category': row[4],
                'before_level': row[5],
                'after_level': row[6],
                'before_capabilities': json.loads(row[7]) if row[7] else {},
                'after_capabilities': json.loads(row[8]) if row[8] else {},
                'upgrade_score': row[9],
                'upgrade_data': json.loads(row[10]) if row[10] else {},
                'upgrade_reason': row[11],
                'status': row[12],
                'performed_by': row[13],
                'created_at': row[14]
            })
        
        return jsonify({'success': True, 'data': history, 'count': len(history),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/rules', methods=['GET'])
@require_admin
def get_system_rules():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            
            if active_only:
                cursor.execute("SELECT * FROM system_rules WHERE is_active = 1 ORDER BY priority DESC")
            else:
                cursor.execute("SELECT * FROM system_rules ORDER BY priority DESC")
            
            rows = cursor.fetchall()
        
        rules = []
        for row in rows:
            rules.append({
                'id': row[0],
                'rule_code': row[1],
                'rule_name': row[2],
                'rule_description': row[3],
                'rule_category': row[4],
                'rule_value': row[5],
                'rule_type': row[6],
                'priority': row[7],
                'is_active': bool(row[8]),
                'created_at': row[9],
                'updated_at': row[10],
                'effective_from': row[11],
                'expires_at': row[12],
                'rule_group': row[13],
                'metadata': json.loads(row[14]) if row[14] else {}
            })
        
        return jsonify({'success': True, 'data': rules, 'count': len(rules), 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/rule/<rule_code>', methods=['GET'])
@require_admin
def get_rule_detail(rule_code):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM system_rules WHERE rule_code = ?", (rule_code,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'success': False, 'error': '规则不存在'}), 404
        
        rule = {
            'id': row[0],
            'rule_code': row[1],
            'rule_name': row[2],
            'rule_description': row[3],
            'rule_category': row[4],
            'rule_value': row[5],
            'rule_type': row[6],
            'priority': row[7],
            'is_active': bool(row[8]),
            'created_at': row[9],
            'updated_at': row[10],
            'effective_from': row[11],
            'expires_at': row[12],
            'rule_group': row[13],
            'metadata': json.loads(row[14]) if row[14] else {}
        }
        
        return jsonify({'success': True, 'data': rule, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/rule/<rule_code>', methods=['PUT'])
@require_admin
def update_rule(rule_code):
    try:
        data = request.get_json() or {}
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM system_rules WHERE rule_code = ?", (rule_code,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '规则不存在'}), 404
            
            updates = []
            params = []
            
            if 'rule_value' in data:
                updates.append('rule_value = ?')
                params.append(data['rule_value'])
            if 'is_active' in data:
                updates.append('is_active = ?')
                params.append(1 if data['is_active'] else 0)
            if 'priority' in data:
                updates.append('priority = ?')
                params.append(data['priority'])
            if 'rule_description' in data:
                updates.append('rule_description = ?')
                params.append(data['rule_description'])
            
            if not updates:
                return jsonify({'success': False, 'error': '没有需要更新的字段'}), 400
            
            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(rule_code)
            
            query = f"UPDATE system_rules SET {', '.join(updates)} WHERE rule_code = ?"
            cursor.execute(query, params)
            conn.commit()
        
        return jsonify({'success': True, 'message': '规则更新成功', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/rule', methods=['POST'])
@require_admin
def create_rule():
    try:
        data = request.get_json() or {}
        
        rule_code = data.get('rule_code')
        rule_name = data.get('rule_name')
        rule_value = data.get('rule_value')
        
        if not rule_code or not rule_name:
            return jsonify({'success': False, 'error': '规则代码和名称不能为空'}), 400
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM system_rules WHERE rule_code = ?", (rule_code,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': '规则代码已存在'}), 400
            
            cursor.execute('''
                INSERT INTO system_rules
                (rule_code, rule_name, rule_description, rule_category, rule_value, rule_type,
                 priority, is_active, created_at, updated_at, effective_from, rule_group, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule_code,
                rule_name,
                data.get('rule_description', ''),
                data.get('rule_category', 'system'),
                rule_value,
                data.get('rule_type', 'string'),
                data.get('priority', 'medium'),
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                data.get('rule_group', 'default'),
                json.dumps(data.get('metadata', {}))
            ))
            conn.commit()
        
        return jsonify({'success': True, 'message': '规则创建成功', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/rule/<rule_code>', methods=['DELETE'])
@require_admin
def delete_rule(rule_code):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM system_rules WHERE rule_code = ?", (rule_code,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '规则不存在'}), 404
            
            cursor.execute("UPDATE system_rules SET is_active = 0, updated_at = ? WHERE rule_code = ?",
                          (datetime.now().isoformat(), rule_code))
            conn.commit()
        
        return jsonify({'success': True, 'message': '规则已禁用', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_auto_upgrade_api.route('/api/ai/upgrade/health', methods=['GET'])
@require_admin
def upgrade_health_check():
    engine = _get_brain_feeding_engine()
    
    health = {
        'status': 'healthy' if engine else 'warning',
        'engine': 'BrainFeedingEngine',
        'available': engine is not None,
        'timestamp': datetime.now().isoformat()
    }
    
    if engine:
        health.update({
            'feeding_count': engine.feeding_count,
            'network_learning_count': engine.network_learning_count,
            'learning_count': engine.learning_count,
            'upgrade_count': engine.upgrade_count,
            'coordination_count': engine.coordination_count
        })
    
    return jsonify({'success': True, 'data': health})
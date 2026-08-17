#!/usr/bin/env python3
""" AI引擎综合API 提供知识图谱、AI助教、游戏化引擎等AI功能的REST API接口 """

import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_engine_api = Bluelogger.info('ai_engine_api', __name__)


def _get_knowledge_graph_engine():
    try:
        from ai_engines.knowledge_graph_engine import KnowledgeGraphEngine
        return KnowledgeGraphEngine()
    except Exception as e:
        return None


def _get_tutor_engine():
    try:
        from ai_engines.ai_tutor_engine import AITutorEngine
        return AITutorEngine()
    except Exception as e:
        return None


def _get_gamification_engine():
    try:
        from ai_engines.gamification_engine import GamificationEngine
        return GamificationEngine()
    except Exception as e:
        return None


@ai_engine_api.route('/api/ai/knowledge/nodes', methods=['POST'])
@require_login
def add_knowledge_node():
    engine = _get_knowledge_graph_engine()
    if not engine:
        return jsonify({'success': False, 'error': '知识图谱引擎不可用'}), 503
    
    data = request.get_json() or {}
    
    result = engine.add_knowledge_node(
        subject=data.get('subject'),
        knowledge_point=data.get('knowledge_point'),
        grade=data.get('grade'),
        category=data.get('category'),
        difficulty=data.get('difficulty', 3),
        importance=data.get('importance', 0.5),
        description=data.get('description'),
        tags=data.get('tags'),
        prerequisites=data.get('prerequisites'),
        dependents=data.get('dependents')
    )
    
    return jsonify(result)


@ai_engine_api.route('/api/ai/knowledge/nodes', methods=['GET'])
@require_login
def get_knowledge_nodes():
    engine = _get_knowledge_graph_engine()
    if not engine:
        return jsonify({'success': False, 'error': '知识图谱引擎不可用'}), 503
    
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM knowledge_nodes'
            params = []
            
            if subject:
                query += ' WHERE subject = ?'
                params.append(subject)
                if grade:
                    query += ' AND grade = ?'
                    params.append(grade)
            elif grade:
                query += ' WHERE grade = ?'
                params.append(grade)
            
            query += ' ORDER BY subject, grade, knowledge_point'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            nodes = []
            for row in rows:
                nodes.append({
                    'node_id': row[0],
                    'subject': row[1],
                    'grade': row[2],
                    'knowledge_point': row[3],
                    'category': row[4],
                    'difficulty': row[5],
                    'importance': row[6],
                    'description': row[7],
                    'prerequisites': json.loads(row[8]) if row[8] else [],
                    'dependents': json.loads(row[9]) if row[9] else [],
                    'tags': json.loads(row[10]) if row[10] else [],
                    'created_at': row[11],
                    'updated_at': row[12]
                })
            
            return jsonify({
                'success': True,
                'data': nodes,
                'count': len(nodes),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/knowledge/nodes/<node_id>', methods=['GET'])
@require_login
def get_knowledge_node(node_id):
    engine = _get_knowledge_graph_engine()
    if not engine:
        return jsonify({'success': False, 'error': '知识图谱引擎不可用'}), 503
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ?', (node_id,))
            row = cursor.fetchone()
            
            if row:
                return jsonify({
                    'success': True,
                    'data': {
                        'node_id': row[0],
                        'subject': row[1],
                        'grade': row[2],
                        'knowledge_point': row[3],
                        'category': row[4],
                        'difficulty': row[5],
                        'importance': row[6],
                        'description': row[7],
                        'prerequisites': json.loads(row[8]) if row[8] else [],
                        'dependents': json.loads(row[9]) if row[9] else [],
                        'tags': json.loads(row[10]) if row[10] else [],
                        'created_at': row[11],
                        'updated_at': row[12]
                    }
                })
            else:
                return jsonify({'success': False, 'error': '知识点不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/knowledge/relations', methods=['POST'])
@require_login
def add_knowledge_relation():
    engine = _get_knowledge_graph_engine()
    if not engine:
        return jsonify({'success': False, 'error': '知识图谱引擎不可用'}), 503
    
    data = request.get_json() or {}
    
    result = engine.add_relation(
        source_node=data.get('source_node'),
        target_node=data.get('target_node'),
        relation_type=data.get('relation_type'),
        strength=data.get('strength', 0.5),
        direction=data.get('direction', 'undirected'),
        description=data.get('description')
    )
    
    return jsonify(result)


@ai_engine_api.route('/api/ai/knowledge/hierarchy', methods=['GET'])
@require_login
def get_knowledge_hierarchy():
    engine = _get_knowledge_graph_engine()
    if not engine:
        return jsonify({'success': False, 'error': '知识图谱引擎不可用'}), 503
    
    return jsonify({
        'success': True,
        'data': engine.subject_hierarchy,
        'timestamp': datetime.now().isoformat()
    })


@ai_engine_api.route('/api/ai/knowledge/search', methods=['GET'])
@require_login
def search_knowledge():
    engine = _get_knowledge_graph_engine()
    if not engine:
        return jsonify({'success': False, 'error': '知识图谱引擎不可用'}), 503
    
    query = request.args.get('q', '')
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(''' SELECT * FROM knowledge_nodes WHERE knowledge_point LIKE ? OR description LIKE ? OR tags LIKE ? ORDER BY importance DESC, difficulty ASC LIMIT 20 ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            rows = cursor.fetchall()
            nodes = []
            for row in rows:
                nodes.append({
                    'node_id': row[0],
                    'subject': row[1],
                    'grade': row[2],
                    'knowledge_point': row[3],
                    'difficulty': row[5],
                    'importance': row[6],
                    'description': row[7]
                })
            
            return jsonify({
                'success': True,
                'data': nodes,
                'count': len(nodes),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/tutor/start', methods=['POST'])
@require_login
def start_tutor_session():
    engine = _get_tutor_engine()
    if not engine:
        return jsonify({'success': False, 'error': 'AI助教引擎不可用'}), 503
    
    data = request.get_json() or {}
    
    result = engine.start_session(
        user_id=data.get('user_id'),
        subject=data.get('subject'),
        topic=data.get('topic')
    )
    
    return jsonify(result)


@ai_engine_api.route('/api/ai/tutor/message', methods=['POST'])
@require_login
def send_tutor_message():
    engine = _get_tutor_engine()
    if not engine:
        return jsonify({'success': False, 'error': 'AI助教引擎不可用'}), 503
    
    data = request.get_json() or {}
    
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    content = data.get('content')
    
    if not session_id or not user_id or not content:
        return jsonify({'success': False, 'error': 'session_id, user_id, content不能为空'}), 400
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(''' INSERT INTO tutor_messages (session_id, user_id, role, content, message_type) VALUES (?, ?, 'user', ?, 'text') ''', (session_id, user_id, content))
            
            cursor.execute('UPDATE tutor_sessions SET last_activity = CURRENT_TIMESTAMP, message_count = message_count + 1 WHERE session_id = ?', (session_id,))
            conn.commit()
        
        response = engine._generate_response(session_id, user_id, content, data.get('subject'))
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(''' INSERT INTO tutor_messages (session_id, user_id, role, content, message_type) VALUES (?, ?, 'assistant', ?, 'text') ''', (session_id, user_id, response))
            
            cursor.execute('UPDATE tutor_sessions SET last_activity = CURRENT_TIMESTAMP, message_count = message_count + 1 WHERE session_id = ?', (session_id,))
            conn.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/tutor/sessions/<user_id>', methods=['GET'])
@require_login
def get_tutor_sessions(user_id):
    engine = _get_tutor_engine()
    if not engine:
        return jsonify({'success': False, 'error': 'AI助教引擎不可用'}), 503
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(''' SELECT session_id, subject, topic, started_at, last_activity, message_count, status FROM tutor_sessions WHERE user_id = ? ORDER BY started_at DESC ''', (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'subject': row[1],
                    'topic': row[2],
                    'started_at': row[3],
                    'last_activity': row[4],
                    'message_count': row[5],
                    'status': row[6]
                })
            
            return jsonify({
                'success': True,
                'data': sessions,
                'count': len(sessions),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/tutor/session/<session_id>/messages', methods=['GET'])
@require_login
def get_tutor_messages(session_id):
    engine = _get_tutor_engine()
    if not engine:
        return jsonify({'success': False, 'error': 'AI助教引擎不可用'}), 503
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(''' SELECT role, content, message_type, created_at FROM tutor_messages WHERE session_id = ? ORDER BY id ASC ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row[0],
                    'content': row[1],
                    'message_type': row[2],
                    'created_at': row[3]
                })
            
            return jsonify({
                'success': True,
                'data': messages,
                'count': len(messages),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/tutor/explanation/<concept>', methods=['GET'])
@require_login
def get_concept_explanation(concept):
    engine = _get_tutor_engine()
    if not engine:
        return jsonify({'success': False, 'error': 'AI助教引擎不可用'}), 503
    
    if concept in engine._concept_explanations:
        return jsonify({
            'success': True,
            'data': engine._concept_explanations[concept],
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'success': False, 'error': f'未找到"{concept}"的解释'}), 404


@ai_engine_api.route('/api/ai/tutor/concepts', methods=['GET'])
@require_login
def get_all_concepts():
    engine = _get_tutor_engine()
    if not engine:
        return jsonify({'success': False, 'error': 'AI助教引擎不可用'}), 503
    
    return jsonify({
        'success': True,
        'data': list(engine._concept_explanations.keys()),
        'count': len(engine._concept_explanations),
        'timestamp': datetime.now().isoformat()
    })


@ai_engine_api.route('/api/ai/gamification/player/<user_id>', methods=['GET'])
@require_login
def get_player_info(user_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM game_players WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return jsonify({
                    'success': True,
                    'data': {
                        'player_id': row[0],
                        'user_id': row[1],
                        'nickname': row[2],
                        'avatar': row[3],
                        'level': row[4],
                        'exp_points': row[5],
                        'coins': row[6],
                        'gems': row[7],
                        'energy': row[8],
                        'max_energy': row[9],
                        'streak_days': row[10],
                        'last_active_date': row[11],
                        'total_quests_completed': row[12],
                        'total_challenges_won': row[13],
                        'title': row[14],
                        'bio': row[15],
                        'created_at': row[16],
                        'updated_at': row[17]
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({'success': False, 'error': '玩家不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/gamification/player/<user_id>/create', methods=['POST'])
@require_login
def create_player(user_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM game_players WHERE user_id = ?', (user_id,))
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'error': '玩家已存在'}), 400
            
            player_id = f"player_{user_id}_{int(datetime.now().timestamp())}"
            
            cursor.execute(''' INSERT INTO game_players (player_id, user_id, nickname, avatar) VALUES (?, ?, ?, ?) ''', (player_id, user_id, data.get('nickname', '玩家'), data.get('avatar', '👤')))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'player_id': player_id,
                'message': '玩家创建成功',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/gamification/player/<user_id>/exp', methods=['POST'])
@require_login
def add_player_exp(user_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    exp_amount = data.get('exp', 0)
    
    if exp_amount <= 0:
        return jsonify({'success': False, 'error': '经验值必须大于0'}), 400
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT level, exp_points FROM game_players WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'success': False, 'error': '玩家不存在'}), 404
            
            current_level = row[0]
            current_exp = row[1]
            new_exp = current_exp + exp_amount
            
            from ai_engines.gamification_engine import LEVEL_THRESHOLDS
            new_level = current_level
            for i, threshold in enumerate(LEVEL_THRESHOLDS):
                if new_exp >= threshold:
                    new_level = i + 1
            
            level_up = new_level > current_level
            
            cursor.execute(''' UPDATE game_players SET exp_points = ?, level = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? ''', (new_exp, new_level, user_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'previous_level': current_level,
                'new_level': new_level,
                'previous_exp': current_exp,
                'new_exp': new_exp,
                'level_up': level_up,
                'message': '升级成功！' if level_up else '经验值已添加',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/gamification/quests', methods=['GET'])
@require_login
def get_quests():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    quest_type = request.args.get('type')
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            if quest_type:
                cursor.execute(
                'SELECT * FROM game_quests WHERE quest_type = ? AND status = "active" ORDER BY difficulty', (quest_type,
                ))
            else:
                cursor.execute('SELECT * FROM game_quests WHERE status = "active" ORDER BY quest_type, difficulty')
            
            rows = cursor.fetchall()
            quests = []
            for row in rows:
                quests.append({
                    'quest_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'quest_type': row[3],
                    'difficulty': row[4],
                    'category': row[5],
                    'subject': row[6],
                    'target_value': row[7],
                    'reward_exp': row[8],
                    'reward_coins': row[9],
                    'reward_badge': row[10],
                    'prerequisites': json.loads(row[11]) if row[11] else [],
                    'time_limit': row[12],
                    'status': row[13],
                    'created_at': row[14]
                })
            
            return jsonify({
                'success': True,
                'data': quests,
                'count': len(quests),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/gamification/leaderboard', methods=['GET'])
@require_login
def get_leaderboard():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(''' SELECT user_id, nickname, level, exp_points, coins, streak_days, total_quests_completed FROM game_players ORDER BY exp_points DESC LIMIT 50 ''')
            
            rows = cursor.fetchall()
            leaderboard = []
            for i, row in enumerate(rows, 1):
                leaderboard.append({
                    'rank': i,
                    'user_id': row[0],
                    'nickname': row[1],
                    'level': row[2],
                    'exp_points': row[3],
                    'coins': row[4],
                    'streak_days': row[5],
                    'total_quests_completed': row[6]
                })
            
            return jsonify({
                'success': True,
                'data': leaderboard,
                'count': len(leaderboard),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/gamification/items', methods=['GET'])
@require_login
def get_items():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM game_items ORDER BY rarity, price_coins')
            
            rows = cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    'item_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'item_type': row[3],
                    'rarity': row[4],
                    'icon': row[5],
                    'price_coins': row[6],
                    'price_gems': row[7],
                    'effects': json.loads(row[8]) if row[8] else {},
                    'stackable': bool(row[9]),
                    'max_stack': row[10],
                    'created_at': row[11]
                })
            
            return jsonify({
                'success': True,
                'data': items,
                'count': len(items),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_engine_api.route('/api/ai/engine/status', methods=['GET'])
@require_admin
def get_engine_status():
    kg_engine = _get_knowledge_graph_engine()
    tutor_engine = _get_tutor_engine()
    gamification_engine = _get_gamification_engine()
    
    status = {
        'knowledge_graph': {
            'available': kg_engine is not None,
            'initialized': kg_engine._initialized if kg_engine else False
        },
        'ai_tutor': {
            'available': tutor_engine is not None,
            'initialized': tutor_engine._initialized if tutor_engine else False
        },
        'gamification': {
            'available': gamification_engine is not None,
            'initialized': gamification_engine._initialized if gamification_engine else False
        }
    }
    
    return jsonify({
        'success': True,
        'data': status,
        'timestamp': datetime.now().isoformat()
    })
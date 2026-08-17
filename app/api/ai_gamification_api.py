#!/usr/bin/env python3
"""
游戏化引擎API
提供学习游戏化功能：玩家档案、任务系统、挑战、排行榜、奖励、成就、虚拟物品等
"""

import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_gamification_api = Bluelogger.info('ai_gamification_api', __name__)


def _get_gamification_engine():
    try:
        from ai_engines.gamification_engine import GamificationEngine
        return GamificationEngine()
    except Exception as e:
        return None


@ai_gamification_api.route('/api/ai/gamification/player/<user_id>', methods=['GET'])
@require_login
def get_player_profile(user_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        profile = engine.get_player_profile(user_id)
        if profile:
            return jsonify({'success': True, 'data': profile, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': '玩家档案不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/player', methods=['POST'])
@require_login
def create_player_profile():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    user_id = data.get('user_id')
    nickname = data.get('nickname', '')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    try:
        result = engine.create_player(user_id, nickname)
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/player/<user_id>/level', methods=['GET'])
@require_login
def get_player_level(user_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        level_info = engine.get_player_level(user_id)
        return jsonify({'success': True, 'data': level_info, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/player/<user_id>/exp', methods=['POST'])
@require_login
def add_player_exp(user_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    exp_amount = data.get('exp', 0)
    reason = data.get('reason', '')
    
    if exp_amount <= 0:
        return jsonify({'success': False, 'error': '经验值必须大于0'}), 400
    
    try:
        result = engine.add_exp(user_id, exp_amount, reason)
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/tasks', methods=['GET'])
@require_login
def get_tasks():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    difficulty = request.args.get('difficulty')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    
    try:
        tasks = engine.get_tasks(difficulty, status, limit)
        return jsonify({'success': True, 'data': tasks, 'count': len(tasks), 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/task/<task_id>', methods=['GET'])
@require_login
def get_task_detail(task_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        task = engine.get_task(task_id)
        if task:
            return jsonify({'success': True, 'data': task, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/task/<task_id>/complete', methods=['POST'])
@require_login
def complete_task(task_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    try:
        result = engine.complete_task(user_id, task_id)
        if result.get('success'):
            return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': result.get('error', '任务完成失败')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/challenges', methods=['GET'])
@require_login
def get_challenges():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    category = request.args.get('category')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    
    try:
        challenges = engine.get_challenges(category, status, limit)
        return jsonify({'success': True, 'data': challenges, 'count': len(challenges),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/challenge/<challenge_id>/start', methods=['POST'])
@require_login
def start_challenge(challenge_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    try:
        result = engine.start_challenge(user_id, challenge_id)
        if result.get('success'):
            return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': result.get('error', '挑战开始失败')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/challenge/<challenge_id>/complete', methods=['POST'])
@require_login
def complete_challenge(challenge_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    try:
        result = engine.complete_challenge(user_id, challenge_id)
        if result.get('success'):
            return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': result.get('error', '挑战完成失败')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/leaderboard', methods=['GET'])
@require_login
def get_leaderboard():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    limit = int(request.args.get('limit', 50))
    period = request.args.get('period', 'all')
    
    try:
        leaderboard = engine.get_leaderboard(limit, period)
        return jsonify({'success': True, 'data': leaderboard, 'count': len(leaderboard),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/achievements', methods=['GET'])
@require_login
def get_achievements():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    user_id = request.args.get('user_id')
    unlocked_only = request.args.get('unlocked_only', 'false').lower() == 'true'
    
    try:
        achievements = engine.get_achievements(user_id, unlocked_only)
        return jsonify({'success': True, 'data': achievements, 'count': len(achievements),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/rewards', methods=['GET'])
@require_login
def get_rewards():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    user_id = request.args.get('user_id')
    
    try:
        rewards = engine.get_rewards(user_id)
        return jsonify({'success': True, 'data': rewards, 'count': len(rewards),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/reward/<reward_id>/claim', methods=['POST'])
@require_login
def claim_reward(reward_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    try:
        result = engine.claim_reward(user_id, reward_id)
        if result.get('success'):
            return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': result.get('error', '领取奖励失败')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/virtual-items', methods=['GET'])
@require_login
def get_virtual_items():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    user_id = request.args.get('user_id')
    item_type = request.args.get('type')
    
    try:
        items = engine.get_virtual_items(user_id, item_type)
        return jsonify({'success': True, 'data': items, 'count': len(items), 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/virtual-item/<item_id>/purchase', methods=['POST'])
@require_login
def purchase_virtual_item(item_id):
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    try:
        result = engine.purchase_item(user_id, item_id)
        if result.get('success'):
            return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
        return jsonify({'success': False, 'error': result.get('error', '购买失败')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/stats', methods=['GET'])
@require_admin
def get_gamification_stats():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        stats = engine.get_stats()
        return jsonify({'success': True, 'data': stats, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gamification_api.route('/api/ai/gamification/health', methods=['GET'])
@require_admin
def gamification_health_check():
    engine = _get_gamification_engine()
    if not engine:
        return jsonify({'success': False, 'error': '游戏化引擎不可用'}), 503
    
    try:
        health = {
            'status': 'healthy',
            'engine': 'GamificationEngine',
            'timestamp': datetime.now().isoformat()
        }
        return jsonify({'success': True, 'data': health})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
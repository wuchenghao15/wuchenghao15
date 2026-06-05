#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锦标赛系统API路由
"""

from flask import Blueprint, request, jsonify, session
import json
from app.models.exam_tournament import Tournament, TournamentParticipant, TournamentRecord, init_tournament_system
from app.utils.logging import logger
from app.middlewares.access_control import require_admin

tournament_bp = Blueprint('tournament', __name__, url_prefix='/api/tournament')


@tournament_bp.route('/init', methods=['POST'])
def init_system():
    """初始化锦标赛系统"""
    try:
        result = init_tournament_system()
        return jsonify({
            'success': result,
            'message': '锦标赛系统初始化成功'
        })
    except Exception as e:
        logger.error(f"初始化锦标赛系统失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments', methods=['GET'])
def get_tournaments():
    """获取所有锦标赛列表"""
    try:
        status = request.args.get('status')
        tournaments = Tournament.get_all(status=status)
        return jsonify({
            'success': True,
            'data': tournaments
        })
    except Exception as e:
        logger.error(f"获取锦标赛列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    """获取单个锦标赛详情"""
    try:
        tournament = Tournament.get_by_id(tournament_id)
        if not tournament:
            return jsonify({
                'success': False,
                'message': '锦标赛不存在'
            }), 404
        
        participant_count = TournamentParticipant.get_participant_count(tournament_id)
        data = dict(tournament) if isinstance(tournament, tuple) else tournament
        if isinstance(data, dict):
            data['participant_count'] = participant_count
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"获取锦标赛详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments', methods=['POST'])
@require_admin
def create_tournament():
    """创建新锦标赛"""
    try:
        data = request.json
        
        tournament = Tournament(
            name=data.get('name'),
            description=data.get('description'),
            tournament_type=data.get('tournament_type', 'challenge'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            max_participants=data.get('max_participants', 100),
            prize_type=data.get('prize_type', 'points'),
            status=data.get('status', 'upcoming'),
            created_by=session.get('user_id')
        )
        
        success = tournament.save()
        return jsonify({
            'success': success,
            'data': tournament.to_dict() if success else None,
            'message': '创建成功' if success else '创建失败'
        })
    except Exception as e:
        logger.error(f"创建锦标赛失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>', methods=['PUT'])
@require_admin
def update_tournament(tournament_id):
    """更新锦标赛"""
    try:
        data = request.json
        tournament = Tournament.get_by_id(tournament_id)
        
        if not tournament:
            return jsonify({
                'success': False,
                'message': '锦标赛不存在'
            }), 404
        
        t = Tournament(
            tournament_id=tournament['id'] if isinstance(tournament, dict) else tournament[0],
            name=data.get('name', tournament.get('name') if isinstance(tournament, dict) else tournament[1]),
            description=data.get('description', tournament.get('description') if isinstance(tournament, dict) else tournament[2]),
            tournament_type=data.get('tournament_type', tournament.get('tournament_type') if isinstance(tournament, dict) else tournament[3]),
            start_date=data.get('start_date', tournament.get('start_date') if isinstance(tournament, dict) else tournament[4]),
            end_date=data.get('end_date', tournament.get('end_date') if isinstance(tournament, dict) else tournament[5]),
            max_participants=data.get('max_participants', tournament.get('max_participants') if isinstance(tournament, dict) else tournament[6]),
            prize_type=data.get('prize_type', tournament.get('prize_type') if isinstance(tournament, dict) else tournament[7]),
            status=data.get('status', tournament.get('status') if isinstance(tournament, dict) else tournament[8])
        )
        
        success = t.save()
        return jsonify({
            'success': success,
            'message': '更新成功' if success else '更新失败'
        })
    except Exception as e:
        logger.error(f"更新锦标赛失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
@require_admin
def delete_tournament(tournament_id):
    """删除锦标赛"""
    try:
        from app.utils.db import db_manager
        db_manager.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    except Exception as e:
        logger.error(f"删除锦标赛失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>/register', methods=['POST'])
def register_tournament(tournament_id):
    """学生报名参加锦标赛"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        
        tournament = Tournament.get_by_id(tournament_id)
        if not tournament:
            return jsonify({
                'success': False,
                'message': '锦标赛不存在'
            }), 404
        
        current_count = TournamentParticipant.get_participant_count(tournament_id)
        max_participants = tournament['max_participants'] if isinstance(tournament, dict) else tournament[6]
        
        if current_count >= max_participants:
            return jsonify({
                'success': False,
                'message': '报名人数已满'
            }), 400
        
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            user_id=user_id,
            status='registered'
        )
        
        success = participant.save()
        return jsonify({
            'success': success,
            'message': '报名成功' if success else '报名失败'
        })
    except Exception as e:
        logger.error(f"报名锦标赛失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'报名失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>/participants', methods=['GET'])
@require_admin
def get_participants(tournament_id):
    """获取锦标赛参赛者列表"""
    try:
        participants = TournamentParticipant.get_participants(tournament_id)
        return jsonify({
            'success': True,
            'data': participants
        })
    except Exception as e:
        logger.error(f"获取参赛者列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>/complete', methods=['POST'])
def complete_tournament(tournament_id):
    """完成锦标赛并记录成绩"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        
        data = request.json
        score = data.get('score')
        
        if score is None:
            return jsonify({
                'success': False,
                'message': '请提供成绩'
            }), 400
        
        leaderboard = TournamentRecord.get_leaderboard(tournament_id)
        rank = len(leaderboard) + 1
        
        record = TournamentRecord(
            tournament_id=tournament_id,
            user_id=user_id,
            score=score,
            rank=rank
        )
        
        success = record.save()
        
        if success:
            participant = TournamentParticipant()
            participant.participant_id = TournamentParticipant.get_participants(tournament_id)
            participant.status = 'completed'
            participant.save()
        
        return jsonify({
            'success': success,
            'data': {'rank': rank} if success else None,
            'message': '成绩记录成功' if success else '记录失败'
        })
    except Exception as e:
        logger.error(f"完成锦标赛失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'记录失败: {str(e)}'
        }), 500


@tournament_bp.route('/tournaments/<int:tournament_id>/leaderboard', methods=['GET'])
def get_leaderboard(tournament_id):
    """获取锦标赛排行榜"""
    try:
        limit = int(request.args.get('limit', 10))
        leaderboard = TournamentRecord.get_leaderboard(tournament_id, limit)
        return jsonify({
            'success': True,
            'data': leaderboard
        })
    except Exception as e:
        logger.error(f"获取排行榜失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tournament_bp.route('/random', methods=['GET'])
def get_random_tournament():
    """获取随机推荐赛事"""
    try:
        import random
        from app.utils.db import db_manager
        
        # 获取所有即将开始和进行中的锦标赛
        tournaments = db_manager.fetch_all('''
            SELECT * FROM tournaments 
            WHERE status IN ('upcoming', 'active')
            ORDER BY RANDOM()
            LIMIT 1
        ''')
        
        if not tournaments or len(tournaments) == 0:
            return jsonify({
                'success': False,
                'message': '暂无可推荐的赛事'
            })
        
        tournament = tournaments[0]
        
        # 获取参赛者数量
        participant_count = TournamentParticipant.get_participant_count(
            tournament['id'] if isinstance(tournament, dict) else tournament[0]
        )
        
        if isinstance(tournament, dict):
            tournament['participant_count'] = participant_count
        else:
            tournament = {
                'id': tournament[0],
                'name': tournament[1],
                'description': tournament[2],
                'tournament_type': tournament[3],
                'start_date': tournament[4],
                'end_date': tournament[5],
                'max_participants': tournament[6],
                'prize_type': tournament[7],
                'status': tournament[8],
                'created_at': tournament[9],
                'participant_count': participant_count
            }
        
        return jsonify({
            'success': True,
            'data': tournament
        })
    except Exception as e:
        logger.error(f"获取随机赛事失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tournament_bp.route('/upcoming', methods=['GET'])
def get_upcoming_tournaments():
    """获取即将开始的锦标赛（用于首页展示）"""
    try:
        from app.utils.db import db_manager
        
        # 获取即将开始的锦标赛，最多3个
        tournaments = db_manager.fetch_all('''
            SELECT * FROM tournaments 
            WHERE status = 'upcoming'
            ORDER BY created_at DESC
            LIMIT 3
        ''')
        
        result = []
        for t in tournaments:
            if isinstance(t, dict):
                tournament = t
            else:
                tournament = {
                    'id': t[0],
                    'name': t[1],
                    'description': t[2],
                    'tournament_type': t[3],
                    'start_date': t[4],
                    'end_date': t[5],
                    'max_participants': t[6],
                    'prize_type': t[7],
                    'status': t[8],
                    'created_at': t[9]
                }
            
            # 获取参赛者数量
            tournament['participant_count'] = TournamentParticipant.get_participant_count(tournament['id'])
            result.append(tournament)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"获取即将开始的锦标赛失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tournament_bp.route('/my-participations', methods=['GET'])
def get_my_participations():
    """获取当前用户的参赛记录"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        
        from app.utils.db import db_manager
        participations = db_manager.fetch_all('''
            SELECT tp.*, t.name as tournament_name, t.description, t.tournament_type
            FROM tournament_participants tp
            LEFT JOIN tournaments t ON tp.tournament_id = t.id
            WHERE tp.user_id = ?
            ORDER BY tp.registered_at DESC
        ''', (user_id,))
        
        return jsonify({
            'success': True,
            'data': participations
        })
    except Exception as e:
        logger.error(f"获取参赛记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500

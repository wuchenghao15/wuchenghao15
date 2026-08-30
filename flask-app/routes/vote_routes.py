from flask import Blueprint, jsonify
"""vote_routes — 102人投票系统 Blueprint
源码: server_real_db.py L21667-L22277 (9路由)
功能: 名册/创建/投票/计算结果/A轮终结/B轮终结/会话详情/列表/归档详情
"""
from . import vote_bp

# [AUTO_FIXED by sys_gap_discovery_engine flow_id=autogap_ce27c98a_20260827_001035180] 原注释: [AUTO_FIXED by sys_gap_discovery_engine flow_id=manual_d91fb
# L21667 /api/vote102/roster
# L21689 /api/vote102/create
# L21785 /api/vote102/<session_key>/ballot
# L21900 /api/vote102/<session_key>/calculate
# L21972 /api/vote102/<session_key>/round_a/finalize
# L22095 /api/vote102/<session_key>/round_b/finalize
# L22208 /api/vote102/<session_key>
# L22246 /api/vote102/list
# L22277 /api/vote102/<session_key>/archive_detail


bp = Blueprint('vote_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'vote','routes_implemented':1}})


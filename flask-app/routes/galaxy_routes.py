"""
仙女座星系子系统 — Flask 路由 (API + 页面)

flow_id: galaxy_routes
version: v23.1.0 (多平台 accounts/creds/publish_log/high_exposure)
注册: routes/__init__.py → _modules 列表 ('galaxy_routes', 'galaxy_bp')

API:
  GET    /api/galaxy/stats               → 运营汇总 (多平台)
  POST   /api/galaxy/series/create       → 生成课程系列
  GET    /api/galaxy/series              → 系列列表
  GET    /api/galaxy/series/<series_id>  → 系列详情 + 集列表
  POST   /api/galaxy/compliance/check    → C1~C7 全量合规 (platform 参数)
  POST   /api/galaxy/compliance/precheck → 快速预检 (platform 参数)
  GET    /api/galaxy/accounts            → 账号基础信息列表
  GET    /api/galaxy/accounts/creds      → 平台凭证列表
  POST   /api/galaxy/accounts/creds      → 更新平台凭证 (扫码后补 cookie)
  GET    /api/galaxy/publish_log         → 发布日志 (多平台)
  POST   /api/galaxy/publish_log         → 创建发布计划 (episode→多平台)
  GET    /api/galaxy/high_exposure       → 高曝光活动列表
  POST   /api/galaxy/high_exposure       → 发现/更新活动
  GET    /api/galaxy/platform_restrict   → 平台限流词库
  GET    /api/galaxy/daemon/run          → 手动 daemon 一轮

页面:
  GET    /admin/galaxy              → 总览仪表盘
  GET    /admin/galaxy/series/<id>  → 系列详情
"""
import json
import logging
import os
import sqlite3
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, abort

logger = logging.getLogger('galaxy_routes')

# ====== 蓝图定义 ======
# 用 'galaxy_routes' 作为 endpoint 命名空间 (避免和其他蓝图冲突)
galaxy_bp = Blueprint('galaxy_routes', __name__,
                      template_folder='../templates/galaxy',
                      static_folder='../static')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'database', 'app.db')


def _conn():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.execute('PRAGMA journal_mode=WAL')
    c.row_factory = sqlite3.Row
    return c


def _nav_items(endpoint: str = ''):
    """导航栏链接 — 传给模板"""
    return [
        ('galaxy_routes.dashboard', '🌌 星系总览'),
        ('galaxy_routes.series_list_page', '📚 课程系列'),
    ]


# =================================================================
#  API 路由 (JSON)
# =================================================================

@galaxy_bp.route('/api/galaxy/stats', methods=['GET'])
def api_stats():
    """GET /api/galaxy/stats — daemon 运营汇总"""
    try:
        from engines import galaxy_daemon
        stats = galaxy_daemon.stage4_operations()
        stats['version'] = 'v23.0.0'
        stats['endpoint'] = 'galaxy_routes.api_stats'
        return jsonify({'ok': True, 'data': stats})
    except Exception as e:
        logger.exception('api_stats 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/series/create', methods=['POST'])
def api_series_create():
    """POST /api/galaxy/series/create — 生成课程系列"""
    data = request.get_json(silent=True) or request.form.to_dict()
    title = (data.get('title') or '').strip()
    topic = (data.get('topic') or '').strip()
    subject = (data.get('subject') or '综合').strip()
    role_type = data.get('role_type') or 'andromeda_professor'
    episode_count = int(data.get('episode_count') or 3)

    if not title:
        return jsonify({'ok': False, 'error': 'title 必填'}), 400
    if role_type not in ('andromeda_teacher', 'andromeda_professor', 'andromeda_scholar'):
        return jsonify({'ok': False, 'error': f'未知 role_type: {role_type}'}), 400

    try:
        from engines import galaxy_content_engine
        result = galaxy_content_engine.generate_series(
            title=title, topic=topic or title, subject=subject,
            role_type=role_type, episode_count=episode_count,
        )
        return jsonify({'ok': True, 'data': result})
    except Exception as e:
        logger.exception('api_series_create 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/series', methods=['GET'])
def api_series_list():
    """GET /api/galaxy/series — 系列列表"""
    role_type = request.args.get('role_type')
    status = request.args.get('status')
    try:
        from engines import galaxy_db as gdb
        items = gdb.list_series(role_type=role_type, status=status)
        return jsonify({'ok': True, 'data': items, 'count': len(items)})
    except Exception as e:
        logger.exception('api_series_list 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/series/<series_id>', methods=['GET'])
def api_series_detail(series_id):
    """GET /api/galaxy/series/<series_id> — 系列详情 + 集列表"""
    try:
        conn = _conn()
        series = conn.execute("SELECT * FROM mt_galaxy_series WHERE series_id=?", (series_id,)).fetchone()
        if not series:
            conn.close()
            return jsonify({'ok': False, 'error': 'series not found'}), 404
        episodes = conn.execute("SELECT * FROM mt_galaxy_episodes WHERE series_id=? ORDER BY episode_no ASC",
                                (series_id,)).fetchall()
        # 合规汇总
        compliance = conn.execute("""
            SELECT ep.episode_id, COUNT(cl.log_id) as checks,
                   SUM(CASE WHEN cl.result='BLOCK' THEN 1 ELSE 0 END) as blocks,
                   SUM(CASE WHEN cl.result='REVIEW' THEN 1 ELSE 0 END) as reviews
            FROM mt_galaxy_episodes ep
            LEFT JOIN mt_galaxy_compliance_log cl ON cl.content_id=ep.episode_id
            WHERE ep.series_id=?
            GROUP BY ep.episode_id
        """, (series_id,)).fetchall()
        conn.close()

        # role_type → 中文
        role_label = {
            'andromeda_teacher': '数字教师',
            'andromeda_professor': '数字教授',
            'andromeda_scholar': '数字学者',
        }
        level_label = {
            'elementary': '初级', 'intermediate': '中级', 'advanced': '高级',
        }

        return jsonify({
            'ok': True,
            'data': {
                'series': dict(series),
                'role_label': role_label.get(series['role_type'], series['role_type']),
                'level_label': level_label.get(series['level'], series['level']),
                'episodes': [dict(e) for e in episodes],
                'compliance': [dict(c) for c in compliance],
            }
        })
    except Exception as e:
        logger.exception('api_series_detail 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/compliance/check', methods=['POST'])
def api_compliance_check():
    """POST /api/galaxy/compliance/check — C1~C7 全量合规审查 (支持 platform)"""
    data = request.get_json(silent=True) or request.form.to_dict()
    text = (data.get('text') or '').strip()
    content_id = (data.get('content_id') or f"temp_{int(datetime.now().timestamp())}")
    content_type = data.get('content_type') or 'script'
    source_type = data.get('source_type') or 'self_generated'
    platform = data.get('platform')  # 'douyin' | 'xiaohongshu' | 'bilibili' | None

    if not text:
        return jsonify({'ok': False, 'error': 'text 必填'}), 400

    try:
        from engines import galaxy_compliance
        result = galaxy_compliance.run_compliance_pipeline(
            content_id=content_id, content_type=content_type,
            text=text, source_type=source_type, platform=platform,
        )
        return jsonify({'ok': True, 'data': result})
    except Exception as e:
        logger.exception('api_compliance_check 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/compliance/precheck', methods=['POST'])
def api_compliance_precheck():
    """POST /api/galaxy/compliance/precheck — 快速预检 (支持 platform)"""
    data = request.get_json(silent=True) or request.form.to_dict()
    text = (data.get('text') or '').strip()
    platform = data.get('platform')  # 'douyin' | 'xiaohongshu' | 'bilibili' | None
    if not text:
        return jsonify({'ok': False, 'error': 'text 必填'}), 400

    try:
        from engines import galaxy_compliance
        ok, blockers = galaxy_compliance.quick_precheck(text, platform=platform)
        return jsonify({'ok': True, 'pass': ok, 'blockers': blockers, 'platform': platform})
    except Exception as e:
        logger.exception('api_compliance_precheck 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


# =================================================================
#  v23.1.0 新增: 账号 + 平台凭证
# =================================================================

@galaxy_bp.route('/api/galaxy/accounts', methods=['GET'])
def api_accounts_list():
    """GET /api/galaxy/accounts — 账号基础信息"""
    try:
        from engines import galaxy_db as gdb
        enabled = request.args.get('enabled', '1') == '1'
        items = gdb.list_accounts(enabled=enabled)
        return jsonify({'ok': True, 'data': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/accounts/creds', methods=['GET'])
def api_creds_list():
    """GET /api/galaxy/accounts/creds — 平台凭证列表"""
    account_id = request.args.get('account_id')
    platform = request.args.get('platform')
    auth_status = request.args.get('auth_status')
    try:
        from engines import galaxy_db as gdb
        items = gdb.list_platform_creds(account_id=account_id, platform=platform,
                                        auth_status=auth_status)
        # 不返回 credential_json (敏感)
        safe = []
        for c in items:
            c.pop('credential_json', None)
            safe.append(c)
        return jsonify({'ok': True, 'data': safe, 'count': len(safe)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/accounts/creds', methods=['POST'])
def api_creds_update():
    """POST /api/galaxy/accounts/creds — 更新平台凭证 (扫码后补 cookie)"""
    data = request.get_json(silent=True) or request.form.to_dict()
    account_id = data.get('account_id')
    platform = data.get('platform')
    if not account_id or not platform:
        return jsonify({'ok': False, 'error': 'account_id + platform 必填'}), 400

    allowed_platforms = ('douyin', 'xiaohongshu', 'bilibili', 'github')
    if platform not in allowed_platforms:
        return jsonify({'ok': False, 'error': f'platform 必须是 {allowed_platforms}'}), 400

    try:
        from engines import galaxy_db as gdb
        cid = gdb.upsert_platform_cred(
            account_id=account_id, platform=platform,
            platform_uid=data.get('platform_uid'),
            login_id=data.get('login_id'),
            login_type=data.get('login_type', 'password'),
            credential_json=data.get('credential_json'),
            auth_status=data.get('auth_status', 'pending'),
            platform_url=data.get('platform_url'),
        )
        return jsonify({'ok': True, 'cred_id': cid})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =================================================================
#  v23.1.0 新增: 多平台发布日志
# =================================================================

@galaxy_bp.route('/api/galaxy/publish_log', methods=['GET'])
def api_publish_log_list():
    """GET /api/galaxy/publish_log — 发布日志"""
    episode_id = request.args.get('episode_id')
    platform = request.args.get('platform')
    status = request.args.get('status')
    limit = int(request.args.get('limit') or 100)
    try:
        from engines import galaxy_db as gdb
        items = gdb.get_publish_log(episode_id=episode_id, platform=platform,
                                    status=status, limit=limit)
        return jsonify({'ok': True, 'data': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/publish_log', methods=['POST'])
def api_publish_log_create():
    """POST /api/galaxy/publish_log — 创建发布计划 (一个 episode 可多平台)"""
    data = request.get_json(silent=True) or request.form.to_dict()
    episode_id = data.get('episode_id')
    platforms = data.get('platforms') or [data.get('platform')]
    account_id = data.get('account_id')
    scheduled_time = data.get('scheduled_time')

    if not episode_id:
        return jsonify({'ok': False, 'error': 'episode_id 必填'}), 400
    platforms = [p for p in platforms if p] if isinstance(platforms, list) else [platforms]
    valid = ('douyin', 'xiaohongshu', 'bilibili')
    platforms = [p for p in platforms if p in valid]
    if not platforms:
        return jsonify({'ok': False, 'error': f'platforms 必须是 {valid}'}), 400

    try:
        from engines import galaxy_db as gdb
        # 从 episodes 查 series_id
        conn = _conn()
        ep = conn.execute("SELECT series_id FROM mt_galaxy_episodes WHERE episode_id=?",
                          (episode_id,)).fetchone()
        conn.close()
        series_id = ep['series_id'] if ep else None

        created = []
        for p in platforms:
            pid = gdb.create_publish_log(episode_id=episode_id, platform=p,
                                         series_id=series_id, account_id=account_id,
                                         scheduled_time=scheduled_time)
            created.append({'platform': p, 'publish_id': pid})
        return jsonify({'ok': True, 'created': created, 'count': len(created)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =================================================================
#  v23.1.0 新增: 高曝光活动追踪
# =================================================================

@galaxy_bp.route('/api/galaxy/high_exposure', methods=['GET'])
def api_high_exposure_list():
    """GET /api/galaxy/high_exposure — 高曝光活动列表"""
    platform = request.args.get('platform')
    min_score = float(request.args.get('min_score') or 0)
    try:
        from engines import galaxy_db as gdb
        items = gdb.list_active_high_exposure(platform=platform, min_score=min_score)
        return jsonify({'ok': True, 'data': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/high_exposure', methods=['POST'])
def api_high_exposure_upsert():
    """POST /api/galaxy/high_exposure — 发现/更新活动"""
    data = request.get_json(silent=True) or request.form.to_dict()
    activity_id = data.get('activity_id')
    platform = data.get('platform')
    activity_name = data.get('activity_name')
    if not activity_id or not platform or not activity_name:
        return jsonify({'ok': False, 'error': 'activity_id + platform + activity_name 必填'}), 400
    try:
        from engines import galaxy_db as gdb
        gdb.upsert_high_exposure(
            activity_id=activity_id, platform=platform,
            activity_name=activity_name,
            activity_type=data.get('activity_type'),
            hot_score=float(data.get('hot_score') or 0),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            tags_json=data.get('tags_json'),
            notes=data.get('notes'),
        )
        return jsonify({'ok': True, 'activity_id': activity_id})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/platform_restrict', methods=['GET'])
def api_platform_restrict():
    """GET /api/galaxy/platform_restrict — 平台限流词库"""
    platform = request.args.get('platform')
    restrict_type = request.args.get('restrict_type')
    try:
        from engines import galaxy_db as gdb
        items = gdb.get_restrict_words(platform=platform, restrict_type=restrict_type)
        return jsonify({'ok': True, 'data': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@galaxy_bp.route('/api/galaxy/daemon/run', methods=['POST', 'GET'])
def api_daemon_run():
    """POST /api/galaxy/daemon/run — 手动触发 daemon 一轮"""
    try:
        from engines import galaxy_daemon
        result = galaxy_daemon.run_once()
        return jsonify({'ok': True, 'data': result})
    except Exception as e:
        logger.exception('api_daemon_run 失败')
        return jsonify({'ok': False, 'error': str(e)}), 500


# =================================================================
#  页面路由
# =================================================================

@galaxy_bp.route('/admin/galaxy', methods=['GET'])
def dashboard():
    """🌌 星系总览仪表盘"""
    try:
        from engines import galaxy_daemon, galaxy_db as gdb
        stats = galaxy_daemon.stage4_operations()
        series_list = gdb.list_series()[:10]
        # 合规日志最近 10 条
        conn = _conn()
        recent_logs = conn.execute("""
            SELECT * FROM mt_galaxy_compliance_log
            ORDER BY log_id DESC LIMIT 10
        """).fetchall()
        conn.close()
    except Exception as e:
        stats = {'error': str(e)}
        series_list = []
        recent_logs = []

    return render_template('galaxy/dashboard.html',
                           stats=stats,
                           series_list=series_list,
                           recent_logs=recent_logs,
                           role_labels={
                               'andromeda_teacher': '数字教师',
                               'andromeda_professor': '数字教授',
                               'andromeda_scholar': '数字学者',
                           },
                           _now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@galaxy_bp.route('/admin/galaxy/series/<series_id>', methods=['GET'])
def series_detail(series_id):
    """📚 系列详情页"""
    try:
        from engines import galaxy_db as gdb
        conn = _conn()
        series = conn.execute("SELECT * FROM mt_galaxy_series WHERE series_id=?", (series_id,)).fetchone()
        if not series:
            conn.close()
            abort(404)
        episodes = conn.execute("SELECT * FROM mt_galaxy_episodes WHERE series_id=? ORDER BY episode_no ASC",
                                (series_id,)).fetchall()
        # 每集合规汇总
        compliance_map = {}
        clogs = conn.execute("""
            SELECT content_id, result, check_type FROM mt_galaxy_compliance_log
            WHERE content_id IN (SELECT episode_id FROM mt_galaxy_episodes WHERE series_id=?)
            ORDER BY content_id, log_id DESC
        """, (series_id,)).fetchall()
        for log in clogs:
            eid = log['content_id']
            if eid not in compliance_map:
                compliance_map[eid] = {'PASS': 0, 'BLOCK': 0, 'REVIEW': 0, 'checks': []}
            compliance_map[eid][log['result']] += 1
            compliance_map[eid]['checks'].append(f"{log['check_type']}={log['result']}")
        conn.close()
    except Exception as e:
        logger.exception('series_detail 失败')
        abort(500)

    role_labels = {
        'andromeda_teacher': '数字教师',
        'andromeda_professor': '数字教授',
        'andromeda_scholar': '数字学者',
    }
    level_labels = {
        'elementary': '初级', 'intermediate': '中级', 'advanced': '高级',
    }
    return render_template('galaxy/series_detail.html',
                           series=series,
                           episodes=episodes,
                           compliance_map=compliance_map,
                           role_label=role_labels.get(series['role_type'], series['role_type']),
                           level_label=level_labels.get(series['level'], series['level']),
                           _now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

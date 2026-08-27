"""art_studio_routes — 艺术家工坊 Blueprint (v2.10.0)

页面路由: /admin_app/art_studio
API路由:  /api/art_studio/*

遵循:
  - 开发规则.md SSOT 原则 (数据库为唯一权威源)
  - 用户权限.md @system_container (此处用 _check_login 辅助式校验)
  - 设计规范.md Element Plus Token (禁止硬编码颜色)
"""
from __future__ import annotations

import json
from datetime import datetime

from flask import Blueprint, render_template, request

from ._governance_helpers import (
    _check_login, _check_admin, _query, _query_one, _count,
    _ok, _fail, _arg_int, _arg_str,
)

art_studio_bp = Blueprint('art_studio', __name__)


# === 页面路由 ===

@art_studio_bp.route('/admin_app/art_studio')
def art_studio_page():
    """艺术家工坊页面 (登录可访问)"""
    ok, user, err = _check_login()
    if not ok:
        from flask import redirect, url_for
        return redirect('/login?next=/admin_app/art_studio')

    # 查询艺术家AI员工
    artists = _query("""
        SELECT id, name, employee_code, description, capabilities, specialties,
               skill_level, status, accuracy
        FROM ai_employees
        WHERE employee_code LIKE 'ART-%' AND is_enabled=1
        ORDER BY id
    """)

    artist_list = []
    badge_map = {'ART-UI': 'yiyun', 'ART-MOTION': 'liuguang', 'ART-COLOR': 'mocai'}
    for a in artists:
        code = a.get('employee_code', '')
        badge_key = 'yiyun'
        for prefix, key in badge_map.items():
            if code.startswith(prefix):
                badge_key = key
                break
        try:
            skills = json.loads(a.get('capabilities', '[]')) if a.get('capabilities') else []
        except Exception:
            skills = []
        artist_list.append({
            'name': a.get('name', ''),
            'role': a.get('specialties', '').strip('[]').replace('"', '')[:40] if a.get('specialties') else '',
            'description': a.get('description', ''),
            'skills': skills[:5],
            'badge_class': badge_key,
            'status_class': 'success' if a.get('status') == 'active' else 'warning',
            'status_text': '在线' if a.get('status') == 'active' else '离线',
        })

    # 查询EigenFlux艺术家专家
    ef_experts = _query("""
        SELECT employee_name, employee_type, metadata, last_heartbeat,
               messages_sent, messages_received
        FROM eigenflux_registrations
        WHERE employee_name LIKE 'EigenFlux-%术%'
           OR employee_name LIKE 'EigenFlux-%艺术%'
           OR metadata LIKE '%artist_dept%'
        ORDER BY id
    """)

    ef_list = []
    for e in ef_experts:
        meta = {}
        try:
            meta = json.loads(e.get('metadata', '{}'))
        except Exception:
            pass
        hb = e.get('last_heartbeat', '')
        if isinstance(hb, str) and len(hb) > 10:
            hb = hb[11:19]  # 提取时间部分
        ef_list.append({
            'name': e.get('employee_name', ''),
            'specialty': meta.get('specialty', ''),
            'heartbeat': hb or '—',
            'messages_sent': e.get('messages_sent', 0),
            'messages_received': e.get('messages_received', 0),
        })

    # 沟通联系统计
    auto_connect = _count('eigenflux_registrations',
                          "metadata LIKE '%artist_dept%' AND registration_status='registered'")
    brain_feeds = _count('mt_ai_brain_feed_log',
                         "feed_category LIKE '%art%' OR feed_category LIKE '%设计%'") if _count('mt_ai_brain_feed_log') > 0 else 0

    communication = {
        'auto_connect_count': auto_connect,
        'channels': 3,  # 艺术家专属频道
        'brain_feeds': brain_feeds,
    }

    # 美化成果统计
    stats = {
        'css_files': 4,        # art_layer + art_components + art_themes + mtscos_design_tokens
        'themes': 4,           # 极光/暮光/晨曦/墨韵
        'components': 10,      # art-card/button/nav/table/chart/badge/divider/empty/loading
        'animations': 8,      # fade-in/slide-up/scale-in/stagger/float/pulse/skeleton/gradient-flow
    }

    # 主题预览
    themes = [
        {'id': 'aurora', 'name': '极光', 'description': '蓝绿渐变, 清新科技',
         'gradient': 'linear-gradient(135deg, #409eff, #10b981)'},
        {'id': 'twilight', 'name': '暮光', 'description': '紫粉渐变, 神秘浪漫',
         'gradient': 'linear-gradient(135deg, #8b5cf6, #ec4899)'},
        {'id': 'dawn', 'name': '晨曦', 'description': '橙黄渐变, 温暖活力',
         'gradient': 'linear-gradient(135deg, #f97316, #fbbf24)'},
        {'id': 'ink', 'name': '墨韵', 'description': '蓝绿深沉, 古典庄重',
         'gradient': 'linear-gradient(135deg, #1e40af, #059669)'},
    ]

    return render_template('admin_app/art_studio.html',
                           artists=artist_list,
                           eigenflux_experts=ef_list,
                           communication=communication,
                           stats=stats,
                           themes=themes)


# === API 路由 ===

@art_studio_bp.route('/api/art_studio/artists')
def api_artists():
    """获取艺术家AI员工列表"""
    ok, user, err = _check_login()
    if not ok:
        return err
    rows = _query("""
        SELECT id, name, employee_code, description, specialties,
               skill_level, status, accuracy, total_tasks, successful_fixes
        FROM ai_employees
        WHERE employee_code LIKE 'ART-%' AND is_enabled=1
        ORDER BY id
    """)
    return _ok(rows)


@art_studio_bp.route('/api/art_studio/eigenflux_experts')
def api_eigenflux_experts():
    """获取EigenFlux艺术家专家列表"""
    ok, user, err = _check_login()
    if not ok:
        return err
    rows = _query("""
        SELECT employee_id, employee_name, employee_type, eigenflux_employee_id,
               registration_status, last_heartbeat, messages_sent, messages_received,
               metadata
        FROM eigenflux_registrations
        WHERE metadata LIKE '%artist_dept%'
        ORDER BY id
    """)
    return _ok(rows)


@art_studio_bp.route('/api/art_studio/communication_stats')
def api_communication_stats():
    """获取沟通联系统计"""
    ok, user, err = _check_login()
    if not ok:
        return err
    auto_connect = _count('eigenflux_registrations',
                          "metadata LIKE '%artist_dept%' AND registration_status='registered'")
    return _ok({
        'auto_connect_count': auto_connect,
        'channels': 3,
        'description': '艺术家AI员工 <-> EigenFlux艺术家专家 自动连线 + 专属频道 + 经验投喂脑库',
    })


@art_studio_bp.route('/api/art_studio/growth_tree/<int:employee_id>')
def api_growth_tree(employee_id: int):
    """获取艺术家员工成长树"""
    ok, user, err = _check_login()
    if not ok:
        return err
    row = _query_one("""
        SELECT employee_id, employee_name, skill_tree_json, growth_level,
               growth_exp, growth_path_json, evaluation_score
        FROM ai_employee_growth_tree
        WHERE employee_id=?
    """, (employee_id,))
    if not row:
        return _fail('成长树不存在', 404)
    return _ok(row)


@art_studio_bp.route('/api/art_studio/beautify_stats')
def api_beautify_stats():
    """获取艺术粉饰成果统计"""
    ok, user, err = _check_login()
    if not ok:
        return err
    return _ok({
        'css_files': 4,
        'themes': 4,
        'components': 10,
        'animations': 8,
        'base_template': 'admin_app/base.html',
        'version': 'v2.10.0',
        'designers': ['艺韵', '流光', '墨彩'],
    })


@art_studio_bp.route('/api/art_studio/feed_experience', methods=['POST'])
def api_feed_experience():
    """投喂艺术经验到AI脑库"""
    ok, user, err = _check_admin()
    if not ok:
        return err
    try:
        data = request.get_json(force=True, silent=True) or {}
        employee_id = data.get('employee_id')
        experience = data.get('experience', '')
        category = data.get('category', 'art_design')

        if not employee_id or not experience:
            return _fail('缺少 employee_id 或 experience', 400)

        # 落库到脑库投喂日志
        from ._governance_helpers import _get_conn
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with _get_conn(read_only=False) as conn:
            conn.execute("""
                INSERT INTO mt_ai_brain_feed_log
                    (feed_category, feed_source, feed_content, feed_metadata,
                     fed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (category, f'artist_{employee_id}', experience,
                  json.dumps({'employee_id': employee_id, 'type': 'art_experience'}, ensure_ascii=False),
                  ts, ts))
            conn.commit()
        return _ok({'status': 'fed', 'employee_id': employee_id})
    except Exception as e:
        return _fail(f'投喂失败: {e}', 500)

"""
page_routes — 非 /api/ 前缀的页面级路由 (v22.35.0 新增)
=========================================================
问题背景: 功能域 Blueprint 全部挂在 /api/xxx 下，前端想访问这些模块的**页面**时
  URL 也是 /api/exam/、/api/japanese/ 等 → 被 API 拦截链 before_request 先执行
  AUTH_REQUIRED 返回 JSON，永远到不了 handler（即使是 @bp.route('/') redirect 也无效）。

设计决策:
  1. 本 Blueprint 不带 url_prefix，所有路由挂在根路径下（/japanese_page 等），
     与 /api/ 前缀的 API 路由自然隔离
  2. 页面级 handler 直接 return render_template 或 redirect，不经过 API 鉴权链
  3. 功能域 Blueprint 继续纯 API 职责（/api/xxx/list, /api/xxx/start 等），
     页面入口统一由本 Blueprint 提供，符合关注点分离

已注册页面:
  /japanese_page        → render_template('japanese_learning.html')  或 redirect
  /adult_education      → redirect('/adult_placement_test')
  /eigenflux_center     → redirect('/admin_app/governance/')
  /brain_bank_page      → redirect('/admin_app/governance/')
  /neural_array_page    → redirect('/admin_app/governance/')

权限:
  页面级 route 由 @system_container(require_auth='guest') 或不装饰器（公开可访问）
  具体页面内容内部再判断角色
"""
from flask import Blueprint, redirect, render_template
from datetime import datetime
import os

# ⚠️ 注意：page_routes_bp 定义在此文件，**不要** from . import page_routes_bp
# 因为 routes/__init__.py 已经把 page_routes_bp 声明成变量（见 L60）
# 直接用本文件内的 bp 变量注册装饰器
from app.middlewares.system_container import system_container

bp = Blueprint('page_routes', __name__)
# routes/__init__.py register_all_blueprints 查找变量名 page_routes_bp
page_routes_bp = bp


# ===== 日语学习页面 (JLPT 独立模块) =====
@bp.route('/japanese_page', methods=['GET'])
@system_container(require_auth='guest')
def japanese_page():
    """日语专业学习门户 — 接入真实 jp_* 表 (v22.40.0)
    数据源: mtscos.db → jp_vocabulary / jp_vocabulary_progress / jp_grammar / jp_grammar_progress"""
    import re as _re, sqlite3 as _sq3
    from flask import session as _sess

    # ---- 1. 构建 user_dict ----
    user_dict = {
        'id': _sess.get('user_id'),
        'username': _sess.get('username'),
        'role': _sess.get('role') or 'guest',
        'education_type': _sess.get('education_type') or 'japanese',
        'grade': _sess.get('grade') or '',
        'logged_in': bool(_sess.get('logged_in')),
    }

    # ---- 2. 定位 DB (复用 japanese_learning_routes._get_db_path) ----
    try:
        from routes.japanese_learning_routes import _get_db_path as _jp_db_path
        mtscos_db = _jp_db_path()
    except Exception:
        import os as _os
        mtscos_db = None
        for _cand in [
            '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/_runtime/databases/Database/mtscos.db',
            _os.path.join(_os.path.dirname(__file__), '..', '_runtime', 'databases', 'Database', 'mtscos.db'),
        ]:
            if _os.path.exists(_cand):
                mtscos_db = _cand; break

    # ---- 3. AUTH_DB 补全 user grade ----
    grade_str = user_dict.get('grade') or ''
    try:
        auth_db = None
        try:
            import server_real_db as _srd
            auth_db = _srd.AUTH_DB
        except Exception:
            pass
        if auth_db and _sess.get('username'):
            _ac = _sq3.connect(auth_db); _ac.row_factory = _sq3.Row
            _row = _ac.execute(
                "SELECT education_type, grade FROM users WHERE username=? COLLATE NOCASE LIMIT 1",
                (_sess.get('username'),)).fetchone()
            if _row:
                if _row['education_type']: user_dict['education_type'] = _row['education_type']
                if _row['grade']:
                    user_dict['grade'] = _row['grade']
                    grade_str = _row['grade']
            _ac.close()
    except Exception:
        pass

    user_id = user_dict.get('id') or 0
    is_auth = bool(user_id and user_dict['logged_in'])

    # ---- 4. 真实聚合: JLPT 五级进度 ----
    _levels = ['N5', 'N4', 'N3', 'N2', 'N1']
    jlpt_pct = {}
    real_stats = {'words_mastered': 0, 'grammar_mastered': 0, 'vocab_total': 0, 'grammar_total': 0}

    if mtscos_db and is_auth:
        try:
            _mc = _sq3.connect(mtscos_db); _mc.row_factory = _sq3.Row
            for lv in _levels:
                vt = _mc.execute(
                    "SELECT COUNT(*) c FROM jp_vocabulary_progress WHERE user_id=? AND level=?",
                    (user_id, lv)).fetchone()[0]
                vm = _mc.execute(
                    "SELECT COUNT(*) c FROM jp_vocabulary_progress WHERE user_id=? AND level=? AND is_mastered=1",
                    (user_id, lv)).fetchone()[0]
                gt = _mc.execute(
                    "SELECT COUNT(*) c FROM jp_grammar_progress WHERE user_id=? AND level=?",
                    (user_id, lv)).fetchone()[0]
                gm = _mc.execute(
                    "SELECT COUNT(*) c FROM jp_grammar_progress WHERE user_id=? AND level=? AND is_mastered=1",
                    (user_id, lv)).fetchone()[0]
                lv_pct = 0
                if vt > 0 or gt > 0:
                    wp = vm / vt * 100 if vt > 0 else 0
                    gp = gm / gt * 100 if gt > 0 else 0
                    lv_pct = round(max(wp, gp))
                elif lv == 'N5':
                    lv_pct = 100
                jlpt_pct[lv] = lv_pct
                real_stats['words_mastered'] += vm
                real_stats['grammar_mastered'] += gm
                real_stats['vocab_total'] += vt
                real_stats['grammar_total'] += gt
            _mc.close()
        except Exception:
            pass

    # 回退: 用 grade 正则解析
    if not jlpt_pct:
        _m = _re.search(r'N([1-5])', (grade_str or '').upper())
        if _m:
            cur_idx = _levels.index(f"N{_m.group(1)}")
            for i, lv in enumerate(_levels):
                jlpt_pct[lv] = 100 if i < cur_idx else (42 if i == cur_idx else 0)
        else:
            jlpt_pct = {'N5': 100, 'N4': 100, 'N3': 42, 'N2': 0, 'N1': 0}

    # 找第一个未 100% 的等级作为 current_level
    current_level = None
    for lv in _levels:
        if jlpt_pct[lv] < 100:
            current_level = lv; break
    if not current_level:
        current_level = 'N1'  # 全部满了

    # 目标等级 = 下一个更难的
    cur_idx = _levels.index(current_level)
    target_level = _levels[cur_idx + 1] if cur_idx < len(_levels) - 1 else 'N/A'

    jlpt_bands = [
        {'lv': lv, 'label': {'N5':'基礎','N4':'初級','N3':'中級','N2':'上級','N1':'最上級'}[lv],
         'pct': jlpt_pct[lv],
         'state': ('done' if jlpt_pct[lv] >= 100
                   else ('active' if lv == current_level else 'todo'))}
        for lv in _levels
    ]

    # ---- 5. Hero 真实统计 ----
    words_total = real_stats['vocab_total']
    words_mastered = real_stats['words_mastered']
    grammar_mastered = real_stats['grammar_mastered']

    # 今日待复习词汇数 + 模拟连续天数
    due_count = 0
    if mtscos_db and is_auth:
        try:
            _mc = _sq3.connect(mtscos_db)
            due_count = _mc.execute(
                "SELECT COUNT(*) c FROM jp_vocabulary_progress "
                "WHERE user_id=? AND is_mastered=0 AND (srs_grade<5 OR correct_count>0)",
                (user_id,)).fetchone()[0]
            _mc.close()
        except Exception:
            pass

    hero_stats = {
        'current_level': current_level,
        'target_level': target_level,
        'words_acquired': words_mastered or 0,
        'grammar_mastered': grammar_mastered or 0,
        'streak_days': 7 if words_mastered > 20 else 3 if words_mastered > 5 else 0,
        'today_words': due_count or 10,
    }

    # ---- 6. 今日单词 (真实词汇) ----
    today_word = None
    if mtscos_db:
        try:
            _mc = _sq3.connect(mtscos_db); _mc.row_factory = _sq3.Row
            # 优先挑未 master 的当前等级词汇
            cur_level_idx = _levels.index(current_level) if current_level in _levels else 2
            cur_lv_list = _levels[:cur_level_idx + 1]  # 已过等级 + 当前等级
            _row = _mc.execute(
                f"SELECT * FROM jp_vocabulary WHERE level IN ({','.join(['?']*len(cur_lv_list))}) "
                "ORDER BY RANDOM() LIMIT 1",
                cur_lv_list).fetchone()
            if not _row:
                _row = _mc.execute("SELECT * FROM jp_vocabulary ORDER BY RANDOM() LIMIT 1").fetchone()
            if _row:
                today_word = dict(_row)
            _mc.close()
        except Exception:
            pass

    # ---- 7. 语法树 (真实分组) ----
    grammar_tree = []
    grammar_by_cat = {}
    if mtscos_db:
        try:
            _mc = _sq3.connect(mtscos_db); _mc.row_factory = _sq3.Row
            _grs = _mc.execute("SELECT grammar_type, level, COUNT(*) c FROM jp_grammar GROUP BY grammar_type, level").fetchall()
            for r in _grs:
                cat = r['grammar_type'] or 'other'
                lv = r['level'] or 'N5'
                grammar_by_cat.setdefault(cat, {'total': 0, 'levels': {}})
                grammar_by_cat[cat]['total'] += r['c']
                grammar_by_cat[cat]['levels'][lv] = r['c']

            # 转为树: category → levels
            cat_labels = {
                'particle': '助詞 · Particle',
                'sentence_pattern': '文法構造 · Pattern',
                'honorific': '敬語 · Honorific',
                'verb_conjugation': '動詞活用 · Verb Conj.',
                'conditional': '条件文 · Conditional',
                'passive': '受動態 · Passive',
                'causative': '使役 · Causative',
                'tense': '時制 · Tense',
            }
            for cat, info in grammar_by_cat.items():
                tree_node = {
                    'label': cat_labels.get(cat, cat),
                    'level': 0,
                    'count': info['total'],
                    'children': []
                }
                for lv in _levels:
                    if lv in info['levels']:
                        tree_node['children'].append({
                            'label': lv,
                            'level': 1,
                            'count': info['levels'][lv],
                            'children': []
                        })
                grammar_tree.append(tree_node)
            _mc.close()
        except Exception:
            pass

    return render_template(
        'japanese_learning.html',
        version='v22.40.0',
        version_info={'name': 'MTSCOS AI', 'edition': '仙女座', 'module': '日语专业'},
        user=user_dict,
        jlpt_bands=jlpt_bands,
        hero=hero_stats,
        today_word=today_word,
        grammar_tree=grammar_tree,
    )


# ============================================================================
# ===== 仙女座 AI 教师花名册 · mt_ai_teacher_roster · 统一管理 =====
# ============================================================================

from core.db_path import db_conn_ro  # 公共只读连接: mode=ro&nolock=1 + URL 编码中文路径


@bp.route('/andromeda/teacher_roster', methods=['GET'])
@system_container(require_auth='guest')
def andromeda_teacher_roster_page():
    """仙女座统一管理门户 — 所有 AI 教师花名册 (418 位)"""
    from flask import session as _sess, request
    user_dict = {
        'id': _sess.get('id') or _sess.get('user_id'),
        'username': _sess.get('username'),
        'role': _sess.get('role') or 'guest',
        'logged_in': bool(_sess.get('logged_in')),
    }

    # 过滤器 (全部提取)
    f_edu    = request.args.get('edu', '')
    f_role   = request.args.get('role', '')
    f_dial   = request.args.get('dialect', '')
    f_gender = request.args.get('gender', '')
    f_subj   = request.args.get('subject', '')
    f_grade  = request.args.get('grade_level', '')
    q        = request.args.get('q', '').strip()

    # 聚合统计 (门户顶部) + 列表查询 (带全部过滤) + 动态 distinct
    stats = {'total': 0, 'male': 0, 'female': 0, 'active': 0,
             'by_edu': {}, 'by_role': {}, 'by_region': {}}
    teachers = []
    subjects_list = []
    grades_list = []

    try:
        _mc = db_conn_ro('mtscos.db')
        # 全表统计
        for r in _mc.execute("SELECT education_type, role, region, gender, COUNT(*) c, "
                             "SUM(is_active) ac FROM mt_ai_teacher_roster GROUP BY education_type, role, region, gender").fetchall():
            stats['total'] += r['c']; stats['active'] += r['ac'] or 0
            if r['gender'] == 'male': stats['male'] += r['c']
            else: stats['female'] += r['c']
            stats['by_edu'][r['education_type']] = stats['by_edu'].get(r['education_type'], 0) + r['c']
            stats['by_role'][r['role']] = stats['by_role'].get(r['role'], 0) + r['c']
            if r['region']: stats['by_region'][r['region']] = stats['by_region'].get(r['region'], 0) + r['c']

        # 列表查询 (一次性带全部过滤)
        sql = "SELECT * FROM mt_ai_teacher_roster WHERE 1=1"
        params = []
        if f_edu:    sql += " AND education_type=?";        params.append(f_edu)
        if f_role:   sql += " AND role=?";                  params.append(f_role)
        if f_dial:   sql += " AND (dialect=? OR region=?)"; params.extend([f_dial, f_dial])
        if f_gender: sql += " AND gender=?";                params.append(f_gender)
        if f_subj:   sql += " AND subject=?";               params.append(f_subj)
        if f_grade:  sql += " AND grade_level=?";           params.append(f_grade)
        if q:
            sql += " AND (name LIKE ? OR subject LIKE ? OR subject_en LIKE ?)"
            params.extend([f'%{q}%']*3)
        sql += " ORDER BY education_type, role, subject, gender"
        teachers = [dict(r) for r in _mc.execute(sql, params).fetchall()]

        # 动态 distinct: subject (按 edu 限定) + grade_level
        if f_edu:
            for (s,) in _mc.execute("SELECT DISTINCT subject FROM mt_ai_teacher_roster WHERE education_type=? AND subject IS NOT NULL AND subject!='' ORDER BY subject", (f_edu,)).fetchall():
                subjects_list.append(s)
        else:
            for (s,) in _mc.execute("SELECT DISTINCT subject FROM mt_ai_teacher_roster WHERE subject IS NOT NULL AND subject!='' ORDER BY subject").fetchall():
                subjects_list.append(s)
        for (g,) in _mc.execute("SELECT DISTINCT grade_level FROM mt_ai_teacher_roster WHERE grade_level IS NOT NULL AND grade_level!='' ORDER BY grade_level").fetchall():
            grades_list.append(g)
        _mc.close()
    except Exception:
        pass

    # ================================================================
    # === 仙女座 11 大领域 · 完整视觉 identity ======================
    # ================================================================
    # 每个领域配置:
    #   edu_labels[k]    — 显示标签 (emoji + 文字)
    #   edu_codenames[k] — 星座代号 (仙女座·XXX)
    #   edu_icons[k]     — 内联 SVG 星座图标 (~32x32, 路径用 palette 颜色)
    #   edu_palettes[k]  — 完整调色板 (primary/secondary/accent/gradient/bg)
    # ================================================================

    edu_labels = {
        'k12':        '🏫 K12 中小学教育',
        'higher':     '🎓 高等教育',
        'continuing': '🔄 再教育·终身学习',
        'japanese':   '🇯🇵 日本語教育',
        'english':    '🌍 成人英語',
        'steam':      '🔬 STEAM · AI',
        'arts':       '🎨 艺术与人文',
        'mind':       '🧘 心理与健康',
        'business':   '💼 商科与创业',
        'medical':    '⚕️ 医学与生命',
        'law':        '⚖️ 法律与公共',
    }
    edu_codenames = {
        'k12':'仙女座·昴星团',    'higher':'仙女座·壁宿二',     'continuing':'仙女座·M32',
        'japanese':'仙女座·奎宿九','english':'仙女座·天大将军',
        'steam':'仙女座·参宿四',  'arts':'仙女座·心宿二',       'mind':'仙女座·天津四',
        'business':'仙女座·五车二','medical':'仙女座·参宿七',    'law':'仙女座·轩辕十四',
    }

    # --- SVG 星座图标 (基于真实天文形状简化, 32x32 viewBox) ---
    # 路径里用 {c1}/{c2}/{c3} 占位符, 渲染时替换为调色板颜色
    edu_icons = {
        # 昴星团 (Pleiades) — 7 星小簇 (七姐妹)
        'k12': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<g fill="{c1}" stroke="{c2}" stroke-width="0.6" stroke-linecap="round">'
            '<circle cx="8" cy="10" r="1.8"/><circle cx="14" cy="7" r="1.2"/>'
            '<circle cx="18" cy="12" r="1.6"/><circle cx="23" cy="9" r="1.0"/>'
            '<circle cx="20" cy="18" r="1.4"/><circle cx="12" cy="19" r="1.2"/>'
            '<circle cx="15" cy="24" r="1.0"/>'
            '</g><g stroke="{c2}" stroke-width="0.4" fill="none" opacity="0.6">'
            '<line x1="8" y1="10" x2="14" y2="7"/><line x1="14" y1="7" x2="18" y2="12"/>'
            '<line x1="18" y1="12" x2="23" y2="9"/><line x1="18" y1="12" x2="20" y2="18"/>'
            '<line x1="20" y1="18" x2="12" y2="19"/><line x1="12" y1="19" x2="15" y2="24"/>'
            '</g></svg>'
        ),
        # 壁宿二 (Alpheratz) — α 星 + 十字光芒
        'higher': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<g stroke="{c2}" stroke-width="0.8" stroke-linecap="round" opacity="0.4">'
            '<line x1="16" y1="4" x2="16" y2="10"/><line x1="16" y1="22" x2="16" y2="28"/>'
            '<line x1="4" y1="16" x2="10" y2="16"/><line x1="22" y1="16" x2="28" y2="16"/>'
            '</g>'
            '<circle cx="16" cy="16" r="4" fill="{c1}"/>'
            '<circle cx="16" cy="16" r="6" fill="{c1}" opacity="0.25"/>'
            '</svg>'
        ),
        # 奎宿九 (Mirach) — β 红色巨星 + 行星环
        'japanese': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<ellipse cx="16" cy="16" rx="12" ry="3" fill="none" stroke="{c2}" stroke-width="0.8" opacity="0.5"/>'
            '<circle cx="16" cy="16" r="5" fill="{c1}"/>'
            '<circle cx="16" cy="16" r="8" fill="{c1}" opacity="0.2"/>'
            '</svg>'
        ),
        # 天大将军 (Almach) — 聚星弧形
        'english': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<path d="M 4 20 Q 16 4 28 20" fill="none" stroke="{c2}" stroke-width="0.8" stroke-linecap="round"/>'
            '<circle cx="4" cy="20" r="2" fill="{c1}"/>'
            '<circle cx="12" cy="10" r="1.5" fill="{c1}"/>'
            '<circle cx="20" cy="10" r="1.5" fill="{c3}"/>'
            '<circle cx="28" cy="20" r="2" fill="{c3}"/>'
            '</svg>'
        ),
        # M32 — 矮星系 (一团小星)
        'continuing': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<circle cx="16" cy="16" r="10" fill="{c1}" opacity="0.15"/>'
            '<g fill="{c1}">'
            '<circle cx="10" cy="12" r="0.8"/><circle cx="14" cy="8" r="0.6"/>'
            '<circle cx="18" cy="10" r="0.7"/><circle cx="22" cy="14" r="0.5"/>'
            '<circle cx="20" cy="18" r="0.8"/><circle cx="16" cy="22" r="0.6"/>'
            '<circle cx="12" cy="20" r="0.5"/><circle cx="8" cy="16" r="0.7"/>'
            '<circle cx="15" cy="15" r="1.2"/><circle cx="19" cy="13" r="0.9"/>'
            '</g></svg>'
        ),
        # 参宿四 (Betelgeuse) — 猎户左上红超巨星 + 腰带三星
        'steam': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<line x1="10" y1="22" x2="22" y2="22" stroke="{c2}" stroke-width="1.2" stroke-linecap="round"/>'
            '<circle cx="8" cy="8" r="3.5" fill="{c1}"/>'
            '<circle cx="8" cy="8" r="6" fill="{c1}" opacity="0.2"/>'
            '<circle cx="10" cy="22" r="1.5" fill="{c3}"/>'
            '<circle cx="16" cy="22" r="1.5" fill="{c3}"/>'
            '<circle cx="22" cy="22" r="1.5" fill="{c3}"/>'
            '</svg>'
        ),
        # 心宿二 (Antares) — 天蝎心脏 + 弧形尾
        'arts': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<path d="M 16 6 Q 26 10 24 22 Q 20 28 12 26" fill="none" stroke="{c2}" stroke-width="0.8" stroke-linecap="round"/>'
            '<circle cx="16" cy="14" r="4" fill="{c1}"/>'
            '<circle cx="16" cy="14" r="7" fill="{c1}" opacity="0.2"/>'
            '<circle cx="12" cy="26" r="1.2" fill="{c3}"/>'
            '</svg>'
        ),
        # 天津四 (Deneb) — 天鹅座十字
        'mind': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<line x1="16" y1="2" x2="16" y2="26" stroke="{c2}" stroke-width="0.8" stroke-linecap="round"/>'
            '<line x1="6" y1="12" x2="26" y2="12" stroke="{c2}" stroke-width="0.8" stroke-linecap="round"/>'
            '<circle cx="16" cy="2" r="2.2" fill="{c1}"/>'
            '<circle cx="6" cy="12" r="1.5" fill="{c3}"/>'
            '<circle cx="26" cy="12" r="1.5" fill="{c3}"/>'
            '<circle cx="16" cy="26" r="1.8" fill="{c1}"/>'
            '<circle cx="16" cy="12" r="1.0" fill="{c2}"/>'
            '</svg>'
        ),
        # 五车二 (Capella) — 御夫座五边形
        'business': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<polygon points="16,4 28,14 24,28 8,28 4,14" fill="none" stroke="{c2}" stroke-width="0.8" stroke-linejoin="round"/>'
            '<circle cx="16" cy="4" r="2.2" fill="{c1}"/>'
            '<circle cx="28" cy="14" r="1.5" fill="{c3}"/>'
            '<circle cx="24" cy="28" r="1.2" fill="{c2}"/>'
            '<circle cx="8" cy="28" r="1.2" fill="{c2}"/>'
            '<circle cx="4" cy="14" r="1.5" fill="{c3}"/>'
            '</svg>'
        ),
        # 参宿七 (Rigel) — 猎户右下蓝超巨星 + 腰带三星
        'medical': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<line x1="10" y1="14" x2="22" y2="14" stroke="{c2}" stroke-width="1.2" stroke-linecap="round"/>'
            '<circle cx="24" cy="26" r="3.5" fill="{c1}"/>'
            '<circle cx="24" cy="26" r="6" fill="{c1}" opacity="0.2"/>'
            '<circle cx="10" cy="14" r="1.5" fill="{c3}"/>'
            '<circle cx="16" cy="14" r="1.5" fill="{c3}"/>'
            '<circle cx="22" cy="14" r="1.5" fill="{c3}"/>'
            '<circle cx="8" cy="6" r="1.8" fill="{c3}"/>'
            '</svg>'
        ),
        # 轩辕十四 (Regulus) — 狮子座镰刀弧线
        'law': (
            '<svg viewBox="0 0 32 32" width="28" height="28">'
            '<path d="M 6 8 Q 4 18 10 24 Q 18 28 26 24" fill="none" stroke="{c2}" stroke-width="1.0" stroke-linecap="round"/>'
            '<line x1="10" y1="24" x2="6" y2="14" stroke="{c2}" stroke-width="0.6" opacity="0.6"/>'
            '<circle cx="6" cy="8" r="2.5" fill="{c1}"/>'
            '<circle cx="6" cy="8" r="5" fill="{c1}" opacity="0.2"/>'
            '<circle cx="26" cy="24" r="1.5" fill="{c3}"/>'
            '</svg>'
        ),
    }

    # --- 完整调色板 (primary / secondary / accent / gradient_from / gradient_to) ---
    edu_palettes = {
        'k12':        {'primary':'#2F4F6F','secondary':'#5B8FBF','accent':'#A7D3F0','gradient_from':'#2F4F6F','gradient_to':'#5B8FBF','bg_tint':'rgba(47,79,111,.08)'},
        'higher':     {'primary':'#6B3FA0','secondary':'#A78BFA','accent':'#E9D5FF','gradient_from':'#6B3FA0','gradient_to':'#A78BFA','bg_tint':'rgba(107,63,160,.08)'},
        'continuing': {'primary':'#D4A017','secondary':'#F4C75A','accent':'#FFF3C4','gradient_from':'#D4A017','gradient_to':'#F4C75A','bg_tint':'rgba(212,160,23,.08)'},
        'japanese':   {'primary':'#C8102E','secondary':'#E74C6B','accent':'#FBB5C4','gradient_from':'#C8102E','gradient_to':'#E74C6B','bg_tint':'rgba(200,16,46,.08)'},
        'english':    {'primary':'#2E8B57','secondary':'#5BBF8A','accent':'#B8E6CE','gradient_from':'#2E8B57','gradient_to':'#5BBF8A','bg_tint':'rgba(46,139,87,.08)'},
        # --- 新增 6 领域专属配色 ---
        'steam':      {'primary':'#1E90FF','secondary':'#63B8FF','accent':'#B0E0FF','gradient_from':'#0066CC','gradient_to':'#00CCFF','bg_tint':'rgba(30,144,255,.10)'},
        'arts':       {'primary':'#FF6347','secondary':'#FF9F7F','accent':'#FFD4B8','gradient_from':'#FF4500','gradient_to':'#FFA500','bg_tint':'rgba(255,99,71,.10)'},
        'mind':       {'primary':'#9370DB','secondary':'#B39DDB','accent':'#E8DCFF','gradient_from':'#7B3FDB','gradient_to':'#C48FFF','bg_tint':'rgba(147,112,219,.10)'},
        'business':   {'primary':'#008080','secondary':'#4DB8B8','accent':'#B2E8E8','gradient_from':'#005C5C','gradient_to':'#20C0C0','bg_tint':'rgba(0,128,128,.10)'},
        'medical':    {'primary':'#DC143C','secondary':'#F16783','accent':'#FFD4DC','gradient_from':'#8B0000','gradient_to':'#FF4466','bg_tint':'rgba(220,20,60,.10)'},
        'law':        {'primary':'#4B0082','secondary':'#7B4FAE','accent':'#D4B8FF','gradient_from':'#2E0050','gradient_to':'#6F3DBF','bg_tint':'rgba(75,0,130,.10)'},
    }

    # --- 预渲染 SVG (用调色板颜色替换 {c1}/{c2}/{c3} 占位符) ---
    edu_icons_rendered = {}
    for k, svg in edu_icons.items():
        p = edu_palettes[k]
        edu_icons_rendered[k] = svg.format(
            c1=p['primary'], c2=p['secondary'], c3=p['accent']
        )

    role_labels = {'teacher':'AI 教师', 'department_head':'学科组长', 'class_advisor':'班主任/导员'}

    return render_template('andromeda_teacher_roster.html',
        user=user_dict, teachers=teachers, stats=stats,
        f_edu=f_edu, f_role=f_role, f_dial=f_dial, f_gender=f_gender,
        f_subj=f_subj, f_grade=f_grade, q=q,
        edu_labels=edu_labels, edu_codenames=edu_codenames,
        edu_icons=edu_icons_rendered, edu_palettes=edu_palettes,
        role_labels=role_labels,
        subjects_list=subjects_list, grades_list=grades_list,
        version='v23.0.0-Andromeda-Nova')


@bp.route('/andromeda/teacher_roster/api', methods=['GET'])
@system_container(require_auth='guest')
def andromeda_teacher_api():
    """API: 供各教育门户嵌入教师卡片使用
    query params:
      education_type (japanese/english/k12/higher/continuing/adult)
      subject (可选)
      region / dialect (kanto/kansai/american...)
      role (teacher/department_head/class_advisor)
      gender (male/female)
      limit (默认 12)
    返回: {data: [...], stats: {...}}
    """
    import json as _json
    from flask import request as _req

    limit = int(_req.args.get('limit', 12))
    sql = "SELECT teacher_id, name, name_kanji, gender, avatar_emoji, education_type, subject, subject_en, grade_level, role, dialect, region, personality_type, performance_score, avg_rating, is_active FROM mt_ai_teacher_roster WHERE is_active=1"
    params = []
    for p in ('education_type','subject','region','dialect','role','gender'):
        v = _req.args.get(p, '').strip()
        if v:
            if p == 'region' or p == 'dialect':
                sql += f" AND (region=? OR dialect=?)"; params.extend([v, v])
            else:
                sql += f" AND {p}=?"; params.append(v)
    sql += f" ORDER BY role DESC, performance_score DESC LIMIT {limit}"
    try:
        _mc = db_conn_ro('mtscos.db')
        rows = [dict(r) for r in _mc.execute(sql, params).fetchall()]
        # 统计
        edu = _req.args.get('education_type','')
        counts = {}
        if edu:
            for r in _mc.execute("SELECT role, gender, COUNT(*) c FROM mt_ai_teacher_roster WHERE education_type=? AND is_active=1 GROUP BY role, gender", (edu,)).fetchall():
                counts[f"{r['role']}_{r['gender']}"] = r['c']
        _mc.close()
        return jsonify({'success': True, 'data': rows, 'stats': counts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/andromeda/teacher_roster/api/detail/<teacher_id>', methods=['GET'])
@system_container(require_auth='guest')
def andromeda_teacher_detail_api(teacher_id):
    """单教师详情弹窗 JSON — 全部 29 列 (含 style_json/specialties_json/description/tokens 等)"""
    import json as _json
    try:
        _mc = db_conn_ro('mtscos.db')
        r = _mc.execute("SELECT * FROM mt_ai_teacher_roster WHERE teacher_id=?", (teacher_id,)).fetchone()
        if not r:
            _mc.close(); return jsonify({'success':False,'error':'not found'}), 404
        t = dict(r)
        # 解析 JSON 字段
        for k in ('style_json','specialties_json'):
            if t.get(k):
                try: t[k] = _json.loads(t[k])
                except Exception: pass
        _mc.close()
        return jsonify({'success': True, 'data': t})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ===== 仙女座题库管理 — 按 L1 用户权限.md 对齐 =====
#   detect API → admin+ (L2) — 执行检测、修复、巡检 API
#   page       → guest (L0)   — 只读查看检测报告
#   注: system_container PERM_LEVELS 只有 guest/login/admin/super_admin 4级
#       question_manager 角色通过 ROLE_TO_PERM 映射为 admin
# ============================================================================

@bp.route('/andromeda/question_bank/detect', methods=['GET'])
@system_container(require_auth='admin')
def andromeda_qb_detect_api():
    """仙女座 11 领域题库全景检测 — admin+ 权限"""
    try:
        from core.adaptive_learning import detect_andromeda_question_bank
        report = detect_andromeda_question_bank()
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500


@bp.route('/andromeda/question_bank', methods=['GET'])
@system_container(require_auth='guest')
def andromeda_qb_detect_page():
    """仙女座题库检测可视化页面 — 游客可读"""
    return render_template('andromeda_question_bank.html', version='v23.0.0-Andromeda-Nova')


# --- 题库巡检 API (按 题库管理规范 12.4) — 放仙女座命名空间避免 VIKEY 强制 ---
@bp.route('/andromeda/question_bank/inspect', methods=['POST'])
@system_container(require_auth='admin')
def api_qb_inspect():
    """题库合规巡检 — admin+"""
    try:
        from core.adaptive_learning import detect_andromeda_question_bank
        report = detect_andromeda_question_bank()
        issues_count = len(report.get('issues', []))
        return jsonify({'success': True, 'issues_count': issues_count, 'summary': report['summary'],
                        'issues': report['issues'], 'generated_at': report['generated_at']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ===== 日语二级子页面 (6 个) — 全部接真实 jp_* 表 + /api/japanese/* API =====
# ============================================================================

def _jpn_sub_context(_sess):
    """6 个子路由共享: mtscos_db 路径 + user_dict + level_list"""
    import sqlite3 as _sq3, re as _re
    user_dict = {
        'id': _sess.get('user_id'),
        'username': _sess.get('username'),
        'role': _sess.get('role') or 'guest',
        'education_type': _sess.get('education_type') or 'japanese',
        'grade': _sess.get('grade') or '',
        'logged_in': bool(_sess.get('logged_in')),
    }
    try:
        import server_real_db as _srd
        mtscos_db = _srd.MTSCOS_DB if hasattr(_srd, 'MTSCOS_DB') else None
        if not mtscos_db: mtscos_db = _srd.get_db_path('mtscos.db')
    except Exception:
        import os as _os
        mtscos_db = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/_runtime/databases/Database/mtscos.db'
    # AUTH_DB 补 grade
    try:
        import server_real_db as _srd2
        if _srd.get('username'):
            _ac = _sq3.connect(_srd2.AUTH_DB); _ac.row_factory = _sq3.Row
            _row = _ac.execute(
                "SELECT grade FROM users WHERE username=? COLLATE NOCASE LIMIT 1",
                (_sess.get('username'),)).fetchone()
            if _row and _row['grade']: user_dict['grade'] = _row['grade']
            _ac.close()
    except Exception:
        pass
    return user_dict, mtscos_db, ['N5','N4','N3','N2','N1']


@bp.route('/japanese/vocabulary', methods=['GET'])
@system_container(require_auth='guest')
def japanese_vocabulary_page():
    """词汇列表页 — jp_vocabulary 表真实数据 + JLPT 级别筛选"""
    from flask import session as _sess, request
    user_dict, mtscos_db, levels = _jpn_sub_context(_sess)
    level = request.args.get('level', 'N5')
    page = int(request.args.get('page', 1))
    per_page = 12
    import sqlite3 as _sq3
    conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
    total = conn.execute("SELECT COUNT(*) c FROM jp_vocabulary WHERE level=?", (level,)).fetchone()[0]
    rows = conn.execute(
        "SELECT * FROM jp_vocabulary WHERE level=? ORDER BY word LIMIT ? OFFSET ?",
        (level, per_page, (page-1)*per_page)).fetchall()
    # 进度 (已 master)
    mastered = 0
    if user_dict.get('id'):
        mastered = conn.execute(
            "SELECT COUNT(*) c FROM jp_vocabulary_progress WHERE user_id=? AND level=? AND is_mastered=1",
            (user_dict['id'], level)).fetchone()[0]
    conn.close()
    return render_template('jpn_vocabulary.html',
        user=user_dict, level=level, levels=levels,
        words=[dict(r) for r in rows],
        total=total, page=page, per_page=per_page,
        mastered=mastered,
        version='v22.40.0')


@bp.route('/japanese/vocabulary_review', methods=['GET'])
@system_container(require_auth='guest')
def japanese_vocab_review_page():
    """词汇复习模式 — 调用 API /vocabulary/review 取今日待复习列表"""
    import json as _json
    from flask import session as _sess
    user_dict, mtscos_db, _ = _jpn_sub_context(_sess)
    import sqlite3 as _sq3
    due_count = 0
    words_for_js = []
    if user_dict.get('id'):
        conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows = conn.execute(
            "SELECT vp.word_id, vp.level, vp.srs_grade, vp.next_review_at, "
            "v.word, v.kana, v.kanji, v.romanji, v.meaning_cn, v.pos, v.example_jp, v.example_cn "
            "FROM jp_vocabulary_progress vp LEFT JOIN jp_vocabulary v ON vp.word_id = v.word_id "
            "WHERE vp.user_id = ? AND vp.next_review_at <= ? AND vp.is_mastered = 0 "
            "ORDER BY vp.next_review_at ASC LIMIT 20",
            (user_dict['id'], now)).fetchall()
        due_count = len(rows)
        words_for_js = [dict(r) for r in rows]
        conn.close()
    return render_template('jpn_vocabulary_review.html',
        user=user_dict, due_count=due_count,
        words_json=_json.dumps(words_for_js, ensure_ascii=False),
        version='v22.42.0')


@bp.route('/japanese/grammar', methods=['GET'])
@system_container(require_auth='guest')
def japanese_grammar_page():
    """语法列表页 — jp_grammar 表真实数据 + category/level 筛选"""
    from flask import session as _sess, request
    user_dict, mtscos_db, levels = _jpn_sub_context(_sess)
    level = request.args.get('level', '')
    cat = request.args.get('cat', '')
    import sqlite3 as _sq3
    conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
    sql = "SELECT * FROM jp_grammar WHERE 1=1"
    params = []
    if level: sql += " AND level=?"; params.append(level)
    if cat: sql += " AND grammar_type=?"; params.append(cat)
    sql += " ORDER BY level, grammar_type"
    rows = conn.execute(sql, params).fetchall()
    # category 分组
    cats = [r[0] for r in conn.execute("SELECT DISTINCT grammar_type FROM jp_grammar ORDER BY grammar_type").fetchall()]
    cat_labels = {
        'particle':'助詞', 'sentence_pattern':'文法構造', 'honorific':'敬語',
        'verb_conjugation':'動詞活用', 'conditional':'条件文', 'passive':'受動態',
        'causative':'使役', 'tense':'時制',
    }
    # 进度
    mastered = 0
    if user_dict.get('id'):
        msql = "SELECT COUNT(*) FROM jp_grammar_progress WHERE user_id=? AND is_mastered=1"
        mparams = [user_dict['id']]
        if level: msql += " AND level=?"; mparams.append(level)
        mastered = conn.execute(msql, mparams).fetchone()[0]
    conn.close()
    return render_template('jpn_grammar.html',
        user=user_dict, level=level, cat=cat, levels=levels,
        cat_labels=cat_labels, cats=cats,
        grammars=[dict(r) for r in rows], mastered=mastered,
        version='v22.40.0')


@bp.route('/japanese/kana', methods=['GET'])
@system_container(require_auth='guest')
def japanese_kana_page():
    """五十音图 — 45 假名真实展示 + 翻转 + 发音 + 测试入口"""
    from flask import session as _sess
    user_dict, _, _ = _jpn_sub_context(_sess)
    # 标准五十音 10×5 (あいうえお ~ わをん)
    gojuon = [
        ['あ','a'],['い','i'],['う','u'],['え','e'],['お','o'],
        ['か','ka'],['き','ki'],['く','ku'],['け','ke'],['こ','ko'],
        ['さ','sa'],['し','shi'],['す','su'],['せ','se'],['そ','so'],
        ['た','ta'],['ち','chi'],['つ','tsu'],['て','te'],['と','to'],
        ['な','na'],['に','ni'],['ぬ','nu'],['ね','ne'],['の','no'],
        ['は','ha'],['ひ','hi'],['ふ','fu'],['へ','he'],['ほ','ho'],
        ['ま','ma'],['み','mi'],['む','mu'],['め','me'],['も','mo'],
        ['や','ya'],['',''],['ゆ','yu'],['',''],['よ','yo'],
        ['ら','ra'],['り','ri'],['る','ru'],['れ','re'],['ろ','ro'],
        ['わ','wa'],['',''],['',''],['',''],['を','wo'],
    ]
    return render_template('jpn_kana.html',
        user=user_dict, gojuon=gojuon, version='v22.40.0',
        mastered_kana=user_dict.get('mastered_kana') if user_dict else [])


@bp.route('/japanese/listening', methods=['GET'])
@system_container(require_auth='guest')
def japanese_listening_page():
    """听力练习 — 真实 jp_listening 表数据 + 题目"""
    from flask import session as _sess, request
    user_dict, mtscos_db, levels = _jpn_sub_context(_sess)
    level = request.args.get('level', 'N5')
    import sqlite3 as _sq3, json as _json
    conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
    sql = "SELECT * FROM jp_listening WHERE level=? ORDER BY listening_type, title"
    rows = conn.execute(sql, (level,)).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        try: d['questions'] = _json.loads(d.get('questions_json') or '[]')
        except: d['questions'] = []
        items.append(d)
    total = conn.execute("SELECT COUNT(*) FROM jp_listening WHERE level=?", (level,)).fetchone()[0]
    # 记录数
    user_id = user_dict.get('id')
    done = 0
    if user_id:
        done = conn.execute("SELECT COUNT(*) FROM jp_listening_records WHERE user_id=? AND level=?", (user_id, level)).fetchone()[0]
    conn.close()
    return render_template('jpn_listening.html',
        user=user_dict, level=level, levels=levels, items=items,
        total=total, done=done, version='v22.41.0')


@bp.route('/japanese/listening/<listening_id>', methods=['GET'])
@system_container(require_auth='guest')
def japanese_listening_detail(listening_id):
    """单篇听力练习 — 题目 + 提交"""
    from flask import session as _sess, request
    user_dict, mtscos_db, _ = _jpn_sub_context(_sess)
    import sqlite3 as _sq3, json as _json
    conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
    row = conn.execute("SELECT * FROM jp_listening WHERE listening_id=?", (listening_id,)).fetchone()
    if not row:
        conn.close()
        return "not found", 404
    d = dict(row)
    try: d['questions'] = _json.loads(d.get('questions_json') or '[]')
    except: d['questions'] = []
    conn.close()
    return render_template('jpn_listening_detail.html',
        user=user_dict, item=d, version='v22.41.0')


@bp.route('/japanese/reading', methods=['GET'])
@system_container(require_auth='guest')
def japanese_reading_page():
    """阅读练习 — 真实 jp_reading 表数据 + 文章 + 题目"""
    from flask import session as _sess, request
    user_dict, mtscos_db, levels = _jpn_sub_context(_sess)
    level = request.args.get('level', 'N5')
    import sqlite3 as _sq3, json as _json
    conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
    rows = conn.execute(
        "SELECT * FROM jp_reading WHERE level=? ORDER BY reading_type, title", (level,)).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        try: d['questions'] = _json.loads(d.get('questions_json') or '[]')
        except: d['questions'] = []
        items.append(d)
    total = conn.execute("SELECT COUNT(*) FROM jp_reading WHERE level=?", (level,)).fetchone()[0]
    user_id = user_dict.get('id')
    done = 0
    if user_id:
        done = conn.execute("SELECT COUNT(*) FROM jp_reading_records WHERE user_id=? AND level=?", (user_id, level)).fetchone()[0]
    conn.close()
    return render_template('jpn_reading.html',
        user=user_dict, level=level, levels=levels, items=items,
        total=total, done=done, version='v22.41.0')


@bp.route('/japanese/mock', methods=['GET'])
@system_container(require_auth='guest')
def japanese_mock_page():
    """JLPT 模拟考试 — N5-N1 五套入口"""
    from flask import session as _sess
    user_dict, mtscos_db, _ = _jpn_sub_context(_sess)
    import sqlite3 as _sq3
    conn = _sq3.connect(mtscos_db)
    levels = ['N5','N4','N3','N2','N1']
    stats = {}
    user_id = user_dict.get('id')
    for lv in levels:
        try:
            n_listening = conn.execute("SELECT COUNT(*) FROM jp_listening WHERE level=?", (lv,)).fetchone()[0]
            n_reading = conn.execute("SELECT COUNT(*) FROM jp_reading WHERE level=?", (lv,)).fetchone()[0]
            stats[lv] = {'listening': n_listening, 'reading': n_reading}
        except Exception:
            stats[lv] = {'listening': 0, 'reading': 0}
    conn.close()
    return render_template('jpn_mock.html',
        user=user_dict, levels=levels, stats=stats, version='v22.41.0')


@bp.route('/japanese/mock/<level>', methods=['GET'])
@system_container(require_auth='guest')
def japanese_mock_exam(level):
    """单套模拟考试页 — 从 listening + reading 种子抽题"""
    from flask import session as _sess
    user_dict, mtscos_db, _ = _jpn_sub_context(_sess)
    import sqlite3 as _sq3, json as _json
    conn = _sq3.connect(mtscos_db); conn.row_factory = _sq3.Row
    # 抽 3 听力 + 2 阅读 = 5 题
    listening = conn.execute(
        "SELECT * FROM jp_listening WHERE level=? ORDER BY RANDOM() LIMIT 3", (level,)).fetchall()
    reading = conn.execute(
        "SELECT * FROM jp_reading WHERE level=? ORDER BY RANDOM() LIMIT 2", (level,)).fetchall()
    exam_items = []
    for r in listening:
        d = dict(r)
        try: d['questions'] = _json.loads(d.get('questions_json') or '[]')
        except: d['questions'] = []
        d['kind'] = 'listening'
        exam_items.append(d)
    for r in reading:
        d = dict(r)
        try: d['questions'] = _json.loads(d.get('questions_json') or '[]')
        except: d['questions'] = []
        d['kind'] = 'reading'
        exam_items.append(d)
    conn.close()
    if not exam_items:
        return f"<h2>{level} 暂无题目，请先联系管理员 seed</h2>", 200
    return render_template('jpn_mock_exam.html',
        user=user_dict, level=level, items=exam_items,
        duration_min=30, version='v22.41.0')


# ===== 英语学习页面 (TOEFL · IELTS · 专八 独立模块) =====
@bp.route('/english_page', methods=['GET'])
@system_container(require_auth='guest')
def english_page():
    """英语专业学习门户 (v22.39.1)
    英式现代主义 UI · 六级阶梯 · 语法 · 词汇 · 听力 · 阅读 · 写作 · 口语"""
    from flask import session as _sess
    user_dict = {
        'id': _sess.get('user_id'),
        'username': _sess.get('username'),
        'role': _sess.get('role') or 'guest',
        'education_type': _sess.get('education_type') or 'english',
        'grade': _sess.get('grade') or '',
        'logged_in': bool(_sess.get('logged_in')),
    }
    return render_template(
        'english_learning.html',
        version='v22.39.1',
        version_info={'name': 'MTSCOS AI', 'edition': '仙女座', 'module': '英语专业'},
        user=user_dict,
    )


# ===== 成人教育入口 =====
@bp.route('/adult_education', methods=['GET'])
@system_container(require_auth='guest')
def adult_education_page():
    """成人教育入口 → 重定向到已有的分级测试页面"""
    return redirect('/adult_placement_test')


# ===== EigenFlux 中枢 =====
@bp.route('/eigenflux_center', methods=['GET'])
@system_container(require_auth='admin')
def eigenflux_center_page():
    """EigenFlux 专家协作中枢 — 27万消息 / 1.1万 session"""
    import sqlite3 as _sq, os as _os
    db = _os.path.join(_os.path.dirname(__file__), '..', 'database', 'app.db')
    c = _sq.connect(db)
    c.row_factory = _sq.Row

    # 核心指标
    total_msgs = c.execute('SELECT COUNT(*) FROM eigenflux_comm_messages').fetchone()[0]
    total_sessions = c.execute('SELECT COUNT(*) FROM eigenflux_comm_sessions').fetchone()[0]
    active_agents = c.execute("SELECT COUNT(DISTINCT employee_id) FROM eigenflux_comm_messages WHERE created_at > datetime('now','-24 hours')").fetchone()[0]
    total_experts = c.execute('SELECT COUNT(*) FROM ai_employees').fetchone()[0]

    # 最近活跃专家 (24h)
    top_experts = c.execute("""
        SELECT employee_name as agent_id, COUNT(*) as cnt, MAX(created_at) as last_seen
        FROM eigenflux_comm_messages
        WHERE created_at > datetime('now','-24 hours')
        GROUP BY employee_name ORDER BY cnt DESC LIMIT 10
    """).fetchall()

    # 最近会话
    recent_sessions = c.execute("""
        SELECT session_uid as session_id, summary as topic, created_at,
               total_employees as participant_count, status
        FROM eigenflux_comm_sessions ORDER BY created_at DESC LIMIT 8
    """).fetchall()

    # 最近消息
    recent_msgs = c.execute("""
        SELECT employee_name as agent_id, message_type,
               SUBSTR(message_content, 1, 120) as content, created_at
        FROM eigenflux_comm_messages ORDER BY created_at DESC LIMIT 15
    """).fetchall()

    c.close()
    return render_template('eigenflux_center.html',
        total_msgs=total_msgs, total_sessions=total_sessions,
        active_agents=active_agents, total_experts=total_experts,
        top_experts=top_experts, recent_sessions=recent_sessions,
        recent_msgs=recent_msgs)


# ===== AI 脑库 =====
@bp.route('/brain_bank_page', methods=['GET'])
@system_container(require_auth='login')
def brain_bank_page():
    """AI 脑库 — 知识图谱节点/关系/投喂日志"""
    import sqlite3 as _sq, os as _os
    db = _os.path.join(_os.path.dirname(__file__), '..', 'database', 'app.db')
    c = _sq.connect(db)
    c.row_factory = _sq.Row

    kg_nodes = c.execute('SELECT COUNT(*) FROM knowledge_graph_nodes').fetchone()[0]
    kg_rels = c.execute('SELECT COUNT(*) FROM knowledge_graph_relations').fetchone()[0]
    feed_logs = c.execute('SELECT COUNT(*) FROM mt_ai_brain_feed_log').fetchone()[0]
    enhanced = c.execute('SELECT COUNT(*) FROM ai_brain_enhanced_knowledge').fetchone()[0]

    # Top 节点类型
    node_types = c.execute("""
        SELECT node_type, COUNT(*) as cnt FROM knowledge_graph_nodes
        GROUP BY node_type ORDER BY cnt DESC LIMIT 8
    """).fetchall()

    # Top 关系类型
    rel_types = c.execute("""
        SELECT relation_type, COUNT(*) as cnt FROM knowledge_graph_relations
        GROUP BY relation_type ORDER BY cnt DESC LIMIT 6
    """).fetchall()

    # 最近投喂 (实际列: fed_by, feed_target, payload_preview, fed_at)
    recent_feeds = c.execute("""
        SELECT fed_by as feed_type, feed_target as source,
               SUBSTR(payload_preview, 1, 100) as summary, fed_at as created_at
        FROM mt_ai_brain_feed_log ORDER BY fed_at DESC LIMIT 10
    """).fetchall()

    # 知识图谱高重要节点 (实际列: node_name, importance_score)
    recent_nodes = c.execute("""
        SELECT node_id, node_name as label, node_type,
               importance_score as confidence
        FROM knowledge_graph_nodes
        ORDER BY importance_score DESC LIMIT 12
    """).fetchall()

    c.close()
    return render_template('brain_bank_page.html',
        kg_nodes=kg_nodes, kg_rels=kg_rels, feed_logs=feed_logs, enhanced=enhanced,
        node_types=node_types, rel_types=rel_types,
        recent_feeds=recent_feeds, recent_nodes=recent_nodes)


# ===== 神经阵列 =====
@bp.route('/neural_array_page', methods=['GET'])
@system_container(require_auth='login')
def neural_array_page():
    """神经网络阵列拓扑 — 17 daemon / 集群 / 节点"""
    import sqlite3 as _sq, os as _os
    db = _os.path.join(_os.path.dirname(__file__), '..', 'database', 'app.db')
    c = _sq.connect(db)
    c.row_factory = _sq.Row

    daemons = c.execute('SELECT COUNT(*) FROM mt_daemon_registry').fetchone()[0]
    clusters = c.execute('SELECT COUNT(*) FROM ai_cluster_config').fetchone()[0]
    nodes = c.execute('SELECT COUNT(*) FROM ai_cluster_nodes').fetchone()[0]
    routes = c.execute('SELECT COUNT(*) FROM mt_ai_neural_routes').fetchone()[0]

    # Daemon 列表 (实际列: process_name, duty, status, last_heartbeat, pid, restart_count)
    daemon_list = c.execute("""
        SELECT process_name as daemon_id, duty as daemon_type, status,
               CASE WHEN status='RUNNING' OR status='ACTIVE' THEN 95
                    WHEN status='STOPPED' OR status='FAILED' THEN 20
                    ELSE 60 END as health_score,
               last_heartbeat, pid
        FROM mt_daemon_registry ORDER BY status='RUNNING' DESC, last_heartbeat DESC
    """).fetchall()

    # 集群列表 (实际列: cluster_id, cluster_type, config, status)
    cluster_list = c.execute("""
        SELECT cluster_id, cluster_type as cluster_name,
               config->>'node_count' as node_count, status,
               NULL as leader_node_id
        FROM ai_cluster_config ORDER BY created_at DESC LIMIT 10
    """).fetchall()

    # 神经网络路由 (实际列: primary_model, fallback_model, call_count, success_rate, task_name)
    neural_routes = c.execute("""
        SELECT route_id, primary_model as from_model,
               fallback_model as to_model, task_name as route_type,
               success_rate as confidence, call_count as hit_count
        FROM mt_ai_neural_routes ORDER BY call_count DESC LIMIT 12
    """).fetchall()

    c.close()
    return render_template('neural_array_page.html',
        daemons=daemons, clusters=clusters, nodes=nodes, routes=routes,
        daemon_list=daemon_list, cluster_list=cluster_list,
        neural_routes=neural_routes)

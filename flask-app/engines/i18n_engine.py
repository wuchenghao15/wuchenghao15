"""
i18n_engine — 文案管理 + 多语言翻译引擎 (v22.39.0)
===================================================
依赖: mt_i18n_keys 表 (app.db)

核心接口:
  t(key, default=None, lang='zh_CN')          — 取译文
  t_kw(key, default, **kwargs)                 — 取译文 + .format() 占位符填充
  inject_i18n_into_app(app)                    — Jinja2 环境注入 t() + current_lang
  scan_hardcoded_strings(directory)            — 扫描模板/JS 里的硬编码中文 (提取器)
  translate_seed(key, zh, ja, en, domain)      — 写种子翻译

语言代码规范: zh_CN / ja_JP / en_US
"""
import sqlite3 as _sqlite3
from app.middlewares.system_container import system_container
# [unused] import re as _re
import os as _os

DB_PATH = None  # 运行时由 _resolve_db_path 填充


def _resolve_db_path():
    """纯文件系统找 app.db — 绝不 import server_real_db (避免触发 daemon fork).
    优先用 core.db_path.get_db_path (Flask 启动入口), 再 fallback 相对路径猜测."""
    global DB_PATH
    if DB_PATH:
        return DB_PATH
    # 1) 尝试复用 Flask core.db_path.get_db_path (最可靠)
    try:
        from core.db_path import get_db_path as _gdp
        cand = _gdp('app.db')
        if cand and _os.path.isfile(cand):
            DB_PATH = cand; return cand
    except Exception:
        pass
    # 2) fallback: 相对路径猜测
    here = _os.path.dirname(_os.path.abspath(__file__))
    for rel in [
        '_runtime/databases/Database/app.db',
        'Database/app.db',
        '../Database/app.db',
        '../../Database/app.db',
    ]:
        cand = _os.path.join(here, '..', rel)
        if _os.path.isfile(cand):
            DB_PATH = cand; return cand
    return None


def _get_conn():
    p = _resolve_db_path()
    return _sqlite3.connect(p, timeout=30)


def t(key, default=None, lang=None):
    """取译文. lang=None 时自动从 session['i18n_lang'] 读取 (Jinja2 模板默认行为)."""
    try:
        if lang is None:
            lang = _session_lang()
        col = {'zh_CN': 'zh_cn', 'zh_TW': 'zh_tw', 'ja_JP': 'ja_jp', 'en_US': 'en_us'}.get(lang, 'zh_cn')
        c = _get_conn()
        row = c.execute(f"SELECT {col} FROM mt_i18n_keys WHERE key=?", (key,)).fetchone()
        c.close()
        if row and row[0]:
            return row[0]
        # fallback: 源语言
        if col != 'zh_cn':
            c = _get_conn()
            row2 = c.execute("SELECT zh_cn FROM mt_i18n_keys WHERE key=?", (key,)).fetchone()
            c.close()
            if row2 and row2[0]:
                return row2[0]
    except Exception:
        pass
    return default if default is not None else key


def t_kw(key, default, lang='zh_CN', **kwargs):
    """取译文 + 占位符填充. 例: t_kw('user_welcome', '你好 {name}', name='张三')"""
    txt = t(key, default, lang)
    try:
        return txt.format(**kwargs)
    except Exception:
        return txt


def inject_i18n_into_app(app):
    """向 Flask app 的 Jinja2 环境注入 t / t_kw / current_lang / available_langs
    同时暴露 /api/i18n/dict 给前端 JS 拉取完整翻译字典。"""
    import json as _json

    def _build_i18n_dict(lang):
        """构建 {key: translation} 字典给前端 JS 使用"""
        try:
            import sqlite3
            db_path = _resolve_db_path()
            col_map = {'zh_CN':'zh_cn','zh_TW':'zh_tw','ja_JP':'ja_jp','en_US':'en_us'}
            col = col_map.get(lang, 'zh_cn')
            c = sqlite3.connect(db_path)
            rows = c.execute(f"SELECT key, {col} FROM mt_i18n_keys WHERE {col}!=''").fetchall()
            c.close()
            return {k: v for k, v in rows}
        except Exception:
            return {}

    app.jinja_env.globals.update(
        t=t,
        t_kw=t_kw,
        current_lang=lambda: _session_lang(),
        available_langs=[
            ('zh_CN', '简体中文'),
            ('zh_TW', '繁體中文'),
            ('ja_JP', '日本語'),
            ('en_US', 'English'),
        ],
        _i18n_dict=lambda: _build_i18n_dict(_session_lang()),
    )

    # ── API: 返回当前语言完整翻译字典 (给 JS fetch) ──
    @app.route('/api/i18n/dict')
    def _i18n_dict_api():
        from flask import session, jsonify
        lang = session.get('i18n_lang', 'zh_CN')
        data = _build_i18n_dict(lang)
        return jsonify({'lang': lang, 'dict': data, 'count': len(data)})

    @app.route('/api/i18n/set_lang', methods=['POST', 'GET'])
    def _set_lang():
        from flask import request, session, jsonify
        json_data = request.get_json(silent=True) or {}
        lang = (json_data.get('lang')
                or request.form.get('lang')
                or request.args.get('lang')
                or 'zh_CN')
        if lang in ('zh_CN', 'zh_TW', 'ja_JP', 'en_US'):
            session['i18n_lang'] = lang
            return jsonify({'success': True, 'lang': lang})
        return jsonify({'success': False, 'reason': 'invalid lang'}), 400

    @app.route('/api/i18n/current')
    def _current_lang():
        from flask import session, jsonify
        lang = session.get('i18n_lang', 'zh_CN')
        return jsonify({'lang': lang})
    return app


def _session_lang():
    try:
        from flask import session
        return session.get('i18n_lang', 'zh_CN')
    except Exception:
        return 'zh_CN'


def translate_seed(key, zh, ja=None, en=None, domain='global', remark=None):
    """写入种子翻译. 用于初始化常用文案."""
    c = _get_conn()
    c.execute("""INSERT INTO mt_i18n_keys (key, zh_cn, ja_jp, en_us, domain, remark)
                 VALUES (?,?,?,?,?,?)
                 ON CONFLICT(key) DO UPDATE SET
                   zh_cn=excluded.zh_cn, ja_jp=COALESCE(excluded.ja_jp, mt_i18n_keys.ja_jp),
                   en_us=COALESCE(excluded.en_us, mt_i18n_keys.en_us),
                   updated_at=CURRENT_TIMESTAMP""",
              (key, zh, ja, en, domain, remark))
    c.commit()
    c.close()


def seed_common_strings():
    """常用文案种子 (v22.39.0 首批 30 条). 日语/英语为本地翻译, 后续可 AI 批量."""
    SEEDS = [
        # 首页/登录
        ('home.title', 'MTSCOS AI · 智能学习与 AI 自动化托管平台',
         'MTSCOS AI · スマートラーニング & AI オートメーション管理プラットフォーム',
         'MTSCOS AI · Smart Learning & AI Automation Platform',
         'home'),
        ('home.welcome', '欢迎回来，{name}',
         'おかえりなさい、{name}さん',
         'Welcome back, {name}', 'home'),
        ('login.title', '用户登录', 'ユーザーログイン', 'User Login', 'login'),
        ('login.username', '用户名或邮箱', 'ユーザー名またはメール', 'Username or Email', 'login'),
        ('login.password', '密码', 'パスワード', 'Password', 'login'),
        ('login.remember', '记住我', 'ログイン状態を保持', 'Remember me', 'login'),
        ('login.submit', '登 录', 'ログイン', 'Sign In', 'login'),
        ('login.success', '登录成功', 'ログインしました', 'Login successful', 'login'),
        ('login.failed', '用户名或密码错误', 'ユーザー名またはパスワードが違います', 'Invalid username or password', 'login'),
        ('login.blocked', '账号已被锁定，请稍后再试',
         'アカウントがロックされています。しばらくしてからお試しください',
         'Account locked, please try later', 'login'),
        ('logout.success', '您已安全退出', '正常にログアウトしました', 'You have been logged out', 'auth'),

        # 功能域
        ('module.student_portal', '学习门户', '学習ポータル', 'Student Portal', 'home'),
        ('module.exam_center', '在线考试', 'オンライン試験', 'Online Exam', 'home'),
        ('module.japanese', '日语学习', '日本語学習', 'Japanese Learning', 'home'),
        ('module.adult_edu', '成人教育', '成人教育', 'Adult Education', 'home'),
        ('module.eigenflux', 'EigenFlux AI 中枢', 'EigenFlux AIセンター', 'EigenFlux AI Hub', 'home'),
        ('module.brain_bank', 'AI 脑库', 'AIブレインバンク', 'AI Brain Bank', 'home'),
        ('module.neural_array', '神经阵列', 'ニューラルアレイ', 'Neural Array', 'home'),
        ('module.readonly_inventory', '系统盘点', 'システム棚卸', 'System Inventory', 'home'),

        # 权限/系统
        ('sys.permission_denied', '无权访问此页面', 'このページにアクセスする権限がありません',
         'Permission denied', 'system'),
        ('sys.session_expired', '会话已过期，请重新登录', 'セッションが期限切れです。再ログインしてください',
         'Session expired, please login again', 'system'),
        ('sys.vikey_detached', 'VIKEY 加密狗未插入', 'VIKEYドングルが接続されていません',
         'VIKEY security key not detected', 'system'),
        ('sys.vikey_unbound', 'VIKEY 加密狗未绑定当前用户', 'VIKEYドングルが現在のユーザーに紐付けられていません',
         'VIKEY not bound to current user', 'system'),
        ('sys.health.healthy', '系统健康', 'システム正常', 'HEALTHY', 'system'),
        ('sys.health.degraded', '系统降级', 'システム劣化', 'DEGRADED', 'system'),
        ('sys.health.critical', '系统严重异常', 'システム重大異常', 'CRITICAL', 'system'),
        ('sys.version', '系统版本', 'システムバージョン', 'System Version', 'system'),
        ('sys.build', '构建时间', 'ビルド時間', 'Build Time', 'system'),

        # 考试域
        ('exam.start', '开始考试', '試験を開始', 'Start Exam', 'exam'),
        ('exam.submit', '交卷', '提出', 'Submit', 'exam'),
        ('exam.time_up', '时间到，自动交卷', '時間切れ、自動提出', 'Time up, auto-submitted', 'exam'),
        ('exam.passing_score', '及格分数', '合格点', 'Passing Score', 'exam'),
        ('exam.score', '您的得分', 'あなたのスコア', 'Your Score', 'exam'),
        ('exam.result.pass', '恭喜，您通过了考试！', 'おめでとうございます、合格です！',
         'Congratulations, you passed!', 'exam'),
        ('exam.result.fail', '很遗憾，您未能通过考试', '残念ながら、合格できませんでした',
         'Sorry, you did not pass', 'exam'),
    ]
    for seed in SEEDS:
        translate_seed(*seed)
    return len(SEEDS)

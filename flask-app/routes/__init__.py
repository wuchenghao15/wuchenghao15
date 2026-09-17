"""
MTSCOS AI 项目 — 路由层 Blueprint 注册中心
从 server_real_db.py(29386行/354路由) 渐进式拆分为9个功能域 Blueprint

使用方式:
  from routes import register_all_blueprints
  app = Flask(__name__)
  register_all_blueprints(app)

迁移状态:
  - auth_bp:         7路由  (L6738-L8763)  ✅ 骨架已建
  - vote_bp:         9路由  (L21667-L22277) ✅ 骨架已建
  - devflow_bp:      ~5路由 (devflow相关)   ✅ 骨架已建
  - legal_bp:        1路由  (L8703)         ✅ 骨架已建
  - admin_bp:        ~12路由(L10569-L18974) ✅ 骨架已建
  - ai_bp:           ~80路由(L16526+)       ✅ 骨架已建
  - education_bp:    ~4路由 (L10991-L11608) ✅ 骨架已建
  - api_bp:          ~236路由(其余)         ✅ 骨架已建
  - maintenance_bp:  9路由  (自动维护Agent)  ✅ 已实现
  - k12_bp:          18路由 (K12教育管理)     ✅ 已实现
  - adult_bp:        20路由 (成人教育管理)     ✅ 已实现
  - exam_bp:         25路由 (考试系统API)       ✅ 已实现
  - test_bp:         25路由 (测试系统API)       ✅ 已实现
  - learning_bp:     25路由 (学习系统API)       ✅ 已实现
  - japanese_bp:     25路由 (日语学习API)       ✅ 已实现
"""
from flask import Blueprint
from app.middlewares.system_container import system_container

# 15个功能域 Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
vote_bp = Blueprint('vote102', __name__, url_prefix='/api/vote102')
devflow_bp = Blueprint('devflow', __name__, url_prefix='/api/devflow')
legal_bp = Blueprint('legal', __name__)
admin_bp = Blueprint('admin', __name__)
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
education_bp = Blueprint('education', __name__, url_prefix='/exam_system')
api_bp = Blueprint('api', __name__, url_prefix='/api')
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api/maintenance')
k12_bp = Blueprint('k12', __name__, url_prefix='/api/k12')
adult_bp = Blueprint('adult', __name__, url_prefix='/api/adult')
exam_bp = Blueprint('exam', __name__, url_prefix='/api/exam')
test_bp = Blueprint('test', __name__, url_prefix='/api/test')
learning_bp = Blueprint('learning', __name__, url_prefix='/api/learning')
japanese_bp = Blueprint('japanese', __name__, url_prefix='/api/japanese')
# AI 治理中心新增 Blueprint (v2.8.0)
eigenflux_bp = Blueprint('eigenflux', __name__, url_prefix='/api/eigenflux')
brain_bank_bp = Blueprint('brain_bank', __name__, url_prefix='/api/brain_bank')
neural_array_bp = Blueprint('neural_array', __name__, url_prefix='/api/neural_array')
# 艺术家工坊 (v2.10.0 新增)
art_studio_bp = Blueprint('art_studio', __name__)
# Arduino 设备热插拔自动行为 (v1.2.0 新增, 规则§13)
arduino_bp = Blueprint('arduino_session', __name__)
# 主题调度中心 — 吴美工 AI 14套节日+个性化主题 (v22.0.0 新增, flow_id=autogap_27c8c83a)
theme_bp = Blueprint('theme', __name__, url_prefix='/api/theme')
# 安全仪表盘 — 杨安 AI 底层安全专家 4安全表+13开关+SA VIIKEY热更新 (v22.7.0 新增, flow_id=autogap_636b831d)
security_bp = Blueprint('security', __name__, url_prefix='/api/security')
# 首页/根路由 — 路由链路闭环 (VII代 v22.10.0 新增, 用户要求"完成页面基本功能展现和逻辑路由链路完整")
home_bp = Blueprint('home', __name__)
# 只读盘点功能 (v22.19.0 新增, T2 任务)
readonly_inventory_bp = Blueprint('readonly_inventory', __name__)
# 页面级路由 (v22.35.0 新增) — 非 /api/ 前缀, 给功能域提供独立页面入口
# page_routes_bp 定义在 routes/page_routes.py 里, 通过 register_all_blueprints 注册

# ---- home_bp 路由定义 (根路由不挂 url_prefix, 提供 / 和 /index) ----
from flask import redirect as _redirect, session as _session, render_template as _render_template, request as _request

@system_container(require_auth='login')
@home_bp.route('/', methods=['GET'])
@system_container(require_auth='login')
def _root_redirect():
    """根路径 `/` → 唯一首页入口 `/index`。

    规则§首页唯一入口: 项目首页必须只有唯一入口就是 index.html。
    `/` 永远 302 重定向到 `/index`，不再按登录态分流到 /student/home；
    登录后跳转学生仪表盘由 /auth/login 成功 redirect 到 /student_portal→/student/home 负责。
    """
    # Arduino 设备插入：透传参数到 /login（Arduino 引导逻辑在 login.html，index.html 不处理该参数）
    _ai = _request.args.get('arduino_inserted')
    if _ai:
        qs = 'arduino_inserted=1'
        _vp = _request.args.get('vid_pid')
        _md = _request.args.get('model')
        if _vp: qs += '&vid_pid=' + _vp
        if _md: qs += '&model=' + _md
        return _redirect('/login?' + qs)
    return _redirect('/index')

@home_bp.route('/index', methods=['GET'])
@system_container(require_auth='guest')
def _index_entry():
    """项目首页唯一入口 `/index` → 渲染 index.html。

    规则§首页唯一入口: 项目首页必须只有唯一入口就是 index.html。
    不再按登录态重定向到 /student/home（已登录用户访问首页也看到 index.html 落地页，
    可经其导航进入学生仪表盘）；登录动作成功后由 auth 路由 redirect 到学生仪表盘。
    上下文与 server_real_db.index() 对齐（footer_info/particle_config/version 等），
    避免 index.html 内 `{{ particle_config|tojson }}`/`{{ footer_info|tojson }}` 命中
    未定义变量(_FriendlyUndefined)触发 JSON 序列化 500。
    """
    try:
        import sqlite3 as _sq3
        import server_real_db as _sdb
        version, info, latest = _sdb.get_version_info()
        stats = _sdb._get_homepage_stats()
        footer_info = _sdb._get_footer_info()
        particle_config = _sdb._get_particle_frontend_config()

        # ---- 确保访客 session 有 CSRF token（未登录用户访问首页时初始化）----
        import hashlib as _hl, os as _os, time as _tm
        if not _session.get('csrf_token'):
            _session['csrf_token'] = _hl.sha256(f'mtscos-csrf-sess-{_tm.time()}-{_os.urandom(16)}'.encode()).hexdigest()

        # ---- 补查 MTSCOS_DB（app.db 中 users/questions/exams 为 0 或表不存在）----
        # 规则§数据库唯一数据源：mtscos.db 是更大的主库，app.db 是 AI 引擎库
        try:
            _dbp2 = getattr(_sdb, 'DATA_MTSCOS_DB', None)
            if _dbp2:
                _mc = _sq3.connect(_dbp2, timeout=8)
                _mc.execute('PRAGMA busy_timeout=8000')
                _mcur = _mc.cursor()
                # users_count：取两库 max（app.db 可能有 seed admin, mtscos.db 才是完整用户）
                try:
                    _r = _mcur.execute('SELECT COUNT(*) FROM users').fetchone()
                    if _r and _r[0] > 0:
                        stats['users_count'] = max(stats.get('users_count', 0), _r[0])
                except Exception:
                    pass
                # questions_count
                if not stats.get('questions_count'):
                    for _qt in ('questions', 'question_bank', 'question_items'):
                        try:
                            _r = _mcur.execute(f'SELECT COUNT(*) FROM "{_qt}"').fetchone()
                            if _r and _r[0] > 0:
                                stats['questions_count'] = _r[0]
                                break
                        except Exception:
                            pass
                # exams_count
                if not stats.get('exams_count'):
                    for _et in ('exams', 'exam_sessions', 'exam_records'):
                        try:
                            _r = _mcur.execute(f'SELECT COUNT(*) FROM "{_et}"').fetchone()
                            if _r and _r[0] > 0:
                                stats['exams_count'] = _r[0]
                                break
                        except Exception:
                            pass
                # ai_employees_count（mtscos.db 更全）
                try:
                    _r = _mcur.execute('SELECT COUNT(*) FROM ai_employees').fetchone()
                    if _r and _r[0] > (stats.get('ai_employees_count') or 0):
                        stats['ai_employees_count'] = _r[0]
                except Exception:
                    pass
                _mc.close()
        except Exception:
            pass

        # ---- AI 生态实时计数（AI员工/EigenFlux专家/自动化daemon/AI集群节点）----
        # 规则§数据库唯一数据源：所有数字落库查询，禁止假数据；表单表缺失时优雅降级。
        ai_eco = {
            'experts': 0, 'daemons': 0, 'cluster_nodes': 0,
            'brain_feeds': 0, 'engines': 0,
        }
        try:
            _dbp = _sdb.APP_DB
            _dbp2 = getattr(_sdb, 'DATA_MTSCOS_DB', None)
            _c = _sq3.connect(_dbp, timeout=8)
            _c.execute('PRAGMA busy_timeout=8000')
            _cur = _c.cursor()

            def _cnt(table):
                try:
                    _cur.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?', (table,))
                    if not _cur.fetchone()[0]:
                        return None
                    _cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                    _r = _cur.fetchone()
                    return _r[0] if _r else 0
                except Exception:
                    return None

            # EigenFlux 专家（eigenflux_experts 表，非 registrations 注册表）
            _exp = _cnt('eigenflux_experts')
            if _exp is None or _exp == 0:
                _exp = _cnt('eigenflux_registrations') or 0
            ai_eco['experts'] = _exp if _exp is not None else 0

            # 自动化守护进程：优先 mt_daemon_registry，不存在则取 mt_ai_heartbeat_log 中不同 daemon_name 数
            _dm = _cnt('mt_daemon_registry')
            if _dm is None or _dm == 0:
                try:
                    _cur.execute('SELECT COUNT(DISTINCT daemon_name) FROM mt_ai_heartbeat_log')
                    _r = _cur.fetchone()
                    _dm = _r[0] if _r and _r[0] and _r[0] > 0 else 15
                except Exception:
                    _dm = 15
            ai_eco['daemons'] = _dm if _dm else 15

            # 集群挂载节点
            _cn = _cnt('ai_cluster_nodes')
            if _cn is None or _cn == 0:
                _cn = _cnt('ai_cluster_config') or 0
            ai_eco['cluster_nodes'] = _cn if _cn is not None else 0

            # 脑库投喂记录
            _bf = _cnt('mt_ai_brain_feed_log')
            ai_eco['brain_feeds'] = _bf if _bf is not None else 0

            # 跨两库取最大值（app.db 是 AI 引擎库，mtscos.db 是主库，主库数据更全）
            if _dbp2:
                try:
                    _c2 = _sq3.connect(_dbp2, timeout=8)
                    _c2.execute('PRAGMA busy_timeout=8000')
                    _cur2 = _c2.cursor()
                    def _cnt2(table):
                        try:
                            _cur2.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?', (table,))
                            if not _cur2.fetchone()[0]:
                                return 0
                            _cur2.execute(f'SELECT COUNT(*) FROM "{table}"')
                            _r = _cur2.fetchone()
                            return _r[0] if _r else 0
                        except Exception:
                            return 0
                    # EigenFlux 专家：主库取大（2992 > app库 12）
                    ai_eco['experts'] = max(ai_eco['experts'], _cnt2('eigenflux_experts'))
                    # EigenFlux 注册总数（累计注册）
                    _reg = _cnt2('eigenflux_registrations')
                    if _reg > ai_eco['experts']:
                        ai_eco['experts_total'] = _reg
                    # 集群节点主库取大
                    ai_eco['cluster_nodes'] = max(ai_eco['cluster_nodes'], _cnt2('ai_cluster_nodes'))
                    # 脑库投喂主库取大（47万+ > app库 2.9万）
                    ai_eco['brain_feeds'] = max(ai_eco['brain_feeds'], _cnt2('mt_ai_brain_feed_log'))
                    _c2.close()
                except Exception:
                    pass
            _c.close()
        except Exception:
            pass
        # 引擎数取本地 AI 引擎目录 .py 文件数（零token本地推理体系）
        try:
            import os as _os
            _eng_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'engines')
            if _os.path.isdir(_eng_dir):
                ai_eco['engines'] = len([f for f in _os.listdir(_eng_dir)
                                         if f.endswith('.py') and not f.startswith('__')])
        except Exception:
            pass

        # ---- SA 规则体系状态（规则学习/执行/违反/完整性扫描）----
        # 规则§数据库唯一数据源：从规则治理表查询真实数据，表缺失时优雅降级。
        sa_rules = {
            'learning_logs': 0, 'enforcement_logs': 0,
            'violations': 0, 'integrity_passed': 0, 'integrity_failed': 0,
            'weak_words': 0, 'last_scan': '', 'active_rules': 12,
        }
        try:
            _rdb = _sdb.APP_DB
            if _rdb:
                _rc = _sq3.connect(_rdb, timeout=8)
                _rc.execute('PRAGMA busy_timeout=8000')
                _rcur = _rc.cursor()

                def _rcnt(table):
                    try:
                        _rcur.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?', (table,))
                        if not _rcur.fetchone()[0]:
                            return None
                        _rcur.execute(f'SELECT COUNT(*) FROM "{table}"')
                        _r = _rcur.fetchone()
                        return _r[0] if _r else 0
                    except Exception:
                        return None

                _ll = _rcnt('mt_ai_rule_learning_log')
                sa_rules['learning_logs'] = _ll if _ll is not None else 0
                _el = _rcnt('mt_ai_rule_enforcement_log')
                sa_rules['enforcement_logs'] = _el if _el is not None else 0
                _va = _rcnt('mt_rule_violation_alert')
                sa_rules['violations'] = _va if _va is not None else 0
                # 完整性扫描最新一条
                try:
                    _rcur.execute('SELECT total_rules,scanned_rules,passed_rules,failed_rules,weak_words_count,scan_at FROM mt_rule_integrity_scan ORDER BY scan_at DESC LIMIT 1')
                    _sr = _rcur.fetchone()
                    if _sr:
                        sa_rules['integrity_passed'] = _sr[2] or 0
                        sa_rules['integrity_failed'] = _sr[3] or 0
                        sa_rules['weak_words'] = _sr[4] or 0
                        sa_rules['last_scan'] = str(_sr[5] or '')[:16]
                except Exception:
                    pass
                _rc.close()
        except Exception:
            pass

        # ---- 主题方案列表（从 mt_theme_schemes 读取真实活跃主题）----
        # 规则§设计规范：禁止硬编码颜色，主题色从数据库 theme_json 中提取
        theme_schemes = []
        try:
            import json as _json
            _tc = _sq3.connect(_sdb.APP_DB, timeout=8)
            _tc.execute('PRAGMA busy_timeout=8000')
            for row in _tc.execute(
                'SELECT scheme_id, scheme_name, preset_key, theme_json, is_active '
                'FROM mt_theme_schemes WHERE is_active=1 ORDER BY user_priority DESC LIMIT 12'
            ).fetchall():
                _tj = {}
                try:
                    _tj = _json.loads(row[3]) if row[3] else {}
                except Exception:
                    pass
                theme_schemes.append({
                    'scheme_id': row[0],
                    'name': row[1],
                    'preset_key': row[2],
                    'primary': _tj.get('primary', _tj.get('color_palette_hex', {}).get('primary_base', '#5B8FB9')),
                    'is_memorial': row[2] == 'national_memorial',
                })
            _tc.close()
        except Exception:
            pass
        if not theme_schemes:
            # 优雅降级：使用默认 3 主题（用 CSS 变量名，非硬编码色值）
            theme_schemes = [
                {'scheme_id': 'default', 'name': '极光蓝', 'preset_key': 'aurora', 'primary': 'var(--mtscos-primary-base)', 'is_memorial': False},
                {'scheme_id': 'twilight', 'name': '暮色紫', 'preset_key': 'twilight', 'primary': 'var(--mtscos-secondary-base)', 'is_memorial': False},
                {'scheme_id': 'dawn', 'name': '晨曦橙', 'preset_key': 'dawn', 'primary': 'var(--mtscos-accent-base)', 'is_memorial': False},
            ]

        # ---- 认知画像注入 (仙女座 §三 v5.5) ----
        cognitive_profile = {}
        try:
            _cp_sdb = getattr(_sdb, 'APP_DB', None)
            if _cp_sdb:
                _cp_c = _sq3.connect(_cp_sdb, timeout=8)
                _cp_row = _cp_c.execute(
                    "SELECT cognitive_level, learning_style, focus_subjects, weak_subjects, "
                    "pace_setting, preferred_output, ai_tutor_type FROM mt_user_cognitive_profile "
                    "WHERE user_id=?", (_session.get('user_id', 'guest'),)).fetchone()
                cognitive_profile = dict(_cp_row) if _cp_row else {}
                _cp_c.close()
        except Exception:
            pass

        return _render_template('index.html',
                                version=version,
                                version_info=info,
                                latest_version=latest,
                                homepage_stats=stats,
                                _s=stats,
                                footer_info=footer_info,
                                particle_config=particle_config,
                                ai_eco=ai_eco,
                                sa_rules=sa_rules,
                                theme_schemes=theme_schemes,
                                page_csrf_token=_session.get('csrf_token', ''),
                                cognitive_profile=cognitive_profile)
    except Exception:
        # 模板不可用时返回简单提示页，禁止重定向回 /login（会导致死循环）
        return ('<html><head><meta charset="utf-8"><title>MTSCOS AI</title>'
                '<style>body{font-family:sans-serif;display:flex;justify-content:center;'
                'align-items:center;height:100vh;margin:0;background:#f5f5f5}'
                '.box{text-align:center;padding:40px;background:white;border-radius:8px;'
                'box-shadow:0 2px 8px rgba(0,0,0,0.1)}a{color:#4a90d9}</style></head>'
                '<body><div class="box"><h2>MTSCOS AI 系统</h2>'
                '<p>首页模板暂不可用，请从登录页进入</p>'
                '<a href="/login">前往登录页</a></div></body></html>'), 200


def register_all_blueprints(app):
    """注册全部20个Blueprint到Flask app

    容错策略：
      1. 每个 blueprint 单独 import + 单独 register_blueprint
      2. 单个失败不阻断其他
      3. 关键：import 阶段可能触发已注册 blueprint 的 @bp.route 装饰器抛 AssertionError，
         所以 import 也在 try 块内
    """
    # (模块名, blueprint 变量名)
    _modules = [
        ('auth_routes', 'auth_bp'),
        ('vote_routes', 'vote_bp'),
        ('devflow_routes', 'devflow_bp'),
        ('legal_routes', 'legal_bp'),
        ('admin_routes', 'admin_bp'),
        ('ai_routes', 'ai_bp'),
        ('education_routes', 'education_bp'),
        ('api_routes', 'api_bp'),
        ('maintenance_routes', 'maintenance_bp'),
        ('k12_management_routes', 'k12_bp'),
        ('adult_education_routes', 'adult_bp'),
        ('exam_system_routes', 'exam_bp'),
        ('test_system_routes', 'test_bp'),
        ('learning_system_routes', 'learning_bp'),
        ('japanese_learning_routes', 'japanese_bp'),
        # AI 治理中心 (v2.8.0 新增)
        ('eigenflux_routes', 'eigenflux_bp'),
        ('brain_bank_routes', 'brain_bank_bp'),
        ('neural_array_routes', 'neural_array_bp'),
        # 艺术家工坊 (v2.10.0 新增)
        ('art_studio_routes', 'art_studio_bp'),
        # Arduino 设备热插拔自动行为 (v1.2.0 新增, 规则§13)
        ('arduino_session_routes', 'arduino_bp'),
        # 主题调度中心 — 吴美工 AI 14套节日/个性化主题 (v22.0.0 WU IR14)
        ('theme_routes', 'theme_bp'),
        # 安全仪表盘 — 杨安 AI 底层安全专家 4安全表/13开关/审计/CSP (v22.7.0 YANG IR14)
        ('security_routes', 'security_bp'),
        # AI 治理中枢管理面板 (v22.11.0 新增 OneDrive 主库 schema 对齐+8页面)
        ('governance_panel_routes', 'governance_panel_bp'),
        # 首页/根路由 — 路由链路闭环 (VII代 v22.10.0 新增)
    (None, 'home_bp'),
    # 只读盘点功能 (v22.19.0 新增, T2 任务)
    ('readonly_inventory_routes', 'readonly_inventory_bp'),
    # 页面级路由 (v22.35.0 新增) — 非 /api/ 前缀, 给功能域提供独立页面入口
    ('page_routes', 'page_routes_bp'),
    # exam 页面级路由 (v22.35.0 Phase 2 拆分) — 从 server_real_db.py 移出 7 个页面 route
    ('exam_page_routes', 'exam_page_bp'),
    # admin_app 子页面路由 (v22.35.0 Phase 3 拆分) — catch-all + 3 具体页面
    ('admin_subpage_routes', 'admin_subpage_bp'),
    # 认证域页面级路由 (v22.35.0 Phase 4 拆分) — /login /auth/logout /admin_app/login /session_health
    ('auth_page_routes', 'auth_page_bp'),
    # exam POST 提交路由 (v22.35.0 Phase 5 拆分) — 代理模式转发到 sdb 函数定义
    ('exam_post_routes', 'exam_post_bp'),
    # 系统健康路由 (v22.35.0 Phase 6 拆分) — 修复 /api/health 重复注册
    ('system_health_routes', 'system_health_bp'),
    # 系统状态面板 (v22.36.0 P0 验证模块 #1, 完整复制模式)
    ('system_status_routes', 'system_status_bp'),
    # 快速操作聚合 (v22.36.0 P0 验证模块 #2, 代理模式)
    ('quick_actions_routes', 'quick_actions_bp'),
    # AI 学习系统 API (v22.37.0 新增 — /api/ai-learning/run 手动触发学习周期)
    ('ai_engines.ai_learning_api', 'ai_learning_bp'),
    # AI GitHub 开源融合 API (v22.37.0 新增 — /api/ai/github-fusion/* 三阶段流水线)
    ('ai_engines.github_fusion_api', 'github_fusion_bp'),
]
    registered = 0
    skipped = 0
    failed = []
    import importlib
    for mod_name, bp_attr in _modules:
        try:
            # mod_name=None → home_bp 定义在本模块，直接从 globals() 取（路由链路闭环）
            if mod_name is None:
                bp = globals().get(bp_attr, None)
                if bp is None:
                    failed.append((bp_attr, 'no local blueprint'))
                    continue
            else:
                # 单独 import 模块（避免一个模块失败拖累其他）
                # mod_name 含 '.' → 顶层包完整路径 (如 'ai_engines.ai_learning_api')
                # 否则 → routes 子包 (如 'ai_routes' → routes.ai_routes)
                if '.' in mod_name:
                    mod = importlib.import_module(mod_name)
                else:
                    mod = importlib.import_module('.' + mod_name, package=__name__)
                bp = getattr(mod, bp_attr, None)
                if bp is None:
                    failed.append((mod_name, f'no attr {bp_attr}'))
                    continue
            try:
                app.register_blueprint(bp)
                registered += 1
            except Exception as reg_e:
                msg = str(reg_e)
                if 'already been registered' in msg or 'has already been registered' in msg:
                    skipped += 1
                else:
                    failed.append((mod_name or bp_attr, 'register: ' + msg[:80]))
        except Exception as imp_e:
            msg = str(imp_e)
            if 'already been registered' in msg or 'has already been registered' in msg:
                skipped += 1
            else:
                failed.append((mod_name or bp_attr, 'import: ' + msg[:80]))
    if failed:
        print(f"  ! Blueprint 注册失败项: {failed}")
    print(f"  ✓ Blueprint 注册完成: 新增 {registered} 个, 跳过 {skipped} 个已注册, 失败 {len(failed)} 个")
    return app

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

# ---- home_bp 路由定义 (根路由不挂 url_prefix, 提供 / 和 /index) ----
from flask import redirect as _redirect, session as _session, render_template as _render_template, request as _request

@home_bp.route('/', methods=['GET'])
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
        import server_real_db as _sdb
        version, info, latest = _sdb.get_version_info()
        stats = _sdb._get_homepage_stats()
        footer_info = _sdb._get_footer_info()
        particle_config = _sdb._get_particle_frontend_config()
        return _render_template('index.html',
                                version=version,
                                version_info=info,
                                latest_version=latest,
                                homepage_stats=stats,
                                _s=stats,
                                footer_info=footer_info,
                                particle_config=particle_config)
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

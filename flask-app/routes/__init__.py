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


def register_all_blueprints(app):
    """注册全部18个Blueprint到Flask app

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
    ]
    registered = 0
    skipped = 0
    failed = []
    import importlib
    for mod_name, bp_attr in _modules:
        try:
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
                    failed.append((mod_name, 'register: ' + msg[:80]))
        except Exception as imp_e:
            msg = str(imp_e)
            if 'already been registered' in msg or 'has already been registered' in msg:
                skipped += 1
            else:
                failed.append((mod_name, 'import: ' + msg[:80]))
    if failed:
        print(f"  ! Blueprint 注册失败项: {failed}")
    print(f"  ✓ Blueprint 注册完成: 新增 {registered} 个, 跳过 {skipped} 个已注册, 失败 {len(failed)} 个")
    return app

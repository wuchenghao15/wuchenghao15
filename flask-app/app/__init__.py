"""app 包兼容层 — 把 app.* 导入重导出到 ai_engines 已有模块.
修复42个孤儿模块的 ImportError (12步流程 SYS-NORM)."""
import os, sys, sqlite3, logging
from pathlib import Path

# 尝试导入统一权限中间件，若不存在则使用空实现
try:
    from .unified_permission import unified_permission
except Exception:
    def unified_permission():
        """空实现，确保中间件可调用."""
        return None

_BASE = Path(__file__).resolve().parent.parent
_AI = _BASE / "ai_engines"
for _p in (str(_BASE), str(_AI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

logger = logging.getLogger("app_compat")
_MAIN_DB = os.environ.get("MT_MAIN_DB_PATH", str(_AI / "app.db"))


def get_db_connection():
    """获取主库连接."""
    return sqlite3.connect(_MAIN_DB, timeout=15)


def init_db():
    """初始化数据库 (调用 schema_aligner)."""
    try:
        import schema_aligner
        return schema_aligner.ensure_schema_ready()
    except Exception as e:
        logger.warning(f"init_db via schema_aligner 失败: {e}")
        return None


def create_app():
    """创建 Flask app (委托 server_real_db)."""
    try:
        import server_real_db
        app = server_real_db.app

        # 注册统一权限中间件，确保在所有蓝图前执行
        @app.before_request
        def _unified_permission_wrapper():
            return unified_permission()

        return app
    except Exception as e:
        logger.exception("create_app 委托 server_real_db 失败")
        raise RuntimeError("无法加载正式 Flask 应用 server_real_db") from e

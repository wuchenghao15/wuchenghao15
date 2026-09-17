import os
import sys
import sqlite3
import shutil
from functools import wraps

_PROJECT_ROOT = None
_PATCHED = False
_MARKER_FILENAMES = [
    'MTSCOS_PROJECT_ROOT',
    'modular_start.py',
    'server_real_db.py',
    'app.py',
    'VERSION',
]
# VII代 v22.10.0 R4b：真项目根独有特征（flask-app/ 子目录不可能同时拥有这些）
# 用于击败 flask-app/app.py marker 的误命中，锁定 _runtime/databases/Database/app.db
_TRUE_ROOT_MARKERS = (
    'start_smart_mount_daemon.command',
    'start_ai_eigenflux_daemon.command',
    'flask-app',  # 作为子目录
    '.trae',
    'scripts',
)


def resolve_project_root():
    global _PROJECT_ROOT
    if _PROJECT_ROOT and os.path.exists(_PROJECT_ROOT):
        return _PROJECT_ROOT
    current = os.path.dirname(os.path.abspath(__file__))
    max_level = 12
    candidates = []  # [(hits, path)]
    for _ in range(max_level):
        hits = 0
        for m in _MARKER_FILENAMES:
            if os.path.exists(os.path.join(current, m)):
                hits += 1
        for sub in ('Database', 'data', 'templates', 'ai_engines'):
            if os.path.isdir(os.path.join(current, sub)):
                hits += 1
                break
        # --- R4b 路由闭环 + 真库定位修复 (VII代 v22.10.0):
        # 真项目根必须含 _runtime/ 目录 (4.3GB app.db 与守护进程PID在其中)；
        # 含 _runtime/ 的路径 hits 额外 +5；再叠加一组真根独有marker +5/项，
        # 以便在 flask-app/ 有app.py时也能胜出父目录。
        try:
            if os.path.isdir(os.path.join(current, '_runtime')):
                hits += 5
        except Exception:
            pass
        for trm in _TRUE_ROOT_MARKERS:
            try:
                if os.path.exists(os.path.join(current, trm)) or os.path.isdir(os.path.join(current, trm)):
                    hits += 3
            except Exception:
                pass
        if hits >= 2:
            candidates.append((hits, current))
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    if candidates:
        # 命中最高的作为项目根（含_runtime的父目录永远≥子目录命中）
        candidates.sort(reverse=True, key=lambda x: x[0])
        _PROJECT_ROOT = candidates[0][1]
        return _PROJECT_ROOT
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return _PROJECT_ROOT


def _score_db_path(path):
    if not os.path.exists(path):
        return -1, 0
    size = os.path.getsize(path)
    if size == 0:
        return -1, 0
    core_weight = {
        'users': 10, 'questions': 10, 'permissions': 8,
        'system_config': 8, 'system_versions': 8,
        'exams': 6, 'courses': 5, 'system_rules': 5,
        'ai_firewall_rules': 4, 'question_bank': 3,
        'ai_brain_bank': 3, 'access_logs': 3, 'ai_employees': 3,
    }
    try:
        # 只读 + immutable 模式：避免在云盘(OneDrive)上创建 journal/wal 造成大量 IO；
        # 不写入、不加锁，sqlite_master 读取与存在性探测极快。
        conn = sqlite3.connect(f'file:{path}?mode=ro&immutable=1', uri=True, timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = set(r[0] for r in cur.fetchall())
        score = 0
        table_count = len(tables)
        for t, w in core_weight.items():
            if t not in tables:
                continue
            try:
                # O(1) 存在性探测，禁止全表 COUNT(*)（4.9GB 库会卡死在云盘 IO）
                cur.execute(f'SELECT 1 FROM "{t}" LIMIT 1')
                if cur.fetchone():
                    score += w
            except Exception:
                continue
        conn.close()
    except Exception:
        return size * 0 + 0, size
    total = score * 1024 * 1024 + min(size, 50 * 1024 * 1024) + table_count * 100
    return total, table_count


def _discover_canonical_dbs():
    root = resolve_project_root()
    out = {}
    candidate_dirs = [
        # 🆕 2026-09-16: 仙女座演化库有 241 张核心表 (brain+eigenflux+graph) 放在 flask-app/database
        # 之前 list 里只有 flask-app/ (flask-app 根目录) 但演化库在 flask-app/database/ 子目录
        # 导致 app.db 被错误映射到项目根那个 5.6MB 空库 (只有 121 表, brain=252, 无 eigenflux)
        os.path.join(root, 'flask-app', 'database'),
        os.path.join(root, 'data', 'databases'),
        os.path.join(root, 'flask-app'),
        os.path.join(root, 'Database'),
        root,
        os.path.join(root, 'flask-app', 'split_databases'),
        # 文件重组后数据库已迁移至 _runtime/databases/Database（root 可能解析到 flask-app 或项目根）
        os.path.join(root, '..', '_runtime', 'databases', 'Database'),
        os.path.join(root, '_runtime', 'databases', 'Database'),
        os.path.join(root, '..', '_runtime', 'databases'),
        os.path.join(root, '_runtime', 'databases'),
    ]
    scan_db_names = [
        'app.db', 'auth.db', 'mtscos.db', 'version_unified.db',
        'scheduler.db', 'activity_logs.db', 'system_extensions.db',
        'self_learning.db', 'session_security.db', 'permission_manager.db',
        'primary.db', 'backup.db', 'system.db', 'config.db',
        'exam.db', 'question.db', 'user.db', 'learning.db', 'ai.db',
        'log.db', 'proctor.db', 'admin.db', 'physics.db', 'math.db',
        'other.db', 'intelligent_evaluation.db', 'ai_memory.db',
        'emotion_analysis.db', 'ai_adaptive_learning.db', 'ai_qna.db',
        'ai_cognitive.db', 'ai_decision.db', 'ai_prediction.db',
        'ai_recommendation.db', 'professional_role.db',
        'skill_evolution.db', 'theme_manager.db',
    ]
    for name in scan_db_names:
        best = None
        best_score = -1
        seen = set()
        for _idx, d in enumerate(candidate_dirs):
            p = os.path.join(d, name)
            rp = os.path.realpath(p) if os.path.exists(p) else p
            if rp in seen:
                continue
            seen.add(rp)
            score, _ = _score_db_path(p)
            # 🆕 2026-09-16: flask-app/database 子目录权重加成
            # 仙女座演化库 (brain+eigenflux+graph) 放这里, 必须优先
            if '/flask-app/database' in d and os.path.exists(p):
                score += 500000  # 额外加成让它必赢
            if score > best_score:
                best_score = score
                best = p
        if best and os.path.exists(best):
            out[name] = best
    if 'auth.db' not in out:
        for d in candidate_dirs:
            cand = os.path.join(d, 'split_databases', 'auth.db')
            if os.path.exists(cand) and os.path.getsize(cand) > 0:
                out['auth.db'] = cand
                break
    if 'app.db' not in out:
        for p in (os.path.join(root, 'Database', 'app.db'),
                  os.path.join(root, 'app.db')):
            if os.path.exists(p):
                out['app.db'] = p
                break
    return out


_DB_MAPPING = None


def _get_mapping():
    global _DB_MAPPING
    if _DB_MAPPING is None:
        _DB_MAPPING = _discover_canonical_dbs()
    return _DB_MAPPING


def refresh_mapping():
    global _DB_MAPPING
    _DB_MAPPING = None
    return _get_mapping()


def get_db_path(db_name):
    root = resolve_project_root()
    mapping = _get_mapping()
    base = os.path.basename(db_name)
    if not base:
        return os.path.join(root, 'Database', 'app.db')
    if os.path.isabs(db_name):
        cand = db_name
        if not os.path.exists(cand) or (os.path.exists(cand) and os.path.getsize(cand) == 0):
            alt = mapping.get(base)
            if alt and alt != cand:
                return alt
        return cand
    if base in mapping:
        return mapping[base]
    return os.path.join(root, 'Database', base)


def map_db_name(db_name):
    mapping = _get_mapping()
    base = os.path.basename(db_name)
    return mapping.get(base, os.path.join(resolve_project_root(), 'Database', base))


def db_conn(db_name, *args, **kwargs):
    path = get_db_path(db_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return sqlite3.connect(path, *args, **kwargs)


def db_conn_ro(db_name, timeout=30):
    """只读 SQLite 连接 — URI mode=ro&immutable=1，彻底免疫 daemon 写锁。
    所有 Flask 路由只读端点统一使用此函数，避免 'database is locked'。
    自动对路径做 URL 编码以处理 OneDrive 中文路径 (OneDrive-个人/文档/...)。

    注意: 用 immutable=1 而非 nolock=1 — nolock=1 在 macOS OneDrive 云盘上会导致
    'unable to open database file'；immutable=1 会让 SQLite 完全跳过 journal/WAL 创建，
    读操作不接触任何锁，云盘 IO 最友好。
    """
    import urllib.parse as _up
    path = get_db_path(db_name)
    path = os.path.realpath(path)              # 展开 ../ 和符号链接
    encoded = _up.quote(path, safe='/')        # 保留斜杠，只编码中文/空格
    uri = f'file:{encoded}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True, timeout=timeout, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def patch_sqlite3_connect(verbose=False):
    global _PATCHED
    if _PATCHED:
        return getattr(sqlite3, '_mtscos_original_connect', sqlite3.connect)
    try:
        original_connect = sqlite3.connect
    except Exception:
        original_connect = sqlite3.connect
    sqlite3._mtscos_original_connect = original_connect
    mapping = _get_mapping()

    @wraps(original_connect)
    def new_connect(database, *args, **kwargs):
        actual_path = database
        redirected = False
        if isinstance(database, str) and database != ':memory:':
            base = os.path.basename(database)
            if base in mapping:
                canonical = mapping[base]
                if database != canonical:
                    if not os.path.isabs(database):
                        actual_path = canonical
                        redirected = True
                    elif (os.path.exists(database)
                          and os.path.exists(canonical)
                          and os.path.getsize(database) < max(4096, os.path.getsize(canonical) * 0.05)):
                        actual_path = canonical
                        redirected = True
                    elif not os.path.exists(database):
                        actual_path = canonical
                        redirected = True
        if verbose and redirected:
            try:
                sys.stderr.write(f"[DB Patch] sqlite3.connect('{database}') -> '{actual_path}'\n")
            except Exception:
                pass
        if actual_path != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(actual_path)), exist_ok=True)
        conn = original_connect(actual_path, *args, **kwargs)
        # 🆕 2026-09-17: 所有连接自动加 busy_timeout=60s + 强制 WAL
        # 之前 journal_mode 被某个模块先开成 delete → 所有后续连接继承 delete → 写锁竞争极激烈
        # Flask 多线程里多个 BEGIN IMMEDIATE 互相等 → 死锁 → 永久 database is locked
        # 强制 WAL: 读不阻塞写 + 写不阻塞读, busy_timeout=60s 让 SQLite 内部排队
        # ⚠️ 关键: PRAGMA journal_mode 只能在第一个连接设, 必须确保第一个连接就是 WAL
        try:
            conn.execute("PRAGMA busy_timeout=60000")
            # 检查当前 journal_mode, 如果不是 WAL 就强制
            cur_mode = conn.execute("PRAGMA journal_mode").fetchone()
            if cur_mode and cur_mode[0] != 'wal':
                conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA wal_autocheckpoint=1000")
            conn.execute("PRAGMA recursive_triggers=ON")
        except Exception:
            pass  # 只读连接或 :memory: 可能不支持, 忽略
        return conn

    sqlite3.connect = new_connect
    try:
        import pysqlite3  # type: ignore
        try:
            pysqlite3.connect = new_connect
        except Exception:
            pass
    except Exception:
        pass
    _PATCHED = True
    return original_connect


def is_patched():
    global _PATCHED
    return _PATCHED


def db_status_report():
    root = resolve_project_root()
    mapping = _get_mapping()
    lines = []
    lines.append(f"[DB Status] project_root = {root}")
    lines.append(f"[DB Status] patched = {_PATCHED}")
    lines.append(f"[DB Status] discovered databases = {len(mapping)}")
    for name, path in sorted(mapping.items()):
        try:
            size = os.path.getsize(path)
        except Exception:
            size = -1
        lines.append(f"  - {name} => {path} ({size} bytes)")
    return '\n'.join(lines)


def try_merge_small_app_db():
    root = resolve_project_root()
    mapping = _get_mapping()
    canon = mapping.get('app.db')
    if not canon:
        return
    small_candidates = [
        os.path.join(root, 'app.db'),
        os.path.join(root, 'Database', 'app.db'),
    ]
    for sc in small_candidates:
        if not os.path.exists(sc) or os.path.abspath(sc) == os.path.abspath(canon):
            continue
        if os.path.getsize(sc) > 0 and os.path.getsize(sc) < 20 * 1024 * 1024:
            try:
                os.remove(sc)
                shutil.copy2(canon, sc)
                sys.stderr.write(f"[DB Merge] updated small {sc} from canonical {canon}\n")
            except Exception:
                pass


__all__ = [
    'resolve_project_root', 'get_db_path', 'db_conn', 'db_conn_ro', 'map_db_name',
    'patch_sqlite3_connect', 'is_patched', 'db_status_report',
    'refresh_mapping', 'try_merge_small_app_db',
]

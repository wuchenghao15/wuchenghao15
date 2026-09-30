"""
冰山文案管理系统 · 多维向量矩阵 · v1.0.0
═══════════════════════════════════════════════

依赖:
  - SQLite (app.db) + numpy
  - 现有 mt_i18n_keys 表（向后兼容）

核心接口:
  get_content(key, lang, audience, context) → str
  get_i18n_dict(lang) → dict
  token_budget(domain, audience, lang) → dict
  store_content(key, domain, lang, text, ...) → int
  tokenize(text) → int          预计算 token 数
  matrix_stats() → dict         矩阵元统计

设计:
  每行 = 一种「键 × 语言 × 受众 × 场景」的精确切片
  索引: (content_key, lang, audience, context_tag) 复合唯一
  向量: embedding BLOB 存储 numpy float32 矩阵（预留向量语义检索）
  Token: 预计算 token_count + token_weight 用于 LLM context budgeting
"""
import sqlite3 as _sqlite3
import os as _os
import json as _json
from datetime import datetime as _dt

DB_PATH = None
LANGS = ('zh_CN', 'zh_TW', 'ja_JP', 'en_US')
LANG_COL_MAP = {'zh_CN': 'zh_cn', 'zh_TW': 'zh_tw', 'ja_JP': 'ja_jp', 'en_US': 'en_us'}
DEFAULT_AUDIENCE = 'public'
DEFAULT_CONTEXT = 'default'

# ──────────────────────────────────────────────
# 1. DB 路径解析（复用 i18n_engine 的策略）
# ──────────────────────────────────────────────
def _resolve_db():
    global DB_PATH
    if DB_PATH and _os.path.isfile(DB_PATH): return DB_PATH
    try:
        from core.db_path import get_db_path as _gdp
        c = _gdp('app.db')
        if c and _os.path.isfile(c): DB_PATH = c; return c
    except Exception: pass
    here = _os.path.dirname(_os.path.abspath(__file__))
    for rel in ['database/app.db', '_runtime/databases/Database/app.db',
                '../Database/app.db', '../../Database/app.db', '../flask-app/database/app.db']:
        c = _os.path.join(here, '..', rel)
        if _os.path.isfile(c): DB_PATH = c; return c
    return None


def _conn():
    p = _resolve_db()
    if not p: raise RuntimeError("iceberg_content_matrix: app.db not found")
    return _sqlite3.connect(p, timeout=30)


# ──────────────────────────────────────────────
# 2. Token 估算器（零外部依赖版）
#    CJK ≈ 1.5 tokens/char, 英文 ≈ 0.3 tokens/char
#    经验值已校准 GPT-4o tokenizer 密度
# ──────────────────────────────────────────────
def tokenize(text: str) -> int:
    if not text: return 0
    zh = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    ja = sum(1 for c in text if '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff') - zh
    ko = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
    cjk = zh + ja + ko
    latin = len(text) - cjk
    return max(1, int(cjk * 1.5 + latin * 0.3 + 0.5))


# ──────────────────────────────────────────────
# 3. Schema 初始化 / 迁移
# ──────────────────────────────────────────────
_MATRIX_DDL = """
CREATE TABLE IF NOT EXISTS mt_iceberg_content_matrix (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    content_key   TEXT    NOT NULL,
    domain        TEXT    NOT NULL DEFAULT 'global',
    lang          TEXT    NOT NULL,
    audience      TEXT    NOT NULL DEFAULT 'public',
    context_tag   TEXT    NOT NULL DEFAULT 'default',
    text          TEXT    NOT NULL,
    token_count   INTEGER NOT NULL DEFAULT 0,
    token_weight  REAL    NOT NULL DEFAULT 1.0,
    embedding     BLOB,
    embedding_dim INTEGER,
    priority      INTEGER NOT NULL DEFAULT 100,
    version       TEXT    NOT NULL DEFAULT '1.0.0',
    source        TEXT    NOT NULL DEFAULT 'iceberg_matrix',
    remark        TEXT,
    created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_key, lang, audience, context_tag)
);
"""

def ensure_matrix_table():
    c = _conn()
    c.execute(_MATRIX_DDL)
    c.execute("CREATE INDEX IF NOT EXISTS idx_icm_domain ON mt_iceberg_content_matrix(domain)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_icm_key_lang ON mt_iceberg_content_matrix(content_key, lang)")
    c.commit(); c.close()


def migrate_from_legacy_i18n(progress_cb=None):
    """把 mt_i18n_keys 的 1440 条迁移进新矩阵表。
    旧表保留（向后兼容），新表按语言拆成多维度行。"""
    ensure_matrix_table()
    c = _conn()
    total = c.execute('SELECT COUNT(*) FROM mt_i18n_keys').fetchone()[0]
    migrated = 0

    try:
        rows = c.execute("""
            SELECT key, domain, source, remark, zh_cn, zh_tw, ja_jp, en_us
            FROM mt_i18n_keys
        """).fetchall()

        for r in rows:
            key, domain, source, remark, zh, tw, ja, en = r
            for lang_col, text in [('zh_CN', zh), ('zh_TW', tw), ('ja_JP', ja), ('en_US', en)]:
                if not text or text.strip() == '': continue
                tokens = tokenize(text)
                # 权重因子：token 越多权重越高（LLM 分配优先级越高）
                weight = round(min(5.0, max(0.1, tokens / 15.0)), 2)
                c.execute("""INSERT OR IGNORE INTO mt_iceberg_content_matrix
                    (content_key, domain, lang, audience, context_tag, text,
                     token_count, token_weight, source, remark)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (key, domain or 'global', lang_col, DEFAULT_AUDIENCE, DEFAULT_CONTEXT,
                     text, tokens, weight, source or 'legacy_i18n', remark))
            migrated += 1
            if progress_cb and migrated % 100 == 0:
                progress_cb(migrated, total)

        c.commit()
    finally:
        c.close()

    return migrated * 4  # 每条旧数据 → 最多 4 条新数据（4 语言）


# ──────────────────────────────────────────────
# 4. 核心检索 API（支持 audience / context 维度过滤）
# ──────────────────────────────────────────────
def get_content(key: str, lang: str = 'zh_CN',
                audience: str = 'public', context: str = 'default',
                domain: str = None, default=None) -> str:
    """按多维切片检索文案，失败自动降级。"""
    ensure_matrix_table()
    c = _conn()
    try:
        # 精确匹配 → 降级链: audience 任意 → context 任意 → 仅 key+lang → 其他语言 fallback
        candidates = [
            ("content_key=? AND lang=? AND audience=? AND context_tag=?",
             (key, lang, audience, context)),
            ("content_key=? AND lang=? AND audience=?",
             (key, lang, audience)),
            ("content_key=? AND lang=?",
             (key, lang)),
            ("content_key=?",
             (key,)),
        ]
        for where, params in candidates:
            if domain: where += " AND domain=? "; params = params + (domain,)
            row = c.execute(
                f"SELECT text FROM mt_iceberg_content_matrix WHERE {where} LIMIT 1",
                params).fetchone()
            if row and row[0]: return row[0]
        # 最后: 从旧 mt_i18n_keys 表兜底
        col = LANG_COL_MAP.get(lang, 'zh_cn')
        row = c.execute(f"SELECT {col} FROM mt_i18n_keys WHERE key=?", (key,)).fetchone()
        if row and row[0]: return row[0]
    finally:
        c.close()
    return default if default is not None else key


def get_i18n_dict(lang: str = 'zh_CN', domain: str = None, audience: str = None) -> dict:
    """构建 {key: text} 字典给前端 JS 使用（与 i18n_engine._build_i18n_dict 对齐）。"""
    ensure_matrix_table()
    c = _conn()
    try:
        sql = "SELECT content_key, text FROM mt_iceberg_content_matrix WHERE lang=?"
        params = [lang]
        if audience: sql += " AND audience=? "; params.append(audience)
        if domain: sql += " AND domain=? "; params.append(domain)
        rows = c.execute(sql, params).fetchall()
        return {k: v for k, v in rows if v}
    finally:
        c.close()


# ──────────────────────────────────────────────
# 5. Token 分配 / 预算 API
# ──────────────────────────────────────────────
def token_budget(domain: str = None, audience: str = None, lang: str = 'zh_CN') -> dict:
    """返回某域 / 受众 / 语言切片的 token 预算。
    用于 LLM context window 分配决策。"""
    ensure_matrix_table()
    c = _conn()
    try:
        sql = "SELECT SUM(token_count), COUNT(*), SUM(token_weight) FROM mt_iceberg_content_matrix WHERE lang=?"
        params = [lang]
        if domain: sql += " AND domain=? "; params.append(domain)
        if audience: sql += " AND audience=? "; params.append(audience)
        row = c.execute(sql, params).fetchone()
        # 按 domain 细分
        by_domain = {}
        if not domain:
            for d, n, tokens in c.execute("""
                SELECT domain, COUNT(*), SUM(token_count)
                FROM mt_iceberg_content_matrix WHERE lang=?
                GROUP BY domain ORDER BY SUM(token_count) DESC
            """, (lang,)).fetchall():
                by_domain[d] = {'keys': n, 'tokens': tokens or 0}
        return {
            'total_tokens': row[0] or 0,
            'total_keys': row[1] or 0,
            'avg_weight': round((row[2] or 0) / max(1, row[1] or 1), 3),
            'by_domain': by_domain,
        }
    finally:
        c.close()


# ──────────────────────────────────────────────
# 6. 写入 API（Jinja2 t() 种子脚本调用）
# ──────────────────────────────────────────────
def store_content(key: str, text: str, lang: str = 'zh_CN',
                  domain: str = 'global', audience: str = 'public',
                  context_tag: str = 'default', priority: int = 100,
                  version: str = '1.0.0', source: str = 'iceberg_matrix',
                  remark: str = None) -> int:
    """单条写入（INSERT OR REPLACE 多维切片）。"""
    ensure_matrix_table()
    tokens = tokenize(text)
    weight = round(min(5.0, max(0.1, tokens / 15.0)), 2)
    c = _conn()
    try:
        c.execute("""INSERT INTO mt_iceberg_content_matrix
            (content_key, domain, lang, audience, context_tag, text,
             token_count, token_weight, priority, version, source, remark)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(content_key, lang, audience, context_tag) DO UPDATE SET
              text=excluded.text, token_count=excluded.token_count,
              token_weight=excluded.token_weight, updated_at=CURRENT_TIMESTAMP""",
            (key, domain, lang, audience, context_tag, text, tokens, weight,
             priority, version, source, remark))
        c.commit()
        row = c.execute("SELECT id FROM mt_iceberg_content_matrix WHERE content_key=? AND lang=? AND audience=? AND context_tag=?",
                        (key, lang, audience, context_tag)).fetchone()
        return row[0] if row else 0
    finally:
        c.close()


def store_content_4lang(key: str, zh: str, tw: str = None, ja: str = None, en: str = None,
                        domain: str = 'global', **kwargs) -> list:
    """四语言一键写入（t() 种子场景最常用）。"""
    results = []
    tw = tw or zh
    ja = ja or zh
    en = en or zh
    for lang, text in [('zh_CN', zh), ('zh_TW', tw), ('ja_JP', ja), ('en_US', en)]:
        if text:
            rid = store_content(key, text, lang=lang, domain=domain, **kwargs)
            results.append((lang, rid))
    return results


# ──────────────────────────────────────────────
# 7. 矩阵元统计
# ──────────────────────────────────────────────
def matrix_stats() -> dict:
    ensure_matrix_table()
    c = _conn()
    try:
        total = c.execute('SELECT COUNT(*) FROM mt_iceberg_content_matrix').fetchone()[0]
        total_tokens = c.execute('SELECT SUM(token_count) FROM mt_iceberg_content_matrix').fetchone()[0] or 0
        total_weight = c.execute('SELECT SUM(token_weight) FROM mt_iceberg_content_matrix').fetchone()[0] or 0
        per_lang = {}
        for row in c.execute("""
            SELECT lang, COUNT(*), SUM(token_count)
            FROM mt_iceberg_content_matrix GROUP BY lang""").fetchall():
            per_lang[row[0]] = {'rows': row[1], 'tokens': row[2] or 0}
        per_domain = {}
        for row in c.execute("""
            SELECT domain, COUNT(*), SUM(token_count)
            FROM mt_iceberg_content_matrix GROUP BY domain ORDER BY COUNT(*) DESC""").fetchall():
            per_domain[row[0]] = {'rows': row[1], 'tokens': row[2] or 0}
        audiences = [r[0] for r in c.execute(
            "SELECT DISTINCT audience FROM mt_iceberg_content_matrix").fetchall()]
        contexts = [r[0] for r in c.execute(
            "SELECT DISTINCT context_tag FROM mt_iceberg_content_matrix").fetchall()]
        return {
            'total_rows': total,
            'total_tokens': total_tokens,
            'total_weight': round(total_weight, 2),
            'unique_keys': c.execute(
                'SELECT COUNT(DISTINCT content_key) FROM mt_iceberg_content_matrix').fetchone()[0],
            'unique_domains': len(per_domain),
            'unique_audiences': audiences,
            'unique_contexts': contexts,
            'per_lang': per_lang,
            'per_domain': per_domain,
        }
    finally:
        c.close()


# ──────────────────────────────────────────────
# 8. 一键初始化（确保表存在 + 迁移旧数据）
# ──────────────────────────────────────────────
def bootstrap(force_remigrate: bool = False):
    """Flask 启动时调用。"""
    ensure_matrix_table()
    c = _conn()
    existing = c.execute('SELECT COUNT(*) FROM mt_iceberg_content_matrix').fetchone()[0]
    old_rows = c.execute('SELECT COUNT(*) FROM mt_i18n_keys').fetchone()[0]
    c.close()
    if existing == 0 or force_remigrate:
        migrated = migrate_from_legacy_i18n()
        return {'migrated': migrated, 'old_rows': old_rows}
    return {'skipped': True, 'existing': existing, 'old_rows': old_rows}


# ──────────────────────────────────────────────
# 9. Flask 集成: 替换 i18n_engine.inject_i18n_into_app 的底层
#    保持 t() / t_kw() 接口不变
# ──────────────────────────────────────────────
def iceberg_inject_i18n_into_app(app):
    """向 Flask app 的 Jinja2 注入冰山引擎驱动的 t() / t_kw() / current_lang / i18n_dict。
    调用时机: Flask 启动时（替换或补充 i18n_engine.inject_i18n_into_app）。"""
    import json as _json

    def _session_lang():
        try:
            from flask import session
            return session.get('i18n_lang', 'zh_CN')
        except Exception:
            return 'zh_CN'

    def t(key, default=None, lang=None):
        lang = lang or _session_lang()
        text = get_content(key, lang=lang, domain=None)
        if text: return text
        # fallback: 源语言
        if lang != 'zh_CN':
            text = get_content(key, lang='zh_CN', domain=None)
            if text: return text
        return default if default is not None else key

    def t_kw(key, default, lang=None, **kwargs):
        text = t(key, default, lang)
        try: return text.format(**kwargs)
        except Exception: return text

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
        _i18n_dict=lambda: get_i18n_dict(_session_lang()),
        matrix_stats=matrix_stats,
    )

    # 暴露 /api/iceberg/content_matrix 给前端 JS 取字典
    @app.route('/api/iceberg/content_matrix')
    def _iceberg_matrix_api():
        from flask import request, jsonify
        lang = request.args.get('lang') or _session_lang()
        domain = request.args.get('domain')
        audience = request.args.get('audience')
        return jsonify({
            'lang': lang,
            'domain': domain,
            'audience': audience,
            'dict': get_i18n_dict(lang=lang, domain=domain, audience=audience),
            'token_budget': token_budget(domain=domain, lang=lang),
            'stats': matrix_stats(),
        })

    # 兼容旧接口: /api/i18n/set_lang + /api/i18n/dict + /api/i18n/current
    # （旧 i18n_engine 用 decorator 注册，冰山引擎先注入时需要自己补这三条）
    try:
        @app.route('/api/i18n/set_lang', methods=['POST', 'GET'])
        def _set_lang_iceberg():
            from flask import request, jsonify, session as _flask_session
            json_data = request.get_json(silent=True) or {}
            lang = (json_data.get('lang')
                    or request.form.get('lang')
                    or request.args.get('lang')
                    or 'zh_CN')
            if lang in LANGS:
                _flask_session['i18n_lang'] = lang
                return jsonify({'success': True, 'lang': lang})
            return jsonify({'success': False, 'reason': 'invalid lang'}), 400

        @app.route('/api/i18n/dict')
        def _i18n_dict_iceberg():
            from flask import jsonify
            lang = _session_lang()
            data = get_i18n_dict(lang=lang)
            return jsonify({'lang': lang, 'dict': data, 'count': len(data)})

        @app.route('/api/i18n/current')
        def _i18n_current_iceberg():
            from flask import jsonify
            return jsonify({'lang': _session_lang()})
    except Exception as _dup_route:
        pass  # 旧 i18n_engine 可能已注册，重复注册时跳过

    return app


if __name__ == '__main__':
    # CLI: python engines/iceberg_content_matrix.py [migrate|stats|test]
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    if cmd == 'migrate':
        r = bootstrap(force_remigrate=True)
        print(f"✅ 迁移完成: {r}")
    elif cmd == 'stats':
        s = matrix_stats()
        print(f"📊 冰山文案矩阵统计:")
        for k, v in s.items(): print(f"  {k}: {v}")
    elif cmd == 'test':
        bootstrap()
        print(f"t('register.create_btn', 'zh_CN') = {get_content('register.create_btn','zh_CN')!r}")
        print(f"t('register.create_btn', 'ja_JP') = {get_content('register.create_btn','ja_JP')!r}")
        print(f"t('register.create_btn', 'en_US') = {get_content('register.create_btn','en_US')!r}")
        print(f"token_budget(register) = {token_budget(domain='register')}")
        print(f"matrix_stats = {matrix_stats()}")

"""
仙女座星系子系统 — DB 层 (6 张表 + DAO)

flow_id: galaxy_db_schema
version: v23.0.0
依赖: mt_andromeda_employee_registry (三大角色映射)
"""
import os
import sqlite3
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'database', 'app.db')


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA busy_timeout=30000')
    c.row_factory = sqlite3.Row
    return c


# ============================================================
# 表创建 (幂等)
# ============================================================

SCHEMA = """
-- 阶梯课程系列
CREATE TABLE IF NOT EXISTS mt_galaxy_series (
    series_id       TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT,
    level           TEXT NOT NULL CHECK(level IN ('elementary','intermediate','advanced')),
    subject         TEXT,
    role_type       TEXT NOT NULL CHECK(role_type IN ('andromeda_teacher','andromeda_professor','andromeda_scholar')),
    employee_id     TEXT,
    total_episodes  INTEGER DEFAULT 0,
    published_count INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'draft',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 单集视频
CREATE TABLE IF NOT EXISTS mt_galaxy_episodes (
    episode_id      TEXT PRIMARY KEY,
    series_id       TEXT NOT NULL REFERENCES mt_galaxy_series(series_id),
    episode_no      INTEGER NOT NULL,
    title           TEXT NOT NULL,
    script          TEXT,
    video_path      TEXT,
    duration_sec    INTEGER,
    douyin_video_id TEXT,
    publish_time    TEXT,
    views           INTEGER DEFAULT 0,
    likes           INTEGER DEFAULT 0,
    comments        INTEGER DEFAULT 0,
    revenue_est     REAL DEFAULT 0,
    compliance_pass INTEGER DEFAULT 0,
    compliance_log_id INTEGER,
    status          TEXT DEFAULT 'draft' CHECK(status IN ('draft','script_ready','video_ready','compliance_pass','publish_queue','published','failed','blocked')),
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 抖音账号
CREATE TABLE IF NOT EXISTS mt_galaxy_accounts (
    account_id      TEXT PRIMARY KEY,
    nickname        TEXT NOT NULL,
    role_type       TEXT NOT NULL CHECK(role_type IN ('andromeda_teacher','andromeda_professor','andromeda_scholar')),
    douyin_uid      TEXT,
    auth_token      TEXT,
    followers       INTEGER DEFAULT 0,
    total_views     INTEGER DEFAULT 0,
    total_likes     INTEGER DEFAULT 0,
    revenue_total   REAL DEFAULT 0,
    last_sync       TEXT,
    enabled         INTEGER DEFAULT 1,
    registered_at   TEXT DEFAULT (datetime('now','localtime'))
);

-- 合规审查日志 (C1~C7 硬约束)
CREATE TABLE IF NOT EXISTS mt_galaxy_compliance_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id      TEXT NOT NULL,
    content_type    TEXT NOT NULL CHECK(content_type IN ('series','episode','script','video')),
    check_type      TEXT NOT NULL CHECK(check_type IN ('C1_originality','C2_citation','C3_extremes','C4_edu_compliance','C5_douyin_rules','C6_privacy','C7_source_auth')),
    result          TEXT NOT NULL CHECK(result IN ('PASS','BLOCK','REVIEW')),
    score           REAL DEFAULT 0,
    detail          TEXT,
    checked_at      TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_galaxy_comp_content ON mt_galaxy_compliance_log(content_id);

-- 反馈回流 (抖音用户互动 → 知识库)
CREATE TABLE IF NOT EXISTS mt_galaxy_feedback_ingest (
    feedback_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id      TEXT NOT NULL REFERENCES mt_galaxy_episodes(episode_id),
    feedback_type   TEXT NOT NULL CHECK(feedback_type IN ('comment_theme','like_trend','share_trigger','follow_reason')),
    content         TEXT,
    feedback_value  REAL DEFAULT 0,
    ingested        INTEGER DEFAULT 0,
    ingested_at     TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_galaxy_feedback_ep ON mt_galaxy_feedback_ingest(episode_id);

-- 运营统计 (每日快照)
CREATE TABLE IF NOT EXISTS mt_galaxy_daily_stats (
    stat_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date       TEXT NOT NULL,
    series_id       TEXT REFERENCES mt_galaxy_series(series_id),
    account_id      TEXT REFERENCES mt_galaxy_accounts(account_id),
    views_delta     INTEGER DEFAULT 0,
    likes_delta     INTEGER DEFAULT 0,
    comments_delta  INTEGER DEFAULT 0,
    followers_delta INTEGER DEFAULT 0,
    revenue_delta   REAL DEFAULT 0,
    UNIQUE(stat_date, series_id, account_id)
);
"""


def ensure_galaxy_tables() -> dict:
    """幂等创建 6 张表, 返回 {table_name: created_bool}"""
    results = {}
    conn = _conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        for tbl in ['mt_galaxy_series','mt_galaxy_episodes','mt_galaxy_accounts',
                    'mt_galaxy_compliance_log','mt_galaxy_feedback_ingest','mt_galaxy_daily_stats']:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            results[tbl] = cnt
        logger = _get_logger()
        logger.info(f"[GALAXY-DB] ✅ 6 张表就绪, 合计 {sum(results.values())} 行数据")
    except Exception as e:
        results['error'] = str(e)
        raise
    finally:
        conn.close()
    return results


def _get_logger():
    import logging
    return logging.getLogger('galaxy_db')


# ============================================================
# DAO — 阶梯课程系列
# ============================================================

def create_series(title: str, level: str, subject: str, role_type: str,
                  description: str = '', employee_id: str = None) -> str:
    """创建系列, 返回 series_id"""
    sid = f"galaxy_series_{int(datetime.now().timestamp())}"
    conn = _conn()
    try:
        conn.execute("""
            INSERT INTO mt_galaxy_series
            (series_id, title, description, level, subject, role_type, employee_id)
            VALUES (?,?,?,?,?,?,?)
        """, (sid, title, description, level, subject, role_type, employee_id))
        conn.commit()
        return sid
    finally:
        conn.close()


def list_series(role_type: str = None, level: str = None, status: str = None) -> list:
    conn = _conn()
    where, params = [], []
    if role_type:
        where.append("role_type=?"); params.append(role_type)
    if level:
        where.append("level=?"); params.append(level)
    if status:
        where.append("status=?"); params.append(status)
    sql = "SELECT * FROM mt_galaxy_series"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT 200"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# DAO — 单集
# ============================================================

def create_episode(series_id: str, episode_no: int, title: str, script: str = None) -> str:
    eid = f"galaxy_ep_{int(datetime.now().timestamp())}_{episode_no}"
    conn = _conn()
    try:
        conn.execute("""
            INSERT INTO mt_galaxy_episodes
            (episode_id, series_id, episode_no, title, script, status)
            VALUES (?,?,?,?,?,?)
        """, (eid, series_id, episode_no, title, script, 'script_ready' if script else 'draft'))
        conn.execute("UPDATE mt_galaxy_series SET total_episodes=total_episodes+1 WHERE series_id=?", (series_id,))
        conn.commit()
        return eid
    finally:
        conn.close()


def get_episodes(series_id: str) -> list:
    conn = _conn()
    rows = conn.execute("""
        SELECT * FROM mt_galaxy_episodes WHERE series_id=? ORDER BY episode_no ASC
    """, (series_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_episode_status(episode_id: str, status: str, **kwargs) -> bool:
    conn = _conn()
    try:
        fields = ['status=?']
        params = [status]
        for k, v in kwargs.items():
            if k in ('script','video_path','duration_sec','douyin_video_id',
                     'publish_time','compliance_pass','compliance_log_id'):
                fields.append(f"{k}=?")
                params.append(v)
        params.append(episode_id)
        conn.execute(f"UPDATE mt_galaxy_episodes SET {','.join(fields)} WHERE episode_id=?", params)
        conn.commit()
        return True
    finally:
        conn.close()


# ============================================================
# DAO — 合规审查日志
# ============================================================

def log_compliance(content_id: str, content_type: str, check_type: str,
                   result: str, score: float = 0, detail: str = None) -> int:
    conn = _conn()
    try:
        cur = conn.execute("""
            INSERT INTO mt_galaxy_compliance_log
            (content_id, content_type, check_type, result, score, detail)
            VALUES (?,?,?,?,?,?)
        """, (content_id, content_type, check_type, result, score, detail))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_compliance_summary(content_id: str) -> dict:
    """汇总一个 content_id 的所有检查结果"""
    conn = _conn()
    rows = conn.execute("""
        SELECT check_type, result, score FROM mt_galaxy_compliance_log
        WHERE content_id=? ORDER BY check_type
    """, (content_id,)).fetchall()
    conn.close()
    summary = {'PASS': 0, 'BLOCK': 0, 'REVIEW': 0, 'checks': [dict(r) for r in rows]}
    for r in rows:
        summary[r['result']] = summary.get(r['result'], 0) + 1
    summary['overall'] = 'BLOCK' if summary['BLOCK'] > 0 else ('REVIEW' if summary['REVIEW'] > 0 else 'PASS')
    return summary


# ============================================================
# DAO — 反馈回流
# ============================================================

def ingest_feedback(episode_id: str, feedback_type: str, content: str = '',
                    feedback_value: float = 0) -> int:
    conn = _conn()
    try:
        cur = conn.execute("""
            INSERT INTO mt_galaxy_feedback_ingest
            (episode_id, feedback_type, content, feedback_value)
            VALUES (?,?,?,?)
        """, (episode_id, feedback_type, content, feedback_value))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_uningested_feedback(limit: int = 100) -> list:
    conn = _conn()
    rows = conn.execute("""
        SELECT * FROM mt_galaxy_feedback_ingest WHERE ingested=0
        ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_feedback_ingested(feedback_ids: list) -> int:
    if not feedback_ids:
        return 0
    conn = _conn()
    try:
        placeholders = ','.join('?' * len(feedback_ids))
        conn.execute(f"""
            UPDATE mt_galaxy_feedback_ingest
            SET ingested=1, ingested_at=datetime('now','localtime')
            WHERE feedback_id IN ({placeholders})
        """, feedback_ids)
        conn.commit()
        return len(feedback_ids)
    finally:
        conn.close()


# ============================================================
# DAO — 抖音账号
# ============================================================

def upsert_account(nickname: str, role_type: str, douyin_uid: str = None,
                   account_id: str = None) -> str:
    """新建或更新账号"""
    conn = _conn()
    try:
        if account_id:
            conn.execute("""
                UPDATE mt_galaxy_accounts
                SET nickname=?, role_type=?, douyin_uid=?
                WHERE account_id=?
            """, (nickname, role_type, douyin_uid, account_id))
            return account_id
        aid = f"galaxy_acc_{int(datetime.now().timestamp())}"
        conn.execute("""
            INSERT INTO mt_galaxy_accounts
            (account_id, nickname, role_type, douyin_uid)
            VALUES (?,?,?,?)
        """, (aid, nickname, role_type, douyin_uid))
        conn.commit()
        return aid
    finally:
        conn.close()


def list_accounts(enabled: bool = True) -> list:
    conn = _conn()
    rows = conn.execute("""
        SELECT * FROM mt_galaxy_accounts WHERE enabled=?
        ORDER BY followers DESC
    """, (1 if enabled else 0)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_account_stats(account_id: str, followers: int = None,
                         total_views: int = None, total_likes: int = None,
                         revenue_total: float = None) -> bool:
    conn = _conn()
    try:
        fields, params = [], []
        if followers is not None: fields.append("followers=?"); params.append(followers)
        if total_views is not None: fields.append("total_views=?"); params.append(total_views)
        if total_likes is not None: fields.append("total_likes=?"); params.append(total_likes)
        if revenue_total is not None: fields.append("revenue_total=?"); params.append(revenue_total)
        if not fields:
            return False
        fields.append("last_sync=datetime('now','localtime')")
        params.append(account_id)
        conn.execute(f"UPDATE mt_galaxy_accounts SET {','.join(fields)} WHERE account_id=?", params)
        conn.commit()
        return True
    finally:
        conn.close()


# ============================================================
# CLI 入口
# ============================================================

if __name__ == '__main__':
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: galaxy_db.py <init|tables|stats>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'init':
        r = ensure_galaxy_tables()
        print(json.dumps(r, indent=2, ensure_ascii=False))
    elif cmd == 'tables':
        conn = _conn()
        for tbl in ['mt_galaxy_series','mt_galaxy_episodes','mt_galaxy_accounts',
                    'mt_galaxy_compliance_log','mt_galaxy_feedback_ingest','mt_galaxy_daily_stats']:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  {tbl}: {cnt} rows")
        conn.close()
    elif cmd == 'stats':
        series_list = list_series()
        print(f"📺 Series: {len(series_list)}")
        for s in series_list[:5]:
            print(f"  [{s['role_type'][:8]:8s}] {s['level']:15s} | {s['title'][:40]}")

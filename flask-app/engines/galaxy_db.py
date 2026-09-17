"""
仙女座星系子系统 — DB 层 (8 张表 + DAO)

flow_id: galaxy_db_schema
version: v23.1.0 (多平台扩展 + publish_log + platform_creds)
依赖: mt_andromeda_employee_registry (三大角色映射)
"""
import os
import sqlite3
import json as _json
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
# 表创建 (幂等) — v23.1.0 多平台扩展
# ============================================================

SCHEMA = """
-- 阶梯课程系列 (不变)
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

-- 单集视频 (douyin_video_id 保留兼容, 推荐用 publish_log)
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

-- === v23.1.0 新增: 账号基础信息 (单条 per account) ===
CREATE TABLE IF NOT EXISTS mt_galaxy_accounts (
    account_id      TEXT PRIMARY KEY,
    nickname        TEXT NOT NULL,
    role_type       TEXT NOT NULL CHECK(role_type IN ('andromeda_teacher','andromeda_professor','andromeda_scholar')),
    douyin_uid      TEXT,               -- 兼容旧字段, 推荐用 platform_creds
    auth_token      TEXT,               -- 兼容旧字段
    followers       INTEGER DEFAULT 0,
    total_views     INTEGER DEFAULT 0,
    total_likes     INTEGER DEFAULT 0,
    revenue_total   REAL DEFAULT 0,
    last_sync       TEXT,
    enabled         INTEGER DEFAULT 1,
    registered_at   TEXT DEFAULT (datetime('now','localtime'))
);

-- === v23.1.0 新增: 平台凭证 (per-account × per-platform) ===
CREATE TABLE IF NOT EXISTS mt_galaxy_platform_creds (
    cred_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id      TEXT NOT NULL REFERENCES mt_galaxy_accounts(account_id),
    platform        TEXT NOT NULL CHECK(platform IN ('douyin','xiaohongshu','bilibili','github')),
    platform_uid    TEXT,                               -- 各平台 UID/昵称
    login_id        TEXT,                               -- 登录账号 (手机号/邮箱)
    login_type      TEXT DEFAULT 'password' CHECK(login_type IN ('password','qrcode','cookie')),
    credential_json TEXT,                               -- cookie / token / 密码等敏感信息 (JSON)
    auth_status     TEXT DEFAULT 'pending' CHECK(auth_status IN ('pending','authorized','expired','failed')),
    followers       INTEGER DEFAULT 0,
    platform_url    TEXT,                               -- 主页 URL (可选)
    last_checked    TEXT,
    UNIQUE(account_id, platform)
);

-- === v23.1.0 新增: 发布日志 (泛化, 一个 episode 可发多平台) ===
CREATE TABLE IF NOT EXISTS mt_galaxy_publish_log (
    publish_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id      TEXT NOT NULL REFERENCES mt_galaxy_episodes(episode_id),
    series_id       TEXT REFERENCES mt_galaxy_series(series_id),
    account_id      TEXT REFERENCES mt_galaxy_accounts(account_id),
    platform        TEXT NOT NULL CHECK(platform IN ('douyin','xiaohongshu','bilibili')),
    platform_video_id TEXT,                             -- 各平台返回的 video/aweme/note id
    publish_url     TEXT,                               -- 发布后的访问 URL
    publish_status  TEXT DEFAULT 'pending' CHECK(publish_status IN ('pending','scheduled','published','failed','blocked')),
    scheduled_time  TEXT,
    published_at    TEXT,
    views           INTEGER DEFAULT 0,
    likes           INTEGER DEFAULT 0,
    comments        INTEGER DEFAULT 0,
    shares          INTEGER DEFAULT 0,
    revenue_est     REAL DEFAULT 0,
    tags_applied    TEXT,                               -- 实际打上的标签 (JSON array)
    activity_tags   TEXT,                               -- 活动标签 (JSON array)
    error_msg       TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_galaxy_publish_ep ON mt_galaxy_publish_log(episode_id);
CREATE INDEX IF NOT EXISTS idx_galaxy_publish_platform ON mt_galaxy_publish_log(platform, publish_status);

-- === v23.1.0 新增: 平台限流词库 (各平台差异化) ===
CREATE TABLE IF NOT EXISTS mt_galaxy_platform_restrict (
    restrict_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT NOT NULL CHECK(platform IN ('douyin','xiaohongshu','bilibili','all')),
    restrict_type    TEXT NOT NULL CHECK(restrict_type IN ('extreme','ad','copyright','sensitive','platform_specific')),
    word            TEXT NOT NULL,
    level           TEXT DEFAULT 'BLOCK' CHECK(level IN ('BLOCK','REVIEW','WARN')),
    note            TEXT,
    UNIQUE(platform, word)
);

-- === v23.1.0 新增: 高曝光活动追踪 ===
CREATE TABLE IF NOT EXISTS mt_galaxy_high_exposure (
    activity_id     TEXT PRIMARY KEY,
    platform        TEXT NOT NULL CHECK(platform IN ('douyin','xiaohongshu','bilibili','github')),
    activity_name   TEXT NOT NULL,
    activity_type   TEXT CHECK(activity_type IN ('challenge','hashtag','contest','topic','release')),
    hot_score       REAL DEFAULT 0,                     -- 热度分 (0~100)
    start_time      TEXT,
    end_time        TEXT,
    is_active       INTEGER DEFAULT 1,
    joined          INTEGER DEFAULT 0,
    tags_json       TEXT,                               -- 活动推荐标签
    notes           TEXT,
    discovered_at   TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_galaxy_exposure_platform ON mt_galaxy_high_exposure(platform, is_active);

-- 合规审查日志 (C5_douyin_rules 保留兼容, 新增 C5_platform_rules)
CREATE TABLE IF NOT EXISTS mt_galaxy_compliance_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id      TEXT NOT NULL,
    content_type    TEXT NOT NULL CHECK(content_type IN ('series','episode','script','video')),
    check_type      TEXT NOT NULL CHECK(check_type IN ('C1_originality','C2_citation','C3_extremes','C4_edu_compliance','C5_douyin_rules','C5_platform_rules','C6_privacy','C7_source_auth')),
    result          TEXT NOT NULL CHECK(result IN ('PASS','BLOCK','REVIEW')),
    score           REAL DEFAULT 0,
    detail          TEXT,
    platform        TEXT,
    checked_at      TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_galaxy_comp_content ON mt_galaxy_compliance_log(content_id);

-- 反馈回流
CREATE TABLE IF NOT EXISTS mt_galaxy_feedback_ingest (
    feedback_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id      TEXT NOT NULL REFERENCES mt_galaxy_episodes(episode_id),
    feedback_type   TEXT NOT NULL CHECK(feedback_type IN ('comment_theme','like_trend','share_trigger','follow_reason')),
    content         TEXT,
    feedback_value  REAL DEFAULT 0,
    platform        TEXT,
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
    platform        TEXT,
    views_delta     INTEGER DEFAULT 0,
    likes_delta     INTEGER DEFAULT 0,
    comments_delta  INTEGER DEFAULT 0,
    shares_delta    INTEGER DEFAULT 0,
    followers_delta INTEGER DEFAULT 0,
    revenue_delta   REAL DEFAULT 0,
    UNIQUE(stat_date, series_id, account_id, platform)
);
"""


def ensure_galaxy_tables() -> dict:
    """幂等创建 8 张表, 返回 {table_name: row_count}"""
    results = {}
    conn = _conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        all_tables = [
            'mt_galaxy_series',
            'mt_galaxy_episodes',
            'mt_galaxy_accounts',
            'mt_galaxy_platform_creds',
            'mt_galaxy_publish_log',
            'mt_galaxy_platform_restrict',
            'mt_galaxy_high_exposure',
            'mt_galaxy_compliance_log',
            'mt_galaxy_feedback_ingest',
            'mt_galaxy_daily_stats',
        ]
        for tbl in all_tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            results[tbl] = cnt
        logger = _get_logger()
        logger.info(f"[GALAXY-DB] ✅ {len(all_tables)} 张表就绪, 合计 {sum(results.values())} 行数据")
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
        allowed = ('script', 'video_path', 'duration_sec', 'douyin_video_id',
                   'publish_time', 'compliance_pass', 'compliance_log_id')
        for k, v in kwargs.items():
            if k in allowed:
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
                   result: str, score: float = 0, detail: str = None,
                   platform: str = None) -> int:
    conn = _conn()
    try:
        cur = conn.execute("""
            INSERT INTO mt_galaxy_compliance_log
            (content_id, content_type, check_type, result, score, detail, platform)
            VALUES (?,?,?,?,?,?,?)
        """, (content_id, content_type, check_type, result, score, detail, platform))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_compliance_summary(content_id: str, platform: str = None) -> dict:
    """汇总一个 content_id 的所有检查结果"""
    conn = _conn()
    sql = "SELECT check_type, result, score, platform FROM mt_galaxy_compliance_log WHERE content_id=?"
    params = [content_id]
    if platform:
        sql += " AND (platform=? OR platform IS NULL)"; params.append(platform)
    sql += " ORDER BY check_type"
    rows = conn.execute(sql, params).fetchall()
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
                    feedback_value: float = 0, platform: str = None) -> int:
    conn = _conn()
    try:
        cur = conn.execute("""
            INSERT INTO mt_galaxy_feedback_ingest
            (episode_id, feedback_type, content, feedback_value, platform)
            VALUES (?,?,?,?,?)
        """, (episode_id, feedback_type, content, feedback_value, platform))
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
# DAO — 账号 (基础信息)
# ============================================================

def upsert_account(nickname: str, role_type: str, douyin_uid: str = None,
                   account_id: str = None) -> str:
    """新建或更新账号基础信息"""
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
# DAO — v23.1.0 新增: 平台凭证 (per-account × per-platform)
# ============================================================

def upsert_platform_cred(account_id: str, platform: str, platform_uid: str = None,
                         login_id: str = None, login_type: str = 'password',
                         credential_json: str = None, auth_status: str = 'pending',
                         platform_url: str = None) -> int:
    """新建或更新一个平台凭证, 返回 cred_id"""
    conn = _conn()
    try:
        existing = conn.execute("""
            SELECT cred_id FROM mt_galaxy_platform_creds
            WHERE account_id=? AND platform=?
        """, (account_id, platform)).fetchone()

        if existing:
            cid = existing[0]
            conn.execute("""
                UPDATE mt_galaxy_platform_creds
                SET platform_uid=COALESCE(?, platform_uid),
                    login_id=COALESCE(?, login_id),
                    login_type=COALESCE(?, login_type),
                    credential_json=COALESCE(?, credential_json),
                    auth_status=COALESCE(?, auth_status),
                    platform_url=COALESCE(?, platform_url),
                    last_checked=datetime('now','localtime')
                WHERE cred_id=?
            """, (platform_uid, login_id, login_type, credential_json,
                  auth_status, platform_url, cid))
            conn.commit()
            return cid
        else:
            cur = conn.execute("""
                INSERT INTO mt_galaxy_platform_creds
                (account_id, platform, platform_uid, login_id, login_type,
                 credential_json, auth_status, platform_url)
                VALUES (?,?,?,?,?,?,?,?)
            """, (account_id, platform, platform_uid, login_id, login_type,
                  credential_json, auth_status, platform_url))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_platform_cred(account_id: str, platform: str) -> dict:
    conn = _conn()
    row = conn.execute("""
        SELECT * FROM mt_galaxy_platform_creds
        WHERE account_id=? AND platform=?
    """, (account_id, platform)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_platform_creds(account_id: str = None, platform: str = None,
                        auth_status: str = None) -> list:
    conn = _conn()
    where, params = [], []
    if account_id:
        where.append("account_id=?"); params.append(account_id)
    if platform:
        where.append("platform=?"); params.append(platform)
    if auth_status:
        where.append("auth_status=?"); params.append(auth_status)
    sql = "SELECT * FROM mt_galaxy_platform_creds"
    if where:
        sql += " WHERE " + " AND ".join(where)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# DAO — v23.1.0 新增: 发布日志 (多平台泛化)
# ============================================================

def create_publish_log(episode_id: str, platform: str, series_id: str = None,
                       account_id: str = None, scheduled_time: str = None) -> int:
    """创建待发布记录, 返回 publish_id"""
    conn = _conn()
    try:
        cur = conn.execute("""
            INSERT INTO mt_galaxy_publish_log
            (episode_id, series_id, account_id, platform,
             publish_status, scheduled_time)
            VALUES (?,?,?,?,?,?)
        """, (episode_id, series_id, account_id, platform,
              'scheduled' if scheduled_time else 'pending', scheduled_time))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_publish_log(publish_id: int, **kwargs) -> bool:
    """更新发布状态/结果/指标"""
    conn = _conn()
    try:
        allowed = ('platform_video_id', 'publish_url', 'publish_status',
                   'scheduled_time', 'published_at',
                   'views', 'likes', 'comments', 'shares', 'revenue_est',
                   'tags_applied', 'activity_tags', 'error_msg')
        fields, params = [], []
        for k, v in kwargs.items():
            if k in allowed:
                fields.append(f"{k}=?"); params.append(v)
        if not fields:
            return False
        params.append(publish_id)
        conn.execute(f"UPDATE mt_galaxy_publish_log SET {','.join(fields)} WHERE publish_id=?", params)
        conn.commit()
        return True
    finally:
        conn.close()


def get_publish_log(episode_id: str = None, platform: str = None,
                    status: str = None, limit: int = 100) -> list:
    conn = _conn()
    where, params = [], []
    if episode_id:
        where.append("episode_id=?"); params.append(episode_id)
    if platform:
        where.append("platform=?"); params.append(platform)
    if status:
        where.append("publish_status=?"); params.append(status)
    sql = "SELECT * FROM mt_galaxy_publish_log"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# DAO — v23.1.0 新增: 平台限流词库
# ============================================================

def upsert_restrict_word(platform: str, word: str, restrict_type: str = 'extreme',
                         level: str = 'BLOCK', note: str = None) -> int:
    conn = _conn()
    try:
        existing = conn.execute("""
            SELECT restrict_id FROM mt_galaxy_platform_restrict
            WHERE platform=? AND word=?
        """, (platform, word)).fetchone()
        if existing:
            conn.execute("""
                UPDATE mt_galaxy_platform_restrict
                SET restrict_type=?, level=?, note=?
                WHERE restrict_id=?
            """, (restrict_type, level, note, existing[0]))
            conn.commit()
            return existing[0]
        cur = conn.execute("""
            INSERT INTO mt_galaxy_platform_restrict
            (platform, restrict_type, word, level, note)
            VALUES (?,?,?,?,?)
        """, (platform, restrict_type, word, level, note))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_restrict_words(platform: str = None, restrict_type: str = None) -> list:
    conn = _conn()
    where, params = [], []
    if platform:
        where.append("platform IN (?, 'all')"); params.append(platform)
    if restrict_type:
        where.append("restrict_type=?"); params.append(restrict_type)
    sql = "SELECT * FROM mt_galaxy_platform_restrict"
    if where:
        sql += " WHERE " + " AND ".join(where)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# DAO — v23.1.0 新增: 高曝光活动追踪
# ============================================================

def upsert_high_exposure(activity_id: str, platform: str, activity_name: str,
                         activity_type: str = None, hot_score: float = 0,
                         start_time: str = None, end_time: str = None,
                         tags_json: str = None, notes: str = None) -> int:
    conn = _conn()
    try:
        existing = conn.execute("""
            SELECT activity_id FROM mt_galaxy_high_exposure WHERE activity_id=?
        """, (activity_id,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE mt_galaxy_high_exposure
                SET platform=?, activity_name=?, activity_type=?,
                    hot_score=?, start_time=?, end_time=?,
                    tags_json=?, notes=?, updated_at=datetime('now','localtime')
                WHERE activity_id=?
            """, (platform, activity_name, activity_type, hot_score,
                  start_time, end_time, tags_json, notes, activity_id))
            conn.commit()
            return 1
        conn.execute("""
            INSERT INTO mt_galaxy_high_exposure
            (activity_id, platform, activity_name, activity_type,
             hot_score, start_time, end_time, tags_json, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (activity_id, platform, activity_name, activity_type,
              hot_score, start_time, end_time, tags_json, notes))
        conn.commit()
        return 1
    finally:
        conn.close()


def list_active_high_exposure(platform: str = None, min_score: float = 0) -> list:
    conn = _conn()
    where, params = ["is_active=1", f"hot_score>=?"]
    params = [min_score]
    if platform:
        where.append("platform=?"); params.append(platform)
    sql = f"SELECT * FROM mt_galaxy_high_exposure WHERE {' AND '.join(where)}"
    sql += " ORDER BY hot_score DESC LIMIT 50"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_exposure_joined(activity_id: str) -> bool:
    conn = _conn()
    try:
        conn.execute("""
            UPDATE mt_galaxy_high_exposure SET joined=1 WHERE activity_id=?
        """, (activity_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ============================================================
# CLI 入口
# ============================================================

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: galaxy_db.py <init|tables|stats|seed_accounts>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'init':
        r = ensure_galaxy_tables()
        import json as _j; print(_j.dumps(r, indent=2, ensure_ascii=False))
    elif cmd == 'tables':
        conn = _conn()
        for tbl in [
            'mt_galaxy_series', 'mt_galaxy_episodes', 'mt_galaxy_accounts',
            'mt_galaxy_platform_creds', 'mt_galaxy_publish_log',
            'mt_galaxy_platform_restrict', 'mt_galaxy_high_exposure',
            'mt_galaxy_compliance_log', 'mt_galaxy_feedback_ingest',
            'mt_galaxy_daily_stats',
        ]:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  {tbl}: {cnt} rows")
        conn.close()
    elif cmd == 'stats':
        series_list = list_series()
        print(f"📺 Series: {len(series_list)}")
        for s in series_list[:5]:
            print(f"  [{s['role_type'][:8]:8s}] {s['level']:15s} | {s['title'][:40]}")
    elif cmd == 'seed_accounts':
        # 种子账号 (三平台)
        acc_id = upsert_account(
            nickname='仙女座数字教师',
            role_type='andromeda_teacher',
            douyin_uid='1222452416'
        )
        print(f"✅ 账号已创建: {acc_id}")

        # 三平台凭证
        creds = [
            ('douyin', '1222452416', None, 'password'),
            ('xiaohongshu', '5583475306', None, 'password'),
            ('bilibili', '18717895602', 'wuchenghao_15@163.com', 'password'),
        ]
        for plat, uid, login, ltype in creds:
            cid = upsert_platform_cred(
                account_id=acc_id,
                platform=plat,
                platform_uid=uid,
                login_id=login,
                login_type=ltype,
                auth_status='pending'
            )
            print(f"  ✅ {plat} cred_id={cid} (UID={uid})")
        print("⚠️  credential_json 留空, 后续扫码登录补填")

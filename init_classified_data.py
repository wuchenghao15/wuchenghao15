#!/usr/bin/env python3
"""
mt_classified_data 表初始化 + 机密等级数据注册表
================================================
对应 MT_RULE_CLASSIFICATION 机密等级与访问控制规范

三 tier (strict fail-closed):
  极密 (TOP_SECRET) → 仅 SA + VIKEY 硬件狗双因子 → 加密 + 审计
  机密 (SECRET)     → admin+ 角色                 → 加密 + 审计  
  秘密 (CONFIDENTIAL) → login+ 角色                → 可选加密 + 日志

不可加密字段（autosync 双向合并依赖）:
  所有表的 PRIMARY KEY, created_at, updated_at, data_code
"""
import os, sys, sqlite3, json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "flask-app", "database", "app.db")

def run():
    print(f"[CLASSIFIED] DB={DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # ── 建表 ──
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS mt_classified_data (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        data_code       TEXT UNIQUE NOT NULL,          -- 唯一代码, 被 classification_guard 引用
        classification  TEXT NOT NULL,                 -- 极密 / 机密 / 秘密
        data_category   TEXT,                          -- 类别: credential/firmware/key/pii/system/...
        target_table    TEXT,                          -- 加密后的目标表
        target_column   TEXT,                          -- 加密后的目标列 (NULL=整行级)
        encrypt_method  TEXT,                          -- AES-256-GCM / FERNET / HMAC_ONLY / NONE
        key_source      TEXT,                          -- VIKEY_DERIVED / SERVER_MASTER / SESSION
        encrypted_suffix TEXT DEFAULT '_enc',          -- 加密列后缀
        is_encrypted    INTEGER DEFAULT 0,             -- 0=未加密 1=已加密
        owner           TEXT,                          -- system/sa/devops/...
        notes           TEXT,
        created_at      TEXT DEFAULT (datetime('now','localtime')),
        updated_at      TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_classified_level ON mt_classified_data(classification);
    CREATE INDEX IF NOT EXISTS idx_classified_table ON mt_classified_data(target_table);
    """)
    conn.commit()

    # ── 真实机密数据 (一次性 seed) ──
    SEEDS = [
        # ── 极密 TOP_SECRET (VIKEY 双因子) ──
        ("TS_VIKEY_SPEC", "极密", "credential",    "system_vikey_config", "spec_json",   "AES-256-GCM", "VIKEY_DERIVED", "_enc", 0, "sa", "VIKEY 加密狗规格/密钥派生参数"),
        ("TS_VIKEY_KEY",  "极密", "credential",    "system_vikey_config", "vikey_priv",  "AES-256-GCM", "VIKEY_DERIVED", "_enc", 0, "sa", "VIKEY 硬件狗私钥片段"),
        ("TS_FIRMWARE",   "极密", "firmware",      "arduino_firmware",    "bin_data",    "AES-256-GCM", "VIKEY_DERIVED", "_enc", 0, "sa", "SZU100 Arduino 固件二进制"),
        ("TS_EF_PRIVKEY", "极密", "key",           "eigenflux_keys",      "private_key", "AES-256-GCM", "VIKEY_DERIVED", "_enc", 0, "sa", "EigenFlux AI 通信私钥"),

        # ── 机密 SECRET (admin+ 角色) ──
        ("S_DB_MASTER",   "机密", "credential",    "system_config",     "db_master_key",   "AES-256-GCM", "SERVER_MASTER", "_enc", 0, "devops", "DB 主密钥加密后的备份"),
        ("S_API_KEYS",    "机密", "credential",    "system_api_keys",   "api_key_value",   "AES-256-GCM", "SERVER_MASTER", "_enc", 0, "devops", "第三方 API Key"),
        ("S_VOLCENGINE",  "机密", "credential",    "system_api_keys",   "volcengine_ak",   "AES-256-GCM", "SERVER_MASTER", "_enc", 0, "devops", "火山引擎 Ark API (即梦视频)"),
        ("S_AWS_CREDS",   "机密", "credential",    "system_api_keys",   "aws_ak_sk",       "AES-256-GCM", "SERVER_MASTER", "_enc", 0, "devops", "AWS AK/SK"),
        ("S_USER_PASSWORD","机密","pii",           "users",             "password_hash",   "HMAC_ONLY",   "SERVER_MASTER", "",    0, "auth",   "用户密码 HMAC (不恢复原文)"),

        # ── 秘密 CONFIDENTIAL (login+ 角色) ──
        ("C_EMAIL",       "秘密", "pii",           "users",             "email",           "FERNET",      "SESSION",       "_enc", 0, "user",   "用户邮箱"),
        ("C_PHONE",       "秘密", "pii",           "users",             "phone",           "FERNET",      "SESSION",       "_enc", 0, "user",   "用户手机号"),
        ("C_AI_TOKEN",    "秘密", "credential",    "ai_service_tokens", "token_value",     "FERNET",      "SESSION",       "_enc", 0, "ai",     "AI 服务短期 Token"),
    ]

    existing = conn.execute("SELECT data_code FROM mt_classified_data").fetchall()
    existing_codes = set(r[0] for r in existing)
    inserted = 0
    for row in SEEDS:
        if row[0] not in existing_codes:
            conn.execute("""
                INSERT INTO mt_classified_data
                (data_code, classification, data_category, target_table, target_column,
                 encrypt_method, key_source, encrypted_suffix, is_encrypted, owner, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", row)
            inserted += 1
    conn.commit()

    # 打印汇总
    rows = conn.execute("""
        SELECT classification, COUNT(*), SUM(is_encrypted)
        FROM mt_classified_data GROUP BY classification
        ORDER BY CASE classification WHEN '极密' THEN 1 WHEN '机密' THEN 2 ELSE 3 END
    """).fetchall()
    print(f"[CLASSIFIED] mt_classified_data: {inserted} inserted, total {sum(r[1] for r in rows)} rows")
    for cls, total, enc in rows:
        print(f"  {cls}: {total} 条 (已加密 {enc})")

    # 打真实数据
    all_rows = conn.execute("""
        SELECT data_code, classification, target_table || '.' || COALESCE(target_column,'*'),
               encrypt_method, key_source, is_encrypted
        FROM mt_classified_data ORDER BY classification, data_code
    """).fetchall()
    for r in all_rows:
        print(f"  [{r[1]}] {r[0]:20s} {r[2]:35s} enc={r[3]:12s} key={r[4]:14s} done={r[5]}")

    conn.close()
    print("[CLASSIFIED] ✅ 完成")

if __name__ == "__main__":
    run()

-- 创建多因素验证所需的数据库表

-- 用户验证信息表
CREATE TABLE IF NOT EXISTS user_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    verification_type TEXT NOT NULL, -- 验证类型：roll_code, unique_code, anti_fake_code, db_id, password, vikey
    verification_value TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    UNIQUE(user_id, verification_type)
);

-- 验证码表
CREATE TABLE IF NOT EXISTS verification_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    code_type TEXT NOT NULL, -- 验证类型：roll_code, unique_code, anti_fake_code
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    is_used INTEGER DEFAULT 0,
    used_at DATETIME,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    UNIQUE(code, code_type)
);

-- Vikey硬件信息表
CREATE TABLE IF NOT EXISTS vikey_hardware (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hardware_id TEXT NOT NULL UNIQUE,
    user_id INTEGER,
    username TEXT,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 登录验证日志表
CREATE TABLE IF NOT EXISTS login_verification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    verification_type TEXT NOT NULL,
    verification_value TEXT,
    is_successful INTEGER,
    error_message TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_user_verification_user_id ON user_verification(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_codes_user_id ON verification_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_codes_code ON verification_codes(code);
CREATE INDEX IF NOT EXISTS idx_vikey_hardware_hardware_id ON vikey_hardware(hardware_id);
CREATE INDEX IF NOT EXISTS idx_login_verification_log_username ON login_verification_log(username);

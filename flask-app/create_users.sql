-- 创建用户表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    activation_key TEXT,
    reset_token TEXT,
    reset_token_expiry TIMESTAMP,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMP,
    locked_until TIMESTAMP
);

-- 插入硬件管理员用户
INSERT OR IGNORE INTO users (username, password, email, role, status, is_active) VALUES (
    'wuchenghao15',
    'LoginMe.1988',
    'wuchenghao_15@163.com',
    'hardware_admin',
    'approved',
    1
);

-- 插入超级管理员用户
INSERT OR IGNORE INTO users (username, password, email, role, status, is_active) VALUES (
    'wuchenghao16',
    'ppo900lik',
    '2@2.com',
    'super_admin',
    'approved',
    1
);

-- 插入普通用户
INSERT OR IGNORE INTO users (username, password, email, role, status, is_active) VALUES (
    'caopw',
    'xuxu2pipo',
    '1175061512@qq.com',
    'user',
    'approved',
    1
);

-- 查询插入结果
SELECT id, username, email, role, status, is_active FROM users;

-- 创建白名单 token 表
CREATE TABLE IF NOT EXISTS whitelist_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    user_id INTEGER,
    username TEXT,
    token_type TEXT NOT NULL DEFAULT 'bearer',
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,  -- 可选，用于有期限的 token
    description TEXT,  -- 可选，token 的描述
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_whitelist_tokens_token ON whitelist_tokens(token);
CREATE INDEX IF NOT EXISTS idx_whitelist_tokens_user_id ON whitelist_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_whitelist_tokens_is_active ON whitelist_tokens(is_active);

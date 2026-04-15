-- ViKey数据库初始化SQL脚本
-- 创建时间: 2025-01-19
-- 版本: v1.0.0

-- 1. 创建vikey_devices表
CREATE TABLE IF NOT EXISTS vikey_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hardware_id TEXT NOT NULL UNIQUE,
    device_type INTEGER NOT NULL DEFAULT 1,
    firmware_version TEXT,
    serial_number TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建users表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    status TEXT DEFAULT 'active',
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 创建vikey_user_bindings表
CREATE TABLE IF NOT EXISTS vikey_user_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    binding_type INTEGER DEFAULT 1,
    permissions TEXT,
    expires_at DATETIME,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES vikey_devices(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(device_id, user_id)
);

-- 4. 创建access_logs表
CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    user_id INTEGER,
    action TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES vikey_devices(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 5. 创建sessions表
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    device_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES vikey_devices(id) ON DELETE SET NULL
);

-- 6. 创建system_settings表
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type TEXT DEFAULT 'string',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_vikey_devices_hardware_id ON vikey_devices(hardware_id);
CREATE INDEX IF NOT EXISTS idx_vikey_devices_status ON vikey_devices(status);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_vikey_user_bindings_device_id ON vikey_user_bindings(device_id);
CREATE INDEX IF NOT EXISTS idx_vikey_user_bindings_user_id ON vikey_user_bindings(user_id);
CREATE INDEX IF NOT EXISTS idx_vikey_user_bindings_is_active ON vikey_user_bindings(is_active);
CREATE INDEX IF NOT EXISTS idx_access_logs_device_id ON access_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key);

-- 插入初始数据
-- 插入默认管理员用户 (密码: admin123)
INSERT OR IGNORE INTO users (username, password_hash, email, full_name, role) 
VALUES ('admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin@mtscos.com', '系统管理员', 'admin');

-- 插入测试用户 (密码: test123)
INSERT OR IGNORE INTO users (username, password_hash, email, full_name, role) 
VALUES ('test', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'test@mtscos.com', '测试用户', 'user');

-- 插入系统设置
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('vikey_max_devices_per_user', '5', 'integer', '每个用户最多绑定的ViKey设备数量'),
('vikey_session_timeout', '3600', 'integer', 'ViKey会话超时时间（秒）'),
('vikey_max_login_attempts', '5', 'integer', '最大登录尝试次数'),
('vikey_lockout_duration', '900', 'integer', '账户锁定时间（秒）'),
('vikey_require_device_verification', '1', 'boolean', '是否要求设备验证'),
('vikey_auto_cleanup_sessions', '1', 'boolean', '是否自动清理过期会话'),
('vikey_log_level', 'info', 'string', '日志级别 (debug, info, warning, error)'),
('vikey_encryption_enabled', '1', 'boolean', '是否启用数据加密');

-- 插入示例ViKey设备
INSERT OR IGNORE INTO vikey_devices (hardware_id, device_type, firmware_version, serial_number) 
VALUES ('DEMO-VIKEY-001', 1, 'v2.1.3', 'VK2024111701');
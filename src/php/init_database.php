<?php
/**
 * ViKey数据库初始化脚本
 * 创建SQLite数据库和必要的表结构
 * 
 * 创建时间: 2025-01-19
 * 版本: v1.0.0
 */

// 设置错误报告
error_reporting(E_ALL);
ini_set('display_errors', 1);

// 设置时区
date_default_timezone_set('Asia/Shanghai');

// 数据库文件路径
define('DB_PATH', __DIR__ . '/../Database/vikey_system.db');

try {
    // 创建数据库目录（如果不存在）
    $dbDir = dirname(DB_PATH);
    if (!is_dir($dbDir)) {
        mkdir($dbDir, 0755, true);
    }
    
    // 连接SQLite数据库
    $pdo = new PDO('sqlite:' . DB_PATH);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    
    echo "数据库连接成功！\n";
    
    // 创建表结构
    createTables($pdo);
    
    // 插入初始数据
    insertInitialData($pdo);
    
    echo "ViKey数据库初始化完成！\n";
    echo "数据库文件位置: " . DB_PATH . "\n";
    
} catch (PDOException $e) {
    echo "数据库初始化失败: " . $e->getMessage() . "\n";
    exit(1);
}

/**
 * 创建表结构
 */
function createTables($pdo) {
    echo "正在创建表结构...\n";
    
    // 1. 创建vikey_devices表
    $sql = "CREATE TABLE IF NOT EXISTS vikey_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hardware_id VARCHAR(255) NOT NULL UNIQUE,
        device_type INTEGER NOT NULL DEFAULT 1,
        firmware_version VARCHAR(100),
        serial_number VARCHAR(100),
        status VARCHAR(20) DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )";
    $pdo->exec($sql);
    echo "✓ vikey_devices表创建成功\n";
    
    // 2. 创建users表
    $sql = "CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        full_name VARCHAR(255),
        role VARCHAR(50) DEFAULT 'user',
        status VARCHAR(20) DEFAULT 'active',
        last_login DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )";
    $pdo->exec($sql);
    echo "✓ users表创建成功\n";
    
    // 3. 创建vikey_user_bindings表
    $sql = "CREATE TABLE IF NOT EXISTS vikey_user_bindings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        binding_type INTEGER DEFAULT 1,
        permissions TEXT,
        expires_at DATETIME,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES vikey_devices(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(device_id, user_id)
    )";
    $pdo->exec($sql);
    echo "✓ vikey_user_bindings表创建成功\n";
    
    // 4. 创建access_logs表
    $sql = "CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        user_id INTEGER,
        action VARCHAR(100) NOT NULL,
        ip_address VARCHAR(45),
        user_agent TEXT,
        success BOOLEAN DEFAULT 1,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES vikey_devices(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )";
    $pdo->exec($sql);
    echo "✓ access_logs表创建成功\n";
    
    // 5. 创建sessions表
    $sql = "CREATE TABLE IF NOT EXISTS sessions (
        id VARCHAR(255) PRIMARY KEY,
        user_id INTEGER NOT NULL,
        device_id INTEGER,
        ip_address VARCHAR(45),
        user_agent TEXT,
        expires_at DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (device_id) REFERENCES vikey_devices(id) ON DELETE SET NULL
    )";
    $pdo->exec($sql);
    echo "✓ sessions表创建成功\n";
    
    // 6. 创建system_settings表
    $sql = "CREATE TABLE IF NOT EXISTS system_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key VARCHAR(100) NOT NULL UNIQUE,
        setting_value TEXT,
        setting_type VARCHAR(20) DEFAULT 'string',
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )";
    $pdo->exec($sql);
    echo "✓ system_settings表创建成功\n";
    
    // 创建索引
    createIndexes($pdo);
}

/**
 * 创建索引
 */
function createIndexes($pdo) {
    echo "正在创建索引...\n";
    
    $indexes = [
        'CREATE INDEX IF NOT EXISTS idx_vikey_devices_hardware_id ON vikey_devices(hardware_id)',
        'CREATE INDEX IF NOT EXISTS idx_vikey_devices_status ON vikey_devices(status)',
        'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
        'CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)',
        'CREATE INDEX IF NOT EXISTS idx_vikey_user_bindings_device_id ON vikey_user_bindings(device_id)',
        'CREATE INDEX IF NOT EXISTS idx_vikey_user_bindings_user_id ON vikey_user_bindings(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_vikey_user_bindings_is_active ON vikey_user_bindings(is_active)',
        'CREATE INDEX IF NOT EXISTS idx_access_logs_device_id ON access_logs(device_id)',
        'CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)',
        'CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key)'
    ];
    
    foreach ($indexes as $indexSql) {
        $pdo->exec($indexSql);
    }
    
    echo "✓ 索引创建成功\n";
}

/**
 * 插入初始数据
 */
function insertInitialData($pdo) {
    echo "正在插入初始数据...\n";
    
    // 1. 插入默认管理员用户
    $adminPasswordHash = password_hash('admin123', PASSWORD_DEFAULT);
    $sql = "INSERT OR IGNORE INTO users (username, password_hash, email, full_name, role) 
            VALUES (?, ?, ?, ?, ?)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(['admin', $adminPasswordHash, 'admin@mtscos.com', '系统管理员', 'admin']);
    echo "✓ 默认管理员用户创建成功 (用户名: admin, 密码: admin123)\n";
    
    // 2. 插入测试用户
    $testPasswordHash = password_hash('test123', PASSWORD_DEFAULT);
    $sql = "INSERT OR IGNORE INTO users (username, password_hash, email, full_name, role) 
            VALUES (?, ?, ?, ?, ?)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(['test', $testPasswordHash, 'test@mtscos.com', '测试用户', 'user']);
    echo "✓ 测试用户创建成功 (用户名: test, 密码: test123)\n";
    
    // 3. 插入系统设置
    $settings = [
        ['vikey_max_devices_per_user', '5', 'integer', '每个用户最多绑定的ViKey设备数量'],
        ['vikey_session_timeout', '3600', 'integer', 'ViKey会话超时时间（秒）'],
        ['vikey_max_login_attempts', '5', 'integer', '最大登录尝试次数'],
        ['vikey_lockout_duration', '900', 'integer', '账户锁定时间（秒）'],
        ['vikey_require_device_verification', '1', 'boolean', '是否要求设备验证'],
        ['vikey_auto_cleanup_sessions', '1', 'boolean', '是否自动清理过期会话'],
        ['vikey_log_level', 'info', 'string', '日志级别 (debug, info, warning, error)'],
        ['vikey_encryption_enabled', '1', 'boolean', '是否启用数据加密']
    ];
    
    $sql = "INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description) 
            VALUES (?, ?, ?, ?)";
    $stmt = $pdo->prepare($sql);
    
    foreach ($settings as $setting) {
        $stmt->execute($setting);
    }
    echo "✓ 系统设置插入成功\n";
    
    // 4. 创建示例ViKey设备（用于测试）
    $sql = "INSERT OR IGNORE INTO vikey_devices (hardware_id, device_type, firmware_version, serial_number) 
            VALUES (?, ?, ?, ?)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(['DEMO-VIKEY-001', 1, 'v2.1.3', 'VK2024111701']);
    echo "✓ 示例ViKey设备创建成功\n";
    
    // 5. 绑定示例设备到管理员用户
    $deviceId = $pdo->lastInsertId();
    $adminId = $pdo->query("SELECT id FROM users WHERE username = 'admin'")->fetchColumn();
    
    if ($deviceId && $adminId) {
        $sql = "INSERT OR IGNORE INTO vikey_user_bindings (device_id, user_id, binding_type, permissions) 
                VALUES (?, ?, ?, ?)";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$deviceId, $adminId, 1, 'admin']);
        echo "✓ 示例设备绑定成功\n";
    }
    
    echo "✓ 初始数据插入完成\n";
}

/**
 * 显示数据库信息
 */
function showDatabaseInfo($pdo) {
    echo "\n=== 数据库信息 ===\n";
    
    // 显示表信息
    $tables = $pdo->query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")->fetchAll();
    echo "数据库表:\n";
    foreach ($tables as $table) {
        $count = $pdo->query("SELECT COUNT(*) FROM " . $table['name'])->fetchColumn();
        echo "  - {$table['name']}: {$count} 条记录\n";
    }
    
    // 显示数据库文件大小
    if (file_exists(DB_PATH)) {
        $size = filesize(DB_PATH);
        echo "\n数据库文件大小: " . formatBytes($size) . "\n";
    }
    
    echo "\n初始化完成！\n";
}

/**
 * 格式化字节大小
 */
function formatBytes($bytes, $precision = 2) {
    $units = array('B', 'KB', 'MB', 'GB', 'TB');
    
    for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
        $bytes /= 1024;
    }
    
    return round($bytes, $precision) . ' ' . $units[$i];
}

// 显示数据库信息
showDatabaseInfo($pdo);
?>
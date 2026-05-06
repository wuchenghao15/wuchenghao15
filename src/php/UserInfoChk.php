<?php
// UserInfoChk.php - 用户登录验证处理文件
// 版本: 1.0.0
// 创建时间: 2025-11-08

// 设置响应头
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *'); // 在生产环境中应该限制具体域名
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// 日志记录函数
function logLoginAttempt($username, $success, $ip, $userAgent) {
    $logFile = '../Logs/login_attempts.log';
    $timestamp = date('Y-m-d H:i:s');
    $status = $success ? 'SUCCESS' : 'FAILED';
    $logEntry = "[$timestamp] $status - Username: $username, IP: $ip, User-Agent: $userAgent\n";
    
    // 确保日志目录存在
    if (!file_exists(dirname($logFile))) {
        mkdir(dirname($logFile), 0755, true);
    }
    
    // 写入日志
    file_put_contents($logFile, $logEntry, FILE_APPEND);
}

// 模拟用户数据库（实际项目中应连接真实数据库）
$users = [
    'admin' => [
        'password' => 'Admin123456', // 实际项目中应存储哈希密码
        'role' => 'admin',
        'name' => '系统管理员'
    ],
    'test_user' => [
        'password' => 'Test@123456',
        'role' => 'user',
        'name' => '测试用户'
    ],
    'readonly' => [
        'password' => 'Readonly@123',
        'role' => 'readonly',
        'name' => '只读用户'
    ]
];

// 获取客户端信息
$clientIP = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$userAgent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';

// 处理POST请求
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // 获取并验证输入数据
    $data = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($data['username']) || !isset($data['password'])) {
        logLoginAttempt('unknown', false, $clientIP, $userAgent);
        echo json_encode([
            'success' => false,
            'message' => '缺少必要的登录参数',
            'error_code' => 'MISSING_PARAMS'
        ]);
        exit;
    }
    
    $username = trim($data['username']);
    $password = $data['password'];
    $rememberMe = isset($data['rememberMe']) ? (bool)$data['rememberMe'] : false;
    
    // 验证用户名和密码
    if (isset($users[$username]) && $users[$username]['password'] === $password) {
        // 登录成功
        logLoginAttempt($username, true, $clientIP, $userAgent);
        
        // 生成会话token（简化版，实际项目中应使用更安全的方式）
        $token = bin2hex(random_bytes(16));
        
        // 返回成功响应
        echo json_encode([
            'success' => true,
            'message' => '登录成功',
            'token' => $token,
            'user' => [
                'username' => $username,
                'name' => $users[$username]['name'],
                'role' => $users[$username]['role']
            ],
            'redirect' => 'dashboard.html'
        ]);
    } else {
        // 登录失败
        logLoginAttempt($username, false, $clientIP, $userAgent);
        echo json_encode([
            'success' => false,
            'message' => '用户名或密码错误',
            'error_code' => 'INVALID_CREDENTIALS'
        ]);
    }
} else {
    // 不是POST请求
    logLoginAttempt('unknown', false, $clientIP, $userAgent);
    echo json_encode([
        'success' => false,
        'message' => '只允许POST请求',
        'error_code' => 'INVALID_METHOD'
    ]);
}

// 更新机制触发点 - 可以在这里添加检查更新的逻辑
function checkForUpdates() {
    // 这里可以实现检查系统更新的逻辑
    // 例如检查远程服务器上的版本文件，与本地版本比较
    return false; // 当前没有更新
}

// 调用检查更新函数（可以根据需要调整调用时机）
// checkForUpdates();
?>
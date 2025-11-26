<?php
// MTSCOS 配置文件
// 用于存储动态设置和系统参数

return [
    // 系统设置
    'system' => [
        'name' => 'MTSCOS AI Project',
        'version' => '1.0.0',
        'debug' => true,
    ],
    
    // 管理员设置
    'admin' => [
        'auto_refresh' => 60, // 秒
        'theme' => 'light', // light, dark, auto
        'sidebar_collapsed' => false,
    ],
    
    // 监控设置
    'monitoring' => [
        'enabled' => true,
        'check_interval' => 60, // 秒
        'log_level' => 'info', // debug, info, warning, error
    ],
    
    // 文件设置
    'files' => [
        'backup_dir' => '../Backups/auto_collected',
        'log_dir' => '../Logs',
    ],
];
?>

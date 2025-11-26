<?php
/**
 * 统一数据库管理系统
 * 负责处理所有数据库操作，包括用户认证、配置管理、日志记录等
 * 支持异步同步、多备份机制和错误处理
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');

// 处理预检请求
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// 引入配置文件
require_once __DIR__ . '/config.php
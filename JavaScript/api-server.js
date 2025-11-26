/**
 * MTSCOS API服务器 - 增强版
 * 提供完整的前后端握手机制和API接口
 * 作者: Chenghao Wu
 * 版本: 2.0.0
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 配置
const PORT = process.env.PORT || 3001;
const BASE_DIR = path.join(__dirname, '..');
const HTML_DIR = path.join(__dirname, '../HTML');
const JS_DIR = path.join(__dirname, '../JavaScript');
const CSS_DIR = path.join(__dirname, '../CSS');

// 会话存储
const sessions = new Map();
const apiKeys = new Map();
const rateLimitMap = new Map();

// 服务器状态
let serverStatus = {
    status: 'running',
    uptime: Date.now(),
    version: '1.3.0',
    lastHealthCheck: Date.now(),
    activeConnections: 0,
    totalRequests: 0,
    errorCount: 0
};

// MIME类型映射
const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf'
};

/**
 * 生成会话ID
 */
function generateSessionId() {
    return crypto.randomBytes(32).toString('hex');
}

/**
 * 生成API密钥
 */
function generateApiKey() {
    return crypto.randomBytes(16).toString('hex');
}

/**
 * 验证API密钥
 */
function validateApiKey(req) {
    const apiKey = req.headers['x-api-key'];
    if (!apiKey) return false;
    
    const keyData = apiKeys.get(apiKey);
    if (!keyData) return false;
    
    // 检查密钥是否过期
    if (Date.now() > keyData.expires) {
        apiKeys.delete(apiKey);
        return false;
    }
    
    return true;
}

/**
 * 速率限制检查
 */
function checkRateLimit(clientId, limit = 100, window = 60000) {
    const now = Date.now();
    const clientData = rateLimitMap.get(clientId) || { count: 0, resetTime: now + window };
    
    if (now > clientData.resetTime) {
        clientData.count = 0;
        clientData.resetTime = now + window;
    }
    
    clientData.count++;
    rateLimitMap.set(clientId, clientData);
    
    return clientData.count <= limit;
}

/**
 * 获取客户端IP
 */
function getClientIP(req) {
    return req.headers['x-forwarded-for'] || 
           req.connection.remoteAddress || 
           req.socket.remoteAddress ||
           (req.connection.socket ? req.connection.socket.remoteAddress : null);
}

/**
 * CORS处理
 */
function handleCORS(res, origin = '*') {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key, X-Session-ID');
    res.setHeader('Access-Control-Max-Age', '86400');
}

/**
 * 发送JSON响应
 */
function sendJSON(res, data, statusCode = 200) {
    res.writeHead(statusCode, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data, null, 2));
}

/**
 * 发送错误响应
 */
function sendError(res, message, statusCode = 400, error = null) {
    serverStatus.errorCount++;
    const errorData = {
        success: false,
        error: message,
        timestamp: new Date().toISOString(),
        statusCode: statusCode
    };
    
    if (error) {
        errorData.details = error.message;
    }
    
    sendJSON(res, errorData, statusCode);
}

/**
 * API握手处理
 */
function handleHandshake(req, res) {
    const clientId = getClientIP(req);
    
    // 检查速率限制
    if (!checkRateLimit(clientId, 10, 60000)) {
        return sendError(res, '请求过于频繁，请稍后再试', 429);
    }
    
    // 生成新的会话和API密钥
    const sessionId = generateSessionId();
    const apiKey = generateApiKey();
    
    // 存储会话信息
    sessions.set(sessionId, {
        clientId: clientId,
        createdAt: Date.now(),
        lastActivity: Date.now(),
        userAgent: req.headers['user-agent'],
        authenticated: false
    });
    
    // 存储API密钥
    apiKeys.set(apiKey, {
        sessionId: sessionId,
        createdAt: Date.now(),
        expires: Date.now() + 24 * 60 * 60 * 1000 // 24小时
    });
    
    sendJSON(res, {
        success: true,
        message: '握手成功',
        data: {
            sessionId: sessionId,
            apiKey: apiKey,
            serverVersion: serverStatus.version,
            timestamp: new Date().toISOString()
        }
    });
}

/**
 * 状态检查API
 */
function handleStatus(req, res) {
    const now = Date.now();
    const uptime = now - serverStatus.uptime;
    
    sendJSON(res, {
        success: true,
        data: {
            status: serverStatus.status,
            uptime: uptime,
            version: serverStatus.version,
            lastHealthCheck: serverStatus.lastHealthCheck,
            activeConnections: serverStatus.activeConnections,
            totalRequests: serverStatus.totalRequests,
            errorCount: serverStatus.errorCount,
            activeSessions: sessions.size,
            activeApiKeys: apiKeys.size,
            timestamp: new Date().toISOString()
        }
    });
}

/**
 * 心跳检测API
 */
function handleHeartbeat(req, res) {
    const sessionId = req.headers['x-session-id'];
    
    if (sessionId && sessions.has(sessionId)) {
        const session = sessions.get(sessionId);
        session.lastActivity = Date.now();
        sessions.set(sessionId, session);
    }
    
    sendJSON(res, {
        success: true,
        message: 'heartbeat',
        timestamp: new Date().toISOString()
    });
}

/**
 * 认证API
 */
function handleAuth(req, res) {
    let body = '';
    
    req.on('data', chunk => {
        body += chunk.toString();
    });
    
    req.on('end', () => {
        try {
            const data = JSON.parse(body);
            const sessionId = req.headers['x-session-id'];
            
            if (!sessionId || !sessions.has(sessionId)) {
                return sendError(res, '无效的会话', 401);
            }
            
            // 这里应该实现真实的认证逻辑
            // 目前为演示目的，简单验证
            if (data.username && data.password) {
                const session = sessions.get(sessionId);
                session.authenticated = true;
                session.authTime = Date.now();
                sessions.set(sessionId, session);
                
                sendJSON(res, {
                    success: true,
                    message: '认证成功',
                    data: {
                        authenticated: true,
                        sessionId: sessionId
                    }
                });
            } else {
                sendError(res, '认证失败', 401);
            }
        } catch (error) {
            sendError(res, '请求数据格式错误', 400, error);
        }
    });
}

/**
 * 清理过期会话
 */
function cleanupExpiredSessions() {
    const now = Date.now();
    const expiredSessions = [];
    
    sessions.forEach((session, sessionId) => {
        if (now - session.lastActivity > 30 * 60 * 1000) { // 30分钟
            expiredSessions.push(sessionId);
        }
    });
    
    expiredSessions.forEach(sessionId => {
        sessions.delete(sessionId);
    });
    
    const expiredKeys = [];
    apiKeys.forEach((keyData, apiKey) => {
        if (now > keyData.expires) {
            expiredKeys.push(apiKey);
        }
    });
    
    expiredKeys.forEach(apiKey => {
        apiKeys.delete(apiKey);
    });
}

/**
 * 处理静态文件
 */
function handleStaticFile(req, res) {
    let filePath = req.url === '/' ? '/index.html' : req.url;
    
    // 处理特殊路由
    const routeMap = {
        '/about.html': '/HTML/about.html',
        '/news.html': '/HTML/about/news.html',
        '/team.html': '/HTML/about/team.html',
        '/history.html': '/HTML/about/history.html',
        '/company.html': '/HTML/about/company.html'
    };
    
    if (routeMap[filePath]) {
        filePath = routeMap[filePath];
    } else if (filePath.startsWith('/CSS/')) {
        filePath = path.join(__dirname, '../' + filePath);
    } else if (filePath.startsWith('/JavaScript/')) {
        filePath = path.join(__dirname, '../' + filePath);
    } else if (filePath.startsWith('/Encrypted_JS/')) {
        filePath = path.join(__dirname, '../' + filePath);
    } else if (!filePath.includes('/HTML/') && !filePath.includes('/CSS/') && 
               !filePath.includes('/JavaScript/') && !filePath.includes('/Encrypted_JS/')) {
        filePath = path.join(HTML_DIR, filePath);
    } else {
        filePath = path.join(__dirname, '../' + filePath);
    }
    
    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'text/plain';
    
    fs.readFile(filePath, (err, content) => {
        if (err) {
            console.error(`[api-server.js] 读取文件错误: ${err.message}`);
            if (err.code === 'ENOENT') {
                sendError(res, '页面未找到', 404);
            } else {
                sendError(res, '服务器内部错误', 500);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content);
        }
    });
}

/**
 * 主请求处理器
 */
const server = http.createServer((req, res) => {
    serverStatus.totalRequests++;
    serverStatus.activeConnections++;
    
    const clientIP = getClientIP(req);
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} - ${clientIP}`);
    
    // CORS处理
    handleCORS(res);
    
    // 处理OPTIONS请求
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end().catch(error => console.error(`[api-server.js] res.end failed:`, error));
        return;
    }
    
    // API路由处理
    if (req.url.startsWith('/api/')) {
        switch (req.url) {
            case '/api/handshake':
                if (req.method === 'POST') {
                    handleHandshake(req, res);
                } else {
                    sendError(res, '方法不允许', 405);
                }
                break;
                
            case '/api/status':
                if (req.method === 'GET') {
                    handleStatus(req, res);
                } else {
                    sendError(res, '方法不允许', 405);
                }
                break;
                
            case '/api/heartbeat':
                if (req.method === 'POST') {
                    handleHeartbeat(req, res);
                } else {
                    sendError(res, '方法不允许', 405);
                }
                break;
                
            case '/api/auth':
                if (req.method === 'POST') {
                    handleAuth(req, res);
                } else {
                    sendError(res, '方法不允许', 405);
                }
                break;
                
            case '/api/csrf-token':
                if (req.method === 'GET') {
                    sendJSON(res, {
                        success: true,
                        csrfToken: crypto.randomBytes(32).toString('hex'),
                        timestamp: new Date().toISOString()
                    });
                } else {
                    sendError(res, '方法不允许', 405);
                }
                break;
                
            default:
                sendError(res, 'API端点不存在', 404);
        }
    } else {
        // 静态文件处理
        handleStaticFile(req, res);
    }
    
    serverStatus.activeConnections--;
});

/**
 * 启动服务器
 */
server.listen(PORT, '0.0.0.0', () => {
    console.log(`[${new Date().toISOString()}] MTSCOS API服务器启动成功`);
    console.log(`[${new Date().toISOString()}] 服务地址: http://0.0.0.0:${PORT}`);
    console.log(`[${new Date().toISOString()}] 版本: ${serverStatus.version}`);
    console.log(`[${new Date().toISOString()}] 支持的API端点:`);
    console.log(`  - POST /api/handshake   - 前后端握手`);
    console.log(`  - GET  /api/status      - 服务器状态`);
    console.log(`  - POST /api/heartbeat   - 心跳检测`);
    console.log(`  - POST /api/auth        - 用户认证`);
});

/**
 * 错误处理
 */
server.on('error', (err) => {
    console.error(`[api-server.js] [${new Date().toISOString()}] 服务器错误: ${err.message}`);
    serverStatus.errorCount++;
});

/**
 * 定期清理任务
 */
setInterval(() => {
    cleanupExpiredSessions();
    serverStatus.lastHealthCheck = Date.now().catch(error => console.error(`[api-server.js] Date.now failed:`, error));
    console.log(`[${new Date().toISOString()}] 定期清理完成 - 活跃会话: ${sessions.size}, API密钥: ${apiKeys.size}`);
}, 5 * 60 * 1000); // 每5分钟清理一次

/**
 * 优雅关闭
 */
process.on('SIGTERM', () => {
    console.log(`[${new Date().toISOString()}] 收到SIGTERM信号，开始优雅关闭...`);
    server.close(() => {
        console.log(`[${new Date().toISOString()}] 服务器已关闭`);
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log(`[${new Date().toISOString()}] 收到SIGINT信号，开始优雅关闭...`);
    server.close(() => {
        console.log(`[${new Date().toISOString()}] 服务器已关闭`);
        process.exit(0);
    });
});

console.log(`[${new Date().toISOString()}] MTSCOS API服务器初始化中...`);
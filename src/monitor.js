/**
 * MTSCOS AI 项目管理系统 - 监控进程
 * 监控客户端异常错误并自动记录日志系统
 */

const https = require('https');
const fs = require('fs');
const WebSocket = require('ws');
const crypto = require('crypto');
const { DataAPI } = require('./database/db');

// 加载SSL证书
const options = {
    key: fs.readFileSync('./certs/key.pem'),
    cert: fs.readFileSync('./certs/cert.pem')
};

// 创建HTTPS服务器
const server = https.createServer(options, (req, res) => {
    if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('MTSCOS AI Monitor Service');
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

// 创建WebSocket服务器
const wss = new WebSocket.Server({ server, path: '/ws' });

// 客户端连接管理
const clients = new Map();

// 日志系统
const logs = [];

// 启动服务器
const PORT = 8443;
server.listen(PORT, () => {
    console.log(`监控进程启动成功，监听端口: ${PORT}`);
    console.log(`WebSocket地址: wss://localhost:${PORT}/ws`);
});

// 处理客户端连接
wss.on('connection', (ws, req) => {
    // 生成客户端ID
    const clientId = crypto.randomBytes(16).toString('hex');
    clients.set(clientId, {
        ws: ws,
        connectedAt: new Date().toISOString(),
        ip: req.socket.remoteAddress
    });

    console.log(`客户端连接成功: ${clientId}, IP: ${req.socket.remoteAddress}`);

    // 发送初始化消息
    ws.send(JSON.stringify({
        type: 'INIT',
        data: {
            clientId: clientId,
            message: '监控连接已建立'
        }
    }));

    // 处理客户端消息
ws.on('message', async (message) => {
    try {
        const data = JSON.parse(message);
        await handleClientMessage(clientId, data);
    } catch (error) {
        console.error('解析客户端消息失败:', error);
    }
});

    // 处理客户端断开连接
    ws.on('close', () => {
        clients.delete(clientId);
        console.log(`客户端断开连接: ${clientId}`);
    });

    // 处理客户端错误
    ws.on('error', (error) => {
        console.error(`客户端错误: ${clientId}`, error);
        clients.delete(clientId);
    });
});

// 处理客户端消息
async function handleClientMessage(clientId, data) {
    console.log(`收到客户端消息: ${clientId}`, data.type);

    switch (data.type) {
        case 'INIT_STATUS':
            await handleInitStatus(clientId, data.data);
            break;
        case 'ERROR_REPORT':
            await handleErrorReport(clientId, data.data);
            break;
        case 'HEARTBEAT':
            handleHeartbeat(clientId, data.data);
            break;
        default:
            console.log(`未知消息类型: ${data.type}`);
    }
}

// 处理初始化状态
async function handleInitStatus(clientId, status) {
    console.log(`客户端初始化状态: ${clientId}`, status);

    // 记录初始化状态
    const initLog = {
        type: 'INIT_STATUS',
        clientId: clientId,
        data: status,
        timestamp: new Date().toISOString()
    };
    logs.push(initLog);

    // 保存到数据库
    try {
        let initLogs = await DataAPI.getConfig('monitor.initLogs') || [];
        if (!Array.isArray(initLogs)) {
            initLogs = [];
        }
        initLogs.push(initLog);
        
        // 只保留最近30天的日志
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        const filteredLogs = initLogs.filter(log => {
            const logDate = new Date(log.timestamp);
            return logDate > thirtyDaysAgo;
        });
        
        await DataAPI.setConfig('monitor.initLogs', filteredLogs, 'json', '监控初始化日志');
        console.log('初始化状态已保存到数据库');
    } catch (error) {
        console.error('保存初始化状态到数据库失败:', error);
    }

    // 发送确认消息
    const client = clients.get(clientId);
    if (client) {
        client.ws.send(JSON.stringify({
            type: 'INIT_CONFIRMED',
            data: {
                message: '初始化状态已收到',
                timestamp: new Date().toISOString()
            }
        }));
    }
}

// 处理错误报告
async function handleErrorReport(clientId, errorData) {
    console.error(`客户端错误报告: ${clientId}`, errorData);

    // 分析错误
    const errorAnalysis = analyzeError(errorData);

    // 记录错误
    const errorLog = {
        type: 'ERROR_REPORT',
        clientId: clientId,
        error: errorData,
        analysis: errorAnalysis,
        timestamp: new Date().toISOString()
    };

    logs.push(errorLog);

    // 保存错误到数据库
    await saveErrorToDatabase(errorLog);

    // 发送确认消息
    const client = clients.get(clientId);
    if (client) {
        client.ws.send(JSON.stringify({
            type: 'ERROR_CONFIRMED',
            data: {
                message: '错误报告已收到',
                analysis: errorAnalysis,
                timestamp: new Date().toISOString()
            }
        }));
    }
}

// 处理心跳
function handleHeartbeat(clientId, data) {
    // 发送心跳响应
    const client = clients.get(clientId);
    if (client) {
        client.ws.send(JSON.stringify({
            type: 'HEARTBEAT_RESPONSE',
            data: {
                timestamp: new Date().toISOString()
            }
        }));
    }
}

// 分析错误
function analyzeError(errorData) {
    // 模拟AI分析过程
    const errorType = detectErrorType(errorData.message);
    const severity = assessSeverity(errorData.message);
    const suggestion = generateSuggestion(errorData.message);

    return {
        errorType: errorType,
        severity: severity,
        suggestion: suggestion,
        confidence: Math.random() * 0.3 + 0.7 // 70-100% 置信度
    };
}

// 检测错误类型
function detectErrorType(errorMessage) {
    const errorPatterns = {
        'SyntaxError': ['syntax', 'unexpected', 'token'],
        'ReferenceError': ['reference', 'is not defined'],
        'TypeError': ['type', 'cannot read property', 'is not a function'],
        'NetworkError': ['network', 'fetch', 'timeout', 'connection'],
        'SecurityError': ['security', 'permission', 'denied'],
        'UnknownError': []
    };

    for (const [type, patterns] of Object.entries(errorPatterns)) {
        if (patterns.some(pattern => errorMessage.toLowerCase().includes(pattern))) {
            return type;
        }
    }
    return 'UnknownError';
}

// 评估错误严重程度
function assessSeverity(errorMessage) {
    const severePatterns = ['fatal', 'critical', 'crash', 'security'];
    const mediumPatterns = ['error', 'warning', 'timeout'];
    const lowPatterns = ['info', 'debug', 'notice'];

    if (severePatterns.some(pattern => errorMessage.toLowerCase().includes(pattern))) {
        return 'High';
    } else if (mediumPatterns.some(pattern => errorMessage.toLowerCase().includes(pattern))) {
        return 'Medium';
    } else if (lowPatterns.some(pattern => errorMessage.toLowerCase().includes(pattern))) {
        return 'Low';
    }
    return 'Medium';
}

// 生成错误处理建议
function generateSuggestion(errorMessage) {
    const suggestions = {
        'SyntaxError': '检查代码语法，特别是括号、引号等配对符号',
        'ReferenceError': '检查变量是否已定义，或作用域是否正确',
        'TypeError': '检查变量类型是否正确，或方法是否存在',
        'NetworkError': '检查网络连接，或API端点是否可访问',
        'SecurityError': '检查权限设置，或CORS配置是否正确',
        'UnknownError': '查看详细错误信息，或检查浏览器控制台'
    };

    const errorType = detectErrorType(errorMessage);
    return suggestions[errorType] || suggestions['UnknownError'];
}

// 保存错误到数据库
async function saveErrorToDatabase(errorLog) {
    try {
        // 从数据库获取现有日志
        let errorLogs = await DataAPI.getConfig('monitor.errorLogs') || [];
        
        // 确保是数组格式
        if (!Array.isArray(errorLogs)) {
            errorLogs = [];
        }
        
        // 添加新日志
        errorLogs.push(errorLog);
        
        // 只保留最近30天的日志
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        const filteredLogs = errorLogs.filter(log => {
            const logDate = new Date(log.timestamp);
            return logDate > thirtyDaysAgo;
        });
        
        // 保存到数据库
        await DataAPI.setConfig('monitor.errorLogs', filteredLogs, 'json', '监控错误日志');
        console.log('错误日志已保存到数据库');
        
        return true;
    } catch (error) {
        console.error('保存错误日志到数据库失败:', error);
        return false;
    }
}

// 上传错误到数据库
async function uploadErrorToDatabase(errorLog) {
    // 直接调用saveErrorToDatabase函数，实现真正的数据库上传
    await saveErrorToDatabase(errorLog);
}

// 定期清理过期日志
setInterval(() => {
    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    // 清理内存中的日志
    const filteredLogs = logs.filter(log => {
        const logDate = new Date(log.timestamp);
        return logDate > sevenDaysAgo;
    });

    logs.length = 0;
    logs.push(...filteredLogs);

    console.log(`清理过期日志，剩余日志数量: ${logs.length}`);
}, 24 * 60 * 60 * 1000); // 每24小时清理一次

// 处理服务器错误
server.on('error', (error) => {
    console.error('监控进程错误:', error);
});

// 处理进程终止信号
process.on('SIGINT', () => {
    console.log('收到终止信号，正在关闭监控进程...');
    server.close(() => {
        console.log('监控进程已关闭');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('收到终止信号，正在关闭监控进程...');
    server.close(() => {
        console.log('监控进程已关闭');
        process.exit(0);
    });
});

module.exports = { server, wss };

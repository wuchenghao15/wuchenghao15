// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 请求日志中间件
 * 记录所有API请求
 */

const fs = require('fs');
const path = require('path');

// 确保日志目录存在
const LOG_DIR = path.join(__dirname, '../../../Logs');
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

/**
 * 请求日志中间件
 */
const requestLoggerMiddleware = (req, res, next) => {
    const startTime = Date.now();
    
    // 检查res对象是否存在
    if (!res || typeof res.end !== 'function') {
        next();
        return;
    }
    
    // 拦截响应结束事件
    const originalEnd = res.end;
    res.end = function(...args) {
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        // 构建请求日志
        const logData = {
            method: req.method,
            url: req.url,
            statusCode: res.statusCode,
            responseTime: responseTime,
            ip: req.ip,
            userAgent: req.headers['user-agent'],
            contentType: req.headers['content-type'],
            contentLength: res.get('content-length'),
            timestamp: new Date().toISOString()
        };
        
        // 控制台输出
        const statusColor = res.statusCode >= 500 ? '\x1b[31m' : 
                           res.statusCode >= 400 ? '\x1b[33m' : 
                           '\x1b[32m';
        console.log(`${statusColor}${logData.timestamp} ${logData.method} ${logData.url} ${logData.statusCode} ${logData.responseTime}ms${'\x1b[0m'}`);
        
        // 文件输出
        try {
            const logFile = path.join(LOG_DIR, 'request.log');
            fs.appendFileSync(logFile, JSON.stringify(logData) + '\n', { encoding: 'utf8' });
        } catch (error) {
            console.error('日志写入失败:', error);
        }
        
        originalEnd.apply(this, args);
    };
    
    next();
};

module.exports = requestLoggerMiddleware;
/**
 * MTSCOS AI 系统 - 错误处理中间件
 * 用于统一处理系统错误
 */

const logger = require('./logger');

// 全局错误处理中间件
const errorHandler = (err, req, res, next) => {
    // 记录错误日志
    logger.error('系统错误', {
        error: err.message,
        stack: err.stack,
        url: req.url,
        method: req.method,
        ip: req.ip
    });
    
    // 定义错误响应格式
    const errorResponse = {
        status: 'error',
        message: err.message || '服务器内部错误',
        timestamp: new Date().toISOString(),
        path: req.url
    };
    
    // 设置HTTP状态码
    const statusCode = err.statusCode || 500;
    
    // 返回错误响应
    res.status(statusCode).json(errorResponse);
};

// 404错误处理中间件
const notFoundHandler = (req, res, next) => {
    const err = new Error('请求的资源不存在');
    err.statusCode = 404;
    next(err);
};

module.exports = {
    errorHandler,
    notFoundHandler
};

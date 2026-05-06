/**
 * MTSCOS AI 系统 - 日志模块
 * 用于记录系统日志
 */

const fs = require('fs');
const path = require('path');

class Logger {
    constructor() {
        this.logDir = path.join(__dirname, '..', 'Logs');
        this.ensureLogDirectory();
        this.logLevel = process.env.LOG_LEVEL || 'info';
    }
    
    // 确保日志目录存在
    ensureLogDirectory() {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }
    
    // 生成日志文件名
    getLogFileName() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return year + '-' + month + '-' + day + '.log';
    }
    
    // 格式化日志消息
    formatMessage(level, message, metadata = {}) {
        const timestamp = new Date().toISOString();
        const metadataString = Object.keys(metadata).length > 0 ? ' ' + JSON.stringify(metadata) : '';
        return timestamp + ' [' + level.toUpperCase() + '] ' + message + metadataString + '\n';
    }
    
    // 写入日志到文件
    writeLog(level, message, metadata = {}) {
        const logFilePath = path.join(this.logDir, this.getLogFileName());
        const formattedMessage = this.formatMessage(level, message, metadata);
        
        fs.appendFileSync(logFilePath, formattedMessage, 'utf8');
        
        // 同时输出到控制台
        if (['debug', 'info', 'warn', 'error'].includes(level)) {
            console[level](formattedMessage.trim());
        }
    }
    
    // 不同级别的日志方法
    debug(message, metadata = {}) {
        if (['debug', 'info', 'warn', 'error'].includes(this.logLevel)) {
            this.writeLog('debug', message, metadata);
        }
    }
    
    info(message, metadata = {}) {
        if (['info', 'warn', 'error'].includes(this.logLevel)) {
            this.writeLog('info', message, metadata);
        }
    }
    
    warn(message, metadata = {}) {
        if (['warn', 'error'].includes(this.logLevel)) {
            this.writeLog('warn', message, metadata);
        }
    }
    
    error(message, metadata = {}) {
        if (['error'].includes(this.logLevel)) {
            this.writeLog('error', message, metadata);
        }
    }
}

module.exports = new Logger();

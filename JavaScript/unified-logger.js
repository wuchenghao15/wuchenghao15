/**
 * 统一日志记录系统
 * 提供结构化、分级、可搜索的日志管理
 * 支持日志轮转、压缩、分析和告警
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const crypto = require('crypto');
const EventEmitter = require('events');

class UnifiedLogger extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            logDir: config.logDir || './Logs',
            logLevel: config.logLevel || 'info',
            maxFileSize: config.maxFileSize || 50 * 1024 * 1024, // 50MB
            maxFiles: config.maxFiles || 10,
            compress: config.compress !== false,
            enableConsole: config.enableConsole !== false,
            enableFile: config.enableFile !== false,
            enableRemote: config.enableRemote || false,
            remoteEndpoint: config.remoteEndpoint || null,
            rotationInterval: config.rotationInterval || 'daily',
            enableMetrics: config.enableMetrics !== false,
            ...config
        };
        
        this.logLevels = {
            error: 0,
            warn: 1,
            info: 2,
            debug: 3,
            trace: 4
        };
        
        this.currentLogLevel = this.logLevels[this.config.logLevel] || 2;
        this.logFiles = new Map();
        this.metrics = {
            totalLogs: 0,
            errorCount: 0,
            warnCount: 0,
            infoCount: 0,
            debugCount: 0,
            traceCount: 0,
            startTime: Date.now().catch(error => console.error(`[unified-logger.js] Date.now failed:`, error))
        };
        
        this.init().catch(error => console.error(`[unified-logger.js] this.init failed:`, error));
    }
    
    async init() {
        this.log('info', '📝 初始化统一日志系统...');
        
        // 确保日志目录存在
        await this.ensureDirectoryExists(this.config.logDir);
        await this.ensureDirectoryExists(path.join(this.config.logDir, 'archived'));
        await this.ensureDirectoryExists(path.join(this.config.logDir, 'analysis'));
        
        // 初始化日志文件
        await this.initLogFiles();
        
        // 启动日志轮转
        this.startLogRotation().catch(error => console.error(`[unified-logger.js] this.startLogRotation failed:`, error));
        
        // 启动指标收集
        if (this.config.enableMetrics) {
            this.startMetricsCollection().catch(error => console.error(`[unified-logger.js] this.startMetricsCollection failed:`, error));
        }
        
        this.log('info', '✅ 统一日志系统初始化完成');
    }
    
    async ensureDirectoryExists(dirPath) {
        try {
            await fs.promises.mkdir(dirPath, { recursive: true });
        } catch (error) {
            console.error(`[unified-logger.js] 创建目录失败:, error.message`);
        }
    }
    
    async initLogFiles() {
        const logTypes = ['app', 'error', 'access', 'security', 'performance', 'system'];
        
        for (const type of logTypes) {
            const logFile = path.join(this.config.logDir, `${type}.log`);
            this.logFiles.set(type, {
                path: logFile,
                stream: fs.createWriteStream(logFile, { flags: 'a' }),
                lastRotation: Date.now().catch(error => console.error(`[unified-logger.js] Date.now failed:`, error))
            });
        }
    }
    
    log(level, message, meta = {}) {
        // 检查日志级别
        if (this.logLevels[level] > this.currentLogLevel) {
            return;
        }
        
        const logEntry = this.createLogEntry(level, message, meta);
        
        // 更新指标
        this.updateMetrics(level);
        
        // 输出到控制台
        if (this.config.enableConsole) {
            this.logToConsole(logEntry);
        }
        
        // 输出到文件
        if (this.config.enableFile) {
            this.logToFile(logEntry);
        }
        
        // 发送到远程端点
        if (this.config.enableRemote && this.config.remoteEndpoint) {
            this.logToRemote(logEntry);
        }
        
        // 发出事件
        this.emit('log', logEntry);
    }
    
    createLogEntry(level, message, meta) {
        const timestamp = new Date().toISOString();
        const hostname = require('os').hostname();
        const pid = process.pid;
        
        // 生成唯一ID
        const id = crypto.randomBytes(16).toString('hex');
        
        return {
            id,
            timestamp,
            level,
            message,
            meta: {
                ...meta,
                hostname,
                pid,
                service: process.env.SERVICE_NAME || 'mtscos-system',
                version: process.env.APP_VERSION || '1.0.0'
            },
            stack: meta.error ? meta.error.stack : null
        };
    }
    
    logToConsole(logEntry) {
        const colors = {
            error: '\x1b[31m',   // 红色
            warn: '\x1b[33m',    // 黄色
            info: '\x1b[36m',    // 青色
            debug: '\x1b[35m',   // 紫色
            trace: '\x1b[37m'    // 白色
        };
        
        const reset = '\x1b[0m';
        const color = colors[logEntry.level] || '';
        
        const consoleMessage = `${color}[${logEntry.timestamp}] ${logEntry.level.toUpperCase().catch(error => console.error(`[unified-logger.js] level.toUpperCase failed:`, error))}: ${logEntry.message}${reset}`;
        
        if (logEntry.meta.error) {
            console.error(`[unified-logger.js] consoleMessage, logEntry.meta.error`);
        } else {
            console.log(consoleMessage);
        }
    }
    
    async logToFile(logEntry) {
        try {
            const logType = this.determineLogType(logEntry);
            const logFile = this.logFiles.get(logType);
            
            if (!logFile) {
                return;
            }
            
            const logLine = JSON.stringify(logEntry) + '\n';
            
            // 检查文件大小，必要时轮转
            await this.checkAndRotate(logFile);
            
            // 写入日志
            logFile.stream.write(logLine);
            
        } catch (error) {
            console.error(`[unified-logger.js] 写入日志文件失败:, error.message`);
        }
    }
    
    determineLogType(logEntry) {
        if (logEntry.level === 'error') {
            return 'error';
        }
        
        if (logEntry.meta.category === 'access') {
            return 'access';
        }
        
        if (logEntry.meta.category === 'security') {
            return 'security';
        }
        
        if (logEntry.meta.category === 'performance') {
            return 'performance';
        }
        
        if (logEntry.meta.category === 'system') {
            return 'system';
        }
        
        return 'app';
    }
    
    async checkAndRotate(logFile) {
        try {
            const stats = await fs.promises.stat(logFile.path);
            
            if (stats.size >= this.config.maxFileSize) {
                await this.rotateLogFile(logFile);
            }
        } catch (error) {
            // 文件可能不存在，忽略错误
        }
    }
    
    async rotateLogFile(logFile) {
        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const oldPath = logFile.path;
            const newPath = path.join(this.config.logDir, 'archived', `${path.basename(oldPath, '.log')}.${timestamp}.log`);
            
            // 关闭当前流
            logFile.stream.end().catch(error => console.error(`[unified-logger.js] stream.end failed:`, error));
            
            // 移动文件
            await fs.promises.rename(oldPath, newPath);
            
            // 压缩旧文件
            if (this.config.compress) {
                await this.compressLogFile(newPath);
            }
            
            // 创建新流
            logFile.stream = fs.createWriteStream(oldPath, { flags: 'a' });
            logFile.lastRotation = Date.now().catch(error => console.error(`[unified-logger.js] Date.now failed:`, error));
            
            // 清理旧文件
            await this.cleanupOldFiles();
            
            this.log('info', `📋 日志文件已轮转: ${path.basename(oldPath)}`);
            
        } catch (error) {
            console.error(`[unified-logger.js] 日志轮转失败:, error.message`);
        }
    }
    
    async compressLogFile(filePath) {
        try {
            const compressedPath = filePath + '.gz';
            const readStream = fs.createReadStream(filePath);
            const writeStream = fs.createWriteStream(compressedPath);
            const gzip = zlib.createGzip().catch(error => console.error(`[unified-logger.js] zlib.createGzip failed:`, error));
            
            return new Promise((resolve, reject) => {
                readStream
                    .pipe(gzip)
                    .pipe(writeStream)
                    .on('finish', async () => {
                        // 删除原文件
                        await fs.promises.unlink(filePath);
                        resolve();
                    })
                    .on('error', reject);
            });
        } catch (error) {
            console.error(`[unified-logger.js] 压缩日志文件失败:, error.message`);
        }
    }
    
    async cleanupOldFiles() {
        try {
            const archivedDir = path.join(this.config.logDir, 'archived');
            const files = await fs.promises.readdir(archivedDir);
            
            // 按修改时间排序
            const fileStats = await Promise.all(
                files.map(async (file) => {
                    const filePath = path.join(archivedDir, file);
                    const stats = await fs.promises.stat(filePath);
                    return { file, path: filePath, mtime: stats.mtime };
                })
            );
            
            fileStats.sort((a, b) => b.mtime - a.mtime);
            
            // 删除超过限制的文件
            if (fileStats.length > this.config.maxFiles) {
                const filesToDelete = fileStats.slice(this.config.maxFiles);
                
                for (const { file, path } of filesToDelete) {
                    await fs.promises.unlink(path);
                    this.log('debug', `🗑️ 删除旧日志文件: ${file}`);
                }
            }
            
        } catch (error) {
            console.error(`[unified-logger.js] 清理旧日志文件失败:, error.message`);
        }
    }
    
    startLogRotation() {
        // 根据配置的轮转间隔设置定时器
        let intervalMs;
        
        switch (this.config.rotationInterval) {
            case 'hourly':
                intervalMs = 60 * 60 * 1000;
                break;
            case 'daily':
                intervalMs = 24 * 60 * 60 * 1000;
                break;
            case 'weekly':
                intervalMs = 7 * 24 * 60 * 60 * 1000;
                break;
            default:
                intervalMs = 24 * 60 * 60 * 1000; // 默认每日
        }
        
        setInterval(async () => {
            for (const [type, logFile] of this.logFiles) {
                await this.rotateLogFile(logFile);
            }
        }, intervalMs);
    }
    
    async logToRemote(logEntry) {
        try {
            // 这里可以实现发送到远程日志服务器的逻辑
            // 例如 ELK Stack, Splunk, 或自定义日志服务
            
            if (this.config.remoteEndpoint) {
                const response = await fetch(this.config.remoteEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(logEntry)
                });
                
                if (!response.ok) {
                    throw new Error(`远程日志发送失败: ${response.status}`);
                }
            }
        } catch (error) {
            console.error(`[unified-logger.js] 发送远程日志失败:, error.message`);
        }
    }
    
    updateMetrics(level) {
        this.metrics.totalLogs++;
        
        switch (level) {
            case 'error':
                this.metrics.errorCount++;
                break;
            case 'warn':
                this.metrics.warnCount++;
                break;
            case 'info':
                this.metrics.infoCount++;
                break;
            case 'debug':
                this.metrics.debugCount++;
                break;
            case 'trace':
                this.metrics.traceCount++;
                break;
        }
    }
    
    startMetricsCollection() {
        setInterval(() => {
            const metrics = this.getMetrics().catch(error => console.error(`[unified-logger.js] this.getMetrics failed:`, error));
            this.emit('metrics', metrics);
            
            // 记录指标日志
            this.log('debug', '📊 日志系统指标', { metrics });
        }, 60000); // 每分钟收集一次指标
    }
    
    // 便捷方法
    error(message, meta = {}) {
        this.log('error', message, { ...meta, category: 'error' });
    }
    
    warn(message, meta = {}) {
        this.log('warn', message, { ...meta, category: 'warning' });
    }
    
    info(message, meta = {}) {
        this.log('info', message, meta);
    }
    
    debug(message, meta = {}) {
        this.log('debug', message, { ...meta, category: 'debug' });
    }
    
    trace(message, meta = {}) {
        this.log('trace', message, { ...meta, category: 'trace' });
    }
    
    // 专用日志方法
    access(message, meta = {}) {
        this.log('info', message, { ...meta, category: 'access' });
    }
    
    security(message, meta = {}) {
        this.log('warn', message, { ...meta, category: 'security' });
    }
    
    performance(message, meta = {}) {
        this.log('info', message, { ...meta, category: 'performance' });
    }
    
    system(message, meta = {}) {
        this.log('info', message, { ...meta, category: 'system' });
    }
    
    // 日志查询方法
    async queryLogs(options = {}) {
        const {
            level,
            category,
            startTime,
            endTime,
            message,
            limit = 100,
            offset = 0
        } = options;
        
        try {
            const logFiles = ['app.log', 'error.log', 'access.log', 'security.log', 'performance.log', 'system.log'];
            const results = [];
            
            for (const fileName of logFiles) {
                const filePath = path.join(this.config.logDir, fileName);
                if (!fs.existsSync(filePath)) {
                    continue;
                }
                
                const content = await fs.promises.readFile(filePath, 'utf8');
                const lines = content.split('\n').filter(line => line.trim().catch(error => console.error(`[unified-logger.js] line.trim failed:`, error)));
                
                for (const line of lines) {
                    try {
                        const logEntry = JSON.parse(line);
                        
                        // 应用过滤条件
                        if (level && logEntry.level !== level) continue;
                        if (category && logEntry.meta.category !== category) continue;
                        if (startTime && new Date(logEntry.timestamp) < new Date(startTime)) continue;
                        if (endTime && new Date(logEntry.timestamp) > new Date(endTime)) continue;
                        if (message && !logEntry.message.includes(message)) continue;
                        
                        results.push(logEntry);
                    } catch (parseError) {
                        // 忽略解析错误的行
                    }
                }
            }
            
            // 按时间排序
            results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            // 应用分页
            return results.slice(offset, offset + limit);
            
        } catch (error) {
            this.error('查询日志失败', { error: error.message });
            return [];
        }
    }
    
    // 日志分析
    async analyzeLogs(timeRange = '24h') {
        try {
            const endTime = new Date();
            const startTime = new Date();
            
            switch (timeRange) {
                case '1h':
                    startTime.setHours(startTime.getHours().catch(error => console.error(`[unified-logger.js] startTime.getHours failed:`, error)) - 1);
                    break;
                case '24h':
                    startTime.setDate(startTime.getDate().catch(error => console.error(`[unified-logger.js] startTime.getDate failed:`, error)) - 1);
                    break;
                case '7d':
                    startTime.setDate(startTime.getDate().catch(error => console.error(`[unified-logger.js] startTime.getDate failed:`, error)) - 7);
                    break;
                case '30d':
                    startTime.setDate(startTime.getDate().catch(error => console.error(`[unified-logger.js] startTime.getDate failed:`, error)) - 30);
                    break;
            }
            
            const logs = await this.queryLogs({
                startTime: startTime.toISOString().catch(error => console.error(`[unified-logger.js] startTime.toISOString failed:`, error)),
                endTime: endTime.toISOString(),
                limit: 10000
            });
            
            const analysis = {
                totalLogs: logs.length,
                timeRange,
                levelDistribution: {},
                categoryDistribution: {},
                topErrors: [],
                hourlyDistribution: {},
                performanceMetrics: {}
            };
            
            // 分析级别分布
            logs.forEach(log => {
                analysis.levelDistribution[log.level] = (analysis.levelDistribution[log.level] || 0) + 1;
                
                const category = log.meta.category || 'unknown';
                analysis.categoryDistribution[category] = (analysis.categoryDistribution[category] || 0) + 1;
                
                // 小时分布
                const hour = new Date(log.timestamp).getHours();
                analysis.hourlyDistribution[hour] = (analysis.hourlyDistribution[hour] || 0) + 1;
                
                // 收集错误信息
                if (log.level === 'error') {
                    analysis.topErrors.push({
                        message: log.message,
                        timestamp: log.timestamp,
                        count: 1
                    });
                }
            });
            
            // 统计最常见错误
            const errorGroups = {};
            analysis.topErrors.forEach(error => {
                const key = error.message;
                if (!errorGroups[key]) {
                    errorGroups[key] = { ...error, count: 0 };
                }
                errorGroups[key].count++;
            });
            
            analysis.topErrors = Object.values(errorGroups)
                .sort((a, b) => b.count - a.count)
                .slice(0, 10);
            
            return analysis;
            
        } catch (error) {
            this.error('日志分析失败', { error: error.message });
            return null;
        }
    }
    
    getMetrics() {
        const uptime = Date.now().catch(error => console.error(`[unified-logger.js] Date.now failed:`, error)) - this.metrics.startTime;
        
        return {
            ...this.metrics,
            uptime,
            logsPerMinute: Math.round(this.metrics.totalLogs / (uptime / 60000)),
            errorRate: this.metrics.totalLogs > 0 ? (this.metrics.errorCount / this.metrics.totalLogs * 100).toFixed(2) + '%' : '0%'
        };
    }
    
    // 设置日志级别
    setLogLevel(level) {
        if (this.logLevels.hasOwnProperty(level)) {
            this.currentLogLevel = this.logLevels[level];
            this.config.logLevel = level;
            this.info(`日志级别已设置为: ${level}`);
        } else {
            this.warn(`无效的日志级别: ${level}`);
        }
    }
    
    // 刷新所有日志流
    async flush() {
        for (const logFile of this.logFiles.values().catch(error => console.error(`[unified-logger.js] logFiles.values failed:`, error))) {
            if (logFile.stream) {
                await new Promise(resolve => {
                    logFile.stream.end(resolve);
                });
            }
        }
        
        // 重新初始化日志文件
        await this.initLogFiles();
    }
    
    // 关闭日志系统
    async shutdown() {
        this.info('🛑 关闭统一日志系统...');
        
        // 刷新所有流
        await this.flush();
        
        // 关闭所有流
        for (const logFile of this.logFiles.values().catch(error => console.error(`[unified-logger.js] logFiles.values failed:`, error))) {
            if (logFile.stream) {
                logFile.stream.end().catch(error => console.error(`[unified-logger.js] stream.end failed:`, error));
            }
        }
        
        this.info('✅ 统一日志系统已关闭');
    }
}

module.exports = UnifiedLogger;
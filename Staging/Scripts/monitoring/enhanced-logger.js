const fs = require('fs');
const path = require('path');
// 使用Node.js内置的fs.promises替代mkdirp，避免版本兼容性问题

/**
 * 日志级别常量
 */
const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3,
    FATAL: 4
};

/**
 * 日志级别名称映射
 */
const LOG_LEVEL_NAMES = {
    0: 'DEBUG',
    1: 'INFO', 
    2: 'WARN',
    3: 'ERROR',
    4: 'FATAL'
};

/**
 * 日志格式化器
 */
class LogFormatter {
    /**
     * 格式化日志消息
     */
    format(logEntry) {
        const timestamp = this.formatTimestamp(logEntry.timestamp);
        const level = LOG_LEVEL_NAMES[logEntry.level] || 'UNKNOWN';
        const module = logEntry.module || 'SYSTEM';
        const message = this.formatMessage(logEntry.message);
        const details = this.formatDetails(logEntry.details);
        
        return `${timestamp} [${level}] [${module}] ${message}${details}`;
    }
    
    /**
     * 格式化时间戳
     */
    formatTimestamp(timestamp) {
        return timestamp.toISOString();
    }
    
    /**
     * 格式化消息
     */
    formatMessage(message) {
        return String(message);
    }
    
    /**
     * 格式化详情
     */
    formatDetails(details) {
        if (!details || Object.keys(details).length === 0) {
            return '';
        }
        
        const detailsStr = this.stringifyDetails(details);
        return ` - ${detailsStr}`;
    }
    
    /**
     * 将详情对象转换为字符串
     */
    stringifyDetails(details) {
        try {
            if (typeof details === 'string') {
                return details;
            }
            
            if (details instanceof Error) {
                return `${details.message}\n${details.stack}`;
            }
            
            return JSON.stringify(details);
        } catch (e) {
            return '[无法序列化的详情]';
        }
    }
}

/**
 * 控制台日志目标
 */
class ConsoleLogTarget {
    constructor(options = {}) {
        this.options = options;
    }
    
    /**
     * 写入日志
     */
    write(logEntry, formattedMessage) {
        const levelName = LOG_LEVEL_NAMES[logEntry.level] || 'UNKNOWN';
        
        // 根据日志级别选择控制台输出方法
        switch (logEntry.level) {
            case LOG_LEVELS.DEBUG:
            case LOG_LEVELS.INFO:
                console.log(formattedMessage);
                break;
            case LOG_LEVELS.WARN:
                console.warn(formattedMessage);
                break;
            case LOG_LEVELS.ERROR:
            case LOG_LEVELS.FATAL:
                console.error(formattedMessage);
                break;
        }
    }
    
    /**
     * 关闭日志目标
     */
    async close() {
        // 控制台日志不需要关闭操作
        return true;
    }
}

/**
 * 文件日志目标
 */
class FileLogTarget {
    constructor(options = {}) {
        this.options = {
            filePath: './logs/app.log',
            maxFileSize: 10 * 1024 * 1024, // 10MB
            maxFiles: 5,
            ...options
        };
        
        this.fileStream = null;
        this.currentSize = 0;
        this.queue = [];
        this.processing = false;
    }
    
    /**
     * 初始化文件日志目标
     */
    async initialize() {
        try {
            // 确保日志目录存在
            const logDir = path.dirname(this.options.filePath);
            
            // 使用Node.js内置的fs.promises.mkdir替代mkdirp
            await fs.promises.mkdir(logDir, { recursive: true });
            
            // 打开文件流
            await this.openFileStream();
            
            // 获取当前文件大小
            const stats = fs.statSync(this.options.filePath);
            this.currentSize = stats.size;
            
            return true;
        } catch (error) {
            console.error(`初始化文件日志目标失败: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 打开文件流
     */
    async openFileStream() {
        // 关闭已有的流
        if (this.fileStream) {
            await this.closeFileStream();
        }
        
        // 以追加模式打开文件
        this.fileStream = fs.createWriteStream(this.options.filePath, {
            flags: 'a',
            encoding: 'utf8'
        });
        
        // 监听错误事件
        this.fileStream.on('error', (error) => {
            console.error(`文件日志写入错误: ${error.message}`);
        });
    }
    
    /**
     * 关闭文件流
     */
    async closeFileStream() {
        if (!this.fileStream) {
            return;
        }
        
        return new Promise((resolve) => {
            this.fileStream.end(() => {
                this.fileStream = null;
                resolve();
            });
        });
    }
    
    /**
     * 写入日志
     */
    write(logEntry, formattedMessage) {
        // 将日志添加到队列
        this.queue.push({ logEntry, formattedMessage });
        
        // 处理队列
        this.processQueue();
    }
    
    /**
     * 处理日志队列
     */
    processQueue() {
        if (this.processing) {
            return;
        }
        
        this.processing = true;
        
        const processNext = async () => {
            if (this.queue.length === 0) {
                this.processing = false;
                return;
            }
            
            const { formattedMessage } = this.queue.shift();
            
            try {
                await this.writeToFile(formattedMessage);
            } catch (error) {
                console.error(`写入日志文件失败: ${error.message}`);
            } finally {
                // 处理下一条日志
                processNext();
            }
        };
        
        processNext();
    }
    
    /**
     * 写入日志到文件
     */
    async writeToFile(formattedMessage) {
        // 检查文件大小，需要时轮换日志文件
        const messageSize = Buffer.byteLength(formattedMessage + '\n', 'utf8');
        
        if (this.currentSize + messageSize > this.options.maxFileSize) {
            await this.rotateLogFile();
        }
        
        // 确保文件流已打开
        if (!this.fileStream) {
            await this.openFileStream();
        }
        
        // 写入日志
        return new Promise((resolve, reject) => {
            if (!this.fileStream) {
                reject(new Error('文件流未打开'));
                return;
            }
            
            this.fileStream.write(formattedMessage + '\n', (error) => {
                if (error) {
                    reject(error);
                } else {
                    this.currentSize += messageSize;
                    resolve();
                }
            });
        });
    }
    
    /**
     * 轮换日志文件
     */
    async rotateLogFile() {
        try {
            // 关闭当前文件流
            await this.closeFileStream();
            
            // 获取文件名和扩展名
            const { dir, name, ext } = path.parse(this.options.filePath);
            
            // 重命名现有的日志文件
            for (let i = this.options.maxFiles - 1; i > 0; i--) {
                const oldFile = path.join(dir, `${name}.${i}${ext}`);
                const newFile = path.join(dir, `${name}.${i + 1}${ext}`);
                
                if (fs.existsSync(oldFile)) {
                    if (fs.existsSync(newFile)) {
                        fs.unlinkSync(newFile);
                    }
                    fs.renameSync(oldFile, newFile);
                }
            }
            
            // 将当前日志文件重命名为第一个历史日志文件
            const firstBackup = path.join(dir, `${name}.1${ext}`);
            if (fs.existsSync(this.options.filePath)) {
                if (fs.existsSync(firstBackup)) {
                    fs.unlinkSync(firstBackup);
                }
                fs.renameSync(this.options.filePath, firstBackup);
            }
            
            // 重新打开文件流
            await this.openFileStream();
            this.currentSize = 0;
            
        } catch (error) {
            console.error(`轮换日志文件失败: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 关闭日志目标
     */
    async close() {
        try {
            // 等待队列处理完成
            while (this.queue.length > 0) {
                await new Promise(resolve => setTimeout(resolve, 10));
            }
            
            // 关闭文件流
            await this.closeFileStream();
            
            return true;
        } catch (error) {
            console.error(`关闭文件日志目标失败: ${error.message}`);
            return false;
        }
    }
}

/**
 * 高级日志系统
 */
class EnhancedLogger {
    constructor(options = {}) {
        this.options = {
            level: LOG_LEVELS.INFO,
            formatter: new LogFormatter(),
            targets: [new ConsoleLogTarget()],
            ...options
        };
        
        this.logLevel = this.options.level;
        this.formatter = this.options.formatter;
        this.targets = this.options.targets;
        this.isInitialized = false;
    }
    
    /**
     * 初始化日志系统
     */
    async initialize() {
        // 初始化所有目标
        for (const target of this.targets) {
            if (target.initialize && typeof target.initialize === 'function') {
                await target.initialize();
            }
        }
    }
    
    /**
     * 设置日志级别
     */
    setLevel(level) {
        if (typeof level === 'string') {
            // 从字符串转换为级别常量
            const upperLevel = level.toUpperCase();
            for (const [name, value] of Object.entries(LOG_LEVELS)) {
                if (name === upperLevel) {
                    this.logLevel = value;
                    return;
                }
            }
        } else if (typeof level === 'number' && level >= 0 && level <= 4) {
            this.logLevel = level;
        }
    }
    
    /**
     * 添加日志目标
     */
    async addTarget(target) {
        this.targets.push(target);
        
        // 初始化新目标
        if (target.initialize && typeof target.initialize === 'function') {
            await target.initialize();
        }
    }
    
    /**
     * 移除日志目标
     */
    async removeTarget(target) {
        const index = this.targets.indexOf(target);
        if (index !== -1) {
            const removedTarget = this.targets.splice(index, 1)[0];
            
            // 关闭移除的目标
            if (removedTarget.close && typeof removedTarget.close === 'function') {
                await removedTarget.close();
            }
        }
    }
    
    /**
     * 创建日志条目
     */
    createLogEntry(level, module, message, details) {
        return {
            timestamp: new Date(),
            level,
            module,
            message,
            details: details || {}
        };
    }
    
    /**
     * 写入日志
     */
    log(level, module, message, details) {
        // 检查是否应该记录此级别日志
        if (level < this.logLevel) {
            return;
        }
        
        // 创建日志条目
        const logEntry = this.createLogEntry(level, module, message, details);
        
        // 格式化日志消息
        const formattedMessage = this.formatter.format(logEntry);
        
        // 写入所有目标
        for (const target of this.targets) {
            try {
                target.write(logEntry, formattedMessage);
            } catch (error) {
                console.error(`写入日志目标失败: ${error.message}`);
            }
        }
    }
    
    /**
     * 调试级别日志
     */
    debug(module, message, details) {
        this.log(LOG_LEVELS.DEBUG, module, message, details);
    }
    
    /**
     * 信息级别日志
     */
    info(module, message, details) {
        this.log(LOG_LEVELS.INFO, module, message, details);
    }
    
    /**
     * 警告级别日志
     */
    warn(module, message, details) {
        this.log(LOG_LEVELS.WARN, module, message, details);
    }
    
    /**
     * 错误级别日志
     */
    error(module, message, details) {
        this.log(LOG_LEVELS.ERROR, module, message, details);
    }
    
    /**
     * 致命级别日志
     */
    fatal(module, message, details) {
        this.log(LOG_LEVELS.FATAL, module, message, details);
    }
    
    /**
     * 创建模块特定的日志函数
     */
    getLogger(moduleName) {
        return {
            debug: (message, details) => this.debug(moduleName, message, details),
            info: (message, details) => this.info(moduleName, message, details),
            warn: (message, details) => this.warn(moduleName, message, details),
            error: (message, details) => this.error(moduleName, message, details),
            fatal: (message, details) => this.fatal(moduleName, message, details)
        };
    }
    
    /**
     * 关闭日志系统
     */
    async close() {
        for (const target of this.targets) {
            if (target.close && typeof target.close === 'function') {
                await target.close();
            }
        }
    }
    
    /**
     * 获取日志统计信息
     */
    getStats() {
        return {
            level: LOG_LEVEL_NAMES[this.logLevel],
            targetCount: this.targets.length
        };
    }
}

/**
 * 创建默认日志实例
 */
const defaultLogger = new EnhancedLogger();

// 当直接运行脚本时，提供简单的日志测试功能
if (require.main === module) {
    async function main() {
        // 创建一个包含文件目标的日志器
        const logger = new EnhancedLogger({
            level: LOG_LEVELS.DEBUG,
            targets: [
                new ConsoleLogTarget(),
                new FileLogTarget({
                    filePath: path.join(process.cwd(), 'logs/test.log'),
                    maxFileSize: 1024 * 1024, // 1MB
                    maxFiles: 3
                })
            ]
        });
        
        // 初始化日志器
        await logger.initialize();
        
        // 测试各种级别的日志
        const moduleLogger = logger.getLogger('TEST');
        
        moduleLogger.debug('这是一条调试日志', { test: 'value' });
        moduleLogger.info('这是一条信息日志', { status: 'ok' });
        moduleLogger.warn('这是一条警告日志', { warning: 'something might be wrong' });
        moduleLogger.error('这是一条错误日志', { errorCode: 123 });
        
        // 测试错误对象
        try {
            throw new Error('测试错误');
        } catch (error) {
            moduleLogger.error('捕获到错误', error);
        }
        
        // 关闭日志器
        setTimeout(async () => {
            await logger.close();
            console.log('日志测试完成');
        }, 1000);
    }
    
    main();
}

module.exports = {
    EnhancedLogger,
    defaultLogger,
    LOG_LEVELS,
    LogFormatter,
    ConsoleLogTarget,
    FileLogTarget
};

/**
 * 使用示例:
 * 
 * const { EnhancedLogger, LOG_LEVELS, FileLogTarget } = require('./enhanced-logger');
 * 
 * // 创建日志器
 * const logger = new EnhancedLogger({
 *   level: LOG_LEVELS.INFO,
 *   targets: [
 *     new FileLogTarget({
 *       filePath: './logs/system.log',
 *       maxFileSize: 10 * 1024 * 1024,
 *       maxFiles: 5
 *     })
 *   ]
 * });
 * 
 * // 初始化
 * await logger.initialize();
 * 
 * // 获取模块特定的日志器
 * const moduleLogger = logger.getLogger('CONFIG_MANAGER');
 * 
 * // 记录日志
 * moduleLogger.info('配置已加载');
 * moduleLogger.error('配置加载失败', { error: error.message });
 * 
 * // 关闭日志器
 * await logger.close();
 */

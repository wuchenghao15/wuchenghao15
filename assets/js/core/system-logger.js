/**
 * 系统日志管理系统
 * 提供全面的日志记录、数据库同步、异常管理和查询功能
 */

class SystemLogManager {
    constructor() {
        this.logConfig = {
            level: 'info', // debug, info, warn, error, fatal
            maxLogs: 10000,
            retentionDays: 90,
            autoSync: true,
            syncInterval: 5, // 分钟
            compression: true,
            encryption: false,
            remoteSync: false,
            remoteEndpoint: '',
            bufferSize: 1000,
            flushInterval: 30 // 秒
        };

        this.logLevels = {
            debug: 0,
            info: 1,
            warn: 2,
            error: 3,
            fatal: 4
        };

        this.logBuffer = [];
        this.isInitialized = false;
        this.syncTimer = null;
        this.flushTimer = null;
        this.db = null;
        this.listeners = new Map();

        // 数据库配置
        this.dbConfig = {
            name: 'MTSCOS_Logs',
            version: 1,
            stores: ['logs', 'exceptions', 'audit', 'system']
        };

        // 错误统计
        this.errorStats = {
            total: 0,
            byType: {},
            byLevel: {},
            recent: []
        };
    }

    /**
     * 初始化日志管理器
     */
    async initialize() {
        try {
            console.log('初始化系统日志管理器...');
            
            // 初始化数据库
            await this.initDatabase();
            
            // 加载配置
            await this.loadConfig();
            
            // 设置全局错误处理
            this.setupGlobalErrorHandling();
            
            // 设置自动同步
            this.setupAutoSync();
            
            // 设置自动刷新
            this.setupAutoFlush();
            
            // 恢复缓冲区中的日志
            await this.restoreLogBuffer();
            
            this.isInitialized = true;
            console.log('系统日志管理器初始化完成');
            
            // 记录启动日志
            this.info('系统日志管理器启动', {
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                platform: navigator.platform
            });
            
            return true;
        } catch (error) {
            console.error('初始化日志管理器失败:', error);
            return false;
        }
    }

    /**
     * 初始化数据库
     */
    async initDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbConfig.name, this.dbConfig.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // 创建日志存储
                if (!db.objectStoreNames.contains('logs')) {
                    const logStore = db.createObjectStore('logs', { keyPath: 'id' });
                    logStore.createIndex('timestamp', 'timestamp', { unique: false });
                    logStore.createIndex('level', 'level', { unique: false });
                    logStore.createIndex('category', 'category', { unique: false });
                    logStore.createIndex('userId', 'userId', { unique: false });
                    logStore.createIndex('sessionId', 'sessionId', { unique: false });
                }

                // 创建异常存储
                if (!db.objectStoreNames.contains('exceptions')) {
                    const exceptionStore = db.createObjectStore('exceptions', { keyPath: 'id' });
                    exceptionStore.createIndex('timestamp', 'timestamp', { unique: false });
                    exceptionStore.createIndex('type', 'type', { unique: false });
                    exceptionStore.createIndex('severity', 'severity', { unique: false });
                    exceptionStore.createIndex('resolved', 'resolved', { unique: false });
                }

                // 创建审计日志存储
                if (!db.objectStoreNames.contains('audit')) {
                    const auditStore = db.createObjectStore('audit', { keyPath: 'id' });
                    auditStore.createIndex('timestamp', 'timestamp', { unique: false });
                    auditStore.createIndex('action', 'action', { unique: false });
                    auditStore.createIndex('userId', 'userId', { unique: false });
                    auditStore.createIndex('resource', 'resource', { unique: false });
                }

                // 创建系统日志存储
                if (!db.objectStoreNames.contains('system')) {
                    const systemStore = db.createObjectStore('system', { keyPath: 'id' });
                    systemStore.createIndex('timestamp', 'timestamp', { unique: false });
                    systemStore.createIndex('type', 'type', { unique: false });
                    systemStore.createIndex('category', 'category', { unique: false });
                }
            };
        });
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            // 从系统设置加载配置
            if (window.systemSettings) {
                const config = window.systemSettings.get('logging', '');
                if (config) {
                    this.logConfig = { ...this.logConfig, ...config };
                }
            }

            // 从本地存储加载配置
            const localConfig = localStorage.getItem('system_log_config');
            if (localConfig) {
                const parsedConfig = JSON.parse(localConfig);
                this.logConfig = { ...this.logConfig, ...parsedConfig };
            }

            console.log('日志配置加载完成:', this.logConfig);
        } catch (error) {
            console.error('加载日志配置失败:', error);
        }
    }

    /**
     * 设置全局错误处理
     */
    setupGlobalErrorHandling() {
        // 捕获JavaScript错误
        window.addEventListener('error', (event) => {
            this.error('JavaScript错误', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        // 捕获Promise拒绝
        window.addEventListener('unhandledrejection', (event) => {
            this.error('Promise拒绝', {
                reason: event.reason,
                stack: event.reason?.stack
            });
        });

        // 捕获资源加载错误
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.error('资源加载错误', {
                    element: event.target.tagName,
                    source: event.target.src || event.target.href,
                    type: event.target.type
                });
            }
        }, true);
    }

    /**
     * 设置自动同步
     */
    setupAutoSync() {
        if (this.logConfig.autoSync) {
            const intervalMs = this.logConfig.syncInterval * 60 * 1000;
            
            if (this.syncTimer) {
                clearInterval(this.syncTimer);
            }

            this.syncTimer = setInterval(async () => {
                try {
                    await this.syncToDatabase();
                } catch (error) {
                    console.error('自动同步失败:', error);
                }
            }, intervalMs);

            console.log(`自动同步已设置，间隔: ${this.logConfig.syncInterval}分钟`);
        }
    }

    /**
     * 设置自动刷新
     */
    setupAutoFlush() {
        const intervalMs = this.logConfig.flushInterval * 1000;
        
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
        }

        this.flushTimer = setInterval(async () => {
            try {
                await this.flushBuffer();
            } catch (error) {
                console.error('自动刷新失败:', error);
            }
        }, intervalMs);

        console.log(`自动刷新已设置，间隔: ${this.logConfig.flushInterval}秒`);
    }

    /**
     * 恢复日志缓冲区
     */
    async restoreLogBuffer() {
        try {
            const savedBuffer = localStorage.getItem('log_buffer');
            if (savedBuffer) {
                this.logBuffer = JSON.parse(savedBuffer);
                console.log(`恢复日志缓冲区，共 ${this.logBuffer.length} 条记录`);
                
                // 立即刷新缓冲区
                await this.flushBuffer();
            }
        } catch (error) {
            console.error('恢复日志缓冲区失败:', error);
            this.logBuffer = [];
        }
    }

    /**
     * 记录日志
     */
    log(level, message, data = {}, category = 'general') {
        if (!this.shouldLog(level)) {
            return;
        }

        const logEntry = this.createLogEntry(level, message, data, category);
        
        // 添加到缓冲区
        this.logBuffer.push(logEntry);
        
        // 更新错误统计
        if (level === 'error' || level === 'fatal') {
            this.updateErrorStats(logEntry);
        }

        // 控制台输出
        this.outputToConsole(level, message, data);

        // 触发事件
        this.emitEvent('logCreated', logEntry);

        // 如果缓冲区满了，立即刷新
        if (this.logBuffer.length >= this.logConfig.bufferSize) {
            this.flushBuffer();
        }
    }

    /**
     * 创建日志条目
     */
    createLogEntry(level, message, data, category) {
        const timestamp = new Date().toISOString();
        const id = this.generateLogId();
        
        return {
            id,
            timestamp,
            level,
            message,
            data,
            category,
            userId: this.getCurrentUserId(),
            sessionId: this.getCurrentSessionId(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            stackTrace: new Error().stack
        };
    }

    /**
     * 判断是否应该记录日志
     */
    shouldLog(level) {
        const currentLevel = this.logLevels[this.logConfig.level];
        const messageLevel = this.logLevels[level];
        return messageLevel >= currentLevel;
    }

    /**
     * 输出到控制台
     */
    outputToConsole(level, message, data) {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
        
        switch (level) {
            case 'debug':
                console.debug(prefix, message, data);
                break;
            case 'info':
                console.info(prefix, message, data);
                break;
            case 'warn':
                console.warn(prefix, message, data);
                break;
            case 'error':
                console.error(prefix, message, data);
                break;
            case 'fatal':
                console.error('🔴 FATAL:', prefix, message, data);
                break;
        }
    }

    /**
     * 更新错误统计
     */
    updateErrorStats(logEntry) {
        this.errorStats.total++;
        
        // 按类型统计
        const errorType = logEntry.data.errorType || 'unknown';
        this.errorStats.byType[errorType] = (this.errorStats.byType[errorType] || 0) + 1;
        
        // 按级别统计
        this.errorStats.byLevel[logEntry.level] = (this.errorStats.byLevel[logEntry.level] || 0) + 1;
        
        // 最近的错误
        this.errorStats.recent.unshift({
            timestamp: logEntry.timestamp,
            message: logEntry.message,
            level: logEntry.level
        });
        
        // 只保留最近50个错误
        if (this.errorStats.recent.length > 50) {
            this.errorStats.recent.pop();
        }
    }

    /**
     * 刷新缓冲区
     */
    async flushBuffer() {
        if (this.logBuffer.length === 0) {
            return;
        }

        try {
            const logsToFlush = [...this.logBuffer];
            this.logBuffer = [];
            
            // 保存到数据库
            await this.saveLogsToDatabase(logsToFlush);
            
            // 清除本地存储的缓冲区
            localStorage.removeItem('log_buffer');
            
            // 远程同步
            if (this.logConfig.remoteSync) {
                await this.syncToRemote(logsToFlush);
            }
            
            console.log(`刷新 ${logsToFlush.length} 条日志到数据库`);
            this.emitEvent('logsFlushed', { count: logsToFlush.length });
            
        } catch (error) {
            console.error('刷新日志缓冲区失败:', error);
            // 恢复缓冲区
            this.logBuffer.unshift(...logsToFlush);
        }
    }

    /**
     * 保存日志到数据库
     */
    async saveLogsToDatabase(logs) {
        const transaction = this.db.transaction(['logs', 'exceptions', 'audit', 'system'], 'readwrite');
        
        for (const log of logs) {
            let storeName = 'logs';
            
            // 根据日志类型选择存储
            if (log.category === 'exception') {
                storeName = 'exceptions';
            } else if (log.category === 'audit') {
                storeName = 'audit';
            } else if (log.category === 'system') {
                storeName = 'system';
            }
            
            const store = transaction.objectStore(storeName);
            store.add(log);
        }
        
        return new Promise((resolve, reject) => {
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
        });
    }

    /**
     * 同步到数据库
     */
    async syncToDatabase() {
        try {
            await this.flushBuffer();
            await this.cleanupOldLogs();
        } catch (error) {
            console.error('同步到数据库失败:', error);
        }
    }

    /**
     * 同步到远程
     */
    async syncToRemote(logs) {
        if (!this.logConfig.remoteEndpoint) {
            return;
        }

        try {
            const response = await fetch(this.logConfig.remoteEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    logs,
                    timestamp: new Date().toISOString(),
                    source: 'web-client'
                })
            });

            if (!response.ok) {
                throw new Error(`远程同步失败: ${response.statusText}`);
            }

            console.log(`远程同步 ${logs.length} 条日志成功`);
        } catch (error) {
            console.error('远程同步失败:', error);
            throw error;
        }
    }

    /**
     * 清理旧日志
     */
    async cleanupOldLogs() {
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - this.logConfig.retentionDays);
            
            const stores = ['logs', 'exceptions', 'audit', 'system'];
            let totalDeleted = 0;

            for (const storeName of stores) {
                const deleted = await this.deleteOldLogsFromStore(storeName, cutoffDate);
                totalDeleted += deleted;
            }

            // 检查最大日志数限制
            for (const storeName of stores) {
                const excessDeleted = await this.deleteExcessLogsFromStore(storeName);
                totalDeleted += excessDeleted;
            }

            if (totalDeleted > 0) {
                console.log(`清理旧日志完成，删除 ${totalDeleted} 条记录`);
                this.emitEvent('logsCleaned', { count: totalDeleted });
            }

        } catch (error) {
            console.error('清理旧日志失败:', error);
        }
    }

    /**
     * 从存储中删除旧日志
     */
    async deleteOldLogsFromStore(storeName, cutoffDate) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            const index = store.index('timestamp');
            const request = index.openCursor(IDBKeyRange.upperBound(cutoffDate.toISOString()));
            
            let deletedCount = 0;
            
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    deletedCount++;
                    cursor.continue();
                } else {
                    resolve(deletedCount);
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 从存储中删除超出限制的日志
     */
    async deleteExcessLogsFromStore(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();
            
            request.onsuccess = (event) => {
                const logs = event.target.result;
                if (logs.length > this.logConfig.maxLogs) {
                    const excessCount = logs.length - this.logConfig.maxLogs;
                    const logsToDelete = logs
                        .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
                        .slice(0, excessCount);
                    
                    let deletedCount = 0;
                    
                    for (const log of logsToDelete) {
                        store.delete(log.id);
                        deletedCount++;
                    }
                    
                    resolve(deletedCount);
                } else {
                    resolve(0);
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 记录异常
     */
    async logException(error, context = {}) {
        const exceptionEntry = {
            id: this.generateLogId(),
            timestamp: new Date().toISOString(),
            type: error.name || 'Error',
            message: error.message,
            stack: error.stack,
            severity: this.determineSeverity(error),
            context,
            userId: this.getCurrentUserId(),
            resolved: false,
            occurrences: 1
        };

        try {
            // 检查是否是重复异常
            const existingException = await this.findSimilarException(exceptionEntry);
            if (existingException) {
                await this.updateExceptionOccurrence(existingException.id);
            } else {
                await this.saveExceptionToDatabase(exceptionEntry);
            }

            this.emitEvent('exceptionLogged', exceptionEntry);
        } catch (dbError) {
            console.error('保存异常失败:', dbError);
        }

        // 同时记录为错误日志
        this.error('异常记录', {
            exception: exceptionEntry,
            ...context
        }, 'exception');
    }

    /**
     * 确定异常严重程度
     */
    determineSeverity(error) {
        if (error.name === 'TypeError' || error.name === 'ReferenceError') {
            return 'high';
        } else if (error.name === 'NetworkError' || error.message.includes('network')) {
            return 'medium';
        } else {
            return 'low';
        }
    }

    /**
     * 查找相似异常
     */
    async findSimilarException(exceptionEntry) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('exceptions', 'readonly');
            const store = transaction.objectStore('exceptions');
            const index = store.index('type');
            const request = index.get(exceptionEntry.type);
            
            request.onsuccess = (event) => {
                const existing = event.target.result;
                if (existing && existing.message === exceptionEntry.message) {
                    resolve(existing);
                } else {
                    resolve(null);
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 更新异常出现次数
     */
    async updateExceptionOccurrence(exceptionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('exceptions', 'readwrite');
            const store = transaction.objectStore('exceptions');
            const request = store.get(exceptionId);
            
            request.onsuccess = (event) => {
                const exception = event.target.result;
                if (exception) {
                    exception.occurrences++;
                    exception.lastOccurred = new Date().toISOString();
                    store.put(exception);
                    resolve(exception);
                } else {
                    resolve(null);
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 保存异常到数据库
     */
    async saveExceptionToDatabase(exceptionEntry) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('exceptions', 'readwrite');
            const store = transaction.objectStore('exceptions');
            const request = store.add(exceptionEntry);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 记录审计日志
     */
    audit(action, resource, details = {}) {
        const auditEntry = {
            id: this.generateLogId(),
            timestamp: new Date().toISOString(),
            action,
            resource,
            details,
            userId: this.getCurrentUserId(),
            sessionId: this.getCurrentSessionId(),
            ip: this.getClientIP(),
            userAgent: navigator.userAgent
        };

        this.saveAuditToDatabase(auditEntry);
        
        this.info(`审计日志: ${action}`, {
            resource,
            ...details
        }, 'audit');
    }

    /**
     * 保存审计日志到数据库
     */
    async saveAuditToDatabase(auditEntry) {
        try {
            return new Promise((resolve, reject) => {
                const transaction = this.db.transaction('audit', 'readwrite');
                const store = transaction.objectStore('audit');
                const request = store.add(auditEntry);
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        } catch (error) {
            console.error('保存审计日志失败:', error);
        }
    }

    /**
     * 查询日志
     */
    async queryLogs(options = {}) {
        const {
            level,
            category,
            userId,
            startTime,
            endTime,
            limit = 100,
            offset = 0,
            store = 'logs'
        } = options;

        try {
            return new Promise((resolve, reject) => {
                const transaction = this.db.transaction(store, 'readonly');
                const storeObj = transaction.objectStore(store);
                let request;

                if (level) {
                    const index = storeObj.index('level');
                    request = index.getAll(level);
                } else {
                    request = storeObj.getAll();
                }

                request.onsuccess = (event) => {
                    let logs = event.target.result;

                    // 应用过滤条件
                    if (category) {
                        logs = logs.filter(log => log.category === category);
                    }
                    if (userId) {
                        logs = logs.filter(log => log.userId === userId);
                    }
                    if (startTime) {
                        logs = logs.filter(log => new Date(log.timestamp) >= new Date(startTime));
                    }
                    if (endTime) {
                        logs = logs.filter(log => new Date(log.timestamp) <= new Date(endTime));
                    }

                    // 排序和分页
                    logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                    const paginatedLogs = logs.slice(offset, offset + limit);

                    resolve({
                        logs: paginatedLogs,
                        total: logs.length,
                        offset,
                        limit
                    });
                };

                request.onerror = () => reject(request.error);
            });
        } catch (error) {
            console.error('查询日志失败:', error);
            return { logs: [], total: 0, offset, limit };
        }
    }

    /**
     * 获取错误统计
     */
    getErrorStats() {
        return { ...this.errorStats };
    }

    /**
     * 导出日志
     */
    async exportLogs(options = {}) {
        try {
            const logs = await this.queryLogs({ ...options, limit: 10000 });
            const exportData = {
                timestamp: new Date().toISOString(),
                total: logs.total,
                logs: logs.logs,
                config: this.logConfig
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `logs_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.info('日志导出完成', { count: logs.total });
            return true;
        } catch (error) {
            console.error('导出日志失败:', error);
            return false;
        }
    }

    /**
     * 更新配置
     */
    async updateConfig(newConfig) {
        try {
            this.logConfig = { ...this.logConfig, ...newConfig };
            
            // 保存配置到本地存储
            localStorage.setItem('system_log_config', JSON.stringify(this.logConfig));
            
            // 重新设置定时器
            this.setupAutoSync();
            this.setupAutoFlush();
            
            this.emitEvent('configUpdated', this.logConfig);
            console.log('日志配置更新完成');
            
            return true;
        } catch (error) {
            console.error('更新日志配置失败:', error);
            return false;
        }
    }

    /**
     * 辅助方法
     */
    generateLogId() {
        return `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getCurrentUserId() {
        return window.currentUser?.id || 'anonymous';
    }

    getCurrentSessionId() {
        return sessionStorage.getItem('session_id') || 'unknown';
    }

    getClientIP() {
        // 在实际应用中，这应该从服务器获取
        return 'client_ip';
    }

    /**
     * 便捷日志方法
     */
    debug(message, data = {}, category = 'general') {
        this.log('debug', message, data, category);
    }

    info(message, data = {}, category = 'general') {
        this.log('info', message, data, category);
    }

    warn(message, data = {}, category = 'general') {
        this.log('warn', message, data, category);
    }

    error(message, data = {}, category = 'general') {
        this.log('error', message, data, category);
    }

    fatal(message, data = {}, category = 'general') {
        this.log('fatal', message, data, category);
    }

    /**
     * 事件处理
     */
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    removeEventListener(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emitEvent(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`日志事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 销毁管理器
     */
    destroy() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
        }
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
        }
        
        // 最后一次刷新缓冲区
        this.flushBuffer();
        
        this.listeners.clear();
        this.isInitialized = false;
    }
}

// 创建全局实例
window.systemLogger = new SystemLogManager();

// 自动初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.systemLogger.initialize();
        console.log('系统日志管理器已准备就绪');
    } catch (error) {
        console.error('系统日志管理器初始化失败:', error);
    }
});

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemLogManager;
}
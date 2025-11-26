/**
 * logging.js - 操作日志记录系统
 * 提供全面的日志记录、查询、过滤和管理功能
 */

// 日志级别常量
const LOG_LEVELS = {
    DEBUG: 'debug',
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    CRITICAL: 'critical'
};

// 日志类型常量
const LOG_TYPES = {
    USER_ACTION: 'user_action',
    SYSTEM_EVENT: 'system_event',
    RULE_ACTION: 'rule_action',
    ADMIN_ACTION: 'admin_action',
    DATA_CHANGE: 'data_change',
    AUTHENTICATION: 'authentication'
};

// 日志存储键名
const LOG_STORAGE_KEY = 'mtscos_logs';
const LOG_CONFIG_KEY = 'mtscos_log_config';

// 默认配置
const DEFAULT_CONFIG = {
    maxLogs: 10000,           // 最大存储日志数量
    logLevel: LOG_LEVELS.INFO, // 默认日志级别
    autoCleanup: true,        // 自动清理旧日志
    cleanupInterval: 86400000, // 清理间隔（毫秒），默认24小时
    localStorage: true,       // 是否使用localStorage存储
    serverSync: false,        // 是否同步到服务器
    serverEndpoint: '/api/logs', // 服务器同步端点
    syncInterval: 300000      // 服务器同步间隔（毫秒），默认5分钟
};

// 日志管理模块
const Logging = (() => {
    // 私有变量
    let config = null;
    let logs = [];
    let syncTimer = null;
    let cleanupTimer = null;
    
    // 初始化
    function init() {
        // 加载配置
        loadConfig();
        
        // 加载现有日志
        loadLogs();
        
        // 启动自动清理
        if (config.autoCleanup) {
            startAutoCleanup();
        }
        
        // 启动服务器同步
        if (config.serverSync) {
            startServerSync();
        }
        
        // 添加错误监听
        addErrorListeners();
    }
    
    // 加载配置
    function loadConfig() {
        try {
            const savedConfig = localStorage.getItem(LOG_CONFIG_KEY);
            config = savedConfig ? { ...DEFAULT_CONFIG, ...JSON.parse(savedConfig) } : DEFAULT_CONFIG;
        } catch (error) {
            console.error('加载日志配置失败:', error);
            config = DEFAULT_CONFIG;
        }
    }
    
    // 保存配置
    function saveConfig() {
        try {
            localStorage.setItem(LOG_CONFIG_KEY, JSON.stringify(config));
        } catch (error) {
            console.error('保存日志配置失败:', error);
        }
    }
    
    // 加载日志
    function loadLogs() {
        if (!config.localStorage) return;
        
        try {
            const savedLogs = localStorage.getItem(LOG_STORAGE_KEY);
            logs = savedLogs ? JSON.parse(savedLogs) : [];
        } catch (error) {
            console.error('加载日志失败:', error);
            logs = [];
        }
    }
    
    // 保存日志
    function saveLogs() {
        if (!config.localStorage) return;
        
        try {
            localStorage.setItem(LOG_STORAGE_KEY, JSON.stringify(logs));
        } catch (error) {
            console.error('保存日志失败:', error);
        }
    }
    
    // 添加错误监听
    function addErrorListeners() {
        // 监听未捕获的JavaScript错误
        window.addEventListener('error', (errorEvent) => {
            logError(
                'JavaScript错误',
                `错误: ${errorEvent.message}\n文件: ${errorEvent.filename}\n行: ${errorEvent.lineno}\n列: ${errorEvent.colno}`,
                { error: errorEvent.error ? errorEvent.error.stack : '无堆栈信息' }
            );
        });
        
        // 监听未处理的Promise拒绝
        window.addEventListener('unhandledrejection', (rejectionEvent) => {
            logError(
                'Promise拒绝',
                `原因: ${rejectionEvent.reason?.message || String(rejectionEvent.reason)}`,
                { rejectionEvent: rejectionEvent }
            );
        });
    }
    
    // 开始自动清理
    function startAutoCleanup() {
        // 清除可能存在的旧定时器
        if (cleanupTimer) {
            clearInterval(cleanupTimer);
        }
        
        // 设置新定时器
        cleanupTimer = setInterval(() => {
            cleanupOldLogs();
        }, config.cleanupInterval);
    }
    
    // 开始服务器同步
    function startServerSync() {
        // 清除可能存在的旧定时器
        if (syncTimer) {
            clearInterval(syncTimer);
        }
        
        // 设置新定时器
        syncTimer = setInterval(() => {
            syncLogsToServer();
        }, config.syncInterval);
    }
    
    // 清理旧日志
    function cleanupOldLogs() {
        if (logs.length <= config.maxLogs) return;
        
        // 计算需要删除的日志数量
        const logsToDelete = logs.length - config.maxLogs;
        
        // 删除最旧的日志
        logs.splice(0, logsToDelete);
        
        // 保存更新后的日志
        saveLogs();
        
        // 记录清理操作
        logInfo('日志自动清理', `已清理 ${logsToDelete} 条旧日志`);
    }
    
    // 同步日志到服务器
    function syncLogsToServer() {
        if (!config.serverSync) return;
        
        // 获取未同步的日志
        const unsyncedLogs = logs.filter(log => !log.synced);
        
        if (unsyncedLogs.length === 0) return;
        
        // 在实际应用中，这里应该发送日志到服务器
        console.log(`准备同步 ${unsyncedLogs.length} 条日志到服务器`);
        
        // 模拟同步
        setTimeout(() => {
            // 标记日志为已同步
            unsyncedLogs.forEach(log => {
                const logIndex = logs.findIndex(l => l.id === log.id);
                if (logIndex !== -1) {
                    logs[logIndex].synced = true;
                    logs[logIndex].syncedAt = new Date().toISOString();
                }
            });
            
            // 保存更新后的日志
            saveLogs();
            
            console.log(`已同步 ${unsyncedLogs.length} 条日志到服务器`);
        }, 1000);
    }
    
    // 生成日志ID
    function generateLogId() {
        return 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // 获取当前用户
    function getCurrentUser() {
        try {
            // 假设Auth模块可用
            if (window.Auth && typeof Auth.getCurrentUser === 'function') {
                const user = Auth.getCurrentUser();
                return user ? user.username || 'unknown_user' : 'unknown_user';
            }
        } catch (error) {
            console.error('获取当前用户失败:', error);
        }
        return 'unknown_user';
    }
    
    // 记录日志的基础函数
    function log(level, type, message, details = {}) {
        // 检查日志级别是否应该记录
        if (getLogLevelPriority(level) < getLogLevelPriority(config.logLevel)) {
            return;
        }
        
        // 创建日志条目
        const logEntry = {
            id: generateLogId(),
            timestamp: new Date().toISOString(),
            level: level,
            type: type,
            message: message,
            details: details,
            user: getCurrentUser(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            synced: false
        };
        
        // 添加到日志数组
        logs.push(logEntry);
        
        // 限制日志数量
        if (logs.length > config.maxLogs) {
            logs.shift(); // 删除最旧的日志
        }
        
        // 保存日志
        saveLogs();
        
        // 控制台输出
        console[level === 'warning' ? 'warn' : level === 'error' || level === 'critical' ? 'error' : 'log'](
            `[${formatDate(logEntry.timestamp)}] [${level.toUpperCase()}] [${type}] ${message}`,
            details
        );
        
        // 如果是错误或严重错误，尝试同步到服务器
        if ((level === LOG_LEVELS.ERROR || level === LOG_LEVELS.CRITICAL) && config.serverSync) {
            syncLogsToServer();
        }
        
        return logEntry.id;
    }
    
    // 获取日志级别优先级
    function getLogLevelPriority(level) {
        const priorities = {
            [LOG_LEVELS.DEBUG]: 0,
            [LOG_LEVELS.INFO]: 1,
            [LOG_LEVELS.WARNING]: 2,
            [LOG_LEVELS.ERROR]: 3,
            [LOG_LEVELS.CRITICAL]: 4
        };
        return priorities[level] || 1;
    }
    
    // 格式化日期
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    // 导出公开方法
    return {
        // 初始化方法
        init: init,
        
        // 日志记录方法
        logDebug: (message, details = {}) => log(LOG_LEVELS.DEBUG, LOG_TYPES.SYSTEM_EVENT, message, details),
        logInfo: (message, details = {}) => log(LOG_LEVELS.INFO, LOG_TYPES.SYSTEM_EVENT, message, details),
        logWarning: (message, details = {}) => log(LOG_LEVELS.WARNING, LOG_TYPES.SYSTEM_EVENT, message, details),
        logError: (message, details = {}) => log(LOG_LEVELS.ERROR, LOG_TYPES.SYSTEM_EVENT, message, details),
        logCritical: (message, details = {}) => log(LOG_LEVELS.CRITICAL, LOG_TYPES.SYSTEM_EVENT, message, details),
        
        // 用户操作日志
        logAction: (action, details = {}) => log(LOG_LEVELS.INFO, LOG_TYPES.USER_ACTION, action, details),
        
        // 管理员操作日志
        logAdminAction: (action, details = {}) => log(LOG_LEVELS.INFO, LOG_TYPES.ADMIN_ACTION, action, details),
        
        // 规则操作日志
        logRuleAction: (action, details = {}) => log(LOG_LEVELS.INFO, LOG_TYPES.RULE_ACTION, action, details),
        
        // 数据变更日志
        logDataChange: (action, details = {}) => log(LOG_LEVELS.INFO, LOG_TYPES.DATA_CHANGE, action, details),
        
        // 认证相关日志
        logAuth: (action, details = {}) => log(LOG_LEVELS.INFO, LOG_TYPES.AUTHENTICATION, action, details),
        
        // 查询日志
        getLogs: () => [...logs],
        
        // 搜索日志
        searchLogs: (params) => {
            let filteredLogs = [...logs];
            
            // 根据时间范围过滤
            if (params.startDate) {
                const startDate = new Date(params.startDate);
                filteredLogs = filteredLogs.filter(log => new Date(log.timestamp) >= startDate);
            }
            
            if (params.endDate) {
                const endDate = new Date(params.endDate);
                filteredLogs = filteredLogs.filter(log => new Date(log.timestamp) <= endDate);
            }
            
            // 根据日志级别过滤
            if (params.level) {
                filteredLogs = filteredLogs.filter(log => log.level === params.level);
            }
            
            // 根据日志类型过滤
            if (params.type) {
                filteredLogs = filteredLogs.filter(log => log.type === params.type);
            }
            
            // 根据用户过滤
            if (params.user) {
                filteredLogs = filteredLogs.filter(log => log.user.toLowerCase().includes(params.user.toLowerCase()));
            }
            
            // 根据关键词过滤
            if (params.keyword) {
                const keyword = params.keyword.toLowerCase();
                filteredLogs = filteredLogs.filter(log => 
                    log.message.toLowerCase().includes(keyword) ||
                    JSON.stringify(log.details).toLowerCase().includes(keyword)
                );
            }
            
            // 排序
            filteredLogs.sort((a, b) => 
                params.sortBy === 'timestamp' && params.order === 'asc' 
                    ? new Date(a.timestamp) - new Date(b.timestamp)
                    : new Date(b.timestamp) - new Date(a.timestamp)
            );
            
            // 分页
            if (params.page && params.pageSize) {
                const startIndex = (params.page - 1) * params.pageSize;
                filteredLogs = filteredLogs.slice(startIndex, startIndex + params.pageSize);
            }
            
            return filteredLogs;
        },
        
        // 获取日志统计
        getLogStats: () => {
            const stats = {
                total: logs.length,
                byLevel: {},
                byType: {},
                byUser: {},
                today: 0,
                yesterday: 0
            };
            
            // 初始化统计数据
            Object.values(LOG_LEVELS).forEach(level => {
                stats.byLevel[level] = 0;
            });
            
            Object.values(LOG_TYPES).forEach(type => {
                stats.byType[type] = 0;
            });
            
            // 获取今天和昨天的日期
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            
            // 统计
            logs.forEach(log => {
                // 按级别统计
                if (stats.byLevel[log.level] !== undefined) {
                    stats.byLevel[log.level]++;
                }
                
                // 按类型统计
                if (stats.byType[log.type] !== undefined) {
                    stats.byType[log.type]++;
                }
                
                // 按用户统计
                if (!stats.byUser[log.user]) {
                    stats.byUser[log.user] = 0;
                }
                stats.byUser[log.user]++;
                
                // 统计今天和昨天的日志
                const logDate = new Date(log.timestamp);
                logDate.setHours(0, 0, 0, 0);
                
                if (logDate.getTime() === today.getTime()) {
                    stats.today++;
                } else if (logDate.getTime() === yesterday.getTime()) {
                    stats.yesterday++;
                }
            });
            
            return stats;
        },
        
        // 导出日志
        exportLogs: (format = 'json') => {
            let content = '';
            
            if (format === 'json') {
                content = JSON.stringify(logs, null, 2);
            } else if (format === 'csv') {
                // 生成CSV头部
                content = 'ID,时间戳,级别,类型,消息,用户,URL\n';
                
                // 生成CSV数据行
                logs.forEach(log => {
                    const row = [
                        log.id,
                        log.timestamp,
                        log.level,
                        log.type,
                        `"${log.message.replace(/"/g, '""')}"`,
                        log.user,
                        `"${log.url.replace(/"/g, '""')}"`
                    ];
                    content += row.join(',') + '\n';
                });
            } else if (format === 'txt') {
                logs.forEach(log => {
                    content += `[${formatDate(log.timestamp)}] [${log.level.toUpperCase()}] [${log.type}] [${log.user}] ${log.message}\n`;
                });
            }
            
            // 创建下载链接
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            
            a.href = url;
            a.download = `mtscos_logs_${new Date().toISOString().slice(0, 10)}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            // 记录导出操作
            logInfo('日志导出', `已导出 ${logs.length} 条日志，格式: ${format}`);
        },
        
        // 清除日志
        clearLogs: (beforeDate = null) => {
            let logsToRemove = 0;
            
            if (beforeDate) {
                const cutoffDate = new Date(beforeDate);
                logsToRemove = logs.length;
                logs = logs.filter(log => new Date(log.timestamp) > cutoffDate);
                logsToRemove -= logs.length;
            } else {
                logsToRemove = logs.length;
                logs = [];
            }
            
            // 保存更新后的日志
            saveLogs();
            
            // 记录清除操作
            logInfo('日志清除', `已清除 ${logsToRemove} 条日志`);
            
            return logsToRemove;
        },
        
        // 更新配置
        updateConfig: (newConfig) => {
            config = { ...config, ...newConfig };
            saveConfig();
            
            // 重启定时器
            if (config.autoCleanup) {
                startAutoCleanup();
            } else if (cleanupTimer) {
                clearInterval(cleanupTimer);
                cleanupTimer = null;
            }
            
            if (config.serverSync) {
                startServerSync();
            } else if (syncTimer) {
                clearInterval(syncTimer);
                syncTimer = null;
            }
            
            // 记录配置更新
            logInfo('日志配置更新', '日志系统配置已更新', newConfig);
        },
        
        // 获取配置
        getConfig: () => ({ ...config }),
        
        // 手动同步到服务器
        syncLogs: () => {
            return new Promise((resolve) => {
                syncLogsToServer();
                setTimeout(resolve, 1000); // 模拟异步操作
            });
        },
        
        // 日志级别常量
        LOG_LEVELS: LOG_LEVELS,
        
        // 日志类型常量
        LOG_TYPES: LOG_TYPES
    };
})();

// 等待DOM加载完成后初始化日志系统
document.addEventListener('DOMContentLoaded', function() {
    try {
        Logging.init();
        Logging.logInfo('日志系统初始化完成');
    } catch (error) {
        console.error('日志系统初始化失败:', error);
    }
});

// 暴露Logging对象到全局
globalThis.Logging = Logging;
/**
 * MTSCOS 统一错误处理器
 * 合并了 error-handler.js、error_handler.js 和 unified-error-handler.js 的功能
 * 提供完整的错误处理、性能监控和日志记录功能
 * 版本: 3.0.0 (统一版)
 */

// 防止重复定义
if (typeof MTSCOSUnifiedErrorHandler === 'undefined') {

// HTTP错误处理函数 - 统一版本
function fetchErrorHandler(response) {
    if (!response.ok) {
        const errorInfo = {
            status: response.status,
            statusText: response.statusText,
            url: response.url
        };

        // 记录到统一错误处理器
        if (window.MTSCOSUnifiedErrorHandler) {
            window.MTSCOSUnifiedErrorHandler.handleError({
                type: 'HTTP_ERROR',
                message: `HTTP ${response.status}: ${response.statusText}`,
                status: response.status,
                url: response.url,
                timestamp: Date.now()
            });
        }

        if (response.status === 404) {
            console.error('资源未找到 (404):', response.url);
        } else if (response.status === 403) {
            console.error('访问被拒绝 (403):', response.url);
        } else if (response.status === 401) {
            console.error('未授权访问 (401):', response.url);
        } else if (response.status >= 500) {
            console.error('服务器错误:', response.status, response.statusText);
        } else {
            console.error('HTTP错误:', response.status, response.statusText);
        }

        throw new Error(`HTTP错误: ${response.status} - ${response.statusText}`);
    }

    return response;
}

class MTSCOSUnifiedErrorHandler {
    constructor() {
        this.version = '3.0.0';
        this.errorTypes = {
            HTTP_ERROR: 'HTTP_ERROR',
            LOGIN_ERROR: 'LOGIN_ERROR', 
            SECURITY_ERROR: 'SECURITY_ERROR',
            VALIDATION_ERROR: 'VALIDATION_ERROR',
            NETWORK_ERROR: 'NETWORK_ERROR',
            SYSTEM_ERROR: 'SYSTEM_ERROR',
            JAVASCRIPT_ERROR: 'JAVASCRIPT_ERROR',
            RESOURCE_ERROR: 'RESOURCE_ERROR',
            PROMISE_ERROR: 'PROMISE_ERROR'
        };
        
        // 错误日志和统计
        this.errorLog = [];
        this.errorCounts = {};
        this.maxLogSize = 1000;
        this.maxErrorsPerType = 10;
        
        // 性能监控
        this.performanceMetrics = {
            pageLoad: null,
            apiCalls: new Map(),
            userInteractions: new Map(),
            memoryUsage: [],
            errors: []
        };
        
        // 配置
        this.config = {
            maxErrorLogSize: 100,
            maxPerformanceLogSize: 50,
            enableConsoleLogging: true,
            enableRemoteLogging: false,
            remoteLogEndpoint: '/api/logs',
            enableUserNotifications: true,
            enablePerformanceMonitoring: true
        };
        
        this.isInitialized = false;
        this.init();
    }

    /**
     * 初始化错误处理器
     */
    init() {
        if (this.isInitialized) return;
        
        this.setupGlobalErrorHandlers();
        this.setupUnhandledRejectionHandler();
        
        if (this.config.enablePerformanceMonitoring) {
            this.setupPerformanceObservers();
            this.setupMemoryMonitoring();
            this.setupNetworkMonitoring();
        }
        
        this.isInitialized = true;
        console.log(`[MTSCOS统一错误处理器] v${this.version} 初始化完成`);
    }

    /**
     * 设置全局错误处理器
     */
    setupGlobalErrorHandlers() {
        // JavaScript运行时错误
        window.addEventListener('error', (event) => {
            if (event.target === window) {
                this.handleError({
                    type: this.errorTypes.JAVASCRIPT_ERROR,
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    stack: event.error?.stack,
                    timestamp: Date.now()
                });
            } else {
                // 资源加载错误
                this.handleError({
                    type: this.errorTypes.RESOURCE_ERROR,
                    message: `Failed to load ${event.target.tagName}`,
                    source: event.target.src || event.target.href,
                    element: event.target.tagName,
                    timestamp: Date.now()
                });
            }
        }, true);
    }

    /**
     * 设置未处理的Promise拒绝处理器
     */
    setupUnhandledRejectionHandler() {
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                type: this.errorTypes.PROMISE_ERROR,
                message: event.reason?.message || String(event.reason),
                reason: event.reason,
                promise: event.promise,
                timestamp: Date.now()
            });
            
            // 防止错误在控制台显示
            event.preventDefault();
        });
    }

    /**
     * 设置性能观察器
     */
    setupPerformanceObservers() {
        // 页面加载性能
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    this.recordPageLoadPerformance();
                }, 0);
            });
        }

        // 长任务监控
        if ('PerformanceObserver' in window) {
            try {
                const longTaskObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.recordLongTask(entry);
                    }
                });
                longTaskObserver.observe({ entryTypes: ['longtask'] });
            } catch (error) {
                console.warn('长任务监控不支持:', error);
            }
        }
    }

    /**
     * 设置内存监控
     */
    setupMemoryMonitoring() {
        if ('memory' in performance) {
            setInterval(() => {
                this.recordMemoryUsage();
            }, 30000); // 每30秒记录一次
        }
    }

    /**
     * 设置网络监控
     */
    setupNetworkMonitoring() {
        // 监控fetch请求
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const url = args[0];
            
            try {
                const response = await originalFetch(...args);
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                this.recordApiCall(url, 'success', duration, response.status);
                return response;
            } catch (error) {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                this.recordApiCall(url, 'error', duration, null, error);
                throw error;
            }
        };
    }

    /**
     * 处理错误的核心方法
     */
    handleError(errorInfo) {
        try {
            // 生成错误ID
            const errorId = this.generateErrorId();
            const timestamp = new Date().toISOString();
            
            const error = {
                id: errorId,
                timestamp,
                url: window.location.href,
                userAgent: navigator.userAgent,
                ...errorInfo
            };
            
            // 记录错误
            this.logError(error);
            
            // 更新错误计数
            this.updateErrorCount(errorInfo.type);
            
            // 根据错误类型进行处理
            this.handleSpecificError(error);
            
            // 检查错误阈值
            this.checkErrorThreshold(errorInfo.type);
            
        } catch (handlingError) {
            console.error('[MTSCOS统一错误处理器] 错误处理失败:', handlingError);
        }
    }

    /**
     * 处理特定类型的错误
     */
    handleSpecificError(error) {
        switch(error.type) {
            case this.errorTypes.HTTP_ERROR:
                this.handleHttpError(error);
                break;
            case this.errorTypes.LOGIN_ERROR:
                this.handleLoginError(error);
                break;
            case this.errorTypes.SECURITY_ERROR:
                this.handleSecurityError(error);
                break;
            case this.errorTypes.VALIDATION_ERROR:
                this.handleValidationError(error);
                break;
            case this.errorTypes.NETWORK_ERROR:
            case this.errorTypes.RESOURCE_ERROR:
                this.handleNetworkError(error);
                break;
            case this.errorTypes.JAVASCRIPT_ERROR:
                this.handleJavaScriptError(error);
                break;
            case this.errorTypes.PROMISE_ERROR:
                this.handlePromiseError(error);
                break;
            case this.errorTypes.SYSTEM_ERROR:
            default:
                this.handleSystemError(error);
                break;
        }
    }

    /**
     * 处理HTTP错误
     */
    handleHttpError(error) {
        console.error(`[HTTP错误] ${error.message}`);
        
        if (error.status) {
            switch(error.status) {
                case 401:
                    this.showUserMessage('登录已过期，请重新登录', 'warning');
                    this.redirectToLogin();
                    break;
                case 403:
                    this.showUserMessage('访问被拒绝，权限不足', 'error');
                    break;
                case 404:
                    console.warn(`[404] 资源未找到: ${error.url}`);
                    break;
                case 500:
                    this.showUserMessage('服务器内部错误，请稍后重试', 'error');
                    break;
                default:
                    this.showUserMessage(`网络错误: ${error.status}`, 'error');
            }
        }
    }

    /**
     * 处理登录错误
     */
    handleLoginError(error) {
        console.error(`[登录错误] ${error.message}`);
        
        if (error.message.includes('不支持的登录方式')) {
            this.showUserMessage('暂不支持此登录方式，请选择其他登录方式', 'warning');
        } else {
            this.showUserMessage(error.message || '登录失败，请重试', 'error');
        }
    }

    /**
     * 处理安全错误
     */
    handleSecurityError(error) {
        console.error(`[安全错误] ${error.message}`);
        
        if (error.message.includes('危险标签')) {
            console.warn('[安全警告] 检测到潜在的脚本注入尝试，已阻止');
        } else {
            this.showUserMessage('安全检查失败，操作已阻止', 'error');
        }
    }

    /**
     * 处理验证错误
     */
    handleValidationError(error) {
        console.warn(`[验证错误] ${error.message}`);
        this.showUserMessage(error.message || '输入验证失败', 'warning');
    }

    /**
     * 处理网络错误
     */
    handleNetworkError(error) {
        console.error(`[网络错误] ${error.message}`);
        this.showUserMessage('网络连接异常，请检查网络设置', 'error');
    }

    /**
     * 处理JavaScript错误
     */
    handleJavaScriptError(error) {
        console.error(`[JavaScript错误] ${error.message}`);
        
        if (this.isCriticalFunction(error.filename, error.message)) {
            this.showUserMessage('系统功能出现问题，正在尝试恢复...', 'warning');
        }
    }

    /**
     * 处理Promise错误
     */
    handlePromiseError(error) {
        console.warn(`[Promise错误] ${error.message}`);
    }

    /**
     * 处理系统错误
     */
    handleSystemError(error) {
        console.error(`[系统错误] ${error.message}`);
        this.showUserMessage('系统出现异常，请稍后重试', 'error');
    }

    /**
     * 记录错误日志
     */
    logError(error) {
        this.errorLog.push(error);
        
        // 限制日志大小
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift();
        }
        
        // 输出到控制台
        if (this.config.enableConsoleLogging) {
            console.error('[MTSCOS错误]', error);
        }
        
        // 保存到本地存储
        this.saveErrorLog();
        
        // 远程日志记录
        if (this.config.enableRemoteLogging) {
            this.sendErrorToRemote(error);
        }
    }

    /**
     * 更新错误计数
     */
    updateErrorCount(errorType) {
        if (!this.errorCounts[errorType]) {
            this.errorCounts[errorType] = 0;
        }
        this.errorCounts[errorType]++;
    }

    /**
     * 检查错误阈值
     */
    checkErrorThreshold(errorType) {
        const count = this.errorCounts[errorType] || 0;
        
        if (count >= this.maxErrorsPerType) {
            this.showUserMessage(
                `检测到多个${this.getErrorTypeName(errorType)}错误，建议刷新页面`, 
                'error'
            );
        }
    }

    /**
     * 获取错误类型名称
     */
    getErrorTypeName(type) {
        const typeNames = {
            [this.errorTypes.HTTP_ERROR]: 'HTTP',
            [this.errorTypes.LOGIN_ERROR]: '登录',
            [this.errorTypes.SECURITY_ERROR]: '安全',
            [this.errorTypes.VALIDATION_ERROR]: '验证',
            [this.errorTypes.NETWORK_ERROR]: '网络',
            [this.errorTypes.SYSTEM_ERROR]: '系统',
            [this.errorTypes.JAVASCRIPT_ERROR]: 'JavaScript',
            [this.errorTypes.RESOURCE_ERROR]: '资源',
            [this.errorTypes.PROMISE_ERROR]: 'Promise'
        };
        
        return typeNames[type] || '未知';
    }

    /**
     * 检查是否是关键功能
     */
    isCriticalFunction(filename, message) {
        const criticalFunctions = [
            'theme-manager',
            'login',
            'authentication',
            'api-client',
            'error-handler'
        ];
        
        return criticalFunctions.some(func => 
            filename.includes(func) || message.includes(func)
        );
    }

    /**
     * 显示用户消息
     */
    showUserMessage(message, type = 'error') {
        if (!this.config.enableUserNotifications) return;
        
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ff6b6b' : type === 'warning' ? '#ffa726' : '#66bb6a'};
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // 自动移除
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * 重定向到登录页面
     */
    redirectToLogin() {
        setTimeout(() => {
            window.location.href = '/HTML/login.html';
        }, 2000);
    }

    /**
     * 生成错误ID
     */
    generateErrorId() {
        return 'error_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 保存错误日志到本地存储
     */
    saveErrorLog() {
        try {
            localStorage.setItem('mtscos_error_log', JSON.stringify(this.errorLog));
            localStorage.setItem('mtscos_error_counts', JSON.stringify(this.errorCounts));
        } catch (e) {
            console.warn('无法保存错误日志到本地存储:', e);
        }
    }

    /**
     * 从本地存储加载错误日志
     */
    loadErrorLog() {
        try {
            const savedLog = localStorage.getItem('mtscos_error_log');
            const savedCounts = localStorage.getItem('mtscos_error_counts');
            
            if (savedLog) {
                this.errorLog = JSON.parse(savedLog);
            }
            if (savedCounts) {
                this.errorCounts = JSON.parse(savedCounts);
            }
        } catch (e) {
            console.warn('无法从本地存储加载错误日志:', e);
        }
    }

    /**
     * 发送错误到远程服务器
     */
    async sendErrorToRemote(error) {
        try {
            await fetch(this.config.remoteLogEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(error)
            });
        } catch (e) {
            console.warn('Failed to send error to remote server:', e);
        }
    }

    // 性能监控相关方法
    recordPageLoadPerformance() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            this.performanceMetrics.pageLoad = {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                totalTime: navigation.loadEventEnd - navigation.navigationStart,
                dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                tcpConnection: navigation.connectEnd - navigation.connectStart,
                requestTime: navigation.responseEnd - navigation.requestStart,
                timestamp: Date.now()
            };

            console.log('页面加载性能指标:', this.performanceMetrics.pageLoad);
        }
    }

    recordLongTask(entry) {
        this.logWarning('Long Task Detected', {
            duration: entry.duration,
            startTime: entry.startTime,
            timestamp: Date.now()
        });
    }

    recordMemoryUsage() {
        if (performance.memory) {
            const memory = {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit,
                timestamp: Date.now()
            };
            
            this.performanceMetrics.memoryUsage.push(memory);
            
            // 限制记录数量
            if (this.performanceMetrics.memoryUsage.length > 50) {
                this.performanceMetrics.memoryUsage.shift();
            }
        }
    }

    recordApiCall(url, status, duration, responseStatus, error = null) {
        if (!this.performanceMetrics.apiCalls.has(url)) {
            this.performanceMetrics.apiCalls.set(url, {
                count: 0,
                successCount: 0,
                errorCount: 0,
                totalDuration: 0,
                averageDuration: 0,
                lastStatus: null
            });
        }
        
        const metrics = this.performanceMetrics.apiCalls.get(url);
        metrics.count++;
        metrics.totalDuration += duration;
        metrics.averageDuration = metrics.totalDuration / metrics.count;
        metrics.lastStatus = status;
        
        if (status === 'success') {
            metrics.successCount++;
        } else {
            metrics.errorCount++;
        }
    }

    recordUserInteraction(type, target, data = {}) {
        const key = `${type}_${target}`;
        if (!this.performanceMetrics.userInteractions.has(key)) {
            this.performanceMetrics.userInteractions.set(key, {
                count: 0,
                totalTime: 0,
                averageTime: 0
            });
        }
        
        const interaction = this.performanceMetrics.userInteractions.get(key);
        interaction.count++;
        
        if (data.duration) {
            interaction.totalTime += data.duration;
            interaction.averageTime = interaction.totalTime / interaction.count;
        }
    }

    logWarning(message, data = {}) {
        this.handleError({
            type: this.errorTypes.SYSTEM_ERROR,
            message,
            severity: 'warning',
            ...data
        });
    }

    logInfo(message, data = {}) {
        if (this.config.enableConsoleLogging) {
            console.log(`[MTSCOS信息] ${message}`, data);
        }
    }

    /**
     * 获取性能报告
     */
    getPerformanceReport() {
        return {
            pageLoad: this.performanceMetrics.pageLoad,
            apiCalls: Object.fromEntries(this.performanceMetrics.apiCalls),
            userInteractions: Object.fromEntries(this.performanceMetrics.userInteractions),
            memoryUsage: this.performanceMetrics.memoryUsage.slice(-10),
            errors: this.errorLog.slice(-10),
            summary: this.generatePerformanceSummary()
        };
    }

    /**
     * 生成性能摘要
     */
    generatePerformanceSummary() {
        const summary = {
            totalErrors: this.errorLog.length,
            totalApiCalls: Array.from(this.performanceMetrics.apiCalls.values())
                .reduce((sum, metrics) => sum + metrics.count, 0),
            averageResponseTime: this.calculateAverageResponseTime(),
            memoryTrend: this.calculateMemoryTrend(),
            performanceScore: this.calculatePerformanceScore()
        };

        return summary;
    }

    calculateAverageResponseTime() {
        const allApiCalls = Array.from(this.performanceMetrics.apiCalls.values());
        if (allApiCalls.length === 0) return 0;
        
        const totalDuration = allApiCalls.reduce((sum, metrics) => sum + metrics.totalDuration, 0);
        const totalCount = allApiCalls.reduce((sum, metrics) => sum + metrics.count, 0);
        
        return totalCount > 0 ? totalDuration / totalCount : 0;
    }

    calculateMemoryTrend() {
        const memoryUsage = this.performanceMetrics.memoryUsage;
        if (memoryUsage.length < 2) return 'stable';
        
        const recent = memoryUsage.slice(-5);
        const first = recent[0].used;
        const last = recent[recent.length - 1].used;
        
        const change = (last - first) / first;
        
        if (change > 0.1) return 'increasing';
        if (change < -0.1) return 'decreasing';
        return 'stable';
    }

    calculatePerformanceScore() {
        let score = 100;
        
        score -= Math.min(30, this.errorLog.length * 2);
        
        const slowRequests = Array.from(this.performanceMetrics.apiCalls.values())
            .filter(metrics => metrics.averageDuration > 3000).length;
        score -= Math.min(20, slowRequests * 5);
        
        if (this.performanceMetrics.memoryUsage.length > 0) {
            const latestMemory = this.performanceMetrics.memoryUsage[this.performanceMetrics.memoryUsage.length - 1];
            const memoryRatio = latestMemory.used / latestMemory.limit;
            if (memoryRatio > 0.8) score -= 20;
            else if (memoryRatio > 0.6) score -= 10;
        }
        
        return Math.max(0, score);
    }

    /**
     * 清理日志
     */
    clearLogs() {
        this.errorLog = [];
        this.errorCounts = {};
        this.performanceMetrics.errors = [];
        this.performanceMetrics.memoryUsage = [];
        
        // 清理本地存储
        localStorage.removeItem('mtscos_error_log');
        localStorage.removeItem('mtscos_error_counts');
        
        console.log('错误日志已清理');
    }

    /**
     * 导出日志
     */
    exportLogs() {
        const logs = {
            errors: this.errorLog,
            errorCounts: this.errorCounts,
            performanceMetrics: this.performanceMetrics,
            exportTime: Date.now(),
            version: this.version
        };
        
        const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mtscos-unified-logs-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * 获取错误统计
     */
    getErrorStats() {
        return {
            totalErrors: this.errorLog.length,
            errorCounts: { ...this.errorCounts },
            recentErrors: this.errorLog.slice(-5),
            mostCommonError: this.getMostCommonErrorType()
        };
    }

    getMostCommonErrorType() {
        let maxCount = 0;
        let mostCommon = null;
        
        for (const [type, count] of Object.entries(this.errorCounts)) {
            if (count > maxCount) {
                maxCount = count;
                mostCommon = type;
            }
        }
        
        return mostCommon;
    }
}

// 创建全局实例
window.MTSCOSUnifiedErrorHandler = new MTSCOSUnifiedErrorHandler();

// 向后兼容：创建别名
window.MTSCOSErrorHandler = window.MTSCOSUnifiedErrorHandler;
window.errorHandler = window.MTSCOSUnifiedErrorHandler;
window.unifiedErrorHandler = window.MTSCOSUnifiedErrorHandler;

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MTSCOSUnifiedErrorHandler;
}

} // 结束 typeof MTSCOSUnifiedErrorHandler === 'undefined' 检查
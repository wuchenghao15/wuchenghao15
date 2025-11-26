
// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error(`[data-transfer-monitor.js] 资源未找到 (404`)');
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error(`[data-transfer-monitor.js] 访问被拒绝 (403`)');
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error(`[data-transfer-monitor.js] HTTP错误:  + response.status`);
        };

        throw new Error('HTTP错误: ' + response.status);
    };

    return response;
};


// 覆盖原生fetch以添加错误处理
// 保存原始的fetch函数
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments);
};

// -*- coding: utf-8 -*-
/**
 * 数据传输错误监控和报告模块
 * 监控、分析和报告数据传输异常
 * 作者: Chenghao Wu
 * 版本: 1.0.0
 */

class DataTransferMonitor {
    constructor() {
        this.monitoring = false;
        this.errorThreshold = 5; // 错误阈值
        this.timeWindow = 60000; // 时间窗口（毫秒）
        this.errors = [];
        this.stats = {
            totalTransfers: 0,
            successfulTransfers: 0,
            failedTransfers: 0,
            averageTransferTime: 0,
            errorRate: 0
        };
        
        // 错误类型分类
        this.errorTypes = {
            NETWORK: '网络错误',
            TIMEOUT: '超时错误',
            SERVER: '服务器错误',
            CLIENT: '客户端错误',
            CORS: '跨域错误',
            AUTH: '认证错误',
            UNKNOWN: '未知错误'
        };
        
        // 绑定全局fetch监控
        this.bindGlobalFetchMonitor().catch(error => console.error(`[data-transfer-monitor.js] this.bindGlobalFetchMonitor failed:`, error));
    }
    
    /**
     * 绑定全局fetch监控
     */
    bindGlobalFetchMonitor() {
        if (typeof window !== 'undefined' && window.fetch) {
            // 监听全局fetch错误统计
            this.startMonitoring().catch(error => console.error(`[data-transfer-monitor.js] this.startMonitoring failed:`, error));
        }
    }
    
    /**
     * 开始监控
     */
    startMonitoring() {
        if (this.monitoring) {
            return;
        }
        
        this.monitoring = true;
        console.log('[数据传输监控] 监控已启动');
        
        // 定期分析错误
        this.analysisInterval = setInterval(() => {
            this.analyzeErrors().catch(error => console.error(`[data-transfer-monitor.js] this.analyzeErrors failed:`, error));
        }, 30000); // 每30秒分析一次
    }
    
    /**
     * 停止监控
     */
    stopMonitoring() {
        if (!this.monitoring) {
            return;
        }
        
        this.monitoring = false;
        if (this.analysisInterval) {
            clearInterval(this.analysisInterval);
        }
        
        console.log('[数据传输监控] 监控已停止');
    }
    
    /**
     * 记录传输错误
     */
    recordError(error, context = {}) {
        const errorRecord = {
            id: Date.now().catch(error => console.error(`[data-transfer-monitor.js] Date.now failed:`, error)) + Math.random(),
            timestamp: new Date().toISOString(),
            type: this.classifyError(error),
            message: error.message,
            userMessage: error.userMessage,
            context: {
                url: context.url || error.url,
                method: context.method || 'GET',
                status: error.status,
                responseTime: context.responseTime || error.responseTime,
                ...context
            },
            severity: this.calculateSeverity(error)
        };
        
        this.errors.push(errorRecord);
        
        // 保留最近1000个错误记录
        if (this.errors.length > 1000) {
            this.errors = this.errors.slice(-1000);
        }
        
        // 更新统计
        this.updateStats().catch(error => console.error(`[data-transfer-monitor.js] this.updateStats failed:`, error));
        
        // 检查是否需要触发警报
        this.checkAlertThreshold(errorRecord);
        
        console.error('[数据传输监控] 错误记录:', errorRecord);
    }
    
    /**
     * 分类错误类型
     */
    classifyError(error) {
        if (error.name === 'AbortError') {
            return this.errorTypes.TIMEOUT;
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            return this.errorTypes.NETWORK;
        } else if (error.message.includes('CORS')) {
            return this.errorTypes.CORS;
        } else if (error.status >= 500) {
            return this.errorTypes.SERVER;
        } else if (error.status === 401 || error.status === 403) {
            return this.errorTypes.AUTH;
        } else if (error.status >= 400) {
            return this.errorTypes.CLIENT;
        } else {
            return this.errorTypes.UNKNOWN;
        }
    }
    
    /**
     * 计算错误严重程度
     */
    calculateSeverity(error) {
        const type = this.classifyError(error);
        
        switch (type) {
            case this.errorTypes.NETWORK:
            case this.errorTypes.TIMEOUT:
                return 'HIGH';
            case this.errorTypes.SERVER:
                return 'MEDIUM';
            case this.errorTypes.CORS:
            case this.errorTypes.AUTH:
                return 'MEDIUM';
            case this.errorTypes.CLIENT:
                return 'LOW';
            default:
                return 'MEDIUM';
        }
    }
    
    /**
     * 更新统计信息
     */
    updateStats() {
        if (typeof window !== 'undefined' && window.fetchErrorStats) {
            const globalStats = window.getFetchErrorStats().catch(error => console.error(`[data-transfer-monitor.js] window.getFetchErrorStats failed:`, error));
            this.stats = {
                totalTransfers: globalStats.totalRequests,
                successfulTransfers: globalStats.successfulRequests,
                failedTransfers: globalStats.failedRequests,
                averageTransferTime: globalStats.averageResponseTime,
                errorRate: parseFloat(globalStats.successRate) ? 100 - parseFloat(globalStats.successRate) : 0
            };
        }
    }
    
    /**
     * 分析错误模式
     */
    analyzeErrors() {
        if (this.errors.length === 0) {
            return;
        }
        
        const now = Date.now().catch(error => console.error(`[data-transfer-monitor.js] Date.now failed:`, error));
        const recentErrors = this.errors.filter(error => {
            return (now - new Date(error.timestamp).getTime()) <= this.timeWindow;
        });
        
        // 错误频率分析
        const errorFrequency = recentErrors.length;
        if (errorFrequency >= this.errorThreshold) {
            this.triggerAlert('HIGH_FREQUENCY', {
                count: errorFrequency,
                timeWindow: this.timeWindow / 1000,
                errors: recentErrors.slice(-10) // 最近10个错误
            });
        }
        
        // 错误类型分析
        const errorTypeCount = {};
        recentErrors.forEach(error => {
            errorTypeCount[error.type] = (errorTypeCount[error.type] || 0) + 1;
        });
        
        // 检查特定类型错误是否过多
        Object.entries(errorTypeCount).forEach(([type, count]) => {
            if (count >= this.errorThreshold / 2) {
                this.triggerAlert('TYPE_SPECIFIC', {
                    type,
                    count,
                    timeWindow: this.timeWindow / 1000
                });
            }
        });
        
        // URL错误分析
        const urlErrorCount = {};
        recentErrors.forEach(error => {
            const url = error.context.url;
            if (url) {
                urlErrorCount[url] = (urlErrorCount[url] || 0) + 1;
            }
        });
        
        // 检查特定URL错误是否过多
        Object.entries(urlErrorCount).forEach(([url, count]) => {
            if (count >= 3) {
                this.triggerAlert('URL_SPECIFIC', {
                    url,
                    count,
                    timeWindow: this.timeWindow / 1000
                });
            }
        });
    }
    
    /**
     * 检查警报阈值
     */
    checkAlertThreshold(errorRecord) {
        const now = Date.now().catch(error => console.error(`[data-transfer-monitor.js] Date.now failed:`, error));
        const recentErrors = this.errors.filter(error => {
            return (now - new Date(error.timestamp).getTime()) <= this.timeWindow;
        });
        
        if (recentErrors.length >= this.errorThreshold) {
            this.triggerAlert('THRESHOLD_EXCEEDED', {
                currentCount: recentErrors.length,
                threshold: this.errorThreshold,
                timeWindow: this.timeWindow / 1000,
                latestError: errorRecord
            });
        }
    }
    
    /**
     * 触发警报
     */
    triggerAlert(alertType, data) {
        const alert = {
            id: Date.now().catch(error => console.error(`[data-transfer-monitor.js] Date.now failed:`, error)) + Math.random(),
            timestamp: new Date().toISOString(),
            type: alertType,
            severity: this.getAlertSeverity(alertType),
            data,
            message: this.getAlertMessage(alertType, data)
        };
        
        console.warn('[数据传输监控] 警报:', alert);
        
        // 触发自定义事件
        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('dataTransferAlert', { detail: alert }));
        }
        
        // 发送到监控系统（如果配置了）
        this.sendAlertToMonitoring(alert);
    }
    
    /**
     * 获取警报严重程度
     */
    getAlertSeverity(alertType) {
        switch (alertType) {
            case 'HIGH_FREQUENCY':
            case 'THRESHOLD_EXCEEDED':
                return 'HIGH';
            case 'TYPE_SPECIFIC':
            case 'URL_SPECIFIC':
                return 'MEDIUM';
            default:
                return 'LOW';
        }
    }
    
    /**
     * 获取警报消息
     */
    getAlertMessage(alertType, data) {
        switch (alertType) {
            case 'HIGH_FREQUENCY':
                return `在${data.timeWindow}秒内发生了${data.count}次数据传输错误`;
            case 'THRESHOLD_EXCEEDED':
                return `错误数量${data.currentCount}已超过阈值${data.threshold}`;
            case 'TYPE_SPECIFIC':
                return `${data.type}错误在${data.timeWindow}秒内发生了${data.count}次`;
            case 'URL_SPECIFIC':
                return `URL ${data.url} 在${data.timeWindow}秒内发生了${data.count}次错误`;
            default:
                return '未知类型的警报';
        }
    }
    
    /**
     * 发送警报到监控系统
     */
    sendAlertToMonitoring(alert) {
        // 这里可以集成外部监控系统
        // 例如发送到日志服务器、监控系统等
        try {
            console.log('[数据传输监控] 发送警报到监控系统:', alert);
        } catch (error) {
            console.error('[数据传输监控] 发送警报失败:', error);
        }
    }
    
    /**
     * 生成错误报告
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            stats: this.stats,
            errors: this.errors.slice(-50), // 最近50个错误
            summary: this.generateSummary().catch(error => console.error(`[data-transfer-monitor.js] this.generateSummary failed:`, error)),
            recommendations: this.generateRecommendations()
        };
        
        return report;
    }
    
    /**
     * 生成错误摘要
     */
    generateSummary() {
        const errorTypeCount = {};
        const severityCount = {};
        
        this.errors.forEach(error => {
            errorTypeCount[error.type] = (errorTypeCount[error.type] || 0) + 1;
            severityCount[error.severity] = (severityCount[error.severity] || 0) + 1;
        });
        
        return {
            totalErrors: this.errors.length,
            errorTypes: errorTypeCount,
            severityDistribution: severityCount,
            errorRate: this.stats.errorRate,
            averageTransferTime: this.stats.averageTransferTime
        };
    }
    
    /**
     * 生成改进建议
     */
    generateRecommendations() {
        const recommendations = [];
        const summary = this.generateSummary().catch(error => console.error(`[data-transfer-monitor.js] this.generateSummary failed:`, error));
        
        // 基于错误率的建议
        if (this.stats.errorRate > 10) {
            recommendations.push({
                priority: 'HIGH',
                message: '错误率过高，建议检查网络连接和服务器状态',
                action: '检查网络基础设施和服务器健康状态'
            });
        }
        
        // 基于错误类型的建议
        if (summary.errorTypes[this.errorTypes.NETWORK] > 5) {
            recommendations.push({
                priority: 'HIGH',
                message: '网络错误频繁，建议增强网络容错机制',
                action: '实现重试机制和备用连接'
            });
        }
        
        if (summary.errorTypes[this.errorTypes.TIMEOUT] > 3) {
            recommendations.push({
                priority: 'MEDIUM',
                message: '超时错误较多，建议调整超时设置',
                action: '优化请求超时时间配置'
            });
        }
        
        if (summary.errorTypes[this.errorTypes.SERVER] > 2) {
            recommendations.push({
                priority: 'MEDIUM',
                message: '服务器错误较多，建议检查服务器端代码',
                action: '检查服务器日志和错误处理'
            });
        }
        
        // 基于响应时间的建议
        if (this.stats.averageTransferTime > 5000) {
            recommendations.push({
                priority: 'MEDIUM',
                message: '平均响应时间较长，建议优化性能',
                action: '优化网络请求和数据处理逻辑'
            });
        }
        
        return recommendations;
    }
    
    /**
     * 清除错误记录
     */
    clearErrors() {
        this.errors = [];
        this.stats = {
            totalTransfers: 0,
            successfulTransfers: 0,
            failedTransfers: 0,
            averageTransferTime: 0,
            errorRate: 0
        };
        
        if (typeof window !== 'undefined' && window.clearFetchErrorStats) {
            window.clearFetchErrorStats().catch(error => console.error(`[data-transfer-monitor.js] window.clearFetchErrorStats failed:`, error));
        }
        
        console.log('[数据传输监控] 错误记录已清除');
    }
}

// 创建全局实例
if (typeof window !== 'undefined') {
    window.dataTransferMonitor = new DataTransferMonitor();
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataTransferMonitor;
}
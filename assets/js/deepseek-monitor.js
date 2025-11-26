
// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error(`[deepseek-monitor.js] 资源未找到 (404)`);
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error(`[deepseek-monitor.js] 访问被拒绝 (403)`);
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error(`[deepseek-monitor.js] HTTP错误: ${response.status}`);
        };

        throw new Error('HTTP错误: ' + response.status);
    };

    return response;
};
/**
 * DeepSeek AI 页面性能监控模块
 * 优化版本 - 包含缓存、错误处理和性能监控
 */

// 防止重复定义类
if (typeof DeepSeekMonitor === 'undefined') {
class DeepSeekMonitor {
    constructor() {
        this.monitoringInterval = null;
        this.monitoringData = {};
        this.apiBase = window.API_BASE || '';
        this.performanceMetrics = {
            requestCount: 0,
            errorCount: 0,
            averageResponseTime: 0,
            responseTimes: []
        };
        this.cache = new Map();
        this.isMonitoring = false;
        this.isVisible = !document.hidden;
        
        try {
            this.init();
        } catch (error) {
            console.error(`[deepseek-monitor.js] this.init failed:`, error);
        }
    }

    /**
     * 初始化监控模块
     */
    init() {
        try {
            this.setupEventListeners();
        } catch (error) {
            console.error(`[deepseek-monitor.js] this.setupEventListeners failed:`, error);
        }
        this.setupVisibilityHandlers();
        try {
            this.setupKeyboardShortcuts();
        } catch (error) {
            console.error(`[deepseek-monitor.js] this.setupKeyboardShortcuts failed:`, error);
        }
        this.setupTextareaAutoResize();
        
        console.log('DeepSeek监控模块初始化完成');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 页面加载完成后启动监控
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                try {
                    this.start();
                } catch (error) {
                    console.error(`[deepseek-monitor.js] this.start failed:`, error);
                }
            });
        } else {
            try {
                this.start();
            } catch (error) {
                console.error(`[deepseek-monitor.js] this.start failed:`, error);
            }
        }

        // 页面卸载时清理资源
        window.addEventListener('beforeunload', () => {
            try {
                this.cleanup();
            } catch (error) {
                console.error(`[deepseek-monitor.js] this.cleanup failed:`, error);
            }
        });
    }

    /**
     * 设置页面可见性处理
     */
    setupVisibilityHandlers() {
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            if (this.isVisible) {
                try {
                    this.startMonitoring();
                } catch (error) {
                    console.error(`[deepseek-monitor.js] this.startMonitoring failed:`, error);
                }
                this.addLog('info', '监控', '页面重新可见，恢复监控');
            } else {
                try {
                    this.stopMonitoring();
                } catch (error) {
                    console.error(`[deepseek-monitor.js] this.stopMonitoring failed:`, error);
                }
                this.addLog('info', '监控', '页面隐藏，暂停监控');
            }
        });
    }

    /**
     * 设置键盘快捷键
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                this.handleKeyboardShortcut(e);
            }
        });
    }

    /**
     * 处理键盘快捷键
     */
    handleKeyboardShortcut(e) {
        const keyHandlers = {
            '1': () => this.switchTab('chat'),
            '2': () => this.switchTab('code'),
            '3': () => this.switchTab('analyze'),
            '4': () => this.switchTab('translate'),
            '5': () => this.switchTab('summarize'),
            'Enter': () => {
                try {
                    this.executeActiveTabFunction();
                } catch (error) {
                    console.error(`[deepseek-monitor.js] this.executeActiveTabFunction failed:`, error);
                }
            }
        };

        const handler = keyHandlers[e.key];
        if (handler) {
            try {
                e.preventDefault();
            } catch (error) {
                console.error(`[deepseek-monitor.js] e.preventDefault failed:`, error);
            }
            handler();
        }
    }

    /**
     * 设置文本框自动调整大小
     */
    setupTextareaAutoResize() {
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', () => {
                this.autoResizeTextarea(textarea);
            });
        });
    }

    /**
     * 自动调整文本框大小
     */
    autoResizeTextarea(textarea) {
        const originalHeight = textarea.style.height;
        textarea.style.height = 'auto';
        const newHeight = Math.max(140, textarea.scrollHeight);
        textarea.style.height = `${newHeight}px`;
        
        // 避免频繁重排
        if (originalHeight !== `${newHeight}px`) {
            requestAnimationFrame(() => {
                textarea.style.height = `${newHeight}px`;
            });
        }
    }

    /**
     * 启动监控
     */
    start() {
        try {
            this.initEventListeners();
        } catch (error) {
            console.error(`[deepseek-monitor.js] this.initEventListeners failed:`, error);
        }
        this.startAutoStatusCheck();
        try {
            this.startMonitoring();
        } catch (error) {
            console.error(`[deepseek-monitor.js] this.startMonitoring failed:`, error);
        }
        this.checkServiceStatus();
        this.addLog('info', '系统', '页面初始化完成');
    }

    /**
     * 开始监控
     */
    startMonitoring() {
        if (this.isMonitoring || !this.isVisible) return;
        
        this.isMonitoring = true;
        this.monitoringInterval = setInterval(() => {
            try {
                this.updateMonitoring();
            } catch (error) {
                console.error(`[deepseek-monitor.js] this.updateMonitoring failed:`, error);
            }
        }, 2000);
        
        this.addLog('info', '监控', '实时监控已启动');
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        this.addLog('info', '监控', '实时监控已停止');
    }

    /**
     * 更新监控数据
     */
    async updateMonitoring() {
        try {
            await Promise.all([
                this.updateSystemInfo().catch(error => console.error(`[deepseek-monitor.js] this.updateSystemInfo failed:`, error)),
                this.updateMetrics(),
            ]);
        } catch (error) {
            console.error(`[deepseek-monitor.js] 监控更新失败:`, error);
            this.performanceMetrics.errorCount++;
        }
    }

    /**
     * 更新系统信息
     */
    async updateSystemInfo() {
        try {
            let startTime;
            try {
                startTime = performance.now();
            } catch (error) {
                console.error(`[deepseek-monitor.js] performance.now failed:`, error);
                startTime = 0;
            }
            const response = await this.fetchWithCache(`${this.apiBase}/system-info`, 5000);
            let responseTime;
            try {
                responseTime = performance.now() - startTime;
            } catch (error) {
                console.error(`[deepseek-monitor.js] performance.now failed:`, error);
                responseTime = 0;
            }
            
            this.updatePerformanceMetrics(responseTime);
            
            if (response.success) {
                this.updateSystemDisplay(response.data);
            }
        } catch (error) {
            console.error(`[deepseek-monitor.js] 获取系统信息失败:, error`);
            try {
                this.updateFallbackSystemInfo();
            } catch (error) {
                console.error(`[deepseek-monitor.js] this.updateFallbackSystemInfo failed:`, error);
            }
        }
    }

    /**
     * 带缓存的fetch请求
     */
    async fetchWithCache(url, cacheTime = 30000) {
        const cacheKey = url;
        const cached = this.cache.get(cacheKey);
        
        if (cached) {
            const cachedTime = new Date(cached.timestamp).getTime();
            const currentTime = new Date().getTime();
            if (currentTime - cachedTime < cacheTime) {
                return cached.data;
            }
        }

        const response = await fetch(url);
        const data = await response.json();
        
        this.cache.set(cacheKey, {
            data: data,
            timestamp: new Date().toISOString()
        });

        return data;
    }

    /**
     * 更新性能指标
     */
    updatePerformanceMetrics(responseTime) {
        this.performanceMetrics.responseTimes.push(responseTime);
        this.performanceMetrics.requestCount++;
        
        // 只保留最近50次的响应时间
        if (this.performanceMetrics.responseTimes.length > 50) {
            this.performanceMetrics.responseTimes.shift();
        }
        
        // 计算平均响应时间
        const times = this.performanceMetrics.responseTimes;
        this.performanceMetrics.averageResponseTime = 
            times.reduce((sum, time) => sum + time, 0) / times.length;
    }

    /**
     * 更新系统显示
     */
    updateSystemDisplay(data) {
        // 更新内存使用
        if (data.memory) {
            const memoryUsage = Math.round((data.memory.used / data.memory.total) * 100);
            this.updateElementWithAnimation('memoryUsage', `${memoryUsage}%`);
            this.updateTrend('memoryUsage', memoryUsage, 'memory');
        }

        // 更新运行时间
        if (data.uptime) {
            const uptimeText = this.formatUptime(data.uptime);
            this.updateElementWithAnimation('uptime', uptimeText);
        }

        // 更新CPU使用（模拟值）
        const cpuUsage = Math.round(Math.random() * 20 + 5);
        this.updateElementWithAnimation('cpuUsage', cpuUsage);
        this.updateTrend('cpuUsage', cpuUsage, 'cpu');
    }

    /**
     * 带动画的元素更新
     */
    updateElementWithAnimation(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.transition = 'all 0.3s ease';
            element.textContent = value;
        }
    }

    /**
     * 更新趋势指示器
     */
    updateTrend(elementId, currentValue, type) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const trendElement = element.parentElement?.querySelector('.monitoring-trend');
        if (!trendElement) return;
        
        if (!this.monitoringData[type]) {
            this.monitoringData[type] = [];
        }
        
        this.monitoringData[type].push(currentValue);
        
        // 只保留最近10个数据点
        if (this.monitoringData[type].length > 10) {
            this.monitoringData[type].shift();
        }
        
        // 计算趋势
        if (this.monitoringData[type].length >= 2) {
            const previous = this.monitoringData[type][this.monitoringData[type].length - 2];
            const current = this.monitoringData[type][this.monitoringData[type].length - 1];
            const change = ((current - previous) / previous * 100).toFixed(1);
            
            this.updateTrendDisplay(trendElement, change);
        }
    }

    /**
     * 更新趋势显示
     */
    updateTrendDisplay(trendElement, change) {
        const changeValue = Math.abs(change);
        
        if (changeValue < 5) {
            trendElement.className = 'monitoring-trend trend-stable';
            trendElement.textContent = '稳定';
        } else if (change > 0) {
            trendElement.className = 'monitoring-trend trend-up';
            trendElement.textContent = `↑${changeValue}%`;
        } else {
            trendElement.className = 'monitoring-trend trend-down';
            trendElement.textContent = `↓${changeValue}%`;
        }
    }

    /**
     * 格式化运行时间
     */
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    /**
     * 更新性能指标
     */
    async updateMetrics() {
        try {
            const response = await this.fetchWithCache(`${this.apiBase}/metrics`, 10000);
            if (response.success) {
                console.log('性能指标:', response.metrics);
            }
        } catch (error) {
            console.error(`[deepseek-monitor.js] 获取性能指标失败:, error`);
            this.performanceMetrics.errorCount++;
        }
    }

    /**
     * 备用系统信息更新
     */
    updateFallbackSystemInfo() {
        // 使用模拟数据
        const memoryUsage = Math.round(Math.random() * 30 + 40);
        const cpuUsage = Math.round(Math.random() * 20 + 5);
        
        this.updateElementWithAnimation('memoryUsage', `${memoryUsage}%`);
        this.updateElementWithAnimation('cpuUsage', cpuUsage);
    }

    /**
     * 添加日志条目
     */
    addLog(level, module, message) {
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;
        
        const logEntry = this.createLogEntry(level, module, message);
        this.insertLogEntry(logsContainer, logEntry);
        this.limitLogEntries(logsContainer);
    }

    /**
     * 创建日志条目
     */
    createLogEntry(level, module, message) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        
        const timestamp = new Date().toLocaleTimeString('zh-CN');
        
        logEntry.innerHTML = `
            <div class="log-timestamp">${timestamp} [${module}]</div>
            <div class="log-message">${message}</div>
        `;
        
        return logEntry;
    }

    /**
     * 插入日志条目
     */
    insertLogEntry(logsContainer, logEntry) {
        logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    }

    /**
     * 限制日志条目数量
     */
    limitLogEntries(logsContainer, maxEntries = 20) {
        const logEntries = logsContainer.querySelectorAll('.log-entry');
        if (logEntries.length > maxEntries) {
            const excessEntries = Array.from(logEntries).slice(maxEntries);
            excessEntries.forEach(entry => {
                try {
                    entry.remove();
                } catch (error) {
                    console.error(`[deepseek-monitor.js] entry.remove failed:`, error);
                }
            });
        }
    }

    /**
     * 获取系统日志
     */
    async fetchLogs() {
        try {
            const response = await this.fetchWithCache(`${this.apiBase}/logs?limit=10`, 5000);
            
            if (response.success) {
                this.displayLogs(response.logs);
            }
        } catch (error) {
            console.error(`[deepseek-monitor.js] 获取日志失败:, error`);
            this.performanceMetrics.errorCount++;
        }
    }

    /**
     * 显示日志
     */
    displayLogs(logs) {
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;
        
        logsContainer.innerHTML = '';
        
        logs.forEach(log => {
            const logEntry = this.createLogEntry(log.level, log.module, log.message);
            logsContainer.appendChild(logEntry);
        });
    }

    /**
     * 开始自动状态检查
     */
    startAutoStatusCheck() {
        setInterval(() => {
            if (this.isVisible) {
                try {
                    this.checkServiceStatus();
                } catch (error) {
                    console.error(`[deepseek-monitor.js] this.checkServiceStatus failed:`, error);
                }
            }
        }, 30000);
    }

    /**
     * 检查服务状态
     */
    async checkServiceStatus() {
        try {
            const response = await this.fetchWithCache(`${this.apiBase}/status`, 10000);
            if (response.success) {
                console.log('服务状态正常');
            }
        } catch (error) {
            console.error(`[deepseek-monitor.js] 检查服务状态失败:, error`);
        }
    }

    /**
     * 切换标签页
     */
    switchTab(tabName) {
        // 移除所有活动状态
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // 添加新的活动状态
        const activeTab = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
        const activeContent = document.getElementById(`${tabName}-content`);
        
        if (activeTab) activeTab.classList.add('active');
        if (activeContent) activeContent.classList.add('active');
    }

    /**
     * 执行活动标签页功能
     */
    executeActiveTabFunction() {
        const activeTab = document.querySelector('.tab.active');
        if (!activeTab) return;
        
        const tabName = activeTab.getAttribute('onclick')?.match(/switchTab\('(.+?)'\)/)?.[1];
        if (!tabName) return;
        
        const functionMap = {
            'chat': () => window.chat?.(),
            'code': () => window.generateCode?.(),
            'analyze': () => window.analyzeText?.(),
            'translate': () => window.translateText?.(),
            'summarize': () => window.summarizeText?.()
        };
        
        const func = functionMap[tabName];
        if (func) func();
    }

    /**
     * 初始化事件监听器（兼容原有代码）
     */
    initEventListeners() {
        // 这里可以添加其他事件监听器
    }

    /**
     * 清理资源
     */
    cleanup() {
        try {
            this.stopMonitoring();
        } catch (error) {
            console.error(`[deepseek-monitor.js] this.stopMonitoring failed:`, error);
        }
        this.cache.clear();
        console.log('DeepSeek监控模块资源已清理');
    }

    /**
     * 获取性能指标
     */
    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            cacheSize: this.cache.size,
            isMonitoring: this.isMonitoring,
            isVisible: this.isVisible
        };
    }
}

// 创建全局监控实例
window.deepSeekMonitor = new DeepSeekMonitor();

// 导出类以供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DeepSeekMonitor;
}

} // 结束 typeof DeepSeekMonitor === 'undefined' 检查
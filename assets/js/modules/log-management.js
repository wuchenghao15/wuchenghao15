/**
 * MTSCOS 日志管理模块
 * 提供日志文件加载、过滤、搜索和实时更新功能
 */

class LogManager {
    constructor(options = {}) {
        this.apiUrl = options.apiUrl || 'http://localhost:8082';
        this.logCache = [];
        this.listeners = new Map();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentFilters = {};
        this.websocket = null;
    }
    
    /**
     * 加载日志文件
     * @param {Object} filters - 过滤条件
     * @returns {Promise<Array>} 日志数据数组
     */
    async loadLogs(filters = {}) {
        try {
            // 构建查询参数
            const queryParams = new URLSearchParams();
            
            // 添加通用过滤条件
            if (filters.startTime) queryParams.append('start_time', filters.startTime);
            if (filters.endTime) queryParams.append('end_time', filters.endTime);
            if (filters.actionType) queryParams.append('action_type', filters.actionType);
            if (filters.sessionId) queryParams.append('session_id', filters.sessionId);
            if (filters.userId) queryParams.append('user_id', filters.userId);
            if (filters.searchText) queryParams.append('search', filters.searchText);
            if (filters.limit) queryParams.append('limit', filters.limit);
            if (filters.offset) queryParams.append('offset', filters.offset);
            
            // 保存当前过滤条件
            this.currentFilters = { ...filters };
            
            // 尝试从API获取数据
            try {
                const response = await fetch(`${this.apiUrl}/logs?${queryParams.toString()}`);
                if (response.ok) {
                    const data = await response.json();
                    this.logCache = data.logs || [];
                    this.notifyListeners('logsLoaded', this.logCache);
                    return this.logCache;
                }
                throw new Error('API响应失败');
            } catch (apiError) {
                console.warn('无法连接到日志API，使用本地日志文件');
                // 如果API不可用，尝试从本地日志文件加载
                return this.loadLocalLogs(filters);
            }
        } catch (error) {
            console.error('加载日志失败:', error);
            this.notifyListeners('error', error);
            // 生成模拟数据作为备份
            return this.generateMockLogs(filters);
        }
    }
    
    /**
     * 从本地文件系统加载日志
     * @param {Object} filters - 过滤条件
     * @returns {Promise<Array>} 本地日志数据
     */
    async loadLocalLogs(filters = {}) {
        // 这里会通过HTTP服务器访问本地日志文件
        try {
            // 由于浏览器安全限制，我们不能直接访问本地文件系统
            // 但是可以通过HTTP服务访问服务器上的日志文件
            const response = await fetch('/logs/action_logs.json');
            if (response.ok) {
                const data = await response.json();
                const filteredLogs = this.applyFilters(data, filters);
                this.logCache = filteredLogs;
                this.notifyListeners('logsLoaded', filteredLogs);
                return filteredLogs;
            }
            throw new Error('无法加载本地日志文件');
        } catch (error) {
            console.error('加载本地日志失败:', error);
            return [];
        }
    }
    
    /**
     * 应用过滤条件
     * @param {Array} logs - 日志数组
     * @param {Object} filters - 过滤条件
     * @returns {Array} 过滤后的日志
     */
    applyFilters(logs, filters) {
        return logs.filter(log => {
            // 按时间过滤
            if (filters.startTime) {
                const logTime = new Date(log.timestamp).getTime();
                const startTime = new Date(filters.startTime).getTime();
                if (logTime < startTime) return false;
            }
            
            if (filters.endTime) {
                const logTime = new Date(log.timestamp).getTime();
                const endTime = new Date(filters.endTime).getTime();
                if (logTime > endTime) return false;
            }
            
            // 按动作类型过滤
            if (filters.actionType) {
                if (!log.actionType.includes(filters.actionType)) return false;
            }
            
            // 按会话ID过滤
            if (filters.sessionId) {
                if (!log.sessionId.includes(filters.sessionId)) return false;
            }
            
            // 按用户ID过滤
            if (filters.userId) {
                if (!log.userId.includes(filters.userId)) return false;
            }
            
            // 按搜索文本过滤
            if (filters.searchText) {
                const searchText = filters.searchText.toLowerCase();
                const logString = JSON.stringify(log).toLowerCase();
                if (!logString.includes(searchText)) return false;
            }
            
            return true;
        });
    }
    
    /**
     * 生成模拟日志数据
     * @param {Object} filters - 过滤条件
     * @returns {Array} 模拟日志数据
     */
    generateMockLogs(filters = {}) {
        const mockLogs = [];
        const now = new Date();
        const limit = parseInt(filters.limit || 100);
        
        // 定义各种动作类型和权重
        const actionTypes = [
            { type: 'PAGE_LOADED', weight: 20 },
            { type: 'PAGE_UNLOADED', weight: 10 },
            { type: 'USER_CLICK', weight: 30 },
            { type: 'FORM_SUBMIT', weight: 15 },
            { type: 'JAVASCRIPT_ERROR', weight: 5 },
            { type: 'RESOURCE_ERROR', weight: 5 },
            { type: 'STATE_CHANGE', weight: 10 },
            { type: 'CUSTOM_ACTION', weight: 5 }
        ];
        
        // 生成加权随机动作类型
        function getRandomActionType() {
            const totalWeight = actionTypes.reduce((sum, type) => sum + type.weight, 0);
            let random = Math.random() * totalWeight;
            
            for (const type of actionTypes) {
                random -= type.weight;
                if (random <= 0) return type.type;
            }
            return actionTypes[0].type;
        }
        
        // 生成模拟日志
        for (let i = 0; i < limit; i++) {
            // 生成随机时间戳（过去24小时内）
            const randomTime = now.getTime() - Math.floor(Math.random() * 24 * 60 * 60 * 1000);
            const timestamp = new Date(randomTime).toISOString();
            
            // 获取随机动作类型
            const actionType = getRandomActionType();
            
            // 根据动作类型生成详细数据
            let data = {};
            
            switch (actionType) {
                case 'PAGE_LOADED':
                    data = {
                        url: ['/HTML/index.html', '/HTML/dashboard.html', '/HTML/settings.html', '/HTML/log-viewer.html'][Math.floor(Math.random() * 4)],
                        title: ['MTSCOS 首页', 'MTSCOS 仪表盘', 'MTSCOS 设置', 'MTSCOS 日志查看器'][Math.floor(Math.random() * 4)],
                        loadTime: Math.floor(Math.random() * 3000) + 500, // 500-3500ms
                        referrer: ['', '/HTML/index.html', 'https://google.com', 'https://baidu.com'][Math.floor(Math.random() * 4)]
                    };
                    break;
                
                case 'PAGE_UNLOADED':
                    data = {
                        url: ['/HTML/index.html', '/HTML/dashboard.html', '/HTML/settings.html', '/HTML/log-viewer.html'][Math.floor(Math.random() * 4)],
                        title: ['MTSCOS 首页', 'MTSCOS 仪表盘', 'MTSCOS 设置', 'MTSCOS 日志查看器'][Math.floor(Math.random() * 4)],
                        timeSpent: Math.floor(Math.random() * 300) + 10, // 10-310秒
                        scrollPosition: Math.floor(Math.random() * 100)
                    };
                    break;
                
                case 'USER_CLICK':
                    const elements = [
                        { tagName: 'BUTTON', id: 'login-btn', text: '登录' },
                        { tagName: 'BUTTON', id: 'submit-btn', text: '提交' },
                        { tagName: 'A', id: 'nav-dashboard', text: '仪表盘' },
                        { tagName: 'A', id: 'nav-settings', text: '设置' },
                        { tagName: 'INPUT', id: 'search-input', text: '' },
                        { tagName: 'SELECT', id: 'filter-select', text: '' }
                    ];
                    const element = elements[Math.floor(Math.random() * elements.length)];
                    
                    data = {
                        element: element,
                        x: Math.floor(Math.random() * 1200),
                        y: Math.floor(Math.random() * 800),
                        modifierKeys: ['', 'ctrl', 'shift', 'alt'][Math.floor(Math.random() * 4)]
                    };
                    break;
                
                case 'FORM_SUBMIT':
                    const forms = [
                        { formId: 'login-form', formAction: '/api/login', formMethod: 'post' },
                        { formId: 'search-form', formAction: '/api/search', formMethod: 'get' },
                        { formId: 'settings-form', formAction: '/api/settings', formMethod: 'put' }
                    ];
                    
                    data = forms[Math.floor(Math.random() * forms.length)];
                    break;
                
                case 'JAVASCRIPT_ERROR':
                    const errors = [
                        { message: '未定义的变量: xyz', filename: 'main.js', lineno: Math.floor(Math.random() * 100) },
                        { message: '无法读取null的属性', filename: 'utils.js', lineno: Math.floor(Math.random() * 100) },
                        { message: '超出最大调用栈大小', filename: 'components.js', lineno: Math.floor(Math.random() * 100) }
                    ];
                    const error = errors[Math.floor(Math.random() * errors.length)];
                    
                    data = {
                        ...error,
                        error: `${error.message}\n    at ${error.filename}:${error.lineno}:15`,
                        stack: `Error: ${error.message}\n    at Object.function (${error.filename}:${error.lineno}:15)\n    at main.js:10:20`
                    };
                    break;
                
                case 'RESOURCE_ERROR':
                    const resources = [
                        '/assets/css/missing.css',
                        '/assets/js/non-existent.js',
                        '/assets/images/broken.png'
                    ];
                    
                    data = {
                        target: resources[Math.floor(Math.random() * resources.length)],
                        tagName: ['LINK', 'SCRIPT', 'IMG'][Math.floor(Math.random() * 3)],
                        errorCode: Math.floor(Math.random() * 3) + 400 // 400-403
                    };
                    break;
                
                case 'STATE_CHANGE':
                    const stateChanges = [
                        { stateType: 'user_status', oldState: 'anonymous', newState: 'authenticated' },
                        { stateType: 'theme', oldState: 'light', newState: 'dark' },
                        { stateType: 'connection', oldState: 'online', newState: 'offline' },
                        { stateType: 'connection', oldState: 'offline', newState: 'online' }
                    ];
                    
                    data = stateChanges[Math.floor(Math.random() * stateChanges.length)];
                    break;
                
                case 'CUSTOM_ACTION':
                    const customActions = [
                        { action: 'LOGIN', username: 'user_' + Math.floor(Math.random() * 1000), success: true },
                        { action: 'LOGOUT', username: 'user_' + Math.floor(Math.random() * 1000), success: true },
                        { action: 'DATA_EXPORT', format: ['json', 'csv', 'pdf'][Math.floor(Math.random() * 3)] },
                        { action: 'SETTINGS_CHANGE', setting: 'language', value: ['zh-CN', 'en-US', 'ja-JP'][Math.floor(Math.random() * 3)] }
                    ];
                    
                    data = customActions[Math.floor(Math.random() * customActions.length)];
                    break;
            }
            
            // 生成日志条目
            const logEntry = {
                timestamp: timestamp,
                actionType: actionType,
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36',
                sessionId: 'session_' + Math.floor(Math.random() * 100),
                userId: Math.random() > 0.2 ? 'user_' + Math.floor(Math.random() * 50) : 'anonymous',
                ipAddress: `192.168.1.${Math.floor(Math.random() * 255)}`,
                data: data
            };
            
            mockLogs.push(logEntry);
        }
        
        // 按时间戳降序排序
        mockLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // 应用过滤条件
        const filteredLogs = this.applyFilters(mockLogs, filters);
        
        this.logCache = filteredLogs;
        this.notifyListeners('logsLoaded', filteredLogs);
        
        return filteredLogs;
    }
    
    /**
     * 保存日志条目到服务器
     * @param {Object} logEntry - 日志条目
     * @returns {Promise<boolean>} 是否成功
     */
    async saveLog(logEntry) {
        try {
            const response = await fetch(`${this.apiUrl}/logs`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(logEntry)
            });
            
            if (response.ok) {
                // 将新日志添加到缓存
                this.logCache.unshift(logEntry);
                this.notifyListeners('logAdded', logEntry);
                return true;
            }
            
            // 如果API失败，保存到本地存储
            this.saveToLocalStorage(logEntry);
            return true;
        } catch (error) {
            console.error('保存日志失败:', error);
            // 保存到本地存储作为备份
            this.saveToLocalStorage(logEntry);
            return true; // 即使API失败，我们仍然认为保存成功（本地备份）
        }
    }
    
    /**
     * 批量保存日志条目
     * @param {Array} logEntries - 日志条目数组
     * @returns {Promise<boolean>} 是否成功
     */
    async saveLogs(logEntries) {
        try {
            const response = await fetch(`${this.apiUrl}/logs/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ logs: logEntries })
            });
            
            if (response.ok) {
                // 将新日志添加到缓存
                this.logCache = [...logEntries, ...this.logCache];
                this.notifyListeners('logsAdded', logEntries);
                return true;
            }
            
            // 保存失败，尝试单个保存
            for (const log of logEntries) {
                this.saveToLocalStorage(log);
            }
            return true;
        } catch (error) {
            console.error('批量保存日志失败:', error);
            // 保存到本地存储
            for (const log of logEntries) {
                this.saveToLocalStorage(log);
            }
            return true;
        }
    }
    
    /**
     * 保存日志到本地存储
     * @param {Object} logEntry - 日志条目
     */
    saveToLocalStorage(logEntry) {
        try {
            // 获取现有日志
            const storedLogs = localStorage.getItem('mtscos_local_logs');
            let logs = storedLogs ? JSON.parse(storedLogs) : [];
            
            // 添加新日志
            logs.unshift(logEntry);
            
            // 限制存储数量（最多1000条）
            if (logs.length > 1000) {
                logs = logs.slice(0, 1000);
            }
            
            // 保存回本地存储
            localStorage.setItem('mtscos_local_logs', JSON.stringify(logs));
        } catch (error) {
            console.error('保存到本地存储失败:', error);
        }
    }
    
    /**
     * 获取本地存储的日志
     * @returns {Array} 本地日志
     */
    getLocalStorageLogs() {
        try {
            const storedLogs = localStorage.getItem('mtscos_local_logs');
            return storedLogs ? JSON.parse(storedLogs) : [];
        } catch (error) {
            console.error('获取本地日志失败:', error);
            return [];
        }
    }
    
    /**
     * 清除本地存储的日志
     */
    clearLocalStorageLogs() {
        try {
            localStorage.removeItem('mtscos_local_logs');
        } catch (error) {
            console.error('清除本地日志失败:', error);
        }
    }
    
    /**
     * 连接到WebSocket进行实时更新
     * @param {string} wsUrl - WebSocket URL
     */
    connectWebSocket(wsUrl = 'ws://localhost:8082/ws') {
        if (this.websocket && (this.websocket.readyState === WebSocket.OPEN || this.websocket.readyState === WebSocket.CONNECTING)) {
            return;
        }
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket连接已建立');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.notifyListeners('connected');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const logData = JSON.parse(event.data);
                    
                    if (logData.type === 'new_log') {
                        // 添加新日志到缓存
                        this.logCache.unshift(logData.log);
                        
                        // 检查是否符合当前过滤条件
                        const filtered = this.applyFilters([logData.log], this.currentFilters);
                        if (filtered.length > 0) {
                            this.notifyListeners('newLog', logData.log);
                        }
                    } else if (logData.type === 'batch_logs') {
                        // 批量日志更新
                        this.logCache = [...logData.logs, ...this.logCache];
                        this.notifyListeners('logsAdded', logData.logs);
                    } else if (logData.type === 'status') {
                        // 状态更新
                        this.notifyListeners('status', logData.status);
                    }
                } catch (error) {
                    console.error('处理WebSocket消息失败:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket连接已关闭');
                this.isConnected = false;
                this.notifyListeners('disconnected');
                
                // 尝试重新连接
                this.attemptReconnect(wsUrl);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                this.notifyListeners('error', error);
            };
        } catch (error) {
            console.error('创建WebSocket连接失败:', error);
            this.attemptReconnect(wsUrl);
        }
    }
    
    /**
     * 尝试重新连接WebSocket
     * @param {string} wsUrl - WebSocket URL
     */
    attemptReconnect(wsUrl) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('达到最大重连次数，停止重连');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指数退避
        
        console.log(`将在 ${delay}ms 后进行第 ${this.reconnectAttempts} 次重连`);
        
        setTimeout(() => {
            this.connectWebSocket(wsUrl);
        }, delay);
    }
    
    /**
     * 断开WebSocket连接
     */
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.reconnectAttempts = 0;
    }
    
    /**
     * 注册事件监听器
     * @param {string} eventType - 事件类型
     * @param {Function} callback - 回调函数
     */
    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, []);
        }
        this.listeners.get(eventType).push(callback);
    }
    
    /**
     * 移除事件监听器
     * @param {string} eventType - 事件类型
     * @param {Function} callback - 回调函数
     */
    off(eventType, callback) {
        if (this.listeners.has(eventType)) {
            const callbacks = this.listeners.get(eventType);
            const index = callbacks.indexOf(callback);
            if (index !== -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    /**
     * 通知所有监听器
     * @param {string} eventType - 事件类型
     * @param {*} data - 事件数据
     */
    notifyListeners(eventType, data) {
        if (this.listeners.has(eventType)) {
            const callbacks = this.listeners.get(eventType);
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`执行 ${eventType} 监听器时出错:`, error);
                }
            });
        }
    }
    
    /**
     * 获取日志统计信息
     * @returns {Object} 统计信息
     */
    getStatistics() {
        const stats = {
            total: this.logCache.length,
            byType: {},
            byUser: {},
            errors: 0,
            warnings: 0,
            success: 0
        };
        
        this.logCache.forEach(log => {
            // 按类型统计
            if (!stats.byType[log.actionType]) {
                stats.byType[log.actionType] = 0;
            }
            stats.byType[log.actionType]++;
            
            // 按用户统计
            if (!stats.byUser[log.userId]) {
                stats.byUser[log.userId] = 0;
            }
            stats.byUser[log.userId]++;
            
            // 按状态统计
            if (log.actionType.includes('ERROR')) {
                stats.errors++;
            } else if (log.actionType.includes('WARNING')) {
                stats.warnings++;
            } else {
                stats.success++;
            }
        });
        
        return stats;
    }
    
    /**
     * 导出日志数据
     * @param {string} format - 导出格式 ('json', 'csv', 'txt')
     * @returns {Blob} 导出数据的Blob对象
     */
    exportLogs(format = 'json') {
        let content = '';
        let mimeType = 'application/json';
        
        switch (format.toLowerCase()) {
            case 'json':
                content = JSON.stringify(this.logCache, null, 2);
                mimeType = 'application/json';
                break;
            
            case 'csv':
                content = this.convertToCSV(this.logCache);
                mimeType = 'text/csv';
                break;
            
            case 'txt':
                content = this.logCache.map(log => JSON.stringify(log)).join('\n');
                mimeType = 'text/plain';
                break;
            
            default:
                throw new Error(`不支持的导出格式: ${format}`);
        }
        
        return new Blob([content], { type: mimeType });
    }
    
    /**
     * 将日志数据转换为CSV格式
     * @param {Array} logs - 日志数据
     * @returns {string} CSV格式的字符串
     */
    convertToCSV(logs) {
        // CSV头部
        const headers = ['timestamp', 'actionType', 'sessionId', 'userId', 'data'];
        let csv = headers.join(',') + '\n';
        
        // 添加数据行
        logs.forEach(log => {
            const row = [
                `"${log.timestamp || ''}"`,
                `"${log.actionType || ''}"`,
                `"${log.sessionId || ''}"`,
                `"${log.userId || ''}"`,
                `"${JSON.stringify(log.data || {}).replace(/"/g, '""')}"`
            ];
            csv += row.join(',') + '\n';
        });
        
        return csv;
    }
    
    /**
     * 清除日志缓存
     */
    clearCache() {
        this.logCache = [];
        this.notifyListeners('cacheCleared');
    }
}

// 导出单例实例
const logManager = new LogManager();

export { LogManager, logManager };

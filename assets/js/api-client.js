
// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error(`[api-client.js] 资源未找到 (404)`);
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error(`[api-client.js] 访问被拒绝 (403)`);
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error(`[api-client.js] HTTP错误: ${response.status}`);
        };

        throw new Error('HTTP错误: ' + response.status);
    };

    return response;
};


// 保存原始fetch引用，避免循环调用
if (!window.MTSCOSOriginalFetch) {
    window.MTSCOSOriginalFetch = window.fetch;
}

// 增强版全局fetch错误处理器
if (!window.GlobalOriginalFetch) {
    window.GlobalOriginalFetch = window.fetch;
}

// 全局错误统计
window.fetchErrorStats = {
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    errors: [],
    lastError: null,
    averageResponseTime: 0
};

window.fetch = async function(url, options = {}) {
    const requestId = Math.random();
    const startTime = Date.now();
    
    // 更新统计
    window.fetchErrorStats.totalRequests++;
    
    try {
        // 记录请求开始
        console.log(`[Global Fetch] 请求开始: ${url} (ID: ${requestId})`);
        
        // 设置默认超时
        const fetchOptions = {
            ...options,
            signal: options.signal || AbortSignal.timeout(30000) // 30秒默认超时
        };
        
        // 发送请求
        const response = await window.GlobalOriginalFetch.call(this, url, fetchOptions);
        
        // 计算响应时间
        const responseTime = Date.now() - startTime;
        
        // 更新成功统计
        window.fetchErrorStats.successfulRequests++;
        
        // 更新平均响应时间
        const totalTime = window.fetchErrorStats.averageResponseTime * (window.fetchErrorStats.successfulRequests - 1) + responseTime;
        window.fetchErrorStats.averageResponseTime = totalTime / window.fetchErrorStats.successfulRequests;
        
        console.log(`[Global Fetch] 请求成功: ${url} (${responseTime}ms)`);
        
        // 检查响应状态
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.status = response.status;
            error.url = url;
            error.responseTime = responseTime;
            throw error;
        }
        
        return response;
        
    } catch (error) {
        // 计算响应时间
        const responseTime = Date.now() - startTime;
        
        // 更新失败统计
        window.fetchErrorStats.failedRequests++;
        
        // 记录错误详情
        const errorDetails = {
            requestId,
            url,
            error: error.message,
            status: error.status || null,
            responseTime,
            timestamp: new Date().toISOString(),
            options: {
                method: options.method || 'GET',
                headers: options.headers || {}
            }
        };
        
        window.fetchErrorStats.errors.push(errorDetails);
        window.fetchErrorStats.lastError = errorDetails;
        
        // 保留最近100个错误记录
        if (window.fetchErrorStats.errors.length > 100) {
            window.fetchErrorStats.errors.shift();
        }
        
        console.error(`[Global Fetch] 请求失败: ${url} - ${error.message} (${responseTime}ms)`);
        
        // 根据错误类型提供用户友好的错误信息
        if (error.name === 'AbortError') {
            error.userMessage = '请求超时，请检查网络连接后重试';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            error.userMessage = '网络连接失败，请检查网络设置';
        } else if (error.message.includes('CORS')) {
            error.userMessage = '跨域请求被阻止，请联系管理员';
        } else if (error.status >= 500) {
            error.userMessage = '服务器内部错误，请稍后重试';
        } else if (error.status === 404) {
            error.userMessage = '请求的资源不存在';
        } else if (error.status === 403) {
            error.userMessage = '没有权限访问此资源';
        } else if (error.status === 401) {
            error.userMessage = '需要登录或授权已过期';
        } else {
            error.userMessage = error.message;
        }
        
        // 集成数据传输监控
        if (typeof window !== 'undefined' && window.dataTransferMonitor) {
            window.dataTransferMonitor.recordError(error, {
                url: url,
                method: options.method || 'GET',
                responseTime: responseTime
            });
        }
        
        throw error;
    }
};

/**
 * 获取全局fetch错误统计
 */
window.getFetchErrorStats = function() {
    return {
        ...window.fetchErrorStats,
        successRate: window.fetchErrorStats.totalRequests > 0 
            ? (window.fetchErrorStats.successfulRequests / window.fetchErrorStats.totalRequests * 100).toFixed(2) + '%'
            : '0%'
    };
};

/**
 * 清除全局fetch错误统计
 */
window.clearFetchErrorStats = function() {
    window.fetchErrorStats = {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        errors: [],
        lastError: null,
        averageResponseTime: 0
    };
};
/**
 * MTSCOS API客户端 - 增强版
 * 提供完整的前后端握手机制和API通信
 * 作者: Chenghao Wu
 * 版本: 2.0.0
 */

class MTSCOSApiClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || 'http://localhost:3001';
        this.sessionId = null;
        this.apiKey = null;
        this.authenticated = false;
        this.heartbeatInterval = null;
        this.heartbeatEnabled = true;
        this.heartbeatDelay = 30000; // 30秒心跳间隔
        this.lastHeartbeat = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.eventListeners = new Map();
        this.connectionStatus = 'disconnected';
        this.requestQueue = [];
        this.isProcessingQueue = false;
        
        // 心跳统计
        this.heartbeatStats = {
            successCount: 0,
            failureCount: 0,
            consecutiveFailures: 0,
            lastSuccess: null,
            lastFailure: null,
            responseTime: 0,
            averageResponseTime: 0
        };
        
        // 绑定方法上下文
        this.handleOnline = this.handleOnline.bind(this);
        this.handleOffline = this.handleOffline.bind(this);
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        
        // 初始化事件监听
        this.initEventListeners();
        
        // 尝试从存储中恢复会话
        this.restoreSession();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 网络状态监听
        window.addEventListener('online', this.handleOnline);
        window.addEventListener('offline', this.handleOffline);
        
        // 页面可见性监听
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        // 页面关闭前清理
        window.addEventListener('beforeunload', () => {
            this.disconnect().catch(error => console.error(`[api-client.js] this.disconnect failed:`, error));
        });
    }

    /**
     * 网络连接恢复处理
     */
    handleOnline() {
        console.log('[API客户端] 网络连接已恢复');
        if (this.connectionStatus === 'disconnected') {
            this.reconnect().catch(error => console.error(`[api-client.js] this.reconnect failed:`, error));
        }
    }

    /**
     * 网络连接断开处理
     */
    handleOffline() {
        console.log('[API客户端] 网络连接已断开');
        this.connectionStatus = 'offline';
        this.stopHeartbeat().catch(error => console.error(`[api-client.js] this.stopHeartbeat failed:`, error));
        this.emit('offline');
    }

    /**
     * 页面可见性变化处理
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // 页面隐藏时降低心跳频率
            this.stopHeartbeat().catch(error => console.error(`[api-client.js] this.stopHeartbeat failed:`, error));
        } else {
            // 页面显示时恢复心跳
            if (this.connectionStatus === 'connected') {
                this.startHeartbeat(30000); // 30秒心跳
            }
        }
    }

    /**
     * 事件监听器管理
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('[API客户端] 事件回调错误:', error);
                }
            });
        }
    }

    /**
     * 保存会话到本地存储
     */
    saveSession() {
        if (this.sessionId && this.apiKey) {
            const sessionData = {
                sessionId: this.sessionId,
                apiKey: this.apiKey,
                authenticated: this.authenticated,
                timestamp: Date.now()
            };
            localStorage.setItem('mtscos_api_session', JSON.stringify(sessionData));
        }
    }

    /**
     * 从本地存储恢复会话
     */
    restoreSession() {
        try {
            const sessionData = localStorage.getItem('mtscos_api_session');
            if (sessionData) {
                const session = JSON.parse(sessionData);
                // 检查会话是否过期（24小时）
                if (Date.now() - session.timestamp < 24 * 60 * 60 * 1000) {
                    this.sessionId = session.sessionId;
                    this.apiKey = session.apiKey;
                    this.authenticated = session.authenticated;
                    console.log('[API客户端] 会话已从本地存储恢复');
                    return true;
                }
            }
        } catch (error) {
            console.error('[API客户端] 恢复会话失败:', error);
        }
        return false;
    }

    /**
     * 清除本地会话
     */
    clearSession() {
        localStorage.removeItem('mtscos_api_session');
        this.sessionId = null;
        this.apiKey = null;
        this.authenticated = false;
    }

    /**
     * 建立连接和握手
     */
    async connect() {
        try {
            this.connectionStatus = 'connecting';
            this.emit('connecting');

            // 使用健康检查API来验证连接
            const response = await this.fetch('/api/health', {
                method: 'GET'
            });

            if (response.success || response.status === 'ok') {
                // 生成临时会话信息
                this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                this.apiKey = 'temp_api_key_' + Date.now();
                this.connectionStatus = 'connected';
                this.reconnectAttempts = 0;
                this.authenticated = true;
                
                // 保存会话
                this.saveSession();
                
                // 启动心跳
                this.startHeartbeat().catch(error => console.error(`[api-client.js] this.startHeartbeat failed:`, error));
                
                // 处理请求队列
                this.processRequestQueue().catch(error => console.error(`[api-client.js] this.processRequestQueue failed:`, error));
                
                console.log('[API客户端] 连接成功');
                this.emit('connected', { 
                    sessionId: this.sessionId,
                    apiKey: this.apiKey,
                    status: 'connected'
                });
                
                return { 
                    sessionId: this.sessionId,
                    apiKey: this.apiKey,
                    status: 'connected'
                };
            } else {
                throw new Error('服务器健康检查失败');
            }
        } catch (error) {
            this.connectionStatus = 'disconnected';
            console.error('[API客户端] 连接失败:', error);
            this.emit('error', error);
            throw error;
        }
    }

    /**
     * 重新连接（增强版）
     */
    async reconnect() {
        if (this.reconnecting) {
            return;
        }

        this.reconnecting = true;
        
        try {
            // 计算退避延迟（指数退避 + 随机抖动）
            const baseDelay = 1000; // 1秒基础延迟
            const maxDelay = 30000; // 最大30秒
            const jitter = Math.random() * 1000; // 随机抖动
            
            const delay = Math.min(
                baseDelay * Math.pow(2, this.reconnectAttempts) + jitter,
                maxDelay
            );

            this.logRequest('RECONNECT_ATTEMPT', { 
                attempt: this.reconnectAttempts + 1, 
                delay: Math.round(delay) 
            });

            // 等待退避延迟
            await this.sleep(delay);

            // 检查网络状态
            if (!navigator.onLine) {
                throw new Error('网络不可用');
            }

            // 尝试重新连接
            await this.connect();
            
            // 重连成功，处理队列中的请求
            if (this.requestQueue.length > 0) {
                this.logRequest('PROCESSING_QUEUE', { 
                    queueLength: this.requestQueue.length 
                });
                this.processRequestQueue().catch(error => console.error(`[api-client.js] this.processRequestQueue failed:`, error));
            }

        } catch (error) {
            this.reconnectAttempts++;
            
            this.logRequest('RECONNECT_FAILED', { 
                attempt: this.reconnectAttempts, 
                error: error.message 
            });

            // 检查是否达到最大重试次数
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.logRequest('RECONNECT_ABANDONED', { 
                    maxAttempts: this.maxReconnectAttempts 
                });
                
                // 清空请求队列，避免内存泄漏
                this.requestQueue.forEach(request => {
                    if (request.reject) {
                        request.reject(new Error('连接重试次数已达上限'));
                    }
                });
                this.requestQueue = [];
                
                // 触发连接失败事件
                this.emit('connectionFailed', { 
                    error: '连接重试次数已达上限',
                    attempts: this.reconnectAttempts 
                });
                
                return;
            }

            // 继续重试
            setTimeout(() => this.reconnect().catch(error => console.error(`[api-client.js] this.reconnect failed:`, error)), 1000);
            
        } finally {
            this.reconnecting = false;
        }
    }

    /**
     * 断开连接
     */
    disconnect() {
        this.connectionStatus = 'disconnected';
        this.stopHeartbeat().catch(error => console.error(`[api-client.js] this.stopHeartbeat failed:`, error));
        this.clearSession();
        this.emit('disconnected');
    }

    /**
     * 启动心跳检测
     */
    startHeartbeat(interval = 30000) {
        this.stopHeartbeat().catch(error => console.error(`[api-client.js] this.stopHeartbeat failed:`, error));
        
        this.heartbeatInterval = setInterval(async () => {
            try {
                await this.heartbeat();
            } catch (error) {
                console.error('[API客户端] 心跳失败:', error);
                this.handleConnectionError(error);
            }
        }, interval);
    }

    /**
     * 停止心跳检测
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * 发送心跳（增强版）
     */
    async heartbeat() {
        if (!this.isConnected || !this.heartbeatEnabled) {
            return;
        }

        try {
            // 记录心跳开始时间
            const heartbeatStart = Date.now();
            
            // 根据认证状态选择心跳端点
            const endpoint = this.authenticated ? '/api/heartbeat' : '/api/health';
            const method = this.authenticated ? 'POST' : 'GET';
            
            // 发送心跳请求
            const response = await this.fetch(endpoint, {
                method: method,
                timeout: 5000 // 5秒心跳超时
            });
            
            // 计算心跳响应时间
            const heartbeatTime = Date.now() - heartbeatStart;
            
            // 更新心跳统计
            this.heartbeatStats.lastSuccess = new Date();
            this.heartbeatStats.responseTime = heartbeatTime;
            this.heartbeatStats.successCount++;
            
            this.logRequest('HEARTBEAT_SUCCESS', { 
                endpoint,
                responseTime: heartbeatTime,
                consecutiveFailures: this.heartbeatStats.consecutiveFailures 
            });
            
            // 重置连续失败计数
            this.heartbeatStats.consecutiveFailures = 0;
            
            // 检查响应时间是否异常
            if (heartbeatTime > 3000) { // 超过3秒认为响应缓慢
                this.logRequest('HEARTBEAT_SLOW', { responseTime: heartbeatTime });
                this.emit('heartbeatSlow', { responseTime: heartbeatTime });
            }
            
            if (response.success) {
                this.lastHeartbeat = Date.now();
                this.emit('heartbeat');
            }
            
            return response;

        } catch (error) {
            // 更新失败统计
            this.heartbeatStats.consecutiveFailures++;
            this.heartbeatStats.lastFailure = new Date();
            this.heartbeatStats.failureCount++;
            
            this.logRequest('HEARTBEAT_FAILED', { 
                error: error.message,
                consecutiveFailures: this.heartbeatStats.consecutiveFailures 
            });
            
            // 检查连续失败次数
            if (this.heartbeatStats.consecutiveFailures >= 3) {
                this.logRequest('HEARTBEAT_CONNECTION_LOST', { 
                    consecutiveFailures: this.heartbeatStats.consecutiveFailures 
                });
                
                // 认为连接丢失，触发重连
                this.handleConnectionError(error);
            } else {
                // 发射心跳失败事件，但不立即重连
                this.emit('heartbeatFailed', { 
                    error: error.message,
                    consecutiveFailures: this.heartbeatStats.consecutiveFailures 
                });
            }
        }
    }

    /**
     * 处理连接错误
     */
    handleConnectionError(error) {
        this.connectionStatus = 'disconnected';
        this.stopHeartbeat().catch(error => console.error(`[api-client.js] this.stopHeartbeat failed:`, error));
        this.emit('connectionError', error);
        
        // 尝试重连
        if (navigator.onLine) {
            this.reconnect().catch(error => console.error(`[api-client.js] this.reconnect failed:`, error));
        }
    }

    /**
     * 通用请求方法（增强版）
     */
    async fetch(endpoint, options = {}) {
        const requestId = Date.now() + Math.random();
        const startTime = Date.now();
        const url = `${this.baseUrl}${endpoint}`;
        
        // 验证endpoint格式
        if (!endpoint || typeof endpoint !== 'string') {
            throw new Error('无效的endpoint');
        }

        const headers = {
            'Content-Type': 'application/json',
            'X-Request-ID': requestId.toString(),
            ...options.headers
        };

        // 添加认证头
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        if (this.sessionId) {
            headers['X-Session-ID'] = this.sessionId;
        }

        const fetchOptions = {
            timeout: options.timeout || 30000, // 30秒超时
            ...options,
            headers
        };

        try {
            // 记录请求开始
            this.emit('requestStart', { url, requestId, options: fetchOptions });

            // 使用AbortController实现超时控制
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), fetchOptions.timeout);
            fetchOptions.signal = controller.signal;

            // 使用保存的原始fetch引用，避免循环调用
            const response = await window.MTSCOSOriginalFetch(url, fetchOptions);
            clearTimeout(timeoutId);

            // 记录响应时间
            const responseTime = Date.now() - startTime;
            this.emit('requestComplete', { 
                url, 
                requestId, 
                status: response.status, 
                responseTime 
            });
            
            // 检查HTTP状态
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    // 忽略解析错误
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            
            // 检查API响应状态
            if (!data.success) {
                throw new Error(data.error || 'API请求失败');
            }

            return data;
        } catch (error) {
            const responseTime = Date.now() - startTime;
            
            // 记录错误
            this.emit('requestError', { 
                url, 
                requestId, 
                error: error.message, 
                responseTime 
            });

            // 处理不同类型的错误
            if (error.name === 'AbortError') {
                throw new Error('请求超时，请检查网络连接');
            } else if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
                this.handleConnectionError(error);
                throw new Error('网络连接失败，请检查网络设置');
            } else if (error.message.includes('CORS')) {
                throw new Error('跨域请求被阻止，请联系管理员');
            } else {
                throw error;
            }
        }
    }

    /**
     * 添加请求到队列
     */
    queueRequest(method, endpoint, data, resolve, reject) {
        this.requestQueue.push({
            method,
            endpoint,
            data,
            resolve,
            reject,
            timestamp: Date.now()
        });
    }

    /**
     * 处理请求队列（增强版）
     */
    async processRequestQueue() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;
        
        try {
            this.logRequest('QUEUE_PROCESSING_START', { 
                queueLength: this.requestQueue.length 
            });

            // 使用while循环处理队列，确保所有请求都被处理
            while (this.requestQueue.length > 0 && this.isConnected) {
                const requests = this.requestQueue.splice(0, 5); // 每次处理5个请求
                
                // 并行处理这批请求
                const promises = requests.map(async (request) => {
                    try {
                        let response;
                        switch (request.method.toUpperCase()) {
                            case 'GET':
                                response = await this.get(request.endpoint);
                                break;
                            case 'POST':
                                response = await this.post(request.endpoint, request.data);
                                break;
                            case 'PUT':
                                response = await this.put(request.endpoint, request.data);
                                break;
                            case 'DELETE':
                                response = await this.delete(request.endpoint);
                                break;
                            default:
                                throw new Error(`不支持的请求方法: ${request.method}`);
                        }
                        if (request.resolve) {
                            request.resolve(response);
                        }
                        return { success: true, request };
                    } catch (error) {
                        if (request.reject) {
                            request.reject(error);
                        }
                        return { success: false, request, error };
                    }
                });

                // 等待这批请求完成
                await Promise.allSettled(promises);
                
                // 如果队列中还有请求，短暂延迟后继续处理
                if (this.requestQueue.length > 0) {
                    await this.sleep(100); // 100ms延迟
                }
            }

            this.logRequest('QUEUE_PROCESSING_COMPLETE', { 
                remainingQueueLength: this.requestQueue.length 
            });

        } catch (error) {
            this.logRequest('QUEUE_PROCESSING_ERROR', { error: error.message });
            console.error(`[api-client.js] 处理请求队列时发生错误:`, error);
        } finally {
            this.isProcessingQueue = false;
        }
    }

    /**
     * GET请求
     */
    async get(endpoint, options = {}) {
        if (this.connectionStatus !== 'connected') {
            return new Promise((resolve, reject) => {
                this.queueRequest('GET', endpoint, null, resolve, reject);
            });
        }
        
        return this.fetch(endpoint, { method: 'GET', ...options });
    }

    /**
     * POST请求
     */
    async post(endpoint, data, options = {}) {
        if (this.connectionStatus !== 'connected') {
            return new Promise((resolve, reject) => {
                this.queueRequest('POST', endpoint, data, resolve, reject);
            });
        }
        
        return this.fetch(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined,
            ...options
        });
    }

    /**
     * PUT请求
     */
    async put(endpoint, data, options = {}) {
        if (this.connectionStatus !== 'connected') {
            return new Promise((resolve, reject) => {
                this.queueRequest('PUT', endpoint, data, resolve, reject);
            });
        }
        
        return this.fetch(endpoint, {
            method: 'PUT',
            body: data ? JSON.stringify(data) : undefined,
            ...options
        });
    }

    /**
     * DELETE请求
     */
    async delete(endpoint, options = {}) {
        if (this.connectionStatus !== 'connected') {
            return new Promise((resolve, reject) => {
                this.queueRequest('DELETE', endpoint, null, resolve, reject);
            });
        }
        
        return this.fetch(endpoint, { method: 'DELETE', ...options });
    }

    /**
     * 获取服务器状态
     */
    async getStatus() {
        return this.get('/api/status');
    }

    /**
     * 用户认证
     */
    async authenticate(credentials) {
        const response = await this.post('/api/auth', credentials);
        
        if (response.success) {
            this.authenticated = true;
            this.saveSession().catch(error => console.error(`[api-client.js] this.saveSession failed:`, error));
            this.emit('authenticated', response.data);
        }
        
        return response;
    }

    /**
     * 获取连接状态
     */
    getConnectionStatus() {
        return {
            status: this.connectionStatus,
            authenticated: this.authenticated,
            lastHeartbeat: this.lastHeartbeat,
            sessionId: this.sessionId,
            reconnectAttempts: this.reconnectAttempts
        };
    }

    /**
     * 解析错误响应
     */
    async parseErrorResponse(response) {
        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return { message: await response.text() };
            }
        } catch (error) {
            return { message: response.statusText };
        }
    }

    /**
     * 获取CSRF令牌
     */
    getCSRFToken() {
        try {
            return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                   localStorage.getItem('csrf-token') ||
                   sessionStorage.getItem('csrf-token');
        } catch (error) {
            return null;
        }
    }

    /**
     * 记录请求日志
     */
    logRequest(type, data) {
        try {
            const logEntry = {
                type,
                timestamp: new Date().toISOString(),
                ...data
            };
            
            console.log(`[API Client] ${type}:`, logEntry);
            
            // 触发事件
            if (this.eventEmitter) {
                this.eventEmitter.emit('apiLog', logEntry);
            }
        } catch (error) {
            console.error(`[api-client.js] 记录请求日志失败:, error`);
        }
    }
}

// 创建全局实例
window.MTSCOSApiClient = MTSCOSApiClient;

// 自动初始化
window.mtscosApi = new MTSCOSApiClient();

// 页面加载完成后自动连接
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // 延迟2秒后尝试连接，确保所有资源都已加载
        setTimeout(() => {
            window.mtscosApi.connect().catch(error => {
                console.error('[API客户端] 自动连接失败:', error);
                // 尝试重新连接
                setTimeout(() => {
                    window.mtscosApi.connect().catch(err => {
                        console.error('[API客户端] 重连失败:', err);
                    });
                }, 3000);
            });
        }, 2000);
    });
} else {
    // 延迟2秒后尝试连接，确保所有资源都已加载
    setTimeout(() => {
        window.mtscosApi.connect().catch(error => {
            console.error('[API客户端] 自动连接失败:', error);
            // 尝试重新连接
            setTimeout(() => {
                window.mtscosApi.connect().catch(err => {
                    console.error('[API客户端] 重连失败:', err);
                });
            }, 3000);
        });
    }, 2000);
}

console.log('[API客户端] MTSCOS API客户端已加载');
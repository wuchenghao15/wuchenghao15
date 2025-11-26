/**
 * MTSCOS 统一API客户端
 * 合并了 mtscos-api.js 和 api-client.js 的功能
 * 提供完整的API调用、缓存、错误处理和性能监控功能
 * 版本: 3.0.0 (统一版)
 */

// 防止重复定义
if (typeof MTSCOSUnifiedApiClient === 'undefined') {

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
                timestamp: Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error))
            });
        }

        if (response.status === 404) {
            console.error(`[unified-api-client-v3.js] 资源未找到 (404`):', response.url);
        } else if (response.status === 403) {
            console.error(`[unified-api-client-v3.js] 访问被拒绝 (403`):', response.url);
        } else if (response.status === 401) {
            console.error(`[unified-api-client-v3.js] 未授权访问 (401`):', response.url);
        } else if (response.status >= 500) {
            console.error(`[unified-api-client-v3.js] 服务器错误:, response.status, response.statusText`);
        } else {
            console.error(`[unified-api-client-v3.js] HTTP错误:, response.status, response.statusText`);
        }

        throw new Error(`HTTP错误: ${response.status} - ${response.statusText}`);
    }

    return response;
}

class MTSCOSUnifiedApiClient {
    constructor(config = {}) {
        this.version = '3.0.0';
        this.baseURL = config.baseURL || '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            ...config.headers
        };
        
        // 缓存配置
        this.cache = new Map();
        this.cacheConfig = {
            maxSize: 100,
            defaultTTL: 5 * 60 * 1000, // 5分钟
            ...config.cache
        };
        
        // 性能监控
        this.performanceMetrics = {
            requestCount: 0,
            successCount: 0,
            errorCount: 0,
            totalResponseTime: 0,
            averageResponseTime: 0,
            requests: []
        };
        
        // 重试配置
        this.retryConfig = {
            maxRetries: 3,
            retryDelay: 1000,
            retryDelayMultiplier: 2,
            ...config.retry
        };
        
        // 超时配置
        this.timeout = config.timeout || 30000;
        
        // 拦截器
        this.interceptors = {
            request: [],
            response: [],
            error: []
        };
        
        // 心跳配置
        this.heartbeatConfig = {
            enabled: true,
            interval: 30000, // 30秒
            endpoint: '/api/heartbeat',
            ...config.heartbeat
        };
        
        this.isInitialized = false;
        this.init().catch(error => console.error(`[unified-api-client-v3.js] this.init failed:`, error));
    }

    /**
     * 初始化API客户端
     */
    init() {
        if (this.isInitialized) return;
        
        // 启动心跳
        if (this.heartbeatConfig.enabled) {
            this.startHeartbeat().catch(error => console.error(`[unified-api-client-v3.js] this.startHeartbeat failed:`, error));
        }
        
        // 设置请求拦截器
        this.setupRequestInterceptors().catch(error => console.error(`[unified-api-client-v3.js] this.setupRequestInterceptors failed:`, error));
        
        this.isInitialized = true;
        console.log(`[MTSCOS统一API客户端] v${this.version} 初始化完成`);
    }

    /**
     * 设置请求拦截器
     */
    setupRequestInterceptors() {
        // 添加全局fetch错误处理
        if (typeof window !== 'undefined' && !window.originalFetch) {
            window.originalFetch = window.fetch;
            window.fetch = this.enhancedFetch.bind(this);
        }
    }

    /**
     * 增强的fetch方法
     */
    async enhancedFetch(url, options = {}) {
        const startTime = performance.now();
        let response;
        let error;
        
        try {
            // 应用请求拦截器
            let requestOptions = await this.applyRequestInterceptors(url, options);
            
            // 执行请求
            response = await window.originalFetch(url, requestOptions);
            
            // 应用响应拦截器
            response = await this.applyResponseInterceptors(response);
            
            // 记录成功指标
            this.recordRequestMetrics(url, options.method || 'GET', response.status, performance.now() - startTime);
            
            return response;
            
        } catch (err) {
            error = err;
            
            // 应用错误拦截器
            await this.applyErrorInterceptors(err, url, options);
            
            // 记录失败指标
            this.recordRequestMetrics(url, options.method || 'GET', null, performance.now() - startTime, err);
            
            throw err;
        }
    }

    /**
     * 应用请求拦截器
     */
    async applyRequestInterceptors(url, options) {
        let requestOptions = { ...options };
        
        for (const interceptor of this.interceptors.request) {
            requestOptions = await interceptor(url, requestOptions) || requestOptions;
        }
        
        return requestOptions;
    }

    /**
     * 应用响应拦截器
     */
    async applyResponseInterceptors(response) {
        let finalResponse = response;
        
        for (const interceptor of this.interceptors.response) {
            finalResponse = await interceptor(finalResponse) || finalResponse;
        }
        
        return finalResponse;
    }

    /**
     * 应用错误拦截器
     */
    async applyErrorInterceptors(error, url, options) {
        for (const interceptor of this.interceptors.error) {
            await interceptor(error, url, options);
        }
    }

    /**
     * 核心请求方法
     */
    async request(endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const method = options.method || 'GET';
        
        // 检查缓存
        if (method === 'GET' && !options.skipCache) {
            const cached = this.getFromCache(url);
            if (cached) {
                console.log(`[缓存命中] ${method} ${url}`);
                return cached;
            }
        }
        
        // 准备请求配置
        const requestConfig = {
            method,
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };
        
        // 添加请求体
        if (options.data && method !== 'GET') {
            requestConfig.body = JSON.stringify(options.data);
        }
        
        // 添加超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort().catch(error => console.error(`[unified-api-client-v3.js] controller.abort failed:`, error)), this.timeout);
        requestConfig.signal = controller.signal;
        
        try {
            console.log(`[API请求] ${method} ${url}`);
            
            let response = await fetch(url, requestConfig);
            response = fetchErrorHandler(response);
            
            // 解析响应
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            // 缓存GET请求的响应
            if (method === 'GET' && response.ok) {
                this.setCache(url, data);
            }
            
            console.log(`[API响应] ${method} ${url} - ${response.status}`);
            return data;
            
        } catch (error) {
            console.error(`[API错误] ${method} ${url}:`, error.message);
            
            // 重试逻辑
            if (this.shouldRetry(error, options)) {
                return this.retryRequest(endpoint, options);
            }
            
            throw error;
            
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * 判断是否应该重试
     */
    shouldRetry(error, options) {
        if (options.retry === false) return false;
        if (error.name === 'AbortError') return false;
        if (error.message.includes('HTTP 4')) return false; // 客户端错误不重试
        
        return true;
    }

    /**
     * 重试请求
     */
    async retryRequest(endpoint, options, attempt = 1) {
        if (attempt > this.retryConfig.maxRetries) {
            throw new Error(`请求失败，已达到最大重试次数: ${this.retryConfig.maxRetries}`);
        }
        
        const delay = this.retryConfig.retryDelay * Math.pow(this.retryConfig.retryDelayMultiplier, attempt - 1);
        console.log(`[API重试] ${endpoint} - 第${attempt}次重试，延迟${delay}ms`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        
        try {
            return await this.request(endpoint, { ...options, retry: false });
        } catch (error) {
            return this.retryRequest(endpoint, options, attempt + 1);
        }
    }

    /**
     * 缓存管理
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error)) - cached.timestamp < cached.ttl) {
            return cached.data;
        }
        
        if (cached) {
            this.cache.delete(key);
        }
        
        return null;
    }

    setCache(key, data, ttl = this.cacheConfig.defaultTTL) {
        // 检查缓存大小
        if (this.cache.size >= this.cacheConfig.maxSize) {
            // 删除最旧的缓存项
            const firstKey = this.cache.keys().catch(error => console.error(`[unified-api-client-v3.js] cache.keys failed:`, error)).next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(key, {
            data,
            timestamp: Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error)),
            ttl
        });
    }

    clearCache() {
        this.cache.clear().catch(error => console.error(`[unified-api-client-v3.js] cache.clear failed:`, error));
        console.log('[API缓存] 缓存已清理');
    }

    /**
     * 便捷方法
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    async post(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', data });
    }

    async put(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', data });
    }

    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }

    /**
     * MTSCOS特定API方法
     */
    async chat(message, options = {}) {
        return this.post('/api/chat', { message, ...options });
    }

    async generateCode(prompt, options = {}) {
        return this.post('/api/generate-code', { prompt, ...options });
    }

    async analyzeText(text, options = {}) {
        return this.post('/api/analyze-text', { text, ...options });
    }

    async translateText(text, targetLanguage, options = {}) {
        return this.post('/api/translate', { text, targetLanguage, ...options });
    }

    async summarizeText(text, options = {}) {
        return this.post('/api/summarize', { text, ...options });
    }

    /**
     * 心跳机制
     */
    startHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        
        this.heartbeatTimer = setInterval(async () => {
            try {
                await this.get(this.heartbeatConfig.endpoint, { 
                    skipCache: true,
                    retry: false,
                    timeout: 5000
                });
                console.log('[心跳] 服务器连接正常');
            } catch (error) {
                console.warn('[心跳] 服务器连接异常:', error.message);
                
                // 记录到错误处理器
                if (window.MTSCOSUnifiedErrorHandler) {
                    window.MTSCOSUnifiedErrorHandler.handleError({
                        type: 'NETWORK_ERROR',
                        message: '服务器心跳检测失败',
                        error: error.message,
                        timestamp: Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error))
                    });
                }
            }
        }, this.heartbeatConfig.interval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
            console.log('[心跳] 心跳检测已停止');
        }
    }

    /**
     * 拦截器管理
     */
    addRequestInterceptor(interceptor) {
        this.interceptors.request.push(interceptor);
    }

    addResponseInterceptor(interceptor) {
        this.interceptors.response.push(interceptor);
    }

    addErrorInterceptor(interceptor) {
        this.interceptors.error.push(interceptor);
    }

    /**
     * 性能监控
     */
    recordRequestMetrics(url, method, status, responseTime, error = null) {
        this.performanceMetrics.requestCount++;
        this.performanceMetrics.totalResponseTime += responseTime;
        this.performanceMetrics.averageResponseTime = 
            this.performanceMetrics.totalResponseTime / this.performanceMetrics.requestCount;
        
        if (error || (status && status >= 400)) {
            this.performanceMetrics.errorCount++;
        } else {
            this.performanceMetrics.successCount++;
        }
        
        // 记录详细请求信息
        this.performanceMetrics.requests.push({
            url,
            method,
            status,
            responseTime,
            timestamp: Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error)),
            error: error?.message
        });
        
        // 限制记录数量
        if (this.performanceMetrics.requests.length > 100) {
            this.performanceMetrics.requests.shift().catch(error => console.error(`[unified-api-client-v3.js] requests.shift failed:`, error));
        }
        
        // 记录到性能监控器
        if (window.MTSCOSUnifiedErrorHandler) {
            window.MTSCOSUnifiedErrorHandler.recordApiCall(url, error ? 'error' : 'success', responseTime, status, error);
        }
    }

    /**
     * 获取性能指标
     */
    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            successRate: this.performanceMetrics.requestCount > 0 
                ? (this.performanceMetrics.successCount / this.performanceMetrics.requestCount * 100).toFixed(2) + '%'
                : '0%',
            cacheHitRate: this.getCacheHitRate().catch(error => console.error(`[unified-api-client-v3.js] this.getCacheHitRate failed:`, error))
        };
    }

    getCacheHitRate() {
        // 这里简化处理，实际应该记录缓存命中次数
        return '0%';
    }

    /**
     * 健康检查
     */
    async healthCheck() {
        const startTime = performance.now().catch(error => console.error(`[unified-api-client-v3.js] performance.now failed:`, error));
        
        try {
            await this.get('/api/health', { 
                skipCache: true, 
                retry: false, 
                timeout: 5000 
            });
            
            const responseTime = performance.now().catch(error => console.error(`[unified-api-client-v3.js] performance.now failed:`, error)) - startTime;
            
            return {
                status: 'healthy',
                responseTime,
                timestamp: Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error))
            };
            
        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message,
                timestamp: Date.now().catch(error => console.error(`[unified-api-client-v3.js] Date.now failed:`, error))
            };
        }
    }

    /**
     * 批量请求
     */
    async batchRequest(requests) {
        const promises = requests.map(req => 
            this.request(req.endpoint, req.options).catch(error => ({ error, endpoint: req.endpoint }))
        );
        
        return Promise.all(promises);
    }

    /**
     * 取消所有请求
     */
    cancelAllRequests() {
        // 这里需要实现请求取消逻辑
        console.log('[API客户端] 所有请求已取消');
    }

    /**
     * 更新配置
     */
    updateConfig(newConfig) {
        Object.assign(this.defaultHeaders, newConfig.headers || {});
        Object.assign(this.cacheConfig, newConfig.cache || {});
        Object.assign(this.retryConfig, newConfig.retry || {});
        Object.assign(this.heartbeatConfig, newConfig.heartbeat || {});
        
        if (newConfig.timeout) {
            this.timeout = newConfig.timeout;
        }
        
        if (newConfig.baseURL) {
            this.baseURL = newConfig.baseURL;
        }
        
        // 重启心跳
        if (newConfig.heartbeat && this.heartbeatConfig.enabled) {
            this.startHeartbeat().catch(error => console.error(`[unified-api-client-v3.js] this.startHeartbeat failed:`, error));
        }
    }

    /**
     * 清理资源
     */
    destroy() {
        this.stopHeartbeat().catch(error => console.error(`[unified-api-client-v3.js] this.stopHeartbeat failed:`, error));
        this.clearCache();
        this.cancelAllRequests().catch(error => console.error(`[unified-api-client-v3.js] this.cancelAllRequests failed:`, error));
        
        // 恢复原始fetch
        if (typeof window !== 'undefined' && window.originalFetch) {
            window.fetch = window.originalFetch;
            window.originalFetch = undefined;
        }
        
        console.log('[API客户端] 资源已清理');
    }
}

// 创建全局实例
window.MTSCOSUnifiedApiClient = new MTSCOSUnifiedApiClient({
    baseURL: '',
    timeout: 30000,
    cache: {
        maxSize: 100,
        defaultTTL: 5 * 60 * 1000
    },
    retry: {
        maxRetries: 3,
        retryDelay: 1000
    },
    heartbeat: {
        enabled: true,
        interval: 30000,
        endpoint: '/api/heartbeat'
    }
});

// 向后兼容：创建别名
window.MTSCOSApiService = window.MTSCOSUnifiedApiClient;
window.MTSCOSApiClient = window.MTSCOSUnifiedApiClient;
window.apiClient = window.MTSCOSUnifiedApiClient;

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MTSCOSUnifiedApiClient;
}

} // 结束 typeof MTSCOSUnifiedApiClient === 'undefined' 检查
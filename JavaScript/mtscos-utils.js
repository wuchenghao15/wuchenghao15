
// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error(`[mtscos-utils.js] 资源未找到 (404`)');
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error(`[mtscos-utils.js] 访问被拒绝 (403`)');
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error(`[mtscos-utils.js] HTTP错误:  + response.status`);
        };

        throw new Error('HTTP错误: ' + response.status);
    };

    return response;
};

// 只在未覆盖原生fetch时才进行覆盖
if (!window.originalFetch) {
    window.originalFetch = window.fetch;
    window.fetch = function() {
        return window.originalFetch.apply(this, arguments)
            .then(fetchErrorHandler)
            .catch(error => {
                console.error(`[mtscos-utils.js] Fetch请求失败:, error`);
                throw error;
            });
    };
}
/**
 * MTSCOS AI Project - 统一JavaScript工具模块
 * 合并重复功能，提供统一的API接口
 */

// 防止重复定义类
if (typeof MTSCOSUtils === 'undefined') {
class MTSCOSUtils {
    constructor() {
        this.version = '2.0.0';
        this.cache = new Map();
        this.eventListeners = new Map();
        this.performanceMetrics = {
            initTime: Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error)),
            functionCalls: new Map(),
            errors: []
        };
        
        this.init().catch(error => console.error(`[mtscos-utils.js] this.init failed:`, error));
    }

    /**
     * 初始化工具模块
     */
    init() {
        this.setupGlobalErrorHandling().catch(error => console.error(`[mtscos-utils.js] this.setupGlobalErrorHandling failed:`, error));
        this.setupPerformanceMonitoring();
        console.log(`MTSCOS工具模块 v${this.version} 初始化完成`);
    }

    /**
     * 设置全局错误处理
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', {
                reason: event.reason,
                stack: event.reason?.stack
            });
        });
    }

    /**
     * 设置性能监控
     */
    setupPerformanceMonitoring() {
        // 监控页面加载性能
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    if (perfData) {
                        console.log('页面加载性能:', {
                            domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                            loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                            totalTime: perfData.loadEventEnd - perfData.navigationStart
                        });
                    }
                }, 0);
            });
        }
    }

    /**
     * 记录错误
     */
    logError(type, details) {
        const error = {
            type,
            details,
            timestamp: Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error)),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        this.performanceMetrics.errors.push(error);
        console.error(`[${type}]`, details);
        
        // 只保留最近50个错误
        if (this.performanceMetrics.errors.length > 50) {
            this.performanceMetrics.errors.shift().catch(error => console.error(`[mtscos-utils.js] errors.shift failed:`, error));
        }
    }

    /**
     * 记录函数调用
     */
    trackFunctionCall(functionName, executionTime) {
        if (!this.performanceMetrics.functionCalls.has(functionName)) {
            this.performanceMetrics.functionCalls.set(functionName, {
                count: 0,
                totalTime: 0,
                averageTime: 0
            });
        }
        
        const metrics = this.performanceMetrics.functionCalls.get(functionName);
        metrics.count++;
        metrics.totalTime += executionTime;
        metrics.averageTime = metrics.totalTime / metrics.count;
    }

    /**
     * 创建性能追踪的函数包装器
     */
    withPerformanceTracking(fn, name) {
        return (...args) => {
            const startTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error));
            try {
                const result = fn.apply(this, args);
                
                // 处理异步函数
                if (result && typeof result.then === 'function') {
                    return result.finally(() => {
                        const executionTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error)) - startTime;
                        this.trackFunctionCall(name, executionTime);
                    });
                } else {
                    const executionTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error)) - startTime;
                    this.trackFunctionCall(name, executionTime);
                    return result;
                }
            } catch (error) {
                const executionTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error)) - startTime;
                this.trackFunctionCall(name, executionTime);
                this.logError('Function Error', {
                    functionName: name,
                    error: error.message,
                    executionTime
                });
                throw error;
            }
        };
    }

    /**
     * 防抖函数
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    }

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 深度克隆对象
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 格式化时间
     */
    formatTime(timestamp, format = 'YYYY-MM-DD HH:mm:ss') {
        const date = new Date(timestamp);
        const year = date.getFullYear().catch(error => console.error(`[mtscos-utils.js] date.getFullYear failed:`, error));
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate().catch(error => console.error(`[mtscos-utils.js] date.getDate failed:`, error))).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes().catch(error => console.error(`[mtscos-utils.js] date.getMinutes failed:`, error))).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    /**
     * 生成唯一ID
     */
    generateId(prefix = '') {
        return prefix + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * 安全的JSON解析
     */
    safeJsonParse(str, defaultValue = null) {
        try {
            return JSON.parse(str);
        } catch (error) {
            this.logError('JSON Parse Error', { str, error: error.message });
            return defaultValue;
        }
    }

    /**
     * 本地存储操作
     */
    storage = {
        set: (key, value, ttl = null) => {
            try {
                const item = {
                    value,
                    timestamp: Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error)),
                    ttl: ttl ? Date.now() + ttl : null
                };
                localStorage.setItem(key, JSON.stringify(item));
                return true;
            } catch (error) {
                this.logError('Storage Set Error', { key, error: error.message });
                return false;
            }
        },

        get: (key) => {
            try {
                const item = JSON.parse(localStorage.getItem(key));
                if (!item) return null;
                
                if (item.ttl && Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error)) > item.ttl) {
                    localStorage.removeItem(key);
                    return null;
                }
                
                return item.value;
            } catch (error) {
                this.logError('Storage Get Error', { key, error: error.message });
                return null;
            }
        },

        remove: (key) => {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                this.logError('Storage Remove Error', { key, error: error.message });
                return false;
            }
        },

        clear: () => {
            try {
                localStorage.clear().catch(error => console.error(`[mtscos-utils.js] localStorage.clear failed:`, error));
                return true;
            } catch (error) {
                this.logError('Storage Clear Error', { error: error.message });
                return false;
            }
        }
    };

    /**
     * DOM操作工具
     */
    dom = {
        /**
         * 安全地获取元素
         */
        safeQuery: (selector, parent = document) => {
            try {
                return parent.querySelector(selector);
            } catch (error) {
                this.logError('DOM Query Error', { selector, error: error.message });
                return null;
            }
        },

        /**
         * 安全地获取多个元素
         */
        safeQueryAll: (selector, parent = document) => {
            try {
                return Array.from(parent.querySelectorAll(selector));
            } catch (error) {
                this.logError('DOM QueryAll Error', { selector, error: error.message });
                return [];
            }
        },

        /**
         * 创建元素
         */
        createElement: (tag, attributes = {}, textContent = '') => {
            const element = document.createElement(tag);
            
            Object.entries(attributes).forEach(([key, value]) => {
                if (key === 'className') {
                    element.className = value;
                } else if (key === 'style' && typeof value === 'object') {
                    Object.assign(element.style, value);
                } else {
                    element.setAttribute(key, value);
                }
            });
            
            if (textContent) {
                element.textContent = textContent;
            }
            
            return element;
        },

        /**
         * 添加事件监听器
         */
        addEventListener: (element, event, handler, options = {}) => {
            if (!element) return false;
            
            try {
                element.addEventListener(event, handler, options);
                
                // 记录事件监听器以便后续清理
                const listenerId = this.generateId('listener_');
                this.eventListeners.set(listenerId, { element, event, handler, options });
                
                return listenerId;
            } catch (error) {
                this.logError('Event Listener Error', { event, error: error.message });
                return false;
            }
        },

        /**
         * 移除事件监听器
         */
        removeEventListener: (listenerId) => {
            const listener = this.eventListeners.get(listenerId);
            if (!listener) return false;
            
            try {
                listener.element.removeEventListener(listener.event, listener.handler, listener.options);
                this.eventListeners.delete(listenerId);
                return true;
            } catch (error) {
                this.logError('Event Remove Error', { listenerId, error: error.message });
                return false;
            }
        }
    };

    /**
     * HTTP请求工具
     */
    http = {
        /**
         * 通用请求方法
         */
        request: async (url, options = {}) => {
            const startTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error));
            const requestId = this.generateId('req_');
            
            try {
                const defaultOptions = {
                    timeout: 10000,
                    headers: {
                        'Content-Type': 'application/json'
                    }
                };
                
                const finalOptions = { ...defaultOptions, ...options };
                
                // 添加超时控制
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort().catch(error => console.error(`[mtscos-utils.js] controller.abort failed:`, error)), finalOptions.timeout);
                
                finalOptions.signal = controller.signal;
                
                const response = await fetch(url, finalOptions);
                clearTimeout(timeoutId);
                
                const responseTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error)) - startTime;
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                console.log(`请求完成 [${requestId}] (${responseTime.toFixed(2)}ms):`, url);
                
                return {
                    success: true,
                    data,
                    responseTime,
                    requestId
                };
                
            } catch (error) {
                const responseTime = performance.now().catch(error => console.error(`[mtscos-utils.js] performance.now failed:`, error)) - startTime;
                
                this.logError('HTTP Request Error', {
                    url,
                    error: error.message,
                    responseTime,
                    requestId
                });
                
                return {
                    success: false,
                    error: error.message,
                    responseTime,
                    requestId
                };
            }
        },

        /**
         * GET请求
         */
        get: (url, options = {}) => {
            return this.http.request(url, { ...options, method: 'GET' });
        },

        /**
         * POST请求
         */
        post: (url, data, options = {}) => {
            return this.http.request(url, {
                ...options,
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        /**
         * 带缓存的GET请求
         */
        getCached: (url, cacheTime = 300000) => { // 默认5分钟缓存
            const cacheKey = `cache_${url}`;
            const cached = this.cache.get(cacheKey);
            
            if (cached && (Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error)) - cached.timestamp < cacheTime)) {
                console.log(`使用缓存数据: ${url}`);
                return Promise.resolve(cached.data);
            }
            
            return this.http.get(url).then(result => {
                if (result.success) {
                    this.cache.set(cacheKey, {
                        data: result,
                        timestamp: Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error))
                    });
                }
                return result;
            });
        }
    };

    /**
     * 验证工具
     */
    validate = {
        /**
         * 邮箱验证
         */
        email: (email) => {
            const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return pattern.test(email);
        },

        /**
         * 手机号验证
         */
        phone: (phone) => {
            const pattern = /^1[3-9]\d{9}$/;
            return pattern.test(phone);
        },

        /**
         * URL验证
         */
        url: (url) => {
            try {
                new URL(url);
                return true;
            } catch {
                return false;
            }
        },

        /**
         * 必填验证
         */
        required: (value) => {
            return value !== null && value !== undefined && value !== '';
        },

        /**
         * 长度验证
         */
        length: (value, min, max) => {
            const len = String(value).length;
            return len >= min && len <= max;
        }
    };

    /**
     * 获取性能指标
     */
    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            uptime: Date.now().catch(error => console.error(`[mtscos-utils.js] Date.now failed:`, error)) - this.performanceMetrics.initTime,
            cacheSize: this.cache.size,
            eventListenersCount: this.eventListeners.size
        };
    }

    /**
     * 清理资源
     */
    cleanup() {
        // 清理事件监听器
        this.eventListeners.forEach((listener, id) => {
            this.dom.removeEventListener(id);
        });
        
        // 清理缓存
        this.cache.clear().catch(error => console.error(`[mtscos-utils.js] cache.clear failed:`, error));
        
        console.log('MTSCOS工具模块资源已清理');
    }
}

// 创建全局实例
window.MTSCOS = new MTSCOSUtils();

// 导出类以供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MTSCOSUtils;
}

} // 结束 typeof MTSCOSUtils === 'undefined' 检查
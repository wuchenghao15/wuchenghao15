/**
 * 统一错误处理机制
 * 用于处理项目中所有的异常情况，避免未捕获的错误导致系统崩溃
 */

class UnifiedErrorHandler {
    constructor() {
        this.errorTypes = {
            HTTP_ERROR: 'HTTP_ERROR',
            LOGIN_ERROR: 'LOGIN_ERROR', 
            SECURITY_ERROR: 'SECURITY_ERROR',
            VALIDATION_ERROR: 'VALIDATION_ERROR',
            NETWORK_ERROR: 'NETWORK_ERROR',
            SYSTEM_ERROR: 'SYSTEM_ERROR'
        };
        
        this.errorLog = [];
        this.maxLogSize = 1000;
        this.isInitialized = false;
        
        this.init();
    }
    
    /**
     * 初始化错误处理器
     */
    init() {
        if (this.isInitialized) return;
        
        // 设置全局错误处理
        this.setupGlobalErrorHandlers();
        
        // 设置未处理的Promise拒绝处理
        this.setupUnhandledRejectionHandler();
        
        this.isInitialized = true;
        console.log('[UnifiedErrorHandler] 统一错误处理器已初始化');
    }
    
    /**
     * 设置全局错误处理器
     */
    setupGlobalErrorHandlers() {
        // 捕获JavaScript运行时错误
        window.addEventListener('error', (event) => {
            this.handleError({
                type: this.errorTypes.SYSTEM_ERROR,
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error,
                timestamp: new Date().toISOString()
            });
        });
        
        // 捕获资源加载错误
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.handleError({
                    type: this.errorTypes.NETWORK_ERROR,
                    message: `资源加载失败: ${event.target.src || event.target.href}`,
                    element: event.target.tagName,
                    source: event.target.src || event.target.href,
                    timestamp: new Date().toISOString()
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
                type: this.errorTypes.SYSTEM_ERROR,
                message: '未处理的Promise拒绝',
                reason: event.reason,
                promise: event.promise,
                timestamp: new Date().toISOString()
            });
            
            // 防止错误在控制台显示
            event.preventDefault();
        });
    }
    
    /**
     * 处理错误的核心方法
     */
    handleError(errorInfo) {
        try {
            // 记录错误
            this.logError(errorInfo);
            
            // 根据错误类型进行处理
            switch(errorInfo.type) {
                case this.errorTypes.HTTP_ERROR:
                    this.handleHttpError(errorInfo);
                    break;
                case this.errorTypes.LOGIN_ERROR:
                    this.handleLoginError(errorInfo);
                    break;
                case this.errorTypes.SECURITY_ERROR:
                    this.handleSecurityError(errorInfo);
                    break;
                case this.errorTypes.VALIDATION_ERROR:
                    this.handleValidationError(errorInfo);
                    break;
                case this.errorTypes.NETWORK_ERROR:
                    this.handleNetworkError(errorInfo);
                    break;
                case this.errorTypes.SYSTEM_ERROR:
                default:
                    this.handleSystemError(errorInfo);
                    break;
            }
        } catch (handlingError) {
            // 防止错误处理本身出错
            console.error('[UnifiedErrorHandler] 错误处理失败:', handlingError);
        }
    }
    
    /**
     * 处理HTTP错误
     */
    handleHttpError(errorInfo) {
        console.error(`[HTTP错误] ${errorInfo.message}`);
        
        // 根据状态码进行特殊处理
        if (errorInfo.status) {
            switch(errorInfo.status) {
                case 401:
                    this.showUserMessage('登录已过期，请重新登录', 'warning');
                    this.redirectToLogin();
                    break;
                case 403:
                    this.showUserMessage('访问被拒绝，权限不足', 'error');
                    break;
                case 404:
                    console.warn(`[404] 资源未找到: ${errorInfo.url}`);
                    break;
                case 500:
                    this.showUserMessage('服务器内部错误，请稍后重试', 'error');
                    break;
                default:
                    this.showUserMessage(`网络错误: ${errorInfo.status}`, 'error');
            }
        }
    }
    
    /**
     * 处理登录错误
     */
    handleLoginError(errorInfo) {
        console.error(`[登录错误] ${errorInfo.message}`);
        
        // 不直接抛出错误，而是记录并显示用户友好的消息
        if (errorInfo.message.includes('不支持的登录方式')) {
            this.showUserMessage('暂不支持此登录方式，请选择其他登录方式', 'warning');
        } else {
            this.showUserMessage(errorInfo.message || '登录失败，请重试', 'error');
        }
    }
    
    /**
     * 处理安全错误
     */
    handleSecurityError(errorInfo) {
        console.error(`[安全错误] ${errorInfo.message}`);
        
        // 安全错误不应该向用户显示详细信息
        if (errorInfo.message.includes('危险标签')) {
            console.warn('[安全警告] 检测到潜在的脚本注入尝试，已阻止');
            // 不显示用户消息，避免泄露安全信息
        } else {
            this.showUserMessage('安全检查失败，操作已阻止', 'error');
        }
    }
    
    /**
     * 处理验证错误
     */
    handleValidationError(errorInfo) {
        console.warn(`[验证错误] ${errorInfo.message}`);
        this.showUserMessage(errorInfo.message || '输入验证失败', 'warning');
    }
    
    /**
     * 处理网络错误
     */
    handleNetworkError(errorInfo) {
        console.error(`[网络错误] ${errorInfo.message}`);
        this.showUserMessage('网络连接异常，请检查网络设置', 'error');
    }
    
    /**
     * 处理系统错误
     */
    handleSystemError(errorInfo) {
        console.error(`[系统错误] ${errorInfo.message}`);
        
        // 系统错误通常不需要显示给用户，只记录日志
        // 但如果是关键错误，可以显示通用消息
        if (errorInfo.fatal) {
            this.showUserMessage('系统出现错误，请刷新页面重试', 'error');
        }
    }
    
    /**
     * 记录错误日志
     */
    logError(errorInfo) {
        const logEntry = {
            ...errorInfo,
            id: Date.now() + Math.random(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        this.errorLog.push(logEntry);
        
        // 限制日志大小
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog = this.errorLog.slice(-this.maxLogSize);
        }
        
        // 输出到控制台（开发环境）
        if (console && console.error) {
            console.error('[错误日志]', logEntry);
        }
        
        // 发送到服务器（如果需要）
        this.sendErrorToServer(logEntry);
    }
    
    /**
     * 发送错误到服务器
     */
    sendErrorToServer(errorInfo) {
        // 只在生产环境发送
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return;
        }
        
        try {
            fetch('/api/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorInfo)
            }).catch(() => {
                // 忽略发送失败，避免无限循环
            });
        } catch (e) {
            // 忽略发送失败
        }
    }
    
    /**
     * 显示用户友好的消息
     */
    showUserMessage(message, type = 'info') {
        // 检查是否有统一的消息显示组件
        if (window.authManager && window.authManager.showMessage) {
            window.authManager.showMessage(message, type);
            return;
        }
        
        // 检查页面是否有错误消息元素
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            const errorText = document.getElementById('error-text') || errorElement;
            errorText.textContent = message;
            
            // 设置背景颜色
            switch(type) {
                case 'error':
                    errorElement.style.backgroundColor = '#dc3545';
                    break;
                case 'warning':
                    errorElement.style.backgroundColor = '#ffc107';
                    break;
                case 'success':
                    errorElement.style.backgroundColor = '#28a745';
                    break;
                default:
                    errorElement.style.backgroundColor = '#007bff';
            }
            
            errorElement.style.display = 'block';
            
            // 自动隐藏
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 3000);
        } else {
            // 回退到alert
            if (type === 'error' || type === 'warning') {
                console.warn(`[用户消息] ${message}`);
            } else {
                console.log(`[用户消息] ${message}`);
            }
        }
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
     * 安全的fetch包装器
     */
    safeFetch(url, options = {}) {
        return fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    // 不直接抛出错误，而是通过错误处理器处理
                    this.handleError({
                        type: this.errorTypes.HTTP_ERROR,
                        message: `HTTP错误: ${response.status}`,
                        status: response.status,
                        url: url,
                        timestamp: new Date().toISOString()
                    });
                    
                    // 返回一个rejected的Promise，但包含错误信息
                    return Promise.reject({
                        handled: true,
                        status: response.status,
                        message: `HTTP错误: ${response.status}`
                    });
                }
                return response;
            })
            .catch(error => {
                // 如果错误已经被处理过，直接重新抛出
                if (error.handled) {
                    throw error;
                }
                
                // 处理网络错误
                this.handleError({
                    type: this.errorTypes.NETWORK_ERROR,
                    message: `网络请求失败: ${error.message}`,
                    url: url,
                    timestamp: new Date().toISOString()
                });
                
                throw {
                    handled: true,
                    message: '网络请求失败'
                };
            });
    }
    
    /**
     * 安全的错误抛出方法
     */
    safeThrow(error, type = this.errorTypes.SYSTEM_ERROR) {
        this.handleError({
            type: type,
            message: error.message || error,
            timestamp: new Date().toISOString()
        });
        
        // 返回一个rejected的Promise而不是抛出错误
        return Promise.reject({
            handled: true,
            type: type,
            message: error.message || error
        });
    }
    
    /**
     * 获取错误日志
     */
    getErrorLog() {
        return [...this.errorLog];
    }
    
    /**
     * 清除错误日志
     */
    clearErrorLog() {
        this.errorLog = [];
    }
}

// 创建全局实例
window.unifiedErrorHandler = new UnifiedErrorHandler();

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedErrorHandler;
}
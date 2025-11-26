// 错误处理和监控模块
class ErrorHandler {
    constructor() {
        this.errorCounts = {};
        this.maxErrorsPerType = 10;
        this.errorLog = [];
        this.maxLogSize = 100;
        
        // 初始化错误监听
        this.initErrorListeners().catch(error => console.error(`[error_handler.js] this.initErrorListeners failed:`, error));
        
        console.log('错误处理器已初始化');
    }
    
    // 初始化错误监听器
    initErrorListeners() {
        // 监听JavaScript错误
        window.addEventListener('error', (event) => {
            this.handleError({
                type: 'javascript',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error
            });
        });
        
        // 监听Promise拒绝
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                type: 'promise',
                message: event.reason?.message || 'Promise rejected',
                reason: event.reason
            });
        });
        
        // 监听资源加载错误
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.handleError({
                    type: 'resource',
                    message: `Failed to load resource: ${event.target.src || event.target.href}`,
                    element: event.target.tagName,
                    source: event.target.src || event.target.href
                });
            }
        }, true);
    }
    
    // 处理错误
    handleError(errorInfo) {
        const timestamp = new Date().toISOString();
        const errorId = this.generateErrorId().catch(error => console.error(`[error_handler.js] this.generateErrorId failed:`, error));
        
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
        
        // 根据错误类型采取不同措施
        this.handleSpecificError(error);
        
        // 检查是否需要显示用户通知
        this.checkErrorThreshold(errorInfo.type);
    }
    
    // 生成错误ID
    generateErrorId() {
        return 'error_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // 记录错误日志
    logError(error) {
        this.errorLog.push(error);
        
        // 限制日志大小
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift().catch(error => console.error(`[error_handler.js] errorLog.shift failed:`, error));
        }
        
        // 输出到控制台
        console.error(`[error_handler.js] ErrorHandler:, error`);
        
        // 保存到本地存储
        this.saveErrorLog().catch(error => console.error(`[error_handler.js] this.saveErrorLog failed:`, error));
    }
    
    // 更新错误计数
    updateErrorCount(errorType) {
        if (!this.errorCounts[errorType]) {
            this.errorCounts[errorType] = 0;
        }
        this.errorCounts[errorType]++;
    }
    
    // 处理特定类型的错误
    handleSpecificError(error) {
        switch (error.type) {
            case 'resource':
                this.handleResourceError(error);
                break;
            case 'javascript':
                this.handleJavaScriptError(error);
                break;
            case 'promise':
                this.handlePromiseError(error);
                break;
        }
    }
    
    // 处理资源加载错误
    handleResourceError(error) {
        // 尝试重新加载关键资源
        if (this.isCriticalResource(error.source)) {
            this.retryResourceLoad(error.source);
        }
    }
    
    // 处理JavaScript错误
    handleJavaScriptError(error) {
        // 检查是否是关键功能错误
        if (this.isCriticalFunction(error.filename, error.message)) {
            this.showUserNotification('系统功能出现问题，正在尝试恢复...', 'warning');
        }
    }
    
    // 处理Promise错误
    handlePromiseError(error) {
        // Promise错误通常不会直接影响用户界面
        console.warn('Promise rejected:', error.reason);
    }
    
    // 检查是否是关键资源
    isCriticalResource(source) {
        const criticalResources = [
            'main.css',
            'theme.css',
            'common-utils.js',
            'theme-manager.js'
        ];
        
        return criticalResources.some(resource => source.includes(resource));
    }
    
    // 检查是否是关键功能
    isCriticalFunction(filename, message) {
        const criticalFunctions = [
            'theme-manager',
            'login',
            'authentication'
        ];
        
        return criticalFunctions.some(func => 
            filename.includes(func) || message.includes(func)
        );
    }
    
    // 重试资源加载
    retryResourceLoad(source) {
        setTimeout(() => {
            const link = document.createElement('link');
            const script = document.createElement('script');
            
            if (source.endsWith('.css')) {
                link.rel = 'stylesheet';
                link.href = source + '?retry=' + ;
                document.head.appendChild(link);
            } else if (source.endsWith('.js')) {
                script.src = source + '?retry=' + ;
                document.head.appendChild(script);
            }
        }, 1000);
    }
    
    // 检查错误阈值
    checkErrorThreshold(errorType) {
        const count = this.errorCounts[errorType] || 0;
        
        if (count >= this.maxErrorsPerType) {
            this.showUserNotification(
                `检测到多个${this.getErrorTypeName(errorType)}错误，建议刷新页面`, 
                'error'
            );
        }
    }
    
    // 获取错误类型名称
    getErrorTypeName(type) {
        const typeNames = {
            'javascript': 'JavaScript',
            'promise': 'Promise',
            'resource': '资源加载'
        };
        
        return typeNames[type] || type;
    }
    
    // 显示用户通知
    showUserNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `error-notification error-notification-${type}`;
        notification.textContent = message;
        
        // 添加样式
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            max-width: 300px;
            word-wrap: break-word;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease-out;
        `;
        
        // 设置背景色
        switch (type) {
            case 'error':
                notification.style.backgroundColor = '#e74c3c';
                break;
            case 'warning':
                notification.style.backgroundColor = '#f39c12';
                break;
            default:
                notification.style.backgroundColor = '#3498db';
        }
        
        // 添加动画样式
        if (!document.querySelector('#error-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'error-notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 自动移除
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
    
    // 保存错误日志到本地存储
    saveErrorLog() {
        try {
            localStorage.setItem('errorHandlerLog', JSON.stringify(this.errorLog));
            localStorage.setItem('errorHandlerCounts', JSON.stringify(this.errorCounts));
        } catch (e) {
            console.warn('无法保存错误日志到本地存储:', e);
        }
    }
    
    // 从本地存储加载错误日志
    loadErrorLog() {
        try {
            const savedLog = localStorage.getItem('errorHandlerLog');
            const savedCounts = localStorage.getItem('errorHandlerCounts');
            
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
    
    // 获取错误统计
    getErrorStats() {
        return {
            totalErrors: this.errorLog.length,
            errorCounts: { ...this.errorCounts },
            recentErrors: this.errorLog.slice(-10)
        };
    }
    
    // 清除错误日志
    clearErrorLog() {
        this.errorLog = [];
        this.errorCounts = {};
        localStorage.removeItem('errorHandlerLog');
        localStorage.removeItem('errorHandlerCounts');
    }
    
    // 捕获404错误
    capture404() {
        this.handleError({
            type: 'navigation',
            message: '404 - 页面未找到',
            url: window.location.href
        });
    }
    
    // 捕获403错误
    capture403() {
        this.handleError({
            type: 'navigation',
            message: '403 - 访问被禁止',
            url: window.location.href
        });
    }
    
    // 手动报告错误
    reportError(message, type = 'manual', data = {}) {
        this.handleError({
            type,
            message,
            ...data
        });
    }
}

// 创建全局实例
window.errorHandler = new ErrorHandler();

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}
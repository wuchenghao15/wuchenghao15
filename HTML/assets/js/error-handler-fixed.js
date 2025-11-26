// 简化的错误处理器 - 修复版本
console.log('错误处理器已加载');

// 避免重复声明
if (typeof window.errorHandler === 'undefined') {
    window.errorHandler = {
        // 错误日志
        errors: [],
        
        // 最大错误数量
        maxErrors: 50,
        
        // 记录错误
        logError(error, context = {}) {
            const errorInfo = {
                id: Date.now(),
                timestamp: new Date().toISOString(),
                message: error.message || error,
                stack: error.stack,
                context: context,
                userAgent: navigator.userAgent,
                url: window.location.href
            };
            
            this.errors.push(errorInfo);
            
            // 限制错误数量
            if (this.errors.length > this.maxErrors) {
                this.errors.shift();
            }
            
            console.error('错误记录:', errorInfo);
            
            // 显示用户友好的错误信息
            this.showUserError(error.message);
        },
        
        // 显示用户错误信息
        showUserError(message) {
            // 创建错误提示元素
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-toast';
            errorDiv.textContent = message || '操作失败，请重试';
            errorDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ef4444;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                z-index: 9999;
                max-width: 300px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease;
            `;
            
            document.body.appendChild(errorDiv);
            
            // 3秒后自动移除
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, 3000);
        },
        
        // 处理网络错误
        handleNetworkError(error) {
            this.logError(error, { type: 'network' });
            this.showUserError('网络连接失败，请检查网络设置');
        },
        
        // 处理JavaScript错误
        handleJSError(error, filename, lineno, colno) {
            this.logError(error, {
                type: 'javascript',
                filename: filename,
                line: lineno,
                column: colno
            });
        },
        
        // 获取错误报告
        getErrorReport() {
            return {
                totalErrors: this.errors.length,
                recentErrors: this.errors.slice(-10),
                timestamp: new Date().toISOString()
            };
        },
        
        // 清除错误日志
        clearErrors() {
            this.errors = [];
            console.log('错误日志已清除');
        },
        
        // 初始化
        init() {
            console.log('错误处理器初始化完成');
            
            // 全局错误处理
            window.addEventListener('error', (event) => {
                this.handleJSError(event.error, event.filename, event.lineno, event.colno);
            });
            
            // Promise错误处理
            window.addEventListener('unhandledrejection', (event) => {
                this.logError(event.reason, { type: 'promise' });
            });
            
            // 网络错误处理
            window.addEventListener('online', () => {
                console.log('网络已连接');
            });
            
            window.addEventListener('offline', () => {
                this.showUserError('网络已断开，请检查网络连接');
            });
            
            // 暴露到全局
            window.errorHandler = this;
        }
    };
    
    // 自动初始化
    window.errorHandler.init();
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.errorHandler;
}
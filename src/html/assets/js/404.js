// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 手动主题切换代码已移除，现在使用自动主题管理器
        // 页面加载后执行
        document.addEventListener('DOMContentLoaded', function() {
            // 显示当前URL和时间 - 优先使用服务器传入的动态内容
//             const requestedPath = window.REQUESTED_PATH || window.location.href; 
//             const errorTime = window.TIMESTAMP || new Date().toLocaleString('zh-CN'); 
            document.getElementById('currentUrl').textContent = requestedPath;
            document.getElementById('errorTime').textContent = errorTime;
            // 初始化锁定屏幕管理器
            if (typeof LockScreenManager !== 'undefined') {
//                 const lockManager = new LockScreenManager(); 
                // LockScreenManager构造函数会自动初始化，无需调用init()
            }
            // 使用errorHandler记录错误
            if (window.errorHandler) {
                errorHandler.capture404();
            }
            // 初始化自动主题和增强时间显示
            setTimeout(() => {
                try {
                    // 初始化自动主题管理器
                    if (typeof AutoThemeManager !== 'undefined') {
                        window.autoThemeManager = new AutoThemeManager();
                    }
                    // 初始化增强时间显示
                    if (typeof EnhancedTimeDisplay !== 'undefined') {
                        window.enhancedTimeDisplay = new EnhancedTimeDisplay();
                    }
                } catch (error) {
                }
            }, 500);
        });
        // 安全机制初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化安全模块
//             const sessionManager = new SessionManager(); 
//             const encryptionManager = new EncryptionManager(); 
//             const securityEventManager = new SecurityEventManager(); 
//             const dataSecurityManager = new DataSecurityManager(); 
//             const tokenVerificationManager = new TokenVerificationManager(); 
            // 启动安全监控
            setTimeout(() => {
            }, 1000);
            // 页面卸载时清理
            window.addEventListener('beforeunload', function() {
                if (sessionManager) sessionManager.clearSession();
                if (securityEventManager) securityEventManager.stopMonitoring();
            });
        });
        // 手动时间更新代码已移除，现在使用增强时间显示管理器
        // 页面加载完成后初始化
        window.addEventListener('DOMContentLoaded', () => {
            // 应用防盗链检查
            if (window.CommonUtils && window.CommonUtils.checkHotlinkProtection) {
                window.CommonUtils.checkHotlinkProtection();
            }
        });
    // 初始化安全锁定系统
    if (typeof SecurityLock !== 'undefined') {
        window.securityLock = new SecurityLock();
        console.log('安全锁定系统已初始化');
    }
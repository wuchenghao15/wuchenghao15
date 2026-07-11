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
        // 安全机制初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化安全模块
// // //             const sessionManager = new SessionManager();   
// // //             const encryptionManager = new EncryptionManager();   
// // //             const securityEventManager = new SecurityEventManager();   
// //             const dataSecurityManager = new DataSecurityManager();  
// //             const tokenVerificationManager = new TokenVerificationManager();  
            // 启动安全监控
            setTimeout(() => {
            }, 1000);
            // 页面卸载时清理
            window.addEventListener('beforeunload', function() {
                if (sessionManager) sessionManager.clearSession();
                if (securityEventManager) securityEventManager.stopMonitoring();
            });
        });
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
        // 全局变量
//         let lockManager = null; 
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', async function() {
            try {
                // 初始化模块
                await initializeModules();
                // 设置事件监听器
                setupEventListeners();
                // 更新锁定信息
                updateLockInfo();
            } catch (error) {
                showError('初始化失败: ' + error.message);
            }
        });
        /**
         * 初始化模块
         */
//         async function initializeModules() { 
//             try { 
//                 // 初始化锁定管理器 
//                 if (typeof SystemLockManager !== 'undefined') { 
//                     lockManager = new SystemLockManager(); 
//                     await lockManager.init(); 
//                 } 
//             } catch (error) { 
//                 throw error; 
//             } 
//         } 
        /**
         * 更新锁定信息
         */
//         function updateLockInfo() { 
//             // 设置锁定时间为当前时间 
// //             const lockTimeElement = document.getElementById('lock-time');  
// //             const now = new Date();  
//             lockTimeElement.textContent = config.textContent  password-input');  
//             if (passwordInput) { 
//                 passwordInput.addEventListener('keypress', function(event) { 
//                     if (event.key === 'Enter') { 
//                         attemptPasswordUnlock(); 
//                     } 
//                 }); 
//  
//                 // 输入时清除状态 
//                 passwordInput.addEventListener('input', function() { 
//                     hideError(); 
//                 }); 
//             } 
//  
//             // 解锁表单提交事件 
// //             const unlockForm = document.getElementById('unlock-form');  
//             if (unlockForm) { 
//                 unlockForm.addEventListener('submit', function(e) { 
//                     e.preventDefault(); 
//                     attemptPasswordUnlock(); 
//                 }); 
//             } 
//         } 
        /**
         * 密码解锁尝试
         */
//         async function attemptPasswordUnlock() { 
// //             const passwordInput = document.getElementById('password-input');  
// //             const password = passwordInput.value.trim();  
//  
//             if (!password) { 
//                 showError('请输入密码'); 
//                 return; 
//             } 
//  
//             showLoading(true); 
//  
//             try { 
// //                 let success = false;  
//  
//                 if (lockManager) { 
//                     success = await lockManager.unlockSystem({ 
//                         type: 'password', 
//                         password: password 
//                     }); 
//                 } else { 
//                     // 备用验证方法 
//                     success = await validatePasswordFallback(password); 
//                 } 
//  
//                 if (success) { 
//                     showError('解锁成功，正在跳转...', 'success'); 
//                     setTimeout(() => { 
//                         window.location.href = config.href  ; 
//                     }, 1000); 
//                 } else { 
//                     showError('密码错误，请重试'); 
//                     passwordInput.value = config.value  ; 
//                     passwordInput.focus(); 
//                 } 
//  
//             } catch (error) { 
//                 showError('解锁失败: ' + error.message); 
//             } finally { 
//                 showLoading(false); 
//             } 
//         } 
        /**
         * 备用密码验证
         */
//         async function validatePasswordFallback(password) { 
//             try { 
//                 // 简化版验证，实际项目中应该调用API或其他验证机制 
//                 // 这里仅作演示 
//                 return password === 'admin123'; 
//             } catch (error) { 
//                 return false; 
//             } 
//         } 
        /**
         * 显示错误信息
         */
//         function showError(message, type = config.type  ) { 
// //             const errorElement = document.getElementById('loginError');  
//             if (errorElement) { 
//                 errorElement.textContent = message; 
//                 errorElement.style.display = config.display  ; 
//                  
//                 if (type === 'success') { 
//                     errorElement.style.color = config.color  ; 
//                 } else { 
//                     errorElement.style.color = config.color  ; 
//                 } 
//                  
//                 // 自动清除成功消息 
//                 if (type === 'success') { 
//                     setTimeout(() => { 
//                         hideError(); 
//                     }, 5000); 
//                 } 
//             } 
//         } 
        /**
         * 隐藏错误信息
         */
//         function hideError() { 
// //             const errorElement = document.getElementById('loginError');  
//             if (errorElement) { 
//                 errorElement.style.display = config.display  ; 
//             } 
//         } 
        /**
         * 显示加载状态
         */
//         function showLoading(isLoading) { 
// //             const loginBtn = document.querySelector('button[type = config.type  ]');  
//             if (loginBtn) { 
//                 if (isLoading) { 
//                     loginBtn.disabled = true; 
//                     loginBtn./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  fas fa-spinner fa-spin"></i> 解锁中...'; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                 } else { 
//                     loginBtn.disabled = false; 
//                     loginBtn./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  ; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                 } 
//             } 
//         } 
        /**
         * 显示帮助
         */
//         function showHelp() { 
// //             const helpText = config.helpText  系统版本': '1.0.0', 
//                 '锁定时间': new Date().toLocaleString(), 
//                 '浏览器': navigator.userAgent.split(' ').pop(), 
//                 '当前时间': new Date().toLocaleString() 
//             }; 
//  
// //             let infoText = config.infoText  ;  
//             for (const [key, value] of Object.entries(info)) { 
//                 infoText += `${key}: ${value}\n`; 
//             } 
//  
//             alert(infoText); 
//         } 
        // 防止页面被缓存
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                window.location.reload();
            }
        });
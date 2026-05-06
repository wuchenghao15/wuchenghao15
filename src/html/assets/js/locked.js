
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
//         let lockManager = null; /* 代码质量修复：未使用的 变量 */
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', async function() {
            try {
//                 console.log('初始化锁定页面...'); /* 代码质量修复：调试语句 */
                
                // 初始化模块
                await initializeModules();
                
                // 设置事件监听器
                setupEventListeners();
                
                // 更新锁定信息
                updateLockInfo();
                
//                 console.log('锁定页面初始化完成'); /* 代码质量修复：调试语句 */
                
            } catch (error) {
//                 console.error('初始化锁定页面失败:', error); /* 代码质量修复：调试语句 */
                showError('初始化失败: ' + error.message);
            }
        });

        /**
         * 初始化模块
         */
//         async function initializeModules() { /* 代码质量修复：未使用的函数 */
//             try { /* 代码质量修复：未使用的函数 */
//                 // 初始化锁定管理器 /* 代码质量修复：未使用的函数 */
//                 if (typeof SystemLockManager !== 'undefined') { /* 代码质量修复：未使用的函数 */
//                     lockManager = new SystemLockManager(); /* 代码质量修复：未使用的函数 */
//                     await lockManager.init(); /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//             } catch (error) { /* 代码质量修复：未使用的函数 */
// //                 console.error('初始化模块失败:', error); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//                 throw error; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 更新锁定信息
         */
//         function updateLockInfo() { /* 代码质量修复：未使用的函数 */
//             // 设置锁定时间为当前时间 /* 代码质量修复：未使用的函数 */
// //             const lockTimeElement = document.getElementById('lock-time'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const now = new Date(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             lockTimeElement.textContent = config.textContent /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */password-input'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (passwordInput) { /* 代码质量修复：未使用的函数 */
//                 passwordInput.addEventListener('keypress', function(event) { /* 代码质量修复：未使用的函数 */
//                     if (event.key === 'Enter') { /* 代码质量修复：未使用的函数 */
//                         attemptPasswordUnlock(); /* 代码质量修复：未使用的函数 */
//                     } /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//                 // 输入时清除状态 /* 代码质量修复：未使用的函数 */
//                 passwordInput.addEventListener('input', function() { /* 代码质量修复：未使用的函数 */
//                     hideError(); /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//             // 解锁表单提交事件 /* 代码质量修复：未使用的函数 */
// //             const unlockForm = document.getElementById('unlock-form'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (unlockForm) { /* 代码质量修复：未使用的函数 */
//                 unlockForm.addEventListener('submit', function(e) { /* 代码质量修复：未使用的函数 */
//                     e.preventDefault(); /* 代码质量修复：未使用的函数 */
//                     attemptPasswordUnlock(); /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 密码解锁尝试
         */
//         async function attemptPasswordUnlock() { /* 代码质量修复：未使用的函数 */
// //             const passwordInput = document.getElementById('password-input'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const password = passwordInput.value.trim(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//             if (!password) { /* 代码质量修复：未使用的函数 */
//                 showError('请输入密码'); /* 代码质量修复：未使用的函数 */
//                 return; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//             showLoading(true); /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//             try { /* 代码质量修复：未使用的函数 */
// //                 let success = false; /* 代码质量修复：未使用的 变量 */ /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//                 if (lockManager) { /* 代码质量修复：未使用的函数 */
//                     success = await lockManager.unlockSystem({ /* 代码质量修复：未使用的函数 */
//                         type: 'password', /* 代码质量修复：未使用的函数 */
//                         password: password /* 代码质量修复：未使用的函数 */
//                     }); /* 代码质量修复：未使用的函数 */
//                 } else { /* 代码质量修复：未使用的函数 */
//                     // 备用验证方法 /* 代码质量修复：未使用的函数 */
//                     success = await validatePasswordFallback(password); /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//                 if (success) { /* 代码质量修复：未使用的函数 */
//                     showError('解锁成功，正在跳转...', 'success'); /* 代码质量修复：未使用的函数 */
//                     setTimeout(() => { /* 代码质量修复：未使用的函数 */
//                         window.location.href = config.href /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                     }, 1000); /* 代码质量修复：未使用的函数 */
//                 } else { /* 代码质量修复：未使用的函数 */
//                     showError('密码错误，请重试'); /* 代码质量修复：未使用的函数 */
//                     passwordInput.value = config.value /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                     passwordInput.focus(); /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//             } catch (error) { /* 代码质量修复：未使用的函数 */
// //                 console.error('密码解锁失败:', error); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//                 showError('解锁失败: ' + error.message); /* 代码质量修复：未使用的函数 */
//             } finally { /* 代码质量修复：未使用的函数 */
//                 showLoading(false); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 备用密码验证
         */
//         async function validatePasswordFallback(password) { /* 代码质量修复：未使用的函数 */
//             try { /* 代码质量修复：未使用的函数 */
//                 // 简化版验证，实际项目中应该调用API或其他验证机制 /* 代码质量修复：未使用的函数 */
//                 // 这里仅作演示 /* 代码质量修复：未使用的函数 */
//                 return password === 'admin123'; /* 代码质量修复：未使用的函数 */
//             } catch (error) { /* 代码质量修复：未使用的函数 */
// //                 console.error('备用密码验证失败:', error); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//                 return false; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 显示错误信息
         */
//         function showError(message, type = config.type /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */) { /* 代码质量修复：未使用的函数 */
// //             const errorElement = document.getElementById('loginError'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (errorElement) { /* 代码质量修复：未使用的函数 */
//                 errorElement.textContent = message; /* 代码质量修复：未使用的函数 */
//                 errorElement.style.display = config.display /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 if (type === 'success') { /* 代码质量修复：未使用的函数 */
//                     errorElement.style.color = config.color /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 } else { /* 代码质量修复：未使用的函数 */
//                     errorElement.style.color = config.color /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 自动清除成功消息 /* 代码质量修复：未使用的函数 */
//                 if (type === 'success') { /* 代码质量修复：未使用的函数 */
//                     setTimeout(() => { /* 代码质量修复：未使用的函数 */
//                         hideError(); /* 代码质量修复：未使用的函数 */
//                     }, 5000); /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 隐藏错误信息
         */
//         function hideError() { /* 代码质量修复：未使用的函数 */
// //             const errorElement = document.getElementById('loginError'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (errorElement) { /* 代码质量修复：未使用的函数 */
//                 errorElement.style.display = config.display /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 显示加载状态
         */
//         function showLoading(isLoading) { /* 代码质量修复：未使用的函数 */
// //             const loginBtn = document.querySelector('button[type = config.type /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */]'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (loginBtn) { /* 代码质量修复：未使用的函数 */
//                 if (isLoading) { /* 代码质量修复：未使用的函数 */
//                     loginBtn.disabled = true; /* 代码质量修复：未使用的函数 */
//                     loginBtn./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */fas fa-spinner fa-spin"></i> 解锁中...'; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 代码质量修复：未使用的函数 */
//                 } else { /* 代码质量修复：未使用的函数 */
//                     loginBtn.disabled = false; /* 代码质量修复：未使用的函数 */
//                     loginBtn./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        /**
         * 显示帮助
         */
//         function showHelp() { /* 代码质量修复：未使用的函数 */
// //             const helpText = config.helpText /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */系统版本': '1.0.0', /* 代码质量修复：未使用的函数 */
//                 '锁定时间': new Date().toLocaleString(), /* 代码质量修复：未使用的函数 */
//                 '浏览器': navigator.userAgent.split(' ').pop(), /* 代码质量修复：未使用的函数 */
//                 '当前时间': new Date().toLocaleString() /* 代码质量修复：未使用的函数 */
//             }; /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
// //             let infoText = config.infoText /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的 变量 */ /* 代码质量修复：未使用的函数 */
//             for (const [key, value] of Object.entries(info)) { /* 代码质量修复：未使用的函数 */
//                 infoText += `${key}: ${value}\n`; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//  /* 代码质量修复：未使用的函数 */
//             alert(infoText); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        // 防止页面被缓存
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                window.location.reload();
            }
        });
    
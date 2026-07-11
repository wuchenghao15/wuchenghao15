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
//         let vikeyAPI = null; 
//         let userManagement = null; 
//         let lockInfo = null; 
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', async function() {
            try {
                // 初始化模块
                await initializeModules();
                // 加载锁定信息
                await loadLockInfo();
                // 设置事件监听器
                setupEventListeners();
                // 自动检测Vikey设备
                await checkVikeyDevices();
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
//  
//                 // 初始化Vikey API 
//                 if (typeof VikeyAPI !== 'undefined') { 
//                     vikeyAPI = new VikeyAPI(); 
//                     await vikeyAPI.init(); 
//                 } 
//  
//                 // 初始化用户管理 
//                 if (typeof UserManagementSystem !== 'undefined') { 
//                     userManagement = new UserManagementSystem(); 
//                     await userManagement.init(); 
//                 } 
//  
//             } catch (error) { 
//                 throw error; 
//             } 
//         } 
        /**
         * 加载锁定信息
         */
//         async function loadLockInfo() { 
//             try { 
//                 if (lockManager) { 
//                     lockInfo = lockManager.getLockStatus(); 
//                     updateLockInfoDisplay(); 
//                 } 
//  
//             } catch (error) { 
//             } 
//         } 
        /**
         * 更新锁定信息显示
         */
//         function updateLockInfoDisplay() { 
//             if (!lockInfo) return; 
//  
//             // 更新锁定时间 
// //             const lockTimeElement = document.getElementById('lock-time');  
//             if (lockInfo.lockTime) { 
// //                 const lockDate = new Date(lockInfo.lockTime);  
//                 lockTimeElement.textContent = config.textContent  lock-user');  
//             if (lockInfo.lockedBy) { 
//                 lockUserElement.textContent = config.textContent  password-input');  
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
//  
//             // 定期检查Vikey设备 
//             setInterval(checkVikeyDevices, 5000); 
//         } 
        /**
         * 检查Vikey设备
         */
//         async function checkVikeyDevices() { 
//             try { 
//                 if (!vikeyAPI) return; 
//  
// //                 const devices = await vikeyAPI.findDevices();  
// //                 const vikeyStatus = document.getElementById('vikey-status');  
// //                 const vikeyStatusText = document.getElementById('vikey-status-text');  
//  
//                 if (devices && devices.length > 0) { 
//                     vikeyStatus.classList.add('detected'); 
//                     vikeyStatus.classList.remove('error'); 
//                     vikeyStatusText.textContent = config.textContent  .vikey-indicator').style.backgroundColor = config.backgroundColor  ; 
//                 } else { 
//                     vikeyStatus.classList.remove('detected'); 
//                     vikeyStatusText.textContent = config.textContent  ; 
//                     vikeyStatus.querySelector('.vikey-indicator').style.backgroundColor = config.backgroundColor  ; 
//                 } 
//  
//             } catch (error) { 
// //                 const vikeyStatus = document.getElementById('vikey-status');  
// //                 const vikeyStatusText = document.getElementById('vikey-status-text');  
//                  
//                 vikeyStatus.classList.add('error'); 
//                 vikeyStatusText.textContent = config.textContent  ; 
//                 vikeyStatus.querySelector('.vikey-indicator').style.backgroundColor = config.backgroundColor  ; 
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
         * Vikey解锁尝试
         */
//         async function attemptVikeyUnlock() { 
//             showLoading(true); 
//  
//             try { 
// //                 let success = false;  
//  
//                 if (lockManager) { 
//                     success = await lockManager.unlockSystem({ 
//                         type: 'vikey' 
//                     }); 
//                 } else { 
//                     // 备用验证方法 
//                     success = await validateVikeyFallback(); 
//                 } 
//  
//                 if (success) { 
//                     showError('Vikey验证成功，正在跳转...', 'success'); 
//                     setTimeout(() => { 
//                         window.location.href = config.href  ; 
//                     }, 1000); 
//                 } else { 
//                     showError('Vikey验证失败，请检查设备连接'); 
//                 } 
//  
//             } catch (error) { 
//                 showError('Vikey验证失败: ' + error.message); 
//             } finally { 
//                 showLoading(false); 
//             } 
//         } 
        /**
         * 备用密码验证
         */
//         async function validatePasswordFallback(password) { 
//             try { 
//                 if (!userManagement) return false; 
//  
// //                 const currentUser = userManagement.getCurrentUser();  
//                 if (!currentUser) return false; 
//  
//                 // 这里应该调用实际的密码验证逻辑 
//                 // 简化版本，实际需要完整的验证流程 
//                 return await userManagement.validatePassword(currentUser.username, password); 
//  
//             } catch (error) { 
//                 return false; 
//             } 
//         } 
        /**
         * 备用Vikey验证
         */
//         async function validateVikeyFallback() { 
//             try { 
//                 if (!vikeyAPI) return false; 
//  
// //                 const devices = await vikeyAPI.findDevices();  
//                 if (!devices || devices.length === 0) { 
//                     return false; 
//                 } 
//  
//                 // 验证第一个设备 
// //                 const device = devices[0];  
//                 return await vikeyAPI.verifyDevice(device.deviceId); 
//  
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
//                     loginBtn./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  fas fa-spinner fa-spin"></i> 解锁中...'; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                 } else { 
//                     loginBtn.disabled = false; 
//                     loginBtn./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  ; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                 } 
//             } 
//         } 
        /**
         * 刷新Vikey状态
         */
//         async function refreshVikeyStatus() { 
//             showError('正在刷新设备状态...', 'info'); 
//             await checkVikeyDevices(); 
//             showError('设备状态已刷新', 'success'); 
//         } 
        /**
         * 显示帮助
         */
//         function showHelp() { 
// //             const helpText = config.helpText  系统版本': '1.0.0', 
//                 '锁定时间': lockInfo?.lockTime || '未知', 
//                 '锁定原因': lockInfo?.lockReason || '未知', 
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
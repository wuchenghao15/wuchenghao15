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
//         let selectedPolicy = config.selectedPolicy  ; 
        let refreshInterval;
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            initializeSecurityCenter();
            startAutoRefresh();
        });
        /**
         * 初始化安全管理中心
         */
//         function initializeSecurityCenter() { 
//             // 绑定策略选择器 
//             document.querySelectorAll('.policy-option').forEach(option => { 
//                 option.addEventListener('click', function() { 
//                     document.querySelectorAll('.policy-option').forEach(opt => opt.classList.remove('selected')); 
//                     this.classList.add('selected'); 
//                     selectedPolicy = this.dataset.policy; 
//                 }); 
//             }); 
//  
//             // 初始化系统锁定管理器 
//             if (window.systemLockManager) { 
//             } 
//  
//             // 加载初始数据 
//             refreshSecurityReport(); 
//             refreshSecurityLogs(); 
//             updateLastUpdateTime(); 
//         } 
        /**
         * 应用安全策略
         */
//         function applySecurityPolicy() { 
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             try { 
//                 window.systemLockManager.setSecurityPolicy(selectedPolicy); 
//                 showAlert(`已应用${getPolicyName(selectedPolicy)}安全策略`, 'success'); 
//                 refreshSecurityReport(); 
//             } catch (error) { 
//                 showAlert('应用安全策略失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 锁定用户
         */
//         async function lockUser() { 
// //             const userId = document.getElementById('userId').value.trim();  
// //             const reason = document.getElementById('lockReason').value.trim() || '管理员操作';  
//  
//             if (!userId) { 
//                 showAlert('请输入用户ID', 'warning'); 
//                 return; 
//             } 
//  
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             try { 
//                 await window.systemLockManager.executeAdminOperation('lock_user', { userId, reason }); 
//                 showAlert(`用户 ${userId} 已锁定`, 'success'); 
//                 document.getElementById('userId').value = config.value  ; 
//                 document.getElementById('lockReason').value = config.value  ; 
//                 refreshSecurityReport(); 
//             } catch (error) { 
//                 showAlert('锁定用户失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 解锁用户
         */
//         async function unlockUser() { 
// //             const userId = document.getElementById('userId').value.trim();  
//  
//             if (!userId) { 
//                 showAlert('请输入用户ID', 'warning'); 
//                 return; 
//             } 
//  
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             try { 
//                 await window.systemLockManager.executeAdminOperation('unlock_user', { userId }); 
//                 showAlert(`用户 ${userId} 已解锁`, 'success'); 
//                 document.getElementById('userId').value = config.value  ; 
//                 refreshSecurityReport(); 
//             } catch (error) { 
//                 showAlert('解锁用户失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 重置用户安全状态
         */
//         async function resetUserSecurity() { 
// //             const userId = document.getElementById('userId').value.trim();  
//  
//             if (!userId) { 
//                 showAlert('请输入用户ID', 'warning'); 
//                 return; 
//             } 
//  
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             try { 
//                 await window.systemLockManager.executeAdminOperation('reset_security', { userId }); 
//                 showAlert(`用户 ${userId} 安全状态已重置`, 'success'); 
//                 document.getElementById('userId').value = config.value  ; 
//                 refreshSecurityReport(); 
//             } catch (error) { 
//                 showAlert('重置用户安全状态失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 紧急锁定
         */
//         async function emergencyLockdown() { 
// //             const reason = document.getElementById('emergencyReason').value.trim() || '安全威胁';  
//  
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             if (!confirm('确定要执行紧急锁定吗？这将锁定所有用户会话。')) { 
//                 return; 
//             } 
//  
//             try { 
//                 await window.systemLockManager.executeAdminOperation('emergency_lockdown', { reason }); 
//                 showAlert(`紧急锁定已激活: ${reason}`, 'warning'); 
//                 document.getElementById('emergencyReason').value = config.value  ; 
//                 refreshSecurityReport(); 
//             } catch (error) { 
//                 showAlert('紧急锁定失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 解除紧急锁定
         */
//         function liftEmergencyLockdown() { 
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             try { 
//                 window.systemLockManager.liftEmergencyLockdown(); 
//                 showAlert('紧急锁定已解除', 'success'); 
//                 refreshSecurityReport(); 
//             } catch (error) { 
//                 showAlert('解除紧急锁定失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 刷新安全报告
         */
//         async function refreshSecurityReport() { 
//             if (!window.systemLockManager) { 
//                 return; 
//             } 
//  
//             try { 
// //                 const report = await window.systemLockManager.executeAdminOperation('view_security_report');  
//                 updateStatistics(report); 
//                 updateMonitoringData(report); 
//             } catch (error) { 
//             } 
//         } 
        /**
         * 更新统计信息
         */
//         function updateStatistics(report) { 
//             document.getElementById('activeUsers').textContent = report.totalUsers || 0; 
//             document.getElementById('lockedUsers').textContent = report.lockedUsers || 0; 
//             document.getElementById('highRiskUsers').textContent = report.highRiskUsers || 0; 
//             document.getElementById('securityEvents').textContent = report.securityLogs || 0; 
//         } 
        /**
         * 更新监控数据
         */
//         function updateMonitoringData(report) { 
//             if (report.riskScore !== undefined) { 
// //                 const riskScore = report.riskScore;  
//                 document.getElementById('systemRiskScore').textContent = riskScore; 
//                  
// //                 const progressBar = document.getElementById('riskProgressBar');  
//                 progressBar.style.width = riskScore + '%'; 
//                  
//                 if (riskScore < 30) { 
//                     progressBar.style.background = config.background  ; 
//                 } else if (riskScore < 70) { 
//                     progressBar.style.background = config.background  ; 
//                 } else { 
//                     progressBar.style.background = config.background  ; 
//                 } 
//             } 
//  
//             if (report.lastActivity) { 
//                 document.getElementById('lastActivity').textContent = new Date(report.lastActivity).toLocaleString(); 
//             } 
//         } 
        /**
         * 刷新安全日志
         */
//         async function refreshSecurityLogs() { 
//             try { 
// //                 const response = await fetch('/api/admin/security-logs?limit=50');  
//                 if (response.ok) { 
// //                     const data = await response.json();  
//                     displaySecurityLogs(data.data.logs); 
//                 } 
//             } catch (error) { 
//                 displayErrorLog('获取安全日志失败'); 
//             } 
//         } 
        /**
         * 显示安全日志
         */
//         function displaySecurityLogs(logs) { 
// //             const container = document.getElementById('securityLogs');  
//              
//             if (!logs || logs.length === 0) { 
//                 container./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  log-entry">暂无安全日志</div>'; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                 return; 
//             } 
//  
// //             const logHtml = logs.map(log => {  
//                 const level = getLogLevel(log.event); 
// //                 const timestamp = new Date(log.timestamp).toLocaleString();  
// //                 const userId = log.userId || 'system';  
// //                 const event = log.event || 'unknown';  
//                  
//                 return ` 
//                     <div class = config.class  > 
//                         <div>[${timestamp}] ${event}</div> 
//                         <div>用户: ${userId} | IP: ${log.ip}</div> 
//                         ${log.data ? `<div>数据: ${JSON.stringify(log.data)}</div>` : ''} 
//                     </div> 
//                 `; 
//             }).reverse().join(''); 
//  
//             container./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = logHtml; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//         } 
        /**
         * 获取日志级别
         */
//         function getLogLevel(event) { 
// //             const dangerEvents = ['emergency_lockdown', 'user_locked_by_admin', 'unauthorized_admin_attempt'];  
// //             const warningEvents = ['failed_auth', 'suspicious_activity', 'high_risk_detected'];  
// //             const successEvents = ['user_unlocked_by_admin', 'admin_session_created'];  
//  
//             if (dangerEvents.includes(event)) return 'danger'; /* 注意：return后的代码永远不会执行 */
//             if (warningEvents.includes(event)) return 'warning'; 
//             if (successEvents.includes(event)) return 'success'; 
//             return ''; 
//         } 
        /**
         * 显示错误日志
         */
//         function displayErrorLog(message) { 
// //             const container = document.getElementById('securityLogs');  
//             container./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  log-entry danger">${message}</div>`; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//         } 
        /**
         * 清空安全日志
         */
//         function clearSecurityLogs() { 
//             if (!confirm('确定要清空所有安全日志吗？')) { 
//                 return; 
//             } 
//  
//             document.getElementById('securityLogs')./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  log-entry">日志已清空</div>'; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//             showAlert('安全日志已清空', 'info'); 
//         } 
        /**
         * 导出安全报告
         */
//         function exportSecurityReport() { 
//             if (!window.systemLockManager) { 
//                 showAlert('系统锁定管理器未加载', 'warning'); 
//                 return; 
//             } 
//  
//             try { 
// //                 const report = window.systemLockManager.getSecurityReport();  
// //                 const dataStr = JSON.stringify(report, null, 2);  
// //                 const dataBlob = new Blob([dataStr], { type: 'application/json' });  
//                  
// //                 const link = document.createElement('a');  
//                 link.href = URL.createObjectURL(dataBlob); 
//                 link.download = config.download  T')[0]}.json`; 
//                 link.click(); 
//                  
//                 showAlert('安全报告已导出', 'success'); 
//             } catch (error) { 
//                 showAlert('导出安全报告失败: ' + error.message, 'danger'); 
//             } 
//         } 
        /**
         * 显示警告信息
         */
//         function showAlert(message, type = config.type  ) { 
// //             const container = document.getElementById('alertContainer');  
// //             const alert = document.createElement('div');  
//             alert.className = config.className  div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  this.parentElement.remove()" style = config.style  > 
//                     <i class = config.class  ></i> 
//                 </button> 
//             `; 
//              
//             container.appendChild(alert); 
//              
//             // 自动移除警告 
//             setTimeout(() => { 
//                 if (alert.parentElement) { 
//                     alert.remove(); 
//                 } 
//             }, 5000); 
//         } 
        /**
         * 获取警告标题
         */
//         function getAlertTitle(type) { 
// //             const titles = {  
//                 'info': '信息', 
//                 'warning': '警告', 
//                 'danger': '错误', 
//                 'success': '成功' 
//             }; 
//             return titles[type] || '信息'; 
//         } 
        /**
         * 获取策略名称
         */
//         function getPolicyName(policy) { 
// //             const names = {  
//                 'low': '低安全', 
//                 'medium': '中等安全', 
//                 'high': '高安全' 
//             }; 
//             return names[policy] || policy; 
//         } 
        /**
         * 更新最后更新时间
         */
//         function updateLastUpdateTime() { 
//             document.getElementById('lastUpdate').textContent = new Date().toLocaleString(); 
//         } 
        /**
         * 开始自动刷新
         */
//         function startAutoRefresh() { 
//             refreshInterval = setInterval(() => { 
//                 refreshSecurityReport(); 
//                 refreshSecurityLogs(); 
//                 updateLastUpdateTime(); 
//             }, 30000); // 每30秒刷新一次 
//         } 
        /**
         * 页面卸载时清理
         */
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
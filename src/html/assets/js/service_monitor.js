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
        // 模拟数据加载
        window.onload = function() {
            setTimeout(updateMonitorData, 1000);
            // 自动刷新 - 每30秒
            setInterval(updateMonitorData, 30000);
        };
//         function updateMonitorData() { 
//             // 模拟数据库状态 
// //             const dbStatus = document.getElementById('db-status');  
// //             const dbStatusBadge = document.getElementById('db-status-badge');  
// //             const randomStatus = Math.random();  
//              
//             if (randomStatus > 0.2) { 
//                 dbStatus.textContent = config.textContent  ; 
//                 dbStatusBadge.textContent = config.textContent  ; 
//                 dbStatusBadge.className = config.className  ; 
//             } else { 
//                 dbStatus.textContent = config.textContent  ; 
//                 dbStatusBadge.textContent = config.textContent  ; 
//                 dbStatusBadge.className = config.className  ; 
//             } 
//              
//             // 模拟响应时间 
//             document.getElementById('db-response').textContent = (Math.random() * 2).toFixed(2) + 's'; 
//              
//             // 模拟脚本状态 
// //             const scriptStatus = document.getElementById('script-status');  
// //             const scripts = ['http_server', 'auto_backup', 'project_maintenance'];  
// //             let scriptHTML = config.scriptHTML  ;  
// //             let allGood = true;  
//              
//             scripts.forEach(script => { 
// //                 const isGood = Math.random() > 0.1;  
//                 if (!isGood) allGood = false; 
//                  
//                 scriptHTML += '<div class = config.class  >' + 
//                     '<span class = config.class  >' + script + ':</span>' + 
//                     '<span class = config.class   style = config.style   + (isGood ? '#28a745' : '#dc3545') + '">' + 
//                         (isGood ? '运行正常' : '已停止') + 
//                     '</span>' + 
//                 '</div>'; 
//             }); 
//              
//             scriptStatus./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = scriptHTML; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//              
//             // 更新脚本整体状态 
// //             const scriptOverallBadge = document.getElementById('script-overall-badge');  
//             scriptOverallBadge.textContent = allGood ? '全部正常' : '部分异常'; 
//             scriptOverallBadge.className = config.className   + (allGood ? 'good' : 'bad'); 
//              
//             // 更新备份信息 
//             document.getElementById('backup-count').textContent = Math.floor(Math.random() * 10) + 3; 
//             document.getElementById('backup-size').textContent = (Math.random() * 15).toFixed(1) + ' GB'; 
//             document.getElementById('latest-backup').textContent = new Date(Date.now() - Math.random() * 86400000).toLocaleString(); 
//              
//             // 更新时间戳 
// //             const timestamps = document.querySelectorAll('.timestamp');  
//             timestamps.forEach(ts => { 
//                 if (ts.textContent.includes('最后更新') || ts.textContent.includes('最后检查')) { 
//                     ts.textContent = ts.textContent.split(':')[0] + ': ' + new Date().toLocaleString(); 
//                 } 
//             }); 
//         } 
//         function refreshMonitor() { 
//             updateMonitorData(); 
//             alert('监控数据已刷新'); 
//         } 
//         function viewLogs() { 
//             alert('查看日志功能待实现'); 
//         } 
//         function manageBackups() { 
//             window.location.href = config.href  ; 
//         } 
        // 计算运行时间
//         function updateUptime() { 
//             // 这里应该从服务器获取真实的运行时间 
// //             const uptimeEl = document.getElementById('uptime');  
// //             let seconds = 0;  
//              
//             setInterval(() => { 
//                 seconds++; 
// //                 const hours = Math.floor(seconds / 3600);  
// //                 const minutes = Math.floor((seconds % 3600) / 60);  
// //                 const secs = seconds % 60;  
//                 uptimeEl.textContent = hours + 'h ' + minutes + 'm ' + secs + 's'; 
//             }, 1000); 
//         } 
        updateUptime();
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
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', () => {
            // 初始化日志查看器
            initLogViewer();
        });
//         function initLogViewer() { 
// //             const logContainer = document.getElementById('log-container');  
// //             const generateLogsBtn = document.getElementById('generate-logs-btn');  
// //             const clearLogsBtn = document.getElementById('clear-logs-btn');  
// //             const exportLogsBtn = document.getElementById('export-logs-btn');  
// //             const keywordFilter = document.getElementById('keyword-filter');  
// //             const levelFilter = document.getElementById('level-filter');  
// //             const categoryFilter = document.getElementById('category-filter');  
// //             const filterBtn = document.getElementById('filter-btn');  
// //             const resetFilterBtn = document.getElementById('reset-filter-btn');  
// //             const totalLogsEl = document.getElementById('total-logs');  
// //             const errorLogsEl = document.getElementById('error-logs');  
// //             const warningLogsEl = document.getElementById('warning-logs');  
// //             const successLogsEl = document.getElementById('success-logs');  
//              
//             // 渲染日志 
//             function renderLogs(logs = null) { 
//                 // 如果没有提供日志，使用所有日志 
//                 if (!logs) { 
//                     logs = logManager.getLogs(); 
//                 } 
//                  
//                 // 更新统计信息 
// //                 const stats = logManager.getStats();  
//                 totalLogsEl.textContent = stats.total; 
//                 errorLogsEl.textContent = stats.byLevel.error || 0; 
//                 warningLogsEl.textContent = stats.byLevel.warning || 0; 
//                 successLogsEl.textContent = stats.byLevel.success || 0; 
//                  
//                 // 清空容器 
//                 logContainer./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  ; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                  
//                 // 如果没有日志，显示空状态 
//                 if (logs.length === 0) { 
//                     logContainer./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  empty-state"> 
//                             <i class = config.class  ></i> 
//                             <h3>暂无日志</h3> 
//                             <p>点击"生成100条日志"按钮生成日志，或等待系统自动生成日志</p> 
//                         </div> 
//                     `; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                     return; 
//                 } 
//                  
//                 // 渲染日志列表 
//                 logs.forEach(log => { 
// //                     const logItem = document.createElement('div');  
//                     logItem.className = config.className  div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML  log-header"> 
//                             <span class = config.class  >${log.level.toUpperCase()}</span> 
//                             <span class = config.class  >${new Date(log.timestamp).toLocaleString()}</span> 
//                         </div> 
//                         <div class = config.class  >${log.message}</div> 
//                         <div class = config.class  > 
//                             <span class = config.class  >${log.category}</span> 
//                             <span class = config.class  >${log.action || 'N/A'}</span> 
//                             <span class = config.class  >用户: ${log.userId}</span> 
//                             <span class = config.class  >IP: ${log.ip}</span> 
//                         </div> 
//                     `; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ 
//                     logContainer.appendChild(logItem); 
//                 }); 
//             } 
//              
//             // 生成100条日志 
//             generateLogsBtn.addEventListener('click', () => { 
//                 logManager.generateRandomLogs(100); 
//                 renderLogs(); 
//             }); 
//              
//             // 清空日志 
//             clearLogsBtn.addEventListener('click', () => { 
//                 if (confirm('确定要清空所有日志吗？')) { 
//                     logManager.clearLogs(); 
//                     renderLogs(); 
//                 } 
//             }); 
//              
//             // 导出日志 
//             exportLogsBtn.addEventListener('click', () => { 
//                 logManager.downloadLogs('json'); 
//             }); 
//              
//             // 筛选日志 
//             filterBtn.addEventListener('click', () => { 
// //                 const filter = {  
//                     keyword: keywordFilter.value, 
//                     level: levelFilter.value, 
//                     category: categoryFilter.value 
//                 }; 
// //                 const filteredLogs = logManager.getLogs(filter);  
//                 renderLogs(filteredLogs); 
//             }); 
//              
//             // 返回首页 
//             homeBtn.addEventListener('click', () => { 
//                 window.location.href = config.href  ; 
//             }); 
//              
//             // 重置筛选 
//             resetFilterBtn.addEventListener('click', () => { 
//                 keywordFilter.value = config.value  ; 
//                 levelFilter.value = config.value  ; 
//                 categoryFilter.value = config.value  ; 
//                 renderLogs(); 
//             }); 
//              
//             // 初始渲染 
//             renderLogs(); 
//         } 
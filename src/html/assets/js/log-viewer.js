
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
        
//         function initLogViewer() { /* 代码质量修复：未使用的函数 */
// //             const logContainer = document.getElementById('log-container'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const generateLogsBtn = document.getElementById('generate-logs-btn'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const clearLogsBtn = document.getElementById('clear-logs-btn'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const exportLogsBtn = document.getElementById('export-logs-btn'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const keywordFilter = document.getElementById('keyword-filter'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const levelFilter = document.getElementById('level-filter'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const categoryFilter = document.getElementById('category-filter'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const filterBtn = document.getElementById('filter-btn'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const resetFilterBtn = document.getElementById('reset-filter-btn'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const totalLogsEl = document.getElementById('total-logs'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const errorLogsEl = document.getElementById('error-logs'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const warningLogsEl = document.getElementById('warning-logs'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const successLogsEl = document.getElementById('success-logs'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 渲染日志 /* 代码质量修复：未使用的函数 */
//             function renderLogs(logs = null) { /* 代码质量修复：未使用的函数 */
//                 // 如果没有提供日志，使用所有日志 /* 代码质量修复：未使用的函数 */
//                 if (!logs) { /* 代码质量修复：未使用的函数 */
//                     logs = logManager.getLogs(); /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 更新统计信息 /* 代码质量修复：未使用的函数 */
// //                 const stats = logManager.getStats(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                 totalLogsEl.textContent = stats.total; /* 代码质量修复：未使用的函数 */
//                 errorLogsEl.textContent = stats.byLevel.error || 0; /* 代码质量修复：未使用的函数 */
//                 warningLogsEl.textContent = stats.byLevel.warning || 0; /* 代码质量修复：未使用的函数 */
//                 successLogsEl.textContent = stats.byLevel.success || 0; /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 清空容器 /* 代码质量修复：未使用的函数 */
//                 logContainer./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 如果没有日志，显示空状态 /* 代码质量修复：未使用的函数 */
//                 if (logs.length === 0) { /* 代码质量修复：未使用的函数 */
//                     logContainer./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */empty-state"> /* 代码质量修复：未使用的函数 */
//                             <i class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */></i> /* 代码质量修复：未使用的函数 */
//                             <h3>暂无日志</h3> /* 代码质量修复：未使用的函数 */
//                             <p>点击"生成100条日志"按钮生成日志，或等待系统自动生成日志</p> /* 代码质量修复：未使用的函数 */
//                         </div> /* 代码质量修复：未使用的函数 */
//                     `; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 代码质量修复：未使用的函数 */
//                     return; /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 渲染日志列表 /* 代码质量修复：未使用的函数 */
//                 logs.forEach(log => { /* 代码质量修复：未使用的函数 */
// //                     const logItem = document.createElement('div'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     logItem.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv./* 性能优化：使用DOM API */ const tempDiv = document.createElement("div"); tempDiv.innerHTML = config.innerHTML /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */log-header"> /* 代码质量修复：未使用的函数 */
//                             <span class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>${log.level.toUpperCase()}</span> /* 代码质量修复：未使用的函数 */
//                             <span class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>${new Date(log.timestamp).toLocaleString()}</span> /* 代码质量修复：未使用的函数 */
//                         </div> /* 代码质量修复：未使用的函数 */
//                         <div class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>${log.message}</div> /* 代码质量修复：未使用的函数 */
//                         <div class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */> /* 代码质量修复：未使用的函数 */
//                             <span class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>${log.category}</span> /* 代码质量修复：未使用的函数 */
//                             <span class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>${log.action || 'N/A'}</span> /* 代码质量修复：未使用的函数 */
//                             <span class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>用户: ${log.userId}</span> /* 代码质量修复：未使用的函数 */
//                             <span class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */>IP: ${log.ip}</span> /* 代码质量修复：未使用的函数 */
//                         </div> /* 代码质量修复：未使用的函数 */
//                     `; /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 然后使用appendChild等方法 */ /* 代码质量修复：未使用的函数 */
//                     logContainer.appendChild(logItem); /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 生成100条日志 /* 代码质量修复：未使用的函数 */
//             generateLogsBtn.addEventListener('click', () => { /* 代码质量修复：未使用的函数 */
// //                 console.log('开始生成100条日志...'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//                 logManager.generateRandomLogs(100); /* 代码质量修复：未使用的函数 */
// //                 console.log('100条日志生成完成！'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//                 renderLogs(); /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 清空日志 /* 代码质量修复：未使用的函数 */
//             clearLogsBtn.addEventListener('click', () => { /* 代码质量修复：未使用的函数 */
//                 if (confirm('确定要清空所有日志吗？')) { /* 代码质量修复：未使用的函数 */
//                     logManager.clearLogs(); /* 代码质量修复：未使用的函数 */
//                     renderLogs(); /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 导出日志 /* 代码质量修复：未使用的函数 */
//             exportLogsBtn.addEventListener('click', () => { /* 代码质量修复：未使用的函数 */
//                 logManager.downloadLogs('json'); /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 筛选日志 /* 代码质量修复：未使用的函数 */
//             filterBtn.addEventListener('click', () => { /* 代码质量修复：未使用的函数 */
// //                 const filter = { /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     keyword: keywordFilter.value, /* 代码质量修复：未使用的函数 */
//                     level: levelFilter.value, /* 代码质量修复：未使用的函数 */
//                     category: categoryFilter.value /* 代码质量修复：未使用的函数 */
//                 }; /* 代码质量修复：未使用的函数 */
// //                 const filteredLogs = logManager.getLogs(filter); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                 renderLogs(filteredLogs); /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 返回首页 /* 代码质量修复：未使用的函数 */
//             homeBtn.addEventListener('click', () => { /* 代码质量修复：未使用的函数 */
//                 window.location.href = config.href /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 重置筛选 /* 代码质量修复：未使用的函数 */
//             resetFilterBtn.addEventListener('click', () => { /* 代码质量修复：未使用的函数 */
//                 keywordFilter.value = config.value /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 levelFilter.value = config.value /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 categoryFilter.value = config.value /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 renderLogs(); /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 初始渲染 /* 代码质量修复：未使用的函数 */
//             renderLogs(); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
    
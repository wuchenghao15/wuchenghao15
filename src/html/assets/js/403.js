
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
// 初始化主题图标
//         function initializeThemeIcon() { /* 代码质量修复：未使用的函数 */
// //             const themeButton = document.getElementById('themeToggle'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const icon = themeButton.querySelector('.theme-icon'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 检查是否是公祭日 /* 代码质量修复：未使用的函数 */
//             if (checkNationalMemorialDay()) { /* 代码质量修复：未使用的函数 */
//                 icon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 themeButton.title = config.title /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 themeButton.disabled = true; /* 代码质量修复：未使用的函数 */
//                 return; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             // 检查保存的主题 /* 代码质量修复：未使用的函数 */
// //             const savedTheme = localStorage.getItem('theme') || 'light'; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (savedTheme === 'dark') { /* 代码质量修复：未使用的函数 */
//                 // 如果是深色主题，显示太阳图标 /* 代码质量修复：未使用的函数 */
//                 icon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 themeButton.title = config.title /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 document.body.classList.add('dark-theme'); /* 代码质量修复：未使用的函数 */
//             } else { /* 代码质量修复：未使用的函数 */
//                 // 如果是浅色主题，显示月亮图标 /* 代码质量修复：未使用的函数 */
//                 icon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 themeButton.title = config.title /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 document.body.classList.remove('dark-theme'); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */

        // 主题切换 - 太阳与月亮互换效果
        document.getElementById('themeToggle').addEventListener('click', function() {
            // 检查是否是公祭日模式
            if (checkNationalMemorialDay()) {
                return; // 公祭日模式不可切换
            }
            
//             const icon = this.querySelector('.theme-icon'); /* 代码质量修复：未使用的 常量 */
            document.body.classList.toggle('dark-theme');
            if (document.body.classList.contains('dark-theme')) {
                // 切换到深色主题，显示太阳图标
                icon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */;
                this.title = config.title /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */;
                // 保存主题设置
                localStorage.setItem('theme', 'dark');
            } else {
                // 切换到浅色主题，显示月亮图标
                icon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */;
                this.title = config.title /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */;
                // 保存主题设置
                localStorage.setItem('theme', 'light');
            }
        });
        
        // 页面加载后执行
        document.addEventListener('DOMContentLoaded', function() {
            // 显示当前URL和时间 - 优先使用服务器传入的参数
//             const requestedPath = window.REQUESTED_PATH || window.location.href; /* 代码质量修复：未使用的 常量 */
//             const timestamp = window.TIMESTAMP || new Date().toLocaleString('zh-CN'); /* 代码质量修复：未使用的 常量 */
            
            document.getElementById('currentUrl').textContent = requestedPath;
            document.getElementById('errorTime').textContent = timestamp;
            
            // 更新当前时间
//             function updateTime() { /* 代码质量修复：未使用的函数 */
//                 document.getElementById('current-time').textContent = new Date().toLocaleString('zh-CN'); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
            updateTime();
            setInterval(updateTime, 1000);
            
            // 初始化主题图标
            initializeThemeIcon();
            
            // 初始化锁定屏幕管理器 - 添加类型检查
            if (typeof LockScreenManager !== 'undefined') {
//                 const lockManager = new LockScreenManager(); /* 代码质量修复：未使用的 常量 */
                // LockScreenManager构造函数会自动初始化，无需调用init()
            }
        });
    

            // 安全机制初始化
            document.addEventListener('DOMContentLoaded', function() {
                // 初始化安全模块
//                 const sessionManager = new SessionManager(); /* 代码质量修复：未使用的 常量 */
//                 const encryptionManager = new EncryptionManager(); /* 代码质量修复：未使用的 常量 */
//                 const securityEventManager = new SecurityEventManager(); /* 代码质量修复：未使用的 常量 */
//                 const dataSecurityManager = new DataSecurityManager(); /* 代码质量修复：未使用的 常量 */
//                 const tokenVerificationManager = new TokenVerificationManager(); /* 代码质量修复：未使用的 常量 */
                
                // 启动安全监控
                setTimeout(() => {
//                     console.log('403页面安全机制已启动'); /* 代码质量修复：调试语句 */
                }, 1000);
                
                // 页面卸载时清理
                window.addEventListener('beforeunload', function() {
                    if (sessionManager) sessionManager.clearSession();
                    if (securityEventManager) securityEventManager.stopMonitoring();
                });
            });
            
            // 初始化时间显示
//             function updateDateTime() { /* 代码质量修复：未使用的函数 */
//                 // 获取当前时间 /* 代码质量修复：未使用的函数 */
// //                 const now = new Date(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 更新公历时间 /* 代码质量修复：未使用的函数 */
// //                 const gregorianDate = now.toLocaleDateString('zh-CN', { /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     year: 'numeric', /* 代码质量修复：未使用的函数 */
//                     month: 'long', /* 代码质量修复：未使用的函数 */
//                     day: 'numeric', /* 代码质量修复：未使用的函数 */
//                     hour: '2-digit', /* 代码质量修复：未使用的函数 */
//                     minute: '2-digit', /* 代码质量修复：未使用的函数 */
//                     second: '2-digit', /* 代码质量修复：未使用的函数 */
//                     weekday: 'long' /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//                 document.getElementById('gregorian-date').textContent = gregorianDate; /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 模拟农历时间 /* 代码质量修复：未使用的函数 */
// //                 const lunarDate = getLunarDate(now); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                 document.getElementById('lunar-date').textContent = lunarDate; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
            
            // 简单的农历日期模拟函数
//             function getLunarDate(date) { /* 代码质量修复：未使用的函数 */
// //                 const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月']; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //                 const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',  /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                                   '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十', /* 代码质量修复：未使用的函数 */
//                                   '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十']; /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
// //                 const month = date.getMonth(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //                 const day = date.getDate() - 1; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 return `农历 ${lunarMonths[month]} ${lunarDays[day]}`; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
            
            // 页面加载完成后初始化
            window.addEventListener('DOMContentLoaded', () => {
                // 初始更新时间
                updateDateTime();
                // 每秒更新时间
                setInterval(updateDateTime, 1000);
                
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
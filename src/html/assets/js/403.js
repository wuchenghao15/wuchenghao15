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
//         function initializeThemeIcon() { 
// //             const themeButton = document.getElementById('themeToggle');  
// //             const icon = themeButton.querySelector('.theme-icon');  
//              
//             // 检查是否是公祭日 
//             if (checkNationalMemorialDay()) { 
//                 icon.className = config.className  ; 
//                 themeButton.title = config.title  ; 
//                 themeButton.disabled = true; 
//                 return; 
//             } 
//              
//             // 检查保存的主题 
// //             const savedTheme = localStorage.getItem('theme') || 'light';  
//             if (savedTheme === 'dark') { 
//                 // 如果是深色主题，显示太阳图标 
//                 icon.className = config.className  ; 
//                 themeButton.title = config.title  ; 
//                 document.body.classList.add('dark-theme'); 
//             } else { 
//                 // 如果是浅色主题，显示月亮图标 
//                 icon.className = config.className  ; 
//                 themeButton.title = config.title  ; 
//                 document.body.classList.remove('dark-theme'); 
//             } 
//         } 
        // 主题切换 - 太阳与月亮互换效果
        document.getElementById('themeToggle').addEventListener('click', function() {
            // 检查是否是公祭日模式
            if (checkNationalMemorialDay()) {
                return; // 公祭日模式不可切换
            }
//             const icon = this.querySelector('.theme-icon'); 
            document.body.classList.toggle('dark-theme');
            if (document.body.classList.contains('dark-theme')) {
                // 切换到深色主题，显示太阳图标
                icon.className = config.className  ;
                this.title = config.title  ;
                // 保存主题设置
                localStorage.setItem('theme', 'dark');
            } else {
                // 切换到浅色主题，显示月亮图标
                icon.className = config.className  ;
                this.title = config.title  ;
                // 保存主题设置
                localStorage.setItem('theme', 'light');
            }
        });
        // 页面加载后执行
        document.addEventListener('DOMContentLoaded', function() {
            // 显示当前URL和时间 - 优先使用服务器传入的参数
//             const requestedPath = window.REQUESTED_PATH || window.location.href; 
//             const timestamp = window.TIMESTAMP || new Date().toLocaleString('zh-CN'); 
            document.getElementById('currentUrl').textContent = requestedPath;
            document.getElementById('errorTime').textContent = timestamp;
            // 更新当前时间
//             function updateTime() { 
//                 document.getElementById('current-time').textContent = new Date().toLocaleString('zh-CN'); 
//             } 
            updateTime();
            setInterval(updateTime, 1000);
            // 初始化主题图标
            initializeThemeIcon();
            // 初始化锁定屏幕管理器 - 添加类型检查
            if (typeof LockScreenManager !== 'undefined') {
//                 const lockManager = new LockScreenManager(); 
                // LockScreenManager构造函数会自动初始化，无需调用init()
            }
        });
            // 安全机制初始化
            document.addEventListener('DOMContentLoaded', function() {
                // 初始化安全模块
//                 const sessionManager = new SessionManager(); 
//                 const encryptionManager = new EncryptionManager(); 
//                 const securityEventManager = new SecurityEventManager(); 
//                 const dataSecurityManager = new DataSecurityManager(); 
//                 const tokenVerificationManager = new TokenVerificationManager(); 
                // 启动安全监控
                setTimeout(() => {
                }, 1000);
                // 页面卸载时清理
                window.addEventListener('beforeunload', function() {
                    if (sessionManager) sessionManager.clearSession();
                    if (securityEventManager) securityEventManager.stopMonitoring();
                });
            });
            // 初始化时间显示
//             function updateDateTime() { 
//                 // 获取当前时间 
// //                 const now = new Date();  
//                  
//                 // 更新公历时间 
// //                 const gregorianDate = now.toLocaleDateString('zh-CN', {  
//                     year: 'numeric', 
//                     month: 'long', 
//                     day: 'numeric', 
//                     hour: '2-digit', 
//                     minute: '2-digit', 
//                     second: '2-digit', 
//                     weekday: 'long' 
//                 }); 
//                 document.getElementById('gregorian-date').textContent = gregorianDate; 
//                  
//                 // 模拟农历时间 
// //                 const lunarDate = getLunarDate(now);  
//                 document.getElementById('lunar-date').textContent = lunarDate; 
//             } 
            // 简单的农历日期模拟函数
//             function getLunarDate(date) { 
// //                 const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];  
// //                 const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',   
//                                   '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十', 
//                                   '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十']; 
//                  
// //                 const month = date.getMonth();  
// //                 const day = date.getDate() - 1;  
//                  
//                 return `农历 ${lunarMonths[month]} ${lunarDays[day]}`; 
//             } 
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
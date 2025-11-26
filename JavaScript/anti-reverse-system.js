// 防止逆向跳转安全系统 - 简化版本（移除锁定功能）
class AntiReverseSystem {
    constructor() {
        this.blockedAttempts = 0;
        this.maxBlockedAttempts = 5;
        this.blockDuration = 5 * 60 * 1000; // 5分钟封禁
        
        this.init().catch(error => console.error(`[anti-reverse-system.js] this.init failed:`, error));
    }

    // 初始化防逆向系统
    init() {
        console.log('初始化防逆向跳转系统（简化版）');
        
        // 监听浏览器历史操作
        this.setupHistoryMonitoring().catch(error => console.error(`[anti-reverse-system.js] this.setupHistoryMonitoring failed:`, error));
        
        // 监听键盘快捷键
        this.setupKeyboardMonitoring().catch(error => console.error(`[anti-reverse-system.js] this.setupKeyboardMonitoring failed:`, error));
        
        // 监听右键菜单
        this.setupContextMenuMonitoring().catch(error => console.error(`[anti-reverse-system.js] this.setupContextMenuMonitoring failed:`, error));
        
        // 监听开发者工具
        this.setupDevToolsMonitoring().catch(error => console.error(`[anti-reverse-system.js] this.setupDevToolsMonitoring failed:`, error));
    }

    // 设置历史监控
    setupHistoryMonitoring() {
        // 监听popstate事件
        window.addEventListener('popstate', (e) => {
            this.logSecurityEvent('popstate_detected', window.location.href);
        });

        // 重写history方法并记录
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = function(state, title, url) {
            if (window.antiReverseSystem) {
                window.antiReverseSystem.logSecurityEvent('push_state', url);
            }
            return originalPushState.call(this, state, title, url);
        };

        history.replaceState = function(state, title, url) {
            if (window.antiReverseSystem) {
                window.antiReverseSystem.logSecurityEvent('replace_state', url);
            }
            return originalReplaceState.call(this, state, title, url);
        };
    }

    // 设置键盘监控
    setupKeyboardMonitoring() {
        document.addEventListener('keydown', (e) => {
            // 检测常见的开发者工具快捷键
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'C') ||
                (e.ctrlKey && e.key === 'U')) {
                
                this.logSecurityEvent('devtools_shortcut', e.key);
                this.handleBlockedAttempt().catch(error => console.error(`[anti-reverse-system.js] this.handleBlockedAttempt failed:`, error));
            }
        });
    }

    // 设置右键菜单监控
    setupContextMenuMonitoring() {
        document.addEventListener('contextmenu', (e) => {
            this.logSecurityEvent('context_menu', 'right_click');
            // 可以选择是否阻止右键菜单
            // e.preventDefault();
        });
    }

    // 设置开发者工具监控
    setupDevToolsMonitoring() {
        let devtools = {open: false, orientation: null};
        
        const threshold = 160;
        
        setInterval(() => {
            if (window.outerHeight - window.innerHeight > threshold || 
                window.outerWidth - window.innerWidth > threshold) {
                if (!devtools.open) {
                    devtools.open = true;
                    this.logSecurityEvent('devtools_open', 'detected');
                    this.handleBlockedAttempt().catch(error => console.error(`[anti-reverse-system.js] this.handleBlockedAttempt failed:`, error));
                }
            } else {
                devtools.open = false;
            }
        }, 500);
    }

    // 处理阻止的尝试
    async handleBlockedAttempt() {
        this.blockedAttempts++;
        
        if (this.blockedAttempts >= this.maxBlockedAttempts) {
            this.logSecurityEvent('max_attempts_reached', this.blockedAttempts);
            
            // 可以选择重定向到登录页面
            // window.location.href = '../HTML/index.html?reason=security_violation';
        }
    }

    // 记录安全事件
    logSecurityEvent(eventType, details) {
        const logData = {
            timestamp: new Date().toISOString(),
            type: eventType,
            details: details,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        // 存储在localStorage中
        let securityLogs = JSON.parse(localStorage.getItem('security_logs') || '[]');
        securityLogs.push(logData);
        
        // 只保留最近100条记录
        if (securityLogs.length > 100) {
            securityLogs = securityLogs.slice(-100);
        }
        
        localStorage.setItem('security_logs', JSON.stringify(securityLogs));
        console.log('安全事件记录:', logData);
    }

    // 获取安全状态
    getSecurityStatus() {
        return {
            blockedAttempts: this.blockedAttempts,
            maxBlockedAttempts: this.maxBlockedAttempts,
            isBlocked: this.blockedAttempts >= this.maxBlockedAttempts
        };
    }

    // 重置阻止计数
    resetBlockedAttempts() {
        this.blockedAttempts = 0;
        this.logSecurityEvent('reset_attempts', 'manual_reset');
    }

    // 清除安全日志
    clearSecurityLogs() {
        localStorage.removeItem('security_logs');
        console.log('安全日志已清除');
    }

    // 获取安全日志
    getSecurityLogs() {
        return JSON.parse(localStorage.getItem('security_logs') || '[]');
    }
}

// 初始化防逆向系统
window.antiReverseSystem = new AntiReverseSystem();

// 导出类以供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AntiReverseSystem;
}
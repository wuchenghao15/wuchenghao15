// 防止逆向跳转安全机制
class AntiReverseSystem {
    constructor() {
        this.isLocked = false;
        this.lockStartTime = null;
        this.originalLocation = null;
        this.blockedAttempts = 0;
        this.maxBlockedAttempts = 5;
        this.blockDuration = 5 * 60 * 1000; // 5分钟封禁
        
        this.init();
    }

    // 初始化防逆向系统
    init() {
        // 检查是否为锁定页面
        if (this.isLockPage()) {
            console.log('初始化防逆向跳转系统');
            this.lockPage();
            this.setupSecurityMeasures();
        }
        
        // 监听浏览器历史操作
        this.setupHistoryMonitoring();
        
        // 监听键盘快捷键
        this.setupKeyboardMonitoring();
        
        // 监听右键菜单
        this.setupContextMenuMonitoring();
        
        // 监听开发者工具
        this.setupDevToolsMonitoring();
    }

    // 检查是否为锁定页面
    isLockPage() {
        return window.location.pathname.includes('locked.html') || 
               window.location.pathname.endsWith('/locked');
    }

    // 锁定页面
    lockPage() {
        this.isLocked = true;
        this.lockStartTime = Date.now();
        this.originalLocation = window.location.href;
        
        // 禁用导航
        this.disableNavigation();
        
        // 防止关闭
        this.preventClose();
        
        // 全屏模式
        this.enforceFullscreen();
        
        console.log('页面已锁定，防止逆向跳转');
    }

    // 设置安全措施
    setupSecurityMeasures() {
        // 清除历史记录
        this.clearHistory();
        
        // 阻止后退
        this.blockBackNavigation();
        
        // 防止刷新
        this.preventRefresh();
        
        // 监听页面可见性
        this.setupVisibilityMonitoring();
    }

    // 禁用导航
    disableNavigation() {
        // 禁用链接点击
        document.addEventListener('click', (e) => {
            const target = e.target.closest('a');
            if (target && target.href) {
                e.preventDefault();
                e.stopPropagation();
                this.logSecurityEvent('blocked_navigation', target.href);
                return false;
            }
        }, true);

        // 禁用表单提交
        document.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.logSecurityEvent('blocked_form_submit', e.target.action);
            return false;
        }, true);

        // 禁用window.location改变
        const originalLocation = window.location;
        Object.defineProperty(window, 'location', {
            get: () => originalLocation,
            set: (value) => {
                this.logSecurityEvent('blocked_location_change', value);
                return originalLocation;
            }
        });
    }

    // 防止关闭
    preventClose() {
        window.addEventListener('beforeunload', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                e.returnValue = '系统已锁定，无法关闭此页面。请通过解锁系统来正常退出。';
                return e.returnValue;
            }
        });

        window.addEventListener('unload', (e) => {
            if (this.isLocked) {
                // 记录异常关闭尝试
                this.logSecurityEvent('attempted_close', 'beforeunload');
                
                // 尝试阻止关闭
                e.preventDefault();
                return false;
            }
        });
    }

    // 强制全屏
    enforceFullscreen() {
        const requestFullscreen = () => {
            const elem = document.documentElement;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) {
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) {
                elem.msRequestFullscreen();
            }
        };

        // 延迟请求全屏，避免被阻止
        setTimeout(requestFullscreen, 1000);

        // 监听全屏变化
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && this.isLocked) {
                // 如果退出全屏，尝试重新进入
                setTimeout(requestFullscreen, 100);
            }
        });
    }

    // 设置历史监控
    setupHistoryMonitoring() {
        // 监听popstate事件
        window.addEventListener('popstate', (e) => {
            if (this.isLocked && this.isLockPage()) {
                e.preventDefault();
                e.stopPropagation();
                
                // 强制回到锁定页面
                window.history.pushState({}, '', window.location.href);
                
                this.logSecurityEvent('blocked_back_navigation', window.location.href);
                this.handleBlockedAttempt();
                return false;
            }
        });

        // 重写history方法
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = function(state, title, url) {
            if (window.antiReverseSystem && window.antiReverseSystem.isLocked) {
                window.antiReverseSystem.logSecurityEvent('blocked_push_state', url);
                return false;
            }
            return originalPushState.call(this, state, title, url);
        };

        history.replaceState = function(state, title, url) {
            if (window.antiReverseSystem && window.antiReverseSystem.isLocked) {
                window.antiReverseSystem.logSecurityEvent('blocked_replace_state', url);
                return false;
            }
            return originalReplaceState.call(this, state, title, url);
        };
    }

    // 阻止后退导航
    blockBackNavigation() {
        // 添加历史记录项
        window.history.pushState({ noBack: true }, '', window.location.href);
        
        // 连续添加多个历史记录项，使后退无效
        for (let i = 0; i < 10; i++) {
            window.history.pushState({ noBack: true }, '', window.location.href);
        }
    }

    // 清除历史记录
    clearHistory() {
        try {
            // 尝试清除历史记录
            window.history.replaceState({}, '', window.location.href);
            
            // 添加大量无用的历史记录项
            for (let i = 0; i < 100; i++) {
                window.history.pushState({ dummy: true }, '', window.location.href);
            }
            
            // 回到当前位置
            window.history.go(-100);
            
        } catch (error) {
            console.error('清除历史记录失败:', error);
        }
    }

    // 设置键盘监控
    setupKeyboardMonitoring() {
        document.addEventListener('keydown', (e) => {
            if (!this.isLocked) return;

            // 阻止常见快捷键
            const blockedKeys = [
                // 后退
                'Backspace',
                // 刷新
                'F5',
                'r',
                'R',
                // 开发者工具
                'F12',
                'I',
                'i',
                'J',
                'j',
                'C',
                'c',
                // Alt + 左箭头 (后退)
                'ArrowLeft',
                // ESC
                'Escape'
            ];

            const key = e.key;
            const ctrl = e.ctrlKey || e.metaKey;
            const alt = e.altKey;
            const shift = e.shiftKey;

            // 检查是否为被阻止的快捷键
            if (blockedKeys.includes(key)) {
                // 特殊处理需要组合键的情况
                if ((key === 'r' || key === 'R') && ctrl) {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_refresh', 'Ctrl+R');
                    return false;
                }
                
                if ((key === 'ArrowLeft') && alt) {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_back', 'Alt+Left');
                    return false;
                }
                
                if (key === 'F5') {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_refresh', 'F5');
                    return false;
                }
                
                if (key === 'F12') {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_devtools', 'F12');
                    return false;
                }
                
                if ((key === 'I' || key === 'i') && ctrl && shift) {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_devtools', 'Ctrl+Shift+I');
                    return false;
                }
                
                if ((key === 'J' || key === 'j') && ctrl && shift) {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_devtools', 'Ctrl+Shift+J');
                    return false;
                }
                
                if ((key === 'C' || key === 'c') && ctrl && shift) {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_devtools', 'Ctrl+Shift+C');
                    return false;
                }
                
                if (key === 'Backspace' && !['input', 'textarea'].includes(e.target.tagName.toLowerCase())) {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_backspace', 'Backspace');
                    return false;
                }
                
                if (key === 'Escape') {
                    e.preventDefault();
                    this.logSecurityEvent('blocked_escape', 'Escape');
                    return false;
                }
            }
        }, true);
    }

    // 设置右键菜单监控
    setupContextMenuMonitoring() {
        document.addEventListener('contextmenu', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                e.stopPropagation();
                this.logSecurityEvent('blocked_context_menu', 'contextmenu');
                return false;
            }
        }, true);

        // 阻止拖拽
        document.addEventListener('dragstart', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                this.logSecurityEvent('blocked_drag', 'dragstart');
                return false;
            }
        }, true);

        // 阻止选择文本
        document.addEventListener('selectstart', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                this.logSecurityEvent('blocked_selection', 'selectstart');
                return false;
            }
        }, true);
    }

    // 设置开发者工具监控
    setupDevToolsMonitoring() {
        let devtools = { open: false, orientation: null };
        
        const threshold = 160;
        
        setInterval(() => {
            if (this.isLocked) {
                if (window.outerHeight - window.innerHeight > threshold || 
                    window.outerWidth - window.innerWidth > threshold) {
                    if (!devtools.open) {
                        devtools.open = true;
                        this.handleDevToolsDetected();
                    }
                } else {
                    devtools.open = false;
                }
            }
        }, 500);

        // 监控控制台输出
        const originalLog = console.log;
        const originalWarn = console.warn;
        const originalError = console.error;
        
        console.log = function(...args) {
            if (window.antiReverseSystem && window.antiReverseSystem.isLocked) {
                window.antiReverseSystem.logSecurityEvent('console_log', args.join(' '));
            }
            return originalLog.apply(console, args);
        };
        
        console.warn = function(...args) {
            if (window.antiReverseSystem && window.antiReverseSystem.isLocked) {
                window.antiReverseSystem.logSecurityEvent('console_warn', args.join(' '));
            }
            return originalWarn.apply(console, args);
        };
        
        console.error = function(...args) {
            if (window.antiReverseSystem && window.antiReverseSystem.isLocked) {
                window.antiReverseSystem.logSecurityEvent('console_error', args.join(' '));
            }
            return originalError.apply(console, args);
        };
    }

    // 处理开发者工具检测
    handleDevToolsDetected() {
        this.logSecurityEvent('devtools_detected', '开发者工具已打开');
        
        // 显示警告
        this.showSecurityWarning('检测到开发者工具', '请关闭开发者工具以继续使用系统。');
        
        // 尝试关闭开发者工具
        this.attemptCloseDevTools();
    }

    // 尝试关闭开发者工具
    attemptCloseDevTools() {
        // 清除控制台
        console.clear();
        
        // 显示大量警告信息
        for (let i = 0; i < 100; i++) {
            console.warn('⚠️ 安全警告：系统已锁定，请勿尝试绕过安全机制！');
        }
        
        // 尝试关闭窗口
        setTimeout(() => {
            window.close();
        }, 1000);
    }

    // 设置可见性监控
    setupVisibilityMonitoring() {
        document.addEventListener('visibilitychange', () => {
            if (this.isLocked) {
                if (document.hidden) {
                    this.logSecurityEvent('page_hidden', '页面被隐藏');
                    
                    // 页面隐藏时的处理
                    this.handlePageHidden();
                } else {
                    this.logSecurityEvent('page_visible', '页面重新可见');
                    
                    // 页面重新可见时的处理
                    this.handlePageVisible();
                }
            }
        });
    }

    // 处理页面隐藏
    handlePageHidden() {
        // 记录隐藏时间
        sessionStorage.setItem('pageHiddenTime', Date.now());
        
        // 显示警告
        this.showSecurityWarning('页面已隐藏', '请保持页面可见状态以确保系统安全。');
    }

    // 处理页面重新可见
    handlePageVisible() {
        const hiddenTime = sessionStorage.getItem('pageHiddenTime');
        if (hiddenTime) {
            const hiddenDuration = Date.now() - parseInt(hiddenTime);
            
            if (hiddenDuration > 5000) { // 隐藏超过5秒
                this.logSecurityEvent('long_hidden', `页面隐藏了 ${Math.round(hiddenDuration / 1000)} 秒`);
                
                // 可能需要重新验证
                this.handleSuspiciousActivity();
            }
            
            sessionStorage.removeItem('pageHiddenTime');
        }
    }

    // 处理可疑活动
    handleSuspiciousActivity() {
        this.blockedAttempts++;
        
        if (this.blockedAttempts >= this.maxBlockedAttempts) {
            this.handleExcessiveBlockedAttempts();
        } else {
            this.showSecurityWarning('可疑活动检测', '检测到可疑活动，请正确使用系统。');
        }
    }

    // 处理过多的阻止尝试
    handleExcessiveBlockedAttempts() {
        this.logSecurityEvent('excessive_blocked_attempts', `阻止尝试次数: ${this.blockedAttempts}`);
        
        // 显示严重警告
        this.showSecurityWarning('安全警告', '检测到多次尝试绕过安全机制，系统将采取进一步措施。');
        
        // 可能的额外安全措施
        this.enhanceSecurityMeasures();
    }

    // 增强安全措施
    enhanceSecurityMeasures() {
        // 更频繁的检查
        setInterval(() => {
            if (this.isLocked) {
                this.verifySecurityStatus();
            }
        }, 1000);
        
        // 更严格的键盘监控
        this.setupStrictKeyboardMonitoring();
        
        // 禁用更多功能
        this.disableAdvancedFeatures();
    }

    // 验证安全状态
    verifySecurityStatus() {
        // 检查是否仍在锁定页面
        if (!this.isLockPage()) {
            this.logSecurityEvent('page_changed', '页面已改变');
            this.redirectToLockPage();
        }
        
        // 检查全屏状态
        if (!document.fullscreenElement) {
            this.enforceFullscreen();
        }
        
        // 检查开发者工具
        this.checkDevToolsStatus();
    }

    // 设置严格键盘监控
    setupStrictKeyboardMonitoring() {
        document.addEventListener('keydown', (e) => {
            if (this.isLocked) {
                // 阻止所有键盘输入，除了允许的输入框
                const allowedInputs = ['input', 'textarea'];
                const isAllowedTarget = allowedInputs.includes(e.target.tagName.toLowerCase());
                
                if (!isAllowedTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            }
        }, true);
    }

    // 禁用高级功能
    disableAdvancedFeatures() {
        // 禁用复制粘贴
        document.addEventListener('copy', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                return false;
            }
        });
        
        document.addEventListener('paste', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                return false;
            }
        });
        
        // 禁用打印
        window.addEventListener('beforeprint', (e) => {
            if (this.isLocked) {
                e.preventDefault();
                return false;
            }
        });
    }

    // 检查开发者工具状态
    checkDevToolsStatus() {
        const threshold = 160;
        
        if (window.outerHeight - window.innerHeight > threshold || 
            window.outerWidth - window.innerWidth > threshold) {
            this.handleDevToolsDetected();
        }
    }

    // 处理阻止的尝试
    handleBlockedAttempt() {
        this.blockedAttempts++;
        
        if (this.blockedAttempts >= this.maxBlockedAttempts) {
            this.handleExcessiveBlockedAttempts();
        }
    }

    // 重定向到锁定页面
    redirectToLockPage() {
        const lockPageUrl = '/HTML/locked.html';
        if (window.location.pathname !== lockPageUrl) {
            window.location.href = lockPageUrl;
        }
    }

    // 显示安全警告
    showSecurityWarning(title, message) {
        // 创建警告元素
        const warning = document.createElement('div');
        warning.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc2626;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 999999;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        
        warning.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">${title}</div>
            <div style="font-size: 14px;">${message}</div>
        `;
        
        document.body.appendChild(warning);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (warning.parentNode) {
                warning.parentNode.removeChild(warning);
            }
        }, 3000);
    }

    // 记录安全事件
    logSecurityEvent(event, details) {
        const securityEvent = {
            timestamp: Date.now(),
            event: event,
            details: details,
            userAgent: navigator.userAgent,
            page: window.location.href
        };
        
        // 保存到本地存储
        const securityLogs = JSON.parse(localStorage.getItem('securityLogs') || '[]');
        securityLogs.push(securityEvent);
        
        // 只保留最近100条记录
        if (securityLogs.length > 100) {
            securityLogs.splice(0, securityLogs.length - 100);
        }
        
        localStorage.setItem('securityLogs', JSON.stringify(securityLogs));
        
        console.log('安全事件:', securityEvent);
    }

    // 解锁页面
    unlockPage() {
        this.isLocked = false;
        this.lockStartTime = null;
        this.blockedAttempts = 0;
        
        // 恢复正常功能
        this.restoreNormalFunctionality();
        
        console.log('页面已解锁');
    }

    // 恢复正常功能
    restoreNormalFunctionality() {
        // 这里可以恢复被禁用的功能
        // 实际实现中可能需要重新加载页面来完全恢复
    }

    // 获取安全状态
    getSecurityStatus() {
        return {
            isLocked: this.isLocked,
            lockStartTime: this.lockStartTime,
            blockedAttempts: this.blockedAttempts,
            maxBlockedAttempts: this.maxBlockedAttempts
        };
    }
}

// 创建全局实例
let antiReverseSystem;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    antiReverseSystem = new AntiReverseSystem();
    
    // 暴露到全局作用域
    window.antiReverseSystem = antiReverseSystem;
    
    console.log('防逆向跳转系统已初始化');
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AntiReverseSystem;
}
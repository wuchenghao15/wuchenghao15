/**
 * 安全事件防护机制 - MTSCOS AI Security Events Module
 * 提供防右击、防查看源码、防下载等安全防护功能
 */

class SecurityEventManager {
    constructor() {
        this.isLocked = false;
        this.securityLevel = 'medium'; // low, medium, high
        this.blockedKeys = ['F12', 'F5', 'Ctrl+R', 'Ctrl+Shift+I', 'Ctrl+Shift+J', 'Ctrl+U'];
        this.blockedEvents = ['contextmenu', 'keydown', 'keyup', 'mousedown', 'dragstart', 'selectstart'];
        this.suspiciousActions = 0;
        this.maxSuspiciousActions = 10;
        this.lockDuration = 300000; // 5分钟
        this.originalContent = '';
        this.decoyContent = this.generateDecoyContent();
        this.isCheckingIntegrity = false; // 防止递归调用
        this.isHandlingSuspiciousAction = false; // 防止递归调用
        this.originalConsoleWarn = console.warn; // 保存原始的console.warn方法
        
        this.init();
    }

    init() {
        this.setupEventBlockers();
        this.setupKeyboardShortcuts();
        this.setupContentProtection();
        this.setupDevToolsDetection();
        this.setupCopyProtection();
        this.setupPrintProtection();
        this.setupScreenshotProtection();
        
        console.log('[安全事件] 安全事件管理器已初始化');
    }

    // 设置事件阻止器
    setupEventBlockers() {
        // 阻止右键菜单
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleSuspiciousAction('contextmenu');
            return false;
        });

        // 阻止文本选择
        document.addEventListener('selectstart', (e) => {
            if (this.securityLevel !== 'low') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('select');
                return false;
            }
        });

        // 阻止拖拽
        document.addEventListener('dragstart', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleSuspiciousAction('drag');
            return false;
        });

        // 阻止特定鼠标操作
        document.addEventListener('mousedown', (e) => {
            // 检测是否是开发者工具的快捷键组合
            if (e.button === 2 || (e.button === 0 && e.ctrlKey && e.shiftKey)) {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('mouse_dev_tools');
                return false;
            }
        });

        // 阻止双击选择
        document.addEventListener('dblclick', (e) => {
            if (this.securityLevel === 'high') {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        });
    }

    // 设置键盘快捷键阻止
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            const key = e.key;
            const ctrl = e.ctrlKey || e.metaKey;
            const shift = e.shiftKey;
            const alt = e.altKey;

            // 阻止F12开发者工具
            if (key === 'F12') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('f12');
                this.showSecurityWarning('开发者工具已被禁用');
                return false;
            }

            // 阻止Ctrl+Shift+I/C/J (开发者工具快捷键)
            if (ctrl && shift && (key === 'I' || key === 'C' || key === 'J')) {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('dev_tools_shortcut');
                this.showSecurityWarning('开发者工具快捷键已被禁用');
                return false;
            }

            // 阻止Ctrl+U (查看源码)
            if (ctrl && key === 'u') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('view_source');
                this.showSecurityWarning('查看源码已被禁用');
                return false;
            }

            // 阻止Ctrl+S (保存)
            if (ctrl && key === 's') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('save');
                this.showSecurityWarning('保存功能已被禁用');
                return false;
            }

            // 阻止Ctrl+P (打印)
            if (ctrl && key === 'p') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('print');
                this.showSecurityWarning('打印功能已被禁用');
                return false;
            }

            // 阻止F5刷新 (在高安全级别)
            if (this.securityLevel === 'high' && key === 'F5') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('refresh');
                return false;
            }

            // 阻止Ctrl+R刷新
            if (ctrl && key === 'r') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('refresh');
                return false;
            }

            // 阻止Ctrl+A全选
            if (ctrl && key === 'a' && this.securityLevel === 'high') {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }

            // 阻止Ctrl+C/V/X (复制/粘贴/剪切)
            if (ctrl && (key === 'c' || key === 'v' || key === 'x') && this.securityLevel === 'high') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('copy_paste');
                return false;
            }
        });
    }

    // 设置内容保护
    setupContentProtection() {
        // 保存原始内容
        this.originalContent = document.documentElement.outerHTML;

        // 监控DOM变化
        this.mutationObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    this.checkContentIntegrity();
                }
            });
        });

        this.mutationObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeOldValue: true
        });

        // 定期检查内容完整性
        setInterval(() => {
            this.checkContentIntegrity();
        }, 5000);
    }

    // 设置开发者工具检测
    setupDevToolsDetection() {
        // 检测窗口大小变化
        let originalWidth = window.outerWidth;
        let originalHeight = window.outerHeight;
        
        setInterval(() => {
            const currentWidth = window.outerWidth;
            const currentHeight = window.outerHeight;
            
            // 检测开发者工具打开导致的窗口大小变化
            if (Math.abs(currentWidth - originalWidth) > 200 || 
                Math.abs(currentHeight - originalHeight) > 200) {
                this.handleSuspiciousAction('dev_tools_detected');
                this.showSecurityWarning('检测到开发者工具活动');
            }
            
            originalWidth = currentWidth;
            originalHeight = currentHeight;
        }, 1000);

        // 检测控制台输出
        const originalLog = console.log;
        const originalWarn = console.warn;
        const originalError = console.error;
        const originalInfo = console.info;

        const securityManager = this;
        // 添加页面初始化延迟，避免页面加载时的正常控制台输出触发检测
        let isInitializationComplete = false;
        setTimeout(() => {
            isInitializationComplete = true;
        }, 3000); // 3秒后认为初始化完成

        const checkDevTools = () => {
            // 只有在初始化完成且不在处理可疑操作时才处理控制台访问
            if (isInitializationComplete && !securityManager.isHandlingSuspiciousAction) {
                securityManager.handleSuspiciousAction('console_access');
            }
        };

        console.log = function(...args) {
            checkDevTools();
            return originalLog.apply(console, args);
        };

        console.warn = function(...args) {
            checkDevTools();
            return originalWarn.apply(console, args);
        };

        console.error = function(...args) {
            checkDevTools();
            return originalError.apply(console, args);
        };

        console.info = function(...args) {
            checkDevTools();
            return originalInfo.apply(console, args);
        };

        // 检测开发者工具的另一种方法
        const devtools = {
            open: false,
            orientation: null
        };

        const threshold = 160;
        
        setInterval(() => {
            if (window.outerHeight - window.innerHeight > threshold || 
                window.outerWidth - window.innerWidth > threshold) {
                if (!devtools.open) {
                    devtools.open = true;
                    this.handleSuspiciousAction('dev_tools_open');
                    this.showSecurityWarning('开发者工具已被检测并阻止');
                }
            } else {
                devtools.open = false;
            }
        }, 500);
    }

    // 设置复制保护
    setupCopyProtection() {
        document.addEventListener('copy', (e) => {
            if (this.securityLevel !== 'low') {
                e.preventDefault();
                e.stopPropagation();
                
                // 提供虚假内容
                const fakeContent = this.decoyContent;
                e.clipboardData.setData('text/plain', fakeContent);
                
                this.handleSuspiciousAction('copy');
                this.showSecurityWarning('复制功能已被保护');
                return false;
            }
        });

        document.addEventListener('cut', (e) => {
            if (this.securityLevel !== 'low') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('cut');
                return false;
            }
        });

        document.addEventListener('paste', (e) => {
            if (this.securityLevel === 'high') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('paste');
                return false;
            }
        });
    }

    // 设置打印保护
    setupPrintProtection() {
        window.addEventListener('beforeprint', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleSuspiciousAction('print_attempt');
            this.showSecurityWarning('打印功能已被禁用');
            return false;
        });

        // 重写print方法
        const originalPrint = window.print;
        window.print = function() {
            this.handleSuspiciousAction('print_method');
            this.showSecurityWarning('打印功能已被禁用');
            return false;
        }.bind(this);
    }

    // 设置截图保护
    setupScreenshotProtection() {
        // 检测截图快捷键
        document.addEventListener('keydown', (e) => {
            // Windows截图快捷键
            if (e.key === 'PrintScreen') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('screenshot');
                this.showSecurityWarning('截图功能已被禁用');
                return false;
            }

            // Mac截图快捷键
            if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key >= '3' && e.key <= '4') {
                e.preventDefault();
                e.stopPropagation();
                this.handleSuspiciousAction('screenshot_mac');
                this.showSecurityWarning('截图功能已被禁用');
                return false;
            }
        });

        // 添加CSS防止截图
        const style = document.createElement('style');
        style.textContent = `
            * {
                -webkit-user-select: none !important;
                -moz-user-select: none !important;
                -ms-user-select: none !important;
                user-select: none !important;
                -webkit-touch-callout: none !important;
                -webkit-tap-highlight-color: transparent !important;
            }
            
            body::before {
                content: "截图已禁用";
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                z-index: 999999;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s;
            }
            
            body.screenshot-warning::before {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }

    // 处理可疑操作
    handleSuspiciousAction(action) {
        // 防止递归调用
        if (this.isHandlingSuspiciousAction) {
            return;
        }
        
        this.isHandlingSuspiciousAction = true;
        this.suspiciousActions++;
        
        try {
            // 使用原始的console.warn方法，避免递归调用
            this.originalConsoleWarn(`[安全事件] 检测到可疑操作: ${action} (总计: ${this.suspiciousActions})`);
            
            // 记录到安全日志
            this.logSecurityEvent(action);

            if (this.suspiciousActions >= this.maxSuspiciousActions) {
                this.lockPage();
            } else {
                this.showSecurityWarning(`检测到可疑操作: ${action}`);
            }
        } finally {
            // 确保标志被重置
            this.isHandlingSuspiciousAction = false;
        }
    }

    // 锁定页面
    lockPage() {
        if (this.isLocked) return;
        
        this.isLocked = true;
        document.body.classList.add('screenshot-warning');
        
        // 重定向到锁定页面
        setTimeout(() => {
            window.location.href = '/HTML/locked.html';
        }, 2000);
        
        this.showSecurityWarning('页面已被锁定，正在重定向...');
    }

    // 显示安全警告
    showSecurityWarning(message) {
        // 移除现有警告
        const existingWarning = document.querySelector('.security-warning');
        if (existingWarning) {
            existingWarning.remove();
        }

        // 创建警告元素
        const warning = document.createElement('div');
        warning.className = 'security-warning';
        warning.textContent = message;
        warning.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff4444;
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            z-index: 999999;
            font-family: Arial, sans-serif;
            font-size: 14px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease-out;
        `;

        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(warning);

        // 3秒后自动移除
        setTimeout(() => {
            if (warning.parentNode) {
                warning.remove();
            }
        }, 3000);
    }

    // 检查内容完整性
    checkContentIntegrity() {
        // 防止递归调用
        if (this.isCheckingIntegrity) return;
        this.isCheckingIntegrity = true;
        
        try {
            // 暂时断开MutationObserver以避免递归
            if (this.mutationObserver) {
                this.mutationObserver.disconnect();
            }
            
            // 检查是否有恶意脚本注入
            const scripts = document.querySelectorAll('script');
            scripts.forEach(script => {
                if (script.src && !script.src.includes(window.location.hostname)) {
                    this.handleSuspiciousAction('external_script');
                    script.remove();
                }
            });

            // 检查是否有隐藏的iframe
            const iframes = document.querySelectorAll('iframe');
            iframes.forEach(iframe => {
                if (iframe.style.display === 'none' || iframe.hidden) {
                    this.handleSuspiciousAction('hidden_iframe');
                    iframe.remove();
                }
            });
        } finally {
            this.isCheckingIntegrity = false;
            // 重新连接MutationObserver
            if (this.mutationObserver) {
                this.mutationObserver.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeOldValue: true
                });
            }
        }
    }

    // 生成虚假内容
    generateDecoyContent() {
        return `
MTSCOS AI System - 安全保护已激活
=====================================

警告：此内容受安全保护
未经授权的访问已被记录

系统信息：
- 版本: MTSCOS-AI-v2.0.1
- 安全级别: 高级
- 加密状态: 已启用
- 访问控制: 已激活

联系方式：security@mtscos.ai
        `.trim();
    }

    // 记录安全事件
    logSecurityEvent(action) {
        const event = {
            action: action,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            suspiciousCount: this.suspiciousActions
        };

        // 存储到本地
        const logs = JSON.parse(localStorage.getItem('security_logs') || '[]');
        logs.push(event);
        
        // 只保留最近100条记录
        if (logs.length > 100) {
            logs.shift();
        }
        
        localStorage.setItem('security_logs', JSON.stringify(logs));
    }

    // 设置安全级别
    setSecurityLevel(level) {
        this.securityLevel = level;
        console.log(`[安全事件] 安全级别已设置为: ${level}`);
    }

    // 重置可疑操作计数
    resetSuspiciousCount() {
        this.suspiciousActions = 0;
        console.log('[安全事件] 可疑操作计数已重置');
    }

    // 获取安全状态
    getSecurityStatus() {
        return {
            isLocked: this.isLocked,
            securityLevel: this.securityLevel,
            suspiciousActions: this.suspiciousActions,
            maxSuspiciousActions: this.maxSuspiciousActions,
            blockedKeys: this.blockedKeys,
            blockedEvents: this.blockedEvents
        };
    }

    // 解除锁定
    unlock() {
        this.isLocked = false;
        this.suspiciousActions = 0;
        document.body.classList.remove('screenshot-warning');
        console.log('[安全事件] 页面锁定已解除');
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityEventManager;
} else {
    window.SecurityEventManager = SecurityEventManager;
}
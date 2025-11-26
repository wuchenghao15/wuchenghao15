// VERSION: 20251106.cccfadfcf3db8e91653

// MTSCOS 防盗链与资源保护脚本
// 版本: 2.251031.113000

/**
 * 安全级别配置
 * level: 1-基础保护, 2-中等保护, 3-高级保护
 */
const securityLevel = 3;

/**
 * 允许访问的域名白名单
 */
const allowedDomains = [
    'mtscos.com',
    'www.mtscos.com',
    'login.mtscos.com',
    'api.mtscos.com',
    'localhost',
    '127.0.0.1'
];

/**
 * 初始化防盗链保护
 */
function initAntiHotlink() {
    // 检查是否处于诊断模式
    const isDiagnosticMode = new URLSearchParams(window.location.search).get('diagnostic') === 'true';
    
    // 日志记录函数
    const logSecurityEvent = (eventType, details = '') => {
        if (!isDiagnosticMode) return;
        console.log(`[MTSCOS Security] ${eventType}: ${details}`);
    };
    
    // 1. Referer检查 (级别1及以上)
    if (securityLevel >= 1) {
        checkReferer(logSecurityEvent);
    }
    
    // 2. 右键菜单保护 (级别2及以上)
    if (securityLevel >= 2) {
        protectRightClick(logSecurityEvent);
        disableTextSelection(logSecurityEvent);
    }
    
    // 3. 高级保护措施 (级别3)
    if (securityLevel >= 3) {
        disableCopyPaste(logSecurityEvent);
        detectBrowserConsole(logSecurityEvent);
        preventFrameEmbedding(logSecurityEvent);
        addResourceObfuscation(logSecurityEvent);
        monitorPageVisibility(logSecurityEvent);
    }
    
    // 加载完成后执行的安全检查
    window.addEventListener('load', () => {
        logSecurityEvent('Security System', `Level ${securityLevel} initialized`);
        addSessionTracking();
    });
}

/**
 * 检查Referer头信息
 */
function checkReferer(log) {
    const referer = document.referrer;
    
    if (!referer) {
        // 直接访问允许通过，但记录日志
        log('Direct Access', 'No referer detected');
        return;
    }
    
    try {
        const refererUrl = new URL(referer);
        const refererDomain = refererUrl.hostname;
        
        // 检查是否在白名单中
        const isAllowed = allowedDomains.some(domain => 
            refererDomain === domain || refererDomain.endsWith(`.${domain}`)
        );
        
        if (!isAllowed && !window.location.search.includes('allowed=true')) {
            log('Unauthorized Referer', refererDomain);
            // 显示警告消息
            showWarning('检测到非授权来源访问，请通过官方渠道访问系统。');
        } else {
            log('Allowed Referer', refererDomain);
        }
    } catch (e) {
        log('Invalid Referer', referer);
    }
}

/**
 * 保护右键菜单
 */
function protectRightClick(log) {
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        log('Right Click Blocked', e.target.tagName);
        
        // 可选：显示自定义右键菜单或提示
        showNotification('右键菜单已被禁用，以保护系统安全。');
    });
}

/**
 * 禁用文本选择
 */
function disableTextSelection(log) {
    document.addEventListener('selectstart', (e) => {
        e.preventDefault();
        log('Text Selection Blocked', e.target.tagName);
    });
    
    // 设置CSS防止选择
    const style = document.createElement('style');
    style.textContent = `
        body {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        input, textarea {
            -webkit-user-select: text;
            -moz-user-select: text;
            -ms-user-select: text;
            user-select: text;
        }
    `;
    document.head.appendChild(style);
}

/**
 * 禁用复制粘贴功能
 */
function disableCopyPaste(log) {
    // 禁用复制
    document.addEventListener('copy', (e) => {
        e.preventDefault();
        log('Copy Blocked', e.target.tagName);
        showNotification('复制功能已被限制。');
    });
    
    // 禁用剪切
    document.addEventListener('cut', (e) => {
        e.preventDefault();
        log('Cut Blocked', e.target.tagName);
    });
    
    // 允许粘贴到输入框，但监控其他区域的粘贴
    document.addEventListener('paste', (e) => {
        if (!['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            e.preventDefault();
            log('Paste Blocked', e.target.tagName);
        }
    });
    
    // 防止键盘快捷键
    document.addEventListener('keydown', (e) => {
        // Ctrl+A, Ctrl+C, Ctrl+X, Ctrl+V
        if (e.ctrlKey || e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'a':
                    if (!['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                        e.preventDefault();
                        log('Select All Blocked', e.target.tagName);
                    }
                    break;
                case 'c':
                    e.preventDefault();
                    log('Ctrl+C Blocked', e.target.tagName);
                    break;
                case 'x':
                    e.preventDefault();
                    log('Ctrl+X Blocked', e.target.tagName);
                    break;
                case 'v':
                    if (!['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                        e.preventDefault();
                        log('Ctrl+V Blocked', e.target.tagName);
                    }
                    break;
            }
        }
    });
}

// 全局定时器变量
let performanceMonitorInterval = null;
let sessionTrackingInterval = null;

/**
 * 检测浏览器开发者工具
 */
function detectBrowserConsole(log) {
    let devToolsOpen = false;
    const threshold = 160;
    
    // 检测控制台打开
    const checkDevTools = () => {
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;
        const isDevTools = widthThreshold || heightThreshold;
        
        if (isDevTools && !devToolsOpen) {
            devToolsOpen = true;
            log('Developer Tools Detected', 'Console opened');
            showWarning('检测到开发者工具。出于安全考虑，某些功能可能受到限制。');
        } else if (!isDevTools && devToolsOpen) {
            devToolsOpen = false;
            log('Developer Tools Closed', 'Console closed');
        }
    };
    
    window.addEventListener('resize', checkDevTools);
    
    // 性能监控检测
    performanceMonitorInterval = setInterval(() => {
        const startTime = performance.now();
        // 尝试触发控制台记录
        console.log('Security check');
        console.clear();
        const endTime = performance.now();
        
        // 如果执行时间过长，可能控制台已打开
        if (endTime - startTime > 100) {
            checkDevTools();
        }
    }, 2000);
    
    // 清理函数
    window.addEventListener('beforeunload', () => {
        if (performanceMonitorInterval) {
            clearInterval(performanceMonitorInterval);
            performanceMonitorInterval = null;
        }
        if (sessionTrackingInterval) {
            clearInterval(sessionTrackingInterval);
            sessionTrackingInterval = null;
        }
    });
}

/**
 * 防止页面被iframe嵌入
 */
function preventFrameEmbedding(log) {
    if (window !== window.top) {
        log('Frame Embedding Detected', window.top.location.href);
        // 重定向到顶级窗口
        window.top.location.href = window.location.href;
        showWarning('禁止在iframe中嵌入本页面。');
    }
    
    // 设置X-Frame-Options
    const meta = document.createElement('meta');
    meta.httpEquiv = 'X-Frame-Options';
    meta.content = 'DENY';
    document.head.appendChild(meta);
}

/**
 * 添加资源混淆保护
 */
function addResourceObfuscation(log) {
    // 监控图片加载
    document.addEventListener('DOMContentLoaded', () => {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            // 添加防盗链检查
            img.addEventListener('error', () => {
                log('Image Load Error', img.src);
                img.src = '';
                img.alt = '资源无法加载';
            });
        });
    });
    
    // 混淆CSS和JS资源路径
    const obfuscateResourcePath = (path) => {
        return path + '?v=' + Date.now();
    };
    
    // 动态修改资源URL以防止缓存攻击
    document.querySelectorAll('link[rel="stylesheet"], script[src]').forEach(el => {
        if (el.hasAttribute('data-no-obfuscate')) return;
        
        if (el.tagName === 'LINK') {
            el.href = obfuscateResourcePath(el.href);
        } else if (el.tagName === 'SCRIPT') {
            el.src = obfuscateResourcePath(el.src);
        }
    });
}

/**
 * 监控页面可见性变化
 */
function monitorPageVisibility(log) {
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            log('Page Hidden', 'User switched tabs');
            // 可选：暂停敏感操作
            pauseSensitiveOperations();
        } else {
            log('Page Visible', 'User returned to tab');
            // 可选：验证会话
            verifySession();
        }
    });
}

/**
 * 添加会话跟踪
 */
function addSessionTracking() {
    // 生成会话ID
    const sessionId = generateSessionId();
    localStorage.setItem('mtscos_session', sessionId);
    
    // 记录页面停留时间
    let startTime = Date.now();
    
    const updateSessionTime = () => {
        const currentTime = Date.now();
        const elapsed = Math.floor((currentTime - startTime) / 1000);
        // 可以将此信息发送到服务器
        if (elapsed > 3600) { // 每小时重置
            startTime = currentTime;
            // 刷新会话
            localStorage.setItem('mtscos_session', generateSessionId());
        }
    };
    
    sessionTrackingInterval = setInterval(updateSessionTime, 60000); // 每分钟更新
}

/**
 * 生成唯一会话ID
 */
function generateSessionId() {
    return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * 暂停敏感操作
 */
function pauseSensitiveOperations() {
    // 可以在这里实现暂停自动保存、验证等功能
}

/**
 * 验证会话
 */
function verifySession() {
    const sessionId = localStorage.getItem('mtscos_session');
    if (!sessionId) {
        showNotification('会话已过期，请刷新页面。');
    }
}

/**
 * 显示警告消息
 */
function showWarning(message) {
    const warningDiv = document.createElement('div');
    warningDiv.className = 'security-warning';
    warningDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #f8d7da;
        color: #721c24;
        padding: 12px 16px;
        border-radius: 4px;
        border: 1px solid #f5c6cb;
        z-index: 9999;
        max-width: 300px;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    `;
    warningDiv.textContent = message;
    
    document.body.appendChild(warningDiv);
    
    setTimeout(() => {
        warningDiv.remove();
    }, 5000);
}

/**
 * 显示通知消息
 */
function showNotification(message) {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'security-notification';
    notificationDiv.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        z-index: 9999;
        font-size: 13px;
        animation: fadeInOut 2s ease-in-out;
    `;
    notificationDiv.textContent = message;
    
    document.body.appendChild(notificationDiv);
    
    setTimeout(() => {
        notificationDiv.remove();
    }, 2000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes fadeInOut {
        0%, 100% { opacity: 0; }
        20%, 80% { opacity: 1; }
    }
`;
document.head.appendChild(style);

// 初始化防盗链系统
document.addEventListener('DOMContentLoaded', initAntiHotlink);

// 导出函数供其他模块使用
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = {
        initAntiHotlink,
        checkReferer,
        protectRightClick,
        disableTextSelection,
        disableCopyPaste
    };
}

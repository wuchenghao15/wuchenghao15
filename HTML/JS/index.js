// 全局错误处理增强，捕获详细的错误信息
window.addEventListener('error', function(e) {
    console.error('捕获到错误:', e.error);
    console.error('错误文件:', e.filename);
    console.error('错误行号:', e.lineno);
    console.error('错误列号:', e.colno);
    // 记录错误到错误日志系统
    if (typeof window.reportError === 'function') {
        window.reportError(e.error);
    }
});

// 强制最大化页面功能
(function() {
    // 存储原始窗口大小和位置
    let originalWindowState = {
        width: window.innerWidth,
        height: window.innerHeight,
        left: window.screenLeft,
        top: window.screenTop
    };
    
    // 检查是否可以操作窗口
    const canManipulateWindow = () => {
        // 只有在顶层窗口并且不是iframe中才能操作
        return window.top === window && window.self === window.top;
    };
    
    // 强制最大化窗口
    const forceMaximizeWindow = () => {
        if (!canManipulateWindow()) return;
        
        try {
            // 获取屏幕的可用尺寸（减去任务栏等）
            const screenWidth = window.screen.availWidth;
            const screenHeight = window.screen.availHeight;
            
            // 最大化窗口
            window.moveTo(0, 0);
            window.resizeTo(screenWidth, screenHeight);
            
            console.log('[窗口控制] 页面已强制最大化');
        } catch (error) {
            console.warn('[窗口控制] 无法强制最大化窗口:', error);
        }
    };
    
    // 恢复原始窗口大小
    window.restoreOriginalWindowSize = () => {
        if (!canManipulateWindow()) return;
        
        try {
            window.moveTo(originalWindowState.left, originalWindowState.top);
            window.resizeTo(originalWindowState.width, originalWindowState.height);
            console.log('[窗口控制] 窗口已恢复到原始大小');
        } catch (error) {
            console.warn('[窗口控制] 无法恢复原始窗口大小:', error);
        }
    };
    
    // 监听窗口大小变化，强制恢复最大化
    window.addEventListener('resize', () => {
        // 检查窗口是否已经是最大化状态
        const isMaximized = window.innerWidth === window.screen.availWidth && 
                           window.innerHeight === window.screen.availHeight;
        
        if (!isMaximized) {
            // 延迟执行，避免频繁触发
            setTimeout(forceMaximizeWindow, 100);
        }
    });
    
    // 页面加载完成后强制最大化
    window.addEventListener('load', () => {
        // 延迟执行，确保页面完全加载
        setTimeout(forceMaximizeWindow, 500);
    });
    
    // 当用户退出系统时恢复原始窗口大小
    window.addEventListener('beforeunload', () => {
        // 可以在这里调用恢复函数，但通常浏览器会阻止窗口大小的改变
        // 如果需要，系统可以提供一个退出按钮，点击时调用window.restoreOriginalWindowSize()
    });
})();

// 自动主题系统初始化
window.addEventListener('DOMContentLoaded', function() {
    // 初始化自动主题管理器
    setTimeout(() => {
        if (window.autoThemeManager) {
            console.log('[主题] 自动主题管理器已启动');
        }
    }, 500);
});

// 安全机制初始化 - 延迟初始化确保所有脚本都已加载
window.addEventListener('load', function() {
    // 给额外时间让所有defer脚本完全加载
    setTimeout(() => {
        initializeSecurityModules();
    }, 500);
});

// 安全模块初始化函数
function initializeSecurityModules() {
    try {
        console.log('[安全] 开始初始化安全模块...');
        
        // 增加等待时间，确保所有脚本完全加载
        setTimeout(() => {
            // 检查必需的类是否已加载
            const requiredClasses = [
                'SessionManager',
                'EncryptionManager', 
                'SecurityEventManager',
                'DataSecurityManager',
                'TokenVerificationManager'
            ];
            
            const missingClasses = requiredClasses.filter(className => {
                const isAvailable = typeof window[className] !== 'undefined';
                if (!isAvailable) {
                    console.error(`[安全] 缺少必需类: ${className}`);
                }
                return !isAvailable;
            });
            
            if (missingClasses.length > 0) {
                console.warn(`[安全] 部分安全类尚未加载: ${missingClasses.join(', ')}`);
                console.log('[安全] 跳过安全模块初始化，继续使用基础功能');
                return; // 不再抛出错误，直接返回
            }
            
            // 初始化会话管理器
            if (typeof SessionManager !== 'undefined') {
                window.sessionManager = new SessionManager();
                console.log('[安全] 会话管理器已初始化');
            }
            
            // 初始化加密管理器
            if (typeof EncryptionManager !== 'undefined') {
                window.encryptionManager = new EncryptionManager();
                console.log('[安全] 加密管理器已初始化');
            }
            
            // 初始化安全事件管理器
            if (typeof SecurityEventManager !== 'undefined') {
                window.securityEventManager = new SecurityEventManager();
                console.log('[安全] 安全事件管理器已初始化');
            }
            
            // 初始化数据安全管理器
            if (typeof DataSecurityManager !== 'undefined') {
                window.dataSecurityManager = new DataSecurityManager();
                console.log('[安全] 数据安全管理器已初始化');
            }
            
            // 初始化令牌验证管理器
            if (typeof TokenVerificationManager !== 'undefined') {
                window.tokenVerificationManager = new TokenVerificationManager();
                console.log('[安全] 令牌验证管理器已初始化');
            }
            
            // 启动安全监控
            setTimeout(() => {
                if (window.sessionManager) {
                    window.sessionManager.startMonitoring();
                }
                if (window.securityEventManager) {
                    window.securityEventManager.startMonitoring();
                }
                console.log('[安全] 安全监控已启动');
            }, 1000);
            
            console.log('[安全] 所有安全模块初始化完成');
            
        }, 2000); // 增加等待时间到2秒
        
    } catch (error) {
        console.error('[安全] 安全模块初始化失败:', error);
        console.log('[安全] 将在基础模式下运行，不会重定向');
        // 移除重定向逻辑，允许页面继续使用
    }
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    try {
        if (window.sessionManager) {
            window.sessionManager.destroy();
        }
        if (window.dataSecurityManager) {
            window.dataSecurityManager.lockAllData();
        }
    } catch (error) {
        console.error('[安全] 页面卸载清理失败:', error);
    }
});

// 清理输入，防止XSS攻击
function sanitizeInput(input) {
    return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// 应用于表单提交前的验证
window.addEventListener('DOMContentLoaded', function() {
    document.getElementById('login-form')?.addEventListener('submit', (e) => {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const captcha = document.getElementById('captcha').value;
        
        // 简单的XSS防护示例
        if (username !== sanitizeInput(username) || 
            password !== sanitizeInput(password) || 
            captcha !== sanitizeInput(captcha)) {
            alert('输入内容包含不安全字符');
            e.preventDefault();
        }
    });
});

console.log('CSS样式已加载');
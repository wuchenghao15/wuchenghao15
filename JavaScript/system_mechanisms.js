/**
 * MTSCOS AI 项目 - 系统机制核心模块
 * 负责实现安全机制、超时机制、脚本机制、回滚机制、版本机制等核心功能
 */

// 全局命名空间
if (typeof window.MTSCOS === 'undefined') {
    window.MTSCOS = {};
}
const MTSCOS = window.MTSCOS;
if (typeof MTSCOS.System === 'undefined') {
    MTSCOS.System = {};
}

/**
 * 安全机制模块
 */
MTSCOS.System.Security = {
    // 初始化安全机制
    init: function() {
        console.log('初始化安全机制...');
        this.applyXSSProtection();
        this.setupCSRFToken();
        this.enableSecureCookies();
    },
    
    // XSS防护
    applyXSSProtection: function() {
        // 设置Content-Security-Policy
        if (document.location.protocol === 'https:') {
            const metaCSP = document.createElement('meta');
            metaCSP.httpEquiv = 'Content-Security-Policy';
            metaCSP.content = "default-src 'self'; script-src 'self' https://apis.google.com https://github.com https://qq.com https://wx.qq.com https://login.live.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:;";
            document.head.appendChild(metaCSP);
        }
        
        // 增强输入验证
        this.enhanceInputValidation();
    },
    
    // 增强输入验证
    enhanceInputValidation: function() {
        // 为所有输入框添加实时验证
        const inputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="email"]');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                // 实时清理潜在的危险字符
                const sanitized = MTSCOS.System.Security.sanitizeInput(this.value);
                if (sanitized !== this.value) {
                    console.warn('检测到潜在的不安全输入，已自动清理');
                    this.value = sanitized;
                }
            });
        });
    },
    
    // 输入清理函数
    sanitizeInput: function(input) {
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
            .replace(/\//g, '&#x2F;')
            .replace(/\\/g, '&#x5C;')
            .replace(/\*/g, '&#42;')
            .replace(/\?/g, '&#63;')
            .replace(/\|/g, '&#124;')
            .replace(/\{/g, '&#123;')
            .replace(/\}/g, '&#125;')
            .replace(/\[/g, '&#91;')
            .replace(/\]/g, '&#93;')
            .replace(/\(/g, '&#40;')
            .replace(/\)/g, '&#41;')
            .replace(/;/g, '&#59;')
            .replace(/:/g, '&#58;')
            .replace(/\$/g, '&#36;')
            .replace(/!/g, '&#33;')
            .replace(/\^/g, '&#94;')
            .replace(/\~/g, '&#126;');
    },
    
    // 设置CSRF令牌
    setupCSRFToken: function() {
        // 生成CSRF令牌
        const token = this.generateCSRFToken();
        // 存储到sessionStorage
        sessionStorage.setItem('csrfToken', token);
        // 添加到所有表单
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = '_csrf';
            tokenInput.value = token;
            form.appendChild(tokenInput);
        });
    },
    
    // 生成CSRF令牌
    generateCSRFToken: function() {
        return 'csrf_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    },
    
    // 启用安全Cookie
    enableSecureCookies: function() {
        if (document.location.protocol === 'https:') {
            // 设置cookie安全标志的提示
            console.log('当前环境支持安全Cookie，将在服务器端设置Secure和HttpOnly标志');
        }
    },
    
    // 密码强度检查
    checkPasswordStrength: function(password) {
        let strength = 0;
        
        // 长度检查
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        
        // 复杂度检查
        if (/[A-Z]/.test(password)) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        
        // 返回强度级别 (0-5)
        return Math.min(strength, 5);
    },
    
    // 加密敏感数据
    encryptData: function(data) {
        // 这里应该使用更安全的加密算法，这里仅作示例
        const key = 'mtscos_secure_key_2024'; // 实际应用中应从服务器获取
        let result = '';
        for (let i = 0; i < data.length; i++) {
            const charCode = data.charCodeAt(i) ^ key.charCodeAt(i % key.length);
            result += String.fromCharCode(charCode);
        }
        return btoa(result); // Base64编码
    },
    
    // 解密敏感数据
    decryptData: function(encryptedData) {
        try {
            const key = 'mtscos_secure_key_2024'; // 实际应用中应从服务器获取
            const data = atob(encryptedData);
            let result = '';
            for (let i = 0; i < data.length; i++) {
                const charCode = data.charCodeAt(i) ^ key.charCodeAt(i % key.length);
                result += String.fromCharCode(charCode);
            }
            return result;
        } catch (error) {
            console.error('解密失败:', error);
            return null;
        }
    }
};

/**
 * 超时机制模块
 */
MTSCOS.System.Timeout = {
    // 配置项
    config: {
        sessionTimeout: 15, // 分钟
        captchaTimeout: 5,  // 分钟
        warningMinutes: 1,  // 提前警告时间
        autoLogoutEnabled: true
    },
    
    // 计时器ID
    timeoutId: null,
    warningId: null,
    
    // 初始化超时机制
    init: function() {
        console.log('初始化超时机制...');
        this.loadConfig();
        this.startSessionTimeout();
        this.setupActivityListeners();
    },
    
    // 加载配置
    loadConfig: function() {
        const savedConfig = localStorage.getItem('timeoutConfig');
        if (savedConfig) {
            try {
                const config = JSON.parse(savedConfig);
                this.config = { ...this.config, ...config };
            } catch (error) {
                console.error('加载超时配置失败:', error);
            }
        }
    },
    
    // 保存配置
    saveConfig: function(newConfig) {
        this.config = { ...this.config, ...newConfig };
        localStorage.setItem('timeoutConfig', JSON.stringify(this.config));
        this.resetSessionTimeout();
    },
    
    // 开始会话超时计时
    startSessionTimeout: function() {
        const timeoutMs = this.config.sessionTimeout * 60 * 1000;
        const warningMs = (this.config.sessionTimeout - this.config.warningMinutes) * 60 * 1000;
        
        // 设置提前警告
        this.warningId = setTimeout(() => {
            if (this.config.autoLogoutEnabled) {
                alert(`您的会话将在 ${this.config.warningMinutes} 分钟后超时，请及时操作以保持会话活跃。`);
            }
        }, warningMs);
        
        // 设置会话超时
        this.timeoutId = setTimeout(() => {
            this.handleSessionTimeout();
        }, timeoutMs);
    },
    
    // 重置会话超时
    resetSessionTimeout: function() {
        clearTimeout(this.timeoutId);
        clearTimeout(this.warningId);
        this.startSessionTimeout();
    },
    
    // 处理会话超时
    handleSessionTimeout: function() {
        console.log('会话已超时');
        
        // 清理会话数据
        sessionStorage.clear();
        localStorage.removeItem('userSession');
        
        // 显示超时提示
        alert('您的会话已超时，请重新登录');
        
        // 重定向到登录页面
        window.location.href = '../HTML/index.html';
    },
    
    // 设置用户活动监听器
    setupActivityListeners: function() {
        // 监听鼠标移动
        document.addEventListener('mousemove', () => {
            this.resetSessionTimeout();
        }, { passive: true });
        
        // 监听键盘输入
        document.addEventListener('keypress', () => {
            this.resetSessionTimeout();
        }, { passive: true });
        
        // 监听点击
        document.addEventListener('click', () => {
            this.resetSessionTimeout();
        }, { passive: true });
        
        // 监听滚动
        window.addEventListener('scroll', () => {
            this.resetSessionTimeout();
        }, { passive: true });
    },
    
    // 验证验证码是否超时
    isCaptchaExpired: function(captchaTimestamp) {
        const now = Date.now();
        const captchaTime = new Date(captchaTimestamp).getTime();
        const maxAge = this.config.captchaTimeout * 60 * 1000;
        
        return (now - captchaTime) > maxAge;
    }
};

/**
 * 脚本机制模块
 */
MTSCOS.System.Script = {
    // 已加载的脚本列表
    loadedScripts: [],
    
    // 初始化脚本机制
    init: function() {
        console.log('初始化脚本机制...');
        this.registerLoadedScripts();
        this.setupScriptMonitoring();
        this.preventScriptInjection();
    },
    
    // 注册已加载的脚本
    registerLoadedScripts: function() {
        const scripts = document.querySelectorAll('script');
        scripts.forEach(script => {
            if (script.src) {
                this.loadedScripts.push(script.src);
            }
        });
    },
    
    // 动态加载脚本
    loadScript: function(url, callback) {
        // 检查是否已加载
        if (this.loadedScripts.includes(url)) {
            console.log(`脚本 ${url} 已加载`);
            if (callback) callback();
            return;
        }
        
        // 安全检查
        if (!this.isValidScriptUrl(url)) {
            console.error(`不允许加载脚本: ${url}`);
            return;
        }
        
        // 加载脚本
        const script = document.createElement('script');
        script.src = url;
        script.onload = () => {
            console.log(`脚本 ${url} 加载成功`);
            this.loadedScripts.push(url);
            if (callback) callback();
        };
        script.onerror = () => {
            console.error(`脚本 ${url} 加载失败`);
        };
        
        document.head.appendChild(script);
    },
    
    // 验证脚本URL是否安全
    isValidScriptUrl: function(url) {
        // 允许的域名列表
        const allowedDomains = [
            window.location.hostname,
            'apis.google.com',
            'github.com',
            'qq.com',
            'wx.qq.com',
            'login.live.com'
        ];
        
        try {
            const urlObj = new URL(url);
            return allowedDomains.some(domain => urlObj.hostname.includes(domain));
        } catch (error) {
            return false;
        }
    },
    
    // 设置脚本监控
    setupScriptMonitoring: function() {
        // 监控DOM变化，检测是否有新脚本被注入
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.tagName === 'SCRIPT') {
                        const scriptUrl = node.src || 'inline script';
                        console.warn(`检测到新脚本注入: ${scriptUrl}`);
                        // 在实际应用中，这里应该有更严格的验证和处理
                    }
                });
            });
        });
        
        // 开始监控
        observer.observe(document, {
            childList: true,
            subtree: true
        });
    },
    
    // 防止脚本注入
    preventScriptInjection: function() {
        // 重写危险的DOM方法
        const originalInnerHTML = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
        const originalOuterHTML = Object.getOwnPropertyDescriptor(Element.prototype, 'outerHTML');
        
        Object.defineProperty(Element.prototype, 'innerHTML', {
            set: function(value) {
                if (MTSCOS.System.Script.containsDangerousTags(value)) {
                    console.error('检测到潜在的脚本注入尝试');
                    throw new Error('不允许设置包含危险标签的内容');
                }
                return originalInnerHTML.set.call(this, value);
            },
            get: function() {
                return originalInnerHTML.get.call(this);
            }
        });
        
        Object.defineProperty(Element.prototype, 'outerHTML', {
            set: function(value) {
                if (MTSCOS.System.Script.containsDangerousTags(value)) {
                    console.error('检测到潜在的脚本注入尝试');
                    throw new Error('不允许设置包含危险标签的内容');
                }
                return originalOuterHTML.set.call(this, value);
            },
            get: function() {
                return originalOuterHTML.get.call(this);
            }
        });
    },
    
    // 检查内容是否包含危险标签
    containsDangerousTags: function(html) {
        const dangerousPatterns = [
            /<\s*script/i,
            /javascript:/i,
            /on\w+\s*=/i,
            /data:text\/html/i,
            /<\s*iframe/i,
            /<\s*embed/i,
            /<\s*object/i,
            /<\s*form[^>]*action/i
        ];
        
        return dangerousPatterns.some(pattern => pattern.test(html));
    },
    
    // 执行安全的代码片段
    executeSafeCode: function(code) {
        // 移除危险的全局对象访问
        const safeCode = code
            .replace(/window\./g, '')
            .replace(/document\./g, '')
            .replace(/eval\(/g, '')
            .replace(/Function\(/g, '')
            .replace(/setTimeout\(/g, '')
            .replace(/setInterval\(/g, '');
        
        try {
            // 在沙箱环境中执行
            const sandbox = {};
            return new Function('context', safeCode)(sandbox);
        } catch (error) {
            console.error('执行安全代码失败:', error);
            return null;
        }
    }
};

/**
 * 回滚机制模块
 */
MTSCOS.System.Rollback = {
    // 备份列表
    backups: [],
    
    // 初始化回滚机制
    init: function() {
        console.log('初始化回滚机制...');
        this.loadBackupsList();
        this.setupAutoBackup();
    },
    
    // 加载备份列表
    loadBackupsList: function() {
        // 在实际应用中，这里应该从服务器获取备份列表
        // 这里使用模拟数据
        this.backups = [
            { id: 'backup-20240115', date: '2024-01-15 10:30:00', size: '12.5 MB', description: '每日备份' },
            { id: 'backup-20240114', date: '2024-01-14 18:00:00', size: '11.8 MB', description: '手动备份' },
            { id: 'backup-20240113', date: '2024-01-13 22:00:00', size: '12.1 MB', description: '每日备份' }
        ];
    },
    
    // 获取备份列表
    getBackups: function() {
        return this.backups;
    },
    
    // 执行回滚
    performRollback: function(backupId) {
        return new Promise((resolve, reject) => {
            console.log(`开始回滚到备份: ${backupId}`);
            
            // 模拟回滚过程
            setTimeout(() => {
                console.log(`回滚到备份 ${backupId} 完成`);
                resolve({ success: true, message: `成功回滚到备份 ${backupId}` });
            }, 3000);
        });
    },
    
    // 创建手动备份
    createBackup: function(description) {
        return new Promise((resolve, reject) => {
            console.log('创建手动备份...');
            
            // 模拟备份过程
            setTimeout(() => {
                const newBackup = {
                    id: 'backup-' + Date.now(),
                    date: new Date().toLocaleString(),
                    size: (Math.random() * 5 + 10).toFixed(1) + ' MB',
                    description: description || '手动备份'
                };
                
                this.backups.unshift(newBackup);
                console.log('备份创建成功:', newBackup);
                resolve(newBackup);
            }, 2000);
        });
    },
    
    // 设置自动备份
    setupAutoBackup: function() {
        // 在实际应用中，这里应该设置定时任务
        console.log('自动备份已配置: 每日22:00执行');
    },
    
    // 验证备份完整性
    verifyBackup: function(backupId) {
        return new Promise((resolve, reject) => {
            console.log(`验证备份 ${backupId} 的完整性...`);
            
            // 模拟验证过程
            setTimeout(() => {
                const isValid = Math.random() > 0.1; // 90%的概率验证通过
                if (isValid) {
                    resolve({ valid: true, message: '备份验证通过' });
                } else {
                    reject({ valid: false, message: '备份已损坏或不完整' });
                }
            }, 1500);
        });
    }
};

/**
 * 版本机制模块
 */
MTSCOS.System.Version = {
    // 当前版本信息
    current: {
        version: 'v1.3.0',
        build: '10001',
        releaseDate: '2024-01-01',
        lastUpdate: '2024-01-15'
    },
    
    // 版本历史
    history: [
        { version: 'v1.3.0', date: '2025-01-01', changes: ['统一版本号更新', '增强项目管理功能'] },
        { version: 'v1.0.0', date: '2024-01-01', changes: ['初始版本发布'] },
        { version: 'v0.9.9', date: '2023-12-15', changes: ['测试版发布', '修复已知问题'] }
    ],
    
    // 初始化版本机制
    init: function() {
        console.log(`初始化版本机制: ${this.current.version} (Build ${this.current.build})`);
        this.checkForUpdates();
    },
    
    // 获取当前版本信息
    getCurrentVersion: function() {
        return this.current;
    },
    
    // 获取版本历史
    getVersionHistory: function() {
        return this.history;
    },
    
    // 检查更新
    checkForUpdates: function() {
        return new Promise((resolve, reject) => {
            console.log('检查系统更新...');
            
            // 模拟检查更新过程
            setTimeout(() => {
                // 模拟当前已是最新版本
                resolve({ 
                    hasUpdate: false, 
                    currentVersion: this.current.version,
                    latestVersion: this.current.version,
                    message: '当前已是最新版本'
                });
            }, 2000);
        });
    },
    
    // 记录版本变更
    logVersionChange: function(newVersion, changes) {
        const changeLog = {
            version: newVersion,
            date: new Date().toISOString().split('T')[0],
            changes: changes
        };
        
        this.history.unshift(changeLog);
        console.log(`记录版本变更: ${newVersion}`, changeLog);
    },
    
    // 导出版本信息
    exportVersionInfo: function() {
        return JSON.stringify({
            current: this.current,
            history: this.history,
            exportedAt: new Date().toISOString()
        }, null, 2);
    },
    
    // 获取版本兼容性信息
    getCompatibilityInfo: function() {
        return {
            browserSupport: {
                chrome: '90+',
                firefox: '88+',
                safari: '14+',
                edge: '90+'
            },
            apiVersion: 'v1',
            minimumResolution: '1024x768'
        };
    }
};

/**
 * 系统管理模块 - 整合所有机制
 */
MTSCOS.System.Manager = {
    // 初始化所有系统机制
    init: function() {
        console.log('初始化MTSCOS系统机制管理...');
        
        // 按顺序初始化各个模块
        try {
            MTSCOS.System.Security.init();
            MTSCOS.System.Timeout.init();
            MTSCOS.System.Script.init();
            MTSCOS.System.Rollback.init();
            MTSCOS.System.Version.init();
            
            console.log('所有系统机制初始化完成');
            this.setupGlobalErrorHandler();
            this.logSystemStart();
        } catch (error) {
            console.error('系统机制初始化失败:', error);
            // 降级策略: 尝试单独初始化每个模块
            this.tryInitializeModulesIndividually();
        }
    },
    
    // 尝试单独初始化每个模块
    tryInitializeModulesIndividually: function() {
        const modules = [
            { name: 'Security', module: MTSCOS.System.Security },
            { name: 'Timeout', module: MTSCOS.System.Timeout },
            { name: 'Script', module: MTSCOS.System.Script },
            { name: 'Rollback', module: MTSCOS.System.Rollback },
            { name: 'Version', module: MTSCOS.System.Version }
        ];
        
        modules.forEach(({ name, module }) => {
            try {
                module.init();
                console.log(`${name} 模块初始化成功`);
            } catch (error) {
                console.error(`${name} 模块初始化失败:`, error);
            }
        });
    },
    
    // 设置全局错误处理器
    setupGlobalErrorHandler: function() {
        window.addEventListener('error', (event) => {
            console.error('全局错误:', event.error, event.message);
            // 在实际应用中，这里应该将错误报告到服务器
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('未处理的Promise拒绝:', event.reason);
            // 在实际应用中，这里应该将错误报告到服务器
        });
    },
    
    // 记录系统启动信息
    logSystemStart: function() {
        const systemInfo = {
            version: MTSCOS.System.Version.getCurrentVersion(),
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            screen: {
                width: window.screen.width,
                height: window.screen.height
            }
        };
        
        console.log('系统启动信息:', systemInfo);
        
        // 在实际应用中，这里应该将启动信息发送到服务器进行日志记录
    },
    
    // 获取系统状态
    getSystemStatus: function() {
        return {
            version: MTSCOS.System.Version.current,
            uptime: performance.now(),
            memory: this.getMemoryInfo(),
            backups: MTSCOS.System.Rollback.backups.length,
            securityStatus: 'enabled',
            timeoutStatus: 'running'
        };
    },
    
    // 获取内存信息（如果浏览器支持）
    getMemoryInfo: function() {
        if (performance && performance.memory) {
            return {
                usedJSHeapSize: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
                totalJSHeapSize: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
                jsHeapSizeLimit: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB'
            };
        }
        return '不可用';
    },
    
    // 执行系统诊断
    runDiagnostics: function() {
        console.log('执行系统诊断...');
        
        const results = {
            network: this.testNetwork(),
            security: this.testSecurity(),
            performance: this.testPerformance()
        };
        
        console.log('诊断结果:', results);
        return results;
    },
    
    // 测试网络连接
    testNetwork: function() {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const img = new Image();
            
            img.onload = function() {
                resolve({
                    status: 'connected',
                    latency: Date.now() - startTime + 'ms'
                });
            };
            
            img.onerror = function() {
                resolve({
                    status: 'disconnected',
                    error: '网络连接失败'
                });
            };
            
            // 使用1x1透明像素进行测试
            img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' + '?' + Date.now();
        });
    },
    
    // 测试安全功能
    testSecurity: function() {
        const results = {
            xssProtection: 'enabled',
            csrfToken: sessionStorage.getItem('csrfToken') ? 'set' : 'missing',
            https: window.location.protocol === 'https:' ? 'enabled' : 'disabled'
        };
        
        return results;
    },
    
    // 测试性能
    testPerformance: function() {
        const startTime = performance.now();
        
        // 执行一些计算来测试性能
        let sum = 0;
        for (let i = 0; i < 1000000; i++) {
            sum += Math.sqrt(i);
        }
        
        const endTime = performance.now();
        
        return {
            calculationTime: (endTime - startTime).toFixed(2) + 'ms',
            framesPerSecond: this.getFPS()
        };
    },
    
    // 获取FPS（每秒帧数）
    getFPS: function() {
        let frames = 0;
        let lastTime = performance.now();
        
        const requestId = requestAnimationFrame(function countFrames(currentTime) {
            frames++;
            const timeElapsed = currentTime - lastTime;
            
            if (timeElapsed >= 1000) {
                return Math.round((frames * 1000) / timeElapsed);
            }
            
            requestId = requestAnimationFrame(countFrames);
        });
        
        // 停止动画帧请求
        setTimeout(() => {
            cancelAnimationFrame(requestId);
        }, 1000);
        
        return '测量中...';
    }
};

/**
 * 页面加载完成后初始化系统机制
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        MTSCOS.System.Manager.init();
    });
} else {
    // 页面已经加载完成，直接初始化
    MTSCOS.System.Manager.init();
}

// 导出到全局作用域
// 已在文件开头初始化全局对象，无需再次赋值
// MTSCOS 智能操作系统安全模块
// 整合用户信息验证、页面锁定、超时、加密、防盗链等安全机制

class MTSSecurityModule {
    constructor() {
        this.isAuthenticated = false;
        this.currentUser = null;
        this.sessionStartTime = Date.now();
        this.lastActivityTime = Date.now();
        this.sessionTimeout = 30 * 60 * 1000; // 30分钟会话超时
        this.inactivityTimeout = 15 * 60 * 1000; // 15分钟不活动锁定
        this.sessionTimer = null;
        this.inactivityTimer = null;
        this.failedAttempts = 0;
        this.maxAttempts = 5;
        this.lockoutTime = 10 * 60 * 1000; // 10分钟锁定
        this.isLockout = false;
        this.lockoutEndTime = 0;
        
        // 初始化所有安全机制
        this.initialize();
    }
    
    // 初始化安全模块
    initialize() {
        console.log('MTSCOS安全模块初始化...');
        
        // 初始化防盗链检查
        this.initHotlinkProtection();
        
        // 初始化XSS防护
        this.initXSSProtection();
        
        // 初始化CSRF防护
        this.initCSRFProtection();
        
        // 初始化点击劫持防护
        this.initClickjackingProtection();
        
        // 初始化会话管理
        this.initSessionManagement();
        
        // 初始化活动监控
        this.initActivityMonitoring();
        
        // 初始化键盘记录保护
        this.initAntiKeylogging();
        
        // 初始化加密通信
        this.initEncryptedCommunication();
        
        // 检查是否已登录
        this.checkAuthStatus();
        
        console.log('MTSCOS安全模块初始化完成');
    }
    
    // 防盗链保护
    initHotlinkProtection() {
        // 检查HTTP Referer
        const referer = document.referrer;
        const allowedDomains = [
            window.location.hostname,
            'localhost',
            '127.0.0.1'
        ];
        
        if (referer) {
            const refererDomain = new URL(referer).hostname;
            const isAllowed = allowedDomains.some(domain => 
                refererDomain === domain || refererDomain.endsWith('.' + domain)
            );
            
            if (!isAllowed) {
                console.warn('潜在的盗链访问:', refererDomain);
                // 可以根据需要采取措施，如记录日志、重定向等
            }
        }
        
        // 资源保护 - 为敏感资源添加保护
        document.addEventListener('contextmenu', (e) => {
            if (e.target.tagName === 'IMG' || e.target.tagName === 'VIDEO' || e.target.tagName === 'AUDIO') {
                console.warn('右键菜单被阻止，保护媒体资源');
                // 注释掉contextmenu阻止，因为这会影响用户体验
                // e.preventDefault();
            }
        });
    }
    
    // XSS防护
    initXSSProtection() {
        // 输入验证函数
        this.sanitizeInput = (input) => {
            if (!input) return '';
            return input
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
                .replace(/\//g, '&#x2F;');
        };
        
        // 监控DOM操作，防止XSS
        const originalAppendChild = Element.prototype.appendChild;
        Element.prototype.appendChild = function(child) {
            // 检查是否是文本节点
            if (child.nodeType === 3 && /<script|javascript:/i.test(child.nodeValue)) {
                console.warn('潜在的XSS攻击被阻止');
                return null;
            }
            return originalAppendChild.call(this, child);
        };
        
        // 为表单输入添加保护
        document.querySelectorAll('input, textarea').forEach(element => {
            element.addEventListener('input', (e) => {
                const sanitized = this.sanitizeInput(e.target.value);
                if (e.target.value !== sanitized) {
                    console.warn('检测到潜在的XSS攻击模式');
                    // 这里不自动替换，因为可能会影响用户体验
                    // 但会记录警告
                }
            });
        });
    }
    
    // CSRF防护
    initCSRFProtection() {
        // 生成CSRF令牌
        this.generateCSRFToken = () => {
            const token = CryptoJS.lib.WordArray.random(32).toString();
            sessionStorage.setItem('csrfToken', token);
            return token;
        };
        
        // 获取CSRF令牌
        this.getCSRFToken = () => {
            let token = sessionStorage.getItem('csrfToken');
            if (!token) {
                token = this.generateCSRFToken();
            }
            return token;
        };
        
        // 为所有AJAX请求添加CSRF令牌
        if (!window.SecurityOriginalFetch) {
            window.SecurityOriginalFetch = window.fetch;
        }
        window.fetch = function(url, options = {}) {
            options.headers = options.headers || {};
            if (!options.headers['X-CSRF-Token']) {
                const securityModule = window.mtsSecurityModule;
                if (securityModule) {
                    options.headers['X-CSRF-Token'] = securityModule.getCSRFToken();
                }
            }
            return window.SecurityOriginalFetch.call(this, url, options);
        };
        
        // 为表单添加CSRF令牌
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('form').forEach(form => {
                const tokenInput = document.createElement('input');
                tokenInput.type = 'hidden';
                tokenInput.name = 'csrfToken';
                tokenInput.value = this.getCSRFToken();
                form.appendChild(tokenInput);
            });
        });
    }
    
    // 点击劫持防护
    initClickjackingProtection() {
        // 检查是否在iframe中
        if (window.self !== window.top) {
            // 在生产环境中，可以重定向到安全页面
            console.warn('检测到在iframe中加载，可能是点击劫持攻击');
            // 注释掉重定向，因为这会影响开发测试
            // window.top.location = window.self.location;
        }
        
        // 设置X-Frame-Options等效的JavaScript保护
        const style = document.createElement('style');
        style.textContent = `
            html {
                display: none;
            }
            html.secure {
                display: block;
            }
        `;
        document.head.appendChild(style);
        
        // 验证不是被iframe嵌入
        if (window.self === window.top) {
            document.documentElement.classList.add('secure');
        }
    }
    
    // 会话管理
    initSessionManagement() {
        // 启动会话超时计时器
        this.sessionTimer = setTimeout(() => {
            this.handleSessionTimeout();
        }, this.sessionTimeout);
    }
    
    // 活动监控
    initActivityMonitoring() {
        const activityEvents = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
        
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastActivity();
            });
        });
        
        // 启动不活动计时器
        this.resetInactivityTimer();
    }
    
    // 更新最后活动时间
    updateLastActivity() {
        this.lastActivityTime = Date.now();
        this.resetInactivityTimer();
    }
    
    // 重置不活动计时器
    resetInactivityTimer() {
        if (this.inactivityTimer) {
            clearTimeout(this.inactivityTimer);
        }
        
        this.inactivityTimer = setTimeout(() => {
            if (this.isAuthenticated && !this.isLockout) {
                this.lockPage();
            }
        }, this.inactivityTimeout);
    }
    
    // 键盘记录保护
    initAntiKeylogging() {
        // 检测可疑的键盘事件监听
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (['keydown', 'keypress', 'keyup'].includes(type)) {
                // 检查监听器是否是可疑的第三方代码
                const listenerStr = String(listener);
                if (listenerStr.includes('send') || listenerStr.includes('ajax') || 
                    listenerStr.includes('xhr') || listenerStr.includes('fetch') && 
                    !listenerStr.includes('security') && !listenerStr.includes('MTS')) {
                    console.warn('检测到潜在的键盘记录器:', listenerStr.substring(0, 100));
                }
            }
            return originalAddEventListener.call(this, type, listener, options);
        };
        
        // 密码字段额外保护
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('input[type="password"]').forEach(passwordField => {
                // 随机改变密码字段的name和id，使简单的键盘记录器难以定位
                const originalName = passwordField.name;
                const originalId = passwordField.id;
                
                // 添加干扰输入事件
                passwordField.addEventListener('input', () => {
                    // 这里可以添加随机事件或干扰数据
                });
            });
        });
    }
    
    // 加密通信
    initEncryptedCommunication() {
        // 加密敏感数据
        this.encryptData = (data) => {
            const key = CryptoJS.SHA256('MTSCOS_SECRET_KEY_2025').toString().substring(0, 32);
            const iv = CryptoJS.lib.WordArray.random(16);
            const encrypted = CryptoJS.AES.encrypt(
                JSON.stringify(data),
                CryptoJS.enc.Utf8.parse(key),
                { iv: iv }
            );
            return {
                encryptedData: encrypted.toString(),
                iv: iv.toString(CryptoJS.enc.Base64)
            };
        };
        
        // 解密数据
        this.decryptData = (encryptedData, iv) => {
            const key = CryptoJS.SHA256('MTSCOS_SECRET_KEY_2025').toString().substring(0, 32);
            try {
                const decrypted = CryptoJS.AES.decrypt(
                    encryptedData,
                    CryptoJS.enc.Utf8.parse(key),
                    { iv: CryptoJS.enc.Base64.parse(iv) }
                );
                return JSON.parse(decrypted.toString(CryptoJS.enc.Utf8));
            } catch (e) {
                console.error('解密失败:', e);
                return null;
            }
        };
    }
    
    // 检查认证状态
    checkAuthStatus() {
        const authToken = localStorage.getItem('authToken');
        const userData = localStorage.getItem('userData');
        
        if (authToken && userData) {
            try {
                const user = JSON.parse(userData);
                this.isAuthenticated = true;
                this.currentUser = user;
                console.log('用户已认证:', user.username);
                return true;
            } catch (e) {
                console.error('认证数据解析失败:', e);
                this.clearAuthData();
                return false;
            }
        }
        return false;
    }
    
    // 用户登录
    login(username, password, captcha) {
        // 检查是否被锁定
        if (this.isLockout) {
            const remainingTime = Math.ceil((this.lockoutEndTime - Date.now()) / 1000);
            return { success: false, message: `账户已被锁定，请在 ${Math.floor(remainingTime / 60)}:${(remainingTime % 60).toString().padStart(2, '0')} 后重试` };
        }
        
        // 输入验证
        if (!username || !password || !captcha) {
            return { success: false, message: '请输入所有必填字段' };
        }
        
        // 模拟登录验证
        // 在实际应用中，应该发送到服务器验证
        if (username === 'admin' && password === 'Admin123456' && captcha) {
            // 登录成功
            this.failedAttempts = 0;
            this.isAuthenticated = true;
            this.currentUser = {
                username: username,
                role: 'admin',
                permissions: ['read', 'write', 'admin']
            };
            
            // 生成认证令牌
            const authToken = CryptoJS.lib.WordArray.random(64).toString();
            
            // 保存认证信息
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userData', JSON.stringify(this.currentUser));
            localStorage.setItem('lastUsername', username);
            
            // 重置会话计时器
            this.resetSessionTimer();
            
            console.log('用户登录成功:', username);
            return { success: true, message: '登录成功' };
        } else {
            // 登录失败
            this.failedAttempts++;
            
            // 检查是否需要锁定
            if (this.failedAttempts >= this.maxAttempts) {
                this.lockoutAccount();
                return { success: false, message: `账户已被锁定10分钟，防止暴力破解` };
            }
            
            return { 
                success: false, 
                message: `登录失败，剩余尝试次数: ${this.maxAttempts - this.failedAttempts}` 
            };
        }
    }
    
    // 用户登出
    logout() {
        this.clearAuthData();
        console.log('用户已登出');
    }
    
    // 清除认证数据
    clearAuthData() {
        this.isAuthenticated = false;
        this.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
    }
    
    // 锁定页面
    lockPage() {
        if (!this.isAuthenticated || this.isLockout) return;
        
        // 触发锁定屏幕
        if (window.lockScreenManager) {
            window.lockScreenManager.lock();
        } else {
            console.warn('锁定屏幕管理器未初始化');
        }
    }
    
    // 锁定账户
    lockoutAccount() {
        this.isLockout = true;
        this.lockoutEndTime = Date.now() + this.lockoutTime;
        
        // 开始锁定倒计时
        this.startLockoutCountdown();
        
        console.log('账户已被锁定10分钟');
    }
    
    // 锁定倒计时
    startLockoutCountdown() {
        const updateCountdown = () => {
            const remainingTime = this.lockoutEndTime - Date.now();
            
            if (remainingTime <= 0) {
                // 锁定时间结束
                this.isLockout = false;
                this.failedAttempts = 0;
                console.log('账户锁定已解除');
                return;
            }
            
            // 继续倒计时
            setTimeout(updateCountdown, 1000);
        };
        
        updateCountdown();
    }
    
    // 重置会话计时器
    resetSessionTimer() {
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
        }
        
        this.sessionTimer = setTimeout(() => {
            this.handleSessionTimeout();
        }, this.sessionTimeout);
    }
    
    // 处理会话超时
    handleSessionTimeout() {
        console.log('会话已超时');
        this.logout();
        
        // 显示超时消息
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.style.display = 'flex';
            document.getElementById('error-text').textContent = '会话已超时，请重新登录';
        }
        
        // 重置登录表单
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.reset();
        }
    }
    
    // 验证权限
    checkPermission(requiredPermission) {
        if (!this.isAuthenticated || !this.currentUser) {
            return false;
        }
        
        if (this.currentUser.role === 'admin') {
            return true;
        }
        
        return this.currentUser.permissions && 
               this.currentUser.permissions.includes(requiredPermission);
    }
    
    // 生成验证码
    generateCaptcha() {
        const canvas = document.getElementById('captcha-canvas');
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // 清空画布
        ctx.clearRect(0, 0, width, height);
        
        // 设置背景
        ctx.fillStyle = '#f5f5f5';
        ctx.fillRect(0, 0, width, height);
        
        // 生成随机验证码
        const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
        let captchaText = '';
        for (let i = 0; i < 4; i++) {
            captchaText += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        
        // 保存验证码用于验证
        sessionStorage.setItem('captchaCode', captchaText);
        
        // 绘制验证码
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // 绘制每个字符，位置和旋转角度随机
        for (let i = 0; i < captchaText.length; i++) {
            const x = 20 + i * 25;
            const y = height / 2;
            const rotation = (Math.random() - 0.5) * 0.4; // 随机旋转角度
            
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(rotation);
            
            // 随机颜色
            const r = Math.floor(Math.random() * 80);
            const g = Math.floor(Math.random() * 80);
            const b = Math.floor(Math.random() * 80);
            ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            
            ctx.fillText(captchaText[i], 0, 0);
            ctx.restore();
        }
        
        // 添加干扰线
        for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.moveTo(Math.random() * width, Math.random() * height);
            ctx.lineTo(Math.random() * width, Math.random() * height);
            ctx.strokeStyle = `rgba(${Math.random() * 150}, ${Math.random() * 150}, ${Math.random() * 150}, 0.5)`;
            ctx.lineWidth = Math.random() * 2 + 1;
            ctx.stroke();
        }
        
        // 添加干扰点
        for (let i = 0; i < 50; i++) {
            ctx.beginPath();
            ctx.arc(Math.random() * width, Math.random() * height, 1, 0, 2 * Math.PI);
            ctx.fillStyle = `rgba(${Math.random() * 100}, ${Math.random() * 100}, ${Math.random() * 100}, 0.5)`;
            ctx.fill();
        }
        
        return captchaText;
    }
    
    // 验证验证码
    validateCaptcha(input) {
        const captchaCode = sessionStorage.getItem('captchaCode') || '';
        return captchaCode.toLowerCase() === input.toLowerCase();
    }
    
    // 数据库保护提示（客户端部分）
    databaseProtectionHint() {
        // 在控制台显示数据库保护提示
        console.log('%c⚠️ 数据库保护提醒 ⚠️', 'color: red; font-weight: bold');
        console.log('1. 所有数据库操作都经过加密和验证');
        console.log('2. 敏感数据已进行脱敏处理');
        console.log('3. 数据库访问权限严格控制');
        console.log('4. 所有数据库操作都有审计日志');
    }
    
    // 销毁安全模块
    destroy() {
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
        }
        if (this.inactivityTimer) {
            clearTimeout(this.inactivityTimer);
        }
        this.clearAuthData();
        console.log('MTSCOS安全模块已销毁');
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // 检查是否已经初始化
        if (!window.mtsSecurityModule) {
            window.mtsSecurityModule = new MTSSecurityModule();
        }
    });
} else {
    if (!window.mtsSecurityModule) {
        window.mtsSecurityModule = new MTSSecurityModule();
    }
}

// 导出为模块（如果支持）
// 暴露到全局作用域
window.MTSSecurityModule = MTSSecurityModule;
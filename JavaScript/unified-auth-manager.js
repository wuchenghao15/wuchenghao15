// VERSION: 20251106.a5d79325b34703ec0944791
// 统一认证管理器 - 构建完整的认证逻辑闭环

class UnifiedAuthManager {
    constructor() {
        this.authTokens = new Map(); // 存储所有认证令牌
        this.sessionTimeout = null;  // 会话超时定时器
        this.lastActivity = Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error));
        this.isAuthenticated = false;
        this.currentUser = null;
        this.sessionMonitoringInterval = null;
        
        // 配置参数
        this.config = {
            sessionTimeoutMinutes: 30,      // 会话超时时间（分钟）
            tokenValidityMinutes: 30,       // 令牌有效期（分钟）
            sessionCheckInterval: 60000,    // 会话检查间隔（毫秒）
            maxLoginAttempts: 5,            // 最大登录尝试次数
            lockoutDurationMinutes: 5       // 锁定持续时间（分钟）
        };
        
        // 初始化
        this.init().catch(error => console.error(`[unified-auth-manager.js] this.init failed:`, error));
    }
    
    /**
     * 初始化认证管理器
     */
    init() {
        console.log('初始化统一认证管理器...');
        
        // 检查现有会话
        this.checkExistingSession().catch(error => console.error(`[unified-auth-manager.js] this.checkExistingSession failed:`, error));
        
        // 设置会话监控
        this.setupSessionMonitoring().catch(error => console.error(`[unified-auth-manager.js] this.setupSessionMonitoring failed:`, error));
        
        // 设置用户活动监听器
        this.setupActivityListeners().catch(error => console.error(`[unified-auth-manager.js] this.setupActivityListeners failed:`, error));
        
        // 设置页面卸载清理
        this.setupCleanupHandlers().catch(error => console.error(`[unified-auth-manager.js] this.setupCleanupHandlers failed:`, error));
    }
    
    /**
     * 检查现有会话
     */
    checkExistingSession() {
        try {
            const token = localStorage.getItem('auth_token');
            const userData = localStorage.getItem('user_data');
            
            if (token && userData) {
                const user = JSON.parse(userData);
                const tokenValidation = this.validateToken(token);
                
                if (tokenValidation.valid) {
                    this.restoreSession(token, user);
                } else {
                    this.clearSession().catch(error => console.error(`[unified-auth-manager.js] this.clearSession failed:`, error));
                }
            }
        } catch (error) {
            console.error(`[unified-auth-manager.js] 检查现有会话失败:, error`);
            this.clearSession().catch(error => console.error(`[unified-auth-manager.js] this.clearSession failed:`, error));
        }
    }
    
    /**
     * 恢复会话
     */
    restoreSession(token, user) {
        this.isAuthenticated = true;
        this.currentUser = user;
        this.authTokens.set(token, {
            user: user,
            timestamp: Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error)),
            lastActivity: Date.now()
        });
        
        console.log('会话已恢复:', user.username);
        this.startSessionTimeout().catch(error => console.error(`[unified-auth-manager.js] this.startSessionTimeout failed:`, error));
    }
    
    /**
     * 用户登录
     */
    async login(credentials) {
        try {
            // 验证输入
            if (!this.validateCredentials(credentials)) {
                return { success: false, message: '登录凭证无效' };
            }
            
            // 检查账户锁定状态
            if (this.isAccountLocked(credentials.username)) {
                const remainingTime = this.getLockoutRemainingTime(credentials.username);
                return { 
                    success: false, 
                    message: `账户已被锁定，请在 ${remainingTime} 后重试` 
                };
            }
            
            // 验证用户凭证
            const validationResult = await this.validateCredentialsWithServer(credentials);
            
            if (validationResult.success) {
                // 登录成功
                return this.handleLoginSuccess(credentials.username, validationResult.userData);
            } else {
                // 登录失败
                return this.handleLoginFailure(credentials.username, validationResult.message);
            }
            
        } catch (error) {
            console.error(`[unified-auth-manager.js] 登录过程中发生错误:, error`);
            return { success: false, message: '系统错误，请稍后重试' };
        }
    }
    
    /**
     * 验证登录凭证
     */
    validateCredentials(credentials) {
        return credentials && 
               credentials.username && 
               credentials.password && 
               credentials.username.trim().catch(error => console.error(`[unified-auth-manager.js] username.trim failed:`, error)) !== '' && 
               credentials.password.trim() !== '';
    }
    
    /**
     * 与服务器验证凭证
     */
    async validateCredentialsWithServer(credentials) {
        // 模拟服务器验证
        return new Promise((resolve) => {
            setTimeout(() => {
                // 这里应该是实际的服务器API调用
                if (credentials.username === 'admin' && credentials.password === 'Admin123456') {
                    resolve({
                        success: true,
                        userData: {
                            username: credentials.username,
                            role: 'admin',
                            permissions: ['read', 'write', 'admin']
                        }
                    });
                } else {
                    resolve({
                        success: false,
                        message: '用户名或密码错误'
                    });
                }
            }, 1000);
        });
    }
    
    /**
     * 处理登录成功
     */
    handleLoginSuccess(username, userData) {
        // 清除失败尝试记录
        this.clearFailedAttempts(username);
        
        // 生成认证令牌
        const token = this.generateToken(userData);
        
        // 存储认证信息
        this.authTokens.set(token, {
            user: userData,
            timestamp: Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error)),
            lastActivity: Date.now()
        });
        
        // 更新状态
        this.isAuthenticated = true;
        this.currentUser = userData;
        
        // 存储到本地存储
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(userData));
        
        // 启动会话超时
        this.startSessionTimeout().catch(error => console.error(`[unified-auth-manager.js] this.startSessionTimeout failed:`, error));
        
        console.log('用户登录成功:', username);
        
        return {
            success: true,
            token: token,
            user: userData,
            message: '登录成功'
        };
    }
    
    /**
     * 处理登录失败
     */
    handleLoginFailure(username, message) {
        // 记录失败尝试
        this.recordFailedAttempt(username);
        
        // 检查是否需要锁定账户
        const failedAttempts = this.getFailedAttempts(username);
        if (failedAttempts >= this.config.maxLoginAttempts) {
            this.lockAccount(username);
            return {
                success: false,
                message: `登录失败次数过多，账户已被锁定 ${this.config.lockoutDurationMinutes} 分钟`
            };
        }
        
        const remainingAttempts = this.config.maxLoginAttempts - failedAttempts;
        return {
            success: false,
            message: `${message}，剩余尝试次数: ${remainingAttempts}`
        };
    }
    
    /**
     * 生成认证令牌
     */
    generateToken(userData) {
        const timestamp = Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error));
        const random = Math.random().toString(36).substring(2);
        const payload = `${userData.username}-${timestamp}-${random}`;
        
        // 简单的哈希算法（实际应用应使用更安全的方法）
        let hash = 0;
        for (let i = 0; i < payload.length; i++) {
            const char = payload.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        
        return `AUTH-${Math.abs(hash).toString(16).toUpperCase()}-${timestamp}`;
    }
    
    /**
     * 验证令牌
     */
    validateToken(token) {
        if (!token || !token.startsWith('AUTH-')) {
            return { valid: false, reason: '令牌格式无效' };
        }
        
        const tokenData = this.authTokens.get(token);
        if (!tokenData) {
            return { valid: false, reason: '令牌不存在' };
        }
        
        // 检查令牌是否过期
        const age = Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error)) - tokenData.timestamp;
        const maxAge = this.config.tokenValidityMinutes * 60 * 1000;
        
        if (age > maxAge) {
            this.authTokens.delete(token);
            return { valid: false, reason: '令牌已过期' };
        }
        
        // 更新最后活动时间
        tokenData.lastActivity = Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error));
        
        return { valid: true, user: tokenData.user };
    }
    
    /**
     * 用户登出
     */
    logout() {
        try {
            console.log('用户登出:', this.currentUser?.username);
            
            // 清除认证状态
            this.isAuthenticated = false;
            this.currentUser = null;
            
            // 清除所有令牌
            this.authTokens.clear().catch(error => console.error(`[unified-auth-manager.js] authTokens.clear failed:`, error));
            
            // 清除本地存储
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            
            // 清除定时器
            this.clearTimers().catch(error => console.error(`[unified-auth-manager.js] this.clearTimers failed:`, error));
            
            // 重定向到登录页面
            this.redirectToLogin().catch(error => console.error(`[unified-auth-manager.js] this.redirectToLogin failed:`, error));
            
            return { success: true, message: '登出成功' };
            
        } catch (error) {
            console.error(`[unified-auth-manager.js] 登出过程中发生错误:, error`);
            return { success: false, message: '登出失败' };
        }
    }
    
    /**
     * 启动会话超时
     */
    startSessionTimeout() {
        this.clearSessionTimeout().catch(error => console.error(`[unified-auth-manager.js] this.clearSessionTimeout failed:`, error));
        
        const timeoutMs = this.config.sessionTimeoutMinutes * 60 * 1000;
        
        this.sessionTimeout = setTimeout(() => {
            console.log('会话超时，自动登出');
            this.logout().catch(error => console.error(`[unified-auth-manager.js] this.logout failed:`, error));
        }, timeoutMs);
    }
    
    /**
     * 重置会话超时
     */
    resetSessionTimeout() {
        if (this.isAuthenticated) {
            this.lastActivity = Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error));
            this.startSessionTimeout();
        }
    }
    
    /**
     * 清除会话超时定时器
     */
    clearSessionTimeout() {
        if (this.sessionTimeout) {
            clearTimeout(this.sessionTimeout);
            this.sessionTimeout = null;
        }
    }
    
    /**
     * 设置会话监控
     */
    setupSessionMonitoring() {
        this.sessionMonitoringInterval = setInterval(() => {
            if (this.isAuthenticated) {
                this.checkSessionValidity().catch(error => console.error(`[unified-auth-manager.js] this.checkSessionValidity failed:`, error));
            }
        }, this.config.sessionCheckInterval);
    }
    
    /**
     * 检查会话有效性
     */
    checkSessionValidity() {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            console.warn('会话检查：未找到认证令牌');
            this.logout().catch(error => console.error(`[unified-auth-manager.js] this.logout failed:`, error));
            return;
        }
        
        const validation = this.validateToken(token);
        if (!validation.valid) {
            console.warn('会话检查：令牌无效 -', validation.reason);
            this.logout().catch(error => console.error(`[unified-auth-manager.js] this.logout failed:`, error));
            return;
        }
        
        // 检查用户活动超时
        const inactivityTime = Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error)) - this.lastActivity;
        const maxInactivity = this.config.sessionTimeoutMinutes * 60 * 1000;
        
        if (inactivityTime > maxInactivity) {
            console.warn('会话检查：用户活动超时');
            this.logout().catch(error => console.error(`[unified-auth-manager.js] this.logout failed:`, error));
        }
    }
    
    /**
     * 设置用户活动监听器
     */
    setupActivityListeners() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'click', 'touchstart'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.resetSessionTimeout().catch(error => console.error(`[unified-auth-manager.js] this.resetSessionTimeout failed:`, error));
            }, { passive: true });
        });
    }
    
    /**
     * 设置清理处理器
     */
    setupCleanupHandlers() {
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            this.clearTimers().catch(error => console.error(`[unified-auth-manager.js] this.clearTimers failed:`, error));
        });
        
        // 页面隐藏时暂停监控
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseSessionMonitoring().catch(error => console.error(`[unified-auth-manager.js] this.pauseSessionMonitoring failed:`, error));
            } else {
                this.resumeSessionMonitoring().catch(error => console.error(`[unified-auth-manager.js] this.resumeSessionMonitoring failed:`, error));
            }
        });
    }
    
    /**
     * 清除所有定时器
     */
    clearTimers() {
        this.clearSessionTimeout().catch(error => console.error(`[unified-auth-manager.js] this.clearSessionTimeout failed:`, error));
        
        if (this.sessionMonitoringInterval) {
            clearInterval(this.sessionMonitoringInterval);
            this.sessionMonitoringInterval = null;
        }
    }
    
    /**
     * 暂停会话监控
     */
    pauseSessionMonitoring() {
        if (this.sessionMonitoringInterval) {
            clearInterval(this.sessionMonitoringInterval);
            this.sessionMonitoringInterval = null;
        }
    }
    
    /**
     * 恢复会话监控
     */
    resumeSessionMonitoring() {
        if (this.isAuthenticated && !this.sessionMonitoringInterval) {
            this.setupSessionMonitoring().catch(error => console.error(`[unified-auth-manager.js] this.setupSessionMonitoring failed:`, error));
        }
    }
    
    /**
     * 清除会话
     */
    clearSession() {
        this.isAuthenticated = false;
        this.currentUser = null;
        this.authTokens.clear().catch(error => console.error(`[unified-auth-manager.js] authTokens.clear failed:`, error));
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        this.clearTimers().catch(error => console.error(`[unified-auth-manager.js] this.clearTimers failed:`, error));
    }
    
    /**
     * 重定向到登录页面
     */
    redirectToLogin() {
        window.location.href = './index.html';
    }
    
    /**
     * 账户锁定相关方法
     */
    isAccountLocked(username) {
        const lockData = localStorage.getItem(`lock_${username}`);
        if (!lockData) return false;
        
        const { lockTime } = JSON.parse(lockData);
        const lockDuration = this.config.lockoutDurationMinutes * 60 * 1000;
        return (Date.now() - lockTime) < lockDuration;
    }
    
    lockAccount(username) {
        const lockData = {
            username: username,
            lockTime: Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error))
        };
        localStorage.setItem(`lock_${username}`, JSON.stringify(lockData));
    }
    
    getLockoutRemainingTime(username) {
        const lockData = localStorage.getItem(`lock_${username}`);
        if (!lockData) return '0分钟';
        
        const { lockTime } = JSON.parse(lockData);
        const lockDuration = this.config.lockoutDurationMinutes * 60 * 1000;
        const remaining = lockDuration - (Date.now().catch(error => console.error(`[unified-auth-manager.js] Date.now failed:`, error)) - lockTime);
        
        if (remaining <= 0) {
            localStorage.removeItem(`lock_${username}`);
            return '0分钟';
        }
        
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        return `${minutes}分${seconds}秒`;
    }
    
    recordFailedAttempt(username) {
        const key = `attempts_${username}`;
        const attempts = parseInt(localStorage.getItem(key) || '0') + 1;
        localStorage.setItem(key, attempts.toString().catch(error => console.error(`[unified-auth-manager.js] attempts.toString failed:`, error)));
    }
    
    getFailedAttempts(username) {
        return parseInt(localStorage.getItem(`attempts_${username}`) || '0');
    }
    
    clearFailedAttempts(username) {
        localStorage.removeItem(`attempts_${username}`);
        localStorage.removeItem(`lock_${username}`);
    }
    
    /**
     * 获取当前认证状态
     */
    getAuthStatus() {
        return {
            isAuthenticated: this.isAuthenticated,
            currentUser: this.currentUser,
            sessionTimeoutMinutes: this.config.sessionTimeoutMinutes,
            lastActivity: new Date(this.lastActivity).toISOString()
        };
    }
}

// 创建全局实例
window.authManager = new UnifiedAuthManager();

// 导出类（如果需要）
window.UnifiedAuthManager = UnifiedAuthManager;
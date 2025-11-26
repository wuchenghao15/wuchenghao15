// VERSION: 20251106.a5d79325b34703ec0944791
// 统一认证管理器 - 构建完整的认证逻辑闭环

// 确保VikeyMockAPI已加载
if (typeof window.VikeyMockAPI === 'undefined') {
    console.warn('VikeyMockAPI未加载，将使用模拟实现');
    // 这里可以添加备用逻辑或尝试动态加载
}

class UnifiedAuthManager {
    constructor() {
        this.authTokens = new Map(); // 存储所有认证令牌
        this.authSessionTimeout = null;  // 会话超时定时器
        this.lastActivity = Date.now();
        this.isAuthenticated = false;
        this.currentUser = null;
        this.sessionMonitoringInterval = null;
        this.vikeyAPI = null; // Vikey API 实例
        
        // 配置参数
        this.config = {
            sessionTimeoutMinutes: 30,      // 会话超时时间（分钟）
            tokenValidityMinutes: 30,       // 令牌有效期（分钟）
            sessionCheckInterval: 60000,    // 会话检查间隔（毫秒）
            maxLoginAttempts: 5,            // 最大登录尝试次数
            lockoutDurationMinutes: 5,      // 锁定持续时间（分钟）
            useVikeyAuth: true              // 是否使用Vikey认证
        };
        
        // 初始化
        this.init().catch(error => console.error(`[unified-auth-manager.js] this.init failed:`, error));
    }
    
    /**
     * 初始化认证管理器
     */
    init() {
        console.log('初始化统一认证管理器...');
        
        // 初始化Vikey API
        this.initVikeyAPI();
        
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
     * 初始化Vikey API
     */
    initVikeyAPI() {
        try {
            if (window.VikeyMockAPI) {
                this.vikeyAPI = new window.VikeyMockAPI();
                console.log('VikeyMockAPI已成功初始化');
            } else {
                console.warn('VikeyMockAPI不可用，Vikey认证功能将被禁用');
                this.config.useVikeyAuth = false;
            }
        } catch (error) {
            console.error('初始化Vikey API失败:', error);
            this.config.useVikeyAuth = false;
        }
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
            timestamp: Date.now(),
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
            
            // 检查是否需要Vikey认证
            if (this.config.useVikeyAuth && this.vikeyAPI && credentials.useVikey) {
                // 执行Vikey认证
                const vikeyResult = await this.performVikeyAuth(credentials.username);
                
                if (!vikeyResult.success) {
                    return {
                        success: false,
                        message: vikeyResult.message || 'Vikey认证失败'
                    };
                }
                
                console.log('Vikey认证成功，继续登录流程');
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
     * 执行Vikey认证
     */
    async performVikeyAuth(username) {
        try {
            console.log(`开始Vikey认证流程，用户: ${username}`);
            
            // 检查Vikey设备连接状态
            const status = await this.vikeyAPI.checkVikeyStatus();
            
            if (status !== this.vikeyAPI.Status.READY) {
                return {
                    success: false,
                    message: 'Vikey设备未连接或未准备就绪'
                };
            }
            
            // 执行Vikey验证
            const verifyResult = await this.vikeyAPI.verifyVikey();
            
            if (!verifyResult.success) {
                return {
                    success: false,
                    message: verifyResult.message || 'Vikey验证失败'
                };
            }
            
            // 读取Vikey设备信息
            const deviceInfo = await this.vikeyAPI.readVikeyInfo();
            
            if (!deviceInfo.success) {
                return {
                    success: false,
                    message: '读取Vikey设备信息失败'
                };
            }
            
            console.log('Vikey设备信息:', deviceInfo.data);
            
            // 验证设备与用户的绑定关系（在实际应用中，这应该在服务器端完成）
            if (this.isVikeyBoundToUser(deviceInfo.data, username)) {
                return {
                    success: true,
                    message: 'Vikey认证成功',
                    deviceInfo: deviceInfo.data
                };
            } else {
                return {
                    success: false,
                    message: 'Vikey设备未绑定到当前用户'
                };
            }
            
        } catch (error) {
            console.error('Vikey认证过程中发生错误:', error);
            return {
                success: false,
                message: `Vikey认证错误: ${error.message || '未知错误'}`
            };
        }
    }
    
    /**
     * 验证Vikey设备是否绑定到用户（模拟实现）
     */
    isVikeyBoundToUser(deviceInfo, username) {
        // 在实际应用中，这应该通过服务器API验证设备ID与用户的绑定关系
        // 这里为了演示，我们简单地检查用户名是否为管理员
        return username === 'admin' || deviceInfo.deviceId === 'MOCK-DEVICE-001';
    }
    
    /**
     * 验证登录凭证
     */
    validateCredentials(credentials) {
        // 如果使用Vikey认证，可能不需要密码
        if (credentials && credentials.useVikey && this.config.useVikeyAuth && this.vikeyAPI) {
            return credentials.username && credentials.username.trim().catch(error => console.error(`[unified-auth-manager.js] username.trim failed:`, error)) !== '';
        }
        
        // 常规登录需要用户名和密码
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
            timestamp: Date.now(),
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
        const timestamp = Date.now();
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
        const age =  - tokenData.timestamp;
        const maxAge = this.config.tokenValidityMinutes * 60 * 1000;
        
        if (age > maxAge) {
            this.authTokens.delete(token);
            return { valid: false, reason: '令牌已过期' };
        }
        
        // 更新最后活动时间
        tokenData.lastActivity = Date.now();
        
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
            this.authTokens.clear();
            
            // 清除本地存储
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            
            // 清除定时器
            this.clearTimers();
            
            // 重定向到登录页面
            this.redirectToLogin();
            
            return { success: true, message: '登出成功' };
            
        } catch (error) {
            console.error(`[unified-auth-manager.js] 登出过程中发生错误:`, error);
            return { success: false, message: '登出失败' };
        }
    }
    
    /**
     * 启动会话超时
     */
    startSessionTimeout() {
        this.clearSessionTimeout();
        
        const timeoutMs = this.config.sessionTimeoutMinutes * 60 * 1000;
        
        this.authSessionTimeout = setTimeout(() => {
            console.log('会话超时，自动登出');
            this.logout();
        }, timeoutMs);
    }
    
    /**
     * 重置会话超时
     */
    resetSessionTimeout() {
        if (this.isAuthenticated) {
            this.lastActivity = Date.now();
            this.startSessionTimeout();
        }
    }
    
    /**
     * 清除会话超时定时器
     */
    clearSessionTimeout() {
        if (this.authSessionTimeout) {
            clearTimeout(this.authSessionTimeout);
            this.authSessionTimeout = null;
        }
    }
    
    /**
     * 设置会话监控
     */
    setupSessionMonitoring() {
        this.sessionMonitoringInterval = setInterval(() => {
            if (this.isAuthenticated) {
                this.checkSessionValidity();
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
            this.logout();
            return;
        }
        
        const validation = this.validateToken(token);
        if (!validation.valid) {
            console.warn('会话检查：令牌无效 -', validation.reason);
            this.logout();
            return;
        }
        
        // 检查用户活动超时
        const inactivityTime = Date.now() - this.lastActivity;
        const maxInactivity = this.config.sessionTimeoutMinutes * 60 * 1000;
        
        if (inactivityTime > maxInactivity) {
            console.warn('会话检查：用户活动超时');
            this.logout();
        }
    }
    
    /**
     * 设置用户活动监听器
     */
    setupActivityListeners() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'click', 'touchstart'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.resetSessionTimeout();
            }, { passive: true });
        });
    }
    
    /**
     * 设置清理处理器
     */
    setupCleanupHandlers() {
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            this.clearTimers();
        });
        
        // 页面隐藏时暂停监控
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseSessionMonitoring();
            } else {
                this.resumeSessionMonitoring();
            }
        });
    }
    
    /**
     * 清除所有定时器
     */
    clearTimers() {
        this.clearSessionTimeout();
        
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
            this.setupSessionMonitoring();
        }
    }
    
    /**
     * 清除会话
     */
    clearSession() {
        this.isAuthenticated = false;
        this.currentUser = null;
        this.authTokens.clear();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        this.clearTimers();
        
        // 停止Vikey监控
        if (this.vikeyAPI) {
            try {
                this.vikeyAPI.stopMonitoring();
            } catch (error) {
                console.error('停止Vikey监控失败:', error);
            }
        }
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
            lockTime: Date.now()
        };
        localStorage.setItem(`lock_${username}`, JSON.stringify(lockData));
    }
    
    getLockoutRemainingTime(username) {
        const lockData = localStorage.getItem(`lock_${username}`);
        if (!lockData) return '0分钟';
        
        const { lockTime } = JSON.parse(lockData);
        const lockDuration = this.config.lockoutDurationMinutes * 60 * 1000;
        const remaining = lockDuration - (Date.now() - lockTime);
        
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
        localStorage.setItem(key, attempts.toString());
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
            lastActivity: new Date(this.lastActivity).toISOString(),
            vikeyAuthAvailable: this.config.useVikeyAuth && !!this.vikeyAPI
        };
    }
    
    /**
     * 检查Vikey设备是否可用
     */
    async checkVikeyAvailability() {
        if (!this.config.useVikeyAuth || !this.vikeyAPI) {
            return { available: false, reason: 'Vikey认证未启用' };
        }
        
        try {
            const status = await this.vikeyAPI.checkVikeyStatus();
            return {
                available: status === this.vikeyAPI.Status.READY,
                status: status,
                statusText: this.getVikeyStatusText(status)
            };
        } catch (error) {
            console.error('检查Vikey可用性失败:', error);
            return { available: false, reason: error.message || '未知错误' };
        }
    }
    
    /**
     * 获取Vikey状态文本
     */
    getVikeyStatusText(status) {
        const statusMap = {
            0: '未初始化',
            1: '就绪',
            2: '连接中',
            3: '断开连接',
            4: '错误',
            5: '需要更新'
        };
        return statusMap[status] || '未知状态';
    }
}

// 创建全局实例
window.authManager = new UnifiedAuthManager();

// 导出类（如果需要）
window.UnifiedAuthManager = UnifiedAuthManager;
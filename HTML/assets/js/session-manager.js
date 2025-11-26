/**
 * MTSCOS 登录状态管理和会话处理
 * 提供完整的用户会话管理功能
 */

class SessionManager {
    constructor() {
        this.currentUser = null;
        this.sessionData = null;
        this.isInitialized = false;
        this.eventListeners = new Map();
        this.heartbeatInterval = null;
        this.autoRefreshTimer = null;
        
        // 会话配置
        this.config = {
            heartbeatInterval: 30000, // 30秒心跳
            autoRefreshThreshold: 300000, // 5分钟自动刷新
            sessionTimeout: 3600000, // 1小时会话超时
            warningThreshold: 300000, // 5分钟超时警告
        };
        
        this.init();
    }

    /**
     * 初始化会话管理器
     */
    async init() {
        try {
            console.log('[SESSION] 初始化会话管理器');
            
            // 检查现有会话
            await this.checkExistingSession();
            
            // 启动心跳检测
            this.startHeartbeat();
            
            // 启动自动刷新
            this.startAutoRefresh();
            
            this.isInitialized = true;
            console.log('[SESSION] 会话管理器初始化完成');
            
        } catch (error) {
            console.error('[SESSION] 初始化失败:', error);
        }
    }

    /**
     * 检查现有会话
     */
    async checkExistingSession() {
        try {
            const token = localStorage.getItem('accessToken');
            const user = localStorage.getItem('currentUser');
            
            if (token && user) {
                console.log('[SESSION] 发现现有令牌，验证有效性');
                
                // 验证令牌
                const isValid = await loginApiClient.verifyToken();
                
                if (isValid) {
                    this.currentUser = loginApiClient.getCurrentUser();
                    this.sessionData = {
                        token,
                        user: this.currentUser,
                        loginTime: localStorage.getItem('loginTime') || Date.now(),
                        lastActivity: Date.now()
                    };
                    
                    console.log('[SESSION] 现有会话有效');
                    this.emit('sessionRestored', this.currentUser);
                    return true;
                } else {
                    console.log('[SESSION] 现有会话无效，清除数据');
                    this.clearSession();
                }
            }
            
            return false;
        } catch (error) {
            console.error('[SESSION] 检查现有会话失败:', error);
            this.clearSession();
            return false;
        }
    }

    /**
     * 创建新会话
     */
    async createSession(userData) {
        try {
            console.log('[SESSION] 创建新会话');
            
            this.currentUser = userData.user;
            this.sessionData = {
                token: userData.accessToken,
                refreshToken: userData.refreshToken,
                user: userData.user,
                loginTime: Date.now(),
                lastActivity: Date.now(),
                expiresAt: userData.expiresIn ? Date.now() + (userData.expiresIn * 1000) : null
            };
            
            // 保存会话数据
            this.saveSessionData();
            
            // 启动会话管理
            this.startSessionManagement();
            
            console.log('[SESSION] 新会话创建成功');
            this.emit('sessionCreated', this.currentUser);
            
            return true;
        } catch (error) {
            console.error('[SESSION] 创建会话失败:', error);
            return false;
        }
    }

    /**
     * 保存认证数据
     */
    saveSessionData() {
        try {
            if (this.sessionData) {
                localStorage.setItem('accessToken', this.sessionData.token);
                if (this.sessionData.refreshToken) {
                    localStorage.setItem('refreshToken', this.sessionData.refreshToken);
                }
                localStorage.setItem('currentUser', JSON.stringify(this.sessionData.user));
                localStorage.setItem('loginTime', this.sessionData.loginTime.toString());
                localStorage.setItem('lastActivity', this.sessionData.lastActivity.toString());
                if (this.sessionData.expiresAt) {
                    localStorage.setItem('tokenExpiresAt', this.sessionData.expiresAt.toString());
                }
            }
        } catch (error) {
            console.error('[SESSION] 保存认证数据失败:', error);
        }
    }

    /**
     * 清除会话数据
     */
    clearSession() {
        try {
            this.currentUser = null;
            this.sessionData = null;
            
            // 清除本地存储
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('currentUser');
            localStorage.removeItem('loginTime');
            localStorage.removeItem('lastActivity');
            localStorage.removeItem('tokenExpiresAt');
            
            // 停止会话管理
            this.stopSessionManagement();
            
            console.log('[SESSION] 会话数据已清除');
            this.emit('sessionCleared');
        } catch (error) {
            console.error('[SESSION] 清除会话数据失败:', error);
        }
    }

    /**
     * 启动会话管理
     */
    startSessionManagement() {
        this.stopSessionManagement(); // 先停止现有的
        
        // 启动心跳检测
        this.startHeartbeat();
        
        // 启动自动刷新
        this.startAutoRefresh();
        
        // 启动超时检查
        this.startTimeoutCheck();
        
        // 监听用户活动
        this.startActivityTracking();
    }

    /**
     * 停止会话管理
     */
    stopSessionManagement() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.autoRefreshTimer) {
            clearTimeout(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
        
        this.stopActivityTracking();
    }

    /**
     * 启动心跳检测
     */
    startHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        this.heartbeatInterval = setInterval(async () => {
            try {
                if (this.isLoggedIn()) {
                    const success = await loginApiClient.sendHeartbeat();
                    if (success) {
                        this.updateLastActivity();
                        console.log('[SESSION] 心跳检测成功');
                    } else {
                        console.warn('[SESSION] 心跳检测失败，可能需要重新登录');
                        this.handleSessionExpired();
                    }
                }
            } catch (error) {
                console.error('[SESSION] 心跳检测异常:', error);
            }
        }, this.config.heartbeatInterval);
    }

    /**
     * 启动自动刷新
     */
    startAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearTimeout(this.autoRefreshTimer);
        }
        
        const checkAndRefresh = async () => {
            try {
                if (this.isLoggedIn() && loginApiClient.isTokenExpiringSoon(5)) {
                    console.log('[SESSION] 令牌即将过期，自动刷新');
                    const success = await loginApiClient.refreshAccessToken();
                    if (success) {
                        this.sessionData.token = loginApiClient.accessToken;
                        this.sessionData.refreshToken = loginApiClient.refreshToken;
                        this.saveSessionData();
                        console.log('[SESSION] 令牌自动刷新成功');
                    } else {
                        console.warn('[SESSION] 令牌刷新失败');
                        this.handleSessionExpired();
                    }
                }
            } catch (error) {
                console.error('[SESSION] 自动刷新异常:', error);
            }
            
            // 设置下次检查
            this.autoRefreshTimer = setTimeout(checkAndRefresh, this.config.autoRefreshThreshold);
        };
        
        // 启动检查
        this.autoRefreshTimer = setTimeout(checkAndRefresh, this.config.autoRefreshThreshold);
    }

    /**
     * 启动超时检查
     */
    startTimeoutCheck() {
        const checkTimeout = () => {
            if (this.isLoggedIn()) {
                const lastActivity = this.getLastActivity();
                const timeSinceActivity = Date.now() - lastActivity;
                
                if (timeSinceActivity > this.config.sessionTimeout) {
                    console.warn('[SESSION] 会话超时');
                    this.handleSessionExpired();
                }
            }
        };
        
        // 每分钟检查一次
        setInterval(checkTimeout, 60000);
    }

    /**
     * 启动活动跟踪
     */
    startActivityTracking() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        
        this.activityHandler = () => {
            this.updateLastActivity();
        };
        
        events.forEach(event => {
            document.addEventListener(event, this.activityHandler, { passive: true });
        });
    }

    /**
     * 停止活动跟踪
     */
    stopActivityTracking() {
        if (this.activityHandler) {
            const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
            events.forEach(event => {
                document.removeEventListener(event, this.activityHandler);
            });
        }
    }

    /**
     * 更新最后活动时间
     */
    updateLastActivity() {
        if (this.sessionData) {
            this.sessionData.lastActivity = Date.now();
            localStorage.setItem('lastActivity', this.sessionData.lastActivity.toString());
        }
    }

    /**
     * 获取最后活动时间
     */
    getLastActivity() {
        if (this.sessionData && this.sessionData.lastActivity) {
            return this.sessionData.lastActivity;
        }
        return parseInt(localStorage.getItem('lastActivity') || '0');
    }

    /**
     * 处理会话过期
     */
    async handleSessionExpired() {
        console.warn('[SESSION] 处理会话过期');
        
        // 清除会话
        this.clearSession();
        
        // 发出事件
        this.emit('sessionExpired');
        
        // 尝试调用系统锁定机制（如果存在）
        if (window.systemLockManager && typeof window.systemLockManager.lock === 'function') {
            console.warn('[SESSION] 调用系统锁定机制');
            try {
                await window.systemLockManager.lock('session_timeout');
            } catch (error) {
                console.error('[SESSION] 系统锁定失败:', error);
            }
        }
        
        // 直接跳转到登录页，不显示前台提示
        if (!window.location.pathname.includes('login.html')) {
            window.location.href = '../HTML/login.html?reason=session_expired';
        }
    }

    /**
     * 显示会话过期消息
     */
    showSessionExpiredMessage() {
        const message = document.createElement('div');
        message.className = 'session-expired-message';
        message.innerHTML = `
            <div class="message-content">
                <h3>会话已过期</h3>
                <p>您的登录会话已过期，请重新登录</p>
            </div>
        `;
        
        // 添加样式
        message.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            padding: 15px 20px;
            border-radius: 6px;
            border: 1px solid #f5c6cb;
            z-index: 10000;
            max-width: 300px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(message);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 3000);
    }

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return !!(this.currentUser && this.sessionData && this.sessionData.token);
    }

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * 获取会话数据
     */
    getSessionData() {
        return this.sessionData;
    }

    /**
     * 手动登出
     */
    async logout() {
        try {
            console.log('[SESSION] 用户手动登出');
            
            // 调用API登出
            await loginApiClient.logout();
            
            // 清除本地会话
            this.clearSession();
            
            // 发出事件
            this.emit('userLogout');
            
            // 跳转到登录页
            if (!window.location.pathname.includes('login.html')) {
                window.location.href = '../HTML/login.html?reason=logout';
            }
            
        } catch (error) {
            console.error('[SESSION] 登出失败:', error);
            // 即使API调用失败，也要清除本地会话
            this.clearSession();
        }
    }

    /**
     * 强制刷新会话
     */
    async forceRefresh() {
        try {
            console.log('[SESSION] 强制刷新会话');
            
            const success = await loginApiClient.refreshAccessToken();
            if (success) {
                this.sessionData.token = loginApiClient.accessToken;
                this.sessionData.refreshToken = loginApiClient.refreshToken;
                this.saveSessionData();
                this.emit('sessionRefreshed');
                return true;
            } else {
                this.handleSessionExpired();
                return false;
            }
        } catch (error) {
            console.error('[SESSION] 强制刷新失败:', error);
            return false;
        }
    }

    /**
     * 添加事件监听器
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    /**
     * 移除事件监听器
     */
    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 发出事件
     */
    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[SESSION] 事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 获取会话统计信息
     */
    getSessionStats() {
        if (!this.sessionData) {
            return null;
        }
        
        const now = Date.now();
        const loginTime = this.sessionData.loginTime;
        const lastActivity = this.sessionData.lastActivity;
        const sessionDuration = now - loginTime;
        const idleTime = now - lastActivity;
        
        return {
            loginTime: new Date(loginTime).toLocaleString(),
            lastActivity: new Date(lastActivity).toLocaleString(),
            sessionDuration: Math.floor(sessionDuration / 1000 / 60), // 分钟
            idleTime: Math.floor(idleTime / 1000 / 60), // 分钟
            isExpiringSoon: loginApiClient.isTokenExpiringSoon(),
            user: this.currentUser
        };
    }

    /**
     * 销毁会话管理器
     */
    destroy() {
        console.log('[SESSION] 销毁会话管理器');
        this.stopSessionManagement();
        this.eventListeners.clear();
        this.isInitialized = false;
    }
}

// 创建全局会话管理器实例
const sessionManager = new SessionManager();

// 暴露到全局
window.sessionManager = sessionManager;

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}
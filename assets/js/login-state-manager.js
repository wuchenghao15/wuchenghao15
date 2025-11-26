/**
 * 登录状态管理模块
 * 用于管理用户登录状态
 */

class LoginStateManager {
    constructor() {
        this.storageKey = 'mtscos_auth';
        this.sessionKey = 'mtscos_session';
        this.currentAuth = null;
        
        this.init().catch(error => console.error(`[login-state-manager.js] this.init failed:`, error));
    }
    
    /**
     * 初始化
     */
    init() {
        this.loadCurrentAuth().catch(error => console.error(`[login-state-manager.js] this.loadCurrentAuth failed:`, error));
        this.setupSessionMonitoring();
    }
    
    /**
     * 加载当前认证状态
     */
    loadCurrentAuth() {
        try {
            const authData = localStorage.getItem(this.storageKey);
            if (authData) {
                this.currentAuth = JSON.parse(authData);
            }
        } catch (error) {
            console.error(`[login-state-manager.js] 加载认证状态失败:, error`);
            this.currentAuth = null;
        }
    }
    
    /**
     * 保存认证状态
     */
    saveAuthState(authData) {
        try {
            const auth = {
                loginType: authData.loginType || 'password',
                userInfo: authData.userInfo,
                loginTime: new Date().toISOString(),
                sessionId: this.generateSessionId(),
                lastActivity: new Date().toISOString(),
                ...authData
            };
            
            localStorage.setItem(this.storageKey, JSON.stringify(auth));
            sessionStorage.setItem(this.sessionKey, auth.sessionId);
            
            this.currentAuth = auth;
            
            console.log('认证状态已保存:', auth.loginType);
            return true;
        } catch (error) {
            console.error(`[login-state-manager.js] 保存认证状态失败:, error`);
            return false;
        }
    }
    
    /**
     * 设置密码登录状态
     */
    setPasswordLogin(userInfo, credentials = {}) {
        const authData = {
            loginType: 'password',
            userInfo: {
                ...userInfo,
                loginMethod: 'password'
            },
            credentials: {
                username: credentials.username,
                // 不保存密码，只保存用户名
                loginTime: new Date().toISOString()
            }
        };
        
        return this.saveAuthState(authData);
    }
    
    /**
     * 获取当前登录类型
     */
    getLoginType() {
        return this.currentAuth ? this.currentAuth.loginType : null;
    }
    
    /**
     * 检查是否是密码登录
     */
    isPasswordLogin() {
        return this.getLoginType() === 'password';
    }
    
    /**
     * 获取用户信息
     */
    getUserInfo() {
        return this.currentAuth ? this.currentAuth.userInfo : null;
    }
    
    /**
     * 检查登录状态是否有效
     */
    isLoginValid() {
        if (!this.currentAuth) {
            return false;
        }
        
        // 检查会话是否有效
        const sessionId = sessionStorage.getItem(this.sessionKey);
        if (!sessionId || sessionId !== this.currentAuth.sessionId) {
            return false;
        }
        
        // 检查登录时间是否过期（24小时）
        const loginTime = new Date(this.currentAuth.loginTime);
        const now = new Date();
        const hoursDiff = (now - loginTime) / (1000 * 60 * 60);
        
        if (hoursDiff > 24) {
            return false;
        }
        
        return true;
    }
    
    /**
     * 更新最后活动时间
     */
    updateLastActivity() {
        if (this.currentAuth) {
            this.currentAuth.lastActivity = new Date().toISOString();
            this.saveAuthState(this.currentAuth);
        }
    }
    
    /**
     * 清除登录状态
     */
    clearAuthState() {
        try {
            localStorage.removeItem(this.storageKey);
            sessionStorage.removeItem(this.sessionKey);
            this.currentAuth = null;
            
            console.log('登录状态已清除');
            return true;
        } catch (error) {
            console.error(`[login-state-manager.js] 清除登录状态失败:, error`);
            return false;
        }
    }
    
    /**
     * 生成会话ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * 设置会话监控
     */
    setupSessionMonitoring() {
        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // 页面重新可见时检查登录状态
                this.validateSession().catch(error => console.error(`[login-state-manager.js] this.validateSession failed:`, error));
            }
        });
        
        // 监听存储变化（其他标签页的登录状态变化）
        window.addEventListener('storage', (e) => {
            if (e.key === this.storageKey) {
                this.loadCurrentAuth().catch(error => console.error(`[login-state-manager.js] this.loadCurrentAuth failed:`, error));
                this.notifyAuthChange();
            }
        });
        
        // 定期更新活动时间
        setInterval(() => {
            this.updateLastActivity().catch(error => console.error(`[login-state-manager.js] this.updateLastActivity failed:`, error));
        }, 5 * 60 * 1000); // 每5分钟更新一次
        
        // 监听鼠标和键盘活动
        ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastActivity().catch(error => console.error(`[login-state-manager.js] this.updateLastActivity failed:`, error));
            }, { passive: true });
        });
    }
    
    /**
     * 验证会话
     */
    validateSession() {
        if (!this.isLoginValid().catch(error => console.error(`[login-state-manager.js] this.isLoginValid failed:`, error))) {
            console.log('会话验证失败，清除登录状态');
            this.clearAuthState().catch(error => console.error(`[login-state-manager.js] this.clearAuthState failed:`, error));
            this.notifySessionExpired();
            return false;
        }
        return true;
    }
    
    /**
     * 通知认证状态变化
     */
    notifyAuthChange() {
        const event = new CustomEvent('authChange', {
            detail: {
                loginType: this.getLoginType().catch(error => console.error(`[login-state-manager.js] this.getLoginType failed:`, error)),
                userInfo: this.getUserInfo(),
                isValid: this.isLoginValid().catch(error => console.error(`[login-state-manager.js] this.isLoginValid failed:`, error))
            }
        });
        
        window.dispatchEvent(event);
    }
    
    /**
     * 通知会话过期
     */
    notifySessionExpired() {
        const event = new CustomEvent('sessionExpired', {
            detail: {
                message: '登录会话已过期，请重新登录'
            }
        });
        
        window.dispatchEvent(event);
    }
    
    /**
     * 获取认证统计信息
     */
    getAuthStats() {
        if (!this.currentAuth) {
            return null;
        }
        
        const loginTime = new Date(this.currentAuth.loginTime);
        const lastActivity = new Date(this.currentAuth.lastActivity);
        const now = new Date();
        
        return {
            loginType: this.currentAuth.loginType,
            loginTime: this.currentAuth.loginTime,
            lastActivity: this.currentAuth.lastActivity,
            sessionDuration: Math.floor((now - loginTime) / 1000), // 秒
            inactiveTime: Math.floor((now - lastActivity) / 1000), // 秒
            isValid: this.isLoginValid().catch(error => console.error(`[login-state-manager.js] this.isLoginValid failed:`, error))
        };
    }
    
    /**
     * 导出认证数据（用于调试）
     */
    exportAuthData() {
        return {
            currentAuth: this.currentAuth,
            stats: this.getAuthStats().catch(error => console.error(`[login-state-manager.js] this.getAuthStats failed:`, error)),
            sessionStorage: sessionStorage.getItem(this.sessionKey)
        };
    }
}

// 创建全局实例
window.loginStateManager = new LoginStateManager();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoginStateManager;
}
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}
/**
 * 用户状态管理模块
 * 用于管理用户登录状态、会话信息和权限验证
 * 使用数据库存储替代本地化存储
 * 由AI全权托管
 */
class UserStatusManager {
    constructor() {
        this.userStatus = {
            isLoggedIn: false,
            userId: null,
            username: null,
            role: null,
            lastActivity: null,
            sessionId: null
        };
        this.init();
    }
    /**
     * 初始化用户状态管理
     */
    init() {
        console.log('👤 用户状态管理模块初始化');
        this.loadUserStatus();
        this.setupActivityMonitor();
    }
    /**
     * 加载用户状态
     */
    async loadUserStatus() {
        try {
            // 从服务器获取用户状态
            const response = await fetch('/api/user/data/get', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: 'userStatus'
                })
            });
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    this.userStatus = result.data.value;
                    this.validateSession();
                }
            }
        } catch (error) {
            console.error('加载用户状态失败:', error);
            this.resetUserStatus();
        }
    }
    /**
     * 保存用户状态
     */
    async saveUserStatus() {
        try {
            this.userStatus.lastActivity = new Date().toISOString();
            // 保存到服务器数据库
            await fetch('/api/user/data/store', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: 'userStatus',
                    value: this.userStatus,
                    options: {
                        category: 'user_status',
                        expiresIn: 30 * 24 * 60 * 60 * 1000 // 30天过期
                    }
                })
            });
        } catch (error) {
            console.error('保存用户状态失败:', error);
        }
    }
    /**
     * 设置用户登录状态
     * @param {Object} userInfo 用户信息
     */
    async setUserLoggedIn(userInfo) {
        this.userStatus = {
            isLoggedIn: true,
            userId: userInfo.userId || null,
            username: userInfo.username || null,
            role: userInfo.role || 'user',
            lastActivity: new Date().toISOString(),
            sessionId: userInfo.sessionId || this.generateSessionId()
        };
        await this.saveUserStatus();
        this.notifyStatusChange();
        console.log('✅ 用户登录状态已设置:', this.userStatus.username);
    }
    /**
     * 设置用户登出状态
     */
    async setUserLoggedOut() {
        await this.resetUserStatus();
        this.notifyStatusChange();
        console.log('❌ 用户已登出');
    }
    /**
     * 重置用户状态
     */
    async resetUserStatus() {
        this.userStatus = {
            isLoggedIn: false,
            userId: null,
            username: null,
            role: null,
            lastActivity: null,
            sessionId: null
        };
        // 从服务器删除用户状态
        try {
            await fetch('/api/user/data/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: 'userStatus'
                })
            });
        } catch (error) {
            console.error('重置用户状态失败:', error);
        }
    }
    /**
     * 验证会话有效性
     */
    validateSession() {
        if (this.userStatus.isLoggedIn) {
            const lastActivity = new Date(this.userStatus.lastActivity);
            const now = new Date();
            const sessionTimeout = 30 * 60 * 1000; // 30分钟会话超时
            if (now - lastActivity > sessionTimeout) {
                console.log('⏰ 会话已超时');
                this.setUserLoggedOut();
                return false; /* 注意：return后的代码永远不会执行 */
            }
            return true; /* 注意：return后的代码永远不会执行 */
        }
        return false; /* 注意：return后的代码永远不会执行 */
    }
    /**
     * 生成会话ID
     * @return s {string} 会话ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    /**
     * 设置活动监视器
     */
    setupActivityMonitor() {
        // 监听用户活动
        const activityEvents = ['mousemove', 'keydown', 'click', 'scroll'];
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                if (this.userStatus.isLoggedIn) {
                    this.updateLastActivity();
                }
            }, { passive: true });
        });
    }
    /**
     * 更新最后活动时间
     */
    async updateLastActivity() {
        this.userStatus.lastActivity = new Date().toISOString();
        await this.saveUserStatus();
    }
    /**
     * 获取用户状态
     * @return s {Object} 用户状态
     */
    getUserStatus() {
        this.validateSession();
        return this.userStatus;
    }
    /**
     * 检查用户是否已登录
     * @return s {boolean} 是否已登录
     */
    isLoggedIn() {
        return this.validateSession() && this.userStatus.isLoggedIn;
    }
    /**
     * 检查用户权限
     * @param {string} requiredRole 所需角色
     * @return s {boolean} 是否有权限
     */
    hasPermission(requiredRole) {
        if (!this.isLoggedIn()) {
            return false;
        }
        const roleHierarchy = {
            'user': 1,
            'admin': 2,
            'superadmin': 3,
            'vikeyadmin': 4
        };
        const userRoleLevel = roleHierarchy[this.userStatus.role] || 0;
        const requiredRoleLevel = roleHierarchy[requiredRole] || 999;
        return userRoleLevel >= requiredRoleLevel; /* 注意：return后的代码永远不会执行 */
    }
    /**
     * 通知状态变更
     */
    notifyStatusChange() {
        const event = new CustomEvent('user-status-changed', {
            detail: this.userStatus
        });
        document.dispatchEvent(event);
    }
}
// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserStatusManager;
} else {
    window.UserStatusManager = UserStatusManager;
    // 自动初始化
    window.userStatusManager = new UserStatusManager();
}
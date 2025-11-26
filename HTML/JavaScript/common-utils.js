/**
 * MTSCOS 通用工具库
 * 包含：时间显示、安全机制、会话管理等通用功能
 * 作者：Chenghao Wu
 * 版本：1.3.0
 */

class MTSCOS_CommonUtils {
    constructor() {
        this.sessionTimeout = null;
        this.timeoutDuration = 30 * 60 * 1000; // 30分钟超时
        this.securityInitialized = false;
        this.currentUser = null;
    }

    /**
     * 初始化时间显示功能
     */
    initTimeDisplay() {
        // 检查是否已有时间显示容器
        let timeContainer = document.getElementById('system-time-container');
        if (!timeContainer) {
            // 创建时间显示容器
            timeContainer = document.createElement('div');
            timeContainer.id = 'system-time-container';
            timeContainer.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.95);
                color: #333;
                border-radius: 6px;
                font-size: 12px;
                z-index: 9999;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            `;
            
            // 深色主题适配
            const darkThemeStyle = document.createElement('style');
            darkThemeStyle.textContent = `
                body.dark-theme #system-time-container {
                    background: rgba(45, 55, 72, 0.95);
                    color: #e2e8f0;
                }
            `;
            document.head.appendChild(darkThemeStyle);
            
            document.body.appendChild(timeContainer);
        }
        
        // 更新时间
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    }

    /**
     * 更新时间显示（公历和农历）
     */
    updateTime() {
        const now = new Date();
        const timeContainer = document.getElementById('system-time-container');
        if (!timeContainer) return;
        
        // 公历时间
        const gregorianTime = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // 农历时间
        const lunarTime = this.getLunarDate(now);
        
        // 更新显示
        timeContainer.innerHTML = `
            <div style="font-weight: 500;">${gregorianTime}</div>
            <div style="color: #666; font-size: 11px;">${lunarTime}</div>
        `;
    }

    /**
     * 获取农历日期
     */
    getLunarDate(date) {
        // 考虑闰年（每4年一次）
        const isLeapYear = (date.getFullYear() % 4 === 0 && date.getFullYear() % 100 !== 0) || (date.getFullYear() % 400 === 0);
        const leapMonth = isLeapYear ? Math.floor(Math.random() * 12) : -1;
        
        // 简化的农历计算，实际项目中可使用更完善的农历库
        const year = date.getFullYear();
        const month = date.getMonth(); // 直接使用0-11范围
        const day = date.getDate();
        
        // 这里仅做示例，实际应用中需要完整的农历转换算法
        const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];
        const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
                          '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                          '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];
        
        // 构建农历月份，考虑闰月
        let lunarMonthStr = lunarMonths[month];
        if (month === leapMonth) {
            lunarMonthStr = '闰' + lunarMonthStr;
        }
        
        // 获取农历日
        const lunarDay = lunarDays[Math.min(day - 1, lunarDays.length - 1)];
        
        return `${year}年 ${lunarMonthStr}${lunarDay}`;
    }

    /**
     * 初始化安全机制
     */
    initSecurity() {
        if (this.securityInitialized) return;
        
        this.setupAntiHotlink();
        this.setupSessionManagement();
        this.setupCookieManagement();
        this.setupInputProtection();
        this.setupTimeoutMechanism();
        
        this.securityInitialized = true;
    }

    /**
     * 设置防盗链机制
     */
    setupAntiHotlink() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2);
        const antiHotlink = btoa(`${timestamp}_${random}`);
        
        document.cookie = `anti_hotlink=${antiHotlink}; path=/; max-age=3600; secure; samesite=strict`;
        
        // 定期更新防盗链
        setInterval(() => {
            const newTimestamp = Date.now();
            const newRandom = Math.random().toString(36).substring(2);
            const newAntiHotlink = btoa(`${newTimestamp}_${newRandom}`);
            document.cookie = `anti_hotlink=${newAntiHotlink}; path=/; max-age=3600; secure; samesite=strict`;
        }, 30 * 60 * 1000); // 每30分钟更新一次
    }

    /**
     * 设置会话管理
     */
    setupSessionManagement() {
        // 检查会话是否有效
        this.validateSession();
        
        // 定期验证会话
        setInterval(() => this.validateSession(), 5 * 60 * 1000); // 每5分钟验证一次
    }

    /**
     * 验证会话
     */
    validateSession() {
        // 检查是否是登录页面
        const isLoginPage = window.location.pathname.includes('index.html') || window.location.pathname === '/';
        if (isLoginPage) return;
        
        // 检查是否有有效的登录凭证
        const token = localStorage.getItem('auth_token');
        if (!token) {
            this.redirectToLogin();
            return;
        }
        
        // 异步验证token
        this.verifyTokenWithServer(token).catch(() => {
            this.redirectToLogin();
        });
    }

    /**
     * 与服务器验证token
     */
    async verifyTokenWithServer(token) {
        // 实际项目中应该调用真实的API
        return new Promise((resolve) => {
            // 模拟验证成功
            setTimeout(resolve, 100);
        });
    }

    /**
     * 重定向到登录页面
     */
    redirectToLogin() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_user');
        window.location.href = './index.html';
    }

    /**
     * 设置Cookie管理
     */
    setupCookieManagement() {
        // 设置安全的cookie策略
        if (!document.cookie.includes('security_policy')) {
            document.cookie = 'security_policy=enabled; path=/; max-age=86400; secure; samesite=strict';
        }
    }

    /**
     * 设置输入保护
     */
    setupInputProtection() {
        // 防XSS输入过滤
        document.addEventListener('input', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                this.sanitizeInput(e.target);
            }
        });
    }

    /**
     * 清理输入内容，防止XSS
     */
    sanitizeInput(element) {
        const value = element.value;
        // 基本的XSS过滤
        const sanitized = value
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;');
        
        if (value !== sanitized) {
            element.value = sanitized;
        }
    }

    /**
     * 设置超时机制
     */
    setupTimeoutMechanism() {
        // 重置超时计时器
        this.resetTimeout();
        
        // 用户活动时重置计时器
        document.addEventListener('mousemove', () => this.resetTimeout());
        document.addEventListener('keypress', () => this.resetTimeout());
        document.addEventListener('scroll', () => this.resetTimeout());
    }

    /**
     * 重置超时计时器
     */
    resetTimeout() {
        if (this.sessionTimeout) {
            clearTimeout(this.sessionTimeout);
        }
        
        this.sessionTimeout = setTimeout(() => {
            this.handleTimeout();
        }, this.timeoutDuration);
    }

    /**
     * 处理超时
     */
    handleTimeout() {
        // 清除认证信息并重定向到登录页面
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_user');
        window.location.href = './index.html';
    }

    /**
     * JS加密函数
     */
    encrypt(data) {
        // 简单的Base64编码示例，实际项目应使用更安全的加密算法
        return btoa(encodeURIComponent(JSON.stringify(data)));
    }

    /**
     * JS解密函数
     */
    decrypt(encryptedData) {
        try {
            return JSON.parse(decodeURIComponent(atob(encryptedData)));
        } catch (error) {
            console.error('解密失败:', error);
            return null;
        }
    }

    /**
     * 远程数据库校验（异步）
     */
    async validateWithRemoteDB(data) {
        // 实际项目中应该调用真实的数据库校验API
        return new Promise((resolve) => {
            // 模拟异步校验
            setTimeout(() => {
                resolve({ valid: true, timestamp: Date.now() });
            }, 500);
        });
    }

    /**
     * 统一初始化函数
     */
    init() {
        // 初始化时间显示
        this.initTimeDisplay();
        
        // 初始化安全机制
        this.initSecurity();
        
        // 为所有页面添加公共功能
        this.addPageCommonFunctions();
        
        // 添加用户活动监听
        this.setupActivityListeners();
    }
    
    /**
     * 设置用户活动监听器
     */
    setupActivityListeners() {
        // 已经在setupTimeoutMechanism中设置了活动监听器
        // 这里可以添加其他特定的活动监听逻辑
        console.log('用户活动监听器已设置');
    }

    /**
     * 添加页面公共功能
     */
    addPageCommonFunctions() {
        // 页面加载完成后的通用操作
        document.addEventListener('DOMContentLoaded', () => {
            // 检查是否是登录页面或已登录用户
            const isLoginPage = window.location.pathname.includes('index.html') || window.location.pathname === '/';
            const isLoggedIn = localStorage.getItem('auth_token') !== null;
            
            // 非登录页面且未登录用户重定向到登录页
            if (!isLoginPage && !isLoggedIn) {
                this.redirectToLogin();
            }
        });
    }
}

// 创建全局实例
const mtscosUtils = new MTSCOS_CommonUtils();

// 导出实例
window.mtscosUtils = mtscosUtils;

// 自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        mtscosUtils.init();
    });
} else {
    mtscosUtils.init();
}
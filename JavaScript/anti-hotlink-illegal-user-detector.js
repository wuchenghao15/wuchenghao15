/**
 * 防盗链和非法用户检测系统
 * 提供多层安全防护机制，包括防盗链检测、非法用户识别、访问控制等功能
 */
class AntiHotlinkIllegalUserDetector {
    constructor(config = {}) {
        this.config = {
            // 防盗链配置
            hotlink: {
                enabled: true,
                tokenExpiry: 3600, // 1小时
                refreshInterval: 30 * 60 * 1000, // 30分钟
                allowedDomains: [],
                allowedReferers: [],
                blockDirectAccess: false
            },
            
            // 非法用户检测配置
            illegalUser: {
                enabled: true,
                maxFailedAttempts: 5,
                timeWindow: 15 * 60 * 1000, // 15分钟
                blacklistDuration: 24 * 60 * 60 * 1000, // 24小时
                suspiciousScoreThreshold: 80,
                monitoringEnabled: true
            },
            
            // 访问控制配置
            accessControl: {
                enabled: true,
                rateLimiting: {
                    enabled: true,
                    maxRequests: 100,
                    timeWindow: 60 * 1000, // 1分钟
                    blockDuration: 10 * 60 * 1000 // 10分钟
                },
                geoBlocking: {
                    enabled: false,
                    allowedCountries: ['CN'],
                    blockedCountries: []
                },
                ipWhitelist: [],
                ipBlacklist: []
            },
            
            // 监控和日志配置
            monitoring: {
                enabled: true,
                logLevel: 'info',
                auditLog: true,
                realTimeAlerts: true,
                statistics: true
            },
            
            ...config
        };
        
        this.isInitialized = false;
        this.startTime = Date.now();
        
        // 存储系统
        this.sessionStore = new Map();
        this.blacklist = new Map();
        this.whitelist = new Map();
        this.accessLog = [];
        this.suspiciousActivities = [];
        this.statistics = {
            totalRequests: 0,
            blockedRequests: 0,
            suspiciousUsers: 0,
            blacklistedUsers: 0
        };
        
        // 防盗链令牌管理
        this.antiHotlinkTokens = new Map();
        this.currentToken = null;
        
        this.init();
    }
    
    /**
     * 初始化防盗链和非法用户检测系统
     */
    async init() {
        try {
            console.log('[防盗链系统] 正在初始化...');
            
            // 初始化防盗链机制
            if (this.config.hotlink.enabled) {
                this.initAntiHotlink();
            }
            
            // 初始化非法用户检测
            if (this.config.illegalUser.enabled) {
                this.initIllegalUserDetection();
            }
            
            // 初始化访问控制
            if (this.config.accessControl.enabled) {
                this.initAccessControl();
            }
            
            // 初始化监控系统
            if (this.config.monitoring.enabled) {
                this.initMonitoring();
            }
            
            // 加载黑名单和白名单
            await this.loadBlacklistAndWhitelist();
            
            // 启动定期清理任务
            this.startPeriodicCleanup();
            
            this.isInitialized = true;
            console.log('[防盗链系统] 初始化完成');
            
            this.logEvent('SYSTEM_INITIALIZED', {
                timestamp: Date.now(),
                config: this.config
            });
            
        } catch (error) {
            console.error('[防盗链系统] 初始化失败:', error);
            this.logEvent('INITIALIZATION_FAILED', { error: error.message });
        }
    }
    
    /**
     * 初始化防盗链机制
     */
    initAntiHotlink() {
        console.log('[防盗链系统] 初始化防盗链机制');
        
        // 生成初始防盗链令牌
        this.generateAntiHotlinkToken();
        
        // 设置定期更新令牌
        setInterval(() => {
            this.generateAntiHotlinkToken();
        }, this.config.hotlink.refreshInterval);
        
        // 监听页面加载事件
        if (typeof document !== 'undefined') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupPageProtection();
            });
        }
    }
    
    /**
     * 生成防盗链令牌
     */
    generateAntiHotlinkToken() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2);
        const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : '';
        const fingerprint = this.generateFingerprint();
        
        const tokenData = {
            timestamp,
            random,
            userAgent: this.hashString(userAgent),
            fingerprint,
            signature: this.generateSignature(timestamp, random, fingerprint)
        };
        
        const token = btoa(JSON.stringify(tokenData));
        
        // 存储当前令牌
        this.currentToken = token;
        this.antiHotlinkTokens.set(token, {
            created: timestamp,
            expires: timestamp + (this.config.hotlink.tokenExpiry * 1000),
            usage: 0
        });
        
        // 设置Cookie
        if (typeof document !== 'undefined') {
            document.cookie = `anti_hotlink=${token}; path=/; max-age=${this.config.hotlink.tokenExpiry}; secure; samesite=strict`;
        }
        
        console.log('[防盗链系统] 生成新的防盗链令牌');
        this.logEvent('ANTI_HOTLINK_TOKEN_GENERATED', { timestamp });
    }
    
    /**
     * 验证防盗链令牌
     */
    validateAntiHotlinkToken(token) {
        if (!token || !this.config.hotlink.enabled) {
            return { valid: false, reason: 'TOKEN_MISSING_OR_DISABLED' };
        }
        
        const tokenData = this.antiHotlinkTokens.get(token);
        if (!tokenData) {
            return { valid: false, reason: 'TOKEN_NOT_FOUND' };
        }
        
        const now = Date.now();
        if (now > tokenData.expires) {
            this.antiHotlinkTokens.delete(token);
            return { valid: false, reason: 'TOKEN_EXPIRED' };
        }
        
        try {
            const decoded = JSON.parse(atob(token));
            
            // 验证时间戳
            if (Math.abs(now - decoded.timestamp) > this.config.hotlink.tokenExpiry * 1000) {
                return { valid: false, reason: 'TIMESTAMP_INVALID' };
            }
            
            // 验证签名
            const expectedSignature = this.generateSignature(decoded.timestamp, decoded.random, decoded.fingerprint);
            if (decoded.signature !== expectedSignature) {
                return { valid: false, reason: 'SIGNATURE_INVALID' };
            }
            
            // 更新使用次数
            tokenData.usage++;
            
            return { valid: true };
            
        } catch (error) {
            return { valid: false, reason: 'TOKEN_DECODE_FAILED' };
        }
    }
    
    /**
     * 初始化非法用户检测
     */
    initIllegalUserDetection() {
        console.log('[防盗链系统] 初始化非法用户检测');
        
        // 监听用户行为
        if (typeof window !== 'undefined') {
            this.setupUserBehaviorMonitoring();
        }
    }
    
    /**
     * 检测非法用户
     */
    detectIllegalUser(userContext) {
        if (!this.config.illegalUser.enabled) {
            return { isIllegal: false, score: 0, reasons: [] };
        }
        
        const userId = userContext.ip || userContext.fingerprint || 'unknown';
        const now = Date.now();
        
        // 获取用户历史记录
        let userRecord = this.sessionStore.get(userId);
        if (!userRecord) {
            userRecord = {
                firstSeen: now,
                lastSeen: now,
                failedAttempts: 0,
                totalRequests: 0,
                suspiciousScore: 0,
                activities: [],
                blacklisted: false
            };
            this.sessionStore.set(userId, userRecord);
        }
        
        const reasons = [];
        let score = 0;
        
        // 检查黑名单
        if (this.blacklist.has(userId)) {
            const blacklistEntry = this.blacklist.get(userId);
            if (now < blacklistEntry.expires) {
                return {
                    isIllegal: true,
                    score: 100,
                    reasons: ['USER_BLACKLISTED'],
                    expires: blacklistEntry.expires
                };
            } else {
                // 黑名单已过期，移除
                this.blacklist.delete(userId);
                userRecord.blacklisted = false;
            }
        }
        
        // 检查失败尝试次数
        if (userRecord.failedAttempts >= this.config.illegalUser.maxFailedAttempts) {
            score += 30;
            reasons.push('EXCESSIVE_FAILED_ATTEMPTS');
        }
        
        // 检查请求频率
        const recentRequests = userRecord.activities.filter(
            activity => (now - activity.timestamp) < this.config.illegalUser.timeWindow
        );
        
        if (recentRequests.length > 50) { // 15分钟内超过50次请求
            score += 25;
            reasons.push('HIGH_FREQUENCY_REQUESTS');
        }
        
        // 检查可疑行为模式
        const suspiciousPatterns = this.detectSuspiciousPatterns(recentRequests);
        if (suspiciousPatterns.length > 0) {
            score += 20;
            reasons.push('SUSPICIOUS_BEHAVIOR_PATTERN');
        }
        
        // 检查用户代理
        if (userContext.userAgent && this.isSuspiciousUserAgent(userContext.userAgent)) {
            score += 15;
            reasons.push('SUSPICIOUS_USER_AGENT');
        }
        
        // 检查地理位置异常
        if (userContext.location && this.isLocationAnomalous(userId, userContext.location)) {
            score += 20;
            reasons.push('LOCATION_ANOMALY');
        }
        
        // 检查时间异常
        if (this.isTimeAnomalous(recentRequests)) {
            score += 15;
            reasons.push('TIME_ANOMALY');
        }
        
        // 更新用户记录
        userRecord.lastSeen = now;
        userRecord.totalRequests++;
        userRecord.suspiciousScore = Math.max(userRecord.suspiciousScore, score);
        
        const isIllegal = score >= this.config.illegalUser.suspiciousScoreThreshold;
        
        // 如果是非法用户，加入黑名单
        if (isIllegal && !userRecord.blacklisted) {
            this.addToBlacklist(userId, score, reasons);
            userRecord.blacklisted = true;
        }
        
        return {
            isIllegal,
            score,
            reasons,
            userRecord
        };
    }
    
    /**
     * 初始化访问控制
     */
    initAccessControl() {
        console.log('[防盗链系统] 初始化访问控制');
        
        // 设置请求拦截器
        if (typeof window !== 'undefined') {
            this.interceptRequests();
        }
    }
    
    /**
     * 检查访问权限
     */
    checkAccess(requestContext) {
        if (!this.config.accessControl.enabled) {
            return { allowed: true, reason: 'ACCESS_CONTROL_DISABLED' };
        }
        
        const ip = requestContext.ip;
        const userAgent = requestContext.userAgent;
        const referer = requestContext.referer;
        
        // 检查IP白名单
        if (this.config.accessControl.ipWhitelist.length > 0) {
            if (!this.config.accessControl.ipWhitelist.includes(ip)) {
                return { allowed: false, reason: 'IP_NOT_WHITELISTED' };
            }
        }
        
        // 检查IP黑名单
        if (this.config.accessControl.ipBlacklist.includes(ip)) {
            return { allowed: false, reason: 'IP_BLACKLISTED' };
        }
        
        // 检查频率限制
        if (this.config.accessControl.rateLimiting.enabled) {
            const rateLimitResult = this.checkRateLimit(ip);
            if (!rateLimitResult.allowed) {
                return rateLimitResult;
            }
        }
        
        // 检查Referer
        if (this.config.hotlink.allowedReferers.length > 0 && referer) {
            const refererDomain = new URL(referer).hostname;
            if (!this.config.hotlink.allowedReferers.includes(refererDomain)) {
                return { allowed: false, reason: 'INVALID_REFERER' };
            }
        }
        
        // 检查防盗链令牌
        if (this.config.hotlink.enabled) {
            const token = this.extractTokenFromRequest(requestContext);
            const tokenValidation = this.validateAntiHotlinkToken(token);
            if (!tokenValidation.valid) {
                return { allowed: false, reason: tokenValidation.reason };
            }
        }
        
        return { allowed: true };
    }
    
    /**
     * 检查频率限制
     */
    checkRateLimit(ip) {
        const now = Date.now();
        const timeWindow = this.config.accessControl.rateLimiting.timeWindow;
        const maxRequests = this.config.accessControl.rateLimiting.maxRequests;
        
        let ipRecord = this.sessionStore.get(`rate_limit_${ip}`);
        if (!ipRecord) {
            ipRecord = { requests: [], blocked: false, blockExpires: 0 };
            this.sessionStore.set(`rate_limit_${ip}`, ipRecord);
        }
        
        // 检查是否在封禁期
        if (ipRecord.blocked && now < ipRecord.blockExpires) {
            return {
                allowed: false,
                reason: 'RATE_LIMIT_BLOCKED',
                blockExpires: ipRecord.blockExpires
            };
        }
        
        // 清理过期请求
        ipRecord.requests = ipRecord.requests.filter(
            timestamp => (now - timestamp) < timeWindow
        );
        
        // 检查是否超过限制
        if (ipRecord.requests.length >= maxRequests) {
            ipRecord.blocked = true;
            ipRecord.blockExpires = now + this.config.accessControl.rateLimiting.blockDuration;
            
            this.logEvent('RATE_LIMIT_EXCEEDED', {
                ip,
                requestCount: ipRecord.requests.length,
                blockDuration: this.config.accessControl.rateLimiting.blockDuration
            });
            
            return {
                allowed: false,
                reason: 'RATE_LIMIT_EXCEEDED',
                blockExpires: ipRecord.blockExpires
            };
        }
        
        // 记录当前请求
        ipRecord.requests.push(now);
        
        return { allowed: true };
    }
    
    /**
     * 设置页面保护
     */
    setupPageProtection() {
        // 禁用右键菜单
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.logEvent('CONTEXT_MENU_BLOCKED', { timestamp: Date.now() });
            return false;
        });
        
        // 禁用文本选择
        document.addEventListener('selectstart', (e) => {
            e.preventDefault();
            return false;
        });
        
        // 禁用复制快捷键
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'x' || e.key === 'u')) {
                e.preventDefault();
                this.logEvent('COPY_SHORTCUT_BLOCKED', { key: e.key });
                return false;
            }
        });
        
        // 监控开发者工具
        this.detectDevTools();
        
        // 监控页面焦点
        this.monitorPageFocus();
    }
    
    /**
     * 检测开发者工具
     */
    detectDevTools() {
        let devtools = { open: false, orientation: null };
        
        const threshold = 160;
        
        setInterval(() => {
            if (window.outerHeight - window.innerHeight > threshold ||
                window.outerWidth - window.innerWidth > threshold) {
                if (!devtools.open) {
                    devtools.open = true;
                    this.logEvent('DEV_TOOLS_DETECTED', { timestamp: Date.now() });
                    this.handleSuspiciousActivity('DEV_TOOLS_OPENED');
                }
            } else {
                devtools.open = false;
            }
        }, 500);
        
        // 监控控制台输出
        const originalLog = console.log;
        console.log = function(...args) {
            originalLog.apply(console, args);
            // 可以在这里添加控制台监控逻辑
        };
    }
    
    /**
     * 监控页面焦点
     */
    monitorPageFocus() {
        let focusLostTime = 0;
        
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                focusLostTime = Date.now();
            } else {
                const focusDuration = Date.now() - focusLostTime;
                if (focusDuration > 60000) { // 失焦超过1分钟
                    this.logEvent('LONG_FOCUS_LOSS', { duration: focusDuration });
                }
            }
        });
        
        window.addEventListener('blur', () => {
            focusLostTime = Date.now();
        });
        
        window.addEventListener('focus', () => {
            const focusDuration = Date.now() - focusLostTime;
            if (focusDuration > 60000) {
                this.logEvent('WINDOW_FOCUS_RETURN', { duration: focusDuration });
            }
        });
    }
    
    /**
     * 设置用户行为监控
     */
    setupUserBehaviorMonitoring() {
        // 监控鼠标移动
        let mouseMovements = 0;
        let lastMouseTime = Date.now();
        
        document.addEventListener('mousemove', () => {
            mouseMovements++;
            const now = Date.now();
            
            if (now - lastMouseTime > 100) { // 超过100ms的移动间隔
                this.logEvent('MOUSE_MOVEMENT', {
                    interval: now - lastMouseTime,
                    totalMovements: mouseMovements
                });
                lastMouseTime = now;
            }
        });
        
        // 监控键盘输入
        let keystrokes = 0;
        document.addEventListener('keydown', () => {
            keystrokes++;
            if (keystrokes % 50 === 0) {
                this.logEvent('KEYSTROKE_COUNT', { count: keystrokes });
            }
        });
        
        // 监控页面滚动
        let scrollEvents = 0;
        document.addEventListener('scroll', () => {
            scrollEvents++;
            if (scrollEvents % 10 === 0) {
                this.logEvent('SCROLL_EVENT', { count: scrollEvents });
            }
        });
    }
    
    /**
     * 检测可疑行为模式
     */
    detectSuspiciousPatterns(activities) {
        const patterns = [];
        
        // 检测机器人行为
        if (this.isBotBehavior(activities)) {
            patterns.push('BOT_BEHAVIOR');
        }
        
        // 检测扫描行为
        if (this.isScanningBehavior(activities)) {
            patterns.push('SCANNING_BEHAVIOR');
        }
        
        // 检测暴力破解
        if (this.isBruteForceBehavior(activities)) {
            patterns.push('BRUTE_FORCE_BEHAVIOR');
        }
        
        return patterns;
    }
    
    /**
     * 检测机器人行为
     */
    isBotBehavior(activities) {
        if (activities.length < 10) return false;
        
        // 检查请求间隔是否过于规律
        const intervals = [];
        for (let i = 1; i < activities.length; i++) {
            intervals.push(activities[i].timestamp - activities[i-1].timestamp);
        }
        
        const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        const variance = intervals.reduce((sum, interval) => {
            return sum + Math.pow(interval - avgInterval, 2);
        }, 0) / intervals.length;
        
        // 如果方差很小，说明请求间隔过于规律，可能是机器人
        return variance < 100; // 方差阈值
    }
    
    /**
     * 检测扫描行为
     */
    isScanningBehavior(activities) {
        // 检查是否访问了大量不同的页面
        const uniquePages = new Set(activities.map(a => a.page)).size;
        const totalActivities = activities.length;
        
        // 如果访问的页面数占总活动数的比例很高，可能是扫描
        return (uniquePages / totalActivities) > 0.8 && totalActivities > 20;
    }
    
    /**
     * 检测暴力破解行为
     */
    isBruteForceBehavior(activities) {
        // 检查是否有大量失败的登录尝试
        const failedLogins = activities.filter(a => a.type === 'LOGIN_FAILED').length;
        const totalLogins = activities.filter(a => a.type === 'LOGIN_ATTEMPT').length;
        
        return totalLogins > 5 && (failedLogins / totalLogins) > 0.7;
    }
    
    /**
     * 检测可疑用户代理
     */
    isSuspiciousUserAgent(userAgent) {
        const suspiciousPatterns = [
            /bot/i,
            /crawler/i,
            /spider/i,
            /scraper/i,
            /curl/i,
            /wget/i,
            /python/i,
            /java/i,
            /perl/i,
            /php/i
        ];
        
        return suspiciousPatterns.some(pattern => pattern.test(userAgent));
    }
    
    /**
     * 检测地理位置异常
     */
    isLocationAnomalous(userId, currentLocation) {
        const userRecord = this.sessionStore.get(userId);
        if (!userRecord || !userRecord.lastLocation) {
            // 第一次访问，记录位置
            userRecord.lastLocation = currentLocation;
            return false;
        }
        
        // 计算地理位置距离（简化版本）
        const distance = this.calculateDistance(
            userRecord.lastLocation,
            currentLocation
        );
        
        // 如果距离超过1000公里且时间间隔小于1小时，认为是异常
        const timeDiff = Date.now() - userRecord.lastLocationTime;
        if (distance > 1000 && timeDiff < 60 * 60 * 1000) {
            return true;
        }
        
        // 更新最后位置
        userRecord.lastLocation = currentLocation;
        userRecord.lastLocationTime = Date.now();
        
        return false;
    }
    
    /**
     * 计算地理位置距离（简化版本）
     */
    calculateDistance(loc1, loc2) {
        if (!loc1.latitude || !loc2.latitude) return 0;
        
        const R = 6371; // 地球半径（公里）
        const dLat = (loc2.latitude - loc1.latitude) * Math.PI / 180;
        const dLon = (loc2.longitude - loc1.longitude) * Math.PI / 180;
        
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(loc1.latitude * Math.PI / 180) * 
                  Math.cos(loc2.latitude * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
    
    /**
     * 检测时间异常
     */
    isTimeAnomalous(activities) {
        if (activities.length < 5) return false;
        
        // 检查是否在不寻常的时间段访问
        const hours = activities.map(a => new Date(a.timestamp).getHours());
        const unusualHours = hours.filter(h => h < 6 || h > 23); // 凌晨0-6点
        
        return unusualHours.length > activities.length * 0.5;
    }
    
    /**
     * 生成设备指纹
     */
    generateFingerprint() {
        if (typeof navigator === 'undefined') {
            return 'server_environment';
        }
        
        const components = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset(),
            navigator.hardwareConcurrency || 'unknown',
            navigator.platform
        ];
        
        return this.hashString(components.join('|'));
    }
    
    /**
     * 生成签名
     */
    generateSignature(timestamp, random, fingerprint) {
        const data = `${timestamp}_${random}_${fingerprint}`;
        return this.hashString(data);
    }
    
    /**
     * 字符串哈希
     */
    hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // 转换为32位整数
        }
        return hash.toString(36);
    }
    
    /**
     * 从请求中提取令牌
     */
    extractTokenFromRequest(requestContext) {
        // 从Cookie中提取
        if (requestContext.cookies && requestContext.cookies.anti_hotlink) {
            return requestContext.cookies.anti_hotlink;
        }
        
        // 从Header中提取
        if (requestContext.headers && requestContext.headers['x-anti-hotlink']) {
            return requestContext.headers['x-anti-hotlink'];
        }
        
        // 从查询参数中提取
        if (requestContext.query && requestContext.query.anti_hotlink) {
            return requestContext.query.anti_hotlink;
        }
        
        return null;
    }
    
    /**
     * 添加到黑名单
     */
    addToBlacklist(userId, score, reasons) {
        const now = Date.now();
        const expires = now + this.config.illegalUser.blacklistDuration;
        
        this.blacklist.set(userId, {
            added: now,
            expires,
            score,
            reasons,
            permanent: score >= 95 // 高分永久封禁
        });
        
        this.statistics.blacklistedUsers++;
        
        this.logEvent('USER_BLACKLISTED', {
            userId,
            score,
            reasons,
            expires,
            permanent: score >= 95
        });
        
        // 触发安全警报
        this.triggerSecurityAlert('USER_BLACKLISTED', {
            userId,
            score,
            reasons
        });
    }
    
    /**
     * 从黑名单移除
     */
    removeFromBlacklist(userId) {
        if (this.blacklist.has(userId)) {
            this.blacklist.delete(userId);
            
            const userRecord = this.sessionStore.get(userId);
            if (userRecord) {
                userRecord.blacklisted = false;
                userRecord.suspiciousScore = 0;
            }
            
            this.logEvent('USER_REMOVED_FROM_BLACKLIST', { userId });
        }
    }
    
    /**
     * 处理可疑活动
     */
    handleSuspiciousActivity(activityType, details = {}) {
        const activity = {
            type: activityType,
            timestamp: Date.now(),
            details
        };
        
        this.suspiciousActivities.push(activity);
        
        // 限制活动记录数量
        if (this.suspiciousActivities.length > 1000) {
            this.suspiciousActivities = this.suspiciousActivities.slice(-500);
        }
        
        this.logEvent('SUSPICIOUS_ACTIVITY', activity);
        
        // 触发安全警报
        this.triggerSecurityAlert(activityType, details);
    }
    
    /**
     * 触发安全警报
     */
    triggerSecurityAlert(alertType, details) {
        if (!this.config.monitoring.realTimeAlerts) return;
        
        const alert = {
            type: alertType,
            timestamp: Date.now(),
            severity: this.getAlertSeverity(alertType),
            details
        };
        
        console.warn('[安全警报]', alert);
        
        // 这里可以添加发送到外部监控系统的逻辑
        // 例如：发送邮件、短信、Slack通知等
    }
    
    /**
     * 获取警报严重程度
     */
    getAlertSeverity(alertType) {
        const severityMap = {
            'USER_BLACKLISTED': 'high',
            'DEV_TOOLS_DETECTED': 'medium',
            'RATE_LIMIT_EXCEEDED': 'medium',
            'SUSPICIOUS_ACTIVITY': 'low'
        };
        
        return severityMap[alertType] || 'low';
    }
    
    /**
     * 拦截请求
     */
    interceptRequests() {
        // 拦截fetch请求
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const request = args[0];
            const context = this.buildRequestContext(request);
            
            const accessResult = this.checkAccess(context);
            if (!accessResult.allowed) {
                this.statistics.blockedRequests++;
                this.logEvent('REQUEST_BLOCKED', {
                    reason: accessResult.reason,
                    url: request.url
                });
                
                throw new Error(`请求被阻止: ${accessResult.reason}`);
            }
            
            this.statistics.totalRequests++;
            return originalFetch.apply(window, args);
        };
        
        // 拦截XMLHttpRequest
        const originalXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            const context = this.buildRequestContext(method, url);
            
            // 注意：这里需要在发送前检查，但由于异步特性，需要在send中处理
            this._antiHotlinkContext = context;
            
            return originalXHROpen.apply(this, [method, url, ...args]);
        };
        
        const originalXHRSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function(...args) {
            if (this._antiHotlinkContext) {
                const accessResult = window.antiHotlinkDetector.checkAccess(this._antiHotlinkContext);
                if (!accessResult.allowed) {
                    window.antiHotlinkDetector.statistics.blockedRequests++;
                    window.antiHotlinkDetector.logEvent('REQUEST_BLOCKED', {
                        reason: accessResult.reason,
                        url: this._antiHotlinkContext.url
                    });
                    
                    // 触发错误事件
                    this.dispatchEvent(new Event('error'));
                    return;
                }
                
                window.antiHotlinkDetector.statistics.totalRequests++;
            }
            
            return originalXHRSend.apply(this, args);
        };
    }
    
    /**
     * 构建请求上下文
     */
    buildRequestContext(request) {
        const context = {
            url: request.url || request,
            method: request.method || 'GET',
            userAgent: navigator.userAgent,
            referer: document.referrer,
            timestamp: Date.now()
        };
        
        // 提取IP地址（在真实环境中需要从服务器获取）
        context.ip = this.getClientIP();
        
        // 提取Cookie
        if (document.cookie) {
            context.cookies = {};
            document.cookie.split(';').forEach(cookie => {
                const [name, value] = cookie.trim().split('=');
                context.cookies[name] = value;
            });
        }
        
        return context;
    }
    
    /**
     * 获取客户端IP（模拟）
     */
    getClientIP() {
        // 在真实环境中，这应该从服务器获取
        // 这里返回一个模拟的IP
        return '192.168.1.' + Math.floor(Math.random() * 254 + 1);
    }
    
    /**
     * 初始化监控系统
     */
    initMonitoring() {
        console.log('[防盗链系统] 初始化监控系统');
        
        // 定期生成统计报告
        setInterval(() => {
            this.generateStatisticsReport();
        }, 5 * 60 * 1000); // 每5分钟
    }
    
    /**
     * 生成统计报告
     */
    generateStatisticsReport() {
        const report = {
            timestamp: Date.now(),
            uptime: Date.now() - this.startTime,
            statistics: { ...this.statistics },
            activeUsers: this.sessionStore.size,
            blacklistedUsers: this.blacklist.size,
            suspiciousActivities: this.suspiciousActivities.length
        };
        
        this.logEvent('STATISTICS_REPORT', report);
        
        console.log('[防盗链系统] 统计报告:', report);
    }
    
    /**
     * 记录事件日志
     */
    logEvent(eventType, data) {
        const logEntry = {
            timestamp: Date.now(),
            type: eventType,
            data
        };
        
        this.accessLog.push(logEntry);
        
        // 限制日志大小
        if (this.accessLog.length > 10000) {
            this.accessLog = this.accessLog.slice(-5000);
        }
        
        // 输出到控制台（开发环境）
        if (this.config.monitoring.logLevel === 'debug') {
            console.log(`[防盗链日志] ${eventType}:`, data);
        }
    }
    
    /**
     * 加载黑名单和白名单
     */
    async loadBlacklistAndWhitelist() {
        try {
            // 从本地存储加载
            if (typeof localStorage !== 'undefined') {
                const savedBlacklist = localStorage.getItem('anti_hotlink_blacklist');
                if (savedBlacklist) {
                    const parsed = JSON.parse(savedBlacklist);
                    parsed.forEach(entry => {
                        this.blacklist.set(entry.userId, entry);
                    });
                }
                
                const savedWhitelist = localStorage.getItem('anti_hotlink_whitelist');
                if (savedWhitelist) {
                    const parsed = JSON.parse(savedWhitelist);
                    parsed.forEach(entry => {
                        this.whitelist.set(entry.userId, entry);
                    });
                }
            }
            
            console.log('[防盗链系统] 加载黑名单和白名单完成');
            
        } catch (error) {
            console.error('[防盗链系统] 加载黑名单和白名单失败:', error);
        }
    }
    
    /**
     * 保存黑名单和白名单
     */
    async saveBlacklistAndWhitelist() {
        try {
            if (typeof localStorage !== 'undefined') {
                const blacklistArray = Array.from(this.blacklist.entries()).map(([userId, entry]) => ({
                    userId,
                    ...entry
                }));
                
                const whitelistArray = Array.from(this.whitelist.entries()).map(([userId, entry]) => ({
                    userId,
                    ...entry
                }));
                
                localStorage.setItem('anti_hotlink_blacklist', JSON.stringify(blacklistArray));
                localStorage.setItem('anti_hotlink_whitelist', JSON.stringify(whitelistArray));
            }
            
        } catch (error) {
            console.error('[防盗链系统] 保存黑名单和白名单失败:', error);
        }
    }
    
    /**
     * 启动定期清理任务
     */
    startPeriodicCleanup() {
        // 每小时清理一次过期数据
        setInterval(() => {
            this.cleanupExpiredData();
        }, 60 * 60 * 1000);
        
        // 每10分钟保存一次数据
        setInterval(() => {
            this.saveBlacklistAndWhitelist();
        }, 10 * 60 * 1000);
    }
    
    /**
     * 清理过期数据
     */
    cleanupExpiredData() {
        const now = Date.now();
        
        // 清理过期的黑名单条目
        for (const [userId, entry] of this.blacklist.entries()) {
            if (!entry.permanent && now > entry.expires) {
                this.blacklist.delete(userId);
                console.log(`[防盗链系统] 用户 ${userId} 已从黑名单中移除（过期）`);
            }
        }
        
        // 清理过期的会话记录
        for (const [userId, record] of this.sessionStore.entries()) {
            if (now - record.lastSeen > 24 * 60 * 60 * 1000) { // 24小时无活动
                this.sessionStore.delete(userId);
            }
        }
        
        // 清理过期的防盗链令牌
        for (const [token, tokenData] of this.antiHotlinkTokens.entries()) {
            if (now > tokenData.expires) {
                this.antiHotlinkTokens.delete(token);
            }
        }
        
        // 清理旧的访问日志
        this.accessLog = this.accessLog.filter(
            entry => now - entry.timestamp < 7 * 24 * 60 * 60 * 1000 // 保留7天
        );
        
        console.log('[防盗链系统] 过期数据清理完成');
    }
    
    /**
     * 获取系统状态
     */
    getSystemStatus() {
        return {
            initialized: this.isInitialized,
            uptime: Date.now() - this.startTime,
            statistics: { ...this.statistics },
            activeUsers: this.sessionStore.size,
            blacklistedUsers: this.blacklist.size,
            whitelistedUsers: this.whitelist.size,
            activeTokens: this.antiHotlinkTokens.size,
            suspiciousActivities: this.suspiciousActivities.length,
            config: this.config
        };
    }
    
    /**
     * 获取用户报告
     */
    getUserReport(userId) {
        const userRecord = this.sessionStore.get(userId);
        const blacklistEntry = this.blacklist.get(userId);
        const whitelistEntry = this.whitelist.get(userId);
        
        return {
            userId,
            userRecord,
            blacklistEntry,
            whitelistEntry,
            recentActivities: this.accessLog
                .filter(log => log.data.userId === userId)
                .slice(-20)
        };
    }
    
    /**
     * 手动封禁用户
     */
    banUser(userId, reason, duration = null) {
        const expires = duration ? Date.now() + duration : Date.now() + 365 * 24 * 60 * 60 * 1000; // 默认1年
        
        this.blacklist.set(userId, {
            added: Date.now(),
            expires,
            reason,
            manual: true,
            permanent: duration === null
        });
        
        this.logEvent('MANUAL_BAN', { userId, reason, expires });
        
        const userRecord = this.sessionStore.get(userId);
        if (userRecord) {
            userRecord.blacklisted = true;
        }
    }
    
    /**
     * 手动解封用户
     */
    unbanUser(userId) {
        this.removeFromBlacklist(userId);
        this.logEvent('MANUAL_UNBAN', { userId });
    }
    
    /**
     * 添加到白名单
     */
    addToWhitelist(userId, reason) {
        this.whitelist.set(userId, {
            added: Date.now(),
            reason,
            permanent: true
        });
        
        this.logEvent('USER_WHITELISTED', { userId, reason });
    }
    
    /**
     * 从白名单移除
     */
    removeFromWhitelist(userId) {
        if (this.whitelist.has(userId)) {
            this.whitelist.delete(userId);
            this.logEvent('USER_REMOVED_FROM_WHITELIST', { userId });
        }
    }
    
    /**
     * 销毁系统
     */
    destroy() {
        // 保存数据
        this.saveBlacklistAndWhitelist();
        
        // 清理定时器
        clearInterval(this.tokenRefreshInterval);
        clearInterval(this.cleanupInterval);
        clearInterval(this.statisticsInterval);
        
        // 清理存储
        this.sessionStore.clear();
        this.blacklist.clear();
        this.whitelist.clear();
        this.antiHotlinkTokens.clear();
        
        this.isInitialized = false;
        
        console.log('[防盗链系统] 系统已销毁');
    }
}

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AntiHotlinkIllegalUserDetector;
} else if (typeof window !== 'undefined') {
    window.AntiHotlinkIllegalUserDetector = AntiHotlinkIllegalUserDetector;
}
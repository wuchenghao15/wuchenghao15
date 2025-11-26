/**
 * 数据库访问互验机制
 * 提供多层验证和安全检查，确保数据库访问的安全性和可靠性
 */

class DatabaseAccessValidator {
    constructor(databaseManager) {
        this.dbManager = databaseManager;
        this.accessHistory = new Map(); // 访问历史记录
        this.blacklist = new Set(); // IP黑名单
        this.suspiciousPatterns = new Map(); // 可疑模式检测
        this.validationRules = new Map(); // 验证规则
        this.sessionTokens = new Map(); // 会话令牌
        this.rateLimits = new Map(); // 频率限制
        this.auditLog = []; // 审计日志
        
        this.initializeValidationRules();
        this.loadBlacklist();
        this.startAuditLogger();
    }

    /**
     * 初始化验证规则
     */
    initializeValidationRules() {
        // SQL注入检测规则
        this.validationRules.set('sqlInjection', {
            patterns: [
                /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/i,
                /(--|\*\/|\/\*|;|'|\"|`|xp_|sp_)/,
                /(\b(OR|AND)\s+\d+\s*=\s*\d+)/i,
                /(\b(OR|AND)\s+['"].*['"]\s*=\s*['"].*['"])/i
            ],
            action: 'block',
            severity: 'high'
        });

        // XSS攻击检测规则
        this.validationRules.set('xss', {
            patterns: [
                /(<script[^>]*>.*?<\/script>)/gi,
                /(javascript:|vbscript:|onload=|onerror=)/gi,
                /(<iframe[^>]*>)/gi,
                /(eval\s*\(|alert\s*\(|confirm\s*\()/gi
            ],
            action: 'block',
            severity: 'high'
        });

        // 异常访问模式检测
        this.validationRules.set('abnormalAccess', {
            patterns: [
                { type: 'frequency', threshold: 100, window: 60000 }, // 每分钟100次请求
                { type: 'burst', threshold: 20, window: 5000 }, // 5秒内20次请求
                { type: 'concurrent', threshold: 10 } // 并发连接数
            ],
            action: 'throttle',
            severity: 'medium'
        });

        // 数据完整性验证规则
        this.validationRules.set('dataIntegrity', {
            maxFieldLength: 10000,
            allowedTypes: ['string', 'number', 'boolean', 'date'],
            requiredFields: ['timestamp', 'source'],
            action: 'validate',
            severity: 'medium'
        });

        console.log('🔐 数据库访问验证规则已初始化');
    }

    /**
     * 加载IP黑名单
     */
    async loadBlacklist() {
        try {
            const blacklistData = await this.dbManager.getSystemFactor('BlacklistedIPs');
            if (blacklistData) {
                const ips = JSON.parse(blacklistData);
                ips.forEach(ip => this.blacklist.add(ip));
                console.log(`🚫 已加载 ${ips.length} 个黑名单IP`);
            }
        } catch (error) {
            console.warn('⚠️ 加载IP黑名单失败:', error.message);
        }
    }

    /**
     * 启动审计日志记录器
     */
    startAuditLogger() {
        setInterval(() => {
            this.flushAuditLog();
        }, 30000); // 每30秒刷新一次审计日志
    }

    /**
     * 验证数据库访问请求
     */
    async validateAccess(request) {
        const requestId = this.generateRequestId();
        const startTime = Date.now();
        
        try {
            // 1. 基础验证
            const basicValidation = this.performBasicValidation(request);
            if (!basicValidation.valid) {
                return this.createValidationResult(false, basicValidation.reason, requestId);
            }

            // 2. IP黑名单检查
            const ipCheck = this.checkIPBlacklist(request.ip);
            if (!ipCheck.allowed) {
                return this.createValidationResult(false, ipCheck.reason, requestId);
            }

            // 3. 频率限制检查
            const rateLimitCheck = this.checkRateLimit(request.ip);
            if (!rateLimitCheck.allowed) {
                return this.createValidationResult(false, rateLimitCheck.reason, requestId);
            }

            // 4. 会话验证
            const sessionCheck = this.validateSession(request);
            if (!sessionCheck.valid) {
                return this.createValidationResult(false, sessionCheck.reason, requestId);
            }

            // 5. SQL注入检测
            const sqlCheck = this.detectSQLInjection(request.query || request.data);
            if (sqlCheck.detected) {
                return this.createValidationResult(false, 'SQL注入攻击检测', requestId);
            }

            // 6. XSS攻击检测
            const xssCheck = this.detectXSS(request.data || request.params);
            if (xssCheck.detected) {
                return this.createValidationResult(false, 'XSS攻击检测', requestId);
            }

            // 7. 数据完整性验证
            const integrityCheck = this.validateDataIntegrity(request.data);
            if (!integrityCheck.valid) {
                return this.createValidationResult(false, integrityCheck.reason, requestId);
            }

            // 8. 异常模式检测
            const patternCheck = this.detectAbnormalPatterns(request);
            if (patternCheck.suspicious) {
                await this.handleSuspiciousActivity(request, patternCheck.reason);
                return this.createValidationResult(false, patternCheck.reason, requestId);
            }

            // 记录成功访问
            this.recordAccess(request, true, startTime);
            
            return this.createValidationResult(true, '访问验证通过', requestId);

        } catch (error) {
            console.error('❌ 访问验证异常:', error);
            this.recordAccess(request, false, startTime, error.message);
            return this.createValidationResult(false, '验证过程异常', requestId);
        }
    }

    /**
     * 执行基础验证
     */
    performBasicValidation(request) {
        if (!request.ip) {
            return { valid: false, reason: '缺少IP地址' };
        }

        if (!request.timestamp) {
            return { valid: false, reason: '缺少时间戳' };
        }

        if (!request.source) {
            return { valid: false, reason: '缺少访问源标识' };
        }

        // 检查时间戳有效性（防止重放攻击）
        const now = Date.now();
        const requestTime = new Date(request.timestamp).getTime();
        if (Math.abs(now - requestTime) > 300000) { // 5分钟窗口
            return { valid: false, reason: '请求时间戳无效' };
        }

        return { valid: true };
    }

    /**
     * 检查IP黑名单
     */
    checkIPBlacklist(ip) {
        if (this.blacklist.has(ip)) {
            return { allowed: false, reason: 'IP地址在黑名单中' };
        }

        // 检查IP段黑名单
        for (const blockedIP of this.blacklist) {
            if (blockedIP.includes('/')) {
                // CIDR格式检查
                if (this.isIPInCIDR(ip, blockedIP)) {
                    return { allowed: false, reason: 'IP段在黑名单中' };
                }
            }
        }

        return { allowed: true };
    }

    /**
     * 检查频率限制
     */
    checkRateLimit(ip) {
        const now = Date.now();
        const windowStart = now - 60000; // 1分钟窗口
        
        if (!this.rateLimits.has(ip)) {
            this.rateLimits.set(ip, []);
        }
        
        const requests = this.rateLimits.get(ip);
        
        // 清理过期记录
        const validRequests = requests.filter(time => time > windowStart);
        this.rateLimits.set(ip, validRequests);
        
        // 检查频率限制
        if (validRequests.length >= 100) { // 每分钟最多100次请求
            return { allowed: false, reason: '请求频率超过限制' };
        }
        
        // 添加当前请求
        validRequests.push(now);
        
        return { allowed: true };
    }

    /**
     * 验证会话
     */
    validateSession(request) {
        if (!request.sessionToken) {
            return { valid: false, reason: '缺少会话令牌' };
        }

        const session = this.sessionTokens.get(request.sessionToken);
        if (!session) {
            return { valid: false, reason: '无效的会话令牌' };
        }

        // 检查会话过期
        if (Date.now() > session.expiresAt) {
            this.sessionTokens.delete(request.sessionToken);
            return { valid: false, reason: '会话已过期' };
        }

        // 检查会话IP一致性
        if (session.ip !== request.ip) {
            return { valid: false, reason: '会话IP地址不匹配' };
        }

        // 更新会话活动时间
        session.lastActivity = Date.now();
        
        return { valid: true };
    }

    /**
     * 检测SQL注入
     */
    detectSQLInjection(input) {
        if (!input || typeof input !== 'string') {
            return { detected: false };
        }

        const sqlRule = this.validationRules.get('sqlInjection');
        for (const pattern of sqlRule.patterns) {
            if (pattern.test(input)) {
                console.warn('🚨 检测到SQL注入尝试:', input);
                return { detected: true, pattern: pattern.source };
            }
        }

        return { detected: false };
    }

    /**
     * 检测XSS攻击
     */
    detectXSS(input) {
        if (!input) {
            return { detected: false };
        }

        const xssRule = this.validationRules.get('xss');
        const inputStr = typeof input === 'string' ? input : JSON.stringify(input);
        
        for (const pattern of xssRule.patterns) {
            if (pattern.test(inputStr)) {
                console.warn('🚨 检测到XSS攻击尝试:', inputStr);
                return { detected: true, pattern: pattern.source };
            }
        }

        return { detected: false };
    }

    /**
     * 验证数据完整性
     */
    validateDataIntegrity(data) {
        if (!data) {
            return { valid: true }; // 空数据是有效的
        }

        const integrityRule = this.validationRules.get('dataIntegrity');
        
        // 检查数据类型
        if (typeof data !== 'object' && typeof data !== 'string' && typeof data !== 'number') {
            return { valid: false, reason: '不支持的数据类型' };
        }

        // 检查字符串长度
        if (typeof data === 'string' && data.length > integrityRule.maxFieldLength) {
            return { valid: false, reason: '数据长度超过限制' };
        }

        // 检查必填字段
        if (typeof data === 'object') {
            for (const field of integrityRule.requiredFields) {
                if (!(field in data)) {
                    return { valid: false, reason: `缺少必填字段: ${field}` };
                }
            }
        }

        return { valid: true };
    }

    /**
     * 检测异常访问模式
     */
    detectAbnormalPatterns(request) {
        const ip = request.ip;
        const now = Date.now();
        
        if (!this.suspiciousPatterns.has(ip)) {
            this.suspiciousPatterns.set(ip, {
                requests: [],
                patterns: new Set()
            });
        }
        
        const ipData = this.suspiciousPatterns.get(ip);
        ipData.requests.push(now);
        
        // 清理过期记录（1小时）
        const validRequests = ipData.requests.filter(time => now - time < 3600000);
        ipData.requests = validRequests;
        
        // 检测异常模式
        const abnormalRule = this.validationRules.get('abnormalAccess');
        
        for (const pattern of abnormalRule.patterns) {
            switch (pattern.type) {
                case 'frequency':
                    const freqRequests = validRequests.filter(time => now - time < pattern.window);
                    if (freqRequests.length > pattern.threshold) {
                        return { suspicious: true, reason: '异常高频访问' };
                    }
                    break;
                    
                case 'burst':
                    const burstRequests = validRequests.filter(time => now - time < pattern.window);
                    if (burstRequests.length > pattern.threshold) {
                        return { suspicious: true, reason: '异常突发访问' };
                    }
                    break;
                    
                case 'concurrent':
                    // 这里需要实际的并发连接数统计
                    break;
            }
        }
        
        return { suspicious: false };
    }

    /**
     * 处理可疑活动
     */
    async handleSuspiciousActivity(request, reason) {
        console.warn('🚨 检测到可疑活动:', { ip: request.ip, reason });
        
        // 记录到审计日志
        this.addToAuditLog({
            type: 'suspicious_activity',
            ip: request.ip,
            reason: reason,
            timestamp: new Date().toISOString(),
            request: this.sanitizeRequest(request)
        });
        
        // 记录到数据库
        await this.dbManager.logSystemEvent('warning', `可疑活动检测: ${reason}`, 'DatabaseValidator', null, {
            ip: request.ip,
            reason: reason
        });
        
        // 根据严重程度决定是否加入黑名单
        const suspiciousCount = this.getSuspiciousActivityCount(request.ip);
        if (suspiciousCount > 5) {
            await this.addToBlacklist(request.ip, '自动检测可疑活动');
        }
    }

    /**
     * 创建会话令牌
     */
    createSessionToken(ip, userId = null) {
        const token = this.generateSecureToken();
        const session = {
            token: token,
            ip: ip,
            userId: userId,
            createdAt: Date.now(),
            lastActivity: Date.now(),
            expiresAt: Date.now() + 1800000 // 30分钟过期
        };
        
        this.sessionTokens.set(token, session);
        
        // 清理过期会话
        this.cleanupExpiredSessions();
        
        return token;
    }

    /**
     * 记录访问
     */
    recordAccess(request, success, startTime, error = null) {
        const duration = Date.now() - startTime;
        const accessRecord = {
            ip: request.ip,
            timestamp: new Date().toISOString(),
            success: success,
            duration: duration,
            endpoint: request.endpoint,
            method: request.method,
            error: error
        };
        
        if (!this.accessHistory.has(request.ip)) {
            this.accessHistory.set(request.ip, []);
        }
        
        const ipHistory = this.accessHistory.get(request.ip);
        ipHistory.push(accessRecord);
        
        // 保持历史记录大小限制
        if (ipHistory.length > 1000) {
            ipHistory.splice(0, 500); // 删除最旧的500条记录
        }
        
        // 添加到审计日志
        this.addToAuditLog(accessRecord);
    }

    /**
     * 添加到审计日志
     */
    addToAuditLog(entry) {
        this.auditLog.push({
            ...entry,
            id: this.generateUUID(),
            timestamp: new Date().toISOString()
        });
        
        // 保持审计日志大小限制
        if (this.auditLog.length > 10000) {
            this.auditLog.splice(0, 5000);
        }
    }

    /**
     * 刷新审计日志到数据库
     */
    async flushAuditLog() {
        if (this.auditLog.length === 0) return;
        
        try {
            const logsToFlush = [...this.auditLog];
            this.auditLog = [];
            
            for (const log of logsToFlush) {
                await this.dbManager.logSystemEvent(
                    log.type || 'info',
                    log.message || log.reason || '数据库访问记录',
                    'DatabaseValidator',
                    log.userId,
                    {
                        ip: log.ip,
                        duration: log.duration,
                        success: log.success,
                        endpoint: log.endpoint,
                        method: log.method,
                        error: log.error
                    }
                );
            }
            
            console.log(`📝 已刷新 ${logsToFlush.length} 条审计日志到数据库`);
        } catch (error) {
            console.error('❌ 刷新审计日志失败:', error);
            // 重新加入队列
            this.auditLog.unshift(...logsToFlush);
        }
    }

    /**
     * 添加IP到黑名单
     */
    async addToBlacklist(ip, reason) {
        this.blacklist.add(ip);
        
        try {
            // 保存到数据库
            const existingBlacklist = await this.dbManager.getSystemFactor('BlacklistedIPs');
            const ips = existingBlacklist ? JSON.parse(existingBlacklist) : [];
            
            if (!ips.includes(ip)) {
                ips.push(ip);
                await this.dbManager.updateSystemFactor('BlacklistedIPs', JSON.stringify(ips));
                
                await this.dbManager.logSystemEvent('warning', `IP已加入黑名单: ${ip}`, 'DatabaseValidator', null, {
                    ip: ip,
                    reason: reason
                });
                
                console.log(`🚫 IP ${ip} 已加入黑名单: ${reason}`);
            }
        } catch (error) {
            console.error('❌ 添加IP到黑名单失败:', error);
        }
    }

    /**
     * 从黑名单移除IP
     */
    async removeFromBlacklist(ip) {
        this.blacklist.delete(ip);
        
        try {
            const existingBlacklist = await this.dbManager.getSystemFactor('BlacklistedIPs');
            const ips = existingBlacklist ? JSON.parse(existingBlacklist) : [];
            
            const index = ips.indexOf(ip);
            if (index > -1) {
                ips.splice(index, 1);
                await this.dbManager.updateSystemFactor('BlacklistedIPs', JSON.stringify(ips));
                
                await this.dbManager.logSystemEvent('info', `IP已从黑名单移除: ${ip}`, 'DatabaseValidator');
                
                console.log(`✅ IP ${ip} 已从黑名单移除`);
            }
        } catch (error) {
            console.error('❌ 从黑名单移除IP失败:', error);
        }
    }

    /**
     * 获取可疑活动计数
     */
    getSuspiciousActivityCount(ip) {
        const ipData = this.suspiciousPatterns.get(ip);
        return ipData ? ipData.requests.length : 0;
    }

    /**
     * 清理过期会话
     */
    cleanupExpiredSessions() {
        const now = Date.now();
        const expiredTokens = [];
        
        for (const [token, session] of this.sessionTokens) {
            if (now > session.expiresAt) {
                expiredTokens.push(token);
            }
        }
        
        expiredTokens.forEach(token => this.sessionTokens.delete(token));
        
        if (expiredTokens.length > 0) {
            console.log(`🧹 清理了 ${expiredTokens.length} 个过期会话`);
        }
    }

    /**
     * 检查IP是否在CIDR范围内
     */
    isIPInCIDR(ip, cidr) {
        // 简化的CIDR检查实现
        const [network, prefixLength] = cidr.split('/');
        const networkParts = network.split('.').map(Number);
        const ipParts = ip.split('.').map(Number);
        const mask = parseInt(prefixLength);
        
        for (let i = 0; i < 4; i++) {
            const networkByte = networkParts[i];
            const ipByte = ipParts[i];
            const bits = Math.min(mask - i * 8, 8);
            
            if (bits <= 0) break;
            
            const networkMask = (255 << (8 - bits)) & 255;
            if ((networkByte & networkMask) !== (ipByte & networkMask)) {
                return false;
            }
        }
        
        return true;
    }

    /**
     * 清理请求对象（移除敏感信息）
     */
    sanitizeRequest(request) {
        const sanitized = { ...request };
        delete sanitized.password;
        delete sanitized.token;
        delete sanitized.sessionToken;
        return sanitized;
    }

    /**
     * 创建验证结果
     */
    createValidationResult(success, reason, requestId) {
        return {
            success: success,
            reason: reason,
            requestId: requestId,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 生成请求ID
     */
    generateRequestId() {
        return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 生成安全令牌
     */
    generateSecureToken() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    /**
     * 生成UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * 获取验证统计信息
     */
    getValidationStats() {
        const stats = {
            totalRequests: 0,
            successfulRequests: 0,
            blockedRequests: 0,
            blacklistedIPs: this.blacklist.size,
            activeSessions: this.sessionTokens.size,
            suspiciousActivities: 0,
            auditLogSize: this.auditLog.length
        };

        for (const [ip, history] of this.accessHistory) {
            history.forEach(record => {
                stats.totalRequests++;
                if (record.success) {
                    stats.successfulRequests++;
                } else {
                    stats.blockedRequests++;
                }
            });
        }

        for (const [ip, data] of this.suspiciousPatterns) {
            stats.suspiciousActivities += data.requests.length;
        }

        return stats;
    }

    /**
     * 导出验证报告
     */
    async exportValidationReport() {
        const report = {
            timestamp: new Date().toISOString(),
            stats: this.getValidationStats(),
            blacklistedIPs: Array.from(this.blacklist),
            recentAuditLog: this.auditLog.slice(-100), // 最近100条记录
            validationRules: Array.from(this.validationRules.entries()).map(([name, rule]) => ({
                name: name,
                patterns: rule.patterns,
                action: rule.action,
                severity: rule.severity
            }))
        };

        await this.dbManager.logSystemEvent('info', '导出验证报告', 'DatabaseValidator', null, {
            stats: report.stats,
            blacklistedIPsCount: report.blacklistedIPs.length
        });

        return report;
    }
}

// 导出类
if (typeof window !== 'undefined') {
    window.DatabaseAccessValidator = DatabaseAccessValidator;
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseAccessValidator;
}
/**
 * 数据库安全增强模块
 * 提供异步锁、行级锁、防暴力破解、端口攻击防护等功能
 */

class DatabaseSecurity {
    constructor() {
        this.locks = new Map(); // 存储锁信息
        this.attemptCounts = new Map(); // 记录失败尝试次数
        this.blockedIPs = new Map(); // 被封禁的IP列表
        this.suspiciousActivities = new Map(); // 可疑活动记录
        
        // 配置参数
        this.config = {
            maxFailedAttempts: 5, // 最大失败尝试次数
            lockoutDuration: 15 * 60 * 1000, // 锁定时间15分钟
            maxLockDuration: 60 * 60 * 1000, // 最大锁定时间1小时
            lockTimeout: 30 * 1000, // 锁超时时间30秒
            suspiciousThreshold: 10, // 可疑活动阈值
            portScanThreshold: 20, // 端口扫描阈值
            auditLogRetention: 90 * 24 * 60 * 60 * 1000 // 审计日志保留90天
        };
        
        this.initializeSecurityMonitoring();
    }

    /**
     * 初始化安全监控
     */
    initializeSecurityMonitoring() {
        // 定期清理过期的锁和封禁记录
        setInterval(() => {
            this.cleanupExpiredLocks();
            this.cleanupExpiredBlocks();
            this.cleanupOldAuditLogs();
        }, 5 * 60 * 1000); // 每5分钟执行一次清理

        // 监控可疑活动
        setInterval(() => {
            this.detectSuspiciousActivities();
        }, 60 * 1000); // 每分钟检查一次
    }

    /**
     * 获取异步锁
     * @param {string} resource - 资源标识符
     * @param {string} requestId - 请求ID
     * @param {number} timeout - 超时时间
     * @returns {Promise<boolean>} 是否成功获取锁
     */
    async acquireLock(resource, requestId, timeout = this.config.lockTimeout) {
        return new Promise((resolve, reject) => {
            const lockKey = `${resource}:${requestId}`;
            const now = Date.now();
            
            // 检查是否已有锁存在
            if (this.locks.has(resource)) {
                const existingLock = this.locks.get(resource);
                
                // 检查锁是否过期
                if (now - existingLock.timestamp > existingLock.timeout) {
                    this.locks.delete(resource);
                } else {
                    // 锁仍然有效，无法获取
                    resolve(false);
                    return;
                }
            }

            // 创建新锁
            const lock = {
                resourceId: resource,
                requestId: requestId,
                timestamp: now,
                timeout: timeout,
                acquired: true
            };

            this.locks.set(resource, lock);
            
            // 设置锁超时自动释放
            setTimeout(() => {
                this.releaseLock(resource, requestId);
            }, timeout);

            // 记录锁获取日志
            this.logSecurityEvent('LOCK_ACQUIRED', {
                resource,
                requestId,
                timeout
            });

            resolve(true);
        });
    }

    /**
     * 释放锁
     * @param {string} resource - 资源标识符
     * @param {string} requestId - 请求ID
     * @returns {boolean} 是否成功释放
     */
    releaseLock(resource, requestId) {
        const lock = this.locks.get(resource);
        
        if (lock && lock.requestId === requestId) {
            this.locks.delete(resource);
            
            this.logSecurityEvent('LOCK_RELEASED', {
                resource,
                requestId,
                duration: Date.now() - lock.timestamp
            });
            
            return true;
        }
        
        return false;
    }

    /**
     * 检查IP是否被封禁
     * @param {string} ip - IP地址
     * @returns {Object} 封禁状态信息
     */
    checkIPBlockStatus(ip) {
        const blockInfo = this.blockedIPs.get(ip);
        
        if (!blockInfo) {
            return { blocked: false };
        }

        const now = Date.now();
        if (now > blockInfo.expiryTime) {
            this.blockedIPs.delete(ip);
            return { blocked: false };
        }

        return {
            blocked: true,
            reason: blockInfo.reason,
            remainingTime: blockInfo.expiryTime - now,
            attemptCount: blockInfo.attemptCount
        };
    }

    /**
     * 记录失败尝试
     * @param {string} ip - IP地址
     * @param {string} identifier - 用户标识符（用户名/邮箱等）
     * @param {string} action - 操作类型
     * @returns {Object} 处理结果
     */
    recordFailedAttempt(ip, identifier, action = 'LOGIN') {
        const key = `${ip}:${identifier}`;
        const now = Date.now();
        
        // 获取当前失败记录
        let attemptRecord = this.attemptCounts.get(key);
        
        if (!attemptRecord) {
            attemptRecord = {
                ip: ip,
                identifier: identifier,
                attempts: 0,
                firstAttempt: now,
                lastAttempt: now,
                actions: []
            };
        }

        // 更新失败记录
        attemptRecord.attempts++;
        attemptRecord.lastAttempt = now;
        attemptRecord.actions.push({
            action: action,
            timestamp: now
        });

        this.attemptCounts.set(key, attemptRecord);

        // 检查是否需要封禁
        if (attemptRecord.attempts >= this.config.maxFailedAttempts) {
            const blockDuration = Math.min(
                this.config.lockoutDuration * Math.pow(2, attemptRecord.attempts - this.config.maxFailedAttempts),
                this.config.maxLockDuration
            );

            this.blockIP(ip, 'BRUTE_FORCE_ATTEMPT', blockDuration, attemptRecord.attempts);
            
            // 清理失败记录
            this.attemptCounts.delete(key);

            return {
                blocked: true,
                reason: 'BRUTE_FORCE_ATTEMPT',
                duration: blockDuration,
                attempts: attemptRecord.attempts
            };
        }

        return {
            blocked: false,
            attempts: attemptRecord.attempts,
            remainingAttempts: this.config.maxFailedAttempts - attemptRecord.attempts
        };
    }

    /**
     * 封禁IP地址
     * @param {string} ip - IP地址
     * @param {string} reason - 封禁原因
     * @param {number} duration - 封禁时长
     * @param {number} attemptCount - 尝试次数
     */
    blockIP(ip, reason, duration, attemptCount = 0) {
        const now = Date.now();
        const blockInfo = {
            ip: ip,
            reason: reason,
            blockTime: now,
            expiryTime: now + duration,
            attemptCount: attemptCount
        };

        this.blockedIPs.set(ip, blockInfo);

        this.logSecurityEvent('IP_BLOCKED', {
            ip,
            reason,
            duration,
            attemptCount,
            expiryTime: blockInfo.expiryTime
        });

        // 如果是暴力破解，触发高级别安全警报
        if (reason === 'BRUTE_FORCE_ATTEMPT') {
            this.triggerSecurityAlert('BRUTE_FORCE_DETECTED', {
                ip,
                attemptCount,
                duration
            });
        }
    }

    /**
     * 检测可疑活动
     */
    detectSuspiciousActivities() {
        const now = Date.now();
        const timeWindow = 5 * 60 * 1000; // 5分钟时间窗口

        // 检测端口扫描
        this.detectPortScanning(timeWindow);
        
        // 检测异常登录模式
        this.detectAbnormalLoginPatterns(timeWindow);
        
        // 检测频繁失败操作
        this.detectFrequentFailures(timeWindow);
    }

    /**
     * 检测端口扫描
     * @param {number} timeWindow - 时间窗口
     */
    detectPortScanning(timeWindow) {
        const ipPortAttempts = new Map();

        // 统计每个IP的端口访问尝试
        for (const [key, record] of this.attemptCounts) {
            const [ip] = key.split(':');
            
            if (now - record.lastAttempt <= timeWindow) {
                if (!ipPortAttempts.has(ip)) {
                    ipPortAttempts.set(ip, []);
                }
                ipPortAttempts.get(ip).push(record);
            }
        }

        // 检测超过阈值的IP
        for (const [ip, attempts] of ipPortAttempts) {
            if (attempts.length >= this.config.portScanThreshold) {
                this.blockIP(ip, 'PORT_SCAN_DETECTED', this.config.maxLockDuration, attempts.length);
                this.triggerSecurityAlert('PORT_SCAN_DETECTED', {
                    ip,
                    attemptCount: attempts.length,
                    timeWindow
                });
            }
        }
    }

    /**
     * 检测异常登录模式
     * @param {number} timeWindow - 时间窗口
     */
    detectAbnormalLoginPatterns(timeWindow) {
        // 检测同一IP短时间内尝试多个不同账户
        const ipUserAttempts = new Map();

        for (const [key, record] of this.attemptCounts) {
            const [ip, identifier] = key.split(':');
            
            if (now - record.lastAttempt <= timeWindow) {
                if (!ipUserAttempts.has(ip)) {
                    ipUserAttempts.set(ip, new Set());
                }
                ipUserAttempts.get(ip).add(identifier);
            }
        }

        for (const [ip, userSet] of ipUserAttempts) {
            if (userSet.size >= this.config.suspiciousThreshold) {
                this.triggerSecurityAlert('SUSPICIOUS_LOGIN_PATTERN', {
                    ip,
                    uniqueUsers: userSet.size,
                    timeWindow
                });
            }
        }
    }

    /**
     * 检测频繁失败操作
     * @param {number} timeWindow - 时间窗口
     */
    detectFrequentFailures(timeWindow) {
        // 实现频繁失败操作检测逻辑
        // 这里可以添加更多具体的检测规则
    }

    /**
     * 触发安全警报
     * @param {string} alertType - 警报类型
     * @param {Object} details - 警报详情
     */
    triggerSecurityAlert(alertType, details) {
        const alert = {
            type: alertType,
            timestamp: Date.now(),
            details: details,
            severity: this.getAlertSeverity(alertType)
        };

        this.logSecurityEvent('SECURITY_ALERT', alert);

        // 可以在这里添加更多的警报处理逻辑，如发送通知等
        console.warn(`🚨 安全警报: ${alertType}`, details);
    }

    /**
     * 获取警报严重程度
     * @param {string} alertType - 警报类型
     * @returns {string} 严重程度
     */
    getAlertSeverity(alertType) {
        const severityMap = {
            'BRUTE_FORCE_DETECTED': 'HIGH',
            'PORT_SCAN_DETECTED': 'HIGH',
            'SUSPICIOUS_LOGIN_PATTERN': 'MEDIUM',
            'FREQUENT_FAILURES': 'LOW'
        };

        return severityMap[alertType] || 'MEDIUM';
    }

    /**
     * 记录安全事件
     * @param {string} eventType - 事件类型
     * @param {Object} details - 事件详情
     */
    logSecurityEvent(eventType, details) {
        const event = {
            type: eventType,
            timestamp: Date.now(),
            details: details
        };

        // 这里可以集成到数据库日志系统
        console.log(`[安全事件] ${eventType}:`, details);
        
        // 异步保存到数据库
        this.saveSecurityEventToDatabase(event);
    }

    /**
     * 保存安全事件到数据库
     * @param {Object} event - 安全事件
     */
    async saveSecurityEventToDatabase(event) {
        try {
            // 这里实现数据库保存逻辑
            // await Database.saveSecurityEvent(event);
        } catch (error) {
            console.error('保存安全事件失败:', error);
        }
    }

    /**
     * 清理过期锁
     */
    cleanupExpiredLocks() {
        const now = Date.now();
        
        for (const [resource, lock] of this.locks) {
            if (now - lock.timestamp > lock.timeout) {
                this.locks.delete(resource);
                this.logSecurityEvent('LOCK_EXPIRED', {
                    resource,
                    requestId: lock.requestId,
                    duration: now - lock.timestamp
                });
            }
        }
    }

    /**
     * 清理过期封禁
     */
    cleanupExpiredBlocks() {
        const now = Date.now();
        
        for (const [ip, blockInfo] of this.blockedIPs) {
            if (now > blockInfo.expiryTime) {
                this.blockedIPs.delete(ip);
                this.logSecurityEvent('IP_BLOCK_EXPIRED', {
                    ip,
                    reason: blockInfo.reason,
                    blockDuration: now - blockInfo.blockTime
                });
            }
        }
    }

    /**
     * 清理旧的审计日志
     */
    cleanupOldAuditLogs() {
        const cutoffTime = Date.now() - this.config.auditLogRetention;
        
        // 这里实现清理逻辑
        // await Database.cleanupOldAuditLogs(cutoffTime);
    }

    /**
     * 获取安全统计信息
     * @returns {Object} 统计信息
     */
    getSecurityStats() {
        return {
            activeLocks: this.locks.size,
            blockedIPs: this.blockedIPs.size,
            failedAttempts: this.attemptCounts.size,
            suspiciousActivities: this.suspiciousActivities.size
        };
    }

    /**
     * 重置用户失败尝试计数
     * @param {string} ip - IP地址
     * @param {string} identifier - 用户标识符
     */
    resetFailedAttempts(ip, identifier) {
        const key = `${ip}:${identifier}`;
        this.attemptCounts.delete(key);
        
        this.logSecurityEvent('FAILED_ATTEMPTS_RESET', {
            ip,
            identifier
        });
    }
}

// 创建全局实例
const dbSecurity = new DatabaseSecurity();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseSecurity;
} else {
    window.DatabaseSecurity = DatabaseSecurity;
    window.dbSecurity = dbSecurity;
}
/**
 * 时区地址异常检测系统
 * 检测IP地址、地理位置、时区异常，提供实时监控和预警机制
 */

class TimezoneAddressDetector {
    constructor(databaseManager) {
        this.dbManager = databaseManager;
        this.detectionRules = new Map();
        this.suspiciousIPs = new Map();
        this.locationHistory = new Map();
        this.timezoneHistory = new Map();
        this.detectionInterval = null;
        this.alertThresholds = {
            ipChangeFrequency: 3, // 3次IP变化
            timezoneChangeFrequency: 2, // 2次时区变化
            locationDistance: 1000, // 1000km距离异常
            timeWindow: 3600000, // 1小时时间窗口
            suspiciousCountries: ['CN', 'RU', 'KP', 'IR'], // 可疑国家代码
            vpnProviders: ['VPN', 'Proxy', 'Tor'], // VPN提供商标识
            maxSessionDuration: 7200000 // 2小时最大会话时长
        };
        
        this.initializeDetectionRules();
        this.startDetection();
    }

    /**
     * 初始化检测规则
     */
    initializeDetectionRules() {
        // IP地址异常检测规则
        this.detectionRules.set('ipAnomaly', {
            name: 'IP地址异常',
            check: (data) => this.checkIPAnomaly(data),
            severity: 'high',
            action: 'alert'
        });

        // 时区异常检测规则
        this.detectionRules.set('timezoneAnomaly', {
            name: '时区异常',
            check: (data) => this.checkTimezoneAnomaly(data),
            severity: 'medium',
            action: 'alert'
        });

        // 地理位置异常检测规则
        this.detectionRules.set('locationAnomaly', {
            name: '地理位置异常',
            check: (data) => this.checkLocationAnomaly(data),
            severity: 'high',
            action: 'alert'
        });

        // 会话异常检测规则
        this.detectionRules.set('sessionAnomaly', {
            name: '会话异常',
            check: (data) => this.checkSessionAnomaly(data),
            severity: 'medium',
            action: 'monitor'
        });

        // 设备指纹异常检测规则
        this.detectionRules.set('fingerprintAnomaly', {
            name: '设备指纹异常',
            check: (data) => this.checkFingerprintAnomaly(data),
            severity: 'medium',
            action: 'alert'
        });

        console.log('🔍 时区地址异常检测规则已初始化');
    }

    /**
     * 启动检测
     */
    startDetection() {
        // 立即执行一次检测
        this.performDetection();
        
        // 每5分钟执行一次检测
        this.detectionInterval = setInterval(() => {
            this.performDetection();
        }, 300000);
        
        console.log('🔍 时区地址异常检测已启动');
    }

    /**
     * 执行检测
     */
    async performDetection() {
        try {
            const currentData = await this.collectCurrentData();
            const sessionId = this.getSessionId();
            
            // 更新历史记录
            this.updateHistory(sessionId, currentData);
            
            // 执行所有检测规则
            const detectionResults = [];
            for (const [ruleId, rule] of this.detectionRules) {
                try {
                    const result = await rule.check(currentData);
                    if (result.detected) {
                        detectionResults.push({
                            ruleId,
                            ruleName: rule.name,
                            severity: rule.severity,
                            action: rule.action,
                            details: result.details,
                            timestamp: new Date().toISOString()
                        });
                    }
                } catch (error) {
                    console.error(`❌ 检测规则 ${ruleId} 执行失败:`, error);
                }
            }
            
            // 处理检测结果
            if (detectionResults.length > 0) {
                await this.handleDetectionResults(sessionId, detectionResults);
            }
            
            // 记录检测日志
            await this.logDetection(sessionId, currentData, detectionResults);
            
        } catch (error) {
            console.error('❌ 检测执行失败:', error);
            await this.dbManager.logSystemEvent('error', '时区地址检测失败', 'TimezoneAddressDetector', null, {
                error: error.message
            });
        }
    }

    /**
     * 收集当前数据
     */
    async collectCurrentData() {
        const data = {
            timestamp: new Date().toISOString(),
            sessionId: this.getSessionId(),
            userAgent: navigator.userAgent,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth
            },
            window: {
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                outerWidth: window.outerWidth,
                outerHeight: window.outerHeight
            },
            timezone: {
                offset: new Date().getTimezoneOffset(),
                name: Intl.DateTimeFormat().resolvedOptions().timeZone,
                dst: this.isDSTActive()
            },
            language: {
                browser: navigator.language,
                system: navigator.systemLanguage || navigator.language,
                languages: navigator.languages
            },
            platform: {
                os: navigator.platform,
                vendor: navigator.vendor,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine
            },
            connection: this.getConnectionInfo(),
            battery: await this.getBatteryInfo(),
            geolocation: await this.getGeolocationData(),
            ip: await this.getIPAddress(),
            fingerprint: this.generateFingerprint()
        };

        return data;
    }

    /**
     * 检查IP地址异常
     */
    async checkIPAnomaly(data) {
        const sessionId = data.sessionId;
        const currentIP = data.ip;
        
        if (!currentIP) {
            return { detected: false, details: '无法获取IP地址' };
        }

        // 检查IP是否在可疑IP列表中
        if (this.suspiciousIPs.has(currentIP)) {
            const suspiciousInfo = this.suspiciousIPs.get(currentIP);
            return {
                detected: true,
                details: {
                    type: 'known_suspicious_ip',
                    ip: currentIP,
                    reason: suspiciousInfo.reason,
                    firstSeen: suspiciousInfo.firstSeen
                }
            };
        }

        // 检查IP变化频率
        const ipHistory = this.locationHistory.get(sessionId)?.ipHistory || [];
        const recentIPs = ipHistory.filter(record => 
            new Date() - new Date(record.timestamp) < this.alertThresholds.timeWindow
        );

        if (recentIPs.length >= this.alertThresholds.ipChangeFrequency) {
            const uniqueIPs = new Set(recentIPs.map(r => r.ip));
            if (uniqueIPs.size >= this.alertThresholds.ipChangeFrequency) {
                return {
                    detected: true,
                    details: {
                        type: 'frequent_ip_changes',
                        currentIP: currentIP,
                        uniqueIPs: Array.from(uniqueIPs),
                        changeCount: uniqueIPs.size,
                        timeWindow: this.alertThresholds.timeWindow
                    }
                };
            }
        }

        // 检查IP地址类型
        const ipAnalysis = this.analyzeIPAddress(currentIP);
        if (ipAnalysis.isSuspicious) {
            return {
                detected: true,
                details: {
                    type: 'suspicious_ip_type',
                    ip: currentIP,
                    analysis: ipAnalysis
                }
            };
        }

        return { detected: false };
    }

    /**
     * 检查时区异常
     */
    async checkTimezoneAnomaly(data) {
        const sessionId = data.sessionId;
        const currentTimezone = data.timezone.name;
        
        if (!currentTimezone) {
            return { detected: false, details: '无法获取时区信息' };
        }

        // 检查时区是否在允许列表中
        const allowedTimezones = [
            'Asia/Shanghai', 'Asia/Beijing', 'Asia/Hong_Kong',
            'Asia/Taipei', 'Asia/Tokyo', 'Asia/Seoul',
            'Asia/Singapore', 'Asia/Kuala_Lumpur'
        ];

        if (!allowedTimezones.includes(currentTimezone)) {
            return {
                detected: true,
                details: {
                    type: 'unallowed_timezone',
                    timezone: currentTimezone,
                    allowedTimezones: allowedTimezones
                }
            };
        }

        // 检查时区变化频率
        const timezoneHistory = this.timezoneHistory.get(sessionId) || [];
        const recentTimezones = timezoneHistory.filter(record => 
            new Date() - new Date(record.timestamp) < this.alertThresholds.timeWindow
        );

        if (recentTimezones.length >= this.alertThresholds.timezoneChangeFrequency) {
            const uniqueTimezones = new Set(recentTimezones.map(r => r.timezone));
            if (uniqueTimezones.size >= this.alertThresholds.timezoneChangeFrequency) {
                return {
                    detected: true,
                    details: {
                        type: 'frequent_timezone_changes',
                        currentTimezone: currentTimezone,
                        uniqueTimezones: Array.from(uniqueTimezones),
                        changeCount: uniqueTimezones.size,
                        timeWindow: this.alertThresholds.timeWindow
                    }
                };
            }
        }

        // 检查时区与地理位置的一致性
        if (data.geolocation && data.geolocation.country) {
            const expectedTimezones = this.getExpectedTimezones(data.geolocation.country);
            if (!expectedTimezones.includes(currentTimezone)) {
                return {
                    detected: true,
                    details: {
                        type: 'timezone_location_mismatch',
                        timezone: currentTimezone,
                        location: data.geolocation,
                        expectedTimezones: expectedTimezones
                    }
                };
            }
        }

        return { detected: false };
    }

    /**
     * 检查地理位置异常
     */
    async checkLocationAnomaly(data) {
        const sessionId = data.sessionId;
        const currentLocation = data.geolocation;
        
        if (!currentLocation || !currentLocation.latitude || !currentLocation.longitude) {
            return { detected: false, details: '无法获取地理位置信息' };
        }

        // 检查是否在可疑国家
        if (this.alertThresholds.suspiciousCountries.includes(currentLocation.country)) {
            return {
                detected: true,
                details: {
                    type: 'suspicious_country',
                    location: currentLocation,
                    suspiciousCountries: this.alertThresholds.suspiciousCountries
                }
            };
        }

        // 检查位置变化距离
        const locationHistory = this.locationHistory.get(sessionId)?.locationHistory || [];
        const recentLocations = locationHistory.filter(record => 
            new Date() - new Date(record.timestamp) < this.alertThresholds.timeWindow
        );

        for (const pastLocation of recentLocations) {
            const distance = this.calculateDistance(
                currentLocation.latitude, currentLocation.longitude,
                pastLocation.latitude, pastLocation.longitude
            );

            if (distance > this.alertThresholds.locationDistance) {
                return {
                    detected: true,
                    details: {
                        type: 'impossible_travel',
                        currentLocation: currentLocation,
                        pastLocation: pastLocation,
                        distance: distance,
                        timeDiff: new Date() - new Date(pastLocation.timestamp)
                    }
                };
            }
        }

        // 检查位置精度
        if (currentLocation.accuracy && currentLocation.accuracy > 1000) {
            return {
                detected: true,
                details: {
                    type: 'low_location_accuracy',
                    location: currentLocation,
                    accuracy: currentLocation.accuracy
                }
            };
        }

        return { detected: false };
    }

    /**
     * 检查会话异常
     */
    async checkSessionAnomaly(data) {
        const sessionId = data.sessionId;
        
        // 检查会话时长
        const sessionStart = this.getSessionStartTime(sessionId);
        if (sessionStart) {
            const sessionDuration = new Date() - sessionStart;
            if (sessionDuration > this.alertThresholds.maxSessionDuration) {
                return {
                    detected: true,
                    details: {
                        type: 'long_session',
                        duration: sessionDuration,
                        maxDuration: this.alertThresholds.maxSessionDuration
                    }
                };
            }
        }

        // 检查会话中的活动模式
        const sessionHistory = this.locationHistory.get(sessionId);
        if (sessionHistory && sessionHistory.activityHistory) {
            const inactivityPeriods = this.detectInactivityPeriods(sessionHistory.activityHistory);
            if (inactivityPeriods.length > 0) {
                return {
                    detected: true,
                    details: {
                        type: 'suspicious_inactivity',
                        inactivityPeriods: inactivityPeriods
                    }
                };
            }
        }

        return { detected: false };
    }

    /**
     * 检查设备指纹异常
     */
    async checkFingerprintAnomaly(data) {
        const sessionId = data.sessionId;
        const currentFingerprint = data.fingerprint;
        
        // 获取历史指纹
        const sessionHistory = this.locationHistory.get(sessionId);
        if (sessionHistory && sessionHistory.fingerprintHistory) {
            const pastFingerprints = sessionHistory.fingerprintHistory;
            
            for (const pastFingerprint of pastFingerprints) {
                const similarity = this.calculateFingerprintSimilarity(currentFingerprint, pastFingerprint.fingerprint);
                if (similarity < 0.8) { // 相似度低于80%
                    return {
                        detected: true,
                        details: {
                            type: 'fingerprint_mismatch',
                            currentFingerprint: currentFingerprint,
                            pastFingerprint: pastFingerprint.fingerprint,
                            similarity: similarity
                        }
                    };
                }
            }
        }

        // 检查可疑的用户代理
        if (this.isSuspiciousUserAgent(data.userAgent)) {
            return {
                detected: true,
                details: {
                    type: 'suspicious_user_agent',
                    userAgent: data.userAgent
                }
            };
        }

        return { detected: false };
    }

    /**
     * 处理检测结果
     */
    async handleDetectionResults(sessionId, results) {
        for (const result of results) {
            // 根据严重程度和动作类型处理
            switch (result.action) {
                case 'alert':
                    await this.triggerAlert(sessionId, result);
                    break;
                case 'monitor':
                    await this.enhanceMonitoring(sessionId, result);
                    break;
                case 'block':
                    await this.blockSession(sessionId, result);
                    break;
            }
        }

        // 发送综合警报
        if (results.some(r => r.severity === 'high')) {
            await this.sendComprehensiveAlert(sessionId, results);
        }
    }

    /**
     * 触发警报
     */
    async triggerAlert(sessionId, result) {
        const alertData = {
            sessionId: sessionId,
            ruleId: result.ruleId,
            ruleName: result.ruleName,
            severity: result.severity,
            details: result.details,
            timestamp: result.timestamp
        };

        // 记录到数据库
        await this.dbManager.logSystemEvent('warning', `时区地址异常检测: ${result.ruleName}`, 'TimezoneAddressDetector', sessionId, alertData);

        // 发送通知（这里可以集成邮件、短信等通知系统）
        console.warn(`🚨 时区地址异常警报: ${result.ruleName}`, alertData);

        // 触发页面级别的安全响应
        this.triggerSecurityResponse(alertData);
    }

    /**
     * 触发安全响应
     */
    triggerSecurityResponse(alertData) {
        // 根据警报严重程度执行不同的安全响应
        switch (alertData.severity) {
            case 'high':
                // 高危警报：可能需要锁定会话或要求重新验证
                this.enhancedSecurityMode();
                break;
            case 'medium':
                // 中危警报：增加监控频率
                this.increaseMonitoringFrequency();
                break;
            case 'low':
                // 低危警报：记录并继续监控
                this.continueMonitoring();
                break;
        }
    }

    /**
     * 增强安全模式
     */
    enhancedSecurityMode() {
        // 显示安全警告
        this.showSecurityWarning('检测到异常活动，已启用增强安全模式');
        
        // 增加验证要求
        this.requireAdditionalVerification();
        
        // 限制某些功能
        this.restrictFunctionality();
    }

    /**
     * 显示安全警告
     */
    showSecurityWarning(message) {
        // 创建警告元素
        const warningElement = document.createElement('div');
        warningElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff4444;
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            z-index: 10000;
            font-family: Arial, sans-serif;
            font-size: 14px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            max-width: 300px;
        `;
        warningElement.textContent = message;
        
        document.body.appendChild(warningElement);
        
        // 5秒后自动移除
        setTimeout(() => {
            if (warningElement.parentNode) {
                warningElement.parentNode.removeChild(warningElement);
            }
        }, 5000);
    }

    /**
     * 获取IP地址
     */
    async getIPAddress() {
        try {
            // 尝试多个IP检测服务
            const services = [
                'https://api.ipify.org?format=json',
                'https://httpbin.org/ip',
                'https://api.ip.sb/ip'
            ];

            for (const service of services) {
                try {
                    const response = await fetch(service, {
                        timeout: 5000,
                        headers: {
                            'Accept': 'application/json'
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.ip) {
                            return data.ip;
                        } else if (data.origin) {
                            return data.origin;
                        }
                    }
                } catch (error) {
                    console.warn(`IP检测服务 ${service} 失败:`, error.message);
                    continue;
                }
            }

            // 如果所有服务都失败，返回本地IP或默认值
            return this.getLocalIP() || '192.168.1.100';
        } catch (error) {
            console.warn('获取IP地址失败:', error.message);
            return '192.168.1.100';
        }
    }

    /**
     * 获取本地IP地址
     */
    getLocalIP() {
        // 简单的本地IP检测（仅适用于开发环境）
        return null;
    }

    /**
     * 获取地理位置数据
     */
    async getGeolocationData() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve(null);
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        altitude: position.coords.altitude,
                        altitudeAccuracy: position.coords.altitudeAccuracy,
                        heading: position.coords.heading,
                        speed: position.coords.speed,
                        timestamp: position.timestamp
                    });
                },
                (error) => {
                    console.warn('获取地理位置失败:', error.message);
                    resolve(null);
                },
                {
                    timeout: 10000,
                    maximumAge: 300000, // 5分钟缓存
                    enableHighAccuracy: true
                }
            );
        });
    }

    /**
     * 获取连接信息
     */
    getConnectionInfo() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        
        if (connection) {
            return {
                effectiveType: connection.effectiveType,
                downlink: connection.downlink,
                rtt: connection.rtt,
                saveData: connection.saveData
            };
        }
        
        return null;
    }

    /**
     * 获取电池信息
     */
    async getBatteryInfo() {
        if (navigator.getBattery) {
            try {
                const battery = await navigator.getBattery();
                return {
                    level: battery.level,
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime
                };
            } catch (error) {
                console.warn('获取电池信息失败:', error.message);
            }
        }
        
        return null;
    }

    /**
     * 生成设备指纹
     */
    generateFingerprint() {
        const components = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            screen.colorDepth,
            new Date().getTimezoneOffset(),
            navigator.platform,
            navigator.hardwareConcurrency || 'unknown',
            navigator.deviceMemory || 'unknown',
            navigator.cookieEnabled,
            navigator.doNotTrack
        ];

        return this.hashString(components.join('|'));
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
        return hash.toString(16);
    }

    /**
     * 分析IP地址
     */
    analyzeIPAddress(ip) {
        const analysis = {
            isPrivate: this.isPrivateIP(ip),
            isVPN: false,
            isProxy: false,
            isSuspicious: false
        };

        // 检查是否为私有IP
        if (analysis.isPrivate) {
            analysis.isSuspicious = false;
        }

        // 检查VPN/代理特征（简化实现）
        const vpnPatterns = ['vpn', 'proxy', 'tor'];
        if (vpnPatterns.some(pattern => ip.toLowerCase().includes(pattern))) {
            analysis.isVPN = true;
            analysis.isSuspicious = true;
        }

        return analysis;
    }

    /**
     * 检查是否为私有IP
     */
    isPrivateIP(ip) {
        const privateRanges = [
            /^10\./,
            /^172\.(1[6-9]|2[0-9]|3[0-1])\./,
            /^192\.168\./,
            /^127\./,
            /^169\.254\./
        ];

        return privateRanges.some(range => range.test(ip));
    }

    /**
     * 计算两点间距离（公里）
     */
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // 地球半径（公里）
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    /**
     * 角度转弧度
     */
    toRadians(degrees) {
        return degrees * (Math.PI / 180);
    }

    /**
     * 检查是否为夏令时
     */
    isDSTActive() {
        const now = new Date();
        const jan = new Date(now.getFullYear(), 0, 1);
        const jul = new Date(now.getFullYear(), 6, 1);
        const stdOffset = Math.max(jan.getTimezoneOffset(), jul.getTimezoneOffset());
        return now.getTimezoneOffset() < stdOffset;
    }

    /**
     * 获取期望的时区
     */
    getExpectedTimezones(country) {
        const timezoneMap = {
            'CN': ['Asia/Shanghai', 'Asia/Beijing'],
            'US': ['America/New_York', 'America/Los_Angeles', 'America/Chicago'],
            'JP': ['Asia/Tokyo'],
            'KR': ['Asia/Seoul'],
            'HK': ['Asia/Hong_Kong'],
            'TW': ['Asia/Taipei']
        };
        
        return timezoneMap[country] || [];
    }

    /**
     * 检查可疑用户代理
     */
    isSuspiciousUserAgent(userAgent) {
        const suspiciousPatterns = [
            /bot/i, /crawler/i, /spider/i, /scraper/i,
            /curl/i, /wget/i, /python/i, /java/i,
            /automated/i, /script/i, /headless/i
        ];
        
        return suspiciousPatterns.some(pattern => pattern.test(userAgent));
    }

    /**
     * 计算指纹相似度
     */
    calculateFingerprintSimilarity(fp1, fp2) {
        if (fp1 === fp2) return 1.0;
        
        // 简化的相似度计算
        const chars1 = fp1.split('');
        const chars2 = fp2.split('');
        const maxLength = Math.max(chars1.length, chars2.length);
        let matches = 0;
        
        for (let i = 0; i < maxLength; i++) {
            if (chars1[i] === chars2[i]) {
                matches++;
            }
        }
        
        return matches / maxLength;
    }

    /**
     * 获取会话ID
     */
    getSessionId() {
        // 从localStorage或生成新的会话ID
        let sessionId = localStorage.getItem('detection_session_id');
        if (!sessionId) {
            sessionId = this.generateSessionId();
            localStorage.setItem('detection_session_id', sessionId);
        }
        return sessionId;
    }

    /**
     * 生成会话ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 获取会话开始时间
     */
    getSessionStartTime(sessionId) {
        const startTime = localStorage.getItem(`session_start_${sessionId}`);
        return startTime ? new Date(startTime) : null;
    }

    /**
     * 更新历史记录
     */
    updateHistory(sessionId, data) {
        // 更新位置历史
        if (!this.locationHistory.has(sessionId)) {
            this.locationHistory.set(sessionId, {
                ipHistory: [],
                locationHistory: [],
                fingerprintHistory: [],
                activityHistory: []
            });
        }

        const sessionHistory = this.locationHistory.get(sessionId);
        
        if (data.ip) {
            sessionHistory.ipHistory.push({
                ip: data.ip,
                timestamp: data.timestamp
            });
        }

        if (data.geolocation) {
            sessionHistory.locationHistory.push({
                ...data.geolocation,
                timestamp: data.timestamp
            });
        }

        if (data.fingerprint) {
            sessionHistory.fingerprintHistory.push({
                fingerprint: data.fingerprint,
                timestamp: data.timestamp
            });
        }

        sessionHistory.activityHistory.push({
            timestamp: data.timestamp,
            type: 'detection'
        });

        // 清理过期记录
        this.cleanupExpiredRecords(sessionHistory);
    }

    /**
     * 清理过期记录
     */
    cleanupExpiredRecords(sessionHistory) {
        const cutoffTime = new Date() - (24 * 60 * 60 * 1000); // 24小时前
        
        sessionHistory.ipHistory = sessionHistory.ipHistory.filter(record => 
            new Date(record.timestamp) > cutoffTime
        );
        
        sessionHistory.locationHistory = sessionHistory.locationHistory.filter(record => 
            new Date(record.timestamp) > cutoffTime
        );
        
        sessionHistory.fingerprintHistory = sessionHistory.fingerprintHistory.filter(record => 
            new Date(record.timestamp) > cutoffTime
        );
        
        sessionHistory.activityHistory = sessionHistory.activityHistory.filter(record => 
            new Date(record.timestamp) > cutoffTime
        );
    }

    /**
     * 检测不活跃时段
     */
    detectInactivityPeriods(activityHistory) {
        const inactivityPeriods = [];
        const inactivityThreshold = 30 * 60 * 1000; // 30分钟

        for (let i = 1; i < activityHistory.length; i++) {
            const timeDiff = new Date(activityHistory[i].timestamp) - new Date(activityHistory[i-1].timestamp);
            if (timeDiff > inactivityThreshold) {
                inactivityPeriods.push({
                    start: activityHistory[i-1].timestamp,
                    end: activityHistory[i].timestamp,
                    duration: timeDiff
                });
            }
        }

        return inactivityPeriods;
    }

    /**
     * 记录检测日志
     */
    async logDetection(sessionId, data, results) {
        const logData = {
            sessionId: sessionId,
            timestamp: data.timestamp,
            dataSummary: {
                ip: data.ip,
                timezone: data.timezone.name,
                location: data.geolocation ? `${data.geolocation.latitude},${data.geolocation.longitude}` : null,
                fingerprint: data.fingerprint
            },
            detectionResults: results,
            resultCount: results.length
        };

        await this.dbManager.logSystemEvent('debug', '时区地址检测完成', 'TimezoneAddressDetector', sessionId, logData);
    }

    /**
     * 增强监控
     */
    async enhanceMonitoring(sessionId, result) {
        console.log(`🔍 增强监控会话 ${sessionId}: ${result.ruleName}`);
        // 实现增强监控逻辑
    }

    /**
     * 阻止会话
     */
    async blockSession(sessionId, result) {
        console.warn(`🚫 阻止会话 ${sessionId}: ${result.ruleName}`);
        // 实现会话阻止逻辑
    }

    /**
     * 发送综合警报
     */
    async sendComprehensiveAlert(sessionId, results) {
        const highSeverityResults = results.filter(r => r.severity === 'high');
        
        await this.dbManager.logSystemEvent('critical', '时区地址高危异常检测', 'TimezoneAddressDetector', sessionId, {
            sessionId: sessionId,
            highSeverityCount: highSeverityResults.length,
            results: highSeverityResults
        });
    }

    /**
     * 增加监控频率
     */
    increaseMonitoringFrequency() {
        // 重新设置检测间隔为1分钟
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        this.detectionInterval = setInterval(() => {
            this.performDetection();
        }, 60000);
        
        console.log('🔍 已增加监控频率至每分钟一次');
    }

    /**
     * 继续监控
     */
    continueMonitoring() {
        console.log('🔍 继续正常监控');
    }

    /**
     * 要求额外验证
     */
    requireAdditionalVerification() {
        // 实现额外验证逻辑
        console.log('🔐 要求额外验证');
    }

    /**
     * 限制功能
     */
    restrictFunctionality() {
        // 实现功能限制逻辑
        console.log('🚫 限制某些功能');
    }

    /**
     * 停止检测
     */
    stopDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        console.log('🛑 时区地址异常检测已停止');
    }

    /**
     * 获取检测状态
     */
    getDetectionStatus() {
        return {
            active: this.detectionInterval !== null,
            rulesCount: this.detectionRules.size,
            suspiciousIPsCount: this.suspiciousIPs.size,
            sessionsCount: this.locationHistory.size,
            lastDetection: this.lastDetectionTime
        };
    }
}

// 导出类
if (typeof window !== 'undefined') {
    window.TimezoneAddressDetector = TimezoneAddressDetector;
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimezoneAddressDetector;
}
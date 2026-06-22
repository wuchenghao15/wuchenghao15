/**
 * MTSCOS AI System - 敏感数据管理师AI员工
 * 版本: 4.4.0
 * 描述: 专注于敏感数据识别、加密存储、安全传输和数据脱敏
 */

class SensitiveDataManager {
    constructor() {
        this.id = 'sensitive-data-manager';
        this.name = '敏感数据管理师';
        this.icon = 'fa-user-secret';
        this.color = '#be123c';
        this.gradient = 'linear-gradient(135deg, #be123c 0%, #9f1239 100%)';
        this.role = '敏感数据专家';
        this.description = '专注于敏感数据识别、加密存储、安全传输和数据脱敏处理';
        this.abilities = [
            '数据识别',
            '加密存储',
            '安全传输',
            '数据脱敏',
            '访问控制',
            '审计追踪'
        ];
        this.status = 'active';
        this.workload = 15;
        this.efficiency = 99;
        this.sensitivePatterns = this.initPatterns();
        this.encryptionKey = null;
        this.auditLog = [];
    }

    // ==================== 敏感数据模式 ====================

    initPatterns() {
        return {
            email: {
                pattern: /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/,
                risk: 'medium',
                category: 'contact',
                mask: (v) => v.replace(/(.{2}).*(@.*)/, '$1***$2')
            },
            phone: {
                pattern: /^1[3-9]\d{9}$/,
                risk: 'high',
                category: 'contact',
                mask: (v) => v.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
            },
            idCard: {
                pattern: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/,
                risk: 'critical',
                category: 'identity',
                mask: (v) => v.replace(/(\d{4})\d{10}(\d{3}[\dXx])/, '$1**********$2')
            },
            bankCard: {
                pattern: /^[1-9]\d{12,18}$/,
                risk: 'critical',
                category: 'financial',
                mask: (v) => v.replace(/(\d{4})\d+(\d{4})/, '$1 **** **** $2')
            },
            password: {
                pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/,
                risk: 'critical',
                category: 'credential',
                mask: () => '********'
            },
            creditCard: {
                pattern: /^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$/,
                risk: 'critical',
                category: 'financial',
                mask: (v) => v.replace(/\d{4}-\d{4}-\d{4}-/, '****-****-****-')
            },
            ipAddress: {
                pattern: /^(\d{1,3}\.){3}\d{1,3}$/,
                risk: 'low',
                category: 'network',
                mask: (v) => v.replace(/\d+$/, '***')
            },
            ssn: {
                pattern: /^\d{3}-\d{2}-\d{4}$/,
                risk: 'critical',
                category: 'identity',
                mask: (v) => v.replace(/\d{3}-\d{2}-/, '***-**-')
            }
        };
    }

    // ==================== 敏感数据识别 ====================

    // 扫描敏感数据
    scanSensitiveData(data) {
        const results = {
            scanned: 0,
            found: [],
            risks: { critical: 0, high: 0, medium: 0, low: 0 },
            recommendations: []
        };

        const scanObject = (obj, path = '') => {
            if (typeof obj !== 'object' || obj === null) return;

            for (const [key, value] of Object.entries(obj)) {
                results.scanned++;
                const fullPath = path ? `${path}.${key}` : key;

                if (typeof value === 'string') {
                    const detected = this.detectInString(value, key);
                    if (detected) {
                        results.found.push({ ...detected, path: fullPath, key });
                        results.risks[detected.risk]++;
                    }
                } else if (typeof value === 'object') {
                    scanObject(value, fullPath);
                }
            }
        };

        scanObject(data);
        results.recommendations = this.generateRecommendations(results.risks);

        this.logAudit('scan', { results });
        return results;
    }

    // 检测字符串中的敏感数据
    detectInString(str, key) {
        for (const [type, config] of Object.entries(this.sensitivePatterns)) {
            if (config.pattern.test(str)) {
                return {
                    type,
                    risk: config.risk,
                    category: config.category,
                    value: str,
                    maskedValue: config.mask(str)
                };
            }
        }

        // 基于键名检测
        const keyLower = key.toLowerCase();
        if (keyLower.includes('password') || keyLower.includes('pwd')) {
            return {
                type: 'password',
                risk: 'critical',
                category: 'credential',
                value: str,
                maskedValue: '********'
            };
        }

        if (keyLower.includes('secret') || keyLower.includes('token')) {
            return {
                type: 'token',
                risk: 'high',
                category: 'credential',
                value: str,
                maskedValue: str.substring(0, 4) + '****'
            };
        }

        return null;
    }

    // 生成建议
    generateRecommendations(risks) {
        const recommendations = [];

        if (risks.critical > 0) {
            recommendations.push({
                priority: 'critical',
                message: `发现 ${risks.critical} 个高风险敏感数据，必须加密存储`
            });
        }

        if (risks.high > 0) {
            recommendations.push({
                priority: 'high',
                message: `发现 ${risks.high} 个中风险敏感数据，建议加密`
            });
        }

        if (risks.medium > 0) {
            recommendations.push({
                priority: 'medium',
                message: `发现 ${risks.medium} 个低风险敏感数据，建议脱敏`
            });
        }

        return recommendations;
    }

    // ==================== 加密存储 ====================

    // 加密数据
    async encrypt(data, options = {}) {
        const key = await this.getOrCreateKey();
        const iv = crypto.getRandomValues(new Uint8Array(12));
        
        const encoded = new TextEncoder().encode(JSON.stringify(data));
        const encrypted = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            key,
            encoded
        );

        const result = {
            encrypted: true,
            data: this.bufferToBase64(encrypted),
            iv: this.bufferToBase64(iv),
            algorithm: 'AES-GCM',
            keyId: key.keyId,
            timestamp: Date.now()
        };

        this.logAudit('encrypt', { keyId: key.keyId, timestamp: result.timestamp });
        return result;
    }

    // 解密数据
    async decrypt(encryptedData) {
        const key = await this.getKey(encryptedData.keyId);
        if (!key) {
            throw new Error('无法找到解密密钥');
        }

        const iv = this.base64ToBuffer(encryptedData.iv);
        const data = this.base64ToBuffer(encryptedData.data);

        const decrypted = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            key,
            data
        );

        const decoded = new TextDecoder().decode(decrypted);
        this.logAudit('decrypt', { keyId: encryptedData.keyId });

        return JSON.parse(decoded);
    }

    // 获取或创建密钥
    async getOrCreateKey() {
        if (this.encryptionKey) {
            return this.encryptionKey;
        }

        const key = await crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );

        key.keyId = 'key_' + Date.now();
        this.encryptionKey = key;

        return key;
    }

    // 获取密钥
    async getKey(keyId) {
        if (this.encryptionKey?.keyId === keyId) {
            return this.encryptionKey;
        }
        return null;
    }

    // 缓冲区转Base64
    bufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        bytes.forEach(b => binary += String.fromCharCode(b));
        return btoa(binary);
    }

    // Base64转缓冲区
    base64ToBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes;
    }

    // ==================== 数据脱敏 ====================

    // 脱敏数据
    desensitize(data, config = {}) {
        const result = { ...data };

        Object.entries(result).forEach(([key, value]) => {
            if (typeof value === 'string') {
                const detected = this.detectInString(value, key);
                if (detected && (config.level === 'all' || this.isHighRisk(detected.risk))) {
                    result[key] = detected.maskedValue;
                }
            } else if (typeof value === 'object' && value !== null) {
                result[key] = this.desensitize(value, config);
            }
        });

        this.logAudit('desensitize', { keys: Object.keys(result).length });
        return result;
    }

    // 是否高风险
    isHighRisk(risk) {
        return ['critical', 'high'].includes(risk);
    }

    // 脱敏字段
    desensitizeField(type, value) {
        const pattern = this.sensitivePatterns[type];
        if (!pattern) return value;
        return pattern.mask(value);
    }

    // ==================== 安全传输 ====================

    // 安全传输数据
    async secureTransfer(data, options = {}) {
        const transfer = {
            id: `transfer_${Date.now()}`,
            timestamp: Date.now(),
            encrypted: options.encrypt !== false,
            signed: options.sign !== false,
            compressed: options.compress || false,
            data: null,
            signature: null
        };

        try {
            // 压缩
            if (transfer.compressed) {
                data = await this.compress(JSON.stringify(data));
            }

            // 加密
            if (transfer.encrypted) {
                const encrypted = await this.encrypt(data);
                transfer.data = encrypted.data;
                transfer.iv = encrypted.iv;
                transfer.keyId = encrypted.keyId;
            } else {
                transfer.data = btoa(JSON.stringify(data));
            }

            // 签名
            if (transfer.signed) {
                transfer.signature = await this.sign(transfer.data);
            }

            this.logAudit('transfer', { id: transfer.id });
            return { success: true, transfer };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // 签名
    async sign(data) {
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(data);
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
        return this.bufferToBase64(hashBuffer);
    }

    // 压缩
    async compress(str) {
        const encoder = new TextEncoder();
        const data = encoder.encode(str);
        const compressed = await crypto.subtle.compress(
            { name: 'gzip' },
            data
        );
        return this.bufferToBase64(compressed);
    }

    // ==================== 访问控制 ====================

    // 检查访问权限
    checkAccess(userId, dataId, action) {
        const accessLevel = this.getUserAccessLevel(userId);
        const requiredLevel = this.getRequiredLevel(action);

        const granted = accessLevel >= requiredLevel;

        this.logAudit('access', {
            userId,
            dataId,
            action,
            granted,
            accessLevel,
            requiredLevel
        });

        return {
            granted,
            userId,
            dataId,
            action,
            reason: granted ? '权限足够' : '权限不足'
        };
    }

    // 获取用户访问级别
    getUserAccessLevel(userId) {
        // 模拟：实际应从数据库获取
        const levels = {
            admin: 100,
            manager: 75,
            user: 50,
            guest: 25
        };
        return levels[userId] || 25;
    }

    // 获取所需级别
    getRequiredLevel(action) {
        const levels = {
            read: 25,
            write: 50,
            delete: 75,
            decrypt: 75,
            export: 50
        };
        return levels[action] || 50;
    }

    // ==================== 审计追踪 ====================

    // 记录审计日志
    logAudit(action, details) {
        const log = {
            id: `audit_${Date.now()}`,
            action,
            details,
            timestamp: Date.now(),
            userAgent: navigator.userAgent
        };
        this.auditLog.push(log);
    }

    // 获取审计日志
    getAuditLog(filter = {}) {
        let logs = [...this.auditLog];

        if (filter.action) {
            logs = logs.filter(l => l.action === filter.action);
        }

        if (filter.from) {
            logs = logs.filter(l => l.timestamp >= filter.from);
        }

        if (filter.to) {
            logs = logs.filter(l => l.timestamp <= filter.to);
        }

        return logs;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            patternsCount: Object.keys(this.sensitivePatterns).length,
            auditLogCount: this.auditLog.length
        };
    }
}

// 创建全局实例
window.sensitiveDataManager = new SensitiveDataManager();

// 导出
window.MTSCOS_SensitiveDataManager = SensitiveDataManager;

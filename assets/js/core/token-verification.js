/**
 * 证书令牌验证和vikey验证机制 - MTSCOS AI Token Verification Module
 * 提供证书验证、令牌管理、vikey加密验证功能
 */

class TokenVerificationManager {
    constructor() {
        this.certificates = new Map();
        this.tokens = new Map();
        this.vikeys = new Map();
        this.verificationEnabled = true;
        this.tokenExpiryTime = 3600000; // 1小时
        this.refreshThreshold = 0.8; // 80%时间后刷新
        this.maxFailedAttempts = 3;
        this.lockoutDuration = 900000; // 15分钟
        this.failedAttempts = new Map();
        this.currentCertificate = null;
        this.currentToken = null;
        this.currentVikey = null;
        
        this.init();
    }

    init() {
        this.setupCertificateSystem();
        this.setupTokenSystem();
        this.setupVikeySystem();
        this.setupVerificationMonitoring();
        this.loadStoredCredentials();
        
        console.log('[令牌验证] 令牌验证管理器已初始化');
    }

    // 设置证书系统
    setupCertificateSystem() {
        // 生成根证书
        this.generateRootCertificate();
        
        // 设置证书验证
        this.setupCertificateValidation();
        
        // 设置证书更新
        this.setupCertificateRenewal();
    }

    // 设置令牌系统
    setupTokenSystem() {
        // 设置令牌生成
        this.setupTokenGeneration();
        
        // 设置令牌验证
        this.setupTokenValidation();
        
        // 设置令牌刷新
        this.setupTokenRefresh();
    }

    // 设置vikey系统
    setupVikeySystem() {
        // 生成vikey
        this.generateVikey();
        
        // 设置vikey验证
        this.setupVikeyValidation();
        
        // 设置vikey同步
        this.setupVikeySync();
    }

    // 设置验证监控
    setupVerificationMonitoring() {
        // 定期验证
        setInterval(() => {
            this.performPeriodicVerification();
        }, 60000); // 每分钟验证一次
        
        // 监控验证失败
        this.monitorVerificationFailures();
    }

    // 生成根证书
    generateRootCertificate() {
        const rootCert = {
            id: 'root_cert_' + Date.now(),
            type: 'root',
            version: '1.0',
            issuer: 'MTSCOS-AI-ROOT',
            subject: 'MTSCOS-AI-SYSTEM',
            serialNumber: this.generateSerialNumber(),
            notBefore: new Date().toISOString(),
            notAfter: new Date(Date.now() + 31536000000).toISOString(), // 1年
            publicKey: this.generatePublicKey(),
            signature: null,
            created: new Date().toISOString()
        };
        
        // 生成签名
        rootCert.signature = this.signCertificate(rootCert);
        
        this.certificates.set(rootCert.id, rootCert);
        this.currentCertificate = rootCert;
        
        console.log('[令牌验证] 根证书已生成:', rootCert.id);
    }

    // 生成用户证书
    generateUserCertificate(userId, permissions = []) {
        const userCert = {
            id: 'user_cert_' + userId + '_' + Date.now(),
            type: 'user',
            version: '1.0',
            issuer: this.currentCertificate.id,
            subject: userId,
            serialNumber: this.generateSerialNumber(),
            notBefore: new Date().toISOString(),
            notAfter: new Date(Date.now() + this.tokenExpiryTime).toISOString(),
            publicKey: this.generatePublicKey(),
            permissions: permissions,
            signature: null,
            created: new Date().toISOString()
        };
        
        // 生成签名
        userCert.signature = this.signCertificate(userCert);
        
        this.certificates.set(userCert.id, userCert);
        
        return userCert;
    }

    // 生成序列号
    generateSerialNumber() {
        return Date.now().toString(16) + Math.random().toString(16).substring(2);
    }

    // 生成公钥
    generatePublicKey() {
        const keyPair = this.generateKeyPair();
        return {
            kty: 'RSA',
            n: keyPair.publicKey.n,
            e: keyPair.publicKey.e,
            keyId: this.generateKeyId()
        };
    }

    // 生成密钥对
    generateKeyPair() {
        // 简化的密钥对生成（实际应用中应使用Web Crypto API）
        const privateKey = this.generateSecureRandom(64);
        const publicKey = {
            n: this.generateSecureRandom(32),
            e: '65537'
        };
        
        return {
            privateKey: privateKey,
            publicKey: publicKey
        };
    }

    // 生成密钥ID
    generateKeyId() {
        return 'key_' + Date.now() + '_' + this.generateSecureRandom(8);
    }

    // 签名证书
    signCertificate(certificate) {
        const certData = JSON.stringify({
            id: certificate.id,
            type: certificate.type,
            issuer: certificate.issuer,
            subject: certificate.subject,
            serialNumber: certificate.serialNumber,
            notBefore: certificate.notBefore,
            notAfter: certificate.notAfter,
            publicKey: certificate.publicKey
        });
        
        return this.generateSignature(certData);
    }

    // 生成签名
    generateSignature(data) {
        const privateKey = this.getPrivateKey();
        const hash = this.hashData(data);
        
        // 简化的签名算法
        let signature = '';
        for (let i = 0; i < hash.length; i++) {
            const charCode = hash.charCodeAt(i);
            const keyChar = privateKey.charCodeAt(i % privateKey.length);
            signature += String.fromCharCode(charCode ^ keyChar);
        }
        
        return btoa(signature);
    }

    // 验证证书
    verifyCertificate(certificate) {
        try {
            // 检查证书格式
            if (!certificate.id || !certificate.type || !certificate.signature) {
                return false;
            }
            
            // 检查证书有效期
            const now = new Date();
            const notBefore = new Date(certificate.notBefore);
            const notAfter = new Date(certificate.notAfter);
            
            if (now < notBefore || now > notAfter) {
                return false;
            }
            
            // 验证签名
            const certData = JSON.stringify({
                id: certificate.id,
                type: certificate.type,
                issuer: certificate.issuer,
                subject: certificate.subject,
                serialNumber: certificate.serialNumber,
                notBefore: certificate.notBefore,
                notAfter: certificate.notAfter,
                publicKey: certificate.publicKey
            });
            
            const expectedSignature = this.generateSignature(certData);
            return certificate.signature === expectedSignature;
            
        } catch (error) {
            console.error('[令牌验证] 证书验证失败:', error);
            return false;
        }
    }

    // 设置证书验证
    setupCertificateValidation() {
        // 定期验证当前证书
        setInterval(() => {
            if (this.currentCertificate) {
                if (!this.verifyCertificate(this.currentCertificate)) {
                    console.warn('[令牌验证] 当前证书验证失败');
                    this.handleCertificateInvalid();
                }
            }
        }, 300000); // 每5分钟验证一次
    }

    // 设置证书更新
    setupCertificateRenewal() {
        // 检查证书过期
        setInterval(() => {
            if (this.currentCertificate) {
                const notAfter = new Date(this.currentCertificate.notAfter);
                const now = new Date();
                const timeUntilExpiry = notAfter.getTime() - now.getTime();
                
                if (timeUntilExpiry < this.tokenExpiryTime * this.refreshThreshold) {
                    console.log('[令牌验证] 证书即将过期，开始更新');
                    this.renewCertificate();
                }
            }
        }, 60000); // 每分钟检查一次
    }

    // 更新证书
    renewCertificate() {
        if (this.currentCertificate) {
            const newCert = { ...this.currentCertificate };
            newCert.id = 'renewed_' + newCert.id;
            newCert.notBefore = new Date().toISOString();
            newCert.notAfter = new Date(Date.now() + this.tokenExpiryTime).toISOString();
            newCert.signature = null;
            
            newCert.signature = this.signCertificate(newCert);
            
            this.certificates.set(newCert.id, newCert);
            this.currentCertificate = newCert;
            
            console.log('[令牌验证] 证书已更新:', newCert.id);
        }
    }

    // 处理证书无效
    handleCertificateInvalid() {
        this.lockSystem('证书验证失败');
        this.triggerSecurityAlert('证书验证失败，系统已锁定');
    }

    // 设置令牌生成
    setupTokenGeneration() {
        // 生成访问令牌
        this.generateAccessToken();
    }

    // 生成访问令牌
    generateAccessToken(userId = 'system', permissions = ['read', 'write']) {
        const token = {
            id: 'token_' + Date.now() + '_' + this.generateSecureRandom(16),
            type: 'access',
            userId: userId,
            permissions: permissions,
            issuedAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + this.tokenExpiryTime).toISOString(),
            issuer: this.currentCertificate ? this.currentCertificate.id : 'system',
            audience: 'mtscos-ai',
            scope: permissions.join(' '),
            signature: null
        };
        
        // 生成签名
        token.signature = this.signToken(token);
        
        this.tokens.set(token.id, token);
        this.currentToken = token;
        
        console.log('[令牌验证] 访问令牌已生成:', token.id);
        return token;
    }

    // 签名令牌
    signToken(token) {
        const tokenData = JSON.stringify({
            id: token.id,
            type: token.type,
            userId: token.userId,
            permissions: token.permissions,
            issuedAt: token.issuedAt,
            expiresAt: token.expiresAt,
            issuer: token.issuer,
            audience: token.audience,
            scope: token.scope
        });
        
        return this.generateSignature(tokenData);
    }

    // 验证令牌
    verifyToken(token) {
        try {
            // 检查令牌格式
            if (!token.id || !token.type || !token.signature) {
                return false;
            }
            
            // 检查令牌有效期
            const now = new Date();
            const issuedAt = new Date(token.issuedAt);
            const expiresAt = new Date(token.expiresAt);
            
            if (now < issuedAt || now > expiresAt) {
                return false;
            }
            
            // 验证签名
            const tokenData = JSON.stringify({
                id: token.id,
                type: token.type,
                userId: token.userId,
                permissions: token.permissions,
                issuedAt: token.issuedAt,
                expiresAt: token.expiresAt,
                issuer: token.issuer,
                audience: token.audience,
                scope: token.scope
            });
            
            const expectedSignature = this.signToken(token);
            return token.signature === expectedSignature;
            
        } catch (error) {
            console.error('[令牌验证] 令牌验证失败:', error);
            return false;
        }
    }

    // 设置令牌验证
    setupTokenValidation() {
        // 定期验证当前令牌
        setInterval(() => {
            if (this.currentToken) {
                if (!this.verifyToken(this.currentToken)) {
                    console.warn('[令牌验证] 当前令牌验证失败');
                    this.handleTokenInvalid();
                }
            }
        }, 60000); // 每分钟验证一次
    }

    // 设置令牌刷新
    setupTokenRefresh() {
        // 检查令牌过期
        setInterval(() => {
            if (this.currentToken) {
                const expiresAt = new Date(this.currentToken.expiresAt);
                const now = new Date();
                const timeUntilExpiry = expiresAt.getTime() - now.getTime();
                
                if (timeUntilExpiry < this.tokenExpiryTime * this.refreshThreshold) {
                    console.log('[令牌验证] 令牌即将过期，开始刷新');
                    this.refreshToken();
                }
            }
        }, 30000); // 每30秒检查一次
    }

    // 刷新令牌
    refreshToken() {
        if (this.currentToken) {
            const newToken = this.generateAccessToken(
                this.currentToken.userId,
                this.currentToken.permissions
            );
            
            console.log('[令牌验证] 令牌已刷新:', newToken.id);
        }
    }

    // 处理令牌无效
    handleTokenInvalid() {
        this.lockSystem('令牌验证失败');
        this.triggerSecurityAlert('令牌验证失败，系统已锁定');
    }

    // 生成vikey
    generateVikey() {
        const vikey = {
            id: 'vikey_' + Date.now(),
            type: 'hardware',
            version: '1.0',
            serialNumber: this.generateSerialNumber(),
            secretKey: this.generateSecureRandom(128),
            publicKey: this.generateSecureRandom(64),
            challenge: this.generateSecureRandom(32),
            response: null,
            created: new Date().toISOString(),
            lastUsed: null,
            usageCount: 0
        };
        
        this.vikeys.set(vikey.id, vikey);
        this.currentVikey = vikey;
        
        console.log('[令牌验证] Vikey已生成:', vikey.id);
        return vikey;
    }

    // 设置vikey验证
    setupVikeyValidation() {
        // 定期验证vikey
        setInterval(() => {
            if (this.currentVikey) {
                this.verifyVikey(this.currentVikey);
            }
        }, 120000); // 每2分钟验证一次
    }

    // 验证vikey
    verifyVikey(vikey) {
        try {
            // 生成新的挑战
            const newChallenge = this.generateSecureRandom(32);
            
            // 计算预期响应
            const expectedResponse = this.calculateVikeyResponse(newChallenge, vikey.secretKey);
            
            // 模拟vikey响应
            const actualResponse = this.simulateVikeyResponse(newChallenge, vikey.secretKey);
            
            // 验证响应
            if (actualResponse === expectedResponse) {
                vikey.lastUsed = new Date().toISOString();
                vikey.usageCount++;
                vikey.challenge = newChallenge;
                vikey.response = actualResponse;
                
                console.log('[令牌验证] Vikey验证成功:', vikey.id);
                return true;
            } else {
                console.warn('[令牌验证] Vikey验证失败:', vikey.id);
                this.handleVikeyFailure(vikey);
                return false;
            }
        } catch (error) {
            console.error('[令牌验证] Vikey验证异常:', error);
            return false;
        }
    }

    // 计算vikey响应
    calculateVikeyResponse(challenge, secretKey) {
        const combined = challenge + secretKey + Date.now().toString();
        return this.hashData(combined);
    }

    // 模拟vikey响应
    simulateVikeyResponse(challenge, secretKey) {
        // 模拟硬件vikey的响应计算
        return this.calculateVikeyResponse(challenge, secretKey);
    }

    // 设置vikey同步
    setupVikeySync() {
        // 定期同步vikey状态
        setInterval(() => {
            this.syncVikeyStatus();
        }, 300000); // 每5分钟同步一次
    }

    // 同步vikey状态
    syncVikeyStatus() {
        if (this.currentVikey) {
            // 检查vikey使用频率
            const timeSinceLastUse = Date.now() - new Date(this.currentVikey.lastUsed).getTime();
            
            if (timeSinceLastUse > 600000) { // 10分钟未使用
                console.warn('[令牌验证] Vikey长时间未使用，可能存在风险');
                this.triggerSecurityAlert('Vikey长时间未使用，请检查设备状态');
            }
            
            // 检查vikey使用次数
            if (this.currentVikey.usageCount > 1000) {
                console.warn('[令牌验证] Vikey使用次数过多，可能存在异常');
                this.triggerSecurityAlert('Vikey使用次数异常，请检查设备状态');
            }
        }
    }

    // 处理vikey失败
    handleVikeyFailure(vikey) {
        const failures = this.failedAttempts.get(vikey.id) || 0;
        this.failedAttempts.set(vikey.id, failures + 1);
        
        if (failures + 1 >= this.maxFailedAttempts) {
            this.lockSystem('Vikey验证失败次数过多');
            this.triggerSecurityAlert('Vikey验证失败次数过多，系统已锁定');
        } else {
            this.triggerSecurityAlert(`Vikey验证失败 (${failures + 1}/${this.maxFailedAttempts})`);
        }
    }

    // 执行定期验证
    performPeriodicVerification() {
        if (!this.verificationEnabled) {
            return;
        }
        
        let verificationPassed = true;
        
        // 验证证书
        if (this.currentCertificate && !this.verifyCertificate(this.currentCertificate)) {
            verificationPassed = false;
        }
        
        // 验证令牌
        if (this.currentToken && !this.verifyToken(this.currentToken)) {
            verificationPassed = false;
        }
        
        // 验证vikey
        if (this.currentVikey && !this.verifyVikey(this.currentVikey)) {
            verificationPassed = false;
        }
        
        if (!verificationPassed) {
            console.warn('[令牌验证] 定期验证失败');
            this.handleVerificationFailure();
        }
    }

    // 监控验证失败
    monitorVerificationFailures() {
        // 监控失败次数
        setInterval(() => {
            const totalFailures = Array.from(this.failedAttempts.values())
                .reduce((sum, count) => sum + count, 0);
            
            if (totalFailures > 10) {
                console.warn('[令牌验证] 验证失败次数过多');
                this.lockSystem('验证失败次数过多');
                this.triggerSecurityAlert('验证失败次数过多，系统已锁定');
            }
        }, 60000); // 每分钟检查一次
    }

    // 处理验证失败
    handleVerificationFailure() {
        this.lockSystem('定期验证失败');
        this.triggerSecurityAlert('定期验证失败，系统已锁定');
    }

    // 加载存储的凭据
    loadStoredCredentials() {
        try {
            // 加载证书
            const storedCerts = localStorage.getItem('stored_certificates');
            if (storedCerts) {
                const certs = JSON.parse(storedCerts);
                certs.forEach(cert => {
                    this.certificates.set(cert.id, cert);
                });
            }
            
            // 加载令牌
            const storedTokens = localStorage.getItem('stored_tokens');
            if (storedTokens) {
                const tokens = JSON.parse(storedTokens);
                tokens.forEach(token => {
                    this.tokens.set(token.id, token);
                });
            }
            
            // 加载vikey
            const storedVikeys = localStorage.getItem('stored_vikeys');
            if (storedVikeys) {
                const vikeys = JSON.parse(storedVikeys);
                vikeys.forEach(vikey => {
                    this.vikeys.set(vikey.id, vikey);
                });
            }
            
            console.log('[令牌验证] 存储的凭据已加载');
        } catch (error) {
            console.error('[令牌验证] 加载存储凭据失败:', error);
        }
    }

    // 保存凭据
    saveCredentials() {
        try {
            // 保存证书
            const certs = Array.from(this.certificates.values());
            localStorage.setItem('stored_certificates', JSON.stringify(certs));
            
            // 保存令牌
            const tokens = Array.from(this.tokens.values());
            localStorage.setItem('stored_tokens', JSON.stringify(tokens));
            
            // 保存vikey
            const vikeys = Array.from(this.vikeys.values());
            localStorage.setItem('stored_vikeys', JSON.stringify(vikeys));
            
            console.log('[令牌验证] 凭据已保存');
        } catch (error) {
            console.error('[令牌验证] 保存凭据失败:', error);
        }
    }

    // 锁定系统
    lockSystem(reason) {
        this.verificationEnabled = false;
        
        // 重定向到锁定页面
        setTimeout(() => {
            window.location.href = '/HTML/locked.html';
        }, 1000);
        
        console.log(`[令牌验证] 系统已锁定: ${reason}`);
    }

    // 解锁系统
    unlockSystem() {
        this.verificationEnabled = true;
        this.failedAttempts.clear();
        
        console.log('[令牌验证] 系统已解锁');
    }

    // 触发安全警告
    triggerSecurityAlert(message) {
        console.warn(`[令牌验证] 安全警告: ${message}`);
        
        // 创建警告元素
        const alert = document.createElement('div');
        alert.textContent = message;
        alert.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #ff9800;
            color: white;
            padding: 15px;
            border-radius: 5px;
            z-index: 999999;
            font-family: Arial, sans-serif;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(alert);
        
        // 5秒后移除
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }

    // 生成安全随机数
    generateSecureRandom(length = 32) {
        const array = new Uint8Array(length);
        crypto.getRandomValues(array);
        return Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // 哈希数据
    hashData(data) {
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }

    // 获取私钥
    getPrivateKey() {
        return localStorage.getItem('verification_private_key') || 
               this.generateSecureRandom(64);
    }

    // 获取验证状态
    getVerificationStatus() {
        return {
            verificationEnabled: this.verificationEnabled,
            currentCertificate: this.currentCertificate ? this.currentCertificate.id : null,
            currentToken: this.currentToken ? this.currentToken.id : null,
            currentVikey: this.currentVikey ? this.currentVikey.id : null,
            certificatesCount: this.certificates.size,
            tokensCount: this.tokens.size,
            vikeysCount: this.vikeys.size,
            failedAttempts: Object.fromEntries(this.failedAttempts)
        };
    }

    // 验证用户权限
    verifyUserPermission(userId, requiredPermission) {
        if (!this.currentToken || this.currentToken.userId !== userId) {
            return false;
        }
        
        return this.currentToken.permissions.includes(requiredPermission);
    }

    // 刷新所有凭据
    refreshAllCredentials() {
        this.renewCertificate();
        this.refreshToken();
        
        // 重新生成vikey
        if (this.currentVikey) {
            this.generateVikey();
        }
        
        this.saveCredentials();
        
        console.log('[令牌验证] 所有凭据已刷新');
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TokenVerificationManager;
} else {
    window.TokenVerificationManager = TokenVerificationManager;
}
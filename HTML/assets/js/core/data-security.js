/**
 * 数据安全机制和数据锁机制 - MTSCOS AI Data Security Module
 * 提供数据保护、锁定、验证和恢复功能
 */

class DataSecurityManager {
    constructor() {
        this.isLocked = false;
        this.lockReason = null;
        this.lockTimestamp = null;
        this.dataIntegrityChecks = true;
        this.encryptionEnabled = true;
        this.backupEnabled = true;
        this.maxBackupCount = 10;
        this.sensitiveDataKeys = ['password', 'token', 'key', 'secret', 'auth'];
        this.protectedStorage = new Map();
        this.dataLocks = new Map();
        this.checksums = new Map();
        this.accessLog = [];
        
        this.init();
    }

    init() {
        this.setupDataProtection();
        this.setupStorageMonitoring();
        this.setupDataLocking();
        this.setupIntegrityChecks();
        this.setupBackupSystem();
        this.setupSecureStorage();
        
        console.log('[数据安全] 数据安全管理器已初始化');
    }

    // 设置数据保护
    setupDataProtection() {
        // 拦截localStorage操作
        const originalSetItem = localStorage.setItem.bind(localStorage);
        const originalGetItem = localStorage.getItem.bind(localStorage);
        const originalRemoveItem = localStorage.removeItem.bind(localStorage);
        const originalClear = localStorage.clear.bind(localStorage);

        localStorage.setItem = (key, value) => {
            if (this.isSensitiveData(key)) {
                return this.setSecureItem(key, value);
            }
            
            // 记录访问日志
            this.logAccess('localStorage.setItem', { key, timestamp: Date.now() });
            
            // 创建数据校验和
            if (this.dataIntegrityChecks) {
                this.createChecksum(key, value);
            }
            
            return originalSetItem(key, value);
        };

        localStorage.getItem = (key) => {
            const value = originalGetItem(key);
            
            // 记录访问日志
            this.logAccess('localStorage.getItem', { key, timestamp: Date.now() });
            
            // 验证数据完整性
            if (this.dataIntegrityChecks && value) {
                this.verifyChecksum(key, value);
            }
            
            return value;
        };

        localStorage.removeItem = (key) => {
            this.logAccess('localStorage.removeItem', { key, timestamp: Date.now() });
            this.removeChecksum(key);
            this.protectedStorage.delete(key);
            return originalRemoveItem(key);
        };

        localStorage.clear = () => {
            this.logAccess('localStorage.clear', { timestamp: Date.now() });
            this.checksums.clear();
            this.protectedStorage.clear();
            return originalClear();
        };

        // 拦截sessionStorage操作
        this.interceptSessionStorage();
    }

    // 拦截sessionStorage
    interceptSessionStorage() {
        const originalSetItem = sessionStorage.setItem.bind(sessionStorage);
        const originalGetItem = sessionStorage.getItem.bind(sessionStorage);

        sessionStorage.setItem = (key, value) => {
            if (this.isSensitiveData(key)) {
                return this.setSecureSessionItem(key, value);
            }
            
            this.logAccess('sessionStorage.setItem', { key, timestamp: Date.now() });
            return originalSetItem(key, value);
        };

        sessionStorage.getItem = (key) => {
            const value = originalGetItem(key);
            this.logAccess('sessionStorage.getItem', { key, timestamp: Date.now() });
            return value;
        };
    }

    // 设置存储监控
    setupStorageMonitoring() {
        // 监控存储变化
        window.addEventListener('storage', (e) => {
            this.logAccess('storage.change', {
                key: e.key,
                oldValue: e.oldValue,
                newValue: e.newValue,
                url: e.url,
                timestamp: Date.now()
            });

            // 检测异常变化
            if (this.detectAnomalousChange(e)) {
                this.handleAnomalousChange(e);
            }
        });

        // 定期检查存储完整性
        setInterval(() => {
            this.performStorageAudit();
        }, 60000); // 每分钟检查一次
    }

    // 设置数据锁定
    setupDataLocking() {
        // 自动锁定敏感数据
        this.lockSensitiveData();
        
        // 设置锁定过期检查
        setInterval(() => {
            this.checkLockExpiry();
        }, 30000); // 每30秒检查一次
    }

    // 设置完整性检查
    setupIntegrityChecks() {
        // 初始化数据校验和
        this.initializeChecksums();
        
        // 定期验证数据完整性
        setInterval(() => {
            this.verifyAllChecksums();
        }, 120000); // 每2分钟验证一次
    }

    // 设置备份系统
    setupBackupSystem() {
        // 创建定期备份
        setInterval(() => {
            if (this.backupEnabled) {
                this.createBackup();
            }
        }, 300000); // 每5分钟备份一次

        // 监听页面卸载事件创建备份
        window.addEventListener('beforeunload', () => {
            if (this.backupEnabled) {
                this.createBackup('unload');
            }
        });
    }

    // 设置安全存储
    setupSecureStorage() {
        // 初始化加密存储
        this.initializeSecureStorage();
        
        // 设置内存保护
        this.setupMemoryProtection();
    }

    // 检查是否为敏感数据
    isSensitiveData(key) {
        const lowerKey = key.toLowerCase();
        return this.sensitiveDataKeys.some(sensitive => 
            lowerKey.includes(sensitive.toLowerCase())
        );
    }

    // 设置安全项
    setSecureItem(key, value) {
        try {
            // 加密数据
            const encryptedValue = this.encryptionEnabled ? 
                this.encryptData(value) : value;
            
            // 存储到受保护的存储中
            this.protectedStorage.set(key, {
                value: encryptedValue,
                timestamp: Date.now(),
                encrypted: this.encryptionEnabled,
                accessCount: 0
            });
            
            // 存储到localStorage（加密后）
            localStorage.setItem(`secure_${key}`, encryptedValue);
            
            this.logAccess('secure.setItem', { key, encrypted: true, timestamp: Date.now() });
            
            return true;
        } catch (error) {
            console.error('[数据安全] 设置安全项失败:', error);
            return false;
        }
    }

    // 获取安全项
    getSecureItem(key) {
        try {
            // 从受保护的存储中获取
            const secureData = this.protectedStorage.get(key);
            if (secureData) {
                secureData.accessCount++;
                this.logAccess('secure.getItem', { key, fromCache: true, timestamp: Date.now() });
                
                // 解密数据
                if (secureData.encrypted) {
                    return this.decryptData(secureData.value);
                }
                return secureData.value;
            }
            
            // 从localStorage中获取
            const encryptedValue = localStorage.getItem(`secure_${key}`);
            if (encryptedValue) {
                const value = this.encryptionEnabled ? 
                    this.decryptData(encryptedValue) : encryptedValue;
                
                // 缓存到受保护的存储中
                this.protectedStorage.set(key, {
                    value: encryptedValue,
                    timestamp: Date.now(),
                    encrypted: this.encryptionEnabled,
                    accessCount: 1
                });
                
                this.logAccess('secure.getItem', { key, fromStorage: true, timestamp: Date.now() });
                return value;
            }
            
            return null;
        } catch (error) {
            console.error('[数据安全] 获取安全项失败:', error);
            return null;
        }
    }

    // 设置安全会话项
    setSecureSessionItem(key, value) {
        try {
            const encryptedValue = this.encryptionEnabled ? 
                this.encryptData(value) : value;
            
            sessionStorage.setItem(`secure_${key}`, encryptedValue);
            
            this.logAccess('secure.setSessionItem', { key, encrypted: true, timestamp: Date.now() });
            
            return true;
        } catch (error) {
            console.error('[数据安全] 设置安全会话项失败:', error);
            return false;
        }
    }

    // 获取安全会话项
    getSecureSessionItem(key) {
        try {
            const encryptedValue = sessionStorage.getItem(`secure_${key}`);
            if (encryptedValue) {
                const value = this.encryptionEnabled ? 
                    this.decryptData(encryptedValue) : encryptedValue;
                
                this.logAccess('secure.getSessionItem', { key, timestamp: Date.now() });
                return value;
            }
            return null;
        } catch (error) {
            console.error('[数据安全] 获取安全会话项失败:', error);
            return null;
        }
    }

    // 加密数据
    encryptData(data) {
        try {
            // 简单的加密实现（实际应用中应使用更强的加密算法）
            const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
            const key = this.getEncryptionKey();
            
            let encrypted = '';
            for (let i = 0; i < dataStr.length; i++) {
                const charCode = dataStr.charCodeAt(i);
                const keyChar = key.charCodeAt(i % key.length);
                encrypted += String.fromCharCode(charCode ^ keyChar);
            }
            
            return btoa(encrypted);
        } catch (error) {
            console.error('[数据安全] 数据加密失败:', error);
            return data;
        }
    }

    // 解密数据
    decryptData(encryptedData) {
        try {
            const key = this.getEncryptionKey();
            const encrypted = atob(encryptedData);
            
            let decrypted = '';
            for (let i = 0; i < encrypted.length; i++) {
                const charCode = encrypted.charCodeAt(i);
                const keyChar = key.charCodeAt(i % key.length);
                decrypted += String.fromCharCode(charCode ^ keyChar);
            }
            
            // 尝试解析为JSON
            try {
                return JSON.parse(decrypted);
            } catch {
                return decrypted;
            }
        } catch (error) {
            console.error('[数据安全] 数据解密失败:', error);
            return encryptedData;
        }
    }

    // 获取加密密钥
    getEncryptionKey() {
        const storedKey = localStorage.getItem('data_encryption_key');
        if (storedKey) {
            return storedKey;
        }
        
        // 生成新的密钥
        const newKey = this.generateEncryptionKey();
        localStorage.setItem('data_encryption_key', newKey);
        return newKey;
    }

    // 生成加密密钥
    generateEncryptionKey() {
        const timestamp = Date.now().toString();
        const random = Math.random().toString(36).substring(2);
        const fingerprint = this.generateDeviceFingerprint();
        
        return this.simpleHash(timestamp + random + fingerprint).substring(0, 32);
    }

    // 生成设备指纹
    generateDeviceFingerprint() {
        return [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset()
        ].join('|');
    }

    // 简单哈希
    simpleHash(data) {
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }

    // 创建校验和
    createChecksum(key, value) {
        const checksum = this.simpleHash(value + key + Date.now());
        this.checksums.set(key, {
            checksum: checksum,
            timestamp: Date.now(),
            value: value
        });
    }

    // 验证校验和
    verifyChecksum(key, value) {
        const storedChecksum = this.checksums.get(key);
        if (!storedChecksum) {
            return true; // 没有校验和，跳过验证
        }
        
        const currentChecksum = this.simpleHash(value + key + storedChecksum.timestamp);
        if (currentChecksum !== storedChecksum.checksum) {
            console.warn(`[数据安全] 检测到数据篡改: ${key}`);
            this.handleDataTampering(key, value, storedChecksum);
            return false;
        }
        
        return true;
    }

    // 移除校验和
    removeChecksum(key) {
        this.checksums.delete(key);
    }

    // 初始化校验和
    initializeChecksums() {
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            const value = localStorage.getItem(key);
            if (value) {
                this.createChecksum(key, value);
            }
        }
    }

    // 验证所有校验和
    verifyAllChecksums() {
        let tamperedCount = 0;
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            const value = localStorage.getItem(key);
            
            if (value && !this.verifyChecksum(key, value)) {
                tamperedCount++;
            }
        }
        
        if (tamperedCount > 0) {
            console.warn(`[数据安全] 检测到 ${tamperedCount} 个被篡改的数据项`);
        }
    }

    // 处理数据篡改
    handleDataTampering(key, currentValue, storedChecksum) {
        this.logAccess('data.tampering', {
            key: key,
            currentValue: currentValue,
            originalValue: storedChecksum.value,
            timestamp: Date.now()
        });
        
        // 恢复原始值
        localStorage.setItem(key, storedChecksum.value);
        
        // 触发安全警告
        this.triggerSecurityAlert(`检测到数据篡改: ${key}`);
    }

    // 锁定敏感数据
    lockSensitiveData() {
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (this.isSensitiveData(key)) {
                this.lockData(key, '自动锁定敏感数据');
            }
        }
    }

    // 锁定数据
    lockData(key, reason = '手动锁定') {
        const lockInfo = {
            reason: reason,
            timestamp: Date.now(),
            duration: 300000, // 5分钟
            locked: true
        };
        
        this.dataLocks.set(key, lockInfo);
        this.logAccess('data.lock', { key: key, reason: reason, timestamp: Date.now() });
    }

    // 解锁数据
    unlockData(key) {
        const lockInfo = this.dataLocks.get(key);
        if (lockInfo) {
            this.dataLocks.delete(key);
            this.logAccess('data.unlock', { key: key, timestamp: Date.now() });
            return true;
        }
        return false;
    }

    // 检查锁定过期
    checkLockExpiry() {
        const now = Date.now();
        
        this.dataLocks.forEach((lockInfo, key) => {
            if (now - lockInfo.timestamp > lockInfo.duration) {
                this.dataLocks.delete(key);
                this.logAccess('data.lockExpired', { key: key, timestamp: now });
            }
        });
    }

    // 检测异常变化
    detectAnomalousChange(event) {
        // 检测快速连续的变化
        const recentChanges = this.accessLog.filter(log => 
            log.action === 'storage.change' && 
            log.key === event.key &&
            (Date.now() - log.timestamp) < 1000
        );
        
        if (recentChanges.length > 5) {
            return true;
        }
        
        // 检测值的异常变化
        if (event.oldValue && event.newValue) {
            const oldLength = event.oldValue.length;
            const newLength = event.newValue.length;
            
            // 检测长度的异常变化
            if (Math.abs(oldLength - newLength) > oldLength * 0.5) {
                return true;
            }
        }
        
        return false;
    }

    // 处理异常变化
    handleAnomalousChange(event) {
        this.logAccess('data.anomalousChange', {
            key: event.key,
            oldValue: event.oldValue,
            newValue: event.newValue,
            timestamp: Date.now()
        });
        
        // 锁定相关数据
        this.lockData(event.key, '检测到异常变化');
        
        // 触发安全警告
        this.triggerSecurityAlert(`检测到异常数据变化: ${event.key}`);
    }

    // 执行存储审计
    performStorageAudit() {
        const audit = {
            timestamp: Date.now(),
            localStorageItems: localStorage.length,
            sessionStorageItems: sessionStorage.length,
            protectedItems: this.protectedStorage.size,
            lockedItems: this.dataLocks.size,
            checksums: this.checksums.size
        };
        
        this.logAccess('storage.audit', audit);
        
        // 检测异常
        if (audit.localStorageItems > 1000) {
            this.triggerSecurityAlert('localStorage项目数量异常');
        }
    }

    // 创建备份
    createBackup(reason = 'scheduled') {
        try {
            const backup = {
                timestamp: Date.now(),
                reason: reason,
                localStorage: {},
                sessionStorage: {},
                checksums: Array.from(this.checksums.entries()),
                locks: Array.from(this.dataLocks.entries())
            };
            
            // 备份localStorage
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                backup.localStorage[key] = localStorage.getItem(key);
            }
            
            // 备份sessionStorage
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                backup.sessionStorage[key] = sessionStorage.getItem(key);
            }
            
            // 存储备份
            const backupKey = `backup_${Date.now()}`;
            localStorage.setItem(backupKey, JSON.stringify(backup));
            
            // 清理旧备份
            this.cleanupOldBackups();
            
            this.logAccess('backup.created', { 
                reason: reason, 
                backupKey: backupKey, 
                timestamp: Date.now() 
            });
            
            console.log(`[数据安全] 备份已创建: ${backupKey}`);
        } catch (error) {
            console.error('[数据安全] 创建备份失败:', error);
        }
    }

    // 清理旧备份
    cleanupOldBackups() {
        const backupKeys = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('backup_')) {
                backupKeys.push(key);
            }
        }
        
        // 按时间排序
        backupKeys.sort();
        
        // 删除多余的备份
        while (backupKeys.length > this.maxBackupCount) {
            const oldBackup = backupKeys.shift();
            localStorage.removeItem(oldBackup);
        }
    }

    // 恢复备份
    restoreBackup(backupKey) {
        try {
            const backupData = localStorage.getItem(backupKey);
            if (!backupData) {
                throw new Error('备份不存在');
            }
            
            const backup = JSON.parse(backupData);
            
            // 清空当前存储
            localStorage.clear();
            sessionStorage.clear();
            
            // 恢复localStorage
            Object.entries(backup.localStorage).forEach(([key, value]) => {
                localStorage.setItem(key, value);
            });
            
            // 恢复sessionStorage
            Object.entries(backup.sessionStorage).forEach(([key, value]) => {
                sessionStorage.setItem(key, value);
            });
            
            // 恢复校验和
            this.checksums = new Map(backup.checksums);
            
            // 恢复锁
            this.dataLocks = new Map(backup.locks);
            
            this.logAccess('backup.restored', { 
                backupKey: backupKey, 
                timestamp: Date.now() 
            });
            
            console.log(`[数据安全] 备份已恢复: ${backupKey}`);
            return true;
        } catch (error) {
            console.error('[数据安全] 恢复备份失败:', error);
            return false;
        }
    }

    // 初始化安全存储
    initializeSecureStorage() {
        // 恢复受保护的存储
        try {
            const protectedData = localStorage.getItem('protected_storage');
            if (protectedData) {
                const data = JSON.parse(protectedData);
                this.protectedStorage = new Map(data);
            }
        } catch (error) {
            console.error('[数据安全] 初始化安全存储失败:', error);
        }
    }

    // 设置内存保护
    setupMemoryProtection() {
        // 定期清理敏感数据
        setInterval(() => {
            this.cleanupSensitiveMemory();
        }, 60000);
        
        // 监听页面卸载
        window.addEventListener('beforeunload', () => {
            this.clearSensitiveMemory();
        });
    }

    // 清理敏感内存
    cleanupSensitiveMemory() {
        this.protectedStorage.forEach((data, key) => {
            // 清理长时间未访问的数据
            if (Date.now() - data.timestamp > 3600000) { // 1小时
                this.protectedStorage.delete(key);
            }
        });
    }

    // 清除敏感内存
    clearSensitiveMemory() {
        this.protectedStorage.clear();
        this.accessLog = [];
    }

    // 记录访问日志
    logAccess(action, data) {
        const log = {
            action: action,
            data: data,
            timestamp: Date.now()
        };
        
        this.accessLog.push(log);
        
        // 限制日志大小
        if (this.accessLog.length > 1000) {
            this.accessLog.shift();
        }
    }

    // 触发安全警告
    triggerSecurityAlert(message) {
        console.warn(`[数据安全] 安全警告: ${message}`);
        
        // 创建警告元素
        const alert = document.createElement('div');
        alert.textContent = message;
        alert.style.cssText = `
            position: fixed;
            top: 50px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            padding: 15px;
            border-radius: 5px;
            z-index: 999999;
            font-family: Arial, sans-serif;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(alert);
        
        // 3秒后移除
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 3000);
    }

    // 锁定所有数据
    lockAllData(reason = '安全锁定') {
        this.isLocked = true;
        this.lockReason = reason;
        this.lockTimestamp = Date.now();
        
        // 锁定所有localStorage项目
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            this.lockData(key, reason);
        }
        
        this.logAccess('data.lockAll', { reason: reason, timestamp: Date.now() });
        console.log(`[数据安全] 所有数据已锁定: ${reason}`);
    }

    // 解锁所有数据
    unlockAllData() {
        this.isLocked = false;
        this.lockReason = null;
        this.lockTimestamp = null;
        
        this.dataLocks.clear();
        
        this.logAccess('data.unlockAll', { timestamp: Date.now() });
        console.log('[数据安全] 所有数据已解锁');
    }

    // 获取安全状态
    getSecurityStatus() {
        return {
            isLocked: this.isLocked,
            lockReason: this.lockReason,
            lockTimestamp: this.lockTimestamp,
            protectedItems: this.protectedStorage.size,
            lockedItems: this.dataLocks.size,
            checksums: this.checksums.size,
            encryptionEnabled: this.encryptionEnabled,
            backupEnabled: this.backupEnabled,
            dataIntegrityChecks: this.dataIntegrityChecks
        };
    }

    // 获取访问日志
    getAccessLog(limit = 100) {
        return this.accessLog.slice(-limit);
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataSecurityManager;
} else {
    window.DataSecurityManager = DataSecurityManager;
}
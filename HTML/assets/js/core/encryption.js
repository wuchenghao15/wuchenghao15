/**
 * 信息加密机制 - MTSCOS AI Security Module
 * 提供数据加密、解密、哈希和数字签名功能
 */

class EncryptionManager {
    constructor() {
        this.algorithm = 'AES-GCM';
        this.keyLength = 256;
        this.ivLength = 12;
        this.saltLength = 16;
        this.tagLength = 16;
        this.masterKey = null;
        this.keyDerivationInfo = 'MTSCOS-AI-SECURITY-2024';
        
        this.init();
    }

    async init() {
        await this.generateMasterKey();
        console.log('[加密管理] 加密管理器已初始化');
    }

    // 生成主密钥
    async generateMasterKey() {
        try {
            // 尝试从安全存储中恢复密钥
            const storedKey = localStorage.getItem('master_key');
            if (storedKey) {
                this.masterKey = await this.importKey(storedKey);
                console.log('[加密管理] 从存储中恢复主密钥');
                return;
            }

            // 生成新的主密钥
            this.masterKey = await crypto.subtle.generateKey(
                {
                    name: this.algorithm,
                    length: this.keyLength
                },
                true,
                ['encrypt', 'decrypt']
            );

            // 导出并存储密钥
            const exportedKey = await crypto.subtle.exportKey('raw', this.masterKey);
            const keyArray = Array.from(new Uint8Array(exportedKey));
            localStorage.setItem('master_key', JSON.stringify(keyArray));
            
            console.log('[加密管理] 新的主密钥已生成并存储');
        } catch (error) {
            console.error('[加密管理] 生成主密钥失败:', error);
            // 降级到简单密钥
            this.masterKey = this.generateFallbackKey();
        }
    }

    // 生成降级密钥
    generateFallbackKey() {
        const timestamp = Date.now().toString();
        const random = Math.random().toString(36).substring(2);
        const fingerprint = this.generateDeviceFingerprint();
        
        const keyMaterial = timestamp + random + fingerprint;
        const hash = this.simpleHash(keyMaterial);
        
        return {
            type: 'fallback',
            key: hash.substring(0, 64),
            encrypt: (data) => this.fallbackEncrypt(data),
            decrypt: (encryptedData) => this.fallbackDecrypt(encryptedData)
        };
    }

    // 导入密钥
    async importKey(keyData) {
        try {
            const keyArray = typeof keyData === 'string' ? 
                JSON.parse(keyData) : keyData;
            
            const keyBuffer = new Uint8Array(keyArray);
            
            return await crypto.subtle.importKey(
                'raw',
                keyBuffer,
                this.algorithm,
                true,
                ['encrypt', 'decrypt']
            );
        } catch (error) {
            console.error('[加密管理] 导入密钥失败:', error);
            return this.generateFallbackKey();
        }
    }

    // 加密数据
    async encrypt(data, password = null) {
        try {
            const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(dataStr);

            if (this.masterKey.type === 'fallback') {
                return this.masterKey.encrypt(dataStr);
            }

            // 生成随机IV
            const iv = crypto.getRandomValues(new Uint8Array(this.ivLength));
            
            // 生成盐值
            const salt = crypto.getRandomValues(new Uint8Array(this.saltLength));

            // 如果提供了密码，派生密钥
            let key = this.masterKey;
            if (password) {
                key = await this.deriveKey(password, salt);
            }

            // 加密数据
            const encryptedBuffer = await crypto.subtle.encrypt(
                {
                    name: this.algorithm,
                    iv: iv,
                    tagLength: this.tagLength
                },
                key,
                dataBuffer
            );

            // 组合IV、盐值和加密数据
            const combined = new Uint8Array(
                salt.length + iv.length + encryptedBuffer.byteLength
            );
            combined.set(salt, 0);
            combined.set(iv, salt.length);
            combined.set(new Uint8Array(encryptedBuffer), salt.length + iv.length);

            // 转换为Base64
            return this.arrayBufferToBase64(combined);
        } catch (error) {
            console.error('[加密管理] 加密失败:', error);
            return this.fallbackEncrypt(dataStr);
        }
    }

    // 解密数据
    async decrypt(encryptedData, password = null) {
        try {
            if (this.masterKey.type === 'fallback') {
                return this.masterKey.decrypt(encryptedData);
            }

            // 从Base64解码
            const combined = this.base64ToArrayBuffer(encryptedData);
            const dataArray = new Uint8Array(combined);

            // 提取盐值、IV和加密数据
            const salt = dataArray.slice(0, this.saltLength);
            const iv = dataArray.slice(this.saltLength, this.saltLength + this.ivLength);
            const encrypted = dataArray.slice(this.saltLength + this.ivLength);

            // 如果提供了密码，派生密钥
            let key = this.masterKey;
            if (password) {
                key = await this.deriveKey(password, salt);
            }

            // 解密数据
            const decryptedBuffer = await crypto.subtle.decrypt(
                {
                    name: this.algorithm,
                    iv: iv,
                    tagLength: this.tagLength
                },
                key,
                encrypted
            );

            const decoder = new TextDecoder();
            const decryptedStr = decoder.decode(decryptedBuffer);

            // 尝试解析为JSON，失败则返回原始字符串
            try {
                return JSON.parse(decryptedStr);
            } catch {
                return decryptedStr;
            }
        } catch (error) {
            console.error('[加密管理] 解密失败:', error);
            return this.fallbackDecrypt(encryptedData);
        }
    }

    // 派生密钥
    async deriveKey(password, salt) {
        try {
            const encoder = new TextEncoder();
            const keyMaterial = await crypto.subtle.importKey(
                'raw',
                encoder.encode(password),
                'PBKDF2',
                false,
                ['deriveBits', 'deriveKey']
            );

            return await crypto.subtle.deriveKey(
                {
                    name: 'PBKDF2',
                    salt: salt,
                    iterations: 100000,
                    hash: 'SHA-256'
                },
                keyMaterial,
                {
                    name: this.algorithm,
                    length: this.keyLength
                },
                true,
                ['encrypt', 'decrypt']
            );
        } catch (error) {
            console.error('[加密管理] 密钥派生失败:', error);
            return this.masterKey;
        }
    }

    // 生成哈希
    async hash(data, algorithm = 'SHA-256') {
        try {
            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(data);
            
            const hashBuffer = await crypto.subtle.digest(algorithm, dataBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        } catch (error) {
            console.error('[加密管理] 哈希生成失败:', error);
            return this.simpleHash(data);
        }
    }

    // 生成HMAC
    async hmac(data, key, algorithm = 'SHA-256') {
        try {
            const encoder = new TextEncoder();
            const keyBuffer = encoder.encode(key);
            const dataBuffer = encoder.encode(data);

            const cryptoKey = await crypto.subtle.importKey(
                'raw',
                keyBuffer,
                {
                    name: 'HMAC',
                    hash: algorithm
                },
                false,
                ['sign']
            );

            const signature = await crypto.subtle.sign('HMAC', cryptoKey, dataBuffer);
            const signatureArray = Array.from(new Uint8Array(signature));
            
            return signatureArray.map(b => b.toString(16).padStart(2, '0')).join('');
        } catch (error) {
            console.error('[加密管理] HMAC生成失败:', error);
            return this.simpleHmac(data, key);
        }
    }

    // 生成数字签名
    async sign(data, privateKey = null) {
        try {
            const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(dataStr);

            // 如果没有提供私钥，使用主密钥
            if (!privateKey) {
                const hash = await this.hash(dataStr);
                return await this.hmac(hash, this.masterKey.key || 'default-key');
            }

            const signature = await crypto.subtle.sign(
                {
                    name: 'ECDSA',
                    hash: 'SHA-256'
                },
                privateKey,
                dataBuffer
            );

            return this.arrayBufferToBase64(signature);
        } catch (error) {
            console.error('[加密管理] 签名生成失败:', error);
            return this.simpleHash(dataStr + 'signature');
        }
    }

    // 验证数字签名
    async verify(data, signature, publicKey = null) {
        try {
            const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
            
            // 如果没有提供公钥，使用HMAC验证
            if (!publicKey) {
                const hash = await this.hash(dataStr);
                const expectedSignature = await this.hmac(hash, this.masterKey.key || 'default-key');
                return signature === expectedSignature;
            }

            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(dataStr);
            const signatureBuffer = this.base64ToArrayBuffer(signature);

            return await crypto.subtle.verify(
                {
                    name: 'ECDSA',
                    hash: 'SHA-256'
                },
                publicKey,
                signatureBuffer,
                dataBuffer
            );
        } catch (error) {
            console.error('[加密管理] 签名验证失败:', error);
            return false;
        }
    }

    // 生成安全随机数
    generateSecureRandom(length = 32) {
        try {
            const array = new Uint8Array(length);
            crypto.getRandomValues(array);
            return Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('');
        } catch (error) {
            console.error('[加密管理] 安全随机数生成失败:', error);
            return this.generateFallbackRandom(length);
        }
    }

    // 生成密钥对
    async generateKeyPair() {
        try {
            const keyPair = await crypto.subtle.generateKey(
                {
                    name: 'ECDSA',
                    namedCurve: 'P-256'
                },
                true,
                ['sign', 'verify']
            );

            const publicKey = await crypto.subtle.exportKey('spki', keyPair.publicKey);
            const privateKey = await crypto.subtle.exportKey('pkcs8', keyPair.privateKey);

            return {
                publicKey: this.arrayBufferToBase64(publicKey),
                privateKey: this.arrayBufferToBase64(privateKey),
                keyPair: keyPair
            };
        } catch (error) {
            console.error('[加密管理] 密钥对生成失败:', error);
            return this.generateFallbackKeyPair();
        }
    }

    // 降级加密方法
    fallbackEncrypt(data) {
        const key = this.masterKey.key;
        let encrypted = '';
        
        for (let i = 0; i < data.length; i++) {
            const charCode = data.charCodeAt(i);
            const keyChar = key.charCodeAt(i % key.length);
            encrypted += String.fromCharCode(charCode ^ keyChar);
        }
        
        return btoa(encrypted);
    }

    // 降级解密方法
    fallbackDecrypt(encryptedData) {
        try {
            const key = this.masterKey.key;
            const encrypted = atob(encryptedData);
            let decrypted = '';
            
            for (let i = 0; i < encrypted.length; i++) {
                const charCode = encrypted.charCodeAt(i);
                const keyChar = key.charCodeAt(i % key.length);
                decrypted += String.fromCharCode(charCode ^ keyChar);
            }
            
            return decrypted;
        } catch (error) {
            console.error('[加密管理] 降级解密失败:', error);
            return null;
        }
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

    // 简单HMAC
    simpleHmac(data, key) {
        return this.simpleHash(data + key + 'hmac');
    }

    // 生成降级随机数
    generateFallbackRandom(length) {
        let result = '';
        const characters = '0123456789abcdef';
        for (let i = 0; i < length * 2; i++) {
            result += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        return result;
    }

    // 生成降级密钥对
    generateFallbackKeyPair() {
        const privateKey = this.generateSecureRandom(32);
        const publicKey = this.simpleHash(privateKey + 'public');
        
        return {
            publicKey: publicKey,
            privateKey: privateKey,
            keyPair: null
        };
    }

    // 生成设备指纹
    generateDeviceFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint for MTSCOS AI', 2, 2);
        
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            screen.colorDepth,
            new Date().getTimezoneOffset(),
            canvas.toDataURL(),
            navigator.hardwareConcurrency || 'unknown',
            navigator.deviceMemory || 'unknown'
        ].join('|');
        
        return this.simpleHash(fingerprint);
    }

    // ArrayBuffer转Base64
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    // Base64转ArrayBuffer
    base64ToArrayBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    // 安全比较两个字符串
    secureCompare(a, b) {
        if (a.length !== b.length) {
            return false;
        }
        
        let result = 0;
        for (let i = 0; i < a.length; i++) {
            result |= a.charCodeAt(i) ^ b.charCodeAt(i);
        }
        
        return result === 0;
    }

    // 清除敏感数据
    clearSensitiveData() {
        if (this.masterKey && this.masterKey.type !== 'fallback') {
            try {
                crypto.subtle.deleteKey(this.masterKey);
            } catch (error) {
                console.error('[加密管理] 清除密钥失败:', error);
            }
        }
        
        localStorage.removeItem('master_key');
        this.masterKey = null;
        
        console.log('[加密管理] 敏感数据已清除');
    }

    // 获取加密状态
    getEncryptionStatus() {
        return {
            algorithm: this.algorithm,
            keyLength: this.keyLength,
            hasMasterKey: !!this.masterKey,
            keyType: this.masterKey ? this.masterKey.type : 'none',
            isSecure: this.masterKey && this.masterKey.type !== 'fallback'
        };
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EncryptionManager;
} else {
    window.EncryptionManager = EncryptionManager;
}
/**
 * MTSCOS AI System - 数据库加密管理器
 * 版本: 1.0.0
 * 描述: 提供AES-256-GCM加密、SHA-256哈希、安全密钥管理
 */

class DatabaseEncryption {
    constructor(options = {}) {
        this.algorithm = options.algorithm || 'AES-GCM';
        this.keyLength = options.keyLength || 256;
        this.ivLength = options.ivLength || 12;
        this.saltLength = options.saltLength || 16;
        this.iterations = options.iterations || 100000;
        this.encryptedCollections = new Set();
        this.keyCache = new Map();
        this.init();
    }
    
    async init() {
        console.log('🔐 数据库加密管理器初始化中...');
        // 生成主密钥
        await this.generateMasterKey();
        console.log('✅ 数据库加密管理器就绪');
    }
    
    /**
     * 生成主密钥
     */
    async generateMasterKey() {
        try {
            // 使用Web Crypto API生成随机密钥
            this.masterKey = await crypto.subtle.generateKey(
                {
                    name: this.algorithm,
                    length: this.keyLength
                },
                true,
                ['encrypt', 'decrypt']
            );
            console.log('🔑 主密钥生成成功');
        } catch (error) {
            console.error('❌ 主密钥生成失败:', error);
            throw error;
        }
    }
    
    /**
     * 从密码派生密钥
     */
    async deriveKeyFromPassword(password, salt = null) {
        const encoder = new TextEncoder();
        
        if (!salt) {
            salt = crypto.getRandomValues(new Uint8Array(this.saltLength));
        } else if (typeof salt === 'string') {
            salt = this.base64ToBuffer(salt);
        }
        
        // 导入密码
        const baseKey = await crypto.subtle.importKey(
            'raw',
            encoder.encode(password),
            { name: 'PBKDF2' },
            false,
            ['deriveKey']
        );
        
        // 派生密钥
        const derivedKey = await crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: salt,
                iterations: this.iterations,
                hash: 'SHA-256'
            },
            baseKey,
            {
                name: this.algorithm,
                length: this.keyLength
            },
            true,
            ['encrypt', 'decrypt']
        );
        
        return { key: derivedKey, salt };
    }
    
    /**
     * 加密数据
     */
    async encrypt(data, key = null) {
        try {
            const useKey = key || this.masterKey;
            const encoder = new TextEncoder();
            
            // 序列化数据
            const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
            const dataBuffer = encoder.encode(dataStr);
            
            // 生成IV
            const iv = crypto.getRandomValues(new Uint8Array(this.ivLength));
            
            // 加密
            const encryptedBuffer = await crypto.subtle.encrypt(
                {
                    name: this.algorithm,
                    iv: iv
                },
                useKey,
                dataBuffer
            );
            
            // 组合 IV + 密文
            const result = new Uint8Array(iv.length + encryptedBuffer.byteLength);
            result.set(iv, 0);
            result.set(new Uint8Array(encryptedBuffer), iv.length);
            
            return this.bufferToBase64(result);
        } catch (error) {
            console.error('❌ 加密失败:', error);
            throw error;
        }
    }
    
    /**
     * 解密数据
     */
    async decrypt(encryptedData, key = null) {
        try {
            const useKey = key || this.masterKey;
            
            // 解析 Base64
            const buffer = this.base64ToBuffer(encryptedData);
            
            // 提取 IV
            const iv = buffer.slice(0, this.ivLength);
            const data = buffer.slice(this.ivLength);
            
            // 解密
            const decryptedBuffer = await crypto.subtle.decrypt(
                {
                    name: this.algorithm,
                    iv: iv
                },
                useKey,
                data
            );
            
            const decoder = new TextDecoder();
            const dataStr = decoder.decode(decryptedBuffer);
            
            // 尝试解析JSON
            try {
                return JSON.parse(dataStr);
            } catch {
                return dataStr;
            }
        } catch (error) {
            console.error('❌ 解密失败:', error);
            throw error;
        }
    }
    
    /**
     * SHA-256哈希
     */
    async hash(data) {
        const encoder = new TextEncoder();
        const dataBuffer = typeof data === 'string' 
            ? encoder.encode(data) 
            : data;
        
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
        return this.bufferToHex(hashBuffer);
    }
    
    /**
     * HMAC签名
     */
    async sign(data, key = null) {
        const useKey = key || this.masterKey;
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(typeof data === 'string' ? data : JSON.stringify(data));
        
        // 创建HMAC密钥
        const hmacKey = await crypto.subtle.importKey(
            'raw',
            await crypto.subtle.exportKey('raw', useKey),
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        
        const signature = await crypto.subtle.sign('HMAC', hmacKey, dataBuffer);
        return this.bufferToBase64(signature);
    }
    
    /**
     * 验证签名
     */
    async verify(data, signature, key = null) {
        const computedSignature = await this.sign(data, key);
        return computedSignature === signature;
    }
    
    /**
     * 加密数据库记录
     */
    async encryptRecord(record) {
        return {
            ...record,
            _encrypted: true,
            _algorithm: this.algorithm,
            _data: await this.encrypt(record),
            _hash: await this.hash(JSON.stringify(record)),
            _timestamp: Date.now()
        };
    }
    
    /**
     * 解密数据库记录
     */
    async decryptRecord(encryptedRecord) {
        if (!encryptedRecord._encrypted) {
            return encryptedRecord;
        }
        
        const decrypted = await this.decrypt(encryptedRecord._data);
        return {
            ...decrypted,
            _hash: encryptedRecord._hash,
            _timestamp: encryptedRecord._timestamp
        };
    }
    
    /**
     * 注册加密集合
     */
    registerEncryptedCollection(name) {
        this.encryptedCollections.add(name);
        console.log(`🔒 集合已注册为加密: ${name}`);
    }
    
    /**
     * 加密存储到数据库
     */
    async encryptedAdd(database, collectionName, record) {
        if (this.encryptedCollections.has(collectionName)) {
            const encrypted = await this.encryptRecord(record);
            return database.add(collectionName, encrypted);
        }
        return database.add(collectionName, record);
    }
    
    /**
     * 从数据库读取并解密
     */
    async encryptedGet(database, collectionName, key) {
        const record = await database.get(collectionName, key);
        if (record && record._encrypted) {
            return await this.decryptRecord(record);
        }
        return record;
    }
    
    /**
     * 获取所有解密后的记录
     */
    async encryptedGetAll(database, collectionName) {
        const records = await database.getAll(collectionName);
        if (this.encryptedCollections.has(collectionName)) {
            return Promise.all(records.map(r => this.decryptRecord(r)));
        }
        return records;
    }
    
    /**
     * 加密导出所有数据
     */
    async exportEncrypted(data, password) {
        const { key, salt } = await this.deriveKeyFromPassword(password);
        const encrypted = await this.encrypt(data, key);
        return {
            encrypted: true,
            algorithm: this.algorithm,
            salt: this.bufferToBase64(salt),
            iterations: this.iterations,
            data: encrypted,
            timestamp: Date.now()
        };
    }
    
    /**
     * 解密导入数据
     */
    async importEncrypted(exportedData, password) {
        if (!exportedData.encrypted) {
            return exportedData;
        }
        
        const salt = this.base64ToBuffer(exportedData.salt);
        const { key } = await this.deriveKeyFromPassword(password, salt);
        return await this.decrypt(exportedData.data, key);
    }
    
    /**
     * 健康检查
     */
    healthCheck() {
        return {
            status: this.masterKey ? 'healthy' : 'error',
            algorithm: this.algorithm,
            keyLength: this.keyLength,
            encryptedCollections: Array.from(this.encryptedCollections),
            webCryptoAvailable: !!crypto?.subtle
        };
    }
    
    // ==================== 工具方法 ====================
    
    bufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
    
    base64ToBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes;
    }
    
    bufferToHex(buffer) {
        return Array.from(new Uint8Array(buffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
}

// 导出
if (typeof window !== 'undefined') {
    window.DatabaseEncryption = DatabaseEncryption;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseEncryption;
}

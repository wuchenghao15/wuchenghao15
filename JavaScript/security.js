/**
 * 安全模块 - 电子签名、Token和证书管理
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// 项目根目录
const PROJECT_ROOT = path.join(__dirname, '..');

// 安全配置目录
const SECURITY_DIR = path.join(PROJECT_ROOT, 'Security');
const CERTS_DIR = path.join(SECURITY_DIR, 'certs');
const KEYS_DIR = path.join(SECURITY_DIR, 'keys');

// 确保目录存在
fs.mkdirSync(SECURITY_DIR, { recursive: true });
fs.mkdirSync(CERTS_DIR, { recursive: true });
fs.mkdirSync(KEYS_DIR, { recursive: true });

// 读取或生成密钥
const getSecretKey = () => {
    const keyPath = path.join(KEYS_DIR, 'jwt_secret.key');
    
    try {
        if (fs.existsSync(keyPath)) {
            return fs.readFileSync(keyPath, 'utf8');
        }
        
        // 生成新的密钥
        const secretKey = crypto.randomBytes(32).toString('hex');
        fs.writeFileSync(keyPath, secretKey, 'utf8');
        console.log('[security.js] 生成新的JWT密钥');
        return secretKey;
    } catch (error) {
        console.error('[security.js] 获取密钥失败:', error);
        return process.env.JWT_SECRET || 'default_secret_key'; // 回退密钥
    }
};

// 电子签名模块
const digitalSignature = {
    // 生成密钥对
    generateKeyPair: (keyName = 'default') => {
        const keyPair = crypto.generateKeyPairSync('rsa', {
            modulusLength: 2048,
            publicKeyEncoding: {
                type: 'spki',
                format: 'pem'
            },
            privateKeyEncoding: {
                type: 'pkcs8',
                format: 'pem',
                cipher: 'aes-256-cbc',
                passphrase: 'mtscos_ai_passphrase'
            }
        });
        
        // 保存密钥
        fs.writeFileSync(path.join(KEYS_DIR, `${keyName}_public.pem`), keyPair.publicKey);
        fs.writeFileSync(path.join(KEYS_DIR, `${keyName}_private.pem`), keyPair.privateKey);
        
        return keyPair;
    },
    
    // 签名数据
    sign: (data, keyName = 'default') => {
        const privateKeyPath = path.join(KEYS_DIR, `${keyName}_private.pem`);
        
        if (!fs.existsSync(privateKeyPath)) {
            this.generateKeyPair(keyName);
        }
        
        const privateKey = fs.readFileSync(privateKeyPath, 'utf8');
        const sign = crypto.createSign('SHA256');
        sign.update(JSON.stringify(data));
        sign.end();
        
        const signature = sign.sign(
            {
                key: privateKey,
                passphrase: 'mtscos_ai_passphrase'
            },
            'base64'
        );
        
        return signature;
    },
    
    // 验证签名
    verify: (data, signature, keyName = 'default') => {
        const publicKeyPath = path.join(KEYS_DIR, `${keyName}_public.pem`);
        
        if (!fs.existsSync(publicKeyPath)) {
            return false;
        }
        
        const publicKey = fs.readFileSync(publicKeyPath, 'utf8');
        const verify = crypto.createVerify('SHA256');
        verify.update(JSON.stringify(data));
        verify.end();
        
        return verify.verify(publicKey, signature, 'base64');
    }
};

// Token认证模块
const tokenAuth = {
    secretKey: getSecretKey(),
    
    // 生成Token
    generateToken: (payload, expiresIn = '24h') => {
        return jwt.sign(payload, tokenAuth.secretKey, {
            expiresIn: expiresIn,
            issuer: 'mtscos-ai',
            audience: 'mtscos-ai-users'
        });
    },
    
    // 验证Token
    verifyToken: (token) => {
        try {
            return jwt.verify(token, tokenAuth.secretKey, {
                issuer: 'mtscos-ai',
                audience: 'mtscos-ai-users'
            });
        } catch (error) {
            console.error('[security.js] Token验证失败:', error.message);
            return null;
        }
    },
    
    // 中间件：验证Token
    middleware: (req, res, next) => {
        // 排除不需要认证的路由
        const excludedRoutes = [
            '/api/health',
            '/api/auth/login',
            '/api/auth/register'
        ];
        
        if (excludedRoutes.some(route => req.path.startsWith(route))) {
            return next();
        }
        
        // 获取Token
        const authHeader = req.headers.authorization;
        const token = authHeader && authHeader.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({
                error: 'Unauthorized',
                message: 'Token is required'
            });
        }
        
        // 验证Token
        const decoded = tokenAuth.verifyToken(token);
        
        if (!decoded) {
            return res.status(401).json({
                error: 'Unauthorized',
                message: 'Invalid token'
            });
        }
        
        // 将用户信息添加到请求中
        req.user = decoded;
        next();
    }
};

// 证书管理模块
const certificateManager = {
    // 生成自签名证书
    generateCertificate: (commonName = 'mtscos-ai.local', validityDays = 365) => {
        const keyPair = crypto.generateKeyPairSync('rsa', {
            modulusLength: 2048
        });
        
        // 创建证书请求
        const csr = crypto.createSign('SHA256');
        
        const attrs = [
            { name: 'commonName', value: commonName },
            { name: 'organizationName', value: 'MTSCOS AI' },
            { name: 'organizationalUnitName', value: 'Development' },
            { name: 'localityName', value: 'Localhost' },
            { name: 'stateOrProvinceName', value: 'Local' },
            { name: 'countryName', value: 'CN' }
        ];
        
        // 生成证书 (简化版自签名)
        const certificate = {
            version: 3,
            serialNumber: '01',
            issuer: attrs,
            subject: attrs,
            notBefore: new Date(),
            notAfter: new Date(Date.now() + validityDays * 24 * 60 * 60 * 1000),
            publicKey: keyPair.publicKey
        };
        
        // 保存证书和密钥
        const certPath = path.join(CERTS_DIR, `${commonName}.pem`);
        const keyPath = path.join(CERTS_DIR, `${commonName}.key`);
        
        // 注意：这是简化版证书，实际应用中应使用完整的X.509证书
        fs.writeFileSync(certPath, JSON.stringify(certificate, null, 2));
        fs.writeFileSync(keyPath, keyPair.privateKey.export({ type: 'pkcs1', format: 'pem' }));
        
        return {
            certificate,
            publicKey: keyPair.publicKey,
            privateKey: keyPair.privateKey
        };
    },
    
    // 获取证书
    getCertificate: (commonName = 'mtscos-ai.local') => {
        const certPath = path.join(CERTS_DIR, `${commonName}.pem`);
        const keyPath = path.join(CERTS_DIR, `${commonName}.key`);
        
        if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
            return {
                certificate: JSON.parse(fs.readFileSync(certPath, 'utf8')),
                publicKey: fs.readFileSync(certPath, 'utf8'),
                privateKey: fs.readFileSync(keyPath, 'utf8')
            };
        }
        
        // 如果证书不存在，生成新的
        return certificateManager.generateCertificate(commonName);
    },
    
    // 验证证书
    verifyCertificate: (certificate) => {
        try {
            // 检查证书是否过期
            const notBefore = new Date(certificate.notBefore);
            const notAfter = new Date(certificate.notAfter);
            const now = new Date();
            
            if (now < notBefore || now > notAfter) {
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('[security.js] 证书验证失败:', error);
            return false;
        }
    }
};

// 加密解密模块
const encryption = {
    algorithm: 'aes-256-cbc',
    
    // 生成加密密钥
    generateKey: () => {
        return crypto.randomBytes(32).toString('hex');
    },
    
    // 加密数据
    encrypt: (data, key) => {
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv(encryption.algorithm, Buffer.from(key, 'hex'), iv);
        
        let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
        encrypted += cipher.final('hex');
        
        return {
            iv: iv.toString('hex'),
            encryptedData: encrypted
        };
    },
    
    // 解密数据
    decrypt: (encryptedData, key, iv) => {
        const decipher = crypto.createDecipheriv(encryption.algorithm, Buffer.from(key, 'hex'), Buffer.from(iv, 'hex'));
        
        let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        
        return JSON.parse(decrypted);
    }
};

// 自我修复机制
const selfRepair = {
    // 检查安全配置
    checkSecurityConfig: () => {
        const checks = [];
        
        // 检查密钥
        checks.push({
            name: 'JWT密钥',
            status: fs.existsSync(path.join(KEYS_DIR, 'jwt_secret.key')) ? 'OK' : 'ERROR'
        });
        
        // 检查默认签名密钥对
        checks.push({
            name: '默认签名密钥对',
            status: (fs.existsSync(path.join(KEYS_DIR, 'default_public.pem')) && 
                     fs.existsSync(path.join(KEYS_DIR, 'default_private.pem'))) ? 'OK' : 'ERROR'
        });
        
        // 检查证书
        checks.push({
            name: '默认证书',
            status: (fs.existsSync(path.join(CERTS_DIR, 'mtscos-ai.local.pem')) && 
                     fs.existsSync(path.join(CERTS_DIR, 'mtscos-ai.local.key'))) ? 'OK' : 'ERROR'
        });
        
        return checks;
    },
    
    // 修复安全配置
    repair: () => {
        console.log('[security.js] 开始安全配置自我修复...');
        
        // 检查并生成JWT密钥
        if (!fs.existsSync(path.join(KEYS_DIR, 'jwt_secret.key'))) {
            console.log('[security.js] 重新生成JWT密钥');
            getSecretKey();
        }
        
        // 检查并生成默认签名密钥对
        if (!fs.existsSync(path.join(KEYS_DIR, 'default_public.pem')) || 
            !fs.existsSync(path.join(KEYS_DIR, 'default_private.pem'))) {
            console.log('[security.js] 重新生成默认签名密钥对');
            digitalSignature.generateKeyPair('default');
        }
        
        // 检查并生成默认证书
        if (!fs.existsSync(path.join(CERTS_DIR, 'mtscos-ai.local.pem')) || 
            !fs.existsSync(path.join(CERTS_DIR, 'mtscos-ai.local.key'))) {
            console.log('[security.js] 重新生成默认证书');
            certificateManager.generateCertificate();
        }
        
        console.log('[security.js] 安全配置自我修复完成');
        return true;
    }
};

// 导出模块
module.exports = {
    digitalSignature,
    tokenAuth,
    certificateManager,
    encryption,
    selfRepair,
    
    // 初始化安全模块
    initialize: () => {
        console.log('[security.js] 初始化安全模块...');
        
        // 确保目录存在
        fs.mkdirSync(SECURITY_DIR, { recursive: true });
        fs.mkdirSync(CERTS_DIR, { recursive: true });
        fs.mkdirSync(KEYS_DIR, { recursive: true });
        
        // 生成必要的密钥和证书
        if (!fs.existsSync(path.join(KEYS_DIR, 'jwt_secret.key'))) {
            getSecretKey();
        }
        
        if (!fs.existsSync(path.join(KEYS_DIR, 'default_public.pem')) || 
            !fs.existsSync(path.join(KEYS_DIR, 'default_private.pem'))) {
            digitalSignature.generateKeyPair('default');
        }
        
        if (!fs.existsSync(path.join(CERTS_DIR, 'mtscos-ai.local.pem')) || 
            !fs.existsSync(path.join(CERTS_DIR, 'mtscos-ai.local.key'))) {
            certificateManager.generateCertificate();
        }
        
        console.log('[security.js] 安全模块初始化完成');
        return true;
    }
};

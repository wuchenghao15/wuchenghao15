/**
 * MTSCOS 登录API服务器
 * 提供真实的用户认证、验证码验证、第三方登录集成等功能
 */

const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const mysql = require('mysql2/promise');
const redis = require('redis');
const crypto = require('crypto');
const svgCaptcha = require('svg-captcha');
const axios = require('axios');
const session = require('express-session');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const validator = require('validator');

const app = express();
const PORT = process.env.LOGIN_API_PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'mtscos-login-secret-key-2025';

// 安全中间件
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
            scriptSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", "https://api.weixin.qq.com", "https://graph.qq.com", "https://accounts.google.com"]
        }
    }
}));

app.use(cors({
    origin: ['http://localhost:8000', 'http://127.0.0.1:8000'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 会话配置
app.use(session({
    secret: process.env.SESSION_SECRET || 'mtscos-session-secret-2025',
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000 // 24小时
    },
    name: 'mtscos_session'
}));

// 限流配置
const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 5, // 最多5次登录尝试
    message: { success: false, message: '登录尝试次数过多，请15分钟后再试' },
    standardHeaders: true,
    legacyHeaders: false
});

const captchaLimiter = rateLimit({
    windowMs: 1 * 60 * 1000, // 1分钟
    max: 10, // 最多10次验证码请求
    message: { success: false, message: '验证码请求过于频繁，请稍后再试' }
});

// 数据库连接池配置
const dbPool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 3306,
    user: process.env.DB_USER || 'mtscos_user',
    password: process.env.DB_PASSWORD || 'mtscos_password',
    database: process.env.DB_NAME || 'mtscos_auth',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
    acquireTimeout: 60000,
    timeout: 60000,
    reconnect: true,
    charset: 'utf8mb4'
});

// Redis连接配置
const redisClient = redis.createClient({
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || '',
    db: 0
});

// 第三方登录配置
const OAUTH_CONFIG = {
    wechat: {
        appId: process.env.WECHAT_APP_ID || 'wx1234567890abcdef',
        appSecret: process.env.WECHAT_APP_SECRET || '1234567890abcdef1234567890abcdef',
        redirectUri: process.env.WECHAT_REDIRECT_URI || 'http://localhost:8000/auth/wechat/callback',
        apiUrl: 'https://api.weixin.qq.com/sns/oauth2/access_token'
    },
    qq: {
        appId: process.env.QQ_APP_ID || '1234567890',
        appSecret: process.env.QQ_APP_SECRET || '1234567890abcdef1234567890abcdef',
        redirectUri: process.env.QQ_REDIRECT_URI || 'http://localhost:8000/auth/qq/callback',
        apiUrl: 'https://graph.qq.com/oauth2.0/token'
    },
    google: {
        clientId: process.env.GOOGLE_CLIENT_ID || '1234567890-abcdef1234567890abcdef12345678.apps.googleusercontent.com',
        clientSecret: process.env.GOOGLE_CLIENT_SECRET || '1234567890abcdef',
        redirectUri: process.env.GOOGLE_REDIRECT_URI || 'http://localhost:8000/auth/google/callback'
    }
};

// 初始化数据库表
async function initializeDatabase() {
    try {
        const connection = await dbPool.getConnection();
        
        // 创建用户表
        await connection.execute(`
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                salt VARCHAR(32) NOT NULL,
                status ENUM('active', 'inactive', 'locked', 'deleted') DEFAULT 'active',
                role ENUM('admin', 'user', 'guest') DEFAULT 'user',
                avatar_url VARCHAR(255),
                last_login_time TIMESTAMP NULL,
                login_attempts INT DEFAULT 0,
                locked_until TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        `);
        
        // 创建第三方登录表
        await connection.execute(`
            CREATE TABLE IF NOT EXISTS oauth_accounts (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                provider ENUM('wechat', 'qq', 'google', 'github') NOT NULL,
                provider_id VARCHAR(100) NOT NULL,
                provider_data JSON,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY uk_provider_user (provider, provider_id),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        `);
        
        // 创建登录日志表
        await connection.execute(`
            CREATE TABLE IF NOT EXISTS login_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                username VARCHAR(50),
                ip_address VARCHAR(45),
                user_agent TEXT,
                login_type ENUM('password', 'oauth') DEFAULT 'password',
                status ENUM('success', 'failed', 'blocked') NOT NULL,
                failure_reason VARCHAR(255),
                session_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_username (username),
                INDEX idx_ip (ip_address),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        `);
        
        // 创建会话表
        await connection.execute(`
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                refresh_token VARCHAR(255) UNIQUE,
                ip_address VARCHAR(45),
                user_agent TEXT,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_session_token (session_token),
                INDEX idx_expires_at (expires_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        `);
        
        connection.release();
        console.log('数据库表初始化完成');
    } catch (error) {
        console.error('数据库初始化失败:', error);
        throw error;
    }
}

// 工具函数
class AuthUtils {
    // 密码加密
    static async hashPassword(password, salt = null) {
        const actualSalt = salt || crypto.randomBytes(16).toString('hex');
        const hash = crypto.pbkdf2Sync(password, actualSalt, 10000, 64, 'sha512').toString('hex');
        return { hash, salt: actualSalt };
    }
    
    // 验证密码
    static async verifyPassword(password, hash, salt) {
        const verifyHash = crypto.pbkdf2Sync(password, salt, 10000, 64, 'sha512').toString('hex');
        return hash === verifyHash;
    }
    
    // 生成JWT令牌
    static generateJWT(payload) {
        return jwt.sign(payload, JWT_SECRET, {
            expiresIn: '24h',
            issuer: 'mtscos-auth',
            audience: 'mtscos-frontend'
        });
    }
    
    // 验证JWT令牌
    static verifyJWT(token) {
        try {
            return jwt.verify(token, JWT_SECRET);
        } catch (error) {
            return null;
        }
    }
    
    // 生成验证码
    static generateCaptcha() {
        const captcha = svgCaptcha.create({
            size: 4,
            ignoreChars: '0o1iIl',
            noise: 2,
            color: true,
            background: '#f0f0f0',
            width: 120,
            height: 40,
            fontSize: 36
        });
        return {
            text: captcha.text.toLowerCase(),
            data: captcha.data
        };
    }
    
    // 验证输入数据
    static validateInput(data, rules) {
        const errors = [];
        
        for (const [field, rule] of Object.entries(rules)) {
            const value = data[field];
            
            if (rule.required && (!value || value.trim() === '')) {
                errors.push(`${rule.label || field}不能为空`);
                continue;
            }
            
            if (value && rule.type === 'email' && !validator.isEmail(value)) {
                errors.push(`${rule.label || field}格式不正确`);
            }
            
            if (value && rule.minLength && value.length < rule.minLength) {
                errors.push(`${rule.label || field}长度不能少于${rule.minLength}个字符`);
            }
            
            if (value && rule.maxLength && value.length > rule.maxLength) {
                errors.push(`${rule.label || field}长度不能超过${rule.maxLength}个字符`);
            }
            
            if (value && rule.pattern && !rule.pattern.test(value)) {
                errors.push(`${rule.label || field}格式不正确`);
            }
        }
        
        return errors;
    }
    
    // 记录登录日志
    static async logLogin(userId, username, ipAddress, userAgent, loginType, status, failureReason = null, sessionId = null) {
        try {
            const connection = await dbPool.getConnection();
            await connection.execute(`
                INSERT INTO login_logs (user_id, username, ip_address, user_agent, login_type, status, failure_reason, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            `, [userId, username, ipAddress, userAgent, loginType, status, failureReason, sessionId]);
            connection.release();
        } catch (error) {
            console.error('记录登录日志失败:', error);
        }
    }
}

// 中间件：验证JWT令牌
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ success: false, message: '访问令牌缺失' });
    }
    
    const decoded = AuthUtils.verifyJWT(token);
    if (!decoded) {
        return res.status(403).json({ success: false, message: '访问令牌无效或已过期' });
    }
    
    req.user = decoded;
    next();
}

// API路由

// 生成验证码
app.get('/api/captcha', captchaLimiter, async (req, res) => {
    try {
        const captcha = AuthUtils.generateCaptcha();
        const captchaId = crypto.randomBytes(16).toString('hex');
        
        // 将验证码存储到Redis，5分钟过期
        await redisClient.setex(`captcha:${captchaId}`, 300, captcha.text);
        
        res.json({
            success: true,
            data: {
                captchaId,
                captchaImage: captcha.data
            }
        });
    } catch (error) {
        console.error('生成验证码失败:', error);
        res.status(500).json({ success: false, message: '验证码生成失败' });
    }
});

// 用户登录
app.post('/api/login', loginLimiter, async (req, res) => {
    try {
        const { username, password, captchaId, captchaText, rememberMe = false } = req.body;
        
        // 验证输入数据
        const validationErrors = AuthUtils.validateInput(req.body, {
            username: { required: true, label: '用户名', minLength: 3, maxLength: 50 },
            password: { required: true, label: '密码', minLength: 6 },
            captchaId: { required: true, label: '验证码ID' },
            captchaText: { required: true, label: '验证码', minLength: 4, maxLength: 4 }
        });
        
        if (validationErrors.length > 0) {
            return res.status(400).json({
                success: false,
                message: validationErrors.join(', ')
            });
        }
        
        // 验证验证码
        const storedCaptcha = await redisClient.get(`captcha:${captchaId}`);
        if (!storedCaptcha || storedCaptcha !== captchaText.toLowerCase()) {
            await AuthUtils.logLogin(null, username, req.ip, req.get('User-Agent'), 'password', 'failed', '验证码错误');
            return res.status(400).json({ success: false, message: '验证码错误' });
        }
        
        // 删除已使用的验证码
        await redisClient.del(`captcha:${captchaId}`);
        
        // 查询用户
        const connection = await dbPool.getConnection();
        const [users] = await connection.execute(
            'SELECT * FROM users WHERE username = ? AND status = "active"',
            [username]
        );
        
        if (users.length === 0) {
            await AuthUtils.logLogin(null, username, req.ip, req.get('User-Agent'), 'password', 'failed', '用户不存在或已被禁用');
            connection.release();
            return res.status(401).json({ success: false, message: '用户名或密码错误' });
        }
        
        const user = users[0];
        
        // 检查账户是否被锁定
        if (user.locked_until && new Date(user.locked_until) > new Date()) {
            const remainingTime = Math.ceil((new Date(user.locked_until) - new Date()) / 60000);
            await AuthUtils.logLogin(user.id, username, req.ip, req.get('User-Agent'), 'password', 'failed', `账户被锁定，剩余${remainingTime}分钟`);
            connection.release();
            return res.status(423).json({ 
                success: false, 
                message: `账户已被锁定，请${remainingTime}分钟后再试` 
            });
        }
        
        // 验证密码
        const isValidPassword = await AuthUtils.verifyPassword(password, user.password_hash, user.salt);
        if (!isValidPassword) {
            // 增加登录失败次数
            const newAttempts = user.login_attempts + 1;
            let lockedUntil = null;
            
            if (newAttempts >= 5) {
                lockedUntil = new Date(Date.now() + 30 * 60 * 1000); // 锁定30分钟
            }
            
            await connection.execute(
                'UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?',
                [newAttempts, lockedUntil, user.id]
            );
            
            const failureReason = newAttempts >= 5 ? '密码错误次数过多，账户已锁定' : '密码错误';
            await AuthUtils.logLogin(user.id, username, req.ip, req.get('User-Agent'), 'password', 'failed', failureReason);
            
            connection.release();
            return res.status(401).json({ 
                success: false, 
                message: failureReason,
                remainingAttempts: Math.max(0, 5 - newAttempts)
            });
        }
        
        // 登录成功，重置失败次数
        await connection.execute(
            'UPDATE users SET login_attempts = 0, locked_until = NULL, last_login_time = NOW() WHERE id = ?',
            [user.id]
        );
        
        // 生成JWT令牌
        const tokenPayload = {
            userId: user.id,
            username: user.username,
            role: user.role,
            loginTime: new Date().toISOString()
        };
        
        const accessToken = AuthUtils.generateJWT(tokenPayload);
        const refreshToken = crypto.randomBytes(32).toString('hex');
        const sessionId = crypto.randomBytes(16).toString('hex');
        
        // 存储会话信息
        const expiresAt = new Date(Date.now() + (rememberMe ? 7 * 24 * 60 * 60 * 1000 : 24 * 60 * 60 * 1000));
        await connection.execute(
            'INSERT INTO user_sessions (user_id, session_token, refresh_token, ip_address, user_agent, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
            [user.id, accessToken, refreshToken, req.ip, req.get('User-Agent'), expiresAt]
        );
        
        // 记录成功登录日志
        await AuthUtils.logLogin(user.id, username, req.ip, req.get('User-Agent'), 'password', 'success', null, sessionId);
        
        connection.release();
        
        res.json({
            success: true,
            message: '登录成功',
            data: {
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    role: user.role,
                    avatar_url: user.avatar_url,
                    last_login_time: user.last_login_time
                },
                tokens: {
                    accessToken,
                    refreshToken,
                    expiresIn: rememberMe ? 7 * 24 * 60 * 60 : 24 * 60 * 60
                },
                sessionId
            }
        });
        
    } catch (error) {
        console.error('登录失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 第三方登录 - 获取授权URL
app.get('/api/oauth/:provider', async (req, res) => {
    try {
        const { provider } = req.params;
        const config = OAUTH_CONFIG[provider];
        
        if (!config) {
            return res.status(400).json({ success: false, message: '不支持的登录方式' });
        }
        
        let authUrl = '';
        const state = crypto.randomBytes(16).toString('hex');
        
        switch (provider) {
            case 'wechat':
                authUrl = `https://open.weixin.qq.com/connect/qrconnect?appid=${config.appId}&redirect_uri=${encodeURIComponent(config.redirectUri)}&response_type=code&scope=snsapi_login&state=${state}#wechat_redirect`;
                break;
            case 'qq':
                authUrl = `https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=${config.appId}&redirect_uri=${encodeURIComponent(config.redirectUri)}&scope=get_user_info&state=${state}`;
                break;
            case 'google':
                authUrl = `https://accounts.google.com/oauth/authorize?response_type=code&client_id=${config.clientId}&redirect_uri=${encodeURIComponent(config.redirectUri)}&scope=openid email profile&state=${state}`;
                break;
            default:
                return res.status(400).json({ success: false, message: '不支持的登录方式' });
        }
        
        // 将state存储到Redis，10分钟过期
        await redisClient.setex(`oauth_state:${state}`, 600, JSON.stringify({ provider }));
        
        res.json({
            success: true,
            data: {
                authUrl,
                state
            }
        });
        
    } catch (error) {
        console.error('获取第三方登录URL失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 第三方登录 - 回调处理
app.post('/api/oauth/:provider/callback', async (req, res) => {
    try {
        const { provider } = req.params;
        const { code, state } = req.body;
        
        if (!code || !state) {
            return res.status(400).json({ success: false, message: '授权参数缺失' });
        }
        
        // 验证state
        const storedState = await redisClient.get(`oauth_state:${state}`);
        if (!storedState) {
            return res.status(400).json({ success: false, message: '授权状态已过期或无效' });
        }
        
        const stateData = JSON.parse(storedState);
        await redisClient.del(`oauth_state:${state}`);
        
        // 获取访问令牌
        let userInfo = null;
        const config = OAUTH_CONFIG[provider];
        
        switch (provider) {
            case 'wechat':
                userInfo = await handleWechatCallback(code, config);
                break;
            case 'qq':
                userInfo = await handleQQCallback(code, config);
                break;
            case 'google':
                userInfo = await handleGoogleCallback(code, config);
                break;
            default:
                return res.status(400).json({ success: false, message: '不支持的登录方式' });
        }
        
        if (!userInfo) {
            return res.status(400).json({ success: false, message: '获取用户信息失败' });
        }
        
        // 查找或创建用户
        const connection = await dbPool.getConnection();
        const [oauthAccounts] = await connection.execute(
            'SELECT oa.*, u.* FROM oauth_accounts oa JOIN users u ON oa.user_id = u.id WHERE oa.provider = ? AND oa.provider_id = ?',
            [provider, userInfo.id]
        );
        
        let user;
        if (oauthAccounts.length > 0) {
            user = oauthAccounts[0];
            
            // 更新OAuth信息
            await connection.execute(
                'UPDATE oauth_accounts SET provider_data = ?, access_token = ?, refresh_token = ?, updated_at = NOW() WHERE id = ?',
                [JSON.stringify(userInfo), userInfo.access_token, userInfo.refresh_token, oauthAccounts[0].id]
            );
        } else {
            // 创建新用户
            const tempPassword = crypto.randomBytes(32).toString('hex');
            const { hash, salt } = await AuthUtils.hashPassword(tempPassword);
            
            const [result] = await connection.execute(
                'INSERT INTO users (username, email, password_hash, salt, role, status, avatar_url) VALUES (?, ?, ?, ?, ?, ?, ?)',
                [
                    `${provider}_${userInfo.id}`,
                    userInfo.email || null,
                    hash,
                    salt,
                    'user',
                    'active',
                    userInfo.avatar || null
                ]
            );
            
            const userId = result.insertId;
            
            // 创建OAuth账户关联
            await connection.execute(
                'INSERT INTO oauth_accounts (user_id, provider, provider_id, provider_data, access_token, refresh_token) VALUES (?, ?, ?, ?, ?, ?)',
                [userId, provider, userInfo.id, JSON.stringify(userInfo), userInfo.access_token, userInfo.refresh_token]
            );
            
            // 获取新用户信息
            const [newUsers] = await connection.execute('SELECT * FROM users WHERE id = ?', [userId]);
            user = newUsers[0];
        }
        
        // 生成JWT令牌
        const tokenPayload = {
            userId: user.id,
            username: user.username,
            role: user.role,
            loginTime: new Date().toISOString(),
            oauthProvider: provider
        };
        
        const accessToken = AuthUtils.generateJWT(tokenPayload);
        const refreshToken = crypto.randomBytes(32).toString('hex');
        const sessionId = crypto.randomBytes(16).toString('hex');
        
        // 存储会话信息
        const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000);
        await connection.execute(
            'INSERT INTO user_sessions (user_id, session_token, refresh_token, ip_address, user_agent, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
            [user.id, accessToken, refreshToken, req.ip, req.get('User-Agent'), expiresAt]
        );
        
        // 记录登录日志
        await AuthUtils.logLogin(user.id, user.username, req.ip, req.get('User-Agent'), 'oauth', 'success', null, sessionId);
        
        connection.release();
        
        res.json({
            success: true,
            message: '登录成功',
            data: {
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    role: user.role,
                    avatar_url: user.avatar_url,
                    oauthProvider: provider
                },
                tokens: {
                    accessToken,
                    refreshToken,
                    expiresIn: 24 * 60 * 60
                },
                sessionId
            }
        });
        
    } catch (error) {
        console.error('第三方登录回调失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 处理微信回调
async function handleWechatCallback(code, config) {
    try {
        // 获取访问令牌
        const tokenResponse = await axios.get(config.apiUrl, {
            params: {
                appid: config.appId,
                secret: config.appSecret,
                code: code,
                grant_type: 'authorization_code'
            }
        });
        
        const { access_token, openid, refresh_token } = tokenResponse.data;
        
        // 获取用户信息
        const userResponse = await axios.get('https://api.weixin.qq.com/sns/userinfo', {
            params: {
                access_token: access_token,
                openid: openid
            }
        });
        
        const userData = userResponse.data;
        
        return {
            id: openid,
            nickname: userData.nickname,
            avatar: userData.headimgurl,
            email: null, // 微信不提供邮箱
            access_token: access_token,
            refresh_token: refresh_token
        };
    } catch (error) {
        console.error('微信登录失败:', error);
        return null;
    }
}

// 处理QQ回调
async function handleQQCallback(code, config) {
    try {
        // 获取访问令牌
        const tokenResponse = await axios.get(config.apiUrl, {
            params: {
                client_id: config.appId,
                client_secret: config.appSecret,
                code: code,
                grant_type: 'authorization_code',
                redirect_uri: config.redirectUri
            }
        });
        
        const tokenData = tokenResponse.data;
        const access_token = new URLSearchParams(tokenData).get('access_token');
        
        // 获取OpenID
        const openidResponse = await axios.get('https://graph.qq.com/oauth2.0/me', {
            params: {
                access_token: access_token
            }
        });
        
        const openidData = JSON.parse(openidResponse.data.replace('callback(', '').replace(');', ''));
        const openid = openidData.openid;
        
        // 获取用户信息
        const userResponse = await axios.get('https://graph.qq.com/user/get_user_info', {
            params: {
                access_token: access_token,
                oauth_consumer_key: config.appId,
                openid: openid
            }
        });
        
        const userData = userResponse.data;
        
        return {
            id: openid,
            nickname: userData.nickname,
            avatar: userData.figureurl_qq_2 || userData.figureurl_qq_1,
            email: null, // QQ不提供邮箱
            access_token: access_token,
            refresh_token: null
        };
    } catch (error) {
        console.error('QQ登录失败:', error);
        return null;
    }
}

// 处理Google回调
async function handleGoogleCallback(code, config) {
    try {
        // 获取访问令牌
        const tokenResponse = await axios.post('https://oauth2.googleapis.com/token', {
            client_id: config.clientId,
            client_secret: config.clientSecret,
            code: code,
            grant_type: 'authorization_code',
            redirect_uri: config.redirectUri
        });
        
        const { access_token, refresh_token, id_token } = tokenResponse.data;
        
        // 获取用户信息
        const userResponse = await axios.get('https://www.googleapis.com/oauth2/v2/userinfo', {
            headers: {
                Authorization: `Bearer ${access_token}`
            }
        });
        
        const userData = userResponse.data;
        
        return {
            id: userData.id,
            nickname: userData.name,
            email: userData.email,
            avatar: userData.picture,
            access_token: access_token,
            refresh_token: refresh_token
        };
    } catch (error) {
        console.error('Google登录失败:', error);
        return null;
    }
}

// 用户登出
app.post('/api/logout', authenticateToken, async (req, res) => {
    try {
        const connection = await dbPool.getConnection();
        await connection.execute(
            'DELETE FROM user_sessions WHERE session_token = ?',
            [req.headers.authorization.split(' ')[1]]
        );
        connection.release();
        
        res.json({ success: true, message: '登出成功' });
    } catch (error) {
        console.error('登出失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 刷新令牌
app.post('/api/refresh', async (req, res) => {
    try {
        const { refreshToken } = req.body;
        
        if (!refreshToken) {
            return res.status(400).json({ success: false, message: '刷新令牌缺失' });
        }
        
        const connection = await dbPool.getConnection();
        const [sessions] = await connection.execute(
            'SELECT s.*, u.* FROM user_sessions s JOIN users u ON s.user_id = u.id WHERE s.refresh_token = ? AND s.expires_at > NOW()',
            [refreshToken]
        );
        
        if (sessions.length === 0) {
            connection.release();
            return res.status(401).json({ success: false, message: '刷新令牌无效或已过期' });
        }
        
        const session = sessions[0];
        
        // 生成新的访问令牌
        const tokenPayload = {
            userId: session.user_id,
            username: session.username,
            role: session.role,
            loginTime: new Date().toISOString()
        };
        
        const newAccessToken = AuthUtils.generateJWT(tokenPayload);
        
        // 更新会话
        await connection.execute(
            'UPDATE user_sessions SET session_token = ?, last_accessed = NOW() WHERE id = ?',
            [newAccessToken, session.id]
        );
        
        connection.release();
        
        res.json({
            success: true,
            data: {
                accessToken: newAccessToken,
                expiresIn: 24 * 60 * 60
            }
        });
        
    } catch (error) {
        console.error('刷新令牌失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 获取用户信息
app.get('/api/user', authenticateToken, async (req, res) => {
    try {
        const connection = await dbPool.getConnection();
        const [users] = await connection.execute(
            'SELECT id, username, email, role, avatar_url, last_login_time, created_at FROM users WHERE id = ? AND status = "active"',
            [req.user.userId]
        );
        
        if (users.length === 0) {
            connection.release();
            return res.status(404).json({ success: false, message: '用户不存在' });
        }
        
        connection.release();
        
        res.json({
            success: true,
            data: users[0]
        });
        
    } catch (error) {
        console.error('获取用户信息失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 错误处理中间件
app.use((error, req, res, next) => {
    console.error('服务器错误:', error);
    res.status(500).json({ 
        success: false, 
        message: process.env.NODE_ENV === 'production' ? '服务器内部错误' : error.message 
    });
});

// 404处理
app.use((req, res) => {
    res.status(404).json({ success: false, message: '接口不存在' });
});

// 启动服务器
async function startServer() {
    try {
        // 初始化数据库
        await initializeDatabase();
        
        // 连接Redis
        await redisClient.connect();
        console.log('Redis连接成功');
        
        // 启动服务器
        app.listen(PORT, () => {
            console.log(`MTSCOS登录API服务器运行在端口 ${PORT}`);
            console.log(`API文档: http://localhost:${PORT}/api`);
        });
    } catch (error) {
        console.error('服务器启动失败:', error);
        process.exit(1);
    }
}

// 优雅关闭
process.on('SIGINT', async () => {
    console.log('正在关闭服务器...');
    await redisClient.quit();
    await dbPool.end();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('正在关闭服务器...');
    await redisClient.quit();
    await dbPool.end();
    process.exit(0);
});

// 启动服务器
startServer();
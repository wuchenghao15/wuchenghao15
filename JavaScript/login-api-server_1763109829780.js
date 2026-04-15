/**
 * MTSCOS 登录API服务器
 * 提供用户认证、会话管理、密码重置等功能
 */

// 加载环境变量
require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const session = require('express-session');
const { createClient } = require('redis');
const RedisStore = require('connect-redis').default;
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const svgCaptcha = require('svg-captcha');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const mysql = require('mysql2/promise');
const moment = require('moment');

const app = express();
const PORT = process.env.PORT || 3000;

// 配置日志
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'login-api' },
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' }),
    ],
});

if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: winston.format.simple()
    }));
}

// 安全中间件
app.use(helmet());
app.use(compression());
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
}));

// 限流中间件
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100, // 限制每个IP 15分钟内最多100个请求
    message: {
        success: false,
        message: '请求过于频繁，请稍后再试'
    }
});
app.use('/api/', limiter);

// 登录限流
const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 5, // 限制每个IP 15分钟内最多5次登录尝试
    message: {
        success: false,
        message: '登录尝试过于频繁，请15分钟后再试'
    }
});

// 解析请求体
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 数据库连接
let db;
async function initDatabase() {
    try {
        db = await mysql.createConnection({
            host: process.env.DB_HOST || 'localhost',
            user: process.env.DB_USER || 'root',
            password: process.env.DB_PASSWORD || '',
            database: process.env.DB_NAME || 'mtscos_ai',
            charset: 'utf8mb4',
            timezone: '+08:00'
        });
        
        logger.info('数据库连接成功');
        
        // 测试连接
        await db.execute('SELECT 1');
        logger.info('数据库连接测试成功');
        
    } catch (error) {
        logger.error('数据库连接失败:', error);
        process.exit(1);
    }
}

// Redis连接
let redisClient;
async function initRedis() {
    try {
        redisClient = createClient({
            url: process.env.REDIS_URL || 'redis://localhost:6379'
        });
        
        redisClient.on('error', (err) => {
            logger.error('Redis连接错误:', err);
        });
        
        redisClient.on('connect', () => {
            logger.info('Redis连接成功');
        });
        
        await redisClient.connect();
        
    } catch (error) {
        logger.error('Redis连接失败:', error);
        process.exit(1);
    }
}

// JWT认证中间件
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({
            success: false,
            message: '访问令牌缺失'
        });
    }
    
    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({
                success: false,
                message: '访问令牌无效'
            });
        }
        req.user = user;
        next();
    });
}

// 记录登录尝试
async function logLoginAttempt(userId, ipAddress, userAgent, success) {
    try {
        await db.execute(
            'INSERT INTO login_logs (user_id, ip_address, user_agent, success, created_at) VALUES (?, ?, ?, ?, NOW())',
            [userId, ipAddress, userAgent, success]
        );
    } catch (error) {
        logger.error('记录登录尝试失败:', error);
    }
}

// 登录验证规则
const loginValidation = [
    body('username').trim().isLength({ min: 3, max: 50 }).withMessage('用户名长度必须在3-50个字符之间'),
    body('password').isLength({ min: 6 }).withMessage('密码长度至少6个字符'),
    body('captcha').trim().isLength({ min: 4, max: 6 }).withMessage('验证码格式不正确'),
    body('captchaId').notEmpty().withMessage('验证码ID不能为空')
];

// 用户注册验证规则
const registerValidation = [
    body('username').trim().isLength({ min: 3, max: 50 }).withMessage('用户名长度必须在3-50个字符之间'),
    body('email').isEmail().withMessage('邮箱格式不正确'),
    body('password').isLength({ min: 6 }).withMessage('密码长度至少6个字符'),
    body('confirmPassword').custom((value, { req }) => {
        if (value !== req.body.password) {
            throw new Error('确认密码不匹配');
        }
        return true;
    })
];

// 密码重置验证规则
const passwordResetValidation = [
    body('email').isEmail().withMessage('邮箱格式不正确')
];

// 密码更新验证规则
const passwordUpdateValidation = [
    body('token').notEmpty().withMessage('重置令牌不能为空'),
    body('password').isLength({ min: 6 }).withMessage('密码长度至少6个字符'),
    body('confirmPassword').custom((value, { req }) => {
        if (value !== req.body.password) {
            throw new Error('确认密码不匹配');
        }
        return true;
    })
];

// API路由

// 验证码生成
app.get('/api/captcha', (req, res) => {
    try {
        const captcha = svgCaptcha.create({
            size: 4,
            noise: 2,
            color: true,
            background: '#f0f0f0'
        });
        
        const captchaId = uuidv4();
        const captchaText = captcha.text.toLowerCase();
        
        // 存储验证码到Redis
        redisClient.setEx(`captcha:${captchaId}`, 300, captchaText);
        
        res.json({
            success: true,
            data: {
                captchaId,
                captchaImage: captcha.data
            }
        });
    } catch (error) {
        logger.error('验证码生成失败:', error);
        res.status(500).json({
            success: false,
            message: '验证码生成失败'
        });
    }
});

// 用户登录
app.post('/api/login', loginLimiter, loginValidation, async (req, res) => {
    try {
        // 检查验证结果
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: '输入验证失败',
                errors: errors.array()
            });
        }

        const { username, password, captcha, captchaId, rememberMe = false } = req.body;
        
        // 验证验证码
        const storedCaptcha = await redisClient.get(`captcha:${captchaId}`);
        if (!storedCaptcha || storedCaptcha !== captcha.toLowerCase()) {
            return res.status(400).json({
                success: false,
                message: '验证码错误'
            });
        }
        
        // 删除已使用的验证码
        await redisClient.del(`captcha:${captchaId}`);
        
        // 查询用户
        const [users] = await db.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            [username, username]
        );
        
        if (users.length === 0) {
            return res.status(401).json({
                success: false,
                message: '用户名或密码错误'
            });
        }
        
        const user = users[0];
        
        // 检查账户状态
        if (user.status !== 'active') {
            return res.status(401).json({
                success: false,
                message: '账户已被禁用'
            });
        }
        
        // 验证密码
        const isValidPassword = await bcrypt.compare(password, user.password);
        if (!isValidPassword) {
            // 记录登录失败
            await logLoginAttempt(user.id, req.ip, req.get('User-Agent'), false);
            return res.status(401).json({
                success: false,
                message: '用户名或密码错误'
            });
        }
        
        // 生成JWT令牌
        const tokenExpiry = rememberMe ? '30d' : '24h';
        const token = jwt.sign(
            { 
                userId: user.id, 
                username: user.username,
                role: user.role 
            },
            process.env.JWT_SECRET,
            { expiresIn: tokenExpiry }
        );
        
        // 创建会话
        const sessionId = uuidv4();
        const sessionData = {
            userId: user.id,
            username: user.username,
            role: user.role,
            loginTime: new Date().toISOString(),
            lastActivity: new Date().toISOString(),
            ipAddress: req.ip,
            userAgent: req.get('User-Agent')
        };
        
        await redisClient.setEx(`session:${sessionId}`, 86400, JSON.stringify(sessionData));
        
        // 记录登录成功
        await logLoginAttempt(user.id, req.ip, req.get('User-Agent'), true);
        
        // 更新用户最后登录时间
        await db.execute(
            'UPDATE users SET last_login = NOW(), last_login_ip = ? WHERE id = ?',
            [req.ip, user.id]
        );
        
        res.json({
            success: true,
            message: '登录成功',
            data: {
                token,
                sessionId,
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    role: user.role,
                    avatar: user.avatar,
                    lastLogin: user.last_login
                },
                expiresIn: rememberMe ? 30 * 24 * 60 * 60 : 24 * 60 * 60
            }
        });
        
    } catch (error) {
        logger.error('登录失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 刷新令牌
app.post('/api/refresh-token', authenticateToken, async (req, res) => {
    try {
        const user = req.user;
        const { rememberMe = false } = req.body;
        
        const tokenExpiry = rememberMe ? '30d' : '24h';
        const newToken = jwt.sign(
            { 
                userId: user.id, 
                username: user.username,
                role: user.role 
            },
            process.env.JWT_SECRET,
            { expiresIn: tokenExpiry }
        );
        
        res.json({
            success: true,
            data: {
                token: newToken,
                expiresIn: rememberMe ? 30 * 24 * 60 * 60 : 24 * 60 * 60
            }
        });
        
    } catch (error) {
        logger.error('令牌刷新失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 验证令牌
app.get('/api/verify-token', authenticateToken, (req, res) => {
    res.json({
        success: true,
        data: {
            user: req.user
        }
    });
});

// 用户登出
app.post('/api/logout', authenticateToken, async (req, res) => {
    try {
        const sessionId = req.headers['x-session-id'];
        if (sessionId) {
            await redisClient.del(`session:${sessionId}`);
        }
        
        res.json({
            success: true,
            message: '登出成功'
        });
        
    } catch (error) {
        logger.error('登出失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 获取用户信息
app.get('/api/user/profile', authenticateToken, async (req, res) => {
    try {
        const [users] = await db.execute(
            'SELECT id, username, email, role, avatar, created_at, last_login FROM users WHERE id = ?',
            [req.user.userId]
        );
        
        if (users.length === 0) {
            return res.status(404).json({
                success: false,
                message: '用户不存在'
            });
        }
        
        res.json({
            success: true,
            data: {
                user: users[0]
            }
        });
        
    } catch (error) {
        logger.error('获取用户信息失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 心跳检测
app.post('/api/heartbeat', authenticateToken, async (req, res) => {
    try {
        const sessionId = req.headers['x-session-id'];
        if (sessionId) {
            const sessionData = await redisClient.get(`session:${sessionId}`);
            if (sessionData) {
                const session = JSON.parse(sessionData);
                session.lastActivity = new Date().toISOString();
                await redisClient.setEx(`session:${sessionId}`, 86400, JSON.stringify(session));
            }
        }
        
        res.json({
            success: true,
            data: {
                timestamp: new Date().toISOString()
            }
        });
        
    } catch (error) {
        logger.error('心跳检测失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 用户注册
app.post('/api/register', registerValidation, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: '输入验证失败',
                errors: errors.array()
            });
        }

        const { username, email, password } = req.body;
        
        // 检查用户名是否已存在
        const [existingUsers] = await db.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            [username, email]
        );
        
        if (existingUsers.length > 0) {
            return res.status(409).json({
                success: false,
                message: '用户名或邮箱已存在'
            });
        }
        
        // 加密密码
        const hashedPassword = await bcrypt.hash(password, 12);
        
        // 创建用户
        const [result] = await db.execute(
            'INSERT INTO users (username, email, password, role, status) VALUES (?, ?, ?, ?, ?)',
            [username, email, hashedPassword, 'user', 'active']
        );
        
        res.status(201).json({
            success: true,
            message: '注册成功',
            data: {
                userId: result.insertId
            }
        });
        
    } catch (error) {
        logger.error('用户注册失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 密码重置请求
app.post('/api/password-reset-request', passwordResetValidation, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: '输入验证失败',
                errors: errors.array()
            });
        }

        const { email } = req.body;
        
        const [users] = await db.execute(
            'SELECT id, username FROM users WHERE email = ?',
            [email]
        );
        
        if (users.length === 0) {
            // 为了安全，即使用户不存在也返回成功
            return res.json({
                success: true,
                message: '如果邮箱存在，重置链接已发送'
            });
        }
        
        const user = users[0];
        const resetToken = uuidv4();
        const expiryTime = new Date(Date.now() + 3600000); // 1小时后过期
        
        await db.execute(
            'INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)',
            [user.id, resetToken, expiryTime]
        );
        
        // 这里应该发送邮件，暂时只返回成功信息
        logger.info(`密码重置请求: 用户 ${user.username}, 邮箱 ${email}, 令牌 ${resetToken}`);
        
        res.json({
            success: true,
            message: '如果邮箱存在，重置链接已发送'
        });
        
    } catch (error) {
        logger.error('密码重置请求失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 密码重置确认
app.post('/api/password-reset-confirm', passwordUpdateValidation, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: '输入验证失败',
                errors: errors.array()
            });
        }

        const { token, password } = req.body;
        
        const [resets] = await db.execute(
            'SELECT user_id FROM password_resets WHERE token = ? AND expires_at > NOW() AND used = FALSE',
            [token]
        );
        
        if (resets.length === 0) {
            return res.status(400).json({
                success: false,
                message: '重置令牌无效或已过期'
            });
        }
        
        const userId = resets[0].user_id;
        const hashedPassword = await bcrypt.hash(password, 12);
        
        await db.execute(
            'UPDATE users SET password = ? WHERE id = ?',
            [hashedPassword, userId]
        );
        
        await db.execute(
            'UPDATE password_resets SET used = TRUE WHERE token = ?',
            [token]
        );
        
        res.json({
            success: true,
            message: '密码重置成功'
        });
        
    } catch (error) {
        logger.error('密码重置确认失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({
        success: true,
        message: '服务运行正常',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

// 错误处理中间件
app.use((err, req, res, next) => {
    logger.error('未处理的错误:', err);
    res.status(500).json({
        success: false,
        message: '服务器内部错误'
    });
});

// 404处理
app.use('*', (req, res) => {
    res.status(404).json({
        success: false,
        message: '接口不存在'
    });
});

// 启动服务器
async function startServer() {
    try {
        await initDatabase();
        await initRedis();
        
        app.listen(PORT, () => {
            logger.info(`登录API服务器启动成功，端口: ${PORT}`);
            console.log(`🚀 MTSCOS 登录API服务器运行在端口 ${PORT}`);
            console.log(`📊 健康检查: http://localhost:${PORT}/api/health`);
            console.log(`🔧 环境: ${process.env.NODE_ENV || 'development'}`);
        });
        
    } catch (error) {
        logger.error('服务器启动失败:', error);
        process.exit(1);
    }
}

// 优雅关闭
process.on('SIGTERM', async () => {
    logger.info('收到SIGTERM信号，开始优雅关闭...');
    if (db) await db.end();
    if (redisClient) await redisClient.quit();
    process.exit(0);
});

process.on('SIGINT', async () => {
    logger.info('收到SIGINT信号，开始优雅关闭...');
    if (db) await db.end();
    if (redisClient) await redisClient.quit();
    process.exit(0);
});

startServer();

module.exports = app;
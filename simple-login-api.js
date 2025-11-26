/**
 * 简化的登录API服务器 - 用于测试
 * 不需要数据库和Redis，使用内存存储
 */

const express = require('express');
const cors = require('cors');
const crypto = require('crypto');

const app = express();
const PORT = 3001;

// 内存存储
const users = new Map();
const sessions = new Map();
const captchaStore = new Map();

// 初始化测试用户
users.set('admin', {
    id: 1,
    username: 'admin',
    password: 'admin123',
    email: 'admin@mtscos.com',
    role: 'admin',
    avatar_url: null,
    last_login_time: null
});

users.set('user', {
    id: 2,
    username: 'user',
    password: 'user123',
    email: 'user@mtscos.com',
    role: 'user',
    avatar_url: null,
    last_login_time: null
});

// 中间件
app.use(cors({
    origin: ['http://localhost:8000', 'http://127.0.0.1:8000'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 生成验证码
app.get('/api/captcha', (req, res) => {
    const captchaId = crypto.randomBytes(16).toString('hex');
    const captchaText = Math.random().toString(36).substring(2, 6).toUpperCase();
    
    captchaStore.set(captchaId, captchaText.toLowerCase());
    
    // 5分钟后删除验证码
    setTimeout(() => {
        captchaStore.delete(captchaId);
    }, 5 * 60 * 1000);
    
    res.json({
        success: true,
        data: {
            captchaId,
            captchaImage: `data:image/svg+xml;base64,${Buffer.from(`
                <svg width="120" height="40" xmlns="http://www.w3.org/2000/svg">
                    <text x="10" y="30" font-family="Arial" font-size="20" fill="#333">${captchaText}</text>
                </svg>
            `).toString('base64')}`
        }
    });
});

// 用户登录
app.post('/api/login', (req, res) => {
    try {
        const { username, password, captchaId, captchaText, rememberMe = false } = req.body;
        
        // 验证输入数据
        if (!username || !password || !captchaId || !captchaText) {
            return res.status(400).json({
                success: false,
                message: '请填写完整的登录信息'
            });
        }
        
        // 验证验证码
        const storedCaptcha = captchaStore.get(captchaId);
        if (!storedCaptcha || storedCaptcha !== captchaText.toLowerCase()) {
            return res.status(400).json({ 
                success: false, 
                message: '验证码错误' 
            });
        }
        
        // 删除已使用的验证码
        captchaStore.delete(captchaId);
        
        // 查询用户
        const user = users.get(username);
        if (!user || user.password !== password) {
            return res.status(401).json({ 
                success: false, 
                message: '用户名或密码错误' 
            });
        }
        
        // 生成令牌
        const accessToken = crypto.randomBytes(32).toString('hex');
        const refreshToken = crypto.randomBytes(32).toString('hex');
        const sessionId = crypto.randomBytes(16).toString('hex');
        
        // 存储会话信息
        const expiresAt = new Date(Date.now() + (rememberMe ? 7 * 24 * 60 * 60 * 1000 : 24 * 60 * 60 * 1000));
        sessions.set(sessionId, {
            userId: user.id,
            username: user.username,
            accessToken,
            refreshToken,
            expiresAt
        });
        
        // 更新用户最后登录时间
        user.last_login_time = new Date().toISOString();
        
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
        console.error('[simple-login-api] 登录失败:', error);
        res.status(500).json({ success: false, message: '服务器内部错误' });
    }
});

// 验证令牌
app.get('/api/auth/verify', (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ success: false, message: '未提供认证令牌' });
    }
    
    const token = authHeader.substring(7);
    const session = Array.from(sessions.values()).find(s => s.accessToken === token);
    
    if (!session || new Date(session.expiresAt) < new Date()) {
        return res.status(401).json({ success: false, message: '令牌无效或已过期' });
    }
    
    const user = users.get(session.username);
    if (!user) {
        return res.status(401).json({ success: false, message: '用户不存在' });
    }
    
    res.json({
        success: true,
        data: {
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                role: user.role,
                avatar_url: user.avatar_url
            }
        }
    });
});

// 调试端点 - 查看当前验证码
app.get('/api/debug/captcha', (req, res) => {
    const captchaList = Array.from(captchaStore.entries()).map(([id, text]) => ({
        id,
        text,
        preview: text.toUpperCase()
    }));
    res.json({
        success: true,
        data: {
            captchaCount: captchaStore.size,
            captchas: captchaList
        }
    });
});

// CSRF令牌端点
app.get('/api/csrf-token', (req, res) => {
    const token = crypto.randomBytes(32).toString('hex');
    res.json({
        success: true,
        data: {
            csrfToken: token,
            expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString() // 1小时后过期
        }
    });
});

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        version: '1.0.0-simple',
        service: 'login-api'
    });
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`\n🔐 简化登录API服务器已启动`);
    console.log(`📍 服务地址: http://localhost:${PORT}`);
    console.log(`👤 测试账户:`);
    console.log(`   • admin / admin123`);
    console.log(`   • user / user123`);
    console.log(`\n📡 API端点:`);
    console.log(`   • 健康检查: http://localhost:${PORT}/api/health`);
    console.log(`   • 获取验证码: http://localhost:${PORT}/api/captcha`);
    console.log(`   • 用户登录: http://localhost:${PORT}/api/login`);
    console.log(`   • 验证令牌: http://localhost:${PORT}/api/auth/verify`);
    console.log(`\n✅ 系统已就绪，可以开始测试登录功能！`);
});
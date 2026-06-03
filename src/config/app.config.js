// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 应用配置文件
 * 统一管理应用配置
 */
;
const path = require('path');
;
module.exports = {
    // 应用基本配置
    app: {
        name: 'MTSCOS AI Project',
        version: '1.20260128.0935',
        description: 'MTSCOS AI 项目管理系统 - 云端AI增强版'
    },
    
    // 服务器配置
    server: {
        port: process.env.PORT || 8080,
        host: process.env.HOST || 'localhost',
        environment: process.env.NODE_ENV || 'development'
    },
    
    // 数据库配置
    database: {
        type: 'sqlite',
        path: path.join(__dirname, '../../data/database.db'),
        pool: {
            max: 10,
            min: 0,
            acquire: 30000,
            idle: 10000
        }
    },
    
    // 安全配置
    security: {
        jwt: {
            secret: process.env.JWT_SECRET || 'your-secret-key',
            expiresIn: '24h'
        },
        bcrypt: {
            saltRounds: 10
        },
        rateLimit: {
            windowMs: 15 * 60 * 1000, // 15分钟
            max: 100 // 每个IP限制100个请求
        },
        encryptionKey: process.env.SECURITY_KEY || 'default_security_key_change_in_production'
    },
    
    // CORS配置
    cors: {
        origin: '*',
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-CSRF-Token'],
        credentials: true
    },
    
    // 日志配置
    logging: {
        level: process.env.LOG_LEVEL || 'info',
        dir: path.join(__dirname, '../../Logs')
    },
    
    // 文件存储配置
    storage: {
        dir: path.join(__dirname, '../../storage'),
        maxFileSize: 10 * 1024 * 1024, // 10MB
        allowedExtensions: ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']
    },
    
    // 监控配置
    monitoring: {
        enabled: true,
        errorThreshold: 10,
        performanceThreshold: 500 // 毫秒
    },
    
    // 防火墙配置
    firewall: require('./firewall.config'),

    // 会话配置
    session: {
        secret: process.env.SESSION_SECRET || 'mtscos-ai-session-secret-key-2026',
        cookie: {
            maxAge: 3600000 // 1小时
        }
    },
    
    // 日语测试系统配置
    jptest: {
        questionBankSize: 10000,
        testDuration: 60, // 分钟
        levels: ['N1', 'N2', 'N3', 'N4', 'N5']
    }
};
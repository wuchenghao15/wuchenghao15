module.exports = {
    // 服务器配置
    server: {
        port: process.env.PORT || 3001,
        host: process.env.HOST || 'localhost',
        env: process.env.NODE_ENV || 'development'
    },

    // 数据库配置
    database: {
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        name: process.env.DB_NAME || 'mtscos_login',
        charset: 'utf8mb4',
        timezone: '+08:00',
        connectionLimit: parseInt(process.env.DB_CONNECTION_LIMIT) || 20,
        queueLimit: parseInt(process.env.DB_QUEUE_LIMIT) || 0,
        acquireTimeout: parseInt(process.env.DB_ACQUIRE_TIMEOUT) || 60000,
        timeout: parseInt(process.env.DB_TIMEOUT) || 60000
    },

    // Redis配置
    redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379,
        password: process.env.REDIS_PASSWORD || '',
        db: parseInt(process.env.REDIS_DB) || 0,
        keyPrefix: process.env.REDIS_KEY_PREFIX || 'mtscos:',
        ttl: {
            captcha: parseInt(process.env.REDIS_CAPTCHA_TTL) || 300, // 验证码5分钟
            session: parseInt(process.env.REDIS_SESSION_TTL) || 86400, // 会话24小时
            loginAttempt: parseInt(process.env.REDIS_LOGIN_ATTEMPT_TTL) || 3600 // 登录尝试记录1小时
        }
    },

    // JWT配置
    jwt: {
        secret: process.env.JWT_SECRET || 'mtscos-login-jwt-secret-key-2024',
        expiresIn: process.env.JWT_EXPIRES_IN || '24h',
        issuer: process.env.JWT_ISSUER || 'mtscos-login-system',
        audience: process.env.JWT_AUDIENCE || 'mtscos-users'
    },

    // 密码安全配置
    password: {
        minLength: parseInt(process.env.PASSWORD_MIN_LENGTH) || 8,
        maxLength: parseInt(process.env.PASSWORD_MAX_LENGTH) || 128,
        requireUppercase: process.env.PASSWORD_REQUIRE_UPPERCASE !== 'false',
        requireLowercase: process.env.PASSWORD_REQUIRE_LOWERCASE !== 'false',
        requireNumbers: process.env.PASSWORD_REQUIRE_NUMBERS !== 'false',
        requireSpecialChars: process.env.PASSWORD_REQUIRE_SPECIAL !== 'false',
        saltRounds: parseInt(process.env.PASSWORD_SALT_ROUNDS) || 12
    },

    // 登录安全配置
    security: {
        maxLoginAttempts: parseInt(process.env.MAX_LOGIN_ATTEMPTS) || 5,
        lockoutDuration: parseInt(process.env.LOCKOUT_DURATION) || 30, // 分钟
        sessionTimeout: parseInt(process.env.SESSION_TIMEOUT) || 24, // 小时
        captchaEnabled: process.env.CAPTCHA_ENABLED !== 'false',
        captchaLength: parseInt(process.env.CAPTCHA_LENGTH) || 6,
        ipWhitelist: process.env.IP_WHITELIST ? process.env.IP_WHITELIST.split(',') : [],
        ipBlacklist: process.env.IP_BLACKLIST ? process.env.IP_BLACKLIST.split(',') : []
    },

    // 限流配置
    rateLimit: {
        windowMs: parseInt(process.env.RATE_LIMIT_WINDOW) || 900000, // 15分钟
        max: parseInt(process.env.RATE_LIMIT_MAX) || 100, // 最大请求数
        message: {
            error: '请求过于频繁，请稍后再试',
            code: 'RATE_LIMIT_EXCEEDED'
        },
        standardHeaders: true,
        legacyHeaders: false
    },

    // CORS配置
    cors: {
        origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : ['http://localhost:8000', 'http://127.0.0.1:8000'],
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
        credentials: true,
        optionsSuccessStatus: 204
    },

    // 第三方登录配置
    oauth: {
        // GitHub OAuth
        github: {
            clientId: process.env.GITHUB_CLIENT_ID || '',
            clientSecret: process.env.GITHUB_CLIENT_SECRET || '',
            redirectUri: process.env.GITHUB_REDIRECT_URI || 'http://localhost:3001/auth/github/callback',
            scope: 'user:email'
        },

        // Google OAuth
        google: {
            clientId: process.env.GOOGLE_CLIENT_ID || '',
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
            redirectUri: process.env.GOOGLE_REDIRECT_URI || 'http://localhost:3001/auth/google/callback',
            scope: ['openid', 'email', 'profile']
        },

        // 微信OAuth
        wechat: {
            appId: process.env.WECHAT_APP_ID || '',
            appSecret: process.env.WECHAT_APP_SECRET || '',
            redirectUri: process.env.WECHAT_REDIRECT_URI || 'http://localhost:3001/auth/wechat/callback',
            scope: 'snsapi_login'
        },

        // QQ OAuth
        qq: {
            appId: process.env.QQ_APP_ID || '',
            appKey: process.env.QQ_APP_KEY || '',
            redirectUri: process.env.QQ_REDIRECT_URI || 'http://localhost:3001/auth/qq/callback',
            scope: 'get_user_info'
        },

        // 支付宝OAuth
        alipay: {
            appId: process.env.ALIPAY_APP_ID || '',
            privateKey: process.env.ALIPAY_PRIVATE_KEY || '',
            publicKey: process.env.ALIPAY_PUBLIC_KEY || '',
            redirectUri: process.env.ALIPAY_REDIRECT_URI || 'http://localhost:3001/auth/alipay/callback',
            scope: 'auth_user'
        }
    },

    // 邮件配置
    email: {
        host: process.env.EMAIL_HOST || 'smtp.gmail.com',
        port: parseInt(process.env.EMAIL_PORT) || 587,
        secure: process.env.EMAIL_SECURE === 'true', // true for 465, false for other ports
        auth: {
            user: process.env.EMAIL_USER || '',
            pass: process.env.EMAIL_PASS || ''
        },
        from: process.env.EMAIL_FROM || 'noreply@mtscos.com'
    },

    // 短信配置
    sms: {
        provider: process.env.SMS_PROVIDER || 'aliyun', // aliyun, tencent
        accessKeyId: process.env.SMS_ACCESS_KEY_ID || '',
        accessKeySecret: process.env.SMS_ACCESS_KEY_SECRET || '',
        signName: process.env.SMS_SIGN_NAME || 'MTSCOS',
        templateCode: process.env.SMS_TEMPLATE_CODE || ''
    },

    // 文件上传配置
    upload: {
        maxFileSize: parseInt(process.env.UPLOAD_MAX_FILE_SIZE) || 5 * 1024 * 1024, // 5MB
        allowedTypes: process.env.UPLOAD_ALLOWED_TYPES ? process.env.UPLOAD_ALLOWED_TYPES.split(',') : ['image/jpeg', 'image/png', 'image/gif'],
        destination: process.env.UPLOAD_DESTINATION || './uploads/',
        baseUrl: process.env.UPLOAD_BASE_URL || '/uploads/'
    },

    // 日志配置
    logging: {
        level: process.env.LOG_LEVEL || 'info',
        format: process.env.LOG_FORMAT || 'combined',
        file: {
            enabled: process.env.LOG_FILE_ENABLED !== 'false',
            filename: process.env.LOG_FILENAME || 'logs/app.log',
            maxSize: process.env.LOG_MAX_SIZE || '10m',
            maxFiles: parseInt(process.env.LOG_MAX_FILES) || 5
        },
        console: {
            enabled: process.env.LOG_CONSOLE_ENABLED !== 'false',
            colorize: process.env.LOG_CONSOLE_COLORIZE !== 'false'
        }
    },

    // 监控配置
    monitoring: {
        enabled: process.env.MONITORING_ENABLED !== 'false',
        metricsPath: process.env.METRICS_PATH || '/metrics',
        healthCheckPath: process.env.HEALTH_CHECK_PATH || '/health',
        performance: {
            enabled: process.env.PERFORMANCE_MONITORING_ENABLED !== 'false',
            sampleRate: parseFloat(process.env.PERFORMANCE_SAMPLE_RATE) || 0.1
        }
    },

    // 缓存配置
    cache: {
        enabled: process.env.CACHE_ENABLED !== 'false',
        ttl: parseInt(process.env.CACHE_TTL) || 300, // 5分钟
        maxSize: parseInt(process.env.CACHE_MAX_SIZE) || 1000
    },

    // API配置
    api: {
        version: process.env.API_VERSION || 'v1',
        prefix: process.env.API_PREFIX || '/api',
        timeout: parseInt(process.env.API_TIMEOUT) || 30000,
        retries: parseInt(process.env.API_RETRIES) || 3
    }
};
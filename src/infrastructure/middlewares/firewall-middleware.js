// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 防火墙中间件
 * 提供请求过滤、访问控制和安全保护
 */

const fs = require('fs');
const path = require('path');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const csrf = require('csurf');
const firewallConfig = require('../../config/firewall.config');

class FirewallMiddleware {
    constructor() {
        this.config = firewallConfig;
        this.ensureDirectories();
        this.initializeRules();
    }
    
    /**
     * 确保必要的目录存在
     */
    ensureDirectories() {
        const logDir = this.config.monitoring.logging.logDir;
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }
    
    /**
     * 初始化防火墙规则
     */
    initializeRules() {
        // 初始化速率限制
        this.rateLimiter = rateLimit({
            windowMs: this.config.network.rateLimit.windowMs,
            max: this.config.network.rateLimit.max,
            message: this.config.network.rateLimit.message,
            standardHeaders: true,
            legacyHeaders: false
        });
        
        // 初始化CSRF保护
        this.csrfProtection = csrf({
            cookie: {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production'
            }
        });
    }
    
    /**
     * IP访问控制中间件
     */
    ipAccessControl() {
        return (req, res, next) => {
            // 检查当前环境
            const environment = process.env.NODE_ENV || 'development';
            
            // 开发环境跳过IP检查
            if (environment === 'development') {
                return next();
            }
            
            const clientIP = req.ip || req.connection.remoteAddress;
            
            // 检查是否在阻止列表中
            if (this.isBlockedIP(clientIP)) {
                return res.status(403).json({
                    success: false,
                    message: 'Access denied: IP address is blocked'
                });
            }
            
            // 检查是否在允许列表中
            if (!this.isAllowedIP(clientIP)) {
                return res.status(403).json({
                    success: false,
                    message: 'Access denied: IP address not allowed'
                });
            }
            
            next();
        };
    }
    
    /**
     * 检查IP是否被阻止
     */
    isBlockedIP(ip) {
        const blockedIPs = this.config.network.blockedIPs;
        return blockedIPs.some(blockedIP => this.checkIPMatch(ip, blockedIP));
    }
    
    /**
     * 检查IP是否被允许
     */
    isAllowedIP(ip) {
        const allowedIPs = this.config.network.allowedIPs;
        return allowedIPs.some(allowedIP => this.checkIPMatch(ip, allowedIP));
    }
    
    /**
     * 检查IP是否匹配规则
     */
    checkIPMatch(ip, rule) {
        // 处理CIDR范围
        if (rule.includes('/')) {
            const [range, prefix] = rule.split('/');
            const ipInt = this.ipToInt(ip);
            const rangeInt = this.ipToInt(range);
            const mask = (0xffffffff << (32 - parseInt(prefix))) & 0xffffffff;
            return (ipInt & mask) === (rangeInt & mask);
        }
        // 处理精确匹配
        return ip === rule;
    }
    
    /**
     * IP地址转整数
     */
    ipToInt(ip) {
        return ip.split('.').reduce((acc, octet) => (acc << 8) + parseInt(octet), 0) >>> 0;
    }
    
    /**
     * 输入验证中间件
     */
    inputValidation() {
        return (req, res, next) => {
            if (!this.config.security.inputValidation.enabled) {
                return next();
            }
            
            // 检查请求体大小
            const contentLength = req.headers['content-length'];
            if (contentLength && parseInt(contentLength) > this.config.security.inputValidation.maxInputLength) {
                return res.status(413).json({
                    success: false,
                    message: 'Request body too large'
                });
            }
            
            next();
        };
    }
    
    /**
     * 安全头部中间件
     */
    securityHeaders() {
        return helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    scriptSrc: ["'self'", "'unsafe-inline'"],
                    styleSrc: ["'self'", "'unsafe-inline'"],
                    imgSrc: ["'self'", "data:"],
                    connectSrc: ["'self'"]
                }
            },
            crossOriginEmbedderPolicy: true,
            crossOriginOpenerPolicy: true,
            crossOriginResourcePolicy: true,
            dnsPrefetchControl: true,
            expectCt: true,
            frameguard: true,
            hidePoweredBy: true,
            hsts: true,
            ieNoOpen: true,
            noSniff: true,
            originAgentCluster: true,
            permittedCrossDomainPolicies: true,
            referrerPolicy: true,
            xssFilter: true
        });
    }
    
    /**
     * API访问控制中间件
     */
    apiAccessControl() {
        return (req, res, next) => {
            const serviceConfig = this.config.services.api;
            
            // 检查HTTP方法
            if (serviceConfig.allowedMethods && !serviceConfig.allowedMethods.includes(req.method)) {
                return res.status(405).json({
                    success: false,
                    message: 'Method not allowed'
                });
            }
            
            next();
        };
    }
    
    /**
     * 管理界面访问控制中间件
     */
    adminAccessControl() {
        return (req, res, next) => {
            const serviceConfig = this.config.services.admin;
            
            // 检查认证
            if (serviceConfig.requireAuth && !req.session.user) {
                return res.status(401).json({
                    success: false,
                    message: 'Authentication required'
                });
            }
            
            // 检查管理员权限
            if (serviceConfig.requireAdmin && (!req.session.user || !req.session.user.isAdmin)) {
                return res.status(403).json({
                    success: false,
                    message: 'Admin access required'
                });
            }
            
            next();
        };
    }
    
    /**
     * 文件上传访问控制中间件
     */
    uploadAccessControl() {
        return (req, res, next) => {
            const serviceConfig = this.config.services.upload;
            
            // 检查认证
            if (serviceConfig.requireAuth && !req.session.user) {
                return res.status(401).json({
                    success: false,
                    message: 'Authentication required'
                });
            }
            
            next();
        };
    }
    
    /**
     * 应用所有防火墙中间件
     */
    applyAll(app) {
        // 应用安全头部
        app.use(this.securityHeaders());
        
        // 应用IP访问控制
        app.use(this.ipAccessControl());
        
        // 应用速率限制
        if (this.config.network.rateLimit.enabled) {
            app.use(this.rateLimiter);
        }
        
        // 应用输入验证
        app.use(this.inputValidation());
        
        // 应用API访问控制
        app.use('/api', this.apiAccessControl());
        
        // 应用管理界面访问控制
        app.use('/admin', this.adminAccessControl());
        
        // 应用文件上传访问控制
        app.use('/upload', this.uploadAccessControl());
        
        // 应用CSRF保护（除了API、静态文件和根路径）
        app.use((req, res, next) => {
            // 跳过API、静态文件路径和根路径的CSRF保护
            if (req.path === '/' || 
                req.path.startsWith('/api') || 
                req.path.startsWith('/html') || 
                req.path.startsWith('/assets') || 
                req.path.startsWith('/JavaScript') || 
                req.path.startsWith('/JS') || 
                req.path.startsWith('/css')) {
                next();
            } else {
                this.csrfProtection(req, res, next);
            }
        });
    }
}

module.exports = new FirewallMiddleware();

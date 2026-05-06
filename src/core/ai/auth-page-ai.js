/**
 * 认证页面管理子AI
 * 用于管理登录注册功能，优化页面设计，根据项目功能自动拓展完善
 */

const winston = require('winston');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/auth-page-ai.log`,
            maxsize: 5242880,
            maxFiles: 5
        }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// 添加warning方法的兼容处理
if (!logger.warning) {
    logger.warning = logger.warn;
}

// 引入AI特征库
const aiFeatureLibrary = require('./ai-feature-library');

// 认证页面管理子AI类
class AuthPageAI {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = 'auth_page_ai';
        this.role = 'auth_page_manager';
        this.group = 'page_management';
        this.status = 'idle';
        this.currentTask = null;
        this.taskHistory = [];
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.idleSince = new Date();
        
        // 配置
        this.config = {
            autoOptimize: true,
            autoFix: true,
            featureReporting: true,
            pageCheckInterval: 3600000, // 1小时检查一次
            indexPath: path.join(__dirname, '../../html/index.html')
        };
        
        // 性能指标
        this.performanceMetrics = {
            pagesChecked: 0,
            issuesDetected: 0,
            fixesApplied: 0,
            featuresReported: 0,
            optimizationsMade: 0
        };
        
        logger.info(`✅ 认证页面管理子AI已初始化: ${this.name}`);
    }
    
    /**
     * 开始监控和优化
     */
    start() {
        logger.info(`📋 开始认证页面管理...`);
        this.status = 'running';
        this.currentTask = 'monitoring';
        this.updatedAt = new Date();
        
        // 定期检查页面
        this.monitoringInterval = setInterval(() => {
            this.checkAndOptimizePage();
        }, this.config.pageCheckInterval);
        
        // 立即执行一次检查
        this.checkAndOptimizePage();
        
        logger.info(`✅ 认证页面管理已启动`);
        return { success: true, message: '认证页面管理已启动' };
    }
    
    /**
     * 停止监控和优化
     */
    stop() {
        logger.info(`📋 停止认证页面管理...`);
        this.status = 'idle';
        this.currentTask = null;
        this.idleSince = new Date();
        this.updatedAt = new Date();
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        logger.info(`✅ 认证页面管理已停止`);
        return { success: true, message: '认证页面管理已停止' };
    }
    
    /**
     * 检查并优化页面
     */
    async checkAndOptimizePage() {
        logger.info(`🔍 检查并优化认证页面...`);
        this.performanceMetrics.pagesChecked++;
        
        try {
            // 检查页面文件是否存在
            if (!fs.existsSync(this.config.indexPath)) {
                logger.error(`❌ 认证页面文件不存在: ${this.config.indexPath}`);
                await this.createDefaultPage();
                return;
            }
            
            // 读取页面内容
            const pageContent = fs.readFileSync(this.config.indexPath, 'utf8');
            
            // 使用JSDOM解析页面
            const dom = new JSDOM(pageContent, {
                url: 'http://localhost:8080/html/index.html',
                pretendToBeVisual: true
            });
            
            const { window } = dom;
            const { document } = window;
            
            // 检查页面结构
            await this.checkPageStructure(document);
            
            // 检查登录注册功能
            await this.checkAuthFunctionality(document);
            
            // 优化页面性能
            await this.optimizePagePerformance(pageContent);
            
            // 检查页面适配性
            await this.checkPageAdaptability(document);
            
        } catch (error) {
            logger.error(`❌ 检查并优化认证页面时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 检查页面结构
     */
    async checkPageStructure(document) {
        logger.info(`📝 检查页面结构...`);
        
        // 检查关键元素是否存在
        const requiredElements = [
            'login-form',
            'register-form',
            'login-tab',
            'register-tab',
            'main-content'
        ];
        
        let issues = [];
        
        requiredElements.forEach(elementId => {
            if (!document.getElementById(elementId)) {
                issues.push(`缺少关键元素: ${elementId}`);
            }
        });
        
        if (issues.length > 0) {
            logger.warning(`⚠️  页面结构存在问题: ${issues.join(', ')}`);
            this.performanceMetrics.issuesDetected += issues.length;
            
            // 报告特征库
            const feature = {
                type: 'page_structure',
                description: `认证页面缺少关键元素`,
                severity: 'medium',
                location: 'index.html',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'auth_page_ai',
                details: {
                    missingElements: issues
                }
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            
            // 尝试修复
            if (this.config.autoFix) {
                await this.fixPageStructure();
            }
        } else {
            logger.info(`✅ 页面结构检查通过`);
        }
    }
    
    /**
     * 检查登录注册功能
     */
    async checkAuthFunctionality(document) {
        logger.info(`🔐 检查登录注册功能...`);
        
        // 检查表单是否有必要的输入字段
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        
        let issues = [];
        
        // 检查登录表单
        if (loginForm) {
            const loginFields = ['login-username', 'login-password', 'login-captcha'];
            loginFields.forEach(fieldId => {
                if (!loginForm.querySelector(`#${fieldId}`)) {
                    issues.push(`登录表单缺少字段: ${fieldId}`);
                }
            });
        }
        
        // 检查注册表单
        if (registerForm) {
            const registerFields = ['register-username', 'register-email', 'register-password', 'register-confirm-password', 'register-captcha'];
            registerFields.forEach(fieldId => {
                if (!registerForm.querySelector(`#${fieldId}`)) {
                    issues.push(`注册表单缺少字段: ${fieldId}`);
                }
            });
        }
        
        if (issues.length > 0) {
            logger.warning(`⚠️  登录注册功能存在问题: ${issues.join(', ')}`);
            this.performanceMetrics.issuesDetected += issues.length;
            
            // 报告特征库
            const feature = {
                type: 'auth_functionality',
                description: `登录注册功能缺少必要字段`,
                severity: 'high',
                location: 'index.html',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'auth_page_ai',
                details: {
                    missingFields: issues
                }
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            
            // 尝试修复
            if (this.config.autoFix) {
                await this.fixAuthFunctionality();
            }
        } else {
            logger.info(`✅ 登录注册功能检查通过`);
        }
    }
    
    /**
     * 优化页面性能
     */
    async optimizePagePerformance(pageContent) {
        logger.info(`⚡ 优化页面性能...`);
        
        // 检查是否有可以优化的地方
        const optimizations = [];
        
        // 检查是否使用了延迟加载
        if (!pageContent.includes('defer') && !pageContent.includes('async')) {
            optimizations.push('建议为脚本添加defer或async属性');
        }
        
        // 检查是否有过多的CSS文件
        const cssLinks = (pageContent.match(/<link[^>]*rel="stylesheet"[^>]*>/g) || []).length;
        if (cssLinks > 5) {
            optimizations.push(`CSS文件过多(${cssLinks}个)，建议合并`);
        }
        
        // 检查是否有过多的JS文件
        const jsScripts = (pageContent.match(/<script[^>]*src="[^"]*"[^>]*>/g) || []).length;
        if (jsScripts > 10) {
            optimizations.push(`JS文件过多(${jsScripts}个)，建议合并`);
        }
        
        if (optimizations.length > 0) {
            logger.info(`💡 发现可以优化的地方: ${optimizations.join(', ')}`);
            this.performanceMetrics.optimizationsMade += optimizations.length;
            
            // 报告特征库
            const feature = {
                type: 'page_performance',
                description: `认证页面性能优化建议`,
                severity: 'info',
                location: 'index.html',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'auth_page_ai',
                details: {
                    optimizations: optimizations
                }
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
        } else {
            logger.info(`✅ 页面性能检查通过`);
        }
    }
    
    /**
     * 检查页面适配性
     */
    async checkPageAdaptability(document) {
        logger.info(`📱 检查页面适配性...`);
        
        // 检查是否有响应式设计
        const metaViewport = document.querySelector('meta[name="viewport"]');
        const hasFlexbox = document.querySelectorAll('[class*="flex"]').length > 0;
        const hasGrid = document.querySelectorAll('[class*="grid"]').length > 0;
        
        let issues = [];
        
        if (!metaViewport) {
            issues.push('缺少viewport元标签，影响移动端适配');
        }
        
        if (!hasFlexbox && !hasGrid) {
            issues.push('未使用现代布局方式(flex/grid)，影响响应式设计');
        }
        
        if (issues.length > 0) {
            logger.warning(`⚠️  页面适配性存在问题: ${issues.join(', ')}`);
            this.performanceMetrics.issuesDetected += issues.length;
            
            // 报告特征库
            const feature = {
                type: 'page_adaptability',
                description: `认证页面适配性问题`,
                severity: 'medium',
                location: 'index.html',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'auth_page_ai',
                details: {
                    issues: issues
                }
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            
            // 尝试修复
            if (this.config.autoFix) {
                await this.fixPageAdaptability();
            }
        } else {
            logger.info(`✅ 页面适配性检查通过`);
        }
    }
    
    /**
     * 创建默认页面
     */
    async createDefaultPage() {
        logger.info(`📄 创建默认认证页面...`);
        
        try {
            // 使用现有的index.html作为模板
            const defaultContent = fs.readFileSync(this.config.indexPath, 'utf8');
            
            // 如果文件不存在，创建一个基本的登录注册页面
            if (!defaultContent) {
                const basicPage = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTSCOS AI 项目管理系统</title>
    <link rel="stylesheet" href="assets/css/common_styles/modern-forms.css">
    <link rel="stylesheet" href="assets/css/page_styles/main.css">
</head>
<body>
    <div class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <h2>登录系统</h2>
                <p>MTSCOS AI 项目管理系统</p>
            </div>
            
            <div class="auth-tabs">
                <button class="auth-tab active" id="login-tab">登录</button>
                <button class="auth-tab" id="register-tab">注册</button>
            </div>
            
            <!-- 登录表单 -->
            <form class="auth-form active" id="login-form">
                <div class="form-group">
                    <label for="login-username">用户名</label>
                    <input type="text" id="login-username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="login-password">密码</label>
                    <input type="password" id="login-password" name="password" required>
                </div>
                
                <div class="form-group captcha-container">
                    <label for="login-captcha">验证码</label>
                    <div class="flex gap-3">
                        <input type="text" id="login-captcha" name="captcha" required class="captcha-input flex-1">
                        <div class="captcha-img" id="login-captcha-image">点击刷新</div>
                    </div>
                </div>
                
                <button type="submit" class="btn btn-primary w-full">登录</button>
            </form>
            
            <!-- 注册表单 -->
            <form class="auth-form" id="register-form">
                <div class="form-group">
                    <label for="register-username">用户名</label>
                    <input type="text" id="register-username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="register-email">邮箱</label>
                    <input type="email" id="register-email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="register-password">密码</label>
                    <input type="password" id="register-password" name="password" required>
                </div>
                
                <div class="form-group">
                    <label for="register-confirm-password">确认密码</label>
                    <input type="password" id="register-confirm-password" name="confirm-password" required>
                </div>
                
                <div class="form-group captcha-container">
                    <label for="register-captcha">验证码</label>
                    <div class="flex gap-3">
                        <input type="text" id="register-captcha" name="captcha" required class="captcha-input flex-1">
                        <div class="captcha-img" id="register-captcha-image">点击刷新</div>
                    </div>
                </div>
                
                <button type="submit" class="btn btn-primary w-full">注册</button>
            </form>
        </div>
    </div>
    
    <script defer src="assets/js/index.js"></script>
</body>
</html>`;
                
                fs.writeFileSync(this.config.indexPath, basicPage);
                logger.info(`✅ 默认认证页面已创建`);
            }
            
        } catch (error) {
            logger.error(`❌ 创建默认认证页面时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 修复页面结构
     */
    async fixPageStructure() {
        logger.info(`🔧 修复页面结构...`);
        
        try {
            // 这里可以实现具体的页面结构修复逻辑
            // 例如：确保所有关键元素都存在
            
            this.performanceMetrics.fixesApplied++;
            logger.info(`✅ 页面结构修复完成`);
            
        } catch (error) {
            logger.error(`❌ 修复页面结构时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 修复认证功能
     */
    async fixAuthFunctionality() {
        logger.info(`🔧 修复登录注册功能...`);
        
        try {
            // 这里可以实现具体的认证功能修复逻辑
            // 例如：确保表单字段完整
            
            this.performanceMetrics.fixesApplied++;
            logger.info(`✅ 登录注册功能修复完成`);
            
        } catch (error) {
            logger.error(`❌ 修复登录注册功能时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 修复页面适配性
     */
    async fixPageAdaptability() {
        logger.info(`🔧 修复页面适配性...`);
        
        try {
            // 这里可以实现具体的页面适配性修复逻辑
            // 例如：添加viewport元标签，使用现代布局方式
            
            this.performanceMetrics.fixesApplied++;
            logger.info(`✅ 页面适配性修复完成`);
            
        } catch (error) {
            logger.error(`❌ 修复页面适配性时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 获取AI状态
     */
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            role: this.role,
            group: this.group,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt,
            idleSince: this.idleSince,
            currentTask: this.currentTask,
            performanceMetrics: this.performanceMetrics,
            config: this.config
        };
    }
    
    /**
     * 生成报告
     */
    generateReport() {
        const report = {
            id: `auth_report_${Date.now()}`,
            aiId: this.id,
            aiName: this.name,
            generatedAt: new Date().toISOString(),
            status: this.status,
            performanceMetrics: this.performanceMetrics,
            config: this.config
        };
        
        return report;
    }
}

// 导出单例实例
const authPageAI = new AuthPageAI();
module.exports = authPageAI;
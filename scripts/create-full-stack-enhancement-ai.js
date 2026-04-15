#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - 全栈功能完善和拓展子AI创建脚本
 * 用于自动完善和拓展前后端各个功能，并上报特征库
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

// 定义项目根目录
const projectRoot = path.join(__dirname, '..');

// 错误特征数据库路径
const errorFeatureDbPath = path.join(projectRoot, 'src', 'data', 'error-feature-db.json');

// 创建AI实例类
class FullStackEnhancementAI {
    constructor() {
        this.id = 'ai_' + crypto.randomBytes(16).toString('hex');
        this.name = '全栈功能完善和拓展AI';
        this.role = 'full_stack_enhancement';
        this.group = 'system_improvement';
        this.type = 'automatic';
        this.level = 'high';
        this.createdAt = new Date().toISOString();
        this.status = 'idle';
        this.features = [];
        this.enhancements = [];
    }

    // 分析系统现有功能
    async analyzeSystemFeatures() {
        console.log('[' + this.name + '] 开始分析系统现有功能...');
        
        // 1. 分析后端功能
        const backendFeatures = this.analyzeBackendFeatures();
        
        // 2. 分析前端功能
        const frontendFeatures = this.analyzeFrontendFeatures();
        
        // 3. 分析API端点
        const apiEndpoints = this.analyzeApiEndpoints();
        
        // 4. 分析数据库结构
        const databaseStructure = this.analyzeDatabaseStructure();
        
        // 5. 分析核心业务逻辑
        const coreBusinessLogic = this.analyzeCoreBusinessLogic();
        
        return {
            backendFeatures,
            frontendFeatures,
            apiEndpoints,
            databaseStructure,
            coreBusinessLogic
        };
    }

    // 分析后端功能
    analyzeBackendFeatures() {
        console.log('[' + this.name + '] 分析后端功能...');
        
        const backendFeatures = {
            controllers: [],
            services: [],
            models: [],
            middlewares: []
        };
        
        // 分析控制器
        const apiControllersDir = path.join(projectRoot, 'src', 'api', 'controllers');
        if (fs.existsSync(apiControllersDir)) {
            const controllerFiles = fs.readdirSync(apiControllersDir);
            controllerFiles.forEach(file => {
                if (file.endsWith('.controller.js')) {
                    backendFeatures.controllers.push(file.replace('.controller.js', ''));
                }
            });
        }
        
        // 分析服务
        const coreServicesDir = path.join(projectRoot, 'src', 'core', 'services');
        if (fs.existsSync(coreServicesDir)) {
            const serviceFiles = fs.readdirSync(coreServicesDir);
            serviceFiles.forEach(file => {
                if (file.endsWith('.js')) {
                    backendFeatures.services.push(file.replace('.js', ''));
                }
            });
        }
        
        return backendFeatures;
    }

    // 分析前端功能
    analyzeFrontendFeatures() {
        console.log('[' + this.name + '] 分析前端功能...');
        
        const frontendFeatures = {
            htmlPages: [],
            jsFiles: [],
            cssFiles: []
        };
        
        // 分析HTML页面
        const htmlDir = path.join(projectRoot, 'src', 'html');
        if (fs.existsSync(htmlDir)) {
            this.traverseHtmlDirectory(htmlDir, frontendFeatures.htmlPages);
        }
        
        // 分析JavaScript文件
        const jsDir = path.join(projectRoot, 'src', 'html', 'assets', 'js');
        if (fs.existsSync(jsDir)) {
            this.traverseDirectory(jsDir, frontendFeatures.jsFiles, '.js');
        }
        
        // 分析CSS文件
        const cssDir = path.join(projectRoot, 'src', 'html', 'assets', 'css');
        if (fs.existsSync(cssDir)) {
            this.traverseDirectory(cssDir, frontendFeatures.cssFiles, '.css');
        }
        
        return frontendFeatures;
    }

    // 遍历目录
    traverseDirectory(dir, resultArray, fileExt) {
        const items = fs.readdirSync(dir);
        
        items.forEach(item => {
            const itemPath = path.join(dir, item);
            const stats = fs.statSync(itemPath);
            
            if (stats.isDirectory()) {
                this.traverseDirectory(itemPath, resultArray, fileExt);
            } else if (path.extname(item) === fileExt) {
                resultArray.push(itemPath.replace(projectRoot, ''));
            }
        });
    }

    // 遍历HTML目录
    traverseHtmlDirectory(dir, htmlPages) {
        const items = fs.readdirSync(dir);
        
        items.forEach(item => {
            const itemPath = path.join(dir, item);
            const stats = fs.statSync(itemPath);
            
            if (stats.isDirectory()) {
                this.traverseHtmlDirectory(itemPath, htmlPages);
            } else if (item.endsWith('.html')) {
                htmlPages.push(itemPath.replace(projectRoot, ''));
            }
        });
    }

    // 分析API端点
    analyzeApiEndpoints() {
        console.log('[' + this.name + '] 分析API端点...');
        
        const apiEndpoints = [];
        const apiControllersDir = path.join(projectRoot, 'src', 'api', 'controllers');
        
        if (fs.existsSync(apiControllersDir)) {
            const controllerFiles = fs.readdirSync(apiControllersDir);
            controllerFiles.forEach(file => {
                if (file.endsWith('.controller.js')) {
                    const filePath = path.join(apiControllersDir, file);
                    const content = fs.readFileSync(filePath, 'utf8');
                    
                    // 简单匹配API路由
                    const routeMatches = content.match(/(get|post|put|delete)\s*\(['"](.*?)['"]/gi);
                    if (routeMatches) {
                        routeMatches.forEach(match => {
                            const parts = match.split(/['"]/);
                            if (parts.length >= 2) {
                                apiEndpoints.push(parts[1]);
                            }
                        });
                    }
                }
            });
        }
        
        // 添加健康检查端点
        apiEndpoints.push('/health');
        
        return apiEndpoints;
    }

    // 分析数据库结构
    analyzeDatabaseStructure() {
        console.log('[' + this.name + '] 分析数据库结构...');
        
        const databaseStructure = {
            tables: [],
            relationships: []
        };
        
        // 简单分析数据库文件
        const dbDir = path.join(projectRoot, 'src', 'database');
        if (fs.existsSync(dbDir)) {
            const dbFiles = fs.readdirSync(dbDir);
            dbFiles.forEach(file => {
                if (file.endsWith('.js')) {
                    databaseStructure.tables.push(file.replace('.js', ''));
                }
            });
        }
        
        return databaseStructure;
    }

    // 分析核心业务逻辑
    analyzeCoreBusinessLogic() {
        console.log('[' + this.name + '] 分析核心业务逻辑...');
        
        const coreBusinessLogic = {
            modules: [],
            services: []
        };
        
        // 分析核心业务模块
        const coreDir = path.join(projectRoot, 'src', 'core');
        if (fs.existsSync(coreDir)) {
            const coreFiles = fs.readdirSync(coreDir);
            coreFiles.forEach(file => {
                if (fs.statSync(path.join(coreDir, file)).isDirectory()) {
                    coreBusinessLogic.modules.push(file);
                }
            });
        }
        
        // 分析业务服务
        const servicesDir = path.join(projectRoot, 'src', 'core', 'services');
        if (fs.existsSync(servicesDir)) {
            const serviceFiles = fs.readdirSync(servicesDir);
            serviceFiles.forEach(file => {
                if (file.endsWith('.js')) {
                    coreBusinessLogic.services.push(file.replace('.js', ''));
                }
            });
        }
        
        return coreBusinessLogic;
    }

    // 生成功能完善和拓展建议
    generateEnhancementSuggestions(systemAnalysis) {
        console.log('[' + this.name + '] 生成功能完善和拓展建议...');
        
        const suggestions = [];
        
        // 后端功能完善建议
        suggestions.push(...this.generateBackendEnhancementSuggestions(systemAnalysis));
        
        // 前端功能完善建议
        suggestions.push(...this.generateFrontendEnhancementSuggestions(systemAnalysis));
        
        // API功能完善建议
        suggestions.push(...this.generateApiEnhancementSuggestions(systemAnalysis));
        
        // 数据库功能完善建议
        suggestions.push(...this.generateDatabaseEnhancementSuggestions(systemAnalysis));
        
        // 核心业务逻辑完善建议
        suggestions.push(...this.generateCoreBusinessEnhancementSuggestions(systemAnalysis));
        
        return suggestions;
    }

    // 生成后端功能完善建议
    generateBackendEnhancementSuggestions(systemAnalysis) {
        const suggestions = [];
        
        // 1. 检查是否缺少用户认证增强
        if (!fs.existsSync(path.join(projectRoot, 'src', 'core', 'auth', 'enhanced-auth.js'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'backend',
                name: '添加增强型用户认证',
                description: '为系统添加增强型用户认证功能，包括JWT刷新机制和角色权限管理',
                severity: 'high',
                priority: 'high',
                target: 'src/core/auth/enhanced-auth.js',
                implementation: 'addEnhancedAuth'
            });
        }
        
        // 2. 检查是否缺少API文档生成
        if (!fs.existsSync(path.join(projectRoot, 'src', 'core', 'api-documentation.js'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'backend',
                name: '添加API文档自动生成',
                description: '为系统添加API文档自动生成功能，基于代码注释生成Swagger文档',
                severity: 'medium',
                priority: 'medium',
                target: 'src/core/api-documentation.js',
                implementation: 'addApiDocumentation'
            });
        }
        
        // 3. 检查是否缺少请求日志中间件
        const appPath = path.join(projectRoot, 'src', 'app.js');
        const appContent = fs.readFileSync(appPath, 'utf8');
        if (!appContent.includes('requestLogger')) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'backend',
                name: '添加请求日志中间件',
                description: '为系统添加请求日志中间件，记录所有API请求的详细信息',
                severity: 'medium',
                priority: 'medium',
                target: 'src/core/middleware/request-logger.js',
                implementation: 'addRequestLoggerMiddleware'
            });
        }
        
        return suggestions;
    }

    // 生成前端功能完善建议
    generateFrontendEnhancementSuggestions(systemAnalysis) {
        const suggestions = [];
        
        // 1. 检查是否缺少前端组件库
        if (!fs.existsSync(path.join(projectRoot, 'src', 'html', 'assets', 'js', 'components'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'frontend',
                name: '添加前端组件库',
                description: '为系统添加前端组件库，包含常用UI组件，提高前端开发效率',
                severity: 'medium',
                priority: 'medium',
                target: 'src/html/assets/js/components',
                implementation: 'addFrontendComponentLibrary'
            });
        }
        
        // 2. 检查是否缺少前端路由管理
        if (!systemAnalysis.frontendFeatures.jsFiles.some(file => file.includes('router'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'frontend',
                name: '添加前端路由管理',
                description: '为系统添加前端路由管理功能，实现单页应用体验',
                severity: 'medium',
                priority: 'medium',
                target: 'src/html/assets/js/router.js',
                implementation: 'addFrontendRouter'
            });
        }
        
        // 3. 检查是否缺少前端状态管理
        if (!systemAnalysis.frontendFeatures.jsFiles.some(file => file.includes('store') || file.includes('state'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'frontend',
                name: '添加前端状态管理',
                description: '为系统添加前端状态管理功能，统一管理应用状态',
                severity: 'medium',
                priority: 'medium',
                target: 'src/html/assets/js/store.js',
                implementation: 'addFrontendStateManagement'
            });
        }
        
        return suggestions;
    }

    // 生成API功能完善建议
    generateApiEnhancementSuggestions(systemAnalysis) {
        const suggestions = [];
        
        // 1. 检查是否缺少API版本控制
        if (!fs.existsSync(path.join(projectRoot, 'src', 'api', 'v1'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'api',
                name: '添加API版本控制',
                description: '为系统API添加版本控制，支持多个API版本共存',
                severity: 'high',
                priority: 'high',
                target: 'src/api/v1',
                implementation: 'addApiVersioning'
            });
        }
        
        // 2. 检查是否缺少API响应统一格式化
        if (!fs.existsSync(path.join(projectRoot, 'src', 'core', 'middleware', 'response-formatter.js'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'api',
                name: '添加API响应统一格式化',
                description: '为系统API添加统一的响应格式化中间件，确保API响应格式一致',
                severity: 'high',
                priority: 'high',
                target: 'src/core/middleware/response-formatter.js',
                implementation: 'addResponseFormatter'
            });
        }
        
        // 3. 检查是否缺少API批量处理支持
        if (!systemAnalysis.apiEndpoints.some(endpoint => endpoint.includes('batch'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'api',
                name: '添加API批量处理支持',
                description: '为系统API添加批量处理支持，提高API调用效率',
                severity: 'medium',
                priority: 'medium',
                target: 'src/api/controllers/batch.controller.js',
                implementation: 'addApiBatchProcessing'
            });
        }
        
        return suggestions;
    }

    // 生成数据库功能完善建议
    generateDatabaseEnhancementSuggestions(systemAnalysis) {
        const suggestions = [];
        
        // 1. 检查是否缺少数据库迁移工具
        if (!fs.existsSync(path.join(projectRoot, 'src', 'database', 'migrations'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'database',
                name: '添加数据库迁移工具',
                description: '为系统添加数据库迁移工具，支持数据库结构的版本控制和迁移',
                severity: 'high',
                priority: 'medium',
                target: 'src/database/migrations',
                implementation: 'addDatabaseMigrations'
            });
        }
        
        // 2. 检查是否缺少数据库索引优化
        if (!fs.existsSync(path.join(projectRoot, 'src', 'database', 'index-optimization.js'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'database',
                name: '添加数据库索引优化',
                description: '为系统数据库添加索引优化，提高查询性能',
                severity: 'medium',
                priority: 'medium',
                target: 'src/database/index-optimization.js',
                implementation: 'addDatabaseIndexOptimization'
            });
        }
        
        return suggestions;
    }

    // 生成核心业务逻辑完善建议
    generateCoreBusinessEnhancementSuggestions(systemAnalysis) {
        const suggestions = [];
        
        // 1. 检查是否缺少业务规则引擎
        if (!fs.existsSync(path.join(projectRoot, 'src', 'core', 'business-rule-engine.js'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'business',
                name: '添加业务规则引擎',
                description: '为系统添加业务规则引擎，支持动态配置业务规则',
                severity: 'medium',
                priority: 'medium',
                target: 'src/core/business-rule-engine.js',
                implementation: 'addBusinessRuleEngine'
            });
        }
        
        // 2. 检查是否缺少事件驱动架构支持
        if (!fs.existsSync(path.join(projectRoot, 'src', 'core', 'event-bus.js'))) {
            suggestions.push({
                id: 'suggestion_' + crypto.randomBytes(8).toString('hex'),
                type: 'business',
                name: '添加事件驱动架构支持',
                description: '为系统添加事件驱动架构支持，实现组件间的松耦合通信',
                severity: 'medium',
                priority: 'medium',
                target: 'src/core/event-bus.js',
                implementation: 'addEventBus'
            });
        }
        
        return suggestions;
    }

    // 实现功能完善和拓展
    async implementEnhancements(suggestions) {
        console.log('[' + this.name + '] 开始实现功能完善和拓展...');
        
        const implementedEnhancements = [];
        
        for (const suggestion of suggestions) {
            try {
                console.log('[' + this.name + '] 实现建议: ' + suggestion.name);
                
                // 根据建议类型实现不同的功能
                switch (suggestion.implementation) {
                    case 'addEnhancedAuth':
                        await this.addEnhancedAuth(suggestion);
                        break;
                    case 'addApiDocumentation':
                        await this.addApiDocumentation(suggestion);
                        break;
                    case 'addRequestLoggerMiddleware':
                        await this.addRequestLoggerMiddleware(suggestion);
                        break;
                    case 'addFrontendComponentLibrary':
                        await this.addFrontendComponentLibrary(suggestion);
                        break;
                    case 'addFrontendRouter':
                        await this.addFrontendRouter(suggestion);
                        break;
                    case 'addFrontendStateManagement':
                        await this.addFrontendStateManagement(suggestion);
                        break;
                    case 'addApiVersioning':
                        await this.addApiVersioning(suggestion);
                        break;
                    case 'addResponseFormatter':
                        await this.addResponseFormatter(suggestion);
                        break;
                    case 'addApiBatchProcessing':
                        await this.addApiBatchProcessing(suggestion);
                        break;
                    case 'addDatabaseMigrations':
                        await this.addDatabaseMigrations(suggestion);
                        break;
                    case 'addDatabaseIndexOptimization':
                        await this.addDatabaseIndexOptimization(suggestion);
                        break;
                    case 'addBusinessRuleEngine':
                        await this.addBusinessRuleEngine(suggestion);
                        break;
                    case 'addEventBus':
                        await this.addEventBus(suggestion);
                        break;
                }
                
                implementedEnhancements.push({
                    ...suggestion,
                    status: 'completed',
                    timestamp: new Date().toISOString()
                });
                
            } catch (error) {
                console.error('[' + this.name + '] 实现建议 ' + suggestion.name + ' 失败:', error.message);
                implementedEnhancements.push({
                    ...suggestion,
                    status: 'failed',
                    timestamp: new Date().toISOString(),
                    error: error.message
                });
            }
        }
        
        this.enhancements = implementedEnhancements;
        return implementedEnhancements;
    }

    // 添加增强型用户认证
    async addEnhancedAuth(suggestion) {
        const authDir = path.join(projectRoot, 'src', 'core', 'auth');
        fs.mkdirSync(authDir, { recursive: true });
        
        const authPath = path.join(projectRoot, suggestion.target);
        const authContent = '/**\n * MTSCOS AI 系统 - 增强型用户认证模块\n * 用于提供增强型用户认证功能，包括JWT刷新机制和角色权限管理\n */\n\nconst jwt = require(\'jsonwebtoken\');\nconst crypto = require(\'crypto\');\n\nclass EnhancedAuth {\n    constructor() {\n        this.secretKey = process.env.JWT_SECRET || \'mtscos-ai-secret-key\';\n        this.refreshSecretKey = process.env.JWT_REFRESH_SECRET || \'mtscos-ai-refresh-secret-key\';\n        this.accessTokenExpiry = process.env.JWT_ACCESS_EXPIRY || \'15m\';\n        this.refreshTokenExpiry = process.env.JWT_REFRESH_EXPIRY || \'7d\';\n    }\n    \n    // 生成访问令牌\n    generateAccessToken(user) {\n        const payload = {\n            userId: user.id,\n            username: user.username,\n            role: user.role || \'user\',\n            type: \'access\'\n        };\n        \n        return jwt.sign(payload, this.secretKey, { expiresIn: this.accessTokenExpiry });\n    }\n    \n    // 生成刷新令牌\n    generateRefreshToken(user) {\n        const payload = {\n            userId: user.id,\n            type: \'refresh\',\n            jti: crypto.randomBytes(32).toString(\'hex\')\n        };\n        \n        return jwt.sign(payload, this.refreshSecretKey, { expiresIn: this.refreshTokenExpiry });\n    }\n    \n    // 验证访问令牌\n    verifyAccessToken(token) {\n        try {\n            return jwt.verify(token, this.secretKey);\n        } catch (error) {\n            throw new Error(\'无效的访问令牌\');\n        }\n    }\n    \n    // 验证刷新令牌\n    verifyRefreshToken(token) {\n        try {\n            return jwt.verify(token, this.refreshSecretKey);\n        } catch (error) {\n            throw new Error(\'无效的刷新令牌\');\n        }\n    }\n    \n    // 刷新访问令牌\n    refreshAccessToken(refreshToken) {\n        const payload = this.verifyRefreshToken(refreshToken);\n        \n        // 这里应该从数据库或缓存中获取用户信息\n        // 简化实现，直接从refresh token中提取userId\n        const user = { id: payload.userId, role: \'user\' };\n        \n        return {\n            accessToken: this.generateAccessToken(user),\n            refreshToken: this.generateRefreshToken(user)\n        };\n    }\n    \n    // 检查用户权限\n    checkPermission(user, requiredPermission) {\n        const rolePermissions = {\n            admin: [\'read\', \'write\', \'delete\', \'admin\'],\n            user: [\'read\', \'write\'],\n            guest: [\'read\']\n        };\n        \n        const permissions = rolePermissions[user.role] || [];\n        return permissions.includes(requiredPermission);\n    }\n    \n    // 权限检查中间件\n    requirePermission(permission) {\n        return (req, res, next) => {\n            const user = req.user;\n            if (!user) {\n                return res.status(401).json({ status: \'error\', message: \'未认证\' });\n            }\n            \n            if (!this.checkPermission(user, permission)) {\n                return res.status(403).json({ status: \'error\', message: \'权限不足\' });\n            }\n            \n            next();\n        };\n    }\n}\n\nmodule.exports = new EnhancedAuth();\n';
        
        fs.writeFileSync(authPath, authContent);
        console.log('[' + this.name + '] 增强型用户认证已添加: ' + authPath);
    }

    // 添加API文档自动生成
    async addApiDocumentation(suggestion) {
        const apiDocPath = path.join(projectRoot, suggestion.target);
        const apiDocContent = '/**\n * MTSCOS AI 系统 - API文档生成模块\n * 用于基于代码注释生成Swagger文档\n */\n\nconst swaggerJsdoc = require(\'swagger-jsdoc\');\nconst swaggerUi = require(\'swagger-ui-express\');\n\nclass ApiDocumentation {\n    constructor() {\n        this.options = {\n            definition: {\n                openapi: \'3.0.0\',\n                info: {\n                    title: \'MTSCOS AI 系统 API\',\n                    version: \'1.0.0\',\n                    description: \'MTSCOS AI 系统的API文档\'\n                },\n                servers: [\n                    {\n                        url: \'http://localhost:8080\',\n                        description: \'本地开发服务器\'\n                    },\n                    {\n                        url: \'https://localhost:8433\',\n                        description: \'本地HTTPS服务器\'\n                    }\n                ]\n            },\n            apis: [\n                path.join(__dirname, \'..\', \'api\', \'**\', \'*.js\'),\n                path.join(__dirname, \'..\', \'app.js\')\n            ]\n        };
    }\n    \n    // 初始化Swagger文档\n    initialize(app) {\n        const specs = swaggerJsdoc(this.options);\n        \n        // 设置Swagger UI路由\n        app.use(\'/api-docs\', swaggerUi.serve, swaggerUi.setup(specs));\n        \n        console.log(\'[ApiDocumentation] Swagger文档已初始化，访问地址: /api-docs\');\n    }\n}\n\nmodule.exports = new ApiDocumentation();\n';
        
        fs.writeFileSync(apiDocPath, apiDocContent);
        console.log('[' + this.name + '] API文档自动生成已添加: ' + apiDocPath);
        
        // 更新app.js，添加API文档初始化
        const appPath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appPath, 'utf8');
        
        // 导入API文档模块
        if (!appContent.includes('const apiDocumentation')) {
            appContent = appContent.replace(
                /const express = require\('express'\);/,
                'const express = require(\'express\');\nconst apiDocumentation = require(\'./core/api-documentation\');'
            );
        }
        
        // 初始化API文档
        if (!appContent.includes('apiDocumentation.initialize')) {
            // 查找app.listen调用，在其之前添加API文档初始化
            const listenMatch = appContent.match(/app\.listen\(([^)]+)\)/);
            if (listenMatch) {
                const listenIndex = appContent.indexOf(listenMatch[0]);
                const beforeListen = appContent.substring(0, listenIndex);
                const afterListen = appContent.substring(listenIndex);
                
                appContent = beforeListen + '\n\n// 初始化API文档\napiDocumentation.initialize(app);\n\n' + afterListen;
            }
        }
        
        fs.writeFileSync(appPath, appContent);
        console.log('[' + this.name + '] 已更新app.js，添加API文档初始化');
    }

    // 添加请求日志中间件
    async addRequestLoggerMiddleware(suggestion) {
        const middlewareDir = path.join(projectRoot, 'src', 'core', 'middleware');
        fs.mkdirSync(middlewareDir, { recursive: true });
        
        const loggerPath = path.join(projectRoot, suggestion.target);
        const loggerContent = '/**\n * MTSCOS AI 系统 - 请求日志中间件\n * 用于记录所有API请求的详细信息\n */\n\nconst logger = require(\'../logger\');\n\n// 请求日志中间件
const requestLogger = (req, res, next) => {
    const start = Date.now();
    const { method, url, ip } = req;
    const userAgent = req.get(\'User-Agent\');\n    \n    // 记录请求开始
    logger.info(\'请求开始\', { method, url, ip, userAgent });
    \n    // 监听响应完成事件
    res.on(\'finish\', () => {
        const duration = Date.now() - start;
        const { statusCode } = res;
        \n        // 记录请求完成
        logger.info(\'请求完成\', { 
            method, 
            url, 
            ip, 
            userAgent, 
            statusCode, 
            duration: duration + \'ms\' 
        });
    });
    \n    next();
};
\nmodule.exports = requestLogger;\n';
        
        fs.writeFileSync(loggerPath, loggerContent);
        console.log('[' + this.name + '] 请求日志中间件已添加: ' + loggerPath);
        
        // 更新app.js，添加请求日志中间件
        const appPath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appPath, 'utf8');
        
        // 导入请求日志中间件
        if (!appContent.includes('const requestLogger')) {
            appContent = appContent.replace(
                /const express = require\('express'\);/,
                'const express = require(\'express\');\nconst requestLogger = require(\'./core/middleware/request-logger\');'
            );
        }
        
        // 使用请求日志中间件
        if (!appContent.includes('app.use(requestLogger)')) {
            // 查找合适的位置添加中间件
            const corsMatch = appContent.match(/app\.use\(cors\(/);
            if (corsMatch) {
                const corsIndex = appContent.indexOf(corsMatch[0]);
                const beforeCors = appContent.substring(0, corsIndex);
                const afterCors = appContent.substring(corsIndex);
                
                appContent = beforeCors + 'app.use(requestLogger);\n' + afterCors;
            } else {
                // 如果没有cors中间件，添加到express实例创建后
                appContent = appContent.replace(
                    /const app = express\(\);/,
                    'const app = express();\n\n// 请求日志中间件\napp.use(requestLogger);'
                );
            }
        }
        
        fs.writeFileSync(appPath, appContent);
        console.log('[' + this.name + '] 已更新app.js，添加请求日志中间件');
    }

    // 添加前端组件库
    async addFrontendComponentLibrary(suggestion) {
        const componentsDir = path.join(projectRoot, suggestion.target);
        fs.mkdirSync(componentsDir, { recursive: true });
        
        // 创建按钮组件
        const buttonComponentPath = path.join(componentsDir, 'Button.js');
        const buttonComponentContent = '/**\n * MTSCOS AI 系统 - 按钮组件\n * 用于创建不同样式的按钮\n */\n\nclass Button {\n    constructor(container, options = {}) {\n        this.container = container;\n        this.options = Object.assign({\n            text: \'Button\',\n            type: \'primary\', // primary, secondary, success, danger, warning\n            size: \'medium\', // small, medium, large\n            disabled: false,\n            onClick: () => {}\n        }, options);\n        \n        this.element = null;\n        this.init();\n    }\n    \n    // 初始化按钮
    init() {
        this.element = document.createElement(\'button\');
        this.element.textContent = this.options.text;
        this.element.className = \'btn btn-\' + this.options.type + \' btn-\' + this.options.size;
        \n        if (this.options.disabled) {
            this.element.disabled = true;
            this.element.classList.add(\'btn-disabled\');
        }
        \n        this.element.addEventListener(\'click\', (e) => {
            if (!this.options.disabled) {
                this.options.onClick(e);
            }
        });\n        \n        this.container.appendChild(this.element);\n    }\n    \n    // 设置按钮文本
    setText(text) {
        this.options.text = text;
        if (this.element) {
            this.element.textContent = text;
        }
    }\n    \n    // 设置按钮状态
    setDisabled(disabled) {
        this.options.disabled = disabled;
        if (this.element) {
            this.element.disabled = disabled;
            if (disabled) {
                this.element.classList.add(\'btn-disabled\');
            } else {
                this.element.classList.remove(\'btn-disabled\');
            }
        }
    }\n    \n    // 销毁按钮
    destroy() {
        if (this.element && this.container.contains(this.element)) {
            this.container.removeChild(this.element);
            this.element = null;
        }
    }\n}\n\n// 导出按钮组件\nif (typeof module !== \'undefined\' && module.exports) {\n    module.exports = Button;\n} else if (typeof window !== \'undefined\') {\n    window.Button = Button;\n}\n';
        fs.writeFileSync(buttonComponentPath, buttonComponentContent);
        
        // 创建卡片组件
        const cardComponentPath = path.join(componentsDir, 'Card.js');
        const cardComponentContent = '/**\n * MTSCOS AI 系统 - 卡片组件\n * 用于创建包含标题、内容和操作的卡片\n */\n\nclass Card {\n    constructor(container, options = {}) {\n        this.container = container;\n        this.options = Object.assign({\n            title: \'Card Title\',\n            content: \'Card Content\',\n            actions: [],\n            footer: \'\'\n        }, options);\n        \n        this.element = null;\n        this.init();\n    }\n    \n    // 初始化卡片
    init() {
        // 创建卡片容器
        this.element = document.createElement(\'div\');
        this.element.className = \'card\';\n        \n        // 创建卡片头部
        if (this.options.title) {
            const header = document.createElement(\'div\');
            header.className = \'card-header\';
            header.textContent = this.options.title;
            this.element.appendChild(header);
        }
        \n        // 创建卡片内容
        const body = document.createElement(\'div\');
        body.className = \'card-body\';
        body.innerHTML = this.options.content;
        this.element.appendChild(body);
        \n        // 创建卡片操作区域
        if (this.options.actions && this.options.actions.length > 0) {
            const actions = document.createElement(\'div\');
            actions.className = \'card-actions\';
            \n            this.options.actions.forEach(action => {
                const button = document.createElement(\'button\');
                button.textContent = action.text;
                button.className = \'btn btn-small btn-\' + (action.type || \'secondary\');
                button.addEventListener(\'click\', action.onClick);
                actions.appendChild(button);
            });
            \n            this.element.appendChild(actions);
        }
        \n        // 创建卡片底部
        if (this.options.footer) {
            const footer = document.createElement(\'div\');
            footer.className = \'card-footer\';
            footer.innerHTML = this.options.footer;
            this.element.appendChild(footer);
        }
        \n        this.container.appendChild(this.element);
    }\n    \n    // 设置卡片内容
    setContent(content) {
        this.options.content = content;
        const body = this.element.querySelector(\'.card-body\');
        if (body) {
            body.innerHTML = content;
        }
    }\n    \n    // 销毁卡片
    destroy() {
        if (this.element && this.container.contains(this.element)) {
            this.container.removeChild(this.element);
            this.element = null;
        }
    }\n}\n\n// 导出卡片组件\nif (typeof module !== \'undefined\' && module.exports) {\n    module.exports = Card;\n} else if (typeof window !== \'undefined\') {\n    window.Card = Card;\n}\n';
        fs.writeFileSync(cardComponentPath, cardComponentContent);
        
        // 创建模态框组件
        const modalComponentPath = path.join(componentsDir, 'Modal.js');
        const modalComponentContent = '/**\n * MTSCOS AI 系统 - 模态框组件\n * 用于创建弹窗模态框\n */\n\nclass Modal {\n    constructor(options = {}) {\n        this.options = Object.assign({\n            title: \'Modal Title\',\n            content: \'Modal Content\',\n            width: \'500px\',\n            showCloseButton: true,\n            onClose: () => {}\n        }, options);\n        \n        this.element = null;
        this.overlay = null;
        this.isVisible = false;
    }\n    \n    // 初始化模态框
    init() {
        // 创建遮罩层
        this.overlay = document.createElement(\'div\');
        this.overlay.className = \'modal-overlay\';
        \n        // 创建模态框容器
        this.element = document.createElement(\'div\');
        this.element.className = \'modal\';
        this.element.style.width = this.options.width;
        \n        // 创建模态框头部
        const header = document.createElement(\'div\');
        header.className = \'modal-header\';
        header.innerHTML = \'<h3>\' + this.options.title + \'</h3>\';
        \n        // 添加关闭按钮
        if (this.options.showCloseButton) {
            const closeButton = document.createElement(\'button\');
            closeButton.className = \'modal-close-btn\';
            closeButton.innerHTML = \'&times;\';
            closeButton.addEventListener(\'click\', () => this.close());
            header.appendChild(closeButton);
        }
        \n        // 创建模态框内容
        const body = document.createElement(\'div\');
        body.className = \'modal-body\';
        body.innerHTML = this.options.content;
        \n        // 组装模态框
        this.element.appendChild(header);
        this.element.appendChild(body);
        this.overlay.appendChild(this.element);
    }\n    \n    // 显示模态框
    show() {
        if (!this.element) {
            this.init();
        }
        \n        document.body.appendChild(this.overlay);
        this.isVisible = true;
        \n        // 添加遮罩层点击事件
        this.overlay.addEventListener(\'click\', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });
        \n        // 添加ESC键关闭事件
        document.addEventListener(\'keydown\', this.handleEscKey);
    }\n    \n    // 关闭模态框
    close() {
        if (this.isVisible && this.overlay && document.body.contains(this.overlay)) {
            document.body.removeChild(this.overlay);
            this.isVisible = false;
            \n            // 移除事件监听
            document.removeEventListener(\'keydown\', this.handleEscKey);
            \n            // 调用关闭回调
            this.options.onClose();
        }
    }\n    \n    // 处理ESC键事件
    handleEscKey = (e) => {
        if (e.key === \'Escape\') {
            this.close();
        }
    }\n    \n    // 设置模态框内容
    setContent(content) {
        this.options.content = content;
        if (this.element) {
            const body = this.element.querySelector(\'.modal-body\');
            if (body) {
                body.innerHTML = content;
            }
        }
    }\n}\n\n// 导出模态框组件\nif (typeof module !== \'undefined\' && module.exports) {\n    module.exports = Modal;\n} else if (typeof window !== \'undefined\') {\n    window.Modal = Modal;\n}\n';
        fs.writeFileSync(modalComponentPath, modalComponentContent);
        
        // 创建组件库入口文件
        const indexPath = path.join(componentsDir, 'index.js');
        const indexContent = '/**\n * MTSCOS AI 系统 - 前端组件库入口\n * 用于导出所有前端组件\n */\n\n// 如果在浏览器环境中\nif (typeof window !== \'undefined\') {\n    // 浏览器环境下不需要导出，组件会挂载到window对象上\n    console.log(\'MTSCOS AI 组件库已加载\');\n} else if (typeof module !== \'undefined\' && module.exports) {\n    // Node.js环境下导出组件\n    module.exports = {\n        Button: require(\'./Button\'),\n        Card: require(\'./Card\'),\n        Modal: require(\'./Modal\')\n    };\n}\n';
        fs.writeFileSync(indexPath, indexContent);
        
        console.log('[' + this.name + '] 前端组件库已添加: ' + componentsDir);
    }

    // 添加前端路由管理
    async addFrontendRouter(suggestion) {
        const routerPath = path.join(projectRoot, suggestion.target);
        const routerContent = '/**\n * MTSCOS AI 系统 - 前端路由管理\n * 用于实现单页应用路由\n */\n\nclass Router {\n    constructor(options = {}) {\n        this.options = Object.assign({\n            mode: \'hash\', // hash, history\n            root: \'/:\',\n            notFound: () => {}
        }, options);\n        \n        this.routes = [];
        this.currentRoute = null;
        this.init();\n    }\n    \n    // 初始化路由
    init() {
        // 监听路由变化
        if (this.options.mode === \'hash\') {
            // hash模式
            window.addEventListener(\'hashchange\', () => this.handleRouteChange());
            window.addEventListener(\'load\', () => this.handleRouteChange());
        } else {
            // history模式
            window.addEventListener(\'popstate\', () => this.handleRouteChange());
            window.addEventListener(\'load\', () => this.handleRouteChange());
        }
    }\n    \n    // 添加路由
    addRoute(path, handler) {
        this.routes.push({ path, handler });
    }\n    \n    // 处理路由变化
    handleRouteChange() {
        const path = this.getPath();
        const route = this.matchRoute(path);
        \n        if (route) {
            this.currentRoute = route;
            route.handler(path);
        } else {
            this.currentRoute = null;
            this.options.notFound(path);
        }
    }\n    \n    // 获取当前路径
    getPath() {
        let path = \'\';
        \n        if (this.options.mode === \'hash\') {
            path = window.location.hash.slice(1) || \'/:\';
        } else {
            path = window.location.pathname || \'/:\';
        }
        \n        return path.startsWith(\'/:\') ? path : \'/' + path;
    }\n    \n    // 匹配路由
    matchRoute(path) {
        // 简单的路径匹配，支持精确匹配和通配符
        for (const route of this.routes) {
            if (route.path === path || route.path === \'*\') {
                return route;
            }
        }
        return null;
    }\n    \n    // 导航到指定路径
    navigate(path) {
        if (this.options.mode === \'hash\') {
            window.location.hash = path;
        } else {
            window.history.pushState(null, \'\', path);
            this.handleRouteChange();
        }
    }\n    \n    // 替换当前路径
    replace(path) {
        if (this.options.mode === \'hash\') {
            window.location.replace(\'#\' + path);
        } else {
            window.history.replaceState(null, \'\', path);
            this.handleRouteChange();
        }
    }\n}\n\n// 导出路由组件\nif (typeof module !== \'undefined\' && module.exports) {\n    module.exports = Router;\n} else if (typeof window !== \'undefined\') {\n    window.Router = Router;\n}\n';
        
        fs.writeFileSync(routerPath, routerContent);
        console.log('[' + this.name + '] 前端路由管理已添加: ' + routerPath);
    }

    // 添加前端状态管理
    async addFrontendStateManagement(suggestion) {
        const storePath = path.join(projectRoot, suggestion.target);
        const storeContent = '/**\n * MTSCOS AI 系统 - 前端状态管理\n * 用于统一管理应用状态\n */\n\nclass Store {\n    constructor(initialState = {}) {
        this.state = initialState;
        this.listeners = [];
    }\n    \n    // 获取状态
    getState() {
        return { ...this.state };
    }\n    \n    // 更新状态
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.notifyListeners();
    }\n    \n    // 重置状态
    resetState() {
        this.state = {};
        this.notifyListeners();
    }\n    \n    // 添加状态监听器
    subscribe(listener) {
        this.listeners.push(listener);
        \n        // 返回取消订阅函数
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }\n    \n    // 通知所有监听器
    notifyListeners() {
        this.listeners.forEach(listener => {
            try {
                listener(this.getState());
            } catch (error) {
                console.error(\'Store listener error:\', error);
            }
        });
    }\n    \n    // 异步更新状态
    async dispatch(action) {
        try {
            // 简单的action处理，支持函数和对象
            if (typeof action === \'function\') {
                await action(this);
            } else if (typeof action === \'object\' && action.type) {
                // 这里可以添加更复杂的reducer逻辑
                this.setState(action.payload || {});
            }
        } catch (error) {
            console.error(\'Store dispatch error:\', error);
        }
    }\n}\n\n// 创建全局store实例
const store = new Store({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    theme: \'light\',
    language: \'zh-CN\'
});\n\n// 导出store
if (typeof module !== \'undefined\' && module.exports) {
    module.exports = store;
} else if (typeof window !== \'undefined\') {
    window.store = store;
}\n';
        
        fs.writeFileSync(storePath, storeContent);
        console.log('[' + this.name + '] 前端状态管理已添加: ' + storePath);
    }

    // 添加API版本控制
    async addApiVersioning(suggestion) {
        const v1Dir = path.join(projectRoot, suggestion.target);
        fs.mkdirSync(v1Dir, { recursive: true });
        
        // 创建v1 API入口文件
        const v1IndexPath = path.join(v1Dir, 'index.js');
        const v1IndexContent = '/**\n * MTSCOS AI 系统 - API v1 入口文件\n */\n\nconst express = require(\'express\');\nconst router = express.Router();\n\n// 导入控制器\nconst jptestController = require(\'../controllers/jptest.controller\');\nconst featureController = require(\'../controllers/feature.controller\');\nconst configController = require(\'../controllers/config.controller\');\nconst userDataController = require(\'../controllers/user-data.controller\');\n\n// 配置路由\nrouter.use(\'/jptest\', jptestController);\nrouter.use(\'/features\', featureController);\nrouter.use(\'/config\', configController);\nrouter.use(\'/user-data\', userDataController);\n\nmodule.exports = router;\n';
        
        fs.writeFileSync(v1IndexPath, v1IndexContent);
        console.log('[' + this.name + '] API版本控制已添加: ' + v1Dir);
        
        // 更新app.js，添加API版本控制
        const appPath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appPath, 'utf8');
        
        // 导入v1 API路由
        if (!appContent.includes('const v1Router')) {
            appContent = appContent.replace(
                /const express = require\('express'\);/,
                'const express = require(\'express\');\nconst v1Router = require(\'./api/v1\');'
            );
        }
        
        // 使用v1 API路由
        if (!appContent.includes('app.use(\'/api/v1\', v1Router)')) {
            // 查找合适的位置添加路由
            const routerMatch = appContent.match(/app\.use\(\/api/);
            if (routerMatch) {
                const routerIndex = appContent.indexOf(routerMatch[0]);
                const beforeRouter = appContent.substring(0, routerIndex);
                const afterRouter = appContent.substring(routerIndex);
                
                appContent = beforeRouter + 'app.use(\'/api/v1\', v1Router);\n' + afterRouter;
            } else {
                // 如果没有其他API路由，添加到express实例创建后
                appContent = appContent.replace(
                    /const app = express\(\);/,
                    'const app = express();\n\n// API v1路由\napp.use(\'/api/v1\', v1Router);'
                );
            }
        }
        
        fs.writeFileSync(appPath, appContent);
        console.log('[' + this.name + '] 已更新app.js，添加API版本控制');
    }

    // 添加API响应统一格式化
    async addResponseFormatter(suggestion) {
        const middlewareDir = path.join(projectRoot, 'src', 'core', 'middleware');
        fs.mkdirSync(middlewareDir, { recursive: true });
        
        const formatterPath = path.join(projectRoot, suggestion.target);
        const formatterContent = '/**\n * MTSCOS AI 系统 - API响应统一格式化中间件\n * 用于确保API响应格式一致\n */\n\n// 成功响应格式化
const successResponse = (res, data = null, message = \'操作成功\', statusCode = 200) => {
    return res.status(statusCode).json({
        status: \'success\',
        message: message,
        data: data,
        timestamp: new Date().toISOString()
    });
};
\n// 错误响应格式化
const errorResponse = (res, message = \'操作失败\', statusCode = 400, error = null) => {
    const response = {
        status: \'error\',
        message: message,
        timestamp: new Date().toISOString()
    };
    
    if (error) {
        response.error = error;
    }
    
    return res.status(statusCode).json(response);
};
\n// 响应格式化中间件
const responseFormatter = (req, res, next) => {
    // 将格式化方法添加到res对象
    res.success = (data, message, statusCode) => successResponse(res, data, message, statusCode);
    res.error = (message, statusCode, error) => errorResponse(res, message, statusCode, error);
    
    next();
};
\nmodule.exports = responseFormatter;\n';
        
        fs.writeFileSync(formatterPath, formatterContent);
        console.log('[' + this.name + '] API响应统一格式化已添加: ' + formatterPath);
        
        // 更新app.js，添加响应格式化中间件
        const appPath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appPath, 'utf8');
        
        // 导入响应格式化中间件
        if (!appContent.includes('const responseFormatter')) {
            appContent = appContent.replace(
                /const express = require\('express'\);/,
                'const express = require(\'express\');\nconst responseFormatter = require(\'./core/middleware/response-formatter\');'
            );
        }
        
        // 使用响应格式化中间件
        if (!appContent.includes('app.use(responseFormatter)')) {
            // 查找bodyParser使用位置，在其后添加响应格式化中间件
            const bodyParserMatch = appContent.match(/app\.use\(bodyParser\./);
            if (bodyParserMatch) {
                const bodyParserIndex = appContent.lastIndexOf(bodyParserMatch[0]);
                const bodyParserLineEnd = appContent.indexOf('\n', bodyParserIndex);
                const beforeBodyParser = appContent.substring(0, bodyParserLineEnd + 1);
                const afterBodyParser = appContent.substring(bodyParserLineEnd + 1);
                
                appContent = beforeBodyParser + 'app.use(responseFormatter);\n' + afterBodyParser;
            } else {
                // 如果没有找到bodyParser，添加到express实例创建后
                appContent = appContent.replace(
                    /const app = express\(\);/,
                    'const app = express();\n\n// 响应格式化中间件\napp.use(responseFormatter);'
                );
            }
        }
        
        fs.writeFileSync(appPath, appContent);
        console.log('[' + this.name + '] 已更新app.js，添加响应格式化中间件');
    }

    // 添加API批量处理支持
    async addApiBatchProcessing(suggestion) {
        const batchControllerPath = path.join(projectRoot, suggestion.target);
        const batchControllerContent = '/**\n * MTSCOS AI 系统 - 批量处理控制器\n * 用于支持API批量处理\n */\n\nconst express = require(\'express\');\nconst router = express.Router();\n\n// 批量处理API
router.post(\'/, async (req, res) => {
    try {
        const { requests } = req.body;
        
        if (!Array.isArray(requests) || requests.length === 0) {
            return res.error(\'无效的批量请求格式\', 400);
        }
        
        // 限制批量请求数量
        if (requests.length > 10) {
            return res.error(\'批量请求数量不能超过10个\', 400);
        }
        
        // 模拟批量处理
        const results = await Promise.all(
            requests.map(async (request, index) => {
                try {
                    // 这里可以根据request.path和request.method调用不同的API
                    // 简化实现，直接返回模拟数据
                    return {
                        id: request.id || index,
                        status: \'success\',
                        data: { message: \'批量处理成功\', request: request },
                        timestamp: new Date().toISOString()
                    };
                } catch (error) {
                    return {
                        id: request.id || index,
                        status: \'error\',
                        message: error.message || \'处理失败\',
                        timestamp: new Date().toISOString()
                    };
                }
            })
        );
        
        return res.success(results, \'批量处理完成\');
    } catch (error) {
        return res.error(\'批量处理失败\', 500, error.message);
    }
});\n\nmodule.exports = router;\n';
        
        fs.writeFileSync(batchControllerPath, batchControllerContent);
        console.log('[' + this.name + '] API批量处理支持已添加: ' + batchControllerPath);
        
        // 更新v1 API路由，添加批量处理路由
        const v1IndexPath = path.join(projectRoot, 'src', 'api', 'v1', 'index.js');
        let v1IndexContent = fs.readFileSync(v1IndexPath, 'utf8');
        
        // 导入批量处理控制器
        if (!v1IndexContent.includes('const batchController')) {
            v1IndexContent = v1IndexContent.replace(
                /const userDataController = require\(\'../controllers/user-data.controller\'\);/,
                'const userDataController = require(\'../controllers/user-data.controller\');\nconst batchController = require(\'../controllers/batch.controller\');'
            );
        }
        
        // 添加批量处理路由
        if (!v1IndexContent.includes('router.use(\'/batch\', batchController)')) {
            v1IndexContent = v1IndexContent.replace(
                /router.use\(\'/user-data\'\, userDataController\);/,
                'router.use(\'/user-data\', userDataController);\nrouter.use(\'/batch\', batchController);'
            );
        }
        
        fs.writeFileSync(v1IndexPath, v1IndexContent);
        console.log('[' + this.name + '] 已更新API v1路由，添加批量处理路由');
    }

    // 添加数据库迁移工具
    async addDatabaseMigrations(suggestion) {
        const migrationsDir = path.join(projectRoot, suggestion.target);
        fs.mkdirSync(migrationsDir, { recursive: true });
        
        // 创建迁移工具入口文件
        const migrationToolPath = path.join(projectRoot, 'src', 'database', 'migration-tool.js');
        const migrationToolContent = '/**\n * MTSCOS AI 系统 - 数据库迁移工具\n * 用于支持数据库结构的版本控制和迁移\n */\n\nconst fs = require(\'fs\');\nconst path = require(\'path\');\n\nclass MigrationTool {\n    constructor(db) {\n        this.db = db;\n        this.migrationsDir = path.join(__dirname, \'migrations\');\n        this.migrationTable = \'migrations\';\n    }\n    \n    // 初始化迁移表
    async init() {\n        // 创建迁移表（如果不存在）
        const createMigrationTableSql = `\n            CREATE TABLE IF NOT EXISTS ${this.migrationTable} (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                name TEXT NOT NULL UNIQUE,\n                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP\n            )\n        `;\n        
        await this.db.execute(createMigrationTableSql);\n        console.log('[' + this.constructor.name + '] 迁移表已初始化');
    }\n    \n    // 获取已应用的迁移
    async getAppliedMigrations() {
        const sql = `SELECT name FROM ${this.migrationTable} ORDER BY applied_at`;
        const result = await this.db.query(sql);\n        return result.map(row => row.name);\n    }\n    \n    // 获取所有迁移文件
    getMigrationFiles() {
        const files = fs.readdirSync(this.migrationsDir);\n        return files\n            .filter(file => file.endsWith(\'.js\'))\n            .sort();\n    }\n    \n    // 应用迁移
    async migrate() {
        await this.init();\n        
        const appliedMigrations = await this.getAppliedMigrations();\n        const migrationFiles = this.getMigrationFiles();\n        
        const migrationsToApply = migrationFiles.filter(file => !appliedMigrations.includes(file));\n        
        if (migrationsToApply.length === 0) {
            console.log('[' + this.constructor.name + '] 没有需要应用的迁移');\n            return;
        }
        
        console.log('[' + this.constructor.name + '] 开始应用迁移: ' + migrationsToApply.length + ' 个');\n        
        for (const migrationFile of migrationsToApply) {
            console.log('[' + this.constructor.name + '] 应用迁移: ' + migrationFile);\n            
            const migration = require(path.join(this.migrationsDir, migrationFile));\n            
            // 执行迁移
            await migration.up(this.db);\n            
            // 记录迁移
            const insertSql = `INSERT INTO ${this.migrationTable} (name) VALUES (?)`;\n            await this.db.execute(insertSql, [migrationFile]);\n            
            console.log('[' + this.constructor.name + '] 迁移应用成功: ' + migrationFile);\n        }
        
        console.log('[' + this.constructor.name + '] 所有迁移应用完成');\n    }\n    \n    // 回滚迁移
    async rollback() {
        await this.init();\n        
        const appliedMigrations = await this.getAppliedMigrations();\n        
        if (appliedMigrations.length === 0) {
            console.log('[' + this.constructor.name + '] 没有需要回滚的迁移');\n            return;
        }
        
        // 获取最后一个应用的迁移
        const lastMigration = appliedMigrations[appliedMigrations.length - 1];\n        console.log('[' + this.constructor.name + '] 开始回滚迁移: ' + lastMigration);\n        
        const migration = require(path.join(this.migrationsDir, lastMigration));\n        
        // 执行回滚
        await migration.down(this.db);\n        
        // 删除迁移记录
        const deleteSql = `DELETE FROM ${this.migrationTable} WHERE name = ?`;\n        await this.db.execute(deleteSql, [lastMigration]);\n        
        console.log('[' + this.constructor.name + '] 迁移回滚成功: ' + lastMigration);\n    }\n    \n    // 创建新迁移
    createMigration(name) {
        const timestamp = new Date().toISOString().replace(/[^0-9]/g, '').slice(0, 14);\n        const migrationName = timestamp + '_' + name + '.js';\n        const migrationPath = path.join(this.migrationsDir, migrationName);\n        
        const migrationContent = '/**\n * MTSCOS AI 系统 - 迁移文件\n * 迁移名称: ' + name + '\n */\n\nmodule.exports = {\n    // 应用迁移\n    async up(db) {\n        // 在这里编写迁移逻辑\n        console.log(`[Migration] 应用迁移: ${migrationName}`);\n    },\n    \n    // 回滚迁移\n    async
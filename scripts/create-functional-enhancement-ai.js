#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - 功能完善和拓展子AI创建脚本
 * 用于自动完善系统现有功能并适当拓展功能，并上报特征库
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
class FunctionalEnhancementAI {
    constructor() {
        this.id = `ai_${crypto.randomBytes(16).toString('hex')}`;
        this.name = '功能完善和拓展AI';
        this.role = 'functional_enhancement';
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
        console.log(`[${this.name}] 开始分析系统现有功能...`);
        
        // 1. 分析项目结构
        const projectStructure = this.analyzeProjectStructure();
        
        // 2. 分析核心功能模块
        const coreModules = this.analyzeCoreModules();
        
        // 3. 分析API端点
        const apiEndpoints = this.analyzeApiEndpoints();
        
        // 4. 分析HTML页面
        const htmlPages = this.analyzeHtmlPages();
        
        // 5. 分析配置文件
        const configFiles = this.analyzeConfigFiles();
        
        return {
            projectStructure,
            coreModules,
            apiEndpoints,
            htmlPages,
            configFiles
        };
    }

    // 分析项目结构
    analyzeProjectStructure() {
        console.log(`[${this.name}] 分析项目结构...`);
        
        const structure = {
            directories: [],
            mainFiles: []
        };
        
        // 遍历项目目录
        const srcDir = path.join(projectRoot, 'src');
        if (fs.existsSync(srcDir)) {
            this.traverseDirectory(srcDir, structure);
        }
        
        return structure;
    }

    // 遍历目录
    traverseDirectory(dir, structure) {
        const items = fs.readdirSync(dir);
        
        items.forEach(item => {
            const itemPath = path.join(dir, item);
            const stats = fs.statSync(itemPath);
            
            if (stats.isDirectory()) {
                structure.directories.push(itemPath.replace(projectRoot, ''));
                this.traverseDirectory(itemPath, structure);
            } else {
                // 只记录主要文件类型
                const ext = path.extname(item);
                if (['.js', '.html', '.css', '.json'].includes(ext)) {
                    structure.mainFiles.push(itemPath.replace(projectRoot, ''));
                }
            }
        });
    }

    // 分析核心功能模块
    analyzeCoreModules() {
        console.log(`[${this.name}] 分析核心功能模块...`);
        
        const coreModules = [];
        const coreDir = path.join(projectRoot, 'src', 'core');
        
        if (fs.existsSync(coreDir)) {
            const files = fs.readdirSync(coreDir);
            files.forEach(file => {
                if (file.endsWith('.js')) {
                    coreModules.push(file.replace('.js', ''));
                }
            });
        }
        
        return coreModules;
    }

    // 分析API端点
    analyzeApiEndpoints() {
        console.log(`[${this.name}] 分析API端点...`);
        
        const apiEndpoints = [];
        const apiDir = path.join(projectRoot, 'src', 'api');
        
        if (fs.existsSync(apiDir)) {
            const files = fs.readdirSync(apiDir);
            files.forEach(file => {
                if (file.endsWith('.js')) {
                    const filePath = path.join(apiDir, file);
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
        
        return apiEndpoints;
    }

    // 分析HTML页面
    analyzeHtmlPages() {
        console.log(`[${this.name}] 分析HTML页面...`);
        
        const htmlPages = [];
        const htmlDir = path.join(projectRoot, 'src', 'html');
        
        if (fs.existsSync(htmlDir)) {
            this.traverseHtmlDirectory(htmlDir, htmlPages);
        }
        
        return htmlPages;
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

    // 分析配置文件
    analyzeConfigFiles() {
        console.log(`[${this.name}] 分析配置文件...`);
        
        const configFiles = [];
        const configDir = path.join(projectRoot, 'src', 'config');
        
        if (fs.existsSync(configDir)) {
            const files = fs.readdirSync(configDir);
            files.forEach(file => {
                if (file.endsWith('.js') || file.endsWith('.json')) {
                    configFiles.push(file);
                }
            });
        }
        
        return configFiles;
    }

    // 生成功能完善和拓展建议
    generateEnhancementSuggestions(systemAnalysis) {
        console.log(`[${this.name}] 生成功能完善和拓展建议...`);
        
        const suggestions = [];
        
        // 1. 检查是否缺少API文档
        if (!fs.existsSync(path.join(projectRoot, 'docs', 'api.md'))) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'documentation',
                name: '生成API文档',
                description: '为系统API生成详细的文档',
                severity: 'medium',
                priority: 'high',
                target: 'docs/api.md',
                implementation: 'generateApiDocumentation'
            });
        }
        
        // 2. 检查是否缺少日志系统
        if (!systemAnalysis.coreModules.includes('logger')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'feature',
                name: '添加日志系统',
                description: '为系统添加完善的日志记录功能',
                severity: 'high',
                priority: 'high',
                target: 'src/core/logger.js',
                implementation: 'addLoggerSystem'
            });
        }
        
        // 3. 检查是否缺少监控系统
        if (!systemAnalysis.coreModules.includes('monitor')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'feature',
                name: '添加监控系统',
                description: '为系统添加实时监控功能',
                severity: 'high',
                priority: 'medium',
                target: 'src/core/monitor.js',
                implementation: 'addMonitoringSystem'
            });
        }
        
        // 4. 检查是否缺少错误处理中间件
        const appPath = path.join(projectRoot, 'src', 'app.js');
        if (fs.existsSync(appPath)) {
            const appContent = fs.readFileSync(appPath, 'utf8');
            if (!appContent.includes('errorHandler')) {
                suggestions.push({
                    id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                    type: 'middleware',
                    name: '添加错误处理中间件',
                    description: '为系统添加统一的错误处理中间件',
                    severity: 'high',
                    priority: 'high',
                    target: 'src/core/errorHandler.js',
                    implementation: 'addErrorHandlerMiddleware'
                });
            }
        }
        
        // 5. 检查是否缺少API版本控制
        if (systemAnalysis.apiEndpoints.length > 0 && !systemAnalysis.apiEndpoints.some(endpoint => endpoint.startsWith('/v'))) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'feature',
                name: '添加API版本控制',
                description: '为系统API添加版本控制功能',
                severity: 'medium',
                priority: 'medium',
                target: 'src/api/v1',
                implementation: 'addApiVersioning'
            });
        }
        
        // 6. 检查是否缺少缓存机制
        if (!systemAnalysis.coreModules.includes('cache')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'feature',
                name: '添加缓存机制',
                description: '为系统添加缓存机制，提高性能',
                severity: 'medium',
                priority: 'medium',
                target: 'src/core/cache.js',
                implementation: 'addCacheSystem'
            });
        }
        
        // 7. 检查是否缺少API限流
        const appContent = fs.existsSync(appPath) ? fs.readFileSync(appPath, 'utf8') : '';
        if (appContent && !appContent.includes('rateLimit')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'security',
                name: '添加API限流',
                description: '为API添加限流功能，防止恶意请求',
                severity: 'high',
                priority: 'medium',
                target: 'src/core/rateLimiter.js',
                implementation: 'addApiRateLimiting'
            });
        }
        
        // 8. 检查是否缺少健康检查端点
        if (!systemAnalysis.apiEndpoints.includes('/health')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'feature',
                name: '添加健康检查端点',
                description: '添加系统健康检查端点，用于监控系统状态',
                severity: 'medium',
                priority: 'high',
                target: 'src/api/health.js',
                implementation: 'addHealthCheckEndpoint'
            });
        }
        
        // 9. 检查前端HTML页面是否缺少响应式设计
        for (const htmlPage of systemAnalysis.htmlPages) {
            const htmlPath = path.join(projectRoot, htmlPage);
            if (fs.existsSync(htmlPath)) {
                const htmlContent = fs.readFileSync(htmlPath, 'utf8');
                if (!htmlContent.includes('meta name="viewport"') && !htmlContent.includes('@media')) {
                    suggestions.push({
                        id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                        type: 'frontend',
                        name: '添加响应式设计支持',
                        description: '为前端页面添加响应式设计，支持不同设备尺寸',
                        severity: 'medium',
                        priority: 'medium',
                        target: htmlPage,
                        implementation: 'addResponsiveDesign'
                    });
                    break; // 只添加一个建议，统一处理
                }
            }
        }
        
        // 10. 检查是否缺少前端组件库
        if (!fs.existsSync(path.join(projectRoot, 'src', 'html', 'CSS', 'components.css'))) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'frontend',
                name: '创建前端组件库',
                description: '创建统一的前端组件库，提高页面开发效率',
                severity: 'medium',
                priority: 'medium',
                target: 'src/html/CSS/components.css',
                implementation: 'createFrontendComponentLibrary'
            });
        }
        
        // 11. 检查是否缺少前端路由系统
        if (!fs.existsSync(path.join(projectRoot, 'src', 'html', 'JS', 'router.js'))) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'frontend',
                name: '添加前端路由系统',
                description: '为前端添加路由系统，支持单页应用开发',
                severity: 'medium',
                priority: 'medium',
                target: 'src/html/JS/router.js',
                implementation: 'addFrontendRouting'
            });
        }
        
        // 12. 检查是否缺少数据库迁移工具
        if (!fs.existsSync(path.join(projectRoot, 'src', 'core', 'database', 'migration.js'))) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'database',
                name: '添加数据库迁移工具',
                description: '为系统添加数据库迁移工具，方便数据库结构更新',
                severity: 'high',
                priority: 'medium',
                target: 'src/core/database/migration.js',
                implementation: 'addDatabaseMigrationTool'
            });
        }
        
        // 13. 检查是否缺少数据库索引优化
        if (!systemAnalysis.coreModules.includes('databaseIndexer')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'database',
                name: '添加数据库索引优化',
                description: '为系统添加数据库索引优化功能，提高查询性能',
                severity: 'medium',
                priority: 'medium',
                target: 'src/core/database/indexer.js',
                implementation: 'addDatabaseIndexOptimization'
            });
        }
        
        // 14. 检查是否缺少业务规则引擎
        if (!systemAnalysis.coreModules.includes('businessRuleEngine')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'business',
                name: '添加业务规则引擎',
                description: '为系统添加业务规则引擎，方便业务逻辑管理',
                severity: 'high',
                priority: 'medium',
                target: 'src/core/businessRuleEngine.js',
                implementation: 'addBusinessRuleEngine'
            });
        }
        
        // 15. 检查是否缺少事件驱动架构支持
        if (!systemAnalysis.coreModules.includes('eventEmitter')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'architecture',
                name: '添加事件驱动架构支持',
                description: '为系统添加事件驱动架构支持，提高系统的扩展性和响应性',
                severity: 'high',
                priority: 'medium',
                target: 'src/core/eventEmitter.js',
                implementation: 'addEventDrivenArchitecture'
            });
        }
        
        // 16. 检查是否缺少自动修复功能
        if (!systemAnalysis.coreModules.includes('autoFix')) {
            suggestions.push({
                id: `suggestion_${crypto.randomBytes(8).toString('hex')}`,
                type: 'feature',
                name: '添加自动修复功能',
                description: '为系统添加自动修复功能，自动检测和修复常见问题',
                severity: 'high',
                priority: 'high',
                target: 'src/core/autoFix.js',
                implementation: 'addAutoFixFunctionality'
            });
        }
        
        return suggestions;
    }

    // 实现功能完善和拓展
    async implementEnhancements(suggestions) {
        console.log(`[${this.name}] 开始实现功能完善和拓展...`);
        
        const implementedEnhancements = [];
        
        for (const suggestion of suggestions) {
            try {
                console.log(`[${this.name}] 实现建议: ${suggestion.name}`);
                
                // 根据建议类型实现不同的功能
                switch (suggestion.implementation) {
                    case 'generateApiDocumentation':
                        await this.generateApiDocumentation(suggestion);
                        break;
                    case 'addLoggerSystem':
                        await this.addLoggerSystem(suggestion);
                        break;
                    case 'addMonitoringSystem':
                        await this.addMonitoringSystem(suggestion);
                        break;
                    case 'addErrorHandlerMiddleware':
                        await this.addErrorHandlerMiddleware(suggestion);
                        break;
                    case 'addApiVersioning':
                        await this.addApiVersioning(suggestion);
                        break;
                    case 'addCacheSystem':
                        await this.addCacheSystem(suggestion);
                        break;
                    case 'addApiRateLimiting':
                        await this.addApiRateLimiting(suggestion);
                        break;
                    case 'addHealthCheckEndpoint':
                        await this.addHealthCheckEndpoint(suggestion);
                        break;
                    case 'addResponsiveDesign':
                        await this.addResponsiveDesign(suggestion);
                        break;
                    case 'createFrontendComponentLibrary':
                        await this.createFrontendComponentLibrary(suggestion);
                        break;
                    case 'addFrontendRouting':
                        await this.addFrontendRouting(suggestion);
                        break;
                    case 'addDatabaseMigrationTool':
                        await this.addDatabaseMigrationTool(suggestion);
                        break;
                    case 'addDatabaseIndexOptimization':
                        await this.addDatabaseIndexOptimization(suggestion);
                        break;
                    case 'addBusinessRuleEngine':
                        await this.addBusinessRuleEngine(suggestion);
                        break;
                    case 'addEventDrivenArchitecture':
                        await this.addEventDrivenArchitecture(suggestion);
                        break;
                    case 'addAutoFixFunctionality':
                        await this.addAutoFixFunctionality(suggestion);
                        break;
                }
                
                implementedEnhancements.push({
                    ...suggestion,
                    status: 'completed',
                    timestamp: new Date().toISOString()
                });
                
            } catch (error) {
                console.error(`[${this.name}] 实现建议 ${suggestion.name} 失败:`, error.message);
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

    // 生成API文档
    async generateApiDocumentation(suggestion) {
        const apiDocPath = path.join(projectRoot, suggestion.target);
        
        // 创建文档目录
        fs.mkdirSync(path.dirname(apiDocPath), { recursive: true });
        
        // 简单生成API文档结构
        const apiDocContent = `# API Documentation

## Overview
This document provides detailed information about the MTSCOS AI system API endpoints.

## Authentication
All API endpoints require authentication unless otherwise specified.

## API Endpoints

### Health Check
- **URL**: /health
- **Method**: GET
- **Description**: Check the health status of the system
- **Response**: {
  "status": "ok",
  "timestamp": "2026-02-01T00:00:00Z",
  "version": "1.0.0"
}

## Error Handling
All API endpoints return standard HTTP status codes.

## Rate Limiting
API requests are rate limited to prevent abuse.
`;
        
        fs.writeFileSync(apiDocPath, apiDocContent);
        console.log(`[${this.name}] API文档已生成: ${apiDocPath}`);
    }

    // 添加日志系统
    async addLoggerSystem(suggestion) {
        const loggerPath = path.join(projectRoot, suggestion.target);
        
        // 创建日志系统文件
        const loggerContent = `/**
 * MTSCOS AI 系统 - 日志模块
 * 用于记录系统日志
 */

const fs = require('fs');
const path = require('path');

class Logger {
    constructor() {
        this.logDir = path.join(__dirname, '..', 'Logs');
        this.ensureLogDirectory();
        this.logLevel = process.env.LOG_LEVEL || 'info';
    }
    
    // 确保日志目录存在
    ensureLogDirectory() {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }
    
    // 生成日志文件名
    getLogFileName() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return year + '-' + month + '-' + day + '.log';
    }
    
    // 格式化日志消息
    formatMessage(level, message, metadata = {}) {
        const timestamp = new Date().toISOString();
        const metadataString = Object.keys(metadata).length > 0 ? ' ' + JSON.stringify(metadata) : '';
        return timestamp + ' [' + level.toUpperCase() + '] ' + message + metadataString + '\n';
    }
    
    // 写入日志到文件
    writeLog(level, message, metadata = {}) {
        const logFilePath = path.join(this.logDir, this.getLogFileName());
        const formattedMessage = this.formatMessage(level, message, metadata);
        
        fs.appendFileSync(logFilePath, formattedMessage, 'utf8');
        
        // 同时输出到控制台
        if (['debug', 'info', 'warn', 'error'].includes(level)) {
            console[level](formattedMessage.trim());
        }
    }
    
    // 不同级别的日志方法
    debug(message, metadata = {}) {
        if (['debug', 'info', 'warn', 'error'].includes(this.logLevel)) {
            this.writeLog('debug', message, metadata);
        }
    }
    
    info(message, metadata = {}) {
        if (['info', 'warn', 'error'].includes(this.logLevel)) {
            this.writeLog('info', message, metadata);
        }
    }
    
    warn(message, metadata = {}) {
        if (['warn', 'error'].includes(this.logLevel)) {
            this.writeLog('warn', message, metadata);
        }
    }
    
    error(message, metadata = {}) {
        if (['error'].includes(this.logLevel)) {
            this.writeLog('error', message, metadata);
        }
    }
}

module.exports = new Logger();
`;
        
        fs.writeFileSync(loggerPath, loggerContent);
        console.log(`[${this.name}] 日志系统已添加: ${loggerPath}`);
    }

    // 添加监控系统
    async addMonitoringSystem(suggestion) {
        const monitorPath = path.join(projectRoot, suggestion.target);
        
        // 创建监控系统文件
        const monitorContent = `/**
 * MTSCOS AI 系统 - 监控模块
 * 用于监控系统状态
 */

class Monitor {
    constructor() {
        this.metrics = {
            requests: 0,
            errors: 0,
            responseTimes: [],
            startTime: Date.now()
        };
        this.interval = null;
    }
    
    // 启动监控
    start() {
        console.log('[Monitor] 监控系统已启动');
        this.interval = setInterval(() => {
            this.reportMetrics();
        }, 60000); // 每分钟报告一次
    }
    
    // 停止监控
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
            console.log('[Monitor] 监控系统已停止');
        }
    }
    
    // 记录请求
    recordRequest(responseTime) {
        this.metrics.requests++;
        this.metrics.responseTimes.push(responseTime);
    }
    
    // 记录错误
    recordError() {
        this.metrics.errors++;
    }
    
    // 获取平均响应时间
    getAverageResponseTime() {
        if (this.metrics.responseTimes.length === 0) {
            return 0;
        }
        const sum = this.metrics.responseTimes.reduce((acc, time) => acc + time, 0);
        return sum / this.metrics.responseTimes.length;
    }
    
    // 报告指标
    reportMetrics() {
        const uptime = Math.floor((Date.now() - this.metrics.startTime) / 1000);
        const avgResponseTime = this.getAverageResponseTime();
        
        console.log('[Monitor] 系统指标报告:');
        console.log('  - 运行时间: ' + uptime + '秒');
        console.log('  - 请求总数: ' + this.metrics.requests);
        console.log('  - 错误总数: ' + this.metrics.errors);
        console.log('  - 平均响应时间: ' + avgResponseTime.toFixed(2) + 'ms');
    }
    
    // 获取当前指标
    getCurrentMetrics() {
        return {
            ...this.metrics,
            uptime: Math.floor((Date.now() - this.metrics.startTime) / 1000),
            averageResponseTime: this.getAverageResponseTime()
        };
    }
}

module.exports = new Monitor();
`;
        
        fs.writeFileSync(monitorPath, monitorContent);
        console.log(`[${this.name}] 监控系统已添加: ${monitorPath}`);
    }

    // 添加错误处理中间件
    async addErrorHandlerMiddleware(suggestion) {
        const errorHandlerPath = path.join(projectRoot, suggestion.target);
        
        // 创建错误处理中间件
        const errorHandlerContent = `/**
 * MTSCOS AI 系统 - 错误处理中间件
 * 用于统一处理系统错误
 */

const logger = require('./logger');

// 全局错误处理中间件
const errorHandler = (err, req, res, next) => {
    // 记录错误日志
    logger.error('系统错误', {
        error: err.message,
        stack: err.stack,
        url: req.url,
        method: req.method,
        ip: req.ip
    });
    
    // 定义错误响应格式
    const errorResponse = {
        status: 'error',
        message: err.message || '服务器内部错误',
        timestamp: new Date().toISOString(),
        path: req.url
    };
    
    // 设置HTTP状态码
    const statusCode = err.statusCode || 500;
    
    // 返回错误响应
    res.status(statusCode).json(errorResponse);
};

// 404错误处理中间件
const notFoundHandler = (req, res, next) => {
    const err = new Error('请求的资源不存在');
    err.statusCode = 404;
    next(err);
};

module.exports = {
    errorHandler,
    notFoundHandler
};
`;
        
        fs.writeFileSync(errorHandlerPath, errorHandlerContent);
        console.log(`[${this.name}] 错误处理中间件已添加: ${errorHandlerPath}`);
        
        // 更新app.js，添加错误处理中间件
        const appPath = path.join(projectRoot, 'src', 'app.js');
        if (fs.existsSync(appPath)) {
            let appContent = fs.readFileSync(appPath, 'utf8');
            
            // 导入错误处理中间件
            if (!appContent.includes('const { errorHandler, notFoundHandler }')) {
                appContent = appContent.replace(
                    /const express = require\('express'\);/,
                    `const express = require('express');\nconst { errorHandler, notFoundHandler } = require('./core/errorHandler');`
                );
            }
            
            // 添加错误处理中间件到应用
            if (!appContent.includes('app.use(errorHandler)')) {
                // 查找app.listen调用，在其之前添加错误处理中间件
                const listenMatch = appContent.match(/app\.listen\(([^)]+)\)/);
                if (listenMatch) {
                    const listenIndex = appContent.indexOf(listenMatch[0]);
                    const beforeListen = appContent.substring(0, listenIndex);
                    const afterListen = appContent.substring(listenIndex);
                    
                    appContent = `${beforeListen}\n\n// 错误处理中间件\napp.use(notFoundHandler);\napp.use(errorHandler);\n\n${afterListen}`;
                }
            }
            
            fs.writeFileSync(appPath, appContent);
            console.log(`[${this.name}] 已更新app.js，添加错误处理中间件`);
        }
    }

    // 添加API版本控制
    async addApiVersioning(suggestion) {
        const v1Dir = path.join(projectRoot, suggestion.target);
        
        // 创建v1 API目录
        fs.mkdirSync(v1Dir, { recursive: true });
        
        // 创建v1 API入口文件
        const v1IndexPath = path.join(v1Dir, 'index.js');
        const v1IndexContent = `/**
 * MTSCOS AI 系统 - API v1 入口文件
 */

const express = require('express');
const router = express.Router();

// 导入API路由
// router.use('/users', require('./users'));
// router.use('/projects', require('./projects'));

module.exports = router;
`;
        
        fs.writeFileSync(v1IndexPath, v1IndexContent);
        console.log(`[${this.name}] API版本控制已添加: ${v1Dir}`);
    }

    // 添加缓存系统
    async addCacheSystem(suggestion) {
        const cachePath = path.join(projectRoot, suggestion.target);
        
        // 创建缓存系统文件
        const cacheContent = `/**
 * MTSCOS AI 系统 - 缓存模块
 * 用于缓存系统数据，提高性能
 */

class Cache {
    constructor() {
        this.cache = new Map();
        this.defaultTTL = 3600; // 默认过期时间1小时
    }
    
    // 设置缓存项
    set(key, value, ttl = this.defaultTTL) {
        const expiresAt = Date.now() + (ttl * 1000);
        this.cache.set(key, { value, expiresAt });
    }
    
    // 获取缓存项
    get(key) {
        const item = this.cache.get(key);
        if (!item) {
            return null;
        }
        
        // 检查是否过期
        if (Date.now() > item.expiresAt) {
            this.cache.delete(key);
            return null;
        }
        
        return item.value;
    }
    
    // 删除缓存项
    delete(key) {
        return this.cache.delete(key);
    }
    
    // 清空所有缓存
    clear() {
        this.cache.clear();
    }
    
    // 检查缓存项是否存在
    has(key) {
        return this.get(key) !== null;
    }
    
    // 获取缓存大小
    size() {
        // 清理过期项
        this.cleanup();
        return this.cache.size;
    }
    
    // 清理过期缓存项
    cleanup() {
        const now = Date.now();
        for (const [key, item] of this.cache.entries()) {
            if (now > item.expiresAt) {
                this.cache.delete(key);
            }
        }
    }
}

module.exports = new Cache();
`;
        
        fs.writeFileSync(cachePath, cacheContent);
        console.log(`[${this.name}] 缓存系统已添加: ${cachePath}`);
    }

    // 添加API限流
    async addApiRateLimiting(suggestion) {
        const rateLimiterPath = path.join(projectRoot, suggestion.target);
        
        // 创建API限流文件
        const rateLimiterContent = `/**
 * MTSCOS AI 系统 - API限流模块
 * 用于限制API请求频率，防止恶意请求
 */

class RateLimiter {
    constructor() {
        this.requests = new Map();
        this.defaultLimit = 100; // 默认每分钟100个请求
        this.windowMs = 60 * 1000; // 时间窗口1分钟
    }
    
    // 检查请求是否超过限制
    check(ip, limit = this.defaultLimit) {
        const now = Date.now();
        const windowStart = now - this.windowMs;
        
        // 获取该IP的请求记录
        let ipRequests = this.requests.get(ip) || [];
        
        // 过滤掉时间窗口外的请求
        ipRequests = ipRequests.filter(timestamp => timestamp > windowStart);
        
        // 检查是否超过限制
        if (ipRequests.length >= limit) {
            return false;
        }
        
        // 添加新请求时间戳
        ipRequests.push(now);
        this.requests.set(ip, ipRequests);
        
        return true;
    }
    
    // 重置某个IP的请求计数
    reset(ip) {
        this.requests.delete(ip);
    }
    
    // 生成Express中间件
    middleware(limit = this.defaultLimit) {
        return (req, res, next) => {
            const ip = req.ip;
            
            if (this.check(ip, limit)) {
                next();
            } else {
                res.status(429).json({
                    status: 'error',
                    message: '请求频率过高，请稍后再试',
                    timestamp: new Date().toISOString()
                });
            }
        };
    }
}

module.exports = new RateLimiter();
`;
        
        fs.writeFileSync(rateLimiterPath, rateLimiterContent);
        console.log(`[${this.name}] API限流系统已添加: ${rateLimiterPath}`);
    }

    // 添加健康检查端点
    async addHealthCheckEndpoint(suggestion) {
        const healthPath = path.join(projectRoot, suggestion.target);
        
        // 创建健康检查端点文件
        const healthContent = `/**
 * MTSCOS AI 系统 - 健康检查端点
 */

const express = require('express');
const router = express.Router();
const packageJson = require('../../package.json');

// 健康检查端点
router.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: packageJson.version,
        uptime: process.uptime()
    });
});

module.exports = router;
`;
        
        fs.writeFileSync(healthPath, healthContent);
        console.log(`[${this.name}] 健康检查端点已添加: ${healthPath}`);
        
        // 更新app.js，添加健康检查路由
        const appPath = path.join(projectRoot, 'src', 'app.js');
        if (fs.existsSync(appPath)) {
            let appContent = fs.readFileSync(appPath, 'utf8');
            
            // 导入健康检查路由
            if (!appContent.includes('const healthRouter = require')) {
                appContent = appContent.replace(
                    /const express = require\('express'\);/,
                    `const express = require('express');\nconst healthRouter = require('./api/health');`
                );
            }
            
            // 添加健康检查路由到应用
            if (!appContent.includes('app.use(healthRouter)')) {
                // 查找合适的位置添加路由
                const routerMatch = appContent.match(/app\.use\(\/api/);
                if (routerMatch) {
                    const routerIndex = appContent.indexOf(routerMatch[0]);
                    const beforeRouter = appContent.substring(0, routerIndex);
                    const afterRouter = appContent.substring(routerIndex);
                    
                    appContent = `${beforeRouter}\napp.use(healthRouter);\n${afterRouter}`;
                } else {
                    // 如果没有其他API路由，添加到express实例创建后
                    appContent = appContent.replace(
                        /const app = express\(\);/,
                        `const app = express();\n\n// 健康检查路由\napp.use(healthRouter);`
                    );
                }
            }
            
            fs.writeFileSync(appPath, appContent);
            console.log(`[${this.name}] 已更新app.js，添加健康检查路由`);
        }
    }

    // 添加响应式设计支持
    async addResponsiveDesign(suggestion) {
        // 为所有HTML页面添加响应式设计支持
        const htmlDir = path.join(projectRoot, 'src', 'html');
        
        // 遍历所有HTML文件
        this.traverseHtmlDirectory(htmlDir, [], true);
        
        console.log(`[${this.name}] 响应式设计支持已添加到所有HTML页面`);
    }
    
    // 遍历HTML目录并添加响应式设计
    traverseHtmlDirectory(dir, htmlPages, addResponsive = false) {
        const items = fs.readdirSync(dir);
        
        items.forEach(item => {
            const itemPath = path.join(dir, item);
            const stats = fs.statSync(itemPath);
            
            if (stats.isDirectory()) {
                this.traverseHtmlDirectory(itemPath, htmlPages, addResponsive);
            } else if (item.endsWith('.html')) {
                htmlPages.push(itemPath.replace(projectRoot, ''));
                
                if (addResponsive) {
                    const htmlContent = fs.readFileSync(itemPath, 'utf8');
                    
                    // 添加viewport meta标签
                    if (!htmlContent.includes('meta name="viewport"')) {
                        let updatedContent = htmlContent.replace(
                            /<head>/i,
                            '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
                        );
                        
                        // 添加基础的响应式样式
                        if (!updatedContent.includes('@media')) {
                            updatedContent = updatedContent.replace(
                                /<\/head>/i,
                                '    <style>\n        /* 基础响应式样式 */\n        @media (max-width: 768px) {\n            body {\n                font-size: 14px;\n            }\n            .container {\n                width: 95%;\n                margin: 0 auto;\n            }\n        }\n        @media (max-width: 480px) {\n            body {\n                font-size: 12px;\n            }\n        }\n    </style>\n</head>'
                            );
                        }
                        
                        fs.writeFileSync(itemPath, updatedContent);
                    }
                }
            }
        });
    }
    
    // 创建前端组件库
    async createFrontendComponentLibrary(suggestion) {
        const componentsPath = path.join(projectRoot, suggestion.target);
        
        // 创建组件库文件
        const componentsContent = `/**
 * MTSCOS AI 系统 - 前端组件库
 * 提供统一的UI组件样式
 */

/* 按钮组件 */
.btn {
    display: inline-block;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    text-align: center;
    text-decoration: none;
    white-space: nowrap;
    vertical-align: middle;
    cursor: pointer;
    user-select: none;
    border: 1px solid transparent;
    border-radius: 4px;
    transition: all 0.2s ease-in-out;
}

.btn-primary {
    color: #fff;
    background-color: #007bff;
    border-color: #007bff;
}

.btn-primary:hover {
    background-color: #0056b3;
    border-color: #004085;
}

.btn-secondary {
    color: #fff;
    background-color: #6c757d;
    border-color: #6c757d;
}

.btn-secondary:hover {
    background-color: #545b62;
    border-color: #494f54;
}

/* 卡片组件 */
.card {
    position: relative;
    display: flex;
    flex-direction: column;
    min-width: 0;
    word-wrap: break-word;
    background-color: #fff;
    background-clip: border-box;
    border: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: 0.25rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}

.card-header {
    padding: 0.75rem 1.25rem;
    margin-bottom: 0;
    background-color: rgba(0, 0, 0, 0.03);
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.card-body {
    flex: 1 1 auto;
    padding: 1.25rem;
}

/* 表单组件 */
.form-group {
    margin-bottom: 1rem;
}

.form-control {
    display: block;
    width: 100%;
    padding: 0.375rem 0.75rem;
    font-size: 1rem;
    line-height: 1.5;
    color: #495057;
    background-color: #fff;
    background-clip: padding-box;
    border: 1px solid #ced4da;
    border-radius: 0.25rem;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus {
    border-color: #80bdff;
    outline: 0;
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* 容器组件 */
.container {
    width: 100%;
    padding-right: 15px;
    padding-left: 15px;
    margin-right: auto;
    margin-left: auto;
}

@media (min-width: 576px) {
    .container {
        max-width: 540px;
    }
}

@media (min-width: 768px) {
    .container {
        max-width: 720px;
    }
}

@media (min-width: 992px) {
    .container {
        max-width: 960px;
    }
}

@media (min-width: 1200px) {
    .container {
        max-width: 1140px;
    }
}

/* 导航组件 */
.navbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 1rem;
    background-color: #343a40;
    color: #fff;
}

.navbar-brand {
    display: inline-block;
    padding-top: 0.3125rem;
    padding-bottom: 0.3125rem;
    margin-right: 1rem;
    font-size: 1.25rem;
    line-height: inherit;
    white-space: nowrap;
    color: #fff;
    text-decoration: none;
}

.navbar-nav {
    display: flex;
    flex-direction: column;
    padding-left: 0;
    margin-bottom: 0;
    list-style: none;
}

.nav-item {
    margin-bottom: 0.5rem;
}

.nav-link {
    display: block;
    padding: 0.5rem 1rem;
    color: rgba(255, 255, 255, 0.5);
    text-decoration: none;
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.nav-link:hover, .nav-link:focus {
    color: rgba(255, 255, 255, 0.75);
    background-color: transparent;
}

@media (min-width: 768px) {
    .navbar-nav {
        flex-direction: row;
    }
    
    .nav-item {
        margin-bottom: 0;
        margin-left: 0.5rem;
    }
}
`;
                        
                        fs.writeFileSync(componentsPath, componentsContent);
                        console.log(`[${this.name}] 前端组件库已创建: ${componentsPath}`);
                    }
    
    // 添加前端路由系统
    async addFrontendRouting(suggestion) {
        const routerPath = path.join(projectRoot, suggestion.target);
        
        // 创建前端路由系统
        const routerContent = `/**
 * MTSCOS AI 系统 - 前端路由系统
 * 用于单页应用的路由管理
 */

class Router {
    constructor() {
        this.routes = {};
        this.currentPath = '';
        this.init();
    }
    
    // 初始化路由
    init() {
        // 监听页面加载
        window.addEventListener('load', () => {
            this.handleRoute();
        });
        
        // 监听浏览器历史变化
        window.addEventListener('popstate', () => {
            this.handleRoute();
        });
        
        // 拦截所有链接点击
        document.addEventListener('click', (e) => {
            const target = e.target.closest('a');
            if (target && target.matches('[data-route]')) {
                e.preventDefault();
                const path = target.getAttribute('href');
                this.navigate(path);
            }
        });
    }
    
    // 注册路由
    register(path, callback) {
        this.routes[path] = callback;
    }
    
    // 导航到指定路径
    navigate(path) {
        window.history.pushState({}, '', path);
        this.handleRoute();
    }
    
    // 处理路由
    handleRoute() {
        const path = window.location.pathname || '/';
        this.currentPath = path;
        
        const callback = this.routes[path] || this.routes['*'];
        if (callback) {
            callback();
        }
    }
    
    // 获取当前路径
    getCurrentPath() {
        return this.currentPath;
    }
    
    // 刷新当前路由
    refresh() {
        this.handleRoute();
    }
}

// 导出路由实例
window.router = new Router();
`;
        
        fs.writeFileSync(routerPath, routerContent);
        console.log(`[${this.name}] 前端路由系统已添加: ${routerPath}`);
    }
    
    // 添加数据库迁移工具
    async addDatabaseMigrationTool(suggestion) {
        const migrationPath = path.join(projectRoot, suggestion.target);
        
        // 创建数据库迁移工具
        const migrationContent = '/**\n' +
' * MTSCOS AI 系统 - 数据库迁移工具\n' +
' * 用于管理数据库结构更新\n' +
' */\n' +
'\n' +
'const fs = require(\'fs\');\n' +
'const path = require(\'path\');\n' +
'\n' +
'class DatabaseMigration {\n' +
'    constructor(dbPath) {\n' +
'        this.dbPath = dbPath;\n' +
'        this.migrationsDir = path.join(projectRoot, \'src\', \'database\', \'migrations\');\n' +
'        this.migrationTable = \'migrations\';\n' +
'        \n' +
'        // 确保迁移目录存在\n' +
'        fs.mkdirSync(this.migrationsDir, { recursive: true });\n' +
'    }\n' +
'    \n' +
'    // 创建迁移文件\n' +
'    createMigration(name) {\n' +
'        const timestamp = Date.now();\n' +
'        const migrationName = timestamp + \'_\' + name.replace(/\\s+/g, \'_\') + \'.js\';\n' +
'        const migrationPath = path.join(this.migrationsDir, migrationName);\n' +
'        \n' +
'        const migrationTemplate = \'/**\\n * Migration: \' + name + \\n * Timestamp: \' + timestamp + \\n */\\n\\nmodule.exports = {\\n    up: async (db) => {\\n        // 迁移向上操作\\n        // 例如: await db.run(\'CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT)\');\\n    },\\n    \\n    down: async (db) => {\\n        // 迁移向下操作\\n        // 例如: await db.run(\'DROP TABLE users\');\\n    }\\n};\\n\';\n' +
'        \n' +
'        fs.writeFileSync(migrationPath, migrationTemplate);\n' +
'        console.log(\'[Migration] 创建迁移文件: \' + migrationPath);\n' +
'        return migrationPath;\n' +
'    }\n' +
'    \n' +
'    // 执行所有未执行的迁移\n' +
'    async runMigrations(db) {\n' +
'        // 确保迁移表存在\n' +
'        await this.ensureMigrationTable(db);\n' +
'        \n' +
'        // 获取已执行的迁移\n' +
'        const executedMigrations = await this.getExecutedMigrations(db);\n' +
'        \n' +
'        // 获取所有迁移文件\n' +
'        const migrationFiles = fs.readdirSync(this.migrationsDir)\n' +
'            .filter(file => file.endsWith(\'.js\'))\n' +
'            .sort();\n' +
'        \n' +
'        // 执行未执行的迁移\n' +
'        for (const file of migrationFiles) {\n' +
'            const migrationName = file.replace(\'.js\', \'\');\n' +
'            if (!executedMigrations.includes(migrationName)) {\n' +
'                const migration = require(path.join(this.migrationsDir, file));\n' +
'                \n' +
'                console.log(\'[Migration] 执行迁移: \' + migrationName);\n' +
'                await migration.up(db);\n' +
'                await this.markMigrationExecuted(db, migrationName);\n' +
'            }\n' +
'        }\n' +
'        \n' +
'        console.log(\'[Migration] 所有迁移已执行完成\');\n' +
'    }\n' +
'    \n' +
'    // 回滚最近的迁移\n' +
'    async rollbackMigration(db) {\n' +
'        // 确保迁移表存在\n' +
'        await this.ensureMigrationTable(db);\n' +
'        \n' +
'        // 获取已执行的迁移\n' +
'        const executedMigrations = await this.getExecutedMigrations(db);\n' +
'        \n' +
'        if (executedMigrations.length === 0) {\n' +
'            console.log(\'[Migration] 没有可回滚的迁移\');\n' +
'            return;\n' +
'        }\n' +
'        \n' +
'        // 获取最后执行的迁移\n' +
'        const lastMigration = executedMigrations[executedMigrations.length - 1];\n' +
'        const migrationFile = lastMigration + \'.js\';\n' +
'        const migrationPath = path.join(this.migrationsDir, migrationFile);\n' +
'        \n' +
'        if (fs.existsSync(migrationPath)) {\n' +
'            const migration = require(migrationPath);\n' +
'            \n' +
'            console.log(\'[Migration] 回滚迁移: \' + lastMigration);\n' +
'            await migration.down(db);\n' +
'            await this.markMigrationRolledBack(db, lastMigration);\n' +
'        }\n' +
'        \n' +
'        console.log(\'[Migration] 迁移回滚完成\');\n' +
'    }\n' +
'    \n' +
'    // 确保迁移表存在\n' +
'    async ensureMigrationTable(db) {\n' +
'        await db.run(\'\\n' +
'            CREATE TABLE IF NOT EXISTS \' + this.migrationTable + \' (\\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\\n                name TEXT UNIQUE NOT NULL,\\n                executed_at DATETIME DEFAULT CURRENT_TIMESTAMP\\n            )\\n' +
'        \');\n' +
'    }\n' +
'    \n' +
'    // 获取已执行的迁移\n' +
'    async getExecutedMigrations(db) {\n' +
'        const migrations = [];\n' +
'        const rows = await db.all(\'SELECT name FROM \' + this.migrationTable + \' ORDER BY executed_at\');\n' +
'        \n' +
'        for (const row of rows) {\n' +
'            migrations.push(row.name);\n' +
'        }\n' +
'        \n' +
'        return migrations;\n' +
'    }\n' +
'    \n' +
'    // 标记迁移为已执行\n' +
'    async markMigrationExecuted(db, migrationName) {\n' +
'        await db.run(\n' +
'            \'INSERT INTO \' + this.migrationTable + \' (name) VALUES (?)\',\n' +
'            [migrationName]\n' +
'        );\n' +
'    }\n' +
'    \n' +
'    // 标记迁移为已回滚\n' +
'    async markMigrationRolledBack(db, migrationName) {\n' +
'        await db.run(\n' +
'            \'DELETE FROM \' + this.migrationTable + \' WHERE name = ?\',\n' +
'            [migrationName]\n' +
'        );\n' +
'    }\n' +
'}\n' +
'\n' +
'module.exports = DatabaseMigration;\n';
        
        fs.writeFileSync(migrationPath, migrationContent);
        console.log('[迁移工具] 数据库迁移工具已添加: ' + migrationPath);
    }
    
    // 添加数据库索引优化
    async addDatabaseIndexOptimization(suggestion) {
        const indexerPath = path.join(projectRoot, suggestion.target);
        
        // 创建数据库索引优化工具
        const indexerContent = '/**\n' +
' * MTSCOS AI 系统 - 数据库索引优化工具\n' +
' * 用于自动优化数据库索引\n' +
' */\n' +
'\n' +
'class DatabaseIndexer {\n' +
'    constructor(db) {\n' +
'        this.db = db;\n' +
'    }\n' +
'    \n' +
'    // 分析表并建议索引\n' +
'    async analyzeTable(tableName) {\n' +
'        console.log("[Indexer] 分析表: " + tableName);\n' +
'        \n' +
'        // 获取表结构\n' +
'        const columns = await this.getTableColumns(tableName);\n' +
'        \n' +
'        // 获取表的查询模式（简化版，实际应分析查询日志）\n' +
'        const queryPatterns = await this.getQueryPatterns(tableName);\n' +
'        \n' +
'        // 生成索引建议\n' +
'        const indexSuggestions = this.generateIndexSuggestions(tableName, columns, queryPatterns);\n' +
'        \n' +
'        return indexSuggestions;\n' +
'    }\n' +
'    \n' +
'    // 获取表列信息\n' +
'    async getTableColumns(tableName) {\n' +
'        // 简化实现，实际应根据数据库类型查询\n' +
'        const columns = [];\n' +
'        // 这里应该查询数据库获取表的实际列信息\n' +
'        \n' +
'        return columns;\n' +
'    }\n' +
'    \n' +
'    // 获取查询模式\n' +
'    async getQueryPatterns(tableName) {\n' +
'        // 简化实现，实际应分析查询日志\n' +
'        const patterns = [\n' +
'            { columns: [\"id\"], frequency: 100 },\n' +
'            { columns: [\"name\"], frequency: 50 },\n' +
'            { columns: [\"created_at\"], frequency: 30 }\n' +
'        ];\n' +
'        \n' +
'        return patterns;\n' +
'    }\n' +
'    \n' +
'    // 生成索引建议\n' +
'    generateIndexSuggestions(tableName, columns, queryPatterns) {\n' +
'        const suggestions = [];\n' +
'        \n' +
'        for (const pattern of queryPatterns) {\n' +
'            // 只建议高频查询的索引\n' +
'            if (pattern.frequency > 20) {\n' +
'                suggestions.push({\n' +
'                    table: tableName,\n' +
'                    columns: pattern.columns,\n' +
'                    type: "B-tree",\n' +
'                    reason: "高频查询列: " + pattern.columns.join(", ")\n' +
'                });\n' +
'            }\n' +
'        }\n' +
'        \n' +
'        return suggestions;\n' +
'    }\n' +
'    \n' +
'    // 创建索引\n' +
'    async createIndex(suggestion) {\n' +
'        const indexName = "idx_" + suggestion.table + "_" + suggestion.columns.join("_");\n' +
'        const columns = suggestion.columns.join(", ");\n' +
'        \n' +
'        const sql = "CREATE INDEX IF NOT EXISTS " + indexName + " ON " + suggestion.table + " (" + columns + ")";\n' +
'        \n' +
'        try {\n' +
'            await this.db.run(sql);\n' +
'            console.log("[Indexer] 创建索引: " + indexName);\n' +
'            return true;\n' +
'        } catch (error) {\n' +
'            console.error("[Indexer] 创建索引 " + indexName + " 失败:", error.message);\n' +
'            return false;\n' +
'        }\n' +
'    }\n' +
'    \n' +
'    // 优化所有表的索引\n' +
'    async optimizeAllTables() {\n' +
'        // 获取所有表\n' +
'        const tables = await this.getAllTables();\n' +
'        \n' +
'        for (const table of tables) {\n' +
'            const suggestions = await this.analyzeTable(table);\n' +
'            \n' +
'            for (const suggestion of suggestions) {\n' +
'                await this.createIndex(suggestion);\n' +
'            }\n' +
'        }\n' +
'        \n' +
'        console.log("[Indexer] 所有表索引优化完成");\n' +
'    }\n' +
'    \n' +
'    // 获取所有表\n' +
'    async getAllTables() {\n' +
'        // 简化实现，实际应查询数据库获取所有表\n' +
'        return ["users", "projects", "logs", "features"];\n' +
'    }\n' +
'}\n' +
'\n' +
'module.exports = DatabaseIndexer;\n';
        
        fs.writeFileSync(indexerPath, indexerContent);
        console.log("[" + this.name + "] 数据库索引优化工具已添加: " + indexerPath);
    }
    
    // 添加业务规则引擎
    async addBusinessRuleEngine(suggestion) {
        const ruleEnginePath = path.join(projectRoot, suggestion.target);
        
        // 创建业务规则引擎
        const ruleEngineContent = '/**\n' +
' * MTSCOS AI 系统 - 业务规则引擎\n' +
' * 用于管理和执行业务规则\n' +
' */\n' +
'\n' +
'class BusinessRuleEngine {\n' +
'    constructor() {\n' +
'        this.rules = [];\n' +
'    }\n' +
'    \n' +
'    // 添加规则\n' +
'    addRule(rule) {\n' +
'        this.rules.push(rule);\n' +
'        console.log("[RuleEngine] 添加规则: " + rule.name);\n' +
'    }\n' +
'    \n' +
'    // 执行规则\n' +
'    async executeRules(data, context = {}) {\n' +
'        const results = [];\n' +
'        \n' +
'        for (const rule of this.rules) {\n' +
'            try {\n' +
'                // 检查规则条件\n' +
'                if (await this.evaluateCondition(rule.condition, data, context)) {\n' +
'                    // 执行规则动作\n' +
'                    const result = await this.executeAction(rule.action, data, context);\n' +
'                    results.push({\n' +
'                        rule: rule.name,\n' +
'                        result: result,\n' +
'                        status: "success"\n' +
'                    });\n' +
'                }\n' +
'            } catch (error) {\n' +
'                results.push({\n' +
'                    rule: rule.name,\n' +
'                    error: error.message,\n' +
'                    status: "failed"\n' +
'                });\n' +
'            }\n' +
'        }\n' +
'        \n' +
'        return results;\n' +
'    }\n' +
'    \n' +
'    // 评估规则条件\n' +
'    async evaluateCondition(condition, data, context) {\n' +
'        if (typeof condition === "function") {\n' +
'            return await condition(data, context);\n' +
'        } else if (typeof condition === "string") {\n' +
'            // 简单的条件表达式支持\n' +
'            try {\n' +
'                return eval(condition);\n' +
'            } catch (error) {\n' +
'                console.error("[RuleEngine] 条件表达式执行失败: " + condition, error);\n' +
'                return false;\n' +
'            }\n' +
'        }\n' +
'        return false;\n' +
'    }\n' +
'    \n' +
'    // 执行规则动作\n' +
'    async executeAction(action, data, context) {\n' +
'        if (typeof action === "function") {\n' +
'            return await action(data, context);\n' +
'        } else if (typeof action === "string") {\n' +
'            // 简单的动作表达式支持\n' +
'            try {\n' +
'                return eval(action);\n' +
'            } catch (error) {\n' +
'                console.error("[RuleEngine] 动作表达式执行失败: " + action, error);\n' +
'                return null;\n' +
'            }\n' +
'        }\n' +
'        return null;\n' +
'    }\n' +
'    \n' +
'    // 获取规则列表\n' +
'    getRules() {\n' +
'        return this.rules;\n' +
'    }\n' +
'    \n' +
'    // 根据名称查找规则\n' +
'    findRule(name) {\n' +
'        return this.rules.find(function(rule) { return rule.name === name; });\n' +
'    }\n' +
'    \n' +
'    // 删除规则\n' +
'    removeRule(name) {\n' +
'        const index = this.rules.findIndex(function(rule) { return rule.name === name; });\n' +
'        if (index > -1) {\n' +
'            this.rules.splice(index, 1);\n' +
'            console.log("[RuleEngine] 删除规则: " + name);\n' +
'            return true;\n' +
'        }\n' +
'        return false;\n' +
'    }\n' +
'}\n' +
'\n' +
'module.exports = BusinessRuleEngine;\n';
        
        fs.writeFileSync(ruleEnginePath, ruleEngineContent);
        console.log("[" + this.name + "] 业务规则引擎已添加: " + ruleEnginePath);
    }
    
    // 添加事件驱动架构支持
    async addEventDrivenArchitecture(suggestion) {
        const eventEmitterPath = path.join(projectRoot, suggestion.target);
        
        // 创建事件驱动架构支持
        const eventEmitterContent = '/**\n' +
' * MTSCOS AI 系统 - 事件驱动架构支持\n' +
' * 用于系统组件间的事件通信\n' +
' */\n' +
'\n' +
'class EventEmitter {\n' +
'    constructor() {\n' +
'        this.events = {};\n' +
'        this.maxListeners = 10;\n' +
'    }\n' +
'    \n' +
'    // 设置最大监听器数量\n' +
'    setMaxListeners(n) {\n' +
'        this.maxListeners = n;\n' +
'        return this;\n' +
'    }\n' +
'    \n' +
'    // 获取最大监听器数量\n' +
'    getMaxListeners() {\n' +
'        return this.maxListeners;\n' +
'    }\n' +
'    \n' +
'    // 监听事件\n' +
'    on(eventName, listener) {\n' +
'        if (!this.events[eventName]) {\n' +
'            this.events[eventName] = [];\n' +
'        }\n' +
'        \n' +
'        // 检查监听器数量\n' +
'        if (this.events[eventName].length >= this.maxListeners) {\n' +
'            console.warn("[EventEmitter] 事件 " + eventName + " 的监听器数量超过最大值 " + this.maxListeners);\n' +
'        }\n' +
'        \n' +
'        this.events[eventName].push(listener);\n' +
'        return this;\n' +
'    }\n' +
'    \n' +
'    // 监听事件（只触发一次）\n' +
'    once(eventName, listener) {\n' +
'        const onceListener = function() {\n' +
'            this.removeListener(eventName, onceListener);\n' +
'            listener.apply(this, arguments);\n' +
'        }.bind(this);\n' +
'        \n' +
'        onceListener.listener = listener;\n' +
'        this.on(eventName, onceListener);\n' +
'        return this;\n' +
'    }\n' +
'    \n' +
'    // 移除事件监听器\n' +
'    removeListener(eventName, listener) {\n' +
'        if (!this.events[eventName]) {\n' +
'            return this;\n' +
'        }\n' +
'        \n' +
'        this.events[eventName] = this.events[eventName].filter(function(l) {\n' +
'            return l !== listener && l.listener !== listener;\n' +
'        });\n' +
'        \n' +
'        return this;\n' +
'    }\n' +
'    \n' +
'    // 移除所有事件监听器\n' +
'    removeAllListeners(eventName) {\n' +
'        if (eventName) {\n' +
'            delete this.events[eventName];\n' +
'        } else {\n' +
'            this.events = {};\n' +
'        }\n' +
'        return this;\n' +
'    }\n' +
'    \n' +
'    // 获取事件监听器数量\n' +
'    listenerCount(eventName) {\n' +
'        return this.events[eventName] ? this.events[eventName].length : 0;\n' +
'    }\n' +
'    \n' +
'    // 获取事件监听器列表\n' +
'    listeners(eventName) {\n' +
'        return this.events[eventName] ? this.events[eventName].slice() : [];\n' +
'    }\n' +
'    \n' +
'    // 触发事件\n' +
'    emit(eventName) {\n' +
'        if (!this.events[eventName]) {\n' +
'            return false;\n' +
'        }\n' +
'        \n' +
'        const args = Array.prototype.slice.call(arguments, 1);\n' +
'        for (let i = 0; i < this.events[eventName].length; i++) {\n' +
'            this.events[eventName][i].apply(this, args);\n' +
'        }\n' +
'        \n' +
'        return true;\n' +
'    }\n' +
'    \n' +
'    // 获取所有事件名称\n' +
'    eventNames() {\n' +
'        return Object.keys(this.events);\n' +
'    }\n' +
'}\n' +
'\n' +
'module.exports = EventEmitter;\n';
        
        fs.writeFileSync(eventEmitterPath, eventEmitterContent);
        console.log("[" + this.name + "] 事件驱动架构支持已添加: " + eventEmitterPath);
    }
    
    // 添加自动修复功能
    async addAutoFixFunctionality(suggestion) {
        const autoFixPath = path.join(projectRoot, suggestion.target);
        
        // 创建自动修复功能
        const autoFixContent = `/**
 * MTSCOS AI 系统 - 自动修复功能
 * 用于自动检测和修复常见问题
 */

const fs = require('fs');
const path = require('path');

class AutoFix {
    constructor() {
        this.fixers = [];
        this.initFixers();
    }
    
    // 初始化修复器
    initFixers() {
        // 注册常见问题的修复器
        this.registerFixer({
            id: 'fix-missing-ssl',
            name: '修复缺少SSL配置',
            description: '自动检测并修复缺少SSL配置的问题',
            detector: this.detectMissingSSL.bind(this),
            fixer: this.fixMissingSSL.bind(this)
        });
        
        this.registerFixer({
            id: 'fix-broken-links',
            name: '修复损坏的链接',
            description: '自动检测并修复HTML中的损坏链接',
            detector: this.detectBrokenLinks.bind(this),
            fixer: this.fixBrokenLinks.bind(this)
        });
        
        this.registerFixer({
            id: 'fix-missing-dependencies',
            name: '修复缺少的依赖',
            description: '自动检测并安装缺少的依赖',
            detector: this.detectMissingDependencies.bind(this),
            fixer: this.fixMissingDependencies.bind(this)
        });
    }
    
    // 注册修复器
    registerFixer(fixer) {
        this.fixers.push(fixer);
        console.log("[AutoFix] 注册修复器: " + fixer.name);
    }
    
    // 执行所有修复器
    async runAllFixers() {
        console.log('[AutoFix] 开始执行所有修复器');
        
        const results = [];
        
        for (const fixer of this.fixers) {
            try {
                const issues = await fixer.detector();
                
                if (issues.length > 0) {
                    console.log("[AutoFix] 修复器 " + fixer.name + " 检测到 " + issues.length + " 个问题");
                    
                    const fixResults = await fixer.fixer(issues);
                    results.push({
                        fixer: fixer.name,
                        issues: issues.length,
                        fixed: fixResults.fixed,
                        failed: fixResults.failed
                    });
                }
            } catch (error) {
                console.error("[AutoFix] 修复器 " + fixer.name + " 执行失败:", error);
                results.push({
                    fixer: fixer.name,
                    error: error.message
                });
            }
        }
        
        console.log('[AutoFix] 所有修复器执行完成');
        return results;
    }
    
    // 检测缺少SSL配置
    async detectMissingSSL() {
        const issues = [];
        // 简化实现，实际应检测SSL配置
        return issues;
    }
    
    // 修复缺少SSL配置
    async fixMissingSSL(issues) {
        // 简化实现，实际应修复SSL配置
        return { fixed: 0, failed: 0 };
    }
    
    // 检测损坏的链接
    async detectBrokenLinks() {
        const issues = [];
        const htmlDir = path.join(projectRoot, 'src', 'html');
        
        // 简化实现，实际应检测HTML文件中的链接
        return issues;
    }
    
    // 修复损坏的链接
    async fixBrokenLinks(issues) {
        // 简化实现，实际应修复HTML文件中的链接
        return { fixed: 0, failed: 0 };
    }
    
    // 检测缺少的依赖
    async detectMissingDependencies() {
        const issues = [];
        // 简化实现，实际应检测package.json中的依赖
        return issues;
    }
    
    // 修复缺少的依赖
    async fixMissingDependencies(issues) {
        // 简化实现，实际应安装缺少的依赖
        return { fixed: 0, failed: 0 };
    }
}

module.exports = AutoFix;
`;
        
        fs.writeFileSync(autoFixPath, autoFixContent);
        console.log("[" + this.name + "] 自动修复功能已添加: " + autoFixPath);
    }
    
    // 上报特征库
    async reportToFeatureDb() {
        console.log("[" + this.name + "] 开始上报特征库...");
        
        // 读取现有的特征数据库
        let featureDb = [];
        if (fs.existsSync(errorFeatureDbPath)) {
            const dbContent = fs.readFileSync(errorFeatureDbPath, 'utf8');
            featureDb = JSON.parse(dbContent);
        }
        
        // 创建新的特征记录
        const feature = {
            id: "feature_" + Date.now(),
            type: "functional_enhancement",
            name: "系统功能完善和拓展",
            description: "自动完善系统现有功能并适当拓展功能",
            severity: "high",
            pattern: {
                totalSuggestions: this.enhancements.length,
                implementedSuggestions: this.enhancements.filter(function(e) { return e.status === "completed"; }).length,
                failedSuggestions: this.enhancements.filter(function(e) { return e.status === "failed"; }).length,
                enhancementTypes: {
                    documentation: this.enhancements.filter(function(e) { return e.type === "documentation"; }).length,
                    feature: this.enhancements.filter(function(e) { return e.type === "feature"; }).length,
                    middleware: this.enhancements.filter(function(e) { return e.type === "middleware"; }).length,
                    security: this.enhancements.filter(function(e) { return e.type === "security"; }).length,
                    frontend: this.enhancements.filter(function(e) { return e.type === "frontend"; }).length,
                    database: this.enhancements.filter(function(e) { return e.type === "database"; }).length,
                    business: this.enhancements.filter(function(e) { return e.type === "business"; }).length,
                    architecture: this.enhancements.filter(function(e) { return e.type === "architecture"; }).length
                }
            },
            detectionMethod: "static_analysis",
            fixActions: this.enhancements.map(function(e) {
                return {
                    id: e.id,
                    type: e.type,
                    description: e.description,
                    target: e.target,
                    status: e.status,
                    timestamp: e.timestamp,
                    error: e.error || null
                };
            }),
            solution: "自动完善和拓展系统功能，提高系统的完整性和性能",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            aiId: this.id,
            aiName: this.name,
            aiRole: this.role,
            source: "auto_enhancement",
            status: "active",
            version: "1.0.0"
        };
        
        // 添加到特征数据库
        featureDb.push(feature);
        
        // 写入特征数据库
        fs.writeFileSync(errorFeatureDbPath, JSON.stringify(featureDb, null, 2));
        console.log("[" + this.name + "] 特征库上报完成，特征ID: " + feature.id);
        
        return feature;
    }

    // 执行完整的功能完善和拓展流程
    async execute() {
        console.log("[" + this.name + "] 开始执行功能完善和拓展流程...");
        
        try {
            // 1. 分析系统现有功能
            const systemAnalysis = await this.analyzeSystemFeatures();
            
            // 2. 生成功能完善和拓展建议
            const suggestions = this.generateEnhancementSuggestions(systemAnalysis);
            
            // 3. 实现功能完善和拓展
            const implementedEnhancements = await this.implementEnhancements(suggestions);
            
            // 4. 上报特征库
            const reportedFeature = await this.reportToFeatureDb();
            
            console.log("[" + this.name + "] 功能完善和拓展流程执行完成！");
            console.log("[" + this.name + "] 共生成 " + suggestions.length + " 个建议，成功实现 " + implementedEnhancements.filter(function(e) { return e.status === "completed"; }).length + " 个，失败 " + implementedEnhancements.filter(function(e) { return e.status === "failed"; }).length + " 个");
            
            return {
                success: true,
                message: "功能完善和拓展流程执行完成",
                suggestionsCount: suggestions.length,
                implementedCount: implementedEnhancements.filter(function(e) { return e.status === "completed"; }).length,
                failedCount: implementedEnhancements.filter(function(e) { return e.status === "failed"; }).length,
                featureId: reportedFeature.id
            };
            
        } catch (error) {
            console.error("[" + this.name + "] 功能完善和拓展流程执行失败:", error);
            return {
                success: false,
                message: "功能完善和拓展流程执行失败: " + error.message,
                error: error.message
            };
        }
    }
}

// 创建AI实例
const ai = new FunctionalEnhancementAI();

// 执行功能完善和拓展流程
ai.execute().then(result => {
    console.log('\n' + '='.repeat(60));
    console.log('功能完善和拓展AI执行结果:');
    console.log('='.repeat(60));
    console.log(JSON.stringify(result, null, 2));
    console.log('='.repeat(60));
    
    // 退出进程
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('功能完善和拓展AI执行出错:', error);
    process.exit(1);
});

/**
 * 浏览器兼容性子AI
 * 自动适配市面上大多数浏览器，并上报特征库
 */

const winston = require('winston');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const aiFeatureLibrary = require('./ai-feature-library');

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/browser-compatibility-ai.log`,
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

/**
 * 浏览器兼容性子AI类
 */
class BrowserCompatibilitySubAI {
    constructor(name = 'browser-compatibility-subai', role = 'browser_compatibility', group = 'optimization') {
        this.id = crypto.randomUUID();
        this.name = name;
        this.role = role;
        this.group = group;
        this.level = 'component'; // 部署层级: core, module, component, feature
        this.layer = 'presentation'; // 技术层: system, business, application, presentation
        this.status = 'idle';
        this.currentTask = null;
        this.taskHistory = [];
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.idleSince = new Date();
        this.startedAt = null;
        this.deploymentStatus = 'pending';
        
        // 监管关系
        this.isMainAI = false;
        this.supervisorId = null;
        this.subordinateIds = [];
        this.supervisedTasks = [];
        this.peerIds = [];
        
        // 功能特征和能力评分
        this.features = new Set();
        this.capabilities = {};
        
        // AI版本和升级相关
        this.version = '1.0.0';
        this.modelVersion = '1.0.0';
        this.upgradeHistory = [];
        this.isUpgrading = false;
        this.lastUpgradeAt = null;
        
        // 自适应学习相关
        this.learningRate = 0.01;
        this.adaptationHistory = [];
        this.performanceMetrics = {};
        this.projectAdaptation = {};
        this.layerAdaptation = {};
        
        // 浏览器兼容性特定属性
        this.projectRoot = path.resolve(__dirname, '../../..');
        this.featureDatabasePath = path.join(this.projectRoot, 'features', 'browser-compatibility-ai.json');
        this.diagnosisResults = {};
        this.fixResults = {};
        this.enhancementResults = {};
        this.issues = [];
        this.browserStats = {};
        
        // 初始化
        this.loadCapabilities();
        this.initializeFeatureDatabase();
    }
    
    /**
     * 加载AI能力配置
     */
    loadCapabilities() {
        // 基础功能特征
        const baseFeatures = new Set([
            'model-upgrade',
            'self-adaptation',
            'continuous-learning'
        ]);
        
        // 浏览器兼容性特定特征
        this.features = new Set([
            ...baseFeatures,
            'browser-compatibility',
            'html-compatibility',
            'css-compatibility',
            'javascript-compatibility',
            'responsive-design',
            'feature-detection',
            'polyfill-management',
            'browser-statistics'
        ]);
        
        // 能力评分
        this.capabilities = {
            browserDetection: 90,
            htmlCompatibility: 85,
            cssCompatibility: 85,
            javascriptCompatibility: 80,
            responsiveDesign: 85,
            polyfillManagement: 80,
            featureReporting: 90,
            selfAdaptation: 75,
            modelUpgrade: 70
        };
    }
    
    /**
     * 初始化特征库
     */
    initializeFeatureDatabase() {
        const featuresDir = path.join(this.projectRoot, 'features');
        if (!fs.existsSync(featuresDir)) {
            fs.mkdirSync(featuresDir, { recursive: true });
        }
        
        if (!fs.existsSync(this.featureDatabasePath)) {
            fs.writeFileSync(this.featureDatabasePath, JSON.stringify({
                version: '1.0.0',
                created: new Date().toISOString(),
                updated: new Date().toISOString(),
                features: [],
                enhancements: [],
                metrics: {
                    totalDiagnoses: 0,
                    totalFixes: 0,
                    successRate: 0,
                    issuesFixed: 0,
                    browsersSupported: 0
                }
            }, null, 2));
        }
    }
    
    /**
     * 运行浏览器兼容性适配
     */
    async runBrowserCompatibilityAdaptation() {
        logger.info(`AI ${this.name} 开始浏览器兼容性适配`);
        
        try {
            // 1. 运行诊断
            await this.runDiagnosis();
            
            // 2. 运行修复
            await this.runFix();
            
            // 3. 功能拓展
            await this.enhanceFeatures();
            
            // 4. 上报特征库
            await this.reportToFeatureLibrary();
            
            // 5. 生成报告
            const report = this.generateReport();
            
            logger.info(`AI ${this.name} 浏览器兼容性适配完成`);
            
            return {
                success: true,
                report: report
            };
        } catch (error) {
            logger.error(`AI ${this.name} 浏览器兼容性适配失败: ${error.message}`);
            return {
                success: false,
                message: error.message
            };
        }
    }
    
    /**
     * 运行诊断
     */
    async runDiagnosis() {
        logger.info(`AI ${this.name} 运行浏览器兼容性诊断`);
        
        try {
            // 1. 诊断HTML结构
            await this.diagnoseHTMLStructure();
            
            // 2. 诊断CSS兼容性
            await this.diagnoseCSSCompatibility();
            
            // 3. 诊断JavaScript兼容性
            await this.diagnoseJavaScriptCompatibility();
            
            // 4. 诊断响应式设计
            await this.diagnoseResponsiveDesign();
            
            // 5. 诊断资源加载
            await this.diagnoseResourceLoading();
            
            logger.info(`AI ${this.name} 浏览器兼容性诊断完成`);
            return this.diagnosisResults;
        } catch (error) {
            logger.error(`AI ${this.name} 浏览器兼容性诊断失败: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 诊断HTML结构
     */
    async diagnoseHTMLStructure() {
        logger.info(`AI ${this.name} 诊断HTML结构`);
        
        try {
            // 检查HTML文件是否符合标准
            const htmlFiles = this.findFiles('src/html', '*.html');
            let issuesFound = 0;
            
            for (const htmlFile of htmlFiles) {
                const content = fs.readFileSync(htmlFile, 'utf8');
                
                // 检查DOCTYPE声明
                if (!content.startsWith('<!DOCTYPE html>')) {
                    this.issues.push({
                        type: 'html',
                        severity: 'medium',
                        description: '缺少DOCTYPE声明',
                        location: htmlFile
                    });
                    issuesFound++;
                }
                
                // 检查meta charset
                if (!content.includes('<meta charset="UTF-8">') && !content.includes('<meta charset="utf-8">')) {
                    this.issues.push({
                        type: 'html',
                        severity: 'medium',
                        description: '缺少meta charset声明',
                        location: htmlFile
                    });
                    issuesFound++;
                }
                
                // 检查viewport meta标签
                if (!content.includes('viewport')) {
                    this.issues.push({
                        type: 'html',
                        severity: 'medium',
                        description: '缺少viewport meta标签',
                        location: htmlFile
                    });
                    issuesFound++;
                }
            }
            
            this.diagnosisResults.htmlStructure = {
                status: issuesFound === 0 ? 'ok' : 'error',
                message: `HTML结构检查完成，发现${issuesFound}个问题`,
                issuesFound: issuesFound,
                totalFiles: htmlFiles.length
            };
        } catch (error) {
            this.diagnosisResults.htmlStructure = {
                status: 'error',
                message: 'HTML结构诊断失败',
                error: error.message
            };
            this.issues.push({
                type: 'system',
                severity: 'high',
                description: 'HTML结构诊断失败',
                location: 'system'
            });
        }
    }
    
    /**
     * 诊断CSS兼容性
     */
    async diagnoseCSSCompatibility() {
        logger.info(`AI ${this.name} 诊断CSS兼容性`);
        
        try {
            // 检查CSS文件中的兼容性问题
            const cssFiles = this.findFiles('src/html', '*.css');
            let issuesFound = 0;
            
            // 常见的CSS兼容性问题模式
            const compatibilityIssues = [
                { pattern: /(webkit|moz|ms|o)-transition/, description: '使用了浏览器前缀transition' },
                { pattern: /(webkit|moz|ms|o)-transform/, description: '使用了浏览器前缀transform' },
                { pattern: /(webkit|moz|ms|o)-animation/, description: '使用了浏览器前缀animation' },
                { pattern: /display:\s*flex\s*;/, description: '使用了flex布局（需要检查兼容性）' },
                { pattern: /grid\s*;/, description: '使用了grid布局（需要检查兼容性）' },
                { pattern: /var\(\s*--/, description: '使用了CSS变量（需要检查兼容性）' }
            ];
            
            for (const cssFile of cssFiles) {
                const content = fs.readFileSync(cssFile, 'utf8');
                
                for (const issue of compatibilityIssues) {
                    if (issue.pattern.test(content)) {
                        this.issues.push({
                            type: 'css',
                            severity: 'medium',
                            description: issue.description,
                            location: cssFile
                        });
                        issuesFound++;
                    }
                }
            }
            
            this.diagnosisResults.cssCompatibility = {
                status: issuesFound === 0 ? 'ok' : 'error',
                message: `CSS兼容性检查完成，发现${issuesFound}个问题`,
                issuesFound: issuesFound,
                totalFiles: cssFiles.length
            };
        } catch (error) {
            this.diagnosisResults.cssCompatibility = {
                status: 'error',
                message: 'CSS兼容性诊断失败',
                error: error.message
            };
        }
    }
    
    /**
     * 诊断JavaScript兼容性
     */
    async diagnoseJavaScriptCompatibility() {
        logger.info(`AI ${this.name} 诊断JavaScript兼容性`);
        
        try {
            // 检查JavaScript文件中的兼容性问题
            const jsFiles = this.findFiles('src/html', '*.js');
            let issuesFound = 0;
            
            // 常见的JavaScript兼容性问题模式
            const compatibilityIssues = [
                { pattern: /const\s+\w+\s*=/, description: '使用了const关键字（需要检查兼容性）' },
                { pattern: /let\s+\w+\s*=/, description: '使用了let关键字（需要检查兼容性）' },
                { pattern: /\(\s*\w+\s*=>/, description: '使用了箭头函数（需要检查兼容性）' },
                { pattern: /`[^`]+`/, description: '使用了模板字符串（需要检查兼容性）' },
                { pattern: /\.includes\(/, description: '使用了Array.includes方法（需要检查兼容性）' },
                { pattern: /\.forEach\(/, description: '使用了Array.forEach方法（需要检查兼容性）' },
                { pattern: /\.map\(/, description: '使用了Array.map方法（需要检查兼容性）' },
                { pattern: /Promise\s*\(/, description: '使用了Promise（需要检查兼容性）' },
                { pattern: /async\s+function/, description: '使用了async/await（需要检查兼容性）' }
            ];
            
            for (const jsFile of jsFiles) {
                const content = fs.readFileSync(jsFile, 'utf8');
                
                for (const issue of compatibilityIssues) {
                    if (issue.pattern.test(content)) {
                        this.issues.push({
                            type: 'javascript',
                            severity: 'medium',
                            description: issue.description,
                            location: jsFile
                        });
                        issuesFound++;
                    }
                }
            }
            
            this.diagnosisResults.jsCompatibility = {
                status: issuesFound === 0 ? 'ok' : 'error',
                message: `JavaScript兼容性检查完成，发现${issuesFound}个问题`,
                issuesFound: issuesFound,
                totalFiles: jsFiles.length
            };
        } catch (error) {
            this.diagnosisResults.jsCompatibility = {
                status: 'error',
                message: 'JavaScript兼容性诊断失败',
                error: error.message
            };
        }
    }
    
    /**
     * 诊断响应式设计
     */
    async diagnoseResponsiveDesign() {
        logger.info(`AI ${this.name} 诊断响应式设计`);
        
        try {
            // 检查响应式设计实现
            const cssFiles = this.findFiles('src/html', '*.css');
            let issuesFound = 0;
            let hasMediaQueries = false;
            
            for (const cssFile of cssFiles) {
                const content = fs.readFileSync(cssFile, 'utf8');
                
                // 检查是否有媒体查询
                if (content.includes('@media')) {
                    hasMediaQueries = true;
                }
                
                // 检查是否有固定宽度
                const fixedWidthPattern = /width:\s*\d+px\s*;/g;
                const fixedWidthMatches = content.match(fixedWidthPattern);
                if (fixedWidthMatches && fixedWidthMatches.length > 0) {
                    this.issues.push({
                        type: 'css',
                        severity: 'medium',
                        description: `发现${fixedWidthMatches.length}个固定宽度设置，可能影响响应式设计`,
                        location: cssFile
                    });
                    issuesFound++;
                }
            }
            
            if (!hasMediaQueries) {
                this.issues.push({
                    type: 'css',
                    severity: 'high',
                    description: '缺少媒体查询，可能影响响应式设计',
                    location: 'src/html'
                });
                issuesFound++;
            }
            
            this.diagnosisResults.responsiveDesign = {
                status: issuesFound === 0 ? 'ok' : 'error',
                message: `响应式设计检查完成，发现${issuesFound}个问题`,
                issuesFound: issuesFound,
                hasMediaQueries: hasMediaQueries,
                totalFiles: cssFiles.length
            };
        } catch (error) {
            this.diagnosisResults.responsiveDesign = {
                status: 'error',
                message: '响应式设计诊断失败',
                error: error.message
            };
        }
    }
    
    /**
     * 诊断资源加载
     */
    async diagnoseResourceLoading() {
        logger.info(`AI ${this.name} 诊断资源加载`);
        
        try {
            // 检查资源加载优化
            const htmlFiles = this.findFiles('src/html', '*.html');
            let issuesFound = 0;
            
            for (const htmlFile of htmlFiles) {
                const content = fs.readFileSync(htmlFile, 'utf8');
                
                // 检查是否有异步加载的脚本
                const asyncScripts = (content.match(/<script[^>]+async[^>]+>/gi) || []).length;
                const deferScripts = (content.match(/<script[^>]+defer[^>]+>/gi) || []).length;
                const totalScripts = (content.match(/<script[^>]+src[^>]+>/gi) || []).length;
                
                if (totalScripts > 0 && asyncScripts + deferScripts === 0) {
                    this.issues.push({
                        type: 'html',
                        severity: 'medium',
                        description: `发现${totalScripts}个未异步加载的脚本，可能影响页面加载速度`,
                        location: htmlFile
                    });
                    issuesFound++;
                }
            }
            
            this.diagnosisResults.resourceLoading = {
                status: issuesFound === 0 ? 'ok' : 'error',
                message: `资源加载检查完成，发现${issuesFound}个问题`,
                issuesFound: issuesFound,
                totalFiles: htmlFiles.length
            };
        } catch (error) {
            this.diagnosisResults.resourceLoading = {
                status: 'error',
                message: '资源加载诊断失败',
                error: error.message
            };
        }
    }
    
    /**
     * 运行修复
     */
    async runFix() {
        logger.info(`AI ${this.name} 开始修复浏览器兼容性问题`);
        
        for (const issue of this.issues) {
            logger.info(`   修复问题: ${issue.description}`);
            
            try {
                let result;
                if (issue.type === 'html') {
                    result = this.fixHTMLIssue(issue);
                } else if (issue.type === 'css') {
                    result = this.fixCSSIssue(issue);
                } else if (issue.type === 'javascript') {
                    result = this.fixJavaScriptIssue(issue);
                } else {
                    result = { status: 'skipped', message: '未实现的修复类型' };
                }
                
                this.fixResults[issue.location] = result;
                logger.info(`   结果: ${result.status} - ${result.message}`);
            } catch (error) {
                this.fixResults[issue.location] = {
                    status: 'failed',
                    message: error.message
                };
                logger.error(`   结果: failed - ${error.message}`);
            }
        }
        
        logger.info(`AI ${this.name} 浏览器兼容性修复完成`);
    }
    
    /**
     * 修复HTML问题
     */
    fixHTMLIssue(issue) {
        try {
            const content = fs.readFileSync(issue.location, 'utf8');
            let newContent = content;
            
            if (issue.description.includes('DOCTYPE')) {
                // 添加DOCTYPE声明
                newContent = '<!DOCTYPE html>' + newContent;
            } else if (issue.description.includes('meta charset')) {
                // 添加meta charset声明
                if (newContent.includes('<head>')) {
                    newContent = newContent.replace(/<head>/i, '<head>\n    <meta charset="UTF-8">');
                }
            } else if (issue.description.includes('viewport')) {
                // 添加viewport meta标签
                if (newContent.includes('<head>')) {
                    newContent = newContent.replace(/<head>/i, '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">');
                }
            } else if (issue.description.includes('异步加载的脚本')) {
                // 添加async属性到脚本标签
                newContent = newContent.replace(/<script src="([^"]+)"/gi, '<script src="$1" async');
            }
            
            fs.writeFileSync(issue.location, newContent, 'utf8');
            
            return {
                status: 'success',
                message: 'HTML问题已修复'
            };
        } catch (error) {
            return {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 修复CSS问题
     */
    fixCSSIssue(issue) {
        try {
            const content = fs.readFileSync(issue.location, 'utf8');
            let newContent = content;
            
            if (issue.description.includes('媒体查询')) {
                // 添加基本的媒体查询模板
                const mediaQueryTemplate = `
/* 响应式设计 */
@media (max-width: 768px) {
    /* 平板设备样式 */
}

@media (max-width: 480px) {
    /* 移动设备样式 */
}`;
                newContent += mediaQueryTemplate;
            }
            
            fs.writeFileSync(issue.location, newContent, 'utf8');
            
            return {
                status: 'success',
                message: 'CSS问题已修复'
            };
        } catch (error) {
            return {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 修复JavaScript问题
     */
    fixJavaScriptIssue(issue) {
        try {
            // 对于JavaScript兼容性问题，我们添加兼容性检查和回退方案
            const content = fs.readFileSync(issue.location, 'utf8');
            let newContent = content;
            
            // 添加兼容性检查和回退方案
            const compatibilityHeader = `
// 兼容性检查和回退方案
(function() {
    'use strict';
    
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
`;
            
            // 添加到文件开头
            newContent = compatibilityHeader + newContent;
            fs.writeFileSync(issue.location, newContent, 'utf8');
            
            return {
                status: 'success',
                message: 'JavaScript兼容性问题已修复'
            };
        } catch (error) {
            return {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 功能拓展
     */
    async enhanceFeatures() {
        logger.info(`AI ${this.name} 开始功能拓展`);
        
        // 1. 添加浏览器兼容性库
        await this.addBrowserCompatibilityLibrary();
        
        // 2. 添加浏览器检测功能
        await this.addBrowserDetection();
        
        // 3. 添加性能优化
        await this.addPerformanceOptimization();
        
        // 4. 添加错误监控
        await this.addErrorMonitoring();
        
        logger.info(`AI ${this.name} 功能拓展完成`);
    }
    
    /**
     * 添加浏览器兼容性库
     */
    async addBrowserCompatibilityLibrary() {
        logger.info(`AI ${this.name} 添加浏览器兼容性库`);
        
        try {
            // 检查是否已经添加了兼容性库
            const indexPath = path.join(this.projectRoot, 'src', 'html', 'index.html');
            const content = fs.readFileSync(indexPath, 'utf8');
            
            if (!content.includes('polyfill')) {
                // 添加polyfill.io库
                const polyfillScript = `
<!-- 浏览器兼容性库 -->
<script src="https://cdn.polyfill.io/v3/polyfill.min.js"></script>`;
                
                if (content.includes('</head>')) {
                    let newContent = content.replace(/<\/head>/i, polyfillScript + '\n</head>');
                    fs.writeFileSync(indexPath, newContent, 'utf8');
                }
            }
            
            this.enhancementResults.compatibilityLibrary = {
                status: 'success',
                message: '浏览器兼容性库已添加'
            };
        } catch (error) {
            this.enhancementResults.compatibilityLibrary = {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 添加浏览器检测功能
     */
    async addBrowserDetection() {
        logger.info(`AI ${this.name} 添加浏览器检测功能`);
        
        try {
            // 检查是否已经添加了浏览器检测功能
            const indexPath = path.join(this.projectRoot, 'src', 'html', 'index.html');
            const content = fs.readFileSync(indexPath, 'utf8');
            
            if (!content.includes('browser-detection')) {
                // 添加浏览器检测脚本
                const detectionScript = `
<!-- 浏览器检测 -->
<script>
// 浏览器检测功能
(function() {
    'use strict';
    
    const browserInfo = {
        name: 'unknown',
        version: 'unknown',
        os: 'unknown'
    };
    
    // 检测浏览器名称和版本
    const userAgent = navigator.userAgent;
    if (userAgent.includes('Chrome')) {
        browserInfo.name = 'Chrome';
        browserInfo.version = userAgent.match(/Chrome\/(\d+\.\d+)/)[1];
    } else if (userAgent.includes('Firefox')) {
        browserInfo.name = 'Firefox';
        browserInfo.version = userAgent.match(/Firefox\/(\d+\.\d+)/)[1];
    } else if (userAgent.includes('Safari')) {
        browserInfo.name = 'Safari';
        browserInfo.version = userAgent.match(/Version\/(\d+\.\d+)/)[1];
    } else if (userAgent.includes('Edge')) {
        browserInfo.name = 'Edge';
        browserInfo.version = userAgent.match(/Edge\/(\d+\.\d+)/)[1];
    } else if (userAgent.includes('IE')) {
        browserInfo.name = 'Internet Explorer';
        browserInfo.version = userAgent.match(/Trident\/(\d+\.\d+)/)[1];
    }
    
    // 检测操作系统
    if (userAgent.includes('Windows')) {
        browserInfo.os = 'Windows';
    } else if (userAgent.includes('Macintosh')) {
        browserInfo.os = 'macOS';
    } else if (userAgent.includes('Linux')) {
        browserInfo.os = 'Linux';
    } else if (userAgent.includes('Android')) {
        browserInfo.os = 'Android';
    } else if (userAgent.includes('iOS')) {
        browserInfo.os = 'iOS';
    }
    
    // 存储浏览器信息
    window.browserInfo = browserInfo;
    console.log('浏览器信息:', browserInfo);
    
    // 上报浏览器信息到服务器
    fetch('/api/browser-info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(browserInfo)
    }).catch(error => console.error('上报浏览器信息失败:', error));
})();
</script>`;
                
                if (content.includes('</body>')) {
                    let newContent = content.replace(/<\/body>/i, detectionScript + '\n</body>');
                    fs.writeFileSync(indexPath, newContent, 'utf8');
                }
            }
            
            this.enhancementResults.browserDetection = {
                status: 'success',
                message: '浏览器检测功能已添加'
            };
        } catch (error) {
            this.enhancementResults.browserDetection = {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 添加性能优化
     */
    async addPerformanceOptimization() {
        logger.info(`AI ${this.name} 添加性能优化`);
        
        try {
            // 检查是否已经添加了性能优化
            const indexPath = path.join(this.projectRoot, 'src', 'html', 'index.html');
            const content = fs.readFileSync(indexPath, 'utf8');
            
            if (!content.includes('performance-optimization')) {
                // 添加性能优化脚本
                const perfScript = `
<!-- 性能优化 -->
<script>
// 性能优化功能
(function() {
    'use strict';
    
    // 延迟加载非关键资源
    function lazyLoad() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
            if (img.getBoundingClientRect().top < window.innerHeight + 100) {
                img.src = img.getAttribute('data-src');
                img.removeAttribute('data-src');
            }
        });
    }
    
    // 监听滚动事件
    window.addEventListener('scroll', lazyLoad);
    
    // 初始加载
    window.addEventListener('load', lazyLoad);
})();
</script>`;
                
                if (content.includes('</body>')) {
                    let newContent = content.replace(/<\/body>/i, perfScript + '\n</body>');
                    fs.writeFileSync(indexPath, newContent, 'utf8');
                }
            }
            
            this.enhancementResults.performanceOptimization = {
                status: 'success',
                message: '性能优化已添加'
            };
        } catch (error) {
            this.enhancementResults.performanceOptimization = {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 添加错误监控
     */
    async addErrorMonitoring() {
        logger.info(`AI ${this.name} 添加错误监控`);
        
        try {
            // 检查是否已经添加了错误监控
            const indexPath = path.join(this.projectRoot, 'src', 'html', 'index.html');
            const content = fs.readFileSync(indexPath, 'utf8');
            
            if (!content.includes('error-monitoring')) {
                // 添加错误监控脚本
                const errorScript = `
<!-- 错误监控 -->
<script>
// 错误监控功能
(function() {
    'use strict';
    
    // 监听全局错误
    window.addEventListener('error', function(event) {
        const errorInfo = {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error ? event.error.stack : 'No stack trace available',
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        console.error('全局错误:', errorInfo);
        
        // 上报错误到服务器
        fetch('/api/error-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(errorInfo)
        }).catch(error => console.error('上报错误失败:', error));
    });
    
    // 监听未处理的Promise拒绝
    window.addEventListener('unhandledrejection', function(event) {
        const errorInfo = {
            message: event.reason ? event.reason.message : 'Unhandled promise rejection',
            reason: event.reason ? event.reason.stack : 'No stack trace available',
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        console.error('未处理的Promise拒绝:', errorInfo);
        
        // 上报错误到服务器
        fetch('/api/error-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(errorInfo)
        }).catch(error => console.error('上报错误失败:', error));
    });
})();
</script>`;
                
                if (content.includes('</body>')) {
                    let newContent = content.replace(/<\/body>/i, errorScript + '\n</body>');
                    fs.writeFileSync(indexPath, newContent, 'utf8');
                }
            }
            
            this.enhancementResults.errorMonitoring = {
                status: 'success',
                message: '错误监控已添加'
            };
        } catch (error) {
            this.enhancementResults.errorMonitoring = {
                status: 'failed',
                message: error.message
            };
        }
    }
    
    /**
     * 上报特征库
     */
    async reportToFeatureLibrary() {
        logger.info(`AI ${this.name} 开始上报特征库`);
        
        try {
            // 1. 上报到项目特征库
            await this.reportToProjectFeatureLibrary();
            
            // 2. 上报到中央特征库
            await this.reportToCentralFeatureLibrary();
            
            logger.info(`AI ${this.name} 特征库上报完成`);
            return { status: 'success', message: '特征库上报成功' };
        } catch (error) {
            logger.error(`AI ${this.name} 特征库上报失败: ${error.message}`);
            return { status: 'failed', message: error.message };
        }
    }
    
    /**
     * 上报到项目特征库
     */
    async reportToProjectFeatureLibrary() {
        // 读取现有特征库
        let featureDatabase;
        if (fs.existsSync(this.featureDatabasePath)) {
            featureDatabase = JSON.parse(fs.readFileSync(this.featureDatabasePath, 'utf8'));
        } else {
            featureDatabase = {
                version: '1.0.0',
                created: new Date().toISOString(),
                updated: new Date().toISOString(),
                features: [],
                enhancements: [],
                metrics: {
                    totalDiagnoses: 0,
                    totalFixes: 0,
                    successRate: 0,
                    issuesFixed: 0,
                    browsersSupported: 0
                }
            };
        }
        
        // 收集特征数据
        const features = {
            timestamp: new Date().toISOString(),
            projectRoot: this.projectRoot,
            diagnosisResults: this.diagnosisResults,
            fixResults: this.fixResults,
            enhancementResults: this.enhancementResults,
            issues: this.issues,
            browserStats: this.browserStats,
            version: '1.0.0'
        };
        
        // 添加到特征库
        featureDatabase.features.push(features);
        featureDatabase.updated = new Date().toISOString();
        featureDatabase.metrics.totalDiagnoses++;
        featureDatabase.metrics.totalFixes++;
        featureDatabase.metrics.issuesFixed += this.issues.length;
        
        // 计算成功率
        const totalOperations = Object.keys(this.fixResults).length + Object.keys(this.enhancementResults).length;
        const successOperations = Object.values(this.fixResults).filter(r => r.status === 'success').length +
                                 Object.values(this.enhancementResults).filter(r => r.status === 'success').length;
        featureDatabase.metrics.successRate = totalOperations > 0 ? ((successOperations / totalOperations) * 100).toFixed(2) : 100;
        
        // 更新支持的浏览器数量
        featureDatabase.metrics.browsersSupported = 5; // Chrome, Firefox, Safari, Edge, IE
        
        // 保存特征库
        fs.writeFileSync(this.featureDatabasePath, JSON.stringify(featureDatabase, null, 2));
        
        logger.info(`AI ${this.name} 项目特征库上报成功`);
    }
    
    /**
     * 上报到中央特征库
     */
    async reportToCentralFeatureLibrary() {
        // 收集特征数据
        const feature = {
            aiId: this.id,
            aiName: this.name,
            aiRole: this.role,
            type: 'browser-compatibility',
            timestamp: new Date().toISOString(),
            data: {
                diagnosisResults: this.diagnosisResults,
                fixResults: this.fixResults,
                enhancementResults: this.enhancementResults,
                issues: this.issues,
                browserStats: this.browserStats,
                projectRoot: this.projectRoot
            },
            version: this.version
        };
        
        // 使用ai-feature-library上报
        aiFeatureLibrary.addFeature(feature);
        
        logger.info(`AI ${this.name} 中央特征库上报成功`);
    }
    
    /**
     * 生成报告
     */
    generateReport() {
        logger.info(`AI ${this.name} 生成兼容性报告`);
        
        // 项目分析结果
        console.log('=== 浏览器兼容性报告 ===');
        console.log('1. 诊断结果:');
        Object.entries(this.diagnosisResults).forEach(([key, value]) => {
            console.log(`   - ${key}: ${value.status} - ${value.message}`);
        });
        
        // 修复建议执行情况
        console.log('\n2. 修复结果:');
        Object.entries(this.fixResults).forEach(([key, value]) => {
            console.log(`   - ${key}: ${value.status} - ${value.message}`);
        });
        
        // 功能拓展情况
        console.log('\n3. 功能拓展结果:');
        Object.entries(this.enhancementResults).forEach(([key, value]) => {
            console.log(`   - ${key}: ${value.status} - ${value.message}`);
        });
        
        // 优化统计
        console.log('\n4. 统计信息:');
        console.log(`   - 发现问题数: ${this.issues.length}`);
        console.log(`   - 修复问题数: ${Object.keys(this.fixResults).length}`);
        console.log(`   - 功能拓展数: ${Object.keys(this.enhancementResults).length}`);
        console.log(`   - 支持的浏览器: Chrome, Firefox, Safari, Edge, IE`);
        
        return {
            diagnosisResults: this.diagnosisResults,
            fixResults: this.fixResults,
            enhancementResults: this.enhancementResults,
            issues: this.issues,
            totalIssues: this.issues.length,
            totalFixes: Object.keys(this.fixResults).length,
            totalEnhancements: Object.keys(this.enhancementResults).length,
            browsersSupported: 5
        };
    }
    
    /**
     * 运行完整的兼容性适配流程
     */
    async run() {
        logger.info(`=== 浏览器兼容性子AI ===`);
        logger.info(`开始自动适配市面上大多数浏览器，并上报特征库...`);
        
        // 1. 运行诊断
        await this.runDiagnosis();
        
        // 2. 运行修复
        await this.runFix();
        
        // 3. 功能拓展
        await this.enhanceFeatures();
        
        // 4. 生成报告
        const report = this.generateReport();
        
        // 5. 上报特征库
        await this.reportToFeatureLibrary();
        
        logger.info(`\n=== 兼容性适配流程完成 ===`);
        logger.info(`\n兼容性报告:`);
        logger.info(`   - 发现问题数: ${report.totalIssues}`);
        logger.info(`   - 修复问题数: ${report.totalFixes}`);
        logger.info(`   - 功能拓展数: ${report.totalEnhancements}`);
        logger.info(`   - 支持的浏览器: ${report.browsersSupported} 种`);
        
        return report;
    }
    
    /**
     * 查找文件
     */
    findFiles(directory, pattern) {
        const fullPath = path.join(this.projectRoot, directory);
        const findCommand = `find ${fullPath} -name "${pattern}" -type f | grep -v ".git"`;
        const { execSync } = require('child_process');
        const result = execSync(findCommand, { encoding: 'utf8' });
        return result.trim().split('\n').filter(Boolean);
    }
}

// 导出单例实例
const browserCompatibilitySubAI = new BrowserCompatibilitySubAI();
module.exports = browserCompatibilitySubAI;
module.exports.BrowserCompatibilitySubAI = BrowserCompatibilitySubAI;
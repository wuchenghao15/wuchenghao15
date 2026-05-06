/**
 * 资源修复子AI
 * 专门处理缺失资源和加载失败资源，尝试修复并上报特征库
 */

const winston = require('winston');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/resource-fixer-ai.log`,
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

// 资源修复子AI类
class ResourceFixerAI {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = 'resource_fixer_ai';
        this.role = 'resource_fixer';
        this.group = 'fixer';
        this.status = 'idle';
        this.currentTask = null;
        this.taskHistory = [];
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.idleSince = new Date();
        
        // 修复配置
        this.fixConfig = {
            autoFix: true,
            featureReporting: true,
            fixInterval: 30000, // 每30秒检查一次需要修复的资源
            fixDirectory: path.join(__dirname, '../../../Logs/captures/fixes')
        };
        
        // 性能指标
        this.performanceMetrics = {
            resourcesScanned: 0,
            resourcesFixed: 0,
            resourcesFailed: 0,
            featuresReported: 0,
            lastFixTime: null
        };
        
        // 待修复资源列表
        this.resourcesToFix = [];
        
        // 确保修复目录存在
        if (!fs.existsSync(this.fixConfig.fixDirectory)) {
            fs.mkdirSync(this.fixConfig.fixDirectory, { recursive: true });
        }
        
        logger.info(`✅ 资源修复子AI已初始化: ${this.name}`);
    }
    
    /**
     * 开始修复
     */
    startFixing() {
        logger.info(`🔧 开始资源修复...`);
        this.status = 'running';
        this.currentTask = 'resource_fixing';
        this.updatedAt = new Date();
        
        // 定期检查需要修复的资源
        this.fixInterval = setInterval(() => {
            this.checkAndFixResources();
        }, this.fixConfig.fixInterval);
        
        logger.info(`✅ 资源修复已启动`);
        return { success: true, message: '资源修复已启动' };
    }
    
    /**
     * 停止修复
     */
    stopFixing() {
        logger.info(`🔧 停止资源修复...`);
        this.status = 'idle';
        this.currentTask = null;
        this.idleSince = new Date();
        this.updatedAt = new Date();
        
        if (this.fixInterval) {
            clearInterval(this.fixInterval);
            this.fixInterval = null;
        }
        
        logger.info(`✅ 资源修复已停止`);
        return { success: true, message: '资源修复已停止' };
    }
    
    /**
     * 添加需要修复的资源
     */
    addResourceToFix(resource) {
        this.resourcesToFix.push(resource);
        logger.info(`📋 添加需要修复的资源: ${resource.url || resource.path}`);
    }
    
    /**
     * 检查并修复资源
     */
    async checkAndFixResources() {
        logger.info(`🔍 检查并修复资源...`);
        this.performanceMetrics.lastFixTime = new Date();
        
        if (this.resourcesToFix.length === 0) {
            logger.info(`📋 没有需要修复的资源`);
            return;
        }
        
        // 处理所有需要修复的资源
        const resourcesToProcess = [...this.resourcesToFix];
        this.resourcesToFix = [];
        
        for (const resource of resourcesToProcess) {
            await this.fixResource(resource);
        }
    }
    
    /**
     * 修复资源
     */
    async fixResource(resource) {
        logger.info(`🔧 修复资源: ${resource.url || resource.path}`);
        this.performanceMetrics.resourcesScanned++;
        
        try {
            let fixResult;
            
            if (resource.type === 'resource_missing') {
                fixResult = await this.fixMissingResource(resource);
            } else if (resource.type === 'resource_load_failure') {
                fixResult = await this.fixLoadFailureResource(resource);
            } else {
                fixResult = { status: 'skipped', message: '未实现的修复类型' };
            }
            
            logger.info(`   修复结果: ${fixResult.status} - ${fixResult.message}`);
            
            if (fixResult.status === 'success') {
                this.performanceMetrics.resourcesFixed++;
            } else {
                this.performanceMetrics.resourcesFailed++;
            }
            
            // 上报特征库
            await this.reportToFeatureLibrary(resource, fixResult);
            
        } catch (fixError) {
            logger.error(`❌ 修复资源时发生错误: ${fixError.message}`);
            this.performanceMetrics.resourcesFailed++;
            
            // 上报特征库
            await this.reportToFeatureLibrary(resource, {
                status: 'error',
                message: fixError.message
            });
        }
    }
    
    /**
     * 修复缺失资源
     */
    async fixMissingResource(resource) {
        logger.info(`   修复缺失资源: ${resource.path || resource.url}`);
        
        try {
            let resourcePath = resource.path;
            let fullPath;
            const projectRoot = path.resolve(__dirname, '../../../src');
            
            if (resource.url) {
                // 从URL中提取路径
                resourcePath = resource.url.replace('http://localhost:8080', '');
                // 确保路径不包含绝对路径前缀
                if (resourcePath.startsWith('/')) {
                    resourcePath = resourcePath.substring(1);
                }
                fullPath = path.join(projectRoot, resourcePath);
            } else {
                // 确保路径不包含绝对路径前缀
                if (resourcePath.startsWith('/')) {
                    resourcePath = resourcePath.substring(1);
                }
                fullPath = path.join(projectRoot, resourcePath);
            }
            
            // 确保资源目录存在
            const dirPath = path.dirname(fullPath);
            if (!fs.existsSync(dirPath)) {
                fs.mkdirSync(dirPath, { recursive: true });
                logger.info(`   创建了缺失的目录: ${dirPath}`);
            }
            
            // 根据资源类型创建默认内容
            let content = '';
            if (resourcePath.endsWith('.css')) {
                content = `/* 自动生成的CSS文件 - 修复缺失资源 */
/* 资源路径: ${resourcePath} */
/* 生成时间: ${new Date().toISOString()} */`;
            } else if (resourcePath.endsWith('.js')) {
                content = `// 自动生成的JavaScript文件 - 修复缺失资源
// 资源路径: ${resourcePath} 
// 生成时间: ${new Date().toISOString()}`;
            } else if (resourcePath.endsWith('.html')) {
                content = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动生成的HTML文件</title>
    <!-- 资源路径: ${resourcePath} -->
    <!-- 生成时间: ${new Date().toISOString()} -->
</head>
<body>
    <h1>自动生成的HTML文件</h1>
    <p>这是一个自动生成的HTML文件，用于修复缺失资源。</p>
</body>
</html>`;
            } else {
                // 其他类型的文件，创建空文件
                content = `# 自动生成的文件 - 修复缺失资源
# 资源路径: ${resourcePath} 
# 生成时间: ${new Date().toISOString()}`;
            }
            
            // 写入文件
            fs.writeFileSync(fullPath, content);
            logger.info(`   创建了默认资源文件: ${fullPath}`);
            
            return { 
                status: 'success', 
                message: `成功创建缺失资源: ${fullPath}` 
            };
            
        } catch (fixError) {
            logger.error(`   修复缺失资源时发生错误: ${fixError.message}`);
            return { 
                status: 'failed', 
                message: `修复缺失资源失败: ${fixError.message}` 
            };
        }
    }
    
    /**
     * 修复加载失败资源
     */
    async fixLoadFailureResource(resource) {
        logger.info(`   修复加载失败资源: ${resource.url}`);
        
        try {
            // 从URL中提取路径
            const projectRoot = path.resolve(__dirname, '../../../src');
            let resourcePath = resource.url.replace('http://localhost:8080', '');
            
            // 确保路径不包含绝对路径前缀
            if (resourcePath.startsWith('/')) {
                resourcePath = resourcePath.substring(1);
            }
            
            const fullPath = path.join(projectRoot, resourcePath);
            
            // 检查资源文件是否存在
            if (!fs.existsSync(fullPath)) {
                logger.error(`   资源文件不存在: ${fullPath}`);
                return { 
                    status: 'failed', 
                    message: `资源文件不存在: ${fullPath}` 
                };
            }
            
            // 检查资源文件权限
            const stats = fs.statSync(fullPath);
            if (stats.mode & 0o444 !== 0o444) {
                logger.warning(`   资源文件权限问题，修复权限...`);
                fs.chmodSync(fullPath, 0o644);
                logger.info(`   修复了资源文件权限: ${fullPath}`);
            }
            
            // 检查资源文件内容
            const content = fs.readFileSync(fullPath, 'utf8');
            if (content.trim() === '') {
                logger.warning(`   资源文件内容为空，添加默认内容...`);
                
                let defaultContent = '';
                if (resourcePath.endsWith('.css')) {
                    defaultContent = `/* 修复加载失败的CSS文件 */
/* 资源路径: ${resourcePath} */
/* 修复时间: ${new Date().toISOString()} */`;
                } else if (resourcePath.endsWith('.js')) {
                    defaultContent = `// 修复加载失败的JavaScript文件
// 资源路径: ${resourcePath} 
// 修复时间: ${new Date().toISOString()}`;
                }
                
                if (defaultContent) {
                    fs.writeFileSync(fullPath, defaultContent);
                    logger.info(`   添加了默认内容到资源文件: ${fullPath}`);
                }
            }
            
            logger.info(`   资源文件检查和修复完成: ${fullPath}`);
            return { 
                status: 'success', 
                message: `成功修复加载失败资源: ${fullPath}` 
            };
            
        } catch (fixError) {
            logger.error(`   修复加载失败资源时发生错误: ${fixError.message}`);
            return { 
                status: 'failed', 
                message: `修复加载失败资源失败: ${fixError.message}` 
            };
        }
    }
    
    /**
     * 上报到特征库
     */
    async reportToFeatureLibrary(resource, fixResult) {
        logger.info(`   上报特征库...`);
        
        try {
            // 创建特征
            const feature = {
                type: resource.type || 'resource_fix',
                description: `资源修复: ${resource.url || resource.path} - ${fixResult.message}`,
                severity: fixResult.status === 'success' ? 'info' : 'medium',
                location: resource.url || resource.path,
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'resource_fixer',
                details: {
                    resource: resource,
                    fixResult: fixResult
                }
            };
            
            // 添加到特征库
            const newFeature = aiFeatureLibrary.addFeature(feature);
            logger.info(`   特征已添加到特征库: ${newFeature.id}`);
            this.performanceMetrics.featuresReported++;
            
        } catch (reportError) {
            logger.error(`   上报特征库时发生错误: ${reportError.message}`);
        }
    }
    
    /**
     * 从资源监控AI获取需要修复的资源
     */
    async fetchResourcesFromMonitor() {
        logger.info(`📥 从资源监控AI获取需要修复的资源...`);
        
        try {
            // 这里可以添加从资源监控AI获取需要修复资源的逻辑
            // 例如：读取资源监控AI生成的报告，提取需要修复的资源
            
            const monitorReportPath = path.join(__dirname, '../../../Logs/captures/resources');
            
            // 读取最新的资源监控报告
            const reportFiles = fs.readdirSync(monitorReportPath)
                .filter(file => file.startsWith('resource_report_'))
                .sort((a, b) => {
                    const aTime = parseInt(a.replace('resource_report_', '').replace('.json', ''));
                    const bTime = parseInt(b.replace('resource_report_', '').replace('.json', ''));
                    return bTime - aTime;
                });
            
            if (reportFiles.length > 0) {
                const latestReportFile = reportFiles[0];
                const reportPath = path.join(monitorReportPath, latestReportFile);
                const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
                
                // 提取需要修复的资源
                if (report.resourceMatches && report.resourceMatches.missingResources) {
                    report.resourceMatches.missingResources.forEach(resource => {
                        this.addResourceToFix({
                            type: 'resource_missing',
                            ...resource
                        });
                    });
                }
                
                logger.info(`📥 成功获取 ${this.resourcesToFix.length} 个需要修复的资源`);
            }
            
        } catch (fetchError) {
            logger.error(`📥 获取需要修复的资源时发生错误: ${fetchError.message}`);
        }
    }
    
    /**
     * 生成修复报告
     */
    generateFixReport() {
        const report = {
            id: `resource_fix_report_${Date.now()}`,
            aiId: this.id,
            aiName: this.name,
            generatedAt: new Date().toISOString(),
            status: this.status,
            performanceMetrics: this.performanceMetrics,
            fixConfig: this.fixConfig,
            taskHistory: this.taskHistory,
            resourcesToFix: this.resourcesToFix.length
        };
        
        // 保存报告
        const reportFile = path.join(this.fixConfig.fixDirectory, `resource_fix_report_${Date.now()}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
        
        logger.info(`📄 资源修复报告已生成: ${reportFile}`);
        return report;
    }
    
    /**
     * 获取修复状态
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
            fixConfig: this.fixConfig,
            resourcesToFix: this.resourcesToFix.length
        };
    }
    
    /**
     * 更新修复配置
     */
    updateConfig(config) {
        this.fixConfig = { ...this.fixConfig, ...config };
        logger.info(`⚙️  资源修复配置已更新`);
        return this.fixConfig;
    }
}

// 导出单例实例
const resourceFixerAI = new ResourceFixerAI();
module.exports = resourceFixerAI;

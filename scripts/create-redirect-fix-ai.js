#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - 重定向修复子AI创建脚本
 * 用于检测和修复HTTP自动重定向到HTTPS的问题
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 定义项目根目录
const projectRoot = path.join(__dirname, '..');

// 错误特征数据库路径
const errorFeatureDbPath = path.join(projectRoot, 'src', 'data', 'error-feature-db.json');

// 创建AI实例类
class AIInstance {
    constructor(name, role, group, type, level) {
        this.id = `ai_${crypto.randomBytes(16).toString('hex')}`;
        this.name = name;
        this.role = role;
        this.group = group;
        this.type = type;
        this.level = level;
        this.createdAt = new Date().toISOString();
        this.status = 'idle';
        this.features = [];
    }

    // 检测重定向问题
    async detectRedirectIssue() {
        console.log(`[${this.name}] 开始检测重定向问题...`);
        
        // 1. 检查app.js中的配置
        const appConfigIssues = await this.checkAppConfig();
        
        // 2. 检查.htaccess文件
        const htaccessIssues = await this.checkHtaccess();
        
        // 3. 检查index.html中的URL配置
        const htmlIssues = await this.checkHtmlConfig();
        
        // 合并所有问题
        const allIssues = [...appConfigIssues, ...htaccessIssues, ...htmlIssues];
        
        console.log(`[${this.name}] 检测完成，发现 ${allIssues.length} 个问题`);
        return allIssues;
    }

    // 检查app.js配置
    async checkAppConfig() {
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        const appContent = fs.readFileSync(appFilePath, 'utf8');
        const issues = [];

        // 检查是否有HTTPS相关配置
        if (appContent.includes('https.createServer')) {
            issues.push({
                type: 'HTTPS_CONFIG',
                severity: 'high',
                description: 'app.js中存在HTTPS服务器创建代码',
                file: 'src/app.js',
                fixable: true
            });
        }

        // 检查helmet配置
        if (appContent.includes('helmet') && !appContent.includes('hsts: false')) {
            issues.push({
                type: 'HSTS_CONFIG',
                severity: 'medium',
                description: 'helmet中间件未禁用HSTS',
                file: 'src/app.js',
                fixable: true
            });
        }

        return issues;
    }

    // 检查.htaccess文件
    async checkHtaccess() {
        const htaccessPath = path.join(projectRoot, 'src', 'html', '.htaccess');
        if (!fs.existsSync(htaccessPath)) {
            return [];
        }

        const htaccessContent = fs.readFileSync(htaccessPath, 'utf8');
        const issues = [];

        // 检查HSTS配置
        if (htaccessContent.includes('Strict-Transport-Security') && 
            !htaccessContent.includes('# Header always set Strict-Transport-Security')) {
            issues.push({
                type: 'HSTS_HTACCESS',
                severity: 'medium',
                description: '.htaccess中存在启用的HSTS配置',
                file: 'src/html/.htaccess',
                fixable: true
            });
        }

        // 检查重定向规则
        if (htaccessContent.includes('RewriteRule') && 
            htaccessContent.includes('https')) {
            issues.push({
                type: 'REDIRECT_RULES',
                severity: 'high',
                description: '.htaccess中存在HTTPS重定向规则',
                file: 'src/html/.htaccess',
                fixable: true
            });
        }

        return issues;
    }

    // 检查HTML文件配置
    async checkHtmlConfig() {
        const htmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
        const htmlContent = fs.readFileSync(htmlPath, 'utf8');
        const issues = [];

        // 检查WebSocket连接
        if (htmlContent.includes('wss://')) {
            issues.push({
                type: 'WS_URL',
                severity: 'medium',
                description: 'index.html中存在WSS连接配置',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        // 检查API请求URL
        if (htmlContent.includes('https://localhost')) {
            issues.push({
                type: 'API_URL',
                severity: 'medium',
                description: 'index.html中存在HTTPS API请求配置',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        return issues;
    }

    // 修复重定向问题
    async fixRedirectIssue(issues) {
        console.log(`[${this.name}] 开始修复 ${issues.length} 个问题...`);
        const fixedIssues = [];

        for (const issue of issues) {
            try {
                switch (issue.type) {
                    case 'HTTPS_CONFIG':
                        await this.fixHttpsConfig();
                        break;
                    case 'HSTS_CONFIG':
                        await this.fixHstsConfig();
                        break;
                    case 'HSTS_HTACCESS':
                        await this.fixHstsHtaccess();
                        break;
                    case 'REDIRECT_RULES':
                        await this.fixRedirectRules();
                        break;
                    case 'WS_URL':
                        await this.fixWsUrl();
                        break;
                    case 'API_URL':
                        await this.fixApiUrl();
                        break;
                    default:
                        console.log(`[${this.name}] 无法修复未知类型问题: ${issue.type}`);
                        continue;
                }
                fixedIssues.push(issue);
                console.log(`[${this.name}] 修复完成: ${issue.description}`);
            } catch (error) {
                console.error(`[${this.name}] 修复失败: ${issue.description}`, error);
            }
        }

        console.log(`[${this.name}] 修复完成，成功修复 ${fixedIssues.length}/${issues.length} 个问题`);
        return fixedIssues;
    }

    // 修复app.js中的HTTPS配置
    async fixHttpsConfig() {
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appFilePath, 'utf8');

        // 确保只使用HTTP服务器
        const httpsCreateServerPattern = /const backupServer = https\.createServer\(options, app\);/g;
        if (httpsCreateServerPattern.test(appContent)) {
            appContent = appContent.replace(httpsCreateServerPattern, 'const backupServer = http.createServer(app);');
        }

        // 确保没有使用https模块
        const httpsModulePattern = /const https = require\('https'\);/g;
        if (httpsModulePattern.test(appContent)) {
            appContent = appContent.replace(httpsModulePattern, '');
        }

        fs.writeFileSync(appFilePath, appContent);
    }

    // 修复helmet的HSTS配置
    async fixHstsConfig() {
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appFilePath, 'utf8');

        // 确保helmet配置中禁用HSTS
        const helmetPattern = /app\.use\(helmet\(([^)]+)\)\);/s;
        const match = appContent.match(helmetPattern);
        
        if (match && match[1]) {
            let helmetConfig = match[1];
            if (!helmetConfig.includes('hsts: false')) {
                // 添加hsts: false配置
                if (helmetConfig.trim().endsWith('}')) {
                    helmetConfig = helmetConfig.trim().slice(0, -1);
                    helmetConfig += ',\n    hsts: false\n';
                } else {
                    helmetConfig += '\n    hsts: false';
                }
                helmetConfig += '}';
                
                appContent = appContent.replace(helmetPattern, `app.use(helmet(${helmetConfig}));`);
                fs.writeFileSync(appFilePath, appContent);
            }
        }
    }

    // 修复.htaccess中的HSTS配置
    async fixHstsHtaccess() {
        const htaccessPath = path.join(projectRoot, 'src', 'html', '.htaccess');
        if (fs.existsSync(htaccessPath)) {
            let htaccessContent = fs.readFileSync(htaccessPath, 'utf8');
            
            // 注释掉HSTS头配置
            const hstsPattern = /Header always set Strict-Transport-Security/g;
            if (hstsPattern.test(htaccessContent)) {
                htaccessContent = htaccessContent.replace(hstsPattern, '# Header always set Strict-Transport-Security');
                fs.writeFileSync(htaccessPath, htaccessContent);
            }
        }
    }

    // 修复重定向规则
    async fixRedirectRules() {
        const htaccessPath = path.join(projectRoot, 'src', 'html', '.htaccess');
        if (fs.existsSync(htaccessPath)) {
            let htaccessContent = fs.readFileSync(htaccessPath, 'utf8');
            
            // 移除所有HTTPS重定向规则
            const redirectPattern = /RewriteRule.*https:/g;
            if (redirectPattern.test(htaccessContent)) {
                htaccessContent = htaccessContent.replace(redirectPattern, '# RewriteRule (HTTPS重定向已禁用)');
                fs.writeFileSync(htaccessPath, htaccessContent);
            }
        }
    }

    // 修复WebSocket URL
    async fixWsUrl() {
        const htmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
        let htmlContent = fs.readFileSync(htmlPath, 'utf8');
        
        // 将wss://替换为ws://
        htmlContent = htmlContent.replace(/wss:\/\//g, 'ws://');
        fs.writeFileSync(htmlPath, htmlContent);
    }

    // 修复API URL
    async fixApiUrl() {
        const htmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
        let htmlContent = fs.readFileSync(htmlPath, 'utf8');
        
        // 将https://localhost替换为http://localhost
        htmlContent = htmlContent.replace(/https:\/\/localhost/g, 'http://localhost');
        fs.writeFileSync(htmlPath, htmlContent);
    }

    // 验证修复结果
    async verifyFix() {
        console.log(`[${this.name}] 开始验证修复结果...`);
        
        // 重新检测问题
        const remainingIssues = await this.detectRedirectIssue();
        
        if (remainingIssues.length === 0) {
            console.log(`[${this.name}] 修复验证通过！所有重定向问题已解决`);
            return true;
        } else {
            console.log(`[${this.name}] 修复验证失败，仍有 ${remainingIssues.length} 个问题未解决`);
            remainingIssues.forEach(issue => {
                console.log(`  - ${issue.description}`);
            });
            return false;
        }
    }

    // 生成错误特征
    generateErrorFeature(issues) {
        console.log(`[${this.name}] 生成错误特征...`);
        
        const feature = {
            id: `feature_${Date.now()}`,
            type: 'redirect_issue',
            name: 'HTTP自动重定向到HTTPS',
            description: '客户端输入HTTP URL时自动重定向到HTTPS',
            severity: 'high',
            pattern: {
                appConfigIssues: issues.filter(issue => issue.file === 'src/app.js').length,
                htaccessIssues: issues.filter(issue => issue.file === 'src/html/.htaccess').length,
                htmlIssues: issues.filter(issue => issue.file === 'src/html/index.html').length
            },
            detectionMethod: 'static_analysis',
            fixActions: [
                '禁用helmet中间件的HSTS配置',
                '移除app.js中的HTTPS服务器配置',
                '注释.htaccess中的HSTS头',
                '移除.htaccess中的HTTPS重定向规则',
                '将index.html中的wss://替换为ws://',
                '将index.html中的https://localhost替换为http://localhost'
            ],
            solution: '完全移除HTTPS支持，仅使用HTTP',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            aiId: this.id
        };
        
        this.features.push(feature);
        return feature;
    }

    // 上传特征到数据库
    async uploadToFeatureLibrary(feature) {
        console.log(`[${this.name}] 上传特征到错误特征数据库...`);
        
        try {
            // 读取现有数据库
            let featureDb = [];
            if (fs.existsSync(errorFeatureDbPath)) {
                const existingContent = fs.readFileSync(errorFeatureDbPath, 'utf8');
                if (existingContent.trim()) {
                    featureDb = JSON.parse(existingContent);
                }
            }
            
            // 检查特征是否已存在
            const existingFeatureIndex = featureDb.findIndex(f => f.type === feature.type);
            if (existingFeatureIndex >= 0) {
                // 更新现有特征
                featureDb[existingFeatureIndex] = feature;
                console.log(`[${this.name}] 特征已存在，已更新`);
            } else {
                // 添加新特征
                featureDb.push(feature);
                console.log(`[${this.name}] 新特征已添加`);
            }
            
            // 写入数据库
            fs.writeFileSync(errorFeatureDbPath, JSON.stringify(featureDb, null, 2));
            console.log(`[${this.name}] 特征上传完成`);
            return true;
        } catch (error) {
            console.error(`[${this.name}] 特征上传失败:`, error);
            return false;
        }
    }

    // 完整修复流程
    async fullFixFlow() {
        console.log(`\n[${this.name}] 开始完整修复流程...`);
        
        this.status = 'working';
        
        try {
            // 1. 检测问题
            const issues = await this.detectRedirectIssue();
            
            if (issues.length === 0) {
                console.log(`[${this.name}] 未发现重定向问题`);
                this.status = 'idle';
                return { success: true, issues: [], fixed: 0 };
            }
            
            // 2. 修复问题
            const fixedIssues = await this.fixRedirectIssue(issues);
            
            // 3. 验证修复
            const verificationResult = await this.verifyFix();
            
            // 4. 生成并上传特征
            const feature = this.generateErrorFeature(issues);
            await this.uploadToFeatureLibrary(feature);
            
            this.status = 'idle';
            
            return {
                success: verificationResult,
                issues: issues,
                fixed: fixedIssues.length,
                feature: feature
            };
        } catch (error) {
            console.error(`[${this.name}] 修复流程失败:`, error);
            this.status = 'error';
            throw error;
        }
    }
}

// 创建重定向修复AI
function createRedirectFixAI() {
    console.log('正在创建重定向修复子AI...');
    
    // 创建AI实例
    const redirectFixAI = new AIInstance(
        'RedirectFixAI',
        'client_exception',
        'monitoring',
        'module',
        'application'
    );
    
    console.log(`成功创建AI实例: ${redirectFixAI.name}`);
    console.log(`AI ID: ${redirectFixAI.id}`);
    console.log(`角色: ${redirectFixAI.role}`);
    console.log(`组: ${redirectFixAI.group}`);
    
    return redirectFixAI;
}

// 主函数
async function main() {
    console.log('========================================');
    console.log('MTSCOS AI 项目 - 重定向修复子AI创建脚本');
    console.log('========================================');
    
    try {
        // 1. 创建AI实例
        const redirectFixAI = createRedirectFixAI();
        
        // 2. 执行完整修复流程
        const fixResult = await redirectFixAI.fullFixFlow();
        
        // 3. 输出修复报告
        console.log('\n========================================');
        console.log('修复报告');
        console.log('========================================');
        console.log(`修复状态: ${fixResult.success ? '成功' : '失败'}`);
        console.log(`检测到问题: ${fixResult.issues.length}`);
        console.log(`成功修复: ${fixResult.fixed}`);
        
        if (fixResult.feature) {
            console.log(`特征ID: ${fixResult.feature.id}`);
            console.log(`特征名称: ${fixResult.feature.name}`);
        }
        
        if (fixResult.success) {
            if (fixResult.issues.length === 0) {
                console.log('\n🎉 未检测到重定向问题，系统配置正确！');
            } else {
                console.log('\n🎉 所有重定向问题已成功修复！');
                console.log('📋 修复内容已上传到错误特征数据库');
                console.log('\n建议：');
                console.log('1. 重启服务器以应用所有更改');
                console.log('2. 清除浏览器缓存后测试');
                console.log('3. 访问 http://localhost:8080 验证修复效果');
            }
        } else {
            console.log('\n⚠️  修复未完全成功，请手动检查剩余问题');
        }
        
        process.exit(0);
    } catch (error) {
        console.error('\n❌ 脚本执行失败:', error);
        process.exit(1);
    }
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = {
    createRedirectFixAI,
    AIInstance
};
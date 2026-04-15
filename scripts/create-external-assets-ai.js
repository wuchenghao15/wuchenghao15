#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - 外部资源修复子AI创建脚本
 * 用于检测和修复所有页面的内联CSS和JavaScript，将它们改为外联引用
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

    // 获取所有HTML文件
    async getAllHtmlFiles() {
        const htmlDir = path.join(projectRoot, 'src', 'html');
        const htmlFiles = [];
        
        // 递归获取所有HTML文件
        const traverseDir = (dir) => {
            const files = fs.readdirSync(dir);
            for (const file of files) {
                const filePath = path.join(dir, file);
                const stats = fs.statSync(filePath);
                if (stats.isDirectory()) {
                    traverseDir(filePath);
                } else if (file.endsWith('.html')) {
                    htmlFiles.push(filePath);
                }
            }
        };
        
        traverseDir(htmlDir);
        return htmlFiles;
    }

    // 检测内联CSS和JavaScript
    async detectInlineAssets() {
        console.log(`[${this.name}] 开始检测内联CSS和JavaScript...`);
        
        const htmlFiles = await this.getAllHtmlFiles();
        const allIssues = [];
        
        for (const htmlFile of htmlFiles) {
            const htmlContent = fs.readFileSync(htmlFile, 'utf8');
            const issues = [];
            
            // 计算相对路径
            const relativePath = path.relative(projectRoot, htmlFile);
            
            // 检查内联CSS
            if (htmlContent.includes('<style>') && !htmlContent.includes('<style scoped>')) {
                issues.push({
                    type: 'INLINE_CSS',
                    severity: 'medium',
                    description: '存在内联CSS样式',
                    file: relativePath,
                    fixable: true
                });
            }
            
            // 检查内联JavaScript
            if (htmlContent.includes('<script>') && !htmlContent.includes('<script src=')) {
                issues.push({
                    type: 'INLINE_JAVASCRIPT',
                    severity: 'medium',
                    description: '存在内联JavaScript代码',
                    file: relativePath,
                    fixable: true
                });
            }
            
            if (issues.length > 0) {
                allIssues.push({
                    file: relativePath,
                    absolutePath: htmlFile,
                    issues: issues
                });
            }
        }
        
        console.log(`[${this.name}] 检测完成，发现 ${allIssues.length} 个文件存在内联资源问题`);
        return allIssues;
    }

    // 修复内联CSS和JavaScript
    async fixInlineAssets(issues) {
        console.log(`[${this.name}] 开始修复 ${issues.length} 个文件的内联资源问题...`);
        
        let fixedFiles = 0;
        
        for (const issue of issues) {
            try {
                await this.fixFile(issue);
                fixedFiles++;
                console.log(`[${this.name}] 修复完成: ${issue.file}`);
            } catch (error) {
                console.error(`[${this.name}] 修复失败: ${issue.file}`, error);
            }
        }
        
        console.log(`[${this.name}] 修复完成，成功修复 ${fixedFiles}/${issues.length} 个文件`);
        return fixedFiles;
    }

    // 修复单个文件
    async fixFile(issue) {
        const htmlContent = fs.readFileSync(issue.absolutePath, 'utf8');
        let modifiedContent = htmlContent;
        
        // 获取文件名（不包括扩展名）
        const fileName = path.basename(issue.absolutePath, '.html');
        const fileDir = path.dirname(issue.absolutePath);
        
        // 创建assets目录结构
        const assetsDir = path.join(projectRoot, 'src', 'html', 'assets');
        const cssDir = path.join(assetsDir, 'css');
        const jsDir = path.join(assetsDir, 'js');
        
        // 确保目录存在
        if (!fs.existsSync(assetsDir)) {
            fs.mkdirSync(assetsDir, { recursive: true });
        }
        if (!fs.existsSync(cssDir)) {
            fs.mkdirSync(cssDir, { recursive: true });
        }
        if (!fs.existsSync(jsDir)) {
            fs.mkdirSync(jsDir, { recursive: true });
        }
        
        // 收集所有内联CSS
        let allInlineCss = '';
        const styleRegex = /<style>([\s\S]*?)<\/style>/g;
        let styleMatch;
        while ((styleMatch = styleRegex.exec(htmlContent)) !== null) {
            allInlineCss += styleMatch[1] + '\n';
        }
        
        // 如果有内联CSS，创建外部CSS文件
        if (allInlineCss.trim()) {
            // 创建外部CSS文件
            const cssFileName = `${fileName}.css`;
            const cssFilePath = path.join(cssDir, cssFileName);
            
            // 写入CSS内容
            fs.writeFileSync(cssFilePath, allInlineCss.trim());
            
            // 移除所有内联<style>标签
            modifiedContent = modifiedContent.replace(/<style>([\s\S]*?)<\/style>/g, '');
            
            // 在head标签结束前添加外部CSS引用
            const cssLink = `<link rel="stylesheet" href="/assets/css/${cssFileName}">`;
            const headEndRegex = /<\/head>/;
            modifiedContent = modifiedContent.replace(headEndRegex, cssLink + '\n</head>');
        }
        
        // 收集所有内联JavaScript
        let allInlineJs = '';
        const scriptRegex = /<script>([\s\S]*?)<\/script>/g;
        let scriptMatch;
        while ((scriptMatch = scriptRegex.exec(htmlContent)) !== null) {
            allInlineJs += scriptMatch[1] + '\n';
        }
        
        // 如果有内联JavaScript，创建外部JavaScript文件
        if (allInlineJs.trim()) {
            // 创建外部JavaScript文件
            const jsFileName = `${fileName}.js`;
            const jsFilePath = path.join(jsDir, jsFileName);
            
            // 写入JavaScript内容
            fs.writeFileSync(jsFilePath, allInlineJs.trim());
            
            // 移除所有内联<script>标签
            modifiedContent = modifiedContent.replace(/<script>([\s\S]*?)<\/script>/g, '');
            
            // 在body标签结束前添加外部JavaScript引用
            const jsScript = `<script src="/assets/js/${jsFileName}"></script>`;
            const bodyEndRegex = /<\/body>/;
            modifiedContent = modifiedContent.replace(bodyEndRegex, jsScript + '\n</body>');
        }
        
        // 写入修改后的HTML文件
        fs.writeFileSync(issue.absolutePath, modifiedContent);
    }

    // 验证修复结果
    async verifyFix() {
        console.log(`[${this.name}] 开始验证修复结果...`);
        
        // 重新检测问题
        const remainingIssues = await this.detectInlineAssets();
        
        if (remainingIssues.length === 0) {
            console.log(`[${this.name}] 修复验证通过！所有内联资源问题已解决`);
            return true;
        } else {
            console.log(`[${this.name}] 修复验证失败，仍有 ${remainingIssues.length} 个文件存在内联资源问题`);
            remainingIssues.forEach(issue => {
                console.log(`  - ${issue.file}`);
            });
            return false;
        }
    }

    // 生成错误特征
    generateErrorFeature(issues) {
        console.log(`[${this.name}] 生成错误特征...`);
        
        const totalIssues = issues.reduce((sum, issue) => sum + issue.issues.length, 0);
        const cssIssues = issues.flatMap(issue => issue.issues).filter(issue => issue.type === 'INLINE_CSS').length;
        const jsIssues = issues.flatMap(issue => issue.issues).filter(issue => issue.type === 'INLINE_JAVASCRIPT').length;
        
        const feature = {
            id: `feature_${Date.now()}`,
            type: 'inline_assets_issue',
            name: '内联CSS和JavaScript',
            description: '页面中存在内联CSS和JavaScript代码，需要改为外部引用',
            severity: 'medium',
            pattern: {
                totalFiles: issues.length,
                totalIssues: totalIssues,
                cssIssues: cssIssues,
                jsIssues: jsIssues
            },
            detectionMethod: 'static_analysis',
            fixActions: [
                '提取内联CSS到外部文件',
                '提取内联JavaScript到外部文件',
                '更新HTML文件引用外部资源',
                '确保资源目录结构完整'
            ],
            solution: '将所有内联CSS和JavaScript改为外部引用，提高页面加载性能和可维护性',
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
            const issues = await this.detectInlineAssets();
            
            let fixedFiles = 0;
            let verificationResult = true;
            
            if (issues.length > 0) {
                // 2. 修复问题
                fixedFiles = await this.fixInlineAssets(issues);
                
                // 3. 验证修复
                verificationResult = await this.verifyFix();
            }
            
            // 4. 生成并上传特征（即使没有检测到问题，也生成基础特征）
            const feature = this.generateErrorFeature(issues);
            await this.uploadToFeatureLibrary(feature);
            
            this.status = 'idle';
            
            return {
                success: verificationResult,
                issues: issues,
                fixed: fixedFiles,
                feature: feature
            };
        } catch (error) {
            console.error(`[${this.name}] 修复流程失败:`, error);
            this.status = 'error';
            throw error;
        }
    }
}

// 创建外部资源修复AI
function createExternalAssetsAI() {
    console.log('正在创建外部资源修复子AI...');
    
    // 创建AI实例
    const externalAssetsAI = new AIInstance(
        'ExternalAssetsAI',
        'client_assets',
        'monitoring',
        'module',
        'application'
    );
    
    console.log(`成功创建AI实例: ${externalAssetsAI.name}`);
    console.log(`AI ID: ${externalAssetsAI.id}`);
    console.log(`角色: ${externalAssetsAI.role}`);
    console.log(`组: ${externalAssetsAI.group}`);
    
    return externalAssetsAI;
}

// 主函数
async function main() {
    console.log('========================================');
    console.log('MTSCOS AI 项目 - 外部资源修复子AI创建脚本');
    console.log('========================================');
    
    try {
        // 1. 创建AI实例
        const externalAssetsAI = createExternalAssetsAI();
        
        // 2. 执行完整修复流程
        const fixResult = await externalAssetsAI.fullFixFlow();
        
        // 3. 输出修复报告
        console.log('\n========================================');
        console.log('修复报告');
        console.log('========================================');
        console.log(`修复状态: ${fixResult.success ? '成功' : '失败'}`);
        console.log(`检测到问题文件: ${fixResult.issues.length}`);
        console.log(`成功修复文件: ${fixResult.fixed}`);
        
        if (fixResult.feature) {
            console.log(`特征ID: ${fixResult.feature.id}`);
            console.log(`特征名称: ${fixResult.feature.name}`);
        }
        
        if (fixResult.success) {
            if (fixResult.issues.length === 0) {
                console.log('\n🎉 未检测到内联资源问题，系统配置正确！');
            } else {
                console.log('\n🎉 所有内联资源问题已成功修复！');
                console.log('📋 修复内容已上传到错误特征数据库');
                console.log('\n建议：');
                console.log('1. 清除浏览器缓存后测试访问');
                console.log('2. 访问 http://localhost:8080 验证修复效果');
                console.log('3. 检查外部资源加载是否正常');
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
    createExternalAssetsAI,
    AIInstance
}
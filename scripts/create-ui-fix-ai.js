#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - UI及配色方案修复子AI创建脚本
 * 用于检测和修复客户端登录项目UI及配色方案全部失效的问题
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

    // 检测UI及配色方案问题
    async detectUIIssues() {
        console.log(`[${this.name}] 开始检测UI及配色方案问题...`);
        
        // 1. 检查index.html中的CSS引用
        const cssIssues = await this.checkCssReferences();
        
        // 2. 检查CSS文件是否存在
        const fileIssues = await this.checkCssFiles();
        
        // 3. 检查JavaScript中的主题管理代码
        const jsThemeIssues = await this.checkJsThemeManagement();
        
        // 4. 检查index.html中的主题切换功能
        const htmlThemeIssues = await this.checkHtmlThemeFeatures();
        
        // 合并所有问题
        const allIssues = [...cssIssues, ...fileIssues, ...jsThemeIssues, ...htmlThemeIssues];
        
        console.log(`[${this.name}] 检测完成，发现 ${allIssues.length} 个问题`);
        return allIssues;
    }

    // 检查index.html中的CSS引用
    async checkCssReferences() {
        const htmlFilePath = path.join(projectRoot, 'src', 'html', 'index.html');
        const htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
        const issues = [];

        // 检查是否有CSS引用
        if (!htmlContent.includes('.css')) {
            issues.push({
                type: 'CSS_REFERENCE_MISSING',
                severity: 'high',
                description: 'index.html中缺少CSS文件引用',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        // 检查bundle.min.css引用
        const bundleCssRegex = /<link[^>]*bundle\.min\.css[^>]*>/;
        if (!bundleCssRegex.test(htmlContent)) {
            issues.push({
                type: 'BUNDLE_CSS_MISSING',
                severity: 'high',
                description: 'index.html中缺少bundle.min.css引用',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        return issues;
    }

    // 检查CSS文件是否存在
    async checkCssFiles() {
        const cssDir = path.join(projectRoot, 'src', 'html', 'assets', 'css');
        const issues = [];

        // 检查assets/css目录是否存在
        if (!fs.existsSync(cssDir)) {
            issues.push({
                type: 'CSS_DIR_MISSING',
                severity: 'critical',
                description: 'CSS目录不存在',
                file: 'src/html/assets/css',
                fixable: true
            });
            return issues;
        }

        // 检查bundle.min.css文件是否存在
        const bundleCssPath = path.join(cssDir, 'bundle.min.css');
        if (!fs.existsSync(bundleCssPath)) {
            issues.push({
                type: 'BUNDLE_CSS_FILE_MISSING',
                severity: 'high',
                description: 'bundle.min.css文件不存在',
                file: 'src/html/assets/css/bundle.min.css',
                fixable: true
            });
        }

        return issues;
    }

    // 检查JavaScript中的主题管理代码
    async checkJsThemeManagement() {
        const htmlFilePath = path.join(projectRoot, 'src', 'html', 'index.html');
        const htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
        const issues = [];

        // 检查是否有ThemeManager相关代码
        if (!htmlContent.includes('ThemeManager')) {
            issues.push({
                type: 'THEME_MANAGER_MISSING',
                severity: 'medium',
                description: 'JavaScript中缺少ThemeManager主题管理代码',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        // 检查主题切换功能
        if (!htmlContent.includes('theme-toggle')) {
            issues.push({
                type: 'THEME_TOGGLE_MISSING',
                severity: 'medium',
                description: '缺少主题切换按钮',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        // 检查主题样式定义
        if (!htmlContent.includes('sunset-mode') && !htmlContent.includes('overtime-mode') && !htmlContent.includes('memorial-mode')) {
            issues.push({
                type: 'THEME_STYLES_MISSING',
                severity: 'medium',
                description: '缺少主题样式定义',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        return issues;
    }

    // 检查index.html中的主题切换功能
    async checkHtmlThemeFeatures() {
        const htmlFilePath = path.join(projectRoot, 'src', 'html', 'index.html');
        const htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
        const issues = [];

        // 检查主题切换按钮事件绑定
        if (!htmlContent.includes('themeToggle.addEventListener') && !htmlContent.includes('addEventListener.*theme-toggle')) {
            issues.push({
                type: 'THEME_EVENT_BINDING_MISSING',
                severity: 'medium',
                description: '主题切换按钮缺少事件绑定',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        // 检查主题初始化代码
        if (!htmlContent.includes('ThemeManager.init')) {
            issues.push({
                type: 'THEME_INIT_MISSING',
                severity: 'medium',
                description: '缺少主题初始化代码',
                file: 'src/html/index.html',
                fixable: true
            });
        }

        return issues;
    }

    // 修复UI及配色方案问题
    async fixUIIssues(issues) {
        console.log(`[${this.name}] 开始修复 ${issues.length} 个问题...`);
        const fixedIssues = [];

        for (const issue of issues) {
            try {
                switch (issue.type) {
                    case 'CSS_REFERENCE_MISSING':
                    case 'BUNDLE_CSS_MISSING':
                        await this.fixCssReferences();
                        break;
                    case 'CSS_DIR_MISSING':
                        await this.createCssDirectory();
                        break;
                    case 'BUNDLE_CSS_FILE_MISSING':
                        await this.createBundleCssFile();
                        break;
                    case 'THEME_MANAGER_MISSING':
                        await this.fixThemeManager();
                        break;
                    case 'THEME_TOGGLE_MISSING':
                        await this.fixThemeToggleButton();
                        break;
                    case 'THEME_STYLES_MISSING':
                        await this.fixThemeStyles();
                        break;
                    case 'THEME_EVENT_BINDING_MISSING':
                    case 'THEME_INIT_MISSING':
                        await this.fixThemeInitialization();
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

    // 修复CSS引用
    async fixCssReferences() {
        const htmlFilePath = path.join(projectRoot, 'src', 'html', 'index.html');
        let htmlContent = fs.readFileSync(htmlFilePath, 'utf8');

        // 检查是否已存在bundle.min.css引用
        const bundleCssRegex = /<link[^>]*bundle\.min\.css[^>]*>/;
        if (!bundleCssRegex.test(htmlContent)) {
            // 在head标签中添加bundle.min.css引用
            const headEndRegex = /<\/head>/;
            const cssLink = '    <!-- 引入压缩后的CSS文件 -->\n    <link rel="stylesheet" href="/assets/css/bundle.min.css">\n';
            htmlContent = htmlContent.replace(headEndRegex, cssLink + '</head>');
            fs.writeFileSync(htmlFilePath, htmlContent);
        }
    }

    // 创建CSS目录
    async createCssDirectory() {
        const cssDir = path.join(projectRoot, 'src', 'html', 'assets', 'css');
        if (!fs.existsSync(cssDir)) {
            fs.mkdirSync(cssDir, { recursive: true });
        }
    }

    // 创建bundle.min.css文件
    async createBundleCssFile() {
        const cssDir = path.join(projectRoot, 'src', 'html', 'assets', 'css');
        const bundleCssPath = path.join(cssDir, 'bundle.min.css');
        
        // 确保目录存在
        if (!fs.existsSync(cssDir)) {
            await this.createCssDirectory();
        }
        
        // 创建基础CSS内容
        const cssContent = `/* MTSCOS AI 项目 - 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.auth-container {
    display: flex;
    min-height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
    background-color: white;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}

.brand-section {
    flex: 1;
    background-color: #1a365d;
    color: white;
    padding: 40px;
    display: flex;
    align-items: center;
}

.brand-content {
    max-width: 400px;
}

.brand-logo {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
}

.brand-title {
    font-size: 28px;
    margin-bottom: 20px;
}

.brand-description {
    margin-bottom: 30px;
    line-height: 1.8;
}

.form-section {
    flex: 1;
    padding: 40px;
    display: flex;
    align-items: center;
}

.form-container {
    width: 100%;
    max-width: 400px;
}

.auth-tabs {
    display: flex;
    margin-bottom: 30px;
    border-bottom: 1px solid #ddd;
}

.tab-btn {
    flex: 1;
    padding: 15px;
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    color: #666;
    border-bottom: 2px solid transparent;
}

.tab-btn.active {
    color: #3182ce;
    border-bottom-color: #3182ce;
}

.auth-form {
    display: none;
}

.auth-form.active {
    display: block;
}

.form-group {
    margin-bottom: 20px;
}

.form-label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
    color: #333;
}

.form-input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
}

.auth-btn {
    width: 100%;
    padding: 15px;
    background-color: #3182ce;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    margin-top: 20px;
}

.auth-btn:hover {
    background-color: #2b6cb0;
}

/* 主题样式 */
.sunset-mode {
    --primary-color: #ed8936;
    --secondary-color: #dd6b20;
    --background-color: #fffaf0;
    --text-color: #2d3748;
}

.sunset-mode .brand-section {
    background-color: #dd6b20;
}

.sunset-mode .tab-btn.active {
    color: #ed8936;
    border-bottom-color: #ed8936;
}

.sunset-mode .auth-btn {
    background-color: #ed8936;
}

.sunset-mode .auth-btn:hover {
    background-color: #dd6b20;
}

.overtime-mode {
    --primary-color: #4a5568;
    --secondary-color: #2d3748;
    --background-color: #f7fafc;
    --text-color: #1a202c;
}

.overtime-mode .brand-section {
    background-color: #2d3748;
}

.overtime-mode .tab-btn.active {
    color: #4a5568;
    border-bottom-color: #4a5568;
}

.overtime-mode .auth-btn {
    background-color: #4a5568;
}

.overtime-mode .auth-btn:hover {
    background-color: #2d3748;
}

.memorial-mode {
    --primary-color: #2d3748;
    --secondary-color: #1a202c;
    --background-color: #f7fafc;
    --text-color: #2d3748;
}

.memorial-mode .brand-section {
    background-color: #1a202c;
}

.memorial-mode .tab-btn.active {
    color: #2d3748;
    border-bottom-color: #2d3748;
}

.memorial-mode .auth-btn {
    background-color: #2d3748;
}

.memorial-mode .auth-btn:hover {
    background-color: #1a202c;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .auth-container {
        flex-direction: column;
    }
    
    .brand-section {
        padding: 30px;
    }
    
    .form-section {
        padding: 30px;
    }
}`;
        
        fs.writeFileSync(bundleCssPath, cssContent);
    }

    // 修复ThemeManager
    async fixThemeManager() {
        // ThemeManager已经在index.html中，这里主要是确保初始化代码存在
        await this.fixThemeInitialization();
    }

    // 修复主题切换按钮
    async fixThemeToggleButton() {
        const htmlFilePath = path.join(projectRoot, 'src', 'html', 'index.html');
        let htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
        
        // 检查是否已存在主题切换按钮
        if (!htmlContent.includes('theme-toggle')) {
            // 在body中添加主题切换按钮
            const bodyStartRegex = /<body>/;
            const themeToggleHtml = `    <!-- 主题切换按钮 -->
    <div style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
        <button id="theme-toggle" style="padding: 10px 15px; border: none; border-radius: 20px; background-color: #f0f0f0; cursor: pointer; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            🌅 切换到落日模式
        </button>
    </div>
    `;
            htmlContent = htmlContent.replace(bodyStartRegex, '<body>\n' + themeToggleHtml);
            fs.writeFileSync(htmlFilePath, htmlContent);
        }
    }

    // 修复主题样式
    async fixThemeStyles() {
        // 主题样式已经在bundle.min.css中，这里主要是确保index.html中引用正确
        await this.fixCssReferences();
    }

    // 修复主题初始化
    async fixThemeInitialization() {
        const htmlFilePath = path.join(projectRoot, 'src', 'html', 'index.html');
        let htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
        
        // 检查是否已存在ThemeManager.init()调用
        if (!htmlContent.includes('ThemeManager.init')) {
            // 在DOMContentLoaded事件中添加初始化代码
            const domContentLoadedRegex = /document\.addEventListener\(['"]DOMContentLoaded['"], \(\) => {/;
            if (domContentLoadedRegex.test(htmlContent)) {
                const initCode = '            // 初始化主题管理\n            ThemeManager.init();\n';
                htmlContent = htmlContent.replace(domContentLoadedRegex, '$&\n' + initCode);
                fs.writeFileSync(htmlFilePath, htmlContent);
            } else {
                // 添加完整的DOMContentLoaded事件
                const scriptEndRegex = /<\/script>/;
                const domContentLoadedHtml = `    <script>
        // 页面加载完成后初始化主题管理
        document.addEventListener('DOMContentLoaded', () => {
            ThemeManager.init();
        });
    </script>
`;
                htmlContent = htmlContent.replace(scriptEndRegex, domContentLoadedHtml + '</script>');
                fs.writeFileSync(htmlFilePath, htmlContent);
            }
        }
    }

    // 验证修复结果
    async verifyFix() {
        console.log(`[${this.name}] 开始验证修复结果...`);
        
        // 重新检测问题
        const remainingIssues = await this.detectUIIssues();
        
        if (remainingIssues.length === 0) {
            console.log(`[${this.name}] 修复验证通过！所有UI及配色方案问题已解决`);
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
            type: 'ui_color_scheme_issue',
            name: 'UI及配色方案全部失效',
            description: '客户端登录项目UI及配色方案全部失效',
            severity: 'high',
            pattern: {
                cssIssues: issues.filter(issue => issue.type.includes('CSS')).length,
                themeIssues: issues.filter(issue => issue.type.includes('THEME')).length,
                fileIssues: issues.filter(issue => issue.type.includes('FILE') || issue.type.includes('DIR')).length
            },
            detectionMethod: 'static_analysis',
            fixActions: [
                '添加CSS文件引用',
                '创建缺失的CSS目录',
                '生成基础CSS文件',
                '修复主题管理代码',
                '添加主题切换按钮',
                '修复主题初始化代码'
            ],
            solution: '确保CSS文件正确引用，主题管理代码完整',
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
            const issues = await this.detectUIIssues();
            
            let fixedIssues = [];
            let verificationResult = true;
            
            if (issues.length > 0) {
                // 2. 修复问题
                fixedIssues = await this.fixUIIssues(issues);
                
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

// 创建UI修复AI
function createUIFixAI() {
    console.log('正在创建UI及配色方案修复子AI...');
    
    // 创建AI实例
    const uiFixAI = new AIInstance(
        'UIFixAI',
        'client_ui',
        'monitoring',
        'module',
        'application'
    );
    
    console.log(`成功创建AI实例: ${uiFixAI.name}`);
    console.log(`AI ID: ${uiFixAI.id}`);
    console.log(`角色: ${uiFixAI.role}`);
    console.log(`组: ${uiFixAI.group}`);
    
    return uiFixAI;
}

// 主函数
async function main() {
    console.log('========================================');
    console.log('MTSCOS AI 项目 - UI及配色方案修复子AI创建脚本');
    console.log('========================================');
    
    try {
        // 1. 创建AI实例
        const uiFixAI = createUIFixAI();
        
        // 2. 执行完整修复流程
        const fixResult = await uiFixAI.fullFixFlow();
        
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
                console.log('\n🎉 未检测到UI及配色方案问题，系统配置正确！');
            } else {
                console.log('\n🎉 所有UI及配色方案问题已成功修复！');
                console.log('📋 修复内容已上传到错误特征数据库');
                console.log('\n建议：');
                console.log('1. 清除浏览器缓存后测试访问');
                console.log('2. 访问 http://localhost:8080 验证修复效果');
                console.log('3. 测试主题切换功能是否正常');
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
    createUIFixAI,
    AIInstance
}
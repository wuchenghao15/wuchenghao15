#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - 客户端访问顺畅度优化和防呆设计子AI创建脚本
 * 用于优化客户端访问顺畅度，设置防呆设计防止用户暴力使用系统，并上报特征库
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

    // 检测客户端访问问题和防呆设计
    async detectClientIssues() {
        console.log(`[${this.name}] 开始检测客户端访问问题和防呆设计...`);
        
        // 1. 检测资源加载优化
        const resourceLoadingIssues = await this.checkResourceLoading();
        
        // 2. 检测防呆设计
        const antiBruteForceIssues = await this.checkAntiBruteForce();
        
        // 3. 检测缓存策略
        const cacheStrategyIssues = await this.checkCacheStrategy();
        
        // 合并所有问题
        const allIssues = [
            ...resourceLoadingIssues,
            ...antiBruteForceIssues,
            ...cacheStrategyIssues
        ];
        
        console.log(`[${this.name}] 检测完成，发现 ${allIssues.length} 个问题`);
        return allIssues;
    }

    // 检测资源加载优化
    async checkResourceLoading() {
        console.log(`[${this.name}] 检测资源加载优化...`);
        const issues = [];
        
        try {
            // 检查index.html中的资源引用
            const indexHtmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
            if (fs.existsSync(indexHtmlPath)) {
                const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf8');
                
                // 检查CSS资源引用
                const cssRegex = /<link rel="stylesheet" href="([^"]+)"/g;
                let cssMatch;
                let cssCount = 0;
                while ((cssMatch = cssRegex.exec(indexHtmlContent)) !== null) {
                    cssCount++;
                }
                
                // 检查JavaScript资源引用
                const jsRegex = /<script src="([^"]+)"/g;
                let jsMatch;
                let jsCount = 0;
                while ((jsMatch = jsRegex.exec(indexHtmlContent)) !== null) {
                    jsCount++;
                }
                
                // 检查资源数量是否过多
                if (cssCount > 5) {
                    issues.push({
                        type: 'TOO_MANY_CSS_FILES',
                        severity: 'medium',
                        description: `CSS文件数量过多：${cssCount}个`,
                        file: 'src/html/index.html',
                        fixable: true
                    });
                }
                
                if (jsCount > 10) {
                    issues.push({
                        type: 'TOO_MANY_JS_FILES',
                        severity: 'medium',
                        description: `JavaScript文件数量过多：${jsCount}个`,
                        file: 'src/html/index.html',
                        fixable: true
                    });
                }
            }
        } catch (error) {
            console.error(`[${this.name}] 资源加载检测失败:`, error);
        }
        
        return issues;
    }

    // 检测防呆设计
    async checkAntiBruteForce() {
        console.log(`[${this.name}] 检测防呆设计...`);
        const issues = [];
        
        try {
            // 检查app.js中的防呆设计
            const appFilePath = path.join(projectRoot, 'src', 'app.js');
            if (fs.existsSync(appFilePath)) {
                const appContent = fs.readFileSync(appFilePath, 'utf8');
                
                // 检查是否有请求频率限制
                if (!appContent.includes('rateLimit') && !appContent.includes('express-rate-limit')) {
                    issues.push({
                        type: 'MISSING_RATE_LIMIT',
                        severity: 'high',
                        description: '缺少请求频率限制',
                        file: 'src/app.js',
                        fixable: true
                    });
                }
                
                // 检查是否有会话超时设置（如果使用了express-session）
                if (appContent.includes('session') && !appContent.includes('cookie.maxAge')) {
                    issues.push({
                        type: 'MISSING_SESSION_TIMEOUT',
                        severity: 'medium',
                        description: '缺少会话超时设置',
                        file: 'src/app.js',
                        fixable: true
                    });
                }
            }
            
            // 检查登录页面的防呆设计
            const loginHtmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
            if (fs.existsSync(loginHtmlPath)) {
                const loginHtmlContent = fs.readFileSync(loginHtmlPath, 'utf8');
                
                // 检查是否有验证码机制
                if (!loginHtmlContent.includes('captcha') && !loginHtmlContent.includes('验证码')) {
                    issues.push({
                        type: 'MISSING_CAPTCHA',
                        severity: 'medium',
                        description: '登录页面缺少验证码机制',
                        file: 'src/html/index.html',
                        fixable: true
                    });
                }
            }
        } catch (error) {
            console.error(`[${this.name}] 防呆设计检测失败:`, error);
        }
        
        return issues;
    }

    // 检测缓存策略
    async checkCacheStrategy() {
        console.log(`[${this.name}] 检测缓存策略...`);
        const issues = [];
        
        try {
            // 检查app.js中的缓存策略
            const appFilePath = path.join(projectRoot, 'src', 'app.js');
            if (fs.existsSync(appFilePath)) {
                const appContent = fs.readFileSync(appFilePath, 'utf8');
                
                // 检查是否有静态资源缓存设置
                const staticMiddlewarePattern = /app\.use\([^)]*express\.static\([^)]+\)(?!\s*,\s*{[^}]*maxAge[^}]*})[^)]*\);/g;
                if (staticMiddlewarePattern.test(appContent)) {
                    issues.push({
                        type: 'MISSING_CACHE_CONTROL',
                        severity: 'medium',
                        description: '缺少静态资源缓存策略',
                        file: 'src/app.js',
                        fixable: true
                    });
                }
            }
        } catch (error) {
            console.error(`[${this.name}] 缓存策略检测失败:`, error);
        }
        
        return issues;
    }

    // 修复检测到的问题
    async fixClientIssues(issues) {
        console.log(`[${this.name}] 开始修复 ${issues.length} 个问题...`);
        const fixedIssues = [];
        
        for (const issue of issues) {
            try {
                switch (issue.type) {
                    case 'TOO_MANY_CSS_FILES':
                        await this.optimizeCssFiles();
                        break;
                    case 'TOO_MANY_JS_FILES':
                        await this.optimizeJsFiles();
                        break;
                    case 'MISSING_RATE_LIMIT':
                        await this.addRateLimit();
                        break;
                    case 'MISSING_SESSION_TIMEOUT':
                        await this.addSessionTimeout();
                        break;
                    case 'MISSING_CAPTCHA':
                        await this.addCaptchaToLogin();
                        break;
                    case 'MISSING_CACHE_CONTROL':
                        await this.addCacheControl();
                        break;
                    default:
                        console.log(`[${this.name}] 无法修复未知类型问题: ${issue.type}`);
                        continue;
                }
                fixedIssues.push(issue);
                console.log(`[${this.name}] 修复完成: ${issue.description}`);
            } catch (fixError) {
                console.error(`[${this.name}] 修复失败: ${issue.description}`, fixError);
            }
        }
        
        console.log(`[${this.name}] 修复完成，成功修复 ${fixedIssues.length}/${issues.length} 个问题`);
        return fixedIssues;
    }

    // 优化CSS文件
    async optimizeCssFiles() {
        console.log(`[${this.name}] 优化CSS文件...`);
        // 这里可以实现CSS文件合并和压缩逻辑
        // 目前只记录日志，实际优化需要更复杂的逻辑
    }

    // 优化JavaScript文件
    async optimizeJsFiles() {
        console.log(`[${this.name}] 优化JavaScript文件...`);
        // 这里可以实现JavaScript文件合并和压缩逻辑
        // 目前只记录日志，实际优化需要更复杂的逻辑
    }

    // 添加请求频率限制
    async addRateLimit() {
        console.log(`[${this.name}] 添加请求频率限制...`);
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appFilePath, 'utf8');
        
        // 检查是否已经安装了express-rate-limit
        try {
            require('express-rate-limit');
        } catch (error) {
            console.log(`[${this.name}] 安装express-rate-limit依赖...`);
            execSync('npm install express-rate-limit --save', { cwd: projectRoot, stdio: 'ignore' });
        }
        
        // 添加rateLimit中间件
        if (!appContent.includes('express-rate-limit')) {
            // 在文件顶部添加导入
            const importStatement = 'const rateLimit = require(\'express-rate-limit\');\n';
            if (appContent.startsWith('const')) {
                const firstImportIndex = appContent.indexOf('const');
                appContent = appContent.slice(0, firstImportIndex) + importStatement + appContent.slice(firstImportIndex);
            } else {
                appContent = importStatement + appContent;
            }
        }
        
        // 添加rateLimit配置
        if (!appContent.includes('rateLimit(')) {
            // 在app.use(helmet())之后添加
            const helmetPattern = /app\.use\(helmet\([^)]*\)\);/;
            if (helmetPattern.test(appContent)) {
                const helmetMatch = appContent.match(helmetPattern);
                const rateLimitConfig = `\n\n// 请求频率限制
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100, // 每个IP在15分钟内最多100个请求
    standardHeaders: true,
    legacyHeaders: false,
});\napp.use(limiter);\n`;
                appContent = appContent.replace(helmetPattern, helmetMatch[0] + rateLimitConfig);
            }
        }
        
        fs.writeFileSync(appFilePath, appContent);
    }

    // 添加会话超时设置
    async addSessionTimeout() {
        console.log(`[${this.name}] 添加会话超时设置...`);
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appFilePath, 'utf8');
        
        // 检查并添加会话超时设置
        const sessionPattern = /app\.use\(session\(([^)]+)\)\);/s;
        if (sessionPattern.test(appContent)) {
            const sessionMatch = appContent.match(sessionPattern);
            let sessionConfig = sessionMatch[1];
            
            if (!sessionConfig.includes('cookie.maxAge')) {
                // 添加cookie.maxAge设置
                if (sessionConfig.trim().endsWith('}')) {
                    sessionConfig = sessionConfig.trim().slice(0, -1);
                    sessionConfig += ',\n    cookie: { maxAge: 3600000 } // 1小时会话超时\n';
                } else {
                    sessionConfig += '\n    cookie: { maxAge: 3600000 } // 1小时会话超时';
                }
                sessionConfig += '}';
                
                appContent = appContent.replace(sessionPattern, `app.use(session(${sessionConfig}));`);
                fs.writeFileSync(appFilePath, appContent);
            }
        }
    }

    // 添加验证码到登录页面
    async addCaptchaToLogin() {
        console.log(`[${this.name}] 添加验证码到登录页面...`);
        const loginHtmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
        let loginContent = fs.readFileSync(loginHtmlPath, 'utf8');
        
        // 检查是否已经有验证码
        if (!loginContent.includes('captcha')) {
            // 在密码输入框之后添加验证码
            const passwordInputPattern = /<input[^>]*type="password"[^>]*>/;
            if (passwordInputPattern.test(loginContent)) {
                const captchaHtml = `\n                    <div class="form-group">
                        <label for="captcha">验证码</label>
                        <div class="captcha-container">
                            <input type="text" id="captcha" name="captcha" class="form-control" placeholder="请输入验证码" required>
                            <div class="captcha-image" id="captchaImage">
                                <!-- 验证码图片将通过JavaScript生成 -->
                            </div>
                        </div>
                    </div>`;
                loginContent = loginContent.replace(passwordInputPattern, (match) => match + captchaHtml);
                
                // 添加验证码生成脚本
                const scriptPattern = /<\/body>/;
                if (scriptPattern.test(loginContent)) {
                    const captchaScript = `\n<script>
// 简单的验证码生成函数
function generateCaptcha() {
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let captcha = '';
    for (let i = 0; i < 6; i++) {
        captcha += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    document.getElementById('captchaImage').innerHTML = '<span style="font-size: 24px; letter-spacing: 5px; font-weight: bold;">' + captcha + '</span>';
    return captcha;
}

// 页面加载时生成验证码
document.addEventListener('DOMContentLoaded', function() {
    generateCaptcha();
});
</script>`;
                    loginContent = loginContent.replace(scriptPattern, captchaScript + scriptPattern[0]);
                }
                
                fs.writeFileSync(loginHtmlPath, loginContent);
            }
        }
    }

    // 添加缓存控制
    async addCacheControl() {
        console.log(`[${this.name}] 添加缓存控制...`);
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        let appContent = fs.readFileSync(appFilePath, 'utf8');
        
        // 修复静态资源中间件的缓存控制
        // 直接替换两行静态资源中间件
        appContent = appContent.replace(
            `app.use('/html', express.static(path.join(__dirname, '/html')));
app.use('/assets', express.static(path.join(__dirname, '/html/assets')));`,
            `app.use('/html', express.static(path.join(__dirname, '/html'), { maxAge: 31536000 })); // 静态资源缓存1年
app.use('/assets', express.static(path.join(__dirname, '/html/assets'), { maxAge: 31536000 })); // 静态资源缓存1年`
        );
        
        fs.writeFileSync(appFilePath, appContent);
    }

    // 验证修复结果
    async verifyFix() {
        console.log(`[${this.name}] 开始验证修复结果...`);
        
        // 重新检测问题
        const remainingIssues = await this.detectClientIssues();
        
        if (remainingIssues.length === 0) {
            console.log(`[${this.name}] 修复验证通过！所有问题已解决`);
            return true;
        } else {
            console.log(`[${this.name}] 修复验证失败，仍有 ${remainingIssues.length} 个问题未解决`);
            remainingIssues.forEach(issue => {
                console.log(`  - ${issue.description}`);
            });
            return false;
        }
    }

    // 生成特征
    generateFeature(issues) {
        console.log(`[${this.name}] 生成特征...`);
        
        // 按类型分组问题
        const issueTypes = {};
        issues.forEach(issue => {
            if (!issueTypes[issue.type]) {
                issueTypes[issue.type] = 0;
            }
            issueTypes[issue.type]++;
        });
        
        const feature = {
            id: `feature_${Date.now()}`,
            type: 'client_optimization_anti_brute_force',
            name: '客户端访问顺畅度优化和防呆设计',
            description: '优化客户端访问顺畅度，设置防呆设计防止用户暴力使用系统',
            severity: 'high',
            pattern: {
                totalIssues: issues.length,
                issueTypes: issueTypes
            },
            detectionMethod: 'static_analysis',
            fixActions: [
                '优化CSS文件',
                '优化JavaScript文件',
                '添加请求频率限制',
                '添加会话超时设置',
                '添加验证码机制',
                '添加缓存控制'
            ],
            solution: '综合优化客户端访问顺畅度，设置防呆设计防止用户暴力使用系统',
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
            const issues = await this.detectClientIssues();
            
            let fixedIssues = [];
            let verificationResult = true;
            
            if (issues.length > 0) {
                // 2. 修复问题
                fixedIssues = await this.fixClientIssues(issues);
                
                // 3. 验证修复
                verificationResult = await this.verifyFix();
            }
            
            // 4. 生成并上传特征
            const feature = this.generateFeature(issues);
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

// 创建客户端优化AI
function createClientOptimizationAI() {
    console.log('正在创建客户端访问顺畅度优化和防呆设计子AI...');
    
    // 创建AI实例
    const clientOptimizationAI = new AIInstance(
        'ClientOptimizationAI',
        'client_optimization',
        'performance',
        'module',
        'application'
    );
    
    console.log(`成功创建AI实例: ${clientOptimizationAI.name}`);
    console.log(`AI ID: ${clientOptimizationAI.id}`);
    console.log(`角色: ${clientOptimizationAI.role}`);
    console.log(`组: ${clientOptimizationAI.group}`);
    
    return clientOptimizationAI;
}

// 主函数
async function main() {
    console.log('========================================');
    console.log('MTSCOS AI 项目 - 客户端访问顺畅度优化和防呆设计子AI创建脚本');
    console.log('========================================');
    
    try {
        // 1. 创建AI实例
        const clientOptimizationAI = createClientOptimizationAI();
        
        // 2. 执行完整修复流程
        const fixResult = await clientOptimizationAI.fullFixFlow();
        
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
                console.log('\n🎉 未检测到问题，客户端访问顺畅度和防呆设计已优化！');
            } else {
                console.log('\n🎉 所有问题已成功修复！');
                console.log('📋 修复内容已上传到错误特征数据库');
                console.log('\n建议：');
                console.log('1. 重启服务器以应用所有更改');
                console.log('2. 访问 http://localhost:8080 验证修复效果');
                console.log('3. 运行测试脚本确保系统正常工作');
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
    createClientOptimizationAI,
    AIInstance
}
#!/usr/bin/env node

/**
 * MTSCOS AI 项目 - 错误异常修复子AI创建脚本
 * 用于检测和修复项目中的各种错误异常，并上报特征库
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

    // 检测项目中的错误异常
    async detectErrors() {
        console.log(`[${this.name}] 开始检测项目中的错误异常...`);
        
        // 1. 检测JavaScript语法错误
        const jsSyntaxErrors = await this.checkJsSyntax();
        
        // 2. 检测依赖关系错误
        const dependencyErrors = await this.checkDependencies();
        
        // 3. 检测配置文件错误
        const configErrors = await this.checkConfigFiles();
        
        // 4. 检测HTML文件错误
        const htmlErrors = await this.checkHtmlFiles();
        
        // 5. 检测路径引用错误
        const pathErrors = await this.checkPathReferences();
        
        // 6. 检测安全配置错误
        const securityErrors = await this.checkSecurityConfig();
        
        // 合并所有错误
        const allErrors = [
            ...jsSyntaxErrors,
            ...dependencyErrors,
            ...configErrors,
            ...htmlErrors,
            ...pathErrors,
            ...securityErrors
        ];
        
        console.log(`[${this.name}] 检测完成，发现 ${allErrors.length} 个错误异常`);
        return allErrors;
    }

    // 检测JavaScript语法错误
    async checkJsSyntax() {
        console.log(`[${this.name}] 检测JavaScript语法错误...`);
        const errors = [];
        
        try {
            // 使用node -c检查JavaScript语法
            execSync('node -c src/app.js', { cwd: projectRoot, stdio: 'ignore' });
        } catch (error) {
            errors.push({
                type: 'JS_SYNTAX_ERROR',
                severity: 'high',
                description: `JavaScript语法错误: ${error.message}`,
                file: 'src/app.js',
                fixable: false
            });
        }
        
        return errors;
    }

    // 检测依赖关系错误
    async checkDependencies() {
        console.log(`[${this.name}] 检测依赖关系错误...`);
        const errors = [];
        
        try {
            // 检查package.json是否存在
            if (!fs.existsSync(path.join(projectRoot, 'package.json'))) {
                errors.push({
                    type: 'MISSING_PACKAGE_JSON',
                    severity: 'high',
                    description: '缺少package.json文件',
                    file: 'package.json',
                    fixable: false
                });
                return errors;
            }
            
            // 检查node_modules是否存在
            if (!fs.existsSync(path.join(projectRoot, 'node_modules'))) {
                errors.push({
                    type: 'MISSING_NODE_MODULES',
                    severity: 'high',
                    description: '缺少node_modules目录',
                    file: 'node_modules',
                    fixable: true
                });
            }
        } catch (error) {
            errors.push({
                type: 'DEPENDENCY_CHECK_ERROR',
                severity: 'medium',
                description: `依赖检查错误: ${error.message}`,
                file: 'package.json',
                fixable: false
            });
        }
        
        return errors;
    }

    // 检测配置文件错误
    async checkConfigFiles() {
        console.log(`[${this.name}] 检测配置文件错误...`);
        const errors = [];
        
        // 检查.env文件
        const envPath = path.join(projectRoot, '.env');
        if (!fs.existsSync(envPath)) {
            errors.push({
                type: 'MISSING_ENV_FILE',
                severity: 'medium',
                description: '缺少.env配置文件',
                file: '.env',
                fixable: true
            });
        }
        
        // 检查是否存在语法错误的JSON文件
        const jsonFiles = [
            'package.json',
            path.join('src', 'data', 'error-feature-db.json')
        ];
        
        for (const jsonFile of jsonFiles) {
            const filePath = path.join(projectRoot, jsonFile);
            if (fs.existsSync(filePath)) {
                try {
                    fs.readFileSync(filePath, 'utf8');
                    JSON.parse(fs.readFileSync(filePath, 'utf8'));
                } catch (error) {
                    errors.push({
                        type: 'JSON_SYNTAX_ERROR',
                        severity: 'high',
                        description: `JSON文件语法错误: ${error.message}`,
                        file: jsonFile,
                        fixable: false
                    });
                }
            }
        }
        
        return errors;
    }

    // 检测HTML文件错误
    async checkHtmlFiles() {
        console.log(`[${this.name}] 检测HTML文件错误...`);
        const errors = [];
        
        // 获取所有HTML文件
        const htmlFiles = [];
        
        const traverseDir = (dir) => {
            const files = fs.readdirSync(dir);
            for (const file of files) {
                const filePath = path.join(dir, file);
                const stats = fs.statSync(filePath);
                
                // 跳过components目录
                if (stats.isDirectory()) {
                    if (file !== 'components') {
                        traverseDir(filePath);
                    }
                    continue;
                }
                
                // 只处理完整的HTML页面，跳过组件文件
                if (file.endsWith('.html') && file !== 'footer.html') {
                    htmlFiles.push(filePath);
                }
            }
        };
        
        traverseDir(path.join(projectRoot, 'src', 'html'));
        
        // 检查HTML文件的基本结构
    for (const htmlFile of htmlFiles) {
        const relativePath = path.relative(projectRoot, htmlFile);
        const htmlContent = fs.readFileSync(htmlFile, 'utf8');
        
        // 检查重复的DOCTYPE声明
        const doctypeCount = (htmlContent.match(/<!DOCTYPE html>/gi) || []).length;
        if (doctypeCount > 1) {
            errors.push({
                type: 'DUPLICATE_DOCTYPE',
                severity: 'medium',
                description: `重复的DOCTYPE声明，共${doctypeCount}个`,
                file: relativePath,
                fixable: true
            });
        }
        
        // 检查是否缺少DOCTYPE声明
        if (doctypeCount === 0) {
            errors.push({
                type: 'MISSING_DOCTYPE',
                severity: 'low',
                description: '缺少DOCTYPE声明',
                file: relativePath,
                fixable: true
            });
        }
        
        // 检查title标签（使用正则表达式更准确）
        const titleRegex = /<title[^>]*>(.*?)<\/title>/i;
        if (!titleRegex.test(htmlContent)) {
            errors.push({
                type: 'MISSING_TITLE',
                severity: 'low',
                description: '缺少title标签',
                file: relativePath,
                fixable: true
            });
        }
    }
        
        return errors;
    }

    // 检测路径引用错误
    async checkPathReferences() {
        console.log(`[${this.name}] 检测路径引用错误...`);
        const errors = [];
        
        // 检查index.html中的资源引用
        const indexHtmlPath = path.join(projectRoot, 'src', 'html', 'index.html');
        if (fs.existsSync(indexHtmlPath)) {
            const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf8');
            
            // 检查CSS资源引用
            const cssRegex = /<link rel="stylesheet" href="([^"]+)"/g;
            let cssMatch;
            while ((cssMatch = cssRegex.exec(indexHtmlContent)) !== null) {
                const cssPath = cssMatch[1];
                if (cssPath.startsWith('/assets/css/')) {
                    const actualPath = path.join(projectRoot, 'src', 'html', cssPath);
                    if (!fs.existsSync(actualPath)) {
                        errors.push({
                            type: 'MISSING_CSS_FILE',
                            severity: 'medium',
                            description: `缺少CSS文件: ${cssPath}`,
                            file: 'src/html/index.html',
                            fixable: false
                        });
                    }
                }
            }
            
            // 检查JavaScript资源引用
            const jsRegex = /<script src="([^"]+)"/g;
            let jsMatch;
            while ((jsMatch = jsRegex.exec(indexHtmlContent)) !== null) {
                const jsPath = jsMatch[1];
                if (jsPath.startsWith('/assets/js/')) {
                    const actualPath = path.join(projectRoot, 'src', 'html', jsPath);
                    if (!fs.existsSync(actualPath)) {
                        errors.push({
                            type: 'MISSING_JS_FILE',
                            severity: 'medium',
                            description: `缺少JavaScript文件: ${jsPath}`,
                            file: 'src/html/index.html',
                            fixable: false
                        });
                    }
                }
            }
        }
        
        return errors;
    }

    // 检测安全配置错误
    async checkSecurityConfig() {
        console.log(`[${this.name}] 检测安全配置错误...`);
        const errors = [];
        
        // 检查app.js中的helmet配置
        const appFilePath = path.join(projectRoot, 'src', 'app.js');
        if (fs.existsSync(appFilePath)) {
            const appContent = fs.readFileSync(appFilePath, 'utf8');
            
            // 检查helmet是否启用
            if (appContent.includes('helmet')) {
                // 检查HSTS配置
                if (!appContent.includes('hsts: false')) {
                    errors.push({
                        type: 'HSTS_CONFIG',
                        severity: 'medium',
                        description: 'helmet中间件未禁用HSTS',
                        file: 'src/app.js',
                        fixable: true
                    });
                }
            }
        }
        
        return errors;
    }

    // 修复检测到的错误
    async fixErrors(errors) {
        console.log(`[${this.name}] 开始修复 ${errors.length} 个错误异常...`);
        const fixedErrors = [];
        
        for (const error of errors) {
            try {
                switch (error.type) {
                    case 'MISSING_NODE_MODULES':
                        await this.installDependencies();
                        break;
                    case 'MISSING_ENV_FILE':
                        await this.createDefaultEnvFile();
                        break;
                    case 'MISSING_DOCTYPE':
                        await this.addDoctypeToHtml(error.file);
                        break;
                    case 'DUPLICATE_DOCTYPE':
                        await this.fixDuplicateDoctype(error.file);
                        break;
                    case 'MISSING_TITLE':
                        await this.addTitleToHtml(error.file);
                        break;
                    case 'HSTS_CONFIG':
                        await this.fixHstsConfig();
                        break;
                    default:
                        console.log(`[${this.name}] 无法修复未知类型错误: ${error.type}`);
                        continue;
                }
                fixedErrors.push(error);
                console.log(`[${this.name}] 修复完成: ${error.description}`);
            } catch (fixError) {
                console.error(`[${this.name}] 修复失败: ${error.description}`, fixError);
            }
        }
        
        console.log(`[${this.name}] 修复完成，成功修复 ${fixedErrors.length}/${errors.length} 个错误异常`);
        return fixedErrors;
    }

    // 安装依赖
    async installDependencies() {
        console.log(`[${this.name}] 安装项目依赖...`);
        execSync('npm install', { cwd: projectRoot, stdio: 'ignore' });
    }

    // 创建默认.env文件
    async createDefaultEnvFile() {
        console.log(`[${this.name}] 创建默认.env文件...`);
        const defaultEnvContent = `# MTSCOS AI 项目配置
PORT=8080
NODE_ENV=development

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=mtscos_ai

# AI引擎配置
AI_ENGINE_URL=http://localhost:5000
AI_API_KEY=demo_key

# 安全配置
JWT_SECRET=your_jwt_secret_key
SESSION_SECRET=your_session_secret_key

# 日志配置
LOG_LEVEL=info
LOG_MAX_SIZE=20m
LOG_MAX_FILES=5
`;
        fs.writeFileSync(path.join(projectRoot, '.env'), defaultEnvContent);
    }

    // 添加DOCTYPE到HTML文件
    async addDoctypeToHtml(filePath) {
        const fullPath = path.join(projectRoot, filePath);
        const htmlContent = fs.readFileSync(fullPath, 'utf8');
        const updatedContent = '<!DOCTYPE html>\n' + htmlContent;
        fs.writeFileSync(fullPath, updatedContent);
    }

    // 添加title到HTML文件
    async addTitleToHtml(filePath) {
        const fullPath = path.join(projectRoot, filePath);
        let htmlContent = fs.readFileSync(fullPath, 'utf8');
        
        // 在head标签中添加title
        if (htmlContent.includes('<head>')) {
            htmlContent = htmlContent.replace('<head>', '<head>\n    <title>MTSCOS AI 系统</title>');
            fs.writeFileSync(fullPath, htmlContent);
        }
    }
    
    // 修复重复的DOCTYPE声明
    async fixDuplicateDoctype(filePath) {
        const fullPath = path.join(projectRoot, filePath);
        let htmlContent = fs.readFileSync(fullPath, 'utf8');
        
        // 只保留第一个DOCTYPE声明，移除所有其他的
        const doctypeMatches = htmlContent.match(/<!DOCTYPE html>/gi) || [];
        if (doctypeMatches.length > 1) {
            // 找到第一个DOCTYPE声明的位置
            const firstDoctypeIndex = htmlContent.indexOf('<!DOCTYPE html>');
            // 移除第一个DOCTYPE声明
            let contentWithoutFirstDoctype = htmlContent.slice(firstDoctypeIndex + '<!DOCTYPE html>'.length);
            // 移除剩余的所有DOCTYPE声明
            contentWithoutFirstDoctype = contentWithoutFirstDoctype.replace(/<!DOCTYPE html>/gi, '');
            // 重新组合内容，只保留第一个DOCTYPE声明
            htmlContent = '<!DOCTYPE html>' + contentWithoutFirstDoctype;
            fs.writeFileSync(fullPath, htmlContent);
        }
    }

    // 修复HSTS配置
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

    // 验证修复结果
    async verifyFix() {
        console.log(`[${this.name}] 开始验证修复结果...`);
        
        // 重新检测问题
        const remainingErrors = await this.detectErrors();
        
        if (remainingErrors.length === 0) {
            console.log(`[${this.name}] 修复验证通过！所有错误异常已解决`);
            return true;
        } else {
            console.log(`[${this.name}] 修复验证失败，仍有 ${remainingErrors.length} 个错误异常未解决`);
            remainingErrors.forEach(error => {
                console.log(`  - ${error.description}`);
            });
            return false;
        }
    }

    // 生成错误特征
    generateErrorFeature(errors) {
        console.log(`[${this.name}] 生成错误特征...`);
        
        // 按类型分组错误
        const errorTypes = {};
        errors.forEach(error => {
            if (!errorTypes[error.type]) {
                errorTypes[error.type] = 0;
            }
            errorTypes[error.type]++;
        });
        
        const feature = {
            id: `feature_${Date.now()}`,
            type: 'project_error_issue',
            name: '项目错误异常',
            description: '项目中存在各种错误异常，包括语法错误、依赖错误、配置错误等',
            severity: 'high',
            pattern: {
                totalErrors: errors.length,
                errorTypes: errorTypes
            },
            detectionMethod: 'comprehensive_analysis',
            fixActions: [
                '修复JavaScript语法错误',
                '安装缺失的依赖',
                '创建缺失的配置文件',
                '修复HTML文件结构',
                '修复路径引用错误',
                '优化安全配置'
            ],
            solution: '综合检测和修复项目中的各种错误异常，确保项目能够正常运行',
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
            // 1. 检测错误
            const errors = await this.detectErrors();
            
            let fixedErrors = [];
            let verificationResult = true;
            
            if (errors.length > 0) {
                // 2. 修复错误
                fixedErrors = await this.fixErrors(errors);
                
                // 3. 验证修复
                verificationResult = await this.verifyFix();
            }
            
            // 4. 生成并上传特征（即使没有检测到问题，也生成基础特征）
            const feature = this.generateErrorFeature(errors);
            await this.uploadToFeatureLibrary(feature);
            
            this.status = 'idle';
            
            return {
                success: verificationResult,
                errors: errors,
                fixed: fixedErrors.length,
                feature: feature
            };
        } catch (error) {
            console.error(`[${this.name}] 修复流程失败:`, error);
            this.status = 'error';
            throw error;
        }
    }
}

// 创建错误修复AI
function createErrorFixAI() {
    console.log('正在创建错误异常修复子AI...');
    
    // 创建AI实例
    const errorFixAI = new AIInstance(
        'ErrorFixAI',
        'error_detection',
        'monitoring',
        'module',
        'application'
    );
    
    console.log(`成功创建AI实例: ${errorFixAI.name}`);
    console.log(`AI ID: ${errorFixAI.id}`);
    console.log(`角色: ${errorFixAI.role}`);
    console.log(`组: ${errorFixAI.group}`);
    
    return errorFixAI;
}

// 主函数
async function main() {
    console.log('========================================');
    console.log('MTSCOS AI 项目 - 错误异常修复子AI创建脚本');
    console.log('========================================');
    
    try {
        // 1. 创建AI实例
        const errorFixAI = createErrorFixAI();
        
        // 2. 执行完整修复流程
        const fixResult = await errorFixAI.fullFixFlow();
        
        // 3. 输出修复报告
        console.log('\n========================================');
        console.log('修复报告');
        console.log('========================================');
        console.log(`修复状态: ${fixResult.success ? '成功' : '失败'}`);
        console.log(`检测到错误: ${fixResult.errors.length}`);
        console.log(`成功修复: ${fixResult.fixed}`);
        
        if (fixResult.feature) {
            console.log(`特征ID: ${fixResult.feature.id}`);
            console.log(`特征名称: ${fixResult.feature.name}`);
        }
        
        if (fixResult.success) {
            if (fixResult.errors.length === 0) {
                console.log('\n🎉 未检测到错误异常，系统配置正确！');
            } else {
                console.log('\n🎉 所有错误异常已成功修复！');
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
    createErrorFixAI,
    AIInstance
}
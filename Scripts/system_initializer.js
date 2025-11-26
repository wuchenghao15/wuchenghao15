#!/usr/bin/env node

// system_initializer.js - MTSCOS 系统初始化和错误检查工具
// 功能：自动检查脚本错误、数学错误、语法逻辑错误、文件路径引用错误、异常处理
//       清理临时工具脚本、优化逻辑引用、更新依赖、验证API、管理版本号
// 版本：1.3.0
// 创建时间：2025-11-10

const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const http = require('http');
const https = require('https');

// 配置参数
const CONFIG = {
    projectRoot: path.resolve(__dirname, '..'),
    scriptsDir: path.resolve(__dirname, '..', 'Scripts'),
    logsDir: path.resolve(__dirname, '..', 'Logs'),
    htmlDir: path.resolve(__dirname, '..', 'HTML'),
    cssDir: path.resolve(__dirname, '..', 'CSS'),
    jsDir: path.resolve(__dirname, '..', 'JavaScript'),
    phpDir: path.resolve(__dirname, '..', 'PHP'),
    errorLogFile: path.resolve(__dirname, '..', 'Logs', 'system_initializer.log'),
    versionFile: path.resolve(__dirname, '..', 'VERSION'),
    tempScriptPatterns: ['.tmp', '_temp', 'temp_', 'temp.', '.temp'],
    maxExecutionTime: 30000, // 最大执行时间（毫秒）
    thirdPartyAPIs: {
        wechat: 'https://api.weixin.qq.com/sns/oauth2/access_token',
        qq: 'https://graph.qq.com/oauth2.0/token',
        github: 'https://github.com/login/oauth/access_token',
        google: 'https://oauth2.googleapis.com/token',
        hotmail: 'https://login.live.com/oauth20_token.srf'
    },
    dependencies: {
        python: 'python3',
        java: 'java',
        mysql: 'mysql',
        mssql: 'sqlcmd',
        node: 'node',
        npm: 'npm'
    }
};

// 工具函数：记录日志
function log(message, type = 'INFO') {
    const timestamp = new Date().toLocaleString('zh-CN');
    const logEntry = `[${timestamp}] [${type}] ${message}\n`;
    
    console.log(`${type}: ${message}`);
    try {
        // 确保日志目录存在
        if (!fs.existsSync(CONFIG.logsDir)) {
            fs.mkdirSync(CONFIG.logsDir, { recursive: true });
        }
        fs.appendFileSync(CONFIG.errorLogFile, logEntry);
    } catch (error) {
        console.error(`[system_initializer.js] `无法写入日志文件: ${error.message}``);
    }
}

// 工具函数：执行命令并返回结果
function executeCommand(command, options = {}) {
    try {
        return {
            success: true,
            output: execSync(command, { ...options, encoding: 'utf8' })
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
            output: error.stdout ? error.stdout.toString().catch(error => console.error(`[system_initializer.js] stdout.toString failed:`, error)) : '',
            stderr: error.stderr ? error.stderr.toString() : ''
        };
    }
}

// 工具函数：检查文件是否存在
function fileExists(filePath) {
    try {
        return fs.existsSync(filePath);
    } catch (error) {
        log(`检查文件存在性失败: ${filePath} - ${error.message}`, 'ERROR');
        return false;
    }
}

// 工具函数：读取文件内容
function readFileContent(filePath) {
    try {
        return fs.readFileSync(filePath, 'utf8');
    } catch (error) {
        log(`读取文件失败: ${filePath} - ${error.message}`, 'ERROR');
        return null;
    }
}

// 工具函数：写入文件内容
function writeFileContent(filePath, content) {
    try {
        // 确保目录存在
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(filePath, content);
        return true;
    } catch (error) {
        log(`写入文件失败: ${filePath} - ${error.message}`, 'ERROR');
        return false;
    }
}

// 第一部分：初始化前的错误检查

// 检查数学错误（除数为零、根为虚数等）
function checkMathErrors() {
    log('开始检查数学错误...');
    const mathErrors = [];
    
    // 检查常见的数学错误模式
    const mathErrorPatterns = [
        { pattern: /\/\s*0/g, message: '除数为零' },
        { pattern: /Math\.sqrt\([^)]*\)/g, message: '可能的虚数根' },
        { pattern: /Math\.log\([^)]*\)/g, message: '可能的对数错误' },
        { pattern: /Math\.asin\([^)]*\)/g, message: '可能的反正弦错误' },
        { pattern: /Math\.acos\([^)]*\)/g, message: '可能的反余弦错误' }
    ];
    
    // 检查JavaScript文件
    const jsFiles = findFilesByExtension(CONFIG.projectRoot, ['.js']);
    
    jsFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            mathErrorPatterns.forEach(({ pattern, message }) => {
                let match;
                const matches = [];
                while ((match = pattern.exec(content)) !== null) {
                    // 获取行号
                    const lineNumber = content.substring(0, match.index).split('\n').length;
                    matches.push({ line: lineNumber, code: match[0] });
                }
                
                if (matches.length > 0) {
                    mathErrors.push({
                        file,
                        message,
                        occurrences: matches
                    });
                }
            });
        }
    });
    
    // 检查PHP文件中的数学运算
    const phpFiles = findFilesByExtension(CONFIG.projectRoot, ['.php']);
    phpFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            // 检查PHP中的除法
            const divPattern = /\/\s*\$?\d+/g;
            let match;
            while ((match = divPattern.exec(content)) !== null) {
                if (match[0].includes('/ 0')) {
                    const lineNumber = content.substring(0, match.index).split('\n').length;
                    mathErrors.push({
                        file,
                        message: 'PHP中的除数为零',
                        occurrences: [{ line: lineNumber, code: match[0] }]
                    });
                }
            }
        }
    });
    
    if (mathErrors.length > 0) {
        log(`发现 ${mathErrors.length} 个潜在的数学错误`, 'WARNING');
        mathErrors.forEach(error => {
            log(`文件: ${error.file}, 问题: ${error.message}`, 'WARNING');
            error.occurrences.forEach(occur => {
                log(`  - 第 ${occur.line} 行: ${occur.code}`, 'WARNING');
            });
        });
    } else {
        log('未发现明显的数学错误', 'INFO');
    }
    
    return mathErrors;
}

// 检查语法和逻辑错误
function checkSyntaxErrors() {
    log('开始检查语法和逻辑错误...');
    const syntaxErrors = [];
    
    // 检查JavaScript文件语法
    const jsFiles = findFilesByExtension(CONFIG.projectRoot, ['.js']);
    
    jsFiles.forEach(file => {
        const result = executeCommand(`node -c ${file}`);
        if (!result.success) {
            syntaxErrors.push({
                file,
                type: 'JavaScript语法错误',
                message: result.error || result.stderr
            });
        }
    });
    
    // 检查PHP文件语法
    const phpFiles = findFilesByExtension(CONFIG.projectRoot, ['.php']);
    phpFiles.forEach(file => {
        const result = executeCommand(`php -l ${file}`);
        if (!result.success) {
            syntaxErrors.push({
                file,
                type: 'PHP语法错误',
                message: result.error || result.stderr || result.output
            });
        }
    });
    
    // 检查HTML文件中的常见错误
    const htmlFiles = findFilesByExtension(CONFIG.projectRoot, ['.html']);
    htmlFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            // 检查未闭合的标签
            const unclosedTags = findUnclosedHtmlTags(content);
            if (unclosedTags.length > 0) {
                syntaxErrors.push({
                    file,
                    type: 'HTML标签错误',
                    message: `发现 ${unclosedTags.length} 个未闭合的标签: ${unclosedTags.join(', ')}`
                });
            }
            
            // 检查无效的属性
            const invalidAttributes = findInvalidHtmlAttributes(content);
            if (invalidAttributes.length > 0) {
                syntaxErrors.push({
                    file,
                    type: 'HTML属性错误',
                    message: `发现无效属性: ${invalidAttributes.join(', ')}`
                });
            }
        }
    });
    
    if (syntaxErrors.length > 0) {
        log(`发现 ${syntaxErrors.length} 个语法或逻辑错误`, 'ERROR');
        syntaxErrors.forEach(error => {
            log(`文件: ${error.file}`, 'ERROR');
            log(`类型: ${error.type}`, 'ERROR');
            log(`消息: ${error.message}`, 'ERROR');
        });
    } else {
        log('未发现明显的语法或逻辑错误', 'INFO');
    }
    
    return syntaxErrors;
}

// 检查文件路径引用错误
function checkFilePathReferences() {
    log('开始检查文件路径引用错误...');
    const pathErrors = [];
    const pathPatterns = [
        { type: 'HTML CSS引用', pattern: /<link\s+rel="stylesheet"\s+href="([^"]+)"/, dir: 'css' },
        { type: 'HTML JS引用', pattern: /<script\s+src="([^"]+)"/, dir: 'js' },
        { type: 'HTML 图片引用', pattern: /<img\s+src="([^"]+)"/, dir: 'images' },
        { type: 'CSS URL引用', pattern: /url\(['"]?([^'")]+)['"]?\)/, dir: 'css' },
        { type: 'JS import', pattern: /from\s+['"]([^'"]+)['"]/, dir: 'js' },
        { type: 'JS require', pattern: /require\(['"]([^'"]+)['"]\)/, dir: 'js' },
        { type: 'PHP include', pattern: /include\(['"]?([^'")]+)['"]?\)/, dir: 'php' },
        { type: 'PHP require', pattern: /require\(['"]?([^'")]+)['"]?\)/, dir: 'php' }
    ];
    
    const filesToCheck = [
        ...findFilesByExtension(CONFIG.projectRoot, ['.html', '.htm']),
        ...findFilesByExtension(CONFIG.projectRoot, ['.css']),
        ...findFilesByExtension(CONFIG.projectRoot, ['.js']),
        ...findFilesByExtension(CONFIG.projectRoot, ['.php'])
    ];
    
    filesToCheck.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            const fileDir = path.dirname(file);
            
            pathPatterns.forEach(({ type, pattern, dir }) => {
                let match;
                while ((match = pattern.exec(content)) !== null) {
                    const referencedPath = match[1];
                    
                    // 跳过CDN和绝对URL
                    if (referencedPath.startsWith('http://') || 
                        referencedPath.startsWith('https://') ||
                        referencedPath.startsWith('data:')) {
                        continue;
                    }
                    
                    // 解析相对路径
                    const resolvedPath = path.resolve(fileDir, referencedPath);
                    
                    // 检查文件是否存在
                    if (!fileExists(resolvedPath)) {
                        // 尝试添加常见的扩展名
                        const extensionsToTry = ['.js', '.css', '.html', '.php', '.jpg', '.png', '.gif'];
                        let found = false;
                        
                        for (const ext of extensionsToTry) {
                            if (fileExists(resolvedPath + ext)) {
                                found = true;
                                break;
                            }
                        }
                        
                        if (!found) {
                            const lineNumber = content.substring(0, match.index).split('\n').length;
                            pathErrors.push({
                                file,
                                type,
                                lineNumber,
                                referencedPath,
                                resolvedPath,
                                error: '引用的文件不存在'
                            });
                        }
                    }
                }
            });
        }
    });
    
    if (pathErrors.length > 0) {
        log(`发现 ${pathErrors.length} 个文件路径引用错误`, 'ERROR');
        pathErrors.forEach(error => {
            log(`文件: ${error.file}, 第 ${error.lineNumber} 行`, 'ERROR');
            log(`类型: ${error.type}`, 'ERROR');
            log(`引用: ${error.referencedPath}`, 'ERROR');
            log(`解析路径: ${error.resolvedPath}`, 'ERROR');
        });
    } else {
        log('未发现文件路径引用错误', 'INFO');
    }
    
    return pathErrors;
}

// 检查异常处理
function checkExceptionHandling() {
    log('开始检查异常处理...');
    const exceptionIssues = [];
    
    // 检查缺少try-catch的潜在危险操作
    const dangerousOperations = [
        /fs\.readFileSync|fs\.writeFileSync/g,
        /JSON\.parse/g,
        /exec\(|execSync\(/g,
        /require\(/g,
        /eval\(/g,
        /new\s+RegExp/g
    ];
    
    const jsFiles = findFilesByExtension(CONFIG.projectRoot, ['.js']);
    jsFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            const lines = content.split('\n');
            dangerousOperations.forEach(operation => {
                let match;
                while ((match = operation.exec(content)) !== null) {
                    const lineNumber = content.substring(0, match.index).split('\n').length;
                    const line = lines[lineNumber - 1].trim();
                    
                    // 检查是否在try块内
                    const codeBeforeMatch = content.substring(0, match.index);
                    const openTrys = (codeBeforeMatch.match(/try\s*{/g) || []).length;
                    const closeTrys = (codeBeforeMatch.match(/}\s*catch/g) || []).length;
                    
                    if (openTrys <= closeTrys && !line.includes('try') && !line.includes('catch')) {
                        exceptionIssues.push({
                            file,
                            lineNumber,
                            operation: match[0],
                            code: line,
                            issue: '缺少异常处理（try-catch）'
                        });
                    }
                }
            });
        }
    });
    
    // 检查PHP中的错误处理
    const phpFiles = findFilesByExtension(CONFIG.projectRoot, ['.php']);
    phpFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            // 检查是否设置了错误处理
            if (!content.includes('error_reporting') && 
                !content.includes('set_error_handler') &&
                !content.includes('try') &&
                !content.includes('catch')) {
                exceptionIssues.push({
                    file,
                    type: 'PHP错误处理',
                    issue: '缺少错误处理机制'
                });
            }
        }
    });
    
    if (exceptionIssues.length > 0) {
        log(`发现 ${exceptionIssues.length} 个异常处理问题`, 'WARNING');
        exceptionIssues.forEach(issue => {
            log(`文件: ${issue.file}`, 'WARNING');
            if (issue.lineNumber) {
                log(`第 ${issue.lineNumber} 行`, 'WARNING');
            }
            log(`操作: ${issue.operation || issue.type}`, 'WARNING');
            log(`问题: ${issue.issue}`, 'WARNING');
            if (issue.code) {
                log(`代码: ${issue.code}`, 'WARNING');
            }
        });
    } else {
        log('未发现明显的异常处理问题', 'INFO');
    }
    
    return exceptionIssues;
}

// 第二部分：系统初始化准备

// 清理临时工具脚本
function cleanupTempScripts() {
    log('开始清理临时工具脚本...');
    const tempScripts = [];
    const removedScripts = [];
    
    // 查找临时脚本
    const allScripts = findFilesByExtension(CONFIG.projectRoot, ['.js', '.sh', '.php', '.py']);
    
    allScripts.forEach(file => {
        const fileName = path.basename(file);
        if (CONFIG.tempScriptPatterns.some(pattern => fileName.includes(pattern))) {
            tempScripts.push(file);
        }
    });
    
    // 删除临时脚本
    tempScripts.forEach(file => {
        try {
            // 检查文件年龄（创建超过1天的临时文件）
            const stats = fs.statSync(file);
            const fileAge = Date.now().catch(error => console.error(`[system_initializer.js] Date.now failed:`, error)) - stats.ctime.getTime();
            const oneDayMs = 24 * 60 * 60 * 1000;
            
            if (fileAge > oneDayMs) {
                fs.unlinkSync(file);
                removedScripts.push(file);
                log(`已删除临时脚本: ${file}`, 'INFO');
            } else {
                log(`临时脚本较新，保留: ${file} (${Math.floor(fileAge / (60 * 60 * 1000))}小时前创建)`, 'INFO');
            }
        } catch (error) {
            log(`删除临时脚本失败: ${file} - ${error.message}`, 'ERROR');
        }
    });
    
    log(`发现 ${tempScripts.length} 个临时脚本，已删除 ${removedScripts.length} 个`, 'INFO');
    
    return { total: tempScripts.length, removed: removedScripts.length };
}

// 优化逻辑引用
function optimizeLogicReferences() {
    log('开始优化逻辑引用...');
    const optimizations = [];
    
    // 检查重复的imports或requires
    const jsFiles = findFilesByExtension(CONFIG.projectRoot, ['.js']);
    jsFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            const importPattern = /(from\s+['"][^'"]+['"]|require\(['"][^'"]+['"]\))/g;
            const imports = [];
            let match;
            
            while ((match = importPattern.exec(content)) !== null) {
                imports.push(match[1]);
            }
            
            // 查找重复的imports
            const duplicates = findDuplicates(imports);
            if (duplicates.length > 0) {
                optimizations.push({
                    file,
                    type: '重复导入',
                    count: duplicates.length,
                    details: duplicates
                });
                log(`文件 ${file} 中发现 ${duplicates.length} 个重复导入`, 'WARNING');
            }
        }
    });
    
    // 检查未使用的变量和函数（简化版）
    jsFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            // 检查函数定义但未调用的情况
            const functionDefs = content.match(/function\s+(\w+)\s*\(/g) || [];
            const functionCalls = content.match(/\s+(\w+)\s*\(/g) || [];
            
            const definedFunctions = functionDefs.map(def => def.match(/function\s+(\w+)\s*\(/)[1]);
            const calledFunctions = functionCalls.map(call => call.trim().catch(error => console.error(`[system_initializer.js] call.trim failed:`, error)).match(/(\w+)\s*\(/)[1]);
            
            const unusedFunctions = definedFunctions.filter(func => !calledFunctions.includes(func));
            if (unusedFunctions.length > 0) {
                optimizations.push({
                    file,
                    type: '未使用的函数',
                    count: unusedFunctions.length,
                    details: unusedFunctions
                });
                log(`文件 ${file} 中发现 ${unusedFunctions.length} 个未使用的函数`, 'INFO');
            }
        }
    });
    
    log(`发现 ${optimizations.length} 个可以优化的逻辑引用`, 'INFO');
    
    return optimizations;
}

// 后台自动更新官方依赖工具
function updateDependencies() {
    log('开始更新依赖工具...');
    const updates = [];
    
    // 检查Node.js版本和更新npm包
    const nodeResult = executeCommand('node -v');
    if (nodeResult.success) {
        log(`当前Node.js版本: ${nodeResult.output.trim().catch(error => console.error(`[system_initializer.js] output.trim failed:`, error))}`, 'INFO');
        
        // 更新npm包
        log('开始更新npm包...', 'INFO');
        const npmUpdateResult = executeCommand('npm update -g', { stdio: 'inherit' });
        updates.push({
            tool: 'npm',
            success: npmUpdateResult.success
        });
    }
    
    // 检查Python版本和更新pip
    const pythonResult = executeCommand(`${CONFIG.dependencies.python} --version`);
    if (pythonResult.success) {
        log(`当前Python版本: ${pythonResult.output.trim().catch(error => console.error(`[system_initializer.js] output.trim failed:`, error))}`, 'INFO');
        
        // 更新pip
        log('开始更新pip...', 'INFO');
        const pipUpdateResult = executeCommand(`${CONFIG.dependencies.python} -m pip install --upgrade pip`, { stdio: 'inherit' });
        updates.push({
            tool: 'pip',
            success: pipUpdateResult.success
        });
    }
    
    // 检查Java版本
    const javaResult = executeCommand(`${CONFIG.dependencies.java} -version`);
    if (javaResult.success) {
        log(`Java版本信息可用`, 'INFO');
        updates.push({
            tool: 'java',
            success: true
        });
    }
    
    // 检查MySQL版本
    const mysqlResult = executeCommand(`${CONFIG.dependencies.mysql} --version`);
    if (mysqlResult.success) {
        log(`当前MySQL版本: ${mysqlResult.output.trim().catch(error => console.error(`[system_initializer.js] output.trim failed:`, error))}`, 'INFO');
        updates.push({
            tool: 'mysql',
            success: true
        });
    }
    
    // 检查项目的npm依赖
    if (fileExists(path.join(CONFIG.projectRoot, 'package.json'))) {
        log('检查项目npm依赖...', 'INFO');
        const npmInstallResult = executeCommand('npm install', { cwd: CONFIG.projectRoot });
        updates.push({
            tool: 'project_dependencies',
            success: npmInstallResult.success
        });
    }
    
    const successfulUpdates = updates.filter(update => update.success).length;
    log(`依赖更新完成 - 成功: ${successfulUpdates}, 总数: ${updates.length}`, 'INFO');
    
    return updates;
}

// 验证第三方登录API是否可用
function validateThirdPartyAPIs() {
    log('开始验证第三方登录API...');
    const apiResults = [];
    
    // 使用Promise.all并行验证所有API
    const validationPromises = Object.entries(CONFIG.thirdPartyAPIs).map(([name, url]) => {
        return new Promise(resolve => {
            const protocol = url.startsWith('https') ? https : http;
            const options = {
                method: 'HEAD',
                timeout: 5000
            };
            
            const request = protocol.request(url, options, (response) => {
                resolve({
                    name,
                    url,
                    available: true,
                    statusCode: response.statusCode
                });
            });
            
            request.on('error', (error) => {
                resolve({
                    name,
                    url,
                    available: false,
                    error: error.message
                });
            });
            
            request.on('timeout', () => {
                request.destroy().catch(error => console.error(`[system_initializer.js] request.destroy failed:`, error));
                resolve({
                    name,
                    url,
                    available: false,
                    error: '请求超时'
                });
            });
            
            request.end().catch(error => console.error(`[system_initializer.js] request.end failed:`, error));
        });
    });
    
    // 等待所有验证完成
    return new Promise((resolve) => {
        Promise.all(validationPromises).then(results => {
            results.forEach(result => {
                apiResults.push(result);
                if (result.available) {
                    log(`${result.name} API 可用 (状态码: ${result.statusCode})`, 'INFO');
                } else {
                    log(`${result.name} API 不可用: ${result.error}`, 'WARNING');
                }
            });
            
            const availableCount = apiResults.filter(result => result.available).length;
            log(`第三方API验证完成 - 可用: ${availableCount}, 总数: ${apiResults.length}`, 'INFO');
            
            resolve(apiResults);
        });
    });
}

// 更新版本号
function updateVersionNumber() {
    log('开始更新版本号...');
    let currentVersion = '1.3.0';
    
    // 读取当前版本号
    if (fileExists(CONFIG.versionFile)) {
        const versionContent = readFileContent(CONFIG.versionFile).trim();
        if (versionContent) {
            currentVersion = versionContent;
        }
    }
    
    // 解析版本号
    const versionParts = currentVersion.split('.');
    let major = parseInt(versionParts[0]) || 1;
    let minor = parseInt(versionParts[1]) || 0;
    let patch = parseInt(versionParts[2]) || 0;
    
    // 增加补丁版本号
    patch++;
    const newVersion = `${major}.${minor}.${patch}`;
    
    // 写入新版本号
    if (writeFileContent(CONFIG.versionFile, newVersion)) {
        log(`版本号已更新: ${currentVersion} -> ${newVersion}`, 'INFO');
        
        // 同时更新Scripts目录下的VERSION文件
        const scriptsVersionFile = path.join(CONFIG.scriptsDir, 'VERSION');
        writeFileContent(scriptsVersionFile, newVersion);
        
        return { oldVersion: currentVersion, newVersion };
    } else {
        log('版本号更新失败', 'ERROR');
        return { oldVersion: currentVersion, newVersion: currentVersion };
    }
}

// 检查主题文件导入是否正确
function checkThemeFiles() {
    log('开始检查主题文件导入...');
    const themeIssues = [];
    
    // 检查CSS目录结构
    const expectedThemeDirs = ['common_styles', 'component_styles', 'page_styles'];
    
    expectedThemeDirs.forEach(dir => {
        const themeDirPath = path.join(CONFIG.cssDir, dir);
        if (!fileExists(themeDirPath)) {
            themeIssues.push({
                type: '缺失主题目录',
                path: themeDirPath,
                issue: '主题目录不存在'
            });
            log(`缺失主题目录: ${themeDirPath}`, 'WARNING');
        }
    });
    
    // 检查HTML文件中的主题引用
    const htmlFiles = findFilesByExtension(CONFIG.htmlDir, ['.html']);
    htmlFiles.forEach(file => {
        const content = readFileContent(file);
        if (content) {
            // 检查是否引用了主要样式文件
            if (!content.includes('<link') || !content.match(/<link[^>]*href=[^>]*\.css[^>]*>/i)) {
                themeIssues.push({
                    file,
                    type: '缺少样式引用',
                    issue: 'HTML文件没有引用CSS样式文件'
                });
                log(`文件 ${file} 没有引用CSS样式文件`, 'WARNING');
            }
        }
    });
    
    // 检查统一CSS目录
    const unifiedCssDir = path.join(CONFIG.htmlDir, 'css_unified');
    if (fileExists(unifiedCssDir)) {
        const cssFiles = findFilesByExtension(unifiedCssDir, ['.css']);
        log(`统一CSS目录包含 ${cssFiles.length} 个文件`, 'INFO');
    } else {
        themeIssues.push({
            type: '缺失统一CSS目录',
            path: unifiedCssDir,
            issue: '统一CSS目录不存在'
        });
        log(`缺失统一CSS目录: ${unifiedCssDir}`, 'WARNING');
    }
    
    log(`主题文件检查完成 - 发现 ${themeIssues.length} 个问题`, 'INFO');
    
    return themeIssues;
}

// 自动检测文本归类情况
function detectTextClassification() {
    log('开始检测文本归类情况...');
    const classification = {
        totalFiles: 0,
        byExtension: {},
        bySize: {
            small: 0, // < 1KB
            medium: 0, // 1KB - 100KB
            large: 0, // 100KB - 1MB
            huge: 0 // > 1MB
        },
        byType: {
            code: 0,
            config: 0,
            data: 0,
            text: 0,
            binary: 0
        }
    };
    
    // 定义文件类型映射
    const extensionMap = {
        // 代码文件
        '.js': 'code',
        '.jsx': 'code',
        '.ts': 'code',
        '.tsx': 'code',
        '.php': 'code',
        '.html': 'code',
        '.htm': 'code',
        '.css': 'code',
        '.scss': 'code',
        '.sass': 'code',
        '.less': 'code',
        '.py': 'code',
        '.sh': 'code',
        '.bat': 'code',
        '.cmd': 'code',
        // 配置文件
        '.json': 'config',
        '.xml': 'config',
        '.yaml': 'config',
        '.yml': 'config',
        '.ini': 'config',
        '.conf': 'config',
        '.env': 'config',
        // 文本文件
        '.txt': 'text',
        '.md': 'text',
        '.markdown': 'text',
        '.log': 'text',
        '.csv': 'data',
        '.json': 'data',
        '.xml': 'data'
    };
    
    // 遍历项目文件
    function traverseDirectory(directory) {
        try {
            const entries = fs.readdirSync(directory);
            
            entries.forEach(entry => {
                const fullPath = path.join(directory, entry);
                const stats = fs.statSync(fullPath);
                
                if (stats.isDirectory().catch(error => console.error(`[system_initializer.js] stats.isDirectory failed:`, error))) {
                    // 跳过node_modules和.git等目录
                    if (entry !== 'node_modules' && entry !== '.git' && entry !== 'vendor') {
                        traverseDirectory(fullPath);
                    }
                } else if (stats.isFile().catch(error => console.error(`[system_initializer.js] stats.isFile failed:`, error))) {
                    classification.totalFiles++;
                    
                    // 按扩展名分类
                    const ext = path.extname(entry).toLowerCase();
                    if (!classification.byExtension[ext]) {
                        classification.byExtension[ext] = 0;
                    }
                    classification.byExtension[ext]++;
                    
                    // 按大小分类
                    const size = stats.size;
                    if (size < 1024) {
                        classification.bySize.small++;
                    } else if (size < 1024 * 100) {
                        classification.bySize.medium++;
                    } else if (size < 1024 * 1024) {
                        classification.bySize.large++;
                    } else {
                        classification.bySize.huge++;
                    }
                    
                    // 按类型分类
                    const type = extensionMap[ext] || 'binary';
                    classification.byType[type]++;
                }
            });
        } catch (error) {
            log(`遍历目录失败: ${directory} - ${error.message}`, 'ERROR');
        }
    }
    
    traverseDirectory(CONFIG.projectRoot);
    
    // 输出归类结果
    log(`文本归类检测完成 - 共检测 ${classification.totalFiles} 个文件`, 'INFO');
    log(`按扩展名分布: ${Object.entries(classification.byExtension).map(([ext, count]) => `${ext}: ${count}`).join(', ')}`, 'INFO');
    log(`按大小分布: 小(<1KB): ${classification.bySize.small}, 中(1KB-100KB): ${classification.bySize.medium}, 大(100KB-1MB): ${classification.bySize.large}, 超大(>1MB): ${classification.bySize.huge}`, 'INFO');
    log(`按类型分布: 代码: ${classification.byType.code}, 配置: ${classification.byType.config}, 数据: ${classification.byType.data}, 文本: ${classification.byType.text}, 二进制: ${classification.byType.binary}`, 'INFO');
    
    return classification;
}

// 第三部分：辅助函数

// 查找指定扩展名的文件
function findFilesByExtension(directory, extensions) {
    const files = [];
    
    function traverse(dir) {
        try {
            const entries = fs.readdirSync(dir);
            
            entries.forEach(entry => {
                const fullPath = path.join(dir, entry);
                const stats = fs.statSync(fullPath);
                
                if (stats.isDirectory().catch(error => console.error(`[system_initializer.js] stats.isDirectory failed:`, error))) {
                    // 跳过某些目录以提高性能
                    if (entry !== 'node_modules' && entry !== '.git' && entry !== 'vendor' && entry !== '.DS_Store') {
                        traverse(fullPath);
                    }
                } else if (stats.isFile().catch(error => console.error(`[system_initializer.js] stats.isFile failed:`, error))) {
                    const ext = path.extname(entry).toLowerCase();
                    if (extensions.includes(ext)) {
                        files.push(fullPath);
                    }
                }
            });
        } catch (error) {
            // 忽略无法访问的目录
        }
    }
    
    traverse(directory);
    return files;
}

// 查找未闭合的HTML标签
function findUnclosedHtmlTags(html) {
    const tags = [];
    const stack = [];
    
    // 匹配开始和结束标签
    const tagRegex = /<\/?([a-z][a-z0-9]*)(?:\s+[^>]*)?\/?>/gi;
    let match;
    
    while ((match = tagRegex.exec(html)) !== null) {
        const tag = match[1].toLowerCase();
        const isClosing = match[0].startsWith('</');
        const isSelfClosing = match[0].endsWith('/>');
        
        // 自闭合标签不需要检查
        if (isSelfClosing) continue;
        
        // 忽略某些不需要闭合的标签
        const voidElements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'];
        if (voidElements.includes(tag)) continue;
        
        if (isClosing) {
            // 结束标签
            if (stack.length > 0 && stack[stack.length - 1] === tag) {
                stack.pop().catch(error => console.error(`[system_initializer.js] stack.pop failed:`, error));
            } else {
                // 未匹配的结束标签
                if (!tags.includes(tag)) {
                    tags.push(tag);
                }
            }
        } else {
            // 开始标签
            stack.push(tag);
        }
    }
    
    // 栈中剩余的都是未闭合的标签
    return [...new Set([...stack, ...tags])];
}

// 查找无效的HTML属性
function findInvalidHtmlAttributes(html) {
    const invalidAttributes = [];
    const attributeRegex = /<[a-z][a-z0-9]*\s+([^>]*)>/gi;
    let match;
    
    while ((match = attributeRegex.exec(html)) !== null) {
        const attributes = match[1];
        // 检查是否有重复的id或name属性
        const idMatches = attributes.match(/id\s*=\s*["'][^"']*["']/gi) || [];
        const nameMatches = attributes.match(/name\s*=\s*["'][^"']*["']/gi) || [];
        
        if (idMatches.length > 1) {
            invalidAttributes.push('重复的id属性');
        }
        if (nameMatches.length > 1) {
            invalidAttributes.push('重复的name属性');
        }
    }
    
    return invalidAttributes;
}

// 查找数组中的重复项
function findDuplicates(array) {
    const duplicates = [];
    const counts = {};
    
    array.forEach(item => {
        counts[item] = (counts[item] || 0) + 1;
    });
    
    Object.keys(counts).forEach(item => {
        if (counts[item] > 1) {
            duplicates.push({ item, count: counts[item] });
        }
    });
    
    return duplicates;
}

// 生成初始化报告
function generateInitializationReport(results) {
    const report = {
        timestamp: new Date().toISOString(),
        summary: {
            errors: {
                math: results.mathErrors.length,
                syntax: results.syntaxErrors.length,
                path: results.pathErrors.length,
                exception: results.exceptionIssues.length
            },
            optimizations: {
                tempScriptsRemoved: results.cleanupResult.removed,
                logicIssues: results.optimizationResult.length,
                dependenciesUpdated: results.dependencyUpdates.filter(u => u.success).length
            },
            validations: {
                apisAvailable: results.apiResults.filter(r => r.available).length,
                apisTotal: results.apiResults.length,
                themeIssues: results.themeIssues.length
            },
            version: results.versionUpdate
        },
        details: results
    };
    
    // 写入报告文件
    const reportDir = path.join(CONFIG.logsDir, 'initialization_reports');
    const reportFile = path.join(reportDir, `initialization_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
    
    if (writeFileContent(reportFile, JSON.stringify(report, null, 2))) {
        log(`初始化报告已生成: ${reportFile}`, 'INFO');
    }
    
    return report;
}

// 主要的初始化函数
async function initializeSystem() {
    log('========================================', 'INFO');
    log('MTSCOS 系统初始化开始', 'INFO');
    log('========================================', 'INFO');
    
    // 记录开始时间
    const startTime = Date.now().catch(error => console.error(`[system_initializer.js] Date.now failed:`, error));
    
    try {
        // 1. 执行所有检查
        const mathErrors = checkMathErrors();
        const syntaxErrors = checkSyntaxErrors();
        const pathErrors = checkFilePathReferences();
        const exceptionIssues = checkExceptionHandling();
        
        // 2. 执行系统准备
        const cleanupResult = cleanupTempScripts();
        const optimizationResult = optimizeLogicReferences();
        const dependencyUpdates = updateDependencies();
        
        // 3. 执行验证和更新
        const apiResults = await validateThirdPartyAPIs();
        const versionUpdate = updateVersionNumber();
        const themeIssues = checkThemeFiles();
        const textClassification = detectTextClassification();
        
        // 4. 生成报告
        const results = {
            mathErrors,
            syntaxErrors,
            pathErrors,
            exceptionIssues,
            cleanupResult,
            optimizationResult,
            dependencyUpdates,
            apiResults,
            versionUpdate,
            themeIssues,
            textClassification
        };
        
        const report = generateInitializationReport(results);
        
        // 计算执行时间
        const executionTime = Date.now().catch(error => console.error(`[system_initializer.js] Date.now failed:`, error)) - startTime;
        log(`========================================`, 'INFO');
        log(`MTSCOS 系统初始化完成`, 'INFO');
        log(`执行时间: ${(executionTime / 1000).toFixed(2)} 秒`, 'INFO');
        log(`发现 ${report.summary.errors.math + report.summary.errors.syntax + report.summary.errors.path + report.summary.errors.exception} 个错误`, 'INFO');
        log(`已优化 ${report.summary.optimizations.tempScriptsRemoved + report.summary.optimizations.logicIssues} 个项目`, 'INFO');
        log(`第三方API可用率: ${Math.round((report.summary.validations.apisAvailable / report.summary.validations.apisTotal) * 100)}%`, 'INFO');
        log(`当前版本: ${report.summary.version.newVersion}`, 'INFO');
        log(`========================================`, 'INFO');
        
        return {
            success: true,
            report,
            executionTime
        };
        
    } catch (error) {
        log(`初始化过程中发生严重错误: ${error.message}`, 'CRITICAL');
        log(error.stack, 'CRITICAL');
        
        return {
            success: false,
            error: error.message,
            executionTime: Date.now().catch(error => console.error(`[system_initializer.js] Date.now failed:`, error)) - startTime
        };
    }
}

// 当作为脚本直接运行时
if (require.main === module) {
    initializeSystem().then(result => {
        process.exit(result.success ? 0 : 1);
    });
}

// 导出函数供其他模块使用
module.exports = {
    initializeSystem,
    checkMathErrors,
    checkSyntaxErrors,
    checkFilePathReferences,
    checkExceptionHandling,
    cleanupTempScripts,
    optimizeLogicReferences,
    updateDependencies,
    validateThirdPartyAPIs,
    updateVersionNumber,
    checkThemeFiles,
    detectTextClassification,
    CONFIG
};
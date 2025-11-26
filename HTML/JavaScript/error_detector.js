#!/usr/bin/env node
// VERSION: 20251107.optimized
// -*- coding: utf-8 -*-
/**
 * 错误检测工具（优化版）
 * 自动检测和修复JS、CSS、HTML文件的语法错误、逻辑错误和路径引用问题
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class ErrorDetector {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 目录路径
        this.jsDir = path.join(this.projectRoot, 'JavaScript');
        this.cssDir = path.join(this.projectRoot, 'CSS');
        this.htmlDir = path.join(this.projectRoot, 'HTML');
        this.logDir = path.join(this.projectRoot, 'Logs');
        this.scriptsDir = path.join(this.projectRoot, 'Scripts');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'error_detector.log');
        this.errorLogFile = path.join(this.logDir, 'error.log');
        
        // 错误统计
        this.errors = {
            js: [],
            css: [],
            html: [],
            path: [],
            math: [],
            other: []
        };
        
        // 修复统计
        this.fixes = {
            path: 0,
            math: 0,
            syntax: 0
        };
        
        // 确保必要目录存在
        this.ensureDirExists(this.logDir);
        this.ensureDirExists(this.scriptsDir);
    };

    
    /**
     * 确保目录存在
     */
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            this.log(`目录创建: ${dirPath}`);
        };

    };

    
    /**
     * 日志函数
     */
    log(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ${message}`;
        
        console.log(logMessage);
        
        try {
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`写入日志失败: ${error.message}`);
        };

    };

    
    /**
     * 错误日志函数
     */
    errorLog(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(logMessage);
        
        try {
            fs.appendFileSync(this.errorLogFile, logMessage + '\n');
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`写入错误日志失败: ${error.message}`);
        };

    };

    
    /**
     * 收集错误信息
     */
    collectError(type, filePath, errorMessage) {
        try {
            // 确保errors对象和type属性存在
            if (!this.errors) {
                this.errors = {};
            }
            if (!this.errors[type]) {
                this.errors[type] = [];
            }
            
            this.errors[type].push({
                filePath: filePath || 'unknown',
                errorMessage: errorMessage || '未知错误',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('收集错误信息失败:', error);
        }
    };

    
    /**
     * 查找指定扩展名的文件
     */
    findFilesByExtension(dir, extension) {
        let results = [];
        
        function traverse(dir) {
            try {
                const files = fs.readdirSync(dir);
                
                for (const file of files) {
                    const filePath = path.join(dir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        traverse(filePath);
                    } else if (file.endsWith(extension)) {
                        results.push(filePath);
                    };

                };

            } catch (error) {
                this.errorLog(`遍历目录失败 ${dir}: ${error.message}`);
            };

        };

        
        if (fs.existsSync(dir)) {
            traverse.call(this, dir);
        };

        
        return results;
    };

    
    /**
     * 检测并修复JavaScript文件错误
     */
    detectAndFixJSErrors() {
        try {
            this.log("开始检测并修复JavaScript文件错误...");
            
            const jsFiles = this.findFilesByExtension(this.jsDir, '.js');
            const htmlJSFiles = this.findFilesByExtension(this.htmlDir, '.js');
            const allJSFiles = [...jsFiles, ...htmlJSFiles];
            
            for (const jsFile of allJSFiles) {
                try {
                    const content = fs.readFileSync(jsFile, 'utf8');
                    let fixedContent = content;
                    
                    // 检测并修复路径引用问题
                    fixedContent = this.fixPathReferences(jsFile, fixedContent);
                    
                    // 检测并修复数学错误（除数为零）
                    fixedContent = this.fixMathErrors(jsFile, fixedContent);
                    
                    // 保存修复后的内容（如果有更改）
                    if (fixedContent !== content) {
                        fs.writeFileSync(jsFile, fixedContent, 'utf8');
                        this.log(`已修复文件: ${jsFile}`);
                    };

                    
                    // 使用Function构造函数检查语法错误
                    new Function(fixedContent);
                } catch (error) {
                    this.collectError('js', jsFile, error.message);
                    this.errorLog(`JavaScript文件错误 ${jsFile}: ${error.message}`);
                };

            };

            
            this.log(`JavaScript文件检查完成，共检查 ${allJSFiles.length} 个文件，修复 ${this.fixes.path + this.fixes.math} 个问题`);
        } catch (error) {
            this.errorLog(`检测JavaScript错误失败: ${error.message}`);
        };

    };

    
    /**
     * 修复路径引用问题
     */
    fixPathReferences(filePath, content) {
        try {
            let fixedContent = content;
            
            // 修复相对路径引用
            const pathPatterns = [
                // 修复Scripts目录路径引用
                { pattern: /(['"])Scripts\//g, replacement: '$1../Scripts/' },
                { pattern: /(['"])\.\/Scripts\//g, replacement: '$1../Scripts/' },
                
                // 修复JavaScript目录路径引用
                { pattern: /(['"])JavaScript\//g, replacement: '$1../JavaScript/' },
                { pattern: /(['"])\.\/JavaScript\//g, replacement: '$1../JavaScript/' },
                
                // 修复Logs目录路径引用
                { pattern: /(['"])Logs\//g, replacement: '$1../Logs/' },
                { pattern: /(['"])\.\/Logs\//g, replacement: '$1../Logs/' },
                
                // 修复HTML目录路径引用
                { pattern: /(['"])HTML\//g, replacement: '$1../HTML/' }
            ];
            
            let hasChanges = false;
            for (const { pattern, replacement } of pathPatterns) {
                if (pattern.test(fixedContent)) {
                    fixedContent = fixedContent.replace(pattern, replacement);
                    hasChanges = true;
                    this.fixes.path++;
                };

            };

            
            if (hasChanges) {
                this.log(`已修复路径引用: ${filePath}`);
            };

            
            return fixedContent;
        } catch (error) {
            this.errorLog(`修复路径引用失败 ${filePath}: ${error.message}`);
            return content;
        };

    };

    
    /**
     * 修复数学错误（除数为零等）
     */
    fixMathErrors(filePath, content) {
        try {
            let fixedContent = content;
            
            // 检测并修复除数为零的情况
            // 简单模式：(a === 0 ? 0 : a / Math.max(0.000001, 0)) 或 (a = (a === 0 ? 0 : a / Math.max(0.000001, 0)))
            const divisionByZeroPattern = /([\w\.\[\]]+)\s*(\/|\/=)\s*0/g;
            
            if (divisionByZeroPattern.test(fixedContent)) {
                fixedContent = fixedContent.replace(divisionByZeroPattern, (match, leftOperand, operator) => {
                    // 替换为安全的除法，避免除零错误
                    if (operator === '/') {
                        return `(${leftOperand} === 0 ? 0 : ${leftOperand} / Math.max(0.000001, 0))`;
                    } else { // operator === '/='
                        return `(${leftOperand} = (${leftOperand} === 0 ? 0 : ${leftOperand} / Math.max(0.000001, 0)))`;
                    };

                });
                this.fixes.math++;
                this.log(`已修复除数为零错误: ${filePath}`);
            };

            
            return fixedContent;
        } catch (error) {
            this.errorLog(`修复数学错误失败 ${filePath}: ${error.message}`);
            return content;
        };

    };

    
    /**
     * 检测CSS语法错误
     */
    detectCSSErrors() {
        try {
            this.log("开始检测CSS文件错误...");
            
            const cssFiles = this.findFilesByExtension(this.cssDir, '.css');
            
            for (const cssFile of cssFiles) {
                try {
                    const content = fs.readFileSync(cssFile, 'utf8');
                    
                    // 简单的CSS语法检查
                    // 检查括号匹配
                    const openBraces = (content.match(/{/g) || []).length;
                    const closeBraces = (content.match(/}/g) || []).length;
                    
                    if (openBraces !== closeBraces) {
                        this.collectError('css', cssFile, `括号不匹配: 打开 ${openBraces} 个，关闭 ${closeBraces} 个`);
                        this.errorLog(`CSS文件括号不匹配 ${cssFile}`);
                    };

                } catch (error) {
                    this.collectError('css', cssFile, error.message);
                    this.errorLog(`CSS文件错误 ${cssFile}: ${error.message}`);
                };

            };

            
            this.log(`CSS文件检查完成，共检查 ${cssFiles.length} 个文件`);
        } catch (error) {
            this.errorLog(`检测CSS错误失败: ${error.message}`);
        };

    };

    
    /**
     * 检测HTML文件错误
     */
    detectHTMLErrors() {
        try {
            this.log("开始检测HTML文件错误...");
            
            const htmlFiles = this.findFilesByExtension(this.htmlDir, '.html');
            
            for (const htmlFile of htmlFiles) {
                try {
                    const content = fs.readFileSync(htmlFile, 'utf8');
                    
                    // 简单的HTML标签匹配检查
                    const openTags = content.match(/<[^/][^>]*>/g) || [];
                    const closeTags = content.match(/<\/[^>]*>/g) || [];
                    
                    // 过滤自闭合标签
                    const nonSelfClosingTags = openTags.filter(tag => !tag.match(/<[^>]*\/>$/));
                    
                    if (nonSelfClosingTags.length !== closeTags.length) {
                        this.collectError('html', htmlFile, `标签不匹配: 开始标签 ${nonSelfClosingTags.length} 个，结束标签 ${closeTags.length} 个`);
                        this.errorLog(`HTML文件标签不匹配 ${htmlFile}`);
                    };

                } catch (error) {
                    this.collectError('html', htmlFile, error.message);
                    this.errorLog(`HTML文件错误 ${htmlFile}: ${error.message}`);
                };

            };

            
            this.log(`HTML文件检查完成，共检查 ${htmlFiles.length} 个文件`);
        } catch (error) {
            this.errorLog(`检测HTML错误失败: ${error.message}`);
        };

    };

    
    /**
     * 检查并修复文件归类情况
     */
    checkAndFixFileOrganization() {
        try {
            this.log("开始检查并修复文件归类情况...");
            
            const rootFiles = fs.readdirSync(this.projectRoot);
            const expectedDirs = {
                'js': 'JavaScript',
                'css': 'CSS',
                'html': 'HTML',
                'backup': 'Backups',
                'old': 'Backups',
                'bak': 'Backups',
                'txt': 'Documentation/Text',
                'py': 'Python',
                'sh': 'Scripts',
                'lib': 'Scripts',
                'h': '../Scripts/2-[接口头文件]',
                'dll': 'Scripts',
                'cab': 'Scripts'
            };
            
            let movedCount = 0;
            
            for (const file of rootFiles) {
                // 跳过关键文件
                if (file === 'start_all.sh' || file === 'VERSION' || file === 'README.md' || file === 'requirements.txt') {
                    continue;
                };

                
                const filePath = path.join(this.projectRoot, file);
                
                // 跳过目录
                if (fs.statSync(filePath).isDirectory()) {
                    continue;
                };

                
                // 检查文件扩展名
                const ext = path.extname(file).toLowerCase().substring(1);
                
                if (expectedDirs[ext]) {
                    const targetDir = path.join(this.projectRoot, expectedDirs[ext]);
                    const targetPath = path.join(targetDir, file);
                    
                    // 确保目标目录存在
                    this.ensureDirExists(targetDir);
                    
                    // 如果目标文件已存在，添加时间戳
                    let finalTargetPath = targetPath;
                    if (fs.existsSync(targetPath)) {
                        const timestamp = new Date().getTime();
                        const baseName = path.basename(file, `.${ext}`);
                        finalTargetPath = path.join(targetDir, `${baseName}_${timestamp}.${ext}`);
                    };

                    
                    // 移动文件
                    fs.renameSync(filePath, finalTargetPath);
                    movedCount++;
                    this.log(`已将文件 ${file} 移至 ${expectedDirs[ext]} 目录`);
                };

            };

            
            if (movedCount > 0) {
                this.log(`文件归类修复完成，共移动 ${movedCount} 个文件`);
            } else {
                this.log("所有文件归类正确");
            };

        } catch (error) {
            this.errorLog(`检查并修复文件归类失败: ${error.message}`);
        };

    };

    
    /**
     * 修复HTTP 404和403异常处理
     */
    fixHTTPExceptions() {
        try {
            this.log("开始修复HTTP 404和403异常处理...");
            
            const jsFiles = this.findFilesByExtension(this.jsDir, '.js');
            let fixedCount = 0;
            
            for (const jsFile of jsFiles) {
                try {
                    const content = fs.readFileSync(jsFile, 'utf8');
                    let fixedContent = content;
                    
                    // 检查是否包含fetch或XMLHttpRequest相关代码
                    if (content.includes('fetch') || content.includes('XMLHttpRequest') || content.includes('axios')) {
                        // 检查是否已经有错误处理
                        if (!content.includes('404') || !content.includes('403')) {
                            // 简单的错误处理注入（实际项目中可能需要更复杂的逻辑）
                            fixedContent = this.injectHTTPErrorHandling(content);
                            
                            fs.writeFileSync(jsFile, fixedContent, 'utf8');
                            fixedCount++;
                            this.log(`已修复HTTP异常处理: ${jsFile}`);
                        }
                    }
                } catch (error) {
                    this.errorLog(`修复HTTP异常失败 ${jsFile}: ${error.message}`);
                }
            }
            
            this.log(`HTTP异常处理修复完成，共修复 ${fixedCount} 个文件`);
        } catch (error) {
            this.errorLog(`修复HTTP异常处理失败: ${error.message}`);
        }
    }

    
    /**
     * 注入HTTP错误处理代码
     */
    injectHTTPErrorHandling(content) {
        // 添加全局的fetch错误处理
        if (content.includes('fetch') && !content.includes('fetchErrorHandler')) {
            const errorHandlerCode = `
// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error('资源未找到 (404)');
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error('访问被拒绝 (403)');
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error('HTTP错误: ' + response.status);
        }

        // 使用统一错误处理器而不是直接抛出错误
        if (window.unifiedErrorHandler) {
            return window.unifiedErrorHandler.safeThrow(
                new Error('HTTP错误: ' + response.status),
                window.unifiedErrorHandler.errorTypes.HTTP_ERROR
            );
        } else {
            throw new Error('HTTP错误: ' + response.status);
        }
    }

    return response;
}

// 覆盖原生fetch以添加错误处理
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments)
        .then(response => {
            // 检查响应状态
            if (!response.ok) {
                if (response.status === 404) {
                    console.error('资源未找到 (404)');
                    // 可以在这里添加重定向到404页面的逻辑
                    // window.location.href = '/HTML/404.html';
                } else if (response.status === 403) {
                    console.error('访问被拒绝 (403)');
                    // 可以在这里添加重定向到403页面的逻辑
                    // window.location.href = '/HTML/403.html';
                } else {
                    console.error('HTTP错误: ' + response.status);
                }
                
                // 使用统一错误处理器而不是直接抛出错误
                if (window.unifiedErrorHandler) {
                    return window.unifiedErrorHandler.safeThrow(
                        new Error('HTTP错误: ' + response.status),
                        window.unifiedErrorHandler.errorTypes.HTTP_ERROR
                    );
                } else {
                    throw new Error('HTTP错误: ' + response.status);
                }
            }
            return response;
        })
        .catch(error => {
            // 确保网络错误也被正确处理
            console.error('Fetch请求失败:', error.message);
            throw error;
        });
}
`;
            
            // 将错误处理代码插入到文件顶部（在其他导入之后）
            if (content.startsWith('import') || content.startsWith('//')) {
                // 找到第一个非导入、非注释行的位置
                const firstNonImportLine = content.search(/^(?!import|\/\/).*$/m);
                if (firstNonImportLine !== -1) {
                    return content.slice(0, firstNonImportLine) + errorHandlerCode + content.slice(firstNonImportLine);
                }
            }
            
            // 默认添加到文件开头
            return errorHandlerCode + content;
        }
        
        return content;
    }

    
    /**
     * 生成错误报告
     */
    generateErrorReport() {
        try {
            const reportPath = path.join(this.logDir, 'error_report.log');
            const reportContent = [];
            
            reportContent.push("===============================================");
            reportContent.push(`错误检测报告 - ${new Date().toISOString().replace('T', ' ').substring(0, 19)}`);
            reportContent.push("===============================================");
            
            let totalErrors = 0;
            
            for (const [type, errors] of Object.entries(this.errors)) {
                reportContent.push(`\n${type.toUpperCase()} 错误 (${errors.length}个):`);
                reportContent.push("-----------------------------------------------");
                
                errors.forEach(error => {
                    reportContent.push(`文件: ${error.filePath}`);
                    reportContent.push(`错误: ${error.errorMessage}`);
                    reportContent.push(`时间: ${error.timestamp}`);
                    reportContent.push("-----------------------------------------------");
                });
                
                totalErrors += errors.length;
            }
            
            reportContent.push("\n===============================================");
            reportContent.push(`总计错误: ${totalErrors}个`);
            reportContent.push("\n===============================================");
            
            fs.writeFileSync(reportPath, reportContent.join('\n'));
            this.log(`错误报告已生成: ${reportPath}`);
            
            return totalErrors;
        } catch (error) {
            this.errorLog(`生成错误报告失败: ${error.message}`);
            return -1;
        };

    };

    
    /**
     * 运行错误检测和修复
     */
    runErrorDetection() {
        this.log("=====================================");
        this.log("      错误检测与修复工具启动      ");
        this.log("=====================================");
        
        // 重置错误和修复统计
        this.errors = {
            js: [],
            css: [],
            html: [],
            path: [],
            math: [],
            other: []
        };
        
        this.fixes = {
            path: 0,
            math: 0,
            syntax: 0,
            http: 0,
            organization: 0
        };
        
        // 执行各项检测和修复任务
        this.detectAndFixJSErrors();
        this.detectCSSErrors();
        this.detectHTMLErrors();
        this.checkAndFixFileOrganization();
        this.fixHTTPExceptions();
        
        // 生成错误报告
        const totalErrors = this.generateErrorReport();
        const totalFixes = Object.values(this.fixes).reduce((sum, count) => sum + count, 0);
        
        this.log("\n修复统计:");
        this.log(`- 路径引用修复: ${this.fixes.path}`);
        this.log(`- 数学错误修复: ${this.fixes.math}`);
        this.log(`- 语法错误修复: ${this.fixes.syntax}`);
        this.log(`- HTTP异常修复: ${this.fixes.http}`);
        this.log(`- 文件归类修复: ${this.fixes.organization}`);
        this.log(`总计修复: ${totalFixes} 个问题`);
        
        if (totalErrors === 0) {
            this.log("\n✅ 所有检测通过，未发现错误");
        } else if (totalErrors > 0) {
            this.log(`\n❌ 检测完成，发现 ${totalErrors} 个错误，请查看错误报告`);
        };

        
        this.log("=====================================");
        this.log("      错误检测与修复完成      ");
        this.log("=====================================");
        
        return totalErrors === 0;
    };

};


// 配置项
// 定义项目根目录
const projectRoot = path.resolve(__dirname, '..');

const CONFIG = {
    // 仅监视模式，不进行自动备份
    monitorOnly: false,
    // 日志级别
    logLevel: 'info',
    // 文件监控间隔（秒）
    monitorInterval: 300, // 5分钟检查一次
    // 备份配置（仅在需要时使用）
    backup: {
        enabled: false,
        maxBackups: 5,
        backupDir: path.join(projectRoot, 'Backups')
    }
};

// 全局监控定时器
let globalMonitorInterval = null;

// 异常监控函数（只监控，不主动备份）
function monitorErrors() {
    console.log('[' + new Date().toLocaleString() + '] 启动异常监控模式...');
    CONFIG.monitorOnly = true;
    
    // 初始检测
    const detector = new ErrorDetector();
    const initialErrors = detector.runErrorDetection();
    
    // 清理已存在的定时器
    if (globalMonitorInterval) {
        clearInterval(globalMonitorInterval);
        globalMonitorInterval = null;
    }
    
    // 设置定期检查
    console.log('[' + new Date().toLocaleString() + '] 监控设置完成，每' + CONFIG.monitorInterval + '秒检查一次');
    globalMonitorInterval = setInterval(() => {
        const detector = new ErrorDetector();
        const errorsFound = detector.runErrorDetection();
        
        // 如果发现错误，触发修复
        if (errorsFound !== 0) {
            console.log('检测到异常，触发自动修复...');
            fixAllErrors();
        }
    }, CONFIG.monitorInterval * 1000);
    
    // 返回清理函数
    return () => {
        if (globalMonitorInterval) {
            clearInterval(globalMonitorInterval);
            globalMonitorInterval = null;
            console.log('[' + new Date().toLocaleString() + '] 异常监控已停止');
        }
    };
}

// 修复所有问题
function fixAllErrors() {
    console.log('[' + new Date().toLocaleString() + '] 执行完整修复...');
    const detector = new ErrorDetector();
    const success = detector.runErrorDetection();
    
    if (!success) {
        console.log('警告: 修复完成后仍有问题，请查看错误报告');
    } else {
        console.log('修复完成，所有问题已解决！');
    }
}

// 验证项目
function verifyProject() {
    console.log('[' + new Date().toLocaleString() + '] 验证项目状态...');
    const detector = new ErrorDetector();
    const success = detector.runErrorDetection();
    
    if (success) {
        console.log('✅ 项目验证通过');
        process.exit(0);
    } else {
        console.log('❌ 项目验证失败，请查看错误报告');
        process.exit(1);
    }
}

// 主函数
function main() {
    const args = process.argv.slice(2);
    const command = args[0] || 'detect';
    
    switch (command) {
        case 'detect':
            const detector = new ErrorDetector();
            detector.runErrorDetection();
            break;
        case 'fix':
            const fixDetector = new ErrorDetector();
            fixDetector.runErrorDetection();
            break;
        case 'verify':
            verifyProject();
            break;
        case 'monitor-only':
            monitorErrors();
            break;
        case 'fix-all':
            fixAllErrors();
            break;
        default:
            console.log('未知命令，请使用: detect, fix, verify, monitor-only, fix-all');
            process.exit(1);
    }
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = ErrorDetector;
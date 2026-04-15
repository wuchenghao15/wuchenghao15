#!/usr/bin/env node
// -*- coding: utf-8 -*-
/**
 * 错误检测工具
 * 自动检测JS CSS等文件的语法错误、逻辑错误和各种异常
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
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'error_detector.log');
        this.errorLogFile = path.join(this.logDir, 'error.log');
        
        // 错误统计
        this.errors = {
            js: [],
            css: [],
            html: [],
            other: []
        };
        
        // 确保必要目录存在
        this.ensureDirExists(this.logDir);
    }
    
    /**
     * 确保目录存在
     */
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            this.log(`目录创建: ${dirPath}`);
        }
    }
    
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
        }
    }
    
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
        }
    }
    
    /**
     * 收集错误信息
     */
    collectError(type, filePath, errorMessage) {
        this.errors[type].push({
            filePath,
            errorMessage,
            timestamp: new Date().toISOString()
        });
    }
    
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
                    }
                }
            } catch (error) {
                this.errorLog(`遍历目录失败 ${dir}: ${error.message}`);
            }
        }
        
        if (fs.existsSync(dir)) {
            traverse.call(this, dir);
        }
        
        return results;
    }
    
    /**
     * 检测JavaScript语法错误
     */
    detectJSErrors() {
        try {
            this.log("开始检测JavaScript文件错误...");
            
            const jsFiles = this.findFilesByExtension(this.jsDir, '.js');
            const htmlJSFiles = this.findFilesByExtension(this.htmlDir, '.js');
            const allJSFiles = [...jsFiles, ...htmlJSFiles];
            
            for (const jsFile of allJSFiles) {
                try {
                    const content = fs.readFileSync(jsFile, 'utf8');
                    // 使用eval检查语法错误（简单方法）
                    // 在实际生产环境中，建议使用更复杂的解析器如esprima
                    new Function(content);
                } catch (error) {
                    this.collectError('js', jsFile, error.message);
                    this.errorLog(`JavaScript文件错误 ${jsFile}: ${error.message}`);
                }
            }
            
            this.log(`JavaScript文件检查完成，共检查 ${allJSFiles.length} 个文件`);
        } catch (error) {
            this.errorLog(`检测JavaScript错误失败: ${error.message}`);
        }
    }
    
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
                    }
                } catch (error) {
                    this.collectError('css', cssFile, error.message);
                    this.errorLog(`CSS文件错误 ${cssFile}: ${error.message}`);
                }
            }
            
            this.log(`CSS文件检查完成，共检查 ${cssFiles.length} 个文件`);
        } catch (error) {
            this.errorLog(`检测CSS错误失败: ${error.message}`);
        }
    }
    
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
                    }
                } catch (error) {
                    this.collectError('html', htmlFile, error.message);
                    this.errorLog(`HTML文件错误 ${htmlFile}: ${error.message}`);
                }
            }
            
            this.log(`HTML文件检查完成，共检查 ${htmlFiles.length} 个文件`);
        } catch (error) {
            this.errorLog(`检测HTML错误失败: ${error.message}`);
        }
    }
    
    /**
     * 检查文件归类情况
     */
    checkFileOrganization() {
        try {
            this.log("开始检查文件归类情况...");
            
            const rootFiles = fs.readdirSync(this.projectRoot);
            const expectedDirs = {
                'js': 'JavaScript',
                'css': 'CSS',
                'html': 'HTML',
                'backup': 'Backups',
                'old': 'Backups',
                'bak': 'Backups',
                'txt': 'Documentation/Text',
                'py': 'SourceCode/Python',
                'sh': 'Scripts'
            };
            
            let misclassifiedFiles = [];
            
            for (const file of rootFiles) {
                const filePath = path.join(this.projectRoot, file);
                
                // 跳过目录
                if (fs.statSync(filePath).isDirectory()) {
                    continue;
                }
                
                // 检查文件扩展名
                const ext = path.extname(file).toLowerCase().substring(1);
                
                if (expectedDirs[ext]) {
                    misclassifiedFiles.push({
                        file,
                        expectedDir: expectedDirs[ext]
                    });
                }
            }
            
            if (misclassifiedFiles.length > 0) {
                this.log(`发现 ${misclassifiedFiles.length} 个文件需要归类:`);
                misclassifiedFiles.forEach(item => {
                    this.log(`- ${item.file} 应该移至 ${item.expectedDir} 目录`);
                });
            } else {
                this.log("所有文件归类正确");
            }
        } catch (error) {
            this.errorLog(`检查文件归类失败: ${error.message}`);
        }
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
            reportContent.push("===============================================");
            
            fs.writeFileSync(reportPath, reportContent.join('\n'));
            this.log(`错误报告已生成: ${reportPath}`);
            
            return totalErrors;
        } catch (error) {
            this.errorLog(`生成错误报告失败: ${error.message}`);
            return -1;
        }
    }
    
    /**
     * 运行错误检测
     */
    runErrorDetection() {
        this.log("=====================================");
        this.log("      错误检测工具启动      ");
        this.log("=====================================");
        
        // 重置错误统计
        this.errors = {
            js: [],
            css: [],
            html: [],
            other: []
        };
        
        // 执行各项检测任务
        this.detectJSErrors();
        this.detectCSSErrors();
        this.detectHTMLErrors();
        this.checkFileOrganization();
        
        // 生成错误报告
        const totalErrors = this.generateErrorReport();
        
        if (totalErrors === 0) {
            this.log("✅ 所有检测通过，未发现错误");
        } else if (totalErrors > 0) {
            this.log(`❌ 检测完成，发现 ${totalErrors} 个错误，请查看错误报告`);
        }
        
        this.log("=====================================");
        this.log("      错误检测完成      ");
        this.log("=====================================");
        
        return totalErrors === 0;
    }
}

// 主函数
function main() {
    const detector = new ErrorDetector();
    const success = detector.runErrorDetection();
    
    // 设置定时检测（每天检测一次）
    setInterval(() => {
        detector.runErrorDetection();
    }, 24 * 60 * 60 * 1000);
    
    // 根据检测结果设置退出码
    process.exit(success ? 0 : 1);
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = ErrorDetector;
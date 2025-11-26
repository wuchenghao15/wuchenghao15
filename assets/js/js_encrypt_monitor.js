#!/usr/bin/env node
// VERSION: 20251106.7da669c8aa73665c820c07
// -*- coding: utf-8 -*-
/**
 * JavaScript自动加密监控器
 * 监控JavaScript文件夹变化，自动加密并备份新文件
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');

class JSEncryptMonitor {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 目录路径
        this.jsDir = path.join(this.projectRoot, 'JavaScript');
        this.encryptedDir = path.join(this.projectRoot, 'Encrypted_JS');
        this.htmlDir = path.join(this.projectRoot, 'HTML');
        this.logDir = path.join(this.projectRoot, 'Logs');
        this.backupDir = path.join(this.projectRoot, 'Backups');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'js_encrypt_monitor.log');
        this.errorLogFile = path.join(this.logDir, 'error.log');
        
        // 记录已加密的文件
        this.encryptedFiles = new Set();
        
        // 确保必要目录存在
        this.ensureDirExists(this.logDir);
        this.ensureDirExists(this.encryptedDir);
        this.ensureDirExists(this.backupDir);
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
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`[js_encrypt_monitor.js] 写入日志失败: ${error.message}`);
        };

    };

    
    /**
     * 错误日志函数
     */
    errorLog(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(`[js_encrypt_monitor.js] ${logMessage}`);
        
        try {
            fs.appendFileSync(this.errorLogFile, logMessage + '/n');
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`[js_encrypt_monitor.js] 写入错误日志失败: ${error.message}`);
        };

    };

    
    /**
     * 获取相对路径
     */
    getRelativePath(target, base) {
        return path.relative(base, target);
    };

    
    /**
     * 加密单个JS文件
     */
    encryptJSFile(jsFilePath) {
        try {
            const jsContent = fs.readFileSync(jsFilePath, 'utf8');
            const encodedContent = Buffer.from(jsContent).toString('base64');
            
            // 生成加密文件路径
            const relPath = path.relative(this.jsDir, jsFilePath);
            const encryptedFileName = `encrypted_${relPath.replace(/\//g, '_')}`;
            const encryptedFilePath = path.join(this.encryptedDir, encryptedFileName);
            
            // 创建自解码的加密JS文件
            const encryptedContent = `// 加密的JavaScript文件
// 原始文件: ${path.basename(jsFilePath)};

// 加密时间: ${new Date().toISOString().replace('T', ' ').substring(0, 19)};


(function() {
    var encoded = '${encodedContent}';
    var decoded = atob(encoded);
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.text = decoded;
    document.head.appendChild(script);
})();`;
            
            fs.writeFileSync(encryptedFilePath, encryptedContent);
            this.log(`加密成功: ${jsFilePath} -> ${encryptedFilePath}`);
            
            return encryptedFilePath;
        } catch (error) {
            this.errorLog(`加密文件失败 ${jsFilePath}: ${error.message}`);
            return null;
        };

    };

    
    /**
     * 更新HTML文件中的JS引用
     */
    updateHTMLReferences(jsFilePath, encryptedFilePath) {
        try {
            // 查找所有HTML文件
            const htmlFiles = this.findFilesByExtension(this.htmlDir, '.html');
            
            for (const htmlFile of htmlFiles) {
                let content = fs.readFileSync(htmlFile, 'utf8');
                const jsFileName = path.basename(jsFilePath);
                
                // 检查HTML文件是否引用了该JS文件
                if (content.includes(jsFileName)) {
                    // 计算相对路径
                    const htmlDir = path.dirname(htmlFile);
                    const relativeJSPath = this.getRelativePath(jsFilePath, htmlDir);
                    const relativeEncryptedPath = this.getRelativePath(encryptedFilePath, htmlDir);
                    
                    // 备份HTML文件
                    const backupPath = htmlFile + '.backup';
                    if (!fs.existsSync(backupPath)) {
                        fs.copyFileSync(htmlFile, backupPath);
                    };

                    
                    // 替换JS引用
                    const regex = new RegExp(`src=["'][^"']*${jsFileName}[^"']*["']`, 'g');
                    const updatedContent = content.replace(regex, `src="${relativeEncryptedPath}"`);
                    
                    if (updatedContent !== content) {
                        fs.writeFileSync(htmlFile, updatedContent);
                        this.log(`已更新HTML引用: ${htmlFile} 中的 ${relativeJSPath} -> ${relativeEncryptedPath}`);
                    };

                };

            };

        } catch (error) {
            this.errorLog(`更新HTML引用失败: ${error.message}`);
        };

    };

    
    /**
     * 查找指定扩展名的文件
     */
    findFilesByExtension(dir, extension) {
        let results = [];
        
        function traverse(dir) {
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

        };

        
        traverse(dir);
        return results;
    };

    
    /**
     * 初始化已加密文件列表
     */
    initializeEncryptedFiles() {
        const encryptedFiles = this.findFilesByExtension(this.encryptedDir, '.js');
        
        for (const file of encryptedFiles) {
            const originalFileName = path.basename(file).replace('encrypted_', '').replace(/_/g, '/');
            const originalFilePath = path.join(this.jsDir, originalFileName);
            this.encryptedFiles.add(originalFilePath);
        };

        
        this.log(`已初始化 ${this.encryptedFiles.size} 个已加密文件`);
    };

    
    /**
     * 检查并加密新的JS文件
     */
    checkAndEncryptNewFiles() {
        try {
            const jsFiles = this.findFilesByExtension(this.jsDir, '.js');
            
            for (const jsFile of jsFiles) {
                // 跳过监控脚本自身和其他不需要加密的文件
                if (jsFile.includes('js_encrypt_monitor.js')) continue;
                
                if (!this.encryptedFiles.has(jsFile)) {
                    this.log(`检测到新文件: ${jsFile}`);
                    const encryptedFilePath = this.encryptJSFile(jsFile);
                    
                    if (encryptedFilePath) {
                        this.updateHTMLReferences(jsFile, encryptedFilePath);
                        this.encryptedFiles.add(jsFile);
                    };

                };

            };

        } catch (error) {
            this.errorLog(`检查新文件失败: ${error.message}`);
        };

    };

    
    /**
     * 启动监控
     */
    startMonitoring() {
        this.log("=====================================");
        this.log("      JavaScript加密监控器启动      ");
        this.log("=====================================");
        
        // 初始化已加密文件列表
        this.initializeEncryptedFiles();
        
        // 立即检查一次
        this.checkAndEncryptNewFiles();
        
        // 设置定时检查
        this.log("开始定时监控JavaScript文件变化...");
        setInterval(() => {
            this.checkAndEncryptNewFiles();
        }, 60000); // 每分钟检查一次
        
        // 处理退出信号
        process.on('SIGINT', () => {
            this.log("收到终止信号，正在停止监控...");
            process.exit(0);
        });
    };

};


// 主函数
function main() {
    const monitor = new JSEncryptMonitor();
    monitor.startMonitoring();
};


// 执行主函数
if (require.main === module) {
    main();
};


module.exports = JSEncryptMonitor;
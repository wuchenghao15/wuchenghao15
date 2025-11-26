#!/usr/bin/env node
// VERSION: 20251106.946ab978f1e3e334e87e144
// -*- coding: utf-8 -*-
/**
 * JS文件自动加密脚本
 * 监控JS文件夹，自动加密新增或修改的JS文件，并备份到指定目录
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

class JSEncryptor {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // JS源目录和加密目录
        this.jsSourceDir = path.join(this.projectRoot, 'JavaScript');
        this.htmlJsSourceDir = path.join(this.projectRoot, 'HTML/JS');
        this.encryptedJsDir = path.join(this.projectRoot, 'Encrypted_JS');
        
        // 日志目录
        this.logDir = path.join(this.projectRoot, 'Logs');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'js_encryptor.log');
        this.errorLogFile = path.join(this.logDir, 'error.log');
        
        // 加密密钥（实际应用中应使用更安全的密钥管理方式）
        this.encryptionKey = crypto.createHash('sha256').update('MTSCOS_SECRET_KEY_2025').digest('base64').substring(0, 32);
        this.iv = crypto.randomBytes(16);
        
        // 已加密文件记录
        this.encryptedFiles = new Set();
        
        // 监控间隔（毫秒）
        this.monitorInterval = 30000; // 30秒
        
        // 确保必要目录存在
        this.ensureDirExists(this.encryptedJsDir);
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
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`[js_encryptor.js] `写入日志失败: ${error.message}``);
        }
    }
    
    /**
     * 错误日志函数
     */
    errorLog(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(`[js_encryptor.js] logMessage`);
        
        try {
            fs.appendFileSync(this.errorLogFile, logMessage + '/n');
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`[js_encryptor.js] `写入错误日志失败: ${error.message}``);
        }
    }
    
    /**
     * 加密文件内容
     */
    encrypt(content) {
        try {
            // 创建加密器
            const cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(this.encryptionKey), this.iv);
            
            // 加密内容
            let encrypted = cipher.update(content, 'utf8', 'base64');
            encrypted += cipher.final('base64');
            
            // 返回IV和加密内容
            return {
                iv: this.iv.toString('base64'),
                encryptedData: encrypted
            };
        } catch (error) {
            this.errorLog(`加密失败: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 解密文件内容
     */
    decrypt(encryptedData, iv) {
        try {
            // 创建解密器
            const decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(this.encryptionKey), Buffer.from(iv, 'base64'));
            
            // 解密内容
            let decrypted = decipher.update(encryptedData, 'base64', 'utf8');
            decrypted += decipher.final('utf8');
            
            return decrypted;
        } catch (error) {
            this.errorLog(`解密失败: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 加密单个JS文件
     */
    encryptJSFile(filePath) {
        try {
            // 读取文件内容
            const content = fs.readFileSync(filePath, 'utf8');
            
            // 加密内容
            const encrypted = this.encrypt(content);
            
            // 生成加密后的文件名
            const relativePath = path.relative(this.projectRoot, filePath);
            const encryptedFileName = relativePath.replace(/\//g, '_') + '.encrypted';
            const encryptedFilePath = path.join(this.encryptedJsDir, encryptedFileName);
            
            // 创建解密包装器代码
            const wrapperCode = `
// 加密JS包装器
(function() {
    const encryptedData = '${encrypted.encryptedData}';
    const iv = '${encrypted.iv}';
    
    // 解密函数
    function decrypt(data, iv) {
        try {
            // 实际应用中，解密函数应该更安全，这里仅作为演示
            const key = CryptoJS.SHA256('MTSCOS_SECRET_KEY_2025').toString().substring(0, 32);
            const decrypted = CryptoJS.AES.decrypt(
                { ciphertext: CryptoJS.enc.Base64.parse(data) },
                CryptoJS.enc.Utf8.parse(key),
                { iv: CryptoJS.enc.Base64.parse(iv) }
            );
            return decrypted.toString(CryptoJS.enc.Utf8);
        } catch (e) {
            console.error(`[js_encryptor.js] 解密失败:, e`);
            return '';
        }
    }
    
    // 解密并执行代码
    try {
        const decryptedCode = decrypt(encryptedData, iv);
        if (decryptedCode) {
            // 使用Function构造器执行代码，避免直接eval
            (new Function(decryptedCode))();
        }
    } catch (e) {
        console.error(`[js_encryptor.js] 执行解密代码失败:, e`);
    }
})();
`;
            
            // 保存加密文件
            fs.writeFileSync(encryptedFilePath, JSON.stringify(encrypted), 'utf8');
            
            // 保存解密包装器（用于HTML引用）
            const wrapperFilePath = path.join(this.encryptedJsDir, path.basename(filePath));
            fs.writeFileSync(wrapperFilePath, wrapperCode, 'utf8');
            
            this.log(`已加密文件: ${filePath} -> ${encryptedFilePath}`);
            this.log(`已创建解密包装器: ${wrapperFilePath}`);
            
            // 记录已加密文件
            this.encryptedFiles.add(filePath);
            
            return encryptedFilePath;
        } catch (error) {
            this.errorLog(`加密文件失败 ${filePath}: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 扫描并加密所有JS文件
     */
    scanAndEncryptAllJSFiles() {
        this.log("开始扫描并加密所有JS文件...");
        
        const jsDirs = [this.jsSourceDir, this.htmlJsSourceDir];
        let encryptedCount = 0;
        let totalCount = 0;
        
        jsDirs.forEach(dir => {
            if (fs.existsSync(dir)) {
                try {
                    const files = fs.readdirSync(dir);
                    
                    files.forEach(file => {
                        if (path.extname(file) === '.js') {
                            const filePath = path.join(dir, file);
                            if (fs.statSync(filePath).isFile()) {
                                totalCount++;
                                
                                // 检查是否已加密
                                if (!this.encryptedFiles.has(filePath)) {
                                    if (this.encryptJSFile(filePath)) {
                                        encryptedCount++;
                                    }
                                }
                            }
                        }
                    });
                } catch (error) {
                    this.errorLog(`扫描目录失败 ${dir}: ${error.message}`);
                }
            }
        });
        
        this.log(`JS文件加密完成: 共${totalCount}个文件，已加密${encryptedCount}个文件`);
    }
    
    /**
     * 监控JS文件夹变化
     */
    monitorJSDirectories() {
        this.log("开始监控JS文件夹变化...");
        
        const jsDirs = [this.jsSourceDir, this.htmlJsSourceDir];
        const watchers = [];
        
        jsDirs.forEach(dir => {
            if (fs.existsSync(dir)) {
                try {
                    const watcher = fs.watch(dir, (eventType, filename) => {
                        if (eventType === 'change' || eventType === 'rename') {
                            if (filename && path.extname(filename) === '.js') {
                                const filePath = path.join(dir, filename);
                                
                                // 检查文件是否存在（rename事件可能是删除）
                                if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
                                    this.log(`检测到JS文件变化: ${filePath}`);
                                    this.encryptJSFile(filePath);
                                    
                                    // 更新HTML中的引用
                                    this.updateHTMLReferences(filePath);
                                }
                            }
                        }
                    });
                    
                    watchers.push(watcher);
                    this.log(`已监控目录: ${dir}`);
                } catch (error) {
                    this.errorLog(`监控目录失败 ${dir}: ${error.message}`);
                }
            }
        });
        
        // 处理进程退出
        process.on('SIGINT', () => {
            watchers.forEach(watcher => watcher.close().catch(error => console.error(`[js_encryptor.js] watcher.close failed:`, error)));
            this.log("已停止监控JS文件夹");
            process.exit(0);
        });
    }
    
    /**
     * 更新HTML文件中的JS引用为加密版本
     */
    updateHTMLReferences(jsFilePath) {
        try {
            const htmlDir = path.join(this.projectRoot, 'HTML');
            
            if (!fs.existsSync(htmlDir)) return;
            
            // 查找所有HTML文件
            const htmlFiles = [];
            
            function findHTMLFiles(dir) {
                const files = fs.readdirSync(dir);
                files.forEach(file => {
                    const filePath = path.join(dir, file);
                    if (fs.statSync(filePath).isDirectory()) {
                        findHTMLFiles(filePath);
                    } else if (path.extname(file) === '.html') {
                        htmlFiles.push(filePath);
                    }
                });
            }
            
            findHTMLFiles(htmlDir);
            
            // 更新每个HTML文件中的引用
            htmlFiles.forEach(htmlFile => {
                try {
                    let content = fs.readFileSync(htmlFile, 'utf8');
                    const jsFileName = path.basename(jsFilePath);
                    const encryptedJsPath = path.join('Encrypted_JS', jsFileName).replace(/\//g, '/');
                    
                    // 查找并替换JS引用
                    const regex = new RegExp(`src=["']([^"']*${jsFileName})["']`, 'g');
                    const newContent = content.replace(regex, `src="${encryptedJsPath}"`);
                    
                    if (newContent !== content) {
                        fs.writeFileSync(htmlFile, newContent, 'utf8');
                        this.log(`已更新HTML文件中的JS引用: ${htmlFile}`);
                    }
                } catch (error) {
                    this.errorLog(`更新HTML文件失败 ${htmlFile}: ${error.message}`);
                }
            });
        } catch (error) {
            this.errorLog(`更新HTML引用失败: ${error.message}`);
        }
    }
    
    /**
     * 生成CryptoJS包含脚本
     */
    generateCryptoJSInclude() {
        const cryptoJsScript = `
<!-- CryptoJS库，用于JS解密 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js"></script>
`;
        
        // 更新所有HTML文件，添加CryptoJS引用
        const htmlDir = path.join(this.projectRoot, 'HTML');
        
        if (fs.existsSync(htmlDir)) {
            function processHTMLFiles(dir) {
                const files = fs.readdirSync(dir);
                files.forEach(file => {
                    const filePath = path.join(dir, file);
                    if (fs.statSync(filePath).isDirectory()) {
                        processHTMLFiles(filePath);
                    } else if (path.extname(file) === '.html') {
                        try {
                            let content = fs.readFileSync(filePath, 'utf8');
                            
                            // 检查是否已经包含CryptoJS
                            if (!content.includes('crypto-js.min.js')) {
                                // 在head标签结束前插入CryptoJS引用
                                content = content.replace('</head>', `${cryptoJsScript}</head>`);
                                fs.writeFileSync(filePath, content, 'utf8');
                            }
                        } catch (error) {
                            console.error(`[js_encryptor.js] `更新HTML文件失败 ${filePath}: ${error.message}``);
                        }
                    }
                });
            }
            
            processHTMLFiles(htmlDir);
        }
    }
    
    /**
     * 启动加密器
     */
    start() {
        this.log("=====================================");
        this.log("      JS文件自动加密器启动      ");
        this.log("=====================================");
        
        // 初始化已加密文件列表
        this.loadEncryptedFilesList().catch(error => console.error(`[js_encryptor.js] this.loadEncryptedFilesList failed:`, error));
        
        // 生成CryptoJS包含脚本
        this.generateCryptoJSInclude().catch(error => console.error(`[js_encryptor.js] this.generateCryptoJSInclude failed:`, error));
        
        // 扫描并加密所有JS文件
        this.scanAndEncryptAllJSFiles().catch(error => console.error(`[js_encryptor.js] this.scanAndEncryptAllJSFiles failed:`, error));
        
        // 启动监控
        this.monitorJSDirectories().catch(error => console.error(`[js_encryptor.js] this.monitorJSDirectories failed:`, error));
        
        this.log("JS文件自动加密器已启动，持续监控和加密JS文件");
    }
    
    /**
     * 加载已加密文件列表
     */
    loadEncryptedFilesList() {
        // 在实际应用中，这里可以从文件或数据库加载已加密文件列表
        // 简化实现，每次启动时重新扫描
        this.encryptedFiles.clear().catch(error => console.error(`[js_encryptor.js] encryptedFiles.clear failed:`, error));
    }
}

// 主函数
function main() {
    const jsEncryptor = new JSEncryptor();
    jsEncryptor.start().catch(error => console.error(`[js_encryptor.js] jsEncryptor.start failed:`, error));
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = JSEncryptor;
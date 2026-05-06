#!/usr/bin/env node
// -*- coding: utf-8 -*-
"""
MTSCOS 脚本验证器
负责验证项目核心脚本文件的完整性和正确性
"""

const fs = require('fs');
const path = require('path');

class MTSCOS_VerifyManager {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 目录路径
        this.jsDir = path.join(this.projectRoot, 'JavaScript');
        this.htmlDir = path.join(this.projectRoot, 'HTML');
        this.cssDir = path.join(this.projectRoot, 'CSS');
        this.logDir = path.join(this.projectRoot, 'Logs');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'verify_scripts.log');
        
        // 确保日志目录存在
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
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`写入错误日志失败: ${error.message}`);
        }
    }
    
    /**
     * 检查文件是否存在
     */
    checkFile(filePath) {
        if (fs.existsSync(filePath)) {
            this.log(`✅ 文件存在: ${path.relative(this.projectRoot, filePath)}`);
            return true;
        } else {
            this.errorLog(`❌ 文件不存在: ${path.relative(this.projectRoot, filePath)}`);
            return false;
        }
    }
    
    /**
     * 检查目录是否存在
     */
    checkDir(dirPath) {
        if (fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory()) {
            this.log(`✅ 目录存在: ${path.relative(this.projectRoot, dirPath)}`);
            return true;
        } else {
            this.errorLog(`❌ 目录不存在: ${path.relative(this.projectRoot, dirPath)}`);
            return false;
        }
    }
    
    /**
     * 验证JavaScript文件
     */
    verifyJsFiles() {
        this.log("验证JavaScript文件...");
        
        const requiredJsFiles = [
            path.join(this.jsDir, 'startup-manager.js'),
            path.join(this.jsDir, 'version-manager.js'),
            path.join(this.jsDir, 'verify-scripts.js'),
            path.join(this.jsDir, 'anti_hotlink.js'),
            path.join(this.jsDir, 'index-script.js')
        ];
        
        let missingCount = 0;
        
        for (const file of requiredJsFiles) {
            if (!this.checkFile(file)) {
                missingCount++;
            } else {
                // 尝试验证JavaScript语法
                try {
                    const content = fs.readFileSync(file, 'utf-8');
                    // 简单的语法检查 - 尝试解析文件内容
                    new Function(`'use strict'; ${content}`);
                    this.log(`✅ JavaScript语法验证通过: ${path.relative(this.projectRoot, file)}`);
                } catch (error) {
                    this.errorLog(`❌ JavaScript语法验证失败: ${path.relative(this.projectRoot, file)} - ${error.message}`);
                    missingCount++;
                }
            }
        }
        
        return missingCount;
    }
    
    /**
     * 验证HTML文件
     */
    verifyHtmlFiles() {
        this.log("验证HTML文件...");
        
        const requiredHtmlFiles = [
            path.join(this.htmlDir, 'index.html'),
            path.join(this.htmlDir, '404.html'),
            path.join(this.htmlDir, 'UpdateInfo.html')
        ];
        
        let missingCount = 0;
        
        for (const file of requiredHtmlFiles) {
            if (!this.checkFile(file)) {
                missingCount++;
            } else {
                // 简单验证HTML标签闭合
                const content = fs.readFileSync(file, 'utf-8').toLowerCase();
                if (content.includes('<!doctype html>') && content.includes('<html') && content.includes('</html>')) {
                    this.log(`✅ HTML基础结构验证通过: ${path.relative(this.projectRoot, file)}`);
                } else {
                    this.errorLog(`⚠️ HTML可能缺少必要标签: ${path.relative(this.projectRoot, file)}`);
                }
            }
        }
        
        return missingCount;
    }
    
    /**
     * 验证配置文件
     */
    verifyConfigFiles() {
        this.log("验证配置文件...");
        
        const requiredConfigFiles = [
            path.join(this.projectRoot, 'VERSION'),
            path.join(this.projectRoot, 'README.md')
        ];
        
        let missingCount = 0;
        
        for (const file of requiredConfigFiles) {
            if (!this.checkFile(file)) {
                missingCount++;
            }
        }
        
        return missingCount;
    }
    
    /**
     * 验证版本格式
     */
    verifyVersionFormat() {
        const versionFile = path.join(this.projectRoot, 'VERSION');
        if (this.checkFile(versionFile)) {
            try {
                const version = fs.readFileSync(versionFile, 'utf-8').trim();
                const versionRegex = /^\d+\.\d+\.\d+$/;
                
                if (versionRegex.test(version)) {
                    this.log(`✅ 版本格式验证通过: ${version}`);
                    return true;
                } else {
                    this.errorLog(`❌ 版本格式错误: ${version} (应为 X.Y.Z 格式)`);
                    return false;
                }
            } catch (error) {
                this.errorLog(`❌ 读取版本文件失败: ${error.message}`);
                return false;
            }
        }
        return false;
    }
    
    /**
     * 执行完整验证
     */
    executeVerification() {
        this.log("=====================================");
        this.log("       MTSCOS 脚本验证器       ");
        this.log("=====================================");
        
        let totalMissing = 0;
        
        // 验证目录结构
        this.log("\n验证目录结构...");
        this.checkDir(this.jsDir);
        this.checkDir(this.htmlDir);
        this.checkDir(this.cssDir);
        this.checkDir(this.logDir);
        
        // 验证各个文件类型
        this.log("\n验证核心文件...");
        totalMissing += this.verifyJsFiles();
        totalMissing += this.verifyHtmlFiles();
        totalMissing += this.verifyConfigFiles();
        
        // 验证版本格式
        this.log("\n验证版本信息...");
        this.verifyVersionFormat();
        
        // 生成验证报告
        this.log("\n=====================================");
        if (totalMissing === 0) {
            this.log("✅ 所有验证通过！");
        } else {
            this.errorLog(`❌ 验证失败，发现 ${totalMissing} 个问题`);
        }
        this.log("=====================================");
        
        return totalMissing === 0 ? 0 : 1;
    }
}

// 命令行处理
function main() {
    const verifyManager = new MTSCOS_VerifyManager();
    
    // 执行验证
    const exitCode = verifyManager.executeVerification();
    process.exit(exitCode);
}

// 执行主函数
if (require.main === module) {
    main();
}

// 导出类供其他模块使用
module.exports = MTSCOS_VerifyManager;
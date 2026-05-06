#!/usr/bin/env node
// -*- coding: utf-8 -*-
"""
MTSCOS 实现验证脚本
用于验证项目文件结构和功能完整性
"""

const fs = require('fs');
const path = require('path');

class MTSCOS_Verifier {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 文件路径定义
        this.jsDir = path.join(this.projectRoot, 'JavaScript');
        this.htmlDir = path.join(this.projectRoot, 'HTML');
        this.logsDir = path.join(this.projectRoot, 'Logs');
        this.startAllPath = path.join(this.projectRoot, 'start_all.sh');
        this.startupManagerPath = path.join(this.jsDir, 'startup-manager.js');
        this.versionFile = path.join(this.projectRoot, 'VERSION');
        
        // 验证结果
        this.success = 0;
        this.failed = 0;
    }
    
    /**
     * 日志函数
     */
    log(message, isError = false) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const prefix = isError ? '[ERROR]' : '[INFO]';
        console.log(`[${timestamp}] ${prefix} ${message}`);
    }
    
    /**
     * 检查文件是否存在
     */
    checkFile(filePath, description) {
        if (fs.existsSync(filePath)) {
            this.log(`✅ ${description}: ${path.basename(filePath)}`);
            this.success++;
            return true;
        } else {
            this.log(`❌ ${description}缺失: ${filePath}`, true);
            this.failed++;
            return false;
        }
    }
    
    /**
     * 检查目录是否存在
     */
    checkDir(dirPath, description) {
        if (fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory()) {
            this.log(`✅ ${description}: ${path.basename(dirPath)}`);
            this.success++;
            return true;
        } else {
            this.log(`❌ ${description}缺失: ${dirPath}`, true);
            this.failed++;
            return false;
        }
    }
    
    /**
     * 检查文件内容
     */
    checkFileContent(filePath, searchPattern, description) {
        try {
            if (!fs.existsSync(filePath)) {
                return false;
            }
            
            const content = fs.readFileSync(filePath, 'utf-8');
            if (content.includes(searchPattern)) {
                this.log(`✅ ${description}验证通过: ${path.basename(filePath)}`);
                this.success++;
                return true;
            } else {
                this.log(`❌ ${description}验证失败: ${path.basename(filePath)}`, true);
                this.failed++;
                return false;
            }
        } catch (error) {
            this.log(`❌ 读取文件失败: ${error.message}`, true);
            this.failed++;
            return false;
        }
    }
    
    /**
     * 验证文件结构
     */
    verifyFileStructure() {
        this.log("\n===== 开始验证文件结构 =====");
        
        // 检查核心目录
        this.checkDir(this.jsDir, "JavaScript目录");
        this.checkDir(this.htmlDir, "HTML目录");
        this.checkDir(this.logsDir, "Logs目录");
        
        // 检查核心文件
        this.checkFile(this.startAllPath, "启动脚本");
        this.checkFile(this.startupManagerPath, "启动管理器");
        this.checkFile(this.versionFile, "版本文件");
        
        // 检查其他必要文件
        this.checkFile(path.join(this.jsDir, "anti_hotlink.js"), "防盗链脚本");
        this.checkFile(path.join(this.jsDir, "index-script.js"), "索引脚本");
        this.checkFile(path.join(this.htmlDir, "UpdateInfo.html"), "更新信息页");
        
        this.log("===== 文件结构验证完成 =====\n");
    }
    
    /**
     * 验证启动管理器功能
     */
    verifyStartupManager() {
        this.log("\n===== 开始验证启动管理器功能 =====");
        
        if (!fs.existsSync(this.startupManagerPath)) {
            this.log("❌ 启动管理器文件不存在，跳过功能验证", true);
            return;
        }
        
        // 检查关键功能
        this.checkFileContent(this.startupManagerPath, "MTSCOS_StartManager", "启动管理器类");
        this.checkFileContent(this.startupManagerPath, "updateVersion", "版本更新功能");
        this.checkFileContent(this.startupManagerPath, "generateUpdateInfo", "更新说明生成功能");
        this.checkFileContent(this.startupManagerPath, "incrementBuildCounter", "内部版本号功能");
        this.checkFileContent(this.startupManagerPath, "startHttpServer", "HTTP服务器启动功能");
        this.checkFileContent(this.startupManagerPath, "verifyScripts", "脚本验证功能");
        
        this.log("===== 启动管理器功能验证完成 =====\n");
    }
    
    /**
     * 验证start_all.sh轻量级实现
     */
    verifyStartAll() {
        this.log("\n===== 开始验证start_all.sh轻量级实现 =====");
        
        if (!fs.existsSync(this.startAllPath)) {
            this.log("❌ start_all.sh文件不存在，跳过验证", true);
            return;
        }
        
        // 检查文件大小是否合理（轻量级）
        const stats = fs.statSync(this.startAllPath);
        const fileSizeInKB = stats.size / 1024;
        
        if (fileSizeInKB < 5) {
            this.log(`✅ start_all.sh文件大小合理: ${fileSizeInKB.toFixed(2)} KB`);
            this.success++;
        } else {
            this.log(`⚠️ start_all.sh文件可能过大: ${fileSizeInKB.toFixed(2)} KB`, true);
            this.failed++;
        }
        
        // 检查是否调用JavaScript启动器
        this.checkFileContent(this.startAllPath, "startup-manager.js", "调用JavaScript启动器");
        
        this.log("===== start_all.sh验证完成 =====\n");
    }
    
    /**
     * 生成验证报告
     */
    generateReport() {
        const total = this.success + this.failed;
        const passRate = total > 0 ? (this.success / total * 100).toFixed(2) : 0;
        
        this.log("\n=====================================");
        this.log(`          验证报告          `);
        this.log("=====================================");
        this.log(`✅ 通过: ${this.success}`);
        this.log(`❌ 失败: ${this.failed}`);
        this.log(`📊 通过率: ${passRate}%`);
        
        if (this.failed === 0) {
            this.log("🎉 所有验证项通过！");
        } else {
            this.log("⚠️ 部分验证项失败，请检查修复！", true);
        }
        
        this.log("=====================================\n");
        
        return this.failed === 0;
    }
    
    /**
     * 运行完整验证
     */
    run() {
        this.log("\n=====================================");
        this.log("       MTSCOS 实现验证       ");
        this.log("=====================================");
        
        this.verifyFileStructure();
        this.verifyStartupManager();
        this.verifyStartAll();
        
        return this.generateReport();
    }
}

// 执行验证
const verifier = new MTSCOS_Verifier();
const result = verifier.run();

// 设置退出码
process.exit(result ? 0 : 1);
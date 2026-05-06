#!/usr/bin/env node
// -*- coding: utf-8 -*-
"""
MTSCOS 版本管理器
负责项目版本管理、内部版本号递增和更新说明文档生成
"""

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class MTSCOS_VersionManager {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 版本管理相关文件路径
        this.versionFile = path.join(this.projectRoot, 'VERSION');
        this.buildCounterFile = path.join(this.projectRoot, 'Logs', 'build_counter.txt');
        this.previousVersionFile = path.join(this.projectRoot, 'Logs', 'previous_version.txt');
        this.updateInfoFile = path.join(this.projectRoot, 'HTML', 'UpdateInfo.html');
        this.logFile = path.join(this.projectRoot, 'Logs', 'version_manager.log');
        
        // 确保目录存在
        this.ensureDirExists(path.join(this.projectRoot, 'Logs'));
        this.ensureDirExists(path.join(this.projectRoot, 'HTML'));
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
     * 获取当前版本
     */
    getCurrentVersion() {
        try {
            if (fs.existsSync(this.versionFile)) {
                const version = fs.readFileSync(this.versionFile, 'utf-8').trim();
                return version;
            }
            this.log('版本文件不存在，使用默认版本: 1.0.0');
            return '1.0.0';
        } catch (error) {
            this.log(`获取版本失败: ${error.message}`);
            return '1.0.0';
        }
    }
    
    /**
     * 保存当前版本为上一版本
     */
    savePreviousVersion(version) {
        try {
            fs.writeFileSync(this.previousVersionFile, version, 'utf-8');
            this.log(`上一版本已保存: ${version}`);
            return true;
        } catch (error) {
            this.log(`保存上一版本失败: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 更新版本号
     * @param {string} versionType - major, minor, patch
     */
    updateVersion(versionType = 'patch') {
        try {
            // 获取当前版本
            const currentVersion = this.getCurrentVersion();
            
            // 保存旧版本
            this.savePreviousVersion(currentVersion);
            
            // 解析版本号
            const versionParts = currentVersion.split('.').map(Number);
            
            // 更新版本号
            switch (versionType) {
                case 'major':
                    versionParts[0] += 1;
                    versionParts[1] = 0;
                    versionParts[2] = 0;
                    this.log(`更新主版本号: ${currentVersion} -> ${versionParts.join('.')}`);
                    break;
                case 'minor':
                    versionParts[1] += 1;
                    versionParts[2] = 0;
                    this.log(`更新次版本号: ${currentVersion} -> ${versionParts.join('.')}`);
                    break;
                case 'patch':
                default:
                    versionParts[2] += 1;
                    this.log(`更新修订号: ${currentVersion} -> ${versionParts.join('.')}`);
                    break;
            }
            
            // 设置新版本
            const newVersion = versionParts.join('.');
            fs.writeFileSync(this.versionFile, newVersion, 'utf-8');
            this.log(`版本文件已更新: ${this.versionFile}`);
            
            return newVersion;
        } catch (error) {
            this.log(`更新版本失败: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 增加内部版本号
     */
    incrementBuildCounter() {
        try {
            let buildCounter = 0;
            
            // 读取现有计数器
            if (fs.existsSync(this.buildCounterFile)) {
                buildCounter = parseInt(fs.readFileSync(this.buildCounterFile, 'utf-8').trim()) || 0;
            }
            
            // 增加计数器
            buildCounter += 1;
            
            // 保存新计数器
            fs.writeFileSync(this.buildCounterFile, buildCounter.toString(), 'utf-8');
            this.log(`内部版本号已更新: Build ${buildCounter}`);
            
            return buildCounter;
        } catch (error) {
            this.log(`更新内部版本号失败: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 获取系统信息
     */
    getSystemInfo() {
        try {
            let osInfo = 'Unknown';
            
            // 尝试获取操作系统信息
            try {
                if (process.platform === 'win32') {
                    osInfo = execSync('ver', { encoding: 'utf-8' }).trim();
                } else {
                    osInfo = execSync('uname -a', { encoding: 'utf-8' }).trim();
                }
            } catch (e) {
                this.log('获取详细系统信息失败，使用平台信息');
                osInfo = process.platform;
            }
            
            return osInfo;
        } catch (error) {
            this.log(`获取系统信息失败: ${error.message}`);
            return 'Unknown';
        }
    }
    
    /**
     * 生成更新说明文档
     * @param {string} updateDetails - 更新说明
     */
    generateUpdateInfo(updateDetails = '') {
        try {
            // 获取版本信息
            const currentVersion = this.getCurrentVersion();
            const previousVersion = fs.existsSync(this.previousVersionFile) ? 
                fs.readFileSync(this.previousVersionFile, 'utf-8').trim() : 'Unknown';
            
            // 增加内部版本号
            const buildCounter = this.incrementBuildCounter();
            
            // 获取系统信息
            const osInfo = this.getSystemInfo();
            const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
            
            // 默认更新说明
            if (!updateDetails) {
                updateDetails = '系统自动更新，版本迭代优化';
            }
            
            // 创建HTML内容
            const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTSCOS 更新信息</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .version-info {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .version-info p {
            margin: 8px 0;
        }
        .update-details {
            background-color: #e8f4fc;
            padding: 20px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
            margin-bottom: 20px;
        }
        .system-info {
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }
        .highlight {
            color: #e74c3c;
            font-weight: bold;
        }
        .timestamp {
            font-style: italic;
            color: #95a5a6;
            text-align: right;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>MTSCOS 更新信息</h1>
        
        <div class="version-info">
            <p><strong>当前版本:</strong> <span class="highlight">v${currentVersion}</span></p>
            <p><strong>上一版本:</strong> ${previousVersion}</p>
            <p><strong>内部版本号:</strong> Build ${buildCounter}</p>
        </div>
        
        <h2>更新说明</h2>
        <div class="update-details">
            <p>${updateDetails}</p>
        </div>
        
        <h2>技术信息</h2>
        <div class="system-info">
            <p><strong>操作系统:</strong> ${osInfo}</p>
            <p><strong>更新时间:</strong> ${timestamp}</p>
        </div>
        
        <p class="timestamp">© MTSCOS 自动化系统</p>
    </div>
</body>
</html>`;
            
            // 写入文件
            fs.writeFileSync(this.updateInfoFile, htmlContent, 'utf-8');
            this.log(`更新说明文档已生成: ${this.updateInfoFile}`);
            
            return true;
        } catch (error) {
            this.log(`生成更新说明文档失败: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 执行版本更新
     * @param {string} versionType - 版本类型
     * @param {string} updateDetails - 更新说明
     */
    executeVersionUpdate(versionType = 'patch', updateDetails = '') {
        this.log("=====================================");
        this.log("       开始版本更新流程       ");
        this.log("=====================================");
        
        // 更新版本号
        const newVersion = this.updateVersion(versionType);
        if (!newVersion) {
            this.log("版本更新失败！", true);
            return 1;
        }
        
        // 生成更新说明
        const result = this.generateUpdateInfo(updateDetails);
        
        if (result) {
            this.log("\n🎉 版本更新完成！");
            this.log(`- 新版本: v${newVersion}`);
            this.log(`- 更新说明: ${this.updateInfoFile}`);
            this.log("=====================================");
            return 0;
        } else {
            this.log("更新说明文档生成失败！", true);
            return 1;
        }
    }
}

// 命令行处理
function main() {
    const versionManager = new MTSCOS_VersionManager();
    
    // 解析命令行参数
    const args = process.argv.slice(2);
    let versionType = 'patch';
    let updateDetails = '';
    
    // 处理参数
    if (args.length > 0) {
        if (['major', 'minor', 'patch'].includes(args[0])) {
            versionType = args[0];
            updateDetails = args.slice(1).join(' ');
        } else {
            updateDetails = args.join(' ');
        }
    }
    
    // 执行更新
    const exitCode = versionManager.executeVersionUpdate(versionType, updateDetails);
    process.exit(exitCode);
}

// 执行主函数
if (require.main === module) {
    main();
}

// 导出类供其他模块使用
module.exports = MTSCOS_VersionManager;
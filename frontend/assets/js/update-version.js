#!/usr/bin/env node
// -*- coding: utf-8 -*-
"""
MTSCOS 版本更新工具
用于更新项目版本、内部版本号和更新说明文档
"""

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class MTSCOS_VersionManager {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 版本文件路径
        this.versionFile = path.join(this.projectRoot, 'VERSION');
        this.buildCounterFile = path.join(this.projectRoot, 'Logs', 'build_counter.txt');
        this.previousVersionFile = path.join(this.projectRoot, 'Logs', 'previous_version.txt');
        this.updateInfoFile = path.join(this.projectRoot, 'HTML', 'UpdateInfo.html');
        
        // 确保日志目录存在
        this.ensureDirExists(path.join(this.projectRoot, 'Logs'));
        this.ensureDirExists(path.join(this.projectRoot, 'HTML'));
    }
    
    /**
     * 确保目录存在
     */
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            console.log(`目录创建: ${dirPath}`);
        }
    }
    
    /**
     * 获取当前版本
     */
    getCurrentVersion() {
        try {
            if (fs.existsSync(this.versionFile)) {
                const version = fs.readFileSync(this.versionFile, 'utf-8').trim();
                console.log(`当前版本: ${version}`);
                return version;
            }
            console.log('版本文件不存在，使用默认版本 1.0.0');
            return '1.0.0';
        } catch (error) {
            console.error(`获取当前版本失败: ${error.message}`);
            return '1.0.0';
        }
    }
    
    /**
     * 更新版本号
     * @param {string} versionType - 版本类型: major, minor, patch
     */
    updateVersion(versionType = 'patch') {
        try {
            const currentVersion = this.getCurrentVersion();
            const versionParts = currentVersion.split('.').map(Number);
            
            // 保存旧版本
            fs.writeFileSync(this.previousVersionFile, currentVersion, 'utf-8');
            
            // 更新版本号
            switch (versionType) {
                case 'major':
                    versionParts[0] += 1;
                    versionParts[1] = 0;
                    versionParts[2] = 0;
                    break;
                case 'minor':
                    versionParts[1] += 1;
                    versionParts[2] = 0;
                    break;
                case 'patch':
                default:
                    versionParts[2] += 1;
                    break;
            }
            
            const newVersion = versionParts.join('.');
            fs.writeFileSync(this.versionFile, newVersion, 'utf-8');
            console.log(`版本已更新: ${currentVersion} -> ${newVersion}`);
            
            return newVersion;
        } catch (error) {
            console.error(`更新版本失败: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 增加内部版本号
     */
    incrementBuildCounter() {
        try {
            let buildCounter = 0;
            
            if (fs.existsSync(this.buildCounterFile)) {
                buildCounter = parseInt(fs.readFileSync(this.buildCounterFile, 'utf-8').trim()) || 0;
            }
            
            buildCounter += 1;
            fs.writeFileSync(this.buildCounterFile, buildCounter.toString(), 'utf-8');
            console.log(`内部版本号已增加: ${buildCounter}`);
            
            return buildCounter;
        } catch (error) {
            console.error(`增加内部版本号失败: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 获取内部版本号
     */
    getBuildCounter() {
        try {
            if (fs.existsSync(this.buildCounterFile)) {
                const counter = parseInt(fs.readFileSync(this.buildCounterFile, 'utf-8').trim()) || 0;
                return counter;
            }
            return 0;
        } catch (error) {
            console.error(`获取内部版本号失败: ${error.message}`);
            return 0;
        }
    }
    
    /**
     * 获取系统信息
     */
    getSystemInfo() {
        try {
            const osType = process.platform;
            const osRelease = execSync('uname -r 2>/dev/null || ver', { encoding: 'utf-8' }).trim();
            const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
            
            return {
                osType,
                osRelease,
                timestamp
            };
        } catch (error) {
            console.error(`获取系统信息失败: ${error.message}`);
            return {
                osType: 'Unknown',
                osRelease: 'Unknown',
                timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19)
            };
        }
    }
    
    /**
     * 生成更新说明文档
     */
    generateUpdateInfo(updateDetails = '') {
        try {
            const currentVersion = this.getCurrentVersion();
            const previousVersion = fs.existsSync(this.previousVersionFile) ? 
                fs.readFileSync(this.previousVersionFile, 'utf-8').trim() : 'Unknown';
            const buildCounter = this.getBuildCounter();
            const systemInfo = this.getSystemInfo();
            
            // 默认更新说明
            if (!updateDetails) {
                updateDetails = '系统自动更新，版本迭代优化';
            }
            
            // HTML模板
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
            margin: 5px 0;
        }
        .update-details {
            background-color: #e8f4fc;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .system-info {
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }
        .timestamp {
            font-style: italic;
            color: #95a5a6;
        }
        .highlight {
            color: #e74c3c;
            font-weight: bold;
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
            <p><strong>操作系统:</strong> ${systemInfo.osType} ${systemInfo.osRelease}</p>
            <p><strong>更新时间:</strong> ${systemInfo.timestamp}</p>
        </div>
        
        <p class="timestamp">© MTSCOS 自动化系统</p>
    </div>
</body>
</html>`;
            
            fs.writeFileSync(this.updateInfoFile, htmlContent, 'utf-8');
            console.log(`更新说明文档已生成: ${this.updateInfoFile}`);
            return true;
        } catch (error) {
            console.error(`生成更新说明文档失败: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 完整的版本更新流程
     */
    fullUpdate(versionType = 'patch', updateDetails = '') {
        console.log('开始执行版本更新流程...');
        
        // 1. 更新版本号
        const newVersion = this.updateVersion(versionType);
        if (!newVersion) {
            return false;
        }
        
        // 2. 增加内部版本号
        const buildCounter = this.incrementBuildCounter();
        if (buildCounter === null) {
            return false;
        }
        
        // 3. 生成更新说明文档
        const updateInfoResult = this.generateUpdateInfo(updateDetails);
        
        if (updateInfoResult) {
            console.log('\n✅ 版本更新完成！');
            console.log(`- 新版本: v${newVersion}`);
            console.log(`- 内部版本: Build ${buildCounter}`);
            console.log(`- 更新说明: ${this.updateInfoFile}`);
            return true;
        } else {
            return false;
        }
    }
}

// 主函数
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
    versionManager.fullUpdate(versionType, updateDetails);
}

// 执行主函数
if (require.main === module) {
    main();
}

// 导出类供其他模块使用
module.exports = MTSCOS_VersionManager;
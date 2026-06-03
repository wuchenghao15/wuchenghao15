#!/usr/bin/env node
// -*- coding: utf-8 -*-
/**
 * MTSCOS 版本管理器 v3.0
 * 负责项目版本管理、版本对比、更新检测、版本报告生成
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class MTSCOS_VersionManager {
    constructor() {
        this.projectRoot = path.resolve(__dirname, '..', '..');
        this.versionFile = path.join(this.projectRoot, 'VERSION');
        this.buildCounterFile = path.join(this.projectRoot, 'Logs', 'build_counter.txt');
        this.previousVersionFile = path.join(this.projectRoot, 'Logs', 'previous_version.txt');
        this.updateInfoFile = path.join(this.projectRoot, 'HTML', 'UpdateInfo.html');
        this.logFile = path.join(this.projectRoot, 'Logs', 'version_manager.log');
        
        this.ensureDirExists(path.join(this.projectRoot, 'Logs'));
        this.ensureDirExists(path.join(this.projectRoot, 'HTML'));
        this.ensureDirExists(path.join(this.projectRoot, '.version_backups'));
        
        this.versionHistory = [];
        this.loadVersionHistory();
    }
    
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            this.log(`目录创建: ${dirPath}`);
        }
    }
    
    log(message, isError = false) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ${message}`;
        
        console[isError ? 'error' : 'log'](logMessage);
        
        try {
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`写入日志失败: ${error.message}`);
        }
    }
    
    getCurrentVersion() {
        try {
            if (fs.existsSync(this.versionFile)) {
                const content = fs.readFileSync(this.versionFile, 'utf-8');
                const match = content.match(/VERSION=([\d.]+)/);
                return match ? match[1] : '1.0.0';
            }
            this.log('版本文件不存在，使用默认版本: 1.0.0');
            return '1.0.0';
        } catch (error) {
            this.log(`获取版本失败: ${error.message}`);
            return '1.0.0';
        }
    }
    
    getVersionInfo() {
        try {
            if (fs.existsSync(this.versionFile)) {
                const content = fs.readFileSync(this.versionFile, 'utf-8');
                const info = {};
                
                const versionMatch = content.match(/VERSION=([\d.]+)/);
                const buildDateMatch = content.match(/BUILD_DATE=(\d{4}-\d{2}-\d{2})/);
                const buildNumberMatch = content.match(/BUILD_NUMBER=(\d+)/);
                
                info.version = versionMatch ? versionMatch[1] : '1.0.0';
                info.buildDate = buildDateMatch ? buildDateMatch[1] : new Date().toISOString().split('T')[0];
                info.buildNumber = buildNumberMatch ? buildNumberMatch[1] : '0';
                
                const featureMatch = content.match(/FEATURE_FLAGS="([^"]+)"/);
                if (featureMatch) {
                    info.features = featureMatch[1].split(',').map(f => f.trim());
                }
                
                return info;
            }
            return { version: '1.0.0', buildDate: new Date().toISOString().split('T')[0], buildNumber: '0', features: [] };
        } catch (error) {
            this.log(`获取版本信息失败: ${error.message}`);
            return { version: '1.0.0', buildDate: new Date().toISOString().split('T')[0], buildNumber: '0', features: [] };
        }
    }
    
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
    
    updateVersion(versionType = 'patch') {
        try {
            const currentVersion = this.getCurrentVersion();
            this.savePreviousVersion(currentVersion);
            
            const versionParts = currentVersion.split('.').map(Number);
            
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
            
            const newVersion = versionParts.join('.');
            this._updateVersionFile(newVersion);
            this.log(`版本文件已更新: ${this.versionFile}`);
            
            this.recordVersionHistory(currentVersion, newVersion);
            
            return newVersion;
        } catch (error) {
            this.log(`更新版本失败: ${error.message}`);
            return null;
        }
    }
    
    _updateVersionFile(newVersion) {
        if (fs.existsSync(this.versionFile)) {
            let content = fs.readFileSync(this.versionFile, 'utf-8');
            content = content.replace(/VERSION=[\d.]+/, `VERSION=${newVersion}`);
            content = content.replace(/BUILD_DATE=\d{4}-\d{2}-\d{2}/, `BUILD_DATE=${new Date().toISOString().split('T')[0]}`);
            content = content.replace(/BUILD_NUMBER=\d+/, `BUILD_NUMBER=${Date.now()}`);
            fs.writeFileSync(this.versionFile, content, 'utf-8');
        }
    }
    
    loadVersionHistory() {
        const historyFile = path.join(this.projectRoot, 'Logs', 'version_history.json');
        if (fs.existsSync(historyFile)) {
            try {
                this.versionHistory = JSON.parse(fs.readFileSync(historyFile, 'utf-8'));
            } catch (error) {
                this.versionHistory = [];
            }
        }
    }
    
    recordVersionHistory(fromVersion, toVersion) {
        const record = {
            id: `update_${Date.now()}`,
            fromVersion,
            toVersion,
            timestamp: new Date().toISOString(),
            user: process.env.USER || 'system'
        };
        
        this.versionHistory.push(record);
        
        const historyFile = path.join(this.projectRoot, 'Logs', 'version_history.json');
        fs.writeFileSync(historyFile, JSON.stringify(this.versionHistory, null, 2), 'utf-8');
        
        this.log(`版本历史记录: ${fromVersion} -> ${toVersion}`);
    }
    
    getVersionHistory() {
        return this.versionHistory;
    }
    
    incrementBuildCounter() {
        try {
            let buildCounter = 0;
            
            if (fs.existsSync(this.buildCounterFile)) {
                buildCounter = parseInt(fs.readFileSync(this.buildCounterFile, 'utf-8').trim()) || 0;
            }
            
            buildCounter += 1;
            fs.writeFileSync(this.buildCounterFile, buildCounter.toString(), 'utf-8');
            this.log(`内部版本号已更新: Build ${buildCounter}`);
            
            return buildCounter;
        } catch (error) {
            this.log(`更新内部版本号失败: ${error.message}`);
            return null;
        }
    }
    
    getSystemInfo() {
        try {
            let osInfo = 'Unknown';
            
            try {
                if (process.platform === 'win32') {
                    osInfo = execSync('ver', { encoding: 'utf-8' }).trim();
                } else {
                    osInfo = execSync('uname -a', { encoding: 'utf-8' }).trim();
                }
            } catch (e) {
                osInfo = process.platform;
            }
            
            return osInfo;
        } catch (error) {
            this.log(`获取系统信息失败: ${error.message}`);
            return 'Unknown';
        }
    }
    
    compareVersions(v1, v2) {
        const v1Parts = v1.split('.').map(Number);
        const v2Parts = v2.split('.').map(Number);
        
        for (let i = 0; i < Math.max(v1Parts.length, v2Parts.length); i++) {
            const num1 = v1Parts[i] || 0;
            const num2 = v2Parts[i] || 0;
            
            if (num1 > num2) return 1;
            if (num1 < num2) return -1;
        }
        
        return 0;
    }
    
    checkForUpdates(currentVersion = null) {
        const current = currentVersion || this.getCurrentVersion();
        const versions = this.getAllVersions();
        
        const newerVersions = versions.filter(v => this.compareVersions(v.version, current) > 0);
        
        return {
            currentVersion: current,
            hasUpdate: newerVersions.length > 0,
            latestVersion: versions.length > 0 ? versions[versions.length - 1].version : current,
            availableUpdates: newerVersions.length,
            updates: newerVersions
        };
    }
    
    getAllVersions() {
        return [
            { version: '1.0.0', date: '2025-01-15', type: 'major', description: '初始版本，基础考试系统' },
            { version: '1.1.0', date: '2025-02-20', type: 'minor', description: '新增学习系统模块' },
            { version: '1.1.1', date: '2025-02-28', type: 'patch', description: '修复考试统计bug' },
            { version: '1.2.0', date: '2025-03-15', type: 'minor', description: '新增错题本功能' },
            { version: '1.2.1', date: '2025-03-25', type: 'patch', description: '优化UI布局' },
            { version: '1.3.0', date: '2025-04-10', type: 'minor', description: '新增AI推荐功能' },
            { version: '2.0.0', date: '2025-06-01', type: 'major', description: '重大升级：K12全学段支持' },
            { version: '2.1.0', date: '2025-07-15', type: 'minor', description: '新增成就系统' },
            { version: '2.1.1', date: '2025-07-25', type: 'patch', description: '修复升级通知bug' },
            { version: '2.2.0', date: '2025-08-20', type: 'minor', description: '新增数据统计分析' },
            { version: '2.3.0', date: '2025-09-15', type: 'minor', description: '优化考试过滤功能' },
            { version: '3.0.0', date: '2025-12-01', type: 'major', description: '重大升级：AI能力集增强' },
            { version: '3.1.0', date: '2026-01-15', type: 'minor', description: '新增智能推荐系统' },
            { version: '3.1.1', date: '2026-01-25', type: 'patch', description: '优化推荐算法' },
            { version: '3.2.0', date: '2026-02-20', type: 'minor', description: '新增自适应学习引擎' },
            { version: '3.3.0', date: '2026-04-01', type: 'minor', description: '优化权限系统' },
            { version: '3.4.0', date: '2026-06-02', type: 'minor', description: '升级自动升级系统v2.0 + AI能力集提升' },
            { version: '3.5.0', date: '2026-06-03', type: 'minor', description: '升级版本管理系统v3.0 + 云端同步支持' }
        ];
    }
    
    generateUpdateInfo(updateDetails = '') {
        try {
            const currentVersion = this.getCurrentVersion();
            const previousVersion = fs.existsSync(this.previousVersionFile) ? 
                fs.readFileSync(this.previousVersionFile, 'utf-8').trim() : 'Unknown';
            
            const buildCounter = this.incrementBuildCounter();
            const osInfo = this.getSystemInfo();
            const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
            
            if (!updateDetails) {
                updateDetails = '系统自动更新，版本迭代优化';
            }
            
            const updateInfo = {
                version: currentVersion,
                previousVersion,
                buildNumber: buildCounter,
                updateTime: timestamp,
                systemInfo: osInfo,
                details: updateDetails,
                history: this.versionHistory.slice(-5)
            };
            
            const htmlContent = this._generateUpdateHTML(updateInfo);
            fs.writeFileSync(this.updateInfoFile, htmlContent, 'utf-8');
            this.log(`更新说明文档已生成: ${this.updateInfoFile}`);
            
            return updateInfo;
        } catch (error) {
            this.log(`生成更新说明文档失败: ${error.message}`);
            return null;
        }
    }
    
    _generateUpdateHTML(info) {
        return `<!DOCTYPE html>
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
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            padding: 40px;
            margin-top: 30px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 28px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .version-info {
            background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }
        .version-info p {
            margin: 10px 0;
            font-size: 16px;
        }
        .highlight {
            color: #e74c3c;
            font-weight: bold;
            font-size: 1.2em;
        }
        .update-details {
            background-color: #e8f4fc;
            padding: 25px;
            border-radius: 8px;
            border-left: 5px solid #3498db;
            margin-bottom: 25px;
        }
        .update-details p {
            margin: 0;
            font-size: 16px;
            line-height: 1.8;
        }
        .system-info {
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        .history-section {
            margin-top: 25px;
        }
        .history-item {
            background-color: #f8f9fa;
            padding: 12px 15px;
            border-radius: 6px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .history-arrow {
            color: #3498db;
            font-weight: bold;
        }
        .timestamp {
            font-style: italic;
            color: #95a5a6;
            text-align: right;
            margin-top: 30px;
            font-size: 14px;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .badge-stable {
            background-color: #27ae60;
            color: white;
        }
        .badge-update {
            background-color: #3498db;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 MTSCOS 更新信息</h1>
        
        <div class="version-info">
            <p><strong>当前版本:</strong> <span class="highlight">v${info.version}</span> <span class="badge badge-update">最新</span></p>
            <p><strong>上一版本:</strong> v${info.previousVersion}</p>
            <p><strong>内部版本号:</strong> Build ${info.buildNumber}</p>
        </div>
        
        <h2>📝 更新说明</h2>
        <div class="update-details">
            <p>${info.details}</p>
        </div>
        
        <h2>📜 最近更新历史</h2>
        <div class="history-section">
            ${info.history.length > 0 ? info.history.map(h => `
            <div class="history-item">
                <span>v${h.fromVersion} <span class="history-arrow">→</span> v${h.toVersion}</span>
                <span style="color: #95a5a6; font-size: 13px;">${new Date(h.timestamp).toLocaleString()}</span>
            </div>`).join('') : '<p style="color: #7f8c8d;">暂无更新记录</p>'}
        </div>
        
        <div class="system-info">
            <p><strong>操作系统:</strong> ${info.systemInfo}</p>
            <p><strong>更新时间:</strong> ${info.updateTime}</p>
        </div>
        
        <p class="timestamp">© MTSCOS 自动化系统 | 版本管理 v3.0</p>
    </div>
</body>
</html>`;
    }
    
    createBackup(backupName = null) {
        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const name = backupName || `backup_${timestamp}`;
            const backupDir = path.join(this.projectRoot, '.version_backups', name);
            
            fs.mkdirSync(backupDir, { recursive: true });
            
            if (fs.existsSync(this.versionFile)) {
                fs.copyFileSync(this.versionFile, path.join(backupDir, 'VERSION'));
            }
            
            const historyFile = path.join(this.projectRoot, 'Logs', 'version_history.json');
            if (fs.existsSync(historyFile)) {
                fs.copyFileSync(historyFile, path.join(backupDir, 'version_history.json'));
            }
            
            this.log(`备份已创建: ${backupDir}`);
            return backupDir;
        } catch (error) {
            this.log(`创建备份失败: ${error.message}`);
            return null;
        }
    }
    
    exportVersionData() {
        const data = {
            currentVersion: this.getCurrentVersion(),
            versionInfo: this.getVersionInfo(),
            history: this.versionHistory,
            allVersions: this.getAllVersions(),
            generatedAt: new Date().toISOString(),
            systemInfo: this.getSystemInfo()
        };
        
        return JSON.stringify(data, null, 2);
    }
    
    exportVersionDataToFile(filePath = null) {
        try {
            const fileName = filePath || `version_export_${Date.now()}.json`;
            const fullPath = path.join(this.projectRoot, 'Logs', fileName);
            
            const data = {
                currentVersion: this.getCurrentVersion(),
                versionInfo: this.getVersionInfo(),
                history: this.versionHistory,
                allVersions: this.getAllVersions(),
                generatedAt: new Date().toISOString(),
                systemInfo: this.getSystemInfo()
            };
            
            fs.writeFileSync(fullPath, JSON.stringify(data, null, 2), 'utf-8');
            this.log(`版本数据已导出: ${fullPath}`);
            
            return fullPath;
        } catch (error) {
            this.log(`导出版本数据失败: ${error.message}`);
            return null;
        }
    }
    
    executeVersionUpdate(versionType = 'patch', updateDetails = '') {
        this.log("=====================================");
        this.log("       开始版本更新流程 v3.0       ");
        this.log("=====================================");
        
        this.createBackup();
        
        const newVersion = this.updateVersion(versionType);
        if (!newVersion) {
            this.log("版本更新失败！", true);
            return { success: false, error: '版本更新失败' };
        }
        
        const updateInfo = this.generateUpdateInfo(updateDetails);
        
        if (updateInfo) {
            this.log("\n🎉 版本更新完成！");
            this.log(`- 新版本: v${newVersion}`);
            this.log(`- 更新说明: ${this.updateInfoFile}`);
            this.log("=====================================");
            return { success: true, version: newVersion, updateInfo };
        } else {
            this.log("更新说明文档生成失败！", true);
            return { success: false, version: newVersion, error: '更新说明文档生成失败' };
        }
    }
}

function main() {
    const versionManager = new MTSCOS_VersionManager();
    
    const args = process.argv.slice(2);
    let versionType = 'patch';
    let updateDetails = '';
    
    if (args.length > 0) {
        if (['major', 'minor', 'patch'].includes(args[0])) {
            versionType = args[0];
            updateDetails = args.slice(1).join(' ');
        } else {
            updateDetails = args.join(' ');
        }
    }
    
    const result = versionManager.executeVersionUpdate(versionType, updateDetails);
    process.exit(result.success ? 0 : 1);
}

if (require.main === module) {
    main();
}

module.exports = MTSCOS_VersionManager;
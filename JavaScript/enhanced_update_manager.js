#!/usr/bin/env node
// VERSION: 20251111.0001

/**
 * MTSCOS 增强版更新日志与自动迭代管理器
 * 功能：
 * 1. 结构化更新日志记录
 * 2. 智能版本号生成与迭代
 * 3. 更新事件追踪与分析
 * 4. 日志轮转与管理
 * 5. 更新统计与报告生成
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync, exec } = require('child_process');
const os = require('os');

// 配置
const CONFIG = {
    // 日志配置
    LOG_CONFIG: {
        LOG_DIR: './Logs',
        MAIN_LOG_FILE: 'update_manager.log',
        EVENTS_LOG_FILE: 'update_events.log',
        ROTATE_SIZE: 1024 * 1024, // 1MB
        MAX_BACKUP_LOGS: 5,
        LOG_LEVEL: 'INFO' // DEBUG, INFO, WARNING, ERROR
    },
    // 版本配置
    VERSION_CONFIG: {
        VERSION_FILE: './VERSION',
        VERSION_PATTERN: /^(\d+)\.(\d+)\.(\d+)(?:\-(\w+))?$/,
        VERSION_FORMAT: '$major.$minor.$patch$prerelease',
        AUTO_INCREMENT: true,
        UPDATE_TIMESTAMP: true
    },
    // 更新事件配置
    EVENT_CONFIG: {
        EVENT_TYPES: [
            'VERSION_UPDATE',
            'FILE_CHANGE',
            'DEPENDENCY_UPDATE',
            'CONFIG_CHANGE',
            'MANUAL_UPDATE',
            'AUTO_UPDATE',
            'SYSTEM_EVENT',
            'ERROR'
        ],
        RETAIN_DAYS: 30
    },
    // 更新报告配置
    REPORT_CONFIG: {
        ENABLED: true,
        REPORT_DIR: './Reports',
        REPORT_INTERVAL: 'weekly', // daily, weekly, monthly
        TEMPLATE_DIR: './Templates'
    },
    // 历史记录配置
    HISTORY_CONFIG: {
        CHANGELOG_FILE: './Documentation/Text/changelog.txt',
        COMPLETE_HISTORY_FILE: './Documentation/Markdown/COMPLETE_HISTORY.md',
        AUTO_UPDATE: true,
        ENTRY_POINTS_FILE: './Documentation/Text/entry_points.txt',
        DUPLICATE_FILES_FILE: './Documentation/Text/duplicate_files.txt'
    },
    // 忽略的目录和文件
    IGNORE_PATTERNS: [
        'node_modules',
        '.git',
        '.svn',
        'Logs',
        'Backups',
        'temp',
        'tmp',
        '*.log',
        '*.bak',
        '*.swp',
        '.*'
    ]
};

/**
 * 增强版日志管理器
 */
class EnhancedLogger {
    constructor() {
        this.logDir = CONFIG.LOG_CONFIG.LOG_DIR;
        this.mainLogFile = path.join(this.logDir, CONFIG.LOG_CONFIG.MAIN_LOG_FILE);
        this.ensureDirExists(this.logDir);
    }

    ensureDirExists(dir) {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }

    getTimestamp() {
        return new Date().toISOString().replace('T', ' ').substring(0, 23);
    }

    shouldLog(level) {
        const levels = { DEBUG: 0, INFO: 1, WARNING: 2, ERROR: 3 };
        return levels[level] >= levels[CONFIG.LOG_CONFIG.LOG_LEVEL];
    }

    log(message, level = 'INFO') {
        if (!this.shouldLog(level)) return;

        const timestamp = this.getTimestamp();
        const logMessage = `[${timestamp}] [${level}] ${message}\n`;

        // 输出到控制台
        if (level === 'ERROR') {
            console.error(logMessage.trim());
        } else {
            console.log(logMessage.trim());
        }

        // 检查是否需要轮转日志
        this.checkAndRotateLogs();

        // 写入日志文件
        try {
            fs.appendFileSync(this.mainLogFile, logMessage, 'utf8');
        } catch (error) {
            console.error(`写入日志文件失败: ${error.message}`);
        }
    }

    checkAndRotateLogs() {
        try {
            if (fs.existsSync(this.mainLogFile)) {
                const stats = fs.statSync(this.mainLogFile);
                if (stats.size >= CONFIG.LOG_CONFIG.ROTATE_SIZE) {
                    this.rotateLogs();
                }
            }
        } catch (error) {
            console.error(`检查日志大小失败: ${error.message}`);
        }
    }

    rotateLogs() {
        try {
            // 清理旧的备份
            const backupFiles = fs.readdirSync(this.logDir)
                .filter(file => file.startsWith(`${CONFIG.LOG_CONFIG.MAIN_LOG_FILE}.`))
                .sort();

            while (backupFiles.length >= CONFIG.LOG_CONFIG.MAX_BACKUP_LOGS) {
                const fileToDelete = path.join(this.logDir, backupFiles.shift());
                fs.unlinkSync(fileToDelete);
                this.log(`已删除旧日志备份: ${fileToDelete}`, 'DEBUG');
            }

            // 创建新备份
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupPath = path.join(this.logDir, `${CONFIG.LOG_CONFIG.MAIN_LOG_FILE}.${timestamp}`);
            fs.renameSync(this.mainLogFile, backupPath);
            this.log(`日志已轮转: ${backupPath}`, 'INFO');
        } catch (error) {
            console.error(`轮转日志失败: ${error.message}`);
        }
    }

    info(message) { this.log(message, 'INFO'); }
    warning(message) { this.log(message, 'WARNING'); }
    error(message) { this.log(message, 'ERROR'); }
    debug(message) { this.log(message, 'DEBUG'); }
    success(message) { this.log(message, 'SUCCESS'); }
}

/**
 * 更新事件管理器
 */
class UpdateEventManager {
    constructor() {
        this.logDir = CONFIG.LOG_CONFIG.LOG_DIR;
        this.eventLogFile = path.join(this.logDir, CONFIG.LOG_CONFIG.EVENTS_LOG_FILE);
        this.logger = new EnhancedLogger();
        this.ensureLogFileExists();
    }

    ensureLogFileExists() {
        if (!fs.existsSync(this.eventLogFile)) {
            this.logger.debug(`创建事件日志文件: ${this.eventLogFile}`);
            fs.writeFileSync(this.eventLogFile, '', 'utf8');
        }
    }

    /**
     * 记录更新事件
     * @param {string} eventType - 事件类型
     * @param {object} eventData - 事件数据
     * @param {string} source - 事件源
     */
    logEvent(eventType, eventData = {}, source = 'system') {
        if (!CONFIG.EVENT_CONFIG.EVENT_TYPES.includes(eventType)) {
            this.logger.warning(`未知的事件类型: ${eventType}`);
        }

        const event = {
            timestamp: new Date().toISOString(),
            eventType,
            source,
            data: eventData,
            processId: process.pid,
            systemInfo: {
                platform: process.platform,
                arch: process.arch,
                nodeVersion: process.version
            }
        };

        try {
            // 检查是否需要清理旧事件
            this.cleanupOldEvents();

            // 写入事件
            fs.appendFileSync(this.eventLogFile, JSON.stringify(event) + '\n', 'utf8');
            this.logger.debug(`已记录事件: ${eventType}`);
        } catch (error) {
            this.logger.error(`记录事件失败: ${error.message}`);
        }
    }

    cleanupOldEvents() {
        try {
            const cutoffDate = new Date(Date.now() - CONFIG.EVENT_CONFIG.RETAIN_DAYS * 24 * 60 * 60 * 1000);
            const events = [];
            let hasOldEvents = false;

            if (fs.existsSync(this.eventLogFile)) {
            try {
                const lines = fs.readFileSync(this.eventLogFile, 'utf8').split('\n').filter(Boolean);
                
                for (const line of lines) {
                    try {
                        const event = JSON.parse(line);
                        if (new Date(event.timestamp) > cutoffDate) {
                            events.push(line);
                        } else {
                            hasOldEvents = true;
                        }
                    } catch (e) {
                        this.logger.warning(`解析事件行失败: ${e.message}`);
                        continue;
                    }
                }
            } catch (readError) {
                this.logger.error(`读取事件日志文件失败: ${readError.message}`);
                return;
            }

                if (hasOldEvents) {
                    fs.writeFileSync(this.eventLogFile, events.join('\n') + '\n', 'utf8');
                    this.logger.info(`已清理 ${CONFIG.EVENT_CONFIG.RETAIN_DAYS} 天前的事件记录`);
                }
            }
        } catch (error) {
            this.logger.error(`清理旧事件失败: ${error.message}`);
        }
    }

    /**
     * 获取事件统计信息
     * @param {number} days - 统计天数
     * @returns {object} 事件统计
     */
    getEventStats(days = 7) {
        try {
            const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
            const stats = {
                total: 0,
                byType: {},
                bySource: {},
                timeline: []
            };

            if (fs.existsSync(this.eventLogFile)) {
                try {
                    const lines = fs.readFileSync(this.eventLogFile, 'utf8').split('\n').filter(Boolean);
                    
                    for (const line of lines) {
                        try {
                            const event = JSON.parse(line);
                            if (new Date(event.timestamp) > cutoffDate) {
                                stats.total++;
                                
                                // 按类型统计
                                if (!stats.byType[event.eventType]) {
                                    stats.byType[event.eventType] = 0;
                                }
                                stats.byType[event.eventType]++;

                                // 按源统计
                                if (!stats.bySource[event.source]) {
                                    stats.bySource[event.source] = 0;
                                }
                                stats.bySource[event.source]++;

                                // 时间线
                                stats.timeline.push({
                                    timestamp: event.timestamp,
                                    eventType: event.eventType,
                                    source: event.source
                                });
                            }
                        } catch (e) {
                            this.logger.warning(`解析事件行失败: ${e.message}`);
                            continue;
                        }
                    }
                } catch (readError) {
                    this.logger.error(`读取事件日志文件失败: ${readError.message}`);
                    return null;
                }
            }

            return stats;
        } catch (error) {
            this.logger.error(`获取事件统计失败: ${error.message}`);
            return null;
        }
    }
}

/**
 * 版本管理器
 */
class VersionManager {
    constructor() {
        this.versionFile = CONFIG.VERSION_CONFIG.VERSION_FILE;
        this.logger = new EnhancedLogger();
        this.eventManager = new UpdateEventManager();
        this.changelogFile = CONFIG.HISTORY_CONFIG.CHANGELOG_FILE;
        this.completeHistoryFile = CONFIG.HISTORY_CONFIG.COMPLETE_HISTORY_FILE;
    }

    /**
     * 获取当前版本
     * @returns {string} 当前版本号
     */
    getCurrentVersion() {
        try {
            if (fs.existsSync(this.versionFile)) {
                return fs.readFileSync(this.versionFile, 'utf8').trim();
            }
            return '1.3.0'; // 默认版本
        } catch (error) {
            this.logger.error(`读取版本文件失败: ${error.message}`);
            return '1.3.0';
        }
    }

    /**
     * 解析版本号
     * @param {string} version - 版本字符串
     * @returns {object} 解析后的版本对象
     */
    parseVersion(version) {
        const match = version.match(CONFIG.VERSION_CONFIG.VERSION_PATTERN);
        if (match) {
            return {
                major: parseInt(match[1]) || 0,
                minor: parseInt(match[2]) || 0,
                patch: parseInt(match[3]) || 0,
                prerelease: match[4] ? `-${match[4]}` : ''
            };
        }
        // 返回默认版本解析
        return {
            major: 1,
            minor: 0,
            patch: 0,
            prerelease: ''
        };
    }

    /**
     * 生成新版本号
     * @param {string} incrementType - 递增类型: major, minor, patch
     * @param {string} prerelease - 预发布版本标识
     * @returns {string} 新版本号
     */
    generateNewVersion(incrementType = 'patch', prerelease = '') {
        const currentVersion = this.getCurrentVersion();
        const parsed = this.parseVersion(currentVersion);
        
        // 递增版本号
        switch (incrementType) {
            case 'major':
                parsed.major++;
                parsed.minor = 0;
                parsed.patch = 0;
                break;
            case 'minor':
                parsed.minor++;
                parsed.patch = 0;
                break;
            case 'patch':
            default:
                parsed.patch++;
                break;
        }

        parsed.prerelease = prerelease ? `-${prerelease}` : '';
        
        // 应用版本格式
        return CONFIG.VERSION_CONFIG.VERSION_FORMAT
            .replace('$major', parsed.major)
            .replace('$minor', parsed.minor)
            .replace('$patch', parsed.patch)
            .replace('$prerelease', parsed.prerelease);
    }

    /**
     * 更新版本
     * @param {string} incrementType - 递增类型
     * @param {string} prerelease - 预发布版本标识
     * @param {string} comment - 更新注释
     * @returns {string} 新版本号
     */
    updateVersion(incrementType = 'patch', prerelease = '', comment = '') {
        const newVersion = this.generateNewVersion(incrementType, prerelease);
        
        try {
            // 确保目录存在
            const versionDir = path.dirname(this.versionFile);
            if (versionDir && versionDir !== '.') {
                this.logger.ensureDirExists(versionDir);
            }

            // 写入版本文件
            fs.writeFileSync(this.versionFile, newVersion, 'utf8');
            
            // 记录更新事件
            this.eventManager.logEvent('VERSION_UPDATE', {
                from: this.getCurrentVersion(),
                to: newVersion,
                incrementType,
                prerelease,
                comment
            }, 'version_manager');
            
            // 自动更新历史记录
            if (CONFIG.HISTORY_CONFIG.AUTO_UPDATE) {
                this.updateHistoryRecords(this.getCurrentVersion(), newVersion, comment);
            }
            
            this.logger.success(`版本已更新: ${newVersion}`);
            return newVersion;
        } catch (error) {
            this.logger.error(`更新版本失败: ${error.message}`);
            this.eventManager.logEvent('ERROR', {
                action: 'update_version',
                error: error.message,
                version: newVersion
            }, 'version_manager');
            return null;
        }
    }
    
    updateHistoryRecords(previousVersion, newVersion, comment) {
        try {
            // 确保目录存在
            const ensureDir = (filePath) => {
                const dir = path.dirname(filePath);
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
            };
            
            // 格式化变更内容
            let changes = comment;
            if (!changes || changes.trim() === '') {
                changes = `- 系统自动更新: ${new Date().toISOString().split('T')[0]}`;
            } else {
                // 将逗号分隔的内容格式化为列表
                changes = changes.split(',').map(change => `- ${change.trim()}`).join('\n');
            }
            
            // 更新changelog.txt
            ensureDir(this.changelogFile);
            if (fs.existsSync(this.changelogFile)) {
                let existingContent = fs.readFileSync(this.changelogFile, 'utf8');
                
                // 检查是否已包含当前版本
                if (!existingContent.includes(`## ${newVersion}`)) {
                    // 移除旧标题并添加新版本
                    existingContent = existingContent.replace(/^# MTSCOS 更新日志[\s\S]*?(?=^## |$)/m, '');
                    const title = '# MTSCOS 更新日志\n\n';
                    const newEntry = `## ${newVersion} (${new Date().toISOString().replace('T', ' ').substring(0, 19)})\n${changes}\n\n`;
                    fs.writeFileSync(this.changelogFile, title + newEntry + existingContent);
                    this.logger.log(`已更新 changelog.txt 至版本 ${newVersion}`, 'INFO');
                }
            } else {
                // 创建新文件
                const content = `# MTSCOS 更新日志\n\n## ${newVersion} (${new Date().toISOString().replace('T', ' ').substring(0, 19)})\n${changes}\n\n`;
                fs.writeFileSync(this.changelogFile, content);
                this.logger.log(`已创建 changelog.txt 并记录版本 ${newVersion}`, 'INFO');
            }
            
            // 更新完整历史记录
            ensureDir(this.completeHistoryFile);
            const currentDate = new Date().toISOString().split('T')[0];
            const newEntry = `### v${newVersion} (当前版本) - ${currentDate}\n**主要更新:**\n${changes}\n\n`;
            
            if (fs.existsSync(this.completeHistoryFile)) {
                let existingContent = fs.readFileSync(this.completeHistoryFile, 'utf8');
                
                // 移除现有的"当前版本"标记
                existingContent = existingContent.replace(/v(\d+\.\d+\.\d+) \(当前版本\)/g, 'v$1');
                
                // 插入新版本
                const updatedContent = existingContent.replace(
                    /## 版本更新记录\n\n/, 
                    `## 版本更新记录\n\n${newEntry}`
                );
                
                // 更新时间戳
                const finalContent = updatedContent.replace(
                    /更新时间: .*/, 
                    `更新时间: ${currentDate}`
                );
                
                fs.writeFileSync(this.completeHistoryFile, finalContent);
                this.logger.log(`已更新完整历史记录至版本 v${newVersion}`, 'INFO');
            }
            
            // 执行入口文件和重复文件检测
            try {
                const updateChangelogScript = path.join(process.cwd(), 'Scripts', 'update_changelog.sh');
                if (fs.existsSync(updateChangelogScript)) {
                    execSync(`chmod +x ${updateChangelogScript} && ${updateChangelogScript}`, {
                        stdio: 'ignore',
                        timeout: 60000
                    });
                    this.logger.log('已执行入口文件和重复文件检测', 'INFO');
                }
            } catch (scriptError) {
                this.logger.log(`执行检测脚本时出现警告: ${scriptError.message}`, 'WARNING');
            }
            
        } catch (error) {
            this.logger.log(`更新历史记录失败: ${error.message}`, 'WARNING');
        }
    }

    /**
     * 获取版本历史
     * @returns {Array} 版本历史记录
     */
    getVersionHistory() {
        try {
            // 尝试从git获取历史
            try {
                const gitLog = execSync('git log --pretty=format:"%h|%ad|%s" --date=iso -- ' + this.versionFile, { encoding: 'utf8' });
                return gitLog.split('\n')
                    .filter(Boolean)
                    .map(line => {
                        const [hash, date, message] = line.split('|');
                        return {
                            hash,
                            date,
                            message
                        };
                    });
            } catch (gitError) {
                this.logger.warning('无法从Git获取版本历史');
                // 返回仅有当前版本的历史
                return [{
                    hash: 'N/A',
                    date: new Date().toISOString(),
                    message: `Current version: ${this.getCurrentVersion()}`
                }];
            }
        } catch (error) {
            this.logger.error(`获取版本历史失败: ${error.message}`);
            return [];
        }
    }
}

/**
 * 文件监控管理器
 */
class FileMonitorManager {
    constructor() {
        this.logger = new EnhancedLogger();
        this.eventManager = new UpdateEventManager();
    }

    /**
     * 检查文件变化
     * @param {string} directory - 要检查的目录
     * @returns {object} 文件变化统计
     */
    checkFileChanges(directory) {
        const stats = {
            total: 0,
            changed: 0,
            added: 0,
            removed: 0,
            details: []
        };

        try {
            const fileHashStore = this.loadFileHashes();
            const currentFiles = this.collectFiles(directory);
            
            // 检查现有文件
            for (const file of currentFiles) {
                stats.total++;
                const currentHash = this.calculateFileHash(file);
                const previousHash = fileHashStore[file];
                
                if (!previousHash) {
                    stats.added++;
                    stats.details.push({
                        file,
                        type: 'added',
                        hash: currentHash
                    });
                } else if (previousHash !== currentHash) {
                    stats.changed++;
                    stats.details.push({
                        file,
                        type: 'changed',
                        oldHash: previousHash,
                        newHash: currentHash
                    });
                }
                
                // 更新哈希存储
                fileHashStore[file] = currentHash;
            }

            // 检查已删除文件
            for (const file in fileHashStore) {
                if (!currentFiles.includes(file)) {
                    stats.removed++;
                    stats.details.push({
                        file,
                        type: 'removed',
                        hash: fileHashStore[file]
                    });
                    delete fileHashStore[file];
                }
            }

            // 保存新的哈希值
            this.saveFileHashes(fileHashStore);

            // 记录文件变化事件
            if (stats.changed > 0 || stats.added > 0 || stats.removed > 0) {
                this.eventManager.logEvent('FILE_CHANGE', {
                    stats,
                    directory
                }, 'file_monitor');
            }

            return stats;
        } catch (error) {
            this.logger.error(`检查文件变化失败: ${error.message}`);
            return null;
        }
    }

    collectFiles(directory) {
        const files = [];
        
        function scan(dir) {
            const entries = fs.readdirSync(dir);
            for (const entry of entries) {
                const fullPath = path.join(dir, entry);
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    if (!CONFIG.IGNORE_PATTERNS.includes(entry)) {
                        scan(fullPath);
                    }
                } else if (stat.isFile()) {
                    const shouldIgnore = CONFIG.IGNORE_PATTERNS.some(pattern => {
                        if (pattern.startsWith('*.')) {
                            return entry.endsWith(pattern.substring(1));
                        }
                        return entry === pattern || entry.startsWith('.');
                    });
                    
                    if (!shouldIgnore) {
                        files.push(fullPath);
                    }
                }
            }
        }
        
        scan(directory);
        return files;
    }

    calculateFileHash(filePath) {
        const buffer = fs.readFileSync(filePath);
        return crypto.createHash('md5').update(buffer).digest('hex');
    }

    loadFileHashes() {
        const hashFile = path.join(CONFIG.LOG_CONFIG.LOG_DIR, 'file_hashes.json');
        try {
            if (fs.existsSync(hashFile)) {
                return JSON.parse(fs.readFileSync(hashFile, 'utf8'));
            }
        } catch (error) {
            this.logger.warning(`加载文件哈希失败: ${error.message}`);
        }
        return {};
    }

    saveFileHashes(hashes) {
        const hashFile = path.join(CONFIG.LOG_CONFIG.LOG_DIR, 'file_hashes.json');
        try {
            fs.writeFileSync(hashFile, JSON.stringify(hashes, null, 2), 'utf8');
        } catch (error) {
            this.logger.error(`保存文件哈希失败: ${error.message}`);
        }
    }
}

/**
 * 更新报告生成器
 */
class UpdateReportGenerator {
    constructor() {
        this.reportDir = CONFIG.REPORT_CONFIG.REPORT_DIR;
        this.logger = new EnhancedLogger();
        this.eventManager = new UpdateEventManager();
        this.versionManager = new VersionManager();
        this.ensureReportDirExists();
    }

    ensureReportDirExists() {
        if (!fs.existsSync(this.reportDir)) {
            fs.mkdirSync(this.reportDir, { recursive: true });
        }
    }

    /**
     * 生成更新报告
     * @param {string} period - 报告周期: daily, weekly, monthly
     * @returns {string} 报告文件路径
     */
    generateReport(period = 'weekly') {
        try {
            const reportDate = new Date();
            const reportId = reportDate.toISOString().replace(/[:.]/g, '-').substring(0, 10);
            const reportPath = path.join(this.reportDir, `update_report_${period}_${reportId}.json`);
            
            // 收集数据
            const days = period === 'daily' ? 1 : period === 'weekly' ? 7 : 30;
            const eventStats = this.eventManager.getEventStats(days);
            const versionHistory = this.versionManager.getVersionHistory().slice(0, 10); // 最近10条
            
            const report = {
                generatedAt: reportDate.toISOString(),
                period,
                currentVersion: this.versionManager.getCurrentVersion(),
                eventStats,
                versionHistory,
                systemInfo: {
                    platform: process.platform,
                    arch: process.arch,
                    nodeVersion: process.version,
                    hostname: require('os').hostname()
                },
                summary: this.generateSummary(eventStats, versionHistory)
            };
            
            // 保存报告
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8');
            
            // 生成HTML版本
            this.generateHtmlReport(report, reportPath.replace('.json', '.html'));
            
            this.logger.info(`更新报告已生成: ${reportPath}`);
            
            return reportPath;
        } catch (error) {
            this.logger.error(`生成更新报告失败: ${error.message}`);
            return null;
        }
    }

    generateSummary(eventStats, versionHistory) {
        let summary = [];
        
        if (eventStats) {
            summary.push(`在报告周期内共记录 ${eventStats.total} 个更新事件`);
            
            const topEvents = Object.entries(eventStats.byType)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3);
            
            if (topEvents.length > 0) {
                summary.push(`主要事件类型: ${topEvents.map(([type, count]) => `${type} (${count})`).join(', ')}`);
            }
        }
        
        if (versionHistory && versionHistory.length > 0) {
            summary.push(`当前版本: ${this.versionManager.getCurrentVersion()}`);
            
            if (versionHistory.length > 1) {
                summary.push(`最近更新: ${versionHistory[0].message}`);
            }
        }
        
        return summary.join('\n');
    }

    generateHtmlReport(report, htmlPath) {
        const html = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTSCOS 更新报告 - ${report.period} ${report.generatedAt.substring(0, 10)}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; }
        .summary { background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .stats { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
        .stat-card { flex: 1; min-width: 250px; background-color: #f9f9f9; padding: 15px; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MTSCOS 更新报告</h1>
        <p>生成时间: ${new Date(report.generatedAt).toLocaleString()}</p>
        <p>报告周期: ${report.period}</p>
        <p>当前版本: ${report.currentVersion}</p>
        
        <div class="summary">
            <h2>摘要</h2>
            <pre>${report.summary}</pre>
        </div>
        
        <h2>事件统计</h2>
        <div class="stats">
            <div class="stat-card">
                <h3>总事件数</h3>
                <p>${report.eventStats.total}</p>
            </div>
        </div>
        
        <h2>按事件类型统计</h2>
        <table>
            <tr>
                <th>事件类型</th>
                <th>数量</th>
            </tr>
            ${Object.entries(report.eventStats.byType)
                .map(([type, count]) => `<tr><td>${type}</td><td>${count}</td></tr>`)
                .join('')}
        </table>
        
        <h2>版本历史</h2>
        <table>
            <tr>
                <th>提交哈希</th>
                <th>日期</th>
                <th>信息</th>
            </tr>
            ${report.versionHistory
                .map(history => `<tr><td>${history.hash}</td><td>${new Date(history.date).toLocaleString()}</td><td>${history.message}</td></tr>`)
                .join('')}
        </table>
        
        <div class="footer">
            <p>此报告由 MTSCOS 增强版更新管理器自动生成</p>
        </div>
    </div>
</body>
</html>
        `;
        
        fs.writeFileSync(htmlPath, html, 'utf8');
    }
}

/**
 * 自动更新管理器
 */
class AutoUpdateManager {
    constructor() {
        this.logger = new EnhancedLogger();
        this.eventManager = new UpdateEventManager();
        this.versionManager = new VersionManager();
        this.fileMonitor = new FileMonitorManager();
        this.reportGenerator = new UpdateReportGenerator();
        this.lastUpdateCheck = null;
    }

    /**
     * 执行自动更新检查
     * @returns {object} 更新结果
     */
    async checkAndUpdate() {
        const result = {
            success: false,
            message: '',
            fileChanges: null,
            versionUpdated: false,
            newVersion: null,
            reportPath: null
        };

        try {
            this.logger.info('开始执行自动更新检查...');
            
            // 检查文件变化
            const projectRoot = process.cwd();
            const fileChanges = this.fileMonitor.checkFileChanges(projectRoot);
            result.fileChanges = fileChanges;
            
            // 如果有文件变化，更新版本
            if (fileChanges && (fileChanges.changed > 0 || fileChanges.added > 0)) {
                this.logger.info(`检测到 ${fileChanges.changed} 个文件变更，${fileChanges.added} 个文件新增`);
                
                // 根据变更规模决定版本递增类型
                let incrementType = 'patch';
                if (fileChanges.changed > 10 || fileChanges.added > 5) {
                    incrementType = 'minor';
                }
                
                const newVersion = this.versionManager.updateVersion(
                    incrementType,
                    '',
                    `自动更新: ${fileChanges.changed}个文件变更, ${fileChanges.added}个文件新增`
                );
                
                if (newVersion) {
                    result.versionUpdated = true;
                    result.newVersion = newVersion;
                }
            }
            
            // 生成更新报告
            const reportPath = this.reportGenerator.generateReport('daily');
            result.reportPath = reportPath;
            
            result.success = true;
            result.message = '自动更新检查完成';
            
            this.eventManager.logEvent('AUTO_UPDATE', result, 'auto_update_manager');
            
            return result;
        } catch (error) {
            this.logger.error(`自动更新失败: ${error.message}`);
            result.message = error.message;
            
            this.eventManager.logEvent('ERROR', {
                action: 'auto_update',
                error: error.message
            }, 'auto_update_manager');
            
            return result;
        }
    }

    /**
     * 手动触发更新
     * @param {string} incrementType - 递增类型
     * @param {string} prerelease - 预发布版本
     * @param {string} comment - 更新注释
     * @returns {object} 更新结果
     */
    triggerManualUpdate(incrementType = 'patch', prerelease = '', comment = '') {
        try {
            this.logger.info(`开始手动更新，类型: ${incrementType}`);
            
            const newVersion = this.versionManager.updateVersion(incrementType, prerelease, comment);
            
            const result = {
                success: !!newVersion,
                newVersion,
                message: newVersion ? '手动更新成功' : '手动更新失败'
            };
            
            this.eventManager.logEvent('MANUAL_UPDATE', {
                incrementType,
                prerelease,
                comment,
                newVersion
            }, 'user');
            
            return result;
        } catch (error) {
            this.logger.error(`手动更新失败: ${error.message}`);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * 获取更新状态
     * @returns {object} 更新状态信息
     */
    getUpdateStatus() {
        const eventStats = this.eventManager.getEventStats(7);
        const versionHistory = this.versionManager.getVersionHistory().slice(0, 5);
        
        return {
            currentVersion: this.versionManager.getCurrentVersion(),
            lastWeekEvents: eventStats,
            recentVersions: versionHistory,
            nextScheduledUpdate: this.calculateNextUpdateTime()
        };
    }

    calculateNextUpdateTime() {
        // 计算下次计划更新时间（24小时后）
        const nextUpdate = new Date(Date.now() + 24 * 60 * 60 * 1000);
        return nextUpdate.toISOString();
    }
}

/**
 * 主函数
 */
async function main() {
    const logger = new EnhancedLogger();
    logger.info('====================================');
    logger.info('  MTSCOS 增强版更新管理器启动');
    logger.info('====================================');
    
    try {
        const manager = new AutoUpdateManager();
        
        // 处理命令行参数
        const args = process.argv.slice(2);
        
        if (args.includes('--check')) {
            // 检查更新
            const result = await manager.checkAndUpdate();
            logger.info('\n更新检查结果:');
            logger.info(`状态: ${result.success ? '成功' : '失败'}`);
            logger.info(`消息: ${result.message}`);
            
            if (result.versionUpdated) {
                logger.success(`版本已更新至: ${result.newVersion}`);
            }
            
            if (result.reportPath) {
                logger.info(`报告已生成: ${result.reportPath}`);
            }
        } else if (args.includes('--update')) {
            // 手动更新
            const incrementType = args.includes('--major') ? 'major' : 
                                args.includes('--minor') ? 'minor' : 'patch';
            const prerelease = args.find(arg => arg.startsWith('--prerelease='))?.split('=')[1] || '';
            const comment = args.find(arg => arg.startsWith('--comment='))?.split('=')[1] || '手动版本更新';
            
            const result = manager.triggerManualUpdate(incrementType, prerelease, comment);
            logger.info('\n手动更新结果:');
            logger.info(`状态: ${result.success ? '成功' : '失败'}`);
            
            if (result.newVersion) {
                logger.success(`新版本: ${result.newVersion}`);
            }
        } else if (args.includes('--status')) {
            // 查看状态
            const status = manager.getUpdateStatus();
            logger.info('\n系统更新状态:');
            logger.info(`当前版本: ${status.currentVersion}`);
            logger.info(`本周事件数: ${status.lastWeekEvents?.total || 0}`);
            logger.info(`下次计划更新: ${new Date(status.nextScheduledUpdate).toLocaleString()}`);
        } else if (args.includes('--report')) {
            // 生成报告
            const period = args.find(arg => arg.startsWith('--period='))?.split('=')[1] || 'weekly';
            const reportGenerator = new UpdateReportGenerator();
            const reportPath = reportGenerator.generateReport(period);
            
            if (reportPath) {
                logger.success(`\n报告已生成: ${reportPath}`);
                logger.info(`HTML版本: ${reportPath.replace('.json', '.html')}`);
            }
        } else {
            // 默认执行自动检查
            const result = await manager.checkAndUpdate();
            logger.info('\n更新检查完成');
            
            if (result.reportPath) {
                logger.info(`详情请查看报告: ${result.reportPath}`);
            }
        }
        
    } catch (error) {
        logger.error(`执行失败: ${error.message}`);
        logger.error(error.stack);
        process.exit(1);
    }
}

// 导出模块
module.exports = {
    EnhancedLogger,
    UpdateEventManager,
    VersionManager,
    FileMonitorManager,
    UpdateReportGenerator,
    AutoUpdateManager,
    main
};

// 直接执行时运行主函数
if (require.main === module) {
    main().catch(error => {
        console.error('未捕获的异常:', error);
        process.exit(1);
    });
}
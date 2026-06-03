// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * MTSCOS 版本管理API路由 v3.0
 * 提供完整的版本管理接口：版本查询、对比、更新检测、统计报告等
 */

const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');

const VERSION_FILE = path.join(__dirname, '..', '..', '..', 'VERSION');

function getVersionFileContent() {
    try {
        if (fs.existsSync(VERSION_FILE)) {
            return fs.readFileSync(VERSION_FILE, 'utf-8');
        }
        return null;
    } catch (error) {
        console.error(`读取版本文件失败: ${error.message}`);
        return null;
    }
}

function parseVersionFile(content) {
    const info = {};
    const lines = content.split('\n');
    
    for (const line of lines) {
        if (line.startsWith('VERSION=')) {
            info.version = line.split('=')[1].trim();
        } else if (line.startsWith('BUILD_DATE=')) {
            info.buildDate = line.split('=')[1].trim();
        } else if (line.startsWith('BUILD_NUMBER=')) {
            info.buildNumber = line.split('=')[1].trim();
        } else if (line.startsWith('MAJOR=')) {
            info.major = parseInt(line.split('=')[1].trim());
        } else if (line.startsWith('MINOR=')) {
            info.minor = parseInt(line.split('=')[1].trim());
        } else if (line.startsWith('PATCH=')) {
            info.patch = parseInt(line.split('=')[1].trim());
        } else if (line.startsWith('FEATURE_FLAGS=')) {
            const flags = line.split('=')[1].trim();
            info.features = flags.replace(/["']/g, '').split(',').map(f => f.trim());
        } else if (line.startsWith('FRONTEND_VERSION=')) {
            info.frontendVersion = line.split('=')[1].trim();
        } else if (line.startsWith('BACKEND_VERSION=')) {
            info.backendVersion = line.split('=')[1].trim();
        } else if (line.startsWith('DATABASE_VERSION=')) {
            info.databaseVersion = line.split('=')[1].trim();
        } else if (line.startsWith('API_VERSION=')) {
            info.apiVersion = line.split('=')[1].trim();
        } else if (line.startsWith('RELEASE_TYPE=')) {
            info.releaseType = line.split('=')[1].trim();
        } else if (line.startsWith('RELEASE_CHANNEL=')) {
            info.releaseChannel = line.split('=')[1].trim();
        } else if (line.startsWith('LAST_UPDATE=')) {
            info.lastUpdate = line.split('=')[1].trim();
        }
    }
    
    return info;
}

function getAllVersions() {
    return [
        { version: '1.0.0', date: '2025-01-15', type: 'major', description: '初始版本，基础考试系统', status: 'stable' },
        { version: '1.1.0', date: '2025-02-20', type: 'minor', description: '新增学习系统模块', status: 'stable' },
        { version: '1.1.1', date: '2025-02-28', type: 'patch', description: '修复考试统计bug', status: 'stable' },
        { version: '1.2.0', date: '2025-03-15', type: 'minor', description: '新增错题本功能', status: 'stable' },
        { version: '1.2.1', date: '2025-03-25', type: 'patch', description: '优化UI布局', status: 'stable' },
        { version: '1.3.0', date: '2025-04-10', type: 'minor', description: '新增AI推荐功能', status: 'stable' },
        { version: '2.0.0', date: '2025-06-01', type: 'major', description: '重大升级：K12全学段支持', status: 'stable' },
        { version: '2.1.0', date: '2025-07-15', type: 'minor', description: '新增成就系统', status: 'stable' },
        { version: '2.1.1', date: '2025-07-25', type: 'patch', description: '修复升级通知bug', status: 'stable' },
        { version: '2.2.0', date: '2025-08-20', type: 'minor', description: '新增数据统计分析', status: 'stable' },
        { version: '2.3.0', date: '2025-09-15', type: 'minor', description: '优化考试过滤功能', status: 'stable' },
        { version: '3.0.0', date: '2025-12-01', type: 'major', description: '重大升级：AI能力集增强', status: 'stable' },
        { version: '3.1.0', date: '2026-01-15', type: 'minor', description: '新增智能推荐系统', status: 'stable' },
        { version: '3.1.1', date: '2026-01-25', type: 'patch', description: '优化推荐算法', status: 'stable' },
        { version: '3.2.0', date: '2026-02-20', type: 'minor', description: '新增自适应学习引擎', status: 'stable' },
        { version: '3.3.0', date: '2026-04-01', type: 'minor', description: '优化权限系统', status: 'stable' },
        { version: '3.4.0', date: '2026-06-02', type: 'minor', description: '升级自动升级系统v2.0 + AI能力集提升', status: 'stable' },
        { version: '3.5.0', date: '2026-06-03', type: 'minor', description: '升级版本管理系统v3.0 + 云端同步支持', status: 'stable' }
    ];
}

function compareVersions(v1, v2) {
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

function getVersionChanges(version) {
    const changes = {
        '1.0.0': ['基础考试系统', '用户登录功能', '考试管理', '成绩统计'],
        '1.1.0': ['学习系统模块', '课程管理', '学习进度追踪'],
        '1.1.1': ['修复考试统计bug', '优化成绩计算'],
        '1.2.0': ['错题本功能', '错题收集', '错题练习'],
        '1.2.1': ['优化UI布局', '响应式设计'],
        '1.3.0': ['AI推荐功能', '个性化推荐'],
        '2.0.0': ['K12全学段支持', '小学/初中/高中', '成就系统基础'],
        '2.1.0': ['成就系统', '7种成就', '成就展示'],
        '2.1.1': ['修复升级通知bug', '优化通知显示'],
        '2.2.0': ['数据统计分析', '学习统计', '升级统计'],
        '2.3.0': ['考试过滤功能', '年级过滤', '科目过滤'],
        '3.0.0': ['AI能力集增强', '智能推荐', '自适应学习'],
        '3.1.0': ['智能推荐系统v3.0', '学习模式分析', '个性化推荐'],
        '3.1.1': ['优化推荐算法', '提升推荐准确率'],
        '3.2.0': ['自适应学习引擎v2.0', '知识图谱', '难度调整'],
        '3.3.0': ['优化权限系统', '教育类型管理'],
        '3.4.0': ['自动升级系统v2.0', 'AI能力集提升', '文档完善'],
        '3.5.0': ['版本管理系统v3.0', '云端同步支持', '版本对比增强', '自动备份', '版本统计报告']
    };
    return changes[version] || [];
}

router.get('/', (req, res) => {
    try {
        const content = getVersionFileContent();
        let versionInfo;
        
        if (content) {
            versionInfo = parseVersionFile(content);
        } else {
            versionInfo = {
                version: '1.0.0',
                buildDate: new Date().toISOString().split('T')[0],
                buildNumber: '0',
                features: []
            };
        }
        
        res.json({
            success: true,
            message: '获取版本信息成功',
            data: versionInfo,
            apiVersion: 'v3'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '获取版本信息失败',
            error: error.message
        });
    }
});

router.get('/history', (req, res) => {
    try {
        const versions = getAllVersions();
        
        res.json({
            success: true,
            message: '获取版本历史成功',
            data: versions,
            total: versions.length
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '获取版本历史失败',
            error: error.message
        });
    }
});

router.get('/compare', (req, res) => {
    try {
        const { v1, v2 } = req.query;
        
        if (!v1 || !v2) {
            return res.status(400).json({
                success: false,
                message: '缺少版本参数',
                error: '请提供 v1 和 v2 参数'
            });
        }
        
        const versions = getAllVersions();
        const version1 = versions.find(v => v.version === v1);
        const version2 = versions.find(v => v.version === v2);
        
        if (!version1 || !version2) {
            return res.status(404).json({
                success: false,
                message: '版本不存在',
                error: `版本 ${!version1 ? v1 : v2} 不存在`
            });
        }
        
        const comparison = compareVersions(v1, v2);
        let comparisonText;
        if (comparison > 0) {
            comparisonText = `${v1} 比 ${v2} 新`;
        } else if (comparison < 0) {
            comparisonText = `${v1} 比 ${v2} 旧`;
        } else {
            comparisonText = '两个版本相同';
        }
        
        const v1Parts = v1.split('.').map(Number);
        const v2Parts = v2.split('.').map(Number);
        
        const startVer = comparison < 0 ? v1 : v2;
        const endVer = comparison < 0 ? v2 : v1;
        
        const startIdx = versions.findIndex(v => v.version === startVer);
        const endIdx = versions.findIndex(v => v.version === endVer);
        
        const changesBetween = [];
        for (let i = startIdx + 1; i <= endIdx; i++) {
            const ver = versions[i];
            const changes = getVersionChanges(ver.version);
            changesBetween.push({
                version: ver.version,
                date: ver.date,
                type: ver.type,
                changes: changes
            });
        }
        
        res.json({
            success: true,
            message: '版本对比成功',
            data: {
                v1: version1,
                v2: version2,
                comparison: comparisonText,
                v1IsNewer: comparison > 0,
                v2IsNewer: comparison < 0,
                isEqual: comparison === 0,
                majorDiff: Math.abs(v1Parts[0] - v2Parts[0]),
                minorDiff: Math.abs(v1Parts[1] - v2Parts[1]),
                patchDiff: Math.abs(v1Parts[2] - v2Parts[2]),
                changesBetween: changesBetween,
                totalChanges: changesBetween.reduce((sum, item) => sum + item.changes.length, 0)
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '版本对比失败',
            error: error.message
        });
    }
});

router.get('/check-update', (req, res) => {
    try {
        const { currentVersion } = req.query;
        const versions = getAllVersions();
        const latestVersion = versions[versions.length - 1].version;
        
        let current = currentVersion;
        if (!current) {
            const content = getVersionFileContent();
            if (content) {
                const info = parseVersionFile(content);
                current = info.version;
            } else {
                current = '1.0.0';
            }
        }
        
        const comparison = compareVersions(latestVersion, current);
        const hasUpdate = comparison > 0;
        
        const newerVersions = versions.filter(v => compareVersions(v.version, current) > 0);
        
        res.json({
            success: true,
            message: '检查版本更新成功',
            data: {
                currentVersion: current,
                latestVersion: latestVersion,
                hasUpdate: hasUpdate,
                availableUpdates: newerVersions.length,
                updates: newerVersions,
                recommendedAction: hasUpdate ? 'upgrade' : 'none',
                criticalUpdates: newerVersions.filter(v => v.type === 'major')
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '检查版本更新失败',
            error: error.message
        });
    }
});

router.get('/statistics', (req, res) => {
    try {
        const versions = getAllVersions();
        const content = getVersionFileContent();
        let currentVersion = '1.0.0';
        
        if (content) {
            const info = parseVersionFile(content);
            currentVersion = info.version;
        }
        
        const majorCount = versions.filter(v => v.type === 'major').length;
        const minorCount = versions.filter(v => v.type === 'minor').length;
        const patchCount = versions.filter(v => v.type === 'patch').length;
        const stableCount = versions.filter(v => v.status === 'stable').length;
        
        let totalDays = 0;
        for (let i = 1; i < versions.length; i++) {
            const prevDate = new Date(versions[i-1].date);
            const currDate = new Date(versions[i].date);
            totalDays += (currDate - prevDate) / (1000 * 60 * 60 * 24);
        }
        const avgDays = versions.length > 1 ? (totalDays / (versions.length - 1)).toFixed(2) : '0';
        
        res.json({
            success: true,
            message: '获取版本统计成功',
            data: {
                totalVersions: versions.length,
                majorVersions: majorCount,
                minorVersions: minorCount,
                patchVersions: patchCount,
                stableVersions: stableCount,
                currentVersion: currentVersion,
                firstRelease: versions[0]?.date || null,
                lastRelease: versions[versions.length - 1]?.date || null,
                averageDaysBetweenReleases: avgDays,
                releaseChannels: ['main', 'beta', 'alpha'],
                currentChannel: 'main'
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '获取版本统计失败',
            error: error.message
        });
    }
});

router.get('/timeline', (req, res) => {
    try {
        const versions = getAllVersions();
        const content = getVersionFileContent();
        let currentVersion = '1.0.0';
        
        if (content) {
            const info = parseVersionFile(content);
            currentVersion = info.version;
        }
        
        const timeline = versions.map((v, index) => ({
            index: index,
            version: v.version,
            date: v.date,
            type: v.type,
            description: v.description,
            status: v.status,
            isCurrent: v.version === currentVersion
        }));
        
        const currentIndex = timeline.findIndex(t => t.isCurrent);
        
        res.json({
            success: true,
            message: '获取版本时间线成功',
            data: {
                timeline: timeline,
                currentIndex: currentIndex,
                totalVersions: versions.length,
                currentVersion: currentVersion
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '获取版本时间线失败',
            error: error.message
        });
    }
});

router.post('/simulate-upgrade', (req, res) => {
    try {
        const { targetVersion } = req.body;
        
        if (!targetVersion) {
            return res.status(400).json({
                success: false,
                message: '缺少目标版本参数',
                error: '请提供 targetVersion 参数'
            });
        }
        
        const versions = getAllVersions();
        const content = getVersionFileContent();
        let currentVersion = '1.0.0';
        
        if (content) {
            const info = parseVersionFile(content);
            currentVersion = info.version;
        }
        
        const targetInfo = versions.find(v => v.version === targetVersion);
        
        if (!targetInfo) {
            return res.status(404).json({
                success: false,
                message: '目标版本不存在',
                error: `版本 ${targetVersion} 不存在`
            });
        }
        
        const comparison = compareVersions(targetVersion, currentVersion);
        
        if (comparison <= 0) {
            return res.json({
                success: true,
                message: '模拟升级完成',
                data: {
                    simulationResult: 'no_upgrade_needed',
                    fromVersion: currentVersion,
                    toVersion: targetVersion,
                    message: '目标版本不高于当前版本，无需升级',
                    changes: [],
                    estimatedTime: '0分钟',
                    backupRequired: false,
                    rollbackPossible: true,
                    warnings: []
                }
            });
        }
        
        const startIdx = versions.findIndex(v => v.version === currentVersion);
        const endIdx = versions.findIndex(v => v.version === targetVersion);
        
        const allChanges = [];
        for (let i = startIdx + 1; i <= endIdx; i++) {
            const ver = versions[i];
            const changes = getVersionChanges(ver.version);
            allChanges.push(...changes);
        }
        
        res.json({
            success: true,
            message: '模拟升级完成',
            data: {
                simulationResult: 'success',
                fromVersion: currentVersion,
                toVersion: targetVersion,
                changes: allChanges,
                estimatedTime: `${allChanges.length * 5}分钟`,
                backupRequired: true,
                rollbackPossible: true,
                warnings: [],
                totalChanges: allChanges.length
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '模拟升级失败',
            error: error.message
        });
    }
});

router.get('/export', (req, res) => {
    try {
        const versions = getAllVersions();
        const content = getVersionFileContent();
        let versionInfo = { version: '1.0.0' };
        
        if (content) {
            versionInfo = parseVersionFile(content);
        }
        
        const exportData = {
            currentVersion: versionInfo.version,
            versionInfo: versionInfo,
            allVersions: versions,
            generatedAt: new Date().toISOString(),
            statistics: {
                totalVersions: versions.length,
                majorVersions: versions.filter(v => v.type === 'major').length,
                minorVersions: versions.filter(v => v.type === 'minor').length,
                patchVersions: versions.filter(v => v.type === 'patch').length
            }
        };
        
        const fileName = `version_export_${Date.now()}.json`;
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', `attachment; filename=${fileName}`);
        
        res.json(exportData);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '导出版本数据失败',
            error: error.message
        });
    }
});

router.get('/changelog/:version?', (req, res) => {
    try {
        const { version } = req.params;
        const versions = getAllVersions();
        
        if (version) {
            const versionInfo = versions.find(v => v.version === version);
            
            if (!versionInfo) {
                return res.status(404).json({
                    success: false,
                    message: '版本不存在',
                    error: `版本 ${version} 不存在`
                });
            }
            
            res.json({
                success: true,
                message: '获取版本变更日志成功',
                data: {
                    version: versionInfo.version,
                    date: versionInfo.date,
                    type: versionInfo.type,
                    status: versionInfo.status,
                    description: versionInfo.description,
                    changes: getVersionChanges(version)
                }
            });
        } else {
            const changelog = versions.reverse().map(v => ({
                version: v.version,
                date: v.date,
                type: v.type,
                status: v.status,
                description: v.description,
                changes: getVersionChanges(v.version)
            }));
            
            res.json({
                success: true,
                message: '获取所有版本变更日志成功',
                data: {
                    allVersions: changelog,
                    totalVersions: changelog.length
                }
            });
        }
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '获取变更日志失败',
            error: error.message
        });
    }
});

router.get('/components', (req, res) => {
    try {
        const content = getVersionFileContent();
        let components = {
            frontend: '1.0.0',
            backend: '1.0.0',
            database: '1.0.0',
            api: '1.0.0',
            aiEngine: '1.0.0'
        };
        
        if (content) {
            const info = parseVersionFile(content);
            components = {
                frontend: info.frontendVersion || '1.0.0',
                backend: info.backendVersion || '1.0.0',
                database: info.databaseVersion || '1.0.0',
                api: info.apiVersion || '1.0.0',
                aiEngine: info.aiEngineVersion || '1.0.0'
            };
        }
        
        res.json({
            success: true,
            message: '获取组件版本成功',
            data: components
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '获取组件版本失败',
            error: error.message
        });
    }
});

module.exports = router;
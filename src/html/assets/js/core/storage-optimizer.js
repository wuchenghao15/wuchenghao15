/**
 * MTSCOS AI System - 存储优化师AI员工
 * 版本: 4.4.0
 * 描述: 专注于存储空间优化、文件压缩、去重分析和磁盘健康监控
 */

class StorageOptimizer {
    constructor() {
        this.id = 'storage-optimizer';
        this.name = '存储优化师';
        this.icon = 'fa-hard-drive';
        this.color = '#8b5cf6';
        this.gradient = 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)';
        this.role = '存储优化专家';
        this.description = '专注于存储空间优化、文件压缩、去重分析和磁盘健康监控';
        this.abilities = [
            '空间优化',
            '文件压缩',
            '去重分析',
            '磁盘监控',
            '容量预测',
            '智能清理'
        ];
        this.status = 'active';
        this.workload = 15;
        this.efficiency = 98;
        this.optimizationHistory = [];
        this.diskStats = null;
    }

    // ==================== 存储分析 ====================

    // 分析存储
    analyzeStorage(config) {
        const analysis = {
            id: `analysis_${Date.now()}`,
            path: config.path || '/',
            timestamp: Date.now(),
            totalSpace: 500 * 1024 * 1024 * 1024, // 500GB
            usedSpace: 0,
            freeSpace: 0,
            usagePercent: 0,
            breakdown: this.analyzeBreakdown(),
            largeFiles: this.findLargeFiles(config),
            oldFiles: this.findOldFiles(config),
            duplicateFiles: this.findDuplicates(config),
            potentialSavings: 0
        };

        analysis.usedSpace = Math.floor(analysis.totalSpace * (Math.random() * 0.5 + 0.3));
        analysis.freeSpace = analysis.totalSpace - analysis.usedSpace;
        analysis.usagePercent = Math.round((analysis.usedSpace / analysis.totalSpace) * 100);
        analysis.potentialSavings = this.calculatePotentialSavings(analysis);

        this.diskStats = analysis;
        return analysis;
    }

    // 分析空间使用分布
    analyzeBreakdown() {
        return {
            byType: [
                { type: 'images', size: 50 * 1024 * 1024, count: 1200, percent: 30 },
                { type: 'videos', size: 120 * 1024 * 1024, count: 50, percent: 40 },
                { type: 'documents', size: 20 * 1024 * 1024, count: 500, percent: 15 },
                { type: 'archives', size: 15 * 1024 * 1024, count: 30, percent: 10 },
                { type: 'other', size: 5 * 1024 * 1024, count: 200, percent: 5 }
            ],
            byFolder: [
                { folder: '/documents', size: 30 * 1024 * 1024, percent: 25 },
                { folder: '/media', size: 150 * 1024 * 1024, percent: 45 },
                { folder: '/projects', size: 40 * 1024 * 1024, percent: 20 },
                { folder: '/other', size: 10 * 1024 * 1024, percent: 10 }
            ]
        };
    }

    // 查找大文件
    findLargeFiles(config) {
        const threshold = config.threshold || 100 * 1024 * 1024; // 100MB
        return [
            { path: '/videos/project_video.mp4', size: 2.5 * 1024 * 1024 * 1024, modified: Date.now() - 86400000 },
            { path: '/backups/backup_2024.zip', size: 5 * 1024 * 1024 * 1024, modified: Date.now() - 604800000 },
            { path: '/media/movie.mkv', size: 1.8 * 1024 * 1024 * 1024, modified: Date.now() - 2592000000 }
        ].filter(f => f.size >= threshold);
    }

    // 查找旧文件
    findOldFiles(config) {
        const age = config.age || 180 * 24 * 60 * 60 * 1000; // 180天
        const cutoff = Date.now() - age;
        return [
            { path: '/old_project.zip', size: 50 * 1024 * 1024, modified: cutoff - 86400000 },
            { path: '/temp/old_backup.tar', size: 100 * 1024 * 1024, modified: cutoff - 2592000000 }
        ];
    }

    // 查找重复文件
    findDuplicates(config) {
        return [
            {
                hash: 'abc123',
                files: [
                    { path: '/docs/report_v1.pdf', size: 5 * 1024 * 1024 },
                    { path: '/docs/report_final.pdf', size: 5 * 1024 * 1024 },
                    { path: '/backups/report.pdf', size: 5 * 1024 * 1024 }
                ],
                wastedSpace: 10 * 1024 * 1024
            },
            {
                hash: 'def456',
                files: [
                    { path: '/images/photo1.jpg', size: 3 * 1024 * 1024 },
                    { path: '/images/backup/photo1.jpg', size: 3 * 1024 * 1024 }
                ],
                wastedSpace: 3 * 1024 * 1024
            }
        ];
    }

    // 计算潜在节省空间
    calculatePotentialSavings(analysis) {
        const savings = {
            duplicates: analysis.duplicateFiles.reduce((sum, d) => sum + d.wastedSpace, 0),
            compressible: Math.floor(analysis.usedSpace * 0.15),
            oldFiles: analysis.oldFiles.reduce((sum, f) => sum + f.size, 0),
            total: 0
        };
        savings.total = savings.duplicates + savings.compressible + savings.oldFiles;
        return savings;
    }

    // ==================== 优化操作 ====================

    // 执行优化
    executeOptimization(config) {
        const optimization = {
            id: `opt_${Date.now()}`,
            actions: [],
            totalSaved: 0,
            startedAt: Date.now(),
            completedAt: null,
            status: 'running'
        };

        // 执行各项优化
        if (config.removeDuplicates) {
            const result = this.removeDuplicates(config.paths);
            optimization.actions.push(...result.actions);
            optimization.totalSaved += result.saved;
        }

        if (config.compressFiles) {
            const result = this.compressFiles(config.paths);
            optimization.actions.push(...result.actions);
            optimization.totalSaved += result.saved;
        }

        if (config.removeOldFiles) {
            const result = this.removeOldFiles(config.age);
            optimization.actions.push(...result.actions);
            optimization.totalSaved += result.saved;
        }

        optimization.status = 'completed';
        optimization.completedAt = Date.now();
        optimization.duration = optimization.completedAt - optimization.startedAt;

        this.optimizationHistory.push(optimization);
        return optimization;
    }

    // 删除重复文件
    removeDuplicates(paths) {
        const duplicates = this.findDuplicates({});
        const actions = [];
        let saved = 0;

        duplicates.forEach(group => {
            // 保留第一个，删除其余
            group.files.slice(1).forEach(file => {
                actions.push({
                    action: 'delete',
                    path: file.path,
                    reason: 'duplicate',
                    savedSpace: file.size
                });
                saved += file.size;
            });
        });

        return { actions, saved };
    }

    // 压缩文件
    compressFiles(paths) {
        return {
            actions: [
                { action: 'compress', path: '/archives/old_data.zip', originalSize: 100 * 1024 * 1024, compressedSize: 30 * 1024 * 1024 }
            ],
            saved: 70 * 1024 * 1024
        };
    }

    // 删除旧文件
    removeOldFiles(age) {
        const oldFiles = this.findOldFiles({ age });
        return {
            actions: oldFiles.map(f => ({
                action: 'delete',
                path: f.path,
                reason: 'old_file',
                savedSpace: f.size,
                lastModified: f.modified
            })),
            saved: oldFiles.reduce((sum, f) => sum + f.size, 0)
        };
    }

    // ==================== 文件压缩 ====================

    // 压缩文件
    compressFile(config) {
        const result = {
            source: config.path,
            destination: config.outputPath || config.path + '.gz',
            originalSize: 0,
            compressedSize: 0,
            ratio: 0,
            algorithm: config.algorithm || 'gzip',
            compressedAt: Date.now()
        };

        // 模拟压缩
        result.originalSize = 100 * 1024 * 1024;
        result.compressedSize = Math.floor(result.originalSize * (0.3 + Math.random() * 0.4));
        result.ratio = Math.round((result.compressedSize / result.originalSize) * 100);

        return result;
    }

    // 解压文件
    decompressFile(config) {
        return {
            source: config.path,
            destination: config.outputPath || config.path.replace(/\.(gz|zip|rar)$/, ''),
            decompressedAt: Date.now(),
            success: true
        };
    }

    // 批量压缩
    batchCompress(config) {
        const results = {
            files: [],
            totalOriginal: 0,
            totalCompressed: 0,
            completedAt: Date.now()
        };

        (config.paths || []).forEach(path => {
            const result = this.compressFile({ path });
            results.files.push(result);
            results.totalOriginal += result.originalSize;
            results.totalCompressed += result.compressedSize;
        });

        results.totalSaved = results.totalOriginal - results.totalCompressed;
        results.averageRatio = Math.round((results.totalCompressed / results.totalOriginal) * 100);

        return results;
    }

    // ==================== 磁盘监控 ====================

    // 监控磁盘健康
    monitorDiskHealth(config) {
        return {
            path: config.path || '/',
            checkedAt: Date.now(),
            health: {
                status: 'good', // good, warning, critical
                smart: {
                    reallocatedSectors: 0,
                    pendingSectors: 0,
                    uncorrectableSectors: 0
                }
            },
            temperature: 35 + Math.floor(Math.random() * 15),
            lifespan: {
                usedPercent: Math.floor(Math.random() * 50),
                estimatedYears: 5 + Math.floor(Math.random() * 5)
            },
            performance: {
                readSpeed: 500 + Math.floor(Math.random() * 500),
                writeSpeed: 300 + Math.floor(Math.random() * 400),
                iops: 10000 + Math.floor(Math.random() * 20000)
            },
            recommendations: this.generateRecommendations()
        };
    }

    // 生成建议
    generateRecommendations() {
        return [
            { priority: 'low', message: '磁盘健康状况良好' },
            { priority: 'medium', message: '建议每周运行一次磁盘检查' }
        ];
    }

    // 容量预测
    predictCapacity(config) {
        const usageHistory = [
            { date: new Date(Date.now() - 30 * 86400000).toISOString(), usage: 60 },
            { date: new Date(Date.now() - 20 * 86400000).toISOString(), usage: 62 },
            { date: new Date(Date.now() - 10 * 86400000).toISOString(), usage: 65 }
        ];

        const trend = this.calculateTrend(usageHistory);
        const daysUntilFull = this.estimateDaysUntilFull(trend);

        return {
            currentUsage: 68,
            dailyGrowth: trend,
            daysUntilFull,
            predictedDate: new Date(Date.now() + daysUntilFull * 86400000).toISOString(),
            recommendations: daysUntilFull < 30 
                ? [{ message: '存储空间即将用尽，请及时清理' }]
                : []
        };
    }

    // 计算增长趋势
    calculateTrend(history) {
        if (history.length < 2) return 0;
        const first = history[0].usage;
        const last = history[history.length - 1].usage;
        return (last - first) / history.length;
    }

    // 估算用完天数
    estimateDaysUntilFull(trend) {
        if (trend <= 0) return 999;
        const currentUsage = 68;
        return Math.floor((100 - currentUsage) / trend);
    }

    // ==================== 智能清理 ====================

    // 智能清理
    smartCleanup(config) {
        const cleanup = {
            id: `cleanup_${Date.now()}`,
            mode: config.mode || 'safe', // safe, moderate, aggressive
            executedAt: Date.now(),
            actions: [],
            totalSaved: 0,
            risk: 'low'
        };

        // 根据模式选择清理策略
        const strategies = {
            safe: [
                { type: 'temp_files', description: '临时文件', maxAge: 7 },
                { type: 'cache', description: '缓存文件', maxAge: 30 },
                { type: 'duplicates', description: '重复文件', keep: 1 }
            ],
            moderate: [
                { type: 'temp_files', description: '临时文件', maxAge: 1 },
                { type: 'cache', description: '缓存文件', maxAge: 7 },
                { type: 'logs', description: '旧日志', maxAge: 30 },
                { type: 'duplicates', description: '重复文件', keep: 1 }
            ],
            aggressive: [
                { type: 'temp_files', description: '临时文件', maxAge: 0 },
                { type: 'cache', description: '缓存文件', maxAge: 1 },
                { type: 'logs', description: '旧日志', maxAge: 7 },
                { type: 'old_backups', description: '旧备份', maxAge: 90 },
                { type: 'duplicates', description: '重复文件', keep: 1 }
            ]
        };

        cleanup.strategies = strategies[cleanup.mode];
        cleanup.estimatedSavings = Math.floor(Math.random() * 10) * 1024 * 1024 * 1024;

        return cleanup;
    }

    // 预览清理
    previewCleanup(config) {
        const preview = this.smartCleanup(config);
        preview.preview = true;
        preview.confirmRequired = true;
        return preview;
    }

    // 执行清理
    executeCleanup(cleanupId, config) {
        return {
            id: cleanupId,
            executed: true,
            executedAt: Date.now(),
            actions: [
                { type: 'temp_files', deleted: 150, saved: 500 * 1024 * 1024 },
                { type: 'cache', deleted: 300, saved: 2 * 1024 * 1024 * 1024 }
            ],
            totalSaved: 2.5 * 1024 * 1024 * 1024,
            errors: []
        };
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            totalOptimizations: this.optimizationHistory.length,
            totalSaved: this.optimizationHistory.reduce((sum, o) => sum + o.totalSaved, 0)
        };
    }

    getOptimizationHistory(limit = 10) {
        return this.optimizationHistory.slice(-limit).reverse();
    }

    formatSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    }
}

// 创建全局实例
window.storageOptimizer = new StorageOptimizer();

// 导出
window.MTSCOS_StorageOptimizer = StorageOptimizer;

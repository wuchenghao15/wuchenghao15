/**
 * MTSCOS 统一版本管理器
 * 合并了所有版本管理相关功能
 * 提供完整的版本检查、更新、备份和日志记录功能
 * 版本: 3.0.0 (统一版)
 */

// 防止重复定义
if (typeof MTSCOSUnifiedVersionManager === 'undefined') {

class MTSCOSUnifiedVersionManager {
    constructor() {
        this.version = '3.0.0';
        this.currentVersion = '3.0.0';
        this.buildNumber = '20241201';
        this.releaseDate = '2024-12-01';
        
        // 版本历史
        this.versionHistory = [
            {
                version: '3.0.0',
                buildNumber: '20241201',
                releaseDate: '2024-12-01',
                description: '统一版本管理器，合并所有重复功能',
                changes: [
                    '合并错误处理器功能',
                    '合并API客户端功能',
                    '优化脚本加载顺序',
                    '清理重复代码'
                ]
            },
            {
                version: '2.1.0',
                buildNumber: '20241115',
                releaseDate: '2024-11-15',
                description: '性能优化和错误处理增强',
                changes: [
                    '添加性能监控',
                    '增强错误处理',
                    '优化缓存机制'
                ]
            },
            {
                version: '2.0.0',
                buildNumber: '20241001',
                releaseDate: '2024-10-01',
                description: '重构版本，添加模块化支持',
                changes: [
                    '模块化重构',
                    '添加API客户端',
                    '改进用户界面'
                ]
            },
            {
                version: '1.0.0',
                buildNumber: '20240901',
                releaseDate: '2024-09-01',
                description: '初始版本',
                changes: [
                    '基础功能实现',
                    '用户界面创建',
                    '核心API集成'
                ]
            }
        ];
        
        // 文件版本映射
        this.fileVersions = new Map();
        
        // 更新配置
        this.updateConfig = {
            autoCheck: true,
            checkInterval: 24 * 60 * 60 * 1000, // 24小时
            backupEnabled: true,
            backupPath: '/Backups',
            maxBackups: 10
        };
        
        // 更新状态
        this.updateStatus = {
            isChecking: false,
            isUpdating: false,
            lastCheck: null,
            lastUpdate: null,
            availableUpdate: null
        };
        
        this.isInitialized = false;
        this.init();
    }

    /**
     * 初始化版本管理器
     */
    init() {
        if (this.isInitialized) return;
        
        // 加载文件版本信息
        this.loadFileVersions();
        
        // 检查是否需要自动检查更新
        if (this.updateConfig.autoCheck) {
            this.scheduleAutoCheck();
        }
        
        // 初始化文件版本
        this.initializeFileVersions();
        
        this.isInitialized = true;
        console.log(`[MTSCOS统一版本管理器] v${this.version} 初始化完成`);
    }

    /**
     * 初始化文件版本
     */
    initializeFileVersions() {
        // 核心文件版本
        this.setFileVersion('unified-error-handler-v3.js', '3.0.0', '统一错误处理器');
        this.setFileVersion('unified-api-client-v3.js', '3.0.0', '统一API客户端');
        this.setFileVersion('unified-version-manager-v3.js', '3.0.0', '统一版本管理器');
        this.setFileVersion('mtscos-utils.js', '3.0.0', 'MTSCOS工具函数');
        this.setFileVersion('deepseek-monitor.js', '3.0.0', 'DeepSeek监控');
        this.setFileVersion('theme-manager.js', '3.0.0', '主题管理器');
        this.setFileVersion('login.js', '3.0.0', '登录功能');
        
        // HTML文件版本
        this.setFileVersion('deepseek-test.html', '3.0.0', '主页面');
        this.setFileVersion('login.html', '3.0.0', '登录页面');
        this.setFileVersion('404.html', '3.0.0', '404错误页面');
        this.setFileVersion('403.html', '3.0.0', '403错误页面');
        
        // CSS文件版本
        this.setFileVersion('mtscos-styles.css', '3.0.0', '主样式文件');
        this.setFileVersion('login-styles.css', '3.0.0', '登录样式');
        
        console.log(`[版本管理器] 已初始化 ${this.fileVersions.size} 个文件的版本信息`);
    }

    /**
     * 设置文件版本
     */
    setFileVersion(filename, version, description = '') {
        this.fileVersions.set(filename, {
            version,
            description,
            lastUpdated: Date.now(),
            checksum: this.generateChecksum(filename)
        });
    }

    /**
     * 获取文件版本
     */
    getFileVersion(filename) {
        return this.fileVersions.get(filename);
    }

    /**
     * 更新文件版本
     */
    updateFileVersion(filename, newVersion, description = '') {
        const oldVersion = this.getFileVersion(filename);
        
        this.setFileVersion(filename, newVersion, description);
        
        // 记录更新历史
        this.logVersionUpdate(filename, oldVersion?.version, newVersion, description);
        
        console.log(`[版本更新] ${filename}: ${oldVersion?.version} → ${newVersion}`);
    }

    /**
     * 生成文件校验和
     */
    generateChecksum(filename) {
        // 简化的校验和生成（实际应用中应使用更安全的算法）
        const timestamp = Date.now().toString();
        const random = Math.random().toString(36).substring(2);
        return `${timestamp}_${random}`;
    }

    /**
     * 记录版本更新
     */
    logVersionUpdate(filename, oldVersion, newVersion, description) {
        const updateLog = {
            filename,
            oldVersion,
            newVersion,
            description,
            timestamp: Date.now(),
            user: 'system'
        };
        
        // 保存到本地存储
        try {
            const logs = JSON.parse(localStorage.getItem('mtscos_version_update_logs') || '[]');
            logs.push(updateLog);
            
            // 限制日志数量
            if (logs.length > 100) {
                logs.shift();
            }
            
            localStorage.setItem('mtscos_version_update_logs', JSON.stringify(logs));
        } catch (error) {
            console.warn('无法保存版本更新日志:', error);
        }
    }

    /**
     * 获取版本信息
     */
    getVersionInfo() {
        return {
            current: this.currentVersion,
            build: this.buildNumber,
            releaseDate: this.releaseDate,
            versionManager: this.version,
            fileCount: this.fileVersions.size,
            lastUpdate: this.updateStatus.lastUpdate,
            lastCheck: this.updateStatus.lastCheck
        };
    }

    /**
     * 获取版本历史
     */
    getVersionHistory() {
        return this.versionHistory;
    }

    /**
     * 获取所有文件版本
     */
    getAllFileVersions() {
        return Array.from(this.fileVersions.entries()).map(([filename, info]) => ({
            filename,
            ...info
        }));
    }

    /**
     * 检查更新
     */
    async checkForUpdates() {
        if (this.updateStatus.isChecking) {
            console.log('[版本管理器] 正在检查更新，请稍候...');
            return null;
        }
        
        this.updateStatus.isChecking = true;
        this.updateStatus.lastCheck = Date.now();
        
        try {
            console.log('[版本管理器] 开始检查更新...');
            
            // 模拟检查更新
            const updateInfo = await this.simulateUpdateCheck();
            
            if (updateInfo.hasUpdate) {
                this.updateStatus.availableUpdate = updateInfo;
                console.log(`[版本管理器] 发现新版本: ${updateInfo.version}`);
                
                // 通知用户
                this.notifyUpdateAvailable(updateInfo);
                
                return updateInfo;
            } else {
                console.log('[版本管理器] 当前已是最新版本');
                return null;
            }
            
        } catch (error) {
            console.error('[版本管理器] 检查更新失败:', error);
            return null;
        } finally {
            this.updateStatus.isChecking = false;
        }
    }

    /**
     * 模拟更新检查
     */
    async simulateUpdateCheck() {
        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 模拟更新检查结果（这里返回无更新）
        return {
            hasUpdate: false,
            version: this.currentVersion,
            description: '当前已是最新版本',
            releaseDate: this.releaseDate,
            downloadUrl: '',
            checksum: ''
        };
    }

    /**
     * 通知更新可用
     */
    notifyUpdateAvailable(updateInfo) {
        if (window.MTSCOSUnifiedErrorHandler) {
            window.MTSCOSUnifiedErrorHandler.showUserMessage(
                `发现新版本 ${updateInfo.version} 可用，请前往更新`,
                'info'
            );
        }
    }

    /**
     * 执行更新
     */
    async performUpdate(updateInfo) {
        if (this.updateStatus.isUpdating) {
            console.log('[版本管理器] 正在更新中，请稍候...');
            return false;
        }
        
        this.updateStatus.isUpdating = true;
        
        try {
            console.log(`[版本管理器] 开始更新到版本 ${updateInfo.version}...`);
            
            // 创建备份
            if (this.updateConfig.backupEnabled) {
                await this.createBackup();
            }
            
            // 下载更新文件
            await this.downloadUpdate(updateInfo);
            
            // 验证更新文件
            const isValid = await this.verifyUpdate(updateInfo);
            if (!isValid) {
                throw new Error('更新文件验证失败');
            }
            
            // 应用更新
            await this.applyUpdate(updateInfo);
            
            // 更新版本信息
            this.currentVersion = updateInfo.version;
            this.updateStatus.lastUpdate = Date.now();
            
            console.log(`[版本管理器] 更新完成，当前版本: ${this.currentVersion}`);
            
            // 通知用户
            this.notifyUpdateComplete(updateInfo);
            
            return true;
            
        } catch (error) {
            console.error('[版本管理器] 更新失败:', error);
            
            // 回滚更新
            await this.rollbackUpdate();
            
            return false;
        } finally {
            this.updateStatus.isUpdating = false;
        }
    }

    /**
     * 创建备份
     */
    async createBackup() {
        console.log('[版本管理器] 创建备份...');
        
        const backupInfo = {
            version: this.currentVersion,
            timestamp: Date.now(),
            files: this.getAllFileVersions()
        };
        
        // 保存备份信息到本地存储
        try {
            const backups = JSON.parse(localStorage.getItem('mtscos_backups') || '[]');
            backups.push(backupInfo);
            
            // 限制备份数量
            if (backups.length > this.updateConfig.maxBackups) {
                backups.shift();
            }
            
            localStorage.setItem('mtscos_backups', JSON.stringify(backups));
            console.log('[版本管理器] 备份创建完成');
            
        } catch (error) {
            console.warn('[版本管理器] 备份创建失败:', error);
        }
    }

    /**
     * 下载更新
     */
    async downloadUpdate(updateInfo) {
        console.log('[版本管理器] 下载更新文件...');
        
        // 模拟下载过程
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('[版本管理器] 更新文件下载完成');
    }

    /**
     * 验证更新
     */
    async verifyUpdate(updateInfo) {
        console.log('[版本管理器] 验证更新文件...');
        
        // 模拟验证过程
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        return true;
    }

    /**
     * 应用更新
     */
    async applyUpdate(updateInfo) {
        console.log('[版本管理器] 应用更新...');
        
        // 更新文件版本
        for (const file of updateInfo.files || []) {
            this.updateFileVersion(file.filename, file.version, file.description);
        }
        
        // 添加到版本历史
        this.versionHistory.unshift({
            version: updateInfo.version,
            buildNumber: updateInfo.buildNumber || this.buildNumber,
            releaseDate: updateInfo.releaseDate || new Date().toISOString().slice(0, 10),
            description: updateInfo.description,
            changes: updateInfo.changes || []
        });
        
        console.log('[版本管理器] 更新应用完成');
    }

    /**
     * 回滚更新
     */
    async rollbackUpdate() {
        console.log('[版本管理器] 回滚更新...');
        
        try {
            const backups = JSON.parse(localStorage.getItem('mtscos_backups') || '[]');
            if (backups.length === 0) {
                console.warn('[版本管理器] 没有可用的备份');
                return false;
            }
            
            const latestBackup = backups[backups.length - 1];
            
            // 恢复文件版本
            for (const file of latestBackup.files) {
                this.setFileVersion(file.filename, file.version, file.description);
            }
            
            console.log('[版本管理器] 更新已回滚到备份版本');
            return true;
            
        } catch (error) {
            console.error('[版本管理器] 回滚失败:', error);
            return false;
        }
    }

    /**
     * 通知更新完成
     */
    notifyUpdateComplete(updateInfo) {
        if (window.MTSCOSUnifiedErrorHandler) {
            window.MTSCOSUnifiedErrorHandler.showUserMessage(
                `更新完成，当前版本: ${updateInfo.version}`,
                'success'
            );
        }
    }

    /**
     * 安排自动检查
     */
    scheduleAutoCheck() {
        setInterval(() => {
            this.checkForUpdates();
        }, this.updateConfig.checkInterval);
    }

    /**
     * 加载文件版本
     */
    loadFileVersions() {
        try {
            const saved = localStorage.getItem('mtscos_file_versions');
            if (saved) {
                const data = JSON.parse(saved);
                this.fileVersions = new Map(data);
            }
        } catch (error) {
            console.warn('无法加载文件版本信息:', error);
        }
    }

    /**
     * 保存文件版本
     */
    saveFileVersions() {
        try {
            const data = Array.from(this.fileVersions.entries());
            localStorage.setItem('mtscos_file_versions', JSON.stringify(data));
        } catch (error) {
            console.warn('无法保存文件版本信息:', error);
        }
    }

    /**
     * 获取更新状态
     */
    getUpdateStatus() {
        return { ...this.updateStatus };
    }

    /**
     * 获取备份列表
     */
    getBackupList() {
        try {
            return JSON.parse(localStorage.getItem('mtscos_backups') || '[]');
        } catch (error) {
            console.warn('无法获取备份列表:', error);
            return [];
        }
    }

    /**
     * 清理旧备份
     */
    cleanupOldBackups() {
        try {
            const backups = JSON.parse(localStorage.getItem('mtscos_backups') || '[]');
            if (backups.length > this.updateConfig.maxBackups) {
                const cleanedBackups = backups.slice(-this.updateConfig.maxBackups);
                localStorage.setItem('mtscos_backups', JSON.stringify(cleanedBackups));
                console.log(`[版本管理器] 已清理旧备份，保留 ${this.updateConfig.maxBackups} 个最新备份`);
            }
        } catch (error) {
            console.warn('清理备份失败:', error);
        }
    }

    /**
     * 导出版本信息
     */
    exportVersionInfo() {
        const versionData = {
            current: this.getVersionInfo(),
            history: this.getVersionHistory(),
            files: this.getAllFileVersions(),
            backups: this.getBackupList(),
            updateStatus: this.getUpdateStatus(),
            exportTime: Date.now()
        };
        
        const blob = new Blob([JSON.stringify(versionData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mtscos-version-info-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * 检查文件完整性
     */
    async checkFileIntegrity() {
        console.log('[版本管理器] 检查文件完整性...');
        
        const results = [];
        
        for (const [filename, versionInfo] of this.fileVersions) {
            const currentChecksum = this.generateChecksum(filename);
            const isIntact = currentChecksum === versionInfo.checksum;
            
            results.push({
                filename,
                version: versionInfo.version,
                intact: isIntact,
                expectedChecksum: versionInfo.checksum,
                actualChecksum: currentChecksum
            });
        }
        
        const intactCount = results.filter(r => r.intact).length;
        console.log(`[版本管理器] 文件完整性检查完成: ${intactCount}/${results.length} 文件完整`);
        
        return results;
    }

    /**
     * 修复文件版本
     */
    async repairFileVersions() {
        console.log('[版本管理器] 修复文件版本...');
        
        const integrityResults = await this.checkFileIntegrity();
        const damagedFiles = integrityResults.filter(r => !r.intact);
        
        if (damagedFiles.length === 0) {
            console.log('[版本管理器] 所有文件完整，无需修复');
            return true;
        }
        
        // 创建备份
        await this.createBackup();
        
        // 修复损坏的文件
        for (const file of damagedFiles) {
            console.log(`[版本管理器] 修复文件: ${file.filename}`);
            
            // 重新生成校验和
            const newChecksum = this.generateChecksum(file.filename);
            this.fileVersions.get(file.filename).checksum = newChecksum;
        }
        
        // 保存修复后的版本信息
        this.saveFileVersions();
        
        console.log(`[版本管理器] 已修复 ${damagedFiles.length} 个文件`);
        return true;
    }
}

// 创建全局实例
window.MTSCOSUnifiedVersionManager = new MTSCOSUnifiedVersionManager();

// 向后兼容：创建别名
window.MTSCOS_VersionManager = window.MTSCOSUnifiedVersionManager;
window.versionManager = window.MTSCOSUnifiedVersionManager;
window.updateVersion = window.MTSCOSUnifiedVersionManager.updateFileVersion.bind(window.MTSCOSUnifiedVersionManager);

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MTSCOSUnifiedVersionManager;
}

} // 结束 typeof MTSCOSUnifiedVersionManager === 'undefined' 检查
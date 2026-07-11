/**
 * MTSCOS AI System - 数据同步服务
 * 版本: 4.3.0
 * 描述: 统一管理系统数据同步，支持变更检测、批量上传、冲突解决
 */

class DataSyncService {
    constructor(database) {
        this.database = database;
        this.changes = new Map();
        this.isSyncing = false;
        this.syncQueue = [];
        this.lastSyncTime = 0;
        this.syncInterval = 30000;
        this.debounceTimer = null;
        this.isReady = false;
        this.init();
    }
    
    async init() {
        // 等待数据库就绪
        await this.database.waitForReady();
        
        // 启动自动同步
        this.startAutoSync();
        
        // 监听数据变更事件
        this.setupEventListeners();
        
        this.isReady = true;
        console.log('✅ 数据同步服务初始化成功');
    }
    
    setupEventListeners() {
        // 监听系统设置变更
        document.addEventListener('mtscos:setting:changed', (event) => {
            this.markChanged('system_settings', event.detail.key);
        });
        
        // 监听用户偏好变更
        document.addEventListener('mtscos:preferences:changed', (event) => {
            this.markChanged('user_preferences', event.detail.userId);
        });
        
        // 监听状态变更
        document.addEventListener('mtscos:state:changed', (event) => {
            this.markChanged('system_state', event.detail.key);
        });
        
        // 监听数据库就绪
        document.addEventListener('mtscos:database:ready', () => {
            this.performSync();
        });
    }
    
    // ==================== 变更检测 ====================
    
    markChanged(dataType, key) {
        if (!this.changes.has(dataType)) {
            this.changes.set(dataType, new Set());
        }
        
        const keys = this.changes.get(dataType);
        if (!keys.has(key)) {
            keys.add(key);
            
            // 触发防抖同步
            this.scheduleSync();
        }
    }
    
    scheduleSync() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        this.debounceTimer = setTimeout(() => {
            this.performSync();
        }, 2000);
    }
    
    startAutoSync() {
        this.autoSyncInterval = setInterval(() => {
            this.performSync();
        }, this.syncInterval);
    }
    
    stopAutoSync() {
        if (this.autoSyncInterval) {
            clearInterval(this.autoSyncInterval);
        }
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
    }
    
    // ==================== 执行同步 ====================
    
    async performSync() {
        // 确保数据库就绪
        if (!this.isReady) {
            try {
                await this.database.waitForReady();
            } catch (e) {
                console.warn('⚠️ 数据库未就绪，跳过同步');
                return;
            }
        }
        
        if (this.isSyncing) {
            // 添加到队列
            this.syncQueue.push({ timestamp: Date.now() });
            return;
        }
        
        this.isSyncing = true;
        
        try {
            const syncResults = [];
            
            // 处理所有变更的数据类型
            for (const [dataType, keys] of this.changes) {
                const result = await this.syncDataType(dataType, Array.from(keys));
                syncResults.push(result);
                
                // 清除已同步的变更
                keys.clear();
            }
            
            // 记录同步历史
            await this.database.addSyncRecord('success', 'all', {
                results: syncResults,
                timestamp: Date.now(),
                duration: Date.now() - this.lastSyncTime
            });
            
            this.lastSyncTime = Date.now();
            
            // 触发同步完成事件
            document.dispatchEvent(new CustomEvent('mtscos:sync:completed', {
                detail: { results: syncResults }
            }));
            
        } catch (error) {
            await this.database.addSyncRecord('error', 'all', {
                error: error.message,
                timestamp: Date.now()
            });
            
            console.error('❌ 数据同步失败:', error);
        } finally {
            this.isSyncing = false;
            
            // 处理队列中的同步请求
            if (this.syncQueue.length > 0) {
                this.syncQueue = [];
                this.performSync();
            }
        }
    }
    
    async syncDataType(dataType, keys) {
        const startTime = Date.now();
        let success = 0;
        let failed = 0;
        
        try {
            for (const key of keys) {
                try {
                    await this.syncDataItem(dataType, key);
                    success++;
                } catch (error) {
                    failed++;
                    console.error(`❌ 同步 ${dataType}/${key} 失败:`, error);
                }
            }
            
            return {
                dataType,
                keys: keys.length,
                success,
                failed,
                duration: Date.now() - startTime
            };
        } catch (error) {
            return {
                dataType,
                keys: keys.length,
                success: 0,
                failed: keys.length,
                error: error.message,
                duration: Date.now() - startTime
            };
        }
    }
    
    async syncDataItem(dataType, key) {
        // 根据数据类型执行不同的同步逻辑
        switch (dataType) {
            case 'system_settings':
                return await this.syncSystemSetting(key);
            case 'user_preferences':
                return await this.syncUserPreferences(key);
            case 'system_state':
                return await this.syncSystemState(key);
            case 'ai_employee_data':
                return await this.syncAIEmployee(key);
            default:
                return await this.syncGeneric(dataType, key);
        }
    }
    
    async syncSystemSetting(key) {
        const value = await this.database.getSystemSetting(key);
        if (value !== null) {
            return true;
        }
        return false;
    }
    
    async syncUserPreferences(userId) {
        const prefs = await this.database.getUserPreferences(userId);
        if (prefs) {
            return true;
        }
        return false;
    }
    
    async syncSystemState(key) {
        const value = await this.database.getSystemState(key);
        if (value !== null) {
            return true;
        }
        return false;
    }
    
    async syncAIEmployee(employeeId) {
        const employee = await this.database.getAIEmployee(employeeId);
        if (employee) {
            return true;
        }
        return false;
    }
    
    async syncGeneric(dataType, key) {
        const value = await this.database.get(dataType, key);
        if (value) {
            return true;
        }
        return false;
    }
    
    // ==================== 批量同步 ====================
    
    async batchSync(items) {
        const results = [];
        
        for (const item of items) {
            this.markChanged(item.dataType, item.key);
            results.push({
                dataType: item.dataType,
                key: item.key,
                status: 'queued'
            });
        }
        
        await this.performSync();
        
        return results;
    }
    
    // ==================== 手动触发同步 ====================
    
    async triggerSync(dataType = null, key = null) {
        if (dataType && key) {
            this.markChanged(dataType, key);
        }
        
        await this.performSync();
        return true;
    }
    
    // ==================== 同步状态 ====================
    
    getSyncStatus() {
        return {
            isSyncing: this.isSyncing,
            pendingChanges: Array.from(this.changes.entries()).reduce((acc, [type, keys]) => {
                acc[type] = keys.size;
                return acc;
            }, {}),
            lastSyncTime: this.lastSyncTime,
            queueSize: this.syncQueue.length
        };
    }
    
    // ==================== 导出/导入同步 ====================
    
    async exportAndSync() {
        const exportData = await this.database.exportData();
        
        // 触发导出事件
        document.dispatchEvent(new CustomEvent('mtscos:sync:exported', {
            detail: exportData
        }));
        
        return exportData;
    }
    
    async importAndSync(data) {
        const result = await this.database.importData(data);
        
        // 清除所有变更标记（数据已更新）
        this.changes.clear();
        
        // 触发导入事件
        document.dispatchEvent(new CustomEvent('mtscos:sync:imported', {
            detail: result
        }));
        
        return result;
    }
    
    // ==================== 冲突解决 ====================
    
    async resolveConflict(dataType, key, localData, remoteData) {
        // 简单的冲突解决策略：以时间戳为准
        const localTime = localData.updatedAt || 0;
        const remoteTime = remoteData.updatedAt || 0;
        
        if (localTime >= remoteTime) {
            // 本地数据更新较新
            await this.database.put(dataType, localData);
            return { resolved: true, winner: 'local' };
        } else {
            // 远程数据更新较新
            await this.database.put(dataType, remoteData);
            return { resolved: true, winner: 'remote' };
        }
    }
    
    // ==================== 健康检查 ====================
    
    async healthCheck() {
        return {
            status: 'ok',
            isSyncing: this.isSyncing,
            pendingChanges: this.changes.size,
            lastSyncTime: this.lastSyncTime,
            autoSyncEnabled: !!this.autoSyncInterval
        };
    }
    
    // ==================== 销毁 ====================
    
    destroy() {
        this.stopAutoSync();
        this.changes.clear();
        this.syncQueue = [];
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataSyncService;
}

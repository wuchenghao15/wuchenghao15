/**
 * 数据库备份管理系统
 * 提供自动备份、手动备份、恢复和配置持久化功能
 */

class DatabaseBackupManager {
    constructor() {
        this.backupConfig = {
            autoBackup: true,
            interval: 24, // 小时
            retention: 30, // 天
            maxBackups: 30,
            compression: true,
            encryption: true,
            remoteBackup: false,
            remotePath: '',
            encryptionKey: null
        };

        this.backupHistory = [];
        this.isBackupInProgress = false;
        this.backupTimer = null;
        this.encryptionKey = null;

        // 数据库配置
        this.dbConfig = {
            name: 'MTSCOS_Backup',
            version: 1,
            stores: ['backups', 'config', 'schedule']
        };

        this.listeners = new Map();
        this.isInitialized = false;
    }

    /**
     * 初始化备份管理器
     */
    async initialize() {
        try {
            console.log('初始化数据库备份管理器...');
            
            // 初始化数据库
            await this.initDatabase();
            
            // 加载配置
            await this.loadConfig();
            
            // 生成或加载加密密钥
            await this.initEncryption();
            
            // 设置自动备份
            this.setupAutoBackup();
            
            // 清理过期备份
            await this.cleanupExpiredBackups();
            
            this.isInitialized = true;
            console.log('数据库备份管理器初始化完成');
            
            return true;
        } catch (error) {
            console.error('初始化备份管理器失败:', error);
            return false;
        }
    }

    /**
     * 初始化数据库
     */
    async initDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbConfig.name, this.dbConfig.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // 创建备份存储
                if (!db.objectStoreNames.contains('backups')) {
                    const backupStore = db.createObjectStore('backups', { keyPath: 'id' });
                    backupStore.createIndex('timestamp', 'timestamp', { unique: false });
                    backupStore.createIndex('type', 'type', { unique: false });
                    backupStore.createIndex('size', 'size', { unique: false });
                }

                // 创建配置存储
                if (!db.objectStoreNames.contains('config')) {
                    db.createObjectStore('config', { keyPath: 'key' });
                }

                // 创建调度存储
                if (!db.objectStoreNames.contains('schedule')) {
                    const scheduleStore = db.createObjectStore('schedule', { keyPath: 'id' });
                    scheduleStore.createIndex('nextRun', 'nextRun', { unique: false });
                }
            };
        });
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            const config = await this.getFromDB('config', 'backup_config');
            if (config) {
                this.backupConfig = { ...this.backupConfig, ...config.value };
            }

            // 从系统设置加载配置
            if (window.systemSettings) {
                const systemConfig = window.systemSettings.get('backup', '');
                if (systemConfig) {
                    this.backupConfig = { ...this.backupConfig, ...systemConfig };
                }
            }

            console.log('备份配置加载完成:', this.backupConfig);
        } catch (error) {
            console.error('加载备份配置失败:', error);
        }
    }

    /**
     * 初始化加密
     */
    async initEncryption() {
        try {
            // 尝试从localStorage加载密钥
            let storedKey = localStorage.getItem('backup_encryption_key');
            
            if (!storedKey) {
                // 生成新密钥
                storedKey = await this.generateEncryptionKey();
                localStorage.setItem('backup_encryption_key', storedKey);
            }

            this.encryptionKey = storedKey;
            console.log('加密密钥初始化完成');
        } catch (error) {
            console.error('初始化加密失败:', error);
            this.backupConfig.encryption = false;
        }
    }

    /**
     * 生成加密密钥
     */
    async generateEncryptionKey() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    /**
     * 设置自动备份
     */
    setupAutoBackup() {
        if (this.backupConfig.autoBackup) {
            const intervalMs = this.backupConfig.interval * 60 * 60 * 1000;
            
            // 清除现有定时器
            if (this.backupTimer) {
                clearInterval(this.backupTimer);
            }

            // 设置新定时器
            this.backupTimer = setInterval(async () => {
                try {
                    await this.createAutoBackup();
                } catch (error) {
                    console.error('自动备份失败:', error);
                    this.emitEvent('autoBackupError', error);
                }
            }, intervalMs);

            console.log(`自动备份已设置，间隔: ${this.backupConfig.interval}小时`);
        }
    }

    /**
     * 创建备份
     */
    async createBackup(options = {}) {
        if (this.isBackupInProgress) {
            throw new Error('备份正在进行中，请稍后再试');
        }

        this.isBackupInProgress = true;
        
        try {
            console.log('开始创建数据库备份...');
            
            const backupId = this.generateBackupId();
            const timestamp = new Date().toISOString();
            
            // 收集所有数据库数据
            const databaseData = await this.collectDatabaseData();
            
            // 收集配置数据
            const configData = await this.collectConfigData();
            
            // 构建备份数据
            const backupData = {
                id: backupId,
                timestamp: timestamp,
                type: options.type || 'manual',
                description: options.description || '',
                version: '1.0.0',
                database: databaseData,
                config: configData,
                metadata: {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language,
                    backupSize: 0
                }
            };

            // 序列化数据
            const serializedData = JSON.stringify(backupData);
            backupData.metadata.backupSize = serializedData.length;

            // 压缩数据
            let processedData = serializedData;
            if (this.backupConfig.compression) {
                processedData = await this.compressData(serializedData);
                backupData.compressed = true;
            }

            // 加密数据
            if (this.backupConfig.encryption && this.encryptionKey) {
                processedData = await this.encryptData(processedData);
                backupData.encrypted = true;
            }

            // 保存备份
            const backupRecord = {
                id: backupId,
                timestamp: timestamp,
                type: backupData.type,
                description: backupData.description,
                size: backupData.metadata.backupSize,
                compressed: backupData.compressed || false,
                encrypted: backupData.encrypted || false,
                data: processedData
            };

            await this.saveToDB('backups', backupRecord);
            
            // 添加到历史记录
            this.backupHistory.unshift(backupRecord);
            
            // 远程备份
            if (this.backupConfig.remoteBackup) {
                try {
                    await this.uploadToRemote(backupRecord);
                } catch (error) {
                    console.warn('远程备份失败:', error);
                }
            }

            this.emitEvent('backupCreated', backupRecord);
            console.log('备份创建完成:', backupId);
            
            return backupRecord;
        } catch (error) {
            console.error('创建备份失败:', error);
            this.emitEvent('backupError', error);
            throw error;
        } finally {
            this.isBackupInProgress = false;
        }
    }

    /**
     * 创建自动备份
     */
    async createAutoBackup() {
        return await this.createBackup({
            type: 'auto',
            description: `自动备份 - ${new Date().toLocaleString()}`
        });
    }

    /**
     * 收集数据库数据
     */
    async collectDatabaseData() {
        const databases = ['MTSCOS_Database', 'MTSCOS_Users', 'MTSCOS_Logs'];
        const databaseData = {};

        for (const dbName of databases) {
            try {
                databaseData[dbName] = await this.exportDatabase(dbName);
            } catch (error) {
                console.warn(`导出数据库 ${dbName} 失败:`, error);
                databaseData[dbName] = { error: error.message };
            }
        }

        return databaseData;
    }

    /**
     * 导出数据库
     */
    async exportDatabase(dbName) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(dbName);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const exportData = {};

                // 导出所有对象存储
                for (const storeName of db.objectStoreNames) {
                    const transaction = db.transaction(storeName, 'readonly');
                    const store = transaction.objectStore(storeName);
                    const data = [];

                    const cursorRequest = store.openCursor();
                    cursorRequest.onsuccess = (event) => {
                        const cursor = event.target.result;
                        if (cursor) {
                            data.push(cursor.value);
                            cursor.continue();
                        } else {
                            exportData[storeName] = data;
                        }
                    };
                }

                // 等待所有事务完成
                db.close();
                setTimeout(() => resolve(exportData), 100);
            };
        });
    }

    /**
     * 收集配置数据
     */
    async collectConfigData() {
        const configData = {};

        // 系统设置
        if (window.systemSettings) {
            configData.systemSettings = window.systemSettings.settings;
        }

        // 本地存储配置
        const localStorageConfig = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && !key.includes('password') && !key.includes('token')) {
                localStorageConfig[key] = localStorage.getItem(key);
            }
        }
        configData.localStorage = localStorageConfig;

        // 会话存储配置
        const sessionStorageConfig = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key && !key.includes('password') && !key.includes('token')) {
                sessionStorageConfig[key] = sessionStorage.getItem(key);
            }
        }
        configData.sessionStorage = sessionStorageConfig;

        return configData;
    }

    /**
     * 压缩数据
     */
    async compressData(data) {
        try {
            // 使用简单的压缩算法（实际项目中可以使用更高效的压缩库）
            const compressed = btoa(encodeURIComponent(data));
            return compressed;
        } catch (error) {
            console.warn('数据压缩失败，使用原始数据:', error);
            return data;
        }
    }

    /**
     * 解压数据
     */
    async decompressData(compressedData) {
        try {
            const decompressed = decodeURIComponent(atob(compressedData));
            return decompressed;
        } catch (error) {
            console.warn('数据解压失败，返回原始数据:', error);
            return compressedData;
        }
    }

    /**
     * 加密数据
     */
    async encryptData(data) {
        try {
            // 简单的XOR加密（实际项目中应使用更强的加密算法）
            const encrypted = [];
            const keyBytes = this.encryptionKey.match(/.{2}/g).map(byte => parseInt(byte, 16));
            
            for (let i = 0; i < data.length; i++) {
                encrypted.push(data.charCodeAt(i) ^ keyBytes[i % keyBytes.length]);
            }
            
            return btoa(String.fromCharCode(...encrypted));
        } catch (error) {
            console.error('数据加密失败:', error);
            throw error;
        }
    }

    /**
     * 解密数据
     */
    async decryptData(encryptedData) {
        try {
            const encrypted = atob(encryptedData);
            const decrypted = [];
            const keyBytes = this.encryptionKey.match(/.{2}/g).map(byte => parseInt(byte, 16));
            
            for (let i = 0; i < encrypted.length; i++) {
                decrypted.push(encrypted.charCodeAt(i) ^ keyBytes[i % keyBytes.length]);
            }
            
            return String.fromCharCode(...decrypted);
        } catch (error) {
            console.error('数据解密失败:', error);
            throw error;
        }
    }

    /**
     * 恢复备份
     */
    async restoreBackup(backupId, options = {}) {
        try {
            console.log('开始恢复备份:', backupId);
            
            // 获取备份数据
            const backupRecord = await this.getFromDB('backups', backupId);
            if (!backupRecord) {
                throw new Error('备份记录不存在');
            }

            let processedData = backupRecord.data;

            // 解密数据
            if (backupRecord.encrypted) {
                processedData = await this.decryptData(processedData);
            }

            // 解压数据
            if (backupRecord.compressed) {
                processedData = await this.decompressData(processedData);
            }

            // 解析备份数据
            const backupData = JSON.parse(processedData);

            // 确认恢复操作
            if (!options.forceConfirm) {
                const confirmMessage = `确定要恢复备份吗？\n备份时间: ${backupData.timestamp}\n备份类型: ${backupData.type}\n\n此操作将覆盖当前所有数据！`;
                if (!confirm(confirmMessage)) {
                    return false;
                }
            }

            // 创建当前数据的备份
            await this.createBackup({
                type: 'pre-restore',
                description: `恢复前备份 - ${new Date().toLocaleString()}`
            });

            // 恢复数据库数据
            if (backupData.database) {
                await this.restoreDatabaseData(backupData.database);
            }

            // 恢复配置数据
            if (backupData.config) {
                await this.restoreConfigData(backupData.config);
            }

            this.emitEvent('backupRestored', { backupId, backupData });
            console.log('备份恢复完成');
            
            return true;
        } catch (error) {
            console.error('恢复备份失败:', error);
            this.emitEvent('restoreError', error);
            throw error;
        }
    }

    /**
     * 恢复数据库数据
     */
    async restoreDatabaseData(databaseData) {
        for (const [dbName, data] of Object.entries(databaseData)) {
            if (data.error) {
                console.warn(`跳过数据库 ${dbName}:`, data.error);
                continue;
            }

            try {
                await this.importDatabase(dbName, data);
                console.log(`数据库 ${dbName} 恢复完成`);
            } catch (error) {
                console.error(`恢复数据库 ${dbName} 失败:`, error);
            }
        }
    }

    /**
     * 导入数据库
     */
    async importDatabase(dbName, data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(dbName, 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                let completed = 0;
                const total = Object.keys(data).length;

                for (const [storeName, records] of Object.entries(data)) {
                    const transaction = db.transaction(storeName, 'readwrite');
                    const store = transaction.objectStore(storeName);

                    // 清空现有数据
                    const clearRequest = store.clear();
                    clearRequest.onsuccess = () => {
                        // 导入新数据
                        records.forEach(record => {
                            store.add(record);
                        });
                    };

                    transaction.oncomplete = () => {
                        completed++;
                        if (completed === total) {
                            db.close();
                            resolve();
                        }
                    };
                }
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // 根据数据创建对象存储
                for (const storeName of Object.keys(data)) {
                    if (!db.objectStoreNames.contains(storeName)) {
                        db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true });
                    }
                }
            };
        });
    }

    /**
     * 恢复配置数据
     */
    async restoreConfigData(configData) {
        try {
            // 恢复系统设置
            if (configData.systemSettings && window.systemSettings) {
                await window.systemSettings.importSettings(configData.systemSettings);
            }

            // 恢复本地存储
            if (configData.localStorage) {
                for (const [key, value] of Object.entries(configData.localStorage)) {
                    localStorage.setItem(key, value);
                }
            }

            // 恢复会话存储
            if (configData.sessionStorage) {
                for (const [key, value] of Object.entries(configData.sessionStorage)) {
                    sessionStorage.setItem(key, value);
                }
            }

            console.log('配置数据恢复完成');
        } catch (error) {
            console.error('恢复配置数据失败:', error);
        }
    }

    /**
     * 清理过期备份
     */
    async cleanupExpiredBackups() {
        try {
            const now = new Date();
            const cutoffDate = new Date(now.getTime() - this.backupConfig.retention * 24 * 60 * 60 * 1000);
            
            const allBackups = await this.getAllFromDB('backups');
            const expiredBackups = allBackups.filter(backup => 
                new Date(backup.timestamp) < cutoffDate
            );

            // 如果备份数量超过限制，删除最旧的备份
            if (allBackups.length > this.backupConfig.maxBackups) {
                const excessBackups = allBackups
                    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
                    .slice(0, allBackups.length - this.backupConfig.maxBackups);
                
                expiredBackups.push(...excessBackups);
            }

            // 删除过期备份
            for (const backup of expiredBackups) {
                await this.deleteFromDB('backups', backup.id);
                console.log('删除过期备份:', backup.id);
            }

            if (expiredBackups.length > 0) {
                this.emitEvent('backupsCleaned', { count: expiredBackups.length });
            }

        } catch (error) {
            console.error('清理过期备份失败:', error);
        }
    }

    /**
     * 上传到远程
     */
    async uploadToRemote(backupRecord) {
        if (!this.backupConfig.remotePath) {
            throw new Error('远程备份路径未配置');
        }

        try {
            const formData = new FormData();
            formData.append('backup', JSON.stringify(backupRecord));
            formData.append('timestamp', backupRecord.timestamp);
            formData.append('type', backupRecord.type);

            const response = await fetch(this.backupConfig.remotePath, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`远程上传失败: ${response.statusText}`);
            }

            console.log('远程备份上传成功');
        } catch (error) {
            console.error('远程备份上传失败:', error);
            throw error;
        }
    }

    /**
     * 获取备份列表
     */
    async getBackupList() {
        try {
            const backups = await this.getAllFromDB('backups');
            return backups.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        } catch (error) {
            console.error('获取备份列表失败:', error);
            return [];
        }
    }

    /**
     * 删除备份
     */
    async deleteBackup(backupId) {
        try {
            await this.deleteFromDB('backups', backupId);
            this.backupHistory = this.backupHistory.filter(backup => backup.id !== backupId);
            this.emitEvent('backupDeleted', { backupId });
            console.log('备份删除成功:', backupId);
            return true;
        } catch (error) {
            console.error('删除备份失败:', error);
            return false;
        }
    }

    /**
     * 更新配置
     */
    async updateConfig(newConfig) {
        try {
            this.backupConfig = { ...this.backupConfig, ...newConfig };
            
            // 保存配置
            await this.saveToDB('config', {
                key: 'backup_config',
                value: this.backupConfig,
                timestamp: new Date().toISOString()
            });

            // 重新设置自动备份
            this.setupAutoBackup();
            
            this.emitEvent('configUpdated', this.backupConfig);
            console.log('备份配置更新完成');
            
            return true;
        } catch (error) {
            console.error('更新备份配置失败:', error);
            return false;
        }
    }

    /**
     * 数据库操作辅助方法
     */
    async getFromDB(store, key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(store, 'readonly');
            const request = transaction.objectStore(store).get(key);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async getAllFromDB(store) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(store, 'readonly');
            const request = transaction.objectStore(store).getAll();
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async saveToDB(store, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(store, 'readwrite');
            const request = transaction.objectStore(store).put(data);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async deleteFromDB(store, key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(store, 'readwrite');
            const request = transaction.objectStore(store).delete(key);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    /**
     * 生成备份ID
     */
    generateBackupId() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const random = Math.random().toString(36).substr(2, 9);
        return `backup_${timestamp}_${random}`;
    }

    /**
     * 事件处理
     */
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    removeEventListener(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emitEvent(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 销毁管理器
     */
    destroy() {
        if (this.backupTimer) {
            clearInterval(this.backupTimer);
        }
        this.listeners.clear();
        this.isInitialized = false;
    }
}

// 创建全局实例
window.databaseBackup = new DatabaseBackupManager();

// 自动初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.databaseBackup.initialize();
        console.log('数据库备份管理器已准备就绪');
    } catch (error) {
        console.error('数据库备份管理器初始化失败:', error);
    }
});

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseBackupManager;
}
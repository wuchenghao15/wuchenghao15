/**
 * MTSCOS AI System - 加密数据库管理器
 * 版本: 1.0.0
 * 描述: 继承DatabaseManager，添加加密功能
 */

class EncryptedDatabaseManager {
    constructor() {
        this.dbName = 'MTSCOS_ENCRYPTED_DB';
        this.dbVersion = 1;
        this.db = null;
        this.isReady = false;
        this.encryption = null;
        this.encryptedCollections = new Set([
            'user_profiles',
            'user_preferences',
            'system_settings',
            'ai_employee_data',
            'rules',
            'logs'
        ]);
        this.collections = [
            { name: 'user_profiles', keyPath: 'id', autoIncrement: false, encrypted: true },
            { name: 'user_preferences', keyPath: 'id', autoIncrement: false, encrypted: true },
            { name: 'system_settings', keyPath: 'id', autoIncrement: false, encrypted: true },
            { name: 'system_state', keyPath: 'id', autoIncrement: false, encrypted: false },
            { name: 'ai_employee_data', keyPath: 'id', autoIncrement: false, encrypted: true },
            { name: 'logs', keyPath: 'id', autoIncrement: true, encrypted: true },
            { name: 'sync_history', keyPath: 'id', autoIncrement: true, encrypted: false },
            { name: 'rules', keyPath: 'id', autoIncrement: false, encrypted: true },
            { name: 'version_history', keyPath: 'id', autoIncrement: false, encrypted: false },
            { name: 'performance_metrics', keyPath: 'id', autoIncrement: true, encrypted: false }
        ];
        this.init();
    }
    
    async init() {
        try {
            // 初始化加密管理器
            this.encryption = new DatabaseEncryption();
            
            // 打开数据库
            this.db = await this.openDatabase();
            this.isReady = true;
            
            console.log('✅ 加密数据库初始化成功');
            
            // 触发就绪事件
            document.dispatchEvent(new CustomEvent('mtscos:encrypted-db:ready', {
                detail: { database: this }
            }));
        } catch (error) {
            console.error('❌ 加密数据库初始化失败:', error);
        }
    }
    
    async openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                for (const collection of this.collections) {
                    if (!db.objectStoreNames.contains(collection.name)) {
                        const store = db.createObjectStore(collection.name, {
                            keyPath: collection.keyPath,
                            autoIncrement: collection.autoIncrement
                        });
                        
                        // 创建常用索引
                        if (collection.name === 'logs') {
                            store.createIndex('timestamp', 'timestamp', { unique: false });
                            store.createIndex('level', 'level', { unique: false });
                        }
                    }
                }
            };
        });
    }
    
    async waitForReady() {
        if (this.isReady) return true;
        
        return new Promise((resolve) => {
            document.addEventListener('mtscos:encrypted-db:ready', (e) => {
                resolve(true);
            }, { once: true });
        });
    }
    
    // ==================== 加密的CRUD操作 ====================
    
    async add(collectionName, data) {
        await this.waitForReady();
        
        // 如果该集合需要加密
        if (this.encryptedCollections.has(collectionName)) {
            const encrypted = await this.encryption.encryptRecord({
                ...data,
                _original: data
            });
            return this.transaction(collectionName, 'readwrite', (store) => {
                return store.add(encrypted);
            });
        }
        
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.add(data);
        });
    }
    
    async put(collectionName, data) {
        await this.waitForReady();
        
        if (this.encryptedCollections.has(collectionName)) {
            const encrypted = await this.encryption.encryptRecord({
                ...data,
                _original: data
            });
            return this.transaction(collectionName, 'readwrite', (store) => {
                return store.put(encrypted);
            });
        }
        
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.put(data);
        });
    }
    
    async get(collectionName, key) {
        await this.waitForReady();
        
        const record = await this.transaction(collectionName, 'readonly', (store) => {
            return store.get(key);
        });
        
        if (record && record._encrypted && this.encryptedCollections.has(collectionName)) {
            return await this.encryption.decryptRecord(record);
        }
        
        return record;
    }
    
    async getAll(collectionName) {
        await this.waitForReady();
        
        const records = await this.transaction(collectionName, 'readonly', (store) => {
            return store.getAll();
        });
        
        if (this.encryptedCollections.has(collectionName)) {
            return Promise.all(
                records.map(r => r._encrypted ? this.encryption.decryptRecord(r) : r)
            );
        }
        
        return records;
    }
    
    async delete(collectionName, key) {
        await this.waitForReady();
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.delete(key);
        });
    }
    
    async clear(collectionName) {
        await this.waitForReady();
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.clear();
        });
    }
    
    async search(collectionName, keyword) {
        const items = await this.getAll(collectionName);
        const lowerKeyword = keyword.toLowerCase();
        
        return items.filter(item => {
            const searchText = JSON.stringify(item).toLowerCase();
            return searchText.includes(lowerKeyword);
        });
    }
    
    // ==================== 加密导出/导入 ====================
    
    async exportAll(password) {
        await this.waitForReady();
        
        const data = {};
        
        for (const collection of this.collections) {
            data[collection.name] = await this.getAll(collection.name);
        }
        
        if (password) {
            return await this.encryption.exportEncrypted(data, password);
        }
        
        return {
            encrypted: false,
            data: data,
            timestamp: Date.now()
        };
    }
    
    async importAll(exportedData, password = null) {
        await this.waitForReady();
        
        let data;
        if (exportedData.encrypted && password) {
            data = await this.encryption.importEncrypted(exportedData, password);
        } else {
            data = exportedData.data || exportedData;
        }
        
        for (const [collectionName, records] of Object.entries(data)) {
            if (Array.isArray(records)) {
                await this.clear(collectionName);
                for (const record of records) {
                    try {
                        await this.add(collectionName, record);
                    } catch (error) {
                        // 忽略重复键错误
                    }
                }
            }
        }
        
        console.log('✅ 数据导入完成');
    }
    
    // ==================== 事务管理 ====================
    
    async transaction(collectionName, mode, callback) {
        if (!this.db) {
            throw new Error('数据库未初始化');
        }
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([collectionName], mode);
            const store = transaction.objectStore(collectionName);
            
            try {
                const request = callback(store);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            } catch (error) {
                reject(error);
            }
        });
    }
    
    // ==================== 健康检查 ====================
    
    async healthCheck() {
        return {
            status: this.isReady ? 'healthy' : 'error',
            database: this.dbName,
            version: this.dbVersion,
            encryption: this.encryption?.healthCheck(),
            encryptedCollections: Array.from(this.encryptedCollections),
            totalCollections: this.collections.length
        };
    }
    
    // ==================== 统计 ====================
    
    async getStats() {
        await this.waitForReady();
        const stats = {};
        
        for (const collection of this.collections) {
            try {
                const items = await this.transaction(collection.name, 'readonly', (store) => {
                    return store.count();
                });
                stats[collection.name] = {
                    count: items,
                    encrypted: this.encryptedCollections.has(collection.name)
                };
            } catch (error) {
                stats[collection.name] = { count: 0, error: error.message };
            }
        }
        
        return stats;
    }
}

// 导出
if (typeof window !== 'undefined') {
    window.EncryptedDatabaseManager = EncryptedDatabaseManager;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EncryptedDatabaseManager;
}

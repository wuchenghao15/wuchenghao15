/**
 * MTSCOS AI System - 数据库管理系统
 * 版本: 4.3.0
 * 描述: 统一管理系统所有数据的数据库服务
 */

class DatabaseManager {
    constructor() {
        this.dbName = 'MTSCOS_DB';
        this.dbVersion = 4;
        this.db = null;
        this.isReady = false;
        this.initPromise = null;
        this.collections = [
            { name: 'system_settings', keyPath: 'key', autoIncrement: false },
            { name: 'user_profiles', keyPath: 'userId', autoIncrement: false },
            { name: 'user_preferences', keyPath: 'userId', autoIncrement: false },
            { name: 'system_state', keyPath: 'key', autoIncrement: false },
            { name: 'ai_employee_data', keyPath: 'employeeId', autoIncrement: false },
            { name: 'logs', keyPath: 'id', autoIncrement: true },
            { name: 'sync_history', keyPath: 'id', autoIncrement: true },
            { name: 'rules', keyPath: 'id', autoIncrement: false },
            { name: 'version_history', keyPath: 'version', autoIncrement: false },
            { name: 'performance_metrics', keyPath: 'timestamp', autoIncrement: false },
            { name: 'password_reset_records', keyPath: 'id', autoIncrement: true }
        ];
        this.initPromise = this.init();
    }
    
    async init() {
        try {
            this.db = await this.openDatabase();
            this.isReady = true;
            console.log('✅ 数据库管理系统初始化成功');
            
            // 初始化默认数据
            await this.initDefaultData();
            
            // 触发数据库就绪事件
            document.dispatchEvent(new CustomEvent('mtscos:database:ready'));
            return true;
        } catch (error) {
            console.error('❌ 数据库管理系统初始化失败:', error);
            return false;
        }
    }
    
    // 等待数据库就绪
    async waitForReady() {
        if (this.isReady) return true;
        if (this.initPromise) {
            await this.initPromise;
        }
        return this.isReady;
    }
    
    async openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            
            request.onsuccess = () => {
                resolve(request.result);
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // 创建所有集合
                for (const collection of this.collections) {
                    if (!db.objectStoreNames.contains(collection.name)) {
                        const store = db.createObjectStore(collection.name, {
                            keyPath: collection.keyPath,
                            autoIncrement: collection.autoIncrement
                        });
                        
                        // 创建索引
                        this.createIndexes(store, collection.name);
                    }
                }
            };
        });
    }
    
    createIndexes(store, collectionName) {
        switch (collectionName) {
            case 'system_settings':
                store.createIndex('category', 'category', { unique: false });
                store.createIndex('updatedAt', 'updatedAt', { unique: false });
                break;
            case 'user_profiles':
                store.createIndex('email', 'email', { unique: true });
                store.createIndex('createdAt', 'createdAt', { unique: false });
                break;
            case 'user_preferences':
                store.createIndex('theme', 'theme', { unique: false });
                store.createIndex('updatedAt', 'updatedAt', { unique: false });
                break;
            case 'logs':
                store.createIndex('level', 'level', { unique: false });
                store.createIndex('timestamp', 'timestamp', { unique: false });
                store.createIndex('source', 'source', { unique: false });
                break;
            case 'sync_history':
                store.createIndex('status', 'status', { unique: false });
                store.createIndex('timestamp', 'timestamp', { unique: false });
                break;
            case 'performance_metrics':
                store.createIndex('type', 'type', { unique: false });
                break;
            case 'password_reset_records':
                store.createIndex('userId', 'userId', { unique: false });
                store.createIndex('email', 'email', { unique: false });
                store.createIndex('status', 'status', { unique: false });
                store.createIndex('createdAt', 'createdAt', { unique: false });
                break;
        }
    }
    
    async initDefaultData() {
        // 初始化系统设置
        const existingSettings = await this.getAll('system_settings');
        if (existingSettings.length === 0) {
            await this.bulkAdd('system_settings', [
                { key: 'theme', value: 'light', category: 'ui', updatedAt: Date.now() },
                { key: 'language', value: 'zh-CN', category: 'system', updatedAt: Date.now() },
                { key: 'timezone', value: 'Asia/Shanghai', category: 'system', updatedAt: Date.now() },
                { key: 'auto_update', value: false, category: 'system', updatedAt: Date.now() },
                { key: 'notifications', value: true, category: 'ui', updatedAt: Date.now() },
                { key: 'analytics', value: true, category: 'system', updatedAt: Date.now() },
                { key: 'performance_monitoring', value: true, category: 'system', updatedAt: Date.now() },
                { key: 'security_enabled', value: true, category: 'security', updatedAt: Date.now() },
                { key: 'cache_enabled', value: true, category: 'performance', updatedAt: Date.now() },
                { key: 'logging_level', value: 'info', category: 'system', updatedAt: Date.now() }
            ]);
        }
    }
    
    // ==================== 基础操作 ====================

    async add(collectionName, data) {
        // 自动等待数据库就绪
        await this.waitForReady();
        if (!this.db) {
            throw new Error('数据库未初始化');
        }
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.add(data);
        });
    }
    
    async put(collectionName, data) {
        // 自动等待数据库就绪
        await this.waitForReady();
        if (!this.db) {
            throw new Error('数据库未初始化');
        }
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.put(data);
        });
    }
    
    async bulkAdd(collectionName, dataArray) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            const results = [];
            dataArray.forEach(data => {
                results.push(store.add(data));
            });
            return results;
        });
    }
    
    async get(collectionName, key) {
        return this.transaction(collectionName, 'readonly', (store) => {
            return store.get(key);
        });
    }
    
    async getAll(collectionName) {
        return this.transaction(collectionName, 'readonly', (store) => {
            return store.getAll();
        });
    }
    
    async getAllByIndex(collectionName, indexName, value) {
        return this.transaction(collectionName, 'readonly', (store) => {
            return store.index(indexName).getAll(value);
        });
    }
    
    async delete(collectionName, key) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.delete(key);
        });
    }
    
    async clear(collectionName) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.clear();
        });
    }
    
    async count(collectionName) {
        return this.transaction(collectionName, 'readonly', (store) => {
            return store.count();
        });
    }
    
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
                
                transaction.onerror = () => reject(transaction.error);
            } catch (error) {
                reject(error);
            }
        });
    }
    
    // ==================== 系统设置操作 ====================
    
    async getSystemSetting(key, defaultValue = null) {
        const setting = await this.get('system_settings', key);
        return setting ? setting.value : defaultValue;
    }
    
    async setSystemSetting(key, value, category = 'system') {
        await this.put('system_settings', {
            key,
            value,
            category,
            updatedAt: Date.now()
        });
        
        // 触发设置变更事件
        document.dispatchEvent(new CustomEvent('mtscos:setting:changed', {
            detail: { key, value, category }
        }));
        
        return true;
    }
    
    async getSettingsByCategory(category) {
        const settings = await this.getAllByIndex('system_settings', 'category', category);
        return settings.reduce((acc, setting) => {
            acc[setting.key] = setting.value;
            return acc;
        }, {});
    }
    
    // ==================== 用户配置操作 ====================
    
    async getUserProfile(userId) {
        return await this.get('user_profiles', userId);
    }
    
    async saveUserProfile(userId, profile) {
        await this.put('user_profiles', {
            userId,
            ...profile,
            updatedAt: Date.now()
        });
        return true;
    }
    
    async getUserPreferences(userId) {
        const prefs = await this.get('user_preferences', userId);
        return prefs || { userId, preferences: {}, updatedAt: Date.now() };
    }
    
    async saveUserPreferences(userId, preferences) {
        await this.put('user_preferences', {
            userId,
            preferences,
            updatedAt: Date.now()
        });
        
        document.dispatchEvent(new CustomEvent('mtscos:preferences:changed', {
            detail: { userId, preferences }
        }));
        
        return true;
    }
    
    async updateUserPreference(userId, key, value) {
        const existing = await this.getUserPreferences(userId);
        existing.preferences = existing.preferences || {};
        existing.preferences[key] = value;
        existing.updatedAt = Date.now();
        await this.put('user_preferences', existing);
        return true;
    }
    
    // ==================== AI员工数据操作 ====================

    async saveAIEmployee(employee) {
        // 等待数据库就绪
        await this.waitForReady();
        if (!this.db) {
            console.warn('数据库未就绪，跳过AI员工保存:', employee?.id);
            return false;
        }
        try {
            // 确保有id字段（keyPath要求）
            const data = {
                id: employee.id || `emp_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
                employeeId: employee.id,
                ...employee,
                updatedAt: Date.now()
            };
            await this.put('ai_employee_data', data);
            return true;
        } catch (error) {
            console.warn('保存AI员工失败:', error.message);
            return false;
        }
    }
    
    async getAllAIEmployees() {
        return await this.getAll('ai_employee_data');
    }
    
    async getAIEmployee(employeeId) {
        return await this.get('ai_employee_data', employeeId);
    }
    
    async updateAIEmployeeStatus(employeeId, status, workload) {
        const employee = await this.getAIEmployee(employeeId);
        if (employee) {
            employee.status = status;
            employee.workload = workload;
            employee.updatedAt = Date.now();
            await this.put('ai_employee_data', employee);
        }
        return true;
    }
    
    // ==================== 日志操作 ====================
    
    async addLog(message, level = 'info', source = 'system', data = {}) {
        // 等待数据库就绪
        await this.waitForReady();
        if (!this.db) {
            console.warn('数据库未就绪，跳过日志:', message);
            return;
        }
        try {
            await this.add('logs', {
                message,
                level,
                source,
                data,
                timestamp: Date.now()
            });
        } catch (error) {
            console.warn('日志写入失败:', error.message);
        }
        
        // 限制日志数量
        this.trimLogs();
        
        return true;
    }
    
    async getLogs(level = null, limit = 100) {
        let logs = await this.getAll('logs');
        
        if (level) {
            logs = logs.filter(log => log.level === level);
        }
        
        logs.sort((a, b) => b.timestamp - a.timestamp);
        
        return logs.slice(0, limit);
    }
    
    async trimLogs(maxCount = 1000) {
        const logs = await this.getAll('logs');
        if (logs.length > maxCount) {
            const toDelete = logs.slice(maxCount);
            for (const log of toDelete) {
                await this.delete('logs', log.id);
            }
        }
    }
    
    // ==================== 性能指标操作 ====================
    
    async addPerformanceMetric(type, value, metadata = {}) {
        await this.add('performance_metrics', {
            type,
            value,
            metadata,
            timestamp: Date.now()
        });
        
        // 保留最近7天的数据
        this.trimPerformanceMetrics();
        
        return true;
    }
    
    async getPerformanceMetrics(type = null, hours = 24) {
        let metrics = await this.getAll('performance_metrics');
        
        if (type) {
            metrics = metrics.filter(m => m.type === type);
        }
        
        const cutoff = Date.now() - (hours * 60 * 60 * 1000);
        metrics = metrics.filter(m => m.timestamp > cutoff);
        
        metrics.sort((a, b) => a.timestamp - b.timestamp);
        
        return metrics;
    }
    
    async trimPerformanceMetrics(days = 7) {
        const metrics = await this.getAll('performance_metrics');
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        
        for (const metric of metrics) {
            if (metric.timestamp < cutoff) {
                await this.delete('performance_metrics', metric.timestamp);
            }
        }
    }
    
    // ==================== 同步历史操作 ====================
    
    async addSyncRecord(status, dataType, details = {}) {
        try {
            await this.waitForReady();
            if (!this.db) {
                console.warn('⚠️ 数据库未就绪，跳过同步记录');
                return false;
            }
            await this.add('sync_history', {
                status,
                dataType,
                details,
                timestamp: Date.now()
            });
            
            // 限制记录数量
            this.trimSyncHistory().catch(() => {});
            
            return true;
        } catch (error) {
            console.warn('⚠️ 添加同步记录失败:', error.message);
            return false;
        }
    }
    
    async getSyncHistory(status = null, limit = 50) {
        let records = await this.getAll('sync_history');
        
        if (status) {
            records = records.filter(r => r.status === status);
        }
        
        records.sort((a, b) => b.timestamp - a.timestamp);
        
        return records.slice(0, limit);
    }
    
    async trimSyncHistory(maxCount = 100) {
        const records = await this.getAll('sync_history');
        if (records.length > maxCount) {
            const toDelete = records.slice(maxCount);
            for (const record of toDelete) {
                await this.delete('sync_history', record.id);
            }
        }
    }
    
    // ==================== 密码重置记录操作 ====================
    
    async addPasswordResetRecord(userId, email, status, details = {}) {
        try {
            await this.waitForReady();
            if (!this.db) {
                console.warn('⚠️ 数据库未就绪，跳过密码重置记录');
                return false;
            }
            
            const record = {
                userId,
                email,
                status,
                details,
                createdAt: Date.now(),
                updatedAt: Date.now()
            };
            
            await this.add('password_reset_records', record);
            
            this.trimPasswordResetRecords().catch(() => {});
            
            return true;
        } catch (error) {
            console.warn('⚠️ 添加密码重置记录失败:', error.message);
            return false;
        }
    }
    
    async updatePasswordResetRecord(recordId, status, details = {}) {
        try {
            await this.waitForReady();
            if (!this.db) {
                console.warn('⚠️ 数据库未就绪，跳过密码重置更新');
                return false;
            }
            
            let record = await this.get('password_reset_records', recordId);
            if (!record) {
                return false;
            }
            
            record.status = status;
            record.details = { ...record.details, ...details };
            record.updatedAt = Date.now();
            
            await this.put('password_reset_records', record);
            
            return true;
        } catch (error) {
            console.warn('⚠️ 更新密码重置记录失败:', error.message);
            return false;
        }
    }
    
    async getPasswordResetRecords(email = null, status = null, limit = 20) {
        let records = await this.getAll('password_reset_records');
        
        if (email) {
            records = records.filter(r => r.email === email);
        }
        
        if (status) {
            records = records.filter(r => r.status === status);
        }
        
        records.sort((a, b) => b.createdAt - a.createdAt);
        
        return records.slice(0, limit);
    }
    
    async getPasswordResetRecordById(recordId) {
        return await this.get('password_reset_records', recordId);
    }
    
    async trimPasswordResetRecords(maxCount = 50) {
        const records = await this.getAll('password_reset_records');
        if (records.length > maxCount) {
            const toDelete = records.slice(maxCount);
            for (const record of toDelete) {
                await this.delete('password_reset_records', record.id);
            }
        }
    }
    
    // ==================== 系统状态操作 ====================
    
    async getSystemState(key) {
        const state = await this.get('system_state', key);
        return state ? state.value : null;
    }
    
    async setSystemState(key, value) {
        await this.put('system_state', {
            key,
            value,
            updatedAt: Date.now()
        });
        
        document.dispatchEvent(new CustomEvent('mtscos:state:changed', {
            detail: { key, value }
        }));
        
        return true;
    }
    
    // ==================== 规则操作 ====================
    
    async saveRule(rule) {
        await this.put('rules', {
            id: rule.id,
            ...rule,
            updatedAt: Date.now()
        });
        return true;
    }
    
    async getAllRules() {
        return await this.getAll('rules');
    }
    
    async getRule(ruleId) {
        return await this.get('rules', ruleId);
    }
    
    // ==================== 版本历史操作 ====================
    
    async saveVersion(versionInfo) {
        await this.put('version_history', {
            version: versionInfo.version,
            ...versionInfo,
            updatedAt: Date.now()
        });
        return true;
    }
    
    async getAllVersions() {
        const versions = await this.getAll('version_history');
        return versions.sort((a, b) => b.buildDate.localeCompare(a.buildDate));
    }
    
    // ==================== 健康检查 ====================
    
    async healthCheck() {
        const results = {};
        
        for (const collection of this.collections) {
            try {
                const count = await this.count(collection.name);
                results[collection.name] = { status: 'ok', count };
            } catch (error) {
                results[collection.name] = { status: 'error', error: error.message };
            }
        }
        
        return {
            status: this.isReady ? 'healthy' : 'unhealthy',
            database: this.dbName,
            version: this.dbVersion,
            collections: results
        };
    }
    
    // ==================== 数据导出/导入 ====================
    
    async exportData(collectionNames = null) {
        const exportData = {};
        const collections = collectionNames || this.collections.map(c => c.name);
        
        for (const name of collections) {
            try {
                exportData[name] = await this.getAll(name);
            } catch (error) {
                exportData[name] = { error: error.message };
            }
        }
        
        return {
            exportedAt: Date.now(),
            database: this.dbName,
            data: exportData
        };
    }
    
    async importData(data) {
        let success = 0;
        let failed = 0;
        
        for (const [collectionName, items] of Object.entries(data.data)) {
            try {
                await this.clear(collectionName);
                if (Array.isArray(items)) {
                    for (const item of items) {
                        try {
                            await this.put(collectionName, item);
                            success++;
                        } catch {
                            failed++;
                        }
                    }
                }
            } catch {
                failed += Array.isArray(items) ? items.length : 1;
            }
        }
        
        return { success, failed, total: success + failed };
    }
    
    // ==================== 销毁 ====================
    
    destroy() {
        if (this.db) {
            this.db.close();
            this.db = null;
        }
        this.isReady = false;
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseManager;
}

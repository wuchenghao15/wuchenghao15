/**
 * MyData 统一数据管理器
 * 负责接管所有本地数据库操作，统一数据存储和管理
 */

class MyDataManager {
    constructor() {
        this.storagePrefix = 'mydata_';
        this.version = '1.0.0';
        this.isInitialized = false;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存超时
        this.encryptionEnabled = true;
        this.compressionEnabled = true;
        
        // 数据表定义
        this.tables = {
            users: {
                name: 'users',
                columns: ['id', 'username', 'email', 'password', 'role', 'createdAt', 'updatedAt', 'isActive'],
                primaryKey: 'id'
            },
            sessions: {
                name: 'sessions',
                columns: ['sessionId', 'userId', 'username', 'loginTime', 'lastActivity', 'ipAddress', 'userAgent', 'expiresAt', 'isActive'],
                primaryKey: 'sessionId'
            },
            systemConfig: {
                name: 'systemConfig',
                columns: ['configKey', 'configValue', 'description', 'category', 'createdAt', 'updatedAt'],
                primaryKey: 'configKey'
            },
            systemFactors: {
                name: 'systemFactors',
                columns: ['factorId', 'factorName', 'factorValue', 'factorType', 'category', 'isActive', 'createdAt', 'updatedAt'],
                primaryKey: 'factorId'
            },
            systemLogs: {
                name: 'systemLogs',
                columns: ['logId', 'logLevel', 'message', 'source', 'userId', 'timestamp', 'metadata'],
                primaryKey: 'logId'
            },
            versionHistory: {
                name: 'versionHistory',
                columns: ['versionId', 'version', 'internalVersion', 'releaseDate', 'description', 'changes', 'isCurrent', 'createdAt'],
                primaryKey: 'versionId'
            },
            userPreferences: {
                name: 'userPreferences',
                columns: ['userId', 'preferenceKey', 'preferenceValue', 'category', 'updatedAt'],
                primaryKey: ['userId', 'preferenceKey']
            },
            themeSettings: {
                name: 'themeSettings',
                columns: ['themeId', 'themeName', 'config', 'isActive', 'createdAt', 'updatedAt'],
                primaryKey: 'themeId'
            },
            securityEvents: {
                name: 'securityEvents',
                columns: ['eventId', 'eventType', 'userId', 'ipAddress', 'userAgent', 'description', 'severity', 'timestamp', 'metadata'],
                primaryKey: 'eventId'
            },
            performanceMetrics: {
                name: 'performanceMetrics',
                columns: ['metricId', 'metricName', 'metricValue', 'metricUnit', 'category', 'timestamp', 'tags'],
                primaryKey: 'metricId'
            }
        };
    }

    /**
     * 初始化MyData管理器
     */
    async initialize() {
        try {
            console.log('🚀 初始化MyData统一数据管理器...');
            
            // 检查浏览器环境
            if (typeof window === 'undefined') {
                throw new Error('MyData管理器需要在浏览器环境中运行');
            }
            
            // 检查localStorage可用性
            if (!this.isLocalStorageAvailable().catch(error => console.error(`[mydata-manager.js] this.isLocalStorageAvailable failed:`, error))) {
                throw new Error('localStorage不可用，无法初始化MyData管理器');
            }
            
            // 迁移现有数据
            await this.migrateExistingData();
            
            // 初始化数据表
            await this.initializeTables();
            
            // 设置默认配置
            await this.setDefaultConfig();
            
            // 清理过期数据
            await this.cleanupExpiredData();
            
            this.isInitialized = true;
            console.log('✅ MyData统一数据管理器初始化完成');
            
            // 记录初始化日志
            await this.logSystemEvent('info', 'MyData管理器初始化完成', 'MyDataManager');
            
        } catch (error) {
            console.error(`[mydata-manager.js] ❌ MyData管理器初始化失败:, error`);
            throw error;
        }
    }

    /**
     * 检查localStorage可用性
     */
    isLocalStorageAvailable() {
        try {
            const test = '__mydata_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * 迁移现有数据
     */
    async migrateExistingData() {
        console.log('📦 开始迁移现有数据...');
        
        const migrationTasks = [];
        
        // 扫描localStorage中的现有数据
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && !key.startsWith(this.storagePrefix) && !key.startsWith('db_table_')) {
                migrationTasks.push(this.migrateDataItem(key));
            }
        }
        
        // 执行迁移
        const results = await Promise.allSettled(migrationTasks);
        const successful = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;
        
        console.log(`📊 数据迁移完成: 成功 ${successful} 项，失败 ${failed} 项`);
        
        // 清理已迁移的数据
        await this.cleanupMigratedData();
    }

    /**
     * 迁移单个数据项
     */
    async migrateDataItem(key) {
        try {
            const value = localStorage.getItem(key);
            if (!value) return;
            
            // 根据key分类存储
            let tableName = 'systemConfig';
            let data = {};
            
            if (key.includes('theme') || key.includes('color')) {
                tableName = 'themeSettings';
                data = {
                    themeId: this.generateUUID().catch(error => console.error(`[mydata-manager.js] this.generateUUID failed:`, error)),
                    themeName: 'migrated',
                    config: { key, value },
                    isActive: key.includes('theme') && !key.includes('mtscos_theme'),
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                };
            } else if (key.includes('auth') || key.includes('token') || key.includes('session')) {
                tableName = 'sessions';
                data = {
                    sessionId: this.generateUUID().catch(error => console.error(`[mydata-manager.js] this.generateUUID failed:`, error)),
                    userId: 'migrated',
                    username: 'migrated',
                    loginTime: new Date().toISOString(),
                    lastActivity: new Date().toISOString(),
                    ipAddress: 'unknown',
                    userAgent: 'migrated',
                    expiresAt: new Date(Date.now().catch(error => console.error(`[mydata-manager.js] Date.now failed:`, error)) + 24 * 60 * 60 * 1000).toISOString(),
                    isActive: false
                };
            } else if (key.includes('log') || key.includes('error')) {
                tableName = 'systemLogs';
                data = {
                    logId: this.generateUUID().catch(error => console.error(`[mydata-manager.js] this.generateUUID failed:`, error)),
                    logLevel: 'info',
                    message: `迁移数据: ${key}`,
                    source: 'Migration',
                    userId: null,
                    timestamp: new Date().toISOString(),
                    metadata: JSON.stringify({ originalKey: key, value })
                };
            } else {
                // 默认存储为系统配置
                data = {
                    configKey: key,
                    configValue: value,
                    description: `从localStorage迁移的数据: ${key}`,
                    category: this.categorizeKey(key),
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                };
            }
            
            await this.insert(tableName, data);
            console.log(`📝 已迁移数据项: ${key} -> ${tableName}`);
            
        } catch (error) {
            console.warn(`⚠️ 迁移数据项失败: ${key}`, error);
        }
    }

    /**
     * 根据key分类
     */
    categorizeKey(key) {
        if (key.includes('theme')) return 'theme';
        if (key.includes('auth') || key.includes('token')) return 'authentication';
        if (key.includes('session')) return 'session';
        if (key.includes('user')) return 'user';
        if (key.includes('system')) return 'system';
        if (key.includes('config')) return 'configuration';
        if (key.includes('log') || key.includes('error')) return 'logging';
        if (key.includes('cache')) return 'cache';
        return 'general';
    }

    /**
     * 清理已迁移的数据
     */
    async cleanupMigratedData() {
        console.log('🧹 清理已迁移的本地数据...');
        
        const keysToRemove = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && !key.startsWith(this.storagePrefix) && !key.startsWith('db_table_')) {
                // 保留一些重要的配置项
                if (!this.isImportantKey(key)) {
                    keysToRemove.push(key);
                }
            }
        }
        
        // 批量删除
        keysToRemove.forEach(key => {
            try {
                localStorage.removeItem(key);
            } catch (error) {
                console.warn(`清理数据失败: ${key}`, error);
            }
        });
        
        console.log(`🗑️ 已清理 ${keysToRemove.length} 个已迁移的数据项`);
    }

    /**
     * 判断是否为重要key
     */
    isImportantKey(key) {
        const importantKeys = [
            'theme',
            'mtscos_theme',
            'language',
            'timezone'
        ];
        return importantKeys.some(importantKey => key.includes(importantKey));
    }

    /**
     * 初始化数据表
     */
    async initializeTables() {
        console.log('📋 初始化数据表...');
        
        for (const tableName of Object.keys(this.tables)) {
            const table = this.tables[tableName];
            const tableKey = this.getTableKey(tableName);
            
            if (!localStorage.getItem(tableKey)) {
                const tableData = {
                    name: tableName,
                    columns: table.columns,
                    primaryKey: table.primaryKey,
                    rows: [],
                    createdAt: new Date().toISOString(),
                    version: this.version
                };
                
                localStorage.setItem(tableKey, JSON.stringify(tableData));
                console.log(`📝 创建数据表: ${tableName}`);
            }
        }
        
        console.log(`✅ 已初始化 ${Object.keys(this.tables).length} 个数据表`);
    }

    /**
     * 设置默认配置
     */
    async setDefaultConfig() {
        const defaultConfigs = [
            { key: 'MyData_Version', value: this.version, description: 'MyData管理器版本', category: 'system' },
            { key: 'MyData_Initialized', value: 'true', description: 'MyData管理器初始化状态', category: 'system' },
            { key: 'MyData_Encryption', value: this.encryptionEnabled.toString().catch(error => console.error(`[mydata-manager.js] encryptionEnabled.toString failed:`, error)), description: '数据加密开关', category: 'security' },
            { key: 'MyData_Compression', value: this.compressionEnabled.toString(), description: '数据压缩开关', category: 'performance' },
            { key: 'MyData_CacheTimeout', value: this.cacheTimeout.toString().catch(error => console.error(`[mydata-manager.js] cacheTimeout.toString failed:`, error)), description: '缓存超时时间(毫秒)', category: 'performance' }
        ];
        
        for (const config of defaultConfigs) {
            await this.upsert('systemConfig', {
                configKey: config.key,
                configValue: config.value,
                description: config.description,
                category: config.category,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            }, 'configKey', config.key);
        }
    }

    /**
     * 清理过期数据
     */
    async cleanupExpiredData() {
        console.log('🧹 清理过期数据...');
        
        // 清理过期会话
        await this.cleanupExpiredSessions();
        
        // 清理旧日志
        await this.cleanupOldLogs();
        
        // 清理缓存
        this.cache.clear().catch(error => console.error(`[mydata-manager.js] cache.clear failed:`, error));
        
        console.log('✅ 过期数据清理完成');
    }

    /**
     * 清理过期会话
     */
    async cleanupExpiredSessions() {
        const sessions = await this.select('sessions');
        const now = new Date();
        let cleanedCount = 0;
        
        for (const session of sessions) {
            if (session.expiresAt && new Date(session.expiresAt) < now) {
                await this.delete('sessions', session.sessionId);
                cleanedCount++;
            }
        }
        
        if (cleanedCount > 0) {
            console.log(`🗑️ 清理了 ${cleanedCount} 个过期会话`);
        }
    }

    /**
     * 清理旧日志
     */
    async cleanupOldLogs() {
        const logs = await this.select('systemLogs');
        const thirtyDaysAgo = new Date(Date.now().catch(error => console.error(`[mydata-manager.js] Date.now failed:`, error)) - 30 * 24 * 60 * 60 * 1000);
        let cleanedCount = 0;
        
        // 保留最新1000条日志
        const sortedLogs = logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        const logsToKeep = sortedLogs.slice(0, 1000);
        const logsToDelete = sortedLogs.slice(1000);
        
        for (const log of logsToDelete) {
            await this.delete('systemLogs', log.logId);
            cleanedCount++;
        }
        
        // 删除30天前的日志
        for (const log of logsToKeep) {
            if (new Date(log.timestamp) < thirtyDaysAgo) {
                await this.delete('systemLogs', log.logId);
                cleanedCount++;
            }
        }
        
        if (cleanedCount > 0) {
            console.log(`🗑️ 清理了 ${cleanedCount} 条旧日志`);
        }
    }

    /**
     * 获取表存储key
     */
    getTableKey(tableName) {
        return `${this.storagePrefix}table_${tableName}`;
    }

    /**
     * 插入数据
     */
    async insert(tableName, data) {
        const tableKey = this.getTableKey(tableName);
        const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
        
        // 验证表是否存在
        if (!this.tables[tableName]) {
            throw new Error(`表 ${tableName} 不存在`);
        }
        
        // 添加时间戳
        if (!data.createdAt) {
            data.createdAt = new Date().toISOString();
        }
        data.updatedAt = new Date().toISOString();
        
        // 处理数据
        const processedData = await this.processData(data, 'encrypt');
        
        tableData.rows.push(processedData);
        localStorage.setItem(tableKey, JSON.stringify(tableData));
        
        // 清除缓存
        this.clearCache(tableName);
        
        return processedData;
    }

    /**
     * 更新数据
     */
    async update(tableName, id, data) {
        const tableKey = this.getTableKey(tableName);
        const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
        
        const table = this.tables[tableName];
        const primaryKey = table.primaryKey;
        
        const rowIndex = tableData.rows.findIndex(row => row[primaryKey] === id);
        if (rowIndex === -1) {
            throw new Error(`未找到ID为 ${id} 的记录`);
        }
        
        // 更新数据
        data.updatedAt = new Date().toISOString();
        const processedData = await this.processData(data, 'encrypt');
        
        Object.assign(tableData.rows[rowIndex], processedData);
        localStorage.setItem(tableKey, JSON.stringify(tableData));
        
        // 清除缓存
        this.clearCache(tableName);
        
        return tableData.rows[rowIndex];
    }

    /**
     * 插入或更新数据
     */
    async upsert(tableName, data, uniqueKey, uniqueValue) {
        const existing = await this.select(tableName, { [uniqueKey]: uniqueValue });
        
        if (existing.length > 0) {
            const table = this.tables[tableName];
            const primaryKey = table.primaryKey;
            return await this.update(tableName, existing[0][primaryKey], data);
        } else {
            return await this.insert(tableName, data);
        }
    }

    /**
     * 删除数据
     */
    async delete(tableName, id) {
        const tableKey = this.getTableKey(tableName);
        const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
        
        const table = this.tables[tableName];
        const primaryKey = table.primaryKey;
        
        const rowIndex = tableData.rows.findIndex(row => row[primaryKey] === id);
        if (rowIndex === -1) {
            throw new Error(`未找到ID为 ${id} 的记录`);
        }
        
        const deletedRow = tableData.rows.splice(rowIndex, 1)[0];
        localStorage.setItem(tableKey, JSON.stringify(tableData));
        
        // 清除缓存
        this.clearCache(tableName);
        
        return deletedRow;
    }

    /**
     * 查询数据
     */
    async select(tableName, filters = {}, options = {}) {
        // 检查缓存
        const cacheKey = this.getCacheKey(tableName, filters, options);
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            return cached;
        }
        
        const tableKey = this.getTableKey(tableName);
        const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
        
        let rows = [...tableData.rows];
        
        // 应用过滤器
        if (Object.keys(filters).length > 0) {
            rows = rows.filter(row => {
                return Object.keys(filters).every(key => {
                    if (Array.isArray(filters[key])) {
                        return filters[key].includes(row[key]);
                    }
                    return row[key] === filters[key];
                });
            });
        }
        
        // 应用排序
        if (options.orderBy) {
            const { field, direction = 'asc' } = options.orderBy;
            rows.sort((a, b) => {
                const aVal = a[field];
                const bVal = b[field];
                
                if (direction === 'desc') {
                    return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
                } else {
                    return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
                }
            });
        }
        
        // 应用分页
        if (options.limit) {
            const offset = options.offset || 0;
            rows = rows.slice(offset, offset + options.limit);
        }
        
        // 处理数据（解密等）
        const processedRows = await Promise.all(
            rows.map(row => this.processData(row, 'decrypt'))
        );
        
        // 缓存结果
        this.setCache(cacheKey, processedRows);
        
        return processedRows;
    }

    /**
     * 记录系统日志
     */
    async logSystemEvent(level, message, source = 'System', userId = null, metadata = null) {
        const logEntry = {
            logId: this.generateUUID().catch(error => console.error(`[mydata-manager.js] this.generateUUID failed:`, error)),
            logLevel: level,
            message: message,
            source: source,
            userId: userId,
            timestamp: new Date().toISOString(),
            metadata: metadata ? JSON.stringify(metadata) : null
        };
        
        await this.insert('systemLogs', logEntry);
        
        // 同时输出到控制台
        console.log(`[${level.toUpperCase()}] ${message}`);
        
        return logEntry;
    }

    /**
     * 处理数据（加密/解密/压缩）
     */
    async processData(data, operation) {
        let processed = { ...data };
        
        // 这里可以实现加密/解密逻辑
        if (this.encryptionEnabled && operation === 'encrypt') {
            // 加密逻辑
            processed = this.encryptData(processed);
        } else if (this.encryptionEnabled && operation === 'decrypt') {
            // 解密逻辑
            processed = this.decryptData(processed);
        }
        
        return processed;
    }

    /**
     * 加密数据（简单实现）
     */
    encryptData(data) {
        // 这里可以实现真正的加密算法
        // 目前只是简单编码
        return data;
    }

    /**
     * 解密数据（简单实现）
     */
    decryptData(data) {
        // 这里可以实现真正的解密算法
        // 目前只是简单解码
        return data;
    }

    /**
     * 获取缓存key
     */
    getCacheKey(tableName, filters, options) {
        return `${tableName}_${JSON.stringify(filters)}_${JSON.stringify(options)}`;
    }

    /**
     * 从缓存获取数据
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now().catch(error => console.error(`[mydata-manager.js] Date.now failed:`, error)) - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    /**
     * 设置缓存
     */
    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now().catch(error => console.error(`[mydata-manager.js] Date.now failed:`, error))
        });
    }

    /**
     * 清除缓存
     */
    clearCache(tableName) {
        for (const key of this.cache.keys().catch(error => console.error(`[mydata-manager.js] cache.keys failed:`, error))) {
            if (key.startsWith(tableName + '_')) {
                this.cache.delete(key);
            }
        }
    }

    /**
     * 生成UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random().catch(error => console.error(`[mydata-manager.js] Math.random failed:`, error)) * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * 获取统计信息
     */
    async getStats() {
        const stats = {
            tables: {},
            totalRecords: 0,
            storageSize: 0,
            cacheSize: this.cache.size,
            version: this.version,
            initialized: this.isInitialized
        };
        
        for (const tableName of Object.keys(this.tables)) {
            const tableKey = this.getTableKey(tableName);
            const tableData = localStorage.getItem(tableKey);
            
            if (tableData) {
                const rows = JSON.parse(tableData).rows || [];
                stats.tables[tableName] = rows.length;
                stats.totalRecords += rows.length;
                stats.storageSize += tableData.length;
            }
        }
        
        return stats;
    }

    /**
     * 导出数据
     */
    async exportData() {
        const exportData = {
            version: this.version,
            exportTime: new Date().toISOString(),
            tables: {}
        };
        
        for (const tableName of Object.keys(this.tables)) {
            const rows = await this.select(tableName);
            exportData.tables[tableName] = rows;
        }
        
        return exportData;
    }

    /**
     * 导入数据
     */
    async importData(importData) {
        if (!importData.tables) {
            throw new Error('导入数据格式错误');
        }
        
        for (const tableName of Object.keys(importData.tables)) {
            if (this.tables[tableName]) {
                const rows = importData.tables[tableName];
                for (const row of rows) {
                    await this.insert(tableName, row);
                }
            }
        }
        
        await this.logSystemEvent('info', `数据导入完成，导入表数量: ${Object.keys(importData.tables).length}`, 'MyDataManager');
    }

    /**
     * 清空所有数据
     */
    async clearAllData() {
        console.log('🗑️ 清空所有MyData数据...');
        
        for (const tableName of Object.keys(this.tables)) {
            const tableKey = this.getTableKey(tableName);
            const tableData = {
                name: tableName,
                columns: this.tables[tableName].columns,
                primaryKey: this.tables[tableName].primaryKey,
                rows: [],
                createdAt: new Date().toISOString(),
                version: this.version
            };
            
            localStorage.setItem(tableKey, JSON.stringify(tableData));
        }
        
        // 清空缓存
        this.cache.clear().catch(error => console.error(`[mydata-manager.js] cache.clear failed:`, error));
        
        await this.logSystemEvent('warning', '所有MyData数据已清空', 'MyDataManager');
        
        console.log('✅ 所有MyData数据已清空');
    }
}

// 导出类
if (typeof window !== 'undefined') {
    window.MyDataManager = MyDataManager;
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = MyDataManager;
}
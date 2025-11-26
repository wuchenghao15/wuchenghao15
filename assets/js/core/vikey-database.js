/**
 * Vikey数据库管理模块
 * 负责Vikey信息的数据库存储、查询、更新等操作
 */

class VikeyDatabase {
    constructor() {
        this.dbName = 'MTSCOS_Vikey';
        this.version = 1;
        this.db = null;
        this.initialized = false;
        
        // 表名定义
        this.tables = {
            VIKEY_INFO: 'vikey_info',
            VIKEY_USERS: 'vikey_users',
            VIKEY_LOGS: 'vikey_logs',
            VIKEY_PERMISSIONS: 'vikey_permissions',
            VIKEY_SESSIONS: 'vikey_sessions'
        };

        // 初始化数据库
        this.initializeDatabase();
    }

    /**
     * 初始化数据库
     */
    async initializeDatabase() {
        try {
            // 使用IndexedDB作为本地数据库
            this.db = await this.openIndexedDB();
            
            // 创建表结构
            await this.createTables();
            
            this.initialized = true;
            console.log('Vikey数据库初始化成功');
            
        } catch (error) {
            console.error('Vikey数据库初始化失败:', error);
            throw error;
        }
    }

    /**
     * 打开IndexedDB数据库
     */
    openIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // 创建Vikey信息表
                if (!db.objectStoreNames.contains(this.tables.VIKEY_INFO)) {
                    const vikeyStore = db.createObjectStore(this.tables.VIKEY_INFO, { keyPath: 'id', autoIncrement: true });
                    vikeyStore.createIndex('vikeyId', 'vikeyId', { unique: true });
                    vikeyStore.createIndex('deviceId', 'deviceId', { unique: false });
                    vikeyStore.createIndex('state', 'state', { unique: false });
                    vikeyStore.createIndex('permissionLevel', 'permissionLevel', { unique: false });
                    vikeyStore.createIndex('lastUsed', 'lastUsed', { unique: false });
                }

                // 创建Vikey用户表
                if (!db.objectStoreNames.contains(this.tables.VIKEY_USERS)) {
                    const userStore = db.createObjectStore(this.tables.VIKEY_USERS, { keyPath: 'id', autoIncrement: true });
                    userStore.createIndex('userId', 'userId', { unique: true });
                    userStore.createIndex('vikeyId', 'vikeyId', { unique: false });
                    userStore.createIndex('username', 'username', { unique: true });
                    userStore.createIndex('role', 'role', { unique: false });
                    userStore.createIndex('isActive', 'isActive', { unique: false });
                }

                // 创建Vikey日志表
                if (!db.objectStoreNames.contains(this.tables.VIKEY_LOGS)) {
                    const logStore = db.createObjectStore(this.tables.VIKEY_LOGS, { keyPath: 'id', autoIncrement: true });
                    logStore.createIndex('vikeyId', 'vikeyId', { unique: false });
                    logStore.createIndex('userId', 'userId', { unique: false });
                    logStore.createIndex('action', 'action', { unique: false });
                    logStore.createIndex('timestamp', 'timestamp', { unique: false });
                    logStore.createIndex('level', 'level', { unique: false });
                }

                // 创建Vikey权限表
                if (!db.objectStoreNames.contains(this.tables.VIKEY_PERMISSIONS)) {
                    const permStore = db.createObjectStore(this.tables.VIKEY_PERMISSIONS, { keyPath: 'id', autoIncrement: true });
                    permStore.createIndex('vikeyId', 'vikeyId', { unique: false });
                    permStore.createIndex('permission', 'permission', { unique: false });
                    permStore.createIndex('resource', 'resource', { unique: false });
                }

                // 创建Vikey会话表
                if (!db.objectStoreNames.contains(this.tables.VIKEY_SESSIONS)) {
                    const sessionStore = db.createObjectStore(this.tables.VIKEY_SESSIONS, { keyPath: 'sessionId', unique: true });
                    sessionStore.createIndex('vikeyId', 'vikeyId', { unique: false });
                    sessionStore.createIndex('userId', 'userId', { unique: false });
                    sessionStore.createIndex('startTime', 'startTime', { unique: false });
                    sessionStore.createIndex('lastActivity', 'lastActivity', { unique: false });
                    sessionStore.createIndex('isActive', 'isActive', { unique: false });
                }
            };
        });
    }

    /**
     * 创建表结构（兼容服务器端数据库）
     */
    async createTables() {
        // 这里可以添加服务器端数据库表的创建逻辑
        // 例如通过API调用创建MySQL/PostgreSQL表
    }

    /**
     * 插入Vikey信息
     * @param {Object} vikeyInfo - Vikey信息
     * @returns {Promise<Object>} 插入结果
     */
    async insertVikeyInfo(vikeyInfo) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_INFO], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_INFO);

            // 准备插入数据
            const data = {
                vikeyId: vikeyInfo.vikeyId,
                vikeyName: vikeyInfo.vikeyName || '',
                deviceId: vikeyInfo.deviceId || '',
                version: vikeyInfo.version || '',
                serialNumber: vikeyInfo.serialNumber || '',
                permissionLevel: vikeyInfo.permissionLevel || 1,
                validFrom: vikeyInfo.validFrom || null,
                validTo: vikeyInfo.validTo || null,
                state: vikeyInfo.state || 1,
                signature: vikeyInfo.signature || '',
                customData: vikeyInfo.customData || '',
                lastUsed: new Date().toISOString(),
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };

            return new Promise((resolve, reject) => {
                const request = store.add(data);
                
                request.onsuccess = () => {
                    // 同步到服务器数据库
                    this.syncToServer('INSERT', 'vikey_info', data);
                    resolve({ success: true, id: request.result, data: data });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('插入Vikey信息失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 更新Vikey信息
     * @param {number} id - 记录ID
     * @param {Object} updateData - 更新数据
     * @returns {Promise<Object>} 更新结果
     */
    async updateVikeyInfo(id, updateData) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_INFO], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_INFO);

            return new Promise((resolve, reject) => {
                const getRequest = store.get(id);
                
                getRequest.onsuccess = () => {
                    const existingData = getRequest.result;
                    if (!existingData) {
                        reject(new Error('Vikey信息不存在'));
                        return;
                    }

                    // 更新数据
                    const updatedData = {
                        ...existingData,
                        ...updateData,
                        updatedAt: new Date().toISOString()
                    };

                    const updateRequest = store.put(updatedData);
                    
                    updateRequest.onsuccess = () => {
                        // 同步到服务器数据库
                        this.syncToServer('UPDATE', 'vikey_info', updatedData);
                        resolve({ success: true, data: updatedData });
                    };
                    
                    updateRequest.onerror = () => reject(updateRequest.error);
                };
                
                getRequest.onerror = () => reject(getRequest.error);
            });

        } catch (error) {
            console.error('更新Vikey信息失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 根据VikeyID查询信息
     * @param {string} vikeyId - VikeyID
     * @returns {Promise<Object>} 查询结果
     */
    async getVikeyInfoById(vikeyId) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_INFO], 'readonly');
            const store = transaction.objectStore(this.tables.VIKEY_INFO);
            const index = store.index('vikeyId');

            return new Promise((resolve, reject) => {
                const request = index.get(vikeyId);
                
                request.onsuccess = () => {
                    resolve({ success: true, data: request.result });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('查询Vikey信息失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 获取所有Vikey信息
     * @param {Object} filters - 过滤条件
     * @returns {Promise<Object>} 查询结果
     */
    async getAllVikeyInfo(filters = {}) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_INFO], 'readonly');
            const store = transaction.objectStore(this.tables.VIKEY_INFO);

            return new Promise((resolve, reject) => {
                const request = store.getAll();
                
                request.onsuccess = () => {
                    let results = request.result || [];
                    
                    // 应用过滤条件
                    if (filters.state !== undefined) {
                        results = results.filter(item => item.state === filters.state);
                    }
                    if (filters.permissionLevel !== undefined) {
                        results = results.filter(item => item.permissionLevel === filters.permissionLevel);
                    }
                    if (filters.isActive !== undefined) {
                        const now = new Date();
                        results = results.filter(item => {
                            if (!item.validFrom || !item.validTo) return true;
                            const validFrom = new Date(item.validFrom);
                            const validTo = new Date(item.validTo);
                            return now >= validFrom && now <= validTo;
                        });
                    }
                    
                    resolve({ success: true, data: results });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('获取所有Vikey信息失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 删除Vikey信息
     * @param {number} id - 记录ID
     * @returns {Promise<Object>} 删除结果
     */
    async deleteVikeyInfo(id) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_INFO], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_INFO);

            return new Promise((resolve, reject) => {
                const getRequest = store.get(id);
                
                getRequest.onsuccess = () => {
                    const existingData = getRequest.result;
                    if (!existingData) {
                        reject(new Error('Vikey信息不存在'));
                        return;
                    }

                    const deleteRequest = store.delete(id);
                    
                    deleteRequest.onsuccess = () => {
                        // 同步到服务器数据库
                        this.syncToServer('DELETE', 'vikey_info', { id: id });
                        resolve({ success: true, deletedData: existingData });
                    };
                    
                    deleteRequest.onerror = () => reject(deleteRequest.error);
                };
                
                getRequest.onerror = () => reject(getRequest.error);
            });

        } catch (error) {
            console.error('删除Vikey信息失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 插入Vikey用户关联
     * @param {Object} userData - 用户数据
     * @returns {Promise<Object>} 插入结果
     */
    async insertVikeyUser(userData) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_USERS], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_USERS);

            const data = {
                userId: userData.userId,
                vikeyId: userData.vikeyId,
                username: userData.username,
                role: userData.role || 'user',
                isActive: userData.isActive !== false,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };

            return new Promise((resolve, reject) => {
                const request = store.add(data);
                
                request.onsuccess = () => {
                    this.syncToServer('INSERT', 'vikey_users', data);
                    resolve({ success: true, id: request.result, data: data });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('插入Vikey用户关联失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 记录Vikey操作日志
     * @param {Object} logData - 日志数据
     * @returns {Promise<Object>} 记录结果
     */
    async logVikeyAction(logData) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_LOGS], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_LOGS);

            const data = {
                vikeyId: logData.vikeyId || '',
                userId: logData.userId || '',
                action: logData.action,
                details: logData.details || '',
                level: logData.level || 'info',
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                ipAddress: logData.ipAddress || ''
            };

            return new Promise((resolve, reject) => {
                const request = store.add(data);
                
                request.onsuccess = () => {
                    this.syncToServer('INSERT', 'vikey_logs', data);
                    resolve({ success: true, id: request.result, data: data });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('记录Vikey日志失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 获取Vikey操作日志
     * @param {Object} filters - 过滤条件
     * @param {number} limit - 限制数量
     * @returns {Promise<Object>} 查询结果
     */
    async getVikeyLogs(filters = {}, limit = 100) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_LOGS], 'readonly');
            const store = transaction.objectStore(this.tables.VIKEY_LOGS);

            return new Promise((resolve, reject) => {
                const request = store.getAll();
                
                request.onsuccess = () => {
                    let results = request.result || [];
                    
                    // 应用过滤条件
                    if (filters.vikeyId) {
                        results = results.filter(item => item.vikeyId === filters.vikeyId);
                    }
                    if (filters.userId) {
                        results = results.filter(item => item.userId === filters.userId);
                    }
                    if (filters.action) {
                        results = results.filter(item => item.action === filters.action);
                    }
                    if (filters.level) {
                        results = results.filter(item => item.level === filters.level);
                    }
                    if (filters.startTime) {
                        const startTime = new Date(filters.startTime);
                        results = results.filter(item => new Date(item.timestamp) >= startTime);
                    }
                    if (filters.endTime) {
                        const endTime = new Date(filters.endTime);
                        results = results.filter(item => new Date(item.timestamp) <= endTime);
                    }
                    
                    // 按时间倒序排列
                    results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                    
                    // 限制数量
                    if (limit > 0) {
                        results = results.slice(0, limit);
                    }
                    
                    resolve({ success: true, data: results });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('获取Vikey日志失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 创建Vikey会话
     * @param {Object} sessionData - 会话数据
     * @returns {Promise<Object>} 创建结果
     */
    async createVikeySession(sessionData) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_SESSIONS], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_SESSIONS);

            const sessionId = this.generateSessionId();
            const now = new Date().toISOString();

            const data = {
                sessionId: sessionId,
                vikeyId: sessionData.vikeyId,
                userId: sessionData.userId,
                startTime: now,
                lastActivity: now,
                isActive: true,
                userAgent: navigator.userAgent,
                ipAddress: sessionData.ipAddress || ''
            };

            return new Promise((resolve, reject) => {
                const request = store.add(data);
                
                request.onsuccess = () => {
                    this.syncToServer('INSERT', 'vikey_sessions', data);
                    resolve({ success: true, sessionId: sessionId, data: data });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('创建Vikey会话失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 更新会话活动时间
     * @param {string} sessionId - 会话ID
     * @returns {Promise<Object>} 更新结果
     */
    async updateSessionActivity(sessionId) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_SESSIONS], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_SESSIONS);

            return new Promise((resolve, reject) => {
                const getRequest = store.get(sessionId);
                
                getRequest.onsuccess = () => {
                    const session = getRequest.result;
                    if (!session) {
                        reject(new Error('会话不存在'));
                        return;
                    }

                    session.lastActivity = new Date().toISOString();

                    const updateRequest = store.put(session);
                    
                    updateRequest.onsuccess = () => {
                        this.syncToServer('UPDATE', 'vikey_sessions', session);
                        resolve({ success: true, data: session });
                    };
                    
                    updateRequest.onerror = () => reject(updateRequest.error);
                };
                
                getRequest.onerror = () => reject(getRequest.error);
            });

        } catch (error) {
            console.error('更新会话活动失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 结束Vikey会话
     * @param {string} sessionId - 会话ID
     * @returns {Promise<Object>} 结束结果
     */
    async endVikeySession(sessionId) {
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_SESSIONS], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_SESSIONS);

            return new Promise((resolve, reject) => {
                const getRequest = store.get(sessionId);
                
                getRequest.onsuccess = () => {
                    const session = getRequest.result;
                    if (!session) {
                        reject(new Error('会话不存在'));
                        return;
                    }

                    session.isActive = false;
                    session.endTime = new Date().toISOString();

                    const updateRequest = store.put(session);
                    
                    updateRequest.onsuccess = () => {
                        this.syncToServer('UPDATE', 'vikey_sessions', session);
                        resolve({ success: true, data: session });
                    };
                    
                    updateRequest.onerror = () => reject(updateRequest.error);
                };
                
                getRequest.onerror = () => reject(getRequest.error);
            });

        } catch (error) {
            console.error('结束Vikey会话失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 同步数据到服务器
     * @param {string} action - 操作类型
     * @param {string} table - 表名
     * @param {Object} data - 数据
     */
    async syncToServer(action, table, data) {
        try {
            // 这里实现服务器同步逻辑
            // 可以通过API调用将数据同步到服务器数据库
            const response = await fetch('/api/vikey/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    table: table,
                    data: data,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                console.warn('数据同步到服务器失败:', await response.text());
            }

        } catch (error) {
            console.warn('数据同步到服务器出错:', error);
        }
    }

    /**
     * 生成会话ID
     * @returns {string} 会话ID
     */
    generateSessionId() {
        return 'vikey_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 清理过期会话
     * @param {number} maxAge - 最大会话时间（毫秒）
     * @returns {Promise<Object>} 清理结果
     */
    async cleanupExpiredSessions(maxAge = 24 * 60 * 60 * 1000) { // 默认24小时
        try {
            const transaction = this.db.transaction([this.tables.VIKEY_SESSIONS], 'readwrite');
            const store = transaction.objectStore(this.tables.VIKEY_SESSIONS);

            return new Promise((resolve, reject) => {
                const request = store.getAll();
                
                request.onsuccess = () => {
                    const sessions = request.result || [];
                    const now = new Date();
                    let cleanedCount = 0;

                    sessions.forEach(session => {
                        const lastActivity = new Date(session.lastActivity);
                        const age = now - lastActivity;
                        
                        if (age > maxAge && session.isActive) {
                            session.isActive = false;
                            session.endTime = now.toISOString();
                            store.put(session);
                            cleanedCount++;
                        }
                    });

                    resolve({ success: true, cleanedCount: cleanedCount });
                };
                
                request.onerror = () => reject(request.error);
            });

        } catch (error) {
            console.error('清理过期会话失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 获取数据库统计信息
     * @returns {Promise<Object>} 统计信息
     */
    async getDatabaseStats() {
        try {
            const stats = {
                vikeyCount: 0,
                userCount: 0,
                logCount: 0,
                activeSessionCount: 0,
                lastSyncTime: null
            };

            // 获取Vikey数量
            const vikeyResult = await this.getAllVikeyInfo();
            if (vikeyResult.success) {
                stats.vikeyCount = vikeyResult.data.length;
            }

            // 获取活跃会话数量
            const sessionTransaction = this.db.transaction([this.tables.VIKEY_SESSIONS], 'readonly');
            const sessionStore = sessionTransaction.objectStore(this.tables.VIKEY_SESSIONS);
            
            stats.activeSessionCount = await new Promise((resolve) => {
                const request = sessionStore.getAll();
                request.onsuccess = () => {
                    const sessions = request.result || [];
                    const activeCount = sessions.filter(s => s.isActive).length;
                    resolve(activeCount);
                };
                request.onerror = () => resolve(0);
            });

            return { success: true, stats: stats };

        } catch (error) {
            console.error('获取数据库统计失败:', error);
            return { success: false, error: error.message };
        }
    }
}

// 创建全局实例
const vikeyDatabase = new VikeyDatabase();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VikeyDatabase;
} else {
    window.VikeyDatabase = VikeyDatabase;
    window.vikeyDatabase = vikeyDatabase;
}
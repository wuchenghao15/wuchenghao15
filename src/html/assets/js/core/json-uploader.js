/**
 * MTSCOS AI System - JSON数据上传管理器
 * 版本: 1.0.0
 * 描述: 批量上传JSON数据到IndexedDB数据库
 */

class JSONDataUploader {
    constructor() {
        this.uploadQueue = [];
        this.uploading = false;
        this.stats = {
            total: 0,
            success: 0,
            failed: 0,
            collections: {}
        };
        this.init();
    }
    
    async init() {
        console.log('📤 JSON数据上传管理器已就绪');
        await this.waitForDatabase();
    }
    
    async waitForDatabase() {
        return new Promise((resolve) => {
            if (window.mtscos && window.mtscos.modules && window.mtscos.modules.database) {
                if (window.mtscos.modules.database.isReady) {
                    resolve();
                } else {
                    document.addEventListener('mtscos:database:ready', resolve, { once: true });
                }
            } else {
                document.addEventListener('mtscos:database:ready', resolve, { once: true });
            }
        });
    }
    
    /**
     * 批量上传JSON文件到数据库
     */
    async uploadAll() {
        const jsonFiles = [
            {
                name: '系统配置',
                path: 'config/system-config.json',
                collection: 'system_settings',
                mapping: this.mapSystemConfig
            },
            {
                name: '系统版本',
                path: 'config/system-version.json',
                collection: 'version_history',
                mapping: this.mapVersionHistory
            },
            {
                name: '升级记录',
                path: 'config/upgrade-record.json',
                collection: 'system_state',
                mapping: this.mapUpgradeRecord
            },
            {
                name: 'AI员工',
                path: 'config/ai-employees.json',
                collection: 'ai_employee_data',
                mapping: this.mapAIEmployees
            },
            {
                name: '端口配置',
                path: 'config/port_config.json',
                collection: 'system_settings',
                mapping: this.mapPortConfig
            }
        ];
        
        // 等待数据库就绪
        await this.waitForDatabaseReady();
        
        this.stats.total = jsonFiles.length;
        console.log(`📤 开始上传 ${jsonFiles.length} 个JSON文件到数据库...`);
        
        for (const file of jsonFiles) {
            try {
                await this.uploadFile(file);
                this.stats.success++;
            } catch (error) {
                this.stats.failed++;
                console.error(`❌ 上传失败: ${file.name}`, error.message);
            }
        }
        
        console.log('📊 上传统计:', this.stats);
        return this.stats;
    }
    
    async waitForDatabaseReady(maxAttempts = 30) {
        for (let i = 0; i < maxAttempts; i++) {
            const db = this.getDatabase();
            if (db && db.isReady) {
                // 验证数据库有可用的集合
                if (db.db) {
                    try {
                        const collections = Array.from(db.db.objectStoreNames || []);
                        if (collections.length > 0) {
                            console.log('✅ 数据库就绪，可用集合:', collections.length);
                            return true;
                        }
                    } catch (e) {
                        // 继续等待
                    }
                }
            }
            await new Promise(r => setTimeout(r, 500));
        }
        console.warn('⚠️ 数据库就绪等待超时，继续尝试');
        return false;
    }
    
    async uploadFile(file) {
        console.log(`📤 上传中: ${file.name} (${file.path})`);
        
        // 获取JSON数据
        const response = await fetch(file.path);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // 映射数据
        const items = file.mapping.call(this, data);
        
        // 上传到对应集合
        const db = this.getDatabase();
        
        // 先检查集合是否存在
        try {
            const storeNames = Array.from(db.db?.objectStoreNames || []);
            if (!storeNames.includes(file.collection)) {
                console.warn(`⚠️ 集合不存在: ${file.collection}，跳过`);
                return;
            }
        } catch (e) {
            // 忽略检查错误，继续尝试
        }
        
        for (const item of items) {
            // 兜底：确保item有id字段（keyPath要求）
            if (!item.id) {
                item.id = `${file.collection}_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
            }
            
            try {
                await db.add(file.collection, item);
                this.stats.collections[file.collection] = (this.stats.collections[file.collection] || 0) + 1;
            } catch (error) {
                // 已存在则更新
                if (error.name === 'ConstraintError') {
                    try {
                        await db.put(file.collection, item);
                    } catch (e2) {
                        // 忽略
                    }
                } else if (error.name === 'NotFoundError') {
                    console.warn(`⚠️ 集合 ${file.collection} 不存在，跳过该条记录`);
                    return;
                } else if (error.name === 'DataError' || /key path/i.test(error.message || '')) {
                    // keyPath问题：尝试用put并指定key
                    console.warn(`⚠️ 记录缺少keyPath，尝试put: ${item.id || 'unknown'}`);
                    try {
                        await db.put(file.collection, { ...item, id: item.id });
                    } catch (e3) {
                        console.warn(`⚠️ put失败: ${e3.message}`);
                    }
                } else {
                    throw error;
                }
            }
        }
        
        console.log(`✅ ${file.name} 上传完成: ${items.length} 条记录`);
    }
    
    getDatabase() {
        if (window.mtscos && window.mtscos.modules && window.mtscos.modules.database) {
            return window.mtscos.modules.database;
        }
        if (window.brain) {
            return window.brain;
        }
        throw new Error('数据库未就绪');
    }
    
    // ==================== 数据映射 ====================
    
    mapSystemConfig(data) {
        const items = [];
        const timestamp = Date.now();
        
        // 系统基本信息
        items.push({
            id: 'system_info',
            type: 'system',
            key: 'system_info',
            value: data.system || {},
            timestamp,
            source: 'config/system-config.json'
        });
        
        // AI员工信息
        if (data.ai_employees) {
            data.ai_employees.forEach(emp => {
                items.push({
                    id: `ai_employee_${emp.id}`,
                    type: 'ai_employee',
                    key: emp.id,
                    value: emp,
                    timestamp,
                    source: 'config/system-config.json'
                });
            });
        }
        
        // 规则
        if (data.rules) {
            Object.entries(data.rules).forEach(([category, rules]) => {
                rules.forEach(rule => {
                    items.push({
                        id: `rule_${rule.id}`,
                        type: 'rule',
                        category,
                        key: rule.id,
                        value: rule,
                        timestamp,
                        source: 'config/system-config.json'
                    });
                });
            });
        }
        
        // 权限角色
        if (data.permissions && data.permissions.roles) {
            data.permissions.roles.forEach(role => {
                items.push({
                    id: `role_${role.id}`,
                    type: 'role',
                    key: role.id,
                    value: role,
                    timestamp,
                    source: 'config/system-config.json'
                });
            });
        }
        
        // 子系统
        if (data.subsystems) {
            Object.entries(data.subsystems).forEach(([id, sub]) => {
                items.push({
                    id: `subsystem_${id}`,
                    type: 'subsystem',
                    key: id,
                    value: sub,
                    timestamp,
                    source: 'config/system-config.json'
                });
            });
        }
        
        return items;
    }
    
    mapVersionHistory(data) {
        const items = [];
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 8);
        
        // 当前版本
        if (data.system) {
            const version = data.system.version || '1.0';
            items.push({
                id: `version_${version}_${timestamp}_${random}`,
                type: 'version',
                key: version,
                value: data.system,
                timestamp,
                source: 'config/system-version.json'
            });
        }
        
        // 功能版本
        if (data.features) {
            Object.entries(data.features).forEach(([id, mod]) => {
                items.push({
                    id: `feature_${id}_${timestamp}_${random}`,
                    type: 'feature_version',
                    key: id,
                    value: mod,
                    timestamp,
                    source: 'config/system-version.json'
                });
            });
        }
        
        // 模块版本
        if (data.modules) {
            Object.entries(data.modules).forEach(([id, mod]) => {
                items.push({
                    id: `module_${id}_${timestamp}_${random}`,
                    type: 'module_version',
                    key: id,
                    value: mod,
                    timestamp,
                    source: 'config/system-version.json'
                });
            });
        }
        
        return items;
    }
    
    mapUpgradeRecord(data) {
        const items = [];
        const timestamp = Date.now();
        
        items.push({
            id: data.upgrade_id || `upgrade_${timestamp}`,
            type: 'upgrade',
            key: data.upgrade_id,
            value: data,
            timestamp: new Date(data.date).getTime() || timestamp,
            source: 'config/upgrade-record.json'
        });
        
        return items;
    }
    
    mapAIEmployees(data) {
        const items = [];
        const timestamp = Date.now();
        
        if (data.employees) {
            data.employees.forEach(emp => {
                items.push({
                    id: `ai_emp_detail_${emp.id}`,
                    type: 'ai_employee_detail',
                    key: emp.id,
                    value: emp,
                    timestamp,
                    source: 'config/ai-employees.json'
                });
            });
        }
        
        return items;
    }
    
    mapPortConfig(data) {
        const items = [];
        const timestamp = Date.now();
        
        items.push({
            id: 'port_config',
            type: 'config',
            key: 'port',
            value: data,
            timestamp,
            source: 'config/port_config.json'
        });
        
        return items;
    }
    
    /**
     * 获取上传统计
     */
    getStats() {
        return this.stats;
    }
    
    /**
     * 手动上传单个文件
     */
    async uploadOne(name, path, collection) {
        await this.uploadFile({ name, path, collection, mapping: (d) => [d] });
        return this.stats;
    }
}

// 导出
if (typeof window !== 'undefined') {
    window.JSONDataUploader = JSONDataUploader;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JSONDataUploader;
}

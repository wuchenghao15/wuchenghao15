/**
 * MTSCOS AI System - 数据库信息查看器
 * 版本: 1.0.0
 * 描述: 在后台控制台显示所有数据库信息
 */

class DatabaseInfoViewer {
    constructor() {
        this.databases = [];
        this.init();
    }
    
    async init() {
        // 等待所有数据库就绪
        await this.waitForDatabases();
        // 收集信息
        await this.collectInfo();
        // 在控制台显示
        this.displayInfo();
    }
    
    async waitForDatabases() {
        return new Promise((resolve) => {
            let count = 0;
            const checkInterval = setInterval(() => {
                count++;
                if (count > 30) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
        });
    }
    
    async collectInfo() {
        const info = {
            timestamp: new Date().toISOString(),
            system: 'MTSCOS AI v4.4.0',
            databases: {}
        };
        
        // 1. 主数据库
        if (window.mtscos?.modules?.database) {
            const db = window.mtscos.modules.database;
            info.databases.main = {
                name: db.dbName || 'MTSCOS_DB',
                version: db.dbVersion || 1,
                status: db.isReady ? 'ready' : 'initializing',
                collections: []
            };
            
            if (db.collections) {
                for (const col of db.collections) {
                    try {
                        const count = await db.transaction(col.name, 'readonly', (store) => store.count());
                        info.databases.main.collections.push({
                            name: col.name,
                            keyPath: col.keyPath,
                            records: count
                        });
                    } catch (e) {
                        info.databases.main.collections.push({
                            name: col.name,
                            keyPath: col.keyPath,
                            records: 0
                        });
                    }
                }
            }
        }
        
        // 2. 加密数据库
        if (window.encryptedDB) {
            const db = window.encryptedDB;
            const stats = await db.getStats();
            info.databases.encrypted = {
                name: db.dbName,
                version: db.dbVersion,
                status: db.isReady ? 'ready' : 'initializing',
                encryption: {
                    algorithm: db.encryption?.algorithm || 'AES-GCM',
                    keyLength: db.encryption?.keyLength || 256
                },
                collections: Object.entries(stats).map(([name, data]) => ({
                    name,
                    records: data.count || 0,
                    encrypted: data.encrypted || false
                }))
            };
        }
        
        // 3. 脑库数据库
        if (window.brain) {
            const brainStats = await window.brain.getStats();
            info.databases.brain = {
                name: window.brain.dbName,
                version: window.brain.dbVersion,
                status: window.brain.isReady ? 'ready' : 'initializing',
                collections: window.brain.collections.map(c => ({
                    name: c.name,
                    keyPath: c.keyPath
                })),
                stats: brainStats
            };
        }
        
        this.databases = info;
    }
    
    displayInfo() {
        const info = this.databases;
        
        console.log('\n');
        console.log('%c╔══════════════════════════════════════════════════════════╗', 'color: #3b82f6; font-weight: bold;');
        console.log('%c║                                                          ║', 'color: #3b82f6; font-weight: bold;');
        console.log('%c║           MTSCOS AI System - 数据库信息面板              ║', 'color: #3b82f6; font-weight: bold;');
        console.log('%c║                  v4.4.0 例行维护升级版                  ║', 'color: #3b82f6; font-weight: bold;');
        console.log('%c║                                                          ║', 'color: #3b82f6; font-weight: bold;');
        console.log('%c╚══════════════════════════════════════════════════════════╝', 'color: #3b82f6; font-weight: bold;');
        console.log(`📅 报告时间: ${info.timestamp}\n`);
        
        // 显示每个数据库
        Object.entries(info.databases).forEach(([key, db]) => {
            this.displayDatabase(key, db);
        });
        
        // 显示汇总
        this.displaySummary(info);
        
        // 显示使用提示
        this.displayHints();
    }
    
    displayDatabase(key, db) {
        const titles = {
            main: '📦 主数据库 (MTSCOS_DB)',
            encrypted: '🔐 加密数据库 (MTSCOS_ENCRYPTED_DB)',
            brain: '🧠 脑库数据库 (MTSCOS_BRAIN_DB)'
        };
        
        const title = titles[key] || `📦 ${db.name}`;
        const statusIcon = db.status === 'ready' ? '✅' : '⏳';
        const statusColor = db.status === 'ready' ? '#22c55e' : '#f59e0b';
        
        console.log(`\n%c${title} ${statusIcon}`, `color: ${statusColor}; font-weight: bold; font-size: 14px;`);
        console.log('%c─'.repeat(60), 'color: #64748b;');
        console.log(`   名称: ${db.name}`);
        console.log(`   版本: v${db.version}`);
        console.log(`   状态: ${db.status === 'ready' ? '✅ 就绪' : '⏳ 初始化中'}`);
        
        if (db.encryption) {
            console.log(`   🔒 加密: ${db.encryption.algorithm} (${db.encryption.keyLength}位)`);
        }
        
        if (db.collections && db.collections.length > 0) {
            console.log(`\n   📋 数据集合 (${db.collections.length}个):`);
            
            const totalRecords = db.collections.reduce((sum, c) => sum + (c.records || 0), 0);
            
            db.collections.forEach((col, i) => {
                const encryptedIcon = col.encrypted ? '🔒' : '📂';
                const count = col.records !== undefined ? col.records : 0;
                const countStr = count.toString().padStart(4, ' ');
                console.log(`      ${encryptedIcon} ${col.name.padEnd(25, ' ')} [${countStr} 条]  key: ${col.keyPath}`);
            });
            
            console.log(`\n   📊 总记录数: ${totalRecords} 条`);
        }
    }
    
    displaySummary(info) {
        console.log('\n%c╔══════════════════════════════════════════════════════════╗', 'color: #a855f7; font-weight: bold;');
        console.log('%c║                       📊 汇总信息                        ║', 'color: #a855f7; font-weight: bold;');
        console.log('%c╚══════════════════════════════════════════════════════════╝', 'color: #a855f7; font-weight: bold;');
        
        let totalCollections = 0;
        let totalRecords = 0;
        let encryptedCollections = 0;
        let dbCount = 0;
        
        Object.values(info.databases).forEach(db => {
            dbCount++;
            if (db.collections) {
                totalCollections += db.collections.length;
                db.collections.forEach(col => {
                    totalRecords += col.records || 0;
                    if (col.encrypted) encryptedCollections++;
                });
            }
        });
        
        console.log(`   📦 数据库数量:     ${dbCount}`);
        console.log(`   📋 数据集合总数:   ${totalCollections}`);
        console.log(`   📊 记录总数:       ${totalRecords} 条`);
        console.log(`   🔒 加密集合:       ${encryptedCollections}`);
        console.log(`   📂 普通集合:       ${totalCollections - encryptedCollections}`);
        console.log(`   🛡️ 加密率:        ${((encryptedCollections / totalCollections) * 100).toFixed(1)}%`);
    }
    
    displayHints() {
        console.log('\n%c╔══════════════════════════════════════════════════════════╗', 'color: #14b8a6; font-weight: bold;');
        console.log('%c║                     💡 使用提示                          ║', 'color: #14b8a6; font-weight: bold;');
        console.log('%c╚══════════════════════════════════════════════════════════╝', 'color: #14b8a6; font-weight: bold;');
        console.log('   📊 实时统计:    dbViewer.showStats()');
        console.log('   📋 集合列表:    dbViewer.listCollections()');
        console.log('   🔍 查看数据:    dbViewer.showCollection("集合名")');
        console.log('   🔐 加密状态:    dbViewer.showEncryption()');
        console.log('   🏥 健康检查:    dbViewer.healthCheck()');
        console.log('   📤 导出数据:    dbViewer.exportData()');
        console.log('   🔄 刷新信息:    dbViewer.refresh()');
    }
    
    // ==================== 交互方法 ====================
    
    async showStats() {
        await this.refresh();
        const info = this.databases;
        console.log('\n%c📊 实时统计信息', 'color: #3b82f6; font-weight: bold; font-size: 14px;');
        console.log('%c─'.repeat(60), 'color: #64748b;');
        
        Object.entries(info.databases).forEach(([key, db]) => {
            if (db.collections) {
                const total = db.collections.reduce((s, c) => s + (c.records || 0), 0);
                console.log(`   ${db.name}: ${db.collections.length}集合, ${total}记录`);
            }
        });
    }
    
    async listCollections() {
        await this.refresh();
        const info = this.databases;
        console.log('\n%c📋 集合列表', 'color: #3b82f6; font-weight: bold; font-size: 14px;');
        console.log('%c─'.repeat(60), 'color: #64748b;');
        
        Object.entries(info.databases).forEach(([key, db]) => {
            console.log(`\n   📦 ${db.name}:`);
            if (db.collections) {
                db.collections.forEach(col => {
                    const icon = col.encrypted ? '🔒' : '📂';
                    console.log(`      ${icon} ${col.name} (${col.records || 0}条)`);
                });
            }
        });
    }
    
    async showCollection(name) {
        console.log(`\n%c🔍 集合详情: ${name}`, 'color: #3b82f6; font-weight: bold; font-size: 14px;');
        console.log('%c─'.repeat(60), 'color: #64748b;');
        
        // 尝试从各个数据库读取
        for (const [key, db] of Object.entries(this.databases.databases)) {
            if (db.collections) {
                const col = db.collections.find(c => c.name === name);
                if (col) {
                    console.log(`   来自: ${db.name}`);
                    console.log(`   记录数: ${col.records || 0}`);
                    
                    try {
                        let data = [];
                        if (key === 'main' && window.mtscos?.modules?.database) {
                            data = await window.mtscos.modules.database.getAll(name);
                        } else if (key === 'encrypted' && window.encryptedDB) {
                            data = await window.encryptedDB.getAll(name);
                        } else if (key === 'brain' && window.brain) {
                            data = await window.brain.getAll(name);
                        }
                        
                        if (data && data.length > 0) {
                            console.log(`\n   📄 前5条记录:`);
                            data.slice(0, 5).forEach((item, i) => {
                                console.log(`      [${i + 1}] ${JSON.stringify(item).substring(0, 150)}${JSON.stringify(item).length > 150 ? '...' : ''}`);
                            });
                        }
                    } catch (e) {
                        console.log(`   ⚠️ 读取失败: ${e.message}`);
                    }
                    return;
                }
            }
        }
        
        console.log(`   ❌ 未找到集合: ${name}`);
    }
    
    async showEncryption() {
        console.log('\n%c🔐 加密状态', 'color: #a855f7; font-weight: bold; font-size: 14px;');
        console.log('%c─'.repeat(60), 'color: #64748b;');
        
        Object.values(this.databases.databases).forEach(db => {
            if (db.collections) {
                const encrypted = db.collections.filter(c => c.encrypted).length;
                const total = db.collections.length;
                console.log(`\n   📦 ${db.name}:`);
                console.log(`      总集合: ${total}`);
                console.log(`      加密: ${encrypted}`);
                console.log(`      普通: ${total - encrypted}`);
                console.log(`      加密率: ${((encrypted / total) * 100).toFixed(1)}%`);
                
                if (db.encryption) {
                    console.log(`      算法: ${db.encryption.algorithm}`);
                    console.log(`      密钥: ${db.encryption.keyLength}位`);
                }
            }
        });
    }
    
    async healthCheck() {
        console.log('\n%c🏥 健康检查', 'color: #22c55e; font-weight: bold; font-size: 14px;');
        console.log('%c─'.repeat(60), 'color: #64748b;');
        
        if (window.mtscos?.modules?.database) {
            const health = await window.mtscos.modules.database.healthCheck();
            console.log('   主数据库:', health);
        }
        
        if (window.encryptedDB) {
            const health = await window.encryptedDB.healthCheck();
            console.log('   加密数据库:', health);
        }
        
        if (window.brain) {
            const health = await window.brain.healthCheck();
            console.log('   脑库数据库:', health);
        }
    }
    
    async exportData() {
        console.log('\n%c📤 导出数据', 'color: #3b82f6; font-weight: bold; font-size: 14px;');
        console.log('%c─'.repeat(60), 'color: #64748b;');
        
        const exportData = {
            exported_at: new Date().toISOString(),
            databases: {}
        };
        
        if (window.mtscos?.modules?.database) {
            for (const col of window.mtscos.modules.database.collections || []) {
                try {
                    exportData.databases[col.name] = await window.mtscos.modules.database.getAll(col.name);
                } catch (e) {}
            }
        }
        
        if (window.encryptedDB) {
            const stats = await window.encryptedDB.getStats();
            exportData.databases.encrypted = stats;
        }
        
        if (window.brain) {
            const stats = await window.brain.getStats();
            exportData.databases.brain = stats;
        }
        
        localStorage.setItem('mtscos_db_export', JSON.stringify(exportData));
        console.log('   ✅ 数据已导出到 localStorage.mtscos_db_export');
        console.log('   📊 导出大小:', JSON.stringify(exportData).length, '字节');
    }
    
    async refresh() {
        await this.collectInfo();
        console.log('%c🔄 数据库信息已刷新', 'color: #22c55e;');
    }
}

// 导出
if (typeof window !== 'undefined') {
    window.DatabaseInfoViewer = DatabaseInfoViewer;
}

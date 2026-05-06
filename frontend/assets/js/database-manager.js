/**
 * MSSQL数据库管理器
 * 负责数据库连接、表维护和系统因子管理
 */

class DatabaseManager {
    constructor() {
        this.connection = null;
        this.config = {
            host: 'wuchenghao15.net',
            port: 33693,
            username: 'sa',
            password: 'LoginMe15',
            database: 'MyData',
            type: 'MSSQL',
            options: {
                encrypt: false,
                trustServerCertificate: true,
                enableArithAbort: true,
                connectionTimeout: 30000,
                requestTimeout: 30000
            }
        };
        this.isConnected = false;
        this.connectionPool = [];
        this.maxPoolSize = 10;
        this.systemTables = new Map();
    }

    /**
     * 初始化数据库连接
     */
    async initialize() {
        try {
            console.log('🗄️ 初始化MSSQL数据库连接...');
            
            // 验证配置
            this.validateConfig();
            
            // 在浏览器环境中使用模拟连接
            if (typeof window !== 'undefined') {
                await this.initializeMockConnection();
            } else {
                await this.initializeRealConnection();
            }
            
            // 创建系统表
            await this.createSystemTables();
            
            // 初始化系统因子
            await this.initializeSystemFactors();
            
            // 启动连接健康检查
            this.startHealthCheck();
            
            console.log('✅ 数据库管理器初始化完成');
            
        } catch (error) {
            console.error('❌ 数据库管理器初始化失败:', error);
            throw error;
        }
    }

    /**
     * 验证数据库配置
     */
    validateConfig() {
        const required = ['host', 'port', 'username', 'password', 'database'];
        for (const field of required) {
            if (!this.config[field]) {
                throw new Error(`数据库配置缺少必需字段: ${field}`);
            }
        }
        
        // 验证端口范围
        if (this.config.port < 1 || this.config.port > 65535) {
            throw new Error('数据库端口号无效');
        }
        
        console.log('✅ 数据库配置验证通过');
    }

    /**
     * 模拟数据库连接（浏览器环境）
     */
    async initializeMockConnection() {
        console.log('🔗 建立模拟MSSQL连接...');
        
        // 模拟连接延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        this.isConnected = true;
        console.log(`✅ 模拟连接成功: ${this.config.host}:${this.config.port}/${this.config.database}`);
        
        // 从本地存储加载模拟数据
        this.loadMockData();
    }

    /**
     * 真实数据库连接（Node.js环境）
     */
    async initializeRealConnection() {
        // 这里会在Node.js环境中实现真实的MSSQL连接
        // 使用mssql或其他MSSQL驱动
        console.log('🔗 建立真实MSSQL连接...');
        // 实际实现会在这里
    }

    /**
     * 创建系统表
     */
    async createSystemTables() {
        console.log('📋 创建系统表...');
        
        const tables = [
            {
                name: 'SystemConfig',
                description: '系统配置表',
                columns: [
                    { name: 'ConfigKey', type: 'NVARCHAR(100)', primaryKey: true },
                    { name: 'ConfigValue', type: 'NVARCHAR(MAX)' },
                    { name: 'Description', type: 'NVARCHAR(500)' },
                    { name: 'Category', type: 'NVARCHAR(50)' },
                    { name: 'CreatedAt', type: 'DATETIME2', defaultValue: 'GETDATE()' },
                    { name: 'UpdatedAt', type: 'DATETIME2', defaultValue: 'GETDATE()' }
                ]
            },
            {
                name: 'SystemFactors',
                description: '系统因子表',
                columns: [
                    { name: 'FactorId', type: 'UNIQUEIDENTIFIER', primaryKey: true, defaultValue: 'NEWID()' },
                    { name: 'FactorName', type: 'NVARCHAR(100)' },
                    { name: 'FactorValue', type: 'NVARCHAR(MAX)' },
                    { name: 'FactorType', type: 'NVARCHAR(50)' },
                    { name: 'Category', type: 'NVARCHAR(50)' },
                    { name: 'IsActive', type: 'BIT', defaultValue: '1' },
                    { name: 'CreatedAt', type: 'DATETIME2', defaultValue: 'GETDATE()' },
                    { name: 'UpdatedAt', type: 'DATETIME2', defaultValue: 'GETDATE()' }
                ]
            },
            {
                name: 'SystemLogs',
                description: '系统日志表',
                columns: [
                    { name: 'LogId', type: 'UNIQUEIDENTIFIER', primaryKey: true, defaultValue: 'NEWID()' },
                    { name: 'LogLevel', type: 'NVARCHAR(20)' },
                    { name: 'Message', type: 'NVARCHAR(MAX)' },
                    { name: 'Source', type: 'NVARCHAR(100)' },
                    { name: 'UserId', type: 'NVARCHAR(100)' },
                    { name: 'Timestamp', type: 'DATETIME2', defaultValue: 'GETDATE()' },
                    { name: 'Metadata', type: 'NVARCHAR(MAX)' }
                ]
            },
            {
                name: 'VersionHistory',
                description: '版本历史表',
                columns: [
                    { name: 'VersionId', type: 'UNIQUEIDENTIFIER', primaryKey: true, defaultValue: 'NEWID()' },
                    { name: 'Version', type: 'NVARCHAR(50)' },
                    { name: 'InternalVersion', type: 'NVARCHAR(50)' },
                    { name: 'ReleaseDate', type: 'DATETIME2' },
                    { name: 'Description', type: 'NVARCHAR(MAX)' },
                    { name: 'Changes', type: 'NVARCHAR(MAX)' },
                    { name: 'IsCurrent', type: 'BIT', defaultValue: '0' },
                    { name: 'CreatedAt', type: 'DATETIME2', defaultValue: 'GETDATE()' }
                ]
            },
            {
                name: 'UserSessions',
                description: '用户会话表',
                columns: [
                    { name: 'SessionId', type: 'UNIQUEIDENTIFIER', primaryKey: true, defaultValue: 'NEWID()' },
                    { name: 'UserId', type: 'NVARCHAR(100)' },
                    { name: 'Username', type: 'NVARCHAR(100)' },
                    { name: 'LoginTime', type: 'DATETIME2', defaultValue: 'GETDATE()' },
                    { name: 'LastActivity', type: 'DATETIME2', defaultValue: 'GETDATE()' },
                    { name: 'IpAddress', type: 'NVARCHAR(45)' },
                    { name: 'UserAgent', type: 'NVARCHAR(500)' },
                    { name: 'IsActive', type: 'BIT', defaultValue: '1' },
                    { name: 'ExpiresAt', type: 'DATETIME2' }
                ]
            },
            {
                name: 'SystemMetrics',
                description: '系统指标表',
                columns: [
                    { name: 'MetricId', type: 'UNIQUEIDENTIFIER', primaryKey: true, defaultValue: 'NEWID()' },
                    { name: 'MetricName', type: 'NVARCHAR(100)' },
                    { name: 'MetricValue', type: 'DECIMAL(18,6)' },
                    { name: 'MetricUnit', type: 'NVARCHAR(20)' },
                    { name: 'Category', type: 'NVARCHAR(50)' },
                    { name: 'Timestamp', type: 'DATETIME2', defaultValue: 'GETDATE()' },
                    { name: 'Tags', type: 'NVARCHAR(MAX)' }
                ]
            }
        ];

        for (const table of tables) {
            await this.createTable(table);
            this.systemTables.set(table.name, table);
        }

        console.log(`✅ 已创建 ${tables.length} 个系统表`);
    }

    /**
     * 创建单个表
     */
    async createTable(tableInfo) {
        if (typeof window !== 'undefined') {
            // 浏览器环境：保存到本地存储
            const tableKey = `db_table_${tableInfo.name}`;
            const existingTable = localStorage.getItem(tableKey);
            
            if (!existingTable) {
                const tableData = {
                    name: tableInfo.name,
                    description: tableInfo.description,
                    columns: tableInfo.columns,
                    rows: [],
                    createdAt: new Date().toISOString()
                };
                localStorage.setItem(tableKey, JSON.stringify(tableData));
                console.log(`📝 创建表: ${tableInfo.name}`);
            }
        } else {
            // Node.js环境：执行真实SQL
            const sql = this.generateCreateTableSQL(tableInfo);
            console.log(`📝 执行SQL: ${sql}`);
            // 实际实现会在这里执行SQL
        }
    }

    /**
     * 生成创建表的SQL语句
     */
    generateCreateTableSQL(tableInfo) {
        let sql = `CREATE TABLE [${tableInfo.name}] (\n`;
        
        tableInfo.columns.forEach((column, index) => {
            sql += `    [${column.name}] ${column.type}`;
            
            if (column.primaryKey) {
                sql += ' PRIMARY KEY';
            }
            
            if (column.defaultValue) {
                sql += ` DEFAULT ${column.defaultValue}`;
            }
            
            if (column.notNull) {
                sql += ' NOT NULL';
            }
            
            if (index < tableInfo.columns.length - 1) {
                sql += ',\n';
            }
        });
        
        sql += '\n);';
        
        return sql;
    }

    /**
     * 初始化系统因子
     */
    async initializeSystemFactors() {
        console.log('🔧 初始化系统因子...');
        
        const factors = [
            // 系统配置因子
            { name: 'SystemName', value: 'MTSCOS AI Project', type: 'string', category: 'system' },
            { name: 'SystemVersion', value: '3.0.0', type: 'string', category: 'system' },
            { name: 'InternalVersion', value: '3.0.0.20250115', type: 'string', category: 'system' },
            { name: 'Environment', value: 'production', type: 'string', category: 'system' },
            { name: 'Timezone', value: 'Asia/Shanghai', type: 'string', category: 'system' },
            
            // 数据库配置因子
            { name: 'DatabaseHost', value: this.config.host, type: 'string', category: 'database' },
            { name: 'DatabasePort', value: this.config.port.toString(), type: 'number', category: 'database' },
            { name: 'DatabaseName', value: this.config.database, type: 'string', category: 'database' },
            { name: 'ConnectionTimeout', value: '30000', type: 'number', category: 'database' },
            
            // 性能配置因子
            { name: 'MaxConnections', value: '100', type: 'number', category: 'performance' },
            { name: 'CacheEnabled', value: 'true', type: 'boolean', category: 'performance' },
            { name: 'CacheTTL', value: '300000', type: 'number', category: 'performance' },
            { name: 'CompressionEnabled', value: 'true', type: 'boolean', category: 'performance' },
            
            // 安全配置因子
            { name: 'SessionTimeout', value: '1800000', type: 'number', category: 'security' },
            { name: 'MaxLoginAttempts', value: '5', type: 'number', category: 'security' },
            { name: 'PasswordMinLength', value: '8', type: 'number', category: 'security' },
            { name: 'EncryptionEnabled', value: 'true', type: 'boolean', category: 'security' },
            
            // 监控配置因子
            { name: 'HealthCheckInterval', value: '60000', type: 'number', category: 'monitoring' },
            { name: 'MetricsEnabled', value: 'true', type: 'boolean', category: 'monitoring' },
            { name: 'LogLevel', value: 'info', type: 'string', category: 'monitoring' },
            { name: 'AlertThresholdCPU', value: '80', type: 'number', category: 'monitoring' }
        ];

        for (const factor of factors) {
            await this.insertSystemFactor(factor);
        }

        console.log(`✅ 已初始化 ${factors.length} 个系统因子`);
    }

    /**
     * 插入系统因子
     */
    async insertSystemFactor(factor) {
        if (typeof window !== 'undefined') {
            // 浏览器环境：保存到本地存储
            const tableKey = 'db_table_SystemFactors';
            const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
            
            // 检查是否已存在
            const existingFactor = tableData.rows.find(row => row.FactorName === factor.name);
            if (!existingFactor) {
                const newFactor = {
                    FactorId: this.generateUUID(),
                    FactorName: factor.name,
                    FactorValue: factor.value,
                    FactorType: factor.type,
                    Category: factor.category,
                    IsActive: true,
                    CreatedAt: new Date().toISOString(),
                    UpdatedAt: new Date().toISOString()
                };
                
                tableData.rows.push(newFactor);
                localStorage.setItem(tableKey, JSON.stringify(tableData));
            }
        } else {
            // Node.js环境：执行真实SQL
            const sql = `
                INSERT INTO SystemFactors (FactorName, FactorValue, FactorType, Category, IsActive)
                VALUES ('${factor.name}', '${factor.value}', '${factor.type}', '${factor.category}', 1)
            `;
            console.log(`📝 执行SQL: ${sql}`);
            // 实际实现会在这里执行SQL
        }
    }

    /**
     * 加载模拟数据
     */
    loadMockData() {
        // 从本地存储加载现有数据
        const tables = ['SystemConfig', 'SystemFactors', 'SystemLogs', 'VersionHistory', 'UserSessions', 'SystemMetrics'];
        tables.forEach(tableName => {
            const tableKey = `db_table_${tableName}`;
            const tableData = localStorage.getItem(tableKey);
            if (tableData) {
                console.log(`📂 加载表数据: ${tableName}`);
            }
        });
    }

    /**
     * 启动连接健康检查
     */
    startHealthCheck() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        
        this.healthCheckInterval = setInterval(async () => {
            try {
                const status = await this.testConnection();
                if (!status.success) {
                    console.warn('⚠️ 数据库连接健康检查失败:', status.message);
                    await this.logSystemEvent('warning', '数据库连接健康检查失败', 'HealthCheck');
                }
            } catch (error) {
                console.error('❌ 健康检查异常:', error);
                await this.logSystemEvent('error', '数据库健康检查异常', 'HealthCheck', null, { error: error.message });
            }
        }, 60000); // 每分钟检查一次
        
        console.log('🏥 数据库连接健康检查已启动');
    }

    /**
     * 停止健康检查
     */
    stopHealthCheck() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
            console.log('🛑 数据库连接健康检查已停止');
        }
    }

    /**
     * 获取系统因子
     */
    async getSystemFactor(factorName) {
        if (typeof window !== 'undefined') {
            const tableKey = 'db_table_SystemFactors';
            const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
            const factor = tableData.rows.find(row => row.FactorName === factorName && row.IsActive);
            return factor ? factor.FactorValue : null;
        }
        return null;
    }

    /**
     * 更新系统因子
     */
    async updateSystemFactor(factorName, value) {
        if (typeof window !== 'undefined') {
            const tableKey = 'db_table_SystemFactors';
            const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
            const factor = tableData.rows.find(row => row.FactorName === factorName);
            
            if (factor) {
                factor.FactorValue = value;
                factor.UpdatedAt = new Date().toISOString();
                localStorage.setItem(tableKey, JSON.stringify(tableData));
                return true;
            }
        }
        return false;
    }

    /**
     * 记录系统日志
     */
    async logSystemEvent(level, message, source = 'System', userId = null, metadata = null) {
        const logEntry = {
            LogId: this.generateUUID(),
            LogLevel: level,
            Message: message,
            Source: source,
            UserId: userId,
            Timestamp: new Date().toISOString(),
            Metadata: metadata ? JSON.stringify(metadata) : null
        };

        if (typeof window !== 'undefined') {
            const tableKey = 'db_table_SystemLogs';
            const tableData = JSON.parse(localStorage.getItem(tableKey) || '{"rows":[]}');
            tableData.rows.push(logEntry);
            
            // 保持日志表大小限制
            if (tableData.rows.length > 1000) {
                tableData.rows = tableData.rows.slice(-500); // 保留最新500条
            }
            
            localStorage.setItem(tableKey, JSON.stringify(tableData));
        }

        console.log(`[${level.toUpperCase()}] ${message}`);
    }

    /**
     * 测试数据库连接
     */
    async testConnection() {
        try {
            if (typeof window !== 'undefined') {
                // 模拟连接测试
                await new Promise(resolve => setTimeout(resolve, 500));
                return {
                    success: true,
                    message: '连接测试成功',
                    responseTime: Math.floor(Math.random() * 100) + 10,
                    serverVersion: 'Microsoft SQL Server 2019'
                };
            }
        } catch (error) {
            return {
                success: false,
                message: error.message,
                responseTime: null,
                serverVersion: null
            };
        }
    }

    /**
     * 获取连接状态
     */
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            config: {
                host: this.config.host,
                port: this.config.port,
                database: this.config.database,
                type: this.config.type
            },
            tablesCount: this.systemTables.size,
            poolSize: this.connectionPool.length
        };
    }

    /**
     * 生成UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * 关闭连接
     */
    async close() {
        if (this.isConnected) {
            console.log('🔌 关闭数据库连接...');
            this.isConnected = false;
            this.connectionPool = [];
            console.log('✅ 数据库连接已关闭');
        }
    }
}

// 导出类（浏览器环境）
if (typeof window !== 'undefined') {
    window.DatabaseManager = DatabaseManager;
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js环境
    module.exports = DatabaseManager;
}
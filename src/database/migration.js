// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 数据迁移脚本
 * 用于将现有数据导入数据库
 */

const db = require('./db');
const fs = require('fs');
const path = require('path');

class DataMigration {
    constructor() {
        this.db = db;
    }

    /**
     * 初始化迁移
     */
    async initialize() {
        console.log('开始数据迁移...');
        await this.db.initialize();
        console.log('数据库连接成功');
    }

    /**
     * 迁移用户数据
     */
    async migrateUsers() {
        console.log('迁移用户数据...');
        
        // 检查是否已有用户数据
        const existingUser = await this.db.getUserByUsername('wuchenghao15');
        if (existingUser) {
            console.log('默认管理员已存在，跳过用户迁移');
            return;
        }

        // 创建默认管理员
        await this.db.createUser({
            username: 'wuchenghao15',
            password: this.hashPassword('admin123'),
            email: 'admin@mtscos.com',
            role: 'super_admin'
        });
        console.log('默认管理员创建成功');

        // 创建测试用户
        await this.db.createUser({
            username: 'testuser',
            password: this.hashPassword('testpass'),
            email: 'test@example.com',
            role: 'user'
        });
        console.log('测试用户创建成功');
    }

    /**
     * 迁移系统设置
     */
    async migrateSystemSettings() {
        console.log('迁移系统设置...');

        // 导入基础系统设置
        const settings = [
            { key: 'system.name', value: 'MTSCOS安全系统', description: '系统名称', category: 'system' },
            { key: 'system.version', value: '1.0.0', description: '系统版本', category: 'system' },
            { key: 'system.maintenanceMode', value: 'false', description: '维护模式', category: 'system' },
            { key: 'security.minPasswordLength', value: '8', description: '最小密码长度', category: 'security' },
            { key: 'security.passwordComplexity', value: 'true', description: '密码复杂性要求', category: 'security' },
            { key: 'vikey.enabled', value: 'true', description: 'Vikey启用状态', category: 'vikey' },
            { key: 'database.type', value: 'SQLite', description: '数据库类型', category: 'database' },
            { key: 'logs.level', value: 'INFO', description: '日志级别', category: 'logs' },
            { key: 'ui.themeMode', value: 'auto', description: '主题模式', category: 'ui' }
        ];

        for (const setting of settings) {
            await this.db.updateSystemSetting(setting.key, setting.value, setting.description, setting.category);
        }

        console.log('系统设置迁移完成');
    }

    /**
     * 迁移服务器配置
     */
    async migrateServerConfig() {
        console.log('迁移服务器配置...');

        // 导入服务器配置
        const configs = [
            { key: 'port', value: '8080', description: '服务器端口' },
            { key: 'host', value: '0.0.0.0', description: '服务器主机' },
            { key: 'timeout', value: '30000', description: '请求超时时间' },
            { key: 'maxUploadSize', value: '10mb', description: '最大上传大小' },
            { key: 'corsEnabled', value: 'true', description: 'CORS启用状态' }
        ];

        for (const config of configs) {
            await this.db.updateServerConfig(config.key, config.value, config.description);
        }

        console.log('服务器配置迁移完成');
    }

    /**
     * 迁移安全设置
     */
    async migrateSecuritySettings() {
        console.log('迁移安全设置...');

        // 导入安全设置
        const securitySettings = [
            { key: 'apiKeyValidation', value: 'true', description: 'API密钥验证' },
            { key: 'rateLimiting', value: 'true', description: '速率限制' },
            { key: 'ipWhitelistEnabled', value: 'false', description: 'IP白名单启用' },
            { key: 'sessionTimeout', value: '1800', description: '会话超时(秒)' },
            { key: 'maxLoginAttempts', value: '5', description: '最大登录尝试次数' }
        ];

        for (const setting of securitySettings) {
            await this.db.updateSecuritySetting(setting.key, setting.value, setting.description);
        }

        console.log('安全设置迁移完成');
    }

    /**
     * 密码哈希
     */
    hashPassword(password) {
        return btoa(password + 'salt');
    }

    /**
     * 执行完整迁移
     */
    async run() {
        try {
            await this.initialize();
            await this.migrateUsers();
            await this.migrateSystemSettings();
            await this.migrateServerConfig();
            await this.migrateSecuritySettings();
            
            console.log('🎉 数据迁移完成！');
            console.log('所有现有数据已成功导入数据库');
            
            // 关闭数据库连接
            this.db.close();
            process.exit(0);
        } catch (error) {
            console.error('❌ 数据迁移失败:', error.message);
            console.error('错误堆栈:', error.stack);
            this.db.close();
            process.exit(1);
        }
    }
}

// 执行迁移
if (require.main === module) {
    const migration = new DataMigration();
    migration.run();
}

module.exports = DataMigration;

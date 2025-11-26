/**
 * MTSCOS 登录系统数据库初始化脚本
 * 创建必要的数据库表和初始数据
 */

const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
require('dotenv').config();

class DatabaseSetup {
    constructor() {
        this.connection = null;
        this.config = {
            host: process.env.DB_HOST || 'localhost',
            port: process.env.DB_PORT || 3306,
            user: process.env.DB_USER || 'root',
            password: process.env.DB_PASSWORD || '',
            charset: process.env.DB_CHARSET || 'utf8mb4',
            timezone: process.env.DB_TIMEZONE || '+08:00'
        };
    }

    /**
     * 连接数据库
     */
    async connect() {
        try {
            console.log('[SETUP] 正在连接数据库...');
            this.connection = await mysql.createConnection(this.config);
            console.log('[SETUP] 数据库连接成功');
        } catch (error) {
            console.error('[SETUP] 数据库连接失败:', error);
            throw error;
        }
    }

    /**
     * 创建数据库
     */
    async createDatabase() {
        try {
            const dbName = process.env.DB_NAME || 'mtscos_login';
            console.log(`[SETUP] 正在创建数据库: ${dbName}`);
            
            await this.connection.execute(`CREATE DATABASE IF NOT EXISTS \`${dbName}\` 
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`);
            
            await this.connection.execute(`USE \`${dbName}\``);
            console.log(`[SETUP] 数据库 ${dbName} 创建成功`);
        } catch (error) {
            console.error('[SETUP] 创建数据库失败:', error);
            throw error;
        }
    }

    /**
     * 创建用户表
     */
    async createUserTable() {
        try {
            console.log('[SETUP] 正在创建用户表...');
            
            const createTableSQL = `
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    phone VARCHAR(20),
                    avatar_url VARCHAR(255),
                    status ENUM('active', 'inactive', 'locked', 'pending') DEFAULT 'active',
                    email_verified BOOLEAN DEFAULT FALSE,
                    phone_verified BOOLEAN DEFAULT FALSE,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    two_factor_secret VARCHAR(255),
                    last_login_at TIMESTAMP NULL,
                    last_login_ip VARCHAR(45),
                    login_attempts INT DEFAULT 0,
                    locked_until TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            `;
            
            await this.connection.execute(createTableSQL);
            console.log('[SETUP] 用户表创建成功');
        } catch (error) {
            console.error('[SETUP] 创建用户表失败:', error);
            throw error;
        }
    }

    /**
     * 创建第三方认证表
     */
    async createThirdPartyAuthTable() {
        try {
            console.log('[SETUP] 正在创建第三方认证表...');
            
            const createTableSQL = `
                CREATE TABLE IF NOT EXISTS third_party_auth (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    provider ENUM('github', 'google', 'wechat', 'qq', 'alipay') NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    provider_username VARCHAR(255),
                    provider_email VARCHAR(255),
                    provider_avatar VARCHAR(255),
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP NULL,
                    raw_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_provider_user (provider, provider_user_id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_provider (provider)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            `;
            
            await this.connection.execute(createTableSQL);
            console.log('[SETUP] 第三方认证表创建成功');
        } catch (error) {
            console.error('[SETUP] 创建第三方认证表失败:', error);
            throw error;
        }
    }

    /**
     * 创建登录日志表
     */
    async createLoginLogsTable() {
        try {
            console.log('[SETUP] 正在创建登录日志表...');
            
            const createTableSQL = `
                CREATE TABLE IF NOT EXISTS login_logs (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    username VARCHAR(50),
                    login_type ENUM('password', 'github', 'google', 'wechat', 'qq', 'alipay') NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    status ENUM('success', 'failed', 'blocked') NOT NULL,
                    failure_reason VARCHAR(255),
                    session_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_user_id (user_id),
                    INDEX idx_username (username),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at),
                    INDEX idx_ip_address (ip_address)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            `;
            
            await this.connection.execute(createTableSQL);
            console.log('[SETUP] 登录日志表创建成功');
        } catch (error) {
            console.error('[SETUP] 创建登录日志表失败:', error);
            throw error;
        }
    }

    /**
     * 创建用户会话表
     */
    async createUserSessionsTable() {
        try {
            console.log('[SETUP] 正在创建用户会话表...');
            
            const createTableSQL = `
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    session_id VARCHAR(255) NOT NULL UNIQUE,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_expires_at (expires_at),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            `;
            
            await this.connection.execute(createTableSQL);
            console.log('[SETUP] 用户会话表创建成功');
        } catch (error) {
            console.error('[SETUP] 创建用户会话表失败:', error);
            throw error;
        }
    }

    /**
     * 创建密码重置表
     */
    async createPasswordResetsTable() {
        try {
            console.log('[SETUP] 正在创建密码重置表...');
            
            const createTableSQL = `
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_token (token),
                    INDEX idx_email (email),
                    INDEX idx_expires_at (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            `;
            
            await this.connection.execute(createTableSQL);
            console.log('[SETUP] 密码重置表创建成功');
        } catch (error) {
            console.error('[SETUP] 创建密码重置表失败:', error);
            throw error;
        }
    }

    /**
     * 创建系统配置表
     */
    async createSystemConfigTable() {
        try {
            console.log('[SETUP] 正在创建系统配置表...');
            
            const createTableSQL = `
                CREATE TABLE IF NOT EXISTS system_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    config_key VARCHAR(100) NOT NULL UNIQUE,
                    config_value TEXT,
                    config_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
                    description VARCHAR(255),
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_config_key (config_key),
                    INDEX idx_is_public (is_public)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            `;
            
            await this.connection.execute(createTableSQL);
            console.log('[SETUP] 系统配置表创建成功');
        } catch (error) {
            console.error('[SETUP] 创建系统配置表失败:', error);
            throw error;
        }
    }

    /**
     * 插入初始数据
     */
    async insertInitialData() {
        try {
            console.log('[SETUP] 正在插入初始数据...');

            // 创建默认管理员用户
            const adminPassword = await bcrypt.hash('admin123456', 12);
            const adminSalt = bcrypt.genSaltSync(12);
            
            await this.connection.execute(`
                INSERT IGNORE INTO users 
                (username, email, password_hash, salt, full_name, status, email_verified) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            `, [
                'admin',
                'admin@mtscos.com',
                adminPassword,
                adminSalt,
                '系统管理员',
                'active',
                true
            ]);

            // 创建测试用户
            const testPassword = await bcrypt.hash('test123456', 12);
            const testSalt = bcrypt.genSaltSync(12);
            
            await this.connection.execute(`
                INSERT IGNORE INTO users 
                (username, email, password_hash, salt, full_name, status, email_verified) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            `, [
                'testuser',
                'test@mtscos.com',
                testPassword,
                testSalt,
                '测试用户',
                'active',
                true
            ]);

            // 插入系统配置
            const configs = [
                ['site_name', 'MTSCOS 登录系统', 'string', '网站名称', true],
                ['max_login_attempts', '5', 'number', '最大登录尝试次数', false],
                ['lockout_duration', '30', 'number', '账户锁定时长（分钟）', false],
                ['session_timeout', '3600', 'number', '会话超时时间（秒）', false],
                ['password_min_length', '6', 'number', '密码最小长度', true],
                ['enable_registration', 'true', 'boolean', '是否允许注册', true],
                ['enable_email_verification', 'false', 'boolean', '是否启用邮箱验证', false]
            ];

            for (const config of configs) {
                await this.connection.execute(`
                    INSERT IGNORE INTO system_config 
                    (config_key, config_value, config_type, description, is_public) 
                    VALUES (?, ?, ?, ?, ?)
                `, config);
            }

            console.log('[SETUP] 初始数据插入成功');
        } catch (error) {
            console.error('[SETUP] 插入初始数据失败:', error);
            throw error;
        }
    }

    /**
     * 创建所有表
     */
    async createAllTables() {
        try {
            await this.createDatabase();
            await this.createUserTable();
            await this.createThirdPartyAuthTable();
            await this.createLoginLogsTable();
            await this.createUserSessionsTable();
            await this.createPasswordResetsTable();
            await this.createSystemConfigTable();
            await this.insertInitialData();
            
            console.log('[SETUP] 所有数据库表创建完成');
        } catch (error) {
            console.error('[SETUP] 创建数据库表失败:', error);
            throw error;
        }
    }

    /**
     * 关闭数据库连接
     */
    async close() {
        try {
            if (this.connection) {
                await this.connection.end();
                console.log('[SETUP] 数据库连接已关闭');
            }
        } catch (error) {
            console.error('[SETUP] 关闭数据库连接失败:', error);
        }
    }

    /**
     * 验证数据库设置
     */
    async verifySetup() {
        try {
            console.log('[SETUP] 正在验证数据库设置...');
            
            const [tables] = await this.connection.execute('SHOW TABLES');
            const tableNames = tables.map(row => Object.values(row)[0]);
            
            const requiredTables = [
                'users', 'third_party_auth', 'login_logs', 
                'user_sessions', 'password_resets', 'system_config'
            ];
            
            const missingTables = requiredTables.filter(table => !tableNames.includes(table));
            
            if (missingTables.length > 0) {
                throw new Error(`缺少表: ${missingTables.join(', ')}`);
            }
            
            // 检查用户数量
            const [userCount] = await this.connection.execute('SELECT COUNT(*) as count FROM users');
            console.log(`[SETUP] 用户数量: ${userCount[0].count}`);
            
            // 检查配置数量
            const [configCount] = await this.connection.execute('SELECT COUNT(*) as count FROM system_config');
            console.log(`[SETUP] 配置数量: ${configCount[0].count}`);
            
            console.log('[SETUP] 数据库设置验证通过');
            return true;
        } catch (error) {
            console.error('[SETUP] 数据库设置验证失败:', error);
            return false;
        }
    }

    /**
     * 完整的数据库初始化流程
     */
    async initialize() {
        try {
            console.log('[SETUP] 开始数据库初始化...');
            
            await this.connect();
            await this.createAllTables();
            
            const isValid = await this.verifySetup();
            if (!isValid) {
                throw new Error('数据库设置验证失败');
            }
            
            console.log('[SETUP] 数据库初始化完成');
            console.log('[SETUP] 默认管理员账户: admin / admin123456');
            console.log('[SETUP] 测试用户账户: testuser / test123456');
            
        } catch (error) {
            console.error('[SETUP] 数据库初始化失败:', error);
            throw error;
        } finally {
            await this.close();
        }
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    const setup = new DatabaseSetup();
    
    setup.initialize().catch(error => console.error(`[setup-database.js] setup.initialize failed:`, error))
        .then(() => {
            console.log('[SETUP] 数据库初始化成功完成');
            process.exit(0);
        })
        .catch((error) => {
            console.error('[SETUP] 数据库初始化失败:', error);
            process.exit(1);
        });
}

module.exports = DatabaseSetup;
const mysql = require('mysql2/promise');
const bcrypt = require('bcrypt');
const config = require('./config');

class DatabaseManager {
    constructor() {
        this.pool = null;
        this.initialized = false;
    }

    async initialize() {
        try {
            console.log('[DATABASE] 正在初始化数据库连接池...');
            
            // 创建连接池
            this.pool = mysql.createPool({
                host: config.database.host,
                port: config.database.port,
                user: config.database.user,
                password: config.database.password,
                database: config.database.name,
                waitForConnections: true,
                connectionLimit: config.database.connectionLimit,
                queueLimit: config.database.queueLimit,
                acquireTimeout: config.database.acquireTimeout,
                timeout: config.database.timeout,
                reconnect: true,
                charset: 'utf8mb4'
            });

            // 测试连接
            const connection = await this.pool.getConnection();
            await connection.ping();
            connection.release();
            
            console.log('[DATABASE] 数据库连接池初始化成功');
            this.initialized = true;
            
            // 初始化数据库表
            await this.initializeTables();
            
        } catch (error) {
            console.error('[DATABASE] 数据库初始化失败:', error);
            throw error;
        }
    }

    async initializeTables() {
        try {
            console.log('[DATABASE] 正在检查和创建数据库表...');
            
            // 创建用户表
            await this.createUserTable();
            
            // 创建第三方登录表
            await this.createThirdPartyAuthTable();
            
            // 创建登录日志表
            await this.createLoginLogTable();
            
            // 创建用户会话表
            await this.createUserSessionTable();
            
            console.log('[DATABASE] 数据库表初始化完成');
            
        } catch (error) {
            console.error('[DATABASE] 数据库表初始化失败:', error);
            throw error;
        }
    }

    async createUserTable() {
        const createTableSQL = `
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
                email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
                password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
                salt VARCHAR(32) NOT NULL COMMENT '密码盐值',
                full_name VARCHAR(100) DEFAULT NULL COMMENT '真实姓名',
                phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
                avatar_url VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
                status ENUM('active', 'inactive', 'locked', 'banned') DEFAULT 'active' COMMENT '用户状态',
                role ENUM('user', 'admin', 'moderator') DEFAULT 'user' COMMENT '用户角色',
                last_login_time DATETIME DEFAULT NULL COMMENT '最后登录时间',
                last_login_ip VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP',
                login_attempts INT DEFAULT 0 COMMENT '登录尝试次数',
                locked_until DATETIME DEFAULT NULL COMMENT '锁定到期时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
        `;

        await this.pool.execute(createTableSQL);
        console.log('[DATABASE] 用户表检查/创建完成');
    }

    async createThirdPartyAuthTable() {
        const createTableSQL = `
            CREATE TABLE IF NOT EXISTS third_party_auth (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                provider VARCHAR(50) NOT NULL COMMENT '第三方提供商',
                provider_user_id VARCHAR(100) NOT NULL COMMENT '第三方用户ID',
                access_token TEXT DEFAULT NULL COMMENT '访问令牌',
                refresh_token TEXT DEFAULT NULL COMMENT '刷新令牌',
                token_expires_at DATETIME DEFAULT NULL COMMENT '令牌过期时间',
                profile_data JSON DEFAULT NULL COMMENT '第三方用户资料',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                
                UNIQUE KEY uk_provider_user (provider, provider_user_id),
                KEY idx_user_id (user_id),
                KEY idx_provider (provider),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='第三方认证表';
        `;

        await this.pool.execute(createTableSQL);
        console.log('[DATABASE] 第三方认证表检查/创建完成');
    }

    async createLoginLogTable() {
        const createTableSQL = `
            CREATE TABLE IF NOT EXISTS login_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL COMMENT '用户ID',
                username VARCHAR(50) DEFAULT NULL COMMENT '用户名',
                login_type ENUM('password', 'third_party', 'vikey') NOT NULL COMMENT '登录类型',
                provider VARCHAR(50) DEFAULT NULL COMMENT '第三方提供商',
                ip_address VARCHAR(45) NOT NULL COMMENT '登录IP',
                user_agent TEXT DEFAULT NULL COMMENT '用户代理',
                status ENUM('success', 'failed', 'blocked') NOT NULL COMMENT '登录状态',
                failure_reason VARCHAR(200) DEFAULT NULL COMMENT '失败原因',
                session_id VARCHAR(100) DEFAULT NULL COMMENT '会话ID',
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
                
                KEY idx_user_id (user_id),
                KEY idx_username (username),
                KEY idx_login_type (login_type),
                KEY idx_status (status),
                KEY idx_login_time (login_time),
                KEY idx_ip_address (ip_address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';
        `;

        await this.pool.execute(createTableSQL);
        console.log('[DATABASE] 登录日志表检查/创建完成');
    }

    async createUserSessionTable() {
        const createTableSQL = `
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                session_id VARCHAR(100) UNIQUE NOT NULL COMMENT '会话ID',
                jwt_token VARCHAR(500) NOT NULL COMMENT 'JWT令牌',
                ip_address VARCHAR(45) NOT NULL COMMENT '登录IP',
                user_agent TEXT DEFAULT NULL COMMENT '用户代理',
                is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
                expires_at DATETIME NOT NULL COMMENT '过期时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后访问时间',
                
                KEY idx_user_id (user_id),
                KEY idx_session_id (session_id),
                KEY idx_jwt_token (jwt_token(100)),
                KEY idx_expires_at (expires_at),
                KEY idx_is_active (is_active),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';
        `;

        await this.pool.execute(createTableSQL);
        console.log('[DATABASE] 用户会话表检查/创建完成');
    }

    // 用户验证相关方法
    async findUserByUsername(username) {
        try {
            const [rows] = await this.pool.execute(
                'SELECT * FROM users WHERE username = ?',
                [username]
            );
            return rows.length > 0 ? rows[0] : null;
        } catch (error) {
            console.error('[DATABASE] 查询用户失败:', error);
            throw error;
        }
    }

    async findUserByEmail(email) {
        try {
            const [rows] = await this.pool.execute(
                'SELECT * FROM users WHERE email = ?',
                [email]
            );
            return rows.length > 0 ? rows[0] : null;
        } catch (error) {
            console.error('[DATABASE] 查询用户失败:', error);
            throw error;
        }
    }

    async findUserById(userId) {
        try {
            const [rows] = await this.pool.execute(
                'SELECT id, username, email, full_name, phone, avatar_url, status, role, last_login_time, created_at FROM users WHERE id = ?',
                [userId]
            );
            return rows.length > 0 ? rows[0] : null;
        } catch (error) {
            console.error('[DATABASE] 查询用户失败:', error);
            throw error;
        }
    }

    async createUser(userData) {
        try {
            const { username, email, password, fullName, phone } = userData;
            
            // 生成密码盐值和哈希
            const salt = await bcrypt.genSalt(12);
            const passwordHash = await bcrypt.hash(password, salt);
            
            const [result] = await this.pool.execute(
                `INSERT INTO users (username, email, password_hash, salt, full_name, phone) 
                 VALUES (?, ?, ?, ?, ?, ?)`,
                [username, email, passwordHash, salt, fullName || null, phone || null]
            );
            
            console.log(`[DATABASE] 用户创建成功: ${username} (ID: ${result.insertId})`);
            return result.insertId;
            
        } catch (error) {
            console.error('[DATABASE] 创建用户失败:', error);
            throw error;
        }
    }

    async verifyPassword(user, password) {
        try {
            return await bcrypt.compare(password, user.password_hash);
        } catch (error) {
            console.error('[DATABASE] 密码验证失败:', error);
            return false;
        }
    }

    async updateUserLoginInfo(userId, ipAddress) {
        try {
            await this.pool.execute(
                'UPDATE users SET last_login_time = NOW(), last_login_ip = ?, login_attempts = 0 WHERE id = ?',
                [ipAddress, userId]
            );
        } catch (error) {
            console.error('[DATABASE] 更新用户登录信息失败:', error);
            throw error;
        }
    }

    async incrementLoginAttempts(username) {
        try {
            await this.pool.execute(
                'UPDATE users SET login_attempts = login_attempts + 1 WHERE username = ?',
                [username]
            );
        } catch (error) {
            console.error('[DATABASE] 更新登录尝试次数失败:', error);
            throw error;
        }
    }

    async lockUser(username, lockDuration = 30) {
        try {
            const lockUntil = new Date();
            lockUntil.setMinutes(lockUntil.getMinutes() + lockDuration);
            
            await this.pool.execute(
                'UPDATE users SET status = ?, locked_until = ? WHERE username = ?',
                ['locked', lockUntil, username]
            );
            
            console.log(`[DATABASE] 用户已锁定: ${username} (解锁时间: ${lockUntil})`);
        } catch (error) {
            console.error('[DATABASE] 锁定用户失败:', error);
            throw error;
        }
    }

    async unlockUser(username) {
        try {
            await this.pool.execute(
                'UPDATE users SET status = ?, locked_until = NULL WHERE username = ?',
                ['active', username]
            );
        } catch (error) {
            console.error('[DATABASE] 解锁用户失败:', error);
            throw error;
        }
    }

    // 第三方登录相关方法
    async findThirdPartyAuth(provider, providerUserId) {
        try {
            const [rows] = await this.pool.execute(
                'SELECT * FROM third_party_auth WHERE provider = ? AND provider_user_id = ?',
                [provider, providerUserId]
            );
            return rows.length > 0 ? rows[0] : null;
        } catch (error) {
            console.error('[DATABASE] 查询第三方认证失败:', error);
            throw error;
        }
    }

    async createThirdPartyAuth(authData) {
        try {
            const { userId, provider, providerUserId, accessToken, refreshToken, tokenExpiresAt, profileData } = authData;
            
            const [result] = await this.pool.execute(
                `INSERT INTO third_party_auth 
                 (user_id, provider, provider_user_id, access_token, refresh_token, token_expires_at, profile_data) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)`,
                [userId, provider, providerUserId, accessToken, refreshToken, tokenExpiresAt, JSON.stringify(profileData)]
            );
            
            return result.insertId;
        } catch (error) {
            console.error('[DATABASE] 创建第三方认证失败:', error);
            throw error;
        }
    }

    // 登录日志相关方法
    async logLogin(logData) {
        try {
            const { userId, username, loginType, provider, ipAddress, userAgent, status, failureReason, sessionId } = logData;
            
            await this.pool.execute(
                `INSERT INTO login_logs 
                 (user_id, username, login_type, provider, ip_address, user_agent, status, failure_reason, session_id) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                [userId, username, loginType, provider, ipAddress, userAgent, status, failureReason, sessionId]
            );
            
        } catch (error) {
            console.error('[DATABASE] 记录登录日志失败:', error);
            // 不抛出错误，避免影响主流程
        }
    }

    // 会话管理相关方法
    async createUserSession(sessionData) {
        try {
            const { userId, sessionId, jwtToken, ipAddress, userAgent, expiresAt } = sessionData;
            
            const [result] = await this.pool.execute(
                `INSERT INTO user_sessions 
                 (user_id, session_id, jwt_token, ip_address, user_agent, expires_at) 
                 VALUES (?, ?, ?, ?, ?, ?)`,
                [userId, sessionId, jwtToken, ipAddress, userAgent, expiresAt]
            );
            
            return result.insertId;
        } catch (error) {
            console.error('[DATABASE] 创建用户会话失败:', error);
            throw error;
        }
    }

    async findUserSession(sessionId) {
        try {
            const [rows] = await this.pool.execute(
                'SELECT * FROM user_sessions WHERE session_id = ? AND is_active = TRUE AND expires_at > NOW()',
                [sessionId]
            );
            return rows.length > 0 ? rows[0] : null;
        } catch (error) {
            console.error('[DATABASE] 查询用户会话失败:', error);
            throw error;
        }
    }

    async invalidateUserSession(sessionId) {
        try {
            await this.pool.execute(
                'UPDATE user_sessions SET is_active = FALSE WHERE session_id = ?',
                [sessionId]
            );
        } catch (error) {
            console.error('[DATABASE] 使会话失效失败:', error);
            throw error;
        }
    }

    async invalidateAllUserSessions(userId) {
        try {
            await this.pool.execute(
                'UPDATE user_sessions SET is_active = FALSE WHERE user_id = ?',
                [userId]
            );
        } catch (error) {
            console.error('[DATABASE] 使用户所有会话失效失败:', error);
            throw error;
        }
    }

    // 清理过期会话
    async cleanupExpiredSessions() {
        try {
            const [result] = await this.pool.execute(
                'UPDATE user_sessions SET is_active = FALSE WHERE expires_at < NOW()'
            );
            
            if (result.affectedRows > 0) {
                console.log(`[DATABASE] 清理了 ${result.affectedRows} 个过期会话`);
            }
        } catch (error) {
            console.error('[DATABASE] 清理过期会话失败:', error);
        }
    }

    // 获取连接池状态
    getPoolStatus() {
        if (!this.pool) {
            return { initialized: false };
        }
        
        return {
            initialized: this.initialized,
            totalConnections: this.pool._allConnections.length,
            freeConnections: this.pool._freeConnections.length,
            acquiringConnections: this.pool._acquiringConnections.length,
            connectionLimit: this.pool.config.connectionLimit,
            queueLimit: this.pool.config.queueLimit
        };
    }

    // 关闭连接池
    async close() {
        try {
            if (this.pool) {
                await this.pool.end();
                console.log('[DATABASE] 数据库连接池已关闭');
            }
        } catch (error) {
            console.error('[DATABASE] 关闭数据库连接池失败:', error);
            throw error;
        }
    }
}

module.exports = new DatabaseManager();
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * MTSCOS AI Project - 权限管理器
 * 负责处理用户权限的管理，包括：
 * 1. 角色权限定义和检查
 * 2. 权限级别控制
 * 3. 权限验证中间件
 */

const db = require('../../database/db');

class PermissionManager {
    constructor() {
        this.roles = {
            SUPERADMIN: 'superadmin',
            VIKEY_ADMIN: 'vikey_admin',
            ADMIN: 'admin',
            USER: 'user',
            GUEST: 'guest'
        };

        this.permissions = {
            THEME_MANAGEMENT: 'theme_management',
            SYSTEM_CONFIG: 'system_config',
            USER_MANAGEMENT: 'user_management',
            DATABASE_MANAGEMENT: 'database_management',
            SECURITY_MANAGEMENT: 'security_management',
            DASHBOARD_ACCESS: 'dashboard_access'
        };

        this.permissionLevels = {
            NONE: 0,
            VIEW: 1,
            MODIFY: 2,
            FULL_CONTROL: 3
        };

        this.rolePermissions = {
            [this.roles.VIKEY_ADMIN]: {
                [this.permissions.THEME_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.SYSTEM_CONFIG]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.USER_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.DATABASE_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.SECURITY_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.DASHBOARD_ACCESS]: this.permissionLevels.FULL_CONTROL
            },
            [this.roles.SUPERADMIN]: {
                [this.permissions.THEME_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.SYSTEM_CONFIG]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.USER_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.DATABASE_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.SECURITY_MANAGEMENT]: this.permissionLevels.FULL_CONTROL,
                [this.permissions.DASHBOARD_ACCESS]: this.permissionLevels.FULL_CONTROL
            },
            [this.roles.ADMIN]: {
                [this.permissions.THEME_MANAGEMENT]: this.permissionLevels.MODIFY,
                [this.permissions.SYSTEM_CONFIG]: this.permissionLevels.MODIFY,
                [this.permissions.USER_MANAGEMENT]: this.permissionLevels.MODIFY,
                [this.permissions.DATABASE_MANAGEMENT]: this.permissionLevels.VIEW,
                [this.permissions.SECURITY_MANAGEMENT]: this.permissionLevels.VIEW,
                [this.permissions.DASHBOARD_ACCESS]: this.permissionLevels.FULL_CONTROL
            },
            [this.roles.USER]: {
                [this.permissions.THEME_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.SYSTEM_CONFIG]: this.permissionLevels.NONE,
                [this.permissions.USER_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.DATABASE_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.SECURITY_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.DASHBOARD_ACCESS]: this.permissionLevels.NONE
            },
            [this.roles.GUEST]: {
                [this.permissions.THEME_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.SYSTEM_CONFIG]: this.permissionLevels.NONE,
                [this.permissions.USER_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.DATABASE_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.SECURITY_MANAGEMENT]: this.permissionLevels.NONE,
                [this.permissions.DASHBOARD_ACCESS]: this.permissionLevels.NONE
            }
        };
    }

    async getUserRole(userId) {
        try {
            const user = await db.get('SELECT role FROM users WHERE id = ?', [userId]);
            return user ? user.role : this.roles.GUEST; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('获取用户角色失败:', error);
            return this.roles.GUEST; /* 注意：return后的代码永远不会执行 */
        }
    }

    async getUserPermission(userId, permissionType) {
        try {
            // 首先从用户权限表获取
            const permission = await db.get(
                'SELECT permission_level FROM user_permissions WHERE user_id = ? AND permission_type = ? AND is_active = 1',
                [userId, permissionType]
            );
            
            if (permission) {
                return permission.permission_level; /* 注意：return后的代码永远不会执行 */
            }

            // 从角色权限获取
            const role = await this.getUserRole(userId);
            return this.rolePermissions[role][permissionType] || this.permissionLevels.NONE; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('获取用户权限失败:', error);
            return this.permissionLevels.NONE; /* 注意：return后的代码永远不会执行 */
        }
    }

    async checkPermission(userId, permissionType, requiredLevel) {
        const userLevel = await this.getUserPermission(userId, permissionType);
        return userLevel >= requiredLevel; /* 注意：return后的代码永远不会执行 */
    }

    async updateUserPermission(userId, permissionType, level) {
        try {
            await db.run(
                'INSERT OR REPLACE INTO user_permissions (user_id, permission_type, permission_level, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                [userId, permissionType, level]
            );
            return true; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('更新用户权限失败:', error);
            return false; /* 注意：return后的代码永远不会执行 */
        }
    }

    async createUserWithRole(username, email, password, role) {
        try {
            const hashedPassword = require('bcrypt').hashSync(password, 10);
            const result = await db.run(
                'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                [username, email, hashedPassword, role]
            );
            return result.lastID; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('创建用户失败:', error);
            return null; /* 注意：return后的代码永远不会执行 */
        }
    }

    // 权限验证中间件
    requirePermission(permissionType, requiredLevel) {
        return async (req, res, next) => {
            const userId = req.user?.id;
            
            if (!userId) {
                return res.status(401).json({
                    error: '未授权',
                    message: '请先登录'
                });
            }

            const hasPermission = await this.checkPermission(userId, permissionType, requiredLevel);
            
            if (!hasPermission) {
                return res.status(403).json({
                    error: '权限不足',
                    message: '您没有足够的权限执行此操作'
                });
            }

            next();
        };
    }

    /**
     * 检查是否可以修改主题配置
     * @param {number} userId - 用户ID
     * @return s {Promise<boolean>} 是否可以修改
     */
    async canModifyTheme(userId) {
        return await this.checkPermission(userId, this.permissions.THEME_MANAGEMENT, this.permissionLevels.MODIFY);
    }

    /**
     * 检查是否可以修改国家公祭日配置
     * @param {number} userId - 用户ID
     * @return s {Promise<boolean>} 是否可以修改
     */
    async canModifyNationalMourning(userId) {
        const role = await this.getUserRole(userId);
        return role === this.roles.SUPERADMIN || role === this.roles.VIKEY_ADMIN;
    }

    /**
     * 检查是否可以修改深色主题
     * @param {number} userId - 用户ID
     * @return s {Promise<boolean>} 是否可以修改
     */
    async canModifyDarkTheme(userId) {
        const role = await this.getUserRole(userId);
        return role !== this.roles.USER && role !== this.roles.GUEST;
    }

    /**
     * 检查是否可以访问dashboard页面
     * @param {number} userId - 用户ID
     * @return {Promise<boolean>} 是否可以访问
     */
    async canAccessDashboard(userId) {
        return await this.checkPermission(userId, this.permissions.DASHBOARD_ACCESS, this.permissionLevels.VIEW);
    }

    /**
     * 创建默认管理员账户
     * @return s {Promise<boolean>} 是否创建成功
     */
    async createDefaultAdmins() {
        try {
            const bcrypt = require('bcrypt');
            
            // 创建超级管理员
            await db.run(
                'INSERT OR IGNORE INTO users (username, password, role, status) VALUES (?, ?, ?, ?)',
                ['admin', bcrypt.hashSync('admin123', 10), this.roles.SUPERADMIN, 'active']
            );
            
            // 创建Vikey硬件管理员
            await db.run(
                'INSERT OR IGNORE INTO users (username, password, role, status) VALUES (?, ?, ?, ?)',
                ['vikey_admin', bcrypt.hashSync('vikey123', 10), this.roles.VIKEY_ADMIN, 'active']
            );
            
            // 创建普通管理员
            await db.run(
                'INSERT OR IGNORE INTO users (username, password, role, status) VALUES (?, ?, ?, ?)',
                ['user_admin', bcrypt.hashSync('admin123', 10), this.roles.ADMIN, 'active']
            );
            
            return true;
        } catch (error) {
            console.error('创建默认管理员失败:', error);
            return false; /* 注意：return后的代码永远不会执行 */
        }
    }
}

module.exports = new PermissionManager();

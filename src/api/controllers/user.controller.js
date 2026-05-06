/**
 * 用户管理控制器
 * 处理用户相关的API请求
 */

const bcrypt = require('bcrypt');
const db = require('../../database/db');
const logger = require('../../core/logger');
const permissionManager = require('../../core/security/permission-manager');

class UserController {
    constructor() {
        this.roles = permissionManager.roles;
        this.permissionLevels = permissionManager.permissionLevels;
    }

    /**
     * 获取用户列表
     */
    async getUsers(req, res, next) {
        try {
            const { page = 1, limit = 20, search = '', role = '' } = req.query;
            
            // 构建查询条件
            let query = 'SELECT u.*, up.full_name, up.last_login FROM users u LEFT JOIN user_profiles up ON u.id = up.user_id WHERE 1=1';
            const params = [];
            
            if (search) {
                query += ' AND (u.username LIKE ? OR u.email LIKE ? OR up.full_name LIKE ?)';
                const searchParam = `%${search}%`;
                params.push(searchParam, searchParam, searchParam);
            }
            
            if (role) {
                query += ' AND u.role = ?';
                params.push(role);
            }
            
            // 添加分页
            const offset = (parseInt(page) - 1) * parseInt(limit);
            query += ' ORDER BY u.created_at DESC LIMIT ? OFFSET ?';
            params.push(parseInt(limit), offset);
            
            // 执行查询
            const users = await db.all(query, params);
            
            // 获取总记录数
            const countQuery = 'SELECT COUNT(*) as total FROM users u LEFT JOIN user_profiles up ON u.id = up.user_id WHERE 1=1' + 
                             (search ? ' AND (u.username LIKE ? OR u.email LIKE ? OR up.full_name LIKE ?)' : '') +
                             (role ? ' AND u.role = ?' : '');
            const countParams = search ? [searchParam, searchParam, searchParam] : [];
            if (role) countParams.push(role);
            const total = await db.get(countQuery, countParams);
            
            res.json({
                success: true,
                data: {
                    users,
                    pagination: {
                        page: parseInt(page),
                        limit: parseInt(limit),
                        total: total.total,
                        pages: Math.ceil(total.total / parseInt(limit))
                    }
                },
                message: '用户列表获取成功'
            });
        } catch (error) {
            logger.error('获取用户列表失败:', error);
            next(error);
        }
    }

    /**
     * 获取单个用户详情
     */
    async getUserById(req, res, next) {
        try {
            const { id } = req.params;
            
            const user = await db.get(
                'SELECT u.*, up.* FROM users u LEFT JOIN user_profiles up ON u.id = up.user_id WHERE u.id = ?',
                [id]
            );
            
            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 获取用户权限
            const permissions = await db.all(
                'SELECT permission_type, permission_level FROM user_permissions WHERE user_id = ? AND is_active = 1',
                [id]
            );
            
            user.permissions = permissions;
            
            res.json({
                success: true,
                data: user,
                message: '用户详情获取成功'
            });
        } catch (error) {
            logger.error('获取用户详情失败:', error);
            next(error);
        }
    }

    /**
     * 创建用户
     */
    async createUser(req, res, next) {
        try {
            const { username, email, password, role, full_name, bio, learning_goal } = req.body;
            
            // 验证必填字段
            if (!username || !email || !password || !role) {
                return res.status(400).json({
                    success: false,
                    message: '用户名、邮箱、密码和角色是必填字段'
                });
            }
            
            // 检查用户名是否已存在
            const existingUser = await db.get('SELECT id FROM users WHERE username = ?', [username]);
            if (existingUser) {
                return res.status(400).json({
                    success: false,
                    message: '用户名已存在'
                });
            }
            
            // 检查邮箱是否已存在
            const existingEmail = await db.get('SELECT id FROM users WHERE email = ?', [email]);
            if (existingEmail) {
                return res.status(400).json({
                    success: false,
                    message: '邮箱已存在'
                });
            }
            
            // 加密密码
            const hashedPassword = await bcrypt.hash(password, 10);
            
            // 开始事务
            await db.run('BEGIN TRANSACTION');
            
            try {
                // 创建用户
                const result = await db.run(
                    'INSERT INTO users (username, email, password, role, status) VALUES (?, ?, ?, ?, ?)',
                    [username, email, hashedPassword, role, 'active']
                );
                
                const userId = result.lastID;
                
                // 创建用户资料
                await db.run(
                    'INSERT INTO user_profiles (user_id, full_name, bio, learning_goal) VALUES (?, ?, ?, ?)',
                    [userId, full_name || '', bio || '', learning_goal || '']
                );
                
                // 提交事务
                await db.run('COMMIT');
                
                logger.info(`用户创建成功: ${username}`, { userId, role });
                
                res.status(201).json({
                    success: true,
                    data: { userId },
                    message: '用户创建成功'
                });
            } catch (error) {
                await db.run('ROLLBACK');
                throw error;
            }
        } catch (error) {
            logger.error('创建用户失败:', error);
            next(error);
        }
    }

    /**
     * 更新用户信息
     */
    async updateUser(req, res, next) {
        try {
            const { id } = req.params;
            const { email, role, status, full_name, bio, learning_goal } = req.body;
            
            // 检查用户是否存在
            const existingUser = await db.get('SELECT id FROM users WHERE id = ?', [id]);
            if (!existingUser) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 开始事务
            await db.run('BEGIN TRANSACTION');
            
            try {
                // 更新用户基本信息
                await db.run(
                    'UPDATE users SET email = ?, role = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    [email, role, status, id]
                );
                
                // 更新用户资料
                await db.run(
                    'INSERT OR REPLACE INTO user_profiles (user_id, full_name, bio, learning_goal, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)',
                    [id, full_name || '', bio || '', learning_goal || '']
                );
                
                // 提交事务
                await db.run('COMMIT');
                
                logger.info(`用户更新成功: ${id}`, { role, status });
                
                res.json({
                    success: true,
                    message: '用户更新成功'
                });
            } catch (error) {
                await db.run('ROLLBACK');
                throw error;
            }
        } catch (error) {
            logger.error('更新用户失败:', error);
            next(error);
        }
    }

    /**
     * 更新用户密码
     */
    async updatePassword(req, res, next) {
        try {
            const { id } = req.params;
            const { password } = req.body;
            
            // 检查用户是否存在
            const existingUser = await db.get('SELECT id FROM users WHERE id = ?', [id]);
            if (!existingUser) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 加密密码
            const hashedPassword = await bcrypt.hash(password, 10);
            
            // 更新密码
            await db.run(
                'UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                [hashedPassword, id]
            );
            
            logger.info(`用户密码更新成功: ${id}`);
            
            res.json({
                success: true,
                message: '密码更新成功'
            });
        } catch (error) {
            logger.error('更新用户密码失败:', error);
            next(error);
        }
    }

    /**
     * 删除用户
     */
    async deleteUser(req, res, next) {
        try {
            const { id } = req.params;
            
            // 检查用户是否存在
            const existingUser = await db.get('SELECT id FROM users WHERE id = ?', [id]);
            if (!existingUser) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 开始事务
            await db.run('BEGIN TRANSACTION');
            
            try {
                // 删除用户相关数据
                await db.run('DELETE FROM user_permissions WHERE user_id = ?', [id]);
                await db.run('DELETE FROM user_profiles WHERE user_id = ?', [id]);
                await db.run('DELETE FROM user_sessions WHERE user_id = ?', [id]);
                await db.run('DELETE FROM auth_tokens WHERE user_id = ?', [id]);
                
                // 删除用户
                await db.run('DELETE FROM users WHERE id = ?', [id]);
                
                // 提交事务
                await db.run('COMMIT');
                
                logger.info(`用户删除成功: ${id}`);
                
                res.json({
                    success: true,
                    message: '用户删除成功'
                });
            } catch (error) {
                await db.run('ROLLBACK');
                throw error;
            }
        } catch (error) {
            logger.error('删除用户失败:', error);
            next(error);
        }
    }

    /**
     * 更新用户权限
     */
    async updateUserPermissions(req, res, next) {
        try {
            const { id } = req.params;
            const permissions = req.body.permissions;
            
            // 检查用户是否存在
            const existingUser = await db.get('SELECT id FROM users WHERE id = ?', [id]);
            if (!existingUser) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 开始事务
            await db.run('BEGIN TRANSACTION');
            
            try {
                // 删除现有权限
                await db.run('DELETE FROM user_permissions WHERE user_id = ?', [id]);
                
                // 添加新权限
                if (Array.isArray(permissions)) {
                    for (const perm of permissions) {
                        await db.run(
                            'INSERT INTO user_permissions (user_id, permission_type, permission_level, is_active) VALUES (?, ?, ?, ?)',
                            [id, perm.type, perm.level, perm.is_active || 1]
                        );
                    }
                }
                
                // 提交事务
                await db.run('COMMIT');
                
                logger.info(`用户权限更新成功: ${id}`);
                
                res.json({
                    success: true,
                    message: '用户权限更新成功'
                });
            } catch (error) {
                await db.run('ROLLBACK');
                throw error;
            }
        } catch (error) {
            logger.error('更新用户权限失败:', error);
            next(error);
        }
    }

    /**
     * 获取用户统计信息
     */
    async getUserStats(req, res, next) {
        try {
            // 获取用户总数
            const totalUsers = await db.get('SELECT COUNT(*) as count FROM users');
            
            // 获取按角色分布
            const roleDistribution = await db.all('SELECT role, COUNT(*) as count FROM users GROUP BY role');
            
            // 获取按状态分布
            const statusDistribution = await db.all('SELECT status, COUNT(*) as count FROM users GROUP BY status');
            
            // 获取最近7天注册用户
            const recentUsers = await db.all(
                'SELECT DATE(created_at) as date, COUNT(*) as count FROM users WHERE created_at >= DATE(now, -7 days) GROUP BY DATE(created_at) ORDER BY date ASC'
            );
            
            res.json({
                success: true,
                data: {
                    total: totalUsers.count,
                    roleDistribution,
                    statusDistribution,
                    recentUsers
                },
                message: '用户统计信息获取成功'
            });
        } catch (error) {
            logger.error('获取用户统计信息失败:', error);
            next(error);
        }
    }

    /**
     * 激活/禁用用户
     */
    async toggleUserStatus(req, res, next) {
        try {
            const { id } = req.params;
            const { status } = req.body;
            
            // 检查用户是否存在
            const existingUser = await db.get('SELECT id FROM users WHERE id = ?', [id]);
            if (!existingUser) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 更新用户状态
            await db.run(
                'UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                [status, id]
            );
            
            logger.info(`用户状态更新成功: ${id} - ${status}`);
            
            res.json({
                success: true,
                message: `用户已${status === 'active' ? '激活' : '禁用'}`
            });
        } catch (error) {
            logger.error('更新用户状态失败:', error);
            next(error);
        }
    }

    /**
     * 获取用户活动日志
     */
    async getUserActivity(req, res, next) {
        try {
            const { id } = req.params;
            const { limit = 50 } = req.query;
            
            // 检查用户是否存在
            const existingUser = await db.get('SELECT id FROM users WHERE id = ?', [id]);
            if (!existingUser) {
                return res.status(404).json({
                    success: false,
                    message: '用户不存在'
                });
            }
            
            // 获取用户活动日志
            const logs = await db.all(
                'SELECT * FROM audit_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
                [id, parseInt(limit)]
            );
            
            res.json({
                success: true,
                data: { logs },
                message: '用户活动日志获取成功'
            });
        } catch (error) {
            logger.error('获取用户活动日志失败:', error);
            next(error);
        }
    }
}

module.exports = new UserController();

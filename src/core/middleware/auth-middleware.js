/**
 * MTSCOS AI 系统 - 认证中间件
 * 处理用户认证和权限验证
 */

const logger = require('../logger');

class AuthMiddleware {
    // 验证用户是否已登录
    async requireAuth(req, res, next) {
        try {
            // 模拟认证检查
            // 在实际应用中，这里应该检查JWT token或session
            const mockUser = {
                id: 1,
                username: 'admin',
                role: 'admin'
            };

            req.user = mockUser;
            next();
        } catch (error) {
            logger.error('认证失败:', error);
            res.status(401).json({
                status: 'error',
                message: '未授权访问'
            });
        }
    }

    // 验证用户是否为管理员
    async requireAdmin(req, res, next) {
        try {
            // 先验证用户是否已登录
            await this.requireAuth(req, res, (err) => {
                if (err) return next(err);
            });

            // 模拟管理员权限检查
            if (req.user && req.user.role === 'admin') {
                next();
            } else {
                res.status(403).json({
                    status: 'error',
                    message: '需要管理员权限'
                });
            }
        } catch (error) {
            logger.error('管理员权限验证失败:', error);
            res.status(403).json({
                status: 'error',
                message: '需要管理员权限'
            });
        }
    }

    // 验证用户是否为审计员
    async requireAuditor(req, res, next) {
        try {
            // 先验证用户是否已登录
            await this.requireAuth(req, res, (err) => {
                if (err) return next(err);
            });

            // 模拟审计员权限检查
            const allowedRoles = ['admin', 'auditor'];
            if (req.user && allowedRoles.includes(req.user.role)) {
                next();
            } else {
                res.status(403).json({
                    status: 'error',
                    message: '需要审计员权限'
                });
            }
        } catch (error) {
            logger.error('审计员权限验证失败:', error);
            res.status(403).json({
                status: 'error',
                message: '需要审计员权限'
            });
        }
    }
}

module.exports = new AuthMiddleware();

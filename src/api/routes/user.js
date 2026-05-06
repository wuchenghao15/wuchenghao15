/**
 * 用户管理API路由
 * 处理用户相关的API请求
 */

const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
const authMiddleware = require('../../core/middleware/auth-middleware');
const permissionManager = require('../../core/security/permission-manager');

// 用户管理权限中间件
const userManagementPermission = permissionManager.requirePermission(
    permissionManager.permissions.USER_MANAGEMENT,
    permissionManager.permissionLevels.VIEW
);

const userManagementModifyPermission = permissionManager.requirePermission(
    permissionManager.permissions.USER_MANAGEMENT,
    permissionManager.permissionLevels.MODIFY
);

// 获取用户列表
router.get('/', 
    authMiddleware.requireAuth, 
    userManagementPermission,
    userController.getUsers
);

// 获取单个用户详情
router.get('/:id', 
    authMiddleware.requireAuth, 
    userManagementPermission,
    userController.getUserById
);

// 创建用户
router.post('/', 
    authMiddleware.requireAuth, 
    userManagementModifyPermission,
    userController.createUser
);

// 更新用户信息
router.put('/:id', 
    authMiddleware.requireAuth, 
    userManagementModifyPermission,
    userController.updateUser
);

// 更新用户密码
router.put('/:id/password', 
    authMiddleware.requireAuth, 
    userManagementModifyPermission,
    userController.updatePassword
);

// 删除用户
router.delete('/:id', 
    authMiddleware.requireAuth, 
    userManagementModifyPermission,
    userController.deleteUser
);

// 更新用户权限
router.put('/:id/permissions', 
    authMiddleware.requireAuth, 
    userManagementModifyPermission,
    userController.updateUserPermissions
);

// 获取用户统计信息
router.get('/stats', 
    authMiddleware.requireAuth, 
    userManagementPermission,
    userController.getUserStats
);

// 激活/禁用用户
router.put('/:id/status', 
    authMiddleware.requireAuth, 
    userManagementModifyPermission,
    userController.toggleUserStatus
);

// 获取用户活动日志
router.get('/:id/activity', 
    authMiddleware.requireAuth, 
    userManagementPermission,
    userController.getUserActivity
);

module.exports = router;

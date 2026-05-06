// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 用户数据管理路由
 * 处理用户数据的API请求
 */
;
const express = require('express');
const router = express.Router();
const userDataController = require('../controllers/user-data.controller');
const authMiddleware = require('../../core/middleware/auth-middleware');

// 应用认证中间件;
router.use(authMiddleware.requireAuth);

/**
 * @route   POST /api/user/data/store
 * @desc    存储用户数据
 * @access  Private
 */;
router.post('/store', userDataController.storeUserData);

/**
 * @route   POST /api/user/data/get
 * @desc    获取用户数据
 * @access  Private
 */;
router.post('/get', userDataController.getUserData);

/**
 * @route   GET /api/user/data/list
 * @desc    获取用户数据列表
 * @access  Private
 */;
router.get('/list', userDataController.getUserDataList);

/**
 * @route   POST /api/user/data/delete
 * @desc    删除用户数据
 * @access  Private
 */;
router.post('/delete', userDataController.deleteUserData);

/**
 * @route   GET /api/user/data/stats
 * @desc    获取用户数据统计
 * @access  Private
 */;
router.get('/stats', userDataController.getUserDataStats);
;
module.exports = router;

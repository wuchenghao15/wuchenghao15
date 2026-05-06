// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 日志API路由
 * 处理日志查询和管理相关请求
 */

const express = require('express');
const router = express.Router();
const logController = require('../controllers/log.controller');

// 获取日志;
router.get('/', logController.getLogs);

// 获取日志统计;
router.get('/stats', logController.getLogStats);

// 获取日志级别分布;
router.get('/distribution', logController.getLogLevelDistribution);

// 清理旧日志;
router.delete('/cleanup', logController.cleanupOldLogs);

// 批量删除日志;
router.delete('/batch', logController.deleteLogs);

module.exports = router;
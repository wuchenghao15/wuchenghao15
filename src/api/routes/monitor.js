// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 监控API路由
 * 处理系统监控相关的API请求
 */

const express = require('express');
const router = express.Router();
const monitorController = require('../controllers/monitor.controller');

// 获取系统监控数据
router.get('/system', monitorController.getSystemStatus);

// 获取服务监控数据
router.get('/services', monitorController.getServicesStatus);

// 获取客户端监控数据
router.get('/clients', monitorController.getClientsStatus);

// 获取AI监控数据
router.get('/ai', monitorController.getAIStatus);

// 获取监控统计数据
router.get('/stats', monitorController.getMonitorStats);

// 获取监控历史数据
router.get('/history', monitorController.getMonitorHistory);

// 获取监控告警
router.get('/alerts', monitorController.getAlerts);

// 清除监控告警
router.delete('/alerts/:id', monitorController.clearAlert);

module.exports = router;
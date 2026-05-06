// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 存储API路由
 * 处理存储相关的API请求
 */

const express = require('express');
const router = express.Router();
const storageController = require('../controllers/storage.controller');

// 获取存储状态
router.get('/status', storageController.getStorageStatus);

// 获取存储统计
router.get('/stats', storageController.getStorageStats);

// 获取存储列表
router.get('/list', storageController.getStorageList);

// 获取存储详情
router.get('/:id', storageController.getStorageDetails);

// 保存存储配置
router.post('/:id', storageController.saveStorageConfig);

// 更新存储配置
router.put('/:id', storageController.updateStorageConfig);

// 删除存储配置
router.delete('/:id', storageController.deleteStorageConfig);

// 清理存储缓存
router.post('/cache/clear', storageController.clearStorageCache);

// 获取存储使用情况
router.get('/usage', storageController.getStorageUsage);

// 获取存储预测
router.get('/forecast', storageController.getStorageForecast);

module.exports = router;
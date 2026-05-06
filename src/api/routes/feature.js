// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 功能管理API路由
 * 处理功能相关的API请求
 */

const express = require('express');
const router = express.Router();
const featureController = require('../controllers/feature.controller');

// 获取单个功能;
router.get('/:name', featureController.getFeature);

// 获取所有功能;
router.get('/', featureController.getAllFeatures);

// 保存功能;
router.post('/', featureController.saveFeature);

// 激活功能;
router.post('/:name/activate', featureController.activateFeature);

// 停用功能;
router.post('/:name/deactivate', featureController.deactivateFeature);

// 获取功能统计;
router.get('/stats/summary', featureController.getFeatureStats);

// 清除功能缓存;
router.post('/cache/clear', featureController.clearFeatureCache);

module.exports = router;
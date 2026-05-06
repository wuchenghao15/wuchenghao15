// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 配置管理API路由
 * 处理配置相关的API请求
 */

const express = require('express');
const router = express.Router();
const configController = require('../controllers/config.controller');

// 获取单个配置;
router.get('/:key', configController.getConfig);

// 获取所有配置;
router.get('/', configController.getAllConfigs);

// 保存配置;
router.post('/:key', configController.saveConfig);

// 更新配置;
router.put('/:key', configController.updateConfig);

// 删除配置;
router.delete('/:key', configController.deleteConfig);

// 获取配置统计;
router.get('/stats/summary', configController.getConfigStats);

// 清除配置缓存;
router.post('/cache/clear', configController.clearConfigCache);

module.exports = router;
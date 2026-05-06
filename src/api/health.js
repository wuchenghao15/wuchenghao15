/**
 * MTSCOS AI 系统 - 健康检查端点
 */

const express = require('express');
const router = express.Router();
const packageJson = require('../../package.json');

// 健康检查端点
router.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: packageJson.version,
        uptime: process.uptime()
    });
});

module.exports = router;

/**
 * MTSCOS AI 系统 - 审核API
 * 用于管理审核流程和数据
 */

const express = require('express');
const router = express.Router();
const auditService = require('../../core/audit/audit-service');
const authMiddleware = require('../../core/middleware/auth-middleware');

// 获取待处理审核列表
router.get('/pending', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const audits = await auditService.getPendingAudits();
        res.json({
            status: 'success',
            data: audits
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取审核历史
router.get('/history', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const audits = await auditService.getAuditHistory();
        res.json({
            status: 'success',
            data: audits
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取审核详情
router.get('/:id', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const audit = await auditService.getAuditById(req.params.id);
        res.json({
            status: 'success',
            data: audit
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 批准审核
router.post('/:id/approve', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const audit = await auditService.approveAudit(req.params.id, req.user.id, req.body.comment);
        res.json({
            status: 'success',
            data: audit
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 拒绝审核
router.post('/:id/reject', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const audit = await auditService.rejectAudit(req.params.id, req.user.id, req.body.comment);
        res.json({
            status: 'success',
            data: audit
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 回滚操作
router.post('/:id/rollback', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const result = await auditService.rollbackOperation(req.params.id, req.user.id);
        res.json({
            status: 'success',
            data: result
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取审核统计
router.get('/stats', authMiddleware.requireAdmin, async (req, res) => {
    try {
        const stats = await auditService.getAuditStats();
        res.json({
            status: 'success',
            data: stats
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

module.exports = router;

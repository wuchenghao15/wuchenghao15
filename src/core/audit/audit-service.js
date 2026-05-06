/**
 * MTSCOS AI 系统 - 审核服务
 * 处理所有审核相关的业务逻辑
 */

const logger = require('../logger');
const multiLevelAudit = require('./multi-level-audit');

class AuditService {
    constructor() {
        this.audits = []; // 临时存储，后续应替换为数据库操作
        this.auditIdCounter = 1;
    }

    // 获取待处理审核列表
    async getPendingAudits() {
        try {
            // 模拟待处理审核列表
            return this.audits.filter(audit => audit.status === 'pending' || audit.status === 'in_progress');
        } catch (error) {
            logger.error('获取待处理审核列表失败:', error);
            throw error;
        }
    }

    // 获取审核历史
    async getAuditHistory() {
        try {
            // 模拟审核历史
            return this.audits.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        } catch (error) {
            logger.error('获取审核历史失败:', error);
            throw error;
        }
    }

    // 获取审核详情
    async getAuditById(id) {
        try {
            // 模拟获取审核详情
            const audit = this.audits.find(a => a.id === parseInt(id));
            if (!audit) {
                throw new Error('审核记录不存在');
            }
            return audit;
        } catch (error) {
            logger.error('获取审核详情失败:', error);
            throw error;
        }
    }

    // 批准审核
    async approveAudit(id, userId, comment) {
        try {
            // 模拟批准审核
            const audit = await this.getAuditById(id);
            audit.status = 'approved';
            audit.approvedBy = userId;
            audit.approvedAt = new Date().toISOString();
            audit.comment = comment;
            audit.updatedAt = new Date().toISOString();
            return audit;
        } catch (error) {
            logger.error('批准审核失败:', error);
            throw error;
        }
    }

    // 拒绝审核
    async rejectAudit(id, userId, comment) {
        try {
            // 模拟拒绝审核
            const audit = await this.getAuditById(id);
            audit.status = 'rejected';
            audit.rejectedBy = userId;
            audit.rejectedAt = new Date().toISOString();
            audit.comment = comment;
            audit.updatedAt = new Date().toISOString();
            return audit;
        } catch (error) {
            logger.error('拒绝审核失败:', error);
            throw error;
        }
    }

    // 回滚操作
    async rollbackOperation(id, userId) {
        try {
            // 模拟回滚操作
            const audit = await this.getAuditById(id);
            audit.rollbackStatus = 'completed';
            audit.rolledBackBy = userId;
            audit.rolledBackAt = new Date().toISOString();
            audit.updatedAt = new Date().toISOString();
            return {
                success: true,
                audit: audit,
                message: '操作已回滚'
            };
        } catch (error) {
            logger.error('回滚操作失败:', error);
            throw error;
        }
    }

    // 获取审核统计
    async getAuditStats() {
        try {
            // 模拟获取审核统计
            return {
                total: this.audits.length,
                pending: this.audits.filter(a => a.status === 'pending' || a.status === 'in_progress').length,
                approved: this.audits.filter(a => a.status === 'approved').length,
                rejected: this.audits.filter(a => a.status === 'rejected').length,
                averageProcessingTime: '2.5h',
                recentAudits: this.audits.slice(0, 5).map(a => ({
                    id: a.id,
                    type: a.type,
                    status: a.status,
                    createdAt: a.createdAt
                }))
            };
        } catch (error) {
            logger.error('获取审核统计失败:', error);
            throw error;
        }
    }

    // 创建审核记录（供内部调用）
    async createAudit(auditData) {
        try {
            const audit = {
                id: this.auditIdCounter++,
                type: auditData.type,
                resourceId: auditData.resourceId,
                resourceType: auditData.resourceType,
                action: auditData.action,
                requestedBy: auditData.requestedBy,
                requestedAt: new Date().toISOString(),
                status: 'pending',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                flow: multiLevelAudit.createMultiLevelAudit(auditData, auditData.riskLevel || 'medium')
            };

            this.audits.push(audit);
            return audit;
        } catch (error) {
            logger.error('创建审核记录失败:', error);
            throw error;
        }
    }
}

module.exports = new AuditService();

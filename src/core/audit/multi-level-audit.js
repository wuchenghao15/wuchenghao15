/**
 * MTSCOS AI 系统 - 多级审核支持
 * 根据操作风险等级设置不同的审核层级
 */

class MultiLevelAudit {
    constructor() {
        this.auditLevels = {
            1: {
                name: '一级审核',
                role: 'auditor',
                description: '基础审核，处理一般风险操作'
            },
            2: {
                name: '二级审核',
                role: 'senior_auditor',
                description: '高级审核，处理高风险操作'
            },
            3: {
                name: '三级审核',
                role: 'admin',
                description: '管理员审核，处理关键风险操作'
            }
        };
    }
    
    // 获取审核层级配置
    getAuditLevelConfig(riskLevel) {
        const levelConfig = {
            'low': 0,
            'medium': 1,
            'high': 2,
            'critical': 3
        };
        
        return levelConfig[riskLevel] || 1;
    }
    
    // 创建多级审核流程
    createMultiLevelAudit(auditInfo, riskLevel) {
        const requiredLevel = this.getAuditLevelConfig(riskLevel);
        
        if (requiredLevel === 0) {
            return null; // 不需要多级审核
        }
        
        const auditFlow = {
            currentLevel: 1,
            requiredLevels: requiredLevel,
            levels: [],
            status: 'pending'
        };
        
        // 创建审核层级
        for (let i = 1; i <= requiredLevel; i++) {
            auditFlow.levels.push({
                level: i,
                name: this.auditLevels[i].name,
                requiredRole: this.auditLevels[i].role,
                status: i === 1 ? 'pending' : 'not_started',
                approvedBy: null,
                approvedAt: null,
                comment: null
            });
        }
        
        return auditFlow;
    }
    
    // 处理审核结果
    processAuditResult(auditId, level, result, auditorId, comment) {
        // 这里可以添加审核结果处理逻辑
        // 例如：更新审核流程状态，通知下一审核层级等
        
        return {
            auditId: auditId,
            level: level,
            result: result,
            auditorId: auditorId,
            comment: comment,
            processedAt: new Date().toISOString()
        };
    }
    
    // 检查是否所有层级都已审核
    checkIfAllLevelsApproved(auditFlow) {
        if (!auditFlow) return true;
        
        return auditFlow.levels.every(level => level.status === 'approved');
    }
    
    // 获取下一个审核层级
    getNextAuditLevel(auditFlow) {
        if (!auditFlow) return null;
        
        const nextLevel = auditFlow.levels.find(level => level.status === 'pending');
        return nextLevel ? nextLevel.level : null;
    }
}

module.exports = new MultiLevelAudit();

/**
 * MTSCOS AI 系统 - 审核中间件
 * 自动记录和审核系统操作
 */

const auditService = require('../audit/audit-service');

// 审核中间件
const auditMiddleware = async (req, res, next) => {
    // 记录操作信息
    const operationInfo = {
        userId: req.user ? req.user.id : null,
        operation: req.method + ' ' + req.path,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        requestBody: req.body,
        timestamp: new Date().toISOString()
    };
    
    try {
        // 检查是否需要审核
        const needsAudit = await auditService.checkIfNeedsAudit(operationInfo);
        
        if (needsAudit) {
            // 创建审核记录
            const auditId = await auditService.createAuditRecord(operationInfo);
            
            // 将审核ID添加到请求
            req.auditId = auditId;
            
            // 对于需要立即审核的操作，暂停执行
            if (needsAudit === 'immediate') {
                res.status(202).json({
                    status: 'pending',
                    message: '操作需要审核，请等待审核结果',
                    auditId: auditId
                });
                return;
            }
        }
        
        next();
    } catch (error) {
        console.error('审核中间件错误:', error);
        next(); // 即使审核失败，也继续执行请求
    }
};

module.exports = {
    auditMiddleware
};

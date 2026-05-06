/**
 * MTSCOS AI 系统 - 审核风险评估
 * 智能评估操作风险等级
 */

class RiskAssessment {
    constructor() {
        this.riskLevels = ['low', 'medium', 'high', 'critical'];
        this.riskRules = {
            // 操作类型风险权重
            operationRisk: {
                'user_delete': 0.9,
                'permission_change': 0.8,
                'data_export': 0.7,
                'user_register': 0.5,
                'data_modify': 0.4,
                'data_view': 0.2
            },
            // 用户角色风险权重
            roleRisk: {
                'anonymous': 0.6,
                'user': 0.3,
                'admin': 0.1
            },
            // 时间风险权重（非常规时间）
            timeRisk: {
                'night': 0.5,
                'weekend': 0.3
            }
        };
    }
    
    // 评估操作风险
    assessRisk(operationInfo) {
        let riskScore = 0;
        
        // 1. 评估操作类型风险
        const operationType = this.extractOperationType(operationInfo.operation);
        const operationRisk = this.riskRules.operationRisk[operationType] || 0.3;
        riskScore += operationRisk * 0.5;
        
        // 2. 评估用户角色风险
        const userRole = operationInfo.userId ? 'user' : 'anonymous';
        const roleRisk = this.riskRules.roleRisk[userRole] || 0.3;
        riskScore += roleRisk * 0.3;
        
        // 3. 评估时间风险
        const timeRisk = this.assessTimeRisk(operationInfo.timestamp);
        riskScore += timeRisk * 0.2;
        
        // 4. 评估IP风险（简化版）
        const ipRisk = this.assessIpRisk(operationInfo.ip);
        riskScore += ipRisk * 0.1;
        
        // 5. 评估请求频率风险
        const frequencyRisk = this.assessFrequencyRisk(operationInfo.userId, operationType);
        riskScore += frequencyRisk * 0.1;
        
        // 确定风险等级
        const riskLevel = this.getRiskLevel(riskScore);
        
        return {
            riskScore: Math.round(riskScore * 100) / 100,
            riskLevel: riskLevel,
            factors: {
                operationType: operationType,
                userRole: userRole,
                timeRisk: timeRisk,
                ipRisk: ipRisk,
                frequencyRisk: frequencyRisk
            }
        };
    }
    
    // 提取操作类型
    extractOperationType(operation) {
        const operationMap = {
            'POST /users': 'user_register',
            'DELETE /users/': 'user_delete',
            'PUT /permissions/': 'permission_change',
            'GET /data/export': 'data_export',
            'PUT /data/': 'data_modify',
            'GET /data/': 'data_view'
        };
        
        for (const [pattern, type] of Object.entries(operationMap)) {
            if (operation.includes(pattern)) {
                return type;
            }
        }
        
        return 'data_view';
    }
    
    // 评估时间风险
    assessTimeRisk(timestamp) {
        const date = new Date(timestamp);
        const hour = date.getHours();
        const day = date.getDay();
        
        // 夜间（22:00-06:00）
        if (hour >= 22 || hour < 6) {
            return this.riskRules.timeRisk['night'] || 0.5;
        }
        
        // 周末
        if (day === 0 || day === 6) {
            return this.riskRules.timeRisk['weekend'] || 0.3;
        }
        
        return 0;
    }
    
    // 评估IP风险（简化版）
    assessIpRisk(ip) {
        // 这里可以添加更复杂的IP风险评估逻辑
        // 例如：检查IP是否在黑名单中，是否是新IP等
        return 0;
    }
    
    // 评估请求频率风险（简化版）
    assessFrequencyRisk(userId, operationType) {
        // 这里可以添加更复杂的请求频率评估逻辑
        // 例如：检查用户在短时间内的请求次数
        return 0;
    }
    
    // 根据风险分数确定风险等级
    getRiskLevel(riskScore) {
        if (riskScore >= 0.8) {
            return 'critical';
        } else if (riskScore >= 0.6) {
            return 'high';
        } else if (riskScore >= 0.3) {
            return 'medium';
        } else {
            return 'low';
        }
    }
    
    // 获取风险等级对应的审核要求
    getAuditRequirements(riskLevel) {
        const requirements = {
            'low': { type: 'ai_audit', approvalCount: 0 },
            'medium': { type: 'ai_audit', approvalCount: 0 },
            'high': { type: 'manual_audit', approvalCount: 1 },
            'critical': { type: 'multi_level_audit', approvalCount: 2 }
        };
        
        return requirements[riskLevel] || requirements['medium'];
    }
}

module.exports = new RiskAssessment();

/**
 * MTSCOS AI 系统 - 用户行为分析器
 * 用于分析用户行为并生成优化建议
 */

class UserBehaviorAnalyzer {
    constructor() {
        this.behaviorHistory = [];
        this.riskThresholds = {
            HIGH: 80,
            MEDIUM: 50,
            LOW: 20
        };
    }

    // 记录用户行为
    recordBehavior(behavior) {
        this.behaviorHistory.push({
            ...behavior,
            timestamp: new Date().toISOString()
        });
        
        // 只保留最近1000条记录
        if (this.behaviorHistory.length > 1000) {
            this.behaviorHistory.shift();
        }
    }

    // 分析用户行为
    analyzeUserBehavior(userId) {
        const userBehaviors = this.behaviorHistory.filter(b => b.userId === userId);
        
        // 分析行为模式
        const behaviorAnalysis = {
            userId,
            totalActions: userBehaviors.length,
            actionTypes: {},
            frequentActions: [],
            riskScore: this.calculateRiskScore(userBehaviors)
        };
        
        // 统计行为类型
        userBehaviors.forEach(behavior => {
            behaviorAnalysis.actionTypes[behavior.actionType] = (behaviorAnalysis.actionTypes[behavior.actionType] || 0) + 1;
        });
        
        // 找出频繁行为
        const sortedActions = Object.entries(behaviorAnalysis.actionTypes)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5);
        behaviorAnalysis.frequentActions = sortedActions.map(([actionType, count]) => ({ actionType, count }));
        
        return behaviorAnalysis;
    }

    // 计算风险评分
    calculateRiskScore(behaviors) {
        let riskScore = 0;
        
        // 简单的风险评分算法
        behaviors.forEach(behavior => {
            switch (behavior.actionType) {
                case 'LOGIN':
                    riskScore += 5;
                    break;
                case 'LOGOUT':
                    riskScore -= 5;
                    break;
                case 'API_CALL':
                    riskScore += 2;
                    break;
                case 'ADMIN_ACTION':
                    riskScore += 10;
                    break;
                default:
                    riskScore += 1;
            }
        });
        
        // 限制在0-100之间
        return Math.max(0, Math.min(100, riskScore));
    }

    // 生成优化建议
    generateSuggestions(analysis) {
        const suggestions = [];
        
        if (analysis.riskScore > this.riskThresholds.HIGH) {
            suggestions.push({
                type: "security",
                message: "检测到高风险用户行为，建议加强安全监控",
                priority: "high"
            });
        }
        
        if (analysis.frequentActions.length > 0) {
            suggestions.push({
                type: "feature",
                message: '用户频繁执行' + analysis.frequentActions[0].actionType + '操作，建议优化该功能',
                priority: "medium"
            });
        }
        
        return suggestions;
    }
}

module.exports = UserBehaviorAnalyzer;

/**
 * MTSCOS AI 系统 - 审核日志分析
 * 分析审核数据并生成见解
 */

class LogAnalysis {
    constructor() {
        this.logPatterns = {
            // 异常登录模式
            unusualLogin: {
                pattern: /(failed login|invalid password).*multiple times/i,
                description: '多次失败登录尝试',
                severity: 'high'
            },
            // 批量操作模式
            bulkOperation: {
                pattern: /(bulk delete|mass update|batch process)/i,
                description: '批量操作',
                severity: 'medium'
            },
            // 权限提升模式
            privilegeEscalation: {
                pattern: /(permission change|role upgrade|admin access)/i,
                description: '权限提升操作',
                severity: 'critical'
            }
        };
    }
    
    // 分析审核日志
    analyzeAuditLogs(logs) {
        const insights = {
            patterns: [],
            anomalies: [],
            trends: {
                byDay: {},
                byHour: {},
                byOperation: {}
            }
        };
        
        logs.forEach(log => {
            // 1. 检测模式
            for (const [patternName, patternConfig] of Object.entries(this.logPatterns)) {
                if (patternConfig.pattern.test(log.message)) {
                    insights.patterns.push({
                        logId: log.id,
                        pattern: patternName,
                        description: patternConfig.description,
                        severity: patternConfig.severity,
                        log: log
                    });
                }
            }
            
            // 2. 统计趋势
            const date = new Date(log.timestamp).toISOString().split('T')[0];
            const hour = new Date(log.timestamp).getHours();
            const operation = log.operation;
            
            // 按天统计
            insights.trends.byDay[date] = (insights.trends.byDay[date] || 0) + 1;
            
            // 按小时统计
            insights.trends.byHour[hour] = (insights.trends.byHour[hour] || 0) + 1;
            
            // 按操作统计
            insights.trends.byOperation[operation] = (insights.trends.byOperation[operation] || 0) + 1;
        });
        
        // 3. 检测异常
        insights.anomalies = this.detectAnomalies(insights.trends);
        
        return insights;
    }
    
    // 检测异常
    detectAnomalies(trends) {
        const anomalies = [];
        
        // 检测操作频率异常
        const avgOperationsPerDay = Object.values(trends.byDay).reduce((sum, count) => sum + count, 0) / Object.values(trends.byDay).length;
        const stdDev = this.calculateStandardDeviation(Object.values(trends.byDay));
        
        for (const [date, count] of Object.entries(trends.byDay)) {
            if (count > avgOperationsPerDay + 2 * stdDev) {
                anomalies.push({
                    type: 'high_operation_count',
                    date: date,
                    count: count,
                    average: avgOperationsPerDay,
                    description: '操作频率异常高于平均值'
                });
            }
        }
        
        // 检测非常规时间操作
        for (const [hour, count] of Object.entries(trends.byHour)) {
            if ((hour >= 22 || hour < 6) && count > 10) {
                anomalies.push({
                    type: 'unusual_time_operation',
                    hour: hour,
                    count: count,
                    description: '非常规时间操作频率异常'
                });
            }
        }
        
        return anomalies;
    }
    
    // 计算标准差
    calculateStandardDeviation(values) {
        const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
        const squaredDifferences = values.map(value => Math.pow(value - avg, 2));
        const avgSquaredDiff = squaredDifferences.reduce((sum, value) => sum + value, 0) / squaredDifferences.length;
        return Math.sqrt(avgSquaredDiff);
    }
    
    // 生成分析报告
    generateAnalysisReport(insights) {
        return {
            generatedAt: new Date().toISOString(),
            totalPatterns: insights.patterns.length,
            totalAnomalies: insights.anomalies.length,
            patterns: insights.patterns,
            anomalies: insights.anomalies,
            trends: insights.trends,
            recommendations: this.generateRecommendations(insights)
        };
    }
    
    // 生成建议
    generateRecommendations(insights) {
        const recommendations = [];
        
        // 根据模式生成建议
        const criticalPatterns = insights.patterns.filter(p => p.severity === 'critical');
        if (criticalPatterns.length > 0) {
            recommendations.push({
                type: 'security_alert',
                description: '检测到关键安全模式，建议立即检查相关日志',
                patterns: criticalPatterns
            });
        }
        
        // 根据异常生成建议
        const highAnomalies = insights.anomalies.filter(a => a.type === 'high_operation_count');
        if (highAnomalies.length > 0) {
            recommendations.push({
                type: 'audit_alert',
                description: '检测到操作频率异常，建议加强监控',
                anomalies: highAnomalies
            });
        }
        
        return recommendations;
    }
}

module.exports = new LogAnalysis();

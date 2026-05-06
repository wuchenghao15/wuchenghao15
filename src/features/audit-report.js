/**
 * MTSCOS AI 系统 - 审核报告功能
 * 生成审核统计和分析报告
 */

const fs = require('fs');
const path = require('path');
const auditService = require('../core/audit/audit-service');

class AuditReport {
    constructor() {
        this.reportsDir = path.join(__dirname, '../reports/audit');
        fs.mkdirSync(this.reportsDir, { recursive: true });
    }
    
    // 生成每日审核报告
    async generateDailyReport(date = new Date()) {
        const reportDate = date.toISOString().split('T')[0];
        const reportFileName = 'audit_report_' + reportDate + '.json';
        const reportPath = path.join(this.reportsDir, reportFileName);
        
        // 获取审核统计数据
        const stats = await auditService.getAuditStats();
        const dailyStats = await auditService.getDailyAuditStats(reportDate);
        
        // 生成报告
        const report = {
            reportDate: reportDate,
            generatedAt: new Date().toISOString(),
            stats: {
                totalAudits: stats.totalAudits,
                pendingAudits: stats.pendingAudits,
                approvedAudits: stats.approvedAudits,
                rejectedAudits: stats.rejectedAudits,
                dailyStats: dailyStats
            },
            topAuditTypes: stats.topAuditTypes,
            auditTrends: stats.auditTrends,
            riskDistribution: stats.riskDistribution
        };
        
        // 写入报告文件
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        return report;
    }
    
    // 生成月度审核报告
    async generateMonthlyReport(year, month) {
        const reportMonth = year + '-' + String(month).padStart(2, '0');
        const reportFileName = 'audit_report_' + reportMonth + '.json';
        const reportPath = path.join(this.reportsDir, reportFileName);
        
        // 获取月度审核统计
        const monthlyStats = await auditService.getMonthlyAuditStats(year, month);
        
        // 生成报告
        const report = {
            reportMonth: reportMonth,
            generatedAt: new Date().toISOString(),
            stats: monthlyStats,
            topAuditTypes: monthlyStats.topAuditTypes,
            auditTrends: monthlyStats.auditTrends,
            riskDistribution: monthlyStats.riskDistribution
        };
        
        // 写入报告文件
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        return report;
    }
    
    // 获取审核报告列表
    getReportList() {
        const reports = [];
        const files = fs.readdirSync(this.reportsDir);
        
        files.forEach(file => {
            if (file.endsWith('.json')) {
                const reportPath = path.join(this.reportsDir, file);
                const reportContent = fs.readFileSync(reportPath, 'utf8');
                const report = JSON.parse(reportContent);
                reports.push({
                    fileName: file,
                    reportDate: report.reportDate || report.reportMonth,
                    generatedAt: report.generatedAt,
                    stats: report.stats
                });
            }
        });
        
        return reports.sort((a, b) => new Date(b.generatedAt) - new Date(a.generatedAt));
    }
    
    // 获取特定报告
    getReport(reportFileName) {
        const reportPath = path.join(this.reportsDir, reportFileName);
        if (fs.existsSync(reportPath)) {
            const reportContent = fs.readFileSync(reportPath, 'utf8');
            return JSON.parse(reportContent);
        }
        return null;
    }
}

module.exports = new AuditReport();

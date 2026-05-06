/**
 * MTSCOS AI 系统 - 服务器监控
 * 监控服务器状态、性能和错误
 */

class ServerMonitor {
    constructor() {
        this.startTime = Date.now();
        this.status = 'running';
        this.errorHistory = [];
        this.performanceData = {
            cpuUsage: 0,
            memoryUsage: 0,
            requestCount: 0,
            responseTime: 0
        };
        this.reset();
    }

    // 获取监控状态
    getStatus() {
        return {
            startTime: this.startTime,
            uptime: Date.now() - this.startTime,
            status: this.status,
            errorHistory: this.errorHistory,
            performance: this.performanceData
        };
    }

    // 记录错误
    recordError(error) {
        this.errorHistory.push({
            timestamp: Date.now(),
            error: error.message || error,
            stack: error.stack || null
        });

        // 只保留最近100条错误记录
        if (this.errorHistory.length > 100) {
            this.errorHistory.shift();
        }
    }

    // 更新性能数据
    updatePerformance(data) {
        this.performanceData = {
            ...this.performanceData,
            ...data
        };
    }

    // 重置监控
    reset() {
        this.errorHistory = [];
        this.performanceData = {
            cpuUsage: Math.random() * 50 + 10, // 模拟10-60%的CPU使用率
            memoryUsage: Math.random() * 40 + 20, // 模拟20-60%的内存使用率
            requestCount: 0,
            responseTime: Math.random() * 200 + 50 // 模拟50-250ms的响应时间
        };
    }

    // 模拟性能数据更新
    simulatePerformanceUpdate() {
        this.performanceData.requestCount++;
        this.performanceData.responseTime = Math.random() * 200 + 50;
    }
}

// 创建单例实例
const serverMonitor = new ServerMonitor();

// 导出服务器监控实例
module.exports = serverMonitor;

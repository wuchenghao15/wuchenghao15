/**
 * MTSCOS AI 系统 - 监控模块
 * 用于监控系统状态
 */

class Monitor {
    constructor() {
        this.metrics = {
            requests: 0,
            errors: 0,
            responseTimes: [],
            startTime: Date.now()
        };
        this.interval = null;
    }
    
    // 启动监控
    start() {
        console.log('[Monitor] 监控系统已启动');
        this.interval = setInterval(() => {
            this.reportMetrics();
        }, 60000); // 每分钟报告一次
    }
    
    // 停止监控
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
            console.log('[Monitor] 监控系统已停止');
        }
    }
    
    // 记录请求
    recordRequest(responseTime) {
        this.metrics.requests++;
        this.metrics.responseTimes.push(responseTime);
    }
    
    // 记录错误
    recordError() {
        this.metrics.errors++;
    }
    
    // 获取平均响应时间
    getAverageResponseTime() {
        if (this.metrics.responseTimes.length === 0) {
            return 0;
        }
        const sum = this.metrics.responseTimes.reduce((acc, time) => acc + time, 0);
        return sum / this.metrics.responseTimes.length;
    }
    
    // 报告指标
    reportMetrics() {
        const uptime = Math.floor((Date.now() - this.metrics.startTime) / 1000);
        const avgResponseTime = this.getAverageResponseTime();
        
        console.log('[Monitor] 系统指标报告:');
        console.log('  - 运行时间: ' + uptime + '秒');
        console.log('  - 请求总数: ' + this.metrics.requests);
        console.log('  - 错误总数: ' + this.metrics.errors);
        console.log('  - 平均响应时间: ' + avgResponseTime.toFixed(2) + 'ms');
    }
    
    // 获取当前指标
    getCurrentMetrics() {
        return {
            ...this.metrics,
            uptime: Math.floor((Date.now() - this.metrics.startTime) / 1000),
            averageResponseTime: this.getAverageResponseTime()
        };
    }
}

module.exports = new Monitor();

#!/usr/bin/env node

/**
 * MTSCOS AI 系统状态监控面板
 * 提供实时系统状态监控、可视化展示和告警通知功能
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const os = require('os');
const { execSync } = require('child_process');

class SystemStatusPanel {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.server = null;
    this.port = 8085; // 默认端口
    this.statusData = {
      system: {},
      resources: {},
      services: {},
      health: {},
      alerts: []
    };
    this.alertHistory = [];
    this.isRunning = false;
    this.monitoringInterval = null;
    
    // 初始化面板
    this.initialize();
  }

  /**
   * 初始化状态面板
   */
  initialize() {
    try {
      // 加载配置文件
      this.config = this.loadConfig();
      
      // 从配置中获取端口
      if (this.config.network?.ports?.statusPanel) {
        this.port = this.config.network.ports.statusPanel;
      }
      
      console.log(`系统状态监控面板初始化完成，将在端口 ${this.port} 启动`);
      
      // 初始化状态数据
      this.initializeStatusData();
      
    } catch (error) {
      console.error('初始化系统状态面板失败:', error.message);
      throw error;
    }
  }

  /**
   * 加载配置文件
   */
  loadConfig() {
    try {
      const configContent = fs.readFileSync(this.configPath, 'utf8');
      return JSON.parse(configContent).stagingEnvironment;
    } catch (error) {
      throw new Error(`无法加载配置文件: ${error.message}`);
    }
  }

  /**
   * 初始化状态数据
   */
  initializeStatusData() {
    this.statusData = {
      system: {
        platform: os.platform(),
        arch: os.arch(),
        release: os.release(),
        hostname: os.hostname(),
        uptime: os.uptime(),
        timestamp: new Date().toISOString()
      },
      resources: {
        cpu: this.getCPUUsage(),
        memory: this.getMemoryInfo(),
        disk: this.getDiskInfo()
      },
      services: {
        monitor: this.checkServiceStatus('environment-monitor'),
        detection: this.checkServiceStatus('auto-detection-repair'),
        maintenance: this.checkServiceStatus('environment-maintenance')
      },
      health: {
        status: 'unknown',
        score: 0,
        issues: [],
        lastCheck: new Date().toISOString()
      },
      alerts: []
    };
  }

  /**
   * 获取CPU使用率
   */
  getCPUUsage() {
    try {
      const cpus = os.cpus();
      const cpuCount = cpus.length;
      
      // 简易CPU使用率计算（实际使用时可能需要更复杂的方法）
      // 这里返回核心数作为参考
      return {
        cores: cpuCount,
        model: cpus[0]?.model || 'Unknown',
        usage: 'N/A' // 在实际环境中可以使用更精确的方法计算
      };
    } catch (error) {
      console.error('获取CPU信息失败:', error.message);
      return {
        cores: 0,
        model: 'Unknown',
        usage: 'Error'
      };
    }
  }

  /**
   * 获取内存信息
   */
  getMemoryInfo() {
    try {
      const totalMem = os.totalmem();
      const freeMem = os.freemem();
      const usedMem = totalMem - freeMem;
      const usedPercent = (usedMem / totalMem * 100).toFixed(2);
      
      return {
        total: this.formatBytes(totalMem),
        free: this.formatBytes(freeMem),
        used: this.formatBytes(usedMem),
        usagePercent: parseFloat(usedPercent),
        thresholdWarning: this.config.resourceLimits?.memory?.warningThreshold || 90,
        thresholdCritical: this.config.resourceLimits?.memory?.limit || 95
      };
    } catch (error) {
      console.error('获取内存信息失败:', error.message);
      return {
        total: '0 B',
        free: '0 B',
        used: '0 B',
        usagePercent: 0,
        thresholdWarning: 90,
        thresholdCritical: 95
      };
    }
  }

  /**
   * 获取磁盘信息
   */
  getDiskInfo() {
    try {
      const baseDir = this.config.basePath;
      
      // 在macOS上获取磁盘使用情况
      if (os.platform() === 'darwin') {
        const dfOutput = execSync(`df -k "${baseDir}"`, { encoding: 'utf8' });
        const lines = dfOutput.trim().split('\n');
        if (lines.length >= 2) {
          const dataLine = lines[1].split(/\s+/);
          const total = parseInt(dataLine[1]) * 1024; // 转换为字节
          const used = parseInt(dataLine[2]) * 1024;
          const free = parseInt(dataLine[3]) * 1024;
          const usagePercent = parseInt(dataLine[4].replace('%', ''));
          
          return {
            total: this.formatBytes(total),
            used: this.formatBytes(used),
            free: this.formatBytes(free),
            usagePercent: usagePercent,
            mountPoint: dataLine[8],
            thresholdWarning: this.config.resourceLimits?.disk?.warningThreshold || 70,
            thresholdCritical: this.config.resourceLimits?.disk?.limit || 80
          };
        }
      }
      
      // 通用情况返回模拟数据
      return {
        total: '100 GB',
        used: '50 GB',
        free: '50 GB',
        usagePercent: 50,
        mountPoint: baseDir,
        thresholdWarning: 70,
        thresholdCritical: 80
      };
    } catch (error) {
      console.error('获取磁盘信息失败:', error.message);
      return {
        total: 'Unknown',
        used: 'Unknown',
        free: 'Unknown',
        usagePercent: 0,
        mountPoint: 'Unknown',
        thresholdWarning: 70,
        thresholdCritical: 80
      };
    }
  }

  /**
   * 格式化字节数
   */
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /**
   * 检查服务状态
   */
  checkServiceStatus(serviceName) {
    try {
      // 使用ps命令检查进程是否存在
      const output = execSync(`ps aux | grep ${serviceName} | grep -v grep`, { encoding: 'utf8' });
      const isRunning = output.length > 0;
      
      if (isRunning) {
        // 提取PID
        const lines = output.trim().split('\n');
        const pid = lines[0].split(/\s+/)[1];
        
        return {
          status: 'running',
          pid: pid,
          lastCheck: new Date().toISOString()
        };
      } else {
        return {
          status: 'stopped',
          pid: null,
          lastCheck: new Date().toISOString()
        };
      }
    } catch (error) {
      return {
        status: 'unknown',
        pid: null,
        lastCheck: new Date().toISOString(),
        error: error.message
      };
    }
  }

  /**
   * 启动状态监控面板服务器
   */
  start() {
    if (this.isRunning) {
      console.log('系统状态监控面板已经在运行中');
      return;
    }

    this.isRunning = true;
    
    // 创建HTTP服务器
    this.server = http.createServer((req, res) => {
      this.handleRequest(req, res);
    });
    
    // 启动服务器
    this.server.listen(this.port, () => {
      console.log(`系统状态监控面板已启动，访问地址: http://localhost:${this.port}`);
    });
    
    // 启动状态监控
    this.startMonitoring();
  }

  /**
   * 启动状态监控
   */
  startMonitoring() {
    // 每秒更新一次状态数据
    this.monitoringInterval = setInterval(() => {
      this.updateStatusData();
      this.checkForAlerts();
    }, 1000);
  }

  /**
   * 更新状态数据
   */
  updateStatusData() {
    try {
      // 更新系统信息
      this.statusData.system.uptime = os.uptime();
      this.statusData.system.timestamp = new Date().toISOString();
      
      // 更新资源使用情况
      this.statusData.resources.cpu = this.getCPUUsage();
      this.statusData.resources.memory = this.getMemoryInfo();
      this.statusData.resources.disk = this.getDiskInfo();
      
      // 更新服务状态
      this.statusData.services.monitor = this.checkServiceStatus('environment-monitor');
      this.statusData.services.detection = this.checkServiceStatus('auto-detection-repair');
      this.statusData.services.maintenance = this.checkServiceStatus('environment-maintenance');
      
      // 更新系统健康状态
      this.updateSystemHealth();
      
    } catch (error) {
      console.error('更新状态数据失败:', error.message);
    }
  }

  /**
   * 更新系统健康状态
   */
  updateSystemHealth() {
    let healthScore = 100;
    const issues = [];
    
    // 检查内存使用
    const memUsage = this.statusData.resources.memory.usagePercent;
    const memWarning = this.statusData.resources.memory.thresholdWarning;
    const memCritical = this.statusData.resources.memory.thresholdCritical;
    
    if (memUsage >= memCritical) {
      healthScore -= 40;
      issues.push(`内存使用率严重超标: ${memUsage}%`);
    } else if (memUsage >= memWarning) {
      healthScore -= 20;
      issues.push(`内存使用率警告: ${memUsage}%`);
    }
    
    // 检查磁盘使用
    const diskUsage = this.statusData.resources.disk.usagePercent;
    const diskWarning = this.statusData.resources.disk.thresholdWarning;
    const diskCritical = this.statusData.resources.disk.thresholdCritical;
    
    if (diskUsage >= diskCritical) {
      healthScore -= 30;
      issues.push(`磁盘使用率严重超标: ${diskUsage}%`);
    } else if (diskUsage >= diskWarning) {
      healthScore -= 15;
      issues.push(`磁盘使用率警告: ${diskUsage}%`);
    }
    
    // 检查服务状态
    let serviceCount = 0;
    let runningServices = 0;
    
    for (const [service, status] of Object.entries(this.statusData.services)) {
      serviceCount++;
      if (status.status === 'running') {
        runningServices++;
      } else {
        issues.push(`服务 ${service} 未运行`);
      }
    }
    
    if (serviceCount > 0) {
      const serviceScore = (runningServices / serviceCount) * 30;
      healthScore = healthScore - 30 + serviceScore;
    }
    
    // 确定健康状态
    let healthStatus = 'healthy';
    if (healthScore < 50) {
      healthStatus = 'critical';
    } else if (healthScore < 70) {
      healthStatus = 'warning';
    }
    
    this.statusData.health = {
      status: healthStatus,
      score: Math.max(0, Math.round(healthScore)),
      issues: issues,
      lastCheck: new Date().toISOString()
    };
  }

  /**
   * 检查是否需要触发告警
   */
  checkForAlerts() {
    const newAlerts = [];
    
    // 检查内存告警
    const memUsage = this.statusData.resources.memory.usagePercent;
    const memWarning = this.statusData.resources.memory.thresholdWarning;
    const memCritical = this.statusData.resources.memory.thresholdCritical;
    
    if (memUsage >= memCritical && !this.isAlertActive('memory_critical')) {
      newAlerts.push(this.createAlert('memory_critical', 'critical', `内存使用率严重超标: ${memUsage}%`));
    } else if (memUsage >= memWarning && !this.isAlertActive('memory_warning') && memUsage < memCritical) {
      newAlerts.push(this.createAlert('memory_warning', 'warning', `内存使用率警告: ${memUsage}%`));
    } else if (memUsage < memWarning) {
      this.resolveAlert('memory_warning');
      this.resolveAlert('memory_critical');
    }
    
    // 检查磁盘告警
    const diskUsage = this.statusData.resources.disk.usagePercent;
    const diskWarning = this.statusData.resources.disk.thresholdWarning;
    const diskCritical = this.statusData.resources.disk.thresholdCritical;
    
    if (diskUsage >= diskCritical && !this.isAlertActive('disk_critical')) {
      newAlerts.push(this.createAlert('disk_critical', 'critical', `磁盘使用率严重超标: ${diskUsage}%`));
    } else if (diskUsage >= diskWarning && !this.isAlertActive('disk_warning') && diskUsage < diskCritical) {
      newAlerts.push(this.createAlert('disk_warning', 'warning', `磁盘使用率警告: ${diskUsage}%`));
    } else if (diskUsage < diskWarning) {
      this.resolveAlert('disk_warning');
      this.resolveAlert('disk_critical');
    }
    
    // 检查服务告警
    for (const [service, status] of Object.entries(this.statusData.services)) {
      if (status.status !== 'running' && !this.isAlertActive(`service_${service}_down`)) {
        newAlerts.push(this.createAlert(`service_${service}_down`, 'critical', `服务 ${service} 未运行`));
      } else if (status.status === 'running') {
        this.resolveAlert(`service_${service}_down`);
      }
    }
    
    // 添加新告警
    if (newAlerts.length > 0) {
      this.statusData.alerts = [...this.statusData.alerts, ...newAlerts];
      this.alertHistory = [...this.alertHistory, ...newAlerts];
      
      // 发送告警通知
      newAlerts.forEach(alert => {
        this.sendAlertNotification(alert);
      });
      
      // 限制告警历史记录数量
      if (this.alertHistory.length > 100) {
        this.alertHistory = this.alertHistory.slice(-100);
      }
    }
    
    // 限制当前活跃告警数量
    if (this.statusData.alerts.length > 50) {
      this.statusData.alerts = this.statusData.alerts.slice(-50);
    }
  }

  /**
   * 创建告警
   */
  createAlert(id, level, message) {
    return {
      id: id,
      level: level,
      message: message,
      timestamp: new Date().toISOString(),
      status: 'active'
    };
  }

  /**
   * 检查告警是否活跃
   */
  isAlertActive(alertId) {
    return this.statusData.alerts.some(alert => alert.id === alertId && alert.status === 'active');
  }

  /**
   * 解决告警
   */
  resolveAlert(alertId) {
    this.statusData.alerts = this.statusData.alerts.map(alert => {
      if (alert.id === alertId && alert.status === 'active') {
        return {
          ...alert,
          status: 'resolved',
          resolvedAt: new Date().toISOString()
        };
      }
      return alert;
    });
  }

  /**
   * 发送告警通知
   */
  sendAlertNotification(alert) {
    try {
      console.log(`[${alert.level.toUpperCase()}] ${alert.message} (${alert.timestamp})`);
      
      // 保存告警到日志文件
      const logDir = this.config.logConfig?.path || path.join(this.config.basePath, 'Logs');
      const alertLogFile = path.join(logDir, 'alerts.log');
      
      const logEntry = `[${alert.timestamp}] [${alert.level.toUpperCase()}] ${alert.message}\n`;
      fs.appendFileSync(alertLogFile, logEntry, 'utf8');
      
      // 这里可以添加更多的通知方式，如邮件、短信等
      if (alert.level === 'critical') {
        this.triggerCriticalAlertAction(alert);
      }
      
    } catch (error) {
      console.error('发送告警通知失败:', error.message);
    }
  }

  /**
   * 触发严重告警的响应动作
   */
  triggerCriticalAlertAction(alert) {
    // 根据不同的严重告警类型执行不同的响应动作
    if (alert.id.includes('memory')) {
      console.log('执行内存危机响应...');
      // 这里可以调用内存清理脚本
    } else if (alert.id.includes('disk')) {
      console.log('执行磁盘空间危机响应...');
      // 这里可以调用磁盘清理脚本
    } else if (alert.id.includes('service')) {
      console.log(`尝试重启停止的服务...`);
      // 这里可以尝试重启停止的服务
    }
  }

  /**
   * 处理HTTP请求
   */
  handleRequest(req, res) {
    // 设置CORS头
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    // 处理OPTIONS请求
    if (req.method === 'OPTIONS') {
      res.writeHead(200);
      res.end();
      return;
    }
    
    // 路由处理
    if (req.url === '/') {
      this.serveStatusPage(res);
    } else if (req.url === '/api/status') {
      this.serveStatusApi(res);
    } else if (req.url === '/api/health') {
      this.serveHealthApi(res);
    } else if (req.url === '/api/alerts') {
      this.serveAlertsApi(res);
    } else if (req.url === '/api/metrics') {
      this.serveMetricsApi(res);
    } else {
      this.serveNotFound(res);
    }
  }

  /**
   * 提供状态页面
   */
  serveStatusPage(res) {
    const html = this.generateStatusHtml();
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(html);
  }

  /**
   * 生成状态页面HTML
   */
  generateStatusHtml() {
    const health = this.statusData.health;
    const resources = this.statusData.resources;
    const services = this.statusData.services;
    const system = this.statusData.system;
    const alerts = this.statusData.alerts.filter(a => a.status === 'active');
    
    // 获取健康状态颜色
    const getHealthColor = (status) => {
      switch(status) {
        case 'healthy': return '#4CAF50';
        case 'warning': return '#FF9800';
        case 'critical': return '#F44336';
        default: return '#9E9E9E';
      }
    };
    
    // 获取服务状态颜色
    const getServiceStatusColor = (status) => {
      switch(status) {
        case 'running': return '#4CAF50';
        case 'stopped': return '#F44336';
        default: return '#9E9E9E';
      }
    };
    
    // 获取告警级别颜色
    const getAlertLevelColor = (level) => {
      switch(level) {
        case 'critical': return '#F44336';
        case 'warning': return '#FF9800';
        case 'info': return '#2196F3';
        default: return '#9E9E9E';
      }
    };
    
    return `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>MTSCOS AI 系统状态监控面板</title>
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        
        body {
          background-color: #f5f7fa;
          color: #333;
          line-height: 1.6;
        }
        
        .container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 20px;
        }
        
        header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 30px;
          border-radius: 15px;
          margin-bottom: 30px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        header h1 {
          font-size: 2.5rem;
          margin-bottom: 10px;
          font-weight: 700;
        }
        
        header p {
          font-size: 1.1rem;
          opacity: 0.9;
        }
        
        .status-overview {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }
        
        .status-card {
          background: white;
          padding: 25px;
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .status-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .status-card h3 {
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: #666;
          margin-bottom: 15px;
          font-weight: 600;
        }
        
        .status-card .value {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 8px;
        }
        
        .status-card .label {
          font-size: 0.9rem;
          color: #888;
        }
        
        .system-info {
          background: white;
          padding: 30px;
          border-radius: 12px;
          margin-bottom: 30px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        .system-info h2 {
          font-size: 1.5rem;
          margin-bottom: 20px;
          color: #444;
          font-weight: 600;
        }
        
        .system-info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 15px;
        }
        
        .info-item {
          padding: 12px 0;
          border-bottom: 1px solid #f0f0f0;
        }
        
        .info-item:last-child {
          border-bottom: none;
        }
        
        .info-label {
          font-size: 0.9rem;
          color: #666;
          margin-bottom: 4px;
        }
        
        .info-value {
          font-size: 1.1rem;
          font-weight: 500;
          color: #333;
        }
        
        .resources-section {
          margin-bottom: 30px;
        }
        
        .section-title {
          font-size: 1.5rem;
          margin-bottom: 20px;
          color: #444;
          font-weight: 600;
        }
        
        .resources-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
        }
        
        .resource-card {
          background: white;
          padding: 25px;
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        .resource-card h3 {
          font-size: 1.2rem;
          margin-bottom: 20px;
          color: #444;
          font-weight: 600;
        }
        
        .usage-bar {
          width: 100%;
          height: 25px;
          background-color: #e9ecef;
          border-radius: 12.5px;
          overflow: hidden;
          margin-bottom: 10px;
          position: relative;
        }
        
        .usage-fill {
          height: 100%;
          border-radius: 12.5px;
          transition: width 1s ease, background-color 0.5s ease;
          background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .usage-text {
          display: flex;
          justify-content: space-between;
          font-size: 0.9rem;
          color: #666;
        }
        
        .services-section {
          margin-bottom: 30px;
        }
        
        .services-table {
          width: 100%;
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        .services-table table {
          width: 100%;
          border-collapse: collapse;
        }
        
        .services-table th,
        .services-table td {
          padding: 15px 20px;
          text-align: left;
          border-bottom: 1px solid #f0f0f0;
        }
        
        .services-table th {
          background-color: #f8f9fa;
          font-weight: 600;
          color: #444;
          font-size: 0.95rem;
        }
        
        .services-table tr:last-child td {
          border-bottom: none;
        }
        
        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 0.85rem;
          font-weight: 600;
        }
        
        .alerts-section {
          margin-bottom: 30px;
        }
        
        .alerts-list {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
          max-height: 400px;
          overflow-y: auto;
        }
        
        .alert-item {
          padding: 20px;
          border-bottom: 1px solid #f0f0f0;
          transition: background-color 0.2s ease;
        }
        
        .alert-item:hover {
          background-color: #f8f9fa;
        }
        
        .alert-item:last-child {
          border-bottom: none;
        }
        
        .alert-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .alert-level {
          font-size: 0.9rem;
          font-weight: 600;
          padding: 2px 8px;
          border-radius: 4px;
        }
        
        .alert-time {
          font-size: 0.85rem;
          color: #888;
        }
        
        .alert-message {
          font-size: 1rem;
          color: #333;
        }
        
        .no-alerts {
          padding: 40px 20px;
          text-align: center;
          color: #888;
        }
        
        footer {
          text-align: center;
          padding: 20px;
          color: #888;
          font-size: 0.9rem;
        }
        
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.7; }
          100% { opacity: 1; }
        }
        
        .pulse {
          animation: pulse 2s infinite;
        }
        
        @media (max-width: 768px) {
          .container {
            padding: 15px;
          }
          
          header {
            padding: 20px;
          }
          
          header h1 {
            font-size: 2rem;
          }
          
          .status-overview,
          .resources-grid {
            grid-template-columns: 1fr;
          }
          
          .services-table th,
          .services-table td {
            padding: 12px 15px;
            font-size: 0.9rem;
          }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <h1>MTSCOS AI 系统状态监控面板</h1>
          <p>实时监控系统健康状态、资源使用和服务运行情况</p>
        </header>
        
        <div class="status-overview">
          <div class="status-card">
            <h3>系统健康状态</h3>
            <div class="value" style="color: ${getHealthColor(health.status)}">${health.status === 'healthy' ? '健康' : health.status === 'warning' ? '警告' : '严重'}</div>
            <div class="label">健康得分: ${health.score}/100</div>
          </div>
          
          <div class="status-card">
            <h3>内存使用率</h3>
            <div class="value">${resources.memory.usagePercent}%</div>
            <div class="label">可用: ${resources.memory.free}</div>
          </div>
          
          <div class="status-card">
            <h3>磁盘使用率</h3>
            <div class="value">${resources.disk.usagePercent}%</div>
            <div class="label">可用: ${resources.disk.free}</div>
          </div>
          
          <div class="status-card">
            <h3>活跃告警</h3>
            <div class="value ${alerts.length > 0 ? 'pulse' : ''}" style="color: ${alerts.length > 0 ? '#F44336' : '#4CAF50'}">${alerts.length}</div>
            <div class="label">最近检查: 刚刚</div>
          </div>
        </div>
        
        <div class="system-info">
          <h2>系统信息</h2>
          <div class="system-info-grid">
            <div class="info-item">
              <div class="info-label">主机名</div>
              <div class="info-value">${system.hostname}</div>
            </div>
            <div class="info-item">
              <div class="info-label">操作系统</div>
              <div class="info-value">${system.platform} ${system.release}</div>
            </div>
            <div class="info-item">
              <div class="info-label">架构</div>
              <div class="info-value">${system.arch}</div>
            </div>
            <div class="info-item">
              <div class="info-label">CPU核心数</div>
              <div class="info-value">${resources.cpu.cores}</div>
            </div>
            <div class="info-item">
              <div class="info-label">CPU型号</div>
              <div class="info-value">${resources.cpu.model}</div>
            </div>
            <div class="info-item">
              <div class="info-label">运行时间</div>
              <div class="info-value">${this.formatUptime(system.uptime)}</div>
            </div>
            <div class="info-item">
              <div class="info-label">总内存</div>
              <div class="info-value">${resources.memory.total}</div>
            </div>
            <div class="info-item">
              <div class="info-label">磁盘总量</div>
              <div class="info-value">${resources.disk.total}</div>
            </div>
          </div>
        </div>
        
        <div class="resources-section">
          <h2 class="section-title">资源使用情况</h2>
          <div class="resources-grid">
            <div class="resource-card">
              <h3>内存使用</h3>
              <div class="usage-bar">
                <div class="usage-fill" style="width: ${Math.min(resources.memory.usagePercent, 100)}%; background-color: ${resources.memory.usagePercent > resources.memory.thresholdCritical ? '#F44336' : resources.memory.usagePercent > resources.memory.thresholdWarning ? '#FF9800' : '#4CAF50'}"></div>
              </div>
              <div class="usage-text">
                <span>已使用: ${resources.memory.used}</span>
                <span>${resources.memory.usagePercent}%</span>
              </div>
            </div>
            
            <div class="resource-card">
              <h3>磁盘使用</h3>
              <div class="usage-bar">
                <div class="usage-fill" style="width: ${Math.min(resources.disk.usagePercent, 100)}%; background-color: ${resources.disk.usagePercent > resources.disk.thresholdCritical ? '#F44336' : resources.disk.usagePercent > resources.disk.thresholdWarning ? '#FF9800' : '#4CAF50'}"></div>
              </div>
              <div class="usage-text">
                <span>已使用: ${resources.disk.used}</span>
                <span>${resources.disk.usagePercent}%</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="services-section">
          <h2 class="section-title">服务状态</h2>
          <div class="services-table">
            <table>
              <thead>
                <tr>
                  <th>服务名称</th>
                  <th>状态</th>
                  <th>PID</th>
                  <th>最后检查</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>环境监控服务</td>
                  <td><span class="status-badge" style="background-color: ${getServiceStatusColor(services.monitor.status)}; color: white">${services.monitor.status === 'running' ? '运行中' : services.monitor.status === 'stopped' ? '已停止' : '未知'}</span></td>
                  <td>${services.monitor.pid || '-'}</td>
                  <td>${this.formatTimeAgo(new Date(services.monitor.lastCheck))}</td>
                </tr>
                <tr>
                  <td>自动检测与修复引擎</td>
                  <td><span class="status-badge" style="background-color: ${getServiceStatusColor(services.detection.status)}; color: white">${services.detection.status === 'running' ? '运行中' : services.detection.status === 'stopped' ? '已停止' : '未知'}</span></td>
                  <td>${services.detection.pid || '-'}</td>
                  <td>${this.formatTimeAgo(new Date(services.detection.lastCheck))}</td>
                </tr>
                <tr>
                  <td>环境维护服务</td>
                  <td><span class="status-badge" style="background-color: ${getServiceStatusColor(services.maintenance.status)}; color: white">${services.maintenance.status === 'running' ? '运行中' : services.maintenance.status === 'stopped' ? '已停止' : '未知'}</span></td>
                  <td>${services.maintenance.pid || '-'}</td>
                  <td>${this.formatTimeAgo(new Date(services.maintenance.lastCheck))}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <div class="alerts-section">
          <h2 class="section-title">活跃告警</h2>
          <div class="alerts-list">
            ${alerts.length > 0 ? alerts.map(alert => `
              <div class="alert-item">
                <div class="alert-header">
                  <span class="alert-level" style="background-color: ${getAlertLevelColor(alert.level)}; color: white">${alert.level === 'critical' ? '严重' : alert.level === 'warning' ? '警告' : '信息'}</span>
                  <span class="alert-time">${this.formatTimeAgo(new Date(alert.timestamp))}</span>
                </div>
                <div class="alert-message">${alert.message}</div>
              </div>
            `).join('') : `
              <div class="no-alerts">
                <p>暂无活跃告警</p>
              </div>
            `}
          </div>
        </div>
        
        <footer>
          <p>© ${new Date().getFullYear()} MTSCOS AI 系统 - 系统状态监控面板</p>
        </footer>
      </div>
      
      <script>
        // 每30秒自动刷新页面
        setInterval(() => {
          location.reload();
        }, 30000);
        
        // 实时更新资源使用进度条动画
        document.addEventListener('DOMContentLoaded', () => {
          const fillElements = document.querySelectorAll('.usage-fill');
          fillElements.forEach(el => {
            const targetWidth = el.style.width;
            el.style.width = '0%';
            setTimeout(() => {
              el.style.width = targetWidth;
            }, 100);
          });
        });
      </script>
    </body>
    </html>
    `;
  }

  /**
   * 格式化运行时间
   */
  formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    let result = '';
    if (days > 0) result += `${days} 天 `;
    if (hours > 0) result += `${hours} 小时 `;
    if (minutes > 0) result += `${minutes} 分钟`;
    
    return result || '刚刚启动';
  }

  /**
   * 格式化时间为相对时间
   */
  formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return '刚刚';
    if (diffMins < 60) return `${diffMins} 分钟前`;
    if (diffHours < 24) return `${diffHours} 小时前`;
    if (diffDays < 30) return `${diffDays} 天前`;
    
    return date.toLocaleDateString();
  }

  /**
   * 提供状态API
   */
  serveStatusApi(res) {
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(this.statusData, null, 2));
  }

  /**
   * 提供健康API
   */
  serveHealthApi(res) {
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(this.statusData.health, null, 2));
  }

  /**
   * 提供告警API
   */
  serveAlertsApi(res) {
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({
      current: this.statusData.alerts.filter(a => a.status === 'active'),
      history: this.alertHistory.slice(-50)
    }, null, 2));
  }

  /**
   * 提供指标API
   */
  serveMetricsApi(res) {
    const metrics = {
      cpu: this.statusData.resources.cpu,
      memory: this.statusData.resources.memory,
      disk: this.statusData.resources.disk,
      services: this.statusData.services
    };
    
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(metrics, null, 2));
  }

  /**
   * 提供404页面
   */
  serveNotFound(res) {
    res.writeHead(404, {'Content-Type': 'text/plain'});
    res.end('Not Found');
  }

  /**
   * 停止状态监控面板
   */
  stop() {
    if (!this.isRunning) {
      console.log('系统状态监控面板未在运行');
      return;
    }

    this.isRunning = false;
    
    // 清除监控定时器
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }
    
    // 停止服务器
    if (this.server) {
      this.server.close(() => {
        console.log('系统状态监控面板已停止');
      });
    }
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  try {
    const statusPanel = new SystemStatusPanel(configPath);
    statusPanel.start();
    
    // 处理信号
    process.on('SIGINT', () => {
      console.log('收到终止信号，正在停止系统状态监控面板...');
      statusPanel.stop();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('启动系统状态监控面板失败:', error.message);
    process.exit(1);
  }
}

module.exports = SystemStatusPanel;
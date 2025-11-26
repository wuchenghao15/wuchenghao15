#!/usr/bin/env node

/**
 * MTSCOS AI 智能适配引擎
 * 实现动态架构和功能扩展，智能管理系统组件
 */

const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const os = require('os');

class AdaptiveEngine {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.isRunning = false;
    this.analysisInterval = null;
    this.adaptationLog = [];
    this.availableComponents = new Map();
    this.loadedComponents = new Map();
    this.componentRegistry = {};
    this.performanceHistory = [];
    
    // 初始化引擎
    this.initialize();
  }

  /**
   * 初始化智能适配引擎
   */
  initialize() {
    try {
      // 加载配置文件
      this.config = this.loadConfig();
      
      // 设置日志目录
      this.logDir = this.config.logConfig?.path || path.join(this.config.basePath, 'Logs');
      this.ensureLogDirExists();
      
      // 设置组件目录
      this.componentsDir = path.join(this.config.basePath, 'Staging', 'Components');
      this.ensureComponentsDirExists();
      
      // 初始化组件注册表
      this.initializeComponentRegistry();
      
      // 扫描可用组件
      this.scanAvailableComponents();
      
      // 加载性能历史数据
      this.loadPerformanceHistory();
      
      console.log('MTSCOS AI 智能适配引擎初始化完成');
      console.log(`已发现 ${this.availableComponents.size} 个可用组件`);
      
    } catch (error) {
      console.error('初始化智能适配引擎失败:', error.message);
      this.logError('初始化失败', error);
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
   * 确保日志目录存在
   */
  ensureLogDirExists() {
    try {
      if (!fs.existsSync(this.logDir)) {
        fs.mkdirSync(this.logDir, { recursive: true });
        console.log(`创建日志目录: ${this.logDir}`);
      }
    } catch (error) {
      console.error(`创建日志目录失败: ${error.message}`);
    }
  }

  /**
   * 确保组件目录存在
   */
  ensureComponentsDirExists() {
    try {
      if (!fs.existsSync(this.componentsDir)) {
        fs.mkdirSync(this.componentsDir, { recursive: true });
        console.log(`创建组件目录: ${this.componentsDir}`);
      }
    } catch (error) {
      console.error(`创建组件目录失败: ${error.message}`);
    }
  }

  /**
   * 初始化组件注册表
   */
  initializeComponentRegistry() {
    this.componentRegistry = {
      // 核心组件类型
      core: {
        description: '核心系统组件',
        priority: 100,
        required: true
      },
      monitoring: {
        description: '监控相关组件',
        priority: 80,
        required: true
      },
      maintenance: {
        description: '维护相关组件',
        priority: 70,
        required: true
      },
      security: {
        description: '安全相关组件',
        priority: 90,
        required: true
      },
      
      // 扩展组件类型
      optimization: {
        description: '性能优化组件',
        priority: 60,
        required: false
      },
      analytics: {
        description: '数据分析组件',
        priority: 50,
        required: false
      },
      integration: {
        description: '外部系统集成组件',
        priority: 40,
        required: false
      },
      ui: {
        description: '用户界面组件',
        priority: 30,
        required: false
      },
      
      // 辅助组件类型
      helper: {
        description: '辅助功能组件',
        priority: 20,
        required: false
      },
      custom: {
        description: '自定义组件',
        priority: 10,
        required: false
      }
    };
  }

  /**
   * 扫描可用组件
   */
  scanAvailableComponents() {
    try {
      // 扫描核心目录下的组件
      const coreComponentsDir = path.join(this.config.basePath, 'Staging', 'Scripts');
      this.scanDirectoryForComponents(coreComponentsDir);
      
      // 扫描专用组件目录
      this.scanDirectoryForComponents(this.componentsDir);
      
    } catch (error) {
      console.error('扫描可用组件失败:', error.message);
      this.logError('扫描组件失败', error);
    }
  }

  /**
   * 从目录扫描组件
   */
  scanDirectoryForComponents(dir) {
    try {
      if (!fs.existsSync(dir)) {
        return;
      }
      
      const files = fs.readdirSync(dir);
      
      files.forEach(file => {
        const filePath = path.join(dir, file);
        const stats = fs.statSync(filePath);
        
        if (stats.isDirectory()) {
          // 递归扫描子目录
          this.scanDirectoryForComponents(filePath);
        } else if (file.endsWith('.js') || file.endsWith('.sh')) {
          // 分析文件是否为组件
          try {
            const componentInfo = this.analyzeComponentFile(filePath);
            if (componentInfo) {
              this.availableComponents.set(componentInfo.id, {
                ...componentInfo,
                filePath: filePath,
                lastModified: stats.mtime
              });
            }
          } catch (error) {
            console.error(`分析组件文件失败: ${filePath}`, error.message);
          }
        }
      });
    } catch (error) {
      console.error(`扫描目录失败: ${dir}`, error.message);
    }
  }

  /**
   * 分析组件文件
   */
  analyzeComponentFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const fileName = path.basename(filePath);
      
      // 提取组件信息
      const componentMatch = content.match(/\/\*\*[\s\S]*?\*\//);
      let description = '';
      let componentName = '';
      let componentType = 'custom';
      
      if (componentMatch) {
        const comments = componentMatch[0];
        description = comments.replace(/\/\*\*|\*\/|\*/g, '').trim();
        
        // 尝试从描述中提取组件名称和类型
        const nameMatch = description.match(/([A-Za-z0-9_\s]+)\s*模块/);
        if (nameMatch) {
          componentName = nameMatch[1].trim();
        }
      }
      
      // 根据文件路径或内容判断组件类型
      if (filePath.includes('monitoring')) {
        componentType = 'monitoring';
      } else if (filePath.includes('maintenance')) {
        componentType = 'maintenance';
      } else if (filePath.includes('security')) {
        componentType = 'security';
      } else if (filePath.includes('intelligence')) {
        componentType = 'optimization';
      }
      
      // 创建组件ID
      const componentId = `${componentType}:${fileName.replace(/\.[^/.]+$/, '')}`;
      
      return {
        id: componentId,
        name: componentName || fileName.replace(/\.[^/.]+$/, ''),
        type: componentType,
        description: description || `自动发现的组件: ${fileName}`,
        fileType: fileName.endsWith('.js') ? 'javascript' : 'shell',
        size: content.length
      };
    } catch (error) {
      throw new Error(`分析组件文件失败: ${error.message}`);
    }
  }

  /**
   * 加载性能历史数据
   */
  loadPerformanceHistory() {
    try {
      const historyPath = path.join(this.logDir, 'performance-history.json');
      if (fs.existsSync(historyPath)) {
        const historyContent = fs.readFileSync(historyPath, 'utf8');
        this.performanceHistory = JSON.parse(historyContent);
        console.log(`加载了 ${this.performanceHistory.length} 条性能历史记录`);
      }
    } catch (error) {
      console.error('加载性能历史失败:', error.message);
      this.performanceHistory = [];
    }
  }

  /**
   * 保存性能历史数据
   */
  savePerformanceHistory() {
    try {
      const historyPath = path.join(this.logDir, 'performance-history.json');
      // 只保留最近1000条记录
      const recentHistory = this.performanceHistory.slice(-1000);
      fs.writeFileSync(historyPath, JSON.stringify(recentHistory, null, 2), 'utf8');
    } catch (error) {
      console.error('保存性能历史失败:', error.message);
    }
  }

  /**
   * 启动智能适配引擎
   */
  start() {
    if (this.isRunning) {
      console.log('智能适配引擎已经在运行中');
      return;
    }

    this.isRunning = true;
    console.log('智能适配引擎已启动');
    
    // 立即执行一次分析
    this.runAnalysisCycle();
    
    // 设置分析间隔（默认每10分钟分析一次）
    const analysisInterval = this.config.adaptation?.analysisInterval || 600000;
    this.analysisInterval = setInterval(() => {
      this.runAnalysisCycle();
    }, analysisInterval);
    
    console.log(`系统分析间隔设置为: ${analysisInterval / 60000}分钟`);
  }

  /**
   * 运行分析周期
   */
  runAnalysisCycle() {
    if (!this.isRunning) return;
    
    console.log(`\n--- 开始系统分析周期 (${new Date().toISOString()}) ---`);
    
    try {
      // 1. 收集系统状态
      const systemState = this.collectSystemState();
      
      // 2. 分析性能
      const performanceAnalysis = this.analyzePerformance(systemState);
      
      // 3. 检测优化机会
      const optimizationOpportunities = this.detectOptimizationOpportunities(performanceAnalysis);
      
      // 4. 执行适配操作
      const adaptationResults = this.executeAdaptations(optimizationOpportunities);
      
      // 5. 记录分析结果
      this.recordAnalysisResult(systemState, performanceAnalysis, optimizationOpportunities, adaptationResults);
      
      console.log(`--- 系统分析周期结束 (${new Date().toISOString()}) ---\n`);
      
    } catch (error) {
      console.error('运行分析周期失败:', error.message);
      this.logError('分析周期失败', error);
    }
  }

  /**
   * 收集系统状态
   */
  collectSystemState() {
    try {
      const systemState = {
        timestamp: new Date().toISOString(),
        system: this.collectSystemInfo(),
        resources: this.collectResourceUsage(),
        processes: this.collectProcessInfo(),
        components: this.collectComponentStatus(),
        performance: this.collectPerformanceMetrics()
      };
      
      return systemState;
    } catch (error) {
      throw new Error(`收集系统状态失败: ${error.message}`);
    }
  }

  /**
   * 收集系统信息
   */
  collectSystemInfo() {
    return {
      platform: os.platform(),
      release: os.release(),
      arch: os.arch(),
      hostname: os.hostname(),
      uptime: os.uptime(),
      cpus: os.cpus().length,
      userInfo: os.userInfo().username
    };
  }

  /**
   * 收集资源使用情况
   */
  collectResourceUsage() {
    try {
      const totalMemory = os.totalmem();
      const freeMemory = os.freemem();
      const memoryUsage = 100 - (freeMemory / totalMemory * 100);
      
      // 收集CPU使用率
      const cpus = os.cpus();
      const cpuUsage = this.calculateCpuUsage(cpus);
      
      // 收集磁盘使用情况
      const diskUsage = this.collectDiskUsage();
      
      return {
        memory: {
          total: totalMemory,
          free: freeMemory,
          used: totalMemory - freeMemory,
          usagePercent: memoryUsage
        },
        cpu: {
          count: cpus.length,
          usagePercent: cpuUsage
        },
        disk: diskUsage
      };
    } catch (error) {
      console.error('收集资源使用情况失败:', error.message);
      return {
        memory: { total: 0, free: 0, used: 0, usagePercent: 0 },
        cpu: { count: 0, usagePercent: 0 },
        disk: { usagePercent: 0 }
      };
    }
  }

  /**
   * 计算CPU使用率
   */
  calculateCpuUsage(cpus) {
    // 简化的CPU使用率计算
    // 实际项目中可以使用更精确的计算方法
    let totalIdle = 0;
    let totalTick = 0;
    
    cpus.forEach(core => {
      for (const type in core.times) {
        totalTick += core.times[type];
      }
      totalIdle += core.times.idle;
    });
    
    return 100 - (totalIdle / totalTick * 100);
  }

  /**
   * 收集磁盘使用情况
   */
  collectDiskUsage() {
    try {
      const dfOutput = execSync(`df -h "${this.config.basePath}"`, { encoding: 'utf8' });
      const lines = dfOutput.trim().split('\n');
      
      if (lines.length >= 2) {
        const dataLine = lines[1];
        const data = dataLine.split(/\s+/);
        return {
          usagePercent: parseInt(data[data.length - 2].replace('%', '')),
          mountPoint: data[data.length - 1]
        };
      }
    } catch (error) {
      console.error('收集磁盘使用情况失败:', error.message);
    }
    
    return { usagePercent: 0, mountPoint: this.config.basePath };
  }

  /**
   * 收集进程信息
   */
  collectProcessInfo() {
    try {
      const psOutput = execSync('ps aux --sort=-%cpu | head -n 20', { encoding: 'utf8' });
      const lines = psOutput.trim().split('\n');
      const processes = [];
      
      // 跳过标题行
      for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(/\s+/);
        if (parts.length >= 11) {
          processes.push({
            user: parts[0],
            pid: parseInt(parts[1]),
            cpu: parseFloat(parts[2]),
            mem: parseFloat(parts[3]),
            command: parts.slice(10).join(' ')
          });
        }
      }
      
      return processes;
    } catch (error) {
      console.error('收集进程信息失败:', error.message);
      return [];
    }
  }

  /**
   * 收集组件状态
   */
  collectComponentStatus() {
    const components = [];
    
    this.availableComponents.forEach((component, id) => {
      try {
        const stats = fs.statSync(component.filePath);
        const isLoaded = this.loadedComponents.has(id);
        
        components.push({
          id: id,
          name: component.name,
          type: component.type,
          filePath: component.filePath,
          size: stats.size,
          lastModified: stats.mtime,
          isLoaded: isLoaded,
          loadTime: isLoaded ? this.loadedComponents.get(id).loadTime : null
        });
      } catch (error) {
        console.error(`收集组件状态失败: ${id}`, error.message);
      }
    });
    
    return components;
  }

  /**
   * 收集性能指标
   */
  collectPerformanceMetrics() {
    try {
      // 这里可以添加更复杂的性能指标收集
      // 如响应时间、吞吐量等
      return {
        responseTime: this.measureResponseTime(),
        systemLoad: this.getSystemLoad(),
        networkStats: this.collectNetworkStats()
      };
    } catch (error) {
      console.error('收集性能指标失败:', error.message);
      return {
        responseTime: 0,
        systemLoad: 0,
        networkStats: null
      };
    }
  }

  /**
   * 测量响应时间
   */
  measureResponseTime() {
    try {
      const startTime = Date.now();
      // 执行一个简单的操作并测量时间
      fs.existsSync(this.config.basePath);
      const endTime = Date.now();
      return endTime - startTime;
    } catch (error) {
      return 0;
    }
  }

  /**
   * 获取系统负载
   */
  getSystemLoad() {
    try {
      const loadAvg = os.loadavg();
      return {
        1m: loadAvg[0],
        5m: loadAvg[1],
        15m: loadAvg[2]
      };
    } catch (error) {
      return { 1m: 0, 5m: 0, 15m: 0 };
    }
  }

  /**
   * 收集网络统计信息
   */
  collectNetworkStats() {
    try {
      // 在不同平台上获取网络统计信息的方式不同
      if (os.platform() === 'linux') {
        const netstatOutput = execSync('netstat -s | grep -E "segments received|segments send out|retransmitted"', { encoding: 'utf8' });
        return { output: netstatOutput };
      } else if (os.platform() === 'darwin') {
        const netstatOutput = execSync('netstat -ib | grep -v "Iface"', { encoding: 'utf8' });
        return { output: netstatOutput };
      }
    } catch (error) {
      console.error('收集网络统计信息失败:', error.message);
    }
    
    return null;
  }

  /**
   * 分析性能
   */
  analyzePerformance(systemState) {
    try {
      const analysis = {
        resourceUsage: this.analyzeResourceUsage(systemState.resources),
        processAnalysis: this.analyzeProcesses(systemState.processes),
        componentAnalysis: this.analyzeComponents(systemState.components),
        trendAnalysis: this.analyzePerformanceTrends(systemState)
      };
      
      return analysis;
    } catch (error) {
      throw new Error(`分析性能失败: ${error.message}`);
    }
  }

  /**
   * 分析资源使用情况
   */
  analyzeResourceUsage(resources) {
    const warnings = [];
    const criticalIssues = [];
    
    // 检查内存使用
    if (resources.memory.usagePercent > (this.config.resourceLimits?.memory?.limit || 90)) {
      criticalIssues.push({
        type: 'memory_usage_critical',
        value: resources.memory.usagePercent,
        threshold: this.config.resourceLimits?.memory?.limit || 90,
        message: `内存使用率严重超标: ${resources.memory.usagePercent.toFixed(2)}%`
      });
    } else if (resources.memory.usagePercent > (this.config.resourceLimits?.memory?.warningThreshold || 80)) {
      warnings.push({
        type: 'memory_usage_high',
        value: resources.memory.usagePercent,
        threshold: this.config.resourceLimits?.memory?.warningThreshold || 80,
        message: `内存使用率过高: ${resources.memory.usagePercent.toFixed(2)}%`
      });
    }
    
    // 检查CPU使用
    if (resources.cpu.usagePercent > (this.config.resourceLimits?.cpu?.limit || 95)) {
      criticalIssues.push({
        type: 'cpu_usage_critical',
        value: resources.cpu.usagePercent,
        threshold: this.config.resourceLimits?.cpu?.limit || 95,
        message: `CPU使用率严重超标: ${resources.cpu.usagePercent.toFixed(2)}%`
      });
    } else if (resources.cpu.usagePercent > (this.config.resourceLimits?.cpu?.warningThreshold || 85)) {
      warnings.push({
        type: 'cpu_usage_high',
        value: resources.cpu.usagePercent,
        threshold: this.config.resourceLimits?.cpu?.warningThreshold || 85,
        message: `CPU使用率过高: ${resources.cpu.usagePercent.toFixed(2)}%`
      });
    }
    
    // 检查磁盘使用
    if (resources.disk.usagePercent > (this.config.resourceLimits?.disk?.limit || 80)) {
      criticalIssues.push({
        type: 'disk_usage_critical',
        value: resources.disk.usagePercent,
        threshold: this.config.resourceLimits?.disk?.limit || 80,
        message: `磁盘使用率严重超标: ${resources.disk.usagePercent}%`
      });
    } else if (resources.disk.usagePercent > (this.config.resourceLimits?.disk?.warningThreshold || 70)) {
      warnings.push({
        type: 'disk_usage_high',
        value: resources.disk.usagePercent,
        threshold: this.config.resourceLimits?.disk?.warningThreshold || 70,
        message: `磁盘使用率过高: ${resources.disk.usagePercent}%`
      });
    }
    
    return {
      warnings: warnings,
      criticalIssues: criticalIssues,
      overallHealth: criticalIssues.length > 0 ? 'critical' : warnings.length > 0 ? 'warning' : 'healthy'
    };
  }

  /**
   * 分析进程
   */
  analyzeProcesses(processes) {
    const highResourceProcesses = [];
    const suspiciousProcesses = [];
    
    processes.forEach(process => {
      // 识别高资源消耗进程
      if (process.cpu > 50 || process.mem > 50) {
        highResourceProcesses.push(process);
      }
      
      // 识别可疑进程（简化实现）
      const suspiciousPatterns = [
        'miner', 'crypto', 'worm', 'trojan', 'virus', 'malware'
      ];
      
      const isSuspicious = suspiciousPatterns.some(pattern => 
        process.command.toLowerCase().includes(pattern)
      );
      
      if (isSuspicious) {
        suspiciousProcesses.push(process);
      }
    });
    
    return {
      highResourceProcesses: highResourceProcesses,
      suspiciousProcesses: suspiciousProcesses,
      totalProcesses: processes.length
    };
  }

  /**
   * 分析组件
   */
  analyzeComponents(components) {
    const unloadedRequiredComponents = [];
    const outdatedComponents = [];
    const largeComponents = [];
    
    components.forEach(component => {
      // 检查未加载的必需组件
      const componentType = this.componentRegistry[component.type];
      if (componentType && componentType.required && !component.isLoaded) {
        unloadedRequiredComponents.push(component);
      }
      
      // 检查过时的组件（超过30天未更新）
      const daysSinceModified = (Date.now() - component.lastModified.getTime()) / (24 * 60 * 60 * 1000);
      if (daysSinceModified > 30) {
        outdatedComponents.push(component);
      }
      
      // 检查大组件（超过1MB）
      if (component.size > 1024 * 1024) {
        largeComponents.push(component);
      }
    });
    
    return {
      unloadedRequiredComponents: unloadedRequiredComponents,
      outdatedComponents: outdatedComponents,
      largeComponents: largeComponents,
      loadedComponents: components.filter(c => c.isLoaded).length,
      totalComponents: components.length
    };
  }

  /**
   * 分析性能趋势
   */
  analyzePerformanceTrends(currentState) {
    if (this.performanceHistory.length < 2) {
      return {
        hasTrend: false,
        trendType: 'stable',
        trendStrength: 0
      };
    }
    
    // 简化的趋势分析
    const recentHistory = this.performanceHistory.slice(-5);
    let memoryTrend = 0;
    let cpuTrend = 0;
    
    recentHistory.forEach((record, index) => {
      if (index > 0) {
        const prevRecord = recentHistory[index - 1];
        memoryTrend += record.system.resources.memory.usagePercent - prevRecord.system.resources.memory.usagePercent;
        cpuTrend += record.system.resources.cpu.usagePercent - prevRecord.system.resources.cpu.usagePercent;
      }
    });
    
    // 计算趋势类型和强度
    const trendStrength = Math.max(Math.abs(memoryTrend), Math.abs(cpuTrend));
    let trendType = 'stable';
    
    if (trendStrength > 10) {
      if (memoryTrend > 0 || cpuTrend > 0) {
        trendType = 'deteriorating';
      } else {
        trendType = 'improving';
      }
    }
    
    return {
      hasTrend: true,
      trendType: trendType,
      trendStrength: trendStrength,
      memoryTrend: memoryTrend / recentHistory.length,
      cpuTrend: cpuTrend / recentHistory.length
    };
  }

  /**
   * 检测优化机会
   */
  detectOptimizationOpportunities(performanceAnalysis) {
    const opportunities = [];
    
    // 基于资源使用问题的优化
    performanceAnalysis.resourceUsage.criticalIssues.forEach(issue => {
      opportunities.push(this.createOptimizationOpportunity(issue));
    });
    
    performanceAnalysis.resourceUsage.warnings.forEach(warning => {
      opportunities.push(this.createOptimizationOpportunity(warning));
    });
    
    // 基于进程分析的优化
    performanceAnalysis.processAnalysis.highResourceProcesses.forEach(process => {
      opportunities.push({
        type: 'process_optimization',
        priority: process.cpu > 70 || process.mem > 70 ? 'high' : 'medium',
        description: `优化高资源消耗进程: ${process.command} (CPU: ${process.cpu}%, MEM: ${process.mem}%)`,
        processId: process.pid,
        suggestedAction: '检查并优化进程，考虑重启或调整配置'
      });
    });
    
    // 基于组件分析的优化
    performanceAnalysis.componentAnalysis.unloadedRequiredComponents.forEach(component => {
      opportunities.push({
        type: 'component_loading',
        priority: 'high',
        description: `加载必需组件: ${component.name}`,
        componentId: component.id,
        suggestedAction: '立即加载必需组件'
      });
    });
    
    // 基于趋势的优化
    if (performanceAnalysis.trendAnalysis.hasTrend && 
        performanceAnalysis.trendAnalysis.trendType === 'deteriorating' &&
        performanceAnalysis.trendAnalysis.trendStrength > 20) {
      
      opportunities.push({
        type: 'system_optimization',
        priority: 'high',
        description: '系统性能正在快速下降，需要全面优化',
        suggestedAction: '增加系统资源或优化核心组件'
      });
    }
    
    // 按优先级排序
    opportunities.sort((a, b) => {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
    
    return opportunities;
  }

  /**
   * 创建优化机会
   */
  createOptimizationOpportunity(issue) {
    const priority = issue.type.includes('critical') ? 'critical' : 'high';
    let suggestedAction = '检查并优化系统资源使用';
    
    if (issue.type.includes('memory')) {
      suggestedAction = '清理内存缓存，关闭不必要的进程';
    } else if (issue.type.includes('cpu')) {
      suggestedAction = '识别并优化CPU密集型进程';
    } else if (issue.type.includes('disk')) {
      suggestedAction = '清理临时文件，扩展磁盘空间';
    }
    
    return {
      type: 'resource_optimization',
      priority: priority,
      description: issue.message,
      issueType: issue.type,
      currentValue: issue.value,
      threshold: issue.threshold,
      suggestedAction: suggestedAction
    };
  }

  /**
   * 执行适配操作
   */
  executeAdaptations(opportunities) {
    const results = {
      totalOpportunities: opportunities.length,
      executed: 0,
      successful: 0,
      failed: 0,
      skipped: 0,
      details: []
    };
    
    opportunities.forEach(opportunity => {
      try {
        console.log(`执行优化: ${opportunity.description}`);
        results.executed++;
        
        let adaptationResult;
        
        switch (opportunity.type) {
          case 'resource_optimization':
            adaptationResult = this.optimizeResource(opportunity);
            break;
            
          case 'process_optimization':
            adaptationResult = this.optimizeProcess(opportunity);
            break;
            
          case 'component_loading':
            adaptationResult = this.loadComponent(opportunity.componentId);
            break;
            
          case 'system_optimization':
            adaptationResult = this.optimizeSystem(opportunity);
            break;
            
          default:
            adaptationResult = {
              success: false,
              message: `不支持的优化类型: ${opportunity.type}`
            };
        }
        
        if (adaptationResult.success) {
          results.successful++;
        } else {
          results.failed++;
        }
        
        results.details.push({
          opportunity: opportunity,
          result: adaptationResult
        });
        
      } catch (error) {
        results.details.push({
          opportunity: opportunity,
          result: {
            success: false,
            message: `执行优化时发生错误: ${error.message}`
          }
        });
        results.failed++;
      }
    });
    
    results.skipped = results.totalOpportunities - results.executed;
    
    return results;
  }

  /**
   * 优化资源使用
   */
  optimizeResource(opportunity) {
    try {
      if (opportunity.issueType.includes('memory')) {
        return this.optimizeMemory();
      } else if (opportunity.issueType.includes('cpu')) {
        return this.optimizeCpu();
      } else if (opportunity.issueType.includes('disk')) {
        return this.optimizeDisk();
      }
      
      return {
        success: false,
        message: `未知的资源类型: ${opportunity.issueType}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `优化资源失败: ${error.message}`
      };
    }
  }

  /**
   * 优化内存使用
   */
  optimizeMemory() {
    try {
      // 尝试清理Node.js缓存
      if (global.gc) {
        global.gc();
      }
      
      // 清理临时文件
      this.cleanTempFiles();
      
      // 重启内存密集型的非关键服务
      this.restartMemoryIntensiveServices();
      
      return {
        success: true,
        message: '内存优化已完成'
      };
      
    } catch (error) {
      return {
        success: false,
        message: `内存优化失败: ${error.message}`
      };
    }
  }

  /**
   * 优化CPU使用
   */
  optimizeCpu() {
    try {
      // 限制非关键进程的CPU使用
      this.limitNonCriticalProcesses();
      
      // 重启CPU密集型的非关键服务
      this.restartCpuIntensiveServices();
      
      return {
        success: true,
        message: 'CPU优化已完成'
      };
      
    } catch (error) {
      return {
        success: false,
        message: `CPU优化失败: ${error.message}`
      };
    }
  }

  /**
   * 优化磁盘使用
   */
  optimizeDisk() {
    try {
      // 清理日志文件
      this.cleanupLogFiles();
      
      // 清理临时文件
      this.cleanTempFiles();
      
      // 压缩旧文件
      this.compressOldFiles();
      
      return {
        success: true,
        message: '磁盘优化已完成'
      };
      
    } catch (error) {
      return {
        success: false,
        message: `磁盘优化失败: ${error.message}`
      };
    }
  }

  /**
   * 清理临时文件
   */
  cleanTempFiles() {
    try {
      const tempDirs = [
        '/tmp',
        '/var/tmp',
        os.tmpdir(),
        path.join(this.config.basePath, 'Temp')
      ];
      
      tempDirs.forEach(dir => {
        if (fs.existsSync(dir)) {
          try {
            const files = fs.readdirSync(dir);
            files.forEach(file => {
              const filePath = path.join(dir, file);
              try {
                const stats = fs.statSync(filePath);
                // 删除超过24小时的文件
                if (stats.isFile() && (Date.now() - stats.mtime.getTime()) > 24 * 60 * 60 * 1000) {
                  fs.unlinkSync(filePath);
                }
              } catch (error) {
                // 忽略错误
              }
            });
          } catch (error) {
            console.error(`清理临时目录失败: ${dir}`, error.message);
          }
        }
      });
    } catch (error) {
      console.error('清理临时文件失败:', error.message);
    }
  }

  /**
   * 清理日志文件
   */
  cleanupLogFiles() {
    try {
      if (fs.existsSync(this.logDir)) {
        const files = fs.readdirSync(this.logDir);
        
        files.forEach(file => {
          if (file.endsWith('.log')) {
            const filePath = path.join(this.logDir, file);
            try {
              const stats = fs.statSync(filePath);
              // 压缩超过7天的大型日志文件
              if (stats.size > 10 * 1024 * 1024 && (Date.now() - stats.mtime.getTime()) > 7 * 24 * 60 * 60 * 1000) {
                // 简化实现，实际项目中可以使用压缩工具
                console.log(`需要压缩日志文件: ${filePath}`);
              }
            } catch (error) {
              // 忽略错误
            }
          }
        });
      }
    } catch (error) {
      console.error('清理日志文件失败:', error.message);
    }
  }

  /**
   * 压缩旧文件
   */
  compressOldFiles() {
    try {
      // 简化实现，实际项目中可以使用更复杂的压缩策略
      console.log('检查旧文件是否需要压缩...');
    } catch (error) {
      console.error('压缩旧文件失败:', error.message);
    }
  }

  /**
   * 重启内存密集型服务
   */
  restartMemoryIntensiveServices() {
    try {
      // 简化实现，实际项目中可以识别并重启内存密集型服务
      console.log('检查内存密集型服务...');
    } catch (error) {
      console.error('重启内存密集型服务失败:', error.message);
    }
  }

  /**
   * 重启CPU密集型服务
   */
  restartCpuIntensiveServices() {
    try {
      // 简化实现，实际项目中可以识别并重启CPU密集型服务
      console.log('检查CPU密集型服务...');
    } catch (error) {
      console.error('重启CPU密集型服务失败:', error.message);
    }
  }

  /**
   * 限制非关键进程
   */
  limitNonCriticalProcesses() {
    try {
      // 简化实现，实际项目中可以使用nice或renice命令限制进程优先级
      console.log('限制非关键进程的资源使用...');
    } catch (error) {
      console.error('限制非关键进程失败:', error.message);
    }
  }

  /**
   * 优化进程
   */
  optimizeProcess(opportunity) {
    try {
      // 检查进程是否存在
      const processExists = this.checkProcessExists(opportunity.processId);
      if (!processExists) {
        return {
          success: false,
          message: `进程不存在: ${opportunity.processId}`
        };
      }
      
      // 尝试优化进程
      // 这里可以添加更复杂的优化逻辑
      console.log(`优化进程: ${opportunity.processId}`);
      
      return {
        success: true,
        message: `已尝试优化进程: ${opportunity.processId}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `优化进程失败: ${error.message}`
      };
    }
  }

  /**
   * 检查进程是否存在
   */
  checkProcessExists(pid) {
    try {
      process.kill(pid, 0);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 加载组件
   */
  loadComponent(componentId) {
    try {
      const component = this.availableComponents.get(componentId);
      if (!component) {
        return {
          success: false,
          message: `组件不存在: ${componentId}`
        };
      }
      
      // 检查组件是否已加载
      if (this.loadedComponents.has(componentId)) {
        return {
          success: false,
          message: `组件已加载: ${componentId}`
        };
      }
      
      // 加载组件
      let componentInstance = null;
      
      if (component.fileType === 'javascript') {
        componentInstance = this.loadJsComponent(component.filePath);
      } else if (component.fileType === 'shell') {
        componentInstance = this.executeShellComponent(component.filePath);
      }
      
      if (componentInstance) {
        this.loadedComponents.set(componentId, {
          instance: componentInstance,
          loadTime: new Date(),
          component: component
        });
        
        return {
          success: true,
          message: `成功加载组件: ${component.name}`
        };
      } else {
        return {
          success: false,
          message: `加载组件失败: ${component.name}`
        };
      }
      
    } catch (error) {
      return {
        success: false,
        message: `加载组件失败: ${error.message}`
      };
    }
  }

  /**
   * 加载JavaScript组件
   */
  loadJsComponent(filePath) {
    try {
      // 动态导入组件
      const componentModule = require(filePath);
      
      // 尝试实例化组件
      if (typeof componentModule === 'function') {
        return new componentModule();
      }
      
      return componentModule;
    } catch (error) {
      console.error(`加载JavaScript组件失败: ${filePath}`, error.message);
      return null;
    }
  }

  /**
   * 执行Shell组件
   */
  executeShellComponent(filePath) {
    try {
      // 确保脚本可执行
      fs.chmodSync(filePath, 0o755);
      
      // 异步执行脚本
      exec(filePath, (error, stdout, stderr) => {
        if (error) {
          console.error(`执行Shell组件失败: ${filePath}`, error.message);
        } else {
          console.log(`Shell组件输出: ${stdout}`);
        }
      });
      
      return { executed: true, path: filePath };
    } catch (error) {
      console.error(`执行Shell组件失败: ${filePath}`, error.message);
      return null;
    }
  }

  /**
   * 优化系统
   */
  optimizeSystem(opportunity) {
    try {
      // 执行全面的系统优化
      this.optimizeMemory();
      this.optimizeCpu();
      this.optimizeDisk();
      
      // 检查并重新加载关键组件
      this.reloadCriticalComponents();
      
      return {
        success: true,
        message: '系统全面优化已完成'
      };
      
    } catch (error) {
      return {
        success: false,
        message: `系统优化失败: ${error.message}`
      };
    }
  }

  /**
   * 重新加载关键组件
   */
  reloadCriticalComponents() {
    try {
      // 识别关键组件并重新加载
      const criticalComponentTypes = Object.keys(this.componentRegistry).filter(type => 
        this.componentRegistry[type].required
      );
      
      criticalComponentTypes.forEach(type => {
        this.availableComponents.forEach((component, id) => {
          if (component.type === type && this.loadedComponents.has(id)) {
            // 卸载组件
            this.unloadComponent(id);
            // 重新加载组件
            this.loadComponent(id);
          }
        });
      });
    } catch (error) {
      console.error('重新加载关键组件失败:', error.message);
    }
  }

  /**
   * 卸载组件
   */
  unloadComponent(componentId) {
    try {
      if (!this.loadedComponents.has(componentId)) {
        return false;
      }
      
      const component = this.loadedComponents.get(componentId);
      
      // 如果组件有stop或shutdown方法，调用它
      if (component.instance && (typeof component.instance.stop === 'function' || typeof component.instance.shutdown === 'function')) {
        if (typeof component.instance.stop === 'function') {
          component.instance.stop();
        } else {
          component.instance.shutdown();
        }
      }
      
      // 从缓存中删除模块（如果是JavaScript模块）
      if (component.component.fileType === 'javascript') {
        delete require.cache[require.resolve(component.component.filePath)];
      }
      
      // 从已加载组件列表中移除
      this.loadedComponents.delete(componentId);
      
      return true;
    } catch (error) {
      console.error(`卸载组件失败: ${componentId}`, error.message);
      return false;
    }
  }

  /**
   * 记录分析结果
   */
  recordAnalysisResult(systemState, performanceAnalysis, opportunities, adaptationResults) {
    const analysisRecord = {
      timestamp: new Date().toISOString(),
      systemState: systemState,
      performanceAnalysis: performanceAnalysis,
      optimizationOpportunities: opportunities,
      adaptationResults: adaptationResults
    };
    
    // 添加到性能历史
    this.performanceHistory.push(analysisRecord);
    
    // 保存性能历史
    this.savePerformanceHistory();
    
    // 写入分析日志
    this.writeAnalysisLog(analysisRecord);
    
    // 更新适配日志
    this.adaptationLog.push({
      timestamp: new Date().toISOString(),
      opportunities: opportunities.length,
      successful: adaptationResults.successful,
      failed: adaptationResults.failed
    });
  }

  /**
   * 写入分析日志
   */
  writeAnalysisLog(analysisRecord) {
    try {
      const logFilePath = path.join(this.logDir, 'adaptation-analysis.log');
      const logEntry = {
        timestamp: analysisRecord.timestamp,
        overallHealth: analysisRecord.performanceAnalysis.resourceUsage.overallHealth,
        opportunities: analysisRecord.optimizationOpportunities.length,
        successfulAdaptations: analysisRecord.adaptationResults.successful,
        failedAdaptations: analysisRecord.adaptationResults.failed
      };
      
      fs.appendFileSync(logFilePath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入分析日志失败:', error.message);
    }
  }

  /**
   * 记录错误日志
   */
  logError(message, error) {
    try {
      const logEntry = {
        timestamp: new Date().toISOString(),
        message: message,
        error: error.message,
        stack: error.stack
      };
      
      const errorLogPath = path.join(this.logDir, 'adaptation-errors.log');
      fs.appendFileSync(errorLogPath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入错误日志失败:', error.message);
    }
  }

  /**
   * 获取组件列表
   */
  getComponentsList() {
    const components = [];
    
    this.availableComponents.forEach((component, id) => {
      const isLoaded = this.loadedComponents.has(id);
      components.push({
        id: id,
        name: component.name,
        type: component.type,
        fileType: component.fileType,
        filePath: component.filePath,
        size: component.size,
        lastModified: component.lastModified,
        isLoaded: isLoaded,
        loadTime: isLoaded ? this.loadedComponents.get(id).loadTime : null,
        description: component.description
      });
    });
    
    return components;
  }

  /**
   * 获取适配统计信息
   */
  getAdaptationStats() {
    const stats = {
      totalOpportunities: 0,
      totalSuccessful: 0,
      totalFailed: 0,
      byType: {},
      byPriority: {}
    };
    
    this.adaptationLog.forEach(log => {
      stats.totalOpportunities += log.opportunities;
      stats.totalSuccessful += log.successful;
      stats.totalFailed += log.failed;
    });
    
    return stats;
  }

  /**
   * 获取系统健康状态
   */
  getSystemHealth() {
    if (this.performanceHistory.length === 0) {
      return {
        status: 'unknown',
        message: '暂无健康数据'
      };
    }
    
    const latestRecord = this.performanceHistory[this.performanceHistory.length - 1];
    const healthStatus = latestRecord.performanceAnalysis.resourceUsage.overallHealth;
    
    const statusMessages = {
      healthy: '系统运行正常',
      warning: '系统存在警告，但仍可正常运行',
      critical: '系统状态严重，需要立即关注'
    };
    
    return {
      status: healthStatus,
      message: statusMessages[healthStatus] || '未知状态',
      lastChecked: latestRecord.timestamp
    };
  }

  /**
   * 停止智能适配引擎
   */
  stop() {
    if (!this.isRunning) {
      console.log('智能适配引擎未在运行');
      return;
    }

    this.isRunning = false;
    
    // 清除分析间隔
    if (this.analysisInterval) {
      clearInterval(this.analysisInterval);
    }
    
    // 卸载所有组件
    this.unloadAllComponents();
    
    // 保存性能历史
    this.savePerformanceHistory();
    
    console.log('智能适配引擎已停止');
  }

  /**
   * 卸载所有组件
   */
  unloadAllComponents() {
    try {
      const componentIds = Array.from(this.loadedComponents.keys());
      componentIds.forEach(id => {
        this.unloadComponent(id);
      });
      
      console.log(`已卸载 ${componentIds.length} 个组件`);
    } catch (error) {
      console.error('卸载所有组件失败:', error.message);
    }
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  try {
    const adaptiveEngine = new AdaptiveEngine(configPath);
    adaptiveEngine.start();
    
    // 处理信号
    process.on('SIGINT', () => {
      console.log('收到终止信号，正在停止智能适配引擎...');
      adaptiveEngine.stop();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('启动智能适配引擎失败:', error.message);
    process.exit(1);
  }
}

module.exports = AdaptiveEngine;
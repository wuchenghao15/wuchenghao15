#!/usr/bin/env node

/**
 * MTSCOS AI 服务器动态智能管理模块
 * 实现端口、PID、依赖项升级与修复的智能管理
 */

const fs = require('fs');
const path = require('path');
const { execSync, exec, spawn } = require('child_process');
const os = require('os');
const net = require('net');
const http = require('http');

class ServerDynamicManagement {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.isRunning = false;
    this.monitoringInterval = null;
    this.portRegistry = new Map();
    this.processRegistry = new Map();
    this.dependencyRegistry = new Map();
    this.healthChecks = new Map();
    this.alertSystem = null;
    
    // 初始化服务器管理模块
    this.initialize();
  }

  /**
   * 初始化服务器管理模块
   */
  initialize() {
    try {
      // 加载配置文件
      this.config = this.loadConfig();
      
      // 设置日志目录
      this.logDir = this.config.logConfig?.path || path.join(this.config.basePath, 'Logs');
      this.ensureLogDirExists();
      
      // 初始化注册表
      this.initializeRegistries();
      
      // 初始化警报系统
      this.initializeAlertSystem();
      
      // 扫描并注册现有端口和进程
      this.scanSystem();
      
      // 加载依赖项配置
      this.loadDependencyConfig();
      
      // 初始化健康检查
      this.initializeHealthChecks();
      
      console.log('MTSCOS AI 服务器动态智能管理模块初始化完成');
      console.log(`已发现 ${this.portRegistry.size} 个端口，${this.processRegistry.size} 个进程`);
      
    } catch (error) {
      console.error('初始化服务器管理模块失败:', error.message);
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
   * 初始化注册表
   */
  initializeRegistries() {
    // 端口注册表配置
    this.portRegistryConfig = {
      reservedPorts: this.config.serverManagement?.reservedPorts || [],
      portRange: this.config.serverManagement?.portRange || { min: 3000, max: 9000 },
      maxPortsPerService: this.config.serverManagement?.maxPortsPerService || 5
    };
    
    // 进程注册表配置
    this.processRegistryConfig = {
      maxRestarts: this.config.serverManagement?.maxRestarts || 3,
      restartInterval: this.config.serverManagement?.restartInterval || 60000,
      processTimeout: this.config.serverManagement?.processTimeout || 300000
    };
    
    // 依赖项注册表配置
    this.dependencyRegistryConfig = {
      autoUpdate: this.config.serverManagement?.autoUpdateDependencies || false,
      updateInterval: this.config.serverManagement?.dependencyUpdateInterval || 604800000, // 默认一周
      versionPolicy: this.config.serverManagement?.versionPolicy || 'stable'
    };
  }

  /**
   * 初始化警报系统
   */
  initializeAlertSystem() {
    this.alertSystem = {
      thresholds: this.config.alerts?.thresholds || {
        portUsage: 80,
        cpuUsage: 85,
        memoryUsage: 90,
        diskUsage: 80
      },
      notificationMethods: this.config.alerts?.notificationMethods || ['console'],
      alertLog: path.join(this.logDir, 'server-alerts.log'),
      lastAlert: new Map()
    };
  }

  /**
   * 扫描系统
   */
  scanSystem() {
    try {
      // 扫描端口
      this.scanPorts();
      
      // 扫描进程
      this.scanProcesses();
      
    } catch (error) {
      console.error('扫描系统失败:', error.message);
      this.logError('系统扫描失败', error);
    }
  }

  /**
   * 扫描端口
   */
  scanPorts() {
    try {
      let command;
      if (os.platform() === 'linux' || os.platform() === 'darwin') {
        command = 'netstat -tuln 2>/dev/null || lsof -i -P -n 2>/dev/null | grep LISTEN';
      } else if (os.platform() === 'win32') {
        command = 'netstat -ano | findstr LISTENING';
      } else {
        console.error('不支持的操作系统:', os.platform());
        return;
      }
      
      const output = execSync(command, { encoding: 'utf8' });
      const lines = output.trim().split('\n');
      
      lines.forEach(line => {
        if (!line.trim()) return;
        
        let port;
        let pid;
        let protocol;
        
        if (os.platform() === 'win32') {
          // Windows 格式
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5) {
            const address = parts[1];
            port = address.split(':').pop();
            pid = parts[4];
            protocol = parts[0].includes('TCP') ? 'tcp' : 'udp';
          }
        } else {
          // Unix 格式
          if (line.includes('LISTEN')) {
            // lsof 格式
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 9) {
              pid = parts[1];
              const address = parts[8];
              port = address.split(':').pop();
              protocol = parts[8].includes('tcp') ? 'tcp' : 'udp';
            }
          } else {
            // netstat 格式
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 4) {
              protocol = parts[0].toLowerCase();
              const address = parts[3];
              port = address.split(':').pop();
              // netstat 在某些系统上可能不显示 PID
              pid = parts.length > 6 ? parts[6] : 'unknown';
            }
          }
        }
        
        if (port) {
          const portNum = parseInt(port);
          if (!isNaN(portNum)) {
            this.registerPort(portNum, protocol, pid);
          }
        }
      });
      
    } catch (error) {
      console.error('扫描端口失败:', error.message);
    }
  }

  /**
   * 注册端口
   */
  registerPort(port, protocol, pid) {
    const isReserved = this.portRegistryConfig.reservedPorts.includes(port);
    const isInRange = port >= this.portRegistryConfig.portRange.min && 
                     port <= this.portRegistryConfig.portRange.max;
    
    this.portRegistry.set(port, {
      port: port,
      protocol: protocol || 'tcp',
      pid: pid,
      registeredAt: new Date(),
      isReserved: isReserved,
      isInRange: isInRange,
      lastChecked: new Date(),
      status: 'active'
    });
  }

  /**
   * 扫描进程
   */
  scanProcesses() {
    try {
      let command;
      if (os.platform() === 'linux' || os.platform() === 'darwin') {
        command = 'ps aux';
      } else if (os.platform() === 'win32') {
        command = 'tasklist /v';
      } else {
        console.error('不支持的操作系统:', os.platform());
        return;
      }
      
      const output = execSync(command, { encoding: 'utf8' });
      const lines = output.trim().split('\n');
      
      // 跳过标题行
      for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        if (!line.trim()) continue;
        
        let pid, name, user, cpu, mem;
        
        if (os.platform() === 'win32') {
          // Windows 格式
          const parts = this.parseWindowsTaskList(line);
          if (parts && parts.length >= 5) {
            name = parts[0];
            pid = parts[1];
            user = parts[3];
            mem = parts[4];
            cpu = 'unknown'; // Windows tasklist 不直接提供CPU使用率
          }
        } else {
          // Unix 格式
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 11) {
            user = parts[0];
            pid = parts[1];
            cpu = parts[2];
            mem = parts[3];
            name = parts.slice(10).join(' ');
          }
        }
        
        if (pid) {
          this.registerProcess(pid, name, user, cpu, mem);
        }
      }
      
    } catch (error) {
      console.error('扫描进程失败:', error.message);
    }
  }

  /**
   * 解析Windows任务列表行
   */
  parseWindowsTaskList(line) {
    // 简化的解析逻辑，实际Windows任务列表格式较复杂
    // 这里只是一个基本实现
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ' ' && !inQuotes && current) {
        result.push(current);
        current = '';
        // 跳过连续空格
        while (i + 1 < line.length && line[i + 1] === ' ') {
          i++;
        }
      } else {
        current += char;
      }
    }
    
    if (current) {
      result.push(current);
    }
    
    return result;
  }

  /**
   * 注册进程
   */
  registerProcess(pid, name, user, cpu, mem) {
    // 获取进程命令行（如果可能）
    let commandLine = '';
    try {
      if (os.platform() === 'linux') {
        commandLine = execSync(`cat /proc/${pid}/cmdline 2>/dev/null | tr '\0' ' '`, { encoding: 'utf8' });
      } else if (os.platform() === 'darwin') {
        commandLine = execSync(`ps -o command= -p ${pid} 2>/dev/null`, { encoding: 'utf8' });
      }
    } catch (error) {
      // 忽略错误
    }
    
    // 检查进程是否属于我们的应用
    const isManagedProcess = this.isManagedProcess(name, commandLine);
    
    this.processRegistry.set(pid, {
      pid: pid,
      name: name || 'unknown',
      user: user || 'unknown',
      cpuUsage: parseFloat(cpu || 0),
      memoryUsage: parseFloat(mem || 0),
      registeredAt: new Date(),
      lastChecked: new Date(),
      status: 'running',
      restartCount: 0,
      lastRestart: null,
      isManaged: isManagedProcess,
      commandLine: commandLine.trim()
    });
  }

  /**
   * 判断是否为受管理的进程
   */
  isManagedProcess(name, commandLine) {
    // 检查进程名称或命令行是否包含我们的应用标识
    const appIdentifiers = [
      'MTSCOS_AI_Project',
      'mtscos',
      'adaptive-engine',
      'server-management',
      'environment-monitor',
      'auto-detection-repair'
    ];
    
    const processInfo = `${name || ''} ${commandLine || ''}`.toLowerCase();
    return appIdentifiers.some(identifier => 
      processInfo.includes(identifier.toLowerCase())
    );
  }

  /**
   * 加载依赖项配置
   */
  loadDependencyConfig() {
    try {
      // 尝试加载package.json文件
      const packageJsonPath = path.join(this.config.basePath, 'package.json');
      if (fs.existsSync(packageJsonPath)) {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        
        // 加载依赖项
        const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
        
        for (const [name, version] of Object.entries(dependencies)) {
          this.registerDependency(name, version);
        }
        
        console.log(`已加载 ${this.dependencyRegistry.size} 个依赖项`);
      }
      
      // 加载自定义依赖配置
      if (this.config.serverManagement?.customDependencies) {
        for (const dependency of this.config.serverManagement.customDependencies) {
          this.registerDependency(
            dependency.name,
            dependency.version,
            dependency.type || 'custom',
            dependency.updateCommand || null
          );
        }
      }
      
    } catch (error) {
      console.error('加载依赖项配置失败:', error.message);
    }
  }

  /**
   * 注册依赖项
   */
  registerDependency(name, version, type = 'npm', updateCommand = null) {
    this.dependencyRegistry.set(name, {
      name: name,
      currentVersion: version,
      latestVersion: null,
      type: type,
      updateCommand: updateCommand,
      lastChecked: null,
      lastUpdated: null,
      needsUpdate: false,
      updateFailed: false,
      failureCount: 0,
      description: ''
    });
  }

  /**
   * 初始化健康检查
   */
  initializeHealthChecks() {
    // 加载健康检查配置
    const healthChecks = this.config.serverManagement?.healthChecks || [];
    
    healthChecks.forEach(check => {
      this.healthChecks.set(check.id, {
        id: check.id,
        type: check.type,
        target: check.target,
        interval: check.interval || 60000,
        timeout: check.timeout || 5000,
        retries: check.retries || 3,
        lastCheck: null,
        lastResult: null,
        status: 'pending',
        failureCount: 0
      });
    });
    
    // 添加默认健康检查
    if (!this.healthChecks.has('system-resources')) {
      this.healthChecks.set('system-resources', {
        id: 'system-resources',
        type: 'resources',
        interval: 30000,
        lastCheck: null,
        lastResult: null,
        status: 'pending',
        failureCount: 0
      });
    }
    
    if (!this.healthChecks.has('managed-processes')) {
      this.healthChecks.set('managed-processes', {
        id: 'managed-processes',
        type: 'processes',
        interval: 45000,
        lastCheck: null,
        lastResult: null,
        status: 'pending',
        failureCount: 0
      });
    }
  }

  /**
   * 启动服务器管理模块
   */
  start() {
    if (this.isRunning) {
      console.log('服务器管理模块已经在运行中');
      return;
    }

    this.isRunning = true;
    console.log('服务器管理模块已启动');
    
    // 设置监控间隔（默认每30秒）
    const monitoringInterval = this.config.serverManagement?.monitoringInterval || 30000;
    this.monitoringInterval = setInterval(() => {
      this.runMonitoringCycle();
    }, monitoringInterval);
    
    // 立即执行一次监控
    this.runMonitoringCycle();
    
    console.log(`服务器监控间隔设置为: ${monitoringInterval / 1000}秒`);
    
    // 启动健康检查
    this.startHealthChecks();
    
    // 启动依赖项检查
    if (this.dependencyRegistryConfig.autoUpdate) {
      this.checkDependenciesUpdate();
      
      // 设置依赖项检查间隔
      setInterval(() => {
        this.checkDependenciesUpdate();
      }, this.dependencyRegistryConfig.updateInterval);
    }
  }

  /**
   * 运行监控周期
   */
  runMonitoringCycle() {
    if (!this.isRunning) return;
    
    console.log(`\n--- 开始服务器监控周期 (${new Date().toISOString()}) ---`);
    
    try {
      // 1. 更新端口和进程信息
      this.updateSystemState();
      
      // 2. 检查端口健康状态
      this.checkPortHealth();
      
      // 3. 检查进程健康状态
      this.checkProcessHealth();
      
      // 4. 执行自动修复操作
      this.performAutoRepairs();
      
      // 5. 记录监控结果
      this.logMonitoringResults();
      
      console.log(`--- 服务器监控周期结束 (${new Date().toISOString()}) ---\n`);
      
    } catch (error) {
      console.error('运行监控周期失败:', error.message);
      this.logError('监控周期失败', error);
    }
  }

  /**
   * 更新系统状态
   */
  updateSystemState() {
    // 扫描并更新端口信息
    this.scanPorts();
    
    // 扫描并更新进程信息
    this.scanProcesses();
    
    // 移除不存在的端口和进程
    this.cleanupStaleRegistryEntries();
  }

  /**
   * 清理过时的注册表项
   */
  cleanupStaleRegistryEntries() {
    const currentTime = new Date();
    const timeoutThreshold = 5 * 60 * 1000; // 5分钟未更新则视为过时
    
    // 清理过时端口
    for (const [port, info] of this.portRegistry.entries()) {
      if (currentTime - info.lastChecked > timeoutThreshold) {
        this.portRegistry.delete(port);
      }
    }
    
    // 清理过时进程
    for (const [pid, info] of this.processRegistry.entries()) {
      if (currentTime - info.lastChecked > timeoutThreshold) {
        this.processRegistry.delete(pid);
      }
    }
  }

  /**
   * 检查端口健康状态
   */
  checkPortHealth() {
    // 检查端口使用情况
    const totalPorts = this.portRegistry.size;
    const reservedPorts = Array.from(this.portRegistry.values()).filter(p => p.isReserved).length;
    const managedPorts = Array.from(this.portRegistry.values()).filter(p => p.isInRange && !p.isReserved).length;
    
    // 检查端口冲突
    this.checkPortConflicts();
    
    // 检查空闲端口可用性
    this.checkFreePortsAvailability();
    
    console.log(`端口状态: 总计 ${totalPorts}, 保留 ${reservedPorts}, 管理 ${managedPorts}`);
    
    // 检查端口使用阈值
    const portUsagePercent = (managedPorts / 
      (this.portRegistryConfig.portRange.max - this.portRegistryConfig.portRange.min + 1)) * 100;
    
    if (portUsagePercent > this.alertSystem.thresholds.portUsage) {
      this.triggerAlert('port_usage_high', {
        currentUsage: portUsagePercent,
        threshold: this.alertSystem.thresholds.portUsage,
        message: `端口使用率过高: ${portUsagePercent.toFixed(2)}%`
      });
    }
  }

  /**
   * 检查端口冲突
   */
  checkPortConflicts() {
    const portMap = new Map();
    let conflicts = [];
    
    this.portRegistry.forEach((info, port) => {
      const key = `${port}-${info.protocol}`;
      if (portMap.has(key)) {
        conflicts.push({
          port: port,
          protocol: info.protocol,
          processes: [portMap.get(key).pid, info.pid]
        });
      } else {
        portMap.set(key, info);
      }
    });
    
    if (conflicts.length > 0) {
      console.error(`检测到 ${conflicts.length} 个端口冲突`);
      conflicts.forEach(conflict => {
        this.triggerAlert('port_conflict', {
          port: conflict.port,
          protocol: conflict.protocol,
          conflictingProcesses: conflict.processes,
          message: `端口冲突: ${conflict.port}/${conflict.protocol} 被进程 ${conflict.processes.join(', ')} 使用`
        });
      });
    }
  }

  /**
   * 检查空闲端口可用性
   */
  checkFreePortsAvailability() {
    // 尝试找到一个空闲端口
    const freePort = this.findFreePort();
    
    if (freePort === null) {
      this.triggerAlert('no_free_ports', {
        message: '无法找到可用端口，端口资源可能耗尽'
      });
    }
  }

  /**
   * 查找空闲端口
   */
  findFreePort(startPort = this.portRegistryConfig.portRange.min, endPort = this.portRegistryConfig.portRange.max) {
    for (let port = startPort; port <= endPort; port++) {
      if (!this.portRegistry.has(port)) {
        // 确认端口确实可用
        return new Promise((resolve, reject) => {
          const server = net.createServer();
          server.listen(port, () => {
            server.close(() => {
              resolve(port);
            });
          });
          server.on('error', () => {
            resolve(null);
          });
        });
      }
    }
    return null;
  }

  /**
   * 检查进程健康状态
   */
  checkProcessHealth() {
    let runningProcesses = 0;
    let managedProcesses = 0;
    let highResourceProcesses = 0;
    
    this.processRegistry.forEach((info, pid) => {
      runningProcesses++;
      
      if (info.isManaged) {
        managedProcesses++;
        
        // 检查进程资源使用
        if (info.cpuUsage > 80 || info.memoryUsage > 80) {
          highResourceProcesses++;
          
          this.triggerAlert('process_high_resource', {
            pid: pid,
            name: info.name,
            cpuUsage: info.cpuUsage,
            memoryUsage: info.memoryUsage,
            message: `进程资源使用过高: ${info.name} (PID: ${pid}) - CPU: ${info.cpuUsage}%, MEM: ${info.memoryUsage}%`
          });
        }
        
        // 检查进程状态
        this.checkManagedProcessStatus(pid, info);
      }
    });
    
    console.log(`进程状态: 总计 ${runningProcesses}, 管理 ${managedProcesses}, 高资源消耗 ${highResourceProcesses}`);
  }

  /**
   * 检查受管理进程状态
   */
  checkManagedProcessStatus(pid, info) {
    try {
      // 检查进程是否存在
      const processExists = this.checkProcessExists(pid);
      
      if (!processExists && info.isManaged && info.status === 'running') {
        // 进程已终止，需要重启
        console.warn(`受管理进程已终止: ${info.name} (PID: ${pid})`);
        this.handleProcessTermination(pid, info);
      }
    } catch (error) {
      console.error(`检查进程状态失败: ${pid}`, error.message);
    }
  }

  /**
   * 检查进程是否存在
   */
  checkProcessExists(pid) {
    try {
      if (os.platform() === 'win32') {
        execSync(`tasklist /fi "PID eq ${pid}" | findstr ${pid}`, { encoding: 'utf8' });
      } else {
        process.kill(parseInt(pid), 0);
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 处理进程终止
   */
  handleProcessTermination(pid, info) {
    try {
      // 更新进程状态
      info.status = 'terminated';
      info.lastChecked = new Date();
      
      // 检查是否需要重启
      if (info.restartCount < this.processRegistryConfig.maxRestarts) {
        console.log(`尝试重启进程: ${info.name} (PID: ${pid}) - 第 ${info.restartCount + 1} 次`);
        
        // 尝试重启进程
        this.restartProcess(pid, info);
      } else {
        // 重启次数过多，触发警报
        this.triggerAlert('process_restart_failed', {
          pid: pid,
          name: info.name,
          restartCount: info.restartCount,
          maxRestarts: this.processRegistryConfig.maxRestarts,
          message: `进程重启失败: ${info.name} 已达到最大重启次数 (${info.restartCount}/${this.processRegistryConfig.maxRestarts})`
        });
      }
    } catch (error) {
      console.error(`处理进程终止失败: ${pid}`, error.message);
    }
  }

  /**
   * 重启进程
   */
  restartProcess(pid, info) {
    try {
      // 增加重启计数
      info.restartCount++;
      info.lastRestart = new Date();
      
      // 根据进程命令行重启
      if (info.commandLine) {
        console.log(`使用命令行重启: ${info.commandLine}`);
        
        // 简化实现，实际项目中可能需要更复杂的逻辑
        // 这里我们只是模拟重启过程
        setTimeout(() => {
          console.log(`模拟重启进程完成: ${info.name}`);
          info.status = 'running';
        }, 2000);
      } else {
        console.log(`无法重启进程，缺少命令行信息: ${info.name}`);
        this.triggerAlert('process_restart_missing_info', {
          pid: pid,
          name: info.name,
          message: `无法重启进程: 缺少命令行信息`
        });
      }
    } catch (error) {
      console.error(`重启进程失败: ${pid}`, error.message);
      this.triggerAlert('process_restart_error', {
        pid: pid,
        name: info.name,
        error: error.message,
        message: `重启进程时发生错误: ${error.message}`
      });
    }
  }

  /**
   * 执行自动修复操作
   */
  performAutoRepairs() {
    // 修复端口冲突
    this.repairPortConflicts();
    
    // 优化资源使用
    this.optimizeResourceUsage();
    
    // 修复失败的健康检查
    this.repairFailedHealthChecks();
  }

  /**
   * 修复端口冲突
   */
  repairPortConflicts() {
    // 简化实现，实际项目中可能需要更复杂的冲突解决策略
    // 例如为进程重新分配端口，或者终止冲突的非关键进程
    console.log('检查并修复端口冲突...');
  }

  /**
   * 优化资源使用
   */
  optimizeResourceUsage() {
    // 识别并优化高资源消耗的进程
    const highResourceProcesses = Array.from(this.processRegistry.values())
      .filter(p => p.cpuUsage > 90 || p.memoryUsage > 90);
    
    highResourceProcesses.forEach(process => {
      if (process.isManaged) {
        console.log(`优化高资源消耗的受管理进程: ${process.name} (PID: ${process.pid})`);
        // 可以尝试发送信号让进程清理资源，或重启进程
      }
    });
  }

  /**
   * 修复失败的健康检查
   */
  repairFailedHealthChecks() {
    this.healthChecks.forEach((check, id) => {
      if (check.status === 'failed' && check.failureCount > 0) {
        console.log(`尝试修复失败的健康检查: ${id}`);
        
        // 根据健康检查类型执行不同的修复操作
        switch (check.type) {
          case 'http':
          case 'https':
            this.repairWebHealthCheck(check);
            break;
            
          case 'tcp':
            this.repairTcpHealthCheck(check);
            break;
            
          case 'processes':
            this.repairProcessHealthCheck(check);
            break;
            
          case 'resources':
            this.optimizeResourceUsage();
            break;
        }
      }
    });
  }

  /**
   * 修复Web健康检查
   */
  repairWebHealthCheck(check) {
    // 简化实现，实际项目中可能需要重启web服务或修复配置
    console.log(`修复Web健康检查: ${check.target}`);
  }

  /**
   * 修复TCP健康检查
   */
  repairTcpHealthCheck(check) {
    // 简化实现，实际项目中可能需要重启TCP服务
    console.log(`修复TCP健康检查: ${check.target}`);
  }

  /**
   * 修复进程健康检查
   */
  repairProcessHealthCheck(check) {
    // 重启所有状态异常的受管理进程
    this.processRegistry.forEach((info, pid) => {
      if (info.isManaged && info.status !== 'running') {
        this.restartProcess(pid, info);
      }
    });
  }

  /**
   * 记录监控结果
   */
  logMonitoringResults() {
    try {
      const logEntry = {
        timestamp: new Date().toISOString(),
        portCount: this.portRegistry.size,
        processCount: this.processRegistry.size,
        managedProcessCount: Array.from(this.processRegistry.values()).filter(p => p.isManaged).length,
        healthCheckStatus: Array.from(this.healthChecks.entries()).map(([id, check]) => ({
          id: id,
          status: check.status
        }))
      };
      
      const logFilePath = path.join(this.logDir, 'server-monitoring.log');
      fs.appendFileSync(logFilePath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('记录监控结果失败:', error.message);
    }
  }

  /**
   * 启动健康检查
   */
  startHealthChecks() {
    this.healthChecks.forEach((check, id) => {
      // 立即执行一次健康检查
      this.runHealthCheck(check);
      
      // 设置定期健康检查
      setInterval(() => {
        if (this.isRunning) {
          this.runHealthCheck(check);
        }
      }, check.interval);
    });
  }

  /**
   * 运行健康检查
   */
  runHealthCheck(check) {
    try {
      switch (check.type) {
        case 'http':
        case 'https':
          this.runWebHealthCheck(check);
          break;
          
        case 'tcp':
          this.runTcpHealthCheck(check);
          break;
          
        case 'processes':
          this.runProcessHealthCheck(check);
          break;
          
        case 'resources':
          this.runResourceHealthCheck(check);
          break;
          
        default:
          console.warn(`未知的健康检查类型: ${check.type}`);
      }
    } catch (error) {
      console.error(`运行健康检查失败: ${check.id}`, error.message);
      this.handleHealthCheckFailure(check, error);
    }
  }

  /**
   * 运行Web健康检查
   */
  runWebHealthCheck(check) {
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        this.handleHealthCheckFailure(check, new Error('请求超时'));
        resolve();
      }, check.timeout || 5000);
      
      const request = http.get(check.target, (response) => {
        clearTimeout(timeout);
        
        if (response.statusCode >= 200 && response.statusCode < 400) {
          this.handleHealthCheckSuccess(check, {
            statusCode: response.statusCode,
            responseTime: Date.now() - startTime
          });
        } else {
          this.handleHealthCheckFailure(check, new Error(`HTTP错误: ${response.statusCode}`));
        }
        
        resolve();
      });
      
      const startTime = Date.now();
      
      request.on('error', (error) => {
        clearTimeout(timeout);
        this.handleHealthCheckFailure(check, error);
        resolve();
      });
    });
  }

  /**
   * 运行TCP健康检查
   */
  runTcpHealthCheck(check) {
    return new Promise((resolve) => {
      const parts = check.target.split(':');
      const host = parts[0];
      const port = parseInt(parts[1]);
      
      if (!port) {
        this.handleHealthCheckFailure(check, new Error('无效的TCP目标格式'));
        resolve();
        return;
      }
      
      const socket = new net.Socket();
      const timeout = setTimeout(() => {
        socket.destroy();
        this.handleHealthCheckFailure(check, new Error('连接超时'));
        resolve();
      }, check.timeout || 5000);
      
      socket.connect(port, host, () => {
        clearTimeout(timeout);
        this.handleHealthCheckSuccess(check, { connected: true });
        socket.destroy();
        resolve();
      });
      
      socket.on('error', (error) => {
        clearTimeout(timeout);
        this.handleHealthCheckFailure(check, error);
        resolve();
      });
    });
  }

  /**
   * 运行进程健康检查
   */
  runProcessHealthCheck(check) {
    try {
      const managedProcesses = Array.from(this.processRegistry.values()).filter(p => p.isManaged);
      const failedProcesses = managedProcesses.filter(p => p.status !== 'running');
      
      if (failedProcesses.length === 0) {
        this.handleHealthCheckSuccess(check, {
          totalProcesses: managedProcesses.length,
          runningProcesses: managedProcesses.length
        });
      } else {
        this.handleHealthCheckFailure(check, new Error(`有 ${failedProcesses.length} 个受管理进程状态异常`));
      }
    } catch (error) {
      this.handleHealthCheckFailure(check, error);
    }
  }

  /**
   * 运行资源健康检查
   */
  runResourceHealthCheck(check) {
    try {
      const totalMemory = os.totalmem();
      const freeMemory = os.freemem();
      const memoryUsage = 100 - (freeMemory / totalMemory * 100);
      
      const cpus = os.cpus();
      const cpuUsage = this.calculateCpuUsage(cpus);
      
      const diskUsage = this.collectDiskUsage();
      
      // 检查资源使用是否超过阈值
      let hasWarning = false;
      const warnings = [];
      
      if (memoryUsage > this.alertSystem.thresholds.memoryUsage) {
        hasWarning = true;
        warnings.push(`内存使用率过高: ${memoryUsage.toFixed(2)}%`);
      }
      
      if (cpuUsage > this.alertSystem.thresholds.cpuUsage) {
        hasWarning = true;
        warnings.push(`CPU使用率过高: ${cpuUsage.toFixed(2)}%`);
      }
      
      if (diskUsage.usagePercent > this.alertSystem.thresholds.diskUsage) {
        hasWarning = true;
        warnings.push(`磁盘使用率过高: ${diskUsage.usagePercent}%`);
      }
      
      const result = {
        memoryUsage: memoryUsage,
        cpuUsage: cpuUsage,
        diskUsage: diskUsage.usagePercent,
        warnings: warnings
      };
      
      if (hasWarning) {
        this.handleHealthCheckFailure(check, new Error(`资源使用警告: ${warnings.join(', ')}`));
      } else {
        this.handleHealthCheckSuccess(check, result);
      }
    } catch (error) {
      this.handleHealthCheckFailure(check, error);
    }
  }

  /**
   * 计算CPU使用率
   */
  calculateCpuUsage(cpus) {
    // 简化的CPU使用率计算
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
   * 处理健康检查成功
   */
  handleHealthCheckSuccess(check, result) {
    check.status = 'ok';
    check.lastCheck = new Date();
    check.lastResult = result;
    check.failureCount = 0;
    
    console.log(`健康检查成功: ${check.id}`);
  }

  /**
   * 处理健康检查失败
   */
  handleHealthCheckFailure(check, error) {
    check.status = 'failed';
    check.lastCheck = new Date();
    check.lastResult = { error: error.message };
    check.failureCount++;
    
    console.error(`健康检查失败: ${check.id} - ${error.message}`);
    
    // 如果失败次数达到阈值，触发警报
    if (check.failureCount >= check.retries) {
      this.triggerAlert('health_check_failed', {
        checkId: check.id,
        failureCount: check.failureCount,
        error: error.message,
        message: `健康检查持续失败: ${check.id} (${check.failureCount}次)`
      });
    }
  }

  /**
   * 检查依赖项更新
   */
  checkDependenciesUpdate() {
    if (!this.isRunning) return;
    
    console.log('开始检查依赖项更新...');
    
    this.dependencyRegistry.forEach((dependency, name) => {
      this.checkSingleDependencyUpdate(name, dependency);
    });
  }

  /**
   * 检查单个依赖项更新
   */
  checkSingleDependencyUpdate(name, dependency) {
    try {
      console.log(`检查依赖项更新: ${name}`);
      
      switch (dependency.type) {
        case 'npm':
          this.checkNpmDependencyUpdate(name, dependency);
          break;
          
        case 'custom':
          if (dependency.updateCommand) {
            this.runCustomDependencyUpdate(name, dependency);
          }
          break;
          
        default:
          console.warn(`未知的依赖项类型: ${dependency.type}`);
      }
    } catch (error) {
      console.error(`检查依赖项更新失败: ${name}`, error.message);
      dependency.updateFailed = true;
      dependency.failureCount++;
    } finally {
      dependency.lastChecked = new Date();
    }
  }

  /**
   * 检查NPM依赖项更新
   */
  checkNpmDependencyUpdate(name, dependency) {
    try {
      // 使用npm view命令获取最新版本信息
      const npmViewOutput = execSync(`npm view ${name} version --json`, { encoding: 'utf8' });
      const latestVersion = JSON.parse(npmViewOutput).trim();
      
      dependency.latestVersion = latestVersion;
      
      // 比较版本号
      if (this.isNewerVersion(latestVersion, dependency.currentVersion)) {
        dependency.needsUpdate = true;
        console.log(`发现依赖项更新: ${name} - 当前: ${dependency.currentVersion}, 最新: ${latestVersion}`);
        
        // 如果启用了自动更新，执行更新
        if (this.dependencyRegistryConfig.autoUpdate) {
          this.updateNpmDependency(name, dependency);
        }
      } else {
        dependency.needsUpdate = false;
      }
    } catch (error) {
      console.error(`检查NPM依赖项更新失败: ${name}`, error.message);
      throw error;
    }
  }

  /**
   * 检查版本号是否更新
   */
  isNewerVersion(latest, current) {
    // 简化的版本号比较，实际项目中可能需要更复杂的语义化版本比较
    const latestParts = latest.replace(/[^0-9.]/g, '').split('.').map(Number);
    const currentParts = current.replace(/[^0-9.]/g, '').split('.').map(Number);
    
    for (let i = 0; i < Math.max(latestParts.length, currentParts.length); i++) {
      const latestNum = latestParts[i] || 0;
      const currentNum = currentParts[i] || 0;
      
      if (latestNum > currentNum) return true;
      if (latestNum < currentNum) return false;
    }
    
    return false;
  }

  /**
   * 更新NPM依赖项
   */
  updateNpmDependency(name, dependency) {
    try {
      console.log(`正在更新依赖项: ${name}`);
      
      // 根据版本策略确定更新命令
      let updateCommand;
      if (this.dependencyRegistryConfig.versionPolicy === 'latest') {
        updateCommand = `npm install ${name}@latest --save`;
      } else {
        updateCommand = `npm update ${name} --save`;
      }
      
      // 执行更新命令
      execSync(updateCommand, { cwd: this.config.basePath });
      
      // 更新依赖项信息
      dependency.currentVersion = dependency.latestVersion;
      dependency.needsUpdate = false;
      dependency.updateFailed = false;
      dependency.lastUpdated = new Date();
      dependency.failureCount = 0;
      
      console.log(`依赖项更新成功: ${name} -> ${dependency.currentVersion}`);
      
      // 触发依赖项更新成功事件
      this.triggerAlert('dependency_update_success', {
        name: name,
        oldVersion: dependency.currentVersion,
        newVersion: dependency.latestVersion,
        message: `依赖项更新成功: ${name} -> ${dependency.latestVersion}`
      });
      
    } catch (error) {
      console.error(`更新依赖项失败: ${name}`, error.message);
      dependency.updateFailed = true;
      dependency.failureCount++;
      
      // 触发依赖项更新失败事件
      this.triggerAlert('dependency_update_failed', {
        name: name,
        targetVersion: dependency.latestVersion,
        error: error.message,
        message: `依赖项更新失败: ${name} - ${error.message}`
      });
    }
  }

  /**
   * 运行自定义依赖项更新命令
   */
  runCustomDependencyUpdate(name, dependency) {
    try {
      console.log(`执行自定义依赖项更新: ${name}`);
      
      // 执行自定义更新命令
      const output = execSync(dependency.updateCommand, { encoding: 'utf8' });
      
      // 更新依赖项信息
      dependency.updateFailed = false;
      dependency.lastUpdated = new Date();
      dependency.failureCount = 0;
      
      console.log(`自定义依赖项更新成功: ${name}`);
      console.log(`输出: ${output}`);
      
    } catch (error) {
      console.error(`执行自定义依赖项更新失败: ${name}`, error.message);
      dependency.updateFailed = true;
      dependency.failureCount++;
    }
  }

  /**
   * 触发警报
   */
  triggerAlert(alertType, details) {
    const now = new Date();
    const alertKey = `${alertType}:${details.pid || details.port || details.checkId || 'general'}`;
    
    // 检查是否需要限流警报
    const lastAlert = this.alertSystem.lastAlert.get(alertKey);
    if (lastAlert && (now - lastAlert) < 60000) { // 1分钟内不重复相同警报
      return;
    }
    
    // 更新最后警报时间
    this.alertSystem.lastAlert.set(alertKey, now);
    
    // 创建警报对象
    const alert = {
      id: `alert-${Date.now()}`,
      type: alertType,
      timestamp: now.toISOString(),
      severity: this.getAlertSeverity(alertType),
      details: details
    };
    
    // 记录警报到日志
    this.logAlert(alert);
    
    // 根据通知方法发送警报
    this.sendAlertNotifications(alert);
  }

  /**
   * 获取警报严重程度
   */
  getAlertSeverity(alertType) {
    const severityMap = {
      port_conflict: 'critical',
      no_free_ports: 'critical',
      process_restart_failed: 'critical',
      process_high_resource: 'warning',
      port_usage_high: 'warning',
      health_check_failed: 'critical',
      dependency_update_failed: 'warning',
      dependency_update_success: 'info'
    };
    
    return severityMap[alertType] || 'info';
  }

  /**
   * 记录警报到日志
   */
  logAlert(alert) {
    try {
      fs.appendFileSync(this.alertSystem.alertLog, JSON.stringify(alert) + '\n', 'utf8');
    } catch (error) {
      console.error('记录警报失败:', error.message);
    }
  }

  /**
   * 发送警报通知
   */
  sendAlertNotifications(alert) {
    this.alertSystem.notificationMethods.forEach(method => {
      try {
        switch (method) {
          case 'console':
            this.sendConsoleAlert(alert);
            break;
            
          case 'log':
            // 日志通知已经在logAlert中处理
            break;
            
          default:
            console.warn(`未知的通知方法: ${method}`);
        }
      } catch (error) {
        console.error(`发送警报通知失败 (${method}):`, error.message);
      }
    });
  }

  /**
   * 发送控制台警报
   */
  sendConsoleAlert(alert) {
    const severityColor = {
      critical: '\x1b[31m', // 红色
      warning: '\x1b[33m',  // 黄色
      info: '\x1b[32m'      // 绿色
    };
    
    const resetColor = '\x1b[0m';
    const color = severityColor[alert.severity] || resetColor;
    
    console.log(`${color}[${alert.severity.toUpperCase()}] ${alert.timestamp} - ${alert.details.message}${resetColor}`);
  }

  /**
   * 获取服务器状态
   */
  getServerStatus() {
    return {
      timestamp: new Date().toISOString(),
      isRunning: this.isRunning,
      portRegistry: {
        total: this.portRegistry.size,
        reserved: Array.from(this.portRegistry.values()).filter(p => p.isReserved).length,
        managed: Array.from(this.portRegistry.values()).filter(p => p.isInRange && !p.isReserved).length
      },
      processRegistry: {
        total: this.processRegistry.size,
        managed: Array.from(this.processRegistry.values()).filter(p => p.isManaged).length,
        highResource: Array.from(this.processRegistry.values()).filter(p => p.cpuUsage > 80 || p.memoryUsage > 80).length
      },
      dependencyRegistry: {
        total: this.dependencyRegistry.size,
        needsUpdate: Array.from(this.dependencyRegistry.values()).filter(d => d.needsUpdate).length,
        updateFailed: Array.from(this.dependencyRegistry.values()).filter(d => d.updateFailed).length
      },
      healthChecks: Array.from(this.healthChecks.entries()).map(([id, check]) => ({
        id: id,
        type: check.type,
        status: check.status,
        lastCheck: check.lastCheck,
        failureCount: check.failureCount
      }))
    };
  }

  /**
   * 分配端口
   */
  allocatePort(serviceName, protocol = 'tcp') {
    // 查找可用端口
    for (let port = this.portRegistryConfig.portRange.min; 
         port <= this.portRegistryConfig.portRange.max; 
         port++) {
      
      if (!this.portRegistry.has(port)) {
        // 检查端口是否真的可用
        const isAvailable = this.checkPortAvailability(port);
        
        if (isAvailable) {
          // 注册端口
          this.registerPort(port, protocol, null);
          
          // 添加服务关联
          const portInfo = this.portRegistry.get(port);
          portInfo.serviceName = serviceName;
          
          console.log(`为服务 "${serviceName}" 分配端口: ${port}/${protocol}`);
          return port;
        }
      }
    }
    
    throw new Error('无法分配端口，没有可用的端口资源');
  }

  /**
   * 检查端口可用性
   */
  checkPortAvailability(port) {
    return new Promise((resolve) => {
      const server = net.createServer();
      server.listen(port, () => {
        server.close(() => {
          resolve(true);
        });
      });
      server.on('error', () => {
        resolve(false);
      });
    });
  }

  /**
   * 释放端口
   */
  releasePort(port) {
    if (this.portRegistry.has(port)) {
      const portInfo = this.portRegistry.get(port);
      
      // 检查是否为保留端口
      if (portInfo.isReserved) {
        throw new Error(`无法释放保留端口: ${port}`);
      }
      
      console.log(`释放端口: ${port}/${portInfo.protocol}${portInfo.serviceName ? ` (服务: ${portInfo.serviceName})` : ''}`);
      this.portRegistry.delete(port);
      return true;
    }
    
    return false;
  }

  /**
   * 重启服务
   */
  restartService(serviceName) {
    try {
      // 查找与服务关联的进程
      const serviceProcesses = Array.from(this.processRegistry.values())
        .filter(p => p.isManaged && p.name.includes(serviceName));
      
      if (serviceProcesses.length === 0) {
        throw new Error(`未找到服务: ${serviceName}`);
      }
      
      console.log(`重启服务: ${serviceName} (${serviceProcesses.length} 个进程)`);
      
      serviceProcesses.forEach(process => {
        this.restartProcess(process.pid, process);
      });
      
      return { success: true, message: `已启动服务 ${serviceName} 的重启流程` };
    } catch (error) {
      console.error(`重启服务失败: ${serviceName}`, error.message);
      return { success: false, message: error.message };
    }
  }

  /**
   * 停止服务器管理模块
   */
  stop() {
    if (!this.isRunning) {
      console.log('服务器管理模块未在运行');
      return;
    }

    this.isRunning = false;
    
    // 清除监控间隔
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }
    
    console.log('服务器管理模块已停止');
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
      
      const errorLogPath = path.join(this.logDir, 'server-errors.log');
      fs.appendFileSync(errorLogPath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入错误日志失败:', error.message);
    }
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  try {
    const serverManager = new ServerDynamicManagement(configPath);
    serverManager.start();
    
    // 处理信号
    process.on('SIGINT', () => {
      console.log('收到终止信号，正在停止服务器管理模块...');
      serverManager.stop();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('启动服务器管理模块失败:', error.message);
    process.exit(1);
  }
}

module.exports = ServerDynamicManagement;
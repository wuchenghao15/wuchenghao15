#!/usr/bin/env node

/**
 * MTSCOS AI 系统自动检测与修复引擎
 * 实现系统自主检测、修复、维护和监控功能
 * 功能包括：文件完整性检查、进程监控、异常修复、资源管理等
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync, spawn, exec } = require('child_process');
const os = require('os');
const http = require('http');

class AutoDetectionRepairEngine {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.logger = null;
    this.isRunning = false;
    this.lastIntegrityCheck = null;
    this.criticalFiles = [];
    this.monitoredProcesses = [];
    this.healthCheckResults = [];
    this.errorHistory = [];
    
    // 初始化引擎
    this.initialize();
  }

  /**
   * 初始化引擎配置和日志系统
   */
  initialize() {
    try {
      // 加载配置文件
      this.config = this.loadConfig();
      console.log('成功加载配置文件');
      
      // 初始化日志系统
      this.initializeLogger();
      console.log('成功初始化日志系统');
      
      // 收集关键文件信息
      this.collectCriticalFiles();
      console.log(`已收集 ${this.criticalFiles.length} 个关键文件用于监控`);
      
      // 初始化监控进程列表
      this.initializeMonitoredProcesses();
      console.log(`已配置 ${this.monitoredProcesses.length} 个进程监控项`);
      
      this.log('info', '自动检测与修复引擎初始化完成');
    } catch (error) {
      console.error('初始化引擎失败:', error.message);
      process.exit(1);
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
   * 初始化日志系统
   */
  initializeLogger() {
    // 确保日志目录存在
    const logDir = this.config.logConfig?.path || path.join(this.config.basePath, 'Logs');
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    // 创建日志文件路径
    const logFile = path.join(logDir, 'auto-detection.log');
    
    // 简易日志系统实现
    this.logger = {
      log: (level, message) => {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}] [${level.toUpperCase()}] ${message}\n`;
        
        // 写入文件
        fs.appendFileSync(logFile, logEntry, 'utf8');
        
        // 同时输出到控制台
        console[level === 'error' ? 'error' : 'log'](logEntry.trim());
      }
    };
  }

  /**
   * 记录日志
   */
  log(level, message) {
    if (this.logger) {
      this.logger.log(level, message);
    } else {
      console[level === 'error' ? 'error' : 'log'](`[${level.toUpperCase()}] ${message}`);
    }
  }

  /**
   * 收集关键文件信息用于完整性检查
   */
  collectCriticalFiles() {
    const criticalDirectories = [
      path.join(this.config.basePath, 'Scripts'),
      path.resolve(__dirname, '..', '..', '..', 'Scripts'),
      path.resolve(__dirname, '..', '..', '..', 'config')
    ];
    
    const fileExtensions = ['.js', '.sh', '.json', '.html', '.css'];
    
    criticalDirectories.forEach(dir => {
      if (fs.existsSync(dir)) {
        this.walkDirectory(dir, (filePath) => {
          if (fileExtensions.some(ext => filePath.endsWith(ext))) {
            try {
              const hash = this.calculateFileHash(filePath);
              this.criticalFiles.push({
                path: filePath,
                hash: hash,
                lastModified: fs.statSync(filePath).mtime
              });
            } catch (error) {
              this.log('warning', `无法处理文件 ${filePath}: ${error.message}`);
            }
          }
        });
      }
    });
  }

  /**
   * 遍历目录
   */
  walkDirectory(dir, callback) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      if (stat.isDirectory()) {
        // 跳过 node_modules 和 .git 目录
        if (file !== 'node_modules' && file !== '.git') {
          this.walkDirectory(filePath, callback);
        }
      } else {
        callback(filePath);
      }
    }
  }

  /**
   * 计算文件哈希值
   */
  calculateFileHash(filePath) {
    const fileBuffer = fs.readFileSync(filePath);
    const hash = crypto.createHash('sha256');
    hash.update(fileBuffer);
    return hash.digest('hex');
  }

  /**
   * 初始化监控进程列表
   */
  initializeMonitoredProcesses() {
    // 从配置中获取需要监控的进程
    this.monitoredProcesses = [
      {
        name: 'environment-monitor',
        script: this.config.scripts?.monitor,
        restartCommand: `node ${this.config.scripts?.monitor}`
      },
      {
        name: 'environment-maintenance',
        script: this.config.scripts?.maintenance,
        restartCommand: `node ${this.config.scripts?.maintenance}`
      }
    ];
  }

  /**
   * 启动自动检测与修复引擎
   */
  start() {
    if (this.isRunning) {
      this.log('warning', '引擎已经在运行中');
      return;
    }

    this.isRunning = true;
    this.log('info', '自动检测与修复引擎已启动');
    
    // 立即执行一次完整检查
    this.performFullSystemCheck();
    
    // 设置定期检查
    this.setupScheduledChecks();
  }

  /**
   * 停止引擎
   */
  stop() {
    if (!this.isRunning) {
      this.log('warning', '引擎已经停止');
      return;
    }

    this.isRunning = false;
    
    // 清除定时器
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }
    
    this.log('info', '自动检测与修复引擎已停止');
  }

  /**
   * 设置定期检查
   */
  setupScheduledChecks() {
    // 每5分钟执行一次快速检查
    this.checkInterval = setInterval(() => {
      if (this.isRunning) {
        this.performQuickCheck();
      }
    }, 5 * 60 * 1000);
    
    // 每小时执行一次完整检查
    setInterval(() => {
      if (this.isRunning) {
        this.performFullSystemCheck();
      }
    }, 60 * 60 * 1000);
  }

  /**
   * 执行快速检查
   */
  performQuickCheck() {
    this.log('info', '开始执行快速系统检查');
    
    try {
      // 检查进程状态
      this.checkProcesses();
      
      // 检查资源使用情况
      this.checkResourceUsage();
      
      // 检查系统基本健康状态
      this.checkSystemHealth();
      
      this.log('info', '快速系统检查完成');
    } catch (error) {
      this.log('error', `快速检查出错: ${error.message}`);
    }
  }

  /**
   * 执行完整系统检查
   */
  performFullSystemCheck() {
    this.log('info', '开始执行完整系统检查');
    
    try {
      // 执行所有检查
      this.checkFileIntegrity();
      this.checkProcesses();
      this.checkResourceUsage();
      this.checkSystemHealth();
      this.checkPermissions();
      this.checkNetworkConnectivity();
      
      // 保存检查结果
      this.saveHealthCheckResults();
      
      this.log('info', '完整系统检查完成');
    } catch (error) {
      this.log('error', `完整检查出错: ${error.message}`);
    }
  }

  /**
   * 检查文件完整性
   */
  checkFileIntegrity() {
    this.log('info', '开始文件完整性检查');
    let issuesFound = 0;
    
    this.criticalFiles.forEach(fileInfo => {
      try {
        // 检查文件是否存在
        if (!fs.existsSync(fileInfo.path)) {
          this.log('error', `文件缺失: ${fileInfo.path}`);
          issuesFound++;
          this.attemptFileRecovery(fileInfo.path);
          return;
        }
        
        // 计算当前哈希值并比较
        const currentHash = this.calculateFileHash(fileInfo.path);
        if (currentHash !== fileInfo.hash) {
          this.log('warning', `文件被修改: ${fileInfo.path}`);
          issuesFound++;
          
          // 记录修改信息
          const fileStat = fs.statSync(fileInfo.path);
          this.log('info', `修改时间: ${fileStat.mtime.toISOString()}`);
          
          // 尝试修复（如果配置允许）
          if (this.config.maintenance?.systemChecks?.autoRepair) {
            this.attemptFileRepair(fileInfo);
          }
        }
      } catch (error) {
        this.log('error', `检查文件 ${fileInfo.path} 时出错: ${error.message}`);
      }
    });
    
    this.log('info', `文件完整性检查完成，发现 ${issuesFound} 个问题`);
  }

  /**
   * 尝试修复被修改的文件
   */
  attemptFileRepair(fileInfo) {
    try {
      this.log('info', `尝试修复文件: ${fileInfo.path}`);
      
      // 这里可以实现从备份恢复文件的逻辑
      const backupDir = this.config.backupPolicy?.localPath;
      if (backupDir && fs.existsSync(backupDir)) {
        // 查找最近的备份
        const backupFiles = fs.readdirSync(backupDir)
          .filter(f => f.includes(path.basename(fileInfo.path)))
          .sort()
          .reverse();
        
        if (backupFiles.length > 0) {
          const latestBackup = path.join(backupDir, backupFiles[0]);
          // 复制备份文件到原位置
          fs.copyFileSync(latestBackup, fileInfo.path);
          this.log('info', `成功从备份恢复文件: ${fileInfo.path}`);
          
          // 更新哈希值
          const newHash = this.calculateFileHash(fileInfo.path);
          fileInfo.hash = newHash;
          fileInfo.lastModified = fs.statSync(fileInfo.path).mtime;
          return;
        }
      }
      
      // 如果没有备份，记录警告
      this.log('warning', `没有找到文件 ${fileInfo.path} 的备份，无法自动修复`);
    } catch (error) {
      this.log('error', `修复文件 ${fileInfo.path} 失败: ${error.message}`);
    }
  }

  /**
   * 尝试恢复缺失的文件
   */
  attemptFileRecovery(filePath) {
    try {
      this.log('info', `尝试恢复缺失的文件: ${filePath}`);
      
      // 查找备份
      const backupDir = this.config.backupPolicy?.localPath;
      if (backupDir && fs.existsSync(backupDir)) {
        const backupFiles = fs.readdirSync(backupDir)
          .filter(f => f.includes(path.basename(filePath)))
          .sort()
          .reverse();
        
        if (backupFiles.length > 0) {
          const latestBackup = path.join(backupDir, backupFiles[0]);
          // 确保目标目录存在
          const dir = path.dirname(filePath);
          if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
          }
          
          // 复制备份文件
          fs.copyFileSync(latestBackup, filePath);
          this.log('info', `成功恢复缺失文件: ${filePath}`);
          return;
        }
      }
      
      // 如果是脚本文件，尝试重新创建基础版本
      if (filePath.endsWith('.js') || filePath.endsWith('.sh')) {
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        
        let content = '';
        if (filePath.endsWith('.js')) {
          content = '// 自动恢复的脚本文件\nconsole.log(\"This file was automatically recovered\");\n';
        } else if (filePath.endsWith('.sh')) {
          content = '#!/bin/bash\necho "This file was automatically recovered"\n';
        }
        
        fs.writeFileSync(filePath, content);
        
        // 如果是sh文件，设置执行权限
        if (filePath.endsWith('.sh')) {
          fs.chmodSync(filePath, '755');
        }
        
        this.log('info', `已创建基础版本的缺失文件: ${filePath}`);
      }
    } catch (error) {
      this.log('error', `恢复文件 ${filePath} 失败: ${error.message}`);
    }
  }

  /**
   * 检查进程状态
   */
  checkProcesses() {
    this.log('info', '开始进程状态检查');
    
    this.monitoredProcesses.forEach(processInfo => {
      try {
        // 使用ps命令检查进程是否存在
        let processExists = false;
        try {
          const output = execSync(`ps aux | grep ${processInfo.name} | grep -v grep`, { encoding: 'utf8' });
          processExists = output.length > 0;
        } catch (e) {
          processExists = false;
        }
        
        if (!processExists && processInfo.restartCommand) {
          this.log('warning', `进程 ${processInfo.name} 未运行，尝试重启`);
          this.restartProcess(processInfo);
        } else if (processExists) {
          this.log('info', `进程 ${processInfo.name} 运行正常`);
        }
      } catch (error) {
        this.log('error', `检查进程 ${processInfo.name} 时出错: ${error.message}`);
      }
    });
    
    this.log('info', '进程状态检查完成');
  }

  /**
   * 重启进程
   */
  restartProcess(processInfo) {
    try {
      this.log('info', `正在重启进程: ${processInfo.name}`);
      
      // 使用spawn启动进程，使其在后台运行
      const process = spawn(processInfo.restartCommand, { 
        detached: true,
        shell: true,
        stdio: 'ignore' 
      });
      
      // 分离进程，使其独立运行
      process.unref();
      
      this.log('info', `进程 ${processInfo.name} 已启动`);
    } catch (error) {
      this.log('error', `重启进程 ${processInfo.name} 失败: ${error.message}`);
    }
  }

  /**
   * 检查系统资源使用情况
   */
  checkResourceUsage() {
    this.log('info', '开始资源使用情况检查');
    
    // 获取CPU使用情况
    const cpus = os.cpus();
    const cpuCount = cpus.length;
    
    // 获取内存使用情况
    const memInfo = os.freemem();
    const totalMem = os.totalmem();
    const usedMemPercent = ((totalMem - memInfo) / totalMem * 100).toFixed(2);
    
    // 获取磁盘使用情况
    let diskInfo = null;
    try {
      const baseDir = this.config.basePath;
      diskInfo = fs.statSync(baseDir);
      // 在macOS上获取磁盘使用情况
      const dfOutput = execSync('df -h', { encoding: 'utf8' });
      // 简单解析输出
      const lines = dfOutput.split('\n');
      for (const line of lines) {
        if (line.includes('/dev/')) {
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5) {
            const usagePercent = parts[4].replace('%', '');
            this.log('info', `磁盘使用率: ${usagePercent}%`);
            
            // 检查是否超过警告阈值
            if (parseInt(usagePercent) > this.config.resourceLimits?.disk?.warningThreshold || 70) {
              this.log('warning', '磁盘使用率超过警告阈值');
            }
          }
        }
      }
    } catch (error) {
      this.log('warning', `获取磁盘信息失败: ${error.message}`);
    }
    
    this.log('info', `内存使用率: ${usedMemPercent}%`);
    this.log('info', `CPU核心数: ${cpuCount}`);
    
    // 检查内存使用是否超过警告阈值
    if (parseFloat(usedMemPercent) > this.config.resourceLimits?.memory?.warningThreshold || 90) {
      this.log('warning', '内存使用率超过警告阈值');
      this.attemptMemoryCleanup();
    }
    
    this.log('info', '资源使用情况检查完成');
  }

  /**
   * 尝试清理内存
   */
  attemptMemoryCleanup() {
    try {
      this.log('info', '尝试清理系统内存');
      
      // 在不同系统上尝试清理内存
      if (os.platform() === 'linux') {
        execSync('sync && echo 3 > /proc/sys/vm/drop_caches', { stdio: 'ignore' });
      } else if (os.platform() === 'darwin') {
        // macOS上可以尝试清理文件系统缓存
        execSync('sudo purge', { stdio: 'ignore' });
      }
      
      this.log('info', '内存清理尝试完成');
    } catch (error) {
      this.log('warning', `内存清理失败: ${error.message}`);
    }
  }

  /**
   * 检查系统健康状态
   */
  checkSystemHealth() {
    this.log('info', '开始系统健康状态检查');
    
    const healthStatus = {
      timestamp: new Date().toISOString(),
      status: 'healthy',
      issues: []
    };
    
    // 检查配置文件是否可访问
    if (!fs.existsSync(this.configPath)) {
      healthStatus.status = 'critical';
      healthStatus.issues.push('配置文件不可访问');
    }
    
    // 检查必要目录是否存在
    const requiredDirs = [
      this.config.directories?.scripts,
      this.config.directories?.logs,
      this.config.directories?.backups
    ].filter(Boolean);
    
    requiredDirs.forEach(dir => {
      if (!fs.existsSync(dir)) {
        healthStatus.status = 'degraded';
        healthStatus.issues.push(`必要目录不存在: ${dir}`);
        
        // 尝试创建缺失的目录
        try {
          fs.mkdirSync(dir, { recursive: true });
          this.log('info', `已创建缺失的目录: ${dir}`);
        } catch (error) {
          this.log('error', `创建目录 ${dir} 失败: ${error.message}`);
        }
      }
    });
    
    // 检查临时目录大小
    const tempDir = this.config.directories?.temp;
    if (tempDir && fs.existsSync(tempDir)) {
      try {
        const tempSize = this.getDirectorySize(tempDir);
        const maxTempSize = (this.config.limits?.maxFileSizeMB || 500) * 1024 * 1024; // 默认500MB
        
        if (tempSize > maxTempSize) {
          healthStatus.status = 'warning';
          healthStatus.issues.push('临时目录过大');
          this.cleanupTempDirectory(tempDir);
        }
      } catch (error) {
        this.log('warning', `检查临时目录失败: ${error.message}`);
      }
    }
    
    this.healthCheckResults.push(healthStatus);
    
    // 只保留最近100条记录
    if (this.healthCheckResults.length > 100) {
      this.healthCheckResults.shift();
    }
    
    this.log('info', `系统健康状态: ${healthStatus.status}`);
    if (healthStatus.issues.length > 0) {
      this.log('info', `发现问题: ${healthStatus.issues.join(', ')}`);
    }
    
    this.log('info', '系统健康状态检查完成');
  }

  /**
   * 获取目录大小
   */
  getDirectorySize(dirPath) {
    let totalSize = 0;
    
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        totalSize += this.getDirectorySize(filePath);
      } else {
        totalSize += stat.size;
      }
    }
    
    return totalSize;
  }

  /**
   * 清理临时目录
   */
  cleanupTempDirectory(tempDir) {
    try {
      this.log('info', `正在清理临时目录: ${tempDir}`);
      
      const files = fs.readdirSync(tempDir);
      const now = new Date();
      const oneDayAgo = now.getTime() - (24 * 60 * 60 * 1000);
      
      files.forEach(file => {
        const filePath = path.join(tempDir, file);
        const stat = fs.statSync(filePath);
        
        // 删除一天前的文件
        if (stat.mtime.getTime() < oneDayAgo) {
          if (stat.isDirectory()) {
            fs.rmdirSync(filePath, { recursive: true });
          } else {
            fs.unlinkSync(filePath);
          }
        }
      });
      
      this.log('info', '临时目录清理完成');
    } catch (error) {
      this.log('error', `清理临时目录失败: ${error.message}`);
    }
  }

  /**
   * 检查文件权限
   */
  checkPermissions() {
    this.log('info', '开始文件权限检查');
    
    // 检查关键脚本文件是否有执行权限
    const scriptFiles = [
      this.config.scripts?.setup,
      this.config.scripts?.start,
      this.config.scripts?.stop
    ].filter(Boolean);
    
    scriptFiles.forEach(scriptPath => {
      if (fs.existsSync(scriptPath) && scriptPath.endsWith('.sh')) {
        try {
          const stat = fs.statSync(scriptPath);
          // 检查是否有执行权限
          if (!(stat.mode & fs.constants.S_IXUSR)) {
            this.log('warning', `脚本文件 ${scriptPath} 缺少执行权限`);
            // 添加执行权限
            fs.chmodSync(scriptPath, '755');
            this.log('info', `已为脚本 ${scriptPath} 添加执行权限`);
          }
        } catch (error) {
          this.log('error', `检查脚本权限失败: ${error.message}`);
        }
      }
    });
    
    this.log('info', '文件权限检查完成');
  }

  /**
   * 检查网络连接
   */
  checkNetworkConnectivity() {
    this.log('info', '开始网络连接检查');
    
    // 检查本地服务是否正常运行
    const webPort = this.config.network?.ports?.web || 8001;
    const apiPort = this.config.network?.ports?.api || 8081;
    
    const portsToCheck = [webPort, apiPort];
    
    portsToCheck.forEach(port => {
      this.checkPortAvailability(port, (available) => {
        if (!available) {
          this.log('warning', `端口 ${port} 不可用，可能服务未启动`);
          // 这里可以添加自动启动服务的逻辑
        } else {
          this.log('info', `端口 ${port} 可用`);
        }
      });
    });
    
    this.log('info', '网络连接检查完成');
  }

  /**
   * 检查端口是否可用
   */
  checkPortAvailability(port, callback) {
    const server = http.createServer();
    
    server.listen(port, 'localhost', () => {
      server.close();
      callback(true);
    });
    
    server.on('error', () => {
      callback(false);
    });
  }

  /**
   * 保存健康检查结果
   */
  saveHealthCheckResults() {
    try {
      const resultsPath = path.join(this.config.directories?.logs || path.join(this.config.basePath, 'Logs'), 'health-checks.json');
      fs.writeFileSync(resultsPath, JSON.stringify(this.healthCheckResults, null, 2));
      this.log('info', `健康检查结果已保存到: ${resultsPath}`);
    } catch (error) {
      this.log('error', `保存健康检查结果失败: ${error.message}`);
    }
  }

  /**
   * 记录错误
   */
  recordError(error) {
    const errorRecord = {
      timestamp: new Date().toISOString(),
      message: error.message,
      stack: error.stack,
      type: error.name || 'UnknownError'
    };
    
    this.errorHistory.push(errorRecord);
    
    // 只保留最近50条错误记录
    if (this.errorHistory.length > 50) {
      this.errorHistory.shift();
    }
    
    this.log('error', error.message);
  }

  /**
   * 生成系统状态报告
   */
  generateSystemReport() {
    const report = {
      timestamp: new Date().toISOString(),
      systemInfo: {
        platform: os.platform(),
        arch: os.arch(),
        release: os.release(),
        uptime: os.uptime(),
        hostname: os.hostname()
      },
      resourceUsage: {
        cpu: os.cpus(),
        memory: {
          total: os.totalmem(),
          free: os.freemem(),
          usagePercent: ((os.totalmem() - os.freemem()) / os.totalmem() * 100).toFixed(2)
        }
      },
      healthStatus: this.healthCheckResults[this.healthCheckResults.length - 1] || { status: 'unknown' },
      recentErrors: this.errorHistory.slice(-10),
      monitoredProcesses: this.monitoredProcesses.map(p => ({
        name: p.name,
        status: 'unknown' // 这里应该检查实际状态
      }))
    };
    
    // 保存报告到文件
    try {
      const reportPath = path.join(this.config.directories?.logs || path.join(this.config.basePath, 'Logs'), `system-report-${Date.now()}.json`);
      fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
      this.log('info', `系统状态报告已生成: ${reportPath}`);
    } catch (error) {
      this.log('error', `生成系统状态报告失败: ${error.message}`);
    }
    
    return report;
  }

  /**
   * 智能修复模式 - 分析并尝试修复所有检测到的问题
   */
  async runIntelligentRepair() {
    this.log('info', '开始智能修复模式');
    
    try {
      // 先执行完整检查以发现所有问题
      await this.performFullSystemCheck();
      
      // 执行特定修复任务
      await this.repairConfigurationIssues();
      await this.optimizeSystemPerformance();
      await this.cleanupUnusedResources();
      
      this.log('info', '智能修复模式完成');
      return true;
    } catch (error) {
      this.log('error', `智能修复失败: ${error.message}`);
      return false;
    }
  }

  /**
   * 修复配置问题
   */
  async repairConfigurationIssues() {
    this.log('info', '开始修复配置问题');
    // 这里可以实现更复杂的配置修复逻辑
  }

  /**
   * 优化系统性能
   */
  async optimizeSystemPerformance() {
    this.log('info', '开始优化系统性能');
    // 清理临时文件
    if (this.config.directories?.temp) {
      this.cleanupTempDirectory(this.config.directories.temp);
    }
    
    // 优化文件系统缓存
    this.attemptMemoryCleanup();
  }

  /**
   * 清理未使用的资源
   */
  async cleanupUnusedResources() {
    this.log('info', '开始清理未使用的资源');
    // 这里可以实现清理未使用资源的逻辑
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  // 创建并启动引擎
  const engine = new AutoDetectionRepairEngine(configPath);
  
  // 处理命令行参数
  const args = process.argv.slice(2);
  const command = args[0] || 'start';
  
  switch (command) {
    case 'start':
      engine.start();
      break;
    case 'stop':
      engine.stop();
      break;
    case 'check':
      engine.performFullSystemCheck();
      break;
    case 'repair':
      engine.runIntelligentRepair();
      break;
    case 'report':
      engine.generateSystemReport();
      break;
    default:
      console.log('用法: node auto-detection-repair.js [start|stop|check|repair|report]');
      break;
  }
}

module.exports = AutoDetectionRepairEngine;
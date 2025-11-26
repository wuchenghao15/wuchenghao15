#!/usr/bin/env node

/**
 * MTSCOS AI 自动修复引擎
 * 专注于系统错误和异常的自动检测与修复功能
 */

const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const os = require('os');

class AutoRepairEngine {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.isRunning = false;
    this.repairInterval = null;
    this.repairLog = [];
    this.repairRules = {};
    this.failedRepairs = new Map();
    this.maxRetries = 3;
    this.cooldownPeriod = 30000; // 30秒冷却期，避免重复修复
    
    // 初始化引擎
    this.initialize();
  }

  /**
   * 初始化自动修复引擎
   */
  initialize() {
    try {
      // 加载配置文件
      this.config = this.loadConfig();
      
      // 初始化修复规则
      this.initializeRepairRules();
      
      // 设置日志目录
      this.logDir = this.config.logConfig?.path || path.join(this.config.basePath, 'Logs');
      this.ensureLogDirExists();
      
      // 初始化修复日志
      this.initializeRepairLog();
      
      console.log('MTSCOS AI 自动修复引擎初始化完成');
      
    } catch (error) {
      console.error('初始化自动修复引擎失败:', error.message);
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
   * 初始化修复规则
   */
  initializeRepairRules() {
    // 文件完整性修复规则
    this.repairRules.fileIntegrity = {
      detect: this.detectFileIntegrityIssues.bind(this),
      repair: this.repairFileIntegrity.bind(this),
      priority: 'high'
    };
    
    // 进程修复规则
    this.repairRules.process = {
      detect: this.detectProcessIssues.bind(this),
      repair: this.repairProcessIssues.bind(this),
      priority: 'critical'
    };
    
    // 资源使用率修复规则
    this.repairRules.resource = {
      detect: this.detectResourceIssues.bind(this),
      repair: this.repairResourceIssues.bind(this),
      priority: 'medium'
    };
    
    // 网络连接修复规则
    this.repairRules.network = {
      detect: this.detectNetworkIssues.bind(this),
      repair: this.repairNetworkIssues.bind(this),
      priority: 'medium'
    };
    
    // 依赖项修复规则
    this.repairRules.dependency = {
      detect: this.detectDependencyIssues.bind(this),
      repair: this.repairDependencyIssues.bind(this),
      priority: 'high'
    };
    
    // 日志文件修复规则
    this.repairRules.log = {
      detect: this.detectLogIssues.bind(this),
      repair: this.repairLogIssues.bind(this),
      priority: 'low'
    };
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
   * 初始化修复日志
   */
  initializeRepairLog() {
    this.repairLog = [];
    // 加载之前的修复日志（如果存在）
    try {
      const logFilePath = path.join(this.logDir, 'repair-history.log');
      if (fs.existsSync(logFilePath)) {
        const logContent = fs.readFileSync(logFilePath, 'utf8');
        this.repairLog = logContent.split('\n')
          .filter(line => line.trim())
          .map(line => JSON.parse(line))
          .slice(-100); // 只保留最近100条记录
      }
    } catch (error) {
      console.error('加载修复日志失败:', error.message);
    }
  }

  /**
   * 启动自动修复引擎
   */
  start() {
    if (this.isRunning) {
      console.log('自动修复引擎已经在运行中');
      return;
    }

    this.isRunning = true;
    console.log('自动修复引擎已启动');
    
    // 立即执行一次修复检查
    this.runRepairCycle();
    
    // 设置修复检查间隔（默认每60秒检查一次）
    const checkInterval = this.config.maintenance?.repairCheckInterval || 60000;
    this.repairInterval = setInterval(() => {
      this.runRepairCycle();
    }, checkInterval);
    
    console.log(`修复检查间隔设置为: ${checkInterval / 1000}秒`);
  }

  /**
   * 运行修复周期
   */
  runRepairCycle() {
    if (!this.isRunning) return;
    
    console.log(`\n--- 开始修复周期 (${new Date().toISOString()}) ---`);
    
    // 按优先级排序修复规则
    const priorityOrder = ['critical', 'high', 'medium', 'low'];
    const sortedRules = Object.entries(this.repairRules).sort((a, b) => {
      return priorityOrder.indexOf(a[1].priority) - priorityOrder.indexOf(b[1].priority);
    });
    
    // 执行每个修复规则
    sortedRules.forEach(([ruleName, rule]) => {
      try {
        // 检测问题
        const issues = rule.detect();
        
        if (issues && issues.length > 0) {
          console.log(`检测到 ${ruleName} 问题: ${issues.length} 个`);
          
          // 修复问题
          const repairResult = rule.repair(issues);
          
          // 记录修复结果
          this.logRepairResult(ruleName, issues, repairResult);
          
        } else {
          console.log(`未检测到 ${ruleName} 问题`);
        }
        
      } catch (error) {
        console.error(`执行 ${ruleName} 修复规则失败:`, error.message);
        this.logError(`执行修复规则 ${ruleName} 失败`, error);
      }
    });
    
    console.log(`--- 修复周期结束 (${new Date().toISOString()}) ---\n`);
  }

  /**
   * 检测文件完整性问题
   */
  detectFileIntegrityIssues() {
    const issues = [];
    const criticalFiles = [
      path.join(this.config.basePath, 'Staging/Scripts/monitoring/environment-monitor.js'),
      path.join(this.config.basePath, 'Staging/Scripts/maintenance/environment-maintenance.js'),
      path.join(this.config.basePath, 'Staging/Scripts/monitoring/auto-detection-repair.js'),
      path.join(this.config.basePath, 'Staging/Scripts/start-auto-services.sh'),
      path.join(this.config.basePath, 'config/staging-environment.json')
    ];
    
    criticalFiles.forEach(filePath => {
      try {
        // 检查文件是否存在
        if (!fs.existsSync(filePath)) {
          issues.push({
            type: 'file_missing',
            filePath: filePath,
            severity: 'critical',
            description: `关键文件缺失: ${filePath}`
          });
          return;
        }
        
        // 检查文件权限
        const stats = fs.statSync(filePath);
        const isExecutable = stats.mode & 0o111;
        
        // 如果是脚本文件，检查执行权限
        if (filePath.endsWith('.js') || filePath.endsWith('.sh')) {
          if (!isExecutable) {
            issues.push({
              type: 'file_permission',
              filePath: filePath,
              severity: 'high',
              description: `文件缺少执行权限: ${filePath}`,
              currentPermissions: stats.mode.toString(8)
            });
          }
        }
        
        // 检查文件大小是否异常
        const fileSize = stats.size;
        if (fileSize === 0) {
          issues.push({
            type: 'file_empty',
            filePath: filePath,
            severity: 'high',
            description: `空文件: ${filePath}`
          });
        }
        
      } catch (error) {
        issues.push({
          type: 'file_access_error',
          filePath: filePath,
          severity: 'high',
          description: `访问文件失败: ${filePath}`,
          error: error.message
        });
      }
    });
    
    return issues;
  }

  /**
   * 修复文件完整性问题
   */
  repairFileIntegrity(issues) {
    const results = {
      total: issues.length,
      fixed: 0,
      failed: 0,
      details: []
    };
    
    issues.forEach(issue => {
      try {
        // 检查是否在冷却期
        const issueKey = `${issue.type}:${issue.filePath}`;
        if (this.isInCooldown(issueKey)) {
          results.details.push({
            issue: issue,
            status: 'cooldown',
            message: '修复请求已在冷却期内，跳过本次修复'
          });
          results.failed++;
          return;
        }
        
        let result;
        
        switch (issue.type) {
          case 'file_missing':
            result = this.restoreMissingFile(issue.filePath);
            break;
            
          case 'file_permission':
            result = this.fixFilePermissions(issue.filePath);
            break;
            
          case 'file_empty':
            result = this.restoreEmptyFile(issue.filePath);
            break;
            
          default:
            result = {
              success: false,
              message: `不支持的问题类型: ${issue.type}`
            };
        }
        
        if (result.success) {
          results.fixed++;
          this.markLastRepair(issueKey);
        } else {
          results.failed++;
          this.recordFailedRepair(issueKey);
        }
        
        results.details.push({
          issue: issue,
          status: result.success ? 'fixed' : 'failed',
          message: result.message
        });
        
      } catch (error) {
        results.details.push({
          issue: issue,
          status: 'error',
          message: `修复过程中发生错误: ${error.message}`
        });
        results.failed++;
      }
    });
    
    return results;
  }

  /**
   * 恢复缺失的文件
   */
  restoreMissingFile(filePath) {
    try {
      // 创建文件目录（如果不存在）
      const dirPath = path.dirname(filePath);
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
      }
      
      // 根据文件类型创建基础内容
      let content = '';
      
      if (filePath.endsWith('staging-environment.json')) {
        content = this.createDefaultEnvironmentConfig();
      } else if (filePath.endsWith('.js')) {
        content = this.createDefaultJsScript(filePath);
      } else if (filePath.endsWith('.sh')) {
        content = this.createDefaultShScript(filePath);
      }
      
      // 写入文件
      fs.writeFileSync(filePath, content, 'utf8');
      
      // 设置执行权限
      if (filePath.endsWith('.js') || filePath.endsWith('.sh')) {
        fs.chmodSync(filePath, 0o755);
      }
      
      return {
        success: true,
        message: `已成功创建缺失文件: ${filePath}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `创建缺失文件失败: ${error.message}`
      };
    }
  }

  /**
   * 修复文件权限
   */
  fixFilePermissions(filePath) {
    try {
      fs.chmodSync(filePath, 0o755);
      return {
        success: true,
        message: `已修复文件权限: ${filePath}`
      };
    } catch (error) {
      return {
        success: false,
        message: `修复文件权限失败: ${error.message}`
      };
    }
  }

  /**
   * 恢复空文件
   */
  restoreEmptyFile(filePath) {
    try {
      // 备份原文件（如果需要）
      const backupPath = filePath + '.bak';
      if (fs.existsSync(filePath)) {
        fs.renameSync(filePath, backupPath);
      }
      
      // 根据文件类型创建基础内容
      let content = '';
      
      if (filePath.endsWith('staging-environment.json')) {
        content = this.createDefaultEnvironmentConfig();
      } else if (filePath.endsWith('.js')) {
        content = this.createDefaultJsScript(filePath);
      } else if (filePath.endsWith('.sh')) {
        content = this.createDefaultShScript(filePath);
      }
      
      // 写入文件
      fs.writeFileSync(filePath, content, 'utf8');
      
      return {
        success: true,
        message: `已恢复空文件: ${filePath}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `恢复空文件失败: ${error.message}`
      };
    }
  }

  /**
   * 创建默认环境配置文件
   */
  createDefaultEnvironmentConfig() {
    return JSON.stringify({
      stagingEnvironment: {
        name: "MTSCOS AI 灰度测试环境",
        description: "用于系统测试、升级和维护的灰度环境",
        version: "1.0.0",
        createdAt: new Date().toISOString(),
        basePath: this.config?.basePath || "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project",
        environmentType: "staging",
        securityLevel: "medium",
        maintenance: {
          cleaning: {
            enabled: true,
            frequency: "daily",
            fileTypes: [".log", ".tmp", ".bak"],
            maxFileAge: 30
          },
          backup: {
            enabled: true,
            frequency: "daily",
            retention: 7,
            github: {
              enabled: true,
              repository: "mtscos-ai-project",
              branch: "backup"
            }
          },
          systemChecks: {
            enabled: true,
            frequency: "hourly",
            components: ["filesystem", "memory", "processes", "network"]
          }
        },
        resourceLimits: {
          memory: {
            warningThreshold: 80,
            limit: 90
          },
          disk: {
            warningThreshold: 70,
            limit: 80
          },
          cpu: {
            warningThreshold: 85,
            limit: 95
          }
        },
        network: {
          ports: {
            statusPanel: 8085,
            monitoring: 8086,
            api: 8087
          }
        }
      }
    }, null, 2);
  }

  /**
   * 创建默认JavaScript脚本
   */
  createDefaultJsScript(filePath) {
    const fileName = path.basename(filePath);
    const moduleName = fileName.replace(/\.[^/.]+$/, '');
    
    return `#!/usr/bin/env node

/**
 * ${moduleName}
 * MTSCOS AI 系统组件
 */

const fs = require('fs');
const path = require('path');

class ${this.capitalizeFirstLetter(moduleName)} {
  constructor() {
    console.log('${moduleName} 模块初始化');
  }
  
  initialize() {
    console.log('${moduleName} 模块初始化完成');
  }
  
  start() {
    console.log('${moduleName} 模块已启动');
  }
  
  stop() {
    console.log('${moduleName} 模块已停止');
  }
}

function ${this.capitalizeFirstLetter(moduleName)}() {
  return {
    initialize: () => console.log('${moduleName} 函数初始化'),
    execute: () => console.log('${moduleName} 函数执行')
  };
}

// 主程序入口
if (require.main === module) {
  const instance = new ${this.capitalizeFirstLetter(moduleName)}();
  instance.initialize();
  instance.start();
}

module.exports = ${this.capitalizeFirstLetter(moduleName)};
`;
  }

  /**
   * 创建默认Shell脚本
   */
  createDefaultShScript(filePath) {
    const fileName = path.basename(filePath);
    
    return `#!/bin/bash

# ${fileName}
# MTSCOS AI 系统组件启动脚本

echo "Starting ${fileName}..."

# 设置错误时退出
set -e

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "${SCRIPT_DIR}")")"

# 日志函数
log_info() {
  echo -e "[${GREEN}INFO${NC}] $1"
}

log_warn() {
  echo -e "[${YELLOW}WARN${NC}] $1"
}

log_error() {
  echo -e "[${RED}ERROR${NC}] $1"
}

# 主函数
main() {
  log_info "Starting ${fileName} from ${SCRIPT_DIR}"
  log_info "Project root: ${PROJECT_ROOT}"
  
  # 检查环境
  check_environment
  
  # 执行主要功能
  execute_main_function
  
  log_info "${fileName} execution completed successfully"
}

# 检查环境
check_environment() {
  log_info "Checking environment..."
  # 环境检查代码
}

# 执行主要功能
execute_main_function() {
  log_info "Executing main function..."
  # 主要功能代码
}

# 执行主函数
main "$@"
`;
  }

  /**
   * 首字母大写
   */
  capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  /**
   * 检测进程问题
   */
  detectProcessIssues() {
    const issues = [];
    const criticalServices = [
      { name: 'environment-monitor', script: 'environment-monitor.js' },
      { name: 'auto-detection-repair', script: 'auto-detection-repair.js' },
      { name: 'environment-maintenance', script: 'environment-maintenance.js' },
      { name: 'system-status-panel', script: 'system-status-panel.js' }
    ];
    
    criticalServices.forEach(service => {
      try {
        // 检查进程是否正在运行
        const output = execSync(`ps aux | grep ${service.script} | grep -v grep`, { encoding: 'utf8' });
        const isRunning = output.length > 0;
        
        if (!isRunning) {
          issues.push({
            type: 'process_not_running',
            service: service.name,
            script: service.script,
            severity: 'critical',
            description: `关键服务未运行: ${service.name}`
          });
        }
        
      } catch (error) {
        // 命令执行失败，假设服务未运行
        issues.push({
          type: 'process_not_running',
          service: service.name,
          script: service.script,
          severity: 'critical',
          description: `关键服务未运行: ${service.name}`
        });
      }
    });
    
    // 检查是否有僵尸进程
    try {
      const zombieOutput = execSync('ps aux | grep "defunct" | grep -v grep', { encoding: 'utf8' });
      if (zombieOutput.length > 0) {
        const zombieCount = zombieOutput.trim().split('\n').length;
        issues.push({
          type: 'zombie_processes',
          count: zombieCount,
          severity: 'medium',
          description: `检测到 ${zombieCount} 个僵尸进程`
        });
      }
    } catch (error) {
      // 忽略错误，可能是ps命令输出格式问题
    }
    
    return issues;
  }

  /**
   * 修复进程问题
   */
  repairProcessIssues(issues) {
    const results = {
      total: issues.length,
      fixed: 0,
      failed: 0,
      details: []
    };
    
    issues.forEach(issue => {
      try {
        // 检查是否在冷却期
        const issueKey = `${issue.type}:${issue.service || issue.count}`;
        if (this.isInCooldown(issueKey)) {
          results.details.push({
            issue: issue,
            status: 'cooldown',
            message: '修复请求已在冷却期内，跳过本次修复'
          });
          results.failed++;
          return;
        }
        
        let result;
        
        if (issue.type === 'process_not_running') {
          result = this.restartService(issue.service, issue.script);
        } else if (issue.type === 'zombie_processes') {
          result = this.cleanupZombieProcesses();
        } else {
          result = {
            success: false,
            message: `不支持的问题类型: ${issue.type}`
          };
        }
        
        if (result.success) {
          results.fixed++;
          this.markLastRepair(issueKey);
        } else {
          results.failed++;
          this.recordFailedRepair(issueKey);
        }
        
        results.details.push({
          issue: issue,
          status: result.success ? 'fixed' : 'failed',
          message: result.message
        });
        
      } catch (error) {
        results.details.push({
          issue: issue,
          status: 'error',
          message: `修复过程中发生错误: ${error.message}`
        });
        results.failed++;
      }
    });
    
    return results;
  }

  /**
   * 重启服务
   */
  restartService(serviceName, scriptName) {
    try {
      const scriptPath = path.join(
        this.config.basePath,
        'Staging/Scripts/monitoring',
        scriptName
      );
      
      // 检查脚本是否存在
      if (!fs.existsSync(scriptPath)) {
        return {
          success: false,
          message: `服务脚本不存在: ${scriptPath}`
        };
      }
      
      // 停止可能正在运行的进程
      try {
        execSync(`pkill -f ${scriptName}`, { stdio: 'ignore' });
      } catch (error) {
        // 忽略停止失败
      }
      
      // 启动服务（异步执行）
      const command = `nohup node ${scriptPath} > /dev/null 2>&1 &`;
      execSync(command);
      
      // 等待几秒让服务启动
      setTimeout(() => {}, 3000);
      
      // 验证服务是否成功启动
      const psOutput = execSync(`ps aux | grep ${scriptName} | grep -v grep`, { encoding: 'utf8' });
      if (psOutput.length > 0) {
        return {
          success: true,
          message: `成功重启服务: ${serviceName}`
        };
      } else {
        return {
          success: false,
          message: `服务启动失败，无法验证进程是否运行: ${serviceName}`
        };
      }
      
    } catch (error) {
      return {
        success: false,
        message: `重启服务失败: ${error.message}`
      };
    }
  }

  /**
   * 清理僵尸进程
   */
  cleanupZombieProcesses() {
    try {
      // 获取僵尸进程的父进程ID
      const zombieOutput = execSync('ps -eo pid,ppid,stat | grep Z', { encoding: 'utf8' });
      const zombieLines = zombieOutput.trim().split('\n');
      
      let cleanedCount = 0;
      
      zombieLines.forEach(line => {
        const parts = line.trim().split(/\s+/);
        const parentPid = parts[1];
        
        try {
          // 向父进程发送SIGCHLD信号，让它回收僵尸进程
          process.kill(parseInt(parentPid), 'SIGCHLD');
          cleanedCount++;
        } catch (error) {
          // 忽略错误
        }
      });
      
      return {
        success: true,
        message: `已尝试清理 ${cleanedCount} 个僵尸进程`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `清理僵尸进程失败: ${error.message}`
      };
    }
  }

  /**
   * 检测资源使用问题
   */
  detectResourceIssues() {
    const issues = [];
    
    // 检测内存使用
    try {
      const freeOutput = execSync('free -m', { encoding: 'utf8' });
      const lines = freeOutput.trim().split('\n');
      
      if (lines.length >= 2) {
        const memLine = lines[1];
        const memData = memLine.split(/\s+/);
        const totalMem = parseInt(memData[1]);
        const usedMem = parseInt(memData[2]);
        const memUsagePercent = (usedMem / totalMem * 100).toFixed(2);
        
        if (parseFloat(memUsagePercent) > (this.config.resourceLimits?.memory?.limit || 90)) {
          issues.push({
            type: 'memory_usage_critical',
            usagePercent: parseFloat(memUsagePercent),
            used: usedMem,
            total: totalMem,
            severity: 'critical',
            description: `内存使用率严重超标: ${memUsagePercent}%`
          });
        } else if (parseFloat(memUsagePercent) > (this.config.resourceLimits?.memory?.warningThreshold || 80)) {
          issues.push({
            type: 'memory_usage_high',
            usagePercent: parseFloat(memUsagePercent),
            used: usedMem,
            total: totalMem,
            severity: 'warning',
            description: `内存使用率过高: ${memUsagePercent}%`
          });
        }
      }
    } catch (error) {
      // 在macOS上使用vm_stat命令
      if (os.platform() === 'darwin') {
        try {
          const vmStatOutput = execSync('vm_stat', { encoding: 'utf8' });
          // 简化的内存使用检测
          issues.push({
            type: 'resource_check_failed',
            resource: 'memory',
            severity: 'low',
            description: '内存使用检测失败，需要手动检查'
          });
        } catch (error) {
          // 忽略错误
        }
      }
    }
    
    // 检测磁盘使用
    try {
      const dfOutput = execSync(`df -h "${this.config.basePath}"`, { encoding: 'utf8' });
      const lines = dfOutput.trim().split('\n');
      
      if (lines.length >= 2) {
        const dataLine = lines[1];
        const data = dataLine.split(/\s+/);
        const usagePercent = parseInt(data[data.length - 2].replace('%', ''));
        
        if (usagePercent > (this.config.resourceLimits?.disk?.limit || 80)) {
          issues.push({
            type: 'disk_usage_critical',
            usagePercent: usagePercent,
            mountPoint: data[data.length - 1],
            severity: 'critical',
            description: `磁盘使用率严重超标: ${usagePercent}%`
          });
        } else if (usagePercent > (this.config.resourceLimits?.disk?.warningThreshold || 70)) {
          issues.push({
            type: 'disk_usage_high',
            usagePercent: usagePercent,
            mountPoint: data[data.length - 1],
            severity: 'warning',
            description: `磁盘使用率过高: ${usagePercent}%`
          });
        }
      }
    } catch (error) {
      console.error('磁盘使用检测失败:', error.message);
    }
    
    return issues;
  }

  /**
   * 修复资源使用问题
   */
  repairResourceIssues(issues) {
    const results = {
      total: issues.length,
      fixed: 0,
      failed: 0,
      details: []
    };
    
    issues.forEach(issue => {
      try {
        // 检查是否在冷却期
        const issueKey = `${issue.type}`;
        if (this.isInCooldown(issueKey)) {
          results.details.push({
            issue: issue,
            status: 'cooldown',
            message: '修复请求已在冷却期内，跳过本次修复'
          });
          results.failed++;
          return;
        }
        
        let result;
        
        if (issue.type.includes('memory')) {
          result = this.freeMemory();
        } else if (issue.type.includes('disk')) {
          result = this.cleanupDiskSpace();
        } else {
          result = {
            success: false,
            message: `不支持的问题类型: ${issue.type}`
          };
        }
        
        if (result.success) {
          results.fixed++;
          this.markLastRepair(issueKey);
        } else {
          results.failed++;
          this.recordFailedRepair(issueKey);
        }
        
        results.details.push({
          issue: issue,
          status: result.success ? 'fixed' : 'failed',
          message: result.message
        });
        
      } catch (error) {
        results.details.push({
          issue: issue,
          status: 'error',
          message: `修复过程中发生错误: ${error.message}`
        });
        results.failed++;
      }
    });
    
    return results;
  }

  /**
   * 释放内存
   */
  freeMemory() {
    try {
      // 尝试清除系统缓存
      if (os.platform() === 'linux') {
        // 在Linux上，我们可以尝试清理页面缓存等
        // 注意：这需要root权限，可能会失败
        try {
          execSync('sync && echo 3 > /proc/sys/vm/drop_caches', { stdio: 'ignore' });
        } catch (error) {
          // 如果没有权限，尝试其他方法
        }
      }
      
      // 清理Node.js进程缓存
      if (global.gc) {
        global.gc();
      }
      
      // 找出并终止占用内存过高的进程
      try {
        const topOutput = execSync('ps aux --sort=-%mem | head -n 10', { encoding: 'utf8' });
        console.log('内存使用排名前10的进程:\n', topOutput);
        
        // 这里可以添加逻辑来终止可疑的高内存进程
        // 但为了安全，默认不执行终止操作
      } catch (error) {
        console.error('获取进程内存使用失败:', error.message);
      }
      
      return {
        success: true,
        message: '已尝试释放内存'
      };
      
    } catch (error) {
      return {
        success: false,
        message: `释放内存失败: ${error.message}`
      };
    }
  }

  /**
   * 清理磁盘空间
   */
  cleanupDiskSpace() {
    try {
      const tempDirs = [
        '/tmp',
        '/var/tmp',
        path.join(os.tmpdir(), 'MTSCOS_AI'),
        path.join(this.config.basePath, 'Logs')
      ];
      
      let cleanedBytes = 0;
      
      tempDirs.forEach(dir => {
        try {
          if (fs.existsSync(dir)) {
            // 删除旧文件（7天前）
            const oldFiles = this.findOldFiles(dir, 7);
            oldFiles.forEach(file => {
              try {
                const stats = fs.statSync(file);
                fs.unlinkSync(file);
                cleanedBytes += stats.size;
              } catch (error) {
                // 忽略删除失败的文件
              }
            });
          }
        } catch (error) {
          console.error(`清理目录失败: ${dir}`, error.message);
        }
      });
      
      return {
        success: true,
        message: `已清理约 ${this.formatBytes(cleanedBytes)} 磁盘空间`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `清理磁盘空间失败: ${error.message}`
      };
    }
  }

  /**
   * 查找旧文件
   */
  findOldFiles(dir, days) {
    const oldFiles = [];
    const now = new Date().getTime();
    const daysInMs = days * 24 * 60 * 60 * 1000;
    
    try {
      const files = fs.readdirSync(dir);
      files.forEach(file => {
        const filePath = path.join(dir, file);
        try {
          const stats = fs.statSync(filePath);
          if (stats.isFile() && now - stats.mtime.getTime() > daysInMs) {
            oldFiles.push(filePath);
          }
        } catch (error) {
          // 忽略错误
        }
      });
    } catch (error) {
      console.error(`查找旧文件失败: ${dir}`, error.message);
    }
    
    return oldFiles;
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
   * 检测网络连接问题
   */
  detectNetworkIssues() {
    const issues = [];
    const testEndpoints = [
      { name: 'local_network', host: 'localhost' },
      { name: 'internet_connection', host: '8.8.8.8' },
      { name: 'github_access', host: 'github.com' }
    ];
    
    testEndpoints.forEach(endpoint => {
      try {
        // 简单的ping测试
        execSync(`ping -c 1 -W 2 ${endpoint.host}`, { stdio: 'ignore' });
      } catch (error) {
        issues.push({
          type: 'network_connection_failed',
          endpoint: endpoint.name,
          host: endpoint.host,
          severity: 'medium',
          description: `无法连接到 ${endpoint.name}: ${endpoint.host}`
        });
      }
    });
    
    // 检查服务端口是否正常监听
    const servicePorts = [
      { name: 'status_panel', port: this.config.network?.ports?.statusPanel || 8085 }
    ];
    
    servicePorts.forEach(service => {
      try {
        // 检查端口是否被占用
        execSync(`lsof -i:${service.port}`, { stdio: 'ignore' });
      } catch (error) {
        issues.push({
          type: 'port_not_listening',
          service: service.name,
          port: service.port,
          severity: 'high',
          description: `服务端口未监听: ${service.name} (${service.port})`
        });
      }
    });
    
    return issues;
  }

  /**
   * 修复网络连接问题
   */
  repairNetworkIssues(issues) {
    const results = {
      total: issues.length,
      fixed: 0,
      failed: 0,
      details: []
    };
    
    issues.forEach(issue => {
      try {
        // 检查是否在冷却期
        const issueKey = `${issue.type}:${issue.endpoint || issue.service}`;
        if (this.isInCooldown(issueKey)) {
          results.details.push({
            issue: issue,
            status: 'cooldown',
            message: '修复请求已在冷却期内，跳过本次修复'
          });
          results.failed++;
          return;
        }
        
        let result;
        
        if (issue.type === 'network_connection_failed') {
          result = this.resetNetworkConnection(issue.host);
        } else if (issue.type === 'port_not_listening') {
          result = this.restartServiceByPort(issue.service, issue.port);
        } else {
          result = {
            success: false,
            message: `不支持的问题类型: ${issue.type}`
          };
        }
        
        if (result.success) {
          results.fixed++;
          this.markLastRepair(issueKey);
        } else {
          results.failed++;
          this.recordFailedRepair(issueKey);
        }
        
        results.details.push({
          issue: issue,
          status: result.success ? 'fixed' : 'failed',
          message: result.message
        });
        
      } catch (error) {
        results.details.push({
          issue: issue,
          status: 'error',
          message: `修复过程中发生错误: ${error.message}`
        });
        results.failed++;
      }
    });
    
    return results;
  }

  /**
   * 重置网络连接
   */
  resetNetworkConnection(host) {
    try {
      // 尝试刷新DNS缓存
      if (os.platform() === 'darwin') {
        execSync('dscacheutil -flushcache; sudo killall -HUP mDNSResponder', { stdio: 'ignore' });
      } else if (os.platform() === 'linux') {
        execSync('systemctl restart NetworkManager', { stdio: 'ignore' });
      }
      
      // 再次测试连接
      try {
        execSync(`ping -c 1 -W 2 ${host}`, { stdio: 'ignore' });
        return {
          success: true,
          message: `网络连接已恢复: ${host}`
        };
      } catch (error) {
        return {
          success: false,
          message: `无法恢复网络连接: ${host}`
        };
      }
      
    } catch (error) {
      return {
        success: false,
        message: `重置网络连接失败: ${error.message}`
      };
    }
  }

  /**
   * 根据端口重启服务
   */
  restartServiceByPort(serviceName, port) {
    // 这里可以根据端口找到对应的服务并重启
    // 简化实现，直接调用通用重启函数
    const serviceMap = {
      status_panel: { name: 'system-status-panel', script: 'system-status-panel.js' }
    };
    
    const service = serviceMap[serviceName];
    if (service) {
      return this.restartService(service.name, service.script);
    }
    
    return {
      success: false,
      message: `未知的服务: ${serviceName}`
    };
  }

  /**
   * 检测依赖项问题
   */
  detectDependencyIssues() {
    const issues = [];
    const requiredNodeModules = ['fs', 'path', 'child_process', 'os', 'http'];
    
    // 检查Node.js模块
    requiredNodeModules.forEach(module => {
      try {
        require.resolve(module);
      } catch (error) {
        issues.push({
          type: 'missing_node_module',
          module: module,
          severity: 'high',
          description: `缺少必要的Node.js模块: ${module}`
        });
      }
    });
    
    // 检查必要的系统命令
    const requiredCommands = ['ps', 'df', 'free', 'ping', 'lsof'];
    
    requiredCommands.forEach(command => {
      try {
        execSync(`which ${command}`, { stdio: 'ignore' });
      } catch (error) {
        issues.push({
          type: 'missing_system_command',
          command: command,
          severity: 'medium',
          description: `缺少必要的系统命令: ${command}`
        });
      }
    });
    
    return issues;
  }

  /**
   * 修复依赖项问题
   */
  repairDependencyIssues(issues) {
    const results = {
      total: issues.length,
      fixed: 0,
      failed: 0,
      details: []
    };
    
    issues.forEach(issue => {
      try {
        // 检查是否在冷却期
        const issueKey = `${issue.type}:${issue.module || issue.command}`;
        if (this.isInCooldown(issueKey)) {
          results.details.push({
            issue: issue,
            status: 'cooldown',
            message: '修复请求已在冷却期内，跳过本次修复'
          });
          results.failed++;
          return;
        }
        
        let result;
        
        if (issue.type === 'missing_node_module') {
          result = this.installNodeModule(issue.module);
        } else if (issue.type === 'missing_system_command') {
          result = this.installSystemCommand(issue.command);
        } else {
          result = {
            success: false,
            message: `不支持的问题类型: ${issue.type}`
          };
        }
        
        if (result.success) {
          results.fixed++;
          this.markLastRepair(issueKey);
        } else {
          results.failed++;
          this.recordFailedRepair(issueKey);
        }
        
        results.details.push({
          issue: issue,
          status: result.success ? 'fixed' : 'failed',
          message: result.message
        });
        
      } catch (error) {
        results.details.push({
          issue: issue,
          status: 'error',
          message: `修复过程中发生错误: ${error.message}`
        });
        results.failed++;
      }
    });
    
    return results;
  }

  /**
   * 安装Node.js模块
   */
  installNodeModule(moduleName) {
    try {
      // 对于内置模块，不需要安装
      const builtinModules = ['fs', 'path', 'child_process', 'os', 'http', 'https', 'net', 'stream'];
      
      if (builtinModules.includes(moduleName)) {
        return {
          success: true,
          message: `${moduleName} 是Node.js内置模块，不需要安装`
        };
      }
      
      // 对于第三方模块，尝试安装
      execSync(`npm install ${moduleName}`, { stdio: 'ignore' });
      
      // 验证安装
      require.resolve(moduleName);
      
      return {
        success: true,
        message: `已成功安装Node.js模块: ${moduleName}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `安装Node.js模块失败: ${error.message}`
      };
    }
  }

  /**
   * 安装系统命令
   */
  installSystemCommand(command) {
    try {
      let installCommand = '';
      
      if (os.platform() === 'darwin') {
        // macOS
        installCommand = `brew install ${command}`;
      } else if (os.platform() === 'linux') {
        // Linux (Debian/Ubuntu)
        if (command === 'lsof') {
          installCommand = 'sudo apt-get install -y lsof';
        } else {
          installCommand = `sudo apt-get install -y ${command}`;
        }
      } else {
        return {
          success: false,
          message: `不支持的操作系统: ${os.platform()}`
        };
      }
      
      // 尝试安装
      execSync(installCommand, { stdio: 'ignore' });
      
      // 验证安装
      execSync(`which ${command}`, { stdio: 'ignore' });
      
      return {
        success: true,
        message: `已成功安装系统命令: ${command}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `安装系统命令失败: ${error.message}`
      };
    }
  }

  /**
   * 检测日志文件问题
   */
  detectLogIssues() {
    const issues = [];
    const logDir = this.logDir;
    
    try {
      if (fs.existsSync(logDir)) {
        const files = fs.readdirSync(logDir);
        
        files.forEach(file => {
          const filePath = path.join(logDir, file);
          try {
            const stats = fs.statSync(filePath);
            
            // 检查日志文件大小
            if (stats.isFile() && stats.size > 100 * 1024 * 1024) { // 100MB
              issues.push({
                type: 'large_log_file',
                filePath: filePath,
                size: stats.size,
                severity: 'warning',
                description: `日志文件过大: ${file} (${this.formatBytes(stats.size)})`
              });
            }
            
            // 检查日志文件是否超过30天
            const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
            if (stats.isFile() && stats.mtime.getTime() < thirtyDaysAgo) {
              issues.push({
                type: 'old_log_file',
                filePath: filePath,
                age: Math.floor((Date.now() - stats.mtime.getTime()) / (24 * 60 * 60 * 1000)),
                severity: 'low',
                description: `日志文件过旧: ${file} (${Math.floor((Date.now() - stats.mtime.getTime()) / (24 * 60 * 60 * 1000))} 天)`
              });
            }
            
          } catch (error) {
            // 忽略错误
          }
        });
      }
    } catch (error) {
      console.error('检测日志文件问题失败:', error.message);
    }
    
    return issues;
  }

  /**
   * 修复日志文件问题
   */
  repairLogIssues(issues) {
    const results = {
      total: issues.length,
      fixed: 0,
      failed: 0,
      details: []
    };
    
    issues.forEach(issue => {
      try {
        // 检查是否在冷却期
        const issueKey = `${issue.type}:${issue.filePath}`;
        if (this.isInCooldown(issueKey)) {
          results.details.push({
            issue: issue,
            status: 'cooldown',
            message: '修复请求已在冷却期内，跳过本次修复'
          });
          results.failed++;
          return;
        }
        
        let result;
        
        if (issue.type === 'large_log_file') {
          result = this.rotateLogFile(issue.filePath);
        } else if (issue.type === 'old_log_file') {
          result = this.archiveOldLogFile(issue.filePath);
        } else {
          result = {
            success: false,
            message: `不支持的问题类型: ${issue.type}`
          };
        }
        
        if (result.success) {
          results.fixed++;
          this.markLastRepair(issueKey);
        } else {
          results.failed++;
          this.recordFailedRepair(issueKey);
        }
        
        results.details.push({
          issue: issue,
          status: result.success ? 'fixed' : 'failed',
          message: result.message
        });
        
      } catch (error) {
        results.details.push({
          issue: issue,
          status: 'error',
          message: `修复过程中发生错误: ${error.message}`
        });
        results.failed++;
      }
    });
    
    return results;
  }

  /**
   * 轮转日志文件
   */
  rotateLogFile(filePath) {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const rotatedFilePath = `${filePath}.${timestamp}`;
      
      // 备份原文件
      fs.copyFileSync(filePath, rotatedFilePath);
      
      // 清空原文件
      fs.writeFileSync(filePath, '', 'utf8');
      
      return {
        success: true,
        message: `已轮转日志文件: ${path.basename(filePath)}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `轮转日志文件失败: ${error.message}`
      };
    }
  }

  /**
   * 归档旧日志文件
   */
  archiveOldLogFile(filePath) {
    try {
      const archiveDir = path.join(path.dirname(filePath), 'archive');
      
      // 创建归档目录
      if (!fs.existsSync(archiveDir)) {
        fs.mkdirSync(archiveDir, { recursive: true });
      }
      
      const archivePath = path.join(archiveDir, path.basename(filePath));
      
      // 移动文件到归档目录
      fs.renameSync(filePath, archivePath);
      
      return {
        success: true,
        message: `已归档旧日志文件: ${path.basename(filePath)}`
      };
      
    } catch (error) {
      return {
        success: false,
        message: `归档旧日志文件失败: ${error.message}`
      };
    }
  }

  /**
   * 记录修复结果
   */
  logRepairResult(ruleName, issues, results) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      ruleName: ruleName,
      issues: issues.map(issue => ({ type: issue.type, severity: issue.severity })),
      results: results
    };
    
    this.repairLog.push(logEntry);
    
    // 写入日志文件
    this.writeRepairLog(logEntry);
    
    // 限制日志大小
    if (this.repairLog.length > 100) {
      this.repairLog = this.repairLog.slice(-100);
    }
  }

  /**
   * 写入修复日志到文件
   */
  writeRepairLog(logEntry) {
    try {
      const logFilePath = path.join(this.logDir, 'repair-history.log');
      fs.appendFileSync(logFilePath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入修复日志失败:', error.message);
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
      
      const errorLogPath = path.join(this.logDir, 'repair-errors.log');
      fs.appendFileSync(errorLogPath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入错误日志失败:', error.message);
    }
  }

  /**
   * 检查是否在冷却期
   */
  isInCooldown(issueKey) {
    const lastRepair = this.failedRepairs.get(issueKey);
    if (lastRepair) {
      const timeSinceLastRepair = Date.now() - lastRepair.timestamp;
      return timeSinceLastRepair < this.cooldownPeriod;
    }
    return false;
  }

  /**
   * 标记最后一次修复时间
   */
  markLastRepair(issueKey) {
    this.failedRepairs.set(issueKey, {
      timestamp: Date.now(),
      retryCount: 0
    });
  }

  /**
   * 记录修复失败
   */
  recordFailedRepair(issueKey) {
    const repairRecord = this.failedRepairs.get(issueKey);
    const retryCount = repairRecord ? repairRecord.retryCount + 1 : 1;
    
    this.failedRepairs.set(issueKey, {
      timestamp: Date.now(),
      retryCount: retryCount
    });
    
    // 如果重试次数超过最大值，发出警告
    if (retryCount >= this.maxRetries) {
      console.warn(`修复失败达到最大重试次数 (${this.maxRetries}次): ${issueKey}`);
    }
  }

  /**
   * 获取修复统计信息
   */
  getRepairStats() {
    const stats = {
      totalRepairs: this.repairLog.length,
      successfulRepairs: 0,
      failedRepairs: 0,
      byRule: {},
      bySeverity: {}
    };
    
    this.repairLog.forEach(log => {
      stats.successfulRepairs += log.results.fixed;
      stats.failedRepairs += log.results.failed;
      
      if (!stats.byRule[log.ruleName]) {
        stats.byRule[log.ruleName] = { fixed: 0, failed: 0 };
      }
      
      stats.byRule[log.ruleName].fixed += log.results.fixed;
      stats.byRule[log.ruleName].failed += log.results.failed;
      
      log.issues.forEach(issue => {
        if (!stats.bySeverity[issue.severity]) {
          stats.bySeverity[issue.severity] = { fixed: 0, failed: 0 };
        }
        
        // 简化处理，假设问题被修复
        stats.bySeverity[issue.severity].fixed++;
      });
    });
    
    return stats;
  }

  /**
   * 停止自动修复引擎
   */
  stop() {
    if (!this.isRunning) {
      console.log('自动修复引擎未在运行');
      return;
    }

    this.isRunning = false;
    
    // 清除修复间隔
    if (this.repairInterval) {
      clearInterval(this.repairInterval);
    }
    
    console.log('自动修复引擎已停止');
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  try {
    const repairEngine = new AutoRepairEngine(configPath);
    repairEngine.start();
    
    // 处理信号
    process.on('SIGINT', () => {
      console.log('收到终止信号，正在停止自动修复引擎...');
      repairEngine.stop();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('启动自动修复引擎失败:', error.message);
    process.exit(1);
  }
}

module.exports = AutoRepairEngine;
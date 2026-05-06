/**
 * 错误自动检测和修复系统
 * 实时监控系统错误，自动诊断并尝试修复
 * 提供智能错误分类、修复策略和恢复机制
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const EventEmitter = require('events');
const crypto = require('crypto');

class AutoErrorRepairSystem extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            projectRoot: config.projectRoot || process.cwd(),
            logPath: config.logPath || './Logs/auto-error-repair.log',
            checkInterval: config.checkInterval || 10000,
            maxRepairAttempts: config.maxRepairAttempts || 3,
            backupDir: config.backupDir || './Backups/auto_repair',
            ...config
        };
        
        this.errorPatterns = new Map();
        this.repairStrategies = new Map();
        this.errorHistory = [];
        this.repairAttempts = new Map();
        this.isRepairing = false;
        
        this.init();
    }
    
    async init() {
        this.log('🔧 初始化自动错误修复系统...');
        
        // 确保目录存在
        await this.ensureDirectoryExists(this.config.backupDir);
        await this.ensureDirectoryExists(path.dirname(this.config.logPath));
        
        // 初始化错误模式
        this.initErrorPatterns();
        
        // 初始化修复策略
        this.initRepairStrategies();
        
        // 启动监控
        this.startMonitoring();
        
        this.log('✅ 自动错误修复系统初始化完成');
    }
    
    async ensureDirectoryExists(dirPath) {
        try {
            await fs.promises.mkdir(dirPath, { recursive: true });
        } catch (error) {
            this.log(`❌ 创建目录失败: ${dirPath} - ${error.message}`);
        }
    }
    
    initErrorPatterns() {
        // JavaScript错误模式
        this.errorPatterns.set('SyntaxError', {
            pattern: /SyntaxError:\s*(.+)/i,
            severity: 'high',
            category: 'syntax'
        });
        
        this.errorPatterns.set('ReferenceError', {
            pattern: /ReferenceError:\s*(.+) is not defined/i,
            severity: 'medium',
            category: 'reference'
        });
        
        this.errorPatterns.set('TypeError', {
            pattern: /TypeError:\s*(.+)/i,
            severity: 'medium',
            category: 'type'
        });
        
        // 网络错误模式
        this.errorPatterns.set('NetworkError', {
            pattern: /NetworkError:\s*(.+)/i,
            severity: 'high',
            category: 'network'
        });
        
        this.errorPatterns.set('ConnectionRefused', {
            pattern: /ECONNREFUSED|Connection refused/i,
            severity: 'high',
            category: 'connection'
        });
        
        // 文件系统错误模式
        this.errorPatterns.set('FileNotFound', {
            pattern: /ENOENT:\s*no such file or directory/i,
            severity: 'high',
            category: 'filesystem'
        });
        
        this.errorPatterns.set('PermissionDenied', {
            pattern: /EACCES:\s*permission denied/i,
            severity: 'high',
            category: 'permission'
        });
        
        // 内存错误模式
        this.errorPatterns.set('OutOfMemory', {
            pattern: /JavaScript heap out of memory|OutOfMemoryError/i,
            severity: 'critical',
            category: 'memory'
        });
        
        // 端口占用错误
        this.errorPatterns.set('PortInUse', {
            pattern: /EADDRINUSE:\s*address already in use.*:(\d+)/i,
            severity: 'medium',
            category: 'port'
        });
    }
    
    initRepairStrategies() {
        // 语法错误修复策略
        this.repairStrategies.set('syntax', [
            {
                name: 'backup_restore',
                description: '从备份恢复文件',
                execute: async (error) => await this.repairFromBackup(error)
            },
            {
                name: 'syntax_fix',
                description: '自动语法修复',
                execute: async (error) => await this.fixSyntaxError(error)
            }
        ]);
        
        // 引用错误修复策略
        this.repairStrategies.set('reference', [
            {
                name: 'import_fix',
                description: '修复导入语句',
                execute: async (error) => await this.fixImportError(error)
            },
            {
                name: 'variable_declaration',
                description: '添加变量声明',
                execute: async (error) => await this.fixVariableDeclaration(error)
            }
        ]);
        
        // 网络错误修复策略
        this.repairStrategies.set('network', [
            {
                name: 'service_restart',
                description: '重启网络服务',
                execute: async (error) => await this.restartNetworkService(error)
            },
            {
                name: 'connection_retry',
                description: '重试连接',
                execute: async (error) => await this.retryConnection(error)
            }
        ]);
        
        // 文件系统错误修复策略
        this.repairStrategies.set('filesystem', [
            {
                name: 'create_missing_file',
                description: '创建缺失文件',
                execute: async (error) => await this.createMissingFile(error)
            },
            {
                name: 'fix_path',
                description: '修复文件路径',
                execute: async (error) => await this.fixFilePath(error)
            }
        ]);
        
        // 端口占用修复策略
        this.repairStrategies.set('port', [
            {
                name: 'kill_process',
                description: '终止占用端口的进程',
                execute: async (error) => await this.killPortProcess(error)
            },
            {
                name: 'change_port',
                description: '更改端口号',
                execute: async (error) => await this.changePort(error)
            }
        ]);
        
        // 内存错误修复策略
        this.repairStrategies.set('memory', [
            {
                name: 'increase_memory',
                description: '增加内存限制',
                execute: async (error) => await this.increaseMemoryLimit(error)
            },
            {
                name: 'restart_service',
                description: '重启服务释放内存',
                execute: async (error) => await this.restartService(error)
            }
        ]);
    }
    
    startMonitoring() {
        // 监控日志文件
        this.monitorLogs();
        
        // 监控进程
        this.monitorProcesses();
        
        // 监控文件变化
        this.monitorFiles();
        
        // 定期系统检查
        setInterval(() => {
            this.performSystemCheck();
        }, this.config.checkInterval);
        
        this.log('✅ 错误监控已启动');
    }
    
    monitorLogs() {
        const logFiles = [
            './Logs/error.log',
            './Logs/node_server.log',
            './Logs/api_server.log'
        ];
        
        logFiles.forEach(logFile => {
            this.watchLogFile(logFile);
        });
    }
    
    watchLogFile(logFile) {
        if (!fs.existsSync(logFile)) {
            return;
        }
        
        fs.watchFile(logFile, (curr, prev) => {
            if (curr.size > prev.size) {
                // 读取新增内容
                const stream = fs.createReadStream(logFile, {
                    start: prev.size,
                    end: curr.size
                });
                
                let newData = '';
                stream.on('data', (chunk) => {
                    newData += chunk.toString();
                });
                
                stream.on('end', () => {
                    this.processLogData(newData);
                });
            }
        });
    }
    
    processLogData(data) {
        const lines = data.split('\n').filter(line => line.trim());
        
        lines.forEach(line => {
            const error = this.parseError(line);
            if (error) {
                this.handleError(error);
            }
        });
    }
    
    parseError(logLine) {
        for (const [name, pattern] of this.errorPatterns) {
            const match = logLine.match(pattern.pattern);
            if (match) {
                return {
                    type: name,
                    message: match[1] || logLine,
                    fullMessage: logLine,
                    severity: pattern.severity,
                    category: pattern.category,
                    timestamp: new Date(),
                    raw: logLine
                };
            }
        }
        
        // 通用错误检测
        if (logLine.includes('Error') || logLine.includes('error') || logLine.includes('Exception')) {
            return {
                type: 'UnknownError',
                message: logLine,
                fullMessage: logLine,
                severity: 'medium',
                category: 'unknown',
                timestamp: new Date(),
                raw: logLine
            };
        }
        
        return null;
    }
    
    async handleError(error) {
        this.log(`🚨 检测到错误: ${error.type} - ${error.message}`);
        
        // 添加到历史记录
        this.errorHistory.push(error);
        if (this.errorHistory.length > 1000) {
            this.errorHistory.shift();
        }
        
        // 发出错误事件
        this.emit('error', error);
        
        // 如果正在修复中，跳过
        if (this.isRepairing) {
            this.log('⚠️ 系统正在修复中，跳过新错误');
            return;
        }
        
        // 尝试自动修复
        await this.attemptRepair(error);
    }
    
    async attemptRepair(error) {
        const errorKey = `${error.category}_${error.type}`;
        const attempts = this.repairAttempts.get(errorKey) || 0;
        
        if (attempts >= this.config.maxRepairAttempts) {
            this.log(`❌ 错误 ${errorKey} 已达到最大修复次数，停止尝试`);
            return;
        }
        
        this.isRepairing = true;
        this.repairAttempts.set(errorKey, attempts + 1);
        
        const strategies = this.repairStrategies.get(error.category) || [];
        
        for (const strategy of strategies) {
            try {
                this.log(`🔧 尝试修复策略: ${strategy.description}`);
                
                const result = await strategy.execute(error);
                
                if (result.success) {
                    this.log(`✅ 修复成功: ${strategy.description}`);
                    this.emit('repaired', { error, strategy, result });
                    this.repairAttempts.delete(errorKey);
                    break;
                } else {
                    this.log(`❌ 修复失败: ${strategy.description} - ${result.message}`);
                }
            } catch (repairError) {
                this.log(`❌ 修复策略执行失败: ${repairError.message}`);
            }
        }
        
        this.isRepairing = false;
    }
    
    // 修复策略实现
    async repairFromBackup(error) {
        try {
            // 从错误消息中提取文件路径
            const filePath = this.extractFilePath(error.message);
            if (!filePath) {
                return { success: false, message: '无法提取文件路径' };
            }
            
            const backupPath = path.join(this.config.backupDir, path.basename(filePath));
            if (!fs.existsSync(backupPath)) {
                return { success: false, message: '备份文件不存在' };
            }
            
            // 创建当前文件的备份
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const currentBackup = `${filePath}.backup.${timestamp}`;
            await fs.promises.copyFile(filePath, currentBackup);
            
            // 从备份恢复
            await fs.promises.copyFile(backupPath, filePath);
            
            return { success: true, message: '从备份恢复成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }
    
    async fixSyntaxError(error) {
        try {
            const filePath = this.extractFilePath(error.message);
            if (!filePath) {
                return { success: false, message: '无法提取文件路径' };
            }
            
            const content = await fs.promises.readFile(filePath, 'utf8');
            
            // 简单的语法修复逻辑
            let fixedContent = content;
            
            // 修复常见的语法错误
            fixedContent = fixedContent.replace(/;\s*;/g, ';'); // 双分号
            fixedContent = fixedContent.replace(/\{\s*\}/g, '{}'); // 空块
            fixedContent = fixedContent.replace(/\(\s*\)/g, '()'); // 空括号
            
            if (fixedContent !== content) {
                await fs.promises.writeFile(filePath, fixedContent);
                return { success: true, message: '语法错误修复完成' };
            }
            
            return { success: false, message: '未发现可修复的语法错误' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }
    
    async killPortProcess(error) {
        try {
            const portMatch = error.message.match(/:(\d+)/);
            if (!portMatch) {
                return { success: false, message: '无法提取端口号' };
            }
            
            const port = portMatch[1];
            
            return new Promise((resolve) => {
                exec(`lsof -ti:${port} | xargs kill -9`, (error, stdout, stderr) => {
                    if (error) {
                        resolve({ success: false, message: error.message });
                    } else {
                        resolve({ success: true, message: `已终止占用端口 ${port} 的进程` });
                    }
                });
            });
        } catch (error) {
            return { success: false, message: error.message };
        }
    }
    
    async increaseMemoryLimit(error) {
        try {
            // 修改package.json中的内存限制
            const packageJsonPath = path.join(this.config.projectRoot, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(await fs.promises.readFile(packageJsonPath, 'utf8'));
                
                if (packageJson.scripts) {
                    Object.keys(packageJson.scripts).forEach(scriptName => {
                        const script = packageJson.scripts[scriptName];
                        if (script.includes('node')) {
                            if (!script.includes('--max-old-space-size')) {
                                packageJson.scripts[scriptName] = script.replace('node', 'node --max-old-space-size=4096');
                            }
                        }
                    });
                    
                    await fs.promises.writeFile(packageJsonPath, JSON.stringify(packageJson, null, 2));
                    return { success: true, message: '内存限制已增加到4GB' };
                }
            }
            
            return { success: false, message: '无法修改package.json' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }
    
    extractFilePath(errorMessage) {
        // 尝试从错误消息中提取文件路径
        const pathMatch = errorMessage.match(/at\s+.*\(([^:]+):\d+:\d+\)/);
        if (pathMatch) {
            return pathMatch[1];
        }
        
        const simplePathMatch = errorMessage.match(/([\/\\][^:\s]+):\d+/);
        if (simplePathMatch) {
            return simplePathMatch[1];
        }
        
        return null;
    }
    
    monitorProcesses() {
        // 监控关键进程
        setInterval(() => {
            this.checkProcessHealth();
        }, 30000);
    }
    
    async checkProcessHealth() {
        const criticalProcesses = ['node', 'python', 'nginx'];
        
        for (const processName of criticalProcesses) {
            try {
                const result = await this.executeCommand(`pgrep ${processName}`);
                if (!result.stdout.trim()) {
                    this.log(`⚠️ 关键进程 ${processName} 未运行`);
                    await this.restartProcess(processName);
                }
            } catch (error) {
                this.log(`❌ 检查进程 ${processName} 失败: ${error.message}`);
            }
        }
    }
    
    async restartProcess(processName) {
        try {
            this.log(`🔄 重启进程: ${processName}`);
            
            // 根据进程类型执行不同的重启命令
            let restartCommand;
            switch (processName) {
                case 'node':
                    restartCommand = 'npm start';
                    break;
                case 'nginx':
                    restartCommand = 'sudo systemctl restart nginx';
                    break;
                default:
                    restartCommand = `${processName} --restart`;
            }
            
            await this.executeCommand(restartCommand);
            this.log(`✅ 进程 ${processName} 重启成功`);
        } catch (error) {
            this.log(`❌ 重启进程 ${processName} 失败: ${error.message}`);
        }
    }
    
    monitorFiles() {
        const criticalFiles = [
            './package.json',
            './config.json',
            './.env'
        ];
        
        criticalFiles.forEach(file => {
            if (fs.existsSync(file)) {
                fs.watchFile(file, (curr, prev) => {
                    if (curr.mtime > prev.mtime) {
                        this.log(`📝 关键文件已修改: ${file}`);
                        this.validateFile(file);
                    }
                });
            }
        });
    }
    
    async validateFile(filePath) {
        try {
            if (filePath.endsWith('.json')) {
                JSON.parse(await fs.promises.readFile(filePath, 'utf8'));
                this.log(`✅ JSON文件验证通过: ${filePath}`);
            }
        } catch (validationError) {
            this.log(`❌ 文件验证失败: ${filePath} - ${validationError.message}`);
            
            // 尝试从备份恢复
            const error = {
                type: 'FileValidationError',
                message: `文件 ${filePath} 验证失败`,
                category: 'filesystem'
            };
            
            await this.attemptRepair(error);
        }
    }
    
    async performSystemCheck() {
        try {
            // 检查磁盘空间
            const diskUsage = await this.checkDiskSpace();
            if (diskUsage.usage > 90) {
                this.log(`⚠️ 磁盘空间不足: ${diskUsage.usage}%`);
                await this.cleanupDiskSpace();
            }
            
            // 检查内存使用
            const memoryUsage = await this.checkMemoryUsage();
            if (memoryUsage.usage > 90) {
                this.log(`⚠️ 内存使用过高: ${memoryUsage.usage}%`);
                await this.optimizeMemory();
            }
            
        } catch (error) {
            this.log(`❌ 系统检查失败: ${error.message}`);
        }
    }
    
    async checkDiskSpace() {
        return new Promise((resolve, reject) => {
            exec('df -h /', (error, stdout) => {
                if (error) {
                    reject(error);
                    return;
                }
                
                const lines = stdout.split('\n');
                const dataLine = lines[1];
                const parts = dataLine.split(/\s+/);
                const usage = parseInt(parts[4].replace('%', ''));
                
                resolve({ usage });
            });
        });
    }
    
    async cleanupDiskSpace() {
        try {
            this.log('🧹 开始清理磁盘空间...');
            
            // 清理日志文件
            const logDir = './Logs';
            if (fs.existsSync(logDir)) {
                const files = await fs.promises.readdir(logDir);
                for (const file of files) {
                    if (file.endsWith('.old') || file.endsWith('.bak')) {
                        await fs.promises.unlink(path.join(logDir, file));
                        this.log(`🗑️ 删除旧日志文件: ${file}`);
                    }
                }
            }
            
            // 清理临时文件
            const tempDirs = ['./temp', './tmp'];
            for (const tempDir of tempDirs) {
                if (fs.existsSync(tempDir)) {
                    await this.executeCommand(`rm -rf ${tempDir}/*`);
                    this.log(`🗑️ 清理临时目录: ${tempDir}`);
                }
            }
            
            this.log('✅ 磁盘空间清理完成');
        } catch (error) {
            this.log(`❌ 清理磁盘空间失败: ${error.message}`);
        }
    }
    
    async checkMemoryUsage() {
        return new Promise((resolve, reject) => {
            exec('free -m', (error, stdout) => {
                if (error) {
                    reject(error);
                    return;
                }
                
                const lines = stdout.split('\n');
                const memLine = lines[1];
                const parts = memLine.split(/\s+/);
                const total = parseInt(parts[1]);
                const used = parseInt(parts[2]);
                const usage = Math.round((used / total) * 100);
                
                resolve({ usage, total, used });
            });
        });
    }
    
    async optimizeMemory() {
        try {
            this.log('🧠 开始内存优化...');
            
            // 清理系统缓存
            await this.executeCommand('sync && echo 3 > /proc/sys/vm/drop_caches');
            
            // 重启高内存使用的服务
            const highMemoryProcesses = ['node', 'python'];
            for (const process of highMemoryProcesses) {
                await this.restartProcess(process);
            }
            
            this.log('✅ 内存优化完成');
        } catch (error) {
            this.log(`❌ 内存优化失败: ${error.message}`);
        }
    }
    
    executeCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }
    
    getSystemStatus() {
        return {
            errorHistory: this.errorHistory.slice(-10),
            repairAttempts: Object.fromEntries(this.repairAttempts),
            isRepairing: this.isRepairing,
            uptime: process.uptime(),
            memoryUsage: process.memoryUsage()
        };
    }
    
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        fs.appendFile(this.config.logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error('写入日志失败:', err);
            }
        });
    }
}

module.exports = AutoErrorRepairSystem;
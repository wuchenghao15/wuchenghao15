/**
 * 依赖项自动更新管理系统
 * 监控npm、pip、系统包等依赖项版本
 * 自动检查更新、安全漏洞、兼容性
 * 支持回滚、备份、渐进式更新
 */

const { EventEmitter } = require('events');
const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class DependencyManager extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            checkInterval: config.checkInterval || 24 * 60 * 60 * 1000, // 24小时
            enableAutoUpdate: config.enableAutoUpdate || false,
            enableSecurityCheck: config.enableSecurityCheck !== false,
            enableCompatibilityCheck: config.enableCompatibilityCheck !== false,
            enableBackup: config.enableBackup !== false,
            backupDir: config.backupDir || './Backups/Dependencies',
            logDir: config.logDir || './Logs',
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 5000,
            updateStrategy: config.updateStrategy || 'patch', // patch, minor, major
            excludePackages: config.excludePackages || [],
            ...config
        };
        
        this.dependencies = new Map();
        this.updateQueue = [];
        this.isUpdating = false;
        this.metrics = {
            totalChecks: 0,
            updatesFound: 0,
            updatesApplied: 0,
            securityIssues: 0,
            rollbacks: 0,
            startTime: Date.now()
        };
        
        this.logger = null;
        this.checkInterval = null;
        
        this.init();
    }
    
    async init() {
        this.log('info', '📦 初始化依赖项管理系统...');
        
        // 确保目录存在
        await this.ensureDirectoryExists(this.config.backupDir);
        await this.ensureDirectoryExists(this.config.logDir);
        
        // 扫描现有依赖
        await this.scanDependencies();
        
        // 启动定期检查
        this.startPeriodicCheck();
        
        this.log('info', '✅ 依赖项管理系统初始化完成');
    }
    
    async ensureDirectoryExists(dirPath) {
        try {
            await fs.mkdir(dirPath, { recursive: true });
        } catch (error) {
            console.error('创建目录失败:', error.message);
        }
    }
    
    async scanDependencies() {
        this.log('info', '🔍 扫描项目依赖项...');
        
        // 扫描npm依赖
        await this.scanNpmDependencies();
        
        // 扫描pip依赖
        await this.scanPipDependencies();
        
        // 扫描系统依赖
        await this.scanSystemDependencies();
        
        this.log('info', `📋 发现 ${this.dependencies.size} 个依赖项`);
    }
    
    async scanNpmDependencies() {
        try {
            const packageJsonPath = path.join(process.cwd(), 'package.json');
            
            if (await this.fileExists(packageJsonPath)) {
                const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf8'));
                
                // 扫描dependencies
                if (packageJson.dependencies) {
                    for (const [name, version] of Object.entries(packageJson.dependencies)) {
                        await this.addNpmDependency(name, version, 'production');
                    }
                }
                
                // 扫描devDependencies
                if (packageJson.devDependencies) {
                    for (const [name, version] of Object.entries(packageJson.devDependencies)) {
                        await this.addNpmDependency(name, version, 'development');
                    }
                }
            }
        } catch (error) {
            this.log('error', '扫描npm依赖失败', { error: error.message });
        }
    }
    
    async addNpmDependency(name, currentVersion, type) {
        try {
            // 获取最新版本信息
            const info = await this.getNpmPackageInfo(name);
            
            const dependency = {
                name,
                manager: 'npm',
                type,
                currentVersion,
                latestVersion: info.latest,
                wantedVersion: info.wanted,
                outdated: info.outdated,
                securityIssues: info.security || [],
                lastChecked: new Date().toISOString(),
                updateAvailable: info.outdated,
                updateType: this.determineUpdateType(currentVersion, info.latest),
                compatibility: null,
                backup: null
            };
            
            this.dependencies.set(`npm:${name}`, dependency);
            
        } catch (error) {
            this.log('warn', `获取npm包信息失败: ${name}`, { error: error.message });
        }
    }
    
    async getNpmPackageInfo(packageName) {
        return new Promise((resolve, reject) => {
            const npm = spawn('npm', ['view', packageName, 'version', 'dist-tags.latest'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            let errorOutput = '';
            
            npm.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            npm.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            npm.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(errorOutput));
                    return;
                }
                
                const lines = output.trim().split('\n');
                const version = lines[0];
                const latest = lines[1];
                
                resolve({
                    current: version,
                    latest: latest,
                    wanted: latest,
                    outdated: version !== latest
                });
            });
        });
    }
    
    async scanPipDependencies() {
        try {
            const requirementsPath = path.join(process.cwd(), 'requirements.txt');
            
            if (await this.fileExists(requirementsPath)) {
                const requirements = await fs.readFile(requirementsPath, 'utf8');
                const lines = requirements.split('\n').filter(line => line.trim() && !line.startsWith('#'));
                
                for (const line of lines) {
                    const match = line.match(/^([a-zA-Z0-9\-_]+)([=<>!]+)(.+)$/);
                    if (match) {
                        const [, name, operator, version] = match;
                        await this.addPipDependency(name, version, operator);
                    }
                }
            }
        } catch (error) {
            this.log('error', '扫描pip依赖失败', { error: error.message });
        }
    }
    
    async addPipDependency(name, currentVersion, operator) {
        try {
            // 获取最新版本信息
            const info = await this.getPipPackageInfo(name);
            
            const dependency = {
                name,
                manager: 'pip',
                type: 'production',
                currentVersion,
                latestVersion: info.latest,
                wantedVersion: info.latest,
                outdated: this.isVersionOutdated(currentVersion, info.latest),
                securityIssues: info.security || [],
                lastChecked: new Date().toISOString(),
                updateAvailable: this.isVersionOutdated(currentVersion, info.latest),
                updateType: this.determineUpdateType(currentVersion, info.latest),
                compatibility: null,
                backup: null
            };
            
            this.dependencies.set(`pip:${name}`, dependency);
            
        } catch (error) {
            this.log('warn', `获取pip包信息失败: ${name}`, { error: error.message });
        }
    }
    
    async getPipPackageInfo(packageName) {
        return new Promise((resolve, reject) => {
            const pip = spawn('pip', ['index', 'versions', packageName], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            let errorOutput = '';
            
            pip.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            pip.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            pip.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(errorOutput));
                    return;
                }
                
                // 解析pip输出
                const latestMatch = output.match(/Latest:\s*(.+)/);
                const latest = latestMatch ? latestMatch[1].trim() : '0.0.0';
                
                resolve({
                    latest,
                    security: [] // 简化实现，实际应调用pip-audit
                });
            });
        });
    }
    
    async scanSystemDependencies() {
        try {
            // 扫描系统包（简化实现）
            const systemPackages = ['node', 'npm', 'python3', 'pip3'];
            
            for (const pkg of systemPackages) {
                try {
                    const version = await this.getSystemPackageVersion(pkg);
                    
                    const dependency = {
                        name: pkg,
                        manager: 'system',
                        type: 'system',
                        currentVersion: version,
                        latestVersion: version, // 简化实现
                        wantedVersion: version,
                        outdated: false,
                        securityIssues: [],
                        lastChecked: new Date().toISOString(),
                        updateAvailable: false,
                        updateType: null,
                        compatibility: null,
                        backup: null
                    };
                    
                    this.dependencies.set(`system:${pkg}`, dependency);
                    
                } catch (error) {
                    this.log('debug', `获取系统包版本失败: ${pkg}`, { error: error.message });
                }
            }
        } catch (error) {
            this.log('error', '扫描系统依赖失败', { error: error.message });
        }
    }
    
    async getSystemPackageVersion(packageName) {
        return new Promise((resolve, reject) => {
            const cmd = spawn(packageName, ['--version'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            
            cmd.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            cmd.on('close', (code) => {
                if (code === 0) {
                    const version = output.trim().match(/v?(\d+\.\d+\.\d+)/);
                    resolve(version ? version[1] : 'unknown');
                } else {
                    reject(new Error('Package not found'));
                }
            });
        });
    }
    
    startPeriodicCheck() {
        this.checkInterval = setInterval(async () => {
            await this.checkForUpdates();
        }, this.config.checkInterval);
        
        this.log('info', '🔄 启动定期依赖检查');
    }
    
    stopPeriodicCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
    
    async checkForUpdates() {
        this.log('info', '🔍 检查依赖项更新...');
        this.metrics.totalChecks++;
        
        try {
            // 重新扫描依赖
            await this.scanDependencies();
            
            // 检查安全漏洞
            if (this.config.enableSecurityCheck) {
                await this.checkSecurityVulnerabilities();
            }
            
            // 检查兼容性
            if (this.config.enableCompatibilityCheck) {
                await this.checkCompatibility();
            }
            
            // 识别可更新的依赖
            const updatableDeps = Array.from(this.dependencies.values())
                .filter(dep => dep.updateAvailable && !this.config.excludePackages.includes(dep.name));
            
            this.metrics.updatesFound = updatableDeps.length;
            
            if (updatableDeps.length > 0) {
                this.log('info', `📦 发现 ${updatableDeps.length} 个可更新依赖`);
                
                if (this.config.enableAutoUpdate) {
                    await this.queueUpdates(updatableDeps);
                } else {
                    this.emit('updates-available', updatableDeps);
                }
            }
            
            // 发出指标事件
            this.emit('metrics', this.getMetrics());
            
        } catch (error) {
            this.log('error', '检查更新失败', { error: error.message });
        }
    }
    
    async checkSecurityVulnerabilities() {
        this.log('info', '🔒 检查安全漏洞...');
        
        for (const [key, dependency] of this.dependencies) {
            try {
                if (dependency.manager === 'npm') {
                    const securityIssues = await this.checkNpmSecurity(dependency.name);
                    dependency.securityIssues = securityIssues;
                    
                    if (securityIssues.length > 0) {
                        this.metrics.securityIssues += securityIssues.length;
                        this.log('warn', `🚨 发现安全漏洞: ${dependency.name}`, { 
                            count: securityIssues.length 
                        });
                    }
                }
            } catch (error) {
                this.log('debug', `检查安全漏洞失败: ${dependency.name}`, { error: error.message });
            }
        }
    }
    
    async checkNpmSecurity(packageName) {
        return new Promise((resolve, reject) => {
            const audit = spawn('npm', ['audit', '--json'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            
            audit.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            audit.on('close', (code) => {
                try {
                    const auditResult = JSON.parse(output);
                    const vulnerabilities = auditResult.vulnerabilities || {};
                    const packageVulns = vulnerabilities[packageName] || [];
                    
                    resolve(packageVulns.map(vuln => ({
                        severity: vuln.severity,
                        title: vuln.title,
                        url: vuln.url,
                        fixAvailable: vuln.fixAvailable
                    })));
                } catch (error) {
                    resolve([]); // 解析失败时返回空数组
                }
            });
        });
    }
    
    async checkCompatibility() {
        this.log('info', '🔗 检查兼容性...');
        
        for (const [key, dependency] of this.dependencies) {
            try {
                // 简化的兼容性检查
                dependency.compatibility = await this.checkPackageCompatibility(dependency);
            } catch (error) {
                this.log('debug', `兼容性检查失败: ${dependency.name}`, { error: error.message });
                dependency.compatibility = { compatible: false, reason: error.message };
            }
        }
    }
    
    async checkPackageCompatibility(dependency) {
        // 简化实现：检查Node.js版本兼容性
        if (dependency.manager === 'npm') {
            try {
                const packageInfo = await this.getNpmPackageInfo(dependency.name);
                const engines = await this.getPackageEngines(dependency.name);
                
                if (engines.node) {
                    const currentNodeVersion = process.version;
                    const compatible = this.isNodeVersionCompatible(currentNodeVersion, engines.node);
                    
                    return {
                        compatible,
                        reason: compatible ? 'Node.js版本兼容' : 'Node.js版本不兼容',
                        currentNodeVersion,
                        requiredNodeVersion: engines.node
                    };
                }
            } catch (error) {
                // 忽略错误，返回兼容
            }
        }
        
        return { compatible: true, reason: '默认兼容' };
    }
    
    async getPackageEngines(packageName) {
        return new Promise((resolve, reject) => {
            const npm = spawn('npm', ['view', packageName, 'engines'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            
            npm.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            npm.on('close', (code) => {
                if (code === 0 && output.trim()) {
                    try {
                        resolve(JSON.parse(output.trim()));
                    } catch {
                        resolve({});
                    }
                } else {
                    resolve({});
                }
            });
        });
    }
    
    isNodeVersionCompatible(current, required) {
        // 简化的版本兼容性检查
        const currentNum = current.replace('v', '').split('.').map(Number);
        const requiredMatch = required.match(/>=?(\d+\.\d+)/);
        
        if (requiredMatch) {
            const requiredNum = requiredMatch[1].split('.').map(Number);
            
            for (let i = 0; i < Math.max(currentNum.length, requiredNum.length); i++) {
                const curr = currentNum[i] || 0;
                const req = requiredNum[i] || 0;
                
                if (curr > req) return true;
                if (curr < req) return false;
            }
        }
        
        return true;
    }
    
    async queueUpdates(dependencies) {
        // 根据更新策略过滤依赖
        const filteredDeps = dependencies.filter(dep => {
            switch (this.config.updateStrategy) {
                case 'patch':
                    return dep.updateType === 'patch';
                case 'minor':
                    return dep.updateType === 'patch' || dep.updateType === 'minor';
                case 'major':
                    return true;
                default:
                    return dep.updateType === 'patch';
            }
        });
        
        // 按优先级排序：安全漏洞 > 补丁 > 次要版本 > 主要版本
        filteredDeps.sort((a, b) => {
            const aPriority = this.getUpdatePriority(a);
            const bPriority = this.getUpdatePriority(b);
            return bPriority - aPriority;
        });
        
        this.updateQueue = filteredDeps;
        
        if (this.updateQueue.length > 0) {
            this.log('info', `📋 将 ${this.updateQueue.length} 个依赖加入更新队列`);
            await this.processUpdateQueue();
        }
    }
    
    getUpdatePriority(dependency) {
        let priority = 0;
        
        // 安全漏洞优先级最高
        if (dependency.securityIssues.length > 0) {
            priority += 1000;
        }
        
        // 更新类型优先级
        switch (dependency.updateType) {
            case 'patch':
                priority += 100;
                break;
            case 'minor':
                priority += 50;
                break;
            case 'major':
                priority += 10;
                break;
        }
        
        return priority;
    }
    
    async processUpdateQueue() {
        if (this.isUpdating || this.updateQueue.length === 0) {
            return;
        }
        
        this.isUpdating = true;
        
        while (this.updateQueue.length > 0) {
            const dependency = this.updateQueue.shift();
            
            try {
                await this.updateDependency(dependency);
            } catch (error) {
                this.log('error', `更新依赖失败: ${dependency.name}`, { error: error.message });
            }
        }
        
        this.isUpdating = false;
    }
    
    async updateDependency(dependency) {
        this.log('info', `🔄 更新依赖: ${dependency.name} (${dependency.currentVersion} → ${dependency.latestVersion})`);
        
        try {
            // 创建备份
            if (this.config.enableBackup) {
                await this.createBackup(dependency);
            }
            
            // 执行更新
            let success = false;
            
            switch (dependency.manager) {
                case 'npm':
                    success = await this.updateNpmPackage(dependency);
                    break;
                case 'pip':
                    success = await this.updatePipPackage(dependency);
                    break;
                case 'system':
                    success = await this.updateSystemPackage(dependency);
                    break;
            }
            
            if (success) {
                this.metrics.updatesApplied++;
                dependency.currentVersion = dependency.latestVersion;
                dependency.updateAvailable = false;
                dependency.lastUpdated = new Date().toISOString();
                
                this.log('info', `✅ 依赖更新成功: ${dependency.name}`);
                this.emit('dependency-updated', dependency);
            } else {
                throw new Error('更新命令执行失败');
            }
            
        } catch (error) {
            this.log('error', `更新依赖失败: ${dependency.name}`, { error: error.message });
            
            // 尝试回滚
            if (this.config.enableBackup && dependency.backup) {
                await this.rollbackDependency(dependency);
            }
            
            throw error;
        }
    }
    
    async createBackup(dependency) {
        try {
            const backupId = crypto.randomBytes(8).toString('hex');
            const backupPath = path.join(this.config.backupDir, `${dependency.name}-${backupId}.json`);
            
            const backup = {
                id: backupId,
                timestamp: new Date().toISOString(),
                dependency: { ...dependency }
            };
            
            await fs.writeFile(backupPath, JSON.stringify(backup, null, 2));
            dependency.backup = backup;
            
            this.log('debug', `💾 创建备份: ${dependency.name} (${backupId})`);
            
        } catch (error) {
            this.log('warn', `创建备份失败: ${dependency.name}`, { error: error.message });
        }
    }
    
    async updateNpmPackage(dependency) {
        return new Promise((resolve, reject) => {
            const npm = spawn('npm', ['install', `${dependency.name}@${dependency.latestVersion}`, '--save'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            let errorOutput = '';
            
            npm.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            npm.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            npm.on('close', (code) => {
                if (code === 0) {
                    this.log('debug', `npm更新输出: ${dependency.name}`, { output: output.substring(0, 500) });
                    resolve(true);
                } else {
                    this.log('error', `npm更新失败: ${dependency.name}`, { 
                        code,
                        error: errorOutput.substring(0, 500) 
                    });
                    reject(new Error(errorOutput));
                }
            });
        });
    }
    
    async updatePipPackage(dependency) {
        return new Promise((resolve, reject) => {
            const pip = spawn('pip', ['install', '--upgrade', `${dependency.name}==${dependency.latestVersion}`], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let output = '';
            let errorOutput = '';
            
            pip.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            pip.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            pip.on('close', (code) => {
                if (code === 0) {
                    this.log('debug', `pip更新输出: ${dependency.name}`, { output: output.substring(0, 500) });
                    resolve(true);
                } else {
                    this.log('error', `pip更新失败: ${dependency.name}`, { 
                        code,
                        error: errorOutput.substring(0, 500) 
                    });
                    reject(new Error(errorOutput));
                }
            });
        });
    }
    
    async updateSystemPackage(dependency) {
        // 系统包更新需要管理员权限，这里只是示例
        this.log('warn', `系统包更新需要手动执行: ${dependency.name}`);
        return false;
    }
    
    async rollbackDependency(dependency) {
        if (!dependency.backup) {
            this.log('warn', `没有可用的备份: ${dependency.name}`);
            return false;
        }
        
        this.log('info', `🔄 回滚依赖: ${dependency.name}`);
        
        try {
            const success = await this.restoreFromBackup(dependency);
            
            if (success) {
                this.metrics.rollbacks++;
                this.log('info', `✅ 依赖回滚成功: ${dependency.name}`);
                this.emit('dependency-rolled-back', dependency);
                return true;
            }
            
        } catch (error) {
            this.log('error', `依赖回滚失败: ${dependency.name}`, { error: error.message });
        }
        
        return false;
    }
    
    async restoreFromBackup(dependency) {
        // 简化实现：恢复到备份版本
        switch (dependency.manager) {
            case 'npm':
                return await this.updateNpmPackage({
                    ...dependency,
                    latestVersion: dependency.backup.dependency.currentVersion
                });
            case 'pip':
                return await this.updatePipPackage({
                    ...dependency,
                    latestVersion: dependency.backup.dependency.currentVersion
                });
            default:
                return false;
        }
    }
    
    determineUpdateType(currentVersion, latestVersion) {
        const current = currentVersion.replace(/[^0-9.]/g, '').split('.').map(Number);
        const latest = latestVersion.replace(/[^0-9.]/g, '').split('.').map(Number);
        
        if (latest[0] > current[0]) return 'major';
        if (latest[1] > current[1]) return 'minor';
        if (latest[2] > current[2]) return 'patch';
        
        return null;
    }
    
    isVersionOutdated(current, latest) {
        const currentNum = current.replace(/[^0-9.]/g, '').split('.').map(Number);
        const latestNum = latest.replace(/[^0-9.]/g, '').split('.').map(Number);
        
        for (let i = 0; i < Math.max(currentNum.length, latestNum.length); i++) {
            const curr = currentNum[i] || 0;
            const lat = latestNum[i] || 0;
            
            if (lat > curr) return true;
            if (lat < curr) return false;
        }
        
        return false;
    }
    
    getDependencyStatus(name) {
        for (const [key, dependency] of this.dependencies) {
            if (dependency.name === name) {
                return { ...dependency };
            }
        }
        return null;
    }
    
    getAllDependencies() {
        return Array.from(this.dependencies.values());
    }
    
    getUpdateQueue() {
        return [...this.updateQueue];
    }
    
    getMetrics() {
        const uptime = Date.now() - this.metrics.startTime;
        
        return {
            ...this.metrics,
            uptime,
            totalDependencies: this.dependencies.size,
            updatableDependencies: Array.from(this.dependencies.values()).filter(d => d.updateAvailable).length,
            securityIssues: Array.from(this.dependencies.values()).reduce((sum, d) => sum + d.securityIssues.length, 0),
            updateSuccessRate: this.metrics.updatesFound > 0 ? 
                (this.metrics.updatesApplied / this.metrics.updatesFound * 100).toFixed(2) + '%' : '0%'
        };
    }
    
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }
    
    log(level, message, meta = {}) {
        if (this.logger) {
            this.logger.log(level, message, { ...meta, component: 'DependencyManager' });
        } else {
            console.log(`[${level.toUpperCase()}] ${message}`, meta);
        }
    }
    
    setLogger(logger) {
        this.logger = logger;
    }
    
    async shutdown() {
        this.log('info', '🛑 关闭依赖项管理系统...');
        
        this.stopPeriodicCheck();
        
        this.log('info', '✅ 依赖项管理系统已关闭');
    }
}

module.exports = DependencyManager;
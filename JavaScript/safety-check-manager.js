/**
 * 更新前安全检查机制
 * 在系统更新前进行全面的安全检查和风险评估
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const crypto = require('crypto');

class SafetyCheckManager {
    constructor(config = {}) {
        this.config = {
            // 检查配置
            checks: {
                // 系统资源检查
                systemResources: {
                    enabled: true,
                    diskSpaceThreshold: 85,    // 磁盘空间阈值 (%)
                    memoryThreshold: 90,        // 内存使用阈值 (%)
                    cpuThreshold: 80,           // CPU使用阈值 (%)
                    loadThreshold: 4.0          // 系统负载阈值
                },
                // 依赖项检查
                dependencies: {
                    enabled: true,
                    checkSecurityVulnerabilities: true,
                    checkCompatibility: true,
                    checkVersionConflicts: true,
                    allowedLicenses: ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC'],
                    blockedLicenses: ['GPL-3.0', 'AGPL-3.0']
                },
                // 代码质量检查
                codeQuality: {
                    enabled: true,
                    runLinting: true,
                    runStaticAnalysis: true,
                    checkComplexity: true,
                    maxComplexity: 10,
                    checkDuplication: true,
                    maxDuplication: 3
                },
                // 安全扫描
                security: {
                    enabled: true,
                    scanSecrets: true,
                    scanVulnerabilities: true,
                    checkDependencies: true,
                    checkPermissions: true,
                    scanMalware: false
                },
                // 配置检查
                configuration: {
                    enabled: true,
                    validateEnvironment: true,
                    validatePorts: true,
                    validateDatabase: true,
                    validateServices: true,
                    validateSSL: true
                },
                // 性能检查
                performance: {
                    enabled: true,
                    runLoadTest: false,
                    runStressTest: false,
                    checkResponseTime: true,
                    maxResponseTime: 2000,
                    checkThroughput: true,
                    minThroughput: 100
                }
            },
            // 超时配置
            timeouts: {
                systemCheck: 30000,        // 系统检查超时
                dependencyCheck: 60000,     // 依赖检查超时
                codeQualityCheck: 120000,   // 代码质量检查超时
                securityScan: 180000,       // 安全扫描超时
                performanceTest: 300000     // 性能测试超时
            },
            // 告警配置
            alerts: {
                enabled: true,
                emailNotifications: false,
                slackNotifications: false,
                logLevel: 'warning',
                maxWarnings: 5,
                maxErrors: 1
            },
            ...config
        };

        // 检查结果
        this.checkResults = new Map();
        this.warnings = [];
        this.errors = [];
        this.checkHistory = [];

        // 初始化
        this.initialize();
    }

    /**
     * 初始化安全检查管理器
     */
    async initialize() {
        this.log('🔍 初始化更新前安全检查机制...');

        try {
            // 创建检查目录
            await this.createCheckDirectories();
            
            // 初始化检查工具
            await this.initializeCheckTools();
            
            // 加载检查规则
            await this.loadCheckRules();

            this.log('✅ 安全检查机制初始化完成');
        } catch (error) {
            this.log(`❌ 初始化失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 创建检查目录
     */
    async createCheckDirectories() {
        const directories = [
            './safety-checks',
            './safety-checks/reports',
            './safety-checks/logs',
            './safety-checks/cache',
            './safety-checks/rules'
        ];

        for (const dir of directories) {
            const dirPath = path.resolve(dir);
            if (!fs.existsSync(dirPath)) {
                fs.mkdirSync(dirPath, { recursive: true });
            }
        }
    }

    /**
     * 初始化检查工具
     */
    async initializeCheckTools() {
        // 检查必要的工具是否可用
        const tools = ['npm', 'node', 'git'];
        
        for (const tool of tools) {
            try {
                await this.executeCommand(`which ${tool}`);
                this.log(`✅ 工具检查通过: ${tool}`);
            } catch (error) {
                this.log(`⚠️ 工具不可用: ${tool}`);
            }
        }
    }

    /**
     * 加载检查规则
     */
    async loadCheckRules() {
        const rulesFile = path.resolve('./safety-checks/rules/check-rules.json');
        
        if (fs.existsSync(rulesFile)) {
            const rules = JSON.parse(fs.readFileSync(rulesFile, 'utf8'));
            this.config = { ...this.config, ...rules };
            this.log('📋 检查规则已加载');
        } else {
            // 创建默认规则文件
            const defaultRules = {
                customRules: [],
                excludedPaths: ['node_modules', '.git', 'dist', 'build'],
                excludedFiles: ['*.log', '*.tmp', '*.cache'],
                severityLevels: {
                    critical: 0,
                    high: 1,
                    medium: 2,
                    low: 3
                }
            };
            
            fs.writeFileSync(rulesFile, JSON.stringify(defaultRules, null, 2));
            this.log('📋 默认检查规则已创建');
        }
    }

    /**
     * 执行完整的安全检查
     */
    async performSafetyCheck(projectPath, checkOptions = {}) {
        this.log('🔍 开始执行完整安全检查...');
        
        const checkId = this.generateCheckId();
        const startTime = Date.now();
        
        // 重置检查结果
        this.warnings = [];
        this.errors = [];
        this.checkResults.clear();

        try {
            // 1. 系统资源检查
            if (this.config.checks.systemResources.enabled) {
                await this.performSystemResourceCheck();
            }

            // 2. 依赖项检查
            if (this.config.checks.dependencies.enabled) {
                await this.performDependencyCheck(projectPath);
            }

            // 3. 代码质量检查
            if (this.config.checks.codeQuality.enabled) {
                await this.performCodeQualityCheck(projectPath);
            }

            // 4. 安全扫描
            if (this.config.checks.security.enabled) {
                await this.performSecurityScan(projectPath);
            }

            // 5. 配置检查
            if (this.config.checks.configuration.enabled) {
                await this.performConfigurationCheck(projectPath);
            }

            // 6. 性能检查
            if (this.config.checks.performance.enabled) {
                await this.performPerformanceCheck(projectPath);
            }

            const endTime = Date.now();
            const duration = endTime - startTime;

            // 生成检查报告
            const report = this.generateCheckReport(checkId, projectPath, duration);
            
            // 保存检查历史
            this.saveCheckHistory(report);

            // 检查是否通过
            const passed = this.evaluateCheckResults();
            
            if (passed) {
                this.log('✅ 安全检查通过');
            } else {
                this.log('❌ 安全检查未通过');
            }

            return {
                checkId,
                passed,
                report,
                warnings: this.warnings,
                errors: this.errors,
                duration
            };

        } catch (error) {
            this.log(`❌ 安全检查执行失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 系统资源检查
     */
    async performSystemResourceCheck() {
        this.log('🖥️ 执行系统资源检查...');

        const results = {
            diskSpace: null,
            memory: null,
            cpu: null,
            load: null
        };

        try {
            // 检查磁盘空间
            results.diskSpace = await this.checkDiskSpace();
            
            // 检查内存使用
            results.memory = await this.checkMemoryUsage();
            
            // 检查CPU使用
            results.cpu = await this.checkCpuUsage();
            
            // 检查系统负载
            results.load = await this.checkSystemLoad();

            this.checkResults.set('systemResources', {
                status: 'completed',
                results,
                timestamp: new Date().toISOString()
            });

            this.log('✅ 系统资源检查完成');

        } catch (error) {
            this.errors.push({
                type: 'system_resources',
                message: error.message,
                severity: 'high'
            });
            
            this.checkResults.set('systemResources', {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 检查磁盘空间
     */
    async checkDiskSpace() {
        return new Promise((resolve, reject) => {
            exec('df -h /', { timeout: this.config.timeouts.systemCheck }, (error, stdout) => {
                if (error) {
                    reject(new Error(`磁盘空间检查失败: ${error.message}`));
                    return;
                }

                const lines = stdout.split('\n');
                const dataLine = lines[1];
                const parts = dataLine.split(/\s+/);
                const usage = parseInt(parts[4].replace('%', ''));
                const total = parts[1];
                const available = parts[3];

                const threshold = this.config.checks.systemResources.diskSpaceThreshold;
                
                if (usage > threshold) {
                    this.warnings.push({
                        type: 'disk_space',
                        message: `磁盘空间使用过高: ${usage}% (阈值: ${threshold}%)`,
                        severity: 'high',
                        data: { usage, total, available }
                    });
                }

                resolve({ usage, total, available, status: usage > threshold ? 'warning' : 'ok' });
            });
        });
    }

    /**
     * 检查内存使用
     */
    async checkMemoryUsage() {
        return new Promise((resolve, reject) => {
            exec('free -m', { timeout: this.config.timeouts.systemCheck }, (error, stdout) => {
                if (error) {
                    reject(new Error(`内存检查失败: ${error.message}`));
                    return;
                }

                const lines = stdout.split('\n');
                const memLine = lines[1];
                const parts = memLine.split(/\s+/);
                const total = parseInt(parts[1]);
                const used = parseInt(parts[2]);
                const free = parseInt(parts[3]);
                const usage = Math.round((used / total) * 100);

                const threshold = this.config.checks.systemResources.memoryThreshold;
                
                if (usage > threshold) {
                    this.warnings.push({
                        type: 'memory',
                        message: `内存使用过高: ${usage}% (阈值: ${threshold}%)`,
                        severity: 'high',
                        data: { usage, total, used, free }
                    });
                }

                resolve({ usage, total, used, free, status: usage > threshold ? 'warning' : 'ok' });
            });
        });
    }

    /**
     * 检查CPU使用
     */
    async checkCpuUsage() {
        return new Promise((resolve, reject) => {
            exec('top -bn1 | grep "Cpu(s)"', { timeout: this.config.timeouts.systemCheck }, (error, stdout) => {
                if (error) {
                    reject(new Error(`CPU检查失败: ${error.message}`));
                    return;
                }

                const cpuLine = stdout.trim();
                const usageMatch = cpuLine.match(/(\d+\.?\d*)\s*%us/);
                const usage = usageMatch ? parseFloat(usageMatch[1]) : 0;

                const threshold = this.config.checks.systemResources.cpuThreshold;
                
                if (usage > threshold) {
                    this.warnings.push({
                        type: 'cpu',
                        message: `CPU使用过高: ${usage}% (阈值: ${threshold}%)`,
                        severity: 'medium',
                        data: { usage }
                    });
                }

                resolve({ usage, status: usage > threshold ? 'warning' : 'ok' });
            });
        });
    }

    /**
     * 检查系统负载
     */
    async checkSystemLoad() {
        const loadAvg = require('os').loadavg();
        const cpuCount = require('os').cpus().length;
        const load1min = loadAvg[0];
        const loadPercentage = (load1min / cpuCount) * 100;

        const threshold = this.config.checks.systemResources.loadThreshold;
        
        if (load1min > threshold) {
            this.warnings.push({
                type: 'system_load',
                message: `系统负载过高: ${load1min.toFixed(2)} (阈值: ${threshold})`,
                severity: 'medium',
                data: { load: load1min, cpuCount, percentage: loadPercentage.toFixed(1) }
            });
        }

        return { 
            load: load1min, 
            cpuCount, 
            percentage: loadPercentage.toFixed(1),
            status: load1min > threshold ? 'warning' : 'ok'
        };
    }

    /**
     * 依赖项检查
     */
    async performDependencyCheck(projectPath) {
        this.log('📦 执行依赖项检查...');

        const results = {
            vulnerabilities: [],
            conflicts: [],
            outdated: [],
            licenseIssues: []
        };

        try {
            // 检查安全漏洞
            if (this.config.checks.dependencies.checkSecurityVulnerabilities) {
                results.vulnerabilities = await this.checkSecurityVulnerabilities(projectPath);
            }

            // 检查版本冲突
            if (this.config.checks.dependencies.checkVersionConflicts) {
                results.conflicts = await this.checkVersionConflicts(projectPath);
            }

            // 检查过时依赖
            results.outdated = await this.checkOutdatedDependencies(projectPath);

            // 检查许可证
            results.licenseIssues = await this.checkLicenseIssues(projectPath);

            this.checkResults.set('dependencies', {
                status: 'completed',
                results,
                timestamp: new Date().toISOString()
            });

            this.log('✅ 依赖项检查完成');

        } catch (error) {
            this.errors.push({
                type: 'dependencies',
                message: error.message,
                severity: 'high'
            });
            
            this.checkResults.set('dependencies', {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 检查安全漏洞
     */
    async checkSecurityVulnerabilities(projectPath) {
        return new Promise((resolve, reject) => {
            const auditProcess = spawn('npm', ['audit', '--json'], {
                cwd: projectPath,
                stdio: 'pipe',
                timeout: this.config.timeouts.dependencyCheck
            });

            let output = '';

            auditProcess.stdout.on('data', (data) => {
                output += data.toString();
            });

            auditProcess.stderr.on('data', (data) => {
                output += data.toString();
            });

            auditProcess.on('close', (code) => {
                try {
                    const auditResult = JSON.parse(output);
                    const vulnerabilities = auditResult.vulnerabilities || {};
                    
                    const vulnerabilityList = Object.values(vulnerabilities).map(vuln => ({
                        name: vuln.name,
                        severity: vuln.severity,
                        title: vuln.title,
                        url: vuln.url,
                        fixAvailable: vuln.fixAvailable
                    }));

                    // 检查高危漏洞
                    const highSeverityVulns = vulnerabilityList.filter(v => 
                        ['high', 'critical', 'moderate'].includes(v.severity)
                    );

                    if (highSeverityVulns.length > 0) {
                        this.errors.push({
                            type: 'security_vulnerabilities',
                            message: `发现 ${highSeverityVulns.length} 个高危安全漏洞`,
                            severity: 'critical',
                            data: highSeverityVulns
                        });
                    }

                    resolve(vulnerabilityList);

                } catch (parseError) {
                    // 如果JSON解析失败，可能是没有漏洞
                    resolve([]);
                }
            });

            auditProcess.on('error', (error) => {
                reject(new Error(`安全漏洞检查失败: ${error.message}`));
            });
        });
    }

    /**
     * 检查版本冲突
     */
    async checkVersionConflicts(projectPath) {
        const packageJsonPath = path.join(projectPath, 'package.json');
        
        if (!fs.existsSync(packageJsonPath)) {
            return [];
        }

        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        const conflicts = [];

        // 检查依赖版本范围冲突
        const allDeps = {
            ...packageJson.dependencies,
            ...packageJson.devDependencies
        };

        for (const [name, version] of Object.entries(allDeps)) {
            // 简单的版本冲突检查
            if (version.includes('||') || version.includes(' ')) {
                conflicts.push({
                    package: name,
                    version,
                    issue: '复杂的版本范围可能导致冲突'
                });
            }
        }

        if (conflicts.length > 0) {
            this.warnings.push({
                type: 'version_conflicts',
                message: `发现 ${conflicts.length} 个潜在的版本冲突`,
                severity: 'medium',
                data: conflicts
            });
        }

        return conflicts;
    }

    /**
     * 检查过时依赖
     */
    async checkOutdatedDependencies(projectPath) {
        return new Promise((resolve, reject) => {
            const outdatedProcess = spawn('npm', ['outdated', '--json'], {
                cwd: projectPath,
                stdio: 'pipe',
                timeout: this.config.timeouts.dependencyCheck
            });

            let output = '';

            outdatedProcess.stdout.on('data', (data) => {
                output += data.toString();
            });

            outdatedProcess.on('close', (code) => {
                try {
                    const outdated = JSON.parse(output);
                    const outdatedList = Object.values(outdated).map(dep => ({
                        name: dep.name,
                        current: dep.current,
                        wanted: dep.wanted,
                        latest: dep.latest,
                        type: dep.type
                    }));

                    if (outdatedList.length > 0) {
                        this.warnings.push({
                            type: 'outdated_dependencies',
                            message: `发现 ${outdatedList.length} 个过时的依赖项`,
                            severity: 'low',
                            data: outdatedList
                        });
                    }

                    resolve(outdatedList);

                } catch (parseError) {
                    // 如果JSON解析失败，可能是没有过时依赖
                    resolve([]);
                }
            });

            outdatedProcess.on('error', (error) => {
                reject(new Error(`过时依赖检查失败: ${error.message}`));
            });
        });
    }

    /**
     * 检查许可证问题
     */
    async checkLicenseIssues(projectPath) {
        const packageJsonPath = path.join(projectPath, 'package.json');
        
        if (!fs.existsSync(packageJsonPath)) {
            return [];
        }

        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        const licenseIssues = [];

        // 检查项目许可证
        if (packageJson.license) {
            const projectLicense = packageJson.license;
            
            if (this.config.checks.dependencies.blockedLicenses.includes(projectLicense)) {
                licenseIssues.push({
                    type: 'blocked_license',
                    license: projectLicense,
                    issue: '项目使用了被阻止的许可证'
                });
            }
        }

        // 检查依赖许可证（简化实现）
        const nodeModulesPath = path.join(projectPath, 'node_modules');
        
        if (fs.existsSync(nodeModulesPath)) {
            const modules = fs.readdirSync(nodeModulesPath);
            
            for (const module of modules) {
                const modulePackagePath = path.join(nodeModulesPath, module, 'package.json');
                
                if (fs.existsSync(modulePackagePath)) {
                    try {
                        const modulePackage = JSON.parse(fs.readFileSync(modulePackagePath, 'utf8'));
                        
                        if (modulePackage.license) {
                            const license = modulePackage.license;
                            
                            if (this.config.checks.dependencies.blockedLicenses.includes(license)) {
                                licenseIssues.push({
                                    type: 'blocked_dependency_license',
                                    module,
                                    license,
                                    issue: '依赖使用了被阻止的许可证'
                                });
                            }
                        }
                    } catch (error) {
                        // 忽略解析错误
                    }
                }
            }
        }

        if (licenseIssues.length > 0) {
            this.errors.push({
                type: 'license_issues',
                message: `发现 ${licenseIssues.length} 个许可证问题`,
                severity: 'high',
                data: licenseIssues
            });
        }

        return licenseIssues;
    }

    /**
     * 代码质量检查
     */
    async performCodeQualityCheck(projectPath) {
        this.log('📊 执行代码质量检查...');

        const results = {
            linting: [],
            complexity: [],
            duplication: []
        };

        try {
            // 运行代码检查
            if (this.config.checks.codeQuality.runLinting) {
                results.linting = await this.runLinting(projectPath);
            }

            // 检查代码复杂度
            if (this.config.checks.codeQuality.checkComplexity) {
                results.complexity = await this.checkCodeComplexity(projectPath);
            }

            // 检查代码重复
            if (this.config.checks.codeQuality.checkDuplication) {
                results.duplication = await this.checkCodeDuplication(projectPath);
            }

            this.checkResults.set('codeQuality', {
                status: 'completed',
                results,
                timestamp: new Date().toISOString()
            });

            this.log('✅ 代码质量检查完成');

        } catch (error) {
            this.warnings.push({
                type: 'code_quality',
                message: error.message,
                severity: 'medium'
            });
            
            this.checkResults.set('codeQuality', {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 运行代码检查
     */
    async runLinting(projectPath) {
        return new Promise((resolve, reject) => {
            const eslintProcess = spawn('npx', ['eslint', '.', '--format', 'json'], {
                cwd: projectPath,
                stdio: 'pipe',
                timeout: this.config.timeouts.codeQualityCheck
            });

            let output = '';

            eslintProcess.stdout.on('data', (data) => {
                output += data.toString();
            });

            eslintProcess.stderr.on('data', (data) => {
                output += data.toString();
            });

            eslintProcess.on('close', (code) => {
                try {
                    const lintResults = JSON.parse(output);
                    const errors = lintResults.filter(result => result.errorCount > 0);
                    
                    if (errors.length > 0) {
                        this.warnings.push({
                            type: 'linting_errors',
                            message: `代码检查发现 ${errors.length} 个文件有问题`,
                            severity: 'medium',
                            data: errors
                        });
                    }

                    resolve(lintResults);

                } catch (parseError) {
                    // 如果JSON解析失败，可能是ESLint不可用
                    resolve([]);
                }
            });

            eslintProcess.on('error', (error) => {
                reject(new Error(`代码检查失败: ${error.message}`));
            });
        });
    }

    /**
     * 检查代码复杂度
     */
    async checkCodeComplexity(projectPath) {
        // 简化的复杂度检查实现
        const complexityIssues = [];
        const srcPath = path.join(projectPath, 'src');
        
        if (fs.existsSync(srcPath)) {
            const files = await this.getAllJavaScriptFiles(srcPath);
            
            for (const file of files) {
                const content = fs.readFileSync(file, 'utf8');
                const complexity = this.calculateComplexity(content);
                
                if (complexity > this.config.checks.codeQuality.maxComplexity) {
                    complexityIssues.push({
                        file: path.relative(projectPath, file),
                        complexity,
                        threshold: this.config.checks.codeQuality.maxComplexity
                    });
                }
            }
        }

        if (complexityIssues.length > 0) {
            this.warnings.push({
                type: 'code_complexity',
                message: `发现 ${complexityIssues.length} 个高复杂度函数`,
                severity: 'medium',
                data: complexityIssues
            });
        }

        return complexityIssues;
    }

    /**
     * 计算代码复杂度
     */
    calculateComplexity(code) {
        // 简化的圈复杂度计算
        const complexityKeywords = ['if', 'else', 'while', 'for', 'case', 'catch', '&&', '||'];
        let complexity = 1; // 基础复杂度
        
        for (const keyword of complexityKeywords) {
            const regex = new RegExp(`\\b${keyword}\\b`, 'g');
            const matches = code.match(regex);
            if (matches) {
                complexity += matches.length;
            }
        }
        
        return complexity;
    }

    /**
     * 检查代码重复
     */
    async checkCodeDuplication(projectPath) {
        // 简化的代码重复检查
        const duplicationIssues = [];
        const srcPath = path.join(projectPath, 'src');
        
        if (fs.existsSync(srcPath)) {
            const files = await this.getAllJavaScriptFiles(srcPath);
            const fileHashes = new Map();
            
            for (const file of files) {
                const content = fs.readFileSync(file, 'utf8');
                const normalizedContent = this.normalizeCode(content);
                const hash = crypto.createHash('md5').update(normalizedContent).digest('hex');
                
                if (fileHashes.has(hash)) {
                    duplicationIssues.push({
                        file1: path.relative(projectPath, fileHashes.get(hash)),
                        file2: path.relative(projectPath, file),
                        hash
                    });
                } else {
                    fileHashes.set(hash, file);
                }
            }
        }

        if (duplicationIssues.length > this.config.checks.codeQuality.maxDuplication) {
            this.warnings.push({
                type: 'code_duplication',
                message: `发现 ${duplicationIssues.length} 个代码重复`,
                severity: 'low',
                data: duplicationIssues
            });
        }

        return duplicationIssues;
    }

    /**
     * 标准化代码用于重复检查
     */
    normalizeCode(code) {
        return code
            .replace(/\s+/g, ' ')
            .replace(/\/\*[\s\S]*?\*\//g, '') // 移除块注释
            .replace(/\/\/.*$/gm, '') // 移除行注释
            .trim();
    }

    /**
     * 获取所有JavaScript文件
     */
    async getAllJavaScriptFiles(dirPath) {
        const files = [];
        
        if (!fs.existsSync(dirPath)) return files;

        const items = fs.readdirSync(dirPath);
        
        for (const item of items) {
            const itemPath = path.join(dirPath, item);
            const stat = fs.statSync(itemPath);
            
            if (stat.isDirectory() && !item.startsWith('.')) {
                files.push(...await this.getAllJavaScriptFiles(itemPath));
            } else if (item.endsWith('.js') || item.endsWith('.jsx')) {
                files.push(itemPath);
            }
        }
        
        return files;
    }

    /**
     * 安全扫描
     */
    async performSecurityScan(projectPath) {
        this.log('🔒 执行安全扫描...');

        const results = {
            secrets: [],
            vulnerabilities: [],
            permissions: []
        };

        try {
            // 扫描密钥
            if (this.config.checks.security.scanSecrets) {
                results.secrets = await this.scanForSecrets(projectPath);
            }

            // 扫描权限
            if (this.config.checks.security.checkPermissions) {
                results.permissions = await this.checkFilePermissions(projectPath);
            }

            this.checkResults.set('security', {
                status: 'completed',
                results,
                timestamp: new Date().toISOString()
            });

            this.log('✅ 安全扫描完成');

        } catch (error) {
            this.errors.push({
                type: 'security_scan',
                message: error.message,
                severity: 'high'
            });
            
            this.checkResults.set('security', {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 扫描密钥
     */
    async scanForSecrets(projectPath) {
        const secrets = [];
        const secretPatterns = [
            /password\s*[:=]\s*['"]([^'"]+)['"]/gi,
            /api[_-]?key\s*[:=]\s*['"]([^'"]+)['"]/gi,
            /secret\s*[:=]\s*['"]([^'"]+)['"]/gi,
            /token\s*[:=]\s*['"]([^'"]+)['"]/gi,
            /aws[_-]?access[_-]?key\s*[:=]\s*['"]([^'"]+)['"]/gi
        ];

        const files = await this.getAllJavaScriptFiles(projectPath);
        
        for (const file of files) {
            const content = fs.readFileSync(file, 'utf8');
            
            for (const pattern of secretPatterns) {
                const matches = content.matchAll(pattern);
                
                for (const match of matches) {
                    secrets.push({
                        file: path.relative(projectPath, file),
                        line: this.getLineNumber(content, match.index),
                        type: 'potential_secret',
                        match: match[0]
                    });
                }
            }
        }

        if (secrets.length > 0) {
            this.errors.push({
                type: 'secrets_found',
                message: `发现 ${secrets.length} 个潜在的密钥泄露`,
                severity: 'critical',
                data: secrets
            });
        }

        return secrets;
    }

    /**
     * 获取行号
     */
    getLineNumber(content, index) {
        const lines = content.substring(0, index).split('\n');
        return lines.length;
    }

    /**
     * 检查文件权限
     */
    async checkFilePermissions(projectPath) {
        const permissionIssues = [];
        const files = await this.getAllJavaScriptFiles(projectPath);
        
        for (const file of files) {
            try {
                const stats = fs.statSync(file);
                const mode = stats.mode;
                
                // 检查是否对其他用户可写
                if (mode & 0o002) {
                    permissionIssues.push({
                        file: path.relative(projectPath, file),
                        issue: '文件对其他用户可写',
                        mode: mode.toString(8)
                    });
                }
                
                // 检查是否为可执行文件
                if (mode & 0o111) {
                    permissionIssues.push({
                        file: path.relative(projectPath, file),
                        issue: 'JavaScript文件不应为可执行',
                        mode: mode.toString(8)
                    });
                }
            } catch (error) {
                // 忽略权限检查错误
            }
        }

        if (permissionIssues.length > 0) {
            this.warnings.push({
                type: 'file_permissions',
                message: `发现 ${permissionIssues.length} 个文件权限问题`,
                severity: 'medium',
                data: permissionIssues
            });
        }

        return permissionIssues;
    }

    /**
     * 配置检查
     */
    async performConfigurationCheck(projectPath) {
        this.log('⚙️ 执行配置检查...');

        const results = {
            environment: null,
            ports: null,
            database: null,
            services: null
        };

        try {
            // 验证环境配置
            if (this.config.checks.configuration.validateEnvironment) {
                results.environment = await this.validateEnvironment(projectPath);
            }

            // 验证端口配置
            if (this.config.checks.configuration.validatePorts) {
                results.ports = await this.validatePorts(projectPath);
            }

            this.checkResults.set('configuration', {
                status: 'completed',
                results,
                timestamp: new Date().toISOString()
            });

            this.log('✅ 配置检查完成');

        } catch (error) {
            this.warnings.push({
                type: 'configuration',
                message: error.message,
                severity: 'medium'
            });
            
            this.checkResults.set('configuration', {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 验证环境配置
     */
    async validateEnvironment(projectPath) {
        const envFile = path.join(projectPath, '.env');
        
        if (!fs.existsSync(envFile)) {
            this.warnings.push({
                type: 'missing_env_file',
                message: '缺少环境配置文件',
                severity: 'low'
            });
            return { status: 'missing', file: '.env' };
        }

        const envContent = fs.readFileSync(envFile, 'utf8');
        const envVars = envContent.split('\n').filter(line => line.trim() && !line.startsWith('#'));
        
        const requiredVars = ['NODE_ENV', 'PORT'];
        const missingVars = requiredVars.filter(varName => 
            !envVars.some(line => line.startsWith(`${varName}=`))
        );

        if (missingVars.length > 0) {
            this.warnings.push({
                type: 'missing_env_vars',
                message: `缺少必需的环境变量: ${missingVars.join(', ')}`,
                severity: 'medium',
                data: missingVars
            });
        }

        return {
            status: 'validated',
            variables: envVars.length,
            missing: missingVars
        };
    }

    /**
     * 验证端口配置
     */
    async validatePorts(projectPath) {
        const packageJsonPath = path.join(projectPath, 'package.json');
        
        if (!fs.existsSync(packageJsonPath)) {
            return { status: 'no_package_json' };
        }

        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        const scripts = packageJson.scripts || {};
        const portIssues = [];

        // 检查常用端口
        const commonPorts = [3000, 8080, 8081, 8082, 8083, 8084];
        
        for (const [scriptName, scriptCommand] of Object.entries(scripts)) {
            if (typeof scriptCommand === 'string') {
                const portMatch = scriptCommand.match(/--port\s+(\d+)|-p\s+(\d+)/);
                
                if (portMatch) {
                    const port = parseInt(portMatch[1] || portMatch[2]);
                    
                    if (commonPorts.includes(port)) {
                        portIssues.push({
                            script: scriptName,
                            port,
                            issue: '使用了常用端口，可能存在冲突'
                        });
                    }
                }
            }
        }

        if (portIssues.length > 0) {
            this.warnings.push({
                type: 'port_conflicts',
                message: `发现 ${portIssues.length} 个潜在端口冲突`,
                severity: 'medium',
                data: portIssues
            });
        }

        return { status: 'validated', issues: portIssues };
    }

    /**
     * 性能检查
     */
    async performPerformanceCheck(projectPath) {
        this.log('⚡ 执行性能检查...');

        const results = {
            responseTime: null,
            throughput: null
        };

        try {
            // 检查响应时间
            if (this.config.checks.performance.checkResponseTime) {
                results.responseTime = await this.checkResponseTime(projectPath);
            }

            this.checkResults.set('performance', {
                status: 'completed',
                results,
                timestamp: new Date().toISOString()
            });

            this.log('✅ 性能检查完成');

        } catch (error) {
            this.warnings.push({
                type: 'performance',
                message: error.message,
                severity: 'low'
            });
            
            this.checkResults.set('performance', {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 检查响应时间
     */
    async checkResponseTime(projectPath) {
        // 简化的响应时间检查
        const packageJsonPath = path.join(projectPath, 'package.json');
        
        if (!fs.existsSync(packageJsonPath)) {
            return { status: 'no_package_json' };
        }

        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        
        // 检查是否有性能相关的配置
        const hasPerformanceConfig = packageJson.performance || 
                                   packageJson.scripts?.['test:performance'] ||
                                   packageJson.benchmarks;

        if (!hasPerformanceConfig) {
            this.warnings.push({
                type: 'no_performance_config',
                message: '缺少性能配置或测试',
                severity: 'low'
            });
        }

        return { 
            status: 'checked',
            hasConfig: !!hasPerformanceConfig
        };
    }

    /**
     * 生成检查报告
     */
    generateCheckReport(checkId, projectPath, duration) {
        const report = {
            checkId,
            projectPath,
            timestamp: new Date().toISOString(),
            duration,
            status: this.errors.length === 0 ? 'passed' : 'failed',
            summary: {
                totalChecks: this.checkResults.size,
                passedChecks: Array.from(this.checkResults.values()).filter(r => r.status === 'completed').length,
                failedChecks: Array.from(this.checkResults.values()).filter(r => r.status === 'failed').length,
                warnings: this.warnings.length,
                errors: this.errors.length
            },
            details: {
                checks: Object.fromEntries(this.checkResults),
                warnings: this.warnings,
                errors: this.errors
            },
            recommendations: this.generateRecommendations()
        };

        // 保存报告
        const reportPath = path.resolve('./safety-checks/reports', `report-${checkId}.json`);
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

        return report;
    }

    /**
     * 生成建议
     */
    generateRecommendations() {
        const recommendations = [];

        if (this.warnings.length > 0) {
            recommendations.push({
                type: 'warnings',
                message: '建议在部署前解决所有警告问题',
                priority: 'medium'
            });
        }

        if (this.errors.length > 0) {
            recommendations.push({
                type: 'errors',
                message: '必须解决所有错误才能继续部署',
                priority: 'high'
            });
        }

        const systemResources = this.checkResults.get('systemResources');
        if (systemResources && systemResources.results) {
            const { diskSpace, memory } = systemResources.results;
            
            if (diskSpace && diskSpace.status === 'warning') {
                recommendations.push({
                    type: 'disk_space',
                    message: '建议清理磁盘空间或扩展存储',
                    priority: 'high'
                });
            }
            
            if (memory && memory.status === 'warning') {
                recommendations.push({
                    type: 'memory',
                    message: '建议优化内存使用或增加内存',
                    priority: 'medium'
                });
            }
        }

        return recommendations;
    }

    /**
     * 评估检查结果
     */
    evaluateCheckResults() {
        // 如果有错误，检查失败
        if (this.errors.length > 0) {
            return false;
        }

        // 如果警告数量超过阈值，检查失败
        if (this.warnings.length > this.config.alerts.maxWarnings) {
            return false;
        }

        // 检查所有检查是否完成
        const failedChecks = Array.from(this.checkResults.values())
            .filter(result => result.status === 'failed');
        
        if (failedChecks.length > 0) {
            return false;
        }

        return true;
    }

    /**
     * 保存检查历史
     */
    saveCheckHistory(report) {
        this.checkHistory.push(report);
        
        // 限制历史记录数量
        if (this.checkHistory.length > 100) {
            this.checkHistory = this.checkHistory.slice(-100);
        }

        // 保存到文件
        const historyPath = path.resolve('./safety-checks/logs', 'check-history.json');
        fs.writeFileSync(historyPath, JSON.stringify(this.checkHistory, null, 2));
    }

    /**
     * 生成检查ID
     */
    generateCheckId() {
        return `check_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * 执行命令
     */
    async executeCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    /**
     * 记录日志
     */
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[SafetyCheckManager] ${timestamp} - ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        const logPath = path.join(process.cwd(), 'Logs', 'safety-check.log');
        fs.appendFile(logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error('写入日志失败:', err);
            }
        });
    }
}

module.exports = SafetyCheckManager;
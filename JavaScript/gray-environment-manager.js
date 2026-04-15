/**
 * 灰色测试环境管理系统
 * 防治系统更新混乱异常而导致项目崩溃
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const crypto = require('crypto');

class GrayEnvironmentManager {
    constructor(config = {}) {
        this.config = {
            // 环境配置
            environments: {
                production: {
                    path: './production',
                    port: 8081,
                    priority: 'high',
                    backupRequired: true
                },
                staging: {
                    path: './staging',
                    port: 8082,
                    priority: 'medium',
                    backupRequired: true
                },
                gray: {
                    path: './gray',
                    port: 8083,
                    priority: 'low',
                    backupRequired: false
                },
                development: {
                    path: './development',
                    port: 8084,
                    priority: 'low',
                    backupRequired: false
                }
            },
            // 安全检查配置
            safetyChecks: {
                diskSpaceThreshold: 85, // 磁盘空间阈值
                memoryThreshold: 90,   // 内存使用阈值
                testTimeout: 300000,   // 测试超时时间 (5分钟)
                rollbackTimeout: 60000  // 回滚超时时间 (1分钟)
            },
            // 监控配置
            monitoring: {
                healthCheckInterval: 30000,  // 健康检查间隔
                logRetentionDays: 30,         // 日志保留天数
                alertThreshold: 3             // 告警阈值
            },
            ...config
        };

        // 环境状态
        this.environmentStatus = {};
        this.deploymentHistory = [];
        this.rollbackStack = [];
        this.activeTests = new Map();
        this.alerts = [];

        // 初始化环境
        this.initializeEnvironments();
    }

    /**
     * 初始化所有环境
     */
    async initializeEnvironments() {
        this.log('🚀 初始化灰色测试环境管理系统...');

        try {
            // 创建环境目录
            for (const [envName, envConfig] of Object.entries(this.config.environments)) {
                await this.createEnvironment(envName, envConfig);
            }

            // 初始化监控
            this.startMonitoring();

            // 检查环境状态
            await this.checkAllEnvironments();

            this.log('✅ 灰色测试环境管理系统初始化完成');
        } catch (error) {
            this.log(`❌ 初始化失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 创建环境
     */
    async createEnvironment(envName, envConfig) {
        const envPath = path.resolve(envConfig.path);
        
        // 创建环境目录
        if (!fs.existsSync(envPath)) {
            fs.mkdirSync(envPath, { recursive: true });
            this.log(`📁 创建环境目录: ${envPath}`);
        }

        // 创建环境配置文件
        const envConfigFile = path.join(envPath, '.env-config.json');
        const configData = {
            name: envName,
            path: envPath,
            port: envConfig.port,
            priority: envConfig.priority,
            backupRequired: envConfig.backupRequired,
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            version: '1.0.0',
            status: 'initialized'
        };

        fs.writeFileSync(envConfigFile, JSON.stringify(configData, null, 2));

        // 创建必要的子目录
        const subdirs = ['backups', 'logs', 'temp', 'tests'];
        for (const subdir of subdirs) {
            const subdirPath = path.join(envPath, subdir);
            if (!fs.existsSync(subdirPath)) {
                fs.mkdirSync(subdirPath, { recursive: true });
            }
        }

        this.environmentStatus[envName] = {
            ...configData,
            isRunning: false,
            healthScore: 100,
            lastHealthCheck: null
        };

        this.log(`✅ 环境 ${envName} 创建完成`);
    }

    /**
     * 部署到灰色环境
     */
    async deployToGray(sourcePath, deploymentConfig = {}) {
        const deploymentId = this.generateDeploymentId();
        const grayEnv = this.config.environments.gray;
        
        this.log(`🚀 开始部署到灰色环境: ${deploymentId}`);

        try {
            // 1. 部署前安全检查
            await this.performPreDeploymentChecks();

            // 2. 备份当前版本
            const backupPath = await this.createBackup('gray', deploymentId);

            // 3. 复制文件到灰色环境
            await this.copyFiles(sourcePath, grayEnv.path);

            // 4. 安装依赖
            await this.installDependencies(grayEnv.path);

            // 5. 运行自动化测试
            const testResults = await this.runAutomatedTests(grayEnv.path);

            // 6. 启动灰色环境服务
            await this.startEnvironment('gray');

            // 7. 健康检查
            const healthCheck = await this.performHealthCheck('gray');

            // 记录部署历史
            const deployment = {
                id: deploymentId,
                environment: 'gray',
                sourcePath,
                backupPath,
                testResults,
                healthCheck,
                timestamp: new Date().toISOString(),
                status: 'success'
            };

            this.deploymentHistory.push(deployment);
            this.log(`✅ 灰色环境部署成功: ${deploymentId}`);

            return deployment;

        } catch (error) {
            this.log(`❌ 灰色环境部署失败: ${error.message}`);
            
            // 自动回滚
            await this.rollbackDeployment('gray', deploymentId);
            
            throw error;
        }
    }

    /**
     * 部署前安全检查
     */
    async performPreDeploymentChecks() {
        this.log('🔍 执行部署前安全检查...');

        const checks = [
            this.checkDiskSpace(),
            this.checkMemoryUsage(),
            this.checkSystemResources(),
            this.validateDependencies(),
            this.checkPortsAvailability()
        ];

        const results = await Promise.allSettled(checks);
        const failures = results.filter(result => result.status === 'rejected');

        if (failures.length > 0) {
            const errors = failures.map(f => f.reason.message);
            throw new Error(`安全检查失败: ${errors.join(', ')}`);
        }

        this.log('✅ 安全检查通过');
    }

    /**
     * 检查磁盘空间
     */
    async checkDiskSpace() {
        return new Promise((resolve, reject) => {
            exec('df -h /', (error, stdout) => {
                if (error) {
                    reject(new Error(`磁盘空间检查失败: ${error.message}`));
                    return;
                }

                const lines = stdout.split('\n');
                const dataLine = lines[1];
                const parts = dataLine.split(/\s+/);
                const usage = parseInt(parts[4].replace('%', ''));

                if (usage > this.config.safetyChecks.diskSpaceThreshold) {
                    reject(new Error(`磁盘空间不足: ${usage}%`));
                } else {
                    resolve({ usage, status: 'ok' });
                }
            });
        });
    }

    /**
     * 检查内存使用
     */
    async checkMemoryUsage() {
        return new Promise((resolve, reject) => {
            exec('free -m', (error, stdout) => {
                if (error) {
                    reject(new Error(`内存检查失败: ${error.message}`));
                    return;
                }

                const lines = stdout.split('\n');
                const memLine = lines[1];
                const parts = memLine.split(/\s+/);
                const total = parseInt(parts[1]);
                const used = parseInt(parts[2]);
                const usage = Math.round((used / total) * 100);

                if (usage > this.config.safetyChecks.memoryThreshold) {
                    reject(new Error(`内存使用过高: ${usage}%`));
                } else {
                    resolve({ usage, total, used, status: 'ok' });
                }
            });
        });
    }

    /**
     * 检查系统资源
     */
    async checkSystemResources() {
        const loadAvg = require('os').loadavg();
        const cpuCount = require('os').cpus().length;
        const loadPercentage = (loadAvg[0] / cpuCount) * 100;

        if (loadPercentage > 80) {
            throw new Error(`系统负载过高: ${loadPercentage.toFixed(1)}%`);
        }

        return { loadAvg, cpuCount, loadPercentage: loadPercentage.toFixed(1) };
    }

    /**
     * 验证依赖项
     */
    async validateDependencies() {
        const packageJsonPath = path.join(process.cwd(), 'package.json');
        
        if (!fs.existsSync(packageJsonPath)) {
            throw new Error('package.json 文件不存在');
        }

        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        
        // 检查是否有版本冲突
        const conflicts = await this.checkDependencyConflicts(packageJson);
        
        if (conflicts.length > 0) {
            throw new Error(`依赖项冲突: ${conflicts.join(', ')}`);
        }

        return { packageJson, conflicts: [] };
    }

    /**
     * 检查端口可用性
     */
    async checkPortsAvailability() {
        const usedPorts = [];
        
        for (const [envName, envConfig] of Object.entries(this.config.environments)) {
            const isAvailable = await this.isPortAvailable(envConfig.port);
            if (!isAvailable) {
                usedPorts.push(envConfig.port);
            }
        }

        if (usedPorts.length > 0) {
            throw new Error(`端口已被占用: ${usedPorts.join(', ')}`);
        }

        return { availablePorts: Object.values(this.config.environments).map(e => e.port) };
    }

    /**
     * 检查端口是否可用
     */
    async isPortAvailable(port) {
        return new Promise((resolve) => {
            const server = require('net').createServer();
            
            server.listen(port, () => {
                server.once('close', () => resolve(true));
                server.close();
            });
            
            server.on('error', () => resolve(false));
        });
    }

    /**
     * 创建备份
     */
    async createBackup(environment, deploymentId) {
        const envConfig = this.config.environments[environment];
        const backupDir = path.join(envConfig.path, 'backups');
        const backupName = `backup_${deploymentId}_${Date.now()}`;
        const backupPath = path.join(backupDir, backupName);

        this.log(`💾 创建备份: ${backupName}`);

        // 创建备份目录
        fs.mkdirSync(backupPath, { recursive: true });

        // 复制当前环境文件
        await this.copyDirectory(envConfig.path, backupPath, [path.join(backupDir, backupName)]);

        // 创建备份元数据
        const metadata = {
            deploymentId,
            environment,
            backupPath,
            timestamp: new Date().toISOString(),
            files: await this.getDirectoryFiles(envConfig.path)
        };

        fs.writeFileSync(
            path.join(backupPath, 'backup-metadata.json'),
            JSON.stringify(metadata, null, 2)
        );

        this.log(`✅ 备份创建完成: ${backupPath}`);
        return backupPath;
    }

    /**
     * 复制文件
     */
    async copyFiles(sourcePath, targetPath) {
        this.log(`📁 复制文件: ${sourcePath} -> ${targetPath}`);

        // 清空目标目录（保留配置文件）
        await this.cleanTargetDirectory(targetPath);

        // 复制源文件
        await this.copyDirectory(sourcePath, targetPath);

        this.log('✅ 文件复制完成');
    }

    /**
     * 清空目标目录
     */
    async cleanTargetDirectory(targetPath) {
        const excludeFiles = ['.env-config.json', 'backups', 'logs'];
        
        if (fs.existsSync(targetPath)) {
            const files = fs.readdirSync(targetPath);
            
            for (const file of files) {
                if (!excludeFiles.includes(file)) {
                    const filePath = path.join(targetPath, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        fs.rmSync(filePath, { recursive: true, force: true });
                    } else {
                        fs.unlinkSync(filePath);
                    }
                }
            }
        }
    }

    /**
     * 复制目录
     */
    async copyDirectory(source, target, exclude = []) {
        if (!fs.existsSync(source)) return;

        if (!fs.existsSync(target)) {
            fs.mkdirSync(target, { recursive: true });
        }

        const files = fs.readdirSync(source);
        
        for (const file of files) {
            const sourcePath = path.join(source, file);
            const targetPath = path.join(target, file);
            
            // 检查是否在排除列表中
            const shouldExclude = exclude.some(excludePath => 
                sourcePath.startsWith(excludePath)
            );
            
            if (shouldExclude) continue;

            const stat = fs.statSync(sourcePath);
            
            if (stat.isDirectory()) {
                await this.copyDirectory(sourcePath, targetPath, exclude);
            } else {
                fs.copyFileSync(sourcePath, targetPath);
            }
        }
    }

    /**
     * 获取目录文件列表
     */
    async getDirectoryFiles(dirPath, relativePath = '') {
        const files = [];
        
        if (!fs.existsSync(dirPath)) return files;

        const items = fs.readdirSync(dirPath);
        
        for (const item of items) {
            const itemPath = path.join(dirPath, item);
            const itemRelativePath = path.join(relativePath, item);
            const stat = fs.statSync(itemPath);
            
            if (stat.isDirectory()) {
                files.push(...await this.getDirectoryFiles(itemPath, itemRelativePath));
            } else {
                files.push({
                    path: itemRelativePath,
                    size: stat.size,
                    hash: this.calculateFileHash(itemPath)
                });
            }
        }
        
        return files;
    }

    /**
     * 计算文件哈希
     */
    calculateFileHash(filePath) {
        const fileContent = fs.readFileSync(filePath);
        return crypto.createHash('md5').update(fileContent).digest('hex');
    }

    /**
     * 安装依赖
     */
    async installDependencies(envPath) {
        this.log('📦 安装依赖项...');

        return new Promise((resolve, reject) => {
            const npmInstall = spawn('npm', ['install'], {
                cwd: envPath,
                stdio: 'pipe'
            });

            let output = '';
            let errorOutput = '';

            npmInstall.stdout.on('data', (data) => {
                output += data.toString();
            });

            npmInstall.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });

            npmInstall.on('close', (code) => {
                if (code === 0) {
                    this.log('✅ 依赖项安装完成');
                    resolve({ output });
                } else {
                    reject(new Error(`依赖项安装失败: ${errorOutput}`));
                }
            });

            npmInstall.on('error', (error) => {
                reject(new Error(`依赖项安装错误: ${error.message}`));
            });
        });
    }

    /**
     * 运行自动化测试
     */
    async runAutomatedTests(envPath) {
        this.log('🧪 运行自动化测试...');

        const testResults = {
            unit: { passed: 0, failed: 0, errors: [] },
            integration: { passed: 0, failed: 0, errors: [] },
            performance: { passed: 0, failed: 0, errors: [] }
        };

        try {
            // 运行单元测试
            await this.runTestSuite('unit', envPath, testResults);
            
            // 运行集成测试
            await this.runTestSuite('integration', envPath, testResults);
            
            // 运行性能测试
            await this.runTestSuite('performance', envPath, testResults);

            const totalPassed = Object.values(testResults).reduce((sum, suite) => sum + suite.passed, 0);
            const totalFailed = Object.values(testResults).reduce((sum, suite) => sum + suite.failed, 0);

            if (totalFailed > 0) {
                throw new Error(`测试失败: ${totalFailed} 个测试未通过`);
            }

            this.log(`✅ 自动化测试完成: ${totalPassed} 个测试通过`);
            return testResults;

        } catch (error) {
            this.log(`❌ 自动化测试失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 运行测试套件
     */
    async runTestSuite(suiteName, envPath, results) {
        return new Promise((resolve, reject) => {
            const testCommand = this.getTestCommand(suiteName);
            const testProcess = spawn('npm', ['run', testCommand], {
                cwd: envPath,
                stdio: 'pipe',
                timeout: this.config.safetyChecks.testTimeout
            });

            let output = '';

            testProcess.stdout.on('data', (data) => {
                output += data.toString();
            });

            testProcess.stderr.on('data', (data) => {
                output += data.toString();
            });

            testProcess.on('close', (code) => {
                const parsedResults = this.parseTestOutput(output);
                results[suiteName] = parsedResults;
                resolve(parsedResults);
            });

            testProcess.on('error', (error) => {
                results[suiteName].errors.push(error.message);
                reject(error);
            });
        });
    }

    /**
     * 获取测试命令
     */
    getTestCommand(suiteName) {
        const commands = {
            unit: 'test:unit',
            integration: 'test:integration',
            performance: 'test:performance'
        };
        
        return commands[suiteName] || 'test';
    }

    /**
     * 解析测试输出
     */
    parseTestOutput(output) {
        const results = { passed: 0, failed: 0, errors: [] };
        
        // 简单的测试输出解析
        const lines = output.split('\n');
        for (const line of lines) {
            if (line.includes('✓') || line.includes('pass')) {
                results.passed++;
            } else if (line.includes('✗') || line.includes('fail')) {
                results.failed++;
            } else if (line.includes('Error') || line.includes('error')) {
                results.errors.push(line.trim());
            }
        }
        
        return results;
    }

    /**
     * 启动环境
     */
    async startEnvironment(environment) {
        const envConfig = this.config.environments[environment];
        
        this.log(`🚀 启动环境: ${environment}`);

        try {
            // 检查环境是否已经运行
            if (this.environmentStatus[environment]?.isRunning) {
                this.log(`⚠️ 环境 ${environment} 已在运行`);
                return;
            }

            // 启动服务
            await this.startService(envConfig);

            // 更新状态
            this.environmentStatus[environment].isRunning = true;
            this.environmentStatus[environment].lastStarted = new Date().toISOString();

            this.log(`✅ 环境 ${environment} 启动成功`);

        } catch (error) {
            this.log(`❌ 环境 ${environment} 启动失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 启动服务
     */
    async startService(envConfig) {
        return new Promise((resolve, reject) => {
            const serviceProcess = spawn('npm', ['start'], {
                cwd: envConfig.path,
                stdio: 'pipe',
                env: {
                    ...process.env,
                    PORT: envConfig.port.toString(),
                    NODE_ENV: 'production'
                }
            });

            let startupOutput = '';

            serviceProcess.stdout.on('data', (data) => {
                startupOutput += data.toString();
                
                // 检查服务是否启动成功
                if (startupOutput.includes('Server started') || 
                    startupOutput.includes('listening on port')) {
                    resolve({ process: serviceProcess, output: startupOutput });
                }
            });

            serviceProcess.stderr.on('data', (data) => {
                startupOutput += data.toString();
            });

            serviceProcess.on('error', (error) => {
                reject(new Error(`服务启动错误: ${error.message}`));
            });

            // 超时检查
            setTimeout(() => {
                if (!serviceProcess.killed) {
                    serviceProcess.kill();
                    reject(new Error('服务启动超时'));
                }
            }, 30000);
        });
    }

    /**
     * 执行健康检查
     */
    async performHealthCheck(environment) {
        const envConfig = this.config.environments[environment];
        
        this.log(`🔍 执行健康检查: ${environment}`);

        try {
            const healthChecks = [
                this.checkServiceHealth(envConfig),
                this.checkDatabaseHealth(envConfig),
                this.checkApiHealth(envConfig),
                this.checkResourceUsage(envConfig)
            ];

            const results = await Promise.allSettled(healthChecks);
            const healthScore = this.calculateHealthScore(results);
            
            const healthCheck = {
                environment,
                timestamp: new Date().toISOString(),
                score: healthScore,
                checks: results.map(r => r.status === 'fulfilled' ? r.value : r.reason),
                status: healthScore >= 80 ? 'healthy' : healthScore >= 60 ? 'warning' : 'critical'
            };

            // 更新环境状态
            this.environmentStatus[environment].healthScore = healthScore;
            this.environmentStatus[environment].lastHealthCheck = healthCheck.timestamp;

            this.log(`✅ 健康检查完成: ${environment} - ${healthScore}%`);
            return healthCheck;

        } catch (error) {
            this.log(`❌ 健康检查失败: ${environment} - ${error.message}`);
            throw error;
        }
    }

    /**
     * 检查服务健康状态
     */
    async checkServiceHealth(envConfig) {
        const response = await fetch(`http://localhost:${envConfig.port}/health`);
        
        if (!response.ok) {
            throw new Error(`服务响应异常: ${response.status}`);
        }

        const data = await response.json();
        return { type: 'service', status: 'ok', data };
    }

    /**
     * 检查数据库健康状态
     */
    async checkDatabaseHealth(envConfig) {
        // 模拟数据库健康检查
        return { type: 'database', status: 'ok', responseTime: '12ms' };
    }

    /**
     * 检查API健康状态
     */
    async checkApiHealth(envConfig) {
        const endpoints = ['/api/status', '/api/health'];
        const results = [];

        for (const endpoint of endpoints) {
            try {
                const response = await fetch(`http://localhost:${envConfig.port}${endpoint}`);
                results.push({ endpoint, status: response.ok });
            } catch (error) {
                results.push({ endpoint, status: false, error: error.message });
            }
        }

        const allOk = results.every(r => r.status);
        return { type: 'api', status: allOk ? 'ok' : 'error', results };
    }

    /**
     * 检查资源使用情况
     */
    async checkResourceUsage(envConfig) {
        const memoryUsage = process.memoryUsage();
        const cpuUsage = process.cpuUsage();
        
        return {
            type: 'resources',
            status: 'ok',
            memory: {
                rss: memoryUsage.rss,
                heapUsed: memoryUsage.heapUsed,
                heapTotal: memoryUsage.heapTotal
            },
            cpu: cpuUsage
        };
    }

    /**
     * 计算健康评分
     */
    calculateHealthScore(results) {
        let totalScore = 0;
        let validChecks = 0;

        for (const result of results) {
            if (result.status === 'fulfilled') {
                totalScore += 100;
                validChecks++;
            } else {
                totalScore += 0;
                validChecks++;
            }
        }

        return validChecks > 0 ? Math.round(totalScore / validChecks) : 0;
    }

    /**
     * 回滚部署
     */
    async rollbackDeployment(environment, deploymentId) {
        this.log(`🔄 开始回滚部署: ${environment} - ${deploymentId}`);

        try {
            // 查找备份
            const backup = await this.findBackup(environment, deploymentId);
            
            if (!backup) {
                throw new Error(`未找到部署 ${deploymentId} 的备份`);
            }

            // 停止当前服务
            await this.stopEnvironment(environment);

            // 恢复备份
            await this.restoreBackup(environment, backup);

            // 重启服务
            await this.startEnvironment(environment);

            // 记录回滚
            const rollback = {
                deploymentId,
                environment,
                backup,
                timestamp: new Date().toISOString(),
                status: 'success'
            };

            this.rollbackStack.push(rollback);
            this.log(`✅ 回滚完成: ${environment} - ${deploymentId}`);

            return rollback;

        } catch (error) {
            this.log(`❌ 回滚失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 查找备份
     */
    async findBackup(environment, deploymentId) {
        const envConfig = this.config.environments[environment];
        const backupDir = path.join(envConfig.path, 'backups');
        
        if (!fs.existsSync(backupDir)) {
            return null;
        }

        const backups = fs.readdirSync(backupDir);
        
        for (const backupName of backups) {
            if (backupName.includes(deploymentId)) {
                const backupPath = path.join(backupDir, backupName);
                const metadataPath = path.join(backupPath, 'backup-metadata.json');
                
                if (fs.existsSync(metadataPath)) {
                    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
                    return { ...metadata, backupPath };
                }
            }
        }

        return null;
    }

    /**
     * 恢复备份
     */
    async restoreBackup(environment, backup) {
        const envConfig = this.config.environments[environment];
        
        this.log(`📦 恢复备份: ${backup.backupPath}`);

        // 清空当前环境
        await this.cleanTargetDirectory(envConfig.path);

        // 恢复备份文件
        await this.copyDirectory(backup.backupPath, envConfig.path, [
            path.join(backup.backupPath, 'backup-metadata.json')
        ]);

        this.log('✅ 备份恢复完成');
    }

    /**
     * 停止环境
     */
    async stopEnvironment(environment) {
        this.log(`🛑 停止环境: ${environment}`);

        try {
            // 查找并终止相关进程
            const envConfig = this.config.environments[environment];
            await this.killProcessesOnPort(envConfig.port);

            // 更新状态
            this.environmentStatus[environment].isRunning = false;
            this.environmentStatus[environment].lastStopped = new Date().toISOString();

            this.log(`✅ 环境 ${environment} 已停止`);

        } catch (error) {
            this.log(`❌ 停止环境失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 终止指定端口的进程
     */
    async killProcessesOnPort(port) {
        return new Promise((resolve, reject) => {
            exec(`lsof -ti:${port} | xargs kill -9`, (error) => {
                if (error && !error.message.includes('No such file')) {
                    reject(error);
                } else {
                    resolve();
                }
            });
        });
    }

    /**
     * 检查所有环境状态
     */
    async checkAllEnvironments() {
        this.log('🔍 检查所有环境状态...');

        for (const envName of Object.keys(this.config.environments)) {
            try {
                const healthCheck = await this.performHealthCheck(envName);
                this.environmentStatus[envName] = {
                    ...this.environmentStatus[envName],
                    ...healthCheck
                };
            } catch (error) {
                this.log(`⚠️ 环境 ${envName} 检查失败: ${error.message}`);
                this.environmentStatus[envName].status = 'error';
            }
        }

        this.log('✅ 环境状态检查完成');
    }

    /**
     * 开始监控
     */
    startMonitoring() {
        this.log('📊 启动环境监控...');

        // 定期健康检查
        setInterval(async () => {
            try {
                await this.checkAllEnvironments();
                await this.checkAlerts();
            } catch (error) {
                this.log(`❌ 监控检查失败: ${error.message}`);
            }
        }, this.config.monitoring.healthCheckInterval);

        // 定期清理日志
        setInterval(async () => {
            await this.cleanupOldLogs();
        }, 24 * 60 * 60 * 1000); // 每天清理一次

        this.log('✅ 环境监控已启动');
    }

    /**
     * 检查告警
     */
    async checkAlerts() {
        const alerts = [];

        for (const [envName, status] of Object.entries(this.environmentStatus)) {
            if (status.healthScore < 60) {
                alerts.push({
                    type: 'health',
                    environment: envName,
                    message: `健康评分过低: ${status.healthScore}%`,
                    severity: 'critical'
                });
            }

            if (status.isRunning && status.lastHealthCheck) {
                const timeSinceLastCheck = Date.now() - new Date(status.lastHealthCheck).getTime();
                if (timeSinceLastCheck > 5 * 60 * 1000) { // 5分钟
                    alerts.push({
                        type: 'timeout',
                        environment: envName,
                        message: '健康检查超时',
                        severity: 'warning'
                    });
                }
            }
        }

        if (alerts.length > 0) {
            this.alerts.push(...alerts);
            await this.sendAlerts(alerts);
        }
    }

    /**
     * 发送告警
     */
    async sendAlerts(alerts) {
        for (const alert of alerts) {
            this.log(`🚨 告警: [${alert.severity.toUpperCase()}] ${alert.environment} - ${alert.message}`);
        }
    }

    /**
     * 清理旧日志
     */
    async cleanupOldLogs() {
        const retentionDays = this.config.monitoring.logRetentionDays;
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        for (const [envName, envConfig] of Object.entries(this.config.environments)) {
            const logDir = path.join(envConfig.path, 'logs');
            
            if (fs.existsSync(logDir)) {
                const files = fs.readdirSync(logDir);
                
                for (const file of files) {
                    const filePath = path.join(logDir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.mtime < cutoffDate) {
                        fs.unlinkSync(filePath);
                        this.log(`🗑️ 删除旧日志: ${file}`);
                    }
                }
            }
        }
    }

    /**
     * 生成部署ID
     */
    generateDeploymentId() {
        return `deploy_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * 获取环境状态
     */
    getEnvironmentStatus() {
        return {
            environments: this.environmentStatus,
            deployments: this.deploymentHistory.slice(-10),
            rollbacks: this.rollbackStack.slice(-10),
            alerts: this.alerts.slice(-20),
            systemInfo: {
                uptime: process.uptime(),
                memoryUsage: process.memoryUsage(),
                nodeVersion: process.version,
                platform: process.platform
            }
        };
    }

    /**
     * 记录日志
     */
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[GrayEnvironmentManager] ${timestamp} - ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        const logPath = path.join(process.cwd(), 'Logs', 'gray-environment.log');
        fs.appendFile(logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error('写入日志失败:', err);
            }
        });
    }
}

module.exports = GrayEnvironmentManager;
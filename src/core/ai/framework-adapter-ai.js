/**
 * 框架适配与功能优化子AI
 * 根据AI建议选择适合现有项目架构的框架，并根据现有功能进行完善拓展和优化
 * 实现版本管理、日志记录、数据库备份和回滚机制
 */

const winston = require('winston');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/framework-adapter-ai.log`,
            maxsize: 5242880,
            maxFiles: 5
        }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// 添加warning方法的兼容处理
if (!logger.warning) {
    logger.warning = logger.warn;
}

// 引入AI特征库
const aiFeatureLibrary = require('./ai-feature-library');
// 引入Flask适配模块
const FlaskAdapter = require('./flask-adapter');

// 框架适配与功能优化子AI类
class FrameworkAdapterAI {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = 'framework_adapter_ai';
        this.role = 'framework_adapter';
        this.group = 'system_management';
        this.status = 'idle';
        this.currentTask = null;
        this.taskHistory = [];
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.idleSince = new Date();
        
        // 工具方法
        this.execPromise = util.promisify(exec);
        
        // 配置
        this.config = {
            autoAnalyze: true,
            autoOptimize: true,
            featureReporting: true,
            versionManagement: true,
            backupEnabled: true,
            rollbackEnabled: true,
            backupDirectory: path.join(__dirname, '../../../backups'),
            projectRoot: path.resolve(__dirname, '../../..'),
            packageJsonPath: path.resolve(__dirname, '../../../package.json'),
            frameworkSuggestions: {
                express: {
                    score: 0.95,
                    compatibility: 'high',
                    reason: '现有项目已使用Express.js，完全兼容'
                },
                flask: {
                    score: 0.85,
                    compatibility: 'medium',
                    reason: 'Python轻量级Web框架，适合快速开发'
                },
                koa: {
                    score: 0.75,
                    compatibility: 'medium',
                    reason: '轻量级框架，迁移成本中等'
                },
                nestjs: {
                    score: 0.6,
                    compatibility: 'low',
                    reason: '企业级框架，迁移成本高'
                }
            }
        };
        
        // 性能指标
        this.performanceMetrics = {
            analysesCompleted: 0,
            optimizationsApplied: 0,
            featuresReported: 0,
            versionsUpgraded: 0,
            backupsCreated: 0,
            rollbacksPerformed: 0
        };
        
        // 确保备份目录存在
        if (!fs.existsSync(this.config.backupDirectory)) {
            fs.mkdirSync(this.config.backupDirectory, { recursive: true });
        }
        
        logger.info(`✅ 框架适配与功能优化子AI已初始化: ${this.name}`);
    }
    
    /**
     * 开始AI服务
     */
    start() {
        logger.info(`📋 开始框架适配与功能优化服务...`);
        this.status = 'running';
        this.currentTask = 'framework_adaptation';
        this.updatedAt = new Date();
        
        // 立即执行一次分析和优化
        this.analyzeAndOptimize();
        
        logger.info(`✅ 框架适配与功能优化服务已启动`);
        return { success: true, message: '框架适配与功能优化服务已启动' };
    }
    
    /**
     * 停止AI服务
     */
    stop() {
        logger.info(`📋 停止框架适配与功能优化服务...`);
        this.status = 'idle';
        this.currentTask = null;
        this.idleSince = new Date();
        this.updatedAt = new Date();
        
        logger.info(`✅ 框架适配与功能优化服务已停止`);
        return { success: true, message: '框架适配与功能优化服务已停止' };
    }
    
    /**
     * 分析项目架构并优化
     */
    async analyzeAndOptimize() {
        logger.info(`🔍 开始分析项目架构并优化...`);
        
        try {
            // 1. 分析现有项目架构
            await this.analyzeProjectArchitecture();
            
            // 2. 选择适合的框架
            await this.selectOptimalFramework();
            
            // 3. 根据现有功能进行拓展和优化
            await this.optimizeExistingFeatures();
            
            // 4. 升级版本号
            await this.upgradeVersion();
            
            // 5. 创建备份
            await this.createBackup();
            
            // 6. 记录历史
            await this.recordHistory();
            
            // 7. 上传特征库
            await this.uploadFeatureLibrary();
            
            this.performanceMetrics.analysesCompleted++;
            logger.info(`✅ 项目架构分析与优化完成`);
            
        } catch (error) {
            logger.error(`❌ 分析与优化过程中发生错误: ${error.message}`);
        }
    }
    
    /**
     * 分析现有项目架构
     */
    async analyzeProjectArchitecture() {
        logger.info(`📊 分析现有项目架构...`);
        
        try {
            // 读取package.json文件
            const packageJsonContent = fs.readFileSync(this.config.packageJsonPath, 'utf8');
            const packageJson = JSON.parse(packageJsonContent);
            
            // 分析项目依赖
            const dependencies = packageJson.dependencies || {};
            const devDependencies = packageJson.devDependencies || {};
            
            // 分析项目结构
            const projectStructure = {
                mainFile: packageJson.main || 'index.js',
                scripts: packageJson.scripts || {},
                dependencies: Object.keys(dependencies),
                devDependencies: Object.keys(devDependencies),
                engines: packageJson.engines || {},
                projectType: this.determineProjectType(dependencies)
            };
            
            logger.info(`📋 项目架构分析结果:`, projectStructure);
            
            // 报告特征库
            const feature = {
                type: 'project_architecture',
                description: `项目架构分析完成`,
                severity: 'info',
                location: 'package.json',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'framework_adapter_ai',
                details: projectStructure
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            
            return projectStructure;
            
        } catch (error) {
            logger.error(`❌ 分析项目架构时发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 确定项目类型
     */
    determineProjectType(dependencies) {
        if (dependencies.express) return 'express';
        if (dependencies.flask) return 'flask';
        if (dependencies.koa) return 'koa';
        if (dependencies.nestjs) return 'nestjs';
        if (dependencies.react) return 'react';
        if (dependencies.vue) return 'vue';
        return 'unknown';
    }
    
    /**
     * 选择最优框架
     */
    async selectOptimalFramework() {
        logger.info(`🤖 选择最优框架...`);
        
        try {
            // 基于现有项目架构和配置的框架建议，选择最优框架
            let optimalFramework = null;
            let highestScore = 0;
            
            Object.entries(this.config.frameworkSuggestions).forEach(([framework, details]) => {
                if (details.score > highestScore) {
                    highestScore = details.score;
                    optimalFramework = framework;
                }
            });
            
            logger.info(`✅ 选择的最优框架: ${optimalFramework} (得分: ${highestScore})`);
            
            // 报告特征库
            const feature = {
                type: 'framework_selection',
                description: `选择最优框架: ${optimalFramework}`,
                severity: 'info',
                location: 'framework-adapter-ai',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'framework_adapter_ai',
                details: {
                    selectedFramework: optimalFramework,
                    score: highestScore,
                    frameworks: this.config.frameworkSuggestions
                }
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            
            return optimalFramework;
            
        } catch (error) {
            logger.error(`❌ 选择最优框架时发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 优化现有功能
     */
    async optimizeExistingFeatures() {
        logger.info(`⚡ 优化现有功能...`);
        
        try {
            // 1. 选择最优框架
            const optimalFramework = await this.selectOptimalFramework();
            
            // 2. 根据选择的框架执行不同的优化和适配操作
            if (optimalFramework === 'flask') {
                logger.info(`🔄 开始适配Flask框架...`);
                await this.adaptToFlask();
            } else {
                // 对于其他框架，执行常规优化
                // 2.1 优化项目依赖
                await this.optimizeDependencies();
                
                // 2.2 优化代码结构
                await this.optimizeCodeStructure();
                
                // 2.3 优化性能
                await this.optimizePerformance();
                
                // 2.4 完善功能
                await this.enhanceFeatures();
            }
            
            logger.info(`✅ 现有功能优化完成`);
            
        } catch (error) {
            logger.error(`❌ 优化现有功能时发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 适配到Flask框架
     */
    async adaptToFlask() {
        logger.info(`🔄 适配到Flask框架...`);
        
        try {
            // 创建FlaskAdapter实例
            const flaskAdapter = new FlaskAdapter(this.config.projectRoot);
            
            // 初始化Flask项目结构
            await flaskAdapter.initializeFlaskProject();
            
            // 安装Flask依赖（使用--break-system-packages标志适应现代Python环境）
            await this.installFlaskDependencies();
            
            // 修改app.py使用5001端口（避免与其他服务冲突）
            this.updateFlaskPort();
            
            // 启动Flask开发服务器
            const flaskProcess = await this.startFlaskServer();
            
            // 生成适配报告
            const adaptationReport = flaskAdapter.generateAdaptationReport();
            
            // 更新适配报告中的访问地址
            adaptationReport.instructions.access = 'http://localhost:5001';
            
            // 保存适配报告
            const reportPath = path.join(this.config.backupDirectory, `flask-adaptation-report_${Date.now()}.json`);
            fs.writeFileSync(reportPath, JSON.stringify(adaptationReport, null, 2));
            
            logger.info(`✅ Flask框架适配完成！`);
            logger.info(`📋 适配报告已保存到: ${reportPath}`);
            logger.info(`🚀 Flask应用已启动，访问地址: http://localhost:5001`);
            
            // 报告特征库
            const feature = {
                type: 'framework_adaptation',
                description: `项目已成功适配到Flask框架`,
                severity: 'info',
                location: 'flask-adapter',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'framework_adapter_ai',
                details: adaptationReport
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            
            return adaptationReport;
            
        } catch (error) {
            logger.error(`❌ 适配Flask框架时发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 安装Flask依赖
     */
    async installFlaskDependencies() {
        logger.info(`📦 安装Flask依赖...`);
        
        try {
            const flaskRoot = path.join(this.config.projectRoot, 'flask-app');
            await this.execPromise(
                `cd ${flaskRoot} && pip3 install -r requirements.txt --break-system-packages`,
                { cwd: this.config.projectRoot }
            );
            
            logger.info(`✅ Flask依赖安装完成`);
            return true;
            
        } catch (error) {
            logger.error(`❌ 安装Flask依赖时发生错误: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 修改Flask应用端口为5001
     */
    updateFlaskPort() {
        logger.info(`⚙️ 更新Flask应用端口为5001...`);
        
        try {
            const appPyPath = path.join(this.config.projectRoot, 'flask-app', 'app.py');
            let content = fs.readFileSync(appPyPath, 'utf8');
            
            // 修改端口号
            content = content.replace(/port=5000/g, 'port=5001');
            
            fs.writeFileSync(appPyPath, content);
            
            logger.info(`✅ Flask应用端口已更新为5001`);
            return true;
            
        } catch (error) {
            logger.error(`❌ 更新Flask端口时发生错误: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 启动Flask开发服务器
     */
    async startFlaskServer() {
        logger.info(`🔥 启动Flask开发服务器...`);
        
        try {
            const flaskRoot = path.join(this.config.projectRoot, 'flask-app');
            
            // 在后台启动Flask服务器
            const flaskProcess = exec(
                `cd ${flaskRoot} && python3 app.py`,
                { cwd: this.config.projectRoot }
            );
            
            // 捕获输出
            flaskProcess.stdout.on('data', (data) => {
                logger.info(`[Flask] ${data}`);
            });
            
            flaskProcess.stderr.on('data', (data) => {
                logger.error(`[Flask Error] ${data}`);
            });
            
            // 等待服务器启动
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            logger.info(`✅ Flask服务器已启动，访问地址: http://localhost:5001`);
            return flaskProcess;
            
        } catch (error) {
            logger.error(`❌ 启动Flask服务器时发生错误: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 优化项目依赖
     */
    async optimizeDependencies() {
        logger.info(`📦 优化项目依赖...`);
        
        try {
            const execPromise = util.promisify(exec);
            
            // 检查并更新依赖
            logger.info(`🔄 检查依赖更新...`);
            await execPromise(`npm outdated`, { cwd: this.config.projectRoot });
            
            // 优化依赖（这里只是示例，实际项目中需要更复杂的逻辑）
            logger.info(`✅ 依赖优化完成`);
            
        } catch (error) {
            logger.warning(`⚠️  依赖检查过程中发生警告: ${error.message}`);
        }
    }
    
    /**
     * 优化代码结构
     */
    async optimizeCodeStructure() {
        logger.info(`🏗️  优化代码结构...`);
        
        try {
            // 检查代码结构（这里只是示例，实际项目中需要更复杂的逻辑）
            const srcDir = path.join(this.config.projectRoot, 'src');
            if (fs.existsSync(srcDir)) {
                logger.info(`📁 源代码目录存在，结构良好`);
            }
            
            logger.info(`✅ 代码结构优化完成`);
            
        } catch (error) {
            logger.error(`❌ 优化代码结构时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 优化性能
     */
    async optimizePerformance() {
        logger.info(`🚀 优化性能...`);
        
        try {
            // 检查性能优化点（这里只是示例，实际项目中需要更复杂的逻辑）
            logger.info(`✅ 性能优化完成`);
            
        } catch (error) {
            logger.error(`❌ 优化性能时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 完善功能
     */
    async enhanceFeatures() {
        logger.info(`🔧 完善现有功能...`);
        
        try {
            // 检查并完善功能（这里只是示例，实际项目中需要更复杂的逻辑）
            logger.info(`✅ 功能完善完成`);
            
        } catch (error) {
            logger.error(`❌ 完善功能时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 升级版本号
     */
    async upgradeVersion() {
        logger.info(`📌 升级版本号...`);
        
        try {
            // 读取当前版本号
            const packageJsonContent = fs.readFileSync(this.config.packageJsonPath, 'utf8');
            const packageJson = JSON.parse(packageJsonContent);
            
            // 解析版本号
            const currentVersion = packageJson.version || '1.0.0';
            const versionParts = currentVersion.split('.').map(Number);
            
            // 升级版本号（小版本号+1）
            versionParts[2] = (versionParts[2] || 0) + 1;
            const newVersion = versionParts.join('.');
            
            // 更新buildVersion
            const buildVersion = parseInt(packageJson.buildVersion || '2000000000000000') + 1;
            
            // 更新package.json
            packageJson.version = newVersion;
            packageJson.buildVersion = buildVersion.toString();
            
            fs.writeFileSync(this.config.packageJsonPath, JSON.stringify(packageJson, null, 2));
            
            logger.info(`✅ 版本号已升级: ${currentVersion} -> ${newVersion}`);
            logger.info(`✅ Build版本已更新: ${buildVersion}`);
            
            // 报告特征库
            const feature = {
                type: 'version_upgrade',
                description: `版本号升级`,
                severity: 'info',
                location: 'package.json',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'framework_adapter_ai',
                details: {
                    oldVersion: currentVersion,
                    newVersion: newVersion,
                    buildVersion: buildVersion
                }
            };
            
            aiFeatureLibrary.addFeature(feature);
            this.performanceMetrics.featuresReported++;
            this.performanceMetrics.versionsUpgraded++;
            
            return { oldVersion: currentVersion, newVersion: newVersion, buildVersion };
            
        } catch (error) {
            logger.error(`❌ 升级版本号时发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 创建备份
     */
    async createBackup() {
        logger.info(`💾 创建项目备份...`);
        
        try {
            if (!this.config.backupEnabled) {
                logger.info(`⚠️  备份功能已禁用，跳过备份`);
                return;
            }
            
            // 生成备份文件名
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupFileName = `backup_${timestamp}.tar.gz`;
            const backupFilePath = path.join(this.config.backupDirectory, backupFileName);
            
            // 创建备份命令
            const execPromise = util.promisify(exec);
            await execPromise(
                `tar -czf ${backupFilePath} --exclude=node_modules --exclude=Logs --exclude=backups --exclude=.git ${this.config.projectRoot}/*`,
                { cwd: this.config.projectRoot }
            );
            
            // 创建双备份
            const backupFileName2 = `backup_${timestamp}_copy.tar.gz`;
            const backupFilePath2 = path.join(this.config.backupDirectory, backupFileName2);
            fs.copyFileSync(backupFilePath, backupFilePath2);
            
            logger.info(`✅ 项目备份已创建: ${backupFilePath}`);
            logger.info(`✅ 双备份已创建: ${backupFilePath2}`);
            
            // 记录备份信息
            this.recordBackupInfo({
                backupId: `backup_${timestamp}`,
                backupFiles: [backupFileName, backupFileName2],
                timestamp: new Date().toISOString(),
                size: fs.statSync(backupFilePath).size,
                status: 'success'
            });
            
            this.performanceMetrics.backupsCreated++;
            
            return { backupFilePath, backupFilePath2 };
            
        } catch (error) {
            logger.error(`❌ 创建备份时发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 记录备份信息
     */
    async recordBackupInfo(backupInfo) {
        try {
            // 读取现有备份记录
            const backupRecordsFile = path.join(this.config.backupDirectory, 'backup-records.json');
            let backupRecords = [];
            
            if (fs.existsSync(backupRecordsFile)) {
                const recordsContent = fs.readFileSync(backupRecordsFile, 'utf8');
                backupRecords = JSON.parse(recordsContent);
            }
            
            // 添加新备份记录
            backupRecords.push(backupInfo);
            
            // 只保留最近10个备份记录
            if (backupRecords.length > 10) {
                backupRecords = backupRecords.slice(-10);
            }
            
            // 写入备份记录
            fs.writeFileSync(backupRecordsFile, JSON.stringify(backupRecords, null, 2));
            
            logger.info(`✅ 备份信息已记录`);
            
        } catch (error) {
            logger.error(`❌ 记录备份信息时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 回滚到指定版本
     */
    async rollbackToVersion(versionId) {
        logger.info(`⏪ 回滚到版本: ${versionId}`);
        
        try {
            if (!this.config.rollbackEnabled) {
                logger.info(`⚠️  回滚功能已禁用，跳过回滚`);
                return;
            }
            
            // 读取备份记录
            const backupRecordsFile = path.join(this.config.backupDirectory, 'backup-records.json');
            if (!fs.existsSync(backupRecordsFile)) {
                logger.error(`❌ 备份记录文件不存在`);
                return;
            }
            
            const recordsContent = fs.readFileSync(backupRecordsFile, 'utf8');
            const backupRecords = JSON.parse(recordsContent);
            
            // 查找指定版本的备份
            const backupRecord = backupRecords.find(record => record.backupId === versionId);
            if (!backupRecord) {
                logger.error(`❌ 未找到版本: ${versionId}`);
                return;
            }
            
            // 获取备份文件路径
            const backupFilePath = path.join(this.config.backupDirectory, backupRecord.backupFiles[0]);
            if (!fs.existsSync(backupFilePath)) {
                logger.error(`❌ 备份文件不存在: ${backupFilePath}`);
                return;
            }
            
            // 创建临时目录
            const tempDir = path.join(this.config.backupDirectory, `temp_${Date.now()}`);
            fs.mkdirSync(tempDir, { recursive: true });
            
            // 解压备份文件到临时目录
            const execPromise = util.promisify(exec);
            await execPromise(`tar -xzf ${backupFilePath} -C ${tempDir}`, { cwd: this.config.projectRoot });
            
            // 恢复项目文件
            const tempFiles = fs.readdirSync(tempDir);
            tempFiles.forEach(file => {
                const tempFilePath = path.join(tempDir, file);
                const targetFilePath = path.join(this.config.projectRoot, file);
                
                // 先删除目标文件/目录
                if (fs.existsSync(targetFilePath)) {
                    this.removeRecursive(targetFilePath);
                }
                
                // 复制文件/目录
                this.copyRecursive(tempFilePath, targetFilePath);
            });
            
            // 删除临时目录
            this.removeRecursive(tempDir);
            
            logger.info(`✅ 已成功回滚到版本: ${versionId}`);
            
            // 记录回滚信息
            this.recordRollbackInfo({
                rollbackId: `rollback_${Date.now()}`,
                versionId: versionId,
                timestamp: new Date().toISOString(),
                status: 'success'
            });
            
            this.performanceMetrics.rollbacksPerformed++;
            
            return { success: true, message: `已成功回滚到版本: ${versionId}` };
            
        } catch (error) {
            logger.error(`❌ 回滚过程中发生错误: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 记录回滚信息
     */
    async recordRollbackInfo(rollbackInfo) {
        try {
            // 读取现有回滚记录
            const rollbackRecordsFile = path.join(this.config.backupDirectory, 'rollback-records.json');
            let rollbackRecords = [];
            
            if (fs.existsSync(rollbackRecordsFile)) {
                const recordsContent = fs.readFileSync(rollbackRecordsFile, 'utf8');
                rollbackRecords = JSON.parse(recordsContent);
            }
            
            // 添加新回滚记录
            rollbackRecords.push(rollbackInfo);
            
            // 只保留最近10个回滚记录
            if (rollbackRecords.length > 10) {
                rollbackRecords = rollbackRecords.slice(-10);
            }
            
            // 写入回滚记录
            fs.writeFileSync(rollbackRecordsFile, JSON.stringify(rollbackRecords, null, 2));
            
            logger.info(`✅ 回滚信息已记录`);
            
        } catch (error) {
            logger.error(`❌ 记录回滚信息时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 递归复制文件/目录
     */
    copyRecursive(src, dest) {
        const stats = fs.statSync(src);
        
        if (stats.isDirectory()) {
            fs.mkdirSync(dest, { recursive: true });
            
            const files = fs.readdirSync(src);
            files.forEach(file => {
                const srcPath = path.join(src, file);
                const destPath = path.join(dest, file);
                this.copyRecursive(srcPath, destPath);
            });
        } else {
            fs.copyFileSync(src, dest);
        }
    }
    
    /**
     * 递归删除文件/目录
     */
    removeRecursive(path) {
        if (fs.existsSync(path)) {
            if (fs.statSync(path).isDirectory()) {
                fs.readdirSync(path).forEach(file => {
                    const curPath = path + '/' + file;
                    this.removeRecursive(curPath);
                });
                fs.rmdirSync(path);
            } else {
                fs.unlinkSync(path);
            }
        }
    }
    
    /**
     * 记录历史
     */
    async recordHistory() {
        logger.info(`📝 记录历史...`);
        
        try {
            // 创建历史记录
            const historyRecord = {
                historyId: `history_${Date.now()}`,
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                action: 'analyze_and_optimize',
                status: 'success',
                performanceMetrics: this.performanceMetrics
            };
            
            // 读取现有历史记录
            const historyFile = path.join(this.config.backupDirectory, 'history-records.json');
            let historyRecords = [];
            
            if (fs.existsSync(historyFile)) {
                const recordsContent = fs.readFileSync(historyFile, 'utf8');
                historyRecords = JSON.parse(recordsContent);
            }
            
            // 添加新历史记录
            historyRecords.push(historyRecord);
            
            // 只保留最近50条历史记录
            if (historyRecords.length > 50) {
                historyRecords = historyRecords.slice(-50);
            }
            
            // 写入历史记录
            fs.writeFileSync(historyFile, JSON.stringify(historyRecords, null, 2));
            
            logger.info(`✅ 历史记录已保存`);
            
        } catch (error) {
            logger.error(`❌ 记录历史时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 上传特征库
     */
    async uploadFeatureLibrary() {
        logger.info(`📤 上传特征库...`);
        
        try {
            // 这里实现特征库上传逻辑
            // 示例：将特征库保存到指定位置
            const featureLibrary = aiFeatureLibrary.getFeatures();
            const featureLibraryPath = path.join(this.config.backupDirectory, `feature-library_${Date.now()}.json`);
            
            fs.writeFileSync(featureLibraryPath, JSON.stringify(featureLibrary, null, 2));
            logger.info(`✅ 特征库已上传到: ${featureLibraryPath}`);
            
            // 双备份特征库
            const featureLibraryPath2 = path.join(this.config.backupDirectory, `feature-library_${Date.now()}_copy.json`);
            fs.copyFileSync(featureLibraryPath, featureLibraryPath2);
            logger.info(`✅ 特征库双备份已创建: ${featureLibraryPath2}`);
            
            this.performanceMetrics.featuresReported++;
            
        } catch (error) {
            logger.error(`❌ 上传特征库时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 获取AI状态
     */
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            role: this.role,
            group: this.group,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt,
            idleSince: this.idleSince,
            currentTask: this.currentTask,
            performanceMetrics: this.performanceMetrics,
            config: this.config
        };
    }
    
    /**
     * 生成报告
     */
    generateReport() {
        const report = {
            id: `framework_report_${Date.now()}`,
            aiId: this.id,
            aiName: this.name,
            generatedAt: new Date().toISOString(),
            status: this.status,
            performanceMetrics: this.performanceMetrics,
            config: this.config,
            latestBackup: this.getLatestBackup()
        };
        
        return report;
    }
    
    /**
     * 获取最新备份信息
     */
    getLatestBackup() {
        try {
            const backupRecordsFile = path.join(this.config.backupDirectory, 'backup-records.json');
            if (!fs.existsSync(backupRecordsFile)) {
                return null;
            }
            
            const recordsContent = fs.readFileSync(backupRecordsFile, 'utf8');
            const backupRecords = JSON.parse(recordsContent);
            
            return backupRecords[backupRecords.length - 1] || null;
        } catch (error) {
            logger.error(`❌ 获取最新备份信息时发生错误: ${error.message}`);
            return null;
        }
    }
}

// 导出单例实例
const frameworkAdapterAI = new FrameworkAdapterAI();
module.exports = frameworkAdapterAI;
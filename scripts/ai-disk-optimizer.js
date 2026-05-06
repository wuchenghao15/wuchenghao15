/**
 * AI磁盘优化脚本
 * 使用本地AI引擎组自动优化系统磁盘使用
 */

const { AIAutoFix } = require('../src/core/ai/ai-auto-fix');
// 确保AIAutoFix正确加载
if (typeof AIAutoFix !== 'function') {
    console.error('AIAutoFix加载失败');
    process.exit(1);
}
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class AIDiskOptimizer {
    constructor() {
        this.aiAutoFix = new AIAutoFix();
        this.logger = {
            info: (...args) => console.log('[AIDiskOptimizer] INFO:', ...args),
            warn: (...args) => console.warn('[AIDiskOptimizer] WARN:', ...args),
            error: (...args) => console.error('[AIDiskOptimizer] ERROR:', ...args)
        };
        this.projectPath = path.resolve(__dirname, '..');
    }
    
    async initialize() {
        this.logger.info('正在初始化AI磁盘优化器...');
        const success = await this.aiAutoFix.initialize();
        if (success) {
            this.logger.info('AI磁盘优化器初始化完成');
            return true;
        } else {
            this.logger.error('AI磁盘优化器初始化失败');
            return false;
        }
    }
    
    /**
     * 分析磁盘使用情况
     */
    analyzeDiskUsage() {
        this.logger.info('开始分析磁盘使用情况...');
        
        const diskIssues = [];
        
        // 1. 检查磁盘使用百分比
        const diskUsage = this.getDiskUsage();
        diskIssues.push({
            type: '磁盘使用率',
            description: `当前磁盘使用率: ${diskUsage.usedPercentage}%`,
            details: diskUsage
        });
        
        // 2. 检查大文件
        const largeFiles = this.findLargeFiles(this.projectPath, 5 * 1024 * 1024); // 5MB以上
        if (largeFiles.length > 0) {
            diskIssues.push({
                type: '大文件',
                description: `发现 ${largeFiles.length} 个大于5MB的文件`,
                files: largeFiles
            });
        }
        
        // 3. 检查重复文件
        const duplicateFiles = this.findDuplicateFiles(this.projectPath);
        if (duplicateFiles.length > 0) {
            diskIssues.push({
                type: '重复文件',
                description: `发现 ${duplicateFiles.length} 组重复文件`,
                files: duplicateFiles
            });
        }
        
        // 4. 检查临时文件
        const tempFiles = this.findTempFiles(this.projectPath);
        if (tempFiles.length > 0) {
            diskIssues.push({
                type: '临时文件',
                description: `发现 ${tempFiles.length} 个临时文件`,
                files: tempFiles
            });
        }
        
        // 5. 检查日志文件
        const logFiles = this.findLogFiles(this.projectPath);
        if (logFiles.length > 0) {
            diskIssues.push({
                type: '日志文件',
                description: `发现 ${logFiles.length} 个日志文件`,
                files: logFiles
            });
        }
        
        this.logger.info('磁盘使用情况分析完成:', diskIssues);
        return diskIssues;
    }
    
    /**
     * 获取磁盘使用情况
     */
    getDiskUsage() {
        try {
            // 使用df命令获取磁盘使用情况
            const output = execSync('df -h /', { encoding: 'utf8' });
            const lines = output.trim().split('\n');
            const dataLine = lines[1];
            const parts = dataLine.split(/\s+/);
            
            return {
                filesystem: parts[0],
                size: parts[1],
                used: parts[2],
                available: parts[3],
                usedPercentage: parts[4].replace('%', ''),
                mountedOn: parts[5]
            };
        } catch (error) {
            this.logger.warn('获取磁盘使用情况时出错:', error.message);
            return {
                filesystem: 'Unknown',
                size: 'Unknown',
                used: 'Unknown',
                available: 'Unknown',
                usedPercentage: 'Unknown',
                mountedOn: 'Unknown'
            };
        }
    }
    
    /**
     * 查找大文件
     */
    findLargeFiles(dir, sizeThreshold) {
        const largeFiles = [];
        
        const scanDir = (currentDir) => {
            try {
                const files = fs.readdirSync(currentDir);
                for (const file of files) {
                    const filePath = path.join(currentDir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        if (file !== 'node_modules' && file !== '.git' && file !== 'dist' && file !== 'build') {
                            scanDir(filePath);
                        }
                    } else if (stat.size > sizeThreshold) {
                        largeFiles.push({
                            path: filePath,
                            size: stat.size,
                            sizeMB: (stat.size / (1024 * 1024)).toFixed(2)
                        });
                    }
                }
            } catch (error) {
                this.logger.warn('扫描目录时出错:', error.message);
            }
        };
        
        scanDir(dir);
        return largeFiles.sort((a, b) => b.size - a.size);
    }
    
    /**
     * 查找重复文件
     */
    findDuplicateFiles(dir) {
        const duplicateFiles = [];
        const fileHashes = new Map();
        
        const scanDir = (currentDir) => {
            try {
                const files = fs.readdirSync(currentDir);
                for (const file of files) {
                    const filePath = path.join(currentDir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        if (file !== 'node_modules' && file !== '.git' && file !== 'dist' && file !== 'build') {
                            scanDir(filePath);
                        }
                    } else if (stat.size > 1024 * 1024) { // 只检查大于1MB的文件
                        try {
                            // 使用简单的文件大小和修改时间作为哈希
                            const hash = `${stat.size}_${stat.mtime.getTime()}`;
                            if (fileHashes.has(hash)) {
                                const existingFiles = fileHashes.get(hash);
                                existingFiles.push(filePath);
                                fileHashes.set(hash, existingFiles);
                            } else {
                                fileHashes.set(hash, [filePath]);
                            }
                        } catch (error) {
                            this.logger.warn('计算文件哈希时出错:', error.message);
                        }
                    }
                }
            } catch (error) {
                this.logger.warn('扫描目录时出错:', error.message);
            }
        };
        
        scanDir(dir);
        
        // 收集重复文件组
        for (const [hash, files] of fileHashes.entries()) {
            if (files.length > 1) {
                duplicateFiles.push({
                    hash: hash,
                    files: files,
                    count: files.length
                });
            }
        }
        
        return duplicateFiles;
    }
    
    /**
     * 查找临时文件
     */
    findTempFiles(dir) {
        const tempFiles = [];
        const tempExtensions = ['.tmp', '.temp', '.swp', '.swo', '.log', '.bak', '.old'];
        const tempDirs = ['temp', 'tmp', 'logs', 'backup'];
        
        const scanDir = (currentDir) => {
            try {
                const files = fs.readdirSync(currentDir);
                for (const file of files) {
                    const filePath = path.join(currentDir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        if (tempDirs.includes(file.toLowerCase())) {
                            // 这是临时目录，收集所有文件
                            this.collectDirFiles(filePath, tempFiles);
                        } else if (file !== 'node_modules' && file !== '.git' && file !== 'dist' && file !== 'build') {
                            scanDir(filePath);
                        }
                    } else {
                        // 检查文件扩展名
                        const ext = path.extname(file).toLowerCase();
                        if (tempExtensions.includes(ext)) {
                            tempFiles.push({
                                path: filePath,
                                size: stat.size,
                                sizeMB: (stat.size / (1024 * 1024)).toFixed(2),
                                type: 'extension'
                            });
                        }
                        // 检查文件名
                        if (file.toLowerCase().includes('temp') || file.toLowerCase().includes('tmp')) {
                            tempFiles.push({
                                path: filePath,
                                size: stat.size,
                                sizeMB: (stat.size / (1024 * 1024)).toFixed(2),
                                type: 'name'
                            });
                        }
                    }
                }
            } catch (error) {
                this.logger.warn('扫描目录时出错:', error.message);
            }
        };
        
        scanDir(dir);
        return tempFiles;
    }
    
    /**
     * 收集目录中的所有文件
     */
    collectDirFiles(dir, fileList) {
        try {
            const files = fs.readdirSync(dir);
            for (const file of files) {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory()) {
                    this.collectDirFiles(filePath, fileList);
                } else {
                    fileList.push({
                        path: filePath,
                        size: stat.size,
                        sizeMB: (stat.size / (1024 * 1024)).toFixed(2),
                        type: 'directory'
                    });
                }
            }
        } catch (error) {
            this.logger.warn('收集目录文件时出错:', error.message);
        }
    }
    
    /**
     * 查找日志文件
     */
    findLogFiles(dir) {
        const logFiles = [];
        const logExtensions = ['.log', '.txt', '.out'];
        
        const scanDir = (currentDir) => {
            try {
                const files = fs.readdirSync(currentDir);
                for (const file of files) {
                    const filePath = path.join(currentDir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        if (file !== 'node_modules' && file !== '.git' && file !== 'dist' && file !== 'build') {
                            scanDir(filePath);
                        }
                    } else {
                        const ext = path.extname(file).toLowerCase();
                        if (logExtensions.includes(ext) || file.toLowerCase().includes('log')) {
                            logFiles.push({
                                path: filePath,
                                size: stat.size,
                                sizeMB: (stat.size / (1024 * 1024)).toFixed(2),
                                lastModified: stat.mtime
                            });
                        }
                    }
                }
            } catch (error) {
                this.logger.warn('扫描目录时出错:', error.message);
            }
        };
        
        scanDir(dir);
        return logFiles.sort((a, b) => b.size - a.size);
    }
    
    /**
     * 优化磁盘使用
     */
    async optimizeDisk() {
        this.logger.info('开始磁盘优化...');
        
        const diskIssues = this.analyzeDiskUsage();
        
        // 1. 清理临时文件
        this.cleanupTempFiles();
        
        // 2. 清理日志文件
        this.cleanupLogFiles();
        
        // 3. 清理npm缓存
        this.cleanupNpmCache();
        
        // 4. 清理重复文件
        this.cleanupDuplicateFiles();
        
        // 5. 优化代码文件大小
        await this.optimizeCodeFiles();
        
        // 6. 提供优化建议
        this.provideOptimizationSuggestions(diskIssues);
        
        // 7. 再次检查磁盘使用情况
        const finalDiskUsage = this.getDiskUsage();
        this.logger.info('优化后的磁盘使用情况:', finalDiskUsage);
        
        this.logger.info('磁盘优化完成');
    }
    
    /**
     * 清理临时文件
     */
    cleanupTempFiles() {
        this.logger.info('开始清理临时文件...');
        
        const tempFiles = this.findTempFiles(this.projectPath);
        let cleanedCount = 0;
        let freedSpace = 0;
        
        for (const tempFile of tempFiles) {
            try {
                fs.unlinkSync(tempFile.path);
                cleanedCount++;
                freedSpace += tempFile.size;
                this.logger.info(`清理临时文件: ${tempFile.path} (${tempFile.sizeMB} MB)`);
            } catch (error) {
                this.logger.warn(`清理临时文件时出错: ${tempFile.path}`, error.message);
            }
        }
        
        this.logger.info(`清理完成，共清理 ${cleanedCount} 个临时文件，释放 ${(freedSpace / (1024 * 1024)).toFixed(2)} MB 空间`);
    }
    
    /**
     * 清理日志文件
     */
    cleanupLogFiles() {
        this.logger.info('开始清理日志文件...');
        
        const logFiles = this.findLogFiles(this.projectPath);
        let cleanedCount = 0;
        let freedSpace = 0;
        
        for (const logFile of logFiles) {
            try {
                // 只清理超过1MB的日志文件
                if (logFile.size > 1024 * 1024) {
                    // 清空日志文件而不是删除
                    fs.writeFileSync(logFile.path, '', 'utf8');
                    cleanedCount++;
                    freedSpace += logFile.size;
                    this.logger.info(`清理日志文件: ${logFile.path} (${logFile.sizeMB} MB)`);
                }
            } catch (error) {
                this.logger.warn(`清理日志文件时出错: ${logFile.path}`, error.message);
            }
        }
        
        this.logger.info(`清理完成，共清理 ${cleanedCount} 个日志文件，释放 ${(freedSpace / (1024 * 1024)).toFixed(2)} MB 空间`);
    }
    
    /**
     * 清理npm缓存
     */
    cleanupNpmCache() {
        this.logger.info('开始清理npm缓存...');
        
        try {
            execSync('npm cache clean --force', { encoding: 'utf8' });
            this.logger.info('npm缓存清理完成');
        } catch (error) {
            this.logger.warn('清理npm缓存时出错:', error.message);
        }
        
        // 清理node_modules中的缓存
        const nodeModulesPath = path.join(this.projectPath, 'node_modules', '.cache');
        if (fs.existsSync(nodeModulesPath)) {
            try {
                this.removeDir(nodeModulesPath);
                this.logger.info('node_modules缓存清理完成');
            } catch (error) {
                this.logger.warn('清理node_modules缓存时出错:', error.message);
            }
        }
    }
    
    /**
     * 清理重复文件
     */
    cleanupDuplicateFiles() {
        this.logger.info('开始清理重复文件...');
        
        const duplicateFiles = this.findDuplicateFiles(this.projectPath);
        let cleanedCount = 0;
        let freedSpace = 0;
        
        for (const duplicateGroup of duplicateFiles) {
            // 保留第一个文件，删除其他重复文件
            for (let i = 1; i < duplicateGroup.files.length; i++) {
                const duplicateFile = duplicateGroup.files[i];
                try {
                    const stat = fs.statSync(duplicateFile);
                    fs.unlinkSync(duplicateFile);
                    cleanedCount++;
                    freedSpace += stat.size;
                    this.logger.info(`清理重复文件: ${duplicateFile}`);
                } catch (error) {
                    this.logger.warn(`清理重复文件时出错: ${duplicateFile}`, error.message);
                }
            }
        }
        
        this.logger.info(`清理完成，共清理 ${cleanedCount} 个重复文件，释放 ${(freedSpace / (1024 * 1024)).toFixed(2)} MB 空间`);
    }
    
    /**
     * 优化代码文件大小
     */
    async optimizeCodeFiles() {
        this.logger.info('开始优化代码文件大小...');
        
        const jsFiles = this.findFilesByExtension(this.projectPath, '.js');
        const filesToOptimize = jsFiles.filter(file => 
            !file.includes('node_modules') && 
            !file.includes('dist') && 
            !file.includes('build')
        );
        
        this.logger.info(`找到 ${filesToOptimize.length} 个JavaScript文件需要优化`);
        
        let optimizedCount = 0;
        
        for (const jsFile of filesToOptimize) {
            try {
                const content = fs.readFileSync(jsFile, 'utf8');
                
                // 检测代码大小问题
                if (content.length > 100000) { // 超过100KB的文件
                    this.logger.info(`优化大文件: ${jsFile} (${(content.length / 1024).toFixed(2)} KB)`);
                    
                    // 使用AI优化代码
                    const optimizedContent = await this.optimizeCode(content, jsFile);
                    
                    if (optimizedContent && optimizedContent.length < content.length) {
                        fs.writeFileSync(jsFile, optimizedContent, 'utf8');
                        const savedSpace = content.length - optimizedContent.length;
                        this.logger.info(`优化完成，节省 ${(savedSpace / 1024).toFixed(2)} KB 空间`);
                        optimizedCount++;
                    }
                }
            } catch (error) {
                this.logger.warn('优化代码文件时出错:', error.message);
            }
        }
        
        this.logger.info(`代码文件优化完成，优化了 ${optimizedCount} 个文件`);
    }
    
    /**
     * 优化代码内容
     */
    async optimizeCode(code, filePath) {
        try {
            const prompt = `请优化以下代码，减少文件大小同时保持功能不变：

文件路径: ${filePath}

代码内容:
${code}

优化要求：
1. 移除不必要的注释
2. 移除空白行和多余的空格
3. 简化重复代码
4. 保持原有功能不变
5. 只返回优化后的代码，不要添加任何额外的解释`;
            
            const result = await this.aiAutoFix.aiEngine.generateResponse(prompt, { taskType: 'code' });
            return result.response;
        } catch (error) {
            this.logger.warn('优化代码时出错:', error.message);
            return null;
        }
    }
    
    /**
     * 查找指定扩展名的文件
     */
    findFilesByExtension(dir, extension) {
        const files = [];
        
        const scanDir = (currentDir) => {
            try {
                const dirFiles = fs.readdirSync(currentDir);
                for (const file of dirFiles) {
                    const filePath = path.join(currentDir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        if (file !== 'node_modules' && file !== '.git' && file !== 'dist' && file !== 'build') {
                            scanDir(filePath);
                        }
                    } else if (path.extname(file) === extension) {
                        files.push(filePath);
                    }
                }
            } catch (error) {
                // 忽略权限错误
            }
        };
        
        scanDir(dir);
        return files;
    }
    
    /**
     * 递归删除目录
     */
    removeDir(dir) {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            if (stat.isDirectory()) {
                this.removeDir(filePath);
            } else {
                fs.unlinkSync(filePath);
            }
        }
        fs.rmdirSync(dir);
    }
    
    /**
     * 提供优化建议
     */
    provideOptimizationSuggestions(diskIssues) {
        this.logger.info('=== 磁盘优化建议 ===');
        
        for (const issue of diskIssues) {
            if (issue.type === '磁盘使用率') {
                const usedPercentage = parseInt(issue.details.usedPercentage);
                if (usedPercentage > 80) {
                    this.logger.info('磁盘使用率优化建议:');
                    this.logger.info(`当前使用率: ${usedPercentage}%，建议保持在70%以下`);
                    this.logger.info('建议: 考虑清理更多不必要的文件或扩展磁盘空间');
                }
            }
            
            if (issue.type === '大文件') {
                this.logger.info('大文件优化建议:');
                issue.files.slice(0, 5).forEach(file => {
                    this.logger.info(`- ${file.path} (${file.sizeMB} MB)`);
                });
                this.logger.info('建议: 考虑压缩或移重大文件到外部存储');
            }
            
            if (issue.type === '重复文件') {
                this.logger.info('重复文件优化建议:');
                issue.files.slice(0, 3).forEach(group => {
                    this.logger.info(`- 发现 ${group.count} 个重复文件`);
                    group.files.slice(0, 2).forEach(file => {
                        this.logger.info(`  * ${file}`);
                    });
                });
                this.logger.info('建议: 定期清理重复文件以节省空间');
            }
        }
        
        this.logger.info('=== 系统级优化建议 ===');
        this.logger.info('1. 定期执行磁盘清理: npm run cleanup');
        this.logger.info('2. 使用.gitignore文件排除不必要的文件');
        this.logger.info('3. 考虑使用压缩工具压缩不常用的文件');
        this.logger.info('4. 定期备份重要数据并清理旧备份');
        this.logger.info('5. 检查并清理系统临时目录');
        this.logger.info('6. 考虑使用SSD存储以提高性能');
    }
}

// 执行磁盘优化
async function runDiskOptimization() {
    const optimizer = new AIDiskOptimizer();
    
    try {
        const initialized = await optimizer.initialize();
        if (initialized) {
            await optimizer.optimizeDisk();
        } else {
            console.error('AI磁盘优化器初始化失败');
        }
    } catch (error) {
        console.error('执行磁盘优化时出错:', error);
    }
}

if (require.main === module) {
    runDiskOptimization();
}

module.exports = AIDiskOptimizer;
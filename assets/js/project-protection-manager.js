// MTSCOS 项目自我保护和管理系统
// 作者: Chenghao Wu
// 版本: 2.0.0
// 功能: 文件完整性检查、自动备份、安全监控、性能优化

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { exec } = require('child_process');
const os = require('os');
const VikeyAPI = require('./core/vikey-api');

class ProjectProtectionManager {
    constructor(rootDir = null) {
        this.rootDir = rootDir || path.dirname(path.dirname(__filename));
        this.config = {
            // 备份配置
            backup: {
                enabled: true,
                interval: 30 * 60 * 1000, // 30分钟
                maxBackups: 15,
                excludeDirs: ['Backups', '.git', 'node_modules', '.snapshots', '.encrypted'],
                excludeFiles: ['.DS_Store', '*.tmp', '*.log']
            },
            // 文件监控配置
            fileMonitor: {
                enabled: true,
                interval: 60 * 1000, // 1分钟
                criticalExtensions: ['.js', '.html', '.css', '.json', '.sh'],
                hashAlgorithm: 'sha256'
            },
            // 安全配置
            security: {
                enabled: true,
                scanInterval: 5 * 60 * 1000, // 5分钟
                maxFileSize: 10 * 1024 * 1024, // 10MB
                suspiciousPatterns: [
                    /eval\s*\(/gi,
                    /document\.write\s*\(/gi,
                    /innerHTML\s*=/gi,
                    /outerHTML\s*=/gi
                ]
            },
            // 性能配置
            performance: {
                enabled: true,
                memoryThreshold: 0.8, // 80%
                cpuThreshold: 0.7, // 70%
                diskThreshold: 0.9 // 90%
            },
            // 封装配置
            encapsulation: {
                enabled: true,
                encryptKeySize: 256,
                criticalExtensions: ['.js', '.py', '.html', '.css', '.json', '.java', '.cpp', '.c'],
                excludeDirs: ['Backups', '.git', 'node_modules', '.snapshots', '.encrypted'],
                excludeFiles: ['.DS_Store', '*.tmp', '*.log', 'package.json', 'requirements.txt'],
                requireVikeyForEncapsulation: false // 默认封装时不需要vikey设备
            }
        };

        this.state = {
            lastBackup: null,
            fileHashes: new Map(),
            suspiciousFiles: new Set(),
            protectedFiles: new Set(),
            isEncapsulated: false,
            metrics: {
                backupCount: 0,
                securityScans: 0,
                fileChanges: 0,
                errors: 0,
                encapsulations: 0,
                decapsulations: 0
            }
        };

        this.logDir = path.join(this.rootDir, 'Logs');
        this.backupDir = path.join(this.rootDir, 'Backups');
        this.encryptedDir = path.join(this.rootDir, '.encrypted');
        // 初始化VikeyAPI
        this.vikeyAPI = new VikeyAPI();
        this.ensureDirectories().catch(error => console.error(`[project-protection-manager.js] this.ensureDirectories failed:`, error));
        this.initializeFileHashes();
        // 检查项目是否已封装
        this.checkEncapsulationStatus();
    }

    // 确保必要的目录存在
    async ensureDirectories() {
        const directories = [
            this.logDir,
            this.backupDir,
            this.encryptedDir
        ];

        for (const dir of directories) {
            try {
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
            } catch (error) {
                this.log('error', `创建目录失败: ${dir}`, error);
            }
        }
    }

    // 日志记录
    log(level, message, data = null) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
        console.log(logMessage);
        
        const logFile = path.join(this.logDir, 'project_protection.log');
        fs.appendFileSync(logFile, logMessage + '\n');
        
        if (data) {
            fs.appendFileSync(logFile, `  Data: ${JSON.stringify(data, null, 2)}\n`);
        }
    }

    // 检查项目封装状态
    checkEncapsulationStatus() {
        try {
            // 检查是否存在封装标记文件
            const encapsulationMarker = path.join(this.rootDir, '.encapsulated');
            this.state.isEncapsulated = fs.existsSync(encapsulationMarker);
            
            if (this.state.isEncapsulated) {
                this.log('info', '检测到项目已封装');
            }
        } catch (error) {
            this.log('error', '检查封装状态失败', error);
            this.state.isEncapsulated = false;
        }
    }

    // 初始化文件哈希
    initializeFileHashes() {
        this.log('info', '初始化文件完整性检查...');
        try {
            this.scanProjectFiles();
        } catch (error) {
            console.error(`[project-protection-manager.js] this.scanProjectFiles failed:`, error);
        }
    }

    // 扫描项目文件
    scanProjectFiles() {
        const scanDir = (dir, relativePath = '') => {
            const items = fs.readdirSync(dir);
            
            for (const item of items) {
                const fullPath = path.join(dir, item);
                const itemRelativePath = path.join(relativePath, item);
                
                // 跳过排除的目录
                if (this.config.backup.excludeDirs.some(excluded => 
                    itemRelativePath.includes(excluded))) {
                    continue;
                }
                
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    scanDir(fullPath, itemRelativePath);
                } else if (stat.isFile()) {
                    // 计算文件哈希
                    try {
                        const hash = this.calculateFileHash(fullPath);
                        this.state.fileHashes.set(itemRelativePath, {
                            hash,
                            size: stat.size,
                            modified: stat.mtime
                        });
                    } catch (error) {
                        this.log('error', `无法计算文件哈希: ${itemRelativePath}`, error.message);
                    }
                }
            }
        };
        
        scanDir(this.rootDir);
        this.log('info', `文件完整性检查完成，共扫描 ${this.state.fileHashes.size} 个文件`);
    }

    // 计算文件哈希
    calculateFileHash(filePath) {
        const content = fs.readFileSync(filePath);
        return crypto.createHash(this.config.fileMonitor.hashAlgorithm).update(content).digest('hex');
    }

    // 检查文件完整性
    checkFileIntegrity() {
        this.log('info', '开始文件完整性检查...');
        const changes = [];
        
        for (const [relativePath, fileInfo] of this.state.fileHashes) {
            const fullPath = path.join(this.rootDir, relativePath);
            
            if (!fs.existsSync(fullPath)) {
                changes.push({ type: 'deleted', path: relativePath });
                continue;
            }
            
            try {
                const currentHash = this.calculateFileHash(fullPath);
                if (currentHash !== fileInfo.hash) {
                    changes.push({ 
                        type: 'modified', 
                        path: relativePath,
                        oldHash: fileInfo.hash,
                        newHash: currentHash
                    });
                    
                    // 更新哈希记录
                    this.state.fileHashes.set(relativePath, {
                        hash: currentHash,
                        size: fs.statSync(fullPath).size,
                        modified: fs.statSync(fullPath).mtime
                    });
                }
            } catch (error) {
                this.log('error', `检查文件时出错: ${relativePath}`, error.message);
            }
        }
        
        if (changes.length > 0) {
            this.state.metrics.fileChanges += changes.length;
            this.log('warning', `检测到 ${changes.length} 个文件变更`, changes);
            
            // 如果有关键文件变更，触发备份
            const criticalChanges = changes.filter(change => 
                this.config.fileMonitor.criticalExtensions.some(ext => 
                    change.path.endsWith(ext)
                )
            );
            
            if (criticalChanges.length > 0) {
                this.log('warning', `检测到关键文件变更，触发自动备份`);
                this.performBackup().catch(error => console.error(`[project-protection-manager.js] this.performBackup failed:`, error));
            }
        }
        
        return changes;
    }

    // 执行备份
    performBackup() {
        if (!this.config.backup.enabled) {
            return;
        }
        
        this.log('info', '开始执行自动备份...');
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
        const version = this.getProjectVersion().catch(error => console.error(`[project-protection-manager.js] this.getProjectVersion failed:`, error));
        const backupName = `backup_${timestamp}_v${version}`;
        const backupPath = path.join(this.backupDir, backupName);
        
        try {
            // 创建备份目录
            fs.mkdirSync(backupPath, { recursive: true });
            
            // 复制项目文件
            this.copyProject(this.rootDir, backupPath);
            
            // 创建备份信息文件
            const backupInfo = {
                timestamp: new Date().toISOString(),
                version,
                fileCount: this.state.fileHashes.size,
                metrics: { ...this.state.metrics }
            };
            fs.writeFileSync(
                path.join(backupPath, 'backup_info.json'), 
                JSON.stringify(backupInfo, null, 2)
            );
            
            this.state.lastBackup = new Date();
            this.state.metrics.backupCount++;
            this.log('info', `备份完成: ${backupName}`);
            
            // 清理旧备份
            this.cleanupOldBackups().catch(error => console.error(`[project-protection-manager.js] this.cleanupOldBackups failed:`, error));
            
        } catch (error) {
            this.state.metrics.errors++;
            this.log('error', '备份失败', error.message);
        }
    }

    // 复制项目文件
    copyProject(src, dest) {
        const copyDir = (srcDir, destDir) => {
            if (!fs.existsSync(destDir)) {
                fs.mkdirSync(destDir, { recursive: true });
            }
            
            const items = fs.readdirSync(srcDir);
            
            for (const item of items) {
                const srcPath = path.join(srcDir, item);
                const destPath = path.join(destDir, item);
                
                // 跳过排除的目录和文件
                if (this.config.backup.excludeDirs.includes(item) ||
                    this.config.backup.excludeFiles.some(pattern => 
                        item.match(pattern.replace('*', '.*'))
                    )) {
                    continue;
                }
                
                const stat = fs.statSync(srcPath);
                
                if (stat.isDirectory()) {
                    copyDir(srcPath, destPath);
                } else {
                    fs.copyFileSync(srcPath, destPath);
                }
            }
        };
        
        copyDir(src, dest);
    }

    // 清理旧备份
    cleanupOldBackups() {
        try {
            const backups = fs.readdirSync(this.backupDir)
                .filter(item => item.startsWith('backup_'))
                .map(item => ({
                    name: item,
                    path: path.join(this.backupDir, item),
                    stat: fs.statSync(path.join(this.backupDir, item))
                }))
                .sort((a, b) => b.stat.mtime - a.stat.mtime);
            
            if (backups.length > this.config.backup.maxBackups) {
                const toDelete = backups.slice(this.config.backup.maxBackups);
                toDelete.forEach(backup => {
                    this.deleteDirectory(backup.path);
                    this.log('info', `已删除旧备份: ${backup.name}`);
                });
            }
        } catch (error) {
            this.log('error', '清理旧备份失败', error.message);
        }
    }

    // 递归删除目录
    deleteDirectory(dirPath) {
        if (fs.existsSync(dirPath)) {
            fs.rmSync(dirPath, { recursive: true, force: true });
        }
    }

    // 安全扫描
    performSecurityScan() {
        if (!this.config.security.enabled) {
            return;
        }
        
        this.log('info', '开始安全扫描...');
        const suspiciousFiles = [];
        
        for (const [relativePath, fileInfo] of this.state.fileHashes) {
            const fullPath = path.join(this.rootDir, relativePath);
            
            // 检查文件大小
            if (fileInfo.size > this.config.security.maxFileSize) {
                suspiciousFiles.push({
                    path: relativePath,
                    reason: '文件过大',
                    size: fileInfo.size
                });
                continue;
            }
            
            // 检查可疑模式
            if (this.config.fileMonitor.criticalExtensions.some(ext => 
                relativePath.endsWith(ext))) {
                try {
                    const content = fs.readFileSync(fullPath, 'utf8');
                    
                    for (const pattern of this.config.security.suspiciousPatterns) {
                        if (pattern.test(content)) {
                            suspiciousFiles.push({
                                path: relativePath,
                                reason: `检测到可疑模式: ${pattern.source}`,
                                pattern: pattern.source
                            });
                            break;
                        }
                    }
                } catch (error) {
                    // 忽略二进制文件的读取错误
                }
            }
        }
        
        this.state.metrics.securityScans++;
        
        if (suspiciousFiles.length > 0) {
            this.log('warning', `安全扫描发现 ${suspiciousFiles.length} 个可疑文件`, suspiciousFiles);
            suspiciousFiles.forEach(file => {
                this.state.suspiciousFiles.add(file.path);
            });
        } else {
            this.log('info', '安全扫描完成，未发现威胁');
        }
        
        return suspiciousFiles;
    }

    // 性能监控
    checkPerformance() {
        if (!this.config.performance.enabled) {
            return;
        }
        
        const metrics = {
            memory: process.memoryUsage().catch(error => console.error(`[project-protection-manager.js] process.memoryUsage failed:`, error)),
            cpu: process.cpuUsage(),
            disk: this.getDiskUsage().catch(error => console.error(`[project-protection-manager.js] this.getDiskUsage failed:`, error))
        };
        
        // 检查内存使用
        const memoryUsage = metrics.memory.heapUsed / metrics.memory.heapTotal;
        if (memoryUsage > this.config.performance.memoryThreshold) {
            this.log('warning', `内存使用率过高: ${(memoryUsage * 100).toFixed(2)}%`);
        }
        
        // 检查磁盘使用
        if (metrics.disk.used > this.config.performance.diskThreshold) {
            this.log('warning', `磁盘使用率过高: ${(metrics.disk.used * 100).toFixed(2)}%`);
        }
        
        return metrics;
    }

    // 获取磁盘使用情况
    getDiskUsage() {
        try {
            const stats = fs.statSync(this.rootDir);
            const total = 100 * 1024 * 1024 * 1024; // 假设100GB
            const used = stats.size / total;
            return { total, used: Math.min(used, 1) };
        } catch (error) {
            return { total: 0, used: 0 };
        }
    }

    // 生成加密密钥
    generateEncryptionKey() {
        try {
            // 使用随机数生成器创建加密密钥
            const key = crypto.randomBytes(this.config.encapsulation.encryptKeySize / 8);
            return key.toString('hex');
        } catch (error) {
            this.log('error', '生成加密密钥失败', error);
            throw error;
        }
    }

    // 加密文件
    encryptFile(filePath, encryptionKey) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const iv = crypto.randomBytes(16);
            const key = Buffer.from(encryptionKey, 'hex');
            const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
            let encrypted = cipher.update(content, 'utf8', 'hex');
            encrypted += cipher.final('hex');
            return {
                iv: iv.toString('hex'),
                encryptedContent: encrypted
            };
        } catch (error) {
            this.log('error', `加密文件失败: ${filePath}`, error);
            throw error;
        }
    }

    // 封装项目
    async encapsulateProject() {
        if (!this.config.encapsulation.enabled) {
            this.log('warning', '项目封装功能未启用');
            return false;
        }

        if (this.state.isEncapsulated) {
            this.log('warning', '项目已处于封装状态');
            return false;
        }

        this.log('info', '开始封装项目...');
        this.log('info', `根目录: ${this.rootDir}`);
        this.log('info', `加密目录: ${this.encryptedDir}`);

        try {
            // 生成加密密钥
            const encryptionKey = this.generateEncryptionKey();
            this.log('info', '生成加密密钥成功');

            // 创建加密目录
            if (!fs.existsSync(this.encryptedDir)) {
                this.log('info', `创建加密目录: ${this.encryptedDir}`);
                fs.mkdirSync(this.encryptedDir, { recursive: true });
            }

            // 扫描需要封装的文件
            const filesToEncrypt = [];
            const scanDirectory = (dir) => {
                this.log('info', `扫描目录: ${dir}`);
                const items = fs.readdirSync(dir);
                this.log('info', `目录 ${dir} 包含 ${items.length} 个文件/目录`);
                for (const item of items) {
                    const itemPath = path.join(dir, item);
                    const relativePath = path.relative(this.rootDir, itemPath);
                    this.log('info', `处理项目: ${relativePath}`);

                    // 跳过排除的目录和文件
                    if (this.config.encapsulation.excludeDirs.some(excludeDir => 
                        relativePath.startsWith(excludeDir) || item === excludeDir)) {
                        this.log('info', `跳过排除目录: ${relativePath}`);
                        continue;
                    }

                    // 检查文件是否匹配排除规则
                    let shouldExclude = false;
                    for (const excludeFile of this.config.encapsulation.excludeFiles) {
                        if (item === excludeFile) {
                            shouldExclude = true;
                            break;
                        }
                        // 处理glob模式（简单实现，仅支持*通配符）
                        if (excludeFile.includes('*')) {
                            const pattern = excludeFile.replace(/\./g, '\\.').replace(/\*/g, '.*');
                            const regex = new RegExp(`^${pattern}$`);
                            if (regex.test(item)) {
                                shouldExclude = true;
                                break;
                            }
                        }
                    }
                    if (shouldExclude) {
                        this.log('info', `跳过排除文件: ${relativePath}`);
                        continue;
                    }

                    try {
                        const stat = fs.statSync(itemPath);
                        if (stat.isDirectory()) {
                            this.log('info', `进入子目录: ${relativePath}`);
                            scanDirectory(itemPath);
                        } else {
                            // 只加密关键文件类型
                            if (this.config.encapsulation.criticalExtensions.some(ext => 
                                itemPath.endsWith(ext))) {
                                this.log('info', `添加文件到加密列表: ${relativePath}`);
                                filesToEncrypt.push(relativePath);
                            } else {
                                this.log('info', `跳过非关键文件: ${relativePath}`);
                            }
                        }
                    } catch (statError) {
                        this.log('error', `获取文件状态失败: ${relativePath}`, statError.message);
                    }
                }
            };

            scanDirectory(this.rootDir);

            this.log('info', `找到 ${filesToEncrypt.length} 个需要封装的文件`);

            // 加密并保存文件
            const encryptedFilesInfo = [];
            for (const relativePath of filesToEncrypt) {
                const filePath = path.join(this.rootDir, relativePath);
                const encryptedInfo = this.encryptFile(filePath, encryptionKey);
                
                // 保存加密文件
                const encryptedFilePath = path.join(this.encryptedDir, relativePath);
                const encryptedDir = path.dirname(encryptedFilePath);
                if (!fs.existsSync(encryptedDir)) {
                    fs.mkdirSync(encryptedDir, { recursive: true });
                }
                
                const encryptedContent = JSON.stringify(encryptedInfo, null, 2);
                fs.writeFileSync(encryptedFilePath, encryptedContent, 'utf8');
                
                // 创建原始文件的替代文件
                const placeholderContent = `// 此文件已被MTSCOS项目保护系统封装\n// 只有通过vikey硬件管理员认证才能访问原始内容\n// 项目保护系统版本: 2.0.0`;
                fs.writeFileSync(filePath, placeholderContent, 'utf8');
                
                encryptedFilesInfo.push(relativePath);
            }

            // 获取当前vikey设备信息用于验证（可选，不影响封装）
            let vikeyDeviceInfo = null;
            if (this.config.encapsulation.requireVikeyForEncapsulation) {
                try {
                    const findResult = await this.vikeyAPI.findVikeyDevice();
                    if (findResult.success) {
                        const verifyResult = await this.vikeyAPI.verifyVikey();
                        if (verifyResult.success) {
                            const vikeyInfo = await this.vikeyAPI.readVikeyInfo();
                            if (vikeyInfo.success && this.vikeyAPI.hasPermission(this.vikeyAPI.PERMISSION_LEVELS.VIKEY_ADMIN)) {
                                vikeyDeviceInfo = {
                                    deviceId: vikeyInfo.deviceId,
                                    deviceName: vikeyInfo.deviceName,
                                    adminLevel: vikeyInfo.adminLevel
                                };
                            } else {
                                this.log('warning', '当前vikey设备不具备管理员权限');
                            }
                        }
                    } else {
                        this.log('warning', '未找到vikey设备');
                    }
                } catch (error) {
                    this.log('warning', '获取vikey设备信息时出错', error);
                }
            }

            // 保存加密信息
            const encryptionInfo = {
                timestamp: new Date().toISOString(),
                key: encryptionKey, // 在实际应用中，这里应该使用vikey存储密钥
                files: encryptedFilesInfo,
                version: '2.0.0', // 使用固定版本号
                adminVikey: vikeyDeviceInfo // 存储管理员的vikey设备信息
            };

            // 保存加密信息到加密目录
            const encryptionInfoPath = path.join(this.encryptedDir, 'encryption-info.json');
            fs.writeFileSync(encryptionInfoPath, JSON.stringify(encryptionInfo, null, 2), 'utf8');

            // 创建封装标记文件
            const encapsulationMarker = path.join(this.rootDir, '.encapsulated');
            fs.writeFileSync(encapsulationMarker, JSON.stringify({
                timestamp: new Date().toISOString(),
                version: '2.0.0', // 使用固定版本号
                fileCount: encryptedFilesInfo.length
            }), 'utf8');

            // 更新状态
            this.state.isEncapsulated = true;
            this.state.metrics.encapsulations++;

            this.log('info', `项目封装完成，共加密 ${encryptedFilesInfo.length} 个文件`);
            return true;
        } catch (error) {
            this.log('error', '项目封装失败', { error: error.message, stack: error.stack });
            console.error('项目封装失败:', error);
            return false;
        }
    }



    // 解密文件
    decryptFile(encryptedInfo, encryptionKey) {
        try {
            const iv = Buffer.from(encryptedInfo.iv, 'hex');
            const key = Buffer.from(encryptionKey, 'hex');
            const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
            let decrypted = decipher.update(encryptedInfo.encryptedContent, 'hex', 'utf8');
            decrypted += decipher.final('utf8');
            return decrypted;
        } catch (error) {
            this.log('error', '解密文件失败', error);
            throw error;
        }
    }

    // 验证vikey硬件管理员身份
    async verifyVikeyAdmin() {
        try {
            this.log('info', '开始验证vikey硬件管理员身份...');

            // 检查vikey是否连接
            const findResult = await this.vikeyAPI.findVikeyDevice();
            if (!findResult.success) {
                this.log('error', '未找到vikey设备');
                return false;
            }

            // 验证vikey
            const verifyResult = await this.vikeyAPI.verifyVikey();
            if (!verifyResult.success) {
                this.log('error', 'vikey验证失败: ' + verifyResult.error);
                return false;
            }

            // 检查权限级别
            const vikeyInfo = await this.vikeyAPI.readVikeyInfo();
            if (!vikeyInfo.success) {
                this.log('error', '读取vikey信息失败: ' + vikeyInfo.error);
                return false;
            }

            // 检查是否为vikey硬件管理员权限
            if (!this.vikeyAPI.hasPermission(this.vikeyAPI.PERMISSION_LEVELS.VIKEY_ADMIN)) {
                this.log('error', '权限不足，需要vikey硬件管理员权限');
                return false;
            }

            this.log('info', 'vikey硬件管理员身份验证成功');
            return true;
        } catch (error) {
            this.log('error', 'vikey管理员身份验证失败', error);
            return false;
        }
    }

    // 解封项目
    async decapsulateProject() {
        if (!this.state.isEncapsulated) {
            this.log('warning', '项目未处于封装状态');
            return false;
        }

        this.log('info', '开始解封项目...');

        try {
            // 验证vikey硬件管理员身份
            const isAdmin = await this.verifyVikeyAdmin();
            if (!isAdmin) {
                this.log('error', '解封失败: 权限不足');
                return false;
            }

            // 读取加密信息
            const encryptionInfoPath = path.join(this.encryptedDir, 'encryption-info.json');
            if (!fs.existsSync(encryptionInfoPath)) {
                this.log('error', '未找到加密信息文件');
                return false;
            }

            const encryptionInfo = JSON.parse(fs.readFileSync(encryptionInfoPath, 'utf8'));
            const encryptionKey = encryptionInfo.key;
            const encryptedFiles = encryptionInfo.files;

            // 验证当前vikey设备是否与封装时的管理员设备匹配
            if (encryptionInfo.adminVikey) {
                try {
                    const currentDeviceInfo = await this.vikeyAPI.readVikeyInfo();
                    if (!currentDeviceInfo.success) {
                        this.log('error', '无法获取当前vikey设备信息');
                        return false;
                    }

                    if (currentDeviceInfo.deviceId !== encryptionInfo.adminVikey.deviceId) {
                        this.log('error', '解封失败: 设备不匹配。只有封装项目的vikey设备才能解封。');
                        return false;
                    }

                    this.log('info', 'vikey设备验证成功: 与封装时使用的设备匹配');
                } catch (error) {
                    this.log('error', 'vikey设备验证失败', error);
                    return false;
                }
            }

            this.log('info', `开始恢复 ${encryptedFiles.length} 个加密文件...`);

            // 解密并恢复文件
            for (const relativePath of encryptedFiles) {
                const encryptedFilePath = path.join(this.encryptedDir, relativePath);
                const originalFilePath = path.join(this.rootDir, relativePath);

                if (!fs.existsSync(encryptedFilePath)) {
                    this.log('warning', `加密文件不存在: ${encryptedFilePath}`);
                    continue;
                }

                try {
                    // 读取加密信息
                    const encryptedInfo = JSON.parse(fs.readFileSync(encryptedFilePath, 'utf8'));
                    
                    // 解密文件
                    const decryptedContent = this.decryptFile(encryptedInfo, encryptionKey);
                    
                    // 恢复原始文件
                    fs.writeFileSync(originalFilePath, decryptedContent, 'utf8');
                    
                    this.log('info', `已恢复文件: ${relativePath}`);
                } catch (error) {
                    this.log('error', `恢复文件失败: ${relativePath}`, error);
                }
            }

            // 清理加密目录
            if (fs.existsSync(this.encryptedDir)) {
                fs.rmSync(this.encryptedDir, { recursive: true, force: true });
            }

            // 删除封装标记文件
            const encapsulationMarker = path.join(this.rootDir, '.encapsulated');
            if (fs.existsSync(encapsulationMarker)) {
                fs.unlinkSync(encapsulationMarker);
            }

            // 更新状态
            this.state.isEncapsulated = false;
            this.state.metrics.decapsulations++;

            this.log('info', '项目解封完成');
            return true;
        } catch (error) {
            this.log('error', '项目解封失败', error);
            return false;
        }
    }

    // 获取系统状态
    getStatus() {
        return {
            uptime: process.uptime(),
            lastBackup: this.state.lastBackup,
            metrics: { ...this.state.metrics },
            fileCount: this.state.fileHashes.size,
            suspiciousFiles: Array.from(this.state.suspiciousFiles),
            protectedFiles: Array.from(this.state.protectedFiles),
            isEncapsulated: this.state.isEncapsulated,
            config: this.config
        };
    }

    // 启动保护系统
    start() {
        this.log('info', '启动MTSCOS项目保护系统...');
        
        // 文件完整性检查
        if (this.config.fileMonitor.enabled) {
            setInterval(() => {
                this.checkFileIntegrity().catch(error => console.error(`[project-protection-manager.js] this.checkFileIntegrity failed:`, error));
            }, this.config.fileMonitor.interval);
        }
        
        // 自动备份
        if (this.config.backup.enabled) {
            setInterval(() => {
                this.performBackup().catch(error => console.error(`[project-protection-manager.js] this.performBackup failed:`, error));
            }, this.config.backup.interval);
        }
        
        // 安全扫描
        if (this.config.security.enabled) {
            setInterval(() => {
                this.performSecurityScan().catch(error => console.error(`[project-protection-manager.js] this.performSecurityScan failed:`, error));
            }, this.config.security.scanInterval);
        }
        
        // 性能监控
        if (this.config.performance.enabled) {
            setInterval(() => {
                this.checkPerformance().catch(error => console.error(`[project-protection-manager.js] this.checkPerformance failed:`, error));
            }, 60000); // 每分钟检查一次
        }
        
        // 立即执行一次完整检查
        this.checkFileIntegrity().catch(error => console.error(`[project-protection-manager.js] this.checkFileIntegrity failed:`, error));
        this.performSecurityScan();
        this.checkPerformance().catch(error => console.error(`[project-protection-manager.js] this.checkPerformance failed:`, error));
        
        this.log('info', 'MTSCOS项目保护系统已启动');
    }

    // 停止保护系统
    stop() {
        this.log('info', '停止MTSCOS项目保护系统...');
        // 这里可以添加清理逻辑
    }
}

// 创建并启动保护系统
const protectionManager = new ProjectProtectionManager();

// 导出模块
module.exports = ProjectProtectionManager;

// 如果直接运行此脚本，启动保护系统
if (require.main === module) {
    protectionManager.start().catch(error => console.error(`[project-protection-manager.js] protectionManager.start failed:`, error));
    
    // 优雅关闭
    process.on('SIGINT', () => {
        protectionManager.stop().catch(error => console.error(`[project-protection-manager.js] protectionManager.stop failed:`, error));
        process.exit(0);
    });
    
    process.on('SIGTERM', () => {
        protectionManager.stop().catch(error => console.error(`[project-protection-manager.js] protectionManager.stop failed:`, error));
        process.exit(0);
    });
}

console.log('[MTSCOS] 项目保护系统已加载');
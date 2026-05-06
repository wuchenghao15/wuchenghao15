#!/usr/bin/env node
// VERSION: 20251106.2cee889cbf5b90dda6bfd8

/**
 * MTSCOS 版本更新管理脚本
 * 功能：自动生成和更新所有脚本和HTML文件的内部版本号
 * 版本：2.0.0 - 增强版
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

// 配置
const CONFIG = {
    // 需要处理的文件类型
    FILE_TYPES: {
        SCRIPT: ['sh', 'js', 'py', 'html'],
        HTML: ['html'],
        IGNORE_DIRS: ['node_modules', '.git', '.svn', 'logs', 'temp', 'tmp', 'Backups', 'Logs']
    },
    // 版本号格式和注释格式
    VERSION_PATTERNS: {
        SH: /#\s*VERSION:\s*[\d.]+/g,
        JS: /\/\/\s*VERSION:\s*[\d.]+/g,
        PY: /#\s*VERSION:\s*[\d.]+/g,
        HTML: /<!--\s*VERSION:\s*[\d.]+\s*-->/g
    },
    // 用于替换的新注释格式
    REPLACEMENT_PATTERNS: {
        SH: '# VERSION: VERSION_PLACEHOLDER',
        JS: '// VERSION: VERSION_PLACEHOLDER',
        PY: '# VERSION: VERSION_PLACEHOLDER',
        HTML: '<!-- VERSION: VERSION_PLACEHOLDER -->'
    },
    // 日志配置
    LOG_CONFIG: {
        LOG_DIR: './Logs',
        LOG_FILE: 'version_update.log'
    },
    // 备份配置
    BACKUP_CONFIG: {
        ENABLED: true,
        BACKUP_DIR: './Backups/auto_version_backup',
        MAX_BACKUPS: 5
    },
    // 性能配置
    PERFORMANCE_CONFIG: {
        CHUNK_SIZE: 100,
        PROGRESS_INTERVAL: 100
    }
};

/**
 * 日志管理器
 */
class Logger {
    constructor() {
        this.logDir = CONFIG.LOG_CONFIG.LOG_DIR;
        this.logFile = CONFIG.LOG_CONFIG.LOG_FILE;
        this.logFilePath = path.join(this.logDir, this.logFile);
        
        // 确保日志目录存在
        this.ensureLogDirExists();
    };

    
    ensureLogDirExists() {
        try {
            if (!fs.existsSync(this.logDir)) {
                fs.mkdirSync(this.logDir, { recursive: true });
            };

        } catch (error) {
            console.error(`创建日志目录失败: ${error.message}`);
        };

    };

    
    getTimestamp() {
        return new Date().toISOString().replace('T', ' ').substring(0, 19);
    };

    
    log(message, level = 'INFO') {
        const timestamp = this.getTimestamp();
        const logMessage = `[${timestamp}] [${level}] ${message}`;
        
        // 输出到控制台
        if (level === 'ERROR') {
            console.error(logMessage);
        } else {
            console.log(logMessage);
        };

        
        // 写入日志文件
        try {
            fs.appendFileSync(this.logFilePath, logMessage + '/n', 'utf8');
        } catch (error) {
            console.error(`写入日志文件失败: ${error.message}`);
        };

    };

    
    info(message) {
        this.log(message, 'INFO');
    };

    
    error(message) {
        this.log(message, 'ERROR');
    };

    
    warning(message) {
        this.log(message, 'WARNING');
    };

    
    success(message) {
        this.log(message, 'SUCCESS');
    };

};


// 创建全局日志实例
const logger = new Logger();

/**
 * 文件备份管理器
 */
class BackupManager {
    constructor() {
        this.enabled = CONFIG.BACKUP_CONFIG.ENABLED;
        this.backupDir = CONFIG.BACKUP_CONFIG.BACKUP_DIR;
        this.maxBackups = CONFIG.BACKUP_CONFIG.MAX_BACKUPS;
        
        if (this.enabled) {
            this.ensureBackupDirExists();
        };

    };

    
    ensureBackupDirExists() {
        try {
            if (!fs.existsSync(this.backupDir)) {
                fs.mkdirSync(this.backupDir, { recursive: true });
            };

        } catch (error) {
            logger.error(`创建备份目录失败: ${error.message}`);
            this.enabled = false;
        };

    };

    
    getBackupFileName(originalFilePath) {
        const relativePath = path.relative(process.cwd(), originalFilePath).replace(/\/\//g, '_');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        return `${relativePath}_${timestamp}.bak`;
    }

    
    backupFile(filePath) {
        if (!this.enabled) return false;
        
        try {
            const backupFileName = this.getBackupFileName(filePath);
            const backupPath = path.join(this.backupDir, backupFileName);
            
            fs.copyFileSync(filePath, backupPath);
            logger.info(`文件已备份: ${backupPath}`);
            
            // 清理旧备份
            this.cleanupOldBackups();
            
            return true;
        } catch (error) {
            logger.error(`备份文件失败 [${filePath}]: ${error.message}`);
            return false;
        }
    }

    
    cleanupOldBackups() {
        try {
            const files = fs.readdirSync(this.backupDir)
                .map(file => path.join(this.backupDir, file))
                .filter(file => fs.statSync(file).isFile())
                .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
            
            while (files.length > this.maxBackups) {
                const fileToDelete = files.pop();
                fs.unlinkSync(fileToDelete);
                logger.info(`已清理旧备份: ${fileToDelete}`);
            }

        } catch (error) {
            logger.error(`清理旧备份失败: ${error.message}`);
        }
    }

};


// 创建全局备份实例
const backupManager = new BackupManager();

/**
 * 进度显示管理器
 */
class ProgressManager {
    constructor(total) {
        this.total = total;
        this.current = 0;
        this.lastUpdate = Date.now();
        this.updateInterval = CONFIG.PERFORMANCE_CONFIG.PROGRESS_INTERVAL;
    }

    
    update() {
        this.current++;
        const now = Date.now();
        
        // 限制更新频率
        if (now - this.lastUpdate >= this.updateInterval) {
            const percentage = Math.round((this.current / this.total) * 100);
            process.stdout.write(`\r处理进度: ${this.current}/${this.total} (${percentage}%)`);
            this.lastUpdate = now;
        }
    }

    
    complete() {
        process.stdout.write(`\r处理完成: ${this.current}/${this.total} (100%)\n`);
    }
};


/**
 * 生成文件的哈希值（基于文件内容）
 * @param {string} filePath - 文件路径
 * @returns {string} 文件哈希值
 */
function generateFileHash(filePath) {
    try {
        // 处理大文件时使用流
        const stream = fs.createReadStream(filePath, { encoding: 'utf8' });
        const hash = crypto.createHash('md5');
        
        return new Promise((resolve, reject) => {
            stream.on('data', (chunk) => hash.update(chunk));
            stream.on('end', () => resolve(hash.digest('hex').substring(0, 8)));
            stream.on('error', (error) => {
                logger.error(`生成文件哈希失败 [${filePath}]: ${error.message}`);
                reject(error);
            });
        });
    } catch (error) {
        logger.error(`生成文件哈希失败 [${filePath}]: ${error.message}`);
        return Promise.resolve(null);
    }
}


/**
 * 生成版本号（时间戳 + 文件哈希）
 * @param {string} filePath - 文件路径
 * @returns {Promise<string>} 版本号
 */
async function generateVersionNumber(filePath) {
    const now = new Date();
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
    let hash = 'unknown';
    
    try {
        hash = await generateFileHash(filePath);
    } catch (error) {
        logger.warning(`使用备用哈希生成方法 [${filePath}]`);
        // 备用哈希生成方法
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            hash = crypto.createHash('md5').update(content).digest('hex').substring(0, 8);
        } catch (e) {
            logger.error(`备用哈希生成也失败 [${filePath}]: ${e.message}`);
        }
    }

    
    return `${timestamp}.${hash}`;
}


/**
 * 获取文件类型对应的配置
 * @param {string} extension - 文件扩展名
 * @returns {object} 文件类型配置
 */
function getFileConfig(extension) {
    const ext = extension.toLowerCase();
    if (['sh'].includes(ext)) return { type: 'SH' };
    if (['js', 'json'].includes(ext)) return { type: 'JS' };
    if (['py'].includes(ext)) return { type: 'PY' };
    if (['html'].includes(ext)) return { type: 'HTML' };
    return null;
}


/**
 * 更新单个文件的版本号
 * @param {string} filePath - 文件路径
 * @returns {Promise<boolean>} 是否成功更新
 */
async function updateFileVersion(filePath) {
    try {
        // 检查文件是否存在
        if (!fs.existsSync(filePath)) {
            logger.error(`文件不存在: ${filePath}`);
            return false;
        }

        
        // 获取文件扩展名
        const ext = path.extname(filePath).substring(1);
        const config = getFileConfig(ext);
        
        // 如果文件类型不支持，跳过
        if (!config) {
            return false;
        }

        
        // 读取文件内容
        let content;
        try {
            content = fs.readFileSync(filePath, 'utf8');
        } catch (readError) {
            logger.error(`读取文件失败 [${filePath}]: ${readError.message}`);
            return false;
        }

        
        const pattern = CONFIG.VERSION_PATTERNS[config.type];
        const replacementPattern = CONFIG.REPLACEMENT_PATTERNS[config.type];
        
        if (!pattern || !replacementPattern) {
            logger.warning(`不支持的文件类型配置: ${config.type}`);
            return false;
        }

        
        // 生成新版本号
        const newVersion = await generateVersionNumber(filePath);
        const replacement = replacementPattern.replace('VERSION_PLACEHOLDER', newVersion);
        
        // 检查文件中是否已有版本注释
        let newContent;
        // 重置正则表达式的lastIndex
        pattern.lastIndex = 0;
        if (pattern.test(content)) {
            // 重置正则表达式的lastIndex
            pattern.lastIndex = 0;
            // 替换现有版本号
            newContent = content.replace(pattern, replacement);
        } else {
            // 添加新的版本注释
            // 根据文件类型添加到适当位置
            if (config.type === 'HTML') {
                // HTML 文件添加到 head 标签内
                if (content.includes('<head>')) {
                    newContent = content.replace('<head>', `<head>\n    ${replacement}`);
                } else {
                    // 如果没有 head 标签，添加到文件开头
                    newContent = `${replacement}\n${content}`;
                }

            } else {
                // 脚本文件添加到文件开头，在可能的 shebang 之后
                if (content.startsWith('#!')) {
                    const firstLineEnd = content.indexOf('\n');
                    if (firstLineEnd !== -1) {
                        newContent = content.substring(0, firstLineEnd + 1) + 
                                    `${replacement}\n` + 
                                    content.substring(firstLineEnd + 1);
                    } else {
                        newContent = `${content}\n${replacement}`;
                    }

                } else {
                    // 没有 shebang，直接添加到开头
                    newContent = `${replacement}\n${content}`;
                }

            }

        }

        
        // 备份文件
        backupManager.backupFile(filePath);
        
        // 写入更新后的内容
        try {
            fs.writeFileSync(filePath, newContent, 'utf8');
            logger.success(`已更新版本: ${filePath} -> ${newVersion}`);
            return true;
        } catch (writeError) {
            logger.error(`写入文件失败 [${filePath}]: ${writeError.message}`);
            return false;
        }

    } catch (error) {
        logger.error(`更新文件版本失败 [${filePath}]: ${error.message}`);
        return false;
    }
}


/**
 * 递归收集目录中的所有文件
 * @param {string} dirPath - 目录路径
 * @returns {object} 包含文件数组和错误数组的对象
 */
function collectFiles(dirPath) {
    const files = [];
    const errors = [];
    
    try {
        if (!fs.existsSync(dirPath)) {
            throw new Error(`目录不存在: ${dirPath}`);
        }

        const entries = fs.readdirSync(dirPath);
        
        for (const entry of entries) {
            try {
                const fullPath = path.join(dirPath, entry);
                
                try {
                    const stat = fs.statSync(fullPath);
                    
                    if (stat.isDirectory()) {
                        if (!CONFIG.FILE_TYPES.IGNORE_DIRS.includes(entry)) {
                            try {
                                const subResult = collectFiles(fullPath);
                                files.push(...subResult.files);
                                errors.push(...subResult.errors);
                            } catch (subDirError) {
                                const errorMsg = `处理子目录失败 ${fullPath}: ${subDirError.message}`;
                                errors.push(errorMsg);
                                logger.error(errorMsg);
                            }
                        }

                    } else if (stat.isFile()) {
                        const ext = path.extname(fullPath).substring(1).toLowerCase();
                        if (CONFIG.FILE_TYPES.SCRIPT.includes(ext)) {
                            files.push(fullPath);
                        }
                    }

                } catch (entryError) {
                    const errorMsg = `无法访问 ${fullPath}: ${entryError.message}`;
                    errors.push(errorMsg);
                    logger.warning(errorMsg);
                    continue;
                }

            } catch (itemError) {
                const errorMsg = `处理项目失败 ${entry}: ${itemError.message}`;
                errors.push(errorMsg);
                logger.error(errorMsg);
            }
        }

    } catch (error) {
        const errorMsg = `收集文件失败 [${dirPath}]: ${error.message}`;
        errors.push(errorMsg);
        logger.error(errorMsg);
    }

    
    return { files, errors };
}


/**
 * 批量处理文件
 * @param {Array<string>} files - 文件路径数组
 * @returns {object} 处理结果统计
 */
async function processFiles(files) {
    const stats = {
        total: files.length,
        updated: 0,
        skipped: 0,
        failed: 0
    };
    
    if (stats.total === 0) {
        logger.info('没有找到需要处理的文件');
        return stats;
    }

    
    logger.info(`开始处理 ${stats.total} 个文件...`);
    
    const progressManager = new ProgressManager(stats.total);
    const chunkSize = CONFIG.PERFORMANCE_CONFIG.CHUNK_SIZE;
    
    // 分块处理文件以提高性能
    for (let i = 0; i < files.length; i += chunkSize) {
        const chunk = files.slice(i, i + chunkSize);
        
        // 并行处理每个块
        const promises = chunk.map(async (filePath) => {
            try {
                const result = await updateFileVersion(filePath);
                progressManager.update();
                return result;
            } catch (error) {
                logger.error(`处理文件时发生异常 [${filePath}]: ${error.message}`);
                progressManager.update();
                return false;
            }

        });
        
        const results = await Promise.all(promises);
        
        // 统计结果
        results.forEach(success => {
            if (success) {
                stats.updated++;
            } else {
                stats.failed++;
            }

        });
    }

    
    progressManager.complete();
    return stats;
};


/**
 * 递归处理目录中的所有文件
 * @param {string} dirPath - 目录路径
 * @returns {Promise<object>} 处理结果统计
 */
async function processDirectory(dirPath) {
    logger.info(`开始扫描目录: ${dirPath}`);
    
    const files = collectFiles(dirPath);
    return await processFiles(files);
}


/**
 * 挂载ViKey相关文件
 * @returns {Promise<boolean>} 是否成功挂载
 */
async function mountViKeyFiles() {
    const vikeyFiles = [
        { source: '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Scripts/ViKey.CAB', target: './ViKey.CAB' },
        { source: '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Scripts/ViKey.Dll', target: './ViKey.Dll' },
        { source: '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Scripts/ViKeyInterface.js', target: '../JavaScript/ViKeyInterface.js' }
    ];
    
    let success = true;
    let mountedCount = 0;
    
    for (const file of vikeyFiles) {
        try {
            logger.info(`挂载ViKey文件: ${file.source} -> ${file.target}`);
            
            // 检查源文件是否存在
            if (!fs.existsSync(file.source)) {
                logger.error(`源文件不存在: ${file.source}`);
                success = false;
                continue;
            }

            
            // 确保目标目录存在
            const targetDir = path.dirname(file.target);
            if (!fs.existsSync(targetDir)) {
                fs.mkdirSync(targetDir, { recursive: true });
                logger.info(`已创建目录: ${targetDir}`);
            }

            
            // 备份目标文件（如果存在）
            if (fs.existsSync(file.target)) {
                backupManager.backupFile(file.target);
            }

            
            // 复制文件
            fs.copyFileSync(file.source, file.target);
            mountedCount++;
            logger.success(`✓ 成功挂载: ${file.target}`);
            
            // 设置正确的文件权限
            try {
                if (process.platform !== 'win32') {
                    fs.chmodSync(file.target, 0o644);
                }

            } catch (chmodError) {
                logger.warning(`设置文件权限失败 [${file.target}]: ${chmodError.message}`);
            }

            
            // 如果是脚本文件，更新其版本号
            if (file.target.endsWith('.js')) {
                await updateFileVersion(file.target);
            }

        } catch (error) {
            logger.error(`✗ 挂载失败 [${file.target}]: ${error.message}`);
            success = false;
        }

    }

    
    logger.info(`ViKey文件挂载完成，成功挂载 ${mountedCount}/${vikeyFiles.length} 个文件`);
    return success;
}


/**
 * 验证系统环境
 * @returns {boolean} 环境是否有效
 */
function validateEnvironment() {
    logger.info('验证系统环境...');
    
    // 检查Node.js版本
    const nodeVersion = process.version;
    logger.info(`Node.js 版本: ${nodeVersion}`);
    
    // 检查必要的目录
    const requiredDirs = [
        './HTML',
        './JavaScript',
        './CSS'
    ];
    
    for (const dir of requiredDirs) {
        if (!fs.existsSync(dir)) {
            logger.warning(`目录不存在: ${dir}`);
        }

    }

    
    return true;
}


/**
 * 记录系统信息
 */
function logSystemInfo() {
    try {
        const platform = process.platform;
        const arch = process.arch;
        const hostname = require('os').hostname();
        
        logger.info(`系统信息: ${platform} ${arch} (${hostname})`);
        
        // 尝试获取Git信息（如果可用）
        try {
            const gitBranch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
            const gitCommit = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim().substring(0, 7);
            logger.info(`Git信息: ${gitBranch} (${gitCommit})`);
        } catch (gitError) {
            logger.info('Git信息不可用');
        }
    } catch (error) {
        logger.error(`获取系统信息失败: ${error.message}`);
    }
}


/**
 * 主函数
 */
async function main() {
    logger.info('====================================');
    logger.info('  MTSCOS 版本更新管理脚本 (v2.0.0)');
    logger.info('====================================');
    
    // 记录开始时间
    const startTime = Date.now();
    
    try {
        // 验证环境
        if (!validateEnvironment()) {
            logger.error('环境验证失败，退出程序');
            process.exit(1);
        };

        
        // 记录系统信息
        logSystemInfo();
        
        // 获取项目根目录
        const projectRoot = process.cwd();
        logger.info(`项目根目录: ${projectRoot}`);
        
        // 挂载ViKey文件
        logger.info('/n开始挂载ViKey相关文件...');
        const vikeyResult = await mountViKeyFiles();
        logger.info(vikeyResult ? 'ViKey文件挂载完成！' : '部分ViKey文件挂载失败！');
        
        // 更新所有文件版本号
        logger.info('/n开始更新文件版本号...');
        const stats = await processDirectory(projectRoot);
        
        // 计算执行时间
        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);
        
        // 显示统计结果
        logger.info('/n====================================');
        logger.info('更新统计:');
        logger.info(`总文件数: ${stats.total}`);
        logger.info(`成功更新: ${stats.updated}`);
        logger.info(`跳过文件: ${stats.skipped}`);
        logger.info(`更新失败: ${stats.failed}`);
        logger.info(`执行时间: ${duration} 秒`);
        logger.info('====================================');
        
        // 设置退出码
        process.exit(stats.failed > 0 ? 1 : 0);
    } catch (error) {
        logger.error(`执行过程中发生致命错误: ${error.message}`);
        logger.error(error.stack);
        process.exit(1);
    };

};


// 执行主函数
if (require.main === module) {
    main().catch(error => {
        console.error('未捕获的异常:', error);
        process.exit(1);
    });
};


// 导出函数供其他脚本使用
module.exports = {
    generateVersionNumber,
    updateFileVersion,
    processDirectory,
    mountViKeyFiles,
    collectFiles,
    processFiles,
    logger,
    backupManager
};
// backup_manager.js - 自动管理bak文件和触发更新机制
// 版本: 1.3.0
// 创建时间: 2025-11-08

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 配置参数
const CONFIG = {
    projectRoot: path.resolve(__dirname, '..'),
    backupDir: path.resolve(__dirname, '..', 'Backups'),
    logDir: path.resolve(__dirname, '..', 'Logs'),
    maxBackups: 10, // 保留的最大备份数量
    maxBackupSize: 5 * 1024 * 1024 * 1024, // 最大备份总大小（5GB）
    fileExtensions: ['.bak', '.backup', '.old', '.copy', '.original'], // 需要管理的文件扩展名
    excludedDirs: ['node_modules', 'vendor', 'logs', 'temp'] // 排除的目录
};

// 创建必要的目录
function ensureDirectories() {
    console.log('检查必要的目录...');
    
    if (!fs.existsSync(CONFIG.backupDir)) {
        fs.mkdirSync(CONFIG.backupDir, { recursive: true });
        console.log(`创建备份目录: ${CONFIG.backupDir}`);
    }
    
    if (!fs.existsSync(CONFIG.logDir)) {
        fs.mkdirSync(CONFIG.logDir, { recursive: true });
        console.log(`创建日志目录: ${CONFIG.logDir}`);
    }
    
    // 创建归档子目录
    const archiveDir = path.join(CONFIG.backupDir, 'archived');
    if (!fs.existsSync(archiveDir)) {
        fs.mkdirSync(archiveDir, { recursive: true });
        console.log(`创建归档目录: ${archiveDir}`);
    }
}

// 记录日志
function log(message, type = 'INFO') {
    const logFile = path.join(CONFIG.logDir, 'backup_manager.log');
    const timestamp = new Date().toLocaleString('zh-CN');
    const logEntry = `[${timestamp}] [${type}] ${message}\n`;
    
    console.log(`${type}: ${message}`);
    fs.appendFileSync(logFile, logEntry);
}

// 遍历目录查找bak文件
function findBackupFiles(dir) {
    const backupFiles = [];
    
    function traverse(currentDir) {
        // 检查是否是排除的目录
        const dirName = path.basename(currentDir);
        if (CONFIG.excludedDirs.includes(dirName)) {
            return;
        }
        
        try {
            const files = fs.readdirSync(currentDir);
            
            files.forEach(file => {
                const fullPath = path.join(currentDir, file);
                const stats = fs.statSync(fullPath);
                
                if (stats.isDirectory().catch(error => console.error(`[backup_manager.js] stats.isDirectory failed:`, error))) {
                    // 递归遍历子目录
                    traverse(fullPath);
                } else if (stats.isFile().catch(error => console.error(`[backup_manager.js] stats.isFile failed:`, error))) {
                    // 检查文件扩展名
                    const ext = path.extname(file).toLowerCase();
                    if (CONFIG.fileExtensions.includes(ext)) {
                        backupFiles.push({
                            path: fullPath,
                            size: stats.size,
                            mtime: stats.mtime.getTime().catch(error => console.error(`[backup_manager.js] mtime.getTime failed:`, error))
                        });
                    }
                }
            });
        } catch (error) {
            log(`遍历目录出错: ${currentDir} - ${error.message}`, 'ERROR');
        }
    }
    
    traverse(dir);
    return backupFiles;
}

// 计算目录大小
function getDirectorySize(dir) {
    let totalSize = 0;
    
    try {
        const files = fs.readdirSync(dir);
        
        for (const file of files) {
            const fullPath = path.join(dir, file);
            const stats = fs.statSync(fullPath);
            
            if (stats.isDirectory().catch(error => console.error(`[backup_manager.js] stats.isDirectory failed:`, error))) {
                totalSize += getDirectorySize(fullPath);
            } else if (stats.isFile().catch(error => console.error(`[backup_manager.js] stats.isFile failed:`, error))) {
                totalSize += stats.size;
            }
        }
    } catch (error) {
        log(`计算目录大小出错: ${dir} - ${error.message}`, 'ERROR');
    }
    
    return totalSize;
}

// 移动文件到归档目录
function archiveBackupFile(file) {
    try {
        const archiveDir = path.join(CONFIG.backupDir, 'archived');
        const fileName = path.basename(file.path);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const archiveFileName = `${fileName}.${timestamp}`;
        const archivePath = path.join(archiveDir, archiveFileName);
        
        fs.renameSync(file.path, archivePath);
        log(`已归档文件: ${file.path} -> ${archivePath}`);
        
        // 触发更新机制
        triggerUpdateMechanism('file_archived', {
            originalPath: file.path,
            archivePath: archivePath,
            fileName: fileName
        });
        
        return true;
    } catch (error) {
        log(`归档文件失败: ${file.path} - ${error.message}`, 'ERROR');
        return false;
    }
}

// 管理bak文件
function manageBackupFiles() {
    log('开始管理备份文件...');
    
    // 查找所有备份文件
    const backupFiles = findBackupFiles(CONFIG.projectRoot);
    log(`找到 ${backupFiles.length} 个备份文件`);
    
    // 按修改时间排序（最旧的在前）
    backupFiles.sort((a, b) => a.mtime - b.mtime);
    
    // 计算备份目录总大小
    const backupDirSize = getDirectorySize(CONFIG.backupDir);
    log(`备份目录当前大小: ${formatBytes(backupDirSize)}`);
    
    let archivedCount = 0;
    let errorCount = 0;
    
    // 1. 清理超过数量限制的文件
    while (backupFiles.length > 0 && archivedCount < backupFiles.length - CONFIG.maxBackups) {
        const oldestFile = backupFiles[archivedCount];
        if (archiveBackupFile(oldestFile)) {
            archivedCount++;
        } else {
            errorCount++;
            // 跳过失败的文件
            archivedCount++;
        }
    }
    
    // 2. 如果仍然超过大小限制，继续清理最旧的文件
    let currentSize = getDirectorySize(CONFIG.backupDir);
    let index = archivedCount;
    
    while (currentSize > CONFIG.maxBackupSize && index < backupFiles.length) {
        const file = backupFiles[index];
        if (archiveBackupFile(file)) {
            archivedCount++;
            // 更新当前大小
            currentSize = getDirectorySize(CONFIG.backupDir);
        } else {
            errorCount++;
        }
        index++;
    }
    
    log(`备份文件管理完成 - 已归档: ${archivedCount}, 错误: ${errorCount}`);
    log(`最终备份目录大小: ${formatBytes(currentSize)}`);
    
    return { archivedCount, errorCount, finalSize: currentSize };
}

// 触发更新机制
function triggerUpdateMechanism(eventType, eventData) {
    log(`触发更新机制 - 事件类型: ${eventType}`);
    
    try {
        // 1. 记录更新事件
        const updateLogFile = path.join(CONFIG.logDir, 'update_events.log');
        const timestamp = new Date().toISOString();
        const logEntry = JSON.stringify({
            timestamp,
            eventType,
            eventData
        }) + '\n';
        
        fs.appendFileSync(updateLogFile, logEntry);
        
        // 2. 创建或更新更新标记文件
        const updateFlagFile = path.join(CONFIG.projectRoot, '.update_required');
        fs.writeFileSync(updateFlagFile, timestamp);
        
        // 3. 如果有更新脚本，可以在这里调用
        // 例如：execSync('node ' + path.join(CONFIG.projectRoot, 'Scripts', 'update_system.js'), { stdio: 'inherit' });
        
    } catch (error) {
        log(`触发更新机制失败: ${error.message}`, 'ERROR');
    }
}

// 格式化为易读的字节大小
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// 将页面CSS和JS统一转存到指定文件夹
function relocateResources() {
    log('开始统一管理资源文件...');
    
    // 创建目标目录
    const cssTargetDir = path.join(CONFIG.projectRoot, 'HTML', 'css_unified');
    const jsTargetDir = path.join(CONFIG.projectRoot, 'HTML', 'js_unified');
    
    [cssTargetDir, jsTargetDir].forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
            log(`创建资源目录: ${dir}`);
        }
    });
    
    // 定义需要处理的HTML文件
    const htmlDir = path.join(CONFIG.projectRoot, 'HTML');
    const htmlFiles = [];
    
    try {
        const files = fs.readdirSync(htmlDir);
        htmlFiles.push(...files.filter(file => path.extname(file).toLowerCase() === '.html'));
    } catch (error) {
        log(`读取HTML目录失败: ${error.message}`, 'ERROR');
        return { success: false, error: error.message };
    }
    
    let cssCount = 0;
    let jsCount = 0;
    
    // 处理每个HTML文件
    htmlFiles.forEach(htmlFile => {
        const htmlPath = path.join(htmlDir, htmlFile);
        let content;
        
        try {
            content = fs.readFileSync(htmlPath, 'utf8');
        } catch (error) {
            log(`读取HTML文件失败: ${htmlFile} - ${error.message}`, 'ERROR');
            return;
        }
        
        // 备份原始文件
        const backupPath = htmlPath + '.before_relocate';
        fs.writeFileSync(backupPath, content);
        
        // 处理CSS引用
        content = content.replace(/<link\s+rel="stylesheet"\s+href="([^"]+)"[^>]*>/g, (match, href) => {
            // 跳过CDN资源
            if (href.startsWith('http://') || href.startsWith('https://')) {
                return match;
            }
            
            try {
                // 解析相对路径
                const cssPath = path.resolve(path.dirname(htmlPath), href);
                if (fs.existsSync(cssPath)) {
                    // 复制到统一目录
                    const cssFileName = path.basename(cssPath);
                    const targetPath = path.join(cssTargetDir, cssFileName);
                    fs.copyFileSync(cssPath, targetPath);
                    
                    cssCount++;
                    log(`已复制CSS文件: ${cssPath} -> ${targetPath}`);
                    
                    // 更新引用路径
                    return `<link rel="stylesheet" href="css_unified/${cssFileName}">`;
                }
            } catch (error) {
                log(`处理CSS引用失败: ${href} - ${error.message}`, 'ERROR');
            }
            
            return match;
        });
        
        // 处理JS引用
        content = content.replace(/<script\s+src="([^"]+)"[^>]*><\/script>/g, (match, src) => {
            // 跳过CDN资源
            if (src.startsWith('http://') || src.startsWith('https://')) {
                return match;
            }
            
            try {
                // 解析相对路径
                const jsPath = path.resolve(path.dirname(htmlPath), src);
                if (fs.existsSync(jsPath)) {
                    // 复制到统一目录
                    const jsFileName = path.basename(jsPath);
                    const targetPath = path.join(jsTargetDir, jsFileName);
                    fs.copyFileSync(jsPath, targetPath);
                    
                    jsCount++;
                    log(`已复制JS文件: ${jsPath} -> ${targetPath}`);
                    
                    // 更新引用路径
                    return `<script src="js_unified/${jsFileName}"></script>`;
                }
            } catch (error) {
                log(`处理JS引用失败: ${src} - ${error.message}`, 'ERROR');
            }
            
            return match;
        });
        
        // 写回更新后的内容
        fs.writeFileSync(htmlPath, content);
        log(`已更新HTML文件: ${htmlFile}`);
    });
    
    log(`资源文件统一管理完成 - 处理CSS: ${cssCount}, 处理JS: ${jsCount}`);
    
    // 触发更新机制
    triggerUpdateMechanism('resources_relocated', {
        cssFiles: cssCount,
        jsFiles: jsCount,
        htmlFiles: htmlFiles.length
    });
    
    return { success: true, cssFiles: cssCount, jsFiles: jsCount };
}

// 主函数
function main() {
    console.log('========================================');
    console.log('MTSCOS 备份管理器 v1.3.0');
    console.log('========================================');
    
    try {
        // 1. 确保目录结构
        ensureDirectories();
        
        // 2. 管理备份文件
        const backupResult = manageBackupFiles();
        
        // 3. 统一管理资源文件
        const resourceResult = relocateResources();
        
        // 4. 生成摘要报告
        log('========================================');
        log('备份管理和资源统一完成');
        log(`- 已归档备份文件: ${backupResult.archivedCount}`);
        log(`- 错误数量: ${backupResult.errorCount}`);
        log(`- 备份目录大小: ${formatBytes(backupResult.finalSize)}`);
        log(`- 统一管理CSS文件: ${resourceResult.cssFiles}`);
        log(`- 统一管理JS文件: ${resourceResult.jsFiles}`);
        log('========================================');
        
        console.log('所有操作已成功完成！');
        
    } catch (error) {
        log(`执行过程中发生错误: ${error.message}`, 'ERROR');
        console.error(`[backup_manager.js] 执行失败:, error`);
        process.exit(1);
    }
}

// 执行主函数
if (require.main === module) {
    main();
}

// 导出函数供其他模块使用
module.exports = {
    manageBackupFiles,
    relocateResources,
    triggerUpdateMechanism,
    CONFIG
};
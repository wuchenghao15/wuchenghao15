// MTSCOS 清理管理器
console.log("[MTSCOS] 清理管理器已启动");

const fs = require('fs');
const path = require('path');
const os = require('os');

// 配置
const ROOT_DIR = path.dirname(path.dirname(__filename));
const LOG_DIR = path.join(ROOT_DIR, 'Logs');

// 确保日志目录存在
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

// 日志函数
function log(message) {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);
    fs.appendFileSync(path.join(LOG_DIR, 'cleanup_manager.log'), logMessage + '\n');
}

// 清理旧日志文件
function cleanupOldLogs() {
    log("开始清理旧日志文件...");
    const now = Date.now();
    const retentionDays = 7;
    const retentionMs = retentionDays * 24 * 60 * 60 * 1000;

    try {
        const files = fs.readdirSync(LOG_DIR);
        files.forEach(file => {
            if (file.endsWith('.log')) {
                const filePath = path.join(LOG_DIR, file);
                const stat = fs.statSync(filePath);
                const fileAge = now - stat.mtime.getTime();

                if (fileAge > retentionMs) {
                    fs.unlinkSync(filePath);
                    log();
                }
            }
        });
    } catch (error) {
        log();
    }
}

// 清理临时文件
function cleanupTempFiles() {
    log("清理临时文件...");
    // 这里添加临时文件清理逻辑
}

// 定期执行清理
function scheduleCleanup() {
    log("设置定期清理任务");

    // 立即执行一次清理
    cleanupOldLogs();
    cleanupTempFiles();

    // 设置每天凌晨执行清理
    setInterval(() => {
        const now = new Date();
        if (now.getHours() === 0 && now.getMinutes() === 0) {
            cleanupOldLogs();
            cleanupTempFiles();
        }
    }, 60000); // 每分钟检查一次
}

// 启动清理调度
scheduleCleanup();

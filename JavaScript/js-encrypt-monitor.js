// MTSCOS 通用服务模板
console.log("[MTSCOS] 服务 js-encrypt-monitor 已启动");

const fs = require('fs');
const path = require('path');

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
    fs.appendFileSync(path.join(LOG_DIR, 'js-encrypt-monitor.log'), logMessage + '\n');
}

// 服务主逻辑
function main() {
    log("服务初始化完成");

    // 这里添加服务的主要逻辑
    setInterval(() => {
        log("服务运行中...");
    }, 60000);
}

// 执行主程序
main();

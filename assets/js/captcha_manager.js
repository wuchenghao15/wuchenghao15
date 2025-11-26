#!/usr/bin/env node
// VERSION: 20251106.a9aab854c251fa0dfe6341eb
// -*- coding: utf-8 -*-
/**
 * 验证码管理器
 * 自动生成验证码并上传到服务器数据库，处理验证码匹配验证
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class CaptchaManager {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 目录路径
        this.logDir = path.join(this.projectRoot, 'Logs');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'captcha_manager.log');
        this.errorLogFile = path.join(this.logDir, 'error.log');
        
        // 本地验证码存储
        this.localCaptchas = new Map();
        
        // 验证码有效期（默认5分钟）
        this.captchaExpiryTime = 5 * 60 * 1000;
        
        // 清理定时器
        this.cleanupInterval = null;
        
        // 确保必要目录存在
        this.ensureDirExists(this.logDir);
    }
    
    /**
     * 确保目录存在
     */
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            this.log(`目录创建: ${dirPath}`);
        }
    }
    
    /**
     * 日志函数
     */
    log(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ${message}`;
        
        console.log(logMessage);
        
        try {
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`[captcha_manager.js] 写入日志失败: ${error.message}`);
        }
    }
    
    /**
     * 错误日志函数
     */
    errorLog(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(`[captcha_manager.js] ${logMessage}`);
        
        try {
            fs.appendFileSync(this.errorLogFile, logMessage + '/n');
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`[captcha_manager.js] 写入错误日志失败: ${error.message}`);
        }
    }
    
    /**
     * 生成随机验证码
     */
    generateCaptcha(length = 6) {
        const characters = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
        let captcha = '';
        
        for (let i = 0; i < length; i++) {
            captcha += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        
        return captcha;
    }
    
    /**
     * 生成验证码ID
     */
    generateCaptchaId() {
        return crypto.randomBytes(16).toString('hex');
    }
    
    /**
     * 创建新的验证码
     */
    createCaptcha() {
        const captchaId = this.generateCaptchaId();
        const captchaValue = this.generateCaptcha();
        const timestamp = Date.now();
        
        // 存储验证码
        this.localCaptchas.set(captchaId, {
            value: captchaValue,
            timestamp: timestamp
        });
        
        // 上传到服务器数据库
        this.uploadToDatabase(captchaId, captchaValue, timestamp);
        
        this.log(`生成新验证码: ID=${captchaId}, Value=${captchaValue}`);
        
        return {
            id: captchaId,
            value: captchaValue, // 在实际应用中，不应该返回真实值，这里仅用于演示
            timestamp: timestamp
        };
    }
    
    /**
     * 上传验证码到数据库
     * 注意：这是一个模拟实现，实际应用中需要连接到真实数据库
     */
    uploadToDatabase(captchaId, captchaValue, timestamp) {
        try {
            // 在实际应用中，这里应该有真实的数据库连接和插入操作
            // 例如使用MySQL或其他数据库的连接池
            
            // 模拟数据库操作
            const dbOperation = {
                table: 'captchas',
                action: 'insert',
                data: {
                    id: captchaId,
                    value: captchaValue, // 在实际应用中应该加密存储
                    created_at: new Date(timestamp).toISOString(),
                    expires_at: new Date(timestamp + this.captchaExpiryTime).toISOString()
                }
            };
            
            this.log(`验证码已上传到数据库: ${JSON.stringify(dbOperation)}`);
            
            // 这里可以添加真实的数据库连接代码
            // 例如使用mysql2、pg等数据库驱动
            
            return true;
        } catch (error) {
            this.errorLog(`上传验证码到数据库失败: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 验证用户提交的验证码
     */
    verifyCaptcha(captchaId, userInput) {
        try {
            // 检查本地存储
            const captcha = this.localCaptchas.get(captchaId);
            
            if (!captcha) {
                this.log(`验证码不存在: ${captchaId}`);
                return false;
            }
            
            // 检查是否过期
            const now = Date.now();
            if (now - captcha.timestamp > this.captchaExpiryTime) {
                this.log(`验证码已过期: ${captchaId}`);
                this.localCaptchas.delete(captchaId);
                return false;
            }
            
            // 比较验证码
            const isValid = captcha.value.toLowerCase() === userInput.toLowerCase();
            
            if (isValid) {
                this.log(`验证码验证成功: ${captchaId}`);
                // 验证成功后删除验证码，防止重复使用
                this.localCaptchas.delete(captchaId);
                // 可以在这里添加删除数据库记录的操作
            } else {
                this.log(`验证码验证失败: ${captchaId}`);
            }
            
            return isValid;
        } catch (error) {
            this.errorLog(`验证验证码失败: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 清理过期的验证码
     */
    cleanupExpiredCaptchas() {
        try {
            const now = Date.now();
            let deletedCount = 0;
            
            this.localCaptchas.forEach((captcha, captchaId) => {
                if (now - captcha.timestamp > this.captchaExpiryTime) {
                    this.localCaptchas.delete(captchaId);
                    deletedCount++;
                    // 可以在这里添加删除数据库过期记录的操作
                }
            });
            
            if (deletedCount > 0) {
                this.log(`已清理 ${deletedCount} 个过期验证码`);
            }
        } catch (error) {
            this.errorLog(`清理过期验证码失败: ${error.message}`);
        }
    }
    
    /**
     * 生成验证码HTML
     */
    generateCaptchaHTML() {
        const captcha = this.createCaptcha();
        
        const html = `
        <div class="captcha-container">
            <input type="hidden" id="captcha-id" value="${captcha.id}">
            <div class="captcha-image" id="captcha-image">
                <!-- 这里应该有真实的验证码图片生成 -->
                <!-- 为了演示，我们使用文本 -->
                <span class="captcha-text">${captcha.value}</span>
            </div>
            <input type="text" id="captcha-input" placeholder="请输入验证码">
            <button id="refresh-captcha">刷新验证码</button>
        </div>
        <script>
            // 验证码验证函数
            function verifyUserCaptcha() {
                const captchaId = document.getElementById('captcha-id').value;
                const userInput = document.getElementById('captcha-input').value;
                
                // 这里应该发送AJAX请求到服务器验证
                // 为了演示，我们假设验证通过
                console.log('验证验证码:', captchaId, userInput);
                return true;
            }
            
            // 刷新验证码
            document.getElementById('refresh-captcha').onclick = function() {
                // 这里应该重新请求服务器生成新的验证码
                console.log('刷新验证码');
                location.reload(); // 简单演示，实际应该用AJAX刷新
            };
        </script>
        `;
        
        return html;
    }
    
    /**
     * 启动验证码管理器
     */
    start() {
        this.log("=====================================");
        this.log("      验证码管理器启动      ");
        this.log("=====================================");
        
        // 启动定期清理任务
        this.cleanupInterval = setInterval(() => {
            this.cleanupExpiredCaptchas();
        }, 60000); // 每分钟清理一次
        
        this.log("验证码管理器已启动，开始监控和管理验证码");
    }
    
    /**
     * 停止验证码管理器
     */
    stop() {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
            this.cleanupInterval = null;
            this.log("验证码管理器已停止，清理定时器已清除");
        }
    }
}

// 主函数
function main() {
    const captchaManager = new CaptchaManager();
    captchaManager.start();
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = CaptchaManager;
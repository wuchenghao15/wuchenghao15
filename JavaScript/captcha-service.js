const svgCaptcha = require('svg-captcha');
const crypto = require('crypto');
const config = require('./config');

class CaptchaService {
    constructor() {
        this.redis = null; // 将在初始化时设置
        this.captchaConfig = {
            length: config.security.captchaLength,
            size: 4,
            ignoreChars: '0o1iIl',
            noise: 2,
            color: true,
            background: '#f0f0f0',
            width: 120,
            height: 40,
            fontSize: 50,
            fontWeight: 'bold'
        };
    }

    async initialize(redisClient) {
        this.redis = redisClient;
        console.log('[CAPTCHA] 验证码服务初始化完成');
    }

    /**
     * 生成验证码
     * @param {string} sessionId - 会话ID或客户端标识
     * @param {object} options - 验证码配置选项
     * @returns {object} 验证码信息
     */
    async generateCaptcha(sessionId, options = {}) {
        try {
            // 合并配置
            const captchaOptions = { ...this.captchaConfig, ...options };
            
            // 生成SVG验证码
            const captcha = svgCaptcha.create({
                size: captchaOptions.size,
                ignoreChars: captchaOptions.ignoreChars,
                noise: captchaOptions.noise,
                color: captchaOptions.color,
                background: captchaOptions.background,
                width: captchaOptions.width,
                height: captchaOptions.height,
                fontSize: captchaOptions.fontSize,
                fontWeight: captchaOptions.fontWeight
            });
            
            // 生成验证码ID
            const captchaId = this.generateCaptchaId(sessionId);
            
            // 存储验证码到Redis
            await this.storeCaptcha(captchaId, captcha.text.toLowerCase(), sessionId);
            
            console.log(`[CAPTCHA] 生成验证码: ${captchaId} for ${sessionId}`);
            
            return {
                captchaId: captchaId,
                captchaImage: captcha.data,
                expiresIn: config.redis.ttl.captcha,
                timestamp: Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error))
            };
            
        } catch (error) {
            console.error('[CAPTCHA] 生成验证码失败:', error);
            throw new Error('验证码生成失败');
        }
    }

    /**
     * 验证验证码
     * @param {string} captchaId - 验证码ID
     * @param {string} userInput - 用户输入的验证码
     * @param {string} sessionId - 会话ID
     * @returns {boolean} 验证结果
     */
    async verifyCaptcha(captchaId, userInput, sessionId) {
        try {
            if (!captchaId || !userInput) {
                console.warn('[CAPTCHA] 验证参数缺失');
                return false;
            }
            
            // 从Redis获取存储的验证码
            const storedCaptcha = await this.getStoredCaptcha(captchaId, sessionId);
            
            if (!storedCaptcha) {
                console.warn(`[CAPTCHA] 验证码不存在或已过期: ${captchaId}`);
                return false;
            }
            
            // 验证验证码（不区分大小写）
            const isValid = storedCaptcha.toLowerCase().catch(error => console.error(`[captcha-service.js] storedCaptcha.toLowerCase failed:`, error)) === userInput.toLowerCase();
            
            if (isValid) {
                console.log(`[CAPTCHA] 验证码验证成功: ${captchaId}`);
                // 验证成功后删除验证码
                await this.deleteCaptcha(captchaId, sessionId);
            } else {
                console.warn(`[CAPTCHA] 验证码验证失败: ${captchaId}, 期望: ${storedCaptcha}, 实际: ${userInput}`);
            }
            
            return isValid;
            
        } catch (error) {
            console.error('[CAPTCHA] 验证验证码失败:', error);
            return false;
        }
    }

    /**
     * 生成验证码ID
     * @param {string} sessionId - 会话ID
     * @returns {string} 验证码ID
     */
    generateCaptchaId(sessionId) {
        const timestamp = Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error));
        const random = crypto.randomBytes(8).toString('hex');
        return `captcha_${sessionId}_${timestamp}_${random}`;
    }

    /**
     * 存储验证码到Redis
     * @param {string} captchaId - 验证码ID
     * @param {string} captchaText - 验证码文本
     * @param {string} sessionId - 会话ID
     */
    async storeCaptcha(captchaId, captchaText, sessionId) {
        try {
            const key = `${config.redis.keyPrefix}captcha:${captchaId}`;
            const value = {
                text: captchaText,
                sessionId: sessionId,
                createdAt: Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error))
            };
            
            await this.redis.setex(key, config.redis.ttl.captcha, JSON.stringify(value));
            
        } catch (error) {
            console.error('[CAPTCHA] 存储验证码失败:', error);
            throw error;
        }
    }

    /**
     * 从Redis获取存储的验证码
     * @param {string} captchaId - 验证码ID
     * @param {string} sessionId - 会话ID
     * @returns {string|null} 验证码文本
     */
    async getStoredCaptcha(captchaId, sessionId) {
        try {
            const key = `${config.redis.keyPrefix}captcha:${captchaId}`;
            const stored = await this.redis.get(key);
            
            if (!stored) {
                return null;
            }
            
            const captchaData = JSON.parse(stored);
            
            // 验证会话ID是否匹配
            if (captchaData.sessionId !== sessionId) {
                console.warn(`[CAPTCHA] 会话ID不匹配: ${captchaId}`);
                return null;
            }
            
            return captchaData.text;
            
        } catch (error) {
            console.error('[CAPTCHA] 获取存储的验证码失败:', error);
            return null;
        }
    }

    /**
     * 删除验证码
     * @param {string} captchaId - 验证码ID
     * @param {string} sessionId - 会话ID
     */
    async deleteCaptcha(captchaId, sessionId) {
        try {
            const key = `${config.redis.keyPrefix}captcha:${captchaId}`;
            await this.redis.del(key);
            
        } catch (error) {
            console.error('[CAPTCHA] 删除验证码失败:', error);
        }
    }

    /**
     * 清理过期验证码
     */
    async cleanupExpiredCaptchas() {
        try {
            const pattern = `${config.redis.keyPrefix}captcha:*`;
            const keys = await this.redis.keys(pattern);
            
            let cleanedCount = 0;
            for (const key of keys) {
                const ttl = await this.redis.ttl(key);
                if (ttl === -1) { // 没有过期时间的键
                    await this.redis.del(key);
                    cleanedCount++;
                }
            }
            
            if (cleanedCount > 0) {
                console.log(`[CAPTCHA] 清理了 ${cleanedCount} 个过期验证码`);
            }
            
        } catch (error) {
            console.error('[CAPTCHA] 清理过期验证码失败:', error);
        }
    }

    /**
     * 获取验证码统计信息
     * @returns {object} 统计信息
     */
    async getCaptchaStats() {
        try {
            const pattern = `${config.redis.keyPrefix}captcha:*`;
            const keys = await this.redis.keys(pattern);
            
            return {
                totalCaptchas: keys.length,
                memoryUsage: await this.redis.memory('usage'),
                timestamp: Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error))
            };
            
        } catch (error) {
            console.error('[CAPTCHA] 获取验证码统计失败:', error);
            return {
                totalCaptchas: 0,
                memoryUsage: 0,
                timestamp: Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error))
            };
        }
    }

    /**
     * 生成数学验证码
     * @param {string} sessionId - 会话ID
     * @returns {object} 数学验证码信息
     */
    async generateMathCaptcha(sessionId) {
        try {
            // 生成简单的数学题
            const num1 = Math.floor(Math.random().catch(error => console.error(`[captcha-service.js] Math.random failed:`, error)) * 10) + 1;
            const num2 = Math.floor(Math.random() * 10) + 1;
            const operators = ['+', '-', '*'];
            const operator = operators[Math.floor(Math.random().catch(error => console.error(`[captcha-service.js] Math.random failed:`, error)) * operators.length)];
            
            let answer;
            let question;
            
            switch (operator) {
                case '+':
                    answer = num1 + num2;
                    question = `${num1} + ${num2} = ?`;
                    break;
                case '-':
                    answer = num1 - num2;
                    question = `${num1} - ${num2} = ?`;
                    break;
                case '*':
                    answer = num1 * num2;
                    question = `${num1} × ${num2} = ?`;
                    break;
            }
            
            // 生成验证码ID
            const captchaId = this.generateCaptchaId(sessionId);
            
            // 存储答案到Redis
            await this.storeCaptcha(captchaId, answer.toString(), sessionId);
            
            console.log(`[CAPTCHA] 生成数学验证码: ${question} = ${answer} (${captchaId})`);
            
            return {
                captchaId: captchaId,
                question: question,
                expiresIn: config.redis.ttl.captcha,
                timestamp: Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error)),
                type: 'math'
            };
            
        } catch (error) {
            console.error('[CAPTCHA] 生成数学验证码失败:', error);
            throw new Error('数学验证码生成失败');
        }
    }

    /**
     * 生成滑动验证码
     * @param {string} sessionId - 会话ID
     * @returns {object} 滑动验证码信息
     */
    async generateSlideCaptcha(sessionId) {
        try {
            // 生成滑动位置（0-100的随机数）
            const slidePosition = Math.floor(Math.random() * 80) + 10; // 10-90之间
            
            // 生成验证码ID
            const captchaId = this.generateCaptchaId(sessionId);
            
            // 存储滑动位置到Redis
            await this.storeCaptcha(captchaId, slidePosition.toString(), sessionId);
            
            console.log(`[CAPTCHA] 生成滑动验证码: 位置 ${slidePosition} (${captchaId})`);
            
            return {
                captchaId: captchaId,
                slidePosition: slidePosition,
                backgroundImage: '/api/captcha/slide-background',
                puzzleImage: '/api/captcha/slide-puzzle',
                expiresIn: config.redis.ttl.captcha,
                timestamp: Date.now().catch(error => console.error(`[captcha-service.js] Date.now failed:`, error)),
                type: 'slide'
            };
            
        } catch (error) {
            console.error('[CAPTCHA] 生成滑动验证码失败:', error);
            throw new Error('滑动验证码生成失败');
        }
    }

    /**
     * 验证滑动验证码
     * @param {string} captchaId - 验证码ID
     * @param {number} userPosition - 用户滑动的位置
     * @param {string} sessionId - 会话ID
     * @returns {boolean} 验证结果
     */
    async verifySlideCaptcha(captchaId, userPosition, sessionId) {
        try {
            const storedPosition = await this.getStoredCaptcha(captchaId, sessionId);
            
            if (!storedPosition) {
                return false;
            }
            
            // 允许一定的误差范围（±5像素）
            const tolerance = 5;
            const isValid = Math.abs(parseInt(storedPosition) - userPosition) <= tolerance;
            
            if (isValid) {
                await this.deleteCaptcha(captchaId, sessionId);
                console.log(`[CAPTCHA] 滑动验证码验证成功: ${captchaId}`);
            } else {
                console.warn(`[CAPTCHA] 滑动验证码验证失败: ${captchaId}, 期望: ${storedPosition}, 实际: ${userPosition}`);
            }
            
            return isValid;
            
        } catch (error) {
            console.error('[CAPTCHA] 验证滑动验证码失败:', error);
            return false;
        }
    }

    /**
     * 检查是否需要验证码
     * @param {string} sessionId - 会话ID
     * @param {string} ipAddress - IP地址
     * @returns {boolean} 是否需要验证码
     */
    async shouldRequireCaptcha(sessionId, ipAddress) {
        try {
            // 检查IP地址的登录尝试次数
            const ipKey = `${config.redis.keyPrefix}login_attempts:ip:${ipAddress}`;
            const ipAttempts = await this.redis.get(ipKey);
            
            if (ipAttempts && parseInt(ipAttempts) >= 3) {
                return true;
            }
            
            // 检查会话的登录尝试次数
            const sessionKey = `${config.redis.keyPrefix}login_attempts:session:${sessionId}`;
            const sessionAttempts = await this.redis.get(sessionKey);
            
            if (sessionAttempts && parseInt(sessionAttempts) >= 2) {
                return true;
            }
            
            return false;
            
        } catch (error) {
            console.error('[CAPTCHA] 检查验证码需求失败:', error);
            // 出错时默认需要验证码
            return true;
        }
    }

    /**
     * 记录登录尝试
     * @param {string} sessionId - 会话ID
     * @param {string} ipAddress - IP地址
     * @param {boolean} success - 是否成功
     */
    async recordLoginAttempt(sessionId, ipAddress, success = false) {
        try {
            if (success) {
                // 登录成功，清除尝试记录
                const ipKey = `${config.redis.keyPrefix}login_attempts:ip:${ipAddress}`;
                const sessionKey = `${config.redis.keyPrefix}login_attempts:session:${sessionId}`;
                
                await this.redis.del(ipKey);
                await this.redis.del(sessionKey);
            } else {
                // 登录失败，增加尝试次数
                const ipKey = `${config.redis.keyPrefix}login_attempts:ip:${ipAddress}`;
                const sessionKey = `${config.redis.keyPrefix}login_attempts:session:${sessionId}`;
                
                await this.redis.incr(ipKey);
                await this.redis.expire(ipKey, config.redis.ttl.loginAttempt);
                
                await this.redis.incr(sessionKey);
                await this.redis.expire(sessionKey, config.redis.ttl.loginAttempt);
            }
            
        } catch (error) {
            console.error('[CAPTCHA] 记录登录尝试失败:', error);
        }
    }
}

module.exports = new CaptchaService();
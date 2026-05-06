#!/usr/bin/env node

/**
 * MTSCOS 手动登录演示脚本
 * 演示如何获取验证码并完成登录流程
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

const API_BASE = 'http://localhost:3000';

async function demonstrateLogin() {
    try {
        console.log('🔐 MTSCOS 登录API演示\n');

        // 1. 获取验证码
        console.log('📸 正在生成验证码...');
        const captchaResponse = await axios.get(`${API_BASE}/api/captcha`);
        const { captchaId, captchaImage } = captchaResponse.data.data;
        
        console.log('✅ 验证码已生成');
        console.log('🆔 验证码ID:', captchaId);
        
        // 保存验证码图片到文件
        const svgFileName = `captcha-${Date.now()}.svg`;
        fs.writeFileSync(svgFileName, captchaImage);
        console.log('🖼️  验证码图片已保存为:', svgFileName);
        console.log('💡 请打开该文件查看验证码内容\n');

        // 模拟用户输入
        console.log('📝 测试账户信息:');
        console.log('   用户名: admin');
        console.log('   密码: admin123');
        console.log('   角色: 管理员\n');

        // 等待用户查看验证码
        console.log('⏳ 请查看验证码图片，然后按任意键继续...');
        await new Promise(resolve => {
            process.stdin.setRawMode(true);
            process.stdin.resume();
            process.stdin.on('data', () => {
                process.stdin.setRawMode(false);
                process.stdin.pause();
                resolve();
            });
        });

        console.log('\n🔄 由于这是自动化测试，我们将模拟正确的验证码...');
        
        // 为了演示，我们需要获取一个新的验证码并直接使用其文本值
        // 在实际应用中，用户会查看图片并输入验证码
        console.log('💡 在实际应用中，用户会查看验证码图片并输入对应的字符');
        console.log('🔧 为了演示完整流程，让我们创建一个已知验证码的测试...\n');

        // 创建一个特殊的测试端点来获取已知验证码
        console.log('📋 登录API使用说明:');
        console.log('1. GET /api/captcha - 获取验证码');
        console.log('2. POST /api/login - 提交登录信息');
        console.log('');
        console.log('📄 登录请求格式:');
        console.log(JSON.stringify({
            username: 'admin',
            password: 'admin123',
            captcha: '用户输入的验证码',
            captchaId: '从步骤1获取的ID',
            rememberMe: false
        }, null, 2));
        console.log('');

        // 展示服务器状态
        const healthResponse = await axios.get(`${API_BASE}/api/health`);
        console.log('📊 当前服务器状态:');
        console.log('   - 在线用户数:', healthResponse.data.stats.sessions);
        console.log('   - 注册用户数:', healthResponse.data.stats.users);
        console.log('   - 活跃验证码数:', healthResponse.data.stats.captchas);
        console.log('   - 登录日志数:', healthResponse.data.stats.loginLogs);
        console.log('');

        console.log('🎯 测试完成！');
        console.log('💡 要进行实际登录测试，请:');
        console.log('   1. 打开生成的SVG文件查看验证码');
        console.log('   2. 使用验证码中的字符调用登录API');
        console.log('   3. 或者使用前端界面进行交互式登录');

        // 清理临时文件
        try {
            fs.unlinkSync(svgFileName);
            console.log('🧹 临时验证码文件已清理');
        } catch (error) {
            // 忽略清理错误
        }

    } catch (error) {
        console.error('❌ 演示失败:', error.message);
        if (error.response) {
            console.error('📄 响应数据:', error.response.data);
            console.error('📊 状态码:', error.response.status);
        }
        process.exit(1);
    }
}

// 运行演示
demonstrateLogin();
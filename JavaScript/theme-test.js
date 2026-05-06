// 主题测试脚本 - 验证CSS变量和主题切换功能

console.log('=== 主题测试开始 ===');

// 检查CSS变量是否正确加载
function checkCSSVariables() {
    console.log('\n1. 检查CSS变量：');
    const rootStyle = getComputedStyle(document.documentElement);
    
    const criticalVariables = [
        '--primary-color',
        '--bg-primary', 
        '--text-primary',
        '--border-color',
        '--danger-color'
    ];
    
    criticalVariables.forEach(variable => {
        const value = rootStyle.getPropertyValue(variable);
        console.log(`  ${variable}: ${value || '未定义'}`);
    });
}

// 检查深色模式切换
function testDarkModeToggle() {
    console.log('\n2. 测试深色模式切换：');
    
    // 尝试切换到深色模式
    document.documentElement.classList.add('dark-theme');
    console.log('   切换到深色模式');
    
    // 检查深色模式下的变量值
    const darkRootStyle = getComputedStyle(document.documentElement);
    const primaryColorDark = darkRootStyle.getPropertyValue('--primary-color');
    const bgColorDark = darkRootStyle.getPropertyValue('--bg-primary');
    
    console.log(`   深色模式主色: ${primaryColorDark}`);
    console.log(`   深色模式背景: ${bgColorDark}`);
    
    // 切换回亮色模式
    document.documentElement.classList.remove('dark-theme');
    console.log('   切换回亮色模式');
}

// 检查登录按钮样式是否应用了CSS变量
function checkButtonStyles() {
    console.log('\n3. 检查登录按钮样式：');
    const loginButton = document.querySelector('.login-button');
    if (loginButton) {
        const buttonStyle = getComputedStyle(loginButton);
        console.log(`   背景: ${buttonStyle.background}`);
        console.log(`   颜色: ${buttonStyle.color}`);
        console.log(`   边框圆角: ${buttonStyle.borderRadius}`);
    } else {
        console.log('   未找到登录按钮');
    }
}

// 检查验证码区域样式
function checkCaptchaStyles() {
    console.log('\n4. 检查验证码样式：');
    const captchaImage = document.querySelector('.captcha-image');
    if (captchaImage) {
        const captchaStyle = getComputedStyle(captchaImage);
        console.log(`   背景: ${captchaStyle.backgroundColor}`);
        console.log(`   边框: ${captchaStyle.border}`);
        console.log(`   边框圆角: ${captchaStyle.borderRadius}`);
    } else {
        console.log('   未找到验证码图像元素');
    }
}

// 运行所有测试
function runAllTests() {
    setTimeout(() => {
        checkCSSVariables();
        testDarkModeToggle();
        checkButtonStyles();
        checkCaptchaStyles();
        console.log('\n=== 主题测试完成 ===');
    }, 1000);
}

// 当页面加载完成后运行测试
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAllTests);
} else {
    runAllTests();
}
const fs = require('fs');
const path = require('path');

// 导入修复引擎
const RepairEngine = require('./repair-engine');

// 创建修复引擎实例
const repairEngine = new RepairEngine();

// 直接调用注册方法，绕过初始化
repairEngine.registerDefaultDetectors();
repairEngine.registerDefaultStrategies();

// 打印注册的检测器和策略
console.log('=== 测试检测器和策略注册 ===');
console.log('注册的检测器:', repairEngine.components.detectors.map(d => d.name));
console.log('注册的策略:', repairEngine.components.strategies.map(s => s.name));

// 创建测试文件
const testFileContent = `// 测试文件：包含各种问题的代码

const unusedVariable = "这是一个未使用的变量";

function emptyFunction() {
    // 空代码块
}

function debugCode() {
    console.log("调试信息");
    return 42;
}

function securityIssue() {
    const userInput = "恶意代码";
    eval(userInput); // 安全漏洞
}

for (let i = 0; i < document.querySelectorAll('.item').length; i++) {
    // 循环中计算长度，性能问题
    console.log(i);
}

function sliceCallIssue() {
    const args = Array.prototype.slice.call(arguments);
    return args;
}
`;

const testFilePath = path.join(__dirname, 'test-code.js');
fs.writeFileSync(testFilePath, testFileContent);

console.log('\n=== 测试问题检测 ===');
// 测试语法错误检测
const syntaxErrorContent = `function syntaxError() {
    let x = 10
    let y = 20
    return x + y
}

// 明显的语法错误：缺少分号和括号
function anotherError() {
    let z = 30
    if (z > 20
    return z
}`;

fs.writeFileSync(testFilePath, syntaxErrorContent);
console.log('测试语法错误检测...');
repairEngine.components.detectors.forEach(detector => {
    try {
        // 使用Promise.resolve确保无论detect是否异步都能处理
        const issues = Promise.resolve(detector.detect(testFilePath, syntaxErrorContent));
        issues.then(result => {
            if (result && result.length > 0) {
                console.log(`  ${detector.name} 检测到 ${result.length} 个问题`);
                result.forEach((issue, index) => {
                    console.log(`    问题 ${index + 1}: ${issue.type} - ${issue.message}`);
                });
            }
        });
    } catch (error) {
        console.log(`  ${detector.name} 检测失败: ${error.message}`);
    }
});

// 等待异步操作完成
setTimeout(() => {
    // 测试逻辑错误检测
    const logicErrorContent = `function logicError() {
        if (true) {
        }
        for (let i = 0; i < 10; i++) {
        }
        console.log("调试信息");
        return false;
    }

    function emptyFunction() {
    }
    `;

    fs.writeFileSync(testFilePath, logicErrorContent);
    console.log('\n测试逻辑错误检测...');
    repairEngine.components.detectors.forEach(detector => {
        try {
            const issues = Promise.resolve(detector.detect(testFilePath, logicErrorContent));
            issues.then(result => {
                if (result && result.length > 0) {
                    console.log(`  ${detector.name} 检测到 ${result.length} 个问题`);
                    result.forEach((issue, index) => {
                        console.log(`    问题 ${index + 1}: ${issue.type} - ${issue.message}`);
                    });
                }
            });
        } catch (error) {
            console.log(`  ${detector.name} 检测失败: ${error.message}`);
        }
    });

    // 等待异步操作完成
    setTimeout(() => {
        // 测试安全漏洞检测
        const securityContent = `function securityIssue() {
            const userInput = "恶意代码";
            eval(userInput); // 安全漏洞
            const password = "123456"; // 硬编码密码
        }
        `;

        fs.writeFileSync(testFilePath, securityContent);
        console.log('\n测试安全漏洞检测...');
        repairEngine.components.detectors.forEach(detector => {
            try {
                const issues = Promise.resolve(detector.detect(testFilePath, securityContent));
                issues.then(result => {
                    if (result && result.length > 0) {
                        console.log(`  ${detector.name} 检测到 ${result.length} 个问题`);
                        result.forEach((issue, index) => {
                            console.log(`    问题 ${index + 1}: ${issue.type} - ${issue.message}`);
                        });
                    }
                });
            } catch (error) {
                console.log(`  ${detector.name} 检测失败: ${error.message}`);
            }
        });

        
    }, 1000);
}, 1000);

// 清理测试文件
fs.unlinkSync(testFilePath);
console.log('\n=== 测试完成 ===');
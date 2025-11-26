function securityIssue() {
            const userInput = "恶意代码";
            eval(userInput); // 安全漏洞
            const password = "123456"; // 硬编码密码
        }
        
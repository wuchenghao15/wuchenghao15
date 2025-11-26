// 反调试保护模块
// 自动生成以解决404错误
console.log('Anti-debug protection module loaded');

// 反调试保护对象
const AntiDebug = {
    // 初始化反调试保护
    init() {
        console.log('Anti-debug protection initialized');
        this.enableAllProtections();
        return this;
    },
    
    // 启用所有保护措施
    enableAllProtections() {
        console.log('Enabling all anti-debug protections');
        
        // 检测开发者工具
        this.detectDevTools();
        
        // 检测断点
        this.detectBreakpoints();
        
        // 检测调试器
        this.detectDebugger();
        
        // 检测修改
        this.detectModifications();
    },
    
    // 检测开发者工具
    detectDevTools() {
        console.log('Setting up dev tools detection');
        
        // 使用performance API检测
        const devToolsCheck = () => {
            const startTime = performance.now();
            // 循环一段时间
            for (let i = 0; i < 1000000; i++) {
                // 空循环
            }
            const endTime = performance.now();
            
            // 如果执行时间过长，可能是调试器在单步执行
            if (endTime - startTime > 100) {
                this.handleDebugDetected('devtools_detected');
            }
        };
        
        // 定期检查
        setInterval(devToolsCheck, 1000);
    },
    
    // 检测断点
    detectBreakpoints() {
        console.log('Setting up breakpoint detection');
        
        // 使用Error构造函数检测
        const detectBreakpoint = () => {
            const error = new Error();
            const stack = error.stack;
            
            // 检查调用栈是否被修改
            if (!stack || stack.length > 1000) {
                this.handleDebugDetected('breakpoint_detected');
            }
        };
        
        // 定期检查
        setInterval(detectBreakpoint, 2000);
    },
    
    // 检测调试器
    detectDebugger() {
        console.log('Setting up debugger detection');
        
        // 使用Date对象检测
        const detectDebugger = () => {
            const startDate = new Date();
            debugger; // 调试器会暂停在这里
            const endDate = new Date();
            const diff = endDate - startDate;
            
            // 如果时间差过大，说明调试器被触发
            if (diff > 100) {
                this.handleDebugDetected('debugger_triggered');
            }
        };
        
        // 定期检查
        setTimeout(detectDebugger, 5000);
    },
    
    // 检测修改
    detectModifications() {
        console.log('Setting up modification detection');
        
        // 保存原始对象
        this.originalConsole = {...console};
        this.originalDocument = document.cloneNode(true);
        
        // 定期检查修改
        setInterval(() => {
            this.checkConsoleModifications();
            this.checkDocumentModifications();
        }, 3000);
    },
    
    // 检查控制台修改
    checkConsoleModifications() {
        for (const key in this.originalConsole) {
            if (console[key] !== this.originalConsole[key]) {
                this.handleDebugDetected('console_modified');
                break;
            }
        }
    },
    
    // 检查文档修改
    checkDocumentModifications() {
        // 简单检查文档大小变化
        const currentSize = document.documentElement.outerHTML.length;
        const originalSize = this.originalDocument.documentElement.outerHTML.length;
        
        // 如果大小变化超过10%，可能被修改
        if (Math.abs(currentSize - originalSize) > originalSize * 0.1) {
            this.handleDebugDetected('document_modified');
        }
    },
    
    // 处理调试检测
    handleDebugDetected(type) {
        console.warn(`Debug detected: ${type}`);
        
        // 触发安全事件
        this.triggerSecurityEvent(type);
        
        // 执行保护措施
        this.executeProtectionActions();
    },
    
    // 触发安全事件
    triggerSecurityEvent(type) {
        const event = new CustomEvent('security:violation', {
            detail: {
                type: 'debug',
                subtype: type,
                timestamp: new Date().toISOString()
            }
        });
        document.dispatchEvent(event);
    },
    
    // 执行保护措施
    executeProtectionActions() {
        console.log('Executing protection actions');
        
        // 这里可以添加更严格的保护措施，如：
        // - 显示警告
        // - 记录事件
        // - 限制功能
        // - 自动登出
        
        // 当前仅记录日志
    },
    
    // 禁用所有保护措施
    disableAllProtections() {
        console.log('Disabling all anti-debug protections');
        // 清理资源
        if (this.intervalIds) {
            this.intervalIds.forEach(id => clearInterval(id));
            this.intervalIds = [];
        }
    }
};

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AntiDebug;
} else if (typeof window !== 'undefined') {
    window.AntiDebug = AntiDebug;
}

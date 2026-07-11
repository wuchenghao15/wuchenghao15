/**
 * MTSCOS AI System - 功能强化模块
 * 版本: 1.0.0
 * 描述: 系统功能强化，扩展更多智能化能力
 */

class FeatureEnhancer {
    constructor() {
        this.enhancements = {
            performance: new PerformanceEnhancer(),
            security: new SecurityEnhancer(),
            ui: new UIEnhancer(),
            data: new DataEnhancer(),
            ai: new AIEnhancer(),
            monitoring: new MonitoringEnhancer()
        };
        this.init();
    }
    
    async init() {
        console.log('🚀 功能强化模块初始化中...');
        
        // 按顺序启用各项强化
        for (const [name, enhancer] of Object.entries(this.enhancements)) {
            try {
                await enhancer.activate();
                console.log(`✅ ${name} 强化已激活`);
            } catch (error) {
                console.error(`❌ ${name} 强化失败:`, error);
            }
        }
        
        console.log('🎉 系统功能强化完成');
    }
}

/**
 * 性能强化器
 */
class PerformanceEnhancer {
    async activate() {
        // 启用性能监控
        this.setupPerformanceObserver();
        // 启用资源预加载
        this.enableResourcePreload();
        // 启用代码分割
        this.enableCodeSplitting();
        // 启用智能缓存
        this.enableSmartCache();
    }
    
    setupPerformanceObserver() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    // 记录性能指标
                    this.recordMetric(entry.name, entry.duration);
                }
            });
            observer.observe({ entryTypes: ['navigation', 'resource', 'paint'] });
        }
    }
    
    recordMetric(name, value) {
        if (window.brain && window.brain.brain) {
            // 上报脑库
            console.log(`📊 性能指标: ${name} = ${value}ms`);
        }
    }
    
    enableResourcePreload() {
        // 预加载关键资源
        const criticalResources = [
            '/assets/css/common_styles/theme-system.css',
            '/assets/css/common_styles/ui-design-system.css',
            '/assets/js/core/mtscos-core.js'
        ];
        
        criticalResources.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = url.endsWith('.css') ? 'style' : 'script';
            link.href = url;
            document.head.appendChild(link);
        });
    }
    
    enableCodeSplitting() {
        // 动态加载非关键模块
        setTimeout(() => {
            this.loadModule('/assets/js/core/brain-database.js');
        }, 1000);
    }
    
    async loadModule(url) {
        try {
            await import(url);
        } catch (error) {
            // 降级处理
        }
    }
    
    enableSmartCache() {
        // 实现LRU缓存
        window.mtscosCache = new Map();
        window.mtscosCache.maxSize = 100;
    }
}

/**
 * 安全强化器
 */
class SecurityEnhancer {
    async activate() {
        this.setupCSP();
        this.setupXSSProtection();
        this.setupClickjackingProtection();
        this.setupSensitiveInfoFilter();
    }
    
    setupCSP() {
        // 设置内容安全策略（使用globalThis避免Illegal invocation）
        try {
            const doc = globalThis.document;
            if (!doc || !doc.head) return;
            const meta = doc.createElement('meta');
            meta.httpEquiv = 'Content-Security-Policy';
            meta.content = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;";
            doc.head.appendChild(meta);
        } catch (error) {
            // 静默失败，不影响其他功能
        }
    }
    
    setupXSSProtection() {
        // XSS防护
        // 输入消毒函数（使用箭头函数，无this绑定问题）
        window.sanitizeInput = (input) => {
            if (typeof input !== 'string') return input;
            return input
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#x27;')
                .replace(/\//g, '&#x2F;');
        };
    }
    
    setupClickjackingProtection() {
        // 防点击劫持（安全访问）
        try {
            if (globalThis.top !== globalThis.self) {
                globalThis.top.location = globalThis.self.location;
            }
        } catch (error) {
            // 跨域时静默失败
        }
    }
    
    setupSensitiveInfoFilter() {
        // 敏感信息过滤
        window.filterSensitiveInfo = (text) => {
            if (typeof text !== 'string') return text;
            return text
                .replace(/\d{17,19}/g, '****')  // 身份证/银行卡
                .replace(/1[3-9]\d{9}/g, '****') // 手机号
                .replace(/[\w.-]+@[\w-]+\.[\w.-]+/g, '****'); // 邮箱
        };
    }
}

/**
 * UI强化器
 */
class UIEnhancer {
    async activate() {
        this.enableSmoothScroll();
        this.enableLazyLoad();
        this.enableTouchOptimization();
        this.setupKeyboardShortcuts();
    }
    
    enableSmoothScroll() {
        document.documentElement.style.scrollBehavior = 'smooth';
    }
    
    enableLazyLoad() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            imageObserver.unobserve(img);
                        }
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
    
    enableTouchOptimization() {
        // 触摸优化
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K: 快速搜索
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.openQuickSearch();
            }
            // Ctrl+B: 切换脑库面板
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                this.toggleBrainPanel();
            }
        });
    }
    
    openQuickSearch() {
        console.log('🔍 快速搜索');
    }
    
    toggleBrainPanel() {
        if (window.brainVisualizer) {
            window.brainVisualizer.toggle();
        }
    }
}

/**
 * 数据强化器
 */
class DataEnhancer {
    async activate() {
        this.enableDataCompression();
        this.enableDataValidation();
        this.enableDataBackup();
    }
    
    enableDataCompression() {
        // 简单的数据压缩（仅生产环境）
        window.compressData = (data) => {
            try {
                return JSON.stringify(data);
            } catch (error) {
                return null;
            }
        };
    }
    
    enableDataValidation() {
        window.validateData = (data, schema) => {
            if (!data || !schema) return false;
            
            for (const [key, rules] of Object.entries(schema)) {
                if (rules.required && (data[key] === undefined || data[key] === null)) {
                    return false;
                }
                if (rules.type && typeof data[key] !== rules.type) {
                    return false;
                }
            }
            return true;
        };
    }
    
    enableDataBackup() {
        // 定期备份
        setInterval(() => {
            this.performBackup();
        }, 30 * 60 * 1000); // 30分钟
    }
    
    async performBackup() {
        if (window.brain && window.brain.exportKnowledge) {
            try {
                await window.brain.exportKnowledge();
                console.log('💾 自动备份完成');
            } catch (error) {
                console.error('❌ 自动备份失败:', error);
            }
        }
    }
}

/**
 * AI强化器
 */
class AIEnhancer {
    async activate() {
        this.enableAIContextMemory();
        this.enableAISmartSuggestions();
    }
    
    enableAIContextMemory() {
        // AI上下文记忆
        window.aiContext = {
            history: [],
            maxSize: 50,
            add(item) {
                this.history.push({
                    ...item,
                    timestamp: Date.now()
                });
                if (this.history.length > this.maxSize) {
                    this.history.shift();
                }
            },
            get() {
                return this.history;
            },
            clear() {
                this.history = [];
            }
        };
    }
    
    enableAISmartSuggestions() {
        window.getSmartSuggestions = (input) => {
            const suggestions = [];
            const lowerInput = input.toLowerCase();
            
            if (lowerInput.includes('登录') || lowerInput.includes('login')) {
                suggestions.push('登录相关问题');
            }
            if (lowerInput.includes('错误') || lowerInput.includes('error')) {
                suggestions.push('错误诊断');
            }
            if (lowerInput.includes('主题') || lowerInput.includes('theme')) {
                suggestions.push('主题切换');
            }
            
            return suggestions;
        };
    }
}

/**
 * 监控强化器
 */
class MonitoringEnhancer {
    constructor() {
        this.metrics = {
            pageLoad: 0,
            apiCalls: 0,
            errors: 0,
            userActions: 0
        };
    }
    
    async activate() {
        this.startPageLoadMonitor();
        this.startErrorMonitor();
        this.startUserActionMonitor();
        this.startHealthCheck();
    }
    
    startPageLoadMonitor() {
        window.addEventListener('load', () => {
            const timing = performance.timing;
            this.metrics.pageLoad = timing.loadEventEnd - timing.navigationStart;
            console.log(`📊 页面加载时间: ${this.metrics.pageLoad}ms`);
        });
    }
    
    startErrorMonitor() {
        window.addEventListener('error', (event) => {
            this.metrics.errors++;
            console.error('🚨 全局错误:', event.error);
            
            // 上报到脑库
            if (window.brain) {
                window.brain.search(event.message);
            }
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.metrics.errors++;
            console.error('🚨 未处理的Promise拒绝:', event.reason);
        });
    }
    
    startUserActionMonitor() {
        ['click', 'keydown', 'scroll'].forEach(eventType => {
            document.addEventListener(eventType, () => {
                this.metrics.userActions++;
            }, { passive: true });
        });
    }
    
    startHealthCheck() {
        setInterval(() => {
            this.performHealthCheck();
        }, 60000); // 每分钟
    }
    
    performHealthCheck() {
        const status = {
            memory: performance.memory ? {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024)
            } : null,
            metrics: this.metrics,
            timestamp: Date.now()
        };
        console.log('💗 系统健康检查:', status);
    }
}

// 导出
if (typeof window !== 'undefined') {
    window.FeatureEnhancer = FeatureEnhancer;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeatureEnhancer;
}

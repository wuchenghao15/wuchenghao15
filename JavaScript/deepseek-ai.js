const axios = require('axios');
const path = require('path');
const winston = require('winston');
const LocalDeepSeekModel = require('./local-deepseek-model');
const configManager = require('./config-manager');

class DeepSeekAI {
    constructor(configPathOrConfig = './Configs/deepseek_config.json') {
        this.configPathOrConfig = configPathOrConfig;
        this.config = null;
        this.cache = new Map();
        this.localModel = null;
        this.logger = winston.createLogger({
            level: 'info',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.json()
            ),
            transports: [
                new winston.transports.File({ filename: '../Logs/deepseek.log' }),
                new winston.transports.Console()
            ]
        });
        this.init().catch(error => console.error(`[deepseek-ai.js] this.init failed:`, error));
    }

    async init() {
        try {
            // 默认配置
            const defaultConfig = {
                deepseek: {
                    apiKey: '',
                    baseUrl: 'https://api.deepseek.com',
                    model: 'deepseek-coder',
                    maxTokens: 1024,
                    temperature: 0.3,
                    timeout: 30000
                },
                cache: {
                    enabled: true,
                    maxSize: 100,
                    ttl: 3600
                },
                localModel: {
                    enabled: false,
                    modelPath: './Models/deepseek-local',
                    maxTokens: 512
                }
            };

            // 使用配置管理器加载配置
            this.config = await configManager.loadConfig(this.configPathOrConfig, defaultConfig);
            
            // 初始化本地模型（如果启用）
            if (this.config.localModel?.enabled) {
                this.localModel = new LocalDeepSeekModel(this.config);
                await this.localModel.initialize();
            }
            
            this.logger.info('DeepSeek AI initialized successfully');
        } catch (error) {
            this.logger.error('Failed to initialize DeepSeek AI:', error);
            throw error;
        }
    }

    getCacheKey(prompt, options = {}) {
        return `${prompt}_${JSON.stringify(options)}`;
    }

    getFromCache(cacheKey) {
        if (!this.config.cache.enabled) return null;
        
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.config.cache.ttl * 1000) {
            return cached.data;
        }
        
        if (cached) {
            this.cache.delete(cacheKey);
        }
        return null;
    }

    setCache(cacheKey, data) {
        if (!this.config.cache.enabled) return;
        
        if (this.cache.size >= this.config.cache.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(cacheKey, {
            data,
            timestamp: Date.now()
        });
    }

    async callAPI(prompt, options = {}) {
        const cacheKey = this.getCacheKey(prompt, options);
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            this.logger.info('Returning cached response');
            return cached;
        }

        // 优先使用本地模型
        if (this.localModel && await this.localModel.isReady()) {
            try {
                const response = await this.localModel.generateResponse(prompt, options);
                this.setCache(cacheKey, response.response);
                this.logger.info('Local model response successful');
                return response.response;
            } catch (error) {
                this.logger.warn('Local model failed, falling back to API:', error);
            }
        }

        // 如果API密钥是演示密钥，使用模拟响应
        if (this.config.deepseek.apiKey === 'sk-demo-key-for-local-testing') {
            const simulatedResponse = this.getSimulatedResponse(prompt, options);
            this.setCache(cacheKey, simulatedResponse);
            return simulatedResponse;
        }

        try {
            const response = await axios.post(
                `${this.config.deepseek.baseUrl}/chat/completions`,
                {
                    model: this.config.deepseek.model,
                    messages: [
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    max_tokens: options.maxTokens || this.config.deepseek.maxTokens,
                    temperature: options.temperature || this.config.deepseek.temperature
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.config.deepseek.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: this.config.deepseek.timeout
                }
            );

            const result = response.data.choices[0].message.content;
            this.setCache(cacheKey, result);
            this.logger.info('API call successful');
            return result;

        } catch (error) {
            this.logger.error('API call failed:', error);
            throw new Error(`DeepSeek API Error: ${error.response?.data?.error?.message || error.message}`);
        }
    }

    /**
     * 获取模拟响应（用于演示和测试）
     */
    getSimulatedResponse(prompt, options = {}) {
        const lowerPrompt = prompt.toLowerCase();
        
        // 根据不同的请求类型返回模拟响应
        if (lowerPrompt.includes('你好') || lowerPrompt.includes('介绍')) {
            return `你好！我是DeepSeek AI助手。我是一个强大的语言模型，能够帮助您处理各种任务，包括：

💬 对话交流
⚡ 代码生成  
📊 文本分析
🌍 语言翻译
📝 文本摘要

我可以根据您的需求提供智能化的帮助。请告诉我您需要什么协助！`;
        }
        
        if (lowerPrompt.includes('计算器') || lowerPrompt.includes('calculator')) {
            return `// 简单的计算器函数
function calculator(a, b, operation) {
    switch(operation) {
        case '+':
            return a + b;
        case '-':
            return a - b;
        case '*':
            return a * b;
        case '/':
            return b !== 0 ? a / b : '除数不能为零';
        default:
            return '不支持的操作';
    }
}

// 使用示例
console.log(calculator(10, 5, '+'));  // 15
console.log(calculator(10, 5, '-'));  // 5
console.log(calculator(10, 5, '*'));  // 50
console.log(calculator(10, 5, '/'));  // 2`;
        }
        
        if (lowerPrompt.includes('分析') || lowerPrompt.includes('analyze')) {
            return `文本分析结果：

📊 **基本统计**
- 字符数：${prompt.length}
- 词数：${prompt.split(/\s+/).length}
- 句子数：${prompt.split(/[。！？.!?]+/).filter(s => s.trim()).length}

🎯 **情感分析**
- 情感倾向：中性
- 积极程度：中等
- 语言类型：中文

📝 **内容特征**
- 包含疑问句：${lowerPrompt.includes('?') || lowerPrompt.includes('？') ? '是' : '否'}
- 包含感叹句：${lowerPrompt.includes('!') || lowerPrompt.includes('！') ? '是' : '否'}
- 正式程度：非正式`;
        }
        
        // 默认响应
        return `感谢您的消息！这是一个模拟响应，用于演示DeepSeek AI的功能。

您的消息："${prompt}"

在实际部署中，您需要：
1. 获取有效的DeepSeek API密钥
2. 更新配置文件中的API密钥
3. 确保网络连接正常

当前运行在演示模式下，所有功能都可以正常测试，但响应为模拟数据。`;
    }



    async translateText(text, targetLanguage) {
        const prompt = `Translate the following text to ${targetLanguage}:\n\n${text}`;
        return this.callAPI(prompt, { temperature: 0.2 });
    }

    async summarizeText(text, maxLength = 200) {
        const prompt = `Summarize the following text in no more than ${maxLength} words:\n\n${text}`;
        return this.callAPI(prompt, { temperature: 0.3 });
    }

    async chatWithAI(message, conversationHistory = []) {
        const messages = [
            ...conversationHistory,
            { role: 'user', content: message }
        ];

        // 如果API密钥是演示密钥，使用模拟响应
        if (this.config.deepseek.apiKey === 'sk-demo-key-for-local-testing') {
            return this.getSimulatedResponse(message, {});
        }

        try {
            const response = await axios.post(
                `${this.config.deepseek.baseUrl}/chat/completions`,
                {
                    model: this.config.deepseek.model,
                    messages: messages,
                    max_tokens: this.config.deepseek.maxTokens,
                    temperature: this.config.deepseek.temperature
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.config.deepseek.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: this.config.deepseek.timeout
                }
            );

            return response.data.choices[0].message.content;
        } catch (error) {
            this.logger.error('Chat API call failed:', error);
            throw new Error(`DeepSeek Chat Error: ${error.response?.data?.error?.message || error.message}`);
        }
    }

    async isConfigured() {
        return this.config && this.config.deepseek.apiKey && this.config.deepseek.apiKey.length > 0;
    }

    getConfig() {
        return { ...this.config };
    }





    /**
     * 批量处理任务
     */
    async batchProcess(tasks) {
        const results = [];
        
        for (const task of tasks) {
            try {
                let result;
                switch (task.type) {
                    case 'chat':
                        result = await this.chatWithAI(task.message, task.history || []);
                        break;
                    case 'analyze':
                        result = await this.analyzeText(task.text);
                        break;
                    case 'translate':
                        result = await this.translateText(task.text, task.targetLanguage);
                        break;
                    case 'summarize':
                        result = await this.summarizeText(task.text, task.maxLength || 200);
                        break;
                    case 'complete':
                        result = await this.completeText(task.text, task.context || '');
                        break;
                    default:
                        throw new Error(`Unknown task type: ${task.type}`);
                }
                
                results.push({
                    id: task.id,
                    success: true,
                    result: result
                });
            } catch (error) {
                results.push({
                    id: task.id,
                    success: false,
                    error: error.message
                });
            }
        }
        
        return results;
    }



    /**
     * 增强的模拟响应
     */
    getSimulatedResponse(prompt, options = {}) {
        const lowerPrompt = prompt.toLowerCase().catch(error => console.error(`[deepseek-ai.js] prompt.toLowerCase failed:`, error));
        
        // 代码生成模拟
        if (lowerPrompt.includes('生成代码') || lowerPrompt.includes('generate code')) {
            return `// 根据您的需求生成的代码
function generateSolution() {
    const config = {
        version: '1.0.0',
        features: ['AI驱动', '实时响应', '智能优化']
    };
    
    return {
        init: () => console.log('系统初始化完成'),
        process: (data) => data.map(item => ({ ...item, processed: true })),
        export: () => config.features.join(', ')
    };
}

// 使用示例
const solution = generateSolution();
solution.init().catch(error => console.error('[deepseek-ai.js] solution.init failed:', error));
const results = solution.process([{ id: 1, name: '测试' }]);
console.log(solution.export());`;
        }
        
        // 文本分析增强
        if (lowerPrompt.includes('分析') || lowerPrompt.includes('analyze')) {
            return `📊 **深度文本分析报告**

🔍 **基础信息**
- 字符数：${prompt.length}
- 词数：${prompt.split(/\s+/).length}
- 段落数：${prompt.split(/\n\n+/).length}

🎯 **AI智能分析**
- 主题类别：${lowerPrompt.includes('代码') ? '技术文档' : '一般文本'}
- 情感倾向：${lowerPrompt.includes('错误') || lowerPrompt.includes('问题') ? '负面' : '中性'}
- 复杂度：${prompt.length > 200 ? '高' : '中等'}

💡 **优化建议**
- ${prompt.length > 500 ? '建议分段以提高可读性' : '长度适中'}
- ${lowerPrompt.includes('?') ? '包含疑问句，可能需要解答' : '陈述性文本'}
- 推荐操作：${lowerPrompt.includes('代码') ? '可进行代码审查' : '可进一步摘要处理'}

⚡ **处理时间**：${new Date().toLocaleString()}`;
        }
        
        // 翻译模拟
        if (lowerPrompt.includes('翻译') || lowerPrompt.includes('translate')) {
            return `🌍 **翻译结果**

原文：${prompt}

🇬🇧 **英文翻译**：
This is a simulated translation response. In a real deployment, this would be translated by the DeepSeek AI model with high accuracy and natural language processing.

🇯🇵 **日文翻译**：
これはシミュレーション翻訳レスポンスです。実際の展開では、DeepSeek AIモデルによって高精度で自然な言語処理が行われます。

📝 **翻译说明**
- 当前为演示模式
- 支持多语言互译
- 保持原文语义和语境
- 自动检测语言类型`;
        }
        
        // 原有的模拟响应逻辑...
        if (lowerPrompt.includes('你好') || lowerPrompt.includes('介绍')) {
            return `你好！我是DeepSeek AI助手。我是一个强大的语言模型，能够帮助您处理各种任务，包括：

💬 对话交流
⚡ 代码生成  
📊 文本分析
🌍 语言翻译
📝 文本摘要
🔄 批量处理
🎯 智能建议
📡 流式响应

我可以根据您的需求提供智能化的帮助。请告诉我您需要什么协助！`;
        }
        
        if (lowerPrompt.includes('计算器') || lowerPrompt.includes('calculator')) {
            return `// 增强版计算器函数
function advancedCalculator() {
    const history = [];
    
    return {
        calculate: function(a, b, operation) {
            const result = this.performOperation(a, b, operation);
            history.push({ a, b, operation, result, timestamp: new Date() });
            return result;
        },
        
        performOperation: function(a, b, operation) {
            switch(operation) {
                case '+': return a + b;
                case '-': return a - b;
                case '*': return a * b;
                case '/': return b !== 0 ? a / b : '除数不能为零';
                case '^': return Math.pow(a, b);
                case '%': return a % b;
                default: return '不支持的操作';
            }
        },
        
        getHistory: () => history.slice(),
        clearHistory: () => history.length = 0
    };
}

// 使用示例
const calc = advancedCalculator();
console.log(calc.calculate(10, 5, '+'));  // 15
console.log(calc.calculate(10, 5, '^'));  // 100000
console.log(calc.getHistory());`;
        }
        
        // 默认响应
        return `🤖 **DeepSeek AI 智能响应**

感谢您的消息！这是一个增强的模拟响应，用于演示DeepSeek AI的完整功能。

💭 **您的消息**："${prompt}"

🚀 **可用功能演示**：
- ✅ 实时对话交流
- ✅ 智能代码生成
- ✅ 深度文本分析
- ✅ 多语言翻译
- ✅ 智能文本摘要
- ✅ 流式响应处理
- ✅ 批量任务处理
- ✅ AI智能建议

📋 **部署说明**：
1. 获取有效的DeepSeek API密钥
2. 更新配置文件中的API密钥
3. 确保网络连接正常
4. 重启服务器以应用配置

⏰ **响应时间**：${new Date().toLocaleString()}
🔧 **运行模式**：演示模式（所有功能可正常测试）`;
    }
}

module.exports = DeepSeekAI;
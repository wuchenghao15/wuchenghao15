const express = require('express');
const path = require('path');
const DeepSeekAI = require('./deepseek-ai');

const app = express();
const PORT = process.env.DEEPSEEK_PORT || 3001;

// 初始化DeepSeek AI
const deepseekAI = new DeepSeekAI();

// 中间件
app.use(express.json().catch(error => console.error(`[deepseek-server.js] express.json failed:`, error)));
app.use(express.static(path.join(__dirname, '../HTML')));

// 检查DeepSeek状态
app.get('/status', async (req, res) => {
    try {
        const isConfigured = await deepseekAI.isConfigured();
        const config = deepseekAI.getConfig();
        // 错误处理：getCacheStats是同步方法，使用try-catch捕获可能的错误
let cacheStats;
try {
    cacheStats = deepseekAI.getCacheStats();
} catch (error) {
    console.error(`[deepseek-server.js] deepseekAI.getCacheStats failed:`, error);
    cacheStats = { size: 0, maxSize: 0, enabled: false };
}

        res.json({ 
            initialized: true,
            configured: isConfigured,
            localModel: {
                enabled: config.localModel?.enabled || false,
                ready: false // 需要异步检查
            },
            features: config.features,
            cache: cacheStats,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({ 
            error: 'Status check failed',
            message: error.message 
        });
    }
});

// 聊天端点
app.post('/chat', async (req, res) => {
    try {
        const { message, options = {} } = req.body;
        
        if (!message) {
            return res.status(400).json({ 
                error: 'Message is required' 
            });
        }

        const response = await deepseekAI.callAPI(message, options);
        
        res.json({
            response: response,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error(`[deepseek-server.js] Chat error:, error`);
        res.status(500).json({ 
            error: 'Chat failed',
            message: error.message 
        });
    }
});

// 代码生成端点
app.post('/generate-code', async (req, res) => {
    try {
        const { description, language = 'javascript' } = req.body;
        
        if (!description) {
            return res.status(400).json({ 
                error: 'Description is required' 
            });
        }

        const code = await deepseekAI.generateCode(description, language);
        
        res.json({
            code: code,
            language: language,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error(`[deepseek-server.js] Code generation error:, error`);
        res.status(500).json({ 
            error: 'Code generation failed',
            message: error.message 
        });
    }
});

// 文本分析端点
app.post('/analyze', async (req, res) => {
    try {
        const { text } = req.body;
        
        if (!text) {
            return res.status(400).json({ 
                error: 'Text is required' 
            });
        }

        const analysis = await deepseekAI.analyzeText(text);
        
        res.json({
            analysis: analysis,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error(`[deepseek-server.js] Text analysis error:, error`);
        res.status(500).json({ 
            error: 'Text analysis failed',
            message: error.message 
        });
    }
});

// 启动服务器
app.listen(PORT, async () => {
    console.log(`🚀 DeepSeek AI 服务启动成功！`);
    console.log(`📍 服务地址: http://localhost:${PORT}`);
    console.log(`🔗 API文档: http://localhost:${PORT}/api-docs`);
    console.log(`📊 状态检查: http://localhost:${PORT}/status`);
    
    try {
        // 检查本地模型状态
        const config = deepseekAI.getConfig().catch(error => console.error(`[deepseek-server.js] deepseekAI.getConfig failed:`, error));
        if (config.localModel?.enabled) {
            console.log(`🤖 本地模型已启用`);
            console.log(`📁 模型路径: ${config.localModel.modelPath}`);
        } else {
            console.log(`🌐 使用云端API模式`);
        }
    } catch (error) {
        console.error(`[deepseek-server.js] 初始化检查失败:, error`);
    }
});

// 优雅关闭
process.on('SIGTERM', () => {
    console.log('收到SIGTERM信号，正在关闭服务器...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('收到SIGINT信号，正在关闭服务器...');
    process.exit(0);
});

module.exports = app;
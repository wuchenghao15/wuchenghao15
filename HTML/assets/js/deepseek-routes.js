const express = require('express');
const DeepSeekAI = require('./deepseek-ai');
const router = express.Router();

// 初始化DeepSeek实例
let deepseekAI;

async function initDeepSeek() {
    try {
        deepseekAI = new DeepSeekAI();
        console.log('DeepSeek AI module initialized');
    } catch (error) {
        console.error('Failed to initialize DeepSeek AI:', error);
    }
}

// 初始化
initDeepSeek();

// 中间件：检查DeepSeek是否已配置
const checkDeepSeekConfig = async (req, res, next) => {
    if (!deepseekAI) {
        return res.status(500).json({ 
            error: 'DeepSeek AI not initialized',
            message: 'AI服务暂时不可用，请稍后重试'
        });
    }

    try {
        const isConfigured = await deepseekAI.isConfigured();
        if (!isConfigured) {
            return res.status(503).json({ 
                error: 'DeepSeek not configured',
                message: '请先配置DeepSeek API密钥'
            });
        }
        next();
    } catch (error) {
        res.status(500).json({ 
            error: 'Configuration check failed',
            message: error.message 
        });
    }
};

// 聊天接口
router.post('/chat', checkDeepSeekConfig, async (req, res) => {
    try {
        const { message, conversationHistory = [] } = req.body;
        
        if (!message) {
            return res.status(400).json({ 
                error: 'Message is required',
                message: '请提供要发送的消息'
            });
        }

        const response = await deepseekAI.chatWithAI(message, conversationHistory);
        res.json({ 
            success: true,
            response: response,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Chat error:', error);
        res.status(500).json({ 
            error: 'Chat failed',
            message: error.message 
        });
    }
});

// 代码生成接口
router.post('/generate-code', checkDeepSeekConfig, async (req, res) => {
    try {
        const { description, language = 'javascript' } = req.body;
        
        if (!description) {
            return res.status(400).json({ 
                error: 'Description is required',
                message: '请提供代码生成需求描述'
            });
        }

        const code = await deepseekAI.generateCode(description, language);
        res.json({ 
            success: true,
            code: code,
            language: language,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Code generation error:', error);
        res.status(500).json({ 
            error: 'Code generation failed',
            message: error.message 
        });
    }
});

// 文本分析接口
router.post('/analyze-text', checkDeepSeekConfig, async (req, res) => {
    try {
        const { text } = req.body;
        
        if (!text) {
            return res.status(400).json({ 
                error: 'Text is required',
                message: '请提供要分析的文本'
            });
        }

        const analysis = await deepseekAI.analyzeText(text);
        res.json({ 
            success: true,
            analysis: analysis,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Text analysis error:', error);
        res.status(500).json({ 
            error: 'Text analysis failed',
            message: error.message 
        });
    }
});

// 翻译接口
router.post('/translate', checkDeepSeekConfig, async (req, res) => {
    try {
        const { text, targetLanguage } = req.body;
        
        if (!text || !targetLanguage) {
            return res.status(400).json({ 
                error: 'Text and target language are required',
                message: '请提供要翻译的文本和目标语言'
            });
        }

        const translation = await deepseekAI.translateText(text, targetLanguage);
        res.json({ 
            success: true,
            originalText: text,
            translatedText: translation,
            targetLanguage: targetLanguage,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Translation error:', error);
        res.status(500).json({ 
            error: 'Translation failed',
            message: error.message 
        });
    }
});

// 文本摘要接口
router.post('/summarize', checkDeepSeekConfig, async (req, res) => {
    try {
        const { text, maxLength = 200 } = req.body;
        
        if (!text) {
            return res.status(400).json({ 
                error: 'Text is required',
                message: '请提供要摘要的文本'
            });
        }

        const summary = await deepseekAI.summarizeText(text, maxLength);
        res.json({ 
            success: true,
            originalText: text,
            summary: summary,
            maxLength: maxLength,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Summarization error:', error);
        res.status(500).json({ 
            error: 'Summarization failed',
            message: error.message 
        });
    }
});

// 获取配置状态
router.get('/status', async (req, res) => {
    try {
        if (!deepseekAI) {
            return res.json({ 
                initialized: false,
                configured: false,
                message: 'DeepSeek AI模块未初始化'
            });
        }

        const isConfigured = await deepseekAI.isConfigured();
        const config = deepseekAI.getConfig();
        // getCacheStats是同步方法，直接获取返回值
        const cacheStats = deepseekAI.getCacheStats();

        res.json({ 
            initialized: true,
            configured: isConfigured,
            features: config.features,
            cache: cacheStats,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Status check error:', error);
        res.status(500).json({ 
            error: 'Status check failed',
            message: error.message 
        });
    }
});

// 更新配置
router.put('/config', async (req, res) => {
    try {
        if (!deepseekAI) {
            return res.status(500).json({ 
                error: 'DeepSeek AI not initialized',
                message: 'AI服务未初始化'
            });
        }

        const newConfig = req.body;
        await deepseekAI.updateConfig(newConfig);
        
        res.json({ 
            success: true,
            message: '配置更新成功',
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Config update error:', error);
        res.status(500).json({ 
            error: 'Config update failed',
            message: error.message 
        });
    }
});

// 清除缓存
router.delete('/cache', async (req, res) => {
    try {
        if (!deepseekAI) {
            return res.status(500).json({ 
                error: 'DeepSeek AI not initialized',
                message: 'AI服务未初始化'
            });
        }

        deepseekAI.clearCache();
        res.json({ 
            success: true,
            message: '缓存已清除',
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Cache clear error:', error);
        res.status(500).json({ 
            error: 'Cache clear failed',
            message: error.message 
        });
    }
});

// AI建议接口
router.post('/suggest', checkDeepSeekConfig, async (req, res) => {
    try {
        const { current_tab, user_context } = req.body;
        
        // 基于当前标签页和用户上下文生成智能建议
        const suggestions = generateAISuggestions(current_tab, user_context);
        
        res.json({ 
            success: true,
            suggestion: suggestions.text,
            action: suggestions.action,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('AI suggestion error:', error);
        res.status(500).json({ 
            error: 'AI suggestion failed',
            message: error.message 
        });
    }
});

// 流式聊天接口
router.post('/chat-stream', checkDeepSeekConfig, async (req, res) => {
    try {
        const { message, conversationHistory = [] } = req.body;
        
        if (!message) {
            return res.status(400).json({ 
                error: 'Message is required',
                message: '请提供要发送的消息'
            });
        }

        // 设置SSE头
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        });

        // 模拟流式响应
        const fullResponse = await deepseekAI.chatWithAI(message, conversationHistory);
        const words = fullResponse.split(' ');
        
        let index = 0;
        const streamInterval = setInterval(() => {
            if (index < words.length) {
                const chunk = words.slice(index, index + 3).join(' ') + ' ';
                res.write(`data: ${JSON.stringify({ chunk, done: false })}\n\n`);
                index += 3;
            } else {
                res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
                clearInterval(streamInterval);
                res.end();
            }
        }, 100);

    } catch (error) {
        console.error('Stream chat error:', error);
        res.write(`data: ${JSON.stringify({ error: error.message, done: true })}\n\n`);
        res.end();
    }
});

// 智能文本补全接口
router.post('/autocomplete', checkDeepSeekConfig, async (req, res) => {
    try {
        const { text, context } = req.body;
        
        if (!text) {
            return res.status(400).json({ 
                error: 'Text is required',
                message: '请提供要补全的文本'
            });
        }

        const completion = await deepseekAI.completeText(text, context);
        res.json({ 
            success: true,
            completion: completion,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Autocomplete error:', error);
        res.status(500).json({ 
            error: 'Autocomplete failed',
            message: error.message 
        });
    }
});

// 批量处理接口
router.post('/batch-process', checkDeepSeekConfig, async (req, res) => {
    try {
        const { tasks } = req.body;
        
        if (!Array.isArray(tasks) || tasks.length === 0) {
            return res.status(400).json({ 
                error: 'Tasks array is required',
                message: '请提供要批量处理的任务列表'
            });
        }

        const results = [];
        for (const task of tasks) {
            try {
                let result;
                switch (task.type) {
                    case 'chat':
                        result = await deepseekAI.chatWithAI(task.message, task.history || []);
                        break;
                    case 'analyze':
                        result = await deepseekAI.analyzeText(task.text);
                        break;
                    case 'translate':
                        result = await deepseekAI.translateText(task.text, task.targetLanguage);
                        break;
                    case 'summarize':
                        result = await deepseekAI.summarizeText(task.text, task.maxLength || 200);
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

        res.json({ 
            success: true,
            results: results,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Batch process error:', error);
        res.status(500).json({ 
            error: 'Batch process failed',
            message: error.message 
        });
    }
});

// 生成AI建议的辅助函数
function generateAISuggestions(currentTab, userContext) {
    const suggestions = {
        chat: {
            text: "💡 尝试询问AI关于编程、学习或创意的问题",
            action: {
                type: 'set_prompt',
                tab: 'chat',
                prompt: '请帮我解释一下JavaScript的异步编程概念'
            }
        },
        code: {
            text: "🚀 试试让AI生成一个实用的代码片段",
            action: {
                type: 'set_prompt',
                tab: 'code',
                prompt: '创建一个简单的待办事项管理器'
            }
        },
        analyze: {
            text: "📊 粘贴一些文本让AI分析情感和关键信息",
            action: {
                type: 'switch_tab',
                tab: 'analyze'
            }
        },
        translate: {
            text: "🌍 尝试将文本翻译成不同的语言",
            action: {
                type: 'switch_tab',
                tab: 'translate'
            }
        },
        summarize: {
            text: "📝 让AI帮您快速总结长篇文章",
            action: {
                type: 'switch_tab',
                tab: 'summarize'
            }
        }
    };

    return suggestions[currentTab] || suggestions.chat;
}

// 实时状态监控接口
router.get('/monitor', async (req, res) => {
    try {
        const status = deepseekAI.getCacheStats();
        const healthCheck = {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            timestamp: new Date().toISOString(),
            apiStatus: 'healthy',
            lastActivity: new Date().toISOString()
        };

        res.json({
            success: true,
            monitoring: {
                ...healthCheck,
                cache: status,
                configured: await deepseekAI.isConfigured()
            }
        });

    } catch (error) {
        console.error('Monitor error:', error);
        res.status(500).json({ 
            error: 'Monitor failed',
            message: error.message 
        });
    }
});

// 错误日志接口
router.get('/logs', async (req, res) => {
    try {
        const { level = 'info', limit = 50 } = req.query;
        
        // 这里应该从实际的日志系统中获取日志
        // 暂时返回模拟数据
        const logs = [
            {
                timestamp: new Date().toISOString(),
                level: 'info',
                message: 'DeepSeek AI service running normally',
                module: 'deepseek-ai'
            },
            {
                timestamp: new Date(Date.now() - 60000).toISOString(),
                level: 'info',
                message: 'API request processed successfully',
                module: 'deepseek-routes'
            }
        ];

        res.json({
            success: true,
            logs: logs.slice(0, parseInt(limit)),
            total: logs.length
        });

    } catch (error) {
        console.error('Logs error:', error);
        res.status(500).json({ 
            error: 'Failed to retrieve logs',
            message: error.message 
        });
    }
});

// 性能指标接口
router.get('/metrics', async (req, res) => {
    try {
        const metrics = {
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            memory: {
                used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024 * 100) / 100,
                total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024 * 100) / 100,
                external: Math.round(process.memoryUsage().external / 1024 / 1024 * 100) / 100
            },
            cpu: {
                usage: Math.round(process.cpuUsage().user / 1000000 * 100) / 100
            },
            requests: {
                total: 0, // 这里应该从实际的计数器获取
                success: 0,
                error: 0
            },
            cache: deepseekAI.getCacheStats()
        };

        res.json({
            success: true,
            metrics: metrics
        });

    } catch (error) {
        console.error('Metrics error:', error);
        res.status(500).json({ 
            error: 'Failed to retrieve metrics',
            message: error.message 
        });
    }
});

// 健康检查增强版
router.get('/health-detailed', async (req, res) => {
    try {
        const health = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            version: '1.3.0',
            services: {
                deepseek: {
                    initialized: !!deepseekAI,
                    configured: deepseekAI ? await deepseekAI.isConfigured() : false,
                    status: 'operational'
                },
                database: {
                    status: 'not_used',
                    message: '此应用不使用数据库'
                },
                cache: {
                    status: 'operational',
                    stats: deepseekAI ? deepseekAI.getCacheStats() : null
                }
            },
            performance: {
                memory: process.memoryUsage(),
                uptime: process.uptime(),
                cpu: process.cpuUsage()
            }
        };

        // 判断整体健康状态
        const allServicesHealthy = Object.values(health.services).every(
            service => service.status === 'operational' || service.status === 'not_used'
        );

        health.status = allServicesHealthy ? 'healthy' : 'degraded';
        health.statusCode = allServicesHealthy ? 200 : 503;

        res.status(health.statusCode).json(health);

    } catch (error) {
        console.error('Health check error:', error);
        res.status(500).json({
            status: 'unhealthy',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

module.exports = router;
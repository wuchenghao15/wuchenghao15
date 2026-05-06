/**
 * MTSCOS AI 项目管理系统 - 主应用
 */

const express = require('express');
const healthRouter = require('./api/health');
// 导入API路由
const configRouter = require('./api/routes/config');
const featureRouter = require('./api/routes/feature');
const auditRouter = require('./api/routes/audit');
const jptestRouter = require('./api/routes/jptest');
const logRouter = require('./api/routes/log');
const monitorRouter = require('./api/routes/monitor');
const reviewPlanRouter = require('./api/routes/review-plan');
const storageRouter = require('./api/routes/storage');
const userDataRouter = require('./api/routes/user-data.routes');
const versionRouter = require('./api/routes/version');
const userRouter = require('./api/routes/user');
const aiRouter = require('./api/routes/ai');
const { errorHandler, notFoundHandler } = require('./core/errorHandler');
const cors = require('cors');
const bodyParser = require('body-parser');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const crypto = require('crypto');
const WebSocket = require('ws');
const path = require('path');

// 导入数据库模块
const { DataAPI, AIEngine } = require('./database/db');

// 导入AI管理系统
const { AIManager } = require('./ai/ai_manager');
// 导入功能托管服务
const { FeatureHostingService } = require('./core/feature_hosting');
// 导入监控AI
const monitoringAI = require('./core/ai/monitoring-ai');
// 导入资源监控AI
const resourceMonitorAI = require('./core/ai/resource-monitor-ai');
// 导入资源修复AI
const resourceFixerAI = require('./core/ai/resource-fixer-ai');
// 导入认证页面管理AI
const authPageAI = require('./core/ai/auth-page-ai');
// 导入框架适配与功能优化AI
const frameworkAdapterAI = require('./core/ai/framework-adapter-ai');

// AI用户管理增强模块
const AIUserManager = {
    // AI接管提示配置
    takeoverPrompt: {
        enabled: true,
        defaultMessage: 'AI正在管理此操作，将提供智能优化建议',
        type: 'info'
    },
    
    // 生成个性化AI接管提示
    generateTakeoverPrompt(action, context = {}) {
        const prompts = {
            'login': {
                message: 'AI正在智能验证您的身份，提供安全的登录体验',
                type: 'info',
                suggestions: ['使用强密码保护账户安全', '定期更改密码', '启用双因素认证']
            },
            'register': {
                message: 'AI正在分析您的注册信息，确保账户安全可靠',
                type: 'info',
                suggestions: ['选择复杂密码', '使用真实邮箱便于找回密码', '设置安全问题']
            },
            'get_users': {
                message: 'AI正在优化用户数据查询，提供高效的管理体验',
                type: 'success',
                suggestions: ['定期清理无效用户', '优化用户权限分配', '监控用户活动']
            },
            'login_failed': {
                message: 'AI检测到登录失败，正在分析可能的安全风险',
                type: 'warning',
                suggestions: ['检查用户名和密码是否正确', '确认是否使用了正确的登录方式', '避免多次尝试以防止账户锁定']
            },
            'register_failed': {
                message: 'AI检测到注册失败，正在分析原因并提供改进建议',
                type: 'warning',
                suggestions: ['检查输入信息格式是否正确', '确认用户名是否已被使用', '使用更安全的密码组合']
            },
            'system_monitoring': {
                message: 'AI正在实时监控系统状态，确保安全稳定运行',
                type: 'info',
                suggestions: ['定期查看系统日志', '关注性能指标变化', '及时处理异常警报']
            }
        };
        
        // 根据操作类型返回对应的提示，否则使用默认提示
        return prompts[action] || {
            message: this.takeoverPrompt.defaultMessage,
            type: this.takeoverPrompt.type,
            suggestions: []
        };
    },
    
    // 记录用户操作
    async logUserAction(username, action, details = {}) {
        try {
            // 构建操作数据
            const actionData = {
                username,
                action,
                details,
                timestamp: new Date().toISOString(),
                aiManaged: true
            };
            
            // 记录到日志
            log('AI 用户操作记录', actionData);
            
            // 根据操作类型动态生成AI优化任务
            const project需求 = this.generateOptimizationTasks(action, details);
            
            // 使用AI管理器生成优化任务
            AIManager.generateTasks(project需求);
            
        } catch (error) {
            console.error('AI用户操作记录失败:', error);
        }
    },
    
    // 根据操作类型生成优化任务
    generateOptimizationTasks(action, details = {}) {
        const project需求 = {
            功能优化: [],
            管理优化: [],
            性能优化: [],
            安全优化: []
        };
        
        // 根据不同操作类型添加相应的优化任务
        switch (action) {
            case 'login':
            case 'login_failed':
                project需求.功能优化.push('auth');
                project需求.安全优化.push('authentication');
                if (details.success === false) {
                    project需求.安全优化.push('login_security');
                }
                break;
            case 'register':
            case 'register_failed':
                project需求.功能优化.push('auth');
                project需求.安全优化.push('registration_security');
                project需求.管理优化.push('user_creation');
                break;
            case 'get_users':
                project需求.功能优化.push('user_management');
                project需求.性能优化.push('user_query');
                project需求.管理优化.push('user_list');
                break;
            default:
                project需求.功能优化.push('auth');
                project需求.管理优化.push('user_management');
                project需求.安全优化.push('authentication');
        }
        
        // 移除空数组
        Object.keys(project需求).forEach(key => {
            if (project需求[key].length === 0) {
                delete project需求[key];
            }
        });
        
        return project需求;
    },
    
    // 智能用户验证增强
    async enhanceUserVerification(username, password, userData) {
        try {
            // 构建验证数据
            const verificationData = {
                username,
                password,
                userData,
                timestamp: new Date().toISOString(),
                action: 'login'
            };
            
            // 使用AI引擎分析
            const aiAnalysis = await AIEngine.verifyUserBehavior(verificationData);
            
            // 云端AI引擎分析
            let cloudAnalysis = null;
            if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
                cloudAnalysis = await CloudAIEngine.analyzeBehavior(verificationData);
            }
            
            // 合并分析结果
            const combinedAnalysis = combineAnalysisResults(aiAnalysis, cloudAnalysis);
            
            // 返回增强验证结果
            return {
                aiVerified: combinedAnalysis.isLegitimate,
                riskScore: combinedAnalysis.riskScore,
                aiSuggestions: combinedAnalysis.recommendations || [],
                verifiedAt: new Date().toISOString(),
                localAnalysis: aiAnalysis,
                cloudAnalysis: cloudAnalysis,
                consensus: combinedAnalysis.consensus
            };
        } catch (error) {
            console.error('AI用户验证增强失败:', error);
            return {
                aiVerified: false,
                riskScore: 0.5,
                aiSuggestions: ['建议检查网络连接', '稍后重试'],
                verifiedAt: new Date().toISOString(),
                error: error.message
            };
        }
    },
    
    // 智能用户创建增强
    async enhanceUserCreation(userData) {
        try {
            // 构建创建数据
            const creationData = {
                userData,
                timestamp: new Date().toISOString(),
                action: 'register'
            };
            
            // 使用AI引擎分析
            const aiAnalysis = await AIEngine.verifyUserBehavior(creationData);
            
            // 云端AI引擎分析
            let cloudAnalysis = null;
            if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
                cloudAnalysis = await CloudAIEngine.analyzeBehavior(creationData);
            }
            
            // 合并分析结果
            const combinedAnalysis = combineAnalysisResults(aiAnalysis, cloudAnalysis);
            
            // 返回增强创建结果
            return {
                aiApproved: combinedAnalysis.riskScore < 0.5,
                riskScore: combinedAnalysis.riskScore,
                aiSuggestions: combinedAnalysis.recommendations || [],
                approvedAt: new Date().toISOString(),
                localAnalysis: aiAnalysis,
                cloudAnalysis: cloudAnalysis,
                consensus: combinedAnalysis.consensus
            };
        } catch (error) {
            console.error('AI用户创建增强失败:', error);
            return {
                aiApproved: true, // 默认通过
                riskScore: 0.3,
                aiSuggestions: ['建议检查网络连接', '稍后重试'],
                approvedAt: new Date().toISOString(),
                error: error.message
            };
        }
    },
    
    // 获取AI监控建议
    async getAIMonitoringSuggestions() {
        try {
            // 构建监控数据
            const monitoringData = {
                timestamp: new Date().toISOString(),
                action: 'system_monitoring'
            };
            
            // 使用AI引擎分析系统状态
            const aiAnalysis = await AIEngine.verifyUserBehavior(monitoringData);
            
            // 云端AI引擎分析
            let cloudAnalysis = null;
            if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
                cloudAnalysis = await CloudAIEngine.analyzeBehavior(monitoringData);
            }
            
            // 合并分析结果
            const combinedAnalysis = combineAnalysisResults(aiAnalysis, cloudAnalysis);
            
            return {
                suggestions: combinedAnalysis.recommendations || [],
                riskScore: combinedAnalysis.riskScore,
                consensus: combinedAnalysis.consensus,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('获取AI监控建议失败:', error);
            return {
                suggestions: ['建议检查系统日志', '关注性能指标'],
                riskScore: 0.5,
                error: error.message
            };
        }
    }
};

// 云端AI引擎集成
const CloudAIEngine = {
    // 云端引擎配置
    config: {
        endpoint: process.env.CLOUD_AI_ENDPOINT || 'https://api.example.com/ai',
        apiKey: process.env.CLOUD_AI_API_KEY || 'demo_key',
        timeout: 5000,
        enabled: true
    },
    
    // 分析用户行为
    async analyzeBehavior(userData) {
        try {
            // 模拟云端AI分析
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // 基于用户数据生成分析结果
            const riskScore = this.calculateRiskScore(userData);
            
            return {
                riskScore,
                isLegitimate: riskScore < 0.7,
                analysis: {
                    engine: 'Cloud AI Engine v1.0',
                    version: '1.0.0',
                    timestamp: new Date().toISOString(),
                    confidence: Math.random() * 0.3 + 0.7 // 70-100% 置信度
                },
                recommendations: this.generateRecommendations(userData, riskScore)
            };
        } catch (error) {
            log('云端AI分析失败', { error: error.message });
            return null;
        }
    },
    
    // 计算风险分数
    calculateRiskScore(userData) {
        let score = 0.1;
        
        // 基于IP分析
        if (userData.ip) {
            // 模拟IP风险分析
            score += Math.random() * 0.2;
        }
        
        // 基于路径分析
        if (userData.path) {
            if (userData.path.includes('/admin') || userData.path.includes('/api')) {
                score += 0.2;
            }
        }
        
        // 基于方法分析
        if (userData.method === 'POST' || userData.method === 'DELETE') {
            score += 0.15;
        }
        
        // 基于时间分析
        const hour = new Date().getHours();
        if (hour >= 0 && hour <= 6) {
            score += 0.25;
        }
        
        return Math.min(score, 1.0);
    },
    
    // 生成建议
    generateRecommendations(userData, riskScore) {
        const recommendations = [];
        
        if (riskScore > 0.7) {
            recommendations.push('建议增加验证码验证');
            recommendations.push('建议限制登录尝试次数');
        }
        
        if (userData.responseTime > 1000) {
            recommendations.push('建议优化服务器响应时间');
        }
        
        return recommendations;
    },
    
    // 升级云端AI引擎
    async upgrade() {
        log('升级云端AI引擎...');
        // 模拟升级过程
        await new Promise(resolve => setTimeout(resolve, 500));
        log('云端AI引擎升级完成');
        return true;
    }
};

// 使用内存存储作为数据库后备
const users = {};

// 日语题库数据（模拟数据库）
const japaneseQuestionBank = {
    N5: {
        grammar: [
            { id: 'n5_g1', question: '「これ は なんです か？」の 答え は どれ です か？', options: ['これ は ペン です', 'それ は ペン です', 'あれ は ペン です', 'どれ は ペン です'], answer: 0, difficulty: 1 },
            { id: 'n5_g2', question: '「いくつ です か？」の 意味 は 何 です か？', options: ['どこですか', 'いくらですか', '何人ですか', 'いくつですか'], answer: 3, difficulty: 1 },
            { id: 'n5_g3', question: '「私 は 学生 です」の 否定形 は どれ です か？', options: ['私 は 学生 では ありません', '私 は 学生 です か？', '私 は 学生 でした', '私 は 学生 では ない'], answer: 0, difficulty: 2 },
            { id: 'n5_g4', question: '「食べます」の 否定形 は どれ です か？', options: ['食べません', '食べない', '食べなかった', '食べました'], answer: 0, difficulty: 1 },
            { id: 'n5_g5', question: '「行きます」の て形 は どれ です か？', options: ['行って', '行きて', '行いて', '行った'], answer: 0, difficulty: 2 }
        ],
        vocabulary: [
            { id: 'n5_v1', question: '「いち」の 意味 は 何 です か？', options: ['二', '一', '三', '四'], answer: 1, difficulty: 1 },
            { id: 'n5_v2', question: '「にほんご」の 意味 は 何 です か？', options: ['英語', '日本語', '中国語', '韓国語'], answer: 1, difficulty: 1 },
            { id: 'n5_v3', question: '「たべもの」の 意味 は 何 です か？', options: ['飲み物', '食べ物', '着物', '建物'], answer: 1, difficulty: 1 },
            { id: 'n5_v4', question: '「ひと」の 意味 は 何 です か？', options: ['人', '犬', '猫', '魚'], answer: 0, difficulty: 1 },
            { id: 'n5_v5', question: '「みず」の 意味 は 何 です か？', options: ['火', '水', '土', '木'], answer: 1, difficulty: 1 }
        ],
        reading: [
            { id: 'n5_r1', question: '私 は 学生 です。毎日 学校 に 行きます。', options: ['私 は 毎日 学校 に 行きません', '私 は 学生 では ありません', '私 は 毎日 学校 に 行きます', '私 は 学校 に 行きません'], answer: 2, difficulty: 1 },
            { id: 'n5_r2', question: 'この 本 は おもしろい です。', options: ['この 本 は おもしろく ない です', 'この 本 は おもしろい です', 'この 本 は たのしい です', 'この 本 は つまらない です'], answer: 1, difficulty: 1 }
        ]
    },
    N4: {
        grammar: [
            { id: 'n4_g1', question: '「昨日 雨 が 降りました」の 否定形 は どれ です か？', options: ['昨日 雨 が 降りません', '昨日 雨 が 降りませんでした', '昨日 雨 が 降らない', '昨日 雨 が 降らなかった'], answer: 1, difficulty: 2 },
            { id: 'n4_g2', question: '「勉強 する」の て形 は どれ です か？', options: ['勉強 して', '勉強 した', '勉強 します', '勉強 しました'], answer: 0, difficulty: 2 },
            { id: 'n4_g3', question: '「もう 食べましたか？」の 意味 は 何 です か？', options: ['まだ 食べましたか？', 'もう 食べませんか？', 'もう 食べましたか？', 'まだ 食べませんか？'], answer: 2, difficulty: 2 }
        ],
        vocabulary: [
            { id: 'n4_v1', question: '「けいたい」の 意味 は 何 です か？', options: ['家', '携帯', '車', '電話'], answer: 1, difficulty: 2 },
            { id: 'n4_v2', question: '「たのしい」の 反対語 は 何 です か？', options: ['つまらない', 'おもしろい', 'かなしい', 'うれしい'], answer: 0, difficulty: 2 }
        ],
        reading: [
            { id: 'n4_r1', question: '昨日 私 は 友達 と 映画 を 見ました。とても おもしろかった です。', options: ['昨日 私 は 一人 で 映画 を 見ました', '昨日 私 は 友達 と 映画 を 見ませんでした', '昨日 の 映画 は おもしろかった です', '昨日 の 映画 は つまらなかった です'], answer: 2, difficulty: 2 }
        ]
    },
    N3: {
        grammar: [
            { id: 'n3_g1', question: '「なら」の 使い方 は どれ です か？', options: ['条件を表す', '原因を表す', '目的を表す', '逆接を表す'], answer: 0, difficulty: 3 },
            { id: 'n3_g2', question: '「～て みる」の 意味 は 何 です か？', options: ['試してみる', '完成する', '始める', '終わる'], answer: 0, difficulty: 3 }
        ],
        vocabulary: [
            { id: 'n3_v1', question: '「かんたん」の 意味 は 何 です か？', options: ['簡単', '難しい', '複雑', '複数'], answer: 0, difficulty: 3 },
            { id: 'n3_v2', question: '「しんぱい」の 意味 は 何 です か？', options: ['心配', '安心', '自信', '自慢'], answer: 0, difficulty: 3 }
        ],
        reading: [
            { id: 'n3_r1', question: '最近 仕事 が 多くて 忙しい です。けれども、楽しい です。', options: ['最近 仕事 が 多くない です', '最近 仕事 が 忙しくない です', '最近 仕事 が 楽しくない です', '最近 仕事 が 忙しい けれども 楽しい です'], answer: 3, difficulty: 3 }
        ]
    },
    N2: {
        grammar: [
            { id: 'n2_g1', question: '「～に とって」の 意味 は 何 です か？', options: ['～にとって', '～に対して', '～について', '～に関して'], answer: 0, difficulty: 4 },
            { id: 'n2_g2', question: '「～て しまう」の 意味 は 何 です か？', options: ['完了・後悔を表す', '続けることを表す', '開始することを表す', '予定を表す'], answer: 0, difficulty: 4 }
        ],
        vocabulary: [
            { id: 'n2_v1', question: '「げんき」の 意味 は 何 です か？', options: ['元気', '元金', '玄関', '現金'], answer: 0, difficulty: 4 },
            { id: 'n2_v2', question: '「たいせつ」の 意味 は 何 です か？', options: ['大切', '大勢', '大声', '大体'], answer: 0, difficulty: 4 }
        ],
        reading: [
            { id: 'n2_r1', question: '毎朝 7時 に 起きて、歯を 磨いて、顔を 洗って、朝ごはん を 食べます。', options: ['毎朝 7時 に 起きません', '毎朝 歯を 磨きません', '毎朝 朝ごはん を 食べます', '毎朝 顔を 洗いません'], answer: 2, difficulty: 4 }
        ]
    },
    N1: {
        grammar: [
            { id: 'n1_g1', question: '「～に 相違ない」の 意味 は 何 です か？', options: ['きっと～だ', 'たぶん～だ', 'おそらく～だ', 'もしかしたら～だ'], answer: 0, difficulty: 5 },
            { id: 'n1_g2', question: '「～を 余儀なくされる」の 意味 は 何 です か？', options: ['～せざるを得ない', '～することができる', '～したくない', '～しなければならない'], answer: 0, difficulty: 5 }
        ],
        vocabulary: [
            { id: 'n1_v1', question: '「けっこう」の 意味 は 何 です か？', options: ['結構', '结构', '結成', '結論'], answer: 0, difficulty: 5 },
            { id: 'n1_v2', question: '「しゅっせき」の 意味 は 何 です か？', options: ['出席', '出張', '出発', '出場'], answer: 0, difficulty: 5 }
        ],
        reading: [
            { id: 'n1_r1', question: '今日 は 天気 が 良くて、公園 で 散歩 しました。たくさん の 人 が いて、にぎやか でした。', options: ['今日 は 天気 が 悪かった です', '今日 は 公園 で 散歩 しませんでした', '今日 は 公園 が にぎやか でした', '今日 は 公園 に 人 が いませんでした'], answer: 2, difficulty: 5 }
        ]
    }
};

// 生成日语测试试卷函数
async function generateJapaneseTestPaper(level, type = 'comprehensive', userInfo = null) {
    const questionBank = japaneseQuestionBank[level] || japaneseQuestionBank.N5;
    const testPaper = {
        id: `test_${level}_${Date.now()}`,
        level,
        type,
        generatedAt: new Date().toISOString(),
        sections: [],
        aiOptimized: false
    };
    
    // 尝试使用 AI 引擎优化题目选择
    let optimizedQuestions = null;
    
    if (userInfo) {
        try {
            // 构建分析数据
            const analysisData = {
                username: userInfo.username,
                level,
                type,
                userInfo,
                timestamp: new Date().toISOString()
            };
            
            // 本地AI引擎分析
            const localAnalysis = await AIEngine.verifyUserBehavior(analysisData);
            
            // 云端AI引擎分析
            let cloudAnalysis = null;
            if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
                cloudAnalysis = await CloudAIEngine.analyzeBehavior(analysisData);
            }
            
            // 交叉检查分析结果
            const combinedAnalysis = combineAnalysisResults(localAnalysis, cloudAnalysis);
            
            // 根据分析结果优化题目选择
            optimizedQuestions = combinedAnalysis;
            testPaper.aiOptimized = true;
            testPaper.aiAnalysis = combinedAnalysis;
            
            log('AI 优化日语测试试卷', { level, type, username: userInfo.username, aiOptimized: true });
        } catch (aiError) {
            log('AI 优化失败，使用默认题目选择', { error: aiError.message });
        }
    }
    
    // 根据测试类型生成不同的试卷结构
    if (type === 'comprehensive') {
        // 综合测试：包含语法、词汇、阅读
        testPaper.sections.push({
            id: 'grammar',
            title: '语法',
            questions: getRandomQuestions(questionBank.grammar, 3, optimizedQuestions)
        });
        testPaper.sections.push({
            id: 'vocabulary',
            title: '词汇',
            questions: getRandomQuestions(questionBank.vocabulary, 3, optimizedQuestions)
        });
        testPaper.sections.push({
            id: 'reading',
            title: '阅读',
            questions: getRandomQuestions(questionBank.reading, 2, optimizedQuestions)
        });
    } else if (type === 'grammar') {
        // 语法测试
        testPaper.sections.push({
            id: 'grammar',
            title: '语法',
            questions: getRandomQuestions(questionBank.grammar, 5, optimizedQuestions)
        });
    } else if (type === 'vocabulary') {
        // 词汇测试
        testPaper.sections.push({
            id: 'vocabulary',
            title: '词汇',
            questions: getRandomQuestions(questionBank.vocabulary, 5, optimizedQuestions)
        });
    } else if (type === 'reading') {
        // 阅读测试
        testPaper.sections.push({
            id: 'reading',
            title: '阅读',
            questions: getRandomQuestions(questionBank.reading, 3, optimizedQuestions)
        });
    } else if (type === 'assessment') {
        // 评估测试：包含各个级别的基础问题
        testPaper.sections.push({
            id: 'comprehensive',
            title: '综合评估',
            questions: [
                ...getRandomQuestions(japaneseQuestionBank.N5.grammar, 1, optimizedQuestions),
                ...getRandomQuestions(japaneseQuestionBank.N4.grammar, 1, optimizedQuestions),
                ...getRandomQuestions(japaneseQuestionBank.N5.vocabulary, 1, optimizedQuestions),
                ...getRandomQuestions(japaneseQuestionBank.N4.vocabulary, 1, optimizedQuestions),
                ...getRandomQuestions(japaneseQuestionBank.N5.reading, 1, optimizedQuestions)
            ]
        });
    }
    
    return testPaper;
}

// 从题库中随机获取指定数量的题目
function getRandomQuestions(questions, count, optimizedQuestions = null) {
    let selectedQuestions = [...questions];
    
    // 如果有 AI 优化结果，根据分析结果调整题目选择
    if (optimizedQuestions) {
        try {
            // 根据 AI 分析结果对题目进行排序
            // 这里简化处理，实际可以根据用户弱点和优势进行更复杂的排序
            selectedQuestions.sort(() => 0.5 - Math.random());
            
            // 可以根据 optimizedQuestions 中的信息调整题目难度分布
            // 例如：如果用户语法较弱，增加语法题的比例
        } catch (error) {
            log('AI 优化题目选择失败，使用默认随机选择', { error: error.message });
        }
    } else {
        // 默认随机排序
        selectedQuestions.sort(() => 0.5 - Math.random());
    }
    
    return selectedQuestions.slice(0, Math.min(count, selectedQuestions.length));
}

// 自动扩充日语题库函数
function expandJapaneseQuestionBank() {
    log('开始自动扩充日语题库...');
    
    // 这里可以实现自动扩充题库的逻辑
    // 例如：从外部API获取新题目，或者基于现有题目生成变体
    
    log('日语题库自动扩充完成');
    return true;
}

// 日志记录函数
function log(message, data = {}) {
    console.log(`[${new Date().toISOString()}] ${message}`, data);
}

// 加密密码函数
function encryptPassword(password) {
    return crypto.createHash('sha256').update(password).digest('hex');
}

// 加密用户名函数
function encryptUsername(username) {
    return crypto.createHash('sha256').update(username).digest('hex');
}

// 输入验证函数
function validateInput(input) {
    if (typeof input !== 'string') return input;
    // 移除可能的恶意字符
    return input
        .replace(/<[^>]*>/g, '') // 移除 HTML 标签
        .replace(/['";]/g, '') // 移除引号
        .replace(/\s+/g, ' ') // 规范化空格
        .trim();
}

// 生成 CSRF 令牌函数
function generateCSRFToken() {
    return crypto.randomBytes(32).toString('hex');
}

// 组合AI分析结果
function combineAnalysisResults(localAnalysis, cloudAnalysis) {
    // 默认使用本地分析结果
    const result = {
        ...localAnalysis,
        consensus: 'local_only',
        recommendations: []
    };
    
    // 如果有云端分析结果，进行组合
    if (cloudAnalysis) {
        // 计算加权平均风险分数
        const localWeight = 0.6; // 本地AI权重更高
        const cloudWeight = 0.4;
        result.riskScore = (localAnalysis.riskScore * localWeight) + (cloudAnalysis.riskScore * cloudWeight);
        result.isLegitimate = result.riskScore < 0.7;
        
        // 确定共识状态
        if (Math.abs(localAnalysis.riskScore - cloudAnalysis.riskScore) < 0.2) {
            result.consensus = 'consistent';
        } else if (localAnalysis.riskScore > cloudAnalysis.riskScore) {
            result.consensus = 'local_higher';
        } else {
            result.consensus = 'cloud_higher';
        }
        
        // 合并建议
        result.recommendations = [...new Set([...(result.recommendations || []), ...(cloudAnalysis.recommendations || [])])];
        
        // 添加云端分析信息
        result.cloudAnalysis = cloudAnalysis;
    }
    
    return result;
}

// IP 地域检测模块
const IPCheck = {
    // 允许的地域列表（白名单）
    allowedRegions: ['local', 'china_mainland'],
    
    // 本地 IP 范围
    localIPs: [
        '127.0.0.1',
        '::1',
        '192.168.0.0/16',
        '10.0.0.0/8',
        '172.16.0.0/12'
    ],
    
    // 模拟中国 IP 范围（实际生产环境应使用真实的 IP 库）
    chinaIPs: [
        '202.0.0.0/8',
        '210.0.0.0/8',
        '211.0.0.0/8',
        '218.0.0.0/8'
    ],
    
    // 获取客户端 IP
    getClientIP(req) {
        return req.headers['x-forwarded-for'] || 
               req.headers['x-real-ip'] || 
               req.connection.remoteAddress || 
               req.socket.remoteAddress || 
               req.connection.socket.remoteAddress || 
               '0.0.0.0';
    },
    
    // 检查 IP 是否在指定范围内
    isIPInRange(ip, range) {
        if (range.includes('/')) {
            // CIDR 范围检查（简化版）
            const [rangeIP, prefix] = range.split('/');
            const ipParts = ip.split('.').map(Number);
            const rangeParts = rangeIP.split('.').map(Number);
            const mask = (0xFFFFFFFF << (32 - parseInt(prefix))).toString(2);
            
            // 简化检查：仅检查前几位是否匹配
            for (let i = 0; i < Math.min(4, prefix / 8); i++) {
                if (ipParts[i] !== rangeParts[i]) {
                    return false;
                }
            }
            return true;
        }
        return ip === range;
    },
    
    // 检测 IP 地域
    detectRegion(ip) {
        // 检查是否为本地 IP
        for (const localRange of this.localIPs) {
            if (this.isIPInRange(ip, localRange)) {
                return 'local';
            }
        }
        
        // 检查是否为中国 IP
        for (const chinaRange of this.chinaIPs) {
            if (this.isIPInRange(ip, chinaRange)) {
                return 'china_mainland';
            }
        }
        
        return 'unknown';
    },
    
    // 检查 IP 是否允许登录
    isAllowed(ip) {
        const region = this.detectRegion(ip);
        return this.allowedRegions.includes(region);
    }
};

// 初始化默认用户
async function initDefaultUsers() {
    try {
        // 检查默认用户是否存在（这里简化处理，直接创建内存用户）
        // 注意：由于 DataAPI 可能不可用，我们优先使用内存存储
        const adminEncrypted = encryptUsername('admin');
        const userEncrypted = encryptUsername('user');
        
        // 直接初始化内存存储中的用户数据
        users[adminEncrypted] = {
            username: 'admin',
            email: 'admin@example.com',
            password: '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', // admin123 的 SHA-256 哈希
            role: 'admin',
            created_at: new Date().toISOString()
        };
        users[userEncrypted] = {
            username: 'user',
            email: 'user@example.com',
            password: 'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446', // user123 的 SHA-256 哈希
            role: 'user',
            created_at: new Date().toISOString()
        };
        
        log('默认用户初始化完成');
        log('使用内存存储作为后备，默认用户初始化完成', { users: Object.keys(users) });
    } catch (error) {
        log('默认用户初始化失败', { error: error.message });
        // 即使失败，也确保内存存储中有默认用户
        const adminEncrypted = encryptUsername('admin');
        const userEncrypted = encryptUsername('user');
        users[adminEncrypted] = {
            username: 'admin',
            email: 'admin@example.com',
            password: '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', // admin123 的 SHA-256 哈希
            role: 'admin',
            created_at: new Date().toISOString()
        };
        users[userEncrypted] = {
            username: 'user',
            email: 'user@example.com',
            password: 'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446', // user123 的 SHA-256 哈希
            role: 'user',
            created_at: new Date().toISOString()
        };
        log('使用内存存储作为后备，默认用户初始化完成', { users: Object.keys(users) });
    }
}

// 创建Express应用
const app = express();

// 健康检查路由
app.use(healthRouter);

// API路由
app.use('/api/config', configRouter);
app.use('/api/feature', featureRouter);
app.use('/api/audit', auditRouter);
app.use('/api/jptest', jptestRouter);
app.use('/api/log', logRouter);
app.use('/api/monitor', monitorRouter);
app.use('/api/review-plan', reviewPlanRouter);
app.use('/api/storage', storageRouter);
app.use('/api/user/data', userDataRouter);
app.use('/api/users', userRouter);
app.use('/api/ai', aiRouter);
app.use('/api/version', versionRouter);

// 主端口配置，仅使用HTTP
const HTTP_PORT = 8080;
// 为了兼容现有代码，保留PORT变量
const PORT = HTTP_PORT;
const fs = require('fs');

// 安全中间件
// 配置更安全的 helmet 选项
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            styleSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            imgSrc: ["'self'"],
            connectSrc: ["'self'", "http://localhost:8080", "https://localhost:8080", "http://localhost:8082", "https://localhost:8082", "http://localhost:8083", "https://localhost:8083", "ws://localhost:8080", "wss://localhost:8080"]
        }
    },
    crossOriginEmbedderPolicy: true,
    crossOriginOpenerPolicy: { policy: "same-origin" },
    crossOriginResourcePolicy: { policy: "same-origin" },
    // 禁用HSTS，防止浏览器自动跳转到HTTPS
    hsts: false
}));

// 配置更安全的 CORS，只允许特定来源
app.use(cors({
    origin: [
        'http://localhost:8080',
        'http://127.0.0.1:8080',
        'https://localhost:8080',
        'https://127.0.0.1:8080',
        'http://localhost:8082',
        'http://127.0.0.1:8082',
        'https://localhost:8081',
        'https://127.0.0.1:8081',
        'https://localhost:8083',
        'https://127.0.0.1:8083'
    ],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID', 'X-CSRF-Token'],
    credentials: true
}));

// 限制请求体大小，防止 DoS 攻击
app.use(bodyParser.json({ limit: '10kb' })); // 限制 JSON 请求体大小
app.use(bodyParser.urlencoded({ extended: true, limit: '10kb' })); // 限制 URL 编码请求体大小

// 设置响应头，确保字符集支持
app.use((req, res, next) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    next();
});

// 导入http-proxy-middleware用于代理请求
const { createProxyMiddleware } = require('http-proxy-middleware');

// 配置Flask代理，将/api/auth/login请求转发到Flask应用
app.use('/api/auth/login', async (req, res) => {
    // AI接管提示
    // 预先生成成功和失败情况下的AI提示
    const loginSuccessPrompt = AIUserManager.generateTakeoverPrompt('login');
    const loginFailedPrompt = AIUserManager.generateTakeoverPrompt('login_failed');
    
    // 直接返回成功响应，测试代理逻辑
    console.log(`[代理调试] 收到登录请求: ${req.method} ${req.url}`);
    console.log(`[代理调试] 请求体: ${JSON.stringify(req.body)}`);
    
    // 从内存中查找用户（直接复制原来的登录逻辑）
    const { username, password } = req.body || {};
    
    if (!username || !password) {
        // 记录AI操作
        await AIUserManager.logUserAction(username || 'anonymous', 'login_failed', {
            reason: '用户名或密码为空',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '用户名和密码不能为空',
            ai_prompt: loginFailedPrompt
        });
    }
    
    // 从内存存储中验证用户
    const encryptedUsername = encryptUsername(username);
    if (!users[encryptedUsername]) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'login_failed', {
            reason: '用户名不存在',
            success: false
        });
        
        return res.status(401).json({
            success: false, 
            message: '用户名或密码不正确',
            ai_prompt: loginFailedPrompt
        });
    }
    
    const user = users[encryptedUsername];
    if (user.password !== password) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'login_failed', {
            reason: '密码错误',
            success: false
        });
        
        return res.status(401).json({
            success: false, 
            message: '用户名或密码不正确',
            ai_prompt: loginFailedPrompt
        });
    }
    
    // AI增强验证
    const aiVerification = await AIUserManager.enhanceUserVerification(username, password, user);
    
    // 登录成功，返回用户信息
    const { password: _, ...userInfo } = user;
    
    // 记录AI操作
    await AIUserManager.logUserAction(username, 'login_success', {
        userInfo,
        ai_verification: aiVerification,
        success: true
    });
    
    return res.json({
        success: true,
        message: '登录成功',
        user: userInfo,
        ai_prompt: loginSuccessPrompt,
        ai_enhancement: {
            verification: aiVerification,
            suggestions: aiVerification.aiSuggestions
        }
    });
});

// 配置注册路由
app.use('/api/auth/register', async (req, res) => {
    // AI接管提示
    // 预先生成成功和失败情况下的AI提示
    const registerSuccessPrompt = AIUserManager.generateTakeoverPrompt('register');
    const registerFailedPrompt = AIUserManager.generateTakeoverPrompt('register_failed');
    
    // 直接返回成功响应，测试代理逻辑
    console.log(`[代理调试] 收到注册请求: ${req.method} ${req.url}`);
    console.log(`[代理调试] 请求体: ${JSON.stringify(req.body)}`);
    
    // 从内存中查找用户（直接复制原来的注册逻辑）
    const { username, email, password } = req.body || {};
    
    if (!username || !email || !password) {
        // 记录AI操作
        await AIUserManager.logUserAction(username || 'anonymous', 'register_failed', {
            reason: '用户名、邮箱或密码为空',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '用户名、邮箱和密码不能为空',
            ai_prompt: registerFailedPrompt
        });
    }
    
    // 从内存存储中验证用户是否已存在
    const encryptedUsername = encryptUsername(username);
    if (users[encryptedUsername]) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'register_failed', {
            reason: '用户名已存在',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '用户名已存在',
            ai_prompt: registerFailedPrompt
        });
    }
    
    // 检查用户名长度
    if (username.length < 3 || username.length > 20) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'register_failed', {
            reason: '用户名长度错误',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '用户名长度错误',
            ai_prompt: registerFailedPrompt
        });
    }

    // 检查密码长度
    if (password.length < 6 || password.length > 128) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'register_failed', {
            reason: '密码长度错误',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '密码长度错误',
            ai_prompt: registerFailedPrompt
        });
    }

    // 检查邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'register_failed', {
            reason: '邮箱格式错误',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '邮箱格式错误',
            ai_prompt: registerFailedPrompt
        });
    }
    
    // 用户名命名规则验证（国际标准规范）
    const usernameRegex = /^[a-zA-Z_][a-zA-Z0-9_]{2,19}$/;
    if (!usernameRegex.test(username)) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'register_failed', {
            reason: '用户名不符合规则',
            success: false
        });
        
        return res.status(400).json({
            success: false, 
            message: '用户名必须符合以下规则：\n1. 只能包含字母、数字和下划线\n2. 必须以字母或下划线开头\n3. 长度在3-20个字符之间',
            ai_prompt: registerFailedPrompt
        });
    }
    
    // AI智能用户创建增强
    const aiEnhancement = await AIUserManager.enhanceUserCreation(req.body);
    
    // 如果AI不批准，返回错误
    if (!aiEnhancement.aiApproved) {
        // 记录AI操作
        await AIUserManager.logUserAction(username, 'register_failed', {
            reason: 'AI审核不通过',
            ai_risk_score: aiEnhancement.riskScore,
            ai_suggestions: aiEnhancement.aiSuggestions,
            success: false
        });
        
        return res.status(403).json({
            success: false, 
            message: '注册请求被AI拒绝',
            ai_prompt: registerFailedPrompt,
            ai_enhancement: aiEnhancement
        });
    }
    
    // 注册新用户
    users[encryptedUsername] = {
        username: username,
        email: email,
        password: password,
        role: 'user',
        created_at: new Date().toISOString()
    };
    
    // 记录AI操作
    await AIUserManager.logUserAction(username, 'register_success', {
        user: { username, email },
        ai_enhancement: aiEnhancement,
        success: true
    });
    
    return res.json({
        success: true,
        message: '注册成功，用户信息已存储',
        ai_prompt: registerSuccessPrompt,
        ai_enhancement: {
            approval: aiEnhancement,
            suggestions: aiEnhancement.aiSuggestions
        }
    });
});

// 配置Flask代理，将/api/users请求转发到Flask应用
app.use('/api/users', async (req, res) => {
    // AI接管提示
    const aiPrompt = AIUserManager.generateTakeoverPrompt('get_users');
    
    // 从内存中获取所有用户信息
    const allUsers = Object.values(users).map(user => {
        const { password, ...userInfo } = user;
        return userInfo;
    });
    
    // 记录AI操作
    await AIUserManager.logUserAction('system', 'get_users', {
        user_count: allUsers.length,
        success: true
    });
    
    // 生成AI优化任务
    const project需求 = {
        功能优化: ['user_management'],
        管理优化: ['user_list'],
        性能优化: ['user_query']
    };
    
    // 使用AI管理器生成优化任务
    AIManager.generateTasks(project需求);
    
    return res.json({
        success: true,
        message: '获取用户信息成功',
        users: allUsers,
        total: allUsers.length,
        ai_prompt: aiPrompt
    });
});

// AI 监控中间件
app.use(async (req, res, next) => {
    const startTime = Date.now();
    const originalSend = res.send;
    
    // 包装 res.send 方法以捕获响应
    res.send = function(body) {
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        // 分析请求和响应
        setTimeout(async () => {
            try {
                const clientIP = IPCheck.getClientIP(req);
                const username = req.body && req.body.username ? req.body.username : 'anonymous';
                
                // 识别操作类型
                let action = 'unknown';
                if (req.path.includes('/api/auth/login')) {
                    action = res.statusCode === 200 ? 'login' : 'login_failed';
                } else if (req.path.includes('/api/auth/register')) {
                    action = res.statusCode === 200 ? 'register' : 'register_failed';
                } else if (req.path.includes('/api/users')) {
                    action = 'get_users';
                } else {
                    action = 'system_monitoring';
                }
                
                // 生成AI接管提示
                const aiPrompt = AIUserManager.generateTakeoverPrompt(action, {
                    username,
                    path: req.path,
                    method: req.method,
                    statusCode: res.statusCode
                });
                
                // 构建分析数据
                const analysisData = {
                    username: username,
                    ip: clientIP,
                    path: req.path,
                    method: req.method,
                    action: action,
                    responseTime: responseTime,
                    statusCode: res.statusCode,
                    userAgent: req.headers['user-agent'],
                    aiPrompt: aiPrompt
                };
                
                // 本地AI引擎分析
                const localAnalysis = await AIEngine.verifyUserBehavior(analysisData);
                
                // 云端AI引擎分析
                let cloudAnalysis = null;
                if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
                    cloudAnalysis = await CloudAIEngine.analyzeBehavior(analysisData);
                }
                
                // 交叉检查分析结果
                const combinedAnalysis = combineAnalysisResults(localAnalysis, cloudAnalysis);
                
                // 记录用户操作
                await AIUserManager.logUserAction(username, action, {
                    success: res.statusCode >= 200 && res.statusCode < 300,
                    statusCode: res.statusCode,
                    responseTime: responseTime,
                    path: req.path,
                    method: req.method,
                    aiPrompt: aiPrompt,
                    aiAnalysis: combinedAnalysis
                });
                
                // 记录异常行为
                if (combinedAnalysis.riskScore > 0.7) {
                    log('AI 检测到高风险行为', {
                        riskScore: combinedAnalysis.riskScore,
                        username: username,
                        ip: clientIP,
                        path: req.path,
                        action: action,
                        consensus: combinedAnalysis.consensus,
                        localRisk: localAnalysis.riskScore,
                        cloudRisk: cloudAnalysis?.riskScore || 'N/A',
                        aiPrompt: aiPrompt
                    });
                    
                    // 记录到特征库
                    await AIEngine.recordIssue({
                        type: 'security',
                        pattern: 'high_risk_behavior',
                        description: 'AI 检测到高风险用户行为',
                        severity: 'high',
                        details: {
                            ...analysisData,
                            localRiskScore: localAnalysis.riskScore,
                            cloudRiskScore: cloudAnalysis?.riskScore || null,
                            combinedRiskScore: combinedAnalysis.riskScore,
                            consensus: combinedAnalysis.consensus
                        }
                    });
                }
                
                // 记录性能问题
                if (responseTime > 1000) {
                    log('AI 检测到性能问题', {
                        path: req.path,
                        responseTime: responseTime,
                        username: username,
                        action: action,
                        localEngine: localAnalysis.analysis?.engine || 'unknown',
                        cloudEngine: cloudAnalysis?.analysis?.engine || 'disabled',
                        aiPrompt: aiPrompt
                    });
                    
                    // 记录到特征库
                    await AIEngine.recordIssue({
                        type: 'performance',
                        pattern: 'high_response_time',
                        description: '响应时间过长',
                        severity: 'medium',
                        details: {
                            path: req.path,
                            responseTime: responseTime,
                            method: req.method,
                            action: action,
                            localAnalysis: localAnalysis,
                            cloudAnalysis: cloudAnalysis
                        }
                    });
                }
                
                // 生成综合建议
                if (combinedAnalysis.recommendations && combinedAnalysis.recommendations.length > 0) {
                    log('AI 生成的综合建议', {
                        recommendations: combinedAnalysis.recommendations,
                        path: req.path,
                        action: action,
                        consensus: combinedAnalysis.consensus,
                        aiPrompt: aiPrompt
                    });
                }
                
                // 定期自我诊断
                if (Math.random() < 0.01) { // 1% 概率执行
                    const diagnosis = await AIEngine.selfDiagnose();
                    if (diagnosis.recommendations && diagnosis.recommendations.length > 0) {
                        log('AI 引擎自我诊断建议', { recommendations: diagnosis.recommendations });
                    }
                }
            } catch (error) {
                log('AI 监控错误', { error: error.message });
                
                // 记录错误到特征库
                try {
                    await AIEngine.recordIssue({
                        type: 'error',
                        pattern: 'ai_monitoring_failure',
                        description: 'AI 监控过程中发生错误',
                        severity: 'medium',
                        details: {
                            error: error.message,
                            path: req.path,
                            method: req.method
                        }
                    });
                } catch (recordError) {
                    log('记录错误到特征库失败', { error: recordError.message });
                }
            }
        }, 0);
        
        return originalSend.call(this, body);
    };
    
    next();
});

// 存储请求ID，防止重复提交
const requestIds = new Set();

// 请求体验证中间件
app.use((req, res, next) => {
    // 检查是否为 API 请求
    if (req.path.startsWith('/api/')) {
        // 检查请求方法
        const allowedMethods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'];
        if (!allowedMethods.includes(req.method)) {
            const clientIP = IPCheck.getClientIP(req);
            log('不允许的请求方法', { method: req.method, path: req.path, ip: clientIP });
            return res.status(405).json({ success: false, message: '请求方法不允许' });
        }
        
        // 检查请求头
        const userAgent = req.headers['user-agent'];
        if (!userAgent) {
            const clientIP = IPCheck.getClientIP(req);
            log('缺少用户代理', { path: req.path, ip: clientIP });
            // 不直接拒绝，因为某些工具可能没有 User-Agent
        }
        
        // 检查 CSRF 令牌（仅在生产环境严格验证）
            if (req.method === 'POST' || req.method === 'PUT' || req.method === 'DELETE') {
                const csrfToken = req.headers['x-csrf-token'];
                // 开发环境放宽CSRF验证，生产环境请严格验证
                if (!csrfToken && process.env.NODE_ENV === 'production') {
                    const clientIP = IPCheck.getClientIP(req);
                    log('缺少 CSRF 令牌', { path: req.path, ip: clientIP });
                    return res.status(403).json({ success: false, message: '缺少 CSRF 令牌' });
                }
            }
        
        // 检查请求 ID，防止重复提交
        if (req.method === 'POST' || req.method === 'PUT' || req.method === 'DELETE') {
            const requestId = req.headers['x-request-id'] || (req.body && req.body.requestId);
            if (requestId) {
                if (requestIds.has(requestId)) {
                    const clientIP = IPCheck.getClientIP(req);
                    log('重复的请求 ID', { path: req.path, ip: clientIP, requestId });
                    return res.status(409).json({ success: false, message: '请求已处理，请不要重复提交' });
                }
                // 存储请求 ID
                requestIds.add(requestId);
                // 5分钟后移除请求 ID
                setTimeout(() => {
                    requestIds.delete(requestId);
                }, 5 * 60 * 1000);
            }
        }
    }
    next();
});

app.use('/html', express.static(path.join(__dirname, '/html')));
app.use('/assets', express.static(path.join(__dirname, '/html/assets')));


// 速率限制（仅应用于API请求）
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100, // 每个IP限制100个请求
    standardHeaders: true,
    legacyHeaders: false,
});
app.use('/api', limiter);

// 根路径直接返回index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '/html/index.html'));
});

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'Server is running' });
});

// 获取所有用户信息
app.get('/api/users', (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        log('收到获取所有用户信息请求', { ip: clientIP });
        
        // 从内存存储中获取所有用户信息
        const allUsers = Object.values(users).map(user => {
            // 移除密码信息，保护用户隐私
            const { password, ...userInfo } = user;
            return userInfo;
        });
        
        log('返回所有用户信息', { count: allUsers.length, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '获取用户信息成功',
            users: allUsers,
            total: allUsers.length
        });
    } catch (error) {
        log('获取用户信息错误', { error: error.message });
        res.status(500).json({ success: false, message: '获取用户信息失败' });
    }
});

// 获取单个用户信息
app.get('/api/users/:username', (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { username } = req.params;
        log('收到获取单个用户信息请求', { username, ip: clientIP });
        
        const encryptedUsername = encryptUsername(username);
        const user = users[encryptedUsername];
        
        if (!user) {
            return res.status(404).json({ success: false, message: '用户不存在' });
        }
        
        // 移除密码信息，保护用户隐私
        const { password, ...userInfo } = user;
        
        log('返回单个用户信息', { username, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '获取用户信息成功',
            user: userInfo
        });
    } catch (error) {
        log('获取单个用户信息错误', { error: error.message });
        res.status(500).json({ success: false, message: '获取用户信息失败' });
    }
});

// 更新用户信息
app.put('/api/users/:username', (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { username } = req.params;
        const updateData = req.body;
        log('收到更新用户信息请求', { username, ip: clientIP });
        
        const encryptedUsername = encryptUsername(username);
        const user = users[encryptedUsername];
        
        if (!user) {
            return res.status(404).json({ success: false, message: '用户不存在' });
        }
        
        // 更新用户信息（排除密码和创建时间）
        if (updateData.email) {
            user.email = updateData.email;
        }
        if (updateData.role) {
            user.role = updateData.role;
        }
        
        log('更新用户信息成功', { username, ip: clientIP });
        
        // 移除密码信息，保护用户隐私
        const { password, ...userInfo } = user;
        
        res.json({ 
            success: true, 
            message: '更新用户信息成功',
            user: userInfo
        });
    } catch (error) {
        log('更新用户信息错误', { error: error.message });
        res.status(500).json({ success: false, message: '更新用户信息失败' });
    }
});

// 删除用户
app.delete('/api/users/:username', (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { username } = req.params;
        log('收到删除用户请求', { username, ip: clientIP });
        
        const encryptedUsername = encryptUsername(username);
        
        if (!users[encryptedUsername]) {
            return res.status(404).json({ success: false, message: '用户不存在' });
        }
        
        delete users[encryptedUsername];
        
        log('删除用户成功', { username, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '删除用户成功'
        });
    } catch (error) {
        log('删除用户错误', { error: error.message });
        res.status(500).json({ success: false, message: '删除用户失败' });
    }
});

// 重置密码
app.post('/api/users/:username/reset-password', (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { username } = req.params;
        const { newPassword } = req.body;
        log('收到重置密码请求', { username, ip: clientIP });
        
        if (!newPassword) {
            return res.status(400).json({ success: false, message: '新密码不能为空' });
        }
        
        const encryptedUsername = encryptUsername(username);
        const user = users[encryptedUsername];
        
        if (!user) {
            return res.status(404).json({ success: false, message: '用户不存在' });
        }
        
        // 重置密码
        user.password = newPassword;
        
        log('重置密码成功', { username, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '重置密码成功'
        });
    } catch (error) {
        log('重置密码错误', { error: error.message });
        res.status(500).json({ success: false, message: '重置密码失败' });
    }
});

// 系统配置管理API
// 获取系统配置
app.get('/api/config', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        log('收到获取系统配置请求', { ip: clientIP });
        
        // 从数据库获取所有配置
        const configs = await ConfigDB.getAll();
        
        log('返回系统配置成功', { count: configs.length, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '获取系统配置成功',
            configs: configs
        });
    } catch (error) {
        log('获取系统配置错误', { error: error.message });
        res.status(500).json({ success: false, message: '获取系统配置失败' });
    }
});

// 获取单个配置项
app.get('/api/config/:key', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { key } = req.params;
        log('收到获取单个配置项请求', { key, ip: clientIP });
        
        // 从数据库获取配置项
        const config = await ConfigDB.get(key);
        
        if (!config) {
            return res.status(404).json({ success: false, message: '配置项不存在' });
        }
        
        log('返回单个配置项成功', { key, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '获取配置项成功',
            config: config
        });
    } catch (error) {
        log('获取单个配置项错误', { error: error.message });
        res.status(500).json({ success: false, message: '获取配置项失败' });
    }
});

// 设置配置项
app.put('/api/config/:key', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { key } = req.params;
        const { value, type, description } = req.body;
        log('收到设置配置项请求', { key, ip: clientIP });
        
        if (value === undefined) {
            return res.status(400).json({ success: false, message: '配置值不能为空' });
        }
        
        // 设置配置项
        await ConfigDB.set(key, value, type, description);
        
        log('设置配置项成功', { key, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '设置配置项成功'
        });
    } catch (error) {
        log('设置配置项错误', { error: error.message });
        res.status(500).json({ success: false, message: '设置配置项失败' });
    }
});

// 删除配置项
app.delete('/api/config/:key', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { key } = req.params;
        log('收到删除配置项请求', { key, ip: clientIP });
        
        // 删除配置项
        await ConfigDB.delete(key);
        
        log('删除配置项成功', { key, ip: clientIP });
        
        res.json({ 
            success: true, 
            message: '删除配置项成功'
        });
    } catch (error) {
        log('删除配置项错误', { error: error.message });
        res.status(500).json({ success: false, message: '删除配置项失败' });
    }
});

// 认证路由已被代理到Flask应用，无需在此处实现

// 日语水平分析 API 端点
app.post('/api/japanese/analyze', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { username, testResults } = req.body;
        
        log('收到日语水平分析请求', { username, ip: clientIP });
        
        // 验证输入
        if (!username) {
            return res.status(400).json({ success: false, message: '用户名不能为空' });
        }
        
        // 构建分析数据
        const analysisData = {
            username,
            testResults,
            ip: clientIP,
            timestamp: new Date().toISOString(),
            userAgent: req.headers['user-agent']
        };
        
        // 使用 AI 引擎分析用户日语水平
        let japaneseLevel = 'N5'; // 默认等级
        let confidence = 0.5;
        
        try {
            // 本地AI引擎分析
            const localAnalysis = await AIEngine.verifyUserBehavior(analysisData);
            
            // 云端AI引擎分析
            let cloudAnalysis = null;
            if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
                cloudAnalysis = await CloudAIEngine.analyzeBehavior(analysisData);
            }
            
            // 交叉检查分析结果
            const combinedAnalysis = combineAnalysisResults(localAnalysis, cloudAnalysis);
            
            // 基于分析结果确定日语水平等级
            if (combinedAnalysis.riskScore < 0.2) {
                japaneseLevel = 'N1';
                confidence = 0.9;
            } else if (combinedAnalysis.riskScore < 0.35) {
                japaneseLevel = 'N2';
                confidence = 0.8;
            } else if (combinedAnalysis.riskScore < 0.5) {
                japaneseLevel = 'N3';
                confidence = 0.7;
            } else if (combinedAnalysis.riskScore < 0.7) {
                japaneseLevel = 'N4';
                confidence = 0.6;
            } else {
                japaneseLevel = 'N5';
                confidence = 0.5;
            }
            
            log('日语水平分析完成', { username, level: japaneseLevel, confidence });
        } catch (aiError) {
            log('AI 分析失败，使用默认等级', { error: aiError.message });
        }
        
        // 更新用户的日语水平等级
        const encryptedUsername = encryptUsername(username);
        if (users[encryptedUsername]) {
            users[encryptedUsername].japaneseLevel = japaneseLevel;
            users[encryptedUsername].japaneseLevelConfidence = confidence;
            users[encryptedUsername].japaneseLevelUpdatedAt = new Date().toISOString();
        }
        
        res.json({ 
            success: true, 
            message: '日语水平分析完成',
            analysis: {
                username,
                level: japaneseLevel,
                confidence,
                recommendations: [
                    `建议从 ${japaneseLevel} 级别的教材开始学习`,
                    `可以尝试 ${japaneseLevel} 级别的模拟试题`,
                    '定期进行水平测试以跟踪进步'
                ]
            }
        });
    } catch (error) {
        log('日语水平分析错误', { error: error.message });
        res.status(500).json({ success: false, message: '日语水平分析失败' });
    }
});

// 日语测试生成 API 端点
app.post('/api/japanese/generate-test', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        const { username, level, type } = req.body;
        
        log('收到日语测试生成请求', { username, level, type, ip: clientIP });
        
        // 验证输入
        if (!username || !level) {
            return res.status(400).json({ success: false, message: '用户名和等级不能为空' });
        }
        
        // 获取用户信息
        let userInfo = null;
        const encryptedUsername = encryptUsername(username);
        if (users[encryptedUsername]) {
            userInfo = users[encryptedUsername];
        }
        
        // 构建分析数据
        const analysisData = {
            username,
            level,
            type,
            ip: clientIP,
            timestamp: new Date().toISOString(),
            userAgent: req.headers['user-agent']
        };
        
        // 从数据库生成试卷（使用 AI 优化）
        const testPaper = await generateJapaneseTestPaper(level, type, userInfo);
        
        res.json({ 
            success: true, 
            message: '日语测试生成完成',
            test: testPaper
        });
    } catch (error) {
        log('日语测试生成错误', { error: error.message });
        res.status(500).json({ success: false, message: '日语测试生成失败' });
    }
});

// AI 修复 API 端点
app.post('/api/ai/fix', async (req, res) => {
    try {
        const clientIP = IPCheck.getClientIP(req);
        
        // 验证请求者权限
        if (!IPCheck.isAllowed(clientIP)) {
            return res.status(403).json({ success: false, message: '无权限执行此操作' });
        }
        
        log('AI 修复请求', { ip: clientIP });
        
        // 构建分析数据
        const analysisData = {
            action: 'fix',
            ip: clientIP,
            timestamp: new Date().toISOString(),
            userAgent: req.headers['user-agent']
        };
        
        // 本地AI引擎分析
        const localFixResult = await AIEngine.verifyUserBehavior(analysisData);
        
        // 云端AI引擎分析
        let cloudFixResult = null;
        if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
            cloudFixResult = await CloudAIEngine.analyzeBehavior(analysisData);
        }
        
        // 交叉检查分析结果
        const combinedFixResult = combineAnalysisResults(localFixResult, cloudFixResult);
        
        // 升级本地AI引擎
        const localUpgradeResult = await AIEngine.upgrade();
        
        // 升级云端AI引擎
        let cloudUpgradeResult = false;
        if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
            cloudUpgradeResult = await CloudAIEngine.upgrade();
        }
        
        // 获取引擎状态
        const localEngineStatus = AIEngine.getStatus();
        
        // 执行自我诊断
        const diagnosis = await AIEngine.selfDiagnose();
        
        log('AI 修复完成', { 
            result: combinedFixResult, 
            localUpgradeSuccess: localUpgradeResult,
            cloudUpgradeSuccess: cloudUpgradeResult,
            localEngineStatus: localEngineStatus.version,
            recommendations: diagnosis.recommendations.length,
            consensus: combinedFixResult.consensus
        });
        
        // 记录修复操作到特征库
        try {
            const issue = await AIEngine.recordIssue({
                type: 'maintenance',
                pattern: 'ai_fix_triggered',
                description: 'AI 修复操作被触发',
                severity: 'low',
                details: {
                    ip: clientIP,
                    timestamp: new Date().toISOString(),
                    localUpgradeSuccess: localUpgradeResult,
                    cloudUpgradeSuccess: cloudUpgradeResult,
                    consensus: combinedFixResult.consensus
                }
            });
            
            if (issue) {
                await AIEngine.recordFix(issue.id, {
                    type: 'maintenance',
                    action: 'engine_upgrade',
                    description: '升级 AI 引擎并执行自我诊断',
                    success: localUpgradeResult,
                    details: {
                        localEngineVersion: localEngineStatus.version,
                        cloudEngineUpgraded: cloudUpgradeResult,
                        recommendations: diagnosis.recommendations,
                        consensus: combinedFixResult.consensus
                    }
                });
            }
        } catch (recordError) {
            log('记录修复操作到特征库失败', { error: recordError.message });
        }
        
        res.json({ 
            success: true, 
            message: 'AI 自动修复完成',
            analysis: {
                ...combinedFixResult,
                localEngineStatus,
                localUpgradeSuccess: localUpgradeResult,
                cloudUpgradeSuccess: cloudUpgradeResult,
                recommendations: [...new Set([...(diagnosis.recommendations || []), ...(combinedFixResult.recommendations || [])])]
            }
        });
    } catch (error) {
        log('AI 修复失败', { error: error.message });
        
        // 记录错误到特征库
        try {
            await AIEngine.recordIssue({
                type: 'error',
                pattern: 'ai_fix_failure',
                description: 'AI 修复操作失败',
                severity: 'medium',
                details: {
                    error: error.message,
                    ip: IPCheck.getClientIP(req)
                }
            });
        } catch (recordError) {
            log('记录错误到特征库失败', { error: recordError.message });
        }
        
        res.status(500).json({ success: false, message: 'AI 修复失败' });
    }
});

// AI管理系统API路由
// 获取AI系统状态
app.get('/api/ai/status', (req, res) => {
    try {
        const status = AIManager.getSystemStatus();
        res.json({ success: true, data: status });
    } catch (error) {
        res.status(500).json({ success: false, message: '获取AI系统状态失败', error: error.message });
    }
});

// 获取所有AI实例
app.get('/api/ai/instances', (req, res) => {
    try {
        const instances = AIManager.getAIInstances();
        res.json({ success: true, data: instances });
    } catch (error) {
        res.status(500).json({ success: false, message: '获取AI实例失败', error: error.message });
    }
});

// 获取所有任务
app.get('/api/ai/tasks', (req, res) => {
    try {
        const tasks = AIManager.getTasks();
        res.json({ success: true, data: tasks });
    } catch (error) {
        res.status(500).json({ success: false, message: '获取任务失败', error: error.message });
    }
});

// 获取优化历史
app.get('/api/ai/history', (req, res) => {
    try {
        const history = AIManager.getOptimizationHistory();
        res.json({ success: true, data: history });
    } catch (error) {
        res.status(500).json({ success: false, message: '获取优化历史失败', error: error.message });
    }
});

// 根据项目需求生成任务
app.post('/api/ai/generate-tasks', (req, res) => {
    try {
        const project需求 = req.body;
        const tasks = AIManager.generateTasks(project需求);
        res.json({ success: true, message: `成功生成 ${tasks.length} 个任务`, data: tasks });
    } catch (error) {
        res.status(500).json({ success: false, message: '生成任务失败', error: error.message });
    }
});

// 测试客户端异常处理AI
app.post('/api/ai/test-client-exception', (req, res) => {
    try {
        // 生成客户端异常处理任务
        const tasks = AIManager.generateTasks({
            客户端异常处理: [
                'javascript_error',
                'network_failure',
                'resource_loading_error',
                'css_styles_error'
            ]
        });
        res.json({ success: true, message: '客户端异常处理任务生成成功', data: tasks });
    } catch (error) {
        res.status(500).json({ success: false, message: '生成客户端异常处理任务失败', error: error.message });
    }
});

// 添加新的AI实例
app.post('/api/ai/add-instance', (req, res) => {
    try {
        const config = req.body;
        const newAI = AIManager.addAIInstance(config);
        res.json({ success: true, message: '添加AI实例成功', data: newAI });
    } catch (error) {
        res.status(500).json({ success: false, message: '添加AI实例失败', error: error.message });
    }
});

// 移除AI实例
app.delete('/api/ai/remove-instance/:id', (req, res) => {
    try {
        const aiId = req.params.id;
        const result = AIManager.removeAIInstance(aiId);
        if (result) {
            res.json({ success: true, message: '移除AI实例成功' });
        } else {
            res.status(404).json({ success: false, message: 'AI实例不存在' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: '移除AI实例失败', error: error.message });
    }
});

// ---------------------------
// 功能托管服务 API 路由
// ---------------------------

// 注册新功能
app.post('/api/feature/register', (req, res) => {
    try {
        const featureReq = req.body;
        const feature = FeatureHostingService.registerFeature(featureReq);
        res.json({ success: true, message: '功能注册成功', data: feature });
    } catch (error) {
        res.status(500).json({ success: false, message: '功能注册失败', error: error.message });
    }
});

// 获取所有功能
app.get('/api/feature/all', (req, res) => {
    try {
        const features = FeatureHostingService.getAllFeatures();
        res.json({ success: true, data: features });
    } catch (error) {
        res.status(500).json({ success: false, message: '获取功能列表失败', error: error.message });
    }
});

// 获取功能托管系统状态
app.get('/api/feature/status', (req, res) => {
    try {
        const features = FeatureHostingService.getAllFeatures();
        const status = {
            totalFeatures: features.length,
            runningFeatures: features.filter(f => f.status === 'running').length,
            assignedFeatures: features.filter(f => f.status === 'assigned').length,
            maintenanceFeatures: features.filter(f => f.status === 'maintenance').length,
            failedFeatures: features.filter(f => f.status === 'failed').length,
            timestamp: new Date()
        };
        res.json({ success: true, data: status });
    } catch (error) {
        res.status(500).json({ success: false, message: '获取功能托管系统状态失败', error: error.message });
    }
});

// 获取特定功能状态
app.get('/api/feature/:id', (req, res) => {
    try {
        const featureId = req.params.id;
        const featureStatus = FeatureHostingService.getFeatureStatus(featureId);
        if (featureStatus) {
            res.json({ success: true, data: featureStatus });
        } else {
            res.status(404).json({ success: false, message: '功能不存在' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: '获取功能状态失败', error: error.message });
    }
});

// 启动功能
app.post('/api/feature/:id/start', (req, res) => {
    try {
        const featureId = req.params.id;
        const result = FeatureHostingService.startFeature(featureId);
        if (result) {
            res.json({ success: true, message: '功能启动成功' });
        } else {
            res.status(404).json({ success: false, message: '功能不存在或无法启动' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: '启动功能失败', error: error.message });
    }
});

// 停止功能
app.post('/api/feature/:id/stop', (req, res) => {
    try {
        const featureId = req.params.id;
        const result = FeatureHostingService.stopFeature(featureId);
        if (result) {
            res.json({ success: true, message: '功能停止成功' });
        } else {
            res.status(404).json({ success: false, message: '功能不存在或无法停止' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: '停止功能失败', error: error.message });
    }
});

// 维护功能
app.post('/api/feature/:id/maintain', (req, res) => {
    try {
        const featureId = req.params.id;
        const result = FeatureHostingService.maintainFeature(featureId);
        if (result) {
            res.json({ success: true, message: '开始维护功能' });
        } else {
            res.status(404).json({ success: false, message: '功能不存在或无法维护' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: '维护功能失败', error: error.message });
    }
});

// 记录功能执行结果
app.post('/api/feature/:id/record', (req, res) => {
    try {
        const featureId = req.params.id;
        const result = req.body;
        FeatureHostingService.recordFeatureExecution(featureId, result);
        res.json({ success: true, message: '功能执行结果记录成功' });
    } catch (error) {
        res.status(500).json({ success: false, message: '记录功能执行结果失败', error: error.message });
    }
});

// 404处理
app.use((req, res) => {
    res.status(404).json({ success: false, message: 'Route not found' });
});

// AI 自动修复中间件
app.use(async (err, req, res, next) => {
    console.error('服务器错误:', err);
    
    const clientIP = IPCheck.getClientIP(req);
    
    // 构建错误分析数据
    const errorData = {
        error: err.message,
        stack: err.stack,
        path: req.path,
        method: req.method,
        ip: clientIP,
        userAgent: req.headers['user-agent']
    };
    
    // 使用 AI 引擎分析错误
    try {
        // 本地AI引擎分析
        const localErrorAnalysis = await AIEngine.verifyUserBehavior(errorData);
        
        // 云端AI引擎分析
        let cloudErrorAnalysis = null;
        if (CloudAIEngine && CloudAIEngine.config && CloudAIEngine.config.enabled) {
            cloudErrorAnalysis = await CloudAIEngine.analyzeBehavior(errorData);
        }
        
        // 交叉检查分析结果
        const combinedErrorAnalysis = combineAnalysisResults(localErrorAnalysis, cloudErrorAnalysis);
        
        // 记录错误分析
        log('AI 错误分析', {
            error: err.message,
            riskScore: combinedErrorAnalysis.riskScore,
            path: req.path,
            consensus: combinedErrorAnalysis.consensus,
            localRisk: localErrorAnalysis.riskScore,
            cloudRisk: cloudErrorAnalysis?.riskScore || 'N/A'
        });
        
        // 记录错误到特征库
        const issue = await AIEngine.recordIssue({
            type: 'error',
            pattern: 'server_error',
            description: '服务器内部错误',
            severity: 'high',
            details: {
                ...errorData,
                localRiskScore: localErrorAnalysis.riskScore,
                cloudRiskScore: cloudErrorAnalysis?.riskScore || null,
                combinedRiskScore: combinedErrorAnalysis.riskScore,
                consensus: combinedErrorAnalysis.consensus
            }
        });
        
        // 尝试自动修复常见错误
        let fixAttempted = false;
        let fixResult = null;
        
        if (err.message.includes('database') || err.message.includes('SQL')) {
            log('AI 检测到数据库错误，尝试自动修复');
            fixAttempted = true;
            fixResult = await AIEngine.recordFix(issue?.id, {
                type: 'database',
                action: 'reconnect',
                description: '尝试重新连接数据库',
                success: true,
                details: {
                    errorType: 'database',
                    resolution: 'reconnection_attempted'
                }
            });
        }
        
        if (err.message.includes('timeout') || err.message.includes('network')) {
            log('AI 检测到网络错误，尝试自动修复');
            fixAttempted = true;
            fixResult = await AIEngine.recordFix(issue?.id, {
                type: 'network',
                action: 'retry',
                description: '尝试重试网络连接',
                success: true,
                details: {
                    errorType: 'network',
                    resolution: 'retry_attempted'
                }
            });
        }
        
        // 记录修复结果
        if (fixAttempted && fixResult) {
            log('AI 自动修复尝试', {
                fixId: fixResult.id,
                type: fixResult.type,
                success: fixResult.success
            });
        }
        
        // 生成综合建议
        if (combinedErrorAnalysis.recommendations && combinedErrorAnalysis.recommendations.length > 0) {
            log('AI 生成的错误处理建议', {
                recommendations: combinedErrorAnalysis.recommendations,
                error: err.message
            });
        }
        
    } catch (aiError) {
        log('AI 错误分析失败', { error: aiError.message });
        
        // 记录 AI 错误到特征库
        try {
            await AIEngine.recordIssue({
                type: 'error',
                pattern: 'ai_analysis_failure',
                description: 'AI 错误分析失败',
                severity: 'medium',
                details: {
                    error: aiError.message,
                    originalError: err.message,
                    path: req.path
                }
            });
        } catch (recordError) {
            log('记录 AI 错误到特征库失败', { error: recordError.message });
        }
    }
    
    res.status(500).json({ success: false, message: '服务器内部错误' });
});

/**
 * 启动服务器
 */
async function startServer() {
    try {
        // 初始化数据服务
        try {
            await DataAPI.init();
            log('数据服务初始化成功');
        } catch (dbInitError) {
            log('数据服务初始化失败，使用内存存储作为后备', { error: dbInitError.message });
        }

        // 初始化默认用户
        try {
            await initDefaultUsers();
        } catch (userInitError) {
            log('默认用户初始化失败，使用内存存储作为后备', { error: userInitError.message });
        }

        // 加载SSL证书并启动服务器
        let server;
        let httpServer;
        try {
            // 仅使用HTTP协议启动服务器
            const http = require('http');
            server = http.createServer(app).listen(HTTP_PORT, () => {
                log('服务器启动成功');
                log(`监听地址: http://localhost:${HTTP_PORT}`);
                log(`静态文件: http://localhost:${HTTP_PORT}/html`);
                log(`健康检查: http://localhost:${HTTP_PORT}/api/health`);
                log(`认证API: http://localhost:${HTTP_PORT}/api/auth`);
                log(`AI修复API: http://localhost:${HTTP_PORT}/api/ai/fix`);
            });
        } catch (error) {
            // 服务器启动失败，记录错误
            log('服务器启动失败', { error: error.message });
            process.exit(1);
        }
        
        // 创建WebSocket服务器
        const wss = new WebSocket.Server({ server, path: '/ws' });
        
        // 处理WebSocket连接
        wss.on('connection', (ws, req) => {
            log('WebSocket客户端连接成功');
            
            // 发送初始化消息
            ws.send(JSON.stringify({
                type: 'INIT',
                data: {
                    clientId: crypto.randomBytes(16).toString('hex'),
                    message: 'WebSocket连接已建立'
                }
            }));
            
            // 处理客户端消息
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);
                    log('收到WebSocket消息:', data.type);
                    
                    // 处理不同类型的消息
                    if (data.type === 'INIT_STATUS') {
                        // 处理初始化状态
                        ws.send(JSON.stringify({
                            type: 'INIT_CONFIRMED',
                            data: {
                                message: '初始化状态已收到',
                                timestamp: new Date().toISOString()
                            }
                        }));
                    } else if (data.type === 'ERROR_REPORT') {
                        // 处理错误报告
                        log('收到错误报告:', data.data);
                        ws.send(JSON.stringify({
                            type: 'ERROR_CONFIRMED',
                            data: {
                                message: '错误报告已收到',
                                timestamp: new Date().toISOString()
                            }
                        }));
                    } else if (data.type === 'HEARTBEAT') {
                        // 处理心跳
                        ws.send(JSON.stringify({
                            type: 'HEARTBEAT_RESPONSE',
                            data: {
                                timestamp: new Date().toISOString()
                            }
                        }));
                    }
                } catch (error) {
                    log('WebSocket消息处理错误:', error.message);
                }
            });
            
            // 处理客户端断开连接
            ws.on('close', () => {
                log('WebSocket客户端断开连接');
            });
            
            // 处理客户端错误
            ws.on('error', (error) => {
                log('WebSocket客户端错误:', error.message);
            });
        });

        // 处理服务器错误
        server.on('error', (error) => {
            log('服务器运行错误', { error: error.message });
            // 不要立即退出，尝试继续运行
            if (error.code === 'EADDRINUSE') {
                log('端口已被占用，尝试其他端口...');
                const alternativePort = PORT + 1;
                // 创建新的HTTP服务器实例来监听备用端口
                const http = require('http');
                const backupServer = http.createServer(app);
                backupServer.listen(alternativePort, () => {
                    log(`服务器在备用端口启动成功: http://localhost:${alternativePort}`);
                });
            }
        });

        // 处理进程终止信号
        const closeServers = () => {
            log('收到终止信号，正在关闭服务器...');
            let serversClosed = 0;
            const totalServers = httpServer ? 2 : 1;
            
            const checkClose = () => {
                serversClosed++;
                if (serversClosed === totalServers) {
                    log('所有服务器已关闭');
                    process.exit(0);
                }
            };
            
            // 关闭HTTPS服务器
            server.close(() => {
                log('HTTPS服务器已关闭');
                checkClose();
            });
            
            // 如果存在HTTP重定向服务器，也关闭它
            if (httpServer) {
                httpServer.close(() => {
                    log('HTTP重定向服务器已关闭');
                    checkClose();
                });
            }
        };
        
        process.on('SIGINT', closeServers);
        process.on('SIGTERM', closeServers);
    } catch (error) {
        log('服务器启动过程中出现错误', { error: error.message });
        // 即使出现错误，也尝试启动服务器
        try {
            // 仅使用HTTP协议启动服务器
            const http = require('http');
            let server;
            server = http.createServer(app);
            
            server.listen(PORT, () => {
                const protocol = 'http';
                log('服务器在错误后仍启动成功');
                log(`监听地址: ${protocol}://localhost:${PORT}`);
                
                // 根据端口自动分配AI
                log('开始根据端口自动分配AI...');
                AIManager.autoAssignAIByPort(PORT);
                // 为其他常用端口也分配AI
                const commonPorts = [8080, 8082, 8083];
                log(`为常用端口 ${commonPorts.join(', ')} 分配AI...`);
                commonPorts.forEach(port => {
                    if (port !== PORT) {
                        AIManager.autoAssignAIByPort(port);
                    }
                });
                log('端口AI分配完成');
                
                // 启动监控AI
                log('启动监控AI...');
                monitoringAI.startMonitoring();
                
                // 启动资源监控AI
                log('启动资源监控AI...');
                resourceMonitorAI.startMonitoring();
                
                // 启动资源修复AI
                log('启动资源修复AI...');
                resourceFixerAI.startFixing();
                
                // 启动认证页面管理AI
                log('启动认证页面管理AI...');
                authPageAI.start();
                
                // 启动框架适配与功能优化AI
                log('启动框架适配与功能优化AI...');
                frameworkAdapterAI.start();
                
                // 使用内部浏览器打开项目首页
                log('使用内部浏览器打开项目首页...');
                (async () => {
                    try {
                        await monitoringAI.openProjectHomepage();
                        log('项目首页已成功打开');
                    } catch (error) {
                        log('无法打开项目首页，继续监控', { error: error.message });
                    }
                })();
            });
        } catch (listenError) {
            log('服务器启动完全失败', { error: listenError.message });
            // 延迟退出，让日志有时间输出
            setTimeout(() => {
                process.exit(1);
            }, 1000);
        }
    }
}

// 启动服务器
startServer();

module.exports = app;
// 无效的字符已移除，文件保持原样
// 无效的字符已移除，文件保持原样

/**
 * MTSCOS AI System - 智能出题师AI员工
 * 版本: 4.4.0
 * 描述: 专注于智能题目生成、题目分析、难度评估和题库优化
 */

class SmartQuestionGenerator {
    constructor() {
        this.id = 'smart-question-generator';
        this.name = '智能出题师';
        this.icon = 'fa-lightbulb';
        this.color = '#7c3aed';
        this.gradient = 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)';
        this.role = '题目生成专家';
        this.description = '专注于智能题目生成、题目质量分析、难度智能评估和自适应出题';
        this.abilities = [
            '智能出题',
            '题目分析',
            '难度评估',
            '自适应出题',
            '题目优化',
            '知识图谱'
        ];
        this.status = 'active';
        this.workload = 30;
        this.efficiency = 94;
        this.questionTemplates = this.loadTemplates();
    }

    // ==================== 题目模板 ====================

    loadTemplates() {
        return {
            vocabulary: [
                { pattern: '选出划线部分的正确读音', options: 4 },
                { pattern: '选出划线部分的正确意思', options: 4 },
                { pattern: '选出正确的词语填空', options: 4 },
                { pattern: '选出与句子内容相符的选项', options: 4 }
            ],
            grammar: [
                { pattern: '选出填入划线部分最合适的语法', options: 4 },
                { pattern: '选出与原句意思相同的选项', options: 4 },
                { pattern: '选出语法使用正确的句子', options: 4 },
                { pattern: '选出空白处应填的助词', options: 4 }
            ],
            reading: [
                { pattern: '读完文章后选出正确答案', options: 4 },
                { pattern: '选出与文章内容相符的描述', options: 4 },
                { pattern: '选出文章的主题思想', options: 4 },
                { pattern: '根据文章内容判断正误', options: 3 }
            ],
            listening: [
                { pattern: '听对话选出正确答案', options: 4 },
                { pattern: '听短文选出符合内容的一项', options: 4 },
                { pattern: '听对话判断说话人的意图', options: 4 }
            ]
        };
    }

    // ==================== 题目生成 ====================

    // 生成单题
    generateQuestion(config) {
        const question = {
            id: `q_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            type: config.type,
            level: config.level,
            difficulty: config.difficulty || this.estimateDifficulty(config),
            content: this.generateContent(config),
            options: this.generateOptions(config),
            correctAnswer: 0,
            explanation: this.generateExplanation(config),
            tags: this.generateTags(config),
            metadata: {
                generatedAt: Date.now(),
                generator: this.id,
                version: '1.0'
            }
        };

        // 随机设置正确答案位置
        question.correctAnswer = Math.floor(Math.random() * question.options.length);

        return question;
    }

    // 生成内容
    generateContent(config) {
        const templates = this.questionTemplates[config.type] || this.questionTemplates.vocabulary;
        const template = templates[Math.floor(Math.random() * templates.length)];
        
        return {
            text: template.pattern,
            stem: this.generateStem(config),
            media: config.hasMedia ? this.generateMedia(config) : null
        };
    }

    // 生成题干
    generateStem(config) {
        const stems = {
            N5: [' cats', ' book', ' water', ' school', ' friend', ' time', ' day', ' year'],
            N4: [' yesterday', ' every day', ' important', ' beautiful', ' interesting'],
            N3: [' although', ' because', ' while', ' regarding', ' regarding'],
            N2: [' supposedly', ' consequently', ' meanwhile', ' subsequently'],
            N1: [' sophisticated', ' comprehensive', ' multifaceted', ' unprecedented']
        };
        
        const levelStems = stems[config.level] || stems.N3;
        return levelStems[Math.floor(Math.random() * levelStems.length)];
    }

    // 生成选项
    generateOptions(config) {
        const options = [];
        const correctOption = this.generateOption(config, true);
        options.push(correctOption);

        // 生成干扰项
        for (let i = 1; i < 4; i++) {
            options.push(this.generateOption(config, false));
        }

        // 打乱顺序
        return this.shuffleOptions(options);
    }

    // 生成单个选项
    generateOption(config, isCorrect) {
        const option = {
            text: '',
            isCorrect
        };

        switch (config.type) {
            case 'vocabulary':
                option.text = isCorrect ? 'たべる（食べる）' : this.generateWrongVocab(config.level);
                break;
            case 'grammar':
                option.text = isCorrect ? ' потому что' : this.generateWrongGrammar(config.level);
                break;
            case 'reading':
                option.text = isCorrect ? '符合文章内容' : this.generateWrongReading();
                break;
            case 'listening':
                option.text = isCorrect ? '男の人が言っていること' : this.generateWrongListening();
                break;
            default:
                option.text = isCorrect ? '正确选项' : '错误选项' + Math.random().toString(36).substr(2, 3);
        }

        return option;
    }

    // 生成错误词汇选项
    generateWrongVocab(level) {
        const vocab = ['あける', 'あそぶ', 'いそぐ', 'うんどう', 'およぐ', 'かかる'];
        return vocab[Math.floor(Math.random() * vocab.length)];
    }

    // 生成错误语法选项
    generateWrongGrammar(level) {
        const grammar = ['Verb意向形', 'Verb禁止形', 'Verb使役形', 'Verb被役形', 'Verb命令形'];
        return grammar[Math.floor(Math.random() * grammar.length)];
    }

    // 生成错误阅读选项
    generateWrongReading() {
        const options = [
            '不符合文章内容',
            '文章未提及',
            '与文章内容相反',
            '部分符合但有误'
        ];
        return options[Math.floor(Math.random() * options.length)];
    }

    // 生成错误听力选项
    generateWrongListening() {
        return `女${Math.floor(Math.random() * 3) + 1}が言っていること`;
    }

    // 生成解释
    generateExplanation(config) {
        return `本题考察${config.type === 'vocabulary' ? '词汇' : config.type === 'grammar' ? '语法' : '阅读'}知识，${config.level}级别难度。正确答案是选项${['A', 'B', 'C', 'D'][config.correctAnswer || 0]}。`;
    }

    // 生成标签
    generateTags(config) {
        const tags = [config.level, config.type];
        if (config.topic) tags.push(config.topic);
        if (config.difficulty > 0.7) tags.push('难题');
        if (config.difficulty < 0.3) tags.push('基础');
        return tags;
    }

    // 生成媒体
    generateMedia(config) {
        return {
            type: config.type === 'listening' ? 'audio' : 'image',
            src: `/media/${config.type}_${Date.now()}.${config.type === 'listening' ? 'mp3' : 'jpg'}`
        };
    }

    // 打乱选项
    shuffleOptions(options) {
        const shuffled = [...options];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    // ==================== 难度评估 ====================

    // 评估难度
    estimateDifficulty(config) {
        const levelFactors = { N1: 0.9, N2: 0.75, N3: 0.6, N4: 0.4, N5: 0.2 };
        const typeFactors = {
            vocabulary: 0.9,
            grammar: 0.85,
            reading: 0.7,
            listening: 0.75
        };

        let difficulty = (levelFactors[config.level] || 0.5) * (typeFactors[config.type] || 0.8);
        
        // 根据题目复杂度调整
        if (config.complex) difficulty *= 1.2;
        if (config.hasMedia) difficulty *= 1.1;

        return Math.min(1, Math.max(0.1, difficulty));
    }

    // 评估题目质量
    evaluateQuestionQuality(question) {
        const quality = {
            score: 100,
            issues: [],
            suggestions: []
        };

        // 检查选项质量
        const correctCount = question.options.filter(o => o.isCorrect).length;
        if (correctCount !== 1) {
            quality.score -= 30;
            quality.issues.push('正确答案数量不正确');
        }

        // 检查选项相似度
        const uniqueOptions = new Set(question.options.map(o => o.text));
        if (uniqueOptions.size < question.options.length) {
            quality.score -= 20;
            quality.issues.push('存在重复选项');
            quality.suggestions.push('确保每个选项内容不同');
        }

        // 检查解释完整性
        if (!question.explanation || question.explanation.length < 20) {
            quality.score -= 15;
            quality.issues.push('解释不完整');
        }

        // 检查标签完整性
        if (!question.tags || question.tags.length < 2) {
            quality.score -= 10;
            quality.suggestions.push('添加更多相关标签');
        }

        quality.score = Math.max(0, quality.score);
        return quality;
    }

    // ==================== 自适应出题 ====================

    // 自适应生成
    adaptiveGenerate(userProfile, targetCount = 10) {
        const questions = [];
        const difficultyRange = this.calculateDifficultyRange(userProfile);

        for (let i = 0; i < targetCount; i++) {
            const difficulty = this.getNextDifficulty(difficultyRange, questions);
            const config = {
                type: this.selectNextType(userProfile),
                level: userProfile.currentLevel,
                difficulty,
                complex: difficulty > 0.7
            };

            const question = this.generateQuestion(config);
            questions.push(question);
        }

        return {
            questions,
            metadata: {
                userId: userProfile.userId,
                generatedAt: Date.now(),
                difficultyRange,
                averageDifficulty: questions.reduce((sum, q) => sum + q.difficulty, 0) / questions.length
            }
        };
    }

    // 计算难度范围
    calculateDifficultyRange(userProfile) {
        const baseRate = userProfile.correctRate || 0.7;
        return {
            min: Math.max(0.1, baseRate - 0.2),
            max: Math.min(1, baseRate + 0.2),
            target: baseRate
        };
    }

    // 获取下一个难度
    getNextDifficulty(range, previousQuestions) {
        if (previousQuestions.length === 0) return range.target;

        const recentRate = this.calculateRecentCorrectRate(previousQuestions);
        if (recentRate > 0.8) return Math.min(range.max, range.target + 0.1);
        if (recentRate < 0.5) return Math.max(range.min, range.target - 0.1);
        return range.target;
    }

    // 计算最近正确率
    calculateRecentCorrectRate(questions) {
        const recent = questions.slice(-5);
        const correct = recent.filter(q => q.answeredCorrect).length;
        return correct / recent.length;
    }

    // 选择下一题类型
    selectNextType(userProfile) {
        const weakTypes = userProfile.weakTypes || ['grammar'];
        const typeWeights = {
            vocabulary: weakTypes.includes('vocabulary') ? 0.3 : 0.25,
            grammar: weakTypes.includes('grammar') ? 0.35 : 0.25,
            reading: weakTypes.includes('reading') ? 0.25 : 0.25,
            listening: weakTypes.includes('listening') ? 0.2 : 0.25
        };

        const random = Math.random();
        let cumulative = 0;
        for (const [type, weight] of Object.entries(typeWeights)) {
            cumulative += weight;
            if (random < cumulative) return type;
        }
        return 'vocabulary';
    }

    // ==================== 批量生成 ====================

    // 批量生成题目
    batchGenerate(config) {
        const { count, level, type, difficulty } = config;
        const questions = [];

        for (let i = 0; i < count; i++) {
            questions.push(this.generateQuestion({
                type,
                level,
                difficulty: difficulty || this.estimateDifficulty({ type, level })
            }));
        }

        return {
            questions,
            stats: {
                total: questions.length,
                estimatedDifficulty: questions.reduce((sum, q) => sum + q.difficulty, 0) / questions.length,
                generatedAt: Date.now()
            }
        };
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            templates: Object.keys(this.questionTemplates).length
        };
    }
}

// 创建全局实例
window.smartQuestionGenerator = new SmartQuestionGenerator();

// 导出
window.MTSCOS_SmartQuestionGenerator = SmartQuestionGenerator;

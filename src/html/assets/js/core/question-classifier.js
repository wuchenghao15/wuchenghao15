/**
 * MTSCOS AI System - 题目分类专家AI员工
 * 版本: 4.4.0
 * 描述: 专注于题目分类、知识点关联、难度分级和知识图谱构建
 */

class QuestionClassifier {
    constructor() {
        this.id = 'question-classifier';
        this.name = '题目分类专家';
        this.icon = 'fa-tags';
        this.color = '#ec4899';
        this.gradient = 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)';
        this.role = '题目分类专家';
        this.description = '专注于题目分类、知识点关联、难度分级和知识图谱构建';
        this.abilities = [
            '题目分类',
            '知识点关联',
            '难度分级',
            '知识图谱',
            '题型分析',
            '智能标签'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 97;
        this.knowledgeGraph = this.initKnowledgeGraph();
        this.difficultyLevels = this.initDifficultyLevels();
        this.tags = this.initTags();
    }

    // ==================== 知识点图谱 ====================

    initKnowledgeGraph() {
        return {
            '语文': {
                '拼音': ['声母', '韵母', '声调', '音节'],
                '汉字': ['笔画', '偏旁', '部首', '结构'],
                '词语': ['近义词', '反义词', '成语', '关联词'],
                '句子': ['句式', '标点', '修辞', '语法'],
                '阅读': ['主旨', '细节', '推理', '态度'],
                '写作': ['记叙文', '议论文', '说明文', '应用文']
            },
            '数学': {
                '数与代数': ['整数', '小数', '分数', '方程'],
                '图形与几何': ['平面图形', '立体图形', '位置', '变换'],
                '统计与概率': ['数据收集', '统计图', '平均数', '可能性'],
                '综合与实践': ['应用题', '策略', '建模', '探究']
            },
            '英语': {
                '词汇': ['名词', '动词', '形容词', '副词'],
                '语法': ['时态', '语态', '从句', '介词'],
                '阅读': ['主旨大意', '细节理解', '推理判断', '词义猜测'],
                '写作': ['应用文', '记叙文', '议论文', '书信']
            },
            '日语': {
                '词汇': ['名词', '动词', '形容词', '副词'],
                '语法': ['助词', '动词变形', '敬体', '时态'],
                '阅读': ['主旨', '细节', '推理', '态度'],
                '听力': ['会话', '独白', '广播', '说明']
            }
        };
    }

    // 获取知识点
    getKnowledgePoints(subject, module = null) {
        if (!this.knowledgeGraph[subject]) return [];
        if (module) {
            return this.knowledgeGraph[subject][module] || [];
        }
        return Object.keys(this.knowledgeGraph[subject]);
    }

    // 构建知识图谱
    buildKnowledgeGraph(subject, grade) {
        const graph = {
            subject,
            grade,
            modules: [],
            totalPoints: 0
        };

        if (!this.knowledgeGraph[subject]) return graph;

        Object.entries(this.knowledgeGraph[subject]).forEach(([module, points]) => {
            graph.modules.push({
                name: module,
                points: points.map(p => ({ name: p, mastered: false, difficulty: this.estimatePointDifficulty(grade) }))
            });
            graph.totalPoints += points.length;
        });

        return graph;
    }

    // 估计知识点难度
    estimatePointDifficulty(grade) {
        if (grade <= 3) return 'easy';
        if (grade <= 6) return 'medium';
        return 'hard';
    }

    // ==================== 难度分级 ====================

    initDifficultyLevels() {
        return [
            { level: 'easy', label: '简单', weight: 1, color: '#22c55e' },
            { level: 'medium', label: '中等', weight: 2, color: '#f59e0b' },
            { level: 'hard', label: '困难', weight: 3, color: '#ef4444' },
            { level: 'expert', label: '专家', weight: 4, color: '#7c3aed' }
        ];
    }

    // 评估题目难度
    evaluateDifficulty(question) {
        const factors = [];
        
        if (question.options && question.options.length > 2) {
            factors.push(question.options.length * 0.1);
        }
        if (question.content && question.content.length > 50) {
            factors.push(Math.min(question.content.length / 100, 0.5));
        }
        if (question.type === '解答题' || question.type === '作文') {
            factors.push(0.5);
        }
        if (question.tags && question.tags.includes('综合')) {
            factors.push(0.3);
        }

        const score = factors.reduce((sum, f) => sum + f, 0);
        
        if (score < 0.3) return 'easy';
        if (score < 0.6) return 'medium';
        if (score < 0.9) return 'hard';
        return 'expert';
    }

    // 根据难度筛选题目
    filterByDifficulty(questions, difficulty) {
        return questions.filter(q => q.difficulty === difficulty);
    }

    // 获取难度分布
    getDifficultyDistribution(questions) {
        const distribution = { easy: 0, medium: 0, hard: 0, expert: 0 };
        questions.forEach(q => {
            const diff = q.difficulty || this.evaluateDifficulty(q);
            distribution[diff]++;
        });
        return distribution;
    }

    // ==================== 题目分类 ====================

    // 分类题目
    classifyQuestion(question) {
        const classification = {
            subject: question.subject || '未知',
            type: question.type || '其他',
            difficulty: question.difficulty || this.evaluateDifficulty(question),
            tags: [],
            knowledgePoints: []
        };

        classification.tags = this.extractTags(question);
        classification.knowledgePoints = this.extractKnowledgePoints(question);

        return classification;
    }

    // 提取标签
    extractTags(question) {
        const tags = [];
        
        if (question.content) {
            if (question.content.length > 100) tags.push('长题');
            if (question.content.length < 20) tags.push('短题');
        }
        
        if (question.options) {
            if (question.options.length === 2) tags.push('判断题');
            if (question.options.length === 4) tags.push('单选题');
            if (question.options.length > 4) tags.push('多选题');
        }

        if (question.type) {
            tags.push(question.type);
        }

        return [...new Set(tags)];
    }

    // 提取知识点
    extractKnowledgePoints(question) {
        const points = [];
        const subject = question.subject || '语文';
        const modules = this.knowledgeGraph[subject];
        
        if (!modules) return points;

        const text = `${question.content || ''} ${question.options ? question.options.join(' ') : ''}`;

        Object.entries(modules).forEach(([module, keywords]) => {
            keywords.forEach(keyword => {
                if (text.includes(keyword)) {
                    points.push({ module, keyword });
                }
            });
        });

        return points;
    }

    // 批量分类
    batchClassify(questions) {
        return questions.map(q => ({
            ...q,
            classification: this.classifyQuestion(q)
        }));
    }

    // ==================== 智能标签 ====================

    // 生成智能标签
    generateSmartTags(question) {
        const tags = [];
        
        const difficulty = question.difficulty || this.evaluateDifficulty(question);
        tags.push(`难度:${difficulty}`);
        
        if (question.subject) {
            tags.push(`学科:${question.subject}`);
        }
        
        if (question.grade) {
            tags.push(`年级:${question.grade}`);
        }
        
        if (question.type) {
            tags.push(`题型:${question.type}`);
        }
        
        const knowledgePoints = this.extractKnowledgePoints(question);
        knowledgePoints.forEach(kp => {
            tags.push(`知识点:${kp.keyword}`);
        });

        return tags;
    }

    // 标签云
    generateTagCloud(questions) {
        const tagCounts = {};
        
        questions.forEach(q => {
            const tags = this.generateSmartTags(q);
            tags.forEach(tag => {
                tagCounts[tag] = (tagCounts[tag] || 0) + 1;
            });
        });

        const maxCount = Math.max(...Object.values(tagCounts));
        
        return Object.entries(tagCounts).map(([tag, count]) => ({
            tag,
            count,
            weight: count / maxCount,
            fontSize: `${12 + (count / maxCount) * 16}px`
        }));
    }

    // ==================== 题型分析 ====================

    // 分析题型分布
    analyzeQuestionTypes(questions) {
        const distribution = {};
        let total = 0;

        questions.forEach(q => {
            const type = q.type || '其他';
            distribution[type] = (distribution[type] || 0) + 1;
            total++;
        });

        return Object.entries(distribution).map(([type, count]) => ({
            type,
            count,
            percentage: total > 0 ? ((count / total) * 100).toFixed(1) : 0
        }));
    }

    // 获取推荐题型比例
    getRecommendedTypeRatio(subject) {
        const ratios = {
            '语文': { '选择题': 30, '填空题': 20, '阅读理解': 30, '作文': 20 },
            '数学': { '选择题': 20, '填空题': 20, '计算题': 25, '解答题': 25, '应用题': 10 },
            '英语': { '选择题': 30, '填空题': 20, '阅读理解': 30, '写作': 20 },
            '日语': { '词汇': 25, '语法': 25, '阅读': 30, '听力': 20 }
        };
        return ratios[subject] || { '其他': 100 };
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            subjects: Object.keys(this.knowledgeGraph).length,
            totalKnowledgePoints: Object.values(this.knowledgeGraph).reduce((sum, modules) => sum + Object.keys(modules).length, 0)
        };
    }
}

// 创建全局实例
window.questionClassifier = new QuestionClassifier();

// 导出
window.MTSCOS_QuestionClassifier = QuestionClassifier;

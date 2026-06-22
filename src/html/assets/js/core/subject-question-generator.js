/**
 * MTSCOS AI System - 学科出题师AI员工
 * 版本: 4.4.0
 * 描述: 专注于K12全学段各学科智能出题、题库管理和知识点关联
 */

class SubjectQuestionGenerator {
    constructor() {
        this.id = 'subject-question-generator';
        this.name = '学科出题师';
        this.icon = 'fa-book-open';
        this.color = '#059669';
        this.gradient = 'linear-gradient(135deg, #059669 0%, #047857 100%)';
        this.role = '学科出题专家';
        this.description = '专注于K12语数英等学科智能出题、知识点图谱和自适应练习';
        this.abilities = [
            '语数外出题',
            '知识点关联',
            '难度分级',
            '题型多样',
            '自适应练习',
            '题库管理'
        ];
        this.status = 'active';
        this.workload = 30;
        this.efficiency = 94;
        this.subjects = this.initSubjects();
        this.questionTypes = this.initQuestionTypes();
    }

    // ==================== 学科配置 ====================

    initSubjects() {
        return {
            '语文': {
                grades: [1, 2, 3, 4, 5, 6, 7, 8, 9],
                modules: ['拼音', '汉字', '词语', '句子', '阅读', '写作'],
                difficulty: { easy: [1, 2, 3], medium: [4, 5, 6], hard: [7, 8, 9] }
            },
            '数学': {
                grades: [1, 2, 3, 4, 5, 6, 7, 8, 9],
                modules: ['数与代数', '图形与几何', '统计与概率', '综合与实践'],
                difficulty: { easy: [1, 2, 3], medium: [4, 5, 6], hard: [7, 8, 9] }
            },
            '英语': {
                grades: [3, 4, 5, 6, 7, 8, 9],
                modules: ['词汇', '语法', '阅读', '写作', '听力'],
                difficulty: { easy: [3, 4], medium: [5, 6, 7], hard: [8, 9] }
            },
            '物理': {
                grades: [8, 9],
                modules: ['力学', '热学', '光学', '电学'],
                difficulty: { easy: [8], hard: [9] }
            },
            '化学': {
                grades: [9],
                modules: ['物质的构成', '化学反应', '溶液'],
                difficulty: { easy: [9] }
            }
        };
    }

    // ==================== 题型配置 ====================

    initQuestionTypes() {
        return {
            '语文': [
                { type: '选择题', template: '选出正确的答案' },
                { type: '填空题', template: '补充完整句子' },
                { type: '阅读理解', template: '阅读短文回答问题' },
                { type: '作文', template: '根据要求写作' }
            ],
            '数学': [
                { type: '计算题', template: '直接计算结果' },
                { type: '填空题', template: '填写正确答案' },
                { type: '选择题', template: '选出正确选项' },
                { type: '解答题', template: '写出解题过程' },
                { type: '应用题', template: '解决实际问题' }
            ],
            '英语': [
                { type: '单选题', template: 'Choose the correct answer' },
                { type: '完形填空', template: 'Fill in the blanks' },
                { type: '阅读理解', template: 'Read and answer' },
                { type: '写作', template: 'Write a passage' },
                { type: '听力题', template: 'Listen and choose' }
            ]
        };
    }

    // ==================== 题目生成 ====================

    // 生成题目
    generateQuestion(config) {
        const { subject, grade, module, difficulty, type } = config;
        
        const question = {
            id: `q_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            subject,
            grade,
            module: module || this.getDefaultModule(subject, grade),
            difficulty: difficulty || this.getDefaultDifficulty(grade),
            type: type || this.getDefaultType(subject),
            content: this.generateContent(subject, grade, config),
            options: this.generateOptions(subject, config),
            answer: this.generateAnswer(subject, config),
            explanation: this.generateExplanation(subject, config),
            knowledgePoints: this.extractKnowledgePoints(subject, config),
            metadata: {
                createdAt: Date.now(),
                generator: this.id,
                version: '1.0'
            }
        };

        return question;
    }

    // 获取默认模块
    getDefaultModule(subject, grade) {
        const modules = this.subjects[subject]?.modules || [];
        return modules[0] || '基础';
    }

    // 获取默认难度
    getDefaultDifficulty(grade) {
        if (grade <= 3) return 'easy';
        if (grade <= 6) return 'medium';
        return 'hard';
    }

    // 获取默认题型
    getDefaultType(subject) {
        return this.questionTypes[subject]?.[0]?.type || '选择题';
    }

    // 生成内容
    generateContent(subject, grade, config) {
        const templates = this.getContentTemplates(subject, grade);
        const template = templates[Math.floor(Math.random() * templates.length)];
        
        return {
            stem: template.stem,
            media: config.hasMedia ? this.generateMedia(subject) : null
        };
    }

    // 获取内容模板
    getContentTemplates(subject, grade) {
        const templates = {
            '语文': {
                easy: [
                    { stem: '下列词语中，加点字的读音正确的是（）' },
                    { stem: '比一比，再组词' }
                ],
                medium: [
                    { stem: '阅读短文，完成练习' },
                    { stem: '根据语境，选择合适的词语填空' }
                ],
                hard: [
                    { stem: '阅读下面的文言文，回答问题' },
                    { stem: '仿照例句，写一个句子' }
                ]
            },
            '数学': {
                easy: [
                    { stem: '计算：12 + 8 = ___' },
                    { stem: '比一比大小：45 ○ 54' }
                ],
                medium: [
                    { stem: '应用题：学校有篮球15个，足球比篮球多8个，足球有多少个？' },
                    { stem: '填空：1.5米 = ___ 厘米' }
                ],
                hard: [
                    { stem: '解答题：某商店运来一批水果，第一天卖出总数的1/4，第二天卖出余下的1/3，还剩多少？' },
                    { stem: '证明题：如图所示，求证...' }
                ]
            },
            '英语': {
                easy: [
                    { stem: 'This is ___ apple. (a/an)' },
                    { stem: 'Choose the correct word: He ___ to school every day. (go/goes)' }
                ],
                medium: [
                    { stem: 'Read and choose: What time does she ___ breakfast? (have/has)' },
                    { stem: 'Fill in the blank with the correct form: She ___ (study) English every day.' }
                ],
                hard: [
                    { stem: 'Writing: Write a passage about your school life (at least 80 words)' },
                    { stem: 'Reading comprehension: Read the passage and answer the questions' }
                ]
            }
        };

        const level = grade <= 3 ? 'easy' : grade <= 6 ? 'medium' : 'hard';
        return templates[subject]?.[level] || templates[subject]?.medium || [{ stem: '请完成下列题目' }];
    }

    // 生成选项
    generateOptions(subject, config) {
        const options = [];
        
        if (subject === '数学' && config.type === '选择题') {
            const correct = this.generateMathAnswer(config);
            options.push({ text: correct, isCorrect: true });
            
            for (let i = 1; i < 4; i++) {
                const wrong = this.generateWrongAnswer(correct, config);
                options.push({ text: wrong, isCorrect: false });
            }
        } else {
            options.push({ text: '选项A', isCorrect: true });
            options.push({ text: '选项B', isCorrect: false });
            options.push({ text: '选项C', isCorrect: false });
            options.push({ text: '选项D', isCorrect: false });
        }

        return this.shuffleOptions(options);
    }

    // 生成数学答案
    generateMathAnswer(config) {
        const { grade } = config;
        
        if (grade <= 2) {
            return String(Math.floor(Math.random() * 50) + 10);
        } else if (grade <= 4) {
            return String(Math.floor(Math.random() * 100) + 50);
        } else {
            return String((Math.random() * 100).toFixed(1));
        }
    }

    // 生成错误答案
    generateWrongAnswer(correct, config) {
        const numCorrect = parseFloat(correct);
        const offset = Math.random() * 20 + 5;
        const wrong = Math.random() > 0.5 ? numCorrect + offset : numCorrect - offset;
        return String(Math.round(wrong * 10) / 10);
    }

    // 生成答案
    generateAnswer(subject, config) {
        if (subject === '数学') {
            return this.generateMathAnswer(config);
        }
        return 'A';
    }

    // 生成解析
    generateExplanation(subject, config) {
        return `本题考察${subject}${config.module || ''}知识，属于${config.difficulty || '中等'}难度。解题要点：认真审题，理清思路，规范作答。`;
    }

    // 提取知识点
    extractKnowledgePoints(subject, config) {
        const points = [`${subject}基础`];
        
        if (config.module) points.push(config.module);
        if (config.grade) points.push(`年级：${config.grade}`);
        
        return points;
    }

    // 生成媒体
    generateMedia(subject) {
        return {
            type: subject === '英语' ? 'audio' : 'image',
            src: `/media/${subject}_${Date.now()}.${subject === '英语' ? 'mp3' : 'png'}`
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

    // ==================== 批量生成 ====================

    // 生成试卷
    generatePaper(config) {
        const { subject, grade, questionCount, difficulty, modules } = config;
        
        const paper = {
            id: `paper_${Date.now()}`,
            subject,
            grade,
            title: `${grade}年级${subject}测试卷`,
            questions: [],
            totalScore: 0,
            duration: this.getDuration(grade),
            createdAt: Date.now()
        };

        // 按模块分配题目
        const moduleList = modules || [this.getDefaultModule(subject, grade)];
        const questionsPerModule = Math.floor(questionCount / moduleList.length);

        moduleList.forEach(module => {
            for (let i = 0; i < questionsPerModule; i++) {
                const question = this.generateQuestion({
                    subject,
                    grade,
                    module,
                    difficulty
                });
                paper.questions.push(question);
                paper.totalScore += question.difficulty === 'easy' ? 5 : question.difficulty === 'medium' ? 8 : 10;
            }
        });

        return paper;
    }

    // 获取考试时长
    getDuration(grade) {
        if (grade <= 2) return 40;
        if (grade <= 4) return 60;
        if (grade <= 6) return 90;
        return 120;
    }

    // ==================== 知识点关联 ====================

    // 构建知识点图谱
    buildKnowledgeGraph(subject, grade) {
        return {
            subject,
            grade,
            nodes: this.generateKnowledgeNodes(subject, grade),
            relations: this.generateKnowledgeRelations(subject, grade)
        };
    }

    // 生成知识点节点
    generateKnowledgeNodes(subject, grade) {
        const nodes = [];
        const modules = this.subjects[subject]?.modules || [];

        modules.forEach((module, idx) => {
            nodes.push({
                id: `${subject}_${module}`,
                name: module,
                level: idx + 1,
                mastery: 0.5 + Math.random() * 0.5
            });
        });

        return nodes;
    }

    // 生成知识点关系
    generateKnowledgeRelations(subject, grade) {
        const relations = [];
        const modules = this.subjects[subject]?.modules || [];

        for (let i = 0; i < modules.length - 1; i++) {
            relations.push({
                source: `${subject}_${modules[i]}`,
                target: `${subject}_${modules[i + 1]}`,
                type: 'prerequisite'
            });
        }

        return relations;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            subjects: Object.keys(this.subjects)
        };
    }
}

// 创建全局实例
window.subjectQuestionGenerator = new SubjectQuestionGenerator();

// 导出
window.MTSCOS_SubjectQuestionGenerator = SubjectQuestionGenerator;

/**
 * MTSCOS AI System - 日语考试专家AI员工
 * 版本: 4.4.0
 * 描述: 专注于日语水平测试、题库管理、考试评估和学习跟踪
 */

class JapaneseExamExpert {
    constructor() {
        this.id = 'japanese-exam-expert';
        this.name = '日语考试专家';
        this.icon = 'fa-graduation-cap';
        this.color = '#e11d48';
        this.gradient = 'linear-gradient(135deg, #e11d48 0%, #be123c 100%)';
        this.role = '日语教育专家';
        this.description = '专注于日语水平测试、N1-N5题库管理、考试评估和学习进度跟踪';
        this.abilities = [
            '日语水平测试',
            '题库管理',
            '考试评估',
            '学习跟踪',
            '智能出题',
            '错题分析'
        ];
        this.status = 'active';
        this.workload = 25;
        this.efficiency = 95;
        this.levels = ['N1', 'N2', 'N3', 'N4', 'N5'];
    }

    // ==================== 考试管理 ====================

    // 创建考试
    createExam(config) {
        return {
            id: `exam_${Date.now()}`,
            title: config.title,
            level: config.level,
            type: config.type || 'full', // full, mini, practice
            duration: config.duration || 90, // 分钟
            questionCount: config.questionCount || 40,
            questionTypes: config.questionTypes || ['vocabulary', 'grammar', 'reading', 'listening'],
            passingScore: config.passingScore || 60,
            createdAt: Date.now(),
            status: 'pending'
        };
    }

    // 生成试卷
    generatePaper(examConfig) {
        const paper = {
            id: `paper_${Date.now()}`,
            examId: examConfig.id,
            questions: [],
            totalScore: 0,
            timeLimit: examConfig.duration * 60, // 转换为秒
            generatedAt: Date.now()
        };

        // 按比例分配题目
        const distribution = this.getQuestionDistribution(examConfig.level);
        
        examConfig.questionTypes.forEach(type => {
            const count = Math.floor(examConfig.questionCount * (distribution[type] || 0.25));
            const questions = this.selectQuestions(type, count, examConfig.level);
            paper.questions.push(...questions);
        });

        // 计算总分
        paper.totalScore = paper.questions.reduce((sum, q) => sum + (q.score || 1), 0);

        return paper;
    }

    // 获取题目分布
    getQuestionDistribution(level) {
        const distributions = {
            N1: { vocabulary: 0.20, grammar: 0.25, reading: 0.35, listening: 0.20 },
            N2: { vocabulary: 0.22, grammar: 0.25, reading: 0.33, listening: 0.20 },
            N3: { vocabulary: 0.25, grammar: 0.25, reading: 0.30, listening: 0.20 },
            N4: { vocabulary: 0.30, grammar: 0.25, reading: 0.25, listening: 0.20 },
            N5: { vocabulary: 0.35, grammar: 0.25, reading: 0.20, listening: 0.20 }
        };
        return distributions[level] || distributions.N3;
    }

    // 选择题目
    selectQuestions(type, count, level) {
        // 模拟题目选择逻辑
        const questions = [];
        for (let i = 0; i < count; i++) {
            questions.push({
                id: `q_${type}_${Date.now()}_${i}`,
                type,
                level,
                score: type === 'reading' ? 2 : 1,
                difficulty: this.calculateDifficulty(level)
            });
        }
        return questions;
    }

    // 计算难度
    calculateDifficulty(level) {
        const baseDifficulty = {
            N1: 0.9,
            N2: 0.75,
            N3: 0.6,
            N4: 0.4,
            N5: 0.2
        };
        return baseDifficulty[level] || 0.5;
    }

    // ==================== 考试评估 ====================

    // 评估答案
    evaluateAnswer(question, userAnswer) {
        const isCorrect = userAnswer === question.correctAnswer;
        return {
            isCorrect,
            score: isCorrect ? (question.score || 1) : 0,
            correctAnswer: question.correctAnswer,
            explanation: question.explanation || ''
        };
    }

    // 计算考试结果
    calculateResult(paper, answers) {
        const result = {
            paperId: paper.id,
            totalScore: 0,
            maxScore: paper.totalScore,
            correctCount: 0,
            totalCount: paper.questions.length,
            sectionScores: {},
            passed: false,
            evaluatedAt: Date.now()
        };

        // 评估每个题目
        paper.questions.forEach((question, index) => {
            const evaluation = this.evaluateAnswer(question, answers[index]);
            result.totalScore += evaluation.score;
            result.correctCount += evaluation.isCorrect ? 1 : 0;
            
            // 分组统计
            if (!result.sectionScores[question.type]) {
                result.sectionScores[question.type] = { correct: 0, total: 0, score: 0 };
            }
            result.sectionScores[question.type].total++;
            result.sectionScores[question.type].score += evaluation.score;
            if (evaluation.isCorrect) {
                result.sectionScores[question.type].correct++;
            }
        });

        // 计算百分比
        result.percentage = Math.round((result.totalScore / result.maxScore) * 100);
        result.passed = result.percentage >= paper.passingScore;

        // 估算等级
        result.estimatedLevel = this.estimateLevel(result.percentage, paper.level);

        return result;
    }

    // 估算等级
    estimateLevel(percentage, currentLevel) {
        const levelIndex = this.levels.indexOf(currentLevel);
        if (percentage >= 90) return this.levels[Math.max(0, levelIndex - 1)] || 'N1+';
        if (percentage >= 70) return currentLevel;
        if (percentage < 50) return this.levels[Math.min(this.levels.length - 1, levelIndex + 1)] || 'N5-';
        return currentLevel;
    }

    // ==================== 学习跟踪 ====================

    // 记录学习进度
    recordProgress(userId, progress) {
        return {
            userId,
            date: new Date().toISOString().split('T')[0],
            level: progress.level,
            questionsAnswered: progress.questionsAnswered || 0,
            correctRate: progress.correctRate || 0,
            studyTime: progress.studyTime || 0,
            masteredWords: progress.masteredWords || [],
            weakPoints: progress.weakPoints || [],
            updatedAt: Date.now()
        };
    }

    // 分析学习模式
    analyzeLearningPattern(userId) {
        return {
            userId,
            studyFrequency: 'daily',
            preferredStudyTime: 'evening',
            strongAreas: ['vocabulary', 'grammar'],
            weakAreas: ['listening', 'reading'],
            recommendedStudyTime: 30, // 分钟
            optimalQuestionCount: 20
        };
    }

    // ==================== 错题分析 ====================

    // 收集错题
    collectMistakes(examResult, paper, answers) {
        const mistakes = [];
        
        paper.questions.forEach((question, index) => {
            const userAnswer = answers[index];
            if (userAnswer !== question.correctAnswer) {
                mistakes.push({
                    question: question,
                    userAnswer,
                    correctAnswer: question.correctAnswer,
                    timestamp: Date.now(),
                    reviewCount: 0,
                    mastered: false
                });
            }
        });

        return mistakes;
    }

    // 生成错题复习计划
    generateReviewPlan(mistakes) {
        // 按错误次数和难度排序
        const sorted = mistakes.sort((a, b) => {
            if (a.reviewCount !== b.reviewCount) return a.reviewCount - b.reviewCount;
            return b.question.difficulty - a.question.difficulty;
        });

        // 使用间隔重复算法
        const plan = {
            reviewItems: [],
            createdAt: Date.now()
        };

        sorted.forEach((mistake, index) => {
            const daysUntilReview = Math.pow(2, mistake.reviewCount); // 1, 2, 4, 8...
            plan.reviewItems.push({
                ...mistake,
                scheduledDate: new Date(Date.now() + daysUntilReview * 24 * 60 * 60 * 1000),
                priority: index + 1
            });
        });

        return plan;
    }

    // ==================== 统计报告 ====================

    // 生成学习报告
    generateProgressReport(userId, dateRange) {
        return {
            userId,
            period: dateRange,
            summary: {
                totalExams: 10,
                averageScore: 78.5,
                averageCorrectRate: 78.5,
                totalStudyTime: 1800, // 分钟
                questionsAnswered: 500
            },
            trends: {
                score: [65, 70, 72, 75, 78, 80, 78, 82],
                correctRate: [65, 70, 72, 75, 78, 80, 78, 82]
            },
            achievements: [
                { title: '连续学习7天', unlocked: true },
                { title: '正确率达到80%', unlocked: true },
                { title: '完成N3全部题目', unlocked: false }
            ],
            recommendations: [
                '建议加强听力训练',
                '每天复习20个错题',
                '完成N2语法专项练习'
            ]
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
            supportedLevels: this.levels
        };
    }

    // 获取当前时间
    getCurrentTime() {
        return new Date().toISOString();
    }
}

// 创建全局实例
window.japaneseExamExpert = new JapaneseExamExpert();

// 导出
window.MTSCOS_JapaneseExamExpert = JapaneseExamExpert;

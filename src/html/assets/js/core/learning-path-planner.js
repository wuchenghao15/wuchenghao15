/**
 * MTSCOS AI System - 学习路径规划师AI员工
 * 版本: 4.4.0
 * 描述: 专注于学习路径规划、自适应学习、进度追踪和学习推荐
 */

class LearningPathPlanner {
    constructor() {
        this.id = 'learning-path-planner';
        this.name = '学习路径规划师';
        this.icon = 'fa-route';
        this.color = '#f97316';
        this.gradient = 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)';
        this.role = '学习路径规划专家';
        this.description = '专注于学习路径规划、自适应学习、进度追踪和学习推荐';
        this.abilities = [
            '学习路径',
            '自适应学习',
            '进度追踪',
            '学习推荐',
            '目标设定',
            '学习报告'
        ];
        this.status = 'active';
        this.workload = 25;
        this.efficiency = 95;
        this.pathTemplates = this.initPathTemplates();
        this.progressCache = {};
    }

    // ==================== 学习路径模板 ====================

    initPathTemplates() {
        return {
            '基础巩固': {
                name: '基础巩固',
                description: '适合零基础或基础薄弱的学习者',
                duration: 30,
                steps: [
                    { day: 1-7, focus: '入门知识', difficulty: 'easy', dailyQuestions: 10 },
                    { day: 8-14, focus: '基础练习', difficulty: 'easy', dailyQuestions: 15 },
                    { day: 15-21, focus: '进阶练习', difficulty: 'medium', dailyQuestions: 20 },
                    { day: 22-30, focus: '综合复习', difficulty: 'medium', dailyQuestions: 25 }
                ]
            },
            '快速提升': {
                name: '快速提升',
                description: '适合有一定基础想快速提升的学习者',
                duration: 20,
                steps: [
                    { day: 1-5, focus: '薄弱点诊断', difficulty: 'medium', dailyQuestions: 20 },
                    { day: 6-10, focus: '专项突破', difficulty: 'hard', dailyQuestions: 25 },
                    { day: 11-15, focus: '综合训练', difficulty: 'hard', dailyQuestions: 30 },
                    { day: 16-20, focus: '模拟考试', difficulty: 'expert', dailyQuestions: 35 }
                ]
            },
            '冲刺备考': {
                name: '冲刺备考',
                description: '适合即将参加考试的学习者',
                duration: 14,
                steps: [
                    { day: 1-3, focus: '真题练习', difficulty: 'hard', dailyQuestions: 30 },
                    { day: 4-7, focus: '错题复习', difficulty: 'hard', dailyQuestions: 25 },
                    { day: 8-10, focus: '模拟考试', difficulty: 'expert', dailyQuestions: 40 },
                    { day: 11-14, focus: '查漏补缺', difficulty: 'expert', dailyQuestions: 35 }
                ]
            },
            '长期培养': {
                name: '长期培养',
                description: '适合长期学习规划',
                duration: 90,
                steps: [
                    { day: 1-30, focus: '基础阶段', difficulty: 'easy', dailyQuestions: 15 },
                    { day: 31-60, focus: '进阶阶段', difficulty: 'medium', dailyQuestions: 20 },
                    { day: 61-90, focus: '提升阶段', difficulty: 'hard', dailyQuestions: 25 }
                ]
            }
        };
    }

    // 获取路径模板
    getPathTemplates() {
        return this.pathTemplates;
    }

    // ==================== 学习路径规划 ====================

    // 创建学习路径
    createLearningPath(userId, config) {
        const template = this.pathTemplates[config.template] || this.pathTemplates['基础巩固'];
        const subject = config.subject || '语文';
        const grade = config.grade || 1;

        const path = {
            id: `path_${Date.now()}`,
            userId,
            subject,
            grade,
            template: template.name,
            name: config.name || `${subject}${grade}年级${template.name}`,
            description: template.description,
            targetLevel: config.targetLevel || '合格',
            startDate: config.startDate || Date.now(),
            endDate: Date.now() + template.duration * 24 * 60 * 60 * 1000,
            status: 'active',
            progress: 0,
            steps: template.steps.map((step, index) => ({
                id: `step_${Date.now()}_${index}`,
                order: index + 1,
                ...step,
                completed: false,
                questionsCompleted: 0,
                questionsTarget: step.dailyQuestions * 7
            })),
            createdAt: Date.now(),
            updatedAt: Date.now()
        };

        this.progressCache[path.id] = { ...path, currentStep: 0 };
        return path;
    }

    // 获取学习路径
    getLearningPath(pathId) {
        return this.progressCache[pathId] || null;
    }

    // 更新学习路径
    updateLearningPath(pathId, updates) {
        const path = this.progressCache[pathId];
        if (!path) return null;

        Object.assign(path, updates, { updatedAt: Date.now() });
        return path;
    }

    // 完成步骤
    completeStep(pathId, stepId) {
        const path = this.progressCache[pathId];
        if (!path) return null;

        const step = path.steps.find(s => s.id === stepId);
        if (step) {
            step.completed = true;
            step.completedAt = Date.now();
            this.updateProgress(path);
        }

        return path;
    }

    // 更新进度
    updateProgress(path) {
        const totalSteps = path.steps.length;
        const completedSteps = path.steps.filter(s => s.completed).length;
        path.progress = Math.round((completedSteps / totalSteps) * 100);
        path.updatedAt = Date.now();
    }

    // 暂停路径
    pausePath(pathId) {
        const path = this.progressCache[pathId];
        if (path) {
            path.status = 'paused';
            path.pausedAt = Date.now();
            path.updatedAt = Date.now();
        }
        return path;
    }

    // 继续路径
    resumePath(pathId) {
        const path = this.progressCache[pathId];
        if (path) {
            path.status = 'active';
            path.resumedAt = Date.now();
            path.updatedAt = Date.now();
        }
        return path;
    }

    // 删除路径
    deletePath(pathId) {
        delete this.progressCache[pathId];
        return true;
    }

    // ==================== 自适应学习 ====================

    // 获取自适应题目
    getAdaptiveQuestions(userId, count = 10) {
        const history = this.getUserHistory(userId);
        const weakPoints = this.identifyWeakPoints(history);
        const strongPoints = this.identifyStrongPoints(history);

        const questions = [];
        
        for (let i = 0; i < count; i++) {
            const useWeak = Math.random() > 0.3;
            if (useWeak && weakPoints.length > 0) {
                const point = weakPoints[Math.floor(Math.random() * weakPoints.length)];
                questions.push(this.generateQuestionForPoint(point, 'medium'));
            } else if (strongPoints.length > 0) {
                const point = strongPoints[Math.floor(Math.random() * strongPoints.length)];
                questions.push(this.generateQuestionForPoint(point, 'hard'));
            } else {
                questions.push(this.generateRandomQuestion());
            }
        }

        return questions;
    }

    // 识别薄弱点
    identifyWeakPoints(history) {
        if (!history || history.length === 0) return [];

        const pointStats = {};
        history.forEach(record => {
            if (record.knowledgePoints) {
                record.knowledgePoints.forEach(kp => {
                    const key = `${kp.module}_${kp.keyword}`;
                    pointStats[key] = pointStats[key] || { correct: 0, total: 0 };
                    pointStats[key].total++;
                    if (record.isCorrect) pointStats[key].correct++;
                });
            }
        });

        return Object.entries(pointStats)
            .filter(([_, stats]) => stats.total >= 3 && stats.correct / stats.total < 0.6)
            .map(([key]) => key)
            .slice(0, 5);
    }

    // 识别强项
    identifyStrongPoints(history) {
        if (!history || history.length === 0) return [];

        const pointStats = {};
        history.forEach(record => {
            if (record.knowledgePoints) {
                record.knowledgePoints.forEach(kp => {
                    const key = `${kp.module}_${kp.keyword}`;
                    pointStats[key] = pointStats[key] || { correct: 0, total: 0 };
                    pointStats[key].total++;
                    if (record.isCorrect) pointStats[key].correct++;
                });
            }
        });

        return Object.entries(pointStats)
            .filter(([_, stats]) => stats.total >= 5 && stats.correct / stats.total >= 0.8)
            .map(([key]) => key)
            .slice(0, 5);
    }

    // 为知识点生成题目
    generateQuestionForPoint(point, difficulty) {
        const [module, keyword] = point.split('_');
        return {
            id: `q_${Date.now()}`,
            content: `关于${keyword}的题目`,
            type: '选择题',
            difficulty,
            tags: [module, keyword],
            knowledgePoints: [{ module, keyword }],
            options: ['A选项', 'B选项', 'C选项', 'D选项'],
            correctAnswer: 0
        };
    }

    // 生成随机题目
    generateRandomQuestion() {
        const difficulties = ['easy', 'medium', 'hard'];
        return {
            id: `q_${Date.now()}`,
            content: '随机生成的题目内容',
            type: '选择题',
            difficulty: difficulties[Math.floor(Math.random() * difficulties.length)],
            options: ['A选项', 'B选项', 'C选项', 'D选项'],
            correctAnswer: Math.floor(Math.random() * 4)
        };
    }

    // ==================== 进度追踪 ====================

    // 获取用户学习历史
    getUserHistory(userId) {
        const stored = localStorage.getItem(`learning_history_${userId}`);
        if (stored) {
            try {
                return JSON.parse(stored);
            } catch (e) {
                console.warn('解析学习历史失败:', e.message);
            }
        }
        return [];
    }

    // 保存学习记录
    saveLearningRecord(userId, record) {
        const history = this.getUserHistory(userId);
        history.push({
            ...record,
            timestamp: Date.now(),
            userId
        });
        
        localStorage.setItem(`learning_history_${userId}`, JSON.stringify(history));
        return history;
    }

    // 获取学习统计
    getLearningStats(userId) {
        const history = this.getUserHistory(userId);
        const total = history.length;
        const correct = history.filter(r => r.isCorrect).length;
        
        const subjectStats = {};
        const dateStats = {};
        
        history.forEach(record => {
            const subject = record.subject || '未知';
            subjectStats[subject] = subjectStats[subject] || { correct: 0, total: 0 };
            subjectStats[subject].total++;
            if (record.isCorrect) subjectStats[subject].correct++;
            
            const date = new Date(record.timestamp).toDateString();
            dateStats[date] = (dateStats[date] || 0) + 1;
        });

        return {
            totalQuestions: total,
            correctRate: total > 0 ? ((correct / total) * 100).toFixed(1) : 0,
            bySubject: subjectStats,
            byDate: dateStats,
            streak: this.calculateStreak(dateStats)
        };
    }

    // 计算连续学习天数
    calculateStreak(dateStats) {
        const dates = Object.keys(dateStats).sort();
        if (dates.length === 0) return 0;

        let streak = 0;
        const today = new Date();
        let checkDate = new Date(today);
        
        for (let i = 0; i < 365; i++) {
            const dateStr = checkDate.toDateString();
            if (dateStats[dateStr]) {
                streak++;
                checkDate.setDate(checkDate.getDate() - 1);
            } else {
                break;
            }
        }

        return streak;
    }

    // ==================== 学习推荐 ====================

    // 生成学习推荐
    generateRecommendations(userId) {
        const stats = this.getLearningStats(userId);
        const recommendations = [];

        if (stats.totalQuestions < 10) {
            recommendations.push({
                type: 'beginner',
                message: '开始您的学习之旅，建议每天完成10道题目',
                priority: 'high'
            });
        }

        if (stats.correctRate < 60) {
            recommendations.push({
                type: 'practice',
                message: '正确率较低，建议复习基础知识',
                priority: 'high'
            });
        }

        if (stats.streak === 0) {
            recommendations.push({
                type: 'streak',
                message: '开始连续学习，养成良好习惯',
                priority: 'medium'
            });
        } else if (stats.streak >= 7) {
            recommendations.push({
                type: 'celebration',
                message: `太棒了！已经连续学习${stats.streak}天`,
                priority: 'low'
            });
        }

        const weakPoints = this.identifyWeakPoints(this.getUserHistory(userId));
        if (weakPoints.length > 0) {
            recommendations.push({
                type: 'weak_points',
                message: `发现薄弱点：${weakPoints.join('、')}，建议加强练习`,
                priority: 'high'
            });
        }

        return recommendations;
    }

    // ==================== 学习报告 ====================

    // 生成学习报告
    generateLearningReport(userId, period = 'week') {
        const stats = this.getLearningStats(userId);
        const history = this.getUserHistory(userId);

        const report = {
            userId,
            period,
            generatedAt: Date.now(),
            summary: {
                totalQuestions: stats.totalQuestions,
                correctRate: stats.correctRate,
                streak: stats.streak,
                activeDays: Object.keys(stats.byDate).length
            },
            details: {
                bySubject: stats.bySubject,
                byDate: stats.byDate
            },
            recommendations: this.generateRecommendations(userId),
            weakPoints: this.identifyWeakPoints(history),
            strongPoints: this.identifyStrongPoints(history)
        };

        return report;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            activePaths: Object.keys(this.progressCache).length,
            templates: Object.keys(this.pathTemplates).length
        };
    }
}

// 创建全局实例
window.learningPathPlanner = new LearningPathPlanner();

// 导出
window.MTSCOS_LearningPathPlanner = LearningPathPlanner;

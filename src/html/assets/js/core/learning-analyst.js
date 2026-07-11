/**
 * MTSCOS AI System - 学习分析师AI员工
 * 版本: 4.4.0
 * 描述: 专注于学习数据分析、进度跟踪、能力评估和个性化学习推荐
 */

class LearningAnalyst {
    constructor() {
        this.id = 'learning-analyst';
        this.name = '学习分析师';
        this.icon = 'fa-chart-bar';
        this.color = '#0891b2';
        this.gradient = 'linear-gradient(135deg, #0891b2 0%, #0e7490 100%)';
        this.role = '学习分析专家';
        this.description = '专注于学习数据分析、能力评估、进度跟踪和个性化学习推荐';
        this.abilities = [
            '学习分析',
            '能力评估',
            '进度跟踪',
            '个性化推荐',
            '薄弱点诊断',
            '学习规划'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 96;
        this.learningModels = this.initLearningModels();
    }

    // ==================== 学习模型 ====================

    initLearningModels() {
        return {
            forgettingCurve: {
                halfLife: 24, // 小时
                formula: (initialStrength, hours) => initialStrength * Math.pow(0.5, hours / 24)
            },
            masteryThreshold: 0.85,
            optimalChunkSize: 7,
            reviewIntervals: [1, 3, 7, 14, 30, 60] // 天
        };
    }

    // ==================== 学习分析 ====================

    // 分析学习数据
    analyzeLearningData(userId, dateRange) {
        const analysis = {
            userId,
            period: dateRange,
            overview: this.generateOverview(),
            detailedMetrics: this.calculateDetailedMetrics(),
            patterns: this.detectPatterns(),
            insights: this.generateInsights(),
            timestamp: Date.now()
        };

        return analysis;
    }

    // 生成概览
    generateOverview() {
        return {
            totalStudyTime: 0,
            totalQuestions: 0,
            averageCorrectRate: 0,
            studyDays: 0,
            currentStreak: 0,
            longestStreak: 0
        };
    }

    // 计算详细指标
    calculateDetailedMetrics() {
        return {
            vocabulary: {
                mastered: 0,
                learning: 0,
                new: 0,
                correctRate: 0
            },
            grammar: {
                mastered: 0,
                learning: 0,
                new: 0,
                correctRate: 0
            },
            reading: {
                mastered: 0,
                learning: 0,
                new: 0,
                correctRate: 0
            },
            listening: {
                mastered: 0,
                learning: 0,
                new: 0,
                correctRate: 0
            }
        };
    }

    // 检测学习模式
    detectPatterns() {
        return {
            studyTimePreference: 'evening',
            optimalSessionLength: 30,
            bestStudyDays: ['weekday', 'weekend'],
            fatiguePoints: [45, 90],
            motivationTrend: 'stable'
        };
    }

    // 生成洞察
    generateInsights() {
        return [
            {
                type: 'strength',
                title: '词汇掌握良好',
                description: '您的词汇正确率达到85%，高于平均水平',
                impact: 'positive'
            },
            {
                type: 'weakness',
                title: '听力需要加强',
                description: '听力正确率仅65%，建议每天增加10分钟听力练习',
                impact: 'negative'
            },
            {
                type: 'suggestion',
                title: '学习时间优化',
                description: '您最有效的学习时间是晚上8-10点',
                impact: 'neutral'
            }
        ];
    }

    // ==================== 能力评估 ====================

    // 评估能力水平
    assessAbilityLevel(userId) {
        const assessment = {
            userId,
            overall: {
                level: 'N3',
                score: 72,
                trend: 'improving'
            },
            components: {
                vocabulary: { level: 'N3+', score: 78, rank: 1 },
                grammar: { level: 'N3', score: 70, rank: 2 },
                reading: { level: 'N3', score: 72, rank: 3 },
                listening: { level: 'N4', score: 65, rank: 4 }
            },
            estimatedTimeToNext: {
                N2: 180, // 天
                confidence: 0.75
            },
            assessedAt: Date.now()
        };

        return assessment;
    }

    // 预测能力发展
    predictAbilityGrowth(userId, months = 6) {
        const predictions = [];
        let currentDate = new Date();

        for (let i = 0; i < months; i++) {
            currentDate.setMonth(currentDate.getMonth() + 1);
            predictions.push({
                date: currentDate.toISOString().split('T')[0],
                estimatedLevel: this.predictLevel(i),
                confidence: Math.max(0.5, 0.9 - i * 0.05),
                recommendedHours: 40 - i * 2
            });
        }

        return predictions;
    }

    // 预测等级
    predictLevel(monthsAhead) {
        const levels = ['N5', 'N4', 'N3', 'N2', 'N2+', 'N1'];
        const currentIndex = 2; // N3
        const newIndex = Math.min(levels.length - 1, currentIndex + Math.floor(monthsAhead / 3));
        return levels[newIndex];
    }

    // ==================== 学习跟踪 ====================

    // 跟踪学习进度
    trackProgress(userId) {
        return {
            userId,
            currentStreak: 7,
            longestStreak: 14,
            totalStudyDays: 45,
            totalStudyTime: 3600, // 分钟
            lastStudyDate: new Date().toISOString().split('T')[0],
            dailyGoal: {
                target: 30,
                achieved: 25,
                progress: 83
            },
            weeklyGoal: {
                target: 150,
                achieved: 120,
                progress: 80
            },
            monthlyGoal: {
                target: 600,
                achieved: 420,
                progress: 70
            }
        };
    }

    // 更新进度
    updateProgress(userId, activity) {
        const progress = this.trackProgress(userId);
        
        // 更新学习时间
        progress.totalStudyTime += activity.studyMinutes || 0;
        
        // 更新连续学习天数
        const today = new Date().toISOString().split('T')[0];
        const lastStudy = progress.lastStudyDate;
        
        if (this.isConsecutiveDay(lastStudy, today)) {
            progress.currentStreak++;
        } else if (lastStudy !== today) {
            progress.currentStreak = 1;
        }
        
        if (progress.currentStreak > progress.longestStreak) {
            progress.longestStreak = progress.currentStreak;
        }

        progress.lastStudyDate = today;
        return progress;
    }

    // 检查是否是连续日期
    isConsecutiveDay(date1, date2) {
        if (!date1) return false;
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        const diff = (d2 - d1) / (1000 * 60 * 60 * 24);
        return diff === 1;
    }

    // ==================== 个性化推荐 ====================

    // 生成学习推荐
    generateRecommendations(userId) {
        const recommendations = {
            userId,
            daily: this.generateDailyRecommendations(),
            weekly: this.generateWeeklyRecommendations(),
            personalized: this.generatePersonalizedPlan(),
            generatedAt: Date.now()
        };

        return recommendations;
    }

    // 生成每日推荐
    generateDailyRecommendations() {
        return [
            {
                type: 'practice',
                subject: 'listening',
                duration: 15,
                reason: '根据您的学习记录，听力是薄弱环节'
            },
            {
                type: 'review',
                subject: 'vocabulary',
                count: 20,
                reason: '今天有5个词汇需要复习'
            },
            {
                type: 'new',
                subject: 'grammar',
                count: 5,
                reason: '建议学习新的语法点 N3-15'
            }
        ];
    }

    // 生成每周推荐
    generateWeeklyRecommendations() {
        return {
            focus: '听力提升',
            targetHours: 5,
            activities: [
                { day: '周一', activity: '听力练习N3', duration: 30 },
                { day: '周二', activity: '词汇复习', duration: 20 },
                { day: '周三', activity: '语法学习', duration: 30 },
                { day: '周四', activity: '阅读理解', duration: 30 },
                { day: '周五', activity: '听力练习N2', duration: 30 },
                { day: '周六', activity: '模拟测试', duration: 60 },
                { day: '周日', activity: '错题复习', duration: 30 }
            ]
        };
    }

    // 生成个性化计划
    generatePersonalizedPlan() {
        return {
            duration: 90, // 天
            targetLevel: 'N2',
            milestones: [
                { day: 30, goal: '完成N3全部词汇', progress: 0 },
                { day: 60, goal: '通过N3模拟测试', progress: 0 },
                { day: 90, goal: '达到N2水平', progress: 0 }
            ],
            dailyRoutine: {
                morning: '复习旧知识 15分钟',
                afternoon: '学习新内容 30分钟',
                evening: '听力练习 20分钟'
            }
        };
    }

    // ==================== 薄弱点诊断 ====================

    // 诊断薄弱点
    diagnoseWeakPoints(userId) {
        return {
            userId,
            overallWeakPoints: [
                { type: 'listening', severity: 'high', details: '长对话理解困难' },
                { type: 'grammar', severity: 'medium', details: '敬语使用不熟练' },
                { type: 'vocabulary', severity: 'low', details: 'N2级别词汇量不足' }
            ],
            specificWeakPoints: [
                { topic: '授受动词', mastery: 0.4, questions: 15, correctRate: 0.4 },
                { topic: '假定形', mastery: 0.5, questions: 20, correctRate: 0.5 },
                { topic: '被动形式', mastery: 0.55, questions: 18, correctRate: 0.55 }
            ],
            recommendations: [
                '每天花15分钟专门练习听力',
                '整理授受动词专项练习',
                '复习敬语使用场景'
            ],
            diagnosedAt: Date.now()
        };
    }

    // 分析错误模式
    analyzeErrorPatterns(userId) {
        return {
            patterns: [
                {
                    type: '混淆相近语法',
                    examples: ['ている vs  てある', 'らしい vs ようだ'],
                    frequency: 5
                },
                {
                    type: '审题不仔细',
                    examples: ['忽略否定词', '忽略时间状语'],
                    frequency: 3
                }
            ],
            rootCauses: [
                '练习量不足',
                '知识点理解不透彻',
                '考试技巧欠缺'
            ]
        };
    }

    // ==================== 学习规划 ====================

    // 创建学习计划
    createStudyPlan(userId, config) {
        const plan = {
            id: `plan_${Date.now()}`,
            userId,
            targetLevel: config.targetLevel,
            duration: config.duration,
            startDate: config.startDate || new Date().toISOString().split('T')[0],
            weeklyTargets: this.calculateWeeklyTargets(config),
            dailySchedule: this.generateDailySchedule(config),
            milestones: this.setMilestones(config),
            createdAt: Date.now()
        };

        return plan;
    }

    // 计算每周目标
    calculateWeeklyTargets(config) {
        const totalHours = config.duration * 2; // 假设每天2小时
        const weeks = Math.ceil(config.duration / 7);
        
        return {
            totalHours,
            weeklyHours: Math.round(totalHours / weeks),
            weeklyQuestions: 200,
            weeklyCorrectRate: 75
        };
    }

    // 生成每日安排
    generateDailySchedule(config) {
        return {
            morning: { activity: '复习', duration: 20, types: ['vocabulary'] },
            afternoon: { activity: '新知识', duration: 40, types: ['grammar', 'vocabulary'] },
            evening: { activity: '练习', duration: 30, types: ['reading', 'listening'] }
        };
    }

    // 设置里程碑
    setMilestones(config) {
        const milestones = [];
        const totalDays = config.duration;
        
        [0.25, 0.5, 0.75, 1].forEach(ratio => {
            const day = Math.floor(totalDays * ratio);
            milestones.push({
                day,
                target: `完成 ${Math.round(ratio * 100)}% 学习内容`,
                assessment: day === totalDays ? 'final' : 'checkpoint'
            });
        });

        return milestones;
    }

    // ==================== 报告生成 ====================

    // 生成学习报告
    generateReport(userId, period = 'week') {
        return {
            userId,
            period,
            summary: {
                studyTime: 180,
                questionsAnswered: 250,
                correctRate: 78,
                levelProgress: '+2%'
            },
            highlights: [
                '连续学习7天',
                '听力正确率提升5%',
                '掌握50个新词汇'
            ],
            areasForImprovement: [
                '需要加强敬语练习',
                '阅读速度有待提升'
            ],
            nextWeekGoals: [
                '完成N3语法第15-20课',
                '听力练习不少于2小时',
                '复习错题50道'
            ],
            generatedAt: Date.now()
        };
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency
        };
    }
}

// 创建全局实例
window.learningAnalyst = new LearningAnalyst();

// 导出
window.MTSCOS_LearningAnalyst = LearningAnalyst;

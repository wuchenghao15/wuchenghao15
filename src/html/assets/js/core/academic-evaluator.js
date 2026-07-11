/**
 * MTSCOS AI System - 学业评估师AI员工
 * 版本: 4.4.0
 * 描述: 专注于K12学生学业水平评估、能力诊断、学习诊断和升学规划
 */

class AcademicEvaluator {
    constructor() {
        this.id = 'academic-evaluator';
        this.name = '学业评估师';
        this.icon = 'fa-clipboard-check';
        this.color = '#dc2626';
        this.gradient = 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)';
        this.role = '学业评估专家';
        this.description = '专注于K12学生学业水平评估、能力诊断、学习诊断和个性化提升方案';
        this.abilities = [
            '学业评估',
            '能力诊断',
            '学习诊断',
            '提升方案',
            '成长追踪',
            '升学规划'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 96;
        this.evaluationCriteria = this.initCriteria();
    }

    // ==================== 评估标准 ====================

    initCriteria() {
        return {
            '语文': {
                dimensions: ['拼音识字', '阅读理解', '写作表达', '古诗文', '口语交际'],
                weights: [0.15, 0.30, 0.25, 0.15, 0.15],
                levels: { excellent: 90, good: 80, pass: 60 }
            },
            '数学': {
                dimensions: ['计算能力', '概念理解', '应用能力', '空间想象', '逻辑思维'],
                weights: [0.20, 0.20, 0.30, 0.15, 0.15],
                levels: { excellent: 90, good: 80, pass: 60 }
            },
            '英语': {
                dimensions: ['听力理解', '口语表达', '阅读理解', '写作能力', '词汇语法'],
                weights: [0.20, 0.15, 0.25, 0.20, 0.20],
                levels: { excellent: 90, good: 80, pass: 60 }
            }
        };
    }

    // ==================== 学业评估 ====================

    // 评估学业水平
    assessAcademicLevel(studentId, subject, grade, examScores) {
        const criteria = this.evaluationCriteria[subject];
        if (!criteria) {
            return { error: `不支持的学科: ${subject}` };
        }

        const evaluation = {
            studentId,
            subject,
            grade,
            timestamp: Date.now(),
            overallScore: 0,
            level: '',
            dimensionScores: {},
            strengths: [],
            weaknesses: [],
            suggestions: []
        };

        // 计算各维度得分
        const dimensions = criteria.dimensions;
        const weights = criteria.weights;

        dimensions.forEach((dim, idx) => {
            const score = examScores[dim] || examScores[`dim${idx}`] || 70;
            evaluation.dimensionScores[dim] = {
                score,
                weight: weights[idx],
                weightedScore: score * weights[idx],
                level: this.getScoreLevel(score)
            };
            evaluation.overallScore += score * weights[idx];
        });

        evaluation.overallScore = Math.round(evaluation.overallScore);
        evaluation.level = this.getScoreLevel(evaluation.overallScore, criteria.levels);

        // 分析优劣势
        Object.entries(evaluation.dimensionScores).forEach(([dim, data]) => {
            if (data.score >= 85) {
                evaluation.strengths.push(dim);
            } else if (data.score < 65) {
                evaluation.weaknesses.push(dim);
            }
        });

        // 生成建议
        evaluation.suggestions = this.generateSuggestions(evaluation);

        return evaluation;
    }

    // 获取分数等级
    getScoreLevel(score, levels) {
        if (!levels) {
            if (score >= 90) return '优秀';
            if (score >= 80) return '良好';
            if (score >= 70) return '中等';
            if (score >= 60) return '及格';
            return '需努力';
        }

        if (score >= levels.excellent) return '优秀';
        if (score >= levels.good) return '良好';
        if (score >= levels.pass) return '及格';
        return '需努力';
    }

    // 生成建议
    generateSuggestions(evaluation) {
        const suggestions = [];

        evaluation.weaknesses.forEach(weakness => {
            suggestions.push({
                area: weakness,
                suggestion: this.getImprovementSuggestion(evaluation.subject, weakness),
                priority: 'high'
            });
        });

        evaluation.strengths.forEach(strength => {
            suggestions.push({
                area: strength,
                suggestion: '继续保持，发挥优势',
                priority: 'low'
            });
        });

        return suggestions;
    }

    // 获取改进建议
    getImprovementSuggestion(subject, weakness) {
        const suggestions = {
            '语文': {
                '拼音识字': '每天练习拼音声调，多读多写',
                '阅读理解': '增加阅读量，练习分段和概括',
                '写作表达': '坚持日记，积累好词好句',
                '古诗文': '理解性背诵，加强默写',
                '口语交际': '多参与讨论，锻炼表达能力'
            },
            '数学': {
                '计算能力': '每天练习口算，提高速度和准确率',
                '概念理解': '理解公式推导，多做变式题',
                '应用能力': '分析题意，找出数量关系',
                '空间想象': '动手操作，多画图分析',
                '逻辑思维': '学习分析方法，多做推理题'
            },
            '英语': {
                '听力理解': '多听英语材料，模仿发音',
                '口语表达': '大胆开口，练习对话',
                '阅读理解': '扩大词汇量，掌握阅读技巧',
                '写作能力': '背诵范文，模仿写作',
                '词汇语法': '系统复习，专项练习'
            }
        };

        return suggestions[subject]?.[weakness] || '加强针对性练习';
    }

    // ==================== 能力诊断 ====================

    // 诊断学习能力
    diagnoseLearningAbility(studentId, data) {
        return {
            studentId,
            abilities: {
                attention: this.evaluateAttention(data.attentionData),
                memory: this.evaluateMemory(data.memoryData),
                thinking: this.evaluateThinking(data.thinkingData),
                creativity: this.evaluateCreativity(data.creativityData),
                selfManagement: this.evaluateSelfManagement(data.managementData)
            },
            overallAbility: this.calculateOverallAbility,
            strengths: [],
            growthPoints: [],
            recommendations: [],
            diagnosedAt: Date.now()
        };
    }

    // 评估专注力
    evaluateAttention(data) {
        return {
            score: data?.score || 75,
            level: '良好',
            details: {
                sustained: data?.sustained || 70,
                selective: data?.selective || 80,
                divided: data?.divided || 65
            },
            suggestions: ['减少干扰因素', '分段学习', '适当休息']
        };
    }

    // 评估记忆力
    evaluateMemory(data) {
        return {
            score: data?.score || 78,
            level: '良好',
            details: {
                visual: data?.visual || 75,
                auditory: data?.auditory || 80,
                working: data?.working || 70
            },
            suggestions: ['使用记忆宫殿', '多感官学习', '定期复习']
        };
    }

    // 评估思维能力
    evaluateThinking(data) {
        return {
            score: data?.score || 72,
            level: '中等',
            details: {
                logical: data?.logical || 70,
                critical: data?.critical || 75,
                creative: data?.creative || 70
            },
            suggestions: ['学习思维导图', '多做分析题', '培养质疑精神']
        };
    }

    // 评估创造力
    evaluateCreativity(data) {
        return {
            score: data?.score || 68,
            level: '中等',
            details: {
                divergent: data?.divergent || 70,
                imagination: data?.imagination || 65
            },
            suggestions: ['鼓励发散思维', '多进行创作活动', '打破思维定式']
        };
    }

    // 评估自我管理
    evaluateSelfManagement(data) {
        return {
            score: data?.score || 70,
            level: '中等',
            details: {
                timeManagement: data?.timeManagement || 65,
                emotionControl: data?.emotionControl || 75,
                goalSetting: data?.goalSetting || 70
            },
            suggestions: ['制定学习计划', '使用时间管理工具', '设置阶段性目标']
        };
    }

    // 计算综合能力
    get calculateOverallAbility() {
        return (abilities) => {
            const scores = Object.values(abilities).map(a => a.score);
            return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        };
    }

    // ==================== 学习诊断 ====================

    // 诊断学习问题
    diagnoseLearningProblems(studentId, grade, recentScores, behaviorData) {
        const diagnosis = {
            studentId,
            grade,
            problems: [],
            rootCauses: [],
            solutions: [],
            confidence: 0.85,
            diagnosedAt: Date.now()
        };

        // 分析成绩趋势
        const trend = this.analyzeScoreTrend(recentScores);
        diagnosis.trend = trend;

        if (trend === 'declining') {
            diagnosis.problems.push('学习成绩呈下降趋势');
            diagnosis.rootCauses.push('学习习惯可能发生变化', '可能存在知识点遗漏');
            diagnosis.solutions.push('分析下降原因', '针对性补缺', '加强课后复习');
        }

        // 分析薄弱环节
        const weakAreas = this.findWeakAreas(recentScores);
        if (weakAreas.length > 0) {
            diagnosis.problems.push(`薄弱环节: ${weakAreas.join(', ')}`);
            diagnosis.solutions.push('加强薄弱环节专项训练', '寻求老师帮助');
        }

        // 分析学习行为
        if (behaviorData) {
            if (behaviorData.studyTime < grade * 10) {
                diagnosis.problems.push('学习时间不足');
                diagnosis.solutions.push('合理安排学习时间');
            }

            if (behaviorData.homeworkCompletion < 0.8) {
                diagnosis.problems.push('作业完成率较低');
                diagnosis.solutions.push('提高作业完成意识');
            }
        }

        return diagnosis;
    }

    // 分析成绩趋势
    analyzeScoreTrend(scores) {
        if (scores.length < 3) return 'stable';
        
        const recent = scores.slice(-3);
        if (recent[2] > recent[1] && recent[1] > recent[0]) return 'improving';
        if (recent[2] < recent[1] && recent[1] < recent[0]) return 'declining';
        return 'stable';
    }

    // 找出薄弱环节
    findWeakAreas(scores) {
        const subjects = Object.entries(scores)
            .filter(([k, v]) => typeof v === 'number')
            .filter(([k]) => k !== 'average');

        return subjects
            .filter(([, v]) => v < 70)
            .map(([k]) => k);
    }

    // ==================== 成长追踪 ====================

    // 追踪成长轨迹
    trackGrowth(studentId, historyData) {
        return {
            studentId,
            timeline: this.generateTimeline(historyData),
            achievements: this.identifyAchievements(historyData),
            progress: this.calculateProgress(historyData),
            predictions: this.predictFutureGrowth(historyData),
            trackedAt: Date.now()
        };
    }

    // 生成时间线
    generateTimeline(historyData) {
        const timeline = [];
        const sorted = historyData.sort((a, b) => a.date - b.date);

        sorted.forEach(data => {
            timeline.push({
                date: data.date,
                grade: data.grade,
                event: this.describeEvent(data),
                highlight: data.highlight || null
            });
        });

        return timeline;
    }

    // 描述事件
    describeEvent(data) {
        if (data.type === 'exam') {
            return `${data.subject}考试，得分${data.score}`;
        } else if (data.type === 'milestone') {
            return data.description || '达成里程碑';
        }
        return '学习记录';
    }

    // 识别成就
    identifyAchievements(historyData) {
        const achievements = [];

        // 连续学习成就
        if (historyData.streak >= 30) {
            achievements.push({
                type: 'streak',
                title: '坚持不懈',
                description: `连续学习${historyData.streak}天`,
                icon: '🔥'
            });
        }

        // 进步成就
        if (historyData.progress >= 20) {
            achievements.push({
                type: 'progress',
                title: '显著进步',
                description: `整体提升${historyData.progress}分`,
                icon: '📈'
            });
        }

        return achievements;
    }

    // 计算进度
    calculateProgress(historyData) {
        const first = historyData.data?.[0];
        const last = historyData.data?.[historyData.data.length - 1];

        if (!first || !last) return { improvement: 0, trend: 'stable' };

        const improvement = last.average - first.average;
        return {
            improvement: Math.round(improvement),
            trend: improvement > 5 ? 'improving' : improvement < -5 ? 'declining' : 'stable'
        };
    }

    // 预测未来成长
    predictFutureGrowth(historyData) {
        return {
            nextMonth: '+5分',
            nextSemester: '+15分',
            confidence: 0.75,
            conditions: ['保持当前学习状态', '加强薄弱环节']
        };
    }

    // ==================== 升学规划 ====================

    // 制定升学规划
    createUpgradePlan(studentId, currentGrade, assessment) {
        const phase = currentGrade <= 6 ? 'primary' : 'junior';
        const phaseEnd = currentGrade <= 6 ? 6 : 9;

        return {
            studentId,
            currentGrade,
            phase,
            targetGrade: phaseEnd,
            timeline: this.createTimeline(phaseEnd, assessment),
            milestones: this.setMilestones(phaseEnd),
            resources: this.suggestResources(assessment),
            createdAt: Date.now()
        };
    }

    // 创建时间线
    createTimeline(targetGrade, assessment) {
        const timeline = [];
        
        for (let g = targetGrade; g <= targetGrade + 1; g++) {
            timeline.push({
                grade: g,
                tasks: this.getGradeTasks(g, assessment),
                target: g === targetGrade ? '当前' : '升学目标'
            });
        }

        return timeline;
    }

    // 获取年级任务
    getGradeTasks(grade, assessment) {
        const tasks = [];

        if (assessment.weaknesses?.length > 0) {
            tasks.push('加强薄弱科目学习');
        }

        if (grade % 3 === 0) {
            tasks.push('参加学业水平测试');
        }

        tasks.push('保持良好学习习惯');

        return tasks;
    }

    // 设置里程碑
    setMilestones(targetGrade) {
        return [
            { grade: targetGrade, name: '当前年级', target: '稳固基础' },
            { grade: targetGrade + 1, name: '升学年级', target: '顺利升学' }
        ];
    }

    // 建议资源
    suggestResources(assessment) {
        return {
            courses: ['基础巩固课程', '专项提升课程'],
            materials: ['配套练习册', '历年真题'],
            tools: ['错题本', '学习计划表']
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
window.academicEvaluator = new AcademicEvaluator();

// 导出
window.MTSCOS_AcademicEvaluator = AcademicEvaluator;

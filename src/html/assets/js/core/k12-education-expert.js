/**
 * MTSCOS AI System - K12教育专家AI员工
 * 版本: 4.4.0
 * 描述: 专注于K12全学段（小学1-6年级、初中7-9年级）教育管理和学业规划
 */

class K12EducationExpert {
    constructor() {
        this.id = 'k12-education-expert';
        this.name = 'K12教育专家';
        this.icon = 'fa-school';
        this.color = '#2563eb';
        this.gradient = 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)';
        this.role = 'K12教育专家';
        this.description = '专注于K12全学段教育管理、学业规划、升学指导和素质教育评估';
        this.abilities = [
            '学段管理',
            '学业规划',
            '升学指导',
            '素质教育',
            '课程设计',
            '教学评估'
        ];
        this.status = 'active';
        this.workload = 25;
        this.efficiency = 95;
        this.grades = this.initGrades();
        this.phases = ['小学', '初中'];
    }

    // ==================== 学段配置 ====================

    initGrades() {
        return {
            primary: {
                name: '小学',
                grades: [
                    { grade: 1, name: '一年级', age: 6, subjects: ['语文', '数学', '道德与法治'] },
                    { grade: 2, name: '二年级', age: 7, subjects: ['语文', '数学', '道德与法治'] },
                    { grade: 3, name: '三年级', age: 8, subjects: ['语文', '数学', '英语', '道德与法治', '科学'] },
                    { grade: 4, name: '四年级', age: 9, subjects: ['语文', '数学', '英语', '道德与法治', '科学'] },
                    { grade: 5, name: '五年级', age: 10, subjects: ['语文', '数学', '英语', '道德与法治', '科学'] },
                    { grade: 6, name: '六年级', age: 11, subjects: ['语文', '数学', '英语', '道德与法治', '科学'] }
                ],
                phase: 'primary'
            },
            junior: {
                name: '初中',
                grades: [
                    { grade: 7, name: '七年级', age: 12, subjects: ['语文', '数学', '英语', '道德与法治', '历史', '地理', '生物'] },
                    { grade: 8, name: '八年级', age: 13, subjects: ['语文', '数学', '英语', '道德与法治', '历史', '地理', '物理'] },
                    { grade: 9, name: '九年级', age: 14, subjects: ['语文', '数学', '英语', '道德与法治', '历史', '物理', '化学'] }
                ],
                phase: 'junior'
            }
        };
    }

    // ==================== 学段管理 ====================

    // 获取年级信息
    getGradeInfo(grade) {
        for (const [phase, data] of Object.entries(this.grades)) {
            const found = data.grades.find(g => g.grade === grade);
            if (found) {
                return {
                    ...found,
                    phase,
                    phaseName: data.name
                };
            }
        }
        return null;
    }

    // 判断学段
    getPhase(grade) {
        if (grade >= 1 && grade <= 6) return 'primary';
        if (grade >= 7 && grade <= 9) return 'junior';
        return null;
    }

    // 获取学段课程
    getPhaseCurriculum(phase) {
        const gradeList = this.grades[phase]?.grades || [];
        const subjects = new Set();
        
        gradeList.forEach(g => {
            g.subjects.forEach(s => subjects.add(s));
        });

        return {
            phase,
            name: this.grades[phase]?.name,
            grades: gradeList.map(g => g.name),
            subjects: Array.from(subjects)
        };
    }

    // ==================== 学业规划 ====================

    // 生成学业规划
    generateStudyPlan(studentId, currentGrade) {
        const phase = this.getPhase(currentGrade);
        const gradeInfo = this.getGradeInfo(currentGrade);

        return {
            studentId,
            currentGrade,
            phase,
            phaseName: gradeInfo?.name,
            shortTermGoals: this.generateShortTermGoals(currentGrade),
            longTermGoals: this.generateLongTermGoals(phase),
            subjectPriorities: this.getSubjectPriorities(currentGrade),
            recommendedStudyTime: this.calculateStudyTime(currentGrade),
            milestones: this.generateMilestones(currentGrade),
            createdAt: Date.now()
        };
    }

    // 生成短期目标
    generateShortTermGoals(grade) {
        return [
            { term: '本月', goal: '巩固基础知识，查漏补缺' },
            { term: '本学期', goal: '期中期末考试成绩达到班级前50%' },
            { term: '下学期', goal: '薄弱科目提升20%' }
        ];
    }

    // 生成长期目标
    generateLongTermGoals(phase) {
        if (phase === 'primary') {
            return [
                { term: '小升初', goal: '顺利升入理想初中' },
                { term: '初中入学', goal: '适应初中学习节奏' }
            ];
        } else {
            return [
                { term: '中考', goal: '考入重点高中' },
                { term: '高中学习', goal: '为高考打好基础' }
            ];
        }
    }

    // 获取科目优先级
    getSubjectPriorities(grade) {
        const priorities = {
            1: [{ subject: '语文', priority: 1 }, { subject: '数学', priority: 1 }],
            2: [{ subject: '语文', priority: 1 }, { subject: '数学', priority: 1 }],
            3: [{ subject: '语文', priority: 1 }, { subject: '数学', priority: 1 }, { subject: '英语', priority: 2 }],
            4: [{ subject: '语文', priority: 1 }, { subject: '数学', priority: 1 }, { subject: '英语', priority: 2 }],
            5: [{ subject: '数学', priority: 1 }, { subject: '语文', priority: 1 }, { subject: '英语', priority: 2 }],
            6: [{ subject: '数学', priority: 1 }, { subject: '语文', priority: 1 }, { subject: '英语', priority: 1 }],
            7: [{ subject: '数学', priority: 1 }, { subject: '语文', priority: 1 }, { subject: '英语', priority: 1 }],
            8: [{ subject: '数学', priority: 1 }, { subject: '物理', priority: 2 }, { subject: '英语', priority: 2 }],
            9: [{ subject: '数学', priority: 1 }, { subject: '物理', priority: 1 }, { subject: '化学', priority: 2 }, { subject: '英语', priority: 2 }]
        };
        return priorities[grade] || priorities[7];
    }

    // 计算学习时间
    calculateStudyTime(grade) {
        const baseTime = grade <= 3 ? 60 : grade <= 6 ? 90 : 120;
        return {
            daily: baseTime,
            weekly: baseTime * 5,
            subjectDistribution: {
                '语文': 0.3,
                '数学': 0.35,
                '英语': 0.2,
                '其他': 0.15
            }
        };
    }

    // 生成里程碑
    generateMilestones(grade) {
        const milestones = [];
        const phase = this.getPhase(grade);
        const endGrade = phase === 'primary' ? 6 : 9;

        for (let g = grade; g <= endGrade; g++) {
            milestones.push({
                grade: g,
                name: this.getGradeInfo(g)?.name,
                keyTasks: this.getGradeKeyTasks(g),
                target: g === grade ? '当前' : `升入${this.getGradeInfo(g)?.name}`
            });
        }

        return milestones;
    }

    // 获取年级关键任务
    getGradeKeyTasks(grade) {
        const tasks = {
            1: ['适应小学生活', '养成良好学习习惯', '掌握基础拼音和计算'],
            2: ['提升阅读能力', '加强口算速度', '培养英语兴趣'],
            3: ['开始英语学习', '应用题思维培养', '科学探索启蒙'],
            4: ['学科分化意识', '阅读理解提升', '实验操作能力'],
            5: ['小升初准备', '思维深化', '自主学习能力'],
            6: ['小升初冲刺', '初中预习', '学习习惯固化'],
            7: ['适应初中节奏', '养成理科思维', '英语能力提升'],
            8: ['物理新增', '两极分化应对', '中考准备启动'],
            9: ['中考冲刺', '化学学习', '升学规划']
        };
        return tasks[grade] || [];
    }

    // ==================== 升学指导 ====================

    // 升学评估
    assessUpgradeEligibility(studentId, currentGrade, scores) {
        const phase = this.getPhase(currentGrade);
        const avgScore = scores.average || 60;

        const assessment = {
            studentId,
            currentGrade,
            phase,
            eligible: true,
            status: 'normal',
            recommendation: '',
            suggestions: []
        };

        // 判断是否可以升级
        if (avgScore < 60) {
            assessment.eligible = false;
            assessment.status = '需要补考';
            assessment.recommendation = '建议参加补考或留级';
            assessment.suggestions = [
                '加强基础知识学习',
                '参加课后辅导',
                '与老师沟通学习困难'
            ];
        } else if (avgScore < 75) {
            assessment.status = '良好';
            assessment.recommendation = '可以正常升级，需注意薄弱科目';
            assessment.suggestions = this.getWeaknessSuggestions(scores);
        } else if (avgScore >= 90) {
            assessment.status = '优秀';
            assessment.recommendation = '表现优异，可考虑拓展学习';
            assessment.suggestions = [
                '参加学科竞赛',
                '尝试更高难度内容',
                '发展兴趣爱好'
            ];
        }

        return assessment;
    }

    // 获取薄弱科目建议
    getWeaknessSuggestions(scores) {
        const suggestions = [];
        const weakSubjects = Object.entries(scores)
            .filter(([k, v]) => k !== 'average' && v < 70)
            .map(([k]) => k);

        weakSubjects.forEach(subject => {
            suggestions.push(`重点加强${subject}学习`);
        });

        return suggestions;
    }

    // ==================== 素质教育评估 ====================

    // 素质教育评估
    assessQualityEducation(studentId, data) {
        return {
            studentId,
            dimensions: {
                moral: { score: data.moral || 80, level: '优秀' },
                intellectual: { score: data.intellectual || 75, level: '良好' },
                physical: { score: data.physical || 85, level: '优秀' },
                aesthetic: { score: data.aesthetic || 70, level: '良好' },
                labor: { score: data.labor || 75, level: '良好' }
            },
            overallLevel: this.calculateOverallLevel(data),
            suggestions: this.generateQualitySuggestions(data),
            evaluatedAt: Date.now()
        };
    }

    // 计算整体等级
    calculateOverallLevel(data) {
        const scores = Object.values(data).filter(v => typeof v === 'number');
        const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
        
        if (avg >= 90) return '全优';
        if (avg >= 80) return '优秀';
        if (avg >= 70) return '良好';
        if (avg >= 60) return '及格';
        return '需努力';
    }

    // 生成素质教育建议
    generateQualitySuggestions(data) {
        const suggestions = [];
        
        if (data.moral < 80) suggestions.push('加强品德教育，培养正确价值观');
        if (data.physical < 80) suggestions.push('加强体育锻炼，提高身体素质');
        if (data.aesthetic < 80) suggestions.push('发展艺术兴趣，提升审美能力');
        if (data.labor < 80) suggestions.push('增加劳动实践，培养动手能力');
        
        return suggestions;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            phases: this.phases,
            grades: '1-9年级'
        };
    }
}

// 创建全局实例
window.k12EducationExpert = new K12EducationExpert();

// 导出
window.MTSCOS_K12EducationExpert = K12EducationExpert;

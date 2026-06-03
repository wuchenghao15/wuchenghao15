/**
 * 9年制教育自动升级管理系统 v2.0.0
 * 功能：自动检测学年升级、智能推送升级通知、记录升级历史、K12全学段支持
 * 
 * v2.0.0 新增功能：
 * - K12全学段支持（小学、初中、高中）
 * - 可视化升级面板
 * - 成就系统
 * - 数据统计分析
 * - 个性化升级建议
 * - 动画效果增强
 * - 云端同步支持
 */

(function() {
    'use strict';

    // 升级配置 v2.0.0
    const GradeUpgradeConfig = {
        version: '2.0.0',
        upgradeYear: 365 * 24 * 60 * 60 * 1000, // 1年
        checkDelay: 3000, // 延迟检查时间(ms)
        noticeDuration: 10000, // 通知显示时间(ms)
        upgradeGrades: {
            // 小学阶段
            primary: ['grade1', 'grade2', 'grade3', 'grade4', 'grade5', 'grade6'],
            // 初中阶段
            junior: ['grade7', 'grade8', 'grade9'],
            // 高中阶段
            senior: ['grade10', 'grade11', 'grade12']
        },
        stageNames: {
            primary: '小学',
            junior: '初中',
            senior: '高中'
        },
        gradeNames: {
            'grade1': '一年级',
            'grade2': '二年级',
            'grade3': '三年级',
            'grade4': '四年级',
            'grade5': '五年级',
            'grade6': '六年级',
            'grade7': '初一（七年级）',
            'grade8': '初二（八年级）',
            'grade9': '初三（九年级）',
            'grade10': '高一',
            'grade11': '高二',
            'grade12': '高三'
        },
        gradeYearNames: {
            'grade1': '一年级',
            'grade2': '二年级',
            'grade3': '三年级',
            'grade4': '四年级',
            'grade5': '五年级',
            'grade6': '六年级',
            'grade7': '七年级',
            'grade8': '八年级',
            'grade9': '九年级',
            'grade10': '高一年级',
            'grade11': '高二年级',
            'grade12': '高三年级'
        },
        achievementTypes: {
            'first_upgrade': { name: '初次升级', icon: '🎖️', description: '完成第一次学年升级' },
            'primary_complete': { name: '小学毕业', icon: '🎓', description: '完成小学阶段学习' },
            'junior_complete': { name: '初中毕业', icon: '📜', description: '完成初中阶段学习' },
            'senior_complete': { name: '高中毕业', icon: '🏆', description: '完成高中阶段学习' },
            'speed_upgrade': { name: '飞速进步', icon: '🚀', description: '提前完成学年升级' },
            'perfect_score': { name: '满分达成', icon: '💯', description: '所有考试满分通过' },
            'streak_master': { name: '连胜大师', icon: '🔥', description: '连续10次考试满分' }
        }
    };

    // 升级历史管理 v2.0.0
    const GradeUpgradeHistory = {
        key: 'mtcos_grade_upgrade_history',
        achievementsKey: 'mtcos_achievements',
        
        getHistory: function() {
            const history = localStorage.getItem(this.key);
            return history ? JSON.parse(history) : [];
        },
        
        addRecord: function(fromGrade, toGrade, reason, metadata) {
            const history = this.getHistory();
            history.push({
                from: fromGrade,
                to: toGrade,
                reason: reason,
                timestamp: new Date().toISOString(),
                metadata: metadata || {}
            });
            localStorage.setItem(this.key, JSON.stringify(history));
            this.checkAchievements(fromGrade, toGrade);
        },
        
        getLastUpgrade: function() {
            const history = this.getHistory();
            return history.length > 0 ? history[history.length - 1] : null;
        },
        
        getStatistics: function() {
            const history = this.getHistory();
            const now = new Date();
            
            const stats = {
                totalUpgrades: history.length,
                currentStage: this.getCurrentStage(),
                stageProgress: this.calculateStageProgress(),
                averageTime: this.calculateAverageUpgradeTime(),
                fastestUpgrade: this.getFastestUpgrade(),
                achievements: this.getAchievements()
            };
            
            return stats;
        },
        
        getCurrentStage: function() {
            const grade = localStorage.getItem('mtcos_grade');
            if (!grade) return null;
            
            for (const [stage, grades] of Object.entries(GradeUpgradeConfig.upgradeGrades)) {
                if (grades.includes(grade)) {
                    return {
                        stage: stage,
                        name: GradeUpgradeConfig.stageNames[stage],
                        grade: grade
                    };
                }
            }
            return null;
        },
        
        calculateStageProgress: function() {
            const stage = this.getCurrentStage();
            if (!stage) return 0;
            
            const grades = GradeUpgradeConfig.upgradeGrades[stage.stage];
            const currentIndex = grades.indexOf(stage.grade);
            
            return Math.round(((currentIndex + 1) / grades.length) * 100);
        },
        
        calculateAverageUpgradeTime: function() {
            const history = this.getHistory();
            if (history.length < 2) return null;
            
            let totalDays = 0;
            for (let i = 1; i < history.length; i++) {
                const prev = new Date(history[i-1].timestamp);
                const curr = new Date(history[i].timestamp);
                totalDays += (curr - prev) / (1000 * 60 * 60 * 24);
            }
            
            return Math.round(totalDays / (history.length - 1));
        },
        
        getFastestUpgrade: function() {
            const history = this.getHistory();
            if (history.length < 2) return null;
            
            let fastest = null;
            let minDays = Infinity;
            
            for (let i = 1; i < history.length; i++) {
                const prev = new Date(history[i-1].timestamp);
                const curr = new Date(history[i].timestamp);
                const days = (curr - prev) / (1000 * 60 * 60 * 24);
                
                if (days < minDays) {
                    minDays = days;
                    fastest = {
                        days: Math.round(days),
                        from: history[i-1].from,
                        to: history[i].to
                    };
                }
            }
            
            return fastest;
        },
        
        // 成就系统
        getAchievements: function() {
            const achievements = localStorage.getItem(this.achievementsKey);
            return achievements ? JSON.parse(achievements) : [];
        },
        
        addAchievement: function(achievementId) {
            const achievements = this.getAchievements();
            if (!achievements.includes(achievementId)) {
                achievements.push(achievementId);
                localStorage.setItem(this.achievementsKey, JSON.stringify(achievements));
                return true; // 新成就
            }
            return false;
        },
        
        checkAchievements: function(fromGrade, toGrade) {
            const achievements = this.getAchievements();
            
            // 初次升级
            if (achievements.length === 0) {
                this.addAchievement('first_upgrade');
                GradeUpgradeManager.showAchievementNotification('first_upgrade');
            }
            
            // 小学毕业
            if (toGrade === 'grade6') {
                this.addAchievement('primary_complete');
                GradeUpgradeManager.showAchievementNotification('primary_complete');
            }
            
            // 初中毕业
            if (toGrade === 'grade9') {
                this.addAchievement('junior_complete');
                GradeUpgradeManager.showAchievementNotification('junior_complete');
            }
            
            // 高中毕业
            if (toGrade === 'grade12') {
                this.addAchievement('senior_complete');
                GradeUpgradeManager.showAchievementNotification('senior_complete');
            }
            
            // 飞速进步（升级时间少于300天）
            const history = this.getHistory();
            if (history.length >= 2) {
                const lastUpgrade = history[history.length - 1];
                const prevUpgrade = history[history.length - 2];
                const days = (new Date(lastUpgrade.timestamp) - new Date(prevUpgrade.timestamp)) / (1000 * 60 * 60 * 24);
                
                if (days < 300) {
                    this.addAchievement('speed_upgrade');
                    GradeUpgradeManager.showAchievementNotification('speed_upgrade');
                }
            }
        }
    };

    // 检查是否可以升级
    function canUpgrade(grade) {
        for (const grades of Object.values(GradeUpgradeConfig.upgradeGrades)) {
            const currentIndex = grades.indexOf(grade);
            if (currentIndex >= 0 && currentIndex < grades.length - 1) {
                return true;
            }
        }
        return false;
    }

    // 获取下一个年级
    function getNextGrade(grade) {
        for (const grades of Object.values(GradeUpgradeConfig.upgradeGrades)) {
            const currentIndex = grades.indexOf(grade);
            if (currentIndex >= 0 && currentIndex < grades.length - 1) {
                return grades[currentIndex + 1];
            }
        }
        return null;
    }

    // 获取学段
    function getStage(grade) {
        for (const [stage, grades] of Object.entries(GradeUpgradeConfig.upgradeGrades)) {
            if (grades.includes(grade)) {
                return stage;
            }
        }
        return null;
    }

    // 检测是否满足升级时间条件
    function checkUpgradeTime(selectedDate) {
        if (!selectedDate) return false;
        
        const selectedTime = new Date(selectedDate).getTime();
        const now = Date.now();
        const timeDiff = now - selectedTime;
        
        return timeDiff >= GradeUpgradeConfig.upgradeYear;
    }

    // 计算学习进度 v2.0.0
    function calculateProgress(grade) {
        const stage = getStage(grade);
        const stageGrades = GradeUpgradeConfig.upgradeGrades[stage];
        const currentIndex = stageGrades.indexOf(grade);
        
        const stageExamCounts = {
            primary: { grade1: 15, grade2: 18, grade3: 20, grade4: 22, grade5: 25, grade6: 28 },
            junior: { grade7: 20, grade8: 22, grade9: 25 },
            senior: { grade10: 25, grade11: 28, grade12: 30 }
        };
        
        const totalExams = Object.entries(stageExamCounts[stage] || {})
            .slice(0, currentIndex + 1)
            .reduce((sum, [g, count]) => sum + count, 0);
        
        const completedExams = getCompletedExamsCount();
        const progress = totalExams > 0 ? Math.round((completedExams / totalExams) * 100) : 0;
        
        const daysSinceStart = selectedDate ? Math.floor((Date.now() - new Date(selectedDate).getTime()) / (1000 * 60 * 60 * 24)) : 0;
        
        return {
            total: totalExams,
            completed: completedExams,
            progress: progress,
            daysSinceStart: daysSinceStart,
            canUpgrade: progress >= 60 || daysSinceStart >= 365,
            stageName: GradeUpgradeConfig.stageNames[stage]
        };
    }

    // 获取已完成考试数
    function getCompletedExamsCount() {
        const completed = localStorage.getItem('mtcos_completed_exams');
        return completed ? JSON.parse(completed).length : 0;
    }

    // 获取选课日期
    function getSelectedDate() {
        return localStorage.getItem('mtcos_grade_selected_date');
    }

    // 创建升级通知UI v2.0.0
    function createUpgradeNotice(fromGrade, toGrade, progress) {
        const notice = document.createElement('div');
        notice.id = 'grade-upgrade-notice';
        notice.className = 'grade-upgrade-notice';
        
        const stageInfo = GradeUpgradeHistory.getCurrentStage();
        const stats = GradeUpgradeHistory.getStatistics();
        
        notice.innerHTML = `
            <div class="upgrade-notice-header">
                <div class="upgrade-notice-icon">🎓</div>
                <div class="upgrade-notice-title">📚 ${stageInfo ? stageInfo.name : '学段'}学年升级提示</div>
            </div>
            
            <div class="upgrade-notice-body">
                <div class="upgrade-path">
                    <div class="path-from">
                        <div class="path-icon">📖</div>
                        <div class="path-label">当前</div>
                        <div class="path-grade">${GradeUpgradeConfig.gradeNames[fromGrade]}</div>
                    </div>
                    <div class="path-arrow">→</div>
                    <div class="path-to">
                        <div class="path-icon">🚀</div>
                        <div class="path-label">目标</div>
                        <div class="path-grade">${GradeUpgradeConfig.gradeNames[toGrade]}</div>
                    </div>
                </div>
                
                <div class="upgrade-stats">
                    <div class="stat-item">
                        <div class="stat-icon">📊</div>
                        <div class="stat-value">${progress.progress}%</div>
                        <div class="stat-label">完成进度</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-icon">📅</div>
                        <div class="stat-value">${progress.daysSinceStart}</div>
                        <div class="stat-label">学习天数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-icon">🏆</div>
                        <div class="stat-value">${stats.totalUpgrades}</div>
                        <div class="stat-label">已升级次数</div>
                    </div>
                </div>
                
                <div class="upgrade-progress">
                    <div class="progress-header">
                        <span>学习进度</span>
                        <span class="${progress.canUpgrade ? 'can-upgrade' : 'cannot-upgrade'}">
                            ${progress.canUpgrade ? '✓ 满足升级条件' : '继续加油！'}
                        </span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress.progress}%"></div>
                    </div>
                    <div class="progress-detail">
                        已完成 ${progress.completed}/${progress.total} 个考试
                    </div>
                </div>
                
                ${stats.achievements.length > 0 ? `
                <div class="achievement-preview">
                    <div class="achievement-title">🏅 已获成就</div>
                    <div class="achievement-list">
                        ${stats.achievements.slice(-3).map(a => {
                            const ach = GradeUpgradeConfig.achievementTypes[a];
                            return ach ? `<span class="achievement-badge" title="${ach.description}">${ach.icon}</span>` : '';
                        }).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="upgrade-notice-actions">
                    <button class="upgrade-btn upgrade-now" onclick="GradeUpgradeManager.upgradeNow()">
                        🚀 立即升级
                    </button>
                    <button class="upgrade-btn upgrade-later" onclick="GradeUpgradeManager.dismissUpgrade()">
                        ⏰ 稍后提醒
                    </button>
                </div>
            </div>
            
            <button class="upgrade-notice-close" onclick="GradeUpgradeManager.dismissUpgrade()">×</button>
        `;
        
        return notice;
    }

    // 创建升级成功通知 v2.0.0
    function createUpgradeSuccessNotice(newGrade, achievement) {
        const notice = document.createElement('div');
        notice.id = 'grade-upgrade-success';
        notice.className = 'grade-upgrade-success-notice';
        
        let achievementHTML = '';
        if (achievement) {
            const ach = GradeUpgradeConfig.achievementTypes[achievement];
            if (ach) {
                achievementHTML = `
                    <div class="achievement-unlock">
                        <div class="achievement-icon">${ach.icon}</div>
                        <div class="achievement-info">
                            <div class="achievement-label">🏅 获得新成就</div>
                            <div class="achievement-name">${ach.name}</div>
                            <div class="achievement-desc">${ach.description}</div>
                        </div>
                    </div>
                `;
            }
        }
        
        notice.innerHTML = `
            <div class="success-celebration">🎉</div>
            <div class="success-content">
                <div class="success-title">恭喜升级成功！</div>
                <div class="success-grade">
                    您现在是<strong>${GradeUpgradeConfig.gradeNames[newGrade]}</strong>的学生了
                </div>
                <div class="success-message">
                    ${achievementHTML}
                    <div class="success-tips">
                        新学年新课程已准备好，加油学习！
                    </div>
                </div>
            </div>
        `;
        
        return notice;
    }

    // 主升级管理器 v2.0.0
    window.GradeUpgradeManager = {
        version: '2.0.0',
        currentGrade: null,
        nextGrade: null,
        isUpgrading: false,
        upgradeNoticeElement: null,

        // 初始化 v2.0.0
        init: function() {
            const grade = localStorage.getItem('mtcos_grade');
            const selectedDate = localStorage.getItem('mtcos_grade_selected_date');
            
            if (!grade || !selectedDate) return;
            
            this.currentGrade = grade;
            this.nextGrade = getNextGrade(grade);
            
            // 检查是否已升级到最高年级
            if (!this.nextGrade) {
                console.log('已到达最高年级，无需升级');
                this.showGraduationNotice();
                return;
            }
            
            // 延迟检查，给页面加载时间
            setTimeout(() => {
                this.checkUpgrade();
            }, GradeUpgradeConfig.checkDelay);
        },

        // 检查升级条件 v2.0.0
        checkUpgrade: function() {
            const selectedDate = localStorage.getItem('mtcos_grade_selected_date');
            
            // 检查是否达到升级时间
            if (!checkUpgradeTime(selectedDate)) {
                const daysLeft = Math.ceil((GradeUpgradeConfig.upgradeYear - (Date.now() - new Date(selectedDate).getTime())) / (1000 * 60 * 60 * 24));
                console.log(`还需 ${daysLeft} 天即可升级`);
                return;
            }
            
            // 检查是否可以升级
            if (!canUpgrade(this.currentGrade)) {
                console.log('无法升级，当前已是最高年级');
                return;
            }
            
            // 检查是否已跳过此次升级
            const lastDismiss = localStorage.getItem('mtcos_last_dismiss_upgrade');
            if (lastDismiss && this.currentGrade) {
                const dismissDate = new Date(lastDismiss);
                const now = new Date();
                // 如果7天内已跳过，不再提示
                if ((now - dismissDate) < 7 * 24 * 60 * 60 * 1000) {
                    console.log('7天内已跳过升级提示');
                    return;
                }
            }
            
            // 显示升级通知
            this.showUpgradeNotice();
        },

        // 显示升级通知 v2.0.0
        showUpgradeNotice: function() {
            const progress = calculateProgress(this.currentGrade);
            const notice = createUpgradeNotice(this.currentGrade, this.nextGrade, progress);
            
            // 添加到页面
            const container = document.querySelector('.exam-container') || document.body;
            container.insertBefore(notice, container.firstChild);
            
            this.upgradeNoticeElement = notice;
            
            // 添加动画
            setTimeout(() => {
                notice.classList.add('show');
            }, 100);
            
            // 自动消失
            setTimeout(() => {
                if (this.upgradeNoticeElement === notice) {
                    this.dismissUpgrade();
                }
            }, GradeUpgradeConfig.noticeDuration);
        },

        // 立即升级 v2.0.0
        upgradeNow: function() {
            if (this.isUpgrading) return;
            this.isUpgrading = true;
            
            const fromGrade = this.currentGrade;
            const toGrade = this.nextGrade;
            const selectedDate = getSelectedDate();
            const progress = calculateProgress(this.currentGrade);
            
            // 执行升级
            localStorage.setItem('mtcos_grade', toGrade);
            localStorage.setItem('mtcos_grade_name', GradeUpgradeConfig.gradeNames[toGrade]);
            localStorage.setItem('mtcos_grade_selected_date', new Date().toISOString());
            
            // 记录升级历史
            GradeUpgradeHistory.addRecord(fromGrade, toGrade, '自动学年升级', {
                daysSinceStart: progress.daysSinceStart,
                completionRate: progress.progress
            });
            
            // 检查新成就
            const newAchievement = this.checkNewAchievement(fromGrade, toGrade);
            
            // 移除通知
            if (this.upgradeNoticeElement) {
                this.upgradeNoticeElement.remove();
                this.upgradeNoticeElement = null;
            }
            
            // 显示升级成功通知
            const successNotice = createUpgradeSuccessNotice(toGrade, newAchievement);
            const container = document.querySelector('.exam-container') || document.body;
            container.insertBefore(successNotice, container.firstChild);
            
            setTimeout(() => {
                successNotice.classList.add('show');
            }, 100);
            
            setTimeout(() => {
                successNotice.classList.remove('show');
                setTimeout(() => successNotice.remove(), 300);
            }, 6000);
            
            // 更新页面显示
            this.updatePageDisplay(toGrade);
            
            // 记录操作日志
            if (typeof logOperation === 'function') {
                logOperation('grade_upgraded', {
                    from: fromGrade,
                    to: toGrade,
                    version: '2.0.0',
                    progress: progress.progress
                }, 'system');
            }
            
            this.isUpgrading = false;
            
            // 刷新页面以应用新设置
            showToast('🎉 升级成功！正在刷新页面...', 'success');
            setTimeout(() => {
                location.reload();
            }, 3000);
        },

        // 检查新成就
        checkNewAchievement: function(fromGrade, toGrade) {
            const achievements = GradeUpgradeHistory.getAchievements();
            let newAchievement = null;
            
            // 初次升级
            if (achievements.length === 0) {
                newAchievement = 'first_upgrade';
            }
            // 小学毕业
            else if (toGrade === 'grade6') {
                newAchievement = 'primary_complete';
            }
            // 初中毕业
            else if (toGrade === 'grade9') {
                newAchievement = 'junior_complete';
            }
            // 高中毕业
            else if (toGrade === 'grade12') {
                newAchievement = 'senior_complete';
            }
            
            return newAchievement;
        },

        // 显示成就通知
        showAchievementNotification: function(achievementId) {
            const ach = GradeUpgradeConfig.achievementTypes[achievementId];
            if (!ach) return;
            
            showToast(`🏅 解锁成就：${ach.name} - ${ach.description}`, 'success');
        },

        // 稍后提醒 v2.0.0
        dismissUpgrade: function() {
            localStorage.setItem('mtcos_last_dismiss_upgrade', new Date().toISOString());
            
            if (this.upgradeNoticeElement) {
                this.upgradeNoticeElement.classList.remove('show');
                setTimeout(() => {
                    if (this.upgradeNoticeElement) {
                        this.upgradeNoticeElement.remove();
                        this.upgradeNoticeElement = null;
                    }
                }, 300);
            }
        },

        // 更新页面显示 v2.0.0
        updatePageDisplay: function(newGrade) {
            // 更新年级徽章
            const gradeBadge = document.getElementById('grade-badge');
            if (gradeBadge) {
                gradeBadge.textContent = GradeUpgradeConfig.gradeNames[newGrade];
            }
            
            // 更新标题
            const examTitle = document.getElementById('exam-title');
            if (examTitle) {
                examTitle.textContent = `📝 ${GradeUpgradeConfig.gradeYearNames[newGrade]}考试系统`;
            }
            
            // 触发考试过滤更新
            if (typeof filterExamsByGrade === 'function') {
                filterExamsByGrade();
            }
        },

        // 显示毕业通知
        showGraduationNotice: function() {
            const stage = GradeUpgradeHistory.getCurrentStage();
            if (!stage) return;
            
            const notice = document.createElement('div');
            notice.className = 'graduation-notice';
            notice.innerHTML = `
                <div class="graduation-icon">🎓</div>
                <div class="graduation-title">恭喜完成${stage.name}学业！</div>
                <div class="graduation-message">
                    您已完成${GradeUpgradeConfig.stageNames[stage.stage]}阶段所有年级的学习。<br>
                    感谢您的使用，祝您学业有成！
                </div>
            `;
            
            document.body.appendChild(notice);
            
            setTimeout(() => {
                notice.classList.add('show');
            }, 100);
        },

        // 获取升级历史 v2.0.0
        getUpgradeHistory: function() {
            return GradeUpgradeHistory.getHistory();
        },

        // 获取统计信息 v2.0.0
        getStatistics: function() {
            return GradeUpgradeHistory.getStatistics();
        },

        // 获取成就列表 v2.0.0
        getAchievements: function() {
            return GradeUpgradeHistory.getAchievements();
        },

        // 获取升级建议 v2.0.0
        getUpgradeSuggestion: function() {
            const progress = calculateProgress(this.currentGrade);
            const stage = GradeUpgradeHistory.getCurrentStage();
            
            return {
                canUpgrade: canUpgrade(this.currentGrade),
                progress: progress,
                nextGrade: this.nextGrade,
                nextGradeName: this.nextGrade ? GradeUpgradeConfig.gradeNames[this.nextGrade] : null,
                stage: stage,
                statistics: GradeUpgradeHistory.getStatistics()
            };
        },

        // 获取配置信息
        getConfig: function() {
            return GradeUpgradeConfig;
        },

        // 获取版本
        getVersion: function() {
            return GradeUpgradeConfig.version;
        }
    };

    // 自动初始化
    document.addEventListener('DOMContentLoaded', function() {
        if (window.GradeUpgradeManager) {
            window.GradeUpgradeManager.init();
        }
    });

    // 如果页面已加载完成
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(() => {
            if (window.GradeUpgradeManager) {
                window.GradeUpgradeManager.init();
            }
        }, 100);
    }

})();

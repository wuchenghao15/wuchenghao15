/**
 * 9年制学生升级管理系统 - 前端JavaScript模块
 * 包含完整的升级逻辑、考试管理、权限控制
 * 版本: 1.1 - 从小学1年级开始的完整9年制体系
 */

class NineYearUpgradeManager {
    constructor() {
        this.currentUser = null;
        this.currentGrade = null;
        this.gradeStatus = null;
        this.permissionLevel = null;
        this.API_BASE = 'http://localhost:5002/api/nine-year';
    }

    /**
     * 初始化系统
     */
    async init() {
        await this.loadUserInfo();
        await this.checkGradeStatus();
        this.setupEventListeners();
        this.updateUIByPermission();
    }

    /**
     * 加载用户信息
     */
    async loadUserInfo() {
        this.currentUser = localStorage.getItem('mtcos_username');
        this.currentGrade = localStorage.getItem('mtcos_grade');
        this.gradeStatus = localStorage.getItem('mtcos_grade_status') || 'normal';
        this.permissionLevel = parseInt(localStorage.getItem('mtcos_permission_level')) || 20;

        if (!this.currentUser) {
            console.error('用户未登录');
            return false;
        }

        return true;
    }

    /**
     * 检查年级状态
     */
    async checkGradeStatus() {
        if (!this.currentUser) return;

        try {
            const response = await fetch(`${this.API_BASE}/status/${this.currentUser}`);
            const result = await response.json();

            if (result.success && result.data) {
                this.updateLocalStatus(result.data);
            }
        } catch (error) {
            console.error('获取状态失败:', error);
        }
    }

    /**
     * 更新本地状态
     */
    updateLocalStatus(data) {
        if (data.grade_info) {
            localStorage.setItem('mtcos_grade', data.grade_info.current_grade);
            localStorage.setItem('mtcos_grade_status', data.grade_info.grade_status);
            localStorage.setItem('mtcos_permission_level', data.grade_info.permission_level);

            this.currentGrade = data.grade_info.current_grade;
            this.gradeStatus = data.grade_info.grade_status;
            this.permissionLevel = data.grade_info.permission_level;
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 年级选择
        document.querySelectorAll('.grade-option').forEach(option => {
            option.addEventListener('click', (e) => this.selectGrade(e));
        });

        // 确认年级按钮
        const confirmBtn = document.getElementById('grade-confirm-btn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.confirmGrade());
        }

        // 开始考试按钮
        document.querySelectorAll('.start-exam-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.startExam(e));
        });

        // 暂停考试申请
        document.querySelectorAll('.pause-exam-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.requestPauseExam(e));
        });

        // 提交考试
        document.querySelectorAll('.submit-exam-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.submitExam(e));
        });
    }

    /**
     * 显示年级选择模态框
     */
    showGradeSelectModal() {
        const modal = document.getElementById('grade-select-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    /**
     * 隐藏年级选择模态框
     */
    hideGradeSelectModal() {
        const modal = document.getElementById('grade-select-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * 选择年级
     */
    selectGrade(event) {
        const grade = event.currentTarget.dataset.grade;

        // 移除其他选中状态
        document.querySelectorAll('.grade-option').forEach(opt => {
            opt.classList.remove('selected');
        });

        // 添加选中状态
        event.currentTarget.classList.add('selected');

        // 启用确认按钮
        const confirmBtn = document.getElementById('grade-confirm-btn');
        if (confirmBtn) {
            confirmBtn.disabled = false;
        }

        // 保存选择的年级
        this.pendingGrade = grade;
    }

    /**
     * 确认年级选择
     */
    async confirmGrade() {
        if (!this.pendingGrade) {
            alert('请先选择年级');
            return;
        }

        try {
            // 首先注册年级
            const registerResponse = await fetch(`${this.API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser,
                    grade: this.pendingGrade
                })
            });

            const registerResult = await registerResponse.json();

            if (registerResult.success) {
                // 然后确认年级
                const confirmResponse = await fetch(`${this.API_BASE}/confirm/${this.currentUser}`, {
                    method: 'POST'
                });

                const confirmResult = await confirmResponse.json();

                if (confirmResult.success) {
                    // 保存到本地
                    localStorage.setItem('mtcos_grade', this.pendingGrade);
                    localStorage.setItem('mtcos_grade_status', 'normal');
                    localStorage.setItem('mtcos_permission_level', '20');
                    localStorage.setItem('mtcos_grade_selected_date', new Date().toISOString());

                    this.currentGrade = this.pendingGrade;
                    this.gradeStatus = 'normal';
                    this.permissionLevel = 20;

                    this.hideGradeSelectModal();
                    this.updateGradeDisplay();
                    this.updateUIByPermission();

                    alert('年级选择成功！');
                    this.logOperation('grade_confirmed', { grade: this.pendingGrade }, 'system');
                } else {
                    alert('年级确认失败: ' + confirmResult.error);
                }
            } else {
                alert('年级注册失败: ' + registerResult.error);
            }
        } catch (error) {
            console.error('确认年级失败:', error);
            alert('确认年级失败，请重试');
        }
    }

    /**
     * 更新年级显示
     */
    updateGradeDisplay() {
        const gradeDisplay = document.getElementById('grade-display');
        if (gradeDisplay) {
            const gradeNames = {
                'grade1': '小学1年级',
                'grade2': '小学2年级',
                'grade3': '小学3年级',
                'grade4': '小学4年级',
                'grade5': '小学5年级',
                'grade6': '小学6年级',
                'grade7': '初中1年级',
                'grade8': '初中2年级',
                'grade9': '初中3年级'
            };
            gradeDisplay.textContent = gradeNames[this.currentGrade] || this.currentGrade;
        }
    }

    /**
     * 开始考试
     */
    async startExam(event) {
        const examId = event.currentTarget.dataset.examId;

        if (!this.checkPermission('exam')) {
            alert('您没有考试权限，请联系教师或管理员');
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE}/exam/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ exam_id: examId })
            });

            const result = await response.json();

            if (result.success) {
                alert('考试已开始！');
                this.loadExamContent(examId);
                this.logOperation('exam_started', { exam_id: examId }, 'exam');
            } else {
                alert('开始考试失败: ' + result.error);
            }
        } catch (error) {
            console.error('开始考试失败:', error);
            alert('开始考试失败，请重试');
        }
    }

    /**
     * 申请暂停考试
     */
    async requestPauseExam(event) {
        const examId = event.currentTarget.dataset.examId;
        const reason = prompt('请输入暂停考试的原因：');

        if (!reason) {
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE}/exam/pause-request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exam_id: examId,
                    user_id: this.currentUser,
                    reason: reason
                })
            });

            const result = await response.json();

            if (result.success) {
                alert('暂停申请已提交，请等待教师审批！');
                this.logOperation('pause_requested', { exam_id: examId, reason: reason }, 'exam');
            } else {
                alert('申请失败: ' + result.error);
            }
        } catch (error) {
            console.error('申请暂停失败:', error);
            alert('申请暂停失败，请重试');
        }
    }

    /**
     * 提交考试成绩
     */
    async submitExam(event) {
        const examId = event.currentTarget.dataset.examId;
        const score = prompt('请输入考试成绩：');

        if (!score || isNaN(score)) {
            alert('请输入有效的成绩');
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE}/exam/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exam_id: examId,
                    score: parseFloat(score)
                })
            });

            const result = await response.json();

            if (result.success) {
                alert(result.message);
                await this.checkUpgradeEligibility();
                this.logOperation('exam_submitted', { 
                    exam_id: examId, 
                    score: score,
                    status: result.status
                }, 'exam');
            } else {
                alert('提交失败: ' + result.error);
            }
        } catch (error) {
            console.error('提交成绩失败:', error);
            alert('提交成绩失败，请重试');
        }
    }

    /**
     * 检查升级资格
     */
    async checkUpgradeEligibility() {
        try {
            const response = await fetch(`${this.API_BASE}/upgrade-check/${this.currentUser}`);
            const result = await response.json();

            if (result.success) {
                this.displayUpgradeInfo(result.data);

                if (result.data.eligible) {
                    this.showUpgradeOption(result.data);
                }
            }
        } catch (error) {
            console.error('检查升级资格失败:', error);
        }
    }

    /**
     * 显示升级信息
     */
    displayUpgradeInfo(data) {
        const container = document.getElementById('upgrade-info-container');
        if (!container) return;

        const gradeNames = {
            'grade1': '小学1年级',
            'grade2': '小学2年级',
            'grade3': '小学3年级',
            'grade4': '小学4年级',
            'grade5': '小学5年级',
            'grade6': '小学6年级',
            'grade7': '初中1年级',
            'grade8': '初中2年级',
            'grade9': '初中3年级'
        };

        let html = `
            <div class="upgrade-info-card">
                <h3>📊 升级资格检查</h3>
                <div class="info-item">
                    <span class="label">当前年级:</span>
                    <span class="value">${gradeNames[data.current_grade] || data.current_grade}</span>
                </div>
                <div class="info-item">
                    <span class="label">升级状态:</span>
                    <span class="value ${data.eligible ? 'success' : 'warning'}">
                        ${data.eligible ? '✅ 符合升级条件' : '❌ 不符合升级条件'}
                    </span>
                </div>
                <div class="info-item">
                    <span class="label">原因:</span>
                    <span class="value">${data.reason}</span>
                </div>
        `;

        if (data.eligible && data.next_grade) {
            html += `
                <div class="info-item">
                    <span class="label">下一学年:</span>
                    <span class="value">${gradeNames[data.next_grade] || data.next_grade}</span>
                </div>
            `;
        }

        if (data.upgrade_type === 'conditional') {
            html += `
                <div class="warning-box">
                    ⚠️ 条件升级 - 需要完成额外学习任务
                </div>
            `;
        }

        if (data.restrictions) {
            html += `
                <div class="restrictions-box">
                    <h4>⚠️ 限制条件</h4>
                    <ul>
            `;
            data.restrictions.forEach(restriction => {
                html += `<li>${restriction}</li>`;
            });
            html += `
                    </ul>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * 显示升级选项
     */
    showUpgradeOption(data) {
        if (confirm(`您符合升级条件！是否申请升级到${this.getGradeName(data.next_grade)}？`)) {
            this.performUpgrade(data.upgrade_type);
        }
    }

    /**
     * 执行升级
     */
    async performUpgrade(upgradeType = 'normal') {
        try {
            const response = await fetch(`${this.API_BASE}/upgrade`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser,
                    upgrade_type: upgradeType
                })
            });

            const result = await response.json();

            if (result.success) {
                alert('升级成功！');
                this.logOperation('upgrade_completed', { 
                    upgrade_type: upgradeType 
                }, 'system');

                // 刷新页面
                window.location.reload();
            } else {
                alert('升级失败: ' + result.error);
            }
        } catch (error) {
            console.error('升级失败:', error);
            alert('升级失败，请重试');
        }
    }

    /**
     * 根据权限更新UI
     */
    updateUIByPermission() {
        // 考试系统访问
        const examSection = document.getElementById('exam-section');
        if (examSection) {
            if (this.permissionLevel < 10) {
                examSection.style.opacity = '0.5';
                examSection.querySelectorAll('button').forEach(btn => {
                    btn.disabled = true;
                });
            } else {
                examSection.style.opacity = '1';
                examSection.querySelectorAll('button').forEach(btn => {
                    btn.disabled = false;
                });
            }
        }

        // 学习系统访问
        const learningSection = document.getElementById('learning-section');
        if (learningSection) {
            if (this.gradeStatus === 'restricted') {
                // 仅显示复习内容
                learningSection.querySelectorAll('.advanced-content').forEach(el => {
                    el.style.display = 'none';
                });
            }
        }

        // 状态徽章更新
        this.updateStatusBadge();
    }

    /**
     * 更新状态徽章
     */
    updateStatusBadge() {
        const badge = document.getElementById('status-badge');
        if (!badge) return;

        const statusConfig = {
            'normal': { text: '正常', class: 'badge-success' },
            'conditional': { text: '条件升级', class: 'badge-warning' },
            'restricted': { text: '受限', class: 'badge-danger' },
            'suspended': { text: '已暂停', class: 'badge-info' },
            'repeating': { text: '留级', class: 'badge-secondary' },
            'graduated': { text: '已毕业', class: 'badge-primary' }
        };

        const config = statusConfig[this.gradeStatus] || statusConfig['normal'];
        badge.textContent = config.text;
        badge.className = `badge ${config.class}`;
    }

    /**
     * 检查权限
     */
    checkPermission(resource) {
        const permissionRules = {
            'exam': this.permissionLevel >= 10,
            'makeup': this.permissionLevel >= 10 && this.gradeStatus === 'restricted',
            'advanced_learning': this.permissionLevel >= 20,
            'upgrade_apply': this.permissionLevel >= 20,
            'admin': this.permissionLevel >= 80
        };

        return permissionRules[resource] || false;
    }

    /**
     * 获取年级名称
     */
    getGradeName(gradeCode) {
        const gradeNames = {
            'grade1': '小学1年级',
            'grade2': '小学2年级',
            'grade3': '小学3年级',
            'grade4': '小学4年级',
            'grade5': '小学5年级',
            'grade6': '小学6年级',
            'grade7': '初中1年级',
            'grade8': '初中2年级',
            'grade9': '初中3年级'
        };
        return gradeNames[gradeCode] || gradeCode;
    }

    /**
     * 记录操作日志
     */
    logOperation(operation, data, category) {
        const logData = {
            operation: operation,
            category: category,
            user_id: this.currentUser,
            data: data,
            timestamp: new Date().toISOString()
        };

        console.log('Operation:', logData);

        // 发送到服务器
        fetch(`${this.API_BASE}/log`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(logData)
        }).catch(err => console.error('日志记录失败:', err));
    }

    /**
     * 加载考试内容
     */
    loadExamContent(examId) {
        console.log('加载考试内容:', examId);
        // 这里实现考试内容加载逻辑
    }
}

// 创建全局实例
window.nineYearUpgradeManager = new NineYearUpgradeManager();

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否为9年制学生
    const studentType = localStorage.getItem('mtcos_studentType');
    if (studentType === 'nine_year' || studentType === 'nine_year_system') {
        window.nineYearUpgradeManager.init();
    }
});

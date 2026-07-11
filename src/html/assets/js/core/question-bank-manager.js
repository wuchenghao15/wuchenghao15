/**
 * MTSCOS AI System - 题库管理员AI员工
 * 版本: 4.4.0
 * 描述: 专注于题库管理、题目增删改查、题库刷新和状态同步
 */

class QuestionBankManager {
    constructor() {
        this.id = 'question-bank-manager';
        this.name = '题库管理员';
        this.icon = 'fa-database';
        this.color = '#06b6d4';
        this.gradient = 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)';
        this.role = '题库管理专家';
        this.description = '专注于题库管理、题目增删改查、题库刷新和状态同步';
        this.abilities = [
            '题库管理',
            '题目CRUD',
            '题库刷新',
            '状态同步',
            '题库统计',
            '题库导出'
        ];
        this.status = 'active';
        this.workload = 25;
        this.efficiency = 96;
        this.banks = {};
        this.expandStateCache = {};
    }

    // ==================== 题库管理 ====================

    // 获取所有题库
    async getAllBanks() {
        try {
            const response = await fetch('/api/banks');
            const data = await response.json();
            this.banks = data.reduce((acc, bank) => {
                acc[bank.id] = bank;
                return acc;
            }, {});
            return this.banks;
        } catch (error) {
            console.warn('获取题库失败:', error.message);
            return this.banks;
        }
    }

    // 获取单个题库
    async getBank(bankId) {
        if (this.banks[bankId]) {
            return this.banks[bankId];
        }
        try {
            const response = await fetch(`/api/banks/${bankId}`);
            const data = await response.json();
            this.banks[bankId] = data;
            return data;
        } catch (error) {
            console.warn('获取题库失败:', error.message);
            return null;
        }
    }

    // 创建题库
    async createBank(config) {
        const bank = {
            id: `bank_${Date.now()}`,
            name: config.name,
            description: config.description || '',
            subject: config.subject,
            grade: config.grade,
            questionCount: 0,
            createdAt: Date.now(),
            updatedAt: Date.now()
        };

        try {
            const response = await fetch('/api/banks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bank)
            });
            if (response.ok) {
                const created = await response.json();
                this.banks[bank.id] = created;
                await this.refreshBankTree();
                return created;
            }
        } catch (error) {
            console.warn('创建题库失败:', error.message);
        }
        return bank;
    }

    // 更新题库
    async updateBank(bankId, updates) {
        const bank = this.banks[bankId];
        if (!bank) return null;

        Object.assign(bank, updates, { updatedAt: Date.now() });

        try {
            const response = await fetch(`/api/banks/${bankId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bank)
            });
            if (response.ok) {
                await this.refreshBankTree();
            }
        } catch (error) {
            console.warn('更新题库失败:', error.message);
        }
        return bank;
    }

    // 删除题库
    async deleteBank(bankId) {
        try {
            const response = await fetch(`/api/banks/${bankId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                delete this.banks[bankId];
                delete this.expandStateCache[bankId];
                await this.refreshBankTree();
                return true;
            }
        } catch (error) {
            console.warn('删除题库失败:', error.message);
        }
        return false;
    }

    // ==================== 题目管理 ====================

    // 获取题目列表
    async getQuestions(bankId, params = {}) {
        const bank = await this.getBank(bankId);
        if (!bank) return [];

        try {
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`/api/banks/${bankId}/questions?${query}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('获取题目失败:', error.message);
            return [];
        }
    }

    // 添加题目
    async addQuestion(bankId, question) {
        const bank = await this.getBank(bankId);
        if (!bank) return null;

        const newQuestion = {
            id: `q_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            ...question,
            bankId,
            createdAt: Date.now(),
            updatedAt: Date.now()
        };

        try {
            const response = await fetch(`/api/banks/${bankId}/questions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newQuestion)
            });
            if (response.ok) {
                bank.questionCount++;
                bank.updatedAt = Date.now();
                await this.refreshBankTree();
                return await response.json();
            }
        } catch (error) {
            console.warn('添加题目失败:', error.message);
        }
        return newQuestion;
    }

    // 批量添加题目
    async addQuestions(bankId, questions) {
        const bank = await this.getBank(bankId);
        if (!bank) return [];

        const results = [];
        for (const question of questions) {
            const result = await this.addQuestion(bankId, question);
            if (result) results.push(result);
        }
        return results;
    }

    // 更新题目
    async updateQuestion(bankId, questionId, updates) {
        try {
            const response = await fetch(`/api/banks/${bankId}/questions/${questionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            if (response.ok) {
                const bank = this.banks[bankId];
                if (bank) bank.updatedAt = Date.now();
                return await response.json();
            }
        } catch (error) {
            console.warn('更新题目失败:', error.message);
        }
        return null;
    }

    // 删除题目
    async deleteQuestion(bankId, questionId) {
        try {
            const response = await fetch(`/api/banks/${bankId}/questions/${questionId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                const bank = this.banks[bankId];
                if (bank) {
                    bank.questionCount--;
                    bank.updatedAt = Date.now();
                }
                await this.refreshBankTree();
                return true;
            }
        } catch (error) {
            console.warn('删除题目失败:', error.message);
        }
        return false;
    }

    // 清空题库
    async clearBankQuestions(bankId) {
        const bank = await this.getBank(bankId);
        if (!bank) return false;

        try {
            const response = await fetch(`/api/banks/${bankId}/questions`, {
                method: 'DELETE'
            });
            if (response.ok) {
                bank.questionCount = 0;
                bank.updatedAt = Date.now();
                await this.refreshBankTree();
                return true;
            }
        } catch (error) {
            console.warn('清空题库失败:', error.message);
        }

        try {
            const questions = await this.getQuestions(bankId);
            for (const q of questions) {
                await this.deleteQuestion(bankId, q.id);
            }
            bank.questionCount = 0;
            bank.updatedAt = Date.now();
            await this.refreshBankTree();
            return true;
        } catch (e) {
            console.warn('清空题库降级方案失败:', e.message);
            return false;
        }
    }

    // ==================== 题库刷新 ====================

    // 统一刷新入口
    async refreshBankTree() {
        await this.getAllBanks();
        this.notifyRefresh();
    }

    // 通知刷新
    notifyRefresh() {
        const event = new CustomEvent('bankTreeRefreshed', {
            detail: { banks: this.banks, timestamp: Date.now() }
        });
        document.dispatchEvent(event);
    }

    // ==================== 展开状态管理 ====================

    // 设置展开状态
    setExpandState(bankId, state) {
        this.expandStateCache[bankId] = state;
        localStorage.setItem(`bank_expand_${bankId}`, JSON.stringify(state));
    }

    // 获取展开状态
    getExpandState(bankId, defaultValue = false) {
        const cached = this.expandStateCache[bankId];
        if (cached !== undefined) return cached;

        const stored = localStorage.getItem(`bank_expand_${bankId}`);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                this.expandStateCache[bankId] = parsed;
                return parsed;
            } catch (e) {
                console.warn('解析展开状态失败:', e.message);
            }
        }

        return defaultValue;
    }

    // 清除展开状态
    clearExpandState(bankId) {
        delete this.expandStateCache[bankId];
        localStorage.removeItem(`bank_expand_${bankId}`);
    }

    // 批量清除展开状态
    clearAllExpandStates() {
        this.expandStateCache = {};
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('bank_expand_')) {
                localStorage.removeItem(key);
            }
        });
    }

    // ==================== 题库统计 ====================

    // 获取题库统计
    getBankStats(bankId) {
        const bank = this.banks[bankId];
        if (!bank) return null;

        return {
            bankId: bank.id,
            name: bank.name,
            questionCount: bank.questionCount,
            subject: bank.subject,
            grade: bank.grade,
            createdAt: bank.createdAt,
            updatedAt: bank.updatedAt,
            status: bank.status || 'active'
        };
    }

    // 获取全局统计
    getGlobalStats() {
        const banks = Object.values(this.banks);
        const totalQuestions = banks.reduce((sum, b) => sum + (b.questionCount || 0), 0);
        
        return {
            totalBanks: banks.length,
            totalQuestions,
            subjects: banks.reduce((acc, b) => {
                acc[b.subject] = (acc[b.subject] || 0) + 1;
                return acc;
            }, {}),
            grades: banks.reduce((acc, b) => {
                acc[b.grade] = (acc[b.grade] || 0) + 1;
                return acc;
            }, {}),
            activeBanks: banks.filter(b => b.status === 'active').length
        };
    }

    // ==================== 题库导出 ====================

    // 导出题库
    exportBank(bankId, format = 'json') {
        const bank = this.banks[bankId];
        if (!bank) return null;

        const exportData = {
            id: bank.id,
            name: bank.name,
            description: bank.description,
            subject: bank.subject,
            grade: bank.grade,
            questionCount: bank.questionCount,
            exportedAt: Date.now()
        };

        if (format === 'json') {
            return JSON.stringify(exportData, null, 2);
        }
        if (format === 'csv') {
            return Object.entries(exportData).map(([k, v]) => `${k},${v}`).join('\n');
        }

        return null;
    }

    // 导入题库
    async importBank(data) {
        try {
            const bankData = typeof data === 'string' ? JSON.parse(data) : data;
            return await this.createBank(bankData);
        } catch (error) {
            console.warn('导入题库失败:', error.message);
            return null;
        }
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            bankCount: Object.keys(this.banks).length
        };
    }
}

// 创建全局实例
window.questionBankManager = new QuestionBankManager();

// 导出
window.MTSCOS_QuestionBankManager = QuestionBankManager;

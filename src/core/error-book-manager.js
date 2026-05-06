// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 错题本管理器
 * 记录用户错题，提供分析和AI优化功能
 */

class ErrorBookManager {
    constructor() {
        this.errorBook = this.loadErrorBook();
        this.setupEventListeners();
    }

    // 加载错题本
    loadErrorBook() {
        const savedErrorBook = localStorage.getItem('error_book');
        return savedErrorBook ? JSON.parse(savedErrorBook) : {
            totalErrors: 0,
            errorsByType: {},
            errorsByLevel: {},
            errorList: []
        };
    }

    // 保存错题本
    saveErrorBook() {
        localStorage.setItem('error_book', JSON.stringify(this.errorBook));
    }

    // 设置事件监听器
    setupEventListeners() {
        // 监听其他页面的错题记录事件
        window.addEventListener('error_recorded', (event) => {
            this.addError(event.detail);
        });
    }

    // 添加错题
    addError(errorData) {
        const {
            question,
            options,
            userAnswer,
            correctAnswer,
            type,
            level,
            tags = [],
            explanation = ''
        } = errorData;

        // 生成错题ID
        const errorId = Date.now() + Math.random().toString(36).substr(2, 9);

        // 创建错题记录
        const errorRecord = {
            id: errorId,
            question,
            options,
            userAnswer,
            correctAnswer,
            type,
            level,
            tags,
            explanation,
            recordedAt: new Date().toISOString(),
            reviewCount: 0,
            lastReviewedAt: null
        };

        // 添加到错题列表
        this.errorBook.errorList.push(errorRecord);

        // 更新统计信息
        this.errorBook.totalErrors++;

        // 更新按题型统计
        if (!this.errorBook.errorsByType[type]) {
            this.errorBook.errorsByType[type] = 0;
        }
        this.errorBook.errorsByType[type]++;

        // 更新按级别统计
        if (!this.errorBook.errorsByLevel[level]) {
            this.errorBook.errorsByLevel[level] = 0;
        }
        this.errorBook.errorsByLevel[level]++;

        // 保存错题本
        this.saveErrorBook();

        console.log(`✅ 错题已添加: ${question.substring(0, 30)}...`);

        // 触发错题记录事件
        window.dispatchEvent(new CustomEvent('error_added', {
            detail: errorRecord
        }));

        return errorId;
    }

    // 获取所有错题
    getAllErrors() {
        return this.errorBook.errorList;
    }

    // 根据题型获取错题
    getErrorsByType(type) {
        return this.errorBook.errorList.filter(error => error.type === type);
    }

    // 根据级别获取错题
    getErrorsByLevel(level) {
        return this.errorBook.errorList.filter(error => error.level === level);
    }

    // 获取错题统计
    getStatistics() {
        return {
            totalErrors: this.errorBook.totalErrors,
            errorsByType: this.errorBook.errorsByType,
            errorsByLevel: this.errorBook.errorsByLevel,
            errorList: this.errorBook.errorList
        };
    }

    // 标记错题已复习
    markAsReviewed(errorId) {
        const errorIndex = this.errorBook.errorList.findIndex(error => error.id === errorId);
        if (errorIndex !== -1) {
            this.errorBook.errorList[errorIndex].reviewCount++;
            this.errorBook.errorList[errorIndex].lastReviewedAt = new Date().toISOString();
            this.saveErrorBook();
            return true;
        }
        return false;
    }

    // 删除错题
    deleteError(errorId) {
        const errorIndex = this.errorBook.errorList.findIndex(error => error.id === errorId);
        if (errorIndex !== -1) {
            const error = this.errorBook.errorList[errorIndex];
            
            // 更新统计信息
            this.errorBook.totalErrors--;
            if (this.errorBook.errorsByType[error.type] > 0) {
                this.errorBook.errorsByType[error.type]--;
            }
            if (this.errorBook.errorsByLevel[error.level] > 0) {
                this.errorBook.errorsByLevel[error.level]--;
            }
            
            // 从列表中删除
            this.errorBook.errorList.splice(errorIndex, 1);
            this.saveErrorBook();
            return true;
        }
        return false;
    }

    // 清空错题本
    clearErrorBook() {
        this.errorBook = {
            totalErrors: 0,
            errorsByType: {},
            errorsByLevel: {},
            errorList: []
        };
        this.saveErrorBook();
    }

    // 生成错题分析报告
    generateAnalysisReport() {
        const report = {
            totalErrors: this.errorBook.totalErrors,
            mostErrorProneTypes: Object.entries(this.errorBook.errorsByType)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 3),
            mostErrorProneLevels: Object.entries(this.errorBook.errorsByLevel)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 3),
            recentErrors: this.errorBook.errorList
                .sort((a, b) => new Date(b.recordedAt) - new Date(a.recordedAt))
                .slice(0, 5),
            leastReviewedErrors: this.errorBook.errorList
                .sort((a, b) => a.reviewCount - b.reviewCount)
                .slice(0, 5)
        };

        return report;
    }

    // 生成AI优化建议
    generateAISuggestions() {
        if (this.errorBook.totalErrors === 0) {
            return {
                suggestions: [],
                recommendedPractice: []
            };
        }

        // 分析错误类型
        const errorTypes = Object.entries(this.errorBook.errorsByType);
        const mainWeakness = errorTypes.sort((a, b) => b[1] - a[1])[0];

        // 分析错误级别
        const errorLevels = Object.entries(this.errorBook.errorsByLevel);
        const levelWeakness = errorLevels.sort((a, b) => b[1] - a[1])[0];

        // 生成建议
        const suggestions = [
            {
                type: 'focus',
                content: `重点关注 ${mainWeakness[0]} 类型的题目，您在此类型上出错最多（${mainWeakness[1]} 题）`,
                priority: 'high'
            },
            {
                type: 'level',
                content: `加强 ${levelWeakness[0]} 级别的练习，您在此级别上出错较多（${levelWeakness[1]} 题）`,
                priority: 'medium'
            },
            {
                type: 'review',
                content: '定期复习错题，巩固知识点',
                priority: 'medium'
            }
        ];

        // 生成推荐练习
        const recommendedPractice = [
            {
                type: mainWeakness[0],
                level: levelWeakness[0],
                description: `专项练习 ${mainWeakness[0]} 类型的题目`,
                quantity: 10
            },
            {
                type: 'mixed',
                level: levelWeakness[0],
                description: `综合练习 ${levelWeakness[0]} 级别的题目`,
                quantity: 15
            }
        ];

        return {
            suggestions,
            recommendedPractice
        };
    }

    // 导出错题本
    exportErrorBook() {
        const exportData = {
            ...this.errorBook,
            exportTime: new Date().toISOString(),
            version: '1.0.0'
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `error_book_${new Date().toISOString().slice(0, 10)}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
    }

    // 导入错题本
    importErrorBook(jsonData) {
        try {
            const importedData = JSON.parse(jsonData);
            
            // 验证数据格式
            if (importedData.errorList && Array.isArray(importedData.errorList)) {
                // 合并错题
                importedData.errorList.forEach(error => {
                    // 检查是否已存在
                    const exists = this.errorBook.errorList.some(e => 
                        e.question === error.question && 
                        JSON.stringify(e.options) === JSON.stringify(error.options)
                    );
                    
                    if (!exists) {
                        this.addError(error);
                    }
                });
                
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('导入错题本失败:', error);
            return false;
        }
    }
}

// 导出模块
export default ErrorBookManager;

// 全局实例
if (typeof window !== 'undefined') {
    window.ErrorBookManager = ErrorBookManager;
    window.errorBookManager = new ErrorBookManager();
}

// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}
const el_assessment_result = document.getElementById('assessment-result');
const el_next_assessment_question = document.getElementById('next-assessment-question');
const el_submit_assessment_answer = document.getElementById('submit-assessment-answer');
/**
 * 日语水平评估测试脚本
 * 实现评估测试的完整流程，包括开始测试、答题、提交答案和显示结果
 */
class JapaneseLevelAssessment {
    constructor() {
        this.currentQuestion = 0;
        this.totalQuestions = 20;
        this.correctAnswers = 0;
        this.userAnswers = [];
        this.questions = [];
        this.userLevel = this.getUserLevel();
        this.setupEventListeners();
    }
    // 获取用户等级
    getUserLevel() {
        const savedLevel = localStorage.getItem('japanese_level');
        return savedLevel || 'N5'; // 默认N5级
    }
    // 生成评估题目（使用AI动态生成）
    generateQuestions() {
        if (window.aiQuestionGenerator) {
            console.log(`AI生成题目：用户等级 ${this.userLevel}，共 ${this.totalQuestions} 题`);
            const questions = window.aiQuestionGenerator.generateQuestions(this.userLevel, this.totalQuestions);
            // 转换题目格式以适应现有系统
            return questions.map(q => ({
                question: q.question,
                options: q.options,
                correct: q.correct
            }));
        } else {
            //  fallback to default questions if AI generator is not available
            console.warn('AI试题生成器不可用，使用默认题目');
            return this.getDefaultQuestions();
        }
    }
    // 默认题目（fallback）
    getDefaultQuestions() {
        return [
            {
                question: "\"こんにちは\"の意味は何ですか？",
                options: ["早上好", "下午好", "晚上好", "再见"],
                correct: 1
            },
            {
                question: "\"私は学生です\"の意味は何ですか？",
                options: ["你是学生", "我是学生", "他是学生", "她是学生"],
                correct: 1
            },
            {
                question: "\"ありがとう\"の意味は何ですか？",
                options: ["谢谢", "对不起", "请", "再见"],
                correct: 0
            },
            {
                question: "\"いいえ\"の意味は何ですか？",
                options: ["是", "不是", "好的", "不好"],
                correct: 1
            },
            {
                question: "\"はい\"の意味は何ですか？",
                options: ["是", "不是", "好的", "不好"],
                correct: 0
            }
        ];
    }
    // 设置事件监听器
    setupEventListeners() {
        // 开始评估按钮
        const startBtn = document.getElementById('start-assessment');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startAssessment());
        }
        // 提交答案按钮
        const submitBtn = document.getElementById('submit-assessment-answer');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitAnswer());
        }
        // 下一题按钮
        const nextBtn = document.getElementById('next-assessment-question');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextQuestion());
        }
    }
    // 开始评估
    startAssessment() {
        // 生成新的题目
        this.questions = this.generateQuestions();
        this.currentQuestion = 0;
        this.correctAnswers = 0;
        this.userAnswers = [];
        this.userLevel = this.getUserLevel(); // 重新获取用户等级
        // 隐藏开始界面，显示题目界面
        document.querySelector('.assessment-start-screen').style.display = 'none';
        document.querySelector('.assessment-question-screen').style.display = 'block';
        // 显示第一题
        this.showQuestion();
    }
    // 显示题目
    showQuestion() {
        if (this.currentQuestion < this.totalQuestions) {
            const question = this.questions[this.currentQuestion];
            // 更新题目编号
            document.getElementById('assessment-question-number').textContent = `题目 ${this.currentQuestion + 1}/${this.totalQuestions}`;
            // 更新进度条
            const progressPercentage = ((this.currentQuestion + 1) / this.totalQuestions) * 100;
            document.getElementById('assessment-progress-fill').style.width = `${progressPercentage}%`;
            // 更新题目内容
            document.getElementById('assessment-question-content').textContent = question.question;
            // 更新选项
            const optionsContainer = document.getElementById('assessment-question-options');
            optionsContainer.innerHTML = '';
            question.options.forEach((option, index) => {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'assessment-option';
                optionDiv.innerHTML = `
                    <input type="radio" id="option-${index}" name="assessment-option" value="${index}">
                    <label for="option-${index}">${option}</label>
                `;
                optionsContainer.appendChild(optionDiv);
            });
            // 重置按钮状态
            document.getElementById('submit-assessment-answer').style.display = 'block';
            document.getElementById('next-assessment-question').style.display = 'none';
        } else {
            // 所有题目完成，显示结果
            this.showResults();
        }
    }
    // 提交答案
    submitAnswer() {
        const selectedOption = document.querySelector('input[name="assessment-option"]:checked');
        if (!selectedOption) {
            alert('请选择一个答案');
            return;
        }
        const userAnswer = parseInt(selectedOption.value);
        const question = this.questions[this.currentQuestion];
        // 检查答案是否正确
        const isCorrect = userAnswer === question.correct;
        if (isCorrect) {
            this.correctAnswers++;
        } else {
            // 记录错题
            this.recordError(userAnswer, question);
        }
        // 保存用户答案
        this.userAnswers.push(userAnswer);
        // 显示下一题按钮
        document.getElementById('submit-assessment-answer').style.display = 'none';
        document.getElementById('next-assessment-question').style.display = 'block';
    }
    // 记录错题
    recordError(userAnswer, question) {
        if (window.errorBookManager) {
            const errorData = {
                question: question.question,
                options: question.options,
                userAnswer: userAnswer,
                correctAnswer: question.correct,
                type: this.getUserQuestionType(question),
                level: this.userLevel,
                tags: this.getQuestionTags(question),
                explanation: this.generateExplanation(question)
            };
            window.errorBookManager.addError(errorData);
            console.log('✅ 错题已记录到错题本');
        }
    }
    // 获取题目类型
    getUserQuestionType(question) {
        // 根据题目内容判断类型
        if (question.question.includes('の意味は何ですか？')) {
            return '词汇';
        } else if (question.question.includes('の読み方は何ですか？')) {
            return '词汇';
        } else if (question.question.includes('__。')) {
            return '语法';
        } else if (question.question.includes('文章を読んで')) {
            return '阅读';
        }
        return '词汇'; // 默认类型
    }
    // 获取题目标签
    getQuestionTags(question) {
        const tags = [];
        tags.push(`${this.userLevel}${this.getUserQuestionType(question)}`);
        if (question.question.includes('の意味は何ですか？')) {
            tags.push('词汇含义');
        } else if (question.question.includes('の読み方は何ですか？')) {
            tags.push('词汇读音');
        } else if (question.question.includes('__。')) {
            tags.push('语法填空');
        }
        return tags;
    }
    // 生成解析
    generateExplanation(question) {
        const correctOption = question.options[question.correct];
        const type = this.getUserQuestionType(question);
        if (type === '词汇') {
            if (question.question.includes('の意味は何ですか？')) {
                const word = question.question.match(/"(.+?)"/)?.[1] || '该词';
                return `${word}的意思是${correctOption}。`;
            } else if (question.question.includes('の読み方は何ですか？')) {
                const word = question.question.match(/"(.+?)"/)?.[1] || '该词';
                return `${word}的正确读音是${correctOption}。`;
            }
        } else if (type === '语法') {
            return `本题考察语法知识，正确答案是${correctOption}。`;
        } else if (type === '阅读') {
            return `本题考察阅读能力，正确答案是${correctOption}。`;
        }
        return `正确答案是${correctOption}。`;
    }
    // 下一题
    nextQuestion() {
        this.currentQuestion++;
        this.showQuestion();
    }
    // 显示结果
    showResults() {
        // 隐藏题目界面，显示结果界面
        document.querySelector('.assessment-question-screen').style.display = 'none';
        document.getElementById('assessment-result').style.display = 'block';
        // 计算得分和正确率
        const score = Math.round((this.correctAnswers / this.totalQuestions) * 100);
        const accuracy = Math.round((this.correctAnswers / this.totalQuestions) * 100);
        // 更新结果信息
        document.getElementById('total-questions').textContent = this.totalQuestions;
        document.getElementById('correct-answers').textContent = this.correctAnswers;
        document.getElementById('assessment-score').textContent = score;
        document.getElementById('accuracy').textContent = accuracy;
        // 推荐等级
        let recommendedLevel = 'N5';
        if (score >= 90) {
            recommendedLevel = 'N1';
        } else if (score >= 80) {
            recommendedLevel = 'N2';
        } else if (score >= 65) {
            recommendedLevel = 'N3';
        } else if (score >= 45) {
            recommendedLevel = 'N4';
        }
        document.getElementById('suggested-level').textContent = recommendedLevel;
        document.getElementById('recommended-level').textContent = recommendedLevel;
        // 设置保存等级按钮事件
        document.getElementById('save-level').addEventListener('click', () => {
            this.saveLevel(recommendedLevel);
        });
        // 设置重新评估按钮事件
        document.getElementById('restart-assessment').addEventListener('click', () => {
            this.restartAssessment();
        });
        // 设置跳过按钮事件
        document.getElementById('skip-assessment').addEventListener('click', () => {
            this.skipAssessment();
        });
    }
    // 保存等级
    saveLevel(level) {
        // 保存等级到本地存储
        localStorage.setItem('japanese_level', level);
        alert(`您的日语水平等级 ${level} 已保存`);
    }
    // 重新评估
    restartAssessment() {
        // 重置评估状态
        this.currentQuestion = 0;
        this.correctAnswers = 0;
        this.userAnswers = [];
        this.questions = [];
        this.userLevel = this.getUserLevel(); // 重新获取用户等级
        // 显示开始界面
        document.getElementById('assessment-result').style.display = 'none';
        document.querySelector('.assessment-start-screen').style.display = 'block';
    }
    // 跳過评估
    skipAssessment() {
        // 跳转到日语考试页面
        window.location.href = 'japanese-exam.html';
    }
}
// 页面加载完成后初始化评估系统
document.addEventListener('DOMContentLoaded', function() {
    new JapaneseLevelAssessment();
});
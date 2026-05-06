
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

const el_ai_solution = document.getElementById('ai-solution');
const el_answer_explanation = document.getElementById('answer-explanation');
const el_result_feedback = document.getElementById('result-feedback');
const el_prev_question = document.getElementById('prev-question');
/**
 * 日语历年练习题系统脚本
 * 实现日语考试练习的完整功能，包括题目展示、答案提交、AI解题等
 */

class JapaneseExamSystem {
    constructor() {
        this.currentQuestion = 0;
        this.totalQuestions = 0;
        this.correctAnswers = 0;
        this.userAnswers = [];
        this.questions = [];
        this.selectedMode = 'random';
        this.selectedLevel = 'N1';
        this.selectedType = '词汇';
        this.setupEventListeners();
        this.loadQuestions();
    }

    // 加载题目
    loadQuestions() {
        if (window.aiQuestionGenerator) {
            console.log(`AI生成题目：模式 ${this.selectedMode}，级别 ${this.selectedLevel}，题型 ${this.selectedType}`);
            
            // 根据选择的级别生成题目
            let targetLevel = this.selectedLevel;
            if (targetLevel === 'all') {
                targetLevel = 'N3'; // 综合级别默认N3
            }
            
            // 生成题目
            const questions = window.aiQuestionGenerator.generateQuestions(targetLevel, 10);
            
            // 根据选择的题型过滤
            this.questions = questions;
            if (this.selectedType !== 'all') {
                this.questions = this.questions.filter(q => q.type === this.selectedType);
            }
            
            // 如果过滤后题目太少，重新生成
            if (this.questions.length < 5) {
                this.questions = window.aiQuestionGenerator.generateQuestions(targetLevel, 10);
            }
            
        } else {
            //  fallback to default questions if AI generator is not available
            console.warn('AI试题生成器不可用，使用默认题目');
            this.questions = this.getDefaultQuestions();
        }

        this.totalQuestions = this.questions.length;
        this.updateStats();
        this.showQuestion();
    }

    // 默认题目（fallback）
    getDefaultQuestions() {
        return [
            {
                id: 1,
                question: "この計画は、実現するためには多くの資金と時間が__。",
                options: ["必要とされる", "必要である", "必要となる", "必要であった"],
                correct: 0,
                type: "词汇",
                level: "N1",
                tags: ["N1词汇", "动词用法", "惯用表达"],
                explanation: "本题考察动词的被动用法。「必要とされる」是「必要とする」的被动形式，表示"被需要"。句意为"这个计划要实现需要很多资金和时间"。"
            },
            {
                id: 2,
                question: "彼の言うことは、いつも__という感じがする。",
                options: ["当たり前", "当然", "自然", "普通"],
                correct: 0,
                type: "词汇",
                level: "N1",
                tags: ["N1词汇", "形容词用法"],
                explanation: "本题考察形容词的用法。「当たり前」表示"理所当然"，符合句意"他说的话总是给人一种理所当然的感觉"。"
            },
            {
                id: 3,
                question: "彼女は、いつも__に仕事をこなす。",
                options: ["速い", "早い", "迅速", "急いで"],
                correct: 2,
                type: "词汇",
                level: "N1",
                tags: ["N1词汇", "副词用法"],
                explanation: "本题考察副词的用法。「迅速」是副词，表示"迅速地"，符合句意"她总是迅速地完成工作"。"
            }
        ];
    }

    // 设置事件监听器
    setupEventListeners() {
        // 模式选择
        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.mode-option').forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                this.selectedMode = option.dataset.mode;
                this.loadQuestions();
            });
        });

        // 级别选择
        document.querySelectorAll('.level-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.level-option').forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                this.selectedLevel = option.dataset.level;
                this.loadQuestions();
            });
        });

        // 题型选择
        document.querySelectorAll('.type-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.type-option').forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                this.selectedType = option.dataset.type;
                this.loadQuestions();
            });
        });

        // 提交答案
        document.getElementById('submit-answer').addEventListener('click', () => {
            this.submitAnswer();
        });

        // 下一题
        document.getElementById('next-question').addEventListener('click', () => {
            this.nextQuestion();
        });

        // 重置
        document.getElementById('reset-question').addEventListener('click', () => {
            this.resetQuestion();
        });

        // AI解题
        document.getElementById('ai-solution-btn').addEventListener('click', () => {
            this.getAISolution();
        });

        // 导航按钮
        document.getElementById('next-question-btn').addEventListener('click', () => {
            this.nextQuestion();
        });

        document.getElementById('prev-question').addEventListener('click', () => {
            this.prevQuestion();
        });
    }

    // 更新统计信息
    updateStats() {
        document.getElementById('total-questions').textContent = this.totalQuestions;
        document.getElementById('current-question').textContent = this.currentQuestion + 1;
        document.getElementById('correct-answers').textContent = this.correctAnswers;
        document.getElementById('accuracy').textContent = this.totalQuestions > 0 ? Math.round((this.correctAnswers / this.totalQuestions) * 100) + '%' : '0%';
        document.getElementById('nav-info').textContent = `第 ${this.currentQuestion + 1} 题 / 共 ${this.totalQuestions} 题`;
    }

    // 显示题目
    showQuestion() {
        if (this.currentQuestion < this.totalQuestions) {
            const question = this.questions[this.currentQuestion];
            
            // 更新题目内容
            document.getElementById('question-content').textContent = question.question;
            document.getElementById('question-number').textContent = `问题 ${this.currentQuestion + 1}`;
            document.getElementById('question-type').textContent = question.type;
            
            // 更新知识点标签
            const tagsContainer = document.getElementById('knowledge-tags');
            tagsContainer.innerHTML = '';
            question.tags.forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'knowledge-tag';
                tagSpan.textContent = tag;
                tagsContainer.appendChild(tagSpan);
            });
            
            // 更新选项
            const optionsContainer = document.getElementById('question-options');
            optionsContainer.innerHTML = '';
            
            question.options.forEach((option, index) => {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'option-item';
                optionDiv.dataset.option = String.fromCharCode(65 + index);
                optionDiv.innerHTML = `
                    <div class="option-letter">${String.fromCharCode(65 + index)}</div>
                    <div class="option-content">${option}</div>
                `;
                optionDiv.addEventListener('click', () => {
                    // 移除其他选项的选中状态
                    document.querySelectorAll('.option-item').forEach(opt => opt.classList.remove('selected'));
                    // 添加当前选项的选中状态
                    optionDiv.classList.add('selected');
                });
                optionsContainer.appendChild(optionDiv);
            });

            // 更新进度
            const progressPercentage = ((this.currentQuestion + 1) / this.totalQuestions) * 100;
            document.getElementById('progress-fill').style.width = `${progressPercentage}%`;
            document.getElementById('progress-text').textContent = `${Math.round(progressPercentage)}%`;

            // 重置界面
            document.getElementById('result-feedback').innerHTML = '';
            document.getElementById('answer-explanation').style.display = 'none';
            document.getElementById('ai-solution').style.display = 'none';

            // 更新导航按钮状态
            document.getElementById('prev-question').disabled = this.currentQuestion === 0;
        }
    }

    // 提交答案
    submitAnswer() {
        const selectedOption = document.querySelector('.option-item.selected');
        if (!selectedOption) {
            alert('请选择一个答案');
            return;
        }

        const selectedIndex = selectedOption.dataset.option.charCodeAt(0) - 65;
        const question = this.questions[this.currentQuestion];
        const isCorrect = selectedIndex === question.correct;

        // 显示反馈
        const feedbackDiv = document.getElementById('result-feedback');
        if (isCorrect) {
            feedbackDiv.innerHTML = '<div class="correct-feedback">✅ 回答正确！</div>';
            this.correctAnswers++;
        } else {
            feedbackDiv.innerHTML = '<div class="incorrect-feedback">❌ 回答错误</div>';
            // 记录错题
            this.recordError(selectedIndex, question);
        }

        // 显示正确答案和解析
        const explanationDiv = document.getElementById('answer-explanation');
        document.getElementById('correct-answer').textContent = String.fromCharCode(65 + question.correct);
        document.getElementById('explanation-content').textContent = question.explanation;
        explanationDiv.style.display = 'block';

        // 更新统计信息
        this.updateStats();
    }

    // 记录错题
    recordError(userAnswer, question) {
        if (window.errorBookManager) {
            const errorData = {
                question: question.question,
                options: question.options,
                userAnswer: userAnswer,
                correctAnswer: question.correct,
                type: question.type || '词汇',
                level: question.level || this.selectedLevel,
                tags: question.tags || [],
                explanation: question.explanation || ''
            };
            
            window.errorBookManager.addError(errorData);
            console.log('✅ 错题已记录到错题本');
        }
    }

    // 下一题
    nextQuestion() {
        if (this.currentQuestion < this.totalQuestions - 1) {
            this.currentQuestion++;
            this.showQuestion();
        } else {
            alert('已经是最后一题了');
        }
    }

    // 上一题
    prevQuestion() {
        if (this.currentQuestion > 0) {
            this.currentQuestion--;
            this.showQuestion();
        }
    }

    // 重置题目
    resetQuestion() {
        // 移除选项的选中状态
        document.querySelectorAll('.option-item').forEach(opt => opt.classList.remove('selected'));
        // 重置反馈
        document.getElementById('result-feedback').innerHTML = '';
        document.getElementById('answer-explanation').style.display = 'none';
        document.getElementById('ai-solution').style.display = 'none';
    }

    // 获取AI解题
    getAISolution() {
        const question = this.questions[this.currentQuestion];
        const solutionDiv = document.getElementById('ai-solution');
        const solutionContent = document.getElementById('solution-content');

        // 显示加载状态
        solutionContent.innerHTML = '<div class="loading">AI正在分析...请稍候</div>';
        solutionDiv.style.display = 'block';

        // 模拟AI分析
        setTimeout(() => {
            solutionContent.innerHTML = `
                <h4>题目分析</h4>
                <p>${question.question}</p>
                
                <h4>选项分析</h4>
                <ul>
                    ${question.options.map((option, index) => 
                        `<li>${String.fromCharCode(65 + index)}. ${option} ${index === question.correct ? '(正确答案)' : ''}</li>`
                    ).join('')}
                </ul>
                
                <h4>语法解析</h4>
                <p>${question.explanation}</p>
                
                <h4>知识点</h4>
                <p>${question.tags.join(', ')}</p>
                
                <h4>难度评估</h4>
                <p>⭐⭐⭐⭐⭐ (N1级别)</p>
            `;
        }, 1500);
    }
}

// 页面加载完成后初始化系统
document.addEventListener('DOMContentLoaded', function() {
    new JapaneseExamSystem();
});
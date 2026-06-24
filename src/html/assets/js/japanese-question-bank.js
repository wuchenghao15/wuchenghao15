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
/**
 * MTSCOS AI 系统 - 日语题库前端功能
 * 包含练习模式和考试模式
 */
class JapaneseQuestionBank {
    constructor() {
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.answers = [];
        this.mode = 'practice'; // practice or exam
        this.score = 0;
        this.startTime = null;
        this.endTime = null;
    }
    // 初始化题库
    async init() {
        await this.loadQuestions();
        this.renderQuestion();
    }
    // 加载题目
    async loadQuestions() {
        const response = await fetch('/api/jptest/questions');
        const data = await response.json();
        this.questions = data.data;
    }
    // 设置模式
    setMode(mode) {
        this.mode = mode;
        this.reset();
        this.renderQuestion();
    }
    // 重置
    reset() {
        this.currentQuestionIndex = 0;
        this.answers = [];
        this.score = 0;
        this.startTime = new Date();
        this.endTime = null;
    }
    // 渲染题目
    renderQuestion() {
        if (this.currentQuestionIndex >= this.questions.length) {
            this.renderResult();
            return;
        }
        const question = this.questions[this.currentQuestionIndex];
        // 渲染题目到页面
        console.log('渲染题目:', question.question);
    }
    // 提交答案
    submitAnswer(answerIndex) {
        const question = this.questions[this.currentQuestionIndex];
        const isCorrect = answerIndex === question.answer;
        this.answers.push({
            questionId: question.id,
            selectedAnswer: answerIndex,
            isCorrect: isCorrect
        });
        if (isCorrect) {
            this.score++;
        }
        if (this.mode === 'practice') {
            // 练习模式下显示答案解析
            this.showExplanation(question, answerIndex, isCorrect);
        }
        this.currentQuestionIndex++;
        this.renderQuestion();
    }
    // 显示答案解析
    showExplanation(question, selectedAnswer, isCorrect) {
        console.log('答案解析:', question.explanation);
        console.log('是否正确:', isCorrect);
    }
    // 渲染结果
    renderResult() {
        this.endTime = new Date();
        const duration = (this.endTime - this.startTime) / 1000;
        console.log('测试完成!');
        console.log('得分:', this.score, '/', this.questions.length);
        console.log('用时:', duration, '秒');
        // 渲染结果到页面
    }
}
// 初始化
const questionBank = new JapaneseQuestionBank();
questionBank.init();
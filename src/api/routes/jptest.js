/**
 * MTSCOS AI 系统 - 日语题库API
 * 用于管理日语题库数据
 */

const express = require('express');
const router = express.Router();

// 验证题目的中间件
const validateQuestion = (req, res, next) => {
    const { question, options, correctAnswer, category, difficulty } = req.body;
    
    if (!question || !options || !correctAnswer || !category || !difficulty) {
        return res.status(400).json({
            status: "error",
            message: "缺少必要的题目字段"
        });
    }
    
    if (!Array.isArray(options) || options.length < 2) {
        return res.status(400).json({
            status: "error",
            message: "题目选项必须是至少包含2个元素的数组"
        });
    }
    
    if (!options.includes(correctAnswer)) {
        return res.status(400).json({
            status: "error",
            message: "正确答案必须是选项之一"
        });
    }
    
    next();
};

const fs = require('fs');
const path = require('path');

// 日语题库数据文件路径
const questionsFilePath = path.join(__dirname, '../../data/japanese-questions.json');

// 获取所有题目
router.get('/questions', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        res.json({
            status: 'success',
            data: questions
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});


// 添加题目
router.post('/questions', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        const newQuestion = {
            id: 'q' + Date.now(),
            ...req.body,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        
        questions.push(newQuestion);
        fs.writeFileSync(questionsFilePath, JSON.stringify(questions, null, 2));
        
        res.json({
            status: 'success',
            data: newQuestion
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 更新题目
router.put('/questions/:id', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        let questions = JSON.parse(data);
        
        const questionIndex = questions.findIndex(q => q.id === req.params.id);
        if (questionIndex === -1) {
            return res.status(404).json({
                status: 'error',
                message: '题目未找到'
            });
        }
        
        questions[questionIndex] = {
            ...questions[questionIndex],
            ...req.body,
            updatedAt: new Date().toISOString()
        };
        
        fs.writeFileSync(questionsFilePath, JSON.stringify(questions, null, 2));
        
        res.json({
            status: 'success',
            data: questions[questionIndex]
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 删除题目
router.delete('/questions/:id', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        let questions = JSON.parse(data);
        
        const initialLength = questions.length;
        questions = questions.filter(q => q.id !== req.params.id);
        
        if (questions.length === initialLength) {
            return res.status(404).json({
                status: 'error',
                message: '题目未找到'
            });
        }
        
        fs.writeFileSync(questionsFilePath, JSON.stringify(questions, null, 2));
        
        res.json({
            status: 'success',
            message: '题目已删除'
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取题目分类
router.get('/categories', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        const categories = [...new Set(questions.map(q => q.category))];
        
        res.json({
            status: 'success',
            data: categories
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取题目难度等级
router.get('/difficulties', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        const difficulties = [...new Set(questions.map(q => q.difficulty))];
        
        res.json({
            status: 'success',
            data: difficulties
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});


// 搜索题目
router.get('/questions/search', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        const { keyword, category, difficulty } = req.query;
        let filteredQuestions = [...questions];
        
        // 根据关键词搜索
        if (keyword) {
            filteredQuestions = filteredQuestions.filter(q => 
                q.question.includes(keyword)
            );
        }
        
        // 根据分类过滤
        if (category) {
            filteredQuestions = filteredQuestions.filter(q => q.category === category);
        }
        
        // 根据难度过滤
        if (difficulty) {
            filteredQuestions = filteredQuestions.filter(q => q.difficulty === difficulty);
        }
        
        res.json({
            status: 'success',
            data: filteredQuestions
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});


// 获取分页题目
router.get('/questions/paginated', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        
        const paginatedQuestions = questions.slice(startIndex, endIndex);
        
        res.json({
            status: 'success',
            data: {
                questions: paginatedQuestions,
                total: questions.length,
                page: page,
                limit: limit,
                totalPages: Math.ceil(questions.length / limit)
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取所有分类
router.get('/categories', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        // 提取所有唯一分类
        const categories = [...new Set(questions.map(q => q.category))];
        
        res.json({
            status: 'success',
            data: categories
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 获取所有难度等级
router.get('/difficulties', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        const questions = JSON.parse(data);
        
        // 提取所有唯一难度等级
        const difficulties = [...new Set(questions.map(q => q.difficulty))];
        
        res.json({
            status: 'success',
            data: difficulties
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

// 搜索题目
router.get('/questions/search', async (req, res) => {
    try {
        const data = fs.readFileSync(questionsFilePath, 'utf8');
        let questions = JSON.parse(data);
        
        const { keyword, category, difficulty, page = 1, limit = 10 } = req.query;
        
        // 搜索过滤
        let filteredQuestions = questions;
        
        if (keyword) {
            filteredQuestions = filteredQuestions.filter(q => 
                q.question.includes(keyword) || 
                q.explanation.includes(keyword)
            );
        }
        
        if (category) {
            filteredQuestions = filteredQuestions.filter(q => q.category === category);
        }
        
        if (difficulty) {
            filteredQuestions = filteredQuestions.filter(q => q.difficulty === difficulty);
        }
        
        // 分页
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + parseInt(limit);
        const paginatedQuestions = filteredQuestions.slice(startIndex, endIndex);
        
        res.json({
            status: 'success',
            data: {
                questions: paginatedQuestions,
                total: filteredQuestions.length,
                page: parseInt(page),
                limit: parseInt(limit),
                totalPages: Math.ceil(filteredQuestions.length / limit)
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

module.exports = router;


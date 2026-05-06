// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 复习计划管理API路由
 * 提供复习计划的创建、查询、更新和删除功能
 */
;
const express = require('express');
const router = express.Router();
const reviewPlanController = require('../controllers/review-plan-controller');

// 复习计划相关路由;
router.get('/plans', reviewPlanController.getUserPlans);
router.post('/plans', reviewPlanController.createReviewPlan);
router.get('/plans/:planId', reviewPlanController.getPlanById);
router.put('/plans/:planId', reviewPlanController.updateReviewPlan);
router.delete('/plans/:planId', reviewPlanController.deleteReviewPlan);

// 学习进度相关路由;
router.get('/progress', reviewPlanController.getUserProgress);
router.post('/progress', reviewPlanController.updateProgress);
router.get('/progress/:planId', reviewPlanController.getPlanProgress);

// 练习记录相关路由;
router.get('/practices', reviewPlanController.getUserPractices);
router.post('/practices', reviewPlanController.addPracticeRecord);
router.get('/practices/:recordId', reviewPlanController.getPracticeRecord);

// 试卷相关路由;
router.get('/papers', reviewPlanController.getUserPapers);
router.post('/papers/generate', reviewPlanController.generatePaper);
router.get('/papers/:paperId', reviewPlanController.getPaperById);

// 统计分析相关路由;
router.get('/stats', reviewPlanController.getUserStats);
router.get('/stats/analysis', reviewPlanController.getLearningAnalysis);
;
module.exports = router;
#!/usr/bin/env node

/**
 * 日语复习计划数据库初始化脚本
 * 创建数据库结构并添加示例数据
 */

const japaneseReviewPlanManager = require('./src/core/database/japanese-review-plan-manager');

// 示例复习计划数据
const samplePlans = [
    {
        plan_id: 'plan_n5_2026',
        user_id: 1,
        plan_name: 'N5备考计划',
        level: 'N5',
        target_score: 120,
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'active',
        total_days: 90,
        daily_target: 30,
        description: '90天N5备考计划，每天30分钟学习时间'
    },
    {
        plan_id: 'plan_n4_2026',
        user_id: 1,
        plan_name: 'N4强化计划',
        level: 'N4',
        target_score: 130,
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'active',
        total_days: 60,
        daily_target: 45,
        description: '60天N4强化计划，每天45分钟学习时间'
    }
];

// 示例练习记录
const samplePracticeRecords = [
    {
        record_id: 'practice_001',
        user_id: 1,
        plan_id: 'plan_n5_2026',
        paper_id: 'daily_20260123',
        paper_type: 'daily_practice',
        level: 'N5',
        score: 85,
        total_questions: 20,
        correct_answers: 17,
        time_spent: 1200,
        questions: [1, 2, 3, 4, 5],
        answers: ['A', 'B', 'C', 'D', 'A'],
        correct_answers: ['A', 'B', 'C', 'D', 'A'],
        difficulty: 2,
        feedback: '做得不错，继续加油！',
        status: 'completed'
    }
];

/**
 * 初始化日语复习计划数据库
 */
async function initializeReviewPlanDatabase() {
    console.log('🚀 开始初始化日语复习计划数据库...');
    
    try {
        // 初始化数据库管理器
        await japaneseReviewPlanManager.initialize();
        
        // 添加示例复习计划
        console.log('📝 添加示例复习计划...');
        for (const plan of samplePlans) {
            const result = await japaneseReviewPlanManager.addReviewPlan(plan);
            console.log(`   ✅ 添加计划: ${plan.plan_name}`);
        }
        
        // 添加示例练习记录
        console.log('📝 添加示例练习记录...');
        for (const record of samplePracticeRecords) {
            const result = await japaneseReviewPlanManager.addPracticeRecord(record);
            console.log(`   ✅ 添加练习记录: ${record.record_id}`);
        }
        
        // 获取数据库统计信息
        const stats = await japaneseReviewPlanManager.getStatistics();
        console.log('📊 数据库统计信息:');
        console.log(`   总复习计划: ${stats.total_plans}`);
        console.log(`   总学习进度: ${stats.total_progress}`);
        console.log(`   总练习记录: ${stats.total_records}`);
        console.log(`   总AI试卷: ${stats.total_ai_papers}`);
        console.log(`   总提取题目: ${stats.total_extracted_questions}`);
        
        // 获取用户计划
        const userPlans = await japaneseReviewPlanManager.getUserPlans(1);
        console.log('👤 用户复习计划:');
        userPlans.forEach(plan => {
            console.log(`   - ${plan.plan_name} (${plan.level})`);
        });
        
        console.log('🎉 日语复习计划数据库初始化成功！');
        
    } catch (error) {
        console.error('❌ 初始化失败:', error);
    } finally {
        // 关闭数据库连接
        japaneseReviewPlanManager.close();
    }
}

// 执行初始化
if (require.main === module) {
    initializeReviewPlanDatabase();
}

module.exports = {
    initializeReviewPlanDatabase,
    samplePlans,
    samplePracticeRecords
};
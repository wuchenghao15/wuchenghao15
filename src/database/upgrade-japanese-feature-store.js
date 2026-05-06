// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 升级日语题库特征库到数据库
 * 将日语题库的特征库升级到 AI 特征库存储系统
 */

const db = require('./db');
const aiFeatureStoreService = require('../core/storage/ai-feature-store-service');

async function upgradeJapaneseFeatureStore() {
    try {
        console.log('🔄 开始升级日语题库特征库到数据库');
        
        // 确保数据库连接已初始化
        await db.initialize();
        console.log('✅ 数据库连接初始化成功');
        
        // 初始化 AI 特征库服务
        await aiFeatureStoreService.init();
        console.log('✅ AI 特征库服务初始化成功');
        
        // 获取日语学习相关分类
        const categories = await db.query('SELECT * FROM ai_feature_categories WHERE category_name IN (?, ?, ?)', [
            'japanese_learning', 'question_generation', 'exam_preparation'
        ]);
        
        const categoryMap = {};
        categories.forEach(cat => {
            categoryMap[cat.category_name] = cat.id;
        });
        
        console.log('✅ 日语学习相关分类获取成功:', categoryMap);
        
        // 定义日语题库特征
        const japaneseFeatures = [
            // 日语学习特征
            {
                feature_id: 'japanese_kanji_recognition',
                feature_name: '日语汉字识别',
                feature_type: 'natural_language',
                category_id: categoryMap.japanese_learning,
                description: '识别和处理日语汉字的能力',
                feature_data: {
                    kanji_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    common_kanji: 2136,
                    radicals: 214,
                    stroke_order: true
                }
            },
            {
                feature_id: 'japanese_vocabulary_mastery',
                feature_name: '日语词汇掌握',
                feature_type: 'natural_language',
                category_id: categoryMap.japanese_learning,
                description: '掌握日语词汇的能力',
                feature_data: {
                    vocabulary_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    word_count: {
                        N5: 800,
                        N4: 1500,
                        N3: 3000,
                        N2: 6000,
                        N1: 10000
                    },
                    part_of_speech: ['noun', 'verb', 'adjective', 'adverb', 'particle']
                }
            },
            {
                feature_id: 'japanese_grammar_understanding',
                feature_name: '日语语法理解',
                feature_type: 'natural_language',
                category_id: categoryMap.japanese_learning,
                description: '理解和应用日语语法的能力',
                feature_data: {
                    grammar_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    grammar_points: {
                        N5: 80,
                        N4: 160,
                        N3: 320,
                        N2: 640,
                        N1: 1280
                    },
                    sentence_patterns: true
                }
            },
            {
                feature_id: 'japanese_listening_comprehension',
                feature_name: '日语听力理解',
                feature_type: 'speech_recognition',
                category_id: categoryMap.japanese_learning,
                description: '理解日语听力内容的能力',
                feature_data: {
                    listening_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    audio_types: ['conversation', 'announcement', 'lecture', 'news'],
                    speed_levels: ['slow', 'normal', 'fast']
                }
            },
            {
                feature_id: 'japanese_reading_comprehension',
                feature_name: '日语阅读理解',
                feature_type: 'natural_language',
                category_id: categoryMap.japanese_learning,
                description: '理解日语阅读内容的能力',
                feature_data: {
                    reading_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    text_types: ['conversation', 'announcement', 'article', 'essay'],
                    text_length: {
                        N5: 50-100,
                        N4: 100-200,
                        N3: 200-400,
                        N2: 400-800,
                        N1: 800-1600
                    }
                }
            },
            {
                feature_id: 'japanese_writing_ability',
                feature_name: '日语写作能力',
                feature_type: 'natural_language',
                category_id: categoryMap.japanese_learning,
                description: '用日语进行写作的能力',
                feature_data: {
                    writing_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    writing_types: ['short_message', 'email', 'essay', 'report'],
                    word_count: {
                        N5: 50-100,
                        N4: 100-200,
                        N3: 200-300,
                        N2: 300-500,
                        N1: 500-800
                    }
                }
            },
            
            // 题目生成特征
            {
                feature_id: 'japanese_question_generator',
                feature_name: '日语题目生成器',
                feature_type: 'question_generation',
                category_id: categoryMap.question_generation,
                description: '生成日语练习题的能力',
                feature_data: {
                    question_types: ['listening', 'vocabulary', 'grammar', 'reading', 'writing'],
                    difficulty_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    question_count: 10000,
                    generation_strategy: 'adaptive'
                }
            },
            {
                feature_id: 'japanese_question_adapter',
                feature_name: '日语题目适配器',
                feature_type: 'question_generation',
                category_id: categoryMap.question_generation,
                description: '根据用户水平调整日语题目的能力',
                feature_data: {
                    adaptation_strategies: ['difficulty_adjustment', 'topic_adjustment', 'format_adjustment'],
                    user_profiles: true,
                    learning_paths: true
                }
            },
            {
                feature_id: 'japanese_question_evaluator',
                feature_name: '日语题目评估器',
                feature_type: 'question_generation',
                category_id: categoryMap.question_generation,
                description: '评估日语题目质量的能力',
                feature_data: {
                    evaluation_metrics: ['difficulty', 'relevance', 'coverage', 'fairness'],
                    quality_threshold: 0.8,
                    feedback_loop: true
                }
            },
            
            // 考试准备特征
            {
                feature_id: 'japanese_exam_strategy',
                feature_name: '日语考试策略',
                feature_type: 'exam_preparation',
                category_id: categoryMap.exam_preparation,
                description: '针对日语考试的备考策略',
                feature_data: {
                    exam_types: ['JLPT', 'JTEST', 'EJU'],
                    exam_levels: ['N5', 'N4', 'N3', 'N2', 'N1'],
                    study_plan: true,
                    time_management: true
                }
            },
            {
                feature_id: 'japanese_exam_simulator',
                feature_name: '日语考试模拟器',
                feature_type: 'exam_preparation',
                category_id: categoryMap.exam_preparation,
                description: '模拟日语考试环境的能力',
                feature_data: {
                    exam_formats: ['paper', 'computer-based'],
                    time_limits: true,
                    scoring_system: true,
                    result_analysis: true
                }
            },
            {
                feature_id: 'japanese_exam_analyzer',
                feature_name: '日语考试分析器',
                feature_type: 'exam_preparation',
                category_id: categoryMap.exam_preparation,
                description: '分析日语考试结果的能力',
                feature_data: {
                    analysis_dimensions: ['accuracy', 'speed', 'knowledge_gaps', 'strengths'],
                    improvement_suggestions: true,
                    progress_tracking: true
                }
            }
        ];
        
        // 存储日语题库特征
        let storedCount = 0;
        for (const feature of japaneseFeatures) {
            const result = await aiFeatureStoreService.storeAiFeature(feature);
            if (result.success) {
                storedCount++;
                console.log(`✅ 特征存储成功: ${feature.feature_name}`);
            } else {
                console.error(`❌ 特征存储失败: ${feature.feature_name}`, result.error);
            }
        }
        
        console.log(`🎉 日语题库特征库升级完成，共存储 ${storedCount} 个特征`);
        
        // 验证特征存储结果
        const featureList = await aiFeatureStoreService.getAiFeatureList({
            category_id: categoryMap.japanese_learning,
            limit: 50
        });
        
        console.log(`✅ 日语学习特征验证成功，共 ${featureList.data.length} 个特征`);
        
        // 获取特征统计信息
        const stats = await aiFeatureStoreService.getAiFeatureStats();
        console.log('✅ 特征库统计信息:', stats.data);
        
    } catch (error) {
        console.error('❌ 日语题库特征库升级失败:', error);
        console.error('Error stack:', error.stack);
    } finally {
        // 关闭数据库连接
        db.close();
        console.log('✅ 数据库连接关闭');
    }
}

// 执行升级
upgradeJapaneseFeatureStore();
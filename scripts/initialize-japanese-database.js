/**
 * 日语题库初始化脚本
 * 为日语测试系统添加示例题目
 */

const japaneseDatabaseManager = require('../src/core/database/japanese-database-manager');

// 示例日语题目数据
const sampleQuestions = [
    // N5 级别题目
    {
        question_id: 'N5-VOCAB-001',
        level: 'N5',
        type: 'vocabulary',
        question_text: 'これは＿＿です。',
        options: ['いぬ', 'うさぎ', 'ねこ', 'たぬき'],
        correct_answer: 'いぬ',
        explanation: '「いぬ」は「狗」の意味です。',
        difficulty: 1,
        category: 'vocabulary',
        subcategory: 'animals',
        tags: ['N5', 'vocabulary', 'animals']
    },
    {
        question_id: 'N5-GRAMMAR-001',
        level: 'N5',
        type: 'grammar',
        question_text: '私は＿＿です。',
        options: ['学生', '先生', '医者', '会社員'],
        correct_answer: '学生',
        explanation: '「私は学生です」は「I am a student」の意味です。',
        difficulty: 1,
        category: 'grammar',
        subcategory: 'basic',
        tags: ['N5', 'grammar', 'basic']
    },
    {
        question_id: 'N5-VOCAB-002',
        level: 'N5',
        type: 'vocabulary',
        question_text: '＿＿を食べました。',
        options: ['ご飯', '水', 'お茶', '牛乳'],
        correct_answer: 'ご飯',
        explanation: '「ご飯」は「rice」の意味です。',
        difficulty: 1,
        category: 'vocabulary',
        subcategory: 'food',
        tags: ['N5', 'vocabulary', 'food']
    },
    {
        question_id: 'N5-GRAMMAR-002',
        level: 'N5',
        type: 'grammar',
        question_text: '昨日、＿＿に行きました。',
        options: ['公園', '病院', '銀行', '図書館'],
        correct_answer: '公園',
        explanation: '「公園」は「park」の意味です。',
        difficulty: 1,
        category: 'grammar',
        subcategory: 'places',
        tags: ['N5', 'grammar', 'places']
    },
    
    // N4 级别题目
    {
        question_id: 'N4-VOCAB-001',
        level: 'N4',
        type: 'vocabulary',
        question_text: '昨日、＿＿に行きました。',
        options: ['学校', '病院', '銀行', '図書館'],
        correct_answer: '学校',
        explanation: '「学校」は「school」の意味です。',
        difficulty: 2,
        category: 'vocabulary',
        subcategory: 'places',
        tags: ['N4', 'vocabulary', 'places']
    },
    {
        question_id: 'N4-GRAMMAR-001',
        level: 'N4',
        type: 'grammar',
        question_text: '毎朝、７時に＿＿ます。',
        options: ['起き', '寝', '食べ', '勉強'],
        correct_answer: '起き',
        explanation: '「起きます」は「to wake up」の意味です。',
        difficulty: 2,
        category: 'grammar',
        subcategory: 'daily',
        tags: ['N4', 'grammar', 'daily']
    },
    {
        question_id: 'N4-VOCAB-002',
        level: 'N4',
        type: 'vocabulary',
        question_text: 'この本は＿＿です。',
        options: ['安い', '高い', '大きい', '小さい'],
        correct_answer: '安い',
        explanation: '「安い」は「cheap」の意味です。',
        difficulty: 2,
        category: 'vocabulary',
        subcategory: 'adjectives',
        tags: ['N4', 'vocabulary', 'adjectives']
    },
    {
        question_id: 'N4-GRAMMAR-002',
        level: 'N4',
        type: 'grammar',
        question_text: '友達と＿＿に行きました。',
        options: ['一緒に', '一人で', '二人で', '三人で'],
        correct_answer: '一緒に',
        explanation: '「一緒に」は「together」の意味です。',
        difficulty: 2,
        category: 'grammar',
        subcategory: 'adverbs',
        tags: ['N4', 'grammar', 'adverbs']
    },
    
    // N3 级别题目
    {
        question_id: 'N3-VOCAB-001',
        level: 'N3',
        type: 'vocabulary',
        question_text: 'この本はとても＿＿です。',
        options: ['面白い', '難しい', '簡単', '大きい'],
        correct_answer: '面白い',
        explanation: '「面白い」は「interesting」の意味です。',
        difficulty: 3,
        category: 'vocabulary',
        subcategory: 'adjectives',
        tags: ['N3', 'vocabulary', 'adjectives']
    },
    {
        question_id: 'N3-GRAMMAR-001',
        level: 'N3',
        type: 'grammar',
        question_text: '雨が降っているので、傘を＿＿行きました。',
        options: ['持って', '持たない', '持ち', '持た'],
        correct_answer: '持って',
        explanation: '「持って」は「with」の意味で、動詞のて形です。',
        difficulty: 3,
        category: 'grammar',
        subcategory: 'te-form',
        tags: ['N3', 'grammar', 'te-form']
    },
    {
        question_id: 'N3-VOCAB-002',
        level: 'N3',
        type: 'vocabulary',
        question_text: '彼は＿＿になりました。',
        options: ['医者', '教師', '会社員', '学生'],
        correct_answer: '医者',
        explanation: '「医者」は「doctor」の意味です。',
        difficulty: 3,
        category: 'vocabulary',
        subcategory: 'jobs',
        tags: ['N3', 'vocabulary', 'jobs']
    },
    {
        question_id: 'N3-GRAMMAR-002',
        level: 'N3',
        type: 'grammar',
        question_text: '彼は＿＿から来ました。',
        options: ['東京', '大阪', '京都', '福岡'],
        correct_answer: '東京',
        explanation: '「から」は「from」の意味です。',
        difficulty: 3,
        category: 'grammar',
        subcategory: 'particles',
        tags: ['N3', 'grammar', 'particles']
    },
    
    // N2 级别题目
    {
        question_id: 'N2-VOCAB-001',
        level: 'N2',
        type: 'vocabulary',
        question_text: '彼は会社を＿＿後、海外旅行に行きました。',
        options: ['辞めて', '入って', '始めて', '続けて'],
        correct_answer: '辞めて',
        explanation: '「辞めて」は「quit」の意味です。',
        difficulty: 4,
        category: 'vocabulary',
        subcategory: 'work',
        tags: ['N2', 'vocabulary', 'work']
    },
    {
        question_id: 'N2-GRAMMAR-001',
        level: 'N2',
        type: 'grammar',
        question_text: 'その計画は実行に＿＿難しいだろう。',
        options: ['移すのが', '移るのが', '移すことが', '移ることが'],
        correct_answer: '移すのが',
        explanation: '「移す」は「to move/transfer」の意味で、「のが」は形式名詞です。',
        difficulty: 4,
        category: 'grammar',
        subcategory: 'noun-phrase',
        tags: ['N2', 'grammar', 'noun-phrase']
    },
    {
        question_id: 'N2-VOCAB-002',
        level: 'N2',
        type: 'vocabulary',
        question_text: 'この計画は＿＿です。',
        options: ['実現可能', '不可能', '難しい', '簡単'],
        correct_answer: '実現可能',
        explanation: '「実現可能」は「feasible」の意味です。',
        difficulty: 4,
        category: 'vocabulary',
        subcategory: 'abstract',
        tags: ['N2', 'vocabulary', 'abstract']
    },
    {
        question_id: 'N2-GRAMMAR-002',
        level: 'N2',
        type: 'grammar',
        question_text: '彼は＿＿に成功しました。',
        options: ['努力', '勉強', '仕事', '試験'],
        correct_answer: '努力',
        explanation: '「努力に成功する」は「succeed through effort」の意味です。',
        difficulty: 4,
        category: 'grammar',
        subcategory: 'set-phrase',
        tags: ['N2', 'grammar', 'set-phrase']
    },
    
    // N1 级别题目
    {
        question_id: 'N1-VOCAB-001',
        level: 'N1',
        type: 'vocabulary',
        question_text: 'その提案は実現可能性が＿＿と思われる。',
        options: ['高い', '低い', '大きい', '小さい'],
        correct_answer: '高い',
        explanation: '「高い」は「high」の意味で、「可能性が高い」は「high possibility」です。',
        difficulty: 5,
        category: 'vocabulary',
        subcategory: 'abstract',
        tags: ['N1', 'vocabulary', 'abstract']
    },
    {
        question_id: 'N1-GRAMMAR-001',
        level: 'N1',
        type: 'grammar',
        question_text: '彼の言うことは常に信頼に＿＿。',
        options: ['足る', '足りる', '及ぶ', '及ぼす'],
        correct_answer: '足る',
        explanation: '「信頼に足る」は「worthy of trust」の意味です。',
        difficulty: 5,
        category: 'grammar',
        subcategory: 'set-phrase',
        tags: ['N1', 'grammar', 'set-phrase']
    },
    {
        question_id: 'N1-VOCAB-002',
        level: 'N1',
        type: 'vocabulary',
        question_text: '彼は＿＿な意見を述べました。',
        options: ['独創的', '一般的', '普通', '特別'],
        correct_answer: '独創的',
        explanation: '「独創的」は「original」の意味です。',
        difficulty: 5,
        category: 'vocabulary',
        subcategory: 'abstract',
        tags: ['N1', 'vocabulary', 'abstract']
    },
    {
        question_id: 'N1-GRAMMAR-002',
        level: 'N1',
        type: 'grammar',
        question_text: '彼の行動は常に＿＿に基づいている。',
        options: ['論理', '感情', '直感', '経験'],
        correct_answer: '論理',
        explanation: '「論理に基づく」は「based on logic」の意味です。',
        difficulty: 5,
        category: 'grammar',
        subcategory: 'set-phrase',
        tags: ['N1', 'grammar', 'set-phrase']
    },
    
    // 新增：听写题（基于日本新闻和事件）
    {
        question_id: 'N3-DICTATION-001',
        level: 'N3',
        type: 'dictation',
        question_text: '日本の首都は東京です。',
        correct_answer: '日本の首都は東京です。',
        explanation: '这是关于日本首都的基本事实。',
        difficulty: 3,
        category: 'dictation',
        subcategory: 'basic-facts',
        tags: ['N3', 'dictation', 'basic-facts', 'news']
    },
    {
        question_id: 'N2-DICTATION-001',
        level: 'N2',
        type: 'dictation',
        question_text: '東京オリンピックは2020年に開催されました。',
        correct_answer: '東京オリンピックは2020年に開催されました。',
        explanation: '东京奥运会于2020年举行（实际因疫情推迟到2021年）。',
        difficulty: 4,
        category: 'dictation',
        subcategory: 'events',
        tags: ['N2', 'dictation', 'events', 'news']
    },
    {
        question_id: 'N1-DICTATION-001',
        level: 'N1',
        type: 'dictation',
        question_text: '日本政府は新しい経済政策を発表しました。',
        correct_answer: '日本政府は新しい経済政策を発表しました。',
        explanation: '日本政府发布了新的经济政策。',
        difficulty: 5,
        category: 'dictation',
        subcategory: 'politics',
        tags: ['N1', 'dictation', 'politics', 'news']
    },
    {
        question_id: 'N3-DICTATION-002',
        level: 'N3',
        type: 'dictation',
        question_text: '富士山は日本で一番高い山です。',
        correct_answer: '富士山は日本で一番高い山です。',
        explanation: '富士山是日本最高的山。',
        difficulty: 3,
        category: 'dictation',
        subcategory: 'geography',
        tags: ['N3', 'dictation', 'geography', 'news']
    },
    {
        question_id: 'N2-DICTATION-002',
        level: 'N2',
        type: 'dictation',
        question_text: '日本の人口は1億2千万人ぐらいです。',
        correct_answer: '日本の人口は1億2千万人ぐらいです。',
        explanation: '日本的人口约为1.2亿。',
        difficulty: 4,
        category: 'dictation',
        subcategory: 'demographics',
        tags: ['N2', 'dictation', 'demographics', 'news']
    },
    {
        question_id: 'N1-DICTATION-002',
        level: 'N1',
        type: 'dictation',
        question_text: '東京証券取引所は日本最大の株式市場です。',
        correct_answer: '東京証券取引所は日本最大の株式市場です。',
        explanation: '东京证券交易所是日本最大的股票市场。',
        difficulty: 5,
        category: 'dictation',
        subcategory: 'economy',
        tags: ['N1', 'dictation', 'economy', 'news']
    },
    {
        question_id: 'N3-DICTATION-003',
        level: 'N3',
        type: 'dictation',
        question_text: '日本の国旗は日章旗と呼ばれています。',
        correct_answer: '日本の国旗は日章旗と呼ばれています。',
        explanation: '日本的国旗被称为日章旗。',
        difficulty: 3,
        category: 'dictation',
        subcategory: 'culture',
        tags: ['N3', 'dictation', 'culture', 'news']
    }
];

/**
 * 初始化日语题库
 */
async function initializeJapaneseDatabase() {
    console.log('🚀 开始初始化日语题库...');
    
    try {
        // 初始化数据库管理器
        await japaneseDatabaseManager.initialize();
        
        // 添加示例题目
        console.log('📝 添加示例题目...');
        const result = await japaneseDatabaseManager.addQuestions(sampleQuestions);
        
        console.log('✅ 题目添加完成:');
        console.log(`   总计: ${result.total} 题`);
        console.log(`   成功: ${result.successful} 题`);
        console.log(`   失败: ${result.failed} 题`);
        
        // 获取题库统计信息
        const stats = await japaneseDatabaseManager.getStatistics();
        console.log('📊 题库统计信息:');
        stats.forEach(stat => {
            console.log(`   ${stat.level} ${stat.type}: ${stat.count}题 (难度: ${stat.avg_difficulty.toFixed(1)})`);
        });
        
        console.log('🎉 日语题库初始化成功！');
        
    } catch (error) {
        console.error('❌ 初始化失败:', error);
    } finally {
        // 关闭数据库连接
        japaneseDatabaseManager.close();
    }
}

// 执行初始化
if (require.main === module) {
    initializeJapaneseDatabase();
}

module.exports = {
    initializeJapaneseDatabase,
    sampleQuestions
};
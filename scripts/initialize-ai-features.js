/**
 * 重新初始化AI特征库
 * 确保特征库文件被正确创建
 */

const fs = require('fs');
const path = require('path');

// 确保数据目录存在
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
    console.log('✅ 数据目录创建成功');
}

// 创建AI特征库文件
const featuresPath = path.join(dataDir, 'ai-features.json');

const aiFeatures = {
    version: '1.0.0',
    lastUpdated: new Date().toISOString(),
    categories: {
        text: {
            description: '文本处理相关特征',
            features: [
                'text-generation',
                'translation',
                'summarization',
                'sentiment-analysis',
                'named-entity-recognition',
                'part-of-speech-tagging',
                'dependency-parsing',
                'text-classification',
                'question-answering',
                'chatbot',
                'dialogue-management',
                'text-similarity',
                'keyword-extraction',
                'topic-modeling',
                'text-clustering'
            ]
        },
        code: {
            description: '代码处理相关特征',
            features: [
                'code-generation',
                'code-completion',
                'code-review',
                'bug-detection',
                'code-refactoring',
                'program-synthesis',
                'algorithm-design',
                'data-structures',
                'software-engineering',
                'devops',
                'api-design',
                'database-design'
            ]
        },
        business: {
            description: '商业智能相关特征',
            features: [
                'business-intelligence',
                'market-analysis',
                'competitive-analysis',
                'business-planning',
                'financial-analysis',
                'risk-assessment',
                'project-management',
                'operations-research',
                'supply-chain',
                'customer-analysis'
            ]
        },
        creative: {
            description: '创意内容相关特征',
            features: [
                'creative-writing',
                'storytelling',
                'poetry',
                'lyrics',
                'script-writing',
                'copywriting',
                'marketing-content',
                'branding',
                'design-concepts',
                'creative-strategy'
            ]
        },
        education: {
            description: '教育相关特征',
            features: [
                'tutoring',
                'homework-help',
                'exam-preparation',
                'language-learning',
                'skill-assessment',
                'curriculum-design',
                'educational-content',
                'learning-strategies',
                'career-counseling'
            ]
        },
        multilingual: {
            description: '多语言处理特征',
            features: [
                'multilingual',
                'translation',
                'language-detection',
                'cross-lingual',
                'multilingual-summary',
                'multilingual-qa'
            ]
        },
        domain: {
            description: '专业领域相关特征',
            features: [
                'e-commerce',
                'healthcare',
                'legal',
                'finance',
                'technology',
                'science',
                'engineering',
                'art',
                'music',
                'sports',
                'gaming'
            ]
        },
        technical: {
            description: '技术能力相关特征',
            features: [
                'problem-solving',
                'critical-thinking',
                'logical-reasoning',
                'mathematical-reasoning',
                'spatial-reasoning',
                'pattern-recognition',
                'abstraction',
                'algorithmic-thinking',
                'system-design'
            ]
        },
        assistant: {
            description: '个人助理相关特征',
            features: [
                'personal-assistant',
                'schedule-management',
                'task-management',
                'reminders',
                'note-taking',
                'research-assistant',
                'shopping-assistant',
                'travel-assistant',
                'health-assistant'
            ]
        },
        smart: {
            description: '智能设备相关特征',
            features: [
                'smart-home',
                'iot-integration',
                'device-control',
                'home-automation',
                'energy-management',
                'security-monitoring'
            ]
        }
    },
    modelFeatures: {
        model_deepseek: ['text-generation', 'code-generation', 'problem-solving', 'logical-reasoning'],
        model_chatgpt: ['text-generation', 'chatbot', 'question-answering', 'translation'],
        model_qwen: ['text-generation', 'multilingual', 'translation', 'summarization'],
        model_doubao: ['text-generation', 'creative-writing', 'storytelling', 'poetry'],
        model_volcano: ['text-generation', 'multimodal', 'creative-content', 'marketing'],
        model_tencent: ['text-generation', 'business-intelligence', 'market-analysis', 'project-management'],
        model_ali: ['text-generation', 'e-commerce', 'customer-analysis', 'supply-chain'],
        model_xiaomi: ['text-generation', 'smart-home', 'iot-integration', 'device-control'],
        model_apple: ['text-generation', 'on-device-processing', 'personal-assistant', 'task-management'],
        model_afu: ['text-generation', 'personal-assistant', 'schedule-management', 'research-assistant']
    }
};

// 保存AI特征库文件
fs.writeFileSync(featuresPath, JSON.stringify(aiFeatures, null, 2));
console.log('✅ AI特征库文件创建成功');
console.log(`   文件路径: ${featuresPath}`);
console.log(`   版本: ${aiFeatures.version}`);
console.log(`   类别数: ${Object.keys(aiFeatures.categories).length}`);
console.log(`   总特征数: ${Object.values(aiFeatures.categories).reduce((sum, cat) => sum + cat.features.length, 0)}`);
console.log(`   模型映射数: ${Object.keys(aiFeatures.modelFeatures).length}`);
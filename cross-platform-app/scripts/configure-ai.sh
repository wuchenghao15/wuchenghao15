#!/bin/bash

# AI配置初始化脚本
echo "=========================================="
echo "  AI配置初始化"
echo "=========================================="
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm未安装"
    exit 1
fi

echo "[1/5] 检查项目结构..."
if [ ! -d "src/services" ]; then
    echo "❌ 项目结构不正确"
    exit 1
fi
echo "✓ 项目结构正确"

echo ""
echo "[2/5] 检查AI服务文件..."
if [ ! -f "src/services/AIService.js" ]; then
    echo "❌ AIService.js不存在"
    exit 1
fi
echo "✓ AIService.js存在"

echo ""
echo "[3/5] 检查依赖..."
echo "检查axios..."
if grep -q "axios" package.json; then
    echo "✓ axios已安装"
else
    echo "⚠️ axios未安装，将在安装依赖时添加"
fi

echo "检查@react-native-async-storage/async-storage..."
if grep -q "@react-native-async-storage/async-storage" package.json; then
    echo "✓ async-storage已安装"
else
    echo "⚠️ async-storage未安装，将在安装依赖时添加"
fi

echo ""
echo "[4/5] 配置AI默认参数..."

# 创建默认配置文件
cat > src/config/ai.config.js << 'EOF'
// AI服务配置
export const AI_CONFIG = {
  // 启用AI功能
  enabled: true,
  
  // 默认模型
  defaultModel: 'gpt-4',
  
  // 可用模型列表
  availableModels: [
    {id: 'gpt-4', name: 'GPT-4', description: '最先进的模型，适合复杂任务'},
    {id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: '快速高效，性价比高'},
    {id: 'claude-3', name: 'Claude 3', description: '长上下文支持，适合文档分析'},
    {id: 'llama-3', name: 'Llama 3', description: '开源模型，隐私友好'},
  ],
  
  // 默认参数
  defaultParameters: {
    maxTokens: 1024,
    temperature: 0.7,
    timeout: 30000,
    maxRetries: 3,
    retryDelay: 1000,
  },
  
  // API端点配置
  endpoints: {
    chat: '/api/ai/chat',
    analyze: '/api/ai/analyze',
    generateQuestions: '/api/ai/generate/questions',
    correct: '/api/ai/correct',
    status: '/api/ai/status',
    suggest: '/api/ai/suggest',
    summarize: '/api/ai/summarize',
    translate: '/api/ai/translate',
    classify: '/api/ai/classify',
  },
  
  // 系统提示词
  systemPrompt: `你是一个智能教育助手，专门帮助学生学习和备考。
请使用中文回答，保持友好、专业的语气。
对于学习问题，请提供详细的解释和示例。
对于考试相关问题，请给出准确的答案和解题思路。`,
  
  // 功能开关
  features: {
    chat: true,
    questionGeneration: true,
    correction: true,
    suggestions: true,
    summarization: true,
    translation: true,
    classification: true,
  },
};

export default AI_CONFIG;
EOF

echo "✓ AI配置文件已创建"

echo ""
echo "[5/5] 验证配置..."
if [ -f "src/config/ai.config.js" ]; then
    echo "✓ AI配置文件验证通过"
else
    echo "❌ AI配置文件创建失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "  AI配置初始化完成！"
echo "=========================================="
echo ""
echo "配置文件: src/config/ai.config.js"
echo ""
echo "默认配置:"
echo "  - 模型: GPT-4"
echo "  - 最大Token: 1024"
echo "  - 温度: 0.7"
echo "  - 超时时间: 30秒"
echo "  - 最大重试次数: 3次"
echo ""
echo "可用功能:"
echo "  ✓ AI聊天对话"
echo "  ✓ 智能题目生成"
echo "  ✓ 作业批改"
echo "  ✓ 学习建议"
echo "  ✓ 文本摘要"
echo "  ✓ 翻译"
echo "  ✓ 文本分类"
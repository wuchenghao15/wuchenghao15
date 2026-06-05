# AI题库优化员工使用指南

## 概述

AI题库优化员工是MTSCOS 9年教育系统中的智能组件，专门用于优化和管理题库内容。它能够自动分析题目难度、评估质量、生成优化建议，并提供批量处理功能。

## 核心功能

### 1. 题目分析

```python
from app.ai.question_bank_ai import question_bank_ai

# 分析单个题目
question = {
    'content': '请分析下列日语形容词的用法区别：美しい、花しい、綺麗だ',
    'options': ['A. 美し是形容词', 'B. 花しい表示心情愉悦', 'C. 綺麗主要用于视觉感受', 'D. 以上都正确'],
    'answer': 'D',
    'explanation': '美しい表示内在美，花しい表示令人惊叹的美，綺麗主要用于外在的视觉美。',
    'tags': ['日语', '形容词', '词汇辨析']
}

analysis = question_bank_ai.analyze_question(question)

# 返回结果包含:
# - difficulty: 难度等级 (easy/medium/hard)
# - question_type: 题目类型 (choice/fill/essay/code)
# - keywords: 关键词列表
# - quality: 质量评分和建议
```

### 2. 题目优化

```python
# 优化单个题目
optimized = question_bank_ai.optimize_question(question)

# 批量优化题目
questions = [q1, q2, q3]
results = question_bank_ai.process_question_batch(questions, optimize=True)

# results 包含:
# - total: 总题数
# - analyzed: 已分析数
# - optimized: 已优化数
# - average_quality_score: 平均质量分数
# - quality_scores: 各题质量分数列表
```

### 3. 优化建议

```python
# 生成优化建议
suggestions = question_bank_ai.generate_suggestions(question)

# 返回结果包含:
# - current_quality_score: 当前质量分数
# - suggestions: 改进建议列表
# - strengths: 题目优点列表
# - recommended_actions: 推荐操作列表
```

### 4. 统计分析

```python
# 获取统计报告
report = question_bank_ai.get_statistics_report()

# report 包含:
# - distribution: 题目分布统计
# - quality: 质量报告
# - optimization_potential: 优化潜力分析

# 获取优化摘要
summary = question_bank_ai.get_optimization_summary()

# summary 包含:
# - total_questions: 总题数
# - average_quality_score: 平均质量分数
# - needs_optimization: 需优化题目数
# - explanation_rate: 解析覆盖率
# - tag_rate: 标签覆盖率
# - recommendations: 优化建议
```

## API接口

AI题库优化员工提供以下RESTful API接口：

### 1. 分析题目
```
POST /api/question-bank-ai/ai/analyze
Content-Type: application/json

{
    "content": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "explanation": "解析...",
    "tags": ["标签1", "标签2"]
}
```

### 2. 优化题目
```
POST /api/question-bank-ai/ai/optimize
Content-Type: application/json

{
    "content": "题目内容",
    "question_type": "choice",
    "answer": "B"
}
```

### 3. 批量优化
```
POST /api/question-bank-ai/ai/batch-optimize
Content-Type: application/json

{
    "questions": [
        {"content": "题目1...", "answer": "A"},
        {"content": "题目2...", "answer": "B"},
        {"content": "题目3...", "answer": "C"}
    ]
}
```

### 4. 获取建议
```
POST /api/question-bank-ai/ai/suggestions
Content-Type: application/json

{
    "content": "题目内容",
    "answer": "答案"
}
```

### 5. 统计报告
```
GET /api/question-bank-ai/ai/statistics
```

### 6. 优化摘要
```
GET /api/question-bank-ai/ai/summary
```

### 7. AI能力
```
GET /api/question-bank-ai/ai/capabilities
```

## 难度等级

AI自动将题目分为三个难度等级：

- **easy (简单)**: 基础、入门、认识、了解类题目
- **medium (中等)**: 理解、掌握、应用、分析类题目
- **hard (困难)**: 综合、复杂、创新、设计、评估类题目

## 题目类型

AI支持识别以下题目类型：

- **choice (选择题)**: 选择、判断类题目
- **fill (填空题)**: 填空、补全类题目
- **essay (论述题)**: 论述、说明、解释类题目
- **code (代码题)**: 代码、程序、算法类题目

## 质量评估标准

AI根据以下标准评估题目质量（0-100分）：

| 评估项目 | 分数范围 | 评估标准 |
|---------|---------|---------|
| 内容长度 | -10~+10 | 10-500字符为最佳 |
| 选项完整性 | -20~+10 | 至少2个选项，4个为佳 |
| 答案完整性 | -30~+20 | 必须有答案 |
| 解析完整性 | -5~+5 | 有解析为佳 |
| 标签完整性 | -5~+5 | 至少3个标签为佳 |

## 使用场景

### 1. 新题目录入
在新题目录入时，使用AI进行自动分析和优化：

```python
# 录入新题目
new_question = {
    'content': '请分析「美しい」和「綺麗」的区别'
}

# AI自动分析
analysis = question_bank_ai.analyze_question(new_question)
print(f"建议难度: {analysis['difficulty']}")
print(f"建议类型: {analysis['question_type']}")

# AI自动优化
optimized = question_bank_ai.optimize_question(new_question)
# 自动添加标签、优化格式等
```

### 2. 题库质量检查
对现有题库进行质量评估：

```python
# 获取质量报告
report = question_bank_ai.get_statistics_report()

print(f"平均质量分数: {summary['average_quality_score']}")
print(f"需优化题目: {summary['needs_optimization']}")
print(f"解析覆盖率: {summary['explanation_rate']}%")

# 查看优化建议
for rec in summary['recommendations']:
    print(f"- {rec}")
```

### 3. 批量优化
对大量题目进行批量优化：

```python
# 获取所有待优化题目
potential = report['optimization_potential']

# 批量优化
results = question_bank_ai.process_question_batch(potential['needs_explanation'], optimize=True)
print(f"优化了 {results['optimized']} 道题目")
print(f"平均质量提升: {results['average_quality_score']}")
```

## 集成到Flask应用

在Flask应用中，AI题库优化API已自动注册到路由中：

```python
from app import create_app

app = create_app()

# API路由已自动注册:
# - /api/question-bank-ai/ai/analyze
# - /api/question-bank-ai/ai/optimize
# - /api/question-bank-ai/ai/batch-optimize
# - /api/question-bank-ai/ai/suggestions
# - /api/question-bank-ai/ai/statistics
# - /api/question-bank-ai/ai/summary
# - /api/question-bank-ai/ai/capabilities
```

## 扩展功能

AI题库优化员工支持以下扩展功能：

1. **自定义难度关键词**: 可以扩展 `difficulty_keywords` 字典来调整难度识别规则
2. **自定义类型关键词**: 可以扩展 `type_keywords` 字典来调整类型识别规则
3. **自定义质量标准**: 可以修改 `assess_quality` 方法来调整质量评估标准
4. **数据库集成**: 可以通过 `QuestionStatistics` 类与数据库集成

## 注意事项

1. AI分析基于关键词匹配，可能不完全准确
2. 建议将AI分析结果作为参考，由人工审核确认
3. 批量处理时注意API调用频率限制
4. 定期进行题库质量评估和优化

## 版本历史

- **v1.0.0** (2024-04-30): 初始版本
  - 实现题目分析功能
  - 实现题目优化功能
  - 实现质量评估功能
  - 实现统计报告功能
  - 提供RESTful API接口

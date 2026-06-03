# MTSCOS AI Project - AI引擎架构 v3.0

## 概述

本项目已升级到 **AI引擎 v3.0**，提供了增强的多模型支持、智能路由、异步处理、响应缓存等功能。

## 升级特性

| 特性 | 说明 |
|------|------|
| **多模型支持** | OpenAI、Anthropic、Google Gemini、Ollama、DeepSeek、Qwen、Local |
| **智能路由** | 基于优先级和健康状态自动选择最佳模型 |
| **异步处理** | 支持异步生成AI响应，提升并发处理能力 |
| **响应缓存** | LRU缓存策略，支持自定义TTL和容量 |
| **故障转移** | 自动降级到备用模型，确保服务可用性 |
| **性能监控** | 实时收集请求指标和延迟数据 |
| **提示词模板** | 内置8种专业模板，支持自定义扩展 |
| **流式响应** | 支持流式输出，提升用户体验 |

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI引擎层 (v3.0)                               │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│   │   AI模型路由器   │  │   异步客户端     │  │   响应缓存      │      │
│   │ (智能选择)      │  │ (并发控制)      │  │ (LRU淘汰)      │      │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘      │
│            │                    │                    │                │
│            └────────────────────┼────────────────────┘                │
│                                 ▼                                    │
│                    ┌─────────────────────┐                           │
│                    │      多模型支持      │                           │
│                    │ OpenAI/Claude/Gemini│                           │
│                    │ Ollama/DeepSeek/Qwen│                           │
│                    └─────────────────────┘                           │
│                                 │                                    │
│         ┌───────────────────────┼───────────────────────┐            │
│         ▼                       ▼                       ▼            │
│   ┌───────────┐         ┌───────────┐         ┌───────────┐          │
│   │ 提示词模板│         │ 规则引擎   │         │ 性能监控   │          │
│   │   管理器  │         │           │         │           │          │
│   └───────────┘         └───────────┘         └───────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

## AI引擎使用指南

### 快速开始

```python
from ai_engines.ai_engine_v3 import get_ai_engine

# 获取AI引擎实例
engine = get_ai_engine()

# 生成响应(使用默认设置)
response = engine.generate("你好,有什么可以帮助我的?")
print(response['content'])

# 使用提示词模板
response = engine.generate("分析一下销售数据", template='analyst')

# 指定模型类型
response = engine.generate("生成代码", model_type='openai', template='coder')

# 流式响应
for chunk in engine.stream_generate("请分析这个问题"):
    print(chunk['content'], end='')
```

### 支持的模型类型

| 模型类型 | 名称 | 优先级 | 默认端点 |
|----------|------|--------|----------|
| `openai` | OpenAI GPT-4o | 1 | https://api.openai.com/v1 |
| `anthropic` | Anthropic Claude 3.5 | 2 | https://api.anthropic.com/v1 |
| `google` | Google Gemini 1.5 | 3 | https://generativelanguage.googleapis.com/v1 |
| `ollama` | Llama 3.1 | 5 | http://localhost:11434 |
| `deepseek` | DeepSeek | 4 | https://api.deepseek.com/v1 |
| `qwen` | Qwen 2 | 4 | https://api.qwenlm.cn/v1 |
| `local` | Local Model | 10 | http://localhost:8000/v1 |

### 环境变量配置

```bash
# OpenAI API Key
export OPENAI_API_KEY="your-key"

# Anthropic API Key
export ANTHROPIC_API_KEY="your-key"

# Google API Key
export GOOGLE_API_KEY="your-key"

# DeepSeek API Key
export DEEPSEEK_API_KEY="your-key"

# Qwen API Key
export QWEN_API_KEY="your-key"
```

### 提示词模板

内置8种专业模板：

| 模板名称 | 用途 | 场景 |
|----------|------|------|
| `analyst` | 数据分析师 | 数据分析、报告生成 |
| `customer_service` | 客服代表 | 客户服务、问题解答 |
| `teacher` | 教师助手 | 教育教学、知识讲解 |
| `writer` | 内容创作 | 文章写作、内容生成 |
| `translator` | 翻译专家 | 多语言翻译 |
| `coder` | 代码助手 | 代码生成、技术文档 |
| `exam_generator` | 试题生成器 | 考试题目生成 |
| `summarizer` | 文本摘要器 | 文章摘要、要点提取 |

### 添加自定义模板

```python
engine.add_prompt_template('my_template', {
    'name': '自定义模板',
    'system_prompt': '你是一位专业助手，请根据用户需求提供帮助。',
    'placeholder': '{input}',
    'description': '自定义场景'
})

response = engine.generate("你的需求", template='my_template')
```

### 智能路由配置

```python
# 为特定任务类型设置首选模型
engine.set_preferred_model('code_generation', 'openai')
engine.set_preferred_model('creative_writing', 'anthropic')
engine.set_preferred_model('analysis', 'google')

# 引擎会根据任务类型自动选择最佳模型
response = engine.generate("编写Python代码", task_type='code_generation')
```

### 缓存配置

```python
# 获取缓存统计
cache_stats = engine.get_cache_stats()
print(f"缓存命中率: {cache_stats['hit_rate']}%")

# 清空缓存
engine.clear_cache()
```

### 性能监控

```python
# 获取引擎统计
stats = engine.get_stats()

# 模型状态
for model_type, info in stats['models'].items():
    print(f"{info['name']}: {info['status']}")

# 请求统计
print(f"总请求数: {stats['monitor']['total_requests']}")
print(f"平均延迟: {stats['monitor']['latency']['success']['avg']}ms")
```

## 核心类说明

### AIEngineV3

AI引擎核心类，提供以下方法：

| 方法 | 说明 |
|------|------|
| `generate()` | 同步生成AI响应 |
| `generate_async()` | 异步生成AI响应 |
| `stream_generate()` | 流式生成响应 |
| `get_models()` | 获取所有模型状态 |
| `set_preferred_model()` | 设置任务类型的首选模型 |
| `add_prompt_template()` | 添加提示词模板 |
| `get_prompt_templates()` | 获取所有模板 |
| `clear_cache()` | 清空缓存 |
| `get_stats()` | 获取引擎统计 |

### AIModel

模型封装类，管理单个AI模型的状态和配置。

### AIModelRouter

智能路由器，根据优先级、健康状态和任务类型选择最佳模型。

### AICache

LRU缓存系统，支持自定义容量和TTL。

### PromptTemplateManager

提示词模板管理器，管理内置和自定义模板。

## 配置示例

```python
config = {
    'cache_max_size': 5000,
    'cache_ttl': 3600,
    'max_history': 50,
    'models': {
        'openai': {
            'enabled': True,
            'priority': 1,
            'max_concurrent': 10,
            'api_key': 'your-key'
        },
        'local': {
            'enabled': True,
            'priority': 5,
            'endpoint': 'http://localhost:8000/v1'
        }
    }
}

engine = AIEngineV3(config)
```

## 故障转移机制

引擎具备自动故障转移能力：

1. **健康检查** - 每个模型定期检查健康状态
2. **自动降级** - 主模型失败时自动切换到备用模型
3. **重试机制** - 支持多模型重试
4. **状态恢复** - 故障模型恢复后自动重新加入可用池

## 性能优化

| 优化项 | 说明 |
|--------|------|
| **缓存** | LRU策略减少重复请求 |
| **异步** | 非阻塞调用提升并发 |
| **并发控制** | 限制每个模型的并发请求数 |
| **智能路由** | 选择最优模型减少延迟 |

## 总结

AI引擎 v3.0 提供了：

1. **多模型支持** - 7种AI模型，覆盖主流提供商
2. **智能路由** - 自动选择最佳可用模型
3. **高性能** - 异步处理 + 缓存机制
4. **高可用** - 自动故障转移和降级
5. **易用性** - 简洁的API接口和丰富的模板

所有功能已完整实现，可以直接使用！
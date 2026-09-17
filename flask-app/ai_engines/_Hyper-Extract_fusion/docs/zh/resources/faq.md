# 常见问题

关于 Hyper-Extract 的常见问题解答。

---

## 通用问题

### Hyper-Extract 是什么？

Hyper-Extract 是一个基于大语言模型的知识提取框架，可以将非结构化文本转换为结构化的知识图谱、列表、模型等。

### 它可以用来做什么？

- 研究论文分析
- 知识库构建
- 文档处理
- 信息提取
- 问答系统

### 它是免费的吗？

本软件是开源的（Apache-2.0 协议）。您需要从支持的 LLM 提供商获取 API 密钥（OpenAI、Anthropic、DeepSeek、阿里云百炼或本地 vLLM）。

---

## 安装问题

### 系统要求是什么？

- Python 3.11+
- 任意支持的提供商的 API 密钥（OpenAI、Anthropic、DeepSeek、百炼或本地 vLLM）

### 如何安装？

```bash
pip install hyperextract
```

### 安装失败，提示 "No module named 'hyperextract'"

尝试：
```bash
pip install --upgrade hyperextract
```

或使用虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install hyperextract
```

---

## 配置问题

### 在哪里设置 API 密钥？

**选项 1**：命令行

```bash
# OpenAI / 百炼（一步到位）
he config init -p openai -k YOUR_API_KEY
he config init -p bailian -k YOUR_API_KEY

# Anthropic / DeepSeek（LLM + 独立嵌入器）
he config llm -p deepseek -k YOUR_DEEPSEEK_API_KEY
he config embedder -p openai -k YOUR_OPENAI_API_KEY
```

**选项 2**：环境变量

```bash
export OPENAI_API_KEY=your-api-key        # OpenAI/百炼
export ANTHROPIC_API_KEY=your-api-key     # Anthropic
export DEEPSEEK_API_KEY=your-api-key      # DeepSeek
```

**选项 3**：`.env` 文件
```
OPENAI_API_KEY=your-api-key
```

## 可以使用其他大语言模型提供商吗？

可以！Hyper-Extract 开箱即用支持 OpenAI、Anthropic、DeepSeek、阿里云百炼和本地 vLLM：

```bash
# OpenAI / 百炼
he config init -p openai -k YOUR_API_KEY

# DeepSeek / Anthropic（仅 LLM，需搭配 OpenAI 嵌入器）
he config llm -p deepseek -k YOUR_DEEPSEEK_API_KEY
he config embedder -p openai -k YOUR_OPENAI_API_KEY
```

对于自定义的 OpenAI 兼容端点：
```bash
he config llm --base-url https://your-provider.com/v1 -k YOUR_API_KEY
```

参见 [Provider 系统](../concepts/provider-system.md) 了解完整兼容性列表。

## 支持哪些模型？

- **OpenAI**：gpt-4o、gpt-4o-mini、gpt-5
- **Anthropic**：claude-opus-4-8、claude-sonnet-4-6、claude-haiku-4-5
- **DeepSeek**：deepseek-v4-flash、deepseek-v4-pro
- **阿里云百炼**：qwen-plus、qwen-turbo、qwen3.6-plus
- **本地 vLLM**：通过 vLLM 提供的任意模型（如 Qwen/Qwen3.5-9B）

参见 [Provider 系统](../concepts/provider-system.md) 了解完整兼容性表格。

---

## 使用问题

### 应该使用哪个模板？

参见[如何选择](../templates/how-to-choose.md)指南或使用：
```bash
he list template
```

### 如何处理 PDF 文件？

直接喂入即可（需要可选的 ingest extra——同时支持 Word、PowerPoint、Excel、HTML、EPUB 等）：
```bash
pip install "hyperextract[ingest]"
he parse document.pdf -t general/graph -o ./ka/ -l zh
```

扫描版（纯图片）PDF 没有文字层——请先做 OCR。完整格式表见 [he parse](../cli/commands/parse.md)。

### 可以处理多个文档吗？

**选项 1**：增量添加
```bash
he parse doc1.md -t general/graph -o ./ka/ -l zh
he feed ./ka/ doc2.md
he feed ./ka/ doc3.md
```

**选项 2**：处理目录
```bash
he parse ./docs/ -t general/graph -o ./ka/ -l zh
```

### 如何提取中文内容？

```bash
he parse doc.md -t general/biography_graph -l zh
```

### 如何从已有知识摘要中删除知识？

```bash
# 硬删除节点（以其为端点的边会一并删除）
he remove ./ka/ --node Apple

# 软删除节点中一条错误/过时的事实，其余内容保留
he remove ./ka/ --edit-node Apple --fact "founded by Steve Jobs" --dry-run
he remove ./ka/ --edit-node Apple --fact "founded by Steve Jobs" -y
```

软删除由大模型在相同 schema 下重写条目，带 key 不变性校验和自动 `data.json` 备份。若要删除**某份文档贡献的全部知识**，请去掉该文档后重建 KA——按文档溯源删除尚未实现。详见 [`he remove`](../cli/commands/remove.md)。

---

## 性能问题

### 为什么提取速度很慢？

- 长文档会被分块并行处理
- 每个分块都需要调用大语言模型
- 建议在批量处理时使用 `--no-index`

### 如何加快速度？

1. 使用更小的分块大小
2. 如果达到速率限制，减少 `max_workers`
3. 并行处理文档（手动）

### 大文档导致内存不足？

分批处理：
```python
for batch in chunks(documents, 5):
    for doc in batch:
        ka.feed_text(doc)
    ka.dump("./checkpoint/")
```

---

## 结果问题

### 数据存储在哪里？

```
./output/
├── data.json      # 提取的知识
├── metadata.json  # 提取信息
└── index/         # 搜索索引
```

### 如何可视化结果？

```bash
he show ./output/
```

或在 Python 中：
```python
# 构建索引以支持可视化中的交互式搜索/对话
result.build_index()

result.show()
```

![交互式可视化](../../assets/zh_show.jpg)

## 可以导出为其他格式吗？

```python
import json

# 导出为 JSON
json_data = result.data.model_dump_json()

# 导出为字典
data_dict = result.data.model_dump()
```

---

## 故障排除

### "API key not found"

```bash
# 指定您的提供商
he config init -p openai -k YOUR_API_KEY
# 或：-p bailian、-p deepseek 等
```

## "Template not found"

列出可用模板：
```bash
he list template
```

### "Index not found" 错误

构建索引：
```bash
he build-index ./output/
```

### 搜索没有返回结果

尝试：
- 使用不同的搜索词
- 增加 `top_k`：`he search ./ka/ "查询" -n 10`
- 检查索引是否已构建：`he info ./ka/`

---

## 高级功能

### 可以创建自定义模板吗？

可以！参见[自定义模板](../python/guides/custom-templates.md)。

### 可以使用自己的提取方法吗？

可以，实现并注册：
```python
from hyperextract.methods import register_method

class MyMethod:
    def extract(self, text):
        # 您的逻辑
        pass

register_method("my_method", MyMethod, "graph", "Description")
```

### 如何集成到我的应用程序中？

```python
from hyperextract import Template

class MyApp:
    def __init__(self):
        self.ka = Template.create("general/graph", "zh")
    
    def process_document(self, text):
        return self.ka.parse(text)
```

---

## 获取更多帮助

- [GitHub Issues](https://github.com/yifanfeng97/hyper-extract/issues)
- [故障排除指南](troubleshooting.md)
- [CLI 文档](../cli/index.md)
- [Python SDK](../python/index.md)

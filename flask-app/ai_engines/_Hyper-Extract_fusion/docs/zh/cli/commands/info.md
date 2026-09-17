# he info

显示知识库的信息和统计信息。

---

## 概要

```bash
he info KA_PATH
```

## 参数

| 参数 | 描述 |
|----------|-------------|
| `KA_PATH` | 知识库目录的路径 |

---

## 描述

显示知识库的元数据和统计信息：

- **路径** — 知识库的位置
- **模板** — 用于提取的模板
- **语言** — 语言代码（en/zh）
- **时间戳** — 创建和最后更新时间
- **统计信息** — 节点数、边数
- **索引状态** — 搜索索引是否已构建
- **来源台账** — 使用 `--sources` 显示贡献过知识的文档

---

## 示例

### 基本用法

```bash
he info ./output/
```

**输出：**
```
Knowledge Abstract Info

Path          ./output/
Template      general/biography_graph
Language      en
Created       2024-01-15 10:30:00
Updated       2024-01-15 10:35:22
Nodes         25
Edges         32
Index         Built
```

### 提取后

```bash
he parse sushi.md -t general/biography_graph -o ./ka/ -l zh
he info ./ka/
```

### Feed 后

```bash
he feed ./ka/ more_content.md
he info ./ka/
# 注意更新的节点/边数和时间戳
```

---

## 输出字段

| 字段 | 描述 |
|-------|-------------|
| `Path` | 知识库的绝对路径 |
| `Template` | 模板标识符（例如 `general/biography_graph`） |
| `Language` | 处理语言（`en` 或 `zh`） |
| `Created` | 初始提取时间戳 |
| `Updated` | 最后修改时间戳 |
| `Nodes` | 实体/项目数量 |
| `Edges` | 关系数量 |
| `Index` | 搜索索引状态（`Built` 或 `Not Built`） |

---

## 来源台账

传入 `--sources` 可以同时显示哪些文档为知识库做出过贡献：

```bash
he info ./ka/ --sources
```

**输出：**
```
Knowledge Abstract Info

Path          ./ka/
Template      general/biography_graph
Language      en
Created       2024-01-15 10:30:00
Updated       2024-01-15 10:35:22
Nodes         25
Edges         32
Index         Built

                        Source Ledger
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Source ID  ┃ Raw Items ┃ Content Hash                       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ doc-1      │        12 │ 9f86d081884c7d659a2febb0c0413a6e…  │
└────────────┴───────────┴────────────────────────────────────┘
```

台账读取自知识库目录中的 `sources_nodes.json` / `sources_edges.json`，在使用 `--source` 摄取文档时写入（参见 [`he feed`](feed.md)）。如果没有台账文件，命令会输出 `No source ledger found`（未找到来源台账）提示，而不是表格。

---

## 用例

### 验证提取

检查提取是否成功：

```bash
he info ./ka/
# 应该显示 Nodes > 0, Edges > 0
```

## 检查索引状态

在使用搜索或聊天之前：

```bash
he info ./ka/
# 如果索引显示 "Not Built"，运行：
he build-index ./ka/
```

## 监控增长

跟踪知识库随时间的增长：

```bash
he info ./ka/
# 喂养更多文档
he feed ./ka/ update.md
he info ./ka/
# 比较节点/边数
```

## 脚本

在自动化脚本中使用：

```bash
#!/bin/bash

if he info ./ka/ 2>/dev/null; then
    echo "Knowledge base exists"
    he feed ./ka/ new_doc.md
else
    echo "Creating new knowledge abstract"
    he parse new_doc.md -t general/biography_graph -o ./ka/ -l zh
fi
```

---

## 故障排除

### "未找到知识库目录"

目录不存在或不包含知识库：

```bash
# 检查目录存在
ls ./ka/

# 应该包含：
# - data.json
# - metadata.json
```

## 元数据缺失

如果元数据损坏，模板/语言显示为 "unknown"：

```bash
he info ./ka/
# Template: [yellow]unknown[/yellow]
# Language: [yellow]unknown[/yellow]
```

知识库仍然可用，但某些功能可能受限。

---

## 另请参见

- [`he parse`](parse.md) — 创建知识库
- [`he feed`](feed.md) — 添加到知识库
- [`he build-index`](build-index.md) — 构建搜索索引

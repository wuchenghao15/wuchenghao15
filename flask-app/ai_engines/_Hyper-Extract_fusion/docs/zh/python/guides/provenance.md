# 来源标注与溯源

追踪哪些文档为知识摘要做出过贡献，跳过未变更的重复喂养，并按文档回滚其贡献，而不影响其余知识。

---

## 概述

**带来源标注**摄取文档（CLI 用 `--source`，Python 用 `source_id=`）会让知识摘要记住该文档：其原始提取结果会保存在**来源台账**中，并记录输入文本的 SHA-256 内容哈希。

溯源提供三项能力：

| 能力 | CLI | Python |
|------|-----|--------|
| **按文档回滚** | `he remove --document ID` | `ka.remove_source(ID)` |
| **变更检测** | `he feed --source` 跳过未变更文档 | `ka.source_content_hash(ID)` |
| **审计** | `he info --sources` | `ka.sources()` |

图谱类知识摘要（graph、hypergraph、时序/空间图谱）默认开启来源追踪。

---

## 带来源标注的摄取

```bash
# 解析时标注（首个文档）
he parse doc1.md -t general/graph -o ./ka/ -l zh --source doc-1

# 喂养进现有知识库时标注
he feed ./ka/ doc2.md --source doc-2
```

```python
from hyperextract import Template

ka = Template.create("general/graph", language="zh")

with open("doc1.md") as f:
    result = ka.parse(f.read(), source_id="doc-1")

result.feed_text(doc2_text, source_id="doc-2")
result.dump("./ka/")
```

## 变更检测

同一来源再次喂养且内容未变化时，`he feed` 会比对内容哈希并完全跳过该文档——**零 LLM 调用**：

```bash
he feed ./ka/ doc2.md --source doc-2
# Source 'doc-2' is unchanged (content hash matches) — nothing to do.
# Use --refeed to re-ingest anyway.
```

```bash
# 即使哈希一致也强制重新摄取
he feed ./ka/ doc2.md --source doc-2 --refeed
```

---

## 查看来源台账

```bash
he info ./ka/ --sources
```

**输出：**
```
                        Source Ledger
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Source ID  ┃ Raw Items ┃ Content Hash                       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ doc-1      │        12 │ 9f86d081884c7d659a2febb0c0413a6e…  │
│ doc-2      │         8 │ 2c26b44babbfb4c6a5cc6b3f2a4b2f1d…  │
└────────────┴───────────┴────────────────────────────────────┘
```

在 Python 中：

```python
ka.sources()
# {
#     "doc-1": {"raw_items": 12, "content_hash": "9f86d0…"},
#     "doc-2": {"raw_items": 8, "content_hash": "2c26b4…"},
# }
```

---

## 回滚整个文档

删除某个文档贡献的全部知识：

```bash
he remove ./ka/ --document doc-1

# 显式指定策略
he remove ./ka/ --document doc-1 --strategy touched
```

```python
report = ka.remove_source("doc-1")                      # exact（默认）
report = ka.remove_source("doc-1", strategy="touched")

result.dump("./ka/")  # 持久化
```

策略决定与其他文档**共享**的 key 如何处理：

| 策略 | 共享 key | 独占 key |
|------|----------|----------|
| `exact`（默认） | 从幸存来源的原始结果重新合并（经典合并策略下完全确定） | 删除 |
| `touched` | 直接删除 | 删除 |

`exact` 保证其余每个文档的贡献完整保留；`touched` 保证被删文档的影响不留痕迹，代价是其他文档也支持的事实会被一并删除。使用 LLM 合并策略时，`exact` 的重新合并会保留语义、措辞近似。未知或无贡献的来源会报告 `Nothing matched` 并正常退出。无论哪种情况，已构建的搜索索引都会原地修补。

!!! note
    基于哈希的变更检测内置于 `he feed --source`。Python 调用者可以在调用 `feed_text` 前，将 `ka.source_content_hash(source_id)` 与自行计算的文本哈希比对，实现同样效果。

---

## 事实级编辑

若只需保留节点但移除其中一条错误描述，请使用事实级编辑而非整体回滚：

```python
report = ka.edit_node("Apple", remove_fact="founded by Steve Jobs", dry_run=True)
ka.edit_node("Apple", remove_fact="founded by Steve Jobs")  # 应用
```

```bash
he remove ./ka/ --edit-node Apple --fact "founded by Steve Jobs" -y
```

完整安全护栏（key 不变性、预览、备份）见 [`he remove`](../../cli/commands/remove.md)。

---

## 持久化

`ka.dump()`——以及每次 `he parse` / `he feed`——会把台账写在 `data.json` 旁边：

```
./ka/
├── data.json             # 提取的知识
├── metadata.json         # 提取元数据
├── sources_nodes.json    # 节点台账：每个来源的原始条目
├── sources_edges.json    # 边台账：每个来源的原始条目
├── sources_chunks.json   # 块台账（chunk 型知识库）：每个来源的原始块
└── documents/            # 原始文档归档，每个来源保留一份当前副本
```

- 请将台账文件与知识摘要放在一起保存（像 `data.json` 一样纳入版本控制）：每个来源的原始结果只存在于这里，删除台账文件会导致该知识摘要无法回滚、也无法做变更检测。
- `he feed --source` 会同时把原始文档归档到 `documents/`（保留原始字节，每个来源一份当前副本；用 `--no-store-doc` 关闭）。`he remove --document` 时传入 `--purge-documents` 可在回滚的同时删除归档副本。
- 每次写入前，`he remove` 会将 `data.json` 备份为 `data.json.bak.<时间戳>`（除非传入 `--no-backup`），因此回滚本身也可以撤销。

---

## 路线图

- **已落地（v0.8.0）** —— 基于内容哈希的变更检测：`he feed --source` 会在任何 LLM 调用之前计算输入哈希并跳过未变更文档。
- **已落地（v0.9.0）** —— 原始文档归档（`documents/`），以及直接检索原始文本块的 `chunk_rag` 方法（chunk 级*检索*）。
- **规划中** —— 更细粒度的溯源：把图谱型知识库中的每个节点/边映射回它被提取自的确切文本块（chunk）。注意这与 `chunk_rag` 不同——后者检索 chunk，但不做结构化。

---

## 另请参阅

- [`he feed`](../../cli/commands/feed.md) — `--source` 与 `--refeed` 参数
- [`he info`](../../cli/commands/info.md) — 查看来源台账
- [`he remove`](../../cli/commands/remove.md) — 文档级回滚与事实级编辑参考
- [增量更新](incremental-updates.md) — 喂养时的合并行为

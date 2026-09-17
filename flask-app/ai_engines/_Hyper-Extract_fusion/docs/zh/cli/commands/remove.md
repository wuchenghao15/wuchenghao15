# he remove

从已有知识摘要中删除知识：按键硬删除节点/边，或借助大模型软删除单条事实。

---

## 用法

```bash
he remove KA_PATH [选项]
```

## 选项

| 选项 | 默认值 | 说明 |
|--------|---------|-------------|
| `--node TEXT` | — | **硬删除**指定节点；以被删节点为端点的边会一并删除 |
| `--edge TEXT` | — | **硬删除**指定边 |
| `--edit-node TEXT` | — | **软编辑**指定节点（大模型重写，移除 `--fact`） |
| `--edit-edge TEXT` | — | **软编辑**指定边 |
| `--document TEXT` | — | **回滚**某个来源文档贡献的全部知识（要求 KA 在摄取时使用了 `--source`） |
| `--strategy` | `exact` | `--document` 的回滚策略：`exact` 或 `touched` |
| `--fact TEXT` | — | 要从 `--edit-node` / `--edit-edge` 条目中移除的事实 |
| `--instruction TEXT` | — | 自由格式的编辑指令（替代 `--fact`） |
| `--dry-run` | 关闭 | 仅预览变更，不落盘 |
| `--backup / --no-backup` | 开启 | 写入前将 `data.json` 备份为 `data.json.bak.<时间戳>` |
| `--yes` | `-y` | 跳过确认提示 |

硬删除（`--node` / `--edge`）与软删除（`--edit-node` / `--edit-edge`）互斥。

---

## 硬删除：按键删除

删除整个条目。key 由模板的 `identifiers` 生成（节点通常为实体名，边通常为 `"{source}|{type}|{target}"` 风格）。可用 [`he show`](show.md) 或直接查看 `data.json` 找到它们。

```bash
# 删除两个节点；以它们为端点的边会被一并删除
he remove ./ka/ --node Apple --node Nokia

# 按精确 key 删除一条边
he remove ./ka/ --edge "Apple-partner-Google"
```

命令会输出删除报告（已删除项、未命中的 key、被清理的孤儿边）。

!!! warning
    对被删除的条目而言，硬删除是**永久的**。除非传入 `--no-backup`，否则写入前会在 KA 目录旁生成 `data.json.bak.<时间戳>` 备份。

---

## 软删除：移除单条事实（大模型辅助）

有时节点需要保留，但其中的某条描述是错误的或已过时：

```bash
# 先预览（不落盘）
he remove ./ka/ --edit-node Apple \
  --fact "founded by Steve Jobs" --dry-run

# 应用
he remove ./ka/ --edit-node Apple \
  --fact "founded by Steve Jobs" -y
```

大模型会在**相同 schema** 下重写该条目，只移除目标事实，其余字段保持不变。安全护栏：

- **key 不变性** — 重写若改变了条目的 key 会被拒绝（改名不属于编辑；应显式删除旧条目再添加新条目）。
- **预览** — `--dry-run` 打印旧条目与拟定条目，不写入任何内容。
- **无变化检测** — 若未找到目标事实，命令报告 `No change` 且不写入。
- **备份** — 除非传入 `--no-backup`，编辑前会生成 `data.json.bak.<时间戳>`。

对边进行软编辑时请注意：构成边 key 的字段（如 `relation_type`）无法通过软编辑修改——重写会被拒绝；此时请改用硬删除。

```bash
he remove ./ka/ --edit-edge "Apple-acquired-Beats" \
  --instruction "Remove the price from the description"
```

---

## 删除之后

如果知识摘要已有搜索索引，`he remove` 会**原地修补索引**——只删除/重嵌受影响的向量，之后**无需**再执行 `he build-index`，搜索立即可用。

如果此前没有构建过索引（或原地修补不可用），过期的磁盘索引会被删除；再次搜索或对话前请先重建：

```bash
he build-index ./ka/
```

---

## 文档级回滚：删除整个来源文档的贡献

当文档以来源标注方式摄取后，可以整体回滚其贡献：

```bash
# 带来源标注摄取
he feed ./ka/ doc1.md --source doc-1
he feed ./ka/ doc2.md --source doc-2

# 之后：回滚 doc-1 贡献的全部知识（共享 key 会通过 doc-2 保留）
he remove ./ka/ --document doc-1

# 或删除该文档触及的所有 key，即使其他文档也共享这些 key
he remove ./ka/ --document doc-1 --strategy touched
```

## 回滚策略（`--strategy`）

| 策略 | 行为 |
|------|------|
| `exact`（默认） | 仅由被删文档贡献的 key 会被删除；与其他文档**共享**的 key 会从幸存来源的原始结果重新合并——经典合并策略下完全确定（LLM 策略保留语义、措辞近似） |
| `touched` | 该文档触及的每个 key 都会直接删除，包括其他文档也贡献过的 key |

要求 KA 的记忆开启来源追踪（图谱类 KA 默认开启）。若该文档没有已记录的贡献，命令会报告 `Nothing matched` 并正常退出。

---

## Python API

```python
ka.remove_nodes("Apple", "Nokia")   # -> {"removed_nodes": [...], "not_found_nodes": [...], "removed_orphan_edges": [...]}
ka.remove_edges("Apple-partner-Google")

report = ka.edit_node("Apple", remove_fact="founded by Steve Jobs", dry_run=True)
# report: {"changed": bool, "applied": bool, "old": <item>, "new": <item>}
ka.edit_node("Apple", remove_fact="founded by Steve Jobs")  # 应用

ka.dump("./ka/")  # 持久化
```

适用于 graph、hypergraph 以及时序/空间图谱知识摘要。

---

## 另请参阅

- [`he clean`](clean.md) — 删除搜索索引或整个 KA
- [`he show`](show.md) — 删除前查看 key
- [`he build-index`](build-index.md) — 删除后重建搜索索引

## 另请参阅

- [`he feed --source`](feed.md) — 来源标注摄取（生命周期的另一半）
- [`he tag`](tag.md) — 为来源打标签以启用范围检索
- [管理文档的生命周期](managing-documents.md) — 完整生命周期指南

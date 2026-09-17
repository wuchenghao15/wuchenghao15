# 选择方法：基线 vs 结构化抽取

什么时候值得为图谱抽取多付钱，什么时候只用原文 chunks 就够？

本页是决策说明，不是评测框架。它不定义召回指标、QA 对，也不给出 CI 分数。同一语料上的答案、延迟和 token 用量，等 `examples/en/methods/chunk_vs_graph_rag.py` 落地后，用 `examples/en/tesla.md` 跑那个脚本即可。那是手工演示，CI 不会跑它。

算法目录见 [方法](methods.md)。调用方式见 [使用方法](../python/guides/using-methods.md)。

---

## 两个默认选项

| 需求 | 先用 | 原因 |
|------|------|------|
| 查找、引用原文、定位段落 | `chunk_rag` | 摄入只做分块和嵌入，没有 LLM 抽取成本。检索直接返回原文 chunk。 |
| 多跳或关系密集的问题 | `graph_rag` | 抽取会建节点和边，答案可以顺着关系走，而不只靠字面重叠。 |

`chunk_rag` 就是零抽取基线。先用它；只有当额外的摄入成本能改变你关心的答案时，再为 `graph_rag`（或其他结构化方法）付钱。

---

## 什么时候 chunks 就够

优先 `chunk_rag` 当：

- 问题是 **lookup 式**：「哪一年……？」「引用那一条款……」「文档哪里写了……？」
- 你需要 **原文措辞**，而不是合成后的图谱事实。
- 语料很大，**摄入阶段的 LLM 成本** 是瓶颈。
- 你还在判断抽取值不值 —— 这就是基线。

摄入：分块 → 嵌入 → 建索引。查询：检索 chunks →（可选）基于这些 chunks 做 chat。

---

## 什么时候图谱抽取划算

优先 `graph_rag`（或其他图谱 / 超图方法）当：

- 问题是 **多跳**：「收购了 X 的那家公司，出资人是谁？」
- 问题是 **关系密集**：对手、继任、股权、因果。
- 你会 **复用这张图**（导出、范围检索、可视化），而不是只问一次。

摄入时要用 LLM 抽结构。如果每个问题都能靠指到一段原文回答，这笔钱就浪费了。

---

## 同一语料、同一套 provenance

`chunk_rag` 和 `graph_rag` 共用 provenance：来源台账、`he tag`、范围限定的 `he search` / `he talk`、按文档回滚。在同一份语料（`examples/en/tesla.md`）上对比是 apples-to-apples —— 差别在抽取，不在打标或回滚。

见[来源标注与溯源](../python/guides/provenance.md)。

---

## 这不是评测框架

本页不定义命中率、期望 span，也不提供基准集。CI 里的 hash embedding 会让 recall 数字没有意义。任何 harness 都应另开 RFC —— 这里不做。

---

## 另请参见

- [方法](methods.md) — 算法目录与对照表
- [使用方法](../python/guides/using-methods.md) — `Template.create("method/…")`
- [搜索和聊天](../python/guides/search-and-chat.md) — 选定方法后的 `search` / `chat`

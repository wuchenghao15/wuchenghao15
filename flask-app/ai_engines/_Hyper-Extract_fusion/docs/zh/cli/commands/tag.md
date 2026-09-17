# he tag

管理知识库来源文档的标签 —— 组织来源，用于范围搜索和回滚。

---

## 概要

```bash
he tag KA_PATH --source SOURCE_ID [--add TAG ...] [--remove TAG ...]
he tag KA_PATH --list
he tag KA_PATH --source SOURCE_ID          # 查看当前标签
```

## 参数

| 参数 | 描述 |
|----------|-------------|
| `KA_PATH` | 知识库目录的路径 |

## 选项

| 选项 | 简写 | 默认值 | 描述 |
|--------|-------|---------|-------------|
| `--source TEXT` | — | **必填** | 要打标签的来源文档 id |
| `--add TEXT` | — | — | 要添加的标签（可重复） |
| `--remove TEXT` | — | — | 要移除的标签（可重复） |
| `--list` | `-l` | off | 列出所有来源及其标签 |

---

## 描述

`he tag` 为知识库内的来源文档附加自由格式的标签：

- **持久化** — 标签保存在**来源台账**（`sources_nodes.json` / `sources_edges.json`）中，与 [`he feed --source`](feed.md) 记录来源标注使用的是同一组文件，因此标签随知识库一起在 `he dump` / `he load` 之间持久保存。
- **范围检索** — 标签允许你将 [`he search`](search.md) 限定为带有指定标签的来源所贡献的知识（见下方「范围搜索」章节）。
- **可用范围** — 适用于图谱族知识库，即来源台账会追踪来源的知识库（见[来源标注与溯源](../../python/guides/provenance.md)）。

---

## 示例

### 为来源添加标签

```bash
he tag ./ka/ --source contract-2024 --add legal --add reviewed
# → Tagged! contract-2024: legal, reviewed
```

## 移除来源的标签

```bash
he tag ./ka/ --source contract-2024 --remove reviewed
```

### 查看来源的当前标签

```bash
he tag ./ka/ --source contract-2024
# → contract-2024 tags: legal
```

## 列出所有来源及其标签

```bash
he tag ./ka/ --list
```

输出来源台账表格：来源 id、原始条目数和标签。

---

## 范围搜索

标签与 [`he search`](search.md) 的 `--tag` 选项配合使用：

```bash
# 只搜索带有 `legal` 标签的来源所贡献的知识
he search ./ka/ "终止条件" --tag legal
```

范围限定要求来源在摄入时带有标注（`he feed ./ka/ doc.md --source contract-2024`），这样台账才会存在。

---

## 另请参见

- [`he remove`](remove.md) — 文档级回滚（`--document`），使用同一份来源台账
- [来源标注与溯源](../../python/guides/provenance.md) — 来源标注、来源台账与变更检测

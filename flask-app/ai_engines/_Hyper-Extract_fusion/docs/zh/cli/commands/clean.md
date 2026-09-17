# he clean

清理知识摘要——删除其搜索索引，或使用 `--all` 删除整个 KA。

---

## 用法

```bash
he clean KA_PATH [选项]
```

## 参数

| 参数 | 说明 |
|----------|-------------|
| `KA_PATH` | 知识摘要目录路径 |

## 选项

| 选项 | 别名 | 默认值 | 说明 |
|--------|-------|---------|-------------|
| `--all` | `-a` | 关闭 | 删除**整个** KA 目录（数据、元数据和索引） |
| `--yes` | `-y` | 关闭 | 跳过确认提示 |

---

## 说明

`he clean` 删除知识摘要的一部分：

- **默认** — 仅删除向量索引（`index/` 子目录）。提取的数据（`data.json`）和元数据会保留；之后可用 [`he build-index`](build-index.md) 重新构建。
- **`--all`** — 删除整个 KA 目录。

删除是**不可恢复**的。命令会先要求确认；使用 `--yes` 可跳过提示（例如脚本中）。

为安全起见，`he clean` 只对真正的知识摘要（包含 `data.json` 的目录）生效。它拒绝删除任意目录，因此输错路径不会误删无关文件。

---

## 示例

### 清理索引（保留数据）

```bash
he clean ./tesla_kb/
# → 确认后删除 ./tesla_kb/index/
```

## 删除整个知识摘要

```bash
he clean ./tesla_kb/ --all
```

### 非交互（脚本 / CI）

```bash
he clean ./tesla_kb/ --all --yes
```

---

## 删除内容

| 模式 | 删除 | 保留 |
|------|---------|------|
| 默认 | `index/` | `data.json`、`metadata.json` |
| `--all` | 整个 `KA_PATH` 目录 | — |

> 由 [`he export obsidian`](export.md) 生成的 Obsidian 知识库是独立文件夹，**不会**被 `he clean` 影响。请用 shell 删除（`rm -rf ./vault/`）。

---

## 另请参阅

- [`he build-index`](build-index.md) — 清理索引后重新构建
- [`he info`](info.md) — 清理前查看知识摘要
- [`he parse`](parse.md) — 重新创建知识摘要

# 新闻动态

版本发布与功能亮点。完整变更日志见 [GitHub Releases](https://github.com/yifanfeng97/hyper-extract/releases)。

---

## v0.10.2 — 范围对话、方法选型指南与持久化修复

- **💬 范围对话** — `he talk --source/--tag`（及 `ka.chat`）可将上下文限定在已标注/打标签的文档内，对不支持的类型自动能力探测。*(#161, #160)*
- **📖 方法选型** — 新增"基线 vs 结构化"选型指南，以及同语料 `chunk_rag` vs `graph_rag` 的并排对比示例（含成本/延迟）。*(#162, #163 —— #117 的前两步)*
- **🏗️ 内部改进** — `GraphIndexMixin` 抽取 graph/hypergraph 共享的合并/索引/检索面（净删 168 行）。*(#145)*
- **🐛 修复** — 时空图谱 observation 上下文现在能跨 dump/load 保留（此前静默丢失）；MCP 加载失败以工具结果返回，不再炸掉 stdio 会话；`he config init` 不再为纯 LLM provider 写入同源坏嵌入器；`Cog_RAG.chat` 透传 `source_ids`/`tags`；`he list --lang zh` 保留方法模板；document 模板增加输出结构校验；CLI banner 列出 jsonld/cypher。*(#167, #169, #165, #171, #159, #173, #155)*
- **📚 文档** — 解决 MCP 文档残留冲突标记；JSON-LD/Cypher 章节排版修复；索引布局说明按类型区分；Gemini provider 指南。*(#149, #151, #153, #157)*

---

## v0.10.1 — 索引存储脱离 pickle

- **🔒 安全的索引格式** — `AutoModel`/`AutoList` 的索引改为 JSON 存储（`index.json`：向量 + 文档），加载时在内存中重建——**没有 pickle，不执行任何代码**。旧 pickle 索引（<= v0.10.0）仍可加载但会给出警告；`he build-index --force` 即可迁移。*(#116)*

---

## v0.10.0 — 更多导出格式、Gemini 与质量加固

- **📤 JSON-LD 与 Cypher 导出** — `he export jsonld`（二元边 + GraphML 风格超边）与 `he export cypher`（Neo4j 兼容 MERGE 脚本；N 元边编码为 Hyperedge 节点，不做有损团 expansion）。*(#139, #141)*
- **🔌 MCP 导出对齐** — `he-mcp` 新增 `export_graphml`、`export_csv`、`export_jsonld`、`export_cypher` 工具；MCP `list_templates` 包含方法模板、`info` 与 CLI 一样展示 chunks/时间戳/来源。*(#106, #131, #133, #144)*
- **📄 `he feed` 支持目录** — 与 `he parse` 对齐：逐文件来源标注、相同的跳过/警告行为。*(#135)*
- **🧠 原生 Gemini 支持** — 此前未接线的 `[google]` extra 已接入 `create_llm`：`pip install "hyperextract[google]"`。*(#137)*
- **🏗️ 内部改进** — `GraphIndexMixin` 抽取 graph/hypergraph 共享的合并/索引/检索面（净删 168 行）；全部注册方法的契约测试；测试矩阵加入 Windows。*(#112, #108, #145)*
- **🛡️ 加固** — chunk 参数解析期校验（`chunk_overlap < chunk_size`）；`relation_members` 必须含 `source`/`target` 角色；Windows `config.toml` ACL 收紧到当前用户；FAISS 反序列化警告。*(#91, #92, #110, #94)*
- **🐛 修复** — 超图范围检索透传；`he search` 打印节点/边而非原始元组；MCP `search` 不再因三元组崩溃；GraphML 导出尊重 `--force`。*(#90, #144)*

---

## v0.9.1 — 范围检索补全与校验器加固

- **🐛 修复** — 超图 `search` 透传 scope（此前丢弃 `source_ids`/`tags`）；AutoSet 溯源端到端接通（记录/标签/回滚/持久化）；`Graph_RAG`/`Cog_RAG` scope 转发；无账本类型上范围检索给出明确报错。

---

## v0.9.0 — 丰富的文档输入与 chunk_rag 基线

- **📄 丰富的文档输入** — `he parse` / `he feed` 现在支持 PDF、Word、PowerPoint、Excel、HTML、CSV/JSON/XML、EPUB 等格式，安装可选依赖即可启用（`pip install "hyperextract[ingest]"`，由 [MarkItDown](https://github.com/microsoft/markitdown) 驱动）。非 UTF-8 文本（GBK 等）自动识别编码；无文字层的扫描版 PDF 会给出明确的 OCR 提示，而不是静默摄入乱码。
- **🧱 `chunk_rag` 基线方法** — 全新的零提取方法：文档直接分块并向量化，检索返回原始文本块。摄入零 LLM 成本，且具备完整溯源能力（标签、范围检索、按文档回滚）。语料问答与方法对比的块检索基线。
- **🐛 修复** — `he tag` 在所有知识库上都会崩溃（`tag_source` 此前从未在任何类型上实现）；`he search`/`he talk`/`he feed`/`he remove --document` 在方法型知识库上会崩溃（`method/*` 模板无法从元数据解析）。

---

## v0.8.1 / v0.8.2

- **🏷️ 来源标签与范围检索** — `he tag ./ka/ --source doc-1 --add legal`，然后 `he search ./ka/ "query" --tag legal` 即可只在已标注文档范围内检索。适用于 graph、hypergraph 和 set。*(#89, #84)*
- **🛡️ 输入类型校验** — `he parse` / `he feed` 现在会拒绝不支持的文件类型并给出转换提示，而不是静默摄入乱码。*(#88)*
- **📦 文档存档修复** — 同一来源换文件名重喂不再积累陈旧副本。*(#89)*

---

## v0.8.0

- **🔄 文档级 Upsert** — 对已标注的文档重新喂入时，旧版本贡献自动回滚：删除的事实消失，共享键从幸存来源重新合并。*(#84)*
- **📁 逐文件来源标注** — `he parse ./docs/` 自动按文件名标注来源；之后可回滚或审计任意单个文件。显式 `--source` 仍然优先。
- **⏱️ 时空溯源** — 时间/空间/时空图谱完整支持来源标注与回滚，并通过确定性的（MERGE_FIELD）回放测试。

---

## v0.5.0 – v0.7.0

- **🗑️ 两级知识删除** — 按键硬删（`he remove --node/--edge`，孤立边自动修剪），或通过 LLM 辅助编辑删除单条错误事实（`he remove --edit-node --fact`），支持 dry-run、键不变性检查与自动备份。*(#84)*
- **📜 来源标注与溯源** — `he feed --source` / `he parse --source` 记录每个文档的原始贡献；`he remove --document` 精确回滚单个文档的贡献；`he info --sources` 展示来源账本。*(#84)*
- **📈 全面增量** — feed/parse/删除/编辑均原地修补向量索引（仅重嵌入受影响的向量）；内容哈希未变的文档自动跳过（`--refeed` 强制）。*(#84)*
- **🧪 `he template validate`** — 在为 LLM 调用付费之前发现模板语义错误：9 条诊断规则、`--json` 输出接入 CI、`--all` 扫描目录。*(#77)*
- **📊 GraphML 与 CSV 导出** — 对接桌面图工具与表格软件；超图导出超边表。*(#85)*
- **🌐 OrcaRouter Provider** — 一个 key 接入 150+ 模型（`create_client("orcarouter")`）。*(#71)*
- **🔐 配置文件权限** — `~/.he/config.toml` 以 `0600` 权限保存。*(#86)*
- **🔗 Obsidian 双链修复** — 别名不再因 `[ ] | # ^` 等字符出错。*(#87)*
- **🛡️ Chunk 级故障隔离** — 单个 chunk 失败不再丢弃整个多 chunk 提取结果。*(#78)*
- **⚡ MCP Python SDK 2.x** — `he-mcp` 同时兼容 mcp 1.x 与 2.x。*(#72, #82)*
- **🔀 有向边修复** — 保留 `(source, target)` 顺序；支持自定义端点字段名。*(#74)*
- **🔑 DeepSeek API Key 修复** — OpenAI 兼容路径下正确识别 `DEEPSEEK_API_KEY`。*(#76)*
- **🎓 教育领域模板** — `course_concept_graph` + `curriculum_structure`。*(#80)*
- **🧭 其他修复** — Graph_RAG.search 三元组；`he talk -i --top-k`；引导与文档整体翻新。*(#70, #73, #57)*

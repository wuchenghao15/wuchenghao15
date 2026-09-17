# Hyper-Extract Skills

Hyper-Extract 的知识模板设计技能。

## 技能概述

| 技能 | 用途 |
|------|------|
| Root | 模板设计的入口点 |
| brainstorm | 需求探索和类型讨论 |
| record-designer | 设计 model/list/set 结构 |
| graph-designer | 设计 graph/hypergraph/etc 结构 |
| yaml-validator | 验证 YAML 配置 |
| multilingual | 转换为多语言支持 |
| template-optimizer | 优化模板并修复常见问题 |

## 安装

### Claude Code

将 `hyperextract-skills` 文件夹复制到您的 Claude Code 技能目录：

```bash
cp -r hyperextract-skills ~/.claude/skills/
```

或使用插件命令：

```bash
/plugin install hyperextract-skills
```

### Trae

将 `hyperextract-skills` 文件夹复制到您的 Trae 技能目录：

```bash
cp -r hyperextract-skills ~/.trae/skills/
```

## 使用

### 快速开始

1. 从 brainstorm 技能开始探索您的需求
2. 根据推荐的类型，使用 record-designer 或 graph-designer
3. **使用 template-optimizer 优化**（推荐）
4. 可选择使用 yaml-validator 验证
5. 可选择转换为多语言

### 示例工作流

```
您：我想从财务报告中提取关键信息

Assistant（使用 brainstorm）：
让我们探索您的需求...

您：我需要从财报电话会议中提取公司名称、营收和季度

Assistant（使用 brainstorm）：
根据您的描述，我推荐：model 类型

Assistant（使用 record-designer）：
让我们为您的 model 设计字段...
```

## 支持的类型

### 记录类型
- **model**：单个结构化对象
- **list**：同类对象列表
- **set**：去重对象集合

### 图谱类型
- **graph**：二元关系图谱
- **hypergraph**：多实体关系超图
- **temporal_graph**：带时间维度的时序图谱
- **spatial_graph**：带位置维度的空间图谱
- **spatio_temporal_graph**：时空结合的图谱

## 目录结构

```
hyperextract-skills/
├── SKILL.md                    # 根技能
├── brainstorm/
│   └── SKILL.md               # 需求探索
├── record-designer/
│   ├── SKILL.md               # 记录类型设计
│   ├── cases/                 # 示例模板（YAML）
│   │   ├── earnings-summary.yaml
│   │   ├── product-features.yaml
│   │   └── entity-registry.yaml
│   └── references/            # 设计模式
│       ├── field.md
│       └── identifier.md
├── graph-designer/
│   ├── SKILL.md               # 图谱类型设计
│   ├── cases/                 # 示例模板（YAML）
│   │   ├── corporate-ownership.yaml
│   │   ├── battle-analysis.yaml
│   │   └── meeting-records.yaml
│   └── references/            # 设计模式
│       ├── entity.md
│       ├── relation.md
│       ├── hypergraph.md
│       └── dimensions.md
├── yaml-validator/
│   ├── SKILL.md               # YAML 验证
│   └── references/            # 验证规则
│       ├── rules-syntax.md
│       ├── rules-types.md
│       ├── rules-identifiers.md
│       └── rules-errors.md
├── multilingual/
│   └── SKILL.md               # 多语言转换
└── template-optimizer/
    ├── SKILL.md               # 模板优化
    └── references/            # 优化规则
        ├── rules-naming.md
        ├── rules-multilingual.md
        ├── rules-field-count.md
        └── rules-consistency.md
```

## 设计原则

设计模板时，请记住：**Schema 定义 WHAT，Guideline 定义 HOW TO DO WELL**。
详情参见 `graph-designer/SKILL.md` 或 `record-designer/SKILL.md`。

## 许可证

Apache 2.0

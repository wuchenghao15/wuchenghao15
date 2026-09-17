---
name: hyper-extract
description: |
  Hyper-Extract Knowledge Template Designer for structured knowledge extraction.
  Use when user wants to: design YAML templates, extract structured knowledge, create knowledge graphs.
  Available skills: brainstorm, record-designer, graph-designer, yaml-validator, multilingual.
  Trigger: User mentions template design, extraction, knowledge graph, or YAML configuration.
---

# Hyper-Extract

## Overview

Hyper-Extract helps users design YAML configuration templates for structured knowledge extraction.

## Workflow

```
User → brainstorm → designer → validator → multilingual
```

## Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| brainstorm | Explore requirements, determine types | First step, when unsure |
| record-designer | Design model/list/set structures | For Record types |
| graph-designer | Design graph/hypergraph structures | For Graph types |
| yaml-validator | Validate YAML correctness | Optional, after design |
| multilingual | Multi-language support | Optional |

---

## Skill Workflow

### Step 1: brainstorm
Discuss requirements, determine type, create design draft.

### Step 2: designer
Generate YAML based on design draft:
- record-designer → model/list/set
- graph-designer → graph/hypergraph/temporal/spatial

### Step 3: validator (optional)
Validate YAML syntax and structure.

### Step 4: multilingual (optional)
Add multi-language support.

---

## Supported Types

| Type | Description |
|------|-------------|
| model | Single structured object |
| list | Ordered list of items |
| set | Deduplicated set |
| graph | Binary relations (A→B) |
| hypergraph | Multi-entity relations |
| temporal_graph | + time dimension |
| spatial_graph | + space dimension |
| spatio_temporal_graph | + time + space |

---

## Hypergraph Grouping

| Type | relation_members | Use Case |
|------|-----------------|----------|
| Simple | `participants` (string) | Flat list |
| Nested | `[group_a, group_b]` (list) | Semantic roles |

---

## Skill Calling Conventions

### brainstorm → designer

Pass design draft:
```markdown
## Type: hypergraph
## Groups: [attackers, defenders]
## Fields: [battle_name, outcome]
```

### designer → validator (optional)

```markdown
## Generated YAML
[yaml content]
```

---

## Type Determination Quick Reference

```
Need relationships?
├─ No → model / list / set
└─ Yes → graph / hypergraph
    ├─ Binary → graph
    └─ Multi-entity → hypergraph

+ time → temporal_graph
+ space → spatial_graph
+ both → spatio_temporal_graph
```

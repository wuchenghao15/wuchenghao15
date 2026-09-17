---
name: template-optimizer
description: |
  Optimize YAML templates for Hyper-Extract.
  Use when: "optimize template", "fix YAML issues", "improve quality", "lint template"
  Trigger: After creating templates or during review
  Skip: Creating new templates (use brainstorm + designer instead)
---

# Template Optimizer

Automatically analyze and optimize YAML templates by applying best practices and fixing common issues.

## Workflow

```
1. Parse YAML → 2. Analyze Issues → 3. Apply Fixes → 4. Generate Report
```

### Step 1: Parse YAML

Load the YAML template and validate basic structure.

### Step 2: Analyze Issues

Check against these rules:

| Rule | What to Check |
|------|--------------|
| [rules-naming.md](references/rules-naming.md) | Field naming standardization |
| [rules-multilingual.md](references/rules-multilingual.md) | Language consistency |
| [rules-field-count.md](references/rules-field-count.md) | Information density |
| [rules-consistency.md](references/rules-consistency.md) | Schema vs Guideline separation |
| [rules-hypergraph-grouping.md](references/rules-hypergraph-grouping.md) | Hypergraph grouping strategy |

### Step 3: Apply Fixes

Apply fixes based on optimization level:

| Level | Description | Example |
|-------|-------------|---------|
| **Auto-fix** | Safe changes that always improve | `relation_type` → `type` |
| **Suggest** | Changes that may need review | Field count > 5 |
| **Review** | Design decisions | Relation type openness |

### Step 4: Generate Report

Output changes with explanations for learning.

---

## Detection Rules

### Rule 1: Multi-language Consistency

```
❌ Pattern: [a-zA-Z]+\([^)]+\) in zh fields
❌ Pattern: Chinese chars in en fields
```

**Fix**: Separate language content, use pure Chinese in zh, pure English in en.

### Rule 2: Field Naming

```
❌ relation_type → type
❌ event_date → time
❌ entity_type → type
```

**Fix**: Standardize to concise names.

### Rule 3: Field Count

```
⚠️ entities.fields > 5 → Flag for review
⚠️ relations.fields > 5 → Flag for review
```

**Fix**: Simplify to essential fields, use priority: Essential → Important → Optional.

### Rule 4: Schema-Guideline Separation

```
❌ Repetition of field definitions in guideline
❌ Schema descriptions in rules
```

**Fix**: Schema defines WHAT, Guideline defines HOW TO DO WELL.

### Rule 5: Hypergraph Grouping

```
❌ relation_members: participants (string) + role field exists
❌ relation_id contains participant field
```

**Fix**: Use nested grouping `relation_members: [group_a, group_b]` when entities partition by roles.

---

## Design Principles

### Schema vs Guideline

| Schema Defines | Guideline Defines |
|---------------|-----------------|
| Field names | Extraction strategy |
| Field types | Quality requirements |
| Field descriptions | Creation conditions |
| Required/optional | Common mistakes |

**❌ Wrong**: Guideline repeats schema definitions
**✅ Correct**: Guideline explains how to extract well

### Information Density

For **entities** and **relations**:

| Field Priority | Examples |
|---------------|---------|
| Essential | source, target, participants |
| Important | type, time, location |
| Optional | description, metadata |

**Max**: 5 fields per component

### Naming Conventions

| For | Use | Example |
|-----|------|---------|
| Template name | CamelCase | `EarningsSummary` |
| Field names | snake_case | `company_name` |
| Tags | lowercase | `finance, investor` |

---

## Reference Files

| Topic | When to Check |
|-------|--------------|
| [rules-naming.md](references/rules-naming.md) | Field naming issues |
| [rules-multilingual.md](references/rules-multilingual.md) | Language consistency |
| [rules-field-count.md](references/rules-field-count.md) | Too many fields |
| [rules-consistency.md](references/rules-consistency.md) | Schema-guideline overlap |
| [rules-hypergraph-grouping.md](references/rules-hypergraph-grouping.md) | Role field vs nested grouping |

---

## Output Format

```markdown
# Optimization Report

## Changes Made

| File | Issue | Fix | Level |
|------|-------|-----|-------|
| template.yaml | `relation_type` | renamed to `type` | Auto-fix |
| template.yaml | Mixed language | Fixed zh/en separation | Auto-fix |
| template.yaml | 7 relation fields | Suggested simplification | Suggest |

## Summary

- Auto-fix: 2
- Suggestions: 1
- Manual review: 0
```

---

## Integration

```
Full workflow: brainstorm → designer → optimizer → validator
                           ↓
                    Apply best practices
                    Auto-fix common issues
```

**When to use**:
- After creating new templates
- Before validator
- During template review
- Batch optimization of existing templates

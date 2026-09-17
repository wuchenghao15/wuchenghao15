---
name: record-designer
description: |
  Design YAML extraction templates for record types (model, list, set).
  Use when user says: "design model template", "create item list extraction", "extract items", "deduplicate entities".
  Trigger: User wants to extract structured records, lists, or deduplicated entities.
  Skip: User mentions graph, relations, or knowledge graph (use graph-designer instead).
---

# Record Designer: model/list/set

## Input from Brainstorm

Receive design specs from brainstorm:
- What fields to extract
- Field types and requirements
- Deduplication needs (for set)

## Workflow

1. **Confirm type** (model/list/set)
2. **Design fields** (output.fields)
3. **Configure identifiers** (identifiers.item_id for set)
4. **Set display** (display.label)
5. **Write guideline** (guideline)
6. **Review and output YAML**

## Critical: Output vs Guideline

**Key Principle**: Schema defines "WHAT", Guideline defines "HOW TO DO WELL". DO NOT repeat schema definitions in guideline.

| Guideline Should Have | Guideline Should NOT Have |
|-----------------------|-------------------------|
| Extraction strategy ("extract key information for...") | Field definitions ("field_a is for...") |
| Quality requirements ("maintain format consistency") | Type descriptions ("type field should be...") |
| Deduplication rules (for set type) | Required/optional clarifications |
| Common mistakes to avoid | Default value explanations |

## Type Confirmation

| Type | Identifiers | Use Case |
|------|-------------|----------|
| model | Not needed | Single object |
| list | Not needed | List of items |
| set | `item_id` required | Deduplicated entities |

## Output Template

```yaml
language: en

name: [TemplateName]
type: [model/list/set]
tags: [...]
description: '...'

output:
  description: '...'
  fields:
    - name: field_name
      type: str/int/float/list
      description: '...'
      required: true/false
      default: '...'

guideline:
  target: 'You are a [domain] expert...'
  rules: [...]

identifiers: {}  # Or item_id for set

display:
  label: '{field_name}'
```

## Type-Specific Output

### model

```yaml
type: model
identifiers: {}  # Not needed
```

### list

```yaml
type: list
identifiers: {}  # Not needed
```

### set

```yaml
type: set
identifiers:
  item_id: [deduplication field]
```

## Cases by Type

**Important**: Load only the case matching user's selected type.

| Type | Case File |
|------|-----------|
| model | [cases/earnings-summary.yaml](cases/earnings-summary.yaml) |
| list | [cases/product-features.yaml](cases/product-features.yaml) |
| set | [cases/entity-registry.yaml](cases/entity-registry.yaml) |

## Reference Files

**Important**: Check these files only when needed for the specific design task.

| Topic | When to Check |
|-------|--------------|
| [references/field.md](references/field.md) | When designing output.fields |
| [references/identifier.md](references/identifier.md) | For set type only |

## Design Checklist

- [ ] All fields have clear semantic meaning?
- [ ] Field types are appropriate (str/int/float/list)?
- [ ] Required vs optional is reasonable?
- [ ] Default values are safe/meaningful?
- [ ] For set: item_id can uniquely identify records?
- [ ] Display label references correct fields?

### Guideline (Must Check)
- [ ] No field definitions repeated from schema?
- [ ] Extraction strategy defined?
- [ ] Quality requirements specified?
- [ ] Common mistakes warned?
- [ ] For set: deduplication rules clear?

### Multi-language
- [ ] `zh` descriptions use pure Chinese
- [ ] `en` descriptions use pure English

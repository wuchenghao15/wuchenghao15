# Syntax Validation Rules

Syntax validation for YAML configurations. See [SKILL.md](SKILL.md) for workflow.

---

## Required Fields

All configurations must have:

```yaml
- [ ] language: zh/en
- [ ] name: PascalCase
- [ ] type: valid AutoType
- [ ] tags: lowercase array
- [ ] description: non-empty string
- [ ] output: exists
- [ ] guideline: exists
```

---

## Naming Conventions

| Field | Convention | Example |
|-------|-----------|---------|
| name | PascalCase | `EarningsCallSummary` |
| tags | lowercase array | `[finance, earnings]` |
| field names | snake_case | `company_name` |

---

## Valid AutoType Values

```
model, list, set, graph, hypergraph,
temporal_graph, spatial_graph, spatio_temporal_graph
```

Common errors:
- Typo: `"graphh"` → should be `"graph"`
- Non-standard: `"binary_graph"` → not valid

---

## YAML Structure

### Required Structure

```yaml
language: en
name: TemplateName
type: [type]
tags: [...]
description: '...'
output: {...}
guideline: {...}
```

### Optional Structure

```yaml
identifiers: {...}
display: {...}
options: {...}
```

---

## Common Syntax Errors

1. **Invalid YAML**: Missing colon, incorrect indentation
2. **Missing quotes**: Special characters in strings
3. **Type errors**: Wrong type for field value
4. **Missing required fields**: Required fields not present

---

## Validation Tips

1. Check YAML is valid first
2. Verify all required fields present
3. Check naming conventions
4. Validate field value types

---

## Multi-language Consistency

| Field | Rule | ❌ Wrong | ✅ Correct |
|-------|------|----------|------------|
| `zh` | Pure Chinese | `类型：entity(实体)` | `类型：实体/抽象` |
| `en` | Pure English | `Type: 实体` | `Type: entity/abstract` |

Detection pattern: `[a-zA-Z]+\([^)]+\)` in `zh` fields.

---
name: yaml-validator
description: |
  Validate Hyper-Extract YAML templates for syntax and structure errors.
  Use when user says: "validate template", "check YAML", "fix errors", "validate syntax".
  Trigger: User wants to verify their YAML configuration is correct.
  Skip: User wants to design a new template (use record-designer or graph-designer instead).
---

# YAML Validator

## Validation Workflow

1. **Syntax check**: YAML is valid
2. **Required fields**: All required fields present
3. **Type check**: Valid AutoType value
4. **Identifiers check**: Proper configuration for type
5. **Field validation**: Types and descriptions present

## Quick Validation Checklist

### All Types

```yaml
- [ ] language: zh/en
- [ ] name: PascalCase
- [ ] type: valid AutoType
- [ ] tags: lowercase array
- [ ] description: non-empty
- [ ] output: exists
- [ ] guideline: exists
```

### Graph Types

```yaml
- [ ] output.entities: exists
- [ ] output.relations: exists
- [ ] identifiers.entity_id: exists
- [ ] identifiers.relation_id: exists
- [ ] identifiers.relation_members: configured
```

### Hypergraph

```yaml
- [ ] relation_members is string OR list
- [ ] If list: all fields are type: list
```

### Temporal/Spatial

```yaml
- [ ] identifiers.time_field: configured (temporal)
- [ ] identifiers.location_field: configured (spatial)
```

## Validation Levels

| Level | Meaning | Action |
|-------|---------|--------|
| ERROR | Must fix | Won't work without fix |
| WARNING | Should fix | May affect quality |
| INFO | Reference | Recommended to follow |

## Reference Files

**Important**: Check these files only when needed during validation process.

| Topic | When to Check |
|-------|--------------|
| [references/rules-syntax.md](references/rules-syntax.md) | Always (first step) |
| [references/rules-types.md](references/rules-types.md) | Type-specific validation |
| [references/rules-identifiers.md](references/rules-identifiers.md) | Identifier configuration check |
| [references/rules-errors.md](references/rules-errors.md) | When errors are found |

## Validation Order

**Recommended order**: Follow this sequence for efficient validation:

1. **Syntax** → [rules-syntax.md](references/rules-syntax.md) - Check YAML validity first
2. **Structure** → [rules-types.md](references/rules-types.md) - Validate based on type
3. **Identifiers** → [rules-identifiers.md](references/rules-identifiers.md) - Check identifier config
4. **Errors** → [rules-errors.md](references/rules-errors.md) - Look up fixes if needed

## Error Message Format

```markdown
## Validation Results

### Syntax Validation
✅ PASSED

### Structure Validation
✅ PASSED
- language: ✅
- name: ✅
- type: ✅
- tags: ✅
- description: ✅
- output: ✅

### Semantic Validation
⚠️ 2 warnings
- WARNING: [message]
- WARNING: [message]

### Overall Assessment
✅ Configuration valid
```

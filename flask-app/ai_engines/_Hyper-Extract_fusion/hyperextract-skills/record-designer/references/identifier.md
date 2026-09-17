# Identifier Design Reference

Identifier configuration for record types. See [SKILL.md](SKILL.md) for workflow.

---

## When Identifiers Are Needed

| Type | Identifiers Needed | Purpose |
|------|-------------------|---------|
| model | No | Single object, no deduplication |
| list | No | Ordered items, position-based |
| set | **Yes** | Deduplication required |

---

## Set Type: Deduplication Key

### Single Field Deduplication

```yaml
identifiers:
  item_id: name  # Deduplicate based on name field
```

### Multi-Field Deduplication

```yaml
identifiers:
  item_id: '{name}|{category}'  # Deduplicate by combination
```

---

## Model/List Types

Usually not needed:

```yaml
identifiers: {}
```

Or simply omit:

```yaml
# identifiers field not present
```

---

## Label Template Syntax

```yaml
display:
  label: '{field_name}'  # How to display each record
```

Examples:
- `'{name}'` → "Company ABC"
- `'{name} - {category}'` → "Company ABC - Technology"
- `'{order}. {item}'` → "1. First item"

---

## Design Principles

1. **For Set**: Choose a field that uniquely identifies each record
2. **Multi-Field**: Use template syntax for combined keys
3. **For Display**: Create human-readable labels
4. **Consistency**: Keep label templates consistent

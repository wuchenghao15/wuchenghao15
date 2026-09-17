# Information Density Rules

Guidelines for keeping templates focused and readable.

---

## Core Principle

**Limit entity/relation fields to ≤5 for visual clarity and cognitive load.**

| Component | Max Fields | Reason |
|-----------|-----------|--------|
| `entities.fields` | 5 | Visual clarity in graph nodes |
| `relations.fields` | 5 | Readable edge labels |

---

## Field Priority

### Essential (Always Include)

| For | Fields |
|-----|--------|
| Graph | `source`, `target` |
| Hypergraph | `participants` (or grouping fields) |
| Temporal | `time` |
| Spatial | `location` |

### Important (Include If Needed)

| For | Fields |
|-----|--------|
| Type identification | `type` |
| Context | `description` |
| Metadata | `category`, `role` |

### Optional (Use Sparingly)

| For | Fields |
|-----|--------|
| Additional context | `notes` |
| Quality indicators | `confidence` |
| External references | `source` |

---

## Simplification Strategies

When fields exceed 5:

1. **Merge related fields**: `first_name` + `last_name` → `name`
2. **Move to description**: Move optional details to `description` field
3. **Use grouping**: Extract sub-fields into nested structure
4. **Prioritize**: Keep essential, mark others as optional

---

## Examples

### ❌ Too Many Fields (7)

```yaml
relations:
  fields:
    - name: source
    - name: target
    - name: type
    - name: strength
    - name: description
    - name: source_context
    - name: target_context
```

### ✅ Simplified (5)

```yaml
relations:
  fields:
    - name: source
    - name: target
    - name: type
    - name: strength
    - name: description  # Includes context info
```

---

## Detection

Flag for review when:
- `entities.fields` > 5
- `relations.fields` > 5

**Note**: This is a suggestion, not an error. Some templates may legitimately need more fields.

# Field Naming Standards

Standardized field names for consistency across templates.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Template name | CamelCase | `EarningsSummary` |
| Field names | snake_case | `company_name` |
| Tags | lowercase, comma-separated | `finance, investor` |

---

## Standard Field Names

### Graph Types (relations)

| Wrong | Correct | Reason |
|-------|---------|--------|
| `relation_type` | `type` | Redundant - already in relation context |
| `event_date` | `time` | More generic for temporal graphs |
| `location_info` | `location` | Shorter, clearer |
| `participant_list` | `participants` | Consistent with hypergraph |

### Entity Types

| Wrong | Correct | Reason |
|-------|---------|--------|
| `entity_type` | `type` | Consistency with relations |
| `object_type` | `type` | Shorter, same meaning |
| `node_category` | `type` | Shorter |

### Common Fields

| Wrong | Correct | Reason |
|-------|---------|--------|
| `created_at` | `created` | Shorter |
| `updated_at` | `updated` | Shorter |
| `description_text` | `description` | Redundant suffix |

---

## Detection Patterns

```
relation_type → type
entity_type → type
event_date → time
```

---

## Auto-fix Rules

These are safe to auto-fix:

1. `relation_type` → `type`
2. `event_date` → `time`
3. `entity_type` → `type`

**Note**: Also update identifiers.relation_id template and display.relation_label references.

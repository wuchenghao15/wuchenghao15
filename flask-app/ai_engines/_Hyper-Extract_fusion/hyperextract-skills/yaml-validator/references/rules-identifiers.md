# Identifier Validation Rules

Identifier configuration validation. See [SKILL.md](SKILL.md) for workflow.

---

## Binary Relations (graph/temporal/spatial)

```yaml
identifiers:
  entity_id: name              # ✓ References entity field
  relation_id: '{source}|...' # ✓ Template syntax correct
  relation_members:           # ✓ Map correctly
    source: source
    target: target
```

---

## Hypergraph

### Simple Hypergraph

```yaml
identifiers:
  entity_id: name
  relation_id: '{ruleType}|{action}'
  relation_members: participants  # STRING
```

### Nested Hypergraph

```yaml
identifiers:
  entity_id: name
  relation_id: '{event_name}'
  relation_members: [attackers, defenders]  # LIST
```

---

## Temporal Graph

```yaml
identifiers:
  time_field: event_date  # ✓ Must exist
```

---

## Spatial Graph

```yaml
identifiers:
  location_field: location  # ✓ Must exist
```

---

## Common Identifier Errors

1. **Missing identifiers**: Required but not present
2. **Wrong format**: relation_members type mismatch
3. **Invalid reference**: Referenced field doesn't exist
4. **Missing time/location field**: Required for temporal/spatial

---

## Validation Checklist

- [ ] identifiers.entity_id exists
- [ ] identifiers.relation_id exists
- [ ] identifiers.relation_members configured
- [ ] time_field configured (temporal types)
- [ ] location_field configured (spatial types)

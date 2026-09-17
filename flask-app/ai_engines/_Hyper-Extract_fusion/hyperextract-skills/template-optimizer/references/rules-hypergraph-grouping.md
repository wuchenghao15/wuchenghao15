# Hypergraph Grouping Rules

## Anti-Pattern Detection

### Pattern: Role Field + Simple Relation Members

**❌ Anti-Pattern**:
```yaml
relations:
  - name: event
  - name: participant
  - name: role  # ← Has role field

identifiers:
  relation_members: participants  # ← Simple string
```

**Problem**: When `relation_members` is a string but relations have a `role` field, entities should be partitioned by role.

**✅ Fix**: Use nested grouping
```yaml
relations:
  - name: event
  - name: group_a
    type: list
  - name: group_b
    type: list

identifiers:
  relation_members: [group_a, group_b]  # ← List of lists
```

## Decision Matrix

| Scenario | relation_members | Example |
|----------|-----------------|---------|
| Independent participants | `participants` (string) | Transaction between entities |
| Role-based groups | `[group_a, group_b]` (list) | Attackers/defenders in battle |
| Same semantic whole | `[group_a, group_b]` (list) | Herbs in formula by 君臣佐使 |

## Common Cases

| Scenario | Should Use Nested | Groups |
|----------|-----------------|--------|
| Formula composition | ✅ Yes | sovereigns, ministers, assistants, envoys |
| Battle participants | ✅ Yes | attackers, defenders |
| Meeting attendees | ✅ Yes | speakers, attendees |
| Independent trades | ❌ No | - |

## Rule Summary

⚠️ **If you have a `role` field in relations, consider using nested grouping instead.**

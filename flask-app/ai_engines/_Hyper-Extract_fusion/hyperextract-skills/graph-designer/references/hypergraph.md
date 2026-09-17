# Hypergraph Design Reference

Hypergraph design patterns for graph types. See [SKILL.md](SKILL.md) for workflow.

---

## Simple Hypergraph

Flat list of participants:

```yaml
relations:
  description: 'Hyperedge definitions'
  fields:
    - name: event_name
      type: str
      description: 'Event/relation name'
    - name: participants
      type: list
      description: 'List of participating entity names'
    - name: action
      type: str
      description: 'What happened'
    - name: outcome
      type: str
      description: 'Result or conclusion'
      required: false
```

### Identifier Configuration

```yaml
identifiers:
  entity_id: name
  relation_id: '{event_name}|{action}'
  relation_members: participants  # STRING
```

---

## Nested Hypergraph (Semantic Grouping)

Participants grouped by semantic role:

```yaml
relations:
  description: 'Hyperedge with semantic grouping'
  fields:
    - name: event_name
      type: str
    - name: group_a
      type: list
      description: 'Group A participants'
    - name: group_b
      type: list
      description: 'Group B participants'
    - name: group_c
      type: list
      description: 'Group C participants'
      required: false
    - name: outcome
      type: str
    - name: reasoning
      type: str
      required: false
```

### Identifier Configuration

```yaml
identifiers:
  entity_id: name
  relation_id: '{event_name}'
  relation_members: [group_a, group_b, group_c]  # LIST
```

---

## Common Grouping Patterns

| Scenario | Groups | Use Case |
|----------|--------|----------|
| Battle | attackers, defenders | Military conflicts |
| Political | attackers, defenders, planners, turncoats | Political struggles |
| Transaction | buyers, sellers, intermediaries | Commercial transactions |
| Project | leaders, developers, designers, testers | Software projects |
| Meeting | organizers, speakers, attendees | Business meetings |
| Contract | parties, witnesses | Legal documents |
| Negotiation | side_a, side_b, mediators | Diplomatic talks |

---

## Design Principles

1. **Group Count**: 2-5 groups per hyperedge is ideal
2. **Semantic Names**: Use meaningful role names
3. **Avoid Overlap**: Members usually in one group
4. **Consistent Structure**: Same groups across relations
5. **Clear Outcomes**: Always include outcome field

---

## When to Use Nested Grouping

Use **nested grouping** (list of lists) when:
- Same semantic whole: Entities naturally belong to the same concept
- Role-based partitioning: Entities partition by semantic roles
- Shared context: All entities share common attributes

⚠️ **If you find yourself adding a `role` field, consider using nested grouping instead.**

**❌ Wrong**: `relation_members: participants` + `role` field
**✅ Correct**: `relation_members: [group_a, group_b]`

| Scenario | Should Use Nested | Groups |
|----------|-----------------|--------|
| Formula (君臣佐使) | ✅ | sovereigns, ministers, assistants, envoys |
| Battle (攻防) | ✅ | attackers, defenders |
| Independent trades | ❌ | - |

---

## Design Checklist

- [ ] How many semantic groups?
- [ ] What are the group names?
- [ ] Can members belong to multiple groups?
- [ ] Is there an outcome/result?
- [ ] Is reasoning needed?
- [ ] Should use nested grouping instead of role field?

---
name: brainstorm
description: |
  Explore requirements and determine extraction type for Hyper-Extract.
  Use when user says: "design template", "extract data", "create extraction", "unsure which type to use".
  Trigger: User needs help deciding extraction type (model/list/set/graph/hypergraph).
  Skip: User already knows the type and wants specific design help.
---

# Brainstorm: Requirements Exploration

## Workflow

1. Clarify input/output
2. Discuss type details
3. Output design draft → Pass to designer

---

## Type Determination

### Decision Tree

```
Need to model relationships?
├─ No → Record types
│   ├─ Single object → model
│   ├─ Ordered list → list
│   └─ Deduplicated set → set
└─ Yes → Graph types
    ├─ Binary (A→B) → graph
    └─ Multi-entity (A+B+C→D)
        ├─ Flat list → hypergraph (simple)
        └─ Role groups → hypergraph (nested)

After graph:
├─ + time dimension → temporal_graph
├─ + space dimension → spatial_graph
└─ + both → spatio_temporal_graph
```

### Quick Reference

| Intent | Type |
|--------|------|
| Summary/card | model |
| Ordered items | list |
| Deduplicated entities | set |
| Binary relations | graph |
| Multi-party events | hypergraph |
| + time | temporal_graph |
| + space | spatial_graph |
| + time + space | spatio_temporal_graph |

---

## Discussion Questions

### For All Types
- What is the input source?
- What to extract?
- Key fields needed?

### For Graph Types
- Entity types and granularity?
- Relation types (predefined or custom)?
- Multi-type nodes?

### For Hypergraph
- Simple or nested grouping?
- How many semantic groups?
- Group names?

### For Temporal/Spatial
- Time/space on edge or node?
- Format handling?

---

## Output: Design Draft

### For Record Types (model/list/set)

```markdown
## Type: [model/list/set]

## Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| [name] | str | yes | ... |

## Notes
[Any special requirements]
```

### For Graph Types (graph/hypergraph/temporal/spatial)

```markdown
## Type: [graph/hypergraph/temporal/spatial]

## Entities
| Field | Type | Description |
|-------|------|-------------|
| name | str | Entity name |
| category | str | Entity type |

## Relations
| Field | Type | Description |
|-------|------|-------------|
| [field] | str/list | ... |

## Identifiers
- entity_id: name
- relation_id: '{...}'
- relation_members: [...]

## Notes
[Any special requirements]
```

### Type-Specific Fields

| Type | Additional Fields |
|------|-------------------|
| hypergraph | Participants or Groups |
| temporal_graph | time_field |
| spatial_graph | location_field |
| spatio_temporal_graph | time_field + location_field |

---

## Pass to Designer

After brainstorm, invoke the appropriate designer:
- model/list/set → record-designer
- graph/hypergraph/temporal/spatial → graph-designer

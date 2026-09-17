# Type-Specific Validation Rules

Type-specific validation for YAML configurations. See [SKILL.md](SKILL.md) for workflow.

---

## Record Types (model/list/set)

```yaml
output:
  description: '...'      # ✓ Exists
  fields:                 # ✓ Exists
    - name: ...           # ✓ Each field has name
      type: ...          # ✓ Has type
      description: ...   # ✓ Has description
```

### model

- No identifiers needed
- Single output structure

### list

- No identifiers needed
- Ordered items

### set

- identifiers.item_id required
- Deduplication key

---

## Graph Types

**Important**: All graph types (graph, hypergraph, temporal_graph, spatial_graph, spatio_temporal_graph) **must** use `entities` and `relations` as keys.

```yaml
output:
  entities:               # ✓ Required for ALL graph types (not nodes)
    description: '...'
    fields:
      - name: name
      - name: type
  relations:              # ✓ Required for ALL graph types (not hyperedges)
    description: '...'
    fields:
      - name: source     # ✓ graph: binary relation
      - name: target     # ✓ graph
      # --- OR ---
      - name: participants  # ✓ hypergraph: multi-entity relation
```

### graph

- Binary relations (source/target)
- identifiers with {source, target}
- identifiers.relation_members: source, target

### hypergraph

- Multi-entity relations (participants)
- identifiers.relation_members: participants
- **NOT** `nodes`/`hyperedges`, but `entities`/`relations`

### temporal_graph

- identifiers.time_field required
- Must also satisfy graph requirements

### spatial_graph

- identifiers.location_field required
- Must also satisfy graph requirements

### spatio_temporal_graph

- Both time_field and location_field required
- Must also satisfy graph requirements

---

## Common Validation Errors

### Hypergraph Common Errors

❌ **Wrong Example**:
```yaml
output:
  nodes:          # ✗ Wrong: not nodes
    ...
  hyperedges:     # ✗ Wrong: not hyperedges
    ...
guideline:
  rules_for_nodes:        # ✗ Wrong
  rules_for_hyperedges:  # ✗ Wrong
identifiers:
  node_id:       # ✗ Wrong
  hyperedge_id:   # ✗ Wrong
display:
  node_label:     # ✗ Wrong
  hyperedge_label: # ✗ Wrong
```

✅ **Correct Example**:
```yaml
output:
  entities:           # ✓ Correct
    ...
  relations:          # ✓ Correct
    ...
guideline:
  rules_for_entities:   # ✓ Correct
  rules_for_relations:  # ✓ Correct
identifiers:
  entity_id:       # ✓ Correct
  relation_id:     # ✓ Correct
  relation_members: participants
display:
  entity_label:    # ✓ Correct
  relation_label:   # ✓ Correct
```

---

## Field Value Validation

| Field | Valid Values | Common Errors |
|-------|-------------|---------------|
| output.fields[].type | str, int, float, bool, list | Typo: "bol" |
| language | zh/en or [zh, en] | Non-standard: "chinese" |
| extraction_mode | one_stage, two_stage | Typo: "two-stage" |

**Note**: The top-level `type` field must be one of the 8 AutoTypes: model, list, set, graph, hypergraph, temporal_graph, spatial_graph, spatio_temporal_graph.

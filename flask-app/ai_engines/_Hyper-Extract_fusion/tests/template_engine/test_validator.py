"""Unit tests for the template semantic validator."""

from pathlib import Path
from textwrap import dedent

from hyperextract.utils.template_engine import (
    validate_template,
    validate_template_dir,
)
from hyperextract.utils.template_engine.validator import (
    HE_T001,
    HE_T002,
    HE_T003,
    HE_T004,
    HE_T005,
    HE_T006,
    HE_T007,
    HE_T008,
    HE_T009,
)

PRESETS_DIR = (
    Path(__file__).resolve().parents[2] / "hyperextract" / "templates" / "presets"
)

VALID_GRAPH = """
language: en
name: ValidGraph
type: graph
tags: [test]
description: A valid graph template
output:
  description: graph output
  entities:
    description: entities
    fields:
      - name: name
        type: str
        description: entity name
      - name: type
        type: str
        description: entity type
  relations:
    description: relations
    fields:
      - name: source
        type: str
        description: source entity
      - name: target
        type: str
        description: target entity
      - name: type
        type: str
        description: relation type
guideline:
  target: Extract entities and relations
  rules_for_entities: Keep names stable
  rules_for_relations: Only explicit links
identifiers:
  entity_id: name
  relation_id: '{source}|{type}|{target}'
  relation_members:
    source: source
    target: target
display:
  entity_label: '{name}'
  relation_label: '{type}'
"""

VALID_HYPERGRAPH = """
language: en
name: ValidHypergraph
type: hypergraph
tags: [test]
description: A valid hypergraph template
output:
  description: hypergraph output
  entities:
    description: entities
    fields:
      - name: name
        type: str
        description: entity name
  relations:
    description: relations
    fields:
      - name: name
        type: str
        description: hyperedge name
      - name: participants
        type: list
        description: participating entities
guideline:
  target: Extract hyperedges
  rules_for_entities: Keep names stable
  rules_for_relations: Group co-participants
identifiers:
  entity_id: name
  relation_id: '{name}'
  relation_members: participants
display:
  entity_label: '{name}'
  relation_label: '{name}'
"""

VALID_SET = """
language: en
name: ValidSet
type: set
tags: [test]
description: A valid set template
output:
  description: set output
  fields:
    - name: name
      type: str
      description: item name
guideline:
  target: Extract items
  rules: Keep names stable
identifiers:
  item_id: name
display:
  label: '{name}'
"""


def _write(tmp_path: Path, content: str, name: str = "template.yaml") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
    return path


def _codes(result) -> list[str]:
    return [d.code for d in result.diagnostics]


def _by_code(result, code: str):
    return [d for d in result.diagnostics if d.code == code]


class TestValidTemplates:
    def test_valid_graph_has_no_diagnostics(self, tmp_path):
        path = _write(tmp_path, VALID_GRAPH)
        result = validate_template(path)
        assert result.ok
        assert result.diagnostics == []
        assert result.to_dict()["ok"] is True
        assert result.to_dict()["file"] == str(path)

    def test_valid_hypergraph_has_no_diagnostics(self, tmp_path):
        result = validate_template(_write(tmp_path, VALID_HYPERGRAPH))
        assert result.ok
        assert result.diagnostics == []

    def test_valid_set_has_no_diagnostics(self, tmp_path):
        result = validate_template(_write(tmp_path, VALID_SET))
        assert result.ok
        assert result.diagnostics == []

    def test_gallery_base_document_has_no_errors(self):
        result = validate_template(PRESETS_DIR / "general" / "base_document.yaml")
        assert result.ok
        assert not any(d.severity == "error" for d in result.diagnostics)


class TestStructureErrors:
    def test_invalid_yaml(self, tmp_path):
        path = _write(tmp_path, "name: [\n")
        result = validate_template(path)
        assert not result.ok
        assert HE_T001 in _codes(result)

    def test_invalid_schema_type(self, tmp_path):
        path = _write(tmp_path, VALID_GRAPH.replace("type: graph", "type: graphh"))
        result = validate_template(path)
        assert not result.ok
        assert HE_T002 in _codes(result)

    def test_document_with_graph_output_is_he_t002(self, tmp_path):
        yaml_text = VALID_GRAPH.replace("type: graph", "type: document").replace(
            "name: ValidGraph", "name: BadDocument"
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T002)
        assert diags
        assert any("output.fields" in d.message for d in diags)

    def test_document_with_only_entities_is_he_t002(self, tmp_path):
        yaml_text = """
language: en
name: EntitiesOnlyDocument
type: document
tags: [test]
description: document with a graph entities block
output:
  description: wrong shape
  entities:
    description: entities
    fields:
      - name: name
        type: str
        description: entity name
guideline:
  target: Extract
  rules: Keep names
display:
  label: '{name}'
"""
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        assert HE_T002 in _codes(result)

    def test_missing_file(self, tmp_path):
        result = validate_template(tmp_path / "missing.yaml")
        assert not result.ok
        assert HE_T001 in _codes(result)


class TestIdentifierErrors:
    def test_missing_entity_field(self, tmp_path):
        yaml_text = VALID_GRAPH.replace("entity_id: name", "entity_id: nickname")
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T003)
        assert diags
        assert diags[0].path == "identifiers.entity_id"
        assert "nickname" in diags[0].message

    def test_relation_members_dict_value_must_be_edge_field(self, tmp_path):
        yaml_text = VALID_GRAPH.replace(
            "    source: source\n    target: target",
            "    source: src\n    target: target",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T003)
        assert any(d.path == "identifiers.relation_members.source" for d in diags)

    def test_relation_members_must_define_source_and_target_roles(self, tmp_path):
        # Non-standard role keys ("from"/"to") whose VALUES are valid edge
        # fields: the extractor reads members["source"]/["target"], so the
        # validator must reject this instead of letting it KeyError at runtime.
        yaml_text = VALID_GRAPH.replace(
            "    source: source\n    target: target",
            "    from: source\n    to: target",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T003)
        assert any("source" in d.message for d in diags)
        assert any("target" in d.message for d in diags)

    def test_graph_members_must_be_dict(self, tmp_path):
        yaml_text = VALID_GRAPH.replace(
            "  relation_members:\n    source: source\n    target: target",
            "  relation_members: participants",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        assert HE_T004 in _codes(result)

    def test_hypergraph_members_must_not_be_dict(self, tmp_path):
        yaml_text = VALID_HYPERGRAPH.replace(
            "  relation_members: participants",
            "  relation_members:\n    source: source\n    target: target",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        assert HE_T004 in _codes(result)

    def test_hypergraph_member_field_must_be_list_type(self, tmp_path):
        yaml_text = VALID_HYPERGRAPH.replace(
            "      - name: participants\n        type: list",
            "      - name: participants\n        type: str",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        assert HE_T004 in _codes(result)


class TestDisplayErrors:
    def test_entity_label_unknown_placeholder(self, tmp_path):
        yaml_text = VALID_GRAPH.replace(
            "  entity_label: '{name}'",
            "  entity_label: '{title}'",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T005)
        assert diags
        assert diags[0].path == "display.entity_label"
        assert "title" in diags[0].message

    def test_constant_display_label_is_allowed(self, tmp_path):
        yaml_text = VALID_SET.replace("  label: '{name}'", "  label: '出院指导'")
        result = validate_template(_write(tmp_path, yaml_text))
        assert result.ok
        assert HE_T005 not in _codes(result)


class TestSpatiotemporalErrors:
    def test_temporal_graph_requires_time_field(self, tmp_path):
        yaml_text = VALID_GRAPH.replace("type: graph", "type: temporal_graph")
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T006)
        assert any(d.path == "identifiers.time_field" for d in diags)

    def test_spatial_graph_requires_location_field(self, tmp_path):
        yaml_text = VALID_GRAPH.replace("type: graph", "type: spatial_graph")
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        diags = _by_code(result, HE_T006)
        assert any(d.path == "identifiers.location_field" for d in diags)

    def test_spatio_temporal_requires_both(self, tmp_path):
        yaml_text = VALID_GRAPH.replace("type: graph", "type: spatio_temporal_graph")
        result = validate_template(_write(tmp_path, yaml_text))
        assert not result.ok
        paths = {d.path for d in _by_code(result, HE_T006)}
        assert "identifiers.time_field" in paths
        assert "identifiers.location_field" in paths


class TestWarningsDoNotFail:
    def test_bilingual_gap_is_warning(self, tmp_path):
        yaml_text = VALID_GRAPH.replace(
            "language: en\nname: ValidGraph",
            "language: [zh, en]\nname: ValidGraph",
        ).replace(
            "description: A valid graph template",
            "description:\n  en: A valid graph template",
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert result.ok
        assert result.error_count == 0
        assert HE_T007 in _codes(result)
        assert all(d.severity == "warning" for d in _by_code(result, HE_T007))

    def test_field_count_over_limit_is_warning(self, tmp_path):
        extra_fields = "\n".join(
            f"      - name: extra_{i}\n        type: str\n        description: extra"
            for i in range(4)
        )
        yaml_text = VALID_GRAPH.replace(
            "      - name: type\n        type: str\n        description: entity type",
            "      - name: type\n        type: str\n        description: entity type\n"
            + extra_fields,
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert result.ok
        diags = _by_code(result, HE_T008)
        assert diags
        assert diags[0].severity == "warning"
        assert diags[0].path == "output.entities.fields"

    def test_model_field_count_over_limit_is_warning(self, tmp_path):
        extra_fields = "\n".join(
            f"    - name: extra_{i}\n      type: str\n      description: extra"
            for i in range(5)
        )
        yaml_text = VALID_SET.replace("type: set", "type: model").replace(
            "    - name: name\n      type: str\n      description: item name",
            "    - name: name\n      type: str\n      description: item name\n"
            + extra_fields,
        )
        result = validate_template(_write(tmp_path, yaml_text))
        assert result.ok
        diags = _by_code(result, HE_T008)
        assert diags
        assert diags[0].severity == "warning"
        assert diags[0].path == "output.fields"
        assert "model" in diags[0].message

    def test_gallery_name_collision_is_warning(self, tmp_path):
        path = _write(
            tmp_path / "general",
            VALID_GRAPH.replace("name: ValidGraph", "name: graph"),
            name="dup.yaml",
        )
        result = validate_template(path)
        assert result.ok
        diags = _by_code(result, HE_T009)
        assert diags
        assert "general/graph" in diags[0].message


class TestJsonShape:
    def test_to_dict_is_stable(self, tmp_path):
        result = validate_template(
            _write(
                tmp_path,
                VALID_GRAPH.replace("entity_id: name", "entity_id: missing"),
            )
        )
        payload = result.to_dict()
        assert set(payload) == {"file", "diagnostics", "ok"}
        assert payload["ok"] is False
        assert payload["diagnostics"]
        item = payload["diagnostics"][0]
        assert set(item) == {"code", "severity", "path", "message"}


# Bundled presets that currently fail error-level checks. Keep the allowlist
# tight so new errors still fail; empty means every preset passes clean.
KNOWN_PRESET_ERRORS: dict = {}


class TestPresetBootstrap:
    def test_bundled_presets_have_no_unexpected_errors(self):
        results = validate_template_dir(PRESETS_DIR)
        assert results, "expected bundled presets"

        unexpected = []
        seen_known = set()
        for item in results:
            relative = str(Path(item.file).relative_to(PRESETS_DIR)).replace("\\", "/")
            error_codes = {d.code for d in item.diagnostics if d.severity == "error"}
            allowed = KNOWN_PRESET_ERRORS.get(relative, set())
            extra = error_codes - allowed
            missing = allowed - error_codes
            if extra or missing:
                unexpected.append((relative, sorted(error_codes), sorted(allowed)))
            if relative in KNOWN_PRESET_ERRORS:
                seen_known.add(relative)

        assert unexpected == []
        assert seen_known == set(KNOWN_PRESET_ERRORS)

        collisions = [
            item.file
            for item in results
            if any(d.code == HE_T009 for d in item.diagnostics)
        ]
        assert collisions == []

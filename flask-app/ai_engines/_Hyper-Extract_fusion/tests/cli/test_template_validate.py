"""Tests for the `he template validate` command."""

import json
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from hyperextract.cli.cli import app

runner = CliRunner()

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


def _write(tmp_path: Path, content: str, name: str = "template.yaml") -> Path:
    path = tmp_path / name
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
    return path


class TestTemplateValidateCli:
    def test_valid_template_exits_zero(self, tmp_path):
        path = _write(tmp_path, VALID_GRAPH)
        result = runner.invoke(app, ["template", "validate", str(path)])
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_document_graph_output_exits_one_with_he_t002(self, tmp_path):
        path = _write(
            tmp_path,
            VALID_GRAPH.replace("type: graph", "type: document").replace(
                "name: ValidGraph", "name: BadDocument"
            ),
        )
        result = runner.invoke(app, ["template", "validate", str(path)])
        assert result.exit_code == 1
        assert "HE-T002" in result.output
        assert "output.fields" in result.output

    def test_base_document_preset_is_clean(self):
        path = PRESETS_DIR / "general" / "base_document.yaml"
        result = runner.invoke(app, ["template", "validate", str(path)])
        assert result.exit_code == 0, result.output
        assert "OK" in result.output

    def test_identifier_error_exits_one(self, tmp_path):
        path = _write(
            tmp_path, VALID_GRAPH.replace("entity_id: name", "entity_id: nope")
        )
        result = runner.invoke(app, ["template", "validate", str(path)])
        assert result.exit_code == 1
        assert "HE-T003" in result.output
        assert "FAILED" in result.output

    def test_warning_only_exits_zero(self, tmp_path):
        yaml_text = VALID_GRAPH.replace(
            "language: en\nname: ValidGraph",
            "language: [zh, en]\nname: ValidGraph",
        ).replace(
            "description: A valid graph template",
            "description:\n  en: A valid graph template",
        )
        path = _write(tmp_path, yaml_text)
        result = runner.invoke(app, ["template", "validate", str(path)])
        assert result.exit_code == 0
        assert "HE-T007" in result.output

    def test_json_output_is_parseable(self, tmp_path):
        path = _write(
            tmp_path, VALID_GRAPH.replace("entity_id: name", "entity_id: missing")
        )
        result = runner.invoke(app, ["template", "validate", str(path), "--json"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["ok"] is False
        assert payload["file"] == str(path)
        assert isinstance(payload["diagnostics"], list)
        item = payload["diagnostics"][0]
        assert set(item) == {"code", "severity", "path", "message"}
        assert item["code"] == "HE-T003"

    def test_json_success_shape(self, tmp_path):
        path = _write(tmp_path, VALID_GRAPH)
        result = runner.invoke(app, ["template", "validate", str(path), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {"file": str(path), "diagnostics": [], "ok": True}

    def test_directory_requires_all(self, tmp_path):
        _write(tmp_path, VALID_GRAPH)
        result = runner.invoke(app, ["template", "validate", str(tmp_path)])
        assert result.exit_code == 1
        assert "--all" in result.output

    def test_batch_valid_directory_is_green(self, tmp_path):
        _write(tmp_path, VALID_GRAPH, name="a.yaml")
        _write(
            tmp_path,
            VALID_GRAPH.replace("name: ValidGraph", "name: Other"),
            name="b.yaml",
        )
        result = runner.invoke(app, ["template", "validate", str(tmp_path), "--all"])
        assert result.exit_code == 0, result.output

    def test_batch_presets_are_clean(self):
        result = runner.invoke(
            app, ["template", "validate", str(PRESETS_DIR), "--all", "--json"]
        )
        # All bundled presets pass error-level checks. workflow_graph was
        # retagged from temporal_graph to graph (it has no time fields);
        # education presets added in v0.5.0 must not fail either.
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        failed = [item for item in payload["results"] if not item["ok"]]
        assert failed == []
        education = [
            item
            for item in payload["results"]
            if item["file"]
            .replace("\\", "/")
            .endswith(("course_concept_graph.yaml", "curriculum_structure.yaml"))
        ]
        assert len(education) == 2
        assert all(item["ok"] for item in education)

    def test_batch_json_wraps_results(self, tmp_path):
        _write(tmp_path, VALID_GRAPH, name="a.yaml")
        _write(
            tmp_path,
            VALID_GRAPH.replace("name: ValidGraph", "name: Other"),
            name="b.yaml",
        )
        result = runner.invoke(
            app, ["template", "validate", str(tmp_path), "--all", "--json"]
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert len(payload["results"]) == 2
        assert {item["ok"] for item in payload["results"]} == {True}

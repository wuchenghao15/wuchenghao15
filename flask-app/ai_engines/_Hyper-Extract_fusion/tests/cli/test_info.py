"""Tests for the `he info` command (--sources source ledger view)."""

import json

from typer.testing import CliRunner

from hyperextract.cli.cli import app

runner = CliRunner()


def _make_ka_with_sources(tmp_path, *, with_ledger: bool = True):
    """A minimal KA directory on disk, optionally with source ledger files."""
    ka = tmp_path / "ka"
    ka.mkdir(parents=True)
    (ka / "data.json").write_text(
        json.dumps(
            {
                "nodes": [{"name": "mock_name", "type": "ENTITY", "description": ""}],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    (ka / "metadata.json").write_text(
        json.dumps({"template": "general/graph", "lang": "en"}),
        encoding="utf-8",
    )
    if with_ledger:
        (ka / "sources_nodes.json").write_text(
            json.dumps(
                [
                    {
                        "source_id": "doc-1",
                        "content_hash": "abc",
                        "raw_items": [
                            {"name": "mock_name", "type": "ENTITY", "description": ""}
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        (ka / "sources_edges.json").write_text(json.dumps([]), encoding="utf-8")
    return ka


class TestInfoSourcesCli:
    def test_sources_renders_source_ledger(self, tmp_path):
        ka = _make_ka_with_sources(tmp_path)

        result = runner.invoke(app, ["info", str(ka), "--sources"])

        assert result.exit_code == 0, result.output
        assert "Source Ledger" in result.output
        assert "doc-1" in result.output
        assert "abc" in result.output

    def test_sources_without_ledger_prints_hint(self, tmp_path):
        ka = _make_ka_with_sources(tmp_path, with_ledger=False)

        result = runner.invoke(app, ["info", str(ka), "--sources"])

        assert result.exit_code == 0, result.output
        assert "No source ledger" in result.output

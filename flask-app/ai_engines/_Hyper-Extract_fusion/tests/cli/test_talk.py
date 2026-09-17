"""Tests for the interactive `he talk` chat loop and scoped chat flags."""

import inspect
import json
from pathlib import Path
from unittest.mock import patch

from pydantic import BaseModel
from typer.testing import CliRunner

import hyperextract.cli.cli as climod
from hyperextract.cli.cli import app
from hyperextract.types import AutoList

runner = CliRunner()


def _ka_dir(tmp_path: Path) -> Path:
    ka = tmp_path / "ka"
    ka.mkdir()
    (ka / "data.json").write_text("{}", encoding="utf-8")
    (ka / "metadata.json").write_text(
        json.dumps({"template": "general/graph", "lang": "en"}),
        encoding="utf-8",
    )
    index = ka / "index"
    index.mkdir()
    (index / "dummy").write_text("x", encoding="utf-8")
    return ka


def test_chat_loop_passes_top_k(monkeypatch):
    """Interactive chat must forward top_k to ka.chat, not use the default."""
    recorded = {}

    class _StubKA:
        def chat(self, query, top_k=3, *, source_ids=None, tags=None):
            recorded["top_k"] = top_k
            recorded["source_ids"] = source_ids
            recorded["tags"] = tags
            return type("_Resp", (), {"content": "ok"})()

    queries = iter(["hello", "exit"])
    monkeypatch.setattr(climod.console, "input", lambda *a, **k: next(queries))

    climod.chat_loop(_StubKA(), "some/ka", top_k=10, source_ids=["s1"], tags=["t1"])

    assert recorded["top_k"] == 10
    assert recorded["source_ids"] == ["s1"]
    assert recorded["tags"] == ["t1"]


def test_talk_forwards_source_and_tag(tmp_path):
    recorded = {}

    class _GraphChatKA:
        def load(self, path):
            pass

        def search(self, query, top_k=3, *, source_ids=None, tags=None):
            return []

        def chat(self, query, top_k=3, *, source_ids=None, tags=None):
            recorded["query"] = query
            recorded["source_ids"] = source_ids
            recorded["tags"] = tags
            return type("_Resp", (), {"content": "ok", "additional_kwargs": {}})()

    ka_dir = _ka_dir(tmp_path)
    with (
        patch("hyperextract.cli.cli.validate_config"),
        patch("hyperextract.cli.cli.Template.create", return_value=_GraphChatKA()),
    ):
        result = runner.invoke(
            app,
            [
                "talk",
                str(ka_dir),
                "-q",
                "hello",
                "--source",
                "s1",
                "--tag",
                "t1",
            ],
        )

    assert result.exit_code == 0, result.output
    assert recorded["query"] == "hello"
    assert recorded["source_ids"] == ["s1"]
    assert recorded["tags"] == ["t1"]


class _ListItem(BaseModel):
    name: str


def test_talk_scope_rejected_on_autolist(tmp_path, llm_client, embedder):
    """Production AutoList inherits base.chat(source_ids=...), but search() has no ledger.

    A stub whose chat() omits those kwargs hid the bug: inspecting chat() then
    lets `he talk --source` through and silently ignores the filter.
    """
    ka = AutoList(
        item_schema=_ListItem,
        llm_client=llm_client,
        embedder=embedder,
    )
    assert "source_ids" in inspect.signature(type(ka).chat).parameters
    assert "source_ids" not in inspect.signature(type(ka).search).parameters

    ka_dir = _ka_dir(tmp_path)
    with (
        patch("hyperextract.cli.cli.validate_config"),
        patch("hyperextract.cli.cli.Template.create", return_value=ka),
        patch.object(ka, "load"),
    ):
        result = runner.invoke(
            app,
            ["talk", str(ka_dir), "-q", "hello", "--source", "s1"],
        )

    assert result.exit_code == 1
    assert "AutoList" in result.output
    assert "source ledger" in result.output
    assert "scoped chat" in result.output.lower() or "Scoped chat" in result.output


def test_talk_scope_rejected_when_chat_does_not_forward(tmp_path):
    """search() can scope, but chat() does not yet accept the kwargs (Cog_RAG pre-#171)."""

    class _SearchScopedChatPlain:
        def load(self, path):
            pass

        def search(self, query, top_k=3, *, source_ids=None, tags=None):
            return []

        def chat(self, query, top_k=3):
            return type("_Resp", (), {"content": "ok", "additional_kwargs": {}})()

    ka_dir = _ka_dir(tmp_path)
    with (
        patch("hyperextract.cli.cli.validate_config"),
        patch(
            "hyperextract.cli.cli.Template.create",
            return_value=_SearchScopedChatPlain(),
        ),
    ):
        result = runner.invoke(
            app,
            ["talk", str(ka_dir), "-q", "hello", "--source", "s1"],
        )

    assert result.exit_code == 1
    assert "Scoped chat" in result.output or "scoped chat" in result.output.lower()

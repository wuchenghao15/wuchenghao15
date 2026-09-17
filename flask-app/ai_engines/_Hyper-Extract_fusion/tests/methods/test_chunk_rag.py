"""End-to-end coverage for the chunk_rag method and the `he tag` fix.

Registry resolution, Template.create wiring, CLI search/info/tag on a real
on-disk KA (LLM mocked), and AutoGraph tag delegation (latent bug: the `he
tag` command called ka.tag_source which no graph type implemented).
"""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from hyperextract.cli.cli import app
from hyperextract.methods.rag import Chunk_RAG
from hyperextract.methods.registry import get_method, get_method_cfg
from hyperextract.utils.template_engine import Template
from hyperextract.utils.template_engine.template import Template as TemplateClass

runner = CliRunner()


def _patch_create(llm_client, embedder):
    """Patch Template.create to build instances with mock clients.

    Routes through TemplateFactory so the patched method is not re-entered.
    """
    from hyperextract.utils.template_engine.factory import TemplateFactory

    def _factory(source, language=None, **kwargs):
        return TemplateFactory.create(source, llm_client=llm_client, embedder=embedder)

    return patch.object(TemplateClass, "create", side_effect=_factory)


def _build_ka_on_disk(llm_client, embedder, tmp_path):
    """Build a chunk_rag KA directory exactly like `he parse` would."""
    ka = Template.create("method/chunk_rag", llm_client=llm_client, embedder=embedder)
    ka.feed_text("Alpha loves beta. " * 200, source_id="docA", content_hash="ha")
    ka.feed_text("Gamma is a different document.", source_id="docB", content_hash="hb")
    ka.tag_source("docB", add=["team-b"])
    ka.dump(tmp_path)
    ka.build_index()
    ka.dump(tmp_path)
    (tmp_path / "metadata.json").write_text(
        json.dumps({"template": "method/chunk_rag", "lang": "en"}),
        encoding="utf-8",
    )
    return ka


class TestRegistry:
    def test_registered_as_document_method(self):
        info = get_method("chunk_rag")
        assert info is not None
        assert info["class"] is Chunk_RAG
        assert info["type"] == "document"

        cfg = get_method_cfg("chunk_rag")
        assert cfg is not None and cfg.type == "document"

    def test_template_get_and_create(self, llm_client, embedder):
        cfg = Template.get("method/chunk_rag")
        assert cfg is not None and cfg.type == "document"

        ka = Template.create(
            "method/chunk_rag", llm_client=llm_client, embedder=embedder
        )
        assert isinstance(ka, Chunk_RAG)
        assert ka.metadata["template"] == "method/chunk_rag"

    def test_template_list_includes_method(self):
        names = set(Template.list(include_methods=True))
        assert "method/chunk_rag" in names


class TestCliOnDiskKA:
    @pytest.fixture
    def ka_dir(self, llm_client, embedder, tmp_path):
        target = tmp_path / "ka"
        target.mkdir()
        _build_ka_on_disk(llm_client, embedder, target)
        return target

    def test_get_template_from_ka_resolves_method(self, ka_dir):
        from hyperextract.cli.utils import get_template_from_ka

        template, lang = get_template_from_ka(ka_dir)
        assert template == "method/chunk_rag"
        assert lang == "en"

    def test_search_command_prints_chunks(self, ka_dir, llm_client, embedder):
        with (
            patch("hyperextract.cli.cli.validate_config"),
            _patch_create(llm_client, embedder),
        ):
            # Fetch all 3 chunks: hash-based mock embeddings give no semantic
            # ranking, so asserting on a top-2 slice would be order-fragile.
            result = runner.invoke(
                app, ["search", str(ka_dir), "gamma document", "-n", "3"]
            )

        assert result.exit_code == 0, result.output
        assert "Gamma is a different document." in result.output

    def test_search_command_scoped_by_tag(self, ka_dir, llm_client, embedder):
        with (
            patch("hyperextract.cli.cli.validate_config"),
            _patch_create(llm_client, embedder),
        ):
            result = runner.invoke(
                app,
                [
                    "search",
                    str(ka_dir),
                    "alpha loves beta",
                    "-n",
                    "5",
                    "--tag",
                    "team-b",
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Alpha" not in result.output

    def test_info_shows_chunks(self, ka_dir):
        result = runner.invoke(app, ["info", str(ka_dir)])
        assert result.exit_code == 0, result.output
        assert "Chunks" in result.output

    def test_info_sources_lists_ledger(self, ka_dir):
        result = runner.invoke(app, ["info", str(ka_dir), "--sources"])
        assert result.exit_code == 0, result.output
        assert "docA" in result.output and "docB" in result.output

    def test_tag_command_adds_tags(self, ka_dir, llm_client, embedder):
        with _patch_create(llm_client, embedder):
            result = runner.invoke(
                app,
                ["tag", str(ka_dir), "--source", "docA", "--add", "team-a"],
            )

        assert result.exit_code == 0, result.output
        assert "team-a" in result.output

    def test_remove_document_rolls_back(self, ka_dir, llm_client, embedder):
        with (
            patch("hyperextract.cli.cli.validate_config"),
            _patch_create(llm_client, embedder),
        ):
            result = runner.invoke(
                app,
                ["remove", str(ka_dir), "--document", "docA", "--no-backup", "-y"],
            )

        assert result.exit_code == 0, result.output
        assert "removed_chunks" in result.output

        # The rollback is persisted and the ledger is gone for docA.
        restored = Template.create(
            "method/chunk_rag", llm_client=llm_client, embedder=embedder
        )
        restored.load(ka_dir)
        assert "docA" not in restored.sources()
        assert "docB" in restored.sources()


class TestGraphTagDelegation:
    """`he tag` calls ka.tag_source / ka.source_tags — never implemented on
    graph types (latent AttributeError). Direct unit coverage here."""

    @staticmethod
    def _graph():
        from ontomem.merger import MergeStrategy
        from pydantic import BaseModel

        from hyperextract.types import AutoGraph
        from tests.mocks import MockChatModel, MockEmbeddings

        class Entity(BaseModel):
            name: str
            type: str = "ENTITY"
            description: str = ""

        class Relation(BaseModel):
            source: str
            target: str
            relation_type: str
            description: str = ""

        return AutoGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=MockChatModel(),
            embedder=MockEmbeddings(),
            node_strategy_or_merger=MergeStrategy.MERGE_FIELD,
            edge_strategy_or_merger=MergeStrategy.MERGE_FIELD,
        )

    def test_tag_applies_to_both_ledgers(self):
        graph = self._graph()
        node = {"name": "Alice", "type": "PERSON", "description": ""}
        edge = {
            "source": "Alice",
            "target": "Bob",
            "relation_type": "knows",
            "description": "",
        }
        graph._node_memory.record_source("s1", [node])
        graph._edge_memory.record_source("s1", [edge])

        tags = graph.tag_source("s1", add=["papers"])
        assert tags == ["papers"]
        assert graph.source_tags("s1") == ["papers"]
        # Both ledgers stay in sync so scoped search is consistent.
        assert graph._node_memory.source_tags("s1") == ["papers"]
        assert graph._edge_memory.source_tags("s1") == ["papers"]

    def test_tag_source_in_edge_ledger_only(self):
        graph = self._graph()
        edge = {
            "source": "A",
            "target": "B",
            "relation_type": "r",
            "description": "",
        }
        graph._edge_memory.record_source("edge-only", [edge])
        assert graph.tag_source("edge-only", add=["t"]) == ["t"]
        assert graph.source_tags("edge-only") == ["t"]

    def test_unknown_source_raises_keyerror(self):
        graph = self._graph()
        with pytest.raises(KeyError):
            graph.tag_source("missing", add=["t"])

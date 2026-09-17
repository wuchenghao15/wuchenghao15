"""Tests for the `he remove` command (hard delete + LLM-assisted soft delete)."""

import json

import pytest
from pydantic import BaseModel
from typer.testing import CliRunner

import hyperextract.cli.cli as climod
from hyperextract.cli.cli import app
from hyperextract.types import AutoGraph
from tests.mocks import MockChatModel, MockEmbeddings

runner = CliRunner()


class E(BaseModel):
    name: str
    type: str = "ENTITY"
    description: str = ""


class R(BaseModel):
    source: str
    target: str
    relation_type: str
    description: str = ""


class FakeChatModel:
    """Chat-model stub: with_structured_output returns the canned item."""

    def __init__(self, canned):
        self.canned = canned

    def with_structured_output(self, schema):
        model = self

        from langchain_core.runnables import Runnable

        class _Runnable(Runnable):
            def invoke(self, prompt_value, config=None, **kwargs):
                return model.canned

        return _Runnable()


def _real_ka():
    g = AutoGraph(
        node_schema=E,
        edge_schema=R,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
    )
    g._node_memory.add(
        [
            E(
                name="Apple",
                description="Apple was founded by Steve Jobs. Apple makes iPhones.",
            ),
            E(name="Google"),
        ]
    )
    g._edge_memory.add([R(source="Apple", target="Google", relation_type="partner")])
    return g


@pytest.fixture
def ka_env(tmp_path, monkeypatch):
    """A real AutoGraph dumped to disk; Template.create returns it in tests."""
    g = _real_ka()
    g.metadata["template"] = "general/graph"
    g.metadata["lang"] = "en"
    ka = tmp_path / "ka"
    g.dump(ka)
    # A stale index dir, like a KA that was searched before.
    (ka / "index" / "node_index").mkdir(parents=True, exist_ok=True)
    (ka / "index" / "node_index" / "index.faiss").write_text("x")

    monkeypatch.setattr(climod.Template, "create", staticmethod(lambda *a, **k: g))
    return ka, g


def _data(ka):
    return json.loads((ka / "data.json").read_text())


class TestHardDeleteCli:
    def test_remove_node_updates_data_and_writes_backup(self, ka_env):
        ka, _ = ka_env
        result = runner.invoke(app, ["remove", str(ka), "--node", "Apple", "-y"])

        assert result.exit_code == 0, result.output
        names = [n["name"] for n in _data(ka)["nodes"]]
        assert names == ["Google"]
        # Orphan edge pruned in the persisted data too.
        assert _data(ka)["edges"] == []
        # Backup + stale index handling.
        assert list(ka.glob("data.json.bak.*"))
        assert not (ka / "index").exists()

    def test_dry_run_persists_nothing(self, ka_env):
        ka, _ = ka_env
        result = runner.invoke(app, ["remove", str(ka), "--node", "Apple", "--dry-run"])

        assert result.exit_code == 0, result.output
        assert [n["name"] for n in _data(ka)["nodes"]] == ["Apple", "Google"]
        assert not list(ka.glob("data.json.bak.*"))

    def test_built_index_is_patched_not_discarded(self, tmp_path, monkeypatch):
        """With a real built index, he remove patches it in place."""
        g = _real_ka()
        g.metadata["template"] = "general/graph"
        g.metadata["lang"] = "en"
        g.build_index()
        ka = tmp_path / "ka"
        g.dump(ka)
        assert (ka / "index" / "node_index" / "index.faiss").exists()
        monkeypatch.setattr(climod.Template, "create", staticmethod(lambda *a, **k: g))

        result = runner.invoke(app, ["remove", str(ka), "--node", "Apple", "-y"])

        assert result.exit_code == 0, result.output
        assert "patched in place" in result.output
        # The index survives, and its docstore no longer holds the removed node.
        assert (ka / "index" / "node_index" / "index.faiss").exists()
        docstore = (ka / "index" / "node_index" / "index.pkl").read_bytes()
        assert b"Apple" not in docstore
        assert b"Google" in docstore
        assert [n["name"] for n in _data(ka)["nodes"]] == ["Google"]

    def test_no_match_reports_and_writes_nothing(self, ka_env):
        ka, _ = ka_env
        result = runner.invoke(app, ["remove", str(ka), "--node", "Ghost", "-y"])

        assert result.exit_code == 0
        assert "Nothing matched" in result.output
        assert [n["name"] for n in _data(ka)["nodes"]] == ["Apple", "Google"]
        assert not list(ka.glob("data.json.bak.*"))


class TestSoftDeleteCli:
    def test_soft_delete_applies_with_backup(self, ka_env):
        ka, g = ka_env
        g._node_memory.llm_client = FakeChatModel(
            E(name="Apple", description="Apple makes iPhones.")
        )

        result = runner.invoke(
            app,
            [
                "remove",
                str(ka),
                "--edit-node",
                "Apple",
                "--fact",
                "founded by Steve Jobs",
                "-y",
            ],
        )

        assert result.exit_code == 0, result.output
        apple = next(n for n in _data(ka)["nodes"] if n["name"] == "Apple")
        assert apple["description"] == "Apple makes iPhones."
        assert list(ka.glob("data.json.bak.*"))

    def test_soft_delete_dry_run_shows_proposal_only(self, ka_env):
        ka, g = ka_env
        g._node_memory.llm_client = FakeChatModel(
            E(name="Apple", description="Apple makes iPhones.")
        )

        result = runner.invoke(
            app,
            [
                "remove",
                str(ka),
                "--edit-node",
                "Apple",
                "--fact",
                "founded by Steve Jobs",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0, result.output
        assert "Proposed" in result.output
        apple = next(n for n in _data(ka)["nodes"] if n["name"] == "Apple")
        assert "founded by Steve Jobs" in apple["description"]
        assert not list(ka.glob("data.json.bak.*"))

    def test_soft_delete_key_change_rejected(self, ka_env):
        ka, g = ka_env
        g._node_memory.llm_client = FakeChatModel(E(name="Renamed"))

        result = runner.invoke(
            app,
            ["remove", str(ka), "--edit-node", "Apple", "--fact", "x", "-y"],
        )

        assert result.exit_code == 1
        assert "key changed" in result.output
        assert [n["name"] for n in _data(ka)["nodes"]] == ["Apple", "Google"]


class TestDocumentRollbackCli:
    def test_document_rollback_removes_only_that_document(self, tmp_path, monkeypatch):
        g = _real_ka()
        g.metadata["template"] = "general/graph"
        g.metadata["lang"] = "en"
        g._node_memory.add([E(name="Apple"), E(name="Google")])
        g.feed_text("Apple partners with DeepMind on AI research.", source_id="doc-1")
        ka = tmp_path / "ka"
        g.dump(ka)
        monkeypatch.setattr(climod.Template, "create", staticmethod(lambda *a, **k: g))

        result = runner.invoke(app, ["remove", str(ka), "--document", "doc-1", "-y"])

        assert result.exit_code == 0, result.output
        names = [n["name"] for n in _data(ka)["nodes"]]
        # Direct-added nodes stay; everything doc-1 contributed is rolled back.
        assert "Apple" in names and "Google" in names
        assert "mock_name" not in names
        # Provenance ledger persisted alongside the KA.
        assert (ka / "sources_nodes.json").exists()

    def test_document_without_contributions_reports_nothing(
        self, tmp_path, monkeypatch
    ):
        g = _real_ka()
        g.metadata["template"] = "general/graph"
        g.metadata["lang"] = "en"
        g._node_memory.add([E(name="Apple")])
        ka = tmp_path / "ka"
        g.dump(ka)
        monkeypatch.setattr(climod.Template, "create", staticmethod(lambda *a, **k: g))

        result = runner.invoke(
            app, ["remove", str(ka), "--document", "ghost-doc", "-y"]
        )

        assert result.exit_code == 0
        assert "Nothing matched" in result.output


class TestDocumentRollbackStrategies:
    @staticmethod
    def _strategy_ka(tmp_path, monkeypatch):
        """A KA with two recorded sources sharing the node "Shared", plus
        s1's own node "FromS1" — all seeded deterministically (no extraction
        LLM): ledger entries via record_source, storage via direct add()."""
        g = _real_ka()
        g.metadata["template"] = "general/graph"
        g.metadata["lang"] = "en"
        g._node_memory.add(
            [E(name="FromS1", type="X"), E(name="Shared", description="shared")]
        )
        g._node_memory.record_source(
            "s1",
            [E(name="FromS1", type="X").model_dump(), E(name="Shared").model_dump()],
        )
        g._node_memory.record_source("s2", [E(name="Shared").model_dump()])
        # The edge ledger needs the source too, or remove_source bails out
        # with KeyError before any node is touched.
        g._edge_memory.record_source("s1", [])
        g._edge_memory.record_source("s2", [])
        ka = tmp_path / "ka"
        g.dump(ka)
        monkeypatch.setattr(climod.Template, "create", staticmethod(lambda *a, **k: g))
        return ka, g

    def test_remove_document_strategy_touched(self, tmp_path, monkeypatch):
        ka, _ = self._strategy_ka(tmp_path, monkeypatch)

        result = runner.invoke(
            app,
            ["remove", str(ka), "--document", "s1", "--strategy", "touched", "-y"],
        )

        assert result.exit_code == 0, result.output
        names = [n["name"] for n in _data(ka)["nodes"]]
        # Touched deletes every key s1 touched outright — "Shared" is gone
        # even though s2 also contributed it (no re-merge step).
        assert "FromS1" not in names
        assert "Shared" not in names
        assert "Apple" in names and "Google" in names
        assert "Document Rollback Report" in result.output
        assert "FromS1" in result.output
        assert "Shared" in result.output

    def test_remove_document_strategy_exact_remerges(self, tmp_path, monkeypatch):
        from ontomem.merger import MergeStrategy, create_merger

        ka, g = self._strategy_ka(tmp_path, monkeypatch)
        # Deterministic re-merge: the default LLM.BALANCED merger would need
        # a real LLM; MERGE_FIELD keeps this offline.
        g._node_memory._merger = create_merger(
            MergeStrategy.MERGE_FIELD, key_extractor=lambda x: x.name
        )

        result = runner.invoke(
            app,
            ["remove", str(ka), "--document", "s1", "--strategy", "exact", "-y"],
        )

        assert result.exit_code == 0, result.output
        names = [n["name"] for n in _data(ka)["nodes"]]
        # "Shared" survives: re-merged from s2's raw contribution. "FromS1"
        # (s1's sole contribution) is gone.
        assert "Shared" in names
        assert "FromS1" not in names
        assert "Document Rollback Report" in result.output
        assert "Shared" in result.output


class TestArgumentValidation:
    def test_hard_and_soft_delete_are_mutually_exclusive(self, ka_env):
        ka, _ = ka_env
        result = runner.invoke(
            app,
            [
                "remove",
                str(ka),
                "--node",
                "Apple",
                "--edit-node",
                "Apple",
                "--fact",
                "x",
            ],
        )
        assert result.exit_code == 1

    def test_soft_delete_requires_fact_or_instruction(self, ka_env):
        ka, _ = ka_env
        result = runner.invoke(app, ["remove", str(ka), "--edit-node", "Apple"])
        assert result.exit_code == 1

    def test_no_action_prints_hint(self, ka_env):
        ka, _ = ka_env
        result = runner.invoke(app, ["remove", str(ka)])
        assert result.exit_code == 0
        assert "Nothing to do" in result.output


class TestNonGraphKa:
    def test_list_ka_gets_friendly_error(self, tmp_path, monkeypatch):
        """List/set/model KAs don't support keyed deletion — say so clearly."""
        from hyperextract.types import AutoList

        class Item(BaseModel):
            name: str

        g = AutoList(
            item_schema=Item,
            llm_client=MockChatModel(),
            embedder=MockEmbeddings(),
        )
        g.metadata["template"] = "general/list"
        g.metadata["lang"] = "en"
        ka = tmp_path / "ka"
        g.dump(ka)
        monkeypatch.setattr(climod.Template, "create", staticmethod(lambda *a, **k: g))

        result = runner.invoke(app, ["remove", str(ka), "--node", "Apple", "-y"])

        assert result.exit_code == 1
        assert "graph-family" in result.output
        assert "AutoList" in result.output

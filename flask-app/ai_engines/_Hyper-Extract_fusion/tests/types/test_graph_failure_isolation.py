"""Graph-family extraction isolates per-chunk LLM failures (issue #78).

BaseAutoType already treats one bad chunk as a partial result; the graph-family
overrides (one-stage invoke/batch, two-stage node/edge batches) previously let
a single provider error (rate limit, timeout, unparseable output) abort the
whole run and discard every other chunk's data. These tests pin the contract:

- one-stage single/batch paths survive chunk failures (empty result, no raise)
- two-stage skips edge extraction for chunks whose node extraction failed
  (no wasted LLM call with an empty node list) while keeping merge alignment
- observation time/location injection keeps working for the spatiotemporal
  subclasses alongside the isolation
"""

from pydantic import BaseModel, Field

from hyperextract.types import AutoGraph, AutoHypergraph, AutoTemporalGraph
from tests.mocks import MockChatModel, MockEmbeddings


class Entity(BaseModel):
    """Simple node schema for testing."""

    name: str
    type: str = "ENTITY"
    properties: dict = Field(default_factory=dict)


class Relation(BaseModel):
    """Simple edge schema for testing."""

    source: str
    target: str
    relation_type: str


class HyperRelation(BaseModel):
    """Simple hyperedge schema for testing."""

    participants: list[str] = Field(default_factory=list)
    relation_type: str = "related"


LONG_TEXT = "sentence about entities. " * 100  # forces multi-chunk at small chunk_size


class _FlakyBatch:
    """Extractor stub that fails odd-index chunks.

    Mirrors the Runnable.batch contract: with return_exceptions=True failures
    come back as exceptions in the list; without it the first failure raises.
    """

    def __init__(self, ok_factory):
        self.ok_factory = ok_factory
        self.batch_sizes = []  # number of inputs per batch() call

    def invoke(self, _input, config=None):
        return self.ok_factory(0)

    def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
        self.batch_sizes.append(len(inputs))
        results = []
        for i in range(len(inputs)):
            if i % 2 == 1:
                err = RuntimeError(f"429 rate limit on chunk {i}")
                if return_exceptions:
                    results.append(err)
                else:
                    raise err
            else:
                results.append(self.ok_factory(i))
        return results


class _InvokeFails:
    """Extractor stub whose invoke() always raises (unparseable LLM output)."""

    def invoke(self, _input, config=None):
        raise ValueError("Invalid JSON: expected value at line 1 column 1")

    def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
        raise AssertionError("batch() not expected on the single-chunk path")


class _RecordingEdgeExtractor:
    """Edge-extractor stub recording every batch input it is given."""

    def __init__(self, empty_factory):
        self.seen_inputs = []
        self.empty_factory = empty_factory  # returns an empty EdgeListSchema

    def invoke(self, _input, config=None):
        raise AssertionError("invoke() not expected in two-stage edge extraction")

    def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
        self.seen_inputs.extend(inputs)
        return [self.empty_factory() for _ in inputs]


def _graph(extraction_mode="one_stage", chunk_size=64):
    g = AutoGraph(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
        extraction_mode=extraction_mode,
        chunk_size=chunk_size,
        chunk_overlap=16,
    )
    return g


def _hypergraph(extraction_mode="one_stage", chunk_size=64):
    h = AutoHypergraph(
        node_schema=Entity,
        edge_schema=HyperRelation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.relation_type}_{sorted(x.participants)}",
        nodes_in_edge_extractor=lambda x: tuple(x.participants),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
        extraction_mode=extraction_mode,
        chunk_size=chunk_size,
        chunk_overlap=16,
    )
    return h


class TestOneStageIsolation:
    """One-stage extraction survives per-chunk provider failures."""

    def test_multi_chunk_batch_failure_keeps_good_chunks(self):
        g = _graph()
        g.data_extractor = _FlakyBatch(
            lambda i: g.graph_schema(nodes=[Entity(name=f"N{i}")], edges=[])
        )

        result = g.parse(LONG_TEXT)

        names = {n.name for n in result.nodes}
        # Even-index chunks must survive; odd ones failed with a 429.
        assert "N0" in names
        assert "N2" in names
        assert all(not n.name.endswith(("1", "3", "5", "7", "9")) for n in result.nodes)

    def test_single_chunk_invoke_failure_yields_empty_result(self):
        g = _graph(chunk_size=100_000)  # short text -> single invoke() path
        g.data_extractor = _InvokeFails()

        result = g.parse("a short biography text")

        assert result.empty()


class TestTwoStageIsolation:
    """Two-stage extraction isolates node/edge batch failures."""

    def test_node_failure_skips_edge_llm_call(self):
        g = _graph(extraction_mode="two_stage")
        g.node_extractor = _FlakyBatch(
            lambda i: g.node_list_schema(items=[Entity(name=f"N{i}")])
        )
        edge_stub = _RecordingEdgeExtractor(lambda: g.edge_list_schema(items=[]))
        g.edge_extractor = edge_stub

        result = g.parse(LONG_TEXT)

        node_batches = g.node_extractor.batch_sizes
        assert node_batches and node_batches[0] >= 2  # multi-chunk run

        # Chunks are len(chunks); failed (odd) ones must not reach the LLM.
        num_chunks = node_batches[0]
        expected_edge_inputs = (num_chunks + 1) // 2  # even indices only
        assert len(edge_stub.seen_inputs) == expected_edge_inputs

        # Nodes from the successful chunks are still merged in.
        names = {n.name for n in result.nodes}
        assert "N0" in names

    def test_edge_batch_failure_degrades_to_nodes_only(self):
        g = _graph(extraction_mode="two_stage")
        g.node_extractor = _FlakyBatch(
            lambda i: g.node_list_schema(items=[Entity(name=f"N{i}")])
        )
        g.edge_extractor = _FlakyBatch(lambda i: g.edge_list_schema(items=[]))

        result = g.parse(LONG_TEXT)

        # Edges all failed (odd) or were empty (even), but nodes survive.
        names = {n.name for n in result.nodes}
        assert "N0" in names and "N2" in names


class TestHypergraphIsolation:
    """AutoHypergraph mirrors the graph-family isolation contract."""

    def test_one_stage_batch_failure_keeps_good_chunks(self):
        h = _hypergraph()
        h.data_extractor = _FlakyBatch(
            lambda i: h.graph_schema(
                nodes=[Entity(name=f"H{i}")],
                edges=[HyperRelation(participants=[f"H{i}"], relation_type="rel")],
            )
        )

        result = h.parse(LONG_TEXT)

        names = {n.name for n in result.nodes}
        assert "H0" in names and "H2" in names

    def test_two_stage_node_failure_skips_edge_llm_call(self):
        h = _hypergraph(extraction_mode="two_stage")
        h.node_extractor = _FlakyBatch(
            lambda i: h.node_list_schema(items=[Entity(name=f"H{i}")])
        )
        edge_stub = _RecordingEdgeExtractor(lambda: h.edge_list_schema(items=[]))
        h.edge_extractor = edge_stub

        result = h.parse(LONG_TEXT)

        num_chunks = h.node_extractor.batch_sizes[0]
        expected_edge_inputs = (num_chunks + 1) // 2
        assert len(edge_stub.seen_inputs) == expected_edge_inputs
        assert "H0" in {n.name for n in result.nodes}


class TestTemporalInjectionWithIsolation:
    """Spatiotemporal subclasses keep observation_time injection while isolating."""

    def _temporal_graph(self, extraction_mode="two_stage", chunk_size=64):
        g = AutoTemporalGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            time_in_edge_extractor=lambda x: "",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=MockChatModel(),
            embedder=MockEmbeddings(),
            observation_time="2026-09-01",
            extraction_mode=extraction_mode,
            chunk_size=chunk_size,
            chunk_overlap=16,
        )
        return g

    def test_two_stage_edge_inputs_keep_observation_time(self):
        g = self._temporal_graph()
        g.node_extractor = _FlakyBatch(
            lambda i: g.node_list_schema(items=[Entity(name=f"T{i}")])
        )
        edge_stub = _RecordingEdgeExtractor(lambda: g.edge_list_schema(items=[]))
        g.edge_extractor = edge_stub

        g.parse(LONG_TEXT)

        assert edge_stub.seen_inputs
        assert all(
            inp.get("observation_time") == "2026-09-01" for inp in edge_stub.seen_inputs
        )

    def test_one_stage_failure_survives_with_injection(self):
        g = self._temporal_graph(extraction_mode="one_stage")

        recorded = {}

        class _Probe:
            def invoke(self, inp, config=None):
                recorded.update(inp)
                raise ValueError("429")

            def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
                recorded.update(inputs[0])
                if return_exceptions:
                    return [ValueError("429")] * len(inputs)
                raise ValueError("429")

        g.data_extractor = _Probe()

        result = g.parse(LONG_TEXT)

        # Injection still happens on the failed call, and the run survives.
        assert recorded.get("observation_time") == "2026-09-01"
        assert result.empty()


class TestFailureLogging:
    """Failure logs carry chunk_index and never echo source text."""

    def test_batch_failure_logs_chunk_index_not_source_text(self):
        import logging

        class LogCapture(logging.Handler):
            def __init__(self):
                super().__init__()
                self.messages = []

            def emit(self, record):
                self.messages.append(self.format(record))

        handler = LogCapture()
        handler.setLevel(logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))
        # _batch_safe lives in base.py, so records come from that logger.
        logger = logging.getLogger("hyperextract.types.base")
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        try:
            g = _graph()
            g.data_extractor = _FlakyBatch(
                lambda i: g.graph_schema(nodes=[Entity(name=f"N{i}")], edges=[])
            )

            g.parse(LONG_TEXT)
        finally:
            logger.removeHandler(handler)

        # Failures identify the chunk (stub exception message carries the index,
        # structlog renders it via positional_args)...
        assert any(
            "chunk_extract_failed" in m and "429 rate limit on chunk 1" in m
            for m in handler.messages
        )
        # ...and never echo user content.
        assert all("sentence about entities" not in m for m in handler.messages)

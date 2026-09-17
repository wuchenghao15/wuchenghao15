"""Observation time/location must survive dump/load (not just live on the instance)."""

import json

from pydantic import BaseModel, Field

from hyperextract.methods.typical.atom import Atom
from hyperextract.types import (
    AutoSpatialGraph,
    AutoSpatioTemporalGraph,
    AutoTemporalGraph,
)
from tests.mocks import MockChatModel, MockEmbeddings


class Entity(BaseModel):
    name: str
    type: str = "ENTITY"
    properties: dict = Field(default_factory=dict)


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str


OBS_TIME = "2020-01-01"
OBS_LOCATION = "Beijing"


class _RecordingExtractor:
    """Edge-extractor stub that records batch inputs."""

    def __init__(self, empty_factory):
        self.seen_inputs: list[dict] = []
        self.empty_factory = empty_factory

    def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
        self.seen_inputs.extend(inputs)
        return [self.empty_factory() for _ in inputs]


def _assert_edge_inputs_carry(loaded, **expected):
    recorder = _RecordingExtractor(lambda: loaded.edge_list_schema(items=[]))
    loaded.edge_extractor = recorder
    nodes = loaded.node_list_schema(items=[Entity(name="Alice")])
    loaded._extract_edges_batch(["Alice met Bob yesterday."], [nodes])
    assert recorder.seen_inputs
    for key, value in expected.items():
        assert all(inp.get(key) == value for inp in recorder.seen_inputs)


def _graph_kwargs():
    return dict(
        node_schema=Entity,
        edge_schema=Relation,
        node_key_extractor=lambda x: x.name,
        edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        nodes_in_edge_extractor=lambda x: (x.source, x.target),
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
    )


def _assert_not_in_data_json(folder):
    data = json.loads((folder / "data.json").read_text(encoding="utf-8"))
    blob = json.dumps(data)
    assert "observation_time" not in blob
    assert "observation_location" not in blob


def test_temporal_graph_observation_time_roundtrip(tmp_path):
    original = AutoTemporalGraph(
        **_graph_kwargs(),
        time_in_edge_extractor=lambda x: "",
        observation_time=OBS_TIME,
    )
    dest = tmp_path / "temporal"
    original.dump(dest)

    meta = json.loads((dest / "metadata.json").read_text(encoding="utf-8"))
    assert meta["observation_time"] == OBS_TIME
    _assert_not_in_data_json(dest)

    loaded = AutoTemporalGraph(
        **_graph_kwargs(),
        time_in_edge_extractor=lambda x: "",
    )
    loaded.load(dest)

    assert loaded.observation_time == OBS_TIME
    assert loaded.metadata["observation_time"] == OBS_TIME
    _assert_edge_inputs_carry(loaded, observation_time=OBS_TIME)


def test_spatial_graph_observation_location_roundtrip(tmp_path):
    original = AutoSpatialGraph(
        **_graph_kwargs(),
        location_in_edge_extractor=lambda x: "",
        observation_location=OBS_LOCATION,
    )
    dest = tmp_path / "spatial"
    original.dump(dest)

    meta = json.loads((dest / "metadata.json").read_text(encoding="utf-8"))
    assert meta["observation_location"] == OBS_LOCATION
    _assert_not_in_data_json(dest)

    loaded = AutoSpatialGraph(
        **_graph_kwargs(),
        location_in_edge_extractor=lambda x: "",
    )
    loaded.load(dest)

    assert loaded.observation_location == OBS_LOCATION
    assert loaded.metadata["observation_location"] == OBS_LOCATION
    _assert_edge_inputs_carry(loaded, observation_location=OBS_LOCATION)


def test_spatio_temporal_graph_observation_roundtrip(tmp_path):
    original = AutoSpatioTemporalGraph(
        **_graph_kwargs(),
        time_in_edge_extractor=lambda x: "",
        location_in_edge_extractor=lambda x: "",
        observation_time=OBS_TIME,
        observation_location=OBS_LOCATION,
    )
    dest = tmp_path / "st"
    original.dump(dest)

    meta = json.loads((dest / "metadata.json").read_text(encoding="utf-8"))
    assert meta["observation_time"] == OBS_TIME
    assert meta["observation_location"] == OBS_LOCATION
    _assert_not_in_data_json(dest)

    loaded = AutoSpatioTemporalGraph(
        **_graph_kwargs(),
        time_in_edge_extractor=lambda x: "",
        location_in_edge_extractor=lambda x: "",
    )
    loaded.load(dest)

    assert loaded.observation_time == OBS_TIME
    assert loaded.observation_location == OBS_LOCATION
    _assert_edge_inputs_carry(
        loaded, observation_time=OBS_TIME, observation_location=OBS_LOCATION
    )


def test_atom_observation_time_roundtrip(tmp_path):
    original = Atom(
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
        observation_time=OBS_TIME,
    )
    dest = tmp_path / "atom"
    original.dump(dest)

    meta = json.loads((dest / "metadata.json").read_text(encoding="utf-8"))
    assert meta["observation_time"] == OBS_TIME
    _assert_not_in_data_json(dest)

    loaded = Atom(
        llm_client=MockChatModel(),
        embedder=MockEmbeddings(),
    )
    loaded.load(dest)

    assert loaded.observation_time == OBS_TIME
    assert loaded.metadata["observation_time"] == OBS_TIME

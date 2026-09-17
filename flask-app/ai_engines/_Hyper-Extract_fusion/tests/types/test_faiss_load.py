"""Tests for FAISS local-index load warnings on AutoModel and AutoList."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from hyperextract.types import AutoList, AutoModel
from hyperextract.types._faiss import _warned_index_paths
from tests.fixtures import PersonSchema

_FORBIDDEN_WARNING_SNIPPETS = (
    "malicious",
    "gadget",
    "construct",
    "payload",
    "exploit",
    "rce",
)


class PersonItemSchema(BaseModel):
    name: str
    age: int | None = None


@pytest.fixture(autouse=True)
def _reset_faiss_load_warnings():
    _warned_index_paths.clear()
    yield
    _warned_index_paths.clear()


def _assert_trusted_load_warning(caplog: pytest.LogCaptureFixture, folder) -> None:
    warning_text = " ".join(
        record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING
    )
    assert warning_text, "expected a warning when loading a local FAISS index"
    assert str(folder) in warning_text or folder.name in warning_text
    assert "deserializ" in warning_text.lower()
    assert "trust" in warning_text.lower()
    lowered = warning_text.lower()
    for snippet in _FORBIDDEN_WARNING_SNIPPETS:
        assert snippet not in lowered


def _assert_dangerous_deserialization_enabled(mock_load_local: MagicMock) -> None:
    mock_load_local.assert_called_once()
    _, kwargs = mock_load_local.call_args
    assert kwargs.get("allow_dangerous_deserialization") is True


class TestAutoModelFaissLoad:
    @patch("hyperextract.types.model.FAISS.load_local")
    def test_load_index_warns_and_keeps_deserialization_flag(
        self, mock_load_local, llm_client, embedder, tmp_path, caplog
    ):
        mock_load_local.return_value = MagicMock(name="faiss_index")
        folder = tmp_path / "model-index"
        folder.mkdir()

        model = AutoModel(
            data_schema=PersonSchema,
            llm_client=llm_client,
            embedder=embedder,
        )

        with caplog.at_level(logging.WARNING, logger="hyperextract.types._faiss"):
            model.load_index(folder)

        _assert_dangerous_deserialization_enabled(mock_load_local)
        assert mock_load_local.call_args.args[0] == str(folder)
        assert mock_load_local.call_args.args[1] is embedder
        assert model._index is mock_load_local.return_value
        _assert_trusted_load_warning(caplog, folder)

    @patch("hyperextract.types.model.FAISS.load_local")
    def test_load_index_warns_once_per_path(
        self, mock_load_local, llm_client, embedder, tmp_path, caplog
    ):
        mock_load_local.return_value = MagicMock(name="faiss_index")
        folder = tmp_path / "model-index"
        folder.mkdir()
        model = AutoModel(
            data_schema=PersonSchema,
            llm_client=llm_client,
            embedder=embedder,
        )

        with caplog.at_level(logging.WARNING, logger="hyperextract.types._faiss"):
            model.load_index(folder)
            model.load_index(folder)

        warning_records = [
            record
            for record in caplog.records
            if record.levelno >= logging.WARNING and "FAISS" in record.getMessage()
        ]
        assert len(warning_records) == 1
        assert mock_load_local.call_count == 2


class TestAutoListFaissLoad:
    @patch("hyperextract.types.list.FAISS.load_local")
    def test_load_index_warns_and_keeps_deserialization_flag(
        self, mock_load_local, llm_client, embedder, tmp_path, caplog
    ):
        mock_load_local.return_value = MagicMock(name="faiss_index")
        folder = tmp_path / "list-index"
        folder.mkdir()

        auto_list = AutoList(
            item_schema=PersonItemSchema,
            llm_client=llm_client,
            embedder=embedder,
        )

        with caplog.at_level(logging.WARNING, logger="hyperextract.types._faiss"):
            auto_list.load_index(folder)

        _assert_dangerous_deserialization_enabled(mock_load_local)
        assert mock_load_local.call_args.args[0] == str(folder)
        assert mock_load_local.call_args.args[1] is embedder
        assert auto_list._index is mock_load_local.return_value
        _assert_trusted_load_warning(caplog, folder)

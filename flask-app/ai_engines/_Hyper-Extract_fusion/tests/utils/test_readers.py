"""Unit tests for hyperextract.utils.readers (document input layer)."""

from pathlib import Path

import pytest

from hyperextract.utils import readers
from hyperextract.utils.readers import (
    INGESTABLE_SUFFIXES,
    TEXT_SUFFIXES,
    ReaderError,
    convert_document,
    markitdown_available,
    read_document,
    read_text_with_fallback,
    supported_suffixes,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "documents"

requires_markitdown = pytest.mark.skipif(
    not markitdown_available(), reason="markitdown not installed"
)


class TestSuffixSets:
    def test_text_suffixes_always_supported(self):
        assert {".txt", ".md"} <= supported_suffixes()

    def test_ingestable_suffixes_require_backend(self):
        if markitdown_available():
            assert ".pdf" in supported_suffixes()
        else:
            assert ".pdf" not in supported_suffixes()
            assert ".pdf" in INGESTABLE_SUFFIXES

    def test_text_suffixes_not_in_ingestable(self):
        assert not TEXT_SUFFIXES & set(INGESTABLE_SUFFIXES)


class TestTextReading:
    def test_utf8(self, tmp_path):
        f = tmp_path / "note.md"
        f.write_text("hello 你好", encoding="utf-8")
        assert read_text_with_fallback(f) == "hello 你好"

    def test_non_utf8_fallback(self, tmp_path):
        f = tmp_path / "note.txt"
        # Long enough for charset-normalizer to reach a confident verdict.
        f.write_bytes(("这是一段用于编码检测的中文正文内容。" * 20).encode("gbk"))
        text = read_text_with_fallback(f)
        assert "这是一段用于编码检测的中文正文内容" in text

    def test_dispatch_to_text_reader(self, tmp_path):
        f = tmp_path / "note.md"
        f.write_text("body", encoding="utf-8")
        assert read_document(f) == "body"


class TestDocumentConversion:
    @requires_markitdown
    def test_html(self):
        text = convert_document(FIXTURES / "sample.html")
        assert "Hello Hyper Extract" in text

    @requires_markitdown
    def test_pdf(self):
        text = convert_document(FIXTURES / "sample.pdf")
        assert "Hello Hyper Extract from PDF" in text

    @requires_markitdown
    def test_docx(self):
        text = convert_document(FIXTURES / "sample.docx")
        assert "Hello Hyper Extract from DOCX" in text

    @requires_markitdown
    def test_xlsx(self):
        text = convert_document(FIXTURES / "sample.xlsx")
        assert "Hello Hyper Extract from XLSX" in text

    @requires_markitdown
    def test_textless_pdf_reports_scanned(self):
        with pytest.raises(ReaderError, match="scanned|OCR"):
            convert_document(FIXTURES / "blank.pdf")

    @requires_markitdown
    def test_read_document_dispatches_pdf(self):
        assert "PDF" in read_document(FIXTURES / "sample.pdf")

    def test_backend_missing_hint(self, tmp_path, monkeypatch):
        monkeypatch.setattr(readers, "markitdown_available", lambda: False)
        fake = tmp_path / "doc.pdf"
        fake.write_bytes(b"%PDF-1.4 fake")
        with pytest.raises(ReaderError, match=r"hyperextract\[ingest\]"):
            convert_document(fake)


class TestUnsupported:
    def test_unsupported_suffix_raises(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x00\x01")
        with pytest.raises(ReaderError, match="Unsupported"):
            read_document(f)

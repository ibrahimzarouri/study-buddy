import io

import pytest

from tools.document_loader import load_document
from tools.rag import chunk_text


class TestChunkText:
    def test_short_text_single_chunk(self):
        assert chunk_text("hello world") == ["hello world"]

    def test_empty_text_no_chunks(self):
        assert chunk_text("") == []

    def test_chunks_respect_size(self):
        text = "abcdefghij" * 200  # 2000 chars
        chunks = chunk_text(text, size=600, overlap=80)
        assert all(len(c) <= 600 for c in chunks)
        assert len(chunks) >= 3

    def test_consecutive_chunks_overlap(self):
        text = "abcdefghij" * 200
        chunks = chunk_text(text, size=600, overlap=80)
        assert chunks[0][-80:] == chunks[1][:80]

    def test_collapses_excess_blank_lines(self):
        assert chunk_text("para1\n\n\n\n\npara2") == ["para1\n\npara2"]


class TestLoadDocument:
    def test_txt_file(self):
        f = io.BytesIO("Hallo Netzwerksicherheit".encode("utf-8"))
        assert load_document(f, "notes.txt") == "Hallo Netzwerksicherheit"

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_document(io.BytesIO(b"x"), "slides.pptx")

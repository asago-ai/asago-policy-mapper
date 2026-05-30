from pathlib import Path
import tempfile

from concorde_policy_mapper.extract.parse import (
    ParsedDocument,
    Chunk,
    parse_document,
    chunk_documents,
)


def test_parsed_document_fields():
    doc = ParsedDocument(source="test.md", content="hello world", doc=None)
    assert doc.source == "test.md"
    assert doc.content == "hello world"
    assert doc.doc is None


def test_chunk_fields():
    chunk = Chunk(text="some text", source="test.md", index=0)
    assert chunk.text == "some text"
    assert chunk.index == 0


def test_parse_plain_text():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("This is a plain text policy document.\nIt has multiple lines.")
        f.flush()
        result = parse_document(Path(f.name))
    assert "plain text policy document" in result.content
    assert result.doc is None
    assert result.source == f.name


def test_parse_markdown():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write("# Policy\n\nThis is a markdown policy with enough words to pass the minimum threshold for docling conversion output.")
        f.flush()
        result = parse_document(Path(f.name))
    assert "Policy" in result.content
    assert result.doc is not None


def test_chunk_plain_text_documents():
    docs = [
        ParsedDocument(source="a.txt", content="Short document.", doc=None),
        ParsedDocument(source="b.txt", content="Another short document.", doc=None),
    ]
    chunks = chunk_documents(docs)
    assert len(chunks) == 2
    assert chunks[0].source == "a.txt"
    assert chunks[0].index == 0
    assert chunks[1].source == "b.txt"
    assert chunks[1].index == 0


def test_chunk_preserves_content():
    content = "A " * 500
    docs = [ParsedDocument(source="big.txt", content=content, doc=None)]
    chunks = chunk_documents(docs)
    assert len(chunks) >= 1
    joined = " ".join(c.text for c in chunks)
    assert "A" in joined


def test_chunk_has_provenance_fields():
    chunk = Chunk(
        text="Some policy text.",
        source="policy.pdf",
        index=0,
        page=3,
        section="Section 4: Oversight",
    )
    assert chunk.page == 3
    assert chunk.section == "Section 4: Oversight"


def test_chunk_provenance_defaults_to_none():
    chunk = Chunk(text="Text.", source="doc.md", index=0)
    assert chunk.page is None
    assert chunk.section is None

from unittest.mock import MagicMock

from asago_policy_mapper.extract.models import RetrievalConfig
from asago_policy_mapper.extract.parse import Chunk, ParsedDocument, chunk_documents
from asago_policy_mapper.extract.querygen import (
    ChunkGroup,
    GeneratedQueries,
    generate_queries,
    group_chunks,
)


def test_retrieval_config_query_gen_default_true():
    rc = RetrievalConfig()
    assert rc.query_gen is True
    assert rc.grounding_batch_size == 15


def test_retrieval_config_query_gen_in_metadata():
    rc = RetrievalConfig(query_gen=True)
    meta = rc.to_metadata()
    assert meta["query_gen"] is True


def test_retrieval_config_query_gen_false_in_metadata():
    rc = RetrievalConfig(query_gen=False)
    meta = rc.to_metadata()
    assert meta["query_gen"] is False


def test_group_chunks_by_section():
    chunks = [
        Chunk(text="a", source="doc.pdf", index=0, section="Intro"),
        Chunk(text="b", source="doc.pdf", index=1, section="Intro"),
        Chunk(text="c", source="doc.pdf", index=2, section="Privacy"),
        Chunk(text="d", source="doc.pdf", index=3, section="Privacy"),
        Chunk(text="e", source="doc.pdf", index=4, section="Privacy"),
    ]
    groups = group_chunks(chunks)
    assert len(groups) == 2
    assert groups[0] == ChunkGroup(chunk_indices=[0, 1], section="Intro")
    assert groups[1] == ChunkGroup(chunk_indices=[2, 3, 4], section="Privacy")


def test_group_chunks_size_cap_splits():
    chunks = [Chunk(text=f"chunk {i}", source="doc.pdf", index=i, section="Big") for i in range(8)]
    groups = group_chunks(chunks, max_group_size=3)
    assert len(groups) == 3
    assert groups[0].chunk_indices == [0, 1, 2]
    assert groups[1].chunk_indices == [3, 4, 5]
    assert groups[2].chunk_indices == [6, 7]
    assert all(g.section == "Big" for g in groups)


def test_group_chunks_none_merges_into_previous():
    chunks = [
        Chunk(text="a", source="doc.pdf", index=0, section="Intro"),
        Chunk(text="b", source="doc.pdf", index=1, section=None),
        Chunk(text="c", source="doc.pdf", index=2, section=None),
    ]
    groups = group_chunks(chunks)
    assert len(groups) == 1
    assert groups[0].chunk_indices == [0, 1, 2]
    assert groups[0].section == "Intro"


def test_group_chunks_none_at_start():
    chunks = [
        Chunk(text="a", source="doc.pdf", index=0, section=None),
        Chunk(text="b", source="doc.pdf", index=1, section=None),
        Chunk(text="c", source="doc.pdf", index=2, section="Privacy"),
    ]
    groups = group_chunks(chunks)
    assert len(groups) == 2
    assert groups[0].chunk_indices == [0, 1]
    assert groups[0].section is None
    assert groups[1].chunk_indices == [2]


def test_group_chunks_all_none_degrades_to_windows():
    chunks = [Chunk(text=f"chunk {i}", source="doc.pdf", index=i, section=None) for i in range(7)]
    groups = group_chunks(chunks, max_group_size=3)
    assert len(groups) == 3
    assert groups[0].chunk_indices == [0, 1, 2]
    assert groups[1].chunk_indices == [3, 4, 5]
    assert groups[2].chunk_indices == [6]


def test_group_chunks_non_overlapping():
    chunks = [
        Chunk(text="a", source="doc.pdf", index=0, section="A"),
        Chunk(text="b", source="doc.pdf", index=1, section=None),
        Chunk(text="c", source="doc.pdf", index=2, section="B"),
        Chunk(text="d", source="doc.pdf", index=3, section="B"),
        Chunk(text="e", source="doc.pdf", index=4, section=None),
    ]
    groups = group_chunks(chunks)
    all_indices = []
    for g in groups:
        all_indices.extend(g.chunk_indices)
    assert sorted(all_indices) == [0, 1, 2, 3, 4]
    assert len(all_indices) == len(set(all_indices))


def test_group_chunks_single_chunk():
    chunks = [Chunk(text="only", source="doc.pdf", index=0, section="Solo")]
    groups = group_chunks(chunks)
    assert len(groups) == 1
    assert groups[0].chunk_indices == [0]


def test_group_chunks_empty():
    groups = group_chunks([])
    assert groups == []


def test_group_chunks_none_merges_respects_size_cap():
    chunks = [Chunk(text=f"chunk {i}", source="doc.pdf", index=i, section="A") for i in range(4)] + [
        Chunk(text="null chunk", source="doc.pdf", index=4, section=None),
    ]
    groups = group_chunks(chunks, max_group_size=3)
    # Section "A" splits into [0,1,2] and [3]. None merges into [3] -> [3,4]
    assert groups[0].chunk_indices == [0, 1, 2]
    assert groups[1].chunk_indices == [3, 4]


def _make_mock_client(queries_per_call):
    """Build a mock instructor client that returns GeneratedQueries."""
    client = MagicMock()

    def fake_create(**kwargs):
        return GeneratedQueries(queries=queries_per_call.pop(0))

    client.chat.completions.create = MagicMock(side_effect=fake_create)
    return client


def test_generate_queries_basic():
    chunks = [
        Chunk(text="AI systems must not discriminate.", source="doc.pdf", index=0, section="Bias"),
        Chunk(text="Protected groups need equal treatment.", source="doc.pdf", index=1, section="Bias"),
    ]
    groups = [ChunkGroup(chunk_indices=[0, 1], section="Bias")]
    client = _make_mock_client(
        [
            ["Unfair treatment in AI decisions based on protected characteristics"],
        ]
    )

    results = generate_queries(chunks, groups, client, "test-model")

    assert len(results) == 1
    assert results[0].query == "Unfair treatment in AI decisions based on protected characteristics"
    assert results[0].chunk_indices == [0, 1]
    assert results[0].section == "Bias"


def test_generate_queries_empty_list_skips_group():
    chunks = [
        Chunk(text="Table of contents page 1", source="doc.pdf", index=0, section="TOC"),
    ]
    groups = [ChunkGroup(chunk_indices=[0], section="TOC")]
    client = _make_mock_client([[]])

    results = generate_queries(chunks, groups, client, "test-model")

    assert results == []


def test_generate_queries_multiple_groups():
    chunks = [
        Chunk(text="privacy concern", source="doc.pdf", index=0, section="A"),
        Chunk(text="security concern", source="doc.pdf", index=1, section="B"),
    ]
    groups = [
        ChunkGroup(chunk_indices=[0], section="A"),
        ChunkGroup(chunk_indices=[1], section="B"),
    ]
    client = _make_mock_client(
        [
            ["data privacy in AI training"],
            ["adversarial attacks on AI systems"],
        ]
    )

    results = generate_queries(chunks, groups, client, "test-model")

    assert len(results) == 2
    assert results[0].chunk_indices == [0]
    assert results[1].chunk_indices == [1]


def test_generate_queries_records_llm_calls():
    chunks = [
        Chunk(text="AI bias text", source="doc.pdf", index=0, section="Bias"),
    ]
    groups = [ChunkGroup(chunk_indices=[0], section="Bias")]
    client = _make_mock_client([["bias query"]])
    call_collector = []

    generate_queries(chunks, groups, client, "test-model", call_collector=call_collector)

    assert len(call_collector) == 1
    assert call_collector[0].stage == "query_gen"


def test_generate_queries_fallback_on_failure():
    chunks = [
        Chunk(text="Privacy concerns in AI", source="doc.pdf", index=0, section="A"),
        Chunk(text="Security risks in ML", source="doc.pdf", index=1, section="B"),
    ]
    groups = [
        ChunkGroup(chunk_indices=[0], section="A"),
        ChunkGroup(chunk_indices=[1], section="B"),
    ]

    def fail_group_a(**kwargs):
        # Determine which group by inspecting the message content
        msgs = kwargs.get("messages", [])
        text = "".join(m.get("content", "") for m in msgs if isinstance(m, dict))
        if "Privacy concerns" in text:
            raise Exception("LLM timeout")
        return GeneratedQueries(queries=["query for B"])

    client = MagicMock()
    client.chat.completions.create = MagicMock(side_effect=fail_group_a)

    results, fallback_indices = generate_queries(chunks, groups, client, "test-model", return_fallbacks=True)

    assert len(results) == 1
    assert results[0].chunk_indices == [1]
    assert fallback_indices == [0]


def _make_prompt_echo_client():
    """Return a client whose query names the document markers found in the prompt."""
    client = MagicMock()

    def fake_create(**kwargs):
        text = "".join(m.get("content", "") for m in kwargs["messages"] if isinstance(m, dict))
        markers = sorted(m for m in ("ALPHA", "BETA") if m in text)
        return GeneratedQueries(queries=["+".join(markers)])

    client.chat.completions.create = MagicMock(side_effect=fake_create)
    return client


def _two_document_chunks():
    # Per-document Chunk.index values restart at 0, as chunk_documents produces them.
    return [
        Chunk(text="ALPHA first passage", source="alpha.pdf", index=0, section="Governance"),
        Chunk(text="ALPHA second passage", source="alpha.pdf", index=1, section="Governance"),
        Chunk(text="BETA first passage", source="beta.pdf", index=0, section="Privacy"),
        Chunk(text="BETA second passage", source="beta.pdf", index=1, section="Privacy"),
    ]


def test_generate_queries_multi_document_reads_each_groups_own_text():
    chunks = _two_document_chunks()
    client = _make_prompt_echo_client()

    results = generate_queries(chunks, group_chunks(chunks), client, "test-model")

    by_section = {r.section: r for r in results}
    assert by_section["Governance"].query == "ALPHA"
    assert by_section["Privacy"].query == "BETA"


def test_multi_document_chunk_indices_are_merged_list_positions():
    chunks = _two_document_chunks()
    client = _make_prompt_echo_client()

    results = generate_queries(chunks, group_chunks(chunks), client, "test-model")

    by_section = {r.section: r for r in results}
    assert by_section["Governance"].chunk_indices == [0, 1]
    assert by_section["Privacy"].chunk_indices == [2, 3]
    for r in results:
        assert {chunks[i].section for i in r.chunk_indices} == {r.section}
        assert len({chunks[i].source for i in r.chunk_indices}) == 1


def test_group_chunks_does_not_span_documents_with_same_section_name():
    chunks = [
        Chunk(text="ALPHA intro", source="alpha.pdf", index=0, section="Overview"),
        Chunk(text="BETA intro", source="beta.pdf", index=0, section="Overview"),
        Chunk(text="BETA untitled continuation", source="beta.pdf", index=1, section=None),
    ]

    groups = group_chunks(chunks)

    assert [g.chunk_indices for g in groups] == [[0], [1, 2]]


def test_group_chunks_unsectioned_start_of_next_document_opens_new_group():
    chunks = [
        Chunk(text="ALPHA body", source="alpha.pdf", index=0, section="Governance"),
        Chunk(text="BETA preamble", source="beta.pdf", index=0, section=None),
    ]

    groups = group_chunks(chunks)

    assert [g.chunk_indices for g in groups] == [[0], [1]]
    assert groups[1].section is None


def test_multi_document_query_gen_from_chunk_documents_resolves_own_text():
    docs = [
        ParsedDocument(source="alpha.txt", content="ALPHA policy text about governance.", doc=None),
        ParsedDocument(source="beta.txt", content="BETA policy text about privacy.", doc=None),
    ]
    chunks = chunk_documents(docs)
    client = _make_prompt_echo_client()

    results = generate_queries(chunks, group_chunks(chunks), client, "test-model")

    assert len(results) == 2
    for r in results:
        sources = {chunks[i].source for i in r.chunk_indices}
        assert len(sources) == 1
        marker = "ALPHA" if sources == {"alpha.txt"} else "BETA"
        assert r.query == marker

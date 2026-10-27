import json

import pytest

from knowledge.answers.citations import (
    CitationTextDecoder, alias_grounding, citation_aliases, decode_citation_deltas,
)
from knowledge.integrations.providers import ProviderDelta


def retrieval():
    return {"hits": [{"passageId": "original-a"}], "grounding": {
        "passages": [
            {"id": "psg_12345678901234567890123456789012", "passageId": "psg_12345678901234567890123456789012",
             "sourceRevisionId": "rev-a", "text": "250°C의 조건", "documentForm": "text_extraction"},
            {"passageId": "psg_abcdefghijklmnopqrstuvwxyz123456", "sourceRevisionId": "rev-b", "text": "결과"}],
        "relations": [{"id": "relation-a", "summary": "관련 설명", "evidenceRefs": [
            {"passageId": "psg_abcdefghijklmnopqrstuvwxyz123456", "sourceRevisionId": "rev-b"}]}],
        "sourceViews": [{"sourceRevisionId": "rev-a", "evidenceRefs": [
            {"passageId": "psg_12345678901234567890123456789012", "sourceRevisionId": "rev-a"}]}]}}


def test_prompt_aliases_preserve_original_sources_and_link_relation_evidence():
    original = retrieval()
    before = json.dumps(original, ensure_ascii=False, sort_keys=True)
    mapping = citation_aliases(original)
    assert mapping == {"E1": "psg_12345678901234567890123456789012", "E2": "psg_abcdefghijklmnopqrstuvwxyz123456"}
    prompt = alias_grounding(original)
    assert [p["id"] for p in prompt["passages"]] == ["E1", "E2"]
    assert prompt["relations"][0]["evidenceRefs"] == [{"id": "E2"}]
    assert prompt["sourceViews"][0]["evidenceRefs"] == [{"id": "E1"}]
    assert "sourceRevisionId" not in json.dumps(prompt)
    assert "passageId" not in json.dumps(prompt)
    assert json.dumps(original, ensure_ascii=False, sort_keys=True) == before


def test_aliases_share_duplicates_and_reject_unavailable_relation_evidence():
    value = retrieval()
    value["grounding"]["passages"].append(value["grounding"]["passages"][0].copy())
    assert len(citation_aliases(value)) == 2
    value["grounding"]["relations"][0]["evidenceRefs"][0]["passageId"] = "not-in-grounding"
    with pytest.raises(ValueError, match="outside"):
        alias_grounding(value)


def test_relation_references_use_the_passage_alias_even_when_citation_id_differs():
    value = retrieval()
    value["grounding"]["passages"][1]["id"] = "citation-b"
    assert citation_aliases(value)["E2"] == "citation-b"
    assert alias_grounding(value)["relations"][0]["evidenceRefs"] == [{"id": "E2"}]


@pytest.mark.parametrize("split", range(1, 55))
def test_citation_restoration_handles_every_delta_boundary_without_touching_other_text(split):
    text = "E1 기술 [E1] [다른 문법] 값 [출처: E1, E2; E999] 뒤"
    decoder = CitationTextDecoder({"E1": "actual-one", "E2": "actual-two"})
    decoded = decoder.feed(text[:split]) + decoder.feed(text[split:]) + decoder.finish()
    assert decoded == "E1 기술 [E1] [다른 문법] 값 [출처: actual-one, actual-two; E999] 뒤"
    assert decoder.unknown_references == {"E999"}


def test_stream_buffer_is_bounded_and_finish_preserves_incomplete_text():
    decoder = CitationTextDecoder({"E1": "source"})
    assert decoder.feed("설명 즉시 ") == "설명 즉시 "
    assert decoder.feed("E1 [다른 문법] " * 1000) == "E1 [다른 문법] " * 1000
    assert decoder.feed("[출처: E") == ""
    assert decoder.finish() == "[출처: E"
    assert decoder.finish() == ""
    oversized = "[출처: " + "가" * 1000
    assert decoder.feed(oversized) == oversized
    assert decoder.finish() == ""
    assert decoder.feed("[출처: E1]") == "[출처: source]"


def test_one_character_deltas_restore_multiple_citations_with_whitespace():
    decoder = CitationTextDecoder({"E1": "first", "E2": "second"})
    text = "앞 [출처 : E1; E2] 중간 [출처: E1] 뒤"
    output = []
    for character in text:
        output.append(decoder.feed(character))
        assert len(decoder._pending.encode("utf-8")) <= 2048
    assert "".join(output) + decoder.finish() == "앞 [출처 : first; second] 중간 [출처: first] 뒤"


def test_existing_exact_source_ids_are_valid_but_other_tokens_are_not_guessed():
    decoder = CitationTextDecoder({"E1": "actual-one"})
    assert decoder.feed("[출처 : actual-one; E01, E1x, E1 and E2]") == "[출처 : actual-one; E01, E1x, E1 and E2]"
    assert decoder.unknown_references == {"E01", "E1x", "E1 and E2"}


@pytest.mark.asyncio
async def test_delta_wrapper_keeps_usage_model_and_event_metadata_and_flushes_pending():
    usage = {"costUsd": .01, "outputTokens": 10}
    parts = [ProviderDelta(text="조건 [출", model="model", provider_event_type="delta"),
             ProviderDelta(text="처: E1]", model="model", provider_event_type="delta"),
             ProviderDelta(text=" 끝 [출처: E", usage=usage, model="returned-model", provider_event_type="completed")]

    async def stream():
        for part in parts:
            yield part

    source = retrieval()
    decoder = CitationTextDecoder(citation_aliases(source))
    decoded = [part async for part in decode_citation_deltas(stream(), source, decoder=decoder)]
    assert "".join(part.text for part in decoded) == "조건 [출처: psg_12345678901234567890123456789012] 끝 [출처: E"
    assert len(decoded) == 4
    for before, after in zip(parts, decoded):
        assert after.usage is before.usage
        assert after.model == before.model and after.provider_event_type == before.provider_event_type
    assert decoded[-1] == ProviderDelta(text="[출처: E")

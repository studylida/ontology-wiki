import json

import pytest

from knowledge.rag.grounding import compose_grounding, encoded
from knowledge.rag.dto import AnswerRequest
from knowledge.answers.prompt import build_messages
from knowledge.answers.citations import alias_grounding


def test_relation_and_source_view_evidence_share_one_deduplicated_budget():
    hits = [{"id": f"p{i}", "passageId": f"p{i}", "sourceRevisionId": f"r{i}", "title": "테스트 원문",
             "locator": "조건", "text": "조건을 가진 원문 근거. " * 80, "excerpt": "조건을 가진 원문 근거. " * 80}
            for i in range(20)]
    relations = [{"id": f"rel{i}", "fromConceptId": "A", "toConceptId": f"B{i}", "type": "alternative_to",
                  "summary": "특정 조건에서의 대안", "conditions": "온도와 장비가 같은 경우", "evidence": [hits[i], hits[i + 1]]}
                 for i in range(12)]
    views = [{"id": f"view{i}", "conceptId": "A", "sourceRevisionId": f"r{i}", "summary": "작성자의 해석", "documentForm": "edited_derivative",
              "conditions": "문헌에 명시된 범위", "evidence": [hits[i]]} for i in range(16)]
    selected, grounding, stats = compose_grounding(hits[:4], relations, views, 12000)
    assert len(encoded(grounding)) <= 12000
    assert len({h["passageId"] for h in selected}) == len(selected)
    assert any("relation_evidence" in hit.get("methods", []) for hit in selected)
    assert stats["relations"] > 0 or stats["sourceViews"] > 0
    assert all(view["documentForm"] == "edited_derivative" for view in grounding["sourceViews"])
    assert all("evidence" not in card for card in grounding["relations"] + grounding["sourceViews"])
    ids = {hit["passageId"] for hit in selected}
    assert all(ref["passageId"] in ids for card in grounding["relations"] + grounding["sourceViews"] for ref in card["evidenceRefs"])


def test_total_prompt_bound_keeps_latest_history_without_extra_model_calls():
    request = AnswerRequest(clientRequestId="budget", message="a" * 20000)
    retrieval = {"grounding": {"passages": [{"text": "e" * 18000}], "relations": [], "sourceViews": []},
                 "warnings": [], "groupCoverage": [], "requirementCoverage": []}
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i) + "h" * 5999} for i in range(8)]
    messages = build_messages(request, retrieval, history, max_characters=50000)
    assert sum(len(m["content"]) for m in messages) <= 50000
    assert messages[-2]["content"].startswith("7")
    assert len(messages) < len(history) + 2


@pytest.mark.parametrize("mode", ["wiki", "analysis"])
@pytest.mark.parametrize("question", ["열압착 본딩의 원리와 적용 조건을 설명해 주세요.", "각 자료의 해석과 출처를 비교해 주세요."])
def test_readable_answer_prompt_preserves_question_and_source_provenance(mode, question):
    request = AnswerRequest(clientRequestId="source-contract", message=question, responseMode=mode)
    evidence = {"passages": [{"id": "p1", "passageId": "p1", "sourceRevisionId": "r1", "documentForm": "text_extraction",
                             "title": "원문 제목", "author": "원문 저자", "locator": "페이지 4 표 2", "text": "시편 A의 조건과 측정 결과"}],
                "relations": [], "sourceViews": []}
    retrieval = {"grounding": evidence, "warnings": [], "groupCoverage": [], "requirementCoverage": []}
    messages = build_messages(request, retrieval, [])
    assert [message["role"] for message in messages] == ["system", "user"]
    user_question, payload = messages[-1]["content"].split("\n\nEVIDENCE_JSON\n", 1)
    evidence_text, coverage_text = payload.split("\nCOVERAGE_JSON\n", 1)
    assert user_question == question
    assert json.loads(evidence_text) == alias_grounding(retrieval)
    assert json.loads(evidence_text)["passages"][0]["id"] == "E1"
    assert evidence["passages"][0]["id"] == "p1"
    assert json.loads(coverage_text) == {"groups": []}


def test_ranked_direct_evidence_has_priority_over_graph_expansion():
    hits = [{"id": f"p{i}", "passageId": f"p{i}", "sourceRevisionId": f"r{i}", "text": "검색 근거 " * 50}
            for i in range(3)]
    graph = [{"id": f"g{i}", "passageId": f"g{i}", "sourceRevisionId": f"gr{i}", "excerpt": "관계 근거 " * 50}
             for i in range(6)]
    views = [{"id": f"v{i}", "conceptId": "c", "sourceRevisionId": g["sourceRevisionId"], "evidence": [g]}
             for i, g in enumerate(graph)]
    selected, grounding, _ = compose_grounding(hits, [], views, 2600)
    assert [hit["passageId"] for hit in selected[:3]] == ["p0", "p1", "p2"]
    assert len(encoded(grounding)) <= 2600


def test_source_discrepancy_is_called_out_using_only_included_citation_aliases():
    request = AnswerRequest(clientRequestId="discrepancy", message="실험 조건은?")
    evidence = {"passages": [
        {"id": "p1", "passageId": "p1", "sourceRevisionId": "r1", "text": "측정 결과"},
        {"id": "p2", "passageId": "p2", "sourceRevisionId": "r1", "text": "원문 내부 유량 불일치: 20 sccm, 50 sccm"}],
        "relations": [], "sourceViews": []}
    content = build_messages(request, {"grounding": evidence}, [])[-1]["content"]
    assert "수치 대조가 필요한 근거: E2" in content
    assert "서로 다른 실험이면 구분" in content
    assert "수치 대조가 필요한 근거" not in build_messages(request, {"grounding": {"passages": evidence["passages"][:1]}}, [])[-1]["content"]


def test_graph_does_not_shrink_budget_for_direct_search_passages():
    hits = [{"id": f"p{i}", "passageId": f"p{i}", "sourceRevisionId": f"r{i}", "text": "a" * 300} for i in range(4)]
    reference = {"id": "g", "passageId": "g", "sourceRevisionId": "gr", "excerpt": "b" * 300}
    views = [{"id": "v", "conceptId": "c", "sourceRevisionId": "gr", "evidence": [reference]}]
    selected, grounding, _ = compose_grounding(hits, [], views, 1800)
    assert [hit["passageId"] for hit in selected[:4]] == ["p0", "p1", "p2", "p3"]
    assert all(not hit.get("contextTruncated") for hit in selected[:4])
    assert len(encoded(grounding)) <= 1800

"""Small, inspectable internal exploration plan; no LLM or external search call.

Literal aspect signals are candidate coverage, never a semantic truth/sufficiency
score. Unknown items remain unknown in the answer context and audit record.
"""
import re


ASPECTS = (
    ("definition", "정의", r"정의|의미|무엇|뭐|개념|definition|defined|refers to"),
    ("purpose", "목적", r"목적|왜|필요|용도|purpose|used for"),
    ("principle", "원리", r"원리|작동|동작|기전|메커니즘|principle|mechanism|operates"),
    ("path", "경로와 구조", r"경로|\bpath\b|\broute\b"),
    ("delay", "지연 특성", r"지연|\bdelay\b|\blatency\b"),
    ("conditions", "적용 조건", r"조건|환경|경우|상황|적용|공정창|condition|when|under"),
    ("limits", "한계", r"한계|단점|제약|실패|어려움|limit|drawback|constraint|failure"),
    ("alternatives", "대안", r"대안|대체|대신|alternative|instead"),
    ("sequence", "절차와 순서", r"순서|절차|선행|후속|단계|sequence|before|after|step"),
    ("comparison", "비교 조건과 차이", r"비교|차이|versus|\bvs\b|comparison|difference"),
    ("examples", "사례", r"사례|예시|example|case study"),
)

# Concrete parameters in the question take priority over broad words such as
# "conditions". These rules choose search queries; they do not verify values.
PARAMETERS = (
    ("power", "소비 전력·비트당 에너지의 수치와 측정·비교 조건", r"전력|소비.?에너지|비트당.?에너지|\bpower\b|\benergy\b"),
    ("temperature", "온도 조건·수치와 측정 범위", r"온도|\btemperatures?\b"),
    ("pressure", "압력 조건·수치와 측정 범위", r"압력|\bpressures?\b"),
    ("warpage", "휨의 허용치·측정 조건", r"휨|\bwarpage\b"),
    ("yield", "수율의 값·정의·비교 조건", r"수율|\byield\b"),
    ("thickness", "두께·치수의 값과 허용 범위", r"두께|치수|\bthickness\b|\bdimensions?\b"),
    ("duration", "시간·기간과 공정 조건", r"유지 시간|가압 시간|공정 시간|\bduration\b|\bdwell time\b"),
)


def plan_requirements(message, aspect=None):
    matched = [{"id": key, "aspect": label, "pattern": pattern} for key, label, pattern in PARAMETERS + ASPECTS
               if re.search(pattern, message, re.I)]
    if aspect:
        known = next((row for row in ASPECTS if aspect in (row[0], row[1])), None)
        item = {"id": known[0] if known else "explicit_aspect", "aspect": aspect,
                "pattern": known[2] if known else re.escape(aspect)}
        if not any(row["id"] == item["id"] for row in matched):
            matched.insert(0, item)
    if not matched:
        # Explicit V1 heuristic for a broad, unstructured Korean/English question.
        matched = [{"id": row[0], "aspect": row[1], "pattern": row[2]} for row in ASPECTS
                   if row[0] in ("definition", "conditions")]
    for item in matched:
        item["query"] = f"{message}\n추가 확인 항목: {item['aspect']}의 근거와 적용 조건"
    return matched


def coverage(plan, hits):
    result = []
    for item in plan:
        evidence_ids = list(dict.fromkeys(hit["passageId"] for hit in hits
            if re.search(item["pattern"], hit.get("text", hit.get("excerpt", "")), re.I)))
        result.append({"id": item["id"], "aspect": item["aspect"],
                       "status": "candidate_found" if evidence_ids else "unknown",
                       "evidencePassageIds": evidence_ids,
                       "assessment": "literal_aspect_signal_only"})
    return result


def reranking_query(query, plan):
    if not re.search(r"수치|정량|측정값|얼마|\bnumerical\b|\bquantitative\b|how much", query, re.I):
        return query
    parameter_ids = {row[0] for row in PARAMETERS}
    focus = [item["aspect"] for item in plan if item["id"] in parameter_ids]
    if not focus:
        return query
    return query + "\n중점 확인: " + "; ".join(focus) + ". 실제 수치 비교와 측정 조건을 우선 확인."


def context_characters(hits):
    unique = {hit["passageId"]: hit.get("text", hit.get("excerpt", "")) for hit in hits}
    return sum(len(text) for text in unique.values())

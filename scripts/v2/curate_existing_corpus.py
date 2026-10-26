"""Prepare traceable, offline derivatives of the supplied 129-document corpus."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat


EDITOR = "Codex 기존 문헌 정리 lane"
GENERAL_LIMIT = "제공 텍스트만 대조했으며 제조사 웹 원출처와 전체 주장의 진위는 검증하지 않았습니다."
QUANTITY_LIMIT = "교육·정성 설명용 조건부 후보입니다. 수치·사양·시장 현황을 독립 실험 결과나 보편적 공정 조건으로 사용하지 않습니다."
CONSTANTS = "review/lanes/power/physical-constants.json"

# Reviewed source-specific text stays in the private run, not in the repository.
def load_rules(root):
    rule_bytes = confined_path(root, "curation-rules.json").read_bytes()
    control = json.loads(confined_path(root, "run-control.json").read_text(encoding="utf-8-sig"))
    require(sha(rule_bytes) == control.get("curation_rules_sha256"), "Curation rules hash differs from run control")
    rules = json.loads(rule_bytes.decode("utf-8"))
    names = {"HOLD_LINES", "CUT_TEXT", "CORRECTION_NOTES", "CORRECTION_EVIDENCE", "SAMSUNG_REREVIEW_STEMS"}
    require(set(rules) == names, "Curation rules schema differs")
    global HOLD_LINES, CUT_TEXT, CORRECTION_NOTES, CORRECTION_EVIDENCE, SAMSUNG_REREVIEW_STEMS
    HOLD_LINES = {stem: {int(line): value for line, value in entries.items()} for stem, entries in rules["HOLD_LINES"].items()}
    CUT_TEXT = {stem: {int(line): value for line, value in entries.items()} for stem, entries in rules["CUT_TEXT"].items()}
    CORRECTION_NOTES = rules["CORRECTION_NOTES"]
    CORRECTION_EVIDENCE = rules["CORRECTION_EVIDENCE"]
    SAMSUNG_REREVIEW_STEMS = set(rules["SAMSUNG_REREVIEW_STEMS"])




def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def confined_path(root, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and not relative.drive and ".." not in relative.parts, f"Invalid relative path: {relative}")
    path = root
    for part in relative.parts:
        path = path / part
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        reparse_point = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        require(not stat.S_ISLNK(info.st_mode) and not reparse_point, f"Linked path is not allowed: {path}")
    require(path.resolve().is_relative_to(root), f"Path escapes the run root: {path}")
    return path


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def control_check(root):
    control = json.loads(confined_path(root, "run-control.json").read_text(encoding="utf-8-sig"))
    now = datetime.now(timezone.utc)
    deadline = datetime.fromisoformat(control["wrapup_at_utc"].replace("Z", "+00:00"))
    checked_at = datetime.fromisoformat(control["last_check_at_utc"].replace("Z", "+00:00"))
    if control["status"] not in ("running", "running_resumed") or control["minimum_remaining_percent"] <= 35 or now >= deadline:
        raise RuntimeError("Run control requires wrap-up or stop; no new curation is permitted.")
    if not 0 <= (now - checked_at).total_seconds() <= 300:
        raise RuntimeError("Usage checkpoint is stale or in the future; refresh it before curation.")


def frontmatter(lines):
    require(bool(lines) and (lines[0] == "---" or lines[0].startswith("# ")), "Invalid or empty source document")
    if lines[0] != "---":
        return {}, 0
    end = lines.index("---", 1)
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key] = value.strip().strip('"')
    return meta, end + 1


def body_range(path, lines, meta, front_end):
    if "/samsung/" in path:
        titles = [l.removesuffix(" - 삼성전자 반도체 뉴스룸") for l in lines if l.endswith(" - 삼성전자 반도체 뉴스룸")]
        require(len(titles) == 1, f"Expected one Samsung page title: {path}")
        start = lines.index("주소복사") + 1
        ends = [i for i, l in enumerate(lines) if re.match(r"^#{1,6} 관련태그$", l)]
        require(len(ends) == 1, f"Expected one Samsung body end: {path}")
        end = ends[0]
        while start < end and lines[start].strip() in ("", "-"):
            start += 1
        return titles[0], start, end
    start = front_end
    while start < len(lines) and (not lines[start].strip() or lines[start].startswith("# ")):
        start += 1
    end = len(lines)
    title = meta.get("title") or lines[0].lstrip("# ")
    if "/lam_research/lam_solution_" in path:
        start = next(i for i, l in enumerate(lines) if l.startswith("### "))
        related = [i for i, l in enumerate(lines) if l.strip().casefold() in ("related blog posts", "관련 블로그 게시물", "관련 블로그 기사")]
        require(len(related) == 1, f"Expected one Lam related-post boundary: {path}")
        end = related[0]
        while end > start and lines[end - 1].strip() in ("", "###"):
            end -= 1
    return title, start, end


def topics(title, path):
    text = (title + " " + path).lower()
    rules = {
        "본딩·패키징": r"bond|본딩|패키|tsv|칩렛|chiplet|이종집적|mcp|리드-프레임",
        "메모리·컴퓨팅": r"메모리|낸드|nand|dram|d램|s램|hbm|cxl|pim|ssd|gpu|뉴로모픽|computational|memory|sram|ram|rom|hdd|emmc|ufs",
        "산화·증착·식각": r"산화|oxidation|증착|deposition|식각|etch|cmp|epi",
        "노광·장비·배선": r"포토|photo|금속|배선|metal|asml|amat|마스크|mask|웨이퍼|wafer|잉곳|트렌치",
        "수율·신뢰성·검사": r"수율|신뢰|reliability|eds|tat|테스트|검사",
        "소자·기초용어": r"glossary|소자|트랜지스터|반도체|ic|cmos|c[i]?s|isocell|led|다이오드|커패시|저항|파운드리|팹리스|soc|ddi",
        "표준·팹 자동화": r"semi/|standard|자동화",
    }
    return [topic for topic, pattern in rules.items() if re.search(pattern, text)] or ["반도체 기초·산업"]


def classify(path, meta):
    stem = Path(path).stem
    if not meta.get("source_url"):
        return "보류", "held", "unverified_editorial_compilation", "원출처 URL·문서별 판본/위치가 없는 편집 묶음입니다. 'official'이라는 자체 표기를 출처 검증으로 인정하지 않습니다."
    if "/samsung_glossary_" in path or stem == "samsung_fab_00_overview":
        return "보류", "held", "video_or_navigation_introduction", "제공된 본문은 영상·모아보기·이동 안내이며 제목의 기술 설명·영상 자막·연결 콘텐츠 본문을 확보하지 못했습니다."
    if stem == "skhynix_tech_tsv_mr_muf":
        return "보류", "held", "partial_lecture_introduction", "제공본은 29줄의 강연 도입·인물 캡션까지이며 TSV/MR-MUF 강연 전체를 복구하지 못했습니다."
    if stem.endswith("_kr") and "/lam_solution_" in path:
        return "동일계보중복", "conditional", "manufacturer_translation", "같은 Lam 솔루션의 한국어 번역본입니다. 한국어 검색을 위해 조건부 후보로 보존하되 영어 문헌과 같은 계보로 묶고 독립 근거로 중복 집계하지 않습니다. 번역 정확성 전수 대조는 미완료입니다."
    kind = "manufacturer_education"
    if "/glossary/" in path or stem == "lam_technical_glossary":
        kind = "manufacturer_glossary"
    elif stem.startswith("skhynix_research_"):
        kind = "newsroom_research_summary_and_interview"
    elif stem.startswith(("skhynix_ai_", "skhynix_frontend_", "skhynix_pkg_", "skhynix_tech_hybrid")):
        kind = "external_expert_column"
    elif stem.startswith("lam_solution_"):
        kind = "manufacturer_product_overview"
    return "수정", "conditional", kind, "제공 텍스트와 대조해 본문·제목·귀속·한계를 정리한 조건부 후보입니다. 웹 원출처 검증이나 정량 비교 승인은 아닙니다."


def author_info(stem, lines):
    if stem.startswith("skhynix_ai_") and any("정인성 작가" in l for l in lines):
        return "정인성", [{"line": 11, "role": "외부 기고자", "name": "정인성"}]
    names = {"skhynix_pkg_01_chiplet": "최리노", "skhynix_pkg_02_3d_heterogeneous": "이병훈", "skhynix_tech_hybrid_bonding": "주승환"}
    if stem in names:
        require(len(lines) > 12 and names[stem] in lines[12], f"Expert attribution mismatch: {stem}")
        return names[stem], [{"line": 13, "role": "외부 전문가", "name": names[stem]}]
    if stem == "skhynix_research_cti_nand":
        return None, [{"line": 19, "role": "소개된 논문 저자·인터뷰 주체, 기사 저자와 구분", "name": "진상완"}]
    if stem == "skhynix_research_computational_nand":
        return None, [{"line": 21, "role": "소개된 논문 저자, 기사 저자와 구분", "name": "구원태·김지훈"}]
    return None, []


def blocks(rows):
    result, block = [], []
    for row in rows + [(0, "")]:
        if row[1].strip():
            if block and row[0] != block[-1][0] + 1:
                result.append(block)
                block = []
            block.append(row)
        elif block:
            result.append(block)
            block = []
    return result


def main(root):
    # shortcut: budget is checked at start; add per-document checks if runs become long.
    control_check(root)
    load_rules(root)
    out = confined_path(root, "curated/existing")
    review = confined_path(root, "review/lanes/existing")
    if any(path.exists() and any(path.iterdir()) for path in (out, review)):
        raise FileExistsError("Existing outputs must be preserved; use a fresh run root.")
    manifest = json.loads(confined_path(root, "raw/input-manifest.json").read_text(encoding="utf-8"))
    documents = sorted(manifest["documents"], key=lambda d: d["path"])
    require(len(documents) == 129 and len({d["path"] for d in documents}) == 129, "Input manifest cardinality or paths are invalid")
    raw = confined_path(root, "raw/existing").resolve()
    out.mkdir(parents=True, exist_ok=True)
    review.mkdir(parents=True, exist_ok=True)
    records, claims, all_checks = [], [], []
    for number, doc in enumerate(documents, 1):
        ident, path = f"e{number:03}", doc["path"]
        original = confined_path(raw, path).resolve()
        data = original.read_bytes()
        require(sha(data) == doc["sha256"] and len(data) == doc["bytes"], f"Input hash or length differs: {path}")
        lines = data.decode("utf-8-sig").splitlines()
        meta, front_end = frontmatter(lines)
        title, start, end = body_range(path, lines, meta, front_end)
        require(bool(title.strip()) and start < end and any(l.strip() for l in lines[start:end]), f"Missing source title or body: {path}")
        disposition, status, kind, reason = classify(path, meta)
        stem = Path(path).stem
        author, attributed = author_info(stem, lines)
        lineage = meta.get("source_url") or "provided-editorial:" + stem
        if stem.startswith("lam_solution_"):
            lineage = "lam:solution:" + ("deposition" if "deposition" in stem else "etch")
        limitations = [GENERAL_LIMIT, QUANTITY_LIMIT]
        changes = []
        omitted = []
        if "/samsung/" in path:
            changes += ["반복 메뉴·인기 검색어·공유·관련기사·태그·푸터를 본문과 분리했습니다.", "뉴스룸 페이지 제목을 식별했고 원 본문 범위의 모든 비어 있지 않은 줄을 대조했습니다."]
        if "/glossary/" in path:
            require(meta.get("title") == "용어사전" and title != "용어사전", f"Glossary title mismatch: {path}")
            limitations.append("기초 정의용이며 일반적인 공정 레시피·최신 제품 사양·독립 실험 근거로 확대하지 않습니다.")
        if any("▲" in l or "그림" in l or "표 " in l for l in lines[start:end]):
            limitations.append("제공 텍스트의 그림·표 언급과 캡션은 보존했으나 원 이미지·표 셀은 이 lane에서 재확보하지 않았습니다.")
        if kind == "external_expert_column":
            limitations.append("외부 전문가 칼럼이며 발행 회사의 공식 입장·제품 사양과 구분합니다. 본문에서 이름을 확인할 수 없는 필자는 미확인입니다.")
        if kind == "newsroom_research_summary_and_interview":
            limitations.append("원 논문이 아닌 뉴스룸 소개·인터뷰입니다. 논문 저자와 기사 작성자를 구분하며 실측·시뮬레이션을 서로 바꾸지 않습니다.")
        if kind == "manufacturer_translation":
            limitations.append("같은 영문 원문의 번역 계보이므로 독립 근거가 아닙니다. 번역 정확성과 현재 웹 원문을 전수 대조하지 않았습니다.")
        if stem in SAMSUNG_REREVIEW_STEMS:
            limitations.append("기존 독립 사후 검토 스냅샷 이후 수정된 문서입니다. 변경된 본문과 편집 주석에 대한 검토자 재확인이 필요합니다.")
        if stem == "samsung_fab_07_metal_interconnect":
            limitations.append("L146–148 사이의 조건 목록은 제공 텍스트에 없으며 삼성 원문 그림에서 확인한 교육용 요약을 출처와 함께 별도 주석으로 보완했습니다. 재료별 정량 합격 기준은 없습니다.")
        if stem == "skhynix_frontend_04_etch":
            limitations.append("L79 식각 가스 종류 그림은 캡션뿐입니다. 원 교재 443쪽 그림의 셀·수치·전체 내용을 확보하지 않았습니다.")
        if stem == "skhynix_tech_hybrid_bonding":
            limitations.append("L67·81에서 MR-MUF를 TCB 범주로 설명하는 것은 이 칼럼의 분류 표현입니다. 보편적인 표준 공정 분류로 확정하지 않습니다.")
            limitations.append("서로 상충하는 HBM4 전환 전망은 보류했습니다. 실제 상용화 상태·장비 정밀도·세대 규격은 현재 사실로 재검증하지 않았습니다.")
        if status == "held":
            limitations.append(reason)
        if not meta.get("source_url"):
            limitations.append("publisher/type의 '공식' 표기는 제공본의 주장일 뿐입니다. 원 발행기관의 작성·배포·내용 검증을 확인하지 못했습니다.")
            if stem == "tier2_current_production_applied_papers":
                limitations.append("기존 조사 문서에서 L121–125의 DOI 10.1016/j.actamat.2022.118021이 본딩 아닌 자성체 논문으로 확인됐습니다. 전체 묶음을 보류하며 404 두 건은 허위 논문 확정으로 해석하지 않습니다.")
        rows = []
        effective_end = end
        if stem in ("skhynix_tech_hybrid_bonding", "skhynix_pkg_02_3d_heterogeneous"):
            disclaimer = [i for i, l in enumerate(lines) if l.startswith("※") and "공식 입장" in l]
            require(len(disclaimer) == 1, f"Expected one expert disclaimer: {path}")
            if disclaimer[0] + 1 < end:
                effective_end = disclaimer[0] + 1
                omitted.append({"start_line": effective_end + 1, "end_line": end, "kind": "unverified_appended_qa", "reason": "칼럼 면책문 뒤에 붙은 Q&A의 작성 주체·원문 포함 여부를 확인하지 못했습니다. 같은 문헌의 재서술이므로 독립 근거로 쓰지 않습니다."})
                changes.append("면책문 뒤 출처 미확인 Q&A를 검토 기록으로 분리했습니다.")
        holds = HOLD_LINES.get(stem, {})
        cuts = CUT_TEXT.get(stem, {})
        for index in range(start, effective_end):
            line_no, text = index + 1, lines[index]
            if line_no in holds:
                expected, why = holds[line_no]
                require(expected in text, f"Held line marker mismatch: {path}:{line_no}")
                omitted.append({"start_line": line_no, "end_line": line_no, "kind": "held_claim", "reason": why, "original_text": text})
                continue
            if line_no in cuts:
                cut, why = cuts[line_no]
                require(text.count(cut) == 1, f"Held sentence marker mismatch: {path}:{line_no}")
                before, after = text.split(cut)
                require(before + cut + after == text, f"Held sentence reconstruction failed: {path}:{line_no}")
                omitted.append({"start_line": line_no, "end_line": line_no, "kind": "held_sentence", "reason": why, "original_text": cut})
                text = (before + after).strip()
            if stem.startswith("lam_solution_") and text.strip() in ("###", "-->"):
                omitted.append({"start_line": line_no, "end_line": line_no, "kind": "markup_only", "reason": "비어 있는 제목·HTML 마커만 제거했습니다."})
                continue
            rows.append((line_no, text))
        for line_no in holds:
            require(start < line_no <= effective_end, f"Held line outside source body: {path}:{line_no}")
        for line_no in cuts:
            require(start < line_no <= effective_end, f"Held sentence outside source body: {path}:{line_no}")
        block_list = blocks(rows)
        source_map = [{"start_line": b[0][0], "end_line": b[-1][0], "text_sha256": sha("\n".join(t for _, t in b).encode())} for b in block_list]
        original_nonblank = [(i + 1, lines[i]) for i in range(start, effective_end) if lines[i].strip()]
        kept_nonblank = [(i, t) for i, t in rows if t.strip()]
        if not holds and not cuts and not stem.startswith("lam_solution_"):
            require(original_nonblank == kept_nonblank, f"Unaccounted body change: {path}")
        for line_no, text in kept_nonblank:
            if line_no not in cuts:
                require(text == lines[line_no - 1], f"Unaccounted line change: {path}:{line_no}")
            else:
                require(text == lines[line_no - 1].replace(cuts[line_no][0], "").strip(), f"Edited line mismatch: {path}:{line_no}")
        if holds or cuts:
            changes.append("원출처·조건 미확인 수치 또는 상충 구절만 범위를 좁혀 보류했으며 모델 상식으로 대체하지 않았습니다.")
        if stem in CORRECTION_NOTES:
            if stem in ("skhynix_frontend_02_oxidation", "skhynix_frontend_05_deposition"):
                require(confined_path(root, CONSTANTS).is_file(), "Physical-constants evidence record is required before publishing correction notes")
            changes.append("제공본 대조 또는 확인된 외부 출처를 명시한 편집 주석을 별도 표시했습니다.")
        date = next((l for l in lines[:start] if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", l)), None)
        curated_path = f"curated/existing/{ident}-{stem}.md" if status == "conditional" else None
        record = {
            "id": ident, "original_path": path, "original_sha256": doc["sha256"],
            "title": title, "source_url": meta.get("source_url"), "publisher": meta.get("publisher"),
            "author": author, "attributed_to": attributed, "source_type": kind,
            "claimed_source_type": meta.get("type"), "publication_date_in_provided_text": date,
            "topics": topics(title, path), "lineage_id": lineage,
            "translation_of": path.removesuffix("_kr.md") + "_en.md" if kind == "manufacturer_translation" else None,
            "disposition": disposition, "reason": reason,
            "review_depth": "제공 본문 경계·제목 대조와 선별 위험 검토 및 문단 보존검사; 웹 원출처 미대조",
            "curated_path": curated_path, "acceptance_status": status,
            "source_access_scope": "provided_text_only", "editorial_changes": changes,
            "limitations": limitations,
            "checked_source_locations": [{"path": path, "start_line": 1, "end_line": len(lines), "purpose": "제공 텍스트 구조·메타데이터 확인"}, {"path": path, "start_line": start + 1, "end_line": end, "purpose": "본문 경계·정성 설명 범위·보존 대조"}],
            "source_line_map": source_map,
            "omitted_body_ranges": omitted,
            "correction_evidence_record": CONSTANTS if stem in ("skhynix_frontend_02_oxidation", "skhynix_frontend_05_deposition") else None,
            "correction_evidence": CORRECTION_EVIDENCE.get(stem, []),
            "online_original_verified": False,
            "allowed_use": ["기초 정의·정성 설명의 원출처 재검토 후보"] if status == "conditional" else [],
            "not_allowed_use": ["원출처 검증 완료 주장", "조건 없는 정량 비교", "즉시 일괄 승인·등록·색인"],
        }
        if stem in SAMSUNG_REREVIEW_STEMS:
            record["semantic_recheck_required"] = True
            record["semantic_recheck_reason"] = "기존 삼성 사후 검토 스냅샷 이후 내용이 수정됨"
        if stem == "tier2_current_production_applied_papers":
            record["checked_source_locations"].append({"path": "docs/CORPUS_GAPS_AND_COLLECTION_PLAN_20261026.md", "section": "실제 확인한 서지 불일치", "purpose": "기존 직접 서지 대조 결과 재사용"})
        if curated_path:
            header = {k: record[k] for k in ("id", "title", "source_url", "publisher", "author", "source_type", "lineage_id", "acceptance_status", "source_access_scope", "original_path", "original_sha256")}
            header["editor"] = EDITOR
            result = "---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in header.items()) + "\n---\n\n# " + title + "\n\n"
            intro = ["편집자: " + EDITOR, "원자료: raw/existing/" + path + f" (제공본 L{start + 1}–L{end}); SHA-256 " + doc["sha256"], "변경: " + " ".join(changes), "한계: " + " ".join(limitations)]
            result += "\n\n".join("> " + t for t in intro) + "\n\n"
            if omitted:
                result += "> 보류 범위: " + "; ".join(f"L{x['start_line']}–L{x['end_line']}: {x['reason']}" for x in omitted if x["kind"] != "markup_only") + "\n\n"
            if stem in CORRECTION_NOTES:
                result += "## 편집 정정주석\n\n" + "\n\n".join(CORRECTION_NOTES[stem]) + "\n\n"
            result += "## 제공 텍스트 본문\n\n"
            for b in block_list:
                result += f"<!-- provided-source: {path}:L{b[0][0]}-L{b[-1][0]} -->\n" + "\n".join(t for _, t in b) + "\n\n"
            target = root / curated_path
            target.write_text(result, encoding="utf-8")
            written = target.read_text(encoding="utf-8")
            require("# " + title + "\n" in written, f"Derivative title is missing: {path}")
            for b in block_list:
                require("\n".join(t for _, t in b) in written, f"Derivative block is missing: {path}:{b[0][0]}")
            record["curated_sha256"] = sha(target.read_bytes())
            for forbidden in ("메뉴 열기", "검색 레이어 열기", "© 2026."):
                require(forbidden not in written.split("## 제공 텍스트 본문\n\n", 1)[1], f"Navigation residue found: {path}:{forbidden}")
        for omitted_item in omitted:
            if omitted_item["kind"] in ("held_claim", "held_sentence", "unverified_appended_qa"):
                claims.append({"id": f"{ident}-hold-{len(claims) + 1:03}", "document_id": ident, "source_url": meta.get("source_url"), "source_access_scope": "provided_text_only", "status": "held", "source_path": path, **omitted_item})
        check = {"document_id": ident, "original_path": path, "input_hash_match": True, "title_identified": True, "body_start_line": start + 1, "body_end_line": end, "body_nonblank_lines": len(original_nonblank), "retained_nonblank_lines": len(kept_nonblank), "retained_blocks": len(block_list), "known_omissions_accounted_for": True, "unreported_text_change": False, "web_original_check": False}
        all_checks.append(check)
        dump(review / "documents" / (ident + ".json"), {"record": record, "preservation_check": check})
        records.append(record)
    require(len(records) == 129 and len(all_checks) == 129, "Output inventory cardinality differs from input")
    require(sum("/glossary/" in r["original_path"] for r in records) == 78, "Samsung glossary count differs from input")
    for doc in documents:
        require(sha(confined_path(raw, doc["path"]).read_bytes()) == doc["sha256"], f"Input changed during curation: {doc['path']}")
    jsonl(review / "inventory.jsonl", records)
    jsonl(review / "claims.jsonl", claims)
    dump(review / "preservation-checks.json", all_checks)
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "editor": EDITOR, "scope": "existing supplied 129 documents only", "document_count": 129, "disposition_counts": dict(Counter(r["disposition"] for r in records)), "acceptance_counts": dict(Counter(r["acceptance_status"] for r in records)), "derived_document_count": sum(r["curated_path"] is not None for r in records), "raw_hashes_unchanged": True, "preservation_checks_passed": 129, "samsung_glossary_title_body_checks_passed": 78, "held_claim_or_qa_count": len(claims), "source_access_scope": "provided_text_only", "manufacturer_web_originals_verified": 0, "service_api_calls": 0, "database_changes": 0, "limitations": [GENERAL_LIMIT, "모든 수치·문장의 전수 진위 검증이 아닙니다.", "conditional은 서비스 반입 승인·원출처 검증 완료가 아닙니다."], "inventory_path": "review/lanes/existing/inventory.jsonl", "claims_path": "review/lanes/existing/claims.jsonl", "correction_evidence_record": CONSTANTS}
    dump(out / "report.json", report)
    dump(review / "checkpoint.json", {"completed_at_utc": report["generated_at_utc"], "status": "first_pass_complete_pending_independent_review", "document_count": 129, "next": "부모 lane의 독립 검토·원출처 대조 및 전체 inventory 병합"})
    readme = "# 기존 129개 제공 문헌의 정리 결과\n\n원본 바이트는 raw/existing에 보존했습니다. 이 폴더는 제공본을 대조한 파생 문헌이며 제조사 웹 원문을 재검증한 자료집이 아닙니다. 조건부 후보는 정의·정성 설명의 재검토용입니다. 일괄 승인·등록·색인하면 안 됩니다.\n\n"
    readme += "처분: " + json.dumps(report["disposition_counts"], ensure_ascii=False) + "; 상태: " + json.dumps(report["acceptance_counts"], ensure_ascii=False) + ".\n\n"
    readme += "검사: 129개 입력 해시 일치와 원본 보존, 129개 본문 범위·줄/문단 대조, 삼성 용어 78개 실제 제목·본문 경계 보존을 확인했습니다. 보류한 문장·Q&A는 review/lanes/existing/claims.jsonl와 documents/*.json에 위치·이유를 기록했습니다. 이는 모든 문장의 사실 검증이 아닙니다.\n\n"
    readme += "정정: 산화 각주의 물 분자량과 증착 글의 Al 녹는점 문구는 원문을 바꾸지 않고 부모 lane의 NIST/RSC 확인 기록에 연결해 편집 주석으로 분리했습니다. 물성값은 성장률 인과나 공정 허용 온도를 검증하지 않습니다.\n\n"
    readme += "산출물: review/lanes/existing/inventory.jsonl, claims.jsonl, preservation-checks.json, documents/*.json; curated/existing/report.json. 같은 Lam 영문/한국어 페이지는 한 계보이며 독립 근거 두 개가 아닙니다. 삼성 영상 소개 6개·공정 개요 안내 1개, 강연 도입 1개, 출처 없는 편집 묶음 9개는 보류했습니다.\n\n"
    readme += "| ID | 제목 | 처분 | 상태 | 본문 위치 |\n| --- | --- | --- | --- | --- |\n"
    for r, c in zip(records, all_checks):
        readme += f"| {r['id']} | {r['title'].replace('|', ' / ')} | {r['disposition']} | {r['acceptance_status']} | {r['original_path']}:L{c['body_start_line']}–L{c['body_end_line']} |\n"
    (out / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    main(args.run_root.resolve())

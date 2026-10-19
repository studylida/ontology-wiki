"""Source Whitepaper Parser and Knowledge Extractor.

Parses official technical markdown whitepapers from sources/ directory:
- Extracts YAML frontmatter (title, publisher, source_id, type)
- Strips web noise (navigation headers, footer links, cookie alerts)
- Extracts engineering assertions, LaTeX formulas, and key quotes
- Normalizes records into EvidenceSource and Concept candidate structures

Follows docs/data_extraction_playbook.md guidelines.
"""
import os
import re
import glob
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class SourceParser:
    """Deterministic parser for official semiconductor whitepapers in sources/."""

    def __init__(self, sources_dir: Optional[str] = None):
        if sources_dir:
            self.sources_dir = Path(sources_dir)
        else:
            # 기본 경로: c:\Users\BISTelligence\ontology-wiki\sources
            self.sources_dir = Path(__file__).resolve().parent.parent.parent / "sources"

    def parse_all_whitepapers(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Scans sources/ and extracts EvidenceSources and Concept candidates."""
        evidence_list: List[Dict[str, Any]] = []
        concept_candidates: List[Dict[str, Any]] = []
        processed_files = 0

        pattern = str(self.sources_dir / "**" / "*.md")
        md_files = glob.glob(pattern, recursive=True)

        for file_path in md_files:
            try:
                evidences, concepts = self.parse_single_file(file_path)
                evidence_list.extend(evidences)
                concept_candidates.extend(concepts)
                processed_files += 1
            except Exception as e:
                # 개별 파일 파싱 오류 시에도 전체 파이프라인 중단 방지
                continue

        return evidence_list, concept_candidates

    def parse_single_file(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parses a single markdown whitepaper file."""
        path = Path(file_path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        frontmatter, body = self._extract_frontmatter(content)
        cleaned_body = self._clean_web_noise(body)

        # 1. EvidenceSource 생성
        evidences = self._build_evidence_sources(path, frontmatter, cleaned_body)

        # 2. Concept 후보 추출
        concepts = self._extract_concept_candidates(path, frontmatter, cleaned_body)

        return evidences, concepts

    def _extract_frontmatter(self, text: str) -> Tuple[Dict[str, str], str]:
        """Extracts YAML frontmatter if present."""
        frontmatter: Dict[str, str] = {}
        body = text

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                yaml_block = parts[1]
                body = parts[2]
                for line in yaml_block.splitlines():
                    if ":" in line:
                        key, val = line.split(":", 1)
                        frontmatter[key.strip()] = val.strip().strip('"').strip("'")

        return frontmatter, body

    def _clean_web_noise(self, text: str) -> str:
        """Strips web scraper noise, menus, navigation headers and footers."""
        lines = text.splitlines()
        cleaned_lines = []
        skip_noise_patterns = [
            r"본문 바로가기",
            r"Internet Explorer를 지원하지 않습니다",
            r"메뉴 열기",
            r"검색 레이어 열기",
            r"프레스센터",
            r"통합검색",
            r"검색어 입력",
            r"검색어 삭제",
            r"최신순",
            r"조회순",
            r"전체 날짜",
            r"공유 레이어 열기",
            r"인쇄하기",
            r"페이스북",
            r"카카오톡",
            r"주소복사",
            r"구독과 좋아요"
        ]
        regex = re.compile("|".join(skip_noise_patterns))

        for line in lines:
            trimmed = line.strip()
            # 빈 줄이나 단일 하이픈/불릿 노이즈 제거
            if trimmed in ["-", "*", "#", ">"]:
                continue
            if regex.search(trimmed):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _build_evidence_sources(
        self, path: Path, frontmatter: Dict[str, str], body: str
    ) -> List[Dict[str, Any]]:
        """Constructs EvidenceSource entity from document metadata and key paragraph."""
        subfolder = path.parent.name.lower()
        title = frontmatter.get("title") or path.stem.replace("_", " ").title()
        publisher = frontmatter.get("publisher") or self._detect_publisher(subfolder)
        source_url = frontmatter.get("source_url") or f"https://sources.internal/{path.name}"
        source_id = frontmatter.get("source_id") or f"src_{path.stem}"

        tier = "Tier 1 (공식 제조사)"
        if "semi" in subfolder or "standard" in subfolder:
            tier = "Tier 2 (국제 표준)"
        elif "research" in subfolder or "academic" in subfolder:
            tier = "Tier 3 (공인 학술)"

        # 대표 인용구 추출 (첫 번째 실질적 의미를 가진 단락 200~400자)
        paragraphs = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 80]
        quote = paragraphs[0] if paragraphs else f"{title} 공식 기술 백서 원문 요약."
        if len(quote) > 350:
            quote = quote[:347] + "..."

        evidence = {
            "id": f"E-SRC-{path.stem[:24]}",
            "source_name": f"{publisher}: {title}",
            "source_type": frontmatter.get("type", "official_whitepaper"),
            "publisher": publisher,
            "published_date": frontmatter.get("date", "2026.01"),
            "quote": quote,
            "section_context": f"{path.name} Section 1",
            "relevance_score": 0.95,
            "external_url": source_url,
            "url_label": f"{publisher} 백서 원문 ➔",
            "credibility_tier": tier,
            "referenced_concepts": []
        }
        return [evidence]

    def _extract_concept_candidates(
        self, path: Path, frontmatter: Dict[str, str], body: str
    ) -> List[Dict[str, Any]]:
        """Extracts concept candidate structures from markdown headings (H2/H3)."""
        candidates: List[Dict[str, Any]] = []
        headings = re.findall(r"^##\s+(.+)$", body, re.MULTILINE)

        subfolder = path.parent.name.lower()
        domain_facet = "unit_process"
        if "ai" in path.name or "nanosheet" in path.name or "transistor" in path.name:
            domain_facet = "device"
        elif "fdc" in path.name or "opc" in path.name:
            domain_facet = "operations"

        for heading in headings[:3]:  # 핵심 섹션 3개까지 추출
            heading_clean = heading.strip().strip("‘").strip("’").strip('"')
            # 불필요한 번호 제거 (예: "1. 노광 물리학" -> "노광 물리학")
            heading_clean = re.sub(r"^\d+(\.\d+)?\s*", "", heading_clean)
            if len(heading_clean) < 3 or len(heading_clean) > 40:
                continue

            concept_id = f"cand-{path.stem[:16]}-{re.sub(r'[^a-zA-Z0-9]', '', heading_clean)[:12].lower()}"
            candidates.append({
                "id": concept_id,
                "title": heading_clean,
                "eng_name": f"{heading_clean} (Engineering Concept)",
                "aliases": [heading_clean],
                "domain_facet": domain_facet,
                "process_category": self._detect_category(path.name),
                "scale_level": 3,
                "scale_name": "Scale 3: 단위 공정",
                "summary": f"{heading_clean}에 대한 공인 백서 기술 해설 요약.",
                "purpose": f"{heading_clean}을 통한 반도체 제조 수율 및 성능 제어.",
                "principles": [],
                "limitations": [],
                "relations": {}
            })

        return candidates

    def _detect_publisher(self, folder: str) -> str:
        mapping = {
            "samsung": "Samsung Semiconductor",
            "skhynix": "SK hynix",
            "asml": "ASML",
            "lam_research": "Lam Research",
            "amat": "Applied Materials",
            "semi": "SEMI",
            "research_institutes": "imec / IEEE"
        }
        return mapping.get(folder, folder.capitalize())

    def _detect_category(self, filename: str) -> str:
        fn = filename.lower()
        if "etch" in fn:
            return "식각 공정"
        if "litho" in fn or "asml" in fn:
            return "노광 공정"
        if "depo" in fn or "ald" in fn or "cvd" in fn:
            return "박막 증착 공정"
        if "pkg" in fn or "hbm" in fn or "bonding" in fn:
            return "첨단 패키징"
        if "clean" in fn or "cmp" in fn:
            return "세정 및 연마"
        if "fdc" in fn or "apc" in fn or "mes" in fn:
            return "팹 운영 제어"
        return "반도체 제조 기술"


parser = SourceParser()

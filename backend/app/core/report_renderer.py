"""Section 6.3: Engineering Report Renderer (엔지니어링 기술 보고서 렌더러).

Unified renderer for standard engineering Markdown and technical whitepapers across:
- Tab 2: Perspective Studio Comparison Matrix & Tuning Recipe Report.
- Tab 4: Deep Research Technical Whitepaper & Literature Synthesis Report.
"""
from datetime import datetime
from typing import Dict, Any, List
from fastapi.responses import Response


class ReportRenderer:
    """반도체 엔지니어링 표준 기술 동향 및 비교 보고서 마크다운 생성기."""

    @staticmethod
    def render_deep_research_report(
        session_topic: str,
        user_id: str,
        created_at: str,
        synthesis: Dict[str, Any],
        evidence_feeds: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Tab 4 심층 기술 분석 화이트페이퍼 마크다운을 렌더링합니다."""
        now_str = datetime.utcnow().strftime("%Y.%m.%d")
        
        # 1. 헤더 & 메타데이터
        md = [
            f"# 📑 [심층 기술 동향 보고서] {session_topic}",
            f"- **조사 주제**: {session_topic}",
            f"- **담당 엔지니어**: {user_id} | **보고서 발행일**: {now_str}",
            f"- **분석 공인 문헌 풀**: 총 {len(evidence_feeds)}편 교차 분석 완료",
            "\n---\n"
        ]

        # 2. 총괄 요약
        exec_sum = synthesis.get("executiveSummary") or synthesis.get("executive_summary") or "총괄 요약 정보가 없습니다."
        md.extend([
            "## 1. 📌 총괄 요약 (Executive Summary)",
            f"{exec_sum}\n"
        ])

        # 3. 물리 메커니즘 심층 분석
        mech = synthesis.get("physicalMechanism") or synthesis.get("physical_mechanism") or "메커니즘 분석 정보가 없습니다."
        md.extend([
            "## 2. 🔬 공정 물리 메커니즘 심층 분석 (Physical Mechanism)",
            f"{mech}\n"
        ])

        # 4. 학계 vs 산업계 마진 대조표
        margins = synthesis.get("academicVsIndustry") or synthesis.get("academic_vs_industry") or []
        md.extend([
            "## 3. ⚖️ 글로벌 학계 vs 양산 제조사 공정 마진 대조표 (Comparative Margin Analysis)",
            "| 평가 지표 (Specification) | 학계 연구 규격 (Academia) | 글로벌 제조사 양산 마진 (Industry) | 공학적 시사점 및 타협 사유 |",
            "| :--- | :--- | :--- | :--- |"
        ])
        if margins:
            for m in margins:
                spec = m.get("specName") or m.get("spec_name") or "-"
                acad = m.get("academicSpec") or m.get("academic_spec") or "-"
                ind = m.get("industryMargin") or m.get("industry_margin") or "-"
                comm = m.get("commentary") or "-"
                md.append(f"| **{spec}** | {acad} | {ind} | {comm} |")
        else:
            md.append("| - | 데이터 없음 | 데이터 없음 | - |")
        md.append("\n")

        # 5. 엔지니어링 트레이드오프 및 한계
        tradeoff = synthesis.get("tradeoffAnalysis") or synthesis.get("tradeoff_analysis") or "상충 분석 정보가 없습니다."
        md.extend([
            "## 4. ⚠️ 핵심 엔지니어링 트레이드오프 및 병목 극복 대안 (Trade-offs & Solutions)",
            f"{tradeoff}\n"
        ])

        # 6. 사내 팹 라인 적용 권고안
        recom = synthesis.get("actionableRecommendations") or synthesis.get("actionable_recommendations") or "적용 권고안이 없습니다."
        md.extend([
            "## 5. 💡 사내 팹 라인 적용 권고안 (Actionable Fab Implementation Guide)",
            f"{recom}\n"
        ])

        # 7. 온톨로지 편입 제안 후보
        if candidates:
            md.extend([
                "## 6. 🏛️ 사내 온톨로지 편입 제안 후보 (Ontology Candidates)",
            ])
            for i, c in enumerate(candidates, 1):
                c_title = c.get("title") or "무제 후보"
                c_type = c.get("candidateType") or c.get("candidate_type") or "신규 편입"
                c_rat = c.get("rationale") or "-"
                md.extend([
                    f"### [후보 {i}] {c_title} ({c_type})",
                    f"- **제안 사유 및 근거**: {c_rat}\n"
                ])

        # 8. 공인 출처 증빙 각주
        if evidence_feeds:
            md.extend([
                "## 7. 📚 공인 출처 증빙 원문 인용 및 신뢰도 각주 (Evidence Details)",
            ])
            for i, f in enumerate(evidence_feeds, 1):
                s_name = f.get("sourceName") or f.get("source_name") or "출처"
                pub = f.get("publisher") or "공인 기관"
                tier = f.get("credibilityTier") or f.get("credibility_tier") or "Tier 1"
                quote = f.get("quote") or ""
                url = f.get("externalUrl") or f.get("external_url") or "#"
                md.extend([
                    f"- **[E-{i:02d}] {s_name}** ({pub}, {tier})",
                    f"  - *핵심 인용*: \"{quote}\"",
                    f"  - *원문 링크*: [공식 PDF 열람]({url})"
                ])

        return "\n".join(md)

    @staticmethod
    def render_comparison_report(
        session_title: str,
        user_id: str,
        target_a_title: str,
        target_b_title: str,
        matrix_rows: List[Dict[str, Any]],
        tuning_recipes: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Tab 2 비교 분석 매트릭스 및 보상 레시피 마크다운을 렌더링합니다."""
        now_str = datetime.utcnow().strftime("%Y.%m.%d")
        md = [
            f"# ⚖️ [기술 대안 심층 비교분석 리포트] {target_a_title} vs {target_b_title}",
            f"- **비교 테마**: {session_title}",
            f"- **작성 엔지니어**: {user_id} | **생성 일시**: {now_str}",
            "\n---\n",
            "## 1. 📊 기술 대안 가로 대조 매트릭스 (Comparison Matrix)",
            f"| 평가 축 (Axis) | 분류 (Category) | {target_a_title} | {target_b_title} |",
            "| :--- | :--- | :--- | :--- |"
        ]

        for r in matrix_rows:
            axis = r.get("axisName") or r.get("axis_name") or "-"
            cat = r.get("category") or "-"
            cell_a = r.get("targetA") or {}
            cell_b = r.get("targetB") or {}
            val_a = f"{cell_a.get('value', '-')} {cell_a.get('unit', '')}".strip()
            val_b = f"{cell_b.get('value', '-')} {cell_b.get('unit', '')}".strip()
            md.append(f"| **{axis}** | {cat} | {val_a} | {val_b} |")

        md.append("\n")

        if tuning_recipes:
            md.extend([
                "## 2. 🛠️ AI 설비 한계 극복 보상 레시피 (Tuning Recipes)",
            ])
            for i, recipe in enumerate(tuning_recipes, 1):
                plan_type = recipe.get("planType") or recipe.get("plan_type") or "추천안"
                param = recipe.get("parameterName") or recipe.get("parameter_name") or "-"
                val = recipe.get("recommendedValue") or recipe.get("recommended_value") or "-"
                unit = recipe.get("unit") or ""
                tradeoff = recipe.get("expectedTradeoff") or recipe.get("expected_tradeoff") or "-"
                md.extend([
                    f"### [플랜 {i}] {plan_type}: {param}",
                    f"- **추천 튜닝 수치**: `{val} {unit}`",
                    f"- **예상 상충 페널티**: {tradeoff}\n"
                ])

        return "\n".join(md)

    @staticmethod
    def create_file_response(filename: str, content: str) -> Response:
        """마크다운 다운로드용 HTTP 응답 객체를 생성합니다."""
        return Response(
            content=content.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )


report_renderer = ReportRenderer()

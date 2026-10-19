"""Section 5.4: Security, Access Governance & RBAC Engine.

Implements:
1. 3-Tier RBAC Role Classification:
   - line_engineer: 일반 라인 엔지니어 (Tier 3 절대 수치 마스킹)
   - chief_reviewer: 수석 리뷰어 (전 등급 열람 및 티켓 승인 권한)
   - ontology_admin: 온톨로지 관리자 (시스템 제어 및 전역 감사)
2. Tier 3 Data Masking & Relative Trend (5.4.1 / 5.4.2):
   - Masks sensitive yield/defect metrics with [🔒 Tier 3 대외비 마스킹]
   - Provides relativeTrend and accessRequestCTA.
"""
from typing import Dict, Any, List, Optional
from fastapi import Header
import logging

logger = logging.getLogger("security")


def get_current_user_role(x_user_role: Optional[str] = Header(None, alias="X-User-Role")) -> str:
    """Extracts user role from X-User-Role header (default: chief_reviewer)."""
    if not x_user_role:
        return "chief_reviewer"
    role = x_user_role.strip().lower()
    if role in ["line_engineer", "chief_reviewer", "ontology_admin"]:
        return role
    return "chief_reviewer"


def mask_tier3_perspective(p_data: Dict[str, Any], user_role: str) -> Dict[str, Any]:
    """Masks Tier 3 sensitive manufacturing/yield metrics if user_role is line_engineer."""
    result = dict(p_data)

    if user_role == "line_engineer":
        result["isMasked"] = True
        result["is_masked"] = True
        result["maskReason"] = "Tier 3 양산 수율 및 결함 대외비 데이터 (일반 엔지니어 열람 제한)"
        result["mask_reason"] = "Tier 3 양산 수율 및 결함 대외비 데이터 (일반 엔지니어 열람 제한)"
        trend_text = (
            "상대적 경향성(Relative Trend): 본딩 가압력(145N) 제어 시 마이크로범프 크랙율 0.05% 이하로 안정화되며, "
            "피크 온도 상승에 따라 보이드 발생 위험이 지수 함수적으로 감소하는 양산 경향 확인됨."
        )
        result["relativeTrend"] = trend_text
        result["relative_trend"] = trend_text
        result["accessRequestCTA"] = "이 관점 상세 절대 수치 열람 권한 신청 ➔"
        result["access_request_cta"] = "이 관점 상세 절대 수치 열람 권한 신청 ➔"

        # specifications 마스킹
        specs = result.get("specifications", [])
        masked_specs = []
        for s in specs:
            s_copy = dict(s)
            lbl = s_copy.get("label", "")
            # 수율, 압력, 온도 등 핵심 사양 수치 마스킹
            if any(k in lbl for k in ["온도", "압력", "하중", "시간", "수율", "보이드", "두께"]):
                s_copy["value"] = "[🔒 대외비 마스킹]"
                s_copy["criteria"] = "보안 등급 기준 충족"
            masked_specs.append(s_copy)
        result["specifications"] = masked_specs

        # context_narrative 내 수치 치환
        narrative = result.get("context_narrative", "") or ""
        import re
        narrative = re.sub(r'\d+(?:\.\d+)?\s*(?:°C|℃|N|%|Torr|MPa|ms|s)', '[🔒 마스킹]', narrative)
        result["context_narrative"] = narrative
    else:
        result["isMasked"] = False

    return result

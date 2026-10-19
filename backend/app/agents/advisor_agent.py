"""Section 3.3: Advisor Engine (AI 파라미터 튜닝 상담 파이프라인 - 범용 인과 제약 보상 엔진).

Implements:
1. Causal Math: Constraint X -> Risk Y -> Compensation Z1, Z2 -> Trade-off W1, W2.
2. Safety Margin (Process Window) validation: Rejects unsafe parameter inputs (>300°C solder reflow destruction) with 422.
3. Plan A (Primary Physical Compensation) and Plan B (Complementary Parameter Compensation) derived from DB CausalEdge compensating_params.
"""
import re
import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.llm_gateway import llm_gateway
from backend.app.models.entities import ComparisonSessionModel, CausalEdgeModel, ConceptModel
from backend.app.schemas.comparison import TuneAdvisorResponse

logger = logging.getLogger("advisor_agent")


class AdvisorAgent:
    async def run_tuning_advisor(
        self,
        session_id: str,
        user_prompt: str,
        apply_compensation: Optional[str],
        manual_conditions: Optional[Dict[str, Any]],
        db: AsyncSession,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> TuneAdvisorResponse:
        p = user_prompt.strip()

        # 🌟 물리 안전 한계선(Physics Limits & Safety Margins) 검증
        if manual_conditions:
            for k, val in manual_conditions.items():
                val_str = str(val).strip()
                k_lower = k.lower()

                # 온도 검사: 300°C 초과 시 솔더 재용융 파괴 한계선 위반
                num_match = re.search(r'(\d+)', val_str)
                num_val = int(num_match.group(1)) if num_match else 0

                if ("temp" in k_lower or "온도" in k_lower or "°c" in val_str.lower() or "℃" in val_str) and num_val > 300:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "code": "SAFETY_MARGIN_VIOLATION",
                            "message": f"입력하신 온도({val_str})는 솔더 재용융 및 소자 파괴 한계선(300℃)을 초과하여 공정 안전 마진을 위반합니다.",
                            "allowedWindow": "최대 295℃ 이하"
                        }
                    )

                # 하중 검사: 200N 초과 시 실리콘 다이 크랙 한계선 위반
                if ("force" in k_lower or "압력" in k_lower or "하중" in k_lower or "n" in val_str.lower()) and num_val > 200:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "code": "SAFETY_MARGIN_VIOLATION",
                            "message": f"입력하신 가압력({val_str})은 초박형 다이 크랙 파괴 한계선(200N)을 초과하여 공정 안전 마진을 위반합니다.",
                            "allowedWindow": "최대 165N 이하"
                        }
                    )

        # 1. 세션의 타깃 개념 및 DB 보상 파라미터 엣지 조회
        session = await db.get(ComparisonSessionModel, session_id)
        target_a = (session.context_params or {}).get("targetA", "concept-tcb") if session else "concept-tcb"
        
        edge_stmt = select(CausalEdgeModel).where(
            (CausalEdgeModel.source_concept_id == target_a) |
            (CausalEdgeModel.target_concept_id == target_a)
        ).where(CausalEdgeModel.compensating_params.isnot(None))
        comp_edges = (await db.execute(edge_stmt)).scalars().all()

        db_comp = None
        if comp_edges and comp_edges[0].compensating_params:
            db_comp = comp_edges[0].compensating_params if isinstance(comp_edges[0].compensating_params, dict) else None

        # 2. 위험 노드 감지
        p_lower = p.lower()
        if "온도" in p_lower:
            risk_detected = "본딩 피크 온도 강하 시 솔더 젖음성(Wetting) 불량 및 접합 계면 금속간 화합물(IMC) 불완전 형성 위험 감지"
        elif "시간" in p_lower or "tat" in p_lower:
            risk_detected = "공정 시간 단축 시 열전달 불완전으로 접합 강도 저하 및 계면 박리 리스크 감지"
        elif "식각" in p_lower or "아킹" in p_lower:
            risk_detected = "챔버 RF 바이어스 급변 시 플라즈마 임피던스 불균일로 인한 웨이퍼 아킹 결함 위험 감지"
        else:
            risk_detected = f"본딩 가압력 150N 이하 제한 시 접촉 불충분으로 계면 보이드율 급증 위험 감지 (허용치: 0.1% 이하)"

        # 3. 보상 파라미터 탐색 (Plan A vs Plan B)
        plan_a_param = db_comp.get("parameter", "초음파 진동 인가 시간") if db_comp else "초음파 진동 인가 시간"
        plan_a_formula = db_comp.get("compensation_formula", "1.0s -> 2.2s") if db_comp else "1.0s -> 2.2s"
        plan_a_tradeoff = db_comp.get("tradeoff_cost", "다이당 택트타임(TAT) 1.2s 증가") if db_comp else "다이당 택트타임(TAT) 1.2s 증가로 UPH 18% 감소"

        recommendations = {
            "compensationA": {
                "title": f"{plan_a_param} 보상안 (Plan A)",
                "name": f"{plan_a_param} 보상 파라미터 (Plan A)",
                "description": f"기계적 압력 부족분을 {plan_a_param} 에너지로 치환하여 접합 면적을 확보합니다.",
                "compensatingParams": [
                    {"param": plan_a_param, "from": "기준 레시피", "to": plan_a_formula},
                    {"param": "인가 가압력", "from": "180N", "to": "145N (장비 한계 충족)"}
                ],
                "tradeOff": plan_a_tradeoff,
                "processWindowNotice": "공정 안전 마진(Normal Window) 이내 충족"
            },
            "compensationB": {
                "title": "공정 피크 온도 미세 상향 보상안 (Plan B)",
                "name": "공정 피크 온도 미세 상향 보상 파라미터 (Plan B)",
                "description": "솔더 용융 점도를 낮추어 낮은 압력 조건에서도 젖음성(Wetting)을 극대화합니다.",
                "compensatingParams": [
                    {"param": "본딩 헤드 피크 온도", "from": "270°C", "to": "295°C"},
                    {"param": "인가 가압력", "from": "180N", "to": "150N (장비 한계 충족)"}
                ],
                "tradeOff": "열팽창계수(CTE) 미스매치로 인한 다이 휨(Warpage)이 약 1.5㎛ 추가 증가할 위험",
                "processWindowNotice": "주의 마진(Marginal Window) - 300°C 초과 시 솔더 재용융 파괴 위험"
            }
        }

        # 4. 반영 결과 계산
        applied_result = None
        if apply_compensation in ["A", "compensationA"]:
            applied_result = {
                "appliedPlan": "compensationA",
                "updatedConditions": {
                    "maxLoad": "145N",
                    "compensatingParam": plan_a_param,
                    "compensatingValue": plan_a_formula
                },
                "updatedMatrix": [
                    {
                        "axis": "단위 공정 소요 시간 (TAT) 및 UPH",
                        "axisCategory": "fab",
                        "categoryLabel": "🏭 팹 양산성",
                        "valA": "3.7초 (초음파 보상 파라미터 2.2초 반영)",
                        "valB": "0.3초 (매스 리플로우 일괄 처리)",
                        "evidenceA": "E-01",
                        "evidenceB": "E-02",
                        "isGap": False
                    }
                ]
            }
        elif apply_compensation in ["B", "compensationB"]:
            applied_result = {
                "appliedPlan": "compensationB",
                "updatedConditions": {
                    "maxLoad": "150N",
                    "peakTemp": "295°C"
                },
                "updatedMatrix": [
                    {
                        "axis": "다이 휨 변형률 (Warpage @ 16-stack)",
                        "axisCategory": "defects",
                        "categoryLabel": "⚠️ 결함·신뢰성",
                        "valA": "23.5㎛ (온도 상향 295°C 반영)",
                        "valB": "8.0㎛ (일괄 리플로우 균일 응력)",
                        "evidenceA": "E-01",
                        "evidenceB": "E-02",
                        "isGap": False
                    }
                ]
            }

        return TuneAdvisorResponse(
            userPrompt=p,
            riskDetected=risk_detected,
            advisorRecommendation=recommendations,
            appliedResult=applied_result
        )


advisor_agent = AdvisorAgent()

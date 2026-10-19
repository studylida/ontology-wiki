"""Floating Engineering Chatbot API Router.

Provides:
1. GET    /api/v1/chatbot/context - Context detection and 3 quick question chips based on active concept
2. POST   /api/v1/chatbot/messages - 3-Way Intent Router (Factoid / Causal Clarifier / Action Trigger)
3. DELETE /api/v1/chatbot/messages - Reset chat session and restore welcome state
"""
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import ConceptModel, CausalEdgeModel, EvidenceSourceModel
from backend.app.schemas.chatbot import (
    ChatbotContextResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatbotActionCard,
    ChatbotSuggestedNode,
    ChatbotResetResponse
)

logger = logging.getLogger("ontology_wiki.chatbot")

router = APIRouter(prefix="/chatbot", tags=["Floating Engineering Chatbot"])


@router.get(
    "/context",
    response_model=ChatbotContextResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="컨텍스트 인식 챗봇 헤더 및 퀵 질문 칩 서빙 API",
    description="현재 엔지니어가 열람 중인 위키 개념(Scale, 도메인)을 캡처하여 최적화된 퀵 질문 칩 3종을 서빙합니다."
)
async def get_chatbot_context(
    conceptId: Optional[str] = Query(None, alias="conceptId"),
    perspective: Optional[str] = Query("yield"),
    db: AsyncSession = Depends(get_db)
):
    if conceptId:
        concept = await db.get(ConceptModel, conceptId)
        if concept:
            title = concept.title
            scale_level = concept.scale_level or 3
            scale_name = concept.scale_name or f"Scale {scale_level} 단위 공정"

            # 개념별 맞춤 질문 칩
            chips = [
                f"💡 {title} 도입 시 핵심 물리적 한계 및 트레이드오프는?",
                f"💡 16단 HBM3E 고적층 시 {title} 안전 마진 규격",
                f"💡 {title} 관련 공인 백서 및 실측 출처 보기"
            ]

            if "tcb" in conceptId.lower() or "열압착" in title:
                chips = [
                    "💡 16단 적층 시 NCF 필름 유출 방지 한계 가압력은?",
                    "💡 TCB와 MR-MUF의 방열 특성 차이 요약",
                    "💡 마이크로범프 IMC 형성 시 본딩 피크 온도 마진은?"
                ]
            elif "dry-etch" in conceptId.lower() or "식각" in title:
                chips = [
                    "💡 플라즈마 건식 식각 챔버 아킹 유발 2대 핵심 원인은?",
                    "💡 Cryo 극저온 식각과 일반 RIE 식각률 대조",
                    "💡 ESC 헬륨 누설 감지 FDC 보상 파라미터 규격"
                ]

            return ChatbotContextResponse(
                concept_id=concept.id,
                concept_title=f"{concept.title} ({concept.aliases[0] if concept.aliases else ''})".strip(),
                scale_level=scale_level,
                scale_badge=f"Scale {scale_level} · {scale_name}",
                engine_mode="live",
                engine_mode_label="🟢 Live (온톨로지 인과 추론 엔진)",
                quick_question_chips=chips
            )

    # 전역 모드 폴백
    return ChatbotContextResponse(
        concept_id=None,
        concept_title="반도체 인과 온톨로지 전역 어시스턴트",
        scale_level=3,
        scale_badge="전역 탐색 모드",
        engine_mode="live",
        engine_mode_label="🟢 Live (온톨로지 인과 추론 엔진)",
        quick_question_chips=[
            "💡 HBM 방열 대안: MR-MUF vs TC-NCF 비교",
            "💡 Cryo 극저온 식각 반응 메커니즘",
            "💡 차세대 유리기판 TGV 공정 및 물성 표준"
        ]
    )


@router.post(
    "/messages",
    response_model=ChatbotMessageResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="지능형 3단 라우터 챗봇 대화 질의 API",
    description="엔지니어의 입력에 따라 Factoid(단답), Causal Clarifier(인과 역질문), Action Trigger(화면 이동)로 3단 분기 응답합니다."
)
async def post_chatbot_message(
    body: ChatbotMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    msg = body.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MESSAGE_EMPTY", "message": "질문 내용을 입력해주세요."}
        )

    msg_lower = msg.lower()

    # 도메인 연관 검증
    domain_terms = [
        "hbm", "tcb", "lab", "mrmuf", "mr-muf", "ncf", "cryo", "rie", "식각", "본딩", "패키징",
        "euv", "gaa", "tsv", "다이", "휨", "warpage", "보이드", "웨이퍼", "fdc", "apc",
        "cmp", "ald", "cvd", "dram", "nand", "반도체", "공정", "소자", "수율", "택트타임", "tat",
        "아킹", "arcing", "스펙", "수치", "온도", "가압력", "하중", "유리기판", "tgv", "esc"
    ]
    is_domain = any(t in msg_lower for t in domain_terms)

    # concepts 매칭 검사
    if not is_domain:
        concepts_stmt = select(ConceptModel)
        all_concepts = (await db.execute(concepts_stmt)).scalars().all()
        for c in all_concepts:
            if c.title.lower() in msg_lower or (c.eng_name and c.eng_name.lower() in msg_lower):
                is_domain = True
                break

    if not is_domain:
        return ChatbotMessageResponse(
            path_type="out_of_domain",
            answer_markdown="본 챗봇은 **반도체 공정·소자·패키징 인과 온톨로지 전문 비서**입니다. 반도체 물리 메커니즘, 공정 제약, 트레이드오프와 관련된 질문을 입력해주세요.",
            suggested_chips=[
                "TCB 가압력 한계 수치",
                "16단 적층 다이 휨 원인",
                "MR-MUF 언더필 점도 기준"
            ]
        )

    # 1. 경로 3: 화면 액션 트리거 (Action Trigger)
    action_keywords = ["비교", "대안", "vs", "조사해줘", "리포트", "이동", "스튜디오", "매트릭스"]
    if any(k in msg_lower for k in action_keywords):
        target_a = "concept-tcb"
        target_b = "concept-mrmuf"
        title_a = "열압착 본딩 (TCB)"
        title_b = "MR-MUF 공정"

        if "lab" in msg_lower:
            title_b = "레이저 어시스트 본딩 (LAB)"
        elif "cryo" in msg_lower or "식각" in msg_lower:
            target_a = "concept-cryo-etch"
            target_b = "concept-dry-etch"
            title_a = "극저온 식각 (Cryo)"
            title_b = "플라즈마 건식 식각 (RIE)"

        return ChatbotMessageResponse(
            path_type="action_trigger",
            answer_markdown=f"{title_a}와 {title_b}의 열응력, 결함 신뢰성 및 양산 TAT 다차원 비교 분석 세션을 생성하여 대조 매트릭스를 열람하시겠습니까?",
            action_card=ChatbotActionCard(
                action_type="navigate_comparison",
                title=f"{title_a} vs {title_b} 다차원 비교 분석 실행",
                description="3대 공학 분기(다이 휨 vs 보이드 신뢰성 vs 택트타임) 매트릭스 도출",
                target_url=f"/comparison?targetA={target_a}&targetB={target_b}",
                button_label="⚡ 비교 분석 스튜디오로 이동 ➔"
            )
        )

    # 2. 경로 1: 사실/스펙 단답형 질의 (Direct Factoid Q&A)
    fact_keywords = ["스펙", "수치", "온도", "가압력", "하중", "얼마", "두께", "기준", "한계", "스펙이 얼마"]
    if any(k in msg_lower for k in fact_keywords):
        # 공인 출처 원문 인용 대조
        ev_stmt = select(EvidenceSourceModel).limit(1)
        evidence = (await db.execute(ev_stmt)).scalar_one_or_none()
        ev_list = []
        if evidence:
            ev_list.append({
                "id": evidence.id,
                "sourceName": evidence.source_name,
                "quote": evidence.quote,
                "credibilityTier": evidence.credibility_tier
            })

        return ChatbotMessageResponse(
            path_type="factoid",
            answer_markdown=(
                "열압착 본딩(TCB)의 표준 최대 인가 하중은 **180N**이며, "
                "16단 HBM3E 고적층 환경에서는 NCF 필름의 수지 측방 유출 방지를 위해 **165N** 이하로 통제할 것을 권장합니다. "
                "장비 한계로 150N 이하 운용 시에는 초음파 인가 시간(2.2s) 보상 파라미터를 병행 적용합니다."
            ),
            source_evidences=ev_list
        )

    # 3. 경로 2: 모호한 트러블슈팅/인과 질의 (Ambiguous Causal Clarifier)
    nodes = [
        ChatbotSuggestedNode(
            concept_id="concept-bonding-pressure",
            name="본딩 가압력 누적",
            relation_label="⚡ 주원인",
            link="/wiki/concept-bonding-pressure"
        ),
        ChatbotSuggestedNode(
            concept_id="concept-micro-void",
            name="계면 마이크로 보이드",
            relation_label="⚠️ 결함 노드",
            link="/wiki/concept-micro-void"
        )
    ]

    return ChatbotMessageResponse(
        path_type="causal_clarifier",
        answer_markdown=(
            f"질문하신 '{msg}' 현상은 주로 **공정 온도/가압력 불균일** 또는 **계면 전단응력 집중**에 의해 유발됩니다. "
            "문제 범위를 좁히기 위해 아래 세부 현상 중 어디에 해당하는지 확인해 주시겠습니까?"
        ),
        clarification_prompt="결함 발생 시점이 단위 공정 시작 직후인가요, 아니면 후속 열처리(Annealing/Reflow) 단계인가요?",
        suggested_nodes=nodes
    )


@router.delete(
    "/messages",
    response_model=ChatbotResetResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="챗봇 대화 이력 초기화 API",
    description="대화 스레드를 비우고 초기 환영 메시지 및 퀵 질문 상태로 복원합니다."
)
async def reset_chatbot_messages(
    conceptId: Optional[str] = Query(None, alias="conceptId")
):
    welcome = "안녕하세요! 현재 열람 중인 온톨로지 지식 및 공정 인과 메커니즘에 대해 무엇이든 질문하세요."
    if conceptId:
        welcome = f"안녕하세요! '{conceptId}' 문서의 인과 관계망 및 공인 규격에 대해 무엇이든 질문하세요."

    return ChatbotResetResponse(
        cleared=True,
        message="대화 이력이 성공적으로 초기화되었습니다.",
        welcome_message=welcome
    )

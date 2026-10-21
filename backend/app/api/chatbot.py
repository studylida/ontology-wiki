"""Floating Engineering Chatbot API Router.

Provides:
1. GET    /api/v1/chatbot/context - Context detection and 3 quick question chips based on active concept
2. POST   /api/v1/chatbot/messages - 3-Way Intent Router (Factoid / Causal Clarifier / Action Trigger) via ClarifierAgent
3. POST   /api/v1/chatbot/messages/stream - SSE Real-time Token Streaming via ClarifierAgent
4. DELETE /api/v1/chatbot/messages - Reset chat session and restore welcome state
"""
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import ConceptModel
from backend.app.schemas.chatbot import (
    ChatbotContextResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatbotResetResponse
)
from backend.app.agents.clarifier_agent import clarifier_agent

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

            chips = [
                f"💡 {title} 핵심 물리 임계치 및 트레이드오프는?",
                f"💡 {title} 안전 마진 및 보상 파라미터 규격",
                f"💡 {title} 관련 공인 백서 및 실측 출처 보기"
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
    description="엔지니어의 입력에 따라 ClarifierAgent를 통해 Factoid(단답), Causal Clarifier(인과 역질문), Action Trigger(화면 이동)로 3단 분기 응답합니다."
)
async def post_chatbot_message(
    body: ChatbotMessageRequest,
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    msg = body.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MESSAGE_EMPTY", "message": "질문 내용을 입력해주세요."}
        )

    # 🌟 3.1절 ClarifierAgent로 100% 위임
    return await clarifier_agent.route_chatbot_intent(
        utterance=msg,
        concept_id=body.conceptId,
        db=db,
        gemini_key=x_gemini_key,
        openai_key=x_openai_key
    )


@router.post("/messages/stream")
async def stream_chatbot_message(
    body: ChatbotMessageRequest,
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    """5.2.2 Server-Sent Events (SSE) Chatbot Real-time Token Streaming."""
    import json
    import asyncio
    from fastapi.responses import StreamingResponse

    msg = body.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MESSAGE_EMPTY", "message": "질문 내용을 입력해주세요."}
        )

    async def token_generator():
        res = await clarifier_agent.route_chatbot_intent(
            utterance=msg,
            concept_id=body.conceptId,
            db=db,
            gemini_key=x_gemini_key,
            openai_key=x_openai_key
        )

        # 1. 의도 라우팅 알림
        path_type = res.pathType
        yield f"event: routing\ndata: {json.dumps({'intent': path_type, 'pathType': path_type})}\n\n"
        await asyncio.sleep(0.04)

        # 2. 텍스트 토큰 스트리밍
        text = res.answerMarkdown or ""
        words = text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"event: delta\ndata: {json.dumps({'delta': chunk})}\n\n"
            await asyncio.sleep(0.015)

        # 3. 완료 및 액션 카드 이벤트
        yield f"event: done\ndata: {json.dumps(res.model_dump(by_alias=True))}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
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

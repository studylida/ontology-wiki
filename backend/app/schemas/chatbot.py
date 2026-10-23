"""Floating Engineering Chatbot Schemas.

Covers Context Detection, 3-Way Intent Routing (Factoid / Causal Clarifier / Action Trigger), and Reset.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ChatbotContextResponse(BaseModel):
    """현재 위키 열람 개념 기반 챗봇 컨텍스트 및 퀵 질문 칩 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    conceptId: Optional[str] = Field(None, alias="concept_id", serialization_alias="conceptId")
    conceptTitle: str = Field(..., alias="concept_title", serialization_alias="conceptTitle")
    scaleLevel: Optional[int] = Field(None, alias="scale_level", serialization_alias="scaleLevel")
    scaleBadge: str = Field("전역 탐색 모드", alias="scale_badge", serialization_alias="scaleBadge")
    engineMode: str = Field("wiki", alias="engine_mode", serialization_alias="engineMode")
    engineModeLabel: str = Field("위키 등록 지식 기반", alias="engine_mode_label", serialization_alias="engineModeLabel")
    quickQuestionChips: List[str] = Field(..., alias="quick_question_chips", serialization_alias="quickQuestionChips")


class ChatbotMessageRequest(BaseModel):
    """엔지니어 챗봇 대화 입력 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    message: str = Field(..., min_length=1, description="엔지니어 자연어 질의")
    knowledgeScope: Literal["local", "global"] = "local"
    conceptId: Optional[str] = Field(None, alias="concept_id", serialization_alias="conceptId")
    targetConceptId: Optional[str] = Field(None, alias="target_concept_id", serialization_alias="targetConceptId")
    perspective: Optional[str] = "process"
    currentUrlContext: Optional[str] = Field(None, alias="current_url_context", serialization_alias="currentUrlContext")


class ChatbotActionCard(BaseModel):
    """화면 전환 액션 트리거 카드 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    actionType: str = Field(..., alias="action_type", serialization_alias="actionType")
    title: str
    description: str
    targetUrl: str = Field(..., alias="target_url", serialization_alias="targetUrl")
    buttonLabel: str = Field(..., alias="button_label", serialization_alias="buttonLabel")


class ChatbotSuggestedNode(BaseModel):
    """인과 탐색 연관 노드 칩 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    name: str
    relationLabel: str = Field(..., alias="relation_label", serialization_alias="relationLabel")
    link: str


class ChatbotMessageResponse(BaseModel):
    """3대 경로 분기형 챗봇 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True, arbitrary_types_allowed=True)

    pathType: Any = Field(..., alias="path_type", serialization_alias="pathType")
    answerMarkdown: str = Field(..., alias="answer_markdown", serialization_alias="answerMarkdown")
    knowledgeScope: Literal["local", "global"] = "local"
    clarificationPrompt: Optional[str] = Field(None, alias="clarification_prompt", serialization_alias="clarificationPrompt")
    sourceEvidences: List[Dict[str, Any]] = Field(default_factory=list, alias="source_evidences", serialization_alias="sourceEvidences")
    suggestedNodes: List[ChatbotSuggestedNode] = Field(default_factory=list, alias="suggested_nodes", serialization_alias="suggestedNodes")
    suggestedChips: List[str] = Field(default_factory=list, alias="suggested_chips", serialization_alias="suggestedChips")
    actionCard: Optional[ChatbotActionCard] = Field(None, alias="action_card", serialization_alias="actionCard")


class GlobalChatAnswer(BaseModel):
    domain: Literal["semiconductor", "out_of_domain"]
    answerMarkdown: str = Field(..., min_length=1)


class ChatbotResetResponse(BaseModel):
    """대화 이력 초기화 완료 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    cleared: bool = True
    message: str
    welcomeMessage: str = Field(..., alias="welcome_message", serialization_alias="welcomeMessage")

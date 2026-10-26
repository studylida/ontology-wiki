import json

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from ..core.errors import AppError
from ..identity.dependencies import current_principal
from ..rag.dto import AnswerRequest
from .dto import ClientMetricsRequest

router = APIRouter(tags=["answers"])


@router.post("/answer-runs", status_code=202)
async def create_run(body: AnswerRequest, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.create(principal, body)


@router.post("/conversations/{conversation_id}/turns", status_code=202)
async def create_turn(conversation_id: str, body: AnswerRequest, request: Request, principal=Depends(current_principal)):
    if body.conversation_id and body.conversation_id != conversation_id:
        raise AppError(422, "CONVERSATION_MISMATCH", "URL과 요청의 대화 ID가 다릅니다.")
    return await request.app.state.services.answers.create(principal, body.model_copy(update={"conversation_id": conversation_id}))


@router.get("/answer-runs/{run_id}")
async def get_run(run_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.get(principal, run_id)


@router.post("/answer-runs/{run_id}/cancel")
async def cancel(run_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.cancel(principal, run_id)


@router.post("/answer-runs/{run_id}/client-metrics")
async def client_metrics(run_id: str, body: ClientMetricsRequest, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.record_client_metrics(principal, run_id, body.first_visible_text_ms)


@router.get("/answer-runs/{run_id}/events")
async def events(run_id: str, request: Request, after: int = Query(0, ge=0), principal=Depends(current_principal)):
    service = request.app.state.services.answers
    await service.check_stream(principal, run_id, after)

    async def stream():
        async for event in service.event_stream(principal, run_id, after, request.is_disconnected):
            if event is None:
                yield ": keep-alive\n\n"
            else:
                yield f"id: {event['seq']}\nevent: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"})

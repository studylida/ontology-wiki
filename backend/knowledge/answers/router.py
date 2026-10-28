import json
from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse
from knowledge.core.errors import AppError
from knowledge.identity.dependencies import current_principal
from .dto import AnswerRequest, RetryRequest, TurnRequest

router = APIRouter(tags=['answers'])


@router.post('/answer-runs', status_code=202)
async def create_run(body: AnswerRequest, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.create(principal, body)


@router.post('/conversations/{conversation_id}/turns', status_code=202)
async def create_turn(conversation_id: str, body: TurnRequest, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.create(principal,
        AnswerRequest(conversation_id=conversation_id, **body.model_dump()))


@router.get('/answer-runs/{run_id}')
async def get_run(run_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.get(principal, run_id)


@router.post('/answer-runs/{run_id}/cancel')
async def cancel(run_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.cancel(principal, run_id)


@router.post('/answer-runs/{run_id}/retry', status_code=202)
async def retry(run_id: str, body: RetryRequest, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.answers.retry(principal, run_id, body)


@router.get('/answer-runs/{run_id}/events')
async def events(run_id: str, request: Request, after: int = Query(0, ge=0),
                 last_event_id: str | None = Header(None), principal=Depends(current_principal)):
    if last_event_id is not None:
        if not last_event_id.isascii() or not last_event_id.isdecimal() or len(last_event_id) > 12:
            raise AppError(422, 'invalid_event_cursor', 'Last-Event-ID는 저장된 이벤트의 정수 번호여야 합니다.')
        after = max(after, int(last_event_id))
    services = request.app.state.services
    await services.answers.check_stream(principal, run_id, after)
    token = request.headers.get('authorization', '').split(' ', 1)[-1]

    async def authenticate():
        return await services.identity.authenticate(token)

    async def stream():
        async for event in services.answers.event_stream(principal, run_id, after, request.is_disconnected, authenticate):
            if event is None:
                yield ': keep-alive\n\n'
            else:
                identity = f"id: {event['seq']}\n" if 'seq' in event else ''
                yield identity + f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(stream(), media_type='text/event-stream', headers={
        'Cache-Control': 'no-store, no-transform', 'X-Accel-Buffering': 'no'})

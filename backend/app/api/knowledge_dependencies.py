"""HTTP concerns shared by comparison and research controllers."""
from fastapi import Header, HTTPException


async def knowledge_errors():
    try:
        yield
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def llm_keys(x_gemini_key: str | None = Header(None), x_openai_key: str | None = Header(None)):
    return {"gemini_key": x_gemini_key, "openai_key": x_openai_key}

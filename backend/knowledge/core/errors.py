import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str,
                 details=None, retryable: bool = False):
        super().__init__(message)
        self.status_code, self.code, self.message = status_code, code, message
        self.details, self.retryable = details, retryable

    def public(self) -> dict:
        value = {"code": self.code, "message": self.message, "retryable": self.retryable}
        if self.details is not None:
            value["details"] = self.details
        return value


def install_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def domain_error(request: Request, exc: AppError):
        return JSONResponse({"error": exc.public()}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Do not echo request bodies (passwords, private text) through validation errors.
        details = [{"location": list(e["loc"]), "message": e["msg"], "type": e["type"]}
                   for e in exc.errors()]
        return JSONResponse({"error": {"code": "INVALID_REQUEST", "message": "요청 형식을 확인해 주세요.",
                                      "details": details, "retryable": False}}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse({"error": {"code": "HTTP_ERROR", "message": str(exc.detail),
                                      "retryable": False}}, status_code=exc.status_code,
                            headers=exc.headers)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        # Do not log SQL parameters, request text, authorization headers or keys.
        logging.getLogger("knowledge.api").error("request_failed error_type=%s", type(exc).__name__)
        return JSONResponse({"error": {"code": "INTERNAL_ERROR", "message": "요청 처리 중 오류가 발생했습니다.",
                                      "retryable": True}}, status_code=500)

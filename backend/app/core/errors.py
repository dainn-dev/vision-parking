from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details


def not_found(resource: str, ident: Any = None) -> ApiError:
    return ApiError(
        "NOT_FOUND",
        f"{resource} not found" + (f": {ident}" if ident is not None else ""),
        status.HTTP_404_NOT_FOUND,
    )


def forbidden(message: str = "Insufficient permissions") -> ApiError:
    return ApiError("FORBIDDEN", message, status.HTTP_403_FORBIDDEN)


def unauthorized(message: str = "Authentication required") -> ApiError:
    return ApiError("UNAUTHORIZED", message, status.HTTP_401_UNAUTHORIZED)


def conflict(code: str, message: str) -> ApiError:
    return ApiError(code, message, status.HTTP_409_CONFLICT)


def error_body(code: str, message: str, details: Any = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=error_body(exc.code, exc.message, exc.details),
    )

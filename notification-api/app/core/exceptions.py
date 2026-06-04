from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled {type(exc).__name__} on "
        f"{request.method} {request.url.path} - {exc}" 
    )

    return JSONResponse(
        status_code=500,
        content={
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred.",
            "details": []
        }
    )
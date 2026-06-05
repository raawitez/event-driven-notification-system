import time
import uuid
from fastapi import Request
from loguru import logger


async def log_requests(request: Request, call_next):

    request_id = str(uuid.uuid4())[:8]

    start = time.time()

    logger.info(
        f"[{request_id}] → {request.method} {request.url.path}"
    )


    response = await call_next(request)

    duration_ms = (time.time() - start) * 1000

    if response.status_code >= 500:
        log_fn = logger.error
    elif response.status_code >= 400:
        log_fn = logger.warning
    else:
        log_fn = logger.info

    log_fn(
        f"[{request_id}] ← {response.status_code} "
        f"{request.method} {request.url.path} "
        f"in {duration_ms:.1f}ms"
    )

    response.headers["X-Request-ID"] = request_id
    return response
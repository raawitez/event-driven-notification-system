from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.core.logger import setup_logger
from app.core.exceptions import global_exception_handler

setup_logger()

from app.database import Base, engine, SessionLocal
from app.models import notification_model          
from app.routers import auth_router, notification_router
from app.middleware.logging_middleware import log_requests
from app.cache.redis_client import check_redis
from app.messaging.rabbitmq_client import publisher


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("=" * 55)
    logger.info("Notification API — Starting Up")
    logger.info("=" * 55)


    Base.metadata.create_all(bind=engine)
    logger.info(" Database tables ready")

    redis_ok = check_redis()
    if not redis_ok:
        logger.warning("  Redis unavailable — status polling will use DB")

    publisher.connect()
    if publisher.channel:
        logger.info(" RabbitMQ publisher connected")
    else:
        logger.warning("  RabbitMQ unavailable — events will be skipped")

    logger.info("=" * 55)
    logger.info("API ready → http://localhost:8000/docs")
    logger.info("=" * 55)

    yield   

    logger.info("Shutting down...")
    publisher.disconnect()
    logger.info("Goodbye.")

app = FastAPI(
    title="Notification API",
    version="1.0",
    description="""
## Event-Driven Notification System

**How it works:**
1. Register and login to get a JWT token
2. POST /notify/ with token → notification queued
3. Worker processes notification asynchronously
4. GET /notify/{id} → check delivery status

**Tech stack:** FastAPI · SQLAlchemy · RabbitMQ · Redis · JWT
    """,
    lifespan=lifespan
)

app.middleware("http")(log_requests)

app.add_exception_handler(Exception, global_exception_handler)

app.include_router(auth_router.router)
app.include_router(notification_router.router)

@app.get("/health", tags=["Health"])
def health():
    from app.cache.redis_client import redis_client

    db_status    = "ok"
    redis_status = "ok"
    mq_status    = "ok" if publisher.channel else "error"

    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception:
        db_status = "error"

    try:
        redis_client.ping()
    except Exception:
        redis_status = "error"

    overall = (
        "healthy"
        if all(s == "ok" for s in [db_status, redis_status, mq_status])
        else "degraded"
    )

    return {
        "status":   overall,
        "database": db_status,
        "redis":    redis_status,
        "rabbitmq": mq_status
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "name":    "Notification API",
        "version": "1.0",
        "docs":    "/docs"
    }
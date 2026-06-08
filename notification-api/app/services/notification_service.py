from sqlalchemy.orm import Session
from fastapi import HTTPException
from loguru import logger

from app.models.notification_model import Notification
from app.cache.redis_client import (
    get_cache, set_cache, delete_cache,
    CACHE_NOTIFICATION, TTL_NOTIFICATION
)
from app.messaging.rabbitmq_client import publisher
from app.messaging.events import (
    QUEUE_NOTIFICATIONS,
    build_notification_event
)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: int,
        channel: str,
        message: str
    ) -> Notification:
        
        notification = Notification(
            user_id=user_id,
            channel=channel,
            message=message,
            status="queued"
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)  

        logger.info(
            f"Notification {notification.id} created — "
            f"channel={channel} user_id={user_id}"
        )

        event = build_notification_event(
            notification_id=notification.id,
            user_id=user_id,
            channel=channel,
            message=message
        )
        published = publisher.publish(QUEUE_NOTIFICATIONS, event)

        if not published:
            logger.warning(
                f"Notification {notification.id} saved to DB "
                f"but NOT published to RabbitMQ — "
                f"worker will not process until RabbitMQ is available"
            )

        cache_key = CACHE_NOTIFICATION.format(id=notification.id)
        set_cache(cache_key, {
            "id":      notification.id,
            "status":  "queued",
            "channel": channel
        })

        return notification

    def get_notification_status(self, notification_id: int) -> dict:
        cache_key = CACHE_NOTIFICATION.format(id=notification_id)

        cached = get_cache(cache_key)
        if cached:
            logger.info(f"Cache HIT — notification:{notification_id}")
            return cached

        logger.info(f"Cache MISS — querying DB for notification:{notification_id}")
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

        if not notification:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notification_id} not found"
            )

        result = {
            "id":      notification.id,
            "status":  notification.status,
            "channel": notification.channel
        }

        set_cache(cache_key, result)
        return result

    def update_notification_status(
        self,
        notification_id: int,
        status: str
    ):

        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

        if notification:
            notification.status = status
            self.db.commit()

            cache_key = CACHE_NOTIFICATION.format(id=notification_id)
            set_cache(cache_key, {
                "id":      notification_id,
                "status":  status,
                "channel": notification.channel
            })

            logger.info(
                f"Notification {notification_id} "
                f"status updated to '{status}'"
            )
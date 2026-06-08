import json
import time
import signal
import pika
from loguru import logger
from sqlalchemy.orm import Session

from app.core.logger import setup_logger
from app.database import SessionLocal, engine, Base
from app.models.notification_model import Notification
from app.cache.redis_client import set_cache, CACHE_NOTIFICATION
from app.messaging.events import QUEUE_NOTIFICATIONS

setup_logger()


def update_status(notification_id: int, status: str):
    db: Session = SessionLocal()
    try:
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )
        if notification:
            notification.status = status
            db.commit()

            cache_key = CACHE_NOTIFICATION.format(id=notification_id)
            set_cache(cache_key, {
                "id":      notification_id,
                "status":  status,
                "channel": notification.channel
            })

            logger.info(
                f"[WORKER] Notification {notification_id} "
                f"→ status updated to '{status}'"
            )
    finally:
        db.close()


def process_notification(event: dict):
    notification_id = event["notification_id"]
    channel         = event["channel"]
    message         = event["message"]
    user_id         = event["user_id"]

    logger.info(f"[WORKER] Processing notification {notification_id}")
    logger.info(f"[WORKER] Channel: {channel} | User: {user_id}")
    logger.info(f"[WORKER] Message: {message}")

    update_status(notification_id, "processing")

    if channel == "email":
        logger.info(f"[WORKER] Sending EMAIL to user {user_id}...")
        time.sleep(1.5)   
        logger.info(f"[WORKER] EMAIL sent successfully ")

    elif channel == "sms":
        logger.info(f"[WORKER] Sending SMS to user {user_id}...")
        time.sleep(0.8)   
        logger.info(f"[WORKER] SMS sent successfully ")

    update_status(notification_id, "delivered")


def on_message(ch, method, properties, body):
    logger.info(f"\n{'─' * 55}")
    logger.info(f"[WORKER] Message received from queue")

    try:
        event = json.loads(body.decode("utf-8"))

        logger.info(f"[WORKER] Event: {event.get('event')}")
        logger.info(f"[WORKER] Notification ID: {event.get('notification_id')}")

        process_notification(event)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"[WORKER] Message acknowledged ")

    except json.JSONDecodeError as e:
        logger.error(f"[WORKER] Invalid JSON: {e}")
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )

    except Exception as e:
        notification_id = None
        try:
            event = json.loads(body.decode("utf-8"))
            notification_id = event.get("notification_id")
        except Exception:
            pass

        logger.error(f"[WORKER] Processing failed: {e}")

        if notification_id:
            update_status(notification_id, "failed")

        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


def main():
    Base.metadata.create_all(bind=engine)

    logger.info("=" * 55)
    logger.info("Notification Worker — Starting")
    logger.info("=" * 55)

    logger.info("Connecting to RabbitMQ...")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="localhost",
            port=5672,
            heartbeat=600
        )
    )
    channel = connection.channel()
    logger.info(" Connected to RabbitMQ")

    channel.queue_declare(queue=QUEUE_NOTIFICATIONS, durable=True)
    logger.info(f" Queue '{QUEUE_NOTIFICATIONS}' ready")


    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NOTIFICATIONS,
        on_message_callback=on_message,
        auto_ack=False   
    )

    logger.info(f"Listening on '{QUEUE_NOTIFICATIONS}'")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 55)

    def shutdown(sig, frame):
        logger.info("Shutting down worker...")
        channel.stop_consuming()

    signal.signal(signal.SIGINT, shutdown)

    channel.start_consuming()
    connection.close()
    logger.info("Worker stopped.")


if __name__ == "__main__":
    main()
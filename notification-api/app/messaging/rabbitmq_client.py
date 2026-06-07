import json
import pika
from loguru import logger


class RabbitMQPublisher:

    def __init__(self):
        self.connection = None
        self.channel    = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host="localhost",
                    port=5672,
                    heartbeat=600
                )
            )
            self.channel = self.connection.channel()
            logger.info("RabbitMQ publisher connected")
        except Exception as e:
            logger.warning(f"RabbitMQ connection failed: {e}")
            self.connection = None
            self.channel    = None

    def disconnect(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ publisher disconnected")
        except Exception as e:
            logger.warning(f"RabbitMQ disconnect error: {e}")

    def publish(self, queue_name: str, event: dict) -> bool:
        if not self.channel:
            logger.warning(
                f"RabbitMQ unavailable — "
                f"event {event.get('event')} not published"
            )
            return False

        try:
            self.channel.queue_declare(
                queue=queue_name,
                durable=True
            )

            self.channel.basic_publish(
                exchange="",             
                routing_key=queue_name,  
                body=json.dumps(event),  
                properties=pika.BasicProperties(
                    delivery_mode=2      
                )
            )

            logger.info(
                f"[MQ] Published '{event.get('event')}' "
                f"notification_id={event.get('notification_id')}"
            )
            return True

        except Exception as e:
            logger.error(f"[MQ] Publish failed: {e}")
            self.connect()   
            return False


publisher = RabbitMQPublisher()
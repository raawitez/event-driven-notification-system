from datetime import datetime

QUEUE_NOTIFICATIONS = "notifications"

EVENT_NOTIFICATION_REQUESTED = "notification_requested"


def build_notification_event(
    notification_id: int,
    user_id:         int,
    channel:         str,
    message:         str
) -> dict:
    
    return {
        "event":           EVENT_NOTIFICATION_REQUESTED,
        "notification_id": notification_id,
        "user_id":         user_id,
        "channel":         channel,
        "message":         message,
        "timestamp":       datetime.utcnow().isoformat()
    }
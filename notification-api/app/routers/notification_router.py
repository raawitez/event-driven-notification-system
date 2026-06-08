from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.notification_schema import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus
)
from app.services.notification_service import NotificationService
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/notify", tags=["Notifications"])


def get_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=202,    
    summary="Request a notification"
)
def create_notification(
    body:         NotificationCreate,
    service:      NotificationService = Depends(get_service),
    current_user: dict = Depends(get_current_user)  
):
    notification = service.create_notification(
        user_id=body.user_id,
        channel=body.channel,
        message=body.message
    )
    return notification


@router.get(
    "/{notification_id}",
    response_model=NotificationStatus,
    summary="Check notification status"
)
def get_status(
    notification_id: int,
    service:         NotificationService = Depends(get_service)
):
    return service.get_notification_status(notification_id)
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    user_id: int = Field(
        ge=1,
        description="ID of the user to notify"
    )
    channel: str = Field(
        description="Delivery channel: email or sms"
    )
    message: str = Field(
        min_length=1,
        max_length=500,
        description="Notification message content"
    )


    from pydantic import field_validator

    @field_validator("channel")
    @classmethod
    def channel_must_be_valid(cls, v):
        if v not in ["email", "sms"]:
            raise ValueError("channel must be 'email' or 'sms'")
        return v


class NotificationResponse(BaseModel):
    id:         int
    user_id:    int
    channel:    str
    message:    str
    status:     str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationStatus(BaseModel):
    id:     int
    status: str
    channel: str

class UserRegister(BaseModel):
    email:    str = Field(min_length=3)
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
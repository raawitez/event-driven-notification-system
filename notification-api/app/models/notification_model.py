from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, nullable=False)
    channel    = Column(String(20), nullable=False) 
    message    = Column(String(500), nullable=False)
    status     = Column(String(20), default="queued", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return (
            f"<Notification id={self.id} "
            f"channel={self.channel} "
            f"status={self.status}>"
        )
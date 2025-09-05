from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.meeting_room_mcp.config.database_config import Base
from src.meeting_room_mcp.server.room.room_enum import RoomStatus
from src.meeting_room_mcp.shared.models import MeetingRoom


class MeetingRoomEntity(Base):
    """회의실 테이블"""
    __tablename__ = 'meeting_rooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String(100), nullable=False)
    equipment = Column(Text)
    status = Column(String(20), nullable=False, default='available')
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # 관계 설정
    reservations = relationship("ReservationEntity", back_populates="room")

    # 인덱스
    __table_args__ = (
        Index('idx_meeting_rooms_status', 'status'),
        Index('idx_meeting_rooms_capacity', 'capacity'),
    )

    def to_model(self) -> MeetingRoom:
        """엔티티를 모델로 변환"""
        return MeetingRoom(
            id=self.id,
            name=self.name,
            capacity=self.capacity,
            location=self.location,
            equipment=self.equipment or "",
            status=RoomStatus(self.status)
        )

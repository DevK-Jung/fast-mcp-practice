"""
SQLAlchemy 데이터베이스 엔티티 모델
"""

import json

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.meeting_room_mcp.config.database_config import Base
from src.meeting_room_mcp.shared.models import Reservation


class ReservationEntity(Base):
    """예약 테이블"""
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('meeting_rooms.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default='')
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    organizer_email = Column(String(255), nullable=False)
    participants = Column(Text, nullable=False)  # JSON 문자열
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # 관계 설정
    room = relationship("MeetingRoomEntity", back_populates="reservations")

    # 제약 조건 및 인덱스
    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_time_order'),
        Index('idx_reservations_room_time', 'room_id', 'start_time', 'end_time'),
        Index('idx_reservations_time_range', 'start_time', 'end_time'),
        Index('idx_reservations_organizer', 'organizer_email'),
    )

    def to_model(self) -> Reservation:
        """엔티티를 모델로 변환"""
        participants = json.loads(self.participants) if self.participants else []

        return Reservation(
            id=self.id,
            room_id=self.room_id,
            title=self.title,
            description=self.description or "",
            start_time=self.start_time,
            end_time=self.end_time,
            organizer_email=self.organizer_email,
            participants=participants,
            created_at=self.created_at
        )

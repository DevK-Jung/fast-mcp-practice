"""
공통 데이터 모델 정의
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.meeting_room_mcp.server.reservation.reservation_schemas import Reservation
from src.meeting_room_mcp.server.room.room_schemas import MeetingRoom


@dataclass
class ReservationSession:
    """예약 세션 모델 (대화형 예약용)"""
    session_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    organizer_email: Optional[str] = None
    participants: Optional[List[str]] = None
    room_id: Optional[int] = None
    min_capacity: Optional[int] = None
    step: str = "initial"
    available_rooms: List[MeetingRoom] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.available_rooms is None:
            self.available_rooms = []
        if self.participants is None:
            self.participants = []

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'session_id': self.session_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'organizer_email': self.organizer_email,
            'participants': self.participants,
            'room_id': self.room_id,
            'min_capacity': self.min_capacity,
            'step': self.step,
            'available_rooms': [
                {
                    'id': room.id,
                    'name': room.name,
                    'capacity': room.capacity,
                    'location': room.location,
                    'equipment': room.equipment
                } for room in self.available_rooms
            ],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ReservationSession':
        """딕셔너리에서 복원"""
        session = cls(session_id=data['session_id'])
        session.title = data.get('title')
        session.description = data.get('description')
        session.start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
        session.end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        session.organizer_email = data.get('organizer_email')
        session.participants = data.get('participants', [])
        session.room_id = data.get('room_id')
        session.min_capacity = data.get('min_capacity')
        session.step = data.get('step', 'initial')

        # available_rooms 복원
        if data.get('available_rooms'):
            session.available_rooms = [
                MeetingRoom(
                    id=room['id'],
                    name=room['name'],
                    capacity=room['capacity'],
                    location=room['location'],
                    equipment=room['equipment']
                ) for room in data['available_rooms']
            ]

        if data.get('created_at'):
            session.created_at = datetime.fromisoformat(data['created_at'])

        return session


@dataclass
class RoomSearchCriteria:
    """회의실 검색 조건"""
    start_time: datetime
    end_time: datetime
    min_capacity: int = 1
    equipment_required: Optional[List[str]] = None
    location_preference: Optional[str] = None

    def __post_init__(self):
        if self.equipment_required is None:
            self.equipment_required = []

    def matches_room(self, room: MeetingRoom) -> bool:
        """회의실이 검색 조건에 맞는지 확인"""
        if room.capacity < self.min_capacity:
            return False

        if self.location_preference and self.location_preference not in room.location:
            return False

        if self.equipment_required:
            room_equipment = room.equipment.lower()
            for required in self.equipment_required:
                if required.lower() not in room_equipment:
                    return False

        return True


@dataclass
class EmailNotification:
    """이메일 알림 모델"""
    to_emails: List[str]
    subject: str
    body: str
    reservation: Reservation
    room: MeetingRoom

    def __post_init__(self):
        if not self.subject:
            self.subject = f"[회의 알림] {self.reservation.title}"

        if not self.body:
            self.body = self._generate_default_body()

    def _generate_default_body(self) -> str:
        """기본 이메일 본문 생성"""
        return f"""
회의가 예약되었습니다.

📋 회의 정보:
• 제목: {self.reservation.title}
• 설명: {self.reservation.description}
• 일시: {self.reservation.start_time.strftime('%Y-%m-%d %H:%M')} ~ {self.reservation.end_time.strftime('%Y-%m-%d %H:%M')}
• 회의실: {self.room.name} ({self.room.location})
• 주최자: {self.reservation.organizer_email}
• 참가자: {', '.join(self.reservation.participants)}

🏢 회의실 정보:
• 수용인원: {self.room.capacity}명
• 장비: {self.room.equipment}

이 메일은 자동으로 발송된 메일입니다.
"""

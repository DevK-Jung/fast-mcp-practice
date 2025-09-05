from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Reservation:
    """예약 모델"""
    id: Optional[int]
    room_id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    organizer_email: str
    participants: List[str]
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def duration_hours(self) -> float:
        """회의 지속 시간 (시간 단위)"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600

    @property
    def participant_count(self) -> int:
        """참가자 수"""
        return len(self.participants)

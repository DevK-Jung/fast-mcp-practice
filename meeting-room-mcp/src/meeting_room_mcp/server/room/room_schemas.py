from dataclasses import dataclass

from src.meeting_room_mcp.server.room.room_enum import RoomStatus


@dataclass
class MeetingRoom:
    """회의실 모델"""
    id: int
    name: str
    capacity: int
    location: str
    equipment: str
    status: RoomStatus = RoomStatus.AVAILABLE

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = RoomStatus(self.status)

    @property
    def available(self) -> bool:
        return self.status == RoomStatus.AVAILABLE

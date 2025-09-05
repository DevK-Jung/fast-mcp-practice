"""
회의실 비즈니스 로직 서비스
"""

import logging
from datetime import datetime
from typing import List, Optional

from src.meeting_room_mcp.config.database_config import DatabaseConfig
from src.meeting_room_mcp.server.room.room_enum import RoomStatus
from src.meeting_room_mcp.server.room.room_repository import RoomRepository
from src.meeting_room_mcp.shared.models import MeetingRoom, RoomSearchCriteria

logger = logging.getLogger(__name__)


class RoomService:
    """회의실 비즈니스 로직"""

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config

    def search_available_rooms(
            self,
            start_time: datetime,
            end_time: datetime,
            min_capacity: int = 1,
            location_preference: str = "",
            equipment_required: List[str] = []
    ) -> List[MeetingRoom]:
        """사용 가능한 회의실 검색"""
        # 검색 조건 생성
        criteria = RoomSearchCriteria(
            start_time=start_time,
            end_time=end_time,
            min_capacity=min_capacity,
            equipment_required=equipment_required,
            location_preference=location_preference if location_preference else None
        )

        with self.db_config.get_session() as session:
            room_repo = RoomRepository(session)
            return room_repo.get_available_rooms(start_time, end_time, criteria)

    def get_room_info(self, room_id: int) -> Optional[MeetingRoom]:
        """회의실 상세 정보 조회"""
        with self.db_config.get_session() as session:
            room_repo = RoomRepository(session)
            return room_repo.get_by_id(room_id)

    def get_all_rooms(self) -> List[MeetingRoom]:
        """모든 회의실 목록 조회"""
        with self.db_config.get_session() as session:
            room_repo = RoomRepository(session)
            return room_repo.get_all()

    def update_room_status(self, room_id: int, status: RoomStatus) -> bool:
        """회의실 상태 업데이트"""
        with self.db_config.get_session() as session:
            room_repo = RoomRepository(session)
            return room_repo.update_status(room_id, status)

    def get_room_statistics(self) -> dict:
        """회의실 통계 정보"""
        with self.db_config.get_session() as session:
            room_repo = RoomRepository(session)

            total_rooms = room_repo.get_room_count()
            active_rooms = room_repo.get_active_room_count()

            return {
                'total_rooms': total_rooms,
                'active_rooms': active_rooms,
                'inactive_rooms': total_rooms - active_rooms
            }

    def initialize_sample_data(self):
        """샘플 데이터 초기화"""
        with self.db_config.get_session() as session:
            room_repo = RoomRepository(session)
            room_repo.insert_sample_data()

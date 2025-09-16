"""
회의실 데이터 접근 레이어
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.meeting_room_mcp.server.entities import ReservationEntity
from src.meeting_room_mcp.server.room.room_enum import RoomStatus
from src.meeting_room_mcp.server.room.room_models import MeetingRoomEntity
from src.meeting_room_mcp.shared.models import MeetingRoom, RoomSearchCriteria

logger = logging.getLogger(__name__)


class RoomRepository:
    """회의실 데이터 접근 객체"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, room_id: int) -> Optional[MeetingRoom]:
        """회의실 ID로 조회"""
        try:
            room_entity = self.session.query(MeetingRoomEntity).filter(
                MeetingRoomEntity.id == room_id
            ).first()

            if room_entity:
                room = room_entity.to_model()
                # 현재 시간에 예약이 있는지 확인
                room.status = self._get_current_room_status(room_id)
                return room

            return None

        except Exception as e:
            logger.error(f"회의실 조회 실패 (ID: {room_id}): {e}")
            return None

    def get_by_name(self, room_name: str) -> Optional[MeetingRoom]:
        """회의실 이름으로 조회"""
        try:
            room_entity = self.session.query(MeetingRoomEntity).filter(
                (MeetingRoomEntity.name == room_name) |
                (MeetingRoomEntity.name.contains(room_name))
            ).first()

            return room_entity.to_model() if room_entity else None

        except Exception as e:
            logger.error(f"회의실 조회 실패 (이름: {room_name}): {e}")
            return None

    def get_all(self) -> List[MeetingRoom]:
        """모든 회의실 조회"""
        try:
            room_entities = self.session.query(MeetingRoomEntity).order_by(
                MeetingRoomEntity.location, MeetingRoomEntity.capacity
            ).all()

            rooms = []
            for entity in room_entities:
                room = entity.to_model()
                # 현재 시간에 예약이 있는지 확인
                room.status = self._get_current_room_status(entity.id)
                rooms.append(room)

            return rooms

        except Exception as e:
            logger.error(f"전체 회의실 조회 실패: {e}")
            return []

    def get_available_rooms(
            self,
            start_time: datetime,
            end_time: datetime,
            criteria: Optional[RoomSearchCriteria] = None
    ) -> List[MeetingRoom]:
        """사용 가능한 회의실 조회"""
        try:
            query = self.session.query(MeetingRoomEntity).filter(
                MeetingRoomEntity.status == 'available'
            )

            # 최소 인원수 조건
            if criteria and criteria.min_capacity:
                query = query.filter(MeetingRoomEntity.capacity >= criteria.min_capacity)

            # 위치 조건
            if criteria and criteria.location_preference:
                query = query.filter(
                    MeetingRoomEntity.location.contains(criteria.location_preference)
                )

            # 장비 조건
            if criteria and criteria.equipment_required:
                for equipment in criteria.equipment_required:
                    query = query.filter(
                        MeetingRoomEntity.equipment.contains(equipment)
                    )

            # 시간 충돌 체크 - 해당 시간에 예약이 없는 회의실만
            conflicting_reservations = self.session.query(ReservationEntity.room_id).filter(
                (
                        (ReservationEntity.start_time < end_time) &
                        (ReservationEntity.end_time > start_time)
                )
            ).subquery()

            query = query.filter(
                ~MeetingRoomEntity.id.in_(conflicting_reservations)
            )

            # 정렬
            query = query.order_by(MeetingRoomEntity.capacity.asc(), MeetingRoomEntity.name.asc())

            room_entities = query.all()
            rooms = [entity.to_model() for entity in room_entities]

            logger.info(f"사용 가능한 회의실 {len(rooms)}개 조회됨 ({start_time} ~ {end_time})")
            return rooms

        except Exception as e:
            logger.error(f"회의실 조회 실패: {e}")
            return []

    def update_status(self, room_id: int, status: RoomStatus) -> bool:
        """회의실 상태 업데이트"""
        try:
            room_entity = self.session.query(MeetingRoomEntity).filter(
                MeetingRoomEntity.id == room_id
            ).first()

            if room_entity:
                room_entity.status = status.value
                self.session.commit()

                logger.info(f"회의실 상태 업데이트: room_id={room_id}, status={status.value}")
                return True

            return False

        except Exception as e:
            logger.error(f"회의실 상태 업데이트 실패: {e}")
            return False

    def get_room_count(self) -> int:
        """전체 회의실 수"""
        return self.session.query(MeetingRoomEntity).count()

    def get_active_room_count(self) -> int:
        """활성 회의실 수"""
        return self.session.query(MeetingRoomEntity).filter(
            MeetingRoomEntity.status == 'available'
        ).count()

    def insert_sample_data(self):
        """샘플 데이터 삽입"""
        if self.session.query(MeetingRoomEntity).count() > 0:
            return  # 이미 데이터가 있으면 스킵

        sample_rooms = [
            MeetingRoomEntity(
                name='회의실 A',
                capacity=8,
                location='2층',
                equipment='TV, 화이트보드, 프로젝터',
                status='available'
            ),
            MeetingRoomEntity(
                name='회의실 B',
                capacity=12,
                location='3층',
                equipment='TV, 화이트보드',
                status='available'
            ),
            MeetingRoomEntity(
                name='회의실 C',
                capacity=6,
                location='2층',
                equipment='화이트보드',
                status='available'
            ),
            MeetingRoomEntity(
                name='대회의실',
                capacity=20,
                location='1층',
                equipment='TV, 프로젝터, 음향시설',
                status='available'
            ),
            MeetingRoomEntity(
                name='소회의실 1',
                capacity=4,
                location='4층',
                equipment='화이트보드',
                status='available'
            ),
            MeetingRoomEntity(
                name='소회의실 2',
                capacity=4,
                location='4층',
                equipment='화이트보드',
                status='available'
            ),
            MeetingRoomEntity(
                name='임원회의실',
                capacity=10,
                location='5층',
                equipment='TV, 프로젝터, 화이트보드, 화상회의',
                status='available'
            ),
            MeetingRoomEntity(
                name='창의공간',
                capacity=15,
                location='1층',
                equipment='프로젝터, 화이트보드, 빔백',
                status='available'
            ),
        ]

        for room in sample_rooms:
            self.session.add(room)

        self.session.commit()
        logger.info(f"샘플 회의실 {len(sample_rooms)}개 추가됨")

    def _get_current_room_status(self, room_id: int) -> RoomStatus:
        """현재 시간 기준으로 회의실의 실제 사용 가능 상태 반환"""
        try:
            # 먼저 회의실의 기본 상태 확인
            room_entity = self.session.query(MeetingRoomEntity).filter(
                MeetingRoomEntity.id == room_id
            ).first()

            if not room_entity:
                return RoomStatus.MAINTENANCE

            # 기본 상태가 available이 아니면 그대로 반환
            if room_entity.status != 'available':
                return RoomStatus(room_entity.status)

            # 현재 시간에 진행 중인 예약이 있는지 확인
            current_time = datetime.now()
            current_reservation = self.session.query(ReservationEntity).filter(
                ReservationEntity.room_id == room_id,
                ReservationEntity.start_time <= current_time,
                ReservationEntity.end_time > current_time
            ).first()

            if current_reservation:
                return RoomStatus.OCCUPIED

            return RoomStatus.AVAILABLE

        except Exception as e:
            logger.error(f"회의실 상태 확인 실패 (room_id: {room_id}): {e}")
            return RoomStatus.MAINTENANCE

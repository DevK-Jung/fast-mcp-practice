"""
예약 비즈니스 로직 서비스
"""

import logging
from datetime import datetime
from typing import List, Optional

from src.meeting_room_mcp.config.database_config import DatabaseConfig
from src.meeting_room_mcp.server.reservation.reservation_repository import ReservationRepository
from src.meeting_room_mcp.server.reservation.reservation_schemas import Reservation

logger = logging.getLogger(__name__)


class ReservationService:
    """예약 비즈니스 로직"""

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config

    def create_reservation(self, reservation: Reservation) -> int:
        """예약 생성"""
        # 비즈니스 규칙 검증
        self._validate_reservation(reservation)

        with self.db_config.get_session() as session:
            reservation_repo = ReservationRepository(session)
            return reservation_repo.create(reservation)

    def get_reservation_details(self, reservation_id: int) -> Optional[Reservation]:
        """예약 상세 정보 조회"""
        with self.db_config.get_session() as session:
            reservation_repo = ReservationRepository(session)
            return reservation_repo.get_by_id(reservation_id)

    def cancel_reservation(self, reservation_id: int) -> bool:
        """예약 취소"""
        with self.db_config.get_session() as session:
            reservation_repo = ReservationRepository(session)

            # 예약 존재 여부 확인
            reservation = reservation_repo.get_by_id(reservation_id)
            if not reservation:
                return False

            # 취소 가능 여부 검증 (예: 시작 시간 1시간 전까지만 취소 가능)
            if not self._can_cancel_reservation(reservation):
                raise ValueError("예약 취소 불가: 시작 시간이 너무 가까움")

            return reservation_repo.delete(reservation_id)

    def get_room_reservations(
            self,
            room_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Reservation]:
        """특정 회의실의 예약 목록 조회"""
        with self.db_config.get_session() as session:
            reservation_repo = ReservationRepository(session)
            return reservation_repo.get_by_room(room_id, start_date, end_date)

    def get_reservation_statistics(self) -> dict:
        """예약 통계 정보"""
        with self.db_config.get_session() as session:
            reservation_repo = ReservationRepository(session)

            total_reservations = reservation_repo.get_reservation_count()
            today_reservations = reservation_repo.get_today_reservation_count()

            return {
                'total_reservations': total_reservations,
                'today_reservations': today_reservations
            }

    def _validate_reservation(self, reservation: Reservation):
        """예약 유효성 검증"""
        current_time = datetime.now()

        # 과거 시간 예약 불가
        if reservation.start_time <= current_time:
            raise ValueError("과거 시간으로 예약할 수 없습니다")

        # 시작 시간이 종료 시간보다 늦으면 안됨
        if reservation.start_time >= reservation.end_time:
            raise ValueError("시작 시간이 종료 시간보다 늦을 수 없습니다")

        # 예약 시간이 너무 길면 안됨 (예: 8시간 이상)
        duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
        if duration_hours > 8:
            raise ValueError("예약 시간이 8시간을 초과할 수 없습니다")

        # 이메일 형식 간단 검증
        if '@' not in reservation.organizer_email:
            raise ValueError("올바른 이메일 주소를 입력해주세요")

        # 참가자 수 제한 (예: 50명)
        if len(reservation.participants) > 50:
            raise ValueError("참가자 수는 50명을 초과할 수 없습니다")

    def _can_cancel_reservation(self, reservation: Reservation) -> bool:
        """예약 취소 가능 여부 확인"""
        current_time = datetime.now()
        time_until_start = (reservation.start_time - current_time).total_seconds() / 3600

        # 시작 시간 1시간 전까지만 취소 가능
        return time_until_start >= 1

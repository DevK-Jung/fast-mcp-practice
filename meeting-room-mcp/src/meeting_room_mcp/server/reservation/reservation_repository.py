"""
예약 데이터 접근 레이어
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.meeting_room_mcp.server.entities import ReservationEntity
from src.meeting_room_mcp.server.reservation.reservation_schemas import Reservation

logger = logging.getLogger(__name__)


class ReservationRepository:
    """예약 데이터 접근 객체"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, reservation: Reservation) -> int:
        """예약 생성"""
        try:
            # 중복 예약 체크
            if self._check_conflict(reservation):
                raise ValueError("해당 시간에 이미 예약이 있습니다")

            # 예약 엔티티 생성
            reservation_entity = ReservationEntity(
                room_id=reservation.room_id,
                title=reservation.title,
                description=reservation.description,
                start_time=reservation.start_time,
                end_time=reservation.end_time,
                organizer_email=reservation.organizer_email,
                participants=json.dumps(reservation.participants, ensure_ascii=False)
            )

            self.session.add(reservation_entity)
            self.session.commit()
            self.session.refresh(reservation_entity)

            reservation_id = reservation_entity.id
            logger.info(f"예약 생성 완료: ID={reservation_id}, 회의실={reservation.room_id}")
            return reservation_id

        except Exception as e:
            self.session.rollback()
            logger.error(f"예약 생성 실패: {e}")
            raise

    def get_by_id(self, reservation_id: int) -> Optional[Reservation]:
        """예약 ID로 조회"""
        try:
            reservation_entity = self.session.query(ReservationEntity).filter(
                ReservationEntity.id == reservation_id
            ).first()

            return reservation_entity.to_model() if reservation_entity else None

        except Exception as e:
            logger.error(f"예약 조회 실패 (ID: {reservation_id}): {e}")
            return None

    def get_by_room(
            self,
            room_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Reservation]:
        """특정 회의실의 예약 목록 조회"""
        try:
            query = self.session.query(ReservationEntity).filter(
                ReservationEntity.room_id == room_id
            )

            if start_date:
                query = query.filter(ReservationEntity.end_time >= start_date)

            if end_date:
                query = query.filter(ReservationEntity.start_time <= end_date)

            query = query.order_by(ReservationEntity.start_time.asc())

            reservation_entities = query.all()
            return [entity.to_model() for entity in reservation_entities]

        except Exception as e:
            logger.error(f"회의실 예약 목록 조회 실패 (room_id: {room_id}): {e}")
            return []

    def delete(self, reservation_id: int) -> bool:
        """예약 삭제"""
        try:
            reservation_entity = self.session.query(ReservationEntity).filter(
                ReservationEntity.id == reservation_id
            ).first()

            if reservation_entity:
                self.session.delete(reservation_entity)
                self.session.commit()

                logger.info(f"예약 삭제 완료: reservation_id={reservation_id}")
                return True

            return False

        except Exception as e:
            self.session.rollback()
            logger.error(f"예약 삭제 실패: {e}")
            return False

    def get_reservation_count(self) -> int:
        """전체 예약 수"""
        return self.session.query(ReservationEntity).count()

    def get_today_reservation_count(self) -> int:
        """오늘 예약 수"""
        today = datetime.now().date()
        return self.session.query(ReservationEntity).filter(
            func.date(ReservationEntity.start_time) == today
        ).count()

    def _check_conflict(self, reservation: Reservation) -> bool:
        """예약 충돌 체크"""
        conflict_count = self.session.query(ReservationEntity).filter(
            ReservationEntity.room_id == reservation.room_id,
            (
                    (ReservationEntity.start_time < reservation.end_time) &
                    (ReservationEntity.end_time > reservation.start_time)
            )
        ).count()

        return conflict_count > 0

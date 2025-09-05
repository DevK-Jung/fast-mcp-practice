"""
예약 관련 MCP Tools
"""

import logging
from datetime import datetime
from typing import List

from fastmcp import FastMCP

from src.meeting_room_mcp.server.reservation.reservation_schemas import Reservation
from src.meeting_room_mcp.server.reservation.reservation_service import ReservationService
from src.meeting_room_mcp.server.services import RoomService

logger = logging.getLogger(__name__)


def register_reservation_tools(
        app: FastMCP,
        room_service: RoomService,
        reservation_service: ReservationService
):
    """예약 관련 도구 등록"""

    @app.tool()
    def create_reservation(
            room_id: int,
            title: str,
            description: str,
            start_time: str,  # ISO 8601
            end_time: str,  # ISO 8601
            organizer_email: str,
            participants: List[str]  # 참가자 이메일 목록
    ) -> str:
        """회의실 예약을 생성합니다."""
        try:
            # 시간 변환
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            # 예약 객체 생성
            reservation = Reservation(
                id=None,
                room_id=room_id,
                title=title,
                description=description,
                start_time=start_dt,
                end_time=end_dt,
                organizer_email=organizer_email,
                participants=participants
            )

            # 예약 생성
            reservation_id = reservation_service.create_reservation(reservation)

            return f"예약이 성공적으로 생성되었습니다. 예약 ID: {reservation_id}"

        except Exception as e:
            logger.error(f"예약 생성 오류: {e}")
            return f"오류: {e}"

    @app.tool()
    def get_reservation_details(reservation_id: int) -> str:
        """예약 상세 정보를 조회합니다."""
        try:
            reservation = reservation_service.get_reservation_details(reservation_id)
            if not reservation:
                return f"예약 ID {reservation_id}를 찾을 수 없습니다."

            room = room_service.get_room_info(reservation.room_id)

            result = f"예약 상세 정보 (ID: {reservation_id}):\n"
            result += f"• 제목: {reservation.title}\n"
            result += f"• 설명: {reservation.description}\n"
            result += f"• 시작: {reservation.start_time.strftime('%Y-%m-%d %H:%M')}\n"
            result += f"• 종료: {reservation.end_time.strftime('%Y-%m-%d %H:%M')}\n"
            result += f"• 회의실: {room.name if room else '알 수 없음'}\n"
            result += f"• 주최자: {reservation.organizer_email}\n"
            result += f"• 참가자: {', '.join(reservation.participants)}\n"

            return result

        except Exception as e:
            logger.error(f"예약 조회 오류: {e}")
            return f"오류: {e}"

    @app.tool()
    def cancel_reservation(reservation_id: int, reason: str = "") -> str:
        """예약을 취소합니다."""
        try:
            # 예약 취소
            if reservation_service.cancel_reservation(reservation_id):
                result = f"예약 ID {reservation_id}가 성공적으로 취소되었습니다."
                if reason:
                    result += f"\n취소 사유: {reason}"
                return result
            else:
                return f"예약 ID {reservation_id}를 찾을 수 없습니다."

        except ValueError as e:
            return f"취소 실패: {e}"
        except Exception as e:
            logger.error(f"예약 취소 오류: {e}")
            return f"오류: {e}"

"""
알림 관련 MCP Tools
"""

import logging

from fastmcp import FastMCP

from src.meeting_room_mcp.server.services.email_sevice import EmailService
from src.meeting_room_mcp.server.services import RoomService
from src.meeting_room_mcp.server.reservation.reservation_service import ReservationService

logger = logging.getLogger(__name__)


def register_notification_tools(
    app: FastMCP,
    room_service: RoomService,
    reservation_service: ReservationService,
    email_service: EmailService
):
    """알림 관련 도구 등록"""
    
    @app.tool()
    def send_notification(
            reservation_id: int,
            notification_type: str = "confirmation",  # confirmation, cancellation, reminder
            message: str = ""
    ) -> str:
        """예약 관련 이메일 알림을 발송합니다."""
        try:
            reservation = reservation_service.get_reservation_details(reservation_id)
            if not reservation:
                return f"예약 ID {reservation_id}를 찾을 수 없습니다."

            room = room_service.get_room_info(reservation.room_id)
            if not room:
                return "회의실 정보를 찾을 수 없습니다."

            success = False
            if notification_type == "confirmation":
                success = email_service.send_reservation_confirmation(reservation, room)
            elif notification_type == "cancellation":
                success = email_service.send_reservation_cancellation(reservation, room, message)
            elif notification_type == "reminder":
                success = email_service.send_reminder(reservation, room)
            else:
                return f"지원하지 않는 알림 타입: {notification_type}"

            if success:
                return f"이메일 알림이 성공적으로 발송되었습니다."
            else:
                return "이메일 발송에 실패했습니다."

        except Exception as e:
            logger.error(f"이메일 발송 오류: {e}")
            return f"오류: {e}"
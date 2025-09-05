"""
이메일 서비스 모듈
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from src.meeting_room_mcp.shared.models import Reservation, MeetingRoom, EmailNotification

logger = logging.getLogger(__name__)


class EmailService:
    """이메일 발송 서비스"""

    def __init__(
            self,
            smtp_server: str = "localhost",
            smtp_port: int = 587,
            username: Optional[str] = None,
            password: Optional[str] = None,
            use_tls: bool = True,
            mock_mode: bool = True  # 개발 모드에서는 실제 메일 발송 대신 로그만
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.mock_mode = mock_mode

    def send_meeting_notification(
            self,
            reservation: Reservation,
            room: MeetingRoom,
            additional_message: str = ""
    ) -> bool:
        """회의 알림 메일 발송"""
        try:
            notification = EmailNotification(
                to_emails=reservation.participants + [reservation.organizer_email],
                subject=f"[회의 알림] {reservation.title}",
                body="",  # 자동 생성됨
                reservation=reservation,
                room=room
            )

            if additional_message:
                notification.body = additional_message + "\n\n" + notification.body

            return self._send_email(notification)

        except Exception as e:
            logger.error(f"회의 알림 메일 발송 실패: {e}")
            return False

    def send_reservation_confirmation(
            self,
            reservation: Reservation,
            room: MeetingRoom
    ) -> bool:
        """예약 확인 메일 발송"""
        try:
            subject = f"[예약 확인] {reservation.title} - {room.name}"
            body = self._generate_confirmation_body(reservation, room)

            notification = EmailNotification(
                to_emails=[reservation.organizer_email],
                subject=subject,
                body=body,
                reservation=reservation,
                room=room
            )

            return self._send_email(notification)

        except Exception as e:
            logger.error(f"예약 확인 메일 발송 실패: {e}")
            return False

    def send_reservation_cancellation(
            self,
            reservation: Reservation,
            room: MeetingRoom,
            reason: str = ""
    ) -> bool:
        """예약 취소 메일 발송"""
        try:
            subject = f"[예약 취소] {reservation.title} - {room.name}"
            body = self._generate_cancellation_body(reservation, room, reason)

            notification = EmailNotification(
                to_emails=reservation.participants + [reservation.organizer_email],
                subject=subject,
                body=body,
                reservation=reservation,
                room=room
            )

            return self._send_email(notification)

        except Exception as e:
            logger.error(f"예약 취소 메일 발송 실패: {e}")
            return False

    def _send_email(self, notification: EmailNotification) -> bool:
        """실제 이메일 발송"""
        if self.mock_mode:
            return self._mock_send_email(notification)
        else:
            return self._real_send_email(notification)

    def _mock_send_email(self, notification: EmailNotification) -> bool:
        """모의 이메일 발송 (개발/테스트용)"""
        try:
            logger.info("=== 모의 이메일 발송 ===")
            logger.info(f"수신자: {', '.join(notification.to_emails)}")
            logger.info(f"제목: {notification.subject}")
            logger.info(f"본문:\n{notification.body}")
            logger.info("=== 모의 이메일 발송 완료 ===")
            return True
        except Exception as e:
            logger.error(f"모의 이메일 발송 실패: {e}")
            return False

    def _real_send_email(self, notification: EmailNotification) -> bool:
        """실제 이메일 발송"""
        try:
            # SMTP 서버 연결
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                    
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                # 각 수신자에게 개별 발송
                for to_email in notification.to_emails:
                    msg = MIMEMultipart()
                    msg['From'] = self.username or 'meeting-system@company.com'
                    msg['To'] = to_email
                    msg['Subject'] = notification.subject
                    
                    # 본문 추가
                    msg.attach(MIMEText(notification.body, 'plain', 'utf-8'))
                    
                    # 발송
                    server.send_message(msg)
                    
                logger.info(f"이메일 발송 완료: {len(notification.to_emails)}명")
                return True
                
        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False
            
    def _generate_confirmation_body(self, reservation: Reservation, room: MeetingRoom) -> str:
        """예약 확인 이메일 본문 생성"""
        return f"""
🎉 회의실 예약이 확정되었습니다!

📋 예약 정보:
• 예약 ID: {reservation.id}
• 회의 제목: {reservation.title}
• 회의 설명: {reservation.description}
• 일시: {reservation.start_time.strftime('%Y년 %m월 %d일 %H:%M')} ~ {reservation.end_time.strftime('%H:%M')}
• 지속 시간: {reservation.duration_hours:.1f}시간
• 주최자: {reservation.organizer_email}
• 참가자: {', '.join(reservation.participants)}

🏢 회의실 정보:
• 이름: {room.name}
• 위치: {room.location}
• 수용인원: {room.capacity}명
• 장비: {room.equipment}

📝 참고사항:
• 회의 시작 10분 전에 회의실에 도착해 주세요.
• 회의 종료 후 정리를 부탁드립니다.
• 예약 변경이나 취소가 필요한 경우 관리자에게 연락해 주세요.

이 메일은 자동으로 발송된 메일입니다.
"""

    def _generate_cancellation_body(self, reservation: Reservation, room: MeetingRoom, reason: str = "") -> str:
        """예약 취소 이메일 본문 생성"""
        body = f"""
❌ 회의실 예약이 취소되었습니다.

📋 취소된 예약 정보:
• 예약 ID: {reservation.id}
• 회의 제목: {reservation.title}
• 일시: {reservation.start_time.strftime('%Y년 %m월 %d일 %H:%M')} ~ {reservation.end_time.strftime('%H:%M')}
• 회의실: {room.name} ({room.location})
• 주최자: {reservation.organizer_email}
"""
        
        if reason:
            body += f"\n📝 취소 사유: {reason}"
            
        body += """

죄송합니다. 일정에 변동이 있어 예약이 취소되었습니다.
새로운 회의 일정이 확정되면 다시 예약해 주세요.

이 메일은 자동으로 발송된 메일입니다.
"""
        
        return body
        
    def send_reminder(self, reservation: Reservation, room: MeetingRoom, minutes_before: int = 30) -> bool:
        """회의 리마인더 발송"""
        try:
            subject = f"[회의 알림] {reservation.title} - {minutes_before}분 전"
            body = f"""
⏰ 회의 시작 {minutes_before}분 전입니다!

📋 회의 정보:
• 제목: {reservation.title}
• 시작 시간: {reservation.start_time.strftime('%Y년 %m월 %d일 %H:%M')}
• 회의실: {room.name} ({room.location})
• 지속 시간: {reservation.duration_hours:.1f}시간

🏃‍♂️ 회의실로 이동 준비를 해주세요!

이 메일은 자동으로 발송된 메일입니다.
"""
            
            notification = EmailNotification(
                to_emails=reservation.participants + [reservation.organizer_email],
                subject=subject,
                body=body,
                reservation=reservation,
                room=room
            )
            
            return self._send_email(notification)
            
        except Exception as e:
            logger.error(f"리마인더 메일 발송 실패: {e}")
            return False
            
    def test_connection(self) -> bool:
        """이메일 서버 연결 테스트"""
        if self.mock_mode:
            logger.info("이메일 모의 모드 활성화됨")
            return True
            
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                    
                if self.username and self.password:
                    server.login(self.username, self.password)
                    
            logger.info("이메일 서버 연결 테스트 성공")
            return True
            
        except Exception as e:
            logger.error(f"이메일 서버 연결 테스트 실패: {e}")
            return False
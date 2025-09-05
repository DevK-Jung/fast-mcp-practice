"""
Meeting Room MCP Server - 순수한 도구 제공
"""

import logging

from fastmcp import FastMCP

from src.meeting_room_mcp.server.notification.notification_tools import register_notification_tools
from src.meeting_room_mcp.server.reservation.reservation_tools import register_reservation_tools
from src.meeting_room_mcp.server.room.room_tools import register_room_tools
from ..config.settings import get_db_settings, get_email_settings
from src.meeting_room_mcp.config.database_config import DatabaseConfig
from src.meeting_room_mcp.server.services.email_sevice import EmailService
from src.meeting_room_mcp.server.services import RoomService
from src.meeting_room_mcp.server.reservation.reservation_service import ReservationService

# 설정 로드
db_settings = get_db_settings()
email_settings = get_email_settings()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastMCP 앱 생성
app = FastMCP("Meeting Room MCP Server")

# SQLite 개발용 데이터베이스 URL
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
database_url = f"sqlite:///{project_root / 'data' / 'meeting_room.db'}"

# 전역 객체들
db_config = DatabaseConfig(database_url)
room_service = RoomService(db_config)
reservation_service = ReservationService(db_config)

email_service = EmailService(
    smtp_server=email_settings.smtp_host,
    smtp_port=email_settings.smtp_port,
    username=email_settings.smtp_user,
    password=email_settings.smtp_pass,
    use_tls=email_settings.smtp_tls,
    mock_mode=email_settings.mock_mode
)

def main():
    """서버 시작"""
    try:
        logger.info("=== Meeting Room MCP Server 시작 ===")
        logger.info(f"데이터베이스: {database_url}")

        # 데이터베이스 연결 확인 및 테이블 생성
        db_config.create_tables()
        
        if not db_config.health_check():
            logger.warning("데이터베이스 연결 실패 - 계속 진행")
        else:
            # 샘플 데이터 초기화
            room_service.initialize_sample_data()

        # MCP 도구 등록
        register_room_tools(app, room_service)
        register_reservation_tools(app, room_service, reservation_service)
        register_notification_tools(app, room_service, reservation_service, email_service)

        # 이메일 서비스 테스트
        if email_service.test_connection():
            logger.info("이메일 서비스 준비 완료")
        else:
            logger.warning("이메일 서비스 연결 실패 - 모의 모드로 진행")

        app.run()

    except Exception as e:
        logger.error(f"서버 실행 오류: {e}")
        raise
    finally:
        db_config.close()
        logger.info("서버 종료")

if __name__ == "__main__":
    app.run()  # stdIo

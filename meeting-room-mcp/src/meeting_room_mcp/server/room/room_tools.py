"""
회의실 관련 MCP Tools
"""

import logging
from datetime import datetime
from typing import List

from fastmcp import FastMCP

from src.meeting_room_mcp.server.services import RoomService

logger = logging.getLogger(__name__)


def register_room_tools(app: FastMCP, room_service: RoomService):
    """회의실 관련 도구 등록"""

    @app.tool()
    def search_available_rooms(
            start_time: str,  # ISO 8601 형식
            end_time: str,  # ISO 8601 형식
            capacity: int = 1,  # 최소 필요 인원수
            location: str = "",  # 선호 위치
            equipment: List[str] = []  # 필요한 장비
    ) -> str:
        """지정된 조건에 맞는 사용 가능한 회의실을 검색합니다."""
        try:
            # 시간 변환
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            # 검색 실행
            available_rooms = room_service.search_available_rooms(
                start_dt, end_dt, capacity, location, equipment
            )

            if not available_rooms:
                return "해당 조건에 맞는 사용 가능한 회의실이 없습니다."

            # 결과 포맷팅
            result = f"사용 가능한 회의실 ({len(available_rooms)}개):\n\n"
            for room in available_rooms:
                result += f"ID: {room.id}, 이름: {room.name}, 위치: {room.location}, "
                result += f"수용인원: {room.capacity}명, 장비: {room.equipment}\n"

            return result

        except Exception as e:
            logger.error(f"회의실 검색 오류: {e}")
            return f"오류: {e}"

    @app.tool()
    def get_room_info(room_id: int) -> str:
        """특정 회의실의 상세 정보를 조회합니다."""
        try:
            room = room_service.get_room_info(room_id)
            if not room:
                return f"회의실 ID {room_id}를 찾을 수 없습니다."

            result = f"회의실 정보:\n"
            result += f"• ID: {room.id}\n"
            result += f"• 이름: {room.name}\n"
            result += f"• 위치: {room.location}\n"
            result += f"• 수용인원: {room.capacity}명\n"
            result += f"• 장비: {room.equipment}\n"
            result += f"• 상태: {room.status.value}\n"

            return result

        except Exception as e:
            logger.error(f"회의실 정보 조회 오류: {e}")
            return f"오류: {e}"

    @app.tool()
    def get_all_rooms() -> str:
        """모든 회의실 목록을 조회합니다."""
        try:
            rooms = room_service.get_all_rooms()
            if not rooms:
                return "등록된 회의실이 없습니다."

            result = f"전체 회의실 ({len(rooms)}개):\n\n"
            for room in rooms:
                result += f"ID: {room.id}, 이름: {room.name}, 위치: {room.location}, "
                result += f"수용인원: {room.capacity}명, 상태: {room.status.value}\n"

            return result

        except Exception as e:
            logger.error(f"회의실 목록 조회 오류: {e}")
            return f"오류: {e}"

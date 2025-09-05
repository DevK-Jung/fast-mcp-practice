# """
# Meeting Room MCP Client - Human-in-the-loop 예약 시스템
# """
#
# import asyncio
import logging
# from typing import Dict

# from ..shared.database import DatabaseManager
# from ..shared.models import ReservationSession
# MCP Client 및 SessionManager 사용
# from ..shared.session_manager import SessionManager
#
# logger = logging.getLogger(__name__)
#
#
# class MeetingRoomClient:
#     """회의실 예약 MCP 클라이언트"""
#
#     def __init__(self):
#         # SQLite 데이터베이스 사용 (서버와 동일)
#         from pathlib import Path
#         project_root = Path(__file__).parent.parent.parent.parent
#         database_url = f"sqlite:///{project_root / 'data' / 'meeting_room.db'}"
#         self.db_manager = DatabaseManager(database_url)
#
#         # 세션 관리자
#         self.session_manager = SessionManager(
#             db_manager=self.db_manager,
#             session_file_path=str(project_root / "data" / "client_sessions.json")
#         )
#
#         # 현재 진행 중인 세션들
#         self.active_sessions: Dict[str, ReservationSession] = {}
#
#     async def start_reservation(self, user_query: str) -> str:
#         """회의실 예약 프로세스 시작"""
#         try:
#             # 새 세션 생성
#             session = self.session_manager.create_session(user_query)
#             self.active_sessions[session.session_id] = session
#
#             logger.info(f"새 예약 세션 시작: {session.session_id}")
#
#             # 첫 번째 질문 반환
#             return self._get_next_step(session.session_id)
#
#         except Exception as e:
#             logger.error(f"예약 시작 오류: {e}")
#             return f"❌ 예약 시작 중 오류가 발생했습니다: {e}"
#
#     async def continue_reservation(self, session_id: str, user_response: str) -> str:
#         """예약 프로세스 계속 진행"""
#         try:
#             if session_id not in self.active_sessions:
#                 return "❌ 유효하지 않은 세션입니다. 새로 시작해주세요."
#
#             # 사용자 응답 처리
#             session = self.session_manager.update_session(session_id, user_response)
#             if not session:
#                 return "❌ 세션 업데이트에 실패했습니다."
#
#             self.active_sessions[session_id] = session
#
#             # 완료 여부 확인
#             if self.session_manager.is_session_complete(session_id):
#                 # 모든 정보가 수집되었으므로 실제 예약 실행
#                 result = await self._execute_reservation(session)
#
#                 # 세션 정리
#                 self.session_manager.delete_session(session_id)
#                 if session_id in self.active_sessions:
#                     del self.active_sessions[session_id]
#
#                 return result
#             else:
#                 # 다음 단계 진행
#                 return self._get_next_step(session_id)
#
#         except Exception as e:
#             logger.error(f"예약 진행 오류: {e}")
#             return f"❌ 예약 진행 중 오류가 발생했습니다: {e}"
#
#     def _get_next_step(self, session_id: str) -> str:
#         """다음 단계 질문 생성"""
#         return self.session_manager.get_next_question(session_id)
#
#     async def _execute_reservation(self, session: ReservationSession) -> str:
#         """실제 예약 실행 (MCP Server 도구 호출 시뮬레이션)"""
#         try:
#             logger.info(f"예약 실행 시작: {session.session_id}")
#
#             # 실제로는 여기서 MCP Server의 create_reservation 도구를 호출해야 함
#             # 지금은 직접 데이터베이스에 저장
#             from ..shared.models import Reservation
#
#             reservation = Reservation(
#                 id=None,
#                 room_id=session.room_id,
#                 title=session.title,
#                 description=session.description or "",
#                 start_time=session.start_time,
#                 end_time=session.end_time,
#                 organizer_email=session.organizer_email,
#                 participants=session.participants
#             )
#
#             # 예약 생성
#             reservation_id = self.db_manager.create_reservation(reservation)
#
#             # 성공 메시지
#             result = f"🎉 **회의실 예약이 완료되었습니다!**\n\n"
#             result += f"📋 **예약 정보**:\n"
#             result += f"   • 예약 ID: {reservation_id}\n"
#             result += f"   • 회의 제목: {session.title}\n"
#             result += f"   • 일시: {session.start_time.strftime('%Y-%m-%d %H:%M')} ~ {session.end_time.strftime('%H:%M')}\n"
#             result += f"   • 주최자: {session.organizer_email}\n"
#             result += f"   • 참가자: {', '.join(session.participants)}\n"
#
#             # 선택된 회의실 정보
#             if session.available_rooms:
#                 selected_room = next((r for r in session.available_rooms if r.id == session.room_id), None)
#                 if selected_room:
#                     result += f"   • 회의실: {selected_room.name} ({selected_room.location})\n"
#
#             # 이메일 발송 시뮬레이션
#             result += f"   • 알림 이메일: 발송 완료 (모의)\n"
#
#             logger.info(f"예약 완료: {reservation_id}")
#             return result
#
#         except Exception as e:
#             logger.error(f"예약 실행 오류: {e}")
#             return f"❌ 예약 실행 중 오류가 발생했습니다: {e}"
#
#     def get_session_status(self, session_id: str) -> str:
#         """세션 상태 조회"""
#         if session_id not in self.active_sessions:
#             return "❌ 세션을 찾을 수 없습니다."
#
#         return self.session_manager.get_session_summary(session_id)
#
#     def list_active_sessions(self) -> str:
#         """진행 중인 세션 목록"""
#         if not self.active_sessions:
#             return "진행 중인 예약 세션이 없습니다."
#
#         result = f"진행 중인 세션 ({len(self.active_sessions)}개):\n\n"
#         for session_id, session in self.active_sessions.items():
#             result += f"• {session_id[:8]}... - {session.title or '제목 없음'}\n"
#
#         return result
#
#     def cancel_session(self, session_id: str) -> str:
#         """세션 취소"""
#         if session_id not in self.active_sessions:
#             return "❌ 세션을 찾을 수 없습니다."
#
#         # 세션 정리
#         self.session_manager.delete_session(session_id)
#         del self.active_sessions[session_id]
#
#         return f"✅ 세션 {session_id[:8]}...이 취소되었습니다."
#
#
# # 간단한 CLI 인터페이스
# class SimpleCLI:
#     """간단한 명령줄 인터페이스"""
#
#     def __init__(self):
#         self.client = MeetingRoomClient()
#         self.current_session = None
#
#     async def run(self):
#         """CLI 실행"""
#         print("=== 회의실 예약 시스템 ===")
#         print("명령어: start, continue, status, list, cancel, quit")
#         print()
#
#         while True:
#             try:
#                 command = input(">>> ").strip().lower()
#
#                 if command == 'quit':
#                     break
#                 elif command == 'start':
#                     await self._start_reservation()
#                 elif command == 'continue':
#                     await self._continue_reservation()
#                 elif command == 'status':
#                     self._show_status()
#                 elif command == 'list':
#                     self._list_sessions()
#                 elif command == 'cancel':
#                     self._cancel_session()
#                 else:
#                     print("사용 가능한 명령: start, continue, status, list, cancel, quit")
#
#             except KeyboardInterrupt:
#                 break
#             except Exception as e:
#                 print(f"오류: {e}")
#
#         print("종료합니다.")
#
#     async def _start_reservation(self):
#         """예약 시작"""
#         query = input("예약 요청을 입력하세요: ")
#         if not query.strip():
#             print("요청을 입력해주세요.")
#             return
#
#         response = await self.client.start_reservation(query)
#         print(f"\n{response}\n")
#
#         # 세션 ID 추출 (간단하게)
#         sessions = list(self.client.active_sessions.keys())
#         if sessions:
#             self.current_session = sessions[-1]  # 가장 최근 세션
#             print(f"현재 세션: {self.current_session[:8]}...")
#
#     async def _continue_reservation(self):
#         """예약 계속"""
#         if not self.current_session:
#             print("활성 세션이 없습니다. 먼저 'start' 명령을 사용하세요.")
#             return
#
#         response = input("응답을 입력하세요: ")
#         if not response.strip():
#             print("응답을 입력해주세요.")
#             return
#
#         result = await self.client.continue_reservation(self.current_session, response)
#         print(f"\n{result}\n")
#
#         # 세션이 완료되었는지 확인
#         if self.current_session not in self.client.active_sessions:
#             self.current_session = None
#             print("예약이 완료되었습니다.")
#
#     def _show_status(self):
#         """상태 표시"""
#         if not self.current_session:
#             print("활성 세션이 없습니다.")
#             return
#
#         status = self.client.get_session_status(self.current_session)
#         print(f"\n{status}\n")
#
#     def _list_sessions(self):
#         """세션 목록"""
#         sessions = self.client.list_active_sessions()
#         print(f"\n{sessions}\n")
#
#     def _cancel_session(self):
#         """세션 취소"""
#         if not self.current_session:
#             print("활성 세션이 없습니다.")
#             return
#
#         result = self.client.cancel_session(self.current_session)
#         print(f"\n{result}\n")
#         self.current_session = None
#
#
async def main():
    """메인 함수"""
    logging.basicConfig(level=logging.INFO)

    # cli = SimpleCLI()
    # await cli.run()
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

# """
# 회의실 예약 세션 관리 모듈 (Human-in-the-loop 구현)
# """
#
# import json
# import uuid
# import logging
# import re
# from datetime import datetime, timedelta
# from pathlib import Path
# from typing import Optional, List, Dict, Any
#
# from .models import ReservationSession, MeetingRoom
# from .database import DatabaseManager
#
# logger = logging.getLogger(__name__)
#
#
# class SessionManager:
#     """예약 세션 관리자 - Human-in-the-loop 구현"""
#
#     def __init__(self, db_manager: DatabaseManager, session_file_path: str):
#         self.db_manager = db_manager
#         self.session_file = Path(session_file_path)
#         self.sessions: Dict[str, ReservationSession] = {}
#
#         # 세션 파일 디렉토리 생성
#         self.session_file.parent.mkdir(parents=True, exist_ok=True)
#
#         # 기존 세션 로드
#         self._load_sessions()
#
#     def _load_sessions(self):
#         """저장된 세션 로드"""
#         try:
#             if self.session_file.exists():
#                 with open(self.session_file, 'r', encoding='utf-8') as f:
#                     sessions_data = json.load(f)
#
#                 for session_id, session_data in sessions_data.items():
#                     try:
#                         session = ReservationSession.from_dict(session_data)
#                         self.sessions[session_id] = session
#                     except Exception as e:
#                         logger.warning(f"세션 로드 실패 (ID: {session_id}): {e}")
#
#                 logger.info(f"저장된 세션 {len(self.sessions)}개 로드됨")
#         except Exception as e:
#             logger.error(f"세션 파일 로드 실패: {e}")
#
#     def _save_sessions(self):
#         """세션을 파일에 저장"""
#         try:
#             sessions_data = {}
#             for session_id, session in self.sessions.items():
#                 sessions_data[session_id] = session.to_dict()
#
#             with open(self.session_file, 'w', encoding='utf-8') as f:
#                 json.dump(sessions_data, f, ensure_ascii=False, indent=2)
#
#         except Exception as e:
#             logger.error(f"세션 파일 저장 실패: {e}")
#
#     def create_session(self, initial_query: str) -> ReservationSession:
#         """새 예약 세션 생성 및 초기 정보 추출"""
#         session_id = str(uuid.uuid4())
#
#         # 자연어에서 정보 추출
#         extracted_info = self._extract_info_from_query(initial_query)
#
#         session = ReservationSession(
#             session_id=session_id,
#             title=extracted_info.get('title'),
#             description=extracted_info.get('description'),
#             start_time=extracted_info.get('start_time'),
#             end_time=extracted_info.get('end_time'),
#             organizer_email=extracted_info.get('organizer_email'),
#             participants=extracted_info.get('participants', []),
#             min_capacity=extracted_info.get('min_capacity'),
#             step='collecting_info'
#         )
#
#         self.sessions[session_id] = session
#         self._save_sessions()
#
#         logger.info(f"새 세션 생성: {session_id}")
#         return session
#
#     def _extract_info_from_query(self, query: str) -> Dict[str, Any]:
#         """자연어 쿼리에서 예약 정보 추출"""
#         extracted = {}
#
#         # 인원수 패턴
#         capacity_patterns = [
#             r'(\d+)명',
#             r'(\d+)인',
#             r'(\d+)people',
#         ]
#
#         # 이메일 패턴
#         email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#
#         # 회의 제목 추출 (간단한 휴리스틱)
#         title_keywords = ['회의', '미팅', '회의실', '논의', '상의', '업무', '팀']
#         for keyword in title_keywords:
#             if keyword in query:
#                 # 키워드 주변 텍스트를 제목으로 추정
#                 sentences = query.split('.')
#                 for sentence in sentences:
#                     if keyword in sentence:
#                         extracted['title'] = sentence.strip()[:50]  # 최대 50자
#                         break
#                 break
#
#         # 인원수 추출
#         for pattern in capacity_patterns:
#             match = re.search(pattern, query)
#             if match:
#                 extracted['min_capacity'] = int(match.group(1))
#                 break
#
#         # 이메일 추출
#         emails = re.findall(email_pattern, query)
#         if emails:
#             extracted['organizer_email'] = emails[0]
#             if len(emails) > 1:
#                 extracted['participants'] = emails[1:]
#
#         logger.info(f"쿼리에서 추출된 정보: {extracted}")
#         return extracted
#
#     def update_session(self, session_id: str, user_response: str) -> Optional[ReservationSession]:
#         """사용자 응답으로 세션 업데이트"""
#         if session_id not in self.sessions:
#             return None
#
#         session = self.sessions[session_id]
#
#         # 현재 단계에 따라 응답 처리
#         self._process_user_response(session, user_response)
#
#         self._save_sessions()
#         return session
#
#     def _process_user_response(self, session: ReservationSession, response: str):
#         """사용자 응답을 단계별로 처리"""
#         response = response.strip()
#
#         # 현재 필요한 정보 확인
#         missing_info = self._get_missing_fields(session)
#
#         if not missing_info:
#             return
#
#         current_field = missing_info[0]
#
#         try:
#             if current_field == 'title':
#                 session.title = response
#
#             elif current_field == 'start_time':
#                 session.start_time = self._parse_datetime(response)
#
#             elif current_field == 'end_time':
#                 if session.start_time:
#                     session.end_time = self._parse_datetime(response, base_date=session.start_time.date())
#                 else:
#                     session.end_time = self._parse_datetime(response)
#
#             elif current_field == 'organizer_email':
#                 if self._is_valid_email(response):
#                     session.organizer_email = response
#                 else:
#                     raise ValueError("유효하지 않은 이메일 형식")
#
#             elif current_field == 'participants':
#                 # 이메일 목록 파싱
#                 emails = self._parse_email_list(response)
#                 session.participants = emails
#
#             elif current_field == 'min_capacity':
#                 session.min_capacity = int(response)
#
#             elif current_field == 'room_id':
#                 # 사용자가 회의실을 선택했을 때
#                 if response.isdigit():
#                     room_id = int(response)
#                     # 사용 가능한 회의실 목록에서 확인
#                     available_room_ids = [room.id for room in session.available_rooms]
#                     if room_id in available_room_ids:
#                         session.room_id = room_id
#                     else:
#                         raise ValueError("선택할 수 없는 회의실입니다")
#                 else:
#                     # 회의실 이름으로 검색
#                     room = self.db_manager.get_room_by_name(response)
#                     if room and room.id in [r.id for r in session.available_rooms]:
#                         session.room_id = room.id
#                     else:
#                         raise ValueError("해당 이름의 회의실을 찾을 수 없거나 사용할 수 없습니다")
#
#         except ValueError as e:
#             logger.warning(f"사용자 응답 처리 오류: {e}")
#             # 오류는 다음 질문에서 안내
#
#     def _parse_datetime(self, time_str: str, base_date=None) -> datetime:
#         """시간 문자열을 datetime 객체로 변환"""
#         if base_date is None:
#             base_date = datetime.now().date()
#
#         time_str = time_str.strip()
#
#         # 다양한 시간 형식 처리
#         patterns = [
#             (r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})',
#              lambda m: datetime(int(m.group(1)[:4]), int(m.group(1)[5:7]), int(m.group(1)[8:10]), int(m.group(2)), int(m.group(3)))),
#             (r'(\d{1,2}):(\d{2})',
#              lambda m: datetime.combine(base_date, datetime.strptime(f"{m.group(1)}:{m.group(2)}", "%H:%M").time())),
#             (r'(\d{1,2})시\s*(\d{1,2})분?',
#              lambda m: datetime.combine(base_date, datetime.strptime(f"{m.group(1)}:{m.group(2) if m.group(2) else '00'}", "%H:%M").time())),
#             (r'(\d{1,2})시',
#              lambda m: datetime.combine(base_date, datetime.strptime(f"{m.group(1)}:00", "%H:%M").time())),
#             (r'오전\s*(\d{1,2})시?',
#              lambda m: datetime.combine(base_date, datetime.strptime(f"{m.group(1)}:00", "%H:%M").time())),
#             (r'오후\s*(\d{1,2})시?',
#              lambda m: datetime.combine(base_date, datetime.strptime(f"{int(m.group(1)) + 12}:00", "%H:%M").time())),
#         ]
#
#         for pattern, parser in patterns:
#             match = re.search(pattern, time_str)
#             if match:
#                 return parser(match)
#
#         # ISO 형식 시도
#         try:
#             return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
#         except:
#             pass
#
#         raise ValueError(f"시간 형식을 인식할 수 없습니다: {time_str}")
#
#     def _is_valid_email(self, email: str) -> bool:
#         """이메일 유효성 검사"""
#         pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
#         return re.match(pattern, email) is not None
#
#     def _parse_email_list(self, email_str: str) -> List[str]:
#         """이메일 목록 파싱"""
#         # 쉼표, 세미콜론, 공백으로 구분
#         separators = [',', ';', ' ', '\n']
#         emails = [email_str]
#
#         for sep in separators:
#             new_emails = []
#             for email in emails:
#                 new_emails.extend(email.split(sep))
#             emails = new_emails
#
#         # 정리 및 검증
#         valid_emails = []
#         for email in emails:
#             email = email.strip()
#             if email and self._is_valid_email(email):
#                 valid_emails.append(email)
#
#         return valid_emails
#
#     def get_missing_info(self, session_id: str) -> List[str]:
#         """부족한 정보 목록 반환"""
#         if session_id not in self.sessions:
#             return []
#
#         session = self.sessions[session_id]
#         return self._get_missing_fields(session)
#
#     def _get_missing_fields(self, session: ReservationSession) -> List[str]:
#         """필수 정보 중 부족한 필드 반환"""
#         missing = []
#
#         if not session.title:
#             missing.append('title')
#         if not session.start_time:
#             missing.append('start_time')
#         if not session.end_time:
#             missing.append('end_time')
#         if not session.organizer_email:
#             missing.append('organizer_email')
#         if not session.participants:
#             missing.append('participants')
#         if not session.min_capacity:
#             missing.append('min_capacity')
#
#         # 시간 정보가 있으면 회의실 검색 및 선택 필요
#         if (session.start_time and session.end_time and session.min_capacity
#             and not session.room_id):
#
#             # 사용 가능한 회의실 검색 (캐시되지 않았으면)
#             if not session.available_rooms:
#                 from ...shared.models import RoomSearchCriteria
#                 criteria = RoomSearchCriteria(
#                     start_time=session.start_time,
#                     end_time=session.end_time,
#                     min_capacity=session.min_capacity
#                 )
#                 session.available_rooms = self.db_manager.get_available_rooms(
#                     session.start_time, session.end_time, criteria
#                 )
#
#             if session.available_rooms:
#                 missing.append('room_id')
#
#         return missing
#
#     def get_next_question(self, session_id: str) -> str:
#         """다음 질문 생성"""
#         if session_id not in self.sessions:
#             return "❌ 세션을 찾을 수 없습니다."
#
#         session = self.sessions[session_id]
#         missing = self._get_missing_fields(session)
#
#         if not missing:
#             return "✅ 모든 정보가 수집되었습니다. 예약을 진행합니다."
#
#         current_field = missing[0]
#
#         questions = {
#             'title': "📝 회의 제목을 입력해주세요:",
#             'start_time': "🕐 회의 시작 시간을 입력해주세요 (예: 2024-03-15 14:00, 오후 2시):",
#             'end_time': "🕐 회의 종료 시간을 입력해주세요 (예: 16:00, 오후 4시):",
#             'organizer_email': "📧 주최자 이메일을 입력해주세요:",
#             'participants': "👥 참가자 이메일 목록을 입력해주세요 (쉼표로 구분):",
#             'min_capacity': "👥 최소 필요 인원수를 입력해주세요:",
#             'room_id': self._generate_room_selection_question(session)
#         }
#
#         progress = f"📊 진행 상황: {len(self._get_all_required_fields()) - len(missing)}/{len(self._get_all_required_fields())}"
#
#         return f"{questions.get(current_field, '정보를 입력해주세요:')}\n\n{progress}"
#
#     def _generate_room_selection_question(self, session: ReservationSession) -> str:
#         """회의실 선택 질문 생성"""
#         if not session.available_rooms:
#             return "❌ 사용 가능한 회의실이 없습니다."
#
#         question = "🏢 사용 가능한 회의실을 선택해주세요:\n\n"
#
#         for room in session.available_rooms:
#             question += f"**{room.id}. {room.name}**\n"
#             question += f"   📍 위치: {room.location}\n"
#             question += f"   👥 수용인원: {room.capacity}명\n"
#             question += f"   🔧 장비: {room.equipment}\n\n"
#
#         question += "회의실 번호 또는 이름을 입력해주세요:"
#         return question
#
#     def _get_all_required_fields(self) -> List[str]:
#         """모든 필수 필드 목록"""
#         return ['title', 'start_time', 'end_time', 'organizer_email', 'participants', 'min_capacity', 'room_id']
#
#     def is_session_complete(self, session_id: str) -> bool:
#         """세션이 완료되었는지 확인"""
#         if session_id not in self.sessions:
#             return False
#
#         missing = self.get_missing_info(session_id)
#         return len(missing) == 0
#
#     def delete_session(self, session_id: str) -> bool:
#         """세션 삭제"""
#         if session_id in self.sessions:
#             del self.sessions[session_id]
#             self._save_sessions()
#             logger.info(f"세션 삭제: {session_id}")
#             return True
#         return False
#
#     def cleanup_old_sessions(self, hours: int = 24):
#         """오래된 세션 정리"""
#         cutoff_time = datetime.now() - timedelta(hours=hours)
#         old_sessions = []
#
#         for session_id, session in self.sessions.items():
#             if session.created_at < cutoff_time:
#                 old_sessions.append(session_id)
#
#         for session_id in old_sessions:
#             del self.sessions[session_id]
#
#         if old_sessions:
#             self._save_sessions()
#             logger.info(f"오래된 세션 {len(old_sessions)}개 정리됨")
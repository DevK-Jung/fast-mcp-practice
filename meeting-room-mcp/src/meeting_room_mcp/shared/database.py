# """
# SQLAlchemy를 사용한 MySQL 데이터베이스 관리 모듈
# """
# 
# import json
# import logging
# from datetime import datetime
# from typing import List, Optional
# from sqlalchemy import (
#     create_engine, Column, Integer, String, DateTime, Text, Boolean,
#     ForeignKey, Index, CheckConstraint
# )
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session, relationship
# from sqlalchemy.sql import func
# 
# from .models import MeetingRoom, Reservation, RoomStatus, RoomSearchCriteria
# 
# logger = logging.getLogger(__name__)
# 
# # SQLAlchemy Base
# Base = declarative_base()
# 
# 
# class MeetingRoomEntity(Base):
#     """회의실 테이블"""
#     __tablename__ = 'meeting_rooms'
# 
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(100), nullable=False, unique=True)
#     capacity = Column(Integer, nullable=False)
#     location = Column(String(100), nullable=False)
#     equipment = Column(Text)
#     status = Column(String(20), nullable=False, default='available')
#     created_at = Column(DateTime, nullable=False, default=func.now())
#     updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
# 
#     # 관계 설정
#     reservations = relationship("ReservationEntity", back_populates="room")
# 
#     # 인덱스
#     __table_args__ = (
#         Index('idx_meeting_rooms_status', 'status'),
#         Index('idx_meeting_rooms_capacity', 'capacity'),
#     )
# 
#     def to_model(self) -> MeetingRoom:
#         """엔티티를 모델로 변환"""
#         return MeetingRoom(
#             id=self.id,
#             name=self.name,
#             capacity=self.capacity,
#             location=self.location,
#             equipment=self.equipment or "",
#             status=RoomStatus(self.status)
#         )
# 
# 
# class ReservationEntity(Base):
#     """예약 테이블"""
#     __tablename__ = 'reservations'
# 
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     room_id = Column(Integer, ForeignKey('meeting_rooms.id'), nullable=False)
#     title = Column(String(200), nullable=False)
#     description = Column(Text, default='')
#     start_time = Column(DateTime, nullable=False)
#     end_time = Column(DateTime, nullable=False)
#     organizer_email = Column(String(255), nullable=False)
#     participants = Column(Text, nullable=False)  # JSON 문자열
#     created_at = Column(DateTime, nullable=False, default=func.now())
#     updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
# 
#     # 관계 설정
#     room = relationship("MeetingRoomEntity", back_populates="reservations")
# 
#     # 제약 조건 및 인덱스
#     __table_args__ = (
#         CheckConstraint('start_time < end_time', name='check_time_order'),
#         Index('idx_reservations_room_time', 'room_id', 'start_time', 'end_time'),
#         Index('idx_reservations_time_range', 'start_time', 'end_time'),
#         Index('idx_reservations_organizer', 'organizer_email'),
#     )
# 
#     def to_model(self) -> Reservation:
#         """엔티티를 모델로 변환"""
#         participants = json.loads(self.participants) if self.participants else []
# 
#         return Reservation(
#             id=self.id,
#             room_id=self.room_id,
#             title=self.title,
#             description=self.description or "",
#             start_time=self.start_time,
#             end_time=self.end_time,
#             organizer_email=self.organizer_email,
#             participants=participants,
#             created_at=self.created_at
#         )
# 
# 
# class DatabaseManager:
#     """SQLAlchemy 기반 MySQL 데이터베이스 관리자"""
# 
#     def __init__(self, database_url: str):
#         """
#         database_url 예시:
#         mysql+pymysql://username:password@localhost:3306/meeting_room_db
#         sqlite:///./data/meeting_room.db
#         """
#         # SQLite 개발용 설정
#         if database_url.startswith('sqlite'):
#             self.engine = create_engine(
#                 database_url,
#                 echo=False,  # SQL 로그 출력 여부
#                 connect_args={"check_same_thread": False}
#             )
#         else:
#             # MySQL 프로덕션 설정  
#             self.engine = create_engine(
#                 database_url,
#                 echo=False,  # SQL 로그 출력 여부
#                 pool_size=10,
#                 max_overflow=20,
#                 pool_pre_ping=True,  # 연결 상태 확인
#                 pool_recycle=3600  # 1시간마다 연결 재생성
#             )
# 
#         self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
# 
#         # 테이블 생성
#         self.init_database()
# 
#     def init_database(self):
#         """데이터베이스 및 테이블 초기화"""
#         try:
#             # 모든 테이블 생성
#             Base.metadata.create_all(bind=self.engine)
# 
#             # 샘플 데이터 추가 (처음 실행시에만)
#             with self.SessionLocal() as session:
#                 if session.query(MeetingRoomEntity).count() == 0:
#                     self._insert_sample_data(session)
#                     session.commit()
# 
#             logger.info("데이터베이스 초기화 완료")
# 
#         except Exception as e:
#             logger.error(f"데이터베이스 초기화 실패: {e}")
#             raise
# 
#     def _insert_sample_data(self, session: Session):
#         """샘플 데이터 삽입"""
#         sample_rooms = [
#             MeetingRoomEntity(
#                 name='회의실 A',
#                 capacity=8,
#                 location='2층',
#                 equipment='TV, 화이트보드, 프로젝터',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='회의실 B',
#                 capacity=12,
#                 location='3층',
#                 equipment='TV, 화이트보드',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='회의실 C',
#                 capacity=6,
#                 location='2층',
#                 equipment='화이트보드',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='대회의실',
#                 capacity=20,
#                 location='1층',
#                 equipment='TV, 프로젝터, 음향시설',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='소회의실 1',
#                 capacity=4,
#                 location='4층',
#                 equipment='화이트보드',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='소회의실 2',
#                 capacity=4,
#                 location='4층',
#                 equipment='화이트보드',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='임원회의실',
#                 capacity=10,
#                 location='5층',
#                 equipment='TV, 프로젝터, 화이트보드, 화상회의',
#                 status='available'
#             ),
#             MeetingRoomEntity(
#                 name='창의공간',
#                 capacity=15,
#                 location='1층',
#                 equipment='프로젝터, 화이트보드, 빔백',
#                 status='available'
#             ),
#         ]
# 
#         for room in sample_rooms:
#             session.add(room)
# 
#         logger.info(f"샘플 회의실 {len(sample_rooms)}개 추가됨")
# 
#     def get_available_rooms(
#             self,
#             start_time: datetime,
#             end_time: datetime,
#             criteria: Optional[RoomSearchCriteria] = None
#     ) -> List[MeetingRoom]:
#         """사용 가능한 회의실 조회"""
#         try:
#             with self.SessionLocal() as session:
#                 query = session.query(MeetingRoomEntity).filter(
#                     MeetingRoomEntity.status == 'available'
#                 )
# 
#                 # 최소 인원수 조건
#                 if criteria and criteria.min_capacity:
#                     query = query.filter(MeetingRoomEntity.capacity >= criteria.min_capacity)
# 
#                 # 위치 조건
#                 if criteria and criteria.location_preference:
#                     query = query.filter(
#                         MeetingRoomEntity.location.contains(criteria.location_preference)
#                     )
# 
#                 # 장비 조건
#                 if criteria and criteria.equipment_required:
#                     for equipment in criteria.equipment_required:
#                         query = query.filter(
#                             MeetingRoomEntity.equipment.contains(equipment)
#                         )
# 
#                 # 시간 충돌 체크 - 해당 시간에 예약이 없는 회의실만
#                 conflicting_reservations = session.query(ReservationEntity.room_id).filter(
#                     (
#                             (ReservationEntity.start_time < end_time) &
#                             (ReservationEntity.end_time > start_time)
#                     )
#                 ).subquery()
# 
#                 query = query.filter(
#                     ~MeetingRoomEntity.id.in_(conflicting_reservations)
#                 )
# 
#                 # 정렬
#                 query = query.order_by(MeetingRoomEntity.capacity.asc(), MeetingRoomEntity.name.asc())
# 
#                 room_entities = query.all()
#                 rooms = [entity.to_model() for entity in room_entities]
# 
#                 logger.info(f"사용 가능한 회의실 {len(rooms)}개 조회됨 ({start_time} ~ {end_time})")
#                 return rooms
# 
#         except Exception as e:
#             logger.error(f"회의실 조회 실패: {e}")
#             return []
# 
#     def create_reservation(self, reservation: Reservation) -> int:
#         """예약 생성"""
#         try:
#             with self.SessionLocal() as session:
#                 # 중복 예약 체크
#                 if self._check_reservation_conflict(session, reservation):
#                     raise ValueError("해당 시간에 이미 예약이 있습니다")
# 
#                 # 예약 엔티티 생성
#                 reservation_entity = ReservationEntity(
#                     room_id=reservation.room_id,
#                     title=reservation.title,
#                     description=reservation.description,
#                     start_time=reservation.start_time,
#                     end_time=reservation.end_time,
#                     organizer_email=reservation.organizer_email,
#                     participants=json.dumps(reservation.participants, ensure_ascii=False)
#                 )
# 
#                 session.add(reservation_entity)
#                 session.commit()
#                 session.refresh(reservation_entity)
# 
#                 reservation_id = reservation_entity.id
#                 logger.info(f"예약 생성 완료: ID={reservation_id}, 회의실={reservation.room_id}")
#                 return reservation_id
# 
#         except Exception as e:
#             logger.error(f"예약 생성 실패: {e}")
#             raise
# 
#     def _check_reservation_conflict(self, session: Session, reservation: Reservation) -> bool:
#         """예약 충돌 체크"""
#         conflict_count = session.query(ReservationEntity).filter(
#             ReservationEntity.room_id == reservation.room_id,
#             (
#                     (ReservationEntity.start_time < reservation.end_time) &
#                     (ReservationEntity.end_time > reservation.start_time)
#             )
#         ).count()
# 
#         return conflict_count > 0
# 
#     def get_room_by_id(self, room_id: int) -> Optional[MeetingRoom]:
#         """회의실 ID로 회의실 정보 조회"""
#         try:
#             with self.SessionLocal() as session:
#                 room_entity = session.query(MeetingRoomEntity).filter(
#                     MeetingRoomEntity.id == room_id
#                 ).first()
# 
#                 if room_entity:
#                     return room_entity.to_model()
#                 return None
# 
#         except Exception as e:
#             logger.error(f"회의실 조회 실패 (ID: {room_id}): {e}")
#             return None
# 
#     def get_room_by_name(self, room_name: str) -> Optional[MeetingRoom]:
#         """회의실 이름으로 조회"""
#         try:
#             with self.SessionLocal() as session:
#                 room_entity = session.query(MeetingRoomEntity).filter(
#                     (MeetingRoomEntity.name == room_name) |
#                     (MeetingRoomEntity.name.contains(room_name))
#                 ).first()
# 
#                 if room_entity:
#                     return room_entity.to_model()
#                 return None
# 
#         except Exception as e:
#             logger.error(f"회의실 조회 실패 (이름: {room_name}): {e}")
#             return None
# 
#     def get_all_rooms(self) -> List[MeetingRoom]:
#         """모든 회의실 조회"""
#         try:
#             with self.SessionLocal() as session:
#                 room_entities = session.query(MeetingRoomEntity).order_by(
#                     MeetingRoomEntity.location, MeetingRoomEntity.capacity
#                 ).all()
# 
#                 return [entity.to_model() for entity in room_entities]
# 
#         except Exception as e:
#             logger.error(f"전체 회의실 조회 실패: {e}")
#             return []
# 
#     def get_reservation_by_id(self, reservation_id: int) -> Optional[Reservation]:
#         """예약 ID로 예약 정보 조회"""
#         try:
#             with self.SessionLocal() as session:
#                 reservation_entity = session.query(ReservationEntity).filter(
#                     ReservationEntity.id == reservation_id
#                 ).first()
# 
#                 if reservation_entity:
#                     return reservation_entity.to_model()
#                 return None
# 
#         except Exception as e:
#             logger.error(f"예약 조회 실패 (ID: {reservation_id}): {e}")
#             return None
# 
#     def get_reservations_by_room(
#             self,
#             room_id: int,
#             start_date: Optional[datetime] = None,
#             end_date: Optional[datetime] = None
#     ) -> List[Reservation]:
#         """특정 회의실의 예약 목록 조회"""
#         try:
#             with self.SessionLocal() as session:
#                 query = session.query(ReservationEntity).filter(
#                     ReservationEntity.room_id == room_id
#                 )
# 
#                 if start_date:
#                     query = query.filter(ReservationEntity.end_time >= start_date)
# 
#                 if end_date:
#                     query = query.filter(ReservationEntity.start_time <= end_date)
# 
#                 query = query.order_by(ReservationEntity.start_time.asc())
# 
#                 reservation_entities = query.all()
#                 return [entity.to_model() for entity in reservation_entities]
# 
#         except Exception as e:
#             logger.error(f"회의실 예약 목록 조회 실패 (room_id: {room_id}): {e}")
#             return []
# 
#     def update_room_status(self, room_id: int, status: RoomStatus) -> bool:
#         """회의실 상태 업데이트"""
#         try:
#             with self.SessionLocal() as session:
#                 room_entity = session.query(MeetingRoomEntity).filter(
#                     MeetingRoomEntity.id == room_id
#                 ).first()
# 
#                 if room_entity:
#                     room_entity.status = status.value
#                     room_entity.updated_at = func.now()
#                     session.commit()
# 
#                     logger.info(f"회의실 상태 업데이트: room_id={room_id}, status={status.value}")
#                     return True
# 
#                 return False
# 
#         except Exception as e:
#             logger.error(f"회의실 상태 업데이트 실패: {e}")
#             return False
# 
#     def delete_reservation(self, reservation_id: int) -> bool:
#         """예약 삭제"""
#         try:
#             with self.SessionLocal() as session:
#                 reservation_entity = session.query(ReservationEntity).filter(
#                     ReservationEntity.id == reservation_id
#                 ).first()
# 
#                 if reservation_entity:
#                     session.delete(reservation_entity)
#                     session.commit()
# 
#                     logger.info(f"예약 삭제 완료: reservation_id={reservation_id}")
#                     return True
# 
#                 return False
# 
#         except Exception as e:
#             logger.error(f"예약 삭제 실패: {e}")
#             return False
# 
#     def get_database_stats(self) -> dict:
#         """데이터베이스 통계 정보"""
#         try:
#             with self.SessionLocal() as session:
#                 # 회의실 수
#                 room_count = session.query(MeetingRoomEntity).count()
# 
#                 # 예약 수
#                 reservation_count = session.query(ReservationEntity).count()
# 
#                 # 오늘 예약 수
#                 today = datetime.now().date()
#                 today_reservations = session.query(ReservationEntity).filter(
#                     func.date(ReservationEntity.start_time) == today
#                 ).count()
# 
#                 # 활성 회의실 수
#                 active_rooms = session.query(MeetingRoomEntity).filter(
#                     MeetingRoomEntity.status == 'available'
#                 ).count()
# 
#                 return {
#                     'total_rooms': room_count,
#                     'active_rooms': active_rooms,
#                     'total_reservations': reservation_count,
#                     'today_reservations': today_reservations,
#                     'database_url': str(self.engine.url).replace(self.engine.url.password,
#                                                                  '***') if self.engine.url.password else str(
#                         self.engine.url)
#                 }
# 
#         except Exception as e:
#             logger.error(f"데이터베이스 통계 조회 실패: {e}")
#             return {}
# 
#     def get_session(self) -> Session:
#         """SQLAlchemy 세션 반환 (고급 사용자용)"""
#         return self.SessionLocal()
# 
#     def close(self):
#         """데이터베이스 연결 종료"""
#         self.engine.dispose()
#         logger.info("데이터베이스 연결 종료")
# 
#     def health_check(self) -> bool:
#         """데이터베이스 연결 상태 확인"""
#         try:
#             from sqlalchemy import text
#             with self.SessionLocal() as session:
#                 session.execute(text("SELECT 1"))
#                 return True
#         except Exception as e:
#             logger.error(f"데이터베이스 연결 확인 실패: {e}")
#             return False
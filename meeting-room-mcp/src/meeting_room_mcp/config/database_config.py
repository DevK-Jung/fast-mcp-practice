"""
데이터베이스 연결 설정 및 관리
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class DatabaseConfig:
    """데이터베이스 연결 설정 관리"""
    
    def __init__(self, database_url: str):
        """
        database_url 예시:
        mysql+pymysql://username:password@localhost:3306/meeting_room_db
        sqlite:///./data/meeting_room.db
        """
        self.database_url = database_url
        
        # SQLite 개발용 설정
        if database_url.startswith('sqlite'):
            self.engine = create_engine(
                database_url,
                echo=False,  # SQL 로그 출력 여부
                connect_args={"check_same_thread": False}
            )
        else:
            # MySQL 프로덕션 설정  
            self.engine = create_engine(
                database_url,
                echo=False,  # SQL 로그 출력 여부
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # 연결 상태 확인
                pool_recycle=3600  # 1시간마다 연결 재생성
            )

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """SQLAlchemy 세션 반환"""
        return self.SessionLocal()
    
    def create_tables(self):
        """모든 테이블 생성"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("데이터베이스 테이블 생성 완료")
    
    def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            from sqlalchemy import text
            with self.SessionLocal() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 확인 실패: {e}")
            return False
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.engine.dispose()
        logger.info("데이터베이스 연결 종료")
"""
프로젝트 설정 모듈
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 데이터베이스 설정 (MySQL)
    db_host: str = Field(default="localhost", description="MySQL 호스트")
    db_port: int = Field(default=3306, description="MySQL 포트")
    db_username: str = Field(default="meeting_user", description="MySQL 사용자명")
    db_password: str = Field(default="meeting_password", description="MySQL 비밀번호")
    db_name: str = Field(default="meeting_room_db", description="데이터베이스 이름")

    @property
    def database_url(self) -> str:
        """MySQL 연결 URL 생성"""
        return f"mysql+pymysql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"

    # API 설정
    api_host: str = Field(default="0.0.0.0", description="API 서버 호스트")
    api_port: int = Field(default=8000, description="API 서버 포트")
    api_debug: bool = Field(default=False, description="API 디버그 모드")

    # MCP 서버 설정
    mcp_server_script: str = Field(
        default=str(PROJECT_ROOT / "scripts" / "start_server.py"),
        description="MCP 서버 스크립트 경로"
    )

    # LLM API 키들
    openai_api_key: str = Field(default="", description="OpenAI API 키")
    anthropic_api_key: str = Field(default="", description="Anthropic API 키")

    # 이메일 설정
    smtp_server: str = Field(default="localhost", description="SMTP 서버")
    smtp_port: int = Field(default=587, description="SMTP 포트")
    smtp_username: str = Field(default="", description="SMTP 사용자명")
    smtp_password: str = Field(default="", description="SMTP 비밀번호")
    smtp_use_tls: bool = Field(default=True, description="SMTP TLS 사용")
    email_mock_mode: bool = Field(default=True, description="이메일 모의 모드")

    # 로깅 설정
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_dir: Path = Field(default=PROJECT_ROOT / "logs", description="로그 디렉토리")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="로그 포맷"
    )

    # 세션 관리
    session_file: str = Field(
        default=str(PROJECT_ROOT / "data" / "sessions.json"),
        description="세션 저장 파일"
    )
    session_cleanup_hours: int = Field(default=24, description="세션 정리 시간(시간)")

    # 보안 설정
    secret_key: str = Field(default="your-secret-key-change-in-production", description="보안 키")
    allowed_origins: list = Field(default=["*"], description="CORS 허용 도메인")

    # 애플리케이션 설정
    app_name: str = Field(default="Meeting Room MCP", description="애플리케이션 이름")
    app_version: str = Field(default="1.0.0", description="애플리케이션 버전")

    # 환경 설정
    environment: str = Field(default="development", description="실행 환경")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


class DatabaseSettings(BaseSettings):
    """데이터베이스 전용 설정"""

    # MySQL 설정
    mysql_host: str = Field(default="localhost")
    mysql_port: int = Field(default=3306)
    mysql_user: str = Field(default="meeting_user")
    mysql_password: str = Field(default="meeting_password")
    mysql_database: str = Field(default="meeting_room_db")
    mysql_charset: str = Field(default="utf8mb4")

    # 커넥션 풀 설정
    pool_size: int = Field(default=10, description="커넥션 풀 크기")
    max_overflow: int = Field(default=20, description="최대 오버플로우")
    pool_timeout: int = Field(default=30, description="커넥션 타임아웃")
    pool_recycle: int = Field(default=3600, description="커넥션 재활용 시간")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        extra = "allow"


class EmailSettings(BaseSettings):
    """이메일 전용 설정"""

    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_pass: str = Field(default="")
    smtp_tls: bool = Field(default=True)
    mock_mode: bool = Field(default=True)

    # 발송자 정보
    from_email: str = Field(default="meeting-system@company.com")
    from_name: str = Field(default="회의실 예약 시스템")

    # 템플릿 설정
    template_dir: str = Field(default=str(PROJECT_ROOT / "templates" / "email"))

    class Config:
        env_prefix = "EMAIL_"
        env_file = ".env"
        extra = "allow"


class LLMSettings(BaseSettings):
    """LLM 관련 설정"""

    # OpenAI 설정
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4-turbo-preview")
    openai_temperature: float = Field(default=0.1)
    openai_max_tokens: int = Field(default=1000)

    # Anthropic 설정
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")
    anthropic_max_tokens: int = Field(default=1000)

    # 공통 설정
    default_provider: str = Field(default="openai", description="기본 LLM 제공자")
    timeout: int = Field(default=30, description="LLM API 타임아웃")

    class Config:
        env_prefix = "LLM_"
        env_file = ".env"
        extra = "allow"


# 전역 설정 인스턴스들
settings = Settings()
db_settings = DatabaseSettings()
email_settings = EmailSettings()
llm_settings = LLMSettings()


def get_settings() -> Settings:
    """메인 설정 반환"""
    return settings


def get_db_settings() -> DatabaseSettings:
    """데이터베이스 설정 반환"""
    return db_settings


def get_email_settings() -> EmailSettings:
    """이메일 설정 반환"""
    return email_settings


def get_llm_settings() -> LLMSettings:
    """LLM 설정 반환"""
    return llm_settings


def validate_settings():
    """설정 값 검증"""
    errors = []

    # 필수 설정 체크
    if settings.is_production:
        if not settings.secret_key or settings.secret_key == "your-secret-key-change-in-production":
            errors.append("Production 환경에서는 SECRET_KEY를 설정해야 합니다")

        if not db_settings.mysql_password:
            errors.append("Production 환경에서는 데이터베이스 비밀번호를 설정해야 합니다")

    # LLM API 키 체크
    # if not llm_settings.openai_api_key and not llm_settings.anthropic_api_key:
    #     errors.append("최소 하나의 LLM API 키를 설정해야 합니다")

    # 디렉토리 생성
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.session_file).parent.mkdir(parents=True, exist_ok=True)

    if errors:
        raise ValueError("설정 오류:\n" + "\n".join(f"- {error}" for error in errors))


# 초기화 시 설정 검증
if __name__ != "__main__":
    try:
        validate_settings()
    except ValueError as e:
        import logging
        logging.getLogger(__name__).warning(f"설정 검증 실패: {e}")


# 환경별 설정 오버라이드
if settings.environment == "test":
    # 테스트 환경 설정
    settings.db_name = "meeting_room_test_db"
    settings.email_mock_mode = True
    settings.log_level = "DEBUG"

elif settings.environment == "production":
    # 프로덕션 환경 설정
    settings.api_debug = False
    settings.email_mock_mode = False
    settings.log_level = "INFO"
"""
Configuration Settings

환경변수 기반 애플리케이션 설정
"""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Environment
    env: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///./interviews.db"
    redis_url: str = "redis://localhost:6379"
    
    # External APIs
    github_token: Optional[str] = None
    openai_api_key: Optional[str] = None  # Deprecated - Use Gemini instead
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None  # Required for Gemini
    
    # LangSmith
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "techgiterview"
    
    # Vector Database
    chroma_host: str = "localhost"
    chroma_port: int = 8000  # 8001과 충돌 방지를 위해 8000으로 변경
    
    # Security
    secret_key: str = "default_secret_key_for_development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,https://tgv.oursophy.com"
    
    def get_allowed_origins(self) -> List[str]:
        """CORS allowed origins 리스트 반환"""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return self.allowed_origins
    
    # GitHub API
    github_api_base_url: str = "https://api.github.com"
    github_rate_limit_per_hour: int = 5000
    
    # Performance
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    cache_ttl_seconds: int = 3600
    
    class Config:
        env_file = ".env.dev"
        case_sensitive = False
        env_file_encoding = 'utf-8'


def check_env_file_exists() -> bool:
    """환경 파일이 존재하는지 확인"""
    env = os.getenv("ENV", "development")
    env_file_name = f".env.{env}" if env != "development" else ".env.dev"
    return os.path.exists(env_file_name)


def is_development_mode_active() -> bool:
    """
    개발 모드 활성화 여부 확인
    
    .env.dev 파일이 존재하는 경우에만 개발 모드로 간주
    이를 통해 최근 활동 섹션의 표시 여부를 제어
    """
    try:
        # .env.dev 파일의 절대 경로 확인
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # src/backend 디렉토리
        env_dev_path = os.path.join(current_dir, ".env.dev")
        
        exists = os.path.exists(env_dev_path)
        print(f"[CONFIG] 개발 모드 체크 - .env.dev 파일: {env_dev_path} (존재: {exists})")
        return exists
    except Exception as e:
        print(f"[CONFIG] 개발 모드 체크 오류: {e}")
        return False


def update_api_keys(github_token: str, google_api_key: str) -> None:
    """런타임에 API 키 업데이트 및 AI 서비스 재초기화"""
    import logging
    
    logger = logging.getLogger(__name__)
    global settings
    settings.github_token = github_token
    settings.google_api_key = google_api_key
    
    # AI 서비스 재초기화
    try:
        from app.core.ai_service import ai_service
        logger.info("Reinitializing AI service with new API keys...")
        ai_service.reinitialize()
        
        # 사용 가능한 모든 프로바이더 로그
        for provider, config in ai_service.available_providers.items():
            logger.info(f"- {provider.value}: {config['model']} ({config['status']})")
            
    except Exception as e:
        logger.error(f"Failed to reinitialize AI service: {e}")
        raise


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 인스턴스 반환"""
    env = os.getenv("ENV", "development")
    env_file_name = f".env.{env}" if env != "development" else ".env.dev"
    
    class _Settings(Settings):
        class Config:
            env_file = env_file_name if os.path.exists(env_file_name) else None
            case_sensitive = False
    
    return _Settings()


# 전역 설정 인스턴스
settings = get_settings()
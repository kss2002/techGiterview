"""
Database Configuration

PostgreSQL 및 Redis 연결 설정
"""

import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .config import settings

# 데이터베이스 엔진 (SQLite/PostgreSQL 지원)
database_url = settings.database_url
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(
    database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 동기 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Base 클래스
Base = declarative_base()


def init_database_on_startup():
    """앱 시작시 데이터베이스 자동 초기화 - 테이블 누락 확인 및 생성 + 스키마 검증"""
    try:
        print("[DATABASE] 데이터베이스 초기화 확인 시작...")
        
        with engine.connect() as conn:
            # SQLite와 PostgreSQL 구분하여 테이블 목록 조회
            if "sqlite" in database_url.lower():
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            else:
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            
            existing_tables = [row[0] for row in result]
            print(f"[DATABASE] 기존 테이블: {existing_tables}")
            
            required_tables = ['repository_analyses', 'interview_sessions', 'interview_questions', 'interview_answers']
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if missing_tables:
                print(f"[DATABASE] 누락된 테이블 발견: {missing_tables}")
                print("[DATABASE] 테이블 자동 생성 중... (데이터 생성 없음)")
                
                # Base.metadata.create_all()로 모든 테이블 생성
                Base.metadata.create_all(bind=engine)
                
                # 생성 후 재확인
                if "sqlite" in database_url.lower():
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                else:
                    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
                
                created_tables = [row[0] for row in result]
                print(f"[DATABASE] 테이블 생성 완료: {created_tables}")
            else:
                print("[DATABASE] 모든 필요 테이블이 존재합니다.")
        
        # 🔧 스키마 검증 및 자동 마이그레이션 실행
        try:
            print("[DATABASE] 스키마 검증 및 자동 마이그레이션 시작...")
            from app.core.schema_validator import auto_validate_schema
            
            schema_result = auto_validate_schema()
            
            if schema_result['summary']['status'] == 'success':
                print(f"[DATABASE] ✅ 스키마 검증 완료: {schema_result['summary']}")
                if schema_result['added_columns']:
                    print(f"[DATABASE] 자동 추가된 컬럼: {schema_result['added_columns']}")
            elif schema_result['summary']['status'] == 'partial_success':
                print(f"[DATABASE] ⚠️  스키마 검증 부분 성공: {schema_result['summary']}")
                if schema_result['added_columns']:
                    print(f"[DATABASE] 자동 추가된 컬럼: {schema_result['added_columns']}")
                if schema_result['errors']:
                    print(f"[DATABASE] 오류 목록: {schema_result['errors']}")
            else:
                print(f"[DATABASE] ❌ 스키마 검증 실패: {schema_result['errors']}")
                
        except ImportError as e:
            print(f"[DATABASE] 스키마 검증 모듈 로드 실패: {e}")
        except Exception as e:
            print(f"[DATABASE] 스키마 검증 중 오류 (앱은 계속 실행): {e}")
                
    except Exception as e:
        print(f"[DATABASE] 초기화 오류 (앱은 계속 실행): {e}")
        # 오류가 있어도 앱은 계속 실행되도록 함


def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Redis 연결 풀
redis_pool = None


async def get_redis_pool():
    """Redis 연결 풀 생성"""
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20
        )
    return redis_pool


async def get_redis() -> redis.Redis:
    """Redis 클라이언트 반환"""
    pool = await get_redis_pool()
    return redis.Redis(connection_pool=pool)


async def close_db_connections():
    """데이터베이스 연결 종료"""
    global redis_pool
    
    # PostgreSQL 연결 종료 (임시 비활성화)
    # if engine:
    #     await engine.dispose()
    
    # Redis 연결 풀 종료
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None
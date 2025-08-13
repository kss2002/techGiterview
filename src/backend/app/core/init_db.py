"""
Database Initialization

데이터베이스 테이블 생성 및 초기화
"""

from sqlalchemy import create_engine
from app.core.database import Base
from app.core.config import settings
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer, InterviewConversation, InterviewReport
from app.models.user import User
from app.models.repository import RepositoryAnalysis


def create_tables():
    """모든 테이블 생성"""
    engine = create_engine(settings.database_url, echo=True)
    
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블이 성공적으로 생성되었습니다.")


if __name__ == "__main__":
    create_tables()
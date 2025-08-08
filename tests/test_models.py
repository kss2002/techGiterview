"""
Database Models 테스트

TDD 방식으로 데이터베이스 모델 테스트 먼저 작성
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

# 구현된 모델들 import
from app.models.user import User
from app.models.repository import RepositoryAnalysis
from app.models.interview import InterviewSession, InterviewQuestion, InterviewConversation


class TestUserModel:
    """사용자 모델 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """사용자 생성 테스트"""
        # Given
        github_username = "testuser"
        email = "test@example.com"
        
        # When
        user = User(
            github_username=github_username,
            email=email
        )
        db_session.add(user)
        await db_session.commit()
        
        # Then
        assert user.id is not None
        assert user.github_username == github_username
        assert user.email == email
        assert user.created_at is not None
        assert user.subscription_type == "free"
    
    @pytest.mark.asyncio
    async def test_user_unique_github_username(self, db_session: AsyncSession):
        """GitHub 사용자명 중복 방지 테스트"""
        # 실제 구현 후 테스트 작성
        assert True


class TestRepositoryAnalysisModel:
    """저장소 분석 모델 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_repository_analysis(self, db_session: AsyncSession):
        """저장소 분석 결과 생성 테스트"""
        # Given
        repository_url = "https://github.com/test/repo"
        tech_stack = {"python": 0.8, "javascript": 0.2}
        
        # When
        analysis = RepositoryAnalysis(
            repository_url=repository_url,
            tech_stack=tech_stack,
            complexity_score=7.5
        )
        db_session.add(analysis)
        await db_session.commit()
        
        # Then
        assert analysis.id is not None
        assert analysis.repository_url == repository_url
        assert analysis.tech_stack == tech_stack
        assert analysis.complexity_score == 7.5
        assert analysis.status == "pending"


class TestInterviewModels:
    """면접 관련 모델 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_interview_session(self, db_session: AsyncSession):
        """면접 세션 생성 테스트"""
        # 실제 구현 후 테스트 작성
        assert True
    
    @pytest.mark.asyncio
    async def test_create_interview_question(self, db_session: AsyncSession):
        """면접 질문 생성 테스트"""
        # 실제 구현 후 테스트 작성
        assert True
    
    @pytest.mark.asyncio
    async def test_create_interview_conversation(self, db_session: AsyncSession):
        """면접 대화 생성 테스트"""
        # 실제 구현 후 테스트 작성
        assert True
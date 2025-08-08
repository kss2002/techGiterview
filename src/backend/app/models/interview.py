"""
Interview Models

면접 관련 모델들
"""

from sqlalchemy import Column, String, DateTime, Integer, Numeric, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class InterviewQuestion(Base):
    """면접 질문 모델"""
    
    __tablename__ = "interview_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("repository_analyses.id"), nullable=False)
    category = Column(String(100), nullable=False)  # technical, behavioral, architectural
    difficulty = Column(String(50), nullable=False)  # junior, mid, senior
    question_text = Column(Text, nullable=False)
    expected_points = Column(JSON, nullable=True)  # 평가 포인트들
    related_files = Column(JSON, nullable=True)  # 관련 파일 경로들 (리스트)
    context = Column(JSON, nullable=True)  # 질문 생성 시 사용된 컨텍스트
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("RepositoryAnalysis", backref="interview_questions")
    
    def __repr__(self):
        return f"<InterviewQuestion(id={self.id}, category='{self.category}', difficulty='{self.difficulty}')>"


class InterviewSession(Base):
    """면접 세션 모델"""
    
    __tablename__ = "interview_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("repository_analyses.id"), nullable=False)
    interview_type = Column(String(50), nullable=False)  # technical, behavioral, mixed
    difficulty = Column(String(50), nullable=False)  # junior, mid, senior
    status = Column(String(50), default="active", nullable=False)  # active, completed, abandoned
    overall_score = Column(Numeric(3, 2), nullable=True)  # 전체 점수 (0.00 ~ 10.00)
    feedback = Column(JSON, nullable=True)  # 종합 피드백
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", backref="interview_sessions")
    analysis = relationship("RepositoryAnalysis", backref="interview_sessions")
    
    def __repr__(self):
        return f"<InterviewSession(id={self.id}, interview_type='{self.interview_type}', status='{self.status}')>"


class InterviewConversation(Base):
    """면접 대화 기록 모델"""
    
    __tablename__ = "interview_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("interview_questions.id"), nullable=True)
    conversation_order = Column(Integer, nullable=False)  # 대화 순서
    speaker = Column(String(20), nullable=False)  # 'ai' or 'user'
    message_type = Column(String(20), default="text", nullable=False)  # text, audio, system
    message_content = Column(Text, nullable=False)
    answer_score = Column(Numeric(3, 2), nullable=True)  # 개별 답변 점수
    ai_feedback = Column(Text, nullable=True)  # AI 피드백
    extra_metadata = Column(JSON, nullable=True)  # 추가 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("InterviewSession", backref="conversations")
    question = relationship("InterviewQuestion", backref="conversations")
    
    def __repr__(self):
        return f"<InterviewConversation(id={self.id}, speaker='{self.speaker}', order={self.conversation_order})>"


class InterviewReport(Base):
    """면접 결과 리포트 모델"""
    
    __tablename__ = "interview_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    overall_score = Column(Numeric(3, 2), nullable=False)
    category_scores = Column(JSON, nullable=False)  # {"technical": 8.5, "communication": 7.0}
    strengths = Column(JSON, nullable=True)  # 강점들 (리스트)
    improvements = Column(JSON, nullable=True)  # 개선점들 (리스트)
    recommendations = Column(JSON, nullable=True)  # 학습 추천사항
    detailed_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("InterviewSession", backref="report", uselist=False)
    
    def __repr__(self):
        return f"<InterviewReport(id={self.id}, overall_score={self.overall_score})>"
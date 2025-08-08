"""
Repository Analysis Models

저장소 분석 관련 모델
"""

from sqlalchemy import Column, String, DateTime, Integer, Numeric, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class RepositoryAnalysis(Base):
    """저장소 분석 결과 모델"""
    
    __tablename__ = "repository_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    repository_url = Column(String(500), nullable=False, index=True)
    repository_name = Column(String(255), nullable=True)
    primary_language = Column(String(100), nullable=True)
    tech_stack = Column(JSON, nullable=True)  # {"python": 0.8, "javascript": 0.2}
    file_count = Column(Integer, nullable=True)
    complexity_score = Column(Numeric(3, 2), nullable=True)  # 0.00 ~ 10.00
    analysis_metadata = Column(JSON, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, analyzing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="repository_analyses")
    
    def __repr__(self):
        return f"<RepositoryAnalysis(id={self.id}, repository_name='{self.repository_name}', status='{self.status}')>"


class AnalyzedFile(Base):
    """분석된 파일 정보 모델"""
    
    __tablename__ = "analyzed_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("repository_analyses.id"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=True)  # source, config, test, documentation
    language = Column(String(50), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    lines_of_code = Column(Integer, nullable=True)
    complexity_score = Column(Numeric(3, 2), nullable=True)
    importance_score = Column(Numeric(3, 2), nullable=True)  # AI가 계산한 중요도
    content_summary = Column(Text, nullable=True)  # LLM이 생성한 파일 요약
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("RepositoryAnalysis", backref="analyzed_files")
    
    def __repr__(self):
        return f"<AnalyzedFile(id={self.id}, file_path='{self.file_path}', importance_score={self.importance_score})>"
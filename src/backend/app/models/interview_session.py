"""
Interview Session Models

면접 세션 데이터 보존을 위한 데이터 모델들
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class InterviewStatus(str, Enum):
    """면접 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FeedbackType(str, Enum):
    """피드백 타입"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class MessageType(str, Enum):
    """메시지 타입"""
    SYSTEM = "system"
    USER = "user"
    AI = "ai"
    FEEDBACK = "feedback"


class QuestionFeedback(BaseModel):
    """질문별 피드백"""
    question_id: str
    score: float = Field(..., ge=0, le=10)
    message: str
    feedback_type: FeedbackType
    details: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionAnswer(BaseModel):
    """질문 답변"""
    question_id: str
    question_text: str
    user_answer: str
    response_time: int  # 초
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    feedback: Optional[QuestionFeedback] = None


class ConversationMessage(BaseModel):
    """대화 메시지"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    content: str
    question_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InterviewSessionData(BaseModel):
    """면접 세션 데이터 (영속성)"""
    interview_id: str
    analysis_id: str
    repo_url: str
    question_ids: List[str]
    current_question_index: int = 0
    interview_type: str = "technical"
    difficulty_level: str = "medium"
    status: InterviewStatus = InterviewStatus.ACTIVE
    participant_name: Optional[str] = None
    
    # 시간 정보
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expected_duration: int = 0  # 분
    
    # 답변 및 피드백 데이터
    answers: List[QuestionAnswer] = Field(default_factory=list)
    conversations: List[ConversationMessage] = Field(default_factory=list)
    
    # 진행 상황
    progress: Dict[str, Any] = Field(default_factory=dict)
    
    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_answer(self, question_id: str, question_text: str, user_answer: str, response_time: int) -> None:
        """답변 추가"""
        answer = QuestionAnswer(
            question_id=question_id,
            question_text=question_text,
            user_answer=user_answer,
            response_time=response_time
        )
        self.answers.append(answer)
        self.updated_at = datetime.utcnow()

    def add_feedback(self, question_id: str, feedback: QuestionFeedback) -> None:
        """피드백 추가"""
        for answer in self.answers:
            if answer.question_id == question_id:
                answer.feedback = feedback
                self.updated_at = datetime.utcnow()
                break

    def add_conversation_message(self, message_type: MessageType, content: str, 
                               question_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> str:
        """대화 메시지 추가"""
        message = ConversationMessage(
            type=message_type,
            content=content,
            question_id=question_id,
            metadata=metadata or {}
        )
        self.conversations.append(message)
        self.updated_at = datetime.utcnow()
        return message.id

    def get_answer_by_question_id(self, question_id: str) -> Optional[QuestionAnswer]:
        """질문 ID로 답변 조회"""
        for answer in self.answers:
            if answer.question_id == question_id:
                return answer
        return None

    def get_conversation_messages_for_question(self, question_id: str) -> List[ConversationMessage]:
        """특정 질문에 대한 대화 메시지들 조회"""
        return [msg for msg in self.conversations if msg.question_id == question_id]

    def calculate_progress(self) -> Dict[str, Any]:
        """진행률 계산"""
        total_questions = len(self.question_ids)
        answered_questions = len(self.answers)
        
        progress_percentage = (self.current_question_index / total_questions * 100) if total_questions > 0 else 0
        
        elapsed_time = int((datetime.utcnow() - self.started_at).total_seconds())
        remaining_time = max(0, self.expected_duration * 60 - elapsed_time) if self.expected_duration > 0 else 0
        
        return {
            "current_question": self.current_question_index + 1,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "progress_percentage": round(progress_percentage, 1),
            "elapsed_time": elapsed_time,
            "remaining_time": remaining_time,
            "completion_rate": round((answered_questions / total_questions) * 100, 1) if total_questions > 0 else 0
        }

    def calculate_average_score(self) -> float:
        """평균 점수 계산"""
        scores = [answer.feedback.score for answer in self.answers if answer.feedback]
        return sum(scores) / len(scores) if scores else 0.0

    def is_completed(self) -> bool:
        """면접 완료 여부"""
        return self.status == InterviewStatus.COMPLETED or self.current_question_index >= len(self.question_ids)

    def complete_interview(self) -> None:
        """면접 완료 처리"""
        self.status = InterviewStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_summary(self) -> Dict[str, Any]:
        """세션 요약 정보"""
        progress = self.calculate_progress()
        
        return {
            "interview_id": self.interview_id,
            "analysis_id": self.analysis_id,
            "repo_url": self.repo_url,
            "status": self.status.value,
            "interview_type": self.interview_type,
            "difficulty_level": self.difficulty_level,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": progress,
            "average_score": self.calculate_average_score(),
            "participant_name": self.participant_name
        }


class InterviewSessionManager:
    """면접 세션 관리자"""
    
    def __init__(self):
        self._sessions: Dict[str, InterviewSessionData] = {}
    
    def create_session(self, interview_id: str, analysis_id: str, repo_url: str, 
                      question_ids: List[str], **kwargs) -> InterviewSessionData:
        """새 세션 생성"""
        session = InterviewSessionData(
            interview_id=interview_id,
            analysis_id=analysis_id,
            repo_url=repo_url,
            question_ids=question_ids,
            expected_duration=len(question_ids) * 30,  # 질문당 30분
            **kwargs
        )
        self._sessions[interview_id] = session
        return session
    
    def get_session(self, interview_id: str) -> Optional[InterviewSessionData]:
        """세션 조회"""
        return self._sessions.get(interview_id)
    
    def update_session(self, interview_id: str, session: InterviewSessionData) -> None:
        """세션 업데이트"""
        session.updated_at = datetime.utcnow()
        self._sessions[interview_id] = session
    
    def delete_session(self, interview_id: str) -> bool:
        """세션 삭제"""
        if interview_id in self._sessions:
            del self._sessions[interview_id]
            return True
        return False
    
    def list_sessions(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """세션 목록 조회"""
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        return [session.to_summary() for session in sessions[offset:offset + limit]]
    
    def get_session_count(self) -> int:
        """전체 세션 수"""
        return len(self._sessions)
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """만료된 세션 정리"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = []
        
        for interview_id, session in self._sessions.items():
            if session.created_at < cutoff_time and session.status != InterviewStatus.ACTIVE:
                expired_sessions.append(interview_id)
        
        for interview_id in expired_sessions:
            del self._sessions[interview_id]
        
        return len(expired_sessions)


# 전역 세션 매니저 인스턴스
session_manager = InterviewSessionManager()
"""
Interview Repository Service

면접 세션 데이터 영구 저장 및 조회를 위한 데이터베이스 레이어
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.interview import (
    InterviewSession, 
    InterviewQuestion, 
    InterviewAnswer, 
    InterviewConversation,
    InterviewReport
)
from app.models.repository import RepositoryAnalysis
from app.core.database import get_db


class InterviewRepository:
    """면접 데이터 저장소 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, data: Dict[str, Any]) -> InterviewSession:
        """새 면접 세션 생성"""
        session = InterviewSession(
            id=uuid.uuid4(),
            user_id=data.get('user_id', None),  # 더미 데이터 생성 없이 NULL 사용 (게스트 지원)
            analysis_id=data['analysis_id'],
            interview_type=data.get('interview_type', 'technical'),
            difficulty=data.get('difficulty_level', 'medium'),
            status='active',
            started_at=datetime.utcnow()
        )
        
        print(f"[REPO] 면접 세션 생성: {session.id}, analysis_id: {session.analysis_id}")
        self.db.add(session)
        # commit은 상위 레벨(API)에서 처리하도록 변경
        self.db.flush()  # DB에 반영하지만 commit하지 않음
        
        return session
    
    def get_session(self, session_id: uuid.UUID) -> Optional[InterviewSession]:
        """면접 세션 조회"""
        print(f"[REPO] 면접 세션 조회 시도: {session_id}")
        session = self.db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()
        
        if session:
            print(f"[REPO] 면접 세션 조회 성공: {session.id}, status: {session.status}")
        else:
            print(f"[REPO] 면접 세션 조회 실패: {session_id} - 세션을 찾을 수 없음")
            
        return session
    
    def get_session_with_details(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """면접 세션 상세 정보 조회 (답변, 대화 포함)"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # 답변 조회
        answers = self.db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session_id
        ).order_by(InterviewAnswer.submitted_at).all()
        
        # 대화 조회
        conversations = self.db.query(InterviewConversation).filter(
            InterviewConversation.session_id == session_id
        ).order_by(InterviewConversation.conversation_order).all()
        
        return {
            'session': session,
            'answers': answers,
            'conversations': conversations,
            'progress': self._calculate_progress(session, answers)
        }
    
    def save_answer(self, session_id: uuid.UUID, question_id: uuid.UUID, 
                   answer_data: Dict[str, Any]) -> InterviewAnswer:
        """답변 저장"""
        # 기존 답변 확인 (수정 케이스)
        existing_answer = self.db.query(InterviewAnswer).filter(
            and_(
                InterviewAnswer.session_id == session_id,
                InterviewAnswer.question_id == question_id
            )
        ).first()
        
        if existing_answer:
            # 기존 답변 업데이트
            existing_answer.user_answer = answer_data['answer']
            existing_answer.time_taken_seconds = answer_data.get('time_taken', 0)
            existing_answer.updated_at = datetime.utcnow()
            
            if 'feedback' in answer_data:
                feedback = answer_data['feedback']
                existing_answer.feedback_score = feedback.get('score')
                existing_answer.feedback_message = feedback.get('message')
                existing_answer.feedback_details = feedback
            
            answer = existing_answer
        else:
            # 새 답변 생성
            answer = InterviewAnswer(
                session_id=session_id,
                question_id=question_id,
                user_answer=answer_data['answer'],
                time_taken_seconds=answer_data.get('time_taken', 0)
            )
            
            if 'feedback' in answer_data:
                feedback = answer_data['feedback']
                answer.feedback_score = feedback.get('score')
                answer.feedback_message = feedback.get('message')
                answer.feedback_details = feedback
            
            self.db.add(answer)
        
        self.db.commit()
        self.db.refresh(answer)
        
        return answer
    
    def save_conversation(self, session_id: uuid.UUID, conversation_data: Dict[str, Any]) -> InterviewConversation:
        """대화 메시지 저장"""
        # 기존 대화 순서 확인
        max_order = self.db.query(InterviewConversation).filter(
            InterviewConversation.session_id == session_id
        ).order_by(desc(InterviewConversation.conversation_order)).first()
        
        next_order = (max_order.conversation_order + 1) if max_order else 1
        
        conversation = InterviewConversation(
            session_id=session_id,
            question_id=conversation_data.get('question_id'),
            conversation_order=next_order,
            speaker=conversation_data['speaker'],  # 'user' or 'ai'
            message_type=conversation_data.get('message_type', 'text'),
            message_content=conversation_data['content'],
            answer_score=conversation_data.get('score'),
            ai_feedback=conversation_data.get('feedback'),
            extra_metadata=conversation_data.get('metadata')
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def update_session_status(self, session_id: uuid.UUID, status: str) -> bool:
        """세션 상태 업데이트"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.status = status
        if status == 'completed':
            session.ended_at = datetime.utcnow()
            
            # 평균 점수 계산
            answers = self.db.query(InterviewAnswer).filter(
                and_(
                    InterviewAnswer.session_id == session_id,
                    InterviewAnswer.feedback_score.isnot(None)
                )
            ).all()
            
            if answers:
                avg_score = sum(a.feedback_score for a in answers) / len(answers)
                session.overall_score = round(avg_score, 2)
        
        self.db.commit()
        return True
    
    def get_active_sessions(self, limit: int = 10) -> List[InterviewSession]:
        """활성 세션 목록 조회"""
        return self.db.query(InterviewSession).filter(
            InterviewSession.status == 'active'
        ).order_by(desc(InterviewSession.started_at)).limit(limit).all()
    
    def get_latest_session(self) -> Optional[InterviewSession]:
        """가장 최근 세션 조회"""
        return self.db.query(InterviewSession).order_by(
            desc(InterviewSession.started_at)
        ).first()
    
    def _calculate_progress(self, session: InterviewSession, answers: List[InterviewAnswer]) -> Dict[str, Any]:
        """진행률 계산"""
        # 해당 분석에서 생성된 질문 수 확인
        total_questions = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.analysis_id == session.analysis_id
        ).count()
        
        answered_questions = len(answers)
        elapsed_time = int((datetime.utcnow() - session.started_at).total_seconds())
        
        return {
            "current_question": answered_questions + 1,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "progress_percentage": round((answered_questions / total_questions) * 100, 1) if total_questions > 0 else 0,
            "elapsed_time": elapsed_time,
            "remaining_time": max(0, (total_questions * 5 * 60) - elapsed_time),  # 질문당 5분 예상
            "completion_rate": round((answered_questions / total_questions) * 100, 1) if total_questions > 0 else 0
        }


def get_interview_repository(db: Session = None) -> InterviewRepository:
    """InterviewRepository 인스턴스 생성 헬퍼"""
    if db is None:
        db = next(get_db())
    return InterviewRepository(db)
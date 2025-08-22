"""
Interview API Router - Database-based Version

실제 데이터베이스를 사용한 영구 면접 세션 관리 API
"""

import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.interview_repository import InterviewRepository
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.agents.mock_interview_agent import MockInterviewAgent


router = APIRouter()


class InterviewStartRequest(BaseModel):
    """면접 시작 요청"""
    repo_url: HttpUrl
    analysis_id: str
    question_ids: List[str]
    interview_type: str = "technical"
    difficulty_level: str = "medium"


class AnswerSubmitRequest(BaseModel):
    """답변 제출 요청"""
    interview_id: str
    question_id: str
    answer: str
    time_taken: int = 0


class ConversationRequest(BaseModel):
    """대화 요청"""
    interview_id: str
    question_id: str
    original_answer: str
    conversation_question: str


@router.post("/start")
async def start_interview(
    request: InterviewStartRequest, 
    db: Session = Depends(get_db),
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key")
):
    """새 면접 세션 시작"""
    try:
        # API 키 우선순위 결정: .env.dev > 헤더 > 기본값
        from app.core.config import settings
        
        # GitHub Token 우선순위
        effective_github_token = None
        if settings.github_token and settings.github_token != "your_github_token_here":
            effective_github_token = settings.github_token
            github_token_source = "환경변수(.env.dev)"
        elif github_token:
            effective_github_token = github_token
            github_token_source = "요청 헤더"
        else:
            github_token_source = "없음"
        
        # Google API Key 우선순위
        effective_google_api_key = None
        if settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
            effective_google_api_key = settings.google_api_key
            google_api_key_source = "환경변수(.env.dev)"
        elif google_api_key:
            effective_google_api_key = google_api_key
            google_api_key_source = "요청 헤더"
        else:
            google_api_key_source = "없음"
        
        # API 키 사용 현황 로깅
        print(f"[INTERVIEW_START] ========== 면접 시작 요청 ==========")
        print(f"[INTERVIEW_START] 분석 ID: {request.analysis_id}")
        print(f"[INTERVIEW_START] API 키 사용 현황:")
        print(f"[INTERVIEW_START]   - GitHub Token: {github_token_source}")
        print(f"[INTERVIEW_START]   - Google API Key: {google_api_key_source}")
        if effective_github_token:
            print(f"[INTERVIEW_START]   - 사용될 GitHub Token: {effective_github_token[:20]}...")
        if effective_google_api_key:
            print(f"[INTERVIEW_START]   - 사용될 Google API Key: {effective_google_api_key[:20]}...")
        
        # 질문 ID 유효성 검증
        if not request.question_ids:
            raise HTTPException(status_code=400, detail="질문 ID가 제공되지 않았습니다.")
        
        # 질문 캐시에서 질문 데이터 확인 (실제 질문이 없으면 오류 반환 - 더미데이터 생성 없음)
        from app.api.questions import question_cache
        # UUID 정규화: 하이픈 제거하여 캐시 키와 매칭
        normalized_analysis_id = request.analysis_id.replace('-', '')
        
        if normalized_analysis_id not in question_cache:
            print(f"[ERROR] 질문 캐시 없음: {normalized_analysis_id}")
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "QUESTIONS_NOT_FOUND", 
                    "message": "해당 분석 ID에 대한 질문이 존재하지 않습니다.",
                    "analysis_id": request.analysis_id,
                    "suggestion": "먼저 질문 생성을 완료해주세요."
                }
            )
        
        cache_data = question_cache[normalized_analysis_id]
        cached_questions = cache_data.parsed_questions
        available_question_ids = {q.id for q in cached_questions}
        
        # 요청된 질문 ID가 모두 캐시에 있는지 확인
        missing_question_ids = set(request.question_ids) - available_question_ids
        if missing_question_ids:
            print(f"[ERROR] 요청한 질문 ID 없음: {missing_question_ids}")
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "INVALID_QUESTION_IDS",
                    "message": f"요청한 질문 중 존재하지 않는 ID가 있습니다: {list(missing_question_ids)}",
                    "available_question_ids": list(available_question_ids),
                    "missing_question_ids": list(missing_question_ids)
                }
            )
        
        # 분석 ID 검증 - 다양한 UUID 형식으로 조회 시도
        from app.models.repository import RepositoryAnalysis
        
        analysis = None
        analysis_uuid = None
        
        # 1. 하이픈 포함된 원본 ID로 시도
        try:
            analysis_uuid = uuid.UUID(request.analysis_id)
            analysis = db.query(RepositoryAnalysis).filter(
                RepositoryAnalysis.id == analysis_uuid
            ).first()
            if analysis:
                print(f"[SUCCESS] 분석 데이터 찾음 (하이픈 포함): {request.analysis_id}")
        except ValueError:
            pass
        
        # 2. 하이픈 제거된 ID로 시도
        if not analysis:
            try:
                cleaned_id = request.analysis_id.replace('-', '')
                analysis_uuid = uuid.UUID(f"{cleaned_id[:8]}-{cleaned_id[8:12]}-{cleaned_id[12:16]}-{cleaned_id[16:20]}-{cleaned_id[20:]}")
                analysis = db.query(RepositoryAnalysis).filter(
                    RepositoryAnalysis.id == analysis_uuid
                ).first()
                if analysis:
                    print(f"[SUCCESS] 분석 데이터 찾음 (하이픈 제거 후 재조합): {analysis_uuid}")
            except (ValueError, IndexError):
                pass
        
        # 3. 문자열로 직접 조회 시도
        if not analysis:
            try:
                from sqlalchemy import text
                # 하이픈 포함/제거 모두 시도
                result = db.execute(text("SELECT * FROM repository_analyses WHERE id = :id1 OR id = :id2"), 
                                  {"id1": request.analysis_id, "id2": request.analysis_id.replace('-', '')})
                row = result.fetchone()
                if row:
                    analysis_uuid = uuid.UUID(str(row[0]))  # id 컬럼
                    analysis = db.query(RepositoryAnalysis).filter(
                        RepositoryAnalysis.id == analysis_uuid
                    ).first()
                    if analysis:
                        print(f"[SUCCESS] 분석 데이터 찾음 (문자열 직접 조회): {analysis_uuid}")
            except Exception as e:
                print(f"[DEBUG] 문자열 직접 조회 실패: {e}")
        
        if not analysis:
            print(f"[ERROR] 분석 데이터 없음: {request.analysis_id}")
            # 데이터베이스에 어떤 분석 데이터가 있는지 확인
            try:
                from sqlalchemy import text
                result = db.execute(text("SELECT id FROM repository_analyses LIMIT 5"))
                existing_ids = [str(row[0]) for row in result.fetchall()]
                print(f"[DEBUG] 데이터베이스의 기존 분석 ID들: {existing_ids}")
            except Exception as e:
                print(f"[DEBUG] 기존 분석 ID 조회 실패: {e}")
                
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "ANALYSIS_NOT_FOUND",
                    "message": "해당 분석 ID에 대한 분석 데이터가 존재하지 않습니다.",
                    "analysis_id": request.analysis_id,
                    "suggestion": "먼저 저장소 분석을 완료해주세요."
                }
            )
        
        # InterviewRepository를 사용하여 세션 생성
        repo = InterviewRepository(db)
        session = repo.create_session({
            'analysis_id': analysis_uuid,
            'interview_type': request.interview_type,
            'difficulty_level': request.difficulty_level
        })
        
        # 선택된 질문들을 데이터베이스에 저장 (필요시)
        question_id_mapping = {}  # 원본 ID -> UUID 매핑
        
        for question_data in cached_questions:
            if question_data.id in request.question_ids:
                # 질문 ID가 UUID 형식인지 확인
                try:
                    question_uuid = uuid.UUID(question_data.id)
                    # UUID 형식이면 기존 질문 확인
                    existing_question = db.query(InterviewQuestion).filter(
                        InterviewQuestion.id == question_uuid
                    ).first()
                except ValueError:
                    # UUID 형식이 아니면 새 UUID 생성
                    question_uuid = uuid.uuid4()
                    existing_question = None
                
                question_id_mapping[question_data.id] = question_uuid
                
                if not existing_question:
                    # 새 질문 저장
                    db_question = InterviewQuestion(
                        id=question_uuid,
                        analysis_id=analysis_uuid,
                        category=question_data.type,  # QuestionResponse uses 'type' not 'category'
                        difficulty=question_data.difficulty,
                        question_text=question_data.question,
                        context={"original_data": question_data.dict(), "original_id": question_data.id}
                    )
                    db.add(db_question)
        
        db.commit()
        
        return {
            "success": True,
            "message": "면접이 성공적으로 시작되었습니다.",
            "data": {
                "interview_id": str(session.id),
                "analysis_id": request.analysis_id,
                "interview_type": session.interview_type,
                "difficulty": session.difficulty,
                "status": session.status,
                "started_at": session.started_at.isoformat(),
                "question_count": len(request.question_ids)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"면접 시작에 실패했습니다: {str(e)}")


@router.get("/session/{interview_id}")
async def get_interview_session(interview_id: str, db: Session = Depends(get_db)):
    """면접 세션 정보 조회"""
    try:
        # UUID 정규화 후 검증
        normalized_interview_id = normalize_uuid_string(interview_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        print(f"[DEBUG] 면접 세션 조회 - UUID 정규화: '{interview_id}' → '{normalized_interview_id}'")
    except ValueError as e:
        print(f"[ERROR] 면접 ID UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 면접 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    session_data = repo.get_session_with_details(session_uuid)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    session = session_data['session']
    progress = session_data['progress']
    
    return {
        "success": True,
        "data": {
            "interview_id": str(session.id),
            "analysis_id": str(session.analysis_id),
            "interview_type": session.interview_type,
            "difficulty_level": session.difficulty,
            "status": session.status,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "overall_score": float(session.overall_score) if session.overall_score else None,
            "progress": progress
        }
    }


@router.get("/session/{interview_id}/questions")
async def get_interview_questions(interview_id: str, db: Session = Depends(get_db)):
    """면접 질문 목록 조회"""
    try:
        normalized_interview_id = normalize_uuid_string(interview_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        print(f"[DEBUG] 면접 질문 조회 - UUID 정규화: '{interview_id}' → '{normalized_interview_id}'")
    except ValueError as e:
        print(f"[ERROR] 면접 ID UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 면접 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    session = repo.get_session(session_uuid)
    
    if not session:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    # 해당 분석의 모든 질문 조회
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.analysis_id == session.analysis_id
    ).all()
    
    # 답변된 질문 수 확인
    answered_count = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_uuid
    ).count()
    
    questions_data = []
    for question in questions:
        questions_data.append({
            "id": str(question.id),
            "question": question.question_text,
            "category": question.category,
            "difficulty": question.difficulty,
            "context": question.context.get("original_data") if question.context else None
        })
    
    return {
        "success": True,
        "data": {
            "questions": questions_data,
            "current_question_index": answered_count,
            "total_questions": len(questions_data)
        }
    }


@router.get("/session/{interview_id}/data")
async def get_session_data(interview_id: str, db: Session = Depends(get_db)):
    """세션 데이터 상세 조회 (답변 및 피드백 포함)"""
    try:
        normalized_interview_id = normalize_uuid_string(interview_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        print(f"[DEBUG] 면접 질문 조회 - UUID 정규화: '{interview_id}' → '{normalized_interview_id}'")
    except ValueError as e:
        print(f"[ERROR] 면접 ID UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 면접 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    session_data = repo.get_session_with_details(session_uuid)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    # 답변 데이터 포맷팅
    answers_data = []
    for answer in session_data['answers']:
        answers_data.append({
            "question_id": str(answer.question_id),
            "user_answer": answer.user_answer,
            "submitted_at": answer.submitted_at.isoformat(),
            "feedback": {
                "score": float(answer.feedback_score) if answer.feedback_score else None,
                "message": answer.feedback_message,
                "details": answer.feedback_details,
                "created_at": answer.submitted_at.isoformat()
            } if answer.feedback_score else None
        })
    
    # 대화 데이터 포맷팅
    conversations_data = []
    for conv in session_data['conversations']:
        conversations_data.append({
            "id": str(conv.id),
            "question_id": str(conv.question_id) if conv.question_id else None,
            "type": conv.speaker,
            "content": conv.message_content,
            "timestamp": conv.created_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "answers": answers_data,
            "conversations": conversations_data,
            "progress": session_data['progress']
        }
    }


def normalize_uuid_string(uuid_str: str) -> str:
    """UUID 문자열을 표준 형식으로 변환 (하이픈 제거/추가 자동 처리)"""
    if not uuid_str:
        raise ValueError("UUID 문자열이 비어있습니다.")
    
    # 하이픈 제거
    cleaned = uuid_str.replace('-', '')
    
    # 길이 검증
    if len(cleaned) != 32:
        raise ValueError(f"UUID 길이가 올바르지 않습니다: {len(cleaned)} (32 필요)")
    
    # 표준 UUID 형식으로 변환
    return f"{cleaned[:8]}-{cleaned[8:12]}-{cleaned[12:16]}-{cleaned[16:20]}-{cleaned[20:]}"


@router.post("/answer")
async def submit_answer(
    request: AnswerSubmitRequest, 
    db: Session = Depends(get_db),
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key")
):
    """답변 제출"""
    print(f"[SUBMIT_ANSWER] ========== 답변 제출 요청 ===========")
    print(f"[SUBMIT_ANSWER] interview_id: '{request.interview_id}'")
    print(f"[SUBMIT_ANSWER] question_id: '{request.question_id}'")
    print(f"[SUBMIT_ANSWER] answer: '{request.answer[:50]}...'")
    print(f"[SUBMIT_ANSWER] 받은 헤더:")
    print(f"[SUBMIT_ANSWER]   - GitHub Token: {'있음' if github_token else '없음'}")
    print(f"[SUBMIT_ANSWER]   - Google API Key: {'있음' if google_api_key else '없음'}")
    if github_token:
        print(f"[SUBMIT_ANSWER]   - GitHub Token 값: {github_token[:20]}...")
    if google_api_key:
        print(f"[SUBMIT_ANSWER]   - Google API Key 값: {google_api_key[:20]}...")
    
    try:
        # Interview ID는 UUID 형식으로 정규화 및 변환
        normalized_interview_id = normalize_uuid_string(request.interview_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        
        # Question ID는 UUID 형식인지 확인하고, 아니면 문자열 그대로 사용
        try:
            normalized_question_id = normalize_uuid_string(request.question_id)
            question_uuid = uuid.UUID(normalized_question_id)
            question_id_is_uuid = True
            print(f"[DEBUG] 질문 ID가 UUID 형식: {question_uuid}")
        except ValueError:
            # UUID 형식이 아니면 문자열 그대로 사용 (예: 'tech_stack_1632')
            question_id_is_uuid = False
            question_string_id = request.question_id
            print(f"[DEBUG] 질문 ID가 문자열 형식: {question_string_id}")
        
        print(f"[DEBUG] 정규화된 ID:")
        print(f"  - interview_id: '{normalized_interview_id}' → UUID: {session_uuid}")
        print(f"  - question_id: '{request.question_id}' → UUID 형식: {question_id_is_uuid}")
        
    except ValueError as e:
        print(f"[ERROR] Interview ID UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 면접 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    session = repo.get_session(session_uuid)
    
    if not session:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    if session.status != "active":
        raise HTTPException(status_code=400, detail="활성화된 면접 세션에만 답변할 수 있습니다.")
    
    try:
        # 질문 ID에 따른 조회 방식 결정
        if question_id_is_uuid:
            # UUID 형식의 질문 ID로 데이터베이스 조회
            existing_answer = db.query(InterviewAnswer).filter(
                InterviewAnswer.session_id == session_uuid,
                InterviewAnswer.question_id == question_uuid
            ).first()
            
            question = db.query(InterviewQuestion).filter(
                InterviewQuestion.id == question_uuid
            ).first()
            
            question_identifier = str(question_uuid)
            print(f"[DEBUG] UUID 질문 조회: {question_uuid}")
        else:
            # 문자열 질문 ID로 메모리 캐시에서 정보 가져오기
            existing_answer = None  # 문자열 ID는 데이터베이스에 저장되지 않음
            question = None  # 메모리 캐시의 질문 사용
            question_identifier = question_string_id
            print(f"[DEBUG] 문자열 질문 ID 사용: {question_string_id}")
            
        is_first_answer = existing_answer is None
        print(f"[DEBUG] 질문 {question_identifier}: 첫 번째 답변? {is_first_answer}")
        print(f"[DEBUG] 기존 답변 존재: {existing_answer is not None}")
        
        # 문자열 질문 ID의 경우 캐시에서 질문 정보 가져오기
        if not question_id_is_uuid:
            # 질문 캐시에서 질문 텍스트 찾기
            from app.api.questions import question_cache
            normalized_analysis_id = str(session.analysis_id).replace('-', '')  # 캐시 키 정규화
            
            if normalized_analysis_id in question_cache:
                cache_data = question_cache[normalized_analysis_id]
                cached_questions = cache_data.parsed_questions
                
                # 질문 ID로 질문 찾기
                cached_question = None
                for q in cached_questions:
                    if q.id == question_string_id:
                        cached_question = q
                        break
                
                if not cached_question:
                    raise HTTPException(status_code=404, detail=f"캐시에서 질문을 찾을 수 없습니다: {question_string_id}")
                    
                # 임시 질문 객체 생성
                class TempQuestion:
                    def __init__(self, q):
                        self.question_text = q.question
                        self.category = q.type
                        self.difficulty = q.difficulty
                        self.expected_points = getattr(q, 'expected_answer_points', [])
                        
                question = TempQuestion(cached_question)
                print(f"[DEBUG] 캐시에서 질문 정보 가져옴: {question.question_text[:50]}...")
            else:
                raise HTTPException(status_code=404, detail="질문 캐시를 찾을 수 없습니다.")
        elif not question:
            raise HTTPException(status_code=404, detail="데이터베이스에서 질문을 찾을 수 없습니다.")
        
        # Mock Interview Agent를 사용하여 피드백 생성 (우선순위 적용된 API 키 전달)
        from app.core.config import settings
        
        # GitHub Token 우선순위 적용
        effective_github_token = None
        if settings.github_token and settings.github_token != "your_github_token_here":
            effective_github_token = settings.github_token
        elif github_token:
            effective_github_token = github_token
            
        # Google API Key 우선순위 적용  
        effective_google_api_key = None
        if settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
            effective_google_api_key = settings.google_api_key
        elif google_api_key:
            effective_google_api_key = google_api_key
            
        interview_agent = MockInterviewAgent(github_token=effective_github_token, google_api_key=effective_google_api_key)
        
        # 피드백 생성 (답변 횟수 정보 포함)
        feedback_result = await interview_agent.evaluate_answer(
            question=question.question_text,
            answer=request.answer,
            is_first_answer=is_first_answer,  # 답변 횟수 정보 전달
            context={
                "category": question.category,
                "difficulty": question.difficulty,
                "expected_points": question.expected_points or []
            }
        )
        
        print(f"[FEEDBACK_RESULT] 피드백 생성 결과:", feedback_result)
        if feedback_result and feedback_result.get("success"):
            feedback_data = feedback_result.get("data", {})
            print(f"[FEEDBACK_DATA] 피드백 데이터:")
            print(f"  - overall_score: {feedback_data.get('overall_score', 'N/A')}")
            print(f"  - feedback: {feedback_data.get('feedback', 'N/A')[:50]}...")
            print(f"  - suggestions count: {len(feedback_data.get('suggestions', []))}")
        
        # 답변 및 피드백 저장 (문자열 ID는 메모리만 사용, UUID ID는 데이터베이스에 저장)
        answer_data = {
            "answer": request.answer,
            "time_taken": request.time_taken,
            "feedback": feedback_result if feedback_result.get("success") else None,
            "question_id_type": "uuid" if question_id_is_uuid else "string",
            "question_identifier": question_identifier
        }
        
        if question_id_is_uuid:
            # UUID 질문은 데이터베이스에 저장
            saved_answer = repo.save_answer(session_uuid, question_uuid, answer_data)
            saved_answer_id = str(saved_answer.id)
        else:
            # 문자열 질문은 메모리만 사용 (임시 처리)
            saved_answer_id = f"temp_answer_{question_string_id}_{session_uuid}"
            print(f"[DEBUG] 문자열 질문 답변은 메모리 처리: {saved_answer_id}")
        
        # 다음 질문 확인 (현재는 간단히 처리)
        # 문자열 질문의 경우 캐시의 전체 질문 수로 비교
        if question_id_is_uuid:
            total_questions = db.query(InterviewQuestion).filter(
                InterviewQuestion.analysis_id == session.analysis_id
            ).count()
            
            answered_questions = db.query(InterviewAnswer).filter(
                InterviewAnswer.session_id == session_uuid
            ).count()
        else:
            # 캐시에서 전체 질문 수 가져오기
            normalized_analysis_id = str(session.analysis_id).replace('-', '')
            if normalized_analysis_id in question_cache:
                total_questions = len(question_cache[normalized_analysis_id].parsed_questions)
            else:
                total_questions = 1  # 기본값
            
            # 임시로 답변 수는 1로 처리 (실제 구현 시 세션별 답변 추적 필요)
            answered_questions = 1
            
        is_completed = answered_questions >= total_questions
        print(f"[DEBUG] 질문 진행상황: {answered_questions}/{total_questions}, 완료: {is_completed}")
        
        if is_completed:
            repo.update_session_status(session_uuid, "completed")
        
        return {
            "success": True,
            "message": "답변이 성공적으로 제출되었습니다.",
            "data": {
                "answer_id": saved_answer_id,
                "feedback": feedback_result.get("data") if feedback_result and feedback_result.get("success") else None,
                "is_completed": is_completed,
                "next_question_index": answered_questions if not is_completed else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 처리에 실패했습니다: {str(e)}")


@router.post("/conversation")
async def handle_conversation(
    request: ConversationRequest, 
    db: Session = Depends(get_db),
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key")
):
    """대화 처리"""
    print(f"[CONVERSATION] ========== 대화 처리 요청 ===========")
    print(f"[CONVERSATION] interview_id: '{request.interview_id}'")
    print(f"[CONVERSATION] question_id: '{request.question_id}'")
    print(f"[CONVERSATION] conversation_question: '{request.conversation_question[:50]}...'")
    print(f"[CONVERSATION] 받은 헤더:")
    print(f"[CONVERSATION]   - GitHub Token: {'있음' if github_token else '없음'}")
    print(f"[CONVERSATION]   - Google API Key: {'있음' if google_api_key else '없음'}")
    if github_token:
        print(f"[CONVERSATION]   - GitHub Token 값: {github_token[:20]}...")
    if google_api_key:
        print(f"[CONVERSATION]   - Google API Key 값: {google_api_key[:20]}...")
    
    try:
        normalized_interview_id = normalize_uuid_string(request.interview_id)
        normalized_question_id = normalize_uuid_string(request.question_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        question_uuid = uuid.UUID(normalized_question_id)
        print(f"[CONVERSATION] UUID 정규화: '{request.interview_id}' → '{normalized_interview_id}', '{request.question_id}' → '{normalized_question_id}'")
    except ValueError as e:
        print(f"[ERROR] 대화 처리 UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail="올바르지 않은 ID 형식입니다.")
    
    repo = InterviewRepository(db)
    session = repo.get_session(session_uuid)
    
    if not session:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    try:
        # 사용자 질문 저장
        user_conversation = repo.save_conversation(session_uuid, {
            "question_id": question_uuid,
            "speaker": "user",
            "content": request.conversation_question,
            "metadata": {"original_answer": request.original_answer}
        })
        
        # AI 응답 생성 (우선순위 적용된 API 키 전달)
        # GitHub Token 우선순위 적용
        effective_github_token = None
        if settings.github_token and settings.github_token != "your_github_token_here":
            effective_github_token = settings.github_token
        elif github_token:
            effective_github_token = github_token
            
        # Google API Key 우선순위 적용  
        effective_google_api_key = None
        if settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
            effective_google_api_key = settings.google_api_key
        elif google_api_key:
            effective_google_api_key = google_api_key
            
        interview_agent = MockInterviewAgent(github_token=effective_github_token, google_api_key=effective_google_api_key)
        ai_response = await interview_agent.handle_follow_up_question(
            original_question="",  # 필요시 DB에서 조회
            original_answer=request.original_answer,
            follow_up_question=request.conversation_question
        )
        
        # AI 응답 저장
        ai_conversation = repo.save_conversation(session_uuid, {
            "question_id": question_uuid,
            "speaker": "ai",
            "content": ai_response.get("response", "죄송합니다. 응답을 생성할 수 없습니다."),
            "metadata": {"response_data": ai_response}
        })
        
        return {
            "success": True,
            "message": "대화가 성공적으로 처리되었습니다.",
            "data": {
                "response": ai_response.get("response", "응답을 생성할 수 없습니다."),
                "conversation_id": str(ai_conversation.id)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 처리에 실패했습니다: {str(e)}")


@router.get("/sessions")
async def list_sessions(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """세션 목록 조회"""
    sessions = db.query(InterviewSession).order_by(
        InterviewSession.started_at.desc()
    ).offset(offset).limit(limit).all()
    
    total_count = db.query(InterviewSession).count()
    
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "interview_id": str(session.id),
            "analysis_id": str(session.analysis_id),
            "interview_type": session.interview_type,
            "difficulty": session.difficulty,
            "status": session.status,
            "overall_score": float(session.overall_score) if session.overall_score else None,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None
        })
    
    return {
        "success": True,
        "data": {
            "sessions": sessions_data,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        }
    }


@router.get("/sessions/latest")
async def get_latest_session(db: Session = Depends(get_db)):
    """가장 최근 세션 조회"""
    repo = InterviewRepository(db)
    session = repo.get_latest_session()
    
    if not session:
        raise HTTPException(status_code=404, detail="세션이 없습니다.")
    
    return {
        "success": True,
        "data": {
            "interview_id": str(session.id),
            "analysis_id": str(session.analysis_id),
            "status": session.status,
            "started_at": session.started_at.isoformat()
        }
    }


@router.post("/session/{interview_id}/complete")
async def complete_interview(interview_id: str, db: Session = Depends(get_db)):
    """면접 완료 처리"""
    try:
        normalized_interview_id = normalize_uuid_string(interview_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        print(f"[DEBUG] 면접 질문 조회 - UUID 정규화: '{interview_id}' → '{normalized_interview_id}'")
    except ValueError as e:
        print(f"[ERROR] 면접 ID UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 면접 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    success = repo.update_session_status(session_uuid, "completed")
    
    if not success:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    return {
        "success": True,
        "message": "면접이 완료되었습니다.",
        "data": {"status": "completed"}
    }


@router.post("/{interview_id}/finish")
async def finish_interview(interview_id: str, db: Session = Depends(get_db)):
    """면접 종료 처리 (프론트엔드 호환성을 위한 별칭)"""
    # complete_interview 함수와 동일한 로직
    try:
        normalized_interview_id = normalize_uuid_string(interview_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        print(f"[DEBUG] 면접 질문 조회 - UUID 정규화: '{interview_id}' → '{normalized_interview_id}'")
    except ValueError as e:
        print(f"[ERROR] 면접 ID UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 면접 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    success = repo.update_session_status(session_uuid, "completed")
    
    if not success:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    return {
        "success": True,
        "message": "면접이 종료되었습니다.",
        "data": {"status": "completed"}
    }
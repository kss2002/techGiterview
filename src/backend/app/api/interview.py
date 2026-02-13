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
from app.models.repository import RepositoryAnalysis
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

        # 분석 ID 검증 (DB 우선)
        analysis = None
        analysis_uuid = None
        try:
            analysis_uuid = uuid.UUID(request.analysis_id)
            analysis = db.query(RepositoryAnalysis).filter(
                RepositoryAnalysis.id == analysis_uuid
            ).first()
        except ValueError:
            pass

        if not analysis:
            try:
                cleaned_id = request.analysis_id.replace('-', '')
                analysis_uuid = uuid.UUID(
                    f"{cleaned_id[:8]}-{cleaned_id[8:12]}-{cleaned_id[12:16]}-{cleaned_id[16:20]}-{cleaned_id[20:]}"
                )
                analysis = db.query(RepositoryAnalysis).filter(
                    RepositoryAnalysis.id == analysis_uuid
                ).first()
            except (ValueError, IndexError):
                pass

        if not analysis or not analysis_uuid:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ANALYSIS_NOT_FOUND",
                    "message": "해당 분석 ID에 대한 분석 데이터가 존재하지 않습니다.",
                    "analysis_id": request.analysis_id,
                    "suggestion": "먼저 저장소 분석을 완료해주세요."
                }
            )

        # 질문 데이터 로딩: DB 우선, 캐시 폴백
        from app.api.questions import question_cache, QuestionResponse
        cached_questions = []

        db_questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.analysis_id == analysis_uuid
        ).order_by(InterviewQuestion.created_at.asc()).all()

        if db_questions:
            requested_ids = set(request.question_ids)
            selected_questions = [q for q in db_questions if str(q.id) in requested_ids]

            if not selected_questions:
                selected_questions = db_questions[:len(request.question_ids)]
                request.question_ids = [str(q.id) for q in selected_questions]
                print(f"[INTERVIEW_START] 요청 질문 ID가 DB와 불일치하여 최신 질문으로 대체: {request.question_ids}")

            cached_questions = [
                QuestionResponse(
                    id=str(q.id),
                    type=q.category,
                    question=q.question_text,
                    difficulty=q.difficulty,
                    expected_answer_points=(q.context or {}).get("expected_answer_points", [])
                )
                for q in selected_questions
            ]
            print(f"[INTERVIEW_START] DB에서 질문 로딩 완료: {len(cached_questions)}개")
        else:
            normalized_analysis_id = request.analysis_id.replace('-', '')
            if normalized_analysis_id not in question_cache:
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
            missing_question_ids = set(request.question_ids) - available_question_ids
            if missing_question_ids:
                fallback_questions = cached_questions[:len(request.question_ids)]
                request.question_ids = [q.id for q in fallback_questions]
                print(f"[INTERVIEW_START] 캐시 질문 ID 불일치로 대체: {request.question_ids}")

            print(f"[INTERVIEW_START] 캐시에서 질문 로딩 완료: {len(cached_questions)}개")
        
        # InterviewRepository를 사용하여 세션 생성
        repo = InterviewRepository(db)
        print(f"[DEBUG] InterviewRepository 생성 완료, 세션 생성 시작...")
        session = repo.create_session({
            'analysis_id': analysis_uuid,
            'interview_type': request.interview_type,
            'difficulty_level': request.difficulty_level
        })
        print(f"[DEBUG] 면접 세션 생성 완료: {session.id}")
        
        # 선택된 질문들을 데이터베이스에 저장 (필요시)
        question_id_mapping = {}  # 원본 ID -> UUID 매핑
        questions_to_add = []
        
        print(f"[DEBUG] 질문 저장 시작: {len(request.question_ids)}개 질문 처리")
        
        for question_data in cached_questions:
            if question_data.id in request.question_ids:
                print(f"[DEBUG] 질문 처리: {question_data.id}")
                
                # 질문 ID가 UUID 형식인지 확인
                try:
                    question_uuid = uuid.UUID(question_data.id)
                    # UUID 형식이면 기존 질문 확인
                    existing_question = db.query(InterviewQuestion).filter(
                        InterviewQuestion.id == question_uuid
                    ).first()
                    print(f"[DEBUG] UUID 질문 {question_uuid}: 기존 존재={existing_question is not None}")
                except ValueError:
                    # UUID 형식이 아니면 새 UUID 생성
                    question_uuid = uuid.uuid4()
                    existing_question = None
                    print(f"[DEBUG] 문자열 질문 {question_data.id} -> 새 UUID {question_uuid}")
                
                question_id_mapping[question_data.id] = question_uuid
                
                if not existing_question:
                    # 새 질문 저장 준비
                    db_question = InterviewQuestion(
                        id=question_uuid,
                        analysis_id=analysis_uuid,
                        category=question_data.type,  # QuestionResponse uses 'type' not 'category'
                        difficulty=question_data.difficulty,
                        question_text=question_data.question,
                        context={"original_data": question_data.dict(), "original_id": question_data.id}
                    )
                    questions_to_add.append(db_question)
                    print(f"[DEBUG] 새 질문 저장 예정: {question_uuid}")
        
        # 질문들을 한번에 추가
        if questions_to_add:
            print(f"[DEBUG] {len(questions_to_add)}개 질문을 데이터베이스에 저장 중...")
            for q in questions_to_add:
                db.add(q)
        
        print(f"[DEBUG] 데이터베이스 commit 시작...")
        try:
            db.commit()
            print(f"[DEBUG] 데이터베이스 commit 완료")
        except Exception as commit_e:
            print(f"[ERROR] 데이터베이스 commit 실패: {commit_e}")
            db.rollback()
            raise
        
        print(f"[DEBUG] 응답 생성 시작...")
        response_data = {
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
        
        print(f"[DEBUG] 면접 시작 완료 - session_id: {session.id}")
        return response_data
        
    except Exception as e:
        print(f"[ERROR] 면접 시작 API 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 데이터베이스 롤백 시도
        try:
            db.rollback()
            print(f"[ERROR] 데이터베이스 롤백 완료")
        except Exception as rollback_e:
            print(f"[ERROR] 롤백 실패: {rollback_e}")
        
        raise HTTPException(status_code=500, detail=f"면접 시작에 실패했습니다: {type(e).__name__}: {str(e)}")


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
    
    # 해당 분석의 모든 질문 조회 (중복 제거 및 정렬)
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.analysis_id == session.analysis_id
    ).order_by(InterviewQuestion.created_at).distinct().all()
    
    print(f"[DEBUG] 질문 조회 완료 - analysis_id: {session.analysis_id}, 질문 수: {len(questions)}")
    
    # 답변된 질문 수 확인
    answered_count = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_uuid
    ).count()
    
    # 질문 데이터 변환 및 추가 중복 제거
    questions_data = []
    seen_questions = set()  # 중복 질문 텍스트 추적
    
    for question in questions:
        # 질문 텍스트 기반 중복 체크
        question_hash = hash(question.question_text.strip())
        if question_hash in seen_questions:
            print(f"[DEBUG] 중복 질문 제거: {question.id}")
            continue
        
        seen_questions.add(question_hash)
        questions_data.append({
            "id": str(question.id),
            "question": question.question_text,
            "category": question.category,
            "difficulty": question.difficulty,
            "context": question.context.get("original_data") if question.context else None
        })
    
    print(f"[DEBUG] 중복 제거 후 질문 수: {len(questions_data)}")
    
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
        normalized_interview_id = normalize_uuid_string(request.interview_id)
        normalized_question_id = normalize_uuid_string(request.question_id)
        session_uuid = uuid.UUID(normalized_interview_id)
        question_uuid = uuid.UUID(normalized_question_id)
        print(f"[DEBUG] 정규화된 ID:")
        print(f"  - interview_id: '{normalized_interview_id}' → UUID: {session_uuid}")
        print(f"  - question_id: '{normalized_question_id}' → UUID: {question_uuid}")
    except ValueError as e:
        print(f"[ERROR] UUID 변환 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=f"올바르지 않은 ID 형식입니다: {str(e)}")
    
    repo = InterviewRepository(db)
    session = repo.get_session(session_uuid)
    
    if not session:
        raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
    
    if session.status != "active":
        raise HTTPException(status_code=400, detail="활성화된 면접 세션에만 답변할 수 있습니다.")
    
    try:
        existing_answer = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session_uuid,
            InterviewAnswer.question_id == question_uuid
        ).first()
        question = db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_uuid
        ).first()
        question_identifier = str(question_uuid)
        print(f"[DEBUG] UUID 질문 조회: {question_uuid}")

        is_first_answer = existing_answer is None
        print(f"[DEBUG] 질문 {question_identifier}: 첫 번째 답변? {is_first_answer}")
        print(f"[DEBUG] 기존 답변 존재: {existing_answer is not None}")
        
        if not question:
            raise HTTPException(status_code=404, detail="데이터베이스에서 질문을 찾을 수 없습니다.")
        
        # Mock Interview Agent를 사용하여 피드백 생성 (통합된 API 키 처리)
        from app.core.api_utils import get_effective_api_keys
        
        # API 키 추출 및 우선순위 적용
        api_keys = get_effective_api_keys(
            github_token=github_token,
            google_api_key=google_api_key
        )
        
        interview_agent = MockInterviewAgent(api_keys=api_keys)
        
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
        
        # 안전한 피드백 처리
        feedback_data = None
        if feedback_result and isinstance(feedback_result, dict) and feedback_result.get("success"):
            feedback_data = feedback_result.get("data", {})
            print(f"[FEEDBACK_DATA] 피드백 데이터:")
            print(f"  - overall_score: {feedback_data.get('overall_score', 'N/A')}")
            print(f"  - feedback: {feedback_data.get('feedback', 'N/A')[:50]}...")
            print(f"  - suggestions count: {len(feedback_data.get('suggestions', []))}")
        else:
            print(f"[FEEDBACK_RESULT] 피드백 생성 실패 또는 없음 - 기본 응답 사용")
        
        # 답변 및 피드백 저장
        answer_data = {
            "answer": request.answer,
            "time_taken": request.time_taken,
            "feedback": feedback_data if feedback_data else None,  # 안전한 처리
            "question_id_type": "uuid",
            "question_identifier": question_identifier
        }
        
        saved_answer = repo.save_answer(session_uuid, question_uuid, answer_data)
        saved_answer_id = str(saved_answer.id)

        total_questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.analysis_id == session.analysis_id
        ).count()
        answered_questions = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session_uuid
        ).count()
            
        is_completed = answered_questions >= total_questions
        print(f"[DEBUG] 질문 진행상황: {answered_questions}/{total_questions}, 완료: {is_completed}")
        
        if is_completed:
            repo.update_session_status(session_uuid, "completed")
        
        return {
            "success": True,
            "message": "답변이 성공적으로 제출되었습니다.",
            "data": {
                "answer_id": saved_answer_id,
                "feedback": feedback_data,  # 이미 안전하게 처리된 데이터 사용
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

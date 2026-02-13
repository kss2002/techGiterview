"""
Report System API

면접 리포트 생성 및 조회를 위한 REST API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from app.agents.mock_interview_agent import MockInterviewAgent
from app.agents.repository_analyzer import RepositoryAnalyzer
from app.agents.question_generator import QuestionGenerator
from app.services.vector_db import VectorDBService
from app.core.database import get_db
from app.models.interview import (
    InterviewSession, InterviewAnswer, InterviewQuestion, 
    InterviewReport, ProjectTechnicalAnalysis, InterviewImprovementPlan
)
from sqlalchemy.orm import Session
from sqlalchemy import func

router = APIRouter()

# 서비스 인스턴스
interview_agent = MockInterviewAgent()
repo_analyzer = RepositoryAnalyzer()
question_generator = QuestionGenerator()
# vector_db = VectorDBService()  # 지연 초기화로 변경하여 서버 시작 시 블로킹 방지

# 지연 초기화 함수
def get_vector_db():
    """VectorDB 인스턴스를 지연 초기화로 반환"""
    if not hasattr(get_vector_db, '_instance'):
        try:
            get_vector_db._instance = VectorDBService()
        except Exception as e:
            print(f"VectorDB 초기화 실패: {e}")
            get_vector_db._instance = None
    return get_vector_db._instance


@router.post("/repository/analyze")
async def analyze_repository(
    repo_url: str,
    store_results: bool = True
):
    """
    GitHub 저장소 분석
    
    Args:
        repo_url: GitHub 저장소 URL
        store_results: 분석 결과를 벡터 DB에 저장할지 여부
    
    Returns:
        저장소 분석 결과
    """
    try:
        # 저장소 분석 수행
        analysis_result = await repo_analyzer.analyze_repository(repo_url)
        
        if not analysis_result.get("success", False):
            raise HTTPException(
                status_code=400, 
                detail=f"저장소 분석 실패: {analysis_result.get('error', 'Unknown error')}"
            )
        
        # 벡터 DB에 결과 저장 (옵션)
        if store_results:
            try:
                # 분석 결과 저장
                vector_db = get_vector_db()
                if vector_db:
                    analysis_id = await vector_db.store_analysis_result(repo_url, analysis_result)
                analysis_result["analysis_id"] = analysis_id
                
                # 코드 스니펫 저장 (중요 파일들)
                important_files = analysis_result.get("important_files", [])
                if important_files:
                    # 파일 내용을 가져와서 저장 (실제로는 GitHubClient에서)
                    if vector_db:
                        stored_snippets = await vector_db.store_code_snippets(repo_url, important_files)
                    analysis_result["stored_snippets_count"] = len(stored_snippets)
                
            except Exception as e:
                # 벡터 DB 저장 실패는 분석 자체의 실패로 간주하지 않음
                analysis_result["storage_warning"] = f"벡터 DB 저장 실패: {str(e)}"
        
        return {
            "success": True,
            "data": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/questions/generate")
async def generate_interview_questions(
    repo_url: str,
    difficulty_level: str = "medium",
    question_count: int = 5,
    question_types: Optional[List[str]] = None
):
    """
    면접 질문 생성
    
    Args:
        repo_url: GitHub 저장소 URL
        difficulty_level: 난이도 (easy, medium, hard)
        question_count: 생성할 질문 개수
        question_types: 질문 타입 리스트
    
    Returns:
        생성된 면접 질문들
    """
    try:
        # 기본 질문 타입 설정
        if question_types is None:
            question_types = ["code_analysis", "tech_stack", "architecture", "problem_solving"]
        
        # 질문 생성
        questions_result = await question_generator.generate_questions(
            repo_url=repo_url,
            difficulty_level=difficulty_level,
            question_count=question_count,
            question_types=question_types
        )
        
        if not questions_result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=f"질문 생성 실패: {questions_result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "data": questions_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interview/{interview_id}/report")
async def get_interview_report(interview_id: str):
    """
    면접 리포트 조회
    
    Args:
        interview_id: 면접 ID
    
    Returns:
        상세 면접 리포트
    """
    try:
        # 면접 리포트 생성
        report_result = await interview_agent.get_interview_report(interview_id)
        
        if not report_result.get("success", False):
            raise HTTPException(
                status_code=404,
                detail=f"면접 리포트를 찾을 수 없습니다: {report_result.get('error', 'Unknown error')}"
            )
        
        report = report_result["report"]
        
        # 리포트 추가 처리
        enhanced_report = await _enhance_interview_report(report)
        
        return {
            "success": True,
            "data": enhanced_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interview/{interview_id}/summary")
async def get_interview_summary(interview_id: str):
    """
    면접 요약 정보 조회
    
    Args:
        interview_id: 면접 ID
    
    Returns:
        면접 요약 정보
    """
    try:
        # 면접 상태 조회
        status_result = await interview_agent.get_interview_status(interview_id)
        
        if not status_result.get("success", False):
            raise HTTPException(
                status_code=404,
                detail=f"면접 정보를 찾을 수 없습니다: {status_result.get('error', 'Unknown error')}"
            )
        
        # 요약 정보 생성
        summary = {
            "interview_id": interview_id,
            "status": status_result["status"],
            "progress": status_result["progress"],
            "elapsed_time": status_result["elapsed_time"],
            "total_score": status_result["total_score"],
            "difficulty_level": status_result.get("difficulty_level", "unknown")
        }
        
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/overview")
async def get_analytics_overview(
    days: int = Query(30, description="분석 기간 (일)"),
    user_id: Optional[str] = Query(None, description="특정 사용자 필터"),
    db: Session = Depends(get_db)
):
    """
    분석 대시보드 개요
    
    Args:
        days: 분석 기간
        user_id: 특정 사용자 ID (옵션)
    
    Returns:
        분석 대시보드 데이터
    """
    try:
        start_boundary = datetime.now() - timedelta(days=days)
        base_query = db.query(InterviewSession).filter(InterviewSession.started_at >= start_boundary)

        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                base_query = base_query.filter(InterviewSession.user_id == user_uuid)
            except ValueError:
                return {
                    "success": True,
                    "data": {
                        "overview": {
                            "total_interviews": 0,
                            "completed_interviews": 0,
                            "in_progress_interviews": 0,
                            "completion_rate": 0,
                            "average_score": 0
                        },
                        "difficulty_distribution": {},
                        "period_days": days,
                        "user_filter": user_id,
                        "last_updated": datetime.now().isoformat()
                    },
                    "timestamp": datetime.now().isoformat()
                }

        sessions = base_query.all()
        total_interviews = len(sessions)
        completed_interviews = sum(1 for s in sessions if s.status == "completed")
        in_progress_interviews = sum(1 for s in sessions if s.status == "active")

        completed_scores = [
            float(s.overall_score) for s in sessions
            if s.status == "completed" and s.overall_score is not None
        ]
        avg_score = sum(completed_scores) / len(completed_scores) if completed_scores else 0

        difficulty_distribution = {}
        for session in sessions:
            difficulty = session.difficulty or "unknown"
            difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1

        analytics_data = {
            "overview": {
                "total_interviews": total_interviews,
                "completed_interviews": completed_interviews,
                "in_progress_interviews": in_progress_interviews,
                "completion_rate": (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0,
                "average_score": round(avg_score, 2)
            },
            "difficulty_distribution": difficulty_distribution,
            "period_days": days,
            "user_filter": user_id,
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": analytics_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance")
async def get_performance_analytics(
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    repo_url: Optional[str] = Query(None, description="저장소 URL"),
    db: Session = Depends(get_db)
):
    """
    성능 분석 데이터
    
    Args:
        user_id: 특정 사용자 ID
        repo_url: 특정 저장소 URL
    
    Returns:
        성능 분석 데이터
    """
    try:
        from app.models.repository import RepositoryAnalysis

        session_query = db.query(InterviewSession).filter(InterviewSession.status == "completed")

        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                session_query = session_query.filter(InterviewSession.user_id == user_uuid)
            except ValueError:
                return {
                    "success": True,
                    "data": {"message": "분석할 완료된 면접이 없습니다.", "sessions_count": 0},
                    "timestamp": datetime.now().isoformat()
                }

        if repo_url:
            session_query = session_query.join(
                RepositoryAnalysis, InterviewSession.analysis_id == RepositoryAnalysis.id
            ).filter(RepositoryAnalysis.repository_url == repo_url)

        completed_sessions = session_query.all()

        if not completed_sessions:
            return {
                "success": True,
                "data": {
                    "message": "분석할 완료된 면접이 없습니다.",
                    "sessions_count": 0
                },
                "timestamp": datetime.now().isoformat()
            }

        session_ids = [s.id for s in completed_sessions]
        answers = db.query(InterviewAnswer, InterviewQuestion).outerjoin(
            InterviewQuestion, InterviewAnswer.question_id == InterviewQuestion.id
        ).filter(
            InterviewAnswer.session_id.in_(session_ids)
        ).all()

        scored_answers = [a for a, _ in answers if a.feedback_score is not None]
        avg_overall_score = (
            sum(float(a.feedback_score) for a in scored_answers) / len(scored_answers)
            if scored_answers else 0
        )

        criteria_keys = ["technical_accuracy", "code_quality", "problem_solving", "communication"]
        criteria_scores_map = {k: [] for k in criteria_keys}
        question_type_performance: Dict[str, List[float]] = {}

        for answer, question in answers:
            if answer.feedback_score is not None and question and question.category:
                question_type_performance.setdefault(question.category, []).append(float(answer.feedback_score))

            if answer.feedback_details and isinstance(answer.feedback_details, dict):
                criteria_scores = answer.feedback_details.get("criteria_scores", {})
                if isinstance(criteria_scores, dict):
                    for key in criteria_keys:
                        value = criteria_scores.get(key)
                        if isinstance(value, (int, float)):
                            criteria_scores_map[key].append(float(value))

        criteria_averages = {
            key: (sum(values) / len(values) if values else 0)
            for key, values in criteria_scores_map.items()
        }

        avg_duration_minutes = 0
        duration_values = []
        for session in completed_sessions:
            if session.started_at and session.ended_at:
                duration_values.append((session.ended_at - session.started_at).total_seconds() / 60.0)
        if duration_values:
            avg_duration_minutes = sum(duration_values) / len(duration_values)

        question_type_averages = {
            qtype: (sum(scores) / len(scores) if scores else 0)
            for qtype, scores in question_type_performance.items()
        }

        performance_data = {
            "overall_statistics": {
                "sessions_analyzed": len(completed_sessions),
                "total_questions_answered": len(answers),
                "average_overall_score": round(avg_overall_score, 2),
                "average_duration_minutes": round(avg_duration_minutes, 1)
            },
            "criteria_performance": {
                criteria: round(score, 2)
                for criteria, score in criteria_averages.items()
            },
            "question_type_performance": {
                qtype: round(avg_score, 2)
                for qtype, avg_score in question_type_averages.items()
            },
            "improvement_areas": _identify_improvement_areas(criteria_averages),
            "strengths": _identify_strengths(criteria_averages)
        }
        
        return {
            "success": True,
            "data": performance_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_reports_list(
    status_filter: Optional[str] = Query(None, description="상태 필터 (completed, in_progress)"),
    db: Session = Depends(get_db)
):
    """
    면접 리포트 목록 조회 (데이터베이스 기반)
    
    Args:
        status_filter: 상태별 필터링 옵션
        db: 데이터베이스 세션
    
    Returns:
        면접 리포트 목록
    """
    try:
        print(f"[REPORTS_API] 리포트 목록 요청 - 필터: {status_filter}")
        
        # 데이터베이스에서 면접 세션 조회
        from app.models.interview import InterviewSession, InterviewAnswer
        from app.models.repository import RepositoryAnalysis
        from sqlalchemy import desc, and_, func
        
        # 기본 쿼리 구성
        query = db.query(InterviewSession)\
            .join(RepositoryAnalysis, InterviewSession.analysis_id == RepositoryAnalysis.id)
        
        # 상태 필터링
        if status_filter:
            if status_filter == "completed":
                query = query.filter(InterviewSession.status == "completed")
            elif status_filter == "in_progress":
                query = query.filter(InterviewSession.status == "active")
        
        # 시작시간 기준 내림차순 정렬
        sessions = query.order_by(desc(InterviewSession.started_at)).all()
        
        print(f"[REPORTS_API] 데이터베이스에서 {len(sessions)}개 세션 조회됨")
        
        reports = []
        
        for session in sessions:
            # 연관된 저장소 분석 정보
            analysis = session.analysis
            if not analysis:
                continue
            
            # URL에서 저장소 이름 추출
            url_parts = analysis.repository_url.replace("https://github.com/", "").split("/")
            repo_name = url_parts[1] if len(url_parts) > 1 else analysis.repository_name or "Unknown"
            
            # 답변 개수 조회
            answers_count = db.query(func.count(InterviewAnswer.id))\
                .filter(InterviewAnswer.session_id == session.id)\
                .scalar()
            
            # 질문 개수 조회 (분석에서 생성된 질문 수)
            questions_count = db.query(func.count(InterviewQuestion.id))\
                .filter(InterviewQuestion.analysis_id == session.analysis_id)\
                .scalar()
            
            # 면접 지속 시간 계산 (최대 10시간 = 600분으로 제한)
            duration_minutes = 0
            if session.started_at and session.ended_at:
                duration_seconds = (session.ended_at - session.started_at).total_seconds()
                duration_minutes = min(int(duration_seconds / 60), 600)  # 최대 600분(10시간)
            elif session.started_at and session.status == "active":
                # 진행 중인 면접의 경우 현재까지의 시간
                duration_seconds = (datetime.now() - session.started_at).total_seconds()
                duration_minutes = min(int(duration_seconds / 60), 600)  # 최대 600분(10시간)
            
            # 카테고리별 점수 (feedback JSON에서 추출)
            category_scores = {}
            if session.feedback and isinstance(session.feedback, dict):
                category_scores = session.feedback.get("category_scores", {})
            
            # 상태 매핑 (DB의 status -> 프론트엔드 예상 형식)
            status_map = {
                "active": "in_progress",
                "completed": "completed",
                "abandoned": "completed"
            }
            frontend_status = status_map.get(session.status, "in_progress")
            
            report = {
                "id": str(session.id),
                "repo_url": analysis.repository_url,
                "repo_name": repo_name,
                "completed_at": session.ended_at.isoformat() if session.ended_at else session.started_at.isoformat(),
                "total_questions": questions_count,
                "answered_questions": answers_count,
                "overall_score": round(float(session.overall_score), 1) if session.overall_score else 0.0,
                "category_scores": category_scores,
                "duration_minutes": duration_minutes,
                "status": frontend_status
            }
            
            reports.append(report)
        
        print(f"[REPORTS_API] {len(reports)}개 리포트 반환")
        
        return {
            "success": True,
            "data": {
                "reports": reports,
                "total_count": len(reports),
                "filters_applied": {"status": status_filter}
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[REPORTS_API] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 오류 시 빈 결과 반환 (사용자 경험 개선)
        return {
            "success": True,
            "data": {
                "reports": [],
                "total_count": 0,
                "filters_applied": {"status": status_filter},
                "error": f"데이터 조회 중 오류가 발생했습니다: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }


@router.get("/{interview_id}/detailed")
async def get_detailed_report(interview_id: str, db: Session = Depends(get_db)):
    """
    상세 면접 리포트 조회 (데이터베이스 기반)
    
    Args:
        interview_id: 면접 ID
        db: 데이터베이스 세션
    
    Returns:
        상세 면접 리포트
    """
    try:
        print(f"[DETAILED_REPORT] 상세 리포트 요청: {interview_id}")
        
        # UUID 정규화 (SQLAlchemy UUID 타입용)
        import uuid
        try:
            # 하이픈이 없으면 추가, 있으면 그대로 사용
            if '-' not in interview_id and len(interview_id) == 32:
                # 32자 문자열을 UUID 형식으로 변환
                formatted_id = f"{interview_id[:8]}-{interview_id[8:12]}-{interview_id[12:16]}-{interview_id[16:20]}-{interview_id[20:]}"
                normalized_uuid = uuid.UUID(formatted_id)
            else:
                normalized_uuid = uuid.UUID(interview_id)
        except ValueError:
            print(f"[DETAILED_REPORT] UUID 변환 실패: {interview_id}")
            raise HTTPException(status_code=400, detail="잘못된 UUID 형식입니다.")
            
        print(f"[DETAILED_REPORT] UUID 정규화: {interview_id} -> {normalized_uuid}")
        
        # 데이터베이스에서 세션 조회
        from app.models.interview import InterviewSession, InterviewAnswer, InterviewQuestion
        from app.models.repository import RepositoryAnalysis
        from sqlalchemy.orm import joinedload
        
        try:
            # 관계 로딩 없이 먼저 세션만 조회
            session = db.query(InterviewSession)\
                .filter(InterviewSession.id == normalized_uuid)\
                .first()
                
            if not session:
                print(f"[DETAILED_REPORT] 세션을 찾을 수 없음: {normalized_uuid}")
                raise HTTPException(status_code=404, detail="면접 세션을 찾을 수 없습니다.")
                
            print(f"[DETAILED_REPORT] 세션 조회 성공: {session.id}, analysis_id: {session.analysis_id}")
            
        except Exception as db_error:
            print(f"[DETAILED_REPORT] DB 쿼리 오류: {db_error}")
            raise HTTPException(status_code=500, detail=f"데이터베이스 쿼리 오류: {str(db_error)}")
        
        # 저장소 분석 정보 별도 조회
        try:
            analysis = db.query(RepositoryAnalysis)\
                .filter(RepositoryAnalysis.id == session.analysis_id)\
                .first()
                
            if not analysis:
                print(f"[DETAILED_REPORT] 분석 정보가 없음: analysis_id={session.analysis_id}")
                raise HTTPException(status_code=404, detail="저장소 분석 정보를 찾을 수 없습니다.")
                
            print(f"[DETAILED_REPORT] 분석 정보 조회 성공: {analysis.id}")
            
        except Exception as analysis_error:
            print(f"[DETAILED_REPORT] 분석 정보 조회 오류: {analysis_error}")
            raise HTTPException(status_code=500, detail=f"저장소 분석 정보 조회 오류: {str(analysis_error)}")
        
        # 저장소 정보 구성
        url_parts = analysis.repository_url.replace("https://github.com/", "").split("/")
        repo_info = {
            "name": url_parts[1] if len(url_parts) > 1 else analysis.repository_name or "Unknown",
            "owner": url_parts[0] if len(url_parts) > 0 else "Unknown",
            "description": "GitHub repository analysis",  # analysis_summary 필드가 없으므로 기본값 사용
            "language": analysis.primary_language or "Multiple"
        }
        
        # 면접 질문들 조회
        try:
            questions = db.query(InterviewQuestion)\
                .filter(InterviewQuestion.analysis_id == session.analysis_id)\
                .order_by(InterviewQuestion.created_at)\
                .all()
            print(f"[DETAILED_REPORT] 질문 조회 성공: {len(questions)}개")
        except Exception as q_error:
            print(f"[DETAILED_REPORT] 질문 조회 오류: {q_error}")
            questions = []
        
        # 답변들 조회
        try:
            answers = db.query(InterviewAnswer)\
                .filter(InterviewAnswer.session_id == session.id)\
                .order_by(InterviewAnswer.submitted_at)\
                .all()
            print(f"[DETAILED_REPORT] 답변 조회 성공: {len(answers)}개")
        except Exception as a_error:
            print(f"[DETAILED_REPORT] 답변 조회 오류: {a_error}")
            answers = []
        
        print(f"[DETAILED_REPORT] 총 질문 {len(questions)}개, 답변 {len(answers)}개 조회")
        
        # 질문별 분석 구성
        question_analyses = []
        try:
            for i, question in enumerate(questions):
                # 해당 질문에 대한 답변 찾기
                answer = next((a for a in answers if str(a.question_id) == str(question.id)), None)
                
                # 안전한 데이터 접근
                try:
                    analysis_item = {
                        "question": getattr(question, 'question_text', '질문 정보 없음'),
                        "category": getattr(question, 'category', 'general'),
                        "difficulty": getattr(question, 'difficulty', 'medium'),
                        "answer": getattr(answer, 'user_answer', '답변 없음') if answer else "답변 없음",
                        "score": float(answer.feedback_score) if answer and hasattr(answer, 'feedback_score') and answer.feedback_score else 0.0,
                        "feedback": getattr(answer, 'feedback_message', '피드백 없음') if answer else "피드백 없음",
                        "improvement_suggestions": []
                    }
                    
                    # improvement_suggestions 안전한 추출
                    if answer and hasattr(answer, 'feedback_details') and answer.feedback_details:
                        if isinstance(answer.feedback_details, dict):
                            analysis_item["improvement_suggestions"] = answer.feedback_details.get("improvement_suggestions", [])
                    
                    question_analyses.append(analysis_item)
                    
                except Exception as item_error:
                    print(f"[DETAILED_REPORT] 질문 {i} 분석 오류: {item_error}")
                    # 기본 분석 항목 추가
                    question_analyses.append({
                        "question": f"질문 {i+1} (데이터 오류)",
                        "category": "general",
                        "difficulty": "medium",
                        "answer": "데이터를 불러올 수 없습니다",
                        "score": 0.0,
                        "feedback": "분석 데이터 오류",
                        "improvement_suggestions": []
                    })
                    
        except Exception as qa_error:
            print(f"[DETAILED_REPORT] 질문별 분석 구성 오류: {qa_error}")
            question_analyses = []
        
        # 평균 점수 계산
        try:
            answered_questions = [q for q in question_analyses if q.get("score", 0) > 0]
            avg_score = sum(q.get("score", 0) for q in answered_questions) / len(answered_questions) if answered_questions else 0.0
            print(f"[DETAILED_REPORT] 평균 점수 계산: {avg_score:.2f} (답변된 질문: {len(answered_questions)}개)")
        except Exception as avg_error:
            print(f"[DETAILED_REPORT] 평균 점수 계산 오류: {avg_error}")
            avg_score = 0.0
        
        # 카테고리별 점수 계산
        try:
            category_scores = {}
            if hasattr(session, 'feedback') and session.feedback and isinstance(session.feedback, dict):
                category_scores = session.feedback.get("category_scores", {})
            print(f"[DETAILED_REPORT] 카테고리별 점수: {category_scores}")
        except Exception as cat_error:
            print(f"[DETAILED_REPORT] 카테고리 점수 계산 오류: {cat_error}")
            category_scores = {}
        
        # 성능 지표 계산
        try:
            performance_metrics = {
                "response_time_avg": 45.0,  # 실제 답변 시간 계산은 추후 구현
                "completeness_score": (len(answers) / max(len(questions), 1)) * 100 if questions else 0,
                "technical_accuracy": category_scores.get("technical_accuracy", avg_score),
                "communication_clarity": category_scores.get("communication", avg_score)
            }
            print(f"[DETAILED_REPORT] 성능 지표: {performance_metrics}")
        except Exception as perf_error:
            print(f"[DETAILED_REPORT] 성능 지표 계산 오류: {perf_error}")
            performance_metrics = {
                "response_time_avg": 45.0,
                "completeness_score": 0,
                "technical_accuracy": 0,
                "communication_clarity": 0
            }
        
        # 종합 평가 구성
        try:
            overall_score = float(session.overall_score) if hasattr(session, 'overall_score') and session.overall_score else avg_score
            print(f"[DETAILED_REPORT] 종합 점수: {overall_score}")
        except Exception as overall_error:
            print(f"[DETAILED_REPORT] 종합 점수 계산 오류: {overall_error}")
            overall_score = avg_score
        overall_assessment = {
            "score": round(overall_score, 1),
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        # 강점과 약점 분석
        if overall_score >= 8.0:
            overall_assessment["strengths"].extend([
                "높은 기술적 이해도",
                "명확한 의사소통",
                "체계적인 문제 접근법"
            ])
        elif overall_score >= 6.0:
            overall_assessment["strengths"].extend([
                "기본적인 개념 이해",
                "적절한 답변 구조"
            ])
        
        if overall_score < 6.0:
            overall_assessment["weaknesses"].extend([
                "기술적 정확성 부족",
                "문제 해결 능력 개선 필요"
            ])
            overall_assessment["recommendations"].extend([
                "핵심 개념 복습 권장",
                "실습 프로젝트 수행",
                "기술 문서 정독"
            ])
        elif overall_score < 8.0:
            overall_assessment["weaknesses"].extend([
                "세부 구현 이해 부족",
                "최적화 관점 부족"
            ])
            overall_assessment["recommendations"].extend([
                "심화 학습 권장",
                "코드 리뷰 경험 증대"
            ])
        
        # AI 인사이트 생성 및 확장된 분석 데이터 조회
        try:
            enhanced_insights = await _generate_and_store_insights(
                session, questions, answers, analysis, db
            )
            print(f"[DETAILED_REPORT] AI 인사이트 생성 완료")
        except Exception as insight_error:
            print(f"[DETAILED_REPORT] AI 인사이트 생성 실패: {insight_error}")
            enhanced_insights = None

        detailed_report = {
            "interview_id": str(session.id),
            "repo_info": repo_info,
            "overall_assessment": overall_assessment,
            "question_analyses": question_analyses,
            "performance_metrics": performance_metrics
        }
        
        # 새로운 인사이트 섹션들 추가 (실제 AI 분석이 성공한 경우에만)
        if enhanced_insights:
            detailed_report.update({
                "interview_summary": enhanced_insights.get("interview_summary"),
                "technical_analysis": enhanced_insights.get("technical_analysis"),
                "improvement_plan": enhanced_insights.get("improvement_plan")
            })
        else:
            # 답변이 없는 경우 AI 분석 섹션 제외
            if len(answers) == 0:
                print(f"[DETAILED_REPORT] 답변 없음 - AI 분석 섹션 제외")
            else:
                # AI 분석 실패 시 데이터베이스에서 직접 조회
                existing_report = db.query(InterviewReport)\
                    .filter(InterviewReport.session_id == session.id)\
                    .first()
                
                if existing_report and existing_report.is_ai_generated:
                    # 데이터베이스에 실제 AI 분석 데이터가 있는 경우
                    detailed_report.update({
                        "interview_summary": {
                            "overall_comment": existing_report.overall_summary,
                            "readiness_score": existing_report.interview_readiness_score,
                            "key_talking_points": existing_report.key_talking_points
                        }
                    })
                    
                    # 기술 분석 데이터 조회
                    technical_analysis = db.query(ProjectTechnicalAnalysis)\
                        .filter(ProjectTechnicalAnalysis.report_id == existing_report.id)\
                        .filter(ProjectTechnicalAnalysis.is_ai_generated == True)\
                        .first()
                    
                    if technical_analysis:
                        detailed_report["technical_analysis"] = {
                            "architecture_understanding": technical_analysis.architecture_understanding,
                            "code_quality_awareness": technical_analysis.code_quality_awareness,
                            "problem_solving_approach": technical_analysis.problem_solving_approach,
                            "technology_depth": technical_analysis.technology_depth,
                            "project_complexity_handling": technical_analysis.project_complexity_handling
                        }
                    
                    # 개선 플랜 데이터 조회
                    improvement_plan = db.query(InterviewImprovementPlan)\
                        .filter(InterviewImprovementPlan.report_id == existing_report.id)\
                        .filter(InterviewImprovementPlan.is_ai_generated == True)\
                        .first()
                    
                    if improvement_plan:
                        detailed_report["improvement_plan"] = {
                            "immediate_actions": improvement_plan.immediate_actions,
                            "study_recommendations": improvement_plan.study_recommendations,
                            "practice_scenarios": improvement_plan.practice_scenarios,
                            "weak_areas": improvement_plan.weak_areas,
                            "preparation_timeline": improvement_plan.preparation_timeline
                        }
                else:
                    # AI 분석 데이터가 없는 경우 - 빈 섹션으로 표시하거나 분석 진행 중 표시
                    print(f"[DETAILED_REPORT] AI 분석 데이터 없음 - 빈 인사이트 섹션")
        
        print(f"[DETAILED_REPORT] 상세 리포트 생성 완료")
        
        return {
            "success": True,
            "data": detailed_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DETAILED_REPORT] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=Dict[str, Any])
async def get_recent_reports(limit: int = 5, db: Session = Depends(get_db)):
    """최근 완료된 면접 리포트 요약 조회 (데이터베이스 기반)"""
    try:
        # 개발 모드 활성화 여부 확인
        from app.core.config import is_development_mode_active
        if not is_development_mode_active():
            print(f"[RECENT_REPORTS] 개발 모드 비활성화 - 빈 결과 반환")
            return {
                "success": True,
                "data": {
                    "reports": [],
                    "total": 0,
                    "message": "Development mode is disabled. Recent reports are not available."
                }
            }
        
        print(f"[RECENT_REPORTS] 최근 리포트 요청 - limit: {limit}")
        
        # 데이터베이스에서 완료된 면접 세션 조회
        from app.models.repository import RepositoryAnalysis
        from sqlalchemy import desc, and_
        
        # 완료된 면접 세션 조회 (completed 상태 또는 overall_score가 있는 것)
        completed_sessions = db.query(InterviewSession)\
            .join(RepositoryAnalysis, InterviewSession.analysis_id == RepositoryAnalysis.id)\
            .filter(
                and_(
                    InterviewSession.status == "completed",
                    InterviewSession.overall_score.isnot(None)
                )
            )\
            .order_by(desc(InterviewSession.ended_at))\
            .limit(limit)\
            .all()
        
        completed_reports = []
        
        for session in completed_sessions:
            # 연관된 저장소 분석 정보 가져오기
            analysis = session.analysis
            if not analysis:
                continue
                
            # URL에서 owner/repo 추출
            url_parts = analysis.repository_url.replace("https://github.com/", "").split("/")
            repo_owner = url_parts[0] if len(url_parts) > 0 else "Unknown"
            repo_name = url_parts[1] if len(url_parts) > 1 else analysis.repository_name or "Unknown"
            
            # 면접 지속 시간 계산 (최대 10시간 = 600분으로 제한)
            duration_minutes = 0
            if session.started_at and session.ended_at:
                duration_seconds = (session.ended_at - session.started_at).total_seconds()
                duration_minutes = min(int(duration_seconds / 60), 600)  # 최대 600분(10시간)
            
            # 카테고리별 점수 (feedback JSON에서 추출)
            category_scores = {}
            if session.feedback and isinstance(session.feedback, dict):
                category_scores = session.feedback.get("category_scores", {})
            
            # 답변 개수 계산
            answers_count = len(session.answers) if session.answers else 0
            questions_count = len(session.interview_questions) if hasattr(session, 'interview_questions') else 0
            
            completed_reports.append({
                "interview_id": str(session.id),
                "repository_name": repo_name,
                "repository_owner": repo_owner,
                "overall_score": round(float(session.overall_score), 1) if session.overall_score else 0.0,
                "completed_at": session.ended_at.isoformat() if session.ended_at else None,
                "duration_minutes": duration_minutes,
                "questions_count": questions_count,
                "answers_count": answers_count,
                "category_scores": category_scores,
                "difficulty_level": session.difficulty
            })
        
        print(f"[RECENT_REPORTS] 데이터베이스에서 {len(completed_reports)}개 리포트 반환")
        
        return {
            "success": True,
            "data": {
                "reports": completed_reports,
                "total_completed": len(completed_reports)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[RECENT_REPORTS] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "data": {
                "reports": [],
                "total_completed": 0
            },
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/health/services")
async def check_services_health():
    """
    서비스들의 상태 확인
    
    Returns:
        각 서비스의 상태 정보
    """
    try:
        health_status = {
            "interview_agent": {
                "status": "healthy",
                "active_sessions": len(interview_agent.active_sessions),
                "details": "Mock Interview Agent 정상 작동"
            },
            "repository_analyzer": {
                "status": "healthy",
                "details": "Repository Analyzer 정상 작동"
            },
            "question_generator": {
                "status": "healthy",
                "details": "Question Generator 정상 작동"
            },
            "vector_db": {
                "status": "unknown",
                "details": "Vector DB 연결 상태 확인 필요"
            }
        }
        
        # Vector DB 연결 테스트
        try:
            vector_db = get_vector_db()
            if vector_db and vector_db.code_collection is not None:
                health_status["vector_db"]["status"] = "healthy"
                health_status["vector_db"]["details"] = "ChromaDB 연결 정상"
            else:
                health_status["vector_db"]["status"] = "degraded"
                health_status["vector_db"]["details"] = "ChromaDB 연결 없음 (기능 제한)"
        except Exception as e:
            health_status["vector_db"]["status"] = "unhealthy"
            health_status["vector_db"]["details"] = f"ChromaDB 오류: {str(e)}"
        
        # 전체 상태 결정
        all_statuses = [service["status"] for service in health_status.values()]
        
        if "unhealthy" in all_statuses:
            overall_status = "unhealthy"
        elif "degraded" in all_statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "success": True,
            "overall_status": overall_status,
            "services": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def _enhance_interview_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """면접 리포트 향상"""
    
    enhanced_report = report.copy()
    
    # 추가 분석 정보
    if "detailed_evaluation" in report and report["detailed_evaluation"]:
        evaluations = report["detailed_evaluation"]
        
        # 질문별 성능 분석
        question_performance = []
        for i, evaluation in enumerate(evaluations):
            performance = {
                "question_number": i + 1,
                "overall_score": evaluation.get("overall_score", 0),
                "criteria_scores": evaluation.get("criteria_scores", {}),
                "time_efficiency": "good",  # 실제로는 시간 기반 계산
                "improvement_level": _calculate_improvement_level(evaluation)
            }
            question_performance.append(performance)
        
        enhanced_report["question_performance"] = question_performance
        
        # 전체 진행률 분석
        avg_scores = {
            "technical_accuracy": 0,
            "code_quality": 0,
            "problem_solving": 0,
            "communication": 0
        }
        
        for criteria in avg_scores.keys():
            scores = [eval_data.get("criteria_scores", {}).get(criteria, 0) 
                     for eval_data in evaluations]
            avg_scores[criteria] = sum(scores) / len(scores) if scores else 0
        
        enhanced_report["category_averages"] = avg_scores
        enhanced_report["strongest_area"] = max(avg_scores, key=avg_scores.get)
        enhanced_report["weakest_area"] = min(avg_scores, key=avg_scores.get)
    
    # 개선 우선순위
    enhanced_report["improvement_priority"] = _generate_improvement_priority(enhanced_report)
    
    # 학습 리소스 추천
    enhanced_report["learning_resources"] = _recommend_learning_resources(enhanced_report)
    
    return enhanced_report


def _calculate_improvement_level(evaluation: Dict[str, Any]) -> str:
    """개선 수준 계산"""
    overall_score = evaluation.get("overall_score", 0)
    
    if overall_score >= 8.5:
        return "excellent"
    elif overall_score >= 7.0:
        return "good"
    elif overall_score >= 5.5:
        return "needs_improvement"
    else:
        return "needs_significant_improvement"


def _identify_improvement_areas(criteria_averages: Dict[str, float]) -> List[str]:
    """개선이 필요한 영역 식별"""
    improvement_areas = []
    
    for criteria, score in criteria_averages.items():
        if score < 6.0:
            improvement_areas.append(criteria)
    
    # 점수가 낮은 순으로 정렬
    improvement_areas.sort(key=lambda x: criteria_averages[x])
    
    return improvement_areas


def _identify_strengths(criteria_averages: Dict[str, float]) -> List[str]:
    """강점 영역 식별"""
    strengths = []
    
    for criteria, score in criteria_averages.items():
        if score >= 8.0:
            strengths.append(criteria)
    
    # 점수가 높은 순으로 정렬
    strengths.sort(key=lambda x: criteria_averages[x], reverse=True)
    
    return strengths


def _generate_improvement_priority(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """개선 우선순위 생성"""
    priorities = []
    
    if "category_averages" in report:
        averages = report["category_averages"]
        
        for criteria, score in sorted(averages.items(), key=lambda x: x[1]):
            if score < 7.0:
                priority_level = "high" if score < 5.0 else "medium" if score < 6.5 else "low"
                
                priorities.append({
                    "category": criteria,
                    "current_score": round(score, 2),
                    "target_score": min(score + 2.0, 10.0),
                    "priority": priority_level,
                    "estimated_effort": "2-4 weeks" if priority_level == "high" else "1-2 weeks"
                })
    
    return priorities


def _recommend_learning_resources(report: Dict[str, Any]) -> Dict[str, List[str]]:
    """학습 리소스 추천"""
    resources = {
        "technical_accuracy": [
            "공식 기술 문서 읽기",
            "온라인 코딩 플랫폼 문제 해결",
            "기술 서적 읽기"
        ],
        "code_quality": [
            "Clean Code 서적 읽기",
            "코드 리뷰 참여",
            "리팩토링 연습"
        ],
        "problem_solving": [
            "알고리즘 문제 해결",
            "시스템 디자인 연습",
            "케이스 스터디 분석"
        ],
        "communication": [
            "기술 발표 연습",
            "기술 블로그 작성",
            "페어 프로그래밍 참여"
        ]
    }
    
    recommended = {}
    
    if "weakest_area" in report:
        weakest = report["weakest_area"]
        if weakest in resources:
            recommended[weakest] = resources[weakest]
    
    # 개선이 필요한 모든 영역에 대한 리소스 추가
    if "improvement_priority" in report:
        for priority in report["improvement_priority"]:
            category = priority["category"]
            if category in resources and category not in recommended:
                recommended[category] = resources[category]
    
    return recommended


# 새로 추가되는 AI 인사이트 관련 함수들

async def _generate_and_store_insights(session, questions, answers, analysis, db):
    """AI 인사이트 생성 및 데이터베이스 저장"""
    from app.agents.report_generator_agent import get_report_generator
    import uuid
    
    try:
        # ReportGenerator 에이전트 인스턴스 가져오기
        report_generator = get_report_generator()
        
        # 프로젝트 컨텍스트 구성
        project_context = {
            "repository_url": analysis.repository_url,
            "tech_stack": analysis.tech_stack or {},
            "complexity_score": float(analysis.complexity_score) if analysis.complexity_score else 5.0,
            "primary_language": analysis.primary_language
        }
        
        # 면접 데이터 구성
        interview_data = {
            "questions": [
                {
                    "question": q.question_text,
                    "category": q.category,
                    "difficulty": q.difficulty
                } for q in questions
            ],
            "answers": [
                {
                    "answer": a.user_answer,
                    "score": float(a.feedback_score) if a.feedback_score else 0.0,
                    "feedback": a.feedback_message
                } for a in answers
            ]
        }
        
        print(f"[INSIGHTS] AI 인사이트 생성 시작 - 질문 {len(questions)}개, 답변 {len(answers)}개")
        
        # 답변이 없는 경우 AI 분석 생성하지 않음
        if len(answers) == 0:
            print(f"[INSIGHTS] 답변이 없어 AI 분석 생성 중단")
            return None
        
        # AI 인사이트 생성
        insights = await report_generator.generate_interview_insights(
            project_context=project_context,
            interview_data=interview_data
        )
        
        # AI 생성 성공 여부 확인 (폴백 데이터가 아닌 실제 AI 분석인지 검증)
        is_real_ai_analysis = _validate_real_ai_analysis(insights)
        print(f"[INSIGHTS] AI 인사이트 생성 완료 - 실제 AI 분석: {is_real_ai_analysis}")
        
        # InterviewReport 조회 또는 생성
        existing_report = db.query(InterviewReport)\
            .filter(InterviewReport.session_id == session.id)\
            .first()
        
        if existing_report:
            # 기존 리포트 업데이트 (실제 AI 분석인 경우에만)
            if is_real_ai_analysis:
                existing_report.overall_summary = insights["interview_summary"]["overall_comment"]
                existing_report.interview_readiness_score = insights["interview_summary"]["readiness_score"]
                existing_report.key_talking_points = insights["interview_summary"]["key_talking_points"]
                existing_report.is_ai_generated = True
            else:
                existing_report.is_ai_generated = False
            report_id = existing_report.id
            print(f"[INSIGHTS] 기존 리포트 업데이트: {report_id} (AI 분석: {is_real_ai_analysis})")
        else:
            # 새 리포트 생성
            new_report = InterviewReport(
                session_id=session.id,
                overall_score=5.0,  # 기본값
                category_scores={"general": 5.0},
                overall_summary=insights["interview_summary"]["overall_comment"] if is_real_ai_analysis else None,
                interview_readiness_score=insights["interview_summary"]["readiness_score"] if is_real_ai_analysis else None,
                key_talking_points=insights["interview_summary"]["key_talking_points"] if is_real_ai_analysis else None,
                is_ai_generated=is_real_ai_analysis
            )
            db.add(new_report)
            db.flush()  # ID 생성을 위해 flush
            report_id = new_report.id
            print(f"[INSIGHTS] 새 리포트 생성: {report_id} (AI 분석: {is_real_ai_analysis})")
        
        # ProjectTechnicalAnalysis 저장/업데이트
        existing_technical = db.query(ProjectTechnicalAnalysis)\
            .filter(ProjectTechnicalAnalysis.report_id == report_id)\
            .first()
            
        tech_analysis_data = insights["technical_analysis"]
        
        if existing_technical:
            # 업데이트 (실제 AI 분석인 경우에만)
            if is_real_ai_analysis:
                existing_technical.architecture_understanding = tech_analysis_data["architecture_understanding"]
                existing_technical.code_quality_awareness = tech_analysis_data["code_quality_awareness"]
                existing_technical.problem_solving_approach = tech_analysis_data["problem_solving_approach"]
                existing_technical.technology_depth = tech_analysis_data["technology_depth"]
                existing_technical.project_complexity_handling = tech_analysis_data["project_complexity_handling"]
                existing_technical.is_ai_generated = True
            else:
                existing_technical.is_ai_generated = False
            print(f"[INSIGHTS] 기술 분석 업데이트 완료 (AI 분석: {is_real_ai_analysis})")
        else:
            # 생성
            technical_analysis = ProjectTechnicalAnalysis(
                report_id=report_id,
                architecture_understanding=tech_analysis_data["architecture_understanding"] if is_real_ai_analysis else None,
                code_quality_awareness=tech_analysis_data["code_quality_awareness"] if is_real_ai_analysis else None,
                problem_solving_approach=tech_analysis_data["problem_solving_approach"] if is_real_ai_analysis else None,
                technology_depth=tech_analysis_data["technology_depth"] if is_real_ai_analysis else None,
                project_complexity_handling=tech_analysis_data["project_complexity_handling"] if is_real_ai_analysis else None,
                is_ai_generated=is_real_ai_analysis
            )
            db.add(technical_analysis)
            print(f"[INSIGHTS] 새 기술 분석 생성 완료 (AI 분석: {is_real_ai_analysis})")
        
        # InterviewImprovementPlan 저장/업데이트
        existing_plan = db.query(InterviewImprovementPlan)\
            .filter(InterviewImprovementPlan.report_id == report_id)\
            .first()
            
        improvement_data = insights["improvement_plan"]
        
        if existing_plan:
            # 업데이트 (실제 AI 분석인 경우에만)
            if is_real_ai_analysis:
                existing_plan.immediate_actions = improvement_data["immediate_actions"]
                existing_plan.study_recommendations = improvement_data["study_recommendations"]
                existing_plan.practice_scenarios = improvement_data["practice_scenarios"]
                existing_plan.weak_areas = improvement_data["weak_areas"]
                existing_plan.preparation_timeline = improvement_data["preparation_timeline"]
                existing_plan.is_ai_generated = True
            else:
                existing_plan.is_ai_generated = False
            print(f"[INSIGHTS] 개선 플랜 업데이트 완료 (AI 분석: {is_real_ai_analysis})")
        else:
            # 생성
            improvement_plan = InterviewImprovementPlan(
                report_id=report_id,
                immediate_actions=improvement_data["immediate_actions"] if is_real_ai_analysis else None,
                study_recommendations=improvement_data["study_recommendations"] if is_real_ai_analysis else None,
                practice_scenarios=improvement_data["practice_scenarios"] if is_real_ai_analysis else None,
                weak_areas=improvement_data["weak_areas"] if is_real_ai_analysis else None,
                preparation_timeline=improvement_data["preparation_timeline"] if is_real_ai_analysis else None,
                is_ai_generated=is_real_ai_analysis
            )
            db.add(improvement_plan)
            print(f"[INSIGHTS] 새 개선 플랜 생성 완료 (AI 분석: {is_real_ai_analysis})")
        
        # 데이터베이스 커밋
        db.commit()
        print(f"[INSIGHTS] 데이터베이스 저장 완료")
        
        # 실제 AI 분석이 성공한 경우에만 인사이트 반환
        if is_real_ai_analysis:
            return insights
        else:
            print(f"[INSIGHTS] 폴백 데이터 사용됨 - 인사이트 반환하지 않음")
            return None
        
    except Exception as e:
        print(f"[INSIGHTS] 오류 발생: {e}")
        db.rollback()
        raise e


def _validate_real_ai_analysis(insights: dict) -> bool:
    """
    AI 분석이 실제 분석인지 폴백 데이터인지 검증
    폴백 데이터의 특정 패턴을 감지하여 판단
    """
    try:
        # 1. 폴백 데이터의 고정 점수값 확인
        tech_analysis = insights.get("technical_analysis", {})
        arch_score = tech_analysis.get("architecture_understanding", 0)
        quality_score = tech_analysis.get("code_quality_awareness", 0)
        
        # 폴백 데이터의 정확한 점수값들 (65, 60)
        fallback_scores = [65, 60]
        if arch_score in fallback_scores and quality_score in fallback_scores:
            print(f"[VALIDATION] 폴백 점수 패턴 감지: {arch_score}, {quality_score}")
            return False
        
        # 2. 폴백 데이터의 고정 문구 확인
        summary = insights.get("interview_summary", {})
        overall_comment = summary.get("overall_comment", "")
        
        fallback_phrases = [
            "프로젝트에 대한 기본적인 이해도를 보여주었으나",
            "기술적 세부사항과 구현 경험에 대한 더 깊은 설명이 필요합니다"
        ]
        
        for phrase in fallback_phrases:
            if phrase in overall_comment:
                print(f"[VALIDATION] 폴백 문구 감지: {phrase}")
                return False
        
        # 3. 개선 플랜의 고정 액션 확인
        improvement_plan = insights.get("improvement_plan", {})
        immediate_actions = improvement_plan.get("immediate_actions", [])
        
        fallback_actions = [
            "답변 시 STAR 방법론(Situation, Task, Action, Result) 활용",
            "기술 용어 사용 시 구체적인 예시와 함께 설명"
        ]
        
        for action in fallback_actions:
            if action in immediate_actions:
                print(f"[VALIDATION] 폴백 액션 감지: {action}")
                return False
        
        print(f"[VALIDATION] 실제 AI 분석으로 판정")
        return True
        
    except Exception as e:
        print(f"[VALIDATION] 검증 중 오류: {e} - 폴백으로 판정")
        return False

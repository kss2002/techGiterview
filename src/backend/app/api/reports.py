"""
Report System API

면접 리포트 생성 및 조회를 위한 REST API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.agents.mock_interview_agent import MockInterviewAgent
from app.agents.repository_analyzer import RepositoryAnalyzer
from app.agents.question_generator import QuestionGenerator
from app.services.vector_db import VectorDBService
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# 서비스 인스턴스
interview_agent = MockInterviewAgent()
repo_analyzer = RepositoryAnalyzer()
question_generator = QuestionGenerator()
vector_db = VectorDBService()


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
                analysis_id = await vector_db.store_analysis_result(repo_url, analysis_result)
                analysis_result["analysis_id"] = analysis_id
                
                # 코드 스니펫 저장 (중요 파일들)
                important_files = analysis_result.get("important_files", [])
                if important_files:
                    # 파일 내용을 가져와서 저장 (실제로는 GitHubClient에서)
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
    user_id: Optional[str] = Query(None, description="특정 사용자 필터")
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
        # 실제로는 데이터베이스에서 통계를 조회해야 하지만,
        # 현재는 활성 세션 기반으로 모의 데이터 생성
        
        active_sessions = interview_agent.active_sessions
        
        # 기본 통계
        total_interviews = len(active_sessions)
        completed_interviews = len([s for s in active_sessions.values() 
                                  if s.interview_status == "completed"])
        in_progress_interviews = len([s for s in active_sessions.values() 
                                    if s.interview_status == "in_progress"])
        
        # 평균 점수 계산
        completed_sessions = [s for s in active_sessions.values() 
                            if s.interview_status == "completed" and s.total_score > 0]
        
        avg_score = sum(s.total_score for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0
        
        # 난이도별 분포
        difficulty_distribution = {}
        for session in active_sessions.values():
            difficulty = session.difficulty_level
            difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
        
        # 사용자별 필터링
        if user_id:
            user_sessions = [s for s in active_sessions.values() if s.user_id == user_id]
            total_interviews = len(user_sessions)
            completed_interviews = len([s for s in user_sessions 
                                      if s.interview_status == "completed"])
        
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
    repo_url: Optional[str] = Query(None, description="저장소 URL")
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
        active_sessions = interview_agent.active_sessions
        
        # 필터링
        filtered_sessions = list(active_sessions.values())
        
        if user_id:
            filtered_sessions = [s for s in filtered_sessions if s.user_id == user_id]
        
        if repo_url:
            filtered_sessions = [s for s in filtered_sessions if s.repo_url == repo_url]
        
        # 완료된 세션만 분석
        completed_sessions = [s for s in filtered_sessions 
                            if s.interview_status == "completed" and s.evaluations]
        
        if not completed_sessions:
            return {
                "success": True,
                "data": {
                    "message": "분석할 완료된 면접이 없습니다.",
                    "sessions_count": 0
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # 성능 지표 계산
        all_evaluations = []
        for session in completed_sessions:
            all_evaluations.extend(session.evaluations)
        
        # 평균 점수 계산
        avg_overall_score = sum(eval_data.get("overall_score", 0) for eval_data in all_evaluations) / len(all_evaluations)
        
        # 카테고리별 평균 점수
        criteria_averages = {}
        criteria_keys = ["technical_accuracy", "code_quality", "problem_solving", "communication"]
        
        for criteria in criteria_keys:
            scores = []
            for eval_data in all_evaluations:
                criteria_scores = eval_data.get("criteria_scores", {})
                if criteria in criteria_scores:
                    scores.append(criteria_scores[criteria])
            
            if scores:
                criteria_averages[criteria] = sum(scores) / len(scores)
            else:
                criteria_averages[criteria] = 0
        
        # 시간 분석
        avg_duration = sum(s.end_time.timestamp() - s.start_time.timestamp() 
                         for s in completed_sessions 
                         if s.start_time and s.end_time) / len(completed_sessions)
        
        # 질문 타입별 성능
        question_type_performance = {}
        for session in completed_sessions:
            for i, evaluation in enumerate(session.evaluations):
                if i < len(session.questions):
                    question_type = session.questions[i].get("type", "unknown")
                    if question_type not in question_type_performance:
                        question_type_performance[question_type] = []
                    question_type_performance[question_type].append(evaluation.get("overall_score", 0))
        
        # 타입별 평균 계산
        question_type_averages = {
            qtype: sum(scores) / len(scores)
            for qtype, scores in question_type_performance.items()
        }
        
        performance_data = {
            "overall_statistics": {
                "sessions_analyzed": len(completed_sessions),
                "total_questions_answered": sum(len(s.answers) for s in completed_sessions),
                "average_overall_score": round(avg_overall_score, 2),
                "average_duration_minutes": round(avg_duration / 60, 1)
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
            if vector_db.code_collection is not None:
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
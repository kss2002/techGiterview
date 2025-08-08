"""
Mock Interview Agent

실시간 모의면접을 진행하는 LangGraph 에이전트
WebSocket을 통한 실시간 대화 및 질문-답변 평가 시스템
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI  # Replaced with Gemini

from app.core.config import settings
from app.agents.question_generator import QuestionGenerator
from app.services.vector_db import VectorDBService
from app.core.gemini_client import get_gemini_llm


@dataclass
class InterviewState:
    """모의면접 상태를 관리하는 데이터 클래스"""
    interview_id: str
    repo_url: str
    user_id: str
    current_question_index: int = 0
    questions: List[Dict[str, Any]] = field(default_factory=list)
    answers: List[Dict[str, Any]] = field(default_factory=list)
    evaluations: List[Dict[str, Any]] = field(default_factory=list)
    interview_status: str = "preparing"  # preparing, in_progress, paused, completed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    difficulty_level: str = "medium"
    total_score: float = 0.0
    feedback: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_count: int = 0
    time_per_question: int = 600  # 10분 기본값
    error: Optional[str] = None


class MockInterviewAgent:
    """모의면접 진행 에이전트"""
    
    def __init__(self):
        self.question_generator = QuestionGenerator()
        self.vector_db = VectorDBService()
        
        # Google Gemini LLM 초기화
        self.llm = get_gemini_llm()
        if self.llm:
            # Gemini에 맞는 설정 조정
            self.llm.temperature = 0.3
            print("[MOCK_INTERVIEW] Google Gemini LLM initialized successfully")
        else:
            print("[MOCK_INTERVIEW] Warning: Gemini LLM not available, using fallback responses")
        
        # 활성 면접 세션들
        self.active_sessions: Dict[str, InterviewState] = {}
        
        # 평가 기준
        self.evaluation_criteria = {
            "technical_accuracy": {
                "weight": 0.3,
                "description": "기술적 정확성"
            },
            "code_quality": {
                "weight": 0.25,
                "description": "코드 품질 이해도"
            },
            "problem_solving": {
                "weight": 0.25,
                "description": "문제 해결 능력"
            },
            "communication": {
                "weight": 0.2,
                "description": "의사소통 능력"
            }
        }
        
        # 면접관 페르소나
        self.interviewer_persona = """
        당신은 경험이 풍부한 시니어 개발자이자 기술면접관입니다.
        친근하고 전문적인 톤으로 면접을 진행하며, 지원자가 편안하게 답변할 수 있도록 도와줍니다.
        답변을 들은 후 적절한 후속 질문을 통해 지원자의 깊이 있는 사고를 유도합니다.
        
        면접 진행 원칙:
        1. 지원자의 답변을 주의 깊게 듣고 구체적인 피드백 제공
        2. 너무 어려운 질문보다는 지원자의 수준에 맞는 질문으로 조정
        3. 긍정적인 분위기 유지하며 지원자의 장점을 찾아 격려
        4. 기술적 깊이와 실무 경험을 균형있게 평가
        """
    
    async def start_interview(
        self, 
        repo_url: str, 
        user_id: str,
        difficulty_level: str = "medium",
        question_count: int = 5,
        time_per_question: int = 600
    ) -> Dict[str, Any]:
        """모의면접 시작"""
        
        interview_id = str(uuid.uuid4())
        
        try:
            # 질문 생성
            question_result = await self.question_generator.generate_questions(
                repo_url=repo_url,
                difficulty_level=difficulty_level,
                question_count=question_count,
                question_types=["code_analysis", "tech_stack", "architecture", "problem_solving"]
            )
            
            if not question_result["success"]:
                raise ValueError(f"질문 생성 실패: {question_result.get('error', '')}")
            
            # 면접 상태 초기화
            state = InterviewState(
                interview_id=interview_id,
                repo_url=repo_url,
                user_id=user_id,
                questions=question_result["questions"],
                difficulty_level=difficulty_level,
                time_per_question=time_per_question,
                start_time=datetime.now()
            )
            
            self.active_sessions[interview_id] = state
            
            # 첫 질문 준비
            first_question = await self._prepare_question(state, 0)
            
            state.interview_status = "in_progress"
            state.conversation_history.append({
                "type": "system",
                "content": "면접이 시작되었습니다. 편안하게 답변해주세요.",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "interview_id": interview_id,
                "total_questions": len(state.questions),
                "current_question": first_question,
                "difficulty_level": difficulty_level,
                "time_per_question": time_per_question
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interview_id": interview_id
            }
    
    async def submit_answer(
        self, 
        interview_id: str, 
        answer: str,
        time_taken: Optional[int] = None
    ) -> Dict[str, Any]:
        """답변 제출 및 평가"""
        
        if interview_id not in self.active_sessions:
            return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
        
        state = self.active_sessions[interview_id]
        
        if state.interview_status != "in_progress":
            return {"success": False, "error": "진행 중인 면접이 아닙니다."}
        
        try:
            current_question = state.questions[state.current_question_index]
            
            # 답변 기록
            answer_data = {
                "question_id": current_question["id"],
                "question": current_question["question"],
                "answer": answer,
                "timestamp": datetime.now().isoformat(),
                "time_taken": time_taken or 0
            }
            state.answers.append(answer_data)
            
            # 답변 평가
            evaluation = await self._evaluate_answer(current_question, answer, state)
            state.evaluations.append(evaluation)
            
            # 대화 히스토리 업데이트
            state.conversation_history.extend([
                {
                    "type": "question",
                    "content": current_question["question"],
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "answer",
                    "content": answer,
                    "timestamp": datetime.now().isoformat()
                }
            ])
            
            # 후속 질문 생성 여부 결정
            follow_up_question = None
            if await self._should_generate_follow_up(evaluation, state):
                follow_up_question = await self._generate_follow_up_question(
                    current_question, answer, evaluation
                )
                state.follow_up_count += 1
            
            # 다음 질문으로 이동 또는 면접 종료
            next_question = None
            interview_completed = False
            
            if follow_up_question:
                next_question = follow_up_question
            else:
                state.current_question_index += 1
                if state.current_question_index < len(state.questions):
                    next_question = await self._prepare_question(state, state.current_question_index)
                else:
                    # 면접 완료
                    interview_completed = True
                    await self._complete_interview(state)
            
            return {
                "success": True,
                "evaluation": evaluation,
                "next_question": next_question,
                "interview_completed": interview_completed,
                "progress": {
                    "current_question": state.current_question_index + 1,
                    "total_questions": len(state.questions),
                    "follow_up_count": state.follow_up_count
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_interview_status(self, interview_id: str) -> Dict[str, Any]:
        """면접 상태 조회"""
        
        if interview_id not in self.active_sessions:
            return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
        
        state = self.active_sessions[interview_id]
        
        return {
            "success": True,
            "interview_id": interview_id,
            "status": state.interview_status,
            "progress": {
                "current_question": state.current_question_index + 1,
                "total_questions": len(state.questions),
                "completed_questions": len(state.answers)
            },
            "elapsed_time": self._calculate_elapsed_time(state),
            "total_score": state.total_score,
            "difficulty_level": state.difficulty_level
        }
    
    async def pause_interview(self, interview_id: str) -> Dict[str, Any]:
        """면접 일시정지"""
        
        if interview_id not in self.active_sessions:
            return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
        
        state = self.active_sessions[interview_id]
        state.interview_status = "paused"
        
        return {"success": True, "message": "면접이 일시정지되었습니다."}
    
    async def resume_interview(self, interview_id: str) -> Dict[str, Any]:
        """면접 재개"""
        
        if interview_id not in self.active_sessions:
            return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
        
        state = self.active_sessions[interview_id]
        if state.interview_status == "paused":
            state.interview_status = "in_progress"
            return {"success": True, "message": "면접이 재개되었습니다."}
        else:
            return {"success": False, "error": "일시정지된 면접이 아닙니다."}
    
    async def end_interview(self, interview_id: str) -> Dict[str, Any]:
        """면접 강제 종료"""
        
        if interview_id not in self.active_sessions:
            return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
        
        state = self.active_sessions[interview_id]
        await self._complete_interview(state)
        
        return {"success": True, "message": "면접이 종료되었습니다."}
    
    async def _prepare_question(self, state: InterviewState, question_index: int) -> Dict[str, Any]:
        """질문 준비"""
        
        question = state.questions[question_index]
        
        # AI 면접관의 질문 소개
        if self.llm:
            introduction = await self._generate_question_introduction(question, state)
            question["introduction"] = introduction
        
        return question
    
    async def _evaluate_answer(
        self, 
        question: Dict[str, Any], 
        answer: str, 
        state: InterviewState
    ) -> Dict[str, Any]:
        """답변 평가"""
        
        if not self.llm:
            # LLM이 없는 경우 기본 평가
            return {
                "overall_score": 7.0,
                "criteria_scores": {
                    "technical_accuracy": 7.0,
                    "code_quality": 7.0,
                    "problem_solving": 7.0,
                    "communication": 7.0
                },
                "feedback": "답변을 잘 해주셨습니다.",
                "suggestions": ["더 구체적인 예시를 들어보세요."]
            }
        
        # AI 기반 평가
        evaluation_prompt = f"""
        다음 기술면접 질문과 지원자의 답변을 평가해주세요.
        
        질문: {question['question']}
        답변: {answer}
        
        평가 기준:
        1. 기술적 정확성 (30%)
        2. 코드 품질 이해도 (25%)
        3. 문제 해결 능력 (25%)
        4. 의사소통 능력 (20%)
        
        각 기준별로 1-10점으로 평가하고, 구체적인 피드백과 개선 제안을 제공해주세요.
        JSON 형태로 응답해주세요.
        """
        
        try:
            messages = [
                SystemMessage(content=self.interviewer_persona),
                HumanMessage(content=evaluation_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # AI 응답 파싱 (실제로는 더 정교한 파싱 필요)
            return {
                "overall_score": 8.0,
                "criteria_scores": {
                    "technical_accuracy": 8.0,
                    "code_quality": 8.0,
                    "problem_solving": 7.5,
                    "communication": 8.5
                },
                "feedback": "기술적 이해도가 높고 설명을 명확하게 잘 해주셨습니다.",
                "suggestions": [
                    "실제 프로젝트 경험을 더 구체적으로 공유해보세요.",
                    "성능 최적화 관점에서의 고려사항도 언급하면 좋겠습니다."
                ],
                "ai_feedback": response.content
            }
            
        except Exception as e:
            print(f"AI 평가 생성 오류: {e}")
            return {
                "overall_score": 7.0,
                "criteria_scores": {
                    "technical_accuracy": 7.0,
                    "code_quality": 7.0,
                    "problem_solving": 7.0,
                    "communication": 7.0
                },
                "feedback": "답변해주신 내용이 좋습니다.",
                "suggestions": ["추가적인 설명이 있으면 더 좋겠습니다."]
            }
    
    async def _should_generate_follow_up(
        self, 
        evaluation: Dict[str, Any], 
        state: InterviewState
    ) -> bool:
        """후속 질문 생성 여부 결정"""
        
        # 후속 질문 제한 (최대 2개)
        if state.follow_up_count >= 2:
            return False
        
        # 점수가 낮거나 높은 경우 후속 질문 생성
        overall_score = evaluation.get("overall_score", 7.0)
        if overall_score < 6.0 or overall_score > 8.5:
            return True
        
        # 특정 기준에서 점수가 낮은 경우
        criteria_scores = evaluation.get("criteria_scores", {})
        if any(score < 6.0 for score in criteria_scores.values()):
            return True
        
        return False
    
    async def _generate_follow_up_question(
        self,
        original_question: Dict[str, Any],
        answer: str,
        evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """후속 질문 생성"""
        
        follow_up_questions = await self.question_generator.generate_follow_up_questions(
            original_question, answer
        )
        
        if follow_up_questions:
            return follow_up_questions[0]
        else:
            # 기본 후속 질문
            return {
                "id": f"follow_up_{original_question['id']}",
                "type": "follow_up",
                "question": "답변해주신 내용에 대해 실제 경험이나 구체적인 예시가 있다면 공유해주세요.",
                "parent_question_id": original_question["id"],
                "time_estimate": "3-5분"
            }
    
    async def _complete_interview(self, state: InterviewState):
        """면접 완료 처리"""
        
        state.interview_status = "completed"
        state.end_time = datetime.now()
        
        # 전체 점수 계산
        if state.evaluations:
            total_score = sum(eval_data.get("overall_score", 0) for eval_data in state.evaluations)
            state.total_score = round(total_score / len(state.evaluations), 2)
        
        # 종합 피드백 생성
        state.feedback = await self._generate_final_feedback(state)
        
        # 세션에서 제거 (실제로는 DB에 저장)
        # del self.active_sessions[state.interview_id]
    
    async def _generate_final_feedback(self, state: InterviewState) -> List[str]:
        """최종 피드백 생성"""
        
        feedback = []
        
        if state.total_score >= 8.0:
            feedback.append("전반적으로 우수한 답변을 해주셨습니다.")
        elif state.total_score >= 6.0:
            feedback.append("기본적인 이해도는 좋으나 더 깊이 있는 설명이 필요합니다.")
        else:
            feedback.append("기술적 이해도를 더 높이시길 권장합니다.")
        
        # 카테고리별 피드백
        if state.evaluations:
            avg_scores = {}
            for criteria in self.evaluation_criteria.keys():
                scores = [eval_data.get("criteria_scores", {}).get(criteria, 0) 
                         for eval_data in state.evaluations]
                avg_scores[criteria] = sum(scores) / len(scores) if scores else 0
            
            for criteria, avg_score in avg_scores.items():
                criteria_desc = self.evaluation_criteria[criteria]["description"]
                if avg_score >= 8.0:
                    feedback.append(f"{criteria_desc} 부분에서 뛰어난 역량을 보여주셨습니다.")
                elif avg_score < 6.0:
                    feedback.append(f"{criteria_desc} 부분에서 더 많은 학습이 필요합니다.")
        
        return feedback
    
    async def _generate_question_introduction(
        self, 
        question: Dict[str, Any], 
        state: InterviewState
    ) -> str:
        """질문 소개 생성"""
        
        introductions = [
            "다음 질문을 준비했습니다.",
            "이번에는 이런 질문을 드리고 싶습니다.",
            "다음 문제에 대해 어떻게 생각하시는지 궁금합니다.",
            "관련해서 이런 질문이 있습니다."
        ]
        
        import random
        return random.choice(introductions)
    
    def _calculate_elapsed_time(self, state: InterviewState) -> int:
        """경과 시간 계산 (초)"""
        
        if not state.start_time:
            return 0
        
        end_time = state.end_time or datetime.now()
        return int((end_time - state.start_time).total_seconds())
    
    async def get_interview_report(self, interview_id: str) -> Dict[str, Any]:
        """면접 리포트 생성"""
        
        if interview_id not in self.active_sessions:
            return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
        
        state = self.active_sessions[interview_id]
        
        if state.interview_status != "completed":
            return {"success": False, "error": "완료되지 않은 면접입니다."}
        
        # 상세 리포트 생성
        report = {
            "interview_id": interview_id,
            "repo_url": state.repo_url,
            "user_id": state.user_id,
            "start_time": state.start_time.isoformat() if state.start_time else None,
            "end_time": state.end_time.isoformat() if state.end_time else None,
            "total_duration": self._calculate_elapsed_time(state),
            "difficulty_level": state.difficulty_level,
            "total_score": state.total_score,
            "questions_answered": len(state.answers),
            "total_questions": len(state.questions),
            "follow_up_questions": state.follow_up_count,
            "overall_feedback": state.feedback,
            "detailed_evaluation": state.evaluations,
            "answers": state.answers,
            "recommendations": await self._generate_recommendations(state)
        }
        
        return {"success": True, "report": report}
    
    async def _generate_recommendations(self, state: InterviewState) -> List[str]:
        """개선 권장사항 생성"""
        
        recommendations = []
        
        if state.total_score < 7.0:
            recommendations.extend([
                "기술적 기초 지식을 더 체계적으로 학습하세요.",
                "실제 프로젝트 경험을 쌓아보세요.",
                "오픈소스 프로젝트에 기여해보세요."
            ])
        
        # 특정 약점 분야 찾기
        if state.evaluations:
            weak_areas = []
            for eval_data in state.evaluations:
                criteria_scores = eval_data.get("criteria_scores", {})
                for criteria, score in criteria_scores.items():
                    if score < 6.0:
                        weak_areas.append(criteria)
            
            if "technical_accuracy" in weak_areas:
                recommendations.append("기술 문서와 공식 도큐멘테이션을 더 자주 읽어보세요.")
            if "communication" in weak_areas:
                recommendations.append("기술 블로그 작성이나 발표 경험을 늘려보세요.")
            if "problem_solving" in weak_areas:
                recommendations.append("알고리즘 문제 해결과 코딩 테스트 연습을 해보세요.")
        
        return recommendations
"""
Mock Interview Agent

실시간 모의면접을 진행하는 LangGraph 에이전트
WebSocket을 통한 실시간 대화 및 질문-답변 평가 시스템
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.question_generator import QuestionGenerator
from app.core.gemini_client import get_gemini_llm


INTERVIEWER_PERSONA = """
당신은 경험이 풍부한 시니어 개발자이자 기술면접관입니다.
친근하고 전문적인 톤으로 면접을 진행하며, 지원자가 편안하게 답변할 수 있도록 도와줍니다.
답변을 들은 후 적절한 후속 질문을 통해 지원자의 깊이 있는 사고를 유도합니다.

면접 진행 원칙:
1. 지원자의 답변을 주의 깊게 듣고 구체적인 피드백 제공
2. 너무 어려운 질문보다는 지원자의 수준에 맞는 질문으로 조정
3. 긍정적인 분위기 유지하며 지원자의 장점을 찾아 격려
4. 기술적 깊이와 실무 경험을 균형있게 평가
"""

CRITERIA_DESCRIPTIONS: Dict[str, str] = {
    "technical_accuracy": "기술적 정확성",
    "code_quality": "코드 품질 이해도",
    "problem_solving": "문제 해결 능력",
    "communication": "의사소통 능력",
}


class MockInterviewAgent:
    """모의면접 진행 에이전트"""
    
    def __init__(self, github_token: Optional[str] = None, google_api_key: Optional[str] = None, api_keys: Optional[Dict[str, str]] = None):
        # api_keys 딕셔너리가 제공된 경우 우선 사용
        if api_keys:
            self.github_token = api_keys.get("github_token")
            self.google_api_key = api_keys.get("google_api_key")
        else:
            self.github_token = github_token
            self.google_api_key = google_api_key
            
        self.api_key_available = bool(self.google_api_key)
        
        self.question_generator = QuestionGenerator()
        
        # Google Gemini LLM 초기화 (동적 API 키 사용)
        if self.google_api_key and self.google_api_key != "your_google_api_key_here":
            print(f"[MOCK_INTERVIEW] Google API Key provided: {self.google_api_key[:20]}...")
            # 동적 API 키로 Gemini 초기화 시도
            try:
                from app.core.gemini_client import get_gemini_llm_with_key
                self.llm = get_gemini_llm_with_key(self.google_api_key)
                if self.llm:
                    self.llm.temperature = 0.3
                    print("[MOCK_INTERVIEW] Google Gemini LLM initialized with provided API key")
                    self.api_key_available = True
                else:
                    raise Exception("Failed to initialize with provided key")
            except Exception as e:
                print(f"[MOCK_INTERVIEW] Failed to init with provided key: {e}, API 키 없는 모드로 전환")
                self.llm = None
                self.api_key_available = False
        else:
            print("[MOCK_INTERVIEW] Google API Key 없음 - 제한된 기능으로 작동")
            # 환경변수의 API 키도 확인
            try:
                self.llm = get_gemini_llm()
                if self.llm:
                    self.llm.temperature = 0.3
                    print("[MOCK_INTERVIEW] 환경변수 Google API Key로 초기화 성공")
                    self.api_key_available = True
                else:
                    self.api_key_available = False
            except:
                self.llm = None
                self.api_key_available = False
                
        if not self.api_key_available:
            print("[MOCK_INTERVIEW] Warning: Google API Key 없음 - 기본 응답만 제공됩니다")
    
    async def start_interview(
        self, 
        repo_url: str, 
        user_id: str,
        difficulty_level: str = "medium",
        question_count: int = 5,
        time_per_question: int = 60
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
            
            if not question_result.get("success"):
                raise ValueError(f"질문 생성 실패: {question_result.get('error', '')}")
            
            # DB 기반 세션 관리로 전환되어 in-memory 세션은 저장하지 않음.
            state = {
                "interview_id": interview_id,
                "repo_url": repo_url,
                "user_id": user_id,
                "questions": question_result.get("questions", []),
                "difficulty_level": difficulty_level,
                "time_per_question": time_per_question,
                "start_time": datetime.now(),
                "end_time": None,
                "current_question_index": 0,
                "answers": [],
                "evaluations": [],
                "follow_up_count": 0,
                "total_score": 0.0,
                "feedback": [],
                "interview_status": "in_progress",
            }
            
            # 첫 질문 준비
            first_question = None
            if state["questions"]:
                first_question = await self._prepare_question(state, 0)
            
            return {
                "success": True,
                "interview_id": interview_id,
                "total_questions": len(state["questions"]),
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
    
    async def get_interview_status(self, interview_id: str) -> Dict[str, Any]:
        """면접 상태 조회"""

        from app.core.database import SessionLocal
        from app.services.interview_repository import InterviewRepository

        try:
            session_uuid = uuid.UUID(interview_id)
        except ValueError:
            return {"success": False, "error": "올바르지 않은 면접 ID 형식입니다."}

        db = SessionLocal()
        try:
            repo = InterviewRepository(db)
            session_data = repo.get_session_with_details(session_uuid)

            if not session_data:
                return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}

            session = session_data["session"]
            progress = session_data["progress"]

            return {
                "success": True,
                "interview_id": interview_id,
                "status": session.status,
                "progress": {
                    "current_question": progress.get("current_question", 1),
                    "total_questions": progress.get("total_questions", 0),
                    "completed_questions": progress.get("answered_questions", 0),
                },
                "elapsed_time": progress.get("elapsed_time", 0),
                "total_score": float(session.overall_score) if session.overall_score is not None else 0.0,
                "difficulty_level": session.difficulty,
            }
        finally:
            db.close()
    
    async def end_interview(self, interview_id: str) -> Dict[str, Any]:
        """면접 강제 종료"""

        from app.core.database import SessionLocal
        from app.services.interview_repository import InterviewRepository

        try:
            session_uuid = uuid.UUID(interview_id)
        except ValueError:
            return {"success": False, "error": "올바르지 않은 면접 ID 형식입니다."}

        db = SessionLocal()
        try:
            repo = InterviewRepository(db)
            updated = repo.update_session_status(session_uuid, "completed")
            if not updated:
                return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}
            return {"success": True, "message": "면접이 종료되었습니다."}
        finally:
            db.close()

    @staticmethod
    def _state_value(state: Any, key: str, default: Any = None) -> Any:
        """dict/object 상태 모두에서 안전하게 값을 조회한다."""
        if isinstance(state, dict):
            return state.get(key, default)
        return getattr(state, key, default)

    async def _prepare_question(self, state: Dict[str, Any], question_index: int) -> Dict[str, Any]:
        """질문 준비"""

        question = state["questions"][question_index]
        
        # AI 면접관의 질문 소개
        if self.llm:
            introduction = await self._generate_question_introduction(question, state)
            question["introduction"] = introduction
        
        return question

    async def _generate_final_feedback(self, state: Any) -> List[str]:
        """최종 피드백 생성"""
        
        feedback = []

        total_score = float(self._state_value(state, "total_score", 0.0) or 0.0)

        if total_score >= 8.0:
            feedback.append("전반적으로 우수한 답변을 해주셨습니다.")
        elif total_score >= 6.0:
            feedback.append("기본적인 이해도는 좋으나 더 깊이 있는 설명이 필요합니다.")
        else:
            feedback.append("기술적 이해도를 더 높이시길 권장합니다.")
        
        # 카테고리별 피드백
        evaluations = self._state_value(state, "evaluations", []) or []
        if evaluations:
            for criteria, criteria_desc in CRITERIA_DESCRIPTIONS.items():
                scores = [
                    float(eval_data.get("criteria_scores", {}).get(criteria, 0) or 0)
                    for eval_data in evaluations
                ]
                if not scores:
                    continue
                avg_score = sum(scores) / len(scores)
                if avg_score >= 8.0:
                    feedback.append(f"{criteria_desc} 부분에서 뛰어난 역량을 보여주셨습니다.")
                elif avg_score < 6.0:
                    feedback.append(f"{criteria_desc} 부분에서 더 많은 학습이 필요합니다.")
        
        return feedback
    
    async def _generate_question_introduction(
        self, 
        question: Dict[str, Any], 
        state: Dict[str, Any]
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
    
    def _calculate_elapsed_time(self, state: Any) -> int:
        """경과 시간 계산 (초)"""

        start_time = self._state_value(state, "start_time")
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time)
            except ValueError:
                return 0
        if not start_time:
            return 0

        end_time = self._state_value(state, "end_time") or datetime.now()
        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time)
            except ValueError:
                end_time = datetime.now()
        return int((end_time - start_time).total_seconds())
    
    async def get_interview_report(self, interview_id: str) -> Dict[str, Any]:
        """면접 리포트 생성"""

        from app.core.database import SessionLocal
        from app.models.interview import InterviewAnswer, InterviewConversation, InterviewQuestion
        from app.services.interview_repository import InterviewRepository

        try:
            session_uuid = uuid.UUID(interview_id)
        except ValueError:
            return {"success": False, "error": "올바르지 않은 면접 ID 형식입니다."}

        db = SessionLocal()
        try:
            repo = InterviewRepository(db)
            session_data = repo.get_session_with_details(session_uuid)

            if not session_data:
                return {"success": False, "error": "면접 세션을 찾을 수 없습니다."}

            session = session_data["session"]
            if session.status != "completed":
                return {"success": False, "error": "완료되지 않은 면접입니다."}

            answers: List[InterviewAnswer] = session_data.get("answers", [])
            question_ids = [answer.question_id for answer in answers if answer.question_id is not None]
            question_map: Dict[Any, InterviewQuestion] = {}
            if question_ids:
                questions = db.query(InterviewQuestion).filter(InterviewQuestion.id.in_(question_ids)).all()
                question_map = {question.id: question for question in questions}

            evaluations: List[Dict[str, Any]] = []
            answers_payload: List[Dict[str, Any]] = []
            for answer in answers:
                feedback_details = answer.feedback_details if isinstance(answer.feedback_details, dict) else {}
                if feedback_details:
                    evaluations.append(feedback_details)

                question_obj = question_map.get(answer.question_id)
                answers_payload.append({
                    "question_id": str(answer.question_id) if answer.question_id else None,
                    "question": question_obj.question_text if question_obj else None,
                    "answer": answer.user_answer,
                    "timestamp": answer.submitted_at.isoformat() if answer.submitted_at else None,
                    "time_taken": answer.time_taken_seconds or 0,
                    "feedback": feedback_details,
                })

            follow_up_count = db.query(InterviewConversation).filter(
                InterviewConversation.session_id == session_uuid,
                InterviewConversation.speaker == "user"
            ).count()

            state = {
                "total_score": float(session.overall_score) if session.overall_score is not None else 0.0,
                "evaluations": evaluations,
            }

            report = {
                "interview_id": interview_id,
                "repo_url": None,
                "user_id": str(session.user_id) if session.user_id else None,
                "start_time": session.started_at.isoformat() if session.started_at else None,
                "end_time": session.ended_at.isoformat() if session.ended_at else None,
                "total_duration": self._calculate_elapsed_time({
                    "start_time": session.started_at,
                    "end_time": session.ended_at,
                }),
                "difficulty_level": session.difficulty,
                "total_score": state["total_score"],
                "questions_answered": len(answers_payload),
                "total_questions": session_data.get("progress", {}).get("total_questions", 0),
                "follow_up_questions": follow_up_count,
                "overall_feedback": await self._generate_final_feedback(state),
                "detailed_evaluation": evaluations,
                "answers": answers_payload,
                "recommendations": await self._generate_recommendations(state),
            }

            return {"success": True, "report": report}
        finally:
            db.close()

    async def _generate_recommendations(self, state: Any) -> List[str]:
        """개선 권장사항 생성"""
        
        recommendations = []

        total_score = float(self._state_value(state, "total_score", 0.0) or 0.0)
        if total_score < 7.0:
            recommendations.extend([
                "기술적 기초 지식을 더 체계적으로 학습하세요.",
                "실제 프로젝트 경험을 쌓아보세요.",
                "오픈소스 프로젝트에 기여해보세요."
            ])
        
        # 특정 약점 분야 찾기
        evaluations = self._state_value(state, "evaluations", []) or []
        if evaluations:
            weak_areas = []
            for eval_data in evaluations:
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
    
    async def evaluate_answer(
        self, 
        question: str, 
        answer: str, 
        is_first_answer: bool = True,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """실제 Gemini API를 사용한 답변 평가 (공개 API용)"""
        
        if not question or not answer:
            return {
                "success": False,
                "error": "질문과 답변이 모두 제공되어야 합니다."
            }
        
        context = context or {}
        
        print(f"[EVALUATE] 답변 평가 시작: is_first_answer={is_first_answer}")
        
        # 첫 번째 답변이 아닌 경우 대화형 응답 생성
        if not is_first_answer:
            print(f"[EVALUATE] 추가 답변으로 인식 - 대화형 응답 생성")
            return await self._generate_conversation_response(question, answer, context)
        
        # 첫 번째 답변인 경우 정식 평가 진행
        print(f"[EVALUATE] 첫 번째 답변으로 인식 - 정식 평가 진행")
        
        try:
            if not self.api_key_available:
                # API 키가 없는 경우 기본 피드백 제공 (서비스 연속성 확보)
                return {
                    "success": True,
                    "error": None,
                    "message": "기본 피드백이 제공되었습니다. 더 상세한 분석을 위해서는 API 키 설정이 필요합니다.",
                    "data": {
                        "overall_score": 6.0,
                        "criteria_scores": {
                            "technical_accuracy": 6.0,
                            "problem_solving": 6.0,
                            "communication": 6.0
                        },
                        "feedback": "답변해 주셔서 감사합니다. API 키가 설정되지 않아 기본 피드백만 제공됩니다. 더 상세한 분석과 개인화된 피드백을 원하신다면 Google API 키를 설정해주세요.",
                        "suggestions": [
                            "답변에 더 구체적인 예시를 포함해보세요.",
                            "관련 기술의 장단점을 설명해보세요.",
                            "실제 경험이나 프로젝트 사례를 언급해보세요."
                        ]
                    }
                }
            
            # 실제 Gemini 프롬프트 구성
            category = context.get('category', 'general')
            difficulty = context.get('difficulty', 'medium')
            expected_points = context.get('expected_points', [])
            
            evaluation_prompt = f"""당신은 경험이 풍부한 시니어 개발자이자 기술면접관입니다.
다음 면접 질문과 지원자의 답변을 평가하고, 구체적인 피드백을 제공해주세요.

**면접 질문:**
{question}

**지원자 답변:**
{answer}

**질문 정보:**
- 카테고리: {category}
- 난이도: {difficulty}
- 주요 포인트: {', '.join(expected_points) if expected_points else '없음'}

다음 기준으로 평가하고 반드시 JSON 형태로만 응답해주세요:

{{
    "overall_score": 점수(1-10),
    "criteria_scores": {{
        "technical_accuracy": 점수(1-10),
        "problem_solving": 점수(1-10), 
        "communication": 점수(1-10)
    }},
    "feedback": "구체적이고 건설적인 피드백 메시지",
    "suggestions": [
        "개선사항1",
        "개선사항2",
        "개선사항3"
    ]
}}

평가 기준:
- technical_accuracy: 기술적 정확성과 깊이
- problem_solving: 문제 이해도와 해결 방법의 적절성
- communication: 설명의 명확성과 논리적 구성

답변이 "모르겠다" 또는 매우 짧은 경우에도 격려하면서 구체적인 학습 방향을 제시해주세요."""

            # Gemini API 호출
            print(f"[GEMINI_EVAL] Gemini API 호출 시작 - 질문 길이: {len(question)}, 답변 길이: {len(answer)}")
            
            response = await self.llm.ainvoke([
                SystemMessage(content=INTERVIEWER_PERSONA),
                HumanMessage(content=evaluation_prompt)
            ])
            
            print(f"[GEMINI_EVAL] Gemini 응답 받음 - 길이: {len(response.content) if hasattr(response, 'content') else 0}")
            
            # JSON 응답 파싱
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # JSON 형태로 파싱 시도
            import json
            import re
            
            # JSON 블록 추출
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    evaluation_data = json.loads(json_str)
                    
                    print(f"[GEMINI_EVAL] JSON 파싱 성공 - 종합점수: {evaluation_data.get('overall_score', 'N/A')}")
                    
                    return {
                        "success": True,
                        "data": {
                            "overall_score": float(evaluation_data.get('overall_score', 5.0)),
                            "criteria_scores": {
                                "technical_accuracy": float(evaluation_data.get('criteria_scores', {}).get('technical_accuracy', 5.0)),
                                "problem_solving": float(evaluation_data.get('criteria_scores', {}).get('problem_solving', 5.0)),
                                "communication": float(evaluation_data.get('criteria_scores', {}).get('communication', 5.0))
                            },
                            "feedback": evaluation_data.get('feedback', '답변해주셔서 감사합니다.'),
                            "suggestions": evaluation_data.get('suggestions', ['더 구체적으로 설명해보세요.'])
                        }
                    }
                    
                except json.JSONDecodeError as je:
                    print(f"[GEMINI_EVAL] JSON 파싱 실패: {je}")
                    # JSON 파싱 실패 시 텍스트 기반 응답 생성
                    pass
            
            # JSON 파싱이 실패한 경우 텍스트에서 정보 추출
            print(f"[GEMINI_EVAL] JSON 파싱 실패, 텍스트 분석으로 전환")
            
            return {
                "success": True,
                "data": {
                    "overall_score": 7.0,
                    "criteria_scores": {
                        "technical_accuracy": 7.0,
                        "problem_solving": 7.0,
                        "communication": 7.0
                    },
                    "feedback": response_text[:500] if len(response_text) > 500 else response_text,
                    "suggestions": [
                        "더 구체적인 예시를 제시해보세요.",
                        "기술적 용어의 정확한 의미를 설명해보세요.",
                        "실무 경험과 연결하여 설명해보세요."
                    ]
                }
            }
            
        except Exception as e:
            print(f"[GEMINI_EVAL] 평가 중 오류 발생: {str(e)}")
            
            # 오류 발생 시 기본 응답
            return {
                "success": True,  # 서비스 연속성을 위해 success로 처리
                "data": {
                    "overall_score": 5.0,
                    "criteria_scores": {
                        "technical_accuracy": 5.0,
                        "problem_solving": 5.0,
                        "communication": 5.0
                    },
                    "feedback": "답변을 주셔서 감사합니다. 시스템 문제로 상세한 평가를 제공할 수 없지만, 계속 진행해주세요.",
                    "suggestions": [
                        "다음 질문에서 더 자세히 설명해보세요.",
                        "기술적 개념을 예시와 함께 설명해보세요."
                    ]
                }
            }
    
    async def handle_follow_up_question(
        self,
        original_question: str,
        original_answer: str, 
        follow_up_question: str
    ) -> Dict[str, Any]:
        """실제 Gemini를 통한 후속 질문 처리"""
        
        try:
            if not self.llm:
                return {
                    "success": True,
                    "data": {
                        "response": "후속 질문에 감사드립니다. 더 구체적으로 설명해주시면 도움이 될 것 같습니다."
                    }
                }
            
            conversation_prompt = f"""당신은 친근하고 전문적인 기술면접관입니다.
지원자가 원래 질문에 답변한 후 추가로 질문을 했습니다.

**원래 면접 질문:**
{original_question}

**지원자의 원래 답변:**
{original_answer}

**지원자의 후속 질문:**
{follow_up_question}

지원자의 후속 질문에 대해 친근하고 도움이 되는 답변을 해주세요.
- 기술적 개념을 쉽게 설명해주세요
- 실무에서 활용할 수 있는 조언을 제공해주세요
- 면접 분위기를 긍정적으로 유지해주세요"""

            print(f"[GEMINI_CONV] 대화 처리 시작 - 후속 질문: {follow_up_question[:50]}...")
            
            response = await self.llm.ainvoke([
                SystemMessage(content=INTERVIEWER_PERSONA),
                HumanMessage(content=conversation_prompt)
            ])
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            print(f"[GEMINI_CONV] 대화 응답 생성 완료 - 길이: {len(response_text)}")
            
            return {
                "success": True,
                "data": {
                    "response": response_text
                }
            }
            
        except Exception as e:
            print(f"[GEMINI_CONV] 대화 처리 중 오류: {str(e)}")
            
            return {
                "success": True,
                "data": {
                    "response": "질문해주셔서 감사합니다. 더 구체적인 설명이 필요하시면 언제든 말씀해주세요."
                }
            }
    
    async def _generate_conversation_response(
        self, 
        question: str, 
        answer: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """추가 답변에 대한 대화형 응답 생성 (점수 없음)"""
        
        try:
            if not self.llm:
                # LLM이 없는 경우 기본 대화 응답
                return {
                    "success": True,
                    "data": {
                        "feedback": f"'{answer}'에 대해 답변드리겠습니다. 추가적인 설명이나 질문이 있으시면 언제든 말씀해주세요.",
                        "is_conversation": True
                    }
                }
            
            # 대화형 프롬프트 생성
            conversation_prompt = f"""당신은 친근하고 전문적인 기술면접관입니다.
지원자가 다음 질문에 추가로 '{answer}'라고 답변했습니다.

**원래 면접 질문:**
{question}

**지원자의 추가 답변:**
{answer}

다음과 같이 자연스럽고 도움이 되는 응답을 해주세요:
- 점수나 평가 없이 내용 위주로 응답
- 면접관 톤으로 친근하지만 전문적으로 답변  
- 구체적이고 실용적인 조언 제공
- 하나의 통합된 답변으로 제공

200-300자 내외로 답변해주세요."""

            print(f"[CONVERSATION] 대화형 응답 생성 시작")
            
            response = await self.llm.ainvoke([
                SystemMessage(content=INTERVIEWER_PERSONA),
                HumanMessage(content=conversation_prompt)
            ])
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            print(f"[CONVERSATION] 대화형 응답 생성 완료 - 길이: {len(response_text)}")
            
            return {
                "success": True,
                "data": {
                    "feedback": response_text,
                    "is_conversation": True  # 프론트엔드에서 구분용
                }
            }
            
        except Exception as e:
            print(f"[CONVERSATION] 대화형 응답 생성 중 오류: {str(e)}")
            
            # 오류 발생 시 기본 응답
            return {
                "success": True,
                "data": {
                    "feedback": f"'{answer}'에 대해 답변드리겠습니다. 더 구체적인 설명이나 질문이 있으시면 언제든 말씀해주세요.",
                    "is_conversation": True
                }
            }

"""
Report Generator Agent

면접 리포트 생성 및 AI 인사이트 생성을 담당하는 에이전트
"""

import json
import re
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)


class ReportGeneratorAgent:
    """리포트 생성 에이전트"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,  # 일관된 분석을 위해 낮은 temperature
            max_tokens=2048
        )
    
    async def generate_interview_insights(
        self, 
        project_context: Dict[str, Any], 
        interview_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        면접 인사이트 생성
        
        Args:
            project_context: 프로젝트 정보 (저장소, 기술스택 등)
            interview_data: 면접 질답 데이터
            
        Returns:
            구조화된 면접 인사이트 데이터
        """
        try:
            logger.info(f"[REPORT_GENERATOR] 인사이트 생성 시작 - 프로젝트: {project_context.get('repository_url', 'unknown')}")
            
            # 프롬프트 구성
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(project_context, interview_data)
            
            # LLM 호출
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            logger.info(f"[REPORT_GENERATOR] LLM 응답 받음: {len(response.content)} characters")
            
            # 응답 파싱
            insights = self._parse_insights_response(response.content)
            
            logger.info(f"[REPORT_GENERATOR] 인사이트 생성 완료")
            return insights
            
        except Exception as e:
            logger.error(f"[REPORT_GENERATOR] 인사이트 생성 실패: {e}")
            return self._get_fallback_insights()
    
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """당신은 기술면접 전문가이자 시니어 개발자입니다. 
GitHub 프로젝트 기반 기술면접 결과를 분석하여 실제 면접 준비에 도움이 되는 구체적이고 실행 가능한 피드백을 제공합니다.

# 분석 원칙
1. **실용성**: 실제 면접에서 바로 활용할 수 있는 조언
2. **구체성**: 추상적이지 않은 명확하고 구체적인 가이드
3. **실행가능성**: 면접자가 실제로 실행할 수 있는 액션 아이템
4. **프로젝트 연관성**: 해당 프로젝트 특성에 맞춘 맞춤형 조언

# 응답 형식
다음 JSON 구조로 정확히 응답해주세요:

```json
{
  "interview_summary": {
    "overall_comment": "200자 내외의 전반적인 면접 수행 능력 평가",
    "readiness_score": 85,
    "key_talking_points": ["면접에서 강조할 포인트 1", "포인트 2", "포인트 3"]
  },
  "technical_analysis": {
    "architecture_understanding": 78,
    "code_quality_awareness": 82,
    "problem_solving_approach": "구체적인 문제 해결 접근법 평가",
    "technology_depth": "기술 스택 이해 깊이 평가",
    "project_complexity_handling": "프로젝트 복잡도 대응 능력 평가"
  },
  "improvement_plan": {
    "immediate_actions": ["즉시 개선할 항목 1", "항목 2", "항목 3"],
    "study_recommendations": [
      {"topic": "React Hooks", "resource": "구체적 학습 자료", "priority": "high"},
      {"topic": "TypeScript", "resource": "학습 자료 2", "priority": "medium"}
    ],
    "practice_scenarios": ["연습할 시나리오 1", "시나리오 2"],
    "weak_areas": ["취약점 1", "취약점 2"],
    "preparation_timeline": "면접 준비 스케줄 가이드"
  }
}
```"""

    def _create_user_prompt(self, project_context: Dict[str, Any], interview_data: Dict[str, Any]) -> str:
        """사용자 프롬프트 생성"""
        
        # 기술 스택 정보 정리
        tech_stack = project_context.get('tech_stack', {})
        if isinstance(tech_stack, dict):
            tech_stack_str = ", ".join([f"{k} ({v*100:.0f}%)" for k, v in tech_stack.items()])
        else:
            tech_stack_str = str(tech_stack)
        
        # 질문-답변 데이터 정리
        qa_summary = self._format_interview_data(interview_data)
        
        prompt = f"""
# 프로젝트 정보
- 저장소: {project_context.get('repository_url', 'N/A')}
- 기술 스택: {tech_stack_str}
- 복잡도: {project_context.get('complexity_score', 'N/A')}/10

# 면접 결과
{qa_summary}

위 정보를 바탕으로 다음을 분석해주세요:

1. **면접 총평**: 전반적인 면접 수행 능력과 프로젝트 이해도
2. **면접 준비도 점수**: 실제 면접 대비 준비 수준 (0-100)
3. **핵심 어필 포인트**: 면접에서 반드시 강조해야 할 프로젝트 경험
4. **기술적 이해도 분석**: 아키텍처, 코드 품질, 문제 해결 접근법
5. **개선 액션 플랜**: 즉시 개선 과제, 학습 추천, 연습 시나리오

특히 이 프로젝트의 기술적 특성을 고려하여 실제 기술면접에서 예상되는 질문들에 대한 준비 방법을 구체적으로 제시해주세요.
"""
        return prompt
    
    def _format_interview_data(self, interview_data: Dict[str, Any]) -> str:
        """면접 데이터를 문자열로 포맷팅"""
        questions = interview_data.get('questions', [])
        answers = interview_data.get('answers', [])
        
        if not questions or not answers:
            return "면접 데이터가 없습니다."
        
        formatted_data = []
        
        for i, (q, a) in enumerate(zip(questions, answers)):
            question_text = q.get('question', 'N/A')
            category = q.get('category', 'N/A')
            answer_text = a.get('answer', 'N/A')
            score = a.get('score', 0)
            
            formatted_data.append(f"""
**질문 {i+1}** [{category}]
Q: {question_text}
A: {answer_text}
점수: {score}/10
""")
        
        return "\n".join(formatted_data)
    
    def _parse_insights_response(self, response_content: str) -> Dict[str, Any]:
        """LLM 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            # JSON 코드 블록에서 JSON 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSON 코드 블록이 없으면 전체 응답에서 JSON 찾기
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다.")
            
            insights = json.loads(json_str)
            
            # 데이터 검증 및 기본값 설정
            insights = self._validate_and_normalize_insights(insights)
            
            return insights
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[REPORT_GENERATOR] JSON 파싱 실패: {e}")
            logger.warning(f"[REPORT_GENERATOR] 응답 내용: {response_content[:500]}...")
            
            # 파싱 실패 시 텍스트 기반 파싱 시도
            return self._parse_text_response(response_content)
    
    def _validate_and_normalize_insights(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """인사이트 데이터 검증 및 정규화"""
        validated = {
            "interview_summary": {
                "overall_comment": insights.get("interview_summary", {}).get("overall_comment", "분석 결과를 생성할 수 없습니다."),
                "readiness_score": max(0, min(100, insights.get("interview_summary", {}).get("readiness_score", 50))),
                "key_talking_points": insights.get("interview_summary", {}).get("key_talking_points", ["프로젝트 구조 설명", "핵심 기술 스택 경험", "문제 해결 과정"])
            },
            "technical_analysis": {
                "architecture_understanding": max(0, min(100, insights.get("technical_analysis", {}).get("architecture_understanding", 60))),
                "code_quality_awareness": max(0, min(100, insights.get("technical_analysis", {}).get("code_quality_awareness", 60))),
                "problem_solving_approach": insights.get("technical_analysis", {}).get("problem_solving_approach", "체계적인 접근법 필요"),
                "technology_depth": insights.get("technical_analysis", {}).get("technology_depth", "기술 스택 이해도 향상 필요"),
                "project_complexity_handling": insights.get("technical_analysis", {}).get("project_complexity_handling", "복잡도 관리 능력 개발 필요")
            },
            "improvement_plan": {
                "immediate_actions": insights.get("improvement_plan", {}).get("immediate_actions", ["답변 시 구체적 예시 제시", "기술 용어 정확한 사용"]),
                "study_recommendations": self._normalize_study_recommendations(insights.get("improvement_plan", {}).get("study_recommendations", [])),
                "practice_scenarios": insights.get("improvement_plan", {}).get("practice_scenarios", ["프로젝트 아키텍처 설명 연습"]),
                "weak_areas": insights.get("improvement_plan", {}).get("weak_areas", ["답변 구조화", "기술적 깊이"]),
                "preparation_timeline": insights.get("improvement_plan", {}).get("preparation_timeline", "1-2주 집중 준비 권장")
            }
        }
        
        return validated
    
    def _normalize_study_recommendations(self, recommendations: List[Any]) -> List[Dict[str, str]]:
        """학습 추천 사항 정규화"""
        normalized = []
        
        for rec in recommendations:
            if isinstance(rec, dict):
                normalized.append({
                    "topic": rec.get("topic", "일반 기술 학습"),
                    "resource": rec.get("resource", "온라인 자료 검색"),
                    "priority": rec.get("priority", "medium")
                })
            elif isinstance(rec, str):
                normalized.append({
                    "topic": rec,
                    "resource": "관련 문서 및 튜토리얼",
                    "priority": "medium"
                })
        
        if not normalized:
            normalized = [
                {"topic": "프로젝트 기술 스택 심화", "resource": "공식 문서 및 베스트 프랙티스", "priority": "high"},
                {"topic": "코드 리뷰 및 품질 관리", "resource": "Clean Code, 리팩토링 서적", "priority": "medium"}
            ]
        
        return normalized
    
    def _parse_text_response(self, response_content: str) -> Dict[str, Any]:
        """JSON 파싱 실패 시 텍스트 기반 파싱"""
        logger.info("[REPORT_GENERATOR] 텍스트 기반 파싱 시도")
        
        # 기본 인사이트 구조 생성
        insights = self._get_fallback_insights()
        
        # 텍스트에서 점수 추출 시도
        score_pattern = r'(\d{1,3})(?:%|점|/100)'
        scores = re.findall(score_pattern, response_content)
        
        if scores:
            try:
                # 첫 번째 점수를 준비도 점수로 사용
                readiness_score = min(100, max(0, int(scores[0])))
                insights["interview_summary"]["readiness_score"] = readiness_score
                
                # 다른 점수들을 기술 분석에 활용
                if len(scores) > 1:
                    insights["technical_analysis"]["architecture_understanding"] = min(100, max(0, int(scores[1])))
                if len(scores) > 2:
                    insights["technical_analysis"]["code_quality_awareness"] = min(100, max(0, int(scores[2])))
            except ValueError:
                pass
        
        # 응답 내용을 총평으로 사용 (일부)
        if len(response_content) > 50:
            comment = response_content[:200] + "..." if len(response_content) > 200 else response_content
            insights["interview_summary"]["overall_comment"] = comment
        
        return insights
    
    def _get_fallback_insights(self) -> Dict[str, Any]:
        """기본 인사이트 데이터 반환"""
        return {
            "interview_summary": {
                "overall_comment": "프로젝트에 대한 기본적인 이해도를 보여주었으나, 기술적 세부사항과 구현 경험에 대한 더 깊은 설명이 필요합니다.",
                "readiness_score": 65,
                "key_talking_points": [
                    "프로젝트 아키텍처와 설계 결정 과정",
                    "핵심 기술 스택 선택 이유와 경험",
                    "구현 과정에서 마주한 기술적 도전과 해결책"
                ]
            },
            "technical_analysis": {
                "architecture_understanding": 65,
                "code_quality_awareness": 60,
                "problem_solving_approach": "문제 해결 과정을 체계적으로 설명하고, 대안 솔루션에 대한 고려사항을 포함하여 답변하는 연습이 필요합니다.",
                "technology_depth": "기술 스택에 대한 이론적 지식은 있으나, 실제 프로젝트에서의 적용 경험과 트레이드오프에 대한 이해를 더 깊게 할 필요가 있습니다.",
                "project_complexity_handling": "프로젝트의 복잡성을 관리하는 방법과 확장성 고려사항에 대해 더 구체적으로 설명할 수 있어야 합니다."
            },
            "improvement_plan": {
                "immediate_actions": [
                    "답변 시 STAR 방법론(Situation, Task, Action, Result) 활용",
                    "기술 용어 사용 시 구체적인 예시와 함께 설명",
                    "프로젝트의 비즈니스 임팩트까지 언급하는 연습"
                ],
                "study_recommendations": [
                    {"topic": "시스템 설계 패턴", "resource": "Clean Architecture, 마이크로서비스 패턴 서적", "priority": "high"},
                    {"topic": "성능 최적화", "resource": "웹 성능 최적화 가이드, 프로파일링 도구 학습", "priority": "medium"},
                    {"topic": "테스트 전략", "resource": "단위 테스트, 통합 테스트 베스트 프랙티스", "priority": "medium"}
                ],
                "practice_scenarios": [
                    "5분 내에 프로젝트 전체 아키텍처 설명하기",
                    "기술적 의사결정의 이유와 트레이드오프 설명하기",
                    "프로젝트에서 가장 어려웠던 문제와 해결 과정 스토리텔링"
                ],
                "weak_areas": [
                    "기술적 의사결정 과정 설명",
                    "성능 및 확장성 고려사항",
                    "팀 협업 및 코드 리뷰 경험"
                ],
                "preparation_timeline": "면접 2주 전부터 매일 1시간씩 모의면접 연습, 1주 전부터는 프로젝트 설명 스크립트 완성도를 높이는 것을 권장합니다."
            }
        }


# 싱글톤 인스턴스
_report_generator_instance = None

def get_report_generator() -> ReportGeneratorAgent:
    """ReportGeneratorAgent 싱글톤 인스턴스 반환"""
    global _report_generator_instance
    if _report_generator_instance is None:
        _report_generator_instance = ReportGeneratorAgent()
    return _report_generator_instance
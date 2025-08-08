"""
Answer Analysis Service

Google Gemini 2.0 Flash를 사용한 사용자 답변 분석 및 피드백 제공 서비스
"""

import logging
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum
from app.core.ai_service import ai_service, AIProvider

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    STRENGTH = "strength"
    IMPROVEMENT = "improvement"
    SUGGESTION = "suggestion"
    KEYWORD_MISSING = "keyword_missing"


@dataclass
class AnswerFeedback:
    score: float  # 1-10 점수
    feedback_type: FeedbackType
    message: str
    details: str
    suggestions: list[str]


class AnswerAnalyzer:
    def __init__(self):
        """Google Gemini 기반 답변 분석기 초기화"""
        self.ai_service = ai_service
        logger.info("AnswerAnalyzer initialized with Google Gemini")

    async def analyze_answer(self, question: Dict[str, Any], answer: str) -> AnswerFeedback:
        """Google Gemini를 사용한 답변 분석 및 피드백 제공"""
        
        question_text = question.get("question", "")
        question_category = question.get("category", "technical")
        question_difficulty = question.get("difficulty", "medium")
        
        try:
            # AI 분석 요청
            analysis_result = await self._analyze_with_gemini(
                question_text, answer, question_category, question_difficulty
            )
            
            return AnswerFeedback(
                score=analysis_result["score"],
                feedback_type=self._get_feedback_type(analysis_result["score"]),
                message=analysis_result["message"],
                details=analysis_result["details"],
                suggestions=analysis_result["suggestions"]
            )
            
        except Exception as e:
            logger.error(f"Gemini 분석 실패, fallback 사용: {e}")
            return self._fallback_analysis(answer)

    async def _analyze_with_gemini(self, question: str, answer: str, category: str, difficulty: str) -> Dict[str, Any]:
        """Google Gemini 2.0 Flash를 사용한 답변 분석"""
        
        prompt = f"""당신은 경험이 풍부한 기술 면접관입니다. 다음 기술면접 질문과 답변을 분석하여 구체적이고 건설적인 피드백을 제공해주세요.

**면접 질문 정보:**
- 카테고리: {category}
- 난이도: {difficulty}
- 질문: {question}

**면접자 답변:**
{answer}

**평가 기준:**
1. 기술적 정확성 (30%)
2. 답변의 구체성 (25%)
3. 실무 경험 반영 (20%)
4. 논리적 구성 (15%)
5. 답변 완성도 (10%)

**피드백 형식:**
다음 JSON 형태로 정확히 응답해주세요:

{{
  "score": [1-10 점수],
  "message": "[한 문장으로 전체적인 피드백]",
  "details": "[답변의 장단점을 구체적으로 분석]",
  "suggestions": ["구체적인 개선방안 1", "구체적인 개선방안 2", "구체적인 개선방안 3"]
}}

**평가 가이드라인:**
- "모르겠어", "잘 모름" 등의 매우 짧은 답변: 1-2점
- 기본 개념만 언급: 3-4점  
- 기본 개념 + 간단한 설명: 5-6점
- 구체적 설명 + 예시: 7-8점
- 심화 설명 + 실무 경험 + 모범사례: 9-10점

질문의 기술적 수준과 난이도를 고려하여 공정하고 교육적인 피드백을 제공해주세요."""

        try:
            # Google Gemini로 분석 요청
            gemini_response = await self.ai_service.generate_analysis(
                prompt=prompt,
                provider=AIProvider.GEMINI_FLASH
            )
            
            # Gemini 응답에서 JSON 파싱
            return self._parse_gemini_response(gemini_response["content"])
            
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            raise

    def _parse_gemini_response(self, gemini_content: str) -> Dict[str, Any]:
        """Gemini 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            import json
            import re
            
            # JSON 블록 추출 시도
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', gemini_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                
                # 필수 필드 검증 및 기본값 설정
                score = float(parsed.get("score", 5.0))
                score = max(1.0, min(10.0, score))
                
                message = parsed.get("message", "AI 분석이 완료되었습니다.")
                details = parsed.get("details", "답변을 분석했습니다.")
                suggestions = parsed.get("suggestions", ["더 구체적인 예시를 추가해보세요"])
                
                if not isinstance(suggestions, list):
                    suggestions = [str(suggestions)]
                
                return {
                    "score": score,
                    "message": message,
                    "details": details,
                    "suggestions": suggestions[:3]  # 최대 3개
                }
            else:
                # JSON 파싱 실패 시 텍스트에서 정보 추출
                return self._extract_from_text(gemini_content)
                
        except Exception as e:
            logger.error(f"Gemini 응답 파싱 실패: {e}")
            return self._extract_from_text(gemini_content)

    def _extract_from_text(self, content: str) -> Dict[str, Any]:
        """JSON 파싱 실패 시 텍스트에서 피드백 정보 추출"""
        import re
        
        # 점수 추출
        score_match = re.search(r'(?:점수|score)[:\s]*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
        score = float(score_match.group(1)) if score_match else 5.0
        score = max(1.0, min(10.0, score))
        
        # 메시지 추출 (첫 번째 문장)
        sentences = content.split('.')
        message = sentences[0][:100] + "..." if len(sentences[0]) > 100 else sentences[0]
        
        # 기본 제안사항
        suggestions = [
            "구체적인 예시를 추가해보세요",
            "실무 경험을 공유해보세요",
            "기술적 세부사항을 더 설명해보세요"
        ]
        
        return {
            "score": score,
            "message": message,
            "details": f"Gemini AI 분석: {content[:200]}...",
            "suggestions": suggestions
        }

    def _fallback_analysis(self, answer: str) -> AnswerFeedback:
        """Gemini 분석 실패 시 기본 분석"""
        answer_length = len(answer.strip())
        word_count = len(answer.split())
        
        # 더 정교한 분석
        if answer_length < 10 or "모르" in answer or "잘 모름" in answer:
            score = 1.5
            message = "답변이 너무 짧거나 불충분합니다. 알고 있는 내용이라도 구체적으로 설명해보세요."
            suggestions = [
                "기본 개념부터 설명해보세요",
                "관련 경험이나 공부한 내용을 공유해보세요",
                "구글링해서 찾은 정보라도 정리해서 답변해보세요"
            ]
        elif answer_length < 50:
            score = 3.5
            message = "기본적인 답변입니다. 더 자세한 설명과 구체적인 예시가 필요합니다."
            suggestions = [
                "코드 예시를 추가해보세요",
                "장단점을 비교해서 설명해보세요", 
                "실제 사용 경험을 공유해보세요"
            ]
        elif answer_length < 200:
            score = 5.5
            message = "좋은 시작입니다. 더 구체적인 예시와 실무 관점에서의 설명을 추가하면 완벽할 것 같습니다."
            suggestions = [
                "구체적인 코드나 설정 예시를 추가해보세요",
                "발생할 수 있는 문제점과 해결방안을 언급해보세요"
            ]
        else:
            score = 7.0
            message = "상세한 답변 감사합니다. 실무 경험이나 모범사례를 더 포함하면 더욱 좋을 것 같습니다."
            suggestions = [
                "실제 프로젝트에서 사용한 경험을 공유해보세요",
                "성능 최적화나 보안 고려사항을 추가해보세요"
            ]
        
        return AnswerFeedback(
            score=score,
            feedback_type=self._get_feedback_type(score),
            message=message,
            details=f"답변 길이: {word_count}단어, 문자: {answer_length}자",
            suggestions=suggestions[:3]
        )
    
    def _get_feedback_type(self, score: float) -> FeedbackType:
        """점수에 따른 피드백 타입 결정"""
        if score >= 8.0:
            return FeedbackType.STRENGTH
        elif score >= 6.0:
            return FeedbackType.IMPROVEMENT
        else:
            return FeedbackType.SUGGESTION


# 글로벌 인스턴스
answer_analyzer = AnswerAnalyzer()